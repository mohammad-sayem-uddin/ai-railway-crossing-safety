"""Phase 12: approved-Stage-2.1-records-only ground-truth loader.

Fail-closed boundary between ground truth and evaluation. Loads ONLY records
that are schema `8.1.0-stage2.1` AND adjudication_status `APPROVED`. Refuses:

- any other schema_version (legacy 6.0.0/7.0.0 records, candidates);
- candidate proposal files (wrong shape -> refusal, never partial parsing);
- UNCERTAIN boundaries used as if observable (raises, never returns 0.0/NaN);
- censored boundaries used in latency denominators.

No metric in Phase 12 may be computed against data this loader did not yield.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from railway_detection.annotation.schemas import SchemaValidationError
from railway_detection.annotation.stage2_1_schema import (
    STAGE_2_1_SCHEMA_VERSION,
    build_stage2_1_record_from_dict,
)


class GroundTruthLoadError(RuntimeError):
    """Base refusal for any unusable ground-truth source."""


class LegacyRecordRefused(GroundTruthLoadError):
    """A non-8.1.0-stage2.1 record was supplied."""


# Public names used by the Phase 12 report and retained as compatibility
# aliases for callers that prefer the explicit "Error" terminology.
LegacyRecordError = LegacyRecordRefused


class CandidateProposalRefused(GroundTruthLoadError):
    """A Stage-1 candidate proposal was supplied as ground truth."""


class NotApprovedRefused(GroundTruthLoadError):
    """A record whose adjudication_status is not APPROVED was supplied."""


UnapprovedRecordError = NotApprovedRefused


class BoundaryNotComputable(GroundTruthLoadError):
    """A boundary that is censored/uncertain/not-applicable was requested
    as an observable value. Callers must catch this and mark the affected
    metric NOT_COMPUTABLE -- never substitute 0.0 or NaN."""


UncertainBoundaryError = BoundaryNotComputable


@dataclass(frozen=True)
class ApprovedEventGroundTruth:
    event_id: str
    cohort: str
    review_id: str
    reviewer_id: str
    observable_boundaries: dict[str, float]      # boundary -> value_s
    censored_boundaries: tuple[str, ...]
    uncertain_boundaries: tuple[str, ...]
    not_applicable_boundaries: tuple[str, ...]
    # boundary -> camera clock ("front"/"back") its value was annotated on.
    boundary_cameras: dict[str, str] = field(default_factory=dict)
    # The record's own event_id when ``event_id`` has been cohort-qualified.
    record_event_id: str = ""
    # Full-file SHA-256 of the media the reviewer observed (front/back).
    reviewed_media_sha256: dict[str, str] = field(default_factory=dict)

    def observable_value(self, boundary: str) -> float:
        """Return the observable value or raise BoundaryNotComputable."""
        if boundary in self.observable_boundaries:
            return self.observable_boundaries[boundary]
        if boundary in self.censored_boundaries:
            raise BoundaryNotComputable(
                f"{boundary} is CENSORED for event {self.event_id}: excluded "
                "from denominators per protocol, never 0.0 or NaN."
            )
        if boundary in self.uncertain_boundaries:
            raise BoundaryNotComputable(
                f"{boundary} is UNCERTAIN for event {self.event_id}: not observable."
            )
        raise BoundaryNotComputable(
            f"{boundary} is UNOBSERVABLE_NOT_APPLICABLE or unknown for event {self.event_id}."
        )


def load_approved_ground_truth(
    record_dicts: list[dict[str, Any]],
    *,
    qualify_event_ids: bool = False,
) -> list[ApprovedEventGroundTruth]:
    """Convert raw record dicts into approved ground truth, refusing all else.

    ``event_id`` is only unique within a cohort (``event_001`` exists in
    ``train_events``, ``no_train_events`` and ``engine_events``). With
    ``qualify_event_ids`` the identity becomes ``"<cohort>/<event_id>"`` -- the
    key used by the calibration manifest and by official input manifests -- and
    duplicate detection runs on that key.
    """
    out: list[ApprovedEventGroundTruth] = []
    seen_event_ids: set[str] = set()
    for rec in record_dicts:
        if not isinstance(rec, dict):
            raise GroundTruthLoadError("Ground-truth record must be a JSON object")
        version = rec.get("schema_version")
        # Proposal-shaped files are never ground truth, even if a candidate
        # happens to carry an older schema_version.
        is_candidate_shape = any(
            key in rec
            for key in ("proposal_id", "proposed_timestamps", "ai_assistant_metadata")
        ) and "boundary_adjudications" not in rec
        if (
            version is None
            or ("proposal_file" in rec and "boundary_adjudications" not in rec)
            or is_candidate_shape
        ):
            raise CandidateProposalRefused(
                f"Record for event '{rec.get('event_id', '<unknown>')}' is not a "
                f"Stage-2.1 review record; candidate proposals are never ground truth."
            )
        if version != STAGE_2_1_SCHEMA_VERSION:
            raise LegacyRecordRefused(
                f"schema_version '{version}' != '{STAGE_2_1_SCHEMA_VERSION}' for event "
                f"'{rec.get('event_id', '<unknown>')}'. Legacy records are never evaluated against."
            )
        try:
            built = build_stage2_1_record_from_dict(rec)
        except (SchemaValidationError, TypeError, AttributeError, ValueError) as exc:
            raise GroundTruthLoadError(f"Schema-invalid record: {exc}") from exc
        if built.adjudication_status != "APPROVED":
            raise NotApprovedRefused(
                f"Event '{built.event_id}' has status '{built.adjudication_status}'; "
                "only APPROVED records are usable."
            )
        if built.second_review_of is not None:
            # An independent second review (RD-043) verifies a primary record; it is never an
            # additional ground-truth event. It is still schema- and status-validated above.
            continue
        identity = f"{built.cohort}/{built.event_id}" if qualify_event_ids else built.event_id
        if identity in seen_event_ids:
            raise GroundTruthLoadError(
                f"Duplicate approved ground-truth event_id '{identity}' supplied"
            )
        seen_event_ids.add(identity)
        obs: dict[str, float] = {}
        cameras: dict[str, str] = {}
        censored: list[str] = []
        uncertain: list[str] = []
        not_applicable: list[str] = []
        for name, adj in built.boundary_adjudications.items():
            if adj.state == "OBSERVABLE":
                assert adj.value_s is not None  # schema-enforced
                obs[name] = adj.value_s
                assert adj.reference_camera is not None  # schema-enforced
                cameras[name] = adj.reference_camera
            elif adj.state == "CENSORED":
                censored.append(name)
            elif adj.state == "UNCERTAIN":
                uncertain.append(name)
            else:
                not_applicable.append(name)
        out.append(ApprovedEventGroundTruth(
            event_id=identity,
            cohort=built.cohort,
            review_id=built.review_id,
            reviewer_id=built.reviewer_metadata.reviewer_id,
            observable_boundaries=obs,
            censored_boundaries=tuple(sorted(censored)),
            uncertain_boundaries=tuple(sorted(uncertain)),
            not_applicable_boundaries=tuple(sorted(not_applicable)),
            boundary_cameras=cameras,
            record_event_id=built.event_id,
            reviewed_media_sha256={
                "front": built.reviewer_observed_media_hashes.front_sha256,
                "back": built.reviewer_observed_media_hashes.back_sha256,
            },
        ))
    return out


def load_approved_ground_truth_with_hashes(
    reviews_dir: Path, *, qualify_event_ids: bool = False
) -> tuple[list[ApprovedEventGroundTruth], dict[str, str]]:
    """Load every ``*_review.json`` (fail-closed) and return the digest of the exact bytes parsed.

    Each file is read once; the digest and the parsed record come from the same bytes, so a
    caller comparing the digests with an earlier verification cannot be fooled by a swap
    between hashing and parsing. Digest keys are paths relative to ``reviews_dir``.
    """
    if not reviews_dir.exists() or not reviews_dir.is_dir():
        raise GroundTruthLoadError(
            f"Reviews directory does not exist or is not a directory: {reviews_dir}"
        )
    from railway_detection.annotation.notices import (
        excused_legacy_records,
        invalid_notices,
        is_notice_path,
    )

    bad_notices = invalid_notices(reviews_dir)
    if bad_notices:
        raise CandidateProposalRefused(
            f"Invalidation notice {bad_notices[0].notice} failed verification: "
            f"{bad_notices[0].problem}"
        )
    excused = excused_legacy_records(reviews_dir)
    all_json = sorted(reviews_dir.rglob("*.json"))
    review_paths = [
        path
        for path in all_json
        if path.name.endswith("_review.json")
        and path.relative_to(reviews_dir).as_posix() not in excused
    ]
    unexpected = [
        path
        for path in all_json
        if not path.name.endswith("_review.json") and not is_notice_path(path)
    ]
    if unexpected:
        raise CandidateProposalRefused(
            f"Non-review JSON found under reviews directory: {unexpected[0]}; "
            "candidate sources are refused."
        )
    dicts: list[dict[str, Any]] = []
    hashes: dict[str, str] = {}
    for path in review_paths:
        try:
            raw = path.read_bytes()
            value = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise GroundTruthLoadError(f"Could not read review record {path}: {exc}") from exc
        if not isinstance(value, dict):
            raise GroundTruthLoadError(f"Review record {path} must contain a JSON object")
        dicts.append(value)
        hashes[path.relative_to(reviews_dir).as_posix()] = hashlib.sha256(raw).hexdigest()
    return load_approved_ground_truth(dicts, qualify_event_ids=qualify_event_ids), hashes


def load_approved_ground_truth_from_dir(
    reviews_dir: Path, *, qualify_event_ids: bool = False
) -> list[ApprovedEventGroundTruth]:
    """Load every ``*_review.json`` under a reviews directory (fail-closed)."""
    return load_approved_ground_truth_with_hashes(
        reviews_dir, qualify_event_ids=qualify_event_ids
    )[0]
