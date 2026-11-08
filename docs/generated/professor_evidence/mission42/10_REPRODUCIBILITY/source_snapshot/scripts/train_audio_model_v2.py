#!/usr/bin/env python3
"""
Phase 2: Train, Calibrate, Evaluate, and Compare Audio Model V2.
Strict adherence to:
- Standalone audio dataset only (zero Layer B evaluation video/audio leakage).
- Recording-level split (zero duplicate/recording leakage).
- Threshold calibrated on Validation set, evaluated on held-out Test set.
- Formal V1 vs V2 statistical and operational comparison.
- Full research figures and machine-readable manifests.
"""
from __future__ import annotations

import csv
import json
import logging
import math
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
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

WORKSPACE = Path("/Users/sayemuddin/Desktop/Train_automation")
RUN_ID = "RUN_20261008_AUDIO_V2"
RUN_DIR = WORKSPACE / "experiments/audio" / RUN_ID
V1_RUN_DIR = WORKSPACE / "experiments/audio/RUN_20260923_AUDIO_001"
MANIFEST_PATH = WORKSPACE / "data/manifests/audio_training_dataset_v2.json"


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# --- Architecture: CompactTrainHornCNN ---
class CompactTrainHornCNN(nn.Module):
    def __init__(self, in_channels: int = 1, dropout: float = 0.3) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, 16, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(16)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(32)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(64)
        self.pool3 = nn.AdaptiveAvgPool2d((1, 1))

        self.fc1 = nn.Linear(64, 32)
        self.bn_fc = nn.BatchNorm1d(32)
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(32, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 3:
            x = x.unsqueeze(1)
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))
        x = x.flatten(start_dim=1)
        x = self.dropout(F.relu(self.bn_fc(self.fc1(x))))
        return self.fc2(x).squeeze(-1)


# --- Audio Dataset Loader ---
class AudioWindowDataset:
    def __init__(self, manifest_path: Path, partition: str, workspace_root: Path):
        with open(manifest_path) as f:
            all_records = json.load(f)
        self.records = [r for r in all_records if r["partition"] == partition]
        self.workspace_root = workspace_root
        self.positive_count = sum(1 for r in self.records if r["class_id"] == 1)
        self.negative_count = sum(1 for r in self.records if r["class_id"] == 0)

    def __len__(self) -> int:
        return len(self.records)

    def get_features_and_labels(self) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
        feats = []
        labels = []
        for r in self.records:
            fp = self.workspace_root / r["feature_path"]
            feats.append(np.load(fp))
            labels.append(r["class_id"])
        return np.stack(feats, axis=0), np.array(labels, dtype=np.int64), self.records


