"""Phase 10 candidate decision engine (policy v2.0.0-candidate).

A separate, versioned engine class implementing the candidate semantics
defined in `fusion/rules_v2_candidate.py`. Does NOT modify, subclass, or
import from `fusion/decision_engine.py` in any way that would affect the
frozen engine's behavior -- it is a standalone class with the same public
interface (`reset`, `evaluate_frame`) so it is a drop-in replacement for
`MultimodalDecisionEngine` wherever a caller (e.g.
`experiments.diagnostic_trace.run_with_diagnostics`) accepts a pluggable
engine factory. `configs/decision_policy_v1.yaml` and
`configs/frozen_experiment_v1.yaml` are read-only inputs (the same
`FrozenExperimentConfig` object the frozen engine uses, for timing/threshold
values only) and are never modified by this module.

Differences from the frozen engine (see `rules_v2_candidate.py`'s module
docstring for the full rationale) are confined to exactly the two mechanisms
Phase 9 identified as the source of the clearance divergence:

1. Departure confirmation (TRAIN_DEPARTING -> REAR_CONFIRMED) now requires
   EITHER an unambiguous "rear" label from a departure-role source, OR
   sustained disappearance (no qualifying detection for `confirm_frames`
   ticks) from an available departure-role source -- or, when no dedicated
   departure-role camera is registered at all (single-camera topology),
   sustained disappearance from the sole camera. Ambiguous "side"/"train"
   labels can no longer, by themselves, confirm departure.

2. The new-train interrupt (RULE_7, scoped to REAR_CONFIRMED/CROSSING_CLEAR/
   GATE_OPENING exactly as in the frozen policy) now requires either an
   unambiguous "front" label, or an ambiguous label that is genuinely
   REAPPEARING after a tracked silence -- continuing, unbroken ambiguous
   detections of the same still-visible train no longer reset the clearance
   dwell at all.

Every other mechanism (out-of-order/duplicate-frame rejection, fail-safe
clamps, degraded-source hold, stale-source abort, sensor recovery, audio
support-only delay, warning/gate-closing/gate-opening dwell timers) is
reused with IDENTICAL logic to the frozen engine, not reinvented, so that
any behavioral difference observed between the two engines is attributable
specifically to the two changes above.
"""

from __future__ import annotations

from typing import Any

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.evidence import DecisionRecord, Modality
from railway_detection.fusion.rules import CrossingState, GateState, has_audio_train_presence
from railway_detection.fusion.rules_v2_candidate import (
    RuleIdV2,
    detection_sources_this_tick,
    has_any_qualifying_detection,
    has_genuinely_new_approach_evidence,
    has_unambiguous_departure_label_from,
    is_departure_role_source,
)
from railway_detection.fusion.source_tracker import SourceTracker
from railway_detection.utils.logging import get_logger

logger = get_logger("fusion.decision_engine_v2_candidate")


