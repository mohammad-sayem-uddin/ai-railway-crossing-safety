"""PROPOSED Stage-2.1 review-record schema (Mission 5A, RD-012) -- NOT ACTIVE, NOT APPROVED.

This module is a *proposal* that sits beside the historical, still-authoritative
``stage2_1_schema.py`` (schema ``8.1.0-stage2.1``).  It is imported by **no** gate, loader,
promotion or readiness code, it can create no review record by itself, and its version string
carries ``-proposed`` so it can never satisfy the existing ``8.1.0-stage2.1`` requirement.

Design points (see docs/generated/mission_5a/STAGE21_SCHEMA_PROPOSAL_20261101_M5A.md):

* Four explicit boundary states: ``OBSERVABLE``, ``UNCERTAIN``, ``CENSORED``, ``NOT_OBSERVABLE``.
* Structured ``censoring_direction`` (``LEFT``/``RIGHT``), ``timestamp_uncertainty_s`` (nullable:
  the review tolerance is DEFERRED, RD-012), ``onset_provenance`` (T1/T2 only; a replay-derived
  onset is rejected), ``reference_camera``, ``frame_index``, ``rationale`` and
  ``evidence_status`` on every observation.
* Train direction is recorded per event by the reviewer; it is never inferred from candidates.
* A first and a second reviewer keep **independent** observations.  Adjudication is a separate
  entry that references, and can never overwrite, those observations.
* The review-status vocabulary has **no** ``APPROVED`` value: approval and promotion are
  governance acts outside this schema.
* No reviewer identity is supplied, defaulted or invented here.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any

from railway_detection.annotation.schemas import CANONICAL_TIMESTAMPS

PROPOSED_SCHEMA_VERSION = "8.2.0-stage2.1-proposed"
ACTIVE_SCHEMA_VERSION_NOT_SATISFIED = "8.1.0-stage2.1"  # the proposal never equals this

BOUNDARY_STATES = ("OBSERVABLE", "UNCERTAIN", "CENSORED", "NOT_OBSERVABLE")
CENSORING_DIRECTIONS = ("LEFT", "RIGHT")
NOT_OBSERVABLE_REASONS = (
    "not_applicable_for_cohort",
    "not_visible_in_recording",
    "landmark_not_defined",
)
EVIDENCE_STATUSES = ("PRESENT", "MISSING", "INSUFFICIENT")
REFERENCE_CAMERAS = ("front", "back")
DIRECTION_STATES = ("OBSERVABLE", "UNCERTAIN", "NOT_OBSERVABLE")
TRAIN_DIRECTIONS = ("left_to_right", "right_to_left")
REVIEWER_ROLES = ("FIRST", "SECOND", "AUDIT")
#: No ``APPROVED`` / ``PROMOTED`` value exists on purpose (approval is a separate governance act).
REVIEW_STATUSES = (
    "DRAFT",
    "SUBMITTED",
    "NEEDS_SECOND_REVIEW",
    "DISPUTED",
    "ADJUDICATED_UNCERTAIN",
    "ADJUDICATED_RESOLVED",
)
ONSET_BOUNDARIES = ("T1_danger_zone_entry", "T2_crossing_occupancy_start")
ONSET_BASES = ("HUMAN_VISUAL_LANDMARK", "NOT_ESTABLISHED")
FORBIDDEN_ONSET_BASES = ("REPLAY_DERIVED", "FIRST_BLOCKED", "MODEL_PREDICTION")
COHORTS = ("train_events", "no_train_events", "engine_events")


class ProposedSchemaError(ValueError):
    """The proposed record violates the proposed schema."""


def _finite_nonneg(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProposedSchemaError(f"{name} must be a number")
    if not math.isfinite(value) or value < 0.0:
        raise ProposedSchemaError(f"{name} must be finite and nonnegative")
    return float(value)


@dataclass
class OnsetProvenance:
    """How a T1/T2 onset was established.  ``landmark_description`` is free text by design:
    the physical entry landmark is DEFERRED (RD-006) and is never defaulted here."""

    basis: str
    landmark_description: str | None = None

    def __post_init__(self) -> None:
        if self.basis in FORBIDDEN_ONSET_BASES:
            raise ProposedSchemaError(
                f"onset basis {self.basis!r} is forbidden: onset must be independently "
                "established by a human, never replay- or model-derived"
            )
        if self.basis not in ONSET_BASES:
            raise ProposedSchemaError(f"onset basis must be one of {ONSET_BASES}")
        if self.basis == "HUMAN_VISUAL_LANDMARK" and not (self.landmark_description or "").strip():
            raise ProposedSchemaError("landmark_description is required for HUMAN_VISUAL_LANDMARK")


@dataclass
class BoundaryObservation:
    """One reviewer's observation of one boundary."""

    state: str
    rationale: str
    evidence_status: str
    value_s: float | None = None
    reference_camera: str | None = None
    frame_index: int | None = None
    censoring_direction: str | None = None
    timestamp_uncertainty_s: float | None = None  # tolerance DEFERRED: None is valid
    not_observable_reason: str | None = None
    onset_provenance: OnsetProvenance | None = None

    def __post_init__(self) -> None:
        if self.state not in BOUNDARY_STATES:
            raise ProposedSchemaError(f"state must be one of {BOUNDARY_STATES}")
        if not self.rationale.strip():
            raise ProposedSchemaError("rationale must be non-empty")
        if self.evidence_status not in EVIDENCE_STATUSES:
            raise ProposedSchemaError(f"evidence_status must be one of {EVIDENCE_STATUSES}")
        if self.reference_camera is not None and self.reference_camera not in REFERENCE_CAMERAS:
            raise ProposedSchemaError(f"reference_camera must be one of {REFERENCE_CAMERAS}")
        if self.frame_index is not None and (
            isinstance(self.frame_index, bool)
            or not isinstance(self.frame_index, int)
            or self.frame_index < 0
        ):
            raise ProposedSchemaError("frame_index must be a nonnegative integer")
        if self.timestamp_uncertainty_s is not None:
            _finite_nonneg("timestamp_uncertainty_s", self.timestamp_uncertainty_s)
        if self.state == "OBSERVABLE":
            if self.value_s is None:
                raise ProposedSchemaError("value_s is required when OBSERVABLE")
            _finite_nonneg("value_s", self.value_s)
            if self.reference_camera is None:
                raise ProposedSchemaError("reference_camera is required when OBSERVABLE")
            if self.evidence_status != "PRESENT":
                raise ProposedSchemaError("OBSERVABLE requires evidence_status PRESENT")
        else:
            if self.value_s is not None:
                raise ProposedSchemaError(f"value_s must be None when {self.state}")
        if self.state == "CENSORED":
            if self.censoring_direction not in CENSORING_DIRECTIONS:
                raise ProposedSchemaError("CENSORED requires censoring_direction LEFT or RIGHT")
        elif self.censoring_direction is not None:
            raise ProposedSchemaError("censoring_direction is only valid when CENSORED")
        if self.state == "NOT_OBSERVABLE":
            if self.not_observable_reason not in NOT_OBSERVABLE_REASONS:
                raise ProposedSchemaError(
                    f"NOT_OBSERVABLE requires not_observable_reason in {NOT_OBSERVABLE_REASONS}"
                )
        elif self.not_observable_reason is not None:
            raise ProposedSchemaError("not_observable_reason is only valid when NOT_OBSERVABLE")

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "rationale": self.rationale,
            "evidence_status": self.evidence_status,
            "value_s": self.value_s,
            "reference_camera": self.reference_camera,
            "frame_index": self.frame_index,
            "censoring_direction": self.censoring_direction,
            "timestamp_uncertainty_s": self.timestamp_uncertainty_s,
            "not_observable_reason": self.not_observable_reason,
            "onset_provenance": (
                None
                if self.onset_provenance is None
                else {
                    "basis": self.onset_provenance.basis,
                    "landmark_description": self.onset_provenance.landmark_description,
                }
            ),
        }


