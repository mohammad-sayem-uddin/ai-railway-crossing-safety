"""Generate all 10 publication-grade figures directly from verified results/exploratory_v2/ artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9.5,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelsize": 9.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.5,
        "figure.titlesize": 13,
        "figure.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)

BLUE = "#0072B2"
ORANGE = "#E69F00"
GREEN = "#009E73"
RED = "#D55E00"
SKY = "#56B4E9"
PURPLE = "#CC79A7"
SLATE = "#3B4252"
LIGHT_BG = "#F8FAFC"


def _load(results_root: Path, rel: str) -> Any:
    return json.loads((results_root / rel).read_text(encoding="utf-8"))


def _save(fig: plt.Figure, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _draw_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    subtitle: str = "",
    *,
    fc: str = "#EFF6FF",
    ec: str = BLUE,
    lw: float = 1.6,
    title_size: float = 9.5,
    sub_size: float = 7.8,
) -> None:
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
    )
    ax.add_patch(box)
    if subtitle:
        ax.text(
            x + w / 2,
            y + h * 0.66,
            title,
            ha="center",
            va="center",
            fontsize=title_size,
            fontweight="bold",
            color="#0F172A",
        )
        ax.text(
            x + w / 2,
            y + h * 0.29,
            subtitle,
            ha="center",
            va="center",
            fontsize=sub_size,
            color="#334155",
        )
    else:
        ax.text(
            x + w / 2,
            y + h / 2,
            title,
            ha="center",
            va="center",
            fontsize=title_size,
            fontweight="bold",
            color="#0F172A",
        )


def _arrow(
    ax: plt.Axes,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    label: str = "",
    *,
    color: str = SLATE,
    lw: float = 1.4,
    rad: float = 0.0,
    lx: float | None = None,
    ly: float | None = None,
) -> None:
    ax.annotate(
        "",
        xy=(x1, y1),
        xytext=(x0, y0),
        arrowprops={
            "arrowstyle": "-|>",
            "color": color,
            "lw": lw,
            "connectionstyle": f"arc3,rad={rad}",
            "shrinkA": 2,
            "shrinkB": 2,
        },
    )
    if label:
        tx = lx if lx is not None else (x0 + x1) / 2
        ty = ly if ly is not None else (y0 + y1) / 2
        ax.text(
            tx,
            ty,
            label,
            ha="center",
            va="center",
            fontsize=7.6,
            color=color,
            bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.9},
        )


def make_fig01_system_architecture(results_root: Path, fig_dir: Path) -> None:
    master = _load(results_root, "MASTER_V2_SUMMARY.json")
    exp_e = _load(results_root, "experiments/exp_e_occupancy.json")
    t_clear_cov = exp_e["real_data_coverage"]["events_with_T_scene_clear"]
    tot_ev = exp_e["real_data_coverage"]["total_events"]

    fig, ax = plt.subplots(figsize=(15.4, 7.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    fig.suptitle(
        "Figure 1: Four-Layer + Occupancy Multimodal Level-Crossing Protection Architecture",
        y=0.98,
    )
    ax.text(
        0.5,
        0.945,
        "Causal Temporal Fusion (allow_stale_detection_backfill=False) | 11-State Fail-Safe Arbiter | Deterministic Physical Gate Control",
        ha="center",
        va="center",
        fontsize=9.5,
        color="#334155",
    )

    # Column 1: 5 Physical/Logical Sensor Layers (wider boxes & compact text)
    _draw_box(
        ax,
        0.015,
        0.74,
        0.245,
        0.135,
        "Layer 1: Front Approach Camera",
        "camera_1 (~5 Hz, 0.2 s) | Auto-rot 0/±90/±180/±270°\nIndependent early approach trigger (no waiting)",
        fc="#DBEAFE",
        ec=BLUE,
        title_size=9.0,
        sub_size=7.3,
    )
    _draw_box(
        ax,
        0.015,
        0.57,
        0.245,
        0.135,
        "Layer 2: Side Crossing View",
        "camera_side (proxy in v2 caches) | MovementTracker\nMOVING vs STOPPED vs SINGLE_FRAME (no reopen)",
        fc="#E0F2FE",
        ec=SKY,
        title_size=9.0,
        sub_size=7.3,
    )
    _draw_box(
        ax,
        0.015,
        0.40,
        0.245,
        0.135,
        "Layer 3: Trackside Audio / Horn",
        "audio_1 (0.5 s hop, 1.0 s window, natural log-Mel)\nThr = 0.37 | Presence & dwell extension ONLY",
        fc="#FEF3C7",
        ec=ORANGE,
        title_size=9.0,
        sub_size=7.3,
    )
    _draw_box(
        ax,
        0.015,
        0.23,
        0.245,
        0.135,
        "Layer 4: Back / Exit Camera",
        "camera_2 (~5 Hz, synced on 11/27 events)\nPositive rear + last_carriage vs guarded disappear",
        fc="#FCE7F3",
        ec=PURPLE,
        title_size=9.0,
        sub_size=7.3,
    )
    _draw_box(
        ax,
        0.015,
        0.06,
        0.245,
        0.135,
        "Layer 5: Crossing Occupancy",
        f"Zone sensor (0/27 in Layer B v2; {t_clear_cov}/{tot_ev} T_scene_clear)\nOCCUPIED | CLEAR | UNKNOWN | MISSING | CONTRADICTORY",
        fc="#DCFCE7",
        ec=GREEN,
        title_size=9.0,
        sub_size=7.1,
    )

    # Column 2: Decoding, Sync, Causal Collector
    _draw_box(
        ax,
        0.305,
        0.48,
        0.215,
        0.365,
        "Causal Temporal Ingestion\n& Media Normalization",
        "• Video: frame_generator() rotation\n• SyncAligner: cam_2 -> master clock\n• MultimodalEvidenceCollector:\n  - Strict causality (t_obs <= t)\n  - No stale backfill (V3 default)\n  - Latest-per-source, 1-shot read\n  - Separate occupancy channel",
        fc="#F1F5F9",
        ec=SLATE,
        title_size=9.1,
        sub_size=7.3,
    )
    _draw_box(
        ax,
        0.305,
        0.10,
        0.215,
        0.31,
        "SourceTracker &\nHealth Diagnostics",
        "• Heartbeat timeout = 2.0 s\n• States: POSITIVE, NEGATIVE,\n  UNAVAILABLE, STALE, MISSING\n• Inference timeout & stream EOF\n  flagged -> FAIL-SAFE close",
        fc="#FEF2F2",
        ec=RED,
        title_size=9.1,
        sub_size=7.3,
    )

    # Column 3: V3 Decision Engine
    _draw_box(
        ax,
        0.575,
        0.19,
        0.23,
        0.655,
        "MultimodalDecisionEngineV3\n(11-State Asymmetric Safety Arbiter)",
        "1. APPROACH / CLOSE PATH (Early)\n"
        "   - L1 confirmed (2 fr @ 0.35) -> WARNING\n"
        "   - OR Critical Fault -> FAULT_FAIL_SAFE\n\n"
        "2. CROSSING MONITORING\n"
        "   - L2 SideMovementTracker passage state\n"
        "   - L3 Horn extends dwell hold (1.5 s)\n\n"
        "3. REOPENING GATE (Strict AND-Gate)\n"
        "   - Positive L4 rear (+ tail if configured)\n"
        "   - AND OccupancyVerifier == CLEAR\n"
        "   - AND Required sensors healthy\n"
        "   - AND Zero contradictions\n"
        "   - AND Clearance dwell >= 1.5 s\n"
        f"   -> {master['exp_d_premature_counts']['V3_CONSERVATIVE_POSITIVE']}/11 premature openings on sync11",
        fc="#ECFDF5",
        ec=GREEN,
        title_size=9.1,
        sub_size=7.2,
    )

    # Column 4: Gate Model & Audit Logging
    _draw_box(
        ax,
        0.855,
        0.54,
        0.132,
        0.28,
        "PhysicalGateModel",
        "OPEN (90°)\n↓ 2.0s warn + 3.0s close\nCLOSED (0°)\n↓ 1.5s dwell + 2.0s open\nOPEN (90°)",
        fc="#EFF6FF",
        ec=BLUE,
        title_size=9.0,
        sub_size=7.4,
    )
    _draw_box(
        ax,
        0.855,
        0.19,
        0.132,
        0.28,
        "Audit & Governance\nReceipt Layer",
        "• EventSimulationRunner\n• ALLOWED_TRANSITIONS\n• Conv A +0.20s note\n• SHA-256 Hashes",
        fc="#F8FAFC",
        ec=SLATE,
        title_size=9.0,
        sub_size=7.4,
    )

    for y_src in (0.805, 0.635, 0.465):
        _arrow(ax, 0.26, y_src, 0.305, 0.66, color=BLUE)
    for y_src in (0.295, 0.125):
        _arrow(ax, 0.26, y_src, 0.305, 0.56 if y_src > 0.2 else 0.255, color=SLATE)
    _arrow(ax, 0.4125, 0.48, 0.4125, 0.41, color=RED)
    _arrow(ax, 0.52, 0.66, 0.575, 0.66, "Frame", color=SLATE, ly=0.695)
    _arrow(ax, 0.52, 0.255, 0.575, 0.31, "Health", color=RED, ly=0.255)
    _arrow(ax, 0.805, 0.68, 0.855, 0.68, "Cmd", color=BLUE, ly=0.715)
    _arrow(ax, 0.805, 0.33, 0.855, 0.33, "Record", color=SLATE, ly=0.365)

    ax.text(
        0.5,
        0.015,
        "Qualification: Exploratory architecture prototype evaluated on pre-db40305 caches + synthetic scenarios; raw media isolated behind AUTH-MEDIA-ACCESS guard.",
        ha="center",
        va="center",
        fontsize=8,
        style="italic",
        color="#475569",
    )
    _save(fig, fig_dir / "fig01_system_architecture.png")


def make_fig02_four_layer_workflow(results_root: Path, fig_dir: Path) -> None:
    syn = _load(results_root, "failure_injection/exp_l_fault_injection.json")
    all_legal = syn["all_transitions_legal"]
    unsafe = syn["unsafe_opening_count"]

    fig, ax = plt.subplots(figsize=(15.4, 7.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    fig.suptitle(
        "Figure 2: Four-Layer 11-State Finite State Machine & Fail-Safe Transitions",
        y=0.98,
    )
    ax.text(
        0.5,
        0.945,
        f"Enforced via ALLOWED_TRANSITIONS | Synthetic 18-Scenario Legal Check: all_transitions_legal={all_legal}, unsafe_openings={unsafe}",
        ha="center",
        va="center",
        fontsize=9.2,
        color="#334155",
    )

    # Row 1: Approach -> Closing
    _draw_box(ax, 0.015, 0.72, 0.145, 0.125, "IDLE", "Gate OPEN (90°)", fc="#E2E8F0", ec=SLATE, title_size=8.8, sub_size=7.4)
    _draw_box(ax, 0.205, 0.72, 0.16, 0.125, "TRAIN_APPROACHING", "L1 front count >= 1", fc="#DBEAFE", ec=BLUE, title_size=8.6, sub_size=7.4)
    _draw_box(ax, 0.415, 0.72, 0.15, 0.125, "WARNING", "Confirmed (>= 2 frames)\nDwell 2.0 s", fc="#FEF3C7", ec=ORANGE, title_size=8.8, sub_size=7.3)
    _draw_box(ax, 0.615, 0.72, 0.15, 0.125, "GATE_CLOSING", "Actuator 90° -> 0°\n(3.0 s travel)", fc="#FFEDD5", ec=RED, title_size=8.8, sub_size=7.3)
    _draw_box(ax, 0.815, 0.72, 0.165, 0.125, "TRAIN_PRESENT", "Gate CLOSED (0°)\nPassage blocked", fc="#FEE2E2", ec=RED, title_size=8.8, sub_size=7.3)

    # Row 2: Crossing -> Reopening
    _draw_box(ax, 0.815, 0.41, 0.165, 0.125, "CROSSING_OCCUPIED", "L2 side moving OR\nOccupancy OCCUPIED", fc="#FEE2E2", ec=RED, title_size=8.5, sub_size=7.2)
    _draw_box(ax, 0.615, 0.41, 0.15, 0.125, "TRAIN_DEPARTING", "L4 rear onset observed\n(back camera)", fc="#FCE7F3", ec=PURPLE, title_size=8.7, sub_size=7.2)
    _draw_box(ax, 0.415, 0.41, 0.15, 0.125, "REAR_CONFIRMED", "L4 departure verified\n(await CLEAR)", fc="#E0E7FF", ec=BLUE, title_size=8.7, sub_size=7.2)
    _draw_box(ax, 0.215, 0.41, 0.15, 0.125, "CROSSING_CLEAR", "L5 CLEAR + Healthy\nDwell >= 1.5 s", fc="#DCFCE7", ec=GREEN, title_size=8.7, sub_size=7.2)
    _draw_box(ax, 0.015, 0.41, 0.145, 0.125, "GATE_OPENING", "Actuator 0° -> 90°\nRe-close if re-entry", fc="#D1FAE5", ec=GREEN, title_size=8.8, sub_size=7.2)

    # Bottom Fault Safe box
    _draw_box(
        ax,
        0.26,
        0.09,
        0.48,
        0.155,
        "FAULT_FAIL_SAFE (Force CLOSED / Hold CLOSED)",
        "Triggered from ANY non-terminal state on: critical sensor failure, front/back timeout,\n"
        "occupancy CONTRADICTORY, stream EOF during passage, or required source loss.\n"
        "Never permits GATE_OPENING while active fault persists.",
        fc="#FEF2F2",
        ec=RED,
        lw=2.0,
        title_size=9.2,
        sub_size=7.5,
    )

    _arrow(ax, 0.16, 0.782, 0.205, 0.782, "L1 >= thr", color=BLUE, lx=0.182, ly=0.818)
    _arrow(ax, 0.265, 0.72, 0.105, 0.72, "Glitch reset", color=SLATE, rad=-0.26, lx=0.185, ly=0.635)
    _arrow(ax, 0.365, 0.782, 0.415, 0.782, "2 frames", color=ORANGE, lx=0.39, ly=0.818)
    _arrow(ax, 0.565, 0.782, 0.615, 0.782, ">= 2.0 s", color=RED, lx=0.59, ly=0.818)
    _arrow(ax, 0.765, 0.782, 0.815, 0.782, "0° reached", color=RED, lx=0.79, ly=0.818)

    _arrow(ax, 0.897, 0.72, 0.897, 0.535, "L2/Occ active", color=RED, lx=0.942, ly=0.625)
    _arrow(ax, 0.815, 0.472, 0.765, 0.472, "L4 rear", color=PURPLE, lx=0.79, ly=0.512)
    _arrow(ax, 0.615, 0.472, 0.565, 0.472, "L4 ver.", color=BLUE, lx=0.59, ly=0.512)
    _arrow(ax, 0.415, 0.472, 0.365, 0.472, "Occ CLEAR", color=GREEN, lx=0.39, ly=0.512)
    _arrow(ax, 0.215, 0.472, 0.16, 0.472, "1.5 s dwell", color=GREEN, lx=0.187, ly=0.512)
    _arrow(ax, 0.087, 0.535, 0.087, 0.72, "90° OPEN", color=GREEN, lx=0.048, ly=0.625)

    _arrow(ax, 0.14, 0.535, 0.285, 0.72, "2nd train L1", color=RED, rad=0.08, lx=0.225, ly=0.59)
    _arrow(ax, 0.49, 0.72, 0.49, 0.245, "Any critical fault / timeout", color=RED, lx=0.555, ly=0.315)
    _arrow(ax, 0.85, 0.41, 0.74, 0.17, "Timeout / Contradiction", color=RED, lx=0.84, ly=0.28)

    ax.text(
        0.5,
        0.02,
        "Note: Layer 3 (Audio Horn) never triggers state progression alone and never suppresses warnings; it only extends clearance_dwell hold time.",
        ha="center",
        va="center",
        fontsize=8.2,
        style="italic",
        color="#475569",
    )
    _save(fig, fig_dir / "fig02_four_layer_workflow.png")


def make_fig03_gate_closure_timeline(results_root: Path, fig_dir: Path) -> None:
    syn_traces = _load(results_root, "replays/synthetic_scenarios_traces.json")["traces"]
    nom = syn_traces["00_nominal_4layer_full_cycle"]
    cmp_sync = _load(results_root, "replays/real_sync11_policy_comparison_traces.json")["traces"]
    exp_d = _load(results_root, "experiments/exp_d_back_departure.json")
    t4_map = {r["event_id"]: r["T4_master_s"] for r in exp_d["sync11_comparison"]}

    fig, axes = plt.subplots(3, 1, figsize=(13.2, 9.6), constrained_layout=True)
    fig.suptitle("Figure 3: Event Replay Gate Angle & Safety State Timelines (Synthetic & Real Sync11)")

    # Panel A: Synthetic Nominal 4-layer cycle with staggered non-overlapping annotations
    ax = axes[0]
    ts = [s["t"] for s in nom["steps"]]
    angs = [s["gate_angle_deg"] for s in nom["steps"]]
    ax.plot(ts, angs, color=BLUE, lw=2.3, label="Gate angle (V3 Conservative)")
    ax.axvspan(1.0, 5.0, color=SKY, alpha=0.14, label="L1 Front [1.0–5.0 s]")
    ax.axvspan(4.0, 12.6, color=ORANGE, alpha=0.14, label="L2/L4 Train in zone [4.0–12.6 s]")
    ax.axvline(3.0, color=RED, ls="--", lw=1.2, label="Entry ref (3.0 s)")
    ax.axvline(13.0, color=GREEN, ls="--", lw=1.2, label="Clearance ref (13.0 s)")

    ann_pos = {
        "TRAIN_APPROACHING": (0.8, 56),
        "WARNING": (2.2, 74),
        "GATE_CLOSING": (4.7, 74),
        "TRAIN_PRESENT": (6.6, 20),
        "REAR_CONFIRMED": (11.6, 20),
        "GATE_OPENING": (15.5, 16),
        "IDLE": (18.8, 70),
    }
    for tr in nom["transitions"]:
        to_s = tr["to"]
        if to_s in ann_pos:
            tx, ty = ann_pos[to_s]
            ax.annotate(
                f"{to_s}\n@{tr['t']:.1f}s",
                xy=(tr["t"], tr["gate_angle_deg"]),
                xytext=(tx, ty),
                fontsize=7.4,
                ha="center",
                bbox={"boxstyle": "round,pad=0.18", "fc": "white", "ec": "#CBD5E1", "alpha": 0.94},
                arrowprops={"arrowstyle": "->", "lw": 0.85, "color": "#475569"},
            )
    ax.set_title("A. Controlled Synthetic 4-Layer Nominal Cycle (00_nominal_4layer_full_cycle)", loc="left")
    ax.set_ylabel("Gate Angle (°)")
    ax.set_ylim(-8, 108)
    ax.legend(loc="center", bbox_to_anchor=(0.56, 0.88), ncol=3, frameon=True, fontsize=7.9)
    ax.grid(alpha=0.25)

    # Panel B & C: Real sync11 comparisons
    sync11_full = _load(results_root, "replays/real_sync11_v3_traces.json")["traces"]
    for idx, (eid, title_tag) in enumerate(
        [
            ("train_events/event_013", "B. Real Sync11 (event_013): V3 Conservative Holds Closed While V2 Opens Prematurely Before T4"),
            ("train_events/event_006", "C. Real Sync11 (event_006): Late Pre-db40305 Front Detection + V3 Prevents Mid-Passage Opening"),
        ],
        start=1,
    ):
        ax = axes[idx]
        tr_v3 = sync11_full[eid]["steps"]
        t_v3 = [s["t"] for s in tr_v3]
        a_v3 = [s["gate_angle_deg"] for s in tr_v3]
        ax.plot(t_v3, a_v3, color=GREEN, lw=2.5, label="V3_CONSERVATIVE_POSITIVE (actual replay)")

        pols = cmp_sync[eid]
        v2_open = next((tr["t"] for tr in pols["V2_RULE_3B_3C"]["transitions"] if tr["to"] == "GATE_OPENING"), None)
        v1_open = next((tr["t"] for tr in pols["V1_RULE_3"]["transitions"] if tr["to"] == "GATE_OPENING"), None)
        g_open = next((tr["t"] for tr in pols["V3_GUARDED_DISAPPEARANCE"]["transitions"] if tr["to"] == "GATE_OPENING"), None)
        t4 = t4_map[eid]
        if v2_open is not None:
            ax.axvline(v2_open, color=RED, ls="-.", lw=1.6, label=f"V2_RULE_3B_3C premature open ({v2_open:.1f} s)")
        if v1_open is not None and v1_open != v2_open:
            ax.axvline(v1_open, color=ORANGE, ls=":", lw=1.6, label=f"V1_RULE_3 premature open ({v1_open:.1f} s)")
        if g_open is not None and g_open != v2_open:
            ax.axvline(g_open, color=PURPLE, ls="--", lw=1.5, label=f"V3_GUARDED premature open ({g_open:.1f} s)")
        ax.axvline(t4, color=SLATE, ls="--", lw=1.8, label=f"Adopted clearance T4_master = {t4:.2f} s")

        ax.set_title(title_tag + " [Exploratory]", loc="left")
        ax.set_ylabel("Gate Angle (°)")
        ax.set_ylim(-8, 108)
        ax.legend(loc="center left" if idx == 1 else "lower left", frameon=True, ncol=2)
        ax.grid(alpha=0.25)

    axes[2].set_xlabel("Master Clock Time (s)")
    _save(fig, fig_dir / "fig03_gate_closure_timeline.png")


def make_fig04_departure_and_clearance_workflow(results_root: Path, fig_dir: Path) -> None:
    exp_e = _load(results_root, "experiments/exp_e_occupancy.json")
    exp_d = _load(results_root, "experiments/exp_d_back_departure.json")

    fig = plt.figure(figsize=(14.4, 6.8))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.1, 1.05], wspace=0.34, bottom=0.22, top=0.88, left=0.03, right=0.98)
    fig.suptitle("Figure 4: Layer 4 Departure & Layer 5 Occupancy Clearance Verification Workflow", y=0.97)

    ax = fig.add_subplot(gs[0])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("A. Mandatory Reopening AND-Gate Logic (Zero Unsafe Shortcut)", loc="left")

    gates = [
        ("Gate 1: Positive L4 Rear Departure", "camera_2 sees 'rear' (+ 'last_carriage' when configured)\nDisappearance alone BLOCKED in CONSERVATIVE_POSITIVE", "#FCE7F3", PURPLE),
        ("Gate 2: Explicit Occupancy == CLEAR", "OccupancyVerifier requires fresh dedicated sensor == CLEAR\nUNKNOWN / MISSING / OCCUPIED / CONTRADICTORY -> HOLD CLOSED", "#DCFCE7", GREEN),
        ("Gate 3: Required Source Health & Zero Faults", "No sensor timeouts, no FAULT_FAIL_SAFE, required back/occ healthy\nNo conflicting side/rear detections while CLEAR reported", "#FEF3C7", ORANGE),
        ("Gate 4: Clearance Dwell >= 1.5 s & Quiet Audio", "Stable CLEAR interval without recent audio horn hold (1.5 s)\nThen GATE_OPENING (0° -> 90°) with instant L1/Occ re-close interrupt", "#DBEAFE", BLUE),
    ]
    ys = [0.78, 0.54, 0.30, 0.06]
    for i, (t, s, fc, ec) in enumerate(gates):
        _draw_box(ax, 0.03, ys[i], 0.94, 0.165, t, s, fc=fc, ec=ec, title_size=9.1, sub_size=7.6)
        if i < len(gates) - 1:
            _arrow(ax, 0.50, ys[i], 0.50, ys[i + 1] + 0.165, color=SLATE)

    ax2 = fig.add_subplot(gs[1])
    occ_states = exp_e["synthetic_occupancy_unit_states"]
    short_names = {
        "OCCUPIED_explicit": "OCCUPIED\n(explicit)",
        "CLEAR_explicit_healthy": "CLEAR\n(healthy)",
        "UNKNOWN_no_sensor": "UNKNOWN\n(no sensor)",
        "MISSING_unavailable": "MISSING\n(unavailable)",
        "CONTRADICTORY_clear_vs_vision": "CONTRADICTORY\n(vs crossing vision)",
    }
    labels = [short_names.get(s["case"], s["case"]) for s in occ_states]
    cleared = [1 if s["verified_clear"] else 0 for s in occ_states]
    colors = [GREEN if c else RED for c in cleared]
    y_pos = np.arange(len(labels))
    ax2.barh(y_pos, [1] * len(labels), color=colors, alpha=0.84, height=0.56)
    for i, s in enumerate(occ_states):
        verdict = "PERMITS REOPEN (verified_clear=True)" if s["verified_clear"] else f"HOLDS CLOSED ({s['resolved_state'].upper()})"
        ax2.text(0.5, i, verdict, ha="center", va="center", color="white", fontweight="bold", fontsize=8.3)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(labels, fontsize=8.5)
    ax2.set_xticks([])
    ax2.set_xlim(0, 1)
    ax2.invert_yaxis()
    ax2.set_title("B. OccupancyVerifier Unit Verification & Real Hardware Gap", loc="left")

    cov = exp_e["real_data_coverage"]
    total_rear = sum(r["rear_dets"] for r in exp_d["back27_local_clock_summary"])
    total_tail = sum(r["last_carriage_labels"] for r in exp_d["back27_local_clock_summary"])
    note = (
        f"Real Layer B v2 Dataset Audit (Exploratory):  • Dedicated occupancy sensors present: {cov['dedicated_occupancy_sensors']}/{cov['total_events']}  "
        f"• Adopted T_scene_clear: {cov['events_with_T_scene_clear']}/{cov['total_events']} "
        f"({next(iter(cov['T_scene_clear_values'].keys()))} @ {next(iter(cov['T_scene_clear_values'].values()))} s)\n"
        f"• Back camera predictions across all 27 streams: {total_rear} 'rear', {total_tail} 'last_carriage'  "
        f"-> V3 safely resolves UNKNOWN & refuses unverified reopening."
    )
    fig.text(
        0.5,
        0.08,
        note,
        ha="center",
        va="center",
        fontsize=8.6,
        bbox={"boxstyle": "round,pad=0.45", "fc": "#F8FAFC", "ec": "#CBD5E1"},
    )
    _save(fig, fig_dir / "fig04_departure_and_clearance_workflow.png")


def make_fig05_modality_ablation(results_root: Path, fig_dir: Path) -> None:
    exp_k = _load(results_root, "experiments/exp_k_ablation.json")
    real_k = exp_k["real_sync11_ablation"]
    syn_k = exp_k["synthetic_4layer_ablation"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.6), constrained_layout=True)
    fig.suptitle("Figure 5: Leave-One-Modality-Out Ablation Study (Real Sync11 Exploratory & Synthetic 4-Layer)")

    real_order = [
        ("full_sync11_front_audio_back", "Full Sync11\n(Front+Audio+Back)"),
        ("no_audio_front_back_sync11", "No Audio\n(Front+Back)"),
        ("no_back_front_audio_sync11", "No Back\n(Front+Audio, B4)"),
        ("no_front_back_only_sync11", "No Front\n(Back Only)"),
        ("audio_only_no_vision_sync11", "Audio Only\n(No Vision)"),
    ]
    x = np.arange(len(real_order))
    w = 0.27
    closures = [real_k[k]["closures"] for k, _ in real_order]
    reopens = [real_k[k]["reopenings"] for k, _ in real_order]
    prem = [real_k[k]["premature_openings"] for k, _ in real_order]

    b1 = ax1.bar(x - w, closures, width=w, color=BLUE, label="Closures Triggered (/11)")
    b2 = ax1.bar(x, reopens, width=w, color=GREEN, label="Reopenings (/11)")
    b3 = ax1.bar(x + w, prem, width=w, color=RED, label="Premature Openings (/11)")
    for bars in (b1, b2, b3):
        ax1.bar_label(bars, padding=2, fontsize=8)
    ax1.set_xticks(x)
    ax1.set_xticklabels([lbl for _, lbl in real_order], fontsize=8.2)
    ax1.set_ylim(0, 11.8)
    ax1.set_ylabel("Event Count (sync11, n = 11)")
    ax1.set_title("A. Real Sync11 Cohort Ablation (Exploratory, Causal V3)", loc="left")
    ax1.legend(loc="upper right")
    ax1.grid(axis="y", alpha=0.25)

    syn_order = [
        ("full_4layer_nominal", "Full 4-Layer\nNominal"),
        ("no_side_camera", "No Side\nCamera"),
        ("no_audio", "No Audio\nSensor"),
        ("no_back_camera", "No Back\nCamera"),
        ("no_occupancy_sensor", "No Occupancy\nSensor"),
        ("no_front_camera", "No Front\nCamera"),
    ]
    y_pos = np.arange(len(syn_order))
    close_t = [syn_k[k]["t_fully_closed_s"] or 0.0 for k, _ in syn_order]
    open_t = [syn_k[k]["first_opening_s"] for k, _ in syn_order]
    bar_colors = []
    status_txt = []
    for k, _ in syn_order:
        r = syn_k[k]
        if not r["closure_triggered"]:
            bar_colors.append(RED)
            status_txt.append("NO CLOSURE (No L1 Front)")
        elif r["first_opening_s"] is None:
            bar_colors.append(ORANGE)
            status_txt.append(f"HELD CLOSED ({r['final_crossing_state']})")
        else:
            bar_colors.append(GREEN)
            status_txt.append(f"Closed {r['t_fully_closed_s']:.1f}s -> Opened {r['first_opening_s']:.1f}s")

    ax2.barh(y_pos, close_t, color=bar_colors, alpha=0.86, height=0.58)
    for i, txt in enumerate(status_txt):
        ax2.text(max(close_t[i], 0.3) + 0.35, i, txt, va="center", ha="left", fontsize=8.2, fontweight="bold")
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([lbl for _, lbl in syn_order])
    ax2.invert_yaxis()
    ax2.set_xlim(0, 14.5)
    ax2.set_xlabel("Time to Full Gate Closure (s) | Nominal Ref: Entry 6.5 s, Clear 13.0 s")
    ax2.set_title("B. Synthetic 4-Layer 5-Source Ablation Outcomes", loc="left")
    ax2.grid(axis="x", alpha=0.25)

    _save(fig, fig_dir / "fig05_modality_ablation.png")


def make_fig06_closure_performance(results_root: Path, fig_dir: Path) -> None:
    exp_j = _load(results_root, "experiments/exp_j_temporal_vs_stateless.json")
    exp_i = _load(results_root, "experiments/exp_i_complete_system.json")
    exp_c = _load(results_root, "experiments/exp_c_audio_horn.json")
    aud = exp_c["audio23_metrics"]
    mcn_j = exp_j["mcnemar_v3_vs_stateless_union_no_train_fp"]

    fig, axes = plt.subplots(1, 3, figsize=(14.5, 5.2), constrained_layout=True)
    fig.suptitle("Figure 6: Temporal vs. Stateless Gate Triggering, Causal Collector Delta & Audio Diagnostics [Exploratory]")

    # Panel A: Temporal vs Stateless on B4
    ax = axes[0]
    pols = [
        ("stateless_union", "Stateless\nUnion"),
        ("stateless_vision_rule2", "Stateless\nVision"),
        ("v1", "V1\nTemporal"),
        ("v2", "V2\nTemporal"),
        ("v3_conservative", "V3 4-Layer\nConservative"),
    ]
    x = np.arange(len(pols))
    w = 0.36
    tr23 = [exp_j["policies"][p]["b4_train23_closures"] for p, _ in pols]
    nt3 = [exp_j["policies"][p]["b4_no_train3_false_closures"] for p, _ in pols]
    b1 = ax.bar(x - w / 2, tr23, width=w, color=BLUE, label="Train Events (/23)")
    b2 = ax.bar(x + w / 2, nt3, width=w, color=RED, label="No-Train FP (/3)")
    ax.bar_label(b1, padding=2, fontsize=8)
    ax.bar_label(b2, padding=2, fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([l for _, l in pols], fontsize=8)
    ax.set_ylim(0, 27)
    ax.set_ylabel("Closed Event Count")
    ax.set_title(f"A. B4 Cohort (McNemar FP p={mcn_j['exact_p_value']})", loc="left")
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.25)

    # Panel B: Causal Collector vs Legacy Backfill (B4 train23)
    ax = axes[1]
    cb = exp_i["causal_vs_backfill_b4_train23_closures"]
    cats = ["Legacy Stale\nBackfill (True)", "Strict Causal\nNo Backfill (V3)"]
    vals = [cb["legacy_backfill"], cb["causal"]]
    bars = ax.bar(cats, vals, color=[ORANGE, BLUE], width=0.52)
    ax.bar_label(bars, labels=[f"{v}/23 ({v/23:.1%})" for v in vals], padding=3, fontsize=8.5, fontweight="bold")
    ax.set_ylim(0, 22)
    ax.set_ylabel("B4 Train23 Closures Triggered")
    ax.set_title("B. Collector Causality Impact (B4 Train23)", loc="left")
    ax.text(
        0.5,
        0.82,
        "Pre-db40305 unrotated caches\n+ 0-frame backfill elimination\nexplain 16 -> 10 closure shift",
        transform=ax.transAxes,
        ha="center",
        fontsize=8,
        bbox={"boxstyle": "round,pad=0.3", "fc": "#FFFBEB", "ec": ORANGE},
    )
    ax.grid(axis="y", alpha=0.25)

    # Panel C: Audio V3 Horn Metrics + non-train scores
    ax = axes[2]
    met_names = ["Recall", "Precision", "F1", "Accuracy", "Spec.", "ROC-AUC", "AP"]
    met_vals = [
        aud["recall"],
        aud["precision"],
        aud["f1"],
        aud["accuracy"],
        aud["specificity"],
        aud["event_max_roc_auc"],
        aud["event_max_average_precision"],
    ]
    bars = ax.barh(np.arange(len(met_names)), met_vals, color=[BLUE, ORANGE, BLUE, SKY, RED, GREEN, GREEN], height=0.58)
    ax.bar_label(bars, fmt="%.3f", padding=3, fontsize=8)
    ax.set_yticks(np.arange(len(met_names)))
    ax.set_yticklabels(met_names)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.18)
    ax.set_xlabel("Score on audio23 (thr = 0.37)")
    ax.set_title("C. Audio Horn Classifier (Supporting-Only)", loc="left")
    ax.text(
        0.98,
        0.38,
        f"TP={aud['TP']}, FP={aud['FP']}\nFN={aud['FN']}, TN={aud['TN']}\nno_train max: 0.800–0.826",
        transform=ax.transAxes,
        ha="right",
        fontsize=7.8,
        bbox={"boxstyle": "round,pad=0.25", "fc": "#FEF2F2", "ec": RED},
    )
    ax.grid(axis="x", alpha=0.25)

    _save(fig, fig_dir / "fig06_closure_performance.png")


def make_fig07_premature_opening_analysis(results_root: Path, fig_dir: Path) -> None:
    exp_d = _load(results_root, "experiments/exp_d_back_departure.json")
    exp_l = _load(results_root, "failure_injection/exp_l_fault_injection.json")
    prem = exp_d["sync11_premature_opening_counts"]
    mcn = exp_d["mcnemar_v2_vs_v3_conservative_premature"]
    syn_cmp = exp_l["sparse_dropout_departure_comparison"]

    fig, axes = plt.subplots(1, 3, figsize=(14.5, 5.4), constrained_layout=True)
    fig.suptitle("Figure 7: Premature Reopening Prevention Across Departure Policies (Real Sync11 & Synthetic Sparse Dropout)")

    # Panel A: Sync11 premature count comparison
    ax = axes[0]
    order = [
        ("V1_RULE_3", "V1\nRULE_3", ORANGE),
        ("V2_RULE_3B_3C", "V2\nRULE_3B/3C", RED),
        ("V3_GUARDED_DISAPPEARANCE", "V3 Guarded\nDisappear", PURPLE),
        ("V3_CONSERVATIVE_POSITIVE", "V3 4-Layer\nConservative", GREEN),
    ]
    vals = [prem[k] for k, _, _ in order]
    bars = ax.bar([l for _, l, _ in order], vals, color=[c for _, _, c in order], width=0.55)
    ax.bar_label(bars, labels=[f"{v}/11" for v in vals], padding=3, fontsize=9, fontweight="bold")
    ax.set_ylim(0, 5.2)
    ax.set_ylabel("Premature Openings Before T4_master")
    ax.set_title(f"A. Sync11 Cohort (McNemar p={mcn['exact_p_value']})", loc="left")
    ax.grid(axis="y", alpha=0.25)

    # Panel B: Per-event reopening vs T4 on affected sync11 events
    ax = axes[1]
    affected = [
        r for r in exp_d["sync11_comparison"]
        if any(r["policies"][p]["premature_opening_vs_T4"] for p in r["policies"])
    ]
    y_pos = np.arange(len(affected))
    seen_labels: set[str] = set()
    for i, r in enumerate(affected):
        t4 = r["T4_master_s"]
        lbl_t4 = "Adopted T4_master" if "Adopted T4_master" not in seen_labels else ""
        seen_labels.add("Adopted T4_master")
        ax.scatter(t4, i, marker="D", s=65, color=SLATE, zorder=5, label=lbl_t4)
        for p, col, mk, off in [
            ("V1_RULE_3", ORANGE, "s", -0.14),
            ("V2_RULE_3B_3C", RED, "o", 0.0),
            ("V3_GUARDED_DISAPPEARANCE", PURPLE, "^", 0.14),
        ]:
            t_op = r["policies"][p]["first_opening_s"]
            if t_op is not None:
                plbl = p if p not in seen_labels else ""
                seen_labels.add(p)
                ax.scatter(t_op, i + off, marker=mk, s=55, color=col, label=plbl)
                ax.plot([t_op, t4], [i + off, i + off], color=col, lw=1.1, alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels([r["event_id"].replace("train_events/", "") for r in affected])
    ax.invert_yaxis()
    ax.set_xlabel("Master Clock Time (s) — Left of Diamond = Premature")
    ax.set_title("B. Premature Opening Events vs. T4_master [Exploratory]", loc="left")
    ax.legend(loc="lower right", fontsize=7.4)
    ax.grid(alpha=0.25)

    # Panel C: Synthetic sparse-dropout test
    ax = axes[2]
    syn_order = [
        ("V2_RULE_3C_DISAPPEARANCE", "V2_RULE_3C"),
        ("V1_RULE_3", "V1_RULE_3"),
        ("V3_GUARDED_DISAPPEARANCE", "V3_GUARDED"),
        ("V3_CONSERVATIVE_POSITIVE", "V3_CONSERVATIVE"),
    ]
    y2 = np.arange(len(syn_order))
    for i, (k, lbl) in enumerate(syn_order):
        r = syn_cmp[k]
        if r["reopened_at_all"]:
            ax.barh(i, r["first_opening_s"], color=RED, height=0.48, alpha=0.88)
            ax.text(r["first_opening_s"] * 0.5, i, f"PREMATURE @ {r['first_opening_s']:.1f} s", va="center", ha="center", color="white", fontweight="bold", fontsize=8.3)
        else:
            ax.barh(i, 24.0, color=GREEN, height=0.48, alpha=0.28, edgecolor=GREEN, lw=1.4)
            ax.text(0.8, i, f"HELD CLOSED ({r['final_state']})", va="center", color="#065F46", fontweight="bold", fontsize=8.3)
    ax.axvline(15.0, color=SLATE, ls="--", lw=1.8, label="True Clearance T4 = 15.0 s")
    ax.set_yticks(y2)
    ax.set_yticklabels([l for _, l in syn_order])
    ax.invert_yaxis()
    ax.set_xlim(0, 26.5)
    ax.set_xlabel("Simulation Timeline (s)")
    ax.set_title("C. Synthetic Sparse-Dropout Test (1 Blip @ 8 s)", loc="left")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="x", alpha=0.25)

    _save(fig, fig_dir / "fig07_premature_opening_analysis.png")


def make_fig08_fault_injection_outcomes(results_root: Path, fig_dir: Path) -> None:
    exp_l = _load(results_root, "failure_injection/exp_l_fault_injection.json")
    scenarios = exp_l["fault_and_operational_scenarios"]

    fig, ax = plt.subplots(figsize=(13.8, 7.6), constrained_layout=True)
    fig.suptitle("Figure 8: Controlled Synthetic Nominal & 17 Part-6 Fault Injection Verification Matrix (Exp L)")

    cols = ["Closed", "Fault\nSeen", "Reopened", "Unsafe\nOpen", "Returned\nIDLE", "Transitions\nLegal", "Final State / Gate"]
    n_rows = len(scenarios)
    n_cols = len(cols) - 1

    mat = np.zeros((n_rows, n_cols), dtype=float)
    cell_text = []
    y_labels = []

    for r_idx, s in enumerate(scenarios):
        sid = s["scenario_id"]
        y_labels.append(sid)
        is_glitch = sid.startswith("16_")
        closed = bool(s["closure_triggered"])
        fault_seen = s["first_fault_detected_s"] is not None
        reopened = bool(s["reopened"])
        unsafe = bool(s["premature_opening_detected"])
        ret_idle = bool(s["returned_idle"])
        legal = bool(s["transition_legality"]["legal"])

        # Color semantics: 1 = safe/expected good, 0 = neutral False, -1 = safety hazard (never occurs)
        mat[r_idx, 0] = 1.0 if ((not is_glitch and closed) or (is_glitch and not closed)) else -1.0
        mat[r_idx, 1] = 0.4 if fault_seen else 0.0
        mat[r_idx, 2] = 1.0 if reopened else 0.15
        mat[r_idx, 3] = -1.0 if unsafe else 1.0
        mat[r_idx, 4] = 1.0 if ret_idle else 0.15
        mat[r_idx, 5] = 1.0 if legal else -1.0

        cell_text.append([
            "NO (OK)" if (is_glitch and not closed) else ("YES" if closed else "NO"),
            f"@{s['first_fault_detected_s']:.1f}s" if fault_seen else "None",
            "YES" if reopened else "HOLD",
            "0 (SAFE)" if not unsafe else "UNSAFE",
            "YES" if ret_idle else "HOLD",
            f"100% ({s['transition_legality']['step_count']})" if legal else "ILLEGAL",
            f"{s['final_crossing_state']} / {s['final_gate_state']}",
        ])

    cmap = matplotlib.colors.ListedColormap(["#FEE2E2", "#F1F5F9", "#FEF3C7", "#DCFCE7"])
    bounds = [-1.5, -0.5, 0.25, 0.6, 1.5]
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)

    ax.imshow(mat, cmap=cmap, norm=norm, aspect="auto")
    for i in range(n_rows):
        for j in range(n_cols):
            ax.text(j, i, cell_text[i][j], ha="center", va="center", fontsize=8.0, fontweight="bold", color="#0F172A")
        ax.text(n_cols + 0.05, i, cell_text[i][-1], ha="left", va="center", fontsize=8.0, color="#1E293B", fontweight="bold")

    ax.set_xticks(list(np.arange(n_cols)) + [n_cols + 0.95])
    ax.set_xticklabels(cols, fontsize=8.8, fontweight="bold")
    ax.xaxis.tick_top()
    ax.set_yticks(np.arange(n_rows))
    ax.set_yticklabels(y_labels, fontsize=8.3)
    ax.set_xlim(-0.5, n_cols + 2.65)
    ax.set_title(
        f"Summary: {n_rows}/18 scenarios legal={exp_l['all_transitions_legal']}, unsafe_openings={exp_l['unsafe_opening_count']}, false_glitch_closed={exp_l['false_train_glitch_closed']}",
        loc="left",
        pad=14,
    )
    _save(fig, fig_dir / "fig08_fault_injection_outcomes.png")


def make_fig09_detection_and_actuation_timing(results_root: Path, fig_dir: Path) -> None:
    exp_a = _load(results_root, "experiments/exp_a_front_detection.json")
    exp_m = _load(results_root, "sensitivity/exp_m_sensitivity.json")["sweeps"]

    fig, axes = plt.subplots(1, 3, figsize=(14.5, 5.2), constrained_layout=True)
    fig.suptitle("Figure 9: Warning/Closure Margins, Parameter Sensitivity & Upstream Placement Engineering Curves")

    # Panel A: Exp A margins
    ax = axes[0]
    closed_rows = [r for r in exp_a["per_event"] if r["event_type"] == "REAL_WORLD_TRAIN_EVENT" and r["margin_full_vs_T2_s"] is not None]
    closed_rows.sort(key=lambda r: r["margin_full_vs_T2_s"])
    y = np.arange(len(closed_rows))
    ax.barh(y, [r["margin_full_vs_T2_s"] for r in closed_rows], color=RED, alpha=0.82, height=0.55, label="Full Close Margin vs T2")
    ax.barh(y, [r["det_lead_vs_T2_s"] for r in closed_rows], color=BLUE, alpha=0.72, height=0.28, label="First Det Lead vs T2")
    ax.axvline(0.0, color=SLATE, ls="--", lw=1.4)
    ax.set_yticks(y)
    ax.set_yticklabels([r["event_id"].replace("train_events/", "") for r in closed_rows], fontsize=8)
    ax.set_xlabel("Time Relative to Adopted T2 Arrival (s)")
    ax.set_title("A. Real B4 Full-Closure Margin (n=9) [Exploratory]", loc="left")
    ax.legend(loc="center left", fontsize=7.6)
    ax.grid(axis="x", alpha=0.25)

    # Panel B: Exp M key sweeps (confirm_frames + detection_confidence on full secondary top axis)
    ax = axes[1]
    cf = exp_m["confirm_frames"]
    dc = exp_m["detection_confidence"]
    tt = exp_m["temporal_tolerance_s"]
    ax.plot([r["param_value"] for r in cf], [r["real_b4_train23_closures"] for r in cf], "o-", color=BLUE, lw=2.0, label="confirm_frames (train23 closures)")
    ax.plot([r["param_value"] for r in cf], [r["real_b4_no_train3_fp"] for r in cf], "s--", color=RED, lw=1.8, label="confirm_frames (no_train3 FP)")
    ax.set_xlabel("confirm_frames (ticks)")
    ax.set_ylabel("Closed Events on Real B4 Cohort")
    ax.set_ylim(-0.8, 25.5)
    ax.set_title("B. Exp M Sensitivity Highlights [Exploratory]", loc="left")
    ax.grid(alpha=0.25)
    ax_t = ax.twiny()
    ax_t.plot([r["param_value"] for r in dc], [r["real_b4_train23_closures"] for r in dc], "^:", color=GREEN, lw=2.0, label="det_conf [0.20–0.65] (top axis)")
    ax_t.set_xlabel("detection_confidence threshold", color=GREEN, fontsize=8.5)
    ax_t.tick_params(axis="x", colors=GREEN)
    ax_t.set_xlim(0.15, 0.70)
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax_t.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="center right", fontsize=7.5)
    ax.text(
        0.04,
        0.92,
        f"Note: tol=0.15s < 0.20s cadence\ntriggers fail-safe on all {tt[0]['real_b4_train23_closures']}/23 + {tt[0]['real_b4_no_train3_fp']}/3",
        transform=ax.transAxes,
        va="top",
        fontsize=7.6,
        bbox={"boxstyle": "round,pad=0.25", "fc": "#FEF2F2", "ec": RED},
    )

    # Panel C: Engineering distance curves
    ax = axes[2]
    profs = exp_a["upstream_camera_distance_engineering_scenarios"]["profiles"]
    colors = [BLUE, GREEN, ORANGE]
    for p, c in zip(profs, colors):
        spds = sorted(int(k) for k in p["required_upstream_distance_m_by_speed_kmh"])
        dists = [p["required_upstream_distance_m_by_speed_kmh"][str(v)] for v in spds]
        ax.plot(spds, dists, "o-", color=c, lw=2.1, label=f"{p['name']} ({p['total_required_time_s']} s)")
        ax.text(spds[-1] + 1.5, dists[-1], f"{dists[-1]:.0f}m", va="center", fontsize=8, color=c, fontweight="bold")
    ax.set_xlim(25, 114)
    ax.set_xlabel("Train Approach Speed (km/h)")
    ax.set_ylabel("Required Upstream Camera Distance (m)")
    ax.set_title("C. Upstream Camera Placement Curves", loc="left")
    ax.legend(loc="upper left", fontsize=7.6)
    ax.grid(alpha=0.25)

    _save(fig, fig_dir / "fig09_detection_and_actuation_timing.png")


def make_fig10_real_world_installation_concept(fig_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(13.5, 6.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    fig.suptitle(
        "Figure 10: Real-World Railway Crossing Four-Layer + Occupancy Field Installation Concept (Bangladesh Context)",
        y=0.98,
    )
    ax.text(
        0.5,
        0.942,
        "Conceptual Field Architecture Addressing Prototype Gaps: Upstream Placement (d_req), Upright Mounts, Crossing Occupancy Sensor & Fail-Safe Barriers",
        ha="center",
        va="center",
        fontsize=9.2,
        color="#334155",
    )

    # Railway track (horizontal)
    ax.add_patch(patches.Rectangle((0.02, 0.44), 0.96, 0.12, facecolor="#E2E8F0", edgecolor="#64748B", lw=1.2))
    ax.plot([0.02, 0.98], [0.47, 0.47], color="#1E293B", lw=2.2)
    ax.plot([0.02, 0.98], [0.53, 0.53], color="#1E293B", lw=2.2)
    for tx in np.linspace(0.03, 0.97, 36):
        ax.plot([tx, tx], [0.455, 0.545], color="#64748B", lw=1.5)

    # Road crossing (vertical, behind track & boxes cleanly without striking through labels)
    ax.add_patch(patches.Rectangle((0.44, 0.14), 0.12, 0.72, facecolor="#F8FAFC", edgecolor="#94A3B8", lw=1.2, zorder=0))
    ax.plot([0.50, 0.50], [0.14, 0.42], color="#94A3B8", ls="--", lw=1.2, zorder=1)
    ax.plot([0.50, 0.50], [0.58, 0.71], color="#94A3B8", ls="--", lw=1.2, zorder=1)
    ax.text(0.50, 0.09, "Highway / Road Carriageway", ha="center", fontweight="bold", color="#334155")

    # Crossing zone hazard box + Dedicated Occupancy Loop
    ax.add_patch(
        patches.Rectangle((0.43, 0.425), 0.14, 0.15, facecolor="#FEE2E2", edgecolor=RED, lw=2.2, ls="--", alpha=0.65, zorder=2)
    )
    _draw_box(
        ax,
        0.38,
        0.22,
        0.24,
        0.13,
        "Layer 5: Occupancy Sensor",
        "Axle counter / radar / LiDAR / loop\nOutputs OCCUPIED | CLEAR | UNKNOWN\n(Missing in prototype dataset)",
        fc="#DCFCE7",
        ec=GREEN,
        title_size=8.8,
        sub_size=7.3,
    )
    _arrow(ax, 0.50, 0.35, 0.50, 0.425, color=GREEN, lw=1.6)

    # Physical motorized gates
    ax.add_patch(patches.Rectangle((0.435, 0.575), 0.13, 0.022, facecolor=RED, edgecolor="white", zorder=3))
    ax.add_patch(patches.Rectangle((0.435, 0.403), 0.13, 0.022, facecolor=RED, edgecolor="white", zorder=3))
    ax.text(
        0.50,
        0.625,
        "Motorized Barrier Gates + Warning Siren",
        ha="center",
        fontweight="bold",
        fontsize=8.8,
        color=RED,
        bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none", "alpha": 0.92},
        zorder=4,
    )

    # Layer 1 Upstream front camera
    _draw_box(
        ax,
        0.04,
        0.69,
        0.25,
        0.16,
        "Layer 1: Upstream Front Camera",
        "Sited d_req = 126–283 m upstream\n(at 60–100 km/h, 7.6–10.2 s budget)\nLocked upright mount + rotation guard",
        fc="#DBEAFE",
        ec=BLUE,
        title_size=9.0,
        sub_size=7.4,
    )
    _arrow(ax, 0.165, 0.69, 0.165, 0.56, "Approach Zone", color=BLUE, lx=0.225, ly=0.62)

    # Layer 2 Side view
    _draw_box(
        ax,
        0.375,
        0.72,
        0.25,
        0.15,
        "Layer 2: Crossing-Zone Side Camera",
        "Tracks lateral train motion across zone\nMOVING vs STOPPED vs glint rejection\n(Planned upgrade; proxy-only in v2)",
        fc="#E0F2FE",
        ec=SKY,
        title_size=9.0,
        sub_size=7.4,
    )
    _arrow(ax, 0.50, 0.72, 0.50, 0.64, color=SKY)

    # Layer 3 Audio microphone
    _draw_box(
        ax,
        0.04,
        0.18,
        0.24,
        0.14,
        "Layer 3: Trackside Horn Mic",
        "16 kHz / 0.5 s hop, natural log-Mel\nSupports dwell extension only\nCannot override silence/road horns",
        fc="#FEF3C7",
        ec=ORANGE,
        title_size=9.0,
        sub_size=7.4,
    )

    # Layer 4 Back / Exit camera
    _draw_box(
        ax,
        0.71,
        0.69,
        0.25,
        0.16,
        "Layer 4: Downstream Exit Camera",
        "Synchronized NTP/PTP/GPS master clock\nDetects positive rear & last_carriage\nNo disappearance-only reopening",
        fc="#FCE7F3",
        ec=PURPLE,
        title_size=9.0,
        sub_size=7.4,
    )
    _arrow(ax, 0.835, 0.69, 0.835, 0.56, "Exit Zone", color=PURPLE, lx=0.885, ly=0.62)

    # Local Edge Fail-Safe Controller Box
    _draw_box(
        ax,
        0.71,
        0.18,
        0.25,
        0.18,
        "Edge Safety PLC / Jetson Node",
        "Runs Causal Collector + V3 FSM Arbiter\nHardwired Watchdog -> Fail-Safe CLOSE\non power, camera, or comms timeout",
        fc="#F1F5F9",
        ec=SLATE,
        title_size=9.0,
        sub_size=7.4,
    )
    ax.annotate("", xy=(0.14, 0.50), xytext=(0.05, 0.50), arrowprops={"arrowstyle": "-|>", "color": SLATE, "lw": 2.4})
    ax.text(0.095, 0.50, "Train Travel Direction", ha="center", va="center", fontsize=8, color="white", fontweight="bold", bbox={"boxstyle": "round,pad=0.2", "fc": SLATE, "ec": "none"})

    _save(fig, fig_dir / "fig10_real_world_installation_concept.png")


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    results_root = repo_root / "results/exploratory_v2"
    fig_dir = repo_root / "docs/generated/final_research_v2/figures"

    make_fig01_system_architecture(results_root, fig_dir)
    make_fig02_four_layer_workflow(results_root, fig_dir)
    make_fig03_gate_closure_timeline(results_root, fig_dir)
    make_fig04_departure_and_clearance_workflow(results_root, fig_dir)
    make_fig05_modality_ablation(results_root, fig_dir)
    make_fig06_closure_performance(results_root, fig_dir)
    make_fig07_premature_opening_analysis(results_root, fig_dir)
    make_fig08_fault_injection_outcomes(results_root, fig_dir)
    make_fig09_detection_and_actuation_timing(results_root, fig_dir)
    make_fig10_real_world_installation_concept(fig_dir)
    print(f"Generated {len(list(fig_dir.glob('fig*.png')))} figures in {fig_dir}")


if __name__ == "__main__":
    main()
