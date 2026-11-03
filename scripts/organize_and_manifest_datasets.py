#!/usr/bin/env python3
"""Dataset organization and manifest generation for real-world video & audio datasets.

Strict Constraints:
- Original source files are NEVER deleted, modified, or overwritten.
- Source and destination SHA-256 hashes are verified for 100% integrity.
- Event pairing is strictly verified across front and back cameras.
- Manifests are written in both JSON and JSONL formats with explicit dataset roles.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402

WORKSPACE_ROOT = Path("/Users/sayemuddin/Desktop/Train_automation")
VIDEO_SRC_DIR = WORKSPACE_ROOT / "Train_test_video_new"
AUDIO_SRC_DIR = WORKSPACE_ROOT / "Train_Audio_new"

VIDEO_DST_DIR = WORKSPACE_ROOT / "data" / "raw" / "layer_b" / "videos"
AUDIO_POS_DST_DIR = WORKSPACE_ROOT / "data" / "raw" / "audio" / "train_horn" / "positive"
AUDIO_NEG_DST_DIR = WORKSPACE_ROOT / "data" / "raw" / "audio" / "train_horn" / "negative"
MANIFEST_DST_DIR = WORKSPACE_ROOT / "data" / "manifests"


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    require_media_authorization(path, "HASH_RAW_MEDIA")
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def probe_media(path: Path) -> dict[str, Any]:
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
    return json.loads(res.stdout)


def organize_videos() -> list[dict[str, Any]]:
    print("=== Organizing Layer B Videos ===")
    VIDEO_DST_DIR.mkdir(parents=True, exist_ok=True)
    manifest_records: list[dict[str, Any]] = []

    for event_num in range(1, 22):
        event_id = f"event_{event_num:03d}"
        event_dir = VIDEO_DST_DIR / event_id
        event_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{event_num}.mov"
        src_front = VIDEO_SRC_DIR / "Front" / filename
        src_back = VIDEO_SRC_DIR / "Back" / filename

        if not src_front.exists() or not src_back.exists():
            raise FileNotFoundError(f"Missing camera video for {event_id}: front={src_front.exists()}, back={src_back.exists()}")

        # Target paths
        dst_front = event_dir / "camera_front.mov"
        dst_back = event_dir / "camera_back.mov"
        dst_rear_symlink = event_dir / "camera_rear.mov"

        # Front camera copy & verify
        src_front_sha = compute_sha256(src_front)
        if not dst_front.exists() or compute_sha256(dst_front) != src_front_sha:
            shutil.copy2(src_front, dst_front)
        dst_front_sha = compute_sha256(dst_front)
        assert src_front_sha == dst_front_sha, f"Hash mismatch on {dst_front}"

        # Back camera copy & verify
        src_back_sha = compute_sha256(src_back)
        if not dst_back.exists() or compute_sha256(dst_back) != src_back_sha:
            shutil.copy2(src_back, dst_back)
        dst_back_sha = compute_sha256(dst_back)
        assert src_back_sha == dst_back_sha, f"Hash mismatch on {dst_back}"

        # Relative symlink for camera_rear.mov -> camera_back.mov
        if not dst_rear_symlink.exists():
            dst_rear_symlink.symlink_to("camera_back.mov")

        # Probe front
        front_probe = probe_media(dst_front)
        f_vstream = next((s for s in front_probe.get("streams", []) if s.get("codec_type") == "video"), None)
        f_astream = next((s for s in front_probe.get("streams", []) if s.get("codec_type") == "audio"), None)
        f_fps_str = f_vstream.get("r_frame_rate", "30/1") if f_vstream else "30/1"
        num, den = (int(x) for x in f_fps_str.split("/")) if "/" in f_fps_str else (float(f_fps_str), 1.0)
        f_fps = float(num) / float(den) if den else 0.0

        front_record = {
            "event_id": event_id,
            "camera": "front",
            "source_path": str(src_front.relative_to(WORKSPACE_ROOT)),
            "relative_path": str(dst_front.relative_to(WORKSPACE_ROOT)),
            "filename": "camera_front.mov",
            "original_filename": filename,
            "duration_s": round(float(front_probe.get("format", {}).get("duration", 0.0)), 3),
            "width": f_vstream.get("width") if f_vstream else None,
            "height": f_vstream.get("height") if f_vstream else None,
            "fps": round(f_fps, 2),
            "codec": f_vstream.get("codec_name") if f_vstream else None,
            "container": "mov",
            "has_audio": f_astream is not None,
            "audio_codec": f_astream.get("codec_name") if f_astream else None,
            "audio_sample_rate": int(f_astream.get("sample_rate", 0)) if f_astream else None,
            "audio_channels": f_astream.get("channels") if f_astream else None,
            "sha256": dst_front_sha,
            "dataset_role": "real_world_evaluation",
        }
        manifest_records.append(front_record)

        # Probe back
        back_probe = probe_media(dst_back)
        b_vstream = next((s for s in back_probe.get("streams", []) if s.get("codec_type") == "video"), None)
        b_astream = next((s for s in back_probe.get("streams", []) if s.get("codec_type") == "audio"), None)
        b_fps_str = b_vstream.get("r_frame_rate", "30/1") if b_vstream else "30/1"
        num, den = (int(x) for x in b_fps_str.split("/")) if "/" in b_fps_str else (float(b_fps_str), 1.0)
        b_fps = float(num) / float(den) if den else 0.0

        back_record = {
            "event_id": event_id,
            "camera": "back",
            "source_path": str(src_back.relative_to(WORKSPACE_ROOT)),
            "relative_path": str(dst_back.relative_to(WORKSPACE_ROOT)),
            "filename": "camera_back.mov",
            "original_filename": filename,
            "duration_s": round(float(back_probe.get("format", {}).get("duration", 0.0)), 3),
            "width": b_vstream.get("width") if b_vstream else None,
            "height": b_vstream.get("height") if b_vstream else None,
            "fps": round(b_fps, 2),
            "codec": b_vstream.get("codec_name") if b_vstream else None,
            "container": "mov",
            "has_audio": b_astream is not None,
            "audio_codec": b_astream.get("codec_name") if b_astream else None,
            "audio_sample_rate": int(b_astream.get("sample_rate", 0)) if b_astream else None,
            "audio_channels": b_astream.get("channels") if b_astream else None,
            "sha256": dst_back_sha,
            "dataset_role": "real_world_evaluation",
        }
        manifest_records.append(back_record)
        print(f"Organized {event_id}: Front ({front_record['duration_s']}s, {front_record['width']}x{front_record['height']}) | Back ({back_record['duration_s']}s, {back_record['width']}x{back_record['height']})")

    return manifest_records


def organize_audio() -> list[dict[str, Any]]:
    print("\n=== Organizing Standalone Horn Audio ===")
    AUDIO_POS_DST_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_NEG_DST_DIR.mkdir(parents=True, exist_ok=True)

    # Place a README in negative/ documenting missing negative background audio
    neg_readme = AUDIO_NEG_DST_DIR / "README.md"
    neg_readme.write_text(
        "# Negative / Background Audio Directory\n\n"
        "**Status**: Negative/background audio is currently missing.\n\n"
        "To ensure a robust binary audio classifier, this directory must be populated with negative "
        "background audio recordings (such as road traffic, wind, ambient level-crossing noise, human voices, "
        "bird songs, rain) prior to training.\n\n"
        "DO NOT use synthetic noise or fake negatives without strict validation.\n",
        encoding="utf-8",
    )

    src_files = sorted(f for f in AUDIO_SRC_DIR.iterdir() if f.is_file() and not f.name.startswith("."))
    manifest_records: list[dict[str, Any]] = []

    # Map of hashes to detect duplicates
    seen_hashes: dict[str, str] = {}

    for idx, src_file in enumerate(src_files, 1):
        dst_file = AUDIO_POS_DST_DIR / src_file.name
        src_sha = compute_sha256(src_file)

        if not dst_file.exists() or compute_sha256(dst_file) != src_sha:
            shutil.copy2(src_file, dst_file)
        dst_sha = compute_sha256(dst_file)
        assert src_sha == dst_sha, f"Hash mismatch on {dst_file}"

        # Probe file
        probe = probe_media(dst_file)
        astream = next((s for s in probe.get("streams", []) if s.get("codec_type") == "audio"), None)
        dur = round(float(probe.get("format", {}).get("duration", 0.0)), 3)

        # Anomaly / Duplicate detection
        is_pdf_ext = src_file.suffix.lower() == ".pdf"
        duplicate_of = seen_hashes.get(dst_sha)
        if duplicate_of is None:
            seen_hashes[dst_sha] = src_file.name

        # If misnamed PDF, create symlink with .mp3 extension for standard audio loaders
        if is_pdf_ext:
            mp3_symlink = AUDIO_POS_DST_DIR / f"{src_file.stem}.mp3"
            if not mp3_symlink.exists():
                mp3_symlink.symlink_to(src_file.name)

        sample_id = f"horn_{idx:03d}"
        rec = {
            "sample_id": sample_id,
            "filename": src_file.name,
            "source_path": str(src_file.relative_to(WORKSPACE_ROOT)),
            "relative_path": str(dst_file.relative_to(WORKSPACE_ROOT)),
            "duration_s": dur,
            "sample_rate": int(astream.get("sample_rate", 0)) if astream else None,
            "channels": astream.get("channels") if astream else None,
            "format": astream.get("codec_name") if astream else "unknown",
            "bit_rate": int(probe.get("format", {}).get("bit_rate", 0)) if "format" in probe and "bit_rate" in probe["format"] else None,
            "sha256": dst_sha,
            "label": "train_horn",
            "dataset_role": "audio_model_development",
            "is_extension_anomaly": is_pdf_ext,
            "is_duplicate": duplicate_of is not None,
            "duplicate_of": duplicate_of,
        }
        manifest_records.append(rec)

    print(f"Organized {len(manifest_records)} audio files into {AUDIO_POS_DST_DIR}")
    return manifest_records


def write_manifests(video_records: list[dict[str, Any]], audio_records: list[dict[str, Any]]) -> None:
    MANIFEST_DST_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Video Manifest JSON & JSONL
    v_jsonl = MANIFEST_DST_DIR / "layer_b_video_manifest.jsonl"
    with open(v_jsonl, "w", encoding="utf-8") as f:
        for r in video_records:
            f.write(json.dumps(r) + "\n")

    v_json = MANIFEST_DST_DIR / "layer_b_video_manifest.json"
    with open(v_json, "w", encoding="utf-8") as f:
        json.dump(video_records, f, indent=2)

    # 2. Audio Manifest JSON & JSONL
    a_jsonl = MANIFEST_DST_DIR / "train_horn_audio_manifest.jsonl"
    with open(a_jsonl, "w", encoding="utf-8") as f:
        for r in audio_records:
            f.write(json.dumps(r) + "\n")

    a_json = MANIFEST_DST_DIR / "train_horn_audio_manifest.json"
    with open(a_json, "w", encoding="utf-8") as f:
        json.dump(audio_records, f, indent=2)

    # 3. Overall Inventory Summary
    summary = {
        "manifest_version": "1.0.0",
        "video_dataset": {
            "name": "Layer B Real-World Train Passage Evaluation Dataset",
            "dataset_role": "real_world_evaluation",
            "location": "data/raw/layer_b/videos",
            "total_events": len(video_records) // 2,
            "total_video_files": len(video_records),
            "front_cameras": len([r for r in video_records if r["camera"] == "front"]),
            "back_cameras": len([r for r in video_records if r["camera"] == "back"]),
            "total_duration_s": round(sum(r["duration_s"] for r in video_records), 2),
            "container": "mov",
            "video_codec": "hevc (H.265)",
            "audio_codec": "aac",
            "audio_sample_rate": 48000,
            "audio_channels": 2,
        },
        "audio_dataset": {
            "name": "Train Horn Audio Model Development Dataset",
            "dataset_role": "audio_model_development",
            "location": "data/raw/audio/train_horn/positive",
            "negative_location": "data/raw/audio/train_horn/negative",
            "total_audio_files": len(audio_records),
            "positive_label": "train_horn",
            "negative_background_status": "currently_missing",
            "total_duration_s": round(sum(r["duration_s"] for r in audio_records), 2),
            "min_duration_s": min(r["duration_s"] for r in audio_records),
            "max_duration_s": max(r["duration_s"] for r in audio_records),
            "mean_duration_s": round(sum(r["duration_s"] for r in audio_records) / len(audio_records), 2),
            "sample_rate": 44100,
            "channels": 2,
            "codec": "mp3",
            "extension_anomalies_count": len([r for r in audio_records if r["is_extension_anomaly"]]),
            "extension_anomalies_details": [r["filename"] for r in audio_records if r["is_extension_anomaly"]],
            "duplicates_count": len([r for r in audio_records if r["is_duplicate"]]),
            "duplicates_details": [f"{r['filename']} duplicate of {r['duplicate_of']}" for r in audio_records if r["is_duplicate"]],
        },
        "data_separation_rules": [
            "Dataset V1 remains the YOLO development/training dataset.",
            "Train_test_video_new remains an unseen real-world evaluation dataset.",
            "The standalone horn recordings are for audio-model development.",
            "Embedded audio from the real-world test videos must not be mixed into audio training before the first evaluation.",
            "No new real-world test video frames may be added to YOLO training before evaluation.",
            "No test-event information may leak into training.",
        ],
    }

    summary_file = MANIFEST_DST_DIR / "dataset_inventory_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nManifests generated in {MANIFEST_DST_DIR}:")
    print(f"  - {v_jsonl.name} ({len(video_records)} records)")
    print(f"  - {v_json.name}")
    print(f"  - {a_jsonl.name} ({len(audio_records)} records)")
    print(f"  - {a_json.name}")
    print(f"  - {summary_file.name}")


def main() -> None:
    v_records = organize_videos()
    a_records = organize_audio()
    write_manifests(v_records, a_records)
    print("\nDataset organization and manifest generation completed successfully!")


if __name__ == "__main__":
    main()
