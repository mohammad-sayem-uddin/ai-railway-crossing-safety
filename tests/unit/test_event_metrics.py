"""Unit tests for event-level and cohort safety evaluation metrics."""

from __future__ import annotations

import pytest

from railway_detection.evaluation.metrics import (
    EventMetricsCalculator,
    SingleEventEvaluation,
    wilson_score_interval,
)
from railway_detection.fusion.evidence import DecisionRecord
from railway_detection.simulation.runner import SimulationRunResult, SimulationStep


def test_wilson_score_interval():
    # 0 out of 20
    low, high = wilson_score_interval(0, 20)
    assert low == 0.0
    assert 0.15 < high < 0.20

    # 10 out of 20 (50%)
    low, high = wilson_score_interval(10, 20)
    assert 0.29 < low < 0.35
    assert 0.65 < high < 0.72

    # 0 out of 0 has no denominator and is explicitly not computable.
    assert wilson_score_interval(0, 0) is None
    # All events and invalid counts are handled without fabricated bounds.
    low, high = wilson_score_interval(3, 3)
    assert 0.43 < low < 0.45
    assert high == 1.0
    with pytest.raises(ValueError):
        wilson_score_interval(4, 3)


def test_evaluate_run_safe_event():
    # Gate closed at t=4, train enters at 5, clears at 10, opens at 13.
    steps = [
        SimulationStep(
            timestamp_s=t,
            crossing_state="CROSSING_OCCUPIED" if 5.0 <= t <= 10.0 else "IDLE",
            gate_state="CLOSED" if 4.0 <= t <= 12.0 else "OPEN",
            gate_angle_deg=0.0 if 4.0 <= t <= 12.0 else 90.0,
            is_passage_blocked=(4.0 <= t <= 12.0),
            decision=DecisionRecord(
                timestamp_s=t,
                scenario_run_id="run_1",
                previous_state="IDLE",
                resulting_state="IDLE",
                previous_gate_state="OPEN",
                resulting_gate_state="OPEN",
            ),
        )
        for t in [0.0, 2.0, 4.0, 5.0, 8.0, 10.0, 12.0, 13.0]
    ]

    sim_res = SimulationRunResult(
        event_id="train_events/evt_01",
        scenario_name="safe",
        steps=steps,
        total_duration_s=13.0,
        closed_duration_s=8.0,
        warning_lead_time_s=3.0,
        premature_opening_detected=False,
    )

    ev = EventMetricsCalculator.evaluate_run(
        sim_res,
        entry_time_s=5.0,
        clearance_time_s=10.0,
        premature_opening_window="t1_entry_to_t4_clearance",
    )
    assert not ev.missed_train
    assert ev.premature_opening is False
    assert ev.warning_lead_time_s == 3.0
    assert ev.excess_closed_duration_s == 3.0  # 8.0s closed - 5.0s passage
    assert ev.total_closed_s == 8.0


def test_evaluate_run_missed_train():
    # Gate was open at train entry (t=5.0)
    steps = [
        SimulationStep(
            timestamp_s=5.0,
            crossing_state="IDLE",
            gate_state="OPEN",
            gate_angle_deg=90.0,
            is_passage_blocked=False,
            decision=DecisionRecord(
                timestamp_s=5.0,
                scenario_run_id="run_missed",
                previous_state="IDLE",
                resulting_state="IDLE",
                previous_gate_state="OPEN",
                resulting_gate_state="OPEN",
            ),
        )
    ]
    sim_res = SimulationRunResult(
        event_id="train_events/evt_missed",
        scenario_name="fail",
        steps=steps,
        closed_duration_s=0.0,
    )
    ev = EventMetricsCalculator.evaluate_run(sim_res, entry_time_s=5.0)
    assert ev.missed_train


def test_evaluate_run_unobservable_clearance():
    # If clearance_time_s is None, premature_opening must be None (not_evaluable)
    sim_res = SimulationRunResult(
        event_id="train_events/evt_unobs",
        scenario_name="unobs",
        steps=[],
        total_duration_s=10.0,
        closed_duration_s=10.0,
    )
    ev = EventMetricsCalculator.evaluate_run(
        sim_res,
        entry_time_s=5.0,
        clearance_time_s=None,
        premature_opening_window="t1_entry_to_t4_clearance",
    )
    assert ev.premature_opening is None  # Not False, not True!


