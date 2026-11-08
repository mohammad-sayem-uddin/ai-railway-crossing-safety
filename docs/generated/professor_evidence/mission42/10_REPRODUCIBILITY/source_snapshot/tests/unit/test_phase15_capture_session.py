"""Phase 15 capture-session record validation (synthetic records; no field activity)."""

from __future__ import annotations

import copy
import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from railway_detection.field_validation import (
    CAPTURE_SESSION_SCHEMA,
    describe_capture_files,
    validate_capture_session,
)

NOW = datetime(2026, 12, 1, tzinfo=UTC)
RECORDERS = frozenset({"researcher@example.org"})
SHA = "a" * 64


def _record() -> dict:
    return {
        "schema_version": CAPTURE_SESSION_SCHEMA,
        "session_id": "synthetic-session-1",
        "recorded_by": "researcher@example.org",
        "mode": "passive_observation",
        "actuator_connections": [],
        "controls_operated": False,
        "intervention_performed": False,
        "labels_from_model_predictions": False,
        "annotation_status": "UNANNOTATED",
        "site_authorization": {
            "authority_name": "Synthetic Test Authority",
            "reference_id": "SYN-1",
            "document_sha256": SHA,
            "granted_on_utc": "2026-11-01T00:00:00Z",
            "scope_covers_session": True,
        },
        "safety_case": {
            "version": "0.1-synthetic",
            "approved_by_authority": "Synthetic Test Authority",
            "approved_on_utc": "2026-11-02T00:00:00Z",
            "document_sha256": SHA,
            "minimum_observer_distance_from_track_m": 10.0,
        },
        "observer_distance_from_track_m": 12.0,
        "start_utc": "2026-11-20T09:00:00Z",
        "end_utc": "2026-11-20T09:30:00Z",
        "devices": [
            {"device_id": "cam_front", "kind": "camera", "clock_source": "device"},
            {"device_id": "cam_back", "kind": "camera", "clock_source": "device"},
        ],
        "camera_synchronization": {"unresolved": True, "offset_s": None},
        "stop_conditions_observed": [],
        "terminated_early": False,
        "data_files": [
            {"path": "session/cam_front.mov", "sha256": SHA, "device_id": "cam_front"},
            {"path": "session/cam_back.mov", "sha256": SHA, "device_id": "cam_back"},
        ],
    }


def _codes(record: dict) -> tuple[str, ...]:
    return validate_capture_session(record, authorized_recorders=RECORDERS, now=NOW).codes()


