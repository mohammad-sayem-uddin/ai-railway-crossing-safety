"""Read-only reconciliation of legacy review records against Stage 2.1.

This module answers one question per legacy record: *what exactly stands
between this file and a valid Stage-2.1 promotion record?* It is analysis
only. It never writes into ``data/ground_truth``, never migrates a record,
never changes a label, and never consults model output.

Why there is deliberately no migration path
-------------------------------------------
A Stage-2.1 record must carry reviewer-observed full-file media hashes, a
timed review session, a model-independence attestation, a per-boundary
four-state adjudication and an append-only adjudication history. A legacy
``6.0.0`` record carries none of these. Synthesizing them from the legacy
fields would assert that a review session happened that the evidence does not
show, which is exactly the fabrication the Stage-2.1 schema exists to prevent.
Compatibility is therefore limited to *classification and traceability*.

The derived report is additive: it is written only to a caller-chosen path
outside the review tree, and the originals are re-hashed to prove they were
not changed.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from railway_detection.annotation.stage2_1_schema import (
    REVIEWER_ID_BLOCKLIST,
    STAGE_2_1_SCHEMA_VERSION,
    Stage21ReviewRecord,
)

REPORT_SCHEMA = "legacy-review-reconciliation/1"

# Stage-2.1 top-level fields a legacy record would have to supply truthfully.
_STAGE21_REQUIRED = tuple(
    field.name
    for field in dataclasses.fields(Stage21ReviewRecord)
    if field.default is dataclasses.MISSING
)

_NOT_MIGRATABLE = (
    "Stage-2.1 requires evidence a legacy record does not contain "
    "(reviewer-observed media hashes, timed review session, model-independence "
    "attestation, per-boundary states, append-only history). Deriving them would "
    "fabricate review evidence."
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _active_proposals(proposals_dir: Path) -> dict[tuple[str, str], tuple[int, Path]]:
    """Highest ``_proposal[_vN].json`` per (cohort, event)."""
    active: dict[tuple[str, str], tuple[int, Path]] = {}
    for path in sorted(proposals_dir.rglob("*_proposal*.json")):
        stem = path.stem
        event_id, sep, version = stem.partition("_proposal")
        number = 1
        if sep and version.startswith("_v") and version[2:].isdigit():
            number = int(version[2:])
        elif version:
            continue
        key = (path.parent.name, event_id)
        if key not in active or number > active[key][0]:
            active[key] = (number, path)
    return active


def reconcile_legacy_reviews(repository_root: Path | str) -> dict[str, Any]:
    """Classify every review record under ``data/ground_truth/reviews``."""
    root = Path(repository_root).resolve()
    reviews_dir = root / "data/ground_truth/reviews"
    proposals_dir = root / "data/ground_truth/proposals"
    active = _active_proposals(proposals_dir) if proposals_dir.is_dir() else {}

    loaded: list[tuple[Path, dict[str, Any], str]] = []
    for path in sorted(reviews_dir.rglob("*_review.json")) if reviews_dir.is_dir() else []:
        raw = path.read_bytes()
        value = json.loads(raw)
        record = value if isinstance(value, dict) else {}
        loaded.append((path, record, hashlib.sha256(raw).hexdigest()))

    timestamps = Counter(
        (record.get("reviewer_metadata") or {}).get("review_date_utc") for _p, record, _h in loaded
    )

    entries: list[dict[str, Any]] = []
    for path, record, digest in loaded:
        cohort = path.parent.name
        event_id = str(record.get("event_id", "<unknown>"))
        meta = record.get("reviewer_metadata") or {}
        reviewer = str(meta.get("reviewer_id", record.get("reviewer_id", "<none>")))
        stamp = meta.get("review_date_utc")
        reference = record.get("proposal_reference") or {}
        recorded_sha = reference.get("proposal_sha256")
        referenced_path = root / str(reference.get("proposal_file", ""))
        referenced_exists = referenced_path.is_file()
        referenced_sha = _sha256(referenced_path) if referenced_exists else None
        active_entry = active.get((cohort, event_id))
        active_sha = _sha256(active_entry[1]) if active_entry else None
        reasons: list[str] = []
        if record.get("schema_version") != STAGE_2_1_SCHEMA_VERSION:
            reasons.append(f"schema_version {record.get('schema_version')!r} is not Stage 2.1")
        if reviewer.strip().lower() in REVIEWER_ID_BLOCKLIST:
            reasons.append(f"reviewer_id {reviewer!r} is blocklisted (not an individual identity)")
        if stamp is not None and timestamps[stamp] > 1:
            reasons.append(
                f"review timestamp {stamp} is shared by {timestamps[stamp]} records "
                "(not consistent with per-event human review)"
            )
        if active_sha is not None and recorded_sha != active_sha:
            reasons.append("proposal_sha256 does not match the currently active proposal")
        if not referenced_exists:
            reasons.append("referenced proposal file is absent")
        missing = [name for name in _STAGE21_REQUIRED if name not in record]
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": digest,
                "cohort": cohort,
                "event_id": event_id,
                "schema_version": record.get("schema_version"),
                "adjudication_status": record.get("adjudication_status"),
                "reviewer_id": reviewer,
                "review_date_utc": stamp,
                "records_sharing_review_timestamp": timestamps[stamp] if stamp else 0,
                "recorded_proposal_sha256": recorded_sha,
                "active_proposal": (
                    active_entry[1].relative_to(root).as_posix() if active_entry else None
                ),
                "active_proposal_sha256": active_sha,
                "recorded_proposal_matches_referenced_file": (
                    recorded_sha == referenced_sha if referenced_sha is not None else None
                ),
                "recorded_proposal_matches_active": (
                    recorded_sha == active_sha if active_sha is not None else None
                ),
                "stage21_fields_missing": missing,
                "accepted_by_ground_truth_loader": False,
                "migratable_to_stage21": False,
                "migration_blocker": _NOT_MIGRATABLE,
                "findings": reasons,
            }
        )

    summary = {
        "record_count": len(entries),
        "schema_versions": dict(Counter(str(e["schema_version"]) for e in entries)),
        "reviewer_ids": dict(Counter(e["reviewer_id"] for e in entries)),
        "blocklisted_reviewer_count": sum(
            1 for e in entries if e["reviewer_id"].strip().lower() in REVIEWER_ID_BLOCKLIST
        ),
        "distinct_review_timestamps": len({e["review_date_utc"] for e in entries}),
        "proposal_hash_stale_count": sum(
            1 for e in entries if e["recorded_proposal_matches_active"] is False
        ),
        "stage21_record_count": sum(
            1 for e in entries if e["schema_version"] == STAGE_2_1_SCHEMA_VERSION
        ),
        "migratable_count": 0,
    }
    return {
        "schema_version": REPORT_SCHEMA,
        "purpose": (
            "Additive, read-only classification of legacy review records. Not an approval, "
            "invalidation or migration."
        ),
        "stage21_required_fields": list(_STAGE21_REQUIRED),
        "summary": summary,
        "records": entries,
    }


def write_reconciliation_report(
    repository_root: Path | str, output_path: Path | str
) -> dict[str, Any]:
    """Write the report outside the review/proposal trees and prove no original changed."""
    root = Path(repository_root).resolve()
    destination = Path(output_path).resolve()
    for protected in (root / "data/ground_truth",):
        if destination == protected or protected in destination.parents:
            raise ValueError(f"refusing to write inside protected path {protected}")
    before = reconcile_legacy_reviews(root)
    hashes_before = {e["path"]: e["sha256"] for e in before["records"]}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(before, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    hashes_after = {e["path"]: e["sha256"] for e in reconcile_legacy_reviews(root)["records"]}
    if hashes_after != hashes_before:
        raise RuntimeError("original review records changed during reconciliation")
    return before
