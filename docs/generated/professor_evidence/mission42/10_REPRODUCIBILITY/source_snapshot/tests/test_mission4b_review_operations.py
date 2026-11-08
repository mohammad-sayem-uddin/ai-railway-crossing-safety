"""Mission 4B synthetic tests.

All fixtures are under pytest ``tmp_path`` and contain text bytes with media
file suffixes only to exercise the existing schema helpers.  No repository raw
media is opened, decoded, or hashed by this suite.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from railway_detection.annotation.promotion_gate import (
    AuthorizedReviewersLoadError,
    load_authorized_reviewers,
    validate_batch_for_promotion,
    validate_for_promotion,
)
from railway_detection.annotation.review_progress import (
    TRACKER_STATUSES,
    build_progress_tracker,
    validate_progress_tracker,
)
from railway_detection.annotation.review_queue_validator import audit_review_queue
from railway_detection.annotation.review_session import build_review_record
from railway_detection.annotation.schemas import SchemaValidationError
from railway_detection.annotation.stage2_1_schema import CANONICAL_TIMESTAMPS


REVIEWER_A = "alice.reviewer@example.org"
REVIEWER_B = "bob.reviewer@example.org"
SHA = "a" * 64


def _boundaries(*, uncertain: bool = False) -> dict[str, dict]:
    result = {
        name: {
            "state": "OBSERVABLE",
            "rationale": f"Synthetic fixture evidence for {name}",
            "value_s": float(index),
            "reference_camera": "front" if index < 3 else "back",
            "frame_index": index,
        }
        for index, name in enumerate(CANONICAL_TIMESTAMPS)
    }
    if uncertain:
        result["T4_tail_clearance"] = {
            "state": "UNCERTAIN",
            "rationale": "Synthetic fixture intentionally lacks sufficient evidence",
            "value_s": None,
            "reference_camera": None,
            "frame_index": None,
        }
    return result


def _record(tmp_path: Path, reviewer: str = REVIEWER_A, *, review_id: str = "review-a", uncertain: bool = False) -> dict:
    front = tmp_path / f"{review_id}_front.mov"
    back = tmp_path / f"{review_id}_back.mov"
    front.write_bytes(f"synthetic front {review_id}".encode())
    back.write_bytes(f"synthetic back {review_id}".encode())
    start = datetime(2026, 11, 1, 10, 0, 0, tzinfo=UTC)
    ts = lambda seconds: (start + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")
    return build_review_record(
        event_id=f"synthetic_{review_id}",
        cohort="train_events",
        reviewer_id=reviewer,
        authorized_reviewers=frozenset({REVIEWER_A, REVIEWER_B}),
        review_session_id=f"session-{review_id}",
        review_start_utc=ts(0),
        review_end_utc=ts(60),
        inspection_tool="synthetic fixture tool",
        attestation_statement="I inspected only synthetic source bytes and no model predictions.",
        attested_at_utc=ts(61),
        front_media_path=front,
        back_media_path=back,
        observed_at_utc=ts(1),
        proposal_file=f"synthetic/{review_id}_proposal.json",
        proposal_sha256=SHA,
        boundary_adjudications=_boundaries(uncertain=uncertain),
        adjudication_status="APPROVED",
        review_id=review_id,
    )


def _promotion_context(tmp_path: Path, record: dict) -> dict:
    front = tmp_path / f"{record['review_id']}_front.mov"
    back = tmp_path / f"{record['review_id']}_back.mov"
    pair = {
        "front": hashlib.sha256(front.read_bytes()).hexdigest(),
        "back": hashlib.sha256(back.read_bytes()).hexdigest(),
    }
    key = f"{record['cohort']}/{record['event_id']}"
    return {
        "active_proposal_sha256_by_event": {key: SHA},
        "media_sha256_registry": {key: pair},
        "authorized_reviewers": frozenset({REVIEWER_A, REVIEWER_B}),
        "media_file_paths": {key: {"front": str(front), "back": str(back)}},
    }


def test_real_queue_has_all_27_cohort_qualified_events_and_no_synthetic() -> None:
    audit = audit_review_queue(Path.cwd())
    assert audit.passed
    assert audit.total_events == 27
    assert audit.queue_category_counts == {"INVALID": 27}
    assert audit.synthetic_event_keys == ()
    assert audit.reviewed_without_genuine_record == ()
    assert audit.inventory_status_mismatches == ()

    queue = json.loads(Path("docs/generated/STAGE21_REVIEW_QUEUE.json").read_text(encoding="utf-8"))
    engine_keys = {item["event_key"] for item in queue["items"] if item["cohort"] == "engine_events"}
    train_keys = {item["event_key"] for item in queue["items"] if item["cohort"] == "train_events"}
    assert engine_keys == {"engine_events/event_001"}
    assert not engine_keys & train_keys


def test_queue_validator_detects_duplicate_missing_and_wrong_cohort(tmp_path: Path) -> None:
    inventory = {"train_events/event_001": {"event_id": "event_001", "category": "train_events"}}
    queue = {
        "items": [
            {"event_key": "train_events/event_001", "cohort": "train_events", "event_id": "event_001", "queue_id": "q"},
            {"event_key": "train_events/event_001", "cohort": "no_train_events", "event_id": "event_001", "queue_id": "q"},
        ]
    }
    review_inventory = {"events": {"train_events/event_001": {"cohort": "train_events", "event_id": "event_001", "review_status": "NOT_STARTED", "stage2_1_review_file": None}}}
    (tmp_path / "inventory.json").write_text(json.dumps(inventory), encoding="utf-8")
    (tmp_path / "queue.json").write_text(json.dumps(queue), encoding="utf-8")
    (tmp_path / "review_inventory.json").write_text(json.dumps(review_inventory), encoding="utf-8")
    audit = audit_review_queue(tmp_path, queue_path="queue.json", inventory_path="inventory.json", review_inventory_path="review_inventory.json", reviews_dir="reviews")
    assert audit.duplicate_event_keys == ("train_events/event_001",)
    assert audit.cohort_mismatches == ("train_events/event_001",)
    assert audit.duplicate_queue_ids == ("q",)
    assert not audit.passed


def test_queue_validator_detects_missing_event(tmp_path: Path) -> None:
    inventory = {
        "train_events/event_001": {"event_id": "event_001", "category": "train_events"},
        "train_events/event_002": {"event_id": "event_002", "category": "train_events"},
    }
    queue = {
        "items": [
            {
                "event_key": "train_events/event_001",
                "cohort": "train_events",
                "event_id": "event_001",
                "queue_id": "q1",
                "active_candidate_proposal": {"path": "data/ground_truth/proposals/train_events/event_001_proposal_v1.json"},
            }
        ]
    }
    review_inventory = {
        "events": {
            key: {
                "cohort": "train_events",
                "event_id": key.rsplit("/", 1)[1],
                "review_status": "NOT_STARTED",
                "stage2_1_review_file": None,
            }
            for key in inventory
        }
    }
    for name, payload in (
        ("inventory.json", inventory),
        ("queue.json", queue),
        ("review_inventory.json", review_inventory),
    ):
        (tmp_path / name).write_text(json.dumps(payload), encoding="utf-8")
    audit = audit_review_queue(
        tmp_path,
        queue_path="queue.json",
        inventory_path="inventory.json",
        review_inventory_path="review_inventory.json",
        reviews_dir="reviews",
    )
    assert audit.missing_event_keys == ("train_events/event_002",)
    assert not audit.passed


def test_allowlist_rejects_duplicate_revoked_blocklisted_and_missing(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    with pytest.raises(AuthorizedReviewersLoadError):
        load_authorized_reviewers(missing)
    for name, payload in {
        "duplicate.json": {"authorized_reviewers": [REVIEWER_A, REVIEWER_A]},
        "revoked.json": {"authorized_reviewers": [REVIEWER_A], "revoked_reviewers": [REVIEWER_A]},
        "blocklisted.json": {"authorized_reviewers": ["reviewer"]},
    }.items():
        path = tmp_path / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(AuthorizedReviewersLoadError):
            load_authorized_reviewers(path)


def test_duration_and_synthetic_rejection_are_fail_closed(tmp_path: Path) -> None:
    record = _record(tmp_path)
    record["reviewer_metadata"]["review_end_utc"] = "2026-11-01T10:00:10Z"
    with pytest.raises(SchemaValidationError):
        from railway_detection.annotation.stage2_1_schema import build_stage2_1_record_from_dict
        build_stage2_1_record_from_dict(record)
    context = _promotion_context(tmp_path, _record(tmp_path, review_id="recheck"))
    violations = validate_for_promotion(_record(tmp_path, review_id="recheck"), disallow_synthetic_identifiers=True, **context)
    assert any(v.code == "SYNTHETIC_RECORD_NOT_PROMOTABLE" for v in violations)


def test_synthetic_reviewer_and_session_identifiers_are_rejected(tmp_path: Path) -> None:
    reviewer_record = _record(tmp_path, review_id="synthetic-reviewer")
    reviewer_record["reviewer_metadata"]["reviewer_id"] = "pilot@synthetic.example.com"
    context = _promotion_context(tmp_path, reviewer_record)
    reviewer_codes = {
        violation.code
        for violation in validate_for_promotion(
            reviewer_record, disallow_synthetic_identifiers=True, **context
        )
    }
    assert "SYNTHETIC_RECORD_NOT_PROMOTABLE" in reviewer_codes

    session_record = _record(tmp_path, review_id="synthetic-session")
    session_record["reviewer_metadata"]["review_session_id"] = "synthetic_session_001"
    context = _promotion_context(tmp_path, session_record)
    session_codes = {
        violation.code
        for violation in validate_for_promotion(
            session_record, disallow_synthetic_identifiers=True, **context
        )
    }
    assert "SYNTHETIC_RECORD_NOT_PROMOTABLE" in session_codes


def test_conflicting_boundary_state_and_value_are_rejected(tmp_path: Path) -> None:
    record = _record(tmp_path, review_id="conflicting-boundary-state")
    record["boundary_adjudications"]["T2_crossing_occupancy_start"] = {
        "state": "UNCERTAIN",
        "rationale": "Synthetic fixture intentionally records unresolved evidence",
        "value_s": 0.5,
        "reference_camera": "front",
        "frame_index": 15,
    }
    from railway_detection.annotation.stage2_1_schema import build_stage2_1_record_from_dict
    with pytest.raises(SchemaValidationError, match="value_s must be None"):
        build_stage2_1_record_from_dict(record)


def test_second_review_requires_distinct_reviewer_and_missing_second_review_blocks(tmp_path: Path) -> None:
    first = _record(tmp_path, REVIEWER_A, review_id="first", uncertain=True)
    context = _promotion_context(tmp_path, first)
    # The current implementation blocks an explicitly unresolved record. It
    # intentionally does not infer a D3(a) trigger from UNCERTAIN/CENSORED
    # alone; that scientific trigger remains pending researcher decision.
    first["adjudication_status"] = "NEEDS_SECOND_REVIEW"
    first["adjudication_history"][-1]["status_set"] = "NEEDS_SECOND_REVIEW"
    missing = validate_for_promotion(first, **context)
    assert any(v.code == "UNRESOLVED_DISAGREEMENT" for v in missing)

    second = copy.deepcopy(first)
    second["review_id"] = "second"
    second["reviewer_metadata"]["reviewer_id"] = REVIEWER_A
    second["reviewer_metadata"]["review_session_id"] = "session-second"
    second["second_review_of"] = "first"
    second["adjudication_history"] = [
        {"event": "created", "by": REVIEWER_A, "at_utc": "2026-11-01T10:00:00Z", "status_set": "APPROVED"},
        {"event": "second_review", "by": REVIEWER_A, "at_utc": "2026-11-01T10:01:00Z", "status_set": "APPROVED"},
    ]
    from railway_detection.annotation.stage2_1_schema import build_stage2_1_record_from_dict
    with pytest.raises(SchemaValidationError):
        build_stage2_1_record_from_dict(second)

    # A different reviewer is accepted by the schema's history-level
    # independence check; a production batch still needs the explicit
    # researcher-approved trigger and resolution policy before promotion.
    distinct = copy.deepcopy(first)
    distinct["review_id"] = "distinct-second"
    distinct["reviewer_metadata"]["reviewer_id"] = REVIEWER_B
    distinct["reviewer_metadata"]["review_session_id"] = "session-distinct-second"
    distinct["second_review_of"] = "first"
    distinct["adjudication_history"] = [
        {"event": "created", "by": REVIEWER_A, "at_utc": "2026-11-01T10:00:00Z", "status_set": "NEEDS_SECOND_REVIEW"},
        {"event": "second_review", "by": REVIEWER_B, "at_utc": "2026-11-01T10:01:00Z", "status_set": "APPROVED"},
    ]
    distinct["adjudication_status"] = "APPROVED"
    # The schema-level independence check is the safeguard under test. The
    # synthetic record is not promoted and still contains a synthetic ID.
    assert build_stage2_1_record_from_dict(distinct).reviewer_metadata.reviewer_id == REVIEWER_B

    distinct_front = tmp_path / "distinct-second_front.mov"
    distinct_back = tmp_path / "distinct-second_back.mov"
    distinct_front.write_bytes(b"synthetic front distinct-second")
    distinct_back.write_bytes(b"synthetic back distinct-second")
    distinct_context = _promotion_context(tmp_path, distinct)
    batch = validate_batch_for_promotion(
        [first, distinct],
        active_proposal_sha256_by_event=distinct_context["active_proposal_sha256_by_event"],
        media_sha256_registry=distinct_context["media_sha256_registry"],
        authorized_reviewers=frozenset({REVIEWER_A, REVIEWER_B}),
        media_file_paths=distinct_context["media_file_paths"],
    )
    assert not any(v.code == "BATCH_SAME_REVIEWER_SECOND_REVIEW" for v in batch)


def test_duplicate_history_and_event_identity_are_rejected(tmp_path: Path) -> None:
    record = _record(tmp_path)
    record["adjudication_history"].append(dict(record["adjudication_history"][0]))
    from railway_detection.annotation.stage2_1_schema import build_stage2_1_record_from_dict
    with pytest.raises(SchemaValidationError):
        build_stage2_1_record_from_dict(record)
    queue = audit_review_queue(Path.cwd())
    assert queue.passed  # Real audit remains read-only and unaffected by synthetic mutation.


def test_progress_tracker_has_all_events_and_never_claims_approval() -> None:
    inventory = json.loads(Path("docs/PHASE11_3_REVIEW_INVENTORY.json").read_text(encoding="utf-8"))
    tracker = build_progress_tracker(inventory)
    assert tracker["total_events"] == 27
    assert tracker["status"] == "DESIGN_ONLY"
    assert tracker["approval_status"] == "NOT_APPROVED"
    assert tracker["status_counts"]["NOT_SCHEDULED"] == 27
    assert all(item["actual_source_status"] == "NOT_STARTED" for item in tracker["items"])
    assert all(item["ground_truth_approval"] is False for item in tracker["items"])
    assert validate_progress_tracker(tracker) == []

    invalid = copy.deepcopy(tracker)
    invalid["items"][0]["tracker_status"] = "APPROVED_BY_AUTHORIZED_REVIEWERS"
    assert validate_progress_tracker(invalid)


def test_progress_tracker_status_vocabulary_is_explicit() -> None:
    assert set(TRACKER_STATUSES) == {
        "NOT_SCHEDULED", "AWAITING_REVIEWER", "REVIEW_IN_PROGRESS", "FIRST_REVIEW_COMPLETE",
        "SECOND_REVIEW_REQUIRED", "SECOND_REVIEW_COMPLETE", "DISPUTED", "INCOMPLETE_EVIDENCE",
        "READY_FOR_HUMAN_VERIFICATION", "APPROVED_BY_AUTHORIZED_REVIEWERS", "BLOCKED_FROM_PROMOTION",
    }