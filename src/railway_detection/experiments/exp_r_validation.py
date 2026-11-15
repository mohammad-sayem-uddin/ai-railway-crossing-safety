"""Independent non-raw cache validation and methodological sensitivity audit for Exp R."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any

from railway_detection.safety.media_guard import require_media_authorization


def _sha256_file(path: Path) -> str:
    require_media_authorization(path, "HASH_RAW_MEDIA")
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def wilson_ci(successes: int, total: int, z: float = 1.959963984540054) -> dict[str, float | None]:
    """Return two-sided Wilson score 95% interval for binomial counts."""
    if total <= 0:
        return {"point": None, "ci95_low": None, "ci95_high": None, "n": 0}
    p = successes / total
    denom = 1.0 + (z * z) / total
    center = (p + (z * z) / (2.0 * total)) / denom
    half = (z * math.sqrt((p * (1.0 - p) + (z * z) / (4.0 * total)) / total)) / denom
    return {
        "point": round(p, 6),
        "ci95_low": round(max(0.0, center - half), 6),
        "ci95_high": round(min(1.0, center + half), 6),
        "n": int(total),
    }


def longest_run(scores: list[float], tau: float) -> int:
    best = cur = 0
    for s in scores:
        if s >= tau:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def classification_metrics(preds: list[bool], labels: list[int]) -> dict[str, Any]:
    tp = sum(1 for p, y in zip(preds, labels, strict=True) if p and y == 1)
    fp = sum(1 for p, y in zip(preds, labels, strict=True) if p and y == 0)
    tn = sum(1 for p, y in zip(preds, labels, strict=True) if not p and y == 0)
    fn = sum(1 for p, y in zip(preds, labels, strict=True) if not p and y == 1)
    n = len(labels)
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    spec = tn / (tn + fp) if (tn + fp) else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    f1 = (2.0 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
    acc = (tp + tn) / n if n else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "recall": round(rec, 6),
        "specificity": round(spec, 6),
        "precision": round(prec, 6),
        "f1": round(f1, 6),
        "accuracy": round(acc, 6),
    }


def _logit(p: float) -> float:
    clipped = min(max(float(p), 1e-6), 1.0 - 1e-6)
    return math.log(clipped / (1.0 - clipped))


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)


def _nll(logits: list[float], labels: list[int], temp: float) -> float:
    total = 0.0
    for z, y in zip(logits, labels, strict=True):
        p = min(max(_sigmoid(z / temp), 1e-12), 1.0 - 1e-12)
        total += -(y * math.log(p) + (1 - y) * math.log(1.0 - p))
    return total / len(labels)


def _brier(probs: list[float], labels: list[int]) -> float:
    return sum((p - y) ** 2 for p, y in zip(probs, labels, strict=True)) / len(labels)


def _ece_5bin(probs: list[float], labels: list[int]) -> dict[str, Any]:
    n = len(probs)
    ece = 0.0
    bins: list[dict[str, Any]] = []
    for b in range(5):
        lo, hi = b * 0.2, (b + 1) * 0.2
        idx = [
            i
            for i, p in enumerate(probs)
            if (lo <= p <= hi if b == 4 else lo <= p < hi)
        ]
        if idx:
            avg_p = sum(probs[i] for i in idx) / len(idx)
            avg_y = sum(labels[i] for i in idx) / len(idx)
            ece += (len(idx) / n) * abs(avg_p - avg_y)
            bins.append(
                {
                    "range": [round(lo, 1), round(hi, 1)],
                    "count": len(idx),
                    "mean_conf": round(avg_p, 6),
                    "empirical_acc": round(avg_y, 6),
                }
            )
        else:
            bins.append({"range": [round(lo, 1), round(hi, 1)], "count": 0, "mean_conf": None, "empirical_acc": None})
    return {"ece": round(ece, 6), "bins": bins}


def load_cached_audio_corpus(repo_root: Path) -> dict[str, Any]:
    """Load non-raw cached audio window scores and verify JSONL SHA-256 and CSV parity."""
    csv_path = repo_root / "docs/generated/professor_evidence/mission44/ALL_AUDIO_WINDOW_SCORES.csv"
    manifest_path = repo_root / "data/manifests/m3_multimodal_replay_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    csv_by_event: dict[str, list[tuple[int, float]]] = {}
    csv_labels: dict[str, str] = {}
    with csv_path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            ev = row["event"]
            csv_labels[ev] = row["adopted_event_horn_status"]
            csv_by_event.setdefault(ev, []).append((int(row["window_index"]), float(row["score"])))

    records: list[dict[str, Any]] = []
    sha_checks: list[dict[str, Any]] = []
    max_csv_jsonl_diff = 0.0
    for entry in manifest["events"]:
        ev = entry["event_id"]
        jsonl_path = repo_root / entry["audio_cache_path"]
        actual_sha = _sha256_file(jsonl_path)
        sha_match = actual_sha == entry["audio_cache_sha256"]
        sha_checks.append({"event_id": ev, "sha256_match": sha_match, "path": entry["audio_cache_path"]})
        jsonl_scores: list[float] = []
        with jsonl_path.open(encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                jsonl_scores.append(float(row["horn_confidence"]))
        if ev.startswith("train_events/"):
            csv_rows = sorted(csv_by_event[ev], key=lambda item: item[0])
            assert len(csv_rows) == len(jsonl_scores), f"Window count mismatch for {ev}"
            for (_, csv_s), js_s in zip(csv_rows, jsonl_scores, strict=True):
                max_csv_jsonl_diff = max(max_csv_jsonl_diff, abs(csv_s - js_s))
            label = 1 if csv_labels[ev] == "present" else 0
            cohort = "train_events"
        elif ev.startswith("no_train_events/"):
            label = None
            cohort = "no_train_events"
        else:
            label = None
            cohort = "engine_events"
        records.append({"event_id": ev, "cohort": cohort, "binary_label": label, "scores": jsonl_scores})

    return {
        "records": records,
        "manifest_sha256_all_match": all(x["sha256_match"] for x in sha_checks),
        "n_events_verified": len(sha_checks),
        "n_total_windows": sum(len(r["scores"]) for r in records),
        "max_csv_vs_jsonl_abs_diff": max_csv_jsonl_diff,
    }


def run_loeo_variant(
    records: list[dict[str, Any]],
    *,
    use_no_train_tiebreak: bool,
    temperatures: tuple[float, ...],
    n_bootstrap: int = 2000,
    seed: int = 20261114,
) -> dict[str, Any]:
    """Run independent 23-fold LOEO hysteresis + temperature calibration evaluation."""
    thresholds = (0.37, 0.50, 0.65, 0.75, 0.80, 0.85, 0.90, 0.95)
    k_values = (1, 2, 3, 4)
    labeled = [r for r in records if r["cohort"] == "train_events" and r["binary_label"] is not None]
    no_train = [r for r in records if r["cohort"] == "no_train_events"]
    raw_max = [max(r["scores"]) for r in labeled]
    labels = [int(r["binary_label"]) for r in labeled]
    raw_logits = [_logit(p) for p in raw_max]

    folds: list[dict[str, Any]] = []
    oof_preds: list[bool] = []
    oof_cal: list[float] = []
    sel_counter: Counter[tuple[float, int]] = Counter()
    ceiling = max(temperatures)

    for i, held in enumerate(labeled):
        train_sub = [r for j, r in enumerate(labeled) if j != i]
        tr_labels = [int(r["binary_label"]) for r in train_sub]
        best_choice: tuple[tuple[float, ...], float, int] | None = None
        for tau in thresholds:
            for k in k_values:
                tr_preds = [longest_run(r["scores"], tau) >= k for r in train_sub]
                m = classification_metrics(tr_preds, tr_labels)
                if use_no_train_tiebreak:
                    nt_fp = sum(1 for r in no_train if longest_run(r["scores"], tau) >= k)
                    key: tuple[float, ...] = (m["f1"], m["specificity"], float(-nt_fp), float(-tau))
                else:
                    key = (m["f1"], m["specificity"], float(-tau))
                if best_choice is None or key > best_choice[0]:
                    best_choice = (key, tau, k)
        assert best_choice is not None
        _, sel_tau, sel_k = best_choice
        sel_counter[(sel_tau, sel_k)] += 1

        tr_logits = [raw_logits[j] for j in range(len(labeled)) if j != i]
        best_temp = min(temperatures, key=lambda t: (_nll(tr_logits, tr_labels, t), t))
        oof_pred = longest_run(held["scores"], sel_tau) >= sel_k
        oof_prob = _sigmoid(raw_logits[i] / best_temp)
        oof_preds.append(oof_pred)
        oof_cal.append(oof_prob)
        folds.append(
            {
                "fold_event": held["event_id"],
                "true_label": int(held["binary_label"]),
                "selected_tau": sel_tau,
                "selected_k": sel_k,
                "selected_temp": best_temp,
                "temp_hit_ceiling": math.isclose(best_temp, ceiling),
                "oof_pred": oof_pred,
                "oof_raw_prob": round(raw_max[i], 6),
                "oof_cal_prob": round(oof_prob, 6),
            }
        )

    baseline_preds = [longest_run(r["scores"], 0.37) >= 1 for r in labeled]
    baseline_m = classification_metrics(baseline_preds, labels)
    oof_m = classification_metrics(oof_preds, labels)
    raw_brier = round(_brier(raw_max, labels), 6)
    cal_brier = round(_brier(oof_cal, labels), 6)
    raw_ece = _ece_5bin(raw_max, labels)
    cal_ece = _ece_5bin(oof_cal, labels)

    pos_idx = [i for i, y in enumerate(labels) if y == 1]
    neg_idx = [i for i, y in enumerate(labels) if y == 0]
    rng = random.Random(seed)
    boot_f1: list[float] = []
    boot_dbrier: list[float] = []
    for _ in range(n_bootstrap):
        sample = [rng.choice(pos_idx) for _ in pos_idx] + [rng.choice(neg_idx) for _ in neg_idx]
        sm = classification_metrics([oof_preds[idx] for idx in sample], [labels[idx] for idx in sample])
        boot_f1.append(sm["f1"])
        boot_dbrier.append(_brier([oof_cal[idx] for idx in sample], [labels[idx] for idx in sample]) - _brier([raw_max[idx] for idx in sample], [labels[idx] for idx in sample]))

    def _ci(vals: list[float]) -> dict[str, float]:
        s = sorted(vals)
        return {
            "mean": round(sum(s) / len(s), 6),
            "ci95_low": round(s[int(0.025 * (len(s) - 1))], 6),
            "ci95_high": round(s[int(0.975 * (len(s) - 1))], 6),
        }

    modal_tau, modal_k = sel_counter.most_common(1)[0][0]
    return {
        "config": {
            "use_no_train_tiebreak": use_no_train_tiebreak,
            "temp_min": min(temperatures),
            "temp_max": ceiling,
            "n_temp_grid": len(temperatures),
        },
        "baseline_metrics": baseline_m,
        "oof_metrics": oof_m,
        "wilson_95_ci": {
            "baseline_recall": wilson_ci(baseline_m["tp"], baseline_m["tp"] + baseline_m["fn"]),
            "oof_recall": wilson_ci(oof_m["tp"], oof_m["tp"] + oof_m["fn"]),
            "baseline_specificity": wilson_ci(baseline_m["tn"], baseline_m["tn"] + baseline_m["fp"]),
            "oof_specificity": wilson_ci(oof_m["tn"], oof_m["tn"] + oof_m["fp"]),
        },
        "calibration": {
            "raw_brier": raw_brier,
            "oof_cal_brier": cal_brier,
            "cal_minus_raw_brier": round(cal_brier - raw_brier, 6),
            "raw_ece_5bin": raw_ece["ece"],
            "oof_cal_ece_5bin": cal_ece["ece"],
            "raw_ece_bins": raw_ece["bins"],
            "oof_ece_bins": cal_ece["bins"],
            "temps_hitting_ceiling_count": sum(1 for f in folds if f["temp_hit_ceiling"]),
            "mean_selected_temp": round(sum(f["selected_temp"] for f in folds) / len(folds), 4),
            "max_selected_temp": max(f["selected_temp"] for f in folds),
        },
        "bootstrap_95_ci": {
            "oof_f1": _ci(boot_f1),
            "cal_minus_raw_brier": _ci(boot_dbrier),
            "cal_minus_raw_brier_crosses_zero": _ci(boot_dbrier)["ci95_low"] <= 0.0 <= _ci(boot_dbrier)["ci95_high"],
        },
        "fold_selection_counts": {f"tau={t}_k={k}": c for (t, k), c in sorted(sel_counter.items())},
        "modal_no_train_fp_at_selection": {
            "tau": modal_tau,
            "k": modal_k,
            "no_train_fp": sum(1 for r in no_train if longest_run(r["scores"], modal_tau) >= modal_k),
            "no_train_total": len(no_train),
        },
        "folds": folds,
    }


def validate_exp_r_independently(repo_root: Path) -> dict[str, Any]:
    """Compare independent cache recomputation against exp_r_crossval_and_failsafe.json + sensitivities."""
    corpus = load_cached_audio_corpus(repo_root)
    records = corpus["records"]

    t_grid_4 = tuple(round(0.5 + 0.1 * i, 2) for i in range(36))
    t_grid_15 = tuple(round(0.5 + 0.1 * i, 2) for i in range(146))

    reproduced = run_loeo_variant(records, use_no_train_tiebreak=True, temperatures=t_grid_4)
    strict_train_only = run_loeo_variant(records, use_no_train_tiebreak=False, temperatures=t_grid_4)
    uncapped_temp = run_loeo_variant(records, use_no_train_tiebreak=False, temperatures=t_grid_15)

    published_path = repo_root / "results/exploratory_v2/optimization_and_stress/exp_r_crossval_and_failsafe.json"
    published = json.loads(published_path.read_text(encoding="utf-8"))
    pub_loeo = published["loeo_acoustic_crossval"]

    fold_mismatches: list[str] = []
    max_prob_diff = 0.0
    for got, exp in zip(reproduced["folds"], pub_loeo["folds"], strict=True):
        if (
            got["fold_event"] != exp["fold_event"]
            or got["selected_tau"] != exp["selected_tau"]
            or got["selected_k"] != exp["selected_k"]
            or not math.isclose(got["selected_temp"], exp["selected_temp"], abs_tol=1e-6)
            or got["oof_pred"] != exp["oof_pred"]
        ):
            fold_mismatches.append(got["fold_event"])
        max_prob_diff = max(
            max_prob_diff,
            abs(got["oof_raw_prob"] - exp["oof_raw_prob"]),
            abs(got["oof_cal_prob"] - exp["oof_cal_prob"]),
        )

    pub_oof = pub_loeo["loeo_oof_hysteresis_metrics"]
    pub_cal = pub_loeo["oof_calibration"]
    oof_metrics_match = all(
        math.isclose(float(reproduced["oof_metrics"][k]), float(pub_oof[k]), abs_tol=1e-4)
        for k in ("tp", "fp", "tn", "fn", "recall", "specificity", "precision", "f1", "accuracy")
    )
    cal_match = (
        math.isclose(reproduced["calibration"]["oof_cal_brier"], float(pub_cal["oof_temp_scaled_brier"]), abs_tol=1e-4)
        and math.isclose(reproduced["calibration"]["oof_cal_ece_5bin"], float(pub_cal["oof_temp_scaled_ece_5bin"]), abs_tol=1e-4)
    )
    metrics_match = oof_metrics_match and cal_match and not fold_mismatches

    return {
        "schema_version": "exp-r-independent-validation/1.0",
        "raw_media_accessed": False,
        "corpus_verification": {
            "manifest_sha256_all_match": corpus["manifest_sha256_all_match"],
            "n_events_verified": corpus["n_events_verified"],
            "n_total_windows": corpus["n_total_windows"],
            "max_csv_vs_jsonl_abs_diff": corpus["max_csv_vs_jsonl_abs_diff"],
        },
        "published_artifact_reproduction": {
            "published_path": str(published_path.relative_to(repo_root)),
            "exact_match_within_published_4dp": metrics_match,
            "oof_metrics_match_within_4dp": oof_metrics_match,
            "calibration_match_within_4dp": cal_match,
            "fold_mismatches": fold_mismatches,
            "max_oof_prob_abs_diff": max_prob_diff,
        },
        "reproduced_published_loeo": reproduced,
        "sensitivity_1_strict_train_only_selection": strict_train_only,
        "sensitivity_2_uncapped_temp_grid_to_15": uncapped_temp,
        "methodological_audit_findings": {
            "f1_drops_vs_frozen_baseline": (
                reproduced["oof_metrics"]["f1"] < reproduced["baseline_metrics"]["f1"]
            ),
            "recall_drops_vs_frozen_baseline": (
                reproduced["oof_metrics"]["recall"] < reproduced["baseline_metrics"]["recall"]
            ),
            "brier_diff_ci_crosses_zero": reproduced["bootstrap_95_ci"]["cal_minus_raw_brier_crosses_zero"],
            "original_temp_ceiling_saturated_folds": reproduced["calibration"]["temps_hitting_ceiling_count"],
            "no_train_tiebreak_changed_folds": [
                a["fold_event"]
                for a, b in zip(reproduced["folds"], strict_train_only["folds"], strict=True)
                if (a["selected_tau"], a["selected_k"]) != (b["selected_tau"], b["selected_k"])
            ],
            "optical_wakeup_ablation_status": "SYNTHETIC_ONLY (default enable_optical_degradation_audio_wakeup=False)",
        },
    }
