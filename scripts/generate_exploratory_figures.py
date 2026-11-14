#!/usr/bin/env python3
"""Generate publication figures for exploratory Train Gate Automation analysis.

Reads ONLY deterministic JSON/CSV artifacts under results/exploratory_execution/
and writes high-resolution PNG figures into docs/generated/final_research/figures/.
Never accesses raw media files, checkpoints, or repository protected assets.
"""

from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
EXPLORATORY_DIR = REPO_ROOT / "results" / "exploratory_execution"
ANALYSIS_DIR = EXPLORATORY_DIR / "analysis"
REPLAY_SUMMARY_PATH = EXPLORATORY_DIR / "replays" / "replay_summary.json"
FAILURE_PATH = EXPLORATORY_DIR / "failure_injection" / "stress_and_recovery_results.json"
FIGURES_DIR = REPO_ROOT / "docs" / "generated" / "final_research" / "figures"

DISCLAIMER = "Exploratory evaluation against researcher-adopted AI-assisted reference annotations."


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _parse_ci(ci_str: str) -> tuple[float, float]:
    vals = ast.literal_eval(ci_str)
    return float(vals[0]), float(vals[1])


def _setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 180,
            "savefig.dpi": 220,
            "font.family": "DejaVu Sans",
            "font.size": 9.5,
            "axes.titlesize": 10.5,
            "axes.titleweight": "bold",
            "axes.labelsize": 9.5,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "legend.fontsize": 8.2,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
        }
    )


