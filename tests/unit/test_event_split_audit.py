"""Synthetic and metadata-parity tests for Task 1 event split leakage audit."""

from __future__ import annotations

import json
from pathlib import Path

from railway_detection.data.split_audit import evaluate_candidate_split, run_split_audit

REPO_ROOT = Path(__file__).resolve().parents[2]


def _synth_event(
    idx: int,
    *,
    cohort: str,
    crossing: str,
    session: str,
    epoch: float,
    mode: str = "dual_camera",
) -> dict:
    return {
        "event_key": f"{cohort}/event_{idx:03d}",
        "cohort": cohort,
        "event_id": f"event_{idx:03d}",
        "crossing_id": crossing,
        "true_capture_session": session,
        "intraday_block_id": f"{session}_blk_01",
        "front_epoch_s": epoch,
        "creationdate_back": f"ts_{idx:03d}",
        "front_sha256": f"f{idx:063x}",
        "back_sha256": f"b{idx:063x}",
        "true_lighting": "day",
        "r04_scope_mode": mode,
    }


def test_multi_crossing_and_multi_session_split_is_leakage_safe():
    events = [
        _synth_event(1, cohort="train_events", crossing="X1", session="S1", epoch=1000.0),
        _synth_event(2, cohort="no_train_events", crossing="X1", session="S1", epoch=2000.0),
        _synth_event(3, cohort="train_events", crossing="X2", session="S2", epoch=5000.0),
        _synth_event(4, cohort="no_train_events", crossing="X2", session="S2", epoch=6000.0),
        _synth_event(5, cohort="train_events", crossing="X3", session="S3", epoch=9000.0),
        _synth_event(6, cohort="no_train_events", crossing="X3", session="S3", epoch=10000.0),
    ]
    partitions = {
        "train": ["train_events/event_001", "no_train_events/event_002"],
        "val": ["train_events/event_003", "no_train_events/event_004"],
        "test": ["train_events/event_005", "no_train_events/event_006"],
    }
    res = evaluate_candidate_split(events, partitions, name="multi_site")
    assert res["leakage_safe"] is True
    assert res["scientific_defects"] == []


def test_single_crossing_or_two_session_split_is_never_marked_leakage_safe():
    events = [
        _synth_event(1, cohort="train_events", crossing="crossing_A", session="S1", epoch=1000.0),
        _synth_event(2, cohort="no_train_events", crossing="crossing_A", session="S1", epoch=2000.0),
        _synth_event(3, cohort="train_events", crossing="crossing_A", session="S2", epoch=5000.0),
        _synth_event(4, cohort="no_train_events", crossing="crossing_A", session="S2", epoch=6000.0),
    ]
    partitions = {
        "train": ["train_events/event_001", "no_train_events/event_002"],
        "val": ["train_events/event_003"],
        "test": ["no_train_events/event_004"],
    }
    res = evaluate_candidate_split(events, partitions, name="single_site")
    assert res["leakage_safe"] is False
    assert res["checks"]["crossing_disjoint"] is False
    assert res["checks"]["session_disjoint"] is False


def test_live_repository_split_audit_matches_checked_in_report():
    report = run_split_audit(REPO_ROOT)
    checked_in = json.loads(
        (REPO_ROOT / "results/dataset_audit/layer_b_split_audit_and_collection_plan.json").read_text(
            encoding="utf-8"
        )
    )
    assert report == checked_in
    assert report["raw_media_accessed"] is False
    assert report["can_27_events_produce_leakage_safe_3way_split"] is False
    assert report["corpus_counts"]["total_events"] == 27
    prior = report["candidate_splits_evaluated"]["prior_hash_candidate_16_6_5"]
    chrono = report["candidate_splits_evaluated"]["chrono_temporal_block_15_5_7"]
    assert prior["leakage_safe"] is False
    assert chrono["leakage_safe"] is False
    assert any("ZERO_DUAL_CAMERA_IN_ROLES" in d for d in prior["scientific_defects"])
    assert prior["overlaps"]["split_adjacent_pairs"]
    assert len(chrono["overlaps"]["split_adjacent_pairs"]) == 1
    assert chrono["role_summary"]["val"]["cohorts"].get("no_train_events", 0) == 1
    assert report["proposal_metadata_inconsistencies_count"] == 7
