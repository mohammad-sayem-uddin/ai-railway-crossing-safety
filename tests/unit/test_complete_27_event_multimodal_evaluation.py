"""Verification tests for Mission 9 27-event multimodal evaluation, causal FSM fusion & forensics."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.decision_engine_v3_four_layer import (
    MultimodalDecisionEngineV3FourLayer,
)
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.safety import media_guard

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO_ROOT / "results" / "multimodal_27_event_evaluation"
READY_TEMPLATE = (
    REPO_ROOT / "docs" / "generated" / "human_approval_templates" / "AUTH_MEDIA_ACCESS_MISSION9_READY.json"
)


def test_complete_27_event_multimodal_outputs_exist_and_cover_all_cohorts() -> None:
    required_files = [
        EVAL_DIR / "event_by_event_27_multimodal_evaluation.csv",
        EVAL_DIR / "event_by_event_27_multimodal_evaluation.json",
        EVAL_DIR / "modality_and_fusion_ablation_metrics.csv",
        EVAL_DIR / "modality_and_fusion_ablation_metrics.json",
        EVAL_DIR / "causal_fsm_gate_timing_summary.csv",
        EVAL_DIR / "causal_fsm_gate_timing_summary.json",
        EVAL_DIR / "failed_events_forensic_diagnosis.json",
        EVAL_DIR / "COMPLETE_27_EVENT_MULTIMODAL_EXPERIMENT_REPORT.md",
        READY_TEMPLATE,
    ]
    for path in required_files:
        assert path.exists(), f"Missing artifact: {path}"
        assert path.stat().st_size > 0, f"Empty artifact: {path}"

    with open(EVAL_DIR / "event_by_event_27_multimodal_evaluation.csv", encoding="utf-8", newline="") as handle:
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
    assert metrics["learned_fusion_model_present"] is False
    assert metrics["all_fusion_rules_type"] == "RULE_BASED_LATE_FUSION"

    v1 = metrics["view1_train23_vs_no_train3_engine_separate"]
    v2 = metrics["view2_train23_vs_controls4"]
    v3 = metrics["view3_rail_vehicle24_vs_no_train3"]
    v4 = metrics["view4_horn13_vs_nohorn14"]

    front_l1 = v1["V2_Front_L1_Confirm2"]
    assert (front_l1["tp"], front_l1["fn"], front_l1["fp"], front_l1["tn"]) == (10, 13, 0, 3)
    assert front_l1["engine_001_detected"] is False

    back_all = v1["V4_Back_Confirm2_AllClasses"]
    back_sr = v1["V5_Back_Confirm2_SideRear"]
    assert (back_all["tp"], back_all["fp"], back_all["engine_001_detected"]) == (9, 2, True)
    assert (back_sr["tp"], back_sr["fp"], back_sr["engine_001_detected"]) == (9, 0, False)

    dual_sr = v1["V8_Dual_Vision_Confirm2_SideRear"]
    assert (dual_sr["tp"], dual_sr["fn"], dual_sr["fp"], dual_sr["tn"]) == (12, 11, 0, 3)
    assert dual_sr["events_gained_over_front_L1"] == ["train_events/event_002", "train_events/event_016"]

    f2_def = v1["F2_V3_Default_Front_L1_Advisory_Audio"]
    assert f2_def["tp"] == front_l1["tp"]
    assert f2_def["fp"] == front_l1["fp"]

    f1_union = v1["F1_Stateless_Union_FrontAny_Or_Audio037"]
    assert (f1_union["tp"], f1_union["fn"], f1_union["fp"], f1_union["tn"]) == (23, 0, 3, 0)

    f6_mm = v1["F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2"]
    assert (f6_mm["tp"], f6_mm["fn"], f6_mm["fp"], f6_mm["tn"]) == (15, 8, 0, 3)
    assert f6_mm["events_gained_over_front_L1"] == [
        "train_events/event_002",
        "train_events/event_005",
        "train_events/event_012",
        "train_events/event_016",
        "train_events/event_017",
    ]

    f7_mm = v1["F7_Exploratory_2of3_Multimodal"]
    assert (f7_mm["tp"], f7_mm["fn"], f7_mm["fp"], f7_mm["tn"]) == (17, 6, 0, 3)

    assert v2["V4_Back_Confirm2_AllClasses"]["fp_engine"] == 1
    assert v2["V5_Back_Confirm2_SideRear"]["fp_engine"] == 0
    assert (v3["V4_Back_Confirm2_AllClasses"]["tp"], v3["V4_Back_Confirm2_AllClasses"]["fn"]) == (10, 14)
    assert (v3["F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2"]["tp"], v3["F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2"]["fn"]) == (15, 9)

    a1_h = v4["A1_Audio_Frozen_037_k1"]
    a3_h = v4["A3_Audio_Hysteresis_075_k2"]
    assert (a1_h["tp"], a1_h["fn"], a1_h["fp"], a1_h["tn"]) == (12, 1, 13, 1)
    assert (a3_h["tp"], a3_h["fn"], a3_h["fp"], a3_h["tn"]) == (8, 5, 1, 13)


def test_causal_fsm_gate_timing_and_forensic_diagnosis() -> None:
    fsm_data = json.loads((EVAL_DIR / "causal_fsm_gate_timing_summary.json").read_text(encoding="utf-8"))
    s = fsm_data["summaries"]

    assert s["FSM_V2_Front_L1"]["train_triggers"] == 10
    assert s["FSM_V2_Front_L1"]["train_full_closures"] == 9
    assert s["FSM_V2_Front_L1"]["train_warning_eof_never_closed"] == 1
    assert s["FSM_V2_Front_L1"]["train_pre_T2_warning"] == 4
    assert s["FSM_V2_Front_L1"]["train_pre_T2_close_cmd"] == 3
    assert s["FSM_V2_Front_L1"]["train_pre_T2_full_closure"] == 0
    assert s["FSM_V2_Front_L1"]["complete_close_reopen_cycles"] == 0

    assert s["FSM_F4_Front_Or_Audio075k2"]["train_triggers"] == 14
    assert s["FSM_F4_Front_Or_Audio075k2"]["train_full_closures"] == 13
    assert s["FSM_F4_Front_Or_Audio075k2"]["no_train_false_closures"] == 0

    assert s["FSM_F6_Full_MM_Sync11"]["train_triggers"] == 8
    assert s["FSM_F6_Full_MM_Sync11"]["train_full_closures"] == 8

    assert s["FSM_F6_Full_MM_Bounded27"]["train_triggers"] == 15
    assert s["FSM_F6_Full_MM_Bounded27"]["train_full_closures"] == 15
    assert s["FSM_F6_Full_MM_Bounded27"]["no_train_false_closures"] == 0
    assert s["FSM_F6_Full_MM_Bounded27"]["engine_001_triggered"] is False
    assert s["FSM_F6_Full_MM_Bounded27"]["complete_close_reopen_cycles"] == 0

    assert s["FSM_F7_Exploratory_2of3_Bounded27"]["train_triggers"] == 17
    assert s["FSM_F7_Exploratory_2of3_Bounded27"]["train_full_closures"] == 17
    assert s["FSM_F7_Exploratory_2of3_Bounded27"]["train_pre_T2_warning"] == 8
    assert s["FSM_F7_Exploratory_2of3_Bounded27"]["no_train_false_closures"] == 0

    forensics = json.loads((EVAL_DIR / "failed_events_forensic_diagnosis.json").read_text(encoding="utf-8"))
    assert forensics["missed_f6_count"] == 8
    assert forensics["orientation_finding"]["all_8_missed_front_minus90_deg"] is True
    assert forensics["orientation_finding"]["all_8_missed_back_minus90_deg"] is True


def test_ready_auth_template_validates_without_granting_canonical_access(tmp_path: Path) -> None:
    # Clone non-raw governance metadata into an isolated temporary repository without canonical AUTH-MEDIA-ACCESS.json
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "data/ground_truth").mkdir(parents=True)
    (tmp_path / "data/governance").mkdir(parents=True)
    (tmp_path / "data/raw/layer_b/v2/train_events/event_001").mkdir(parents=True)
    for rel in (
        "configs/frozen_experiment_v1.yaml",
        "docs/FINAL_GROUND_TRUTH_PROTOCOL.md",
        "data/ground_truth/authorized_reviewers.json",
    ):
        (tmp_path / rel).write_text((REPO_ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8")

    payload = json.loads(READY_TEMPLATE.read_text(encoding="utf-8"))
    media_guard._validate_payload(
        tmp_path,
        payload,
        operation="INFERENCE",
        media_path=tmp_path / "data/raw/layer_b/v2/train_events/event_001/camera_front.mov",
        event_id="train_events/event_001",
        now=datetime.now(UTC),
    )

    # Presence of the template alone must STILL fail closed when canonical AUTH-MEDIA-ACCESS.json is absent.
    try:
        media_guard.verify_authorization_record(
            tmp_path,
            operation="INFERENCE",
            media_path=tmp_path / "data/raw/layer_b/v2/train_events/event_001/camera_front.mov",
            event_id="train_events/event_001",
            now=datetime.now(UTC),
        )
    except media_guard.MediaAccessAuthorizationError as exc:
        assert exc.code == "AUTH_MEDIA_ACCESS_NOT_GRANTED"
    else:
        raise AssertionError("Expected isolated repo without AUTH-MEDIA-ACCESS.json to fail closed")


def test_v3_engine_opt_in_causal_fusion_triggers_deduplicate_audio_and_bridge_gaps() -> None:
    eng = MultimodalDecisionEngineV3FourLayer(
        enable_audio_hysteresis_wakeup=True,
        enable_back_side_rear_approach_backup=True,
        max_approach_inter_frame_gap_s=0.45,
    )
    # Single audio window repeated on two consecutive 0.2s ticks must NOT trigger hysteresis k=2
    win0 = EvidenceRecord(
        timestamp_s=1.0,
        source_id="audio_1",
        modality=Modality.AUDIO,
        available=True,
        detections=(Detection(label="train_horn", confidence=0.85, metadata={"window_index": 0}),),
        metadata={"window_index": 0},
    )
    for ts in (1.0, 1.2, 1.4):
        rec = eng.evaluate_frame(
            MultimodalFrame(master_timestamp_s=ts, vision_records=(), audio_records=(win0,))
        )
        assert rec.resulting_state == "IDLE"

    # Second distinct window_index=1 >= 0.75 triggers WARNING cleanly
    win1 = EvidenceRecord(
        timestamp_s=1.5,
        source_id="audio_1",
        modality=Modality.AUDIO,
        available=True,
        detections=(Detection(label="train_horn", confidence=0.88, metadata={"window_index": 1}),),
        metadata={"window_index": 1},
    )
    rec2 = eng.evaluate_frame(
        MultimodalFrame(master_timestamp_s=1.6, vision_records=(), audio_records=(win1,))
    )
    assert rec2.resulting_state == "WARNING"
    assert eng.timing_trace["engine_trigger_s"] == 1.6


def test_mission12_analysis_deliverable_invariants_and_honesty() -> None:
    """Mission 12 analysis JSON and manifest preserve provenance labels, horizon limits, and zero fake reviews."""
    m12_path = REPO_ROOT / "results" / "upright_27_event_evaluation" / "mission12_scientific_analysis.json"
    manifest_path = REPO_ROOT / "docs" / "generated" / "professor_research_handover" / "HANDOVER_EVIDENCE_MANIFEST.json"
    m12 = json.loads(m12_path.read_text(encoding="utf-8"))
    rec = m12["priority5_and_6_reconciliation"]
    assert rec["streams_verified"] == "54/54"
    assert rec["active_stage21_human_reviews_count"] == 0
    assert rec["official_phase12_ready"] is False
    assert rec["audio_log_scale_and_eps_parity"]["log_scale"] == "natural"
    assert rec["audio_log_scale_and_eps_parity"]["log_epsilon"] == 1e-10
    assert rec["gate_timing_recording_horizon_audit"]["reopening_cycles_completed"] == 0
    assert rec["gate_timing_recording_horizon_audit"]["occupancy_sensors_installed"] == 0

    stress = m12["priority4_synthetic_perturbation_stress"]
    assert "SYNTHETIC_PERTURBATION_STRESS_TEST" in stress["provenance"]
    assert "EXPLORATORY_POST_HOC_MITIGATION" in m12["priority2_no_train_002_forensics"]["in_sample_caution"]

    abl = m12["priority3_and_4_rule_comparison"]["ablation_matrix"]
    assert abl["pred_F10_TrackROI_Or_RailBack_Or_Audio"]["view3_rail24_vs_nt3"]["tp"] == 24
    assert abl["pred_F10_TrackROI_Or_RailBack_Or_Audio"]["view3_rail24_vs_nt3"]["fp"] == 0
    assert abl["pred_F11_RailVehicle_2of3_RawFront"]["view3_rail24_vs_nt3"]["tp"] == 24
    assert abl["pred_F11_RailVehicle_2of3_RawFront"]["view3_rail24_vs_nt3"]["fp"] == 0

    hm = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert hm["artifact_count"] == 51
    assert len(hm["artifacts"]) == 51
    assert hm["mission12_scientific_handover_completed"] is True
