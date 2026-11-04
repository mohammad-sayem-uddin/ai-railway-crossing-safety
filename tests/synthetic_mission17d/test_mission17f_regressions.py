"""Recovered 17F fixtures, migrated to explicit bindings and normal regressions.

The original source and baseline reproductions remain in the 17F audit report.
These checks are authored remediation evidence; they are not a 17H review.
"""
import random
import sys
from dataclasses import replace
from fractions import Fraction as Q
from itertools import product

import pytest

from railway_detection.synthetic.convention_b import (
    CausalRunner,
    SyntheticEvent,
    Watchdog,
    legacy_float_to_us,
)
from railway_detection.synthetic.grouped_cv import (
    Annotation,
    Asset,
    Capture,
    DatasetRole,
    InvalidInput,
    PhysicalEvent,
    RoleContext,
    SyntheticDataset,
    allocate,
    allocation_policy,
    role_plan,
    validate_dataset,
    validate_fit_membership,
    verify_allocation,
)

F17_RESULTS = {'actuator_oracles': 0, 'CV_oracles': 0, 'greedy_dense_oracles': 0,
               'quadratic_scans': [], 'known_feasible_undetermined': [],
               'configuration_collisions': [], 'rejection_checks': []}


def dataset(labels=(('a',),)*6, roles=None, counts=None):
    roles = roles if roles is not None else (DatasetRole.DEVELOPMENT_POOL,)*len(labels)
    counts = counts if counts is not None else (1,)*len(labels)
    ev, cap, assets, ann = [], [], [], []
    for i, (ls, role, count) in enumerate(zip(labels, roles, counts, strict=True)):
        eid, cid = f'synthetic:f17:event:{i:04}', f'synthetic:f17:capture:{i:04}'
        ev.append(PhysicalEvent(eid, role, tuple(ls)))
        cap.append(Capture(cid, (eid,)))
        for j in range(count):
            aid, nid = f'synthetic:f17:asset:{i:04}:{j}', f'synthetic:f17:annotation:{i:04}:{j}'
            assets.append(Asset(aid, eid, 'STILL', (nid,), cid))
            ann.append(Annotation(nid, aid, tuple(ls), confirmed_empty=not ls))
    return SyntheticDataset(
        "synthetic:f17:dataset", tuple(ev), tuple(cap), tuple(assets), tuple(ann)
    )


def event_list(times_us, commands):
    return [SyntheticEvent(f'synthetic:f17:sensor:{i}', t, c)
            for i, (t, c) in enumerate(zip(times_us, commands, strict=True))]


def independent_segment(q, velocity, duration):
    # Geometric partition by clipping/threshold breakpoints; do not call _motion.
    cuts = {Q(0), duration}
    if velocity:
        for landmark in (0, 45, 90):
            point = (landmark-q)/velocity
            if 0 < point < duration:
                cuts.add(point)
    cuts = sorted(cuts)
    def clipped(t):
        return min(Q(90), max(Q(0), q+velocity*t))
    integral = sum((b-a for a, b in zip(cuts, cuts[1:], strict=False)
                    if clipped((a+b)/2) <= 45), Q(0))
    return clipped(duration), integral


def test_independent_geometric_oracle_200_trajectories():
    rng = random.Random(0x17F)
    for _ in range(200):
        initial = rng.choice([Q(0), Q(1, 7), Q(30), Q('44.9999999'), Q(45), Q('45.0000001'), Q(90)])
        closing, opening = rng.choice([Q(3), Q(6), Q(5, 2)]), rng.choice([Q(3), Q(7, 2)])
        times = [rng.choice([0, 1000000])]
        for _ in range(rng.randint(1, 24)):
            times.append(times[-1]+rng.choice([1000, 12500, 100000, 200000, 375000, 1000000]))
        commands = [rng.choice('HLR') for _ in times]
        q, endpoint, continuous = initial, Q(0), Q(0)
        for i in range(1, len(times)):
            d = Q(times[i]-times[i-1], 1000000)
            velocity = {'H': Q(0), 'L': -90/closing, 'R': 90/opening}[commands[i-1]]
            q, integral = independent_segment(q, velocity, d)
            endpoint += d*int(q <= 45)
            continuous += integral
        result = CausalRunner(
            initial_angle=initial, closing_seconds=closing, opening_seconds=opening
        ).run(event_list(times, commands), fixture_id="synthetic:f17:geometric")
        assert (result.final_angle, result.endpoint_seconds, result.continuous_seconds) == (
            q,
            endpoint,
            continuous,
        )
        F17_RESULTS['actuator_oracles'] += 1


