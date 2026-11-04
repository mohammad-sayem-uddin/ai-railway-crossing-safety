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


def evidence_job(source="camera_back", *, modality=None, metadata_source=None):
    from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality

    a = job()
    evidence = EvidenceRecord(
        0.0, source, modality or Modality.VISION, True, (Detection("rear", 0.9),)
    )
    frame = MultimodalFrame(
        0.0,
        (evidence,),
        source_availability=({} if metadata_source is None else {metadata_source: True}),
    )
    b = ConstructedBatch.build(
        "synthetic:descriptive",
        (ConstructedInput("synthetic:f", 0, frame),),
        provenance="CONSTRUCTED_IN_MEMORY",
    )
    q = IntegrationRequest.prepare(
        b, MultimodalDecisionEngine(), mode="ARRIVAL", code_identity="synthetic:code:21"
    )
    return replace(a, request=q, vision_source_id="camera_back")


def test_exact_source_mapping_accepts_declared_evidence_without_name_inference():
    a = replace(evidence_job("synthetic_neutral_1"), vision_source_id="synthetic_neutral_1")
    assert run_constructed_descriptive((a,), expected_controller_json=a.request.controller_json)


@pytest.mark.parametrize("source", ["camera_front", "back_and_front", "camera_back_shadow"])
def test_camera_substring_does_not_establish_identity(source):
    a = evidence_job(source)
    with pytest.raises(ValueError, match="source/modality"):
        run_constructed_descriptive((a,), expected_controller_json=a.request.controller_json)


def test_modality_swap_and_hidden_source_metadata_denied():
    from railway_detection.fusion.evidence import Modality

    for a in (
        evidence_job(modality=Modality.AUDIO),
        evidence_job(metadata_source="camera_front"),
        replace(evidence_job(), vision_source_id=None),
    ):
        with pytest.raises(ValueError):
            run_constructed_descriptive((a,), expected_controller_json=a.request.controller_json)


@pytest.mark.parametrize(
    "event",
    [
        "event_001",
        "train_events/event_999",
        "engine_events/event_002",
        "no_train_events/event_004",
        "train_events/event_000",
    ],
)
def test_audio_only_rows_also_require_qualified_documented_cohort(event):
    a = replace(job("front", "B1_audio"), event_key=event)
    with pytest.raises(ValueError, match="qualified documented"):
        run_constructed_descriptive((a,), expected_controller_json=a.request.controller_json)
