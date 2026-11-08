"""Phase 11.12 fail-closed evaluation-readiness gate tests.

All READY fixtures are synthetic and live under pytest's temporary directory.
No production review record is promoted or modified.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from railway_detection.annotation.evaluation_readiness_gate import evaluate_readiness
from railway_detection.annotation.stage2_1_schema import STAGE_2_1_SCHEMA_VERSION
from second_review_support import SECOND_REVIEWER, independent_second_review
from test_phase11_9_synthetic_pilot import (
    PILOT_REVIEWER,
    SYNTHETIC_EVENTS,
    _build_pilot_record,
    _promo_ctx,
)


def _allowlist(tmp_path: Path) -> Path:
    path = tmp_path / "authorized_reviewers.json"
    path.write_text(json.dumps({"authorized_reviewers": [PILOT_REVIEWER, SECOND_REVIEWER]}), encoding="utf-8")
    return path


def _three_records(tmp_path: Path) -> tuple[list[dict], dict, dict, dict]:
    records: list[dict] = []
    active: dict[str, str] = {}
    registry: dict[str, dict[str, str]] = {}
    paths: dict[str, dict[str, str]] = {}
    for event in SYNTHETIC_EVENTS:
        record = _build_pilot_record(tmp_path, event)
        records.append(record)
        if event["cohort"] == "engine_events":
            # RD-043: an engine-event T3/T4 interpretation requires an independent second review.
            records.append(independent_second_review(record))
        context = _promo_ctx(tmp_path, event, record)
        active.update(context["active_proposal_sha256_by_event"])
        registry.update(context["media_sha256_registry"])
        paths.update(context["media_file_paths"])
    return records, active, registry, paths


def _gate(tmp_path: Path, records: list[dict], active: dict, registry: dict, paths: dict):
    return evaluate_readiness(
        records=records,
        active_proposal_sha256_by_event=active,
        media_sha256_registry=registry,
        allowlist_path=_allowlist(tmp_path),
        media_file_paths=paths,
    )


def test_empty_source_is_not_ready(tmp_path: Path):
    verdict = evaluate_readiness(
        records=[],
        active_proposal_sha256_by_event={},
        media_sha256_registry={},
        allowlist_path=_allowlist(tmp_path),
        media_file_paths={},
    )
    assert not verdict.ready
    assert any("NO_RECORDS" in blocker for blocker in verdict.blockers)


def test_missing_allowlist_fails_closed(tmp_path: Path):
    verdict = evaluate_readiness(
        records=[],
        active_proposal_sha256_by_event={},
        media_sha256_registry={},
        allowlist_path=tmp_path / "missing.json",
        media_file_paths={},
    )
    assert not verdict.ready
    assert any("ALLOWLIST_LOAD_FAILED" in blocker for blocker in verdict.blockers)


def test_reviews_dir_valid_synthetic_records_are_ready(tmp_path: Path):
    records, active, registry, paths = _three_records(tmp_path)
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    for record in records:
        event_id = record["event_id"]
        (reviews / f"{record['review_id']}_review.json").write_text(
            json.dumps(record), encoding="utf-8"
        )
    verdict = evaluate_readiness(
        reviews_dir=reviews,
        active_proposal_sha256_by_event=active,
        media_sha256_registry=registry,
        allowlist_path=_allowlist(tmp_path),
        media_file_paths=paths,
    )
    assert verdict.ready
    assert verdict.stage == "stage3_single_camera_baseline"


def test_reviews_dir_rejects_legacy_record(tmp_path: Path):
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    legacy = {
        "schema_version": "6.0.0",
        "event_id": "legacy_event",
        "adjudication_status": "APPROVED",
    }
    (reviews / "legacy_review.json").write_text(json.dumps(legacy), encoding="utf-8")
    verdict = evaluate_readiness(
        reviews_dir=reviews,
        active_proposal_sha256_by_event={},
        media_sha256_registry={},
        allowlist_path=_allowlist(tmp_path),
        media_file_paths={},
    )
    assert not verdict.ready
    assert any("LEGACY_OR_UNKNOWN_SCHEMA" in blocker for blocker in verdict.blockers)


def test_disputed_record_blocks_readiness(tmp_path: Path):
    records, active, registry, paths = _three_records(tmp_path)
    records[0]["adjudication_status"] = "DISPUTED"
    records[0]["adjudication_history"][-1]["status_set"] = "DISPUTED"
    verdict = _gate(tmp_path, records, active, registry, paths)
    assert not verdict.ready
    assert any("UNRESOLVED_DISAGREEMENT" in blocker for blocker in verdict.blockers)


def test_missing_cohort_blocks_readiness(tmp_path: Path):
    records, active, registry, paths = _three_records(tmp_path)
    verdict = _gate(tmp_path, records[:1], active, registry, paths)
    assert not verdict.ready
    assert any("MISSING_COHORT_APPROVAL:no_train_events" in blocker for blocker in verdict.blockers)


def test_live_media_tampering_blocks_readiness(tmp_path: Path):
    records, active, registry, paths = _three_records(tmp_path)
    front = Path(paths[SYNTHETIC_EVENTS[0]["event_id"]]["front"])
    front.write_bytes(b"tampered after review")
    verdict = _gate(tmp_path, records, active, registry, paths)
    assert not verdict.ready
    assert any(
        "PROMOTION_FAILED:synthetic_pilot_event_001" in blocker
        for blocker in verdict.blockers
    )
    assert any("MEDIA_HASH_CHANGED_SINCE_REVIEW" in blocker for blocker in verdict.blockers)


def test_fully_valid_synthetic_records_are_ready_for_named_stage(tmp_path: Path):
    records, active, registry, paths = _three_records(tmp_path)
    verdict = evaluate_readiness(
        records=records,
        active_proposal_sha256_by_event=active,
        media_sha256_registry=registry,
        allowlist_path=_allowlist(tmp_path),
        media_file_paths=paths,
        stage="phase12_single_camera_baseline",
    )
    assert verdict.ready
    assert verdict.stage == "phase12_single_camera_baseline"
    assert "approved_record_count=4" in verdict.evidence
    assert all(record["schema_version"] == STAGE_2_1_SCHEMA_VERSION for record in records)


def test_duplicate_approved_event_blocks_readiness(tmp_path: Path):
    records, active, registry, paths = _three_records(tmp_path)
    duplicate = dict(records[0])
    duplicate["review_id"] = "duplicate-review"
    records.append(duplicate)
    verdict = _gate(tmp_path, records, active, registry, paths)
    assert not verdict.ready
    assert any(
        "DUPLICATE_APPROVED_RECORD:synthetic_pilot_event_001" in blocker
        for blocker in verdict.blockers
    )


def test_unallowlisted_reviewer_blocks_readiness(tmp_path: Path):
    records, active, registry, paths = _three_records(tmp_path)
    records[0]["reviewer_metadata"]["reviewer_id"] = "unauthorized@example.com"
    verdict = _gate(tmp_path, records, active, registry, paths)
    assert not verdict.ready
    assert any("REVIEWER_NOT_AUTHORIZED" in blocker for blocker in verdict.blockers)


def test_deleted_history_entry_blocks_readiness(tmp_path: Path):
    records, active, registry, paths = _three_records(tmp_path)
    records[0]["adjudication_history"] = []
    verdict = _gate(tmp_path, records, active, registry, paths)
    assert not verdict.ready
    assert any(
        "SCHEMA_VALIDATION_FAILED:synthetic_pilot_event_001" in blocker
        for blocker in verdict.blockers
    )


def test_records_and_reviews_dir_cannot_be_combined(tmp_path: Path):
    records, active, registry, paths = _three_records(tmp_path)
    verdict = evaluate_readiness(
        records=records,
        reviews_dir=tmp_path,
        active_proposal_sha256_by_event=active,
        media_sha256_registry=registry,
        allowlist_path=_allowlist(tmp_path),
        media_file_paths=paths,
    )
    assert not verdict.ready
    assert any("MULTIPLE_RECORD_SOURCES" in blocker for blocker in verdict.blockers)
