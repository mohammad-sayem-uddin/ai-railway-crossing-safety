"""Benchmark and behavioral-equivalence tooling for Phase 14.

This module supplies a repeatable *procedure* (warm-up, repetitions, host
fingerprint, latency distribution) and an *equivalence check* for candidate
optimizations. It deliberately produces no performance claim:

* ``real_time_claim_permitted`` is always ``False``. A sampled percentile is
  not a worst-case execution-time bound, and no safety case exists.
* ``is_target_hardware_evidence`` is ``True`` only when the caller declared a
  target-platform fingerprint, every declared key equals the host that ran the
  measurement, and the sample size meets a minimum. A run on a development
  machine can therefore never be reported as target evidence.
* A latency budget is optional and, if given, is compared descriptively
  (``budget_observation``); it never becomes a verdict.

Reports are local engineering measurements and are never safety evidence.
"""

from __future__ import annotations

import math
import platform
import statistics
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from railway_detection.optimization.profiler import StageProfiler

MIN_TARGET_EVIDENCE_SAMPLES = 100
ACCEPTANCE_STATISTICS = ("mean_ms", "p50_ms", "p95_ms", "p99_ms", "max_ms")
INPUT_CLASSIFICATIONS = ("synthetic", "real")

# Fingerprint keys a caller may declare for a target platform.
# ``cpu_model`` is collected by the full benchmark-suite environment collector,
# while the small primitive below can only provide the portable processor string.
# Keep both names valid so a CLI target declaration is rejected only for a real
# mismatch, not because the protocol schema forgot a supported fingerprint key.
HOST_FINGERPRINT_KEYS = ("system", "machine", "processor", "cpu_model", "cpu_count")


class BenchmarkProtocolError(ValueError):
    """Invalid benchmark protocol or measurement."""


def host_fingerprint() -> dict[str, Any]:
    """Describe the machine actually running the measurement."""
    import os

    return {
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "cpu_model": platform.processor() or "unknown",
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }


