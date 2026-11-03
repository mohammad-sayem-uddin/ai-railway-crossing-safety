"""Non-authoritative adapter from cache replay output to Phase 12 replay types.

Maps validated *synthetic cache replay* outputs to the existing EventReplay/SystemReplay
contract used by internal Phase 12 metric computation. It deliberately does not connect
to RealEventReplayProducer or Phase12EvaluationRunner and cannot manufacture provenance
required by an official phase12-replay-evidence/1 payload.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from railway_detection.evaluation.cache_only_engine import ReplayOutput
from railway_detection.evaluation.clock_aware import EventReplay, SystemReplay
from railway_detection.evaluation.input_contracts import EvidenceClassification
from railway_detection.simulation.runner import SimulationRunResult

ADAPTER_VERSION = "cache-only-phase12-adapter/1"
SUPPORTED_CONDITIONS = frozenset({"B0", "B1", "B2"})
CONDITION_STREAMS: dict[str, tuple[str, ...]] = {
    "B0": ("front_vision",),
    "B1": ("front_audio",),
    "B2": ("front_vision", "front_audio"),
}


class CachePhase12AdapterError(ValueError):
    """Structured refusal to map cache output into a Phase 12 type."""

    def __init__(self, code: str, detail: str, *, event_id: str | None = None) -> None:
        self.code = code
        self.detail = detail
        self.event_id = event_id
        suffix = f" [{event_id}]" if event_id else ""
        super().__init__(f"{code}: {detail}{suffix}")

    def to_dict(self) -> dict[str, str]:
        result = {"code": self.code, "detail": self.detail}
        if self.event_id is not None:
            result["event_id"] = self.event_id
        return result


@dataclass(frozen=True)
class CachePhase12Adaptation:
    """Synthetic-only adaptation result with explicit classification."""

    replay: EventReplay
    evidence_classification: EvidenceClassification
    adapter_version: str = ADAPTER_VERSION


def _require_nonempty(value: Any, field: str, event_id: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CachePhase12AdapterError(
            "ADAPTER_FIELD_INVALID", f"{field} must be non-empty", event_id=event_id
        )
    return value


def _validate_simulation_result(output: ReplayOutput) -> SimulationRunResult:
    event_id = _require_nonempty(output.event_id, "event_id", str(output.event_id))
    if not isinstance(output.result, SimulationRunResult):
        raise CachePhase12AdapterError(
            "SOURCE_TYPE_INVALID",
            f"ReplayOutput.result must be SimulationRunResult, got {type(output.result).__name__}",
            event_id=event_id,
        )
    result = output.result
    if result.event_id != event_id:
        raise CachePhase12AdapterError(
            "EVENT_ID_MISMATCH",
            f"source event_id {event_id!r} differs from simulation result {result.event_id!r}",
            event_id=event_id,
        )
    for field_name in ("total_duration_s", "closed_duration_s"):
        value = getattr(result, field_name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise CachePhase12AdapterError(
                "NUMERIC_FIELD_INVALID", f"{field_name} must be numeric", event_id=event_id
            )
        if not math.isfinite(value) or value < 0:
            raise CachePhase12AdapterError(
                "NUMERIC_FIELD_INVALID",
                f"{field_name} must be finite and non-negative",
                event_id=event_id,
            )
    timestamps = [step.timestamp_s for step in result.steps]
    if any(not math.isfinite(value) or value < 0 for value in timestamps):
        raise CachePhase12AdapterError(
            "TIMESTAMP_INVALID",
            "steps contain a non-finite or negative timestamp",
            event_id=event_id,
        )
    if any(right <= left for left, right in zip(timestamps, timestamps[1:], strict=False)):
        raise CachePhase12AdapterError(
            "TIMESTAMP_ORDER_INVALID",
            "step timestamps must be strictly increasing",
            event_id=event_id,
        )
    if not isinstance(output.deterministic_run_id, str) or not output.deterministic_run_id.strip():
        raise CachePhase12AdapterError(
            "PROVENANCE_INVALID", "deterministic_run_id must be non-empty", event_id=event_id
        )
    if not isinstance(output.manifest_sha256, str) or len(output.manifest_sha256) != 64:
        raise CachePhase12AdapterError(
            "PROVENANCE_INVALID",
            "manifest_sha256 must be a 64-character SHA-256",
            event_id=event_id,
        )
    if not isinstance(output.provenance, dict):
        raise CachePhase12AdapterError(
            "PROVENANCE_INVALID", "ReplayOutput.provenance must be a mapping", event_id=event_id
        )
    return result


def to_event_replay(
    output: ReplayOutput,
    *,
    cohort: str,
    evidence_classification: EvidenceClassification = EvidenceClassification.SYNTHETIC,
) -> CachePhase12Adaptation:
    """Map one validated synthetic cache result to ``EventReplay``.

    Real/official classifications are refused because this adapter has no EVAL-AUTH,
    frozen checkpoint, approved media, or ground-truth binding.
    """
    if not isinstance(output, ReplayOutput):
        raise CachePhase12AdapterError(
            "SOURCE_TYPE_INVALID", f"expected ReplayOutput, got {type(output).__name__}"
        )
    event_id = _require_nonempty(output.event_id, "event_id", str(output.event_id))
    if output.condition not in SUPPORTED_CONDITIONS:
        raise CachePhase12AdapterError(
            "CONDITION_UNSUPPORTED",
            f"condition {output.condition!r} is not one of {sorted(SUPPORTED_CONDITIONS)}",
            event_id=event_id,
        )
    try:
        classification = EvidenceClassification(evidence_classification)
    except (TypeError, ValueError) as exc:
        raise CachePhase12AdapterError(
            "CLASSIFICATION_INVALID", "unknown evidence classification", event_id=event_id
        ) from exc
    if classification is not EvidenceClassification.SYNTHETIC:
        raise CachePhase12AdapterError(
            "OFFICIAL_CONVERSION_REFUSED",
            "cache-only adapter cannot convert synthetic output into real/official evidence",
            event_id=event_id,
        )
    _require_nonempty(cohort, "cohort", event_id)
    result = _validate_simulation_result(output)
    details: dict[str, object] = {
        "adapter_version": ADAPTER_VERSION,
        "source_classification": EvidenceClassification.SYNTHETIC.value,
        "condition": output.condition,
        "streams": list(CONDITION_STREAMS[output.condition]),
        "cache_manifest_sha256": output.manifest_sha256,
        "cache_replay_run_id": output.deterministic_run_id,
        "official_evaluation_eligible": False,
        "provenance": dict(output.provenance),
    }
    system = SystemReplay(
        name="front", clock_offsets_s={"front": 0.0}, result=result, details=details
    )
    replay = EventReplay(
        event_id=event_id,
        cohort=cohort,
        camera_mode="single_camera",
        systems={"front": system},
        provenance=details,
    )
    try:
        replay.validate()
    except Exception as exc:
        raise CachePhase12AdapterError(
            "TARGET_VALIDATION_FAILED", str(exc), event_id=event_id
        ) from exc
    return CachePhase12Adaptation(replay=replay, evidence_classification=classification)


def to_official_evidence_payload(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Refuse conversion to phase12-replay-evidence/1; provenance is incomplete."""
    raise CachePhase12AdapterError(
        "PROVENANCE_INCOMPLETE",
        "cache replay output lacks frozen-config, checkpoint, media, and authorization "
        "bindings required by phase12-replay-evidence/1",
    )


def adapt_batch(
    outputs: Mapping[str, ReplayOutput],
    *,
    cohorts: Mapping[str, str],
    evidence_classification: EvidenceClassification = EvidenceClassification.SYNTHETIC,
) -> dict[str, EventReplay]:
    """Adapt a complete batch atomically; refuse without returning partial output."""
    if not isinstance(outputs, Mapping) or not outputs:
        raise CachePhase12AdapterError("BATCH_INVALID", "outputs must be a non-empty mapping")
    if set(outputs) != set(cohorts):
        raise CachePhase12AdapterError(
            "BATCH_IDENTITY_MISMATCH", "outputs and cohorts must contain exactly the same event IDs"
        )
    adapted: dict[str, EventReplay] = {}
    for event_id in sorted(outputs):
        output = outputs[event_id]
        if not isinstance(output, ReplayOutput) or output.event_id != event_id:
            raise CachePhase12AdapterError(
                "EVENT_ID_MISMATCH",
                f"batch key {event_id!r} differs from output event_id",
                event_id=event_id,
            )
        adapted[event_id] = to_event_replay(
            output, cohort=cohorts[event_id], evidence_classification=evidence_classification
        ).replay
    return adapted

