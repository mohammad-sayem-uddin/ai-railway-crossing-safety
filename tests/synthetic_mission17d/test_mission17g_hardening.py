"""Focused synthetic regression hardening for the five 17F findings."""

from dataclasses import FrozenInstanceError, replace
from fractions import Fraction as Q
import random

import pytest

from railway_detection.synthetic import convention_b as sim
from railway_detection.synthetic.grouped_cv import (
    Annotation,
    Asset,
    DatasetRole,
    InvalidInput,
    RoleContext,
    Transform,
    allocate,
    allocation_policy,
    role_plan,
    validate_dataset,
    validate_fit_membership,
    verify_allocation,
)


def context_and_plan(dataset_factory):
    roles = (DatasetRole.DEVELOPMENT_POOL,)*6 + (DatasetRole.RESERVED_CONTROL,)
    dataset = dataset_factory(labels=(('a',),)*7, roles=roles)
    allocation = allocate(dataset, k=3)
    policy = allocation_policy(k=3)
    tune = (next(e for e, f in allocation.assignments if f != 0),)
    context = RoleContext(dataset, allocation, policy, 0, tune)
    plan = role_plan(dataset, allocation, expected_policy=policy,
                     outer_fold=0, validation_events=tune)
    return context, plan


@pytest.mark.parametrize('field,value', [
    ('dataset_id', None), ('dataset_version', ''), ('input_digest', None),
    ('policy_digest', ''), ('allocation_digest', '0'*64),
    ('original_roles', ()), ('original_roles', None), ('outer_fold', False),
])
def test_role_plan_requires_complete_original_bindings(dataset_factory, field, value):
    context, plan = context_and_plan(dataset_factory)
    validate_fit_membership(plan, 'BASE_MODEL_FIT', plan.training, expected_context=context)
    with pytest.raises(InvalidInput):
        validate_fit_membership(replace(plan, **{field: value}), 'BASE_MODEL_FIT', plan.training,
                                expected_context=context)


def test_missing_original_context_and_changed_original_registry_reject(dataset_factory):
    context, plan = context_and_plan(dataset_factory)
    with pytest.raises(InvalidInput, match='context'):
        validate_fit_membership(plan, 'BASE_MODEL_FIT', plan.training)
    changed_roles = replace(context.dataset, events=tuple(
        replace(e, role=DatasetRole.DEVELOPMENT_POOL) for e in context.dataset.events))
    for changed in (changed_roles, replace(context.dataset, version='2')):
        with pytest.raises(InvalidInput):
            validate_fit_membership(plan, 'BASE_MODEL_FIT', plan.training,
                                    expected_context=replace(context, dataset=changed))
    for changed in (replace(context, outer_fold=1),
                    replace(context, validation_events=(plan.training[0],))):
        with pytest.raises(InvalidInput):
            validate_fit_membership(plan, 'BASE_MODEL_FIT', plan.training,
                                    expected_context=changed)


def test_alias_and_multigeneration_derivatives_inherit_original_role(dataset_factory):
    context, _ = context_and_plan(dataset_factory)
    dataset = context.dataset
    original = dataset.assets[-1]
    event = replace(dataset.events[-1], aliases=('synthetic:g:control-alias',))
    dataset = replace(dataset, events=dataset.events[:-1]+(event,))
    parents = (original.asset_id,)
    for depth in range(3):
        child = Asset(f'synthetic:g:child:{depth}', event.aliases[0], 'DERIVATIVE',
                      (f'synthetic:g:annotation:{depth}',), parent_ids=parents,
                      transform=Transform(f'synthetic:g:transform:{depth}', '1', ()))
        annotation = Annotation(child.annotation_ids[0], child.asset_id, ('a',))
        dataset = replace(dataset, assets=dataset.assets+(child,),
                          annotations=dataset.annotations+(annotation,))
        parents = (child.asset_id,)
    registry = validate_dataset(dataset)
    control = next(g for g in registry.groups if g.event_id == event.event_id)
    assert control.role is DatasetRole.RESERVED_CONTROL
    assert len(control.asset_ids) == 4
    allocation = allocate(dataset, k=3)
    assert event.event_id not in dict(allocation.assignments)
    policy = allocation_policy(k=3)
    tune = (next(e for e, f in allocation.assignments if f != 0),)
    plan = role_plan(dataset, allocation, expected_policy=policy, outer_fold=0,
                     validation_events=tune)
    bound_context = RoleContext(dataset, allocation, policy, 0, tune)
    assert dict(plan.original_roles)[event.event_id] is DatasetRole.RESERVED_CONTROL
    validate_fit_membership(plan, 'BASE_MODEL_FIT', plan.training, expected_context=bound_context)
    with pytest.raises(InvalidInput):
        validate_fit_membership(plan, 'BASE_MODEL_FIT', (event.event_id,),
                                expected_context=bound_context)
    # A derived record cannot acquire a development role by changing its event alias.
    contradictory = replace(dataset, assets=dataset.assets[:-1]+(
        replace(dataset.assets[-1], event_id=dataset.events[0].event_id),))
    with pytest.raises(InvalidInput, match='multi-event'):
        validate_dataset(contradictory)
    with pytest.raises(InvalidInput):
        validate_dataset(replace(dataset, events=dataset.events[:-1]+(replace(event, role=None),)))


