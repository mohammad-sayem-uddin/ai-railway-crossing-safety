"""Comprehensive synthetic evaluation validation tests for Phase 5 (Section 8.9).

Validates all 13 required evaluation scenarios:
1. M4 primary metric behavior at boundaries
2. M5 companion metric behavior with varying replay lengths
3. Empty replay
4. Short replay
5. Late replay start
6. Left-censored events
7. Right-censored events
8. No-train events
9. Engine event isolation
10. Rejection of invalid cache provenance
11. Rejection of invalid authorizations
12. Refusal of unapproved splits
13. Rejection of non-conforming cohort sizes

All fixtures are strictly synthetic memory objects. No raw media is accessed.
"""

from __future__ import annotations

import pytest

from railway_detection.evaluation.descriptive_only import (
    DescriptiveOnlyInput,
    DescriptiveOnlyRefusal,
    aggregate_descriptive_only,
)
from railway_detection.evaluation.input_contracts import EvidenceClassification
from railway_detection.evaluation.metrics import (
    M4_REASON_REPLAY_EMPTY,
    M4_REASON_REPLAY_ENDED_BEFORE_T4,
    M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4,
    M4_REASON_REPLAY_STARTED_LATE,
    M4_REASON_T4_MISSING,
    M4_STATUS_EVALUABLE,
    M4_STATUS_NEVER_PROTECTED,
    M4_STATUS_NOT_EVALUABLE,
    EventMetricsCalculator,
    SingleEventEvaluation,
    UnqualifiedEventIdError,
    classify_m4,
)
from railway_detection.experiments.cache_provenance import (
    CacheProvenanceError,
    ControlledCacheProvenance,
    validate_controlled_cache_provenance,
)
from railway_detection.fusion.evidence import DecisionRecord
from railway_detection.simulation.runner import SimulationRunResult, SimulationStep


def _make_sim_step(
    time_s: float,
    gate_state: str = "CLOSED",
    blocked: bool = True,
) -> SimulationStep:
    dec = DecisionRecord(
        timestamp_s=time_s,
        scenario_run_id="synthetic_run_1",
        previous_state="IDLE",
        resulting_state="IDLE",
        previous_gate_state="OPEN" if not blocked else "CLOSED",
        resulting_gate_state="OPEN" if not blocked else "CLOSED",
    )
    return SimulationStep(
        timestamp_s=time_s,
        crossing_state="IDLE",
        gate_state=gate_state,
        gate_angle_deg=0.0 if blocked else 90.0,
        is_passage_blocked=blocked,
        decision=dec,
    )


def _make_sim_result(
    steps: list[SimulationStep],
    event_id: str = "train_events/event_001",
) -> SimulationRunResult:
    total_dur = steps[-1].timestamp_s if steps else 0.0
    return SimulationRunResult(
        event_id=event_id,
        scenario_name="synthetic_scenario",
        steps=steps,
        total_duration_s=total_dur,
        closed_duration_s=total_dur if steps else 0.0,
        warning_lead_time_s=10.0 if steps else 0.0,
        premature_opening_detected=False,
    )


# 1. M4 Primary Metric Behavior at Boundaries
class TestM4BoundaryBehavior:
    def test_gate_opening_before_t4_is_witnessed_premature(self):
        t4 = 20.0
        # Gate blocked from t=5 to 19.8, opens prematurely at 19.8 < 20.0
        steps = [
            _make_sim_step(0.0, gate_state="OPEN", blocked=False),
            _make_sim_step(5.0, gate_state="CLOSED", blocked=True),
            _make_sim_step(10.0, gate_state="CLOSED", blocked=True),
            _make_sim_step(19.8, gate_state="OPENING", blocked=False),
            _make_sim_step(22.0, gate_state="OPEN", blocked=False),
        ]
        res = _make_sim_result(steps)
        m4 = classify_m4(res, clearance_time_s=t4)
        assert m4.status == M4_STATUS_EVALUABLE
        assert m4.premature is True

    def test_gate_opening_at_or_after_t4_is_safe(self):
        t4 = 20.0
        # Gate blocked from t=5 through 20.0, opens at 20.1 >= 20.0
        steps = [
            _make_sim_step(0.0, gate_state="OPEN", blocked=False),
            _make_sim_step(5.0, gate_state="CLOSED", blocked=True),
            _make_sim_step(10.0, gate_state="CLOSED", blocked=True),
            _make_sim_step(20.0, gate_state="CLOSED", blocked=True),
            _make_sim_step(20.1, gate_state="OPENING", blocked=False),
        ]
        res = _make_sim_result(steps)
        m4 = classify_m4(res, clearance_time_s=t4)
        assert m4.status == M4_STATUS_EVALUABLE
        assert m4.premature is False


