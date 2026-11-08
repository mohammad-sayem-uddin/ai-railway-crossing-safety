"""Synthetic-only tests for Phase 13 plan and replay perturbation helpers."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from railway_detection.evaluation.ablation_runner import (
    Phase13AblationRunner,
    Phase13ExecutionBlocked,
    Phase13Prerequisites,
)
from railway_detection.evaluation.perturbation import (
    PerturbationRefused,
    apply_confidence_noise,
    apply_sensor_dropout,
    apply_timing_jitter,
    refuse_ground_truth_perturbation,
)
from railway_detection.experiments.frozen_config import load_frozen_config
from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.research_contracts import AblationConditionContract, ResearchContractError


@pytest.fixture
def frozen_config_path() -> Path:
    return Path(__file__).resolve().parents[2] / "configs" / "frozen_experiment_v1.yaml"


def _frames() -> list[MultimodalFrame]:
    frames: list[MultimodalFrame] = []
    for timestamp in (0.0, 1.0, 2.0):
        frames.append(
            MultimodalFrame(
                master_timestamp_s=timestamp,
                vision_records=(
                    EvidenceRecord(
                        timestamp_s=timestamp,
                        source_id="camera_1",
                        modality=Modality.VISION,
                        available=True,
                        detections=(Detection("train", 0.8),),
                    ),
                ),
                audio_records=(
                    EvidenceRecord(
                        timestamp_s=timestamp,
                        source_id="audio_1",
                        modality=Modality.AUDIO,
                        available=True,
                        detections=(Detection("horn", 0.7),),
                    ),
                ),
                source_availability={"camera_1": True, "audio_1": True},
                active_sources=("camera_1", "audio_1"),
            )
        )
    return frames


def _shift_frames(frames: list[MultimodalFrame], offset_s: float) -> list[MultimodalFrame]:
    return [
        replace(
            frame,
            master_timestamp_s=frame.master_timestamp_s + offset_s,
            vision_records=tuple(
                replace(record, timestamp_s=record.timestamp_s + offset_s)
                for record in frame.vision_records
            ),
            audio_records=tuple(
                replace(record, timestamp_s=record.timestamp_s + offset_s)
                for record in frame.audio_records
            ),
        )
        for frame in frames
    ]


def _valid_plan(runner: Phase13AblationRunner):
    frozen_hash = load_frozen_config(runner.config_path).config_hash
    return runner.prepare_plan(
        [
            AblationConditionContract("baseline", frozen_hash, (), is_baseline=True),
            AblationConditionContract("vision-only", frozen_hash, ("audio_enabled",)),
        ]
    )


def test_prepare_plan_checks_frozen_hash_and_marks_plan_blocked(frozen_config_path):
    runner = Phase13AblationRunner(frozen_config_path)
    plan = _valid_plan(runner)
    serialized = plan.to_dict()
    assert serialized["execution_status"] == "BLOCKED_NOT_AUTHORIZED"
    assert serialized["results"] is None
    assert len(serialized["frozen_config_sha256"]) == 64


def test_prepare_plan_rejects_condition_with_wrong_frozen_hash(frozen_config_path):
    runner = Phase13AblationRunner(frozen_config_path)
    conditions = [
        AblationConditionContract("baseline", "a" * 64, (), is_baseline=True),
        AblationConditionContract("audio-off", "b" * 64, ("audio_enabled",)),
    ]
    with pytest.raises(ResearchContractError, match="frozen config hash"):
        runner.prepare_plan(conditions)


def test_prepare_plan_rejects_compound_ablation(frozen_config_path):
    runner = Phase13AblationRunner(frozen_config_path)
    frozen_hash = load_frozen_config(frozen_config_path).config_hash
    conditions = [
        AblationConditionContract("baseline", frozen_hash, (), is_baseline=True),
        AblationConditionContract("compound", frozen_hash, ("audio", "vision")),
    ]
    with pytest.raises(ResearchContractError, match="exactly one changed factor"):
        runner.prepare_plan(conditions)


def test_prepare_plan_rejects_audio_v2(frozen_config_path):
    runner = Phase13AblationRunner(frozen_config_path)
    frozen_hash = load_frozen_config(frozen_config_path).config_hash
    conditions = [
        AblationConditionContract("baseline", frozen_hash, (), is_baseline=True),
        AblationConditionContract(
            "legacy-audio", frozen_hash, ("audio_v2",), uses_audio_v2=True
        ),
    ]
    with pytest.raises(ResearchContractError, match="Audio V2 is prohibited"):
        runner.prepare_plan(conditions)


def test_execution_refuses_even_when_caller_sets_all_checklist_flags_true(
    frozen_config_path,
):
    runner = Phase13AblationRunner(frozen_config_path)
    plan = _valid_plan(runner)
    prerequisites = Phase13Prerequisites(True, True, True, True)
    with pytest.raises(Phase13ExecutionBlocked, match="verified researcher authorization"):
        runner.run(plan=plan, prerequisites=prerequisites)


def test_sensor_dropout_is_source_specific_and_does_not_mutate_inputs():
    frames = _frames()
    transformed = apply_sensor_dropout(
        frames, source_id="camera_1", start_s=1.0, duration_s=1.0
    )
    assert frames[1].vision_records[0].available is True
    assert transformed[1].vision_records[0].available is False
    assert transformed[1].vision_records[0].detections == ()
    assert transformed[1].audio_records[0].available is True
    assert transformed[1].source_availability["camera_1"] is False
    assert transformed[0].vision_records[0].available is True


def test_sensor_dropout_rejects_unknown_source_and_nonpositive_window():
    frames = _frames()
    with pytest.raises(PerturbationRefused, match="not present"):
        apply_sensor_dropout(frames, source_id="unknown", start_s=0, duration_s=1)
    with pytest.raises(PerturbationRefused, match="positive"):
        apply_sensor_dropout(frames, source_id="camera_1", start_s=0, duration_s=0)
    with pytest.raises(PerturbationRefused, match="finite number"):
        apply_sensor_dropout(frames, source_id="camera_1", start_s=float("nan"), duration_s=1)


def test_confidence_noise_is_seeded_clamped_and_does_not_mutate_inputs():
    frames = _frames()
    first = apply_confidence_noise(frames, sigma=0.25, seed=17)
    second = apply_confidence_noise(frames, sigma=0.25, seed=17)
    first_conf = first[0].vision_records[0].detections[0].confidence
    second_conf = second[0].vision_records[0].detections[0].confidence
    assert first_conf == second_conf
    assert 0.0 <= first_conf <= 1.0
    assert frames[0].vision_records[0].detections[0].confidence == 0.8
    assert first_conf != 0.8


def test_confidence_noise_rejects_out_of_bounds_input_confidence():
    frame = _frames()[0]
    invalid_detection = replace(
        frame.vision_records[0].detections[0], confidence=1.5
    )
    invalid_record = replace(
        frame.vision_records[0], detections=(invalid_detection,)
    )
    invalid_frame = replace(frame, vision_records=(invalid_record,))
    with pytest.raises(PerturbationRefused, match=r"within \[0, 1\]"):
        apply_confidence_noise([invalid_frame], sigma=0.1)


def test_confidence_noise_rejects_nonfinite_sigma():
    with pytest.raises(PerturbationRefused, match="finite number"):
        apply_confidence_noise(_frames(), sigma=float("inf"))


def test_timing_jitter_is_seeded_and_preserves_monotonic_order():
    frames = _shift_frames(_frames(), 1.0)
    jittered = apply_timing_jitter(frames, max_jitter_s=0.1, seed=9)
    repeated = apply_timing_jitter(frames, max_jitter_s=0.1, seed=9)
    times = [frame.master_timestamp_s for frame in jittered]
    assert times == [frame.master_timestamp_s for frame in repeated]
    assert all(right > left for left, right in zip(times, times[1:], strict=False))
    assert [frame.master_timestamp_s for frame in frames] == [1.0, 2.0, 3.0]


def test_timing_jitter_refuses_reordering():
    frames = _shift_frames(_frames(), 10.0)
    with pytest.raises(PerturbationRefused, match="reorder"):
        apply_timing_jitter(frames, max_jitter_s=2.0, seed=0)


def test_ground_truth_records_cannot_be_passed_to_perturbations():
    stage21_shaped = {
        "schema_version": "8.1.0-stage2.1",
        "event_id": "evt_synthetic",
        "adjudication_status": "APPROVED",
        "boundary_adjudications": {},
    }
    with pytest.raises(PerturbationRefused, match="ground truth is refused"):
        refuse_ground_truth_perturbation([stage21_shaped])


def test_plan_serialization_is_deterministic(frozen_config_path):
    runner = Phase13AblationRunner(frozen_config_path)
    plan = _valid_plan(runner)
    first = json.dumps(plan.to_dict(), sort_keys=True, separators=(",", ":"))
    second = json.dumps(plan.to_dict(), sort_keys=True, separators=(",", ":"))
    assert first.encode() == second.encode()