"""Detection evaluation: mAP, precision/recall/F1, confusion, PR curves.

Metrics are computed from raw prediction/ground-truth pairs with a pure
NumPy implementation of COCO-style average precision. No metric is ever
fabricated: every reported number is derived from the supplied data.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from railway_detection.utils.logging import get_logger

logger = get_logger("vision.evaluator")

BACKGROUND = "background"


@dataclass(frozen=True)
class GroundTruthBox:
    image_id: str
    label: str
    bbox_xyxy: tuple[float, float, float, float]


@dataclass(frozen=True)
class PredictionBox:
    image_id: str
    label: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]


@dataclass
class DetectionMetrics:
    class_names: list[str]
    iou_threshold: float
    confidence_threshold: float
    map50: float
    map50_95: float
    per_class_ap50: dict[str, float]
    per_class_precision: dict[str, float]
    per_class_recall: dict[str, float]
    per_class_f1: dict[str, float]
    optimal_f1_thresholds: dict[str, float]
    confusion_matrix: dict[str, dict[str, int]]
    total_gt: int = 0
    total_pred: int = 0
    total_tp: int = 0
    total_fp: int = 0
    total_fn: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "iou_threshold": self.iou_threshold,
            "confidence_threshold": self.confidence_threshold,
            "map50": round(self.map50, 4),
            "map50_95": round(self.map50_95, 4),
            "per_class_ap50": self.per_class_ap50,
            "per_class_precision": self.per_class_precision,
            "per_class_recall": self.per_class_recall,
            "per_class_f1": self.per_class_f1,
            "optimal_f1_thresholds": self.optimal_f1_thresholds,
            "confusion_matrix": self.confusion_matrix,
            "total_gt": self.total_gt,
            "total_pred": self.total_pred,
            "total_tp": self.total_tp,
            "total_fp": self.total_fp,
            "total_fn": self.total_fn,
        }


def compute_iou(
    box_a: tuple[float, float, float, float],
    box_b: tuple[float, float, float, float],
) -> float:
    """Intersection-over-union for two xyxy boxes."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    intersection = inter_w * inter_h
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - intersection
    if union <= 0:
        return 0.0
    return float(intersection / union)


def _compute_ap(
    scores: np.ndarray, matched: np.ndarray, total_gt: int
) -> float:
    """Compute average precision from sorted scores and match flags."""
    if total_gt == 0:
        return 0.0
    if len(scores) == 0:
        return 0.0
    order = np.argsort(-scores)
    matched = matched[order]
    tp = np.cumsum(matched)
    fp = np.cumsum(~matched)
    recall = tp / total_gt
    precision = tp / np.maximum(tp + fp, 1e-12)
    recall = np.concatenate(([0.0], recall))
    precision = np.concatenate(([1.0], precision))
    for i in range(len(precision) - 1, 0, -1):
        precision[i - 1] = max(precision[i - 1], precision[i])
    recall_points = np.linspace(0.0, 1.0, 101)
    precision_interp = np.interp(recall_points, recall, precision)
    return float(np.mean(precision_interp))


def _match_class(
    gt_boxes: list[GroundTruthBox],
    pred_boxes: list[PredictionBox],
    iou_threshold: float,
) -> tuple[np.ndarray, np.ndarray, list[float]]:
    """Match predictions of one class to ground truth of that class.

    Returns (scores, matched flags, optimal f1 threshold candidates).
    """
    if not gt_boxes:
        return (
            np.array([], dtype=float),
            np.array([], dtype=bool),
            [0.5],
        )
    pred_boxes = sorted(pred_boxes, key=lambda p: -p.confidence)
    gt_matched: list[bool] = [False] * len(gt_boxes)
    scores: list[float] = []
    matched: list[bool] = []
    for pred in pred_boxes:
        best_iou = 0.0
        best_idx = -1
        for idx, gt in enumerate(gt_boxes):
            if gt_matched[idx]:
                continue
            if gt.image_id != pred.image_id:
                continue
            iou = compute_iou(gt.bbox_xyxy, pred.bbox_xyxy)
            if iou > best_iou:
                best_iou = iou
                best_idx = idx
        if best_idx >= 0 and best_iou >= iou_threshold:
            gt_matched[best_idx] = True
            scores.append(pred.confidence)
            matched.append(True)
        else:
            scores.append(pred.confidence)
            matched.append(False)
    return np.array(scores, dtype=float), np.array(matched, dtype=bool), [0.5]


