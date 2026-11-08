"""Build the hash-bound Phase 12 input manifest from the researcher's decisions.

The manifest is derived, never authored: its split and camera scope are copied
from the verified decision artifacts, and each event source (a JSON inference
output, never source media) is hashed from disk. The builder refuses when the
decisions are missing or fail verification, when the supplied events differ
from the decided split, and when the destination already exists.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from railway_detection.evaluation import governance
from railway_detection.evaluation.input_contracts import (
    EvaluationInputError,
    load_evaluation_input_manifest,
    sha256_file,
)


@dataclass(frozen=True)
class EventSourceSpec:
    cohort: str
    source_path: str  # relative to the manifest directory


class ManifestBuildError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def build_evaluation_input_manifest(
    repository_root: Path | str,
    event_sources: Mapping[str, EventSourceSpec],
    output_path: Path | str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    now = now or datetime.now(UTC)
    destination = Path(output_path)
    if not destination.is_absolute():
        destination = root / destination
    if destination.exists():
        raise ManifestBuildError("MANIFEST_EXISTS", f"refusing to overwrite {destination}")
    try:
        allowlist = governance.load_allowlist(root)
        split = governance.verify_decision_file(
            root,
            governance.SPLIT_DECISION_RELATIVE,
            schema=governance.SPLIT_DECISION_SCHEMA,
            missing_code="EVENT_SPLIT_DECISION_MISSING",
            invalid_code="EVENT_SPLIT_DECISION_INVALID",
            allowlist=allowlist,
            now=now,
            check_body=governance.check_split_body,
        )
        scope = governance.verify_decision_file(
            root,
            governance.R04_DECISION_RELATIVE,
            schema=governance.R04_DECISION_SCHEMA,
            missing_code="R04_SCOPE_DECISION_MISSING",
            invalid_code="R04_SCOPE_DECISION_INVALID",
            allowlist=allowlist,
            now=now,
            check_body=governance.check_r04_body,
        )
    except governance.GovernanceError as exc:
        raise ManifestBuildError(exc.code, exc.detail) from exc

    partitions = {role: list(ids) for role, ids in split.payload["partitions"].items()}
    decided = {event_id: role for role, ids in partitions.items() for event_id in ids}
    if set(event_sources) != set(decided):
        raise ManifestBuildError(
            "EVENT_SPLIT_MISMATCH",
            f"event sources differ from the decided split; missing="
            f"{sorted(set(decided) - set(event_sources))}, "
            f"extra={sorted(set(event_sources) - set(decided))}",
        )
    if set(scope.payload["event_modes"]) != set(decided):
        raise ManifestBuildError(
            "CAMERA_SCOPE_INVALID", "R04 decision does not cover exactly the decided events"
        )
    events = []
    for event_id in sorted(decided):
        spec = event_sources[event_id]
        source = (destination.parent / spec.source_path).resolve()
        try:
            digest = sha256_file(source)
        except EvaluationInputError as exc:
            raise ManifestBuildError(exc.code, exc.detail) from exc
        events.append(
            {
                "event_id": event_id,
                "cohort": spec.cohort,
                "split_role": decided[event_id],
                "source_path": spec.source_path,
                "source_sha256": digest,
            }
        )
    manifest = {
        "schema_version": "phase12-evaluation-inputs/1",
        "evidence_classification": "real",
        "partitions": partitions,
        "events": events,
        "camera_scope_by_event": dict(scope.payload["event_modes"]),
        "accepted_sync_events": sorted(scope.payload["accepted_sync_events"]),
        "derived_from": {
            "event_split_decision_sha256": split.sha256,
            "r04_scope_decision_sha256": scope.sha256,
        },
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        load_evaluation_input_manifest(destination, verify_sources=True)
    except EvaluationInputError as exc:
        destination.unlink()
        raise ManifestBuildError(exc.code, exc.detail) from exc
    return manifest
