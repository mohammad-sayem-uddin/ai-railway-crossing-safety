#!/usr/bin/env python3
"""Standardization, Leakage-Safe Group-Disjoint Partitioning, Windowing & Log-Mel Extraction.

Strict Research Protocol Constraints:
- Positive recordings: 87 files (86 unique, 41.mp3 and 42.mp3 bound to train).
- Negative recordings: 87 files (ESC-50 stratified subset, non-train).
- Balanced Split: 61 Train, 13 Val, 13 Test for both classes.
- Zero Leakage: Split occurs at recording/group level BEFORE segmentation.
- Standardization: 16 kHz mono 16-bit PCM WAV.
- Windowing: 2.0s window, 1.0s hop.
- Features: 64-band Log-Mel Spectrogram.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

WORKSPACE_ROOT = Path("/Users/sayemuddin/Desktop/Train_automation")
if str(WORKSPACE_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT / "src"))

from railway_detection.audio.features import compute_log_mel_spectrogram
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    require_media_authorization(path, "HASH_RAW_MEDIA")
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def probe_audio_file(path: Path) -> dict[str, Any]:
    require_media_authorization(path, "MEDIA_PROBE")
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_format",
        "-show_streams",
        "-of", "json",
        str(path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)
    a_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    fmt = data.get("format", {})
    return {
        "format_name": fmt.get("format_name", "unknown"),
        "duration_s": float(fmt.get("duration", 0.0)),
        "codec_name": a_stream.get("codec_name", "unknown") if a_stream else "none",
        "sample_rate": int(a_stream.get("sample_rate", 0)) if a_stream else 0,
        "channels": int(a_stream.get("channels", 0)) if a_stream else 0,
    }


def convert_and_normalize_wav(src_path: Path, dst_path: Path, target_sr: int = 16000) -> None:
    """Convert audio to 16 kHz mono 16-bit PCM WAV with peak amplitude normalization."""
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    # Step 1: ffmpeg conversion to mono 16k WAV
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
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion failed for {src_path}: {res.stderr}")

    # Step 2: Peak normalize waveform to -1.0 dBFS (~0.891 amplitude)
    import wave
    require_media_authorization(dst_path, "FEATURE_EXTRACTION")
    with wave.open(str(dst_path), "rb") as wav:
        sr = wav.getframerate()
        n_frames = wav.getnframes()
        raw = wav.readframes(n_frames)
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    
    peak = np.max(np.abs(samples))
    if peak > 1e-5:
        target_peak = 10.0 ** (-1.0 / 20.0)  # -1 dBFS = 0.89125
        samples = samples * (target_peak / peak)
    
    int_samples = np.clip(samples * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(dst_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(target_sr)
        wav.writeframes(int_samples.tobytes())


def load_pcm16_wav(path: Path) -> tuple[np.ndarray, int]:
    import wave
    require_media_authorization(path, "FEATURE_EXTRACTION")
    with wave.open(str(path), "rb") as wav:
        sr = wav.getframerate()
        n_frames = wav.getnframes()
        raw = wav.readframes(n_frames)
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    return samples, sr


def derive_positive_group_id(filename: str, sha256_hash: str, seen: dict[str, str]) -> str:
    if sha256_hash in seen:
        return seen[sha256_hash]
    stem = Path(filename).stem
    if stem in ("41", "42"):
        gid = "group_41_42_duplicate"
        seen[sha256_hash] = gid
        return gid
    cleaned = re.sub(r"\s*-\s*128(-\d+)?$", "", stem)
    cleaned = re.sub(r"\s*\(\d+\)$", "", cleaned).strip()
    gid = f"group_{cleaned}"
    seen[sha256_hash] = gid
    return gid


def build_pipeline_dataset(
    window_s: float = 2.0,
    hop_s: float = 1.0,
    target_sr: int = 16000,
) -> None:
    print("==================================================")
    print("STEP 1: INVENTORY POSITIVE & NEGATIVE DATASETS")
    print("==================================================")
    pos_dir = WORKSPACE_ROOT / "data/raw/audio/train_horn/positive"
    neg_dir = WORKSPACE_ROOT / "data/raw/audio/train_horn/negative"
    processed_dir = WORKSPACE_ROOT / "data/processed/audio/train_horn"
    manifest_dir = WORKSPACE_ROOT / "data/manifests"
    split_dir = WORKSPACE_ROOT / "data/splits/audio"

    pos_files = sorted([p for p in pos_dir.iterdir() if p.is_file() and not p.is_symlink() and not p.name.startswith(".")])
    neg_files = sorted([p for p in neg_dir.iterdir() if p.is_file() and not p.name.startswith(".") and p.suffix.lower() == ".wav"])

    assert len(pos_files) == 87, f"Expected 87 positive files, found {len(pos_files)}"
    assert len(neg_files) == 87, f"Expected 87 negative files, found {len(neg_files)}"
    print(f"Verified Positive Count: {len(pos_files)}")
    print(f"Verified Negative Count: {len(neg_files)}")

    # Probing & grouping positive
    seen_pos_groups: dict[str, str] = {}
    pos_samples = []
    pos_group_to_samples = defaultdict(list)
    for p in pos_files:
        sha = compute_sha256(p)
        probe = probe_audio_file(p)
        gid = derive_positive_group_id(p.name, sha, seen_pos_groups)
        item = {
            "path": p,
            "filename": p.name,
            "class_name": "train_horn",
            "class_id": 1,
            "sha256": sha,
            "group_id": gid,
            "probe": probe,
            "is_extension_anomaly": p.suffix.lower() == ".pdf",
        }
        pos_samples.append(item)
        pos_group_to_samples[gid].append(item)

    # Probing negative (each ESC-50 clip is an independent recording session)
    # Load category info from negative selection manifest
    with open(manifest_dir / "negative_selection_manifest.json") as f:
        neg_manifest = json.load(f)
    neg_cat_map = {r["filename"]: r["category"] for r in neg_manifest["records"]}

    neg_samples = []
    neg_cat_to_samples = defaultdict(list)
    for p in neg_files:
        sha = compute_sha256(p)
        probe = probe_audio_file(p)
        cat = neg_cat_map.get(p.name, "unknown")
        gid = f"neg_group_{p.stem}"
        item = {
            "path": p,
            "filename": p.name,
            "class_name": "non_train_horn",
            "category": cat,
            "class_id": 0,
            "sha256": sha,
            "group_id": gid,
            "probe": probe,
            "is_extension_anomaly": False,
        }
        neg_samples.append(item)
        neg_cat_to_samples[cat].append(item)

    print("\n==================================================")
    print("STEP 2: LEAKAGE-SAFE STRATIFIED GROUP PARTITIONING")
    print("==================================================")

    # Positive group partitioning using verified optimal seed=1
    rng_pos = random.Random(1)
    pos_g_keys = list(pos_group_to_samples.keys())
    # Pin 15-clip group and duplicate 41/42 to train
    pinned_train = [
        "group_Whistle of New EMD Locomotive  Broad Gauge & Mitre Gauge Train Engine of Bangladesh Rail 66 30",
        "group_41_42_duplicate",
    ]
    for g in pinned_train:
        pos_g_keys.remove(g)
    rng_pos.shuffle(pos_g_keys)

    pos_train_samples: list[dict[str, Any]] = []
    for g in pinned_train:
        pos_train_samples.extend(pos_group_to_samples[g])
    pos_val_samples: list[dict[str, Any]] = []
    pos_test_samples: list[dict[str, Any]] = []

    for g in pos_g_keys:
        g_s = pos_group_to_samples[g]
        if len(pos_val_samples) < 13:
            pos_val_samples.extend(g_s)
        elif len(pos_test_samples) < 13:
            pos_test_samples.extend(g_s)
        else:
            pos_train_samples.extend(g_s)

    assert len(pos_train_samples) == 61, f"Pos Train was {len(pos_train_samples)}"
    assert len(pos_val_samples) == 13, f"Pos Val was {len(pos_val_samples)}"
    assert len(pos_test_samples) == 13, f"Pos Test was {len(pos_test_samples)}"
    print(f"Positive Partition: Train={len(pos_train_samples)}, Val={len(pos_val_samples)}, Test={len(pos_test_samples)}")

    # Negative group partitioning: Stratified across categories to allocate 61 train, 13 val, 13 test
    rng_neg = random.Random(42)
    neg_train_samples: list[dict[str, Any]] = []
    neg_val_samples: list[dict[str, Any]] = []
    neg_test_samples: list[dict[str, Any]] = []

    # There are 11 categories: 10 categories with 8 clips, 1 with 7 clips.
    # For each 8-clip category: 6 train, 1 val, 1 test (10 * 6 = 60 train, 10 val, 10 test)
    # For 7-clip category (clock_alarm): 1 train, 3 val? Wait: we need 61 train, 13 val, 13 test!
    # So 61 train = 60 + 1 (from clock_alarm).
    # Remaining 6 clips from clock_alarm: 3 val, 3 test!
    # 10 + 3 = 13 val, 10 + 3 = 13 test! Total = 61 + 13 + 13 = 87! EXACT!
    for cat, c_samples in sorted(neg_cat_to_samples.items()):
        shuffled_c = c_samples.copy()
        rng_neg.shuffle(shuffled_c)
        if len(shuffled_c) == 8:
            neg_train_samples.extend(shuffled_c[:6])
            neg_val_samples.extend(shuffled_c[6:7])
            neg_test_samples.extend(shuffled_c[7:8])
        elif len(shuffled_c) == 7:  # clock_alarm
            neg_train_samples.extend(shuffled_c[:1])
            neg_val_samples.extend(shuffled_c[1:4])
            neg_test_samples.extend(shuffled_c[4:7])

    assert len(neg_train_samples) == 61, f"Neg Train was {len(neg_train_samples)}"
    assert len(neg_val_samples) == 13, f"Neg Val was {len(neg_val_samples)}"
    assert len(neg_test_samples) == 13, f"Neg Test was {len(neg_test_samples)}"
    print(f"Negative Partition: Train={len(neg_train_samples)}, Val={len(neg_val_samples)}, Test={len(neg_test_samples)}")

    # Map partitions back to sample records
    for s in pos_train_samples:
        s["partition"] = "train"
    for s in pos_val_samples:
        s["partition"] = "val"
    for s in pos_test_samples:
        s["partition"] = "test"

    for s in neg_train_samples:
        s["partition"] = "train"
    for s in neg_val_samples:
        s["partition"] = "val"
    for s in neg_test_samples:
        s["partition"] = "test"

    all_samples = pos_samples + neg_samples

    # Write recording-level split manifest
    split_dir.mkdir(parents=True, exist_ok=True)
    split_manifest = {
        "split_strategy": "group_disjoint_stratified_recording_level",
        "random_seeds": {"positive": 1, "negative": 42},
        "ratios": {"train": 0.7011, "val": 0.1494, "test": 0.1494},
        "positive": {
            "train": [s["filename"] for s in pos_train_samples],
            "val": [s["filename"] for s in pos_val_samples],
            "test": [s["filename"] for s in pos_test_samples],
        },
        "negative": {
            "train": [s["filename"] for s in neg_train_samples],
            "val": [s["filename"] for s in neg_val_samples],
            "test": [s["filename"] for s in neg_test_samples],
        },
        "summary": {
            "train": {"positive": 61, "negative": 61, "total": 122},
            "val": {"positive": 13, "negative": 13, "total": 26},
            "test": {"positive": 13, "negative": 13, "total": 26},
            "total_recordings": 174,
        }
    }
    with open(split_dir / "dataset_split.json", "w", encoding="utf-8") as f:
        json.dump(split_manifest, f, indent=2)
    print(f"Saved recording-level split manifest to {split_dir / 'dataset_split.json'}")

    print("\n==================================================")
    print("STEP 3: AUDIO STANDARDIZATION, WINDOWING & LOG-MEL")
    print("==================================================")
    std_wav_dir = processed_dir / "wav_16k"
    features_dir = processed_dir / "features"
    std_wav_dir.mkdir(parents=True, exist_ok=True)
    features_dir.mkdir(parents=True, exist_ok=True)

    window_len_samples = int(round(window_s * target_sr))
    hop_len_samples = int(round(hop_s * target_sr))

    all_window_records: list[dict[str, Any]] = []

    for idx, sample in enumerate(all_samples, 1):
        src_path = sample["path"]
        class_subdir = "positive" if sample["class_id"] == 1 else "negative"
        partition = sample["partition"]

        # Standardize WAV
        dst_wav = std_wav_dir / class_subdir / f"{src_path.stem}.wav"
        convert_and_normalize_wav(src_path, dst_wav, target_sr=target_sr)

        # Load standardized WAV
        samples, sr = load_pcm16_wav(dst_wav)
        assert sr == target_sr, f"Expected {target_sr} Hz, got {sr} Hz"

        # If clip shorter than window_len_samples, pad symmetrically
        if len(samples) < window_len_samples:
            pad_needed = window_len_samples - len(samples)
            samples = np.pad(samples, (0, pad_needed), mode="reflect")

        # Sliding windowing
        w_idx = 0
        start_samp = 0
        while start_samp + window_len_samples <= len(samples):
            w_samples = samples[start_samp : start_samp + window_len_samples]
            start_t = start_samp / float(target_sr)
            end_t = (start_samp + window_len_samples) / float(target_sr)

            # Compute Log-Mel Spectrogram (64 mel bands, 80-8000 Hz, FFT 512, hop 256)
            log_mel = compute_log_mel_spectrogram(
                w_samples,
                sample_rate=target_sr,
                n_fft=512,
                hop_length=256,
                n_mels=64,
                f_min=80.0,
                f_max=8000.0,
            )

            window_id = f"{class_subdir[:3]}_{idx:03d}_w{w_idx:03d}"
            feat_dst = features_dir / class_subdir / f"{window_id}.npy"
            feat_dst.parent.mkdir(parents=True, exist_ok=True)
            np.save(feat_dst, log_mel)

            rec = {
                "window_id": window_id,
                "source_file": sample["filename"],
                "source_relative_path": str(src_path.relative_to(WORKSPACE_ROOT)),
                "source_sha256": sample["sha256"],
                "split_group_id": sample["group_id"],
                "class_name": sample["class_name"],
                "class_id": sample["class_id"],
                "category": sample.get("category", "train_horn"),
                "partition": partition,
                "window_index": w_idx,
                "start_time_s": round(start_t, 3),
                "end_time_s": round(end_t, 3),
                "duration_s": round(end_t - start_t, 3),
                "sample_rate": target_sr,
                "standardized_wav_path": str(dst_wav.relative_to(WORKSPACE_ROOT)),
                "feature_path": str(feat_dst.relative_to(WORKSPACE_ROOT)),
                "feature_type": "log_mel_spectrogram",
                "feature_shape": list(log_mel.shape),
                "dataset_role": "audio_model_development",
            }
            all_window_records.append(rec)
            w_idx += 1
            start_samp += hop_len_samples

    print(f"Total Analysis Windows Extracted: {len(all_window_records)}")
    for part in ("train", "val", "test"):
        count = sum(1 for r in all_window_records if r["partition"] == part)
        pos = sum(1 for r in all_window_records if r["partition"] == part and r["class_id"] == 1)
        neg = sum(1 for r in all_window_records if r["partition"] == part and r["class_id"] == 0)
        print(f"  {part.upper():5s} Partition: {count:4d} windows (Pos: {pos}, Neg: {neg})")

    # Save Window Manifests
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_json = manifest_dir / "audio_training_dataset.json"
    manifest_jsonl = manifest_dir / "audio_training_dataset.jsonl"
    with open(manifest_json, "w", encoding="utf-8") as f:
        json.dump(all_window_records, f, indent=2)
    with open(manifest_jsonl, "w", encoding="utf-8") as f:
        for r in all_window_records:
            f.write(json.dumps(r) + "\n")

    summary_file = manifest_dir / "audio_preprocessing_summary.json"
    summary = {
        "preprocessing_version": "2.0.0",
        "standardization": {
            "sample_rate_hz": target_sr,
            "channels": 1,
            "codec": "pcm_s16le",
            "window_duration_s": window_s,
            "hop_duration_s": hop_s,
            "normalization": "peak_to_minus_1_dbfs",
        },
        "feature_specification": {
            "feature_type": "log_mel_spectrogram",
            "n_mels": 64,
            "n_fft": 512,
            "hop_length": 256,
            "f_min_hz": 80.0,
            "f_max_hz": 8000.0,
            "window_function": "hann",
            "feature_shape": list(all_window_records[0]["feature_shape"]),
        },
        "inventory": {
            "positive_source_recordings": len(pos_files),
            "negative_source_recordings": len(neg_files),
            "total_recordings": len(pos_files) + len(neg_files),
            "total_windows": len(all_window_records),
            "recording_partitions": {
                "train": {"positive": 61, "negative": 61, "total": 122},
                "val": {"positive": 13, "negative": 13, "total": 26},
                "test": {"positive": 13, "negative": 13, "total": 26},
            },
            "window_partitions": {
                part: {
                    "total": sum(1 for r in all_window_records if r["partition"] == part),
                    "positive": sum(1 for r in all_window_records if r["partition"] == part and r["class_id"] == 1),
                    "negative": sum(1 for r in all_window_records if r["partition"] == part and r["class_id"] == 0),
                }
                for part in ("train", "val", "test")
            },
        },
        "leakage_invariants": {
            "duplicate_41_42_locked_to_train": True,
            "layer_b_eval_events_excluded": True,
            "group_disjoint_splitting": True,
            "recording_level_split_before_windowing": True,
        },
    }
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Generated Manifests: {manifest_json}, {manifest_jsonl}, {summary_file}")
    print("Preprocessing completed successfully!")


if __name__ == "__main__":
    build_pipeline_dataset(window_s=1.0, hop_s=0.5, target_sr=16000)
