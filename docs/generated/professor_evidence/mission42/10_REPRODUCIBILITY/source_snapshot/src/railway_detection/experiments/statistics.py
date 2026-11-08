"""Statistical analysis procedures for real-world benchmark evaluations.

Implements exact requirements from REAL_WORLD_EXPERIMENT_PLAN.md §10:
- Wilson score 95% CI for binomial proportions
- Non-parametric bootstrap 95% CI (10,000 resamples) for continuous metrics
- Paired event-level comparisons (B4 vs B0, B4 vs B3, B4 vs B2)
- Non-parametric sign test p-values
- Safe output of 'not_evaluable' when endpoints cannot be statistically estimated
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from railway_detection.evaluation.metrics import wilson_score_interval


def bootstrap_ci(
    values: list[float],
    n_resamples: int = 10000,
    confidence: float = 0.95,
    seed: int = 42,
) -> tuple[float, float] | str:
    """Compute non-parametric bootstrap confidence interval for the mean.

    Returns:
        (ci_lower, ci_upper) or 'not_evaluable' if insufficient data.
    """
    clean_vals = [v for v in values if v is not None and not math.isnan(v)]
    if len(clean_vals) < 2:
        return "not_evaluable"

    rng = np.random.default_rng(seed)
    arr = np.array(clean_vals, dtype=np.float64)
    boot_means = np.empty(n_resamples, dtype=np.float64)

    for i in range(n_resamples):
        sample = rng.choice(arr, size=len(arr), replace=True)
        boot_means[i] = np.mean(sample)

    alpha = 1.0 - confidence
    lower = float(np.percentile(boot_means, 100.0 * (alpha / 2.0)))
    upper = float(np.percentile(boot_means, 100.0 * (1.0 - alpha / 2.0)))
    return round(lower, 4), round(upper, 4)


def sign_test_p_value(differences: list[float]) -> float | str:
    """Compute exact two-sided sign test p-value for paired differences."""
    clean_diffs = [d for d in differences if d is not None and not math.isnan(d)]
    pos = sum(1 for d in clean_diffs if d > 0)
    neg = sum(1 for d in clean_diffs if d < 0)
    n = pos + neg

    if n == 0:
        return "not_evaluable"

    # Exact binomial p-value under H0: p = 0.5
    k = min(pos, neg)
    p_val = 0.0
    for i in range(k + 1):
        p_val += math.comb(n, i) * (0.5**n)
    p_val = min(1.0, 2.0 * p_val)  # two-sided
    return round(p_val, 4)


def paired_comparison(
    values_a: list[float | None],
    values_b: list[float | None],
    name_a: str = "B4",
    name_b: str = "B0",
    seed: int = 42,
) -> dict[str, Any]:
    """Perform paired event-level comparison between two benchmark conditions on the same events."""
    assert len(values_a) == len(values_b), "Paired comparison requires equal-length lists"

    paired_diffs: list[float] = []
    for a, b in zip(values_a, values_b):
        if a is not None and b is not None and not math.isnan(a) and not math.isnan(b):
            paired_diffs.append(a - b)

    if not paired_diffs:
        return {
            "comparison": f"{name_a} vs {name_b}",
            "n_pairs": 0,
            "mean_difference": "not_evaluable",
            "bootstrap_ci95": "not_evaluable",
            "sign_test_p_value": "not_evaluable",
            "statistically_significant": False,
        }

    mean_diff = float(np.mean(paired_diffs))
    boot_ci = bootstrap_ci(paired_diffs, seed=seed)
    p_val = sign_test_p_value(paired_diffs)

    is_significant = False
    if isinstance(boot_ci, tuple):
        # Significant if 95% CI does not span zero
        is_significant = (boot_ci[0] > 0 and boot_ci[1] > 0) or (boot_ci[0] < 0 and boot_ci[1] < 0)

    return {
        "comparison": f"{name_a} vs {name_b}",
        "n_pairs": len(paired_diffs),
        "mean_difference": round(mean_diff, 4),
        "bootstrap_ci95": list(boot_ci) if isinstance(boot_ci, tuple) else boot_ci,
        "sign_test_p_value": p_val,
        "statistically_significant": is_significant,
    }


def compute_comprehensive_statistics(
    all_condition_results: dict[str, Any],
) -> dict[str, Any]:
    """Compute the master statistical analysis package across all conditions."""
    stats_out: dict[str, Any] = {
        "proportions": {},
        "continuous_endpoints": {},
        "paired_comparisons": {},
        "notes": [
            "Sample size N=21 is limited; all statistical results must be interpreted as exploratory.",
            "Wilson score interval used for binomial proportions (missed-train rate, premature-opening rate).",
            "Non-parametric bootstrap with 10,000 resamples used for continuous endpoints.",
            "Sign test used for paired non-parametric differences on identical events.",
        ],
    }

    # Extract proportions and compute Wilson CIs
    for cond_id, summary in all_condition_results.items():
        if hasattr(summary, "to_dict"):
            s_dict = summary.to_dict()
        elif isinstance(summary, dict):
            s_dict = summary
        else:
            continue

        n_events = s_dict.get("eligible_events", 21)
        missed_cnt = s_dict.get("missed_train_count", 0)
        prem_cnt = s_dict.get("premature_opening_count", 0)
        prem_eval = s_dict.get("premature_opening_evaluable_count", 0)

        mtr_ci = wilson_score_interval(missed_cnt, n_events)
        por_ci = wilson_score_interval(prem_cnt, prem_eval) if prem_eval > 0 else "not_evaluable"

        stats_out["proportions"][cond_id] = {
            "eligible_events": n_events,
            "missed_train_rate": s_dict.get("missed_train_rate"),
            "missed_train_ci95": list(mtr_ci),
            "premature_opening_evaluable": prem_eval,
            "premature_opening_rate": s_dict.get("premature_opening_rate"),
            "premature_opening_ci95": list(por_ci) if isinstance(por_ci, tuple) else por_ci,
        }

    return stats_out
