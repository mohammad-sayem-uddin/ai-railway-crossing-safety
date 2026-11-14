#!/usr/bin/env python3
"""EXP-L: Fair Paired Ablation Matrix & Exact McNemar Discordance Analysis.

Compares policy, modality, and temporal arms strictly within identical event scopes:
- Paired 11 CALIBRATION_SUPPORTED sync events (B0, B2/DUAL_VISION, B4/FRONT_AUDIO,
  B7/DUAL_VISION_AUDIO V1 & V2, and Stateless comparators)
- Paired 23 independent-camera train events (+ 3 no_train controls)
"""

from __future__ import annotations

import argparse
import csv
import json
import math
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


def exact_mcnemar_pvalue(n01: int, n10: int) -> float:
    """Exact two-sided binomial McNemar p-value for discordant pairs (n01, n10)."""
    n_disc = n01 + n10
    if n_disc == 0:
        return 1.0
    k = min(n01, n10)
    tail = sum(math.comb(n_disc, i) for i in range(k + 1)) / (2 ** n_disc)
    return round(min(1.0, 2.0 * tail), 6)


def _load_metrics(output_dir: Path) -> dict[str, Any]:
    with open(
        output_dir / "analysis" / "safety_metrics_summary.json",
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        return json.load(f)


def _index_rows(event_rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(r["run_label"], r["event_id"]): r for r in event_rows}


def _arm_summary_row(
    *,
    scope: str,
    ablation_factor: str,
    run_label: str,
    rows: list[dict[str, Any]],
    no_train_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    n_tr = len(rows)
    missed_eval_rows = [r for r in rows if r["missed_train"] is not None]
    missed = sum(1 for r in missed_eval_rows if r["missed_train"] is True)
    zero_prot = sum(1 for r in rows if r["first_blocked_s"] is None)
    never_prot = sum(1 for r in rows if r["never_protected"] is True)
    m4_rows = [r for r in rows if r["premature_opening_m4"] is not None]
    m4_prem = sum(1 for r in m4_rows if r["premature_opening_m4"] is True)
    cleared = sum(1 for r in rows if r["first_crossing_clear_s"] is not None)
    missed_ci = wilson_ci_95(missed, len(missed_eval_rows))
    zero_ci = wilson_ci_95(zero_prot, n_tr)
    m4_ci = wilson_ci_95(m4_prem, len(m4_rows))

    nt_fa = (
        sum(1 for r in no_train_rows if r["false_alarm"] is True)
        if no_train_rows is not None
        else None
    )
    nt_episodes = (
        sum(r["false_alarm_episodes"] or 0 for r in no_train_rows)
        if no_train_rows is not None
        else None
    )
    nt_blocked_s = (
        round(sum(r["closed_duration_conv_a_s"] for r in no_train_rows), 4)
        if no_train_rows is not None
        else None
    )
    lead_vals = [r["warning_lead_clamped_s"] for r in rows if r["warning_lead_clamped_s"] is not None]
    return {
        "scope": scope,
        "ablation_factor": ablation_factor,
        "run_label": run_label,
        "train_n": n_tr,
        "missed_train_evaluable_n": len(missed_eval_rows),
        "missed_train_n": missed if missed_eval_rows else None,
        "missed_train_rate": round(missed_ci[0], 4) if missed_eval_rows else None,
        "missed_train_ci95": f"[{missed_ci[1]:.4f}, {missed_ci[2]:.4f}]" if missed_eval_rows else "N/A",
        "zero_protection_n": zero_prot,
        "zero_protection_rate": round(zero_ci[0], 4),
        "zero_protection_ci95": f"[{zero_ci[1]:.4f}, {zero_ci[2]:.4f}]",
        "m4_never_protected_n": never_prot,
        "m4_evaluable_n": len(m4_rows),
        "m4_premature_n": m4_prem,
        "m4_premature_rate": round(m4_ci[0], 4) if m4_rows else None,
        "m4_premature_ci95": f"[{m4_ci[1]:.4f}, {m4_ci[2]:.4f}]" if m4_rows else "N/A",
        "reached_clear_n": cleared,
        "mean_warning_lead_s": round(sum(lead_vals) / len(lead_vals), 4) if lead_vals else None,
        "mean_closed_conv_a_s": round(
            sum(r["closed_duration_conv_a_s"] for r in rows) / n_tr, 4
        )
        if n_tr
        else None,
        "mean_closed_conv_b_s": round(
            sum(r["closed_duration_conv_b_s"] for r in rows) / n_tr, 4
        )
        if n_tr
        else None,
        "mean_blocked_fraction": round(sum(r["blocked_fraction"] for r in rows) / n_tr, 4)
        if n_tr
        else None,
        "mean_transitions": round(sum(r["transition_count"] for r in rows) / n_tr, 4)
        if n_tr
        else None,
        "no_train_false_alarm_n": nt_fa,
        "no_train_false_alarm_episodes": nt_episodes,
        "no_train_blocked_s": nt_blocked_s,
    }


def _paired_contrast(
    *,
    name: str,
    research_question: str,
    arm_a: str,
    arm_b: str,
    event_ids: list[str],
    idx: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    outcomes: dict[str, Any] = {}
    for metric in ("premature_opening_m4", "missed_train"):
        a_only, b_only, both_true, both_false = [], [], [], []
        excluded = []
        for ev in event_ids:
            va = idx[(arm_a, ev)][metric]
            vb = idx[(arm_b, ev)][metric]
            if va is None or vb is None:
                excluded.append(ev)
                continue
            if va and not vb:
                a_only.append(ev)
            elif vb and not va:
                b_only.append(ev)
            elif va and vb:
                both_true.append(ev)
            else:
                both_false.append(ev)
        outcomes[metric] = {
            "evaluable_n": len(event_ids) - len(excluded),
            "excluded": excluded,
            "a_true_b_false": len(a_only),
            "a_true_b_false_ids": a_only,
            "a_false_b_true": len(b_only),
            "a_false_b_true_ids": b_only,
            "both_true": len(both_true),
            "both_false": len(both_false),
            "exact_mcnemar_p": exact_mcnemar_pvalue(len(a_only), len(b_only)),
        }

    # Clearance reached & zero_protection comparisons
    a_clear_only, b_clear_only = [], []
    a_zp_only, b_zp_only = [], []
    for ev in event_ids:
        ca = idx[(arm_a, ev)]["first_crossing_clear_s"] is not None
        cb = idx[(arm_b, ev)]["first_crossing_clear_s"] is not None
        if ca and not cb:
            a_clear_only.append(ev)
        elif cb and not ca:
            b_clear_only.append(ev)

        zpa = idx[(arm_a, ev)]["first_blocked_s"] is None
        zpb = idx[(arm_b, ev)]["first_blocked_s"] is None
        if zpa and not zpb:
            a_zp_only.append(ev)
        elif zpb and not zpa:
            b_zp_only.append(ev)

    outcomes["reached_crossing_clear"] = {
        "evaluable_n": len(event_ids),
        "a_clear_b_not": len(a_clear_only),
        "a_clear_b_not_ids": a_clear_only,
        "b_clear_a_not": len(b_clear_only),
        "b_clear_a_not_ids": b_clear_only,
        "exact_mcnemar_p": exact_mcnemar_pvalue(len(a_clear_only), len(b_clear_only)),
    }
    outcomes["zero_protection"] = {
        "evaluable_n": len(event_ids),
        "a_zero_b_prot": len(a_zp_only),
        "a_zero_b_prot_ids": a_zp_only,
        "b_zero_a_prot": len(b_zp_only),
        "b_zero_a_prot_ids": b_zp_only,
        "exact_mcnemar_p": exact_mcnemar_pvalue(len(a_zp_only), len(b_zp_only)),
    }

    closed_deltas = [
        round(
            idx[(arm_b, ev)]["closed_duration_conv_a_s"]
            - idx[(arm_a, ev)]["closed_duration_conv_a_s"],
            6,
        )
        for ev in event_ids
    ]
    trans_deltas = [
        idx[(arm_b, ev)]["transition_count"] - idx[(arm_a, ev)]["transition_count"]
        for ev in event_ids
    ]
    return {
        "contrast_name": name,
        "research_question": research_question,
        "arm_a": arm_a,
        "arm_b": arm_b,
        "paired_events_n": len(event_ids),
        "binary_discordance": outcomes,
        "mean_closed_duration_delta_b_minus_a_s": round(
            sum(closed_deltas) / len(closed_deltas), 4
        )
        if closed_deltas
        else None,
        "mean_transition_delta_b_minus_a": round(sum(trans_deltas) / len(trans_deltas), 4)
        if trans_deltas
        else None,
    }


def run_ablation_matrix(ctx: Any, *, output_dir: Path) -> dict[str, Any]:
    metrics_data = _load_metrics(output_dir)
    idx = _index_rows(metrics_data["event_rows"])

    sync11_ids = sorted(ctx.accepted_sync_events)
    all23_train_ids = [ev for ev in ctx.event_order if ev.startswith("train_events/")]
    no_train_ids = [ev for ev in ctx.event_order if ev.startswith("no_train_events/")]

    sync11_arms = [
        ("B0__v2", "Front vision only (V2)"),
        ("DUAL_VISION__v2", "B2: Front + Back calibrated vision (V2)"),
        ("FRONT_AUDIO__v2", "B4: Front vision + front audio (V2)"),
        ("DUAL_VISION_AUDIO__v2", "B7: Full dual vision + audio (V2 Primary)"),
        ("DUAL_VISION_AUDIO__v1", "B7 baseline: Full dual vision + audio (Frozen V1)"),
        ("DUAL_VISION_AUDIO__stateless_rule2", "EXP-E: Stateless vision-trigger threshold (RULE_2)"),
        ("DUAL_VISION_AUDIO__stateless_union", "EXP-E: Stateless audio-or-vision union threshold"),
    ]
    indep23_arms = [
        ("B0__v2", "Front vision only (V2)"),
        ("B0__v1", "Front vision only (Frozen V1)"),
        ("B0__stateless_rule2", "Front vision only (Stateless)"),
        ("BACK_VISION__v2", "Back vision only on local back clock (V2)"),
        ("BACK_VISION__v1", "Back vision only on local back clock (Frozen V1)"),
        ("AUDIO_ONLY__v2", "Audio only (V2, RULE_2 non-actuation check)"),
        ("FRONT_AUDIO__v2", "Front vision + front audio (V2)"),
        ("FRONT_AUDIO__v1", "Front vision + front audio (Frozen V1)"),
        ("FRONT_AUDIO__stateless_rule2", "Front + audio (Stateless RULE_2)"),
        ("FRONT_AUDIO__stateless_union", "Front + audio (Stateless OR-union)"),
    ]

    matrix_rows: list[dict[str, Any]] = []
    for label, factor in sync11_arms:
        matrix_rows.append(
            _arm_summary_row(
                scope="11_sync_train",
                ablation_factor=factor,
                run_label=label,
                rows=[idx[(label, ev)] for ev in sync11_ids],
            )
        )
    for label, factor in indep23_arms:
        matrix_rows.append(
            _arm_summary_row(
                scope="23_independent_train_+_3_no_train",
                ablation_factor=factor,
                run_label=label,
                rows=[idx[(label, ev)] for ev in all23_train_ids],
                no_train_rows=[idx[(label, ev)] for ev in no_train_ids],
            )
        )

    contrasts = [
        _paired_contrast(
            name="Primary_Q1_B0_vs_B7_sync11",
            research_question="Does synchronized two-camera + audio + V2 policy change outcomes vs front-only B0?",
            arm_a="B0__v2",
            arm_b="DUAL_VISION_AUDIO__v2",
            event_ids=sync11_ids,
            idx=idx,
        ),
        _paired_contrast(
            name="Vision_only_B0_vs_B2_DualVision_sync11",
            research_question="Isolated contribution of calibrated back camera (vision-only) on 11 sync events.",
            arm_a="B0__v2",
            arm_b="DUAL_VISION__v2",
            event_ids=sync11_ids,
            idx=idx,
        ),
        _paired_contrast(
            name="Audio_contribution_DualVision_vs_DualVisionAudio_sync11",
            research_question="Isolated contribution of front audio on calibrated dual-camera system (11 sync events).",
            arm_a="DUAL_VISION__v2",
            arm_b="DUAL_VISION_AUDIO__v2",
            event_ids=sync11_ids,
            idx=idx,
        ),
        _paired_contrast(
            name="BackCamera_on_Audio_B4_vs_B7_sync11",
            research_question="Isolated contribution of calibrated back camera when audio is already present.",
            arm_a="FRONT_AUDIO__v2",
            arm_b="DUAL_VISION_AUDIO__v2",
            event_ids=sync11_ids,
            idx=idx,
        ),
        _paired_contrast(
            name="Audio_contribution_Front_B0_vs_B4_all23",
            research_question="Isolated contribution of audio on front-camera baseline (23 independent train events).",
            arm_a="B0__v2",
            arm_b="FRONT_AUDIO__v2",
            event_ids=all23_train_ids,
            idx=idx,
        ),
        _paired_contrast(
            name="Policy_V1_vs_V2_on_B7_sync11",
            research_question="EXP-J: Frozen V1 vs Adopted V2 policy on identical DUAL_VISION_AUDIO inputs (11 sync events).",
            arm_a="DUAL_VISION_AUDIO__v1",
            arm_b="DUAL_VISION_AUDIO__v2",
            event_ids=sync11_ids,
            idx=idx,
        ),
        _paired_contrast(
            name="Temporal_V2_vs_Stateless_RULE2_on_B7_sync11",
            research_question="EXP-E: Temporal state machine (V2) vs Stateless threshold (RULE_2) on identical B7 inputs.",
            arm_a="DUAL_VISION_AUDIO__stateless_rule2",
            arm_b="DUAL_VISION_AUDIO__v2",
            event_ids=sync11_ids,
            idx=idx,
        ),
        _paired_contrast(
            name="Temporal_V2_vs_Stateless_Union_on_B7_sync11",
            research_question="EXP-E: Temporal state machine (V2) vs Stateless OR-union on identical B7 inputs.",
            arm_a="DUAL_VISION_AUDIO__stateless_union",
            arm_b="DUAL_VISION_AUDIO__v2",
            event_ids=sync11_ids,
            idx=idx,
        ),
        _paired_contrast(
            name="Temporal_V2_vs_Stateless_RULE2_on_Front_all23",
            research_question="EXP-E: Temporal V2 vs Stateless on 23 independent front-camera train events.",
            arm_a="B0__stateless_rule2",
            arm_b="B0__v2",
            event_ids=all23_train_ids,
            idx=idx,
        ),
    ]

    analysis_dir = output_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    csv_path = analysis_dir / "ablation_matrix.csv"
    fields = list(matrix_rows[0].keys())
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in matrix_rows:
            writer.writerow(r)

    sha = write_verified_json(
        analysis_dir / "ablation_matrix.json",
        {
            "exploratory_label": EXPLORATORY_LABEL,
            "ablation_rows": matrix_rows,
            "paired_contrasts": contrasts,
        },
    )
    return {"sha256": sha, "arms_count": len(matrix_rows), "contrasts_count": len(contrasts)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute EXP-L paired ablation matrix.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "results" / "exploratory_execution",
    )
    args = parser.parse_args(argv)
    ctx = load_verified_context(REPO_ROOT)
    out = run_ablation_matrix(ctx, output_dir=args.output_dir)
    print(f"[DONE] arms={out['arms_count']}, contrasts={out['contrasts_count']}, sha256={out['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
