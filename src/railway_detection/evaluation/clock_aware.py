"""Clock-aware evaluation of real-event replays.

Ground-truth boundaries are annotated on a specific camera clock (entry T1 on the
front camera, tail clearance T4 on the back camera). A replay runs on a specific
timeline: the front stream's own clock, the back stream's own clock, or -- only for
events whose synchronization the researcher accepted -- a fused master clock with a
validated per-camera offset.

A boundary may be compared with a replay step only if its camera has a defined
offset into that replay's clock. Anything else is reported as a clock mismatch and
the dependent metric is *not evaluable*; no zero offset is ever assumed. In particular,
a metric that needs boundaries from two different camera clocks (e.g. the protocol-v9
premature-opening window [T1, T4)) is computed only on a fused timeline.

Replays run without ground truth. Per-event outcome flags that depend on boundary times
(premature opening, warning lead) are derived here from the recorded steps, using the
same predicate as ``simulation.runner.EventSimulationRunner``.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping
from dataclasses import dataclass, field

from railway_detection.evaluation.ground_truth_loader import ApprovedEventGroundTruth
from railway_detection.evaluation.lead_in_screen import SCREEN_NOT_APPLIED
from railway_detection.evaluation.metrics import (
    M4_STATUS_EVALUABLE,
    M4_STATUS_NEVER_PROTECTED,
    M4_WINDOW,
    PREMATURE_OPENING_UNDECIDED,
    EventMetricsCalculator,
    SingleEventEvaluation,
    premature_required_boundaries,
)
from railway_detection.evaluation.timebase import normalize_timestamp
from railway_detection.fusion.rules import CrossingState, GateState
from railway_detection.simulation.runner import SimulationRunResult

SYSTEM_PRIORITY = ("fused", "front", "back")
ENTRY = "T1_danger_zone_entry"
CLEARANCE = "T4_tail_clearance"
FIRST_VISIBLE = "T0_first_visible"


class ClockModelError(ValueError):
    """The replay clock model and the ground truth cannot be reconciled."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class SystemReplay:
    """One replayed timeline for an event."""

    name: str  # "front" | "back" | "fused"
    # camera -> seconds to add to that camera's local time to get this system's time
    clock_offsets_s: Mapping[str, float]
    result: SimulationRunResult
    details: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class EventReplay:
    event_id: str
    cohort: str
    camera_mode: str
    systems: Mapping[str, SystemReplay]
    provenance: Mapping[str, object] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.systems or set(self.systems) - set(SYSTEM_PRIORITY):
            raise ClockModelError("REPLAY_INVALID", f"{self.event_id}: unknown or no systems")
        if ("fused" in self.systems) != (self.camera_mode == "dual_camera"):
            raise ClockModelError(
                "REPLAY_INVALID", f"{self.event_id}: fused timeline only for dual_camera"
            )
        for system in self.systems.values():
            if system.result.event_id != self.event_id:
                raise ClockModelError(
                    "REPLAY_INVALID", f"{self.event_id}: result bound to {system.result.event_id}"
                )
            if not system.clock_offsets_s or any(
                not math.isfinite(offset) for offset in system.clock_offsets_s.values()
            ):
                raise ClockModelError("REPLAY_INVALID", f"{self.event_id}: bad clock offsets")


def derive_boundary_flags(
    result: SimulationRunResult, entry_s: float | None, clearance_s: float | None
) -> SimulationRunResult:
    """Recompute boundary-dependent flags from recorded steps (mirrors the runner)."""
    premature = False
    if entry_s is not None and clearance_s is not None:
        entry_n, clearance_n = normalize_timestamp(entry_s), normalize_timestamp(clearance_s)
        premature = any(
            entry_n <= normalize_timestamp(step.timestamp_s) < clearance_n
            and GateState(step.gate_state) in (GateState.OPENING, GateState.OPEN)
            and not step.is_passage_blocked
            for step in result.steps
        )
    lead: float | None = None
    if entry_s is not None:
        first_warning = next(
            (
                step.timestamp_s
                for step in result.steps
                if step.crossing_state == CrossingState.WARNING.value
            ),
            None,
        )
        if first_warning is not None:
            lead = max(0.0, normalize_timestamp(entry_s - first_warning))
    return dataclasses.replace(
        result, premature_opening_detected=premature, warning_lead_time_s=lead
    )


@dataclass(frozen=True)
class _SystemEvaluation:
    """One system's evaluation with the boundaries that were mappable onto its clock."""

    entry: float | None  # T1 on this system's clock, or None if its camera has no offset here
    clearance: float | None  # T4 on this system's clock, likewise
    evaluation: SingleEventEvaluation


