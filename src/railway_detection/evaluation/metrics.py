"""System-level and event-level railway crossing safety metrics.

Implements research evaluation metrics defined in docs/EXPERIMENT_PROTOCOL_V2.md §5 & §11:
- Missed-train rate (safety-critical)
- Premature-opening rate (safety-critical)
- Warning lead time (s)
- Excess gate-closed duration (s)
- Clearance verification latency (s)
- Wilson score 95% confidence intervals for binomial safety rates
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from statistics import NormalDist
from typing import Any, ClassVar

from railway_detection.evaluation.lead_in_screen import (
    SCREEN_EXCLUDING_OUTCOMES,
    SCREEN_INSUFFICIENT_LEAD_IN,
    SCREEN_NOT_APPLIED,
    LeadInScreenResult,
    screen_missed_train_lead_in,
)
from railway_detection.evaluation.timebase import normalize_timestamp
from railway_detection.simulation.runner import SimulationRunResult


def wilson_score_interval(
    successes: int, total: int, confidence: float = 0.95
) -> tuple[float, float] | None:
    """Calculate Wilson score confidence interval for a binomial proportion.

    Args:
        successes: Number of occurrences.
        total: Total number of trials.
        confidence: Confidence level (default 0.95 for z=1.96).

    Returns:
        Tuple of (ci_lower, ci_upper) in [0.0, 1.0], or ``None`` when the
        denominator is zero and the interval is not computable.
    """
    if isinstance(successes, bool) or isinstance(total, bool):
        raise ValueError("successes and total must be integers")
    if not isinstance(successes, int) or not isinstance(total, int):
        raise ValueError("successes and total must be integers")
    if total < 0 or successes < 0 or successes > total:
        raise ValueError("Wilson counts must satisfy 0 <= successes <= total")
    if not 0.0 < confidence < 1.0 or not math.isfinite(confidence):
        raise ValueError("confidence must be strictly between 0 and 1")
    if total == 0:
        # A zero-denominator interval is not a zero-width estimate.  Callers
        # must serialize this as not_evaluable rather than as a fabricated CI.
        return None
    p = float(successes) / float(total)
    z = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    z2 = z * z
    denom = 1.0 + z2 / total
    center = (p + z2 / (2.0 * total)) / denom
    margin = (z / denom) * math.sqrt((p * (1.0 - p) / total) + (z2 / (4.0 * total * total)))
    return max(0.0, center - margin), min(1.0, center + margin)


@dataclass
class SingleEventEvaluation:
    """Evaluation result for one train-passage event."""

    event_id: str
    scenario_name: str
    has_train_ground_truth: bool = True
    missed_train: bool | None = None  # None = not_evaluable (e.g. missing/unapproved ground truth)
    premature_opening: bool | None = None  # None = not_evaluable
    warning_lead_time_s: float | None = None  # None = not_evaluable
    excess_closed_duration_s: float | None = None
    clearance_latency_s: float | None = None
    total_closed_s: float = 0.0
    fault_occurred: bool = False
    evaluable: bool = True
    notes: str = ""
    # Boundary name -> why it was not an observable value ("censored", "uncertain",
    # "not_applicable_or_unknown"). Reported, never silently dropped.
    exclusion_reasons: dict[str, str] = field(default_factory=dict)
    # No-train nuisance reporting (protocol v9 section 11.2): raw seconds/episodes, no rate.
    blocked_seconds: float | None = None
    closure_episodes: int | None = None
    exposure_s: float | None = None
    # metric -> reason, set when the replay clock model (not the label state) is why a
    # metric could not be computed. Takes precedence over ``exclusion_reasons``.
    metric_exclusions: dict[str, str] = field(default_factory=dict)
    # replay system -> blocked seconds (independent-camera replays have one per clock).
    per_system_closed_s: dict[str, float] = field(default_factory=dict)
    # The premature-opening window this evaluation was computed under; ``None`` means the
    # definition was undecided and the metric was deliberately not computed.
    premature_opening_window: str | None = None
    # M5 (design document): the barrier never blocked before T4. Only set under the M4 window.
    never_protected: bool | None = None
    # Mission 5A (RD-016): explicit three-way M4 classification and its reason. ``m4_status`` is
    # ``EVALUABLE`` / ``NEVER_PROTECTED_M5`` / ``NOT_EVALUABLE``; ``None`` if M4 not requested.
    m4_status: str | None = None
    m4_reason: str | None = None
    m4_replay_complete: bool | None = None
    # Mission 5A (RD-021): lead-in feasibility screen outcome for missed-train reporting.
    missed_train_screen: str = SCREEN_NOT_APPLIED
    lead_in_available_s: float | None = None
    # Mission 5B (DEC-B03): the cohort this record belongs to, so a serialized record identifies
    # itself even when ``event_id`` is bare.  ``None`` only for records whose cohort is unresolved.
    cohort: str | None = None


PREMATURE_OPENING_UNDECIDED = "premature_opening_window_undecided"
V9_WINDOW = "t1_entry_to_t4_clearance"
M4_WINDOW = "first_blocked_to_t4_clearance"
IMPLEMENTED_PREMATURE_WINDOWS = frozenset({V9_WINDOW, M4_WINDOW})


def premature_required_boundaries(window: str | None) -> tuple[str, ...]:
    """Boundaries a window needs: v9 needs T1 and T4; M4 only T4 (t_blocked is replay-side)."""
    if window == M4_WINDOW:
        return ("T4_tail_clearance",)
    return ("T1_danger_zone_entry", "T4_tail_clearance")


KNOWN_COHORTS = ("train_events", "no_train_events", "engine_events")


#: Ground-truth statuses whose records are never evaluable and never enter any denominator.
UNVERIFIED_GROUND_TRUTH_STATUSES = frozenset(
    {"missing", "unknown", "unobservable", "not_applicable", "censored", "uncertain"}
)


class UnqualifiedEventIdError(ValueError):
    """An event identity lacks a cohort, or its cohort is unknown or contradictory.

    Event ids are unique only per cohort (``event_001`` exists in three cohorts).  A bare id
    must never be silently treated as a train event, so evaluation fails closed (RD-041 /
    Mission 5A TF-02).
    """


class UnresolvedCohortError(UnqualifiedEventIdError):
    """A bare event id arrived with no cohort at all (not a malformed or contradictory one)."""


def resolve_event_cohort(event_id: str, cohort: str | None = None) -> str:
    """Return the cohort of an event, requiring a cohort-qualified identity.

    Accepts ``"<cohort>/<event>"`` ids, or a bare id together with an explicit ``cohort``.
    Raises :class:`UnqualifiedEventIdError` for a bare id without a cohort, an unknown cohort,
    a malformed qualified id, or a cohort that contradicts the id prefix.
    """
    if not isinstance(event_id, str) or not event_id.strip():
        raise UnqualifiedEventIdError("event_id must be a non-empty string")
    id_cohort: str | None = None
    if "/" in event_id:
        head, _, tail = event_id.partition("/")
        if head not in KNOWN_COHORTS or not tail.strip() or "/" in tail:
            raise UnqualifiedEventIdError(
                f"event_id {event_id!r} is not '<cohort>/<event>' with cohort in {KNOWN_COHORTS}"
            )
        id_cohort = head
    if cohort is not None and cohort not in KNOWN_COHORTS:
        raise UnqualifiedEventIdError(f"unknown cohort {cohort!r}; expected one of {KNOWN_COHORTS}")
    if id_cohort is not None and cohort is not None and id_cohort != cohort:
        raise UnqualifiedEventIdError(
            f"event_id {event_id!r} contradicts cohort {cohort!r}"
        )
    resolved = cohort or id_cohort
    if resolved is None:
        raise UnresolvedCohortError(
            f"event_id {event_id!r} is not cohort-qualified; pass '<cohort>/<event>' or cohort=..."
        )
    return resolved


M4_STATUS_EVALUABLE = "EVALUABLE"
M4_STATUS_NEVER_PROTECTED = "NEVER_PROTECTED_M5"
M4_STATUS_NOT_EVALUABLE = "NOT_EVALUABLE"
M4_REASON_REPLAY_EMPTY = "replay_empty"
M4_REASON_REPLAY_ENDED_BEFORE_T4 = "replay_ended_before_T4"
M4_REASON_NO_INTERIOR_STEPS = "no_steps_in_protection_interval"
M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4 = "replay_started_at_or_after_T4"
M4_REASON_REPLAY_STARTED_LATE = "replay_started_late"
M4_REASON_T4_MISSING = "t4_missing"
#: Reasons meaning "the replay evidence was incomplete" (never safe, never M5).
M4_INCOMPLETE_REPLAY_REASONS = frozenset(
    {
        M4_REASON_REPLAY_EMPTY,
        M4_REASON_REPLAY_ENDED_BEFORE_T4,
        M4_REASON_NO_INTERIOR_STEPS,
        M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4,
        M4_REASON_REPLAY_STARTED_LATE,
    }
)
#: Recording origin.  M5 asserts the barrier never blocked in ``[origin, T4)``, so it needs a replay
#: that begins here (DEC-C01).  This is the exact start of the timeline, not a tolerance.
REPLAY_ORIGIN_S = 0.0


@dataclass(frozen=True)
class M4Classification:
    """Explicit three-way M4/M5 outcome for one replay (Mission 5A, RD-016).

    ``status`` is ``EVALUABLE`` (``premature`` is a bool), ``NEVER_PROTECTED_M5``
    (``never_protected`` is True and M4 is excluded), or ``NOT_EVALUABLE`` (``reason`` says why;
    neither M4 nor M5 is asserted).  ``replay_complete`` records whether the retained steps cover
    what the verdict relies on, under the accepted no-tolerance rule: for M4 the last step reaches
    T4 (``last_step_s >= T4``); for M5 the replay also begins at the zero origin.
    """

    status: str
    premature: bool | None
    never_protected: bool | None
    reason: str | None
    replay_complete: bool | None
    first_blocked_s: float | None
    last_step_s: float | None
    interior_step_count: int
    max_step_gap_s: float | None  # diagnostic only; no tolerance is applied to it
    first_step_s: float | None = None  # Mission 5B: first retained step; diagnostic


def _validated_replay_timestamps(sim_result: SimulationRunResult) -> list[float]:
    """Return the replay timestamps on the one-microsecond grid (DEC-C05), validated."""
    raw = [step.timestamp_s for step in sim_result.steps]
    if any(not math.isfinite(t) or t < 0.0 for t in raw):
        raise ValueError("simulation steps must have finite, strictly increasing timestamps")
    timestamps = [normalize_timestamp(t) for t in raw]
    if any(right <= left for left, right in zip(timestamps, timestamps[1:], strict=False)):
        raise ValueError("simulation steps must have finite, strictly increasing timestamps")
    return timestamps


def classify_m4(
    sim_result: SimulationRunResult, clearance_time_s: float | None
) -> M4Classification:
    """Classify one replay against an approved T4 on the same timeline.

    Rules (strict open interval ``(t_blocked, T4)``; no timestamp tolerance is introduced; step and
    T4 timestamps are first snapped to the one-microsecond grid, DEC-C05):

    1. A violation (unblocked step, or gate state ``OPENING``/``OPEN``) retained strictly inside
       the interval is a *witnessed* premature opening -- definite even if the replay ends
       before T4 or began after the recording origin.
    2. Otherwise the replay must reach T4 (``last_step >= T4``); an incomplete replay is
       ``NOT_EVALUABLE`` (``replay_ended_before_T4``) and is never a clean "not premature" and
       never M5.
    3. A covered replay with no blocked step before T4 is M5 (never protected) only if it also
       begins at the zero origin (DEC-C01): it must have observed all of ``[0, T4)``.  A first
       step at or after T4 is ``NOT_EVALUABLE`` (``replay_started_at_or_after_T4``); any other
       first step after the origin is ``NOT_EVALUABLE`` (``replay_started_late``).  M4 itself
       needs no zero origin: its interval begins at the observed first blocked step.
    4. A covered replay whose protection interval holds no retained step carries no evidence of
       continuous protection and is ``NOT_EVALUABLE`` (``no_steps_in_protection_interval``;
       DEC-C02).  Neither a nominal tick nor the step gap is used to infer protection.
    5. An empty replay is ``NOT_EVALUABLE`` (``replay_empty``); a missing T4 is
       ``NOT_EVALUABLE`` (``t4_missing``).  Invalid replay timestamps or T4 raise ``ValueError``.
    """

    timestamps = _validated_replay_timestamps(sim_result)
    first_step = timestamps[0] if timestamps else None

    def result(status, premature, never, reason, complete, first, last, interior, gap):
        return M4Classification(
            status=status,
            premature=premature,
            never_protected=never,
            reason=reason,
            replay_complete=complete,
            first_blocked_s=first,
            last_step_s=last,
            interior_step_count=interior,
            max_step_gap_s=gap,
            first_step_s=first_step,
        )

    gaps = [normalize_timestamp(b - a) for a, b in zip(timestamps, timestamps[1:], strict=False)]
    max_gap = max(gaps) if gaps else None
    if clearance_time_s is None:
        return result(
            M4_STATUS_NOT_EVALUABLE, None, None, M4_REASON_T4_MISSING, None, None,
            timestamps[-1] if timestamps else None, 0, max_gap,
        )
    if (
        isinstance(clearance_time_s, bool)
        or not math.isfinite(clearance_time_s)
        or clearance_time_s < 0.0
    ):
        raise ValueError("clearance_time_s must be finite and nonnegative")
    t4 = normalize_timestamp(clearance_time_s)
    observed = list(zip(timestamps, sim_result.steps, strict=True))
    if not observed:
        return result(
            M4_STATUS_NOT_EVALUABLE, None, None, M4_REASON_REPLAY_EMPTY, False, None, None, 0, None
        )
    last = timestamps[-1]
    covered = last >= t4
    t_blocked = next((t for t, s in observed if s.is_passage_blocked), None)
    if t_blocked is not None and t_blocked < t4:
        window = [s for t, s in observed if t_blocked < t < t4]
        violation = any(
            (not s.is_passage_blocked) or s.gate_state in ("OPENING", "OPEN") for s in window
        )
        if violation:
            return result(
                M4_STATUS_EVALUABLE, True, False, None, covered,
                t_blocked, last, len(window), max_gap,
            )
        if not covered:
            return result(
                M4_STATUS_NOT_EVALUABLE, None, None, M4_REASON_REPLAY_ENDED_BEFORE_T4, False,
                t_blocked, last, len(window), max_gap,
            )
        if not window:
            return result(
                M4_STATUS_NOT_EVALUABLE, None, None, M4_REASON_NO_INTERIOR_STEPS, True,
                t_blocked, last, 0, max_gap,
            )
        return result(
            M4_STATUS_EVALUABLE, False, False, None, True, t_blocked, last, len(window), max_gap
        )
    if not covered:
        return result(
            M4_STATUS_NOT_EVALUABLE, None, None, M4_REASON_REPLAY_ENDED_BEFORE_T4, False,
            t_blocked, last, 0, max_gap,
        )
    # M5 asserts a universal negative over [origin, T4): only a replay that observed all of it
    # may assert it.
    if first_step >= t4:
        return result(
            M4_STATUS_NOT_EVALUABLE, None, None, M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4, False,
            t_blocked, last, 0, max_gap,
        )
    if first_step > REPLAY_ORIGIN_S:
        return result(
            M4_STATUS_NOT_EVALUABLE, None, None, M4_REASON_REPLAY_STARTED_LATE, False,
            t_blocked, last, 0, max_gap,
        )
    return result(M4_STATUS_NEVER_PROTECTED, None, True, None, True, t_blocked, last, 0, max_gap)


def m4_premature_opening(
    sim_result: SimulationRunResult, clearance_time_s: float
) -> tuple[bool | None, bool | None]:
    """Backward-compatible ``(premature, never_protected)`` view of :func:`classify_m4`.

    ``never_protected`` is ``None`` (not ``False``) when the replay evidence is incomplete, so
    callers cannot mistake an unobserved tail for either "protected" or "never protected".
    """
    classification = classify_m4(sim_result, clearance_time_s)
    return classification.premature, classification.never_protected


def _closure_episodes(sim_result: SimulationRunResult) -> int:
    """Count contiguous blocked intervals (rising edges of ``is_passage_blocked``)."""
    episodes = 0
    previous = False
    for step in sim_result.steps:
        if step.is_passage_blocked and not previous:
            episodes += 1
        previous = step.is_passage_blocked
    return episodes


@dataclass
class CohortEvaluationSummary:
    """Aggregate metrics over a test event cohort (e.g. B0–B7 experiments)."""

    total_events: int = 0
    eligible_events: int = 0
    missed_train_evaluable_count: int = 0
    missed_train_count: int = 0
    missed_train_rate: float | None = None
    missed_train_ci95: tuple[float, float] | None = None

    premature_opening_evaluable_count: int = 0
    premature_opening_count: int = 0
    premature_opening_rate: float | None = None
    premature_opening_ci95: tuple[float, float] | None = None

    mean_warning_lead_time_s: float | None = None
    mean_excess_closed_s: float | None = None
    mean_clearance_latency_s: float | None = None

    fault_event_count: int = 0
    no_train_events: int = 0
    false_alarm_count: int = 0
    false_alarm_evaluable_count: int = 0
    false_alarm_ci95: tuple[float, float] | None = None
    # Raw no-train nuisance totals. Deliberately no per-hour rate: the documented
    # protocol allows only a clearly labelled exploratory extrapolation.
    false_alarm_blocked_seconds: float | None = None
    false_alarm_closure_episodes: int | None = None
    false_alarm_exposure_s: float | None = None
    engine_events: int = 0
    # Mission 5B (DEC-B04): the two remaining partition buckets, so that
    # total_events == eligible_events + no_train_events + engine_events
    #               + unverified_ground_truth_count + excluded_train_events_count.
    # Reporting only: no metric denominator uses them.
    unverified_ground_truth_count: int = 0
    excluded_train_events_count: int = 0
    # Window under which premature opening was computed; ``"undecided"`` => not computed.
    premature_opening_definition: str = "undecided"
    never_protected_evaluable_count: int = 0
    never_protected_count: int = 0
    # Mission 5A (RD-016): M4 outcomes kept distinct. ``premature_opening_evaluable_count`` is the
    # M4 denominator; ``m4_no_violation_count`` + ``premature_opening_count`` partition it.
    m4_no_violation_count: int = 0
    m4_not_evaluable_count: int = 0
    m4_not_evaluable_reasons: dict[str, int] = field(default_factory=dict)
    # Mission 5A (RD-021): events that gave too little physical lead-in are not missed trains.
    missed_train_insufficient_lead_in_count: int = 0
    missed_train_screen_excluded_count: int = 0
    # metric -> [{"event_id", "reason"}] for eligible events the metric excluded.
    exclusions: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    single_events: list[SingleEventEvaluation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_events": self.total_events,
            "eligible_events": self.eligible_events,
            "missed_train_evaluable_count": self.missed_train_evaluable_count,
            "missed_train_count": self.missed_train_count,
            "missed_train_rate": self.missed_train_rate,
            "missed_train_ci95": (
                list(self.missed_train_ci95)
                if self.missed_train_ci95 is not None
                else "not_evaluable"
            ),
            "premature_opening_definition": self.premature_opening_definition,
            "never_protected_evaluable_count": self.never_protected_evaluable_count,
            "never_protected_count": self.never_protected_count,
            "m4_no_violation_count": self.m4_no_violation_count,
            "m4_not_evaluable_count": self.m4_not_evaluable_count,
            "m4_not_evaluable_reasons": dict(sorted(self.m4_not_evaluable_reasons.items())),
            "missed_train_insufficient_lead_in_count": self.missed_train_insufficient_lead_in_count,
            "missed_train_screen_excluded_count": self.missed_train_screen_excluded_count,
            "premature_opening_evaluable_count": self.premature_opening_evaluable_count,
            "premature_opening_count": self.premature_opening_count,
            "premature_opening_rate": self.premature_opening_rate,
            "premature_opening_ci95": (
                list(self.premature_opening_ci95)
                if self.premature_opening_ci95 is not None
                else "not_evaluable"
            ),
            "mean_warning_lead_time_s": self.mean_warning_lead_time_s,
            "mean_excess_closed_s": self.mean_excess_closed_s,
            "mean_clearance_latency_s": self.mean_clearance_latency_s,
            "fault_event_count": self.fault_event_count,
            "no_train_events": self.no_train_events,
            "false_alarm_count": self.false_alarm_count,
            "false_alarm_evaluable_count": self.false_alarm_evaluable_count,
            "false_alarm_ci95": (
                list(self.false_alarm_ci95)
                if self.false_alarm_ci95 is not None
                else "not_evaluable"
            ),
            "false_alarm_blocked_seconds": self.false_alarm_blocked_seconds,
            "false_alarm_closure_episodes": self.false_alarm_closure_episodes,
            "false_alarm_exposure_s": self.false_alarm_exposure_s,
            "false_alarm_hourly_rate": "not_reported_by_protocol",
            "exclusions": {
                metric: [dict(item) for item in items]
                for metric, items in sorted(self.exclusions.items())
            },
            "engine_events": self.engine_events,
            "unverified_ground_truth_count": self.unverified_ground_truth_count,
            "excluded_train_events_count": self.excluded_train_events_count,
        }


class EventMetricsCalculator:
    """Calculates single-event and cohort-level railway crossing safety metrics."""

    @staticmethod
    def evaluate_run(
        sim_result: SimulationRunResult,
        entry_time_s: float | None = None,
        clearance_time_s: float | None = None,
        has_train_ground_truth: bool | None = True,
        exclusion_reasons: dict[str, str] | None = None,
        premature_opening_window: str | None = None,
        *,
        evaluable: bool = True,
        ground_truth_status: str | None = None,
        cohort: str | None = None,
        lead_in_min_block_latency_s: float | None = None,
        lead_in_latency_source: str | None = None,
        first_visible_time_s: float | None = None,
        first_visible_left_censored: bool = False,
    ) -> SingleEventEvaluation:
        """Evaluate safety metrics on a completed simulation replay.

        ``premature_opening_window`` has no default: the definition is an open researcher
        decision (docs/PREMATURE_OPENING_DECISION_EVIDENCE.md). With ``None`` the premature
        opening metric is **not computed** and is reported as excluded for that reason.
        Only windows in ``IMPLEMENTED_PREMATURE_WINDOWS`` are accepted.
        """
        reasons = dict(exclusion_reasons or {})
        if premature_opening_window is not None and (
            premature_opening_window not in IMPLEMENTED_PREMATURE_WINDOWS
        ):
            raise ValueError(
                f"premature_opening_window {premature_opening_window!r} is not implemented; "
                f"implemented: {sorted(IMPLEMENTED_PREMATURE_WINDOWS)}"
            )
        event_id = sim_result.event_id
        scenario = sim_result.scenario_name
        try:
            resolved_cohort: str | None = resolve_event_cohort(event_id, cohort)
        except UnresolvedCohortError:
            # Mission 5A.1: an unannotated event whose cohort cannot be established is recorded as
            # a non-evaluable ``ground_truth_*`` record (it never enters any denominator, as before
            # Mission 5A).  Any record that could be evaluated still fails closed.
            if has_train_ground_truth is not None and (
                ground_truth_status not in UNVERIFIED_GROUND_TRUTH_STATUSES
            ):
                raise
            resolved_cohort = None
        # Mission 5A.1: the cohort must agree with the routing flags; a contradiction would
        # silently pool an event into the wrong denominator.
        if resolved_cohort == "train_events" and has_train_ground_truth is False:
            raise UnqualifiedEventIdError(
                f"{event_id!r} is a train_events event but has_train_ground_truth=False"
            )
        if resolved_cohort == "no_train_events" and has_train_ground_truth is True:
            raise UnqualifiedEventIdError(
                f"{event_id!r} is a no_train_events event but has_train_ground_truth=True"
            )
        if ground_truth_status == "engine" and resolved_cohort != "engine_events":
            raise UnqualifiedEventIdError(
                f"{event_id!r} has ground_truth_status='engine' but cohort {resolved_cohort!r}"
            )

        for name, value in (
            ("entry_time_s", entry_time_s),
            ("clearance_time_s", clearance_time_s),
            ("total_duration_s", sim_result.total_duration_s),
            ("closed_duration_s", sim_result.closed_duration_s),
            ("warning_lead_time_s", sim_result.warning_lead_time_s),
        ):
            if value is not None and (not math.isfinite(value) or value < 0.0):
                raise ValueError(f"{name} must be finite and nonnegative")
        if entry_time_s is not None and clearance_time_s is not None:
            if normalize_timestamp(clearance_time_s) <= normalize_timestamp(entry_time_s):
                raise ValueError("clearance_time_s must be after entry_time_s")
        if sim_result.closed_duration_s > sim_result.total_duration_s:
            raise ValueError("closed_duration_s cannot exceed total_duration_s")
        _validated_replay_timestamps(sim_result)

        is_engine = (
            resolved_cohort == "engine_events"
            or cohort == "engine_events"
            or ground_truth_status == "engine"
            or str(event_id).startswith("engine_events/")
        )
        if is_engine:
            return SingleEventEvaluation(
                event_id=event_id,
                scenario_name=scenario,
                has_train_ground_truth=False,
                missed_train=False,
                premature_opening=None,
                total_closed_s=sim_result.closed_duration_s,
                fault_occurred=sim_result.fault_occurred,
                evaluable=False,
                exclusion_reasons=reasons,
                notes="engine_event_excluded",
                blocked_seconds=sim_result.closed_duration_s,
                closure_episodes=_closure_episodes(sim_result),
                exposure_s=sim_result.total_duration_s,
                cohort=resolved_cohort,
            )

        if (
            has_train_ground_truth is None
            or ground_truth_status in UNVERIFIED_GROUND_TRUTH_STATUSES
        ):
            status_tag = ground_truth_status or "missing"
            if not reasons:
                reasons = {"ground_truth": status_tag}
            return SingleEventEvaluation(
                event_id=event_id,
                scenario_name=scenario,
                has_train_ground_truth=False,
                missed_train=None,
                premature_opening=None,
                total_closed_s=sim_result.closed_duration_s,
                fault_occurred=sim_result.fault_occurred,
                evaluable=False,
                exclusion_reasons=reasons,
                notes=f"ground_truth_{status_tag}",
                blocked_seconds=sim_result.closed_duration_s,
                closure_episodes=_closure_episodes(sim_result),
                exposure_s=sim_result.total_duration_s,
                cohort=resolved_cohort,
            )

        if not has_train_ground_truth:
            # False alarm test scenario (confirmed no-train negative control)
            actuated = sim_result.closed_duration_s > 0.0
            return SingleEventEvaluation(
                event_id=event_id,
                scenario_name=scenario,
                has_train_ground_truth=False,
                missed_train=False,
                premature_opening=None,
                total_closed_s=sim_result.closed_duration_s,
                fault_occurred=sim_result.fault_occurred,
                evaluable=evaluable,
                exclusion_reasons=reasons,
                notes=(
                    ("false_alarm_evaluation" if actuated else "no_false_alarm")
                    if evaluable
                    else "excluded_no_train_event"
                ),
                blocked_seconds=sim_result.closed_duration_s,
                closure_episodes=_closure_episodes(sim_result),
                exposure_s=sim_result.total_duration_s,
                cohort=resolved_cohort,
            )

        # 1. Missed train evaluation
        # Train entered crossing but barrier arm was not blocking traffic (angle > 45°)
        missed: bool | None = None
        if entry_time_s is not None:
            # Find closest simulation step at entry_time_s (both sides on the one-microsecond grid)
            entry_n = normalize_timestamp(entry_time_s)

            def distance_to_entry(item) -> float:
                return normalize_timestamp(abs(normalize_timestamp(item.timestamp_s) - entry_n))

            steps_at_entry = [s for s in sim_result.steps if distance_to_entry(s) <= 0.25]
            if steps_at_entry:
                # Match the observation nearest to the ground-truth boundary,
                # not whichever observation happened to be inserted first.
                step = min(steps_at_entry, key=distance_to_entry)
                missed = not step.is_passage_blocked
        else:
            # A boundary may be approved yet unobservable in this replay;
            # absence of a nearby observation is not evidence of a miss.
            missed = None

        # 1b. Lead-in feasibility screen (RD-021). Off unless a minimum block latency is supplied;
        # an event that gave the policy too little physical warning time is NOT a missed train.
        screen_result: LeadInScreenResult | None = None
        if lead_in_min_block_latency_s is not None:
            screen_result = screen_missed_train_lead_in(
                entry_time_s,
                first_visible_time_s=first_visible_time_s,
                first_visible_left_censored=first_visible_left_censored,
                min_block_latency_s=lead_in_min_block_latency_s,
                min_block_latency_source=lead_in_latency_source or "",
            )
            if not screen_result.evaluable:
                missed = None

        # 2. Premature opening evaluation
        premature: bool | None = None
        never_protected: bool | None = None
        m4_class: M4Classification | None = None
        window_exclusion: dict[str, str] = {}
        if premature_opening_window is None:
            premature = None  # definition undecided: never computed by default
            window_exclusion = {"premature_opening": PREMATURE_OPENING_UNDECIDED}
        elif premature_opening_window == M4_WINDOW:
            m4_class = classify_m4(sim_result, clearance_time_s)
            premature, never_protected = m4_class.premature, m4_class.never_protected
            if m4_class.status == M4_STATUS_NEVER_PROTECTED:
                window_exclusion = {
                    "premature_opening": "never_protected_before_T4 (M5): barrier never "
                    "blocked before tail clearance"
                }
            elif (
                m4_class.status == M4_STATUS_NOT_EVALUABLE
                and m4_class.reason != M4_REASON_T4_MISSING
            ):
                # Incomplete replay evidence: named, never silently safe and never M5.
                window_exclusion = {"premature_opening": str(m4_class.reason)}
        elif clearance_time_s is not None and entry_time_s is not None:
            premature = sim_result.premature_opening_detected
        else:
            premature = None  # not evaluable

        # 3. Warning lead time
        lead_time = sim_result.warning_lead_time_s if entry_time_s is not None else None

        # 4. Excess closed duration
        excess_closed: float | None = None
        if (
            entry_time_s is not None
            and clearance_time_s is not None
            and clearance_time_s > entry_time_s
        ):
            passage_duration = clearance_time_s - entry_time_s
            excess_closed = max(0.0, sim_result.closed_duration_s - passage_duration)

        # 5. Clearance verification latency
        clearance_latency: float | None = None
        if clearance_time_s is not None:
            # Time from ground-truth clearance until gate started opening
            clearance_n = normalize_timestamp(clearance_time_s)
            open_steps = [
                s
                for s in sim_result.steps
                if normalize_timestamp(s.timestamp_s) >= clearance_n
                and s.crossing_state in ("GATE_OPENING", "CROSSING_CLEAR")
            ]
            if open_steps:
                clearance_latency = max(
                    0.0, normalize_timestamp(open_steps[0].timestamp_s - clearance_time_s)
                )

        return SingleEventEvaluation(
            event_id=event_id,
            scenario_name=scenario,
            has_train_ground_truth=True,
            missed_train=missed if evaluable else None,
            premature_opening=premature if evaluable else None,
            warning_lead_time_s=lead_time if evaluable else None,
            excess_closed_duration_s=excess_closed if evaluable else None,
            clearance_latency_s=clearance_latency if evaluable else None,
            total_closed_s=sim_result.closed_duration_s,
            fault_occurred=sim_result.fault_occurred,
            evaluable=evaluable,
            exclusion_reasons=reasons,
            notes="" if evaluable else "excluded_train_event",
            premature_opening_window=premature_opening_window,
            metric_exclusions={
                **window_exclusion,
                **(
                    {"missed_train": str(screen_result.reason)}
                    if screen_result is not None and not screen_result.evaluable
                    else {}
                ),
            },
            never_protected=never_protected if evaluable else None,
            # DEC-B02: an unevaluable record carries no M4 verdict, so it cannot claim "EVALUABLE".
            m4_status=m4_class.status if m4_class is not None and evaluable else None,
            m4_reason=m4_class.reason if m4_class is not None and evaluable else None,
            m4_replay_complete=(
                m4_class.replay_complete if m4_class is not None and evaluable else None
            ),
            missed_train_screen=(
                screen_result.outcome if screen_result is not None else SCREEN_NOT_APPLIED
            ),
            lead_in_available_s=(
                screen_result.available_lead_in_s if screen_result is not None else None
            ),
            cohort=resolved_cohort,
        )

    @classmethod
    def aggregate_cohort(
        cls, evaluations: list[SingleEventEvaluation]
    ) -> CohortEvaluationSummary:
        """Aggregate a cohort of event evaluations into summary metrics and confidence intervals."""
        summary = CohortEvaluationSummary(
            total_events=len(evaluations), single_events=evaluations
        )
        if not evaluations:
            return summary
        event_ids = [evaluation.event_id for evaluation in evaluations]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("cohort evaluations must contain unique event IDs")
        # A record's cohort field and its cohort-qualified id (if any) must agree, so the
        # (cohort, event_id) identity is unambiguous (DEC-B03).  Bare ids stay rejected above.
        for evaluation in evaluations:
            prefix = str(evaluation.event_id).partition("/")[0]
            if (
                evaluation.cohort is not None
                and "/" in str(evaluation.event_id)
                and prefix != evaluation.cohort
            ):
                raise ValueError(
                    f"event {evaluation.event_id!r} contradicts its cohort {evaluation.cohort!r}"
                )

        def _is_engine(e: SingleEventEvaluation) -> bool:
            return e.notes == "engine_event_excluded" or str(e.event_id).startswith(
                "engine_events/"
            )

        def _is_unverified_gt(e: SingleEventEvaluation) -> bool:
            return str(e.notes).startswith("ground_truth_")

        # Only the explicitly declared no-train cohort is a false-alarm
        # denominator. Engine-only records and missing/unknown ground-truth
        # records are neither train nor no-train controls and must not leak
        # into either denominator.
        no_train = [
            e
            for e in evaluations
            if not e.has_train_ground_truth
            and not _is_engine(e)
            and not _is_unverified_gt(e)
        ]
        summary.no_train_events = len(no_train)
        summary.engine_events = sum(1 for e in evaluations if _is_engine(e))
        # Partition buckets (engine > unverified > no-train > train); reporting only.
        summary.unverified_ground_truth_count = sum(
            1 for e in evaluations if not _is_engine(e) and _is_unverified_gt(e)
        )
        summary.excluded_train_events_count = sum(
            1
            for e in evaluations
            if e.has_train_ground_truth
            and not e.evaluable
            and not _is_engine(e)
            and not _is_unverified_gt(e)
        )
        false_alarm = [e for e in no_train if e.evaluable]
        summary.false_alarm_evaluable_count = len(false_alarm)
        summary.false_alarm_count = sum(
            1 for e in false_alarm if e.notes == "false_alarm_evaluation"
        )
        if false_alarm:
            summary.false_alarm_ci95 = wilson_score_interval(
                summary.false_alarm_count, len(false_alarm)
            )
            summary.false_alarm_blocked_seconds = sum(
                e.blocked_seconds or 0.0 for e in false_alarm
            )
            summary.false_alarm_closure_episodes = sum(
                e.closure_episodes or 0 for e in false_alarm
            )
            summary.false_alarm_exposure_s = sum(e.exposure_s or 0.0 for e in false_alarm)
        eligible = [
            e
            for e in evaluations
            if e.evaluable
            and e.has_train_ground_truth
            and not _is_engine(e)
            and not _is_unverified_gt(e)
        ]
        summary.eligible_events = len(eligible)
        if eligible:
            missed_evaluable = [e for e in eligible if e.missed_train is not None]
            summary.missed_train_evaluable_count = len(missed_evaluable)
            if missed_evaluable:
                missed_count = sum(1 for e in missed_evaluable if e.missed_train)
                summary.missed_train_count = missed_count
                summary.missed_train_rate = missed_count / len(missed_evaluable)
                summary.missed_train_ci95 = wilson_score_interval(
                    missed_count, len(missed_evaluable)
                )
            else:
                summary.missed_train_count = 0
                summary.missed_train_rate = None
                summary.missed_train_ci95 = None

            # Premature opening
            premature_evaluable = [
                e for e in eligible if e.premature_opening is not None
            ]
            summary.premature_opening_evaluable_count = len(premature_evaluable)
            if premature_evaluable:
                prem_count = sum(1 for e in premature_evaluable if e.premature_opening)
                summary.premature_opening_count = prem_count
                summary.premature_opening_rate = prem_count / len(premature_evaluable)
                summary.premature_opening_ci95 = wilson_score_interval(
                    prem_count, len(premature_evaluable)
                )

            # Continuous metrics
            lead_times = [
                e.warning_lead_time_s
                for e in eligible
                if e.warning_lead_time_s is not None
            ]
            if lead_times:
                summary.mean_warning_lead_time_s = float(
                    sum(lead_times) / len(lead_times)
                )

            excess_times = [
                e.excess_closed_duration_s
                for e in eligible
                if e.excess_closed_duration_s is not None
            ]
            if excess_times:
                summary.mean_excess_closed_s = float(
                    sum(excess_times) / len(excess_times)
                )

            latency_times = [
                e.clearance_latency_s
                for e in eligible
                if e.clearance_latency_s is not None
            ]
            if latency_times:
                summary.mean_clearance_latency_s = float(
                    sum(latency_times) / len(latency_times)
                )

        windows = {e.premature_opening_window for e in eligible}
        if len(windows) > 1:
            raise ValueError(f"cohort mixes premature-opening windows: {sorted(map(str, windows))}")
        only = next(iter(windows), None)
        summary.premature_opening_definition = only if only is not None else "undecided"
        protected_known = [e for e in eligible if e.never_protected is not None]
        summary.never_protected_evaluable_count = len(protected_known)
        summary.never_protected_count = sum(1 for e in protected_known if e.never_protected)
        summary.m4_no_violation_count = sum(
            1
            for e in eligible
            if e.m4_status == M4_STATUS_EVALUABLE and e.premature_opening is False
        )
        m4_unevaluable = [e for e in eligible if e.m4_status == M4_STATUS_NOT_EVALUABLE]
        summary.m4_not_evaluable_count = len(m4_unevaluable)
        for evaluation in m4_unevaluable:
            key = str(evaluation.m4_reason)
            summary.m4_not_evaluable_reasons[key] = summary.m4_not_evaluable_reasons.get(key, 0) + 1
        summary.missed_train_insufficient_lead_in_count = sum(
            1 for e in eligible if e.missed_train_screen == SCREEN_INSUFFICIENT_LEAD_IN
        )
        summary.missed_train_screen_excluded_count = sum(
            1 for e in eligible if e.missed_train_screen in SCREEN_EXCLUDING_OUTCOMES
        )
        summary.exclusions = cls._exclusions(eligible)
        summary.fault_event_count = sum(1 for e in evaluations if e.fault_occurred)
        return summary

    # Metric -> boundaries it requires (protocol v9 section 5.2 / 5.3).
    REQUIRED_BOUNDARIES: ClassVar[dict[str, tuple[str, ...]]] = {
        "missed_train": ("T1_danger_zone_entry",),
        "premature_opening": ("T1_danger_zone_entry", "T4_tail_clearance"),
        "warning_lead_time": ("T1_danger_zone_entry",),
        "excess_closed_duration": ("T1_danger_zone_entry", "T4_tail_clearance"),
        "clearance_latency": ("T4_tail_clearance",),
    }
    _ATTRIBUTES: ClassVar[dict[str, str]] = {
        "missed_train": "missed_train",
        "premature_opening": "premature_opening",
        "warning_lead_time": "warning_lead_time_s",
        "excess_closed_duration": "excess_closed_duration_s",
        "clearance_latency": "clearance_latency_s",
    }

    @classmethod
    def _exclusions(
        cls, eligible: list[SingleEventEvaluation]
    ) -> dict[str, list[dict[str, str]]]:
        """List every eligible event a metric could not use, with the reason."""
        out: dict[str, list[dict[str, str]]] = {}
        for metric, attribute in cls._ATTRIBUTES.items():
            for evaluation in eligible:
                if getattr(evaluation, attribute) is not None:
                    continue
                missing = [
                    f"{name}:{evaluation.exclusion_reasons[name]}"
                    for name in (
                        premature_required_boundaries(evaluation.premature_opening_window)
                        if metric == "premature_opening"
                        else cls.REQUIRED_BOUNDARIES[metric]
                    )
                    if name in evaluation.exclusion_reasons
                ]
                reason = evaluation.metric_exclusions.get(metric) or (
                    ", ".join(missing) if missing else "no_usable_replay_observation"
                )
                out.setdefault(metric, []).append(
                    {"event_id": evaluation.event_id, "reason": reason}
                )
        return out


@dataclass(frozen=True)
class DescriptiveMetricRow:
    """One camera-local finite-cohort observation; no authority implied by a row."""

    event_key: str
    camera: str
    condition: str
    metric: str
    value: bool | int | float | None
    exclusion_reason: str | None = None
    provenance: str = ""


def summarize_descriptive_rows(rows: tuple[DescriptiveMetricRow, ...]) -> tuple[dict, ...]:
    """Explicit per-metric denominators/reasons, without CI or cross-camera pooling.

    Engine and no-train cohorts remain separate. Missing/censored points remain
    excluded, not zero. M5 is an integer failure indicator, not vehicle intrusion.
    This pure reporting function loads no results and performs no evaluation.
    """
    from collections import Counter
    from statistics import median

    if type(rows) is not tuple:
        raise ValueError("immutable reporting rows required")
    groups: dict[tuple, list] = {}
    seen: set[tuple] = set()
    for row in rows:
        if type(row) is not DescriptiveMetricRow:
            raise ValueError("typed metric row required")
        parts = row.event_key.split("/")
        if (len(parts) != 2 or parts[0] not in KNOWN_COHORTS
                or not parts[1].startswith("event_") or not parts[1][6:].isdigit()
                or row.camera not in ("front", "back") or not row.condition
                or not row.provenance):
            raise ValueError("qualified event/camera/condition/provenance required")
        if row.metric not in ("M4", "M5", "MTR", "WLT", "CLEARANCE", "OCCUPANCY"):
            raise ValueError("unknown metric")
        key = (parts[0], row.camera, row.condition, row.metric)
        identity = (row.event_key, *key[1:])
        if identity in seen:
            raise ValueError("duplicate event in metric denominator")
        seen.add(identity)
        if row.value is None:
            if not row.exclusion_reason:
                raise ValueError("missing point must state exclusion reason")
        else:
            if row.exclusion_reason is not None:
                raise ValueError("excluded point cannot enter denominator")
            if row.metric == "M5":
                if type(row.value) is not int or row.value not in (0, 1):
                    raise ValueError("M5 must be exact integer0/1")
            elif row.metric in ("M4", "MTR"):
                if type(row.value) is not bool:
                    raise ValueError("binary outcome must be boolean")
            elif type(row.value) not in (int, float) or not math.isfinite(row.value):
                raise ValueError("finite continuous value or explicit exclusion required")
        groups.setdefault(key, []).append(row)
    result = []
    for (cohort, camera, condition, metric), members in sorted(groups.items()):
        reasons: Counter[str] = Counter()
        values = []
        for row in members:
            if cohort != "train_events" and metric in ("M4", "M5", "OCCUPANCY"):
                reasons["separate_case_or_control_not_train_metric"] += 1
            elif row.value is None:
                reasons[row.exclusion_reason] += 1
            else:
                values.append(row.value)
        binary = metric in ("M4", "M5", "MTR")
        result.append({"cohort": cohort, "camera": camera, "condition": condition,
                       "metric": metric, "observed_rows": len(members),
                       "denominator": len(values),
                       "excluded_by_reason": dict(sorted(reasons.items())),
                       "numerator": sum(int(v) for v in values) if binary else None,
                       "proportion": (sum(int(v) for v in values)/len(values)
                                      if binary and values else None),
                       "median": median(values) if values and not binary else None,
                       "range": (min(values), max(values)) if values and not binary else None,
                       "event_keys": tuple(row.event_key for row in members),
                       "scope": "finite_cohort_descriptive_no_population_inference"})
    return tuple(result)
