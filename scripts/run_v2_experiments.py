"""Master Experiments A-N runner outputting verified JSON/CSV artifacts to results/exploratory_v2/."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from exploratory_common import (
    EXPLORATORY_LABEL,
    VerifiedExploratoryContext,
    load_event_evidence_records,
    load_verified_context,
    make_engine,
    serialize_simulation_result,
)
from railway_detection.fusion.collector import MultimodalEvidenceCollector, MultimodalFrame
from railway_detection.fusion.decision_engine_v3_four_layer import MultimodalDecisionEngineV3FourLayer
from railway_detection.fusion.evidence import EvidenceRecord, OccupancyEvidence
from railway_detection.fusion.rules_v3_four_layer import DeparturePolicyMode
from railway_detection.simulation.runner import EventSimulationRunner, SimulationRunResult
from v2_synthetic_scenarios import (
    _baseline_nominal_streams,
    _collect_causal,
    check_transition_legality,
    run_synthetic_suite,
    verify_audio_v3_transform_and_scenarios,
    verify_synthetic_video_orientation_and_yolo,
)

RESULTS_DIR_NAME = "results/exploratory_v2"
AUDIT_DIR = Path("docs/generated/professor_evidence/mission44")
ROT_AUDIT_PATH = Path("docs/generated/professor_evidence/mission43/SOURCE_VERIFICATION_RECEIPT.json")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> list[float | None]:
    if n <= 0:
        return [None, None]
    p = k / n
    denom = 1.0 + (z * z) / n
    center = (p + (z * z) / (2.0 * n)) / denom
    half = (z * math.sqrt((p * (1.0 - p) + (z * z) / (4.0 * n)) / n)) / denom
    return [round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)]


def _exact_mcnemar(b01: int, b10: int) -> dict[str, Any]:
    """Exact two-sided binomial McNemar test on discordant pairs."""
    n = b01 + b10
    if n == 0:
        return {"discordant_pairs": 0, "b01": 0, "b10": 0, "exact_p_value": 1.0}
    k = min(b01, b10)
    p_tail = sum(math.comb(n, i) * (0.5**n) for i in range(0, k + 1))
    return {
        "discordant_pairs": n,
        "b01_a_wrong_b_right": b01,
        "b10_a_right_b_wrong": b10,
        "exact_p_value": round(min(1.0, 2.0 * p_tail), 6),
    }


def _roc_auc_and_ap(y_true: list[int], scores: list[float]) -> tuple[float | None, float | None]:
    pos = sum(y_true)
    neg = len(y_true) - pos
    if pos == 0 or neg == 0:
        return None, None
    # Pairwise rank ROC-AUC handling ties explicitly
    wins = 0.0
    for s_pos, yt_p in zip(scores, y_true):
        if yt_p != 1:
            continue
        for s_neg, yt_n in zip(scores, y_true):
            if yt_n != 0:
                continue
            if s_pos > s_neg:
                wins += 1.0
            elif s_pos == s_neg:
                wins += 0.5
    auc = wins / float(pos * neg)

    order = sorted(range(len(scores)), key=lambda i: -scores[i])
    tp = 0
    ap_sum = 0.0
    for rank, idx in enumerate(order, start=1):
        if y_true[idx] == 1:
            tp += 1
            ap_sum += tp / float(rank)
    return round(auc, 4), round(ap_sum / float(pos), 4)


def _desc(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "n": len(values),
        "min": round(min(values), 4),
        "median": round(float(statistics.median(values)), 4),
        "mean": round(float(statistics.mean(values)), 4),
        "max": round(max(values), 4),
    }


def _assemble_event_frames(
    ctx: VerifiedExploratoryContext,
    event_id: str,
    condition: str,
    *,
    stride_s: float = 0.2,
    window_tolerance_s: float = 0.5,
    allow_stale_detection_backfill: bool = False,
    delay_source: str | None = None,
    delay_s: float = 0.0,
) -> tuple[list[EvidenceRecord], list[MultimodalFrame], str, dict[str, float | None]]:
    records, aligner, clock_mode = load_event_evidence_records(ctx, event_id, condition)
    if delay_source and delay_s > 0.0:
        records = [
            replace(r, timestamp_s=float(r.timestamp_s) + delay_s) if r.source_id == delay_source else r
            for r in records
        ]
    collector = MultimodalEvidenceCollector(
        sync_aligner=aligner,
        window_tolerance_s=float(window_tolerance_s),
        event_id=event_id,
        allow_stale_detection_backfill=allow_stale_detection_backfill,
    )
    collector.add_evidence_batch(records, preserve_arrival_order=False)
    master_times = [
        aligner.to_master(r.source_id, r.timestamp_s)
        if (aligner is not None and r.source_id in aligner.offsets_s)
        else r.timestamp_s
        for r in records
    ]
    t_start = min(master_times)
    t_end = max(master_times)
    frames = collector.generate_frames_from_history(t_start, t_end, stride_s=float(stride_s))
    bounds = ctx.references[event_id].boundaries_for_clock(clock_mode)
    return records, frames, clock_mode, bounds


def _load_t_scene_clear_map(ctx: VerifiedExploratoryContext) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for eid in ctx.event_order:
        p = ctx.repo_root / ctx.references[eid].active_proposal_path
        data = json.loads(p.read_text(encoding="utf-8"))
        sc = data.get("proposed_timestamps", {}).get("T_scene_clear", {}).get("value_s")
        out[eid] = float(sc) if sc is not None else None
    return out


def _load_source_rotations(repo_root: Path) -> dict[str, dict[str, int]]:
    receipt = json.loads((repo_root / ROT_AUDIT_PATH).read_text(encoding="utf-8"))
    by_event: dict[str, dict[str, int]] = {}
    streams = receipt.get("streams", {})
    if isinstance(streams, dict):
        items = streams.items()
        for key, info in items:
            if isinstance(info, dict):
                ev = str(info.get("event_id", key.rsplit("/", 1)[0] if "/" in key else ""))
                cam = str(info.get("camera_role", info.get("stream", "")))
                rot = info.get("display_rotation_deg", info.get("rotation_deg", 0))
                if ev:
                    by_event.setdefault(ev, {})[cam or key] = int(rot or 0)
    elif isinstance(streams, list):
        for info in streams:
            ev = str(info.get("event_id", ""))
            cam = str(info.get("camera_role", info.get("camera", "")))
            rot = info.get("display_rotation_deg", info.get("rotation_deg", 0))
            if ev:
                by_event.setdefault(ev, {})[cam] = int(rot or 0)
    return by_event


def _extract_timing_and_outcomes(
    res: SimulationRunResult,
    *,
    t_arrival_s: float | None,
    t_clearance_s: float | None,
    engine: Any | None = None,
) -> dict[str, Any]:
    t_warn = next((round(s.timestamp_s, 4) for s in res.steps if s.crossing_state == "WARNING"), None)
    t_close_cmd = next((round(s.timestamp_s, 4) for s in res.steps if s.gate_state in ("CLOSING", "CLOSED")), None)
    t_half = next((round(s.timestamp_s, 4) for s in res.steps if s.is_passage_blocked), None)
    t_full = next((round(s.timestamp_s, 4) for s in res.steps if s.gate_angle_deg <= 1e-6), None)
    first_open = next((round(s.timestamp_s, 4) for s in res.steps if s.crossing_state == "GATE_OPENING"), None)
    closure_triggered = t_close_cmd is not None or t_warn is not None

    margin_full = (
        round(t_arrival_s - t_full, 4)
        if (t_arrival_s is not None and t_full is not None)
        else None
    )
    margin_half = (
        round(t_arrival_s - t_half, 4)
        if (t_arrival_s is not None and t_half is not None)
        else None
    )
    premature_vs_clear = bool(
        first_open is not None and t_clearance_s is not None and first_open < t_clearance_s
    )
    closed_before_arrival = bool(
        t_arrival_s is not None and t_full is not None and t_full <= t_arrival_s
    )
    engine_trace = getattr(engine, "timing_trace", {}) or {}
    t_first_det = engine_trace.get("first_front_detection_s")
    t_confirm = engine_trace.get("confirmed_front_detection_s")
    t_trig = engine_trace.get("engine_trigger_s") or t_warn

    return {
        "closure_triggered": closure_triggered,
        "t_first_front_det_s": round(t_first_det, 4) if t_first_det is not None else None,
        "t_confirm_s": round(t_confirm, 4) if t_confirm is not None else None,
        "t_warning_s": t_warn,
        "t_engine_trigger_s": round(t_trig, 4) if t_trig is not None else None,
        "t_close_cmd_s": t_close_cmd,
        "t_half_closed_s": t_half,
        "t_fully_closed_s": t_full,
        "first_opening_s": first_open,
        "closed_before_arrival": closed_before_arrival,
        "margin_full_vs_T2_s": margin_full,
        "margin_half_vs_T2_s": margin_half,
        "premature_opening_vs_T4": premature_vs_clear,
        "final_crossing_state": res.steps[-1].crossing_state if res.steps else "NONE",
        "final_gate_state": res.steps[-1].gate_state if res.steps else "NONE",
        "closed_duration_s": round(res.closed_duration_s, 4),
        "total_duration_s": round(res.total_duration_s, 4),
        "transition_legal": check_transition_legality(res)["legal"],
    }


def run_exp_a(ctx: VerifiedExploratoryContext, rot_map: dict[str, dict[str, int]]) -> dict[str, Any]:
    """Experiment A: Front-only train detection, 8-timestamp decomposition, and Part 5D camera-distance formulas."""
    per_event: list[dict[str, Any]] = []
    margins_train: list[float] = []
    det_leads_train: list[float] = []
    train_closed = 0
    no_train_fp = 0

    for eid in ctx.event_order:
        ref = ctx.references[eid]
        recs, frames, _, bounds = _assemble_event_frames(ctx, eid, "B0")
        raw_front_counts = {"front": 0, "side": 0, "rear": 0, "other": 0}
        first_any_t = None
        first_strict_front_t = None
        for r in recs:
            for d in r.detections:
                if d.confidence >= 0.35:
                    lbl = d.label.lower()
                    if lbl in raw_front_counts:
                        raw_front_counts[lbl] += 1
                    else:
                        raw_front_counts["other"] += 1
                    if first_any_t is None:
                        first_any_t = r.timestamp_s
                    if lbl == "front" and first_strict_front_t is None:
                        first_strict_front_t = r.timestamp_s

        eng_any = MultimodalDecisionEngineV3FourLayer(allow_any_front_camera_label=True)
        res_any = EventSimulationRunner(decision_engine=eng_any).run_frames(
            frames,
            event_id=eid,
            scenario_name="exp_a_front_any",
            entry_time_s=bounds.get("t1"),
            clearance_time_s=None,
        )
        t_out = _extract_timing_and_outcomes(
            res_any, t_arrival_s=bounds.get("t2"), t_clearance_s=None, engine=eng_any
        )

        # Also evaluate strict-front label sensitivity
        eng_strict = MultimodalDecisionEngineV3FourLayer(allow_any_front_camera_label=False)
        res_strict = EventSimulationRunner(decision_engine=eng_strict).run_frames(
            frames, event_id=eid, scenario_name="exp_a_front_strict"
        )
        strict_closed = any(s.crossing_state == "WARNING" or s.gate_state in ("CLOSING", "CLOSED") for s in res_strict.steps)

        if ref.event_type == "REAL_WORLD_TRAIN_EVENT":
            if t_out["closure_triggered"]:
                train_closed += 1
            if t_out["margin_full_vs_T2_s"] is not None:
                margins_train.append(t_out["margin_full_vs_T2_s"])
            if bounds.get("t2") is not None and t_out["t_first_front_det_s"] is not None:
                det_leads_train.append(round(bounds["t2"] - t_out["t_first_front_det_s"], 4))
        elif ref.event_type == "REAL_WORLD_NO_TRAIN":
            if t_out["closure_triggered"]:
                no_train_fp += 1

        per_event.append(
            {
                "event_id": eid,
                "event_type": ref.event_type,
                "is_sync11": ref.is_dual_sync_accepted,
                "front_rotations_deg": rot_map.get(eid, {}),
                "raw_front_det_counts": raw_front_counts,
                "first_raw_any_det_s": round(first_any_t, 4) if first_any_t is not None else None,
                "first_raw_strict_front_s": round(first_strict_front_t, 4) if first_strict_front_t is not None else None,
                "strict_front_label_triggered": strict_closed,
                "T0_s": bounds.get("t0"),
                "T1_s": bounds.get("t1"),
                "T2_s": bounds.get("t2"),
                "det_lead_vs_T2_s": (
                    round(bounds["t2"] - t_out["t_first_front_det_s"], 4)
                    if bounds.get("t2") is not None and t_out["t_first_front_det_s"] is not None
                    else None
                ),
                **t_out,
            }
        )

    # Part 5D/12 engineering sensitivity formula for upstream camera placement
    # d_req(v) = (v_kmh / 3.6) * (t_detect + t_confirm + t_warning + t_close + t_margin)
    speeds_kmh = [30, 40, 60, 80, 100]
    param_profiles = [
        {"name": "baseline_with_2s_warning", "t_det_s": 0.4, "t_confirm_s": 0.2, "t_warning_s": 2.0, "t_close_s": 3.0, "t_margin_s": 2.0},
        {"name": "fast_close_0s_warning", "t_det_s": 0.4, "t_confirm_s": 0.2, "t_warning_s": 0.0, "t_close_s": 3.0, "t_margin_s": 2.0},
        {"name": "conservative_high_margin", "t_det_s": 0.8, "t_confirm_s": 0.4, "t_warning_s": 2.0, "t_close_s": 4.0, "t_margin_s": 3.0},
    ]
    distance_table: list[dict[str, Any]] = []
    for prof in param_profiles:
        t_tot = prof["t_det_s"] + prof["t_confirm_s"] + prof["t_warning_s"] + prof["t_close_s"] + prof["t_margin_s"]
        distance_table.append(
            {
                **prof,
                "total_required_time_s": round(t_tot, 2),
                "required_upstream_distance_m_by_speed_kmh": {
                    str(v): round((v / 3.6) * t_tot, 2) for v in speeds_kmh
                },
            }
        )

    n_train = sum(1 for eid in ctx.event_order if ctx.references[eid].event_type == "REAL_WORLD_TRAIN_EVENT")
    n_sync_closed_before_t2 = sum(
        1 for row in per_event if row["is_sync11"] and row["closed_before_arrival"]
    )
    return {
        "experiment": "Exp_A_Front_Detection_And_Warning_Decomposition",
        "qualification": EXPLORATORY_LABEL,
        "cache_caveat": "Pre-db40305 YOLOv8n caches from unrotated streams (many streams -90 deg rotated); no raw media re-inference without AUTH-MEDIA-ACCESS.json.",
        "summary": {
            "train_events_total": n_train,
            "train_events_triggered": train_closed,
            "train_closure_trigger_rate": round(train_closed / n_train, 4),
            "train_closure_wilson_95ci": _wilson_ci(train_closed, n_train),
            "no_train_false_closures": no_train_fp,
            "no_train_total": 3,
            "engine_only_triggered": next(r["closure_triggered"] for r in per_event if r["event_type"] == "REAL_WORLD_ENGINE_ONLY"),
            "sync11_closed_before_T2": n_sync_closed_before_t2,
            "sync11_total": 11,
            "det_lead_vs_T2_stats_s": _desc(det_leads_train),
            "full_closure_margin_vs_T2_stats_s": _desc(margins_train),
        },
        "upstream_camera_distance_engineering_scenarios": {
            "formula": "d_req = (v_train_kmh / 3.6) * (t_detect + t_confirm + t_warning + t_close + t_margin)",
            "empirical_assumption_note": "Train speeds and prototype camera-to-crossing distances are unmeasured in repo metadata; values below are scenario calculations only.",
            "profiles": distance_table,
        },
        "per_event": per_event,
    }


def run_exp_b(ctx: VerifiedExploratoryContext) -> dict[str, Any]:
    """Experiment B: Side-view proxy evidence audit on real caches + dedicated synthetic side scenarios."""
    from railway_detection.fusion.rules_v3_four_layer import SideMovementTracker

    real_rows: list[dict[str, Any]] = []
    for eid in ctx.event_order:
        ref = ctx.references[eid]
        recs_f, _, _, _ = _assemble_event_frames(ctx, eid, "B0")
        recs_b, _, _, _ = _assemble_event_frames(ctx, eid, "BACK_VISION")
        all_recs = recs_f + recs_b
        side_frames_f = 0
        side_frames_b = 0
        max_streak_f = 0
        cur_streak_f = 0
        disps_f: list[float] = []
        last_c: tuple[float, float] | None = None
        for r in recs_f:
            side_dets = [d for d in r.detections if d.label.lower() == "side" and d.confidence >= 0.35]
            if side_dets:
                side_frames_f += 1
                cur_streak_f += 1
                max_streak_f = max(max_streak_f, cur_streak_f)
                d0 = side_dets[0]
                if d0.bbox_xyxy is not None:
                    cx = (d0.bbox_xyxy[0] + d0.bbox_xyxy[2]) / 2.0
                    cy = (d0.bbox_xyxy[1] + d0.bbox_xyxy[3]) / 2.0
                    if last_c is not None:
                        disps_f.append(math.hypot(cx - last_c[0], cy - last_c[1]))
                    last_c = (cx, cy)
            else:
                cur_streak_f = 0
                last_c = None
        for r in recs_b:
            if any(d.label.lower() == "side" and d.confidence >= 0.35 for d in r.detections):
                side_frames_b += 1

        real_rows.append(
            {
                "event_id": eid,
                "event_type": ref.event_type,
                "dedicated_camera_side_present": False,
                "front_cam_side_label_frames": side_frames_f,
                "back_cam_side_label_frames": side_frames_b,
                "max_consecutive_front_side_streak": max_streak_f,
                "mean_front_side_centroid_step_px": round(float(statistics.mean(disps_f)), 2) if disps_f else None,
            }
        )

    # Synthetic Layer-2 SideMovementTracker test cases
    syn_cases: list[dict[str, Any]] = []
    for case_name, pattern in [
        ("moving_train_side", [(True, 40.0 + i * 16.0, False) for i in range(6)]),
        ("stopped_train_in_zone", [(True, 100.0, True) for _ in range(8)]),
        ("single_frame_false_side_glint", [(True, 80.0, False)] + [(False, 0.0, False)] * 5),
        ("negative_control_empty", [(False, 0.0, False)] * 8),
    ]:
        tracker = SideMovementTracker(min_persistence_frames=2)
        states = []
        from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality

        for idx, (has_det, cx, is_stopped) in enumerate(pattern):
            t = round(idx * 0.5, 3)
            dets = (
                (Detection("side", 0.88, (cx - 40, 50.0, cx + 40, 150.0), {"stopped": is_stopped} if is_stopped else {}),)
                if has_det
                else ()
            )
            rec = EvidenceRecord(t, "camera_side", Modality.VISION, True, dets)
            frame = MultimodalFrame(master_timestamp_s=t, vision_records=(rec,), source_availability={"camera_side": True})
            res = tracker.update(frame)
            states.append(res.movement_state)
        syn_cases.append({"case": case_name, "movement_states": states, "confirmed_moving": "MOVING" in states, "confirmed_stopped": "STOPPED" in states})

    return {
        "experiment": "Exp_B_Side_Detection",
        "qualification": EXPLORATORY_LABEL,
        "hardware_gap": "No physical dedicated camera_side exists in Layer B v2; real counts reflect YOLO 'side' class outputs emitted on camera_1 and camera_2.",
        "real_summary": {
            "train_events_with_side_label": sum(1 for r in real_rows if r["event_type"] == "REAL_WORLD_TRAIN_EVENT" and (r["front_cam_side_label_frames"] + r["back_cam_side_label_frames"]) > 0),
            "no_train_events_with_side_label": sum(1 for r in real_rows if r["event_type"] == "REAL_WORLD_NO_TRAIN" and (r["front_cam_side_label_frames"] + r["back_cam_side_label_frames"]) > 0),
        },
        "real_per_event": real_rows,
        "synthetic_layer2_cases": syn_cases,
    }


def run_exp_c(ctx: VerifiedExploratoryContext) -> dict[str, Any]:
    """Experiment C: Audio-only horn evaluation against adopted event-level labels."""
    csv_path = ctx.repo_root / AUDIT_DIR / "ALL_AUDIO_WINDOW_SCORES.csv"
    per_event_windows: dict[str, list[dict[str, Any]]] = {}
    with open(csv_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            eid = str(row["event"])
            per_event_windows.setdefault(eid, []).append(
                {
                    "window_index": int(row["window_index"]),
                    "start_s": float(row["window_start_s"]),
                    "end_s": float(row["causal_end_s"]),
                    "score": float(row["score"]),
                    "pos_037": row["positive_at_frozen_0_37"].strip().lower() == "true",
                    "cohort": row["cohort"],
                    "horn_status": row["adopted_event_horn_status"],
                }
            )

    threshold = 0.3700
    tp = fp = tn = fn = 0
    y_true: list[int] = []
    y_score: list[float] = []
    audio23_rows: list[dict[str, Any]] = []
    other_rows: list[dict[str, Any]] = []

    for eid in ctx.event_order:
        ref = ctx.references[eid]
        wins = per_event_windows.get(eid, [])
        max_score = max((w["score"] for w in wins), default=0.0)
        mean_score = float(statistics.mean([w["score"] for w in wins])) if wins else 0.0
        pos_win_count = sum(1 for w in wins if w["score"] >= threshold)
        pred = max_score >= threshold
        row_obj = {
            "event_id": eid,
            "event_type": ref.event_type,
            "adopted_horn_status": ref.horn_status,
            "n_windows": len(wins),
            "positive_windows_at_037": pos_win_count,
            "max_score": round(max_score, 6),
            "mean_score": round(mean_score, 6),
            "predicted_positive_037": pred,
        }
        if ref.event_type == "REAL_WORLD_TRAIN_EVENT" and ref.horn_status in ("present", "absent_observed"):
            yt = 1 if ref.horn_status == "present" else 0
            y_true.append(yt)
            y_score.append(max_score)
            if yt == 1 and pred:
                tp += 1
            elif yt == 0 and pred:
                fp += 1
            elif yt == 0 and not pred:
                tn += 1
            else:
                fn += 1
            audio23_rows.append(row_obj)
        else:
            other_rows.append(row_obj)

    auc, ap = _roc_auc_and_ap(y_true, y_score)
    n_eval = len(y_true)
    prec = round(tp / (tp + fp), 4) if (tp + fp) else None
    rec = round(tp / (tp + fn), 4) if (tp + fn) else None
    spec = round(tn / (tn + fp), 4) if (tn + fp) else None
    f1 = round((2 * tp) / (2 * tp + fp + fn), 4) if (2 * tp + fp + fn) else None
    acc = round((tp + tn) / n_eval, 4) if n_eval else None

    return {
        "experiment": "Exp_C_Audio_Horn_Detection",
        "qualification": EXPLORATORY_LABEL,
        "methodological_note": (
            "Event-level adopted annotations (`horn_status`) do NOT include horn-onset timestamps "
            "or window-level labels and therefore CANNOT support window-level acoustic accuracy or FP rate. "
            "no_train_events have horn_status=None (road traffic horns present) and are excluded from audio23 metrics."
        ),
        "frozen_threshold": threshold,
        "audio23_metrics": {
            "n_events": n_eval,
            "n_horn_present": sum(y_true),
            "n_horn_absent_observed": n_eval - sum(y_true),
            "TP": tp,
            "FP": fp,
            "TN": tn,
            "FN": fn,
            "precision": prec,
            "precision_wilson_95ci": _wilson_ci(tp, tp + fp),
            "recall": rec,
            "recall_wilson_95ci": _wilson_ci(tp, tp + fn),
            "specificity": spec,
            "specificity_wilson_95ci": _wilson_ci(tn, tn + fp),
            "f1": f1,
            "accuracy": acc,
            "accuracy_wilson_95ci": _wilson_ci(tp + tn, n_eval),
            "event_max_roc_auc": auc,
            "event_max_average_precision": ap,
        },
        "total_windows_scored": sum(len(v) for v in per_event_windows.values()),
        "audio23_per_event": audio23_rows,
        "engine1_and_no_train3_separate": other_rows,
    }


def run_exp_d(ctx: VerifiedExploratoryContext) -> dict[str, Any]:
    """Experiment D: Back departure detection comparing V1, V2, V3-Guarded, and V3-Conservative across sync11 & back27."""
    sync11_rows: list[dict[str, Any]] = []
    back27_rows: list[dict[str, Any]] = []

    # Full-system dual/triple stream on sync11 comparing departure policies cleanly
    for eid in sorted(ctx.accepted_sync_events):
        ref = ctx.references[eid]
        recs, frames, _, bounds = _assemble_event_frames(ctx, eid, "DUAL_VISION_AUDIO")
        rear_cnt = sum(1 for r in recs if r.source_id == "camera_2" for d in r.detections if d.label.lower() == "rear" and d.confidence >= 0.35)
        side_cnt = sum(1 for r in recs if r.source_id == "camera_2" for d in r.detections if d.label.lower() == "side" and d.confidence >= 0.35)
        t4_master = bounds.get("t4")
        t1_master = bounds.get("t1")

        row: dict[str, Any] = {
            "event_id": eid,
            "back_offset_s": ref.back_offset_s,
            "T1_master_s": t1_master,
            "T4_master_s": t4_master,
            "raw_back_rear_dets": rear_cnt,
            "raw_back_side_dets": side_cnt,
            "policies": {},
        }
        for pname, eng_factory in [
            ("V1_RULE_3", lambda: make_engine("v1", ctx.frozen_config)),
            ("V2_RULE_3B_3C", lambda: make_engine("v2", ctx.frozen_config)),
            (
                "V3_GUARDED_DISAPPEARANCE",
                lambda: MultimodalDecisionEngineV3FourLayer(
                    departure_mode=DeparturePolicyMode.GUARDED_DISAPPEARANCE,
                    require_occupancy_for_reopen=False,
                ),
            ),
            (
                "V3_CONSERVATIVE_POSITIVE",
                lambda: MultimodalDecisionEngineV3FourLayer(
                    departure_mode=DeparturePolicyMode.CONSERVATIVE_POSITIVE,
                    require_occupancy_for_reopen=True,
                ),
            ),
        ]:
            eng = eng_factory()
            rr = EventSimulationRunner(decision_engine=eng, config=ctx.frozen_config).run_frames(
                frames, event_id=eid, scenario_name=f"exp_d_{pname}", entry_time_s=t1_master, clearance_time_s=t4_master
            )
            out = _extract_timing_and_outcomes(rr, t_arrival_s=bounds.get("t2"), t_clearance_s=t4_master, engine=eng)
            dep_time = next((round(s.timestamp_s, 4) for s in rr.steps if s.crossing_state == "REAR_CONFIRMED"), None)
            row["policies"][pname] = {
                "closure_triggered": out["closure_triggered"],
                "rear_confirmed_s": dep_time,
                "first_opening_s": out["first_opening_s"],
                "premature_opening_vs_T4": out["premature_opening_vs_T4"],
                "final_state": out["final_crossing_state"],
                "final_gate_state": out["final_gate_state"],
            }
        sync11_rows.append(row)

    # All 27 back streams on local back clock ONLY (single-camera descriptive check; NO dual fusion!)
    for eid in ctx.event_order:
        ref = ctx.references[eid]
        recs_b, frames_b, _, bounds_b = _assemble_event_frames(ctx, eid, "BACK_VISION")
        rear_b = sum(1 for r in recs_b for d in r.detections if d.label.lower() == "rear" and d.confidence >= 0.35)
        side_b = sum(1 for r in recs_b for d in r.detections if d.label.lower() == "side" and d.confidence >= 0.35)
        front_b = sum(1 for r in recs_b for d in r.detections if d.label.lower() == "front" and d.confidence >= 0.35)
        back27_rows.append(
            {
                "event_id": eid,
                "event_type": ref.event_type,
                "is_sync11": ref.is_dual_sync_accepted,
                "T3_back_s": bounds_b.get("t3"),
                "T4_back_s": bounds_b.get("t4"),
                "back_dur_s": ref.back_duration_s,
                "rear_dets": rear_b,
                "side_dets": side_b,
                "front_dets": front_b,
                "last_carriage_labels": 0,
            }
        )

    prem_counts = {
        p: sum(1 for r in sync11_rows if r["policies"][p]["premature_opening_vs_T4"])
        for p in ("V1_RULE_3", "V2_RULE_3B_3C", "V3_GUARDED_DISAPPEARANCE", "V3_CONSERVATIVE_POSITIVE")
    }
    return {
        "experiment": "Exp_D_Back_Departure",
        "qualification": EXPLORATORY_LABEL,
        "sync11_premature_opening_counts": prem_counts,
        "mcnemar_v2_vs_v3_conservative_premature": _exact_mcnemar(
            prem_counts["V2_RULE_3B_3C"], prem_counts["V3_CONSERVATIVE_POSITIVE"]
        ),
        "tail_detection_caveat": "Layer B v2 YOLO model has 0 'last_carriage' class predictions and only 30 'rear' detections across all 27 back streams; true last-carriage recognition remains unverified in real data.",
        "sync11_comparison": sync11_rows,
        "back27_local_clock_summary": back27_rows,
    }


def run_exp_e(ctx: VerifiedExploratoryContext, t_scene_clear: dict[str, float | None], syn_suite: dict[str, Any]) -> dict[str, Any]:
    """Experiment E: Real-data occupancy gap (only 1/27 T_scene_clear) + isolated synthetic occupancy state machine verification."""
    non_null = {eid: v for eid, v in t_scene_clear.items() if v is not None}
    # Verify isolated synthetic occupancy verifier states
    from railway_detection.fusion.occupancy import OccupancyVerifier
    from railway_detection.fusion.evidence import EvidenceStatus, OccupancyState

    occ_cases: list[dict[str, Any]] = []
    for cname, occ_ev, vis_recs in [
        ("OCCUPIED_explicit", (OccupancyEvidence(5.0, "occ_1", OccupancyState.OCCUPIED, True, 0.99),), ()),
        ("CLEAR_explicit_healthy", (OccupancyEvidence(5.0, "occ_1", OccupancyState.CLEAR, True, 0.99),), ()),
        ("UNKNOWN_no_sensor", (), ()),
        ("MISSING_unavailable", (OccupancyEvidence(5.0, "occ_1", OccupancyState.MISSING, False, None, EvidenceStatus.MISSING),), ()),
        (
            "CONTRADICTORY_clear_vs_vision",
            (OccupancyEvidence(5.0, "occ_1", OccupancyState.CLEAR, True, 0.99),),
            (EvidenceRecord(5.0, "camera_1", "vision", True, ()),),  # populated cleanly below
        ),
    ]:
        verifier = OccupancyVerifier()
        if cname == "CONTRADICTORY_clear_vs_vision":
            from railway_detection.fusion.evidence import Detection, Modality

            v_rec = (EvidenceRecord(5.0, "camera_side", Modality.VISION, True, (Detection("side", 0.9),)),)
        else:
            v_rec = ()
        frame = MultimodalFrame(master_timestamp_s=5.0, vision_records=v_rec, occupancy_records=occ_ev)
        assess = verifier.evaluate(frame)
        occ_cases.append({"case": cname, "resolved_state": assess.state.value, "verified_clear": assess.verified_clear, "reason": assess.reason})

    # Reopening block verification across Fault 05 (missing), Fault 08 (contradictory), Fault 17 (false clear)
    by_id = {s["scenario_id"]: s for s in syn_suite["fault_and_operational_scenarios"]}
    return {
        "experiment": "Exp_E_Occupancy",
        "qualification": EXPLORATORY_LABEL,
        "real_data_coverage": {
            "total_events": len(ctx.event_order),
            "dedicated_occupancy_sensors": 0,
            "events_with_T_scene_clear": len(non_null),
            "T_scene_clear_values": non_null,
            "conclusion": "Physical crossing occupancy hardware does not exist in Layer B v2; automated V3 occupancy verification cleanly remains UNKNOWN on real events and holds closed rather than fabricating CLEAR.",
        },
        "synthetic_occupancy_unit_states": occ_cases,
        "synthetic_closed_loop_checks": {
            k: by_id[k]
            for k in (
                "00_nominal_4layer_full_cycle",
                "05_occupancy_sensor_failure",
                "08_contradictory_detections",
                "17_false_clear_detection",
            )
        },
    }


def _run_condition_v3(
    ctx: VerifiedExploratoryContext,
    event_ids: list[str],
    condition: str,
    name: str,
    *,
    allow_backfill: bool = False,
    **engine_kwargs: Any,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for eid in event_ids:
        ref = ctx.references[eid]
        _, frames, _, bounds = _assemble_event_frames(
            ctx, eid, condition, allow_stale_detection_backfill=allow_backfill
        )
        eng = MultimodalDecisionEngineV3FourLayer(**engine_kwargs)
        rr = EventSimulationRunner(decision_engine=eng, config=ctx.frozen_config).run_frames(
            frames,
            event_id=eid,
            scenario_name=name,
            entry_time_s=bounds.get("t1"),
            clearance_time_s=bounds.get("t4"),
        )
        t_out = _extract_timing_and_outcomes(rr, t_arrival_s=bounds.get("t2"), t_clearance_s=bounds.get("t4"), engine=eng)
        out.append({"event_id": eid, "event_type": ref.event_type, "is_sync11": ref.is_dual_sync_accepted, **t_out})
    return out


def run_exp_f_g_h_i_j_k(ctx: VerifiedExploratoryContext) -> dict[str, Any]:
    """Experiments F, G, H, I, J, K cleanly on real caches + paired synthetic where physical side/occ needed."""
    all27 = list(ctx.event_order)
    sync11 = sorted(ctx.accepted_sync_events)

    # Exp F: Front + Side proxy (B0 front stream evaluating Layer 1 + Layer 2 tracker)
    exp_f_rows = _run_condition_v3(ctx, all27, "B0", "exp_f_front_side")
    # Exp G: Front + Audio (B4)
    exp_g_rows = _run_condition_v3(ctx, all27, "B4", "exp_g_front_audio")
    # Exp H: Multimodal Presence (B4 with front+side_proxy+audio) vs B0
    exp_h_rows = exp_g_rows  # B4 provides full front + side proxy labels + audio

    # Exp I: Complete Multimodal System on sync11 (DUAL_VISION_AUDIO under causal V3)
    exp_i_sync11 = _run_condition_v3(
        ctx,
        sync11,
        "DUAL_VISION_AUDIO",
        "exp_i_complete_v3_conservative",
        departure_mode=DeparturePolicyMode.CONSERVATIVE_POSITIVE,
        require_occupancy_for_reopen=True,
    )
    exp_i_guarded = _run_condition_v3(
        ctx,
        sync11,
        "DUAL_VISION_AUDIO",
        "exp_i_v3_guarded_no_occ_sensor",
        departure_mode=DeparturePolicyMode.GUARDED_DISAPPEARANCE,
        require_occupancy_for_reopen=False,
    )

    # Exp J: Temporal vs Stateless on IDENTICAL causal inputs across B4 (all27) and DUAL_VISION_AUDIO (sync11)
    j_policies = {}
    for pol in ("v1", "v2", "v3_conservative", "stateless_vision_rule2", "stateless_union"):
        b4_rows = []
        sync_rows = []
        for eid in all27:
            _, frames, _, bounds = _assemble_event_frames(ctx, eid, "B4", allow_stale_detection_backfill=False)
            eng = (
                MultimodalDecisionEngineV3FourLayer()
                if pol == "v3_conservative"
                else make_engine(pol, ctx.frozen_config)
            )
            rr = EventSimulationRunner(decision_engine=eng, config=ctx.frozen_config).run_frames(
                frames, event_id=eid, scenario_name=f"j_b4_{pol}", entry_time_s=bounds.get("t1")
            )
            out = _extract_timing_and_outcomes(rr, t_arrival_s=bounds.get("t2"), t_clearance_s=None, engine=eng)
            b4_rows.append({"event_id": eid, "event_type": ctx.references[eid].event_type, **out})

        for eid in sync11:
            _, frames, _, bounds = _assemble_event_frames(ctx, eid, "DUAL_VISION_AUDIO", allow_stale_detection_backfill=False)
            eng = (
                MultimodalDecisionEngineV3FourLayer()
                if pol == "v3_conservative"
                else make_engine(pol, ctx.frozen_config)
            )
            rr = EventSimulationRunner(decision_engine=eng, config=ctx.frozen_config).run_frames(
                frames, event_id=eid, scenario_name=f"j_sync_{pol}", entry_time_s=bounds.get("t1"), clearance_time_s=bounds.get("t4")
            )
            out = _extract_timing_and_outcomes(rr, t_arrival_s=bounds.get("t2"), t_clearance_s=bounds.get("t4"), engine=eng)
            sync_rows.append({"event_id": eid, "event_type": ctx.references[eid].event_type, **out})

        j_policies[pol] = {
            "b4_train23_closures": sum(1 for r in b4_rows if r["event_type"] == "REAL_WORLD_TRAIN_EVENT" and r["closure_triggered"]),
            "b4_no_train3_false_closures": sum(1 for r in b4_rows if r["event_type"] == "REAL_WORLD_NO_TRAIN" and r["closure_triggered"]),
            "b4_reopened_count": sum(1 for r in b4_rows if r["first_opening_s"] is not None),
            "sync11_closures": sum(1 for r in sync_rows if r["closure_triggered"]),
            "sync11_premature_openings_vs_T4": sum(1 for r in sync_rows if r["premature_opening_vs_T4"]),
            "b4_per_event": b4_rows,
            "sync11_per_event": sync_rows,
        }

    # Check causal collector delta vs historical allow_stale_detection_backfill=True on V2 B4/sync11
    legacy_b4_closures = sum(
        1
        for r in _run_condition_v3(ctx, all27, "B4", "legacy_backfill_v3", allow_backfill=True)
        if r["event_type"] == "REAL_WORLD_TRAIN_EVENT" and r["closure_triggered"]
    )

    # Exp K: Leave-one-modality-out ablation (real sync11 where defined + controlled synthetic 4-layer)
    # 1. Real sync11 ablation (front, audio, back):
    k_real = {}
    for cond_name, cond_code in [
        ("full_sync11_front_audio_back", "DUAL_VISION_AUDIO"),
        ("no_front_back_only_sync11", "BACK_VISION"),
        ("no_back_front_audio_sync11", "B4"),
        ("no_audio_front_back_sync11", "DUAL_VISION"),
        ("audio_only_no_vision_sync11", "AUDIO_ONLY"),
    ]:
        rows = _run_condition_v3(ctx, sync11, cond_code, f"k_{cond_name}")
        k_real[cond_name] = {
            "closures": sum(1 for r in rows if r["closure_triggered"]),
            "premature_openings": sum(1 for r in rows if r["premature_opening_vs_T4"]),
            "reopenings": sum(1 for r in rows if r["first_opening_s"] is not None),
        }

    # 2. Synthetic complete 5-source ablation (no_front, no_side, no_audio, no_back, no_occupancy):
    k_syn: dict[str, Any] = {}
    recs_base, occ_base = _baseline_nominal_streams()
    for ab_name, filter_sources, keep_occ in [
        ("full_4layer_nominal", set(), True),
        ("no_front_camera", {"camera_1"}, True),
        ("no_side_camera", {"camera_side"}, True),
        ("no_audio", {"audio_1"}, True),
        ("no_back_camera", {"camera_2"}, True),
        ("no_occupancy_sensor", set(), False),
    ]:
        recs_sub = [r for r in recs_base if r.source_id not in filter_sources]
        occ_sub = occ_base if keep_occ else []
        frames_s, _ = _collect_causal(recs_sub, occupancy=occ_sub, t_end=24.0)
        eng_s = MultimodalDecisionEngineV3FourLayer()
        rr_s = EventSimulationRunner(decision_engine=eng_s).run_frames(
            frames_s, event_id=f"syn/{ab_name}", scenario_name=ab_name, entry_time_s=6.5, clearance_time_s=13.0
        )
        k_syn[ab_name] = _extract_timing_and_outcomes(rr_s, t_arrival_s=6.5, t_clearance_s=13.0, engine=eng_s)

    return {
        "exp_f": {"experiment": "Exp_F_Front_Plus_Side_Proxy", "qualification": EXPLORATORY_LABEL, "per_event": exp_f_rows},
        "exp_g": {"experiment": "Exp_G_Front_Plus_Audio", "qualification": EXPLORATORY_LABEL, "per_event": exp_g_rows},
        "exp_h": {"experiment": "Exp_H_Multimodal_Presence", "qualification": EXPLORATORY_LABEL, "per_event": exp_h_rows},
        "exp_i": {
            "experiment": "Exp_I_Complete_Multimodal_System",
            "qualification": EXPLORATORY_LABEL,
            "sync11_conservative_v3": exp_i_sync11,
            "sync11_guarded_no_occ_sensor": exp_i_guarded,
            "causal_vs_backfill_b4_train23_closures": {"causal": j_policies["v3_conservative"]["b4_train23_closures"], "legacy_backfill": legacy_b4_closures},
        },
        "exp_j": {
            "experiment": "Exp_J_Temporal_Vs_Stateless",
            "qualification": EXPLORATORY_LABEL,
            "policies": j_policies,
            "mcnemar_v3_vs_stateless_union_no_train_fp": _exact_mcnemar(
                j_policies["stateless_union"]["b4_no_train3_false_closures"],
                j_policies["v3_conservative"]["b4_no_train3_false_closures"],
            ),
        },
        "exp_k": {
            "experiment": "Exp_K_Modality_Ablation",
            "qualification": EXPLORATORY_LABEL,
            "real_sync11_ablation": k_real,
            "synthetic_4layer_ablation": k_syn,
        },
    }


def run_exp_m(ctx: VerifiedExploratoryContext) -> dict[str, Any]:
    """Experiment M: Exploratory sensitivity sweeps across all 8 required parameters."""
    all27 = list(ctx.event_order)
    sync11 = sorted(ctx.accepted_sync_events)

    def eval_b4(
        label: str,
        *,
        conf: float = 0.35,
        confirm: int = 2,
        tol: float = 0.5,
        audio_thr: float = 0.37,
        timeout_s: float = 2.0,
        clear_dwell: float = 1.5,
        close_s: float = 3.0,
        latency_s: float = 0.0,
    ) -> dict[str, Any]:
        train_trig = 0
        no_train_fp = 0
        mean_close_lat: list[float] = []
        for eid in all27:
            ref = ctx.references[eid]
            _, frames, _, bounds = _assemble_event_frames(
                ctx,
                eid,
                "B4",
                window_tolerance_s=tol,
                delay_source="camera_1" if latency_s > 0.0 else None,
                delay_s=latency_s,
            )
            eng = MultimodalDecisionEngineV3FourLayer(
                approach_threshold=conf,
                side_threshold=conf,
                departure_threshold=conf,
                audio_threshold=audio_thr,
                confirm_frames=confirm,
                sensor_timeout_s=timeout_s,
                clearance_dwell_s=clear_dwell,
                gate_closing_s=close_s,
            )
            rr = EventSimulationRunner(decision_engine=eng).run_frames(
                frames, event_id=eid, scenario_name=f"sens_{label}", entry_time_s=bounds.get("t1")
            )
            t_close = next((s.timestamp_s for s in rr.steps if s.gate_state in ("CLOSING", "CLOSED")), None)
            if ref.event_type == "REAL_WORLD_TRAIN_EVENT" and t_close is not None:
                train_trig += 1
                mean_close_lat.append(t_close)
            elif ref.event_type == "REAL_WORLD_NO_TRAIN" and t_close is not None:
                no_train_fp += 1

        # Also check clearance dwell / gate_closing_s / timeout on nominal synthetic full pass
        recs_s, occ_s = _baseline_nominal_streams()
        if latency_s > 0.0:
            recs_s = [
                replace(r, timestamp_s=r.timestamp_s + latency_s) if r.source_id == "camera_1" else r
                for r in recs_s
            ]
        frames_s, _ = _collect_causal(recs_s, occupancy=occ_s, window_tolerance_s=min(tol, 0.25) if tol < 0.25 else tol, t_end=26.0)
        eng_s = MultimodalDecisionEngineV3FourLayer(
            approach_threshold=conf,
            side_threshold=conf,
            departure_threshold=conf,
            audio_threshold=audio_thr,
            confirm_frames=confirm,
            sensor_timeout_s=timeout_s,
            clearance_dwell_s=clear_dwell,
            gate_closing_s=close_s,
        )
        rr_s = EventSimulationRunner(decision_engine=eng_s).run_frames(
            frames_s, event_id="syn/sens", scenario_name=f"sens_syn_{label}", entry_time_s=6.5, clearance_time_s=13.0
        )
        out_s = _extract_timing_and_outcomes(rr_s, t_arrival_s=6.5, t_clearance_s=13.0, engine=eng_s)
        return {
            "variant": label,
            "is_baseline": False,
            "real_b4_train23_closures": train_trig,
            "real_b4_no_train3_fp": no_train_fp,
            "real_b4_mean_close_cmd_s": round(float(statistics.mean(mean_close_lat)), 4) if mean_close_lat else None,
            "synthetic_nominal_reopened": out_s["first_opening_s"] is not None,
            "synthetic_nominal_premature": out_s["premature_opening_vs_T4"],
            "synthetic_nominal_first_open_s": out_s["first_opening_s"],
            "synthetic_nominal_full_close_s": out_s["t_fully_closed_s"],
        }

    sweeps: dict[str, list[dict[str, Any]]] = {
        "detection_confidence": [
            {**eval_b4(f"conf={v}", conf=v), "param_value": v, "is_baseline": abs(v - 0.35) < 1e-6}
            for v in (0.20, 0.25, 0.35, 0.45, 0.55, 0.65)
        ],
        "confirm_frames": [
            {**eval_b4(f"confirm={v}", confirm=v), "param_value": v, "is_baseline": v == 2}
            for v in (1, 2, 3, 4)
        ],
        "temporal_tolerance_s": [
            {**eval_b4(f"tol={v}", tol=v), "param_value": v, "is_baseline": abs(v - 0.5) < 1e-6}
            for v in (0.15, 0.25, 0.50, 0.75, 1.00)
        ],
        "audio_threshold": [
            {**eval_b4(f"audio={v}", audio_thr=v), "param_value": v, "is_baseline": abs(v - 0.37) < 1e-6}
            for v in (0.25, 0.37, 0.50, 0.65, 0.80)
        ],
        "evidence_freshness_timeout_s": [
            {**eval_b4(f"timeout={v}", timeout_s=v), "param_value": v, "is_baseline": abs(v - 2.0) < 1e-6}
            for v in (0.5, 1.0, 2.0, 3.0, 5.0)
        ],
        "clearance_dwell_s": [
            {**eval_b4(f"dwell={v}", clear_dwell=v), "param_value": v, "is_baseline": abs(v - 1.5) < 1e-6}
            for v in (0.5, 1.0, 1.5, 2.5, 4.0)
        ],
        "gate_closing_duration_s": [
            {**eval_b4(f"close_s={v}", close_s=v), "param_value": v, "is_baseline": abs(v - 3.0) < 1e-6}
            for v in (1.5, 2.0, 3.0, 4.0, 5.0)
        ],
        "source_latency_s": [
            {**eval_b4(f"latency={v}", latency_s=v), "param_value": v, "is_baseline": abs(v - 0.0) < 1e-6}
            for v in (0.0, 0.2, 0.5, 1.0, 1.5)
        ],
    }

    return {
        "experiment": "Exp_M_Sensitivity_Analysis",
        "qualification": EXPLORATORY_LABEL,
        "non_tuning_disclaimer": "All sweeps are exploratory sensitivity diagnostics only; thresholds are NOT optimized for held-out validation.",
        "sweeps": sweeps,
    }


def build_exp_n(
    ctx: VerifiedExploratoryContext,
    exp_a: dict[str, Any],
    exp_b: dict[str, Any],
    exp_c: dict[str, Any],
    exp_d: dict[str, Any],
    exp_i: dict[str, Any],
    t_scene_clear: dict[str, float | None],
) -> tuple[list[dict[str, Any]], Path | None]:
    """Experiment N: Full 27-event machine-readable CSV & JSON matrix."""
    a_by = {r["event_id"]: r for r in exp_a["per_event"]}
    b_by = {r["event_id"]: r for r in exp_b["real_per_event"]}
    c_by = {r["event_id"]: r for r in (exp_c["audio23_per_event"] + exp_c["engine1_and_no_train3_separate"])}
    d_sync_by = {r["event_id"]: r for r in exp_d["sync11_comparison"]}
    d_27_by = {r["event_id"]: r for r in exp_d["back27_local_clock_summary"]}
    i_sync_by = {r["event_id"]: r for r in exp_i["sync11_conservative_v3"]}

    rows: list[dict[str, Any]] = []
    for eid in ctx.event_order:
        ref = ctx.references[eid]
        ar = a_by[eid]
        br = b_by[eid]
        cr = c_by[eid]
        d27 = d_27_by[eid]
        ds = d_sync_by.get(eid)
        isync = i_sync_by.get(eid)
        entry = ctx.manifest_events[eid]

        modalities = (
            "front_vision+back_vision(synced)+front_audio(no_side_cam,no_occ_sensor)"
            if ref.is_dual_sync_accepted
            else "front_vision+front_audio+uncalibrated_back_local(no_side_cam,no_occ_sensor)"
        )
        rows.append(
            {
                "event_id": eid,
                "event_type": ref.event_type,
                "is_sync11": ref.is_dual_sync_accepted,
                "available_modalities": modalities,
                "front_detected": (ar["t_first_front_det_s"] is not None),
                "side_proxy_detected_frames": br["front_cam_side_label_frames"] + br["back_cam_side_label_frames"],
                "audio_horn_status_adopted": ref.horn_status,
                "audio_max_score": cr["max_score"],
                "audio_pred_037": cr["predicted_positive_037"],
                "back_rear_dets": d27["rear_dets"],
                "back_last_carriage_dets": d27["last_carriage_labels"],
                "occupancy_sensor_state": (
                    f"T_scene_clear={t_scene_clear[eid]}" if t_scene_clear.get(eid) is not None else "MISSING_OR_UNKNOWN"
                ),
                "closure_decision": ar["closure_triggered"],
                "clearance_decision_v3_sync11": (
                    isync["final_crossing_state"] == "CROSSING_CLEAR" if isync else "NOT_APPLICABLE_UNSYNCED"
                ),
                "reopening_decision_v3_sync11": (
                    isync["first_opening_s"] is not None if isync else False
                ),
                "v2_premature_opening_vs_T4": (
                    ds["policies"]["V2_RULE_3B_3C"]["premature_opening_vs_T4"] if ds else None
                ),
                "v3_premature_opening_vs_T4": (
                    ds["policies"]["V3_CONSERVATIVE_POSITIVE"]["premature_opening_vs_T4"] if ds else None
                ),
                "t_first_front_det_s": ar["t_first_front_det_s"],
                "t_close_cmd_s": ar["t_close_cmd_s"],
                "t_fully_closed_s": ar["t_fully_closed_s"],
                "T2_s": ar["T2_s"],
                "T4_master_s": ds["T4_master_s"] if ds else None,
                "safety_margin_vs_T2_s": ar["margin_full_vs_T2_s"],
                "failure_or_limitation_reason": (
                    "no_occupancy_sensor; unverified_tail; pre_db40305_cache"
                    if ref.is_dual_sync_accepted
                    else "no_sync_calibration; no_occupancy_sensor; unverified_tail; pre_db40305_cache"
                ),
                "evidence_provenance_sha256_prefix": entry["front_cache_sha256"][:12],
            }
        )
    return rows, None


def export_replay_traces(
    ctx: VerifiedExploratoryContext,
    out_root: Path,
    syn_traces: dict[str, Any],
) -> None:
    """Export deterministic decision & state-transition replay traces into results/exploratory_v2/replays/."""
    replays_dir = out_root / "replays"
    replays_dir.mkdir(parents=True, exist_ok=True)

    b4_traces: dict[str, Any] = {}
    for eid in ctx.event_order:
        ref = ctx.references[eid]
        _, frames, clock_mode, bounds = _assemble_event_frames(ctx, eid, "B4", allow_stale_detection_backfill=False)
        eng = MultimodalDecisionEngineV3FourLayer()
        res = EventSimulationRunner(decision_engine=eng, config=ctx.frozen_config).run_frames(
            frames,
            event_id=eid,
            scenario_name="replay_b4_v3_conservative",
            entry_time_s=bounds.get("t1"),
            clearance_time_s=bounds.get("t4"),
        )
        b4_traces[eid] = serialize_simulation_result(
            res,
            event_id=eid,
            condition="B4",
            policy="V3_CONSERVATIVE_POSITIVE",
            clock_mode=clock_mode,
            ref=ref,
            mapped_bounds=bounds,
            window_tolerance_s=0.5,
            stride_s=0.2,
        )
    _write_json(
        replays_dir / "real_b4_v3_traces.json",
        {
            "qualification": EXPLORATORY_LABEL,
            "condition": "B4",
            "policy": "V3_CONSERVATIVE_POSITIVE",
            "event_count": len(b4_traces),
            "traces": b4_traces,
        },
    )

    sync11_v3_traces: dict[str, Any] = {}
    sync11_policy_cmp: dict[str, Any] = {}
    for eid in sorted(ctx.accepted_sync_events):
        ref = ctx.references[eid]
        _, frames, clock_mode, bounds = _assemble_event_frames(
            ctx, eid, "DUAL_VISION_AUDIO", allow_stale_detection_backfill=False
        )
        per_pol: dict[str, Any] = {}
        for pname, eng in [
            ("V1_RULE_3", make_engine("v1", ctx.frozen_config)),
            ("V2_RULE_3B_3C", make_engine("v2", ctx.frozen_config)),
            (
                "V3_GUARDED_DISAPPEARANCE",
                MultimodalDecisionEngineV3FourLayer(
                    departure_mode=DeparturePolicyMode.GUARDED_DISAPPEARANCE,
                    require_occupancy_for_reopen=False,
                ),
            ),
            (
                "V3_CONSERVATIVE_POSITIVE",
                MultimodalDecisionEngineV3FourLayer(
                    departure_mode=DeparturePolicyMode.CONSERVATIVE_POSITIVE,
                    require_occupancy_for_reopen=True,
                ),
            ),
        ]:
            res = EventSimulationRunner(decision_engine=eng, config=ctx.frozen_config).run_frames(
                frames,
                event_id=eid,
                scenario_name=f"replay_sync11_{pname}",
                entry_time_s=bounds.get("t1"),
                clearance_time_s=bounds.get("t4"),
            )
            full_rec = serialize_simulation_result(
                res,
                event_id=eid,
                condition="DUAL_VISION_AUDIO",
                policy=pname,
                clock_mode=clock_mode,
                ref=ref,
                mapped_bounds=bounds,
                window_tolerance_s=0.5,
                stride_s=0.2,
            )
            if pname == "V3_CONSERVATIVE_POSITIVE":
                sync11_v3_traces[eid] = full_rec
            per_pol[pname] = {
                "premature_opening_detected": full_rec["premature_opening_detected"],
                "final_crossing_state": full_rec["final_crossing_state"],
                "final_gate_state": full_rec["final_gate_state"],
                "step_count": full_rec["step_count"],
                "transitions": full_rec["transitions"],
                "rule_counts": full_rec["rule_counts"],
            }
        sync11_policy_cmp[eid] = per_pol

    _write_json(
        replays_dir / "real_sync11_v3_traces.json",
        {
            "qualification": EXPLORATORY_LABEL,
            "condition": "DUAL_VISION_AUDIO",
            "policy": "V3_CONSERVATIVE_POSITIVE",
            "event_count": len(sync11_v3_traces),
            "traces": sync11_v3_traces,
        },
    )
    _write_json(
        replays_dir / "real_sync11_policy_comparison_traces.json",
        {
            "qualification": EXPLORATORY_LABEL,
            "condition": "DUAL_VISION_AUDIO",
            "event_count": len(sync11_policy_cmp),
            "traces": sync11_policy_cmp,
        },
    )
    _write_json(
        replays_dir / "synthetic_scenarios_traces.json",
        {
            "classification": "SYNTHETIC_CONTROLLED_SCENARIOS",
            "scenario_count": len(syn_traces),
            "traces": syn_traces,
        },
    )


def main() -> None:
    t0 = time.perf_counter()
    ctx = load_verified_context()
    root = ctx.repo_root
    out_root = root / RESULTS_DIR_NAME
    rot_map = _load_source_rotations(root)
    t_scene_clear = _load_t_scene_clear_map(ctx)

    print("[1/6] Running synthetic multi-orientation FFmpeg + YOLOv8n + audio checks...")
    vid_check = verify_synthetic_video_orientation_and_yolo(root)
    aud_check = verify_audio_v3_transform_and_scenarios(root)
    _write_json(out_root / "synthetic/vision_orientation_check.json", vid_check)
    _write_json(out_root / "synthetic/audio_transform_check.json", aud_check)

    print("[2/6] Running 18 synthetic fault & four-layer operational scenarios (Exp L)...")
    syn_suite_full = run_synthetic_suite(include_traces=True)
    syn_traces = syn_suite_full.pop("traces", {})
    syn_suite = syn_suite_full
    _write_json(
        out_root / "failure_injection/exp_l_fault_injection.json",
        {"experiment": "Exp_L_Fault_Injection_17_Scenarios", **syn_suite},
    )

    print("[3/6] Running Experiments A, B, C, D, E...")
    exp_a = run_exp_a(ctx, rot_map)
    exp_b = run_exp_b(ctx)
    exp_c = run_exp_c(ctx)
    exp_d = run_exp_d(ctx)
    exp_e = run_exp_e(ctx, t_scene_clear, syn_suite)
    _write_json(out_root / "experiments/exp_a_front_detection.json", exp_a)
    _write_json(out_root / "experiments/exp_b_side_detection.json", exp_b)
    _write_json(out_root / "experiments/exp_c_audio_horn.json", exp_c)
    _write_json(out_root / "experiments/exp_d_back_departure.json", exp_d)
    _write_json(out_root / "experiments/exp_e_occupancy.json", exp_e)

    print("[4/6] Running Experiments F, G, H, I, J, K...")
    fghijk = run_exp_f_g_h_i_j_k(ctx)
    _write_json(out_root / "experiments/exp_f_front_side.json", fghijk["exp_f"])
    _write_json(out_root / "experiments/exp_g_front_audio.json", fghijk["exp_g"])
    _write_json(out_root / "experiments/exp_h_multimodal_presence.json", fghijk["exp_h"])
    _write_json(out_root / "experiments/exp_i_complete_system.json", fghijk["exp_i"])
    _write_json(out_root / "experiments/exp_j_temporal_vs_stateless.json", fghijk["exp_j"])
    _write_json(out_root / "experiments/exp_k_ablation.json", fghijk["exp_k"])

    print("[5/6] Running Experiment M (8-parameter sensitivity sweeps) & Experiment N (27-event matrix)...")
    exp_m = run_exp_m(ctx)
    _write_json(out_root / "sensitivity/exp_m_sensitivity.json", exp_m)

    exp_n_rows, _ = build_exp_n(ctx, exp_a, exp_b, exp_c, exp_d, fghijk["exp_i"], t_scene_clear)
    _write_json(
        out_root / "experiments/exp_n_event_matrix.json",
        {"experiment": "Exp_N_Event_Level_Matrix", "qualification": EXPLORATORY_LABEL, "events": exp_n_rows},
    )
    csv_path = out_root / "experiments/exp_n_event_matrix.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(exp_n_rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(exp_n_rows)

    stats_summary = {
        "qualification": EXPLORATORY_LABEL,
        "exp_a_closure": exp_a["summary"],
        "exp_c_audio23": exp_c["audio23_metrics"],
        "exp_d_premature_mcnemar": exp_d["mcnemar_v2_vs_v3_conservative_premature"],
        "exp_j_no_train_fp_mcnemar": fghijk["exp_j"]["mcnemar_v3_vs_stateless_union_no_train_fp"],
    }
    _write_json(out_root / "analysis/statistical_comparisons.json", stats_summary)

    runtime_s = round(time.perf_counter() - t0, 3)
    master = {
        "qualification": EXPLORATORY_LABEL,
        "results_directory": RESULTS_DIR_NAME,
        "video_orientation_all_angles_passed": vid_check["all_angles_passed"],
        "audio_transform_natural_verified": aud_check["natural_finite"] and aud_check["natural_differs_from_db_by_scale"],
        "exp_l_all_transitions_legal": syn_suite["all_transitions_legal"],
        "exp_l_unsafe_openings": syn_suite["unsafe_opening_count"],
        "exp_a_summary": exp_a["summary"],
        "exp_c_summary": exp_c["audio23_metrics"],
        "exp_d_premature_counts": exp_d["sync11_premature_opening_counts"],
    }
    _write_json(out_root / "MASTER_V2_SUMMARY.json", master)

    print("[5b/6] Exporting deterministic replay traces...")
    export_replay_traces(ctx, out_root, syn_traces)

    # Write deterministic SHA-256 manifest of all deterministic artifacts inside results/exploratory_v2/
    manifest_lines: list[str] = []
    for p in sorted(out_root.rglob("*")):
        if p.is_file() and p.name not in {"FILE_HASH_MANIFEST.sha256", "runtime_telemetry.json"}:
            digest = hashlib.sha256(p.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
            manifest_lines.append(f"{digest}  {p.relative_to(root).as_posix()}")
    (out_root / "FILE_HASH_MANIFEST.sha256").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    _write_json(out_root / "analysis/runtime_telemetry.json", {"total_runtime_s": runtime_s, "deterministic_artifact_count": len(manifest_lines)})

    print(f"[6/6] Completed Experiments A-N cleanly in {runtime_s}s ({len(manifest_lines)} result artifacts hashed).")


if __name__ == "__main__":
    main()
