"""Phase 1 (Mission 5B) metric-contract closure -- synthetic regression tests.

Every test calls the PRODUCTION functions (``classify_m4``, ``EventMetricsCalculator``,
``evaluate_event_replay``, the lead-in screen and its derivation, the preservation-manifest
builder); no test re-implements the algorithm it checks.  Everything is hand-built in memory or in
pytest's tmp directory: no media, no real events, no cache, no inference.

Researcher-confirmed decisions covered: DEC-C01 (M5 needs zero-origin coverage), DEC-C02 (empty
protection interval stays NOT_EVALUABLE), DEC-C03 (physical screen primary, literal design M3
reported beside it), DEC-C04 (5A.1 fixes are the baseline), DEC-C05 (one-microsecond grid).
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from railway_detection.evaluation.clock_aware import (
    EventReplay,
    SystemReplay,
    evaluate_event_replay,
)
from railway_detection.evaluation.ground_truth_loader import ApprovedEventGroundTruth
from railway_detection.evaluation.lead_in_screen import (
    SCREEN_INSUFFICIENT_LEAD_IN,
    SCREEN_NOT_APPLIED,
    SCREEN_PASSED,
    SCREEN_T1_MISSING,
    SCREEN_UNVERIFIABLE,
    derive_min_block_latency_s,
    derive_min_block_latency_with_provenance,
    screen_missed_train_lead_in,
)
from railway_detection.evaluation.metrics import (
    M4_INCOMPLETE_REPLAY_REASONS,
    M4_REASON_NO_INTERIOR_STEPS,
    M4_REASON_REPLAY_ENDED_BEFORE_T4,
    M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4,
    M4_REASON_REPLAY_STARTED_LATE,
    M4_STATUS_EVALUABLE,
    M4_STATUS_NEVER_PROTECTED,
    M4_STATUS_NOT_EVALUABLE,
    M4_WINDOW,
    EventMetricsCalculator,
    SingleEventEvaluation,
    UnqualifiedEventIdError,
    classify_m4,
    m4_premature_opening,
)
from railway_detection.evaluation.timebase import TIMESTAMP_ROUND_DIGITS, normalize_timestamp
from railway_detection.experiments.frozen_config import load_frozen_config
from railway_detection.simulation.runner import SimulationRunResult, SimulationStep

REPO = Path(__file__).resolve().parents[2]
TRAIN = "train_events/event_001"
T1 = "T1_danger_zone_entry"
T4 = "T4_tail_clearance"
T0 = "T0_first_visible"


# ---------------------------------------------------------------------------
# synthetic builders
# ---------------------------------------------------------------------------


def _step(t, blocked=True, gate=None):
    gate = gate or ("CLOSED" if blocked else "OPEN")
    return SimulationStep(t, "TRAIN_PRESENT", gate, 0.0 if blocked else 90.0, blocked, None)  # type: ignore[arg-type]


def _run(steps, event=TRAIN):
    return SimulationRunResult(
        event_id=event,
        scenario_name="synthetic",
        steps=steps,
        total_duration_s=steps[-1].timestamp_s if steps else 0.0,
        closed_duration_s=0.0,
    )


def _secs(blocked_from, stop, start=0, unblocked_at=()):
    """1 Hz steps start..stop (inclusive); blocked from ``blocked_from``; some forced open."""
    return [
        _step(
            float(t),
            blocked=(blocked_from is not None and t >= blocked_from and t not in unblocked_at),
        )
        for t in range(start, stop + 1)
    ]


def _ticks(blocked_from_tick, last_tick, tick=0.2):
    """Dense ``tick`` replay on the grid; blocked from tick index ``blocked_from_tick``."""
    return [
        _step(normalize_timestamp(i * tick), blocked=i >= blocked_from_tick)
        for i in range(last_tick + 1)
    ]


def _m4(steps, t4=5.0):
    return classify_m4(_run(steps), t4)


# ---------------------------------------------------------------------------
# 1-6  Replay start coverage (DEC-C01)
# ---------------------------------------------------------------------------


class TestReplayStartCoverage:
    def test_full_zero_origin_replay_with_no_block_before_t4_is_valid_m5(self):
        c = _m4(_secs(None, 6))
        assert c.status == M4_STATUS_NEVER_PROTECTED
        assert c.never_protected is True and c.premature is None
        assert c.reason is None and c.replay_complete is True
        assert c.first_step_s == 0.0 and c.last_step_s == 6.0 and c.first_blocked_s is None

    def test_replay_starting_exactly_at_t4_is_not_evaluable(self):
        c = _m4([_step(5.0, False), _step(6.0, False)])
        assert c.status == M4_STATUS_NOT_EVALUABLE
        assert c.reason == M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4
        assert c.never_protected is None and c.premature is None and c.replay_complete is False
        assert c.first_step_s == 5.0

    def test_replay_starting_after_t4_is_not_evaluable(self):
        c = _m4([_step(6.0, False), _step(7.0, False)])
        assert c.status == M4_STATUS_NOT_EVALUABLE
        assert c.reason == M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4
        assert c.never_protected is None

    def test_a_replay_that_begins_blocked_at_or_after_t4_is_also_not_m5(self):
        c = _m4([_step(5.0, True), _step(6.0, True)])
        assert c.status == M4_STATUS_NOT_EVALUABLE
        assert c.reason == M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4

    @pytest.mark.parametrize("first", [1.0, 4.0, 4.9, 0.2, 0.000001])
    def test_late_starting_unblocked_replay_is_not_evaluable_not_m5(self, first):
        # No tolerance: even one tick (or one microsecond) after the origin is "late".
        steps = [_step(first, False), _step(5.0, False), _step(6.0, False)]
        c = _m4(steps)
        assert c.status == M4_STATUS_NOT_EVALUABLE
        assert c.reason == M4_REASON_REPLAY_STARTED_LATE
        assert c.never_protected is None and c.premature is None and c.replay_complete is False

    def test_no_arbitrary_cutoff_discontinuity(self):
        """First step 4.9 and 5.0 (T4=5.0) are both refused -- unlike the reverted 5A.1 attempt."""
        for first in (4.9, 5.0):
            assert _m4([_step(first, False), _step(6.0, False)]).status == M4_STATUS_NOT_EVALUABLE

    def test_first_block_exactly_at_t4_after_full_coverage_is_valid_m5(self):
        c = _m4(_secs(5, 6))  # open 0..4, first block at 5.0 == T4
        assert c.status == M4_STATUS_NEVER_PROTECTED and c.never_protected is True
        assert c.first_blocked_s == 5.0 and c.replay_complete is True

    def test_valid_m4_violation_inside_the_open_interval(self):
        steps = _secs(1, 6, unblocked_at=(3,))  # blocked at 1, open at 3, blocked again, T4 = 5
        c = _m4(steps)
        assert c.status == M4_STATUS_EVALUABLE and c.premature is True
        assert c.never_protected is False and c.first_blocked_s == 1.0
        assert c.interior_step_count == 3  # steps at 2, 3, 4

    def test_witnessed_violation_survives_a_late_start_and_an_early_end(self):
        late_and_short = [_step(2.0), _step(3.0, False), _step(4.0)]  # starts at 2.0, ends at 4.0
        c = _m4(late_and_short)
        assert c.status == M4_STATUS_EVALUABLE and c.premature is True
        assert c.replay_complete is False  # the tail was not observed, the violation was

    def test_m4_is_not_excluded_merely_because_the_replay_started_after_zero(self):
        """M4's interval starts at the observed first blocked step; no zero origin is needed."""
        c = _m4([_step(2.0), _step(3.0), _step(4.0), _step(5.0), _step(6.0)])
        assert c.status == M4_STATUS_EVALUABLE and c.premature is False
        assert c.first_blocked_s == 2.0 and c.first_step_s == 2.0 and c.interior_step_count == 2

    def test_truncated_unblocked_replay_is_still_ended_before_t4(self):
        c = _m4(_secs(None, 3))
        assert c.status == M4_STATUS_NOT_EVALUABLE and c.reason == M4_REASON_REPLAY_ENDED_BEFORE_T4

    def test_backward_compatible_tuple_view(self):
        assert m4_premature_opening(_run(_secs(None, 6)), 5.0) == (None, True)
        assert m4_premature_opening(_run([_step(6.0, False)]), 5.0) == (None, None)
        assert m4_premature_opening(_run(_secs(1, 6, unblocked_at=(3,))), 5.0) == (True, False)

    def test_new_reasons_are_incomplete_replay_reasons(self):
        assert M4_REASON_REPLAY_STARTED_LATE in M4_INCOMPLETE_REPLAY_REASONS
        assert M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4 in M4_INCOMPLETE_REPLAY_REASONS


