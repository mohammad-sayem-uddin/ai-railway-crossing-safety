"""Legacy review reconciliation is read-only classification, never migration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from railway_detection.annotation.legacy_reconciliation import (
    reconcile_legacy_reviews,
    write_reconciliation_report,
)
from railway_detection.evaluation.ground_truth_loader import (
    LegacyRecordRefused,
    load_approved_ground_truth_from_dir,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _legacy_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    proposals = root / "data/ground_truth/proposals/train_events"
    reviews = root / "data/ground_truth/reviews/train_events"
    proposals.mkdir(parents=True)
    reviews.mkdir(parents=True)
    v1 = proposals / "event_001_proposal.json"
    v2 = proposals / "event_001_proposal_v2.json"
    v1.write_text('{"v": 1}')
    v2.write_text('{"v": 2}')
    for index in (1, 2):
        event = f"event_00{index}"
        if index == 2:
            (proposals / "event_002_proposal.json").write_text('{"v": 1}')
        record = {
            "event_id": event,
            "schema_version": "6.0.0",
            "adjudication_status": "APPROVED",
            "proposal_reference": {
                "proposal_file": f"data/ground_truth/proposals/train_events/{event}_proposal.json",
                "proposal_sha256": hashlib.sha256(
                    (proposals / f"{event}_proposal.json").read_bytes()
                ).hexdigest(),
            },
            "reviewer_metadata": {
                "reviewer_id": "human_researcher_lead",
                "review_date_utc": "2026-10-12T16:51:21Z",
            },
        }
        (reviews / f"{event}_review.json").write_text(json.dumps(record))
    return root


def test_each_legacy_record_is_classified_and_none_is_migratable(tmp_path: Path):
    report = reconcile_legacy_reviews(_legacy_repo(tmp_path))
    assert report["summary"]["record_count"] == 2
    assert report["summary"]["migratable_count"] == 0
    assert report["summary"]["distinct_review_timestamps"] == 1
    first, second = report["records"]
    assert first["recorded_proposal_matches_referenced_file"] is True
    assert first["recorded_proposal_matches_active"] is False  # superseded by v2
    assert second["recorded_proposal_matches_active"] is True
    for entry in report["records"]:
        assert entry["accepted_by_ground_truth_loader"] is False
        assert entry["migratable_to_stage21"] is False
        assert "fabricate" in entry["migration_blocker"]
        assert "records_sharing_review_timestamp" in entry
        assert any("blocklisted" in finding for finding in entry["findings"])
        assert any("shared by 2 records" in finding for finding in entry["findings"])
        assert "reviewer_observed_media_hashes" in entry["stage21_fields_missing"]


def test_report_is_additive_and_originals_are_untouched(tmp_path: Path):
    root = _legacy_repo(tmp_path)
    before = {p: p.read_bytes() for p in (root / "data").rglob("*") if p.is_file()}
    out = tmp_path / "out" / "report.json"
    write_reconciliation_report(root, out)
    assert out.is_file()
    assert {p: p.read_bytes() for p in (root / "data").rglob("*") if p.is_file()} == before


def test_report_refuses_to_write_inside_ground_truth(tmp_path: Path):
    root = _legacy_repo(tmp_path)
    with pytest.raises(ValueError, match="protected"):
        write_reconciliation_report(root, root / "data/ground_truth/reviews/x.json")


def test_loader_still_refuses_the_legacy_records(tmp_path: Path):
    root = _legacy_repo(tmp_path)
    with pytest.raises(LegacyRecordRefused):
        load_approved_ground_truth_from_dir(root / "data/ground_truth/reviews")


def test_real_repository_has_no_stage21_records_and_none_migratable():
    report = reconcile_legacy_reviews(REPO_ROOT)
    assert report["summary"]["stage21_record_count"] == 0
    assert report["summary"]["migratable_count"] == 0
    assert report["summary"]["record_count"] == len(
        list((REPO_ROOT / "data/ground_truth/reviews").rglob("*_review.json"))
    )
