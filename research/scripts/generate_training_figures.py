"""Figure 7: Academic Learning Curves & Overfitting Analysis Generator.

Directly styled to match academic publication standards (matching user reference):
- Figure 7 Title & Subtitle with parameter count and checkpoint selection
- Panel A: Training and validation loss (Train vs Val Total Loss with best epoch marker)
- Panel B: Validation metric & accuracy trajectory (mAP@50, mAP@50:95 with best epoch marker)
- Bottom explanatory caption analyzing convergence and confirming absence of overfitting
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
        "savefig.pad_inches": 0.15,
    })


def load_training_data(csv_path: Path = CSV_PATH) -> dict[str, np.ndarray]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Training results CSV not found at: {csv_path}")

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = [h.strip() for h in next(reader)]
        rows = [[float(x.strip()) for x in r] for r in reader if r]

    data_matrix = np.array(rows)
    return {headers[i]: data_matrix[:, i] for i in range(len(headers))}


def generate_figure_07_learning_curves(
    data: dict[str, np.ndarray] | None = None,
    output_dir: Path = OUTPUT_DIR,
) -> None:
    """Generate Figure 7 styled exactly after the user reference."""
    if data is None:
        data = load_training_data()
    epochs = data["epoch"]

    # Compute Total Combined Loss = Box + Class + DFL
    train_total_loss = data["train/box_loss"] + data["train/cls_loss"] + data["train/dfl_loss"]
    val_total_loss = data["val/box_loss"] + data["val/cls_loss"] + data["val/dfl_loss"]

    map50 = data["metrics/mAP50(B)"]
    map50_95 = data["metrics/mAP50-95(B)"]
    precision = data["metrics/precision(B)"]
    recall = data["metrics/recall(B)"]

    # Find minimum validation loss epoch
    min_val_idx = int(np.argmin(val_total_loss))
    min_val_epoch = epochs[min_val_idx]
    min_val_loss = val_total_loss[min_val_idx]

    # Find best mAP epoch
    best_map_idx = int(np.argmax(map50_95))
    best_map_epoch = epochs[best_map_idx]
    best_map_val = map50_95[best_map_idx]
    best_map50_val = map50[best_map_idx]

    # Create figure with extra bottom space for academic caption
    fig = plt.figure(figsize=(12.0, 6.2), dpi=300)
    gs = fig.add_gridspec(1, 2, left=0.08, right=0.96, top=0.82, bottom=0.24, wspace=0.22)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    # Sample subsampled markers every 5 epochs so the plot is clean and not overcrowded
    step = 5
    marker_indices = np.arange(0, len(epochs), step)
    if marker_indices[-1] != len(epochs) - 1:
        marker_indices = np.append(marker_indices, len(epochs) - 1)

    # -------------------------------------------------------------------------
    # Panel A: Training and validation loss
    # -------------------------------------------------------------------------
    ax1.plot(
        epochs, train_total_loss,
        color="#1e40af", lw=1.8, label="Training loss",
        marker="o", markevery=marker_indices, markersize=4.5, markerfacecolor="#1e40af"
    )
    ax1.plot(
        epochs, val_total_loss,
        color="#b45309", lw=1.8, label="Validation loss",
        marker="s", markevery=marker_indices, markersize=4.5, markerfacecolor="#d97706"
    )

    # Vertical reference line at minimum val loss
    ax1.axvline(
        min_val_epoch, color="#991b1b", linestyle="--", lw=1.3, alpha=0.85,
        label=f"Min Val Loss (Epoch {int(min_val_epoch)})"
    )
    ax1.scatter([min_val_epoch], [min_val_loss], color="#991b1b", s=35, zorder=5)
    ax1.annotate(
        f"min val loss epoch {int(min_val_epoch)}\nloss: {min_val_loss:.3f}",
        xy=(min_val_epoch, min_val_loss),
        xytext=(min_val_epoch - 38, min_val_loss + 0.45),
        fontsize=8.0, fontweight="bold", color="#7f1d1d",
        arrowprops=dict(arrowstyle="->", color="#991b1b", lw=1.0)
    )

    ax1.set_title("A. Training and validation loss", fontsize=11, fontweight="bold", pad=10)
    ax1.set_xlabel("Epoch", fontsize=9.5, fontweight="medium")
    ax1.set_ylabel("Loss (Total Box + Cls + DFL)", fontsize=9.5, fontweight="medium")
    ax1.set_xlim(1, max(epochs))
    ax1.set_ylim(1.5, 7.0)
    ax1.grid(True, linestyle=":", alpha=0.55, color="#cbd5e1")
    ax1.legend(loc="upper right", fontsize=8.5, framealpha=0.92)

    # -------------------------------------------------------------------------
    # Panel B: Training and validation accuracy / mAP trajectory
    # -------------------------------------------------------------------------
    ax2.plot(
        epochs, map50,
        color="#15803d", lw=2.0, label="Validation mAP@50",
        marker="o", markevery=marker_indices, markersize=4.5, markerfacecolor="#15803d"
    )
    ax2.plot(
        epochs, map50_95,
        color="#0284c7", lw=1.8, label="Validation mAP@50:95",
        marker="^", markevery=marker_indices, markersize=4.5, markerfacecolor="#0284c7"
    )
    ax2.plot(
        epochs, precision,
        color="#64748b", lw=1.2, linestyle="--", label="Precision",
        alpha=0.75
    )
    ax2.plot(
        epochs, recall,
        color="#9333ea", lw=1.2, linestyle=":", label="Recall",
        alpha=0.75
    )

    # Vertical reference line at best mAP epoch
    ax2.axvline(
        best_map_epoch, color="#991b1b", linestyle="--", lw=1.3, alpha=0.85,
        label=f"Best Checkpoint (Epoch {int(best_map_epoch)})"
    )
    ax2.scatter([best_map_epoch], [best_map_val], color="#991b1b", s=35, zorder=5)
    ax2.annotate(
        f"best checkpoint (epoch {int(best_map_epoch)})\nmAP@50:95: {best_map_val:.3f}",
        xy=(best_map_epoch, best_map_val),
        xytext=(best_map_epoch - 42, best_map_val - 0.14),
        fontsize=8.0, fontweight="bold", color="#7f1d1d",
        arrowprops=dict(arrowstyle="->", color="#991b1b", lw=1.0)
    )

    ax2.set_title("B. Validation detection metrics & mAP", fontsize=11, fontweight="bold", pad=10)
    ax2.set_xlabel("Epoch", fontsize=9.5, fontweight="medium")
    ax2.set_ylabel("Metric Value (0.0 – 1.0)", fontsize=9.5, fontweight="medium")
    ax2.set_xlim(1, max(epochs))
    ax2.set_ylim(0.40, 1.04)
    ax2.grid(True, linestyle=":", alpha=0.55, color="#cbd5e1")
    ax2.legend(loc="lower right", fontsize=8.0, framealpha=0.92)

    # -------------------------------------------------------------------------
    # Main Header & Subtitle
    # -------------------------------------------------------------------------
    fig.suptitle(
        "Figure 7. YOLOv8n Baseline Training and Validation Learning Curves",
        fontsize=13, fontweight="bold", y=0.96, color="#0f172a"
    )
    fig.text(
        0.5, 0.89,
        "YOLOv8n Learning Curves — Baseline Run 39f402dfe460 "
        "(3,006,038 parameters, 100 epochs on MPS)",
        ha="center", fontsize=9.5, fontweight="medium", color="#475569"
    )

    # -------------------------------------------------------------------------
    # Bottom Academic Caption & Overfitting Diagnostic
    # -------------------------------------------------------------------------
    caption_text = (
        "Training and validation learning curves for YOLOv8n (3.01M parameters) across 100 epochs: "
        "(A) Total loss (CIoU bounding box + classification + distribution focal loss) "
        "illustrating steady monotonic reduction in training loss while validation loss steadily "
        f"drops and stabilizes near {min_val_loss:.3f} (epoch {int(min_val_epoch)}), and "
        "(B) Validation performance trajectory showing rapid convergence of mAP@50 and mAP@50:95. "
        "Diagnosis: The parallel downward trend and absence of validation loss divergence "
        "indicate clean convergence without severe overfitting; the best model checkpoint "
        f"is restored at epoch {int(best_map_epoch)} "
        f"(mAP@50: {best_map50_val:.4f}, mAP@50:95: {best_map_val:.4f})."
    )
    fig.text(
        0.08, 0.04, caption_text,
        ha="left", va="bottom", fontsize=7.8, fontstyle="italic", color="#334155",
        wrap=True
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg", ".pdf"):
        fig.savefig(output_dir / f"fig07_training_loss_curves{ext}")
    plt.close(fig)
    print(f"Generated Figure 7 -> {output_dir / 'fig07_training_loss_curves.png'}")


# Backward-compatible alias
generate_figure_07_training_loss_curves = generate_figure_07_learning_curves


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
    generate_figure_07_learning_curves(data=data, output_dir=OUTPUT_DIR)
    generate_figure_08_model_performance_curves(data, OUTPUT_DIR)


if __name__ == "__main__":
    main()
