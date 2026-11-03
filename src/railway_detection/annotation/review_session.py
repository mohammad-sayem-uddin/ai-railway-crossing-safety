"""Phase 11.8: review-session record-construction helper.

Connects the operational review workflow to schema ``8.1.0-stage2.1`` so a
researcher can produce a genuinely promotable Stage-2.1 record. This module
is the missing link identified in the Phase 11.7 report: no tool/workflow
previously called ``compute_media_sha256_pair()`` at review time.

Design principles (fail-closed, matching promotion_gate.py conventions):

1. Reviewer authorization is verified BEFORE any record assembly. An
   unauthorized reviewer cannot produce even a partial record.
2. Media hashes are ALWAYS computed live via ``compute_media_sha256_pair()``
   from the actual file paths. Caller-supplied hash strings are never
   accepted -- there is no "trusted manifest" fast path.
3. The assembled dict is validated through
   ``build_stage2_1_record_from_dict()`` before being returned, so a
   structurally invalid record cannot escape this helper.
4. ``review_duration_s`` is never accepted from the caller; the schema
   always re-derives it from the timestamps.
5. This module never reads model outputs, Phase 8-10.1 results, or
   proposal numeric values into the attestation path.

Authorization boundary: this module NEVER writes to
``data/ground_truth/reviews/``, never creates a real record for a real
event, and never calls ``promote_record``.
"""

from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from railway_detection.annotation.promotion_gate import compute_media_sha256_pair
from railway_detection.annotation.stage2_1_schema import (
    STAGE_2_1_SCHEMA_VERSION,
    build_stage2_1_record_from_dict,
)


class ReviewSessionError(Exception):
    """Base error for review-session construction failures."""


class ReviewerNotAuthorizedError(ReviewSessionError):
    """Raised when the reviewer_id is not in the authorized allowlist.

    Raised BEFORE any record assembly occurs -- no partial record is
    constructed or returned for an unauthorized reviewer.
    """

    code = "REVIEWER_NOT_AUTHORIZED"


def build_review_record(
    *,
    event_id: str,
    cohort: str,
    reviewer_id: str,
    authorized_reviewers: frozenset[str],
    review_session_id: str,
    review_start_utc: str,
    review_end_utc: str,
    inspection_tool: str,
    attestation_statement: str,
    attested_at_utc: str,
    front_media_path: Path | str,
    back_media_path: Path | str,
    observed_at_utc: str,
    proposal_file: str,
    proposal_sha256: str,
    boundary_adjudications: dict[str, dict[str, Any]],
    adjudication_status: str,
    review_id: str | None = None,
    supersedes: str | None = None,
    supersedes_sha256: str | None = None,
    supersedes_invalidation_reason: str | None = None,
    second_review_of: str | None = None,
) -> dict[str, Any]:
    """Assembles a complete, schema-valid Stage-2.1 record dict.

    The media hashes are computed LIVE from ``front_media_path`` and
    ``back_media_path`` via ``compute_media_sha256_pair()``. There is no
    parameter to supply pre-computed hashes -- this is deliberate, per the
    Phase 11.8 plan's safety invariant: "No hardcoding hash values; always
    compute live."

    Raises:
        ReviewerNotAuthorizedError: if ``reviewer_id`` is not in
            ``authorized_reviewers`` (checked first, before any assembly).
        FileNotFoundError: if either media file does not exist (from
            ``compute_media_sha256_pair``, fail-closed).
        SchemaValidationError: if the assembled record fails any schema
            check (duration floor, attestation, boundary states, etc.).
    """
    # Gate 1: reviewer authorization BEFORE any record assembly.
    if reviewer_id not in authorized_reviewers:
        raise ReviewerNotAuthorizedError(
            f"REVIEWER_NOT_AUTHORIZED: reviewer_id '{reviewer_id}' is not present in the "
            "authorized-reviewers allowlist. No record is assembled for an unauthorized reviewer."
        )

    # Gate 2: live media hash computation. Never trust a caller-supplied
    # hash; always compute from the actual files at construction time.
    media_hashes = compute_media_sha256_pair(Path(front_media_path), Path(back_media_path))

    if review_id is None:
        review_id = f"review_{event_id}_v1_{datetime.now(UTC).strftime('%Y%m%d')}"

    record_dict: dict[str, Any] = {
        "schema_version": STAGE_2_1_SCHEMA_VERSION,
        "review_id": review_id,
        "event_id": event_id,
        "cohort": cohort,
        "proposal_reference": {
            "proposal_file": proposal_file,
            "proposal_sha256": proposal_sha256,
        },
        "reviewer_metadata": {
            "reviewer_id": reviewer_id,
            "review_session_id": review_session_id,
            "review_start_utc": review_start_utc,
            "review_end_utc": review_end_utc,
            "inspection_tool": inspection_tool,
        },
        "model_independence_attestation": {
            "attested": True,
            "statement": attestation_statement,
            "attested_at_utc": attested_at_utc,
        },
        "reviewer_observed_media_hashes": {
            "front_sha256": media_hashes["front"],
            "back_sha256": media_hashes["back"],
            "observed_at_utc": observed_at_utc,
        },
        "boundary_adjudications": boundary_adjudications,
        "adjudication_status": adjudication_status,
        "adjudication_history": [
            {
                "event": "created",
                "by": reviewer_id,
                "at_utc": review_end_utc,
                "status_set": adjudication_status,
            },
        ],
    }
    if supersedes is not None:
        record_dict["supersedes"] = supersedes
    if supersedes_sha256 is not None:
        record_dict["supersedes_sha256"] = supersedes_sha256
    if supersedes_invalidation_reason is not None:
        record_dict["supersedes_invalidation_reason"] = supersedes_invalidation_reason
    if second_review_of is not None:
        record_dict["second_review_of"] = second_review_of

    # Gate 3: full schema validation before the record can leave this
    # helper. There is no unvalidated return path.
    build_stage2_1_record_from_dict(record_dict)
    return record_dict