# ---------------------------------------------------------------------------
# 7-9  Empty protection interval (DEC-C02)
# ---------------------------------------------------------------------------


class TestEmptyProtectionInterval:
    def test_no_step_strictly_inside_the_interval_is_not_evaluable_with_diagnostics(self):
        steps = [_step(float(t), False) for t in range(4)] + [_step(4.0), _step(5.0), _step(6.0)]
        c = _m4(steps)  # blocked first at 4.0; the next step is 5.0 == T4
        assert c.status == M4_STATUS_NOT_EVALUABLE and c.reason == M4_REASON_NO_INTERIOR_STEPS
        assert c.premature is None and c.never_protected is None and c.replay_complete is True
        assert c.first_blocked_s == 4.0 and c.last_step_s == 6.0
        assert c.interior_step_count == 0 and c.max_step_gap_s == 1.0

    def test_sparse_replay_with_a_large_gap_is_not_evaluable_not_safe(self):
        c = _m4([_step(0.0), _step(5.0)])
        assert c.status == M4_STATUS_NOT_EVALUABLE and c.reason == M4_REASON_NO_INTERIOR_STEPS
        assert c.premature is None  # never "protected"
        assert c.max_step_gap_s == 5.0 and c.interior_step_count == 0
        c = _m4([_step(0.0), _step(30.0)])
        assert c.premature is None and c.max_step_gap_s == 30.0

    def test_normal_dense_replay_with_no_interior_sample_is_not_evaluable(self):
        """5 Hz replay that first blocks at the last tick before T4 (4.8 s, T4 = 5.0 s)."""
        c = _m4(_ticks(blocked_from_tick=24, last_tick=30))
        assert c.first_blocked_s == 4.8
        assert c.status == M4_STATUS_NOT_EVALUABLE and c.reason == M4_REASON_NO_INTERIOR_STEPS
        assert c.max_step_gap_s == 0.2  # dense sampling does not rescue it: no tick tolerance
        assert c.interior_step_count == 0

    def test_one_interior_tick_makes_the_same_replay_evaluable(self):
        c = _m4(_ticks(blocked_from_tick=23, last_tick=30))  # first block 4.6; 4.8 is interior
        assert c.status == M4_STATUS_EVALUABLE and c.premature is False
        assert c.interior_step_count == 1

    def test_empty_interval_is_counted_under_its_reason_and_excluded_from_denominators(self):
        ev = EventMetricsCalculator.evaluate_run(
            _run([_step(0.0), _step(5.0)]), clearance_time_s=5.0, premature_opening_window=M4_WINDOW
        )
        assert ev.m4_status == M4_STATUS_NOT_EVALUABLE and ev.premature_opening is None
        assert ev.metric_exclusions["premature_opening"] == M4_REASON_NO_INTERIOR_STEPS
        summary = EventMetricsCalculator.aggregate_cohort([ev])
        assert summary.premature_opening_evaluable_count == 0
        assert summary.m4_no_violation_count == 0
        assert summary.m4_not_evaluable_reasons == {M4_REASON_NO_INTERIOR_STEPS: 1}
        assert summary.never_protected_evaluable_count == 0


# ---------------------------------------------------------------------------
# 14  Timestamp normalization (DEC-C05)
# ---------------------------------------------------------------------------


