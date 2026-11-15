"""Four-layer causal multimodal finite-state decision engine (V3).

Integrates:
- Layer 1 (Front camera): Early independent approach detection & closure initiation.
- Layer 2 (Side view): Temporal presence persistence & bounding-box movement tracking.
- Layer 3 (Audio/horn): Supporting presence & clearance-dwell reinforcement only.
- Layer 4 (Back camera): Conservative positive rear/last-carriage departure vs optional
  explicitly guarded disappearance comparison mode.
- Final Clearance (Occupancy): Dedicated crossing occupancy verification gating opening.
"""

from __future__ import annotations

from typing import Any

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.evidence import (
    DecisionRecord,
    EvidenceStatus,
    Modality,
    OccupancyState,
)
from railway_detection.fusion.occupancy import OccupancyAssessment, OccupancyVerifier
from railway_detection.fusion.rules import CrossingState, GateState, RuleId
from railway_detection.fusion.rules_v3_four_layer import (
    DeparturePolicyMode,
    Layer1FrontEvidence,
    Layer2SideEvidence,
    Layer3AudioEvidence,
    Layer4DepartureAssessment,
    RuleIdV3,
    SideMovementTracker,
    classify_vision_sources,
    extract_layer1_front_evidence,
    extract_layer3_audio_evidence,
    extract_layer4_departure_evidence,
)
from railway_detection.fusion.source_tracker import SourceTracker


