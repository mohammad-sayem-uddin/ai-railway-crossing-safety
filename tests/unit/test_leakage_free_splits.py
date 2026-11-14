"""Verification tests for dataset leakage auditing and session/stem-grouped splits."""

from __future__ import annotations

import json
from pathlib import Path

from railway_detection.data.leakage_audit import (
    audit_audio_split,
    audit_vision_partition,
    build_session_grouped_vision_split,
    build_stem_grouped_audio_split,
    extract_audio_positive_stem,
    parse_vision_source_timestamp,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_timestamp_parser_covers_all_encoded_patterns():
    ts1, kind1 = parse_vision_source_timestamp("source:Screenshot-2026-05-23-at-14-00-50_png")
    ts2, kind2 = parse_vision_source_timestamp("source:IMG_20251204_105453_460_jpg")
    ts3, kind3 = parse_vision_source_timestamp("source:image-2025-11-13T223947-481_png")
    ts4, kind4 = parse_vision_source_timestamp("source:1764911995523_jpg")
    ts5, kind5 = parse_vision_source_timestamp("source:96b49441-9695-4325-be1b-bfc25f30cf17_jpeg")
    assert ts1 is not None and kind1 == "Screenshot"
    assert ts2 is not None and kind2 == "IMG"
    assert ts3 is not None and kind3 == "image"
    assert ts4 is not None and abs(ts4 - 1764911995.523) < 1e-6 and kind4 == "epoch_ms"
    assert ts5 is None and kind5 == "unparsed"


def test_real_vision_v1_session_grouped_split_has_zero_leakage():
    manifest_path = REPO_ROOT / "results/dataset_validation/dataset_manifest.jsonl"
    rows = [json.loads(line) for line in manifest_path.read_text().splitlines() if line.strip()]
    records, summary = build_session_grouped_vision_split(rows, gap_s=600.0)
    audit = summary["audit"]

    assert audit["multi_split_source_group_count"] == 0
    for sweep in audit["temporal_session_sweeps"]:
        if sweep["gap_s"] <= 600.0:
            assert sweep["crossing_timestamped_sessions"] == 0
            assert sweep["test_timestamped_imgs_sharing_session_with_train"] == 0
            assert sweep["val_timestamped_imgs_sharing_session_with_train"] == 0

    # Val and test contain strictly 1 canonical image per unique source group (no 3x aug duplicates)
    assert audit["split_image_counts"]["val"] == audit["unique_source_counts"]["val"]
    assert audit["split_image_counts"]["test"] == audit["unique_source_counts"]["test"]
    assert sum(audit["unique_source_counts"].values()) == 1315
    assert len(records["train"]) + len(records["val"]) + len(records["test"]) == summary["total_manifest_images"] - summary["excluded_eval_augmentation_duplicates"]


def test_audio_stem_normalization_and_clean_split_zero_leakage():
    assert extract_audio_positive_stem("pos_Foo Bar - 128-3") == "Foo Bar"
    assert extract_audio_positive_stem("pos_Foo Bar - 128") == "Foo Bar"
    assert extract_audio_positive_stem("pos_Foo Bar-128-12") == "Foo Bar"
    assert extract_audio_positive_stem("pos_19(1)") == "19"

    v3 = json.loads((REPO_ROOT / "data/splits/audio/v3/dataset_split.json").read_text())
    orig_audit = audit_audio_split(v3)
    assert orig_audit["cross_split_negative_fold_count"] == 0
    assert orig_audit["unique_negative_folds"] == 5
    assert orig_audit["cross_split_positive_stem_count"] == 5

    new_payload, summary = build_stem_grouped_audio_split(v3)
    clean_audit = summary["audit_stem_grouped"]
    assert clean_audit["cross_split_positive_stem_count"] == 0
    assert clean_audit["positive_recordings_in_cross_split_stems"] == 0
    assert clean_audit["cross_split_negative_fold_count"] == 0
    assert clean_audit["counts_by_split"]["train"] == {"positive": 60, "negative": 60, "total": 120}
    assert clean_audit["counts_by_split"]["val"] == {"positive": 13, "negative": 13, "total": 26}
    assert clean_audit["counts_by_split"]["test"] == {"positive": 13, "negative": 13, "total": 26}


def test_real_705d_leakage_diagnostic_reproducible():
    manifest_path = REPO_ROOT / "results/dataset_validation/dataset_manifest.jsonl"
    rows = [json.loads(line) for line in manifest_path.read_text().splitlines() if line.strip()]
    s705d = {}
    for sp in ("train", "val", "test"):
        p = REPO_ROOT / f"data/splits/705d388743ea/{sp}.jsonl"
        for line in p.read_text().splitlines():
            if line.strip():
                s705d[json.loads(line)["sample_id"]] = sp
    audit = audit_vision_partition(rows, s705d)
    assert audit["rf_origin_by_split"]["test"]["train"] == 411
    sweep_600 = next(s for s in audit["temporal_session_sweeps"] if s["gap_s"] == 600.0)
    assert sweep_600["crossing_timestamped_sessions"] == 27
    assert sweep_600["test_timestamped_imgs_sharing_session_with_train"] == 447
