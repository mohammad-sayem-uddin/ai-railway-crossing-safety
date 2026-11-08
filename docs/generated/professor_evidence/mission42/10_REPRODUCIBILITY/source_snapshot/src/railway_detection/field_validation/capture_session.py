"""Capture-session record for Phase 15 passive-observation data collection.

The record documents *what was done* during an authorized, passive recording
session so the data can later be audited and fed to the offline pipeline. The
validator checks structure and internal consistency only. It cannot verify that
a site authority actually granted access or that a safety case is sound: those
are external facts, so ``external_authorization_verified`` is always ``False``
and a structurally valid record is never evidence of permission.

Hard requirements enforced here:

* passive observation only: no actuator connection, no control operated, no
  intervention, no model-derived labels;
* a site-authorization and a safety-case reference, each pinned to a document
  hash and recorded by an allowlisted identity;
* the observer distance is compared with a minimum *taken from the safety case
  record itself*; this module supplies no distance threshold of its own;
* multi-camera sessions must record a clock-offset estimate with its method or
  state explicitly that synchronization is unresolved;
* data files are relative, hash-pinned, and never inside the protected
  ``data/raw`` tree.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from railway_detection.safety.media_guard import require_media_authorization

CAPTURE_SESSION_SCHEMA = "phase15-capture-session/1"
SYNC_METHODS = ("audio_cross_correlation", "manual_visual_event", "gnss", "shared_clock")
DEVICE_KINDS = ("camera", "microphone")
_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class SessionViolation:
    code: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "detail": self.detail}


@dataclass(frozen=True)
class CaptureSessionValidation:
    violations: tuple[SessionViolation, ...]
    # Always False: software cannot confirm external authority or a safety case.
    external_authorization_verified: bool = False
    # These statuses describe only what is present in the submitted record.  A
    # recorded reference is deliberately not treated as proof of permission.
    site_authorization_status: str = "missing"
    safety_case_status: str = "missing"

    @property
    def structurally_valid(self) -> bool:
        return not self.violations

    def codes(self) -> tuple[str, ...]:
        return tuple(sorted({v.code for v in self.violations}))

    def to_dict(self) -> dict[str, Any]:
        return {
            "structurally_valid": self.structurally_valid,
            "external_authorization_verified": self.external_authorization_verified,
            "site_authorization_status": self.site_authorization_status,
            "safety_case_status": self.safety_case_status,
            "violations": [v.to_dict() for v in self.violations],
            "note": (
                "Structure only. This is not evidence that site access or a safety case "
                "was granted, and not permission to start any field activity."
            ),
        }


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else None


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _positive_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0
    )


def validate_capture_session(
    record: Mapping[str, Any],
    *,
    authorized_recorders: frozenset[str],
    now: datetime | None = None,
) -> CaptureSessionValidation:
    """Return every structural violation; an empty list is not permission."""
    now = now or datetime.now(UTC)
    found: list[SessionViolation] = []

    def fail(code: str, detail: str) -> None:
        found.append(SessionViolation(code, detail))

    if not isinstance(record, Mapping):
        return CaptureSessionValidation((SessionViolation("RECORD_INVALID", "not an object"),))
    if record.get("schema_version") != CAPTURE_SESSION_SCHEMA:
        fail("SCHEMA_UNSUPPORTED", f"schema_version must be {CAPTURE_SESSION_SCHEMA!r}")
    if not _nonempty(record.get("session_id")):
        fail("SESSION_ID_MISSING", "session_id is required")
    if record.get("recorded_by") not in authorized_recorders:
        fail("RECORDER_NOT_AUTHORIZED", "recorded_by is not on the authority allowlist")

    # Passive observation only -------------------------------------------------
    if record.get("mode") != "passive_observation":
        fail("NOT_PASSIVE_OBSERVATION", "mode must be 'passive_observation'")
    if record.get("actuator_connections") != []:
        fail("ACTUATOR_CONNECTED", "actuator_connections must be an empty list")
    for flag in ("controls_operated", "intervention_performed", "labels_from_model_predictions"):
        if record.get(flag) is not False:
            fail("PASSIVE_CONSTRAINT_VIOLATED", f"{flag} must be exactly false")
    if record.get("annotation_status") != "UNANNOTATED":
        fail("ANNOTATION_PRESENT", "annotation_status must be 'UNANNOTATED' at capture time")

    # Authorizations (recorded, externally unverifiable) ---------------------------
    site = record.get("site_authorization")
    site_status = "missing"
    if not isinstance(site, Mapping):
        fail("SITE_AUTHORIZATION_MISSING", "site_authorization is required")
    else:
        site_status = "recorded_reference_unverified"
        for key in ("authority_name", "reference_id"):
            if not _nonempty(site.get(key)):
                fail("SITE_AUTHORIZATION_INCOMPLETE", f"site_authorization.{key} is required")
        if not (isinstance(site.get("document_sha256"), str)
                and _SHA256.fullmatch(site["document_sha256"])):
            fail("SITE_AUTHORIZATION_INCOMPLETE", "site_authorization.document_sha256 invalid")
        granted = _utc(site.get("granted_on_utc"))
        if granted is None or granted > now:
            fail("SITE_AUTHORIZATION_INCOMPLETE", "granted_on_utc must be a past UTC time")
        if site.get("scope_covers_session") is not True:
            fail("SITE_AUTHORIZATION_SCOPE", "scope_covers_session must be true")
        if any(v.code.startswith("SITE_AUTHORIZATION") for v in found):
            site_status = "invalid_reference"

    case = record.get("safety_case")
    safety_status = "missing"
    if not isinstance(case, Mapping):
        fail("SAFETY_CASE_MISSING", "safety_case is required")
    else:
        safety_status = "recorded_reference_unverified"
        for key in ("version", "approved_by_authority"):
            if not _nonempty(case.get(key)):
                fail("SAFETY_CASE_INCOMPLETE", f"safety_case.{key} is required")
        if not (isinstance(case.get("document_sha256"), str)
                and _SHA256.fullmatch(case["document_sha256"])):
            fail("SAFETY_CASE_INCOMPLETE", "safety_case.document_sha256 invalid")
        approved = _utc(case.get("approved_on_utc"))
        if approved is None or approved > now:
            fail("SAFETY_CASE_INCOMPLETE", "approved_on_utc must be a past UTC time")
        minimum = case.get("minimum_observer_distance_from_track_m")
        actual = record.get("observer_distance_from_track_m")
        if not _positive_number(minimum):
            fail("SAFETY_CASE_INCOMPLETE", "minimum_observer_distance_from_track_m is required")
        if any(v.code.startswith("SAFETY_CASE") for v in found):
            safety_status = "invalid_reference"
        elif not _positive_number(actual):
            fail("OBSERVER_DISTANCE_MISSING", "observer_distance_from_track_m is required")
        elif actual < minimum:
            fail(
                "OBSERVER_TOO_CLOSE",
                f"observer at {actual} m is closer than the safety-case minimum {minimum} m",
            )

    # Time window ---------------------------------------------------------------------
    start, end = _utc(record.get("start_utc")), _utc(record.get("end_utc"))
    if start is None or end is None or end <= start or end > now:
        fail("TIME_WINDOW_INVALID", "start_utc/end_utc must be past UTC times with end > start")

    # Devices and synchronization ---------------------------------------------------------
    devices = record.get("devices")
    cameras = 0
    device_ids: set[str] = set()
    if not isinstance(devices, list) or not devices:
        fail("DEVICES_MISSING", "devices must be a nonempty list")
    else:
        for device in devices:
            if not isinstance(device, Mapping) or not _nonempty(device.get("device_id")):
                fail("DEVICE_INVALID", "each device needs a device_id")
                continue
            if device["device_id"] in device_ids:
                fail("DEVICE_INVALID", f"duplicate device_id {device['device_id']!r}")
            device_ids.add(device["device_id"])
            if device.get("kind") not in DEVICE_KINDS:
                fail("DEVICE_INVALID", f"{device['device_id']}: kind must be one of {DEVICE_KINDS}")
            if not _nonempty(device.get("clock_source")):
                fail("DEVICE_INVALID", f"{device['device_id']}: clock_source is required")
            cameras += device.get("kind") == "camera"
    if cameras >= 2:
        sync = record.get("camera_synchronization")
        if not isinstance(sync, Mapping):
            fail("SYNC_UNDECLARED", "multi-camera sessions must declare camera_synchronization")
        elif sync.get("unresolved") is True:
            if sync.get("offset_s") is not None:
                fail("SYNC_CONTRADICTORY", "unresolved synchronization must not carry an offset")
        else:
            offset = sync.get("offset_s")
            if (
                isinstance(offset, bool)
                or not isinstance(offset, (int, float))
                or not math.isfinite(offset)
            ):
                fail("SYNC_UNDECLARED", "offset_s must be finite (or declare unresolved: true)")
            if sync.get("method") not in SYNC_METHODS:
                fail("SYNC_UNDECLARED", f"method must be one of {SYNC_METHODS}")

    # Stop conditions -------------------------------------------------------------------------
    stops = record.get("stop_conditions_observed")
    if not isinstance(stops, list):
        fail("STOP_CONDITIONS_MISSING", "stop_conditions_observed must be a list (may be empty)")
    elif stops and record.get("terminated_early") is not True:
        fail("STOP_CONDITION_IGNORED", "stop condition observed but terminated_early is not true")

    # Data files ---------------------------------------------------------------------------------
    files = record.get("data_files")
    if not isinstance(files, list) or not files:
        fail("DATA_FILES_MISSING", "data_files must be a nonempty list")
    else:
        seen: set[str] = set()
        for entry in files:
            path = entry.get("path") if isinstance(entry, Mapping) else None
            if not _nonempty(path):
                fail("DATA_FILE_INVALID", "each data file needs a path")
                continue
            pure = PurePosixPath(path)
            if pure.is_absolute() or ".." in pure.parts:
                fail("DATA_FILE_PATH_UNSAFE", f"{path}: must be relative with no '..'")
            if pure.parts[:2] == ("data", "raw"):
                fail("DATA_FILE_PROTECTED_TREE", f"{path}: must not be inside protected data/raw")
            if path in seen:
                fail("DATA_FILE_INVALID", f"duplicate path {path}")
            seen.add(path)
            digest = entry.get("sha256")
            if not (isinstance(digest, str) and _SHA256.fullmatch(digest)):
                fail("DATA_FILE_INVALID", f"{path}: sha256 invalid")
            if entry.get("device_id") not in device_ids:
                fail("DATA_FILE_INVALID", f"{path}: device_id is not a declared device")
    return CaptureSessionValidation(
        tuple(found),
        site_authorization_status=site_status,
        safety_case_status=safety_status,
    )


def describe_capture_files(
    session_dir: Path | str, device_by_relative_path: Mapping[str, str]
) -> list[dict[str, Any]]:
    """Hash captured files (recorded media) into ``data_files`` entries.

    Paths are relative to ``session_dir``. Symlinks are refused so a recorded hash
    always names the bytes of a real captured file.
    """
    base = Path(session_dir).resolve()
    entries: list[dict[str, Any]] = []
    for relative, device_id in sorted(device_by_relative_path.items()):
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts:
            raise ValueError(f"unsafe relative path {relative!r}")
        path = base / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"{relative}: must be a regular, non-symlink file")
        require_media_authorization(path, "HASH_RAW_MEDIA")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        entries.append(
            {
                "path": relative,
                "sha256": digest.hexdigest(),
                "device_id": device_id,
                "bytes": path.stat().st_size,
            }
        )
    return entries

