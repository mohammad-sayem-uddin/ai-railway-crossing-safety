#!/usr/bin/env python3
"""Safety, timing, Convention A/B causality, V9 sensitivity, and stratification metrics.

Computes all event-level and cohort-level exploratory metrics from verified simulation
traces under `results/exploratory_execution/replays/traces/`, strictly separating:
- 11 calibrated sync-supported train events (`DUAL_VISION`, `DUAL_VISION_AUDIO`, paired `B0`/`B4`)
- 23 train events (independent-camera `B0`, `BACK_VISION`, `FRONT_AUDIO`, `AUDIO_ONLY`)
- 3 `no_train_events` negative controls
- 1 isolated `engine_events/event_001` case
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SCRIPTS_DIR = REPO_ROOT / "scripts"
for p in (str(SRC_DIR), str(SCRIPTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from exploratory_common import (  # noqa: E402
    EXPLORATORY_LABEL,
    load_verified_context,
    wilson_ci_95,
    write_verified_json,
)

from railway_detection.evaluation.metrics import M4_WINDOW  # noqa: E402
from railway_detection.fusion.rules import CrossingState, GateState  # noqa: E402


def compute_convention_b_closed_duration(steps: list[dict[str, Any]]) -> tuple[float, float, int]:
    """Compute counterfactual Forward-Causal Convention B closed duration from steps.

    In EventSimulationRunner (Convention A), PhysicalGateModel steps right after the
    decision at tick t_k, assigning duration dt_{k} = t_{k+1} - t_k to b_k (terminal
    step receives no post-step dt EXCEPT inside gate-state integration dt = t_k - t_{k-1}
    applied to post-step b_k). Specifically:
      - Conv A sums `b_k * (t_k - t_{k-1})` for k >= 1 (with t_0 having dt=0).
      - Conv B uses prior step state `b_{k-1}` over interval `[t_{k-1}, t_k)`:
        `sum(b_{k-1} * (t_k - t_{k-1}))` for k >= 1.
    Therefore `Conv B - Conv A = -dt * b_N` (assuming b_0 == False and uniform dt).
    """
    if len(steps) <= 1:
        b_last = 1 if (steps and steps[-1]["is_passage_blocked"]) else 0
        return (0.0, 0.0, b_last)

    conv_a = 0.0
    conv_b = 0.0
    for idx in range(1, len(steps)):
        dt = float(steps[idx]["t"]) - float(steps[idx - 1]["t"])
        if dt > 0.0:
            if steps[idx]["is_passage_blocked"]:
                conv_a += dt
            if steps[idx - 1]["is_passage_blocked"]:
                conv_b += dt
    b_last = 1 if steps[-1]["is_passage_blocked"] else 0
    return (round(conv_a, 6), round(conv_b, 6), b_last)


def _check_v9_legacy_premature(
    steps: list[dict[str, Any]], t1: float | None, t4: float | None
) -> bool | None:
    """Evaluate legacy pre-M4 premature opening definition: unblocked inside [T1, T4)."""
    if t1 is None or t4 is None:
        return None
    return any(
        t1 <= step["t"] < t4
        and not step["is_passage_blocked"]
        and step["gate_state"] in (GateState.OPEN.value, GateState.OPENING.value)
        for step in steps
    )


def _count_false_alarm_episodes(steps: list[dict[str, Any]]) -> int:
    episodes = 0
    in_blocked = False
    for s in steps:
        blocked_or_closing = s["is_passage_blocked"] or s["crossing_state"] not in (
            CrossingState.IDLE.value,
            CrossingState.FAULT_FAIL_SAFE.value,
        )
        if blocked_or_closing and not in_blocked:
            episodes += 1
            in_blocked = True
        elif not blocked_or_closing:
            in_blocked = False
    return episodes


def _mean_or_none(vals: list[float]) -> float | None:
    if not vals:
        return None
    return round(sum(vals) / len(vals), 4)


def run_compute_safety_metrics(
    ctx: Any, *, output_dir: Path
) -> dict[str, Any]:
    replay_path = output_dir / "replays" / "replay_summary.json"
    with open(replay_path, "r", encoding="utf-8", newline="") as f:
        replay_summary = json.load(f)

    event_rows: list[dict[str, Any]] = []
    by_run_label: dict[str, list[dict[str, Any]]] = {}

    for entry in replay_summary["runs"]:
        trace_path = output_dir / entry["trace_relpath"]
        with open(trace_path, "r", encoding="utf-8", newline="") as f:
            trace = json.load(f)

        ev_id = trace["event_id"]
        ref = ctx.references[ev_id]
        steps = trace["steps"]
        em = trace["evaluation_metrics"]
        bounds = trace["mapped_boundaries"]
        t1, t4 = bounds.get("t1"), bounds.get("t4")

        conv_a_calc, conv_b_calc, b_last = compute_convention_b_closed_duration(steps)
        diff_b_minus_a = round(conv_b_calc - float(trace["closed_duration_s"]), 6)

        first_warn_t = next(
            (s["t"] for s in steps if s["crossing_state"] == CrossingState.WARNING.value),
            None,
        )
        first_blocked_t = em.get("first_blocked_s")
        signed_lead_to_t1 = (
            round(t1 - first_warn_t, 6)
            if (t1 is not None and first_warn_t is not None)
            else None
        )
        block_margin_to_t1 = (
            round(t1 - first_blocked_t, 6)
            if (t1 is not None and first_blocked_t is not None)
            else None
        )
        v9_legacy_prem = _check_v9_legacy_premature(steps, t1, t4)

        row = {
            "run_label": entry["run_label"],
            "condition": entry["condition"],
            "policy": entry["policy"],
            "scope_mode": entry["scope_mode"],
            "event_id": ev_id,
            "cohort": ref.cohort,
            "lighting": ref.lighting,
            "horn_status": ref.horn_status,
            "is_dual_sync_accepted": ref.is_dual_sync_accepted,
            "t0_censored": ref.t0_ambiguity,
            "t1_s": t1,
            "t4_s": t4,
            "evaluable": em["evaluable"],
            "missed_train": em["missed_train"],
            "false_alarm": em["false_alarm"],
            "false_alarm_episodes": (
                _count_false_alarm_episodes(steps) if ref.cohort == "no_train_events" else None
            ),
            "premature_opening_m4": em["premature_opening_m4"],
            "m4_status_detail": em["m4_status_detail"],
            "m4_margin_s": em["m4_margin_s"],
            "legacy_v9_premature_t1_to_t4": v9_legacy_prem,
            "never_protected": em["never_protected"],
            "first_warning_s": first_warn_t,
            "first_blocked_s": first_blocked_t,
            "signed_warning_lead_to_t1_s": signed_lead_to_t1,
            "warning_lead_clamped_s": em["warning_lead_time_s"],
            "protection_margin_to_t1_s": block_margin_to_t1,
            "first_crossing_clear_s": em["first_crossing_clear_s"],
            "first_unblocked_after_clear_s": em["first_unblocked_after_clear_s"],
            "total_duration_s": trace["total_duration_s"],
            "closed_duration_conv_a_s": trace["closed_duration_s"],
            "closed_duration_conv_b_s": conv_b_calc,
            "terminal_blocked_flag_bN": b_last,
            "conv_b_minus_conv_a_s": diff_b_minus_a,
            "blocked_fraction": em["blocked_fraction"],
            "transition_count": entry["transition_count"],
            "final_crossing_state": trace["final_crossing_state"],
            "final_gate_state": trace["final_gate_state"],
        }
        event_rows.append(row)
        by_run_label.setdefault(entry["run_label"], []).append(row)

    # Aggregate strictly separated cohorts for every run_label
    cohort_summaries: list[dict[str, Any]] = []
    for run_label, rows in by_run_label.items():
        sample_row = rows[0]
        train_rows = [r for r in rows if r["cohort"] == "train_events"]
        sync11_train_rows = [r for r in train_rows if r["is_dual_sync_accepted"]]
        no_train_rows = [r for r in rows if r["cohort"] == "no_train_events"]
        engine_rows = [r for r in rows if r["cohort"] == "engine_events"]

        def _agg_train(sub: list[dict[str, Any]], slice_name: str) -> dict[str, Any] | None:
            if not sub:
                return None
            n_tr = len(sub)
            missed_eval_rows = [r for r in sub if r["missed_train"] is not None]
            missed_n = sum(1 for r in missed_eval_rows if r["missed_train"] is True)
            zero_prot_n = sum(1 for r in sub if r["first_blocked_s"] is None)
            late_only_n = sum(
                1 for r in missed_eval_rows if r["missed_train"] is True and r["first_blocked_s"] is not None
            )
            never_prot_n = sum(1 for r in sub if r["never_protected"] is True)
            m4_eval_rows = [r for r in sub if r["premature_opening_m4"] is not None]
            m4_prem_n = sum(1 for r in m4_eval_rows if r["premature_opening_m4"] is True)
            v9_eval_rows = [r for r in sub if r["legacy_v9_premature_t1_to_t4"] is not None]
            v9_prem_n = sum(1 for r in v9_eval_rows if r["legacy_v9_premature_t1_to_t4"] is True)
            clear_n = sum(1 for r in sub if r["first_crossing_clear_s"] is not None)
            missed_ci = wilson_ci_95(missed_n, len(missed_eval_rows))
            zero_ci = wilson_ci_95(zero_prot_n, n_tr)
            m4_ci = wilson_ci_95(m4_prem_n, len(m4_eval_rows))
            return {
                "run_label": run_label,
                "condition": sample_row["condition"],
                "policy": sample_row["policy"],
                "cohort_slice": slice_name,
                "train_events_n": n_tr,
                "missed_train_evaluable_n": len(missed_eval_rows),
                "missed_train_n": missed_n,
                "missed_train_rate": round(missed_ci[0], 6) if missed_eval_rows else None,
                "missed_train_ci95": (
                    [round(missed_ci[1], 4), round(missed_ci[2], 4)] if missed_eval_rows else None
                ),
                "late_closure_after_t1_n": late_only_n,
                "zero_protection_n": zero_prot_n,
                "zero_protection_rate": round(zero_ci[0], 6),
                "zero_protection_ci95": [round(zero_ci[1], 4), round(zero_ci[2], 4)],
                "m4_never_protected_n": never_prot_n,
                "m4_evaluable_n": len(m4_eval_rows),
                "m4_excluded_ids": [r["event_id"] for r in sub if r["premature_opening_m4"] is None],
                "m4_premature_n": m4_prem_n,
                "m4_premature_rate": round(m4_ci[0], 6) if m4_eval_rows else None,
                "m4_premature_ci95": (
                    [round(m4_ci[1], 4), round(m4_ci[2], 4)] if m4_eval_rows else None
                ),
                "legacy_v9_evaluable_n": len(v9_eval_rows),
                "legacy_v9_premature_n": v9_prem_n,
                "reached_crossing_clear_n": clear_n,
                "mean_closed_conv_a_s": _mean_or_none([r["closed_duration_conv_a_s"] for r in sub]),
                "mean_closed_conv_b_s": _mean_or_none([r["closed_duration_conv_b_s"] for r in sub]),
                "mean_blocked_fraction": _mean_or_none([r["blocked_fraction"] for r in sub]),
                "mean_transitions": _mean_or_none([float(r["transition_count"]) for r in sub]),
                "mean_warning_lead_clamped_s": _mean_or_none(
                    [r["warning_lead_clamped_s"] for r in sub if r["warning_lead_clamped_s"] is not None]
                ),
                "day_train_n": sum(1 for r in sub if r["lighting"] == "day"),
                "day_missed_n": sum(1 for r in sub if r["lighting"] == "day" and r["missed_train"] is True),
                "night_train_n": sum(1 for r in sub if r["lighting"] == "night"),
                "night_missed_n": sum(1 for r in sub if r["lighting"] == "night" and r["missed_train"] is True),
            }

        agg_sync = _agg_train(sync11_train_rows, "sync11_CALIBRATION_SUPPORTED")
        if agg_sync is not None:
            cohort_summaries.append(agg_sync)
        if sample_row["scope_mode"] == "all27":
            agg_all = _agg_train(train_rows, "all23_independent_train")
            if agg_all is not None:
                cohort_summaries.append(agg_all)

            nt_fa_n = sum(1 for r in no_train_rows if r["false_alarm"] is True)
            nt_ci = wilson_ci_95(nt_fa_n, len(no_train_rows))
            cohort_summaries.append(
                {
                    "run_label": run_label,
                    "condition": sample_row["condition"],
                    "policy": sample_row["policy"],
                    "cohort_slice": "no_train_controls_3",
                    "no_train_n": len(no_train_rows),
                    "false_alarm_events_n": nt_fa_n,
                    "false_alarm_rate": round(nt_ci[0], 6),
                    "false_alarm_ci95": [round(nt_ci[1], 4), round(nt_ci[2], 4)],
                    "total_false_alarm_episodes": sum(
                        r["false_alarm_episodes"] or 0 for r in no_train_rows
                    ),
                    "total_blocked_s": round(
                        sum(r["closed_duration_conv_a_s"] for r in no_train_rows), 4
                    ),
                    "mean_blocked_fraction": _mean_or_none([r["blocked_fraction"] for r in no_train_rows]),
                    "engine_event_isolated": (
                        {
                            "event_id": engine_rows[0]["event_id"],
                            "final_state": engine_rows[0]["final_crossing_state"],
                            "blocked_fraction": engine_rows[0]["blocked_fraction"],
                            "closed_duration_conv_a_s": engine_rows[0]["closed_duration_conv_a_s"],
                            "closed_duration_conv_b_s": engine_rows[0]["closed_duration_conv_b_s"],
                            "never_protected": engine_rows[0]["never_protected"],
                        }
                        if engine_rows
                        else None
                    ),
                }
            )

    # Check Convention B - Convention A identity globally
    conv_diffs = sorted({r["conv_b_minus_conv_a_s"] for r in event_rows})
    non_zero_terminal_diffs = [
        r["conv_b_minus_conv_a_s"] for r in event_rows if r["terminal_blocked_flag_bN"] == 1
    ]

    analysis_dir = output_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    csv_path = analysis_dir / "event_level_safety_metrics.csv"
    csv_fields = [
        "run_label",
        "condition",
        "policy",
        "scope_mode",
        "event_id",
        "cohort",
        "lighting",
        "is_dual_sync_accepted",
        "t1_s",
        "t4_s",
        "missed_train",
        "false_alarm",
        "premature_opening_m4",
        "m4_status_detail",
        "m4_margin_s",
        "legacy_v9_premature_t1_to_t4",
        "never_protected",
        "warning_lead_clamped_s",
        "first_crossing_clear_s",
        "closed_duration_conv_a_s",
        "closed_duration_conv_b_s",
        "conv_b_minus_conv_a_s",
        "blocked_fraction",
        "transition_count",
        "final_crossing_state",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        for r in event_rows:
            writer.writerow({k: r[k] for k in csv_fields})

    out_payload = {
        "exploratory_label": EXPLORATORY_LABEL,
        "premature_opening_windows_catalog": [M4_WINDOW, "entry_to_t4_clearance_legacy_v9"],
        "convention_b_vs_a_verification": {
            "unique_conv_b_minus_a_values_s": conv_diffs,
            "terminal_blocked_unique_diffs_s": sorted(set(non_zero_terminal_diffs)),
            "verified_exact_identity": all(abs(d + 0.2) < 1e-6 or abs(d) < 1e-6 for d in conv_diffs),
        },
        "cohort_summaries": cohort_summaries,
        "total_event_rows": len(event_rows),
        "event_rows": event_rows,
    }
    sha = write_verified_json(analysis_dir / "safety_metrics_summary.json", out_payload)
    return {"sha256": sha, "total_event_rows": len(event_rows), "summary_groups": len(cohort_summaries)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute safety, M4, and Convention A/B metrics.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "results" / "exploratory_execution",
    )
    args = parser.parse_args(argv)
    ctx = load_verified_context(REPO_ROOT)
    res = run_compute_safety_metrics(ctx, output_dir=args.output_dir)
    print(f"[DONE] event_rows={res['total_event_rows']}, summary_groups={res['summary_groups']}, sha256={res['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