def test_policy_binding_requires_expected_request_and_rejects_substitution(dataset_factory):
    dataset = dataset_factory()
    result = allocate(dataset, k=3)
    with pytest.raises(InvalidInput, match='expected'):
        verify_allocation(dataset, result)
    assert verify_allocation(dataset, result, expected_policy=allocation_policy(k=3))
    for policy in (allocation_policy(k=2), allocation_policy(k=3, node_budget=7),
                   allocation_policy(k=3, required_support=(('front', 1),))):
        with pytest.raises(InvalidInput, match='policy'):
            verify_allocation(dataset, result, expected_policy=policy)
    for binding in (None, '', '0'*64):
        malformed = replace(result, policy_digest=binding)
        with pytest.raises(InvalidInput):
            verify_allocation(dataset, malformed, expected_policy=allocation_policy(k=3))
        with pytest.raises(InvalidInput):
            malformed.canonical_json()
    with pytest.raises(InvalidInput):
        verify_allocation(replace(dataset, version='2'), result,
                          expected_policy=allocation_policy(k=3))


def test_policy_normalization_is_deterministic_without_weakening_constraints(dataset_factory):
    dataset = dataset_factory(labels=(('a', 'b'),)*6)
    a = allocate(dataset, k=3, required_support=(('a', 1), ('b', 1)))
    b = allocate(dataset, k=3, required_support=(('b', 1), ('a', 1)))
    assert a.policy_digest == b.policy_digest
    assert a.canonical_json() == b.canonical_json()
    assert verify_allocation(dataset, b, expected_policy=allocation_policy(
        k=3, required_support=(('b', 1), ('a', 1))))


@pytest.mark.parametrize('field,value', [
    ('profile', 'OTHER'), ('receipt_version', 'V1'), ('dataset_id', None),
    ('input_digest', 'not-a-digest'), ('k', True), ('k', 3.0),
    ('required_support', None), ('required_support', (('front', True),)),
    ('required_support', (('front', 1), ('front', 1))),
    ('node_budget', False), ('node_budget', 1.0),
    ('visited_nodes', True), ('visited_nodes', 0.0), ('visited_nodes', -1),
    ('visited_nodes', 100001), ('visited_nodes', 1),
    ('greedy_choices', False), ('greedy_choices', 18.0),
    ('greedy_choices', -1), ('greedy_choices', 19),
    ('status', 'OPTIMAL'), ('status', None),
    ('status', 'INFEASIBLE_EXHAUSTIVE'), ('status', 'UNDETERMINED_SIZE'),
    ('status', 'FEASIBLE_SEARCH'),
    ('assignments', None), ('assignments', []), ('assignments', (('synthetic:g:x', True),)),
    ('objective', None), ('objective', [0, 0, 0]), ('objective', (False, False, False)),
    ('objective', (0.0, 0.0, 0.0)), ('objective', (0, 0, -1)), ('objective', (0, 0)),
    ('reason', ''), ('reason', 'caller says accepted'),
    ('policy_digest', None), ('policy_digest', '0'*64),
    ('limitations', ()), ('limitations', []),
])
def test_every_receipt_field_is_checked(dataset_factory, field, value):
    dataset = dataset_factory()
    allocation = allocate(dataset, k=3)
    assert allocation.objective == (0, 0, 0)
    with pytest.raises(InvalidInput):
        verify_allocation(dataset, replace(allocation, **{field: value}),
                          expected_policy=allocation_policy(k=3))


