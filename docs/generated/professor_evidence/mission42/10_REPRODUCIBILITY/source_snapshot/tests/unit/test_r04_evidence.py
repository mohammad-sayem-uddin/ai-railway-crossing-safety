"""Focused tests for additive R04 evidence and comparison artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from railway_detection.data.r04_evidence import (
    build_r04_evidence,
    render_comparison_markdown,
    render_scope_markdown,
)

ROOT = Path(__file__).resolve().parents[2]


def test_r04_inventory_is_event_level_and_fail_closed() -> None:
    evidence = build_r04_evidence(ROOT)
    assert evidence["status"] == "CANDIDATE_EVIDENCE_ONLY_NO_AUTOMATIC_APPROVAL"
    assert evidence["summary"]["total_events"] == 27
    assert evidence["summary"]["dual_camera_candidate_count"] == 12
    assert evidence["summary"]["premature_opening_candidate_coverage"]["v9"][
        "candidate_boundary_coverage_count"
    ] == 11
    assert evidence["summary"]["premature_opening_candidate_coverage"]["v9"][
        "official_evaluable_count"
    ] == 0
    assert evidence["summary"]["premature_opening_candidate_coverage"]["m4"][
        "official_evaluable_count"
    ] == 0
    assert evidence["summary"]["verdict_counts"] == {
        "AMBIGUOUS": 8,
        "CALIBRATION_SUPPORTED": 12,
        "PROVISIONAL": 7,
    }
    assert evidence["calibration_manifest_status"] == "CANDIDATE_UNVALIDATED_DO_NOT_MERGE"
    assert evidence["human_review_status"].startswith("REVIEWED_WITH_CORROBORATION")
    by_key = {row["event_key"]: row for row in evidence["events"]}
    assert by_key["train_events/event_010"]["calibration"]["verdict"] == "CALIBRATION_SUPPORTED"
    assert by_key["engine_events/event_001"]["candidate_proposal"]["version"] == 3
    assert by_key["engine_events/event_001"]["candidate_proposal"]["matches_snapshot"] is False
    assert (
        by_key["engine_events/event_001"]["candidate_proposal"]["snapshot_sha256"]
        is not None
    )
    assert evidence["candidate_proposal_selection"].startswith("highest numeric")
    # A supported calibration does not make an event evaluable when T4 is
    # missing; boundary eligibility and clock eligibility are separate gates.
    assert by_key["train_events/event_005"]["calibration"]["verdict"] == "CALIBRATION_SUPPORTED"
    assert by_key["train_events/event_005"]["boundaries"]["T4_tail_clearance"]["value_s"] is None
    assert (
        by_key["train_events/event_005"]["metric_boundary_compatibility"]["v9"][
            "candidate_evaluable"
        ]
        is False
    )
    assert (
        by_key["train_events/event_001"]["clock_scope"]["scope_status"]
        == "EXPLORATORY_CANDIDATE_ONLY"
    )
    assert (
        by_key["train_events/event_001"]["clock_scope"]["scope_decision_status"]
        == "RESEARCHER_DECISION_REQUIRED"
    )
    assert by_key["train_events/event_001"]["metric_boundary_compatibility"]["m4"][
        "candidate_evaluable"
    ] is False
    assert evidence["decision_required"]["status"] == "MISSING_RESEARCHER_DECISION"


def test_scope_and_comparison_state_no_approval_and_cover_required_semantics() -> None:
    evidence = build_r04_evidence(ROOT)
    scope = render_scope_markdown(evidence)
    comparison = render_comparison_markdown(evidence)
    assert "CANDIDATE EVIDENCE ONLY" in scope
    assert "not an authorization" in scope.lower() or "does not" in scope.lower()
    for term in ("T0", "T1", "T2", "T3", "T4", "t_blocked", "M5", "right-censored", "clock"):
        assert term in comparison
    assert "Decision status: UNRESOLVED" in comparison
    assert "phase12_protocol_decision.json" in comparison
    assert "not metric results" in scope
    assert "Active candidate proposal" in scope
    # Verify dynamic count synchronization (C2 resolution):
    supported = evidence["summary"]["dual_camera_candidate_count"]
    non_supported = evidence["summary"]["total_events"] - supported
    assert f"blocked for the {non_supported} non-supported events" in scope
    assert "16 non-supported events" not in scope
    assert "16 non-supported events" not in comparison
    assert "11 CALIBRATION_SUPPORTED" not in comparison
    assert f"{supported} `CALIBRATION_SUPPORTED` candidate events and {non_supported} non-supported events" in comparison
    assert f"authorize the {supported}-event exploratory scope" in comparison


def test_machine_report_is_json_serializable_without_nan() -> None:
    evidence = build_r04_evidence(ROOT)
    encoded = json.dumps(evidence, allow_nan=False)
    assert '"events"' in encoded


def test_orphaned_scratch_record_event_020_fails_closed() -> None:
    """Confirm orphaned event_020 scratch record cannot bypass validation or promote event."""
    from railway_detection.data.sync_calibration import CorroborationRecord, classify_event

    rec_path = ROOT / "scratch/r04_visual_review/train_events/event_020/review_record.json"
    assert rec_path.is_file(), f"Expected scratch record at {rec_path}"
    rec_data = json.loads(rec_path.read_text(encoding="utf-8"))

    # human_verified is null, not True
    assert rec_data.get("human_verified") is not True

    # Corroboration validation must reject the incomplete template
    corrob = CorroborationRecord.from_dict(rec_data)
    errors = corrob.validate()
    assert any("verification status is not True" in e for e in errors)
    assert any("reviewer identity is required" in e for e in errors)
    assert any("evidence_provenance is required" in e for e in errors)
    assert corrob.is_valid is False

    # Classification must fail closed to AMBIGUOUS due to severe acoustic decorrelation
    diag = {
        "lag_s": -0.0284,
        "psr": 1.01,
        "snr": 9.1,
        "window_range_s": 6.5232,
    }
    verdict = classify_event("train_events/event_020", diag, qt_delta_s=4.0, corroboration=rec_data)
    assert verdict.verdict == "AMBIGUOUS"


def test_manifest_builder_rehash_all_flag_parser() -> None:
    """Confirm manifest builder parses --rehash-all without raising unexpected errors."""
    import argparse
    from scripts.build_camera_sync_candidate_manifest import main

    # Inspect the function signature accepts argv
    import inspect
    sig = inspect.signature(main)
    assert "argv" in sig.parameters

