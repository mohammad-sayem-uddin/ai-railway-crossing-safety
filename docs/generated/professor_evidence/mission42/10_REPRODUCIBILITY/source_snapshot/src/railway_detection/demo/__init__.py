"""Video demo and testing tool for railway train detection."""

from railway_detection.demo.video_demo import (
    CANONICAL_CLASSES,
    ClassStats,
    FrameDetection,
    VideoDemoSummary,
    create_output_directory,
    normalize_class_name,
    process_video,
    resolve_device,
    select_input_video,
)

__all__ = [
    "CANONICAL_CLASSES",
    "ClassStats",
    "FrameDetection",
    "VideoDemoSummary",
    "create_output_directory",
    "normalize_class_name",
    "process_video",
    "resolve_device",
    "select_input_video",
]
