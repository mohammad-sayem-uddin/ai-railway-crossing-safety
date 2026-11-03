"""Unit tests verifying audio preprocessing, group-disjoint splitting, and data leakage prevention."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from railway_detection.audio.dataset import AudioDatasetLoader
from railway_detection.audio.evaluation import (
    calibrate_operating_threshold,
    compute_binary_metrics,
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
RAW_POS_DIR = WORKSPACE_ROOT / "data" / "raw" / "audio" / "train_horn" / "positive"
MANIFEST_PATH = WORKSPACE_ROOT / "data" / "manifests" / "audio_training_dataset.json"
ORIGINAL_MANIFEST = WORKSPACE_ROOT / "data" / "manifests" / "train_horn_audio_manifest.json"


@pytest.fixture
def manifest_records():
    assert MANIFEST_PATH.exists(), f"Manifest {MANIFEST_PATH} must exist"
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_no_source_recording_in_multiple_partitions(manifest_records):
    """Leakage Test 1: Verify each unique source recording appears in strictly one partition."""
    source_to_partitions: dict[str, set[str]] = {}
    for r in manifest_records:
        src = r["source_file"]
        source_to_partitions.setdefault(src, set()).add(r["partition"])

    for src, partitions in source_to_partitions.items():
        assert len(partitions) == 1, f"Data leakage detected! {src} appears in multiple partitions: {partitions}"


def test_no_sha256_duplicate_in_multiple_partitions(manifest_records):
    """Leakage Test 2: Verify no SHA-256 hash appears across multiple partitions."""
    sha_to_partitions: dict[str, set[str]] = {}
    for r in manifest_records:
        sha = r["source_sha256"]
        sha_to_partitions.setdefault(sha, set()).add(r["partition"])

    for sha, partitions in sha_to_partitions.items():
        assert len(partitions) == 1, f"SHA-256 duplicate leakage! Hash {sha[:12]} appears in multiple partitions: {partitions}"


def test_duplicate_41_and_42_in_same_partition(manifest_records):
    """Leakage Test 3: Specifically enforce 41.mp3 and 42.mp3 are locked into the identical partition."""
    rec_41 = next((r for r in manifest_records if r["source_file"] == "41.mp3"), None)
    rec_42 = next((r for r in manifest_records if r["source_file"] == "42.mp3"), None)

    assert rec_41 is not None and rec_42 is not None
    assert rec_41["source_sha256"] == rec_42["source_sha256"]
    assert rec_41["partition"] == rec_42["partition"], (
        f"41.mp3 ({rec_41['partition']}) and 42.mp3 ({rec_42['partition']}) must be in the same partition!"
    )


def test_windows_from_same_source_remain_together(manifest_records):
    """Leakage Test 4: All sliding windows from a single source file must share the file's partition."""
    file_partitions: dict[str, str] = {}
    for r in manifest_records:
        fname = r["source_file"]
        part = r["partition"]
        if fname in file_partitions:
            assert file_partitions[fname] == part, f"Window partition mismatch for file {fname}"
        else:
            file_partitions[fname] = part


def test_layer_b_event_audio_never_included(manifest_records):
    """Leakage Test 5 & 6: Layer B evaluation videos must NEVER be ingested into training dataset."""
    for r in manifest_records:
        assert "layer_b" not in r["source_relative_path"].lower()
        assert "layer_b" not in r["standardized_wav_path"].lower()
        assert not r["source_file"].endswith(".mov")


def test_raw_source_files_remain_unchanged():
    """Integrity Test 7: Verify raw positive source audio files have identical SHA-256 hashes as original manifest."""
    assert ORIGINAL_MANIFEST.exists()
    with open(ORIGINAL_MANIFEST, encoding="utf-8") as f:
        original_records = json.load(f)

    for r in original_records:
        file_path = WORKSPACE_ROOT / r["relative_path"]
        assert file_path.exists()
        import hashlib
        h = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert h == r["sha256"], f"Raw file altered! {file_path} hash changed!"


def test_window_features_shape_and_range(manifest_records):
    """Feature Test: Verify precomputed Log-Mel spectrograms conform to (64, 63) without NaNs."""
    # Check a sample of 20 random windows across partitions
    import random
    sampled_records = random.sample(manifest_records, min(20, len(manifest_records)))

    for r in sampled_records:
        feat_path = WORKSPACE_ROOT / r["feature_path"]
        assert feat_path.exists()
        feat = np.load(feat_path)
        assert feat.shape == (64, 61), f"Expected shape (64, 61), got {feat.shape}"
        assert not np.isnan(feat).any()
        assert not np.isinf(feat).any()