def test_duplicate_noncanonical_and_coherently_forged_receipts_reject(dataset_factory):
    dataset = dataset_factory()
    result = allocate(dataset, k=3)
    for assignments in (result.assignments+(result.assignments[0],),
                        tuple(reversed(result.assignments)),
                        tuple(list(pair) for pair in result.assignments)):
        with pytest.raises(InvalidInput):
            verify_allocation(dataset, replace(result, assignments=assignments),
                              expected_policy=allocation_policy(k=3))
    # A different balanced partition has the same objective, but is not this
    # deterministic operation's output. Shape/objective checks alone are insufficient.
    different = tuple((e, (f+1) % 3) for e, f in result.assignments)
    with pytest.raises(InvalidInput, match='operation'):
        verify_allocation(dataset, replace(result, assignments=different),
                          expected_policy=allocation_policy(k=3))
    with pytest.raises(InvalidInput):
        replace(allocation_policy(k=3), search_limit=19)
    with pytest.raises(InvalidInput):
        replace(allocation_policy(k=3), allow_ungrouped_fallback=True)


@pytest.mark.parametrize('labels,k,support,budget,status', [
    ((('a',),)*6, 3, (), 100000, 'FEASIBLE_GREEDY'),
    ((('a',), (), ()), 2, (('a', 1),), 100000, 'INFEASIBLE_NECESSARY'),
    ((('a', 'b'), ('a', 'c'), ('b', 'c')), 2,
     (('a', 1), ('b', 1), ('c', 1)), 100000, 'INFEASIBLE_EXHAUSTIVE'),
    ((('r', 'a1', 'a2'), ('b',), ('a1', 'a2', 'b'), ('r',)),
     2, (('r', 1),), 100000, 'FEASIBLE_SEARCH'),
    ((('r', 'a1', 'a2'), ('b',), ('a1', 'a2', 'b'), ('r',)),
     2, (('r', 1),), 1, 'UNDETERMINED_BUDGET'),
    ((('r', 'a1', 'a2'), ('b',), ('a1', 'a2', 'b'), ('r',))+((),)*16,
     2, (('r', 1),), 100000, 'UNDETERMINED_SIZE'),
])
def test_complete_receipt_contract_for_every_status(dataset_factory, labels, k, support,
                                                   budget, status):
    dataset = dataset_factory(labels=labels)
    result = allocate(dataset, k=k, required_support=support, node_budget=budget)
    policy = allocation_policy(k=k, required_support=support, node_budget=budget)
    assert result.status == status
    assert verify_allocation(dataset, result, expected_policy=policy) == status.startswith('FEASIBLE_')
    assert result.policy_digest == policy.digest
    assert result.canonical_json() == allocate(
        dataset, k=k, required_support=support, node_budget=budget).canonical_json()
    # Both valid-looking work counter changes and false reason statements reject.
    with pytest.raises(InvalidInput):
        verify_allocation(dataset, replace(result, greedy_choices=result.greedy_choices+1),
                          expected_policy=policy)
    with pytest.raises(InvalidInput):
        verify_allocation(dataset, replace(result, reason='unverified caller reason'),
                          expected_policy=policy)


def events(times=(0, 1000000), commands='HH'):
    return [sim.SyntheticEvent(f'synthetic:g:input:{i}', t, c)
            for i, (t, c) in enumerate(zip(times, commands, strict=True))]


