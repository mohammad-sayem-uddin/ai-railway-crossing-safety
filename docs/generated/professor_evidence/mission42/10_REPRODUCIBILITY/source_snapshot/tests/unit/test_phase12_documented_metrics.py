"""Documented-protocol metric reporting: exclusions with reasons and nuisance totals."""

from __future__ import annotations

import pytest

from railway_detection.evaluation.evaluation_runner import Phase12EvaluationRunner
from railway_detection.evaluation.ground_truth_loader import ApprovedEventGroundTruth
from railway_detection.evaluation.metrics import EventMetricsCalculator
from railway_detection.evaluation.protocol_choices import (
    DOCUMENTED_PROFILE,
    IMPLEMENTED_OPTIONS,
    PROTOCOL_CHOICE_KEYS,
    ProtocolChoiceError,
    effective_profile,
    profile_sha256,
    unresolved_decisions,
)
from railway_detection.simulation.runner import SimulationRunResult, SimulationStep


def _step(t: float, blocked: bool) -> SimulationStep:
    return SimulationStep(
        timestamp_s=t,
        crossing_state="GATE_CLOSED" if blocked else "IDLE",
        gate_state="CLOSED" if blocked else "OPEN",
        gate_angle_deg=0.0 if blocked else 90.0,
        is_passage_blocked=blocked,
        decision=None,
    )


def _result(event_id: str, blocked_pattern: list[bool], closed_s: float) -> SimulationRunResult:
    return SimulationRunResult(
        event_id=event_id,
        scenario_name="synthetic",
        steps=[_step(0.5 * i, b) for i, b in enumerate(blocked_pattern)],
        total_duration_s=0.5 * len(blocked_pattern),
        closed_duration_s=closed_s,
    )


def test_nuisance_reporting_gives_seconds_episodes_and_exposure_but_no_rate():
    quiet = EventMetricsCalculator.evaluate_run(
        _result("no_train_events/n1", [False] * 6, 0.0), has_train_ground_truth=False
    )
    noisy = EventMetricsCalculator.evaluate_run(
        _result("no_train_events/n2", [True, True, False, False, True, False], 1.5),
        has_train_ground_truth=False,
    )
    assert quiet.closure_episodes == 0 and quiet.blocked_seconds == 0.0
    assert noisy.closure_episodes == 2
    summary = EventMetricsCalculator.aggregate_cohort([quiet, noisy])
    assert summary.false_alarm_count == 1 and summary.false_alarm_evaluable_count == 2
    assert summary.false_alarm_closure_episodes == 2
    assert summary.false_alarm_blocked_seconds == 1.5
    assert summary.false_alarm_exposure_s == 6.0
    payload = summary.to_dict()
    assert payload["false_alarm_hourly_rate"] == "not_reported_by_protocol"
    assert not any(isinstance(v, float) and "per_hour" in k for k, v in payload.items())


def test_initially_blocked_replay_counts_as_one_episode():
    evaluation = EventMetricsCalculator.evaluate_run(
        _result("no_train_events/n", [True, True, True], 1.5), has_train_ground_truth=False
    )
    assert evaluation.closure_episodes == 1


def test_censored_boundaries_are_excluded_with_a_stated_reason_not_zeroed():
    truth = ApprovedEventGroundTruth(
        event_id="train_events/evt_c",
        cohort="train_events",
        review_id="r",
        reviewer_id="synthetic",
        observable_boundaries={"T1_danger_zone_entry": 2.0},
        censored_boundaries=("T4_tail_clearance",),
        uncertain_boundaries=(),
        not_applicable_boundaries=(),
    )
    reasons = Phase12EvaluationRunner._exclusion_reasons(truth)
    assert reasons == {"T4_tail_clearance": "censored"}
    evaluation = EventMetricsCalculator.evaluate_run(
        _result("train_events/evt_c", [False, False, True, True, True, True], 1.0),
        entry_time_s=2.0,
        clearance_time_s=None,
        exclusion_reasons=reasons,
        premature_opening_window="t1_entry_to_t4_clearance",
    )
    assert evaluation.premature_opening is None
    assert evaluation.clearance_latency_s is None
    summary = EventMetricsCalculator.aggregate_cohort([evaluation])
    assert summary.premature_opening_rate is None
    assert summary.premature_opening_evaluable_count == 0
    excluded = {m: [e["reason"] for e in v] for m, v in summary.exclusions.items()}
    assert excluded["premature_opening"] == ["T4_tail_clearance:censored"]
    assert excluded["clearance_latency"] == ["T4_tail_clearance:censored"]
    assert "missed_train" not in excluded  # T1 was usable


def test_uncertain_and_unknown_boundaries_are_distinguished():
    truth = ApprovedEventGroundTruth(
        event_id="train_events/e",
        cohort="train_events",
        review_id="r",
        reviewer_id="s",
        observable_boundaries={},
        censored_boundaries=(),
        uncertain_boundaries=("T1_danger_zone_entry",),
        not_applicable_boundaries=("T4_tail_clearance",),
    )
    assert Phase12EvaluationRunner._exclusion_reasons(truth) == {
        "T1_danger_zone_entry": "uncertain",
        "T4_tail_clearance": "not_applicable_or_unknown",
    }


def test_documented_profile_is_fully_implemented_and_hash_is_stable():
    profile = effective_profile({"premature_opening_window": "t1_entry_to_t4_clearance"})
    assert set(profile) == set(PROTOCOL_CHOICE_KEYS)
    for key, value in profile.items():
        assert value in IMPLEMENTED_OPTIONS[key], key
        assert DOCUMENTED_PROFILE[key][1], f"{key} has no cited source"
        assert DOCUMENTED_PROFILE[key][0] is not None or key == "premature_opening_window"
    assert profile_sha256(profile) == profile_sha256(dict(reversed(list(profile.items()))))
    changed = dict(profile, false_alarm_measure="event_level_any_closure")
    assert profile_sha256(changed) != profile_sha256(profile)


def test_premature_opening_window_is_unresolved_and_never_defaulted():
    value, source, standing = DOCUMENTED_PROFILE["premature_opening_window"]
    assert value is None  # no researcher-attributed acceptance of either candidate
    assert "UNRESOLVED" in standing and "D-10" in standing
    assert "FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL" in source and "EXPERIMENT_DESIGN_FINAL" in source
    assert unresolved_decisions() == ["premature_opening_window"]
    with pytest.raises(ProtocolChoiceError) as info:
        effective_profile()
    assert info.value.code == "PREMATURE_OPENING_DEFINITION_UNDECIDED"
    # Both candidates are selectable once explicitly chosen; neither is a default.
    for choice in ("t1_entry_to_t4_clearance", "first_blocked_to_t4_clearance"):
        assert effective_profile({"premature_opening_window": choice})[
            "premature_opening_window"
        ] == choice
    # An unimplemented alternative is refused, not silently substituted.
    with pytest.raises(ProtocolChoiceError) as info:
        effective_profile({"premature_opening_window": "t0_first_visible_to_t4_clearance"})
    assert info.value.code == "PROTOCOL_CHOICE_NOT_IMPLEMENTED"
