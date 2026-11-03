"""Unit tests for Layer B event bundle ingestion and synchronization."""

from __future__ import annotations

import pytest

from railway_detection.data.layer_b import load_event_bundle
from railway_detection.data.sync import SyncAligner
from tests.fixtures.mock_events import (
    make_mock_event_bundle,
    make_mock_event_bundle_incomplete,
)


def test_load_valid_bundle(tmp_path):
    event_dir = make_mock_event_bundle(tmp_path)
    result = load_event_bundle(event_dir)
    assert result.ok, result.issues
    event = result.event
    assert event is not None
    assert event.event_id == "event_001"
    assert event.crossing_id == "mock_crossing"
    assert event.camera_1_path is not None
    assert event.camera_2_path is not None
    assert event.audio_source is not None
    assert event.sync_method == "audiovisual_clap"
    assert event.sync_uncertainty_s == 0.1
    assert event.direction == "approach_to_departure"
    assert event.geometry_reference == "mock-1"
    assert [label.name for label in event.labels] == [
        "crossing_entry",
        "tail_clearance",
    ]


def test_load_incomplete_bundle_flags_issues(tmp_path):
    event_dir = make_mock_event_bundle_incomplete(tmp_path)
    result = load_event_bundle(event_dir)
    assert not result.ok
    assert any("metadata.json" in issue for issue in result.issues)
    assert any("empty" in issue for issue in result.issues)


def test_load_missing_directory():
    result = load_event_bundle("/nonexistent/path")
    assert not result.ok
    assert any("not found" in issue for issue in result.issues)


def test_missing_metadata_serializes_none(tmp_path):
    event_dir = tmp_path / "event_min"
    event_dir.mkdir()
    (event_dir / "camera_1.mp4").write_bytes(b"x")
    (event_dir / "camera_2.mp4").write_bytes(b"x")
    (event_dir / "audio.wav").write_bytes(b"x")
    result = load_event_bundle(event_dir)
    assert not result.ok  # metadata required
    event = result.event
    assert event is not None
    assert event.crossing_id is None
    assert event.weather is None
    assert event.metadata_status == "missing"


def test_sync_aligner_master_clock():
    aligner = SyncAligner()
    aligner.add_source("camera_1", offset_s=2.0, uncertainty_s=0.1)
    aligner.add_source("camera_2", offset_s=-1.5, uncertainty_s=0.7)
    assert aligner.to_master("camera_1", 10.0) == 12.0
    assert aligner.to_master("camera_2", 10.0) == 8.5
    assert aligner.is_aligned("camera_1") is True
    assert aligner.is_aligned("camera_2") is False


def test_sync_aligner_rejects_unknown_and_invalid():
    aligner = SyncAligner()
    with pytest.raises(ValueError):
        aligner.to_master("unknown", 1.0)
    aligner.add_source("camera_1", offset_s=0.0, uncertainty_s=0.0)
    with pytest.raises(ValueError):
        aligner.to_master("camera_1", -1.0)
    with pytest.raises(ValueError):
        aligner.add_source("bad", offset_s=0.0, uncertainty_s=-0.1)
    with pytest.raises(ValueError, match="must both be explicit"):
        aligner.add_source("missing_offset", uncertainty_s=0.0)
    with pytest.raises(ValueError, match="must both be explicit"):
        aligner.add_source("missing_uncertainty", offset_s=0.0)
    with pytest.raises(ValueError, match="finite"):
        aligner.add_source("non_finite", offset_s=float("nan"), uncertainty_s=0.0)


def test_alignment_summary():
    aligner = SyncAligner(tolerance_s=0.5)
    aligner.add_source("camera_1", offset_s=0.0, uncertainty_s=0.2)
    aligner.add_source("audio", offset_s=1.0, uncertainty_s=0.9)
    summary = aligner.alignment_summary()
    assert summary["sources"]["camera_1"]["aligned"] is True
    assert summary["sources"]["audio"]["aligned"] is False


def test_load_bundle_with_camera_front_rear_aliases(tmp_path):
    event_dir = tmp_path / "event_aliases"
    event_dir.mkdir()
    (event_dir / "camera_front.mp4").write_bytes(b"video1")
    (event_dir / "camera_rear.mp4").write_bytes(b"video2")
    (event_dir / "audio.wav").write_bytes(b"audio1")

    result = load_event_bundle(event_dir, strict_metadata=False)
    assert result.ok, result.issues
    assert result.event is not None
    assert result.event.camera_1_path == str(event_dir / "camera_front.mp4")
    assert result.event.camera_2_path == str(event_dir / "camera_rear.mp4")
    assert result.event.audio_source == str(event_dir / "audio.wav")
    assert any("metadata.json missing" in w for w in result.warnings)


def test_load_bundle_strict_metadata_toggle(tmp_path):
    event_dir = tmp_path / "event_min_toggle"
    event_dir.mkdir()
    (event_dir / "camera_1.mp4").write_bytes(b"video1")
    (event_dir / "camera_2.mp4").write_bytes(b"video2")
    (event_dir / "audio.wav").write_bytes(b"audio1")

    # Strict: metadata missing is an issue
    res_strict = load_event_bundle(event_dir, strict_metadata=True)
    assert not res_strict.ok
    assert any("metadata.json" in i for i in res_strict.issues)

    # Non-strict: metadata missing is a warning, ok is True
    res_lenient = load_event_bundle(event_dir, strict_metadata=False)
    assert res_lenient.ok
    assert any("metadata.json" in w for w in res_lenient.warnings)


def test_load_bundle_audio_extraction_fallback(tmp_path, monkeypatch):
    event_dir = tmp_path / "event_extract_audio"
    event_dir.mkdir()
    (event_dir / "camera_front.mp4").write_bytes(b"video1")
    (event_dir / "camera_rear.mp4").write_bytes(b"video2")

    def mock_extract(video_path, output_wav):
        output_wav.write_bytes(b"extracted_wav_data")
        return output_wav

    monkeypatch.setattr(
        "railway_detection.data.layer_b.extract_audio_from_video",
        mock_extract,
    )

    result = load_event_bundle(event_dir, strict_metadata=False, extract_audio=True)
    assert result.ok, result.issues
    assert result.event is not None
    assert result.event.audio_source == str(event_dir / "audio_extracted.wav")
    assert any("audio extracted from" in w for w in result.warnings)

