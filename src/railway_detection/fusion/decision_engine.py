"""Deterministic multimodal decision engine implementing the safety policy state machine."""

from __future__ import annotations

from typing import Any

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.evidence import DecisionRecord, Modality
from railway_detection.fusion.rules import (
    CrossingState,
    GateState,
    RuleId,
    has_audio_train_presence,
    has_qualified_approach,
    has_qualified_departure,
)
from railway_detection.fusion.source_tracker import SourceTracker
from railway_detection.utils.logging import get_logger

logger = get_logger("fusion.decision_engine")


class MultimodalDecisionEngine:
    """Evaluates MultimodalFrames to make deterministic, safety-critical gate control decisions."""

    def __init__(
        self,
        config: Any | None = None,
        warning_dwell_s: float = 2.0,
        gate_closing_s: float = 3.0,
        gate_opening_s: float = 3.0,
        clearance_dwell_s: float = 3.0,
        approach_threshold: float = 0.35,
        departure_threshold: float = 0.35,
        audio_threshold: float = 0.3700,
        confirm_frames: int = 2,
    ) -> None:
        if config is not None:
            self.warning_dwell_s = float(config.timing.warning_dwell_s)
            self.gate_closing_s = float(config.timing.gate_closing_s)
            self.gate_opening_s = float(config.timing.gate_opening_s)
            self.clearance_dwell_s = float(config.timing.clearance_dwell_s)
            self.approach_threshold = float(config.vision.confidence_threshold_approach)
            self.departure_threshold = float(config.vision.confidence_threshold_departure)
            self.audio_threshold = float(config.audio.operating_threshold)
            self.confirm_frames = int(config.timing.confirm_frames)
            self.source_staleness_s = float(getattr(config.timing, "source_staleness_s", 2.0))
            self.fault_confirm_frames = int(getattr(config.timing, "fault_confirmation_frames", 2))
            self.fault_recovery_hold_s = float(getattr(config.timing, "fault_recovery_hold_s", 3.0))
            self.config = config
        else:
            self.warning_dwell_s = float(warning_dwell_s)
            self.gate_closing_s = float(gate_closing_s)
            self.gate_opening_s = float(gate_opening_s)
            self.clearance_dwell_s = float(clearance_dwell_s)
            self.approach_threshold = float(approach_threshold)
            self.departure_threshold = float(departure_threshold)
            self.audio_threshold = float(audio_threshold)
            self.confirm_frames = int(confirm_frames)
            self.source_staleness_s = 2.0
            self.fault_confirm_frames = 2
            self.fault_recovery_hold_s = 3.0
            self.config = None

        # Internal tracking
        self.current_state: CrossingState = CrossingState.IDLE
        self.current_gate_state: GateState = GateState.OPEN
        self.state_entry_time_s: float = 0.0
        self.last_master_time_s: float = -1.0
        self.consecutive_approach_count: int = 0
        self.consecutive_vision_failure_count: int = 0
        self.consecutive_recovery_count: int = 0
        self.clearance_started_at_s: float | None = None
        self.rear_confirmed_observed: bool = False
        self.fault_entered_from: CrossingState | None = None
        self.train_present_or_approaching: bool = False

        self.source_tracker = SourceTracker(
            default_timeout_s=self.source_staleness_s,
            confirmation_frames=self.confirm_frames,
            recovery_hold_s=self.fault_recovery_hold_s,
        )

    def reset(self, initial_time_s: float = 0.0) -> None:
        """Reset decision engine state."""
        self.current_state = CrossingState.IDLE
        self.current_gate_state = GateState.OPEN
        self.state_entry_time_s = float(initial_time_s)
        self.last_master_time_s = -1.0
        self.consecutive_approach_count = 0
        self.consecutive_vision_failure_count = 0
        self.consecutive_recovery_count = 0
        self.clearance_started_at_s = None
        self.rear_confirmed_observed = False
        self.fault_entered_from = None
        self.train_present_or_approaching = False
        self.source_tracker = SourceTracker(
            default_timeout_s=self.source_staleness_s,
            confirmation_frames=self.confirm_frames,
            recovery_hold_s=self.fault_recovery_hold_s,
        )

    def evaluate_frame(
        self,
        frame: MultimodalFrame,
        scenario_run_id: str = "default_run",
    ) -> DecisionRecord:
        """Process a single MultimodalFrame and determine the resulting state and gate command."""
        t = frame.master_timestamp_s
        prev_state = self.current_state
        prev_gate = self.current_gate_state

        # Check out-of-order timestamp invariant (Rule 8 / Scenario 11)
        if self.last_master_time_s >= 0.0 and t < self.last_master_time_s - 1e-9:
            logger.warning(
                "Out of order timestamp received: %f < %f; ignoring frame for state transition",
                t,
                self.last_master_time_s,
            )
            return self._make_record(
                timestamp_s=t,
                run_id=scenario_run_id,
                prev_s=prev_state,
                next_s=prev_state,
                prev_g=prev_gate,
                next_g=prev_gate,
                rule_id=RuleId.RULE_8_OUT_OF_ORDER_REJECTION.value,
                explanation="Out-of-order timestamp rejected",
                fault_status="out_of_order",
                frame=frame,
                ev_refs=(),
                gate_cmd=prev_gate.value,
            )

        # Duplicate-frame rejection (Rule 10): a second frame delivered at
        # EXACTLY the same master timestamp as the last processed frame must
        # not re-execute state-machine logic. Without this, re-delivery of
        # the same instant (a collector retry, a batch re-ingested twice,
        # or a replayed cache) would double-increment confirmation counters
        # such as consecutive_approach_count and could shave time off, or
        # incorrectly re-stamp, the clearance/warning dwell timers -- the
        # exact "duplicate observations incorrectly satisfying a safety
        # dwell" failure mode this rule exists to prevent. Distinct from
        # out-of-order rejection above (t strictly less than last) because
        # duplicate and disordered inputs have different root causes and
        # should be distinguishable in logs and decision records.
        if self.last_master_time_s >= 0.0 and abs(t - self.last_master_time_s) < 1e-9:
            logger.warning(
                "Duplicate frame timestamp received: %f == %f; ignoring frame for state "
                "transition to prevent double-counting toward confirmation/dwell counters",
                t,
                self.last_master_time_s,
            )
            return self._make_record(
                timestamp_s=t,
                run_id=scenario_run_id,
                prev_s=prev_state,
                next_s=prev_state,
                prev_g=prev_gate,
                next_g=prev_gate,
                rule_id=RuleId.RULE_10_DUPLICATE_FRAME_REJECTION.value,
                explanation="Duplicate frame timestamp rejected",
                fault_status="duplicate_frame",
                frame=frame,
                ev_refs=(),
                gate_cmd=prev_gate.value,
            )

        self.last_master_time_s = t

        # Ingest observations from frame into internal SourceTracker
        for r in frame.vision_records:
            self.source_tracker.record_observation(
                source_id=r.source_id,
                timestamp_s=r.timestamp_s,
                available=r.available,
                detections=r.detections,
                metadata=r.metadata,
            )
        for r in frame.audio_records:
            self.source_tracker.record_observation(
                source_id=r.source_id,
                timestamp_s=r.timestamp_s,
                available=r.available,
                detections=r.detections,
                metadata=r.metadata,
            )

        # Ingest source_availability overrides or explicit registrations from frame
        for src, avail in frame.source_availability.items():
            if src not in self.source_tracker.sources:
                modality = (
                    Modality.AUDIO
                    if ("audio" in src or "mic" in src)
                    else Modality.VISION
                )
                self.source_tracker.register_source(src, modality=modality)
            if not avail:
                self.source_tracker.record_observation(
                    source_id=src,
                    timestamp_s=t,
                    available=False,
                )

        # Check staleness across all known sources at time t
        for src in list(self.source_tracker.sources.keys()):
            self.source_tracker.evaluate_staleness(src, t)

        current_avail = self.source_tracker.get_availability_map(t)
        for src, avail in frame.source_availability.items():
            if not avail:
                current_avail[src] = False
            elif avail:
                current_avail[src] = True

        # Identify vision sources
        vision_sources = [
            src
            for src, status in self.source_tracker.sources.items()
            if status.modality == Modality.VISION
            or "camera" in src
            or "vision" in src
            or "front" in src
            or "rear" in src
        ]
        if not vision_sources:
            vision_sources = [
                src
                for src in frame.source_availability
                if "camera" in src or "vision" in src or "front" in src or "rear" in src
            ]

        has_registered_vision = bool(vision_sources)

        # Departure-camera-specific staleness (fixes an invariant gap found
        # by independent re-derivation: configs/decision_policy_v1.yaml's
        # RULE_5_STALE_SOURCE_ABORT documents "Stale vision data in
        # REAR_CONFIRMED or CROSSING_CLEAR aborts clearance" -- singular,
        # any stale source -- but the pre-existing `all_vision_failed` /
        # `vision_avail` flags below are an OR across every registered
        # vision source, so they only ever trip when EVERY vision source is
        # simultaneously down. A train could be confirmed departed by the
        # rear/departure camera, that SAME camera could then go stale
        # during the clearance dwell, and the dwell would complete anyway
        # as long as an unrelated (e.g. approach) camera stayed healthy --
        # even though the evidence that actually matters for clearance,
        # the departure camera, was no longer being observed. This computes
        # whether specifically a departure-role source (id containing "2",
        # "back", or "rear" -- the same heuristic already used in the
        # TRAIN_DEPARTING branch below) is currently stale or missing,
        # independent of any other camera's health. Does not change the
        # frozen decision policy document; implements it more faithfully.
        departure_sources = [s for s in vision_sources if "2" in s or "back" in s or "rear" in s]
        departure_source_stale = bool(departure_sources) and any(
            not current_avail.get(s, True) for s in departure_sources
        )

        any_vision_frame_avail = any(
            avail
            for src, avail in frame.source_availability.items()
            if (src in vision_sources or "camera" in src or "vision" in src or "front" in src or "rear" in src)
            and avail
        ) or any(r.available for r in frame.vision_records)

        vision_avail = (
            (any_vision_frame_avail or any(current_avail.get(src, False) for src in vision_sources))
            if has_registered_vision
            else True
        )
        all_vision_failed = has_registered_vision and not vision_avail

        fault_status = "none"
        if all_vision_failed:
            fault_status = "all_vision_failed"
            self.consecutive_vision_failure_count += 1
        else:
            self.consecutive_vision_failure_count = 0

        # Evidence presence
        approach_detected = has_qualified_approach(frame, self.approach_threshold)
        departure_detected = has_qualified_departure(frame, self.departure_threshold)
        audio_train_detected = has_audio_train_presence(frame, self.audio_threshold)

        # Evidence references
        ev_refs = []
        for r in frame.vision_records:
            if r.available and r.detections:
                ev_refs.append(f"{r.source_id}:{r.timestamp_s}")
        for r in frame.audio_records:
            if r.available and r.detections:
                ev_refs.append(f"{r.source_id}:{r.timestamp_s}")

        next_state = prev_state
        next_gate = prev_gate
        rule_id = None
        explanation = None

        # Check Fail-safe invariant:
        # 1. If vision fails during clearance or opening, Rule 5 aborts clearance/opening and clamps closed.
        # 2. If vision fails while train approaching/present/departing, Rule 4 clamps closed immediately.
        # 3. If all vision sources fail in IDLE for confirm_frames, Rule 4 clamps closed.
        if all_vision_failed:
            if prev_state in (
                CrossingState.REAR_CONFIRMED,
                CrossingState.CROSSING_CLEAR,
                CrossingState.GATE_OPENING,
            ):
                next_state = CrossingState.FAULT_FAIL_SAFE
                next_gate = GateState.CLOSED
                rule_id = RuleId.RULE_5_STALE_SOURCE_ABORT.value
                explanation = (
                    f"Stale or missing vision source in {prev_state.value}; "
                    "aborting clearance/opening and clamping gate closed"
                )
                self.clearance_started_at_s = None
                self._transition_to(next_state, next_gate, t)
                return self._make_record(
                    timestamp_s=t,
                    run_id=scenario_run_id,
                    prev_s=prev_state,
                    next_s=next_state,
                    prev_g=prev_gate,
                    next_g=next_gate,
                    rule_id=rule_id,
                    explanation=explanation,
                    fault_status=fault_status,
                    frame=frame,
                    ev_refs=tuple(ev_refs),
                    gate_cmd=next_gate.value,
                    source_health=self.source_tracker.get_health_map(t),
                    health_reasons=self.source_tracker.get_reason_map(t),
                    observation_ages=self.source_tracker.get_age_map(t),
                )
            elif prev_state not in (CrossingState.IDLE, CrossingState.FAULT_FAIL_SAFE):
                next_state = CrossingState.FAULT_FAIL_SAFE
                next_gate = GateState.CLOSED
                rule_id = RuleId.RULE_4_FAIL_SAFE_CLAMP.value
                explanation = "All vision sources failed while crossing active; clamping gate closed"
                self._transition_to(next_state, next_gate, t)
                return self._make_record(
                    timestamp_s=t,
                    run_id=scenario_run_id,
                    prev_s=prev_state,
                    next_s=next_state,
                    prev_g=prev_gate,
                    next_g=next_gate,
                    rule_id=rule_id,
                    explanation=explanation,
                    fault_status=fault_status,
                    frame=frame,
                    ev_refs=tuple(ev_refs),
                    gate_cmd=next_gate.value,
                    source_health=self.source_tracker.get_health_map(t),
                    health_reasons=self.source_tracker.get_reason_map(t),
                    observation_ages=self.source_tracker.get_age_map(t),
                )
            elif (
                prev_state == CrossingState.IDLE
                and self.consecutive_vision_failure_count >= self.confirm_frames
            ):
                next_state = CrossingState.FAULT_FAIL_SAFE
                next_gate = GateState.CLOSED
                rule_id = RuleId.RULE_4_FAIL_SAFE_CLAMP.value
                explanation = (
                    f"All vision sources failed in IDLE for "
                    f"{self.consecutive_vision_failure_count} frames; fail-safe clamp closed"
                )
                self._transition_to(next_state, next_gate, t)
                return self._make_record(
                    timestamp_s=t,
                    run_id=scenario_run_id,
                    prev_s=prev_state,
                    next_s=next_state,
                    prev_g=prev_gate,
                    next_g=next_gate,
                    rule_id=rule_id,
                    explanation=explanation,
                    fault_status=fault_status,
                    frame=frame,
                    ev_refs=tuple(ev_refs),
                    gate_cmd=next_gate.value,
                    source_health=self.source_tracker.get_health_map(t),
                    health_reasons=self.source_tracker.get_reason_map(t),
                    observation_ages=self.source_tracker.get_age_map(t),
                )

        # State Machine Transitions
        if prev_state == CrossingState.IDLE:
            if approach_detected:
                self.consecutive_approach_count += 1
                if self.consecutive_approach_count >= self.confirm_frames:
                    next_state = CrossingState.WARNING
                    next_gate = GateState.OPEN  # warning signals start, gate begins closing after warning dwell
                    rule_id = RuleId.RULE_1_APPROACH_TRIGGER.value
                    explanation = f"Qualified approach confirmed over {self.confirm_frames} frames"
                else:
                    next_state = CrossingState.TRAIN_APPROACHING
                    rule_id = RuleId.RULE_1_APPROACH_TRIGGER.value
                    explanation = "Qualified approach detected; awaiting confirmation"
            else:
                self.consecutive_approach_count = 0
                if audio_train_detected:
                    rule_id = RuleId.RULE_2_AUDIO_SUPPORT_ONLY.value
                    explanation = "Audio train noise observed in IDLE; supporting only, no gate actuation"

        elif prev_state == CrossingState.TRAIN_APPROACHING:
            if approach_detected:
                self.consecutive_approach_count += 1
                if self.consecutive_approach_count >= self.confirm_frames:
                    next_state = CrossingState.WARNING
                    rule_id = RuleId.RULE_1_APPROACH_TRIGGER.value
                    explanation = "Approach confirmed; initiating warning phase"
            else:
                self.consecutive_approach_count = 0
                next_state = CrossingState.IDLE
                explanation = "Unconfirmed approach dropped; returning to IDLE"

        elif prev_state == CrossingState.WARNING:
            elapsed = t - self.state_entry_time_s
            if elapsed >= self.warning_dwell_s:
                next_state = CrossingState.GATE_CLOSING
                next_gate = GateState.CLOSING
                explanation = f"Warning dwell of {self.warning_dwell_s}s elapsed; beginning gate closure"

        elif prev_state == CrossingState.GATE_CLOSING:
            elapsed = t - self.state_entry_time_s
            if elapsed >= self.gate_closing_s:
                next_state = CrossingState.TRAIN_PRESENT
                next_gate = GateState.CLOSED
                explanation = f"Gate closing elapsed ({self.gate_closing_s}s); gate fully closed"

        elif prev_state == CrossingState.TRAIN_PRESENT:
            next_gate = GateState.CLOSED
            if approach_detected or departure_detected:
                next_state = CrossingState.CROSSING_OCCUPIED
                explanation = "Train occupancy observed at crossing"

        elif prev_state == CrossingState.CROSSING_OCCUPIED:
            next_gate = GateState.CLOSED
            if departure_detected:
                next_state = CrossingState.TRAIN_DEPARTING
                explanation = "Departure evidence detected on departure camera"

        elif prev_state == CrossingState.TRAIN_DEPARTING:
            next_gate = GateState.CLOSED
            if departure_detected:
                self.rear_confirmed_observed = True
                next_state = CrossingState.REAR_CONFIRMED
                self.clearance_started_at_s = None
                rule_id = RuleId.RULE_3_POSITIVE_CLEARANCE.value
                explanation = "Positive rear clearance evidence confirmed"
            elif not approach_detected and not departure_detected:
                dep_sources = [
                    s for s in vision_sources if "2" in s or "back" in s or "rear" in s
                ]
                if dep_sources and not any(current_avail.get(s, False) for s in dep_sources):
                    rule_id = RuleId.RULE_6_DEGRADED_SOURCE_HOLD.value
                    explanation = (
                        "Departure camera degraded or missing; holding gate closed in TRAIN_DEPARTING"
                    )
                else:
                    rule_id = RuleId.RULE_3_POSITIVE_CLEARANCE.value
                    explanation = (
                        "Train disappearance without positive rear confirmation; gate remains closed"
                    )

        elif prev_state == CrossingState.REAR_CONFIRMED:
            next_gate = GateState.CLOSED
            if approach_detected:
                next_state = CrossingState.TRAIN_PRESENT
                rule_id = RuleId.RULE_7_NEW_TRAIN_INTERRUPT.value
                explanation = (
                    "New train approach detected during rear clearance; returning to TRAIN_PRESENT"
                )
                self.clearance_started_at_s = None
            elif has_registered_vision and (not vision_avail or departure_source_stale):
                next_state = CrossingState.FAULT_FAIL_SAFE
                next_gate = GateState.CLOSED
                rule_id = RuleId.RULE_5_STALE_SOURCE_ABORT.value
                explanation = (
                    "Stale or missing departure vision source during rear clearance dwell; "
                    "aborting clearance and clamping closed"
                    if departure_source_stale and vision_avail
                    else "Stale or missing vision source during rear clearance dwell; "
                    "aborting clearance and clamping closed"
                )
                self.clearance_started_at_s = None
            else:
                if audio_train_detected:
                    rule_id = RuleId.RULE_2_AUDIO_SUPPORT_ONLY.value
                    explanation = "Audio train energy present; delaying clearance dwell"
                    self.clearance_started_at_s = t
                else:
                    if self.clearance_started_at_s is None:
                        self.clearance_started_at_s = t

                    clear_elapsed = t - self.clearance_started_at_s
                    if clear_elapsed >= self.clearance_dwell_s:
                        next_state = CrossingState.CROSSING_CLEAR
                        rule_id = RuleId.RULE_3_POSITIVE_CLEARANCE.value
                        explanation = (
                            f"Clearance dwell of {self.clearance_dwell_s}s satisfied "
                            "with no conflicting evidence"
                        )

        elif prev_state == CrossingState.CROSSING_CLEAR:
            if approach_detected:
                next_state = CrossingState.GATE_CLOSING
                next_gate = GateState.CLOSING
                rule_id = RuleId.RULE_7_NEW_TRAIN_INTERRUPT.value
                explanation = "New train approach detected in CROSSING_CLEAR; aborting opening"
            elif has_registered_vision and (not vision_avail or departure_source_stale):
                next_state = CrossingState.FAULT_FAIL_SAFE
                next_gate = GateState.CLOSED
                rule_id = RuleId.RULE_5_STALE_SOURCE_ABORT.value
                explanation = (
                    "Stale or missing departure vision source in CROSSING_CLEAR; aborting gate opening"
                    if departure_source_stale and vision_avail
                    else "Stale or missing vision source in CROSSING_CLEAR; aborting gate opening"
                )
            else:
                next_state = CrossingState.GATE_OPENING
                next_gate = GateState.OPENING
                explanation = "Clearance verified; initiating gate opening"

        elif prev_state == CrossingState.GATE_OPENING:
            if approach_detected:
                next_state = CrossingState.GATE_CLOSING
                next_gate = GateState.CLOSING
                rule_id = RuleId.RULE_7_NEW_TRAIN_INTERRUPT.value
                explanation = (
                    "New train approach detected while gate opening; aborting to GATE_CLOSING"
                )
            elif has_registered_vision and (not vision_avail or departure_source_stale):
                next_state = CrossingState.FAULT_FAIL_SAFE
                next_gate = GateState.CLOSED
                rule_id = RuleId.RULE_5_STALE_SOURCE_ABORT.value
                explanation = (
                    "Departure vision source lost during gate opening; fail-safe closing gate"
                    if departure_source_stale and vision_avail
                    else "Vision sources lost during gate opening; fail-safe closing gate"
                )
            else:
                elapsed = t - self.state_entry_time_s
                if elapsed >= self.gate_opening_s:
                    next_state = CrossingState.IDLE
                    next_gate = GateState.OPEN
                    explanation = (
                        f"Gate opening elapsed ({self.gate_opening_s}s); crossing returned to IDLE"
                    )

        elif prev_state == CrossingState.FAULT_FAIL_SAFE:
            next_gate = GateState.CLOSED
            if vision_avail and has_registered_vision:
                if approach_detected or departure_detected:
                    next_state = CrossingState.TRAIN_PRESENT
                    explanation = (
                        "Train presence detected while in FAULT_FAIL_SAFE; transitioning to TRAIN_PRESENT"
                    )
                    self.consecutive_recovery_count = 0
                    self.fault_entered_from = None
                elif audio_train_detected:
                    self.consecutive_recovery_count = 0
                    explanation = "Audio train noise observed while in FAULT_FAIL_SAFE; holding closed"
                else:
                    self.consecutive_recovery_count += 1
                    if self.consecutive_recovery_count >= self.confirm_frames:
                        if (
                            self.fault_entered_from == CrossingState.IDLE
                            and not self.train_present_or_approaching
                        ):
                            next_state = CrossingState.IDLE
                            next_gate = GateState.OPEN
                            rule_id = RuleId.RULE_9_SENSOR_RECOVERY.value
                            explanation = (
                                f"All sensors recovered to HEALTHY for "
                                f"{self.consecutive_recovery_count} frames from IDLE fault; restoring crossing to IDLE"
                            )
                        else:
                            # CRITICAL SAFETY INVARIANT: Train was present/approaching before the fault!
                            # Sensor recovery alone MUST NOT establish train clearance or open the gate!
                            next_state = CrossingState.TRAIN_PRESENT
                            next_gate = GateState.CLOSED
                            rule_id = RuleId.RULE_9_SENSOR_RECOVERY.value
                            origin_str = (
                                self.fault_entered_from.value
                                if self.fault_entered_from
                                else "active"
                            )
                            explanation = (
                                f"Sensors recovered after fault during active crossing ({origin_str}); "
                                "holding gate closed in TRAIN_PRESENT awaiting operational departure clearance"
                            )
                        self.consecutive_recovery_count = 0
                        self.fault_entered_from = None
                    else:
                        rule_id = RuleId.RULE_9_SENSOR_RECOVERY.value
                        explanation = (
                            f"Sensors recovering ({self.consecutive_recovery_count}/"
                            f"{self.confirm_frames} frames); maintaining fail-safe clamp"
                        )
            else:
                self.consecutive_recovery_count = 0
                explanation = "System in FAULT_FAIL_SAFE; automatic gate opening prohibited"

        self._transition_to(next_state, next_gate, t)
        return self._make_record(
            timestamp_s=t,
            run_id=scenario_run_id,
            prev_s=prev_state,
            next_s=next_state,
            prev_g=prev_gate,
            next_g=next_gate,
            rule_id=rule_id,
            explanation=explanation,
            fault_status=fault_status,
            frame=frame,
            ev_refs=tuple(ev_refs),
            gate_cmd=next_gate.value,
            source_health=self.source_tracker.get_health_map(t),
            health_reasons=self.source_tracker.get_reason_map(t),
            observation_ages=self.source_tracker.get_age_map(t),
        )

    def _transition_to(
        self, next_state: CrossingState, next_gate: GateState, timestamp_s: float
    ) -> None:
        if next_state != self.current_state:
            if (
                next_state == CrossingState.FAULT_FAIL_SAFE
                and self.fault_entered_from is None
            ):
                self.fault_entered_from = self.current_state
            elif next_state == CrossingState.IDLE:
                self.train_present_or_approaching = False
                self.fault_entered_from = None
            elif next_state in (
                CrossingState.WARNING,
                CrossingState.GATE_CLOSING,
                CrossingState.TRAIN_PRESENT,
                CrossingState.CROSSING_OCCUPIED,
                CrossingState.TRAIN_DEPARTING,
                CrossingState.REAR_CONFIRMED,
                CrossingState.CROSSING_CLEAR,
                CrossingState.GATE_OPENING,
            ):
                self.train_present_or_approaching = True

            self.current_state = next_state
            self.state_entry_time_s = float(timestamp_s)
        self.current_gate_state = next_gate

    def _make_record(
        self,
        timestamp_s: float,
        run_id: str,
        prev_s: CrossingState,
        next_s: CrossingState,
        prev_g: GateState,
        next_g: GateState,
        rule_id: str | None,
        explanation: str | None,
        fault_status: str,
        frame: MultimodalFrame,
        ev_refs: tuple[str, ...],
        gate_cmd: str | None = None,
        source_health: dict[str, str] | None = None,
        health_reasons: dict[str, str] | None = None,
        observation_ages: dict[str, float] | None = None,
    ) -> DecisionRecord:
        s_avail = dict(frame.source_availability)
        s_health = dict(source_health if source_health is not None else frame.source_health)
        h_reasons = dict(health_reasons if health_reasons is not None else frame.health_reasons)
        obs_ages = dict(observation_ages if observation_ages is not None else frame.observation_ages)
        return DecisionRecord(
            timestamp_s=timestamp_s,
            scenario_run_id=run_id,
            previous_state=prev_s.value,
            resulting_state=next_s.value,
            previous_gate_state=prev_g.value,
            resulting_gate_state=next_g.value,
            evidence_references=ev_refs,
            rule_id=rule_id,
            explanation=explanation,
            fault_status=fault_status,
            source_availability=s_avail,
            source_health=s_health,
            health_reasons=h_reasons,
            observation_ages=obs_ages,
            gate_command=gate_cmd if gate_cmd is not None else next_g.value,
        )