def test_aggregate_cohort():
    evals = [
        SingleEventEvaluation(
            event_id="e1",
            scenario_name="normal",
            missed_train=False,
            premature_opening=False,
            warning_lead_time_s=25.0,
            excess_closed_duration_s=4.0,
        ),
        SingleEventEvaluation(
            event_id="e2",
            scenario_name="normal",
            missed_train=False,
            premature_opening=False,
            warning_lead_time_s=23.0,
            excess_closed_duration_s=6.0,
        ),
        SingleEventEvaluation(
            event_id="e3",
            scenario_name="unobs",
            missed_train=False,
            premature_opening=None,  # not evaluable
            warning_lead_time_s=24.0,
        ),
    ]

    summary = EventMetricsCalculator.aggregate_cohort(evals)
    assert summary.total_events == 3
    assert summary.eligible_events == 3
    assert summary.missed_train_count == 0
    assert summary.missed_train_rate == 0.0
    assert summary.premature_opening_evaluable_count == 2
    assert summary.premature_opening_count == 0
    assert summary.premature_opening_rate == 0.0
    assert summary.mean_warning_lead_time_s == 24.0
    assert summary.mean_excess_closed_s == 5.0

    d = summary.to_dict()
    assert d["missed_train_rate"] == 0.0
    assert len(d["missed_train_ci95"]) == 2


def test_cohort_denominators_exclude_engine_and_unobservable_boundaries():
    train = SingleEventEvaluation(
        event_id="train",
        scenario_name="train",
        missed_train=True,
        premature_opening=None,
    )
    no_train = SingleEventEvaluation(
        event_id="negative",
        scenario_name="negative",
        has_train_ground_truth=False,
        missed_train=False,
        notes="false_alarm_evaluation",
    )
    no_alarm = SingleEventEvaluation(
        event_id="negative-clear",
        scenario_name="negative",
        has_train_ground_truth=False,
        missed_train=False,
        notes="no_false_alarm",
    )
    engine = SingleEventEvaluation(
        event_id="engine",
        scenario_name="engine",
        has_train_ground_truth=False,
        evaluable=False,
        notes="engine_event_excluded",
    )
    summary = EventMetricsCalculator.aggregate_cohort([train, no_train, no_alarm, engine])
    assert summary.eligible_events == 1
    assert summary.missed_train_evaluable_count == 1
    assert summary.missed_train_count == 1
    assert summary.no_train_events == 2
    assert summary.false_alarm_evaluable_count == 2
    assert summary.false_alarm_count == 1
    assert summary.engine_events == 1


def test_event_matching_uses_nearest_step_and_missing_boundary_is_not_a_miss():
    def step(timestamp: float, blocked: bool) -> SimulationStep:
        return SimulationStep(
            timestamp_s=timestamp,
            crossing_state="CROSSING_OCCUPIED",
            gate_state="CLOSED" if blocked else "OPEN",
            gate_angle_deg=0.0 if blocked else 90.0,
            is_passage_blocked=blocked,
            decision=DecisionRecord(
                timestamp_s=timestamp,
                scenario_run_id="matching",
                previous_state="IDLE",
                resulting_state="IDLE",
                previous_gate_state="OPEN",
                resulting_gate_state="OPEN",
            ),
        )

    result = SimulationRunResult(
        event_id="train_events/match",
        scenario_name="match",
        steps=[step(4.8, False), step(5.1, True)],
        total_duration_s=6.0,
        closed_duration_s=1.0,
    )
    assert EventMetricsCalculator.evaluate_run(result, entry_time_s=5.0).missed_train is False
    result.steps = [step(1.0, False)]
    assert EventMetricsCalculator.evaluate_run(result, entry_time_s=5.0).missed_train is None


def test_malformed_intervals_are_rejected():
    result = SimulationRunResult(
        event_id="train_events/bad",
        scenario_name="bad",
        total_duration_s=10.0,
        closed_duration_s=1.0,
    )
    with pytest.raises(ValueError, match="after"):
        EventMetricsCalculator.evaluate_run(result, entry_time_s=5.0, clearance_time_s=5.0)
    with pytest.raises(ValueError, match="strictly increasing"):
        result.steps = [
            SimulationStep(
                timestamp_s=1.0,
                crossing_state="IDLE",
                gate_state="OPEN",
                gate_angle_deg=90.0,
                is_passage_blocked=False,
                decision=DecisionRecord(
                    timestamp_s=1.0,
                    scenario_run_id="bad",
                    previous_state="IDLE",
                    resulting_state="IDLE",
                    previous_gate_state="OPEN",
                    resulting_gate_state="OPEN",
                ),
            ),
        ]
        # A duplicate timestamp is represented by a second observation.
        result.steps.append(result.steps[0])
        EventMetricsCalculator.evaluate_run(result)
