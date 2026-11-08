"""Unit tests for FailureInjector and failure schedules."""

from __future__ import annotations

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.simulation.failure_injector import (
    FailureInjector,
    FailureMode,
    FailureSchedule,
)


def _base_frames() -> list[MultimodalFrame]:
    frames = []
    for t in [1.0, 2.0, 3.0, 4.0]:
        v_rec = EvidenceRecord(
            timestamp_s=t,
            source_id="camera_1",
            modality=Modality.VISION,
            available=True,
            detections=(Detection(label="front", confidence=0.8),),
        )
        a_rec = EvidenceRecord(
            timestamp_s=t,
            source_id="audio_1",
            modality=Modality.AUDIO,
            available=True,
            detections=(Detection(label="train", confidence=0.7),),
        )
        frames.append(
            MultimodalFrame(
                master_timestamp_s=t,
                vision_records=(v_rec,),
                audio_records=(a_rec,),
                source_availability={"camera_1": True, "audio_1": True},
                active_sources=("camera_1", "audio_1"),
            )
        )
    return frames


def test_camera_dropout_injection():
    injector = FailureInjector([
        FailureSchedule(
            mode=FailureMode.CAMERA_1_DROPOUT,
            start_time_s=2.0,
            end_time_s=3.0,
        )
    ])
    mutated = injector.inject_failures(_base_frames())
    assert len(mutated) == 4

    # Frame 1 (t=1.0) unaffected
    assert mutated[0].source_availability["camera_1"] is True
    assert len(mutated[0].vision_records[0].detections) == 1

    # Frame 2 (t=2.0) dropped out
    assert mutated[1].source_availability["camera_1"] is False
    assert not mutated[1].vision_records[0].available
    assert len(mutated[1].vision_records[0].detections) == 0

    # Frame 3 (t=3.0) dropped out
    assert mutated[2].source_availability["camera_1"] is False

    # Frame 4 (t=4.0) restored
    assert mutated[3].source_availability["camera_1"] is True


def test_dual_camera_dropout_injection():
    injector = FailureInjector([
        FailureSchedule(
            mode=FailureMode.DUAL_CAMERA_DROPOUT,
            start_time_s=1.0,
            end_time_s=4.0,
        )
    ])
    mutated = injector.inject_failures(_base_frames())
    for f in mutated:
        assert f.source_availability["camera_1"] is False
        assert not f.has_vision_evidence


def test_audio_dropout_injection():
    injector = FailureInjector([
        FailureSchedule(
            mode=FailureMode.AUDIO_DROPOUT,
            start_time_s=1.0,
            end_time_s=4.0,
        )
    ])
    mutated = injector.inject_failures(_base_frames())
    for f in mutated:
        assert f.source_availability["audio_1"] is False
        assert not f.has_audio_evidence


def test_dropped_frames_injection():
    injector = FailureInjector([
        FailureSchedule(
            mode=FailureMode.DROPPED_FRAMES,
            start_time_s=2.0,
            end_time_s=3.0,
        )
    ])
    mutated = injector.inject_failures(_base_frames())
    # Frames at t=2.0 and t=3.0 dropped -> 2 frames remaining
    assert len(mutated) == 2
    assert mutated[0].master_timestamp_s == 1.0
    assert mutated[1].master_timestamp_s == 4.0


