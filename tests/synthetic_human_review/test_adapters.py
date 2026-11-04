from dataclasses import replace

import pytest

from railway_detection.annotation.human_review_adapter import (
    project_constructed_boundaries,
    promote_projection,
)
from railway_detection.annotation.human_review_domain import (
    BOUNDARIES,
    Observation,
    ReviewWorkflow,
    digest,
)


def fixture():
    states = (
        "OBSERVABLE",
        "UNCERTAIN",
        "NOT_OBSERVABLE",
        "CENSORED",
        "OBSERVABLE",
        "NOT_OBSERVABLE",
    )
    observations = tuple(
        Observation(
            name,
            "front",
            state,
            "constructed source",
            value_us=(100001 if name == "T0" else 4000001) if state == "OBSERVABLE" else None,
            censoring_direction="RIGHT" if state == "CENSORED" else None,
            uncertainty_us=7,
        )
        for name, state in zip(BOUNDARIES, states, strict=True)
    )
    return observations


def project(observations, target):
    return project_constructed_boundaries(
        observations,
        target_schema=target,
        expected_body_digest=digest(ReviewWorkflow._body(observations)),
        evidence_statuses=tuple(
            (k, "PRESENT" if o.state == "OBSERVABLE" else "INSUFFICIENT")
            for k, o in zip(BOUNDARIES, observations, strict=True)
        ),
        not_observable_reasons=(
            ("T2", "landmark_not_defined"),
            ("SCENE_CLEAR", "not_visible_in_recording"),
        ),
    )


@pytest.mark.parametrize("target", ["8.1.0-stage2.1", "8.2.0-stage2.1-proposed"])
def test_lossless_sidecar_and_four_states_without_fabricated_metadata(target):
    result = project(fixture(), target)
    assert result["exact_source_body"][3]["censoring_direction"] == "RIGHT"
    assert result["exact_source_body"][0]["value_us"] == 100001
    assert result["active_schema_satisfied"] is False and result["human_review_record"] is False
    assert result["projected_boundaries"]["T4_tail_clearance"]["value_s"] == 4.000001
    assert all(x["frame_index"] is None for x in result["projected_boundaries"].values())
    assert "APPROVED" not in str(result)
    with pytest.raises(PermissionError):
        promote_projection(result, approved=True)


def test_schema_identity_and_binding_cannot_be_coerced():
    with pytest.raises(ValueError, match="unsupported version"):
        project(fixture(), "8.2.0-stage2.1")
    with pytest.raises(ValueError, match="binding"):
        project_constructed_boundaries(
            fixture(),
            target_schema="8.1.0-stage2.1",
            expected_body_digest="0" * 64,
            evidence_statuses=(),
        )


def test_proposed_missing_reasons_or_false_evidence_denied():
    observations = fixture()
    kwargs = dict(
        target_schema="8.2.0-stage2.1-proposed",
        expected_body_digest=digest(ReviewWorkflow._body(observations)),
    )
    with pytest.raises(ValueError, match="reasons"):
        project_constructed_boundaries(
            observations, **kwargs, evidence_statuses=tuple((k, "PRESENT") for k in BOUNDARIES)
        )
    with pytest.raises(ValueError, match="present evidence"):
        project_constructed_boundaries(
            observations,
            target_schema="8.1.0-stage2.1",
            expected_body_digest=kwargs["expected_body_digest"],
            evidence_statuses=tuple((k, "MISSING") for k in BOUNDARIES),
        )


def test_large_clocks_not_silently_overflowed():
    observations = fixture()
    observations = (
        observations[:-2] + (replace(observations[-2], value_us=3_600_000_001),) + observations[-1:]
    )
    with pytest.raises(ValueError, match="one-hour"):
        project(observations, "8.1.0-stage2.1")