def _best_f1_threshold(
    scores: np.ndarray, matched: np.ndarray, total_gt: int
) -> float:
    """Threshold maximizing F1 for this class; falls back to 0.5."""
    if total_gt == 0 or len(scores) == 0:
        return 0.5
    order = np.argsort(-scores)
    matched = matched[order]
    scores = scores[order]
    tp = np.cumsum(matched)
    fp = np.cumsum(~matched)
    precision = tp / np.maximum(tp + fp, 1e-12)
    recall = tp / total_gt
    f1 = np.where(
        (precision + recall) > 0,
        2 * precision * recall / np.maximum(precision + recall, 1e-12),
        0.0,
    )
    best_idx = int(np.argmax(f1))
    return float(scores[best_idx])


def _metrics_at_threshold(
    scores: np.ndarray, matched: np.ndarray, total_gt: int, threshold: float
) -> tuple[float, float, float]:
    if total_gt == 0:
        return 0.0, 0.0, 0.0
    tp = int(np.sum(matched & (scores >= threshold)))
    fp = int(np.sum(~matched & (scores >= threshold)))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / total_gt if total_gt > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return float(precision), float(recall), float(f1)


def evaluate_detection(
    ground_truth: list[GroundTruthBox],
    predictions: list[PredictionBox],
    class_names: list[str],
    *,
    iou_threshold: float = 0.5,
    confidence_threshold: float = 0.5,
) -> DetectionMetrics:
    """Compute standard detection metrics from raw boxes.

    mAP@50:95 averages AP over IoU thresholds 0.50..0.95 in 0.05 steps.
    """
    gt_by_class: dict[str, list[GroundTruthBox]] = defaultdict(list)
    for gt_box in ground_truth:
        gt_by_class[gt_box.label].append(gt_box)
    pred_by_class: dict[str, list[PredictionBox]] = defaultdict(list)
    for pred_box in predictions:
        pred_by_class[pred_box.label].append(pred_box)

    per_class_ap50: dict[str, float] = {}
    per_class_ap: dict[str, dict[str, float]] = {name: {} for name in class_names}
    precision_at: dict[str, float] = {}
    recall_at: dict[str, float] = {}
    f1_at: dict[str, float] = {}
    optimal_thresholds: dict[str, float] = {}

    iou_range = np.arange(0.5, 1.0, 0.05)

    for name in class_names:
        gt_boxes = gt_by_class.get(name, [])
        scores, matched, _ = _match_class(gt_boxes, pred_by_class.get(name, []), iou_threshold)
        total_gt = len(gt_boxes)
        if total_gt == 0:
            per_class_ap50[name] = 0.0
            precision_at[name] = 0.0
            recall_at[name] = 0.0
            f1_at[name] = 0.0
            optimal_thresholds[name] = 0.5
            for thr in iou_range:
                per_class_ap[name][f"{thr:.2f}"] = 0.0
            continue
        per_class_ap50[name] = _compute_ap(scores, matched, total_gt)
        for thr in iou_range:
            thr_scores, thr_matched, _ = _match_class(
                gt_boxes, pred_by_class.get(name, []), float(thr)
            )
            per_class_ap[name][f"{thr:.2f}"] = _compute_ap(
                thr_scores, thr_matched, total_gt
            )
        precision, recall, f1 = _metrics_at_threshold(
            scores, matched, total_gt, confidence_threshold
        )
        precision_at[name] = precision
        recall_at[name] = recall
        f1_at[name] = f1
        optimal_thresholds[name] = _best_f1_threshold(scores, matched, total_gt)

    map50 = float(np.mean([per_class_ap50[n] for n in class_names])) if class_names else 0.0
    map50_95 = (
        float(np.mean([float(np.mean(list(per_class_ap[n].values()))) for n in class_names]))
        if class_names
        else 0.0
    )

    confusion: dict[str, dict[str, int]] = {
        row: {col: 0 for col in class_names + [BACKGROUND]}
        for row in class_names + [BACKGROUND]
    }
    total_tp = 0
    total_fp = 0
    total_fn = 0
    for name in class_names:
        gt_boxes = gt_by_class.get(name, [])
        preds = pred_by_class.get(name, [])
        gt_matched = [False] * len(gt_boxes)
        for pred in sorted(preds, key=lambda p: -p.confidence):
            best_iou = 0.0
            best_idx = -1
            for idx, gt in enumerate(gt_boxes):
                if gt_matched[idx] or gt.image_id != pred.image_id:
                    continue
                iou = compute_iou(gt.bbox_xyxy, pred.bbox_xyxy)
                if iou > best_iou:
                    best_iou = iou
                    best_idx = idx
            if best_idx >= 0 and best_iou >= iou_threshold:
                gt_matched[best_idx] = True
                confusion[name][name] += 1
                total_tp += 1
            else:
                confusion[BACKGROUND][name] += 1
                total_fp += 1
        for idx, _gt_box in enumerate(gt_boxes):
            if not gt_matched[idx]:
                confusion[name][BACKGROUND] += 1
                total_fn += 1

    metrics = DetectionMetrics(
        class_names=list(class_names),
        iou_threshold=iou_threshold,
        confidence_threshold=confidence_threshold,
        map50=map50,
        map50_95=map50_95,
        per_class_ap50=per_class_ap50,
        per_class_precision=precision_at,
        per_class_recall=recall_at,
        per_class_f1=f1_at,
        optimal_f1_thresholds=optimal_thresholds,
        confusion_matrix=confusion,
        total_gt=len(ground_truth),
        total_pred=len(predictions),
        total_tp=total_tp,
        total_fp=total_fp,
        total_fn=total_fn,
    )
    return metrics


