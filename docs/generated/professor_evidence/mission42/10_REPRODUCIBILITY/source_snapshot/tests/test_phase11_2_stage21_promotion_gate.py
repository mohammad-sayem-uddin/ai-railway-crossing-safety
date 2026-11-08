"""Phase 11.2: tests for the Stage-2.1 schema and the fail-closed promotion
gate. Every fixture is synthetic, constructed in this file or in tmp_path.
No test reads, writes, or modifies any file under `data/ground_truth/`.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, UTC
from pathlib import Path

import pytest

from railway_detection.annotation.promotion_gate import (
    PromotionRejected,
    promote_record,
    propose_invalidation,
    validate_batch_for_promotion,
    validate_for_promotion,
    write_invalidation_proposal,
)
from railway_detection.annotation.schemas import SchemaValidationError
from railway_detection.annotation.stage2_1_schema import (
    STAGE_2_1_SCHEMA_VERSION,
    Stage21ReviewRecord,
    build_stage2_1_record_from_dict,
)

VALID_PROPOSAL_SHA = "a" * 64
VALID_MEDIA_FRONT_SHA = "b" * 64
VALID_MEDIA_BACK_SHA = "c" * 64

T0 = datetime(2026, 11, 1, 14, 0, 0, tzinfo=UTC)
T_START = T0.isoformat().replace("+00:00", "Z")
T_END = (T0 + timedelta(seconds=600)).isoformat().replace("+00:00", "Z")
T_ATTEST = (T0 + timedelta(seconds=601)).isoformat().replace("+00:00", "Z")


def _valid_boundary_set() -> dict:
    return {
        "T0_first_visible": {"state": "OBSERVABLE", "rationale": "Visible at frame 0", "value_s": 0.0, "reference_camera": "front"},
        "T1_danger_zone_entry": {"state": "OBSERVABLE", "rationale": "Cowcatcher at landmark", "value_s": 5.8, "reference_camera": "front"},
        "T2_crossing_occupancy_start": {"state": "OBSERVABLE", "rationale": "Pilot crosses plane", "value_s": 6.5, "reference_camera": "front"},
        "T3_locomotive_unit_clearance": {"state": "OBSERVABLE", "rationale": "Rear coupler clears", "value_s": 3.6, "reference_camera": "back"},
        "T4_tail_clearance": {"state": "OBSERVABLE", "rationale": "Final coach clears", "value_s": 45.0, "reference_camera": "back"},
        "T_scene_clear": {"state": "CENSORED", "rationale": "Recording ends while train still visible", "value_s": None, "reference_camera": None},
    }


def _valid_record_dict(event_id: str = "event_001", **overrides) -> dict:
    base = {
        "schema_version": STAGE_2_1_SCHEMA_VERSION,
        "review_id": f"review_{event_id}_v2_20261101",
        "event_id": event_id,
        "cohort": "train_events",
        "proposal_reference": {
            "proposal_file": f"data/ground_truth/proposals/train_events/{event_id}_proposal_v6.json",
            "proposal_sha256": VALID_PROPOSAL_SHA,
        },
        "reviewer_metadata": {
            "reviewer_id": "jane_doe_researcher",
            "review_session_id": "session-2026-11-01-001",
            "review_start_utc": T_START,
            "review_end_utc": T_END,
            "inspection_tool": "ffmpeg frame-by-frame + scipy spectral audit, manual",
        },
        "model_independence_attestation": {
            "attested": True,
            "statement": "I reviewed only the raw video/audio and did not consult any model prediction.",
            "attested_at_utc": T_ATTEST,
        },
        "reviewer_observed_media_hashes": {
            "front_sha256": VALID_MEDIA_FRONT_SHA,
            "back_sha256": VALID_MEDIA_BACK_SHA,
            "observed_at_utc": T_START,
        },
        "boundary_adjudications": _valid_boundary_set(),
        "adjudication_status": "APPROVED",
        "adjudication_history": [
            {"event": "created", "by": "jane_doe_researcher", "at_utc": T_END, "status_set": "APPROVED"},
        ],
    }
    base.update(overrides)
    return base


def _active_proposal_map(event_id: str = "event_001", sha: str = VALID_PROPOSAL_SHA) -> dict:
    return {event_id: sha}


def _media_registry(event_id: str = "event_001") -> dict:
    return {event_id: {"front": VALID_MEDIA_FRONT_SHA, "back": VALID_MEDIA_BACK_SHA}}


def _authorized_reviewers() -> frozenset[str]:
    """Phase 11.7: matches `_valid_record_dict`'s default reviewer_id, so
    tests concerned with something else don't also have to think about the
    allowlist check."""
    return frozenset({"jane_doe_researcher"})


def _bogus_media_file_paths(event_id: str = "event_001") -> dict:
    """Phase 11.7: deliberately NON-existent paths. Safe to use in any test
    whose assertions check for a SPECIFIC violation code via `in`/`any(...)`
    rather than an exact violation count or list -- those tests don't care
    that this also adds MISSING_MEDIA_FILE_PATHS/MEDIA_FILE_MISSING-shaped
    noise, and several of them return early (legacy schema / invalidation
    marker / schema validation failure) before ever reaching the media
    re-verification step at all."""
    return {event_id: {"front": "/nonexistent/front.mov", "back": "/nonexistent/back.mov"}}


def _create_synthetic_media_files(tmp_path: Path, event_id: str = "event_001") -> dict:
    """Creates real, distinct synthetic files and returns both their real
    paths and real SHA-256 hashes, for the tests that need Decision 4's
    LIVE re-hash to genuinely succeed end-to-end, not merely be mocked."""
    front = tmp_path / f"{event_id}_front.mov"
    back = tmp_path / f"{event_id}_back.mov"
    front.write_bytes(f"synthetic front camera content for {event_id}".encode())
    back.write_bytes(f"synthetic back camera content for {event_id}".encode())
    return {
        "paths": {"front": str(front), "back": str(back)},
        "hashes": {
            "front": hashlib.sha256(front.read_bytes()).hexdigest(),
            "back": hashlib.sha256(back.read_bytes()).hexdigest(),
        },
    }


# --- Completion criterion 1: valid synthetic records pass -----------------


def test_valid_stage2_1_record_builds_successfully() -> None:
    record = build_stage2_1_record_from_dict(_valid_record_dict())
    assert isinstance(record, Stage21ReviewRecord)
    assert record.is_resolved
    assert record.reviewer_metadata.review_duration_s == 600.0


def test_valid_record_passes_promotion_validation(tmp_path: Path) -> None:
    media = _create_synthetic_media_files(tmp_path)
    record = _valid_record_dict(reviewer_observed_media_hashes={
        "front_sha256": media["hashes"]["front"], "back_sha256": media["hashes"]["back"],
        "observed_at_utc": T_START,
    })
    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event=_active_proposal_map(),
        media_sha256_registry={"event_001": media["hashes"]},
        authorized_reviewers=_authorized_reviewers(),
        media_file_paths={"event_001": media["paths"]},
    )
    assert violations == []


def test_valid_record_can_be_promoted(tmp_path: Path) -> None:
    media = _create_synthetic_media_files(tmp_path)
    record = _valid_record_dict(reviewer_observed_media_hashes={
        "front_sha256": media["hashes"]["front"], "back_sha256": media["hashes"]["back"],
        "observed_at_utc": T_START,
    })
    out_path = promote_record(
        record, output_dir=tmp_path / "stage3_sandbox",
        active_proposal_sha256_by_event=_active_proposal_map(),
        media_sha256_registry={"event_001": media["hashes"]},
        authorized_reviewers=_authorized_reviewers(),
        media_file_paths={"event_001": media["paths"]},
    )
    assert out_path.exists()
    assert json.loads(out_path.read_text())["event_id"] == "event_001"


# --- Completion criterion 2: legacy/incomplete records fail closed --------


def test_legacy_schema_version_rejected_outright() -> None:
    record = _valid_record_dict(**{"schema_version": "7.0.0"})
    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event=_active_proposal_map(), media_sha256_registry=_media_registry(),
        authorized_reviewers=_authorized_reviewers(), media_file_paths=_bogus_media_file_paths(),
    )
    assert len(violations) == 1
    assert violations[0].code == "LEGACY_OR_UNKNOWN_SCHEMA"


def test_missing_reviewer_metadata_field_rejected() -> None:
    record = _valid_record_dict()
    del record["reviewer_metadata"]["inspection_tool"]
    with pytest.raises(SchemaValidationError):
        build_stage2_1_record_from_dict(record)


def test_missing_boundary_marker_rejected() -> None:
    record = _valid_record_dict()
    del record["boundary_adjudications"]["T4_tail_clearance"]
    with pytest.raises(SchemaValidationError, match="missing required keys"):
        build_stage2_1_record_from_dict(record)


def test_known_role_label_reviewer_id_rejected() -> None:
    """Directly re-proves the Phase 11.1 finding can never recur: the exact
    string found in all 27 fabricated records is permanently blocked."""
    record = _valid_record_dict()
    record["reviewer_metadata"]["reviewer_id"] = "human_researcher_lead"
    with pytest.raises(SchemaValidationError, match="role label or placeholder"):
        build_stage2_1_record_from_dict(record)


def test_implausibly_short_review_duration_rejected() -> None:
    record = _valid_record_dict()
    record["reviewer_metadata"]["review_end_utc"] = (T0 + timedelta(seconds=5)).isoformat().replace("+00:00", "Z")
    with pytest.raises(SchemaValidationError, match="below the minimum plausible threshold"):
        build_stage2_1_record_from_dict(record)


def test_review_end_before_start_rejected() -> None:
    record = _valid_record_dict()
    record["reviewer_metadata"]["review_start_utc"], record["reviewer_metadata"]["review_end_utc"] = (
        record["reviewer_metadata"]["review_end_utc"], record["reviewer_metadata"]["review_start_utc"],
    )
    with pytest.raises(SchemaValidationError, match="must be strictly after"):
        build_stage2_1_record_from_dict(record)


def test_missing_model_independence_attestation_rejected() -> None:
    record = _valid_record_dict()
    record["model_independence_attestation"]["attested"] = False
    with pytest.raises(SchemaValidationError, match="attested must be true"):
        build_stage2_1_record_from_dict(record)


def test_boilerplate_attestation_statement_rejected() -> None:
    record = _valid_record_dict()
    record["model_independence_attestation"]["statement"] = "yes"
    with pytest.raises(SchemaValidationError, match="specific, non-boilerplate"):
        build_stage2_1_record_from_dict(record)


def test_observable_boundary_without_value_rejected() -> None:
    record = _valid_record_dict()
    record["boundary_adjudications"]["T1_danger_zone_entry"] = {
        "state": "OBSERVABLE", "rationale": "x", "value_s": None, "reference_camera": "front",
    }
    with pytest.raises(SchemaValidationError, match="value_s is required"):
        build_stage2_1_record_from_dict(record)


def test_censored_boundary_with_value_rejected() -> None:
    record = _valid_record_dict()
    record["boundary_adjudications"]["T_scene_clear"]["value_s"] = 12.0
    with pytest.raises(SchemaValidationError, match="must be None when state is"):
        build_stage2_1_record_from_dict(record)


def test_empty_adjudication_history_rejected() -> None:
    record = _valid_record_dict()
    record["adjudication_history"] = []
    with pytest.raises(SchemaValidationError, match="must be non-empty"):
        build_stage2_1_record_from_dict(record)


def test_adjudication_history_mismatched_with_status_rejected() -> None:
    record = _valid_record_dict()
    record["adjudication_history"][-1]["status_set"] = "NEEDS_SECOND_REVIEW"
    with pytest.raises(SchemaValidationError, match="must match the record's current adjudication_status"):
        build_stage2_1_record_from_dict(record)


def test_out_of_order_adjudication_history_rejected() -> None:
    record = _valid_record_dict()
    record["adjudication_history"] = [
        {"event": "second", "by": "jane_doe_researcher", "at_utc": T_END, "status_set": "APPROVED"},
        {"event": "first", "by": "jane_doe_researcher", "at_utc": T_START, "status_set": "APPROVED"},
    ]
    with pytest.raises(SchemaValidationError, match="chronologically non-decreasing"):
        build_stage2_1_record_from_dict(record)


# --- Completion criterion 3: stale proposals / mismatched media rejected --


def test_stale_proposal_reference_rejected() -> None:
    violations = validate_for_promotion(
        _valid_record_dict(), active_proposal_sha256_by_event={"event_001": "d" * 64},
        media_sha256_registry=_media_registry(),
        authorized_reviewers=_authorized_reviewers(), media_file_paths=_bogus_media_file_paths(),
    )
    codes = {v.code for v in violations}
    assert "STALE_PROPOSAL_REFERENCE" in codes


def test_missing_media_registry_entry_rejected() -> None:
    violations = validate_for_promotion(
        _valid_record_dict(), active_proposal_sha256_by_event=_active_proposal_map(), media_sha256_registry={},
        authorized_reviewers=_authorized_reviewers(), media_file_paths=_bogus_media_file_paths(),
    )
    codes = {v.code for v in violations}
    assert "MISSING_MEDIA_IDENTITY" in codes


def test_incomplete_media_registry_entry_rejected() -> None:
    violations = validate_for_promotion(
        _valid_record_dict(), active_proposal_sha256_by_event=_active_proposal_map(),
        media_sha256_registry={"event_001": {"front": VALID_MEDIA_FRONT_SHA}},
        authorized_reviewers=_authorized_reviewers(), media_file_paths=_bogus_media_file_paths(),
    )
    codes = {v.code for v in violations}
    assert "INCOMPLETE_MEDIA_IDENTITY" in codes


def test_stale_proposal_promotion_raises_and_writes_nothing(tmp_path: Path) -> None:
    out_dir = tmp_path / "stage3_sandbox"
    with pytest.raises(PromotionRejected) as exc_info:
        promote_record(
            _valid_record_dict(), output_dir=out_dir,
            active_proposal_sha256_by_event={"event_001": "d" * 64}, media_sha256_registry=_media_registry(),
            authorized_reviewers=_authorized_reviewers(), media_file_paths=_bogus_media_file_paths(),
        )
    assert any(v.code == "STALE_PROPOSAL_REFERENCE" for v in exc_info.value.violations)
    assert not out_dir.exists() or not any(out_dir.iterdir())


# --- Completion criterion 4: disagreement cannot resolve automatically ----


def test_needs_second_review_status_rejected_from_promotion() -> None:
    record = _valid_record_dict(adjudication_status="NEEDS_SECOND_REVIEW")
    record["adjudication_history"][-1]["status_set"] = "NEEDS_SECOND_REVIEW"
    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event=_active_proposal_map(), media_sha256_registry=_media_registry(),
        authorized_reviewers=_authorized_reviewers(), media_file_paths=_bogus_media_file_paths(),
    )
    assert any(v.code == "UNRESOLVED_DISAGREEMENT" for v in violations)


def test_disputed_status_rejected_from_promotion() -> None:
    record = _valid_record_dict(adjudication_status="DISPUTED")
    record["adjudication_history"][-1]["status_set"] = "DISPUTED"
    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event=_active_proposal_map(), media_sha256_registry=_media_registry(),
        authorized_reviewers=_authorized_reviewers(), media_file_paths=_bogus_media_file_paths(),
    )
    assert any(v.code == "UNRESOLVED_DISAGREEMENT" for v in violations)


def test_rejected_status_blocked_distinctly_from_unresolved() -> None:
    """REJECTED is a final, resolved outcome (a human explicitly rejected
    the candidate) -- distinct from the pending states above -- but is
    still correctly blocked from promotion, just under a different code."""
    record = _valid_record_dict(adjudication_status="REJECTED")
    record["adjudication_history"][-1]["status_set"] = "REJECTED"
    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event=_active_proposal_map(), media_sha256_registry=_media_registry(),
        authorized_reviewers=_authorized_reviewers(), media_file_paths=_bogus_media_file_paths(),
    )
    codes = {v.code for v in violations}
    assert "NOT_APPROVED" in codes
    assert "UNRESOLVED_DISAGREEMENT" not in codes


def test_no_automated_tie_breaking_function_exists() -> None:
    """There is no function anywhere in promotion_gate.py or
    stage2_1_schema.py that resolves a disagreement automatically (e.g. by
    averaging two values or picking a majority) -- confirmed by absence."""
    import railway_detection.annotation.promotion_gate as gate_module
    import railway_detection.annotation.stage2_1_schema as schema_module

    forbidden_names = ["resolve_disagreement", "average_values", "majority_vote", "auto_resolve"]
    for name in forbidden_names:
        assert not hasattr(gate_module, name)
        assert not hasattr(schema_module, name)


# --- Completion criterion 5: cannot bypass via alternate field names ------


def test_renaming_adjudication_status_to_approval_status_cannot_bypass() -> None:
    """Mutation test: take a VALID record and rename its adjudication_status
    key to approval_status (mimicking the field name the OLD, Stage-1-only
    firewall checks). The Stage-2.1 schema requires `adjudication_status`
    specifically; renaming it away makes the record fail schema validation
    with a missing-field error, not silently pass as approved."""
    record = _valid_record_dict()
    record["approval_status"] = record.pop("adjudication_status")
    with pytest.raises(SchemaValidationError, match="Missing required top-level field"):
        build_stage2_1_record_from_dict(record)

    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event=_active_proposal_map(), media_sha256_registry=_media_registry(),
        authorized_reviewers=_authorized_reviewers(), media_file_paths=_bogus_media_file_paths(),
    )
    assert any(v.code == "SCHEMA_VALIDATION_FAILED" for v in violations)


def test_renaming_approval_status_variant_in_legacy_schema_still_rejected() -> None:
    """The reverse mutation: a legacy-schema (7.0.0) record that ALSO
    happens to carry adjudication_status: APPROVED (i.e. exactly what the
    real 27 records look like) is rejected purely on schema_version,
    before the adjudication_status field is ever inspected."""
    record = {"schema_version": "7.0.0", "event_id": "event_001", "adjudication_status": "APPROVED"}
    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event=_active_proposal_map(), media_sha256_registry=_media_registry(),
        authorized_reviewers=_authorized_reviewers(), media_file_paths=_bogus_media_file_paths(),
    )
    assert len(violations) == 1
    assert violations[0].code == "LEGACY_OR_UNKNOWN_SCHEMA"


def test_invalidation_marker_blocks_promotion_even_if_otherwise_valid() -> None:
    record = _valid_record_dict()
    record["invalidation"] = {"reason": "superseded", "at_utc": T_END}
    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event=_active_proposal_map(), media_sha256_registry=_media_registry(),
        authorized_reviewers=_authorized_reviewers(), media_file_paths=_bogus_media_file_paths(),
    )
    assert len(violations) == 1
    assert violations[0].code == "RECORD_INVALIDATED"


def test_batch_level_identical_timestamp_bypass_blocked() -> None:
    """Reproduces the exact real-world bulk-approval pattern (Phase 11.1) at
    the BATCH promotion level: N records sharing one timestamp, no
    plausible duration recorded in the batch-integrity-relevant fields --
    even if each record individually could pass schema validation with its
    own valid review_duration_s, the batch-level check independently
    re-derives duration from what the shared review_date_utc field implies
    and flags the collision."""
    shared_start = T_START
    records = []
    for i in range(1, 6):
        r = _valid_record_dict(event_id=f"event_{i:03d}")
        r["reviewer_metadata"]["review_start_utc"] = shared_start
        records.append(r)

    violations = validate_batch_for_promotion(
        records,
        active_proposal_sha256_by_event={r["event_id"]: VALID_PROPOSAL_SHA for r in records},
        media_sha256_registry={r["event_id"]: {"front": VALID_MEDIA_FRONT_SHA, "back": VALID_MEDIA_BACK_SHA} for r in records},
        authorized_reviewers=_authorized_reviewers(),
        media_file_paths={r["event_id"]: _bogus_media_file_paths()["event_001"] for r in records},
    )
    batch_codes = {v.code for v in violations if v.code.startswith("BATCH_")}
    assert "BATCH_IDENTICAL_TIMESTAMP_NO_PLAUSIBLE_DURATION" in batch_codes


# --- Task 5: researcher-controlled invalidation (proposed, not executed) --


def test_propose_invalidation_requires_nonempty_reason(tmp_path: Path) -> None:
    fake_record = tmp_path / "fake_review.json"
    fake_record.write_text("{}")
    with pytest.raises(ValueError, match="reason must be"):
        propose_invalidation(
            event_id="event_001", reason="", actor="jane_doe", authorized_statement="I authorize this",
            affected_record_path=fake_record,
        )


def test_propose_invalidation_requires_actor_and_authorization(tmp_path: Path) -> None:
    fake_record = tmp_path / "fake_review.json"
    fake_record.write_text("{}")
    with pytest.raises(ValueError, match="actor must be"):
        propose_invalidation(
            event_id="event_001", reason="stale batch", actor="", authorized_statement="I authorize this",
            affected_record_path=fake_record,
        )
    with pytest.raises(ValueError, match="authorized_statement must be"):
        propose_invalidation(
            event_id="event_001", reason="stale batch", actor="jane_doe", authorized_statement="",
            affected_record_path=fake_record,
        )


def test_propose_invalidation_never_modifies_the_affected_record(tmp_path: Path) -> None:
    fake_record = tmp_path / "fake_review.json"
    original_content = '{"adjudication_status": "APPROVED"}'
    fake_record.write_text(original_content)
    import hashlib
    original_sha = hashlib.sha256(original_content.encode()).hexdigest()

    event = propose_invalidation(
        event_id="event_001", reason="Shares identical batch timestamp with 26 other records; no provenance.",
        actor="jane_doe_researcher", authorized_statement="I, jane_doe_researcher, authorize this invalidation proposal.",
        affected_record_path=fake_record,
    )

    assert fake_record.read_text() == original_content  # byte-for-byte unmodified
    assert event.affected_record_sha256 == original_sha
    assert event.event_id == "event_001"


def test_write_invalidation_proposal_is_append_only(tmp_path: Path) -> None:
    fake_record = tmp_path / "fake_review.json"
    fake_record.write_text('{"x": 1}')
    out_path = tmp_path / "proposed_invalidations.json"

    event1 = propose_invalidation(
        event_id="event_001", reason="reason one", actor="jane_doe", authorized_statement="I authorize this",
        affected_record_path=fake_record,
    )
    write_invalidation_proposal([event1], out_path)
    first_pass = json.loads(out_path.read_text())["disposition_events"]
    assert len(first_pass) == 1

    event2 = propose_invalidation(
        event_id="event_002", reason="reason two", actor="jane_doe", authorized_statement="I authorize this",
        affected_record_path=fake_record,
    )
    write_invalidation_proposal([event2], out_path)
    second_pass = json.loads(out_path.read_text())["disposition_events"]
    assert len(second_pass) == 2  # appended, not replaced
    assert second_pass[0]["event_id"] == "event_001"  # original entry preserved
    assert second_pass[1]["event_id"] == "event_002"


def test_invalidation_proposal_never_targets_the_real_reviews_directory() -> None:
    """Neither function takes a hardcoded default path -- `output_path` and
    `affected_record_path` are both required, caller-supplied parameters
    with no default value at all, so there is no way to invoke either
    function and have it silently fall back to a real data/ground_truth/
    path. Confirmed via the actual function signatures, not by searching
    docstring prose (which legitimately mentions that path in explaining
    why no default points there)."""
    import inspect

    for fn in (write_invalidation_proposal, propose_invalidation):
        for param in inspect.signature(fn).parameters.values():
            if param.name in ("output_path", "affected_record_path"):
                assert param.default is inspect.Parameter.empty, (
                    f"{fn.__name__}'s {param.name} must have no default value"
                )
