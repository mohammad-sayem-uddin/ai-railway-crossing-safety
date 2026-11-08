#!/usr/bin/env python3
"""
Audio Model V3 Preprocessing Pipeline:
Standardize WAVs (16 kHz mono 16-bit PCM WAV),
Sliding 1.0s window extraction (0.5s hop),
64-band Log-Mel Spectrogram extraction,
and Training Manifest Generation.

Reads from data/manifests/audio_v3_selection.json.
Enforces zero data leakage across partitions.
"""
from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402

WORKSPACE = Path("/Users/sayemuddin/Desktop/Train_automation")
SELECTION_MANIFEST = WORKSPACE / "data/manifests/audio_v3_selection.json"
PROCESSED_AUDIO_DIR = WORKSPACE / "data/processed/audio/v3"
WAV_16K_DIR = PROCESSED_AUDIO_DIR / "wav_16k"
FEATURES_DIR = PROCESSED_AUDIO_DIR / "features"
MANIFESTS_DIR = WORKSPACE / "data/manifests"


# --- Pure NumPy Log-Mel implementation matching project specifications ---
def hz_to_mel(frequencies: np.ndarray | float) -> np.ndarray | float:
    return 2595.0 * np.log10(1.0 + np.asarray(frequencies) / 700.0)


def mel_to_hz(mels: np.ndarray | float) -> np.ndarray | float:
    return 700.0 * (10.0 ** (np.asarray(mels) / 2595.0) - 1.0)


def create_mel_filterbank(
    sample_rate: int = 16000,
    n_fft: int = 512,
    n_mels: int = 64,
    f_min: float = 0.0,
    f_max: float | None = None,
) -> np.ndarray:
    if f_max is None:
        f_max = float(sample_rate) / 2.0

    n_freq_bins = n_fft // 2 + 1
    mel_min = float(hz_to_mel(f_min))
    mel_max = float(hz_to_mel(f_max))

    mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
    hz_points = mel_to_hz(mel_points)

    bin_points = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)
    bin_points = np.clip(bin_points, 0, n_freq_bins - 1)

    filterbank = np.zeros((n_mels, n_freq_bins), dtype=np.float64)
    for m in range(1, n_mels + 1):
        f_left = bin_points[m - 1]
        f_center = bin_points[m]
        f_right = bin_points[m + 1]

        if f_center > f_left:
            filterbank[m - 1, f_left:f_center] = (
                np.arange(f_left, f_center) - f_left
            ) / float(f_center - f_left)
        if f_right > f_center:
            filterbank[m - 1, f_center:f_right] = (
                f_right - np.arange(f_center, f_right)
            ) / float(f_right - f_center)

    return filterbank


def compute_stft(
    waveform: np.ndarray,
    n_fft: int = 512,
    hop_length: int = 256,
) -> np.ndarray:
    waveform = np.asarray(waveform, dtype=np.float64)
    if waveform.ndim != 1:
        waveform = waveform.flatten()

    if len(waveform) < n_fft:
        pad_width = n_fft - len(waveform)
        waveform = np.pad(waveform, (0, pad_width), mode="constant")

    window = np.hanning(n_fft)
    n_frames = 1 + (len(waveform) - n_fft) // hop_length

    shape = (n_frames, n_fft)
    strides = (waveform.strides[0] * hop_length, waveform.strides[0])
    frames = np.lib.stride_tricks.as_strided(waveform, shape=shape, strides=strides)

    windowed = frames * window
    stft = np.fft.rfft(windowed, n=n_fft, axis=-1)
    return stft.T


def compute_log_mel_spectrogram(
    waveform: np.ndarray,
    sample_rate: int = 16000,
    n_fft: int = 512,
    hop_length: int = 256,
    n_mels: int = 64,
    f_min: float = 0.0,
    f_max: float | None = None,
    eps: float = 1e-10,
) -> np.ndarray:
    stft = compute_stft(waveform, n_fft=n_fft, hop_length=hop_length)
    power = np.abs(stft) ** 2.0
    filterbank = create_mel_filterbank(
        sample_rate=sample_rate,
        n_fft=n_fft,
        n_mels=n_mels,
        f_min=f_min,
        f_max=f_max,
    )
    mel_energies = np.dot(filterbank, power)
    log_mel = np.log(mel_energies + eps)
    return log_mel


