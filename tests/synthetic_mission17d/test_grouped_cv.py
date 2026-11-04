"""Constructed metadata and independent tiny feasibility oracle only."""

from dataclasses import replace
from itertools import product

import pytest

from railway_detection.synthetic.grouped_cv import (
    Annotation,
    Asset,
    Capture,
    DatasetRole,
    InvalidInput,
    MetadataValue,
    RoleContext,
    Transform,
    allocate,
    allocation_policy,
    role_plan,
    validate_dataset,
    validate_fit_membership,
    verify_allocation,
)


def add_derivative(dataset, *, parents=None, event_id=None):
    original = dataset.assets[0]
    labels = dataset.events[0].labels
    child = Asset("synthetic:derivative:crop", event_id or original.event_id,
                  "DERIVATIVE", ("synthetic:annotation:crop",),
                  parent_ids=parents or (original.asset_id,),
                  transform=Transform("synthetic:transform:crop", "1", (("left", "2"),)))
    ann = Annotation("synthetic:annotation:crop", child.asset_id, labels, not labels)
    return replace(dataset, assets=dataset.assets+(child,), annotations=dataset.annotations+(ann,))


def tiny_feasible(label_sets, k, support):
    """Enumerate only tiny constructed examples, independent of allocator code."""
    for candidate in product(range(k), repeat=len(label_sets)):
        if set(candidate) != set(range(k)):
            continue
        if all(sum(label in label_sets[i] for i, fold in enumerate(candidate) if fold == f)
               >= minimum for label, minimum in support for f in range(k)):
            return True
    return False


def test_alias_camera_versions_and_derivatives_stay_in_one_event_group(dataset_factory):
    d = dataset_factory(counts=(2, 1, 1, 1, 1, 1))
    first = replace(d.events[0], aliases=("synthetic:alias:pass-0",))
    d = replace(d, events=(first,)+d.events[1:])
    d = replace(d, assets=(replace(d.assets[0], event_id=first.aliases[0]),)+d.assets[1:])
    second = Capture("synthetic:capture:second-view", (first.event_id,),
                     camera=MetadataValue("second-camera", None, "synthetic:camera:evidence"))
    assets = list(d.assets)
    assets[1] = replace(assets[1], capture_id=second.capture_id)
    d = replace(d, captures=d.captures+(second,), assets=tuple(assets))
    d = add_derivative(d)
    registry = validate_dataset(d)
    g = registry.groups[0]
    assert g.original_asset_count == 2 and len(g.asset_ids) == 3
    assert dict(registry.aliases)["synthetic:alias:pass-0"] == first.event_id
    result = allocate(d, k=3)
    assert verify_allocation(d, result, expected_policy=allocation_policy(k=3))
    assert len(result.assignments) == 6
    assert first.aliases[0] not in dict(result.assignments)
    assert registry.dataset.assets[-1].transform.parameters == (("left", "2"),)
    assert registry.dataset.captures[-1].camera.value == "second-camera"
    assert registry.dataset.events[0].weather.value == "constructed-dry"
    assert registry.dataset.events[0].lighting.unknown_reason is not None


def test_input_permutation_and_label_parameter_alignment_are_deterministic(dataset_factory):
    d = add_derivative(dataset_factory(labels=(('a', 'b'), ('a',), ('b',), ('a',), ('b',), ('a',))))
    permuted = replace(d, events=tuple(reversed(d.events)), captures=tuple(reversed(d.captures)),
                       assets=tuple(reversed(d.assets)), annotations=tuple(reversed(d.annotations)))
    a = allocate(d, k=3, required_support=(("a", 1),))
    b = allocate(permuted, k=3, required_support=(("a", 1),))
    assert a.canonical_json() == b.canonical_json()
    assert verify_allocation(permuted, a, expected_policy=allocation_policy(
        k=3, required_support=(("a", 1),)))


