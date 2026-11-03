"""Synthetic-only tests for the isolated proposed descriptive aggregator."""

from __future__ import annotations

import copy
import math

import pytest

from railway_detection.evaluation.descriptive_only import (
    DESCRIPTIVE_ONLY_MODE,
    DESCRIPTIVE_ONLY_SCHEMA,
    DescriptiveOnlyInput,
    DescriptiveOnlyRefusal,
    aggregate_descriptive_only,
)
from railway_detection.evaluation.input_contracts import EvidenceClassification
from railway_detection.evaluation.metrics import SingleEventEvaluation


def _event(event_id: str, *, evaluable: bool = True) -> SingleEventEvaluation:
    return SingleEventEvaluation(
        event_id=event_id,
        scenario_name="synthetic_descriptive",
        has_train_ground_truth=True,
        missed_train=False,
        evaluable=evaluable,
        exclusion_reasons={} if evaluable else {"T1_danger_zone_entry": "censored"},
    )


def _input(events: tuple[SingleEventEvaluation, ...] = (_event("train_events/event_001"),)):
    return DescriptiveOnlyInput(
        event_evaluations=events,
        population_label="synthetic_fixed_site_population",
        provenance={"source": "synthetic_fixture", "run_id": "synthetic-run"},
        limitations=("synthetic software test only", "no held-out generalization claim"),
        permitted_claims=("typed aggregation behavior",),
    )


def test_valid_descriptive_aggregation_is_explicitly_nonofficial() -> None:
    report = aggregate_descriptive_only(_input((_event("a"), _event("b", evaluable=False))))
    assert report.mode_id == DESCRIPTIVE_ONLY_MODE
    assert report.schema_version == DESCRIPTIVE_ONLY_SCHEMA
    assert report.evidence_classification is EvidenceClassification.SYNTHETIC
    assert report.official_evaluation_eligible is False
    assert report.event_ids == ("a", "b")
    assert report.excluded_event_ids == ("b",)
    assert report.excluded_event_count == 1
    assert report.summary.total_events == 2


def test_output_is_deterministic_and_does_not_mutate_source() -> None:
    source = _input()
    before = copy.deepcopy(source)
    first = aggregate_descriptive_only(source).to_dict()
    second = aggregate_descriptive_only(source).to_dict()
    assert first == second
    assert source == before


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("mode_id", "official", "MODE_UNSUPPORTED"),
        ("schema_version", "phase12-evaluation-inputs/1", "SCHEMA_UNSUPPORTED"),
        ("population_label", "", "POPULATION_INVALID"),
        ("provenance", {}, "PROVENANCE_MISSING"),
        ("limitations", (), "LIMITATIONS_MISSING"),
        ("permitted_claims", (), "CLAIMS_MISSING"),
        ("event_evaluations", (), "EVENTS_MISSING"),
    ],
)
def test_required_contract_fields_refuse(field: str, value: object, code: str) -> None:
    source = _input()
    object.__setattr__(source, field, value)
    with pytest.raises(DescriptiveOnlyRefusal, match=code):
        aggregate_descriptive_only(source)


def test_real_classification_is_refused() -> None:
    source = _input()
    object.__setattr__(source, "evidence_classification", EvidenceClassification.REAL)
    with pytest.raises(DescriptiveOnlyRefusal, match="OFFICIAL_CONVERSION_REFUSED"):
        aggregate_descriptive_only(source)


def test_duplicate_event_ids_are_refused() -> None:
    with pytest.raises(DescriptiveOnlyRefusal, match="DUPLICATE_EVENT_ID"):
        aggregate_descriptive_only(_input((_event("same"), _event("same"))))


def test_invalid_event_type_is_refused() -> None:
    source = _input()
    object.__setattr__(source, "event_evaluations", (object(),))
    with pytest.raises(DescriptiveOnlyRefusal, match="EVENT_TYPE_INVALID"):
        aggregate_descriptive_only(source)


def test_blank_event_id_is_refused() -> None:
    with pytest.raises(DescriptiveOnlyRefusal, match="EVENT_ID_INVALID"):
        aggregate_descriptive_only(_input((_event("   "),)))


def test_event_id_whitespace_is_preserved_not_normalized() -> None:
    report = aggregate_descriptive_only(_input((_event(" event_001"),)))
    # The current typed-event contract requires nonempty IDs but does not define
    # trimming/normalization. Preserve the caller's identity rather than inventing
    # an equivalence policy.
    assert report.event_ids == (" event_001",)


def test_caller_owned_provenance_is_not_mutated_by_serialization() -> None:
    source = _input()
    source.provenance["nested"] = {"value": 1}  # type: ignore[index]
    report = aggregate_descriptive_only(source)
    serialized = report.to_dict()
    serialized["provenance"]["nested"]["value"] = 99
    assert source.provenance["nested"]["value"] == 1  # type: ignore[index]


def test_invalid_numeric_metadata_is_refused() -> None:
    event = _event("bad")
    event.total_closed_s = math.nan
    with pytest.raises(DescriptiveOnlyRefusal, match="NUMERIC_FIELD_INVALID"):
        aggregate_descriptive_only(_input((event,)))


def test_censored_event_is_counted_and_not_silently_dropped() -> None:
    report = aggregate_descriptive_only(_input((_event("censored", evaluable=False),)))
    assert report.excluded_event_ids == ("censored",)
    assert report.summary.total_events == 1
    assert report.summary.eligible_events == 0


def test_proposed_component_does_not_use_official_runner() -> None:
    import inspect

    import railway_detection.evaluation.descriptive_only as module

    source = inspect.getsource(module)
    assert "Phase12EvaluationRunner" not in source
    assert "RealEventReplayProducer" not in source
    assert "validate_event_level_split" not in source
    assert "frame_generator" not in source
    assert "extract_audio_from_video" not in source