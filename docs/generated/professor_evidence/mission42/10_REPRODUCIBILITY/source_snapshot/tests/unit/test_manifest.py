"""Unit tests for normalized dataset manifest generation."""

from __future__ import annotations

import json

import pytest
from PIL import Image

from railway_detection.data.manifest import (
    MANIFEST_VERSION,
    build_vision_manifest,
    discover_images,
    infer_split_group_id,
    read_manifest,
    split_dir_for,
    write_manifest,
)
from railway_detection.data.validator import label_path_for, parse_label_annotations

CLASS_MAPPING = {"front": 0, "side": 1, "rear": 2}


def make_roboflow_layout(root) -> tuple[object, object, dict]:
    """Build a tiny train/valid Roboflow-style dataset (labels inside root).

    Each label carries two classes to exercise multi-annotation records.
    Returns (dataset_root, annotations_root, metadata) where metadata joins on
    relative image stems.
    """
    dataset_root = root / "dataset"
    samples = [
        ("train", "src_a", "front", "side"),
        ("train", "src_b", "rear", "side"),
        ("valid", "src_c", "front", "rear"),
    ]
    metadata = {}
    for split, source, first, second in samples:
        (dataset_root / split / "images").mkdir(parents=True, exist_ok=True)
        (dataset_root / split / "labels").mkdir(parents=True, exist_ok=True)
        image_path = dataset_root / split / "images" / f"{source}.jpg"
        Image.new("RGB", (64, 64), color=(30, 30, 30)).save(image_path)
        class_ids = [CLASS_MAPPING[first], CLASS_MAPPING[second]]
        label_path = dataset_root / split / "labels" / f"{source}.txt"
        label_path.write_text(
            "\n".join(f"{cid} 0.5 0.5 0.4 0.4" for cid in class_ids) + "\n",
            encoding="utf-8",
        )
        metadata[f"{split}/images/{source}"] = {
            "split_group_id": f"crossing_{source}",
            "crossing_id": f"crossing_{source}",
            "weather": "unknown",
            "mock_data": True,
        }
    return dataset_root, dataset_root, metadata


def make_single_sample_layout(root, name: str, label_text: str) -> tuple[object, object]:
    """Create one image/label pair in the Roboflow train split layout."""
    dataset_root = root / "dataset"
    (dataset_root / "train" / "images").mkdir(parents=True, exist_ok=True)
    (dataset_root / "train" / "labels").mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (32, 32)).save(dataset_root / "train" / "images" / f"{name}.jpg")
    (dataset_root / "train" / "labels" / f"{name}.txt").write_text(
        label_text, encoding="utf-8"
    )
    return dataset_root, dataset_root


def test_discover_images_finds_all(tmp_path):
    (tmp_path / "a.jpg").write_bytes(b"x")
    (tmp_path / "b.png").write_bytes(b"x")
    (tmp_path / "c.webp").write_bytes(b"x")
    (tmp_path / "d.txt").write_text("not an image", encoding="utf-8")
    found = discover_images(tmp_path)
    assert [p.name for p in found] == ["a.jpg", "b.png", "c.webp"]


def test_split_dir_detection(tmp_path):
    assert split_dir_for(tmp_path, tmp_path / "train" / "images" / "x.jpg") == "train"
    assert split_dir_for(tmp_path, tmp_path / "valid" / "images" / "x.jpg") == "valid"
    assert split_dir_for(tmp_path, tmp_path / "test" / "images" / "x.jpg") == "test"
    assert split_dir_for(tmp_path, tmp_path / "other" / "x.jpg") == "unknown"


def test_augmentation_group_hint():
    augmented = "1764911995457_jpg.rf.109e8d9a81ff93c61ff0f1e3bf622e65"
    assert infer_split_group_id(augmented) == "source:1764911995457_jpg"
    plain = "cross_a_img_1"
    assert infer_split_group_id(plain) == "source:cross_a_img_1"


def test_build_manifest_joins_metadata_and_annotations(tmp_path):
    dataset_root, annotations_root, metadata = make_roboflow_layout(tmp_path)

    result, summary = build_vision_manifest(
        dataset_root,
        annotations_root,
        CLASS_MAPPING,
        metadata=metadata,
    )

    assert summary.sample_count == 3
    assert summary.negative_sample_count == 0
    assert summary.ungrouped_sample_count == 0
    assert summary.class_distribution == {"front": 2, "rear": 2, "side": 2}
    assert summary.split_dir_distribution == {"train": 2, "valid": 1}
    assert result.excluded_unreadable == []
    assert result.excluded_invalid_labels == []

    by_id = {record.image_id: record for record in result.records}
    record = by_id["train/images/src_a"]
    assert record.split_group_id == "crossing_src_a"
    assert record.crossing_id == "crossing_src_a"
    assert [ann.label for ann in record.annotations] == ["front", "side"]
    assert record.image_path == "train/images/src_a.jpg"
    assert record.label_path == "train/labels/src_a.txt"


