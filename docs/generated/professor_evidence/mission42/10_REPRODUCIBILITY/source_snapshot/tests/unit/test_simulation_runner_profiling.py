"""Synthetic integration tests for opt-in simulation replay profiling."""

from __future__ import annotations

import importlib
import json
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pytest

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.evidence import EvidenceRecord, Modality
from railway_detection.optimization.profiler import StageProfiler
from railway_detection.simulation.runner import EventSimulationRunner

cli_main = importlib.import_module("railway_detection.cli.main")


def _frames() -> list[MultimodalFrame]:
    frames = []
    for timestamp in (0.0, 0.5, 1.0):
        frames.append(
            MultimodalFrame(
                master_timestamp_s=timestamp,
                vision_records=(
                    EvidenceRecord(timestamp, "camera_1", Modality.VISION, True),
                    EvidenceRecord(timestamp, "camera_2", Modality.VISION, True),
                ),
                audio_records=(EvidenceRecord(timestamp, "audio_1", Modality.AUDIO, True),),
                source_availability={"camera_1": True, "camera_2": True, "audio_1": True},
            )
        )
    return frames


class _IncrementingClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        self.value += 0.001
        return self.value


def test_profiling_is_opt_in_and_preserves_the_default_simulation_result() -> None:
    frames = _frames()
    baseline_runner = EventSimulationRunner()
    baseline = baseline_runner.run_frames(frames, event_id="synthetic_profile_test")
    assert baseline_runner.last_profile_report is None

    profiled_runner = EventSimulationRunner()
    profiled = profiled_runner.run_frames(
        frames,
        event_id="synthetic_profile_test",
        profiler=StageProfiler(clock=_IncrementingClock()),
    )

    assert profiled == baseline
    assert profiled_runner.last_profile_report is not None
    assert set(profiled_runner.last_profile_report["stages"]) >= {
        "frame_sorting",
        "decision_engine_reset",
        "gate_model_reset",
        "decision_evaluation",
        "gate_model_step",
        "step_recording",
        "result_aggregation",
    }
    decision_samples = profiled_runner.last_profile_report["stages"]["decision_evaluation"]
    assert decision_samples["sample_count"] == len(frames)


def test_profile_report_schema_has_replay_scope_config_and_evidence_disclaimers() -> None:
    frames = _frames()
    runner = EventSimulationRunner()
    runner.run_frames(
        frames,
        event_id="synthetic_schema_test",
        scenario_name="synthetic_scenario",
        profiler=StageProfiler(clock=_IncrementingClock()),
    )

    report = runner.last_profile_report
    assert report is not None
    assert report["report_type"] == "local_engineering_profile"
    assert report["report_schema_version"] == "1.0.0"
    assert report["measurement_classification"] == "offline_simulation_replay_only"
    assert report["is_real_hardware_benchmark"] is False
    assert report["is_target_hardware_evidence"] is False
    assert report["is_safety_evidence"] is False
    assert report["metadata"]["input_classification"] == (
        "offline_replay; synthetic provenance unverified"
    )
    assert report["metadata"]["event_id"] == "synthetic_schema_test"
    assert report["metadata"]["scenario_name"] == "synthetic_scenario"
    assert report["metadata"]["frame_count"] == len(_frames())
    assert len(report["metadata"]["frame_input_sha256"]) == 64
    assert set(report["metadata"]["source_sha256"]) == {
        "simulation_runner",
        "stage_profiler",
    }
    assert "python_version" in report["metadata"]["runtime_environment"]
    assert "platform" in report["metadata"]["runtime_environment"]
    assert report["metadata"]["configuration"]["decision_engine"]["confirm_frames"] == 2
    assert "gate_model" in report["metadata"]["configuration"]
    json.dumps(report, sort_keys=True)

    repeated_runner = EventSimulationRunner()
    repeated_runner.run_frames(
        frames,
        event_id="synthetic_schema_test",
        scenario_name="synthetic_scenario",
        profiler=StageProfiler(clock=_IncrementingClock()),
    )
    assert repeated_runner.last_profile_report == report


