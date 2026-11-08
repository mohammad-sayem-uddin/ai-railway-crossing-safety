"""Typed Phase 12 result, provenance, and failure-report contracts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from railway_detection.evaluation.input_contracts import EvidenceClassification


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON deterministically (UTF-8, sorted keys, compact separators)."""
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return (serialized + "\n").encode("utf-8")


@dataclass(frozen=True)
class EvaluationProvenance:
    schema_version: str
    phase: str
    evidence_classification: EvidenceClassification
    input_manifest_sha256: str
    source_sha256_by_event: dict[str, str]
    frozen_config_sha256: str
    decision_policy_sha256: str
    checkpoint_sha256: dict[str, str]
    seed: int
    git_commit: str | None
    official_authorization_verified: bool = False
    input_manifest_path: str | None = None
    source_path_by_event: dict[str, str] = field(default_factory=dict)
    split_identity: dict[str, tuple[str, ...]] = field(default_factory=dict)
    software_version: str = "unknown"
    environment: dict[str, Any] = field(default_factory=dict)
    command: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["evidence_classification"] = self.evidence_classification.value
        return value


@dataclass(frozen=True)
class EvaluationFailureReport:
    schema_version: str
    status: str
    evidence_classification: EvidenceClassification
    blockers: tuple[dict[str, str], ...]
    input_manifest_sha256: str | None = None
    partial_outputs_written: bool = False
    phase: str = "12"
    run_id: str | None = None
    failure_stage: str = "input_validation"
    failure_event_id: str | None = None
    failure_condition_id: str | None = None
    errors: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "evidence_classification": self.evidence_classification.value,
            "blockers": list(self.blockers),
            "input_manifest_sha256": self.input_manifest_sha256,
            "partial_outputs_written": self.partial_outputs_written,
            "phase": self.phase,
            "run_id": self.run_id,
            "failure_stage": self.failure_stage,
            "failure_event_id": self.failure_event_id,
            "failure_condition_id": self.failure_condition_id,
            "errors": list(self.errors),
        }

    def write(self, path: Path | str) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical_json_bytes(self.to_dict()))
        return destination


@dataclass(frozen=True)
class EvaluationRunOutput:
    """Serializable high-level output wrapper for engine integrations."""

    schema_version: str
    evidence_classification: EvidenceClassification
    metrics: dict[str, Any]
    provenance: EvaluationProvenance
    event_count: int
    event_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "evidence_classification": self.evidence_classification.value,
            "metrics": self.metrics,
            "provenance": self.provenance.to_dict(),
            "event_count": self.event_count,
            "event_ids": list(self.event_ids),
        }