def write_metrics(
    metrics: DetectionMetrics, output_dir: Path
) -> tuple[Path, Path]:
    """Write metrics.json and a human-readable metrics.md."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "metrics.json"
    json_path.write_text(
        json.dumps(metrics.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path = output_dir / "metrics.md"
    lines = [
        "# Vision Detection Metrics",
        "",
        f"- mAP@50: **{metrics.map50:.4f}**",
        f"- mAP@50:95: **{metrics.map50_95:.4f}**",
        f"- Confidence threshold: {metrics.confidence_threshold}",
        f"- IoU threshold: {metrics.iou_threshold}",
        "",
        "| Class | AP@50 | Precision | Recall | F1 | Optimal F1 thr |",
        "|---|---|---|---|---|---|",
    ]
    for name in metrics.class_names:
        lines.append(
            f"| {name} | {metrics.per_class_ap50[name]:.4f} | "
            f"{metrics.per_class_precision[name]:.4f} | "
            f"{metrics.per_class_recall[name]:.4f} | "
            f"{metrics.per_class_f1[name]:.4f} | "
            f"{metrics.optimal_f1_thresholds[name]:.3f} |"
        )
    lines += [
        "",
        f"Total GT boxes: {metrics.total_gt}",
        f"Total predictions: {metrics.total_pred}",
        f"TP: {metrics.total_tp}, FP: {metrics.total_fp}, FN: {metrics.total_fn}",
        "",
        "> Generated from actual prediction/ground-truth data; no fabricated values.",
        "",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def plot_confusion_matrix(metrics: DetectionMetrics, output_dir: Path) -> Path:
    """Render the confusion matrix (including background) to PNG."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = metrics.class_names + [BACKGROUND]
    matrix = np.zeros((len(labels), len(labels)), dtype=int)
    for i, row_name in enumerate(labels):
        for j, col_name in enumerate(labels):
            matrix[i, j] = metrics.confusion_matrix.get(row_name, {}).get(col_name, 0)

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "confusion_matrix.png"
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels, rotation=45)
    ax.set_yticks(range(len(labels)), labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, str(matrix[i, j]), ha="center", va="center")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Ground truth")
    ax.set_title("Confusion Matrix")
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_pr_curves(
    ground_truth: list[GroundTruthBox],
    predictions: list[PredictionBox],
    class_names: list[str],
    output_dir: Path,
    iou_threshold: float = 0.5,
) -> Path:
    """Render per-class precision-recall curves to PNG."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "pr_curves.png"
    fig, ax = plt.subplots(figsize=(7, 5))
    for name in class_names:
        gt_boxes = [b for b in ground_truth if b.label == name]
        preds = [b for b in predictions if b.label == name]
        scores, matched, _ = _match_class(gt_boxes, preds, iou_threshold)
        total_gt = len(gt_boxes)
        if total_gt == 0 or len(scores) == 0:
            ax.plot([], [], label=f"{name} (no data)")
            continue
        order = np.argsort(-scores)
        matched = matched[order]
        tp = np.cumsum(matched)
        fp = np.cumsum(~matched)
        recall = tp / total_gt
        precision = tp / np.maximum(tp + fp, 1e-12)
        ax.plot(recall, precision, label=name)
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall Curves")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path