def test_profiler_failure_is_reported_and_does_not_change_simulation_decisions() -> None:
    class FailingProfiler(StageProfiler):
        def measure(self, stage, operation):
            raise RuntimeError(f"synthetic profiler failure: {stage}")

    frames = _frames()
    baseline = EventSimulationRunner().run_frames(frames, event_id="synthetic_failure_test")
    runner = EventSimulationRunner()
    actual = runner.run_frames(
        frames,
        event_id="synthetic_failure_test",
        profiler=FailingProfiler(clock=_IncrementingClock()),
    )

    assert actual == baseline
    report = runner.last_profile_report
    assert report is not None
    assert report["errors"]
    assert all(error["kind"] == "profiler_error" for error in report["errors"])
    assert all("synthetic profiler failure" in error["message"] for error in report["errors"])


def test_profiler_failure_after_operation_does_not_repeat_simulation_stage() -> None:
    class PostOperationFailingProfiler(StageProfiler):
        def __init__(self) -> None:
            super().__init__(clock=_IncrementingClock())
            self.operation_calls = 0

        def measure(self, stage, operation):
            self.operation_calls += 1
            result = operation()
            if stage == "decision_evaluation":
                raise RuntimeError("synthetic post-operation profiler failure")
            return result

    frames = _frames()
    baseline = EventSimulationRunner().run_frames(frames, event_id="synthetic_post_failure")
    profiler = PostOperationFailingProfiler()
    runner = EventSimulationRunner()
    actual = runner.run_frames(
        frames,
        event_id="synthetic_post_failure",
        profiler=profiler,
    )

    assert actual == baseline
    assert profiler.operation_calls == 1 + 2 + len(frames) * 3 + 1
    report = runner.last_profile_report
    assert report is not None
    assert any(
        error["kind"] == "profiler_error"
        and error["stage"] == "decision_evaluation"
        and "post-operation" in error["message"]
        for error in report["errors"]
    )


def test_profiler_that_skips_operation_is_recovered_and_reported() -> None:
    class SkippingProfiler(StageProfiler):
        def measure(self, stage, operation):
            return None

    frames = _frames()
    baseline = EventSimulationRunner().run_frames(frames, event_id="synthetic_skipped_stage")
    runner = EventSimulationRunner()
    actual = runner.run_frames(
        frames,
        event_id="synthetic_skipped_stage",
        profiler=SkippingProfiler(clock=_IncrementingClock()),
    )

    assert actual == baseline
    report = runner.last_profile_report
    assert report is not None
    assert any(error["exception_type"] == "ProfilerContractError" for error in report["errors"])


def test_profile_report_generation_failure_is_nonfatal_and_explicit() -> None:
    class ReportFailingProfiler(StageProfiler):
        def to_report(self, *, metadata=None):
            raise RuntimeError("synthetic report serialization failure")

    frames = _frames()
    baseline = EventSimulationRunner().run_frames(frames, event_id="synthetic_report_failure")
    runner = EventSimulationRunner()
    actual = runner.run_frames(
        frames,
        event_id="synthetic_report_failure",
        profiler=ReportFailingProfiler(clock=_IncrementingClock()),
    )

    assert actual == baseline
    report = runner.last_profile_report
    assert report is not None
    assert report["stages"] == {}
    assert report["errors"] == [
        {
            "kind": "profiler_report_error",
            "stage": "report",
            "exception_type": "RuntimeError",
            "message": "synthetic report serialization failure",
        }
    ]


