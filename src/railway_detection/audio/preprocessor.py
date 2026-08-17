"""Audio preprocessing: load, standardize, and window audio.

Standardizes input WAV files to 16 kHz mono 16-bit PCM and splits continuous
audio into sliding analysis windows with configurable duration and overlap.
Pure stdlib + numpy; no scipy required.
"""

from __future__ import annotations

import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from railway_detection.config.exceptions import ConfigError
from railway_detection.utils.logging import get_logger

logger = get_logger("audio.preprocessor")

TARGET_SAMPLE_RATE = 16000
TARGET_BIT_DEPTH = 16


@dataclass(frozen=True)
class AudioWindow:
    window_id: str
    start_sample: int
    end_sample: int
    sample_rate: int
    samples: np.ndarray
    start_time_s: float

    @property
    def duration_s(self) -> float:
        return float(len(self.samples)) / float(self.sample_rate)


def load_wav(path: str | Path) -> tuple[np.ndarray, int]:
    """Load a WAV file and return (samples, sample_rate).

    Samples are float64 in [-1, 1]. Multi-channel audio is averaged to mono.
    """
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"audio file not found: {path}")
    try:
        with wave.open(str(path), "rb") as wav:
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            sample_rate = wav.getframerate()
            n_frames = wav.getnframes()
            raw = wav.readframes(n_frames)
    except (wave.Error, EOFError, OSError) as exc:
        raise ConfigError(f"cannot read WAV file {path}: {exc}") from exc

    if sample_width == 2:
        dtype: np.dtype[np.generic] = np.dtype("<i2")
    elif sample_width == 4:
        dtype = np.dtype("<i4")
    elif sample_width == 1:
        dtype = np.dtype("u1")
    else:
        raise ConfigError(f"unsupported WAV sample width: {sample_width}")

    samples = np.frombuffer(raw, dtype=dtype).astype(np.float64)
    if sample_width == 1:
        samples = (samples - 128.0) / 128.0
    elif sample_width == 2:
        samples /= 32768.0
    else:
        samples /= 2147483648.0

    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)

    return samples, int(sample_rate)


def resample_linear(samples: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    """Resample via linear interpolation."""
    if source_rate <= 0 or target_rate <= 0:
        raise ValueError("sample rates must be positive")
    if source_rate == target_rate:
        return samples.copy()
    if len(samples) == 0:
        return samples.copy()
    duration = len(samples) / float(source_rate)
    n_out = int(round(duration * target_rate))
    if n_out < 1:
        return samples.copy()
    x_old = np.arange(len(samples)) / float(source_rate)
    x_new = np.arange(n_out) / float(target_rate)
    return np.interp(x_new, x_old, samples).astype(np.float64)


def standardize_wav(
    samples: np.ndarray, source_rate: int, target_rate: int = TARGET_SAMPLE_RATE
) -> np.ndarray:
    """Convert samples to mono 16 kHz float64 in [-1, 1]."""
    mono = samples
    resampled = resample_linear(mono, source_rate, target_rate)
    return np.clip(resampled, -1.0, 1.0).astype(np.float64)


def sliding_windows(
    samples: np.ndarray,
    sample_rate: int,
    *,
    window_s: float = 1.0,
    hop_s: float = 0.5,
) -> list[AudioWindow]:
    """Split audio into overlapping analysis windows."""
    if window_s <= 0 or hop_s <= 0:
        raise ValueError("window_s and hop_s must be positive")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    window_len = int(round(window_s * sample_rate))
    hop_len = int(round(hop_s * sample_rate))
    if window_len < 1:
        raise ValueError("window too short for sample rate")
    if hop_len < 1:
        raise ValueError("hop too short for sample rate")
    windows: list[AudioWindow] = []
    if len(samples) < window_len:
        return windows
    idx = 0
    while idx + window_len <= len(samples):
        windows.append(
            AudioWindow(
                window_id=f"w{idx:08d}",
                start_sample=idx,
                end_sample=idx + window_len,
                sample_rate=sample_rate,
                samples=samples[idx : idx + window_len].copy(),
                start_time_s=idx / float(sample_rate),
            )
        )
        idx += hop_len
    return windows


def preprocess_wav_file(
    path: str | Path,
    *,
    target_rate: int = TARGET_SAMPLE_RATE,
    window_s: float = 1.0,
    hop_s: float = 0.5,
) -> tuple[np.ndarray, int, list[AudioWindow]]:
    """Load, standardize, and window a WAV file.

    Returns (standardized samples, sample_rate, windows).
    """
    samples, source_rate = load_wav(path)
    standardized = standardize_wav(samples, source_rate, target_rate)
    windows = sliding_windows(standardized, target_rate, window_s=window_s, hop_s=hop_s)
    logger.info(
        "preprocessed %s: %d samples -> %d windows",
        path,
        len(standardized),
        len(windows),
    )
    return standardized, target_rate, windows
