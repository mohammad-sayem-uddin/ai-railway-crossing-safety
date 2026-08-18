"""Qualitative Inference Results & Visual Example Figures Generator.

Generates:
- Figure 14: Qualitative Detection Results (FRONT, SIDE, REAR Viewpoints)
- Figure 15: Diagnostic Failure Mode Visual Examples
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import matplotlib.pyplot as plt
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = PROJECT_ROOT / "experiments/vision/39f402dfe460/checkpoints/weights/best.pt"
TEST_IMG_DIR = PROJECT_ROOT / "data/raw/vision/v1/baler.v1i.yolov8/test/images"
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
    """Draw high-contrast bounding box and badge text in RGB format."""
    annotated = img_rgb.copy()
    h, w = annotated.shape[:2]
    x1, y1, x2, y2 = [int(round(v)) for v in box]
    x1, x2 = max(0, min(w - 1, x1)), max(0, min(w - 1, x2))
    y1, y2 = max(0, min(h - 1, y1)), max(0, min(h - 1, y2))

    color_map = {
        "front": (249, 115, 22),   # Vibrant Amber
        "rear": (217, 70, 239),    # Magenta / Purple
        "side": (14, 165, 233),    # Azure Sky Blue
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


def find_representative_images(
    model: YOLO, img_dir: Path
) -> dict[str, list[tuple[Path, list[Any]]]]:
    """Scan available images and group detections by primary class."""
    results_by_class: dict[str, list[tuple[Path, list[Any]]]] = {
        "front": [], "side": [], "rear": []
    }

    img_paths = sorted(list(img_dir.glob("*.jpg")))
    for p in img_paths:
        raw_res: Any = model.predict(source=str(p), conf=0.40, verbose=False)
        res_list: list[Any] = list(raw_res) if raw_res is not None else []
        if res_list:
            res = res_list[0]
            boxes: Any = getattr(res, "boxes", None)
            if boxes is not None and len(boxes) > 0:
                dets = []
                for i in range(len(boxes)):
                    c_idx = int(boxes.cls[i])
                    raw_name = res.names.get(c_idx, str(c_idx))
                    canon_label = normalize_class_name(raw_name)
                    conf = float(boxes.conf[i])
                    xyxy = boxes.xyxy[i].cpu().numpy()
                    dets.append((canon_label, conf, tuple(xyxy)))

                primary_label = dets[0][0]
                if primary_label in results_by_class and len(results_by_class[primary_label]) < 4:
                    results_by_class[primary_label].append((p, dets))

        if all(len(v) >= 2 for v in results_by_class.values()):
            break

    return results_by_class


def generate_figure_14_qualitative_detections(output_dir: Path = OUTPUT_DIR) -> None:
    """Generate Figure 14: 2x3 Grid of Representative Viewpoint Detections."""
    if not MODEL_PATH.exists() or not TEST_IMG_DIR.exists():
        return

    model = YOLO(str(MODEL_PATH))
    reps = find_representative_images(model, TEST_IMG_DIR)

    selected_items: list[tuple[str, Path, list[Any]]] = []
    for cls_name in ("front", "side", "rear"):
        for item in reps.get(cls_name, [])[:2]:
            selected_items.append((cls_name, item[0], item[1]))

    if len(selected_items) < 6:
        all_imgs = sorted(list(TEST_IMG_DIR.glob("*.jpg")))
        for p in all_imgs:
            if len(selected_items) >= 6:
                break
            if not any(p == item[1] for item in selected_items):
                raw_res: Any = model.predict(source=str(p), conf=0.30, verbose=False)
                res_list: list[Any] = list(raw_res) if raw_res is not None else []
                if res_list:
                    res = res_list[0]
                    boxes: Any = getattr(res, "boxes", None)
                    if boxes is not None and len(boxes) > 0:
                        c_idx = int(boxes.cls[0])
                        label = normalize_class_name(res.names.get(c_idx, str(c_idx)))
                        conf = float(boxes.conf[0])
                        xyxy = tuple(boxes.xyxy[0].cpu().numpy())
                        selected_items.append((label, p, [(label, conf, xyxy)]))

    fig, axes = plt.subplots(2, 3, figsize=(12.0, 7.5), dpi=300)
    axes_flat = axes.flatten()

    for idx, (label, img_path, dets) in enumerate(selected_items[:6]):
        bgr = cv2.imread(str(img_path))
        if bgr is None:
            continue
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        for d_label, conf, box in dets:
            rgb = draw_annotation_box(rgb, box, d_label, conf)

        axes_flat[idx].imshow(rgb)
        axes_flat[idx].set_title(
            f"({chr(97 + idx)}) {label.upper()} Viewpoint Detection",
            fontsize=9.5, fontweight="bold", pad=6
        )
        axes_flat[idx].axis("off")

    fig.suptitle(
        "Qualitative Object Detection Examples on Railway Crossing Scenes",
        fontsize=12, fontweight="bold", y=0.98
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg", ".pdf"):
        fig.savefig(output_dir / f"fig14_qualitative_detections{ext}")
    plt.close(fig)
    print(f"Generated Figure 14 -> {output_dir / 'fig14_qualitative_detections.png'}")


def generate_figure_15_failure_examples(
    output_dir: Path = OUTPUT_DIR / "failures"
) -> None:
    """Generate Figure 15: 1x2 Visual Failure & Edge Case Panel from empirical failures."""
    if not MODEL_PATH.exists():
        return

    failure_json = PROJECT_ROOT / "experiments/vision/39f402dfe460/evaluation/failure_analysis.json"
    raw_dir = PROJECT_ROOT / "data/raw/vision/v1/baler.v1i.yolov8"

    edge_cases: list[tuple[str, Path, list[Any]]] = []

    if failure_json.exists():
        data = json.loads(failure_json.read_text(encoding="utf-8"))
        cases = data.get("cases", [])
        for c in cases:
            img_id = c.get("image_id", "")
            cand = raw_dir / f"{img_id}.jpg"
            if cand.exists():
                f_code = c.get("failure_code", "low_confidence_detection")
                conf = float(c.get("confidence", 0.3))
                pred_lbl = normalize_class_name(c.get("predicted_label", "front"))

                if (
                    f_code == "low_confidence_detection"
                    and not any(e[0].startswith("Low-Confidence") for e in edge_cases)
                ):
                    edge_cases.append((
                        f"Low-Confidence Detection (conf = {conf:.2f} < 0.50)",
                        cand,
                        [(pred_lbl, conf, (50.0, 50.0, 550.0, 450.0))]
                    ))
                elif (
                    f_code == "false_train_detection"
                    and not any(e[0].startswith("False Train") for e in edge_cases)
                ):
                    edge_cases.append((
                        "False Train Detection (Trackside Clutter FP)",
                        cand,
                        [(pred_lbl, conf, (80.0, 100.0, 480.0, 420.0))]
                    ))
                elif (
                    f_code == "front_side_confusion"
                    and not any(e[0].startswith("Viewpoint Confusion") for e in edge_cases)
                ):
                    edge_cases.append((
                        "Viewpoint Confusion (Front vs Side Boundary)",
                        cand,
                        [(pred_lbl, conf, (100.0, 80.0, 520.0, 460.0))]
                    ))

            if len(edge_cases) >= 2:
                break

    if len(edge_cases) < 2:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.0, 4.8), dpi=300)
    for ax, (desc, p, _dets) in zip((ax1, ax2), edge_cases[:2], strict=True):
        bgr = cv2.imread(str(p))
        if bgr is None:
            continue
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        model = YOLO(str(MODEL_PATH))
        raw_res: Any = model.predict(source=str(p), conf=0.10, verbose=False)
        res_list: list[Any] = list(raw_res) if raw_res is not None else []
        if res_list:
            res = res_list[0]
            boxes: Any = getattr(res, "boxes", None)
            if boxes is not None and len(boxes) > 0:
                for i in range(len(boxes)):
                    c_idx = int(boxes.cls[i])
                    label = normalize_class_name(res.names.get(c_idx, ""))
                    conf = float(boxes.conf[i])
                    box = tuple(boxes.xyxy[i].cpu().numpy())
                    rgb = draw_annotation_box(rgb, box, label, conf)

        ax.imshow(rgb)
        ax.set_title(desc, fontsize=9.5, fontweight="bold", pad=6)
        ax.axis("off")

    fig.suptitle(
        "Qualitative Failure & Boundary Case Analysis",
        fontsize=11.5, fontweight="bold", y=0.98
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg", ".pdf"):
        fig.savefig(output_dir / f"fig15_failure_examples{ext}")
    plt.close(fig)
    print(f"Generated Figure 15 -> {output_dir / 'fig15_failure_examples.png'}")


def main() -> None:
    setup_matplotlib_style()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "failures").mkdir(parents=True, exist_ok=True)
    generate_figure_14_qualitative_detections()
    generate_figure_15_failure_examples()


if __name__ == "__main__":
    main()
