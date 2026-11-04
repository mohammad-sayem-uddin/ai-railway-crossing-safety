"""Lossless constructed boundary projections, never complete/promotable reviews.

The original exact PTS/uncertainty/censoring body accompanies every projection.
No approval status, human attestation, proposal binding or source hash is filled.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from railway_detection.annotation.human_review_domain import BOUNDARIES, ReviewWorkflow, digest
from railway_detection.annotation.schemas import CANONICAL_TIMESTAMPS
from railway_detection.annotation.stage2_1_schema import (
    STAGE_2_1_SCHEMA_VERSION,
    BoundaryAdjudication,
)
from railway_detection.annotation.stage2_1_schema_proposed import (
    PROPOSED_SCHEMA_VERSION,
    BoundaryObservation,
)


def project_constructed_boundaries(
    observations,
    *,
    target_schema,
    expected_body_digest,
    evidence_statuses,
    not_observable_reasons=(),
):
    body = ReviewWorkflow._body(observations)
    if digest(body) != expected_body_digest:
        raise ValueError("independent exact observation body binding mismatch")
    if target_schema not in {STAGE_2_1_SCHEMA_VERSION, PROPOSED_SCHEMA_VERSION}:
        raise ValueError("unsupported version; no implicit schema adoption")
    statuses = dict(evidence_statuses)
    if (
        len(evidence_statuses) != len(BOUNDARIES)
        or set(statuses) != set(BOUNDARIES)
        or any(value not in {"PRESENT", "MISSING", "INSUFFICIENT"} for value in statuses.values())
    ):
        raise ValueError("explicit complete constructed evidence status fields required")
    reasons = dict(not_observable_reasons)
    not_observable = {o.boundary for o in observations if o.state == "NOT_OBSERVABLE"}
    if target_schema == PROPOSED_SCHEMA_VERSION and (
        len(reasons) != len(not_observable_reasons) or set(reasons) != not_observable
    ):
        raise ValueError("explicit proposed-schema not-observable reasons required")
    projected = {}
    by_name = {o.boundary: o for o in observations}
    for local, canonical_name in zip(BOUNDARIES, CANONICAL_TIMESTAMPS, strict=True):
        observation = by_name[local]
        if observation.value_us is not None and observation.value_us > 3_600_000_000:
            raise ValueError("constructed adapter tested one-hour clock bound exceeded")
        seconds = None if observation.value_us is None else observation.value_us / 1_000_000
        if observation.state == "OBSERVABLE" and statuses[local] != "PRESENT":
            raise ValueError("observable point requires supplied present evidence status")
        if target_schema == STAGE_2_1_SCHEMA_VERSION:
            state = (
                "UNOBSERVABLE_NOT_APPLICABLE"
                if observation.state == "NOT_OBSERVABLE"
                else observation.state
            )
            projected[canonical_name] = asdict(
                BoundaryAdjudication(
                    state, observation.rationale, seconds, observation.camera, None
                )
            )
        else:
            projected[canonical_name] = BoundaryObservation(
                state=observation.state,
                rationale=observation.rationale,
                evidence_status=statuses[local],
                value_s=seconds,
                reference_camera=observation.camera,
                frame_index=None,
                censoring_direction=observation.censoring_direction,
                timestamp_uncertainty_s=(
                    None
                    if observation.uncertainty_us is None
                    else observation.uncertainty_us / 1_000_000
                ),
                not_observable_reason=reasons.get(local),
            ).to_dict()
    return {
        "schema": "CONSTRUCTED_BOUNDARY_PROJECTION_V1",
        "target_boundary_schema": target_schema,
        "active_schema_satisfied": False,
        "human_review_record": False,
        "source_body_digest": expected_body_digest,
        "exact_source_body": json.loads(body),
        "evidence_statuses": statuses,
        "projected_boundaries": projected,
        "limitations": "boundary projection only; missing human/approval/source/protocol evidence; "
        "legacy projection requires exact sidecar to retain structured timing",
    }


def promote_projection(*args, **kwargs):
    raise PermissionError("Constructed projections cannot satisfy an active review or GT promotion")
