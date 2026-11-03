"""Synthetic tests for candidate split and Stage-2.1 queue reporting."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from railway_detection.annotation.candidate_split_queue import (
    build_candidate_event_split,
    build_stage21_review_queue,
    render_stage21_review_queue_markdown,
    write_candidate_event_split,
)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _inventory() -> dict:
    return {
        f"{cohort}/event_001": {
            "category": cohort,
            "event_id": "event_001",
            "front": {"sha256": _sha(cohort.encode() + b"front"), "path": f"{cohort}/front.mov"},
            "back": {"sha256": _sha(cohort.encode() + b"back"), "path": f"{cohort}/back.mov"},
        }
        for cohort in ("train_events", "no_train_events", "engine_events")
    }


def _proposal(path: Path, cohort: str, sha: str) -> None:
    path.write_text(json.dumps({
        "event_id": "event_001",
        "proposed_site_metadata": {
            "crossing_id": "crossing_A",
            "recording_session_id": "session_A",
        },
        "ai_assistant_metadata": {"input_media_files": [
            {
                "file_name": "camera_front.mov",
                "sha256": _inventory()[f"{cohort}/event_001"]["front"]["sha256"],
            },
            {
                "file_name": "camera_back.mov",
                "sha256": _inventory()[f"{cohort}/event_001"]["back"]["sha256"],
            },
        ]},
    }), encoding="utf-8")


def test_candidate_split_is_deterministic_and_cohort_qualified(tmp_path: Path) -> None:
    proposals = tmp_path / "proposals"
    for cohort in ("train_events", "no_train_events", "engine_events"):
        folder = proposals / cohort
        folder.mkdir(parents=True)
        _proposal(folder / "event_001_proposal_v1.json", cohort, "unused")
    first = build_candidate_event_split(_inventory(), proposals_dir=proposals, root=tmp_path)
    second = build_candidate_event_split(_inventory(), proposals_dir=proposals, root=tmp_path)
    assert first == second
    assert sorted(item["event_key"] for item in first["events"]) == sorted(_inventory())
    assert first["approval_status"] == "NOT_APPROVED"
    assert len(first["source_inventory"]["sha256"]) == 64
    assert first["grouping"]["leakage_safe"] is False
    assert first["grouping"]["checks_by_field"]["crossing_id"]["leakage_safe"] is False
    assert first["grouping"]["checks_by_field"]["recording_session_id"]["leakage_safe"] is False
    assert set(first["grouping"]["checks_by_field"]) == {"crossing_id", "recording_session_id"}


def test_split_reports_crossing_and_session_overlap_independently(tmp_path: Path) -> None:
    inventory = _inventory()
    proposals = tmp_path / "proposals"
    for index, (cohort, event) in enumerate(
        (("train_events", "event_001"), ("no_train_events", "event_001"), ("engine_events", "event_001"))
    ):
        folder = proposals / cohort
        folder.mkdir(parents=True, exist_ok=True)
        _proposal(folder / f"{event}_proposal_v1.json", cohort, "unused")
        path = folder / f"{event}_proposal_v1.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["proposed_site_metadata"]["recording_session_id"] = f"session_{index}"
        path.write_text(json.dumps(payload), encoding="utf-8")
    report = build_candidate_event_split(
        inventory,
        proposals_dir=proposals,
        root=tmp_path,
    )
    checks = report["grouping"]["checks_by_field"]
    assert checks["crossing_id"]["leakage_safe"] is False
    assert checks["recording_session_id"]["leakage_safe"] is True
    assert checks["crossing_id"]["overlapping_groups"]["crossing_A"]["roles"]
    assert report["grouping"]["events_missing_any_group_metadata"] == []


def test_split_lists_union_of_events_missing_either_leakage_key(tmp_path: Path) -> None:
    inventory = _inventory()
    proposals = tmp_path / "proposals"
    for cohort in ("train_events", "no_train_events", "engine_events"):
        folder = proposals / cohort
        folder.mkdir(parents=True)
        _proposal(folder / "event_001_proposal_v1.json", cohort, "unused")
    train_proposal = proposals / "train_events/event_001_proposal_v1.json"
    payload = json.loads(train_proposal.read_text(encoding="utf-8"))
    payload["proposed_site_metadata"].pop("recording_session_id")
    train_proposal.write_text(json.dumps(payload), encoding="utf-8")
    report = build_candidate_event_split(
        inventory,
        proposals_dir=proposals,
        root=tmp_path,
    )
    assert report["grouping"]["events_missing_any_group_metadata"] == [
        "train_events/event_001"
    ]


def test_queue_classifies_missing_and_invalid_without_mutating_inputs(tmp_path: Path) -> None:
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(json.dumps(_inventory()), encoding="utf-8")
    proposals = tmp_path / "proposals" / "train_events"
    proposals.mkdir(parents=True)
    _proposal(proposals / "event_001_proposal_v1.json", "train_events", "unused")
    reviews = tmp_path / "reviews" / "train_events"
    reviews.mkdir(parents=True)
    (reviews / "event_001_review.json").write_text(
        json.dumps({"schema_version": "6.0.0", "event_id": "event_001"}),
        encoding="utf-8",
    )
    before = (reviews / "event_001_review.json").read_bytes()
    report = build_stage21_review_queue(
        tmp_path,
        inventory_path=inventory_path,
        proposals_dir=tmp_path / "proposals",
        reviews_dir=tmp_path / "reviews",
    )
    by_key = {item["event_key"]: item for item in report["items"]}
    assert by_key["train_events/event_001"]["queue_category"] == "INVALID"
    assert "LEGACY_SCHEMA" in by_key["train_events/event_001"]["reason_codes"]
    assert by_key["no_train_events/event_001"]["queue_category"] == "MISSING"
    assert by_key["engine_events/event_001"]["queue_category"] == "MISSING"
    item = by_key["train_events/event_001"]
    assert item["stage21_review_status"] == "NEW_STAGE21_RECORD_REQUIRED"
    assert "reviewer_observed_media_hashes.front_sha256" in item["missing_fields"]
    assert item["source_media"]["front"]["path"] == "train_events/front.mov"
    assert set(item["candidate_boundary_evidence"]) == {
        "T0_first_visible",
        "T1_danger_zone_entry",
        "T2_crossing_occupancy_start",
        "T3_locomotive_unit_clearance",
        "T4_tail_clearance",
        "T_scene_clear",
    }
    assert len(item["missing_fields"]) == 25
    assert len(item["workflow_prerequisites"]) == 4
    markdown = render_stage21_review_queue_markdown(report)
    assert "not an annotation, approval" in markdown
    assert "Do not edit or migrate" in markdown
    assert (reviews / "event_001_review.json").read_bytes() == before
    assert report["approval_status"] == "NOT_APPROVED"


def test_report_writer_refuses_protected_ground_truth(tmp_path: Path) -> None:
    report = build_candidate_event_split(_inventory(), root=tmp_path)
    try:
        write_candidate_event_split(tmp_path / "data/ground_truth/report.json", report, root=tmp_path)
    except ValueError:
        pass
    else:
        raise AssertionError("candidate report writer must refuse protected ground-truth paths")
