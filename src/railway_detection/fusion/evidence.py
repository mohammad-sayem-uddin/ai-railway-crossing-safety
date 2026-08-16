"""Typed normalized evidence and decision output contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Modality(StrEnum):
    VISION = "vision"
    AUDIO = "audio"


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
        }
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