def _boundary_in_system(
    truth: ApprovedEventGroundTruth, name: str, system: SystemReplay
) -> float | None:
    if name not in truth.observable_boundaries:
        return None
    camera = truth.boundary_cameras.get(name)
    if camera is None:
        raise ClockModelError(
            "GROUND_TRUTH_CAMERA_MISSING",
            f"{truth.event_id}: boundary {name} has no annotation camera; refusing to guess",
        )
    offset = system.clock_offsets_s.get(camera)
    if offset is None:
        return None
    return normalize_timestamp(truth.observable_boundaries[name] + float(offset))


def _state_of(truth: ApprovedEventGroundTruth, name: str) -> str:
    if name in truth.censored_boundaries:
        return "censored"
    if name in truth.uncertain_boundaries:
        return "uncertain"
    return "not_applicable_or_unknown"


def evaluate_event_replay(
    replay: EventReplay,
    truth: ApprovedEventGroundTruth,
    *,
    premature_opening_window: str | None = None,
    lead_in_min_block_latency_s: float | None = None,
    lead_in_latency_source: str | None = None,
) -> SingleEventEvaluation:
    """Evaluate one event across its replay systems without assuming any clock offset.

    Each metric takes its value from the first system (fused, front, back) that has one.  The
    M4/M5 record (premature opening, never-protected, status, reason, completeness) is taken as a
    unit from a system that carries T4 on its clock, and the lead-in screen record from a system
    that carries T1; a system that lacks the boundary only holds a placeholder (``t4_missing``,
    ``t1_missing``) that must not stand in for the real answer.

    The lead-in screen is off unless ``lead_in_min_block_latency_s`` is given (the official runner
    does not give it).  T0 is mapped onto each clock like any other boundary; a T0 that is
    censored, uncertain, unobservable or unmappable makes the event ``lead_in_unverifiable`` --
    it is never assumed to be visible from the replay start.
    """
    replay.validate()
    has_train = truth.cohort == "train_events"
    ordered = [replay.systems[name] for name in SYSTEM_PRIORITY if name in replay.systems]
    infos: list[_SystemEvaluation] = []
    closed: dict[str, float] = {}
    for system in ordered:
        entry = _boundary_in_system(truth, ENTRY, system) if has_train else None
        clearance = _boundary_in_system(truth, CLEARANCE, system) if has_train else None
        if entry is not None and clearance is not None and clearance <= entry:
            raise ClockModelError(
                "CLOCK_ORDER_INVALID",
                f"{replay.event_id}: on the {system.name} timeline T4 ({clearance:.3f}s) is not "
                f"after T1 ({entry:.3f}s)",
            )
        flagged = derive_boundary_flags(system.result, entry, clearance)
        screen_inputs: dict[str, object] = {}
        if has_train and lead_in_min_block_latency_s is not None:
            screen_inputs = {
                "lead_in_min_block_latency_s": lead_in_min_block_latency_s,
                "lead_in_latency_source": lead_in_latency_source,
                "first_visible_time_s": _boundary_in_system(truth, FIRST_VISIBLE, system),
                "first_visible_left_censored": False,
            }
        evaluation = EventMetricsCalculator.evaluate_run(
            flagged,
            entry_time_s=entry,
            clearance_time_s=clearance,
            has_train_ground_truth=has_train,
            premature_opening_window=premature_opening_window,
            cohort=truth.cohort,
            **screen_inputs,
        )
        infos.append(_SystemEvaluation(entry, clearance, evaluation))
        closed[system.name] = system.result.closed_duration_s
    per_system = [info.evaluation for info in infos]

    if not has_train:
        is_engine = truth.cohort == "engine_events"
        actuated = any(item.notes == "false_alarm_evaluation" for item in per_system)
        return SingleEventEvaluation(
            event_id=replay.event_id,
            scenario_name="phase12_official_replay",
            has_train_ground_truth=False,
            missed_train=False,
            premature_opening=None,
            total_closed_s=sum(closed.values()),
            fault_occurred=any(item.fault_occurred for item in per_system),
            evaluable=not is_engine,
            notes=(
                "engine_event_excluded"
                if is_engine
                else ("false_alarm_evaluation" if actuated else "no_false_alarm")
            ),
            blocked_seconds=sum(item.blocked_seconds or 0.0 for item in per_system),
            closure_episodes=sum(item.closure_episodes or 0 for item in per_system),
            exposure_s=sum(item.exposure_s or 0.0 for item in per_system),
            per_system_closed_s=closed,
            cohort=truth.cohort,
        )

    # M4/M5 comes from a T4-bearing system: the first whose classification is definite, else the
    # first T4-bearing one (it carries the NOT_EVALUABLE reason), else -- T4 not mappable anywhere
    # -- the primary system, which carries ``t4_missing``.
    m4_info: _SystemEvaluation | None = None
    if premature_opening_window == M4_WINDOW:
        bearing = [info for info in infos if info.clearance is not None]
        definite = [
            info
            for info in bearing
            if info.evaluation.m4_status in (M4_STATUS_EVALUABLE, M4_STATUS_NEVER_PROTECTED)
        ]
        m4_info = (definite or bearing or infos)[0]
    # The lead-in screen record comes from a T1-bearing system that actually ran the screen.
    screened = [
        info for info in infos if info.evaluation.missed_train_screen != SCREEN_NOT_APPLIED
    ]
    screen_info = ([i for i in screened if i.entry is not None] or screened or [None])[0]

    fields = {
        "missed_train": "missed_train",
        "premature_opening": "premature_opening",
        "warning_lead_time": "warning_lead_time_s",
        "excess_closed_duration": "excess_closed_duration_s",
        "clearance_latency": "clearance_latency_s",
    }
    merged: dict[str, object] = {}
    exclusions: dict[str, str] = {}
    cameras_available = {cam for system in ordered for cam in system.clock_offsets_s}
    for metric, attribute in fields.items():
        if metric == "premature_opening" and m4_info is not None:
            value = m4_info.evaluation.premature_opening
        else:
            value = next(
                (
                    getattr(item, attribute)
                    for item in per_system
                    if getattr(item, attribute) is not None
                ),
                None,
            )
        merged[attribute] = value
        if value is not None:
            continue
        reasons = []
        needed = (
            premature_required_boundaries(premature_opening_window)
            if metric == "premature_opening"
            else EventMetricsCalculator.REQUIRED_BOUNDARIES[metric]
        )
        for name in needed:
            if name not in truth.observable_boundaries:
                reasons.append(f"{name}:{_state_of(truth, name)}")
            elif truth.boundary_cameras[name] not in cameras_available:
                reasons.append(
                    f"{name}:clock_mismatch(annotated on {truth.boundary_cameras[name]}; "
                    f"replay clocks {sorted(cameras_available)})"
                )
        observable = [n for n in needed if n in truth.observable_boundaries]
        if not reasons and len(observable) == len(needed) and len(needed) > 1:
            reasons.append(
                "clock_mismatch(" + " & ".join(
                    f"{n} on {truth.boundary_cameras[n]}" for n in needed
                ) + " share no replay timeline)"
            )
        if metric == "premature_opening" and premature_opening_window is None:
            exclusions[metric] = PREMATURE_OPENING_UNDECIDED
        elif reasons:
            exclusions[metric] = ", ".join(reasons)
        # A named replay-side reason (M5, incomplete replay, lead-in screen) is more specific
        # than a clock reason or the generic "no_usable_replay_observation".
        if metric == "premature_opening" and m4_info is not None:
            named = m4_info.evaluation.metric_exclusions.get("premature_opening")
            if named:
                exclusions[metric] = named
        if (
            metric == "missed_train"
            and value is None
            and screen_info is not None
            and screen_info.entry is not None
        ):
            named = screen_info.evaluation.metric_exclusions.get("missed_train")
            if named:
                exclusions[metric] = named
    primary = per_system[0]
    m4_eval = m4_info.evaluation if m4_info is not None else None
    screen_eval = screen_info.evaluation if screen_info is not None else None
    return SingleEventEvaluation(
        event_id=replay.event_id,
        scenario_name="phase12_official_replay",
        has_train_ground_truth=True,
        missed_train=merged["missed_train"],  # type: ignore[arg-type]
        premature_opening=merged["premature_opening"],  # type: ignore[arg-type]
        warning_lead_time_s=merged["warning_lead_time_s"],  # type: ignore[arg-type]
        excess_closed_duration_s=merged["excess_closed_duration_s"],  # type: ignore[arg-type]
        clearance_latency_s=merged["clearance_latency_s"],  # type: ignore[arg-type]
        total_closed_s=primary.total_closed_s,
        fault_occurred=any(item.fault_occurred for item in per_system),
        evaluable=True,
        metric_exclusions=exclusions,
        per_system_closed_s=closed,
        premature_opening_window=premature_opening_window,
        never_protected=m4_eval.never_protected if m4_eval is not None else None,
        m4_status=m4_eval.m4_status if m4_eval is not None else None,
        m4_reason=m4_eval.m4_reason if m4_eval is not None else None,
        m4_replay_complete=m4_eval.m4_replay_complete if m4_eval is not None else None,
        missed_train_screen=(
            screen_eval.missed_train_screen if screen_eval is not None else SCREEN_NOT_APPLIED
        ),
        lead_in_available_s=screen_eval.lead_in_available_s if screen_eval is not None else None,
        cohort=truth.cohort,
    )
