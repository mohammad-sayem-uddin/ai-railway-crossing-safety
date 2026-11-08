"""Sequential video frame extraction.

Reads video files with configurable sampling (target FPS or frame stride).
The legacy OpenCV path uses nominal FPS. Opt-in PyAV decoding preserves
original frame PTS and timebase in each VideoFrame; both backends load lazily.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from railway_detection.config.exceptions import ConfigError
from railway_detection.safety.media_guard import require_media_authorization
from railway_detection.utils.logging import get_logger

logger = get_logger("vision.video")

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
SOURCE_DISPLAY_ROTATION_POLICY = "orthogonal_display_matrix_rotation_v1"


@dataclass(frozen=True)
class VideoFrame:
    frame_index: int
    timestamp_s: float
    image: Any
    source_id: str | None = None
    pts_ticks: int | None = None
    timebase: tuple[int, int] | None = None
    stream_index: int | None = None
    stream_start_pts: int | None = None
    display_rotation_deg: int = 0


def timestamps_for_frames(frame_indices: list[int], native_fps: float) -> list[float]:
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
    source_pts: bool = False,
    video_stream_index: int | None = None,
) -> Iterator[VideoFrame]:
    """Yield sampled ``VideoFrame`` records from a video file."""
    path = Path(video_path)
    require_media_authorization(path, "READ_RAW_MEDIA", declared_media=True)
    if not path.exists():
        raise ConfigError(f"video file not found: {path}")
    if path.suffix.lower() not in VIDEO_EXTENSIONS:
        raise ConfigError(f"unsupported video extension: {path.suffix}")

    if source_pts:
        yield from _source_pts_frames(
            path,
            target_fps=target_fps,
            stride=stride,
            source_id=source_id,
            video_stream_index=video_stream_index,
        )
        return
    if video_stream_index is not None:
        raise ConfigError("explicit stream selection requires source_pts=True")

    try:
        import cv2  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ConfigError("opencv-python is not installed; install it to read video files") from exc

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ConfigError(f"cannot open video: {path}")

    try:
        native_fps = float(capture.get(cv2.CAP_PROP_FPS))
        if native_fps <= 0:
            raise ConfigError(f"video reports invalid FPS ({native_fps}); cannot derive timestamps")
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        indices = select_frame_indices(
            total_frames,
            native_fps=native_fps,
            target_fps=target_fps,
            stride=stride,
        )
        timestamps = timestamps_for_frames(indices, native_fps)
        current_frame = -1
        for frame_idx, timestamp_s in zip(indices, timestamps, strict=True):
            while current_frame < frame_idx:
                if not capture.grab():
                    break
                current_frame += 1
            if current_frame != frame_idx:
                logger.warning("failed to advance to frame %d from %s; skipping", frame_idx, path)
                continue
            ok, image = capture.retrieve()
            if not ok or image is None:
                logger.warning("failed to read frame %d from %s; skipping", frame_idx, path)
                continue
            yield VideoFrame(
                frame_index=frame_idx,
                timestamp_s=timestamp_s,
                image=image,
                source_id=source_id,
            )
    finally:
        capture.release()


def _source_pts_frames(
    path: Path,
    *,
    target_fps: float | None,
    stride: int | None,
    source_id: str | None,
    video_stream_index: int | None,
) -> Iterator[VideoFrame]:
    """Decode one video stream with native PTS; never infer or rebase timestamps.

    Sampling uses a rational grid anchored to the first decoded presentation time.
    Exact ticks/timebase remain alongside the float used by existing consumers.
    The caller has already passed the existing media authorization boundary.
    """
    if target_fps is not None and stride is not None:
        raise ConfigError("provide either target_fps or stride, not both")
    if target_fps is not None and (
        isinstance(target_fps, bool) or not math.isfinite(target_fps) or target_fps <= 0
    ):
        raise ConfigError("target_fps must be finite and positive")
    if stride is not None and (type(stride) is not int or stride <= 0):
        raise ConfigError("stride must be a positive integer")
    if video_stream_index is not None and (
        type(video_stream_index) is not int or video_stream_index < 0
    ):
        raise ConfigError("video stream index must be a nonnegative integer")
    try:
        import av
    except ImportError as exc:
        raise ConfigError("native PTS decoding requires the optional 'pts' dependencies") from exc

    try:
        with av.open(str(path), mode="r") as container:
            videos = list(container.streams.video)
            selected = next(
                (s for s in videos if video_stream_index is None or s.index == video_stream_index),
                None,
            )
            if selected is None:
                raise ConfigError("requested video stream is unavailable or not a video stream")
            previous = None
            anchor = None
            due = None
            rate = Fraction(str(target_fps)) if target_fps is not None else None
            for index, frame in enumerate(container.decode(selected)):
                pts = frame.pts
                tb = frame.time_base
                if type(pts) is not int or tb is None:
                    raise ConfigError("decoded frame is missing original PTS/timebase")
                if tb.numerator <= 0 or tb.denominator <= 0:
                    raise ConfigError("decoded frame has invalid original timebase")
                stamp = pts * Fraction(tb)
                if stamp < 0 or (previous is not None and stamp <= previous):
                    raise ConfigError(
                        "original presentation timestamps must be nonnegative and increasing"
                    )
                previous = stamp
                if anchor is None:
                    anchor = due = stamp
                if stride is not None and index % stride:
                    continue
                if rate is not None:
                    assert due is not None
                    if stamp < due:
                        continue
                    due = anchor + ((stamp - anchor) * rate // 1 + 1) / rate
                rotation = getattr(frame, "rotation", 0)
                if type(rotation) is not int or rotation % 90:
                    raise ConfigError("unsupported nonorthogonal source display rotation")
                image = frame.to_ndarray(format="bgr24")
                if rotation % 360:
                    import numpy as np

                    image = np.ascontiguousarray(np.rot90(image, k=rotation // 90))
                yield VideoFrame(
                    frame_index=index,
                    timestamp_s=float(stamp),
                    image=image,
                    source_id=source_id,
                    pts_ticks=pts,
                    timebase=(tb.numerator, tb.denominator),
                    stream_index=selected.index,
                    stream_start_pts=selected.start_time,
                    display_rotation_deg=rotation,
                )
            if previous is None:
                raise ConfigError("video stream contains no decoded presentation frames")
    except ConfigError:
        raise
    except Exception as exc:
        raise ConfigError(f"native PTS video decoding failed: {exc}") from exc
