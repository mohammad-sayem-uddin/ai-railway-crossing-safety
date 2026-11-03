#!/usr/bin/env python3
"""Inter-camera synchronization offset estimation via GCC-PHAT cross-correlation.

Reproducible, standalone estimator for R04. Reads extracted 16 kHz mono WAV
audio tracks for the front and back camera of each Layer B event, computes:

- A monolithic (full-stream) GCC-PHAT lag estimate.
- Peak SNR and Peak-to-Sidelobe Ratio (PSR) diagnostics on that estimate.
- A temporal window-stability audit (three overlapping sub-windows of the
  overlapping duration), reporting the spread (max - min) of the per-window
  lag estimates as `window_range_s`.
- A secondary-peak lag (the highest peak outside the PSR exclusion window).

Sign convention (frozen, verified in `tests/unit/test_sync_offset_estimator.py`):
    t_master = t_back + offset_s
    offset_s > 0 means the back-camera recording started AFTER the front-camera
    recording (equivalently, a shared acoustic event appears EARLIER in the
    back-camera stream's local time than in the front-camera stream's local time).

This module intentionally does not decide calibration acceptance. It only
produces raw, reproducible diagnostics. Acceptance rules live in
`src/railway_detection/data/sync_calibration.py`.
"""

from __future__ import annotations

import argparse
import json
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIO_ROOT = REPO_ROOT / "data" / "processed" / "layer_b" / "audio"
LAG_SEARCH_BOUND_S = 60.0
PSR_EXCLUSION_HALF_WIDTH_S = 0.05  # 50 ms, matches the report's stated definition


@dataclass
class GccPhatResult:
    lag_s: float
    snr: float
    psr: float
    secondary_lag_s: float
    secondary_amplitude_ratio: float
    n_samples_front: int
    n_samples_back: int
    sample_rate: int


def load_wav_mono(path: Path) -> tuple[np.ndarray, int]:
    require_media_authorization(path, "FEATURE_EXTRACTION")
    with wave.open(str(path), "rb") as wf:
        n_channels = wf.getnchannels()
        sample_rate = wf.getframerate()
        sample_width = wf.getsampwidth()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
    if sample_width != 2:
        raise ValueError(f"Expected 16-bit PCM, got sample width {sample_width} bytes: {path}")
    data = np.frombuffer(raw, dtype="<i2").astype(np.float64)
    if n_channels > 1:
        data = data.reshape(-1, n_channels).mean(axis=1)
    # Normalize to [-1, 1] by full-scale int16, do NOT peak-normalize (would
    # destroy relative amplitude information used nowhere here, but keep it
    # principled: fixed-scale normalization is reproducible; peak normalization
    # is not, since it depends on clipping / outlier samples).
    data = data / 32768.0
    return data, sample_rate


