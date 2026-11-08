"""Inter-sensor temporal alignment and master-clock synchronization."""

from __future__ import annotations

import math
from typing import Any


def _finite_number(value: object, field: str) -> float:
    """Return a finite numeric value while rejecting booleans and strings."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field} must be a finite number, got {value!r}")
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"{field} must be finite, got {value}")
    return converted


class SyncAligner:
    """Manages master-clock transformation and synchronization uncertainty for multi-sensor streams."""

    def __init__(self, tolerance_s: float = 0.5) -> None:
        tolerance = _finite_number(tolerance_s, "tolerance_s")
        if tolerance < 0.0:
            raise ValueError(f"tolerance_s must be finite and non-negative, got {tolerance_s}")
        self.tolerance_s = tolerance
        self.offsets_s: dict[str, float] = {}
        self.uncertainties_s: dict[str, float] = {}

    def add_source(
        self,
        source_id: str,
        offset_s: float | None = None,
        uncertainty_s: float | None = None,
    ) -> None:
        """Register a source with explicitly measured/declared clock metadata.

        An omitted value is not equivalent to zero.  In particular, callers
        that intend a reference clock must state ``offset_s=0.0`` explicitly,
        and must state the corresponding uncertainty.  This prevents an
        incomplete calibration record from silently becoming a zero-offset
        dual-camera alignment.
        """
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source_id must be a non-empty string")
        if offset_s is None or uncertainty_s is None:
            raise ValueError(
                "offset_s and uncertainty_s must both be explicit; missing clock metadata "
                "must not default to zero"
            )
        offset = _finite_number(offset_s, "offset_s")
        uncertainty = _finite_number(uncertainty_s, "uncertainty_s")
        if uncertainty < 0.0:
            raise ValueError(f"uncertainty_s must be finite and non-negative, got {uncertainty_s}")
        self.offsets_s[source_id] = offset
        self.uncertainties_s[source_id] = uncertainty

    def to_master(self, source_id: str, timestamp_s: float) -> float:
        """Convert a local sensor timestamp to the aligned master clock time."""
        if source_id not in self.offsets_s:
            raise ValueError(f"Unknown source stream: {source_id}")
        timestamp = _finite_number(timestamp_s, "timestamp_s")
        if timestamp < 0.0:
            raise ValueError(f"Local timestamp must be finite and non-negative, got {timestamp_s}")
        return timestamp + self.offsets_s[source_id]

    def is_aligned(self, source_id: str) -> bool:
        """True if the source uncertainty is within the allowed sync tolerance."""
        if source_id not in self.uncertainties_s:
            return False
        return self.uncertainties_s[source_id] <= self.tolerance_s

    def alignment_summary(self) -> dict[str, Any]:
        """Summary of all registered sensor streams and alignment states."""
        return {
            "tolerance_s": self.tolerance_s,
            "sources": {
                src: {
                    "offset_s": self.offsets_s[src],
                    "uncertainty_s": self.uncertainties_s[src],
                    "aligned": self.is_aligned(src),
                }
                for src in self.offsets_s
            },
        }