class TestTimestampNormalization:
    def test_grid_is_one_microsecond(self):
        assert TIMESTAMP_ROUND_DIGITS == 6
        assert normalize_timestamp(0.1 + 0.2) == 0.3
        assert normalize_timestamp(5.0000001) == 5.0  # 0.1 us collapses
        assert normalize_timestamp(5.000001) != 5.0  # 1 us survives

    def test_a_step_equal_to_t4_on_the_grid_is_outside_the_open_interval(self):
        """Raw floats: step 0.3 < T4 = 0.1 + 0.2, which would flag a violation."""
        steps = [_step(0.0), _step(0.1), _step(0.3, False), _step(0.5)]
        c = classify_m4(_run(steps), 0.1 + 0.2)
        assert c.status == M4_STATUS_EVALUABLE and c.premature is False
        assert c.interior_step_count == 1  # only 0.1

    def test_a_last_step_equal_to_t4_on_the_grid_covers_t4(self):
        """Raw floats: last step 0.3 < T4 = 0.1 + 0.2 would make the replay look truncated."""
        c = classify_m4(_run([_step(0.0), _step(0.1), _step(0.3)]), 0.1 + 0.2)
        assert c.status == M4_STATUS_EVALUABLE and c.replay_complete is True

    def test_first_block_equal_to_t4_on_the_grid_is_not_before_t4(self):
        c = classify_m4(_run([_step(0.0, False), _step(0.1, False), _step(0.3)]), 0.1 + 0.2)
        assert c.status == M4_STATUS_NEVER_PROTECTED  # first block at T4 == not before T4

    def test_genuine_one_microsecond_values_keep_their_strict_order(self):
        base = [_step(0.0), _step(1.0)]
        below = classify_m4(_run([*base, _step(4.999999, False), _step(6.0)]), 5.0)
        above = classify_m4(_run([*base, _step(5.000001, False), _step(6.0)]), 5.0)
        assert below.premature is True  # 1 us before T4: inside (t_blocked, T4)
        assert above.premature is False  # 1 us after T4: outside
        assert classify_m4(_run([*base, _step(5.0, False), _step(6.0)]), 5.0).premature is False
        # and T4 itself, 1 us earlier / later than the opening step
        steps = [*base, _step(5.0, False), _step(6.0)]
        assert classify_m4(_run(steps), 4.999999).premature is False
        assert classify_m4(_run(steps), 5.000001).premature is True

    def test_origin_and_start_are_compared_on_the_grid(self):
        assert _m4([_step(1e-7, False), _step(5.0, False)]).status == M4_STATUS_NEVER_PROTECTED
        late = _m4([_step(1e-6, False), _step(5.0, False)])
        assert late.reason == M4_REASON_REPLAY_STARTED_LATE

    def test_steps_that_collapse_onto_one_grid_point_are_rejected(self):
        with pytest.raises(ValueError, match="strictly increasing"):
            classify_m4(_run([_step(1.0), _step(1.0000001)]), 5.0)
        with pytest.raises(ValueError, match="strictly increasing"):
            EventMetricsCalculator.evaluate_run(_run([_step(1.0), _step(1.0000001)]))

    def test_gap_diagnostic_is_grid_clean(self):
        c = _m4(_ticks(blocked_from_tick=23, last_tick=30))
        assert c.max_step_gap_s == 0.2

    def test_evaluate_run_boundary_ordering_uses_the_grid(self):
        with pytest.raises(ValueError, match="after entry_time_s"):
            EventMetricsCalculator.evaluate_run(
                _run(_secs(None, 6)), entry_time_s=0.3, clearance_time_s=0.1 + 0.2
            )
        ok = EventMetricsCalculator.evaluate_run(
            _run(_secs(None, 6)), entry_time_s=0.3, clearance_time_s=0.300001
        )
        assert ok.evaluable

    def test_entry_step_matching_is_symmetric_on_the_grid(self):
        # |4.55 - 4.8| is 0.25000000000000044 as a raw float: just outside 0.25 by noise only.
        steps = [_step(4.8, blocked=False), _step(9.0, blocked=True)]
        ev = EventMetricsCalculator.evaluate_run(
            _run(steps), entry_time_s=4.55, clearance_time_s=9.0
        )
        assert ev.missed_train is True  # the 4.8 step counts as at entry
        far = EventMetricsCalculator.evaluate_run(
            _run(steps), entry_time_s=4.549999, clearance_time_s=9.0
        )
        assert far.missed_train is None  # 0.250001 s away: genuinely outside

    def test_clearance_latency_uses_the_grid(self):
        steps = [
            _step(0.0),
            SimulationStep(0.3, "GATE_OPENING", "OPENING", 10.0, False, None),  # type: ignore[arg-type]
        ]
        ev = EventMetricsCalculator.evaluate_run(
            _run(steps), entry_time_s=0.05, clearance_time_s=0.1 + 0.2
        )
        assert ev.clearance_latency_s == 0.0  # the 0.3 step is AT T4 on the grid, not 4e-17 after

    def test_lead_in_screen_compares_available_time_on_the_grid(self):
        # 3.8 - 0.2 == 3.5999999999999996 as a raw float, i.e. "less than 3.6".
        edge = screen_missed_train_lead_in(
            3.8,
            first_visible_time_s=0.2,
            first_visible_left_censored=False,
            min_block_latency_s=3.6,
            min_block_latency_source="unit",
        )
        assert edge.outcome == SCREEN_PASSED and edge.available_lead_in_s == 3.6
        short = screen_missed_train_lead_in(
            3.8,
            first_visible_time_s=0.200001,
            first_visible_left_censored=False,
            min_block_latency_s=3.6,
            min_block_latency_source="unit",
        )
        assert short.outcome == SCREEN_INSUFFICIENT_LEAD_IN


# ---------------------------------------------------------------------------
# multi-system builders (clock-aware evaluation)
# ---------------------------------------------------------------------------


def _truth(
    boundaries=None,
    cameras=None,
    event="train_events/case",
    cohort="train_events",
    censored=(),
    uncertain=(),
):
    boundaries = {T1: 5.0, T4: 10.0} if boundaries is None else boundaries
    cameras = cameras or {T0: "front", T1: "front", T4: "back"}
    return ApprovedEventGroundTruth(
        event_id=event,
        cohort=cohort,
        review_id="r",
        reviewer_id="s",
        observable_boundaries=boundaries,
        censored_boundaries=tuple(censored),
        uncertain_boundaries=tuple(uncertain),
        not_applicable_boundaries=(),
        boundary_cameras={k: v for k, v in cameras.items() if k in boundaries},
    )


def _replay(systems, event="train_events/case", mode="independent_camera", cohort="train_events"):
    return EventReplay(
        event_id=event,
        cohort=cohort,
        camera_mode=mode,
        systems={
            name: SystemReplay(name, offsets, _run(steps, event))
            for name, (offsets, steps) in systems.items()
        },
    )