@pytest.mark.parametrize("bad_id", [None, "", "event_001", "train_events/event_001", True])
def test_missing_or_nonsynthetic_event_identity_denies_before_allocation(dataset_factory, bad_id):
    d = dataset_factory()
    d = replace(d, assets=(replace(d.assets[0], event_id=bad_id),)+d.assets[1:])
    with pytest.raises(ValueError):
        allocate(d, k=3)


def test_duplicate_identity_and_alias_collision_fail_closed(dataset_factory):
    d = dataset_factory()
    for broken in [replace(d, events=d.events+(d.events[0],)),
                   replace(d, assets=d.assets+(d.assets[0],)),
                   replace(d, annotations=d.annotations+(d.annotations[0],)),
                   replace(d, events=(d.events[0], replace(d.events[1],
                           aliases=(d.events[0].event_id,)))+d.events[2:])]:
        with pytest.raises(ValueError):
            allocate(broken, k=3)


def test_invalid_input_has_explicit_status_and_no_allocation(dataset_factory):
    with pytest.raises(InvalidInput) as error:
        allocate(dataset_factory(), k=True)
    assert error.value.status == "INVALID_INPUT"


def test_orphan_cyclic_and_multi_event_derivatives_are_rejected(dataset_factory):
    d = dataset_factory()
    orphan = add_derivative(d, parents=("synthetic:missing:parent",))
    multi = add_derivative(d, parents=(d.assets[0].asset_id, d.assets[1].asset_id))
    t = Transform("synthetic:transform:cycle", "1", ())
    a = replace(d.assets[0], kind="DERIVATIVE", parent_ids=(d.assets[1].asset_id,), transform=t)
    b = replace(d.assets[1], kind="DERIVATIVE", parent_ids=(d.assets[0].asset_id,), transform=t)
    cycle = replace(d, assets=(a, b)+d.assets[2:])
    for broken in (orphan, multi, cycle):
        with pytest.raises(ValueError):
            allocate(broken, k=3)


def test_conflicting_content_annotation_capture_and_transform_identity_reject(dataset_factory):
    d = dataset_factory()
    content = "synthetic:content:shared"
    cross_duplicate = replace(d, assets=(replace(d.assets[0], content_identity=content),
                                         replace(d.assets[1], content_identity=content))+d.assets[2:])
    missing_annotation = replace(d, annotations=d.annotations[1:])
    wrong_annotation = replace(d, annotations=(replace(d.annotations[0],
                                      asset_id=d.assets[1].asset_id),)+d.annotations[1:])
    wrong_capture = replace(d, assets=(replace(d.assets[0],
                                   capture_id=d.captures[1].capture_id),)+d.assets[1:])
    invented_label = replace(d, events=(replace(d.events[0], labels=("invented",)),)+d.events[1:])
    for broken in (cross_duplicate, missing_annotation, wrong_annotation, wrong_capture, invented_label):
        with pytest.raises(ValueError):
            allocate(broken, k=3)
    derivative = add_derivative(d)
    child = derivative.assets[-1]
    conflicting = replace(child, asset_id="synthetic:derivative:second",
                          annotation_ids=("synthetic:annotation:second",),
                          transform=replace(child.transform, version="2"))
    extra_annotation = Annotation("synthetic:annotation:second", conflicting.asset_id, ('front',))
    with pytest.raises(ValueError):
        validate_dataset(replace(derivative, assets=derivative.assets+(conflicting,),
                                  annotations=derivative.annotations+(extra_annotation,)))


