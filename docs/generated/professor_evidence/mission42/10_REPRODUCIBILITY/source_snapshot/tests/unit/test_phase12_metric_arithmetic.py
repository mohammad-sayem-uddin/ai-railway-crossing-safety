"""Hand-calculated checks of Phase 12 metric arithmetic and the undecided-window rule.

Every expected number below was worked out on paper from the stated inputs; none is
read back from the code under test. No hourly rate or other metric outside the
documented protocol is introduced.
"""

from __future__ import annotations

import math

import pytest

from railway_detection.evaluation.metrics import (
    PREMATURE_OPENING_UNDECIDED,
    EventMetricsCalculator,
    SingleEventEvaluation,
    wilson_score_interval,
)
from railway_detection.simulation.runner import SimulationRunResult, SimulationStep

V9 = "t1_entry_to_t4_clearance"


def _step(t, crossing="TRAIN_PRESENT", gate="CLOSED", blocked=True):
    return SimulationStep(t, crossing, gate, 0.0 if blocked else 90.0, blocked, None)  # type: ignore[arg-type]


def _run(steps, closed_s, total_s, lead=None, premature=False, event="train_events/e"):
    return SimulationRunResult(
        event_id=event,
        scenario_name="s",
        steps=steps,
        total_duration_s=total_s,
        closed_duration_s=closed_s,
        warning_lead_time_s=lead,
        premature_opening_detected=premature,
    )


# ------------------------------------------------------------------------- Wilson interval


@pytest.mark.parametrize(
    ("k", "n", "lower", "upper"),
    [
        (0, 1, 0.0, 0.7935),  # upper = z^2/(n+z^2) = 3.8415/4.8415
        (0, 3, 0.0, 0.5615),  # 3.8415/6.8415
        (3, 3, 0.4385, 1.0),  # mirror of 0/3
        (2, 4, 0.1500, 0.8500),  # centre .5; margin z/(1+z^2/n)*sqrt(p(1-p)/n+z^2/4n^2)
    ],
)
def test_wilson_interval_matches_hand_calculation(k, n, lower, upper):
    lo, hi = wilson_score_interval(k, n)
    assert lo == pytest.approx(lower, abs=2e-4)
    assert hi == pytest.approx(upper, abs=2e-4)


def test_wilson_is_undefined_not_zero_for_an_empty_denominator():
    assert wilson_score_interval(0, 0) is None
    with pytest.raises(ValueError):
        wilson_score_interval(2, 1)


# -------------------------------------------------------------------- per-event arithmetic


def test_missed_train_uses_the_step_nearest_the_entry_within_a_quarter_second():
    steps = [_step(4.9, blocked=False), _step(5.1, blocked=True)]  # |5.0-5.1|=.1 vs |5.0-4.9|=.1
    # equal distance: min() keeps the first, 4.9 (unblocked) -> missed
    assert EventMetricsCalculator.evaluate_run(_run(steps, 1, 10), entry_time_s=5.0).missed_train
    steps = [_step(4.8, blocked=False), _step(5.1, blocked=True)]  # nearest is 5.1 (blocked)
    assert (
        EventMetricsCalculator.evaluate_run(_run(steps, 1, 10), entry_time_s=5.0).missed_train
        is False
    )
    # nothing within 0.25 s => not evaluable, never "missed"
    far = [_step(4.0, blocked=False), _step(6.0, blocked=False)]
    assert (
        EventMetricsCalculator.evaluate_run(_run(far, 0, 10), entry_time_s=5.0).missed_train is None
    )


def test_excess_closed_duration_is_closed_time_minus_passage_clamped_at_zero():
    steps = [_step(float(t)) for t in range(0, 20)]
    ev = EventMetricsCalculator.evaluate_run(
        _run(steps, closed_s=11.0, total_s=19.0), entry_time_s=5.0, clearance_time_s=12.0
    )
    assert ev.excess_closed_duration_s == pytest.approx(4.0)  # 11 - (12-5)
    short = EventMetricsCalculator.evaluate_run(
        _run(steps, closed_s=3.0, total_s=19.0), entry_time_s=5.0, clearance_time_s=12.0
    )
    assert short.excess_closed_duration_s == 0.0  # max(0, 3 - 7)