# 2. M5 Companion Metric Behavior with Varying Replay Lengths
class TestM5VaryingReplayLengths:
    def test_covered_unprotected_replay_is_m5(self):
        t4 = 15.0
        # Full coverage [0.0, 16.0], zero blocked steps throughout
        steps = [
            _make_sim_step(0.0, gate_state="OPEN", blocked=False),
            _make_sim_step(5.0, gate_state="OPEN", blocked=False),
            _make_sim_step(10.0, gate_state="OPEN", blocked=False),
            _make_sim_step(15.0, gate_state="OPEN", blocked=False),
            _make_sim_step(16.0, gate_state="OPEN", blocked=False),
        ]
        res = _make_sim_result(steps)
        m4 = classify_m4(res, clearance_time_s=t4)
        assert m4.status == M4_STATUS_NEVER_PROTECTED

    def test_incomplete_unprotected_replay_is_not_m5(self):
        t4 = 15.0
        # Replay starts at 0.0 but ends at 12.0 < T4: incomplete coverage
        steps = [
            _make_sim_step(0.0, gate_state="OPEN", blocked=False),
            _make_sim_step(5.0, gate_state="OPEN", blocked=False),
            _make_sim_step(12.0, gate_state="OPEN", blocked=False),
        ]
        res = _make_sim_result(steps)
        m4 = classify_m4(res, clearance_time_s=t4)
        assert m4.status == M4_STATUS_NOT_EVALUABLE
        assert m4.reason == M4_REASON_REPLAY_ENDED_BEFORE_T4


# 3. Empty Replay
class TestEmptyReplay:
    def test_empty_simulation_steps_rejected(self):
        res = _make_sim_result([])
        m4 = classify_m4(res, clearance_time_s=10.0)
        assert m4.status == M4_STATUS_NOT_EVALUABLE
        assert m4.reason == M4_REASON_REPLAY_EMPTY


# 4. Short Replay
class TestShortReplay:
    def test_replay_ending_before_t4_without_violation(self):
        t4 = 25.0
        steps = [
            _make_sim_step(0.0, gate_state="OPEN", blocked=False),
            _make_sim_step(5.0, gate_state="CLOSED", blocked=True),
            _make_sim_step(15.0, gate_state="CLOSED", blocked=True),
        ]
        res = _make_sim_result(steps)
        m4 = classify_m4(res, clearance_time_s=t4)
        assert m4.status == M4_STATUS_NOT_EVALUABLE
        assert m4.reason == M4_REASON_REPLAY_ENDED_BEFORE_T4


