"""Unit tests for the temporal evidence buffer."""

from __future__ import annotations

import pytest

from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.vision.temporal import TemporalConfig, TemporalEvidenceBuffer


def record(t, source, detections, available=True):
    return EvidenceRecord(
        timestamp_s=t,
        source_id=source,
        modality=Modality.VISION,
        available=available,
        detections=tuple(detections),
    )


def det(label, conf):
    return Detection(label, conf)


def test_out_of_order_timestamp_rejected():
    buffer = TemporalEvidenceBuffer(TemporalConfig(confirm_frames=1))
    buffer.process(record(1.0, "camera_1", [det("front", 0.9)]))
    with pytest.raises(ValueError):
        buffer.process(record(0.5, "camera_1", [det("front", 0.9)]))


def test_single_frame_spike_not_confirmed():
    buffer = TemporalEvidenceBuffer(TemporalConfig(confirm_frames=3))
    out = buffer.process(record(0.0, "camera_1", [det("front", 0.95)]))
    front = [d for d in out.detections if d.label == "front"][0]
    assert front.metadata["temporal_confirmed"] is False


def test_consecutive_frames_confirm():
    buffer = TemporalEvidenceBuffer(TemporalConfig(confirm_frames=3))
    buffer.process(record(0.0, "camera_1", [det("front", 0.9)]))
    buffer.process(record(0.1, "camera_1", [det("front", 0.9)]))
    out = buffer.process(record(0.2, "camera_1", [det("front", 0.9)]))
    front = [d for d in out.detections if d.label == "front"][0]
    assert front.metadata["temporal_confirmed"] is True


def test_confirmation_via_window_seconds():
    buffer = TemporalEvidenceBuffer(
        TemporalConfig(confirm_frames=100, confirm_window_s=0.5)
    )
    buffer.process(record(0.0, "camera_1", [det("front", 0.9)]))
    out = buffer.process(record(0.6, "camera_1", [det("front", 0.9)]))
    front = [d for d in out.detections if d.label == "front"][0]
    assert front.metadata["temporal_confirmed"] is True


def test_brief_dropout_persists_state():
    buffer = TemporalEvidenceBuffer(
        TemporalConfig(confirm_frames=2, miss_tolerance_frames=2)
    )
    buffer.process(record(0.0, "camera_1", [det("front", 0.9)]))
    out = buffer.process(record(0.1, "camera_1", [det("front", 0.9)]))
    # One missed frame: persistence retains the smoothed entry.
    out = buffer.process(record(0.2, "camera_1", []))
    assert any(d.label == "front" for d in out.detections)


def test_long_dropout_expires():
    buffer = TemporalEvidenceBuffer(
        TemporalConfig(
            confirm_frames=2,
            miss_tolerance_frames=1,
            evidence_expiry_s=3.0,
        )
    )
    buffer.process(record(0.0, "camera_1", [det("front", 0.9)]))
    buffer.process(record(0.1, "camera_1", [det("front", 0.9)]))
    out = buffer.process(record(5.0, "camera_1", []))
    assert not any(d.label == "front" for d in out.detections)


def test_smoothing_is_exponential():
    buffer = TemporalEvidenceBuffer(
        TemporalConfig(confirm_frames=1, smoothing_alpha=0.5)
    )
    buffer.process(record(0.0, "camera_1", [det("front", 0.8)]))
    out = buffer.process(record(0.1, "camera_1", [det("front", 0.6)]))
    front = [d for d in out.detections if d.label == "front"][0]
    assert front.confidence == pytest.approx(0.7)


def test_unavailable_record_marks_source():
    buffer = TemporalEvidenceBuffer(TemporalConfig(confirm_frames=1))
    out = buffer.process(
        record(1.0, "camera_1", [], available=False)
    )
    assert out.available is False
    assert out.metadata["temporal_status"] == "unavailable"


def test_sources_are_independent():
    buffer = TemporalEvidenceBuffer(TemporalConfig(confirm_frames=1))
    buffer.process(record(0.0, "camera_1", [det("front", 0.9)]))
    out = buffer.process(record(0.0, "camera_2", [det("rear", 0.9)]))
    assert all(d.label == "rear" for d in out.detections)
