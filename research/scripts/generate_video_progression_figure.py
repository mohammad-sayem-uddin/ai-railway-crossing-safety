"""Video Inference Temporal Progression Figure Generator.

Generates:
- Figure 16: Sequential Passage Progression (Approach -> Passage -> Departure)
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import cv2
import matplotlib.pyplot as plt
import numpy as np
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = PROJECT_ROOT / "experiments/vision/39f402dfe460/checkpoints/weights/best.pt"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "figures/qualitative"


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


def normalize_class_name(raw_name: str | int) -> str:
    name = str(raw_name).strip().lower()
    if name in ("rare", "1"):
        return "rear"
    if name in ("0", "front"):
        return "front"
    if name in ("2", "side"):
        return "side"
    return name


def draw_annotation_box(
    img_rgb: Any, box: tuple[float, float, float, float], label: str, conf: float
) -> Any:
    annotated = img_rgb.copy()
    h, w = annotated.shape[:2]
    x1, y1, x2, y2 = [int(round(v)) for v in box]
    x1, x2 = max(0, min(w - 1, x1)), max(0, min(w - 1, x2))
    y1, y2 = max(0, min(h - 1, y1)), max(0, min(h - 1, y2))

    color_map = {
        "front": (249, 115, 22),
        "rear": (217, 70, 239),
        "side": (14, 165, 233),
    }
    color = color_map.get(label, (34, 197, 94))

    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)
    text = f"{label.upper()} {conf:.2f}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), _ = cv2.getTextSize(text, font, 0.65, 2)
    badge_y1 = max(0, y1 - th - 10)
    badge_y2 = y1
    badge_x2 = min(w, x1 + tw + 12)

    cv2.rectangle(annotated, (x1, badge_y1), (badge_x2, badge_y2), color, -1)
    cv2.putText(annotated, text, (x1 + 6, y1 - 6), font, 0.65, (0, 0, 0), 2, cv2.LINE_AA)
    return annotated


def generate_video_progression_figure(
    video_path: Path | None = None,
    output_dir: Path = OUTPUT_DIR,
) -> None:
    """Generate Figure 16: Sequential Passage Progression (FRONT -> SIDE -> REAR)."""
    model = YOLO(str(MODEL_PATH)) if MODEL_PATH.exists() else None
    frames: list[tuple[str, str, np.ndarray]] = []

    if video_path and video_path.exists() and model is not None:
        cap = cv2.VideoCapture(str(video_path))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total > 0:
            indices = [int(total * 0.15), int(total * 0.50), int(total * 0.85)]
            labels = [
                "(a) t = t_approach (FRONT)",
                "(b) t = t_passage (SIDE)",
                "(c) t = t_departure (REAR)",
            ]
            for idx, lbl in zip(indices, labels, strict=True):
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, f = cap.read()
                if ok and f is not None:
                    rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
                    raw_res: Any = model.predict(source=f, conf=0.25, verbose=False)
                    res_list: list[Any] = list(raw_res) if raw_res is not None else []
                    if res_list:
                        res = res_list[0]
                        boxes: Any = getattr(res, "boxes", None)
                        if boxes is not None and len(boxes) > 0:
                            for i in range(len(boxes)):
                                c_idx = int(boxes.cls[i])
                                clabel = normalize_class_name(res.names.get(c_idx, ""))
                                cconf = float(boxes.conf[i])
                                cbox = tuple(boxes.xyxy[i].cpu().numpy())
                                rgb = draw_annotation_box(rgb, cbox, clabel, cconf)
                    frames.append((lbl, "Video Stream", rgb))
        cap.release()

    if len(frames) < 3:
        test_dir = PROJECT_ROOT / "data/raw/vision/v1/baler.v1i.yolov8/test/images"
        if test_dir.exists() and model is not None:
            from research.scripts.generate_qualitative_figures import find_representative_images
            reps = find_representative_images(model, test_dir)
            cls_order = [
                ("front", "(a) State 1: Approach Phase (FRONT Detected)"),
                ("side", "(b) State 2: Continuous Passage (SIDE Detected)"),
                ("rear", "(c) State 3: Departure Clearance (REAR Detected)"),
            ]
            for c_name, stage_label in cls_order:
                items = reps.get(c_name, [])
                if items:
                    p, dets = items[0]
                    bgr = cv2.imread(str(p))
                    if bgr is None:
                        continue
                    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                    for d_label, conf, box in dets:
                        rgb = draw_annotation_box(rgb, box, d_label, conf)
                    frames.append((stage_label, c_name.upper(), rgb))

    if len(frames) < 3:
        return

    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.2), dpi=300)
    for ax, (title, _state, rgb) in zip(axes, frames[:3], strict=True):
        ax.imshow(rgb)
        ax.set_title(title, fontsize=10, fontweight="bold", pad=8)
        ax.axis("off")

    fig.suptitle(
        "Temporal Passage Progression Across Railway Crossing Detection Zones",
        fontsize=12, fontweight="bold", y=0.98
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg", ".pdf"):
        fig.savefig(output_dir / f"fig16_video_progression_sequence{ext}")
    plt.close(fig)
    print(f"Generated Figure 16 -> {output_dir / 'fig16_video_progression_sequence.png'}")


def main() -> None:
    setup_matplotlib_style()
    parser = argparse.ArgumentParser(description="Generate video temporal progression figure")
    parser.add_argument("--video", type=Path, default=None, help="Optional path to processed video")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    generate_video_progression_figure(video_path=args.video, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
