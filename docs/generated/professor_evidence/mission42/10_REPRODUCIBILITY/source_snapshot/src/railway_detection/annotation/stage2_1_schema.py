"""Phase 11.2: the Stage-2.1 ground-truth review-record schema.

Supersedes, for promotion purposes, the `schema_version: "7.0.0"` review
records investigated in Phase 11.1 (`docs/PHASE11_1_ANNOTATION_INTEGRITY_AUDIT.md`)
and specified in `docs/PHASE11_1_REMEDIATION_PLAN.md` Section 3. A
`schema_version: "7.0.0"` record is, by construction, never a valid
Stage-2.1 record -- `Stage21ReviewRecord` has no code path that accepts one,
so the promotion gate (`promotion_gate.py`) rejects every legacy record
outright rather than attempting to partially validate it.

This module builds and validates individual records. It never reads,
writes, or modifies any file under `data/ground_truth/reviews/`; callers
(tests, or a future researcher-run tool) are responsible for all I/O.

Reuses `fusion`-unrelated, already-established conventions from
`schemas.py` (SHA-256 validation, `SchemaValidationError`,
`CANONICAL_TIMESTAMPS`) rather than inventing parallel ones, per the Phase
11.2 brief's instruction to use documented terminology consistently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

from railway_detection.annotation.schemas import (
    CANONICAL_TIMESTAMPS,
    SchemaValidationError,
    validate_sha256,
)

STAGE_2_1_SCHEMA_VERSION = "8.1.0-stage2.1"
# Bumped from "8.0.0-stage2.1" in Phase 11.7: adds the required
# `reviewer_observed_media_hashes` field (Decision 4, media-hash
# verification at review time -- see `ReviewerObservedMediaHashes` below
# and `promotion_gate.py`'s promotion-time re-verification against it). A
# "8.0.0-stage2.1" record is, by the same logic that already rejects
# "7.0.0" records, never a valid record under this version -- there is no
# migration path that silently fills in a missing media-hash observation.

# A review session shorter than this cannot plausibly reflect the
# frame-by-frame visual and spectral-audio inspection this protocol
# requires for a single event. This is a FLOOR, not a claim of
# sufficiency: clearing it does not by itself prove a review was genuine,
# only that it was not obviously too fast to have occurred. Matches the
# constant independently established in Phase 11.1's
# `integrity_safeguard.py` (documented there as derived from the records'
# own stated per-event methodology, not tuned to any score).
MIN_PLAUSIBLE_REVIEW_DURATION_S = 30.0

# Known-bad reviewer identifiers: role labels or placeholders previously
# used in the invalidated 27 records, or generic terms that cannot
# individually attribute a review to a specific human. Phase 11.1 found
# "human_researcher_lead" used identically across all 27 fabricated
# records; this blocklist exists specifically so that string can never be
# accepted as a valid reviewer_id again, alongside other obvious
# non-identifiers.
REVIEWER_ID_BLOCKLIST = frozenset({
    "human_researcher_lead", "human_annotator", "annotator", "reviewer",
    "unknown", "system", "ai", "assistant", "human", "researcher",
    "n/a", "na", "tbd", "",
})

BOUNDARY_STATES = (
    "OBSERVABLE",
    "UNOBSERVABLE_NOT_APPLICABLE",
    "CENSORED",
    "UNCERTAIN",
)

ADJUDICATION_STATUSES = (
    "APPROVED",
    "REJECTED",
    "NEEDS_SECOND_REVIEW",
    "DISPUTED",
)

_UNRESOLVED_STATUSES = frozenset({"NEEDS_SECOND_REVIEW", "DISPUTED"})


def _parse_utc(value: str, field_name: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise SchemaValidationError(f"{field_name} must be a non-empty ISO-8601 string")
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise SchemaValidationError(f"{field_name} is not a valid ISO-8601 timestamp: '{value}'") from exc
    if dt.tzinfo is None:
        raise SchemaValidationError(f"{field_name} must be timezone-aware (e.g. end in 'Z' or '+00:00'): '{value}'")
    return dt.astimezone(UTC)


@dataclass
class ProposalBinding:
    """Exact binding to a specific proposal version. Currency against the
    LIVE proposal directory (i.e. "is this still the active version") is a
    promotion-time concern requiring external state and is checked in
    `promotion_gate.py`, not here -- this class only validates internal
    well-formedness."""

    proposal_file: str
    proposal_sha256: str

    def __post_init__(self) -> None:
        if not self.proposal_file:
            raise SchemaValidationError("proposal_reference.proposal_file must be non-empty")
        self.proposal_sha256 = validate_sha256(self.proposal_sha256, "proposal_reference.proposal_sha256")

    def to_dict(self) -> dict[str, Any]:
        return {"proposal_file": self.proposal_file, "proposal_sha256": self.proposal_sha256}


@dataclass
class ReviewerMetadata:
    reviewer_id: str
    review_session_id: str
    review_start_utc: str
    review_end_utc: str
    inspection_tool: str
    review_duration_s: float = field(init=False)

    def __post_init__(self) -> None:
        if self.reviewer_id.strip().lower() in REVIEWER_ID_BLOCKLIST:
            raise SchemaValidationError(
                f"reviewer_id '{self.reviewer_id}' is a role label or placeholder, not an individually "
                "attributable reviewer identity. See docs/PHASE11_1_ANNOTATION_INTEGRITY_AUDIT.md."
            )
        if not self.review_session_id.strip():
            raise SchemaValidationError("review_session_id must be non-empty")
        if not self.inspection_tool.strip():
            raise SchemaValidationError("inspection_tool must describe the actual tool/command used")

        start = _parse_utc(self.review_start_utc, "review_start_utc")
        end = _parse_utc(self.review_end_utc, "review_end_utc")
        if end <= start:
            raise SchemaValidationError(
                f"review_end_utc ({self.review_end_utc}) must be strictly after review_start_utc ({self.review_start_utc})"
            )
        duration = (end - start).total_seconds()
        if duration < MIN_PLAUSIBLE_REVIEW_DURATION_S:
            raise SchemaValidationError(
                f"review session duration ({duration:.1f}s) is below the minimum plausible threshold "
                f"({MIN_PLAUSIBLE_REVIEW_DURATION_S}s) for a genuine frame-by-frame review. "
                "A timestamp alone is not proof of a genuine review; this check rejects sessions too "
                "short to have plausibly occurred."
            )
        self.review_duration_s = duration

    def to_dict(self) -> dict[str, Any]:
        return {
            "reviewer_id": self.reviewer_id, "review_session_id": self.review_session_id,
            "review_start_utc": self.review_start_utc, "review_end_utc": self.review_end_utc,
            "review_duration_s": self.review_duration_s, "inspection_tool": self.inspection_tool,
        }


@dataclass
class ReviewerObservedMediaHashes:
    """Phase 11.7, Decision 4: the reviewer's OWN full-file SHA-256
    observation of the exact raw media they reviewed, recorded at review
    time and bound into the record itself -- so promotion-time
    verification (`promotion_gate.py`) has something to re-check the live
    file against that is not merely "whatever a trusted manifest says,"
    and that cannot be satisfied by editing a path string alone, since it
    is a content hash, not a reference.

    This is a SEPARATE hash from the legacy-invalidation proposal hash
    used in `invalidation_notice_writer.py` (Phase 11.6C) -- that one
    binds a disposition proposal to the document a human reviewed; this
    one binds a ground-truth review to the raw video a human watched.
    Conflating the two would be a real error, not a naming coincidence."""

    front_sha256: str
    back_sha256: str
    observed_at_utc: str

    def __post_init__(self) -> None:
        self.front_sha256 = validate_sha256(self.front_sha256, "reviewer_observed_media_hashes.front_sha256")
        self.back_sha256 = validate_sha256(self.back_sha256, "reviewer_observed_media_hashes.back_sha256")
        _parse_utc(self.observed_at_utc, "reviewer_observed_media_hashes.observed_at_utc")

    def to_dict(self) -> dict[str, Any]:
        return {
            "front_sha256": self.front_sha256, "back_sha256": self.back_sha256,
            "observed_at_utc": self.observed_at_utc,
        }


@dataclass
class ModelIndependenceAttestation:
    attested: bool
    statement: str
    attested_at_utc: str

    def __post_init__(self) -> None:
        if not self.attested:
            raise SchemaValidationError(
                "model_independence_attestation.attested must be true -- a Stage-2.1 record cannot be "
                "constructed for a review that does not attest independence from model predictions"
            )
        if len(self.statement.strip()) < 20:
            raise SchemaValidationError(
                "model_independence_attestation.statement must be a specific, non-boilerplate statement "
                "(>= 20 characters), not a placeholder"
            )
        _parse_utc(self.attested_at_utc, "model_independence_attestation.attested_at_utc")

    def to_dict(self) -> dict[str, Any]:
        return {"attested": self.attested, "statement": self.statement, "attested_at_utc": self.attested_at_utc}


@dataclass
class BoundaryAdjudication:
    """One $T_0$-$T_4$/$T_{scene\\_clear}$ boundary's final, human-adjudicated
    state, using the explicit four-state taxonomy formalized in
    `docs/PHASE11_GROUND_TRUTH_PROTOCOL.md` Section 2 (Observable /
    Unobservable-Not-Applicable / Censored / Uncertain), rather than the
    prior schema's implicit `applicable`/`candidate_observable`/
    `ambiguity_flag` combination."""

    state: str
    rationale: str
    value_s: float | None = None
    reference_camera: str | None = None
    frame_index: int | None = None

    def __post_init__(self) -> None:
        if self.state not in BOUNDARY_STATES:
            raise SchemaValidationError(f"state must be one of {BOUNDARY_STATES}, got '{self.state}'")
        if not self.rationale.strip():
            raise SchemaValidationError("rationale must be non-empty for every boundary adjudication")
        if self.state == "OBSERVABLE":
            if self.value_s is None:
                raise SchemaValidationError("value_s is required when state is OBSERVABLE")
            if self.reference_camera not in ("front", "back"):
                raise SchemaValidationError(
                    f"reference_camera must be 'front' or 'back' when state is OBSERVABLE, got '{self.reference_camera}'"
                )
        else:
            if self.value_s is not None:
                raise SchemaValidationError(f"value_s must be None when state is {self.state}, got {self.value_s}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state, "rationale": self.rationale, "value_s": self.value_s,
            "reference_camera": self.reference_camera, "frame_index": self.frame_index,
        }


@dataclass
class AdjudicationHistoryEntry:
    event: str
    by: str
    at_utc: str
    status_set: str

    def __post_init__(self) -> None:
        if not self.event.strip():
            raise SchemaValidationError("adjudication_history entry 'event' must be non-empty")
        if not self.by.strip():
            raise SchemaValidationError("adjudication_history entry 'by' must be non-empty")
        if self.by.strip().lower() in REVIEWER_ID_BLOCKLIST:
            raise SchemaValidationError(
                f"adjudication_history entry 'by' ('{self.by}') is on the blocklist "
                f"{sorted(REVIEWER_ID_BLOCKLIST)}; every history entry must identify an attributable human."
            )
        _parse_utc(self.at_utc, "adjudication_history entry 'at_utc'")
        if self.status_set not in ADJUDICATION_STATUSES:
            raise SchemaValidationError(
                f"adjudication_history entry 'status_set' must be one of {ADJUDICATION_STATUSES}, got '{self.status_set}'"
            )

    def to_dict(self) -> dict[str, Any]:
        return {"event": self.event, "by": self.by, "at_utc": self.at_utc, "status_set": self.status_set}


@dataclass
class Stage21ReviewRecord:
    schema_version: str
    review_id: str
    event_id: str
    cohort: str
    proposal_reference: ProposalBinding
    reviewer_metadata: ReviewerMetadata
    model_independence_attestation: ModelIndependenceAttestation
    reviewer_observed_media_hashes: ReviewerObservedMediaHashes
    boundary_adjudications: dict[str, BoundaryAdjudication]
    adjudication_status: str
    adjudication_history: list[AdjudicationHistoryEntry]
    supersedes: str | None = None
    supersedes_sha256: str | None = None
    supersedes_invalidation_reason: str | None = None
    second_review_of: str | None = None

    def __post_init__(self) -> None:
        if self.schema_version != STAGE_2_1_SCHEMA_VERSION:
            raise SchemaValidationError(
                f"schema_version must be exactly '{STAGE_2_1_SCHEMA_VERSION}', got '{self.schema_version}'. "
                "A record with any other schema_version (including the invalidated '7.0.0' records) is "
                "never a valid Stage-2.1 record and must not be coerced into one."
            )
        if not self.review_id.strip():
            raise SchemaValidationError("review_id must be non-empty")
        if not self.event_id.strip():
            raise SchemaValidationError("event_id must be non-empty")
        if self.cohort not in ("train_events", "no_train_events", "engine_events"):
            raise SchemaValidationError(f"cohort must be a known cohort, got '{self.cohort}'")

        missing = [k for k in CANONICAL_TIMESTAMPS if k not in self.boundary_adjudications]
        if missing:
            raise SchemaValidationError(f"boundary_adjudications missing required keys: {missing}")
        extra = [k for k in self.boundary_adjudications if k not in CANONICAL_TIMESTAMPS]
        if extra:
            raise SchemaValidationError(f"boundary_adjudications has unrecognized keys: {extra}")

        if self.adjudication_status not in ADJUDICATION_STATUSES:
            raise SchemaValidationError(
                f"adjudication_status must be one of {ADJUDICATION_STATUSES}, got '{self.adjudication_status}'"
            )

        if not self.adjudication_history:
            raise SchemaValidationError("adjudication_history must be non-empty (append-only, at least one entry)")
        parsed_times = [_parse_utc(e.at_utc, "adjudication_history entry 'at_utc'") for e in self.adjudication_history]
        if parsed_times != sorted(parsed_times):
            raise SchemaValidationError("adjudication_history entries must be chronologically non-decreasing")
        seen_history_keys: set[tuple[str, str, Any, str]] = set()
        for entry, parsed_ts in zip(self.adjudication_history, parsed_times, strict=True):
            hist_key = (entry.event.strip(), entry.by.strip(), parsed_ts, entry.status_set)
            if hist_key in seen_history_keys:
                raise SchemaValidationError(
                    f"adjudication_history contains duplicate entry: event='{entry.event}', "
                    f"by='{entry.by}', at_utc='{entry.at_utc}', status_set='{entry.status_set}'"
                )
            seen_history_keys.add(hist_key)
        if self.adjudication_history[-1].status_set != self.adjudication_status:
            raise SchemaValidationError(
                f"adjudication_history's most recent entry (status_set='{self.adjudication_history[-1].status_set}') "
                f"must match the record's current adjudication_status ('{self.adjudication_status}')"
            )
        has_multi_reviewer_step = any(
            e.event.strip().lower() in ("second_review", "dispute_resolved", "adjudication_resolved")
            for e in self.adjudication_history
        )
        if has_multi_reviewer_step and len(self.adjudication_history) > 1:
            distinct_actors = {e.by.strip() for e in self.adjudication_history}
            if len(distinct_actors) < 2:
                raise SchemaValidationError(
                    "adjudication_history records a second_review or dispute_resolved step, "
                    "but all entries were performed by the same reviewer identity "
                    f"({sorted(distinct_actors)}); independent second review requires a distinct reviewer."
                )

        if self.second_review_of is not None:
            if not self.second_review_of.strip():
                raise SchemaValidationError("second_review_of, if present, must be non-empty")
            if self.second_review_of.strip() == self.review_id.strip():
                raise SchemaValidationError(
                    f"second_review_of ('{self.second_review_of}') cannot reference the record's own review_id"
                )

    @property
    def is_resolved(self) -> bool:
        """True only if the adjudication status reflects a final, non-pending
        outcome. NEEDS_SECOND_REVIEW and DISPUTED are explicitly unresolved --
        see promotion_gate.py, which rejects promotion of unresolved records."""
        return self.adjudication_status not in _UNRESOLVED_STATUSES

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "review_id": self.review_id,
            "event_id": self.event_id,
            "cohort": self.cohort,
            "supersedes": self.supersedes,
            "supersedes_sha256": self.supersedes_sha256,
            "supersedes_invalidation_reason": self.supersedes_invalidation_reason,
            "proposal_reference": self.proposal_reference.to_dict(),
            "reviewer_metadata": self.reviewer_metadata.to_dict(),
            "model_independence_attestation": self.model_independence_attestation.to_dict(),
            "reviewer_observed_media_hashes": self.reviewer_observed_media_hashes.to_dict(),
            "boundary_adjudications": {k: v.to_dict() for k, v in self.boundary_adjudications.items()},
            "adjudication_status": self.adjudication_status,
            "adjudication_history": [e.to_dict() for e in self.adjudication_history],
            "second_review_of": self.second_review_of,
        }


def build_stage2_1_record_from_dict(data: dict[str, Any]) -> Stage21ReviewRecord:
    """Constructs and validates a Stage21ReviewRecord from a plain dict
    (e.g. parsed JSON). Raises SchemaValidationError on any violation --
    this is the single entry point promotion_gate.py uses, so there is no
    second, looser construction path that validation could be bypassed
    through."""
    required_top_level = (
        "schema_version", "review_id", "event_id", "cohort", "proposal_reference",
        "reviewer_metadata", "model_independence_attestation", "reviewer_observed_media_hashes",
        "boundary_adjudications", "adjudication_status", "adjudication_history",
    )
    try:
        for key in required_top_level:
            if key not in data:
                raise KeyError(key)
        proposal_ref = ProposalBinding(**data["proposal_reference"])
        reviewer_meta_in = dict(data["reviewer_metadata"])
        reviewer_meta_in.pop("review_duration_s", None)  # derived field; never trust a caller-supplied value
        reviewer_meta = ReviewerMetadata(**reviewer_meta_in)
        attestation = ModelIndependenceAttestation(**data["model_independence_attestation"])
        media_hashes = ReviewerObservedMediaHashes(**data["reviewer_observed_media_hashes"])
        boundary = {k: BoundaryAdjudication(**v) for k, v in data["boundary_adjudications"].items()}
        history = [AdjudicationHistoryEntry(**e) for e in data["adjudication_history"]]
    except KeyError as exc:
        raise SchemaValidationError(f"Missing required top-level field: {exc}") from exc
    except TypeError as exc:
        raise SchemaValidationError(f"Malformed field structure: {exc}") from exc

    return Stage21ReviewRecord(
        schema_version=data["schema_version"],
        review_id=data["review_id"],
        event_id=data["event_id"],
        cohort=data["cohort"],
        proposal_reference=proposal_ref,
        reviewer_metadata=reviewer_meta,
        model_independence_attestation=attestation,
        reviewer_observed_media_hashes=media_hashes,
        boundary_adjudications=boundary,
        adjudication_status=data["adjudication_status"],
        adjudication_history=history,
        supersedes=data.get("supersedes"),
        supersedes_sha256=data.get("supersedes_sha256"),
        supersedes_invalidation_reason=data.get("supersedes_invalidation_reason"),
        second_review_of=data.get("second_review_of"),
    )
