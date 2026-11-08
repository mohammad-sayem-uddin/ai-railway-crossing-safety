"""Binary audio classification metrics, calibration, and visualization interfaces.

Implements research metrics and plotting functions for train horn acoustic detection:
- Precision, Recall (Sensitivity), Specificity, F1-score, Balanced Accuracy
- Area Under the ROC Curve (AUC-ROC)
- Area Under the Precision-Recall Curve (PR-AUC / Average Precision)
- False Alarm Rate (FAR) per hour of evaluable non-train audio
- Expected Calibration Error (ECE) and Brier Score
- Operating threshold calibration under false alarm constraints
- Publication-grade figure generators
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class BinaryClassificationMetrics:
    """Comprehensive metric report for binary audio classification."""

    threshold: float
    total_samples: int
    positive_samples: int
    negative_samples: int
    tp: int
    fp: int
    fn: int
    tn: int
    accuracy: float
    precision: float
    recall: float
    specificity: float
    f1_score: float
    balanced_accuracy: float
    auc_roc: float
    pr_auc: float
    brier_score: float
    expected_calibration_error: float
    false_alarms_per_hour: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "threshold": round(self.threshold, 4),
            "total_samples": self.total_samples,
            "positive_samples": self.positive_samples,
            "negative_samples": self.negative_samples,
            "confusion_matrix": {
                "tp": self.tp,
                "fp": self.fp,
                "fn": self.fn,
                "tn": self.tn,
            },
            "rates": {
                "accuracy": round(self.accuracy, 4),
                "precision": round(self.precision, 4),
                "recall": round(self.recall, 4),
                "specificity": round(self.specificity, 4),
                "f1_score": round(self.f1_score, 4),
                "balanced_accuracy": round(self.balanced_accuracy, 4),
                "auc_roc": round(self.auc_roc, 4),
                "pr_auc": round(self.pr_auc, 4),
                "brier_score": round(self.brier_score, 4),
                "expected_calibration_error": round(self.expected_calibration_error, 4),
                "false_alarms_per_hour": round(self.false_alarms_per_hour, 2)
                if self.false_alarms_per_hour is not None
                else None,
            },
        }


def compute_roc_curve(
    y_true: np.ndarray, y_score: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Compute Receiver Operating Characteristic (ROC) curve and AUC.

    Args:
        y_true: Ground truth binary labels (0 or 1).
        y_score: Predicted probabilities in [0.0, 1.0].

    Returns:
        Tuple of (fpr_array, tpr_array, thresholds, auc_roc).
    """
    y_true = np.asarray(y_true, dtype=int).flatten()
    y_score = np.asarray(y_score, dtype=float).flatten()

    if len(y_true) != len(y_score):
        raise ValueError("y_true and y_score must have equal length")

    n_pos = int(np.sum(y_true == 1))
    n_neg = int(np.sum(y_true == 0))

    if n_pos == 0 or n_neg == 0:
        # Undefined ROC when only one class is present
        return np.array([0.0, 1.0]), np.array([0.0, 1.0]), np.array([1.0, 0.0]), 0.5

    # Sort descending by score
    desc_indices = np.argsort(y_score)[::-1]
    y_sorted = y_true[desc_indices]
    score_sorted = y_score[desc_indices]

    # Find unique threshold cutoffs
    distinct_mask = np.diff(score_sorted, append=np.nan) != 0
    tps = np.cumsum(y_sorted == 1)[distinct_mask]
    fps = np.cumsum(y_sorted == 0)[distinct_mask]
    thresholds = score_sorted[distinct_mask]

    # Prepend origin (0, 0)
    tpr = np.r_[0.0, tps / float(n_pos)]
    fpr = np.r_[0.0, fps / float(n_neg)]
    thresholds = np.r_[thresholds[0] + 1e-6, thresholds]

    # Trapezoidal integration for AUC (compatible with NumPy 1.x and 2.x)
    if hasattr(np, "trapezoid"):
        auc_roc = float(np.trapezoid(tpr, fpr))
    elif hasattr(np, "trapz"):
        auc_roc = float(getattr(np, "trapz")(tpr, fpr))
    else:
        auc_roc = float(np.sum((fpr[1:] - fpr[:-1]) * (tpr[1:] + tpr[:-1]) / 2.0))
    return fpr, tpr, thresholds, auc_roc


