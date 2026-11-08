"""Phase 15 capture-session v2: accounting, custody, drift, fail-closed checklist (synthetic)."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from railway_detection.field_validation import (
    CAPTURE_SESSION_V2_SCHEMA,
    json_schema,
    validate_capture_session_v2,
    verify_session_files,
)
from railway_detection.field_validation.capture_session_v2 import (
    SAFETY_CASE_REQUIRED,
    TOP_LEVEL_REQUIRED,
)

NOW = datetime(2026, 12, 1, tzinfo=UTC)
RECORDERS = frozenset({"researcher@example.org"})
SHA = "a" * 64
REPO_ROOT = Path(__file__).resolve().parents[2]


def _device(device_id: str, role: str, **extra) -> dict:
    base = {
        "device_id": device_id,
        "kind": "camera",
        "role": role,
        "make": "SyntheticCam",
        "model": "X1",
        "firmware_or_os": "1.0",
        "clock_source": "device",
        "nominal_fps": 30.0,
        "resolution": [1920, 1080],
        "recorded_duration_s": 1790.0,
        "accounting_tolerance_s": 0.05,
        "gaps": [{"start_s": 600.0, "end_s": 610.0}],
        "frame_count": 53700,
        "dropped_frames": 12,
        "clock_checks": [
            {"at_s": 0.0, "offset_to_reference_s": 0.000},
            {"at_s": 1800.0, "offset_to_reference_s": 0.010},
        ],
    }
    base.update(extra)
    return base


def _file(path: str, device: str, content: bytes = b"data") -> dict:
    digest = hashlib.sha256(content).hexdigest()
    return {
        "path": path,
        "sha256": digest,
        "bytes": len(content),
        "device_id": device,
        "custody": [
            {
                "at_utc": "2026-11-20T09:30:00Z",
                "actor": "researcher@example.org",
                "action": "captured",
                "sha256_after": digest,
            },
            {
                "at_utc": "2026-11-20T12:00:00Z",
                "actor": "researcher@example.org",
                "action": "verified",
                "sha256_after": digest,
            },
        ],
    }


def _record() -> dict:
    return {
        "schema_version": CAPTURE_SESSION_V2_SCHEMA,
        "identity": {
            "session_id": "synthetic-v2-1",
            "recorded_by": "researcher@example.org",
            "created_utc": "2026-11-20T08:00:00Z",
        },
        "mode": "passive_observation",
        "actuator_connections": [],
        "controls_operated": False,
        "intervention_performed": False,
        "labels_from_model_predictions": False,
        "annotation_status": "UNANNOTATED",
        "software": {
            "package_version": "0.1.0",
            "code_revision": "c" * 40,
            "python_version": "3.11.15",
        },
        "site_authorization": {
            "authority_name": "Synthetic Authority",
            "reference_id": "SYN-1",
            "document_sha256": SHA,
            "granted_on_utc": "2026-11-01T00:00:00Z",
            "scope_covers_session": True,
        },
        "safety_case": {
            "version": "0.1",
            "approved_by_authority": "Synthetic Authority",
            "approved_on_utc": "2026-11-02T00:00:00Z",
            "document_sha256": SHA,
            "minimum_observer_distance_from_track_m": 10.0,
            "maximum_clock_drift_s_per_hour": 0.1,
            "stop_conditions": ["site access revoked", "operator request"],
            "stop_procedure_reference": "SYN-STOP-1",
        },
        "observer_distance_from_track_m": 12.0,
        "environment": {"weather": "clear", "light": "daylight", "visibility_m": 800.0},
        "observation": {"start_utc": "2026-11-20T09:00:00Z", "end_utc": "2026-11-20T09:30:00Z"},
        "devices": [_device("cam_front", "front"), _device("cam_back", "back")],
        "camera_synchronization": {"unresolved": True, "offset_s": None},
        "stop_conditions_observed": [],
        "terminated_early": False,
        "data_files": [_file("s/cam_front.mov", "cam_front"), _file("s/cam_back.mov", "cam_back")],
    }


def _report(record: dict):
    return validate_capture_session_v2(record, authorized_recorders=RECORDERS, now=NOW)


def _codes(record: dict) -> tuple[str, ...]:
    return _report(record).codes()


def test_complete_record_is_structurally_valid_but_never_externally_verified():
    report = _report(_record())
    assert report.structurally_valid, report.failures()
    out = report.to_dict()
    assert out["overall"] == "STRUCTURALLY_VALID_NOT_PERMISSION"
    assert out["external_authorization_verified"] is False
    assert out["site_authorization_status"] == "recorded_reference_unverified"
    assert "not permission" in out["note"].lower() or "not evidence" in out["note"].lower()


def test_accounting_is_reported_per_device_without_inventing_thresholds():
    acct = _report(_record()).accounting
    assert acct["expected_duration_s"] == 1800.0
    cam = acct["devices"]["cam_front"]
    assert cam["gap_total_s"] == 10.0 and cam["gap_count"] == 1
    assert cam["coverage_fraction"] == pytest.approx(1790 / 1800)
    assert cam["dropped_fraction"] == pytest.approx(12 / (12 + 53700))
    assert cam["clock_drift_s_per_hour"] == pytest.approx(0.010 / 1800 * 3600)  # 0.02 s/h


MUTATIONS = [
    # -- missing metadata
    ("drop environment", lambda r: r.pop("environment"), "REQUIRED_SECTIONS_PRESENT"),
    ("drop software", lambda r: r.pop("software"), "REQUIRED_SECTIONS_PRESENT"),
    ("drop safety_case", lambda r: r.pop("safety_case"), "REQUIRED_SECTIONS_PRESENT"),
    ("no code revision", lambda r: r["software"].pop("code_revision"), "SOFTWARE_PROVENANCE"),
    ("weather omitted", lambda r: r["environment"].pop("weather"), "ENVIRONMENT_RECORDED"),
    ("weather invalid", lambda r: r["environment"].update(weather="sunny"), "ENVIRONMENT_RECORDED"),
    (
        "visibility null without reason",
        lambda r: r["environment"].update(visibility_m=None),
        "ENVIRONMENT_RECORDED",
    ),
    (
        "hardware omitted",
        lambda r: r["devices"][0].pop("firmware_or_os"),
        "DEVICE_HARDWARE_RECORDED",
    ),
    (
        "camera format omitted",
        lambda r: r["devices"][0].pop("resolution"),
        "CAMERA_FORMAT_RECORDED",
    ),
    # -- fail-closed safety checklist: limits must come from the safety case
    *[
        (
            f"safety case lacks {key}",
            lambda r, key=key: r["safety_case"].pop(key),
            "SAFETY_CASE_FIELDS_PRESENT",
        )
        for key in SAFETY_CASE_REQUIRED
    ],
    (
        "no stop conditions",
        lambda r: r["safety_case"].update(stop_conditions=[]),
        "STOP_CONDITIONS_DEFINED",
    ),
    (
        "no stop procedure",
        lambda r: r["safety_case"].update(stop_procedure_reference=" "),
        "STOP_CONDITIONS_DEFINED",
    ),
    (
        "observer too close",
        lambda r: r.update(observer_distance_from_track_m=3.0),
        "OBSERVER_DISTANCE",
    ),
    (
        "unauthorized recorder",
        lambda r: r["identity"].update(recorded_by="x@y.z"),
        "RECORDER_AUTHORIZED",
    ),
    (
        "site scope false",
        lambda r: r["site_authorization"].update(scope_covers_session=False),
        "SITE_AUTHORIZATION_REFERENCE",
    ),
    (
        "stop observed but ignored",
        lambda r: r.update(stop_conditions_observed=["operator request"]),
        "STOP_CONDITIONS_HONORED",
    ),
    # -- passive constraints
    (
        "actuator connected",
        lambda r: r.update(actuator_connections=["gate"]),
        "NO_ACTUATOR_CONNECTION",
    ),
    (
        "model labels",
        lambda r: r.update(labels_from_model_predictions=True),
        "NO_MODEL_DERIVED_LABELS",
    ),
    ("annotated", lambda r: r.update(annotation_status="APPROVED"), "UNANNOTATED_AT_CAPTURE"),
    # -- invalid durations / accounting / gaps
    (
        "end before start",
        lambda r: r["observation"].update(end_utc="2026-11-20T08:00:00Z"),
        "OBSERVATION_WINDOW",
    ),
    (
        "future end",
        lambda r: r["observation"].update(end_utc="2999-01-01T00:00:00Z"),
        "OBSERVATION_WINDOW",
    ),
    (
        "negative duration",
        lambda r: r["devices"][0].update(recorded_duration_s=-5.0),
        "DURATIONS_VALID",
    ),
    (
        "nan duration",
        lambda r: r["devices"][0].update(recorded_duration_s=float("nan")),
        "DURATIONS_VALID",
    ),
    (
        "exposure does not add up",
        lambda r: r["devices"][0].update(recorded_duration_s=1500.0),
        "EXPOSURE_ACCOUNTING_CONSISTENT",
    ),
    (
        "gap outside window",
        lambda r: r["devices"][0].update(gaps=[{"start_s": 1790.0, "end_s": 1900.0}]),
        "GAPS_WELL_FORMED",
    ),
    (
        "overlapping gaps",
        lambda r: r["devices"][0].update(
            gaps=[{"start_s": 100.0, "end_s": 200.0}, {"start_s": 150.0, "end_s": 160.0}]
        ),
        "GAPS_WELL_FORMED",
    ),
    (
        "inverted gap",
        lambda r: r["devices"][0].update(gaps=[{"start_s": 50.0, "end_s": 40.0}]),
        "GAPS_WELL_FORMED",
    ),
    (
        "more frames than possible",
        lambda r: r["devices"][0].update(frame_count=10**7),
        "FRAME_COUNT_PLAUSIBLE",
    ),
    (
        "negative dropped frames",
        lambda r: r["devices"][0].update(dropped_frames=-1),
        "FRAME_COUNTS_RECORDED",
    ),
    # -- clock drift
    (
        "drift above the safety-case limit",
        lambda r: r["devices"][0].update(
            clock_checks=[
                {"at_s": 0.0, "offset_to_reference_s": 0.0},
                {"at_s": 3600.0, "offset_to_reference_s": 5.0},
            ]
        ),
        "CLOCK_DRIFT_WITHIN_SAFETY_CASE_LIMIT",
    ),
    (
        "single clock check cannot establish drift",
        lambda r: r["devices"][0].update(
            clock_checks=[{"at_s": 0.0, "offset_to_reference_s": 0.0}]
        ),
        "CLOCK_DRIFT_WITHIN_SAFETY_CASE_LIMIT",
    ),
    (
        "clock checks malformed",
        lambda r: r["devices"][1].update(clock_checks=[{"at_s": 1}]),
        "CLOCK_DRIFT_WITHIN_SAFETY_CASE_LIMIT",
    ),
    # -- unsupported camera configurations
    (
        "three cameras",
        lambda r: r["devices"].append(_device("cam_x", "front")),
        "CAMERA_CONFIGURATION_SUPPORTED",
    ),
    (
        "duplicate role",
        lambda r: r["devices"][1].update(role="front"),
        "CAMERA_CONFIGURATION_SUPPORTED",
    ),
    (
        "unknown role",
        lambda r: r["devices"][1].update(role="overhead"),
        "CAMERA_CONFIGURATION_SUPPORTED",
    ),
    (
        "duplicate device id",
        lambda r: r["devices"][1].update(device_id="cam_front"),
        "DEVICE_UNIQUE",
    ),
    (
        "unknown device kind",
        lambda r: r["devices"][0].update(kind="lidar"),
        "DEVICE_KIND_SUPPORTED",
    ),
    (
        "two cameras without sync declaration",
        lambda r: r.pop("camera_synchronization"),
        "SYNCHRONIZATION_DECLARED",
    ),
    (
        "unresolved sync carrying an offset",
        lambda r: r.update(camera_synchronization={"unresolved": True, "offset_s": 0.0}),
        "SYNCHRONIZATION_DECLARED",
    ),
    # -- chain of custody / hashes
    ("bad hash format", lambda r: r["data_files"][0].update(sha256="xyz"), "DATA_FILE_HASH_FORMAT"),
    (
        "custody hash differs from file hash",
        lambda r: r["data_files"][0]["custody"][1].update(sha256_after="b" * 64),
        "CHAIN_OF_CUSTODY_INTACT",
    ),
    (
        "custody must begin with capture",
        lambda r: r["data_files"][0]["custody"][0].update(action="copied"),
        "CHAIN_OF_CUSTODY_INTACT",
    ),
    (
        "custody out of order",
        lambda r: r["data_files"][0]["custody"].reverse(),
        "CHAIN_OF_CUSTODY_INTACT",
    ),
    ("custody empty", lambda r: r["data_files"][0].update(custody=[]), "CHAIN_OF_CUSTODY_INTACT"),
    (
        "custody without actor",
        lambda r: r["data_files"][0]["custody"][0].update(actor=""),
        "CHAIN_OF_CUSTODY_INTACT",
    ),
    (
        "unsafe path",
        lambda r: r["data_files"][0].update(path="../escape.mov"),
        "DATA_FILE_PATH_SAFE",
    ),
    (
        "protected tree",
        lambda r: r["data_files"][0].update(path="data/raw/x.mov"),
        "DATA_FILE_PATH_SAFE",
    ),
    (
        "undeclared device",
        lambda r: r["data_files"][0].update(device_id="ghost"),
        "DATA_FILE_DEVICE_DECLARED",
    ),
]


@pytest.mark.parametrize(("label", "mutate", "code"), MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_each_defect_is_caught_by_its_check(label, mutate, code):
    record = _record()
    mutate(record)
    assert code in _codes(record), (label, _codes(record))


def test_single_camera_sessions_need_neither_sync_nor_drift_evidence():
    record = _record()
    record["devices"] = [_device("cam_front", "front", clock_checks=[])]
    record.pop("camera_synchronization")
    record["data_files"] = [_file("s/cam_front.mov", "cam_front")]
    assert _report(record).structurally_valid


def test_microphones_are_inventoried_without_a_camera_role():
    record = _record()
    record["devices"].append(
        {
            "device_id": "mic_1",
            "kind": "microphone",
            "make": "SyntheticMic",
            "model": "M",
            "firmware_or_os": "1",
            "clock_source": "device",
            "recorded_duration_s": 1800.0,
            "accounting_tolerance_s": 0.5,
            "gaps": [],
        }
    )
    record["data_files"].append(_file("s/mic.wav", "mic_1"))
    assert _report(record).structurally_valid


def test_the_validator_never_mutates_its_input_and_empty_input_fails_closed():
    record = _record()
    snapshot = copy.deepcopy(record)
    _report(record)
    assert record == snapshot
    assert not _report({}).structurally_valid
    assert not validate_capture_session_v2(
        None,
        authorized_recorders=RECORDERS,
        now=NOW,  # type: ignore[arg-type]
    ).structurally_valid


def test_every_mandatory_check_failure_blocks_the_overall_result():
    record = _record()
    record["safety_case"].pop("maximum_clock_drift_s_per_hour")
    out = _report(record).to_dict()
    assert out["overall"] == "INVALID" and out["failed_check_ids"]


def test_validation_report_exposes_missing_authorization_and_safety_case_states():
    record = _record()
    record.pop("site_authorization")
    record.pop("safety_case")
    out = _report(record).to_dict()
    assert out["site_authorization_status"] == "missing"
    assert out["safety_case_status"] == "missing"


# ------------------------------------------------------------------------ disk verification


def test_recorded_hashes_are_rechecked_against_the_files(tmp_path: Path):
    (tmp_path / "s").mkdir()
    (tmp_path / "s/cam_front.mov").write_bytes(b"data")
    (tmp_path / "s/cam_back.mov").write_bytes(b"data")
    record = _record()
    assert verify_session_files(tmp_path, record)["verified"] is True

    (tmp_path / "s/cam_back.mov").write_bytes(b"corrupted!")
    out = verify_session_files(tmp_path, record)
    assert out["verified"] is False
    assert {f["path"]: f["status"] for f in out["files"]}["s/cam_back.mov"] == "HASH_MISMATCH"

    (tmp_path / "s/cam_front.mov").unlink()
    statuses = {f["path"]: f["status"] for f in verify_session_files(tmp_path, record)["files"]}
    assert statuses["s/cam_front.mov"] == "MISSING"


def test_size_mismatch_and_symlinks_and_unsafe_paths_are_not_verified(tmp_path: Path):
    (tmp_path / "s").mkdir()
    real = tmp_path / "real.bin"
    real.write_bytes(b"data")
    (tmp_path / "s/cam_front.mov").symlink_to(real)
    (tmp_path / "s/cam_back.mov").write_bytes(b"data")
    record = _record()
    record["data_files"][1]["bytes"] = 999
    record["data_files"].append({**_file("../x", "cam_front")})
    out = {f["path"]: f["status"] for f in verify_session_files(tmp_path, record)["files"]}
    assert out["s/cam_front.mov"] == "MISSING"  # symlinks are not accepted as captured files
    assert out["s/cam_back.mov"] == "SIZE_MISMATCH"
    assert out["../x"] == "UNSAFE_PATH"
    assert verify_session_files(tmp_path, {"data_files": []})["verified"] is False


# ---------------------------------------------------------------------------- the schema


def test_published_schema_matches_the_code_and_the_validator_requirements():
    schema = json_schema()
    published = json.loads(
        (REPO_ROOT / "docs/schemas/phase15-capture-session-2.schema.json").read_text()
    )
    assert published == json.loads(json.dumps(schema)), "regenerate docs/schemas/*.schema.json"
    assert tuple(schema["required"]) == TOP_LEVEL_REQUIRED
    assert tuple(schema["properties"]["safety_case"]["required"]) == SAFETY_CASE_REQUIRED
    # every required section is actually enforced by the validator
    for section in TOP_LEVEL_REQUIRED:
        record = _record()
        record.pop(section)
        assert "REQUIRED_SECTIONS_PRESENT" in _codes(record), section
    assert schema["properties"]["environment"]["properties"]["weather"]["enum"][-1] == "unknown"


def test_software_provenance_is_captured_not_typed_and_empty_revision_fails_closed(tmp_path):
    from railway_detection.field_validation import collect_software_provenance

    captured = collect_software_provenance(REPO_ROOT)
    assert len(captured["code_revision"]) == 40 and captured["python_version"].startswith("3.")
    record = _record()
    record["software"] = captured
    assert "SOFTWARE_PROVENANCE" not in _codes(record)
    outside = collect_software_provenance(tmp_path)  # not a git checkout
    assert outside["code_revision"] == ""
    record["software"] = outside
    assert "SOFTWARE_PROVENANCE" in _codes(record)
