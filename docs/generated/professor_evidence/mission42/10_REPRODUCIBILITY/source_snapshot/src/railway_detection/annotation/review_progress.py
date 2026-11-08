"""Non-authoritative Stage-2.1 review-progress tracker design.

The tracker is deliberately a projection of workflow state, not a ground-truth
store.  It contains no boundary values, no approval authority, and no
promotion operation.  ``build_progress_tracker`` can therefore be used to
prepare a blank tracker from an inventory without creating a review record or
assigning a reviewer.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

TRACKER_STATUSES = (
    "NOT_SCHEDULED",
    "AWAITING_REVIEWER",
    "REVIEW_IN_PROGRESS",
    "FIRST_REVIEW_COMPLETE",
    "SECOND_REVIEW_REQUIRED",
    "SECOND_REVIEW_COMPLETE",
    "DISPUTED",
    "INCOMPLETE_EVIDENCE",
    "READY_FOR_HUMAN_VERIFICATION",
    "APPROVED_BY_AUTHORIZED_REVIEWERS",
    "BLOCKED_FROM_PROMOTION",
)


def _key(entry: Mapping[str, Any]) -> str:
    return f"{entry.get('cohort', '')}/{entry.get('event_id', '')}"


def build_progress_tracker(
    review_inventory: Mapping[str, Any],
    *,
    queue_audit: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a design-only tracker projection from the existing inventory.

    The current repository inventory uses ``NOT_STARTED`` and null assignment
    fields for every event.  Those values are retained verbatim in
    ``actual_source_status``; the tracker-facing projection is
    ``NOT_SCHEDULED``.  No item is marked reviewed or approved.
    """
    events = review_inventory.get("events") if isinstance(review_inventory, Mapping) else None
    if not isinstance(events, Mapping):
        raise ValueError("review_inventory.events must be a mapping")
    items: list[dict[str, Any]] = []
    for event_key in sorted(events):
        entry = events[event_key]
        if not isinstance(entry, Mapping):
            raise ValueError(f"review inventory entry {event_key!r} must be a mapping")
        key = _key(entry)
        if key != event_key:
            raise ValueError(f"review inventory key/identity mismatch: {event_key!r} vs {key!r}")
        source_status = entry.get("review_status")
        assigned = entry.get("assigned_reviewer")
        stage_file = entry.get("stage2_1_review_file")
        if source_status == "NOT_STARTED" and assigned is None and stage_file is None:
            tracker_status = "NOT_SCHEDULED"
        elif stage_file is None and assigned is not None:
            tracker_status = "AWAITING_REVIEWER"
        else:
            # Existing inventory is intentionally not populated beyond the
            # blank state. Any future populated state must be classified by a
            # human-authorized workflow, not guessed by this projection.
            tracker_status = "BLOCKED_FROM_PROMOTION"
        items.append({
            "event_key": event_key,
            "cohort": entry.get("cohort"),
            "event_id": entry.get("event_id"),
            "actual_source_status": source_status,
            "assigned_reviewer": assigned,
            "stage21_review_file": stage_file,
            "tracker_status": tracker_status,
            "ground_truth_approval": False,
            "promotion_authorized": False,
            "status_basis": "read-only inventory projection; not a review record",
        })
    status_counts = Counter(item["tracker_status"] for item in items)
    result: dict[str, Any] = {
        "schema_version": "stage21-review-progress-design/1",
        "status": "DESIGN_ONLY",
        "approval_status": "NOT_APPROVED",
        "ground_truth_approval_authority": "human_researcher_only",
        "promotion_authorized": False,
        "media_accessed": False,
        "total_events": len(items),
        "items": items,
        "status_counts": {name: status_counts.get(name, 0) for name in TRACKER_STATUSES},
        "queue_audit_reference": dict(queue_audit) if queue_audit is not None else None,
        "warning": "This tracker does not create, imply, or replace human review, approval, or promotion records.",
    }
    return result


def validate_progress_tracker(tracker: Mapping[str, Any]) -> list[str]:
    """Return consistency errors without changing tracker state."""
    errors: list[str] = []
    items = tracker.get("items")
    if not isinstance(items, list):
        return ["items must be a list"]
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, Mapping):
            errors.append("non-object tracker item")
            continue
        key = str(item.get("event_key", ""))
        if not key or key in seen:
            errors.append(f"duplicate or blank event_key: {key!r}")
        seen.add(key)
        status = item.get("tracker_status")
        if status not in TRACKER_STATUSES:
            errors.append(f"{key}: unknown tracker_status {status!r}")
        if item.get("ground_truth_approval") is not False:
            errors.append(f"{key}: tracker must not claim ground_truth_approval")
        if item.get("promotion_authorized") is not False:
            errors.append(f"{key}: tracker must not claim promotion_authorized")
        if status == "NOT_SCHEDULED" and (item.get("assigned_reviewer") is not None or item.get("stage21_review_file") is not None):
            errors.append(f"{key}: NOT_SCHEDULED cannot have assignment or review file")
        if status == "APPROVED_BY_AUTHORIZED_REVIEWERS" and not item.get("stage21_review_file"):
            errors.append(f"{key}: approved workflow state requires a review file reference")
    if tracker.get("approval_status") != "NOT_APPROVED":
        errors.append("tracker approval_status must remain NOT_APPROVED")
    if tracker.get("status") != "DESIGN_ONLY":
        errors.append("tracker status must remain DESIGN_ONLY")
    return errors