@dataclass
class DirectionObservation:
    """Per-event train direction as observed by the reviewer (never copied from candidates)."""

    state: str
    rationale: str
    value: str | None = None

    def __post_init__(self) -> None:
        if self.state not in DIRECTION_STATES:
            raise ProposedSchemaError(f"direction state must be one of {DIRECTION_STATES}")
        if not self.rationale.strip():
            raise ProposedSchemaError("direction rationale must be non-empty")
        if self.state == "OBSERVABLE":
            if self.value not in TRAIN_DIRECTIONS:
                raise ProposedSchemaError(f"direction value must be one of {TRAIN_DIRECTIONS}")
        elif self.value is not None:
            raise ProposedSchemaError("direction value must be None unless OBSERVABLE")


def entry_sha256(
    observations: dict[str, BoundaryObservation], direction: DirectionObservation
) -> str:
    """Canonical SHA-256 over a reviewer's observations (provenance of the independent entry)."""
    payload = {
        "observations": {k: observations[k].to_dict() for k in sorted(observations)},
        "direction": {
            "state": direction.state,
            "value": direction.value,
            "rationale": direction.rationale,
        },
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class ReviewerEntry:
    """One reviewer's independent first-pass observation set."""

    reviewer_id: str
    role: str
    review_status: str
    observations: dict[str, BoundaryObservation]
    direction: DirectionObservation
    entry_sha256: str | None = None  # if given, must match the content (immutability check)
    blind_first_pass: bool = False  # RD-013: candidates not shown for the pilot first pass

    def __post_init__(self) -> None:
        if not self.reviewer_id.strip():
            raise ProposedSchemaError("reviewer_id must be supplied by the caller, never defaulted")
        if self.role not in REVIEWER_ROLES:
            raise ProposedSchemaError(f"role must be one of {REVIEWER_ROLES}")
        if self.review_status not in REVIEW_STATUSES:
            raise ProposedSchemaError(
                f"review_status must be one of {REVIEW_STATUSES} (no APPROVED value exists)"
            )
        missing = [k for k in CANONICAL_TIMESTAMPS if k not in self.observations]
        extra = [k for k in self.observations if k not in CANONICAL_TIMESTAMPS]
        if missing or extra:
            raise ProposedSchemaError(f"observations keys invalid: missing={missing} extra={extra}")
        for name, obs in self.observations.items():
            if obs.onset_provenance is not None and name not in ONSET_BOUNDARIES:
                raise ProposedSchemaError("onset_provenance is only valid on T1/T2")
            observable_onset = name in ONSET_BOUNDARIES and obs.state == "OBSERVABLE"
            if observable_onset and obs.onset_provenance is None:
                raise ProposedSchemaError(f"{name} OBSERVABLE requires onset_provenance")
            if (
                name in ONSET_BOUNDARIES
                and obs.onset_provenance is not None
                and obs.state == "OBSERVABLE"
                and obs.onset_provenance.basis != "HUMAN_VISUAL_LANDMARK"
            ):
                raise ProposedSchemaError(f"{name} OBSERVABLE requires a human visual landmark")
        if self.entry_sha256 is not None and self.entry_sha256 != entry_sha256(
            self.observations, self.direction
        ):
            raise ProposedSchemaError("entry_sha256 does not match the reviewer's observations")


@dataclass
class AdjudicationEntry:
    """Separate recorded adjudication.  It references reviewer entries and never rewrites them.

    ``resolutions`` maps a boundary to ``{"state": "UNCERTAIN"|"OBSERVABLE", ...}``; unresolved
    disagreement must stay ``UNCERTAIN`` (RD-045).  The adjudicator identity is supplied by the
    caller and is never defaulted.
    """

    adjudicator_id: str
    resolutions: dict[str, dict[str, Any]]
    rationale: str
    references_entry_sha256: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.adjudicator_id.strip():
            raise ProposedSchemaError("adjudicator_id must be supplied by the caller")
        if not self.rationale.strip():
            raise ProposedSchemaError("adjudication rationale must be non-empty")
        if not self.references_entry_sha256:
            raise ProposedSchemaError("adjudication must reference reviewer entry hashes")
        for name, res in self.resolutions.items():
            if name not in CANONICAL_TIMESTAMPS:
                raise ProposedSchemaError(f"unknown boundary {name!r}")
            if res.get("state") not in ("OBSERVABLE", "UNCERTAIN"):
                raise ProposedSchemaError("adjudicated state must be OBSERVABLE or UNCERTAIN")
            if res["state"] == "OBSERVABLE" and not isinstance(res.get("value_s"), (int, float)):
                raise ProposedSchemaError("an OBSERVABLE adjudication needs value_s")


@dataclass
class ProposedStage21Record:
    """A whole proposed record.  Synthetic use only until a future mission authorizes review."""

    event_id: str
    cohort: str
    reviewers: list[ReviewerEntry]
    adjudication: AdjudicationEntry | None = None
    schema_version: str = PROPOSED_SCHEMA_VERSION
    notes: str = field(default="PROPOSED SCHEMA INSTANCE -- NOT A REVIEW RECORD")

    def __post_init__(self) -> None:
        if self.schema_version != PROPOSED_SCHEMA_VERSION:
            raise ProposedSchemaError(f"schema_version must be {PROPOSED_SCHEMA_VERSION}")
        if self.cohort not in COHORTS:
            raise ProposedSchemaError(f"cohort must be one of {COHORTS}")
        head, sep, tail = self.event_id.partition("/")
        if not sep or head != self.cohort or not tail.strip() or "/" in tail:
            raise ProposedSchemaError("event_id must be cohort-qualified '<cohort>/<event>'")
        if not self.reviewers:
            raise ProposedSchemaError("at least one reviewer entry is required")
        ids = [r.reviewer_id for r in self.reviewers]
        if len(set(ids)) != len(ids):
            raise ProposedSchemaError("reviewer entries must come from distinct reviewers")
        roles = [r.role for r in self.reviewers]
        if roles.count("FIRST") > 1 or roles.count("SECOND") > 1:
            raise ProposedSchemaError("at most one FIRST and one SECOND reviewer entry")
        if "SECOND" in roles and "FIRST" not in roles:
            raise ProposedSchemaError("a SECOND entry requires a FIRST entry")
        if self.adjudication is not None:
            known = {
                r.entry_sha256 or entry_sha256(r.observations, r.direction) for r in self.reviewers
            }
            if not set(self.adjudication.references_entry_sha256) <= known:
                raise ProposedSchemaError("adjudication references an unknown reviewer entry")