@dataclass(frozen=True)
class BenchmarkProtocol:
    """Predeclared measurement procedure; nothing here is tuned after the fact."""

    warmup_iterations: int = 5
    measured_iterations: int = 30
    repetitions: int = 3
    target_platform: Mapping[str, Any] | None = None
    latency_budget_ms: float | None = None
    workload_label: str = "unspecified"
    # {"statistic": "p99_ms"|"max_ms"|"mean_ms"|"p95_ms"|"p50_ms", "limit_ms": float,
    #  "documented_in": "<repository path of the accepting document>"}. None => unresolved.
    acceptance_criterion: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        for name in ("warmup_iterations", "measured_iterations", "repetitions"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise BenchmarkProtocolError(f"{name} must be an integer")
        if self.warmup_iterations < 0:
            raise BenchmarkProtocolError("warmup_iterations must be >= 0")
        if self.measured_iterations < 1 or self.repetitions < 1:
            raise BenchmarkProtocolError("measured_iterations and repetitions must be >= 1")
        if self.latency_budget_ms is not None and (
            isinstance(self.latency_budget_ms, bool)
            or not isinstance(self.latency_budget_ms, (int, float))
            or not math.isfinite(self.latency_budget_ms)
            or self.latency_budget_ms <= 0
        ):
            raise BenchmarkProtocolError("latency_budget_ms must be a positive finite number")
        if not isinstance(self.workload_label, str) or not self.workload_label.strip():
            raise BenchmarkProtocolError("workload_label must be a nonempty string")
        if self.acceptance_criterion is not None:
            criterion = self.acceptance_criterion
            if set(criterion) != {"statistic", "limit_ms", "documented_in"}:
                raise BenchmarkProtocolError(
                    "acceptance_criterion needs exactly statistic, limit_ms, documented_in"
                )
            if criterion["statistic"] not in ACCEPTANCE_STATISTICS:
                raise BenchmarkProtocolError(
                    f"acceptance statistic must be one of {ACCEPTANCE_STATISTICS}"
                )
            limit = criterion["limit_ms"]
            if (
                isinstance(limit, bool)
                or not isinstance(limit, (int, float))
                or not math.isfinite(limit)
                or limit <= 0
            ):
                raise BenchmarkProtocolError("acceptance limit_ms must be positive and finite")
            documented = criterion["documented_in"]
            if not isinstance(documented, str) or not documented.strip():
                raise BenchmarkProtocolError(
                    "an acceptance criterion must cite the document that defines it"
                )
        if self.target_platform is not None:
            if not self.target_platform:
                raise BenchmarkProtocolError("target_platform must not be empty when given")
            unknown = sorted(set(self.target_platform) - set(HOST_FINGERPRINT_KEYS))
            if unknown:
                raise BenchmarkProtocolError(
                    f"unsupported target_platform keys {unknown}; use {list(HOST_FINGERPRINT_KEYS)}"
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "warmup_iterations": self.warmup_iterations,
            "measured_iterations": self.measured_iterations,
            "repetitions": self.repetitions,
            "target_platform": dict(self.target_platform) if self.target_platform else None,
            "latency_budget_ms": self.latency_budget_ms,
            "workload_label": self.workload_label,
            "acceptance_criterion": dict(self.acceptance_criterion)
            if self.acceptance_criterion
            else None,
        }


@dataclass
class BenchmarkResult:
    report: dict[str, Any] = field(default_factory=dict)


def _target_match(
    target: Mapping[str, Any] | None, host: Mapping[str, Any]
) -> tuple[bool, list[str]]:
    if not target:
        return False, ["no target platform declared"]
    mismatches = [
        f"{key}: target {target[key]!r} != host {host.get(key)!r}"
        for key in sorted(target)
        if target[key] != host.get(key)
    ]
    return not mismatches, mismatches


def run_benchmark(
    name: str,
    operation: Callable[[], Any],
    protocol: BenchmarkProtocol,
    *,
    clock: Callable[[], float] = time.perf_counter,
    host: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Measure ``operation`` under ``protocol`` and return a claim-free report.

    Warm-up iterations are executed and discarded (their count is recorded).
    Every repetition measures ``measured_iterations`` fresh calls; per-repetition
    medians are reported so drift between repetitions is visible. Exceptions from
    ``operation`` propagate: a failing workload yields no report.
    """
    if not isinstance(name, str) or not name.strip():
        raise BenchmarkProtocolError("benchmark name must be a nonempty string")
    if not callable(operation):
        raise BenchmarkProtocolError("operation must be callable")
    observed_host = dict(host) if host is not None else host_fingerprint()

    for _ in range(protocol.warmup_iterations):
        operation()

    profiler = StageProfiler(clock=clock)
    repetition_medians: list[float] = []
    for _ in range(protocol.repetitions):
        local = StageProfiler(clock=clock)
        for _ in range(protocol.measured_iterations):
            local.measure(name, operation)
        samples = sorted(local.samples(name))
        repetition_medians.append(statistics.median(samples))
        for value in samples:
            profiler.record(name, value)

    summary = profiler.summarize()[name]
    all_samples = profiler.samples(name)
    stdev = statistics.pstdev(all_samples) if len(all_samples) > 1 else 0.0
    mean = summary.mean_ms
    matches, mismatches = _target_match(protocol.target_platform, observed_host)
    sample_count = summary.sample_count
    target_evidence = matches and sample_count >= MIN_TARGET_EVIDENCE_SAMPLES

    budget_observation: dict[str, Any] | None = None
    if protocol.latency_budget_ms is not None:
        budget = float(protocol.latency_budget_ms)
        budget_observation = {
            "budget_ms": budget,
            "samples_over_budget": sum(1 for v in all_samples if v > budget),
            "sample_count": sample_count,
            "p99_ms": summary.p99_ms,
            "max_ms": summary.max_ms,
            "interpretation": (
                "Descriptive only. A sampled distribution is not a worst-case execution-time "
                "bound and does not establish real-time capability."
            ),
        }

    return {
        "report_type": "phase14_benchmark",
        "benchmark": name,
        "protocol": protocol.to_dict(),
        "host": observed_host,
        "warmup_iterations_discarded": protocol.warmup_iterations,
        "latency_ms": summary.to_dict(),
        "stdev_ms": stdev,
        "coefficient_of_variation": (stdev / mean) if mean > 0 else None,
        "repetition_medians_ms": repetition_medians,
        "repetition_median_spread_ms": max(repetition_medians) - min(repetition_medians),
        "budget_observation": budget_observation,
        "target_platform_declared": protocol.target_platform is not None,
        "host_matches_declared_target": matches,
        "target_mismatches": mismatches,
        "minimum_samples_for_target_evidence": MIN_TARGET_EVIDENCE_SAMPLES,
        "is_target_hardware_evidence": target_evidence,
        "is_safety_evidence": False,
        "real_time_claim_permitted": False,
        "claim_boundary": (
            "Local timing of the wrapped callable only. No real-time, latency-budget or "
            "safety conclusion may be drawn from this report."
        ),
    }


def compare_outputs_for_equivalence(
    reference: Callable[[Any], bytes],
    candidate: Callable[[Any], bytes],
    inputs: Sequence[Any],
) -> dict[str, Any]:
    """Byte-compare a reference and an optimized implementation over fixed inputs.

    Phase 14 optimizations must be behavior-preserving: the candidate is accepted
    only if every serialized output equals the reference's. Any exception or
    non-bytes return is a mismatch, never a skip.
    """
    if not inputs:
        raise BenchmarkProtocolError("equivalence check requires at least one input")
    mismatches: list[dict[str, Any]] = []
    for index, item in enumerate(inputs):
        outcome: dict[str, Any] = {"index": index}
        try:
            expected = reference(item)
            actual = candidate(item)
        except Exception as exc:  # noqa: BLE001 - recorded as a mismatch
            outcome["error"] = f"{type(exc).__name__}: {exc}"
            mismatches.append(outcome)
            continue
        if not isinstance(expected, bytes) or not isinstance(actual, bytes):
            outcome["error"] = "reference and candidate must return bytes"
            mismatches.append(outcome)
        elif expected != actual:
            first_diff = next(
                (i for i, (a, b) in enumerate(zip(expected, actual, strict=False)) if a != b),
                min(len(expected), len(actual)),
            )
            outcome.update(
                first_differing_byte=first_diff,
                reference_length=len(expected),
                candidate_length=len(actual),
            )
            mismatches.append(outcome)
    return {
        "report_type": "phase14_equivalence",
        "input_count": len(inputs),
        "equivalent": not mismatches,
        "mismatches": mismatches,
    }