def test_clearance_latency_is_first_opening_state_at_or_after_t4():
    steps = [
        _step(9.0, "GATE_OPENING", "OPENING", False),  # before T4: ignored
        _step(10.0, "TRAIN_PRESENT"),
        _step(10.6, "TRAIN_PRESENT"),
        _step(11.4, "GATE_OPENING", "OPENING", False),
        _step(12.0, "CROSSING_CLEAR", "OPEN", False),
    ]
    ev = EventMetricsCalculator.evaluate_run(
        _run(steps, 2.0, 12.0), entry_time_s=4.0, clearance_time_s=10.0
    )
    assert ev.clearance_latency_s == pytest.approx(1.4)  # 11.4 - 10.0
    never = EventMetricsCalculator.evaluate_run(
        _run([_step(10.0), _step(11.0)], 2.0, 11.0), entry_time_s=4.0, clearance_time_s=10.0
    )
    assert never.clearance_latency_s is None  # not 0.0


def test_warning_lead_time_comes_from_the_replay_and_is_none_without_entry():
    steps = [_step(float(t)) for t in range(0, 10)]
    run = _run(steps, 2, 9, lead=3.0)
    assert EventMetricsCalculator.evaluate_run(run, entry_time_s=5.0).warning_lead_time_s == 3.0
    assert EventMetricsCalculator.evaluate_run(run).warning_lead_time_s is None


def test_non_finite_and_inverted_inputs_are_refused():
    run = _run([_step(0.0), _step(1.0)], 0, 1)
    with pytest.raises(ValueError):
        EventMetricsCalculator.evaluate_run(run, entry_time_s=math.nan)
    with pytest.raises(ValueError):
        EventMetricsCalculator.evaluate_run(run, entry_time_s=5.0, clearance_time_s=4.0)
    with pytest.raises(ValueError):
        EventMetricsCalculator.evaluate_run(_run([_step(0.0)], closed_s=9, total_s=3))


# ---------------------------------------------------------------- premature-opening window


def test_premature_opening_is_not_computed_without_an_explicit_window():
    steps = [_step(float(t)) for t in range(0, 15)]
    run = _run(steps, 6.0, 14.0, premature=True)  # the flag would say "premature"
    undecided = EventMetricsCalculator.evaluate_run(run, entry_time_s=4.0, clearance_time_s=12.0)
    assert undecided.premature_opening is None
    assert undecided.metric_exclusions["premature_opening"] == PREMATURE_OPENING_UNDECIDED
    decided = EventMetricsCalculator.evaluate_run(
        run, entry_time_s=4.0, clearance_time_s=12.0, premature_opening_window=V9
    )
    assert decided.premature_opening is True


def test_an_unimplemented_window_is_refused_not_silently_replaced():
    run = _run([_step(0.0), _step(1.0)], 0, 1)
    for window in ("t0_first_visible_to_t4_clearance", "made_up"):
        with pytest.raises(ValueError, match="not implemented"):
            EventMetricsCalculator.evaluate_run(run, premature_opening_window=window)


def test_cohort_summary_states_which_window_it_used_and_excludes_with_a_reason():
    steps = [_step(float(t)) for t in range(0, 15)]
    evs = [
        EventMetricsCalculator.evaluate_run(
            _run(steps, 6, 14, event=f"train_events/e{i}"), entry_time_s=4.0, clearance_time_s=12.0
        )
        for i in range(2)
    ]
    summary = EventMetricsCalculator.aggregate_cohort(evs)
    assert summary.premature_opening_definition == "undecided"
    assert summary.premature_opening_rate is None
    assert summary.premature_opening_evaluable_count == 0
    assert [e["reason"] for e in summary.exclusions["premature_opening"]] == [
        PREMATURE_OPENING_UNDECIDED
    ] * 2
    assert summary.to_dict()["premature_opening_definition"] == "undecided"


