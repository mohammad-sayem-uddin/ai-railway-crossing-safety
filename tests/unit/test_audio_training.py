"""Unit tests for audio model training infrastructure, checkpointing, and calibration."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from railway_detection.audio.evaluation import (
    compute_pr_curve,
    compute_roc_curve,
)
from railway_detection.audio.training import (
    AudioModelCheckpoint,
    AudioTrainer,
    AudioTrainingConfig,
    AudioTrainingGatingError,
)

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_audio_training_config_defaults():
    config = AudioTrainingConfig()
    assert config.model_name == "train_horn_classifier"
    assert config.batch_size == 32
    assert config.max_epochs == 50
    assert config.learning_rate == 0.001
    assert config.seed == 42


def test_audio_model_checkpoint_roundtrip(tmp_path):
    ckpt = AudioModelCheckpoint(
        model_name="train_horn_classifier",
        model_level="level_3_cnn",
        operating_threshold=0.5184,
        feature_params={"n_mels": 64, "n_fft": 512, "sample_rate": 16000},
        metrics={"auc_roc": 0.8868, "f1": 0.6971, "accuracy": 0.7350},
    )
    save_path = tmp_path / "checkpoint.json"
    ckpt.save(save_path)
    assert save_path.exists()

    loaded = AudioModelCheckpoint.load(save_path)
    assert loaded.model_name == "train_horn_classifier"
    assert loaded.model_level == "level_3_cnn"
    assert loaded.operating_threshold == 0.5184
    assert loaded.metrics["auc_roc"] == 0.8868


def test_audio_trainer_gates_pass_with_full_dataset():
    """Verify pretraining gates pass when both positive and negative samples are present."""
    trainer = AudioTrainer(workspace_root=WORKSPACE_ROOT)
    # Both train and val negative counts must be > 0
    assert trainer.train_loader.negative_count > 0
    assert trainer.val_loader.negative_count > 0
    assert trainer.train_loader.positive_count >= 10
    # verify_pretraining_gates should not raise
    trainer.verify_pretraining_gates()


def test_audio_trainer_gates_block_layer_b_contamination(tmp_path):
    """Verify pretraining gates strictly reject any Layer B test audio contamination."""
    contaminated_manifest = tmp_path / "contaminated.json"
    items = []
    # 10 positive samples (one contaminated with layer_b)
    items.append({
        "window_id": "pos_001_w000",
        "source_file": "layer_b/videos/event_001/camera_front.mov",
        "source_sha256": "fake_hash",
        "split_group_id": "g1",
        "class_name": "train_horn",
        "class_id": 1,
        "partition": "train",
        "window_index": 0,
        "start_time_s": 0.0,
        "end_time_s": 1.0,
        "duration_s": 1.0,
        "sample_rate": 16000,
        "standardized_wav_path": "data/processed/layer_b/event_001.wav",
        "feature_path": "dummy.npy",
        "feature_type": "log_mel_spectrogram",
        "feature_shape": [64, 61],
        "dataset_role": "real_world_evaluation",
    })
    for i in range(2, 12):
        items.append({
            "window_id": f"pos_{i:03d}_w000",
            "source_file": f"{i}.mp3",
            "source_sha256": f"hash_{i}",
            "split_group_id": f"g_{i}",
            "class_name": "train_horn",
            "class_id": 1,
            "partition": "train",
            "window_index": 0,
            "start_time_s": 0.0,
            "end_time_s": 1.0,
            "duration_s": 1.0,
            "sample_rate": 16000,
            "standardized_wav_path": f"{i}.wav",
            "feature_path": "dummy.npy",
            "feature_type": "log_mel_spectrogram",
            "feature_shape": [64, 61],
            "dataset_role": "audio_model_development",
        })
    # Negative train and val samples
    items.append({
        "window_id": "neg_001_w000",
        "source_file": "neg1.wav",
        "source_sha256": "fake_neg1",
        "split_group_id": "neg_g1",
        "class_name": "non_train_horn",
        "class_id": 0,
        "partition": "train",
        "window_index": 0,
        "start_time_s": 0.0,
        "end_time_s": 1.0,
        "duration_s": 1.0,
        "sample_rate": 16000,
        "standardized_wav_path": "neg1.wav",
        "feature_path": "dummy_neg.npy",
        "feature_type": "log_mel_spectrogram",
        "feature_shape": [64, 61],
        "dataset_role": "audio_model_development",
    })
    items.append({
        "window_id": "neg_002_w000",
        "source_file": "neg2.wav",
        "source_sha256": "fake_neg2",
        "split_group_id": "neg_g2",
        "class_name": "non_train_horn",
        "class_id": 0,
        "partition": "val",
        "window_index": 0,
        "start_time_s": 0.0,
        "end_time_s": 1.0,
        "duration_s": 1.0,
        "sample_rate": 16000,
        "standardized_wav_path": "neg2.wav",
        "feature_path": "dummy_neg.npy",
        "feature_type": "log_mel_spectrogram",
        "feature_shape": [64, 61],
        "dataset_role": "audio_model_development",
    })
    contaminated_manifest.write_text(json.dumps(items), encoding="utf-8")
    cfg = AudioTrainingConfig(manifest_path=str(contaminated_manifest))
    trainer = AudioTrainer(config=cfg, workspace_root=WORKSPACE_ROOT)
    with pytest.raises(AudioTrainingGatingError) as exc_info:
        trainer.verify_pretraining_gates()

    assert "CRITICAL SAFETY VIOLATION" in str(exc_info.value)
    assert "Layer B" in str(exc_info.value)


def test_roc_and_pr_curve_properties():
    """Verify mathematical properties of ROC and PR curves."""
    y_true = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    y_score = np.array([0.95, 0.85, 0.80, 0.70, 0.30, 0.20, 0.15, 0.05])

    fpr, tpr, _, roc_auc = compute_roc_curve(y_true, y_score)
    assert roc_auc == 1.0  # Perfect separation
    assert fpr[0] == 0.0
    assert tpr[-1] == 1.0

    prec, rec, _, pr_auc = compute_pr_curve(y_true, y_score)
    assert pr_auc == 1.0
