"""Synthetic deterministic tests for Phase 14 profiling primitives only."""

from __future__ import annotations

import pytest

from railway_detection.optimization.profiler import StageProfiler


def _clock(values: list[float]):
    iterator = iter(values)
    return lambda: next(iterator)


def test_measure_records_deterministic_duration_and_returns_operation_result() -> None:
    profiler = StageProfiler(clock=_clock([1.0, 1.0125]))

    result = profiler.measure("synthetic_stage", lambda: {"synthetic": True})

    assert result == {"synthetic": True}
    summary = profiler.summarize()["synthetic_stage"]
    assert summary.sample_count == 1
    assert summary.mean_ms == pytest.approx(12.5)
    assert summary.p50_ms == summary.p95_ms == summary.p99_ms == summary.max_ms == pytest.approx(12.5)


def test_measure_records_duration_when_operation_raises_and_preserves_error() -> None:
    profiler = StageProfiler(clock=_clock([2.0, 2.001]))

    def operation():
        raise RuntimeError("synthetic failure")

    with pytest.raises(RuntimeError, match="synthetic failure"):
        profiler.measure("synthetic_failure", operation)
    assert profiler.summarize()["synthetic_failure"].sample_count == 1


def test_summary_uses_nearest_rank_and_stable_stage_order() -> None:
    profiler = StageProfiler(clock=_clock([]))
    profiler.record("z_stage", 8)
    for value in (4, 1, 3, 2):
        profiler.record("a_stage", value)

    summaries = profiler.summarize()
    assert list(summaries) == ["a_stage", "z_stage"]
    assert summaries["a_stage"].p50_ms == 2
    assert summaries["a_stage"].p95_ms == 4
    assert summaries["a_stage"].p99_ms == 4


@pytest.mark.parametrize("duration", [-0.1, float("nan"), float("inf"), True])
def test_record_rejects_invalid_durations(duration) -> None:
    profiler = StageProfiler()
    with pytest.raises((TypeError, ValueError)):
        profiler.record("synthetic_stage", duration)


@pytest.mark.parametrize("stage", ["", " padded ", None])
def test_record_rejects_invalid_stage_names(stage) -> None:
    profiler = StageProfiler()
    with pytest.raises((TypeError, ValueError)):
        profiler.record(stage, 1.0)


def test_decreasing_clock_fails_instead_of_reporting_negative_latency() -> None:
    profiler = StageProfiler(clock=_clock([5.0, 4.0]))
    with pytest.raises(ValueError, match="decreasing"):
        profiler.measure("synthetic_stage", lambda: None)


def test_report_explicitly_disclaims_target_hardware_and_safety_evidence() -> None:
    profiler = StageProfiler(clock=_clock([]))
    profiler.record("synthetic_stage", 1.0)

    report = profiler.to_report(metadata={"fixture": "synthetic"})

    assert report["report_type"] == "local_engineering_profile"
    assert report["is_target_hardware_evidence"] is False
    assert report["is_safety_evidence"] is False
    assert report["stages"]["synthetic_stage"]["sample_count"] == 1