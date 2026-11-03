"""Operation-boundary authorization for raw railway media (Mission 10, WP10.2).

Every code path in this repository that opens, hashes, probes, decodes, extracts from or runs
inference on a raw media file calls :func:`require_media_authorization` *at the lowest level that
touches the bytes*, immediately before the open. A caller-level check is never sufficient: a CLI, a
script, a notebook or a library import all reach the same primitive and meet the same guard.

What the guard enforces
-----------------------
* A media-looking path (by suffix) whose real path lies inside this repository, or anywhere outside
  the operating-system temporary directory, needs a valid ``data/governance/AUTH-MEDIA-ACCESS.json``
  **read from disk on every call** (no cache, no caller flag, no environment switch).
* A media-looking path whose real path lies inside the system temporary directory and outside this
  repository is treated as synthetic test media and needs no authorization. Symbolic links are
  resolved first, so a link from a temporary directory to real media is still guarded.
* ``repo_root`` may point at a *synthetic* repository (tests); it is refused for any path that
  resolves inside the real repository, so a hand-made authorization in a temporary tree can never
  unlock real media.

The authorization record (``phase5-media-access-authorization/2``)
-------------------------------------------------------------------
Exact key set, in the recorded-statement style of ``evaluation.governance`` (unsigned,
tamper-evident
only): ``schema_version``, ``authorization_id``, ``authorization_class`` (must be
``AUTH-MEDIA-ACCESS``), ``status`` (``APPROVED``), ``authorized_by`` (on the authority allowlist),
``authorized_at_utc``, ``expires_at_utc``, ``revoked`` (strict ``False``),
``authorization_statement``,
``attestation`` (``RECORDED_RESEARCHER_STATEMENT``, ``signature: null``), ``recorded_by``,
``scope`` (``operations``, ``datasets``, ``events``, ``media_types``, ``purpose``),
``restrictions`` (``path_prefixes``), ``bindings`` (``protocol_document`` path + SHA-256, re-hashed
live) and ``record_sha256``.

Limitations (disclosed, not hidden): this is a software guard over this repository's code paths. It
is not an operating-system sandbox; a process can still read bytes by calling ``cp``/``cat`` or by
using a library this repository does not wrap. Hard links to media are not detected. The record is
tamper-evident, not tamper-proof (no signature infrastructure exists).
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MEDIA_ACCESS_SCHEMA_VERSION = "phase5-media-access-authorization/2"
AUTHORIZATION_CLASS = "AUTH-MEDIA-ACCESS"
CANONICAL_MEDIA_AUTH_RELATIVE = Path("data/governance/AUTH-MEDIA-ACCESS.json")
CANONICAL_ALLOWLIST_RELATIVE = Path("data/ground_truth/authorized_reviewers.json")
ATTESTATION_RECORDED_STATEMENT = "RECORDED_RESEARCHER_STATEMENT"
ALL_EVENTS_IN_DATASETS = "ALL_EVENTS_IN_DATASETS"

VIDEO_SUFFIXES = frozenset(
    {".mov", ".mp4", ".m4v", ".avi", ".mkv", ".webm", ".mts", ".mpg", ".mpeg"}
)
AUDIO_SUFFIXES = frozenset({".wav", ".mp3", ".flac", ".aac", ".ogg", ".m4a", ".opus", ".aiff"})
IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"})
MEDIA_SUFFIXES = VIDEO_SUFFIXES | AUDIO_SUFFIXES | IMAGE_SUFFIXES

VALID_MEDIA_OPERATIONS = frozenset(
    {
        "READ_RAW_MEDIA",
        "HASH_RAW_MEDIA",
        "MEDIA_PROBE",
        "INFERENCE",
        "FRAME_EXTRACTION",
        "AUDIO_EXTRACTION",
        "FEATURE_EXTRACTION",
        "REAL_REPLAY",
    }
)
VALID_MEDIA_TYPES = frozenset({"video", "audio", "image"})

#: The real repository root, derived from this file's location (never from the environment).
REAL_REPO_ROOT = Path(__file__).resolve().parents[3]

_AUTH_KEYS = frozenset(
    {
        "schema_version",
        "authorization_id",
        "authorization_class",
        "status",
        "authorized_by",
        "authorized_at_utc",
        "expires_at_utc",
        "revoked",
        "authorization_statement",
        "attestation",
        "recorded_by",
        "scope",
        "restrictions",
        "bindings",
        "record_sha256",
    }
)
_SCOPE_KEYS = frozenset({"operations", "datasets", "events", "media_types", "purpose"})
_SHA256 = re.compile(r"[0-9a-f]{64}")
_EVENT = re.compile(r"(train_events|no_train_events|engine_events)/[A-Za-z0-9_.\-]+")


class MediaAccessAuthorizationError(PermissionError):
    """Raised when an operation on raw media lacks a valid, on-disk authorization."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"[{code}] {detail}")


