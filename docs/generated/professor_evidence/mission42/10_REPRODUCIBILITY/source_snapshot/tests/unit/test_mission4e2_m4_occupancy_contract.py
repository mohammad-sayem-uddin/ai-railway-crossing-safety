"""Mission 4E.2 synthetic-only checks for the M4 / M5 / occupancy-duration contracts.

Scope and safety
----------------
* Every timestamp, step and event below is hand-written and synthetic. No media, ground-truth
  file, cache, checkpoint, config or manifest is opened; nothing is inferred or trained.
* Part 1 exercises the production ``m4_premature_opening`` / ``evaluate_run`` /
  ``aggregate_cohort`` code (expectations updated by Mission 5A for the corrected
  classification). Expected values were worked out on paper from the stated inputs.
* Part 2 contains a TEST-LOCAL reference implementation of the PROPOSED, UNAPPROVED
  occupancy-duration contract (docs/generated/OCCUPANCY_DURATION_METRIC_CONTRACT_20261101_M4E2.md).
  It is deliberately not placed under ``src/``: the contract is not approved and no schema
  field for physical crossing-blocked onset has been added or validated. Passing these tests
  therefore validates the *written rules*, not any real-data occupancy metric.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

import pytest

from railway_detection.evaluation.metrics import (
    M4_WINDOW,
    V9_WINDOW,
    EventMetricsCalculator,
    SingleEventEvaluation,
    m4_premature_opening,
)
from railway_detection.simulation.runner import SimulationRunResult, SimulationStep

# ---------------------------------------------------------------------------
# Synthetic builders
# ---------------------------------------------------------------------------


def _step(t, blocked=True, gate="CLOSED"):
    return SimulationStep(t, "TRAIN_PRESENT", gate, 0.0 if blocked else 90.0, blocked, None)  # type: ignore[arg-type]


def _run(steps, event="train_events/event_001", closed_s=0.0, total_s=None):
    return SimulationRunResult(
        event_id=event,
        scenario_name="synthetic",
        steps=steps,
        total_duration_s=total_s
        if total_s is not None
        else (steps[-1].timestamp_s if steps else 0.0),
        closed_duration_s=closed_s,
    )


def _timeline(blocked_flags, start=0.0, dt=1.0, gates=None):
    return [
        _step(start + i * dt, b, (gates[i] if gates else ("CLOSED" if b else "OPEN")))
        for i, b in enumerate(blocked_flags)
    ]


# ---------------------------------------------------------------------------
# Part 1 - M4 (premature gate opening) and M5 (never protected), existing code
# ---------------------------------------------------------------------------


class TestM4StrictInterval:
    def test_continuous_protection_is_not_premature(self):
        # blocked at t=2..9, T4=8.5 -> interval (2, 8.5) = steps 3..8, all blocked
        steps = _timeline([False, False] + [True] * 8)  # t=0,1 open; t=2..9 blocked
        assert m4_premature_opening(_run(steps), 8.5) == (False, False)

    def test_unblocked_step_strictly_inside_interval_is_premature(self):
        steps = _timeline([True, True, False, True, True, True])  # t=2 unblocked
        assert m4_premature_opening(_run(steps), 5.5) == (True, False)

    @pytest.mark.parametrize("state", ["OPENING", "OPEN"])
    def test_opening_or_open_state_inside_interval_is_premature_even_if_still_blocked(self, state):
        gates = ["CLOSED", "CLOSED", state, "CLOSED", "CLOSED"]
        steps = _timeline([True] * 5, gates=gates)  # blocked flag stays True throughout
        assert m4_premature_opening(_run(steps), 4.5) == (True, False)

    def test_start_boundary_step_itself_is_excluded(self):
        # The first blocked step is the start. A non-blocked *state label* on it must not count:
        # (t_blocked, T4) is open at the start. Gate label OPENING on the start step is ignored.
        steps = _timeline([True, True, True], gates=["OPENING", "CLOSED", "CLOSED"])
        # Mission 5A: T4 must be reached by the replay (last step t=2.0), else NOT_EVALUABLE.
        assert m4_premature_opening(_run(steps), 2.0) == (False, False)

    def test_step_exactly_at_t4_is_excluded(self):
        steps = _timeline([True, True, True, False])  # unblocked only at t=3
        assert m4_premature_opening(_run(steps), 3.0) == (False, False)  # t=3 == T4 -> outside
        assert m4_premature_opening(_run(steps), 3.01) == (True, False)  # just inside

    def test_unblocked_steps_before_start_are_ignored(self):
        steps = _timeline([False, False, True, True, True])
        assert m4_premature_opening(_run(steps), 4.0) == (False, False)

    def test_reopen_then_reclose_inside_interval_is_premature(self):
        steps = _timeline([True, False, True, True, True])
        assert m4_premature_opening(_run(steps), 4.5) == (True, False)

    def test_empty_interval_is_not_evaluable_not_vacuously_safe(self):
        # blocked at t=0, next retained step is T4 itself -> no step strictly inside.
        # Mission 5A: no evidence of continuous protection => NOT_EVALUABLE, never "not premature".
        steps = [_step(0.0, True), _step(5.0, False)]
        assert m4_premature_opening(_run(steps), 5.0) == (None, None)


class TestM5NeverProtected:
    def test_never_blocked_is_m5_and_m4_none(self):
        steps = _timeline([False] * 6)
        assert m4_premature_opening(_run(steps), 5.0) == (None, True)

    def test_first_blocked_at_or_after_t4_is_m5(self):
        steps = _timeline([False, False, False, True, True])  # first blocked t=3
        assert m4_premature_opening(_run(steps), 3.0) == (None, True)  # t_blocked == T4
        assert m4_premature_opening(_run(steps), 2.0) == (None, True)  # t_blocked after T4

    def test_empty_replay_is_not_m5(self):
        # Mission 5A: an empty replay observed nothing; it must not assert never-protected.
        assert m4_premature_opening(_run([]), 3.0) == (None, None)


class TestM4EvaluateRunGuards:
    def test_undecided_window_never_computed(self):
        ev = EventMetricsCalculator.evaluate_run(
            _run(_timeline([True, False, True])),
            clearance_time_s=2.5,
            premature_opening_window=None,
        )
        assert ev.premature_opening is None and ev.never_protected is None
        assert ev.metric_exclusions["premature_opening"] == "premature_opening_window_undecided"

    def test_missing_t4_means_not_evaluable_and_no_m5_claim(self):
        ev = EventMetricsCalculator.evaluate_run(
            _run(_timeline([True, False, True])),
            clearance_time_s=None,
            premature_opening_window=M4_WINDOW,
        )
        assert ev.premature_opening is None
        assert ev.never_protected is None  # M5 cannot be asserted without an end boundary

    def test_unimplemented_window_name_rejected(self):
        with pytest.raises(ValueError, match="not implemented"):
            EventMetricsCalculator.evaluate_run(
                _run(_timeline([True])),
                clearance_time_s=1.0,
                premature_opening_window="occupancy_duration",
            )

    @pytest.mark.parametrize("bad_t4", [math.nan, math.inf, -1.0])
    def test_invalid_t4_rejected(self, bad_t4):
        with pytest.raises(ValueError, match="finite and nonnegative"):
            EventMetricsCalculator.evaluate_run(
                _run(_timeline([True, True])),
                clearance_time_s=bad_t4,
                premature_opening_window=M4_WINDOW,
            )

    def test_non_increasing_replay_timestamps_rejected(self):
        steps = [_step(0.0), _step(2.0), _step(2.0)]
        with pytest.raises(ValueError, match="strictly increasing"):
            EventMetricsCalculator.evaluate_run(
                _run(steps), clearance_time_s=3.0, premature_opening_window=M4_WINDOW
            )

    def test_nan_replay_timestamp_rejected(self):
        steps = [_step(0.0), _step(math.nan)]
        with pytest.raises(ValueError):
            EventMetricsCalculator.evaluate_run(
                _run(steps), clearance_time_s=3.0, premature_opening_window=M4_WINDOW
            )

    def test_engine_event_excluded_from_m4(self):
        ev = EventMetricsCalculator.evaluate_run(
            _run(_timeline([True, False, True]), event="engine_events/event_001"),
            clearance_time_s=2.5,
            premature_opening_window=M4_WINDOW,
            cohort="engine_events",
        )
        assert ev.evaluable is False and ev.premature_opening is None and ev.never_protected is None

    @pytest.mark.parametrize("status", ["censored", "uncertain", "missing", "unobservable"])
    def test_unverified_ground_truth_is_not_evaluable(self, status):
        ev = EventMetricsCalculator.evaluate_run(
            _run(_timeline([True, False, True])),
            clearance_time_s=None,
            premature_opening_window=M4_WINDOW,
            ground_truth_status=status,
        )
        assert ev.evaluable is False and ev.premature_opening is None


class TestM4M5DenominatorSeparation:
    """Six synthetic train events + one engine + one no-train, all cohort-qualified."""

    def _cohort(self):
        w = M4_WINDOW
        e = EventMetricsCalculator.evaluate_run
        evs = [
            # A: protected throughout          -> M4 evaluable, not premature
            e(
                _run(_timeline([True] * 6), "train_events/event_001"),
                clearance_time_s=4.5,
                premature_opening_window=w,
            ),
            # B: opens inside interval         -> M4 evaluable, premature
            e(
                _run(_timeline([True, True, False, True, True, True]), "train_events/event_002"),
                clearance_time_s=4.5,
                premature_opening_window=w,
            ),
            # C: never blocked before T4       -> M5, excluded from M4 denominator
            e(
                _run(_timeline([False] * 6), "train_events/event_003"),
                clearance_time_s=4.5,
                premature_opening_window=w,
            ),
            # D: T4 missing/censored           -> neither M4 nor M5 evaluable
            e(
                _run(_timeline([True] * 6), "train_events/event_004"),
                clearance_time_s=None,
                premature_opening_window=w,
                exclusion_reasons={"T4_tail_clearance": "censored"},
            ),
            # E: blocked only at/after T4      -> M5
            e(
                _run(_timeline([False, False, False, True, True]), "train_events/event_005"),
                clearance_time_s=3.0,
                premature_opening_window=w,
            ),
            # F: another premature
            e(
                _run(_timeline([True, False, False, False, True]), "train_events/event_006"),
                clearance_time_s=4.5,
                premature_opening_window=w,
            ),
            # engine + no-train: never in the M4/M5 train denominator
            e(
                _run(_timeline([True, False, True]), "engine_events/event_001"),
                clearance_time_s=2.5,
                premature_opening_window=w,
                cohort="engine_events",
            ),
            e(
                _run(_timeline([False, False]), "no_train_events/event_001"),
                has_train_ground_truth=False,
                premature_opening_window=w,
            ),
        ]
        return EventMetricsCalculator.aggregate_cohort(evs)

    def test_m4_denominator_excludes_m5_missing_t4_engine_and_no_train(self):
        s = self._cohort()
        assert s.eligible_events == 6
        assert s.premature_opening_evaluable_count == 3  # A, B, F
        assert s.premature_opening_count == 2  # B, F
        assert s.premature_opening_rate == pytest.approx(2 / 3)
        assert s.premature_opening_definition == M4_WINDOW

    def test_m5_is_reported_separately(self):
        s = self._cohort()
        # M5 is defined for events with a usable T4: A, B, C, E, F  (D has no T4)
        assert s.never_protected_evaluable_count == 5
        assert s.never_protected_count == 2  # C, E
        assert (
            s.never_protected_count + s.premature_opening_evaluable_count == 5
        )  # partition of M5-evaluable

    def test_engine_and_no_train_counted_in_their_own_buckets(self):
        s = self._cohort()
        assert s.engine_events == 1
        assert s.no_train_events == 1

    def test_unevaluable_reasons_are_listed_not_dropped(self):
        s = self._cohort()
        reasons = {x["event_id"]: x["reason"] for x in s.exclusions["premature_opening"]}
        assert set(reasons) == {
            "train_events/event_003",
            "train_events/event_004",
            "train_events/event_005",
        }
        assert "never_protected_before_T4" in reasons["train_events/event_003"]
        assert "never_protected_before_T4" in reasons["train_events/event_005"]
        assert "T4_tail_clearance" in reasons["train_events/event_004"]

    def test_mixed_windows_rejected(self):
        a = EventMetricsCalculator.evaluate_run(
            _run(_timeline([True] * 4), "train_events/event_001"),
            clearance_time_s=3.5,
            premature_opening_window=M4_WINDOW,
        )
        b = EventMetricsCalculator.evaluate_run(
            _run(_timeline([True] * 4), "train_events/event_002"),
            entry_time_s=0.5,
            clearance_time_s=3.5,
            premature_opening_window=V9_WINDOW,
        )
        with pytest.raises(ValueError, match="mixes premature-opening windows"):
            EventMetricsCalculator.aggregate_cohort([a, b])

    def test_duplicate_bare_ids_rejected(self):
        a = SingleEventEvaluation(event_id="event_001", scenario_name="s")
        with pytest.raises(ValueError, match="unique"):
            EventMetricsCalculator.aggregate_cohort([a, a])


class TestFormerGapNowCorrected:
    """G-M4-02 (replay ending before T4) was corrected in production by Mission 5A (RD-016)."""

    def test_replay_ending_before_t4_is_no_longer_treated_as_protected(self):
        steps = _timeline([True] * 5)  # blocked t=0..4; T4=20 never reached
        assert m4_premature_opening(_run(steps), 20.0) == (None, None)


# ---------------------------------------------------------------------------
# Part 2 - PROPOSED occupancy-duration contract: test-local reference implementation
# ---------------------------------------------------------------------------

HUMAN = "human_boundary"
OCC_EVALUABLE = "EVALUABLE"
OCC_NOT = "NOT_EVALUABLE"


@dataclass(frozen=True)
class SynthBoundary:
    """PROPOSED input shape. Mirrors the supported BoundaryAdjudication states plus the
    proposed (NOT yet supported) ``source`` and ``censoring_direction`` attributes."""

    state: str  # OBSERVABLE | UNOBSERVABLE_NOT_APPLICABLE | CENSORED | UNCERTAIN
    value_s: float | None = None
    camera: str | None = None  # "front" | "back"
    source: str = HUMAN  # PROPOSED: HUMAN | "replay_first_blocked" | ...
    censoring_direction: str | None = None  # PROPOSED: LEFT | RIGHT


@dataclass(frozen=True)
class OccResult:
    status: str
    reason: str | None
    duration_s: float | None = None
    error_bound_s: float | None = None
    cross_camera: bool = False


def _bad(x):
    return x is None or not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0.0


def occupancy_duration(
    cohort,
    onset,
    t4,
    *,
    offset_s=None,  # back-minus-front, seconds (v7 section 5 convention: dt = t_back - t_front)
    alignment=None,  # aligned | partially_aligned | unaligned | None
    offset_uncertainty_s=None,
) -> OccResult:
    """D_occupancy = T4 - T_physical_block_onset (seconds). Fail-closed; never imputes."""
    if cohort == "engine_events":
        return OccResult(OCC_NOT, "engine_event_excluded")
    if cohort == "no_train_events":
        return OccResult(OCC_NOT, "no_train_event")
    if cohort != "train_events":
        return OccResult(OCC_NOT, "cohort_unknown")

    # --- onset ---
    if onset is None:
        return OccResult(OCC_NOT, "physical_onset_missing")
    if onset.source != HUMAN:
        return OccResult(
            OCC_NOT, "onset_not_independently_established"
        )  # e.g. replay first_blocked
    if onset.state == "CENSORED":
        return OccResult(
            OCC_NOT,
            "onset_left_censored" if onset.censoring_direction == "LEFT" else "onset_censored",
        )
    if onset.state == "UNCERTAIN":
        return OccResult(OCC_NOT, "onset_uncertain")
    if onset.state != "OBSERVABLE":
        return OccResult(OCC_NOT, "onset_unobservable_or_not_applicable")
    # --- T4 ---
    if t4 is None:
        return OccResult(OCC_NOT, "t4_missing")
    if t4.state == "CENSORED":
        return OccResult(
            OCC_NOT, "t4_right_censored" if t4.censoring_direction == "RIGHT" else "t4_censored"
        )
    if t4.state == "UNCERTAIN":
        return OccResult(OCC_NOT, "t4_uncertain")
    if t4.state != "OBSERVABLE":
        return OccResult(OCC_NOT, "t4_unobservable_or_not_applicable")
    # --- values ---
    if _bad(onset.value_s) or _bad(t4.value_s):
        return OccResult(OCC_NOT, "invalid_timestamp")
    if onset.camera not in ("front", "back") or t4.camera not in ("front", "back"):
        return OccResult(OCC_NOT, "reference_camera_missing")

    cross = onset.camera != t4.camera
    onset_in_t4_clock = onset.value_s
    bound = None
    if cross:
        if (
            alignment not in ("aligned", "partially_aligned")
            or _bad(offset_uncertainty_s)
            or offset_s is None
        ):
            return OccResult(OCC_NOT, "clock_mismatch_r04_unresolved", cross_camera=True)
        if not math.isfinite(offset_s):
            return OccResult(OCC_NOT, "invalid_timestamp", cross_camera=True)
        if onset.camera == "front" and t4.camera == "back":
            onset_in_t4_clock = onset.value_s + offset_s
        else:  # onset on back, T4 on front
            onset_in_t4_clock = onset.value_s - offset_s
        if alignment == "partially_aligned":
            bound = offset_uncertainty_s
    d = t4.value_s - onset_in_t4_clock
    if d <= 0.0:
        return OccResult(OCC_NOT, "nonpositive_duration", cross_camera=cross)
    return OccResult(OCC_EVALUABLE, None, duration_s=d, error_bound_s=bound, cross_camera=cross)


def summarize_occupancy(results):
    ok = [r.duration_s for r in results if r.status == OCC_EVALUABLE]
    reasons: dict[str, int] = {}
    for r in results:
        if r.status == OCC_NOT:
            reasons[r.reason] = reasons.get(r.reason, 0) + 1
    return {
        "evaluable_n": len(ok),
        "not_evaluable_n": len(results) - len(ok),
        "not_evaluable_reasons": reasons,
        "mean_s": statistics.fmean(ok) if ok else None,
        "median_s": statistics.median(ok) if ok else None,
        "min_s": min(ok) if ok else None,
        "max_s": max(ok) if ok else None,
        "unit": "seconds",
    }


def _obs(v, cam="back", **kw):
    return SynthBoundary("OBSERVABLE", v, cam, **kw)


class TestOccupancyDefinition:
    def test_same_camera_difference_in_seconds(self):
        r = occupancy_duration("train_events", _obs(12.5, "back"), _obs(47.25, "back"))
        assert r.status == OCC_EVALUABLE and r.duration_s == pytest.approx(34.75)
        assert r.cross_camera is False and r.error_bound_s is None

    def test_replay_first_blocked_is_never_a_valid_onset(self):
        r = occupancy_duration(
            "train_events", _obs(10.0, "back", source="replay_first_blocked"), _obs(40.0, "back")
        )
        assert (r.status, r.reason) == (OCC_NOT, "onset_not_independently_established")

    def test_does_not_equal_m4_window(self):
        # Same synthetic event: occupancy uses the human onset (t=2); M4 uses replay first
        # blocked (t=5).
        steps = _timeline([False] * 5 + [True] * 6)  # first blocked at t=5
        _, never = m4_premature_opening(_run(steps), 9.5)
        occ = occupancy_duration("train_events", _obs(2.0, "back"), _obs(9.5, "back"))
        assert never is False and occ.duration_s == pytest.approx(7.5)
        # M4 interval length (9.5-5=4.5) is NOT the occupancy duration (7.5): metrics stay separate.
        assert occ.duration_s != pytest.approx(9.5 - 5.0)


class TestOccupancyMissingnessAndCensoring:
    def test_missing_onset_boundary(self):
        assert (
            occupancy_duration("train_events", None, _obs(30.0)).reason == "physical_onset_missing"
        )

    def test_missing_t4_boundary(self):
        assert occupancy_duration("train_events", _obs(5.0), None).reason == "t4_missing"

    def test_left_censored_onset_not_evaluable_and_no_zero_imputation(self):
        onset = SynthBoundary("CENSORED", None, None, censoring_direction="LEFT")
        r = occupancy_duration("train_events", onset, _obs(30.0))
        assert (r.status, r.reason, r.duration_s) == (OCC_NOT, "onset_left_censored", None)

    def test_right_censored_t4_not_evaluable(self):
        t4 = SynthBoundary("CENSORED", None, None, censoring_direction="RIGHT")
        r = occupancy_duration("train_events", _obs(5.0), t4)
        assert (r.status, r.reason) == (OCC_NOT, "t4_right_censored")

    def test_uncertain_boundaries_not_evaluable(self):
        unc = SynthBoundary("UNCERTAIN", None, None)
        assert occupancy_duration("train_events", unc, _obs(30.0)).reason == "onset_uncertain"
        assert occupancy_duration("train_events", _obs(5.0), unc).reason == "t4_uncertain"

    def test_unobservable_not_applicable(self):
        na = SynthBoundary("UNOBSERVABLE_NOT_APPLICABLE", None, None)
        assert (
            occupancy_duration("train_events", na, _obs(30.0)).reason
            == "onset_unobservable_or_not_applicable"
        )
        assert (
            occupancy_duration("train_events", _obs(5.0), na).reason
            == "t4_unobservable_or_not_applicable"
        )

    @pytest.mark.parametrize("bad", [math.nan, math.inf, -0.5])
    def test_invalid_timestamps(self, bad):
        assert (
            occupancy_duration("train_events", _obs(bad), _obs(30.0)).reason == "invalid_timestamp"
        )
        assert (
            occupancy_duration("train_events", _obs(5.0), _obs(bad)).reason == "invalid_timestamp"
        )

    @pytest.mark.parametrize("onset,t4", [(30.0, 30.0), (31.0, 30.0)])
    def test_nonpositive_duration(self, onset, t4):
        assert (
            occupancy_duration("train_events", _obs(onset), _obs(t4)).reason
            == "nonpositive_duration"
        )

    def test_missing_reference_camera(self):
        assert occupancy_duration(
            "train_events", SynthBoundary("OBSERVABLE", 5.0, None), _obs(30.0)
        ).reason == ("reference_camera_missing")

    def test_engine_and_no_train_excluded(self):
        assert (
            occupancy_duration("engine_events", _obs(1.0), _obs(9.0)).reason
            == "engine_event_excluded"
        )
        assert occupancy_duration("no_train_events", None, None).reason == "no_train_event"


class TestOccupancyClocks:
    def test_cross_camera_without_r04_is_not_evaluable_and_no_zero_offset_assumed(self):
        r = occupancy_duration("train_events", _obs(5.0, "front"), _obs(30.0, "back"))
        assert (r.status, r.reason) == (OCC_NOT, "clock_mismatch_r04_unresolved")

    def test_unaligned_status_rejected(self):
        r = occupancy_duration(
            "train_events",
            _obs(5.0, "front"),
            _obs(30.0, "back"),
            offset_s=1.0,
            alignment="unaligned",
            offset_uncertainty_s=3.0,
        )
        assert r.reason == "clock_mismatch_r04_unresolved"

    def test_aligned_cross_camera_applies_offset_back_minus_front(self):
        # dt = t_back - t_front = +2.0 -> front 5.0 == back 7.0 ; D = 30 - 7 = 23
        r = occupancy_duration(
            "train_events",
            _obs(5.0, "front"),
            _obs(30.0, "back"),
            offset_s=2.0,
            alignment="aligned",
            offset_uncertainty_s=0.3,
        )
        assert r.status == OCC_EVALUABLE and r.duration_s == pytest.approx(23.0) and r.cross_camera
        assert r.error_bound_s is None  # aligned (delta <= 0.5 s): no extra bound required

    def test_partially_aligned_carries_error_bound(self):
        r = occupancy_duration(
            "train_events",
            _obs(5.0, "front"),
            _obs(30.0, "back"),
            offset_s=-1.0,
            alignment="partially_aligned",
            offset_uncertainty_s=1.5,
        )
        assert r.duration_s == pytest.approx(26.0) and r.error_bound_s == pytest.approx(1.5)

    def test_missing_offset_uncertainty_rejected(self):
        r = occupancy_duration(
            "train_events",
            _obs(5.0, "front"),
            _obs(30.0, "back"),
            offset_s=2.0,
            alignment="aligned",
        )
        assert r.reason == "clock_mismatch_r04_unresolved"

    def test_negative_duration_after_offset_rejected(self):
        r = occupancy_duration(
            "train_events",
            _obs(28.0, "front"),
            _obs(30.0, "back"),
            offset_s=5.0,
            alignment="aligned",
            offset_uncertainty_s=0.1,
        )
        assert r.reason == "nonpositive_duration"


class TestOccupancySummaryAndDenominatorSeparation:
    def test_summary_counts_reasons_and_seconds(self):
        rs = [
            occupancy_duration("train_events", _obs(10.0), _obs(40.0)),  # 30
            occupancy_duration("train_events", _obs(0.0), _obs(20.0)),  # 20
            occupancy_duration("train_events", _obs(5.0), _obs(60.0)),  # 55
            occupancy_duration("train_events", None, _obs(30.0)),
            occupancy_duration(
                "train_events",
                SynthBoundary("CENSORED", None, None, censoring_direction="LEFT"),
                _obs(30.0),
            ),
            occupancy_duration("train_events", _obs(5.0, "front"), _obs(30.0, "back")),
        ]
        s = summarize_occupancy(rs)
        assert s["evaluable_n"] == 3 and s["not_evaluable_n"] == 3
        assert s["mean_s"] == pytest.approx(35.0) and s["median_s"] == pytest.approx(30.0)
        assert (s["min_s"], s["max_s"]) == (20.0, 55.0)
        assert s["not_evaluable_reasons"] == {
            "physical_onset_missing": 1,
            "onset_left_censored": 1,
            "clock_mismatch_r04_unresolved": 1,
        }

    def test_all_not_evaluable_yields_no_statistics(self):
        s = summarize_occupancy([occupancy_duration("train_events", None, None)])
        assert s["evaluable_n"] == 0 and s["mean_s"] is None and s["median_s"] is None

    def test_m4_and_occupancy_denominators_are_independent_and_not_combined(self):
        w = M4_WINDOW
        ev = EventMetricsCalculator.evaluate_run
        # event 1: M4 evaluable, occupancy NOT (onset missing)
        m4_1 = ev(
            _run(_timeline([True] * 6), "train_events/event_001"),
            clearance_time_s=4.5,
            premature_opening_window=w,
        )
        occ_1 = occupancy_duration("train_events", None, _obs(4.5))
        # event 2: M5 never protected (M4 excluded), occupancy evaluable
        m4_2 = ev(
            _run(_timeline([False] * 6), "train_events/event_002"),
            clearance_time_s=4.5,
            premature_opening_window=w,
        )
        occ_2 = occupancy_duration("train_events", _obs(1.0), _obs(4.5))
        # event 3: both evaluable
        m4_3 = ev(
            _run(_timeline([True, False, True, True, True, True]), "train_events/event_003"),
            clearance_time_s=4.5,
            premature_opening_window=w,
        )
        occ_3 = occupancy_duration("train_events", _obs(0.5), _obs(4.5))

        summary = EventMetricsCalculator.aggregate_cohort([m4_1, m4_2, m4_3])
        occ = summarize_occupancy([occ_1, occ_2, occ_3])

        assert summary.premature_opening_evaluable_count == 2  # events 1, 3
        assert summary.never_protected_count == 1  # event 2, reported separately
        assert occ["evaluable_n"] == 2  # events 2, 3
        # The counts happen to match (2 and 2); the evaluable *sets* differ -- that is the
        # property under test:
        m4_ids = {e.event_id for e in summary.single_events if e.premature_opening is not None}
        occ_ids = {"train_events/event_002", "train_events/event_003"}
        assert m4_ids == {"train_events/event_001", "train_events/event_003"} and m4_ids != occ_ids
        # No combined/blended score exists in either output.
        assert not any("combined" in k or "composite" in k for k in summary.to_dict())
        assert not any("combined" in k or "composite" in k for k in occ)


# ---------------------------------------------------------------------------
# Part 3 - superseded
# ---------------------------------------------------------------------------
# The Mission 4E.3 test-local reference for the corrected incomplete-replay classification was
# replaced in Mission 5A by tests of the PRODUCTION functions ``classify_m4`` / ``evaluate_run``:
# see tests/unit/test_mission5a_production.py.
