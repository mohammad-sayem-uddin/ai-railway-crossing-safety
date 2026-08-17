"""Precise SNR noise mixing for audio robustness testing.

Mixes a clean signal with noise at an exact target SNR (dB) with reproducible
noise selection. Synthetic-noise results are kept separate from clean and
real-noise evaluations.
"""

from __future__ import annotations

import numpy as np

from railway_detection.utils.logging import get_logger

logger = get_logger("audio.noise_mixer")


def rms(samples: np.ndarray) -> float:
    """Root mean square of a signal."""
    if len(samples) == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(samples))))


def snr_db(signal: np.ndarray, noise: np.ndarray) -> float:
    """Signal-to-noise ratio in dB (signal vs. noise RMS)."""
    signal_rms = rms(signal)
    noise_rms = rms(noise)
    if noise_rms == 0:
        return float("inf") if signal_rms > 0 else 0.0
    if signal_rms == 0:
        return float("-inf")
    return float(20.0 * np.log10(signal_rms / noise_rms))


def mix_at_snr(
    signal: np.ndarray,
    noise: np.ndarray,
    target_snr_db: float,
    *,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Mix signal and noise at the requested target SNR.

    ``noise`` is cropped/tiled to the signal length; a random start offset
    uses ``rng`` when provided, otherwise the noise start is deterministic.
    The result is clipped to [-1, 1] to prevent numerical distortion.
    """
    if len(signal) == 0:
        raise ValueError("signal must not be empty")
    if len(noise) == 0:
        raise ValueError("noise must not be empty")

    signal_rms = rms(signal)
    if signal_rms == 0:
        raise ValueError("signal is silent; cannot mix at a target SNR")

    if rng is not None:
        start = int(rng.integers(0, max(1, len(noise) - len(signal) + 1)))
    else:
        start = 0
    if len(noise) < len(signal):
        repeats = int(np.ceil(len(signal) / len(noise)))
        noise_segment = np.tile(noise, repeats)[: len(signal)]
    else:
        noise_segment = noise[start : start + len(signal)].copy()
        if len(noise_segment) < len(signal):
            noise_segment = np.pad(noise_segment, (0, len(signal) - len(noise_segment)))

    noise_rms = rms(noise_segment)
    if noise_rms == 0:
        return signal.copy()

    scale = signal_rms / (noise_rms * (10 ** (target_snr_db / 20.0)))
    mixed = signal + scale * noise_segment
    return np.clip(mixed, -1.0, 1.0).astype(np.float64)


def verify_snr(
    mixed: np.ndarray, signal: np.ndarray, target_snr_db: float, tolerance_db: float = 0.5
) -> bool:
    """Verify that a mixture is within tolerance of its target SNR."""
    residual = mixed - signal
    achieved = snr_db(signal, residual)
    return abs(achieved - target_snr_db) <= tolerance_db
