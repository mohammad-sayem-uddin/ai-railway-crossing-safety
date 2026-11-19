"""Mission 13 deliverable & forensic finding contract tests (PROCESSED_DATA_ACCESS)."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = REPO_ROOT / "results" / "model_generalization_audit"


def test_mission13_report_figures_and_manifest_complete() -> None:
    report = REPO_ROOT / "docs" / "generated" / "MODEL_GENERALIZATION_AND_OVERFITTING_REPORT.md"
    assert report.is_file()
    txt = report.read_text(encoding="utf-8")
    assert "CompactTrainHornCNN" in txt
    assert "YOLOv8n" in txt
    assert "no_train_002" in txt

    manifest_path = REPO_ROOT / "docs/generated/professor_research_handover/HANDOVER_EVIDENCE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["artifact_count"] == 51
    assert manifest["mission13_model_generalization_audit_completed"] is True
    assert manifest["mission13_artifact_count"] == 23
    for entry in manifest["mission13_model_generalization_audit_artifacts"]:
        assert (REPO_ROOT / entry["path"]).is_file(), f"Missing M13 artifact: {entry['path']}"


def test_mission13_audio_audit_contracts() -> None:
    audio = json.loads((AUDIT_DIR / "audio_audit_summary.json").read_text(encoding="utf-8"))
    v3 = audio["frozen_v3_audit"]
    assert v3["checkpoint_sha256"] == "ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782"
    assert v3["val_037"]["f1"] > v3["test_037"]["f1"]
    assert v3["crossing_a_external"]["recording_26_tau_metrics"]["specificity"] == 0.0
    assert v3["leaked_vs_unseen_stem_positives"]["val"]["leaked_pos_wins_n"] == 51
    assert len(audio["learning_curve"]) == 5
    assert audio["learning_curve"][-1]["test_f1_mean"] > audio["learning_curve"][0]["test_f1_mean"]


def test_mission13_vision_leakage_and_clean_retrain_contracts() -> None:
    v39 = json.loads((AUDIT_DIR / "vision_baseline_39f402_audit.json").read_text(encoding="utf-8"))
    assert v39["frozen_checkpoint_sha256"] == "3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd"
    assert v39["training_history_summary"]["total_epochs_logged"] == 97

    splits = json.loads((AUDIT_DIR / "vision_split_leakage_comparison.json").read_text(encoding="utf-8"))
    assert splits["day_grouped"]["val"]["within_600s_of_train"] == 0
    assert splits["day_grouped"]["val"]["same_calendar_day_as_train"] == 0
    assert splits["day_grouped"]["test"]["within_600s_of_train"] == 0
    assert splits["day_grouped"]["test"]["same_calendar_day_as_train"] == 0

    clean39 = json.loads((AUDIT_DIR / "vision_39f402_on_clean_splits.json").read_text(encoding="utf-8"))["splits"]["best_ep93"]
    assert clean39["session_grouped_test_unseen_to_39f402"]["mAP50_95"] < clean39["session_grouped_test"]["mAP50_95"]
    assert clean39["day_grouped_test_unseen_to_39f402"]["mAP50_95"] < clean39["day_grouped_test"]["mAP50_95"]

    kaggle = json.loads((AUDIT_DIR / "vision_kaggle_clean_retrain_audit.json").read_text(encoding="utf-8"))["runs"]
    for rn in ("session_grouped_base", "day_grouped_base", "day_grouped_reg"):
        assert kaggle[rn]["epochs_ran"] == 100
    assert kaggle["day_grouped_reg"]["eval"]["best"]["test"]["mAP50_95"] > kaggle["day_grouped_base"]["eval"]["best"]["test"]["mAP50_95"]

    field = json.loads((AUDIT_DIR / "vision_clean_vs_frozen_field_diagnostics.json").read_text(encoding="utf-8"))
    assert field["day_grouped_test_264_conf035"]["day_grouped_reg"]["fp_035"] < field["day_grouped_test_264_conf035"]["day_grouped_base"]["fp_035"]
    for m_name in ("frozen_39f402", "session_grouped_base", "day_grouped_base", "day_grouped_reg"):
        assert field["crossing_a_upright_controls_and_engine_conf035"][m_name]["no_train_events/event_002_front"]["det_frames_conf035"] >= 59
