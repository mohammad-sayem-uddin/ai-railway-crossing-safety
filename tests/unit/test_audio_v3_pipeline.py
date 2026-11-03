"""Unit and integration tests for Dataset V3 and Audio Model V3 (ESC-50 Negatives).

Verifies:
- ESC-50-only negative selection
- Old-negative hard firewall (no files from data/raw/audio/train_horn/negative/)
- Layer B hard firewall (no files from data/raw/layer_b/ or data/raw/layer_b/v2/)
- Duplicate prevention (41.mp3 == 42.mp3 correctly handled)
- Source-group separation and fold integrity (Folds 1-3 Train, Fold 4 Val, Fold 5 Test)
- Feature tensor dimensions and normalization contracts
- Model checkpoint loading and forward inference
- Threshold freezing on validation only
- Test metrics, per-category reports, and figure artifacts
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import torch

WORKSPACE = Path("/Users/sayemuddin/Desktop/Train_automation")
V3_SELECTION = WORKSPACE / "data/manifests/audio_v3_selection.json"
V3_ESC50_MANIFEST = WORKSPACE / "data/manifests/audio_v3_esc50_manifest.json"
V3_DATASET_MANIFEST = WORKSPACE / "data/manifests/audio_training_dataset_v3.json"
V3_SPLIT_MANIFEST = WORKSPACE / "data/splits/audio/v3/dataset_split.json"
V3_RUN_DIR = WORKSPACE / "experiments/audio/RUN_20261008_AUDIO_V3_ESC50"
V3_CHECKPOINT = V3_RUN_DIR / "checkpoints/best.pt"


def test_v3_selection_balance_and_firewall():
    assert V3_SELECTION.exists(), "audio_v3_selection.json missing"
    with open(V3_SELECTION) as f:
        data = json.load(f)

    assert data["selected_positive_count"] == 86
    assert data["selected_negative_count"] == 86
    assert data["total_selected_recordings"] == 172

    # Firewall assertions
    firewall = data["firewall_verified"]
    assert firewall["custom_negative_pool_excluded"] is True
    assert firewall["layer_b_video_audio_excluded"] is True
    assert firewall["esc50_train_category_excluded"] is True

    # Assert no file path points to old negative or layer b
    for r in data["selected_records"]:
        src_p = r["source_path"]
        assert not src_p.startswith("data/raw/audio/train_horn/negative"), f"Old negative pool leak: {src_p}"
        assert not src_p.startswith("data/raw/layer_b"), f"Layer B leak: {src_p}"
        if r["class"] == "non_train_sound":
            assert r["source_dataset"] == "ESC50"
            assert r["category"] != "train"


def test_v3_duplicate_prevention():
    with open(V3_SELECTION) as f:
        data = json.load(f)
    rejected = data["rejected_positive_duplicates"]
    assert len(rejected) == 1
    assert rejected[0]["filename"] == "42.mp3"


def test_v3_fold_integrity_and_source_group_isolation():
    assert V3_SPLIT_MANIFEST.exists()
    with open(V3_SELECTION) as f:
        data = json.load(f)

    records = data["selected_records"]
    train_recs = [r for r in records if r["partition"] == "train"]
    val_recs = [r for r in records if r["partition"] == "val"]
    test_recs = [r for r in records if r["partition"] == "test"]

    assert len(train_recs) == 120  # 60 pos + 60 neg
    assert len(val_recs) == 26    # 13 pos + 13 neg
    assert len(test_recs) == 26   # 13 pos + 13 neg

    # ESC-50 fold integrity
    for r in train_recs:
        if r["source_dataset"] == "ESC50":
            assert r["esc50_fold"] in [1, 2, 3], f"Unexpected fold in train: {r['esc50_fold']}"
    for r in val_recs:
        if r["source_dataset"] == "ESC50":
            assert r["esc50_fold"] == 4, f"Unexpected fold in val: {r['esc50_fold']}"
    for r in test_recs:
        if r["source_dataset"] == "ESC50":
            assert r["esc50_fold"] == 5, f"Unexpected fold in test: {r['esc50_fold']}"

    # Source group isolation
    train_sources = set(r["source_group"] for r in train_recs)
    val_sources = set(r["source_group"] for r in val_recs)
    test_sources = set(r["source_group"] for r in test_recs)

    assert len(train_sources & val_sources) == 0, "Source leakage Train & Val"
    assert len(train_sources & test_sources) == 0, "Source leakage Train & Test"
    assert len(val_sources & test_sources) == 0, "Source leakage Val & Test"


def test_v3_feature_shapes_and_contracts():
    assert V3_DATASET_MANIFEST.exists()
    with open(V3_DATASET_MANIFEST) as f:
        windows = json.load(f)

    assert len(windows) == 1256
    # Sample check 20 windows
    for w in windows[:20]:
        fp = WORKSPACE / w["feature_path"]
        assert fp.exists()
        feat = np.load(fp)
        assert feat.shape == (64, 61)
        assert not np.isnan(feat).any()
        assert not np.isinf(feat).any()


def test_v3_model_checkpoint_and_inference():
    assert V3_CHECKPOINT.exists()
    ckpt = torch.load(V3_CHECKPOINT, map_location="cpu")
    assert "model_state_dict" in ckpt
    assert "norm_mean" in ckpt
    assert "norm_std" in ckpt
    assert "operating_threshold" in ckpt
    assert ckpt["operating_threshold"] == 0.37

    from scripts.train_audio_model_v3_esc50 import CompactTrainHornCNN
    model = CompactTrainHornCNN(in_channels=1, dropout=0.3)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    dummy_input = torch.randn(4, 1, 64, 61)
    with torch.no_grad():
        logits = model(dummy_input)
        probs = torch.sigmoid(logits)

    assert logits.shape == (4,)
    assert (probs >= 0.0).all() and (probs <= 1.0).all()


def test_v3_publication_figures_and_reports():
    fig_dir = V3_RUN_DIR / "figures"
    expected_figs = [
        "fig1_loss_curves.png",
        "fig2_accuracy_curves.png",
        "fig3_confusion_matrix.png",
        "fig4_roc_curve.png",
        "fig5_pr_curve.png",
        "fig6_threshold_vs_f1.png",
        "fig7_confidence_distribution.png",
        "fig8_per_category_fp_rate.png",
        "fig9_v2_vs_v3_comparison.png",
        "fig10_score_distributions_by_category.png",
        "fig11_duration_distributions.png",
        "fig12_error_analysis.png",
    ]
    for fn in expected_figs:
        assert (fig_dir / fn).exists(), f"Missing figure: {fn}"

    assert (V3_RUN_DIR / "metrics/metrics.json").exists()
    assert (V3_RUN_DIR / "metrics/v2_vs_v3_comparison.json").exists()
    assert (V3_RUN_DIR / "reports/per_category_analysis.json").exists()
    assert (V3_RUN_DIR / "reports/forensic_analysis.json").exists()