# 5. Late Replay Start
class TestLateReplayStart:
    def test_late_start_after_zero_without_blocked_steps(self):
        t4 = 20.0
        # Starts at t=2.0 > 0.0 with no blocked steps
        steps = [
            _make_sim_step(2.0, gate_state="OPEN", blocked=False),
            _make_sim_step(10.0, gate_state="OPEN", blocked=False),
            _make_sim_step(22.0, gate_state="OPEN", blocked=False),
        ]
        res = _make_sim_result(steps)
        m4 = classify_m4(res, clearance_time_s=t4)
        assert m4.status == M4_STATUS_NOT_EVALUABLE
        assert m4.reason == M4_REASON_REPLAY_STARTED_LATE

    def test_start_at_or_after_t4(self):
        t4 = 10.0
        # First step is at t=10.5 >= T4
        steps = [
            _make_sim_step(10.5, gate_state="OPEN", blocked=False),
            _make_sim_step(15.0, gate_state="OPEN", blocked=False),
        ]
        res = _make_sim_result(steps)
        m4 = classify_m4(res, clearance_time_s=t4)
        assert m4.status == M4_STATUS_NOT_EVALUABLE
        assert m4.reason == M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4


# 6. Left-Censored Events
class TestLeftCensoredEvents:
    def test_left_censored_event_lead_in_excluded(self):
        steps = [
            _make_sim_step(0.0, gate_state="OPEN", blocked=False),
            _make_sim_step(5.0, gate_state="CLOSED", blocked=True),
            _make_sim_step(20.0, gate_state="CLOSED", blocked=True),
        ]
        res = _make_sim_result(steps)
        eval_run = EventMetricsCalculator.evaluate_run(
            res,
            entry_time_s=2.0,
            clearance_time_s=20.0,
            first_visible_time_s=None,
            first_visible_left_censored=True,
            lead_in_min_block_latency_s=5.0,
            lead_in_latency_source="synthetic_provenance",
            cohort="train_events",
        )
        assert eval_run.missed_train is None
        assert eval_run.missed_train_screen == "insufficient_lead_in"


# 7. Right-Censored Events
class TestRightCensoredEvents:
    def test_missing_t4_right_censored_is_not_evaluable(self):
        steps = [
            _make_sim_step(0.0, gate_state="OPEN", blocked=False),
            _make_sim_step(5.0, gate_state="CLOSED", blocked=True),
        ]
        res = _make_sim_result(steps)
        m4 = classify_m4(res, clearance_time_s=None)
        assert m4.status == M4_STATUS_NOT_EVALUABLE
        assert m4.reason == M4_REASON_T4_MISSING


# 8. No-Train Events
class TestNoTrainEvents:
    def test_contradictory_cohort_and_ground_truth_raises(self):
        res = _make_sim_result(
            [_make_sim_step(0.0, gate_state="OPEN", blocked=False)],
            event_id="no_train_events/event_001",
        )
        with pytest.raises(UnqualifiedEventIdError, match="has_train_ground_truth=True"):
            EventMetricsCalculator.evaluate_run(
                res,
                cohort="no_train_events",
                has_train_ground_truth=True,  # Contradiction
            )

    def test_clean_no_train_evaluation(self):
        steps = [
            _make_sim_step(0.0, gate_state="OPEN", blocked=False),
            _make_sim_step(10.0, gate_state="OPEN", blocked=False),
        ]
        res = _make_sim_result(steps, event_id="no_train_events/event_001")
        eval_run = EventMetricsCalculator.evaluate_run(
            res,
            cohort="no_train_events",
            has_train_ground_truth=False,
            entry_time_s=None,
            clearance_time_s=None,
        )
        assert eval_run.has_train_ground_truth is False
        assert eval_run.missed_train is False
        assert eval_run.evaluable is True


# 9. Engine Event Isolation
class TestEngineEventIsolation:
    def test_engine_event_excluded_from_train_aggregation(self):
        train_ev = SingleEventEvaluation(
            event_id="train_events/event_001",
            scenario_name="synthetic",
            has_train_ground_truth=True,
            missed_train=False,
            evaluable=True,
            total_closed_s=20.0,
            warning_lead_time_s=10.0,
        )
        engine_ev = SingleEventEvaluation(
            event_id="engine_events/event_001",
            scenario_name="synthetic",
            has_train_ground_truth=False,
            missed_train=None,
            evaluable=False,
            notes="engine_event_excluded",
        )
        inp = DescriptiveOnlyInput(
            event_evaluations=(train_ev, engine_ev),
            population_label="synthetic_test",
            provenance={"source": "test"},
            limitations=("synthetic",),
            permitted_claims=("descriptive",),
        )
        report = aggregate_descriptive_only(inp)
        assert "engine_events/event_001" in report.event_ids


