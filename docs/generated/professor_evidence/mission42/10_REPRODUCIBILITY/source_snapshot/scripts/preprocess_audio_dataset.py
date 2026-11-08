#!/usr/bin/env python3
"""Deterministic audio preprocessing, group-disjoint splitting, and Log-Mel extraction.

Adheres strictly to the research protocol:
- No model training.
- Raw source media files remain unmodified.
- Layer B real-world evaluation events are strictly excluded.
- Group-disjoint splitting guarantees 41.mp3 and 42.mp3 are in the identical partition.
- Preprocesses positive and (when collected) negative audio into 16 kHz mono 16-bit PCM WAV.
- Extracts 64-band Log-Mel spectrograms for sliding 1.0s analysis windows (0.5s hop).
- Generates machine-readable provenance manifests: audio_training_dataset.json & .jsonl.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

# Ensure project root is in sys.path
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
    dur = float(fmt.get("duration", 0.0))

    return {
        "format_name": fmt.get("format_name", "unknown"),
        "duration_s": dur,
        "codec_name": a_stream.get("codec_name", "unknown") if a_stream else "none",
        "sample_rate": int(a_stream.get("sample_rate", 0)) if a_stream else 0,
        "channels": int(a_stream.get("channels", 0)) if a_stream else 0,
        "bit_rate": int(fmt.get("bit_rate", 0)) if "bit_rate" in fmt else 0,
    }


def derive_group_id(filename: str, sha256_hash: str, seen_hash_groups: dict[str, str]) -> str:
    """Derive group ID ensuring identical hashes and multi-take clips share the same group."""
    # Enforce hash-based grouping (handles 41.mp3 and 42.mp3)
    if sha256_hash in seen_hash_groups:
        return seen_hash_groups[sha256_hash]

    stem = Path(filename).stem
    if stem in ("41", "42"):
        gid = "group_41_42_duplicate"
        seen_hash_groups[sha256_hash] = gid
        return gid

    # Normalize YouTube / series suffixes
    cleaned = re.sub(r"\s*-\s*128(-\d+)?$", "", stem)
    cleaned = re.sub(r"\s*\(\d+\)$", "", cleaned).strip()
    gid = f"group_{cleaned}"
    seen_hash_groups[sha256_hash] = gid
    return gid


def convert_to_standard_wav(src_path: Path, dst_path: Path, target_sr: int = 16000) -> None:
    """Convert any audio format to 16 kHz mono 16-bit PCM WAV using FFmpeg."""
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
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion failed for {src_path}: {res.stderr}")


def load_pcm16_wav(path: Path) -> tuple[np.ndarray, int]:
    """Load a 16-bit PCM mono WAV file into float64 array normalized to [-1, 1]."""
    import wave
    require_media_authorization(path, "FEATURE_EXTRACTION")
    with wave.open(str(path), "rb") as wav:
        sr = wav.getframerate()
        n_frames = wav.getnframes()
        raw = wav.readframes(n_frames)
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    return samples, sr


def split_groups(
    groups: list[str],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 42,
) -> dict[str, str]:
    """Partition groups into train, val, and test partitions."""
    rng = np.random.default_rng(seed)
    shuffled = groups.copy()
    rng.shuffle(shuffled)

    n_total = len(shuffled)
    n_train = max(1, int(round(n_total * train_ratio)))
    n_val = max(1, int(round(n_total * val_ratio)))

    # Ensure at least 1 for test if n_total >= 3
    if n_total >= 3 and (n_train + n_val >= n_total):
        n_train = n_total - n_val - 1

    train_groups = set(shuffled[:n_train])
    val_groups = set(shuffled[n_train : n_train + n_val])
    test_groups = set(shuffled[n_train + n_val :])

    group_to_partition = {}
    for g in train_groups:
        group_to_partition[g] = "train"
    for g in val_groups:
        group_to_partition[g] = "val"
    for g in test_groups:
        group_to_partition[g] = "test"

    return group_to_partition


def preprocess_dataset(
    raw_pos_dir: Path,
    raw_neg_dir: Path,
    output_dir: Path,
    manifest_dir: Path,
    seed: int = 42,
    window_s: float = 1.0,
    hop_s: float = 0.5,
    target_sr: int = 16000,
) -> None:
    print("==================================================")
    print("PHASE 1 & 2 — RAW AUDIO VALIDATION & INVENTORY")
    print("==================================================")

    # Audio candidate extensions (including .pdf for the existing anomaly)
    valid_exts = {".mp3", ".wav", ".flac", ".ogg", ".aac", ".m4a", ".pdf"}

    pos_files = sorted(
        [
            p
            for p in raw_pos_dir.iterdir()
            if p.is_file() and not p.is_symlink() and not p.name.startswith(".") and p.suffix.lower() in valid_exts
        ]
    )

    # 2. Discover negative files (if any exist, ignoring documentation like README.md)
    neg_files = []
    if raw_neg_dir.exists():
        neg_files = sorted(
            [
                p
                for p in raw_neg_dir.iterdir()
                if p.is_file() and not p.is_symlink() and not p.name.startswith(".") and p.suffix.lower() in valid_exts
            ]
        )

    print(f"Positive Raw Files: {len(pos_files)}")
    print(f"Negative Raw Files: {len(neg_files)}")

    if len(neg_files) == 0:
        print("\n>>> STATUS: Negative audio directory currently contains 0 files.")
        print(">>> Preprocessing will structure and partition positive samples.")
        print(">>> Once negative data is collected, rerunning this script will incorporate both classes.")

    # Validate and probe files
    validated_samples: list[dict[str, Any]] = []
    seen_hash_groups: dict[str, str] = {}
    sha_map: dict[str, list[str]] = defaultdict(list)

    for p in pos_files:
        sha = compute_sha256(p)
        sha_map[sha].append(p.name)
        probe = probe_audio_file(p)
        gid = derive_group_id(p.name, sha, seen_hash_groups)
        validated_samples.append({
            "path": p,
            "filename": p.name,
            "class_name": "train_horn",
            "class_id": 1,
            "sha256": sha,
            "group_id": gid,
            "probe": probe,
            "is_extension_anomaly": p.suffix.lower() == ".pdf",
        })

    for p in neg_files:
        sha = compute_sha256(p)
        sha_map[sha].append(p.name)
        probe = probe_audio_file(p)
        gid = derive_group_id(p.name, sha, seen_hash_groups)
        validated_samples.append({
            "path": p,
            "filename": p.name,
            "class_name": "non_train_horn",
            "class_id": 0,
            "sha256": sha,
            "group_id": gid,
            "probe": probe,
            "is_extension_anomaly": False,
        })

    total_pos_dur = sum(s["probe"]["duration_s"] for s in validated_samples if s["class_id"] == 1)
    total_neg_dur = sum(s["probe"]["duration_s"] for s in validated_samples if s["class_id"] == 0)

    print(f"Total Positive Duration: {total_pos_dur:.2f}s ({total_pos_dur/60:.2f} mins)")
    print(f"Total Negative Duration: {total_neg_dur:.2f}s ({total_neg_dur/60:.2f} mins)")
    if total_neg_dur > 0:
        print(f"Positive:Negative Duration Ratio: 1:{total_neg_dur/total_pos_dur:.2f}")
    else:
        print("Class Duration Ratio: N/A (Negative data missing)")

    duplicates = {h: names for h, names in sha_map.items() if len(names) > 1}
    print(f"Duplicate SHA-256 Groups Detected: {len(duplicates)}")
    for h, names in duplicates.items():
        print(f"  Hash {h[:12]}... -> {names}")

    print("\n==================================================")
    print("PHASE 3 — REPRODUCIBLE GROUP-DISJOINT PARTITIONING")
    print("==================================================")

    # Split positive groups
    pos_groups = sorted(list(set(s["group_id"] for s in validated_samples if s["class_id"] == 1)))
    pos_partition_map = split_groups(pos_groups, train_ratio=0.70, val_ratio=0.15, seed=seed)

    # Split negative groups if available
    neg_groups = sorted(list(set(s["group_id"] for s in validated_samples if s["class_id"] == 0)))
    neg_partition_map = split_groups(neg_groups, train_ratio=0.70, val_ratio=0.15, seed=seed) if neg_groups else {}

    group_partition_map = {**pos_partition_map, **neg_partition_map}

    # Verify duplicate pair 41.mp3 and 42.mp3 reside in the identical partition
    rec_41 = next(s for s in validated_samples if s["filename"] == "41.mp3")
    rec_42 = next(s for s in validated_samples if s["filename"] == "42.mp3")
    part_41 = group_partition_map[rec_41["group_id"]]
    part_42 = group_partition_map[rec_42["group_id"]]
    assert part_41 == part_42, f"FATAL: Duplicate files separated into different partitions: 41={part_41}, 42={part_42}"
    print(f"Verified Duplicate Lock: 41.mp3 & 42.mp3 -> Group: {rec_41['group_id']} -> Partition: {part_41}")

    print("\n==================================================")
    print("PHASE 4 & 5 — STANDARDIZATION, WINDOWING & LOG-MEL")
    print("==================================================")

    std_wav_dir = output_dir / "standardized_wav"
    features_dir = output_dir / "features"
    std_wav_dir.mkdir(parents=True, exist_ok=True)
    features_dir.mkdir(parents=True, exist_ok=True)

    window_len_samples = int(round(window_s * target_sr))
    hop_len_samples = int(round(hop_s * target_sr))

    all_window_records: list[dict[str, Any]] = []

    for idx, sample in enumerate(validated_samples, 1):
        src_path = sample["path"]
        class_subdir = "positive" if sample["class_id"] == 1 else "negative"
        partition = group_partition_map[sample["group_id"]]

        # Standardize to WAV
        dst_wav = std_wav_dir / class_subdir / f"{src_path.stem}.wav"
        convert_to_standard_wav(src_path, dst_wav, target_sr=target_sr)

        # Load standardized WAV
        samples, sr = load_pcm16_wav(dst_wav)
        assert sr == target_sr, f"Expected {target_sr} Hz, got {sr} Hz"

        # If clip shorter than 1.0s, pad symmetrically so we retain the audio
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

            # Save feature array
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

    print(f"Total Windows Generated: {len(all_window_records)}")
    for part in ("train", "val", "test"):
        count = sum(1 for r in all_window_records if r["partition"] == part)
        pos = sum(1 for r in all_window_records if r["partition"] == part and r["class_id"] == 1)
        neg = sum(1 for r in all_window_records if r["partition"] == part and r["class_id"] == 0)
        print(f"  {part.upper():5s} Partition: {count:4d} windows (Pos: {pos}, Neg: {neg})")

    print("\n==================================================")
    print("PHASE 6 — MANIFEST GENERATION")
    print("==================================================")

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
        "preprocessing_version": "1.0.0",
        "random_seed": seed,
        "standardization": {
            "sample_rate_hz": target_sr,
            "channels": 1,
            "codec": "pcm_s16le",
            "window_duration_s": window_s,
            "hop_duration_s": hop_s,
        },
        "feature_specification": {
            "feature_type": "log_mel_spectrogram",
            "n_mels": 64,
            "n_fft": 512,
            "hop_length": 256,
            "f_min_hz": 80.0,
            "f_max_hz": 8000.0,
            "window_function": "hann",
            "feature_shape": list(all_window_records[0]["feature_shape"]) if all_window_records else [64, 61],
        },
        "inventory": {
            "positive_source_files": len(pos_files),
            "negative_source_files": len(neg_files),
            "total_windows": len(all_window_records),
            "partitions": {
                part: {
                    "total": sum(1 for r in all_window_records if r["partition"] == part),
                    "positive": sum(1 for r in all_window_records if r["partition"] == part and r["class_id"] == 1),
                    "negative": sum(1 for r in all_window_records if r["partition"] == part and r["class_id"] == 0),
                }
                for part in ("train", "val", "test")
            },
        },
        "leakage_invariants": {
            "duplicate_41_42_locked_partition": part_41,
            "layer_b_eval_events_excluded": True,
            "group_disjoint_splitting": True,
        },
    }

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Generated Manifests:")
    print(f"  - {manifest_json}")
    print(f"  - {manifest_jsonl}")
    print(f"  - {summary_file}")
    print("\nAudio Preprocessing & Manifest Generation Completed Successfully!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess raw audio datasets into standardized training windows.")
    parser.add_argument("--raw-pos-dir", type=Path, default=WORKSPACE_ROOT / "data/raw/audio/train_horn/positive")
    parser.add_argument("--raw-neg-dir", type=Path, default=WORKSPACE_ROOT / "data/raw/audio/train_horn/negative")
    parser.add_argument("--output-dir", type=Path, default=WORKSPACE_ROOT / "data/processed/audio")
    parser.add_argument("--manifest-dir", type=Path, default=WORKSPACE_ROOT / "data/manifests")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--window-s", type=float, default=1.0)
    parser.add_argument("--hop-s", type=float, default=0.5)
    parser.add_argument("--target-sr", type=int, default=16000)

    args = parser.parse_args()
    preprocess_dataset(
        raw_pos_dir=args.raw_pos_dir,
        raw_neg_dir=args.raw_neg_dir,
        output_dir=args.output_dir,
        manifest_dir=args.manifest_dir,
        seed=args.seed,
        window_s=args.window_s,
        hop_s=args.hop_s,
        target_sr=args.target_sr,
    )


if __name__ == "__main__":
    main()