def convert_to_standard_wav(src_path: Path, dst_path: Path, target_sr: int = 16000) -> None:
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    require_media_authorization(src_path, "AUDIO_EXTRACTION")
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(src_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", str(target_sr),
        "-ac", "1",
        str(dst_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def load_wav_samples(wav_path: Path) -> np.ndarray:
    import wave
    require_media_authorization(wav_path, "FEATURE_EXTRACTION")
    with wave.open(str(wav_path), "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        n_frames = wf.getnframes()
        frames = wf.readframes(n_frames)

    if sampwidth == 2:
        samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    else:
        raise ValueError(f"Unsupported sample width {sampwidth} in {wav_path}")

    if n_channels > 1:
        samples = samples.reshape(-1, n_channels).mean(axis=1)
    return samples


def main():
    print("=" * 60)
    print("AUDIO V3 PREPROCESSING & FEATURE EXTRACTION PIPELINE")
    print("=" * 60)

    assert SELECTION_MANIFEST.exists(), f"Missing {SELECTION_MANIFEST}"
    with open(SELECTION_MANIFEST) as f:
        selection_data = json.load(f)

    selected_records = selection_data["selected_records"]
    print(f"Loaded {len(selected_records)} selected records (86 pos, 86 ESC-50 neg).")

    (WAV_16K_DIR / "positive").mkdir(parents=True, exist_ok=True)
    (WAV_16K_DIR / "negative").mkdir(parents=True, exist_ok=True)
    (FEATURES_DIR / "positive").mkdir(parents=True, exist_ok=True)
    (FEATURES_DIR / "negative").mkdir(parents=True, exist_ok=True)

    # 1. Convert to standardized 16 kHz mono WAV
    print("\nStep 1: Converting to standardized 16 kHz mono PCM WAV...")
    for idx, r in enumerate(selected_records, start=1):
        cls_sub = "positive" if r["class"] == "train_horn" else "negative"
        src_path = WORKSPACE / r["source_path"]
        dst_path = WAV_16K_DIR / cls_sub / f"{Path(r['filename']).stem}.wav"

        if not dst_path.exists():
            convert_to_standard_wav(src_path, dst_path)
        r["standardized_wav"] = str(dst_path.relative_to(WORKSPACE))
        if idx % 40 == 0 or idx == len(selected_records):
            print(f"  Processed {idx}/{len(selected_records)} WAV files...")

    # 2. Windowing and Feature Extraction
    print("\nStep 2: Sliding 1.0s Windowing & 64-band Log-Mel Spectrogram Extraction...")
    window_length_s = 1.0
    hop_s = 0.5
    target_sr = 16000
    win_samples = int(window_length_s * target_sr)
    hop_samples = int(hop_s * target_sr)

    all_windows = []
    train_features_list = []

    for idx, r in enumerate(selected_records, start=1):
        wav_path = WORKSPACE / r["standardized_wav"]
        samples = load_wav_samples(wav_path)
        cls_sub = "positive" if r["class"] == "train_horn" else "negative"
        class_id = 1 if r["class"] == "train_horn" else 0

        if len(samples) < win_samples:
            pad = win_samples - len(samples)
            samples = np.pad(samples, (0, pad), mode="reflect")

        n_windows = max(1, 1 + (len(samples) - win_samples) // hop_samples)
        for w_idx in range(n_windows):
            start_s = w_idx * hop_s
            end_s = start_s + window_length_s
            start_sample = w_idx * hop_samples
            end_sample = start_sample + win_samples

            chunk = samples[start_sample:end_sample]
            if len(chunk) < win_samples:
                chunk = np.pad(chunk, (0, win_samples - len(chunk)), mode="reflect")

            feat = compute_log_mel_spectrogram(
                chunk,
                sample_rate=target_sr,
                n_fft=512,
                hop_length=256,
                n_mels=64,
                f_min=80.0,
                f_max=8000.0,
            )
            assert feat.shape == (64, 61), f"Unexpected shape {feat.shape}"

            window_id = f"{r['sample_id']}_w{w_idx:03d}"
            feat_path = FEATURES_DIR / cls_sub / f"{window_id}.npy"
            np.save(feat_path, feat.astype(np.float32))

            win_record = {
                "window_id": window_id,
                "sample_id": r["sample_id"],
                "source_file": r["filename"],
                "source_relative_path": r["source_path"],
                "source_dataset": r["source_dataset"],
                "source_sha256": r["sha256"],
                "class_name": r["class"],
                "class_id": class_id,
                "category": r.get("category", "train_horn"),
                "partition": r["partition"],
                "esc50_fold": r.get("esc50_fold"),
                "source_group": r["source_group"],
                "window_index": w_idx,
                "start_time_s": round(start_s, 2),
                "end_time_s": round(end_s, 2),
                "duration_s": 1.0,
                "sample_rate": target_sr,
                "standardized_wav_path": r["standardized_wav"],
                "feature_path": str(feat_path.relative_to(WORKSPACE)),
                "feature_type": "log_mel_spectrogram",
                "feature_shape": [64, 61],
                "dataset_role": "audio_model_v3_esc50_development",
            }
            all_windows.append(win_record)
            if r["partition"] == "train":
                train_features_list.append(feat)

    print(f"\nGenerated {len(all_windows)} total windows across all partitions.")
    part_counts = defaultdict(lambda: {"pos": 0, "neg": 0})
    for w in all_windows:
        cls_key = "pos" if w["class_id"] == 1 else "neg"
        part_counts[w["partition"]][cls_key] += 1
    for p, c in part_counts.items():
        print(f"  {p:6}: {c['pos']} pos, {c['neg']} neg (Total: {c['pos'] + c['neg']})")

    # Compute training normalization statistics strictly on training partition
    train_concat = np.stack(train_features_list, axis=0)
    norm_mean = float(np.mean(train_concat))
    norm_std = float(np.std(train_concat))
    print(f"\nFeature Normalization Stats (computed on Train windows):")
    print(f"  Mean: {norm_mean:.4f}")
    print(f"  Std:  {norm_std:.4f}")

    manifest_v3_json = MANIFESTS_DIR / "audio_training_dataset_v3.json"
    manifest_v3_jsonl = MANIFESTS_DIR / "audio_training_dataset_v3.jsonl"
    with open(manifest_v3_json, "w") as f:
        json.dump(all_windows, f, indent=2)
    with open(manifest_v3_jsonl, "w") as f:
        for w in all_windows:
            f.write(json.dumps(w) + "\n")
    print(f"\nSaved audio training dataset manifest to {manifest_v3_json}")

    # Save normalization stats metadata
    stats_meta = {
        "norm_mean": norm_mean,
        "norm_std": norm_std,
        "train_windows_count": len(train_features_list),
        "total_windows_count": len(all_windows),
    }
    with open(PROCESSED_AUDIO_DIR / "normalization_stats.json", "w") as f:
        json.dump(stats_meta, f, indent=2)

    print("\nPhase 2 Preprocessing & Feature Extraction completed successfully!")


if __name__ == "__main__":
    main()