def test_a_complete_passive_record_is_structurally_valid_but_never_externally_verified():
    result = validate_capture_session(_record(), authorized_recorders=RECORDERS, now=NOW)
    assert result.structurally_valid
    assert result.external_authorization_verified is False
    assert "not evidence" in result.to_dict()["note"]


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda r: r.__setitem__("mode", "active_control"), "NOT_PASSIVE_OBSERVATION"),
        (lambda r: r.__setitem__("actuator_connections", ["gate_1"]), "ACTUATOR_CONNECTED"),
        (lambda r: r.__setitem__("controls_operated", True), "PASSIVE_CONSTRAINT_VIOLATED"),
        (lambda r: r.__setitem__("intervention_performed", True), "PASSIVE_CONSTRAINT_VIOLATED"),
        (
            lambda r: r.__setitem__("labels_from_model_predictions", True),
            "PASSIVE_CONSTRAINT_VIOLATED",
        ),
        (lambda r: r.__setitem__("annotation_status", "APPROVED"), "ANNOTATION_PRESENT"),
        (lambda r: r.pop("site_authorization"), "SITE_AUTHORIZATION_MISSING"),
        (lambda r: r.pop("safety_case"), "SAFETY_CASE_MISSING"),
        (lambda r: r["site_authorization"].__setitem__("scope_covers_session", False),
         "SITE_AUTHORIZATION_SCOPE"),
        (lambda r: r["site_authorization"].__setitem__("document_sha256", "bad"),
         "SITE_AUTHORIZATION_INCOMPLETE"),
        (lambda r: r["safety_case"].__setitem__("approved_on_utc", "2999-01-01T00:00:00Z"),
         "SAFETY_CASE_INCOMPLETE"),
        (lambda r: r.__setitem__("observer_distance_from_track_m", 5.0), "OBSERVER_TOO_CLOSE"),
        (lambda r: r.pop("observer_distance_from_track_m"), "OBSERVER_DISTANCE_MISSING"),
        (lambda r: r["safety_case"].pop("minimum_observer_distance_from_track_m"),
         "SAFETY_CASE_INCOMPLETE"),
        (lambda r: r.__setitem__("recorded_by", "someone@else.org"), "RECORDER_NOT_AUTHORIZED"),
        (lambda r: r.__setitem__("end_utc", "2026-11-20T08:00:00Z"), "TIME_WINDOW_INVALID"),
        (lambda r: r.pop("camera_synchronization"), "SYNC_UNDECLARED"),
        (lambda r: r.__setitem__("camera_synchronization",
                                 {"unresolved": True, "offset_s": 0.0}), "SYNC_CONTRADICTORY"),
        (lambda r: r.__setitem__("camera_synchronization",
                                 {"offset_s": 0.0, "method": "guess"}), "SYNC_UNDECLARED"),
        (lambda r: r.__setitem__("stop_conditions_observed", ["site_access_revoked"]),
         "STOP_CONDITION_IGNORED"),
        (lambda r: r["data_files"][0].__setitem__("path", "/abs/cam.mov"), "DATA_FILE_PATH_UNSAFE"),
        (lambda r: r["data_files"][0].__setitem__("path", "../escape.mov"),
         "DATA_FILE_PATH_UNSAFE"),
        (lambda r: r["data_files"][0].__setitem__("path", "data/raw/vision/x.mov"),
         "DATA_FILE_PROTECTED_TREE"),
        (lambda r: r["data_files"][0].__setitem__("device_id", "ghost"), "DATA_FILE_INVALID"),
        (lambda r: r.__setitem__("data_files", []), "DATA_FILES_MISSING"),
    ],
)
def test_violations_are_reported(mutate, code):
    record = _record()
    mutate(record)
    assert code in _codes(record)


def test_resolved_sync_requires_a_method_and_finite_offset():
    record = _record()
    record["camera_synchronization"] = {"offset_s": 0.31, "method": "audio_cross_correlation"}
    assert _codes(record) == ()


def test_single_camera_sessions_need_no_synchronization_declaration():
    record = _record()
    record["devices"] = [{"device_id": "cam_front", "kind": "camera", "clock_source": "device"}]
    record.pop("camera_synchronization")
    record["data_files"] = record["data_files"][:1]
    assert _codes(record) == ()


def test_honored_stop_condition_is_accepted():
    record = _record()
    record["stop_conditions_observed"] = ["site_access_revoked"]
    record["terminated_early"] = True
    assert _codes(record) == ()


def test_validator_does_not_mutate_its_input():
    record = _record()
    snapshot = copy.deepcopy(record)
    validate_capture_session(record, authorized_recorders=RECORDERS, now=NOW)
    assert record == snapshot


def test_describe_capture_files_hashes_real_files_and_refuses_symlinks(tmp_path: Path):
    (tmp_path / "a.bin").write_bytes(b"abc")
    (tmp_path / "link.bin").symlink_to(tmp_path / "a.bin")
    entries = describe_capture_files(tmp_path, {"a.bin": "cam_front"})
    assert entries == [
        {
            "path": "a.bin",
            "sha256": hashlib.sha256(b"abc").hexdigest(),
            "device_id": "cam_front",
            "bytes": 3,
        }
    ]
    with pytest.raises(ValueError, match="non-symlink"):
        describe_capture_files(tmp_path, {"link.bin": "cam_front"})
    with pytest.raises(ValueError, match="unsafe"):
        describe_capture_files(tmp_path, {"../a.bin": "cam_front"})