def brute_possible(labels, k):
    for assignment in product(range(k), repeat=len(labels)):
        if set(assignment) != set(range(k)):
            continue
        if all(any(assignment[i] == f and label in labels[i] for i in range(len(labels)))
               for f in range(k) for label in ('a', 'b')):
            return True
    return False


def test_small_cv_exhaustive_oracle_2704_inputs():
    masks = ((), ('a',), ('b',), ('a', 'b'))
    for m in range(2, 6):
        for labels in product(masks, repeat=m):
            for k in range(2, min(m, 3)+1):
                result = allocate(
                    dataset(labels), k=k, required_support=(("a", 1), ("b", 1)), node_budget=10000
                )
                possible = brute_possible(labels, k)
                assert result.status.startswith('FEASIBLE_') == possible
                if not possible:
                    assert result.status.startswith('INFEASIBLE_') and not result.assignments
                assert (
                    verify_allocation(
                        dataset(labels),
                        result,
                        expected_policy=allocation_policy(
                            k=k, required_support=(("a", 1), ("b", 1)), node_budget=10000
                        ),
                    )
                    == possible
                )
                F17_RESULTS['CV_oracles'] += 1
    assert F17_RESULTS['CV_oracles'] == 2704


@pytest.mark.parametrize(
    "size,budget,expected", [(4, 1, "UNDETERMINED_BUDGET"), (20, 100000, "UNDETERMINED_SIZE")]
)
def test_known_feasible_inputs_can_legitimately_remain_undetermined(size, budget, expected):
    labels = (('r', 'a1', 'a2'), ('b',), ('a1', 'a2', 'b'), ('r',))+((),)*(size-4)
    d = dataset(labels)
    result = allocate(d, k=2, required_support=(('r', 1),), node_budget=budget)
    witness = {e.event_id: (0 if i < 2 else 1 if i < 4 else i % 2) for i, e in enumerate(d.events)}
    assert all(
        any("r" in e.labels and witness[e.event_id] == f for e in d.events) for f in range(2)
    )
    assert result.status == expected and not result.assignments
    F17_RESULTS["known_feasible_undetermined"].append(
        {"size": size, "status": result.status, "witness_r_support": [1, 1]}
    )


def dense_objective(groups, assignment, k):
    labels = sorted({label for g in groups for label in g.labels})
    es = [sum(f == j for f in assignment.values()) for j in range(k)]
    fs = [
        sum(g.original_asset_count for g in groups if assignment.get(g.event_id) == j)
        for j in range(k)
    ]

    def score(vs):
        return sum((k*x-sum(vs))**2 for x in vs)
    cs = sum(score([sum(label in g.labels for g in groups if assignment.get(g.event_id) == j)
                    for j in range(k)]) for label in labels)
    return score(es), cs, score(fs)


