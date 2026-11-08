"""Compatibility shim: the media-authorization contract lives in ``railway_detection.safety``.

The previous implementation in this module verified a record only when an entry point chose to call
it, and accepted a loose record (``revoked: "true"`` or a naive expiry slipped through). The
authority is now ``railway_detection.safety.media_guard`` and it is called from the lowest-level
openers, not from entry points. This module only re-exports the public names so that existing
imports keep resolving to the one implementation.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from railway_detection.safety.media_guard import (
    ALL_EVENTS_IN_DATASETS,
    AUTHORIZATION_CLASS,
    CANONICAL_ALLOWLIST_RELATIVE,
    CANONICAL_MEDIA_AUTH_RELATIVE,
    MEDIA_ACCESS_SCHEMA_VERSION,
    VALID_MEDIA_OPERATIONS,
    MediaAccessAuthorizationError,
    precheck_operation_authorized,
    require_media_authorization,
    verify_authorization_record,
)


def verify_media_access_authorization(
    repo_root: Path | str,
    *,
    operation: str,
    media_path: Path | str | None = None,
    event_id: str | None = None,
    now: datetime | None = None,
) -> dict:
    """Verify AUTH-MEDIA-ACCESS for ``operation`` (on ``media_path`` when one is given).

    Without a path only the record-level rules are checked (an entry-point pre-check); dataset,
    event, media-type and path-prefix scope are decided per concrete file at the opener.
    """
    return verify_authorization_record(
        Path(repo_root).resolve(),
        operation=operation,
        media_path=None if media_path is None else Path(media_path).resolve(),
        event_id=event_id,
        now=now,
    )


__all__ = [
    "ALL_EVENTS_IN_DATASETS",
    "AUTHORIZATION_CLASS",
    "CANONICAL_ALLOWLIST_RELATIVE",
    "CANONICAL_MEDIA_AUTH_RELATIVE",
    "MEDIA_ACCESS_SCHEMA_VERSION",
    "VALID_MEDIA_OPERATIONS",
    "MediaAccessAuthorizationError",
    "precheck_operation_authorized",
    "require_media_authorization",
    "verify_authorization_record",
    "verify_media_access_authorization",
]
