"""Typed, hash-bound contracts for Phase 12 replay inputs.

The manifest format is an engineering interface, not a researcher-approved
event split or ground-truth authorization. Synthetic fixtures must be labelled
``synthetic`` and can never satisfy official readiness.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any
from railway_detection.safety.media_guard import require_media_authorization


class EvidenceClassification(StrEnum):
    SYNTHETIC = "synthetic"
    REAL = "real"


class EvaluationInputError(ValueError):
    """Invalid, missing, or hash-mismatched evaluation input."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "detail": self.detail}


@dataclass(frozen=True)
class EvaluationEventInput:
    event_id: str
    cohort: str
    split_role: str
    source_path: Path
    source_sha256: str
    source_payload: dict[str, Any]


@dataclass(frozen=True)
class EvaluationInputSet:
    manifest_path: Path
    manifest_sha256: str
    evidence_classification: EvidenceClassification
    partitions: dict[str, tuple[str, ...]]
    events: tuple[EvaluationEventInput, ...]
    camera_scope_by_event: dict[str, str] = field(default_factory=dict)
    accepted_sync_events: frozenset[str] = frozenset()

    @property
    def by_event_id(self) -> dict[str, EvaluationEventInput]:
        return {item.event_id: item for item in self.events}

    @property
    def source_fingerprints(self) -> dict[str, str]:
        return {item.event_id: item.source_sha256 for item in self.events}


