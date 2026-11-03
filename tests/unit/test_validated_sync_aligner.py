"""Regression tests for manifest-backed, event-scoped, fail-closed SyncAligner
construction (R04 Problem E).

Uses small synthetic manifests and synthetic media files written to tmp_path
-- never the real Layer B dataset -- so these tests do not depend on, and
cannot mutate, any real evidence.
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


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_media(path: Path, content: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return _sha256_bytes(content)


def _base_manifest(root: Path, status: str = "CANDIDATE_UNVALIDATED_DO_NOT_MERGE") -> dict:
    front_path = root / "data/raw/layer_b/v2/train_events/event_001/camera_front.mov"
    back_path = root / "data/raw/layer_b/v2/train_events/event_001/camera_back.mov"
    front_sha = _write_media(front_path, b"front-media-bytes")
    back_sha = _write_media(back_path, b"back-media-bytes")
    return {
        "status": status,
        "manifest_version": "test_v1",
        "events": {
            "train_events/event_001": {
                "calibration_verdict": "CALIBRATION_SUPPORTED",
                "camera_front": {
                    "relative_path": "data/raw/layer_b/v2/train_events/event_001/camera_front.mov",
                    "sha256": front_sha,
                    "offset_s": 0.0,
                },
                "camera_back": {
                    "relative_path": "data/raw/layer_b/v2/train_events/event_001/camera_back.mov",
                    "sha256": back_sha,
                    "offset_s": 7.406,
                    "uncertainty_s": 0.05,
                },
            }
        },
    }


def _write_manifest(path: Path, manifest: dict) -> None:
    path.write_text(yaml.dump(manifest), encoding="utf-8")


def test_accepts_supported_event_with_matching_hashes(tmp_path: Path) -> None:
    manifest = _base_manifest(tmp_path, status="ACCEPTED")
    manifest_path = tmp_path / "manifest.yaml"
    _write_manifest(manifest_path, manifest)

    result = load_validated_sync_aligner(manifest_path, "train_events/event_001", repo_root=tmp_path)

    assert result.verdict == "CALIBRATION_SUPPORTED"
    assert result.aligner.to_master("camera_2", 10.0) == pytest.approx(17.406)
    assert result.aligner.to_master("camera_1", 10.0) == pytest.approx(10.0)


def test_candidate_status_refuses_by_default(tmp_path: Path) -> None:
    manifest = _base_manifest(tmp_path, status="CANDIDATE_UNVALIDATED_DO_NOT_MERGE")
    manifest_path = tmp_path / "manifest.yaml"
    _write_manifest(manifest_path, manifest)

    with pytest.raises(CalibrationNotAcceptedError, match="Candidate calibration"):
        load_validated_sync_aligner(manifest_path, "train_events/event_001", repo_root=tmp_path)


def test_candidate_status_can_be_explicitly_allowed_for_exploratory_use(tmp_path: Path) -> None:
    manifest = _base_manifest(tmp_path, status="CANDIDATE_UNVALIDATED_DO_NOT_MERGE")
    manifest_path = tmp_path / "manifest.yaml"
    _write_manifest(manifest_path, manifest)

    result = load_validated_sync_aligner(
        manifest_path, "train_events/event_001", repo_root=tmp_path, allow_candidate_status=True
    )
    assert result.verdict == "CALIBRATION_SUPPORTED"


@pytest.mark.parametrize("bad_verdict", ["PROVISIONAL", "AMBIGUOUS", "FAILED", "NOT_ASSESSABLE"])
def test_unsupported_verdicts_fail_closed(tmp_path: Path, bad_verdict: str) -> None:
    manifest = _base_manifest(tmp_path, status="ACCEPTED")
    manifest["events"]["train_events/event_001"]["calibration_verdict"] = bad_verdict
    manifest_path = tmp_path / "manifest.yaml"
    _write_manifest(manifest_path, manifest)

    with pytest.raises(CalibrationNotAcceptedError, match="not CALIBRATION_SUPPORTED"):
        load_validated_sync_aligner(manifest_path, "train_events/event_001", repo_root=tmp_path)


def test_missing_event_fails_closed_not_zero_offset(tmp_path: Path) -> None:
    manifest = _base_manifest(tmp_path, status="ACCEPTED")
    manifest_path = tmp_path / "manifest.yaml"
    _write_manifest(manifest_path, manifest)

    with pytest.raises(CalibrationNotAcceptedError, match="No calibration entry"):
        load_validated_sync_aligner(manifest_path, "train_events/event_999", repo_root=tmp_path)


@pytest.mark.parametrize(
    ("camera", "field"),
    [("camera_front", "offset_s"), ("camera_back", "offset_s"), ("camera_back", "uncertainty_s")],
)
def test_missing_clock_metadata_fails_closed_not_zero_default(
    tmp_path: Path, camera: str, field: str
) -> None:
    manifest = _base_manifest(tmp_path, status="ACCEPTED")
    del manifest["events"]["train_events/event_001"][camera][field]
    manifest_path = tmp_path / "manifest.yaml"
    _write_manifest(manifest_path, manifest)

    with pytest.raises(CalibrationNotAcceptedError, match="requires a finite"):
        load_validated_sync_aligner(manifest_path, "train_events/event_001", repo_root=tmp_path)


@pytest.mark.parametrize(
    ("camera", "field", "value", "message"),
    [
        ("camera_front", "offset_s", "0.0", "requires a finite offset_s"),
        ("camera_back", "offset_s", float("inf"), "requires a finite offset_s"),
        ("camera_back", "uncertainty_s", "0.05", "requires a finite uncertainty_s"),
        ("camera_back", "uncertainty_s", float("nan"), "requires a finite uncertainty_s"),
        ("camera_back", "uncertainty_s", -0.01, "must be non-negative"),
    ],
)
def test_invalid_clock_values_fail_closed(
    tmp_path: Path, camera: str, field: str, value: object, message: str
) -> None:
    manifest = _base_manifest(tmp_path, status="ACCEPTED")
    manifest["events"]["train_events/event_001"][camera][field] = value
    manifest_path = tmp_path / "manifest.yaml"
    _write_manifest(manifest_path, manifest)

    with pytest.raises(CalibrationNotAcceptedError, match=message):
        load_validated_sync_aligner(manifest_path, "train_events/event_001", repo_root=tmp_path)


def test_hash_mismatch_detects_stale_media(tmp_path: Path) -> None:
    manifest = _base_manifest(tmp_path, status="ACCEPTED")
    manifest_path = tmp_path / "manifest.yaml"
    _write_manifest(manifest_path, manifest)

    # Overwrite the back-camera media AFTER the manifest was written, so its
    # hash no longer matches what the manifest recorded.
    back_path = tmp_path / "data/raw/layer_b/v2/train_events/event_001/camera_back.mov"
    back_path.write_bytes(b"tampered-or-re-recorded-content")

    with pytest.raises(CalibrationNotAcceptedError, match="SHA-256 mismatch"):
        load_validated_sync_aligner(manifest_path, "train_events/event_001", repo_root=tmp_path)


def test_missing_source_media_file_fails_closed(tmp_path: Path) -> None:
    manifest = _base_manifest(tmp_path, status="ACCEPTED")
    manifest_path = tmp_path / "manifest.yaml"
    _write_manifest(manifest_path, manifest)

    back_path = tmp_path / "data/raw/layer_b/v2/train_events/event_001/camera_back.mov"
    back_path.unlink()

    with pytest.raises(CalibrationNotAcceptedError, match="missing on disk"):
        load_validated_sync_aligner(manifest_path, "train_events/event_001", repo_root=tmp_path)


def test_two_events_produce_isolated_non_shared_aligners(tmp_path: Path) -> None:
    """Event isolation (Problem E.5): calibrating two different events must
    never let one event's offset leak into another's aligner."""
    manifest = _base_manifest(tmp_path, status="ACCEPTED")
    # Add a second event with a very different offset.
    front2 = tmp_path / "data/raw/layer_b/v2/train_events/event_002/camera_front.mov"
    back2 = tmp_path / "data/raw/layer_b/v2/train_events/event_002/camera_back.mov"
    front2_sha = _write_media(front2, b"front-2")
    back2_sha = _write_media(back2, b"back-2")
    manifest["events"]["train_events/event_002"] = {
        "calibration_verdict": "CALIBRATION_SUPPORTED",
        "camera_front": {
            "relative_path": "data/raw/layer_b/v2/train_events/event_002/camera_front.mov",
            "sha256": front2_sha,
            "offset_s": 0.0,
        },
        "camera_back": {
            "relative_path": "data/raw/layer_b/v2/train_events/event_002/camera_back.mov",
            "sha256": back2_sha,
            "offset_s": -1.5,
            "uncertainty_s": 0.05,
        },
    }
    manifest_path = tmp_path / "manifest.yaml"
    _write_manifest(manifest_path, manifest)

    r1 = load_validated_sync_aligner(manifest_path, "train_events/event_001", repo_root=tmp_path)
    r2 = load_validated_sync_aligner(manifest_path, "train_events/event_002", repo_root=tmp_path)

    assert r1.aligner is not r2.aligner
    assert r1.back_offset_s == pytest.approx(7.406)
    assert r2.back_offset_s == pytest.approx(-1.5)
    # r1's aligner must know nothing about event_002's offset.
    assert r1.aligner.offsets_s == {"camera_1": 0.0, "camera_2": 7.406}


def test_invalid_manifest_missing_events_section_fails_closed(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(yaml.dump({"status": "ACCEPTED"}), encoding="utf-8")

    with pytest.raises(CalibrationNotAcceptedError, match="missing a valid 'events' section"):
        load_validated_sync_aligner(manifest_path, "train_events/event_001", repo_root=tmp_path)


@pytest.mark.parametrize(
    ("path_value", "message"),
    [
        ("/outside/camera.mov", "must not be absolute"),
        ("../../outside/camera.mov", "escapes repository root"),
    ],
)
def test_calibration_media_paths_are_confined_to_repository(
    tmp_path: Path, path_value: str, message: str
) -> None:
    manifest = _base_manifest(tmp_path, status="ACCEPTED")
    manifest["events"]["train_events/event_001"]["camera_front"]["relative_path"] = path_value
    manifest_path = tmp_path / "manifest.yaml"
    _write_manifest(manifest_path, manifest)

    with pytest.raises(CalibrationNotAcceptedError, match=message):
        load_validated_sync_aligner(manifest_path, "train_events/event_001", repo_root=tmp_path)


def test_malformed_event_or_camera_entry_fails_closed(tmp_path: Path) -> None:
    manifest = _base_manifest(tmp_path, status="ACCEPTED")
    manifest["events"]["train_events/event_001"] = []
    manifest_path = tmp_path / "manifest.yaml"
    _write_manifest(manifest_path, manifest)
    with pytest.raises(CalibrationNotAcceptedError, match="No calibration entry"):
        load_validated_sync_aligner(manifest_path, "train_events/event_001", repo_root=tmp_path)

    manifest = _base_manifest(tmp_path, status="ACCEPTED")
    manifest["events"]["train_events/event_001"]["camera_back"] = []
    _write_manifest(manifest_path, manifest)
    with pytest.raises(CalibrationNotAcceptedError, match="missing camera_front or camera_back"):
        load_validated_sync_aligner(manifest_path, "train_events/event_001", repo_root=tmp_path)


def test_missing_manifest_file_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_validated_sync_aligner(
            tmp_path / "does_not_exist.yaml", "train_events/event_001", repo_root=tmp_path
        )


def test_manifest_path_outside_repository_is_refused(tmp_path: Path) -> None:
    manifest = _base_manifest(tmp_path, status="ACCEPTED")
    outside = tmp_path.parent / "outside-manifest.yaml"
    _write_manifest(outside, manifest)

    with pytest.raises(CalibrationNotAcceptedError, match="must remain beneath"):
        load_validated_sync_aligner(outside, "train_events/event_001", repo_root=tmp_path)


def test_symlinked_manifest_path_that_escapes_repository_is_refused(tmp_path: Path) -> None:
    manifest = _base_manifest(tmp_path, status="ACCEPTED")
    outside = tmp_path.parent / "outside-symlink-manifest.yaml"
    _write_manifest(outside, manifest)
    alias = tmp_path / "manifest-alias.yaml"
    alias.symlink_to(outside)

    with pytest.raises(CalibrationNotAcceptedError, match="must remain beneath"):
        load_validated_sync_aligner(alias, "train_events/event_001", repo_root=tmp_path)


def test_invalid_yaml_is_a_specific_calibration_refusal(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text("events: [unterminated", encoding="utf-8")

    with pytest.raises(CalibrationNotAcceptedError, match="unreadable or invalid"):
        load_validated_sync_aligner(manifest_path, "train_events/event_001", repo_root=tmp_path)


def test_symlinked_media_path_that_escapes_repository_is_refused(tmp_path: Path) -> None:
    manifest = _base_manifest(tmp_path, status="ACCEPTED")
    outside = tmp_path.parent / "outside-media.mov"
    outside.write_bytes(b"synthetic-outside-media")
    alias = tmp_path / "data/raw/layer_b/v2/train_events/event_001/escaped.mov"
    alias.symlink_to(outside)
    manifest["events"]["train_events/event_001"]["camera_front"]["relative_path"] = (
        "data/raw/layer_b/v2/train_events/event_001/escaped.mov"
    )
    manifest_path = tmp_path / "manifest.yaml"
    _write_manifest(manifest_path, manifest)

    with pytest.raises(CalibrationNotAcceptedError, match="escapes repository root"):
        load_validated_sync_aligner(manifest_path, "train_events/event_001", repo_root=tmp_path)