# --- Augmentation (Train only) ---
def apply_augmentation(feat: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    aug = feat.copy()
    # 1. Gain variation (+/- 2.5 dB)
    gain_db = rng.uniform(-2.5, 2.5)
    aug = aug + gain_db
    # 2. Temporal roll (+/- 3 frames)
    shift = rng.integers(-3, 4)
    if shift != 0:
        aug = np.roll(aug, shift, axis=1)
    # 3. Additive Gaussian noise (std 0.01 - 0.05)
    noise_std = rng.uniform(0.01, 0.05)
    aug = aug + rng.normal(0.0, noise_std, size=aug.shape)
    return aug


# --- Evaluation Metrics ---
def compute_metrics(labels: np.ndarray, scores: np.ndarray, threshold: float = 0.5) -> dict[str, Any]:
    preds = (scores >= threshold).astype(int)
    tp = int(np.sum((preds == 1) & (labels == 1)))
    fp = int(np.sum((preds == 1) & (labels == 0)))
    fn = int(np.sum((preds == 0) & (labels == 1)))
    tn = int(np.sum((preds == 0) & (labels == 0)))

    acc = (tp + tn) / max(len(labels), 1)
    prec = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    spec = tn / max(tn + fp, 1)
    f1 = 2 * prec * rec / max(prec + rec, 1e-6)
    bal_acc = 0.5 * (rec + spec)

    # ROC AUC
    # Rank-based calculation
    pos_mask = (labels == 1)
    n_pos = np.sum(pos_mask)
    n_neg = len(labels) - n_pos
    if n_pos > 0 and n_neg > 0:
        ranks = np.argsort(np.argsort(scores)) + 1
        pos_ranks = ranks[pos_mask]
        auc_roc = float((np.sum(pos_ranks) - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))
    else:
        auc_roc = 0.5

    # PR AUC (trapezoidal rule across sorted thresholds)
    order = np.argsort(-scores)
    sorted_labels = labels[order]
    tp_cum = np.cumsum(sorted_labels == 1)
    fp_cum = np.cumsum(sorted_labels == 0)
    recalls = tp_cum / max(n_pos, 1)
    precisions = tp_cum / np.maximum(tp_cum + fp_cum, 1)
    recalls = np.concatenate(([0.0], recalls, [1.0]))
    precisions = np.concatenate(([1.0], precisions, [0.0]))
    pr_auc = float(np.sum((recalls[1:] - recalls[:-1]) * precisions[1:]))

    # Brier score
    brier = float(np.mean((scores - labels) ** 2))

    return {
        "threshold": round(threshold, 4),
        "total_samples": len(labels),
        "positive_samples": int(n_pos),
        "negative_samples": int(n_neg),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "specificity": round(spec, 4),
        "f1_score": round(f1, 4),
        "balanced_accuracy": round(bal_acc, 4),
        "auc_roc": round(auc_roc, 4),
        "pr_auc": round(pr_auc, 4),
        "brier_score": round(brier, 4),
    }


def main():
    print(f"=== Audio Model V2 Training & Evaluation: {RUN_ID} ===")
    set_seed(42)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Compute device: {device}")

    # Set up experiment directory structure
    for sub in ("checkpoints", "config", "metrics", "figures", "predictions", "manifests", "logs", "report"):
        (RUN_DIR / sub).mkdir(parents=True, exist_ok=True)

    # Logging
    log_file = RUN_DIR / "logs/training.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("audio_v2")
    logger.info("Starting Audio V2 training run %s", RUN_ID)

    # Load datasets
    train_ds = AudioWindowDataset(MANIFEST_PATH, "train", WORKSPACE)
    val_ds = AudioWindowDataset(MANIFEST_PATH, "val", WORKSPACE)
    test_ds = AudioWindowDataset(MANIFEST_PATH, "test", WORKSPACE)

    X_train_raw, y_train, train_meta = train_ds.get_features_and_labels()
    X_val_raw, y_val, val_meta = val_ds.get_features_and_labels()
    X_test_raw, y_test, test_meta = test_ds.get_features_and_labels()

    logger.info("Loaded datasets:")
    logger.info("  Train: %d windows (%d pos, %d neg)", len(y_train), train_ds.positive_count, train_ds.negative_count)
    logger.info("  Val:   %d windows (%d pos, %d neg)", len(y_val), val_ds.positive_count, val_ds.negative_count)
    logger.info("  Test:  %d windows (%d pos, %d neg)", len(y_test), test_ds.positive_count, test_ds.negative_count)

    # Compute normalization mean/std strictly from Train windows
    norm_mean = float(np.mean(X_train_raw))
    norm_std = float(np.std(X_train_raw))
    logger.info("Train Normalization: Mean=%.4f, Std=%.4f", norm_mean, norm_std)

    # Normalize validation and test (fixed stats)
    X_val = (X_val_raw - norm_mean) / norm_std
    X_test = (X_test_raw - norm_mean) / norm_std

    # Model and loss
    model = CompactTrainHornCNN(in_channels=1, dropout=0.3).to(device)
    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info("CompactTrainHornCNN parameter count: %d", param_count)

    pos_weight = torch.tensor([train_ds.negative_count / max(train_ds.positive_count, 1)], device=device, dtype=torch.float32)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = AdamW(model.parameters(), lr=0.001, weight_decay=0.001)
    epochs = 40
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs)

    rng = np.random.default_rng(42)
    history = []
    best_val_loss = float("inf")
    best_val_f1 = 0.0
    best_epoch = -1
    best_model_state = None

    start_time = time.time()
    batch_size = 32

    logger.info("Training for %d epochs...", epochs)
    for epoch in range(1, epochs + 1):
        model.train()
        # Shuffle train data each epoch
        perm = np.random.permutation(len(y_train))
        X_train_shuf = X_train_raw[perm]
        y_train_shuf = y_train[perm]

        train_loss = 0.0
        train_batches = math.ceil(len(y_train) / batch_size)

        for b in range(train_batches):
            b_start = b * batch_size
            b_end = min(b_start + batch_size, len(y_train))
            batch_x = X_train_shuf[b_start:b_end].copy()
            batch_y = y_train_shuf[b_start:b_end]

            # Augmentation
            for i in range(len(batch_x)):
                batch_x[i] = apply_augmentation(batch_x[i], rng)

            # Normalization
            batch_x = (batch_x - norm_mean) / norm_std

            t_x = torch.tensor(batch_x, dtype=torch.float32, device=device).unsqueeze(1)
            t_y = torch.tensor(batch_y, dtype=torch.float32, device=device)

            optimizer.zero_grad()
            logits = model(t_x)
            loss = criterion(logits, t_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * len(batch_y)

        train_loss /= len(y_train)
        scheduler.step()

        # Validation evaluation
        model.eval()
        with torch.no_grad():
            v_x = torch.tensor(X_val, dtype=torch.float32, device=device).unsqueeze(1)
            v_y = torch.tensor(y_val, dtype=torch.float32, device=device)
            v_logits = model(v_x)
            v_loss = criterion(v_logits, v_y).item()
            v_scores = torch.sigmoid(v_logits).cpu().numpy()

        val_m = compute_metrics(y_val, v_scores, threshold=0.5)

        history.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "val_loss": round(v_loss, 4),
            "val_accuracy": val_m["accuracy"],
            "val_precision": val_m["precision"],
            "val_recall": val_m["recall"],
            "val_f1": val_m["f1_score"],
            "val_auc_roc": val_m["auc_roc"],
        })

        if epoch % 5 == 0 or epoch == epochs:
            logger.info("Epoch %2d/%d | Train Loss: %.4f | Val Loss: %.4f | Val F1: %.4f | Val ROC: %.4f",
                        epoch, epochs, train_loss, v_loss, val_m["f1_score"], val_m["auc_roc"])

        # Checkpoint selection (primary: validation loss with high F1)
        if v_loss < best_val_loss and val_m["f1_score"] >= 0.70:
            best_val_loss = v_loss
            best_val_f1 = val_m["f1_score"]
            best_epoch = epoch
            best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        elif best_model_state is None and epoch == epochs:
            best_val_loss = v_loss
            best_val_f1 = val_m["f1_score"]
            best_epoch = epoch
            best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    train_duration = time.time() - start_time
    logger.info("Training complete in %.2f seconds. Best Epoch: %d (Val Loss: %.4f, Val F1: %.4f)",
                train_duration, best_epoch, best_val_loss, best_val_f1)

    # Save checkpoints
    model.load_state_dict(best_model_state)
    best_ckpt_path = RUN_DIR / "checkpoints/best.pt"
    final_ckpt_path = RUN_DIR / "checkpoints/final_checkpoint.pt"

    torch.save({
        "epoch": best_epoch,
        "model_state_dict": best_model_state,
        "optimizer_state_dict": optimizer.state_dict(),
        "norm_mean": norm_mean,
        "norm_std": norm_std,
        "val_loss": best_val_loss,
        "val_f1": best_val_f1,
    }, best_ckpt_path)
    torch.save(model.state_dict(), final_ckpt_path)
    logger.info("Saved best checkpoint to %s", best_ckpt_path)

    # --- Threshold Calibration on Validation Set ---
    logger.info("Calibrating decision threshold on Validation Set...")
    model.eval()
    with torch.no_grad():
        v_x = torch.tensor(X_val, dtype=torch.float32, device=device).unsqueeze(1)
        val_probs = torch.sigmoid(model(v_x)).cpu().numpy()

    thresh_candidates = np.linspace(0.10, 0.90, 81)
    best_t = 0.50
    best_t_f1 = -1.0
    for t in thresh_candidates:
        m = compute_metrics(y_val, val_probs, threshold=float(t))
        if m["f1_score"] > best_t_f1:
            best_t_f1 = m["f1_score"]
            best_t = float(t)

    logger.info("Calibrated Optimal Threshold T* = %.4f (Validation F1 = %.4f)", best_t, best_t_f1)

    # --- Held-Out Test Evaluation at Calibrated Threshold T* ---
    logger.info("Evaluating on Held-Out Test Set at Threshold T* = %.4f...", best_t)
    with torch.no_grad():
        t_x = torch.tensor(X_test, dtype=torch.float32, device=device).unsqueeze(1)
        test_probs = torch.sigmoid(model(t_x)).cpu().numpy()

    test_window_metrics = compute_metrics(y_test, test_probs, threshold=best_t)
    logger.info("Held-Out Test Window Metrics:")
    for k, v in test_window_metrics.items():
        logger.info("  %s: %s", k, v)

    # Recording-Level Evaluation
    rec_preds = defaultdict(list)
    rec_labels = {}
    for i, meta in enumerate(test_meta):
        rec_id = f"{meta['class_name']}/{meta['source_file']}"
        rec_preds[rec_id].append(float(test_probs[i]))
        rec_labels[rec_id] = meta["class_id"]

    rec_names = sorted(list(rec_preds.keys()))
    rec_scores = np.array([np.max(rec_preds[r]) for r in rec_names])
    rec_y = np.array([rec_labels[r] for r in rec_names])
    test_rec_metrics = compute_metrics(rec_y, rec_scores, threshold=best_t)
    logger.info("Held-Out Test Recording Metrics (Max-window pooling, T*=%.4f):", best_t)
    for k, v in test_rec_metrics.items():
        logger.info("  %s: %s", k, v)

    # Save predictions
    predictions_records = []
    for i, meta in enumerate(test_meta):
        prob = float(test_probs[i])
        pred = int(prob >= best_t)
        predictions_records.append({
            "window_id": meta["window_id"],
            "source_file": meta["source_file"],
            "class_name": meta["class_name"],
            "class_id": meta["class_id"],
            "category": meta["category"],
            "probability": round(prob, 4),
            "prediction": pred,
            "correct": pred == meta["class_id"],
            "start_time_s": meta["start_time_s"],
            "end_time_s": meta["end_time_s"],
        })

    with open(RUN_DIR / "predictions/predictions.jsonl", "w") as f:
        for p in predictions_records:
            f.write(json.dumps(p) + "\n")

    with open(RUN_DIR / "predictions/test_predictions.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(predictions_records[0].keys()))
        writer.writeheader()
        writer.writerows(predictions_records)

    # Error analysis
    fps = [p for p in predictions_records if p["class_id"] == 0 and p["prediction"] == 1]
    fns = [p for p in predictions_records if p["class_id"] == 1 and p["prediction"] == 0]
    error_summary = {
        "operating_threshold": best_t,
        "total_test_windows": len(predictions_records),
        "false_positive_count": len(fps),
        "false_negative_count": len(fns),
        "false_positives": fps,
        "false_negatives": fns,
    }
    with open(RUN_DIR / "report/error_analysis.json", "w") as f:
        json.dump(error_summary, f, indent=2)

    # Load V1 metrics for direct comparison
    v1_metrics_file = V1_RUN_DIR / "metrics/metrics.json"
    with open(v1_metrics_file) as f:
        v1_data = json.load(f)

    v1_win = v1_data["window_level_test_metrics"]["rates"]
    v1_rec = v1_data["recording_level_test_metrics"]["rates"]
    v1_thresh = v1_data["operating_threshold"]

    comparison = {
        "metric": [
            "Dataset Composition",
            "Model Architecture",
            "Operating Threshold",
            "Window Test Accuracy",
            "Window Test Precision",
            "Window Test Recall",
            "Window Test Specificity",
            "Window Test F1-Score",
            "Window Test AUC-ROC",
            "Window Test PR-AUC",
            "Recording Test Accuracy",
            "Recording Test Precision",
            "Recording Test Recall",
            "Recording Test Specificity",
            "Recording Test F1-Score",
            "Recording Test AUC-ROC",
        ],
        "V1 (ESC-50 Negative Baseline)": [
            "87 positive + 87 ESC-50 negative",
            "CompactTrainHornCNN (25,697 params)",
            f"{v1_thresh:.4f}",
            f"{v1_win['accuracy']:.4f}",
            f"{v1_win['precision']:.4f}",
            f"{v1_win['recall']:.4f}",
            f"{v1_win['specificity']:.4f}",
            f"{v1_win['f1_score']:.4f}",
            f"{v1_win['auc_roc']:.4f}",
            f"{v1_win['pr_auc']:.4f}",
            f"{v1_rec['accuracy']:.4f}",
            f"{v1_rec['precision']:.4f}",
            f"{v1_rec['recall']:.4f}",
            f"{v1_rec['specificity']:.4f}",
            f"{v1_rec['f1_score']:.4f}",
            f"{v1_rec['auc_roc']:.4f}",
        ],
        "V2 (Empirical Field Negative)": [
            "86 unique positive + 86 field negative",
            "CompactTrainHornCNN (25,697 params)",
            f"{best_t:.4f}",
            f"{test_window_metrics['accuracy']:.4f}",
            f"{test_window_metrics['precision']:.4f}",
            f"{test_window_metrics['recall']:.4f}",
            f"{test_window_metrics['specificity']:.4f}",
            f"{test_window_metrics['f1_score']:.4f}",
            f"{test_window_metrics['auc_roc']:.4f}",
            f"{test_window_metrics['pr_auc']:.4f}",
            f"{test_rec_metrics['accuracy']:.4f}",
            f"{test_rec_metrics['precision']:.4f}",
            f"{test_rec_metrics['recall']:.4f}",
            f"{test_rec_metrics['specificity']:.4f}",
            f"{test_rec_metrics['f1_score']:.4f}",
            f"{test_rec_metrics['auc_roc']:.4f}",
        ]
    }
    with open(RUN_DIR / "metrics/v1_vs_v2_comparison.json", "w") as f:
        json.dump(comparison, f, indent=2)

    # Save metrics.json
    full_metrics = {
        "experiment_id": RUN_ID,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "model_architecture": "CompactTrainHornCNN",
        "parameters_count": param_count,
        "operating_threshold": best_t,
        "training_duration_s": round(train_duration, 2),
        "best_epoch": best_epoch,
        "total_epochs": epochs,
        "window_level_test_metrics": test_window_metrics,
        "recording_level_test_metrics": test_rec_metrics,
        "validation_metrics": compute_metrics(y_val, val_probs, threshold=best_t),
        "feature_normalization": {
            "mean": norm_mean,
            "std": norm_std,
        }
    }
    with open(RUN_DIR / "metrics/metrics.json", "w") as f:
        json.dump(full_metrics, f, indent=2)
    with open(RUN_DIR / "metrics/training_history.json", "w") as f:
        json.dump(history, f, indent=2)

    # Save config
    config_dict = {
        "experiment_id": RUN_ID,
        "random_seed": 42,
        "model": {"name": "CompactTrainHornCNN", "in_channels": 1, "dropout": 0.3, "parameter_count": param_count},
        "preprocessing": {"sample_rate": 16000, "window_duration_s": 1.0, "hop_duration_s": 0.5},
        "features": {"type": "log_mel_spectrogram", "n_mels": 64, "n_fft": 512, "hop_length": 256, "f_min": 80.0, "f_max": 8000.0, "shape": [64, 61]},
        "optimization": {"optimizer": "AdamW", "learning_rate": 0.001, "weight_decay": 0.001, "scheduler": "CosineAnnealingLR", "epochs": epochs, "batch_size": batch_size, "pos_weight": float(pos_weight.item())},
        "operating_threshold": best_t
    }
    with open(RUN_DIR / "config/experiment_config.json", "w") as f:
        json.dump(config_dict, f, indent=2)

    # Copy manifests
    shutil.copy2(WORKSPACE / "data/splits/audio/v2/dataset_split.json", RUN_DIR / "manifests/dataset_split.json")
    shutil.copy2(WORKSPACE / "data/manifests/audio_training_v2_selection.json", RUN_DIR / "manifests/audio_training_v2_selection.json")

    # -------------------------------------------------------------
    # GENERATE RESEARCH FIGURES (11 publication-grade figures)
    # -------------------------------------------------------------
    fig_dir = RUN_DIR / "figures"
    logger.info("Generating publication research figures in %s...", fig_dir)

    # Fig 1: Loss curves
    ep_list = [h["epoch"] for h in history]
    t_loss = [h["train_loss"] for h in history]
    v_loss = [h["val_loss"] for h in history]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(ep_list, t_loss, label="Train Loss (Augmented)", color="#1f77b4", lw=2)
    ax.plot(ep_list, v_loss, label="Validation Loss", color="#ff7f0e", lw=2)
    ax.axvline(best_epoch, color="#d62728", linestyle="--", label=f"Best Checkpoint (Epoch {best_epoch})")
    ax.set_title("Audio Model V2 Training & Validation Loss Curves")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Binary Cross-Entropy Loss")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(frameon=True)
    plt.tight_layout()
    fig.savefig(fig_dir / "fig1_loss_curves.png", dpi=300)
    plt.close(fig)

    # Fig 2: Accuracy curves
    v_acc = [h["val_accuracy"] for h in history]
    v_f1 = [h["val_f1"] for h in history]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(ep_list, v_acc, label="Validation Accuracy", color="#2ca02c", lw=2)
    ax.plot(ep_list, v_f1, label="Validation F1-Score", color="#9467bd", lw=2)
    ax.axvline(best_epoch, color="#d62728", linestyle="--", label=f"Best Checkpoint (Epoch {best_epoch})")
    ax.set_title("Validation Accuracy and F1 Trajectory")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Score")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(frameon=True)
    plt.tight_layout()
    fig.savefig(fig_dir / "fig2_accuracy_curves.png", dpi=300)
    plt.close(fig)

    # Fig 3: Confusion matrix
    cm = np.array([
        [test_window_metrics["tn"], test_window_metrics["fp"]],
        [test_window_metrics["fn"], test_window_metrics["tp"]]
    ])
    fig, ax = plt.subplots(figsize=(6, 5))
    cax = ax.matshow(cm, cmap="Blues")
    fig.colorbar(cax)
    for (i, j), z in np.ndenumerate(cm):
        ax.text(j, i, f"{z:d}", ha="center", va="center", fontsize=14, weight="bold",
                color="white" if z > cm.max()/2 else "black")
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Non-Train (0)", "Train Horn (1)"])
    ax.set_yticklabels(["Non-Train (0)", "Train Horn (1)"])
    ax.set_xlabel(f"Predicted Class (Threshold = {best_t:.4f})")
    ax.set_ylabel("Ground Truth Class")
    ax.set_title(f"Test Set Window Confusion Matrix (N={len(y_test)})", pad=20)
    plt.tight_layout()
    fig.savefig(fig_dir / "fig3_confusion_matrix.png", dpi=300)
    plt.close(fig)

    # Fig 4: ROC curve
    order = np.argsort(-test_probs)
    sorted_labels = y_test[order]
    tp_c = np.cumsum(sorted_labels == 1)
    fp_c = np.cumsum(sorted_labels == 0)
    tpr = tp_c / max(np.sum(sorted_labels == 1), 1)
    fpr = fp_c / max(np.sum(sorted_labels == 0), 1)
    tpr = np.concatenate(([0.0], tpr, [1.0]))
    fpr = np.concatenate(([0.0], fpr, [1.0]))

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color="#1f77b4", lw=2.5, label=f"Audio V2 ROC (AUC = {test_window_metrics['auc_roc']:.4f})")
    ax.plot([0, 1], [0, 1], "k--", lw=1.5, alpha=0.7)
    ax.set_title("Receiver Operating Characteristic (ROC) Curve")
    ax.set_xlabel("False Positive Rate (1 - Specificity)")
    ax.set_ylabel("True Positive Rate (Recall / Sensitivity)")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="lower right", frameon=True)
    plt.tight_layout()
    fig.savefig(fig_dir / "fig4_roc_curve.png", dpi=300)
    plt.close(fig)

    # Fig 5: PR curve
    rec_c = tp_c / max(np.sum(sorted_labels == 1), 1)
    prec_c = tp_c / np.maximum(tp_c + fp_c, 1)
    rec_c = np.concatenate(([0.0], rec_c, [1.0]))
    prec_c = np.concatenate(([1.0], prec_c, [0.0]))

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(rec_c, prec_c, color="#2ca02c", lw=2.5, label=f"Audio V2 PR (AUC = {test_window_metrics['pr_auc']:.4f})")
    ax.set_title("Precision-Recall Curve (Train Horn Class)")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="lower left", frameon=True)
    plt.tight_layout()
    fig.savefig(fig_dir / "fig5_pr_curve.png", dpi=300)
    plt.close(fig)

    # Fig 6: Class metrics bar chart
    metrics_names = ["Accuracy", "Precision", "Recall", "Specificity", "F1-Score"]
    m_values = [test_window_metrics["accuracy"], test_window_metrics["precision"],
                test_window_metrics["recall"], test_window_metrics["specificity"],
                test_window_metrics["f1_score"]]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(metrics_names, [v * 100 for v in m_values], color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"])
    ax.set_ylim([0, 110])
    ax.set_ylabel("Score (%)")
    ax.set_title("Held-Out Test Set Window Classification Metrics")
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 2, f"{h:.1f}%", ha="center", va="bottom", weight="bold")
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    fig.savefig(fig_dir / "fig6_class_metrics.png", dpi=300)
    plt.close(fig)

    # Fig 7: Confidence distribution
    fig, ax = plt.subplots(figsize=(7, 4.5))
    pos_probs = test_probs[y_test == 1]
    neg_probs = test_probs[y_test == 0]
    bins = np.linspace(0.0, 1.0, 26)
    ax.hist(neg_probs, bins=bins, alpha=0.6, color="#2ca02c", label=f"True Negatives (N={len(neg_probs)})", density=True)
    ax.hist(pos_probs, bins=bins, alpha=0.6, color="#1f77b4", label=f"True Positives (N={len(pos_probs)})", density=True)
    ax.axvline(best_t, color="#d62728", linestyle="--", lw=2, label=f"Calibrated Threshold $T^* = {best_t:.4f}$")
    ax.set_title("Confidence Distribution on Held-Out Test Set")
    ax.set_xlabel("Predicted Train Horn Probability")
    ax.set_ylabel("Density")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(frameon=True)
    plt.tight_layout()
    fig.savefig(fig_dir / "fig7_confidence_distribution.png", dpi=300)
    plt.close(fig)

    # Fig 8: Threshold vs F1
    t_eval = np.linspace(0.01, 0.99, 100)
    f1s, precs, recs = [], [], []
    for t in t_eval:
        m = compute_metrics(y_val, val_probs, threshold=float(t))
        f1s.append(m["f1_score"])
        precs.append(m["precision"])
        recs.append(m["recall"])

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(t_eval, f1s, label="Validation F1-Score", color="#2ca02c", lw=2.5)
    ax.plot(t_eval, precs, label="Validation Precision", color="#1f77b4", lw=2.0, linestyle="--")
    ax.plot(t_eval, recs, label="Validation Recall", color="#ff7f0e", lw=2.0, linestyle=":")
    ax.axvline(best_t, color="#d62728", linestyle="-.", lw=2, label=f"Selected $T^* = {best_t:.4f}$ (Val F1={best_t_f1:.4f})")
    ax.set_title("Validation Decision Threshold Calibration Curves")
    ax.set_xlabel("Threshold")
    ax.set_ylabel("Metric Value")
    ax.set_ylim([0, 1.05])
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(frameon=True)
    plt.tight_layout()
    fig.savefig(fig_dir / "fig8_threshold_vs_f1.png", dpi=300)
    plt.close(fig)

    # Fig 9: Error analysis
    sorted_order = np.argsort(test_probs)
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    x_indices = np.arange(len(test_probs))
    ax.scatter(x_indices[y_test[sorted_order] == 0], test_probs[sorted_order][y_test[sorted_order] == 0],
               color="#2ca02c", alpha=0.7, s=35, label="Negative Ground Truth (Non-Horn)")
    ax.scatter(x_indices[y_test[sorted_order] == 1], test_probs[sorted_order][y_test[sorted_order] == 1],
               color="#1f77b4", alpha=0.7, s=35, label="Positive Ground Truth (Train Horn)")
    ax.axhline(best_t, color="#d62728", linestyle="--", lw=2, label=f"Threshold $T^* = {best_t:.4f}$")

    # Mark FP and FN
    fp_mask = (y_test[sorted_order] == 0) & (test_probs[sorted_order] >= best_t)
    fn_mask = (y_test[sorted_order] == 1) & (test_probs[sorted_order] < best_t)
    if np.any(fp_mask):
        ax.scatter(x_indices[fp_mask], test_probs[sorted_order][fp_mask], color="magenta", marker="x", s=90, lw=2.5, label=f"False Positives ({np.sum(fp_mask)})", zorder=5)
    if np.any(fn_mask):
        ax.scatter(x_indices[fn_mask], test_probs[sorted_order][fn_mask], color="red", marker="^", s=90, lw=2.5, label=f"False Negatives ({np.sum(fn_mask)})", zorder=5)

    ax.set_title("Held-Out Test Sample Error Analysis & Prediction Spread")
    ax.set_xlabel("Sorted Test Window Index")
    ax.set_ylabel("Predicted Train Horn Probability")
    ax.set_ylim([-0.05, 1.05])
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left", frameon=True)
    plt.tight_layout()
    fig.savefig(fig_dir / "fig9_error_analysis.png", dpi=300)
    plt.close(fig)

    # Fig 10: Spectrogram examples
    fig, axes = plt.subplots(2, 2, figsize=(9, 7))
    tp_idx = next((i for i in range(len(y_test)) if y_test[i] == 1 and test_probs[i] >= best_t and test_probs[i] > 0.8), None)
    tn_idx = next((i for i in range(len(y_test)) if y_test[i] == 0 and test_probs[i] < best_t and test_probs[i] < 0.2), None)
    fp_idx = next((i for i in range(len(y_test)) if y_test[i] == 0 and test_probs[i] >= best_t), None)
    fn_idx = next((i for i in range(len(y_test)) if y_test[i] == 1 and test_probs[i] < best_t), None)

    if fp_idx is None:
        fp_idx = max([i for i in range(len(y_test)) if y_test[i] == 0], key=lambda i: test_probs[i])
    if fn_idx is None:
        fn_idx = min([i for i in range(len(y_test)) if y_test[i] == 1], key=lambda i: test_probs[i])

    cases = [
        ("True Positive: High-Confidence Horn", tp_idx, axes[0, 0]),
        ("True Negative: Ambient Environment", tn_idx, axes[0, 1]),
        ("Difficult Negative / False Positive", fp_idx, axes[1, 0]),
        ("Difficult Positive / False Negative", fn_idx, axes[1, 1]),
    ]
    for title, idx_case, ax_sub in cases:
        if idx_case is not None:
            m = test_meta[idx_case]
            feat_p = WORKSPACE / m["feature_path"]
            f_arr = np.load(feat_p)
            im = ax_sub.imshow(f_arr, origin="lower", aspect="auto", cmap="magma")
            ax_sub.set_title(f"{title}\n{m['source_file']} (P={test_probs[idx_case]:.3f})", fontsize=9)
            ax_sub.set_xlabel("Time Frames (~1.0s)")
            ax_sub.set_ylabel("Mel Frequency Bin")
            fig.colorbar(im, ax=ax_sub, fraction=0.046, pad=0.04)

    plt.suptitle("Log-Mel Spectrogram Diagnostics (64 Mel Bins, 80–8000 Hz)", fontsize=12, weight="bold")
    plt.tight_layout()
    fig.savefig(fig_dir / "fig10_spectrogram_examples.png", dpi=300)
    plt.close(fig)

    # Fig 11: V1 vs V2 Comparison bar chart
    fig, ax = plt.subplots(figsize=(8, 5))
    comp_metrics = ["Accuracy", "Precision", "Recall", "Specificity", "F1-Score", "AUC-ROC"]
    v1_vals = [v1_win["accuracy"], v1_win["precision"], v1_win["recall"], v1_win["specificity"], v1_win["f1_score"], v1_win["auc_roc"]]
    v2_vals = [test_window_metrics["accuracy"], test_window_metrics["precision"], test_window_metrics["recall"],
               test_window_metrics["specificity"], test_window_metrics["f1_score"], test_window_metrics["auc_roc"]]

    x = np.arange(len(comp_metrics))
    width = 0.35
    b1 = ax.bar(x - width/2, [v*100 for v in v1_vals], width, label="Audio V1 (Synthetic ESC-50 Negative)", color="#7f7f7f")
    b2 = ax.bar(x + width/2, [v*100 for v in v2_vals], width, label="Audio V2 (Empirical Field Negative)", color="#1f77b4")

    ax.set_ylabel("Score (%)")
    ax.set_title("Audio Model Performance Comparison: V1 Baseline vs V2 Empirical Model")
    ax.set_xticks(x)
    ax.set_xticklabels(comp_metrics)
    ax.set_ylim([0, 115])
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)
    ax.legend(frameon=True, loc="upper right")

    for bar in b1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 1.5, f"{h:.1f}%", ha="center", va="bottom", fontsize=8)
    for bar in b2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 1.5, f"{h:.1f}%", ha="center", va="bottom", fontsize=8, weight="bold")

    plt.tight_layout()
    fig.savefig(fig_dir / "fig11_v1_vs_v2_comparison.png", dpi=300)
    plt.close(fig)

    logger.info("Successfully generated all 11 publication figures!")
    print("\nTraining and evaluation finished successfully!")


if __name__ == "__main__":
    main()