def sha256_file(path: Path) -> str:
    require_media_authorization(path, "HASH_RAW_MEDIA")
    digest = hashlib.sha256()
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        with os.fdopen(os.open(path, flags), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise EvaluationInputError("INPUT_MISSING", f"cannot read {path}: {exc}") from exc
    return digest.hexdigest()


def _read_source_bytes_and_hash(path: Path) -> tuple[bytes, str]:
    """Read and hash one descriptor-backed snapshot of a source file."""
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        with os.fdopen(os.open(path, flags), "rb") as handle:
            content = handle.read()
    except OSError as exc:
        raise EvaluationInputError("INPUT_MISSING", f"cannot read {path}: {exc}") from exc
    return content, hashlib.sha256(content).hexdigest()


def load_evaluation_input_manifest(
    manifest_path: Path | str,
    *,
    verify_sources: bool = True,
) -> EvaluationInputSet:
    """Load a deterministic cohort manifest.

    ``verify_sources`` is deliberately explicit.  Internal synthetic execution
    verifies and loads JSON event payloads.  The official readiness gate passes
    ``False`` so it can validate manifest structure, declared hashes, and safe
    paths without opening source media or treating a media file as JSON.
    """
    path = Path(manifest_path).resolve()
    if not path.is_file():
        raise EvaluationInputError("MANIFEST_MISSING", f"manifest does not exist: {path}")
    try:
        raw_bytes = path.read_bytes()
        manifest = json.loads(raw_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationInputError("MANIFEST_INVALID", f"cannot parse {path}: {exc}") from exc
    if not isinstance(manifest, dict):
        raise EvaluationInputError("MANIFEST_INVALID", "manifest root must be an object")
    if manifest.get("schema_version") != "phase12-evaluation-inputs/1":
        raise EvaluationInputError("MANIFEST_SCHEMA_INVALID", "unsupported schema_version")
    try:
        classification = EvidenceClassification(manifest["evidence_classification"])
    except (KeyError, ValueError, TypeError) as exc:
        raise EvaluationInputError(
            "EVIDENCE_CLASSIFICATION_INVALID",
            "evidence_classification must be 'synthetic' or 'real'",
        ) from exc

    raw_partitions = manifest.get("partitions")
    if not isinstance(raw_partitions, dict) or set(raw_partitions) != {"train", "val", "test"}:
        raise EvaluationInputError(
            "SPLIT_INVALID", "partitions must contain exactly train, val, and test"
        )
    partitions: dict[str, tuple[str, ...]] = {}
    seen_roles: dict[str, str] = {}
    for role in ("train", "val", "test"):
        event_ids = raw_partitions[role]
        if not isinstance(event_ids, list) or not event_ids:
            raise EvaluationInputError("SPLIT_INVALID", f"{role} must be a nonempty list")
        if any(not isinstance(event_id, str) or not event_id.strip() for event_id in event_ids):
            raise EvaluationInputError("SPLIT_INVALID", f"{role} contains an invalid event ID")
        if len(event_ids) != len(set(event_ids)):
            raise EvaluationInputError("SPLIT_DUPLICATE_EVENT", f"duplicate event in {role}")
        for event_id in event_ids:
            previous = seen_roles.get(event_id)
            if previous is not None:
                raise EvaluationInputError(
                    "SPLIT_LEAKAGE", f"event {event_id!r} appears in {previous} and {role}"
                )
            seen_roles[event_id] = role
        partitions[role] = tuple(event_ids)

    raw_events = manifest.get("events")
    if not isinstance(raw_events, list) or not raw_events:
        raise EvaluationInputError("EVENTS_MISSING", "events must be a nonempty list")
    events: list[EvaluationEventInput] = []
    seen_event_ids: set[str] = set()
    manifest_root = path.parent
    for index, record in enumerate(raw_events):
        if not isinstance(record, dict):
            raise EvaluationInputError("EVENT_RECORD_INVALID", f"events[{index}] must be an object")
        event_id = record.get("event_id")
        cohort = record.get("cohort")
        role = record.get("split_role")
        source_rel = record.get("source_path")
        expected_hash = record.get("source_sha256")
        if not isinstance(event_id, str) or not event_id.strip() or event_id != event_id.strip():
            raise EvaluationInputError(
                "EVENT_RECORD_INVALID", f"events[{index}] has invalid event_id"
            )
        if event_id in seen_event_ids:
            raise EvaluationInputError("DUPLICATE_EVENT_ID", f"duplicate event_id {event_id!r}")
        seen_event_ids.add(event_id)
        if not isinstance(cohort, str) or not cohort.strip():
            raise EvaluationInputError("EVENT_RECORD_INVALID", f"{event_id}: cohort is required")
        if role not in partitions or event_id not in partitions[role]:
            raise EvaluationInputError(
                "EVENT_SPLIT_MISMATCH", f"{event_id}: record split_role is absent from partitions"
            )
        if not isinstance(source_rel, str) or not source_rel.strip():
            raise EvaluationInputError("INPUT_MISSING", f"{event_id}: source_path is required")
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            raise EvaluationInputError("SOURCE_HASH_INVALID", f"{event_id}: invalid SHA-256")
        source_rel_path = Path(source_rel)
        if source_rel_path.is_absolute():
            raise EvaluationInputError(
                "SOURCE_PATH_AMBIGUOUS", f"{event_id}: source_path must be relative"
            )
        source_declared_path = manifest_root / source_rel_path
        source_path = source_declared_path.resolve()
        if not source_path.is_relative_to(manifest_root):
            raise EvaluationInputError(
                "SOURCE_PATH_ESCAPE", f"{event_id}: path escapes manifest root"
            )
        # Do not allow a manifest to hide identity changes behind symlinks.
        # This is checked even in metadata-only mode using lstat-like path
        # metadata; no source bytes are opened by the official gate.
        relative_parts = source_rel_path.parts
        cursor = manifest_root
        for part in relative_parts[:-1]:
            cursor = cursor / part
            if cursor.is_symlink():
                raise EvaluationInputError(
                    "SOURCE_SYMLINK_UNEXPECTED", f"{event_id}: symlinked source directory"
                )
        if source_path.is_symlink() or source_declared_path.is_symlink():
            raise EvaluationInputError(
                "SOURCE_SYMLINK_UNEXPECTED", f"{event_id}: source path must not be a symlink"
            )
        if any(item.source_path == source_path for item in events):
            raise EvaluationInputError(
                "DUPLICATE_SOURCE_IDENTITY",
                f"{event_id}: source path is already bound to another event",
            )
        if verify_sources:
            if not source_path.is_file():
                raise EvaluationInputError("INPUT_MISSING", f"{event_id}: source does not exist")
            source_bytes, actual_hash = _read_source_bytes_and_hash(source_path)
            if actual_hash != expected_hash:
                raise EvaluationInputError(
                    "SOURCE_HASH_MISMATCH",
                    f"{event_id}: expected {expected_hash}, got {actual_hash}",
                )
            try:
                payload = json.loads(source_bytes.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise EvaluationInputError(
                    "EVENT_INPUT_INVALID", f"{event_id}: source must be valid JSON: {exc}"
                ) from exc
            if not isinstance(payload, dict):
                raise EvaluationInputError(
                    "EVENT_INPUT_INVALID", f"{event_id}: source root must be object"
                )
            actual_hash = expected_hash
        else:
            # The declared digest is retained as provenance.  Computing it here
            # would violate the gate's metadata/schema-only media boundary.
            actual_hash = expected_hash
            payload = {}
        events.append(
            EvaluationEventInput(
                event_id=event_id,
                cohort=cohort,
                split_role=role,
                source_path=source_path,
                source_sha256=actual_hash,
                source_payload=payload,
            )
        )
    if seen_event_ids != set(seen_roles):
        missing = sorted(set(seen_roles) - seen_event_ids)
        extra = sorted(seen_event_ids - set(seen_roles))
        raise EvaluationInputError(
            "EVENT_SPLIT_MISMATCH",
            f"manifest/partition IDs differ; missing={missing}, extra={extra}",
        )
    raw_camera_scope = manifest.get("camera_scope_by_event", {})
    if not isinstance(raw_camera_scope, dict):
        raise EvaluationInputError(
            "CAMERA_SCOPE_INVALID", "camera_scope_by_event must be an object"
        )
    if any(
        not isinstance(event_id, str) or not isinstance(value, str)
        for event_id, value in raw_camera_scope.items()
    ):
        raise EvaluationInputError(
            "CAMERA_SCOPE_INVALID", "camera_scope_by_event keys and values must be strings"
        )
    camera_scope = {
        event_id: value for event_id, value in raw_camera_scope.items()
    }
    if camera_scope and set(camera_scope) != set(seen_roles):
        raise EvaluationInputError(
            "CAMERA_SCOPE_INVALID", "camera_scope_by_event must cover every event when supplied"
        )
    raw_sync = manifest.get("accepted_sync_events", [])
    if not isinstance(raw_sync, list) or any(
        not isinstance(event_id, str) for event_id in raw_sync
    ):
        raise EvaluationInputError("SYNC_SCOPE_INVALID", "accepted_sync_events must be a list")
    if not set(raw_sync).issubset(set(seen_roles)):
        raise EvaluationInputError("SYNC_SCOPE_INVALID", "accepted sync event is not in manifest")
    return EvaluationInputSet(
        manifest_path=path,
        manifest_sha256=hashlib.sha256(raw_bytes).hexdigest(),
        evidence_classification=classification,
        partitions=partitions,
        events=tuple(sorted(events, key=lambda item: item.event_id)),
        camera_scope_by_event=camera_scope,
        accepted_sync_events=frozenset(raw_sync),
    )