"""Sequential video frame extraction.

Reads video files with configurable sampling (target FPS or frame stride)
and yields ``(frame_idx, timestamp_s, image)`` tuples. ``cv2`` is imported
lazily; the timestamp math is pure and separately testable.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from railway_detection.config.exceptions import ConfigError
from railway_detection.utils.logging import get_logger

logger = get_logger("vision.video")

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}


@dataclass(frozen=True)
class VideoFrame:
    frame_index: int
    timestamp_s: float
    image: Any
    source_id: str | None = None


def timestamps_for_frames(
    frame_indices: list[int], native_fps: float
) -> list[float]:
    """Compute per-frame timestamps from frame indices and native FPS."""
    if native_fps <= 0:
        raise ValueError("native_fps must be positive")
    return [float(idx) / float(native_fps) for idx in frame_indices]


def select_frame_indices(
    total_frames: int,
    *,
    native_fps: float,
    target_fps: float | None = None,
    stride: int | None = None,
) -> list[int]:
    """Select sampled frame indices deterministically.

    Exactly one of ``target_fps`` (sampled frames per second) or ``stride``
    (sample every N frames) should be given; if both are None, all frames are
    returned.
    """
    if total_frames <= 0:
        return []
    if target_fps is not None and stride is not None:
        raise ValueError("provide either target_fps or stride, not both")
    if target_fps is not None:
        if target_fps <= 0 or native_fps <= 0:
            raise ValueError("target_fps and native_fps must be positive")
        step = max(1, round(native_fps / target_fps))
    elif stride is not None:
        if stride <= 0:
            raise ValueError("stride must be positive")
        step = stride
    else:
        step = 1
    return list(range(0, total_frames, step))


def frame_generator(
    video_path: str | Path,
    *,
    target_fps: float | None = None,
    stride: int | None = None,
    source_id: str | None = None,
) -> Iterator[VideoFrame]:
    """Yield sampled ``VideoFrame`` records from a video file."""
    path = Path(video_path)
    if not path.exists():
        raise ConfigError(f"video file not found: {path}")
    if path.suffix.lower() not in VIDEO_EXTENSIONS:
        raise ConfigError(f"unsupported video extension: {path.suffix}")

    try:
        import cv2  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ConfigError(
            "opencv-python is not installed; install it to read video files"
        ) from exc

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ConfigError(f"cannot open video: {path}")

    try:
        native_fps = float(capture.get(cv2.CAP_PROP_FPS))
        if native_fps <= 0:
            raise ConfigError(
                f"video reports invalid FPS ({native_fps}); cannot derive timestamps"
            )
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        indices = select_frame_indices(
            total_frames,
            native_fps=native_fps,
            target_fps=target_fps,
            stride=stride,
        )
        timestamps = timestamps_for_frames(indices, native_fps)
        for frame_idx, timestamp_s in zip(indices, timestamps, strict=True):
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ok, image = capture.read()
            if not ok:
                logger.warning(
                    "failed to read frame %d from %s; skipping", frame_idx, path
                )
                continue
            yield VideoFrame(
                frame_index=frame_idx,
                timestamp_s=timestamp_s,
                image=image,
                source_id=source_id,
            )
    finally:
        capture.release()
