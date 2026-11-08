from dataclasses import replace
from fractions import Fraction

import pytest

from railway_detection.experiments.provenance_registry import (
    Artifact,
    ExpectedRegistry,
    InnerSplit,
    Prediction,
    Registry,
    digest,
    validate_registry,
    verify_receipt,
)
from railway_detection.synthetic.grouped_cv import (
    RoleContext,
    allocate,
    allocation_policy,
    role_plan,
    validate_dataset,
)


def fixture(dataset_factory):
    d = dataset_factory(labels=(("front",),) * 8)
    p = allocation_policy(k=4, required_support=(("front", 1),))
    a = allocate(d, k=4, required_support=(("front", 1),))
    c = RoleContext(d, a, p, 0, frozen_rule_id="synthetic:frozen")
    role = role_plan(d, a, outer_fold=0, expected_policy=p, frozen_rule_id="synthetic:frozen")
    members = role.training
    split = InnerSplit("synthetic:inner", members[1:], (), members[:1])
    artifact = Artifact("synthetic:model", "BASE_MODEL", split.training, inner_id=split.inner_id)
    event = members[0]
    asset = next(x.asset_id for x in d.assets if x.event_id == event)
    pred = Prediction(
        "synthetic:prediction",
        event,
        asset,
        artifact.artifact_id,
        ("front",),
        (Fraction(1, 2),),
        0,
        split.inner_id,
    )
    registry = Registry(validate_dataset(d).input_digest, (artifact,), (pred,))
    expected = ExpectedRegistry(c, digest(registry), (split,), (event,), ("front",))
    return registry, expected


def bound(registry, expected):
    return replace(expected, registry_digest=digest(registry))


def test_valid_registry_roundtrip_receipt_and_stale_request(dataset_factory):
    r, e = fixture(dataset_factory)
    receipt = validate_registry(r, expected=e)
    assert receipt.score_count == 1 and verify_receipt(receipt, r, expected=e)
    assert not verify_receipt(replace(receipt, score_count=2), r, expected=e)
    with pytest.raises(ValueError):
        validate_registry(replace(r, version="WRONG"), expected=e)
    with pytest.raises(ValueError):
        validate_registry(r, expected=replace(e, registry_digest="0" * 64))


@pytest.mark.parametrize(
    "change",
    [
        "self_fit",
        "self_select",
        "unknown",
        "orphan",
        "cycle",
        "outer_fit",
        "foreign_inner",
        "duplicate",
        "vocabulary",
        "float_score",
        "missing",
        "wrong_asset",
        "foreign_fold",
        "parent_select",
        "unfrozen_refit",
        "none_calibrator",
    ],
)
def test_transitive_and_exact_oof_negatives(dataset_factory, change):
    r, e = fixture(dataset_factory)
    a = r.artifacts[0]
    s = r.predictions[0]
    if change == "self_fit":
        a = replace(a, fit_events=a.fit_events + (s.event_id,))
    if change == "self_select":
        a = replace(a, selection_events=(s.event_id,))
    if change == "unknown":
        a = replace(a, exposure_status="UNKNOWN")
    if change == "orphan":
        a = replace(a, parents=("synthetic:missing",))
    if change == "cycle":
        a = replace(a, parents=(a.artifact_id,))
    if change == "outer_fit":
        a = replace(a, fit_events=(e.context.allocation.assignments[0][0],))
    if change == "foreign_inner":
        s = replace(s, inner_id="synthetic:other")
    if change == "vocabulary":
        s = replace(s, vocabulary=("rear",))
    if change == "float_score":
        s = replace(s, values=(0.5,))
    if change == "wrong_asset":
        s = replace(s, asset_id="synthetic:missing")
    if change == "foreign_fold":
        s = replace(s, outer_fold=True)
    if change == "unfrozen_refit":
        a = replace(a, kind="FINAL_REFIT")
    if change == "none_calibrator":
        a = replace(a, kind="CALIBRATOR")
    arts = (a,)
    if change == "parent_select":
        parent = Artifact("synthetic:init", "INITIALIZATION", selection_events=(s.event_id,))
        arts = (parent, replace(a, parents=(parent.artifact_id,)))
    preds = () if change == "missing" else (s, s) if change == "duplicate" else (s,)
    r = replace(r, artifacts=arts, predictions=preds)
    with pytest.raises(ValueError):
        validate_registry(r, expected=bound(r, e))


