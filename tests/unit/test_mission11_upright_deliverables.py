"""Verification tests for Mission 11 completed 27-event upright multimodal deliverables."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "results" / "upright_inference_v2" / "UPRIGHT_INFERENCE_MANIFEST.json"
EVAL_DIR = REPO_ROOT / "results" / "upright_27_event_evaluation"
FIG_DIR = REPO_ROOT / "docs" / "generated" / "figures"
HANDOVER_MANIFEST = REPO_ROOT / "docs" / "generated" / "professor_research_handover" / "HANDOVER_EVIDENCE_MANIFEST.json"


def test_upright_inference_manifest_covers_all_54_verified_streams() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["execution_status"] == "SUCCESS"
    assert manifest["errors"] == []
    assert manifest["orientation_policy"] == "orthogonal_display_matrix_rotation_v1"
    assert manifest["apply_display_rotation"] is True
    assert manifest["timestamp_basis"] == "source_pts"
    assert manifest["authorization"]["authorization_id"] == "AUTH-MEDIA-ACCESS-20261119-MISSION10"

    events = manifest["events"]
    assert len(events) == 27

    rot_counts = {-90: 0, 0: 0}
    for ent in events:
        assert ent["execution_status"] == "SUCCESS"
        assert ent["errors"] == []
        assert ent["source_media"]["front_sha256_verified_against_inventory"] is True
        assert ent["source_media"]["back_sha256_verified_against_inventory"] is True
        for cam_key in ("front_orientation", "back_orientation"):
            ori = ent[cam_key]
            assert ori["orientation_verified"] is True
            assert ori["image_coordinate_basis"] == ["orthogonal_display_matrix_rotation_v1"]
            rot = int(ori["expected_quicktime_rotation_deg"])
            assert ori["display_rotation_degrees_observed"] == [rot]
            rot_counts[rot] += 1
        for path_key, sha_key in (
            ("front_path", "front_sha256"),
            ("back_path", "back_sha256"),
            ("audio_path", "audio_sha256"),
        ):
            payload_text = (REPO_ROOT / ent[path_key]).read_text(encoding="utf-8")
            assert hashlib.sha256(payload_text.encode("utf-8")).hexdigest() == ent[sha_key]

    assert rot_counts == {-90: 44, 0: 10}


def test_upright_evaluation_comparison_quorum_and_forensics() -> None:
    comp = json.loads((EVAL_DIR / "baseline_vs_upright_comparison.json").read_text(encoding="utf-8"))
    assert comp["streams_verified_count"] == 54
    assert comp["total_streams"] == 54
    assert comp["audio_invariance"]["n_events"] == 27
    assert comp["audio_invariance"]["max_abs_score_diff_across_all_windows"] == 0.0

    by_cfg = {c["configuration"]: c for c in comp["config_comparison"]}
    assert (by_cfg["V2_Front_L1_Confirm2"]["baseline_tp"], by_cfg["V2_Front_L1_Confirm2"]["upright_tp"], by_cfg["V2_Front_L1_Confirm2"]["upright_fp_no_train"]) == (10, 23, 1)
    assert (by_cfg["V5_Back_Confirm2_SideRear"]["baseline_tp"], by_cfg["V5_Back_Confirm2_SideRear"]["upright_tp"], by_cfg["V5_Back_Confirm2_SideRear"]["upright_fp_no_train"]) == (9, 23, 0)
    assert (by_cfg["F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2"]["baseline_tp"], by_cfg["F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2"]["upright_tp"], by_cfg["F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2"]["upright_fp_no_train"]) == (15, 23, 1)
    assert (by_cfg["F7_Exploratory_2of3_Multimodal"]["baseline_tp"], by_cfg["F7_Exploratory_2of3_Multimodal"]["upright_tp"], by_cfg["F7_Exploratory_2of3_Multimodal"]["upright_fp_no_train"]) == (17, 23, 1)
    assert by_cfg["V2_Front_L1_Confirm2"]["upright_engine_001"] is True
    assert by_cfg["V5_Back_Confirm2_SideRear"]["upright_engine_001"] is False

    q8 = comp["exploratory_quorum_comparison"]["F8_Exploratory_Strong_2of3_Quorum"]
    assert (q8["baseline"]["tp"], q8["upright"]["tp"], q8["upright"]["fp_no_train"]) == (10, 23, 0)
    assert q8["upright"]["engine_001_detected"] is False
    assert q8["upright"]["f1"] == 1.0
    assert q8["causal_quorum_timing_summary"]["f8_pre_T2_confirm"] == 11
    assert q8["causal_quorum_timing_summary"]["v2_pre_T2_confirm"] == 22

    m2 = comp["upright_m2_departure_summary"]
    assert m2["n_events_with_T4_and_back_det"] == 22
    assert m2["non_premature_count"] == 20

    forensics = json.loads((EVAL_DIR / "failed_events_forensic_diagnosis.json").read_text(encoding="utf-8"))
    assert forensics["missed_f6_count"] == 0
    assert forensics["missed_f6_event_ids"] == []


def test_authoritative_27_event_table_figures_and_handover_manifest() -> None:
    with (EVAL_DIR / "authoritative_27_event_results_table.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 27
    cohorts = [r["cohort"] for r in rows]
    assert cohorts.count("train_events") == 23
    assert cohorts.count("no_train_events") == 3
    assert cohorts.count("engine_events") == 1
    assert all(r["reference_label_provenance"] == "RESEARCHER_ADOPTED_AI_ASSISTED_UNREVIEWED_STAGE21" for r in rows)

    by_id = {r["event_id"]: r for r in rows}
    assert by_id["no_train_events/event_002"]["class_F6_train23_vs_nt3"] == "FP"
    assert by_id["no_train_events/event_002"]["class_F8_quorum_train23_vs_nt3"] == "TN"
    assert by_id["engine_events/event_001"]["class_F6_train23_vs_nt3"] == "ENGINE_DETECTED"
    assert by_id["engine_events/event_001"]["class_F8_quorum_train23_vs_nt3"] == "ENGINE_MISSED"

    for fname in (
        "fig16_upright_vs_baseline_ablation.png",
        "fig17_upright_event_recovery_and_fsm_timing.png",
    ):
        fpath = FIG_DIR / fname
        assert fpath.is_file() and fpath.stat().st_size > 10_000

    hm = json.loads(HANDOVER_MANIFEST.read_text(encoding="utf-8"))
    assert hm["artifact_count"] == 51
    assert hm["mission11_raw_media_accessed"] is True
    assert hm["mission11_authorization_id"] == "AUTH-MEDIA-ACCESS-20261119-MISSION10"
    assert len(hm["upright_27_event_experiment_artifacts"]) >= 17
