"""Publication Architecture Diagram Generator.

Generates high-resolution publication-quality architecture figures:
- Figure 1: Overall Multimodal Research System Architecture
- Figure 2: Frame-by-Frame Vision Detection & Temporal Pipeline
- Figure 3: Two-Camera Railway Crossing Conceptual Layout
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "figures/architecture"


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


def draw_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    subtitle: str | None = None,
    facecolor: str = "#f8fafc",
    edgecolor: str = "#334155",
    textcolor: str = "#0f172a",
    lw: float = 1.5,
    title_size: int = 10,
    sub_size: int = 8,
    border_style: str = "-",
) -> None:
    rect = patches.FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.03,rounding_size=0.04",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=lw,
        linestyle=border_style,
        zorder=2,
    )
    ax.add_patch(rect)
    if subtitle:
        ax.text(
            x + w / 2,
            y + h * 0.62,
            title,
            ha="center",
            va="center",
            fontsize=title_size,
            fontweight="bold",
            color=textcolor,
            zorder=3,
        )
        ax.text(
            x + w / 2,
            y + h * 0.32,
            subtitle,
            ha="center",
            va="center",
            fontsize=sub_size,
            color="#475569",
            zorder=3,
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
            color=textcolor,
            zorder=3,
        )


def draw_arrow(
    ax: plt.Axes,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    label: str | None = None,
    color: str = "#475569",
    lw: float = 1.6,
    label_offset_y: float = 0.03,
) -> None:
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=lw,
            mutation_scale=14,
            shrinkA=2,
            shrinkB=2,
        ),
        zorder=1,
    )
    if label:
        ax.text(
            (x1 + x2) / 2,
            (y1 + y2) / 2 + label_offset_y,
            label,
            ha="center",
            va="bottom",
            fontsize=7.5,
            color="#334155",
            fontweight="medium",
            backgroundcolor="white",
            zorder=4,
        )


def generate_figure_01_system_architecture(output_dir: Path = OUTPUT_DIR) -> None:
    """Generate Figure 1: Overall Multimodal Research System Architecture."""
    fig, ax = plt.subplots(figsize=(10.5, 6.0), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.5,
        0.96,
        "Multimodal AI Railway Crossing Safety Architecture",
        ha="center",
        va="top",
        fontsize=13,
        fontweight="bold",
        color="#0f172a",
    )

    # 1. Vision Modality Pipeline (Top)
    draw_box(
        ax, 0.05, 0.65, 0.16, 0.18,
        "Optical Sensors", "Camera Video Stream\n(640×640 Native)",
        facecolor="#eff6ff", edgecolor="#3b82f6", textcolor="#1e3a8a",
    )
    draw_arrow(ax, 0.21, 0.74, 0.26, 0.74, label="Raw Frames")

    draw_box(
        ax, 0.26, 0.65, 0.18, 0.18,
        "Neural Detector", "YOLOv8n Baseline\n(Front, Side, Rear)",
        facecolor="#eff6ff", edgecolor="#2563eb", textcolor="#1e3a8a",
    )
    draw_arrow(ax, 0.44, 0.74, 0.49, 0.74, label="Detections (BBox, Conf)")

    draw_box(
        ax, 0.49, 0.65, 0.19, 0.18,
        "Temporal Filter", "3-Frame Confirmation\nPersistence & Decay",
        facecolor="#f0fdf4", edgecolor="#16a34a", textcolor="#14532d",
    )

    # 2. Audio Modality Pipeline (Bottom)
    draw_box(
        ax, 0.05, 0.18, 0.16, 0.18,
        "Acoustic Sensors", "Field Microphone Array\n(Audio Stream)",
        facecolor="#fdf4ff", edgecolor="#c084fc", textcolor="#581c87",
    )
    draw_arrow(ax, 0.21, 0.27, 0.26, 0.27, label="Audio Chunks")

    draw_box(
        ax, 0.26, 0.18, 0.18, 0.18,
        "Acoustic Classifier", "Train Horn / Engine\nPattern Recognition",
        facecolor="#fdf4ff", edgecolor="#a855f7", textcolor="#581c87",
    )
    draw_arrow(ax, 0.44, 0.27, 0.49, 0.27, label="Acoustic Evidence")

    draw_box(
        ax, 0.49, 0.18, 0.19, 0.18,
        "Audio Evidence Gate", "Closure-Support Only\n(Never Authorizes Opening)",
        facecolor="#fef2f2", edgecolor="#dc2626", textcolor="#7f1d1d",
        border_style="--",
    )

    # 3. Central Decision & Gate Logic
    draw_arrow(ax, 0.68, 0.74, 0.74, 0.53, label="Confirmed Vision Evidence")
    draw_arrow(ax, 0.68, 0.27, 0.74, 0.47, label="Supporting Horn Evidence")

    draw_box(
        ax, 0.74, 0.38, 0.21, 0.26,
        "Safety Decision Logic",
        "Deterministic State Machine\nSafety-First Invariant\n(Uncertainty Favors Closed)",
        facecolor="#fefce8", edgecolor="#ca8a04", textcolor="#713f12",
        lw=2.0,
    )

    # Final Gate Actuation
    draw_arrow(ax, 0.845, 0.38, 0.845, 0.18, label="Control Command")
    draw_box(
        ax, 0.75, 0.05, 0.19, 0.12,
        "Gate Controller", "Crossing Barrier Actuation",
        facecolor="#0f172a", edgecolor="#0f172a", textcolor="#ffffff",
    )

    # Safety Invariant Note
    ax.text(
        0.5,
        0.02,
        "Safety Guarantee: Optical evidence required for departure clearance. "
        "Acoustic horn detection acts strictly as an auxiliary trigger for conservative closure.",
        ha="center",
        va="bottom",
        fontsize=8.5,
        fontstyle="italic",
        color="#475569",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg", ".pdf"):
        fig.savefig(output_dir / f"fig01_system_architecture{ext}")
    plt.close(fig)
    print(f"Generated Figure 1 -> {output_dir / 'fig01_system_architecture.png'}")


def generate_figure_02_vision_pipeline(output_dir: Path = OUTPUT_DIR) -> None:
    """Generate Figure 2: Frame-by-Frame Vision Detection & Temporal Pipeline."""
    fig, ax = plt.subplots(figsize=(10.0, 4.2), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.5,
        0.93,
        "Vision Detection & Temporal Confirmation Pipeline",
        ha="center",
        va="top",
        fontsize=12,
        fontweight="bold",
        color="#0f172a",
    )

    stages = [
        ("Input Video", "Railway Camera\nContinuous Feed", "#f1f5f9", "#64748b"),
        ("Frame Extraction", "RGB Stream\nResolution Invariant", "#eff6ff", "#3b82f6"),
        ("YOLOv8n Model", "Deep Feature Backbone\nMulti-Scale Detection", "#eff6ff", "#2563eb"),
        ("Detection Parsing", "Bounding Boxes\nConfidence Scores", "#f8fafc", "#475569"),
        ("Canonical Classes", "FRONT | SIDE | REAR\nState Viewpoints", "#fef3c7", "#d97706"),
        ("Temporal Buffer", "3-Frame Confirmation\nDropout Tolerance", "#ecfdf5", "#059669"),
        ("Confirmed State", "Verified Visual\nPassage Evidence", "#0f172a", "#0f172a"),
    ]

    w, h = 0.115, 0.50
    y = 0.28
    gap = 0.026
    start_x = 0.02

    for i, (title, sub, fc, ec) in enumerate(stages):
        x = start_x + i * (w + gap)
        tc = "#ffffff" if fc == "#0f172a" else "#0f172a"
        draw_box(ax, x, y, w, h, title, sub, facecolor=fc, edgecolor=ec, textcolor=tc)
        if i < len(stages) - 1:
            draw_arrow(ax, x + w, y + h / 2, x + w + gap, y + h / 2)

    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg", ".pdf"):
        fig.savefig(output_dir / f"fig02_vision_pipeline{ext}")
    plt.close(fig)
    print(f"Generated Figure 2 -> {output_dir / 'fig02_vision_pipeline.png'}")


def generate_figure_03_twocamera_crossing_concept(output_dir: Path = OUTPUT_DIR) -> None:
    """Generate Figure 3: Two-Camera Railway Crossing Conceptual Layout."""
    fig, ax = plt.subplots(figsize=(10.0, 5.0), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.5,
        0.95,
        "Two-Camera Dual-Zone Railway Crossing Detection (Conceptual Architecture)",
        ha="center",
        va="top",
        fontsize=12,
        fontweight="bold",
        color="#0f172a",
    )

    # Railway Track representation
    ax.add_patch(
        patches.Rectangle(
            (0.04, 0.44), 0.92, 0.12,
            facecolor="#f1f5f9", edgecolor="#94a3b8", lw=1.5, zorder=1
        )
    )
    ax.plot([0.04, 0.96], [0.48, 0.48], color="#64748b", lw=2, zorder=2)
    ax.plot([0.04, 0.96], [0.52, 0.52], color="#64748b", lw=2, zorder=2)

    # Crossing Road intersection
    ax.add_patch(
        patches.Rectangle(
            (0.44, 0.25), 0.12, 0.50,
            facecolor="#e2e8f0", edgecolor="#64748b", linestyle="--", lw=1.5, zorder=1
        )
    )
    ax.text(
        0.50, 0.50, "ROADWAY\nCROSSING\nZONE",
        ha="center", va="center", fontsize=8, fontweight="bold", color="#475569", zorder=3
    )

    # Train motion arrow
    ax.annotate(
        "",
        xy=(0.92, 0.50),
        xytext=(0.08, 0.50),
        arrowprops=dict(arrowstyle="->", color="#ef4444", lw=2.5, mutation_scale=18),
        zorder=3,
    )
    ax.text(
        0.25, 0.54, "Direction of Travel",
        ha="center", va="bottom", fontsize=8, color="#ef4444", fontweight="bold", zorder=3
    )

    # Camera 1
    draw_box(
        ax, 0.08, 0.68, 0.28, 0.22,
        "Camera 1: Approach Monitor",
        "Detects locomotive (FRONT)\nTriggers early gate closure\nVerifies safe closing distance",
        facecolor="#eff6ff", edgecolor="#2563eb",
    )
    draw_arrow(ax, 0.22, 0.68, 0.22, 0.57, label="Field of View")

    # Camera 2
    draw_box(
        ax, 0.64, 0.68, 0.28, 0.22,
        "Camera 2: Clearance Monitor",
        "Detects train end (REAR)\nMonitors passage (SIDE)\nVerifies full track clearance",
        facecolor="#fdf4ff", edgecolor="#9333ea",
    )
    draw_arrow(ax, 0.78, 0.68, 0.78, 0.57, label="Field of View")

    # Crossing Gate Actuators
    draw_box(
        ax, 0.41, 0.08, 0.18, 0.15,
        "Safety Gate Barrier",
        "Closed: FRONT/SIDE detected\nOpening: REAR cleared + hold",
        facecolor="#fef2f2", edgecolor="#b91c1c",
    )
    draw_arrow(ax, 0.44, 0.25, 0.47, 0.23)
    draw_arrow(ax, 0.56, 0.25, 0.53, 0.23)

    ax.text(
        0.5,
        0.01,
        "Conceptual Multi-Camera Setup: Spatial coverage ensures overlapping detection boundaries "
        "and eliminates blind spots.",
        ha="center",
        va="bottom",
        fontsize=8,
        fontstyle="italic",
        color="#64748b",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg", ".pdf"):
        fig.savefig(output_dir / f"fig03_twocamera_crossing_concept{ext}")
    plt.close(fig)
    print(f"Generated Figure 3 -> {output_dir / 'fig03_twocamera_crossing_concept.png'}")


def main() -> None:
    setup_matplotlib_style()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generate_figure_01_system_architecture()
    generate_figure_02_vision_pipeline()
    generate_figure_03_twocamera_crossing_concept()


if __name__ == "__main__":
    main()
