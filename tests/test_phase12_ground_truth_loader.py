"""Phase 12 fail-closed approved-ground-truth loader tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from railway_detection.evaluation.ground_truth_loader import (
    BoundaryNotComputable,
    CandidateProposalRefused,
    GroundTruthLoadError,
    LegacyRecordError,
    LegacyRecordRefused,
    NotApprovedRefused,
    UnapprovedRecordError,
    UncertainBoundaryError,
    load_approved_ground_truth,
    load_approved_ground_truth_from_dir,
)
from test_phase11_9_synthetic_pilot import (
    SYNTHETIC_EVENTS,
    _build_pilot_record,
)


def _record(tmp_path: Path, index: int = 0) -> dict:
    return _build_pilot_record(tmp_path, SYNTHETIC_EVENTS[index])


def test_legacy_schema_is_refused_and_alias_matches():
    with pytest.raises(LegacyRecordRefused):
        load_approved_ground_truth([{"schema_version": "6.0.0", "event_id": "legacy"}])
    assert LegacyRecordError is LegacyRecordRefused


def test_candidate_proposal_shape_is_refused():
    candidate = {"proposal_id": "candidate-1", "event_id": "candidate", "schema_version": "5.0.0"}
    with pytest.raises(CandidateProposalRefused):
        load_approved_ground_truth([candidate])
    with pytest.raises(CandidateProposalRefused):
        load_approved_ground_truth([{"event_id": "candidate", "proposal_file": "candidate.json"}])


def test_non_approved_stage21_record_is_refused(tmp_path: Path):
    record = _record(tmp_path)
    record["adjudication_status"] = "REJECTED"
    record["adjudication_history"][-1]["status_set"] = "REJECTED"
    with pytest.raises(NotApprovedRefused):
        load_approved_ground_truth([record])
    assert UnapprovedRecordError is NotApprovedRefused


def test_observable_values_load_and_censored_values_are_not_numeric(tmp_path: Path):
    loaded = load_approved_ground_truth([_record(tmp_path)])
    assert len(loaded) == 1
    truth = loaded[0]
    assert truth.observable_value("T1_danger_zone_entry") == pytest.approx(5.8)
    assert "T_scene_clear" in truth.censored_boundaries
    with pytest.raises(BoundaryNotComputable):
        truth.observable_value("T_scene_clear")


def test_uncertain_boundary_cannot_be_requested_as_observable(tmp_path: Path):
    record = _record(tmp_path)
    boundary = record["boundary_adjudications"]["T1_danger_zone_entry"]
    boundary["state"] = "UNCERTAIN"
    boundary["value_s"] = None
    boundary["reference_camera"] = None
    loaded = load_approved_ground_truth([record])
    assert "T1_danger_zone_entry" in loaded[0].uncertain_boundaries
    with pytest.raises(UncertainBoundaryError):
        loaded[0].observable_value("T1_danger_zone_entry")


def test_directory_loader_loads_approved_review_records(tmp_path: Path):
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    record = _record(tmp_path)
    (reviews / "event_review.json").write_text(json.dumps(record), encoding="utf-8")
    loaded = load_approved_ground_truth_from_dir(reviews)
    assert [item.event_id for item in loaded] == [record["event_id"]]


def test_directory_loader_reads_only_review_suffix_and_rejects_mixed_sources(tmp_path: Path):
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    (reviews / "event_review.json").write_text(json.dumps(_record(tmp_path)), encoding="utf-8")
    (reviews / "candidate.json").write_text(
        json.dumps({"proposal_id": "candidate"}), encoding="utf-8"
    )
    with pytest.raises(CandidateProposalRefused):
        load_approved_ground_truth_from_dir(reviews)


def test_directory_loader_missing_directory_fails_closed(tmp_path: Path):
    with pytest.raises(GroundTruthLoadError):
        load_approved_ground_truth_from_dir(tmp_path / "does-not-exist")


def test_duplicate_event_ids_are_refused(tmp_path: Path):
    first = _record(tmp_path, 0)
    second = dict(first)
    second["review_id"] = "different-review"
    with pytest.raises(GroundTruthLoadError, match="Duplicate approved"):
        load_approved_ground_truth([first, second])
