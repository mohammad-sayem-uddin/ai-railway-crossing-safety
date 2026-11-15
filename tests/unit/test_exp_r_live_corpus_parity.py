"""Verify independent Exp R reproduction and corpus integrity against cached JSONLs."""

from __future__ import annotations

from pathlib import Path

from railway_detection.experiments.exp_r_validation import validate_exp_r_independently

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_validate_exp_r_independently_matches_published_loeo_and_manifests() -> None:
    report = validate_exp_r_independently(REPO_ROOT)

    assert report["raw_media_accessed"] is False
    corpus = report["corpus_verification"]
    assert corpus["manifest_sha256_all_match"] is True
    assert corpus["n_events_verified"] == 27
    assert corpus["n_total_windows"] == 2600
    assert corpus["max_csv_vs_jsonl_abs_diff"] == 0.0

    pub = report["published_artifact_reproduction"]
    assert pub["exact_match_within_published_4dp"] is True
    assert pub["oof_metrics_match_within_4dp"] is True
    assert pub["calibration_match_within_4dp"] is True
    assert pub["fold_mismatches"] == []
    assert pub["max_oof_prob_abs_diff"] < 5e-5

    findings = report["methodological_audit_findings"]
    assert findings["f1_drops_vs_frozen_baseline"] is True
    assert findings["recall_drops_vs_frozen_baseline"] is True
    assert findings["brier_diff_ci_crosses_zero"] is True
    assert findings["original_temp_ceiling_saturated_folds"] == 9
    assert findings["no_train_tiebreak_changed_folds"] == [
        "train_events/event_003",
        "train_events/event_023",
    ]
    assert report["reproduced_published_loeo"]["oof_metrics"]["f1"] == 0.64