FRONT_BLOCKED = ({"front": 0.0}, _secs(3, 12))  # blocked from 3 s: the barrier is down at T1 = 5
BACK_OFFSETS = {"back": 0.0}


def _evaluate(back_steps, front=FRONT_BLOCKED, event="train_events/case", truth=None, **kwargs):
    replay = _replay({"front": front, "back": (BACK_OFFSETS, back_steps)}, event=event)
    return evaluate_event_replay(
        replay, truth or _truth(event=event), premature_opening_window=M4_WINDOW, **kwargs
    )


# ---------------------------------------------------------------------------
# 10-11, 13  Multi-system M4/M5 propagation and front/back responsibilities (F-19)
# ---------------------------------------------------------------------------


class TestClockAwareM4M5Propagation:
    def test_never_protected_is_propagated_from_the_t4_system(self):
        ev = _evaluate(_secs(None, 12))
        assert ev.never_protected is True and ev.premature_opening is None
        assert ev.m4_status == M4_STATUS_NEVER_PROTECTED
        assert ev.m4_reason is None and ev.m4_replay_complete is True
        assert "never_protected_before_T4" in ev.metric_exclusions["premature_opening"]

    def test_witnessed_violation_is_propagated(self):
        ev = _evaluate(_secs(2, 12, unblocked_at=(7,)))
        assert ev.premature_opening is True and ev.never_protected is False
        assert ev.m4_status == M4_STATUS_EVALUABLE and ev.m4_replay_complete is True
        assert "premature_opening" not in ev.metric_exclusions

    def test_clean_m4_is_propagated(self):
        ev = _evaluate(_secs(2, 12))
        assert ev.premature_opening is False and ev.never_protected is False
        assert ev.m4_status == M4_STATUS_EVALUABLE and ev.m4_reason is None

    def test_incomplete_replay_reason_is_propagated_not_overwritten(self):
        ev = _evaluate(_secs(2, 8))  # back replay stops before T4 = 10
        assert ev.m4_status == M4_STATUS_NOT_EVALUABLE
        assert ev.m4_reason == M4_REASON_REPLAY_ENDED_BEFORE_T4
        assert ev.m4_replay_complete is False and ev.premature_opening is None
        assert ev.never_protected is None
        assert ev.metric_exclusions["premature_opening"] == M4_REASON_REPLAY_ENDED_BEFORE_T4

    @pytest.mark.parametrize(
        ("back_steps", "reason"),
        [
            (_secs(None, 8) + [_step(9.0), _step(10.0), _step(11.0)], M4_REASON_NO_INTERIOR_STEPS),
            (_secs(None, 12, start=1), M4_REASON_REPLAY_STARTED_LATE),
            (_secs(None, 12, start=10), M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4),
        ],
    )
    def test_every_incomplete_reason_survives_the_multi_system_merge(self, back_steps, reason):
        ev = _evaluate(back_steps)
        assert ev.m4_status == M4_STATUS_NOT_EVALUABLE and ev.m4_reason == reason
        assert ev.metric_exclusions["premature_opening"] == reason
        summary = EventMetricsCalculator.aggregate_cohort([ev])
        assert summary.m4_not_evaluable_reasons == {reason: 1}
        assert summary.exclusions["premature_opening"] == [
            {"event_id": "train_events/case", "reason": reason}
        ]
        assert summary.never_protected_evaluable_count == 0
        assert summary.premature_opening_evaluable_count == 0

    def test_front_placeholder_never_replaces_the_back_stream_answer(self):
        """The front clock has no T4: its ``t4_missing`` classification is only a placeholder."""
        replay = _replay({"front": FRONT_BLOCKED, "back": (BACK_OFFSETS, _secs(None, 12))})
        front_alone = EventMetricsCalculator.evaluate_run(
            replay.systems["front"].result,
            entry_time_s=5.0,
            clearance_time_s=None,
            has_train_ground_truth=True,
            premature_opening_window=M4_WINDOW,
            cohort="train_events",
        )
        assert front_alone.m4_status == M4_STATUS_NOT_EVALUABLE  # non-None, but meaningless
        assert front_alone.m4_reason == "t4_missing"
        merged = evaluate_event_replay(replay, _truth(), premature_opening_window=M4_WINDOW)
        assert merged.m4_status == M4_STATUS_NEVER_PROTECTED
        assert merged.m4_reason is None

    def test_t4_unmappable_on_every_clock_reports_t4_missing_with_boundary_reason(self):
        truth = _truth(boundaries={T1: 5.0}, censored=(T4,))
        ev = _evaluate(_secs(2, 12), truth=truth)
        assert ev.m4_status == M4_STATUS_NOT_EVALUABLE and ev.m4_reason == "t4_missing"
        assert ev.premature_opening is None and ev.never_protected is None
        assert "T4_tail_clearance:censored" in ev.metric_exclusions["premature_opening"]

    def test_m4_is_not_requested_without_the_m4_window(self):
        replay = _replay({"front": FRONT_BLOCKED, "back": (BACK_OFFSETS, _secs(None, 12))})
        ev = evaluate_event_replay(replay, _truth(), premature_opening_window=None)
        assert ev.m4_status is None and ev.never_protected is None
        assert ev.m4_reason is None and ev.m4_replay_complete is None
        assert ev.metric_exclusions["premature_opening"] == "premature_opening_window_undecided"

    def test_missed_train_still_comes_from_the_front_clock(self):
        ev = _evaluate(_secs(None, 12))
        assert ev.missed_train is False  # front barrier is down at T1 = 5 s
        ev = _evaluate(_secs(None, 12), front=({"front": 0.0}, _secs(None, 12)))
        assert ev.missed_train is True

    def test_total_closed_and_per_system_closed_are_unchanged(self):
        ev = _evaluate(_secs(2, 12))
        assert set(ev.per_system_closed_s) == {"front", "back"}
        assert ev.evaluable is True and ev.has_train_ground_truth is True

    def _dual(self, fused_steps, back_steps):
        offsets = {"front": 0.0, "back": 0.0}
        return _replay(
            {
                "fused": (offsets, fused_steps),
                "front": FRONT_BLOCKED,
                "back": (BACK_OFFSETS, back_steps),
            },
            mode="dual_camera",
        )

    def test_a_definite_system_is_preferred_over_an_incomplete_higher_priority_one(self):
        replay = self._dual(fused_steps=_secs(2, 8), back_steps=_secs(2, 12))  # fused ends early
        ev = evaluate_event_replay(replay, _truth(), premature_opening_window=M4_WINDOW)
        assert ev.m4_status == M4_STATUS_EVALUABLE and ev.premature_opening is False
        assert ev.m4_replay_complete is True

    def test_the_record_never_mixes_verdicts_from_two_systems(self):
        """Fused says M5, back says clean M4: the record follows one system, not both."""
        replay = self._dual(fused_steps=_secs(None, 12), back_steps=_secs(2, 12))
        ev = evaluate_event_replay(replay, _truth(), premature_opening_window=M4_WINDOW)
        assert ev.m4_status == M4_STATUS_NEVER_PROTECTED and ev.never_protected is True
        assert ev.premature_opening is None  # not back's False
        assert not (ev.never_protected and ev.premature_opening is not None)

    def test_no_train_and_engine_records_carry_their_cohort(self):
        for cohort in ("no_train_events", "engine_events"):
            event = f"{cohort}/event_001"
            truth = _truth(boundaries={}, event=event, cohort=cohort)
            replay = _replay(
                {"front": ({"front": 0.0}, _secs(None, 6))}, event=event, cohort=cohort
            )
            ev = evaluate_event_replay(replay, truth, premature_opening_window=M4_WINDOW)
            assert ev.cohort == cohort
            assert ev.m4_status is None
        assert ev.evaluable is False and ev.notes == "engine_event_excluded"

    def test_cohort_is_stamped_on_train_records(self):
        assert _evaluate(_secs(2, 12)).cohort == "train_events"

    def test_dual_camera_boundary_offsets_are_normalized(self):
        """T4 = 0.1 s on the back camera + 0.2 s offset is 0.3 s on the fused clock."""
        truth = _truth(boundaries={T1: 0.05, T4: 0.1}, cameras={T1: "front", T4: "back"})
        steps = [_step(0.0), _step(0.1), _step(0.3, False), _step(0.5)]
        replay = _replay({"back": ({"back": 0.2}, steps)}, event="train_events/case")
        ev = evaluate_event_replay(replay, truth, premature_opening_window=M4_WINDOW)
        assert ev.m4_status == M4_STATUS_EVALUABLE and ev.premature_opening is False


