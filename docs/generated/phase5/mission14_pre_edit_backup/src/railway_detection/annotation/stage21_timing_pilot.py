"""Fail-closed human-only timing pilot, separate from synthetic adjudication.

This module does not choose boundaries, expose model predictions, approve
records, promote ground truth, or run evaluation. A future real-media session
requires both an allowlisted, scope-bound unsigned researcher statement and a
separate activation statement bound to the exact tested release. Hashes bind
files but are not cryptographic proof of authorship.

Preparation/test mode is confined to synthetic fixtures beneath the system
temporary directory. It rejects the project checkout before reading any input.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from railway_detection.safety.media_guard import require_media_authorization

RELEASE_SCHEMA = "stage21-human-review-timing-pilot-release/1"
AUTHORIZATION_SCHEMA = "stage21-human-review-pilot-authorization/1"
ACTIVATION_SCHEMA = "stage21-human-review-pilot-activation/1"
DRAFT_SCHEMA = "stage21-human-review-timing-pilot-record/1"
OPERATION = "stage21_human_review_timing_pilot"
PURPOSE = "genuine_review_timing_pilot"
RELEASE_VERSION = "0.1.0"
OUTPUT_RELATIVE = Path("data/ground_truth/review_pilots")
RELEASE_RELATIVE = Path("docs/generated/stage21_timing_pilot_release.json")
RELEASE_REPORT_RELATIVE = Path("docs/STAGE21_TIMING_PILOT_RELEASE_20261019.md")
IMPLEMENTATION_RELATIVE = Path("src/railway_detection/annotation/stage21_timing_pilot.py")
SCHEMA_RELATIVE = Path("schemas/stage21_timing_pilot.schema.json")
TEST_RELATIVE = Path("tests/test_stage21_timing_pilot.py")
RELEASE_FILES = (
    (IMPLEMENTATION_RELATIVE, "implementation"),
    (SCHEMA_RELATIVE, "schema"),
    (TEST_RELATIVE, "tests"),
)
PERMITTED_OPERATIONS = frozenset(
    {
        "hash_source_media",
        "open_source_media",
        "view_source_media",
        "record_human_timing",
        "write_unapproved_pilot_draft",
    }
)
BOUNDARIES = (
    "T0_first_visible",
    "T1_danger_zone_entry",
    "T2_crossing_occupancy_start",
    "T3_locomotive_unit_clearance",
    "T4_tail_clearance",
    "T_scene_clear",
)
_EVENT_KEY = re.compile(r"(train_events|no_train_events|engine_events)/event_[0-9]{3}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_OFFICIAL_BLOCKED = (
    _REPOSITORY_ROOT / "data/ground_truth/reviews",
    _REPOSITORY_ROOT / "data/evaluation",
    _REPOSITORY_ROOT / "results",
    _REPOSITORY_ROOT / "experiments",
)
_AUTH_KEYS = frozenset(
    {
        "schema_version",
        "authorization_id",
        "authorized_by",
        "authorized_at_utc",
        "expires_at_utc",
        "authorization_statement",
        "scope",
        "attestation",
        "recorded_by",
        "record_sha256",
    }
)
_SCOPE_KEYS = frozenset(
    {
        "operation",
        "purpose",
        "event_keys",
        "reviewer_ids",
        "workflow_release_sha256",
        "permitted_operations",
        "output_directory",
        "source_inventory_sha256",
        "source_media_sha256_by_event",
        "active_proposal_sha256_by_event",
        "no_official_approval",
    }
)
_ACTIVATION_KEYS = frozenset(
    {
        "schema_version",
        "activation_id",
        "activated_by",
        "activated_at_utc",
        "expires_at_utc",
        "authorization_sha256",
        "workflow_release_sha256",
        "scope_sha256",
        "activation_statement",
        "attestation",
        "record_sha256",
    }
)
_SESSION_CAPABILITY = object()


class PilotWorkflowError(ValueError):
    """Fail-closed validation or workflow error with a stable error code."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def canonical_json_bytes(value: Any) -> bytes:
    """Stable UTF-8 JSON representation used for all content hashes."""
    try:
        text = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        )
    except (TypeError, ValueError) as exc:
        raise PilotWorkflowError("JSON_NOT_CANONICALIZABLE", str(exc)) from exc
    return (text + "\n").encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _body_sha256(value: Mapping[str, Any]) -> str:
    return canonical_sha256({key: item for key, item in value.items() if key != "record_sha256"})


def _seal(value: dict[str, Any]) -> dict[str, Any]:
    value.pop("record_sha256", None)
    value["record_sha256"] = _body_sha256(value)
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise PilotWorkflowError("HASH_INVALID", f"{label} must be lowercase SHA-256")
    return value


