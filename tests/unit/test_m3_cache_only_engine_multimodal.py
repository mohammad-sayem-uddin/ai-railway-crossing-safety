"""Mission 3 unit tests for the full-multimodal cache-only replay extension.

Builds a synthetic cache tree in a temp directory (the descriptive gate is
filesystem-scoped to the real repository, so synthetic trees exercise the
loader/replay paths directly). Covers: back-record validation in the
EvidenceRecord serialization, source stamping, DUAL_* sync fail-closure,
the master-time frame-window fix, and B0 delegation to the frozen engine.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from railway_detection.data.sync import SyncAligner
from railway_detection.evaluation.cache_only_engine import CacheReplayRefusal
from railway_detection.evaluation.cache_only_engine_multimodal import (
    MultimodalCacheOnlyReplayEngine,
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_jsonl(path: Path, rows: list[dict]) -> dict:
    payload = "".join(json.dumps(r) + "\n" for r in rows).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {
        "path": str(path.relative_to(path.parents[2])),
        "sha256": _sha(payload),
        "line_count": len(rows),
        "byte_size": len(payload),
    }


def _front_rows(n: int = 25) -> list[dict]:
    rows = []
    for i in range(n):
        t = round(i * 0.2, 6)
        rows.append(
            {
                "frame_index": i * 6,
                "timestamp_sec": t,
                "camera_id": "camera_front",
                "detections": [
                    {
                        "class_id": 2,
                        "class_name": "side",
                        "confidence": 0.9,
                        "bbox_xyxy": [0.0, 0.0, 10.0, 10.0],
                    }
                ]
                if i in (5, 6)
                else [],
                "metadata": {
                    "frame_index": i * 6,
                    "timestamp_basis": "source_pts",
                    "pts_ticks": int(round(t * 600)),
                    "timebase": [1, 600],
                    "stream_index": 0,
                    "stream_start_pts": 0,
                },
            }
        )
    return rows


def _back_rows(n: int = 31, source_id: str = "camera_2", pts_ok: bool = True) -> list[dict]:
    rows = []
    for i in range(n):
        t = round(i * 0.4, 6)
        pts = int(round(t * 600)) if pts_ok else int(round(t * 600)) + 7
        rows.append(
            {
                "timestamp_s": t,
                "source_id": source_id,
                "modality": "vision",
                "available": True,
                "detections": [
                    {"label": "rear", "confidence": 0.9, "bbox_xyxy": [0.0, 0.0, 10.0, 10.0]}
                ]
                if i == n - 2
                else [],
                "metadata": {
                    "frame_index": i * 12,
                    "timestamp_basis": "source_pts",
                    "pts_ticks": pts,
                    "timebase": [1, 600],
                    "stream_index": 0,
                    "stream_start_pts": 0,
                },
            }
        )
    return rows


def _audio_rows(n: int = 5) -> list[dict]:
    return [
        {
            "window_index": i,
            "start_sec": float(i),
            "end_sec": float(i) + 1.0,
            "horn_confidence": 0.1,
            "is_horn_detected": False,
        }
        for i in range(n)
    ]


def _make_engine(tmp_path: Path, back_rows: list[dict] | None = None) -> MultimodalCacheOnlyReplayEngine:
    cache = tmp_path / "data" / "cache"
    front = _write_jsonl(cache / "front.jsonl", _front_rows())
    back = _write_jsonl(cache / "back.jsonl", _back_rows() if back_rows is None else back_rows)
    audio = _write_jsonl(cache / "audio.jsonl", _audio_rows())
    # _write_jsonl computed repo-relative paths against parents[2]; fix them:
    manifest = {
        "manifest_version": "1.0.0",
        "created_at": "2026-11-08T00:00:00Z",
        "cohort": "m3_unit_synthetic",
        "events": {
            "event_001": {
                "event_id": "event_001",
                "front_vision_cache": front,
                "back_vision_cache": back,
                "front_audio_cache": audio,
            }
        },
    }
    manifest_path = tmp_path / "data" / "manifests" / "test_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return MultimodalCacheOnlyReplayEngine(
        manifest_path=manifest_path,
        repo_root=tmp_path,
        output_base_dir=tmp_path / "results" / "replays",
    )


def _aligner(back_offset: float = 5.0) -> SyncAligner:
    aligner = SyncAligner(tolerance_s=0.5)
    aligner.add_source("camera_1", offset_s=0.0, uncertainty_s=0.05)
    aligner.add_source("camera_2", offset_s=back_offset, uncertainty_s=0.05)
    return aligner


def test_back_records_load_and_stamp_camera2(tmp_path):
    engine = _make_engine(tmp_path)
    records = engine.load_back_visual_records("event_001")
    assert len(records) == 31
    assert all(r.source_id == "camera_2" for r in records)
    assert all(r.metadata["record_format"] == "evidence_record" for r in records)
    rear = [r for r in records if r.detections]
    assert len(rear) == 1 and rear[0].detections[0].label == "rear"
    assert rear[0].timestamp_s == pytest.approx(11.6)


def test_back_vision_replay_produces_frames(tmp_path):
    engine = _make_engine(tmp_path)
    out = engine.execute_replay("event_001", "BACK_VISION")
    assert out.frames_produced > 0
    assert out.evidence_records_loaded == 31
    assert out.provenance["protocol_v2_condition"] == "B1"


def test_dual_vision_refuses_without_aligner(tmp_path):
    engine = _make_engine(tmp_path)
    with pytest.raises(CacheReplayRefusal) as excinfo:
        engine.execute_replay("event_001", "DUAL_VISION")
    assert excinfo.value.code == "SYNC_ALIGNMENT_REQUIRED"


def test_dual_vision_master_time_window_extends_beyond_raw_max(tmp_path):
    engine = _make_engine(tmp_path)
    out = engine.execute_replay("event_001", "DUAL_VISION", sync_aligner=_aligner(5.0))
    # Back master span reaches 12.0 + 5.0 = 17.0 s; at 0.2 s stride the frame
    # count must exceed what the raw-timestamp window (max 12.0 s) would give.
    assert out.frames_produced >= 80
    assert out.evidence_records_loaded == 25 + 31


def test_dual_vision_audio_runs(tmp_path):
    engine = _make_engine(tmp_path)
    out = engine.execute_replay("event_001", "DUAL_VISION_AUDIO", sync_aligner=_aligner(5.0))
    assert out.frames_produced > 0
    assert out.evidence_records_loaded == 25 + 31 + 5
    assert out.provenance["protocol_v2_condition"] == "B7"


def test_b0_delegates_to_frozen_engine(tmp_path):
    engine = _make_engine(tmp_path)
    out = engine.execute_replay("event_001", "B0")
    assert out.evidence_records_loaded == 25


def test_back_record_wrong_source_rejected(tmp_path):
    engine = _make_engine(tmp_path, back_rows=_back_rows(source_id="camera_9"))
    with pytest.raises(CacheReplayRefusal) as excinfo:
        engine.load_back_visual_records("event_001")
    assert excinfo.value.code == "RECORD_INVALID_SOURCE"


def test_back_record_pts_mismatch_rejected(tmp_path):
    engine = _make_engine(tmp_path, back_rows=_back_rows(pts_ok=False))
    with pytest.raises(CacheReplayRefusal) as excinfo:
        engine.load_back_visual_records("event_001")
    assert excinfo.value.code == "RECORD_INVALID_TIMESTAMP"
