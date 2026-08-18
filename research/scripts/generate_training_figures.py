"""Training Visualization Generator from Empirical Logs.

Generates:
- Figure 7: Training & Validation Loss Curves
- Figure 8: Model Performance Trajectory (Precision, Recall, mAP)
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CSV_PATH = PROJECT_ROOT / "experiments/vision/39f402dfe460/checkpoints/results.csv"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "figures/training"


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


def load_training_data(csv_path: Path = CSV_PATH) -> dict[str, np.ndarray]:
    """Parse real results.csv into cleaned numpy arrays."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Training results CSV not found at: {csv_path}")

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        header_raw = next(reader)
        headers = [h.strip() for h in header_raw]

        rows = []
        for row in reader:
            if row:
                rows.append([float(v.strip()) for v in row])

    data_matrix = np.array(rows)
    data_dict = {headers[i]: data_matrix[:, i] for i in range(len(headers))}
    return data_dict


def generate_figure_07_training_loss_curves(
    data: dict[str, np.ndarray], output_dir: Path = OUTPUT_DIR
) -> None:
    """Generate Figure 7: Dual-panel Training & Validation Loss Curves."""
    epochs = data["epoch"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.2), dpi=300)

    # Panel A: Box Loss
    ax1.plot(epochs, data["train/box_loss"], label="Train Box Loss", color="#2563eb", lw=1.8)
    ax1.plot(
        epochs, data["val/box_loss"], label="Val Box Loss",
        color="#dc2626", lw=1.8, linestyle="--"
    )
    ax1.set_title("(a) Bounding Box Regression Loss", fontsize=10.5, fontweight="bold", pad=8)
    ax1.set_xlabel("Epoch", fontsize=9.5, fontweight="medium")
    ax1.set_ylabel("Box Loss (CIoU / DFL)", fontsize=9.5, fontweight="medium")
    ax1.set_xlim(1, max(epochs))
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right", fontsize=8.5)

    # Panel B: Classification Loss
    ax2.plot(epochs, data["train/cls_loss"], label="Train Class Loss", color="#2563eb", lw=1.8)
    ax2.plot(
        epochs, data["val/cls_loss"], label="Val Class Loss",
        color="#dc2626", lw=1.8, linestyle="--"
    )
    ax2.set_title("(b) Viewpoint Classification Loss", fontsize=10.5, fontweight="bold", pad=8)
    ax2.set_xlabel("Epoch", fontsize=9.5, fontweight="medium")
    ax2.set_ylabel("Classification Loss (BCE)", fontsize=9.5, fontweight="medium")
    ax2.set_xlim(1, max(epochs))
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right", fontsize=8.5)

    fig.suptitle(
        "YOLOv8n Baseline Training & Validation Loss Evolution Across Epochs",
        fontsize=12, fontweight="bold", y=1.03
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg", ".pdf"):
        fig.savefig(output_dir / f"fig07_training_loss_curves{ext}")
    plt.close(fig)
    print(f"Generated Figure 7 -> {output_dir / 'fig07_training_loss_curves.png'}")


def generate_figure_08_model_performance_curves(
    data: dict[str, np.ndarray], output_dir: Path = OUTPUT_DIR
) -> None:
    """Generate Figure 8: Model Validation Performance Evolution Across Epochs."""
    epochs = data["epoch"]
    map50 = data["metrics/mAP50(B)"]
    map50_95 = data["metrics/mAP50-95(B)"]
    precision = data["metrics/precision(B)"]
    recall = data["metrics/recall(B)"]

    fig, ax = plt.subplots(figsize=(8.5, 4.5), dpi=300)

    ax.plot(
        epochs, map50, label=f"mAP@50 (Final: {map50[-1]:.4f})",
        color="#16a34a", lw=2.2
    )
    ax.plot(
        epochs, map50_95, label=f"mAP@50:95 (Final: {map50_95[-1]:.4f})",
        color="#0284c7", lw=2.0
    )
    ax.plot(
        epochs, precision, label=f"Precision (Final: {precision[-1]:.4f})",
        color="#d97706", lw=1.6, linestyle="--"
    )
    ax.plot(
        epochs, recall, label=f"Recall (Final: {recall[-1]:.4f})",
        color="#9333ea", lw=1.6, linestyle=":"
    )

    best_epoch_idx = int(np.argmax(map50_95))
    best_epoch = epochs[best_epoch_idx]
    best_val = map50_95[best_epoch_idx]
    ax.scatter(
        [best_epoch], [best_val], color="#dc2626", s=50, zorder=5,
        label=f"Best Checkpoint (Epoch {int(best_epoch)})"
    )

    ax.set_title(
        "YOLOv8n Baseline Detection Metrics Trajectory (Held-Out Validation)",
        fontsize=11, fontweight="bold", pad=10
    )
    ax.set_xlabel("Training Epoch", fontsize=9.5, fontweight="medium")
    ax.set_ylabel("Metric Value (0.0 – 1.0)", fontsize=9.5, fontweight="medium")
    ax.set_ylim(0.3, 1.02)
    ax.set_xlim(1, max(epochs))
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower right", fontsize=8.5, framealpha=0.92)

    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg", ".pdf"):
        fig.savefig(output_dir / f"fig08_model_performance_curves{ext}")
    plt.close(fig)
    print(f"Generated Figure 8 -> {output_dir / 'fig08_model_performance_curves.png'}")


def main() -> None:
    setup_matplotlib_style()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = load_training_data()
    generate_figure_07_training_loss_curves(data)
    generate_figure_08_model_performance_curves(data)


if __name__ == "__main__":
    main()
