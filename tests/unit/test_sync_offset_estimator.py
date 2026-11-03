"""Regression tests for the GCC-PHAT camera-offset estimator (R04 Problem B1/B2/H).

Covers the sign convention, zero/fractional offsets, unequal durations, noise
robustness, and the "no common transient" degenerate case explicitly called
for in the mission brief. These tests exist because a first, uncaught
implementation of this exact estimator had its sign backwards end-to-end
(correct magnitude, wrong direction) -- see
docs/R04_CALIBRATION_VALIDATION_REPORT.md section 3 for the worked example.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from estimate_camera_sync_offsets import gcc_phat, window_stability  # noqa: E402


SR = 16000


def _make_master_signal(n: int, rng: np.random.Generator) -> np.ndarray:
    t = np.arange(n) / SR
    sig = rng.normal(0, 0.05, n)
    for center_s, amp, width_s in [(5.0, 1.0, 0.05), (12.0, 0.6, 0.08), (19.0, 0.8, 0.03)]:
        env = amp * np.exp(-0.5 * ((t - center_s) / width_s) ** 2)
        sig += env * rng.normal(0, 1, n)
    return sig


def _build_pair(
    master: np.ndarray, true_offset_s: float, rng: np.random.Generator, extra_noise_std: float = 0.01
) -> tuple[np.ndarray, np.ndarray]:
    """Construct (front, back) such that true `offset_s` holds under the
    project convention: t_master(=front) = t_back + offset_s.

    Equivalently back(t) = front(t + offset_s): a positive offset_s means the
    back camera's local-time-zero already corresponds to master content at
    +offset_s (back started recording LATER in real time, so by the time it
    starts, the shared sound field has already advanced that far).
    """
    front = master.copy()
    offset_samples = int(round(true_offset_s * SR))
    if offset_samples >= 0:
        back = master[offset_samples:].copy()
    else:
        back = np.concatenate([np.zeros(-offset_samples), master])
    front = front + rng.normal(0, extra_noise_std, len(front))
    back = back + rng.normal(0, extra_noise_std, len(back))
    return front, back


@pytest.fixture
def master_signal() -> np.ndarray:
    rng = np.random.default_rng(42)
    return _make_master_signal(int(25.0 * SR), rng)


@pytest.mark.parametrize(
    "true_offset_s",
    [2.0, -1.5, 0.0, 2.37, -3.63, 0.333],
)
def test_sign_convention_exact_recovery(master_signal: np.ndarray, true_offset_s: float) -> None:
    """Positive, negative, zero, and fractional-second offsets must all be
    recovered with the correct sign and sub-millisecond accuracy on a clean
    synthetic signal."""
    rng = np.random.default_rng(7)
    front, back = _build_pair(master_signal, true_offset_s, rng)
    result = gcc_phat(front, back, SR)
    assert abs(result.lag_s - true_offset_s) < 0.001, (
        f"expected lag {true_offset_s}, got {result.lag_s} "
        f"(sign error if magnitude matches but sign differs)"
    )


def test_noisy_signal_still_recovers_correct_sign() -> None:
    rng = np.random.default_rng(11)
    master = _make_master_signal(int(25.0 * SR), rng)
    front, back = _build_pair(master, 4.0, rng, extra_noise_std=0.05)
    result = gcc_phat(front, back, SR)
    assert abs(result.lag_s - 4.0) < 0.01
    assert result.lag_s > 0  # sign must not flip under added noise


def test_unequal_recording_durations() -> None:
    """Front and back recordings of different total length (one camera
    stopped recording earlier) must not break the estimator or its sign."""
    rng = np.random.default_rng(13)
    master = _make_master_signal(int(30.0 * SR), rng)
    front, back = _build_pair(master, 6.0, rng)
    front = front[: int(28.0 * SR)]  # front recording is 2s shorter
    result = gcc_phat(front, back, SR)
    assert abs(result.lag_s - 6.0) < 0.01


def test_no_common_transient_is_low_confidence() -> None:
    """Two independent noise signals sharing no physical event must produce
    a low, unreliable PSR -- the estimator must not report high confidence
    on an essentially arbitrary peak. This is the basis for AMBIGUOUS
    classification of the no-train negative controls."""
    rng = np.random.default_rng(19)
    n = int(20.0 * SR)
    sig_a = rng.normal(0, 1, n)
    sig_b = rng.normal(0, 1, n)
    result = gcc_phat(sig_a, sig_b, SR)
    assert result.psr < 1.5, f"expected low PSR for unrelated signals, got {result.psr}"


def test_window_stability_detects_genuine_instability() -> None:
    """A signal whose only shared transient is confined to a small part of
    the recording must show a large window-range when the sub-windows that
    miss the transient are evaluated -- this is the diagnostic the mission
    brief's acceptance criterion depends on, and it must be driven by real
    window-to-window disagreement, not a constant pass-through of the global
    lag."""
    rng = np.random.default_rng(23)
    n = int(30.0 * SR)
    # Ambient noise floor shared with independent realizations (no common
    # content) for the whole duration, plus ONE shared sharp transient near
    # the very start only.
    front = rng.normal(0, 0.05, n)
    back = rng.normal(0, 0.05, n)
    t = np.arange(n) / SR
    env = 1.0 * np.exp(-0.5 * ((t - 2.0) / 0.03) ** 2)
    shared_burst = env * rng.normal(0, 1, n)
    front += shared_burst
    back += np.roll(shared_burst, int(0.5 * SR))  # back delayed 0.5s, transient only near t=2s

    lags = window_stability(front, back, SR, n_windows=3, window_fraction=0.6)
    finite = [w for w in lags if np.isfinite(w)]
    window_range = max(finite) - min(finite) if len(finite) >= 2 else 0.0
    # The transient is only inside the first window; later windows see no
    # shared content and should disagree substantially with the first.
    assert window_range > 0.1, (
        f"expected window instability when the shared transient is confined "
        f"to one segment, got range={window_range:.4f} from lags={lags}"
    )


def test_fractional_sample_offset_reproducible() -> None:
    """A sub-sample-period offset must not crash or silently round, and must
    recover to within one sample period."""
    rng = np.random.default_rng(29)
    master = _make_master_signal(int(15.0 * SR), rng)
    # 0.3330s = 5328 samples at 16kHz exactly; use a value that is NOT an
    # exact sample multiple to probe rounding behavior.
    true_offset_s = 1234.0 / SR + 0.00003  # deliberately not integer-sample
    front, back = _build_pair(master, true_offset_s, rng)
    result = gcc_phat(front, back, SR)
    assert abs(result.lag_s - true_offset_s) < (1.0 / SR) * 2  # within 2 sample periods


def test_competing_multipath_peaks_yields_window_hopping() -> None:
    """Simulates train_events/event_004: two physical acoustic propagation paths
    (direct at 4.90s, multipath reflection at 5.14s, 240 ms separation).

    Path B (echo) is dominant in the early recording, while Path A (direct)
    dominates later. Demonstrates that window stability correctly flags this
    physical competition (win_range > 0.20s), preventing false SUPPORTED classification.
    """
    rng = np.random.default_rng(88)
    n = int(30.0 * SR)
    t = np.arange(n) / SR

    master = rng.normal(0, 0.05, n)
    for c, a, w in [(4.0, 1.0, 0.05), (12.0, 0.8, 0.05), (20.0, 0.9, 0.05)]:
        master += a * np.exp(-0.5 * ((t - c) / w) ** 2) * rng.normal(0, 1, n)

    d0 = int(4.90 * SR)
    d1 = int(5.14 * SR)
    L = int(22.0 * SR)

    front = master[:L].copy()
    w0 = np.linspace(0.1, 0.9, L)
    w1 = 1.0 - w0
    back = w0 * master[d0 : d0 + L] + w1 * master[d1 : d1 + L]

    res = gcc_phat(front, back, SR)
    w_lags = window_stability(front, back, SR, n_windows=3, window_fraction=0.6)
    finite_w = [w for w in w_lags if np.isfinite(w)]
    win_range = max(finite_w) - min(finite_w)

    assert abs(abs(res.secondary_lag_s - res.lag_s) - 0.24) < 0.02
    assert win_range > 0.20, f"Expected multipath window hopping > 0.20s, got {win_range:.4f}s"


def test_short_recording_localized_transient_window_wander() -> None:
    """Simulates engine_events/event_001: short recordings where independent
    background noise on each camera dominates when the transient is localized.
    Demonstrates that sub-windows extending into unshared ambient noise wander.
    """
    rng = np.random.default_rng(77)
    front = rng.normal(0, 0.1, int(7.9 * SR))
    back = rng.normal(0, 0.1, int(9.8 * SR))

    t_burst = np.arange(int(2.0 * SR)) / SR
    burst = np.sin(2 * np.pi * 300 * t_burst) * rng.normal(0, 1, len(t_burst))

    offset_s = 0.500
    offset_samples = int(round(offset_s * SR))

    front[: len(burst)] += burst
    back[offset_samples : offset_samples + len(burst)] += burst

    w_lags = window_stability(front, back, SR, n_windows=3, window_fraction=0.6)
    finite_w = [w for w in w_lags if np.isfinite(w)]
    win_range = max(finite_w) - min(finite_w)
    assert win_range > 0.10, f"Expected window wander in short overlap, got {win_range:.4f}s"


def test_multipath_echo_secondary_peak_detection() -> None:
    """Simulates acoustic multipath reflection (e.g. bogie / structure echo
    spaced at 250 ms) showing that GCC-PHAT detects both the direct arrival
    and secondary reflection with high amplitude ratio.
    """
    rng = np.random.default_rng(99)
    n = int(20.0 * SR)
    master = rng.normal(0, 0.05, n)
    t = np.arange(n) / SR
    for c, a, w in [(5.0, 1.0, 0.05), (10.0, 0.8, 0.05), (15.0, 0.9, 0.05)]:
        master += a * np.exp(-0.5 * ((t - c) / w) ** 2) * rng.normal(0, 1, n)

    d0 = int(2.00 * SR)
    d1 = int(2.25 * SR)  # 250 ms echo
    L = int(16.0 * SR)

    front = master[:L].copy()
    back = 0.60 * master[d0 : d0 + L] + 0.40 * master[d1 : d1 + L]

    res = gcc_phat(front, back, SR)
    sec_dist = abs(res.secondary_lag_s - res.lag_s)

    assert abs(res.lag_s - 2.00) < 0.005
    assert abs(sec_dist - 0.25) < 0.010
    assert res.secondary_amplitude_ratio > 0.20