def _utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise PilotWorkflowError("TIMESTAMP_INVALID", f"{label} is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PilotWorkflowError("TIMESTAMP_INVALID", f"{label} is not ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise PilotWorkflowError("TIMESTAMP_INVALID", f"{label} must be explicitly UTC")
    return parsed.astimezone(UTC)


def _parse_document(path: Path, code: str = "ARTIFACT_INVALID") -> dict[str, Any]:
    if not path.is_file():
        raise PilotWorkflowError("ARTIFACT_MISSING", f"required artifact is missing: {path}")
    if path.is_symlink():
        raise PilotWorkflowError(code, f"symlink artifacts are refused: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PilotWorkflowError(code, f"cannot read JSON artifact {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PilotWorkflowError(code, f"JSON artifact must be an object: {path}")
    return payload


def _resolve_beneath(root: Path, relative: Any, *, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise PilotWorkflowError("PATH_INVALID", f"{label} must be a non-empty relative path")
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise PilotWorkflowError("PATH_INVALID", f"{label} escapes repository root")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    if resolved == resolved_root or not resolved.is_relative_to(resolved_root):
        raise PilotWorkflowError("PATH_INVALID", f"{label} escapes repository root")
    return resolved


def _require_preparation_isolation(root: Path, paths: tuple[Path, ...]) -> None:
    """Refuse the actual checkout and all official evidence locations pre-read."""
    resolved_root = root.expanduser().resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if not resolved_root.is_relative_to(temp_root) or resolved_root == _REPOSITORY_ROOT:
        raise PilotWorkflowError(
            "PREPARATION_ISOLATION_REQUIRED",
            "preparation_only requires a synthetic repository beneath the system temporary "
            "directory",
        )
    if resolved_root.is_relative_to(_REPOSITORY_ROOT) or _REPOSITORY_ROOT.is_relative_to(
        resolved_root
    ):
        raise PilotWorkflowError(
            "PREPARATION_ISOLATION_REQUIRED", "project checkout is forbidden in preparation mode"
        )
    for path in paths:
        resolved = path.expanduser().resolve()
        if resolved.is_relative_to(_REPOSITORY_ROOT):
            raise PilotWorkflowError(
                "PREPARATION_ISOLATION_REQUIRED", f"repository path refused: {path}"
            )
        if not resolved.is_relative_to(resolved_root):
            raise PilotWorkflowError(
                "PREPARATION_ISOLATION_REQUIRED", f"input outside synthetic root: {path}"
            )
        for blocked in _OFFICIAL_BLOCKED:
            blocked_resolved = blocked.resolve()
            if resolved == blocked_resolved or resolved.is_relative_to(blocked_resolved):
                raise PilotWorkflowError(
                    "PREPARATION_ISOLATION_REQUIRED", f"official path refused: {path}"
                )


@dataclass(frozen=True)
class VerifiedRelease:
    path: Path
    sha256: str
    version: str
    files: tuple[dict[str, str], ...]
    intended_scope: dict[str, Any]


def verify_release_manifest(
    manifest_path: Path | str,
    *,
    expected_release_sha256: str,
    repository_root: Path | str,
) -> VerifiedRelease:
    root = Path(repository_root).expanduser().resolve()
    path = Path(manifest_path).expanduser().resolve()
    if not path.is_relative_to(root):
        raise PilotWorkflowError(
            "RELEASE_MANIFEST_PATH_INVALID", "release manifest must be beneath root"
        )
    if path.is_symlink() or not path.is_file():
        raise PilotWorkflowError(
            "RELEASE_MANIFEST_INVALID", "release manifest must be a regular file"
        )
    _require_sha(expected_release_sha256, "expected release hash")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PilotWorkflowError(
            "ARTIFACT_MISSING", f"cannot read release manifest: {exc}"
        ) from exc
    actual = _sha256_bytes(raw)
    if actual != expected_release_sha256:
        raise PilotWorkflowError(
            "RELEASE_HASH_MISMATCH", "release manifest differs from expected hash"
        )
    try:
        manifest = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PilotWorkflowError("RELEASE_MANIFEST_INVALID", str(exc)) from exc
    if not isinstance(manifest, dict):
        raise PilotWorkflowError(
            "RELEASE_MANIFEST_INVALID", "release manifest must be a JSON object"
        )
    if (
        manifest.get("schema_version") != RELEASE_SCHEMA
        or manifest.get("status") != "PREPARED_NOT_ACTIVATED"
        or not isinstance(manifest.get("version"), str)
        or not manifest["version"].strip()
        or set(manifest)
        != {"schema_version", "version", "status", "files", "test_results", "intended_scope"}
    ):
        raise PilotWorkflowError(
            "RELEASE_MANIFEST_INVALID", "schema, version, or inactive status is invalid"
        )
    intended = manifest.get("intended_scope")
    expected_scope = {
        "operation": OPERATION,
        "purpose": PURPOSE,
        "evaluative": False,
        "activated_for_real_media": False,
    }
    if intended != expected_scope:
        raise PilotWorkflowError(
            "RELEASE_SCOPE_INVALID", "release scope must remain non-evaluative and inactive"
        )
    result = manifest.get("test_results")
    if not isinstance(result, dict) or result.get("focused_status") != "passed":
        raise PilotWorkflowError(
            "RELEASE_TESTS_NOT_PASSED", "focused tests must pass before release"
        )
    entries = manifest.get("files")
    if not isinstance(entries, list) or len(entries) != len(RELEASE_FILES):
        raise PilotWorkflowError(
            "RELEASE_FILE_INVENTORY_INVALID", "release must bind exactly three files"
        )
    expected = {rel.as_posix(): role for rel, role in RELEASE_FILES}
    found: dict[str, str] = {}
    normalized: list[dict[str, str]] = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "role"}:
            raise PilotWorkflowError(
                "RELEASE_FILE_INVENTORY_INVALID", "release file entry has wrong shape"
            )
        rel = entry["path"]
        digest = _require_sha(entry["sha256"], f"release file {rel}")
        role = entry["role"]
        if not isinstance(rel, str) or rel in found or expected.get(rel) != role:
            raise PilotWorkflowError(
                "RELEASE_FILE_INVENTORY_INVALID", f"unexpected or duplicate file: {rel}"
            )
        file_path = _resolve_beneath(root, rel, label="release file")
        if not file_path.is_file() or file_path.is_symlink():
            raise PilotWorkflowError("RELEASE_FILE_MISSING", f"release file unavailable: {rel}")
        if _sha256_bytes(file_path.read_bytes()) != digest:
            raise PilotWorkflowError("RELEASE_FILE_HASH_MISMATCH", f"release file changed: {rel}")
        found[rel] = role
        normalized.append({"path": rel, "sha256": digest, "role": role})
    if found != expected:
        raise PilotWorkflowError(
            "RELEASE_FILE_INVENTORY_INVALID",
            "release inventory is not the exact implementation/schema/test set",
        )
    return VerifiedRelease(path, actual, manifest["version"], tuple(normalized), intended)


def _verify_record_seal(payload: Mapping[str, Any], label: str, code: str) -> str:
    recorded = payload.get("record_sha256")
    if (
        not isinstance(recorded, str)
        or not _SHA256.fullmatch(recorded)
        or _body_sha256(payload) != recorded
    ):
        raise PilotWorkflowError(code, f"{label} content hash is invalid or record was tampered")
    return canonical_sha256(dict(payload))


def validate_authorization(
    authorization: dict[str, Any],
    *,
    allowlisted_researchers: frozenset[str],
    release: VerifiedRelease,
    event_key: str,
    reviewer_id: str,
    now: datetime,
) -> str:
    if not isinstance(authorization, dict) or set(authorization) != _AUTH_KEYS:
        raise PilotWorkflowError(
            "AUTHORIZATION_INVALID", "authorization fields do not exactly match schema"
        )
    if authorization.get("schema_version") != AUTHORIZATION_SCHEMA:
        raise PilotWorkflowError("AUTHORIZATION_INVALID", "unsupported authorization schema")
    digest = _verify_record_seal(authorization, "authorization", "AUTHORIZATION_TAMPERED")
    for field in ("authorization_id", "authorization_statement", "authorized_by"):
        if not isinstance(authorization.get(field), str) or not authorization[field].strip():
            raise PilotWorkflowError("AUTHORIZATION_INVALID", f"{field} is required")
    if authorization["authorized_by"] not in allowlisted_researchers:
        raise PilotWorkflowError(
            "RESEARCHER_NOT_AUTHORIZED", "author is not on the maintained researcher allowlist"
        )
    attestation = authorization.get("attestation")
    if attestation != {"type": "RECORDED_RESEARCHER_STATEMENT", "signature": None}:
        raise PilotWorkflowError(
            "AUTHORIZATION_INVALID", "attestation must be an explicitly unsigned recorded statement"
        )
    recorder = authorization.get("recorded_by")
    if not isinstance(recorder, dict) or set(recorder) - {
        "kind",
        "identity",
        "transcription_source",
    }:
        raise PilotWorkflowError("AUTHORIZATION_INVALID", "recorded_by has invalid fields")
    if (
        recorder.get("kind") not in {"researcher", "agent_transcription"}
        or not isinstance(recorder.get("identity"), str)
        or not recorder["identity"].strip()
    ):
        raise PilotWorkflowError(
            "AUTHORIZATION_INVALID", "recorded_by identity and kind are required"
        )
    if recorder["kind"] == "agent_transcription" and not (
        isinstance(recorder.get("transcription_source"), str)
        and recorder["transcription_source"].strip()
    ):
        raise PilotWorkflowError("AUTHORIZATION_INVALID", "agent transcription source is required")
    authorized_at = _utc(authorization.get("authorized_at_utc"), "authorized_at_utc")
    expires_at = _utc(authorization.get("expires_at_utc"), "expires_at_utc")
    if authorized_at > now or expires_at <= now or expires_at <= authorized_at:
        raise PilotWorkflowError(
            "AUTHORIZATION_EXPIRED_OR_INVALID", "authorization is not currently valid"
        )
    scope = authorization.get("scope")
    if not isinstance(scope, dict) or set(scope) != _SCOPE_KEYS:
        raise PilotWorkflowError(
            "AUTHORIZATION_INVALID", "scope fields do not exactly match schema"
        )
    if scope.get("operation") != OPERATION or scope.get("purpose") != PURPOSE:
        raise PilotWorkflowError("AUTHORIZATION_SCOPE_MISMATCH", "operation or purpose differs")
    if (
        scope.get("no_official_approval") is not True
        or scope.get("output_directory") != OUTPUT_RELATIVE.as_posix()
    ):
        raise PilotWorkflowError(
            "AUTHORIZATION_SCOPE_MISMATCH", "output or non-approval boundary differs"
        )
    if scope.get("permitted_operations") != sorted(PERMITTED_OPERATIONS):
        raise PilotWorkflowError(
            "OPERATION_SCOPE_INVALID", "permitted operations must equal the fixed human-pilot set"
        )
    event_keys = scope.get("event_keys")
    if not isinstance(event_keys, list) or not event_keys:
        raise PilotWorkflowError("EVENT_SCOPE_INVALID", "event scope must be non-empty and unique")
    if any(not isinstance(key, str) or not _EVENT_KEY.fullmatch(key) for key in event_keys):
        raise PilotWorkflowError(
            "EVENT_ID_INVALID", "event keys must be cohort-qualified event identifiers"
        )
    if len(set(event_keys)) != len(event_keys):
        raise PilotWorkflowError("EVENT_SCOPE_INVALID", "event scope must not contain duplicates")
    if event_key not in event_keys:
        raise PilotWorkflowError("EVENT_OUT_OF_SCOPE", f"event is not authorized: {event_key}")
    reviewers = scope.get("reviewer_ids")
    if not isinstance(reviewers, list) or not reviewers:
        raise PilotWorkflowError(
            "REVIEWER_SCOPE_INVALID", "reviewer scope must be non-empty and unique"
        )
    if any(not isinstance(item, str) or not item.strip() for item in reviewers):
        raise PilotWorkflowError("REVIEWER_SCOPE_INVALID", "reviewer identities must be non-empty")
    if len(set(reviewers)) != len(reviewers):
        raise PilotWorkflowError(
            "REVIEWER_SCOPE_INVALID", "reviewer scope must not contain duplicates"
        )
    if reviewer_id not in reviewers:
        raise PilotWorkflowError(
            "REVIEWER_OUT_OF_SCOPE", f"reviewer is not authorized for this event: {reviewer_id}"
        )
    if reviewer_id not in allowlisted_researchers:
        raise PilotWorkflowError(
            "REVIEWER_NOT_AUTHORIZED", "reviewer is not on the maintained reviewer allowlist"
        )
    if scope.get("workflow_release_sha256") != release.sha256:
        raise PilotWorkflowError(
            "RELEASE_HASH_MISMATCH", "authorization does not bind this workflow release"
        )
    _require_sha(scope.get("source_inventory_sha256"), "source inventory hash")
    media = scope.get("source_media_sha256_by_event")
    proposals = scope.get("active_proposal_sha256_by_event")
    if not isinstance(media, dict) or set(media) != set(event_keys):
        raise PilotWorkflowError(
            "MEDIA_BINDING_MISMATCH", "media hash map must exactly match authorized events"
        )
    if not isinstance(proposals, dict) or set(proposals) != set(event_keys):
        raise PilotWorkflowError(
            "PROPOSAL_BINDING_MISMATCH", "proposal hash map must exactly match authorized events"
        )
    for key in event_keys:
        camera_hashes = media[key]
        if not isinstance(camera_hashes, dict) or set(camera_hashes) != {"front", "back"}:
            raise PilotWorkflowError(
                "MEDIA_BINDING_MISMATCH", f"front/back hashes missing for {key}"
            )
        for camera, digest_value in camera_hashes.items():
            _require_sha(digest_value, f"{key} {camera} media hash")
        _require_sha(proposals[key], f"{key} proposal hash")
    return digest


def validate_activation(
    activation: dict[str, Any],
    *,
    authorization: dict[str, Any],
    authorization_sha256: str,
    release: VerifiedRelease,
    allowlisted_researchers: frozenset[str],
    now: datetime,
) -> str:
    if not isinstance(activation, dict) or set(activation) != _ACTIVATION_KEYS:
        raise PilotWorkflowError(
            "ACTIVATION_INVALID", "activation fields do not exactly match schema"
        )
    if activation.get("schema_version") != ACTIVATION_SCHEMA:
        raise PilotWorkflowError("ACTIVATION_INVALID", "unsupported activation schema")
    digest = _verify_record_seal(activation, "activation", "ACTIVATION_TAMPERED")
    for field in ("activation_id", "activated_by", "activation_statement"):
        if not isinstance(activation.get(field), str) or not activation[field].strip():
            raise PilotWorkflowError("ACTIVATION_INVALID", f"{field} is required")
    if activation["activated_by"] not in allowlisted_researchers:
        raise PilotWorkflowError(
            "ACTIVATION_RESEARCHER_NOT_AUTHORIZED", "activation authority is not allowlisted"
        )
    if activation["activated_by"] != authorization["authorized_by"]:
        raise PilotWorkflowError(
            "ACTIVATION_AUTHORITY_MISMATCH", "activation and authorization authorities differ"
        )
    if activation.get("attestation") != {
        "type": "RECORDED_RESEARCHER_STATEMENT",
        "signature": None,
    }:
        raise PilotWorkflowError("ACTIVATION_INVALID", "activation must be explicitly unsigned")
    start = _utc(activation.get("activated_at_utc"), "activated_at_utc")
    end = _utc(activation.get("expires_at_utc"), "activation expires_at_utc")
    auth_end = _utc(authorization["expires_at_utc"], "authorization expires_at_utc")
    auth_start = _utc(authorization["authorized_at_utc"], "authorization authorized_at_utc")
    if start > now or start < auth_start or end <= now or end <= start or end > auth_end:
        raise PilotWorkflowError(
            "ACTIVATION_EXPIRED_OR_INVALID",
            "activation is invalid or exceeds authorization lifetime",
        )
    expected = {
        "authorization_sha256": authorization_sha256,
        "workflow_release_sha256": release.sha256,
        "scope_sha256": canonical_sha256(authorization["scope"]),
    }
    for key, value in expected.items():
        if activation.get(key) != value:
            if key == "workflow_release_sha256":
                raise PilotWorkflowError(
                    "RELEASE_HASH_MISMATCH", "activation does not bind this release"
                )
            raise PilotWorkflowError("ACTIVATION_BINDING_MISMATCH", f"activation {key} differs")
    return digest


@dataclass(frozen=True)
class MediaAccessGrant:
    event_key: str
    reviewer_id: str
    workflow_release_sha256: str
    authorization_sha256: str
    activation_sha256: str
    source_inventory_sha256: str
    front_sha256: str
    back_sha256: str
    proposal_sha256: str
    front_media_path: Path
    back_media_path: Path
    front_relative_path: str
    back_relative_path: str
    authorization_expires_at_utc: str
    activation_expires_at_utc: str
    repository_root: Path
    authorization_path: Path
    activation_path: Path
    release_manifest_path: Path
    allowlist_path: Path
    inventory_path: Path
    queue_path: Path


@dataclass(frozen=True)
class TimingSession:
    grant: MediaAccessGrant
    session_id: str
    started_at_utc: str
    monotonic_started_s: float
    utc_clock: Callable[[], datetime] | None = dataclass_field(
        default=None, repr=False, compare=False
    )
    monotonic_clock: Callable[[], float] | None = dataclass_field(
        default=None, repr=False, compare=False
    )
    _capability: object | None = dataclass_field(default=None, repr=False, compare=False)


@dataclass(frozen=True)
class PreparationOnlyAuthorization:
    """Synthetic fixture grant; never represents researcher authorization."""

    repository_root: Path
    event_key: str
    reviewer_id: str
    release_sha256: str
    inventory_sha256: str
    front_sha256: str
    back_sha256: str
    proposal_sha256: str
    scope_sha256: str
    expires_at_utc: str
    output_directory: str


def record_preparation_authorization(
    *,
    repository_root: Path | str,
    event_key: str,
    reviewer_id: str,
    release: VerifiedRelease,
    inventory_path: Path | str,
    queue_path: Path | str,
    now: datetime,
    expires_at_utc: str,
    permitted_operations: frozenset[str],
    output_directory: str,
) -> PreparationOnlyAuthorization:
    """Issue a non-persisted synthetic grant only for temporary test fixtures."""
    root = Path(repository_root).expanduser().resolve()
    paths = (Path(inventory_path).expanduser(), Path(queue_path).expanduser())
    _require_preparation_isolation(root, paths)
    if not isinstance(event_key, str) or not _EVENT_KEY.fullmatch(event_key):
        raise PilotWorkflowError("EVENT_ID_INVALID", "event key must include a valid cohort")
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        raise PilotWorkflowError("REVIEWER_SCOPE_INVALID", "synthetic reviewer id is required")
    if permitted_operations != frozenset({"record_human_timing"}):
        raise PilotWorkflowError(
            "OPERATION_SCOPE_INVALID", "preparation grants permit timing observation only"
        )
    if output_directory != OUTPUT_RELATIVE.as_posix():
        raise PilotWorkflowError("AUTHORIZATION_SCOPE_MISMATCH", "preparation output path is fixed")
    expiry = _utc(expires_at_utc, "preparation expiry")
    if now.tzinfo is None or expiry <= now.astimezone(UTC):
        raise PilotWorkflowError(
            "AUTHORIZATION_EXPIRED_OR_INVALID", "preparation grant expiry is invalid"
        )
    inventory = Path(inventory_path).expanduser()
    queue = Path(queue_path).expanduser()
    if not inventory.is_absolute():
        inventory = root / inventory
    if not queue.is_absolute():
        queue = root / queue
    inventory_hash, media, front_rel, back_rel, proposal_hash, _queue_hash = _metadata_bindings(
        root=root, event_key=event_key, inventory_path=inventory, queue_path=queue
    )
    front_path = _resolve_beneath(root, front_rel, label="synthetic front fixture")
    back_path = _resolve_beneath(root, back_rel, label="synthetic back fixture")
    if _hash_file(front_path) != media["front"] or _hash_file(back_path) != media["back"]:
        raise PilotWorkflowError(
            "MEDIA_HASH_MISMATCH", "synthetic fixture bytes differ from inventory"
        )
    return PreparationOnlyAuthorization(
        repository_root=root,
        event_key=event_key,
        reviewer_id=reviewer_id,
        release_sha256=release.sha256,
        inventory_sha256=inventory_hash,
        front_sha256=media["front"],
        back_sha256=media["back"],
        proposal_sha256=proposal_hash,
        scope_sha256=canonical_sha256(
            {
                "operation": OPERATION,
                "purpose": PURPOSE,
                "event_key": event_key,
                "reviewer_id": reviewer_id,
                "release_sha256": release.sha256,
                "inventory_sha256": inventory_hash,
                "media_sha256": media,
                "proposal_sha256": proposal_hash,
                "permitted_operations": sorted(permitted_operations),
                "output_directory": output_directory,
            }
        ),
        expires_at_utc=expiry.isoformat().replace("+00:00", "Z"),
        output_directory=output_directory,
    )


def _metadata_bindings(
    *, root: Path, event_key: str, inventory_path: Path, queue_path: Path
) -> tuple[str, dict[str, str], str, str, str, str]:
    if not _EVENT_KEY.fullmatch(event_key):
        raise PilotWorkflowError("EVENT_ID_INVALID", "event key must include a cohort")
    try:
        inventory_raw = inventory_path.read_bytes()
        inventory = json.loads(inventory_raw)
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PilotWorkflowError(
            "ARTIFACT_INVALID", f"inventory/queue metadata unreadable: {exc}"
        ) from exc
    if not isinstance(inventory, dict) or not isinstance(queue, dict):
        raise PilotWorkflowError("ARTIFACT_INVALID", "inventory and queue must be JSON objects")
    entry = inventory.get(event_key)
    if not isinstance(entry, dict):
        raise PilotWorkflowError(
            "EVENT_OUT_OF_SCOPE", f"event absent from source inventory: {event_key}"
        )
    items = queue.get("items")
    if not isinstance(items, list):
        raise PilotWorkflowError("ARTIFACT_INVALID", "review queue has no items list")
    matches = [
        item for item in items if isinstance(item, dict) and item.get("event_key") == event_key
    ]
    if len(matches) != 1:
        raise PilotWorkflowError(
            "QUEUE_EVENT_INVALID", "queue must contain exactly one matching event"
        )
    item = matches[0]
    media_paths: dict[str, str] = {}
    media_hashes: dict[str, str] = {}
    for camera in ("front", "back"):
        description = entry.get(camera)
        queued = item.get("inventory_media_sha256", {}).get(camera)
        if not isinstance(description, dict) or not isinstance(description.get("path"), str):
            raise PilotWorkflowError("MEDIA_BINDING_MISMATCH", f"inventory lacks {camera} source")
        digest = _require_sha(description.get("sha256"), f"inventory {camera} hash")
        if queued != digest:
            raise PilotWorkflowError(
                "MEDIA_BINDING_MISMATCH", f"queue and inventory differ for {camera}"
            )
        media_paths[camera] = description["path"]
        media_hashes[camera] = digest
    active = item.get("active_candidate_proposal")
    if not isinstance(active, dict) or not isinstance(active.get("path"), str):
        raise PilotWorkflowError(
            "PROPOSAL_BINDING_MISMATCH", "queue does not name the active proposal"
        )
    proposal_path = _resolve_beneath(root, active["path"], label="proposal")
    if not proposal_path.is_file() or proposal_path.is_symlink():
        raise PilotWorkflowError(
            "PROPOSAL_BINDING_MISMATCH", "active proposal is missing or symlinked"
        )
    proposal_hash = _sha256_bytes(proposal_path.read_bytes())
    if proposal_hash != active.get("sha256"):
        raise PilotWorkflowError(
            "PROPOSAL_BINDING_MISMATCH", "active proposal hash differs from queue"
        )
    return (
        _sha256_bytes(inventory_raw),
        media_hashes,
        media_paths["front"],
        media_paths["back"],
        proposal_hash,
        canonical_sha256(queue),
    )


def _load_allowlist(path: Path) -> frozenset[str]:
    value = _parse_document(path)
    reviewers = value.get("authorized_reviewers")
    if (
        not isinstance(reviewers, list)
        or not reviewers
        or any(not isinstance(item, str) or not item.strip() for item in reviewers)
        or len(set(reviewers)) != len(reviewers)
    ):
        raise PilotWorkflowError(
            "ALLOWLIST_INVALID", "authorized_reviewers must be non-empty and unique"
        )
    return frozenset(reviewers)


def start_timing_session(
    *,
    repository_root: Path | str,
    authorization_path: Path | str,
    activation_path: Path | str,
    release_manifest_path: Path | str,
    expected_release_sha256: str,
    inventory_path: Path | str,
    queue_path: Path | str,
    allowlist_path: Path | str,
    event_key: str,
    reviewer_id: str,
    session_id: str,
    preparation_only: bool = False,
    preparation_grant: PreparationOnlyAuthorization | None = None,
    now: datetime | None = None,
    utc_clock: Callable[[], datetime] | None = None,
    monotonic_clock: Callable[[], float] | None = None,
) -> TimingSession:
    root = Path(repository_root).expanduser().resolve()
    paths = tuple(
        Path(item).expanduser()
        for item in (
            authorization_path,
            activation_path,
            release_manifest_path,
            inventory_path,
            queue_path,
            allowlist_path,
        )
    )
    if preparation_only:
        _require_preparation_isolation(root, paths)
        if preparation_grant is None:
            raise PilotWorkflowError(
                "PREPARATION_GRANT_REQUIRED", "synthetic preparation grant is required"
            )
    normalized_paths: list[Path] = []
    for label, path in zip(
        ("authorization", "activation", "release manifest", "inventory", "queue", "allowlist"),
        paths,
        strict=True,
    ):
        if not path.is_absolute():
            path = root / path
        path = path.resolve()
        if not path.is_relative_to(root):
            raise PilotWorkflowError("PATH_INVALID", f"{label} must be beneath repository root")
        normalized_paths.append(path)
    auth_path, activation_file, release_path, inventory_file, queue_file, allowlist_file = (
        normalized_paths
    )
    if not isinstance(session_id, str) or not re.fullmatch(
        r"session-[A-Za-z0-9_-]{1,80}", session_id
    ):
        raise PilotWorkflowError(
            "SESSION_ID_INVALID", "session id must use session- prefix and safe characters"
        )
    if not preparation_only and (
        now is not None or utc_clock is not None or monotonic_clock is not None
    ):
        raise PilotWorkflowError(
            "CLOCK_OVERRIDE_FORBIDDEN",
            "clock overrides are permitted only for isolated synthetic preparation tests",
        )
    current = (now or datetime.now(UTC)) if preparation_only else datetime.now(UTC)
    release = verify_release_manifest(
        release_path,
        expected_release_sha256=expected_release_sha256,
        repository_root=root,
    )
    if preparation_only and (
        preparation_grant.repository_root != root
        or preparation_grant.event_key != event_key
        or preparation_grant.reviewer_id != reviewer_id
        or preparation_grant.release_sha256 != release.sha256
        or preparation_grant.output_directory != OUTPUT_RELATIVE.as_posix()
        or current.astimezone(UTC) >= _utc(preparation_grant.expires_at_utc, "preparation expiry")
    ):
        raise PilotWorkflowError(
            "PREPARATION_GRANT_INVALID", "synthetic grant is expired or does not bind this session"
        )
    authorization = _parse_document(auth_path, "AUTHORIZATION_INVALID")
    allowlisted = _load_allowlist(allowlist_file)
    auth_hash = validate_authorization(
        authorization,
        allowlisted_researchers=allowlisted,
        release=release,
        event_key=event_key,
        reviewer_id=reviewer_id,
        now=current,
    )
    activation = _parse_document(activation_file, "ACTIVATION_INVALID")
    activation_hash = validate_activation(
        activation,
        authorization=authorization,
        authorization_sha256=auth_hash,
        release=release,
        allowlisted_researchers=allowlisted,
        now=current,
    )
    inventory_hash, live_media, front_rel, back_rel, proposal_hash, _queue_hash = (
        _metadata_bindings(
            root=root, event_key=event_key, inventory_path=inventory_file, queue_path=queue_file
        )
    )
    scope = authorization["scope"]
    if scope["source_inventory_sha256"] != inventory_hash:
        raise PilotWorkflowError(
            "INVENTORY_BINDING_MISMATCH", "live inventory differs from authorization"
        )
    if scope["source_media_sha256_by_event"].get(event_key) != live_media:
        raise PilotWorkflowError(
            "MEDIA_BINDING_MISMATCH", "live inventory media hashes differ from authorization"
        )
    if scope["active_proposal_sha256_by_event"].get(event_key) != proposal_hash:
        raise PilotWorkflowError(
            "PROPOSAL_BINDING_MISMATCH", "live active proposal differs from authorization"
        )
    if preparation_only and (
        preparation_grant.inventory_sha256 != inventory_hash
        or preparation_grant.front_sha256 != live_media["front"]
        or preparation_grant.back_sha256 != live_media["back"]
        or preparation_grant.proposal_sha256 != proposal_hash
    ):
        raise PilotWorkflowError(
            "PREPARATION_GRANT_INVALID", "synthetic metadata changed after grant creation"
        )
    front_path = _resolve_beneath(root, front_rel, label="front media")
    back_path = _resolve_beneath(root, back_rel, label="back media")
    # This is the first source-media byte access; both unsigned researcher
    # authorization and the separate activation have already been verified.
    live_hashes = {
        "front": _hash_file(front_path),
        "back": _hash_file(back_path),
    }
    if live_hashes != live_media:
        raise PilotWorkflowError(
            "MEDIA_HASH_MISMATCH", "live source bytes differ from inventory hashes"
        )
    if preparation_only:
        clock = utc_clock or (lambda: datetime.now(UTC))
        mono = monotonic_clock or time.monotonic
    else:

        def clock() -> datetime:
            return datetime.now(UTC)

        mono = time.monotonic
    started = clock().astimezone(UTC)
    grant = MediaAccessGrant(
        event_key=event_key,
        reviewer_id=reviewer_id,
        workflow_release_sha256=release.sha256,
        authorization_sha256=auth_hash,
        activation_sha256=activation_hash,
        source_inventory_sha256=inventory_hash,
        front_sha256=live_hashes["front"],
        back_sha256=live_hashes["back"],
        proposal_sha256=proposal_hash,
        front_media_path=front_path,
        back_media_path=back_path,
        front_relative_path=front_rel,
        back_relative_path=back_rel,
        authorization_expires_at_utc=authorization["expires_at_utc"],
        activation_expires_at_utc=activation["expires_at_utc"],
        repository_root=root,
        authorization_path=auth_path,
        activation_path=activation_file,
        release_manifest_path=release_path,
        allowlist_path=allowlist_file,
        inventory_path=inventory_file,
        queue_path=queue_file,
    )
    return TimingSession(
        grant,
        session_id,
        started.isoformat().replace("+00:00", "Z"),
        mono(),
        utc_clock=None if preparation_only else clock,
        monotonic_clock=None if preparation_only else mono,
        _capability=_SESSION_CAPABILITY,
    )


def _hash_file(path: Path) -> str:
    require_media_authorization(path, "HASH_RAW_MEDIA")
    if not path.is_file() or path.is_symlink():
        raise PilotWorkflowError("MEDIA_MISSING", f"source media missing or symlinked: {path}")
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise PilotWorkflowError("MEDIA_READ_FAILED", f"cannot hash media bytes: {exc}") from exc
    return digest.hexdigest()


def _finite_nonnegative(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def _validate_observations(observations: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(observations, Mapping):
        raise PilotWorkflowError("TIMING_FIELDS_INVALID", "observations must be an object")
    if any(not isinstance(key, str) for key in observations):
        raise PilotWorkflowError("TIMING_FIELDS_INVALID", "boundary names must be strings")
    missing = sorted(set(BOUNDARIES) - set(observations))
    extra = sorted(set(observations) - set(BOUNDARIES))
    if missing or extra:
        raise PilotWorkflowError("TIMING_FIELDS_MISSING", f"missing={missing}; unexpected={extra}")
    fields = {
        "state",
        "value_s",
        "reference_camera",
        "timestamp_basis",
        "timestamp_uncertainty_s",
        "rationale",
        "evidence_status",
        "missing_evidence_reason",
        "censoring_direction",
    }
    normalized: dict[str, dict[str, Any]] = {}
    for boundary in BOUNDARIES:
        item = observations[boundary]
        if not isinstance(item, Mapping) or set(item) != fields:
            raise PilotWorkflowError(
                "TIMING_FIELDS_INVALID", f"{boundary} fields do not match schema"
            )
        value = dict(item)
        state = value["state"]
        if not isinstance(state, str) or state not in {
            "OBSERVABLE",
            "UNOBSERVABLE_NOT_APPLICABLE",
            "CENSORED",
            "UNCERTAIN",
        }:
            raise PilotWorkflowError("TIMING_FIELDS_INVALID", f"{boundary} state is invalid")
        if not isinstance(value["rationale"], str) or len(value["rationale"].strip()) < 12:
            raise PilotWorkflowError(
                "TIMING_RATIONALE_REQUIRED", f"{boundary} requires a specific rationale"
            )
        if not isinstance(value["evidence_status"], str) or value["evidence_status"] not in {
            "PRESENT",
            "MISSING",
            "INSUFFICIENT",
        }:
            raise PilotWorkflowError(
                "TIMING_FIELDS_INVALID", f"{boundary} evidence status is invalid"
            )
        reason = value["missing_evidence_reason"]
        if reason is not None and (not isinstance(reason, str) or not reason.strip()):
            raise PilotWorkflowError(
                "TIMING_FIELDS_INVALID", f"{boundary} missing-evidence reason is invalid"
            )
        if state == "OBSERVABLE":
            if not _finite_nonnegative(value["timestamp_uncertainty_s"]):
                raise PilotWorkflowError(
                    "TIMESTAMP_UNCERTAINTY_INVALID",
                    f"observable {boundary} requires finite nonnegative uncertainty",
                )
            if (
                not _finite_nonnegative(value["value_s"])
                or not isinstance(value["reference_camera"], str)
                or value["reference_camera"] not in {"front", "back"}
                or value["timestamp_basis"] != "camera_local_elapsed_seconds"
                or value["evidence_status"] != "PRESENT"
                or reason is not None
                or value["censoring_direction"] is not None
            ):
                raise PilotWorkflowError(
                    "TIMING_FIELDS_CONTRADICTORY", f"observable {boundary} fields conflict"
                )
        elif state == "CENSORED":
            valid_censor = (
                boundary == "T0_first_visible" and value["censoring_direction"] == "LEFT"
            ) or (boundary == "T4_tail_clearance" and value["censoring_direction"] == "RIGHT")
            if not valid_censor:
                raise PilotWorkflowError(
                    "LEFT_CENSOR_INVALID", f"censoring is not valid for {boundary}"
                )
            if (
                value["value_s"] is not None
                or value["reference_camera"] is not None
                or value["timestamp_basis"] is not None
                or value["timestamp_uncertainty_s"] is not None
                or value["evidence_status"] != "PRESENT"
                or reason is not None
            ):
                raise PilotWorkflowError(
                    "TIMING_FIELDS_CONTRADICTORY", f"censored {boundary} fields conflict"
                )
        else:
            if (
                value["value_s"] is not None
                or value["reference_camera"] is not None
                or value["timestamp_basis"] is not None
                or value["timestamp_uncertainty_s"] is not None
                or value["evidence_status"] == "PRESENT"
                or not isinstance(reason, str)
                or not reason.strip()
                or value["censoring_direction"] is not None
            ):
                raise PilotWorkflowError(
                    "TIMING_FIELDS_CONTRADICTORY", f"non-observable {boundary} needs reason only"
                )
        normalized[boundary] = value
    comparable = [
        normalized[name] for name in BOUNDARIES if normalized[name]["state"] == "OBSERVABLE"
    ]
    previous: dict[str, float] = {}
    for item in comparable:
        camera = item["reference_camera"]
        value = float(item["value_s"])
        if camera in previous and value < previous[camera]:
            raise PilotWorkflowError(
                "TIMING_CHRONOLOGY_CONTRADICTION", f"chronology decreases on {camera} clock"
            )
        previous[camera] = value
    return normalized


def build_unapproved_draft(
    *,
    session: TimingSession,
    observations: Mapping[str, Any],
    review_end_utc: str,
    monotonic_ended_s: float,
) -> dict[str, Any]:
    if session.utc_clock is not None:
        review_end_utc = session.utc_clock().astimezone(UTC).isoformat().replace("+00:00", "Z")
    if session.monotonic_clock is not None:
        monotonic_ended_s = session.monotonic_clock()
    end = _utc(review_end_utc, "review_end_utc")
    start = _utc(session.started_at_utc, "session started_at_utc")
    auth_end = _utc(session.grant.authorization_expires_at_utc, "authorization expiry")
    activation_end = _utc(session.grant.activation_expires_at_utc, "activation expiry")
    if end > auth_end or end > activation_end:
        raise PilotWorkflowError(
            "AUTHORIZATION_EXPIRED_DURING_SESSION",
            "authorization/activation expired before review ended",
        )
    if (
        end < start
        or not math.isfinite(monotonic_ended_s)
        or monotonic_ended_s < session.monotonic_started_s
    ):
        raise PilotWorkflowError("SESSION_TIME_INVALID", "review end precedes session start")
    normalized = _validate_observations(observations)
    duration = monotonic_ended_s - session.monotonic_started_s
    if duration <= 0:
        raise PilotWorkflowError(
            "SESSION_TIME_INVALID", "monotonic review duration must be positive"
        )
    draft: dict[str, Any] = {
        "schema_version": DRAFT_SCHEMA,
        "record_version": 1,
        "record_state": "HUMAN_REVIEW_COMPLETED_UNAPPROVED_PILOT",
        "ground_truth_eligible": False,
        "official_approval": False,
        "purpose": PURPOSE,
        "event_key": session.grant.event_key,
        "reviewer_id": session.grant.reviewer_id,
        "session_id": session.session_id,
        "authorization_sha256": session.grant.authorization_sha256,
        "activation_sha256": session.grant.activation_sha256,
        "workflow_release_sha256": session.grant.workflow_release_sha256,
        "provenance": {
            "source_inventory_sha256": session.grant.source_inventory_sha256,
            "source_media_sha256": {
                "front": session.grant.front_sha256,
                "back": session.grant.back_sha256,
            },
            "source_paths": {
                "front": session.grant.front_relative_path,
                "back": session.grant.back_relative_path,
            },
            "active_proposal_sha256": session.grant.proposal_sha256,
            "model_predictions_included": False,
            "candidate_boundaries_included": False,
        },
        "timing": {
            "review_started_at_utc": session.started_at_utc,
            "review_ended_at_utc": end.isoformat().replace("+00:00", "Z"),
            "duration_monotonic_s": duration,
            "duration_wall_clock_s": (end - start).total_seconds(),
        },
        "human_boundary_observations": normalized,
        "audit_history": [
            {
                "event": "UNAPPROVED_TIMING_PILOT_DRAFT_CREATED",
                "reviewer_id": session.grant.reviewer_id,
                "at_utc": end.isoformat().replace("+00:00", "Z"),
                "workflow_release_sha256": session.grant.workflow_release_sha256,
            }
        ],
        "approval_transition": "PROHIBITED_IN_TIMING_PILOT",
    }
    return _seal(draft)


def _validate_draft_record(record: Mapping[str, Any]) -> dict[str, Any]:
    expected_keys = {
        "schema_version",
        "record_version",
        "record_state",
        "ground_truth_eligible",
        "official_approval",
        "purpose",
        "event_key",
        "reviewer_id",
        "session_id",
        "authorization_sha256",
        "activation_sha256",
        "workflow_release_sha256",
        "provenance",
        "timing",
        "human_boundary_observations",
        "audit_history",
        "approval_transition",
        "record_sha256",
    }
    if not isinstance(record, Mapping) or set(record) != expected_keys:
        raise PilotWorkflowError(
            "DRAFT_INVALID", "draft fields do not match the fixed pilot schema"
        )
    if (
        record.get("record_state") != "HUMAN_REVIEW_COMPLETED_UNAPPROVED_PILOT"
        or record.get("official_approval") is not False
        or record.get("ground_truth_eligible") is not False
    ):
        raise PilotWorkflowError(
            "APPROVAL_TRANSITION_FORBIDDEN", "timing pilot cannot approve or promote records"
        )
    if record.get("approval_transition") != "PROHIBITED_IN_TIMING_PILOT":
        raise PilotWorkflowError(
            "APPROVAL_TRANSITION_FORBIDDEN", "approval transition is prohibited"
        )
    if (
        record.get("schema_version") != DRAFT_SCHEMA
        or record.get("record_version") != 1
        or record.get("purpose") != PURPOSE
    ):
        raise PilotWorkflowError("DRAFT_INVALID", "draft version or purpose is invalid")
    if not isinstance(record.get("event_key"), str) or not _EVENT_KEY.fullmatch(
        record["event_key"]
    ):
        raise PilotWorkflowError("DRAFT_INVALID", "draft event key is malformed")
    if not isinstance(record.get("reviewer_id"), str) or not record["reviewer_id"].strip():
        raise PilotWorkflowError("DRAFT_INVALID", "reviewer identity is required")
    if not isinstance(record.get("session_id"), str) or not re.fullmatch(
        r"session-[A-Za-z0-9_-]{1,80}", record["session_id"]
    ):
        raise PilotWorkflowError("DRAFT_INVALID", "session id is malformed")
    for name in ("authorization_sha256", "activation_sha256", "workflow_release_sha256"):
        _require_sha(record.get(name), name)
    provenance = record.get("provenance")
    if not isinstance(provenance, dict) or set(provenance) != {
        "source_inventory_sha256",
        "source_media_sha256",
        "source_paths",
        "active_proposal_sha256",
        "model_predictions_included",
        "candidate_boundaries_included",
    }:
        raise PilotWorkflowError(
            "DRAFT_INVALID", "provenance fields do not match the fixed pilot schema"
        )
    if (
        provenance.get("model_predictions_included") is not False
        or provenance.get("candidate_boundaries_included") is not False
    ):
        raise PilotWorkflowError("DRAFT_INVALID", "provenance must exclude model/candidate output")
    _require_sha(provenance.get("source_inventory_sha256"), "source inventory provenance")
    _require_sha(provenance.get("active_proposal_sha256"), "active proposal provenance")
    source_paths = provenance.get("source_paths")
    if (
        not isinstance(source_paths, dict)
        or set(source_paths) != {"front", "back"}
        or any(not isinstance(path, str) or not path for path in source_paths.values())
    ):
        raise PilotWorkflowError("DRAFT_INVALID", "source media paths are incomplete")
    media = provenance.get("source_media_sha256")
    if not isinstance(media, dict) or set(media) != {"front", "back"}:
        raise PilotWorkflowError("DRAFT_INVALID", "source media provenance is incomplete")
    for camera, digest in media.items():
        _require_sha(digest, f"{camera} media provenance")
    timing = record.get("timing")
    if not isinstance(timing, dict) or set(timing) != {
        "review_started_at_utc",
        "review_ended_at_utc",
        "duration_monotonic_s",
        "duration_wall_clock_s",
    }:
        raise PilotWorkflowError(
            "DRAFT_INVALID", "timing fields do not match the fixed pilot schema"
        )
    started = _utc(timing.get("review_started_at_utc"), "review_started_at_utc")
    ended = _utc(timing.get("review_ended_at_utc"), "review_ended_at_utc")
    if (
        ended < started
        or not _finite_nonnegative(timing.get("duration_monotonic_s"))
        or timing["duration_monotonic_s"] <= 0
        or not _finite_nonnegative(timing.get("duration_wall_clock_s"))
    ):
        raise PilotWorkflowError("DRAFT_INVALID", "timing values are invalid")
    _validate_observations(record.get("human_boundary_observations", {}))
    history = record.get("audit_history")
    if (
        not isinstance(history, list)
        or len(history) != 1
        or not isinstance(history[0], dict)
        or set(history[0]) != {"event", "reviewer_id", "at_utc", "workflow_release_sha256"}
        or history[0].get("event") != "UNAPPROVED_TIMING_PILOT_DRAFT_CREATED"
        or history[0].get("reviewer_id") != record.get("reviewer_id")
        or history[0].get("at_utc") != timing.get("review_ended_at_utc")
        or history[0].get("workflow_release_sha256") != record.get("workflow_release_sha256")
    ):
        raise PilotWorkflowError("DRAFT_INVALID", "audit history is required")
    _require_sha(history[0].get("workflow_release_sha256"), "audit release hash")
    _verify_record_seal(record, "draft", "DRAFT_TAMPERED")
    return dict(record)


def write_unapproved_draft(
    draft: Mapping[str, Any],
    *,
    repository_root: Path | str,
    preparation_only: bool = False,
    session: TimingSession | None = None,
) -> Path:
    root = Path(repository_root).expanduser().resolve()
    if preparation_only:
        _require_preparation_isolation(root, (root / OUTPUT_RELATIVE,))
    elif session is None:
        raise PilotWorkflowError(
            "SESSION_GRANT_REQUIRED", "a verified timing session grant is required to write"
        )
    if not isinstance(draft, Mapping):
        raise PilotWorkflowError("DRAFT_INVALID", "draft must be an object")
    if (
        draft.get("record_state") != "HUMAN_REVIEW_COMPLETED_UNAPPROVED_PILOT"
        or draft.get("official_approval") is not False
        or draft.get("ground_truth_eligible") is not False
        or draft.get("approval_transition") != "PROHIBITED_IN_TIMING_PILOT"
    ):
        raise PilotWorkflowError(
            "APPROVAL_TRANSITION_FORBIDDEN", "timing pilot cannot approve or promote records"
        )
    event_key = draft.get("event_key")
    session_id = draft.get("session_id")
    if not isinstance(event_key, str) or not _EVENT_KEY.fullmatch(event_key):
        raise PilotWorkflowError("DRAFT_INVALID", "draft event key is malformed")
    if not isinstance(session_id, str) or not re.fullmatch(
        r"session-[A-Za-z0-9_-]{1,80}", session_id
    ):
        raise PilotWorkflowError("DRAFT_INVALID", "draft session id is malformed")
    if session is not None:
        grant = session.grant
        if not preparation_only and session._capability is not _SESSION_CAPABILITY:
            raise PilotWorkflowError(
                "SESSION_GRANT_REQUIRED", "session was not issued by the verified session starter"
            )
        if (
            session.session_id != session_id
            or grant.event_key != event_key
            or grant.reviewer_id != draft.get("reviewer_id")
            or grant.authorization_sha256 != draft.get("authorization_sha256")
            or grant.activation_sha256 != draft.get("activation_sha256")
            or grant.workflow_release_sha256 != draft.get("workflow_release_sha256")
            or grant.source_inventory_sha256
            != draft.get("provenance", {}).get("source_inventory_sha256")
            or grant.proposal_sha256 != draft.get("provenance", {}).get("active_proposal_sha256")
            or grant.front_sha256
            != draft.get("provenance", {}).get("source_media_sha256", {}).get("front")
            or grant.back_sha256
            != draft.get("provenance", {}).get("source_media_sha256", {}).get("back")
        ):
            raise PilotWorkflowError(
                "SESSION_PROVENANCE_MISMATCH", "draft differs from the verified session grant"
            )
        current = (
            datetime.now(UTC)
            if not preparation_only
            else _utc(draft.get("timing", {}).get("review_ended_at_utc"), "review_ended_at_utc")
        )
        if current > _utc(
            grant.authorization_expires_at_utc, "authorization expiry"
        ) or current > _utc(grant.activation_expires_at_utc, "activation expiry"):
            raise PilotWorkflowError(
                "AUTHORIZATION_EXPIRED_DURING_SESSION",
                "authorization/activation expired before write",
            )
        ended = _utc(draft.get("timing", {}).get("review_ended_at_utc"), "review_ended_at_utc")
        if ended > _utc(grant.authorization_expires_at_utc, "authorization expiry") or ended > _utc(
            grant.activation_expires_at_utc, "activation expiry"
        ):
            raise PilotWorkflowError(
                "AUTHORIZATION_EXPIRED_DURING_SESSION", "authorization expired before write"
            )
        if root == _REPOSITORY_ROOT:
            if (
                _hash_file(grant.front_media_path) != grant.front_sha256
                or _hash_file(grant.back_media_path) != grant.back_sha256
            ):
                raise PilotWorkflowError(
                    "MEDIA_HASH_MISMATCH", "source media changed before draft write"
                )
        if not preparation_only:
            _revalidate_grant(session)
    output_root = root / OUTPUT_RELATIVE
    if output_root.is_symlink() or not output_root.resolve().is_relative_to(root):
        raise PilotWorkflowError(
            "OUTPUT_PATH_INVALID", "pilot output directory must remain beneath repository root"
        )
    event_component = event_key.replace("/", "__")
    destination = output_root / event_component / f"{session_id}.pilot.json"
    event_directory = output_root / event_component
    if event_directory.is_symlink() or destination.is_symlink():
        raise PilotWorkflowError("OUTPUT_PATH_INVALID", "pilot output symlinks are refused")
    if not destination.resolve().is_relative_to(output_root.resolve()):
        raise PilotWorkflowError("OUTPUT_PATH_INVALID", "draft output escapes the pilot directory")
    if destination.exists():
        try:
            existing = destination.read_bytes()
        except OSError as exc:
            raise PilotWorkflowError("DRAFT_WRITE_FAILED", str(exc)) from exc
        desired = canonical_json_bytes(dict(draft))
        if existing == desired:
            _validate_draft_record(draft)
            return destination
        raise PilotWorkflowError(
            "IDEMPOTENCY_CONFLICT", "session output already exists with different content"
        )
    validated = _validate_draft_record(draft)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".pilot-draft-", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_json_bytes(validated))
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, destination)
        temporary.unlink()
        return destination
    except FileExistsError as exc:
        desired = canonical_json_bytes(validated)
        if destination.is_file() and destination.read_bytes() == desired:
            temporary.unlink(missing_ok=True)
            return destination
        if destination.is_file():
            raise PilotWorkflowError(
                "IDEMPOTENCY_CONFLICT", "concurrent session output differs"
            ) from exc
        raise PilotWorkflowError("DRAFT_WRITE_FAILED", str(exc)) from exc
    except OSError as exc:
        raise PilotWorkflowError("DRAFT_WRITE_FAILED", str(exc)) from exc
    finally:
        temporary.unlink(missing_ok=True)


def _revalidate_grant(session: TimingSession) -> None:
    """Recheck all authorization and provenance bindings before output creation."""
    grant = session.grant
    root = grant.repository_root.resolve()
    release = verify_release_manifest(
        grant.release_manifest_path,
        expected_release_sha256=grant.workflow_release_sha256,
        repository_root=root,
    )
    allowlist = _load_allowlist(grant.allowlist_path)
    authorization = _parse_document(grant.authorization_path, "AUTHORIZATION_INVALID")
    auth_hash = validate_authorization(
        authorization,
        allowlisted_researchers=allowlist,
        release=release,
        event_key=grant.event_key,
        reviewer_id=grant.reviewer_id,
        now=datetime.now(UTC),
    )
    if auth_hash != grant.authorization_sha256:
        raise PilotWorkflowError("AUTHORIZATION_TAMPERED", "authorization changed during session")
    activation = _parse_document(grant.activation_path, "ACTIVATION_INVALID")
    activation_hash = validate_activation(
        activation,
        authorization=authorization,
        authorization_sha256=auth_hash,
        release=release,
        allowlisted_researchers=allowlist,
        now=datetime.now(UTC),
    )
    if activation_hash != grant.activation_sha256:
        raise PilotWorkflowError("ACTIVATION_TAMPERED", "activation changed during session")
    inventory_hash, media, _front, _back, proposal_hash, _queue_hash = _metadata_bindings(
        root=root,
        event_key=grant.event_key,
        inventory_path=grant.inventory_path,
        queue_path=grant.queue_path,
    )
    if inventory_hash != grant.source_inventory_sha256:
        raise PilotWorkflowError("INVENTORY_BINDING_MISMATCH", "inventory changed during session")
    if media != {"front": grant.front_sha256, "back": grant.back_sha256}:
        raise PilotWorkflowError("MEDIA_BINDING_MISMATCH", "media inventory changed during session")
    if proposal_hash != grant.proposal_sha256:
        raise PilotWorkflowError("PROPOSAL_BINDING_MISMATCH", "proposal changed during session")
    if (
        _hash_file(grant.front_media_path) != grant.front_sha256
        or _hash_file(grant.back_media_path) != grant.back_sha256
    ):
        raise PilotWorkflowError("MEDIA_HASH_MISMATCH", "media changed during session")


def create_release_artifacts(
    *,
    repository_root: Path | str,
    focused_test_command: str,
    focused_test_result: str,
    full_test_result: str,
    compile_result: str,
    lint_result: str,
) -> tuple[Path, Path, str]:
    """Create the deterministic inactive release manifest and inspection report."""
    root = Path(repository_root).expanduser().resolve()
    if root != _REPOSITORY_ROOT:
        raise PilotWorkflowError(
            "RELEASE_ROOT_INVALID", "release artifacts may only be built for this checkout"
        )
    statuses = (focused_test_result, full_test_result, compile_result, lint_result)
    if any(value != "passed" for value in statuses):
        raise PilotWorkflowError(
            "RELEASE_TESTS_NOT_PASSED", "tests, compile and lint must all pass"
        )
    entries: list[dict[str, str]] = []
    for relative, role in RELEASE_FILES:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise PilotWorkflowError(
                "RELEASE_FILE_MISSING", f"release input is missing: {relative}"
            )
        entries.append({"path": relative.as_posix(), "sha256": _hash_file(path), "role": role})
    manifest = {
        "schema_version": RELEASE_SCHEMA,
        "version": RELEASE_VERSION,
        "status": "PREPARED_NOT_ACTIVATED",
        "files": entries,
        "test_results": {
            "focused_command": focused_test_command,
            "focused_status": focused_test_result,
            "full_suite_status": full_test_result,
            "compile_status": compile_result,
            "lint_status": lint_result,
            "lint_scope": "pilot implementation and synthetic tests",
            "repository_wide_lint_status": "not_clean_outside_release_scope",
        },
        "intended_scope": {
            "operation": OPERATION,
            "purpose": PURPOSE,
            "evaluative": False,
            "activated_for_real_media": False,
        },
    }
    manifest_path = root / RELEASE_RELATIVE
    report_path = root / RELEASE_REPORT_RELATIVE
    _atomic_replace(manifest_path, canonical_json_bytes(manifest))
    release_hash = _sha256_bytes(manifest_path.read_bytes())
    report_lines = [
        "# Stage-2.1 Human Timing Pilot Workflow Release",
        "",
        f"Version: `{RELEASE_VERSION}`  ",
        f"Release manifest SHA-256: `{release_hash}`  ",
        "Status: **PREPARED — NOT ACTIVATED FOR REAL MEDIA**",
        "",
        "This release is a human-only, non-evaluative timing-pilot workflow. It is",
        "not the synthetic adjudication runner, does not approve or promote ground",
        "truth, and cannot authorize official evaluation or field activity. The",
        "record/hash envelope is unsigned; SHA-256 binds content but does not",
        "authenticate who authored it.",
        "",
        "No source media was opened, decoded, viewed, or processed to prepare this",
        "release. No activation authorization, genuine pilot record, ADJ-AUTH,",
        "EVAL-AUTH, or approval was created.",
        "",
        "## Bound files",
        "",
        *[f"- `{entry['path']}` — `{entry['sha256']}` ({entry['role']})" for entry in entries],
        "",
        "## Validation",
        "",
        f"- Focused tests: `{focused_test_result}` (`{focused_test_command}`).",
        f"- Full suite: `{full_test_result}`.",
        f"- Compile: `{compile_result}`.",
        f"- Targeted Ruff lint (pilot implementation and tests): `{lint_result}`.",
        "- Repository-wide Ruff check: not clean; reported violations outside this release scope.",
        "",
        "## Researcher action required",
        "",
        "Inspect the bound implementation, schema, tests, and this manifest. If",
        "later authorizing media use, provide a separate exact-scope, allowlisted",
        "researcher statement binding event keys, reviewers, source inventory,",
        "media/proposal hashes, permitted operations, output path, purpose, and",
        "this release hash. A second, separate activation statement must bind the",
        "authorization hash, release hash, scope hash, and validity window.",
        "Neither statement can approve labels or evaluation. Formal ADJ-AUTH remains",
        "separately required for Stage-2.1 adjudication.",
        "",
    ]
    report = "\n".join(report_lines)
    _atomic_replace(report_path, report.encode("utf-8"))
    verified = verify_release_manifest(
        manifest_path,
        expected_release_sha256=release_hash,
        repository_root=root,
    )
    return manifest_path, report_path, verified.sha256


def _atomic_replace(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
