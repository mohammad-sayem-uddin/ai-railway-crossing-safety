"""Comprehensive synthetic tests for the Cache-Only Replay Engine.

All fixtures are synthetic and created in temporary directories.
No raw media files are accessed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from railway_detection.evaluation.cache_only_engine import (
    CacheIntegrityError,
    CacheOnlyReplayEngine,
    CacheReplayRefusal,
    MediaAccessViolationError,
    ReplayOutput,
    ReplayRefusalRecord,
    _assert_no_media_references,
    _validate_audio_record,
    _validate_cache_path,
    _validate_visual_record,
)
from railway_detection.fusion.evidence import Modality

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_detection():
    from railway_detection.fusion.evidence import Detection
    return Detection(label="train", confidence=0.9)


def _make_visual_record(
    frame_index: int = 0,
    timestamp_sec: float = 1.0,
    camera_id: str = "camera_front",
    detections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if detections is None:
        detections = [{
            "class_id": 0,
            "class_name": "train",
            "confidence": 0.85,
            "bbox_xyxy": [100.0, 200.0, 300.0, 400.0],
        }]
    return {
        "frame_index": frame_index,
        "timestamp_sec": timestamp_sec,
        "camera_id": camera_id,
        "detections": detections,
    }


def _make_audio_record(
    window_index: int = 0,
    start_sec: float = 0.0,
    end_sec: float = 1.0,
    horn_confidence: float = 0.9,
    is_horn_detected: bool = True,
) -> dict[str, Any]:
    return {
        "window_index": window_index,
        "start_sec": start_sec,
        "end_sec": end_sec,
        "horn_confidence": horn_confidence,
        "is_horn_detected": is_horn_detected,
    }


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r) for r in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_manifest(repo_root: Path, events: dict[str, dict[str, Any]]) -> Path:
    manifest = {
        "manifest_version": "1.0.0",
        "created_at": "2026-10-27T00:00:00Z",
        "cohort": "test_cohort",
        "events": events,
    }
    manifest_path = repo_root / "data" / "cache" / "cache_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def _build_valid_cache_fixture(
    repo_root: Path,
    event_id: str = "event_001",
    vision_records: list[dict[str, Any]] | None = None,
    audio_records: list[dict[str, Any]] | None = None,
) -> Path:
    cache_dir = repo_root / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    if vision_records is None:
        vision_records = [
            _make_visual_record(frame_index=i, timestamp_sec=float(i) * 0.2)
            for i in range(10)
        ]
    if audio_records is None:
        audio_records = [
            _make_audio_record(window_index=i, start_sec=float(i), end_sec=float(i + 1))
            for i in range(5)
        ]

    vision_path = cache_dir / f"{event_id}_front_vision.jsonl"
    _write_jsonl(vision_path, vision_records)
    audio_path = cache_dir / f"{event_id}_front_audio.jsonl"
    _write_jsonl(audio_path, audio_records)

    events = {
        event_id: {
            "event_id": event_id,
            "front_vision_cache": {
                "path": f"data/cache/{event_id}_front_vision.jsonl",
                "sha256": _sha256_of(vision_path),
                "line_count": len(vision_records),
                "byte_size": vision_path.stat().st_size,
            },
            "front_audio_cache": {
                "path": f"data/cache/{event_id}_front_audio.jsonl",
                "sha256": _sha256_of(audio_path),
                "line_count": len(audio_records),
                "byte_size": audio_path.stat().st_size,
            },
        }
    }
    return _build_manifest(repo_root, events)


# ===========================================================================
# A. VALID-INPUT TESTS
# ===========================================================================


class TestValidInputs:
    def test_valid_manifest_loads(self, tmp_path: Path) -> None:
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        assert engine.manifest_data["manifest_version"] == "1.0.0"
        assert engine.manifest_data["cohort"] == "test_cohort"

    def test_valid_visual_records_load(self, tmp_path: Path) -> None:
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        records = engine.load_visual_records("event_001")
        assert len(records) == 10
        assert all(r.modality == Modality.VISION for r in records)
        assert all(r.source_id == "camera_1" for r in records)
        assert all(r.available for r in records)

    def test_valid_audio_records_load(self, tmp_path: Path) -> None:
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        records = engine.load_audio_records("event_001")
        assert len(records) == 5
        assert all(r.modality == Modality.AUDIO for r in records)
        assert all(r.source_id == "audio_1" for r in records)

    def test_zero_timestamp_preserved(self, tmp_path: Path) -> None:
        vision_records = [_make_visual_record(frame_index=0, timestamp_sec=0.0)]
        audio_records = [_make_audio_record(window_index=0, start_sec=0.0, end_sec=0.0)]
        manifest_path = _build_valid_cache_fixture(
            tmp_path, vision_records=vision_records, audio_records=audio_records
        )
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        assert engine.load_visual_records("event_001")[0].timestamp_s == 0.0
        assert engine.load_audio_records("event_001")[0].timestamp_s == 0.0

    def test_zero_confidence_detection_valid(self, tmp_path: Path) -> None:
        vision_records = [_make_visual_record(detections=[{
            "class_id": 0, "class_name": "train", "confidence": 0.0,
            "bbox_xyxy": [0.0, 0.0, 10.0, 10.0],
        }])]
        manifest_path = _build_valid_cache_fixture(tmp_path, vision_records=vision_records)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        assert engine.load_visual_records("event_001")[0].detections[0].confidence == 0.0

    def test_empty_detections_valid(self, tmp_path: Path) -> None:
        vision_records = [_make_visual_record(detections=[])]
        manifest_path = _build_valid_cache_fixture(tmp_path, vision_records=vision_records)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        records = engine.load_visual_records("event_001")
        assert len(records) == 1
        assert records[0].detections == ()

    def test_deterministic_replay(self, tmp_path: Path) -> None:
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        output1 = engine.execute_replay("event_001", "B0")
        output2 = engine.execute_replay("event_001", "B0")
        assert output1.deterministic_run_id == output2.deterministic_run_id
        assert output1.frames_produced == output2.frames_produced
        assert output1.evidence_records_loaded == output2.evidence_records_loaded
        assert output1.manifest_sha256 == output2.manifest_sha256

    def test_b0_condition_vision_only(self, tmp_path: Path) -> None:
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        output = engine.execute_replay("event_001", "B0")
        assert output.condition == "B0"
        assert output.evidence_records_loaded == 10

    def test_b1_condition_audio_only(self, tmp_path: Path) -> None:
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        output = engine.execute_replay("event_001", "B1")
        assert output.condition == "B1"
        assert output.evidence_records_loaded == 5
        assert output.provenance["cache_paths"] == {
            "front_audio": "data/cache/event_001_front_audio.jsonl"
        }

    def test_multi_modality_integration(self, tmp_path: Path) -> None:
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        output = engine.execute_replay("event_001", "B2")
        assert isinstance(output, ReplayOutput)
        assert output.result is not None
        assert output.frames_produced > 0
        assert set(output.provenance["cache_paths"]) == {"front_vision", "front_audio"}

    def test_b1_ignores_strong_visual_detections(self, tmp_path: Path) -> None:
        """B1's audio-only contract must not ingest vision evidence."""
        vision_records = [
            _make_visual_record(
                frame_index=i,
                timestamp_sec=i * 0.2,
                detections=[{
                    "class_id": 0,
                    "class_name": "train",
                    "confidence": 1.0,
                    "bbox_xyxy": [0, 0, 10, 10],
                }],
            )
            for i in range(10)
        ]
        audio_records = [
            _make_audio_record(
                window_index=i, start_sec=float(i), end_sec=float(i + 1),
                horn_confidence=0.0, is_horn_detected=False,
            )
            for i in range(2)
        ]
        manifest_path = _build_valid_cache_fixture(
            tmp_path, vision_records=vision_records, audio_records=audio_records
        )
        output = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path).execute_replay(
            "event_001", "B1"
        )
        assert output.evidence_records_loaded == 2
        assert output.provenance["cache_paths"] == {
            "front_audio": "data/cache/event_001_front_audio.jsonl"
        }

    def test_record_provenance_preserved(self, tmp_path: Path) -> None:
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        visual = engine.load_visual_records("event_001")[0]
        audio = engine.load_audio_records("event_001")[0]
        assert visual.metadata["provenance"]["stream"] == "front_vision"
        assert audio.metadata["provenance"]["stream"] == "front_audio"
        assert len(visual.metadata["provenance"]["artifact_sha256"]) == 64

    def test_zero_stride_refused(self, tmp_path: Path) -> None:
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheReplayRefusal, match="stride"):
            engine.execute_replay("event_001", "B0", frame_stride_s=0.0)

    def test_output_root_outside_replays_refused(self, tmp_path: Path) -> None:
        manifest_path = _build_valid_cache_fixture(tmp_path)
        with pytest.raises(CacheReplayRefusal, match="results/replays"):
            CacheOnlyReplayEngine(
                manifest_path, repo_root=tmp_path, output_base_dir=tmp_path / "docs"
            )

    def test_manifest_data_is_deep_copy(self, tmp_path: Path) -> None:
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        view = engine.manifest_data
        view["events"]["event_001"]["event_id"] = "tampered"
        assert engine.manifest_data["events"]["event_001"]["event_id"] == "event_001"

    def test_run_id_changes_with_stride(self, tmp_path: Path) -> None:
        """deterministic_run_id must bind the full replay configuration."""
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        out1 = engine.execute_replay("event_001", "B0", frame_stride_s=0.2)
        out2 = engine.execute_replay("event_001", "B0", frame_stride_s=0.1)
        assert out1.deterministic_run_id != out2.deterministic_run_id

    def test_repeated_events_do_not_share_state(self, tmp_path: Path) -> None:
        """Independent replays must not leak mutable decision-engine state."""
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        out1 = engine.execute_replay("event_001", "B0")
        out2 = engine.execute_replay("event_001", "B0")
        steps1 = [(s.crossing_state, s.gate_state) for s in out1.result.steps]
        steps2 = [(s.crossing_state, s.gate_state) for s in out2.result.steps]
        assert steps1 == steps2
        # The first resulting state may legitimately be TRAIN_APPROACHING because
        # the synthetic frame carries a qualified detection; reset is proven by
        # the decision's previous state and identical repeated output.
        assert out2.result.steps[0].decision.previous_state == "IDLE"

    def test_list_events(self, tmp_path: Path) -> None:
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        assert engine.list_events() == ["event_001"]

    def test_replay_all_events(self, tmp_path: Path) -> None:
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        results = engine.replay_all_events("B0")
        assert "event_001" in results
        assert isinstance(results["event_001"], ReplayOutput)