@pytest.mark.parametrize('runner,kwargs', [
    ({'closing_seconds': 6}, {}), ({'opening_seconds': 6}, {}),
    ({'watchdog': sim.Watchdog('SCHEDULED', 10000000, 'L')}, {}),
    ({'watchdog': sim.Watchdog('DETECT_ON_ARRIVAL', 10000000, 'R')}, {}),
    ({}, {'mode': 'OFFLINE'}), ({}, {'cutoff': '1.0'}),
    ({}, {'report_times': (0, 1000000)}),
])
def test_material_configuration_is_distinguishable_on_identical_trajectory(runner, kwargs):
    a = sim.CausalRunner().run(events(), fixture_id='synthetic:g:config')
    b = sim.CausalRunner(**runner).run(events(), fixture_id='synthetic:g:config', **kwargs)
    assert (a.final_angle, a.endpoint_seconds, a.continuous_seconds) == (
        b.final_angle, b.endpoint_seconds, b.continuous_seconds)
    assert a.configuration != b.configuration
    assert a.configuration_digest != b.configuration_digest
    assert a.canonical_json() != b.canonical_json()


def test_complete_configuration_snapshot_and_equivalent_representations():
    result = sim.CausalRunner(initial_angle='45', closing_seconds='2.5', opening_seconds=7,
                             watchdog=sim.Watchdog('SCHEDULED', 2000000, 'CLOSED')).run(
        events((1000000, 1500000), 'LR'), fixture_id='synthetic:g:all-settings',
        mode='OFFLINE', cutoff='2', report_times=('1', '1.25', '2'))
    expected = sim.RunConfiguration(Q(45), Q('2.5'), Q(7),
                                    sim.Watchdog('SCHEDULED', 2000000, sim.Command.LOWER),
                                    'OFFLINE', 2000000, (1000000, 1250000, 2000000))
    assert result.configuration == expected
    sim.verify_run_configuration(result, expected_configuration=expected)
    assert result.configuration_digest == expected.digest
    with pytest.raises(FrozenInstanceError):
        result.configuration.closing_seconds = Q(8)
    with pytest.raises(ValueError):
        replace(expected, closing_seconds=None)
    with pytest.raises(ValueError):
        replace(expected, command_latency_us=1)
    with pytest.raises(ValueError):
        replace(expected, dynamics='DIFFERENT_THRESHOLD')


def test_missing_mismatched_or_substituted_configuration_rejects():
    result = sim.CausalRunner().run(events(), fixture_id='synthetic:g:verify')
    expected = sim.RunConfiguration(Q(90), Q(3), Q(3), sim.Watchdog(), 'ARRIVAL', None, None)
    other = replace(expected, closing_seconds=Q(6))
    with pytest.raises(ValueError):
        sim.verify_run_configuration(result)
    for bad in (replace(result, configuration=None),
                replace(result, configuration_digest=None),
                replace(result, configuration_digest='0'*64),
                replace(result, configuration=other, configuration_digest=other.digest),
                replace(result, mode='OFFLINE'), replace(result, initial_angle=Q(80)),
                replace(result, report_grid_kind='FIXED_GRID')):
        with pytest.raises(ValueError):
            sim.verify_run_configuration(bad, expected_configuration=expected)
    for bad in (replace(result, configuration=None),
                replace(result, configuration_digest='0'*64)):
        with pytest.raises(ValueError):
            bad.canonical_json()


@pytest.mark.parametrize('source,mode,status', [
    ([], 'ARRIVAL', 'EMPTY'), (events((0,), 'L'), 'ARRIVAL', 'COMPLETE'),
    (events((0, 1000000), 'LL')+[sim.SyntheticEvent('synthetic:g:bad', None, 'L')],
     'ARRIVAL', 'INCOMPLETE'),
    ([sim.SyntheticEvent('synthetic:g:bad', None, 'L')], 'OFFLINE', 'INCOMPLETE'),
])
def test_empty_partial_and_complete_runs_all_log_actual_settings(source, mode, status):
    result = sim.CausalRunner(closing_seconds=7).run(source, fixture_id='synthetic:g:status', mode=mode)
    expected = sim.RunConfiguration(Q(90), Q(7), Q(3), sim.Watchdog(), mode, None, None)
    assert result.status == status
    sim.verify_run_configuration(result, expected_configuration=expected)
    assert result.configuration.closing_seconds == 7
    assert result.canonical_json()


