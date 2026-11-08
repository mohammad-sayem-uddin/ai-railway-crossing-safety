"""Unit tests for audio preprocessing and SNR mixing."""

from __future__ import annotations

import math
import wave
from pathlib import Path

import numpy as np
import pytest

from railway_detection.audio.noise_mixer import mix_at_snr, rms, snr_db, verify_snr
from railway_detection.audio.preprocessor import (
    load_wav,
    preprocess_wav_file,
    resample_linear,
    sliding_windows,
    standardize_wav,
)


def write_wav(path: Path, samples: np.ndarray, sample_rate: int, channels: int = 1) -> None:
    pcm = np.clip(samples, -1.0, 1.0)
    int16 = (pcm * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(int16.tobytes())


def test_load_wav_round_trip(tmp_path):
    path = tmp_path / "tone.wav"
    rate = 16000
    t = np.arange(rate) / rate
    samples = 0.5 * np.sin(2 * np.pi * 440 * t)
    write_wav(path, samples, rate)
    loaded, loaded_rate = load_wav(path)
    assert loaded_rate == rate
    assert len(loaded) == len(samples)
    assert np.allclose(loaded, samples, atol=1e-3)


def test_load_wav_stereo_averages_to_mono(tmp_path):
    path = tmp_path / "stereo.wav"
    rate = 8000
    left = 0.5 * np.ones(rate // 2)
    right = -0.5 * np.ones(rate // 2)
    stereo = np.stack([left, right], axis=1)
    pcm = np.clip(stereo, -1, 1)
    int16 = (pcm * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(int16.tobytes())
    loaded, _ = load_wav(path)
    assert loaded.shape == (rate // 2,)
    assert np.allclose(loaded, 0.0, atol=1e-2)


def test_load_wav_missing_file():
    from railway_detection.config.exceptions import ConfigError

    with pytest.raises(ConfigError):
        load_wav("/nonexistent/file.wav")


def test_resample_linear_preserves_length_ratio():
    samples = np.linspace(0, 1, 100)
    out = resample_linear(samples, 100, 50)
    assert abs(len(out) - 50) <= 1
    out2 = resample_linear(samples, 100, 200)
    assert abs(len(out2) - 200) <= 1
    # Same rate returns copy unchanged.
    out3 = resample_linear(samples, 100, 100)
    assert np.array_equal(out3, samples)


def test_standardize_wav_target_rate_and_bounds():
    samples = np.sin(np.linspace(0, 10, 8000))
    out = standardize_wav(samples, 8000, 16000)
    assert abs(len(out) - 16000) <= 2
    assert float(np.max(np.abs(out))) <= 1.0


def test_sliding_windows():
    samples = np.ones(16000)
    windows = sliding_windows(samples, 16000, window_s=1.0, hop_s=0.5)
    # 1 second of audio -> 1 window
    assert len(windows) == 1
    assert windows[0].duration_s == pytest.approx(1.0)
    assert windows[0].start_time_s == 0.0

    samples2 = np.ones(32000)
    windows2 = sliding_windows(samples2, 16000, window_s=1.0, hop_s=0.5)
    assert len(windows2) == 3  # [0,1), [0.5,1.5), [1,2)


def test_sliding_windows_reject_invalid():
    with pytest.raises(ValueError):
        sliding_windows(np.ones(10), 16000, window_s=0.0, hop_s=0.5)
    with pytest.raises(ValueError):
        sliding_windows(np.ones(10), 16000, window_s=1.0, hop_s=-1.0)


def test_preprocess_wav_file_end_to_end(tmp_path):
    path = tmp_path / "clip.wav"
    rate = 8000
    t = np.arange(rate * 2) / rate
    write_wav(path, 0.3 * np.sin(2 * np.pi * 220 * t), rate)
    samples, out_rate, windows = preprocess_wav_file(path, window_s=1.0, hop_s=0.5)
    assert out_rate == 16000
    assert len(windows) >= 1
    assert abs(len(samples) - 32000) <= 4


def test_rms_and_snr_math():
    signal = np.ones(1000)
    noise = 0.1 * np.ones(1000)
    assert rms(signal) == pytest.approx(1.0)
    assert snr_db(signal, noise) == pytest.approx(20.0, rel=0.01)
    assert snr_db(signal, np.zeros(1000)) == math.inf


def test_mix_at_snr_achieves_target():
    rng = np.random.default_rng(42)
    signal = 0.5 * np.sin(np.linspace(0, 100, 16000))
    noise = rng.normal(0, 0.3, 20000)
    mixed = mix_at_snr(signal, noise, 5.0, rng=rng)
    assert len(mixed) == len(signal)
    assert float(np.max(np.abs(mixed))) <= 1.0
    assert verify_snr(mixed, signal, 5.0, tolerance_db=1.0)


def test_mix_at_snr_reproducible_with_seed():
    signal = 0.5 * np.sin(np.linspace(0, 100, 8000))
    noise = np.random.default_rng(1).normal(0, 0.3, 10000)
    first = mix_at_snr(signal, noise, 0.0, rng=np.random.default_rng(7))
    second = mix_at_snr(signal, noise, 0.0, rng=np.random.default_rng(7))
    assert np.array_equal(first, second)


def test_mix_at_snr_silent_signal_rejected():
    with pytest.raises(ValueError):
        mix_at_snr(np.zeros(100), np.ones(100), 0.0)
    with pytest.raises(ValueError):
        mix_at_snr(np.ones(100), np.array([]), 0.0)