# ---------------------------------------------------------------------------
# 12  Lead-in screen propagation (F-19) -- optional and off by default
# ---------------------------------------------------------------------------

LATENCY = 3.6
SOURCE = "unit-test synthetic latency (not an approved threshold)"


class TestClockAwareLeadInPropagation:
    def _screened(self, truth, **kwargs):
        return _evaluate(
            _secs(2, 12),
            truth=truth,
            lead_in_min_block_latency_s=LATENCY,
            lead_in_latency_source=SOURCE,
            **kwargs,
        )

    def test_screen_is_off_unless_requested(self):
        ev = _evaluate(_secs(2, 12))
        assert ev.missed_train_screen == SCREEN_NOT_APPLIED and ev.lead_in_available_s is None

    def test_insufficient_lead_in_comes_from_the_t1_system_and_is_not_a_failure(self):
        ev = self._screened(_truth(boundaries={T0: 2.0, T1: 5.0, T4: 10.0}))
        assert ev.missed_train_screen == SCREEN_INSUFFICIENT_LEAD_IN  # not the back's t1_missing
        assert ev.lead_in_available_s == 3.0
        assert ev.missed_train is None
        assert ev.metric_exclusions["missed_train"] == SCREEN_INSUFFICIENT_LEAD_IN
        summary = EventMetricsCalculator.aggregate_cohort([ev])
        assert summary.missed_train_evaluable_count == 0
        assert summary.missed_train_insufficient_lead_in_count == 1
        assert summary.missed_train_screen_excluded_count == 1

    def test_sufficient_lead_in_passes_and_keeps_the_missed_train_verdict(self):
        ev = self._screened(_truth(boundaries={T0: 1.0, T1: 5.0, T4: 10.0}))
        assert ev.missed_train_screen == SCREEN_PASSED and ev.lead_in_available_s == 4.0
        assert ev.missed_train is False  # front barrier is down at T1

    def test_uncertain_t0_is_unverifiable_never_assumed_visible_from_zero(self):
        truth = _truth(boundaries={T1: 5.0, T4: 10.0}, uncertain=(T0,))
        ev = self._screened(truth)
        assert ev.missed_train_screen == SCREEN_UNVERIFIABLE and ev.lead_in_available_s is None
        assert ev.missed_train is None
        assert ev.metric_exclusions["missed_train"] == SCREEN_UNVERIFIABLE

    def test_censored_t0_without_a_direction_is_unverifiable_too(self):
        truth = _truth(boundaries={T1: 5.0, T4: 10.0}, censored=(T0,))
        assert self._screened(truth).missed_train_screen == SCREEN_UNVERIFIABLE

    def test_missing_t1_keeps_the_boundary_reason(self):
        truth = _truth(boundaries={T4: 10.0}, censored=(T1,))
        ev = self._screened(truth)
        assert ev.missed_train_screen == SCREEN_T1_MISSING and ev.missed_train is None
        assert "T1_danger_zone_entry:censored" in ev.metric_exclusions["missed_train"]

    def test_dual_camera_screen_exclusion_propagates_from_the_fused_clock(self):
        offsets = {"front": 0.0, "back": 0.0}
        replay = _replay(
            {
                "fused": (offsets, _secs(2, 12)),
                "front": FRONT_BLOCKED,
                "back": (BACK_OFFSETS, _secs(2, 12)),
            },
            mode="dual_camera",
        )
        truth = _truth(boundaries={T0: 2.0, T1: 5.0, T4: 10.0})
        ev = evaluate_event_replay(
            replay,
            truth,
            premature_opening_window=M4_WINDOW,
            lead_in_min_block_latency_s=LATENCY,
            lead_in_latency_source=SOURCE,
        )
        assert ev.missed_train_screen == SCREEN_INSUFFICIENT_LEAD_IN and ev.missed_train is None

    def test_the_official_runner_does_not_use_the_screen(self):
        text = (REPO / "src/railway_detection/evaluation/evaluation_runner.py").read_text("utf-8")
        assert "lead_in" not in text and "screen_missed_train_lead_in" not in text


