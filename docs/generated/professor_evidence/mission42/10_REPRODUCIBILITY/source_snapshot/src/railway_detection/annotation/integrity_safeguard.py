"""Phase 11.1 prototype: a review-batch integrity safeguard that did not
previously exist anywhere in this repository.

Background: Phase 11's audit found that all 27 existing
`data/ground_truth/reviews/{cohort}/event_XXX_review.json` records claim
`"adjudication_status": "APPROVED"` under a single, identical
`review_date_utc` timestamp -- not possible for genuine, independently
conducted human review. Phase 11.1's investigation (see
`docs/PHASE11_1_ANNOTATION_INTEGRITY_AUDIT.md`) found that
`assert_proposal_approval_firewall` (schemas.py) is the only code-level
approval safeguard in this repository, and it is called ONLY when writing
Stage 1 proposal files, never for Stage 2 review records, and it checks a
different field name (`approval_status`) than the one the actual review
records use (`adjudication_status`) -- so it would not have caught this
batch even if it had been applied to reviews.

This module is a PROTOTYPE, NOT wired into any production write path. It is
not auto-applied anywhere; calling it is an explicit, separate step a
promotion workflow would need to add. It exists to (a) make the exact gap
concretely testable, and (b) give the remediation plan (Task 4) a reusable,
tested starting point -- not to retroactively validate or "fix" the
existing 27 records, which this module never reads or modifies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

MIN_PLAUSIBLE_REVIEW_DURATION_S = 30.0


@dataclass(frozen=True)
class IntegrityViolation:
    event_id: str
    code: str
    message: str


def _reviewer_metadata(record: dict[str, Any]) -> dict[str, Any]:
    """Return the record's reviewer metadata block, or an empty mapping."""
    meta = record.get("reviewer_metadata")
    return meta if isinstance(meta, dict) else {}


def _review_duration_s(record: dict[str, Any]) -> float | None:
    """Read review duration from Stage-2.1 metadata or the legacy top level.

    Stage-2.1 records nest provenance under ``reviewer_metadata``; the legacy
    schema this safeguard was written against used top-level fields. A record
    carrying neither (as all 27 legacy records do) still yields ``None``.
    """
    meta = _reviewer_metadata(record)
    for candidate in (meta.get("review_duration_s"), record.get("review_duration_s")):
        if isinstance(candidate, bool) or not isinstance(candidate, (int, float)):
            continue
        return float(candidate)
    # Stage-2.1 derives duration from the session window, so a raw record dict
    # carries the window but not the computed field.
    return _window_duration_s(meta) or _window_duration_s(record)


def _window_duration_s(source: dict[str, Any]) -> float | None:
    """Derive a session duration from an explicit review start/end window."""
    start_raw = source.get("review_start_utc")
    end_raw = source.get("review_end_utc")
    if not isinstance(start_raw, str) or not isinstance(end_raw, str):
        return None
    try:
        start = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    duration = (end - start).total_seconds()
    return duration if duration > 0 else None


def _review_session_id(record: dict[str, Any]) -> str | None:
    """Read the review session id from Stage-2.1 metadata or the legacy top level."""
    for candidate in (_reviewer_metadata(record).get("review_session_id"),
                      record.get("review_session_id")):
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    return None


def _review_timestamp(record: dict[str, Any]) -> str | None:
    """Read the review timestamp used to detect identical-batch signatures.

    Stage-2.1 has an explicit session window, so its start timestamp is the
    comparable value; the legacy schema exposed only ``review_date_utc``.
    """
    meta = _reviewer_metadata(record)
    for candidate in (meta.get("review_date_utc"), meta.get("review_start_utc"),
                      record.get("review_date_utc")):
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    return None


