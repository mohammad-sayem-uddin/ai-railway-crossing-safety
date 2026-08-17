"""Automated failure analysis for detection results.

Classifies each detection error into predefined failure categories and
produces metadata slices only when the corresponding metadata is present.
Unknown metadata is recorded as ``unknown`` — never inferred from appearance.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from railway_detection.utils.logging import get_logger
from railway_detection.vision.evaluator import (
    GroundTruthBox,
    PredictionBox,
    compute_iou,
)

logger = get_logger("vision.failure_analysis")

FAILURE_CODES = (
    "missed_front",
    "missed_side",
    "missed_rear",
    "front_side_confusion",
    "rear_side_confusion",
    "false_train_detection",
    "low_confidence_detection",
)


@dataclass(frozen=True)
class FailureCase:
    failure_code: str
    image_id: str
    label: str
    predicted_label: str | None
    confidence: float | None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FailureAnalysisResult:
    cases: list[FailureCase] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "failure_count": len(self.cases),
            "cases": [
                {
                    "failure_code": case.failure_code,
                    "image_id": case.image_id,
                    "label": case.label,
                    "predicted_label": case.predicted_label,
                    "confidence": case.confidence,
                    "metadata": case.metadata,
                }
                for case in self.cases
            ],
        }


def analyze_failures(
    ground_truth: list[GroundTruthBox],
    predictions: list[PredictionBox],
    *,
    metadata: dict[str, dict[str, Any]] | None = None,
    iou_threshold: float = 0.5,
    confidence_threshold: float = 0.5,
) -> FailureAnalysisResult:
    """Classify detection failures against ground truth.

    ``metadata`` maps image_id to a metadata record; slices are computed only
    for keys that are actually present, and missing values become
    ``unknown``.
    """
    metadata = metadata or {}
    result = FailureAnalysisResult()

    gt_by_image: dict[str, list[GroundTruthBox]] = defaultdict(list)
    for gt in ground_truth:
        gt_by_image[gt.image_id].append(gt)

    pred_by_image: dict[str, list[PredictionBox]] = defaultdict(list)
    for pred in predictions:
        pred_by_image[pred.image_id].append(pred)

    # Matched ground truth boxes per image.
    matched_gt: set[tuple[str, int]] = set()

    # Pass 1: confusion errors (prediction overlaps a GT of another class).
    for image_id, gt_boxes in gt_by_image.items():
        image_preds = sorted(pred_by_image.get(image_id, []), key=lambda p: -p.confidence)
        for gt_idx, gt in enumerate(gt_boxes):
            best_pred: PredictionBox | None = None
            best_iou = 0.0
            for pred in image_preds:
                iou = compute_iou(gt.bbox_xyxy, pred.bbox_xyxy)
                if iou > best_iou:
                    best_iou = iou
                    best_pred = pred
            if best_pred is not None and best_iou >= iou_threshold:
                if best_pred.confidence < confidence_threshold:
                    result.cases.append(
                        FailureCase(
                            failure_code="low_confidence_detection",
                            image_id=image_id,
                            label=gt.label,
                            predicted_label=best_pred.label,
                            confidence=best_pred.confidence,
                            metadata=metadata.get(image_id, {}),
                        )
                    )
                    continue
                if best_pred.label != gt.label:
                    code = _confusion_code(gt.label, best_pred.label)
                    if code is not None:
                        result.cases.append(
                            FailureCase(
                                failure_code=code,
                                image_id=image_id,
                                label=gt.label,
                                predicted_label=best_pred.label,
                                confidence=best_pred.confidence,
                                metadata=metadata.get(image_id, {}),
                            )
                        )
                matched_gt.add((image_id, gt_idx))

    # Pass 2: missed detections.
    for image_id, gt_boxes in gt_by_image.items():
        for gt_idx, gt in enumerate(gt_boxes):
            if (image_id, gt_idx) in matched_gt:
                continue
            code = {
                "front": "missed_front",
                "side": "missed_side",
                "rear": "missed_rear",
            }.get(gt.label)
            if code is None:
                continue
            # Distinguish "nothing predicted" from "predicted below threshold".
            image_preds = pred_by_image.get(image_id, [])
            closest_pred: PredictionBox | None = None
            best_iou = 0.0
            for pred in image_preds:
                iou = compute_iou(gt.bbox_xyxy, pred.bbox_xyxy)
                if iou > best_iou:
                    best_iou = iou
                    closest_pred = pred
            if closest_pred is not None and closest_pred.confidence < confidence_threshold:
                result.cases.append(
                    FailureCase(
                        failure_code="low_confidence_detection",
                        image_id=image_id,
                        label=gt.label,
                        predicted_label=closest_pred.label,
                        confidence=closest_pred.confidence,
                        metadata=metadata.get(image_id, {}),
                    )
                )
            else:
                result.cases.append(
                    FailureCase(
                        failure_code=code,
                        image_id=image_id,
                        label=gt.label,
                        predicted_label=None,
                        confidence=None,
                        metadata=metadata.get(image_id, {}),
                    )
                )

    # Pass 3: false positives (no overlapping GT of any class).
    for image_id, image_preds in pred_by_image.items():
        gt_boxes = gt_by_image.get(image_id, [])
        for pred in image_preds:
            if pred.confidence < confidence_threshold:
                continue
            overlap = any(
                compute_iou(pred.bbox_xyxy, gt.bbox_xyxy) >= iou_threshold
                for gt in gt_boxes
            )
            if not overlap:
                result.cases.append(
                    FailureCase(
                        failure_code="false_train_detection",
                        image_id=image_id,
                        label=pred.label,
                        predicted_label=pred.label,
                        confidence=pred.confidence,
                        metadata=metadata.get(image_id, {}),
                    )
                )

    result.summary = _summarize(result.cases, metadata, gt_by_image, pred_by_image)
    return result


def _confusion_code(gt_label: str, pred_label: str) -> str | None:
    pair = {gt_label, pred_label}
    if pair == {"front", "side"}:
        return "front_side_confusion"
    if pair == {"rear", "side"}:
        return "rear_side_confusion"
    return None


def _summarize(
    cases: list[FailureCase],
    metadata: dict[str, dict[str, Any]],
    gt_by_image: dict[str, list[GroundTruthBox]],
    pred_by_image: dict[str, list[PredictionBox]],
) -> dict[str, Any]:
    code_counts: Counter[str] = Counter(case.failure_code for case in cases)
    slice_keys = {"weather", "lighting", "occlusion", "distance_band"}
    slice_counts: dict[str, dict[str, int]] = {}
    for key in slice_keys:
        counter: Counter[str] = Counter()
        for case in cases:
            value = case.metadata.get(key)
            counter[str(value) if value is not None else "unknown"] += 1
        slice_counts[key] = dict(sorted(counter.items()))

    image_count_with_metadata = sum(
        1 for image_id in set(gt_by_image) | set(pred_by_image)
        if image_id in metadata
    )
    total_images = len(set(gt_by_image) | set(pred_by_image))

    return {
        "failure_counts": dict(sorted(code_counts.items())),
        "total_failure_cases": len(cases),
        "slices": slice_counts,
        "images_with_metadata": image_count_with_metadata,
        "total_images": total_images,
        "metadata_coverage_note": (
            "slices only count failures whose image has the corresponding "
            "metadata key; unknown values are recorded as 'unknown'"
        ),
    }


def write_failure_analysis(
    analysis: FailureAnalysisResult, output_dir: Path
) -> tuple[Path, Path]:
    """Write failure_analysis.json and failure_report.md."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "failure_analysis.json"
    json_path.write_text(
        json.dumps(analysis.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path = output_dir / "failure_report.md"
    lines = [
        "# Failure Analysis Report",
        "",
        f"Total failure cases: **{len(analysis.cases)}**",
        "",
        "| Failure code | Count |",
        "|---|---|",
    ]
    for code in FAILURE_CODES:
        count = analysis.summary.get("failure_counts", {}).get(code, 0)
        lines.append(f"| {code} | {count} |")
    lines += [
        "",
        "> Generated from actual prediction/ground-truth data; metadata slices "
        "only include images with the corresponding metadata key.",
        "",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path