# ---------------------------------------------------------------------------
# DEC-C03 / DEC-A01  literal design M3, physical screen, provenance
# ---------------------------------------------------------------------------


def _screen(entry, first_visible, censored, latency=LATENCY):
    return screen_missed_train_lead_in(
        entry,
        first_visible_time_s=first_visible,
        first_visible_left_censored=censored,
        min_block_latency_s=latency,
        min_block_latency_source=SOURCE,
    )


class TestLeadInScreenAndLiteralM3:
    @pytest.mark.parametrize(
        ("entry", "t0", "censored", "outcome", "evaluable", "literal"),
        [
            (6.0, 1.0, False, SCREEN_PASSED, True, True),  # cell 1: agree
            (2.5, 1.0, False, SCREEN_INSUFFICIENT_LEAD_IN, False, True),  # cell 2: DIFFER
            (4.0, None, True, SCREEN_PASSED, True, True),  # cell 3: agree
            (2.0, None, True, SCREEN_INSUFFICIENT_LEAD_IN, False, False),  # cell 4: agree
            (4.0, None, False, SCREEN_UNVERIFIABLE, False, True),  # cell 5: DIFFER
            (2.0, None, False, SCREEN_UNVERIFIABLE, False, False),
            (None, 1.0, False, SCREEN_T1_MISSING, False, False),
        ],
    )
    def test_physical_screen_is_primary_and_literal_m3_is_reported_beside_it(
        self, entry, t0, censored, outcome, evaluable, literal
    ):
        result = _screen(entry, t0, censored)
        assert result.outcome == outcome and result.evaluable is evaluable
        assert result.m3_design_literal_evaluable is literal

    def test_insufficient_lead_in_and_unverifiable_stay_distinct(self):
        assert _screen(2.5, 1.0, False).outcome != _screen(4.0, None, False).outcome

    def test_insufficient_lead_in_with_observable_t0_is_not_a_software_failure(self):
        ev = EventMetricsCalculator.evaluate_run(
            _run(_secs(None, 12)),
            entry_time_s=3.0,
            clearance_time_s=9.0,
            lead_in_min_block_latency_s=LATENCY,
            lead_in_latency_source=SOURCE,
            first_visible_time_s=1.0,
        )
        assert ev.missed_train is None  # the barrier never closed, yet this is not a miss
        assert ev.missed_train_screen == SCREEN_INSUFFICIENT_LEAD_IN

    def test_screen_stays_off_by_default_in_evaluate_run(self):
        ev = EventMetricsCalculator.evaluate_run(
            _run(_secs(None, 12)), entry_time_s=3.0, clearance_time_s=9.0
        )
        assert ev.missed_train is True and ev.missed_train_screen == SCREEN_NOT_APPLIED

    def test_derivation_requires_no_threshold_claim_in_its_provenance(self):
        cfg = load_frozen_config(REPO / "configs" / "frozen_experiment_v1.yaml")
        latency, source = derive_min_block_latency_with_provenance(cfg)
        assert cfg.timing.tick_s == 0.2
        assert latency == pytest.approx(3.6)
        assert source.startswith("synthetic_replay_of_frozen_configuration:")
        assert f"tick_s={cfg.timing.tick_s}" in source
        assert f"config_canonical_sha256={cfg.config_hash}" in source
        assert "threshold" not in source and "approved" not in source

    def test_the_config_is_passed_explicitly_into_the_engine(self, monkeypatch):
        import railway_detection.simulation.runner as runner_module

        cfg = load_frozen_config(REPO / "configs" / "frozen_experiment_v1.yaml")
        seen = []

        class Spy(runner_module.EventSimulationRunner):
            def __init__(self, *args, **kwargs):
                seen.append(kwargs.get("config"))
                super().__init__(*args, **kwargs)

        monkeypatch.setattr(runner_module, "EventSimulationRunner", Spy)
        derive_min_block_latency_with_provenance(cfg)
        assert len(seen) == 1 and seen[0] is cfg

    def test_config_derivation_agrees_with_the_unconfigured_value_at_the_frozen_tick(self):
        cfg = load_frozen_config(REPO / "configs" / "frozen_experiment_v1.yaml")
        assert derive_min_block_latency_s(config=cfg) == derive_min_block_latency_s(tick_s=0.2)

    def test_config_and_runner_or_a_contradicting_tick_are_refused(self):
        from railway_detection.simulation.runner import EventSimulationRunner

        cfg = load_frozen_config(REPO / "configs" / "frozen_experiment_v1.yaml")
        with pytest.raises(ValueError, match="either config or runner"):
            derive_min_block_latency_s(config=cfg, runner=EventSimulationRunner())
        with pytest.raises(ValueError, match="contradicts"):
            derive_min_block_latency_s(config=cfg, tick_s=0.5)
        assert derive_min_block_latency_s(config=cfg, tick_s=0.2) == derive_min_block_latency_s(
            config=cfg
        )


# ---------------------------------------------------------------------------
# 15-18  Record consistency, cohort identity, aggregation (F-08, F-09, F-10)
# ---------------------------------------------------------------------------


def _evaluate_run(steps, event, **kwargs):
    kwargs.setdefault("premature_opening_window", M4_WINDOW)
    return EventMetricsCalculator.evaluate_run(_run(steps, event), **kwargs)


class TestUnevaluableRecordConsistency:
    def test_an_excluded_train_event_carries_no_m4_verdict(self):
        ev = _evaluate_run(
            _secs(2, 12), TRAIN, entry_time_s=1.0, clearance_time_s=5.0, evaluable=False
        )
        assert ev.evaluable is False and ev.notes == "excluded_train_event"
        assert ev.m4_status is None and ev.m4_reason is None and ev.m4_replay_complete is None
        assert ev.premature_opening is None and ev.never_protected is None

    def test_the_same_event_evaluable_still_carries_its_verdict(self):
        ev = _evaluate_run(_secs(2, 12), TRAIN, entry_time_s=1.0, clearance_time_s=5.0)
        assert ev.m4_status == M4_STATUS_EVALUABLE and ev.premature_opening is False

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"cohort": "engine_events"},
            {"has_train_ground_truth": None},
            {"ground_truth_status": "uncertain"},
            {"cohort": "no_train_events", "has_train_ground_truth": False},
        ],
    )
    def test_other_unevaluable_records_never_claim_an_m4_status(self, kwargs):
        event = "event_001" if "cohort" in kwargs else TRAIN
        ev = _evaluate_run(_secs(2, 12), event, clearance_time_s=5.0, **kwargs)
        assert ev.m4_status is None and ev.m4_reason is None and ev.m4_replay_complete is None
        assert ev.premature_opening is None and ev.never_protected is None

    def test_no_evaluable_record_has_a_status_contradicting_its_flags(self):
        for steps in (_secs(None, 12), _secs(2, 12), _secs(2, 12, unblocked_at=(3,)), _secs(2, 3)):
            ev = _evaluate_run(steps, TRAIN, entry_time_s=1.0, clearance_time_s=5.0)
            if ev.m4_status == M4_STATUS_EVALUABLE:
                assert ev.premature_opening is not None and ev.never_protected is False
            else:
                assert ev.premature_opening is None


