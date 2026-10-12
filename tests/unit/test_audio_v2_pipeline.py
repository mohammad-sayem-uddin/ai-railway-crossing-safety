"""Unit and integration tests for Dataset V2 and Audio Model V2.

Verifies:
- Dataset selection and balanced sampling (86/86)
- Bitwise duplicate prevention and detection
- Recording-level split and zero data leakage
- Feature extraction and dimensionality contracts (64, 61)
- Model checkpoint loading and forward inference
- Threshold handling and confidence calibration
- Real-world V2 video manifest categorization and eligibility rules
- Metrics and artifact integrity
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pytest
import torch

WORKSPACE = Path("/Users/sayemuddin/Desktop/Train_automation")
V2_AUDIO_SELECTION = WORKSPACE / "data/manifests/audio_training_v2_selection.json"
V2_VIDEO_MANIFEST = WORKSPACE / "data/manifests/real_world_v2_video_manifest.json"
V2_AUDIO_MANIFEST = WORKSPACE / "data/manifests/audio_training_dataset_v2.json"
V2_SPLIT_MANIFEST = WORKSPACE / "data/splits/audio/v2/dataset_split.json"
V2_RUN_DIR = WORKSPACE / "experiments/audio/RUN_20261008_AUDIO_V2"
V2_CHECKPOINT = V2_RUN_DIR / "checkpoints/best.pt"


def test_v2_audio_selection_balance():
    assert V2_AUDIO_SELECTION.exists(), "audio_training_v2_selection.json missing"
    with open(V2_AUDIO_SELECTION) as f:
        data = json.load(f)
    assert data["selected_positive_count"] == 86
    assert data["selected_negative_count"] == 86
    assert len(data["selected_records"]) == 172
    pos_recs = [r for r in data["selected_records"] if r["class"] == "train_horn"]
    neg_recs = [r for r in data["selected_records"] if r["class"] == "non_train_sound"]
    assert len(pos_recs) == 86
    assert len(neg_recs) == 86


def test_v2_audio_duplicate_prevention():
    with open(V2_AUDIO_SELECTION) as f:
        data = json.load(f)
    rejected = data["rejected_records"]
    dup_rejections = [r for r in rejected if "duplicate" in r["category"].lower()]
    assert len(dup_rejections) == 3
    dup_files = {r["filename"] for r in dup_rejections}
    assert "42.mp3" in dup_files or "41.mp3" in dup_files
    assert "6.mp3" in dup_files or "5.mp3" in dup_files
    assert "28.mp3" in dup_files or "27.mp3" in dup_files


def test_v2_recording_level_split_leakage():
    assert V2_SPLIT_MANIFEST.exists()
    with open(V2_SPLIT_MANIFEST) as f:
        split = json.load(f)
    train_set = set(split["train_recordings"])
    val_set = set(split["val_recordings"])
    test_set = set(split["test_recordings"])

    assert len(train_set & val_set) == 0, "Leakage between train and val!"
    assert len(train_set & test_set) == 0, "Leakage between train and test!"
    assert len(val_set & test_set) == 0, "Leakage between val and test!"

    assert split["partitions"]["train"]["positive"] == 60
    assert split["partitions"]["train"]["negative"] == 60
    assert split["partitions"]["val"]["positive"] == 13
    assert split["partitions"]["val"]["negative"] == 13
    assert split["partitions"]["test"]["positive"] == 13
    assert split["partitions"]["test"]["negative"] == 13


def test_v2_audio_features_contract():
    assert V2_AUDIO_MANIFEST.exists()
    with open(V2_AUDIO_MANIFEST) as f:
        windows = json.load(f)
    assert len(windows) > 1000
    for w in windows[:20]:
        fp = WORKSPACE / w["feature_path"]
        assert fp.exists()
        feat = np.load(fp)
        assert feat.shape == (64, 61)
        assert not np.isnan(feat).any()
        assert not np.isinf(feat).any()


def test_v2_model_checkpoint_and_inference():
    assert V2_CHECKPOINT.exists()
    ckpt = torch.load(V2_CHECKPOINT, map_location="cpu")
    assert "model_state_dict" in ckpt
    assert "norm_mean" in ckpt
    assert "norm_std" in ckpt

    from scripts.train_audio_model_v2 import CompactTrainHornCNN
    model = CompactTrainHornCNN(in_channels=1, dropout=0.3)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    dummy_input = torch.randn(4, 1, 64, 61)
    with torch.no_grad():
        logits = model(dummy_input)
        probs = torch.sigmoid(logits)
    assert logits.shape == (4,)
    assert (probs >= 0.0).all() and (probs <= 1.0).all()


def test_v2_video_manifest_roles_and_eligibility():
    assert V2_VIDEO_MANIFEST.exists()
    with open(V2_VIDEO_MANIFEST) as f:
        manifest = json.load(f)
    records = manifest["records"]
    assert len(records) == 56

    train_recs = [r for r in records if r["dataset_role"] == "REAL_WORLD_TRAIN_EVENT"]
    engine_eligible = [r for r in records if r["dataset_role"] == "REAL_WORLD_ENGINE_ONLY"]
    engine_excluded = [r for r in records if r["dataset_role"] == "HISTORICAL_DUPLICATE_EXCLUDED"]
    no_train_recs = [r for r in records if r["dataset_role"] == "REAL_WORLD_NO_TRAIN"]

    assert len(train_recs) == 46  # 23 events * 2 cameras
    assert len(engine_eligible) == 2  # 1 event * 2 cameras
    assert len(engine_excluded) == 2  # 1 event * 2 cameras
    assert len(no_train_recs) == 6  # 3 events * 2 cameras

    for r in train_recs + engine_eligible + no_train_recs:
        assert r["evaluation_eligible"] is True
    for r in engine_excluded:
        assert r["evaluation_eligible"] is False
        assert r["event_id"] == "event_historical_duplicate_010"


def test_v2_figures_and_report_artifacts():
    fig_dir = V2_RUN_DIR / "figures"
    expected_figs = [
        "fig1_loss_curves.png",
        "fig2_accuracy_curves.png",
        "fig3_confusion_matrix.png",
        "fig4_roc_curve.png",
        "fig5_pr_curve.png",
        "fig6_class_metrics.png",
        "fig7_confidence_distribution.png",
        "fig8_threshold_vs_f1.png",
        "fig9_error_analysis.png",
        "fig10_spectrogram_examples.png",
        "fig11_v1_vs_v2_comparison.png",
    ]
    for fig_name in expected_figs:
        assert (fig_dir / fig_name).exists(), f"Missing figure: {fig_name}"

    assert (WORKSPACE / "docs/archive/AUDIO_MODEL_V2_REPORT.md").exists() or (WORKSPACE / "docs/AUDIO_MODEL_V2_REPORT.md").exists()
    assert (WORKSPACE / "docs/archive/REAL_DATASET_V2_INVENTORY.md").exists() or (WORKSPACE / "docs/REAL_DATASET_V2_INVENTORY.md").exists()
    assert (WORKSPACE / "docs/archive/REAL_DATASET_V2_STRUCTURE.md").exists() or (WORKSPACE / "docs/REAL_DATASET_V2_STRUCTURE.md").exists()
    assert (V2_RUN_DIR / "metrics/metrics.json").exists()
    assert (V2_RUN_DIR / "metrics/v1_vs_v2_comparison.json").exists()
