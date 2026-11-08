"""Inactive stateless-comparator admission; no scientific command table exists."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from enum import StrEnum

from railway_detection.application.contracts import EvidenceClass, canonical, synthetic_id
from railway_detection.fusion.evidence import EvidenceRecord, Modality

SCHEMA = "INACTIVE_BACK_COMPARATOR/1"


class Availability(StrEnum):
    FRESH = "FRESH"
    MISSING = "MISSING"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    RECOVERING = "RECOVERING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ProducerReference:
    controller_digest: str
    identity: str = "CONSTRUCTED_RULE_FIXTURE_NO_MODEL"
    class_mapping: tuple[str, ...] = ("front", "rear", "side")
    threshold: float = 0.35
    source_staleness_us: int = 2_000_000

    def validate(self):
        if self.identity != "CONSTRUCTED_RULE_FIXTURE_NO_MODEL" or self.class_mapping != (
            "front",
            "rear",
            "side",
        ):
            raise ValueError("exact constructed producer/class mapping required")
        if (
            self.threshold != 0.35
            or self.source_staleness_us != 2_000_000
            or type(self.source_staleness_us) is not int
        ):
            raise ValueError("producer reference cannot amend frozen context")
        if (
            type(self.controller_digest) is not str
            or len(self.controller_digest) != 64
            or any(c not in "0123456789abcdef" for c in self.controller_digest)
        ):
            raise ValueError("controller snapshot identity required")


@dataclass(frozen=True)
class ComparatorObservation:
    event: str
    observation_id: str
    source: str
    received_us: int
    observed_us: int | None
    availability: Availability
    observed_mask: int | None
    producer: ProducerReference
    camera: str = "back"
    classification: EvidenceClass = EvidenceClass.SYNTHETIC
    unknown_labels: tuple[str, ...] = ()

    def validate(self):
        synthetic_id(self.event)
        synthetic_id(self.observation_id)
        if self.camera != "back" or self.source != "camera_back":
            raise ValueError("only the explicit independent back-camera source is admitted")
        if (
            type(self.classification) is not EvidenceClass
            or self.classification != EvidenceClass.SYNTHETIC
        ):
            raise ValueError("only constructed comparator observations are admitted")
        if type(self.producer) is not ProducerReference:
            raise ValueError("typed producer reference required")
        self.producer.validate()
        if type(self.received_us) is not int or not 0 <= self.received_us <= 3_600_000_000:
            raise ValueError("exact bounded receive timestamp required")
        if self.observed_us is not None and (
            type(self.observed_us) is not int or not 0 <= self.observed_us <= self.received_us
        ):
            raise ValueError("exact source timestamp must not be future/negative")
        if type(self.availability) is not Availability:
            raise ValueError("explicit evidence availability required")
        if self.observed_mask is not None and (
            type(self.observed_mask) is not int or not 0 <= self.observed_mask < 8
        ):
            raise ValueError("mask must be integer0..7 or explicitly unavailable")
        if self.availability == Availability.MISSING:
            if self.observed_mask is not None or self.observed_us is not None:
                raise ValueError("missing evidence cannot become a positive or empty observation")
        elif self.observed_us is None:
            raise ValueError("observed evidence requires its original exact timestamp")
        age = None if self.observed_us is None else self.received_us - self.observed_us
        if self.availability == Availability.FRESH:
            if (
                self.observed_mask is None
                or self.unknown_labels
                or age is None
                or age > self.producer.source_staleness_us
            ):
                raise ValueError("invalid/unknown/stale evidence cannot become fresh")
        if self.availability == Availability.STALE and (
            age is None or age <= self.producer.source_staleness_us
        ):
            raise ValueError("staleness must match the retained producer-age context")

    @classmethod
    def from_vision(
        cls,
        record: EvidenceRecord | None,
        *,
        event: str,
        observation_id: str,
        received_us: int,
        observed_us: int | None,
        producer: ProducerReference,
    ):
        if record is None:
            result = cls(
                event,
                observation_id,
                "camera_back",
                received_us,
                observed_us,
                Availability.MISSING,
                None,
                producer,
            )
        else:
            if (
                type(record) is not EvidenceRecord
                or record.modality is not Modality.VISION
                or record.source_id != "camera_back"
                or type(record.available) is not bool
            ):
                raise ValueError("audio/front/fused evidence cannot supply back-camera commands")
            if (
                type(observed_us) is not int
                or type(record.timestamp_s) not in (float, int)
                or not math.isfinite(record.timestamp_s)
                or record.timestamp_s != observed_us / 1_000_000
            ):
                raise ValueError("exact source clock and controller clock differ")
            labels = []
            mask = 0
            for detection in record.detections:
                if type(detection.label) is not str or not detection.label.strip():
                    raise ValueError("explicit source label required")
                if (
                    type(detection.confidence) not in (float, int)
                    or not math.isfinite(detection.confidence)
                    or not 0 <= detection.confidence <= 1
                ):
                    raise ValueError("invalid confidence cannot become valid evidence")
                if detection.label not in {"front", "rear", "side"}:
                    labels.append(detection.label)
                elif detection.confidence >= producer.threshold:
                    mask |= {"front": 1, "side": 2, "rear": 4}[detection.label]
            availability = Availability.UNKNOWN if labels else Availability.FRESH
            if not record.available:
                result = cls(
                    event,
                    observation_id,
                    record.source_id,
                    received_us,
                    None,
                    Availability.MISSING,
                    None,
                    producer,
                )
            else:
                if received_us - observed_us > producer.source_staleness_us:
                    availability = Availability.STALE
                result = cls(
                    event,
                    observation_id,
                    record.source_id,
                    received_us,
                    observed_us,
                    availability,
                    None if labels else mask,
                    producer,
                    unknown_labels=tuple(sorted(labels)),
                )
        result.validate()
        return result


@dataclass(frozen=True)
class ComparatorOutcome:
    observation: ComparatorObservation
    status: str
    schema: str = SCHEMA
    decision_id: str = "M22-COMP-MAPPING"
    logical_command: None = None
    applied_command: None = None
    active: bool = False

    def __post_init__(self):
        if (
            self.active is not False
            or self.logical_command is not None
            or self.applied_command is not None
        ):
            raise ValueError("no scientific comparator mapping is adopted")
        if (
            self.schema != SCHEMA
            or self.decision_id != "M22-COMP-MAPPING"
            or self.status not in {"REJECTED_TIMESTAMP", "UNAVAILABLE_MAPPING_NOT_ADOPTED"}
        ):
            raise ValueError("inactive comparator schema/status required")

    def to_json(self):
        return canonical(asdict(self))


class InactiveComparator:
    def __init__(self, *, event: str, producer: ProducerReference):
        synthetic_id(event)
        producer.validate()
        self.event, self.producer = event, producer
        self._last: int | None = None

    def reset(self):
        self._last = None

    def evaluate(self, observation: ComparatorObservation) -> ComparatorOutcome:
        if type(observation) is not ComparatorObservation:
            raise ValueError("typed comparator observation required")
        observation.validate()
        if observation.event != self.event or observation.producer != self.producer:
            raise ValueError("event/producer substitution")
        if self._last is not None and observation.received_us <= self._last:
            return ComparatorOutcome(observation, "REJECTED_TIMESTAMP")
        self._last = observation.received_us
        return ComparatorOutcome(observation, "UNAVAILABLE_MAPPING_NOT_ADOPTED")