def test_incremental_greedy_scores_match_dense_recomputation_50_inputs():
    rng = random.Random(1717)
    for _ in range(50):
        m, k = rng.randint(4, 12), rng.randint(2, 4)
        labels = tuple(
            tuple(label for label in ("a", "b", "c") if rng.randrange(2)) for _ in range(m)
        )
        d = dataset(labels, counts=tuple(rng.randint(1, 3) for _ in range(m)))
        groups = validate_dataset(d).groups
        ordered = sorted(groups, key=lambda g: (-g.original_asset_count, g.event_id))
        assignment = {}
        for g in ordered:
            candidates = []
            for fold in range(k):
                candidate = dict(assignment)
                candidate[g.event_id] = fold
                candidates.append((dense_objective(groups, candidate, k), fold))
            assignment[g.event_id] = min(candidates)[1]
        result = allocate(d, k=k)
        assert dict(result.assignments) == assignment
        assert result.objective == dense_objective(groups, assignment, k)
        F17_RESULTS['greedy_dense_oracles'] += 1


def test_context_bound_fit_gate_should_reject_coherent_control_to_train_swap():
    roles = (DatasetRole.DEVELOPMENT_POOL,)*6+(DatasetRole.RESERVED_CONTROL,)
    d = dataset((('a',),)*7, roles)
    a = allocate(d, k=3)
    complement = tuple(e for e, f in a.assignments if f != 0)
    plan = role_plan(
        d,
        a,
        outer_fold=0,
        validation_events=(complement[0],),
        expected_policy=allocation_policy(k=3),
    )
    context = RoleContext(d, a, allocation_policy(k=3), 0, (complement[0],))
    validate_fit_membership(plan, 'BASE_MODEL_FIT', plan.training, expected_context=context)
    control, former_train = plan.reserved_controls[0], plan.training[0]
    altered = replace(
        plan,
        training=(control,) + plan.training[1:],
        reserved_controls=(former_train,),
        development=tuple(control if e == former_train else e for e in plan.development),
    )
    F17_RESULTS['rejection_checks'].append('coherent control/train swap must reject')
    with pytest.raises(InvalidInput, match='provenance'):
        validate_fit_membership(altered, 'BASE_MODEL_FIT', (control,), expected_context=context)


def test_context_bound_allocation_gate_should_reject_weakened_request():
    d = dataset((('r', 'a1', 'a2'), ('b',), ('a1', 'a2', 'b'), ('r',)))
    strong = allocate(d, k=2, required_support=(('r', 1),))
    weak = allocate(d, k=2)
    assert strong.input_digest == weak.input_digest
    assert strong.policy_digest != weak.policy_digest
    assert verify_allocation(d, strong, expected_policy=allocation_policy(
        k=2, required_support=(('r', 1),)))
    assert verify_allocation(d, weak, expected_policy=allocation_policy(k=2))
    assert (
        len(
            {
                f
                for e, f in weak.assignments
                if "r" in next(x.labels for x in d.events if x.event_id == e)
            }
        )
        == 1
    )
    F17_RESULTS["rejection_checks"].append(
        "weaker support request must reject against original expected policy"
    )
    with pytest.raises(InvalidInput, match='policy'):
        verify_allocation(
            d, weak, expected_policy=allocation_policy(k=2, required_support=(("r", 1),))
        )


@pytest.mark.parametrize(
    "change", ["bool_objective", "float_objective", "negative_work", "search_without_nodes"]
)
def test_receipt_validator_should_reject_invalid_types_and_work_semantics(change):
    d = dataset()
    a = allocate(d, k=3)
    assert a.objective == (0, 0, 0)
    assert verify_allocation(d, a, expected_policy=allocation_policy(k=3))
    variants = {
        'bool_objective': replace(a, objective=(False, False, False)),
        'float_objective': replace(a, objective=(0.0, 0.0, 0.0)),
        'negative_work': replace(a, greedy_choices=-1),
        'search_without_nodes': replace(a, status='FEASIBLE_SEARCH', visited_nodes=0),
    }
    F17_RESULTS['rejection_checks'].append(change+' must reject by verify_allocation')
    message = {'bool_objective': 'objective', 'float_objective': 'objective',
               'negative_work': 'work counters', 'search_without_nodes': 'visited nodes'}[change]
    with pytest.raises(InvalidInput, match=message):
        verify_allocation(d, variants[change], expected_policy=allocation_policy(k=3))


