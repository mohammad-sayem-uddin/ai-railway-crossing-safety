"""End-to-end simulation runner replaying multimodal event streams."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, TypeVar

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.evidence import DecisionRecord
from railway_detection.fusion.rules import CrossingState, GateState, RuleId
from railway_detection.optimization.profiler import StageProfiler
from railway_detection.simulation.gate_model import PhysicalGateModel
from railway_detection.utils.logging import get_logger

logger = get_logger("simulation.runner")
_T = TypeVar("_T")


@dataclass(frozen=True)
class SimulationStep:
    """State record for a single simulation time step."""

    timestamp_s: float
    crossing_state: str
    gate_state: str
    gate_angle_deg: float
    is_passage_blocked: bool
    decision: DecisionRecord


@dataclass
class SimulationRunResult:
    """Aggregate results and metrics from an event simulation replay."""

    event_id: str
    scenario_name: str
    steps: list[SimulationStep] = field(default_factory=list)
    total_duration_s: float = 0.0
    closed_duration_s: float = 0.0
    warning_lead_time_s: float | None = None
    premature_opening_detected: bool = False
    fault_occurred: bool = False
    metrics: dict[str, Any] = field(default_factory=dict)
    rejected_steps: list[SimulationStep] = field(default_factory=list)


class EventSimulationRunner:
    """Executes replay simulations by running frames through the decision engine and gate model."""

    def __init__(
        self,
        decision_engine: MultimodalDecisionEngine | None = None,
        gate_model: PhysicalGateModel | None = None,
        config: Any | None = None,
    ) -> None:
        self.config = config
        if decision_engine is not None:
            self.decision_engine = decision_engine
        elif config is not None:
            self.decision_engine = MultimodalDecisionEngine(config=config)
        else:
            self.decision_engine = MultimodalDecisionEngine()

        if gate_model is not None:
            self.gate_model = gate_model
        elif config is not None:
            self.gate_model = PhysicalGateModel(
                closing_duration_s=config.timing.gate_closing_s,
                opening_duration_s=config.timing.gate_opening_s,
            )
        else:
            self.gate_model = PhysicalGateModel()
        self.last_profile_report: dict[str, Any] | None = None

    def run_frames_convention_b(self, request):
        """Explicit constructed-only B path; historical run_frames remains A."""
        from railway_detection.synthetic.convention_b_pipeline import run_pipeline

        return run_pipeline(request, self.decision_engine)

    def run_frames(
        self,
        frames: list[MultimodalFrame],
        event_id: str = "event_001",
        scenario_name: str = "normal",
        entry_time_s: float | None = None,
        clearance_time_s: float | None = None,
        profiler: StageProfiler | None = None,
        preserve_arrival_order: bool = False,
    ) -> SimulationRunResult:
        """Replay frames; profiling is opt-in and cannot alter simulation outcomes.

        When ``profiler`` is supplied, timing/reporting failures are captured in
        ``last_profile_report`` and do not prevent a simulation stage from running
        exactly once. Exceptions raised by the simulation itself are re-raised.
        """
        self.last_profile_report = None
        profile_errors: list[dict[str, str]] = []
        if profiler is None:
            return self._run_frames(
                frames,
                event_id,
                scenario_name,
                entry_time_s,
                clearance_time_s,
                profile_stage=None,
                preserve_arrival_order=preserve_arrival_order,
            )

        try:
            metadata = self._profile_metadata(
                frames,
                event_id,
                scenario_name,
                entry_time_s,
                clearance_time_s,
                profile_errors,
            )
        except Exception as exc:
            profile_errors.append(_error_record("profiler_metadata_error", "metadata", exc))
            metadata = {
                "measurement_kind": "offline_simulation_replay_runtime",
                "input_classification": "offline_replay; synthetic provenance unverified",
                "event_id": event_id,
                "scenario_name": scenario_name,
                "frame_count": len(frames),
                "input_fingerprint_error": "unable to compute frame fingerprint",
                "configuration": {},
            }

        def profile_stage(stage: str, operation: Callable[[], _T]) -> _T:
            return self._run_profiled_stage(profiler, stage, operation, profile_errors)

        try:
            return self._run_frames(
                frames,
                event_id,
                scenario_name,
                entry_time_s,
                clearance_time_s,
                profile_stage=profile_stage,
                preserve_arrival_order=preserve_arrival_order,
            )
        finally:
            self.last_profile_report = self._build_profile_report(
                profiler, metadata, profile_errors
            )

    def _run_frames(
        self,
        frames: list[MultimodalFrame],
        event_id: str,
        scenario_name: str,
        entry_time_s: float | None,
        clearance_time_s: float | None,
        profile_stage: Callable[[str, Callable[[], _T]], _T] | None,
        preserve_arrival_order: bool = False,
    ) -> SimulationRunResult:
        def stage(name: str, operation: Callable[[], _T]) -> _T:
            if profile_stage is None:
                return operation()
            return profile_stage(name, operation)

        if not frames:
            return SimulationRunResult(event_id=event_id, scenario_name=scenario_name)

        sorted_frames = frames if preserve_arrival_order else stage(
            "frame_sorting", lambda: sorted(frames, key=lambda f: f.master_timestamp_s)
        )
        stage(
            "decision_engine_reset",
            lambda: self.decision_engine.reset(initial_time_s=sorted_frames[0].master_timestamp_s),
        )
        stage("gate_model_reset", lambda: self.gate_model.reset(angle_deg=90.0))

        steps: list[SimulationStep] = []
        rejected_steps: list[SimulationStep] = []
        prev_t = sorted_frames[0].master_timestamp_s
        total_closed_time = 0.0
        first_warning_time: float | None = None
        fault_seen = False
        premature_open = False

        for frame in sorted_frames:
            t = frame.master_timestamp_s
            dt = max(0.0, t - prev_t)

            # Evaluate decision engine
            decision = stage(
                "decision_evaluation",
                lambda frame=frame: self.decision_engine.evaluate_frame(
                    frame, scenario_run_id=f"{event_id}_{scenario_name}"
                ),
            )

            # Rule 8 (out-of-order) and Rule 10 (duplicate frame) reject the frame
            # without advancing the master clock or mutating crossing/gate state.
            if decision.rule_id in (
                RuleId.RULE_8_OUT_OF_ORDER_REJECTION.value,
                RuleId.RULE_10_DUPLICATE_FRAME_REJECTION.value,
            ):
                fault_seen = True
                current_angle = self.gate_model.current_angle_deg
                stage(
                    "step_recording",
                    lambda t=t, decision=decision, current_angle=current_angle: rejected_steps.append(
                        SimulationStep(
                            timestamp_s=t,
                            crossing_state=decision.resulting_state,
                            gate_state=self.gate_model.current_state.value,
                            gate_angle_deg=current_angle,
                            is_passage_blocked=self.gate_model.is_passage_blocked,
                            decision=decision,
                        )
                    ),
                )
                continue

            # Map decision to gate command
            commanded_gate = GateState(decision.resulting_gate_state)

            # Step physical gate model
            angle = stage(
                "gate_model_step",
                lambda dt=dt, commanded_gate=commanded_gate: self.gate_model.step(
                    dt, commanded_gate
                ),
            )

            # Track metrics
            if self.gate_model.is_passage_blocked or self.gate_model.is_fully_closed:
                total_closed_time += dt

            if (
                decision.resulting_state == CrossingState.WARNING.value
                and first_warning_time is None
            ):
                first_warning_time = t

            if decision.fault_status not in ("none", "", None):
                fault_seen = True

            # Check premature opening before ground-truth clearance.
            if (
                entry_time_s is not None
                and clearance_time_s is not None
                and entry_time_s <= t < clearance_time_s
            ):
                if self.gate_model.current_state in (GateState.OPENING, GateState.OPEN):
                    if not self.gate_model.is_passage_blocked:
                        premature_open = True

            stage(
                "step_recording",
                lambda t=t, decision=decision, angle=angle: steps.append(
                    SimulationStep(
                        timestamp_s=t,
                        crossing_state=decision.resulting_state,
                        gate_state=self.gate_model.current_state.value,
                        gate_angle_deg=angle,
                        is_passage_blocked=self.gate_model.is_passage_blocked,
                        decision=decision,
                    )
                )
            )
            prev_t = t

        def build_result() -> SimulationRunResult:
            warning_lead_time = None
            if first_warning_time is not None and entry_time_s is not None:
                warning_lead_time = max(0.0, entry_time_s - first_warning_time)

            total_duration = prev_t - sorted_frames[0].master_timestamp_s
            out_of_order_rejected = sum(
                1
                for s in rejected_steps
                if s.decision.rule_id == RuleId.RULE_8_OUT_OF_ORDER_REJECTION.value
            )
            return SimulationRunResult(
                event_id=event_id,
                scenario_name=scenario_name,
                steps=steps,
                total_duration_s=total_duration,
                closed_duration_s=total_closed_time,
                warning_lead_time_s=warning_lead_time,
                premature_opening_detected=premature_open,
                fault_occurred=fault_seen,
                metrics={
                    "step_count": len(steps),
                    "rejected_step_count": len(rejected_steps),
                    "out_of_order_rejected_count": out_of_order_rejected,
                    "total_duration_s": total_duration,
                    "closed_duration_s": total_closed_time,
                    "warning_lead_time_s": warning_lead_time,
                    "premature_opening_detected": premature_open,
                    "fault_occurred": fault_seen,
                },
                rejected_steps=rejected_steps,
            )

        result = stage("result_aggregation", build_result)
        return result

    def _profile_metadata(
        self,
        frames: list[MultimodalFrame],
        event_id: str,
        scenario_name: str,
        entry_time_s: float | None,
        clearance_time_s: float | None,
        errors: list[dict[str, str]],
    ) -> dict[str, Any]:
        frame_input_sha256: str | None
        try:
            frame_payload = json.dumps(
                [asdict(frame) for frame in frames], sort_keys=True, separators=(",", ":")
            )
            frame_input_sha256 = hashlib.sha256(frame_payload.encode("utf-8")).hexdigest()
        except (TypeError, ValueError) as exc:
            frame_input_sha256 = None
            errors.append(_error_record("input_fingerprint_error", "metadata", exc))
        profiler_path = Path(__file__).parents[1] / "optimization" / "profiler.py"
        metadata: dict[str, Any] = {
            "measurement_kind": "offline_simulation_replay_runtime",
            "input_classification": "offline_replay; synthetic provenance unverified",
            "event_id": event_id,
            "scenario_name": scenario_name,
            "frame_count": len(frames),
            "frame_input_sha256": frame_input_sha256,
            "frame_fingerprint_method": (
                "sha256(canonical_json(dataclass frames))" if frame_input_sha256 else None
            ),
            "entry_time_s": entry_time_s,
            "clearance_time_s": clearance_time_s,
            "model_checkpoint_use": "none; runner replays precomputed frames",
            "source_sha256": {
                "simulation_runner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "stage_profiler": hashlib.sha256(profiler_path.read_bytes()).hexdigest(),
            },
            "runtime_environment": {
                "python_version": platform.python_version(),
                "platform": sys.platform,
                "machine": platform.machine(),
            },
            "runner_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "profiler_class": f"{type(self).__module__}.{type(self).__qualname__}",
            "configuration": {
                "config_hash": getattr(self.config, "canonical_hash", None),
                "decision_engine": {
                    "warning_dwell_s": getattr(self.decision_engine, "warning_dwell_s", None),
                    "gate_closing_s": getattr(self.decision_engine, "gate_closing_s", None),
                    "gate_opening_s": getattr(self.decision_engine, "gate_opening_s", None),
                    "clearance_dwell_s": getattr(self.decision_engine, "clearance_dwell_s", None),
                    "approach_threshold": getattr(self.decision_engine, "approach_threshold", None),
                    "departure_threshold": getattr(
                        self.decision_engine, "departure_threshold", None
                    ),
                    "audio_threshold": getattr(self.decision_engine, "audio_threshold", None),
                    "confirm_frames": getattr(self.decision_engine, "confirm_frames", None),
                },
                "gate_model": {
                    "closing_duration_s": getattr(self.gate_model, "closing_duration_s", None),
                    "opening_duration_s": getattr(self.gate_model, "opening_duration_s", None),
                },
            },
        }
        if metadata["configuration"]["config_hash"] is None:
            metadata["configuration"].pop("config_hash")
        return metadata

    @staticmethod
    def _run_profiled_stage(
        profiler: StageProfiler,
        stage: str,
        operation: Callable[[], _T],
        errors: list[dict[str, str]],
    ) -> _T:
        """Use StageProfiler, isolating its failures from the operation itself."""
        state: dict[str, Any] = {"called": False, "result": None, "error": None}

        def once():
            if state["called"]:
                if state["error"] is not None:
                    raise state["error"]
                return state["result"]
            state["called"] = True
            try:
                state["result"] = operation()
                return state["result"]
            except BaseException as exc:
                state["error"] = exc
                raise

        try:
            profiler.measure(stage, once)
        except Exception as profile_exc:
            if state["error"] is not None:
                simulation_exc = state["error"]
                errors.append(_error_record("simulation_stage_error", stage, simulation_exc))
                if simulation_exc is profile_exc:
                    raise simulation_exc from None
                raise simulation_exc from profile_exc
            errors.append(_error_record("profiler_error", stage, profile_exc))
            if state["called"]:
                return state["result"]
            try:
                return once()
            except BaseException as simulation_exc:
                errors.append(_error_record("simulation_stage_error", stage, simulation_exc))
                raise

        if state["error"] is not None:
            simulation_exc = state["error"]
            errors.append(_error_record("simulation_stage_error", stage, simulation_exc))
            raise simulation_exc
        if not state["called"]:
            errors.append(
                {
                    "kind": "profiler_error",
                    "stage": stage,
                    "exception_type": "ProfilerContractError",
                    "message": "profiler returned without invoking the operation",
                }
            )
            try:
                return once()
            except BaseException as simulation_exc:
                errors.append(_error_record("simulation_stage_error", stage, simulation_exc))
                raise
        # Use the operation's actual return value, not a potentially altered profiler return.
        return state["result"]

    @staticmethod
    def _build_profile_report(
        profiler: StageProfiler,
        metadata: dict[str, Any],
        errors: list[dict[str, str]],
    ) -> dict[str, Any]:
        try:
            report = profiler.to_report(metadata=metadata)
            report["report_schema_version"] = "1.0.0"
            report["measurement_classification"] = "offline_simulation_replay_only"
            report["is_real_hardware_benchmark"] = False
            report["errors"] = list(errors)
            return report
        except Exception as exc:
            fallback_errors = [*errors, _error_record("profiler_report_error", "report", exc)]
            return {
                "report_type": "local_engineering_profile",
                "report_schema_version": "1.0.0",
                "evidence_scope": "explicitly wrapped callables only",
                "measurement_classification": "offline_simulation_replay_only",
                "is_target_hardware_evidence": False,
                "is_safety_evidence": False,
                "is_real_hardware_benchmark": False,
                "metadata": metadata,
                "stages": {},
                "errors": fallback_errors,
            }


def _error_record(kind: str, stage: str, error: BaseException) -> dict[str, str]:
    return {
        "kind": kind,
        "stage": stage,
        "exception_type": type(error).__name__,
        "message": str(error),
    }