def test_explicit_empty_negative_and_video_timing_evidence(dataset_factory):
    d = dataset_factory(labels=((),)*6)
    assert verify_allocation(d, allocate(d, k=3), expected_policy=allocation_policy(k=3))
    with pytest.raises(ValueError):
        validate_dataset(replace(d, annotations=(replace(d.annotations[0], confirmed_empty=False),)
                                                   +d.annotations[1:]))
    d = dataset_factory()
    capture = replace(d.captures[0], kind="VIDEO")
    asset = replace(d.assets[0], kind="ORIGINAL_FRAME", frame_index=0,
                    pts_ticks=0, timebase=(1, 30))
    video = replace(d, captures=(capture,)+d.captures[1:], assets=(asset,)+d.assets[1:])
    assert validate_dataset(video).groups[0].original_asset_count == 1
    for invalid_asset in (replace(asset, timebase=(2, 60)), replace(asset, frame_index=True),
                          replace(asset, pts_ticks=None, timebase=None)):
        with pytest.raises(ValueError):
            validate_dataset(replace(video, assets=(invalid_asset,)+video.assets[1:]))
    unknown = replace(asset, frame_index=None, pts_ticks=None, timebase=None,
                      unavailable_reason="synthetic timing deliberately unavailable")
    assert validate_dataset(replace(video, assets=(unknown,)+video.assets[1:]))


@pytest.mark.parametrize("flag", [True, None, "false", 0])
def test_every_fallback_flag_except_exact_false_is_denied(dataset_factory, flag):
    with pytest.raises(ValueError):
        allocate(dataset_factory(), k=3, allow_ungrouped_fallback=flag)


@pytest.mark.parametrize("k,budget,support", [(True, 10, ()), (1, 10, ()), (-3, 10, ()),
                                            (3, 0, ()), (3, True, ()),
                                            (3, 10, (("front", 0),)),
                                            (3, 10, (("front", True),)),
                                            (3, 10, (("front", 1), ("front", 1)))])
def test_invalid_configuration_is_not_silently_relaxed(dataset_factory, k, budget, support):
    with pytest.raises(ValueError):
        allocate(dataset_factory(), k=k, node_budget=budget, required_support=support)


def test_necessary_infeasibility_and_exact_mixed_label_triangle(dataset_factory):
    rare = allocate(dataset_factory(labels=(('rare',), (), (), (), (), ())), k=3,
                    required_support=(("rare", 1),))
    assert rare.status == "INFEASIBLE_NECESSARY" and not rare.assignments
    triangle = (('a', 'b'), ('a', 'c'), ('b', 'c'))
    support = (("a", 1), ("b", 1), ("c", 1))
    result = allocate(dataset_factory(labels=triangle), k=2, required_support=support)
    assert result.status == "INFEASIBLE_EXHAUSTIVE" and result.visited_nodes > 0
    assert not result.assignments and result.objective is None
    assert not tiny_feasible(triangle, 2, support)
    too_few = allocate(dataset_factory(labels=(('front',),)*2), k=3)
    assert too_few.status == "INFEASIBLE_NECESSARY" and not too_few.assignments


@pytest.mark.parametrize("labels,k,support", [
    ((('a',),)*4, 2, (("a", 1),)),
    ((('a',), ('b',), ('a',), ('b',)), 2, (("a", 1), ("b", 1))),
    ((('a', 'b'), ('a', 'c'), ('b', 'c')), 2, (("a", 1), ("b", 1), ("c", 1))),
    ((('a',), (), ()), 2, (("a", 1),)),
    (((),)*5, 3, ()),
])
def test_feasibility_agrees_with_independent_tiny_brute_force(dataset_factory, labels, k, support):
    d = dataset_factory(labels=labels)
    result = allocate(d, k=k, required_support=support, node_budget=10000)
    possible = tiny_feasible(labels, k, support)
    assert result.status.startswith("FEASIBLE_") == possible
    assert verify_allocation(d, result, expected_policy=allocation_policy(
        k=k, required_support=support, node_budget=10000)) == possible
    if not possible:
        assert result.status.startswith("INFEASIBLE_") and not result.assignments


def test_greedy_failure_can_find_a_feasible_bounded_search_candidate(dataset_factory):
    # Nuisance labels influence greedy cost; both required-r events initially land together.
    labels = (('r', 'a1', 'a2'), ('b',), ('a1', 'a2', 'b'), ('r',))
    d = dataset_factory(labels=labels)
    result = allocate(d, k=2, required_support=(("r", 1),))
    assert result.status == "FEASIBLE_SEARCH"
    assert verify_allocation(d, result, expected_policy=allocation_policy(
        k=2, required_support=(("r", 1),)))
    assert tiny_feasible(labels, 2, (("r", 1),))


