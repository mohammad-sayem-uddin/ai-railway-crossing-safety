"""Phase 5 review-tooling facade (Mission 10 rewrite).

There is exactly ONE promotion-receipt authority: ``railway_detection.annotation.readiness_cli``
(``build_promotion_receipt``), verified by ``railway_detection.evaluation.governance``. The
previous ``PromotionReceiptV5`` / ``generate_promotion_receipt`` / ``verify_promotion_receipt``
trio duplicated that authority with a different ``produced_by`` and was rejected by the canonical
verifier; it has been removed rather than patched.

Also removed: the invented second-review triggers (duration, direction, censoring), the
caller-constructed ``AdjudicationOutcome`` and the identical-timestamps ``CONSENSUS`` status.
RD-043 enforcement now lives in ``annotation/second_review.py`` and runs on the actual review
records on disk -- in the readiness gate (producer) and again in the Phase 12 execution gate
(consumer).

What remains here is metadata-only: cohort-qualified event identity, reviewer-identity checks
against the canonical allowlist, timestamp sanity checks and a corpus pre-flight that reports the
RD-043 status of the records on disk without opening any media.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from railway_detection.annotation.evaluation_readiness_gate import _load_review_records
from railway_detection.annotation.promotion_gate import (
    load_authorized_reviewers as load_canonical_allowlist,
)
from railway_detection.annotation.readiness_cli import ReadinessCliError, load_media_context
from railway_detection.annotation.schemas import SchemaValidationError
from railway_detection.annotation.second_review import SecondReviewFinding, assess_second_reviews
from railway_detection.annotation.stage2_1_schema import (
    REVIEWER_ID_BLOCKLIST,
    STAGE_2_1_SCHEMA_VERSION,
    build_stage2_1_record_from_dict,
)
from railway_detection.evaluation.metrics import resolve_event_cohort

EXTENDED_AGENT_BLOCKLIST = REVIEWER_ID_BLOCKLIST | frozenset(
    {
        "gemini_annotator",
        "researcher_agent",
        "batch_annotator",
        "llm_annotator",
        "synthetic_runner",
        "claude_opus",
        "claude_sonnet",
        "gemini",
        "gpt",
        "model",
        "alice",
        "bob",
    }
)


class ReviewToolingError(Exception):
    """Base exception for review tooling and validation failures."""


class ReviewerNotAuthorizedError(ReviewToolingError):
    """Raised when a reviewer is missing from the allowlist or is blocklisted."""


class SecondReviewRequiredError(ReviewToolingError):
    """Raised when RD-043 second review is required but unsatisfied."""


class PromotionViolation(ReviewToolingError):
    """Raised when promotion criteria are violated."""


@dataclass(frozen=True)
class ReviewEventIdentity:
    """Cohort-qualified event identity."""

    cohort: str
    event_id: str

    @property
    def qualified_key(self) -> str:
        return f"{self.cohort}/{self.event_id}"

    @classmethod
    def parse(cls, raw: str) -> ReviewEventIdentity:
        """Parse and validate cohort-qualified event identity using canonical rules."""
        if not isinstance(raw, str) or not raw.strip():
            raise ReviewToolingError("Event identity cannot be empty")
        raw_clean = raw.strip()
        if "/" not in raw_clean:
            raise PromotionViolation(
                f"Bare event ID {raw_clean!r} rejected; must be cohort-qualified '<cohort>/<event>'"
            )
        resolved_cohort = resolve_event_cohort(raw_clean)
        _, _, eid = raw_clean.partition("/")
        return cls(cohort=resolved_cohort, event_id=eid)


def validate_reviewer_identity(
    reviewer_id: str,
    allowlist_path: Path | str,
) -> tuple[bool, str]:
    """Validate a reviewer against the blocklist and the canonical on-disk allowlist.

    The canonical allowlist (``promotion_gate.load_authorized_reviewers``) is the only authority;
    no alternative allowlist format and no role concept is accepted.
    """
    cleaned_id = str(reviewer_id).strip()
    if not cleaned_id:
        return False, "Reviewer ID cannot be empty"
    if cleaned_id.lower() in EXTENDED_AGENT_BLOCKLIST:
        return False, f"Reviewer ID '{cleaned_id}' is explicitly blocklisted as automated/agent"
    path = Path(allowlist_path)
    if not path.is_file():
        return False, f"Authorized reviewers allowlist not found at {path}"
    try:
        allowed = load_canonical_allowlist(path)
    except Exception as exc:
        return False, f"Failed to load allowlist {path}: {exc}"
    if cleaned_id in allowed:
        return True, "Authorized"
    return False, f"Reviewer '{cleaned_id}' is not present in authorized reviewers allowlist"


def validate_timestamps_ordering(
    timestamps: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    """Validate that canonical timestamps are non-negative, finite numbers in order."""
    errors: list[str] = []

    # 1. Type and finiteness validation
    normalized_ts: dict[str, float] = {}
    for k, val in timestamps.items():
        if val is None:
            continue
        # Strict rejection of boolean values (bool is subclass of int)
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            errors.append(f"Timestamp {k}={val!r} must be a real number, got {type(val).__name__}")
            continue
        float_val = float(val)
        if math.isnan(float_val) or math.isinf(float_val):
            errors.append(f"Timestamp {k}={val!r} must be finite")
            continue
        if float_val < 0.0:
            errors.append(f"Timestamp {k}={float_val} cannot be negative")
            continue
        # Snap to 1-microsecond grid
        normalized_ts[k] = round(float_val, 6)

    if errors:
        return False, errors

    # 2. Check chronological sequence for shorthand naming t0_s -> t4_s
    shorthand_order = ["t0_s", "t1_s", "t2_s", "t3_s", "t4_s"]
    present_short = [(k, normalized_ts[k]) for k in shorthand_order if k in normalized_ts]
    for i in range(len(present_short) - 1):
        k1, v1 = present_short[i]
        k2, v2 = present_short[i + 1]
        if v1 > v2:
            errors.append(f"Timestamp sequence violation: {k1} ({v1}s) > {k2} ({v2}s)")

    # 3. Check chronological sequence for protocol naming T0 -> T4 -> T_scene_clear
    protocol_order = [
        "T0_first_visible",
        "T1_danger_zone_entry",
        "T2_crossing_occupancy_start",
        "T3_locomotive_unit_clearance",
        "T4_tail_clearance",
        "T_scene_clear",
    ]
    present_proto = [(k, normalized_ts[k]) for k in protocol_order if k in normalized_ts]
    for i in range(len(present_proto) - 1):
        k1, v1 = present_proto[i]
        k2, v2 = present_proto[i + 1]
        if v1 > v2:
            errors.append(f"Timestamp sequence violation: {k1} ({v1}s) > {k2} ({v2}s)")

    return len(errors) == 0, errors


@dataclass(frozen=True)
class ReviewCorpusAssessment:
    """Metadata-only RD-043 pre-flight of the review records on disk."""

    record_count: int
    findings: tuple[SecondReviewFinding, ...]
    evidence: tuple[str, ...]
    schema_problems: tuple[str, ...]

    @property
    def settled(self) -> bool:
        return bool(self.record_count) and not self.findings and not self.schema_problems


def assess_review_corpus(
    reviews_dir: Path | str,
    *,
    allowlist_path: Path | str,
    inventory_path: Path | str,
    repository_root: Path | str,
) -> ReviewCorpusAssessment:
    """Read the ACTUAL review records and report whether RD-043 is satisfied.

    Opens no media: the inventory is read as JSON and never re-hashed. This is a pre-flight; it is
    not a promotion decision and it issues no receipt.
    """
    records, _ = _load_review_records(Path(reviews_dir))
    allowed = load_canonical_allowlist(Path(allowlist_path))
    problems: list[str] = []
    approved: list[dict[str, Any]] = []
    for record in records:
        if record.get("schema_version") != STAGE_2_1_SCHEMA_VERSION:
            problems.append(f"{record.get('event_id')}: legacy or unknown schema")
            continue
        try:
            built = build_stage2_1_record_from_dict(record)
        except (SchemaValidationError, TypeError, AttributeError, ValueError) as exc:
            problems.append(f"{record.get('event_id')}: {exc}")
            continue
        if built.adjudication_status == "APPROVED":
            approved.append(record)
        else:
            problems.append(f"{built.cohort}/{built.event_id}: status {built.adjudication_status}")
    try:
        registry: dict[str, dict[str, str]] | None = load_media_context(Path(inventory_path))[0]
    except ReadinessCliError:
        registry = None
    findings, evidence = assess_second_reviews(
        approved,
        authorized_reviewers=allowed,
        repository_root=Path(repository_root),
        media_sha256_registry=registry,
    )
    return ReviewCorpusAssessment(
        record_count=len(records),
        findings=tuple(findings),
        evidence=tuple(evidence),
        schema_problems=tuple(problems),
    )