def test_probabilistic_dropped_frames_injection():
    """Verify that a drop_rate of 0.3 drops ~30% of frames deterministically, not 100%."""
    # Build a stream of 100 frames
    stream = [
        MultimodalFrame(
            master_timestamp_s=i * 0.2,
            vision_records=(),
            audio_records=(),
            source_availability={"camera_1": True, "camera_2": True},
            active_sources=("camera_1", "camera_2"),
        )
        for i in range(100)
    ]
    injector = FailureInjector([
        FailureSchedule(
            mode=FailureMode.DROPPED_FRAMES,
            start_time_s=0.0,
            end_time_s=25.0,
            parameters={"drop_rate": 0.3, "seed": 42},
        )
    ])
    mutated = injector.inject_failures(stream)

    # Must NOT drop 100% of frames
    assert len(mutated) > 0, "Probabilistic drop dropped 100% of frames!"
    assert len(mutated) < 100, "Probabilistic drop dropped 0% of frames!"
    
    # Check drop rate is approximately 30% (e.g. between 20% and 40%)
    dropped_count = 100 - len(mutated)
    assert 20 <= dropped_count <= 40, f"Unexpected drop count: {dropped_count}"
    assert injector.last_injection_stats["actual_drop_rate"] == dropped_count / 100.0
    assert len(injector.last_injection_stats["dropped_frame_indices"]) == dropped_count


def test_false_detection_injection():
    injector = FailureInjector([
        FailureSchedule(
            mode=FailureMode.FALSE_DETECTION,
            start_time_s=2.0,
            end_time_s=2.0,
            parameters={"label": "ghost_train", "confidence": 0.99},
        )
    ])
    mutated = injector.inject_failures(_base_frames())
    frame2 = mutated[1]
    # Injected false detection appended
    labels = [d.label for r in frame2.vision_records for d in r.detections]
    assert "ghost_train" in labels


def test_out_of_order_frames_injection():
    injector = FailureInjector([
        FailureSchedule(
            mode=FailureMode.OUT_OF_ORDER_FRAMES,
            start_time_s=1.0,
            end_time_s=2.0,
        )
    ])
    mutated = injector.inject_failures(_base_frames())
    # First two frames swapped: t=2.0 then t=1.0
    assert mutated[0].master_timestamp_s == 2.0
    assert mutated[1].master_timestamp_s == 1.0


def test_stale_timestamps_requires_explicit_parameters() -> None:
    injector = FailureInjector([
        FailureSchedule(
            mode=FailureMode.STALE_TIMESTAMPS,
            start_time_s=1.0,
            end_time_s=2.0,
            target_source="camera_1",
        )
    ])
    import pytest
    with pytest.raises(ValueError, match="delay_s"):
        injector.inject_failures(_base_frames())


def test_stale_timestamps_preserves_content_and_applies_delay() -> None:
    injector = FailureInjector([
        FailureSchedule(
            mode=FailureMode.STALE_TIMESTAMPS,
            start_time_s=2.0,
            end_time_s=2.0,
            target_source="camera_1",
            parameters={"delay_s": 0.5},
        )
    ])
    original = _base_frames()
    mutated = injector.inject_failures(original)
    assert mutated[1].vision_records[0].detections == original[1].vision_records[0].detections
    assert mutated[1].vision_records[0].timestamp_s == 1.5
    assert mutated[1].audio_records[0].timestamp_s == 2.0


def test_stale_timestamp_runs_are_isolated_and_deterministic() -> None:
    schedule = FailureSchedule(
        mode=FailureMode.STALE_TIMESTAMPS,
        start_time_s=2.0,
        end_time_s=3.0,
        target_source="camera_1",
        parameters={"delay_s": 0.25},
    )
    first = FailureInjector([schedule]).inject_failures(_base_frames())
    second = FailureInjector([schedule]).inject_failures(_base_frames())
    assert [r.timestamp_s for r in first[1].vision_records] == [
        r.timestamp_s for r in second[1].vision_records
    ]


def test_out_of_order_input_remains_out_of_order_for_delivery_boundary() -> None:
    """The approved B7d transport fault is preserved for downstream Rule 8."""
    injector = FailureInjector([
        FailureSchedule(
            mode=FailureMode.OUT_OF_ORDER_FRAMES,
            start_time_s=1.0,
            end_time_s=2.0,
        )
    ])
    output = injector.inject_failures(_base_frames())
    assert [frame.master_timestamp_s for frame in output[:2]] == [2.0, 1.0]