def test_budget_and_size_limits_never_claim_infeasible_or_accept_manifest(dataset_factory):
    triangle = (('a', 'b'), ('a', 'c'), ('b', 'c'))
    support = (("a", 1), ("b", 1), ("c", 1))
    budget = allocate(dataset_factory(labels=triangle), k=2, required_support=support, node_budget=1)
    size = allocate(dataset_factory(labels=triangle+((),)*17), k=2, required_support=support)
    assert budget.status == "UNDETERMINED_BUDGET" and budget.visited_nodes == 1
    assert size.status == "UNDETERMINED_SIZE" and size.visited_nodes == 0
    assert not budget.assignments and not size.assignments


def test_large_constructed_metadata_stays_on_polynomial_greedy_path(dataset_factory):
    d = dataset_factory(labels=(('front',),)*1315)
    result = allocate(d, k=5, required_support=(("front", 1),))
    assert result.status == "FEASIBLE_GREEDY" and result.visited_nodes == 0
    assert result.greedy_choices == 1315*5
    assert verify_allocation(d, result, expected_policy=allocation_policy(
        k=5, required_support=(("front", 1),)))
    sizes = [sum(fold == i for _, fold in result.assignments) for i in range(5)]
    assert max(sizes)-min(sizes) <= 1


def test_fold_count_has_no_unpublished_32_fold_cap(dataset_factory):
    d = dataset_factory(labels=(('front',),)*33)
    result = allocate(d, k=33)
    assert result.status == "FEASIBLE_GREEDY"
    assert verify_allocation(d, result, expected_policy=allocation_policy(k=33))
    assert {fold for _, fold in result.assignments} == set(range(33))


def test_forged_assignment_objective_input_role_and_status_are_rejected(dataset_factory):
    d = dataset_factory()
    result = allocate(d, k=3)
    for bad in [replace(result, assignments=result.assignments[:-1]),
                replace(result, assignments=result.assignments+(result.assignments[0],)),
                replace(result, objective=(0, 0, -1)),
                replace(result, input_digest="0"*64),
                replace(result, status="INFEASIBLE_EXHAUSTIVE"),
                replace(result, status="OPTIMAL"),
                replace(result, assignments=((result.assignments[0][0], True),)+result.assignments[1:])]:
        with pytest.raises(ValueError):
            verify_allocation(d, bad, expected_policy=allocation_policy(k=3))


def test_reserved_roles_and_training_calibration_selection_boundaries(dataset_factory):
    roles = (DatasetRole.DEVELOPMENT_POOL,)*6 + (
        DatasetRole.CALIBRATION_ONLY, DatasetRole.RESERVED_CONTROL,
        DatasetRole.CASE_STUDY, DatasetRole.FINAL_DESCRIPTIVE)
    d = dataset_factory(labels=(('front',),)*10, roles=roles)
    result = allocate(d, k=3)
    assert len(result.assignments) == 6
    evaluation = {e for e, fold in result.assignments if fold == 0}
    complement = sorted(set(dict(result.assignments))-evaluation)
    plan = role_plan(d, result, outer_fold=0, validation_events=(complement[0],),
                     calibration_mode="RESERVED_CALIBRATION",
                     expected_policy=allocation_policy(k=3))
    context = RoleContext(d, result, allocation_policy(k=3), 0, (complement[0],),
                          "RESERVED_CALIBRATION")
    siblings = [set(plan.outer_evaluation), set(plan.training), set(plan.validation),
                set(plan.calibration), set(plan.reserved_controls),
                set(plan.case_studies), set(plan.final_descriptive)]
    assert sum(map(len, siblings)) == len(set.union(*siblings)) == 10
    validate_fit_membership(plan, "BASE_MODEL_FIT", plan.training,
                            selection_events=plan.validation, expected_context=context)
    validate_fit_membership(plan, "PREPROCESSOR_FIT", plan.training, expected_context=context)
    validate_fit_membership(plan, "CALIBRATOR_FIT", plan.calibration, expected_context=context)
    for operation in ("BASE_MODEL_FIT", "PREPROCESSOR_FIT", "FEATURE_CACHE", "CALIBRATOR_FIT"):
        for forbidden in (plan.outer_evaluation, plan.reserved_controls, plan.case_studies,
                           plan.final_descriptive):
            with pytest.raises(ValueError):
                validate_fit_membership(plan, operation, forbidden, expected_context=context)
    with pytest.raises(ValueError):
        validate_fit_membership(plan, "FEATURE_CACHE", plan.training,
                                producing_fit_events=plan.outer_evaluation, expected_context=context)
    with pytest.raises(ValueError):
        validate_fit_membership(plan, "BASE_MODEL_FIT", plan.training,
                                selection_events=plan.outer_evaluation, expected_context=context)
    with pytest.raises(ValueError):
        validate_fit_membership(replace(plan, training=plan.outer_evaluation),
                                "BASE_MODEL_FIT", plan.outer_evaluation, expected_context=context)


