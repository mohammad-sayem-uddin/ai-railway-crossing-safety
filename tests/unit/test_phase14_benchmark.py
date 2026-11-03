"""Phase 14 benchmark procedure and equivalence checks (deterministic clocks only)."""

from __future__ import annotations

import pytest

from railway_detection.optimization.benchmark import (
    MIN_TARGET_EVIDENCE_SAMPLES,
    BenchmarkProtocol,
    BenchmarkProtocolError,
    compare_outputs_for_equivalence,
    run_benchmark,
)

HOST = {"system": "Linux", "machine": "aarch64", "processor": "x", "cpu_count": 4}


class StepClock:
    """Each call advances by the next scripted step (seconds)."""

    def __init__(self, durations_s):
        self._durations = list(durations_s)
        self._now = 0.0
        self._pending = None

    def __call__(self):
        if self._pending is None:
            self._pending = self._durations.pop(0)
            return self._now
        self._now += self._pending
        self._pending = None
        return self._now


def test_warmup_is_executed_but_excluded_from_measurements():
    calls = []
    clock = StepClock([0.002] * 6)
    report = run_benchmark(
        "op",
        lambda: calls.append(1),
        BenchmarkProtocol(warmup_iterations=3, measured_iterations=3, repetitions=2),
        clock=clock,
        host=HOST,
    )
    assert len(calls) == 3 + 3 * 2
    assert report["latency_ms"]["sample_count"] == 6
    assert report["warmup_iterations_discarded"] == 3
    assert report["latency_ms"]["mean_ms"] == pytest.approx(2.0)
    assert report["repetition_medians_ms"] == [pytest.approx(2.0)] * 2


def test_report_never_permits_real_time_or_safety_claims():
    report = run_benchmark(
        "op",
        lambda: None,
        BenchmarkProtocol(
            warmup_iterations=0,
            measured_iterations=MIN_TARGET_EVIDENCE_SAMPLES,
            repetitions=1,
            target_platform={"system": "Linux"},
            latency_budget_ms=200.0,
        ),
        clock=StepClock([0.001] * MIN_TARGET_EVIDENCE_SAMPLES),
        host=HOST,
    )
    assert report["is_target_hardware_evidence"] is True  # declared target matches the host
    assert report["real_time_claim_permitted"] is False
    assert report["is_safety_evidence"] is False
    assert report["budget_observation"]["samples_over_budget"] == 0
    assert "worst-case" in report["budget_observation"]["interpretation"]


def test_development_host_is_never_reported_as_target_hardware():
    protocol = BenchmarkProtocol(
        warmup_iterations=0,
        measured_iterations=MIN_TARGET_EVIDENCE_SAMPLES,
        repetitions=1,
        target_platform={"machine": "armv7l"},
    )
    report = run_benchmark(
        "op", lambda: None, protocol, clock=StepClock([0.001] * 100), host=HOST
    )
    assert report["host_matches_declared_target"] is False
    assert report["is_target_hardware_evidence"] is False
    assert "armv7l" in report["target_mismatches"][0]


def test_no_declared_target_or_too_few_samples_is_not_target_evidence():
    undeclared = run_benchmark(
        "op",
        lambda: None,
        BenchmarkProtocol(warmup_iterations=0, measured_iterations=5, repetitions=1),
        clock=StepClock([0.001] * 5),
        host=HOST,
    )
    assert undeclared["is_target_hardware_evidence"] is False
    assert undeclared["target_platform_declared"] is False
    short = run_benchmark(
        "op",
        lambda: None,
        BenchmarkProtocol(
            warmup_iterations=0,
            measured_iterations=5,
            repetitions=1,
            target_platform={"system": "Linux"},
        ),
        clock=StepClock([0.001] * 5),
        host=HOST,
    )
    assert short["host_matches_declared_target"] is True
    assert short["is_target_hardware_evidence"] is False


def test_budget_exceedance_is_counted_descriptively():
    report = run_benchmark(
        "op",
        lambda: None,
        BenchmarkProtocol(
            warmup_iterations=0, measured_iterations=4, repetitions=1, latency_budget_ms=2.5
        ),
        clock=StepClock([0.001, 0.003, 0.004, 0.002]),
        host=HOST,
    )
    assert report["budget_observation"]["samples_over_budget"] == 2
    assert report["real_time_claim_permitted"] is False


def test_failing_workload_yields_no_report():
    def boom():
        raise RuntimeError("workload failed")

    with pytest.raises(RuntimeError):
        run_benchmark(
            "op",
            boom,
            BenchmarkProtocol(warmup_iterations=0, measured_iterations=1, repetitions=1),
            host=HOST,
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"warmup_iterations": -1},
        {"measured_iterations": 0},
        {"repetitions": 0},
        {"warmup_iterations": True},
        {"latency_budget_ms": 0},
        {"latency_budget_ms": float("nan")},
        {"workload_label": " "},
        {"target_platform": {}},
        {"target_platform": {"gpu": "x"}},
    ],
)
def test_protocol_validation(kwargs):
    with pytest.raises(BenchmarkProtocolError):
        BenchmarkProtocol(**kwargs)


def test_equivalence_accepts_identical_and_rejects_any_difference():
    reference = lambda x: f"{x}".encode()  # noqa: E731
    assert compare_outputs_for_equivalence(reference, reference, [1, 2, 3])["equivalent"] is True

    def drifting(x):
        return b"9" if x == 2 else f"{x}".encode()

    report = compare_outputs_for_equivalence(reference, drifting, [1, 2, 3])
    assert report["equivalent"] is False
    assert report["mismatches"][0]["index"] == 1
    assert report["mismatches"][0]["first_differing_byte"] == 0


def test_equivalence_treats_errors_and_non_bytes_as_mismatches():
    ok = lambda x: b"a"  # noqa: E731

    def raises(x):
        raise ValueError("optimized path crashed")

    crashed = compare_outputs_for_equivalence(ok, raises, [1])
    assert "ValueError" in crashed["mismatches"][0]["error"]
    wrong_type = compare_outputs_for_equivalence(ok, lambda x: "a", [1])
    assert "bytes" in wrong_type["mismatches"][0]["error"]
    with pytest.raises(BenchmarkProtocolError):
        compare_outputs_for_equivalence(ok, ok, [])


def test_synthetic_replay_benchmark_runs_end_to_end_without_claims(tmp_path):
    from railway_detection.fusion.collector import MultimodalEvidenceCollector
    from railway_detection.simulation.runner import EventSimulationRunner

    frames = MultimodalEvidenceCollector().generate_frames_from_history(0.0, 4.0, stride_s=0.5)
    runner = EventSimulationRunner()

    def replay():
        runner.run_frames(
            frames=list(frames),
            event_id="bench",
            scenario_name="bench",
            entry_time_s=None,
            clearance_time_s=None,
        )

    report = run_benchmark(
        "simulation_replay",
        replay,
        BenchmarkProtocol(warmup_iterations=1, measured_iterations=3, repetitions=2),
    )
    assert report["latency_ms"]["sample_count"] == 6
    assert report["real_time_claim_permitted"] is False
    assert report["is_target_hardware_evidence"] is False