def test_mixed_windows_in_one_cohort_are_refused():
    steps = [_step(float(t)) for t in range(0, 15)]
    one = EventMetricsCalculator.evaluate_run(
        _run(steps, 6, 14, event="train_events/a"),
        entry_time_s=4.0,
        clearance_time_s=12.0,
        premature_opening_window=V9,
    )
    two = EventMetricsCalculator.evaluate_run(
        _run(steps, 6, 14, event="train_events/b"),
        entry_time_s=4.0,
        clearance_time_s=12.0,
    )
    with pytest.raises(ValueError, match="mixes"):
        EventMetricsCalculator.aggregate_cohort([one, two])


# --------------------------------------------------------------------- cohort denominators


def _ev(event, **kw):
    base = dict(event_id=event, scenario_name="s", has_train_ground_truth=True)
    base.update(kw)
    return SingleEventEvaluation(**base)


def test_cohort_means_and_denominators_by_hand():
    evs = [
        _ev(
            "a",
            missed_train=False,
            premature_opening=False,
            warning_lead_time_s=2.0,
            excess_closed_duration_s=1.0,
            clearance_latency_s=1.0,
            premature_opening_window=V9,
        ),
        _ev(
            "b",
            missed_train=True,
            premature_opening=True,
            warning_lead_time_s=4.0,
            excess_closed_duration_s=3.0,
            clearance_latency_s=None,
            premature_opening_window=V9,
        ),
        _ev(
            "c",
            missed_train=None,
            premature_opening=None,
            warning_lead_time_s=None,
            premature_opening_window=V9,
        ),  # censored boundaries: nothing evaluable
        _ev(
            "d",
            has_train_ground_truth=False,
            notes="false_alarm_evaluation",
            blocked_seconds=4.5,
            closure_episodes=2,
            exposure_s=30.0,
        ),
        _ev(
            "e",
            has_train_ground_truth=False,
            notes="no_false_alarm",
            blocked_seconds=0.0,
            closure_episodes=0,
            exposure_s=20.0,
        ),
        _ev("x", notes="engine_event_excluded", evaluable=False),
    ]
    s = EventMetricsCalculator.aggregate_cohort(evs)
    assert s.total_events == 6 and s.eligible_events == 3  # a, b, c; the engine event is excluded
    assert s.missed_train_evaluable_count == 2 and s.missed_train_count == 1
    assert s.missed_train_rate == 0.5
    assert s.premature_opening_evaluable_count == 2 and s.premature_opening_rate == 0.5
    assert s.mean_warning_lead_time_s == pytest.approx(3.0)  # (2+4)/2
    assert s.mean_excess_closed_s == pytest.approx(2.0)  # (1+3)/2
    assert s.mean_clearance_latency_s == pytest.approx(1.0)  # only "a"
    assert s.no_train_events == 2 and s.false_alarm_evaluable_count == 2
    assert s.false_alarm_count == 1
    assert s.false_alarm_blocked_seconds == pytest.approx(4.5)
    assert s.false_alarm_closure_episodes == 2
    assert s.false_alarm_exposure_s == pytest.approx(50.0)
    assert s.engine_events == 1
    payload = s.to_dict()
    assert payload["false_alarm_hourly_rate"] == "not_reported_by_protocol"
    assert not [k for k in payload if "per_hour" in k or "hourly" in k.replace("_hourly_rate", "")]
    reasons = {m: {e["event_id"] for e in v} for m, v in s.exclusions.items()}
    assert "c" in reasons["missed_train"] and "b" in reasons["clearance_latency"]


def test_event_ids_must_be_unique_in_a_cohort():
    with pytest.raises(ValueError, match="unique"):
        EventMetricsCalculator.aggregate_cohort([_ev("a"), _ev("a")])


# ------------------------------------------------------------------ M4 / M5 (selectable profile)

M4 = "first_blocked_to_t4_clearance"


def _m4_steps(pattern):
    """pattern: list of (t, blocked, gate_state)."""
    return [_step(t, blocked=b, gate=g, crossing="TRAIN_PRESENT") for t, b, g in pattern]


