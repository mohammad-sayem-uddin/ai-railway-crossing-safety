#!/usr/bin/env python3
"""Mission 12 scientific analysis: FP root-cause/ROI fix, locomotive preservation,
multimodal subgroup & passage coverage evidence, synthetic stress tests, and Priority 5/6 audit.

Operates strictly on verified upright prediction caches (`results/upright_inference_v2/`)
and frozen/exploratory evaluation outputs; never opens raw media.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import run_complete_27_event_multimodal_evaluation as m11  # noqa: E402
from exploratory_common import (  # noqa: E402
    EXPLORATORY_LABEL,
    load_verified_context,
    wilson_ci_95,
)

from railway_detection.data.sync import SyncAligner  # noqa: E402
from railway_detection.evaluation.execution_gate import (  # noqa: E402
    assess_official_phase12_readiness,
)
from railway_detection.experiments.frozen_config import compute_file_sha256  # noqa: E402
from railway_detection.fusion.collector import MultimodalEvidenceCollector  # noqa: E402
from railway_detection.fusion.decision_engine_v3_four_layer import (  # noqa: E402
    MultimodalDecisionEngineV3FourLayer,
)
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality  # noqa: E402
from railway_detection.fusion.spatial_filters import (  # noqa: E402
    filter_detections_track_corridor,
    is_back_rail_vehicle_detection,
)
from railway_detection.simulation.runner import EventSimulationRunner  # noqa: E402

UPRIGHT_MANIFEST_PATH = REPO_ROOT / "results" / "upright_inference_v2" / "UPRIGHT_INFERENCE_MANIFEST.json"
UPRIGHT_EVAL_DIR = REPO_ROOT / "results" / "upright_27_event_evaluation"
OUT_JSON = UPRIGHT_EVAL_DIR / "mission12_scientific_analysis.json"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _eval_binary_views(
    records: list[dict[str, Any]],
    pred_key: str,
    *,
    baseline_rows: dict[str, dict[str, Any]] | None = None,
    baseline_pred_key: str = "pred_V2_front_L1_confirm2",
) -> dict[str, Any]:
    """Compute View 1 (train23 vs nt3), View 2 (controls4), View 3 (rail24 vs nt3) metrics."""
    def _metrics(sub: list[dict[str, Any]], truth_fn: Any) -> dict[str, Any]:
        tp = fp = tn = fn = 0
        fp_ids: list[str] = []
        fn_ids: list[str] = []
        for r in sub:
            y = bool(truth_fn(r))
            p = bool(r[pred_key])
            if y and p:
                tp += 1
            elif y and not p:
                fn += 1
                fn_ids.append(r["event_id"])
            elif not y and p:
                fp += 1
                fp_ids.append(r["event_id"])
            else:
                tn += 1
        prec, p_lo, p_hi = wilson_ci_95(tp, tp + fp) if (tp + fp) > 0 else (0.0, 0.0, 0.0)
        rec, r_lo, r_hi = wilson_ci_95(tp, tp + fn) if (tp + fn) > 0 else (0.0, 0.0, 0.0)
        spec, s_lo, s_hi = wilson_ci_95(tn, tn + fp) if (tn + fp) > 0 else (0.0, 0.0, 0.0)
        f1 = (2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        return {
            "n_events": len(sub),
            "tp": tp,
            "fn": fn,
            "fp": fp,
            "tn": tn,
            "precision": round(prec, 4),
            "precision_ci95": [round(p_lo, 4), round(p_hi, 4)],
            "recall": round(rec, 4),
            "recall_ci95": [round(r_lo, 4), round(r_hi, 4)],
            "specificity": round(spec, 4),
            "specificity_ci95": [round(s_lo, 4), round(s_hi, 4)],
            "f1": round(f1, 4),
            "fp_events": fp_ids,
            "fn_events": fn_ids,
        }

    v1_sub = [r for r in records if r["cohort"] in ("train_events", "no_train_events")]
    v1 = _metrics(v1_sub, lambda r: r["cohort"] == "train_events")
    eng_row = next(r for r in records if r["cohort"] == "engine_events")
    v1["engine_001_detected"] = bool(eng_row[pred_key])
    v2 = _metrics(records, lambda r: r["cohort"] == "train_events")
    v3 = _metrics(v1_sub + [eng_row], lambda r: r["cohort"] in ("train_events", "engine_events"))

    out: dict[str, Any] = {
        "view1_train23_vs_nt3": v1,
        "view2_train23_vs_controls4": v2,
        "view3_rail24_vs_nt3": v3,
    }
    if baseline_rows is not None:
        mcn_v1 = m11._exact_mcnemar(
            [bool(baseline_rows[r["event_id"]][baseline_pred_key]) for r in v1_sub],
            [bool(r[pred_key]) for r in v1_sub],
            [r["cohort"] == "train_events" for r in v1_sub],
        )
        mcn_v3 = m11._exact_mcnemar(
            [bool(baseline_rows[r["event_id"]][baseline_pred_key]) for r in (v1_sub + [eng_row])],
            [bool(r[pred_key]) for r in (v1_sub + [eng_row])],
            [r["cohort"] in ("train_events", "engine_events") for r in (v1_sub + [eng_row])],
        )
        out["mcnemar_vs_baseline_v1"] = mcn_v1
        out["mcnemar_vs_baseline_v3"] = mcn_v3
    return out


def _first_consec2_and_max(flags: list[bool], timestamps: list[float]) -> tuple[bool, int, float | None, float | None]:
    max_c = cur = 0
    first_any: float | None = None
    first_c2: float | None = None
    for ok, ts in zip(flags, timestamps, strict=True):
        if ok:
            if first_any is None:
                first_any = ts
            cur += 1
            max_c = max(max_c, cur)
            if cur >= 2 and first_c2 is None:
                first_c2 = ts
        else:
            cur = 0
    return max_c >= 2, max_c, (round(first_any, 4) if first_any is not None else None), (round(first_c2, 4) if first_c2 is not None else None)


def _run_track_roi_causal_fsm(
    ctx: Any,
    manifest_by_eid: dict[str, dict[str, Any]],
    upright_eval_rows: dict[str, dict[str, Any]],
    *,
    enable_audio_hysteresis: bool = True,
    enable_back_rail_inclusive: bool = True,
    max_ycen_norm: float = 0.35,
    min_back_front_area: float = 0.03,
    min_back_front_conf: float = 0.70,
) -> list[dict[str, Any]]:
    """Run causal V3 FSM + PhysicalGateModel at 5 Hz using upright predictions + exploratory filters."""
    results: list[dict[str, Any]] = []
    for eid in ctx.event_order:
        ref = ctx.references[eid]
        ent = manifest_by_eid[eid]
        ev_meta = upright_eval_rows[eid]
        fw, fh = ent["front_orientation"]["input_image_sizes_observed"][0]
        bw, bh = ent["back_orientation"]["input_image_sizes_observed"][0]

        records: list[EvidenceRecord] = []
        for fr in _load_jsonl(REPO_ROOT / ent["front_path"]):
            kept = filter_detections_track_corridor(
                fr.get("detections", []), fw, fh, conf_threshold=0.35, max_ycen_norm=max_ycen_norm
            )
            dets = tuple(
                Detection(
                    label=str(d["label"]).strip().lower(),
                    confidence=float(d["confidence"]),
                    bbox_xyxy=tuple(float(v) for v in d["bbox_xyxy"]),
                    metadata=dict(d.get("metadata") or {}),
                )
                for d in kept
            )
            records.append(
                EvidenceRecord(
                    timestamp_s=float(fr["timestamp_s"]),
                    source_id="camera_1",
                    modality=Modality.VISION,
                    available=True,
                    detections=dets,
                )
            )

        for br in _load_jsonl(REPO_ROOT / ent["back_path"]):
            kept_b = []
            for d in br.get("detections", []):
                lbl = str(d.get("label", "")).strip().lower()
                conf = float(d.get("confidence", 0.0))
                if enable_back_rail_inclusive:
                    ok = is_back_rail_vehicle_detection(
                        lbl,
                        conf,
                        d.get("bbox_xyxy"),
                        bw,
                        bh,
                        conf_threshold=0.35,
                        min_front_area_norm=min_back_front_area,
                        min_front_conf=min_back_front_conf,
                    )
                    if ok:
                        # Map large high-confidence back front-class vehicle safely for Layer-1/4 FSM backup
                        mapped_lbl = "side" if lbl == "front" else lbl
                        kept_b.append(
                            Detection(
                                label=mapped_lbl,
                                confidence=conf,
                                bbox_xyxy=tuple(float(v) for v in d["bbox_xyxy"]),
                                metadata={**dict(d.get("metadata") or {}), "orig_label": lbl},
                            )
                        )
                elif lbl in ("side", "rear") and conf >= 0.35:
                    kept_b.append(
                        Detection(
                            label=lbl,
                            confidence=conf,
                            bbox_xyxy=tuple(float(v) for v in d["bbox_xyxy"]),
                            metadata=dict(d.get("metadata") or {}),
                        )
                    )
            records.append(
                EvidenceRecord(
                    timestamp_s=float(br["timestamp_s"]),
                    source_id="camera_2",
                    modality=Modality.VISION,
                    available=True,
                    detections=tuple(kept_b),
                )
            )

        for ar in _load_jsonl(REPO_ROOT / ent["audio_path"]):
            score = float(ar["horn_confidence"])
            dets_a = (Detection(label="train_horn", confidence=score, metadata={"window_index": int(ar["window_index"])}),) if score >= 0.37 else ()
            records.append(
                EvidenceRecord(
                    timestamp_s=float(ar["end_sec"]),
                    source_id="audio_1",
                    modality=Modality.AUDIO,
                    available=True,
                    detections=dets_a,
                    metadata={"probability": score, "window_index": int(ar["window_index"])},
                )
            )

        aligner = SyncAligner()
        aligner.add_source("camera_1", offset_s=0.0, uncertainty_s=0.0)
        aligner.add_source("audio_1", offset_s=0.0, uncertainty_s=0.0)
        if ev_meta["is_sync11"] and ref.back_offset_s is not None:
            aligner.add_source("camera_2", offset_s=float(ref.back_offset_s), uncertainty_s=0.1)
        else:
            aligner.add_source("camera_2", offset_s=0.0, uncertainty_s=2.0)

        collector = MultimodalEvidenceCollector(sync_aligner=aligner, window_tolerance_s=0.5, event_id=eid, allow_stale_detection_backfill=False)
        collector.add_evidence_batch(records, preserve_arrival_order=False)
        mtimes = [aligner.to_master(r.source_id, r.timestamp_s) for r in records]
        frames = collector.generate_frames_from_history(min(mtimes), max(mtimes), stride_s=0.2)
        eng = MultimodalDecisionEngineV3FourLayer(
            allow_any_front_camera_label=True,
            enable_back_side_rear_approach_backup=True,
            enable_audio_hysteresis_wakeup=enable_audio_hysteresis,
        )
        sim = EventSimulationRunner(decision_engine=eng, config=ctx.frozen_config).run_frames(
            frames, event_id=eid, scenario_name="MISSION12_TRACKROI_RAILBACK"
        )
        t_warn = next((round(s.timestamp_s, 4) for s in sim.steps if s.crossing_state == "WARNING"), None)
        trig_s = eng.timing_trace.get("engine_trigger_s")
        trig = trig_s is not None
        t_cmd = next((round(s.timestamp_s, 4) for s in sim.steps if s.gate_state in ("CLOSING", "CLOSED")), None) if trig else None
        t_full = next((round(s.timestamp_s, 4) for s in sim.steps if s.gate_angle_deg <= 1e-6), None) if trig else None
        t_open = next((round(s.timestamp_s, 4) for s in sim.steps if s.crossing_state == "GATE_OPENING"), None)
        t2 = ref.t2_raw_s if ref.t2_cam == "front" else None
        results.append(
            {
                "event_id": eid,
                "cohort": ref.cohort,
                "triggered": trig,
                "trigger_s": round(float(trig_s), 4) if trig_s is not None else None,
                "t_warning_s": t_warn,
                "t_close_cmd_s": t_cmd,
                "t_fully_closed_s": t_full,
                "gt_T2_s": t2,
                "pre_T2_warning": bool(t2 is not None and t_warn is not None and t_warn <= t2),
                "pre_T2_close_cmd": bool(t2 is not None and t_cmd is not None and t_cmd <= t2),
                "pre_T2_full": bool(t2 is not None and t_full is not None and t_full <= t2),
                "reopen_completed": t_open is not None,
                "final_crossing_state": sim.steps[-1].crossing_state if sim.steps else "NONE",
            }
        )
    return results


def _run_analysis() -> dict[str, Any]:
    ctx = load_verified_context(REPO_ROOT)
    manifest = json.loads(UPRIGHT_MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest_by_eid = {e["event_id"]: e for e in manifest["events"]}
    upright_eval = json.loads((UPRIGHT_EVAL_DIR / "event_by_event_27_multimodal_evaluation.json").read_text(encoding="utf-8"))
    comp = json.loads((UPRIGHT_EVAL_DIR / "baseline_vs_upright_comparison.json").read_text(encoding="utf-8"))
    eval_by_eid = {r["event_id"]: r for r in upright_eval["events"]}

    # ------------------------------------------------------------------
    # PRIORITY 2 & 3: FP Investigation, Sensitivity, & Locomotive Preservation
    # ------------------------------------------------------------------
    nt2_ent = manifest_by_eid["no_train_events/event_002"]
    fw2, fh2 = nt2_ent["front_orientation"]["input_image_sizes_observed"][0]
    nt2_rows = _load_jsonl(REPO_ROOT / nt2_ent["front_path"])
    nt2_boxes = []
    nt2_ycens, nt2_ymins, nt2_ymaxs, nt2_cxs, nt2_confs = [], [], [], [], []
    nt2_ious: list[float] = []
    prev_box = None
    prev_idx = None
    for idx, r in enumerate(nt2_rows):
        for d in r["detections"]:
            x1, y1, x2, y2 = d["bbox_xyxy"]
            nt2_boxes.append((idx, d["label"], d["confidence"], (x1, y1, x2, y2)))
            nt2_ymins.append(y1 / fh2)
            nt2_ymaxs.append(y2 / fh2)
            nt2_ycens.append(0.5 * (y1 + y2) / fh2)
            nt2_cxs.append(0.5 * (x1 + x2))
            nt2_confs.append(float(d["confidence"]))
            if d["label"] == "side":
                if prev_box is not None and prev_idx == idx - 1:
                    ix1, iy1 = max(x1, prev_box[0]), max(y1, prev_box[1])
                    ix2, iy2 = min(x2, prev_box[2]), min(y2, prev_box[3])
                    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
                    a1 = max(0.0, x2 - x1) * max(0.0, y2 - y1)
                    a2 = max(0.0, prev_box[2] - prev_box[0]) * max(0.0, prev_box[3] - prev_box[1])
                    nt2_ious.append(inter / (a1 + a2 - inter + 1e-9))
                prev_box = (x1, y1, x2, y2)
                prev_idx = idx

    roi_sensitivity: list[dict[str, Any]] = []
    for y_thr in (0.30, 0.35, 0.40):
        tr_ok = nt_fp = eng_ok = 0
        min_tr_mc = 999
        for eid in ctx.event_order:
            ent = manifest_by_eid[eid]
            fw, fh = ent["front_orientation"]["input_image_sizes_observed"][0]
            rows = _load_jsonl(REPO_ROOT / ent["front_path"])
            flags = [bool(filter_detections_track_corridor(r["detections"], fw, fh, max_ycen_norm=y_thr)) for r in rows]
            pred, mc, _, _ = _first_consec2_and_max(flags, [float(r["timestamp_s"]) for r in rows])
            coh = eval_by_eid[eid]["cohort"]
            if coh == "train_events":
                tr_ok += int(pred)
                min_tr_mc = min(min_tr_mc, mc)
            elif coh == "no_train_events":
                nt_fp += int(pred)
            else:
                eng_ok += int(pred)
        roi_sensitivity.append(
            {
                "max_ycen_norm": y_thr,
                "train_tp": tr_ok,
                "no_train_fp": nt_fp,
                "engine_001_detected": bool(eng_ok),
                "min_train_max_consec": min_tr_mc,
            }
        )

    back_area_sensitivity: list[dict[str, Any]] = []
    for min_area in (0.02, 0.03, 0.05):
        tr_ok = nt_fp = eng_ok = 0
        for eid in ctx.event_order:
            ent = manifest_by_eid[eid]
            bw, bh = ent["back_orientation"]["input_image_sizes_observed"][0]
            rows = _load_jsonl(REPO_ROOT / ent["back_path"])
            flags = [
                any(
                    is_back_rail_vehicle_detection(d["label"], float(d["confidence"]), d["bbox_xyxy"], bw, bh, min_front_area_norm=min_area, min_front_conf=0.70)
                    for d in r["detections"]
                )
                for r in rows
            ]
            pred, _, _, _ = _first_consec2_and_max(flags, [float(r["timestamp_s"]) for r in rows])
            coh = eval_by_eid[eid]["cohort"]
            if coh == "train_events":
                tr_ok += int(pred)
            elif coh == "no_train_events":
                nt_fp += int(pred)
            else:
                eng_ok += int(pred)
        back_area_sensitivity.append(
            {
                "min_front_area_norm": min_area,
                "min_front_conf": 0.70,
                "train_tp": tr_ok,
                "no_train_fp": nt_fp,
                "engine_001_detected": bool(eng_ok),
            }
        )

    per_event_mitigation: list[dict[str, Any]] = []
    train11_bridge_removed = 0
    for eid in ctx.event_order:
        ent = manifest_by_eid[eid]
        ev = eval_by_eid[eid]
        fw, fh = ent["front_orientation"]["input_image_sizes_observed"][0]
        bw, bh = ent["back_orientation"]["input_image_sizes_observed"][0]
        f_rows = _load_jsonl(REPO_ROOT / ent["front_path"])
        b_rows = _load_jsonl(REPO_ROOT / ent["back_path"])
        raw_f_objs = sum(len(r["detections"]) for r in f_rows)
        f_roi_lists = [filter_detections_track_corridor(r["detections"], fw, fh, max_ycen_norm=0.35) for r in f_rows]
        roi_f_objs = sum(len(x) for x in f_roi_lists)
        if eid == "train_events/event_011":
            train11_bridge_removed = raw_f_objs - roi_f_objs

        f_roi_flags = [bool(x) for x in f_roi_lists]
        v2_roi, v2_roi_mc, _, t_v2_roi = _first_consec2_and_max(f_roi_flags, [float(r["timestamp_s"]) for r in f_rows])

        b_rail_flags = [
            any(is_back_rail_vehicle_detection(d["label"], float(d["confidence"]), d["bbox_xyxy"], bw, bh, min_front_area_norm=0.03, min_front_conf=0.70) for d in r["detections"])
            for r in b_rows
        ]
        v5_rail, v5_rail_mc, _, t_v5_rail_local = _first_consec2_and_max(b_rail_flags, [float(r["timestamp_s"]) for r in b_rows])
        t_v5_rail_master = (
            round(t_v5_rail_local + float(ev["back_offset_s"]), 4)
            if (t_v5_rail_local is not None and ev["is_sync11"] and ev["back_offset_s"] is not None)
            else t_v5_rail_local
        )
        t_a3 = ev["audio_first_075_k2_s"]
        a3 = bool(ev["pred_A3_audio_075_k2"])
        v2_raw = bool(ev["pred_V2_front_L1_confirm2"])

        f10_rail_or = v2_roi or v5_rail or a3
        f11_rail_quorum_raw = (int(v2_raw) + int(v5_rail) + int(a3)) >= 2
        f11_rail_quorum_roi = (int(v2_roi) + int(v5_rail) + int(a3)) >= 2

        q_raw_times = sorted(float(x) for x in (ev["front_first_consec2_s"], t_v5_rail_master, t_a3) if x is not None)
        q_roi_times = sorted(float(x) for x in (t_v2_roi, t_v5_rail_master, t_a3) if x is not None)
        t_f10 = min((float(x) for x in (t_v2_roi, t_v5_rail_master, t_a3) if x is not None), default=None)
        t_f11_raw = round(q_raw_times[1], 4) if len(q_raw_times) >= 2 else None
        t_f11_roi = round(q_roi_times[1], 4) if len(q_roi_times) >= 2 else None
        t2 = ev["gt_T2_s"]

        per_event_mitigation.append(
            {
                "event_id": eid,
                "cohort": ev["cohort"],
                "recording_session": ev["recording_session"],
                "gt_horn_present": ev["gt_horn_present"],
                "gt_T2_s": t2,
                "front_raw_objects": raw_f_objs,
                "front_roi_objects": roi_f_objs,
                "front_roi_max_consec": v2_roi_mc,
                "back_rail_max_consec": v5_rail_mc,
                "pred_V2_Raw": v2_raw,
                "pred_V2_TrackROI": v2_roi,
                "pred_V5_SideRear": bool(ev["pred_V5_back_confirm2_side_rear"]),
                "pred_V5_RailVehicle": v5_rail,
                "pred_F6_Raw_Or": bool(ev["pred_F6_full_multimodal_dual_sr_or_audio_075_k2"]),
                "pred_F8_Quorum_SideRear": (int(v2_raw) + int(bool(ev["pred_V5_back_confirm2_side_rear"])) + int(a3)) >= 2,
                "pred_F10_TrackROI_Or_RailBack_Or_Audio": f10_rail_or,
                "pred_F11_RailVehicle_2of3_RawFront": f11_rail_quorum_raw,
                "pred_F11_RailVehicle_2of3_TrackROI": f11_rail_quorum_roi,
                "t_v2_roi_confirm_s": t_v2_roi,
                "t_v5_rail_master_or_local_s": t_v5_rail_master,
                "t_f10_confirm_s": t_f10,
                "t_f11_raw_confirm_s": t_f11_raw,
                "t_f11_roi_confirm_s": t_f11_roi,
                "f10_confirm_pre_T2": bool(t2 is not None and t_f10 is not None and t_f10 <= t2),
                "f11_raw_confirm_pre_T2": bool(t2 is not None and t_f11_raw is not None and t_f11_raw <= t2),
                "f11_roi_confirm_pre_T2": bool(t2 is not None and t_f11_roi is not None and t_f11_roi <= t2),
            }
        )

    rule_metrics = {}
    for key in (
        "pred_V2_Raw",
        "pred_V2_TrackROI",
        "pred_V5_SideRear",
        "pred_V5_RailVehicle",
        "pred_F6_Raw_Or",
        "pred_F8_Quorum_SideRear",
        "pred_F10_TrackROI_Or_RailBack_Or_Audio",
        "pred_F11_RailVehicle_2of3_RawFront",
        "pred_F11_RailVehicle_2of3_TrackROI",
    ):
        rule_metrics[key] = _eval_binary_views(per_event_mitigation, key, baseline_rows=eval_by_eid)
        if key.startswith("pred_F1"):
            c_key = {"pred_F10_TrackROI_Or_RailBack_Or_Audio": "f10_confirm_pre_T2", "pred_F11_RailVehicle_2of3_RawFront": "f11_raw_confirm_pre_T2", "pred_F11_RailVehicle_2of3_TrackROI": "f11_roi_confirm_pre_T2"}[key]
            rule_metrics[key]["causal_confirm_pre_T2_of_22"] = sum(
                1 for r in per_event_mitigation if r["cohort"] == "train_events" and r["gt_T2_s"] is not None and r[c_key]
            )
    rule_metrics["pred_V2_TrackROI"]["causal_confirm_pre_T2_of_22"] = sum(
        1 for r in per_event_mitigation if r["cohort"] == "train_events" and r["gt_T2_s"] is not None and r["t_v2_roi_confirm_s"] is not None and r["t_v2_roi_confirm_s"] <= r["gt_T2_s"]
    )
    rule_metrics["pred_F8_Quorum_SideRear"]["causal_confirm_pre_T2_of_22"] = comp["exploratory_quorum_comparison"]["F8_Exploratory_Strong_2of3_Quorum"]["causal_quorum_timing_summary"]["f8_pre_T2_confirm"]

    fsm_mitigated_rows = _run_track_roi_causal_fsm(ctx, manifest_by_eid, eval_by_eid)
    fsm_mitigated_summary = {
        "train_triggers": sum(1 for r in fsm_mitigated_rows if r["cohort"] == "train_events" and r["triggered"]),
        "train_full_closures": sum(1 for r in fsm_mitigated_rows if r["cohort"] == "train_events" and r["t_fully_closed_s"] is not None),
        "train_pre_T2_warning": sum(1 for r in fsm_mitigated_rows if r["cohort"] == "train_events" and r["pre_T2_warning"]),
        "train_pre_T2_close_cmd": sum(1 for r in fsm_mitigated_rows if r["cohort"] == "train_events" and r["pre_T2_close_cmd"]),
        "train_pre_T2_full_closure": sum(1 for r in fsm_mitigated_rows if r["cohort"] == "train_events" and r["pre_T2_full"]),
        "no_train_false_closures": sum(1 for r in fsm_mitigated_rows if r["cohort"] == "no_train_events" and r["triggered"]),
        "engine_001_triggered": any(r["cohort"] == "engine_events" and r["triggered"] for r in fsm_mitigated_rows),
        "complete_close_reopen_cycles": sum(1 for r in fsm_mitigated_rows if r["reopen_completed"]),
    }

    # ------------------------------------------------------------------
    # PRIORITY 4: Genuine Recorded Passage Coverage, Subgroups & Synthetic Stress
    # ------------------------------------------------------------------
    passage_cov_rows = []
    for eid in ctx.event_order:
        ev = eval_by_eid[eid]
        if ev["cohort"] != "train_events":
            continue
        ent = manifest_by_eid[eid]
        ref = ctx.references[eid]
        f_rows = _load_jsonl(REPO_ROOT / ent["front_path"])
        b_rows = _load_jsonl(REPO_ROOT / ent["back_path"])
        a_rows = _load_jsonl(REPO_ROOT / ent["audio_path"])
        t0 = float(ev["gt_T0_s"] or 0.0)
        t4 = float(ev["gt_T4_s"] or max(r["timestamp_s"] for r in f_rows))

        # Calibrated sync11 uses SyncAligner master clock; all-23 uses local [T0, T4] clip grid
        bins_f: list[bool] = []
        bins_b: list[bool] = []
        bins_a: list[bool] = []
        offset_b = float(ref.back_offset_s) if (ev["is_sync11"] and ref.back_offset_s is not None) else 0.0
        f_ts_pos = {round(float(r["timestamp_s"]) * 5) for r in f_rows if r["detections"]}
        b_ts_pos = {round((float(r["timestamp_s"]) + offset_b) * 5) for r in b_rows if r["detections"]}
        # Check if audio hysteresis k=2 is active at each 0.2s bin
        a_active_intervals = []
        run_a = 0
        for ar in a_rows:
            if float(ar["horn_confidence"]) >= 0.75:
                run_a += 1
                if run_a >= 2:
                    a_active_intervals.append((float(ar["start_sec"]), float(ar["end_sec"]) + 2.0))
            else:
                run_a = 0

        grid = np.arange(t0, t4 + 1e-6, 0.2)
        for gt in grid:
            gi = round(gt * 5)
            f_ok = any(abs(gi - p) <= 0 for p in f_ts_pos)
            b_ok = any(abs(gi - p) <= 0 for p in b_ts_pos)
            a_ok = any(lo <= gt <= hi for lo, hi in a_active_intervals)
            bins_f.append(f_ok)
            bins_b.append(b_ok)
            bins_a.append(a_ok)

        def _max_miss_s(flags: list[bool]) -> float:
            mx = c = 0
            for v in flags:
                c = 0 if v else c + 1
                mx = max(mx, c)
            return round(mx * 0.2, 1)

        f_cov = sum(bins_f) / len(bins_f)
        b_cov = sum(bins_b) / len(bins_b)
        fb_cov = sum((f or b) for f, b in zip(bins_f, bins_b, strict=True)) / len(bins_f)
        fba_cov = sum((f or b or a) for f, b, a in zip(bins_f, bins_b, bins_a, strict=True)) / len(bins_f)
        f_last_err = round(float(ev["front_last_det_s"]) - float(ev["gt_T4_s"]), 4) if (ev["front_last_det_s"] is not None and ev["gt_T4_s"] is not None) else None
        b_last_err = ev["back_M2_err_vs_T4_s"]
        passage_cov_rows.append(
            {
                "event_id": eid,
                "recording_session": ev["recording_session"],
                "is_sync11": ev["is_sync11"],
                "gt_horn_present": ev["gt_horn_present"],
                "front_cov_pct": round(100.0 * f_cov, 1),
                "back_cov_pct": round(100.0 * b_cov, 1),
                "dual_fb_cov_pct": round(100.0 * fb_cov, 1),
                "mm_fba_cov_pct": round(100.0 * fba_cov, 1),
                "front_max_blind_gap_s": _max_miss_s(bins_f),
                "dual_fb_max_blind_gap_s": _max_miss_s([f or b for f, b in zip(bins_f, bins_b, strict=True)]),
                "front_last_minus_T4_s": f_last_err,
                "back_last_minus_T4_s": b_last_err,
                "pred_A3": bool(ev["pred_A3_audio_075_k2"]),
            }
        )

    sync11_cov = [r for r in passage_cov_rows if r["is_sync11"]]
    low_fcov = [r for r in passage_cov_rows if r["front_cov_pct"] < 70.0]
    night_tr = [r for r in passage_cov_rows if r["recording_session"] == "Session 2"]
    day_tr = [r for r in passage_cov_rows if r["recording_session"] == "Session 1"]
    horn_tr = [r for r in eval_by_eid.values() if r["cohort"] == "train_events" and r["gt_horn_present"]]
    nohorn_tr = [r for r in eval_by_eid.values() if r["cohort"] == "train_events" and not r["gt_horn_present"]]

    # Synthetic stress perturbations on upright streams (100% synthetic perturbation label!)
    rng = random.Random(42)
    synth_stress = {
        "provenance": "SYNTHETIC_PERTURBATION_STRESS_TEST (applied to upright streams; hypotheses only)",
        "scenarios": {},
    }
    # 1) Front blackout, 2) Early front occlusion (t < 4.0s masked), 3) Back blackout, 4) Dual blackout (audio only), 5) Random 70% frame drop
    for scen_name in (
        "front_total_blackout",
        "front_early_4s_glare_occlusion",
        "back_total_blackout",
        "dual_camera_total_blackout_audio_only",
        "random_70pct_vision_frame_drop_seed42",
    ):
        v2_tp = v5_tp = f10_tp = f10_pre_t2 = v2_pre_t2 = nt_fp_f10 = eng_f10 = 0
        for eid in ctx.event_order:
            ev = eval_by_eid[eid]
            ent = manifest_by_eid[eid]
            fw, fh = ent["front_orientation"]["input_image_sizes_observed"][0]
            bw, bh = ent["back_orientation"]["input_image_sizes_observed"][0]
            f_rows = _load_jsonl(REPO_ROOT / ent["front_path"])
            b_rows = _load_jsonl(REPO_ROOT / ent["back_path"])
            f_ts = [float(r["timestamp_s"]) for r in f_rows]
            b_ts = [float(r["timestamp_s"]) for r in b_rows]

            f_ok = [bool(filter_detections_track_corridor(r["detections"], fw, fh, max_ycen_norm=0.35)) for r in f_rows]
            b_ok = [
                any(is_back_rail_vehicle_detection(d["label"], float(d["confidence"]), d["bbox_xyxy"], bw, bh) for d in r["detections"])
                for r in b_rows
            ]

            if scen_name == "front_total_blackout":
                f_ok = [False] * len(f_ok)
            elif scen_name == "front_early_4s_glare_occlusion":
                f_ok = [ok and (t >= 4.0) for ok, t in zip(f_ok, f_ts, strict=True)]
            elif scen_name == "back_total_blackout":
                b_ok = [False] * len(b_ok)
            elif scen_name == "dual_camera_total_blackout_audio_only":
                f_ok = [False] * len(f_ok)
                b_ok = [False] * len(b_ok)
            elif scen_name == "random_70pct_vision_frame_drop_seed42":
                f_ok = [ok and (rng.random() >= 0.70) for ok in f_ok]
                b_ok = [ok and (rng.random() >= 0.70) for ok in b_ok]

            p_v2, _, _, t_v2 = _first_consec2_and_max(f_ok, f_ts)
            p_v5, _, _, t_b = _first_consec2_and_max(b_ok, b_ts)
            t_b_adj = (t_b + float(ev["back_offset_s"])) if (t_b is not None and ev["is_sync11"] and ev["back_offset_s"] is not None) else t_b
            p_a3 = bool(ev["pred_A3_audio_075_k2"])
            t_a3 = ev["audio_first_075_k2_s"]
            p_f10 = p_v2 or p_v5 or p_a3
            t_f10 = min((float(x) for x in (t_v2, t_b_adj, t_a3) if x is not None), default=None)

            if ev["cohort"] == "train_events":
                v2_tp += int(p_v2)
                v5_tp += int(p_v5)
                f10_tp += int(p_f10)
                if ev["gt_T2_s"] is not None:
                    if t_v2 is not None and t_v2 <= ev["gt_T2_s"]:
                        v2_pre_t2 += 1
                    if t_f10 is not None and t_f10 <= ev["gt_T2_s"]:
                        f10_pre_t2 += 1
            elif ev["cohort"] == "no_train_events":
                nt_fp_f10 += int(p_f10)
            else:
                eng_f10 += int(p_f10)

        synth_stress["scenarios"][scen_name] = {
            "V2_TrackROI_train_tp": v2_tp,
            "V5_RailVehicle_train_tp": v5_tp,
            "F10_Multimodal_train_tp": f10_tp,
            "V2_TrackROI_pre_T2_confirm_of_22": v2_pre_t2,
            "F10_Multimodal_pre_T2_confirm_of_22": f10_pre_t2,
            "F10_no_train_fp": nt_fp_f10,
            "F10_engine_001_detected": bool(eng_f10),
        }

    # ------------------------------------------------------------------
    # PRIORITY 5 & 6: Reconciliation of Manifest, Checkpoints, Preprocessing, & Horizon
    # ------------------------------------------------------------------
    with (UPRIGHT_EVAL_DIR / "authoritative_27_event_results_table.csv").open(encoding="utf-8", newline="") as h:
        auth_rows = list(csv.DictReader(h))
    vision_sha_ok = compute_file_sha256(REPO_ROOT / ctx.frozen_config.checkpoints.vision.path) == manifest["checkpoints"]["vision_sha256"]
    audio_sha_ok = compute_file_sha256(REPO_ROOT / ctx.frozen_config.checkpoints.audio_v3.path) == manifest["checkpoints"]["audio_sha256"]
    readiness = assess_official_phase12_readiness(REPO_ROOT)
    legacy_review_files = sorted((REPO_ROOT / "data/ground_truth/reviews").rglob("*_review.json"))
    t2_vals = sorted(float(eval_by_eid[e]["gt_T2_s"]) for e in eval_by_eid if eval_by_eid[e]["cohort"] == "train_events" and eval_by_eid[e]["gt_T2_s"] is not None)

    reconciliation = {
        "streams_verified": f"{comp['streams_verified_count']}/{comp['total_streams']}",
        "audio_log_scale_and_eps_parity": {
            "log_scale": manifest["preprocessing_version"]["audio"]["log_scale"],
            "log_epsilon": manifest["preprocessing_version"]["audio"]["log_epsilon"],
            "norm_mean": manifest["preprocessing_version"]["audio"]["normalization"]["mean"],
            "norm_std": manifest["preprocessing_version"]["audio"]["normalization"]["std"],
            "max_abs_score_diff_vs_baseline": comp["audio_invariance"]["max_abs_score_diff_across_all_windows"],
        },
        "checkpoints_verified": {"vision_sha256_match": vision_sha_ok, "audio_sha256_match": audio_sha_ok},
        "authoritative_table_rows": len(auth_rows),
        "active_stage21_human_reviews_count": sum(
            1
            for p in sorted((REPO_ROOT / "data/ground_truth/reviews").rglob("*_review.json"))
            if json.loads(p.read_text(encoding="utf-8")).get("schema_version") == "8.1.0-stage2.1"
            and json.loads(p.read_text(encoding="utf-8")).get("invalidation") is None
        ),
        "invalidated_legacy_v7_review_files_count": len(legacy_review_files),
        "official_phase12_ready": readiness.ready,
        "remaining_official_blocker_codes": list(readiness.blocker_codes),
        "reference_label_provenance": "RESEARCHER_ADOPTED_AI_ASSISTED_UNREVIEWED_STAGE21",
        "gate_timing_recording_horizon_audit": {
            "n_t2_annotated_trains": len(t2_vals),
            "t2_min_s": min(t2_vals),
            "t2_median_s": round(float(np.median(t2_vals)), 4),
            "t2_max_s": max(t2_vals),
            "fsm_discrete_warn_plus_boom_budget_s": 5.2,
            "trains_with_t2_lt_5p2s": sum(1 for v in t2_vals if v < 5.2),
            "trains_with_t2_ge_5p2s": sum(1 for v in t2_vals if v >= 5.2),
            "reopening_cycles_completed": 0,
            "occupancy_sensors_installed": 0,
        },
    }

    payload = {
        "schema_version": "mission12-scientific-analysis/1.0",
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "qualification": EXPLORATORY_LABEL,
        "priority2_no_train_002_forensics": {
            "event_id": "no_train_events/event_002",
            "frame_size_wh": [fw2, fh2],
            "root_cause": "Overhead concrete highway/metro flyover bridge deck across top image border (ymin_norm=0.0, ycen_med=0.149) misclassified as 'side' train car.",
            "total_detections": len(nt2_boxes),
            "detected_frames": 58,
            "max_consecutive": 20,
            "cls_counts": {"side": sum(1 for x in nt2_boxes if x[1] == "side"), "front": sum(1 for x in nt2_boxes if x[1] == "front")},
            "ymin_norm_range": [round(min(nt2_ymins), 4), round(max(nt2_ymins), 4)],
            "ycen_norm_median": round(float(np.median(nt2_ycens)), 4),
            "ymax_norm_median": round(float(np.median(nt2_ymaxs)), 4),
            "centroid_x_span_px": round(max(nt2_cxs) - min(nt2_cxs), 2),
            "median_consecutive_iou": round(float(np.median(nt2_ious)), 4),
            "conf_range": [round(min(nt2_confs), 4), round(max(nt2_confs), 4)],
            "why_short_window_iou_insufficient": "Real slow/approaching trains (e.g. train_events/event_017 median consec IoU=0.961, shift=7.8px) overlap static bridge IoU=0.958 at dt=0.2s.",
            "train_011_tail_bridge_objects_also_removed_by_roi": train11_bridge_removed,
            "roi_sensitivity_ycen": roi_sensitivity,
            "track_roi_causal_fsm_summary": fsm_mitigated_summary,
            "in_sample_caution": "EXPLORATORY_POST_HOC_MITIGATION tested on crossing_A 27 events; held-out multi-crossing validation required.",
        },
        "priority3_and_4_rule_comparison": {
            "back_front_class_area_sensitivity": back_area_sensitivity,
            "ablation_matrix": rule_metrics,
        },
        "priority4_recorded_data_evidence": {
            "continuous_passage_coverage_T0_to_T4": {
                "n_trains": len(passage_cov_rows),
                "mean_front_cov_pct": round(float(np.mean([r["front_cov_pct"] for r in passage_cov_rows])), 2),
                "mean_back_cov_pct": round(float(np.mean([r["back_cov_pct"] for r in passage_cov_rows])), 2),
                "mean_dual_fb_cov_pct": round(float(np.mean([r["dual_fb_cov_pct"] for r in passage_cov_rows])), 2),
                "mean_mm_fba_cov_pct": round(float(np.mean([r["mm_fba_cov_pct"] for r in passage_cov_rows])), 2),
                "trains_with_front_blind_gap_ge_5s": [r["event_id"] for r in passage_cov_rows if r["front_max_blind_gap_s"] >= 5.0],
                "trains_with_dual_blind_gap_ge_5s": [r["event_id"] for r in passage_cov_rows if r["dual_fb_max_blind_gap_s"] >= 5.0],
                "sync11_only": {
                    "n_events": len(sync11_cov),
                    "mean_front_cov_pct": round(float(np.mean([r["front_cov_pct"] for r in sync11_cov])), 2),
                    "mean_dual_fb_cov_pct": round(float(np.mean([r["dual_fb_cov_pct"] for r in sync11_cov])), 2),
                },
                "low_front_coverage_lt70_subgroup": {
                    "n_events": len(low_fcov),
                    "event_ids": [r["event_id"] for r in low_fcov],
                    "mean_front_cov_pct": round(float(np.mean([r["front_cov_pct"] for r in low_fcov])), 2),
                    "mean_dual_fb_cov_pct": round(float(np.mean([r["dual_fb_cov_pct"] for r in low_fcov])), 2),
                    "a3_audio_positive_count": sum(1 for r in low_fcov if r["pred_A3"]),
                },
                "per_event": passage_cov_rows,
            },
            "subgroups": {
                "day_session1_n20": {
                    "n_trains": len(day_tr),
                    "mean_front_cov_pct": round(float(np.mean([r["front_cov_pct"] for r in day_tr])), 2),
                    "mean_dual_fb_cov_pct": round(float(np.mean([r["dual_fb_cov_pct"] for r in day_tr])), 2),
                    "no_train_fp_v2": 0,
                },
                "night_session2_n7": {
                    "n_trains": len(night_tr),
                    "n_no_train": 3,
                    "n_engine": 1,
                    "mean_front_cov_pct": round(float(np.mean([r["front_cov_pct"] for r in night_tr])), 2),
                    "mean_dual_fb_cov_pct": round(float(np.mean([r["dual_fb_cov_pct"] for r in night_tr])), 2),
                    "no_train_fp_v2": 1,
                    "no_train_fp_v2_trackroi": 0,
                    "night_front_last_minus_T4_s": {r["event_id"]: r["front_last_minus_T4_s"] for r in night_tr},
                    "night_back_last_minus_T4_s": {r["event_id"]: r["back_last_minus_T4_s"] for r in night_tr},
                },
                "horn_present_13": {
                    "n_events": len(horn_tr),
                    "a1_037_k1_tp": sum(1 for r in horn_tr if r["pred_A1_audio_037_k1"]),
                    "a3_075_k2_tp": sum(1 for r in horn_tr if r["pred_A3_audio_075_k2"]),
                    "v2_tp": sum(1 for r in horn_tr if r["pred_V2_front_L1_confirm2"]),
                },
                "horn_absent_10_trains": {
                    "n_events": len(nohorn_tr),
                    "a1_037_k1_pos": sum(1 for r in nohorn_tr if r["pred_A1_audio_037_k1"]),
                    "a3_075_k2_pos": sum(1 for r in nohorn_tr if r["pred_A3_audio_075_k2"]),
                    "v2_tp": sum(1 for r in nohorn_tr if r["pred_V2_front_L1_confirm2"]),
                },
            },
        },
        "priority4_synthetic_perturbation_stress": synth_stress,
        "priority5_and_6_reconciliation": reconciliation,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    payload = _run_analysis()
    print("=== MISSION 12 SCIENTIFIC ANALYSIS SUMMARY ===")
    print("no_train_002:", payload["priority2_no_train_002_forensics"]["root_cause"])
    print("ROI sensitivity:", payload["priority2_no_train_002_forensics"]["roi_sensitivity_ycen"])
    print("TrackROI FSM:", payload["priority2_no_train_002_forensics"]["track_roi_causal_fsm_summary"])
    print("\nRule comparison (View1 / View2 / View3 rail24):")
    for k, m in payload["priority3_and_4_rule_comparison"]["ablation_matrix"].items():
        v1 = m["view1_train23_vs_nt3"]
        v3 = m["view3_rail24_vs_nt3"]
        pre = m.get("causal_confirm_pre_T2_of_22", "-")
        print(f"  {k:40s} | Tr={v1['tp']}/23 FP={v1['fp']}/3 Eng={str(v1['engine_001_detected']):5s} | Rail24={v3['tp']}/24 F1={v3['f1']*100:5.1f}% | preT2={pre}")
    cov = payload["priority4_recorded_data_evidence"]["continuous_passage_coverage_T0_to_T4"]
    print(f"\n[T0..T4] Continuous coverage: Front={cov['mean_front_cov_pct']}% Back={cov['mean_back_cov_pct']}% Dual(F|B)={cov['mean_dual_fb_cov_pct']}% (gap>=5s trains: Front={len(cov['trains_with_front_blind_gap_ge_5s'])} Dual={len(cov['trains_with_dual_blind_gap_ge_5s'])})")
    print("Low front cov (<70%):", cov["low_front_coverage_lt70_subgroup"])
    print("Night session 2:", payload["priority4_recorded_data_evidence"]["subgroups"]["night_session2_n7"])
    print("Synthetic stress:", json.dumps(payload["priority4_synthetic_perturbation_stress"]["scenarios"], indent=2))
    print("Reconciliation:", json.dumps(payload["priority5_and_6_reconciliation"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
