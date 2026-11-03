"""Mission 5A production regression tests -- SYNTHETIC-ONLY.

Every input is hand-built.  No media, ground-truth file, cache, checkpoint, configuration or
manifest is read, and no inference, training, replay of real data or experiment is run.  Unlike
the Mission 4E.2/4E.3 reference-function tests, these exercise the PRODUCTION functions:
``classify_m4``, ``m4_premature_opening``, ``EventMetricsCalculator.evaluate_run`` /
``aggregate_cohort``, ``resolve_event_cohort``, ``screen_missed_train_lead_in``,
``derive_min_block_latency_s`` (synthetic engine trace), the proposed (inactive) Stage-2.1 schema
module, and the in-code decision register.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pytest

from railway_detection.annotation import stage2_1_schema_proposed as proposed
from railway_detection.annotation.batch_multimodal_annotator import (
    BatchMultimodalAnnotator,
    LegacyAnnotatorGuardError,
)
from railway_detection.evaluation.lead_in_screen import (
    SCREEN_INSUFFICIENT_LEAD_IN,
    SCREEN_NOT_APPLIED,
    SCREEN_PASSED,
    SCREEN_T1_MISSING,
    SCREEN_UNVERIFIABLE,
    derive_min_block_latency_s,
    screen_missed_train_lead_in,
)
from railway_detection.evaluation.metrics import (
    M4_REASON_NO_INTERIOR_STEPS,
    M4_REASON_REPLAY_EMPTY,
    M4_REASON_REPLAY_ENDED_BEFORE_T4,
    M4_REASON_T4_MISSING,
    M4_STATUS_EVALUABLE,
    M4_STATUS_NEVER_PROTECTED,
    M4_STATUS_NOT_EVALUABLE,
    M4_WINDOW,
    EventMetricsCalculator,
    SingleEventEvaluation,
    UnqualifiedEventIdError,
    classify_m4,
    m4_premature_opening,
    resolve_event_cohort,
)
from railway_detection.experiments.preflight_validator import (
    CANONICAL_DECISION_REGISTER,
    DECISION_STATUS_APPROVED,
    DECISION_STATUS_PENDING,
    HISTORICAL_DECISION_ALIASES,
    lookup_decision_register,
)
from railway_detection.simulation.runner import SimulationRunResult, SimulationStep

SYNTHETIC_ONLY = True
REPO = Path(__file__).resolve().parents[2]
TRAIN = "train_events/event_001"


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


def _line(flags, gates=None, dt=1.0):
    return [_step(i * dt, f, (gates[i] if gates else None)) for i, f in enumerate(flags)]


def _eval(steps, t4, event=TRAIN, **kw):
    return EventMetricsCalculator.evaluate_run(
        _run(steps, event), clearance_time_s=t4, premature_opening_window=M4_WINDOW, **kw
    )


# ---------------------------------------------------------------------------
# 1. The six confirmed M4/M5 cases (classify_m4 AND evaluate_run)
# ---------------------------------------------------------------------------


class TestSixCasesOnProductionCode:
    def test_case1_violation_observed_before_replay_ends(self):
        steps = _line([False, True, True, False, True, True])  # opens at t=3; T4=4.5 reached
        c = classify_m4(_run(steps), 4.5)
        assert (c.status, c.premature, c.never_protected) == (M4_STATUS_EVALUABLE, True, False)
        ev = _eval(steps, 4.5)
        assert ev.premature_opening is True and ev.m4_status == M4_STATUS_EVALUABLE

    def test_case2_protected_through_valid_t4_no_violation(self):
        steps = _line([False, True, True, True, True, True])
        c = classify_m4(_run(steps), 4.5)
        assert (c.status, c.premature, c.never_protected, c.replay_complete) == (
            M4_STATUS_EVALUABLE,
            False,
            False,
            True,
        )
        assert _eval(steps, 4.5).premature_opening is False

    def test_case3_no_blocked_step_replay_reaches_t4_is_m5(self):
        steps = _line([False] * 6)
        c = classify_m4(_run(steps), 4.5)
        assert (c.status, c.premature, c.never_protected) == (M4_STATUS_NEVER_PROTECTED, None, True)
        ev = _eval(steps, 4.5)
        assert ev.premature_opening is None and ev.never_protected is True
        assert "never_protected_before_T4" in ev.metric_exclusions["premature_opening"]

    def test_case4a_no_blocked_step_short_replay_is_not_evaluable_not_m5(self):
        steps = _line([False] * 4)  # t=0..3; T4=20 unobserved
        c = classify_m4(_run(steps), 20.0)
        assert (c.status, c.never_protected, c.reason) == (
            M4_STATUS_NOT_EVALUABLE,
            None,
            M4_REASON_REPLAY_ENDED_BEFORE_T4,
        )
        ev = _eval(steps, 20.0)
        assert ev.never_protected is None and ev.premature_opening is None
        assert ev.metric_exclusions["premature_opening"] == M4_REASON_REPLAY_ENDED_BEFORE_T4

    def test_case4b_empty_replay_is_not_evaluable_not_m5(self):
        c = classify_m4(_run([]), 5.0)
        assert (c.status, c.never_protected, c.reason, c.replay_complete) == (
            M4_STATUS_NOT_EVALUABLE,
            None,
            M4_REASON_REPLAY_EMPTY,
            False,
        )
        ev = _eval([], 5.0)
        assert ev.never_protected is None and ev.m4_reason == M4_REASON_REPLAY_EMPTY

    def test_case5_blocked_no_violation_replay_ends_before_t4(self):
        steps = _line([True] * 5)  # blocked t=0..4; T4=20
        c = classify_m4(_run(steps), 20.0)
        assert (c.status, c.premature, c.never_protected, c.reason) == (
            M4_STATUS_NOT_EVALUABLE,
            None,
            None,
            M4_REASON_REPLAY_ENDED_BEFORE_T4,
        )
        ev = _eval(steps, 20.0)
        assert ev.premature_opening is None  # NOT a clean "not premature"
        assert ev.m4_status == M4_STATUS_NOT_EVALUABLE

    def test_case6_violation_witnessed_then_replay_ends_before_t4(self):
        steps = _line([True, True, False, True])  # opens at t=2; replay ends t=3 < T4=20
        c = classify_m4(_run(steps), 20.0)
        assert (c.status, c.premature, c.never_protected, c.replay_complete) == (
            M4_STATUS_EVALUABLE,
            True,
            False,
            False,
        )
        assert _eval(steps, 20.0).premature_opening is True

    def test_opening_state_while_still_blocked_is_a_witnessed_violation(self):
        steps = _line([True] * 4, gates=["CLOSED", "OPENING", "CLOSED", "CLOSED"])
        assert classify_m4(_run(steps), 20.0).premature is True


# ---------------------------------------------------------------------------
# 2-7. Empty / truncated / sparse / missing T4 / strict interval / witnessed violation
# ---------------------------------------------------------------------------


class TestReplayCompletenessEdges:
    def test_no_timestamp_tolerance_last_step_just_short_of_t4_is_incomplete(self):
        steps = _line([True] * 5)  # last t=4.0
        assert classify_m4(_run(steps), 4.01).reason == M4_REASON_REPLAY_ENDED_BEFORE_T4
        assert classify_m4(_run(steps), 4.0).status == M4_STATUS_EVALUABLE

    def test_sparse_replay_without_interior_step_is_not_evaluable(self):
        steps = [_step(0.0, True), _step(5.0, True)]  # nothing strictly inside (0, 5)
        c = classify_m4(_run(steps), 5.0)
        assert (c.status, c.reason, c.interior_step_count) == (
            M4_STATUS_NOT_EVALUABLE,
            M4_REASON_NO_INTERIOR_STEPS,
            0,
        )

    def test_sparse_gaps_are_reported_but_no_gap_tolerance_is_applied(self):
        steps = [_step(0.0, True), _step(1.0, True), _step(9.0, True)]  # 8 s gap
        c = classify_m4(_run(steps), 9.0)
        assert c.status == M4_STATUS_EVALUABLE and c.premature is False
        assert c.max_step_gap_s == pytest.approx(8.0)  # diagnostic only

    def test_missing_t4_is_not_evaluable_and_asserts_neither_m4_nor_m5(self):
        steps = _line([True] * 4)
        c = classify_m4(_run(steps), None)
        assert (c.status, c.reason, c.premature, c.never_protected) == (
            M4_STATUS_NOT_EVALUABLE,
            M4_REASON_T4_MISSING,
            None,
            None,
        )
        ev = _eval(steps, None, exclusion_reasons={"T4_tail_clearance": "censored"})
        summary = EventMetricsCalculator.aggregate_cohort([ev])
        assert summary.exclusions["premature_opening"][0]["reason"] == "T4_tail_clearance:censored"

    def test_strict_interval_start_and_t4_steps_are_excluded(self):
        # unblocked step exactly at T4 does not count; just inside it does
        steps = _line([True, True, True, False])
        assert classify_m4(_run(steps), 3.0).premature is False
        assert classify_m4(_run(steps), 3.01).premature is True
        # a non-blocked label on the start step itself is not inside the open interval
        s2 = _line([True, True, True], gates=["OPENING", "CLOSED", "CLOSED"])
        assert classify_m4(_run(s2), 2.0).premature is False

    @pytest.mark.parametrize("bad", [math.nan, math.inf, -1.0])
    def test_invalid_t4_raises(self, bad):
        with pytest.raises(ValueError):
            classify_m4(_run(_line([True] * 3)), bad)

    def test_non_increasing_replay_timestamps_raise(self):
        with pytest.raises(ValueError, match="strictly increasing"):
            classify_m4(_run([_step(0.0), _step(2.0), _step(2.0)]), 5.0)

    def test_backward_compatible_tuple_view(self):
        assert m4_premature_opening(_run(_line([True, False, True, True])), 3.0) == (True, False)
        assert m4_premature_opening(_run(_line([False] * 4)), 20.0) == (None, None)
        assert m4_premature_opening(_run(_line([False] * 6)), 4.5) == (None, True)


# ---------------------------------------------------------------------------
# 8-9. M5 eligibility and M4 denominator correctness (aggregation)
# ---------------------------------------------------------------------------


class TestAggregationSeparation:
    def _cohort(self):
        mk = lambda n, steps, t4, **kw: _eval(steps, t4, event=f"train_events/event_{n:03d}", **kw)  # noqa: E731
        evs = [
            mk(1, _line([True] * 6), 4.5),  # clean
            mk(2, _line([True, True, False, True, True, True]), 4.5),  # premature
            mk(3, _line([False] * 6), 4.5),  # M5
            mk(4, _line([True] * 4), 20.0),  # incomplete (blocked, no violation)
            mk(5, _line([False] * 4), 20.0),  # incomplete (no blocked) -> not M5
            mk(6, _line([True, False, True]), 20.0),  # witnessed violation, incomplete replay
            mk(7, [], 4.5),  # empty
            mk(8, _line([True] * 4), None, exclusion_reasons={"T4_tail_clearance": "censored"}),
        ]
        return EventMetricsCalculator.aggregate_cohort(evs)

    def test_m4_denominator_and_partition(self):
        s = self._cohort()
        assert s.premature_opening_evaluable_count == 3  # events 1, 2, 6
        assert s.premature_opening_count == 2  # 2, 6
        assert s.m4_no_violation_count == 1  # 1
        assert (
            s.premature_opening_count + s.m4_no_violation_count
            == s.premature_opening_evaluable_count
        )

    def test_m5_counts_only_complete_replays_and_identity_holds(self):
        s = self._cohort()
        assert s.never_protected_count == 1  # event 3 only
        assert s.never_protected_evaluable_count == 4  # 1, 2, 3, 6
        assert s.never_protected_evaluable_count == (
            s.premature_opening_evaluable_count + s.never_protected_count
        )

    def test_incomplete_replays_are_listed_with_reasons_not_dropped(self):
        s = self._cohort()
        assert s.m4_not_evaluable_reasons == {
            M4_REASON_REPLAY_ENDED_BEFORE_T4: 2,
            M4_REASON_REPLAY_EMPTY: 1,
            M4_REASON_T4_MISSING: 1,
        }
        assert s.m4_not_evaluable_count == 4
        listed = {x["event_id"] for x in s.exclusions["premature_opening"]}
        assert {
            "train_events/event_003",
            "train_events/event_004",
            "train_events/event_005",
            "train_events/event_007",
            "train_events/event_008",
        } <= listed

    def test_to_dict_exposes_distinct_counts(self):
        d = self._cohort().to_dict()
        for key in (
            "m4_no_violation_count",
            "m4_not_evaluable_count",
            "m4_not_evaluable_reasons",
            "never_protected_count",
            "premature_opening_count",
        ):
            assert key in d

    def test_mixed_windows_are_still_refused(self):
        a = _eval(_line([True] * 6), 4.5)
        b = EventMetricsCalculator.evaluate_run(
            _run(_line([True] * 6), "train_events/event_002"),
            entry_time_s=0.5,
            clearance_time_s=4.5,
            premature_opening_window="t1_entry_to_t4_clearance",
        )
        with pytest.raises(ValueError, match="mixes premature-opening windows"):
            EventMetricsCalculator.aggregate_cohort([a, b])

    def test_unimplemented_window_name_is_refused(self):
        with pytest.raises(ValueError, match="not implemented"):
            EventMetricsCalculator.evaluate_run(
                _run(_line([True])), clearance_time_s=1.0, premature_opening_window="occupancy"
            )


# ---------------------------------------------------------------------------
# 10-12. Engine exclusion, bare-id fail-closed, cohort-qualified identity (TF-02)
# ---------------------------------------------------------------------------


class TestIdentityAndEngineExclusion:
    def test_bare_id_without_cohort_fails_closed(self):
        with pytest.raises(UnqualifiedEventIdError):
            _eval(_line([True] * 4), 3.5, event="event_001")

    def test_bare_id_with_explicit_cohort_is_accepted(self):
        ev = _eval(_line([True] * 4), 3.0, event="event_001", cohort="train_events")
        assert ev.evaluable is True and ev.m4_status == M4_STATUS_EVALUABLE

    def test_bare_engine_id_with_engine_cohort_is_excluded(self):
        ev = _eval(_line([True] * 4), 3.5, event="event_001", cohort="engine_events")
        assert ev.evaluable is False and ev.notes == "engine_event_excluded"
        assert ev.premature_opening is None and ev.never_protected is None

    def test_qualified_engine_id_is_excluded_and_not_pooled(self):
        eng = _eval(_line([True] * 4), 3.0, event="engine_events/event_001")
        trn = _eval(_line([True] * 4), 3.0, event="train_events/event_001")
        s = EventMetricsCalculator.aggregate_cohort([eng, trn])
        assert s.engine_events == 1 and s.eligible_events == 1
        assert s.premature_opening_evaluable_count == 1 and s.never_protected_evaluable_count == 1

    @pytest.mark.parametrize(
        "event,cohort",
        [
            ("train_events/event_001", "engine_events"),  # contradiction
            ("train_events/event_001", "not_a_cohort"),  # unknown cohort
            ("weird_cohort/event_001", None),  # unknown prefix
            ("train_events/", None),  # empty tail
            ("train_events/a/b", None),  # extra separator
            ("", None),
        ],
    )
    def test_malformed_or_contradictory_identity_fails_closed(self, event, cohort):
        with pytest.raises(UnqualifiedEventIdError):
            resolve_event_cohort(event, cohort)

    def test_same_bare_id_in_three_cohorts_stays_distinct(self):
        evs = [
            _eval(
                _line([True] * 4),
                3.5,
                event=f"{c}/event_001",
                has_train_ground_truth=(c != "no_train_events"),
            )
            for c in ("train_events", "no_train_events", "engine_events")
        ]
        s = EventMetricsCalculator.aggregate_cohort(
            [e for e in evs if e.event_id.startswith("train_events")] + [evs[2]]
        )
        assert s.total_events == 2

    def test_no_train_event_is_not_in_m4_or_m5_denominators(self):
        nt = EventMetricsCalculator.evaluate_run(
            _run(_line([False] * 4), "no_train_events/event_001"),
            has_train_ground_truth=False,
            premature_opening_window=M4_WINDOW,
        )
        s = EventMetricsCalculator.aggregate_cohort([nt])
        assert s.no_train_events == 1 and s.premature_opening_evaluable_count == 0
        assert s.never_protected_evaluable_count == 0

    def test_legacy_v6_annotator_fails_closed(self):
        with pytest.raises(LegacyAnnotatorGuardError):
            BatchMultimodalAnnotator()


# ---------------------------------------------------------------------------
# 13. Missed-train lead-in feasibility screen (RD-021)
# ---------------------------------------------------------------------------


class TestLeadInScreen:
    SRC = "unit-test: explicit value"

    def _screen(self, t1, t0=None, censored=False, latency=3.6):
        return screen_missed_train_lead_in(
            t1,
            first_visible_time_s=t0,
            first_visible_left_censored=censored,
            min_block_latency_s=latency,
            min_block_latency_source=self.SRC,
        )

    def test_left_censored_t0_uses_replay_start(self):
        r = self._screen(3.2, censored=True)
        assert (r.outcome, r.evaluable, r.available_lead_in_s) == (
            SCREEN_INSUFFICIENT_LEAD_IN,
            False,
            3.2,
        )
        assert r.approach_start_basis == "replay_start_left_censored"
        assert self._screen(3.6, censored=True).outcome == SCREEN_PASSED  # boundary: >=

    def test_observed_t0_uses_t0_to_t1(self):
        assert self._screen(10.0, t0=7.0).outcome == SCREEN_INSUFFICIENT_LEAD_IN  # 3.0 < 3.6
        assert self._screen(10.0, t0=2.0).outcome == SCREEN_PASSED  # 8.0 >= 3.6

    def test_unknown_t0_is_unverifiable_not_a_failure(self):
        r = self._screen(2.0, t0=None, censored=False)
        assert (r.outcome, r.evaluable) == (SCREEN_UNVERIFIABLE, False)

    def test_missing_t1_is_not_fabricated(self):
        r = self._screen(None, censored=True)
        assert (r.outcome, r.entry_time_s) == (SCREEN_T1_MISSING, None)

    def test_inputs_are_validated(self):
        with pytest.raises(ValueError):
            self._screen(3.0, censored=True, latency=0.0)
        with pytest.raises(ValueError):
            self._screen(math.nan, censored=True)
        with pytest.raises(ValueError, match="after danger-zone entry"):
            self._screen(3.0, t0=5.0)
        with pytest.raises(ValueError, match="provenance"):
            screen_missed_train_lead_in(
                3.0,
                first_visible_time_s=None,
                first_visible_left_censored=True,
                min_block_latency_s=3.6,
                min_block_latency_source=" ",
            )

    def test_derived_latency_is_synthetic_and_matches_screen_boundary(self):
        latency = derive_min_block_latency_s()
        assert 3.0 < latency < 4.5  # the frozen engine/gate model blocks about 3.6 s after evidence
        assert self._screen(latency, censored=True, latency=latency).outcome == SCREEN_PASSED
        assert self._screen(latency - 0.1, censored=True, latency=latency).outcome == (
            SCREEN_INSUFFICIENT_LEAD_IN
        )

    def _missed_replay(self):
        return _line([False] * 12)  # barrier never blocks: a candidate "missed train" if evaluable

    def test_insufficient_lead_in_is_not_a_missed_train_in_evaluate_run(self):
        ev = EventMetricsCalculator.evaluate_run(
            _run(self._missed_replay()),
            entry_time_s=3.0,
            clearance_time_s=10.0,
            lead_in_min_block_latency_s=3.6,
            lead_in_latency_source=self.SRC,
            first_visible_left_censored=True,
        )
        assert ev.missed_train is None  # not a failure
        assert ev.missed_train_screen == SCREEN_INSUFFICIENT_LEAD_IN
        assert ev.metric_exclusions["missed_train"] == SCREEN_INSUFFICIENT_LEAD_IN

    def test_sufficient_lead_in_real_miss_is_still_a_miss(self):
        ev = EventMetricsCalculator.evaluate_run(
            _run(self._missed_replay()),
            entry_time_s=6.0,
            clearance_time_s=10.0,
            lead_in_min_block_latency_s=3.6,
            lead_in_latency_source=self.SRC,
            first_visible_left_censored=True,
        )
        assert ev.missed_train is True and ev.missed_train_screen == SCREEN_PASSED

    def test_screen_is_off_by_default_and_changes_nothing(self):
        ev = EventMetricsCalculator.evaluate_run(
            _run(self._missed_replay()), entry_time_s=3.0, clearance_time_s=10.0
        )
        assert ev.missed_train is True and ev.missed_train_screen == SCREEN_NOT_APPLIED

    def test_aggregation_separates_insufficient_lead_in_from_failures(self):
        def ev(n, t1):
            return EventMetricsCalculator.evaluate_run(
                _run(self._missed_replay(), f"train_events/event_{n:03d}"),
                entry_time_s=t1,
                clearance_time_s=10.0,
                lead_in_min_block_latency_s=3.6,
                lead_in_latency_source=self.SRC,
                first_visible_left_censored=True,
            )

        s = EventMetricsCalculator.aggregate_cohort([ev(1, 2.0), ev(2, 3.0), ev(3, 7.0)])
        assert s.missed_train_insufficient_lead_in_count == 2
        assert s.missed_train_evaluable_count == 1 and s.missed_train_count == 1
        assert s.missed_train_screen_excluded_count == 2

    def test_screen_requires_provenance_when_enabled(self):
        with pytest.raises(ValueError, match="provenance"):
            EventMetricsCalculator.evaluate_run(
                _run(self._missed_replay()),
                entry_time_s=3.0,
                clearance_time_s=10.0,
                lead_in_min_block_latency_s=3.6,
                first_visible_left_censored=True,
            )


# ---------------------------------------------------------------------------
# 14. Censoring handling (RD-011): excluded from point estimates, reasons kept
# ---------------------------------------------------------------------------


class TestCensoringHandling:
    def test_censored_t4_is_excluded_with_reason_and_never_zeroed(self):
        ev = _eval(_line([True] * 5), None, exclusion_reasons={"T4_tail_clearance": "censored"})
        s = EventMetricsCalculator.aggregate_cohort([ev])
        assert s.premature_opening_evaluable_count == 0 and s.premature_opening_rate is None
        assert s.exclusions["premature_opening"][0]["reason"] == "T4_tail_clearance:censored"

    def test_ground_truth_censored_status_event_is_not_evaluable(self):
        ev = _eval(_line([True] * 5), None, ground_truth_status="censored")
        assert ev.evaluable is False and ev.premature_opening is None


# ---------------------------------------------------------------------------
# 15. Proposed (inactive) Stage-2.1 schema validation (RD-012)
# ---------------------------------------------------------------------------


def _obs(state="OBSERVABLE", **kw):
    base = dict(rationale="synthetic rationale text", evidence_status="PRESENT")
    if state == "OBSERVABLE":
        base.update(value_s=12.5, reference_camera="back", frame_index=375)
    base.update(kw)
    return proposed.BoundaryObservation(state=state, **base)


def _entry(reviewer="synthetic_reviewer_A", role="FIRST", obs_overrides=None, status="SUBMITTED"):
    onset = proposed.OnsetProvenance("HUMAN_VISUAL_LANDMARK", "synthetic landmark description")
    obs = {
        "T0_first_visible": _obs(
            "CENSORED", censoring_direction="LEFT", evidence_status="INSUFFICIENT"
        ),
        "T1_danger_zone_entry": _obs(onset_provenance=onset, reference_camera="front"),
        "T2_crossing_occupancy_start": _obs(onset_provenance=onset, reference_camera="front"),
        "T3_locomotive_unit_clearance": _obs(),
        "T4_tail_clearance": _obs(value_s=47.0),
        "T_scene_clear": _obs(
            "NOT_OBSERVABLE",
            not_observable_reason="not_visible_in_recording",
            evidence_status="MISSING",
        ),
    }
    obs.update(obs_overrides or {})
    return proposed.ReviewerEntry(
        reviewer_id=reviewer,
        role=role,
        review_status=status,
        observations=obs,
        direction=proposed.DirectionObservation(
            "OBSERVABLE", "synthetic direction note", "left_to_right"
        ),
    )


class TestProposedSchema:
    def test_version_is_proposed_and_never_the_active_version(self):
        assert proposed.PROPOSED_SCHEMA_VERSION.endswith("-proposed")
        assert proposed.PROPOSED_SCHEMA_VERSION != proposed.ACTIVE_SCHEMA_VERSION_NOT_SATISFIED

    def test_valid_synthetic_record_with_independent_first_and_second_reviews(self):
        rec = proposed.ProposedStage21Record(
            event_id="train_events/event_001",
            cohort="train_events",
            reviewers=[_entry("synthetic_A", "FIRST"), _entry("synthetic_B", "SECOND")],
        )
        assert len(rec.reviewers) == 2

    def test_four_states_are_distinguished(self):
        assert set(proposed.BOUNDARY_STATES) == {
            "OBSERVABLE",
            "UNCERTAIN",
            "CENSORED",
            "NOT_OBSERVABLE",
        }

    def test_censored_requires_direction_and_observable_requires_value_and_camera(self):
        with pytest.raises(proposed.ProposedSchemaError):
            _obs("CENSORED")  # no direction
        with pytest.raises(proposed.ProposedSchemaError):
            proposed.BoundaryObservation("OBSERVABLE", "synthetic text", "PRESENT")
        with pytest.raises(proposed.ProposedSchemaError):
            _obs("UNCERTAIN", value_s=1.0)  # value only when OBSERVABLE
        with pytest.raises(proposed.ProposedSchemaError):
            _obs("NOT_OBSERVABLE")  # reason required

    def test_uncertainty_may_be_none_tolerance_deferred_but_must_be_valid_if_given(self):
        assert _obs(timestamp_uncertainty_s=None).timestamp_uncertainty_s is None
        with pytest.raises(proposed.ProposedSchemaError):
            _obs(timestamp_uncertainty_s=-0.1)

    @pytest.mark.parametrize("basis", ["REPLAY_DERIVED", "FIRST_BLOCKED", "MODEL_PREDICTION"])
    def test_replay_or_model_derived_onset_is_rejected(self, basis):
        with pytest.raises(proposed.ProposedSchemaError, match="forbidden"):
            proposed.OnsetProvenance(basis)

    def test_observable_onset_requires_human_landmark_provenance(self):
        with pytest.raises(proposed.ProposedSchemaError):
            _entry(obs_overrides={"T2_crossing_occupancy_start": _obs()})  # no provenance
        with pytest.raises(proposed.ProposedSchemaError):
            _entry(
                obs_overrides={
                    "T3_locomotive_unit_clearance": _obs(
                        onset_provenance=proposed.OnsetProvenance("NOT_ESTABLISHED")
                    )
                }
            )  # only T1/T2

    def test_no_approved_status_can_be_represented(self):
        assert (
            "APPROVED" not in proposed.REVIEW_STATUSES
            and "PROMOTED" not in proposed.REVIEW_STATUSES
        )
        with pytest.raises(proposed.ProposedSchemaError):
            _entry(status="APPROVED")

    def test_reviewer_identity_is_never_defaulted(self):
        with pytest.raises(proposed.ProposedSchemaError):
            _entry(reviewer="  ")

    def test_distinct_reviewers_and_role_rules(self):
        with pytest.raises(proposed.ProposedSchemaError):
            proposed.ProposedStage21Record(
                "train_events/event_001",
                "train_events",
                [_entry("same", "FIRST"), _entry("same", "SECOND")],
            )
        with pytest.raises(proposed.ProposedSchemaError):
            proposed.ProposedStage21Record(
                "train_events/event_001", "train_events", [_entry("b", "SECOND")]
            )

    def test_event_id_must_be_cohort_qualified_and_match_cohort(self):
        with pytest.raises(proposed.ProposedSchemaError):
            proposed.ProposedStage21Record("event_001", "train_events", [_entry()])
        with pytest.raises(proposed.ProposedSchemaError):
            proposed.ProposedStage21Record("engine_events/event_001", "train_events", [_entry()])

    def test_direction_is_per_event_and_must_be_observed_to_have_a_value(self):
        with pytest.raises(proposed.ProposedSchemaError):
            proposed.DirectionObservation("UNCERTAIN", "note text", "left_to_right")
        with pytest.raises(proposed.ProposedSchemaError):
            proposed.DirectionObservation("OBSERVABLE", "note text", "sideways")

    def test_adjudication_is_separate_and_does_not_alter_reviewer_observations(self):
        a, b = (
            _entry("synthetic_A", "FIRST"),
            _entry(
                "synthetic_B",
                "SECOND",
                obs_overrides={"T4_tail_clearance": _obs(value_s=49.0)},
            ),
        )
        ha, hb = (proposed.entry_sha256(e.observations, e.direction) for e in (a, b))
        before = (
            a.observations["T4_tail_clearance"].value_s,
            b.observations["T4_tail_clearance"].value_s,
        )
        adj = proposed.AdjudicationEntry(
            adjudicator_id="synthetic_researcher",
            resolutions={"T4_tail_clearance": {"state": "UNCERTAIN"}},
            rationale="unresolved disagreement stays UNCERTAIN",
            references_entry_sha256=(ha, hb),
        )
        rec = proposed.ProposedStage21Record("train_events/event_001", "train_events", [a, b], adj)
        after = (
            a.observations["T4_tail_clearance"].value_s,
            b.observations["T4_tail_clearance"].value_s,
        )
        assert before == after == (47.0, 49.0)
        assert rec.adjudication.resolutions["T4_tail_clearance"]["state"] == "UNCERTAIN"
        assert proposed.entry_sha256(a.observations, a.direction) == ha  # provenance unchanged

    def test_entry_hash_detects_tampering_and_adjudication_must_reference_real_entries(self):
        a = _entry("synthetic_A", "FIRST")
        good = proposed.entry_sha256(a.observations, a.direction)
        a.observations["T4_tail_clearance"].value_s = 50.0  # tamper
        with pytest.raises(proposed.ProposedSchemaError, match="entry_sha256"):
            proposed.ReviewerEntry(
                a.reviewer_id,
                a.role,
                a.review_status,
                a.observations,
                a.direction,
                entry_sha256=good,
            )
        c = _entry("synthetic_C", "FIRST")
        bad_adj = proposed.AdjudicationEntry("synthetic_researcher", {}, "reason text", ("0" * 64,))
        with pytest.raises(proposed.ProposedSchemaError, match="unknown reviewer entry"):
            proposed.ProposedStage21Record("train_events/event_002", "train_events", [c], bad_adj)

    def test_proposed_module_is_not_imported_by_any_gate_or_loader(self):
        offenders = []
        for path in (REPO / "src").rglob("*.py"):
            if path.name == "stage2_1_schema_proposed.py":
                continue
            if "stage2_1_schema_proposed" in path.read_text(encoding="utf-8", errors="ignore"):
                offenders.append(str(path))
        assert offenders == []


# ---------------------------------------------------------------------------
# 16. Decision-register consistency (TF-05) -- nothing approved by Mission 5A
# ---------------------------------------------------------------------------


class TestDecisionRegisterConsistency:
    NEW = (
        "GOV-REVIEW-SECOND-REVIEW-TRIGGERS",
        "GOV-REVIEW-CLEAR-BOUNDARY-AUDIT",
        "AUTH-PILOT-EXEC",
        "AUTH-PROMOTE-EXEC",
    )

    def test_new_identifiers_exist_and_are_pending_not_approved(self):
        for key in self.NEW:
            assert CANONICAL_DECISION_REGISTER[key].status == DECISION_STATUS_PENDING

    def test_aliases_resolve_including_the_spelling_variant(self):
        assert lookup_decision_register("D3A").canonical_id == "GOV-REVIEW-SECOND-REVIEW-TRIGGERS"
        assert lookup_decision_register("D3C").canonical_id == "GOV-REVIEW-CLEAR-BOUNDARY-AUDIT"
        assert lookup_decision_register("AUTH-EVAL-OFFICIAL").canonical_id == "AUTH-EVAL-AUTH"
        assert lookup_decision_register("D3").canonical_id == "GOV-D3-DESCRIPTIVE-MODE"

    def test_exactly_the_previously_approved_entries_are_approved(self):
        approved = {
            k
            for k, v in CANONICAL_DECISION_REGISTER.items()
            if v.status == DECISION_STATUS_APPROVED
        }
        assert approved == {
            "GOV-D3-DESCRIPTIVE-MODE",
            "GOV-B7D-DELIVERY-DISORDER",
            "GOV-B7E-MECHANISM",
            "GOV-GT-STATE-SEPARATION",
            "GOV-ENGINE-EVENT-ISOLATION",
            "GOV-LEG-EXEC-INVALIDATION",
            "GOV-STAGE21-SAFEGUARDS",
        }

    def test_key_decisions_remain_pending(self):
        for key in (
            "GOV-D1-PROTOCOL-AUTHORITY",
            "GOV-D2-EVALUATION-PROFILE",
            "AUTH-EVENT-SPLIT",
            "GOV-D4-R04-SYNCHRONIZATION",
            "EXP-B7E-PARAMETERS",
            "EXP-ROI-GEOMETRY",
            "AUTH-STAGE21-ADJUDICATION",
            "AUTH-EVAL-AUTH",
        ):
            assert CANONICAL_DECISION_REGISTER[key].status == DECISION_STATUS_PENDING

    def test_every_alias_targets_a_canonical_entry(self):
        for alias, target in HISTORICAL_DECISION_ALIASES.items():
            assert target in CANONICAL_DECISION_REGISTER, alias

    def test_gate_text_no_longer_says_m4_is_not_implemented(self):
        from railway_detection.evaluation import execution_gate

        text = (REPO / "src/railway_detection/evaluation/execution_gate.py").read_text(
            encoding="utf-8"
        )
        assert "design M4, not implemented" not in text
        assert execution_gate is not None


# ---------------------------------------------------------------------------
# 17-18. Protocol wording consistency and provenance preservation
# ---------------------------------------------------------------------------

M5A_DIR = REPO / "docs" / "generated" / "mission_5a"


class TestProvenancePreservation:
    def test_evaluation_keeps_event_identity_window_and_classification(self):
        ev = _eval(_line([True, False, True, True, True, True]), 4.5)
        assert isinstance(ev, SingleEventEvaluation)
        assert ev.event_id == TRAIN and ev.premature_opening_window == M4_WINDOW
        assert ev.m4_status == M4_STATUS_EVALUABLE and ev.m4_replay_complete is True

    def test_classification_is_deterministic(self):
        steps = _line([False, True, False, True, True, True])
        assert classify_m4(_run(steps), 4.5) == classify_m4(_run(steps), 4.5)

    def test_lead_in_result_carries_its_own_provenance(self):
        r = screen_missed_train_lead_in(
            5.0,
            first_visible_time_s=None,
            first_visible_left_censored=True,
            min_block_latency_s=3.6,
            min_block_latency_source="synthetic_replay:default_engine",
        )
        assert r.min_block_latency_source == "synthetic_replay:default_engine"
        assert r.approach_start_basis == "replay_start_left_censored"


def _active(text: str) -> str:
    """Normative text: everything outside <!--HISTORICAL--> ... <!--/HISTORICAL--> blocks."""
    return re.sub(r"<!--HISTORICAL-->.*?<!--/HISTORICAL-->", "", text, flags=re.S)


def _read(name: str) -> str:
    return (M5A_DIR / name).read_text(encoding="utf-8")


V9P = "FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL_v9.1.0_PROPOSED.md"
V7P = "FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md"
PAPER = "PAPER_REVISION_PROPOSAL_20261101_M5A.md"


@pytest.mark.skipif(not M5A_DIR.exists(), reason="Mission 5A documents not generated")
class TestProtocolWordingConsistency:
    """Checks the PROPOSED protocol/paper files; the in-place v9/v7 files are never edited."""

    def test_proposals_are_marked_proposed_not_approved_and_record_source_hash(self):
        for name in (V9P, V7P):
            head = _read(name)[:900]
            assert "PROPOSED" in head and "NOT APPROVED" in head
            assert re.search(r"SHA-256 `[0-9a-f]{64}`", head)
            assert "-PROPOSED" in head

    def test_historical_markers_are_balanced(self):
        for name in (V9P, V7P):
            text = _read(name)
            assert text.count("<!--HISTORICAL-->") == text.count("<!--/HISTORICAL-->") > 0

    def test_no_active_t1_based_premature_opening_or_old_t2_wording(self):
        for name in (V9P, V7P):
            active = _active(_read(name))
            assert "t \\ge T_1" not in active and "t ≥ T_1" not in active
            assert "fully occupies" not in active
            assert "transverse camera plane" not in active
            assert "DEFERRED (RD-006)" in active
        v9 = _active(_read(V9P))
        assert "first_blocked_to_t4_clearance" in v9
        assert "not a duration" in v9

    def test_t1_is_the_approach_frog_line_in_both_protocols(self):
        for name in (V9P, V7P):
            assert "approach danger-zone line" in _active(_read(name))

    def test_no_inferential_testing_is_planned(self):
        v9 = _active(_read(V9P))
        assert "Planned tests" not in v9 and "Planned Hypothesis Tests" not in v9
        assert "Significance is not guaranteed" not in v9
        assert "Descriptive statistics only" in v9

    def test_full_occupancy_duration_is_deferred_not_measurable(self):
        v9 = _active(_read(V9P))
        assert "DEFERRED (RD-018)" in v9
        assert "not reported" in v9

    def test_independent_camera_primary_and_fusion_exploratory(self):
        v9 = _active(_read(V9P))
        assert "Independent-camera analysis is primary" in v9
        assert "Fused (R04) analysis is exploratory only" in v9
        assert "20/23" in v9 and "not satisfied" in v9

    def test_engine_excluded_and_unimplemented_design_metrics_labelled(self):
        v9 = _active(_read(V9P))
        assert "Engine events are excluded from pooled M4, M5" in v9
        assert "unimplemented / out of scope" in v9

    def test_paper_proposal_has_no_ai_author_and_no_unsupported_claims(self):
        paper = _active(_read(PAPER))
        authors = paper.split("## Proposed author block")[-1].split("## ")[0]
        assert "Antigravity" not in authors and "Autonomous" not in authors
        assert "full occupancy duration is deferred" in paper.lower()
        assert "AI-use disclosure" in paper and "DRAFT" in paper
        assert not re.search(r"\b(McNemar|Wilcoxon|Holm)\b.*\bplanned\b", paper, flags=re.I)
        assert "independent-camera" in paper.lower()


# ---------------------------------------------------------------------------
# Preservation manifest tool (RD-003) -- synthetic temp tree only
# ---------------------------------------------------------------------------


def _load_manifest_tool():
    import importlib.util

    path = REPO / "scripts" / "mission5a_build_preservation_manifest.py"
    spec = importlib.util.spec_from_file_location("mission5a_manifest_tool", path)
    module = importlib.util.module_from_spec(spec)
    import sys

    sys.modules["mission5a_manifest_tool"] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


class TestPreservationManifestTool:
    def _tree(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "src" / "clip.mov").write_bytes(b"not really media")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "n.md").write_text("# n\n", encoding="utf-8")
        (tmp_path / "data" / "raw").mkdir(parents=True)
        (tmp_path / "data" / "raw" / "v.mp4").write_bytes(b"x")
        (tmp_path / "data" / "raw" / "meta.json").write_text("{}", encoding="utf-8")
        (tmp_path / "scratch").mkdir()
        (tmp_path / "scratch" / "s.py").write_text("y = 2\n", encoding="utf-8")
        return tmp_path

    def test_media_and_output_trees_are_never_opened_or_hashed(self, tmp_path, monkeypatch):
        tool = _load_manifest_tool()
        opened = []
        real = tool.sha256_file
        monkeypatch.setattr(tool, "sha256_file", lambda p: (opened.append(p.name), real(p))[1])
        root = self._tree(tmp_path)
        manifest = tool.build_manifest(root)
        paths = {e["path"] for e in manifest["entries"]}
        assert paths == {"src/a.py", "docs/n.md"}
        assert "clip.mov" not in opened and "v.mp4" not in opened and "meta.json" not in opened
        assert "media_binary_or_model_not_opened" in manifest["excluded"]
        # Mission 5B (DEC-A02): output trees are pruned by default and only counted on request.
        assert "generated_output_tree" not in manifest["excluded"]
        counted = tool.build_manifest(root, count_excluded_trees=True)
        assert counted["excluded"]["generated_output_tree"]["file_count"] >= 3
        assert {e["path"] for e in counted["entries"]} == paths

    def test_hashes_are_correct_and_verify_detects_change_and_missing(self, tmp_path):
        import hashlib

        tool = _load_manifest_tool()
        root = self._tree(tmp_path)
        manifest = tool.build_manifest(root)
        entry = next(e for e in manifest["entries"] if e["path"] == "src/a.py")
        assert entry["sha256"] == hashlib.sha256(b"x = 1\n").hexdigest()
        assert tool.verify_manifest(root, manifest)["clean"] is True
        (root / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
        (root / "docs" / "n.md").unlink()
        result = tool.verify_manifest(root, manifest)
        assert result["changed"] == ["src/a.py"] and result["missing"] == ["docs/n.md"]
        assert result["clean"] is False

    def test_manifest_is_labelled_not_an_approval_and_build_refuses_overwrite(self, tmp_path):
        tool = _load_manifest_tool()
        manifest = tool.build_manifest(self._tree(tmp_path))
        assert "NOT AN APPROVAL" in manifest["status"]
        out = tmp_path / "m.json"
        out.write_text("{}", encoding="utf-8")
        assert tool.main(["build", "--root", str(tmp_path), "--out", str(out)]) == 2
