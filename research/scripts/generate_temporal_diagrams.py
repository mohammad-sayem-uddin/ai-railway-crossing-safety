"""Temporal Evidence & Logic Diagrams Generator.

Generates:
- Figure 4: Multi-Frame Confirmation Logic (Persistent vs Glitch)
- Figure 5: Temporal Evidence Persistence & Decay Over Time (Conceptual behavior plot)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "figures/temporal"


def setup_matplotlib_style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
        "mathtext.fontset": "dejavusans",
        "figure.autolayout": False,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.1,
    })


def generate_figure_04_multiframe_confirmation(output_dir: Path = OUTPUT_DIR) -> None:
    """Generate Figure 4: Multi-Frame Confirmation vs False Positive Rejection."""
    fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.5,
        0.95,
        "Temporal Evidence Buffer: Multi-Frame Confirmation Logic",
        ha="center",
        va="top",
        fontsize=12,
        fontweight="bold",
        color="#0f172a",
    )

    def draw_chip(
        x: float, y: float, w: float, h: float, text: str, fc: str, ec: str, tc: str = "#0f172a"
    ) -> None:
        p = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.03",
            facecolor=fc, edgecolor=ec, lw=1.5, zorder=2
        )
        ax.add_patch(p)
        ax.text(
            x + w / 2, y + h / 2, text,
            ha="center", va="center", fontsize=8.5, fontweight="bold", color=tc, zorder=3
        )

    # Top Track: Valid Train Sequence
    ax.text(
        0.04, 0.76, "Scenario A: Consistent Train Signal",
        fontsize=9.5, fontweight="bold", color="#1e3a8a"
    )
    draw_chip(0.04, 0.58, 0.16, 0.14, "Frame t\nDetection (c₁)", "#eff6ff", "#3b82f6")
    ax.annotate(
        "", xy=(0.26, 0.65), xytext=(0.20, 0.65),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="#64748b")
    )

    draw_chip(0.26, 0.58, 0.16, 0.14, "Frame t+1\nDetection (c₂)", "#eff6ff", "#3b82f6")
    ax.annotate(
        "", xy=(0.48, 0.65), xytext=(0.42, 0.65),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="#64748b")
    )

    draw_chip(0.48, 0.58, 0.16, 0.14, "Frame t+2\nDetection (c₃)", "#eff6ff", "#3b82f6")
    ax.annotate(
        "", xy=(0.70, 0.65), xytext=(0.64, 0.65),
        arrowprops=dict(arrowstyle="->", lw=1.8, color="#16a34a")
    )

    draw_chip(
        0.70, 0.56, 0.26, 0.18,
        "CONFIRMED EVIDENCE\n(N ≥ 3 frames)\nStatus: ACTIVE",
        "#dcfce7", "#16a34a", tc="#14532d"
    )

    # Bottom Track: Isolated False Positive
    ax.text(
        0.04, 0.38, "Scenario B: Transient Glitch / Single-Frame Noise",
        fontsize=9.5, fontweight="bold", color="#991b1b"
    )
    draw_chip(0.04, 0.20, 0.16, 0.14, "Frame t\nDetection (c₁)", "#fef2f2", "#ef4444")
    ax.annotate(
        "", xy=(0.26, 0.27), xytext=(0.20, 0.27),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="#64748b")
    )

    draw_chip(
        0.26, 0.20, 0.16, 0.14, "Frame t+1\n[No Detection]",
        "#f8fafc", "#cbd5e1", tc="#64748b"
    )
    ax.annotate(
        "", xy=(0.48, 0.27), xytext=(0.42, 0.27),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="#64748b")
    )

    draw_chip(
        0.48, 0.20, 0.16, 0.14, "Frame t+2\n[No Detection]",
        "#f8fafc", "#cbd5e1", tc="#64748b"
    )
    ax.annotate(
        "", xy=(0.70, 0.27), xytext=(0.64, 0.27),
        arrowprops=dict(arrowstyle="->", lw=1.8, color="#dc2626")
    )

    draw_chip(
        0.70, 0.18, 0.26, 0.18,
        "REJECTED / SUPPRESSED\n(Confirmation Failed)\nStatus: NO ACTION",
        "#fee2e2", "#dc2626", tc="#7f1d1d"
    )

    ax.text(
        0.5,
        0.03,
        "Principle: High-frequency noise and momentary false positives "
        "are rejected before reaching gate logic.",
        ha="center",
        va="bottom",
        fontsize=8.5,
        fontstyle="italic",
        color="#475569",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg", ".pdf"):
        fig.savefig(output_dir / f"fig04_multiframe_confirmation{ext}")
    plt.close(fig)
    print(f"Generated Figure 4 -> {output_dir / 'fig04_multiframe_confirmation.png'}")


def generate_figure_05_evidence_persistence(output_dir: Path = OUTPUT_DIR) -> None:
    """Generate Figure 5: Conceptual Evidence Persistence and Decay Behavior."""
    fig, ax = plt.subplots(figsize=(9.0, 4.8), dpi=300)

    t = np.linspace(0, 10, 300)
    raw_conf = np.zeros_like(t)
    filtered_conf = np.zeros_like(t)
    confirmed_state = np.zeros_like(t)

    # 1. Approach
    mask_train = (t >= 1.0) & (t <= 4.0)
    raw_conf[mask_train] = 0.88 + 0.05 * np.sin(2 * np.pi * 1.5 * t[mask_train])

    # 2. Reappearance
    mask_reappear = (t >= 4.8) & (t <= 7.0)
    raw_conf[mask_reappear] = 0.91 + 0.04 * np.cos(2 * np.pi * 1.2 * t[mask_reappear])

    alpha = 0.4
    state_conf = 0.0
    consecutive = 0
    misses = 0

    for i in range(len(t)):
        c = raw_conf[i]
        if c > 0.3:
            consecutive += 1
            misses = 0
            state_conf = alpha * c + (1 - alpha) * state_conf if state_conf > 0 else c
            if consecutive >= 9:
                confirmed_state[i] = 1.0
        else:
            if misses < 30:
                misses += 1
                state_conf = max(0.0, state_conf * 0.98)
                if consecutive >= 9:
                    confirmed_state[i] = 1.0
            else:
                consecutive = 0
                state_conf = 0.0
                confirmed_state[i] = 0.0

        filtered_conf[i] = state_conf

    ax.plot(
        t, raw_conf, label="Raw Neural Detector Confidence",
        color="#94a3b8", linestyle="--", lw=1.8
    )
    ax.plot(
        t, filtered_conf, label="Temporally Filtered Confidence",
        color="#2563eb", lw=2.4
    )
    ax.fill_between(
        t, 0, confirmed_state * 0.95,
        color="#10b981", alpha=0.15, label="Confirmed Gate-Close Evidence (Active)"
    )

    ax.axvspan(
        4.0, 4.8, color="#fef08a", alpha=0.35,
        label="Momentary Occlusion (Persistence Retains State)"
    )
    ax.axhline(
        0.50, color="#dc2626", linestyle=":", lw=1.2,
        label="Nominal Confidence Threshold"
    )

    ax.set_title(
        "Temporal Evidence Buffer: Persistence & Dropout Tolerance Dynamics\n"
        "(Conceptual Dynamic Simulation)",
        fontsize=11, fontweight="bold", pad=12
    )
    ax.set_xlabel("Time Elapsed (seconds)", fontsize=9.5, fontweight="medium")
    ax.set_ylabel("Confidence Score / Evidence Level", fontsize=9.5, fontweight="medium")
    ax.set_ylim(-0.05, 1.15)
    ax.set_xlim(0, 10)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", fontsize=8.0, framealpha=0.92)

    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg", ".pdf"):
        fig.savefig(output_dir / f"fig05_evidence_persistence{ext}")
    plt.close(fig)
    print(f"Generated Figure 5 -> {output_dir / 'fig05_evidence_persistence.png'}")


def main() -> None:
    setup_matplotlib_style()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generate_figure_04_multiframe_confirmation()
    generate_figure_05_evidence_persistence()


if __name__ == "__main__":
    main()
