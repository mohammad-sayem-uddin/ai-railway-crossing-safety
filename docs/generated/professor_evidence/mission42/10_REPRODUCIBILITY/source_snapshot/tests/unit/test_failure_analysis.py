"""Unit tests for automated failure analysis."""

from __future__ import annotations

import json

from railway_detection.vision.evaluator import GroundTruthBox, PredictionBox
from railway_detection.vision.failure_analysis import (
    analyze_failures,
    write_failure_analysis,
)


def box(x1, y1, x2, y2):
    return (float(x1), float(y1), float(x2), float(y2))


def test_missed_front():
    gt = [GroundTruthBox("img1", "front", box(0, 0, 10, 10))]
    result = analyze_failures(gt, [])
    assert len(result.cases) == 1
    assert result.cases[0].failure_code == "missed_front"
    assert result.cases[0].predicted_label is None


def test_missed_side_and_rear():
    gt = [
        GroundTruthBox("img1", "side", box(0, 0, 10, 10)),
        GroundTruthBox("img2", "rear", box(0, 0, 10, 10)),
    ]
    result = analyze_failures(gt, [])
    codes = sorted(case.failure_code for case in result.cases)
    assert codes == ["missed_rear", "missed_side"]


def test_front_side_confusion():
    gt = [GroundTruthBox("img1", "front", box(0, 0, 10, 10))]
    pred = [PredictionBox("img1", "side", 0.9, box(0, 0, 10, 10))]
    result = analyze_failures(gt, pred)
    assert len(result.cases) == 1
    assert result.cases[0].failure_code == "front_side_confusion"


def test_rear_side_confusion():
    gt = [GroundTruthBox("img1", "rear", box(0, 0, 10, 10))]
    pred = [PredictionBox("img1", "side", 0.8, box(0, 0, 10, 10))]
    result = analyze_failures(gt, pred)
    assert result.cases[0].failure_code == "rear_side_confusion"


def test_false_positive_on_clean_image():
    gt: list[GroundTruthBox] = []
    pred = [PredictionBox("img1", "front", 0.95, box(0, 0, 10, 10))]
    result = analyze_failures(gt, pred)
    assert len(result.cases) == 1
    assert result.cases[0].failure_code == "false_train_detection"


def test_low_confidence_detection():
    gt = [GroundTruthBox("img1", "front", box(0, 0, 10, 10))]
    pred = [PredictionBox("img1", "front", 0.2, box(0, 0, 10, 10))]
    result = analyze_failures(gt, pred, confidence_threshold=0.5)
    assert result.cases[0].failure_code == "low_confidence_detection"
    assert result.cases[0].confidence == 0.2


def test_correct_detection_has_no_failures():
    gt = [GroundTruthBox("img1", "front", box(0, 0, 10, 10))]
    pred = [PredictionBox("img1", "front", 0.9, box(0, 0, 10, 10))]
    result = analyze_failures(gt, pred)
    assert result.cases == []
    assert result.summary["total_failure_cases"] == 0


def test_metadata_slices_use_unknown_for_missing():
    gt = [GroundTruthBox("img1", "front", box(0, 0, 10, 10))]
    metadata = {"img1": {"weather": "rain"}}
    result = analyze_failures(gt, [], metadata=metadata)
    assert result.cases[0].metadata["weather"] == "rain"
    assert result.summary["slices"]["weather"].get("rain") == 1

    result2 = analyze_failures(
        [GroundTruthBox("img2", "front", box(0, 0, 10, 10))], []
    )
    assert result2.cases[0].metadata == {}
    assert result2.summary["slices"]["weather"].get("unknown") == 1


def test_write_failure_analysis_artifacts(tmp_path):
    gt = [GroundTruthBox("img1", "front", box(0, 0, 10, 10))]
    result = analyze_failures(gt, [])
    json_path, md_path = write_failure_analysis(result, tmp_path / "out")
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["failure_count"] == 1
    assert "missed_front" in md_path.read_text(encoding="utf-8")