_OBSERVERS: list = []


def register_observer(callback) -> None:
    """Register ``callback(path, operation)`` to be told of every non-synthetic media check.

    Used by the test access guard so that an attempt stopped *here* (before any open) is still
    recorded -- otherwise a test that reaches real media would be classified as touching nothing.
    A callback may raise to veto the operation even when an authorization exists.
    """
    if callback not in _OBSERVERS:
        _OBSERVERS.append(callback)


def unregister_observer(callback) -> None:
    if callback in _OBSERVERS:
        _OBSERVERS.remove(callback)


def looks_like_media(path: Path | str) -> bool:
    return Path(path).suffix.lower() in MEDIA_SUFFIXES


def media_type_of(path: Path | str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in VIDEO_SUFFIXES:
        return "video"
    if suffix in AUDIO_SUFFIXES:
        return "audio"
    return "image"


def _real(path: Path | str) -> Path:
    return Path(path).expanduser().resolve()


def _inside(child: Path, parent: Path) -> bool:
    return child == parent or parent in child.parents


def _system_temp_dirs() -> tuple[Path, ...]:
    dirs = {_real(tempfile.gettempdir())}
    for candidate in ("/tmp", "/private/tmp", "/var/folders", "/private/var/folders"):
        p = Path(candidate)
        if p.exists():
            dirs.add(_real(p))
    return tuple(dirs)


def is_synthetic_location(path: Path | str) -> bool:
    """True only for a path whose real location is in the OS temp area and outside the repo."""
    real = _real(path)
    if _inside(real, REAL_REPO_ROOT):
        return False
    return any(_inside(real, tmp) for tmp in _system_temp_dirs())


def _canonical_sha256(record: dict[str, Any]) -> str:
    body = {k: v for k, v in record.items() if k != "record_sha256"}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} is not an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must carry a timezone")
    return parsed.astimezone(UTC)


def _string_list(value: Any, field: str, *, allowed: frozenset[str] | None = None) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a non-empty list")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field} entries must be non-empty strings")
        if allowed is not None and item not in allowed:
            raise ValueError(f"{field} entry {item!r} is not one of {sorted(allowed)}")
    if len(set(value)) != len(value):
        raise ValueError(f"{field} contains duplicates")
    return list(value)


def _dataset_of(real: Path, root: Path) -> str | None:
    """Dataset = first path component after ``data/raw`` (e.g. ``layer_b``)."""
    try:
        parts = real.relative_to(root / "data" / "raw").parts
    except ValueError:
        return None
    return parts[0] if len(parts) > 1 else None


def _event_of(real: Path) -> str | None:
    """A cohort-qualified event identity found in the path, if any."""
    posix = real.as_posix()
    match = _EVENT.search(posix)
    return match.group(0) if match else None


