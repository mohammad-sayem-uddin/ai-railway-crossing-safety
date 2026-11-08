"""Phase 11.5: tests for the field-level adjudication record module.
Synthetic fixtures only; never touches data/ground_truth/."""

from __future__ import annotations

import pytest

from railway_detection.annotation.phase11_5_adjudication import (
    FIELD_ADJUDICATION_STATUSES,
    FieldAdjudicationRecord,
)


def _record(**overrides) -> FieldAdjudicationRecord:
    base = dict(
        adjudication_id="adj_test_001",
        event_id="train_events/event_999",
        boundary="T0_first_visible",
        source_video_path="data/raw/layer_b/v2/train_events/event_999/camera_front.mov",
        source_video_sha256="a" * 64,
        legacy_proposal_file="data/ground_truth/proposals/train_events/event_999_proposal_v2.json",
        legacy_proposal_version="2",
        legacy_claimed_value_s=1.5,
        legacy_claimed_classification="NOT_LEFT_CENSORED",
        legacy_claimed_rationale="locomotive nose appears at Frame 45 (t=1.50s)",
        phase_11_4_finding_outcome="VERIFIED_DISCREPANCY",
        phase_11_4_finding_evidence="train visible at t=0.0s",
    )
    base.update(overrides)
    return FieldAdjudicationRecord(**base)


def test_valid_status_accepted() -> None:
    r = _record(current_status="FLAGGED_BY_AUDIT")
    assert r.current_status == "FLAGGED_BY_AUDIT"


def test_invalid_status_rejected() -> None:
    with pytest.raises(ValueError):
        _record(current_status="APPROVED")  # a Stage-2.1 status, not a valid field-adjudication status


def test_append_event_is_additive_not_destructive() -> None:
    r = _record()
    r.append_event(by="phase_11_4_video_audit", status="FLAGGED_BY_AUDIT")
    r.append_event(by="researcher@example.com", status="RESEARCHER_CONFIRMED_CORRECTION")
    assert len(r.adjudication_history) == 2
    assert r.adjudication_history[0].status == "FLAGGED_BY_AUDIT"
    assert r.adjudication_history[1].status == "RESEARCHER_CONFIRMED_CORRECTION"
    assert r.current_status == "RESEARCHER_CONFIRMED_CORRECTION"


def test_history_entry_rejects_invalid_status() -> None:
    r = _record()
    with pytest.raises(ValueError):
        r.append_event(by="x", status="NOT_A_REAL_STATUS")


def test_to_dict_never_modifies_legacy_proposal_fields() -> None:
    r = _record()
    r.append_event(by="researcher@example.com", status="RESEARCHER_CONFIRMED_CORRECTION")
    d = r.to_dict()
    assert d["legacy_claimed_value_s"] == 1.5
    assert d["legacy_claimed_classification"] == "NOT_LEFT_CENSORED"
    assert "NOT constitute formal invalidation" in d["legacy_record_disposition_note"]


def test_field_adjudication_statuses_distinct_from_stage21_statuses() -> None:
    """Confirms this module's status vocabulary is deliberately separate
    from stage2_1_schema.py's record-level ADJUDICATION_STATUSES -- a
    field-level correction is never mislabeled as a full-record APPROVED or
    REJECTED. 'DISPUTED' is the one deliberate, shared term (the Phase 11.5
    brief explicitly asked for "the repository's supported terminology" for
    marking a prior classification as contested), reused on purpose, not by
    accident."""
    from railway_detection.annotation.stage2_1_schema import ADJUDICATION_STATUSES

    assert "APPROVED" not in FIELD_ADJUDICATION_STATUSES
    assert "REJECTED" not in FIELD_ADJUDICATION_STATUSES
    assert "NEEDS_SECOND_REVIEW" not in FIELD_ADJUDICATION_STATUSES
    assert "DISPUTED" in FIELD_ADJUDICATION_STATUSES and "DISPUTED" in ADJUDICATION_STATUSES