def test_audio_dataset_loader_batches():
    """Loader Test: Verify AudioDatasetLoader yields well-formed mini-batches."""
    loader = AudioDatasetLoader(MANIFEST_PATH, partition="train", workspace_root=WORKSPACE_ROOT)
    assert len(loader) > 0

    batch_iter = loader.generate_batches(batch_size=16, shuffle=False)
    first_batch = next(batch_iter)

    assert first_batch.features.shape == (16, 64, 61)
    assert first_batch.labels.shape == (16,)
    assert len(first_batch.window_ids) == 16
    assert len(first_batch.source_files) == 16


def test_training_blocked_without_negative_data(tmp_path):
    """Gating Test: Attempting to train without negative data must raise AudioTrainingGatingError."""
    pos_only_manifest = tmp_path / "pos_only_manifest.json"
    pos_only_manifest.write_text(
        json.dumps([
            {
                "window_id": "pos_001_w000",
                "source_file": "1.mp3",
                "source_sha256": "abc",
                "split_group_id": "g1",
                "class_name": "train_horn",
                "class_id": 1,
                "partition": "train",
                "window_index": 0,
                "start_time_s": 0.0,
                "end_time_s": 1.0,
                "duration_s": 1.0,
                "sample_rate": 16000,
                "standardized_wav_path": "dummy.wav",
                "feature_path": "dummy.npy",
                "feature_type": "log_mel_spectrogram",
                "feature_shape": [64, 61],
                "dataset_role": "audio_model_development",
            }
        ]),
        encoding="utf-8",
    )
    rel_path = pos_only_manifest.relative_to(WORKSPACE_ROOT) if pos_only_manifest.is_relative_to(WORKSPACE_ROOT) else str(pos_only_manifest)
    cfg = AudioTrainingConfig(manifest_path=rel_path)
    trainer = AudioTrainer(config=cfg, workspace_root=WORKSPACE_ROOT)
    with pytest.raises(AudioTrainingGatingError) as exc_info:
        trainer.verify_pretraining_gates()

    assert "Missing negative background audio" in str(exc_info.value)
    assert "AUDIO TRAINING BLOCKED" in str(exc_info.value)


def test_binary_metrics_exact_calculation():
    """Metrics Test: Verify binary metrics, ROC, and PR curves on synthetic test vectors."""
    y_true = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    y_score = np.array([0.9, 0.8, 0.7, 0.3, 0.6, 0.2, 0.1, 0.05])

    metrics = compute_binary_metrics(y_true, y_score, threshold=0.5)
    # y_pred = [1, 1, 1, 0, 1, 0, 0, 0]
    # TP: 3, FP: 1, FN: 1, TN: 3
    assert metrics.tp == 3
    assert metrics.fp == 1
    assert metrics.fn == 1
    assert metrics.tn == 3
    assert metrics.accuracy == 6.0 / 8.0
    assert metrics.precision == 3.0 / 4.0
    assert metrics.recall == 3.0 / 4.0
    assert metrics.f1_score == 0.75

    fpr, tpr, _, auc_roc = compute_roc_curve(y_true, y_score)
    assert 0.8 <= auc_roc <= 1.0

    prec, rec, _, pr_auc = compute_pr_curve(y_true, y_score)
    assert 0.7 <= pr_auc <= 1.0


def test_operating_threshold_calibration():
    """Threshold Test: Verify threshold calibration selects optimal F1 cutoff."""
    y_true = np.array([1, 1, 1, 0, 0, 0])
    y_score = np.array([0.8, 0.7, 0.6, 0.4, 0.2, 0.1])

    best_thresh, best_metrics = calibrate_operating_threshold(y_true, y_score, target_metric="f1")
    assert best_metrics.f1_score == 1.0  # Separable at t in (0.4, 0.6]
    assert 0.4 < best_thresh <= 0.8


def test_audio_checkpoint_serialization(tmp_path):
    """Checkpoint Test: Verify saving and loading model metadata and operating threshold."""
    ckpt = AudioModelCheckpoint(
        model_name="test_model",
        model_level="level_2_classical",
        operating_threshold=0.65,
        feature_params={"n_mels": 64, "n_fft": 512},
        metrics={"auc_roc": 0.95, "f1": 0.88},
    )

    ckpt_file = tmp_path / "checkpoint.json"
    saved = ckpt.save(ckpt_file)
    assert saved.exists()

    loaded = AudioModelCheckpoint.load(ckpt_file)
    assert loaded.model_name == "test_model"
    assert loaded.operating_threshold == 0.65
    assert loaded.feature_params["n_mels"] == 64
    assert loaded.metrics["f1"] == 0.88
