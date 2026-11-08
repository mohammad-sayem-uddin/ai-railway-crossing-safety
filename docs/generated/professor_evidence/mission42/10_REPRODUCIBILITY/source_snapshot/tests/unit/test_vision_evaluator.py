"""Unit tests for detection metric computation.

Metrics are verified against hand-computable synthetic boxes so that the
test suite never depends on a trained model or an external metric library.
"""

from __future__ import annotations

import json

from railway_detection.vision.evaluator import (
    BACKGROUND,
    GroundTruthBox,
    PredictionBox,
    compute_iou,
    evaluate_detection,
    write_metrics,
)


def box(x1, y1, x2, y2):
    return (float(x1), float(y1), float(x2), float(y2))


def test_iou_perfect_and_disjoint():
    a = box(0, 0, 10, 10)
    assert compute_iou(a, box(0, 0, 10, 10)) == 1.0
    assert compute_iou(a, box(20, 20, 30, 30)) == 0.0
    assert compute_iou(a, box(5, 5, 15, 15)) == 25.0 / 175.0


def test_empty_evaluation_is_zero_not_fabricated():
    metrics = evaluate_detection([], [], ["front", "side", "rear"])
    assert metrics.map50 == 0.0
    assert metrics.map50_95 == 0.0
    assert metrics.total_gt == 0
    assert metrics.total_pred == 0
    assert metrics.total_tp == 0


def test_perfect_detection():
    gt = [
        GroundTruthBox("img1", "front", box(0, 0, 10, 10)),
        GroundTruthBox("img2", "side", box(5, 5, 15, 15)),
    ]
    pred = [
        PredictionBox("img1", "front", 0.99, box(0, 0, 10, 10)),
        PredictionBox("img2", "side", 0.98, box(5, 5, 15, 15)),
    ]
    metrics = evaluate_detection(gt, pred, ["front", "side"])
    assert metrics.map50 == 1.0
    assert metrics.per_class_ap50["front"] == 1.0
    assert metrics.per_class_ap50["side"] == 1.0
    assert metrics.per_class_recall["front"] == 1.0
    assert metrics.per_class_precision["front"] == 1.0
    assert metrics.total_tp == 2
    assert metrics.total_fp == 0
    assert metrics.total_fn == 0


def test_missed_detection_counts_as_fn():
    gt = [GroundTruthBox("img1", "front", box(0, 0, 10, 10))]
    pred = []  # detector emitted nothing
    metrics = evaluate_detection(gt, pred, ["front"])
    assert metrics.total_fn == 1
    assert metrics.total_tp == 0
    assert metrics.per_class_recall["front"] == 0.0
    assert metrics.confusion_matrix["front"][BACKGROUND] == 1


def test_false_positive_counts_in_confusion():
    gt = [GroundTruthBox("img1", "front", box(0, 0, 10, 10))]
    pred = [PredictionBox("img1", "rear", 0.9, box(0, 0, 10, 10))]
    metrics = evaluate_detection(gt, pred, ["front", "rear"])
    assert metrics.total_fp == 1
    assert metrics.total_fn == 1
    assert metrics.confusion_matrix[BACKGROUND]["rear"] == 1


def test_low_confidence_below_threshold_not_counted():
    gt = [GroundTruthBox("img1", "front", box(0, 0, 10, 10))]
    pred = [PredictionBox("img1", "front", 0.1, box(0, 0, 10, 10))]
    metrics = evaluate_detection(
        gt, pred, ["front"], confidence_threshold=0.5
    )
    # AP curves still consider the box, but threshold metrics do not.
    assert metrics.per_class_recall["front"] == 0.0
    assert metrics.per_class_precision["front"] == 0.0


def test_iou_below_threshold_is_false_positive():
    gt = [GroundTruthBox("img1", "front", box(0, 0, 10, 10))]
    pred = [PredictionBox("img1", "front", 0.9, box(20, 20, 30, 30))]
    metrics = evaluate_detection(gt, pred, ["front"], iou_threshold=0.5)
    assert metrics.total_fp == 1
    assert metrics.total_fn == 1


def test_write_metrics_artifacts(tmp_path):
    gt = [GroundTruthBox("img1", "front", box(0, 0, 10, 10))]
    pred = [PredictionBox("img1", "front", 0.9, box(0, 0, 10, 10))]
    metrics = evaluate_detection(gt, pred, ["front"])
    json_path, md_path = write_metrics(metrics, tmp_path / "out")
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["map50"] == 1.0
    assert "mAP@50" in md_path.read_text(encoding="utf-8")


def test_confusion_matrix_shape_includes_background():
    gt = [GroundTruthBox("img1", "front", box(0, 0, 10, 10))]
    pred = [PredictionBox("img1", "front", 0.9, box(0, 0, 10, 10))]
    metrics = evaluate_detection(gt, pred, ["front", "side", "rear"])
    for row in metrics.class_names + [BACKGROUND]:
        assert row in metrics.confusion_matrix
        for col in metrics.class_names + [BACKGROUND]:
            assert col in metrics.confusion_matrix[row]
