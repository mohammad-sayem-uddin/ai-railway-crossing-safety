"""Unit tests for refactored ExperimentRunner and B0-B7 benchmark conditions."""

from __future__ import annotations

from pathlib import Path

import pytest

from railway_detection.data.contracts import EventLabel, LayerBEvent
from railway_detection.experiments.runner import BenchmarkCondition, ExperimentRunner
from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality


def _make_test_frames() -> tuple[LayerBEvent, list[MultimodalFrame]]:
    event = LayerBEvent(
        event_id="test_runner_001",
        labels=(
            EventLabel(name="crossing_entry", timestamp_s=8.0, label_status="observed"),
            EventLabel(name="tail_clearance", timestamp_s=14.0, label_status="observed"),
        ),
    )
    frames = []
    # 0.0s - 1.0s: IDLE
    for t in [0.0, 1.0]:
        frames.append(
            MultimodalFrame(
                master_timestamp_s=t,
                vision_records=(),
                audio_records=(),
                source_availability={"camera_1": True, "camera_2": True, "audio_1": True},
                active_sources=("camera_1", "camera_2", "audio_1"),
            )
        )
    # 1.5s - 7.0s: Approach (warning starts at 2.0s, gate closes at 7.0s, before entry at 8.0s)
    for t in [1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]:
        v_rec = EvidenceRecord(
            timestamp_s=t,
            source_id="camera_1",
            modality=Modality.VISION,
            available=True,
            detections=(Detection("front", 0.9),),
        )
        a_rec = EvidenceRecord(
            timestamp_s=t,
            source_id="audio_1",
            modality=Modality.AUDIO,
            available=True,
            detections=(Detection("train", 0.8),),
            metadata={"audio_safety_role": "supporting_only"},
        )
        frames.append(
            MultimodalFrame(
                master_timestamp_s=t,
                vision_records=(v_rec,),
                audio_records=(a_rec,),
                source_availability={"camera_1": True, "camera_2": True, "audio_1": True},
                active_sources=("camera_1", "camera_2", "audio_1"),
            )
        )
    # 8.0s - 12.0s: Occupied
    for t in [8.0, 9.0, 10.0, 11.0, 12.0]:
        v_rec = EvidenceRecord(
            timestamp_s=t,
            source_id="camera_1",
            modality=Modality.VISION,
            available=True,
            detections=(Detection("side", 0.92),),
        )
        frames.append(
            MultimodalFrame(
                master_timestamp_s=t,
                vision_records=(v_rec,),
                audio_records=(),
                source_availability={"camera_1": True, "camera_2": True, "audio_1": True},
                active_sources=("camera_1", "camera_2", "audio_1"),
            )
        )
    # 13.0s - 14.0s: Departure
    for t in [13.0, 13.5, 14.0]:
        v_rec = EvidenceRecord(
            timestamp_s=t,
            source_id="camera_2",
            modality=Modality.VISION,
            available=True,
            detections=(Detection("rear", 0.85),),
        )
        frames.append(
            MultimodalFrame(
                master_timestamp_s=t,
                vision_records=(v_rec,),
                audio_records=(),
                source_availability={"camera_1": True, "camera_2": True, "audio_1": True},
                active_sources=("camera_1", "camera_2", "audio_1"),
            )
        )
    # 14.5s - 20.0s: Clearance & Opening
    for t in [14.5, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0]:
        frames.append(
            MultimodalFrame(
                master_timestamp_s=t,
                vision_records=(),
                audio_records=(),
                source_availability={"camera_1": True, "camera_2": True, "audio_1": True},
                active_sources=("camera_1", "camera_2", "audio_1"),
            )
        )
    return event, frames


def test_b4_full_policy_execution(tmp_path: Path):
    event, frames = _make_test_frames()
    runner = ExperimentRunner(output_root=tmp_path / "exp")
    summary = runner.run_condition(BenchmarkCondition.B4, [(event, frames)])
    assert summary.total_events == 1
    assert summary.eligible_events == 1
    assert summary.missed_train_rate == 0.0
    # The premature-opening profile is a researcher decision and the legacy
    # runner must not silently select v9 or M4.
    assert summary.premature_opening_rate is None
    assert summary.premature_opening_definition == "undecided"


def test_b1_audio_only_never_opens(tmp_path: Path):
    event, frames = _make_test_frames()
    runner = ExperimentRunner(output_root=tmp_path / "exp")
    summary = runner.run_condition(BenchmarkCondition.B1, [(event, frames)])
    assert summary.total_events == 1
    # B1 closes gate on horn, but NEVER opens!
    assert summary.single_events[0].total_closed_s > 0.0
    assert summary.single_events[0].premature_opening is None or summary.single_events[0].premature_opening is False


def test_b6b_dual_camera_failure_fail_safe(tmp_path: Path):
    event, frames = _make_test_frames()
    runner = ExperimentRunner(output_root=tmp_path / "exp")
    summary = runner.run_condition(BenchmarkCondition.B6, [(event, frames)], sub_condition="B6b")
    assert summary.total_events == 1


def test_b7d_preserves_delivery_order_for_rule8(tmp_path: Path):
    event, frames = _make_test_frames()
    runner = ExperimentRunner(output_root=tmp_path / "exp")
    summary = runner.run_condition(BenchmarkCondition.B7, [(event, frames)], sub_condition="B7d")
    assert summary.total_events == 1
    assert summary.eligible_events == 1
    assert summary.single_events[0].fault_occurred is True
    assert summary.fault_event_count == 1


def test_b7e_requires_explicit_delay_configuration():
    from railway_detection.simulation.failure_injector import FailureInjector, FailureMode, FailureSchedule
    import pytest
    from railway_detection.fusion.collector import MultimodalFrame
    frame = MultimodalFrame(master_timestamp_s=1.0, vision_records=(), audio_records=())
    with pytest.raises(ValueError, match="delay_s"):
        FailureInjector([
            FailureSchedule(mode=FailureMode.STALE_TIMESTAMPS, target_source="camera_1")
        ]).inject_failures([frame])