class TestCohortIdentityAndAggregation:
    def _mixed(self):
        evs = {
            "a_m5": _evaluate_run(
                _secs(None, 12), "train_events/a", entry_time_s=1.0, clearance_time_s=5.0
            ),
            "b_viol": _evaluate_run(
                _secs(1, 12, unblocked_at=(3,)),
                "train_events/b",
                entry_time_s=1.0,
                clearance_time_s=5.0,
            ),
            "c_clean": _evaluate_run(
                _secs(1, 12), "train_events/c", entry_time_s=1.0, clearance_time_s=5.0
            ),
            "d_excl": _evaluate_run(
                _secs(1, 12),
                "train_events/d",
                entry_time_s=1.0,
                clearance_time_s=5.0,
                evaluable=False,
            ),
            "e_notrain": _evaluate_run(
                _secs(1, 12), "no_train_events/e", has_train_ground_truth=False
            ),
            "h_notrain_excl": _evaluate_run(
                _secs(None, 12),
                "no_train_events/h",
                has_train_ground_truth=False,
                evaluable=False,
            ),
            "f_engine": _evaluate_run(
                _secs(1, 12), "engine_events/f", has_train_ground_truth=False
            ),
            "g_unverified": _evaluate_run(
                _secs(1, 12), "train_events/g", has_train_ground_truth=None
            ),
        }
        return evs

    def test_every_record_carries_its_cohort(self):
        evs = self._mixed()
        assert {k: v.cohort for k, v in evs.items()} == {
            "a_m5": "train_events",
            "b_viol": "train_events",
            "c_clean": "train_events",
            "d_excl": "train_events",
            "e_notrain": "no_train_events",
            "h_notrain_excl": "no_train_events",
            "f_engine": "engine_events",
            "g_unverified": "train_events",
        }
        bare = _evaluate_run(_secs(1, 12), "event_001", cohort="train_events", clearance_time_s=5.0)
        assert bare.cohort == "train_events" and bare.event_id == "event_001"
        unresolved = _evaluate_run(_secs(1, 12), "event_002", has_train_ground_truth=None)
        assert unresolved.cohort is None and unresolved.notes == "ground_truth_missing"

    def test_partition_identity_holds_and_new_counts_are_exposed(self):
        summary = EventMetricsCalculator.aggregate_cohort(list(self._mixed().values()))
        assert summary.total_events == 8
        assert summary.eligible_events == 3
        assert summary.no_train_events == 2
        assert summary.engine_events == 1
        assert summary.unverified_ground_truth_count == 1
        assert summary.excluded_train_events_count == 1
        assert summary.total_events == (
            summary.eligible_events
            + summary.no_train_events
            + summary.engine_events
            + summary.unverified_ground_truth_count
            + summary.excluded_train_events_count
        )
        exported = summary.to_dict()
        assert exported["unverified_ground_truth_count"] == 1
        assert exported["excluded_train_events_count"] == 1

    def test_partition_identity_holds_for_a_single_bucket_cohort(self):
        for key, ev in self._mixed().items():
            s = EventMetricsCalculator.aggregate_cohort([ev])
            assert s.total_events == 1 and s.total_events == (
                s.eligible_events
                + s.no_train_events
                + s.engine_events
                + s.unverified_ground_truth_count
                + s.excluded_train_events_count
            ), key

    def test_new_counts_do_not_change_any_metric_denominator(self):
        evs = self._mixed()
        everything = EventMetricsCalculator.aggregate_cohort(list(evs.values())).to_dict()
        eligible_only = EventMetricsCalculator.aggregate_cohort(
            [evs["a_m5"], evs["b_viol"], evs["c_clean"], evs["e_notrain"]]
        ).to_dict()
        for key in (
            "eligible_events",
            "missed_train_evaluable_count",
            "missed_train_count",
            "premature_opening_evaluable_count",
            "premature_opening_count",
            "never_protected_evaluable_count",
            "never_protected_count",
            "m4_no_violation_count",
            "m4_not_evaluable_count",
            "false_alarm_evaluable_count",
            "false_alarm_count",
        ):
            assert everything[key] == eligible_only[key], key
        assert everything["premature_opening_evaluable_count"] == 2
        assert everything["never_protected_count"] == 1
        assert everything["m4_no_violation_count"] == 1

    def test_engine_events_never_enter_pooled_train_metrics(self):
        train = _evaluate_run(
            _secs(1, 12), "train_events/t", entry_time_s=1.0, clearance_time_s=5.0
        )
        engine = _evaluate_run(
            _secs(None, 12),
            "engine_events/x",
            entry_time_s=1.0,
            clearance_time_s=5.0,
            has_train_ground_truth=False,
        )
        assert engine.evaluable is False and engine.notes == "engine_event_excluded"
        alone = EventMetricsCalculator.aggregate_cohort([train]).to_dict()
        pooled = EventMetricsCalculator.aggregate_cohort([train, engine]).to_dict()
        for key in alone:
            if key in ("total_events", "engine_events"):
                continue
            assert alone[key] == pooled[key], key
        assert pooled["engine_events"] == 1 and pooled["eligible_events"] == 1
        assert pooled["false_alarm_evaluable_count"] == 0

    def test_a_cohort_field_that_contradicts_a_qualified_id_is_refused(self):
        ev = _evaluate_run(_secs(1, 12), "train_events/x", clearance_time_s=5.0)
        ev.cohort = "no_train_events"
        with pytest.raises(ValueError, match="contradicts its cohort"):
            EventMetricsCalculator.aggregate_cohort([ev])

    def test_duplicate_bare_ids_stay_rejected_even_across_cohorts(self):
        a = _evaluate_run(_secs(1, 12), "event_001", cohort="train_events", clearance_time_s=5.0)
        b = _evaluate_run(
            _secs(1, 12), "event_001", cohort="no_train_events", has_train_ground_truth=False
        )
        with pytest.raises(ValueError, match="unique event IDs"):
            EventMetricsCalculator.aggregate_cohort([a, b])

    def test_qualified_ids_with_the_same_event_number_aggregate_cleanly(self):
        a = _evaluate_run(_secs(1, 12), "train_events/event_001", clearance_time_s=5.0)
        b = _evaluate_run(_secs(1, 12), "no_train_events/event_001", has_train_ground_truth=False)
        s = EventMetricsCalculator.aggregate_cohort([a, b])
        assert (s.eligible_events, s.no_train_events) == (1, 1)

    def test_summary_class_is_the_production_dataclass(self):
        assert isinstance(
            EventMetricsCalculator.aggregate_cohort([]).single_events, list
        ) and SingleEventEvaluation is type(self._mixed()["a_m5"])


