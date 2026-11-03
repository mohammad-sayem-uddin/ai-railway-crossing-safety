"""Deterministic Phase 15 manifest/preflight tests; synthetic records only."""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime

from railway_detection.field_validation import (
    build_capture_manifest,
    capture_preflight,
    write_capture_manifest,
)
from tests.unit.test_phase15_capture_session_v2 import _record

NOW = datetime(2026, 12, 1, tzinfo=UTC)
RECORDERS = frozenset({"researcher@example.org"})


def test_manifest_is_deterministic_and_never_grants_permission(tmp_path):
    record = _record()
    first = build_capture_manifest(record, authorized_recorders=RECORDERS, now=NOW)
    second = build_capture_manifest(record, authorized_recorders=RECORDERS, now=NOW)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["preflight"]["status"] == "STRUCTURALLY_VALID_NOT_PERMISSION"
    assert first["preflight"]["external_authorization_verified"] is False
    assert first["preflight"]["site_authorization_status"] == "recorded_reference_unverified"
    assert first["preflight"]["safety_case_status"] == "recorded_reference_unverified"

    before = copy.deepcopy(record)
    capture_preflight(record, authorized_recorders=RECORDERS, now=NOW)
    assert record == before


def test_missing_authorization_and_safety_case_are_explicit_blockers():
    record = _record()
    record.pop("site_authorization")
    record.pop("safety_case")
    out = capture_preflight(record, authorized_recorders=RECORDERS, now=NOW)
    assert out["status"] == "BLOCKED_STRUCTURAL_INVALID"
    assert "SITE_AUTHORIZATION_MISSING" in out["blockers"]
    assert "SAFETY_CASE_MISSING" in out["blockers"]
    assert out["site_authorization_status"] == "missing"
    assert out["safety_case_status"] == "missing"


def test_manifest_write_is_canonical_and_replaces_atomically(tmp_path):
    manifest = build_capture_manifest(_record(), authorized_recorders=RECORDERS, now=NOW)
    path = write_capture_manifest(manifest, tmp_path / "nested" / "manifest.json")
    assert json.loads(path.read_text()) == manifest
    assert not list(path.parent.glob("*.tmp"))