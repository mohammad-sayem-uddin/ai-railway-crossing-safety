"""Synchronization alignment for Layer B event streams.

Normalizes source timestamps to a master clock using the recorded offset and
applies a configurable alignment-uncertainty guard. Events exceeding the
uncertainty tolerance are flagged and excluded from primary timing analyses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SyncAligner:
    """Applies per-source offsets to produce master-clock timestamps."""

    offsets_s: dict[str, float] = field(default_factory=dict)
    uncertainty_s: dict[str, float] = field(default_factory=dict)
    tolerance_s: float = 0.5

    def add_source(
        self, source_id: str, offset_s: float, uncertainty_s: float = 0.0
    ) -> None:
        if uncertainty_s < 0:
            raise ValueError("uncertainty_s must be non-negative")
        self.offsets_s[source_id] = offset_s
        self.uncertainty_s[source_id] = uncertainty_s

    def to_master(self, source_id: str, source_timestamp_s: float) -> float:
        """Convert a source timestamp to master clock time."""
        if source_id not in self.offsets_s:
            raise ValueError(f"unknown source: {source_id}")
        if source_timestamp_s < 0:
            raise ValueError("source_timestamp_s must be non-negative")
        return source_timestamp_s + self.offsets_s[source_id]

    def is_aligned(self, source_id: str) -> bool:
        """Whether this source's alignment uncertainty is within tolerance."""
        return self.uncertainty_s.get(source_id, 0.0) <= self.tolerance_s

    def alignment_summary(self) -> dict[str, Any]:
        return {
            "tolerance_s": self.tolerance_s,
            "sources": {
                source_id: {
                    "offset_s": self.offsets_s[source_id],
                    "uncertainty_s": self.uncertainty_s.get(source_id, 0.0),
                    "aligned": self.is_aligned(source_id),
                }
                for source_id in self.offsets_s
            },
        }
