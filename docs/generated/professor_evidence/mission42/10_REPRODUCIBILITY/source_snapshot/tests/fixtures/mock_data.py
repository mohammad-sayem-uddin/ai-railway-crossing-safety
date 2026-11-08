"""Utilities for building tiny mock datasets for tests.

Mock data is explicitly labeled with ``mock_data: true`` and must never be used
as research data or in research result tables.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


def make_mock_vision_dataset(root: Path) -> dict[str, object]:
    """Create a small, valid YOLO-style vision dataset under ``root``.

    Returns a metadata mapping from image_id to a group record.
    """
    images = root / "images"
    labels = root / "labels"
    images.mkdir(parents=True, exist_ok=True)
    labels.mkdir(parents=True, exist_ok=True)

    samples = [
        ("cross_a_img_1", 0, "cross_a", "front", (0.5, 0.5, 0.4, 0.4)),
        ("cross_a_img_2", 1, "cross_a", "side", (0.3, 0.5, 0.3, 0.6)),
        ("cross_b_img_1", 2, "cross_b", "rear", (0.6, 0.5, 0.3, 0.3)),
        ("cross_b_img_2", 0, "cross_b", "front", (0.4, 0.4, 0.5, 0.5)),
    ]

    metadata: dict[str, dict[str, object]] = {}
    for image_id, class_id, group, _label_name, (cx, cy, w, h) in samples:
        image_path = images / f"{image_id}.jpg"
        Image.new("RGB", (64, 64), color=(30, 30, 30)).save(image_path)
        label_path = labels / f"{image_id}.txt"
        label_path.write_text(f"{class_id} {cx} {cy} {w} {h}\n", encoding="utf-8")
        metadata[image_id] = {
            "split_group_id": group,
            "crossing_id": group,
            "weather": "unknown",
            "mock_data": True,
        }

    meta_path = root / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return {
        "images_root": images,
        "labels_root": labels,
        "metadata_path": meta_path,
        "metadata": metadata,
        "class_mapping": {"front": 0, "side": 1, "rear": 2},
    }


def make_mock_audio_dataset(root: Path) -> dict[str, object]:
    """Create placeholder audio metadata (no real audio files)."""
    root.mkdir(parents=True, exist_ok=True)
    clips = [
        {"clip_id": "clip_001", "label": "train_horn", "split_group_id": "session_a"},
        {"clip_id": "clip_002", "label": "non_train_sound", "split_group_id": "session_a"},
        {"clip_id": "clip_003", "label": "train_horn", "split_group_id": "session_b"},
        {"clip_id": "clip_004", "label": "non_train_sound", "split_group_id": "session_b"},
    ]
    path = root / "metadata.json"
    path.write_text(
        "\n".join(json.dumps({"mock_data": True, **clip}) for clip in clips) + "\n",
        encoding="utf-8",
    )
    return {"metadata_path": path, "clips": clips}
