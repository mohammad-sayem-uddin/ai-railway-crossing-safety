"""Phase 11.1, Task 3: targeted tests tracing the annotation approval/
promotion safeguards actually present in this repository, and the new
prototype safeguard proposed in `integrity_safeguard.py`.

Every test here uses isolated, synthetic, in-memory or tmp_path fixtures.
None reads, writes, or modifies any file under `data/ground_truth/`. The
real 27 review records are never touched by this test file (confirmed by
the preservation hash check in `docs/PHASE11_1_ANNOTATION_INTEGRITY_AUDIT.md`,
re-run after this test suite executes).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from railway_detection.annotation.integrity_safeguard import (
    check_proposal_currency,
    check_review_batch_integrity,
)
from railway_detection.annotation.schemas import (
    SchemaValidationError,
    assert_proposal_approval_firewall,
)

# --- Task 3: does the EXISTING firewall catch what actually happened? ----


def test_existing_firewall_rejects_approval_status_on_a_proposal_write() -> None:
    """Confirms the one real safeguard that exists works correctly within
    its own actual scope (Stage 1 proposal writes)."""
    proposal_path = Path("data/ground_truth/proposals/train_events/event_999_proposal.json")
    with pytest.raises(SchemaValidationError, match="approval_status: APPROVED"):
        assert_proposal_approval_firewall(proposal_path, {"approval_status": "APPROVED"})


def test_existing_firewall_does_not_recognize_the_field_name_the_real_reviews_use() -> None:
    """THE central gap found in Phase 11.1's investigation: the firewall
    checks for the literal key `approval_status`, but the actual fabricated
    review records use `adjudication_status`. A document carrying
    `adjudication_status: APPROVED` passes this check completely silently,
    even if (hypothetically) routed through the one real safeguard this
    repository has."""
    proposal_path = Path("data/ground_truth/proposals/train_events/event_999_proposal.json")
    # No exception raised -- this is the gap, demonstrated directly.
    assert_proposal_approval_firewall(proposal_path, {"adjudication_status": "APPROVED"})


def test_existing_firewall_is_never_applied_to_a_reviews_directory_path() -> None:
    """The firewall's own directory check only prohibits writes into the
    Stage 3 approved directories (`data/ground_truth/{train,no_train,engine}_events/`)
    when NOT under `proposals/`. A write into `data/ground_truth/reviews/`
    passes through entirely unexamined by this function -- it is neither a
    prohibited Stage 3 directory nor does it need to be under `proposals/`
    to avoid the (irrelevant, for this path) "must be under proposals/"
    check... except it DOES hit that check, for an unrelated reason, since
    `reviews/` is not `proposals/`. This test documents the actual current
    behavior precisely rather than assuming it: calling the firewall on a
    reviews/ path raises only the generic "must be under proposals/" error
    -- a side effect of the directory check's design, not a deliberate
    reviews/-specific protection, and it says nothing about the
    `adjudication_status` content itself (see the test above)."""
    review_path = Path("data/ground_truth/reviews/train_events/event_999_review.json")
    with pytest.raises(SchemaValidationError, match="must be saved under a 'proposals/'"):
        assert_proposal_approval_firewall(review_path, {"adjudication_status": "APPROVED"})
    # Confirms this rejection is incidental to directory structure, not
    # content-aware: the identical call with a harmless payload is
    # rejected for exactly the same reason, proving the content was never
    # inspected.
    with pytest.raises(SchemaValidationError, match="must be saved under a 'proposals/'"):
        assert_proposal_approval_firewall(review_path, {"some_harmless_field": "value"})


def test_no_review_record_validator_exists_anywhere_in_the_annotation_module() -> None:
    """Confirms, by construction, that no function analogous to
    `assert_proposal_approval_firewall` exists for Stage 2 review records."""
    import railway_detection.annotation.schemas as schemas_module

    candidate_names = [
        "assert_review_approval_firewall", "assert_review_requires_human_signoff",
        "validate_review_record", "assert_review_firewall", "check_review_integrity",
    ]
    for name in candidate_names:
        assert not hasattr(schemas_module, name), (
            f"Expected no such safeguard function to exist in schemas.py, found '{name}'"
        )


# --- Task 3: can bulk/implausible approval pass unexamined? --------------


def _synthetic_review(event_id: str, timestamp: str, **overrides) -> dict:
    base = {
        "event_id": event_id,
        "adjudication_status": "APPROVED",
        "reviewer_metadata": {"reviewer_id": "synthetic_reviewer", "review_date_utc": timestamp},
        "proposal_reference": {"proposal_sha256": "a" * 64},
    }
    base.update(overrides)
    return base


def test_bulk_identical_timestamp_batch_is_currently_unchecked_by_any_repo_safeguard(tmp_path: Path) -> None:
    """Reproduces, in isolation (synthetic data, tmp_path only, never
    touching data/ground_truth/), the EXACT pattern Phase 11 found in the
    real 27 records: N review records, all APPROVED, all sharing one
    identical timestamp. Confirms no existing repository function raises
    or flags anything when such a batch is constructed and written --
    because none exists to call (Task 3's "can bulk approval happen /
    can implausible timestamps pass validation" questions, answered
    directly: yes, trivially, because nothing currently checks)."""
    import json

    shared_ts = "2026-10-12T16:51:21Z"
    records = [_synthetic_review(f"event_{i:03d}", shared_ts) for i in range(1, 28)]
    out_dir = tmp_path / "synthetic_reviews"
    out_dir.mkdir()
    for r in records:
        (out_dir / f"{r['event_id']}_review.json").write_text(json.dumps(r), encoding="utf-8")

    written = list(out_dir.glob("*.json"))
    assert len(written) == 27  # the bulk write itself succeeded, unobstructed, exactly as it did for real


def test_new_prototype_safeguard_flags_the_exact_real_world_pattern() -> None:
    """The reference safeguard this phase proposes (`integrity_safeguard.py`)
    DOES flag the reproduced pattern -- demonstrating what SHOULD have
    existed, tested against isolated synthetic data only."""
    shared_ts = "2026-10-12T16:51:21Z"
    records = [_synthetic_review(f"event_{i:03d}", shared_ts) for i in range(1, 28)]

    violations = check_review_batch_integrity(records)

    # Every record trips BOTH checks: it shares the implausible batch
    # timestamp with no distinguishing duration, AND it independently
    # claims APPROVED with no provenance at all -- exactly the real
    # records' actual shape (no review_duration_s or review_session_id
    # field exists anywhere in the real 27 files, confirmed in Phase 11.1's
    # audit).
    identical_ts_violations = [v for v in violations if v.code == "IDENTICAL_TIMESTAMP_NO_PLAUSIBLE_DURATION"]
    no_provenance_violations = [v for v in violations if v.code == "APPROVED_WITHOUT_PROVENANCE"]
    assert len(identical_ts_violations) == 27
    assert len(no_provenance_violations) == 27
    flagged_events = {v.event_id for v in identical_ts_violations}
    assert flagged_events == {r["event_id"] for r in records}


def test_new_prototype_safeguard_accepts_genuinely_distinct_reviews() -> None:
    """Control case: a batch of reviews with genuinely distinct timestamps
    (one every few minutes, consistent with real per-event video review)
    AND individually plausible review durations produces zero violations --
    the fully legitimate case this safeguard is designed to let through."""
    records = [
        _synthetic_review("event_001", "2026-10-14T09:00:00Z", review_duration_s=480.0),
        _synthetic_review("event_002", "2026-10-14T09:14:00Z", review_duration_s=510.0),
        _synthetic_review("event_003", "2026-10-14T09:31:00Z", review_duration_s=390.0),
    ]
    violations = check_review_batch_integrity(records)
    assert violations == []


def test_new_prototype_safeguard_accepts_identical_timestamp_with_plausible_duration() -> None:
    """A shared timestamp is not inherently disqualifying if each record
    independently carries a plausible review_duration_s -- e.g. two
    reviewers working in parallel on different events, each logging their
    own multi-minute session. (Not the pattern found in the real records,
    which have no review_duration_s field at all.)"""
    shared_ts = "2026-10-14T09:00:00Z"
    records = [
        _synthetic_review("event_001", shared_ts, review_duration_s=180.0),
        _synthetic_review("event_002", shared_ts, review_duration_s=240.0),
    ]
    violations = check_review_batch_integrity(records)
    assert violations == []


def test_new_prototype_safeguard_flags_approved_without_any_provenance() -> None:
    record = _synthetic_review("event_001", "2026-10-14T09:00:00Z")
    violations = check_review_batch_integrity([record])
    assert len(violations) == 1
    assert violations[0].code == "APPROVED_WITHOUT_PROVENANCE"


def test_new_prototype_safeguard_flags_stale_proposal_references() -> None:
    """Reproduces, in isolation, Phase 11.1's second finding: all 27 real
    review records reference a superseded (non-latest) proposal version.
    Synthetic equivalent: a review references sha256 'old', but the
    currently active proposal has sha256 'new'."""
    records = [_synthetic_review("event_001", "2026-10-14T09:00:00Z", review_duration_s=120.0)]
    records[0]["proposal_reference"]["proposal_sha256"] = "old" + "0" * 61
    active = {"event_001": "new" + "0" * 61}

    violations = check_proposal_currency(records, active)
    assert len(violations) == 1
    assert violations[0].code == "STALE_PROPOSAL_REFERENCE"


def test_new_prototype_safeguard_accepts_current_proposal_reference() -> None:
    sha = "c" * 64
    records = [_synthetic_review("event_001", "2026-10-14T09:00:00Z", review_duration_s=120.0)]
    records[0]["proposal_reference"]["proposal_sha256"] = sha
    active = {"event_001": sha}

    violations = check_proposal_currency(records, active)
    assert violations == []
