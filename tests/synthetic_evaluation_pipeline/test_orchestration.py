from dataclasses import replace

import pytest

from railway_detection.evaluation.descriptive_constructed import (
    ConstructedDescriptiveJob,
    run_constructed_descriptive,
    run_real_descriptive,
)
from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.synthetic.convention_b_pipeline import (
    ConstructedBatch,
    ConstructedInput,
    IntegrationRequest,
)


def job(camera="back", condition="B0_back"):
    b = ConstructedBatch.build(
        "synthetic:descriptive",
        tuple(
            ConstructedInput("synthetic:frame:" + str(i), t, MultimodalFrame(t / 1_000_000))
            for i, t in enumerate([0, 2000000, 4000000])
        ),
        provenance="CONSTRUCTED_IN_MEMORY",
    )
    q = IntegrationRequest.prepare(
        b, MultimodalDecisionEngine(), mode="ARRIVAL", code_identity="synthetic:code:21"
    )
    return ConstructedDescriptiveJob("train_events/event_001", camera, condition, q, 4000000)


def test_independent_camera_denominators_and_determinism():
    a = job()
    b = job("front", "B0_front")
    r = run_constructed_descriptive((a, b), expected_controller_json=a.request.controller_json)
    assert len(r["runs"]) == 2 and len(r["metrics"]) == 4
    assert all(x["denominator"] == 1 for x in r["metrics"] if x["metric"] == "M5")
    assert r == run_constructed_descriptive(
        (a, b), expected_controller_json=a.request.controller_json
    )
    assert r["official_eligibility"] is False


@pytest.mark.parametrize("condition", ["B0", "B2_back", "B0_back_stateless", "R04_fused"])
def test_unmapped_deferred_conditions_not_silently_reused(condition):
    a = replace(job(), condition=condition)
    with pytest.raises(ValueError):
        run_constructed_descriptive((a,), expected_controller_json=a.request.controller_json)


def test_incomplete_or_missing_human_boundary_never_becomes_zero():
    a = replace(job(), constructed_t4_us=None)
    r = run_constructed_descriptive((a,), expected_controller_json=a.request.controller_json)
    assert all(x["denominator"] == 0 for x in r["metrics"])
    assert all(x["excluded_by_reason"] == {"t4_missing": 1} for x in r["metrics"])


def test_no_real_path_authorized_by_a_constructed_pass():
    with pytest.raises(PermissionError):
        run_real_descriptive(approved=True, ready=True)
    a = replace(job(), boundary_evidence="APPROVED_HUMAN_GT")
    with pytest.raises(ValueError):
        run_constructed_descriptive((a,), expected_controller_json=a.request.controller_json)


def test_audio_perceptual_only_and_duplicate_denominator_rejection():
    a = job("front", "B1_audio")
    r = run_constructed_descriptive((a,), expected_controller_json=a.request.controller_json)
    assert (
        r["metrics"] == () and r["runs"][0]["gate_metrics"] == "NOT_APPLICABLE_AUDIO_SUPPORT_ONLY"
    )
    with pytest.raises(ValueError):
        run_constructed_descriptive((a, a), expected_controller_json=a.request.controller_json)