def compute_pr_curve(
    y_true: np.ndarray, y_score: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Compute Precision-Recall curve and Average Precision (PR-AUC).

    Args:
        y_true: Ground truth binary labels (0 or 1).
        y_score: Predicted probabilities in [0.0, 1.0].

    Returns:
        Tuple of (precision_array, recall_array, thresholds, pr_auc).
    """
    y_true = np.asarray(y_true, dtype=int).flatten()
    y_score = np.asarray(y_score, dtype=float).flatten()

    n_pos = int(np.sum(y_true == 1))
    if n_pos == 0:
        return np.array([0.0]), np.array([0.0]), np.array([1.0]), 0.0

    desc_indices = np.argsort(y_score)[::-1]
    y_sorted = y_true[desc_indices]
    score_sorted = y_score[desc_indices]

    distinct_mask = np.diff(score_sorted, append=np.nan) != 0
    tps = np.cumsum(y_sorted == 1)[distinct_mask]
    fps = np.cumsum(y_sorted == 0)[distinct_mask]
    thresholds = score_sorted[distinct_mask]

    recall = tps / float(n_pos)
    precision = tps / (tps + fps)

    # Prepend recall=0 with precision=1
    recall = np.r_[0.0, recall]
    precision = np.r_[1.0, precision]
    thresholds = np.r_[thresholds[0] + 1e-6, thresholds]

    # Average Precision via step integration
    pr_auc = float(np.sum((recall[1:] - recall[:-1]) * precision[1:]))
    return precision, recall, thresholds, pr_auc


def compute_calibration_error(
    y_true: np.ndarray, y_score: np.ndarray, n_bins: int = 10
) -> tuple[float, float]:
    """Compute Brier Score and Expected Calibration Error (ECE).

    Args:
        y_true: Ground truth binary labels (0 or 1).
        y_score: Predicted probabilities in [0.0, 1.0].
        n_bins: Number of equal-width probability bins.

    Returns:
        Tuple of (brier_score, expected_calibration_error).
    """
    y_true = np.asarray(y_true, dtype=float).flatten()
    y_score = np.asarray(y_score, dtype=float).flatten()

    if len(y_true) == 0:
        return 0.0, 0.0

    # Brier Score = mean squared error between probability and true binary label
    brier_score = float(np.mean((y_score - y_true) ** 2.0))

    # ECE calculation over uniform bins
    bin_limits = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n_total = len(y_true)

    for i in range(n_bins):
        bin_lower = bin_limits[i]
        bin_upper = bin_limits[i + 1]
        if i == n_bins - 1:
            in_bin = (y_score >= bin_lower) & (y_score <= bin_upper)
        else:
            in_bin = (y_score >= bin_lower) & (y_score < bin_upper)

        n_bin = np.sum(in_bin)
        if n_bin > 0:
            bin_acc = float(np.mean(y_true[in_bin]))
            bin_conf = float(np.mean(y_score[in_bin]))
            ece += (n_bin / n_total) * abs(bin_acc - bin_conf)

    return brier_score, float(ece)


def compute_binary_metrics(
    y_true: np.ndarray,
    y_score: np.ndarray,
    threshold: float = 0.5,
    evaluable_negative_hours: float | None = None,
) -> BinaryClassificationMetrics:
    """Compute all evaluation metrics for binary classification at a chosen threshold."""
    y_true = np.asarray(y_true, dtype=int).flatten()
    y_score = np.asarray(y_score, dtype=float).flatten()
    y_pred = (y_score >= threshold).astype(int)

    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))

    n_pos = tp + fn
    n_neg = fp + tn
    total = len(y_true)

    accuracy = float(tp + tn) / float(total) if total > 0 else 0.0
    precision = float(tp) / float(tp + fp) if (tp + fp) > 0 else 0.0
    recall = float(tp) / float(n_pos) if n_pos > 0 else 0.0
    specificity = float(tn) / float(n_neg) if n_neg > 0 else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    balanced_acc = 0.5 * (recall + specificity)

    # Curves & calibration
    _, _, _, auc_roc = compute_roc_curve(y_true, y_score)
    _, _, _, pr_auc = compute_pr_curve(y_true, y_score)
    brier, ece = compute_calibration_error(y_true, y_score)

    far_per_hour = None
    if evaluable_negative_hours is not None and evaluable_negative_hours > 0:
        far_per_hour = float(fp) / float(evaluable_negative_hours)

    return BinaryClassificationMetrics(
        threshold=float(threshold),
        total_samples=total,
        positive_samples=n_pos,
        negative_samples=n_neg,
        tp=tp,
        fp=fp,
        fn=fn,
        tn=tn,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        specificity=specificity,
        f1_score=f1,
        balanced_accuracy=balanced_acc,
        auc_roc=auc_roc,
        pr_auc=pr_auc,
        brier_score=brier,
        expected_calibration_error=ece,
        false_alarms_per_hour=far_per_hour,
    )


def calibrate_operating_threshold(
    y_true: np.ndarray,
    y_score: np.ndarray,
    target_metric: str = "f1",
    max_fpr: float = 0.01,
) -> tuple[float, BinaryClassificationMetrics]:
    """Find the optimal decision threshold on validation data.

    Supported strategies:
    - 'f1': Maximizes the F1-score.
    - 'max_fpr': Constrains FPR <= max_fpr (conservative safety requirement).
    """
    y_true = np.asarray(y_true, dtype=int).flatten()
    y_score = np.asarray(y_score, dtype=float).flatten()

    candidate_thresholds = np.unique(y_score)
    if len(candidate_thresholds) > 200:
        candidate_thresholds = np.percentile(y_score, np.linspace(0, 100, 200))
    candidate_thresholds = np.clip(candidate_thresholds, 0.01, 0.99)

    best_thresh = 0.5
    best_metrics = compute_binary_metrics(y_true, y_score, threshold=0.5)

    if target_metric == "f1":
        best_f1 = -1.0
        for t in candidate_thresholds:
            m = compute_binary_metrics(y_true, y_score, threshold=t)
            if m.f1_score > best_f1:
                best_f1 = m.f1_score
                best_thresh = float(t)
                best_metrics = m
    elif target_metric == "max_fpr":
        best_recall = -1.0
        for t in candidate_thresholds:
            m = compute_binary_metrics(y_true, y_score, threshold=t)
            fpr = float(m.fp) / float(m.negative_samples) if m.negative_samples > 0 else 0.0
            if fpr <= max_fpr and m.recall > best_recall:
                best_recall = m.recall
                best_thresh = float(t)
                best_metrics = m

    return best_thresh, best_metrics


def plot_audio_roc_curve(
    y_true: np.ndarray,
    y_score: np.ndarray,
    output_png_path: str | Path,
    model_name: str = "Audio Classifier",
) -> Path:
    """Generate and save publication ROC curve figure."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path = Path(output_png_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fpr, tpr, _, auc_roc = compute_roc_curve(y_true, y_score)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(fpr, tpr, color="#1f77b4", linewidth=2.5, label=f"{model_name} (AUC = {auc_roc:.3f})")
    ax.plot([0, 1], [0, 1], color="#7f7f7f", linestyle="--", linewidth=1.5, label="Random Guess (AUC = 0.500)")
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
    ax.set_ylabel("True Positive Rate (Recall / Sensitivity)", fontsize=11)
    ax.set_title(f"Receiver Operating Characteristic (ROC)\n{model_name}", fontsize=12, pad=10)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower right", frameon=True)

    plt.tight_layout()
    fig.savefig(str(output_path), dpi=150)
    plt.close(fig)
    return output_path


def plot_audio_pr_curve(
    y_true: np.ndarray,
    y_score: np.ndarray,
    output_png_path: str | Path,
    model_name: str = "Audio Classifier",
) -> Path:
    """Generate and save publication Precision-Recall curve figure."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path = Path(output_png_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    precision, recall, _, pr_auc = compute_pr_curve(y_true, y_score)
    pos_prevalence = float(np.sum(y_true == 1)) / float(len(y_true)) if len(y_true) > 0 else 0.0

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(recall, precision, color="#2ca02c", linewidth=2.5, label=f"{model_name} (PR-AUC = {pr_auc:.3f})")
    ax.axhline(pos_prevalence, color="#d62728", linestyle="--", linewidth=1.5, label=f"Prevalence ({pos_prevalence:.1%})")
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    ax.set_xlabel("Recall (Sensitivity)", fontsize=11)
    ax.set_ylabel("Precision (Positive Predictive Value)", fontsize=11)
    ax.set_title(f"Precision-Recall Curve\n{model_name}", fontsize=12, pad=10)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower left", frameon=True)

    plt.tight_layout()
    fig.savefig(str(output_path), dpi=150)
    plt.close(fig)
    return output_path


def plot_audio_confusion_matrix(
    metrics: BinaryClassificationMetrics,
    output_png_path: str | Path,
    class_names: tuple[str, str] = ("Non-Horn", "Train Horn"),
) -> Path:
    """Generate and save publication-grade normalized 2x2 confusion matrix."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path = Path(output_png_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cm = np.array([[metrics.tn, metrics.fp], [metrics.fn, metrics.tp]])
    row_sums = cm.sum(axis=1, keepdims=True)
    cm_norm = np.divide(cm.astype(float), row_sums, out=np.zeros_like(cm, dtype=float), where=row_sums != 0)

    fig, ax = plt.subplots(figsize=(5, 4.5))
    im = ax.imshow(cm_norm, cmap="Blues", vmin=0.0, vmax=1.0)

    # Add colorbar
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel("Normalized Rate", rotation=-90, va="bottom")

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(class_names, fontsize=10)
    ax.set_yticklabels(class_names, fontsize=10)
    ax.set_xlabel("Predicted Class", fontsize=11)
    ax.set_ylabel("True Ground Truth", fontsize=11)
    ax.set_title(f"Confusion Matrix (T = {metrics.threshold:.2f})\nAccuracy: {metrics.accuracy:.1%}, F1: {metrics.f1_score:.3f}", fontsize=11, pad=10)

    # Annotate counts and percentages
    for i in range(2):
        for j in range(2):
            count = cm[i, j]
            pct = cm_norm[i, j]
            color = "white" if pct > 0.5 else "black"
            ax.text(j, i, f"{count}\n({pct:.1%})", ha="center", va="center", color=color, fontsize=10, weight="bold")

    plt.tight_layout()
    fig.savefig(str(output_path), dpi=150)
    plt.close(fig)
    return output_path