def verify_authorization_record(
    root: Path,
    *,
    operation: str,
    media_path: Path | None,
    event_id: str | None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Validate the on-disk record for one operation on one media path; return the payload.

    ``media_path=None`` is the *operation-level pre-check* used by entry points to fail fast: every
    record-level rule is enforced, but the path-dependent scope rules (dataset, event, media type,
    path prefix) cannot be decided and are skipped. It never authorizes a read; the boundary guard
    re-checks every concrete file.

    Raises :class:`MediaAccessAuthorizationError` on any problem. Reads the record, the authority
    allowlist and the bound protocol document from disk on every call.
    """
    now = now or datetime.now(UTC)
    if operation not in VALID_MEDIA_OPERATIONS:
        raise MediaAccessAuthorizationError(
            "INVALID_OPERATION_TYPE",
            f"{operation!r} is not a recognized media operation; one of "
            f"{sorted(VALID_MEDIA_OPERATIONS)}",
        )
    path = root / CANONICAL_MEDIA_AUTH_RELATIVE
    if not path.is_file():
        raise MediaAccessAuthorizationError(
            "AUTH_MEDIA_ACCESS_NOT_GRANTED",
            f"no recorded AUTH-MEDIA-ACCESS at {path}. Opening, hashing, probing, decoding, "
            "extracting from, or running inference on raw media is prohibited without it.",
        )
    try:
        payload = json.loads(path.read_bytes())
    except (OSError, ValueError) as exc:
        raise MediaAccessAuthorizationError(
            "AUTH_MEDIA_ACCESS_MALFORMED", f"cannot parse {path}: {exc}"
        ) from exc
    try:
        _validate_payload(
            root, payload, operation=operation, media_path=media_path, event_id=event_id, now=now
        )
    except ValueError as exc:
        raise MediaAccessAuthorizationError("AUTH_MEDIA_ACCESS_INVALID", str(exc)) from exc
    return payload


def _validate_payload(
    root: Path,
    payload: Any,
    *,
    operation: str,
    media_path: Path | None,
    event_id: str | None,
    now: datetime,
) -> None:
    if not isinstance(payload, dict):
        raise ValueError("the record must be a JSON object")
    if set(payload) - _AUTH_KEYS:
        raise ValueError(
            f"unexpected fields {sorted(set(payload) - _AUTH_KEYS)}; flags are never honored"
        )
    if _AUTH_KEYS - set(payload):
        raise ValueError(f"missing fields {sorted(_AUTH_KEYS - set(payload))}")
    if payload["schema_version"] != MEDIA_ACCESS_SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version {payload['schema_version']!r}")
    if payload["authorization_class"] != AUTHORIZATION_CLASS:
        raise ValueError(f"authorization_class must be {AUTHORIZATION_CLASS!r}")
    for key in ("authorization_id", "authorized_by", "authorization_statement"):
        if not isinstance(payload[key], str) or not payload[key].strip():
            raise ValueError(f"{key} is required")
    if payload["status"] != "APPROVED":
        raise ValueError(f"status is {payload['status']!r}; it must be 'APPROVED'")
    if payload["revoked"] is not False:
        raise ValueError("revoked must be the boolean false; any other value denies access")

    attestation = payload["attestation"]
    if (
        not isinstance(attestation, dict)
        or set(attestation) != {"type", "signature"}
        or attestation["type"] != ATTESTATION_RECORDED_STATEMENT
        or attestation["signature"] is not None
    ):
        raise ValueError(
            f"attestation must be exactly {{type: {ATTESTATION_RECORDED_STATEMENT}, "
            f"signature: null}}"
        )
    recorded_by = payload["recorded_by"]
    if (
        not isinstance(recorded_by, dict)
        or set(recorded_by) - {"kind", "identity", "transcription_source"}
        or recorded_by.get("kind") not in {"researcher", "agent_transcription"}
        or not isinstance(recorded_by.get("identity"), str)
        or not recorded_by["identity"].strip()
    ):
        raise ValueError(
            "recorded_by must name a kind (researcher|agent_transcription) and identity"
        )
    if recorded_by["kind"] == "agent_transcription" and not (
        isinstance(recorded_by.get("transcription_source"), str)
        and recorded_by["transcription_source"].strip()
    ):
        raise ValueError("agent_transcription requires transcription_source")

    if payload["record_sha256"] != _canonical_sha256(payload):
        raise ValueError("record_sha256 does not match the record content")

    issued = _utc(payload["authorized_at_utc"], "authorized_at_utc")
    expires = _utc(payload["expires_at_utc"], "expires_at_utc")
    if issued > now:
        raise ValueError("authorized_at_utc is in the future")
    if expires <= issued:
        raise ValueError("expires_at_utc must be after authorized_at_utc")
    if now >= expires:
        raise ValueError(f"the authorization expired at {expires.isoformat()}")

    from railway_detection.annotation.promotion_gate import load_authorized_reviewers

    try:
        allowlist = load_authorized_reviewers(root / CANONICAL_ALLOWLIST_RELATIVE)
    except Exception as exc:
        raise ValueError(f"authority allowlist unavailable: {exc}") from exc
    if payload["authorized_by"] not in allowlist:
        raise ValueError(f"signer {payload['authorized_by']!r} is not on the authority allowlist")

    scope = payload["scope"]
    if not isinstance(scope, dict) or set(scope) != _SCOPE_KEYS:
        raise ValueError(f"scope must declare exactly {sorted(_SCOPE_KEYS)}")
    operations = _string_list(
        scope["operations"], "scope.operations", allowed=VALID_MEDIA_OPERATIONS
    )
    datasets = _string_list(scope["datasets"], "scope.datasets")
    events = _string_list(scope["events"], "scope.events")
    media_types = _string_list(scope["media_types"], "scope.media_types", allowed=VALID_MEDIA_TYPES)
    if not isinstance(scope["purpose"], str) or len(scope["purpose"].strip()) < 10:
        raise ValueError("scope.purpose must state a specific purpose")
    if events != [ALL_EVENTS_IN_DATASETS]:
        for ev in events:
            if not _EVENT.fullmatch(ev):
                raise ValueError(
                    f"scope.events entry {ev!r} must be cohort-qualified or "
                    f"{ALL_EVENTS_IN_DATASETS}"
                )

    if operation not in operations:
        raise ValueError(f"operation {operation!r} is not authorized; authorized {operations}")
    restrictions = payload["restrictions"]
    if not isinstance(restrictions, dict) or set(restrictions) != {"path_prefixes"}:
        raise ValueError("restrictions must declare exactly path_prefixes")
    prefixes = restrictions["path_prefixes"]
    if not isinstance(prefixes, list) or any(not isinstance(p, str) or not p for p in prefixes):
        raise ValueError("restrictions.path_prefixes must be a list of non-empty strings")

    if media_path is not None:
        _check_path_scope(root, media_path, event_id, events, datasets, media_types, prefixes)
    _check_bindings(root, payload["bindings"])


def _check_path_scope(
    root: Path,
    media_path: Path,
    event_id: str | None,
    events: list[str],
    datasets: list[str],
    media_types: list[str],
    prefixes: list[str],
) -> None:
    if media_type_of(media_path) not in media_types:
        raise ValueError(f"media type {media_type_of(media_path)!r} is not authorized")

    real = _real(media_path)
    dataset = _dataset_of(real, root.resolve())
    if dataset is None:
        raise ValueError(
            "the media path is not under data/raw/<dataset>/ so its dataset cannot be scoped"
        )
    if dataset not in datasets:
        raise ValueError(f"dataset {dataset!r} is outside the authorized datasets {datasets}")
    path_event = _event_of(real)
    if event_id is not None and path_event is not None and event_id != path_event:
        raise ValueError(f"declared event {event_id!r} contradicts the path event {path_event!r}")
    effective_event = event_id or path_event
    if events != [ALL_EVENTS_IN_DATASETS]:
        if effective_event is None:
            raise ValueError(
                "the event of this media file cannot be determined; scope is per-event"
            )
        if effective_event not in events:
            raise ValueError(f"event {effective_event!r} is outside the authorized events")

    if prefixes:
        rel = real.relative_to(root.resolve()).as_posix()
        if not any(rel.startswith(p) for p in prefixes):
            raise ValueError(f"{rel!r} is outside the restricted path prefixes {prefixes}")


def _check_bindings(root: Path, bindings: Any) -> None:
    if not isinstance(bindings, dict) or set(bindings) != {"protocol_document"}:
        raise ValueError("bindings must declare exactly protocol_document")
    doc = bindings["protocol_document"]
    if not isinstance(doc, dict) or set(doc) != {"path", "sha256"}:
        raise ValueError("bindings.protocol_document must declare path and sha256")
    if (
        not isinstance(doc["path"], str)
        or not isinstance(doc["sha256"], str)
        or not _SHA256.fullmatch(doc["sha256"])
    ):
        raise ValueError("bindings.protocol_document needs a repo-relative path and a SHA-256")
    doc_path = (root / doc["path"]).resolve()
    if root.resolve() not in doc_path.parents or not doc_path.is_file():
        raise ValueError("the bound protocol document is missing or outside the repository")
    if hashlib.sha256(doc_path.read_bytes()).hexdigest() != doc["sha256"]:
        raise ValueError("the bound protocol document changed after the authorization was recorded")


def precheck_operation_authorized(operation: str, *, repo_root: Path | str | None = None) -> None:
    """Fail fast at an entry point: raise unless a valid record permits ``operation`` at all.

    This is a convenience for early, readable failures. It does not replace, and no code relies on,
    the per-file :func:`require_media_authorization` calls at the openers.
    """
    root = REAL_REPO_ROOT if repo_root is None else _real(repo_root)
    verify_authorization_record(root, operation=operation, media_path=None, event_id=None)


def require_media_authorization(
    path: Path | str,
    operation: str,
    *,
    event_id: str | None = None,
    repo_root: Path | str | None = None,
) -> None:
    """Raise unless ``operation`` on the media at ``path`` is currently authorized.

    Call this immediately before opening the file. A non-media suffix is a no-op, so generic
    helpers (JSON hashing) can call it unconditionally.
    """
    if not looks_like_media(path):
        return
    if is_synthetic_location(path):
        return
    real = _real(path)
    if not _inside(real, REAL_REPO_ROOT) and not Path(path).exists():
        return  # outside the repository and absent: there are no bytes to protect
    for observer in tuple(_OBSERVERS):
        observer(real, operation)
    root = REAL_REPO_ROOT
    if repo_root is not None:
        candidate = _real(repo_root)
        if candidate != REAL_REPO_ROOT:
            if _inside(real, REAL_REPO_ROOT):
                raise MediaAccessAuthorizationError(
                    "AUTH_MEDIA_ACCESS_ROOT_OVERRIDE_REFUSED",
                    "repo_root may not redirect authorization for media inside the real repository",
                )
            root = candidate
    verify_authorization_record(root, operation=operation, media_path=real, event_id=event_id)


__all__ = [
    "ALL_EVENTS_IN_DATASETS",
    "AUTHORIZATION_CLASS",
    "CANONICAL_MEDIA_AUTH_RELATIVE",
    "MEDIA_ACCESS_SCHEMA_VERSION",
    "MEDIA_SUFFIXES",
    "MediaAccessAuthorizationError",
    "VALID_MEDIA_OPERATIONS",
    "is_synthetic_location",
    "looks_like_media",
    "precheck_operation_authorized",
    "register_observer",
    "require_media_authorization",
    "unregister_observer",
    "verify_authorization_record",
]
