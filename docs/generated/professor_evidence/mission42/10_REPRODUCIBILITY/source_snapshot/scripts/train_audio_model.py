#!/usr/bin/env python3
"""Train, evaluate, calibrate, and generate publication-quality figures for the train-horn audio classifier.

Strict Research Protocol Constraints:
- Layer B real-world video audio is 100% excluded and untouched.
- Leakage-safe split: Group-disjoint, recording-level split verified.
- Negative data: Stratified ESC-50 subset (87 clips).
- Positive data: 87 clips (86 unique + 1 duplicate pair locked to train).
- Model: CompactTrainHornCNN (PyTorch).
- Evaluation: Optimal threshold calibrated on Validation set, then frozen for Test evaluation.
- Figures: 10 publication-quality research figures (300 DPI).
- Reproducibility: Full machine-readable artifacts, metrics, and report.
"""

from __future__ import annotations

import json
import logging
import random
import shutil
import sys
import time
from collections import defaultdict
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

# Ensure project root is in sys.path
WORKSPACE_ROOT = Path("/Users/sayemuddin/Desktop/Train_automation")
if str(WORKSPACE_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT / "src"))

from railway_detection.audio.dataset import AudioDatasetLoader
from railway_detection.audio.evaluation import (
    BinaryClassificationMetrics,
    calibrate_operating_threshold,
    compute_binary_metrics,
    compute_pr_curve,
    compute_roc_curve,
)
from railway_detection.audio.model import CompactTrainHornCNN, SpectralEnergyBaseline
from railway_detection.audio.training import AudioTrainer, AudioTrainingConfig
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def apply_training_augmentation(feat: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Conservative training-only feature augmentation on Log-Mel spectrogram (64, 61)."""
    aug = feat.copy()
    
    # 1. Mild Gain variation (+/- 2.5 dB)
    gain_db = rng.uniform(-2.5, 2.5)
    aug = aug + gain_db
    
    # 2. Mild temporal roll / shift (+/- 3 frames ~ 0.05s)
    shift = rng.integers(-3, 4)
    if shift != 0:
        aug = np.roll(aug, shift, axis=1)
        
    # 3. Mild additive Gaussian noise (SNR 25-35 dB equivalent on spectrogram)
    noise_std = rng.uniform(0.01, 0.05)
    noise = rng.normal(0.0, noise_std, size=aug.shape)
    aug = aug + noise
    
    return aug


def train_epoch(
    model: nn.Module,
    loader: AudioDatasetLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    mean: float,
    std: float,
    device: torch.device,
    rng: np.random.Generator,
    batch_size: int = 32,
) -> tuple[float, float]:
    model.train()
    total_loss = 0.0
    correct = 0
    total_samples = 0
    
    # Shuffle records
    indices = np.arange(len(loader.records))
    rng.shuffle(indices)
    
    for start_idx in range(0, len(indices), batch_size):
        b_indices = indices[start_idx : start_idx + batch_size]
        feats = []
        labels = []
        for idx in b_indices:
            rec = loader.records[idx]
            raw_feat = loader.load_feature(rec)
            aug_feat = apply_training_augmentation(raw_feat, rng)
            norm_feat = (aug_feat - mean) / std
            feats.append(norm_feat)
            labels.append(rec.class_id)
            
        x = torch.from_numpy(np.stack(feats)).float().to(device)
        y = torch.from_numpy(np.array(labels)).float().to(device)
        
        optimizer.zero_grad()
        logits = model(x)
        loss = criterion(logits, y)
        loss.backward()
        optimizer.step()
        
        total_loss += float(loss.item()) * len(y)
        probs = torch.sigmoid(logits)
        preds = (probs >= 0.5).float()
        correct += int((preds == y).sum().item())
        total_samples += len(y)
        
    return total_loss / max(1, total_samples), correct / max(1, total_samples)


def evaluate_split(
    model: nn.Module,
    loader: AudioDatasetLoader,
    criterion: nn.Module,
    mean: float,
    std: float,
    device: torch.device,
    threshold: float = 0.5,
) -> tuple[float, np.ndarray, np.ndarray, list[dict[str, Any]]]:
    model.eval()
    total_loss = 0.0
    all_scores = []
    all_labels = []
    predictions_meta = []
    
    with torch.no_grad():
        for rec in loader.records:
            raw_feat = loader.load_feature(rec)
            norm_feat = (raw_feat - mean) / std
            x = torch.from_numpy(norm_feat).float().unsqueeze(0).to(device)
            logit = model(x)
            y = torch.tensor([rec.class_id], dtype=torch.float, device=device)
            loss = criterion(logit, y)
            
            prob = float(torch.sigmoid(logit).item())
            total_loss += float(loss.item())
            all_scores.append(prob)
            all_labels.append(rec.class_id)
            
            predictions_meta.append({
                "window_id": rec.window_id,
                "source_file": rec.source_file,
                "class_id": rec.class_id,
                "class_name": rec.class_name,
                "category": getattr(rec, "category", "train_horn" if rec.class_id == 1 else "non_train_horn"),
                "probability": prob,
                "prediction": 1 if prob >= threshold else 0,
                "correct": (1 if prob >= threshold else 0) == rec.class_id,
                "split": rec.partition,
                "window_index": rec.window_index,
                "start_time_s": rec.start_time_s,
                "end_time_s": rec.end_time_s,
            })
            
    avg_loss = total_loss / max(1, len(loader.records))
    return avg_loss, np.array(all_labels), np.array(all_scores), predictions_meta


def generate_research_figures(
    run_dir: Path,
    history: dict[str, list[float]],
    val_metrics: BinaryClassificationMetrics,
    test_metrics: BinaryClassificationMetrics,
    val_labels: np.ndarray,
    val_scores: np.ndarray,
    test_labels: np.ndarray,
    test_scores: np.ndarray,
    test_preds: list[dict[str, Any]],
    best_threshold: float,
) -> None:
    fig_dir = run_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    # Set high-quality styling
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "figure.titlesize": 14,
        "figure.dpi": 300,
        "savefig.dpi": 300,
    })
    
    epochs = list(range(1, len(history["train_loss"]) + 1))
    
    # -------------------------------------------------------------
    # Figure 1: Training & Validation Loss Curves
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(epochs, history["train_loss"], label="Training Loss (BCE)", color="#1f77b4", lw=2.2)
    ax.plot(epochs, history["val_loss"], label="Validation Loss (BCE)", color="#ff7f0e", lw=2.2, linestyle="--")
    best_epoch = int(np.argmin(history["val_loss"])) + 1
    ax.axvline(best_epoch, color="#2ca02c", linestyle=":", label=f"Best Checkpoint (Epoch {best_epoch})")
    ax.set_title("Training and Validation Loss Evolution")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Binary Cross-Entropy Loss")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc")
    plt.tight_layout()
    fig.savefig(fig_dir / "fig1_loss_curves.png")
    plt.close(fig)
    
    # -------------------------------------------------------------
    # Figure 2: Training & Validation Accuracy Curves
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(epochs, [a * 100 for a in history["train_acc"]], label="Training Accuracy", color="#1f77b4", lw=2.2)
    ax.plot(epochs, [a * 100 for a in history["val_acc"]], label="Validation Accuracy", color="#2ca02c", lw=2.2, linestyle="--")
    ax.set_title("Training and Validation Window-Level Accuracy")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim([50, 105])
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc")
    plt.tight_layout()
    fig.savefig(fig_dir / "fig2_accuracy_curves.png")
    plt.close(fig)
    
    # -------------------------------------------------------------
    # Figure 3: Test Confusion Matrix
    # -------------------------------------------------------------
    cm = np.array([[test_metrics.tn, test_metrics.fp], [test_metrics.fn, test_metrics.tp]])
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True) * 100
    
    fig, ax = plt.subplots(figsize=(6, 5))
    cax = ax.imshow(cm, cmap="Blues", interpolation="nearest")
    fig.colorbar(cax, fraction=0.046, pad=0.04)
    
    classes = ["Negative\n(Non-Horn)", "Positive\n(Train Horn)"]
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(classes)
    ax.set_yticklabels(classes)
    ax.set_xlabel("Predicted Class")
    ax.set_ylabel("Ground Truth Class")
    ax.set_title(f"Test Confusion Matrix ($T^* = {best_threshold:.3f}$)")
    
    for i in range(2):
        for j in range(2):
            count = cm[i, j]
            pct = cm_norm[i, j]
            color = "white" if count > cm.max() / 2 else "black"
            ax.text(j, i, f"{count}\n({pct:.1f}%)", ha="center", va="center", color=color, weight="bold", fontsize=12)
            
    plt.tight_layout()
    fig.savefig(fig_dir / "fig3_confusion_matrix.png")
    plt.close(fig)
    
    # -------------------------------------------------------------
    # Figure 4: ROC Curves (Validation & Test)
    # -------------------------------------------------------------
    val_fpr, val_tpr, _, val_auc = compute_roc_curve(val_labels, val_scores)
    test_fpr, test_tpr, _, test_auc = compute_roc_curve(test_labels, test_scores)
    
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.plot(val_fpr, val_tpr, label=f"Validation ROC (AUC = {val_auc:.4f})", color="#ff7f0e", lw=2.2)
    ax.plot(test_fpr, test_tpr, label=f"Test ROC (AUC = {test_auc:.4f})", color="#1f77b4", lw=2.5)
    ax.plot([0, 1], [0, 1], linestyle=":", color="#777777", label="Random Classifier (AUC = 0.50)")
    
    # Mark operating point
    op_fpr = test_metrics.fp / max(1, test_metrics.fp + test_metrics.tn)
    op_tpr = test_metrics.tp / max(1, test_metrics.tp + test_metrics.fn)
    ax.scatter([op_fpr], [op_tpr], color="#d62728", s=100, zorder=5, label=f"Operating Point ($T^*={best_threshold:.2f}$)")
    
    ax.set_title("Receiver Operating Characteristic (ROC)")
    ax.set_xlabel("False Positive Rate (1 - Specificity)")
    ax.set_ylabel("True Positive Rate (Recall / Sensitivity)")
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="#cccccc")
    plt.tight_layout()
    fig.savefig(fig_dir / "fig4_roc_curve.png")
    plt.close(fig)
    
    # -------------------------------------------------------------
    # Figure 5: Precision-Recall Curve
    # -------------------------------------------------------------
    val_prec, val_rec, _, val_pr_auc = compute_pr_curve(val_labels, val_scores)
    test_prec, test_rec, _, test_pr_auc = compute_pr_curve(test_labels, test_scores)
    
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.plot(val_rec, val_prec, label=f"Validation PR (AP = {val_pr_auc:.4f})", color="#ff7f0e", lw=2.2)
    ax.plot(test_rec, test_prec, label=f"Test PR (AP = {test_pr_auc:.4f})", color="#1f77b4", lw=2.5)
    ax.scatter([test_metrics.recall], [test_metrics.precision], color="#d62728", s=100, zorder=5, label=f"Operating Point (P={test_metrics.precision:.2f}, R={test_metrics.recall:.2f})")
    
    ax.set_title("Precision-Recall (PR) Curve")
    ax.set_xlabel("Recall (Sensitivity)")
    ax.set_ylabel("Precision (Positive Predictive Value)")
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="lower left", frameon=True, facecolor="white", edgecolor="#cccccc")
    plt.tight_layout()
    fig.savefig(fig_dir / "fig5_pr_curve.png")
    plt.close(fig)
    
    # -------------------------------------------------------------
    # Figure 6: Per-Class Performance Metrics Bar Chart
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 5))
    metrics_names = ["Precision", "Recall", "F1-Score", "Specificity"]
    pos_values = [test_metrics.precision, test_metrics.recall, test_metrics.f1_score, test_metrics.specificity]
    neg_precision = test_metrics.tn / max(1, test_metrics.tn + test_metrics.fn)
    neg_recall = test_metrics.specificity
    neg_f1 = 2 * neg_precision * neg_recall / max(1e-6, neg_precision + neg_recall)
    neg_values = [neg_precision, neg_recall, neg_f1, test_metrics.recall]
    
    x = np.arange(len(metrics_names))
    width = 0.35
    ax.bar(x - width/2, [v * 100 for v in pos_values], width, label="Positive (Train Horn)", color="#1f77b4")
    ax.bar(x + width/2, [v * 100 for v in neg_values], width, label="Negative (Non-Horn)", color="#2ca02c")
    
    ax.set_ylabel("Score (%)")
    ax.set_title("Per-Class Test Performance Metrics")
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_names)
    ax.set_ylim([0, 110])
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="lower right", frameon=True)
    
    for i in range(len(metrics_names)):
        ax.text(x[i] - width/2, pos_values[i]*100 + 1.5, f"{pos_values[i]*100:.1f}%", ha="center", fontsize=9, weight="bold")
        ax.text(x[i] + width/2, neg_values[i]*100 + 1.5, f"{neg_values[i]*100:.1f}%", ha="center", fontsize=9, weight="bold")
        
    plt.tight_layout()
    fig.savefig(fig_dir / "fig6_class_metrics.png")
    plt.close(fig)
    
    # -------------------------------------------------------------
    # Figure 7: Prediction Confidence Distribution (Separation)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 5))
    pos_test_scores = test_scores[test_labels == 1]
    neg_test_scores = test_scores[test_labels == 0]
    
    bins = np.linspace(0.0, 1.0, 26)
    ax.hist(neg_test_scores, bins=bins, alpha=0.6, color="#2ca02c", label=f"True Negatives (N={len(neg_test_scores)})", density=True)
    ax.hist(pos_test_scores, bins=bins, alpha=0.6, color="#1f77b4", label=f"True Positives (N={len(pos_test_scores)})", density=True)
    ax.axvline(best_threshold, color="#d62728", lw=2, linestyle="--", label=f"Calibrated Threshold $T^* = {best_threshold:.3f}$")
    
    ax.set_title("Prediction Confidence Distribution on Held-Out Test Set")
    ax.set_xlabel("Predicted Train Horn Probability")
    ax.set_ylabel("Probability Density")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc")
    plt.tight_layout()
    fig.savefig(fig_dir / "fig7_confidence_distribution.png")
    plt.close(fig)
    
    # -------------------------------------------------------------
    # Figure 8: Threshold vs F1, Precision, and Recall Curves
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 5))
    thresh_eval = np.linspace(0.01, 0.99, 100)
    p_curve, r_curve, f1_curve = [], [], []
    for t in thresh_eval:
        m = compute_binary_metrics(val_labels, val_scores, threshold=t)
        p_curve.append(m.precision)
        r_curve.append(m.recall)
        f1_curve.append(m.f1_score)
        
    ax.plot(thresh_eval, f1_curve, label="F1-Score", color="#2ca02c", lw=2.5)
    ax.plot(thresh_eval, p_curve, label="Precision", color="#1f77b4", lw=2.0, linestyle="--")
    ax.plot(thresh_eval, r_curve, label="Recall", color="#ff7f0e", lw=2.0, linestyle=":")
    ax.axvline(best_threshold, color="#d62728", lw=1.8, linestyle="-.", label=f"Optimal $T^*={best_threshold:.3f}$ (F1={val_metrics.f1_score:.3f})")
    
    ax.set_title("Validation Threshold Calibration Curves")
    ax.set_xlabel("Decision Threshold")
    ax.set_ylabel("Metric Value")
    ax.set_ylim([0, 1.05])
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="lower center", frameon=True, facecolor="white", edgecolor="#cccccc")
    plt.tight_layout()
    fig.savefig(fig_dir / "fig8_threshold_vs_f1.png")
    plt.close(fig)
    
    # -------------------------------------------------------------
    # Figure 9: Error Analysis Plot (Confidence Margin & Failures)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.5, 5))
    sorted_preds = sorted(test_preds, key=lambda x: (x["class_id"], x["probability"]))
    
    x_pos = [i for i, r in enumerate(sorted_preds) if r["class_id"] == 1]
    y_pos = [r["probability"] for r in sorted_preds if r["class_id"] == 1]
    x_neg = [i for i, r in enumerate(sorted_preds) if r["class_id"] == 0]
    y_neg = [r["probability"] for r in sorted_preds if r["class_id"] == 0]
    
    ax.scatter(x_neg, y_neg, color="#2ca02c", alpha=0.7, s=35, label="Negative Ground Truth (Non-Horn)")
    ax.scatter(x_pos, y_pos, color="#1f77b4", alpha=0.7, s=35, label="Positive Ground Truth (Train Horn)")
    ax.axhline(best_threshold, color="#d62728", linestyle="--", lw=2, label=f"Threshold $T^* = {best_threshold:.3f}$")
    
    # Highlight errors
    fp_pts = [(i, r["probability"]) for i, r in enumerate(sorted_preds) if r["class_id"] == 0 and r["prediction"] == 1]
    fn_pts = [(i, r["probability"]) for i, r in enumerate(sorted_preds) if r["class_id"] == 1 and r["prediction"] == 0]
    
    if fp_pts:
        ax.scatter([p[0] for p in fp_pts], [p[1] for p in fp_pts], color="magenta", marker="x", s=100, lw=2.5, label=f"False Positives ({len(fp_pts)})", zorder=6)
    if fn_pts:
        ax.scatter([p[0] for p in fn_pts], [p[1] for p in fn_pts], color="red", marker="^", s=100, lw=2.5, label=f"False Negatives ({len(fn_pts)})", zorder=6)
        
    ax.set_title("Test Sample Error Analysis & Prediction Confidence Distribution")
    ax.set_xlabel("Sorted Test Window Index")
    ax.set_ylabel("Predicted Train Horn Probability")
    ax.set_ylim([-0.05, 1.05])
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#cccccc", fontsize=9)
    plt.tight_layout()
    fig.savefig(fig_dir / "fig9_error_analysis.png")
    plt.close(fig)
    
    # -------------------------------------------------------------
    # Figure 10: Representative Log-Mel Spectrogram Examples
    # -------------------------------------------------------------
    # Pick 4 representative cases: TP, TN, FP (or low conf TP), and FN (or challenging neg)
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    
    tp_sample = next((r for r in test_preds if r["class_id"] == 1 and r["prediction"] == 1 and r["probability"] > 0.8), None)
    tn_sample = next((r for r in test_preds if r["class_id"] == 0 and r["prediction"] == 0 and r["probability"] < 0.2), None)
    fp_sample = next((r for r in test_preds if r["class_id"] == 0 and r["prediction"] == 1), None)
    fn_sample = next((r for r in test_preds if r["class_id"] == 1 and r["prediction"] == 0), None)
    
    if fp_sample is None:
        # Highest confidence negative
        fp_sample = max([r for r in test_preds if r["class_id"] == 0], key=lambda x: x["probability"])
    if fn_sample is None:
        # Lowest confidence positive
        fn_sample = min([r for r in test_preds if r["class_id"] == 1], key=lambda x: x["probability"])
        
    plot_items = [
        ("True Positive: Train Horn Blast", tp_sample, axes[0, 0]),
        ("True Negative: Environmental Sound", tn_sample, axes[0, 1]),
        ("Near-Threshold / Difficult Negative", fp_sample, axes[1, 0]),
        ("Near-Threshold / Difficult Positive", fn_sample, axes[1, 1]),
    ]
    
    for title, item, ax_sub in plot_items:
        if item is not None:
            feat_path = WORKSPACE_ROOT / "data/processed/audio/train_horn/features" / ("positive" if item["class_id"] == 1 else "negative") / f"{item['window_id']}.npy"
            if feat_path.exists():
                feat = np.load(feat_path)
                im = ax_sub.imshow(feat, origin="lower", aspect="auto", cmap="magma")
                ax_sub.set_title(f"{title}\n{item['source_file']} (P={item['probability']:.3f})", fontsize=10)
                ax_sub.set_xlabel("Time Frames (~1.0s)")
                ax_sub.set_ylabel("Mel Frequency Bin")
                fig.colorbar(im, ax=ax_sub, fraction=0.046, pad=0.04)
            else:
                ax_sub.text(0.5, 0.5, "Spectrogram not found", ha="center")
        else:
            ax_sub.text(0.5, 0.5, "No sample available", ha="center")
            
    plt.suptitle("Log-Mel Spectrogram Diagnostics (64 Mel Bins, 80–8000 Hz)", fontsize=13, weight="bold")
    plt.tight_layout()
    fig.savefig(fig_dir / "fig10_spectrogram_examples.png")
    plt.close(fig)
    
    print(f"Generated all 10 publication figures in {fig_dir}")


def verify_audio_pretraining_gates(manifest_path: Path, workspace_root: Path) -> None:
    """Fail closed before this entry point initializes any training state."""
    trainer = AudioTrainer(
        config=AudioTrainingConfig(manifest_path=manifest_path),
        workspace_root=workspace_root,
    )
    trainer.verify_pretraining_gates()


def run_training_experiment() -> dict[str, Any]:
    manifest_path = WORKSPACE_ROOT / "data/manifests/audio_training_dataset.json"
    verify_audio_pretraining_gates(manifest_path, WORKSPACE_ROOT)

    run_id = f"RUN_{datetime.now(UTC).strftime('%Y%m%d')}_AUDIO_001"
    run_dir = WORKSPACE_ROOT / f"experiments/audio/{run_id}"
    
    for sub in ("checkpoints", "config", "metrics", "figures", "predictions", "manifests", "logs", "report"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
        
    # Set up logging
    log_file = run_dir / "logs/training.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("audio.experiment")
    logger.info("Initializing Audio Classifier Experiment %s", run_id)
    
    set_seed(42)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    logger.info("Using compute device: %s", device)
    
    train_loader = AudioDatasetLoader(manifest_path, partition="train", workspace_root=WORKSPACE_ROOT)
    val_loader = AudioDatasetLoader(manifest_path, partition="val", workspace_root=WORKSPACE_ROOT)
    test_loader = AudioDatasetLoader(manifest_path, partition="test", workspace_root=WORKSPACE_ROOT)
    
    logger.info("Dataset Partitions Loaded:")
    logger.info("  Train: %d windows (Pos: %d, Neg: %d)", len(train_loader), train_loader.positive_count, train_loader.negative_count)
    logger.info("  Val:   %d windows (Pos: %d, Neg: %d)", len(val_loader), val_loader.positive_count, val_loader.negative_count)
    logger.info("  Test:  %d windows (Pos: %d, Neg: %d)", len(test_loader), test_loader.positive_count, test_loader.negative_count)
    
    # Calculate feature normalization statistics over training partition
    train_feats = [train_loader.load_feature(r) for r in train_loader.records]
    all_train_vals = np.concatenate([f.flatten() for f in train_feats])
    feat_mean = float(np.mean(all_train_vals))
    feat_std = float(np.std(all_train_vals))
    logger.info("Training Feature Normalization: mean=%.4f dB, std=%.4f dB", feat_mean, feat_std)
    
    # Instantiate Compact CNN
    model = CompactTrainHornCNN().to(device)
    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info("CompactTrainHornCNN Architecture initialized with %d trainable parameters", param_count)
    
    # Loss function with positive weight adjustment to balance training windows
    pos_weight = torch.tensor([train_loader.negative_count / max(1, train_loader.positive_count)], device=device)
    logger.info("Loss pos_weight: %.3f (train neg/pos window ratio)", float(pos_weight.item()))
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    
    optimizer = AdamW(model.parameters(), lr=1e-3, weight_decay=1e-3)
    epochs = 40
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
    
    history: dict[str, list[float]] = {
        "train_loss": [],
        "train_acc": [],
        "val_loss": [],
        "val_acc": [],
        "val_f1": [],
        "val_auc": [],
    }
    
    best_val_f1 = -1.0
    best_epoch = -1
    best_checkpoint_path = run_dir / "checkpoints/best_checkpoint.pt"
    
    rng = np.random.default_rng(42)
    start_time = time.time()
    
    for epoch in range(1, epochs + 1):
        tr_loss, tr_acc = train_epoch(
            model, train_loader, optimizer, criterion, feat_mean, feat_std, device, rng, batch_size=32
        )
        val_loss, val_y, val_scores, _ = evaluate_split(
            model, val_loader, criterion, feat_mean, feat_std, device, threshold=0.5
        )
        scheduler.step()
        
        val_metrics_raw = compute_binary_metrics(val_y, val_scores, threshold=0.5)
        history["train_loss"].append(tr_loss)
        history["train_acc"].append(tr_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_metrics_raw.accuracy)
        history["val_f1"].append(val_metrics_raw.f1_score)
        history["val_auc"].append(val_metrics_raw.auc_roc)
        
        logger.info(
            "Epoch %02d/%02d: Tr Loss=%.4f, Tr Acc=%.2f%% | Val Loss=%.4f, Val Acc=%.2f%%, Val F1=%.4f, Val AUC=%.4f",
            epoch, epochs, tr_loss, tr_acc * 100, val_loss, val_metrics_raw.accuracy * 100, val_metrics_raw.f1_score, val_metrics_raw.auc_roc
        )
        
        # Checkpointing based on validation F1
        if val_metrics_raw.f1_score > best_val_f1:
            best_val_f1 = val_metrics_raw.f1_score
            best_epoch = epoch
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "feature_mean": feat_mean,
                "feature_std": feat_std,
                "val_loss": val_loss,
                "val_f1": best_val_f1,
                "val_auc": val_metrics_raw.auc_roc,
                "parameters_count": param_count,
            }, best_checkpoint_path)
            
    training_duration = time.time() - start_time
    logger.info("Training completed in %.2f seconds. Best Epoch: %d (Val F1: %.4f)", training_duration, best_epoch, best_val_f1)
    
    # Save final checkpoint
    final_checkpoint_path = run_dir / "checkpoints/final_checkpoint.pt"
    torch.save({
        "epoch": epochs,
        "model_state_dict": model.state_dict(),
        "feature_mean": feat_mean,
        "feature_std": feat_std,
    }, final_checkpoint_path)
    
    # Load Best Model for Calibration and Evaluation
    best_state = torch.load(best_checkpoint_path, map_location=device)
    model.load_state_dict(best_state["model_state_dict"])
    model.eval()
    
    # -------------------------------------------------------------
    # Threshold Calibration on Validation Partition
    # -------------------------------------------------------------
    _, val_y, val_scores, _ = evaluate_split(model, val_loader, criterion, feat_mean, feat_std, device)
    best_threshold, val_metrics = calibrate_operating_threshold(val_y, val_scores, target_metric="f1")
    logger.info("Validation Threshold Calibration: Optimal T* = %.4f (Val F1: %.4f, Val Acc: %.2f%%)", best_threshold, val_metrics.f1_score, val_metrics.accuracy * 100)
    
    # Update checkpoint with calibrated operating threshold
    best_state["operating_threshold"] = best_threshold
    torch.save(best_state, best_checkpoint_path)
    
    # Also save checkpoint to standard project model path
    standard_model_dir = WORKSPACE_ROOT / "models/audio"
    standard_model_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_checkpoint_path, standard_model_dir / "best_checkpoint.pt")
    
    # -------------------------------------------------------------
    # Evaluation on Held-Out Test Set at Frozen Threshold T*
    # -------------------------------------------------------------
    test_loss, test_y, test_scores, test_predictions_meta = evaluate_split(
        model, test_loader, criterion, feat_mean, feat_std, device, threshold=best_threshold
    )
    test_metrics = compute_binary_metrics(test_y, test_scores, threshold=best_threshold)
    
    logger.info("==================================================")
    logger.info("HELD-OUT TEST SET EVALUATION RESULTS (T* = %.4f)", best_threshold)
    logger.info("==================================================")
    logger.info("  Accuracy:           %.4f (%.2f%%)", test_metrics.accuracy, test_metrics.accuracy * 100)
    logger.info("  Precision:          %.4f", test_metrics.precision)
    logger.info("  Recall:             %.4f", test_metrics.recall)
    logger.info("  F1-Score:           %.4f", test_metrics.f1_score)
    logger.info("  Specificity:        %.4f", test_metrics.specificity)
    logger.info("  Balanced Accuracy:  %.4f", test_metrics.balanced_accuracy)
    logger.info("  ROC-AUC:            %.4f", test_metrics.auc_roc)
    logger.info("  PR-AUC:             %.4f", test_metrics.pr_auc)
    logger.info("  Confusion Matrix:   TP=%d, TN=%d, FP=%d, FN=%d", test_metrics.tp, test_metrics.tn, test_metrics.fp, test_metrics.fn)
    logger.info("==================================================")
    
    # Also evaluate Recording-Level Test Metrics (aggregating windows per source recording)
    rec_to_scores = defaultdict(list)
    rec_to_label = {}
    rec_to_cat = {}
    for p in test_predictions_meta:
        src = p["source_file"]
        rec_to_scores[src].append(p["probability"])
        rec_to_label[src] = p["class_id"]
        rec_to_cat[src] = p["category"]
        
    rec_y_true = []
    rec_y_score = []
    for src, scores in rec_to_scores.items():
        rec_y_true.append(rec_to_label[src])
        rec_y_score.append(max(scores))  # Event triggered if max window exceeds threshold
        
    rec_metrics = compute_binary_metrics(np.array(rec_y_true), np.array(rec_y_score), threshold=best_threshold)
    logger.info("RECORDING-LEVEL TEST METRICS (N=%d recordings):", len(rec_y_true))
    logger.info("  Accuracy: %.4f, Precision: %.4f, Recall: %.4f, F1: %.4f", rec_metrics.accuracy, rec_metrics.precision, rec_metrics.recall, rec_metrics.f1_score)
    logger.info("  Recording Confusion Matrix: TP=%d, TN=%d, FP=%d, FN=%d", rec_metrics.tp, rec_metrics.tn, rec_metrics.fp, rec_metrics.fn)
    
    # -------------------------------------------------------------
    # Evaluate Baseline Classifier for Comparative Rigor
    # -------------------------------------------------------------
    baseline = SpectralEnergyBaseline()
    baseline_scores = []
    for rec in test_loader.records:
        # Load standardized wav window
        wav_path = WORKSPACE_ROOT / rec.standardized_wav_path
        import wave
        require_media_authorization(wav_path, "FEATURE_EXTRACTION")
        with wave.open(str(wav_path), "rb") as wfp:
            w_samples = np.frombuffer(wfp.readframes(wfp.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
        conf, _ = baseline.predict_window(w_samples, sample_rate=16000)
        baseline_scores.append(conf)
    baseline_metrics = compute_binary_metrics(test_y, np.array(baseline_scores), threshold=0.35)
    logger.info("SPECTRAL ENERGY BASELINE COMPARISON ON TEST SET:")
    logger.info("  Accuracy: %.4f, Precision: %.4f, Recall: %.4f, F1: %.4f, AUC: %.4f", baseline_metrics.accuracy, baseline_metrics.precision, baseline_metrics.recall, baseline_metrics.f1_score, baseline_metrics.auc_roc)
    
    # -------------------------------------------------------------
    # Generate Research Figures
    # -------------------------------------------------------------
    generate_research_figures(
        run_dir=run_dir,
        history=history,
        val_metrics=val_metrics,
        test_metrics=test_metrics,
        val_labels=val_y,
        val_scores=val_scores,
        test_labels=test_y,
        test_scores=test_scores,
        test_preds=test_predictions_meta,
        best_threshold=best_threshold,
    )
    
    # Copy figures to results/figures for paper documentation
    paper_fig_dir = WORKSPACE_ROOT / "results/figures"
    paper_fig_dir.mkdir(parents=True, exist_ok=True)
    for fig_path in (run_dir / "figures").glob("*.png"):
        shutil.copy2(fig_path, paper_fig_dir / fig_path.name)
        
    # -------------------------------------------------------------
    # Machine-Readable Artifacts & Metadata Export
    # -------------------------------------------------------------
    # 1. metrics.json
    metrics_summary = {
        "experiment_id": run_id,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "model_architecture": "CompactTrainHornCNN",
        "parameters_count": param_count,
        "operating_threshold": round(best_threshold, 4),
        "training_duration_s": round(training_duration, 2),
        "best_epoch": best_epoch,
        "total_epochs": epochs,
        "window_level_test_metrics": test_metrics.to_dict(),
        "recording_level_test_metrics": rec_metrics.to_dict(),
        "spectral_energy_baseline_test_metrics": baseline_metrics.to_dict(),
        "validation_metrics": val_metrics.to_dict(),
        "feature_normalization": {
            "mean": feat_mean,
            "std": feat_std,
        },
    }
    with open(run_dir / "metrics/metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)
        
    # 2. training_history.json
    with open(run_dir / "metrics/training_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
        
    # 3. experiment_config.json
    config_data = {
        "experiment_id": run_id,
        "random_seed": 42,
        "model": {
            "name": "CompactTrainHornCNN",
            "in_channels": 1,
            "dropout": 0.3,
            "parameter_count": param_count,
        },
        "preprocessing": {
            "sample_rate": 16000,
            "window_duration_s": 1.0,
            "hop_duration_s": 0.5,
            "normalization": "peak_to_minus_1_dbfs",
        },
        "features": {
            "type": "log_mel_spectrogram",
            "n_mels": 64,
            "n_fft": 512,
            "hop_length": 256,
            "f_min": 80.0,
            "f_max": 8000.0,
            "shape": [64, 61],
        },
        "optimization": {
            "optimizer": "AdamW",
            "learning_rate": 0.001,
            "weight_decay": 0.001,
            "scheduler": "CosineAnnealingLR",
            "epochs": epochs,
            "batch_size": 32,
            "loss": "BCEWithLogitsLoss",
            "pos_weight": float(pos_weight.item()),
        },
        "safety_constraints": {
            "audio_safety_role": "supporting_only",
            "max_independent_authorization": False,
            "layer_b_eval_events_isolated": True,
        }
    }
    with open(run_dir / "config/experiment_config.json", "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)
        
    # 4. Copy split and selection manifests into experiment directory
    shutil.copy2(WORKSPACE_ROOT / "data/splits/audio/dataset_split.json", run_dir / "manifests/dataset_split.json")
    shutil.copy2(WORKSPACE_ROOT / "data/manifests/negative_selection_manifest.json", run_dir / "manifests/negative_selection_manifest.json")
    
    # 5. predictions.jsonl and test_predictions.csv
    import csv
    with open(run_dir / "predictions/predictions.jsonl", "w", encoding="utf-8") as f:
        for p in test_predictions_meta:
            f.write(json.dumps(p) + "\n")
            
    with open(run_dir / "predictions/test_predictions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["window_id", "source_file", "class_id", "category", "probability", "prediction", "correct", "start_time_s", "end_time_s"])
        writer.writeheader()
        for p in test_predictions_meta:
            writer.writerow({
                "window_id": p["window_id"],
                "source_file": p["source_file"],
                "class_id": p["class_id"],
                "category": p["category"],
                "probability": round(p["probability"], 4),
                "prediction": p["prediction"],
                "correct": p["correct"],
                "start_time_s": p["start_time_s"],
                "end_time_s": p["end_time_s"],
            })
            
    # 6. Detailed Error Analysis
    fps = [p for p in test_predictions_meta if p["class_id"] == 0 and p["prediction"] == 1]
    fns = [p for p in test_predictions_meta if p["class_id"] == 1 and p["prediction"] == 0]
    low_conf_tp = [p for p in test_predictions_meta if p["class_id"] == 1 and p["prediction"] == 1 and p["probability"] < 0.7]
    high_conf_tn = [p for p in test_predictions_meta if p["class_id"] == 0 and p["prediction"] == 0 and p["probability"] > 0.3]
    
    cat_stats = defaultdict(lambda: {"total": 0, "correct": 0, "errors": 0})
    for p in test_predictions_meta:
        c = p["category"]
        cat_stats[c]["total"] += 1
        if p["correct"]:
            cat_stats[c]["correct"] += 1
        else:
            cat_stats[c]["errors"] += 1
            
    error_summary = {
        "total_test_windows": len(test_predictions_meta),
        "false_positives_count": len(fps),
        "false_negatives_count": len(fns),
        "false_positives": fps,
        "false_negatives": fns,
        "low_confidence_true_positives": low_conf_tp,
        "category_performance": {k: {"total": v["total"], "accuracy": v["correct"] / v["total"], "errors": v["errors"]} for k, v in cat_stats.items()},
    }
    with open(run_dir / "report/error_analysis.json", "w", encoding="utf-8") as f:
        json.dump(error_summary, f, indent=2)
        
    logger.info("Saved all experiment artifacts to %s", run_dir)
    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "test_metrics": test_metrics,
        "rec_metrics": rec_metrics,
        "baseline_metrics": baseline_metrics,
        "best_threshold": best_threshold,
        "training_duration": training_duration,
        "fps_count": len(fps),
        "fns_count": len(fns),
    }


if __name__ == "__main__":
    run_training_experiment()
