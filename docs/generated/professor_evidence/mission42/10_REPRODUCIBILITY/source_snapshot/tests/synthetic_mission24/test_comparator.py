from dataclasses import replace
from itertools import product

import pytest

from railway_detection.application.comparator import (
    Availability,
    ComparatorObservation,
    InactiveComparator,
    ProducerReference,
)
from railway_detection.application.contracts import EvidenceClass
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality

EVENT = "synthetic:m24:event"
PRODUCER = ProducerReference("a" * 64)


def observation(mask, t=100_000, availability=Availability.FRESH):
    observed = 0 if availability == Availability.STALE else t
    received = 2_000_001 if availability == Availability.STALE else t
    return ComparatorObservation(
        EVENT,
        "synthetic:obs:" + str(t),
        "camera_back",
        received,
        observed,
        availability,
        mask,
        PRODUCER,
    )


@pytest.mark.parametrize("first,second", tuple(product(range(8), repeat=2)))
def test_all_mask_transitions_inactive_and_reset_deterministic(first, second):
    service = InactiveComparator(event=EVENT, producer=PRODUCER)
    a = service.evaluate(observation(first))
    b = service.evaluate(observation(second, 200_000))
    assert a.status == b.status == "UNAVAILABLE_MAPPING_NOT_ADOPTED"
    assert not a.active and a.logical_command is None and b.applied_command is None
    service.reset()
    assert service.evaluate(observation(first)).to_json() == a.to_json()


@pytest.mark.parametrize(
    "mask,availability",
    tuple(
        product(
            range(8),
            [
                Availability.FRESH,
                Availability.STALE,
                Availability.DEGRADED,
                Availability.RECOVERING,
                Availability.UNKNOWN,
            ],
        )
    ),
)
def test_all_masks_across_observed_availability_states(mask, availability):
    result = InactiveComparator(event=EVENT, producer=PRODUCER).evaluate(
        observation(mask, availability=availability)
    )
    assert result.observation.observed_mask == mask
    assert result.logical_command is None and not result.active


@pytest.mark.parametrize("mask", range(8))
def test_missing_cannot_become_any_observed_mask(mask):
    row = ComparatorObservation(
        EVENT, "synthetic:missing", "camera_back", 0, None, Availability.MISSING, mask, PRODUCER
    )
    with pytest.raises(ValueError, match="missing evidence"):
        row.validate()


@pytest.mark.parametrize("mask", range(8))
def test_masks_come_from_complete_simultaneous_set_without_tie_break(mask):
    labels = [label for label, bit in (("front", 1), ("side", 2), ("rear", 4)) if mask & bit]
    record = EvidenceRecord(
        0.1, "camera_back", Modality.VISION, True, tuple(Detection(label, 0.35) for label in labels)
    )
    kwargs = dict(
        event=EVENT,
        observation_id="synthetic:mask",
        received_us=100_000,
        observed_us=100_000,
        producer=PRODUCER,
    )
    a = ComparatorObservation.from_vision(record, **kwargs)
    b = ComparatorObservation.from_vision(
        replace(record, detections=tuple(reversed(record.detections))), **kwargs
    )
    assert a == b and a.observed_mask == mask


@pytest.mark.parametrize(
    "delta,expected", [(2_000_000, Availability.FRESH), (2_000_001, Availability.STALE)]
)
def test_original_clock_and_strict_producer_staleness_context(delta, expected):
    record = EvidenceRecord(0, "camera_back", Modality.VISION, True, ())
    row = ComparatorObservation.from_vision(
        record,
        event=EVENT,
        observation_id="synthetic:age",
        received_us=delta,
        observed_us=0,
        producer=PRODUCER,
    )
    assert row.availability == expected and row.observed_us == 0


@pytest.mark.parametrize("confidence", [True, float("nan"), float("inf"), -0.1, 1.1])
def test_invalid_confidence_refuses(confidence):
    record = EvidenceRecord(
        0, "camera_back", Modality.VISION, True, (Detection("front", confidence),)
    )
    with pytest.raises(ValueError, match="confidence"):
        ComparatorObservation.from_vision(
            record,
            event=EVENT,
            observation_id="synthetic:bad",
            received_us=0,
            observed_us=0,
            producer=PRODUCER,
        )


def test_missing_unknown_audio_duplicate_and_source_substitution():
    missing = ComparatorObservation.from_vision(
        None,
        event=EVENT,
        observation_id="synthetic:missing",
        received_us=0,
        observed_us=None,
        producer=PRODUCER,
    )
    assert missing.availability == Availability.MISSING and missing.observed_mask is None
    unknown = EvidenceRecord(0, "camera_back", Modality.VISION, True, (Detection("train", 0.99),))
    row = ComparatorObservation.from_vision(
        unknown,
        event=EVENT,
        observation_id="synthetic:unknown",
        received_us=0,
        observed_us=0,
        producer=PRODUCER,
    )
    assert row.availability == Availability.UNKNOWN and row.observed_mask is None
    with pytest.raises(ValueError, match="audio/front/fused"):
        ComparatorObservation.from_vision(
            replace(unknown, modality=Modality.AUDIO),
            event=EVENT,
            observation_id="synthetic:audio",
            received_us=0,
            observed_us=0,
            producer=PRODUCER,
        )
    service = InactiveComparator(event=EVENT, producer=PRODUCER)
    accepted = service.evaluate(observation(1))
    assert service.evaluate(observation(2)).status == "REJECTED_TIMESTAMP"
    assert service.evaluate(observation(2, 0)).status == "REJECTED_TIMESTAMP"
    with pytest.raises(ValueError):
        replace(accepted, active=True)
    with pytest.raises(ValueError):
        service.evaluate(replace(observation(1), source="camera_front"))


@pytest.mark.parametrize(
    "change",
    [
        {"received_us": True},
        {"received_us": -1},
        {"observed_us": 100_001},
        {"observed_mask": True},
        {"observed_mask": 8},
        {"classification": EvidenceClass.EXTERNAL},
        {"availability": "FRESH"},
    ],
)
def test_clock_schema_and_construction_refuse(change):
    with pytest.raises(ValueError):
        InactiveComparator(event=EVENT, producer=PRODUCER).evaluate(
            replace(observation(1), **change)
        )


@pytest.mark.parametrize("available", [1, "true", None])
def test_availability_requires_explicit_boolean_not_coercion(available):
    row = EvidenceRecord(0, "camera_back", Modality.VISION, available, ())
    with pytest.raises(ValueError):
        ComparatorObservation.from_vision(
            row,
            event=EVENT,
            observation_id="synthetic:availability",
            received_us=0,
            observed_us=0,
            producer=PRODUCER,
        )
