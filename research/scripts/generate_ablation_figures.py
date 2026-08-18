"""Ablation Study Comparison & Multi-Level Safety Evaluation Generator.

Processes ablation benchmark records from research/templates/ablation_template.csv
(or a populated results CSV) to generate multi-dimensional safety metric comparisons.

Strictly obeys research integrity rules: Does NOT fabricate experimental results.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_CSV = Path(__file__).resolve().parent.parent / "templates/ablation_template.csv"
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


def generate_ablation_figures(
    csv_path: Path = TEMPLATE_CSV,
    output_dir: Path = OUTPUT_DIR,
) -> bool:
    """Read ablation study records and plot safety comparisons if populated."""
    if not csv_path.exists():
        print(f"Ablation file not found: {csv_path}")
        return False

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("Ablation CSV is empty.")
        return False

    # Check if numerical metrics have been populated
    has_data = all(
        str(row.get("safety_critical_miss_rate_pct") or "").strip() != ""
        for row in rows
    )

    if not has_data:
        print(
            f"Note: Ablation template at {csv_path.name} contains experiment definitions "
            "(B0–B4) but empirical metrics are unpopulated pending future runs. "
            "Skipping figure generation to avoid fabricated data."
        )
        return False

    ablation_ids = [r["ablation_id"] for r in rows]
    miss_rates = [float(r["safety_critical_miss_rate_pct"]) for r in rows]
    false_closures = [float(r["false_closure_rate_pct"]) for r in rows]
    premature_openings = [float(r["premature_opening_rate_pct"]) for r in rows]

    x = np.arange(len(ablation_ids))
    width = 0.25

    fig, ax = plt.subplots(figsize=(9.0, 4.8), dpi=300)
    ax.bar(
        x - width, miss_rates, width,
        label="Safety-Critical Miss Rate (%)", color="#dc2626"
    )
    ax.bar(
        x, false_closures, width,
        label="False Gate Closure Rate (%)", color="#f59e0b"
    )
    ax.bar(
        x + width, premature_openings, width,
        label="Premature Opening Rate (%)", color="#7c3aed"
    )

    ax.set_title(
        "Ablation Study: Multimodal Pipeline Safety Metric Comparison",
        fontsize=11, fontweight="bold", pad=12
    )
    ax.set_xlabel("System Configuration Layer", fontsize=9.5, fontweight="medium")
    ax.set_ylabel("Error Rate (%)", fontsize=9.5, fontweight="medium")
    ax.set_xticks(x)
    ax.set_xticklabels(ablation_ids, fontsize=10, fontweight="bold")
    ax.grid(True, axis="y", linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", fontsize=8.5)

    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg", ".pdf"):
        fig.savefig(output_dir / f"fig17_ablation_comparison{ext}")
    plt.close(fig)
    print(f"Generated Ablation Figure -> {output_dir / 'fig17_ablation_comparison.png'}")
    return True


def main() -> None:
    setup_matplotlib_style()
    parser = argparse.ArgumentParser(
        description="Generate ablation comparison figures from real data"
    )
    parser.add_argument(
        "--csv", type=Path, default=TEMPLATE_CSV,
        help="Path to populated ablation CSV"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=OUTPUT_DIR,
        help="Output directory"
    )
    args = parser.parse_args()

    generate_ablation_figures(csv_path=args.csv, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
