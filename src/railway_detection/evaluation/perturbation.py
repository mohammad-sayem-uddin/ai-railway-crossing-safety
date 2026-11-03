"""Deterministic, replay-input-only perturbations for Phase 13 engineering tests.

These transforms accept only ``MultimodalFrame`` inputs and return new frames;
they do not modify configs, checkpoints, raw media, or ground-truth records.
Their existence does not authorize a Phase 13 experiment.
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.evidence import EvidenceRecord


class PerturbationRefused(ValueError):
    """Raised for malformed or unsafe replay perturbation requests."""


def _require_finite_number(value: object, name: str, *, positive: bool = False) -> None:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
    ):
        raise PerturbationRefused(f"{name} must be a finite number")
    if positive and value <= 0:
        raise PerturbationRefused(f"{name} must be positive")


@dataclass(frozen=True)
class PerturbationSpec:
    """Serializable declaration of one replay-input perturbation."""

    kind: str
    parameters: dict[str, Any]
    seed: int | None = None
    target: str = "replay_predictions"

    def __post_init__(self) -> None:
        if self.target != "replay_predictions":
            raise PerturbationRefused(
                "perturbations may target replay predictions only, never ground truth"
            )
        if not self.kind.strip():
            raise PerturbationRefused("perturbation kind must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "parameters": dict(self.parameters),
            "seed": self.seed,
            "target": self.target,
        }


def _validate_frames(frames: Sequence[MultimodalFrame]) -> None:
    if isinstance(frames, (str, bytes)) or not isinstance(frames, Sequence):
        raise PerturbationRefused("perturbation input must be a sequence of replay frames")
    if any(not isinstance(frame, MultimodalFrame) for frame in frames):
        raise PerturbationRefused(
            "perturbations accept MultimodalFrame replay inputs only; ground truth is refused"
        )


def apply_sensor_dropout(
    frames: Sequence[MultimodalFrame],
    *,
    source_id: str,
    start_s: float,
    duration_s: float,
) -> list[MultimodalFrame]:
    """Mark one sensor unavailable over ``[start_s, start_s + duration_s)``.

    Availability metadata is updated alongside the matching evidence record so
    the decision engine observes a genuine source dropout rather than merely
    missing detections. The input frames remain unchanged.
    """
    _validate_frames(frames)
    if not isinstance(source_id, str) or not source_id.strip():
        raise PerturbationRefused("source_id must be a nonempty string")
    _require_finite_number(start_s, "start_s")
    if start_s < 0:
        raise PerturbationRefused("start_s must be finite and non-negative")
    _require_finite_number(duration_s, "duration_s", positive=True)
    end_s = start_s + duration_s
    source_found = any(
        record.source_id == source_id
        for frame in frames
        for record in (*frame.vision_records, *frame.audio_records)
    ) or any(source_id in frame.source_availability for frame in frames)
    if not source_found:
        raise PerturbationRefused(f"source_id {source_id!r} is not present in replay frames")

    transformed: list[MultimodalFrame] = []
    for frame in frames:
        inside = start_s <= frame.master_timestamp_s < end_s
        vision_records = tuple(
            replace(record, available=False, detections=())
            if inside and record.source_id == source_id
            else record
            for record in frame.vision_records
        )
        audio_records = tuple(
            replace(record, available=False, detections=())
            if inside and record.source_id == source_id
            else record
            for record in frame.audio_records
        )
        availability = dict(frame.source_availability)
        active = frame.active_sources
        missing = frame.missing_sources
        health = dict(frame.source_health)
        reasons = dict(frame.health_reasons)
        if inside:
            availability[source_id] = False
            active = tuple(source for source in active if source != source_id)
            missing = tuple(sorted(set(missing) | {source_id}))
            health[source_id] = "unavailable"
            reasons[source_id] = "phase13_synthetic_sensor_dropout"
        transformed.append(
            replace(
                frame,
                vision_records=vision_records,
                audio_records=audio_records,
                source_availability=availability,
                active_sources=active,
                missing_sources=missing,
                source_health=health,
                health_reasons=reasons,
            )
        )
    return transformed


def apply_confidence_noise(
    frames: Sequence[MultimodalFrame], *, sigma: float, seed: int = 42
) -> list[MultimodalFrame]:
    """Apply seeded Gaussian noise to replay detection confidences only."""
    _validate_frames(frames)
    _require_finite_number(sigma, "sigma", positive=True)
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise PerturbationRefused("seed must be an integer")
    rng = random.Random(seed)

    def noise_record(record: EvidenceRecord) -> EvidenceRecord:
        if not record.available:
            return record
        if any(
            not math.isfinite(detection.confidence)
            or not 0.0 <= detection.confidence <= 1.0
            for detection in record.detections
        ):
            raise PerturbationRefused(
                "input detection confidences must be finite and within [0, 1]"
            )
        detections = tuple(
            replace(
                detection,
                confidence=min(
                    1.0,
                    max(0.0, detection.confidence + rng.gauss(0.0, sigma)),
                ),
            )
            for detection in record.detections
        )
        return replace(record, detections=detections)

    return [
        replace(
            frame,
            vision_records=tuple(noise_record(r) for r in frame.vision_records),
            audio_records=tuple(noise_record(r) for r in frame.audio_records),
        )
        for frame in frames
    ]


def apply_timing_jitter(
    frames: Sequence[MultimodalFrame], *, max_jitter_s: float, seed: int = 42
) -> list[MultimodalFrame]:
    """Jitter replay frame/evidence timestamps, never ground-truth boundaries.

    Uniform seeded jitter is bounded by ``max_jitter_s``. Requests that would
    create negative timestamps or reorder the frame timeline are refused.
    """
    _validate_frames(frames)
    _require_finite_number(max_jitter_s, "max_jitter_s", positive=True)
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise PerturbationRefused("seed must be an integer")
    timestamps = [frame.master_timestamp_s for frame in frames]
    if any(not math.isfinite(t) or t < 0 for t in timestamps):
        raise PerturbationRefused("frame timestamps must be finite and non-negative")
    if any(
        right <= left
        for left, right in zip(timestamps, timestamps[1:], strict=False)
    ):
        raise PerturbationRefused("input frames must have strictly increasing timestamps")

    rng = random.Random(seed)
    offsets = [rng.uniform(-max_jitter_s, max_jitter_s) for _ in frames]
    jittered_timestamps = [
        t + offset for t, offset in zip(timestamps, offsets, strict=True)
    ]
    if any(t < 0 for t in jittered_timestamps):
        raise PerturbationRefused("timing jitter would create a negative timestamp")
    if any(
        right <= left
        for left, right in zip(
            jittered_timestamps, jittered_timestamps[1:], strict=False
        )
    ):
        raise PerturbationRefused("timing jitter would reorder or duplicate replay frames")

    for frame, jittered_t in zip(frames, jittered_timestamps, strict=True):
        delta = jittered_t - frame.master_timestamp_s
        if any(
            not math.isfinite(record.timestamp_s)
            or record.timestamp_s + delta < 0
            for record in (*frame.vision_records, *frame.audio_records)
        ):
            raise PerturbationRefused(
                "evidence timestamps must be finite and remain non-negative after jitter"
            )

    transformed: list[MultimodalFrame] = []
    for frame, jittered_t in zip(frames, jittered_timestamps, strict=True):
        delta = jittered_t - frame.master_timestamp_s
        vision = tuple(
            replace(record, timestamp_s=record.timestamp_s + delta)
            for record in frame.vision_records
        )
        audio = tuple(
            replace(record, timestamp_s=record.timestamp_s + delta)
            for record in frame.audio_records
        )
        transformed.append(
            replace(
                frame,
                master_timestamp_s=jittered_t,
                vision_records=vision,
                audio_records=audio,
            )
        )
    return transformed


def refuse_ground_truth_perturbation(payload: object) -> None:
    """Explicitly reject a ground-truth record passed to a perturbation API."""
    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes)):
        raise PerturbationRefused(
            "ground truth cannot be perturbed; transforms require replay frames"
        )
    _validate_frames(payload)