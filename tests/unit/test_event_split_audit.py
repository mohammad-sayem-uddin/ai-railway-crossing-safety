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

    # Mission 5 Option A stratified diagnostics (Exp S)
    opt_a = report["option_a_stratified_diagnostics"]
    app = opt_a["approach_detection_by_session"]
    assert app["session_20260914_daytime"]["closure_decision_count"] == 7
    assert app["session_20260914_daytime"]["n_events"] == 20
    assert app["session_20261004_night_lowlight"]["closure_decision_count"] == 3
    assert app["session_20261004_night_lowlight"]["n_events"] == 3
    assert app["session_20261004_night_lowlight"]["side_proxy_frames_total"] == 824
    assert app["all_train_events"]["side_proxy_frames_total"] == 967

    exit_diag = opt_a["exit_confirmation_and_sync11_fail_closed_finding"]
    assert exit_diag["sync11_event_count"] == 11
    assert exit_diag["sync11_back_rear_dets_positive_count"] == 0
    assert exit_diag["sync11_v3_premature_opening_count"] == 0
    assert exit_diag["sync11_reopening_decision_v3_count"] == 0
    assert exit_diag["sync11_zero_premature_opening_95_upper_bound_all11"] == 0.2384

    # Mission 5/6 Option C statistical power & reconciled cohort sums
    pwr = report["targeted_additional_data_collection_plan"]["statistical_power_and_sample_size_recalculation"]
    exact_t = pwr["exact_binomial_and_cluster_targets"]
    assert exact_t["zero_failure_95_upper_bound_10pct_unclustered_n"] == 29
    assert exact_t["zero_failure_95_upper_bound_5pct_unclustered_n"] == 59
    assert exact_t["unclustered_n_for_80pct_mcnemar_power_p20"] == 42
    assert exact_t["cluster_adjusted_test_trains_for_10pct_bound"] == 43
    assert exact_t["cluster_adjusted_test_trains_for_5pct_bound"] == 86
    floor = pwr["structural_floor_critique"]["minimal_3crossing_6session_total"]
    assert floor["zero_premature_opening_95_upper_bound"] == 0.2209
    tiers = pwr["reconciled_cohort_tiers"]
    assert tiers["tier_c1_unclustered_10pct_bound"]["grand_total_events"] == 207
    t2 = tiers["tier_c2_cluster_adjusted_10pct_bound_primary"]
    assert t2["grand_total_events"] == 235
    assert (
        t2["cohorts"]["train"]["cohort_total_events"]
        + t2["cohorts"]["val"]["cohort_total_events"]
        + t2["cohorts"]["test"]["cohort_total_events"]
        == 235
    )
    t3 = tiers["tier_c3_cluster_adjusted_80pct_mcnemar_p20"]
    assert t3["grand_total_events"] == 271
    assert t3["effective_test_power_metrics"]["unconditional_mcnemar_power_p20_p005"] >= 0.80

    # Mission 6 autonomous reopening investigation (M1-M5)
    reopen = report["autonomous_reopening_and_clearance_investigation"]
    b = reopen["sync11_v3_outcome_breakdown"]
    assert b["total_sync11"] == 11
    assert b["completed_automatic_reopenings"] == 0
    assert b["l1_approach_closures"] + b["eof_stream_mismatch_failsafe_clamps"] + b["never_closed_idle"] == 11
    methods = {m["method_id"]: m for m in reopen["method_comparison_m1_to_m5"]}
    assert methods["M3_monotonic_transit_and_post_rear_silence"]["real_t4_corpus_premature"] == 0
    assert methods["M5_v3_plus_m3_and_independent_occupancy_sensor"]["synthetic_nominal_with_occ_clear"]["reopened_cleanly"] is True
    assert methods["M5_v3_plus_m3_and_independent_occupancy_sensor"]["synthetic_without_occ_sensor"]["reopened_cleanly"] is False
