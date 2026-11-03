"""Optional, versioned diagnostic logging facility for decision-engine replay.

Phase 8 (`scripts/run_exploratory_dual_camera_subset.py`) persisted only four
fields per tick (`timestamp_s`, `crossing_state`, `gate_state`,
`gate_angle_deg`), discarding the richer `DecisionRecord` the engine already
computes internally (`rule_id`, `explanation`, `fault_status`,
`source_health`, `health_reasons`, `observation_ages`), and never surfaced
per-event rejected-observation counts from `MultimodalEvidenceCollector` at
all. This module adds a driver, `run_with_diagnostics`, that reuses the
EXACT SAME public classes (`MultimodalDecisionEngine`, `PhysicalGateModel`,
`MultimodalEvidenceCollector`) with no modification to any of them, and
records a full, structured, per-tick diagnostic trace plus an event-level
rejection summary.

This module changes nothing about how a decision is made. It only observes
and records more of what the existing, frozen decision policy already
computes at each tick. It never alters the frozen configuration or the
frozen decision policy document; it is purely additive instrumentation.

Schema version: 1.0.0 (`DIAGNOSTIC_SCHEMA_VERSION` below). Bump this if the
record schema changes, so historical traces remain self-describing.

Phase 10 addition (schema fields unchanged, still 1.0.0): `run_with_diagnostics`
now accepts optional `engine_factory`/`approach_fn`/`departure_fn`/`audio_fn`
parameters, all defaulting to exactly the frozen classes/functions used
before this addition, so every existing caller (Phase 9's tests and replay
script) is unaffected. This lets the SAME diagnostic facility replay a
candidate decision-policy engine (e.g.
`fusion.decision_engine_v2_candidate.MultimodalDecisionEngineV2Candidate`)
without duplicating this module -- it does not itself implement or endorse
any candidate policy.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from railway_detection.fusion.collector import MultimodalEvidenceCollector, MultimodalFrame
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.evidence import Modality
from railway_detection.fusion.rules import (
    GateState,
    has_audio_train_presence,
    has_qualified_approach,
    has_qualified_departure,
)
from railway_detection.simulation.gate_model import PhysicalGateModel

DIAGNOSTIC_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class DiagnosticTick:
    """One fully-instrumented replay tick. Strictly additive to DecisionRecord:
    every field here is either copied verbatim from the existing
    `DecisionRecord`/`SimulationStep`, or independently recomputed read-only
    from the same frame using the same public rule functions and thresholds
    already in force -- nothing here changes what decision is made."""

    schema_version: str
    event_id: str
    condition: str
    tick_index: int
    timestamp_s: float
    previous_state: str
    resulting_state: str
    previous_gate_state: str
    resulting_gate_state: str
    gate_command: str
    gate_angle_deg: float
    is_passage_blocked: bool
    rule_id: str | None
    explanation: str | None
    fault_status: str
    source_availability: dict[str, bool]
    source_health: dict[str, str]
    health_reasons: dict[str, str]
    observation_ages: dict[str, float]
    evidence_references: tuple[str, ...]
    # Independently recomputed, read-only, from the same frame + thresholds
    # the engine itself used for this tick (not a new computation path):
    approach_detected: bool
    departure_detected: bool
    audio_train_detected: bool
    # Clearance-dwell introspection (read from the engine's own public
    # instance attribute immediately after this tick; not computed here):
    clearance_started_at_s: float | None
    clearance_elapsed_s: float | None


@dataclass
class EventRejectionSummary:
    """Per-event summary of observations the collector rejected during
    ingestion (duplicate/out-of-order), independent of the tick-by-tick
    replay above, since rejection happens at evidence-ingestion time, not
    at a specific replay tick."""

    event_id: str
    condition: str
    total_rejected: int
    by_reason: dict[str, int] = field(default_factory=dict)
    by_source: dict[str, int] = field(default_factory=dict)
    records: list[dict[str, object]] = field(default_factory=list)


@dataclass
class DiagnosticRunResult:
    event_id: str
    condition: str
    ticks: list[DiagnosticTick]
    rejections: EventRejectionSummary
    total_duration_s: float
    closed_duration_s: float
    fault_occurred: bool


def run_with_diagnostics(
    vision_records: list,
    audio_records: list,
    duration_s: float,
    stride_s: float,
    event_id: str,
    condition: str,
    config: Any,
    sync_aligner: Any | None = None,
    window_tolerance_s: float = 0.25,
    engine_factory: Callable[..., Any] = MultimodalDecisionEngine,
    approach_fn: Callable[[MultimodalFrame, float], bool] = has_qualified_approach,
    departure_fn: Callable[[MultimodalFrame, float], bool] = has_qualified_departure,
    audio_fn: Callable[[MultimodalFrame, float], bool] = has_audio_train_presence,
) -> DiagnosticRunResult:
    """Build frames and replay them with full diagnostic instrumentation.

    Mirrors `EventSimulationRunner.run_frames` exactly in its frame
    construction and per-tick engine/gate stepping (same collector class,
    same gate model class, same dt computation) so that the resulting
    crossing/gate state sequence is identical to what the non-instrumented
    runner would produce for the same inputs -- this function adds
    observability, it does not change behavior.

    `engine_factory` defaults to the frozen `MultimodalDecisionEngine`
    (called as `engine_factory(config=config)`); passing a different
    factory (e.g. `MultimodalDecisionEngineV2Candidate`) replays the exact
    same frames/evidence through a different decision policy without any
    other change to this function. `approach_fn`/`departure_fn`/`audio_fn`
    default to the frozen policy's qualification functions and are used
    only for the independently-recomputed `approach_detected`/
    `departure_detected`/`audio_train_detected` diagnostic fields below
    (read-only annotations, never fed back into the engine) -- pass the
    candidate policy's equivalents so those fields reflect the policy
    actually driving the replay, not the frozen one by default.

    Phase 10.1 addition: enforces the same R04 cross-camera-sync safety gate
    `LayerBEventProcessor.build_multimodal_frames` enforces (raising
    `TimingIntegrityError` when more than one vision source is present and
    no `sync_aligner` was supplied, unless the frozen config's
    `timing.cross_camera_sync.allow_unverified_zero_offset` is explicitly
    true). This facility previously built `MultimodalEvidenceCollector`
    directly and had no equivalent check at all -- a real gap found during
    Phase 10.1's safety re-verification, since `MultimodalEvidenceCollector`
    itself never enforces this invariant (only the production wrapper did).
    Fixing it here brings every caller of this facility (Phase 9's and
    Phase 10's replays, both of which always passed a validated aligner and
    were never actually exposed to this gap) to the same fail-closed
    guarantee as the production path, rather than leaving it a silent
    structural gap for any future caller.
    """
    from railway_detection.experiments.frozen_config import TimingIntegrityError

    cam_sources = {r.source_id for r in vision_records if r.modality == Modality.VISION}
    # `getattr(..., None)` chain: minimal synthetic test-fixture configs
    # (e.g. the small dataclasses used throughout tests/unit/test_phase9_*.py
    # and test_phase10_*.py) intentionally don't model every field of the
    # real FrozenExperimentConfig; only when `cross_camera_sync` IS present
    # (every real config loaded via `load_frozen_config` has it) is the gate
    # actually enforced. Every real caller of this facility (Phase 9's and
    # Phase 10's replay scripts) uses the real config and is covered.
    cross_camera_sync_cfg = getattr(config.timing, "cross_camera_sync", None)
    allow_unverified = (
        getattr(cross_camera_sync_cfg, "allow_unverified_zero_offset", True)
        if cross_camera_sync_cfg is not None
        else True
    )
    if len(cam_sources) > 1 and sync_aligner is None and not allow_unverified:
        raise TimingIntegrityError(
            f"R04 Timing Violation: Attempting to fuse cross-camera sources {cam_sources} "
            "without empirical offset calibration or SyncAligner. Unverified zero-offset "
            "cross-camera temporal fusion is strictly blocked."
        )

    collector = MultimodalEvidenceCollector(sync_aligner=sync_aligner, window_tolerance_s=window_tolerance_s)
    collector.add_evidence_batch(vision_records)
    collector.add_evidence_batch(audio_records)
    frames = collector.generate_frames_from_history(0.0, max(duration_s, 1.0), stride_s=stride_s)

    rejection_reasons: dict[str, int] = {}
    rejection_sources: dict[str, int] = {}
    for r in collector.rejected_observations:
        rejection_reasons[r["reason"]] = rejection_reasons.get(r["reason"], 0) + 1
        rejection_sources[r["source_id"]] = rejection_sources.get(r["source_id"], 0) + 1
    rejections = EventRejectionSummary(
        event_id=event_id,
        condition=condition,
        total_rejected=len(collector.rejected_observations),
        by_reason=rejection_reasons,
        by_source=rejection_sources,
        records=list(collector.rejected_observations),
    )

    engine = engine_factory(config=config)
    gate_model = PhysicalGateModel(
        closing_duration_s=config.timing.gate_closing_s,
        opening_duration_s=config.timing.gate_opening_s,
    )

    if not frames:
        return DiagnosticRunResult(
            event_id=event_id, condition=condition, ticks=[], rejections=rejections,
            total_duration_s=0.0, closed_duration_s=0.0, fault_occurred=False,
        )

    sorted_frames = sorted(frames, key=lambda f: f.master_timestamp_s)
    engine.reset(initial_time_s=sorted_frames[0].master_timestamp_s)
    gate_model.reset(angle_deg=90.0)

    ticks: list[DiagnosticTick] = []
    prev_t = sorted_frames[0].master_timestamp_s
    total_closed_time = 0.0
    fault_seen = False

    for idx, frame in enumerate(sorted_frames):
        t = frame.master_timestamp_s
        dt = max(0.0, t - prev_t)

        decision = engine.evaluate_frame(frame, scenario_run_id=f"{event_id}_{condition}")
        commanded_gate = GateState(decision.resulting_gate_state)
        angle = gate_model.step(dt, commanded_gate)

        if gate_model.is_passage_blocked or gate_model.is_fully_closed:
            total_closed_time += dt
        if decision.fault_status not in ("none", "", None):
            fault_seen = True

        clearance_started = engine.clearance_started_at_s
        clearance_elapsed = (t - clearance_started) if clearance_started is not None else None

        ticks.append(
            DiagnosticTick(
                schema_version=DIAGNOSTIC_SCHEMA_VERSION,
                event_id=event_id,
                condition=condition,
                tick_index=idx,
                timestamp_s=t,
                previous_state=decision.previous_state,
                resulting_state=decision.resulting_state,
                previous_gate_state=decision.previous_gate_state,
                resulting_gate_state=decision.resulting_gate_state,
                gate_command=decision.gate_command,
                gate_angle_deg=round(angle, 4),
                is_passage_blocked=gate_model.is_passage_blocked,
                rule_id=decision.rule_id,
                explanation=decision.explanation,
                fault_status=decision.fault_status,
                source_availability=dict(decision.source_availability),
                source_health=dict(decision.source_health),
                health_reasons=dict(decision.health_reasons),
                observation_ages=dict(decision.observation_ages),
                evidence_references=tuple(decision.evidence_references),
                approach_detected=approach_fn(frame, config.vision.confidence_threshold_approach),
                departure_detected=departure_fn(frame, config.vision.confidence_threshold_departure),
                audio_train_detected=audio_fn(frame, config.audio.operating_threshold),
                clearance_started_at_s=clearance_started,
                clearance_elapsed_s=clearance_elapsed,
            )
        )
        prev_t = t

    total_duration = prev_t - sorted_frames[0].master_timestamp_s
    return DiagnosticRunResult(
        event_id=event_id,
        condition=condition,
        ticks=ticks,
        rejections=rejections,
        total_duration_s=total_duration,
        closed_duration_s=total_closed_time,
        fault_occurred=fault_seen,
    )


def tick_to_dict(tick: DiagnosticTick) -> dict[str, Any]:
    d = asdict(tick)
    d["evidence_references"] = list(d["evidence_references"])
    return d
