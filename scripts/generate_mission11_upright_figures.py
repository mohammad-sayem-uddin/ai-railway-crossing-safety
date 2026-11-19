#!/usr/bin/env python3
"""Generate publication-grade 300-DPI figures for Mission 11 Upright vs Baseline Evaluation.

Reads strictly from ``results/upright_27_event_evaluation/baseline_vs_upright_comparison.json``,
``results/upright_27_event_evaluation/modality_and_fusion_ablation_metrics.json``,
and ``results/upright_27_event_evaluation/causal_fsm_gate_timing_summary.json``.
Never accesses raw media.
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UPRIGHT_EVAL = ROOT / "results" / "upright_27_event_evaluation"
DEFAULT_FIG_DIR = ROOT / "docs" / "generated" / "figures"


def _setup_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9.0,
            "axes.titlesize": 10.5,
            "axes.titleweight": "bold",
            "axes.labelsize": 9.0,
            "legend.fontsize": 8.0,
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 8.0,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 300,
        }
    )


def make_fig16_upright_vs_baseline_ablation(
    eval_dir: Path = DEFAULT_UPRIGHT_EVAL,
    fig_dir: Path = DEFAULT_FIG_DIR,
) -> Path:
    """Compare Pre-db40305 vs Upright db40305 train recall, F1, no-train FPs, and sessions."""
    out, _ = _build_fig16(eval_dir=eval_dir, fig_dir=fig_dir)
    return out


def _build_fig16(
    eval_dir: Path = DEFAULT_UPRIGHT_EVAL,
    fig_dir: Path = DEFAULT_FIG_DIR,
) -> tuple[Path, tuple[int, str]]:
    """Compare Pre-db40305 vs Upright db40305 train recall, F1, no-train FPs, and sessions."""
    comp = json.loads((eval_dir / "baseline_vs_upright_comparison.json").read_text(encoding="utf-8"))
    key_cfgs = [
        ("V2_Front_L1_Confirm2", "V2 Front L1"),
        ("V5_Back_Confirm2_SideRear", "V5 Back SR"),
        ("V8_Dual_Vision_Confirm2_SideRear", "V8 Dual SR"),
        ("A3_Audio_Hysteresis_075_k2", "A3 Aud .75k2"),
        ("F4_Front_L1_Or_Audio075k2", "F4 Fr|Aud"),
        ("F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2", "F6 Full MM"),
        ("F7_Exploratory_2of3_Multimodal", "F7 2-of-3"),
    ]
    by_name = {c["configuration"]: c for c in comp["config_comparison"]}
    q8 = comp["exploratory_quorum_comparison"]["F8_Exploratory_Strong_2of3_Quorum"]

    labels = [lbl for _, lbl in key_cfgs] + ["F8 Quorum*"]
    b_rec = [100.0 * by_name[k]["baseline_recall"] for k, _ in key_cfgs] + [100.0 * q8["baseline"]["recall"]]
    u_rec = [100.0 * by_name[k]["upright_recall"] for k, _ in key_cfgs] + [100.0 * q8["upright"]["recall"]]
    b_tp = [int(by_name[k]["baseline_tp"]) for k, _ in key_cfgs] + [int(q8["baseline"]["tp"])]
    u_tp = [int(by_name[k]["upright_tp"]) for k, _ in key_cfgs] + [int(q8["upright"]["tp"])]
    u_fp = [int(by_name[k]["upright_fp_no_train"]) for k, _ in key_cfgs] + [int(q8["upright"]["fp_no_train"])]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.2, 4.5))

    x = np.arange(len(labels))
    w = 0.36
    bars_b = ax1.bar(x - w / 2, b_rec, w, label="Pre-db40305 Sideways Cache", color="#7F8C8D")
    bars_u = ax1.bar(x + w / 2, u_rec, w, label="Upright db40305 Original Media", color="#0072B2")
    for idx, (rb, ru) in enumerate(zip(bars_b, bars_u, strict=True)):
        ax1.text(rb.get_x() + rb.get_width() / 2 - 0.04, rb.get_height() + 1.5, f"{b_tp[idx]}/23", ha="center", va="bottom", fontsize=6.6, color="#475569")
        extra_y = 7.5 if abs(u_rec[idx] - b_rec[idx]) < 5.0 else 1.5
        ax1.text(ru.get_x() + ru.get_width() / 2 + 0.04, ru.get_height() + extra_y, f"{u_tp[idx]}/23\n(FP={u_fp[idx]})", ha="center", va="bottom", fontsize=6.6, fontweight="bold", color="#0F172A")
    ax1.set_xticks(x, labels, rotation=20, ha="right")
    ax1.set_ylim(0, 130)
    ax1.set_ylabel("Train Recall (% of n=23 Trains)")
    ax1.set_title("(a) Pre-db40305 vs Upright (db40305) Modality & Fusion Recall")
    ax1.legend(loc="upper center", ncol=2, frameon=True)
    ax1.grid(axis="y", alpha=0.25, linestyle="--")

    # Panel B: Session Stratification (Session 1 Day n=20 vs Session 2 Night n=3)
    sess = comp["session_comparison"]
    s1 = sess["Session 1"]
    s2 = sess["Session 2"]
    cats = ["V2 Front L1", "V5 Back SR", "F6 Full MM"]
    s1_b = [100.0 * s1["baseline_V2_train_tp"] / s1["n_train_events"], 100.0 * s1["baseline_V5_back_sr_tp"] / s1["n_train_events"], 100.0 * s1["baseline_F6_train_tp"] / s1["n_train_events"]]
    s1_u = [100.0 * s1["upright_V2_train_tp"] / s1["n_train_events"], 100.0 * s1["upright_V5_back_sr_tp"] / s1["n_train_events"], 100.0 * s1["upright_F6_train_tp"] / s1["n_train_events"]]
    s2_u = [100.0 * s2["upright_V2_train_tp"] / s2["n_train_events"], 100.0 * s2["upright_V5_back_sr_tp"] / s2["n_train_events"], 100.0 * s2["upright_F6_train_tp"] / s2["n_train_events"]]

    xs = np.arange(len(cats))
    ws = 0.25
    ax2.bar(xs - ws, s1_b, ws, label=f"Session 1 Day Base (n={s1['n_train_events']})", color="#94A3B8")
    ax2.bar(xs, s1_u, ws, label=f"Session 1 Day Upright (n={s1['n_train_events']})", color="#009E73")
    ax2.bar(xs + ws, s2_u, ws, label=f"Session 2 Night Upright (n={s2['n_train_events']})", color="#E69F00")
    for idx in range(len(cats)):
        ax2.text(xs[idx] - ws, s1_b[idx] + 1.5, f"{s1_b[idx]:.0f}%", ha="center", va="bottom", fontsize=7.0)
        ax2.text(xs[idx], s1_u[idx] + 1.5, f"{s1_u[idx]:.0f}%", ha="center", va="bottom", fontsize=7.0, fontweight="bold")
        ax2.text(xs[idx] + ws, s2_u[idx] + 1.5, f"{s2_u[idx]:.0f}%", ha="center", va="bottom", fontsize=7.0)
    ax2.set_xticks(xs, cats)
    ax2.set_ylim(0, 132)
    ax2.set_ylabel("Session Train Recall (%)")
    ax2.set_title("(b) Session Stratification Before vs After Upright Correction")
    ax2.legend(loc="upper center", ncol=2, frameon=True, fontsize=7.2)
    ax2.grid(axis="y", alpha=0.25, linestyle="--")

    fig.tight_layout()
    out = fig_dir / "fig16_upright_vs_baseline_ablation.png"
    meta = _save_png_and_digest(fig, out)
    return out, meta


def _build_fig17(
    eval_dir: Path = DEFAULT_UPRIGHT_EVAL,
    fig_dir: Path = DEFAULT_FIG_DIR,
) -> tuple[Path, tuple[int, str]]:
    """Plot front/back detection gain per event and causal V3 gate-timing milestones."""
    comp = json.loads((eval_dir / "baseline_vs_upright_comparison.json").read_text(encoding="utf-8"))
    fsm = json.loads((eval_dir / "causal_fsm_gate_timing_summary.json").read_text(encoding="utf-8"))
    deltas = comp["event_deltas_27"]

    e_labels = [
        d["event_id"].replace("train_events/event_", "T").replace("no_train_events/event_", "NT").replace("engine_events/event_", "E")
        for d in deltas
    ]
    b_tot = [int(d["base_front_df"]) + int(d["base_back_df"]) for d in deltas]
    u_tot = [int(d["up_front_df"]) + int(d["up_back_df"]) for d in deltas]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.2, 4.5))

    x = np.arange(len(e_labels))
    w = 0.40
    ax1.bar(x - w / 2, b_tot, w, label="Pre-db40305 (Front+Back Det Frames)", color="#94A3B8")
    ax1.bar(x + w / 2, u_tot, w, label="Upright db40305 (Front+Back Det Frames)", color="#0072B2")
    ax1.set_xticks(x, e_labels, rotation=55, ha="right", fontsize=7.0)
    ax1.set_ylim(0, max(u_tot + b_tot) * 1.18)
    ax1.set_ylabel("Detected Frames (Front + Back)")
    ax1.set_title("(a) Per-Event Optical Detection Recovery Across All 27 Recordings")
    ax1.legend(loc="upper left", frameon=True)
    ax1.grid(axis="y", alpha=0.25, linestyle="--")

    fsm_order = [
        ("FSM_V2_Front_L1", "V2 Front"),
        ("FSM_F4_Front_Or_Audio075k2", "F4 Fr|Aud"),
        ("FSM_F6_Full_MM_Bounded27", "F6 FullMM"),
        ("FSM_F7_Exploratory_2of3_Bounded27", "F7 2of3"),
    ]
    xf = np.arange(len(fsm_order))
    wf = 0.20
    smap = fsm["summaries"]
    trigs = [smap[k]["train_triggers"] for k, _ in fsm_order]
    fulls = [smap[k]["train_full_closures"] for k, _ in fsm_order]
    warns = [smap[k]["train_pre_T2_warning"] for k, _ in fsm_order]
    cmds = [smap[k]["train_pre_T2_close_cmd"] for k, _ in fsm_order]
    t2full = [smap[k]["train_pre_T2_full_closure"] for k, _ in fsm_order]

    ax2.bar(xf - 1.5 * wf, trigs, wf, label="Triggered (/23)", color="#0072B2")
    ax2.bar(xf - 0.5 * wf, fulls, wf, label="Full Boom Closed (/23)", color="#009E73")
    ax2.bar(xf + 0.5 * wf, warns, wf, label="Warn <= T2", color="#E69F00")
    ax2.bar(xf + 1.5 * wf, cmds, wf, label="Close Cmd <= T2", color="#D55E00")
    for idx in range(len(fsm_order)):
        ax2.text(
            xf[idx],
            max(trigs[idx], fulls[idx]) + 0.6,
            f"Full<=T2: {t2full[idx]}",
            ha="center",
            va="bottom",
            fontsize=7.3,
            fontweight="bold",
        )
    ax2.set_xticks(xf, [lbl for _, lbl in fsm_order])
    ax2.set_ylim(0, 29)
    ax2.set_ylabel("Train Event Count (out of 23)")
    ax2.set_title("(b) Upright Causal Gate-Control Closure & T2 Safety Margins")
    ax2.legend(loc="upper center", ncol=2, frameon=True, fontsize=7.5)
    ax2.grid(axis="y", alpha=0.25, linestyle="--")

    fig.tight_layout()
    out = fig_dir / "fig17_upright_event_recovery_and_fsm_timing.png"
    meta = _save_png_and_digest(fig, out)
    return out, meta


def make_fig17_upright_recovery_and_fsm_timing(
    eval_dir: Path = DEFAULT_UPRIGHT_EVAL,
    fig_dir: Path = DEFAULT_FIG_DIR,
) -> Path:
    """Plot front/back detection gain per event and causal V3 gate-timing milestones."""
    out, _ = _build_fig17(eval_dir=eval_dir, fig_dir=fig_dir)
    return out


def _save_png_and_digest(fig: plt.Figure, out_path: Path) -> tuple[int, str]:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    data = buf.getvalue()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    return len(data), hashlib.sha256(data).hexdigest()


def generate_all(
    eval_dir: Path = DEFAULT_UPRIGHT_EVAL,
    fig_dir: Path = DEFAULT_FIG_DIR,
) -> list[Path]:
    return list(generate_all_with_hashes(eval_dir=eval_dir, fig_dir=fig_dir).keys())


def generate_all_with_hashes(
    eval_dir: Path = DEFAULT_UPRIGHT_EVAL,
    fig_dir: Path = DEFAULT_FIG_DIR,
) -> dict[Path, tuple[int, str]]:
    """Generate fig16 and fig17 and return {path: (size_bytes, sha256)} without re-reading PNGs."""
    _setup_style()
    p16, m16 = _build_fig16(eval_dir=eval_dir, fig_dir=fig_dir)
    p17, m17 = _build_fig17(eval_dir=eval_dir, fig_dir=fig_dir)
    return {p16: m16, p17: m17}


def main() -> int:
    paths = generate_all()
    print(json.dumps({"status": "OK", "figures": [str(p.relative_to(ROOT)) for p in paths]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