class MultimodalDecisionEngineV2Candidate:
    """Candidate-policy state machine. See module docstring for scope."""

    def __init__(self, config: Any) -> None:
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
        # Reuses the frozen config's existing `miss_tolerance_frames` field as
        # the candidate policy's "genuine silence" threshold for distinguishing
        # a reappearing ambiguous detection from a continuing one -- no new
        # configuration field is introduced; this field already exists in
        # configs/frozen_experiment_v1.yaml and is read-only here.
        self.gap_frames_for_new_detection = int(getattr(config.timing, "miss_tolerance_frames", 2))
        self.config = config

        self.current_state: CrossingState = CrossingState.IDLE
        self.current_gate_state: GateState = GateState.OPEN
        self.state_entry_time_s: float = 0.0
        self.last_master_time_s: float = -1.0
        self.consecutive_approach_count: int = 0
        self.consecutive_vision_failure_count: int = 0
        self.consecutive_recovery_count: int = 0
        self.clearance_started_at_s: float | None = None
        self.fault_entered_from: CrossingState | None = None
        self.train_present_or_approaching: bool = False
        self.ticks_since_last_detection: dict[str, int] = {}

        self.source_tracker = SourceTracker(
            default_timeout_s=self.source_staleness_s,
            confirmation_frames=self.confirm_frames,
            recovery_hold_s=self.fault_recovery_hold_s,
        )

    def reset(self, initial_time_s: float = 0.0) -> None:
        self.current_state = CrossingState.IDLE
        self.current_gate_state = GateState.OPEN
        self.state_entry_time_s = float(initial_time_s)
        self.last_master_time_s = -1.0
        self.consecutive_approach_count = 0
        self.consecutive_vision_failure_count = 0
        self.consecutive_recovery_count = 0
        self.clearance_started_at_s = None
        self.fault_entered_from = None
        self.train_present_or_approaching = False
        self.ticks_since_last_detection = {}
        self.source_tracker = SourceTracker(
            default_timeout_s=self.source_staleness_s,
            confirmation_frames=self.confirm_frames,
            recovery_hold_s=self.fault_recovery_hold_s,
        )

    def evaluate_frame(self, frame: MultimodalFrame, scenario_run_id: str = "default_run") -> DecisionRecord:
        t = frame.master_timestamp_s
        prev_state = self.current_state
        prev_gate = self.current_gate_state

        if self.last_master_time_s >= 0.0 and t < self.last_master_time_s - 1e-9:
            return self._make_record(
                t, scenario_run_id, prev_state, prev_state, prev_gate, prev_gate,
                RuleIdV2.RULE_8_OUT_OF_ORDER_REJECTION.value, "Out-of-order timestamp rejected",
                "out_of_order", frame, (), prev_gate.value,
            )

        if self.last_master_time_s >= 0.0 and abs(t - self.last_master_time_s) < 1e-9:
            return self._make_record(
                t, scenario_run_id, prev_state, prev_state, prev_gate, prev_gate,
                RuleIdV2.RULE_10_DUPLICATE_FRAME_REJECTION.value, "Duplicate frame timestamp rejected",
                "duplicate_frame", frame, (), prev_gate.value,
            )

        self.last_master_time_s = t

        for r in frame.vision_records:
            self.source_tracker.record_observation(
                source_id=r.source_id, timestamp_s=r.timestamp_s, available=r.available,
                detections=r.detections, metadata=r.metadata,
            )
        for r in frame.audio_records:
            self.source_tracker.record_observation(
                source_id=r.source_id, timestamp_s=r.timestamp_s, available=r.available,
                detections=r.detections, metadata=r.metadata,
            )
        for src, avail in frame.source_availability.items():
            if src not in self.source_tracker.sources:
                modality = Modality.AUDIO if ("audio" in src or "mic" in src) else Modality.VISION
                self.source_tracker.register_source(src, modality=modality)
            if not avail:
                self.source_tracker.record_observation(source_id=src, timestamp_s=t, available=False)

        for src in list(self.source_tracker.sources.keys()):
            self.source_tracker.evaluate_staleness(src, t)

        current_avail = self.source_tracker.get_availability_map(t)
        for src, avail in frame.source_availability.items():
            current_avail[src] = bool(avail) if not avail else True

        vision_sources = [
            src for src, status in self.source_tracker.sources.items()
            if status.modality == Modality.VISION
            or "camera" in src or "vision" in src or "front" in src or "rear" in src
        ]
        if not vision_sources:
            vision_sources = [
                src for src in frame.source_availability
                if "camera" in src or "vision" in src or "front" in src or "rear" in src
            ]
        has_registered_vision = bool(vision_sources)

        departure_sources = [s for s in vision_sources if is_departure_role_source(s)]
        departure_source_stale = bool(departure_sources) and any(
            not current_avail.get(s, True) for s in departure_sources
        )

        any_vision_frame_avail = any(
            avail for src, avail in frame.source_availability.items()
            if (src in vision_sources or "camera" in src or "vision" in src or "front" in src or "rear" in src)
            and avail
        ) or any(r.available for r in frame.vision_records)
        vision_avail = (
            (any_vision_frame_avail or any(current_avail.get(src, False) for src in vision_sources))
            if has_registered_vision else True
        )
        all_vision_failed = has_registered_vision and not vision_avail

        fault_status = "none"
        if all_vision_failed:
            fault_status = "all_vision_failed"
            self.consecutive_vision_failure_count += 1
        else:
            self.consecutive_vision_failure_count = 0

        audio_train_detected = has_audio_train_presence(frame, self.audio_threshold)

        # Evidence qualification uses the GAP state as it stood at the END of
        # the PREVIOUS tick (i.e. BEFORE this tick's detections are folded
        # in below) -- this is what lets `has_genuinely_new_approach_evidence`
        # distinguish "reappearing after N quiet ticks" from "still here".
        approach_detected_new = has_genuinely_new_approach_evidence(
            frame, self.ticks_since_last_detection, self.approach_threshold, self.gap_frames_for_new_detection,
        )
        any_detection = has_any_qualifying_detection(frame, self.approach_threshold)

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

        if all_vision_failed:
            if prev_state in (CrossingState.REAR_CONFIRMED, CrossingState.CROSSING_CLEAR, CrossingState.GATE_OPENING):
                next_state = CrossingState.FAULT_FAIL_SAFE
                next_gate = GateState.CLOSED
                rule_id = RuleIdV2.RULE_5_STALE_SOURCE_ABORT.value
                explanation = f"Stale or missing vision source in {prev_state.value}; aborting clearance/opening and clamping gate closed"
                self.clearance_started_at_s = None
                self._transition_to(next_state, next_gate, t)
                self._update_gap_state(frame)
                return self._make_record(
                    t, scenario_run_id, prev_state, next_state, prev_gate, next_gate, rule_id, explanation,
                    fault_status, frame, tuple(ev_refs), next_gate.value,
                    self.source_tracker.get_health_map(t), self.source_tracker.get_reason_map(t),
                    self.source_tracker.get_age_map(t),
                )
            elif prev_state not in (CrossingState.IDLE, CrossingState.FAULT_FAIL_SAFE):
                next_state = CrossingState.FAULT_FAIL_SAFE
                next_gate = GateState.CLOSED
                rule_id = RuleIdV2.RULE_4_FAIL_SAFE_CLAMP.value
                explanation = "All vision sources failed while crossing active; clamping gate closed"
                self._transition_to(next_state, next_gate, t)
                self._update_gap_state(frame)
                return self._make_record(
                    t, scenario_run_id, prev_state, next_state, prev_gate, next_gate, rule_id, explanation,
                    fault_status, frame, tuple(ev_refs), next_gate.value,
                    self.source_tracker.get_health_map(t), self.source_tracker.get_reason_map(t),
                    self.source_tracker.get_age_map(t),
                )
            elif prev_state == CrossingState.IDLE and self.consecutive_vision_failure_count >= self.confirm_frames:
                next_state = CrossingState.FAULT_FAIL_SAFE
                next_gate = GateState.CLOSED
                rule_id = RuleIdV2.RULE_4_FAIL_SAFE_CLAMP.value
                explanation = f"All vision sources failed in IDLE for {self.consecutive_vision_failure_count} frames; fail-safe clamp closed"
                self._transition_to(next_state, next_gate, t)
                self._update_gap_state(frame)
                return self._make_record(
                    t, scenario_run_id, prev_state, next_state, prev_gate, next_gate, rule_id, explanation,
                    fault_status, frame, tuple(ev_refs), next_gate.value,
                    self.source_tracker.get_health_map(t), self.source_tracker.get_reason_map(t),
                    self.source_tracker.get_age_map(t),
                )

        if prev_state == CrossingState.IDLE:
            # NOTE: deliberately uses the BROAD `any_detection` check here,
            # not `approach_detected_new` -- RULE_1's "2 consecutive frames"
            # confirmation (unchanged from the frozen policy) REQUIRES a
            # continuing detection stream to accumulate across frames, which
            # is the opposite of what `has_genuinely_new_approach_evidence`
            # (correctly) demands for RULE_7's new-train interrupt. Reusing
            # the strict check here was tried and found to break initial
            # approach confirmation on real events whose front-camera
            # evidence is predominantly ambiguous ("side"/"train") labels,
            # since the second of two consecutive ambiguous detections has
            # gap=0 and would never itself count as "new" -- confirmed via
            # the Phase 10 real-event replay (event_005 got stuck
            # oscillating IDLE/TRAIN_APPROACHING) before this fix.
            if any_detection:
                self.consecutive_approach_count += 1
                if self.consecutive_approach_count >= self.confirm_frames:
                    next_state = CrossingState.WARNING
                    next_gate = GateState.OPEN
                    rule_id = RuleIdV2.RULE_1_APPROACH_TRIGGER.value
                    explanation = f"Qualified approach confirmed over {self.confirm_frames} frames"
                else:
                    next_state = CrossingState.TRAIN_APPROACHING
                    rule_id = RuleIdV2.RULE_1_APPROACH_TRIGGER.value
                    explanation = "Qualified approach detected; awaiting confirmation"
            else:
                self.consecutive_approach_count = 0
                if audio_train_detected:
                    rule_id = RuleIdV2.RULE_2_AUDIO_SUPPORT_ONLY.value
                    explanation = "Audio train noise observed in IDLE; supporting only, no gate actuation"

        elif prev_state == CrossingState.TRAIN_APPROACHING:
            if any_detection:
                self.consecutive_approach_count += 1
                if self.consecutive_approach_count >= self.confirm_frames:
                    next_state = CrossingState.WARNING
                    rule_id = RuleIdV2.RULE_1_APPROACH_TRIGGER.value
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
            if any_detection:
                next_state = CrossingState.CROSSING_OCCUPIED
                explanation = "Train occupancy observed at crossing"

        elif prev_state == CrossingState.CROSSING_OCCUPIED:
            next_gate = GateState.CLOSED
            if any_detection:
                next_state = CrossingState.TRAIN_DEPARTING
                explanation = "Train continues to be observed; entering departure-tracking phase"

        elif prev_state == CrossingState.TRAIN_DEPARTING:
            next_gate = GateState.CLOSED
            if departure_sources:
                dep_role_avail = [s for s in departure_sources if current_avail.get(s, False)]
                if not dep_role_avail:
                    rule_id = RuleIdV2.RULE_6_DEGRADED_SOURCE_HOLD.value
                    explanation = "Departure camera degraded or missing; holding gate closed in TRAIN_DEPARTING"
                elif has_unambiguous_departure_label_from(frame, set(departure_sources), self.departure_threshold):
                    next_state = CrossingState.REAR_CONFIRMED
                    self.clearance_started_at_s = None
                    rule_id = RuleIdV2.RULE_3B_DEPARTURE_CONFIRMED_UNAMBIGUOUS_REAR.value
                    explanation = "Positive rear clearance confirmed by unambiguous 'rear' label from departure-role camera"
                elif all(self.ticks_since_last_detection.get(s, 0) >= self.confirm_frames for s in dep_role_avail):
                    next_state = CrossingState.REAR_CONFIRMED
                    self.clearance_started_at_s = None
                    rule_id = RuleIdV2.RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE.value
                    explanation = (
                        f"Departure-role camera reported no qualifying detection for "
                        f"{self.confirm_frames} consecutive frames; confirming departure by sustained disappearance"
                    )
                else:
                    explanation = "Awaiting unambiguous rear confirmation or sustained disappearance on departure-role camera"
            else:
                # Single-camera (front-only) topology: no departure-role
                # source registered. Confirm departure only via sustained
                # disappearance of the sole camera, never via ambiguous
                # relabeling of its own continuing detections.
                sole_sources = vision_sources
                sole_avail = [s for s in sole_sources if current_avail.get(s, False)]
                if not sole_avail:
                    rule_id = RuleIdV2.RULE_6_DEGRADED_SOURCE_HOLD.value
                    explanation = "Sole camera degraded or missing; holding gate closed in TRAIN_DEPARTING"
                elif sole_avail and all(self.ticks_since_last_detection.get(s, 0) >= self.confirm_frames for s in sole_avail):
                    next_state = CrossingState.REAR_CONFIRMED
                    self.clearance_started_at_s = None
                    rule_id = RuleIdV2.RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE.value
                    explanation = (
                        f"No dedicated departure-role camera registered; sole camera reported no qualifying "
                        f"detection for {self.confirm_frames} consecutive frames; confirming departure by "
                        "sustained disappearance"
                    )
                else:
                    explanation = "No dedicated departure-role camera registered; awaiting sustained disappearance on sole camera"

        elif prev_state == CrossingState.REAR_CONFIRMED:
            next_gate = GateState.CLOSED
            if approach_detected_new:
                next_state = CrossingState.TRAIN_PRESENT
                rule_id = RuleIdV2.RULE_7_NEW_TRAIN_INTERRUPT.value
                explanation = "Genuinely new train approach evidence detected during rear clearance; returning to TRAIN_PRESENT"
                self.clearance_started_at_s = None
            elif has_registered_vision and (not vision_avail or departure_source_stale):
                next_state = CrossingState.FAULT_FAIL_SAFE
                next_gate = GateState.CLOSED
                rule_id = RuleIdV2.RULE_5_STALE_SOURCE_ABORT.value
                explanation = (
                    "Stale or missing departure vision source during rear clearance dwell; aborting clearance and clamping closed"
                    if departure_source_stale and vision_avail
                    else "Stale or missing vision source during rear clearance dwell; aborting clearance and clamping closed"
                )
                self.clearance_started_at_s = None
            else:
                if audio_train_detected:
                    rule_id = RuleIdV2.RULE_2_AUDIO_SUPPORT_ONLY.value
                    explanation = "Audio train energy present; delaying clearance dwell"
                    self.clearance_started_at_s = t
                else:
                    if self.clearance_started_at_s is None:
                        self.clearance_started_at_s = t
                    clear_elapsed = t - self.clearance_started_at_s
                    if clear_elapsed >= self.clearance_dwell_s:
                        next_state = CrossingState.CROSSING_CLEAR
                        rule_id = RuleIdV2.RULE_3_POSITIVE_CLEARANCE.value
                        explanation = f"Clearance dwell of {self.clearance_dwell_s}s satisfied with no genuinely new conflicting evidence"

        elif prev_state == CrossingState.CROSSING_CLEAR:
            if approach_detected_new:
                next_state = CrossingState.GATE_CLOSING
                next_gate = GateState.CLOSING
                rule_id = RuleIdV2.RULE_7_NEW_TRAIN_INTERRUPT.value
                explanation = "Genuinely new train approach evidence detected in CROSSING_CLEAR; aborting opening"
            elif has_registered_vision and (not vision_avail or departure_source_stale):
                next_state = CrossingState.FAULT_FAIL_SAFE
                next_gate = GateState.CLOSED
                rule_id = RuleIdV2.RULE_5_STALE_SOURCE_ABORT.value
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
            if approach_detected_new:
                next_state = CrossingState.GATE_CLOSING
                next_gate = GateState.CLOSING
                rule_id = RuleIdV2.RULE_7_NEW_TRAIN_INTERRUPT.value
                explanation = "Genuinely new train approach evidence detected while gate opening; aborting to GATE_CLOSING"
            elif has_registered_vision and (not vision_avail or departure_source_stale):
                next_state = CrossingState.FAULT_FAIL_SAFE
                next_gate = GateState.CLOSED
                rule_id = RuleIdV2.RULE_5_STALE_SOURCE_ABORT.value
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
                    explanation = f"Gate opening elapsed ({self.gate_opening_s}s); crossing returned to IDLE"

        elif prev_state == CrossingState.FAULT_FAIL_SAFE:
            next_gate = GateState.CLOSED
            if vision_avail and has_registered_vision:
                if any_detection:
                    next_state = CrossingState.TRAIN_PRESENT
                    explanation = "Train presence detected while in FAULT_FAIL_SAFE; transitioning to TRAIN_PRESENT"
                    self.consecutive_recovery_count = 0
                    self.fault_entered_from = None
                elif audio_train_detected:
                    self.consecutive_recovery_count = 0
                    explanation = "Audio train noise observed while in FAULT_FAIL_SAFE; holding closed"
                else:
                    self.consecutive_recovery_count += 1
                    if self.consecutive_recovery_count >= self.confirm_frames:
                        if self.fault_entered_from == CrossingState.IDLE and not self.train_present_or_approaching:
                            next_state = CrossingState.IDLE
                            next_gate = GateState.OPEN
                            rule_id = RuleIdV2.RULE_9_SENSOR_RECOVERY.value
                            explanation = (
                                f"All sensors recovered to HEALTHY for {self.consecutive_recovery_count} "
                                "frames from IDLE fault; restoring crossing to IDLE"
                            )
                        else:
                            next_state = CrossingState.TRAIN_PRESENT
                            next_gate = GateState.CLOSED
                            rule_id = RuleIdV2.RULE_9_SENSOR_RECOVERY.value
                            origin_str = self.fault_entered_from.value if self.fault_entered_from else "active"
                            explanation = (
                                f"Sensors recovered after fault during active crossing ({origin_str}); "
                                "holding gate closed in TRAIN_PRESENT awaiting operational departure clearance"
                            )
                        self.consecutive_recovery_count = 0
                        self.fault_entered_from = None
                    else:
                        rule_id = RuleIdV2.RULE_9_SENSOR_RECOVERY.value
                        explanation = (
                            f"Sensors recovering ({self.consecutive_recovery_count}/{self.confirm_frames} "
                            "frames); maintaining fail-safe clamp"
                        )
            else:
                self.consecutive_recovery_count = 0
                explanation = "System in FAULT_FAIL_SAFE; automatic gate opening prohibited"

        self._transition_to(next_state, next_gate, t)
        self._update_gap_state(frame)
        return self._make_record(
            t, scenario_run_id, prev_state, next_state, prev_gate, next_gate, rule_id, explanation,
            fault_status, frame, tuple(ev_refs), next_gate.value,
            self.source_tracker.get_health_map(t), self.source_tracker.get_reason_map(t),
            self.source_tracker.get_age_map(t),
        )

    def _update_gap_state(self, frame: MultimodalFrame) -> None:
        """Advance per-source continuity tracking for the NEXT tick. Must run
        AFTER this tick's rules have already been evaluated against the
        gap state as it stood going into this tick."""
        detected_sources = detection_sources_this_tick(frame, self.approach_threshold)
        known_sources = {r.source_id for r in frame.vision_records} | set(self.ticks_since_last_detection)
        for src in known_sources:
            if src in detected_sources:
                self.ticks_since_last_detection[src] = 0
            else:
                self.ticks_since_last_detection[src] = self.ticks_since_last_detection.get(src, 0) + 1

    def _transition_to(self, next_state: CrossingState, next_gate: GateState, timestamp_s: float) -> None:
        if next_state != self.current_state:
            if next_state == CrossingState.FAULT_FAIL_SAFE and self.fault_entered_from is None:
                self.fault_entered_from = self.current_state
            elif next_state == CrossingState.IDLE:
                self.train_present_or_approaching = False
                self.fault_entered_from = None
            elif next_state in (
                CrossingState.WARNING, CrossingState.GATE_CLOSING, CrossingState.TRAIN_PRESENT,
                CrossingState.CROSSING_OCCUPIED, CrossingState.TRAIN_DEPARTING, CrossingState.REAR_CONFIRMED,
                CrossingState.CROSSING_CLEAR, CrossingState.GATE_OPENING,
            ):
                self.train_present_or_approaching = True
            self.current_state = next_state
            self.state_entry_time_s = float(timestamp_s)
        self.current_gate_state = next_gate

    def _make_record(
        self, timestamp_s, run_id, prev_s, next_s, prev_g, next_g, rule_id, explanation, fault_status,
        frame, ev_refs, gate_cmd=None, source_health=None, health_reasons=None, observation_ages=None,
    ) -> DecisionRecord:
        s_avail = dict(frame.source_availability)
        s_health = dict(source_health if source_health is not None else frame.source_health)
        h_reasons = dict(health_reasons if health_reasons is not None else frame.health_reasons)
        obs_ages = dict(observation_ages if observation_ages is not None else frame.observation_ages)
        return DecisionRecord(
            timestamp_s=timestamp_s, scenario_run_id=run_id,
            previous_state=prev_s.value, resulting_state=next_s.value,
            previous_gate_state=prev_g.value, resulting_gate_state=next_g.value,
            evidence_references=ev_refs, rule_id=rule_id, explanation=explanation, fault_status=fault_status,
            source_availability=s_avail, source_health=s_health, health_reasons=h_reasons,
            observation_ages=obs_ages, gate_command=gate_cmd if gate_cmd is not None else next_g.value,
        )