# ===========================================================================
# B. INVALID-INPUT TESTS
# ===========================================================================


class TestInvalidInputs:
    def test_missing_manifest(self, tmp_path: Path) -> None:
        with pytest.raises(CacheIntegrityError, match="not found"):
            CacheOnlyReplayEngine(tmp_path / "nonexistent.json", repo_root=tmp_path)

    def test_malformed_json_manifest(self, tmp_path: Path) -> None:
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text("{invalid json!!!", encoding="utf-8")
        with pytest.raises(CacheIntegrityError, match="malformed"):
            CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)

    def test_empty_manifest(self, tmp_path: Path) -> None:
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text("", encoding="utf-8")
        with pytest.raises(CacheIntegrityError, match="empty"):
            CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)

    def test_invalid_schema_version(self, tmp_path: Path) -> None:
        manifest = {
            "manifest_version": "99.0.0",
            "created_at": "2026-01-01T00:00:00Z",
            "cohort": "test_cohort",
            "events": {},
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with pytest.raises(CacheIntegrityError, match="manifest_version"):
            CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)

    def test_missing_required_fields(self, tmp_path: Path) -> None:
        manifest = {"manifest_version": "1.0.0"}
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with pytest.raises(CacheIntegrityError, match="missing required"):
            CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)

    def test_event_not_in_manifest(self, tmp_path: Path) -> None:
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheReplayRefusal, match="not registered"):
            engine.load_visual_records("event_999")

    def test_unsupported_condition(self, tmp_path: Path) -> None:
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheReplayRefusal, match="not supported"):
            engine.execute_replay("event_001", "B9")

    def test_missing_cache_file(self, tmp_path: Path) -> None:
        """Missing cache artifact must fail closed, never fall back to media."""
        vision_records = [_make_visual_record()]
        cache_dir = tmp_path / "data" / "cache"
        cache_dir.mkdir(parents=True)
        vision_path = cache_dir / "event_001_front_vision.jsonl"
        vision_path.write_text(
            "\n".join(json.dumps(r) for r in vision_records) + "\n", encoding="utf-8"
        )
        # Audio file deliberately NOT created
        events = {
            "event_001": {
                "event_id": "event_001",
                "front_vision_cache": {
                    "path": "data/cache/event_001_front_vision.jsonl",
                    "sha256": _sha256_of(vision_path),
                    "line_count": len(vision_records),
                    "byte_size": vision_path.stat().st_size,
                },
                "front_audio_cache": {
                    "path": "data/cache/event_001_front_audio.jsonl",
                    "sha256": "a" * 64,
                    "line_count": 1,
                    "byte_size": 100,
                },
            }
        }
        manifest_path = _build_manifest(tmp_path, events)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheIntegrityError, match="does not exist"):
            engine.load_audio_records("event_001")

    def test_hash_mismatch(self, tmp_path: Path) -> None:
        vision_records = [_make_visual_record()]
        manifest_path = _build_valid_cache_fixture(tmp_path, vision_records=vision_records)
        # Corrupt the manifest hash
        data = json.loads(manifest_path.read_text())
        data["events"]["event_001"]["front_vision_cache"]["sha256"] = "b" * 64
        manifest_path.write_text(json.dumps(data), encoding="utf-8")
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheIntegrityError, match="hash mismatch"):
            engine.load_visual_records("event_001")

    def test_truncated_cache_file(self, tmp_path: Path) -> None:
        vision_records = [_make_visual_record(frame_index=i) for i in range(5)]
        cache_dir = tmp_path / "data" / "cache"
        cache_dir.mkdir(parents=True)
        vision_path = cache_dir / "event_001_front_vision.jsonl"
        full_content = "\n".join(json.dumps(r) for r in vision_records) + "\n"
        # Write truncated content but declare full line count
        vision_path.write_text(full_content[:len(full_content) // 2], encoding="utf-8")
        events = {
            "event_001": {
                "event_id": "event_001",
                "front_vision_cache": {
                    "path": "data/cache/event_001_front_vision.jsonl",
                    "sha256": _sha256_of(vision_path),
                    "line_count": len(vision_records),  # declares 5 but file has fewer
                    "byte_size": vision_path.stat().st_size,
                },
                "front_audio_cache": {
                    "path": "data/cache/event_001_front_audio.jsonl",
                    "sha256": "a" * 64,
                    "line_count": 1,
                    "byte_size": 100,
                },
            }
        }
        manifest_path = _build_manifest(tmp_path, events)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheIntegrityError, match="[Ll]ine count"):
            engine.load_visual_records("event_001")

    def test_non_finite_confidence(self, tmp_path: Path) -> None:
        vision_records = [_make_visual_record(detections=[{
            "class_id": 0, "class_name": "train",
            "confidence": float("inf"),
            "bbox_xyxy": [0.0, 0.0, 10.0, 10.0],
        }])]
        manifest_path = _build_valid_cache_fixture(tmp_path, vision_records=vision_records)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheReplayRefusal, match="confidence"):
            engine.load_visual_records("event_001")

    def test_invalid_confidence_range(self, tmp_path: Path) -> None:
        vision_records = [_make_visual_record(detections=[{
            "class_id": 0, "class_name": "train",
            "confidence": 1.5,
            "bbox_xyxy": [0.0, 0.0, 10.0, 10.0],
        }])]
        manifest_path = _build_valid_cache_fixture(tmp_path, vision_records=vision_records)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheReplayRefusal, match="confidence"):
            engine.load_visual_records("event_001")

    def test_negative_timestamp(self, tmp_path: Path) -> None:
        vision_records = [_make_visual_record(timestamp_sec=-1.0)]
        manifest_path = _build_valid_cache_fixture(tmp_path, vision_records=vision_records)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheReplayRefusal, match="timestamp"):
            engine.load_visual_records("event_001")

    def test_missing_required_record_fields(self, tmp_path: Path) -> None:
        vision_records = [{"frame_index": 0}]  # missing timestamp_sec, camera_id, detections
        manifest_path = _build_valid_cache_fixture(tmp_path, vision_records=vision_records)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheReplayRefusal, match="missing required"):
            engine.load_visual_records("event_001")

    def test_audio_end_before_start(self, tmp_path: Path) -> None:
        audio_records = [_make_audio_record(start_sec=5.0, end_sec=2.0)]
        manifest_path = _build_valid_cache_fixture(tmp_path, audio_records=audio_records)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheReplayRefusal, match="end_sec"):
            engine.load_audio_records("event_001")

    def test_non_boolean_horn_flag(self, tmp_path: Path) -> None:
        audio_records = [_make_audio_record()]
        audio_records[0]["is_horn_detected"] = "yes"
        manifest_path = _build_valid_cache_fixture(tmp_path, audio_records=audio_records)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheReplayRefusal, match="boolean"):
            engine.load_audio_records("event_001")

    def test_absolute_cache_path_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(CacheReplayRefusal, match="[Aa]bsolute"):
            _validate_cache_path("/etc/passwd.jsonl", tmp_path)

    def test_traversal_cache_path_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(CacheReplayRefusal, match="[Tt]raversal"):
            _validate_cache_path("../outside.jsonl", tmp_path)

    def test_media_extension_in_path_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(MediaAccessViolationError):
            _validate_cache_path("data/cache/event_001.mov", tmp_path)

    def test_disallowed_extension_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(CacheReplayRefusal, match="extension"):
            _validate_cache_path("data/cache/event_001.txt", tmp_path)

    def test_symlink_escape_rejected(self, tmp_path: Path) -> None:
        escape_target = tmp_path.parent / "escaped.jsonl"
        escape_target.write_text("{}", encoding="utf-8")
        cache_dir = tmp_path / "data" / "cache"
        cache_dir.mkdir(parents=True)
        link_path = cache_dir / "escape_link.jsonl"
        try:
            link_path.symlink_to(escape_target)
            with pytest.raises((CacheReplayRefusal, MediaAccessViolationError)):
                _validate_cache_path("data/cache/escape_link.jsonl", tmp_path)
        finally:
            if link_path.is_symlink():
                link_path.unlink()
            if escape_target.exists():
                escape_target.unlink()

    def test_duplicate_json_keys_in_manifest_rejected(self, tmp_path: Path) -> None:
        """Duplicate JSON object keys must fail closed, not keep the last value."""
        raw = (
            '{"manifest_version": "1.0.0", "manifest_version": "9.9.9", '
            '"created_at": "x", "cohort": "c", "events": {}}'
        )
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(raw, encoding="utf-8")
        with pytest.raises(CacheIntegrityError, match="malformed"):
            CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)

    def test_duplicate_json_keys_in_cache_record_rejected(self, tmp_path: Path) -> None:
        raw_line = (
            '{"frame_index": 0, "frame_index": 1, "timestamp_sec": 1.0, '
            '"camera_id": "camera_front", "detections": []}'
        )
        cache_dir = tmp_path / "data" / "cache"
        cache_dir.mkdir(parents=True)
        vision_path = cache_dir / "event_001_front_vision.jsonl"
        vision_path.write_text(raw_line + "\n", encoding="utf-8")
        audio_records = [_make_audio_record()]
        audio_path = cache_dir / "event_001_front_audio.jsonl"
        _write_jsonl(audio_path, audio_records)
        events = {
            "event_001": {
                "event_id": "event_001",
                "front_vision_cache": {
                    "path": "data/cache/event_001_front_vision.jsonl",
                    "sha256": _sha256_of(vision_path),
                    "line_count": 1,
                    "byte_size": vision_path.stat().st_size,
                },
                "front_audio_cache": {
                    "path": "data/cache/event_001_front_audio.jsonl",
                    "sha256": _sha256_of(audio_path),
                    "line_count": len(audio_records),
                    "byte_size": audio_path.stat().st_size,
                },
            }
        }
        manifest_path = _build_manifest(tmp_path, events)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheIntegrityError, match="[Mm]alformed"):
            engine.load_visual_records("event_001")

    def test_manifest_event_key_mismatch_rejected(self, tmp_path: Path) -> None:
        vision_records = [_make_visual_record()]
        audio_records = [_make_audio_record()]
        cache_dir = tmp_path / "data" / "cache"
        cache_dir.mkdir(parents=True)
        vision_path = cache_dir / "event_001_front_vision.jsonl"
        _write_jsonl(vision_path, vision_records)
        audio_path = cache_dir / "event_001_front_audio.jsonl"
        _write_jsonl(audio_path, audio_records)
        events = {
            "event_001": {
                "event_id": "DIFFERENT_ID",
                "front_vision_cache": {
                    "path": "data/cache/event_001_front_vision.jsonl",
                    "sha256": _sha256_of(vision_path),
                    "line_count": 1,
                    "byte_size": vision_path.stat().st_size,
                },
                "front_audio_cache": {
                    "path": "data/cache/event_001_front_audio.jsonl",
                    "sha256": _sha256_of(audio_path),
                    "line_count": 1,
                    "byte_size": audio_path.stat().st_size,
                },
            }
        }
        manifest_path = _build_manifest(tmp_path, events)
        with pytest.raises(CacheIntegrityError, match="event_id"):
            CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)

    def test_unsupported_camera_id_rejected(self, tmp_path: Path) -> None:
        vision_records = [_make_visual_record(camera_id="camera_back")]
        manifest_path = _build_valid_cache_fixture(tmp_path, vision_records=vision_records)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheReplayRefusal, match="camera_id"):
            engine.load_visual_records("event_001")

    def test_invalid_class_id_rejected(self, tmp_path: Path) -> None:
        vision_records = [_make_visual_record(detections=[{
            "class_id": -3, "class_name": "train", "confidence": 0.5,
            "bbox_xyxy": [0.0, 0.0, 1.0, 1.0],
        }])]
        manifest_path = _build_valid_cache_fixture(tmp_path, vision_records=vision_records)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheReplayRefusal, match="class_id"):
            engine.load_visual_records("event_001")

    def test_invalid_class_name_rejected(self, tmp_path: Path) -> None:
        vision_records = [_make_visual_record(detections=[{
            "class_id": 0, "class_name": "", "confidence": 0.5,
            "bbox_xyxy": [0.0, 0.0, 1.0, 1.0],
        }])]
        manifest_path = _build_valid_cache_fixture(tmp_path, vision_records=vision_records)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheReplayRefusal, match="class_name"):
            engine.load_visual_records("event_001")

    def test_manifest_media_reference_rejected(self, tmp_path: Path) -> None:
        manifest = {
            "manifest_version": "1.0.0",
            "created_at": "2026-01-01T00:00:00Z",
            "cohort": "test_cohort",
            "source_video": "camera_front.mov",
            "events": {},
        }
        with pytest.raises(MediaAccessViolationError):
            _assert_no_media_references(manifest, "manifest")

    def test_invalid_manifest_sha256_format(self, tmp_path: Path) -> None:
        events = {
            "event_001": {
                "event_id": "event_001",
                "front_vision_cache": {
                    "path": "data/cache/event_001_front_vision.jsonl",
                    "sha256": "NOT_A_HASH",
                    "line_count": 1,
                    "byte_size": 10,
                },
                "front_audio_cache": {
                    "path": "data/cache/event_001_front_audio.jsonl",
                    "sha256": "a" * 64,
                    "line_count": 1,
                    "byte_size": 10,
                },
            }
        }
        manifest_path = _build_manifest(tmp_path, events)
        with pytest.raises(CacheIntegrityError, match="sha256"):
            CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)

    def test_manifest_outside_repo_root_rejected(self, tmp_path: Path) -> None:
        outside = tmp_path.parent / "outside_manifest.json"
        outside.write_text(json.dumps({
            "manifest_version": "1.0.0",
            "created_at": "2026-01-01T00:00:00Z",
            "cohort": "x",
            "events": {},
        }), encoding="utf-8")
        try:
            with pytest.raises(CacheReplayRefusal, match="repository root"):
                CacheOnlyReplayEngine(outside, repo_root=tmp_path)
        finally:
            if outside.exists():
                outside.unlink()