def test_m4_flags_an_unblock_between_first_block_and_t4_and_needs_no_t1():
    steps = _m4_steps(
        [
            (0, False, "OPEN"),
            (1, True, "CLOSED"),
            (2, True, "CLOSED"),
            (3, False, "OPEN"),
            (4, True, "CLOSED"),
            (5, True, "CLOSED"),
        ]
    )
    ev = EventMetricsCalculator.evaluate_run(
        _run(steps, 3, 5), clearance_time_s=5.0, premature_opening_window=M4
    )  # note: no entry_time_s
    assert ev.premature_opening is True and ev.never_protected is False


def test_m4_is_false_when_the_barrier_stays_blocked_until_t4():
    steps = _m4_steps(
        [
            (0, False, "OPEN"),
            (1, True, "CLOSED"),
            (2, True, "CLOSED"),
            (3, True, "CLOSED"),
            (6, False, "OPEN"),
        ]
    )
    ev = EventMetricsCalculator.evaluate_run(
        _run(steps, 3, 6), clearance_time_s=5.0, premature_opening_window=M4
    )
    assert ev.premature_opening is False  # the unblock at t=6 is after T4


def test_m4_counts_an_opening_command_even_while_the_arm_still_blocks():
    steps = _m4_steps([(1, True, "CLOSED"), (2, True, "OPENING"), (3, True, "CLOSED")])
    ev = EventMetricsCalculator.evaluate_run(
        _run(steps, 3, 3), clearance_time_s=5.0, premature_opening_window=M4
    )
    assert ev.premature_opening is True


def test_m5_never_protected_makes_m4_not_evaluable_and_is_counted_separately():
    never = _m4_steps([(0, False, "OPEN"), (1, False, "OPEN"), (6, True, "CLOSED")])
    # first block exactly at T4, after a full zero-origin unblocked replay (DEC-C01: M5 needs it)
    late = _m4_steps(
        [(t, False, "OPEN") for t in range(5)] + [(5, True, "CLOSED"), (6, True, "CLOSED")]
    )
    evs = [
        EventMetricsCalculator.evaluate_run(
            _run(steps, 0, 6, event=f"train_events/{name}"),
            clearance_time_s=5.0,
            premature_opening_window=M4,
        )
        for name, steps in (("a", never), ("b", late))
    ]
    for ev in evs:
        assert ev.premature_opening is None and ev.never_protected is True
        assert "never_protected_before_T4" in ev.metric_exclusions["premature_opening"]
    summary = EventMetricsCalculator.aggregate_cohort(evs)
    assert summary.never_protected_evaluable_count == 2 and summary.never_protected_count == 2
    assert summary.premature_opening_definition == M4
    assert summary.premature_opening_rate is None


def test_m4_without_t4_is_not_evaluable_and_exclusion_names_only_t4():
    steps = _m4_steps([(1, True, "CLOSED"), (2, True, "CLOSED")])
    ev = EventMetricsCalculator.evaluate_run(
        _run(steps, 2, 2),
        entry_time_s=1.0,
        exclusion_reasons={"T4_tail_clearance": "censored"},
        premature_opening_window=M4,
    )
    assert ev.premature_opening is None and ev.never_protected is None
    summary = EventMetricsCalculator.aggregate_cohort([ev])
    assert summary.exclusions["premature_opening"][0]["reason"] == "T4_tail_clearance:censored"


def test_v9_and_m4_disagree_on_the_same_replay_where_expected():
    # The barrier opens at t=2, before T1=4, after being blocked at t=1; T4=8.
    steps = _m4_steps(
        [
            (1, True, "CLOSED"),
            (2, False, "OPEN"),
            (3, False, "OPEN"),
            (4, True, "CLOSED"),
            (6, True, "CLOSED"),
            (9, False, "OPEN"),
        ]
    )
    run = _run(steps, 4, 9, premature=False)  # the v9 predicate saw no opening in [T1, T4)
    v9 = EventMetricsCalculator.evaluate_run(
        run, entry_time_s=4.0, clearance_time_s=8.0, premature_opening_window=V9
    )
    m4 = EventMetricsCalculator.evaluate_run(
        run, entry_time_s=4.0, clearance_time_s=8.0, premature_opening_window=M4
    )
    assert v9.premature_opening is False and m4.premature_opening is True
