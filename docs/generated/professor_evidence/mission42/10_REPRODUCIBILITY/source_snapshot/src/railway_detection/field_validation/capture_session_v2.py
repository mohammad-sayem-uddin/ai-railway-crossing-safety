"""Phase 15 capture-session record, version 2: accounting, custody and a fail-closed checklist.

Version 1 (``capture_session.py``) validates the passive-observation constraints and the
authorization *references*. Version 2 adds what an audit of a recording session needs:
session identity and software provenance, a camera inventory with declared roles,
environment metadata, observation-period/exposure accounting with recording gaps and
dropped frames, per-device clock-drift checks, and a chain-of-custody for every data
file. The validator returns a structured report of PASS / FAIL / NOT_VERIFIABLE checks.

Principles (each has a test):

* **No invented thresholds.** Every numeric limit used to judge a session -- the minimum
  observer distance, the maximum clock drift, the stop conditions -- must come from the
  record's own ``safety_case`` section. If it is absent the check FAILS closed. This
  module supplies none.
* **No self-verified permission.** Site authorization and safety-case approval are
  *recorded references pinned to document hashes*. The validator cannot confirm that any
  authority granted anything, so ``external_authorization_verified`` is always ``False`` and
  an overall ``STRUCTURALLY_VALID`` result is explicitly not permission to start a session.
* **Unknown is a recorded state, not a default.** Weather, light and visibility may be
  ``unknown`` only if stated; they may not be omitted.
* **Hash claims are re-checkable.** ``verify_session_files`` recomputes every file hash
  from disk; a mismatch is reported as corruption.

Nothing here schedules, authorizes or performs field activity or touches railway equipment.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from railway_detection.safety.media_guard import require_media_authorization

CAPTURE_SESSION_V2_SCHEMA = "phase15-capture-session/2"

WEATHER = ("clear", "overcast", "rain", "fog", "snow", "dust", "other", "unknown")
LIGHT = ("daylight", "dusk_dawn", "night_artificial", "night_dark", "unknown")
CAMERA_ROLES = ("front", "back")
DEVICE_KINDS = ("camera", "microphone")
SYNC_METHODS = ("audio_cross_correlation", "manual_visual_event", "gnss", "shared_clock")
CUSTODY_ACTIONS = ("captured", "copied", "verified", "archived")
_SHA256 = re.compile(r"[0-9a-f]{64}")

TOP_LEVEL_REQUIRED = (
    "schema_version",
    "identity",
    "mode",
    "actuator_connections",
    "controls_operated",
    "intervention_performed",
    "labels_from_model_predictions",
    "annotation_status",
    "software",
    "site_authorization",
    "safety_case",
    "observer_distance_from_track_m",
    "environment",
    "observation",
    "devices",
    "stop_conditions_observed",
    "terminated_early",
    "data_files",
)
SAFETY_CASE_REQUIRED = (
    "version",
    "approved_by_authority",
    "approved_on_utc",
    "document_sha256",
    "minimum_observer_distance_from_track_m",
    "maximum_clock_drift_s_per_hour",
    "stop_conditions",
    "stop_procedure_reference",
)


def json_schema() -> dict[str, Any]:
    """Machine-readable (JSON Schema 2020-12) description of the structural contract."""
    sha = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    utc = {"type": "string", "format": "date-time"}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "phase15-capture-session-2.schema.json",
        "title": "Phase 15 passive-observation capture session (v2)",
        "description": (
            "Structure only. Passing this schema, or the validator, is not evidence that site "
            "access or a safety case was granted and is not permission to begin any session."
        ),
        "type": "object",
        "required": list(TOP_LEVEL_REQUIRED),
        "properties": {
            "schema_version": {"const": CAPTURE_SESSION_V2_SCHEMA},
            "identity": {
                "type": "object",
                "required": ["session_id", "recorded_by", "created_utc"],
                "properties": {
                    "session_id": {"type": "string", "minLength": 1},
                    "recorded_by": {"type": "string", "minLength": 1},
                    "created_utc": utc,
                },
            },
            "mode": {"const": "passive_observation"},
            "actuator_connections": {"type": "array", "maxItems": 0},
            "controls_operated": {"const": False},
            "intervention_performed": {"const": False},
            "labels_from_model_predictions": {"const": False},
            "annotation_status": {"const": "UNANNOTATED"},
            "software": {
                "type": "object",
                "required": ["package_version", "code_revision", "python_version"],
            },
            "site_authorization": {
                "type": "object",
                "required": [
                    "authority_name",
                    "reference_id",
                    "document_sha256",
                    "granted_on_utc",
                    "scope_covers_session",
                ],
                "properties": {"document_sha256": sha, "granted_on_utc": utc},
            },
            "safety_case": {
                "type": "object",
                "required": list(SAFETY_CASE_REQUIRED),
                "properties": {
                    "document_sha256": sha,
                    "minimum_observer_distance_from_track_m": {
                        "type": "number",
                        "exclusiveMinimum": 0,
                    },
                    "maximum_clock_drift_s_per_hour": {"type": "number", "exclusiveMinimum": 0},
                    "stop_conditions": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string", "minLength": 1},
                    },
                },
            },
            "observer_distance_from_track_m": {"type": "number", "exclusiveMinimum": 0},
            "environment": {
                "type": "object",
                "required": ["weather", "light", "visibility_m"],
                "properties": {
                    "weather": {"enum": list(WEATHER)},
                    "light": {"enum": list(LIGHT)},
                    "visibility_m": {"type": ["number", "null"]},
                },
            },
            "observation": {
                "type": "object",
                "required": ["start_utc", "end_utc"],
                "properties": {"start_utc": utc, "end_utc": utc},
            },
            "devices": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": [
                        "device_id",
                        "kind",
                        "make",
                        "model",
                        "firmware_or_os",
                        "clock_source",
                        "recorded_duration_s",
                        "accounting_tolerance_s",
                        "gaps",
                    ],
                    "properties": {
                        "kind": {"enum": list(DEVICE_KINDS)},
                        "role": {"enum": list(CAMERA_ROLES)},
                    },
                },
            },
            "camera_synchronization": {"type": "object"},
            "stop_conditions_observed": {"type": "array", "items": {"type": "string"}},
            "terminated_early": {"type": "boolean"},
            "data_files": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["path", "sha256", "bytes", "device_id", "custody"],
                    "properties": {
                        "sha256": sha,
                        "bytes": {"type": "integer", "minimum": 0},
                        "custody": {"type": "array", "minItems": 1},
                    },
                },
            },
        },
        "additionalProperties": True,
    }


@dataclass(frozen=True)
class Check:
    id: str
    status: str  # PASS | FAIL | NOT_VERIFIABLE
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "status": self.status, "detail": self.detail}


@dataclass
class SessionValidationReport:
    checks: list[Check] = field(default_factory=list)
    accounting: dict[str, Any] = field(default_factory=dict)
    # Always False: software cannot confirm external authority or a safety case.
    external_authorization_verified: bool = False

    @property
    def site_authorization_status(self) -> str:
        """Describe the submitted reference, never external permission."""
        check = next((c for c in self.checks if c.id == "SITE_AUTHORIZATION_REFERENCE"), None)
        if check is None:
            return "missing"
        return "recorded_reference_unverified" if check.status == "PASS" else "invalid_reference"

    @property
    def safety_case_status(self) -> str:
        """Describe the submitted safety-case reference, never its approval."""
        fields = next((c for c in self.checks if c.id == "SAFETY_CASE_FIELDS_PRESENT"), None)
        reference = next((c for c in self.checks if c.id == "SAFETY_CASE_REFERENCE"), None)
        if fields is None or fields.status != "PASS":
            return "missing"
        if reference is None or reference.status != "PASS":
            return "invalid_reference"
        return "recorded_reference_unverified"

    def failures(self) -> list[Check]:
        return [c for c in self.checks if c.status == "FAIL"]

    @property
    def structurally_valid(self) -> bool:
        return not self.failures()

    def codes(self) -> tuple[str, ...]:
        return tuple(sorted({c.id for c in self.failures()}))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "phase15-session-validation/2",
            "overall": "STRUCTURALLY_VALID_NOT_PERMISSION"
            if self.structurally_valid
            else "INVALID",
            "external_authorization_verified": self.external_authorization_verified,
            "site_authorization_status": self.site_authorization_status,
            "safety_case_status": self.safety_case_status,
            "checks": [c.to_dict() for c in self.checks],
            "failed_check_ids": list(self.codes()),
            "accounting": self.accounting,
            "note": (
                "Structure and internal consistency only. Not evidence that site access, "
                "operator permission or a safety case was granted; not permission to begin."
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


def _num(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _pos(value: Any) -> bool:
    return _num(value) and value > 0


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_capture_session_v2(
    record: Mapping[str, Any],
    *,
    authorized_recorders: frozenset[str],
    now: datetime | None = None,
) -> SessionValidationReport:
    now = now or datetime.now(UTC)
    report = SessionValidationReport()

    def check(check_id: str, ok: bool, detail: str, *, unverifiable: bool = False) -> None:
        status = "PASS" if ok else ("NOT_VERIFIABLE" if unverifiable else "FAIL")
        # NOT_VERIFIABLE counts as a failure of a mandatory check: fail closed.
        if status == "NOT_VERIFIABLE":
            status = "FAIL"
        report.checks.append(Check(check_id, status, detail))

    if not isinstance(record, Mapping):
        check("RECORD_INVALID", False, "record is not an object")
        return report
    missing = [key for key in TOP_LEVEL_REQUIRED if key not in record]
    check(
        "REQUIRED_SECTIONS_PRESENT",
        not missing,
        f"missing sections: {missing}" if missing else "all required sections present",
    )
    if missing:
        return report  # nothing else can be judged without the sections
    check(
        "SCHEMA_SUPPORTED",
        record["schema_version"] == CAPTURE_SESSION_V2_SCHEMA,
        f"schema_version must be {CAPTURE_SESSION_V2_SCHEMA!r}",
    )

    # --- identity & software provenance
    ident = record["identity"] if isinstance(record["identity"], Mapping) else {}
    created = _utc(ident.get("created_utc"))
    check(
        "IDENTITY_COMPLETE",
        _text(ident.get("session_id"))
        and _text(ident.get("recorded_by"))
        and created is not None
        and created <= now,
        "identity needs session_id, recorded_by and a past created_utc",
    )
    check(
        "RECORDER_AUTHORIZED",
        ident.get("recorded_by") in authorized_recorders,
        "recorded_by must be on the authority allowlist",
    )
    software = record["software"] if isinstance(record["software"], Mapping) else {}
    check(
        "SOFTWARE_PROVENANCE",
        all(_text(software.get(k)) for k in ("package_version", "code_revision", "python_version")),
        "software needs package_version, code_revision and python_version",
    )

    # --- passive observation only
    check(
        "PASSIVE_MODE", record["mode"] == "passive_observation", "mode must be passive_observation"
    )
    check(
        "NO_ACTUATOR_CONNECTION",
        record["actuator_connections"] == [],
        "actuator_connections must be an empty list",
    )
    check(
        "NO_CONTROL_OR_INTERVENTION",
        record["controls_operated"] is False and record["intervention_performed"] is False,
        "controls_operated and intervention_performed must be exactly false",
    )
    check(
        "NO_MODEL_DERIVED_LABELS",
        record["labels_from_model_predictions"] is False,
        "labels_from_model_predictions must be exactly false",
    )
    check(
        "UNANNOTATED_AT_CAPTURE",
        record["annotation_status"] == "UNANNOTATED",
        "annotation_status must be UNANNOTATED at capture time",
    )

    # --- authorization references (recorded, never verified)
    site = record["site_authorization"] if isinstance(record["site_authorization"], Mapping) else {}
    granted = _utc(site.get("granted_on_utc"))
    check(
        "SITE_AUTHORIZATION_REFERENCE",
        _text(site.get("authority_name"))
        and _text(site.get("reference_id"))
        and isinstance(site.get("document_sha256"), str)
        and bool(_SHA256.fullmatch(site["document_sha256"]))
        and granted is not None
        and granted <= now
        and site.get("scope_covers_session") is True,
        "site_authorization needs authority, reference, document hash, past grant date and "
        "scope_covers_session: true",
    )

    # --- mandatory site-specific safety checklist (all limits come from the safety case)
    case = record["safety_case"] if isinstance(record["safety_case"], Mapping) else {}
    absent = [k for k in SAFETY_CASE_REQUIRED if k not in case]
    check(
        "SAFETY_CASE_FIELDS_PRESENT",
        not absent,
        f"safety_case is missing {absent}; no default is ever supplied by the software",
    )
    approved = _utc(case.get("approved_on_utc"))
    check(
        "SAFETY_CASE_REFERENCE",
        _text(case.get("version"))
        and _text(case.get("approved_by_authority"))
        and approved is not None
        and approved <= now
        and isinstance(case.get("document_sha256"), str)
        and bool(_SHA256.fullmatch(case["document_sha256"])),
        "safety_case needs version, approving authority, past approval date and document hash",
    )
    minimum = case.get("minimum_observer_distance_from_track_m")
    actual = record["observer_distance_from_track_m"]
    check(
        "OBSERVER_DISTANCE",
        _pos(minimum) and _pos(actual) and actual >= minimum,
        "observer distance must be at least the safety-case minimum (both required)",
    )
    stops = case.get("stop_conditions")
    check(
        "STOP_CONDITIONS_DEFINED",
        isinstance(stops, list)
        and bool(stops)
        and all(_text(s) for s in stops)
        and _text(case.get("stop_procedure_reference")),
        "the safety case must define stop conditions and a stop-procedure reference",
    )
    observed = record["stop_conditions_observed"]
    check(
        "STOP_CONDITIONS_HONORED",
        isinstance(observed, list) and (not observed or record["terminated_early"] is True),
        "a stop condition was observed but terminated_early is not true",
    )

    # --- environment (unknown must be stated, never omitted)
    env = record["environment"] if isinstance(record["environment"], Mapping) else {}
    vis = env.get("visibility_m")
    vis_ok = (vis is None and _text(env.get("visibility_unknown_reason"))) or _pos(vis)
    check(
        "ENVIRONMENT_RECORDED",
        env.get("weather") in WEATHER and env.get("light") in LIGHT and bool(vis_ok),
        "weather and light must be listed values (or 'unknown'); visibility_m must be a number "
        "or null with visibility_unknown_reason",
    )

    # --- observation period
    obs = record["observation"] if isinstance(record["observation"], Mapping) else {}
    start, end = _utc(obs.get("start_utc")), _utc(obs.get("end_utc"))
    window_ok = start is not None and end is not None and end > start and end <= now
    check(
        "OBSERVATION_WINDOW", window_ok, "start_utc/end_utc must be past UTC times with end > start"
    )
    expected_s = (end - start).total_seconds() if window_ok else None
    report.accounting["expected_duration_s"] = expected_s

    # --- device inventory, accounting, drift
    devices = record["devices"] if isinstance(record["devices"], list) else []
    ids: set[str] = set()
    cameras: list[Mapping[str, Any]] = []
    dev_report: dict[str, Any] = {}
    check("DEVICES_PRESENT", bool(devices), "devices must be a nonempty list")
    for dev in devices:
        if not isinstance(dev, Mapping) or not _text(dev.get("device_id")):
            check("DEVICE_INVALID", False, "each device needs a device_id")
            continue
        did = dev["device_id"]
        check("DEVICE_UNIQUE", did not in ids, f"duplicate device_id {did!r}")
        ids.add(did)
        kind = dev.get("kind")
        check(
            "DEVICE_KIND_SUPPORTED",
            kind in DEVICE_KINDS,
            f"{did}: kind must be one of {DEVICE_KINDS}",
        )
        check(
            "DEVICE_HARDWARE_RECORDED",
            all(_text(dev.get(k)) for k in ("make", "model", "firmware_or_os", "clock_source")),
            f"{did}: make, model, firmware_or_os and clock_source are required",
        )
        if kind == "camera":
            cameras.append(dev)
            res = dev.get("resolution")
            check(
                "CAMERA_FORMAT_RECORDED",
                _pos(dev.get("nominal_fps"))
                and isinstance(res, list)
                and len(res) == 2
                and all(_pos(x) for x in res),
                f"{did}: nominal_fps and resolution [w, h] are required",
            )
        tol = dev.get("accounting_tolerance_s")
        rec = dev.get("recorded_duration_s")
        gaps = dev.get("gaps")
        gaps_ok = isinstance(gaps, list)
        gap_total = 0.0
        prev_end = 0.0
        if gaps_ok:
            for gap in gaps:
                s0, s1 = (
                    (gap.get("start_s"), gap.get("end_s"))
                    if isinstance(gap, Mapping)
                    else (None, None)
                )
                if not (
                    _num(s0)
                    and _num(s1)
                    and 0 <= s0 < s1
                    and s0 >= prev_end
                    and (expected_s is None or s1 <= expected_s + (tol if _num(tol) else 0))
                ):
                    gaps_ok = False
                    break
                gap_total += s1 - s0
                prev_end = s1
        check(
            "GAPS_WELL_FORMED",
            gaps_ok,
            f"{did}: gaps must be ordered, non-overlapping, inside the window",
        )
        durations_ok = _num(rec) and rec >= 0 and _num(tol) and tol >= 0
        check(
            "DURATIONS_VALID",
            durations_ok,
            f"{did}: recorded_duration_s and accounting_tolerance_s must be finite, non-negative",
        )
        consistent = False
        if durations_ok and gaps_ok and expected_s is not None:
            consistent = abs(rec + gap_total - expected_s) <= tol
        check(
            "EXPOSURE_ACCOUNTING_CONSISTENT",
            consistent,
            f"{did}: recorded_duration_s + gaps must equal the observation window within the "
            "device's declared tolerance",
            unverifiable=expected_s is None,
        )
        frame_count, dropped = dev.get("frame_count"), dev.get("dropped_frames")
        if kind == "camera":
            frames_ok = (
                isinstance(frame_count, int)
                and isinstance(dropped, int)
                and not isinstance(frame_count, bool)
                and frame_count >= 0
                and dropped >= 0
            )
            check(
                "FRAME_COUNTS_RECORDED", frames_ok, f"{did}: integer frame_count and dropped_frames"
            )
            if frames_ok and _pos(dev.get("nominal_fps")) and durations_ok:
                max_frames = math.ceil(rec * dev["nominal_fps"]) + 1
                check(
                    "FRAME_COUNT_PLAUSIBLE",
                    frame_count <= max_frames,
                    f"{did}: frame_count {frame_count} exceeds recorded_duration * fps (+1)",
                )
        dev_report[did] = {
            "recorded_duration_s": rec if _num(rec) else None,
            "gap_total_s": gap_total if gaps_ok else None,
            "gap_count": len(gaps) if gaps_ok else None,
            "coverage_fraction": (rec / expected_s) if (_num(rec) and expected_s) else None,
            "dropped_frames": dropped if isinstance(dropped, int) else None,
            "frame_count": frame_count if isinstance(frame_count, int) else None,
            "dropped_fraction": (
                dropped / (dropped + frame_count)
                if isinstance(dropped, int)
                and isinstance(frame_count, int)
                and dropped + frame_count > 0
                else None
            ),
        }
        # clock drift: required wherever more than one camera must be related
        checks_list = dev.get("clock_checks", [])
        drift = _drift_s_per_hour(checks_list)
        dev_report[did]["clock_drift_s_per_hour"] = drift
        dev_report[did]["clock_check_count"] = (
            len(checks_list) if isinstance(checks_list, list) else 0
        )
    report.accounting["devices"] = dev_report

    roles = [c.get("role") for c in cameras]
    check(
        "CAMERA_CONFIGURATION_SUPPORTED",
        1 <= len(cameras) <= 2
        and all(r in CAMERA_ROLES for r in roles)
        and len(set(roles)) == len(roles),
        "supported: one camera, or exactly one 'front' and one 'back' camera "
        f"(found roles {roles})",
    )
    max_drift = case.get("maximum_clock_drift_s_per_hour")
    if len(cameras) == 2:
        sync = record.get("camera_synchronization")
        if isinstance(sync, Mapping) and sync.get("unresolved") is True:
            check(
                "SYNCHRONIZATION_DECLARED",
                sync.get("offset_s") is None,
                "unresolved synchronization must not carry an offset",
            )
        else:
            ok = (
                isinstance(sync, Mapping)
                and _num(sync.get("offset_s"))
                and sync.get("method") in SYNC_METHODS
            )
            check(
                "SYNCHRONIZATION_DECLARED",
                bool(ok),
                "two cameras need a finite offset_s with a method, or unresolved: true",
            )
        for cam in cameras:
            drift = dev_report.get(cam.get("device_id"), {}).get("clock_drift_s_per_hour")
            check(
                "CLOCK_DRIFT_WITHIN_SAFETY_CASE_LIMIT",
                drift is not None and _pos(max_drift) and abs(drift) <= max_drift,
                f"{cam.get('device_id')}: drift {drift} s/h vs safety-case limit {max_drift}; "
                "needs >= 2 clock checks and a limit from the safety case",
                unverifiable=True,
            )

    # --- chain of custody
    files = record["data_files"] if isinstance(record["data_files"], list) else []
    check("DATA_FILES_PRESENT", bool(files), "data_files must be a nonempty list")
    seen: set[str] = set()
    for entry in files:
        path = entry.get("path") if isinstance(entry, Mapping) else None
        if not _text(path):
            check("DATA_FILE_INVALID", False, "each data file needs a path")
            continue
        pure = PurePosixPath(path)
        check(
            "DATA_FILE_PATH_SAFE",
            not pure.is_absolute() and ".." not in pure.parts and pure.parts[:2] != ("data", "raw"),
            f"{path}: must be relative, without '..', and outside protected data/raw",
        )
        check("DATA_FILE_UNIQUE", path not in seen, f"duplicate path {path}")
        seen.add(path)
        digest = entry.get("sha256")
        check(
            "DATA_FILE_HASH_FORMAT",
            isinstance(digest, str) and bool(_SHA256.fullmatch(digest)),
            f"{path}: sha256 invalid",
        )
        check(
            "DATA_FILE_SIZE_RECORDED",
            isinstance(entry.get("bytes"), int)
            and not isinstance(entry.get("bytes"), bool)
            and entry["bytes"] >= 0,
            f"{path}: bytes must be a non-negative integer",
        )
        check(
            "DATA_FILE_DEVICE_DECLARED",
            entry.get("device_id") in ids,
            f"{path}: device_id is not a declared device",
        )
        custody = entry.get("custody")
        custody_ok = isinstance(custody, list) and bool(custody)
        last: datetime | None = None
        if custody_ok:
            for index, step in enumerate(custody):
                when = _utc(step.get("at_utc")) if isinstance(step, Mapping) else None
                good = (
                    isinstance(step, Mapping)
                    and when is not None
                    and when <= now
                    and (last is None or when >= last)
                    and _text(step.get("actor"))
                    and step.get("action") in CUSTODY_ACTIONS
                    and step.get("sha256_after") == digest
                    and (index > 0 or step.get("action") == "captured")
                )
                if not good:
                    custody_ok = False
                    break
                last = when
        check(
            "CHAIN_OF_CUSTODY_INTACT",
            custody_ok,
            f"{path}: custody must start with 'captured', be time-ordered, name actors and keep "
            "the same sha256_after throughout",
        )
    return report


def _drift_s_per_hour(checks: Any) -> float | None:
    """Linear drift of the offset-to-reference between the first and last clock check."""
    if not isinstance(checks, list) or len(checks) < 2:
        return None
    try:
        ordered = sorted((float(c["at_s"]), float(c["offset_to_reference_s"])) for c in checks)
    except (KeyError, TypeError, ValueError):
        return None
    if any(not math.isfinite(v) for pair in ordered for v in pair):
        return None
    (t0, o0), (t1, o1) = ordered[0], ordered[-1]
    if t1 <= t0:
        return None
    return (o1 - o0) / (t1 - t0) * 3600.0


def collect_software_provenance(root: Path | str) -> dict[str, str]:
    """The ``software`` section, captured from the running installation (not typed by hand)."""
    import platform
    import subprocess

    from railway_detection import __version__

    base = Path(root).resolve()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=base, capture_output=True, text=True, check=False,
            timeout=30,
        )
        revision = out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        revision = ""
    return {
        "package_version": str(__version__),
        "code_revision": revision,  # empty => the SOFTWARE_PROVENANCE check fails closed
        "python_version": platform.python_version(),
    }


def verify_session_files(session_dir: Path | str, record: Mapping[str, Any]) -> dict[str, Any]:
    """Recompute every recorded file's hash and size from disk; report corruption."""
    base = Path(session_dir).resolve()
    results = []
    for entry in record.get("data_files", []):
        relative = entry.get("path", "")
        path = base / relative
        outcome: dict[str, Any] = {"path": relative, "status": "OK"}
        pure = PurePosixPath(relative)
        if not relative or pure.is_absolute() or ".." in pure.parts:
            outcome["status"] = "UNSAFE_PATH"
        elif path.is_symlink() or not path.is_file():
            outcome["status"] = "MISSING"
        else:
            require_media_authorization(path, "HASH_RAW_MEDIA")
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            actual, size = digest.hexdigest(), path.stat().st_size
            if actual != entry.get("sha256"):
                outcome.update(status="HASH_MISMATCH", actual_sha256=actual)
            elif size != entry.get("bytes"):
                outcome.update(status="SIZE_MISMATCH", actual_bytes=size)
        results.append(outcome)
    return {
        "verified": all(r["status"] == "OK" for r in results) and bool(results),
        "files": results,
    }
