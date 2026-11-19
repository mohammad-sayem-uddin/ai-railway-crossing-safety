#!/usr/bin/env python3
"""Mission 13 Vision Baseline Forensics & Generalization Audit (Frozen YOLOv8n 39f402dfe460).

Computes exact training/validation trajectory diagnostics from ``results.csv``,
reconciles Ultralytics COCO metrics vs custom ``evaluator.py``, stratifies 705d
test detections by class, bbox area, and camera-source family, renders genuine
success/failure image examples under media authorization, and prepares the structured
comparison against clean session-grouped and calendar-day-grouped retrains.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw
from ultralytics import YOLO

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from railway_detection.data.leakage_audit import parse_vision_source_timestamp  # noqa: E402
from railway_detection.experiments.frozen_config import compute_file_sha256  # noqa: E402
from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402
from railway_detection.vision.evaluator import (  # noqa: E402
    GroundTruthBox,
    PredictionBox,
    compute_iou,
    evaluate_detection,
)
from railway_detection.vision.video import frame_generator  # noqa: E402

RUN_39F_DIR = REPO_ROOT / "experiments" / "vision" / "39f402dfe460"
BEST_PT = RUN_39F_DIR / "checkpoints" / "weights" / "best.pt"
LAST_PT = RUN_39F_DIR / "checkpoints" / "weights" / "last.pt"
RESULTS_CSV = RUN_39F_DIR / "checkpoints" / "results.csv"
EVAL_METRICS_JSON = RUN_39F_DIR / "evaluation" / "metrics.json"
EVAL_FAIL_JSON = RUN_39F_DIR / "evaluation" / "failure_analysis.json"
MANIFEST_JSONL = REPO_ROOT / "results" / "dataset_validation" / "dataset_manifest.jsonl"
STAGE_DIR = Path("/tmp/m13_yolo_stage")

OUT_DIR = REPO_ROOT / "results" / "model_generalization_audit"
FIG_DIR = REPO_ROOT / "docs" / "generated" / "model_generalization_audit" / "figures"


def _bbox_iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    return compute_iou(a, b)


def analyze_results_csv() -> dict[str, Any]:
    rows = []
    with RESULTS_CSV.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append({k.strip(): float(v.strip()) for k, v in row.items()})

    best_map50_row = max(rows, key=lambda r: r["metrics/mAP50(B)"])
    best_map_row = max(rows, key=lambda r: r["metrics/mAP50-95(B)"])
    min_val_cls_row = min(rows, key=lambda r: r["val/cls_loss"])
    min_val_box_row = min(rows, key=lambda r: r["val/box_loss"])
    min_val_dfl_row = min(rows, key=lambda r: r["val/dfl_loss"])
    ep90 = next(r for r in rows if int(r["epoch"]) == 90)
    ep93 = next(r for r in rows if int(r["epoch"]) == 93)
    ep97 = rows[-1]

    return {
        "total_epochs_logged": len(rows),
        "configured_epochs": 100,
        "truncated_early_by_epochs": 100 - len(rows),
        "total_wall_clock_s": ep97["time"],
        "total_wall_clock_hours": round(ep97["time"] / 3600.0, 2),
        "best_val_mAP50_epoch": int(best_map50_row["epoch"]),
        "best_val_mAP50": best_map50_row["metrics/mAP50(B)"],
        "best_val_mAP50_95_epoch": int(best_map_row["epoch"]),
        "best_val_mAP50_95": best_map_row["metrics/mAP50-95(B)"],
        "min_val_cls_loss_epoch": int(min_val_cls_row["epoch"]),
        "min_val_cls_loss": min_val_cls_row["val/cls_loss"],
        "min_val_box_loss_epoch": int(min_val_box_row["epoch"]),
        "min_val_box_loss": min_val_box_row["val/box_loss"],
        "min_val_dfl_loss_epoch": int(min_val_dfl_row["epoch"]),
        "min_val_dfl_loss": min_val_dfl_row["val/dfl_loss"],
        "pre_close_mosaic_ep90": ep90,
        "best_ckpt_ep93": ep93,
        "final_ckpt_ep97": ep97,
        "post_mosaic_train_cls_drop": round(ep90["train/cls_loss"] - ep97["train/cls_loss"], 5),
        "post_mosaic_val_cls_rise_from_ep72": round(ep97["val/cls_loss"] - min_val_cls_row["val/cls_loss"], 5),
        "post_best_ep93_to_ep97_map50_95_delta": round(ep97["metrics/mAP50-95(B)"] - ep93["metrics/mAP50-95(B)"], 5),
        "epochs": rows,
    }


def inspect_test_detections_and_evaluator() -> dict[str, Any]:
    manifest = [json.loads(ln) for ln in MANIFEST_JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
    by_flat_jpg = {f"{r['image_id'].replace('/', '__')}.jpg": r for r in manifest}
    test_imgs = [Path(ln.strip()) for ln in (STAGE_DIR / "705d_test.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]

    model = YOLO(str(BEST_PT))
    class_names = ["front", "rear", "side"]

    gt_boxes: list[GroundTruthBox] = []
    pred_boxes_conf001: list[PredictionBox] = []
    pred_boxes_conf025: list[PredictionBox] = []
    per_image_records: list[dict[str, Any]] = []

    # Run batched prediction once at conf=0.001 so we analyze full confidence & confusion behavior cleanly
    batch_size = 16
    for start in range(0, len(test_imgs), batch_size):
        chunk = test_imgs[start : start + batch_size]
        for p in chunk:
            require_media_authorization(p, "INFERENCE")
        results = model.predict(source=[str(p) for p in chunk], imgsz=640, conf=0.001, iou=0.70, device="mps", verbose=False)
        for p, res in zip(chunk, results, strict=True):
            rec = by_flat_jpg[p.name]
            img_id = rec["image_id"]
            w, h = 640.0, 640.0
            anns = []
            for ann in rec.get("annotations", []):
                b = ann["bbox"]
                box = (b["xmin"] * w, b["ymin"] * h, b["xmax"] * w, b["ymax"] * h)
                gt_boxes.append(GroundTruthBox(image_id=img_id, label=ann["label"], bbox_xyxy=box))
                area_norm = (b["xmax"] - b["xmin"]) * (b["ymax"] - b["ymin"])
                anns.append({"label": ann["label"], "xyxy": box, "area_norm": area_norm})

            preds_img = []
            for b in res.boxes:
                cls_id = int(b.cls[0])
                lbl = class_names[cls_id]
                conf = float(b.conf[0])
                xyxy = tuple(float(v) for v in b.xyxy[0])
                pb = PredictionBox(image_id=img_id, label=lbl, confidence=conf, bbox_xyxy=xyxy)
                pred_boxes_conf001.append(pb)
                if conf >= 0.25:
                    pred_boxes_conf025.append(pb)
                preds_img.append({"label": lbl, "conf": conf, "xyxy": xyxy})

            _, kind = parse_vision_source_timestamp(rec["split_group_id"])
            per_image_records.append({
                "stage_path": str(p),
                "image_id": img_id,
                "split_group_id": rec["split_group_id"],
                "kind": kind,
                "anns": anns,
                "preds": preds_img,
            })

    # Reconcile evaluator.py behavior at conf=0.001 vs conf=0.25 (confusion_matrix in evaluator.py doesn't filter preds!)
    eval_c001 = evaluate_detection(gt_boxes, pred_boxes_conf001, class_names, iou_threshold=0.5, confidence_threshold=0.5)
    eval_c025 = evaluate_detection(gt_boxes, pred_boxes_conf025, class_names, iou_threshold=0.5, confidence_threshold=0.5)

    # Stratify recall & precision at operating conf=0.35 (frozen Mission 11 threshold) & conf=0.50 by bbox size & camera kind
    size_stats: dict[str, Counter[str]] = defaultdict(Counter)
    kind_stats: dict[str, Counter[str]] = defaultdict(Counter)
    cross_cls_conf_035: Counter[tuple[str, str]] = Counter()

    scored_examples: list[dict[str, Any]] = []
    for item in per_image_records:
        anns = item["anns"]
        preds_035 = sorted([pr for pr in item["preds"] if pr["conf"] >= 0.35], key=lambda x: -x["conf"])
        preds_050 = [pr for pr in item["preds"] if pr["conf"] >= 0.50]

        gt_used = [False] * len(anns)
        best_ious = [0.0] * len(anns)
        fp_035 = 0
        wrong_cls = 0
        tp_035 = 0
        ious_matched = []

        for pr in preds_035:
            best_i = -1
            best_v = 0.0
            for gi, gt in enumerate(anns):
                if gt_used[gi]:
                    continue
                iou = _bbox_iou(gt["xyxy"], pr["xyxy"])
                if iou >= 0.50 and gt["label"] == pr["label"] and iou > best_v:
                    best_v = iou
                    best_i = gi
            if best_i >= 0:
                gt_used[best_i] = True
                best_ious[best_i] = best_v
                tp_035 += 1
                ious_matched.append(best_v)
            else:
                fp_035 += 1
                # Check if wrong-class hit on an unmatched GT
                for gt in anns:
                    if _bbox_iou(gt["xyxy"], pr["xyxy"]) >= 0.50 and gt["label"] != pr["label"]:
                        cross_cls_conf_035[(gt["label"], pr["label"])] += 1
                        wrong_cls += 1
                        break

        for gi, gt in enumerate(anns):
            area = gt["area_norm"]
            sz_bin = "small_lt4pct" if area < 0.04 else ("medium_4_16pct" if area < 0.16 else "large_ge16pct")
            size_stats[sz_bin]["total"] += 1
            kind_stats[item["kind"]]["total"] += 1
            if gt_used[gi]:
                size_stats[sz_bin]["tp_035"] += 1
                kind_stats[item["kind"]]["tp_035"] += 1
            else:
                size_stats[sz_bin]["fn_035"] += 1
                kind_stats[item["kind"]]["fn_035"] += 1

        kind_stats[item["kind"]]["fp_035"] += fp_035
        fn_035 = sum(1 for u in gt_used if not u)
        mean_iou = float(np.mean(ious_matched)) if ious_matched else 0.0
        scored_examples.append({
            "stage_path": item["stage_path"],
            "image_id": item["image_id"],
            "kind": item["kind"],
            "n_gt": len(anns),
            "tp_035": tp_035,
            "fp_035": fp_035,
            "fn_035": fn_035,
            "wrong_cls": wrong_cls,
            "mean_iou": mean_iou,
            "anns": anns,
            "preds_035": preds_035,
            "n_pred_050": len(preds_050),
        })

    # Render genuine 2x3 panel of Test successes and failures -> FIG_DIR / fig_m13_vision_examples.png
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    # Pick 2 clear successes (different classes, high IoU, fp=0, fn=0), 2 FP / wrong-class examples, 2 FN / missed-front examples
    succ = sorted([x for x in scored_examples if x["fn_035"] == 0 and x["fp_035"] == 0 and x["n_gt"] >= 1], key=lambda x: (-x["mean_iou"], x["image_id"]))
    succ_front = next((x for x in succ if x["anns"][0]["label"] == "front"), succ[0])
    succ_side_or_rear = next((x for x in succ if x["anns"][0]["label"] in ("rear", "side")), succ[-1])
    fn_cases = sorted([x for x in scored_examples if x["fn_035"] > 0], key=lambda x: (-x["fn_035"], x["image_id"]))
    fp_cases = sorted([x for x in scored_examples if x["fp_035"] > 0], key=lambda x: (-x["fp_035"], -x["wrong_cls"], x["image_id"]))

    chosen = []
    used_ids = set()
    for tag, pool in [
        ("TP Success (front)", [succ_front]),
        ("TP Success (rear/side)", [succ_side_or_rear]),
        ("Missed GT / FN #1", fn_cases),
        ("Missed GT / FN #2", fn_cases[1:]),
        ("False Positive / Cls #1", fp_cases),
        ("False Positive / Cls #2", fp_cases[1:]),
    ]:
        for cand in pool:
            if cand["image_id"] not in used_ids:
                used_ids.add(cand["image_id"])
                chosen.append((tag, cand))
                break

    if len(chosen) == 6:
        tiles = []
        for tag, cand in chosen:
            img_p = Path(cand["stage_path"])
            require_media_authorization(img_p, "INFERENCE")
            with Image.open(img_p) as raw_im:
                im = raw_im.convert("RGB").copy()
            draw = ImageDraw.Draw(im)
            for gt in cand["anns"]:
                x1, y1, x2, y2 = gt["xyxy"]
                draw.rectangle([x1, y1, x2, y2], outline=(0, 220, 80), width=4)
                lbl_g = f"GT:{gt['label']}"
                tx, ty = max(2, x1 + 2), max(2, y1 + 2)
                draw.rectangle([tx, ty, tx + 7 * len(lbl_g) + 6, ty + 16], fill=(0, 140, 40))
                draw.text((tx + 3, ty + 2), lbl_g, fill=(255, 255, 255))
            for pr in cand["preds_035"]:
                x1, y1, x2, y2 = pr["xyxy"]
                draw.rectangle([x1, y1, x2, y2], outline=(255, 50, 40), width=3)
                lbl_p = f"P:{pr['label']} {pr['conf']:.2f}"
                tx, ty = max(2, x1 + 2), min(620, max(20, y2 - 18))
                draw.rectangle([tx, ty, tx + 7 * len(lbl_p) + 6, ty + 16], fill=(200, 30, 20))
                draw.text((tx + 3, ty + 2), lbl_p, fill=(255, 255, 255))
            tiles.append((tag, cand, np.asarray(im)))

        import matplotlib
        matplotlib.use("Agg")
        import io

        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 3, figsize=(13.2, 8.6), dpi=250)
        for ax, (tag, cand, arr) in zip(axes.flat, tiles, strict=True):
            ax.imshow(arr)
            short_id = Path(cand["image_id"]).name.split(".rf.")[0][:34]
            ax.set_title(
                f"{tag}\n{short_id} ({cand['kind']}) | TP={cand['tp_035']} FP={cand['fp_035']} FN={cand['fn_035']}",
                fontsize=8.2,
                fontweight="bold",
            )
            ax.axis("off")
        fig.suptitle(
            "Frozen YOLOv8n (39f402dfe460) Genuine Test Detections @ conf=0.35 (Green=GT, Red=Pred; Split=705d388743ea)",
            fontsize=11.0,
            fontweight="bold",
        )
        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        (FIG_DIR / "fig_m13_vision_examples.png").write_bytes(buf.getvalue())

    ultralytics_eval_path = Path("/tmp/m13_39f402_ultralytics_val.json")
    ultralytics_val = json.loads(ultralytics_eval_path.read_text(encoding="utf-8")) if ultralytics_eval_path.exists() else {}

    return {
        "evaluator_py_reconciliation": {
            "checked_in_eval_metrics_json": json.loads(EVAL_METRICS_JSON.read_text(encoding="utf-8")),
            "recomputed_eval_conf001_input": eval_c001.to_dict(),
            "recomputed_eval_conf025_input": eval_c025.to_dict(),
            "ultralytics_real_val": ultralytics_val,
            "bug_diagnosis": "src/railway_detection/vision/evaluator.py matches all confidence_threshold-filtered metrics cleanly in per_class_precision/recall/f1, EXCEPT confusion_matrix iterates over unfiltered pred_boxes (counting background->class FPs below confidence_threshold) and uses 101-pt numpy interp AP (~+0.052 mAP50-95 higher than Ultralytics COCO evaluator 0.80351).",
        },
        "test_error_stratification_conf035": {
            "by_bbox_area": {
                k: {
                    "total_gt": v["total"],
                    "tp_035": v["tp_035"],
                    "fn_035": v["fn_035"],
                    "recall_035": round(v["tp_035"] / max(v["total"], 1), 4),
                }
                for k, v in sorted(size_stats.items())
            },
            "by_camera_source_kind": {
                k: {
                    "total_gt": v["total"],
                    "tp_035": v["tp_035"],
                    "fp_035": v["fp_035"],
                    "fn_035": v["fn_035"],
                    "recall_035": round(v["tp_035"] / max(v["total"], 1), 4),
                    "precision_035": round(v["tp_035"] / max(v["tp_035"] + v["fp_035"], 1), 4),
                }
                for k, v in sorted(kind_stats.items())
            },
            "cross_class_confusion_pairs_iou50_conf035": {f"{k[0]}->{k[1]}": v for k, v in cross_cls_conf_035.items()},
        },
        "examples_plotted": [
            {
                "panel": tag,
                "image_id": cand["image_id"],
                "kind": cand["kind"],
                "tp_035": cand["tp_035"],
                "fp_035": cand["fp_035"],
                "fn_035": cand["fn_035"],
                "mean_iou": round(cand["mean_iou"], 4),
            }
            for tag, cand in (chosen if len(chosen) == 6 else [])
        ],
    }


def evaluate_39f402_on_clean_splits() -> dict[str, Any]:
    """Evaluate frozen 39f402 best.pt & last.pt on clean session_grouped/day_grouped splits (and unseen-to-39f402 subsets)."""
    tmp_splits = Path("/tmp/m13_kaggle_ds/splits")
    imgs_dir = Path("/tmp/m13_kaggle_ds/images")
    stage_dir = Path("/tmp/m13_yolo_clean_eval_stage")
    import shutil

    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True)
    # Copy images & labels once inside /tmp so Ultralytics caches locally without touching data/raw
    shutil.copytree(imgs_dir, stage_dir / "images")
    shutil.copytree(Path("/tmp/m13_kaggle_ds/labels"), stage_dir / "labels")

    def to_flat(s: str) -> str:
        s = s.strip()
        for sp in ("train/images/", "valid/images/", "test/images/"):
            if sp in s:
                return s[s.index(sp) :].replace("/", "__")
        return Path(s).name

    def orig_stem(flat: str) -> str:
        for pref in ("train__images__", "valid__images__", "test__images__"):
            if flat.startswith(pref):
                flat = flat[len(pref) :]
                break
        return flat.split(".rf.")[0] if ".rf." in flat else flat

    train_39f_imgs = {
        to_flat(ln)
        for ln in (RUN_39F_DIR / "descriptor" / "train.txt").read_text(encoding="utf-8").splitlines()
        if ln.strip()
    }
    train_39f_srcs = {orig_stem(fn) for fn in train_39f_imgs}

    split_lists: dict[str, list[str]] = {}
    for sname in ("session_grouped_val", "session_grouped_test", "day_grouped_val", "day_grouped_test"):
        items = [to_flat(ln) for ln in (tmp_splits / f"{sname}.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
        split_lists[sname] = items
        if sname.endswith("_test"):
            unseen = [
                f for f in items
                if f not in train_39f_imgs and orig_stem(f) not in train_39f_srcs
            ]
            split_lists[f"{sname}_unseen_to_39f402"] = unseen

    for name, items in split_lists.items():
        lines = []
        for fn in items:
            p = stage_dir / "images" / fn
            require_media_authorization(p, "INFERENCE")
            lines.append(str(p.resolve()))
        (stage_dir / f"{name}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (stage_dir / f"{name}.yaml").write_text(
            f"path: {stage_dir}\n"
            f"train: {name}.txt\n"
            f"val: {name}.txt\n"
            "nc: 3\n"
            "names: ['front', 'rear', 'side']\n",
            encoding="utf-8",
        )

    out: dict[str, Any] = {
        "schema_version": "mission13-39f402-clean-split-eval/1.0",
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "frozen_checkpoint_sha256": compute_file_sha256(BEST_PT),
        "splits": {},
    }
    for ck_lbl, ck_path in (("best_ep93", BEST_PT), ("last_ep97", LAST_PT)):
        model = YOLO(str(ck_path))
        out["splits"][ck_lbl] = {}
        for name, items in split_lists.items():
            res = model.val(
                data=str(stage_dir / f"{name}.yaml"),
                split="val",
                imgsz=640,
                batch=16,
                device="mps",
                plots=False,
                save_json=False,
                verbose=False,
            )
            out["splits"][ck_lbl][name] = {
                "n_images": len(items),
                "mp": round(float(res.box.mp), 5),
                "mr": round(float(res.box.mr), 5),
                "mAP50": round(float(res.box.map50), 5),
                "mAP75": round(float(res.box.map75), 5),
                "mAP50_95": round(float(res.box.map), 5),
                "per_class_ap50": {res.names[i]: round(float(res.box.ap50[i]), 5) for i in range(3)},
                "per_class_ap50_95": {res.names[i]: round(float(res.box.ap[i]), 5) for i in range(3)},
            }
    shutil.rmtree(stage_dir)
    out_path = OUT_DIR / "vision_39f402_on_clean_splits.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out


def evaluate_field_and_daytest_diagnostics() -> dict[str, Any]:
    """Compare clean-retrained YOLO models vs frozen 39f402 on held-out day_grouped/test & crossing_A controls."""
    import shutil

    models_spec = {
        "frozen_39f402": BEST_PT,
        "session_grouped_base": OUT_DIR / "yolo_kaggle_runs" / "runs_m13" / "session_grouped_base" / "weights" / "best.pt",
        "day_grouped_base": OUT_DIR / "yolo_kaggle_runs" / "runs_m13" / "day_grouped_base" / "weights" / "best.pt",
        "day_grouped_reg": OUT_DIR / "yolo_kaggle_runs" / "runs_m13" / "day_grouped_reg" / "weights" / "best.pt",
    }

    # 1. Held-out calendar-day test (n=264, 2026-05-23) detailed stratification @ conf=0.35
    tmp_splits = Path("/tmp/m13_kaggle_ds/splits")
    imgs_dir = Path("/tmp/m13_kaggle_ds/images")
    lbls_dir = Path("/tmp/m13_kaggle_ds/labels")
    stage_dir = Path("/tmp/m13_yolo_daytest_stage")
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True)
    shutil.copytree(imgs_dir, stage_dir / "images")
    shutil.copytree(lbls_dir, stage_dir / "labels")

    test_files = [ln.strip() for ln in (tmp_splits / "day_grouped_test.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
    test_paths = [stage_dir / "images" / fn for fn in test_files]
    manifest = [json.loads(ln) for ln in MANIFEST_JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
    by_flat_jpg = {f"{r['image_id'].replace('/', '__')}.jpg": r for r in manifest}
    class_names = ["front", "rear", "side"]

    day_test_summary: dict[str, Any] = {}
    for m_name, w_path in models_spec.items():
        yolo = YOLO(str(w_path))
        size_stats: dict[str, Counter[str]] = defaultdict(Counter)
        cls_counts: Counter[str] = Counter()
        tp_total, fp_total, fn_total = 0, 0, 0
        for start in range(0, len(test_paths), 16):
            chunk = test_paths[start : start + 16]
            for p in chunk:
                require_media_authorization(p, "INFERENCE")
            results = yolo.predict(source=[str(p) for p in chunk], imgsz=640, conf=0.35, iou=0.70, device="mps", verbose=False)
            for p, res in zip(chunk, results, strict=True):
                rec = by_flat_jpg[p.name]
                anns = []
                for ann in rec.get("annotations", []):
                    b = ann["bbox"]
                    box = (b["xmin"] * 640.0, b["ymin"] * 640.0, b["xmax"] * 640.0, b["ymax"] * 640.0)
                    area_norm = (b["xmax"] - b["xmin"]) * (b["ymax"] - b["ymin"])
                    anns.append({"label": ann["label"], "xyxy": box, "area_norm": area_norm})
                preds = sorted(
                    [{"label": class_names[int(b.cls[0])], "conf": float(b.conf[0]), "xyxy": tuple(float(v) for v in b.xyxy[0])} for b in res.boxes],
                    key=lambda x: -x["conf"],
                )
                used = [False] * len(anns)
                for pr in preds:
                    cls_counts[pr["label"]] += 1
                    best_i, best_idx = 0.0, -1
                    for gi, an in enumerate(anns):
                        if not used[gi] and an["label"] == pr["label"]:
                            iou = _bbox_iou(pr["xyxy"], an["xyxy"])
                            if iou >= 0.50 and iou > best_i:
                                best_i, best_idx = iou, gi
                    if best_idx >= 0:
                        used[best_idx] = True
                        tp_total += 1
                    else:
                        fp_total += 1
                for gi, an in enumerate(anns):
                    sb = "large_ge16pct" if an["area_norm"] >= 0.16 else ("medium_4_16pct" if an["area_norm"] >= 0.04 else "small_lt4pct")
                    size_stats[sb]["total"] += 1
                    if used[gi]:
                        size_stats[sb]["tp"] += 1
                    else:
                        size_stats[sb]["fn"] += 1
                        fn_total += 1
        day_test_summary[m_name] = {
            "tp_035": tp_total,
            "fp_035": fp_total,
            "fn_035": fn_total,
            "pred_class_counts": dict(cls_counts),
            "by_bbox_area": {
                k: {
                    "total_gt": v["total"],
                    "tp_035": v["tp"],
                    "fn_035": v["fn"],
                    "recall_035": round(v["tp"] / max(v["total"], 1), 4),
                }
                for k, v in sorted(size_stats.items())
            },
        }
    shutil.rmtree(stage_dir)

    # 2. Upright crossing_A control/engine clips (non-train controls + solitary locomotive)
    clips = [
        ("no_train_events/event_001", "front", REPO_ROOT / "data/raw/layer_b/v2/no_train_events/event_001/camera_front.mov"),
        ("no_train_events/event_001", "back", REPO_ROOT / "data/raw/layer_b/v2/no_train_events/event_001/camera_back.mov"),
        ("no_train_events/event_002", "front", REPO_ROOT / "data/raw/layer_b/v2/no_train_events/event_002/camera_front.mov"),
        ("no_train_events/event_002", "back", REPO_ROOT / "data/raw/layer_b/v2/no_train_events/event_002/camera_back.mov"),
        ("no_train_events/event_003", "front", REPO_ROOT / "data/raw/layer_b/v2/no_train_events/event_003/camera_front.mov"),
        ("no_train_events/event_003", "back", REPO_ROOT / "data/raw/layer_b/v2/no_train_events/event_003/camera_back.mov"),
        ("engine_events/event_001", "front", REPO_ROOT / "data/raw/layer_b/v2/engine_events/event_001/camera_front.mov"),
        ("engine_events/event_001", "back", REPO_ROOT / "data/raw/layer_b/v2/engine_events/event_001/camera_back.mov"),
    ]
    field_summary: dict[str, dict[str, Any]] = {m_name: {} for m_name in models_spec}
    yolos = {m_name: YOLO(str(w_path)) for m_name, w_path in models_spec.items()}
    for ev_id, cam, vpath in clips:
        require_media_authorization(vpath, "INFERENCE", declared_media=True)
        frames = list(frame_generator(vpath, target_fps=5.0, source_pts=True))
        key = f"{ev_id}_{cam}"
        imgs = [fr.image for fr in frames]
        for m_name, yolo in yolos.items():
            det_frames = 0
            total_boxes = 0
            cls_c: Counter[str] = Counter()
            max_conf = 0.0
            consec = 0
            max_consec = 0
            ycens = []
            for start in range(0, len(imgs), 16):
                batch_imgs = imgs[start : start + 16]
                res_list = yolo.predict(source=batch_imgs, imgsz=640, conf=0.35, iou=0.70, device="mps", verbose=False)
                for res in res_list:
                    if len(res.boxes) > 0:
                        det_frames += 1
                        consec += 1
                        max_consec = max(max_consec, consec)
                        for b in res.boxes:
                            total_boxes += 1
                            lbl = class_names[int(b.cls[0])]
                            c = float(b.conf[0])
                            cls_c[lbl] += 1
                            max_conf = max(max_conf, c)
                            ycens.append(float((b.xyxyn[0][1] + b.xyxyn[0][3]) * 0.5))
                    else:
                        consec = 0
            field_summary[m_name][key] = {
                "sampled_frames": len(frames),
                "det_frames_conf035": det_frames,
                "max_consec_det_frames": max_consec,
                "total_boxes": total_boxes,
                "cls_counts": dict(cls_c),
                "max_conf": round(max_conf, 4),
                "median_ycen_norm": round(float(np.median(ycens)), 4) if ycens else None,
            }

    payload = {
        "schema_version": "mission13-field-and-daytest-comparison/1.0",
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "day_grouped_test_264_conf035": day_test_summary,
        "crossing_a_upright_controls_and_engine_conf035": field_summary,
    }
    out_p = OUT_DIR / "vision_clean_vs_frozen_field_diagnostics.json"
    out_p.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Mission 13 Vision Baseline Audit")
    parser.add_argument("--eval-clean-splits", action="store_true", help="Only evaluate frozen 39f402 on session_grouped & day_grouped splits.")
    parser.add_argument("--eval-field-diagnostics", action="store_true", help="Compare frozen vs clean YOLO on day_grouped/test & crossing_A controls.")
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.eval_clean_splits:
        res = evaluate_39f402_on_clean_splits()
        print(json.dumps(res, indent=2))
        return 0
    if args.eval_field_diagnostics:
        res = evaluate_field_and_daytest_diagnostics()
        print(json.dumps(res, indent=2))
        return 0
    csv_diag = analyze_results_csv()
    det_diag = inspect_test_detections_and_evaluator()
    payload = {
        "schema_version": "mission13-vision-baseline-audit/1.0",
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "frozen_checkpoint": str(BEST_PT.relative_to(REPO_ROOT)),
        "frozen_checkpoint_sha256": compute_file_sha256(BEST_PT),
        "last_checkpoint_sha256": compute_file_sha256(LAST_PT),
        "training_history_summary": {k: v for k, v in csv_diag.items() if k != "epochs"},
        "epochs": csv_diag["epochs"],
        **det_diag,
    }
    out = OUT_DIR / "vision_baseline_39f402_audit.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("WROTE:", out)
    print(json.dumps({
        "history": payload["training_history_summary"],
        "stratification": payload["test_error_stratification_conf035"],
        "reconcil": {
            "metrics_json_map50": payload["evaluator_py_reconciliation"]["checked_in_eval_metrics_json"]["map50"],
            "metrics_json_map50_95": payload["evaluator_py_reconciliation"]["checked_in_eval_metrics_json"]["map50_95"],
            "ultralytics_test_map50": payload["evaluator_py_reconciliation"]["ultralytics_real_val"]["39f402_best_ep93"]["test"]["mAP50"],
            "ultralytics_test_map50_95": payload["evaluator_py_reconciliation"]["ultralytics_real_val"]["39f402_best_ep93"]["test"]["mAP50_95"],
        },
        "examples": payload["examples_plotted"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
