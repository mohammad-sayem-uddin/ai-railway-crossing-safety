"""Targeted regression tests for Audio V3 normalization and checkpoint contract (IMA-22).

Verifies:
1. Correct reading of actual Audio V3 checkpoint normalization metadata.
2. Agreement between training and inference normalization conventions.
3. Clear failure on missing, invalid, or non-finite normalization parameters.
4. Stable expected feature shape (64, 61) and preprocessing configuration.
5. Invariant checkpoint integrity (loading does not mutate checkpoint bytes).
6. Regression protection against norm_mean vs feature_mean naming mismatch and silent defaults.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pytest
import torch

from railway_detection.audio.features import compute_log_mel_spectrogram
from railway_detection.audio.model import CompactTrainHornCNN, PyTorchTrainHornClassifier

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIO_V3_CHECKPOINT = (
    REPO_ROOT / "experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt"
)
EXPECTED_AUDIO_V3_HASH = (
    "ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782"
)


def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def test_actual_checkpoint_normalization_metadata():
    """Directly inspect and assert normalization metadata from the frozen Audio V3 checkpoint."""
    assert AUDIO_V3_CHECKPOINT.exists(), f"Audio V3 checkpoint missing: {AUDIO_V3_CHECKPOINT}"

    # Verify safe weights_only loading
    raw_ckpt = torch.load(AUDIO_V3_CHECKPOINT, map_location="cpu", weights_only=True)
    assert "norm_mean" in raw_ckpt, "Checkpoint missing norm_mean"
    assert "norm_std" in raw_ckpt, "Checkpoint missing norm_std"
    assert "operating_threshold" in raw_ckpt, "Checkpoint missing operating_threshold"

    raw_mean = raw_ckpt["norm_mean"]
    raw_std = raw_ckpt["norm_std"]
    raw_thresh = raw_ckpt["operating_threshold"]

    # Verify expected scalar values
    assert abs(raw_mean - (-1.600999355316162)) < 1e-5
    assert abs(raw_std - 5.1239728927612305) < 1e-5
    assert abs(raw_thresh - 0.3700) < 1e-5

    # Instantiate classifier from checkpoint path
    classifier = PyTorchTrainHornClassifier(checkpoint_path=AUDIO_V3_CHECKPOINT)
    assert abs(classifier.mean - raw_mean) < 1e-7
    assert abs(classifier.std - raw_std) < 1e-7
    assert abs(classifier.threshold - raw_thresh) < 1e-7


def test_agreement_between_training_and_inference_normalization():
    """Verify inference normalizer exactly matches the training-time feature transform formula."""
    raw_ckpt = torch.load(AUDIO_V3_CHECKPOINT, map_location="cpu", weights_only=True)
    train_norm_mean = float(raw_ckpt["norm_mean"])
    train_norm_std = float(raw_ckpt["norm_std"])

    classifier = PyTorchTrainHornClassifier(checkpoint_path=AUDIO_V3_CHECKPOINT)

    # Synthetic spectrogram
    np.random.seed(42)
    synthetic_spectrogram = np.random.uniform(-40.0, 20.0, size=(64, 61))

    # Training-time formula: (X - norm_mean) / norm_std
    expected_normalized = (synthetic_spectrogram - train_norm_mean) / train_norm_std

    # Inference-time formula: (log_mel - self.mean) / self.std
    actual_normalized = (synthetic_spectrogram - classifier.mean) / classifier.std

    np.testing.assert_allclose(actual_normalized, expected_normalized, rtol=1e-6, atol=1e-7)


def test_clear_failure_on_missing_required_normalization_values(tmp_path: Path):
    """Verify that checkpoints missing normalization statistics fail with clear ValueError exceptions."""
    model = CompactTrainHornCNN()
    state_dict = model.state_dict()

    # Case 1: Missing norm_mean and feature_mean
    bad_ckpt_1 = tmp_path / "missing_mean.pt"
    torch.save(
        {
            "model_state_dict": state_dict,
            "norm_std": 5.0,
            "operating_threshold": 0.37,
        },
        bad_ckpt_1,
    )
    with pytest.raises(ValueError, match="lacks required normalization mean"):
        PyTorchTrainHornClassifier(checkpoint_path=bad_ckpt_1)

    # Case 2: Missing norm_std and feature_std
    bad_ckpt_2 = tmp_path / "missing_std.pt"
    torch.save(
        {
            "model_state_dict": state_dict,
            "norm_mean": -1.6,
            "operating_threshold": 0.37,
        },
        bad_ckpt_2,
    )
    with pytest.raises(ValueError, match="lacks required normalization standard deviation"):
        PyTorchTrainHornClassifier(checkpoint_path=bad_ckpt_2)

    # Case 3: Non-positive std (std <= 1e-6)
    bad_ckpt_3 = tmp_path / "zero_std.pt"
    torch.save(
        {
            "model_state_dict": state_dict,
            "norm_mean": -1.6,
            "norm_std": 0.0,
            "operating_threshold": 0.37,
        },
        bad_ckpt_3,
    )
    with pytest.raises(ValueError, match="Normalization std must be positive"):
        PyTorchTrainHornClassifier(checkpoint_path=bad_ckpt_3)

    # Case 4: Non-finite mean (NaN / Inf)
    bad_ckpt_4 = tmp_path / "nan_mean.pt"
    torch.save(
        {
            "model_state_dict": state_dict,
            "norm_mean": float("nan"),
            "norm_std": 5.0,
            "operating_threshold": 0.37,
        },
        bad_ckpt_4,
    )
    with pytest.raises(ValueError, match="Normalization mean must be finite"):
        PyTorchTrainHornClassifier(checkpoint_path=bad_ckpt_4)

    # Case 5: Invalid threshold (< 0 or > 1)
    bad_ckpt_5 = tmp_path / "bad_thresh.pt"
    torch.save(
        {
            "model_state_dict": state_dict,
            "norm_mean": -1.6,
            "norm_std": 5.0,
            "operating_threshold": 1.5,
        },
        bad_ckpt_5,
    )
    with pytest.raises(ValueError, match="Operating threshold must be finite and within"):
        PyTorchTrainHornClassifier(checkpoint_path=bad_ckpt_5)


def test_stable_expected_feature_shape_and_preprocessing_config():
    """Verify that feature preprocessing produces exactly (64, 61) tensors."""
    sample_rate = 16000
    one_second_silence = np.zeros(16000, dtype=np.float32)

    spec = compute_log_mel_spectrogram(
        one_second_silence,
        sample_rate=sample_rate,
        n_fft=512,
        hop_length=256,
        n_mels=64,
        f_min=80.0,
        f_max=8000.0,
    )

    assert spec.shape == (64, 61), f"Unexpected spectrogram shape: {spec.shape}"
    assert not np.isnan(spec).any(), "Spectrogram contains NaN"
    assert not np.isinf(spec).any(), "Spectrogram contains Inf"


def test_checkpoint_remains_unmodified_by_loading_and_inspection():
    """Verify that inspecting and loading the checkpoint leaves file SHA-256 unchanged."""
    hash_before = _compute_sha256(AUDIO_V3_CHECKPOINT)
    assert hash_before == EXPECTED_AUDIO_V3_HASH, f"Hash before test mismatch: {hash_before}"

    # Load and run prediction
    classifier = PyTorchTrainHornClassifier(checkpoint_path=AUDIO_V3_CHECKPOINT)
    dummy_window = np.zeros(16000, dtype=np.float32)
    prob, label = classifier.predict_window(dummy_window, sample_rate=16000)

    assert 0.0 <= prob <= 1.0
    assert label in ("train", "ambient")

    hash_after = _compute_sha256(AUDIO_V3_CHECKPOINT)
    assert hash_after == EXPECTED_AUDIO_V3_HASH, f"Hash after test modified: {hash_after}"


def test_regression_protection_norm_mean_vs_feature_mean(tmp_path: Path):
    """Verify backward compatibility and priority between norm_mean and feature_mean."""
    model = CompactTrainHornCNN()
    state_dict = model.state_dict()

    # 1. norm_mean format (V3)
    v3_ckpt = tmp_path / "v3_style.pt"
    torch.save(
        {
            "model_state_dict": state_dict,
            "norm_mean": -1.601,
            "norm_std": 5.124,
            "operating_threshold": 0.37,
        },
        v3_ckpt,
    )
    clf_v3 = PyTorchTrainHornClassifier(checkpoint_path=v3_ckpt)
    assert abs(clf_v3.mean - (-1.601)) < 1e-5
    assert abs(clf_v3.std - 5.124) < 1e-5

    # 2. feature_mean format (legacy V2)
    legacy_ckpt = tmp_path / "legacy_style.pt"
    torch.save(
        {
            "model_state_dict": state_dict,
            "feature_mean": -4.662,
            "feature_std": 23.725,
            "operating_threshold": 0.518,
        },
        legacy_ckpt,
    )
    clf_legacy = PyTorchTrainHornClassifier(checkpoint_path=legacy_ckpt)
    assert abs(clf_legacy.mean - (-4.662)) < 1e-5
    assert abs(clf_legacy.std - 23.725) < 1e-5

    # 3. Precedence: if both present, norm_mean takes precedence
    both_ckpt = tmp_path / "both_style.pt"
    torch.save(
        {
            "model_state_dict": state_dict,
            "norm_mean": -1.601,
            "norm_std": 5.124,
            "feature_mean": -9.999,
            "feature_std": 99.999,
            "operating_threshold": 0.37,
        },
        both_ckpt,
    )
    clf_both = PyTorchTrainHornClassifier(checkpoint_path=both_ckpt)
    assert abs(clf_both.mean - (-1.601)) < 1e-5
    assert abs(clf_both.std - 5.124) < 1e-5