def test_inner_oof_calibration_and_final_refit(dataset_factory):
    r, e = fixture(dataset_factory)
    e = replace(e, calibration_mode="INNER_OOF", frozen_rule_id="synthetic:frozen")
    cal = Artifact(
        "synthetic:calibrator",
        "CALIBRATOR",
        fit_events=e.score_events,
        parents=("synthetic:model",),
    )
    refit = Artifact(
        "synthetic:refit", "FINAL_REFIT", fit_events=e.context.allocation.assignments[1:2][0][:1]
    )
    # Refit exposure is retained; score producer remains the independent inner model.
    r = replace(r, artifacts=r.artifacts + (cal,))
    receipt = validate_registry(r, expected=bound(r, e))
    assert receipt.calibration_mode == "INNER_OOF"
    r = replace(r, artifacts=r.artifacts + (replace(refit, fit_events=r.artifacts[0].fit_events),))
    assert validate_registry(r, expected=bound(r, e))


def test_context_policy_and_coherent_role_swap_denied(dataset_factory):
    r, e = fixture(dataset_factory)
    c = replace(e.context, outer_fold=1)
    with pytest.raises(ValueError):
        validate_registry(r, expected=replace(e, context=c))
    c = replace(e.context, policy=allocation_policy(k=2))
    with pytest.raises(ValueError):
        validate_registry(r, expected=replace(e, context=c))


@pytest.mark.parametrize(
    "change", ["dataset", "excluded", "near_duplicate", "asset_parent", "bool_receipt"]
)
def test_registry_source_transform_and_duplicate_binding(dataset_factory, change):
    r, e = fixture(dataset_factory)
    if change == "dataset":
        r = replace(r, dataset_digest="0" * 64)
    elif change == "excluded":
        r = replace(r, excluded_events=e.score_events)
    elif change == "near_duplicate":
        r = replace(r, unresolved_duplicates=("synthetic:near-conflict",))
    elif change == "asset_parent":
        init = Artifact("synthetic:parent", "INITIALIZATION", fit_events=e.score_events)
        r = replace(
            r,
            artifacts=r.artifacts + (init,),
            asset_artifacts=((r.predictions[0].asset_id, (init.artifact_id,)),),
        )
    else:
        receipt = validate_registry(r, expected=e)
        assert not verify_receipt(replace(receipt, score_count=True), r, expected=e)
        return
    with pytest.raises(ValueError):
        validate_registry(r, expected=bound(r, e))


def test_pure_verifier_has_no_loader_or_fit_api():
    import sys

    for module in (
        "torch",
        "cv2",
        "ultralytics",
        "railway_detection.data.split",
        "railway_detection.simulation.runner",
    ):
        assert module not in sys.modules


def test_reserved_calibration_composition(dataset_factory):
    from railway_detection.synthetic.grouped_cv import DatasetRole

    def with_calibration(**kwargs):
        return dataset_factory(
            labels=(("front",),) * 9,
            roles=(DatasetRole.DEVELOPMENT_POOL,) * 8 + (DatasetRole.CALIBRATION_ONLY,),
        )

    r, e = fixture(with_calibration)
    role = role_plan(
        e.context.dataset,
        e.context.allocation,
        expected_policy=e.context.policy,
        outer_fold=0,
        frozen_rule_id="synthetic:frozen",
    )
    cal = Artifact(
        "synthetic:reserved-calibrator",
        "CALIBRATOR",
        fit_events=role.calibration,
        parents=("synthetic:model",),
    )
    r = replace(r, artifacts=r.artifacts + (cal,))
    e = replace(e, calibration_mode="RESERVED_CALIBRATION")
    assert validate_registry(r, expected=bound(r, e)).calibration_mode == "RESERVED_CALIBRATION"