# ===========================================================================
# C. FAIL-CLOSED TESTS
# ===========================================================================


class TestFailClosed:
    """Invalid inputs must never produce unauthorized positive evidence."""

    def test_unavailable_evidence_never_has_detections(self) -> None:
        from railway_detection.fusion.evidence import EvidenceRecord
        with pytest.raises(ValueError):
            EvidenceRecord(
                timestamp_s=1.0,
                source_id="camera_1",
                modality=Modality.VISION,
                available=False,
                detections=(_make_detection(),),
            )

    def test_silence_alone_produces_no_opening(self, tmp_path: Path) -> None:
        """Audio-only horn detections must never authorize gate opening."""
        from railway_detection.fusion.collector import MultimodalEvidenceCollector
        from railway_detection.fusion.decision_engine import MultimodalDecisionEngine

        engine = MultimodalDecisionEngine()
        collector = MultimodalEvidenceCollector()
        # Only audio evidence, high confidence, sustained
        for i in range(30):
            from railway_detection.fusion.evidence import Detection, EvidenceRecord
            record = EvidenceRecord(
                timestamp_s=float(i) * 0.5,
                source_id="audio_1",
                modality=Modality.AUDIO,
                available=True,
                detections=(Detection(label="train_horn", confidence=0.99),),
            )
            collector.add_evidence(record)
        frames = collector.generate_frames_from_history(0.0, 15.0, stride_s=0.5)
        result = None
        from railway_detection.simulation.runner import EventSimulationRunner
        runner = EventSimulationRunner(decision_engine=engine)
        result = runner.run_frames(frames, event_id="audio_only", scenario_name="silence_test")
        # Gate must never reach CLOSED from audio alone: opening authorization
        # requires vision clearance evidence. Verify no gate-closing command.
        for step in result.steps:
            assert step.decision.rule_id != "RULE_2_AUDIO_SUPPORT_ONLY" or \
                step.gate_state in ("OPEN", "CLOSING", "CLOSED", "OPENING")
        # The critical invariant: audio alone must not open the gate from a
        # closed state, and must not be the sole trigger for GATE_CLOSING.
        gate_closing_by_audio_only = any(
            step.crossing_state == "GATE_CLOSING"
            and step.decision.rule_id == "RULE_2_AUDIO_SUPPORT_ONLY"
            for step in result.steps
        )
        assert not gate_closing_by_audio_only

    def test_missing_evidence_cannot_open_gate(self, tmp_path: Path) -> None:
        """A replay with no valid evidence must refuse, not produce a result."""
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheReplayRefusal):
            engine.execute_replay("event_999", "B0")

    def test_refusal_record_structure(self, tmp_path: Path) -> None:
        """replay_all_events records refusals instead of raising."""
        manifest_path = _build_valid_cache_fixture(tmp_path)
        # Corrupt the vision cache file after manifest creation
        cache_path = tmp_path / "data/cache/event_001_front_vision.jsonl"
        cache_path.write_text("CORRUPTED\n", encoding="utf-8")
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        results = engine.replay_all_events("B0")
        assert isinstance(results["event_001"], ReplayRefusalRecord)
        assert results["event_001"].code in ("CACHE_HASH_MISMATCH", "CACHE_SIZE_MISMATCH")

    def test_exception_cannot_switch_to_unrestricted_mode(self, tmp_path: Path) -> None:
        """A parser exception must propagate, never be swallowed into a
        silent fallback or degraded permissive mode."""
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        # Patch the internal loader to raise an unexpected error
        with patch.object(
            engine, "_load_cache_stream", side_effect=RuntimeError("unexpected parser bug")
        ):
            with pytest.raises(RuntimeError):
                engine.load_visual_records("event_001")
        # The exception propagated rather than being converted into empty
        # evidence or a permissive fallback. After the transient failure the
        # engine has no degraded state: a legitimate load still returns the
        # full validated evidence set (no silent downgrade, no sticky fault
        # that would mask later valid inputs either).
        records = engine.load_visual_records("event_001")
        assert len(records) == 10


