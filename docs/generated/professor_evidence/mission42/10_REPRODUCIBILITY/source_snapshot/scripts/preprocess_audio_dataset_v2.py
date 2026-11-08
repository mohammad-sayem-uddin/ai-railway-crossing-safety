#!/usr/bin/env python3
"""
Phase 2: Deterministic Preprocessing, Recording-Level Splitting, and Feature Extraction for Audio Model V2.
Adheres strictly to the balanced 86/86 selection and zero-leakage protocol.
"""
from __future__ import annotations

import json
import random
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402

WORKSPACE = Path("/Users/sayemuddin/Desktop/Train_automation")
SELECTION_MANIFEST = WORKSPACE / "data/manifests/audio_training_v2_selection.json"
AUDIO_RAW_DIR = WORKSPACE / "data/raw/audio/train_horn"
PROCESSED_AUDIO_DIR = WORKSPACE / "data/processed/audio/v2"

WAV_16K_DIR = PROCESSED_AUDIO_DIR / "wav_16k"
FEATURES_DIR = PROCESSED_AUDIO_DIR / "features"
SPLITS_DIR = WORKSPACE / "data/splits/audio/v2"
MANIFESTS_DIR = WORKSPACE / "data/manifests"


# --- Pure NumPy Log-Mel implementation matching src/railway_detection/audio/features.py ---
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
    print("=== Phase 2 Preprocessing Pipeline ===")
    with open(SELECTION_MANIFEST) as f:
        selection_data = json.load(f)

    selected_records = selection_data["selected_records"]
    print(f"Loaded {len(selected_records)} selected records (86 pos, 86 neg).")

    (WAV_16K_DIR / "positive").mkdir(parents=True, exist_ok=True)
    (WAV_16K_DIR / "negative").mkdir(parents=True, exist_ok=True)
    (FEATURES_DIR / "positive").mkdir(parents=True, exist_ok=True)
    (FEATURES_DIR / "negative").mkdir(parents=True, exist_ok=True)
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Convert to standardized WAVs
    print("\nStep 1: Converting to 16 kHz mono PCM WAV...")
    for idx, r in enumerate(selected_records, start=1):
        fn = r["filename"]
        cls_sub = "positive" if r["class"] == "train_horn" else "negative"
        src_path = AUDIO_RAW_DIR / cls_sub / fn
        dst_path = WAV_16K_DIR / cls_sub / f"{Path(fn).stem}.wav"
        
        if not dst_path.exists():
            convert_to_standard_wav(src_path, dst_path)
        r["standardized_wav"] = str(dst_path.relative_to(WORKSPACE))
        if idx % 40 == 0 or idx == len(selected_records):
            print(f"  Processed {idx}/{len(selected_records)} WAV files...")

    # 2. Recording-Level Split (70% Train, 15% Val, 15% Test)
    print("\nStep 2: Performing Recording-Level Leakage-Free Split (Seed=42)...")
    pos_records = [r for r in selected_records if r["class"] == "train_horn"]
    neg_records = [r for r in selected_records if r["class"] == "non_train_sound"]
    assert len(pos_records) == 86 and len(neg_records) == 86

    rng = random.Random(42)
    shuffled_pos = list(pos_records)
    rng.shuffle(shuffled_pos)
    shuffled_neg = list(neg_records)
    rng.shuffle(shuffled_neg)

    train_pos, val_pos, test_pos = shuffled_pos[:60], shuffled_pos[60:73], shuffled_pos[73:]
    train_neg, val_neg, test_neg = shuffled_neg[:60], shuffled_neg[60:73], shuffled_neg[73:]

    for r in train_pos + train_neg:
        r["partition"] = "train"
    for r in val_pos + val_neg:
        r["partition"] = "val"
    for r in test_pos + test_neg:
        r["partition"] = "test"

    print("Partition counts by recording:")
    print(f"  Train: {len(train_pos)} pos, {len(train_neg)} neg (Total: {len(train_pos) + len(train_neg)})")
    print(f"  Val:   {len(val_pos)} pos, {len(val_neg)} neg (Total: {len(val_pos) + len(val_neg)})")
    print(f"  Test:  {len(test_pos)} pos, {len(test_neg)} neg (Total: {len(test_pos) + len(test_neg)})")

    train_recs = {f"{r['class']}/{r['filename']}" for r in train_pos + train_neg}
    val_recs = {f"{r['class']}/{r['filename']}" for r in val_pos + val_neg}
    test_recs = {f"{r['class']}/{r['filename']}" for r in test_pos + test_neg}
    assert len(train_recs & val_recs) == 0, "Leakage between train and val!"
    assert len(train_recs & test_recs) == 0, "Leakage between train and test!"
    assert len(val_recs & test_recs) == 0, "Leakage between val and test!"

    # Verify zero SHA-256 hash leakage
    train_shas = {r["sha256"] for r in train_pos + train_neg}
    val_shas = {r["sha256"] for r in val_pos + val_neg}
    test_shas = {r["sha256"] for r in test_pos + test_neg}
    assert len(train_shas & val_shas) == 0, "SHA-256 Leakage between train and val!"
    assert len(train_shas & test_shas) == 0, "SHA-256 Leakage between train and test!"
    assert len(val_shas & test_shas) == 0, "SHA-256 Leakage between val and test!"

    split_summary = {
        "seed": 42,
        "split_level": "source_recording",
        "partitions": {
            "train": {"positive": len(train_pos), "negative": len(train_neg), "total": len(train_pos) + len(train_neg)},
            "val": {"positive": len(val_pos), "negative": len(val_neg), "total": len(val_pos) + len(val_neg)},
            "test": {"positive": len(test_pos), "negative": len(test_neg), "total": len(test_pos) + len(test_neg)},
        },
        "train_recordings": sorted(list(train_recs)),
        "val_recordings": sorted(list(val_recs)),
        "test_recordings": sorted(list(test_recs)),
    }
    with open(SPLITS_DIR / "dataset_split.json", "w") as f:
        json.dump(split_summary, f, indent=2)

    # 3. Windowing and Feature Extraction
    print("\nStep 3: Sliding 1.0s Windowing and 64-band Log-Mel Spectrogram Extraction...")
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
            samples = np.pad(samples, (0, pad), mode="constant")

        n_windows = max(1, 1 + (len(samples) - win_samples) // hop_samples)
        for w_idx in range(n_windows):
            start_s = w_idx * hop_s
            end_s = start_s + window_length_s
            start_sample = w_idx * hop_samples
            end_sample = start_sample + win_samples
            
            chunk = samples[start_sample:end_sample]
            if len(chunk) < win_samples:
                chunk = np.pad(chunk, (0, win_samples - len(chunk)), mode="constant")
                
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
                "source_relative_path": f"data/raw/audio/train_horn/{cls_sub}/{r['filename']}",
                "source_sha256": r["sha256"],
                "class_name": r["class"],
                "class_id": class_id,
                "category": r["category"],
                "partition": r["partition"],
                "window_index": w_idx,
                "start_time_s": round(start_s, 2),
                "end_time_s": round(end_s, 2),
                "duration_s": 1.0,
                "sample_rate": target_sr,
                "standardized_wav_path": r["standardized_wav"],
                "feature_path": str(feat_path.relative_to(WORKSPACE)),
                "feature_type": "log_mel_spectrogram",
                "feature_shape": [64, 61],
                "dataset_role": "audio_model_development"
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

    train_concat = np.stack(train_features_list, axis=0)
    norm_mean = float(np.mean(train_concat))
    norm_std = float(np.std(train_concat))
    print(f"\nFeature Normalization Stats (computed on Train windows):")
    print(f"  Mean: {norm_mean:.4f}")
    print(f"  Std:  {norm_std:.4f}")

    manifest_v2_json = MANIFESTS_DIR / "audio_training_dataset_v2.json"
    manifest_v2_jsonl = MANIFESTS_DIR / "audio_training_dataset_v2.jsonl"
    with open(manifest_v2_json, "w") as f:
        json.dump(all_windows, f, indent=2)
    with open(manifest_v2_jsonl, "w") as f:
        for w in all_windows:
            f.write(json.dumps(w) + "\n")
    print(f"\nSaved audio training dataset manifest to {manifest_v2_json}")


if __name__ == "__main__":
    main()
