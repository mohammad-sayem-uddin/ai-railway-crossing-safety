"""Verification of legacy-review invalidation notices (LEG-EXEC outputs).

The sibling notice ``<cohort>/<event>_review.INVALIDATION_NOTICE.json`` is the applied,
non-destructive marker that a legacy review record is invalid. Loaders and gates used to
refuse *any* JSON under the reviews tree that was not a ``*_review.json`` record, so writing
the notices would have made every later load fail closed. This module lets them recognize a
notice -- only when it is verifiably about a real, unchanged, **legacy-schema** record:

* the notice parses and has the documented type and disposition;
* its sibling record exists in the same directory and its *current* SHA-256 equals the hash
  the notice recorded (an edited record is no longer the one that was invalidated);
* the sibling's ``schema_version`` is not Stage 2.1 -- a notice can never invalidate, hide or
  excuse a Stage-2.1 record.

Excusing a legacy record means it is no longer reported as a pending problem; it is never
promoted, migrated or treated as ground truth.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from railway_detection.annotation.stage2_1_schema import STAGE_2_1_SCHEMA_VERSION

NOTICE_INFIX = ".INVALIDATION_NOTICE.json"
NOTICE_TYPE = "LEGACY_REVIEW_INVALIDATION_NOTICE"


@dataclass(frozen=True)
class NoticeVerification:
    notice: str  # path relative to the reviews dir
    record: str  # sibling record, relative to the reviews dir
    valid: bool
    problem: str | None = None


def is_notice_path(path: Path) -> bool:
    return path.name.endswith(NOTICE_INFIX)


def verify_invalidation_notice(notice_path: Path, reviews_dir: Path) -> NoticeVerification:
    relative_notice = notice_path.relative_to(reviews_dir).as_posix()
    record_path = notice_path.with_name(notice_path.name.replace(NOTICE_INFIX, ".json"))
    relative_record = record_path.relative_to(reviews_dir).as_posix()

    def bad(problem: str) -> NoticeVerification:
        return NoticeVerification(relative_notice, relative_record, False, problem)

    try:
        notice = json.loads(notice_path.read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
        return bad(f"unreadable notice: {exc}")
    if not isinstance(notice, dict):
        return bad("notice is not a JSON object")
    if notice.get("notice_type") != NOTICE_TYPE or notice.get("disposition") != "INVALIDATED":
        return bad("not a legacy-review invalidation notice")
    if not record_path.is_file():
        return bad("the record the notice describes is missing")
    applies_to = str(notice.get("applies_to_file", ""))
    if not applies_to.endswith(relative_record):
        return bad(f"applies_to_file {applies_to!r} does not name the sibling {relative_record!r}")
    raw = record_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != notice.get("applies_to_file_sha256_at_notice_time"):
        return bad("the record changed after the notice was written")
    try:
        record = json.loads(raw)
    except json.JSONDecodeError:
        record = {}
    if isinstance(record, dict) and record.get("schema_version") == STAGE_2_1_SCHEMA_VERSION:
        return bad("a notice cannot invalidate or excuse a Stage-2.1 record")
    return NoticeVerification(relative_notice, relative_record, True)


def scan_notices(reviews_dir: Path) -> list[NoticeVerification]:
    if not reviews_dir.is_dir():
        return []
    return [
        verify_invalidation_notice(path, reviews_dir)
        for path in sorted(reviews_dir.rglob(f"*{NOTICE_INFIX}"))
    ]


def excused_legacy_records(reviews_dir: Path) -> dict[str, str]:
    """Verified ``record -> notice`` pairs (both relative to the reviews dir)."""
    return {n.record: n.notice for n in scan_notices(reviews_dir) if n.valid}


def invalid_notices(reviews_dir: Path) -> list[NoticeVerification]:
    return [n for n in scan_notices(reviews_dir) if not n.valid]
