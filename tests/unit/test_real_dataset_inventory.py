"""Unit tests verifying real-world dataset inventory, organization, and manifests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from railway_detection.data.layer_b import load_event_bundle

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
MANIFESTS_DIR = WORKSPACE_ROOT / "data" / "manifests"
LAYER_B_V2_DIR = WORKSPACE_ROOT / "data" / "raw" / "layer_b" / "v2"
V2_VIDEO_MANIFEST_PATH = MANIFESTS_DIR / "real_world_v2_video_manifest.json"
HISTORICAL_V1_DELETION_MANIFEST = WORKSPACE_ROOT / "docs" / "archive" / "OLD_TEST_DATA_DELETION_MANIFEST.md"
AUDIO_DIR = WORKSPACE_ROOT / "data" / "raw" / "audio" / "train_horn" / "positive"
AUDIO_NEG_DIR = WORKSPACE_ROOT / "data" / "raw" / "audio" / "train_horn" / "negative"


def test_video_manifest_integrity():
    """Validate the active Layer B V2 video manifest schema, counts, and media attributes."""
    assert V2_VIDEO_MANIFEST_PATH.exists(), "real_world_v2_video_manifest.json must exist"

    with open(V2_VIDEO_MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["version"] == "2.0.0"
    assert manifest["total_records"] == 56

    summary = manifest["summary"]
    assert summary["train_events"] == 23
    assert summary["engine_events_eligible"] == 1
    assert summary["engine_events_historical_duplicate"] == 1
    assert summary["no_train_events"] == 3
    assert summary["total_video_files"] == 56

    records = manifest["records"]
    assert len(records) == 56

    front_records = [r for r in records if r["camera_id"] == "front"]
    back_records = [r for r in records if r["camera_id"] == "back"]
    assert len(front_records) == 28
    assert len(back_records) == 28

    eligible_records = [r for r in records if r["evaluation_eligible"] is True]
    assert len(eligible_records) == 54  # 27 active evaluation events * 2 cameras

    duplicate_records = [r for r in records if r["evaluation_eligible"] is False]
    assert len(duplicate_records) == 2
    for r in duplicate_records:
        assert r["event_id"] == "event_historical_duplicate_010"
        assert r["dataset_role"] == "HISTORICAL_DUPLICATE_EXCLUDED"

    for r in records:
        assert r["has_audio"] is True
        assert r["audio_codec"] == "aac"
        assert r["audio_sample_rate"] == 48000
        assert r["codec"] in ("hevc", "h264")
        assert len(r["sha256"]) == 64
        dst_path = WORKSPACE_ROOT / r["destination_path"]
        assert dst_path.exists(), f"Destination video {dst_path} does not exist"
        assert dst_path.stat().st_size > 0

    # Verify historical V1 retirement is documented
    assert HISTORICAL_V1_DELETION_MANIFEST.exists(), "OLD_TEST_DATA_DELETION_MANIFEST.md must be preserved in docs/archive/"


def test_audio_manifest_integrity():
    manifest_path = MANIFESTS_DIR / "train_horn_audio_manifest.json"
    assert manifest_path.exists(), "train_horn_audio_manifest.json must exist"

    with open(manifest_path, encoding="utf-8") as f:
        records = json.load(f)

    assert len(records) == 87, f"Expected 87 audio records, found {len(records)}"

    for r in records:
        assert r["dataset_role"] == "audio_model_development"
        assert r["label"] == "train_horn"
        assert r["sample_rate"] == 44100
        assert r["channels"] == 2
        assert r["duration_s"] > 0
        dst_path = WORKSPACE_ROOT / r["relative_path"]
        assert dst_path.exists(), f"Audio file {dst_path} does not exist"


def test_layer_b_event_bundles_loadable():
    """Verify that all 28 Layer B V2 event bundles are discoverable, readable, and loadable."""
    assert LAYER_B_V2_DIR.is_dir(), "data/raw/layer_b/v2 must exist"

    categories = {
        "train_events": 23,
        "engine_events": 2,
        "no_train_events": 3,
    }

    total_bundles = 0
    for category, expected_count in categories.items():
        cat_dir = LAYER_B_V2_DIR / category
        assert cat_dir.is_dir(), f"Missing category directory: {category}"
        event_dirs = sorted([d for d in cat_dir.iterdir() if d.is_dir()])
        assert len(event_dirs) == expected_count, f"Expected {expected_count} {category}, found {len(event_dirs)}"

        for event_dir in event_dirs:
            total_bundles += 1
            result = load_event_bundle(event_dir, strict_metadata=False)
            assert result.ok, f"load_event_bundle failed for {event_dir}: {result.issues}"
            assert result.event is not None
            assert result.event.camera_1_path is not None
            assert result.event.camera_2_path is not None
            assert Path(result.event.camera_1_path).exists(), f"Camera 1 missing in {event_dir}"
            assert Path(result.event.camera_2_path).exists(), f"Camera 2 missing in {event_dir}"

    assert total_bundles == 28, f"Expected 28 total bundles, found {total_bundles}"


def test_negative_audio_directory_documented():
    assert AUDIO_NEG_DIR.exists()
    readme = AUDIO_NEG_DIR / "README.md"
    assert readme.exists()
    content = readme.read_text(encoding="utf-8")
    assert "currently missing" in content.lower()


def test_data_separation_from_dataset_v1():
    """Verify that no Layer B V2 evaluation media or training audio intersects with vision training data."""
    v1_dir = WORKSPACE_ROOT / "data" / "raw" / "vision" / "v1"
    assert v1_dir.exists(), "Dataset V1 vision training directory must exist"

    assert V2_VIDEO_MANIFEST_PATH.exists()
    with open(V2_VIDEO_MANIFEST_PATH, encoding="utf-8") as f:
        v_data = json.load(f)

    for r in v_data["records"]:
        dst_path = r["destination_path"]
        assert "data/raw/vision" not in dst_path
        assert dst_path.startswith("data/raw/layer_b/v2/")
        assert not (v1_dir / r["filename"]).exists(), f"Collision: {r['filename']} found in {v1_dir}"

    a_manifest = MANIFESTS_DIR / "train_horn_audio_manifest.json"
    assert a_manifest.exists()
    with open(a_manifest, encoding="utf-8") as f:
        a_records = json.load(f)

    for r in a_records:
        rel_path = r["relative_path"]
        assert "data/raw/vision" not in rel_path
        assert "data/raw/layer_b" not in rel_path
        assert rel_path.startswith("data/raw/audio/")


def test_audio_duplicate_tracking():
    """Verify that 41.mp3 and 42.mp3 are documented duplicates in the manifest."""
    a_manifest = MANIFESTS_DIR / "train_horn_audio_manifest.json"
    with open(a_manifest, encoding="utf-8") as f:
        a_records = json.load(f)

    rec_41 = next((r for r in a_records if r["filename"] == "41.mp3"), None)
    rec_42 = next((r for r in a_records if r["filename"] == "42.mp3"), None)

    assert rec_41 is not None and rec_42 is not None
    assert rec_41["sha256"] == rec_42["sha256"]
    assert rec_42["is_duplicate"] is True
    assert rec_42["duplicate_of"] == "41.mp3"


def test_audio_extension_anomaly_tracking():
    """Verify that misnamed 43.pdf-46.pdf are tracked and have companion .mp3 symlinks."""
    a_manifest = MANIFESTS_DIR / "train_horn_audio_manifest.json"
    with open(a_manifest, encoding="utf-8") as f:
        a_records = json.load(f)

    pdf_files = ["43.pdf", "44.pdf", "45.pdf", "46.pdf"]
    for pdf_name in pdf_files:
        rec = next((r for r in a_records if r["filename"] == pdf_name), None)
        assert rec is not None
        assert rec["is_extension_anomaly"] is True
        assert rec["format"] == "mp3"
        assert rec["sample_rate"] == 44100
        # Check companion symlink
        stem = pdf_name.split(".")[0]
        symlink_path = AUDIO_DIR / f"{stem}.mp3"
        assert symlink_path.exists()


def test_pretraining_checklist_exists():
    """Verify that docs/AUDIO_MODEL_PRETRAINING_CHECKLIST.md exists and covers key criteria."""
    checklist_path = WORKSPACE_ROOT / "docs" / "AUDIO_MODEL_PRETRAINING_CHECKLIST.md"
    if not checklist_path.exists():
        checklist_path = WORKSPACE_ROOT / "docs" / "archive" / "AUDIO_MODEL_PRETRAINING_CHECKLIST.md"
    assert checklist_path.exists()
    content = checklist_path.read_text(encoding="utf-8")
    assert "Current Dataset Inventory" in content
    assert "Current Implementation Status" in content
    assert "Missing Components" in content
    assert "Negative-Data Requirements" in content
    assert "Leakage-Prevention Rules" in content
    assert "TRAIN_HORN" in content
    assert "NON_TRAIN_HORN" in content