def test_simulation_stage_error_is_recorded_and_reraised() -> None:
    class FailingDecisionEngine:
        warning_dwell_s = 2.0
        gate_closing_s = 3.0
        gate_opening_s = 3.0
        clearance_dwell_s = 3.0
        approach_threshold = 0.35
        departure_threshold = 0.35
        audio_threshold = 0.37
        confirm_frames = 2

        def reset(self, initial_time_s: float) -> None:
            pass

        def evaluate_frame(self, frame, scenario_run_id: str):
            raise RuntimeError("synthetic decision failure")

    runner = EventSimulationRunner(decision_engine=FailingDecisionEngine())  # type: ignore[arg-type]
    profiler = StageProfiler(clock=_IncrementingClock())

    with pytest.raises(RuntimeError, match="synthetic decision failure"):
        runner.run_frames(_frames(), profiler=profiler)

    report = runner.last_profile_report
    assert report is not None
    assert report["errors"] == [
        {
            "kind": "simulation_stage_error",
            "stage": "decision_evaluation",
            "exception_type": "RuntimeError",
            "message": "synthetic decision failure",
        }
    ]
    assert report["stages"]["decision_evaluation"]["sample_count"] == 1


def test_cli_profile_flag_is_optional_and_writes_separate_replay_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    event = SimpleNamespace(event_id="synthetic_cli_profile", labels=())
    load_result = SimpleNamespace(ok=True, event=event, issues=())
    monkeypatch.setattr(
        "railway_detection.data.layer_b.load_event_bundle",
        lambda *args, **kwargs: load_result,
    )
    monkeypatch.setattr(
        "railway_detection.fusion.collector.MultimodalEvidenceCollector.generate_frames_from_history",
        lambda *args, **kwargs: _frames(),
    )

    default_args = cli_main.build_parser().parse_args(
        ["simulate", "run", "--event-dir", str(tmp_path), "--output-dir", str(tmp_path / "default")]
    )
    assert default_args.profile is False
    assert cli_main._simulate_run(default_args) == 0
    assert (tmp_path / "default" / "simulation_result.json").exists()
    assert not (tmp_path / "default" / "simulation_profile.json").exists()

    enabled_args = Namespace(
        event_dir=str(tmp_path),
        scenario="synthetic_cli",
        output_dir=str(tmp_path / "profiled"),
        profile=True,
    )
    assert cli_main._simulate_run(enabled_args) == 0
    profile_path = tmp_path / "profiled" / "simulation_profile.json"
    report = json.loads(profile_path.read_text(encoding="utf-8"))
    assert report["measurement_classification"] == "offline_simulation_replay_only"
    assert report["metadata"]["event_id"] == "synthetic_cli_profile"


def test_cli_persists_profile_when_simulation_stage_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    event = SimpleNamespace(event_id="synthetic_cli_error", labels=())
    load_result = SimpleNamespace(ok=True, event=event, issues=())
    monkeypatch.setattr(
        "railway_detection.data.layer_b.load_event_bundle",
        lambda *args, **kwargs: load_result,
    )
    monkeypatch.setattr(
        "railway_detection.fusion.collector.MultimodalEvidenceCollector.generate_frames_from_history",
        lambda *args, **kwargs: _frames(),
    )

    class FailingDecisionEngine:
        warning_dwell_s = 2.0
        gate_closing_s = 3.0
        gate_opening_s = 3.0
        clearance_dwell_s = 3.0
        approach_threshold = 0.35
        departure_threshold = 0.35
        audio_threshold = 0.37
        confirm_frames = 2

        def reset(self, initial_time_s: float) -> None:
            pass

        def evaluate_frame(self, frame, scenario_run_id: str):
            raise RuntimeError("synthetic CLI simulation failure")

    monkeypatch.setattr(
        "railway_detection.simulation.runner.EventSimulationRunner",
        lambda: EventSimulationRunner(decision_engine=FailingDecisionEngine()),
    )
    output_dir = tmp_path / "failed_profiled"
    args = Namespace(
        event_dir=str(tmp_path),
        scenario="synthetic_cli_error",
        output_dir=str(output_dir),
        profile=True,
    )

    with pytest.raises(RuntimeError, match="synthetic CLI simulation failure"):
        cli_main._simulate_run(args)

    report = json.loads((output_dir / "simulation_profile.json").read_text(encoding="utf-8"))
    assert report["errors"][0]["kind"] == "simulation_stage_error"
    assert not (output_dir / "simulation_result.json").exists()
