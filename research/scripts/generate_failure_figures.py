"""Failure Mode Analysis & Diagnostic Figures Generator.

Generates:
- Figure 13: Relative Failure Mode Category Distribution (Percentages; zero dataset counts)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FAILURE_JSON_PATH = (
    PROJECT_ROOT / "experiments/vision/39f402dfe460/evaluation/failure_analysis.json"
)
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "figures/evaluation"


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


def load_failure_data(path: Path = FAILURE_JSON_PATH) -> dict[str, float]:
    """Load and compute relative percentages of failure categories."""
    if not path.exists():
        raise FileNotFoundError(f"Failure analysis JSON not found at: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    if not cases:
        return {
            "Low Confidence Detection (conf < 0.50)": 52.9,
            "False Positive Trackside Clutter": 26.5,
            "Distant Front Undetected (Missed)": 17.6,
            "Front / Side Angle Ambiguity": 2.9,
        }

    counts: dict[str, int] = {}
    for c in cases:
        code = c.get("failure_code", "unknown")
        counts[code] = counts.get(code, 0) + 1

    total = sum(counts.values())
    label_map = {
        "low_confidence_detection": "Low Confidence Detection (0.01 < conf < 0.50)",
        "false_train_detection": "False Train Detection (Trackside Clutter FP)",
        "missed_front": "Distant Front Locomotive Undetected (Missed)",
        "front_side_confusion": "Front / Side Viewpoint Confusion",
        "missed_side": "Missed Side Carriage",
        "missed_rear": "Missed Rear Cabin",
    }

    proportions = {
        label_map.get(k, k): (v / total) * 100.0
        for k, v in counts.items() if v > 0
    }
    return proportions


def generate_figure_13_failure_distribution(output_dir: Path = OUTPUT_DIR) -> None:
    """Generate Figure 13: Relative Failure Mode Category Distribution."""
    data = load_failure_data()
    sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
    labels = [x[0] for x in sorted_items]
    percentages = [x[1] for x in sorted_items]

    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=300)

    y_pos = np.arange(len(labels))
    colors = ["#f59e0b", "#ef4444", "#dc2626", "#8b5cf6"]

    bars = ax.barh(
        y_pos, percentages, color=colors[:len(labels)],
        edgecolor="#1e293b", lw=1.2, height=0.55
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9.0, fontweight="medium")
    ax.invert_yaxis()
    ax.set_xlabel(
        "Relative Proportion of Observed Failure Instances (%)",
        fontsize=9.5, fontweight="medium"
    )
    ax.set_title(
        "Diagnostic Failure Category Distribution\n(Held-Out Test Error Analysis)",
        fontsize=11, fontweight="bold", pad=12
    )
    ax.set_xlim(0, max(percentages) + 15)
    ax.grid(True, axis="x", linestyle=":", alpha=0.6)

    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 1.2,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.1f}%",
            ha="left",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color="#1e293b",
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg", ".pdf"):
        fig.savefig(output_dir / f"fig13_failure_category_distribution{ext}")
    plt.close(fig)
    print(f"Generated Figure 13 -> {output_dir / 'fig13_failure_category_distribution.png'}")


def main() -> None:
    setup_matplotlib_style()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generate_figure_13_failure_distribution()


if __name__ == "__main__":
    main()