def check_review_batch_integrity(records: list[dict[str, Any]]) -> list[IntegrityViolation]:
    """Check a BATCH of review records (as would be promoted together) for
    the specific integrity signals Phase 11/11.1 found. Returns a list of
    violations; an empty list means no violation of THESE specific checks
    was found (this is not a full schema validator, and passing it is not
    equivalent to "this is a genuine human review" -- it only rules out the
    specific implausibility patterns this phase investigated).

    Checks:
    1. No two records in the batch may share an identical `review_date_utc`
       timestamp, unless each carries its own `review_duration_s` field
       that is independently plausible (>= MIN_PLAUSIBLE_REVIEW_DURATION_S)
       AND those durations are consistent with non-overlapping review
       sessions. (The existing 27 records have neither distinct timestamps
       nor any `review_duration_s` field at all.)
    2. Every record claiming `adjudication_status: APPROVED` (the field
       name actually used) OR `approval_status: APPROVED` (the field name
       the existing firewall checks) must carry a `review_duration_s` field
       of at least MIN_PLAUSIBLE_REVIEW_DURATION_S, or an explicit
       `review_session_id` distinguishing it from every other record in the
       batch.
    3. Every record's referenced proposal (`proposal_reference.proposal_sha256`
       or `proposal_reference.proposal_file`) must be supplied by the
       caller as the CURRENTLY ACTIVE proposal reference for that event
       (via `active_proposal_refs`) -- a review of a superseded proposal
       version is flagged, since it cannot certify the current candidate.
    """
    violations: list[IntegrityViolation] = []

    timestamp_groups: dict[str, list[str]] = {}
    for r in records:
        ts = _review_timestamp(r)
        event_id = r.get("event_id", "<unknown>")
        if ts:
            timestamp_groups.setdefault(ts, []).append(event_id)

    for ts, event_ids in timestamp_groups.items():
        if len(event_ids) <= 1:
            continue
        for r in records:
            if r.get("event_id") not in event_ids:
                continue
            event_id = r.get("event_id", "<unknown>")
            duration = _review_duration_s(r)
            if duration is None or duration < MIN_PLAUSIBLE_REVIEW_DURATION_S:
                violations.append(IntegrityViolation(
                    event_id=event_id,
                    code="IDENTICAL_TIMESTAMP_NO_PLAUSIBLE_DURATION",
                    message=(
                        f"review_date_utc '{ts}' is shared by {len(event_ids)} records "
                        f"({sorted(event_ids)}) with no individually-plausible "
                        f"review_duration_s (>= {MIN_PLAUSIBLE_REVIEW_DURATION_S}s) to "
                        "distinguish genuinely separate review sessions."
                    ),
                ))

    violations.extend(_check_non_overlapping_sessions(records))

    for r in records:
        event_id = r.get("event_id", "<unknown>")
        status = r.get("adjudication_status") or r.get("approval_status")
        if status != "APPROVED":
            continue
        duration = _review_duration_s(r)
        session_id = _review_session_id(r)
        if (duration is None or duration < MIN_PLAUSIBLE_REVIEW_DURATION_S) and not session_id:
            violations.append(IntegrityViolation(
                event_id=event_id,
                code="APPROVED_WITHOUT_PROVENANCE",
                message=(
                    f"Record claims APPROVED status but has neither a plausible "
                    f"review_duration_s nor a review_session_id to evidence a genuine, "
                    "individually-attributable review action."
                ),
            ))

    return violations


def _session_window(record: dict[str, Any]) -> tuple[datetime, datetime] | None:
    """Return a record's parsed [start, end) review window, if it has one."""
    source = _reviewer_metadata(record) or record
    start_raw = source.get("review_start_utc")
    end_raw = source.get("review_end_utc")
    if not isinstance(start_raw, str) or not isinstance(end_raw, str):
        return None
    try:
        start = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (start, end) if end > start else None


def _check_non_overlapping_sessions(
    records: list[dict[str, Any]],
) -> list[IntegrityViolation]:
    """Flag one reviewer claiming overlapping review windows for distinct events.

    Check 1 of this module promises durations "consistent with non-overlapping
    review sessions". A plausible per-record duration does not establish that:
    a single reviewer cannot genuinely review two events at the same time, so
    overlapping windows under one ``reviewer_id`` are not independent reviews
    however long each claims to be.
    """
    violations: list[IntegrityViolation] = []
    by_reviewer: dict[str, list[tuple[datetime, datetime, str]]] = {}
    for record in records:
        window = _session_window(record)
        if window is None:
            continue
        reviewer = _reviewer_metadata(record).get("reviewer_id") or record.get("reviewer_id")
        if not isinstance(reviewer, str) or not reviewer.strip():
            continue
        event_id = record.get("event_id", "<unknown>")
        by_reviewer.setdefault(reviewer, []).append((window[0], window[1], event_id))

    for reviewer, sessions in sorted(by_reviewer.items()):
        ordered = sorted(sessions, key=lambda item: (item[0], item[1], item[2]))
        for (start, end, event_id), (next_start, _, next_event) in zip(
            ordered, ordered[1:], strict=False
        ):
            if next_start < end:
                violations.append(IntegrityViolation(
                    event_id=event_id,
                    code="OVERLAPPING_REVIEW_SESSIONS",
                    message=(
                        f"reviewer '{reviewer}' claims a review of '{event_id}' from "
                        f"{start.isoformat()} to {end.isoformat()} that overlaps the review "
                        f"of '{next_event}' starting {next_start.isoformat()}; one reviewer "
                        "cannot conduct two independent reviews simultaneously."
                    ),
                ))
    return violations


def check_proposal_currency(
    records: list[dict[str, Any]], active_proposal_sha256_by_event: dict[str, str],
) -> list[IntegrityViolation]:
    """Flags any review record that references a proposal SHA-256 other
    than the currently-active one for that event -- i.e. a review of a
    proposal version that has since been superseded, which cannot certify
    the current candidate regardless of how the review itself was conducted."""
    violations: list[IntegrityViolation] = []
    for r in records:
        event_id = r.get("event_id", "<unknown>")
        referenced_sha = r.get("proposal_reference", {}).get("proposal_sha256")
        active_sha = active_proposal_sha256_by_event.get(event_id)
        if active_sha is not None and referenced_sha != active_sha:
            violations.append(IntegrityViolation(
                event_id=event_id,
                code="STALE_PROPOSAL_REFERENCE",
                message=(
                    f"Review references proposal sha256 '{referenced_sha}' but the "
                    f"currently active proposal for this event has sha256 '{active_sha}' "
                    "-- this review does not certify the current candidate."
                ),
            ))
    return violations