class TestMission5A1FailClosedBehaviourIsPreserved:
    def test_bare_id_without_cohort_raises_when_evaluable(self):
        with pytest.raises(UnqualifiedEventIdError):
            _evaluate_run(_secs(1, 12), "event_001", clearance_time_s=5.0)

    @pytest.mark.parametrize(
        ("event", "kwargs"),
        [
            ("train_events/x", {"has_train_ground_truth": False}),
            ("no_train_events/x", {"has_train_ground_truth": True}),
            ("train_events/x", {"ground_truth_status": "engine"}),
            ("engine_events/x", {"cohort": "train_events"}),
        ],
    )
    def test_cohort_versus_routing_contradictions_raise(self, event, kwargs):
        with pytest.raises(UnqualifiedEventIdError):
            _evaluate_run(_secs(1, 12), event, clearance_time_s=5.0, **kwargs)

    def test_unannotated_bare_id_is_a_ground_truth_record_not_an_abort(self):
        ev = _evaluate_run(_secs(1, 12), "event_001", has_train_ground_truth=None)
        assert ev.evaluable is False and ev.notes == "ground_truth_missing"
        s = EventMetricsCalculator.aggregate_cohort([ev])
        assert s.unverified_ground_truth_count == 1 and s.eligible_events == 0


# ---------------------------------------------------------------------------
# WP 1.6  Preservation-manifest directory pruning (DEC-A02)
# ---------------------------------------------------------------------------


def _manifest_tool():
    spec = importlib.util.spec_from_file_location(
        "phase1_manifest_tool", REPO / "scripts" / "mission5a_build_preservation_manifest.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    # Constructed unversioned temp-root fixture: all Git queries report no repository.
    # Git metadata is irrelevant to the path/hash/overwrite contracts under test.
    module._git = lambda root, *args: ""
    return module


class TestManifestNoMediaEnumeration:
    def _tree(self, tmp_path):
        root = tmp_path / "repo"
        (root / "src").mkdir(parents=True)
        (root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        for tree in ("data/raw/nested", "results", "research/figures"):
            (root / tree).mkdir(parents=True)
            (root / tree / "sentinel.txt").write_text("s\n", encoding="utf-8")
        (root / "research" / "code.py").write_text("y = 2\n", encoding="utf-8")
        return root

    @pytest.fixture
    def listed(self, monkeypatch):
        """Record every directory the process lists through os.scandir / os.listdir."""
        seen: list[str] = []
        real_scandir, real_listdir = os.scandir, os.listdir

        def scandir(path="."):
            seen.append(os.fspath(path))
            return real_scandir(path)

        def listdir(path="."):
            seen.append(os.fspath(path))
            return real_listdir(path)

        monkeypatch.setattr(os, "scandir", scandir)
        monkeypatch.setattr(os, "listdir", listdir)
        return seen

    @staticmethod
    def _under(seen, root, tree):
        base = str(root / tree)
        return [p for p in seen if p == base or p.startswith(base + os.sep)]

    def test_default_build_never_lists_output_trees(self, tmp_path, listed):
        root = self._tree(tmp_path)
        listed.clear()
        manifest = _manifest_tool().build_manifest(root)
        for tree in ("data/raw", "results", "research/figures"):
            assert self._under(listed, root, tree) == [], tree
        assert self._under(listed, root, "src"), "governing trees are still walked"
        assert manifest["count_excluded_trees"] is False
        assert manifest["pruned_output_trees"] == ["data/raw", "research/figures", "results"]
        assert "generated_output_tree" not in manifest["excluded"]
        assert {e["path"] for e in manifest["entries"]} == {"src/a.py", "research/code.py"}

    def test_counting_is_opt_in_and_only_counts(self, tmp_path, listed):
        root = self._tree(tmp_path)
        listed.clear()
        manifest = _manifest_tool().build_manifest(root, count_excluded_trees=True)
        assert self._under(listed, root, "data/raw")
        assert manifest["excluded"]["generated_output_tree"]["file_count"] == 3
        assert manifest["pruned_output_trees"] == []
        assert {e["path"] for e in manifest["entries"]} == {"src/a.py", "research/code.py"}

    def test_pruning_does_not_change_the_governing_entries(self, tmp_path):
        root = self._tree(tmp_path)
        tool = _manifest_tool()
        default = tool.build_manifest(root)
        counted = tool.build_manifest(root, count_excluded_trees=True)
        assert default["entries"] == counted["entries"]

    def test_cli_flag_and_verify_round_trip(self, tmp_path, capsys):
        root = self._tree(tmp_path)
        tool = _manifest_tool()
        out = tmp_path / "m.json"
        assert tool.main(["build", "--root", str(root), "--out", str(out)]) == 0
        assert tool.main(["verify", "--root", str(root), "--manifest", str(out)]) == 0
        counted = tmp_path / "counted.json"
        assert (
            tool.main(
                ["build", "--root", str(root), "--out", str(counted), "--count-excluded-trees"]
            )
            == 0
        )
        capsys.readouterr()
        import json

        assert json.loads(counted.read_text("utf-8"))["count_excluded_trees"] is True
        assert json.loads(out.read_text("utf-8"))["count_excluded_trees"] is False