def test_run_consumes_one_snapshot_even_if_runner_is_reconfigured_during_motion(monkeypatch):
    runner = sim.CausalRunner()
    original_motion = sim._motion

    def reconfigure(q, command, duration, down, up):
        runner._configuration = replace(runner._configuration, closing_seconds=Q(6))
        return original_motion(q, command, duration, down, up)

    monkeypatch.setattr(sim, '_motion', reconfigure)
    result = runner.run(events((0, 1000000, 2000000), 'LLL'), fixture_id='synthetic:g:snapshot',
                        report_times=(0, 500000, 2000000))
    assert result.final_angle == 30
    assert result.configuration.closing_seconds == 3
    assert result.report_endpoint_seconds == Q('1.5')
    next_run = runner.run(events((0, 1000000, 2000000), 'LLL'), fixture_id='synthetic:g:snapshot')
    assert next_run.final_angle == 60
    assert next_run.configuration.closing_seconds == 6


@pytest.mark.parametrize('n,multiplier', [(16, 1), (32, 4), (128, 1), (512, 4), (2048, 1)])
def test_fixed_report_grid_uses_linear_interval_accesses(n, multiplier, monkeypatch, record_property):
    original = sim._report_endpoint_seconds
    reads = 0

    class CountedIntervals:
        def __init__(self, values):
            self.values = values

        def __len__(self):
            nonlocal reads
            reads += 1
            return len(self.values)

        def __getitem__(self, index):
            nonlocal reads
            reads += 1
            return self.values[index]

    def measured(intervals, report, down, up):
        return original(CountedIntervals(intervals), report, down, up)

    monkeypatch.setattr(sim, '_report_endpoint_seconds', measured)
    step = 10000
    report = tuple(range(0, n*step+1, step//multiplier))
    result = sim.CausalRunner().run(events(tuple(i*step for i in range(n+1)), 'L'*(n+1)),
                                    fixture_id='synthetic:g:scaling', report_times=report)
    r = len(report)-1
    assert 0 < reads <= 8*(n+r)
    record_property('intervals', n)
    record_property('report_intervals', r)
    record_property('interval_sequence_accesses', reads)
    # Inclusive threshold at1.5s, only when the declared horizon reaches it.
    expected = sum(Q(b-a, 1000000) for a, b in zip(report, report[1:]) if b >= 1500000)
    assert result.report_endpoint_seconds == expected


def test_fixed_grid_merge_matches_separate_slow_geometric_lookup():
    rng = random.Random(1707)
    for _ in range(50):
        times = [0]
        for _ in range(12):
            times.append(times[-1]+rng.choice((100000, 250000, 500000)))
        commands = ''.join(rng.choice('HLR') for _ in times)
        report = tuple(sorted({0, times[-1], *(rng.randrange(times[-1]+1) for _ in range(20))}))
        result = sim.CausalRunner(initial_angle='45', closing_seconds=3, opening_seconds=6).run(
            events(times, commands), fixture_id='synthetic:g:report-oracle', report_times=report)
        expected = Q(0)
        for start, end in zip(report, report[1:]):
            segment = next(i for i in result.intervals if i.start_us <= end <= i.end_us)
            velocity = {sim.Command.HOLD: Q(0), sim.Command.LOWER: Q(-30),
                        sim.Command.RAISE: Q(15)}[segment.applied_command]
            angle = min(Q(90), max(Q(0), segment.pre_angle+velocity*Q(end-segment.start_us, 1000000)))
            expected += Q(end-start, 1000000)*int(angle <= 45)
        assert result.report_endpoint_seconds == expected


def test_report_grid_failure_and_single_point_semantics_are_preserved():
    for report in ((), (0, 0), (0, 500000), (1000000, 2000000)):
        with pytest.raises(ValueError):
            sim.CausalRunner().run(events(), fixture_id='synthetic:g:invalid-grid', report_times=report)
    one = sim.CausalRunner().run(events((500000,), 'L'), fixture_id='synthetic:g:one',
                                report_times=(500000,))
    assert one.report_endpoint_seconds == 0
    with pytest.raises(ValueError):
        sim.CausalRunner().run([], fixture_id='synthetic:g:empty-grid', report_times=(0,))