@pytest.mark.parametrize('configuration', ['actuator_rate', 'watchdog_profile'])
def test_result_configuration_binding_distinguishes_unchanged_path(configuration):
    source = event_list([0, 1000000], 'HH')
    a = CausalRunner().run(source, fixture_id='synthetic:f17:same')
    runner = (
        CausalRunner(closing_seconds=6)
        if configuration == "actuator_rate"
        else CausalRunner(watchdog=Watchdog("SCHEDULED", 10000000, "L"))
    )
    b = runner.run(source, fixture_id='synthetic:f17:same')
    assert (a.final_angle, a.endpoint_seconds, a.continuous_seconds) == (
        b.final_angle,
        b.endpoint_seconds,
        b.continuous_seconds,
    )
    assert a.configuration != b.configuration
    assert a.configuration_digest != b.configuration_digest
    assert a.canonical_json() != b.canonical_json()
    F17_RESULTS['configuration_collisions'].append(configuration+' now distinguishes')


@pytest.mark.parametrize('n', [16, 32, 64, 128])
def test_default_reporting_reuses_event_total_without_interval_lookup(n, monkeypatch):
    from railway_detection.synthetic import convention_b

    def forbidden(*args, **kwargs):
        raise AssertionError('default reporting must reuse event endpoint total')

    monkeypatch.setattr(convention_b, '_report_endpoint_seconds', forbidden)
    result = CausalRunner().run(
        event_list([i * 10000 for i in range(n + 1)], "H" * (n + 1)),
        fixture_id="synthetic:f17:scans",
    )
    assert (
        result.endpoint_seconds == result.report_endpoint_seconds == result.continuous_seconds == 0
    )
    F17_RESULTS['quadratic_scans'].append({'intervals': n, 'report_interval_lookups': 0})


def test_legacy_float_policy_exposes_common_tick_migration_problem():
    assert legacy_float_to_us(.2) == 200000
    with pytest.raises(ValueError):
        legacy_float_to_us(3*.2)


def test_propagated_incomplete_prefix_and_offline_lookahead_are_explicit():
    source = event_list([0, 1000000], "LL") + [
        SyntheticEvent("synthetic:f17:invalid", 2000000, "UNKNOWN")
    ]
    r = CausalRunner().run(source, fixture_id='synthetic:f17:prefix')
    assert r.status == 'INCOMPLETE' and r.final_angle == 60 and r.horizon_us == 1000000
    assert r.report_endpoint_seconds is None
    source = event_list([0, 1000000], "LL") + [
        SyntheticEvent("synthetic:f17:future-invalid", 3000000, "UNKNOWN")
    ]
    arrival = CausalRunner().run(source, fixture_id='synthetic:f17:cutoff', cutoff='1.5')
    offline = CausalRunner().run(
        source, fixture_id="synthetic:f17:cutoff", cutoff="1.5", mode="OFFLINE"
    )
    assert arrival.status == 'COMPLETE' and arrival.final_angle == 45
    assert offline.status == 'INCOMPLETE' and offline.origin_us is None


@pytest.mark.parametrize('mode,expected', [('SCHEDULED', 84), ('DETECT_ON_ARRIVAL', 90)])
def test_rejected_older_arrival_cannot_reschedule_watchdog(mode, expected):
    source = event_list([0, 1000000, 500000], 'HHR')
    r = CausalRunner(watchdog=Watchdog(mode, 2000000, 'L')).run(
        source, fixture_id='synthetic:f17:watchdog', cutoff='3.2')
    assert len(r.rejections) == 1 and r.rejections[0].reason == 'OUT_OF_ORDER'
    assert r.final_angle == expected


def test_no_production_or_model_modules_loaded():
    assert not any(
        m in sys.modules
        for m in (
            "railway_detection.cli.main",
            "railway_detection.simulation.runner",
            "railway_detection.data.split",
            "torch",
            "cv2",
            "ultralytics",
        )
    )