def test_inner_validation_frozen_refit_and_unverified_oof_fail_closed(dataset_factory):
    d = dataset_factory()
    allocation = allocate(d, k=3)
    outer = tuple(e for e, fold in allocation.assignments if fold == 0)
    with pytest.raises(ValueError):
        role_plan(d, allocation, outer_fold=0, validation_events=outer,
                  expected_policy=allocation_policy(k=3))
    with pytest.raises(ValueError):
        role_plan(d, allocation, outer_fold=0, expected_policy=allocation_policy(k=3))
    frozen = role_plan(d, allocation, outer_fold=0, frozen_rule_id="synthetic:rule:frozen",
                       expected_policy=allocation_policy(k=3))
    context = RoleContext(d, allocation, allocation_policy(k=3), 0,
                          frozen_rule_id="synthetic:rule:frozen")
    validate_fit_membership(frozen, "FINAL_REFIT", frozen.training, expected_context=context)
    for bad in (replace(frozen, frozen_rule_id=""),
                replace(frozen, frozen_rule_id=None),
                replace(frozen, calibration_mode="UNKNOWN")):
        with pytest.raises(ValueError):
            validate_fit_membership(bad, "BASE_MODEL_FIT", bad.training, expected_context=context)
    complement = tuple(e for e, fold in allocation.assignments if fold != 0)
    with pytest.raises(ValueError):
        role_plan(d, allocation, outer_fold=0, validation_events=complement,
                  expected_policy=allocation_policy(k=3))
    inner = role_plan(d, allocation, outer_fold=0, validation_events=(complement[0],),
                      calibration_mode="INNER_OOF", expected_policy=allocation_policy(k=3))
    context = RoleContext(d, allocation, allocation_policy(k=3), 0, (complement[0],),
                          "INNER_OOF")
    with pytest.raises(ValueError, match="provenance"):
        validate_fit_membership(inner, "CALIBRATOR_FIT", inner.validation, expected_context=context)


def test_rd024_rd025_not_reinterpreted_as_training_or_confirmation(dataset_factory):
    # Only explicit prospective roles determine membership. Names/categories do not.
    roles = (DatasetRole.DEVELOPMENT_POOL,)*3 + (DatasetRole.CASE_STUDY,
                                               DatasetRole.RESERVED_CONTROL)
    d = dataset_factory(labels=(('train',),)*3+(('engine',), ()), roles=roles)
    result = allocate(d, k=3)
    assert {e for e, _ in result.assignments} == {e.event_id for e in d.events[:3]}
    registry = validate_dataset(d)
    assert registry.groups[3].role == DatasetRole.CASE_STUDY
    assert registry.groups[4].role == DatasetRole.RESERVED_CONTROL
    assert 'synthetic metadata only' in result.limitations[0]
    with pytest.raises(ValueError):
        validate_dataset(replace(d, events=(replace(d.events[0], role="training"),)+d.events[1:]))
