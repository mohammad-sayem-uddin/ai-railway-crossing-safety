"""Deterministic-testable wall-clock profiling primitives for Phase 14.

The collector measures only callable scopes explicitly wrapped by a caller.
It does not execute inference, choose a target platform, define a latency budget,
or claim real-time feasibility. Reports are local engineering measurements and
must not be interpreted as safety or target-hardware evidence.
"""

from __future__ import annotations

import math
import statistics
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class StageTimingSummary:
    """Descriptive statistics for explicitly recorded stage durations in ms."""

    sample_count: int
    mean_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float

    def to_dict(self) -> dict[str, int | float]:
        return {
            "sample_count": self.sample_count,
            "mean_ms": self.mean_ms,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "max_ms": self.max_ms,
        }


@dataclass
class StageProfiler:
    """Collect nonnegative durations using an injectable monotonic clock."""

    clock: Callable[[], float] = field(default=time.perf_counter, repr=False)
    _samples_ms: dict[str, list[float]] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if not callable(self.clock):
            raise TypeError("clock must be callable")

    def record(self, stage: str, duration_ms: float) -> None:
        """Record one already-measured duration; reject invalid measurements."""
        if not isinstance(stage, str) or not stage.strip() or stage != stage.strip():
            raise ValueError("stage must be a nonempty, trimmed string")
        if isinstance(duration_ms, bool) or not isinstance(duration_ms, (int, float)):
            raise TypeError("duration_ms must be a finite number")
        value = float(duration_ms)
        if not math.isfinite(value) or value < 0:
            raise ValueError("duration_ms must be finite and nonnegative")
        self._samples_ms.setdefault(stage, []).append(value)

    def measure(self, stage: str, operation: Callable[[], T]) -> T:
        """Measure one callable and record duration, preserving its return/error."""
        if not callable(operation):
            raise TypeError("operation must be callable")
        start = self.clock()
        try:
            return operation()
        finally:
            end = self.clock()
            duration_s = end - start
            if not math.isfinite(start) or not math.isfinite(end) or duration_s < 0:
                raise ValueError("monotonic clock returned invalid or decreasing values")
            self.record(stage, duration_s * 1000.0)

    def samples(self, stage: str) -> list[float]:
        """Return a copy of the recorded durations (ms) for one stage."""
        return list(self._samples_ms.get(stage, []))

    def summarize(self) -> dict[str, StageTimingSummary]:
        """Return deterministic nearest-rank p50/p95/p99 summaries by stage."""
        result: dict[str, StageTimingSummary] = {}
        for stage, samples in sorted(self._samples_ms.items()):
            ordered = sorted(samples)
            result[stage] = StageTimingSummary(
                sample_count=len(ordered),
                mean_ms=statistics.fmean(ordered),
                p50_ms=_nearest_rank(ordered, 0.50),
                p95_ms=_nearest_rank(ordered, 0.95),
                p99_ms=_nearest_rank(ordered, 0.99),
                max_ms=ordered[-1],
            )
        return result

    def to_report(self, *, metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Serialize measurements with explicit limits and no performance claim."""
        safe_metadata = dict(metadata or {})
        if any(not isinstance(key, str) or not key for key in safe_metadata):
            raise ValueError("metadata keys must be nonempty strings")
        return {
            "report_type": "local_engineering_profile",
            "evidence_scope": "explicitly wrapped callables only",
            "is_target_hardware_evidence": False,
            "is_safety_evidence": False,
            "metadata": safe_metadata,
            "stages": {
                name: summary.to_dict()
                for name, summary in self.summarize().items()
            },
        }


def _nearest_rank(ordered: list[float], quantile: float) -> float:
    """Nearest-rank quantile (rank ceil(p*n)); input must be nonempty/sorted."""
    if not ordered:
        raise ValueError("cannot summarize an empty sample")
    index = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[index]