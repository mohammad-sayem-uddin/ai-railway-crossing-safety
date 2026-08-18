"""Unit tests for the standalone video demonstration and inference tool.

Tests verify class normalization, statistics calculation, device fallback,
directory creation, and error handling using lightweight fixtures without
requiring heavy model weights or long video processing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from railway_detection.config.exceptions import ConfigError
from railway_detection.demo.video_demo import (
    ClassStats,
    FrameDetection,
    VideoDemoSummary,
    create_output_directory,
    draw_detection_box,
    normalize_class_name,
    resolve_device,
    select_input_video,
)


def test_class_name_normalization():
    """Verify that 'rare' typo is mapped to canonical 'rear' and classes normalize properly."""
    assert normalize_class_name("rare") == "rear"
    assert normalize_class_name("RARE") == "rear"
    assert normalize_class_name("Rare") == "rear"
    assert normalize_class_name(1) == "rear"
    assert normalize_class_name("1") == "rear"

    assert normalize_class_name("front") == "front"
    assert normalize_class_name(0) == "front"
    assert normalize_class_name("0") == "front"

    assert normalize_class_name("side") == "side"
    assert normalize_class_name(2) == "side"
    assert normalize_class_name("2") == "side"


def test_class_stats_properties():
    """Verify average and maximum confidence calculation in ClassStats."""
    stats = ClassStats()
    assert stats.avg_confidence == 0.0
    assert stats.max_confidence == 0.0

    stats.confidences = [0.80, 0.90, 1.00]
    stats.total_detections = 3
    stats.frames_with_class = 2

    assert pytest.approx(stats.avg_confidence, abs=1e-4) == 0.90
    assert pytest.approx(stats.max_confidence, abs=1e-4) == 1.00

    d = stats.to_dict()
    assert d["frames_with_class"] == 2
    assert d["total_detections"] == 3
    assert d["avg_confidence"] == 0.90
    assert d["max_confidence"] == 1.00


def test_video_demo_summary_serialization(tmp_path: Path):
    """Verify summary dictionary and markdown generation."""
    front_stats = ClassStats(frames_with_class=10, total_detections=12, confidences=[0.85, 0.95])
    side_stats = ClassStats(frames_with_class=20, total_detections=25, confidences=[0.75, 0.85])
    rear_stats = ClassStats(frames_with_class=5, total_detections=5, confidences=[0.90, 0.92])

    summary = VideoDemoSummary(
        input_video="sample.mp4",
        output_video="outputs/processed_video.mp4",
        model_path="weights/best.pt",
        model_name="best.pt",
        device_used="mps",
        width=1920,
        height=1080,
        fps=30.0,
        total_frames=100,
        processed_frames=100,
        processing_duration_s=5.0,
        inference_fps=20.0,
        total_detections=42,
        confidence_threshold=0.25,
        iou_threshold=0.45,
        temporal_smoothing=False,
        class_stats={"front": front_stats, "side": side_stats, "rear": rear_stats},
        frames_with_no_detections=65,
    )

    assert summary.frames_with_detections == 35
    assert summary.frames_with_detections_pct == 35.0

    data = summary.to_dict()
    assert data["input_video"] == "sample.mp4"
    assert data["device_used"] == "mps"
    assert data["detection_overview"]["total_detections"] == 42
    assert data["class_statistics"]["front"]["total_detections"] == 12

    md = summary.to_markdown()
    assert "# Railway Crossing Video Inference Summary" in md
    assert "FRONT" in md
    assert "REAR" in md
    assert "SIDE" in md
    assert "inference statistics only" in md


def test_create_output_directory(tmp_path: Path):
    """Verify output directory creation with timestamped structure."""
    fake_video = tmp_path / "test_train_video.mp4"
    out_dir = create_output_directory(fake_video, base_output_dir=tmp_path / "outputs")

    assert out_dir.exists()
    assert out_dir.is_dir()
    assert out_dir.name.startswith("test_train_video_")


def test_resolve_device():
    """Verify device selection logic and fallbacks."""
    assert resolve_device("cpu") == "cpu"

    auto_dev = resolve_device("auto")
    assert auto_dev in ("mps", "cuda", "cpu")

    assert resolve_device("invalid_device") == "cpu"


def test_select_input_video_validation(tmp_path: Path):
    """Verify input video selection error handling."""
    with pytest.raises(ConfigError, match="Specified input video does not exist"):
        select_input_video(str(tmp_path / "non_existent.mp4"))

    txt_file = tmp_path / "video.txt"
    txt_file.write_text("not a video")
    with pytest.raises(ConfigError, match="Unsupported video format"):
        select_input_video(str(txt_file))

    valid_file = tmp_path / "train_clip.mp4"
    valid_file.write_bytes(b"dummy video content")
    selected = select_input_video(str(valid_file))
    assert selected == valid_file.resolve()


def test_draw_detection_box():
    """Verify drawing bounding box with badge text on a dummy numpy image."""
    import numpy as np

    dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
    det = FrameDetection(
        label="front",
        confidence=0.94,
        bbox_xyxy=(50.0, 50.0, 200.0, 200.0),
        temporal_confirmed=True,
    )

    draw_detection_box(dummy_image, det)
    assert dummy_image.shape == (480, 640, 3)
    assert np.any(dummy_image > 0)