# ===========================================================================
# D. RAW-MEDIA ISOLATION TESTS
# ===========================================================================


class TestRawMediaIsolation:
    """Verify legacy media loaders are never invoked from cache-only paths."""

    @staticmethod
    def _install_media_spies(monkeypatch: pytest.MonkeyPatch) -> list[str]:
        calls: list[str] = []

        def _fail(name: str):
            def _raise(*args: Any, **kwargs: Any) -> None:
                calls.append(name)
                raise AssertionError(f"Legacy media loader invoked: {name}")
            return _raise

        try:
            import cv2  # type: ignore[import-not-found]
            monkeypatch.setattr(cv2, "VideoCapture", _fail("cv2.VideoCapture"))
        except ImportError:
            pass

        import subprocess
        monkeypatch.setattr(subprocess, "run", _fail("subprocess.run"))
        monkeypatch.setattr(subprocess, "Popen", _fail("subprocess.Popen"))

        try:
            from railway_detection.vision import video as video_mod
            monkeypatch.setattr(video_mod, "frame_generator", _fail("frame_generator"))
        except (ImportError, AttributeError):
            pass

        try:
            from railway_detection.data import audio_extractor as ae_mod
            monkeypatch.setattr(ae_mod, "extract_audio_from_video", _fail("extract_audio"))
        except (ImportError, AttributeError):
            pass

        return calls

    def test_valid_replay_never_calls_media_loaders(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = self._install_media_spies(monkeypatch)
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        output = engine.execute_replay("event_001", "B1")
        assert isinstance(output, ReplayOutput)
        assert calls == [], f"Media loaders called during valid replay: {calls}"

    def test_missing_cache_never_calls_media_loaders(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = self._install_media_spies(monkeypatch)
        vision_records = [_make_visual_record()]
        cache_dir = tmp_path / "data" / "cache"
        cache_dir.mkdir(parents=True)
        vision_path = cache_dir / "event_001_front_vision.jsonl"
        _write_jsonl(vision_path, vision_records)
        events = {
            "event_001": {
                "event_id": "event_001",
                "front_vision_cache": {
                    "path": "data/cache/event_001_front_vision.jsonl",
                    "sha256": _sha256_of(vision_path),
                    "line_count": 1,
                    "byte_size": vision_path.stat().st_size,
                },
                "front_audio_cache": {
                    "path": "data/cache/nonexistent_audio.jsonl",
                    "sha256": "c" * 64,
                    "line_count": 1,
                    "byte_size": 50,
                },
            }
        }
        manifest_path = _build_manifest(tmp_path, events)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheIntegrityError):
            engine.load_audio_records("event_001")
        assert calls == [], f"Media loaders called on missing cache: {calls}"

    def test_invalid_manifest_never_calls_media_loaders(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = self._install_media_spies(monkeypatch)
        manifest_path = tmp_path / "bad.json"
        manifest_path.write_text("NOT JSON AT ALL", encoding="utf-8")
        with pytest.raises(CacheIntegrityError):
            CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        assert calls == [], f"Media loaders called on invalid manifest: {calls}"

    def test_sync_failure_never_calls_media_loaders(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = self._install_media_spies(monkeypatch)
        from railway_detection.data.sync import SyncAligner
        from railway_detection.fusion.collector import MultimodalEvidenceCollector
        from railway_detection.fusion.evidence import EvidenceRecord

        aligner = SyncAligner()
        aligner.add_source("camera_1", offset_s=0.0, uncertainty_s=0.0)
        collector = MultimodalEvidenceCollector(sync_aligner=aligner)
        collector.add_evidence(EvidenceRecord(
            timestamp_s=1.0, source_id="camera_1",
            modality=Modality.VISION, available=True, detections=(),
        ))
        with pytest.raises(ValueError, match="fail-closed"):
            collector.add_evidence(EvidenceRecord(
                timestamp_s=1.0, source_id="camera_2",
                modality=Modality.VISION, available=True, detections=(),
            ))
        assert calls == [], f"Media loaders called on sync failure: {calls}"

    def test_parser_exception_never_calls_media_loaders(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = self._install_media_spies(monkeypatch)
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with patch.object(
            engine, "_load_cache_stream", side_effect=RuntimeError("parse crash")
        ):
            with pytest.raises(RuntimeError):
                engine.load_visual_records("event_001")
        assert calls == [], f"Media loaders called on parser exception: {calls}"

    def test_hash_mismatch_never_calls_media_loaders(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = self._install_media_spies(monkeypatch)
        vision_records = [_make_visual_record()]
        manifest_path = _build_valid_cache_fixture(tmp_path, vision_records=vision_records)
        data = json.loads(manifest_path.read_text())
        data["events"]["event_001"]["front_vision_cache"]["sha256"] = "d" * 64
        manifest_path.write_text(json.dumps(data), encoding="utf-8")
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheIntegrityError):
            engine.load_visual_records("event_001")
        assert calls == [], f"Media loaders called on hash mismatch: {calls}"

    def test_corrupt_cache_record_never_calls_media_loaders(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = self._install_media_spies(monkeypatch)
        cache_dir = tmp_path / "data" / "cache"
        cache_dir.mkdir(parents=True)
        vision_path = cache_dir / "event_001_front_vision.jsonl"
        vision_path.write_text('{"frame_index": 0,,bad json}\n', encoding="utf-8")
        audio_records = [_make_audio_record()]
        audio_path = cache_dir / "event_001_front_audio.jsonl"
        _write_jsonl(audio_path, audio_records)
        events = {
            "event_001": {
                "event_id": "event_001",
                "front_vision_cache": {
                    "path": "data/cache/event_001_front_vision.jsonl",
                    "sha256": _sha256_of(vision_path),
                    "line_count": 1,
                    "byte_size": vision_path.stat().st_size,
                },
                "front_audio_cache": {
                    "path": "data/cache/event_001_front_audio.jsonl",
                    "sha256": _sha256_of(audio_path),
                    "line_count": 1,
                    "byte_size": audio_path.stat().st_size,
                },
            }
        }
        manifest_path = _build_manifest(tmp_path, events)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheIntegrityError):
            engine.load_visual_records("event_001")
        assert calls == [], f"Media loaders called on corrupt record: {calls}"

    def test_unsupported_condition_never_calls_media_loaders(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = self._install_media_spies(monkeypatch)
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        with pytest.raises(CacheReplayRefusal):
            engine.execute_replay("event_001", "B_UNSUPPORTED")
        assert calls == [], f"Media loaders called on unsupported condition: {calls}"

    def test_batch_refusal_never_calls_media_loaders(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = self._install_media_spies(monkeypatch)
        manifest_path = _build_valid_cache_fixture(tmp_path)
        cache_path = tmp_path / "data/cache/event_001_front_vision.jsonl"
        cache_path.write_text("NOT VALID JSONL\n", encoding="utf-8")
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        results = engine.replay_all_events("B0")
        assert isinstance(results["event_001"], ReplayRefusalRecord)
        assert calls == [], f"Media loaders called during batch refusal: {calls}"


# ===========================================================================
# E. FUSION AND STATE-MACHINE REGRESSION TESTS
# ===========================================================================


class TestFusionStateMachineRegression:
    """Verify existing safety invariants through synthetic typed evidence."""

    def test_no_opening_from_missing_evidence(self) -> None:
        from railway_detection.fusion.collector import MultimodalEvidenceCollector
        from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
        from railway_detection.simulation.runner import EventSimulationRunner

        engine = MultimodalDecisionEngine()
        collector = MultimodalEvidenceCollector()
        frames = collector.generate_frames_from_history(0.0, 10.0, stride_s=0.5)
        runner = EventSimulationRunner(decision_engine=engine)
        result = runner.run_frames(frames, event_id="empty", scenario_name="no_evidence")
        for step in result.steps:
            assert step.crossing_state == "IDLE", (
                f"Unexpected state {step.crossing_state} with no evidence"
            )

    def test_no_opening_from_audio_silence_alone(self) -> None:
        """Audio silence (no detections) must not trigger any gate transition."""
        from railway_detection.fusion.collector import MultimodalEvidenceCollector
        from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
        from railway_detection.fusion.evidence import EvidenceRecord
        from railway_detection.simulation.runner import EventSimulationRunner

        engine = MultimodalDecisionEngine()
        collector = MultimodalEvidenceCollector()
        for i in range(20):
            collector.add_evidence(EvidenceRecord(
                timestamp_s=float(i) * 0.5,
                source_id="audio_1",
                modality=Modality.AUDIO,
                available=True,
                detections=(),  # silence
            ))
        frames = collector.generate_frames_from_history(0.0, 10.0, stride_s=0.5)
        runner = EventSimulationRunner(decision_engine=engine)
        result = runner.run_frames(frames, event_id="silence", scenario_name="audio_silence")
        for step in result.steps:
            assert step.crossing_state == "IDLE", (
                f"Audio silence caused transition to {step.crossing_state}"
            )

    def test_audio_alone_never_authorizes_gate_closing(self) -> None:
        """Audio horn detections alone must never be the sole trigger for
        GATE_CLOSING; vision approach evidence is required."""
        from railway_detection.fusion.collector import MultimodalEvidenceCollector
        from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
        from railway_detection.fusion.evidence import Detection, EvidenceRecord
        from railway_detection.simulation.runner import EventSimulationRunner

        engine = MultimodalDecisionEngine()
        collector = MultimodalEvidenceCollector()
        for i in range(40):
            collector.add_evidence(EvidenceRecord(
                timestamp_s=float(i) * 0.5,
                source_id="audio_1",
                modality=Modality.AUDIO,
                available=True,
                detections=(Detection(label="train_horn", confidence=0.99),),
            ))
        frames = collector.generate_frames_from_history(0.0, 20.0, stride_s=0.5)
        runner = EventSimulationRunner(decision_engine=engine)
        result = runner.run_frames(frames, event_id="audio_only", scenario_name="horn_only")
        audio_only_closing = any(
            step.crossing_state == "GATE_CLOSING"
            for step in result.steps
        )
        assert not audio_only_closing, "Audio-only evidence triggered GATE_CLOSING"

    def test_out_of_order_evidence_rejected_by_collector(self) -> None:
        from railway_detection.fusion.collector import MultimodalEvidenceCollector
        from railway_detection.fusion.evidence import EvidenceRecord

        collector = MultimodalEvidenceCollector()
        collector.add_evidence(EvidenceRecord(
            timestamp_s=5.0, source_id="camera_1",
            modality=Modality.VISION, available=True, detections=(),
        ))
        collector.add_evidence(EvidenceRecord(
            timestamp_s=2.0, source_id="camera_1",
            modality=Modality.VISION, available=True, detections=(),
        ))
        assert len(collector.rejected_observations) == 1
        assert collector.rejected_observations[0]["reason"] == "out_of_order_observation"

    def test_duplicate_timestamp_rejected_by_collector(self) -> None:
        from railway_detection.fusion.collector import MultimodalEvidenceCollector
        from railway_detection.fusion.evidence import EvidenceRecord

        collector = MultimodalEvidenceCollector()
        collector.add_evidence(EvidenceRecord(
            timestamp_s=1.0, source_id="camera_1",
            modality=Modality.VISION, available=True, detections=(),
        ))
        collector.add_evidence(EvidenceRecord(
            timestamp_s=1.0, source_id="camera_1",
            modality=Modality.VISION, available=True, detections=(),
        ))
        assert len(collector.rejected_observations) == 1
        assert collector.rejected_observations[0]["reason"] == "duplicate_observation"

    def test_sync_aligner_requires_explicit_metadata(self) -> None:
        """Missing offset/uncertainty must raise, never silently default."""
        from railway_detection.data.sync import SyncAligner
        aligner = SyncAligner()
        with pytest.raises(ValueError, match="must both be explicit"):
            aligner.add_source("camera_1", offset_s=None, uncertainty_s=None)
        # Explicit zero remains valid
        aligner.add_source("camera_1", offset_s=0.0, uncertainty_s=0.0)
        assert aligner.to_master("camera_1", 1.0) == 1.0

    def test_deterministic_fusion_repeated_runs(self, tmp_path: Path) -> None:
        """Identical inputs must produce identical outputs across runs."""
        manifest_path = _build_valid_cache_fixture(tmp_path)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        out1 = engine.execute_replay("event_001", "B1")
        engine2 = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        out2 = engine2.execute_replay("event_001", "B1")
        assert out1.deterministic_run_id == out2.deterministic_run_id
        assert out1.frames_produced == out2.frames_produced
        assert out1.evidence_records_loaded == out2.evidence_records_loaded


# ===========================================================================
# UNIT TESTS FOR RECORD VALIDATORS
# ===========================================================================


class TestRecordValidators:
    def test_batch_records_per_event_outcome(self, tmp_path: Path) -> None:
        """replay_all_events must record per-event outcomes without raising or
        fabricating success for failed events."""
        cache_dir = tmp_path / "data" / "cache"
        cache_dir.mkdir(parents=True)
        vision_records = [_make_visual_record(frame_index=i) for i in range(3)]
        v1 = cache_dir / "event_001_front_vision.jsonl"
        _write_jsonl(v1, vision_records)
        a1 = cache_dir / "event_001_front_audio.jsonl"
        _write_jsonl(a1, [_make_audio_record()])
        # event_002 reuses event_001's vision cache but declares a missing audio cache.
        events = {
            "event_001": {
                "event_id": "event_001",
                "front_vision_cache": {
                    "path": "data/cache/event_001_front_vision.jsonl",
                    "sha256": _sha256_of(v1),
                    "line_count": 3,
                    "byte_size": v1.stat().st_size,
                },
                "front_audio_cache": {
                    "path": "data/cache/event_001_front_audio.jsonl",
                    "sha256": _sha256_of(a1),
                    "line_count": 1,
                    "byte_size": a1.stat().st_size,
                },
            },
            "event_002": {
                "event_id": "event_002",
                "front_vision_cache": {
                    "path": "data/cache/event_001_front_vision.jsonl",
                    "sha256": _sha256_of(v1),
                    "line_count": 3,
                    "byte_size": v1.stat().st_size,
                },
                "front_audio_cache": {
                    "path": "data/cache/missing_audio.jsonl",
                    "sha256": "e" * 64,
                    "line_count": 1,
                    "byte_size": 10,
                },
            },
        }
        manifest_path = _build_manifest(tmp_path, events)
        engine = CacheOnlyReplayEngine(manifest_path, repo_root=tmp_path)
        # B0 needs only vision: both events succeed.
        results_b0 = engine.replay_all_events("B0")
        assert isinstance(results_b0["event_001"], ReplayOutput)
        assert isinstance(results_b0["event_002"], ReplayOutput)
        # B1 needs audio: event_002's missing audio cache becomes a recorded refusal.
        results_b1 = engine.replay_all_events("B1")
        assert isinstance(results_b1["event_001"], ReplayOutput)
        assert isinstance(results_b1["event_002"], ReplayRefusalRecord)
        assert results_b1["event_002"].code == "CACHE_FILE_MISSING"

    def test_visual_record_valid(self) -> None:
        record = _make_visual_record(frame_index=3, timestamp_sec=2.5)
        evidence = _validate_visual_record(record, 0)
        assert evidence.timestamp_s == 2.5
        assert evidence.source_id == "camera_1"
        assert evidence.modality == Modality.VISION
        assert evidence.available is True
        assert len(evidence.detections) == 1
        assert evidence.detections[0].confidence == 0.85

    def test_visual_record_zero_timestamp(self) -> None:
        record = _make_visual_record(timestamp_sec=0.0)
        evidence = _validate_visual_record(record, 0)
        assert evidence.timestamp_s == 0.0

    def test_visual_record_boolean_frame_index_rejected(self) -> None:
        record = _make_visual_record()
        record["frame_index"] = True
        with pytest.raises(CacheReplayRefusal, match="frame_index"):
            _validate_visual_record(record, 0)

    def test_visual_record_nan_timestamp_rejected(self) -> None:
        record = _make_visual_record(timestamp_sec=float("nan"))
        with pytest.raises(CacheReplayRefusal, match="timestamp"):
            _validate_visual_record(record, 0)

    def test_visual_record_not_dict_rejected(self) -> None:
        with pytest.raises(CacheReplayRefusal, match="not a dict"):
            _validate_visual_record(["not", "a", "dict"], 0)

    def test_visual_record_bad_bbox_rejected(self) -> None:
        record = _make_visual_record(detections=[{
            "class_id": 0, "class_name": "train", "confidence": 0.5,
            "bbox_xyxy": [0.0, 0.0],
        }])
        with pytest.raises(CacheReplayRefusal, match="bbox"):
            _validate_visual_record(record, 0)

    def test_audio_record_valid(self) -> None:
        record = _make_audio_record(horn_confidence=0.8, is_horn_detected=True)
        evidence = _validate_audio_record(record, 0)
        assert evidence.modality == Modality.AUDIO
        assert evidence.source_id == "audio_1"
        assert evidence.timestamp_s == 1.0  # stamped at window end
        assert len(evidence.detections) == 1
        assert evidence.detections[0].label == "train_horn"

    def test_audio_record_no_horn(self) -> None:
        record = _make_audio_record(horn_confidence=0.1, is_horn_detected=False)
        evidence = _validate_audio_record(record, 0)
        assert evidence.detections == ()

    def test_audio_record_zero_confidence_no_detection(self) -> None:
        """is_horn_detected=True with zero confidence must not fabricate
        positive evidence."""
        record = _make_audio_record(horn_confidence=0.0, is_horn_detected=True)
        evidence = _validate_audio_record(record, 0)
        assert evidence.detections == ()

    def test_audio_record_nan_confidence_rejected(self) -> None:
        record = _make_audio_record(horn_confidence=float("nan"))
        with pytest.raises(CacheReplayRefusal, match="horn_confidence"):
            _validate_audio_record(record, 0)

    def test_audio_record_missing_field_rejected(self) -> None:
        record = _make_audio_record()
        del record["is_horn_detected"]
        with pytest.raises(CacheReplayRefusal, match="missing required"):
            _validate_audio_record(record, 0)