def generate_fig1_ablation_rates(ablation_data: dict[str, Any]) -> Path:
    """Plot ablation matrix rates with 95% Wilson CIs across sync11 and all23 cohorts."""
    rows = ablation_data["ablation_rows"]
    sync11_order = [
        ("B0__v2", "B0 Front Only (V2)"),
        ("FRONT_AUDIO__v2", "B4 Front+Audio (V2)"),
        ("DUAL_VISION__v2", "B2 Dual Vision (V2)"),
        ("DUAL_VISION_AUDIO__v2", "B7 Dual+Audio (V2)"),
        ("DUAL_VISION_AUDIO__v1", "B7 Dual+Audio (V1)"),
        ("DUAL_VISION_AUDIO__stateless_rule2", "B7 Stateless RULE_2"),
        ("DUAL_VISION_AUDIO__stateless_union", "B7 Stateless Union"),
    ]
    all23_order = [
        ("B0__v2", "B0 Front Only (V2)"),
        ("B0__v1", "B0 Front Only (V1)"),
        ("B0__stateless_rule2", "B0 Stateless RULE_2"),
        ("BACK_VISION__v2", "Back Vision (V2)"),
        ("AUDIO_ONLY__v2", "Audio Only (V2)"),
        ("FRONT_AUDIO__v2", "B4 Front+Audio (V2)"),
        ("FRONT_AUDIO__stateless_union", "B4 Stateless Union"),
    ]

    lookup = {(r["scope"], r["run_label"]): r for r in rows}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.8), constrained_layout=True)

    # Panel A: 11 calibrated dual-camera events
    y1 = np.arange(len(sync11_order))
    zp_rates, zp_err_lo, zp_err_hi, zp_txt = [], [], [], []
    blk_fracs, m4_rates, m4_txt = [], [], []
    for label, _ in sync11_order:
        r = lookup[("11_sync_train", label)]
        p = float(r["zero_protection_rate"])
        lo, hi = _parse_ci(r["zero_protection_ci95"])
        zp_rates.append(p * 100.0)
        zp_err_lo.append((p - lo) * 100.0)
        zp_err_hi.append((hi - p) * 100.0)
        zp_txt.append(f"{r['zero_protection_n']}/{r['train_n']}")
        blk_fracs.append(float(r["mean_blocked_fraction"]) * 100.0)
        m4_r = float(r["m4_premature_rate"]) if r["m4_premature_rate"] is not None else np.nan
        m4_rates.append(m4_r * 100.0)
        m4_txt.append(f"{r['m4_premature_n']}/{r['m4_evaluable_n']}")

    h = 0.26
    bars1 = ax1.barh(y1 - h, zp_rates, height=h, color="#d95f02", label="Zero Protection % (95% Wilson CI)")
    ax1.errorbar(zp_rates, y1 - h, xerr=[zp_err_lo, zp_err_hi], fmt="none", ecolor="#7f2704", elinewidth=1.3, capsize=3)
    bars2 = ax1.barh(y1, m4_rates, height=h, color="#7570b3", label="M4 Premature Opening % (k/eval)")
    bars3 = ax1.barh(y1 + h, blk_fracs, height=h, color="#1b9e77", label="Mean Blocked Fraction %")

    for i, b in enumerate(bars1):
        ax1.text(zp_rates[i] + zp_err_hi[i] + 1.5, b.get_y() + b.get_height() / 2, zp_txt[i], va="center", fontsize=8, color="#7f2704", fontweight="bold")
    for i, b in enumerate(bars2):
        ax1.text(m4_rates[i] + 1.5, b.get_y() + b.get_height() / 2, m4_txt[i], va="center", fontsize=8, color="#3f3b72")
    for i, b in enumerate(bars3):
        ax1.text(blk_fracs[i] + 1.5, b.get_y() + b.get_height() / 2, f"{blk_fracs[i]:.1f}%", va="center", fontsize=8, color="#0d5c45")

    ax1.set_yticks(y1)
    ax1.set_yticklabels([disp for _, disp in sync11_order])
    ax1.invert_yaxis()
    ax1.set_xlim(0, 122)
    ax1.set_xlabel("Percentage (%)")
    ax1.set_title("A. Calibrated Dual-Camera Cohort (N = 11 Sync Events)")
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2, frameon=True, framealpha=0.95)

    # Panel B: 23 independent train + 3 no-train controls
    y2 = np.arange(len(all23_order))
    zp2, zp2_lo, zp2_hi, zp2_txt = [], [], [], []
    blk2, fa_s2, fa_txt2 = [], [], []
    for label, _ in all23_order:
        r = lookup[("23_independent_train_+_3_no_train", label)]
        p = float(r["zero_protection_rate"])
        lo, hi = _parse_ci(r["zero_protection_ci95"])
        zp2.append(p * 100.0)
        zp2_lo.append((p - lo) * 100.0)
        zp2_hi.append((hi - p) * 100.0)
        zp2_txt.append(f"{r['zero_protection_n']}/{r['train_n']}")
        blk2.append(float(r["mean_blocked_fraction"]) * 100.0)
        fa_val = float(r["no_train_blocked_s"]) if r["no_train_blocked_s"] is not None else 0.0
        fa_s2.append(fa_val)
        fa_txt2.append(f"{r['no_train_false_alarm_n']}/3 ({fa_val:.1f}s)")

    b1 = ax2.barh(y2 - 0.2, zp2, height=0.35, color="#d95f02", label="Train Zero Protection % (95% CI)")
    ax2.errorbar(zp2, y2 - 0.2, xerr=[zp2_lo, zp2_hi], fmt="none", ecolor="#7f2704", elinewidth=1.3, capsize=3)
    b2 = ax2.barh(y2 + 0.2, blk2, height=0.35, color="#1b9e77", label="Train Mean Blocked Fraction %")

    for i, b in enumerate(b1):
        ax2.text(zp2[i] + zp2_hi[i] + 1.5, b.get_y() + b.get_height() / 2, zp2_txt[i], va="center", fontsize=8, color="#7f2704", fontweight="bold")
    for i, b in enumerate(b2):
        ax2.text(blk2[i] + 1.5, b.get_y() + b.get_height() / 2, f"{blk2[i]:.1f}% | FA: {fa_txt2[i]}", va="center", fontsize=7.8, color="#1f2937")

    ax2.set_yticks(y2)
    ax2.set_yticklabels([disp for _, disp in all23_order])
    ax2.invert_yaxis()
    ax2.set_xlim(0, 128)
    ax2.set_xlabel("Percentage (%) [Annotations show No-Train Controls FA k/3 (blocked s)]")
    ax2.set_title("B. Full Independent Train Cohort (N = 23) + No-Train (N = 3)")
    ax2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2, frameon=True, framealpha=0.95)

    fig.suptitle(
        "Multimodal & Temporal Policy Ablation Matrix (Exploratory Cache-Only Replay)\n" + DISCLAIMER,
        fontsize=11.5,
        fontweight="bold",
    )
    out = FIGURES_DIR / "fig1_ablation_rates_wilson_ci.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def generate_fig2_sync11_timelines(
    event_rows: list[dict[str, str]],
    dep_rows: list[dict[str, str]],
    replay_sum: dict[str, Any],
) -> Path:
    """Plot per-event Convention-A blocked duration & outcome states across the 11 calibrated sync events."""
    dep_map = {r["event_id"]: r for r in dep_rows}
    ev_order = [r["event_id"] for r in dep_rows]

    def _lookup_dur(run_label: str) -> list[float]:
        m = {r["event_id"]: float(r["closed_duration_conv_a_s"]) for r in event_rows if r["run_label"] == run_label}
        return [m[eid] for eid in ev_order]

    b0_v2 = _lookup_dur("B0__v2")
    b7_v1 = _lookup_dur("DUAL_VISION_AUDIO__v1")
    b7_v2 = _lookup_dur("DUAL_VISION_AUDIO__v2")
    wt25_map = {
        r["event_id"]: float(r["closed_duration_s"])
        for r in replay_sum["window_tolerance_025_sensitivity"]
        if r["policy"] == "v2"
    }
    b7_v2_wt25 = [wt25_map[eid] for eid in ev_order]
    t4_vals = [float(dep_map[eid]["t4_master_s"]) if dep_map[eid]["t4_master_s"] else np.nan for eid in ev_order]
    end_vals = [float(dep_map[eid]["master_end_s"]) for eid in ev_order]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 6.2), gridspec_kw={"width_ratios": [1.35, 1.0]}, constrained_layout=True)

    y = np.arange(len(ev_order))
    h = 0.2
    ax1.barh(y - 1.5 * h, b0_v2, height=h, color="#66c2a5", label="B0 Front Only (V2)")
    ax1.barh(y - 0.5 * h, b7_v1, height=h, color="#8da0cb", label="B7 Dual+Audio (V1)")
    ax1.barh(y + 0.5 * h, b7_v2, height=h, color="#e78ac3", label="B7 Dual+Audio (V2, tol=0.5s)")
    ax1.barh(y + 1.5 * h, b7_v2_wt25, height=h, color="#fc8d62", label="B7 Dual+Audio (V2, tol=0.25s)")

    ax1.scatter(t4_vals, y, marker="|", s=140, color="#111827", linewidths=2.0, zorder=5, label="Reference Tail T4 (master s)")
    ax1.scatter(end_vals, y, marker="x", s=36, color="#6b7280", zorder=5, label="Recording End (master s)")

    ax1.set_yticks(y)
    ax1.set_yticklabels([eid.replace("train_events/", "") for eid in ev_order])
    ax1.invert_yaxis()
    ax1.set_xlabel("Duration / Timeline Timestamp (seconds on master clock)")
    ax1.set_title("A. Per-Event Closed Duration (Conv. A) vs Reference Tail T4")
    ax1.legend(loc="lower right", frameon=True, framealpha=0.92, fontsize=8.0)

    # Panel B: Outcome Classification Grid (4 arms x 11 events)
    b0_map = {r["event_id"]: r for r in event_rows if r["run_label"] == "B0__v2"}
    v1_map = {r["event_id"]: r for r in event_rows if r["run_label"] == "DUAL_VISION_AUDIO__v1"}
    v2_map = {r["event_id"]: r for r in event_rows if r["run_label"] == "DUAL_VISION_AUDIO__v2"}
    wt25_full = {
        r["event_id"]: r
        for r in replay_sum["window_tolerance_025_sensitivity"]
        if r["policy"] == "v2"
    }

    # Codes: 0=Zero-Prot, 1=Held-No-Premature, 2=Premature-M4, 3=Safe-Clear-PostT4, 4=NotEval/NoT4
    code_mat = np.zeros((len(ev_order), 4), dtype=int)
    text_mat: list[list[str]] = []
    for i, eid in enumerate(ev_order):
        row_txt = []
        # B0__v2
        r0 = b0_map[eid]
        if float(r0["closed_duration_conv_a_s"]) == 0.0:
            code_mat[i, 0], txt = 0, "0.0s (Zero)"
        elif r0["premature_opening_m4"] == "True":
            m = float(r0["m4_margin_s"])
            code_mat[i, 0], txt = 2, f"Prem ({m:+.1f}s)"
        elif r0["m4_status_detail"] == "NOT_EVALUABLE":
            code_mat[i, 0], txt = 4, f"Held ({float(r0['closed_duration_conv_a_s']):.1f}s)*"
        elif r0["m4_status_detail"] == "NO_T4_ON_CLOCK":
            code_mat[i, 0], txt = 4, "No T1/T4"
        else:
            code_mat[i, 0], txt = 1, "No Open"
        row_txt.append(txt)

        # B7__v1 & B7__v2
        for col_idx, rm_src in ((1, v1_map), (2, v2_map)):
            rm = rm_src[eid]
            dur = float(rm["closed_duration_conv_a_s"])
            if dur == 0.0:
                code_mat[i, col_idx], txt = 0, "0.0s (Zero)"
            elif rm["premature_opening_m4"] == "True":
                if rm["m4_margin_s"]:
                    txt = f"M4 ({float(rm['m4_margin_s']):+.1f}s)"
                else:
                    txt = "M4 (Clr<T4)"
                code_mat[i, col_idx] = 2
            elif rm["m4_margin_s"]:
                m = float(rm["m4_margin_s"])
                code_mat[i, col_idx], txt = 3, f"Safe ({m:+.1f}s)"
            else:
                code_mat[i, col_idx], txt = 1, f"Held ({dur:.1f}s)"
            row_txt.append(txt)

        # B7__v2 wt=0.25s
        rw = wt25_full[eid]
        if float(rw["closed_duration_s"]) == 0.0:
            code_mat[i, 3], txt = 0, "0.0s (Zero)"
        elif rw["premature_opening_m4"] is True:
            if rw["m4_margin_s"] is not None:
                txt = f"M4 ({float(rw['m4_margin_s']):+.1f}s)"
            else:
                txt = "M4 (Clr<T4)"
            code_mat[i, 3] = 2
        else:
            code_mat[i, 3], txt = 1, f"Held ({float(rw['closed_duration_s']):.1f}s)"
        row_txt.append(txt)
        text_mat.append(row_txt)

    cmap = matplotlib.colors.ListedColormap(["#fee0d2", "#deebf7", "#fcae91", "#c7e9c0", "#f3f4f6"])
    ax2.imshow(code_mat, cmap=cmap, aspect="auto", vmin=0, vmax=4)
    for i in range(len(ev_order)):
        for j in range(4):
            ax2.text(j, i, text_mat[i][j], ha="center", va="center", fontsize=7.8, color="#111827")

    ax2.set_xticks([0, 1, 2, 3])
    ax2.set_xticklabels(["B0 (V2)", "B7 (V1)", "B7 (V2)", "B7 (V2\ntol=0.25s)"])
    ax2.set_yticks(y)
    ax2.set_yticklabels([eid.replace("train_events/", "") for eid in ev_order])
    ax2.set_xlabel("* Front-only B0 has no T4 on local clock; Held = remained blocked to EOF")
    ax2.grid(False)
    ax2.set_title("B. Event-Level M4 & Protection Outcome Classification")

    fig.suptitle(
        "Event-Level Protection, Recording Bounds & Backfill Sensitivity (Sync-11 Cohort)\n" + DISCLAIMER,
        fontsize=11.5,
        fontweight="bold",
    )
    out = FIGURES_DIR / "fig2_sync11_event_timeline_outcomes.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def generate_fig3_departure_margins(dep_rows: list[dict[str, str]]) -> Path:
    """Plot M4 opening margins relative to T4 and RULE_3C vs cam2 qualifying density."""
    # Events that reached clearance under V2 (either numeric m4_margin_s or cleared before T4)
    clearing_rows = [r for r in dep_rows if r["v2_reached_clear"] == "True"]
    eids = [r["event_id"].replace("train_events/", "") for r in clearing_rows]
    # Compute margin using first_clear_s if unblocked wasn't completed before EOF (event_002)
    margins = []
    unblocked_flag = []
    for r in clearing_rows:
        if r["v2_m4_margin_s"]:
            margins.append(float(r["v2_m4_margin_s"]))
            unblocked_flag.append(True)
        else:
            # event_002 cleared at 19.0s < T4=32.9867s, did not complete unblocking before EOF
            margins.append(float(r["v2_first_clear_s"]) - float(r["t4_master_s"]))
            unblocked_flag.append(False)

    cam2_density = [float(r["cam2_qualifying_density"]) * 100.0 for r in clearing_rows]
    post_t4_margin = [float(r["post_t4_recording_margin_s"]) for r in clearing_rows]
    r3c_counts = [int(r["v2_rule_3c_count"]) for r in clearing_rows]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.0, 5.4), constrained_layout=True)

    y = np.arange(len(eids))
    colors = ["#d73027" if m < 0 else "#1a9850" for m in margins]
    bars = ax1.barh(y, margins, color=colors, height=0.58)
    ax1.axvline(0.0, color="#111827", linewidth=1.4, linestyle="-")
    for i, m in enumerate(margins):
        suffix = f" ({m:+.1f}s, RULE_3C x{r3c_counts[i]})" + ("" if unblocked_flag[i] else " [Clear<T4]")
        if m < 0:
            ax1.text(m - 0.8, i, suffix, ha="right", va="center", fontsize=8.0, color="#7f1d1d", fontweight="bold")
        else:
            ax1.text(m + 0.8, i, suffix, ha="left", va="center", fontsize=8.0, color="#14532d", fontweight="bold")

    ax1.set_yticks(y)
    ax1.set_yticklabels(eids)
    ax1.invert_yaxis()
    ax1.set_xlim(-62, 22)
    ax1.set_xlabel("Opening Margin Relative to T4: t_open - T4 (seconds; < 0 = Premature M4)")
    ax1.set_title("A. Premature-Opening Margins on V2 Clearing Events (B7)")

    # Panel B: Back-camera qualifying detection density vs Post-T4 recording margin across ALL 10 sync events with T4
    t4_rows = [r for r in dep_rows if r["t4_master_s"]]
    all_dens = [float(r["cam2_qualifying_density"]) * 100.0 for r in t4_rows]
    all_post = [float(r["post_t4_recording_margin_s"]) for r in t4_rows]
    all_lbls = [r["event_id"].replace("train_events/event_", "ev") for r in t4_rows]
    all_prem = [r["v2_premature_m4"] == "True" for r in t4_rows]

    label_offsets = {
        "ev011": (1.8, 0.0),
        "ev013": (5.0, 0.35),
        "ev014": (-0.6, 0.52),
        "ev012": (3.2, 0.48),
        "ev006": (5.8, 0.05),
        "ev009": (1.5, -0.45),
        "ev017": (5.8, -0.35),
        "ev001": (9.2, -0.22),
        "ev007": (8.5, 0.35),
        "ev002": (-3.0, 0.42),
    }
    for x, p_val, lbl, prem in zip(all_dens, all_post, all_lbls, all_prem):
        c = "#d73027" if prem else ("#1a9850" if lbl == "ev011" else "#2b83ba")
        mk = "o" if prem else ("s" if lbl == "ev011" else "^")
        ax2.scatter(x, p_val, color=c, marker=mk, s=70, zorder=5)
        dx, dy = label_offsets.get(lbl, (0.8, 0.2))
        ax2.annotate(
            lbl,
            xy=(x, p_val),
            xytext=(x + dx, p_val + dy),
            fontsize=8.0,
            color="#111827",
            arrowprops={"arrowstyle": "-", "color": "#9ca3af", "lw": 0.7, "shrinkA": 0, "shrinkB": 3},
        )

    ax2.axhline(3.0, color="#6b7280", linestyle="--", linewidth=1.1, label="T_clear (3.0s) minimum tail margin")
    ax2.axhline(4.6, color="#9ca3af", linestyle=":", linewidth=1.1, label="T_clear + unblocked (4.6s) margin")
    ax2.set_xlabel("Back-Camera Qualifying Detection Density (% of frames >= 0.35)")
    ax2.set_ylabel("Post-T4 Recording Margin (master_end - T4, seconds)")
    ax2.set_xlim(-3, 49)
    ax2.set_ylim(-0.3, 8.6)
    ax2.set_title("B. Sparse Back-Cam Detections vs Post-T4 Recording Tails (10 Events with T4)")
    ax2.legend(loc="upper right", frameon=True, framealpha=0.92, fontsize=8.0)

    fig.suptitle(
        "Departure-Reopening Root Cause: RULE_3C + Sparse Unrotated Back Caches & Tail Censoring\n" + DISCLAIMER,
        fontsize=11.3,
        fontweight="bold",
    )
    out = FIGURES_DIR / "fig3_departure_premature_opening_margins.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def generate_fig4_stress_and_sensitivity(
    stress: dict[str, Any],
    replay_sum: dict[str, Any],
    ablation_data: dict[str, Any],
) -> Path:
    """Plot EXP-G/H/I/K failure-injection safety outcomes and window_tolerance sensitivity."""
    scenarios: list[tuple[str, list[dict[str, Any]]]] = []

    def _group(rows: list[dict[str, Any]], order: list[tuple[str, str]]) -> None:
        by_s: dict[str, list[dict[str, Any]]] = {}
        for r in rows:
            by_s.setdefault(r["scenario"], []).append(r)
        for key, disp in order:
            if key in by_s:
                scenarios.append((disp, by_s[key]))

    _group(
        stress["exp_g_missing_modality"],
        [
            ("G1_front_absent_all", "G1 Front Absent (n=11)"),
            ("G2_back_absent_all", "G2 Back Absent (n=11)"),
            ("G3_audio_absent_all", "G3 Audio Absent (n=11)"),
            ("G4_dual_vision_dropout_mid", "G4 Dual Dropout Mid (n=11)"),
            ("G5_idle_vision_dropout_confirm2", "G5 Idle Dropout (n=3)"),
        ],
    )
    _group(
        stress["exp_h_contradictory_evidence"]["perturbations"],
        [
            ("H1_conflicting_front_and_rear", "H1 Conflict Front/Rear (n=11)"),
            ("H2_subthreshold_vision_cap_034", "H2 Subthresh Vis<0.35 (n=11)"),
            ("H3_audio_fp_burst_in_idle", "H3 Audio Burst Idle (n=6)"),
        ],
    )
    _group(
        stress["exp_i_failure_modes"],
        [
            ("I1_CAMERA_1_DROPOUT", "I1 Cam-1 Dropout (n=11)"),
            ("I2_CAMERA_2_DROPOUT", "I2 Cam-2 Dropout (n=11)"),
            ("I3_DUAL_CAMERA_DROPOUT", "I3 Dual Cam Dropout (n=11)"),
            ("I4_AUDIO_DROPOUT", "I4 Audio Dropout (n=11)"),
            ("I5_STALE_TIMESTAMPS_CAM1", "I5 Stale TS Cam1 (n=11)"),
            ("I6_STALE_TIMESTAMPS_CAM2", "I6 Stale TS Cam2 (n=11)"),
            ("I7_OUT_OF_ORDER_FRAMES", "I7 Out-of-Order (n=11)"),
            ("I8_DROPPED_FRAMES_WINDOW", "I8 Window Drop (n=11)"),
            ("I9_DROPPED_FRAMES_30PCT_SEED42", "I9 Random 30% Drop (n=11)"),
            ("I10_FALSE_DETECTION_1TICK", "I10 1-Tick Inject Idle (n=6)"),
        ],
    )
    _group(
        stress["exp_k_recovery_and_interrupt"],
        [
            ("K1_idle_fault_and_recovery", "K1 Idle Fault+Recov (n=3)"),
            ("K2_active_fault_and_recovery", "K2 Active Fault+Recov (n=11)"),
            ("K3_constructed_multi_train_interrupt", "K3 Multi-Train RULE_7 (n=8)"),
        ],
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.0, 8.0), gridspec_kw={"width_ratios": [1.55, 1.0]}, constrained_layout=True)

    y = np.arange(len(scenarios))
    fault_pct = [100.0 * sum(1 for r in rows if r.get("fault_occurred")) / len(rows) for _, rows in scenarios]
    blk_pct = [100.0 * sum(float(r.get("blocked_fraction", 0.0)) for r in rows) / len(rows) for _, rows in scenarios]
    total_runs = sum(len(rows) for _, rows in scenarios)
    dir_open_total = sum(sum(1 for r in rows if r.get("direct_open_from_fault")) for _, rows in scenarios)

    b_f = ax1.barh(y - 0.18, fault_pct, height=0.34, color="#ef8a62", label="Fault / Reject Triggered Rate (%)")
    b_b = ax1.barh(y + 0.18, blk_pct, height=0.34, color="#67a9cf", label="Mean Blocked Fraction (%)")

    for i, (disp, rows) in enumerate(scenarios):
        n = len(rows)
        f_cnt = sum(1 for r in rows if r.get("fault_occurred"))
        ax1.text(fault_pct[i] + 1.5, b_f[i].get_y() + b_f[i].get_height() / 2, f"{f_cnt}/{n}", va="center", fontsize=7.4, color="#993404")
        ax1.text(blk_pct[i] + 1.5, b_b[i].get_y() + b_b[i].get_height() / 2, f"{blk_pct[i]:.1f}%", va="center", fontsize=7.4, color="#0c4a6e")

    ax1.set_yticks(y)
    ax1.set_yticklabels([disp for disp, _ in scenarios])
    ax1.invert_yaxis()
    ax1.set_xlim(0, 118)
    ax1.set_xlabel("Percentage (%)")
    ax1.set_title(f"A. All 21 Failure/Stress Scenarios (Direct Fault->Open = {dir_open_total}/{total_runs} runs)")
    ax1.legend(loc="lower right", frameon=True, framealpha=0.92, fontsize=8.0)

    # Panel B: window_tolerance_s sensitivity (0.50s vs 0.25s) on B7 V1 & V2
    lookup = {(r["scope"], r["run_label"]): r for r in ablation_data["ablation_rows"]}
    v1_05 = lookup[("11_sync_train", "DUAL_VISION_AUDIO__v1")]
    v2_05 = lookup[("11_sync_train", "DUAL_VISION_AUDIO__v2")]
    wt_rows = replay_sum["window_tolerance_025_sensitivity"]
    v1_25 = [r for r in wt_rows if r["policy"] == "v1"]
    v2_25 = [r for r in wt_rows if r["policy"] == "v2"]

    categories = ["Zero Protection\n(k/11)", "Reached Clear\n(k/11)", "M4 Premature\n(events count)"]
    x = np.arange(len(categories))
    w = 0.19
    vals_v2_50 = [int(v2_05["zero_protection_n"]), int(v2_05["reached_clear_n"]), int(v2_05["m4_premature_n"])]
    vals_v2_25 = [
        sum(1 for r in v2_25 if r["closed_duration_s"] == 0.0),
        sum(1 for r in v2_25 if r["reached_crossing_clear"]),
        sum(1 for r in v2_25 if r["premature_opening_m4"] is True),
    ]
    vals_v1_50 = [int(v1_05["zero_protection_n"]), int(v1_05["reached_clear_n"]), int(v1_05["m4_premature_n"])]
    vals_v1_25 = [
        sum(1 for r in v1_25 if r["closed_duration_s"] == 0.0),
        sum(1 for r in v1_25 if r["reached_crossing_clear"]),
        sum(1 for r in v1_25 if r["premature_opening_m4"] is True),
    ]

    rects = [
        (ax2.bar(x - 1.5 * w, vals_v2_50, width=w, color="#1b9e77", label="V2 (tol=0.50s, default)"), vals_v2_50),
        (ax2.bar(x - 0.5 * w, vals_v2_25, width=w, color="#66c2a5", label="V2 (tol=0.25s, tight)"), vals_v2_25),
        (ax2.bar(x + 0.5 * w, vals_v1_50, width=w, color="#7570b3", label="V1 (tol=0.50s, default)"), vals_v1_50),
        (ax2.bar(x + 1.5 * w, vals_v1_25, width=w, color="#bebada", label="V1 (tol=0.25s, tight)"), vals_v1_25),
    ]
    for container, vals in rects:
        for rect, val in zip(container, vals):
            ax2.text(rect.get_x() + rect.get_width() / 2, val + 0.18, str(val), ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    ax2.set_xticks(x)
    ax2.set_xticklabels(categories)
    ax2.set_ylim(0, 10.5)
    ax2.set_ylabel("Event Count (out of 11 Sync Events)")
    ax2.set_title("B. window_tolerance_s Backfill Sensitivity (0.50s vs 0.25s)")
    ax2.legend(loc="upper right", frameon=True, framealpha=0.92, fontsize=8.0)

    fig.suptitle(
        "Fail-Safe Stress Testing (EXP-G/H/I/K) & Collector Backfill Sensitivity\n" + DISCLAIMER,
        fontsize=11.3,
        fontweight="bold",
    )
    out = FIGURES_DIR / "fig4_failure_injection_and_sensitivity.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> None:
    _setup_style()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    ablation_data = _read_json(ANALYSIS_DIR / "ablation_matrix.json")
    replay_sum = _read_json(REPLAY_SUMMARY_PATH)
    stress = _read_json(FAILURE_PATH)
    event_rows = _read_csv(ANALYSIS_DIR / "event_level_safety_metrics.csv")
    dep_rows = _read_csv(ANALYSIS_DIR / "departure_reopening_analysis.csv")

    generated = [
        generate_fig1_ablation_rates(ablation_data),
        generate_fig2_sync11_timelines(event_rows, dep_rows, replay_sum),
        generate_fig3_departure_margins(dep_rows),
        generate_fig4_stress_and_sensitivity(stress, replay_sum, ablation_data),
    ]
    for p in generated:
        print(f"GENERATED: {p.relative_to(REPO_ROOT)} ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
