"""Verification tests for the complete 27-event multimodal evaluation artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO_ROOT / "results" / "multimodal_27_event_evaluation"


def test_complete_27_event_multimodal_outputs_exist_and_cover_all_cohorts() -> None:
    required_files = [
        EVAL_DIR / "event_by_event_27_multimodal_evaluation.csv",
        EVAL_DIR / "event_by_event_27_multimodal_evaluation.json",
        EVAL_DIR / "modality_and_fusion_ablation_metrics.csv",
        EVAL_DIR / "modality_and_fusion_ablation_metrics.json",
        EVAL_DIR / "COMPLETE_27_EVENT_MULTIMODAL_EXPERIMENT_REPORT.md",
    ]
    for path in required_files:
        assert path.exists(), f"Missing artifact: {path}"
        assert path.stat().st_size > 0, f"Empty artifact: {path}"

    with open(EVAL_DIR / "event_by_event_27_multimodal_evaluation.csv", "r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 27
    cohorts = [r["cohort"] for r in rows]
    assert cohorts.count("train_events") == 23
    assert cohorts.count("no_train_events") == 3
    assert cohorts.count("engine_events") == 1

    payload = json.loads((EVAL_DIR / "event_by_event_27_multimodal_evaluation.json").read_text(encoding="utf-8"))
    assert payload["n_events"] == 27
    assert payload["provenance"]["raw_media_accessed"] is False
    assert "pre-db40305" in payload["provenance"]["vision"]
    assert "CompactTrainHornCNN" in payload["provenance"]["audio"]
    assert "RESEARCHER_ANNOTATION_ADOPTION" in payload["provenance"]["reference"]


def test_ablation_confusion_matrices_and_four_views_are_consistent() -> None:
    metrics = json.loads((EVAL_DIR / "modality_and_fusion_ablation_metrics.json").read_text(encoding="utf-8"))
    v1 = metrics["view1_train23_vs_no_train3_engine_separate"]
    v2 = metrics["view2_train23_vs_controls4"]
    v3 = metrics["view3_rail_vehicle24_vs_no_train3"]
    v4 = metrics["view4_horn13_vs_nohorn14"]

    # View 1: Front L1 vs F6 Multimodal Fusion
    front_l1 = v1["V2_Front_L1_Confirm2"]
    assert (front_l1["tp"], front_l1["fn"], front_l1["fp"], front_l1["tn"]) == (10, 13, 0, 3)
    assert front_l1["engine_001_detected"] is False

    # Back Confirm2 all classes vs side/rear filtered
    back_all = v1["V4_Back_Confirm2_AllClasses"]
    back_sr = v1["V5_Back_Confirm2_SideRear"]
    assert (back_all["tp"], back_all["fp"], back_all["engine_001_detected"]) == (9, 2, True)
    assert (back_sr["tp"], back_sr["fp"], back_sr["engine_001_detected"]) == (9, 0, False)

    # Dual-vision side/rear recovers event_002 and event_016 cleanly
    dual_sr = v1["V8_Dual_Vision_Confirm2_SideRear"]
    assert (dual_sr["tp"], dual_sr["fn"], dual_sr["fp"], dual_sr["tn"]) == (12, 11, 0, 3)
    assert dual_sr["events_gained_over_front_L1"] == ["train_events/event_002", "train_events/event_016"]

    # Default V3 B2/B4 advisory audio yields zero closure recall gain over Front L1
    f2_def = v1["F2_V3_Default_Front_L1_Advisory_Audio"]
    assert f2_def["tp"] == front_l1["tp"]
    assert f2_def["fp"] == front_l1["fp"]
    assert f2_def["events_gained_over_front_L1"] == []

    # Stateless union hits 23/23 recall at cost of 3/3 no-train false positives
    f1_union = v1["F1_Stateless_Union_FrontAny_Or_Audio037"]
    assert (f1_union["tp"], f1_union["fn"], f1_union["fp"], f1_union["tn"]) == (23, 0, 3, 0)

    # Full multimodal fusion (Front L1 OR Back SR L1 OR Audio 0.75 k=2) hits 15/23, 0/3 FP
    f6_mm = v1["F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2"]
    assert (f6_mm["tp"], f6_mm["fn"], f6_mm["fp"], f6_mm["tn"]) == (15, 8, 0, 3)
    assert f6_mm["engine_001_detected"] is False
    assert f6_mm["events_gained_over_front_L1"] == [
        "train_events/event_002",
        "train_events/event_005",
        "train_events/event_012",
        "train_events/event_016",
        "train_events/event_017",
    ]

    # Check View 2 (23 vs 4 controls) and View 3 (24 rail vehicles vs 3 no_train)
    assert v2["V4_Back_Confirm2_AllClasses"]["fp_engine"] == 1
    assert v2["V5_Back_Confirm2_SideRear"]["fp_engine"] == 0
    assert (v3["V4_Back_Confirm2_AllClasses"]["tp"], v3["V4_Back_Confirm2_AllClasses"]["fn"]) == (10, 14)
    assert (v3["F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2"]["tp"], v3["F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2"]["fn"]) == (15, 9)

    # Check View 4 (13 horn_present vs 14 horn_absent)
    a1_h = v4["A1_Audio_Frozen_037_k1"]
    a3_h = v4["A3_Audio_Hysteresis_075_k2"]
    assert (a1_h["tp"], a1_h["fn"], a1_h["fp"], a1_h["tn"]) == (12, 1, 13, 1)
    assert (a3_h["tp"], a3_h["fn"], a3_h["fp"], a3_h["tn"]) == (8, 5, 1, 13)


def test_side_and_sensor_scope_honesty_in_report() -> None:
    report = (EVAL_DIR / "COMPLETE_27_EVENT_MULTIMODAL_EXPERIMENT_REPORT.md").read_text(encoding="utf-8")
    assert "0/27" in report
    assert "CANNOT BE COMPUTED" in report
    assert "pre-db40305" in report
