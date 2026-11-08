"""Layer B media inspection and forensic metadata extraction.

Extracts container metadata, stream properties, and cryptographically verified
SHA-256 hashes using ffprobe and standard hashlib.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from railway_detection.safety.media_guard import require_media_authorization
from dataclasses import dataclass
from pathlib import Path

from railway_detection.annotation.schemas import InputMediaFile, validate_sha256
import logging

logger = logging.getLogger("annotation.media_inspector")


@dataclass
class StreamInfo:
    stream_type: str
    codec_name: str
    duration_s: float
    fps: float | None = None
    frame_count: int | None = None
    width: int | None = None
    height: int | None = None
    sample_rate: int | None = None
    channels: int | None = None


@dataclass
class MediaInspectionResult:
    file_path: Path
    file_name: str
    file_size_bytes: int
    sha256: str
    duration_s: float
    streams: list[StreamInfo]
    creation_time: str | None = None
    location_iso6709: str | None = None
    device_model: str | None = None

    @property
    def primary_video(self) -> StreamInfo | None:
        for s in self.streams:
            if s.stream_type == "video":
                return s
        return None

    @property
    def primary_audio(self) -> StreamInfo | None:
        for s in self.streams:
            if s.stream_type == "audio":
                return s
        return None

    def to_input_media_file(self) -> InputMediaFile:
        return InputMediaFile(
            file_name=self.file_name,
            duration_s=round(self.duration_s, 3),
            sha256=self.sha256,
        )


def compute_file_sha256(file_path: Path | str, block_size: int = 1024 * 1024) -> str:
    """Compute the full 64-character lowercase hexadecimal SHA-256 of a file."""
    path = Path(file_path)
    require_media_authorization(path, "HASH_RAW_MEDIA")
    if not path.is_file():
        raise FileNotFoundError(f"File not found for hashing: {path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(block_size):
            hasher.update(chunk)
    digest = hasher.hexdigest().lower()
    return validate_sha256(digest, f"SHA-256 of {path.name}")


def is_ffprobe_available() -> bool:
    return shutil.which("ffprobe") is not None


def is_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def inspect_media_file(file_path: Path | str) -> MediaInspectionResult:
    """Inspect a single media file using ffprobe and hashlib."""
    path = Path(file_path)
    require_media_authorization(path, "MEDIA_PROBE", declared_media=True)
    if not path.exists():
        raise FileNotFoundError(f"Media file does not exist: {path}")

    sha256 = compute_file_sha256(path)
    file_size = path.stat().st_size

    if not is_ffprobe_available():
        raise RuntimeError("ffprobe is required for media inspection but not found in PATH")

    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {path}: {proc.stderr[:200]}")

    data = json.loads(proc.stdout)
    fmt = data.get("format", {})
    duration_s = float(fmt.get("duration", 0.0))
    tags = fmt.get("tags", {})
    creation_time = tags.get("creation_time") or tags.get("com.apple.quicktime.creationdate")
    location_iso6709 = tags.get("com.apple.quicktime.location.ISO6709")
    device_model = tags.get("com.apple.quicktime.model")

    streams: list[StreamInfo] = []
    for s in data.get("streams", []):
        stype = s.get("codec_type", "unknown")
        codec = s.get("codec_name", "unknown")
        s_dur = float(s.get("duration") or duration_s)

        fps = None
        nb_frames = None
        if "nb_frames" in s and s["nb_frames"].isdigit():
            nb_frames = int(s["nb_frames"])

        r_fps_str = s.get("r_frame_rate", "")
        if "/" in r_fps_str:
            num, den = r_fps_str.split("/")
            if float(den) > 0:
                fps = float(num) / float(den)

        width = s.get("width")
        height = s.get("height")
        sample_rate = int(s.get("sample_rate")) if s.get("sample_rate") else None
        channels = int(s.get("channels")) if s.get("channels") else None

        streams.append(
            StreamInfo(
                stream_type=stype,
                codec_name=codec,
                duration_s=s_dur,
                fps=fps,
                frame_count=nb_frames,
                width=width,
                height=height,
                sample_rate=sample_rate,
                channels=channels,
            )
        )

    return MediaInspectionResult(
        file_path=path,
        file_name=path.name,
        file_size_bytes=file_size,
        sha256=sha256,
        duration_s=duration_s,
        streams=streams,
        creation_time=creation_time,
        location_iso6709=location_iso6709,
        device_model=device_model,
    )


def extract_frame_at_timestamp(
    video_path: Path | str,
    timestamp_s: float,
    output_path: Path | str,
) -> Path | None:
    """Extract a single JPEG frame at a precise timestamp using ffmpeg."""
    require_media_authorization(video_path, "FRAME_EXTRACTION", declared_media=True)
    if not is_ffmpeg_available():
        logger.warning("ffmpeg unavailable; cannot extract frame")
        return None

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{timestamp_s:.3f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(out_p),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode == 0 and out_p.exists():
        return out_p
    logger.warning("Failed to extract frame at %ss: %s", timestamp_s, proc.stderr[:200])
    return None