def gcc_phat(
    sig_front: np.ndarray,
    sig_back: np.ndarray,
    sample_rate: int,
    max_lag_s: float = LAG_SEARCH_BOUND_S,
    psr_exclusion_half_width_s: float = PSR_EXCLUSION_HALF_WIDTH_S,
) -> GccPhatResult:
    """Generalized Cross-Correlation with Phase Transform.

    Convention: cross-correlating front against back such that a positive
    estimated lag tau means front(t) aligns with back(t - tau), i.e.
    front is delayed relative to back by tau seconds. Combined with the
    sign convention in the module docstring, a positive GCC lag here is
    reported directly as `offset_s` in the manifest (same sign).

    Both signals are de-meaned and FFT-correlated with phase-only weighting
    (GCC-PHAT), using an FFT length that is the next power of two at or
    above len(front) + len(back) to avoid circular-correlation wraparound
    (the defect class explicitly flagged in Problem B2).
    """
    if len(sig_front) == 0 or len(sig_back) == 0:
        raise ValueError("Empty audio signal supplied to gcc_phat")

    a = sig_front - np.mean(sig_front)
    b = sig_back - np.mean(sig_back)

    n = len(a) + len(b)
    n_fft = 1
    while n_fft < n:
        n_fft *= 2

    A = np.fft.rfft(a, n=n_fft)
    B = np.fft.rfft(b, n=n_fft)
    R = A * np.conj(B)
    denom = np.abs(R)
    denom[denom < 1e-12] = 1e-12
    R_phat = R / denom

    cc = np.fft.irfft(R_phat, n=n_fft)
    # fftshift-equivalent reordering: cc[k] for k in [0, n_fft) corresponds to
    # lag (in samples) of k for k <= n_fft//2, and (k - n_fft) for k > n_fft//2.
    cc = np.concatenate((cc[n_fft // 2 :], cc[: n_fft // 2]))
    lags_samples = np.arange(-(n_fft // 2), n_fft - n_fft // 2)
    lags_s = lags_samples / float(sample_rate)

    max_lag_samples = int(round(max_lag_s * sample_rate))
    search_mask = np.abs(lags_samples) <= max_lag_samples
    cc_search = cc[search_mask]
    lags_search = lags_s[search_mask]

    abs_cc = np.abs(cc_search)
    peak_idx = int(np.argmax(abs_cc))
    peak_lag_s = float(lags_search[peak_idx])
    peak_amp = float(abs_cc[peak_idx])

    median_amp = float(np.median(abs_cc))
    std_amp = float(np.std(abs_cc))
    snr = (peak_amp - median_amp) / (std_amp + 1e-12)

    exclusion_mask = np.abs(lags_search - peak_lag_s) > psr_exclusion_half_width_s
    if np.any(exclusion_mask):
        sidelobe_amp_arr = abs_cc[exclusion_mask]
        sidelobe_lags_arr = lags_search[exclusion_mask]
        sidelobe_peak_idx = int(np.argmax(sidelobe_amp_arr))
        sidelobe_peak_amp = float(sidelobe_amp_arr[sidelobe_peak_idx])
        secondary_lag_s = float(sidelobe_lags_arr[sidelobe_peak_idx])
    else:
        sidelobe_peak_amp = 1e-12
        secondary_lag_s = float("nan")

    psr = peak_amp / (sidelobe_peak_amp + 1e-12)
    secondary_ratio = sidelobe_peak_amp / (peak_amp + 1e-12)

    return GccPhatResult(
        lag_s=peak_lag_s,
        snr=snr,
        psr=psr,
        secondary_lag_s=secondary_lag_s,
        secondary_amplitude_ratio=secondary_ratio,
        n_samples_front=len(a),
        n_samples_back=len(b),
        sample_rate=sample_rate,
    )


def window_stability(
    sig_front: np.ndarray,
    sig_back: np.ndarray,
    sample_rate: int,
    n_windows: int = 3,
    window_fraction: float = 0.6,
) -> list[float]:
    """Estimate lag independently on `n_windows` overlapping sub-windows.

    Windows span evenly-spaced start fractions of the SHORTER signal's
    duration (0.0 to 1.0 - window_fraction inclusive), each of length
    `window_fraction` of the shorter signal. Returns the list of per-window
    lag estimates (NaN where a window has too little signal to search).
    """
    shorter_len = min(len(sig_front), len(sig_back))
    win_len = int(shorter_len * window_fraction)
    if win_len < sample_rate:  # need at least 1s of audio to be meaningful
        return [float("nan")] * n_windows

    starts = np.linspace(0, shorter_len - win_len, n_windows)
    lags = []
    for start in starts:
        s = int(start)
        e = s + win_len
        try:
            result = gcc_phat(sig_front[s:e], sig_back[s:e], sample_rate)
            lags.append(result.lag_s)
        except ValueError:
            lags.append(float("nan"))
    return lags


def estimate_event(front_wav: Path, back_wav: Path) -> dict:
    sig_front, sr_front = load_wav_mono(front_wav)
    sig_back, sr_back = load_wav_mono(back_wav)
    if sr_front != sr_back:
        raise ValueError(f"Sample rate mismatch: front={sr_front} back={sr_back}")

    main = gcc_phat(sig_front, sig_back, sr_front)
    window_lags = window_stability(sig_front, sig_back, sr_front)
    finite_window_lags = [w for w in window_lags if np.isfinite(w)]
    window_range_s = (
        float(max(finite_window_lags) - min(finite_window_lags))
        if len(finite_window_lags) >= 2
        else float("nan")
    )

    return {
        "lag_s": round(main.lag_s, 4),
        "snr": round(main.snr, 2),
        "psr": round(main.psr, 2),
        "secondary_lag_s": round(main.secondary_lag_s, 4) if np.isfinite(main.secondary_lag_s) else None,
        "secondary_amplitude_ratio": round(main.secondary_amplitude_ratio, 4),
        "window_lags_s": [round(w, 4) if np.isfinite(w) else None for w in window_lags],
        "window_range_s": round(window_range_s, 4) if np.isfinite(window_range_s) else None,
        "duration_front_s": round(len(sig_front) / sr_front, 4),
        "duration_back_s": round(len(sig_back) / sr_back, 4),
        "sample_rate": sr_front,
    }


def discover_events() -> list[tuple[str, str, Path, Path]]:
    out = []
    for cohort_dir in sorted(AUDIO_ROOT.iterdir()):
        if not cohort_dir.is_dir():
            continue
        for event_dir in sorted(cohort_dir.iterdir()):
            if not event_dir.is_dir():
                continue
            front = event_dir / "camera_front.wav"
            back = event_dir / "camera_back.wav"
            if front.exists() and back.exists():
                out.append((cohort_dir.name, event_dir.name, front, back))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate inter-camera sync offsets via GCC-PHAT.")
    parser.add_argument("--events", nargs="*", help="Restrict to specific event_id values.")
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "results" / "r04_sync_estimation" / "gcc_phat_raw_results.json",
    )
    args = parser.parse_args()

    events = discover_events()
    if args.events:
        events = [e for e in events if e[1] in args.events]

    results = {}
    for cohort, event_id, front_wav, back_wav in events:
        key = f"{cohort}/{event_id}"
        print(f"Processing {key} ...")
        try:
            diag = estimate_event(front_wav, back_wav)
            diag["front_wav"] = str(front_wav.relative_to(REPO_ROOT))
            diag["back_wav"] = str(back_wav.relative_to(REPO_ROOT))
            results[key] = diag
        except Exception as exc:  # noqa: BLE001
            results[key] = {"error": str(exc)}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {len(results)} event results to {args.output}")


if __name__ == "__main__":
    main()
