"""Audio feature extraction: STFT and Log-Mel Spectrograms.

Implements portable log-Mel spectrogram extraction using pure NumPy and SciPy.
No torchaudio or librosa dependencies required.
"""

from __future__ import annotations

import numpy as np


def hz_to_mel(frequencies: np.ndarray | float) -> np.ndarray | float:
    """Convert Hz to Mel scale using the Slaney / O'Shaughnessy formula."""
    return 2595.0 * np.log10(1.0 + np.asarray(frequencies) / 700.0)


def mel_to_hz(mels: np.ndarray | float) -> np.ndarray | float:
    """Convert Mel scale to Hz."""
    return 700.0 * (10.0 ** (np.asarray(mels) / 2595.0) - 1.0)


def create_mel_filterbank(
    sample_rate: int = 16000,
    n_fft: int = 512,
    n_mels: int = 64,
    f_min: float = 0.0,
    f_max: float | None = None,
) -> np.ndarray:
    """Construct a triangular Mel filterbank matrix.

    Returns:
        Filterbank weights array of shape (n_mels, n_fft // 2 + 1).
    """
    if f_max is None:
        f_max = float(sample_rate) / 2.0

    n_freq_bins = n_fft // 2 + 1
    mel_min = float(hz_to_mel(f_min))
    mel_max = float(hz_to_mel(f_max))

    mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
    hz_points = mel_to_hz(mel_points)

    bin_points = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)
    bin_points = np.clip(bin_points, 0, n_freq_bins - 1)

    filterbank = np.zeros((n_mels, n_freq_bins), dtype=np.float64)
    for m in range(1, n_mels + 1):
        f_left = bin_points[m - 1]
        f_center = bin_points[m]
        f_right = bin_points[m + 1]

        if f_center > f_left:
            filterbank[m - 1, f_left:f_center] = (
                np.arange(f_left, f_center) - f_left
            ) / float(f_center - f_left)
        if f_right > f_center:
            filterbank[m - 1, f_center:f_right] = (
                f_right - np.arange(f_center, f_right)
            ) / float(f_right - f_center)

    return filterbank


def compute_stft(
    waveform: np.ndarray,
    n_fft: int = 512,
    hop_length: int = 256,
) -> np.ndarray:
    """Compute Short-Time Fourier Transform using Hann window.

    Args:
        waveform: 1D numpy array of audio samples.
        n_fft: FFT size.
        hop_length: Hop length between consecutive frames.

    Returns:
        Complex STFT matrix of shape (n_fft // 2 + 1, n_frames).
    """
    waveform = np.asarray(waveform, dtype=np.float64)
    if waveform.ndim != 1:
        waveform = waveform.flatten()

    if len(waveform) < n_fft:
        pad_width = n_fft - len(waveform)
        waveform = np.pad(waveform, (0, pad_width), mode="constant")

    window = np.hanning(n_fft)
    n_frames = 1 + (len(waveform) - n_fft) // hop_length

    # Create sliding 2D view of frames
    shape = (n_frames, n_fft)
    strides = (waveform.strides[0] * hop_length, waveform.strides[0])
    frames = np.lib.stride_tricks.as_strided(waveform, shape=shape, strides=strides)

    windowed = frames * window
    stft = np.fft.rfft(windowed, n=n_fft, axis=-1)
    return stft.T  # (n_freq_bins, n_frames)


def compute_log_mel_spectrogram(
    waveform: np.ndarray,
    sample_rate: int = 16000,
    n_fft: int = 512,
    hop_length: int = 256,
    n_mels: int = 64,
    f_min: float = 0.0,
    f_max: float | None = None,
    eps: float = 1e-10,
) -> np.ndarray:
    """Extract Log-Mel spectrogram from an audio waveform.

    Args:
        waveform: 1D float array in [-1.0, 1.0].
        sample_rate: Sampling rate in Hz.
        n_fft: FFT window size.
        hop_length: Step size between STFT frames.
        n_mels: Number of Mel frequency bands.
        f_min: Minimum frequency in Hz.
        f_max: Maximum frequency in Hz (defaults to sample_rate / 2).
        eps: Small constant to avoid log(0).

    Returns:
        Log-Mel spectrogram of shape (n_mels, n_frames) in dB scale.
    """
    stft = compute_stft(waveform, n_fft=n_fft, hop_length=hop_length)
    power_spectrum = np.abs(stft) ** 2.0

    filterbank = create_mel_filterbank(
        sample_rate=sample_rate,
        n_fft=n_fft,
        n_mels=n_mels,
        f_min=f_min,
        f_max=f_max,
    )

    mel_spec = np.dot(filterbank, power_spectrum)
    log_mel = 10.0 * np.log10(np.maximum(mel_spec, eps))
    return log_mel
