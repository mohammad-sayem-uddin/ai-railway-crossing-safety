"""Deterministic, read-only capture-session manifest and preflight records.

This module does not open devices, collect media, or grant permission.  It turns
an already-created Phase 15 capture record into an auditable manifest and makes
the external-authority boundary explicit.  A document hash is evidence of the
bytes submitted to this function; it is not proof that an authority approved
the activity.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from railway_detection.field_validation.capture_session_v2 import (
    SessionValidationReport,
    validate_capture_session_v2,
    verify_session_files,
)

MANIFEST_SCHEMA = "phase15-capture-session-manifest/1"
PREFLIGHT_SCHEMA = "phase15-capture-preflight/1"


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON with stable key/order/encoding for reproducible hashes."""
    try:
        text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"value is not canonically JSON serializable: {exc}") from exc
    return (text + "\n").encode("utf-8")


def sha256_bytes(value: Any) -> str:
    """Hash the canonical representation of a JSON-compatible value."""
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _status_from_report(report: SessionValidationReport) -> tuple[str, str]:
    """Return explicit authorization/safety states from the validator checks."""
    return report.site_authorization_status, report.safety_case_status


def capture_preflight(
    record: Mapping[str, Any],
    *,
    authorized_recorders: frozenset[str],
    now: datetime | None = None,
    session_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Run a fail-closed, read-only preflight for a v2 capture record.

    ``READY`` is intentionally not a possible result: external authorization
    and safety-case approval cannot be established by software.  The strongest
    result is ``STRUCTURALLY_VALID_NOT_PERMISSION`` when all internal checks
    and (if supplied) media hashes pass.
    """
    report = validate_capture_session_v2(
        record, authorized_recorders=authorized_recorders, now=now
    )
    site_status, safety_status = _status_from_report(report)
    file_report = None
    if session_dir is not None:
        file_report = verify_session_files(session_dir, record)

    blockers: list[str] = []
    if site_status == "missing":
        blockers.append("SITE_AUTHORIZATION_MISSING")
    elif site_status == "invalid_reference":
        blockers.append("SITE_AUTHORIZATION_INVALID_REFERENCE")
    else:
        blockers.append("SITE_AUTHORIZATION_EXTERNAL_VERIFICATION_REQUIRED")
    if safety_status == "missing":
        blockers.append("SAFETY_CASE_MISSING")
    elif safety_status == "invalid_reference":
        blockers.append("SAFETY_CASE_INVALID_REFERENCE")
    else:
        blockers.append("SAFETY_CASE_EXTERNAL_VERIFICATION_REQUIRED")
    if not report.structurally_valid:
        blockers.extend(f"VALIDATION:{code}" for code in report.codes())
    if file_report is not None and not file_report["verified"]:
        blockers.append("CAPTURE_FILE_INTEGRITY_FAILED")

    if not report.structurally_valid:
        status = "BLOCKED_STRUCTURAL_INVALID"
    elif site_status == "missing":
        status = "BLOCKED_MISSING_SITE_AUTHORIZATION"
    elif safety_status == "missing":
        status = "BLOCKED_MISSING_SAFETY_CASE"
    elif site_status == "invalid_reference":
        status = "BLOCKED_INVALID_SITE_AUTHORIZATION_REFERENCE"
    elif safety_status == "invalid_reference":
        status = "BLOCKED_INVALID_SAFETY_CASE_REFERENCE"
    elif file_report is not None and not file_report["verified"]:
        status = "BLOCKED_CAPTURE_FILE_INTEGRITY"
    else:
        status = "STRUCTURALLY_VALID_NOT_PERMISSION"

    return {
        "schema_version": PREFLIGHT_SCHEMA,
        "status": status,
        "structurally_valid": report.structurally_valid,
        "external_authorization_verified": False,
        "site_authorization_status": site_status,
        "safety_case_status": safety_status,
        "blockers": sorted(set(blockers)),
        "validation": report.to_dict(),
        "file_verification": file_report,
        "note": (
            "Read-only structural preflight. No result is permission, authorization, "
            "safety approval, or evidence that field activity may begin."
        ),
    }


def build_capture_manifest(
    record: Mapping[str, Any],
    *,
    authorized_recorders: frozenset[str],
    now: datetime | None = None,
    session_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Build a deterministic manifest without mutating ``record`` or disk."""
    preflight = capture_preflight(
        record,
        authorized_recorders=authorized_recorders,
        now=now,
        session_dir=session_dir,
    )
    payload = {
        "schema_version": MANIFEST_SCHEMA,
        "capture_schema_version": record.get("schema_version"),
        "session_id": (
            record.get("identity", {}).get("session_id")
            if isinstance(record.get("identity"), Mapping)
            else None
        ),
        "record_sha256": sha256_bytes(record),
        "preflight": preflight,
        "provenance": {
            "manifest_generator": "railway_detection.field_validation.capture_session_manifest",
            "generated_at_utc": None,
            "field_activity_performed_by_software": False,
        },
    }
    # A manifest is reproducible by design.  Wall-clock generation time would
    # make identical records hash differently, so it is explicitly null.
    return payload


def write_capture_manifest(manifest: Mapping[str, Any], path: Path | str) -> Path:
    """Atomically write canonical manifest JSON and return its destination."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_json_bytes(dict(manifest))
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    try:
        temporary.write_bytes(data)
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return destination


__all__ = [
    "MANIFEST_SCHEMA",
    "PREFLIGHT_SCHEMA",
    "canonical_json_bytes",
    "sha256_bytes",
    "capture_preflight",
    "build_capture_manifest",
    "write_capture_manifest",
]