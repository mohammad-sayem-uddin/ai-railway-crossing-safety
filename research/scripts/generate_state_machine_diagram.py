"""Railway Gate Safety State Machine Diagram Generator.

Generates:
- Figure 6: Formal Gate Safety State Machine with safety invariant paths
  and conservative clearance verification.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "figures/system"


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


def generate_figure_06_gate_safety_state_machine(output_dir: Path = OUTPUT_DIR) -> None:
    """Generate Figure 6: Railway Gate Safety State Machine."""
    fig, ax = plt.subplots(figsize=(11.0, 6.5), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.5,
        0.96,
        "Railway Crossing Gate Safety State Machine",
        ha="center",
        va="top",
        fontsize=13,
        fontweight="bold",
        color="#0f172a",
    )

    def draw_state(
        x: float, y: float, w: float, h: float,
        name: str, desc: str,
        gate_state: str,
        fc: str = "#f8fafc", ec: str = "#334155",
        tc: str = "#0f172a", lw: float = 1.6
    ) -> None:
        p = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.03,rounding_size=0.04",
            facecolor=fc, edgecolor=ec, lw=lw, zorder=2
        )
        ax.add_patch(p)
        ax.text(
            x + w / 2, y + h * 0.72, name,
            ha="center", va="center", fontsize=9.0, fontweight="bold", color=tc, zorder=3
        )
        ax.text(
            x + w / 2, y + h * 0.44, desc,
            ha="center", va="center", fontsize=7.5, color="#475569", zorder=3
        )
        badge_tc = "#991b1b" if "CLOSED" in gate_state or "CLOSING" in gate_state else "#166534"
        ax.text(
            x + w / 2, y + h * 0.18, f"[{gate_state}]",
            ha="center", va="center", fontsize=7.0, fontweight="bold", color=badge_tc, zorder=3
        )

    # 1. Top row
    draw_state(
        0.04, 0.68, 0.20, 0.20, "1. IDLE",
        "No evidence detected\nNormal road traffic", "GATE OPEN",
        fc="#f0fdf4", ec="#22c55e"
    )
    draw_state(
        0.28, 0.68, 0.20, 0.20, "2. SUSPICIOUS",
        "Transient 1-frame cue\nConfirmation timer started", "GATE OPEN (ARMED)",
        fc="#fefce8", ec="#eab308"
    )
    draw_state(
        0.52, 0.68, 0.20, 0.20, "3. APPROACH CONFIRMED",
        "N ≥ 3 consecutive FRONT\nEarly safety alert", "GATE TRIGGERED",
        fc="#fff7ed", ec="#ea580c"
    )
    draw_state(
        0.76, 0.68, 0.20, 0.20, "4. GATE CLOSING",
        "Barrier descent active\nSafety warning sirens", "GATE CLOSING",
        fc="#fef2f2", ec="#dc2626"
    )

    ax.annotate(
        "", xy=(0.28, 0.78), xytext=(0.24, 0.78),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569")
    )
    ax.annotate(
        "", xy=(0.52, 0.78), xytext=(0.48, 0.78),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569")
    )
    ax.annotate(
        "", xy=(0.76, 0.78), xytext=(0.72, 0.78),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="#dc2626")
    )
    ax.annotate(
        "", xy=(0.86, 0.52), xytext=(0.86, 0.68),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="#dc2626")
    )

    # 2. Bottom row
    draw_state(
        0.76, 0.32, 0.20, 0.20, "5. TRAIN PASSING",
        "Continuous SIDE carriages\nPersistence active", "GATE CLOSED (LOCKED)",
        fc="#fef2f2", ec="#b91c1c", lw=2.0
    )
    draw_state(
        0.52, 0.32, 0.20, 0.20, "6. CLEARANCE CANDIDATE",
        "REAR detected / SIDE gone\nDeparture sequence", "GATE CLOSED (HOLD)",
        fc="#fdf4ff", ec="#c084fc"
    )
    draw_state(
        0.28, 0.32, 0.20, 0.20, "7. SAFETY VERIFICATION",
        "Hold window (≥ 3.0s)\nZero active detections", "GATE CLOSED (VERIFY)",
        fc="#eff6ff", ec="#3b82f6"
    )
    draw_state(
        0.04, 0.32, 0.20, 0.20, "8. GATE OPENING",
        "Clearance satisfied\nBarrier ascends safely", "GATE OPENING",
        fc="#f0fdf4", ec="#16a34a"
    )

    ax.annotate(
        "", xy=(0.72, 0.42), xytext=(0.76, 0.42),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569")
    )
    ax.annotate(
        "", xy=(0.48, 0.42), xytext=(0.52, 0.42),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569")
    )
    ax.annotate(
        "", xy=(0.24, 0.42), xytext=(0.28, 0.42),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="#16a34a")
    )
    ax.annotate(
        "", xy=(0.14, 0.68), xytext=(0.14, 0.52),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="#16a34a")
    )

    ax.annotate(
        "Glitch Dismissed",
        xy=(0.18, 0.88), xytext=(0.34, 0.88),
        arrowprops=dict(arrowstyle="->", lw=1.2, color="#64748b", linestyle=":"),
        fontsize=7.5, color="#64748b", ha="center"
    )

    ax.text(
        0.5,
        0.08,
        "CORE SAFETY INVARIANT: All ambiguous states and dropouts default to KEEPING GATE CLOSED.\n"
        "Gate opening requires affirmative multi-stage temporal verification.",
        ha="center",
        va="center",
        fontsize=8.5,
        fontweight="bold",
        color="#991b1b",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#fef2f2", edgecolor="#f87171", lw=1.2)
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg", ".pdf"):
        fig.savefig(output_dir / f"fig06_gate_safety_state_machine{ext}")
    plt.close(fig)
    print(f"Generated Figure 6 -> {output_dir / 'fig06_gate_safety_state_machine.png'}")


def main() -> None:
    setup_matplotlib_style()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generate_figure_06_gate_safety_state_machine()


if __name__ == "__main__":
    main()
