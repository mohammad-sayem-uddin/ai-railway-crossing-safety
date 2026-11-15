"""Synthetic unit tests for independent Exp R LOEO validation helpers."""
# INPUT_CLASSIFICATION: SYNTHETIC_ONLY

from __future__ import annotations

import math

import pytest

from railway_detection.experiments.exp_r_validation import (
    classification_metrics,
    longest_run,
    run_loeo_variant,
    wilson_ci,
)


def _synthetic_corpus() -> list[dict]:
    """Build a small synthetic LOEO corpus exercising tie-break and T-ceiling behavior."""
    return [
        {
            "event_id": "train_events/syn_01",
            "cohort": "train_events",
            "binary_label": 1,
            "scores": [0.20, 0.85, 0.88, 0.30],
        },
        {
            "event_id": "train_events/syn_02",
            "cohort": "train_events",
            "binary_label": 1,
            "scores": [0.92, 0.91, 0.40],
        },
        {
            "event_id": "train_events/syn_03",
            "cohort": "train_events",
            "binary_label": 1,
            "scores": [0.55, 0.80, 0.82, 0.25],
        },
        {
            "event_id": "train_events/syn_04",
            "cohort": "train_events",
            "binary_label": 0,
            "scores": [0.90, 0.20, 0.78, 0.25],
        },
        {
            "event_id": "train_events/syn_05",
            "cohort": "train_events",
            "binary_label": 0,
            "scores": [0.40, 0.42, 0.44, 0.10],
        },
        {
            "event_id": "train_events/syn_06",
            "cohort": "train_events",
            "binary_label": 0,
            "scores": [0.81, 0.15, 0.10],
        },
        {
            "event_id": "no_train_events/syn_nt1",
            "cohort": "no_train_events",
            "binary_label": 0,
            "scores": [0.45, 0.50, 0.82, 0.20],
        },
        {
            "event_id": "engine_events/syn_eng1",
            "cohort": "engine_events",
            "binary_label": 0,
            "scores": [0.12, 0.15, 0.14],
        },
    ]


def test_wilson_ci_and_longest_run() -> None:
    zero = wilson_ci(0, 0)
    assert zero == {"point": None, "ci95_low": None, "ci95_high": None, "n": 0}

    ci = wilson_ci(8, 13)
    assert ci["n"] == 13
    assert math.isclose(ci["point"], 8.0 / 13.0, abs_tol=1e-5)
    assert 0.35 <= float(ci["ci95_low"]) < float(ci["point"]) < float(ci["ci95_high"]) <= 0.85

    assert longest_run([0.1, 0.75, 0.80, 0.2, 0.90], 0.75) == 2
    assert longest_run([0.1, 0.2], 0.75) == 0


def test_classification_metrics_balanced() -> None:
    m = classification_metrics([True, False, True, False], [1, 1, 0, 0])
    assert m["tp"] == 1
    assert m["fp"] == 1
    assert m["tn"] == 1
    assert m["fn"] == 1
    assert math.isclose(m["recall"], 0.5)
    assert math.isclose(m["specificity"], 0.5)
    assert math.isclose(m["precision"], 0.5)
    assert math.isclose(m["f1"], 0.5)
    assert math.isclose(m["accuracy"], 0.5)


def test_run_loeo_variant_synthetic_tiebreak_and_temperature_grid() -> None:
    corpus = _synthetic_corpus()
    t_capped = tuple(round(0.5 + 0.1 * i, 1) for i in range(36))
    t_wide = tuple(round(0.5 + 0.1 * i, 1) for i in range(100))

    res_tie = run_loeo_variant(
        corpus, use_no_train_tiebreak=True, temperatures=t_capped, n_bootstrap=50, seed=42
    )
    res_strict = run_loeo_variant(
        corpus, use_no_train_tiebreak=False, temperatures=t_wide, n_bootstrap=50, seed=42
    )

    assert len(res_tie["folds"]) == 6
    assert len(res_strict["folds"]) == 6
    assert set(res_tie["oof_metrics"]).issuperset(
        {"tp", "fp", "tn", "fn", "recall", "specificity", "precision", "f1", "accuracy"}
    )
    assert "oof_cal_brier" in res_tie["calibration"]
    assert "oof_cal_ece_5bin" in res_tie["calibration"]
    assert res_tie["oof_metrics"]["specificity"] == pytest.approx(1.0)
    assert res_tie["oof_metrics"]["recall"] == pytest.approx(1.0)
