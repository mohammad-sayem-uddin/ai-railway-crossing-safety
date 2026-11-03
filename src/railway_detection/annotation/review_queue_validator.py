"""Read-only validation of the Stage-2.1 review queue.

This module intentionally validates *metadata and JSON references only*.  It
does not open, decode, hash, or otherwise inspect source media.  It also never
writes to the queue, the review inventory, or ``data/ground_truth``.  The
result is an audit of whether a queue is structurally complete and whether its
references are cohort-qualified and internally consistent; it is not evidence
that a human reviewed an event.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from railway_detection.annotation.notices import verify_invalidation_notice
from railway_detection.annotation.stage2_1_schema import STAGE_2_1_SCHEMA_VERSION

EXPECTED_COHORT_COUNTS = {
    "train_events": 23,
    "no_train_events": 3,
    "engine_events": 1,
}
EXPECTED_EVENT_COUNT = sum(EXPECTED_COHORT_COUNTS.values())


class ReviewQueueValidationError(ValueError):
    """Raised when a queue or inventory is not a JSON object of the expected shape."""


@dataclass(frozen=True)
class ReviewQueueAudit:
    """Machine-readable, read-only queue audit result."""

    queue_path: str
    inventory_path: str
    total_events: int
    expected_event_count: int
    duplicate_event_keys: tuple[str, ...] = ()
    missing_event_keys: tuple[str, ...] = ()
    unexpected_event_keys: tuple[str, ...] = ()
    cohort_mismatches: tuple[str, ...] = ()
    duplicate_queue_ids: tuple[str, ...] = ()
    synthetic_event_keys: tuple[str, ...] = ()
    incorrect_proposal_references: tuple[str, ...] = ()
    invalid_invalidation_notices: tuple[str, ...] = ()
    missing_invalidation_notices: tuple[str, ...] = ()
    reviewed_without_genuine_record: tuple[str, ...] = ()
    inventory_status_mismatches: tuple[str, ...] = ()
    cohort_count_mismatches: tuple[str, ...] = ()
    queue_category_counts: Mapping[str, int] = field(default_factory=dict)
    notes: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        """Whether the structural/read-only checks passed."""
        return not any(
            (
                self.total_events != self.expected_event_count,
                self.duplicate_event_keys,
                self.missing_event_keys,
                self.unexpected_event_keys,
                self.cohort_mismatches,
                self.duplicate_queue_ids,
                self.synthetic_event_keys,
                self.incorrect_proposal_references,
                self.invalid_invalidation_notices,
                self.missing_invalidation_notices,
                self.reviewed_without_genuine_record,
                self.inventory_status_mismatches,
                self.cohort_count_mismatches,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "PASS" if self.passed else "FAIL",
            "read_only": True,
            "media_accessed": False,
            "queue_path": self.queue_path,
            "inventory_path": self.inventory_path,
            "total_events": self.total_events,
            "expected_event_count": self.expected_event_count,
            "expected_cohort_counts": dict(EXPECTED_COHORT_COUNTS),
            "duplicate_event_keys": list(self.duplicate_event_keys),
            "missing_event_keys": list(self.missing_event_keys),
            "unexpected_event_keys": list(self.unexpected_event_keys),
            "cohort_mismatches": list(self.cohort_mismatches),
            "duplicate_queue_ids": list(self.duplicate_queue_ids),
            "synthetic_event_keys": list(self.synthetic_event_keys),
            "incorrect_proposal_references": list(self.incorrect_proposal_references),
            "invalid_invalidation_notices": list(self.invalid_invalidation_notices),
            "missing_invalidation_notices": list(self.missing_invalidation_notices),
            "reviewed_without_genuine_record": list(self.reviewed_without_genuine_record),
            "inventory_status_mismatches": list(self.inventory_status_mismatches),
            "cohort_count_mismatches": list(self.cohort_count_mismatches),
            "queue_category_counts": dict(self.queue_category_counts),
            "notes": list(self.notes),
        }


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReviewQueueValidationError(f"could not read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReviewQueueValidationError(f"{path} must contain a JSON object")
    return value


def _event_key(value: Mapping[str, Any]) -> str | None:
    key = value.get("event_key")
    if isinstance(key, str) and key.count("/") == 1 and all(key.split("/")):
        return key
    cohort = value.get("cohort")
    event_id = value.get("event_id")
    if isinstance(cohort, str) and isinstance(event_id, str) and cohort and event_id:
        return f"{cohort}/{event_id}"
    return None


def audit_review_queue(
    root: Path | str,
    *,
    queue_path: Path | str = "docs/generated/STAGE21_REVIEW_QUEUE.json",
    inventory_path: Path | str = "data/manifests/layer_b_v2_annotation_inventory.json",
    review_inventory_path: Path | str = "docs/PHASE11_3_REVIEW_INVENTORY.json",
    reviews_dir: Path | str = "data/ground_truth/reviews",
) -> ReviewQueueAudit:
    """Audit a queue against the event inventory without touching source media.

    Review JSON and invalidation notices are read only to establish whether a
    queue item is a legacy/invalidation artifact or a genuine Stage-2.1
    record.  No media path is opened and no digest is computed by this module.
    """
    root_path = Path(root).resolve()
    queue_file = Path(queue_path)
    inventory_file = Path(inventory_path)
    review_inventory_file = Path(review_inventory_path)
    reviews_root = Path(reviews_dir)
    if not queue_file.is_absolute():
        queue_file = root_path / queue_file
    if not inventory_file.is_absolute():
        inventory_file = root_path / inventory_file
    if not review_inventory_file.is_absolute():
        review_inventory_file = root_path / review_inventory_file
    if not reviews_root.is_absolute():
        reviews_root = root_path / reviews_root

    queue = _read_json_object(queue_file)
    inventory = _read_json_object(inventory_file)
    review_inventory = _read_json_object(review_inventory_file)
    raw_items = queue.get("items")
    if not isinstance(raw_items, list):
        raise ReviewQueueValidationError("queue.items must be a list")
    raw_inventory = inventory
    raw_review_inventory = review_inventory.get("events")
    if not isinstance(raw_review_inventory, dict):
        raise ReviewQueueValidationError("review inventory.events must be an object")

    expected_keys = {str(key) for key in raw_inventory}
    observed_keys = [key for item in raw_items if isinstance(item, dict) for key in [_event_key(item)] if key]
    key_counts = Counter(observed_keys)
    duplicate_keys = tuple(sorted(key for key, count in key_counts.items() if count > 1))
    observed_set = set(observed_keys)
    missing_keys = tuple(sorted(expected_keys - observed_set))
    unexpected_keys = tuple(sorted(observed_set - expected_keys))

    cohort_mismatches: list[str] = []
    duplicate_queue_ids: list[str] = []
    queue_ids: list[str] = []
    synthetic_keys: list[str] = []
    incorrect_proposals: list[str] = []
    missing_notices: list[str] = []
    invalid_notices: list[str] = []
    reviewed_without_record: list[str] = []
    category_counts: Counter[str] = Counter()
    observed_cohorts: Counter[str] = Counter()

    for item in raw_items:
        if not isinstance(item, dict):
            cohort_mismatches.append("<non-object queue item>")
            continue
        key = _event_key(item)
        if key is None:
            cohort_mismatches.append("<queue item without cohort-qualified event key>")
            continue
        cohort, event_id = key.split("/", 1)
        observed_cohorts[cohort] += 1
        category_counts[str(item.get("queue_category", "<missing>"))] += 1
        if item.get("cohort") != cohort or item.get("event_id") != event_id:
            cohort_mismatches.append(key)
        queue_id = item.get("queue_id")
        if isinstance(queue_id, str):
            queue_ids.append(queue_id)
        if "synthetic" in key.lower() or "synthetic" in json.dumps(item, sort_keys=True).lower():
            synthetic_keys.append(key)

        proposal = item.get("active_candidate_proposal")
        proposal_path = proposal.get("path") if isinstance(proposal, dict) else None
        if not isinstance(proposal_path, str):
            incorrect_proposals.append(f"{key}:missing active proposal reference")
        else:
            expected_prefix = f"data/ground_truth/proposals/{cohort}/{event_id}_proposal"
            if not proposal_path.startswith(expected_prefix) or not proposal_path.endswith(".json"):
                incorrect_proposals.append(f"{key}:{proposal_path}")

        notice_path = reviews_root / cohort / f"{event_id}_review.INVALIDATION_NOTICE.json"
        if not notice_path.is_file():
            missing_notices.append(key)
        else:
            verification = verify_invalidation_notice(notice_path, reviews_root)
            if not verification.valid:
                invalid_notices.append(f"{key}:{verification.problem}")

        # A queue item may only claim completion when a genuine Stage-2.1
        # record is present. Legacy records, even with APPROVED text, do not
        # count because their notices explicitly exclude them.
        review_path = reviews_root / cohort / f"{event_id}_review.json"
        if item.get("queue_category") == "COMPLETE" or item.get("stage21_review_status") == "VALID_STAGE21_RECORD_PRESENT":
            genuine = False
            if review_path.is_file():
                try:
                    review_value = json.loads(review_path.read_text(encoding="utf-8"))
                    genuine = isinstance(review_value, dict) and review_value.get("schema_version") == STAGE_2_1_SCHEMA_VERSION
                except (OSError, json.JSONDecodeError):
                    genuine = False
            if not genuine:
                reviewed_without_record.append(key)

    duplicate_queue_ids = sorted(key for key, count in Counter(queue_ids).items() if count > 1)
    inventory_status_mismatches: list[str] = []
    for key in sorted(expected_keys):
        entry = raw_review_inventory.get(key)
        if not isinstance(entry, dict):
            inventory_status_mismatches.append(f"{key}:missing review-inventory entry")
            continue
        if entry.get("cohort") != key.split("/", 1)[0] or entry.get("event_id") != key.split("/", 1)[1]:
            inventory_status_mismatches.append(f"{key}:cohort-qualified identity mismatch")
        # Current repository state is NOT_STARTED/null.  A non-null or
        # non-NOT_STARTED value is not silently treated as human evidence.
        if entry.get("review_status") != "NOT_STARTED" or entry.get("stage2_1_review_file") is not None:
            inventory_status_mismatches.append(key)

    cohort_count_mismatches = tuple(
        f"{cohort}: expected {expected_count}, observed {observed_cohorts.get(cohort, 0)}"
        for cohort, expected_count in EXPECTED_COHORT_COUNTS.items()
        if observed_cohorts.get(cohort, 0) != expected_count
    )

    notes = (
        "Queue and review inventory were read only.",
        "Media paths and inventory media hashes were not opened, decoded, or recomputed.",
        "Legacy review JSON files are not genuine Stage-2.1 records; verified notices exclude them.",
    )
    return ReviewQueueAudit(
        queue_path=str(queue_file),
        inventory_path=str(inventory_file),
        total_events=len(raw_items),
        expected_event_count=len(expected_keys),
        duplicate_event_keys=duplicate_keys,
        missing_event_keys=missing_keys,
        unexpected_event_keys=unexpected_keys,
        cohort_mismatches=tuple(sorted(set(cohort_mismatches))),
        duplicate_queue_ids=tuple(duplicate_queue_ids),
        synthetic_event_keys=tuple(sorted(set(synthetic_keys))),
        incorrect_proposal_references=tuple(sorted(set(incorrect_proposals))),
        invalid_invalidation_notices=tuple(sorted(set(invalid_notices))),
        missing_invalidation_notices=tuple(sorted(set(missing_notices))),
        reviewed_without_genuine_record=tuple(sorted(set(reviewed_without_record))),
        inventory_status_mismatches=tuple(sorted(set(inventory_status_mismatches))),
        cohort_count_mismatches=cohort_count_mismatches,
        queue_category_counts=dict(sorted(category_counts.items())),
        notes=notes,
    )


def render_audit_markdown(audit: ReviewQueueAudit) -> str:
    """Render a concise audit without exposing candidate labels."""
    result = audit.to_dict()
    lines = [
        "# Stage-2.1 Review Queue Read-Only Audit",
        "",
        "> This report validates metadata and JSON references only. It is not human review, approval, or promotion.",
        "",
        f"- Result: **{result['status']}**",
        f"- Events: `{audit.total_events}` observed / `{audit.expected_event_count}` expected",
        f"- Media accessed: **no**",
        f"- Queue categories: `{dict(audit.queue_category_counts)}`",
        "",
        "## Findings",
    ]
    finding_fields = (
        "duplicate_event_keys", "missing_event_keys", "unexpected_event_keys", "cohort_mismatches",
        "duplicate_queue_ids", "synthetic_event_keys", "incorrect_proposal_references",
        "invalid_invalidation_notices", "missing_invalidation_notices",
        "reviewed_without_genuine_record", "inventory_status_mismatches",
        "cohort_count_mismatches",
    )
    for field_name in finding_fields:
        values = result[field_name]
        lines.append(f"- `{field_name}`: `{values}`")
    lines.extend(["", "## Scope notes", *[f"- {note}" for note in audit.notes], ""])
    return "\n".join(lines)