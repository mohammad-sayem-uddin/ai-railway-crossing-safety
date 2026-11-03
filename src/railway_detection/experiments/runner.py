"""Benchmark execution orchestrator for B0–B7 research protocol conditions.

Authoritative methodology: docs/REAL_WORLD_EXPERIMENT_PLAN.md
Reconciled B0–B7 definitions:
- B0: Vision Only (front camera only, raw independent-frame, no audio, no temporal, stateless)
- B1: Audio Only (extracted audio only, no vision, invariant: audio NEVER opens gate)
- B2: Vision + Audio (both cameras + audio, stateless 3-frame persistence, no state machine)
- B3: Temporal Evidence (both cameras, no audio, temporal filtering with confirm_frames=2, stateless)
- B4: Temporal + Multimodal (Full proposed policy: both cameras + audio + temporal + state machine)
- B5: Camera 1 Failure (sub-experiments B5a: start dropout, B5b: midway dropout, B5c: flapping)
- B6: Camera 2 / Dual Sensor Failure (sub-experiments B6a: camera 2 dropout, B6b: dual dropout, B6c: sequential dropout)
- B7: Sensor / Timing Robustness (sub-experiments B7a: audio dropout, B7b: 30% frame drops, B7c: false detection conf=0.85, B7d: out-of-order frames, B7e: stale timestamps 2s, B7f: compound audio dropout + 10% frame drops)
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict
from enum import StrEnum
from pathlib import Path
from typing import Any

from railway_detection.data.contracts import LayerBEvent
from railway_detection.evaluation.metrics import (
    CohortEvaluationSummary,
    EventMetricsCalculator,
    SingleEventEvaluation,
)
from railway_detection.experiments.cache_provenance import (
    CACHE_REUSE_ISOLATED_RUN,
    VALID_EXPERIMENT_FAMILIES,
)
from railway_detection.experiments.frozen_config import (
    FrozenExperimentConfig,
    create_condition_config,
    load_frozen_config,
    verify_checkpoint_integrity,
    verify_timing_safeguards,
)
from railway_detection.experiments.preflight_validator import (
    build_experiment_configuration_spec,
)
from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.evidence import DecisionRecord
from railway_detection.fusion.rules import GateState
from railway_detection.simulation.failure_injector import (
    FailureInjector,
    FailureMode,
    FailureSchedule,
)
from railway_detection.simulation.gate_model import PhysicalGateModel
from railway_detection.simulation.runner import (
    EventSimulationRunner,
    SimulationRunResult,
    SimulationStep,
)
from railway_detection.utils.logging import get_logger

logger = get_logger("experiments.runner")


class BenchmarkCondition(StrEnum):
    B0 = "B0"  # Vision Only (raw frames, camera_front only)
    B1 = "B1"  # Audio Only (extracted audio only)
    B2 = "B2"  # Vision + Audio (stateless multimodal union)
    B3 = "B3"  # Temporal Evidence (dual-camera temporal filtering, stateless)
    B4 = "B4"  # Temporal + Multimodal (Full Proposed Policy: dual-cam + audio + temporal + state machine)
    B5 = "B5"  # Camera 1 (Front) Failure
    B6 = "B6"  # Camera 2 / Dual Sensor Failure
    B7 = "B7"  # Sensor / Timing / False-Detection Robustness


class ExperimentRunner:
    """Orchestrates benchmark runs across B0–B7 conditions and exports evaluation artifacts."""

    def __init__(
        self,
        output_root: str | Path = "results/experiments",
        config: FrozenExperimentConfig | None = None,
        verify_safeguards: bool = True,
    ) -> None:
        self.output_root = Path(output_root)
        self.config = config if config is not None else load_frozen_config()
        if verify_safeguards:
            verify_checkpoint_integrity(self.config)
            verify_timing_safeguards(self.config)

    def run_condition(
        self,
        condition: BenchmarkCondition | str,
        events: list[tuple[LayerBEvent, list[MultimodalFrame]]],
        sub_condition: str | None = None,
        custom_output_dir: Path | None = None,
        failure_schedules: list[FailureSchedule] | None = None,
        *,
        run_id: str | None = None,
        evaluation_mode: str = "provisional_exploratory",
        cache_reuse_policy: str = CACHE_REUSE_ISOLATED_RUN,
        stream_cache_provenance_hashes: Mapping[str, str] | None = None,
    ) -> CohortEvaluationSummary:
        """Run all events under the specified benchmark condition or sub-condition."""
        cond_str = condition.value if isinstance(condition, BenchmarkCondition) else str(condition)
        scenario_id = sub_condition if sub_condition is not None else cond_str

        out_dir = (
            custom_output_dir
            if custom_output_dir is not None
            else self.output_root / scenario_id
        )
        out_dir.mkdir(parents=True, exist_ok=True)

        # Derive condition-specific configuration with traceable overrides
        cond_config = create_condition_config(self.config, cond_str, scenario_id)

        logger.info(
            "Executing benchmark scenario %s across %d events (config_hash=%s)",
            scenario_id,
            len(events),
            cond_config.config_hash[:12],
        )
        if scenario_id == "B7e" and not failure_schedules:
            raise ValueError(
                "B7e requires explicit FailureSchedule(STALE_TIMESTAMPS, delay_s, target_source)"
            )

        evaluations: list[SingleEventEvaluation] = []

        for event, frames in events:
            gt_info = self._extract_event_ground_truth(event)

            # Filter/mutate frames for this condition/sub-condition
            cond_frames = self._prepare_frames_for_condition(
                cond_str, scenario_id, frames, failure_schedules
            )

            # Execute simulation for condition
            sim_result = self._execute_simulation(
                cond_str,
                scenario_id,
                cond_frames,
                event.event_id,
                cond_config=cond_config,
            )
            # Calculate safety metrics
            single_eval = EventMetricsCalculator.evaluate_run(
                sim_result=sim_result,
                entry_time_s=gt_info["entry_time_s"],
                clearance_time_s=gt_info["clearance_time_s"],
                has_train_ground_truth=gt_info["has_train_ground_truth"],
                exclusion_reasons=gt_info["exclusion_reasons"],
                premature_opening_window=None,
                evaluable=gt_info["evaluable"],
                ground_truth_status=gt_info["ground_truth_status"],
                cohort=gt_info["cohort"],
            )
            evaluations.append(single_eval)

        summary = EventMetricsCalculator.aggregate_cohort(evaluations)

        # Write artifacts
        summary_path = out_dir / "summary.json"
        summary_path.write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")

        records_path = out_dir / "single_events.json"
        records_data = [asdict(e) for e in evaluations]
        records_path.write_text(json.dumps(records_data, indent=2), encoding="utf-8")

        # Build complete reconstructable experiment specification
        resolved_family = (
            scenario_id
            if scenario_id in VALID_EXPERIMENT_FAMILIES
            else (cond_str if cond_str in VALID_EXPERIMENT_FAMILIES else "B1")
        )
        resolved_injector = (
            scenario_id
            if scenario_id in ("B5a", "B5b", "B5c", "B6a", "B6b", "B6c", "B7a", "B7b", "B7c", "B7d", "B7e", "B7f")
            else "none"
        )
        inj_params: dict[str, Any] = {}
        if failure_schedules:
            sched_list = []
            for sched in failure_schedules:
                sched_list.append(
                    {
                        "mode": sched.mode.value if hasattr(sched.mode, "value") else str(sched.mode),
                        "target_source": sched.target_source,
                        "start_time_s": sched.start_time_s,
                        "end_time_s": sched.end_time_s,
                        "drop_prob": sched.drop_prob,
                        "delay_s": sched.delay_s,
                        "false_conf": sched.false_conf,
                    }
                )
            inj_params["schedules"] = sched_list
            if len(failure_schedules) == 1:
                first_sched = failure_schedules[0]
                if first_sched.delay_s is not None:
                    inj_params["delay_s"] = first_sched.delay_s
                if first_sched.target_source is not None:
                    inj_params["target_source"] = first_sched.target_source
        elif resolved_injector != "none":
            inj_params["preset"] = resolved_injector

        reconstructable_spec = build_experiment_configuration_spec(
            cond_config,
            experiment_family=resolved_family,
            condition_id=scenario_id,
            run_id=run_id or f"{scenario_id}_run",
            evaluation_mode=evaluation_mode,
            failure_injector=resolved_injector,
            injector_parameters=inj_params,
            cache_reuse_policy=cache_reuse_policy,
            stream_cache_provenance_hashes=stream_cache_provenance_hashes,
        )

        # Record auditable configuration provenance
        config_meta_path = out_dir / "frozen_config_meta.json"
        config_meta_path.write_text(
            json.dumps(
                {
                    "condition": cond_str,
                    "scenario_id": scenario_id,
                    "base_config_hash": self.config.config_hash,
                    "condition_config_hash": cond_config.config_hash,
                    "condition_overrides": cond_config.condition_overrides,
                    "version": cond_config.metadata.version,
                    "reconstructable_experiment_spec": reconstructable_spec.to_dict(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        logger.info(
            "Scenario %s completed: %d events, missed_rate=%s, prem_rate=%s",
            scenario_id,
            summary.eligible_events,
            str(summary.missed_train_rate),
            str(summary.premature_opening_rate),
        )
        return summary

    @staticmethod
    def _extract_event_ground_truth(event: LayerBEvent) -> dict[str, Any]:
        """Classify event cohort and boundary ground-truth states without fabricating labels."""
        event_id_str = str(event.event_id)
        cam1_str = str(event.camera_1_path or "")
        train_type_str = (event.train_type or "").strip().lower()

        is_engine = (
            train_type_str in ("engine", "engine_only")
            or event_id_str.startswith("engine_events/")
            or "engine_events" in cam1_str
            or any(lbl.name == "engine_only" for lbl in event.labels)
        )
        if is_engine:
            return {
                "entry_time_s": None,
                "clearance_time_s": None,
                "has_train_ground_truth": False,
                "evaluable": False,
                "ground_truth_status": "engine",
                "cohort": "engine_events",
                "exclusion_reasons": {"event": "engine_event_isolated_case_study"},
            }

        is_no_train = (
            train_type_str in ("no_train", "none")
            or event_id_str.startswith("no_train_events/")
            or "no_train_events" in cam1_str
            or (
                bool(event.labels)
                and any(lbl.name == "no_train" for lbl in event.labels)
                and all(
                    lbl.name == "no_train"
                    or lbl.label_status.strip().lower()
                    in ("not_applicable", "unobservable_not_applicable")
                    for lbl in event.labels
                )
            )
        )
        if is_no_train:
            no_train_reasons: dict[str, str] = {}
            for lbl in event.labels:
                status = lbl.label_status.strip().lower()
                if status in ("censored", "uncertain", "unobservable", "unknown"):
                    no_train_reasons[lbl.name] = status
            evaluable = not bool(no_train_reasons)
            return {
                "entry_time_s": None,
                "clearance_time_s": None,
                "has_train_ground_truth": False,
                "evaluable": evaluable,
                "ground_truth_status": "confirmed_no_train",
                "cohort": "no_train_events",
                "exclusion_reasons": no_train_reasons,
            }

        if not event.labels or event.metadata_status in (
            "ground_truth_missing",
            "unannotated",
            "unverified",
        ):
            return {
                "entry_time_s": None,
                "clearance_time_s": None,
                "has_train_ground_truth": None,
                "evaluable": False,
                "ground_truth_status": "missing",
                "cohort": None,
                "exclusion_reasons": {"ground_truth": "missing"},
            }

        entry_names = {
            "crossing_entry",
            "approach_entry",
            "danger_zone_entry",
            "T1_danger_zone_entry",
        }
        clearance_names = {
            "tail_clearance",
            "clearance",
            "crossing_clearance",
            "T4_tail_clearance",
        }
        observable_statuses = {"observed", "observable"}

        entry_time_s: float | None = None
        clearance_time_s: float | None = None
        exclusion_reasons: dict[str, str] = {}

        for lbl in event.labels:
            status = (lbl.label_status or "").strip().lower()
            if lbl.name in entry_names:
                if status in observable_statuses and lbl.timestamp_s is not None:
                    entry_time_s = float(lbl.timestamp_s)
                else:
                    exclusion_reasons["T1_danger_zone_entry"] = status or "unknown"
            elif lbl.name in clearance_names:
                if status in observable_statuses and lbl.timestamp_s is not None:
                    clearance_time_s = float(lbl.timestamp_s)
                else:
                    exclusion_reasons["T4_tail_clearance"] = status or "unknown"
            else:
                if status not in observable_statuses:
                    exclusion_reasons[lbl.name] = status or "unknown"

        if entry_time_s is None and clearance_time_s is None:
            statuses = {(lbl.label_status or "").strip().lower() for lbl in event.labels}
            if statuses <= {"unknown", "missing", ""}:
                return {
                    "entry_time_s": None,
                    "clearance_time_s": None,
                    "has_train_ground_truth": None,
                    "evaluable": False,
                    "ground_truth_status": "unknown",
                    "cohort": "train_events",
                    "exclusion_reasons": exclusion_reasons or {"ground_truth": "unknown"},
                }
            return {
                "entry_time_s": None,
                "clearance_time_s": None,
                "has_train_ground_truth": True,
                "evaluable": False,
                "ground_truth_status": "confirmed_train",
                "cohort": "train_events",
                "exclusion_reasons": exclusion_reasons,
            }

        return {
            "entry_time_s": entry_time_s,
            "clearance_time_s": clearance_time_s,
            "has_train_ground_truth": True,
            "evaluable": True,
            "ground_truth_status": "confirmed_train",
            "cohort": "train_events",
            "exclusion_reasons": exclusion_reasons,
        }

    def _prepare_frames_for_condition(
        self,
        base_condition: str,
        scenario_id: str,
        frames: list[MultimodalFrame],
        custom_schedules: list[FailureSchedule] | None = None,
    ) -> list[MultimodalFrame]:
        """Transform multimodal frames to adhere to specific baseline constraints and failure injections."""
        prepared: list[MultimodalFrame] = []

        for frame in frames:
            t = frame.master_timestamp_s

            if base_condition == "B0":
                # Single camera: camera_1 / front only, strip camera_2 and audio
                v_recs = tuple(
                    r for r in frame.vision_records
                    if "camera_1" in r.source_id or "front" in r.source_id
                )
                avail = {
                    k: v for k, v in frame.source_availability.items()
                    if "camera_1" in k or "front" in k
                }
                prepared.append(
                    MultimodalFrame(
                        master_timestamp_s=t,
                        vision_records=v_recs,
                        audio_records=(),
                        source_availability=avail,
                        active_sources=tuple(s for s, a in avail.items() if a),
                    )
                )

            elif base_condition == "B1":
                # Audio only: strip all vision records
                prepared.append(
                    MultimodalFrame(
                        master_timestamp_s=t,
                        vision_records=(),
                        audio_records=frame.audio_records,
                        source_availability={
                            k: v for k, v in frame.source_availability.items()
                            if "audio" in k or "microphone" in k
                        },
                        active_sources=tuple(
                            s for s in frame.active_sources
                            if "audio" in s or "microphone" in s
                        ),
                    )
                )

            elif base_condition == "B3":
                # Temporal: Dual cameras, no audio
                prepared.append(
                    MultimodalFrame(
                        master_timestamp_s=t,
                        vision_records=frame.vision_records,
                        audio_records=(),
                        source_availability={
                            k: v for k, v in frame.source_availability.items()
                            if "audio" not in k and "microphone" not in k
                        },
                        active_sources=tuple(
                            s for s in frame.active_sources
                            if "audio" not in s and "microphone" not in s
                        ),
                    )
                )

            else:
                # B2, B4, B5, B6, B7 receive full inputs
                prepared.append(frame)

        # Apply failure injections for B5, B6, B7
        schedules = self._get_failure_schedules(scenario_id, frames, custom_schedules)
        if schedules:
            injector = FailureInjector(schedules)
            prepared = injector.inject_failures(prepared)

        return prepared

    def _get_failure_schedules(
        self,
        scenario_id: str,
        frames: list[MultimodalFrame],
        custom_schedules: list[FailureSchedule] | None = None,
    ) -> list[FailureSchedule]:
        if custom_schedules is not None:
            return custom_schedules

        duration = frames[-1].master_timestamp_s if frames else 30.0

        if scenario_id == "B5a":
            # Camera 1 dropout from event start (full duration)
            return [FailureSchedule(mode=FailureMode.CAMERA_1_DROPOUT, start_time_s=0.0, end_time_s=duration + 1.0)]

        elif scenario_id == "B5b":
            # Camera 1 dropout midway
            return [FailureSchedule(mode=FailureMode.CAMERA_1_DROPOUT, start_time_s=0.3 * duration, end_time_s=0.7 * duration)]

        elif scenario_id == "B5c":
            # Camera 1 intermittent (flapping: 2s on / 2s off)
            scheds = []
            t = 2.0
            while t < duration:
                scheds.append(FailureSchedule(mode=FailureMode.CAMERA_1_DROPOUT, start_time_s=t, end_time_s=t + 2.0))
                t += 4.0
            return scheds

        elif scenario_id == "B5":
            # Default B5: midway camera 1 dropout
            return [FailureSchedule(mode=FailureMode.CAMERA_1_DROPOUT, start_time_s=0.3 * duration, end_time_s=0.7 * duration)]

        elif scenario_id == "B6a":
            # Camera 2 dropout (full duration)
            return [FailureSchedule(mode=FailureMode.CAMERA_2_DROPOUT, start_time_s=0.0, end_time_s=duration + 1.0)]

        elif scenario_id == "B6b":
            # Both cameras fail simultaneously (full duration)
            return [FailureSchedule(mode=FailureMode.DUAL_CAMERA_DROPOUT, start_time_s=0.0, end_time_s=duration + 1.0)]

        elif scenario_id == "B6c":
            # Sequential camera failure: camera 1 at 30%, camera 2 at 60%
            return [
                FailureSchedule(mode=FailureMode.CAMERA_1_DROPOUT, start_time_s=0.3 * duration, end_time_s=duration + 1.0),
                FailureSchedule(mode=FailureMode.CAMERA_2_DROPOUT, start_time_s=0.6 * duration, end_time_s=duration + 1.0),
            ]

        elif scenario_id == "B6":
            # Default B6: dual camera failure
            return [FailureSchedule(mode=FailureMode.DUAL_CAMERA_DROPOUT, start_time_s=0.0, end_time_s=duration + 1.0)]

        elif scenario_id == "B7a":
            # Audio dropout full duration
            return [FailureSchedule(mode=FailureMode.AUDIO_DROPOUT, start_time_s=0.0, end_time_s=duration + 1.0)]

        elif scenario_id == "B7b":
            # 30% dropped frames
            return [FailureSchedule(mode=FailureMode.DROPPED_FRAMES, start_time_s=0.0, end_time_s=duration + 1.0, parameters={"drop_rate": 0.3})]

        elif scenario_id == "B7c":
            # Spurious false detection (label=front, conf=0.85)
            return [
                FailureSchedule(
                    mode=FailureMode.FALSE_DETECTION,
                    start_time_s=1.0,
                    end_time_s=2.5,
                    parameters={"label": "front", "confidence": 0.85},
                )
            ]

        elif scenario_id == "B7d":
            # Out of order frames in middle 20%
            return [FailureSchedule(mode=FailureMode.OUT_OF_ORDER_FRAMES, start_time_s=0.4 * duration, end_time_s=0.6 * duration)]

        elif scenario_id == "B7e":
            raise ValueError(
                "B7e requires explicit FailureSchedule(STALE_TIMESTAMPS, delay_s, target_source)"
            )

        elif scenario_id == "B7f":
            # Combined audio dropout + 10% frame drop
            return [
                FailureSchedule(mode=FailureMode.AUDIO_DROPOUT, start_time_s=0.0, end_time_s=duration + 1.0),
                FailureSchedule(mode=FailureMode.DROPPED_FRAMES, start_time_s=0.0, end_time_s=duration + 1.0, parameters={"drop_rate": 0.1}),
            ]

        elif scenario_id == "B7":
            # Default B7: B7f compound degradation
            return [
                FailureSchedule(mode=FailureMode.AUDIO_DROPOUT, start_time_s=0.0, end_time_s=duration + 1.0),
                FailureSchedule(mode=FailureMode.DROPPED_FRAMES, start_time_s=0.0, end_time_s=duration + 1.0, parameters={"drop_rate": 0.1}),
            ]

        return []

    def _execute_simulation(
        self,
        base_condition: str,
        scenario_id: str,
        frames: list[MultimodalFrame],
        event_id: str,
        cond_config: FrozenExperimentConfig | None = None,
    ) -> SimulationRunResult:
        """Simulate event under specific condition policy."""
        cfg = cond_config if cond_config is not None else self.config

        if base_condition in ("B4", "B5", "B6", "B7"):
            # Full deterministic state-machine policy
            runner = EventSimulationRunner(config=cfg)
            return runner.run_frames(
                frames,
                event_id=event_id,
                scenario_name=scenario_id,
                preserve_arrival_order=(scenario_id == "B7d"),
            )

        elif base_condition == "B1":
            # B1: Audio only. Invariant: Audio NEVER authorizes opening!
            # If train audio detected, trigger warning/closing; gate stays closed until manual reset.
            gate = PhysicalGateModel(
                closing_duration_s=cfg.timing.gate_closing_time_s,
                opening_duration_s=cfg.timing.gate_opening_time_s,
            )
            steps: list[SimulationStep] = []
            prev_t = frames[0].master_timestamp_s if frames else 0.0
            closed_time = 0.0

            for f in frames:
                dt = f.master_timestamp_s - prev_t
                has_train_audio = f.has_audio_evidence
                # Gate closes on audio, but NEVER opens on audio!
                command = GateState.CLOSING if has_train_audio else gate.current_state
                angle = gate.step(dt, command)
                if gate.is_passage_blocked or gate.is_fully_closed:
                    closed_time += dt

                dec = DecisionRecord(
                    timestamp_s=f.master_timestamp_s,
                    scenario_run_id=f"{event_id}_{scenario_id}",
                    previous_state="IDLE",
                    resulting_state="WARNING" if has_train_audio else "IDLE",
                    previous_gate_state=gate.current_state.value,
                    resulting_gate_state=gate.current_state.value,
                )
                steps.append(
                    SimulationStep(
                        timestamp_s=f.master_timestamp_s,
                        crossing_state=dec.resulting_state,
                        gate_state=gate.current_state.value,
                        gate_angle_deg=angle,
                        is_passage_blocked=gate.is_passage_blocked,
                        decision=dec,
                    )
                )
                prev_t = f.master_timestamp_s

            return SimulationRunResult(
                event_id=event_id,
                scenario_name=scenario_id,
                steps=steps,
                total_duration_s=prev_t - (frames[0].master_timestamp_s if frames else 0.0),
                closed_duration_s=closed_time,
                premature_opening_detected=False,
            )

        else:
            # Stateless baseline policies (B0, B2, B3)
            # Direct thresholding: closes if train detected, immediately opens when train disappears!
            # This directly proves why state machine is necessary to prevent premature opening!
            gate = PhysicalGateModel(
                closing_duration_s=cfg.timing.gate_closing_time_s,
                opening_duration_s=cfg.timing.gate_opening_time_s,
            )
            steps: list[SimulationStep] = []
            prev_t = frames[0].master_timestamp_s if frames else 0.0
            closed_time = 0.0
            premature_open = False
            train_seen = False

            # B0: 1-frame threshold on front vision
            # B2: 3-frame persistence on vision OR audio
            # B3: 2-frame persistence on dual-camera vision (confirm_frames=2)
            if base_condition == "B0":
                confirm_needed = 1
            elif base_condition == "B3":
                confirm_needed = 2
            else:
                confirm_needed = 3

            consecutive = 0

            for f in frames:
                dt = f.master_timestamp_s - prev_t
                has_det = f.has_vision_evidence or (
                    base_condition == "B2" and f.has_audio_evidence
                )

                if has_det:
                    consecutive += 1
                else:
                    consecutive = 0

                active = consecutive >= confirm_needed
                if active:
                    train_seen = True

                # Stateless flaw: opens immediately when detection drops!
                command = GateState.CLOSING if active else GateState.OPENING
                angle = gate.step(dt, command)

                if gate.is_passage_blocked or gate.is_fully_closed:
                    closed_time += dt

                # Detect stateless premature opening: train was seen, but detection temporarily dropped
                if train_seen and not active and gate.current_state in (GateState.OPENING, GateState.OPEN):
                    premature_open = True

                dec = DecisionRecord(
                    timestamp_s=f.master_timestamp_s,
                    scenario_run_id=f"{event_id}_{scenario_id}",
                    previous_state="IDLE",
                    resulting_state="TRAIN_PRESENT" if active else "IDLE",
                    previous_gate_state=gate.current_state.value,
                    resulting_gate_state=gate.current_state.value,
                )
                steps.append(
                    SimulationStep(
                        timestamp_s=f.master_timestamp_s,
                        crossing_state=dec.resulting_state,
                        gate_state=gate.current_state.value,
                        gate_angle_deg=angle,
                        is_passage_blocked=gate.is_passage_blocked,
                        decision=dec,
                    )
                )
                prev_t = f.master_timestamp_s

            return SimulationRunResult(
                event_id=event_id,
                scenario_name=scenario_id,
                steps=steps,
                total_duration_s=prev_t - (frames[0].master_timestamp_s if frames else 0.0),
                closed_duration_s=closed_time,
                premature_opening_detected=premature_open,
            )
