"""Typed normalized evidence and decision output contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Modality(StrEnum):
    VISION = "vision"
    AUDIO = "audio"


class EvidenceStatus(StrEnum):
    """Fine-grained semantic status for a source observation at master time t."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNAVAILABLE = "unavailable"
    MISSING = "missing"
    STALE = "stale"
    DEGRADED = "degraded"
    CONTRADICTORY = "contradictory"
    UNKNOWN = "unknown"


class OccupancyState(StrEnum):
    """Explicit crossing-zone occupancy semantics for Layer 4 / Final Clearance."""

    OCCUPIED = "occupied"
    CLEAR = "clear"
    UNKNOWN = "unknown"
    MISSING = "missing"
    CONTRADICTORY = "contradictory"


@dataclass(frozen=True)
class OccupancyEvidence:
    """Typed evidence record from a dedicated or derived crossing occupancy verifier."""

    timestamp_s: float
    source_id: str
    state: OccupancyState
    available: bool = True
    confidence: float | None = None
    evidence_status: EvidenceStatus = EvidenceStatus.UNKNOWN
    explanation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp_s < 0:
            raise ValueError("timestamp_s must be non-negative")
        if not self.available and self.state in (OccupancyState.OCCUPIED, OccupancyState.CLEAR):
            raise ValueError("unavailable occupancy evidence cannot assert OCCUPIED or CLEAR")


def classify_evidence_status(
    *,
    fresh_record: EvidenceRecord | None,
    health: str | None = None,
    health_reason: str | None = None,
    age_s: float | None = None,
    stale_after_s: float | None = None,
    contradictory: bool = False,
) -> EvidenceStatus:
    """Resolve explicit EvidenceStatus distinguishing positive, negative, unavailable, missing, stale, degraded, contradictory, and unknown."""
    if contradictory:
        return EvidenceStatus.CONTRADICTORY
    if fresh_record is not None:
        if not fresh_record.available:
            return EvidenceStatus.UNAVAILABLE
        if fresh_record.detections:
            return EvidenceStatus.POSITIVE
        return EvidenceStatus.NEGATIVE

    normalized_health = (health or "").lower()
    normalized_reason = (health_reason or "").lower()
    if normalized_health in {"missing"} or normalized_reason == "input_missing":
        return EvidenceStatus.MISSING
    if normalized_health in {"stale"} or normalized_reason == "timeout_stale":
        return EvidenceStatus.STALE
    if normalized_health in {"failed"}:
        return EvidenceStatus.UNAVAILABLE
    if normalized_health in {"degraded", "recovering"}:
        return EvidenceStatus.DEGRADED
    if (
        stale_after_s is not None
        and age_s is not None
        and age_s != float("inf")
        and age_s > stale_after_s
        and normalized_reason != "initializing"
    ):
        return EvidenceStatus.STALE
    return EvidenceStatus.UNKNOWN


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceRecord:
    timestamp_s: float
    source_id: str
    modality: Modality
    available: bool
    detections: tuple[Detection, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp_s < 0:
            raise ValueError("timestamp_s must be non-negative")
        if not self.available and self.detections:
            raise ValueError("unavailable evidence must not contain detections")


@dataclass(frozen=True)
class DecisionRecord:
    timestamp_s: float
    scenario_run_id: str
    previous_state: str
    resulting_state: str
    previous_gate_state: str
    resulting_gate_state: str
    evidence_references: tuple[str, ...] = ()
    rule_id: str | None = None
    explanation: str | None = None
    fault_status: str = "none"
    source_availability: dict[str, bool] = field(default_factory=dict)
    source_health: dict[str, str] = field(default_factory=dict)
    health_reasons: dict[str, str] = field(default_factory=dict)
    observation_ages: dict[str, float] = field(default_factory=dict)
    gate_command: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "timestamp_s": self.timestamp_s,
            "scenario_run_id": self.scenario_run_id,
            "previous_state": self.previous_state,
            "resulting_state": self.resulting_state,
            "previous_gate_state": self.previous_gate_state,
            "resulting_gate_state": self.resulting_gate_state,
            "fault_status": self.fault_status,
            "source_availability": self.source_availability,
            "source_health": self.source_health,
            "health_reasons": self.health_reasons,
            "observation_ages": self.observation_ages,
        }
        if self.gate_command is not None:
            data["gate_command"] = self.gate_command
        if self.evidence_references:
            data["evidence_references"] = list(self.evidence_references)
        if self.rule_id is not None:
            data["rule_id"] = self.rule_id
        if self.explanation is not None:
            data["explanation"] = self.explanation
        return data


@dataclass(frozen=True)
class UnavailableSource:
    source_id: str
    modality: Modality
    reason: str

    def to_evidence(self, timestamp_s: float) -> EvidenceRecord:
        return EvidenceRecord(
            timestamp_s=timestamp_s,
            source_id=self.source_id,
            modality=self.modality,
            available=False,
            metadata={"reason": self.reason},
        )
