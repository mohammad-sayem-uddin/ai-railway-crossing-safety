"""Audio extraction utility to isolate WAV streams from video recordings via ffmpeg."""

from __future__ import annotations

import subprocess
from pathlib import Path

from railway_detection.safety.media_guard import require_media_authorization
from railway_detection.utils.logging import get_logger

logger = get_logger("data.audio_extractor")


def extract_audio_from_video(
    video_path: Path | str,
    output_wav_path: Path | str,
    sample_rate: int = 16000,
    channels: int = 1,
) -> Path | None:
    """Extracts an audio track from a video container to a PCM WAV file using ffmpeg.

    Args:
        video_path: Source video file path.
        output_wav_path: Destination WAV file path.
        sample_rate: Target audio sampling rate in Hz (default: 16000).
        channels: Target audio channel count (default: 1 for mono).

    Returns:
        Path to the extracted WAV file if successful, or None on failure.
    """
    video_path = Path(video_path)
    output_wav_path = Path(output_wav_path)
    require_media_authorization(video_path, "AUDIO_EXTRACTION")

    if not video_path.exists():
        logger.warning("Source video does not exist: %s", video_path)
        return None

    output_wav_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output without asking
        "-v",
        "error",
        "-i",
        str(video_path),
        "-vn",  # Disable video stream
        "-acodec",
        "pcm_s16le",
        "-ar",
        str(sample_rate),
        "-ac",
        str(channels),
        str(output_wav_path),
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if res.returncode != 0:
            logger.warning(
                "ffmpeg failed to extract audio from %s: %s",
                video_path,
                res.stderr.decode("utf-8", errors="replace"),
            )
            return None

        if not output_wav_path.exists() or output_wav_path.stat().st_size == 0:
            logger.warning("Extracted WAV file is missing or empty: %s", output_wav_path)
            return None

        return output_wav_path
    except Exception as exc:
        logger.error("Error executing audio extraction on %s: %s", video_path, exc)
        return None
