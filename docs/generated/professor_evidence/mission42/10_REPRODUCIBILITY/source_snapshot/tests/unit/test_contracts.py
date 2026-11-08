import pytest

from railway_detection.fusion.evidence import (
    DecisionRecord,
    Detection,
    EvidenceRecord,
    Modality,
    UnavailableSource,
)


def test_available_evidence_with_detection():
    record = EvidenceRecord(
        timestamp_s=1.0,
        source_id="camera_1",
        modality=Modality.VISION,
        available=True,
        detections=(Detection("front", 0.9, (0, 0, 10, 10)),),
    )
    assert record.available is True
    assert len(record.detections) == 1


def test_unavailable_source_distinct_from_zero_confidence():
    record = EvidenceRecord(
        timestamp_s=1.0,
        source_id="camera_2",
        modality=Modality.VISION,
        available=False,
    )
    assert record.available is False
    assert record.detections == ()


def test_unavailable_with_detections_rejected():
    with pytest.raises(ValueError):
        EvidenceRecord(
            timestamp_s=1.0,
            source_id="camera_1",
            modality=Modality.VISION,
            available=False,
            detections=(Detection("front", 0.0),),
        )


def test_invalid_timestamp_rejected():
    with pytest.raises(ValueError):
        EvidenceRecord(
            timestamp_s=-0.1,
            source_id="camera_1",
            modality=Modality.VISION,
            available=True,
        )


def test_unavailable_source_helper():
    source = UnavailableSource("camera_1", Modality.VISION, "stream lost")
    record = source.to_evidence(3.0)
    assert record.available is False
    assert record.metadata["reason"] == "stream lost"


def test_decision_record_round_trips():
    decision = DecisionRecord(
        timestamp_s=1.0,
        scenario_run_id="run_1",
        previous_state="IDLE",
        resulting_state="TRAIN_APPROACHING",
        previous_gate_state="OPEN",
        resulting_gate_state="OPEN",
        evidence_references=("evt_1",),
        rule_id="R-001",
        explanation="qualified approach evidence",
        fault_status="none",
        source_availability={"camera_1": True, "camera_2": False},
    )
    data = decision.to_dict()
    assert data["resulting_state"] == "TRAIN_APPROACHING"
    assert data["source_availability"]["camera_2"] is False
