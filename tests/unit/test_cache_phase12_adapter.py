"""Synthetic contract tests for the non-authoritative Phase 12 cache adapter."""

from __future__ import annotations

import copy
import inspect
import math

import pytest

from railway_detection.evaluation.cache_only_engine import ReplayOutput
from railway_detection.evaluation.cache_phase12_adapter import (
    ADAPTER_VERSION,
    CachePhase12AdapterError,
    adapt_batch,
    to_event_replay,
    to_official_evidence_payload,
)
from railway_detection.evaluation.clock_aware import EventReplay
from railway_detection.evaluation.input_contracts import EvidenceClassification
from railway_detection.simulation.runner import SimulationRunResult


def _output(
    event_id: str = "event_001",
    condition: str = "B0",
    *,
    provenance: dict[str, object] | None = None,
) -> ReplayOutput:
    return ReplayOutput(
        event_id=event_id,
        condition=condition,
        result=SimulationRunResult(
            event_id=event_id,
            scenario_name=f"cache_only_{condition}",
            total_duration_s=3.0,
            closed_duration_s=0.0,
        ),
        frames_produced=1,
        evidence_records_loaded=1,
        manifest_sha256="a" * 64,
        deterministic_run_id="run-001",
        provenance=provenance or {"condition": condition, "streams": [condition]},
    )


def test_valid_b0_mapping_preserves_identity_and_provenance() -> None:
    source = _output(condition="B0", provenance={"artifact_sha256": "b" * 64})
    before = copy.deepcopy(source)
    adapted = to_event_replay(source, cohort="train_events")
    assert isinstance(adapted.replay, EventReplay)
    assert adapted.replay.event_id == "event_001"
    assert adapted.replay.cohort == "train_events"
    assert adapted.replay.camera_mode == "single_camera"
    assert set(adapted.replay.systems) == {"front"}
    assert adapted.replay.systems["front"].clock_offsets_s == {"front": 0.0}
    assert adapted.replay.provenance["adapter_version"] == ADAPTER_VERSION
    assert adapted.replay.provenance["source_classification"] == "synthetic"
    assert source == before


@pytest.mark.parametrize(
    ("condition", "expected_streams"),
    [
        ("B0", ["front_vision"]),
        ("B1", ["front_audio"]),
        ("B2", ["front_vision", "front_audio"]),
    ],
)
def test_condition_stream_contract_is_preserved(
    condition: str, expected_streams: list[str]
) -> None:
    adapted = to_event_replay(_output(condition=condition), cohort="no_train_events")
    assert adapted.replay.provenance["streams"] == expected_streams


def test_valid_mapping_is_deterministic() -> None:
    source = _output(condition="B2")
    first = to_event_replay(source, cohort="train_events").replay
    second = to_event_replay(source, cohort="train_events").replay
    assert first == second


def test_wrong_source_type_refused() -> None:
    with pytest.raises(CachePhase12AdapterError, match="SOURCE_TYPE_INVALID"):
        to_event_replay(object(), cohort="train_events")  # type: ignore[arg-type]


def test_missing_event_id_refused() -> None:
    source = _output()
    object.__setattr__(source, "event_id", "")
    with pytest.raises(CachePhase12AdapterError, match="event_id"):
        to_event_replay(source, cohort="train_events")


def test_wrong_condition_refused() -> None:
    source = _output(condition="B9")
    with pytest.raises(CachePhase12AdapterError, match="CONDITION_UNSUPPORTED"):
        to_event_replay(source, cohort="train_events")


def test_wrong_result_type_refused() -> None:
    source = _output()
    object.__setattr__(source, "result", {"event_id": "event_001"})
    with pytest.raises(CachePhase12AdapterError, match="SOURCE_TYPE_INVALID"):
        to_event_replay(source, cohort="train_events")


def test_misbound_result_event_id_refused() -> None:
    source = _output()
    source.result.event_id = "different"
    with pytest.raises(CachePhase12AdapterError, match="EVENT_ID_MISMATCH"):
        to_event_replay(source, cohort="train_events")


def test_nonfinite_duration_refused() -> None:
    source = _output()
    source.result.total_duration_s = math.nan
    with pytest.raises(CachePhase12AdapterError, match="NUMERIC_FIELD_INVALID"):
        to_event_replay(source, cohort="train_events")


def test_missing_manifest_provenance_refused() -> None:
    source = _output()
    object.__setattr__(source, "manifest_sha256", "bad")
    with pytest.raises(CachePhase12AdapterError, match="PROVENANCE_INVALID"):
        to_event_replay(source, cohort="train_events")


def test_official_classification_refused_without_authority() -> None:
    with pytest.raises(CachePhase12AdapterError, match="OFFICIAL_CONVERSION_REFUSED"):
        to_event_replay(
            _output(), cohort="train_events", evidence_classification=EvidenceClassification.REAL
        )


def test_official_payload_conversion_refused_without_frozen_bindings() -> None:
    with pytest.raises(CachePhase12AdapterError, match="PROVENANCE_INCOMPLETE"):
        to_official_evidence_payload(_output())


def test_batch_mapping_is_atomic_on_failure() -> None:
    outputs = {"event_001": _output("event_001"), "event_002": _output("event_002")}
    outputs["event_002"].result.event_id = "wrong"
    with pytest.raises(CachePhase12AdapterError, match="EVENT_ID_MISMATCH"):
        adapt_batch(outputs, cohorts={"event_001": "train_events", "event_002": "train_events"})


def test_batch_identity_mismatch_refused() -> None:
    with pytest.raises(CachePhase12AdapterError, match="BATCH_IDENTITY_MISMATCH"):
        adapt_batch({"event_001": _output()}, cohorts={"event_002": "train_events"})


def test_batch_valid_mapping_returns_all_events() -> None:
    outputs = {"event_001": _output("event_001"), "event_002": _output("event_002", "B1")}
    mapped = adapt_batch(
        outputs,
        cohorts={"event_001": "train_events", "event_002": "no_train_events"},
    )
    assert sorted(mapped) == ["event_001", "event_002"]
    assert mapped["event_002"].provenance["condition"] == "B1"


def test_adapter_has_no_official_runner_or_media_loader_path() -> None:
    import railway_detection.evaluation.cache_phase12_adapter as adapter

    for forbidden in (
        "RealEventReplayProducer",
        "Phase12EvaluationRunner",
        "frame_generator",
        "extract_audio_from_video",
        "cv2",
        "subprocess",
    ):
        assert not hasattr(adapter, forbidden.split(".")[-1])
    source = inspect.getsource(adapter.to_event_replay)
    assert "run_official" not in source