class MultimodalDecisionEngineV3FourLayer:
    """Four-layer multimodal crossing protection engine operating on 11 CrossingStates."""

    def __init__(
        self,
        *,
        approach_threshold: float = 0.35,
        side_threshold: float = 0.35,
        audio_threshold: float = 0.37,
        departure_threshold: float = 0.35,
        confirm_frames: int = 2,
        rear_confirm_frames: int = 2,
        warning_dwell_s: float = 2.0,
        gate_closing_s: float = 3.0,
        clearance_dwell_s: float = 1.5,
        gate_opening_s: float = 2.0,
        sensor_timeout_s: float = 2.0,
        audio_hold_s: float = 1.5,
        allow_any_front_camera_label: bool = True,
        departure_mode: DeparturePolicyMode | str = DeparturePolicyMode.CONSERVATIVE_POSITIVE,
        require_last_carriage: bool = False,
        require_occupancy_for_reopen: bool = True,
        require_healthy_back_for_reopen: bool = True,
        require_healthy_front_for_reopen: bool = False,
        require_manual_reset_after_active_fault: bool = False,
        guarded_min_back_frames: int = 2,
        guarded_min_passage_s: float = 1.0,
        guarded_negative_hold_s: float = 1.0,
        enable_optical_degradation_audio_wakeup: bool = False,
        optical_visibility_floor: float = 0.45,
        degraded_audio_wakeup_threshold: float = 0.75,
        degraded_audio_wakeup_frames: int = 3,
        occupancy_verifier: OccupancyVerifier | None = None,
        source_tracker: SourceTracker | None = None,
    ) -> None:
        self.approach_threshold = float(approach_threshold)
        self.side_threshold = float(side_threshold)
        self.audio_threshold = float(audio_threshold)
        self.departure_threshold = float(departure_threshold)
        self.confirm_frames = max(1, int(confirm_frames))
        self.rear_confirm_frames = max(1, int(rear_confirm_frames))
        self.warning_dwell_s = float(warning_dwell_s)
        self.gate_closing_s = float(gate_closing_s)
        self.clearance_dwell_s = float(clearance_dwell_s)
        self.gate_opening_s = float(gate_opening_s)
        self.sensor_timeout_s = float(sensor_timeout_s)
        self.audio_hold_s = float(audio_hold_s)
        self.allow_any_front_camera_label = bool(allow_any_front_camera_label)
        self.departure_mode = DeparturePolicyMode(departure_mode)
        self.require_last_carriage = bool(require_last_carriage)
        self.require_occupancy_for_reopen = bool(require_occupancy_for_reopen)
        self.require_healthy_back_for_reopen = bool(require_healthy_back_for_reopen)
        self.require_healthy_front_for_reopen = bool(require_healthy_front_for_reopen)
        self.require_manual_reset_after_active_fault = bool(require_manual_reset_after_active_fault)
        self.guarded_min_back_frames = max(1, int(guarded_min_back_frames))
        self.guarded_min_passage_s = float(guarded_min_passage_s)
        self.guarded_negative_hold_s = float(guarded_negative_hold_s)
        self.enable_optical_degradation_audio_wakeup = bool(enable_optical_degradation_audio_wakeup)
        self.optical_visibility_floor = float(optical_visibility_floor)
        self.degraded_audio_wakeup_threshold = float(degraded_audio_wakeup_threshold)
        self.degraded_audio_wakeup_frames = max(1, int(degraded_audio_wakeup_frames))

        self.occupancy_verifier = (
            occupancy_verifier
            if occupancy_verifier is not None
            else OccupancyVerifier(
                require_dedicated_sensor=self.require_occupancy_for_reopen,
                max_occupancy_age_s=self.sensor_timeout_s,
                presence_threshold=min(self.approach_threshold, self.side_threshold),
                audio_presence_threshold=self.audio_threshold,
            )
        )
        self.side_tracker = SideMovementTracker(
            presence_threshold=self.side_threshold,
            min_persistence_frames=self.confirm_frames,
        )
        self.source_tracker = (
            source_tracker
            if source_tracker is not None
            else SourceTracker(default_timeout_s=self.sensor_timeout_s)
        )
        self.reset(initial_time_s=0.0)

    def reset(self, initial_time_s: float = 0.0) -> None:
        self.current_state = CrossingState.IDLE
        self.current_gate_state = GateState.OPEN
        self.state_entry_time_s = float(initial_time_s)
        self.last_processed_timestamp_s: float | None = None
        self.consecutive_approach_count = 0
        self.consecutive_rear_count = 0
        self.consecutive_vision_failure_count = 0
        self.consecutive_recovery_count = 0
        self.rear_confirmed_observed = False
        self.last_carriage_confirmed_observed = False
        self.clearance_started_at_s: float | None = None
        self.train_present_or_approaching = False
        self.fault_entered_from: CrossingState | None = None
        self.last_audio_horn_time_s: float | None = None
        self.back_positive_frames = 0
        self.back_first_seen_time_s: float | None = None
        self.back_negative_since_s: float | None = None
        self.consecutive_degraded_audio_count = 0
        self.stream_terminated_sources: set[str] = set()
        self.side_tracker.reset()
        self.occupancy_verifier.reset()
        self.source_tracker = SourceTracker(default_timeout_s=self.sensor_timeout_s)
        self.timing_trace: dict[str, float | None] = {
            "first_front_detection_s": None,
            "confirmed_front_detection_s": None,
            "engine_trigger_s": None,
            "gate_close_command_s": None,
            "rear_confirmed_s": None,
            "crossing_clear_s": None,
            "gate_opening_s": None,
        }

    def _update_source_health(self, frame: MultimodalFrame) -> dict[str, str]:
        t = float(frame.master_timestamp_s)
        timeout_sources: set[str] = set()

        for rec in list(frame.vision_records) + list(frame.audio_records):
            if rec.metadata.get("inference_timeout"):
                timeout_sources.add(rec.source_id)
            if rec.metadata.get("stream_terminated"):
                self.stream_terminated_sources.add(rec.source_id)
            avail = rec.available and (rec.source_id not in timeout_sources)
            self.source_tracker.record_observation(
                source_id=rec.source_id,
                timestamp_s=t,
                available=avail,
                detections=rec.detections if avail else (),
                metadata=rec.metadata,
            )

        for src, avail in frame.source_availability.items():
            if not avail and src not in self.source_tracker.sources:
                modality = (
                    Modality.AUDIO
                    if ("audio" in src.lower() or "mic" in src.lower())
                    else Modality.VISION
                )
                self.source_tracker.register_source(src, modality=modality)
            if not avail:
                self.source_tracker.record_observation(
                    source_id=src,
                    timestamp_s=t,
                    available=False,
                )

        for src in list(self.source_tracker.sources):
            self.source_tracker.evaluate_staleness(src, t)

        health_summary: dict[str, str] = {}
        avail_map = self.source_tracker.get_availability_map(t)
        for src in set(avail_map) | set(frame.source_statuses):
            if src in timeout_sources:
                health_summary[src] = EvidenceStatus.UNAVAILABLE.value
            elif src in frame.source_statuses:
                # Reconcile collector status with tracker staleness
                if not avail_map.get(src, True):
                    health_summary[src] = frame.source_statuses[src]
                    if health_summary[src] in (
                        EvidenceStatus.POSITIVE.value,
                        EvidenceStatus.NEGATIVE.value,
                        EvidenceStatus.UNKNOWN.value,
                    ):
                        health_summary[src] = EvidenceStatus.STALE.value
                else:
                    health_summary[src] = frame.source_statuses[src]
            else:
                health_summary[src] = (
                    EvidenceStatus.NEGATIVE.value
                    if avail_map.get(src, False)
                    else EvidenceStatus.MISSING.value
                )
        return health_summary

    def _collect_ev_refs(self, frame: MultimodalFrame) -> tuple[str, ...]:
        refs: list[str] = []
        for rec in list(frame.vision_records) + list(frame.audio_records):
            if rec.available and rec.detections and not rec.metadata.get("inference_timeout"):
                refs.append(f"{rec.source_id}:{rec.timestamp_s:.3f}")
        for occ in frame.occupancy_records:
            if occ.available:
                refs.append(f"{occ.source_id}:{occ.state.value}@{occ.timestamp_s:.3f}")
        return tuple(refs)

    def _source_is_healthy(
        self,
        src: str,
        t: float,
        frame: MultimodalFrame,
        status_map: dict[str, str],
    ) -> bool:
        if src in self.stream_terminated_sources:
            return False
        if not self.source_tracker.get_availability_map(t).get(src, True):
            return False
        if not frame.source_availability.get(src, True):
            return False
        status = status_map.get(src)
        if status in {EvidenceStatus.STALE.value, EvidenceStatus.UNAVAILABLE.value}:
            return False
        if status == EvidenceStatus.MISSING.value:
            # A lower-rate sensor (e.g., 0.5 s audio hops on a 0.2 s loop) is healthy on
            # inter-sample ticks provided it has delivered a fresh observation within timeout.
            tracker_state = self.source_tracker.sources.get(src)
            if tracker_state is None or tracker_state.last_timestamp_s is None:
                return False
        return True

    def _build_record(
        self,
        *,
        timestamp_s: float,
        scenario_run_id: str,
        prev_s: CrossingState,
        next_s: CrossingState,
        prev_g: GateState,
        next_g: GateState,
        rule_id: str | None,
        explanation: str,
        fault_status: str,
        frame: MultimodalFrame,
        ev_refs: tuple[str, ...],
        extra_avail: dict[str, bool],
    ) -> DecisionRecord:
        if next_s != prev_s:
            self.state_entry_time_s = timestamp_s
        self.current_state = next_s
        self.current_gate_state = next_g
        self.last_processed_timestamp_s = timestamp_s
        if next_g in (GateState.CLOSING, GateState.CLOSED) and self.timing_trace["gate_close_command_s"] is None:
            self.timing_trace["gate_close_command_s"] = timestamp_s
        if next_s == CrossingState.REAR_CONFIRMED and self.timing_trace["rear_confirmed_s"] is None:
            self.timing_trace["rear_confirmed_s"] = timestamp_s
        if next_s == CrossingState.CROSSING_CLEAR and self.timing_trace["crossing_clear_s"] is None:
            self.timing_trace["crossing_clear_s"] = timestamp_s
        if next_s == CrossingState.GATE_OPENING and self.timing_trace["gate_opening_s"] is None:
            self.timing_trace["gate_opening_s"] = timestamp_s
        if next_s == CrossingState.IDLE and next_g == GateState.OPEN:
            self.train_present_or_approaching = False
            self.rear_confirmed_observed = False
            self.last_carriage_confirmed_observed = False
            self.clearance_started_at_s = None
            self.back_positive_frames = 0
            self.back_first_seen_time_s = None
            self.back_negative_since_s = None
            self.consecutive_rear_count = 0

        return DecisionRecord(
            timestamp_s=timestamp_s,
            scenario_run_id=scenario_run_id,
            previous_state=prev_s.value,
            resulting_state=next_s.value,
            previous_gate_state=prev_g.value,
            resulting_gate_state=next_g.value,
            evidence_references=ev_refs,
            rule_id=rule_id,
            explanation=explanation,
            fault_status=fault_status,
            source_availability=extra_avail,
            source_health=self.source_tracker.get_health_map(timestamp_s),
            health_reasons=self.source_tracker.get_reason_map(timestamp_s),
            observation_ages=self.source_tracker.get_age_map(timestamp_s),
            gate_command=next_g.value,
        )

    def _has_clear_reopen_preconditions(
        self,
        *,
        t: float,
        frame: MultimodalFrame,
        status_map: dict[str, str],
        roles: dict[str, list[str]],
        occ: OccupancyAssessment,
        l1: Layer1FrontEvidence,
        l2: Layer2SideEvidence,
        l4: Layer4DepartureAssessment,
        audio_recent: bool,
    ) -> tuple[bool, str, str]:
        """Verify all 6 conservative reopening preconditions cleanly."""
        if not self.rear_confirmed_observed:
            return False, RuleIdV3.RULE_L4_BACK_SPARSE_DROPOUT_HOLD.value, "Departure not yet confirmed"
        if self.require_last_carriage and not self.last_carriage_confirmed_observed:
            return (
                False,
                RuleIdV3.RULE_L4_BACK_SPARSE_DROPOUT_HOLD.value,
                "Required last-carriage confirmation not yet observed",
            )
        if l1.detected or l2.present or l4.back_present or audio_recent:
            return (
                False,
                RuleIdV3.RULE_L3_AUDIO_DWELL_HOLD.value if audio_recent else RuleIdV3.RULE_L2_SIDE_MOVEMENT_CONFIRMED.value,
                "Active or contradictory train/horn presence blocks clearance",
            )
        if self.require_healthy_back_for_reopen and roles["back"]:
            if not all(self._source_is_healthy(s, t, frame, status_map) for s in roles["back"]):
                return False, RuleId.RULE_5_STALE_SOURCE_ABORT.value, "Back/departure camera unhealthy or missing"
        if self.require_healthy_front_for_reopen and roles["front"]:
            if not all(self._source_is_healthy(s, t, frame, status_map) for s in roles["front"]):
                return False, RuleId.RULE_5_STALE_SOURCE_ABORT.value, "Front camera unhealthy or missing"
        if occ.state == OccupancyState.CONTRADICTORY:
            return False, RuleIdV3.RULE_L5_OCCUPANCY_CONTRADICTION_ABORT.value, occ.reason
        if self.require_occupancy_for_reopen and not occ.verified_clear:
            return False, RuleIdV3.RULE_L5_OCCUPANCY_HOLD_UNKNOWN_OR_MISSING.value, occ.reason
        if occ.state in (OccupancyState.OCCUPIED, OccupancyState.CONTRADICTORY):
            return False, RuleIdV3.RULE_L5_OCCUPANCY_HOLD_UNKNOWN_OR_MISSING.value, occ.reason
        return True, RuleIdV3.RULE_L5_OCCUPANCY_CLEAR_VERIFIED.value, "All clearance preconditions verified"

    def evaluate_frame(self, frame: MultimodalFrame, scenario_run_id: str = "v3_run") -> DecisionRecord:
        t = float(frame.master_timestamp_s)
        prev_state = self.current_state
        prev_gate = self.current_gate_state

        # Monotonic causality guard
        if self.last_processed_timestamp_s is not None:
            if abs(t - self.last_processed_timestamp_s) <= 1e-9:
                return DecisionRecord(
                    timestamp_s=t,
                    scenario_run_id=scenario_run_id,
                    previous_state=prev_state.value,
                    resulting_state=prev_state.value,
                    previous_gate_state=prev_gate.value,
                    resulting_gate_state=prev_gate.value,
                    rule_id=RuleId.RULE_10_DUPLICATE_FRAME_REJECTION.value,
                    explanation=f"Duplicate master timestamp {t:.4f}s ignored",
                    fault_status="duplicate_frame",
                    source_availability=dict(frame.source_availability),
                    gate_command=prev_gate.value,
                )
            if t < self.last_processed_timestamp_s - 1e-9:
                return DecisionRecord(
                    timestamp_s=t,
                    scenario_run_id=scenario_run_id,
                    previous_state=prev_state.value,
                    resulting_state=prev_state.value,
                    previous_gate_state=prev_gate.value,
                    resulting_gate_state=prev_gate.value,
                    rule_id=RuleId.RULE_8_OUT_OF_ORDER_REJECTION.value,
                    explanation=f"Out-of-order master timestamp {t:.4f}s < {self.last_processed_timestamp_s:.4f}s",
                    fault_status="out_of_order_frame",
                    source_availability=dict(frame.source_availability),
                    gate_command=prev_gate.value,
                )

        status_map = self._update_source_health(frame)
        avail_map = self.source_tracker.get_availability_map(t)
        all_known_sources = set(self.source_tracker.sources) | set(frame.source_availability) | {
            r.source_id for r in frame.vision_records
        } | {r.source_id for r in frame.audio_records}
        roles = classify_vision_sources(all_known_sources)
        vision_sources = roles["front"] + roles["side"] + roles["back"]

        # Mask out records flagged with inference_timeout
        effective_vision = tuple(
            r for r in frame.vision_records if not r.metadata.get("inference_timeout")
        )
        effective_audio = tuple(
            r for r in frame.audio_records if not r.metadata.get("inference_timeout")
        )
        timeout_seen = len(effective_vision) < len(frame.vision_records) or len(effective_audio) < len(frame.audio_records)

        l1 = extract_layer1_front_evidence(
            frame,
            threshold=self.approach_threshold,
            allow_any_front_camera_label=self.allow_any_front_camera_label,
        )
        if timeout_seen:
            # Re-evaluate using non-timed-out records
            safe_frame = MultimodalFrame(
                master_timestamp_s=frame.master_timestamp_s,
                vision_records=effective_vision,
                audio_records=effective_audio,
                source_availability=frame.source_availability,
                active_sources=frame.active_sources,
                missing_sources=frame.missing_sources,
                source_health=frame.source_health,
                health_reasons=frame.health_reasons,
                observation_ages=frame.observation_ages,
                source_statuses=frame.source_statuses,
                occupancy_records=frame.occupancy_records,
            )
            l1 = extract_layer1_front_evidence(
                safe_frame,
                threshold=self.approach_threshold,
                allow_any_front_camera_label=self.allow_any_front_camera_label,
            )
        else:
            safe_frame = frame

        l2 = self.side_tracker.update(safe_frame)
        l3 = extract_layer3_audio_evidence(safe_frame, threshold=self.audio_threshold)
        l4 = extract_layer4_departure_evidence(
            safe_frame,
            rear_threshold=self.departure_threshold,
            back_sources=roles["back"],
        )
        occ = self.occupancy_verifier.evaluate(
            safe_frame,
            active_crossing_expected=self.train_present_or_approaching,
        )

        if l3.horn_detected:
            self.last_audio_horn_time_s = t
        audio_recent = (
            l3.horn_detected
            or (self.last_audio_horn_time_s is not None and (t - self.last_audio_horn_time_s) <= self.audio_hold_s)
        )

        # Opt-in optical-degradation awareness: track consecutive high-confidence audio horns
        # strictly while front optical telemetry explicitly indicates visibility degradation.
        front_optically_degraded = False
        if self.enable_optical_degradation_audio_wakeup:
            front_degraded_flags: list[bool] = []
            for rec in effective_vision:
                if rec.available and rec.source_id in roles["front"]:
                    explicit_deg = bool(rec.metadata.get("optical_degraded", False))
                    vis_score = rec.metadata.get("optical_visibility_score")
                    score_deg = (
                        isinstance(vis_score, int | float)
                        and not isinstance(vis_score, bool)
                        and float(vis_score) < self.optical_visibility_floor
                    )
                    front_degraded_flags.append(explicit_deg or score_deg)
            front_optically_degraded = bool(front_degraded_flags) and any(front_degraded_flags)
            if not front_optically_degraded:
                self.consecutive_degraded_audio_count = 0
            elif any(r.available for r in effective_audio):
                l3_wakeup = extract_layer3_audio_evidence(
                    safe_frame, threshold=self.degraded_audio_wakeup_threshold
                )
                if l3_wakeup.horn_detected:
                    self.consecutive_degraded_audio_count += 1
                else:
                    self.consecutive_degraded_audio_count = 0

        # Back presence accounting (used by conservative verification and guarded disappearance comparison)
        if l4.back_present:
            self.back_positive_frames += 1
            if self.back_first_seen_time_s is None:
                self.back_first_seen_time_s = t
            self.back_negative_since_s = None
        elif l4.back_source_refreshed and l4.back_source_healthy:
            if self.back_positive_frames > 0 and self.back_negative_since_s is None:
                self.back_negative_since_s = t

        if l1.detected and self.timing_trace["first_front_detection_s"] is None:
            self.timing_trace["first_front_detection_s"] = t

        # Compute vision availability flags safely
        has_vision = bool(vision_sources)
        any_vision_healthy = any(self._source_is_healthy(s, t, frame, status_map) for s in vision_sources)
        all_vision_failed = has_vision and not any_vision_healthy
        front_failed = bool(roles["front"]) and not any(
            self._source_is_healthy(s, t, frame, status_map) for s in roles["front"]
        )
        back_failed = bool(roles["back"]) and not any(
            self._source_is_healthy(s, t, frame, status_map) for s in roles["back"]
        )
        audio_sources = [
            s for s in all_known_sources if "audio" in s.lower() or "mic" in s.lower()
        ]
        audio_failed = bool(audio_sources) and not any(
            self._source_is_healthy(s, t, frame, status_map) for s in audio_sources
        )
        side_failed = bool(roles["side"]) and not any(
            self._source_is_healthy(s, t, frame, status_map) for s in roles["side"]
        )

        fault_flags: list[str] = []
        if timeout_seen:
            fault_flags.append("inference_timeout")
        if self.stream_terminated_sources:
            fault_flags.append("stream_terminated")
        if all_vision_failed:
            fault_flags.append("all_vision_failed")
            self.consecutive_vision_failure_count += 1
        elif front_failed and prev_state in (CrossingState.IDLE, CrossingState.TRAIN_APPROACHING):
            fault_flags.append("front_source_failed")
            self.consecutive_vision_failure_count += 1
        else:
            if front_failed:
                fault_flags.append("front_source_failed")
            self.consecutive_vision_failure_count = 0
        if back_failed:
            fault_flags.append("back_source_failed")
        if audio_failed:
            fault_flags.append("audio_source_failed")
        if side_failed:
            fault_flags.append("side_source_failed")
        if occ.state == OccupancyState.CONTRADICTORY:
            fault_flags.append("occupancy_contradiction")
        elif occ.state == OccupancyState.MISSING and self.require_occupancy_for_reopen:
            fault_flags.append("occupancy_missing")
        if l2.movement_state == "STOPPED":
            fault_flags.append("train_stopped_in_zone")
        if l4.reversing_detected:
            fault_flags.append("train_reversing")

        fault_status = ",".join(fault_flags) if fault_flags else "none"
        ev_refs = self._collect_ev_refs(safe_frame)

        # Top-level fail-safe overrides
        if all_vision_failed:
            if prev_state in (
                CrossingState.REAR_CONFIRMED,
                CrossingState.CROSSING_CLEAR,
                CrossingState.GATE_OPENING,
            ):
                self.fault_entered_from = prev_state
                self.clearance_started_at_s = None
                return self._build_record(
                    timestamp_s=t,
                    scenario_run_id=scenario_run_id,
                    prev_s=prev_state,
                    next_s=CrossingState.FAULT_FAIL_SAFE,
                    prev_g=prev_gate,
                    next_g=GateState.CLOSED,
                    rule_id=RuleId.RULE_5_STALE_SOURCE_ABORT.value,
                    explanation=f"Vision loss/staleness during {prev_state.value}; aborting opening and clamping closed",
                    fault_status=fault_status,
                    frame=frame,
                    ev_refs=ev_refs,
                    extra_avail=avail_map,
                )
            if prev_state not in (CrossingState.IDLE, CrossingState.FAULT_FAIL_SAFE):
                self.fault_entered_from = prev_state
                return self._build_record(
                    timestamp_s=t,
                    scenario_run_id=scenario_run_id,
                    prev_s=prev_state,
                    next_s=CrossingState.FAULT_FAIL_SAFE,
                    prev_g=prev_gate,
                    next_g=GateState.CLOSED,
                    rule_id=RuleId.RULE_4_FAIL_SAFE_CLAMP.value,
                    explanation="All vision sources lost while crossing active; clamping gate closed",
                    fault_status=fault_status,
                    frame=frame,
                    ev_refs=ev_refs,
                    extra_avail=avail_map,
                )
            if prev_state == CrossingState.IDLE and self.consecutive_vision_failure_count >= self.confirm_frames:
                self.fault_entered_from = CrossingState.IDLE
                return self._build_record(
                    timestamp_s=t,
                    scenario_run_id=scenario_run_id,
                    prev_s=prev_state,
                    next_s=CrossingState.FAULT_FAIL_SAFE,
                    prev_g=prev_gate,
                    next_g=GateState.CLOSED,
                    rule_id=RuleId.RULE_4_FAIL_SAFE_CLAMP.value,
                    explanation=f"All vision sources failed in IDLE for {self.consecutive_vision_failure_count} frames",
                    fault_status=fault_status,
                    frame=frame,
                    ev_refs=ev_refs,
                    extra_avail=avail_map,
                )
        elif (
            front_failed
            and prev_state in (CrossingState.IDLE, CrossingState.TRAIN_APPROACHING)
            and self.consecutive_vision_failure_count >= self.confirm_frames
        ):
            self.fault_entered_from = prev_state
            return self._build_record(
                timestamp_s=t,
                scenario_run_id=scenario_run_id,
                prev_s=prev_state,
                next_s=CrossingState.FAULT_FAIL_SAFE,
                prev_g=prev_gate,
                next_g=GateState.CLOSED,
                rule_id=RuleId.RULE_4_FAIL_SAFE_CLAMP.value,
                explanation=(
                    f"Primary front approach camera failed in {prev_state.value} for "
                    f"{self.consecutive_vision_failure_count} frames; fail-safe clamp closed"
                ),
                fault_status=fault_status,
                frame=frame,
                ev_refs=ev_refs,
                extra_avail=avail_map,
            )

        # State-specific causal logic (all edges verified against ALLOWED_TRANSITIONS)
        next_state = prev_state
        next_gate = prev_gate
        rule_id: str | None = None
        explanation = f"Holding {prev_state.value}"

        if prev_state == CrossingState.IDLE:
            if l1.detected:
                self.consecutive_approach_count += 1
                self.train_present_or_approaching = True
                if self.consecutive_approach_count >= self.confirm_frames:
                    next_state = CrossingState.WARNING
                    next_gate = GateState.OPEN if self.warning_dwell_s > 0.0 else GateState.CLOSING
                    rule_id = RuleIdV3.RULE_L1_FRONT_APPROACH_TRIGGER.value
                    self.timing_trace["confirmed_front_detection_s"] = t
                    self.timing_trace["engine_trigger_s"] = t
                    explanation = f"Layer 1 front approach confirmed ({self.confirm_frames} frames); triggering warning"
                else:
                    next_state = CrossingState.TRAIN_APPROACHING
                    rule_id = RuleIdV3.RULE_L1_FRONT_APPROACH_TRIGGER.value
                    explanation = "Layer 1 front approach detected; awaiting confirmation"
            elif (
                self.enable_optical_degradation_audio_wakeup
                and front_optically_degraded
                and self.consecutive_degraded_audio_count >= self.degraded_audio_wakeup_frames
            ):
                self.train_present_or_approaching = True
                next_state = CrossingState.WARNING
                next_gate = GateState.OPEN if self.warning_dwell_s > 0.0 else GateState.CLOSING
                rule_id = RuleIdV3.RULE_L3_OPTICAL_DEGRADED_AUDIO_WAKEUP.value
                self.timing_trace["engine_trigger_s"] = t
                explanation = (
                    f"Opt-in degraded-optics audio wakeup ({self.consecutive_degraded_audio_count} "
                    f"consecutive horn windows >= {self.degraded_audio_wakeup_threshold:.2f}); triggering warning"
                )
            elif l3.horn_detected:
                rule_id = RuleIdV3.RULE_L3_AUDIO_SUPPORT_ONLY.value
                explanation = "Layer 3 audio horn in IDLE held as supporting evidence only (no gate closure)"

        elif prev_state == CrossingState.TRAIN_APPROACHING:
            self.train_present_or_approaching = True
            if l1.detected:
                self.consecutive_approach_count += 1
                if self.consecutive_approach_count >= self.confirm_frames:
                    next_state = CrossingState.WARNING
                    next_gate = GateState.OPEN if self.warning_dwell_s > 0.0 else GateState.CLOSING
                    rule_id = RuleIdV3.RULE_L1_FRONT_APPROACH_TRIGGER.value
                    self.timing_trace["confirmed_front_detection_s"] = t
                    self.timing_trace["engine_trigger_s"] = t
                    explanation = "Layer 1 front approach confirmed; initiating warning"
            else:
                front_negative_fresh = any(
                    r.available and not r.detections for r in effective_vision if r.source_id in roles["front"]
                )
                if front_negative_fresh or not roles["front"]:
                    self.consecutive_approach_count = 0
                    self.train_present_or_approaching = False
                    next_state = CrossingState.IDLE
                    rule_id = RuleIdV3.RULE_L1_APPROACH_UNCONFIRMED_RESET.value
                    explanation = "Single/unconfirmed approach negated by fresh negative frame; returning IDLE"
                else:
                    explanation = "Front source dropped/unrefreshed before confirmation; not duplicating stale detection"

        elif prev_state == CrossingState.WARNING:
            self.train_present_or_approaching = True
            if (t - self.state_entry_time_s) >= self.warning_dwell_s:
                next_state = CrossingState.GATE_CLOSING
                next_gate = GateState.CLOSING
                rule_id = RuleIdV3.RULE_L1_FRONT_APPROACH_TRIGGER.value
                explanation = f"Warning dwell ({self.warning_dwell_s:.2f}s) elapsed; commanding GATE_CLOSING"

        elif prev_state == CrossingState.GATE_CLOSING:
            self.train_present_or_approaching = True
            next_gate = GateState.CLOSING
            if (t - self.state_entry_time_s) >= self.gate_closing_s:
                next_state = CrossingState.TRAIN_PRESENT
                next_gate = GateState.CLOSED
                explanation = f"Gate closing duration ({self.gate_closing_s:.2f}s) completed; gate CLOSED"

        elif prev_state == CrossingState.TRAIN_PRESENT:
            self.train_present_or_approaching = True
            next_gate = GateState.CLOSED
            if l2.present or l1.detected or l4.back_present or l3.horn_detected or occ.state == OccupancyState.OCCUPIED:
                next_state = CrossingState.CROSSING_OCCUPIED
                rule_id = (
                    RuleIdV3.RULE_L2_SIDE_MOVEMENT_CONFIRMED.value
                    if l2.present
                    else RuleIdV3.RULE_L1_FRONT_APPROACH_TRIGGER.value
                )
                explanation = "Train passage/occupancy active at crossing"

        elif prev_state == CrossingState.CROSSING_OCCUPIED:
            self.train_present_or_approaching = True
            next_gate = GateState.CLOSED
            if l2.movement_state == "STOPPED":
                rule_id = RuleIdV3.RULE_L2_SIDE_STOPPED_HOLD.value
                explanation = "Train appears stopped inside crossing zone; holding gate CLOSED"
            elif l4.reversing_detected:
                rule_id = RuleIdV3.RULE_L4_REVERSAL_HOLD.value
                explanation = "Reverse movement detected; holding gate CLOSED"
            elif l4.positive_rear or l4.last_carriage_confirmed:
                next_state = CrossingState.TRAIN_DEPARTING
                self.consecutive_rear_count = 1
                if l4.last_carriage_confirmed:
                    self.last_carriage_confirmed_observed = True
                rule_id = (
                    RuleIdV3.RULE_L4_BACK_LAST_CARRIAGE_CONFIRMED.value
                    if l4.last_carriage_confirmed
                    else RuleIdV3.RULE_L4_BACK_POSITIVE_DEPARTURE.value
                )
                explanation = "Layer 4 positive rear/last-carriage observation; entering TRAIN_DEPARTING"
            elif (
                self.departure_mode == DeparturePolicyMode.GUARDED_DISAPPEARANCE
                and l4.back_source_healthy
                and not l1.detected
                and not l2.present
                and not l4.back_present
                and not audio_recent
                and self.back_positive_frames >= self.guarded_min_back_frames
                and self.back_first_seen_time_s is not None
                and self.back_negative_since_s is not None
                and (self.back_negative_since_s - self.back_first_seen_time_s) >= self.guarded_min_passage_s
                and (t - self.back_negative_since_s) >= self.guarded_negative_hold_s
            ):
                next_state = CrossingState.TRAIN_DEPARTING
                rule_id = RuleIdV3.RULE_L4_BACK_GUARDED_DISAPPEARANCE.value
                explanation = "Guarded disappearance comparison mode: sustained healthy negative back frames after passage"

        elif prev_state == CrossingState.TRAIN_DEPARTING:
            self.train_present_or_approaching = True
            next_gate = GateState.CLOSED
            if l4.reversing_detected or l1.detected or l2.present or l2.movement_state == "STOPPED":
                self.consecutive_rear_count = 0
                rule_id = (
                    RuleIdV3.RULE_L4_REVERSAL_HOLD.value
                    if l4.reversing_detected
                    else RuleIdV3.RULE_L2_SIDE_MOVEMENT_CONFIRMED.value
                )
                explanation = "Active/reversing train detected during departure; resetting rear confirmation and holding CLOSED"
            elif l4.positive_rear or l4.last_carriage_confirmed:
                self.consecutive_rear_count += 1
                if l4.last_carriage_confirmed:
                    self.last_carriage_confirmed_observed = True
                enough_rear = self.consecutive_rear_count >= self.rear_confirm_frames
                enough_tail = (not self.require_last_carriage) or self.last_carriage_confirmed_observed
                if enough_rear and enough_tail and l4.back_source_healthy:
                    self.rear_confirmed_observed = True
                    next_state = CrossingState.REAR_CONFIRMED
                    rule_id = (
                        RuleIdV3.RULE_L4_BACK_LAST_CARRIAGE_CONFIRMED.value
                        if self.last_carriage_confirmed_observed
                        else RuleIdV3.RULE_L4_BACK_POSITIVE_DEPARTURE.value
                    )
                    explanation = "Layer 4 positive departure confirmed; advancing to REAR_CONFIRMED"
            elif (
                self.departure_mode == DeparturePolicyMode.CONSERVATIVE_POSITIVE
                and self.rear_confirm_frames == 1
                and self.consecutive_rear_count >= 1
                and (not self.require_last_carriage or self.last_carriage_confirmed_observed)
                and l4.back_source_refreshed
                and l4.back_source_healthy
                and not l4.back_present
                and not audio_recent
            ):
                self.rear_confirmed_observed = True
                next_state = CrossingState.REAR_CONFIRMED
                rule_id = (
                    RuleIdV3.RULE_L4_BACK_LAST_CARRIAGE_CONFIRMED.value
                    if self.last_carriage_confirmed_observed
                    else RuleIdV3.RULE_L4_BACK_POSITIVE_DEPARTURE.value
                )
                explanation = "Single-frame rear/tail observation followed by healthy negative back frame; confirmed"
            elif (
                self.departure_mode == DeparturePolicyMode.GUARDED_DISAPPEARANCE
                and l4.back_source_healthy
                and not l4.back_present
                and not audio_recent
                and occ.state != OccupancyState.OCCUPIED
                and self.back_positive_frames >= self.guarded_min_back_frames
                and self.back_negative_since_s is not None
                and (t - self.back_negative_since_s) >= self.guarded_negative_hold_s
            ):
                self.rear_confirmed_observed = True
                if not self.require_last_carriage:
                    next_state = CrossingState.REAR_CONFIRMED
                    rule_id = RuleIdV3.RULE_L4_BACK_GUARDED_DISAPPEARANCE.value
                    explanation = "Guarded disappearance confirmed healthy sustained absence; advancing to REAR_CONFIRMED"
            else:
                rule_id = RuleIdV3.RULE_L4_BACK_SPARSE_DROPOUT_HOLD.value
                explanation = "Sparse disappearance or missing positive rear evidence; holding gate CLOSED"

        elif prev_state == CrossingState.REAR_CONFIRMED:
            self.train_present_or_approaching = True
            next_gate = GateState.CLOSED
            if l1.detected or l4.reversing_detected:
                self.rear_confirmed_observed = False
                self.last_carriage_confirmed_observed = False
                self.consecutive_rear_count = 0
                next_state = CrossingState.TRAIN_PRESENT
                rule_id = RuleIdV3.RULE_L5_MULTI_TRAIN_INTERRUPT.value
                explanation = "Second train / reversal detected in REAR_CONFIRMED; returning to TRAIN_PRESENT"
            elif occ.state == OccupancyState.CONTRADICTORY:
                self.fault_entered_from = prev_state
                next_state = CrossingState.FAULT_FAIL_SAFE
                rule_id = RuleIdV3.RULE_L5_OCCUPANCY_CONTRADICTION_ABORT.value
                explanation = occ.reason
            else:
                can_clear, pre_rule, pre_expl = self._has_clear_reopen_preconditions(
                    t=t,
                    frame=frame,
                    status_map=status_map,
                    roles=roles,
                    occ=occ,
                    l1=l1,
                    l2=l2,
                    l4=l4,
                    audio_recent=audio_recent,
                )
                if can_clear:
                    next_state = CrossingState.CROSSING_CLEAR
                    self.clearance_started_at_s = t
                    rule_id = pre_rule
                    explanation = "Verified departure + healthy sources + CLEAR occupancy; starting clearance dwell"
                elif pre_rule == RuleId.RULE_5_STALE_SOURCE_ABORT.value:
                    self.fault_entered_from = prev_state
                    next_state = CrossingState.FAULT_FAIL_SAFE
                    rule_id = pre_rule
                    explanation = pre_expl
                else:
                    rule_id = pre_rule
                    explanation = pre_expl

        elif prev_state == CrossingState.CROSSING_CLEAR:
            next_gate = GateState.CLOSED
            if l1.detected or l2.present or l4.back_present:
                self.rear_confirmed_observed = False
                self.last_carriage_confirmed_observed = False
                self.clearance_started_at_s = None
                next_state = CrossingState.GATE_CLOSING
                next_gate = GateState.CLOSING
                rule_id = RuleId.RULE_7_NEW_TRAIN_INTERRUPT.value
                explanation = "New train / re-entry detected in CROSSING_CLEAR; aborting opening"
            elif occ.state == OccupancyState.CONTRADICTORY:
                self.fault_entered_from = prev_state
                self.clearance_started_at_s = None
                next_state = CrossingState.FAULT_FAIL_SAFE
                rule_id = RuleIdV3.RULE_L5_OCCUPANCY_CONTRADICTION_ABORT.value
                explanation = occ.reason
            elif occ.state == OccupancyState.OCCUPIED or (
                self.require_occupancy_for_reopen and not occ.verified_clear
            ):
                self.fault_entered_from = prev_state
                self.clearance_started_at_s = None
                next_state = CrossingState.FAULT_FAIL_SAFE
                rule_id = RuleIdV3.RULE_L5_OCCUPANCY_HOLD_UNKNOWN_OR_MISSING.value
                explanation = f"Occupancy lost CLEAR status during dwell ({occ.state.value}); clamping closed"
            elif (
                (self.require_healthy_back_for_reopen and roles["back"] and not all(self._source_is_healthy(s, t, frame, status_map) for s in roles["back"]))
                or (self.require_healthy_front_for_reopen and roles["front"] and not all(self._source_is_healthy(s, t, frame, status_map) for s in roles["front"]))
            ):
                self.fault_entered_from = prev_state
                self.clearance_started_at_s = None
                next_state = CrossingState.FAULT_FAIL_SAFE
                rule_id = RuleId.RULE_5_STALE_SOURCE_ABORT.value
                explanation = "Required camera degraded/stale during clearance dwell; fail-safe clamping"
            elif audio_recent:
                self.clearance_started_at_s = t
                rule_id = RuleIdV3.RULE_L3_AUDIO_DWELL_HOLD.value
                explanation = "Audio horn observed during clearance dwell; resetting dwell timer"
            else:
                assert self.clearance_started_at_s is not None
                if (t - self.clearance_started_at_s) >= self.clearance_dwell_s:
                    next_state = CrossingState.GATE_OPENING
                    next_gate = GateState.OPENING
                    rule_id = RuleIdV3.RULE_L5_REOPEN_AUTHORIZED.value
                    explanation = f"Clearance dwell ({self.clearance_dwell_s:.2f}s) + occupancy CLEAR verified; opening gate"

        elif prev_state == CrossingState.GATE_OPENING:
            can_hold_open, pre_rule, pre_expl = self._has_clear_reopen_preconditions(
                t=t,
                frame=frame,
                status_map=status_map,
                roles=roles,
                occ=occ,
                l1=l1,
                l2=l2,
                l4=l4,
                audio_recent=audio_recent,
            )
            if l1.detected or l2.present or l4.back_present:
                self.rear_confirmed_observed = False
                self.last_carriage_confirmed_observed = False
                self.clearance_started_at_s = None
                next_state = CrossingState.GATE_CLOSING
                next_gate = GateState.CLOSING
                rule_id = RuleId.RULE_7_NEW_TRAIN_INTERRUPT.value
                explanation = "New train presence detected while GATE_OPENING; re-closing gate immediately"
            elif not can_hold_open:
                self.fault_entered_from = prev_state
                self.clearance_started_at_s = None
                next_state = CrossingState.FAULT_FAIL_SAFE
                next_gate = GateState.CLOSED
                rule_id = (
                    RuleId.RULE_5_STALE_SOURCE_ABORT.value
                    if pre_rule == RuleId.RULE_5_STALE_SOURCE_ABORT.value
                    else pre_rule
                )
                explanation = f"Reopening aborted safely: {pre_expl}"
            elif (t - self.state_entry_time_s) >= self.gate_opening_s:
                next_state = CrossingState.IDLE
                next_gate = GateState.OPEN
                rule_id = RuleIdV3.RULE_L5_REOPEN_AUTHORIZED.value
                explanation = f"Gate opening completed ({self.gate_opening_s:.2f}s); crossing IDLE"

        elif prev_state == CrossingState.FAULT_FAIL_SAFE:
            next_gate = GateState.CLOSED
            sources_recovered = (
                (not all_vision_failed)
                and (not front_failed)
                and (not (self.require_healthy_back_for_reopen and back_failed))
                and (
                    not (
                        self.require_occupancy_for_reopen
                        and occ.state in (OccupancyState.MISSING, OccupancyState.CONTRADICTORY)
                    )
                )
            )
            if self.require_manual_reset_after_active_fault and self.train_present_or_approaching:
                rule_id = RuleId.RULE_4_FAIL_SAFE_CLAMP.value
                explanation = "Active-crossing fault requires explicit operator reset before recovery"
            elif sources_recovered:
                if l1.detected or l2.present or l4.back_present or occ.state == OccupancyState.OCCUPIED:
                    next_state = CrossingState.TRAIN_PRESENT
                    self.train_present_or_approaching = True
                    self.consecutive_recovery_count = 0
                    self.consecutive_vision_failure_count = 0
                    self.fault_entered_from = None
                    rule_id = RuleId.RULE_9_SENSOR_RECOVERY.value
                    explanation = "Sensors recovered with active train/occupancy; holding CLOSED in TRAIN_PRESENT"
                elif not l3.horn_detected:
                    self.consecutive_recovery_count += 1
                    if self.consecutive_recovery_count >= self.confirm_frames:
                        self.consecutive_recovery_count = 0
                        self.consecutive_vision_failure_count = 0
                        if self.fault_entered_from == CrossingState.IDLE and not self.train_present_or_approaching:
                            next_state = CrossingState.IDLE
                            next_gate = GateState.OPEN
                            rule_id = RuleId.RULE_9_SENSOR_RECOVERY.value
                            self.fault_entered_from = None
                            explanation = "Sensors recovered from IDLE fault without train presence; returning to IDLE"
                        else:
                            next_state = CrossingState.TRAIN_PRESENT
                            next_gate = GateState.CLOSED
                            rule_id = RuleId.RULE_9_SENSOR_RECOVERY.value
                            self.fault_entered_from = None
                            explanation = (
                                "Sensors recovered after active-crossing fault; clamping CLOSED in TRAIN_PRESENT "
                                "until positive departure and CLEAR occupancy are verified"
                            )
            else:
                self.consecutive_recovery_count = 0
                rule_id = RuleId.RULE_4_FAIL_SAFE_CLAMP.value
                explanation = f"Critical source fault active ({fault_status}); holding fail-safe CLOSED"

        return self._build_record(
            timestamp_s=t,
            scenario_run_id=scenario_run_id,
            prev_s=prev_state,
            next_s=next_state,
            prev_g=prev_gate,
            next_g=next_gate,
            rule_id=rule_id,
            explanation=explanation,
            fault_status=fault_status,
            frame=frame,
            ev_refs=ev_refs,
            extra_avail=avail_map,
        )
