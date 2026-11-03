"""Production-path integration tests for manifest-backed dual-camera fusion.

Exercises the ACTUAL production components (`LayerBEventProcessor.build_multimodal_frames`,
`railway_detection.data.sync_calibration.load_validated_sync_aligner`,
`EventSimulationRunner`) with small synthetic `EvidenceRecord` fixtures --
never real video/audio files or model checkpoints for the fixture data
itself, though `LayerBEventProcessor` is still constructed against the
real, checkpoint-hash-verified frozen configuration, so the test also
incidentally re-confirms checkpoint integrity on every run.

This is Task 1's required integration test: proves synchronization is
applied exactly once, and that invalid/missing calibration blocks temporal
merging rather than silently defaulting to zero offset.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from railway_detection.data.sync_calibration import (
    CalibrationNotAcceptedError,
    load_validated_sync_aligner,
)
from railway_detection.experiments.frozen_config import TimingIntegrityError
from railway_detection.experiments.layer_b_processor import LayerBEventProcessor
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.simulation.runner import EventSimulationRunner

REPO_ROOT = Path(__file__).resolve().parents[2]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_media(path: Path, content: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return _sha256_bytes(content)


def _write_synthetic_manifest(tmp_path: Path, back_offset_s: float, verdict: str = "CALIBRATION_SUPPORTED") -> Path:
    front_path = tmp_path / "data/raw/layer_b/v2/train_events/event_900/camera_front.mov"
    back_path = tmp_path / "data/raw/layer_b/v2/train_events/event_900/camera_back.mov"
    front_sha = _write_media(front_path, b"synthetic-front-media")
    back_sha = _write_media(back_path, b"synthetic-back-media")

    manifest = {
        "status": "ACCEPTED_FOR_TEST",
        "manifest_version": "integration_test_v1",
        "events": {
            "train_events/event_900": {
                "calibration_verdict": verdict,
                "camera_front": {
                    "relative_path": "data/raw/layer_b/v2/train_events/event_900/camera_front.mov",
                    "sha256": front_sha,
                    "offset_s": 0.0,
                },
                "camera_back": {
                    "relative_path": "data/raw/layer_b/v2/train_events/event_900/camera_back.mov",
                    "sha256": back_sha,
                    "offset_s": back_offset_s,
                    "uncertainty_s": 0.05,
                },
            }
        },
    }
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(yaml.dump(manifest), encoding="utf-8")
    return manifest_path


def _processor(tmp_path: Path) -> LayerBEventProcessor:
    """Constructs the real production processor against the real, checkpoint-
    hash-verified frozen configuration, but with cache/audio dirs isolated
    to tmp_path so nothing real is touched or polluted."""
    return LayerBEventProcessor(
        repo_root=REPO_ROOT,
        processed_audio_dir=tmp_path / "processed_audio",
        cache_dir=tmp_path / "cache",
    )


def _front_records(n: int = 5, hop_s: float = 1.0) -> list[EvidenceRecord]:
    return [
        EvidenceRecord(
            timestamp_s=i * hop_s,
            source_id="camera_1",
            modality=Modality.VISION,
            available=True,
            detections=(Detection(label="front", confidence=0.8),),
        )
        for i in range(n)
    ]


def _back_records(n: int = 5, hop_s: float = 1.0, start_local_s: float = 0.0) -> list[EvidenceRecord]:
    return [
        EvidenceRecord(
            timestamp_s=start_local_s + i * hop_s,
            source_id="camera_2",
            modality=Modality.VISION,
            available=True,
            detections=(Detection(label="rear", confidence=0.8),),
        )
        for i in range(n)
    ]


def test_synchronization_applied_exactly_once(tmp_path: Path) -> None:
    """A back-camera record at local t=10.0, under a validated offset of
    +7.406s, must appear in the produced frames at master time 17.406 --
    not 10.0 (offset not applied) and not 24.812 (offset applied twice)."""
    back_offset_s = 7.406
    manifest_path = _write_synthetic_manifest(tmp_path, back_offset_s)
    validated = load_validated_sync_aligner(
        manifest_path, "train_events/event_900", repo_root=tmp_path, allow_candidate_status=True
    )

    processor = _processor(tmp_path)
    front_recs = _front_records(n=20, hop_s=1.0)  # local t = 0..19
    back_recs = _back_records(n=20, hop_s=1.0, start_local_s=0.0)  # local t = 0..19

    frames = processor.build_multimodal_frames(
        vision_records=front_recs + back_recs,
        audio_records=[],
        duration_s=30.0,
        stride_s=0.2,
        sync_aligner=validated.aligner,
    )

    # The collector's frame window looks BACKWARD from each frame's own
    # master_timestamp_s (window = [t - window_tolerance_s, t]), so a record
    # at master time M first becomes visible in frames whose own
    # master_timestamp_s lies in [M, M + window_tolerance_s]. Scan every
    # frame for the back-camera's local-t=10.0 record and check which
    # master times it was actually observed at, rather than guessing a
    # single frame index.
    target_master_t = 10.0 + back_offset_s  # expected: applied exactly once
    doubled_master_t = 10.0 + 2 * back_offset_s  # must NOT appear here

    observed_master_times = [
        f.master_timestamp_s
        for f in frames
        for r in f.vision_records
        if r.source_id == "camera_2" and abs(r.timestamp_s - 10.0) < 1e-6
    ]
    assert observed_master_times, "back-camera local t=10.0 record was never observed in any frame"
    assert all(
        target_master_t <= m <= target_master_t + 0.3 for m in observed_master_times
    ), (
        f"back-camera local t=10.0 must surface only within "
        f"[{target_master_t}, {target_master_t + 0.3}] (offset applied exactly once); "
        f"observed at {observed_master_times}"
    )
    assert not any(doubled_master_t - 0.3 <= m <= doubled_master_t + 0.3 for m in observed_master_times), (
        f"offset must not be applied twice (would surface near master_t={doubled_master_t})"
    )

    # The front camera (offset 0.0) must still appear at its own local time.
    front_at_10 = [f for f in frames if abs(f.master_timestamp_s - 10.0) < 0.15]
    assert any(
        r.source_id == "camera_1" and abs(r.timestamp_s - 10.0) < 1e-6
        for f in front_at_10
        for r in f.vision_records
    )


def test_end_to_end_decision_engine_consumes_synchronized_frames(tmp_path: Path) -> None:
    """The full production chain (validated aligner -> build_multimodal_frames
    -> EventSimulationRunner -> MultimodalDecisionEngine) must run without
    error on synchronized dual-camera synthetic evidence."""
    manifest_path = _write_synthetic_manifest(tmp_path, back_offset_s=3.0)
    validated = load_validated_sync_aligner(
        manifest_path, "train_events/event_900", repo_root=tmp_path, allow_candidate_status=True
    )
    processor = _processor(tmp_path)

    front_recs = _front_records(n=30, hop_s=0.5)
    back_recs = _back_records(n=30, hop_s=0.5)
    frames = processor.build_multimodal_frames(
        vision_records=front_recs + back_recs,
        audio_records=[],
        duration_s=30.0,
        stride_s=0.2,
        sync_aligner=validated.aligner,
    )
    runner = EventSimulationRunner()
    result = runner.run_frames(frames, event_id="train_events/event_900", scenario_name="integration_test")
    assert len(result.steps) == len(frames)


def test_unsupported_calibration_blocks_before_fusion(tmp_path: Path) -> None:
    """A PROVISIONAL-verdict event must never reach build_multimodal_frames
    at all -- load_validated_sync_aligner raises first."""
    manifest_path = _write_synthetic_manifest(tmp_path, back_offset_s=3.0, verdict="PROVISIONAL")
    with pytest.raises(CalibrationNotAcceptedError):
        load_validated_sync_aligner(
            manifest_path, "train_events/event_900", repo_root=tmp_path, allow_candidate_status=True
        )


def test_missing_aligner_blocks_dual_camera_merge_via_timing_integrity_error(tmp_path: Path) -> None:
    """Calling build_multimodal_frames with two vision sources and NO
    aligner at all must still raise TimingIntegrityError (the pre-existing
    R04 guard in LayerBEventProcessor), re-confirmed here after this
    session's collector.py changes to prove nothing regressed it."""
    processor = _processor(tmp_path)
    front_recs = _front_records(n=5)
    back_recs = _back_records(n=5)
    with pytest.raises(TimingIntegrityError):
        processor.build_multimodal_frames(
            vision_records=front_recs + back_recs,
            audio_records=[],
            duration_s=10.0,
            stride_s=0.2,
            sync_aligner=None,
        )


def test_single_camera_still_works_without_any_calibration(tmp_path: Path) -> None:
    """Single-camera (no dual-camera fusion attempted) operation must
    continue to work with zero calibration machinery involved."""
    processor = _processor(tmp_path)
    front_recs = _front_records(n=5)
    frames = processor.build_multimodal_frames(
        vision_records=front_recs,
        audio_records=[],
        duration_s=10.0,
        stride_s=0.2,
        sync_aligner=None,
    )
    assert len(frames) > 0
    assert any(r.source_id == "camera_1" for f in frames for r in f.vision_records)