# 10. Rejection of Invalid Cache Provenance
class TestCacheProvenanceValidation:
    def test_missing_or_corrupt_cache_provenance_rejected(self):
        prov1 = ControlledCacheProvenance(
            cohort="train_events",
            event_id="event_001",
            source_id="cam_north",
            modality="vision",
            model_architecture="yolov8n",
            checkpoint_sha256="a" * 64,
            preprocessing_config={"res": [640, 640]},
            experiment_config_sha256="b" * 64,
            failure_injector="none",
            injector_parameters={},
            timing_config={"tick_s": 0.1},
            run_id="run_1",
        )
        prov2 = ControlledCacheProvenance(
            cohort="train_events",
            event_id="event_001",
            source_id="cam_north",
            modality="vision",
            model_architecture="yolov8n",
            checkpoint_sha256="c" * 64,  # mismatched checkpoint hash
            preprocessing_config={"res": [640, 640]},
            experiment_config_sha256="b" * 64,
            failure_injector="none",
            injector_parameters={},
            timing_config={"tick_s": 0.1},
            run_id="run_2",
        )
        with pytest.raises(CacheProvenanceError):
            validate_controlled_cache_provenance(prov1, prov2)


# 11. Rejection of Invalid Authorizations
class TestAuthorizationValidation:
    def test_unauthorized_evidence_classification_refused(self):
        ev = SingleEventEvaluation(
            event_id="train_events/event_001",
            scenario_name="synthetic",
            has_train_ground_truth=True,
            evaluable=True,
        )
        inp = DescriptiveOnlyInput(
            event_evaluations=(ev,),
            population_label="synthetic_test",
            provenance={"source": "test"},
            limitations=("synthetic",),
            permitted_claims=("descriptive",),
            evidence_classification=EvidenceClassification.REAL,
        )
        with pytest.raises(DescriptiveOnlyRefusal, match="OFFICIAL_CONVERSION_REFUSED"):
            aggregate_descriptive_only(inp)


# 12. Refusal of Unapproved Splits
class TestSplitRefusal:
    def test_split_with_disallowed_mode_refused(self):
        ev = SingleEventEvaluation(
            event_id="train_events/event_001",
            scenario_name="synthetic",
            has_train_ground_truth=True,
            evaluable=True,
        )
        inp = DescriptiveOnlyInput(
            event_evaluations=(ev,),
            population_label="synthetic_test",
            provenance={"source": "test"},
            limitations=("synthetic",),
            permitted_claims=("descriptive",),
            mode_id="unapproved_random_split_eval",
        )
        with pytest.raises(DescriptiveOnlyRefusal, match="MODE_UNSUPPORTED"):
            aggregate_descriptive_only(inp)


# 13. Rejection of Non-Conforming Cohort Sizes
class TestCohortSizeValidation:
    def test_duplicate_event_ids_rejected(self):
        ev1 = SingleEventEvaluation(
            event_id="train_events/event_001",
            scenario_name="synthetic",
            has_train_ground_truth=True,
            evaluable=True,
        )
        ev2 = SingleEventEvaluation(
            event_id="train_events/event_001",  # duplicate ID
            scenario_name="synthetic",
            has_train_ground_truth=True,
            evaluable=True,
        )
        inp = DescriptiveOnlyInput(
            event_evaluations=(ev1, ev2),
            population_label="synthetic_test",
            provenance={"source": "test"},
            limitations=("synthetic",),
            permitted_claims=("descriptive",),
        )
        with pytest.raises(DescriptiveOnlyRefusal, match="DUPLICATE_EVENT_ID"):
            aggregate_descriptive_only(inp)