def test_build_manifest_without_metadata_uses_inferred_hints(tmp_path):
    dataset_root, annotations_root, _ = make_roboflow_layout(tmp_path)

    result, summary = build_vision_manifest(
        dataset_root, annotations_root, CLASS_MAPPING, metadata=None
    )

    assert summary.sample_count == 3
    assert result.missing_group_metadata == [
        "train/images/src_a",
        "train/images/src_b",
        "valid/images/src_c",
    ]
    by_id = {record.image_id: record for record in result.records}
    assert by_id["train/images/src_a"].split_group_id == "source:src_a"
    assert by_id["train/images/src_a"].provenance["group_hint"] == "inferred"


def test_empty_label_is_explicit_negative(tmp_path):
    dataset_root, annotations_root = make_single_sample_layout(
        tmp_path, "neg", ""
    )

    result, summary = build_vision_manifest(
        dataset_root, annotations_root, CLASS_MAPPING, metadata=None
    )

    assert summary.sample_count == 1
    assert summary.negative_sample_count == 1
    assert result.records[0].annotations == ()
    assert result.records[0].label_path == "train/labels/neg.txt"


def test_unreadable_image_excluded(tmp_path):
    dataset_root, annotations_root = make_single_sample_layout(
        tmp_path, "broken", "0 0.5 0.5 0.4 0.4\n"
    )
    (dataset_root / "train" / "images" / "broken.jpg").write_bytes(
        b"definitely not a jpeg"
    )

    result, summary = build_vision_manifest(
        dataset_root, annotations_root, CLASS_MAPPING, metadata=None
    )

    assert summary.sample_count == 0
    assert summary.excluded_unreadable_count == 1
    assert result.excluded_unreadable == ["train/images/broken"]
    assert any("unreadable" in warning for warning in result.warnings)


def test_invalid_label_excluded(tmp_path):
    dataset_root, annotations_root = make_single_sample_layout(
        tmp_path, "bad", "99 0.5 0.5 0.4 0.4\n"
    )

    result, summary = build_vision_manifest(
        dataset_root, annotations_root, CLASS_MAPPING, metadata=None
    )

    assert summary.sample_count == 0
    assert summary.excluded_invalid_label_count == 1
    assert result.excluded_invalid_labels == ["train/images/bad"]


def test_write_and_read_manifest_round_trip(tmp_path):
    dataset_root, annotations_root, metadata = make_roboflow_layout(tmp_path)
    result, _ = build_vision_manifest(
        dataset_root, annotations_root, CLASS_MAPPING, metadata=metadata
    )

    output_dir = tmp_path / "out"
    manifest_path = write_manifest(result, output_dir, metadata={"dataset_version": "v1"})
    assert manifest_path.name == "dataset_manifest.jsonl"

    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3

    summary_path = output_dir / "manifest_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["manifest_version"] == MANIFEST_VERSION
    assert summary["sample_count"] == 3
    assert summary["extra"]["dataset_version"] == "v1"

    records = read_manifest(manifest_path)
    assert len(records) == 3
    first = records[0]
    assert first.image_id == "train/images/src_a"
    assert first.split_group_id == "crossing_src_a"
    assert [ann.label for ann in first.annotations] == ["front", "side"]
    assert first.annotations[0].bbox is not None
    assert first.annotations[0].bbox.width() > 0


def test_read_manifest_rejects_malformed_line(tmp_path):
    manifest_path = tmp_path / "dataset_manifest.jsonl"
    manifest_path.write_text(
        '{"image_id": "ok", "image_path": "x.jpg"}\nnot json\n', encoding="utf-8"
    )

    with pytest.raises(ValueError, match="line 2"):
        read_manifest(manifest_path)


def test_label_path_and_annotations_shared_helpers(tmp_path):
    """Validator helpers reused by the manifest stay consistent."""
    dataset_root, annotations_root, _ = make_roboflow_layout(tmp_path)
    image_path = dataset_root / "train" / "images" / "src_a.jpg"
    label_path = label_path_for(annotations_root, image_path)
    assert label_path is not None
    annotations = parse_label_annotations(
        label_path, {class_id: name for name, class_id in CLASS_MAPPING.items()}
    )
    assert [ann.label for ann in annotations] == ["front", "side"]
