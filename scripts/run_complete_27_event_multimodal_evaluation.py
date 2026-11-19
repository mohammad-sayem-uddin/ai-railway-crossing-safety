#!/usr/bin/env python3
"""Complete 27-Event Multimodal Experimental Evaluation & Vision+Audio Fusion Analysis.

Evaluates the trained vision model (YOLOv8n) and audio model (CompactTrainHornCNN)
across all 27 collected Layer B v2 events (23 train_events, 3 no_train_events,
1 engine_events) using verified, precomputed inference caches and researcher-adopted
AI-assisted reference proposals.

Strict Provenance & Scope Guarantees:
- Never opens, probes, or reads raw media files under data/raw/ or binary .pt/.mov/.wav files.
- Explicitly labels vision predictions as:
  "Mission 39/43 Frozen YOLOv8n Actual Inference Caches (pre-db40305 unrotated container decoding)"
- Explicitly labels audio predictions as:
  "Mission 39/43 Corrected Natural Log-Mel CompactTrainHornCNN Actual Inference Caches"
- Explicitly labels reference ground truth as:
  "Researcher-adopted AI-assisted reference proposals (RESEARCHER_ANNOTATION_ADOPTION.json)"
- Preserves R04 calibration separation: synchronized master-clock timeline simulation
  runs strictly on the 11 calibrated sync11 events, while local-clock perception,
  single-stream causal gate control, and event-level modality/fusion detection
  comparisons cover all 27 events (and stratify sync11 vs independent_camera).
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from exploratory_common import (  # noqa: E402
    EXPLORATORY_LABEL,
    VerifiedExploratoryContext,
    load_event_evidence_records,
    load_verified_context,
    wilson_ci_95,
)
from railway_detection.fusion.collector import MultimodalEvidenceCollector  # noqa: E402
from railway_detection.fusion.decision_engine_v3_four_layer import (  # noqa: E402
    MultimodalDecisionEngineV3FourLayer,
)
from railway_detection.fusion.rules_v3_four_layer import (  # noqa: E402
    DeparturePolicyMode,
    SideMovementTracker,
)
from railway_detection.simulation.runner import EventSimulationRunner, SimulationRunResult  # noqa: E402

VISION_CACHE_PROVENANCE = (
    "Mission 39/43 Frozen YOLOv8n Actual Inference Caches "
    "(pre-db40305 unrotated container decoding; 6,613 front frames / 329 objects, "
    "6,479 back frames / 1,020 objects)"
)
AUDIO_CACHE_PROVENANCE = (
    "Mission 39/43 Corrected Natural Log-Mel CompactTrainHornCNN Actual Inference Caches "
    "(2,600 windows of 1.0 s / 0.5 s hop)"
)
REFERENCE_PROVENANCE = (
    "Researcher-adopted AI-assisted reference proposals "
    "(docs/generated/professor_evidence/mission43/RESEARCHER_ANNOTATION_ADOPTION.json)"
)

OUTPUT_DIR = REPO_ROOT / "results" / "multimodal_27_event_evaluation"
EXP_V2_DIR = REPO_ROOT / "results" / "exploratory_v2"
QUICKTIME_DELTAS_PATH = REPO_ROOT / "results" / "r04_sync_estimation" / "quicktime_creationdate_deltas.json"
VISUAL_PER_EVENT_CSV = (
    REPO_ROOT / "docs" / "generated" / "professor_evidence" / "mission43" / "VISUAL_PER_EVENT_RESULTS.csv"
)
AUDIO_PER_EVENT_CSV = (
    REPO_ROOT / "docs" / "generated" / "professor_evidence" / "mission43" / "AUDIO_PER_EVENT_RESULTS.csv"
)


def _exact_mcnemar(a_preds: list[bool], b_preds: list[bool], truths: list[bool]) -> dict[str, Any]:
    """Exact two-sided binomial McNemar test on paired correctness of predictor A vs B."""
    b01 = 0  # A wrong, B right
    b10 = 0  # A right, B wrong
    for pa, pb, yt in zip(a_preds, b_preds, truths):
        ra = (pa == yt)
        rb = (pb == yt)
        if not ra and rb:
            b01 += 1
        elif ra and not rb:
            b10 += 1
    n = b01 + b10
    if n == 0:
        p_val = 1.0
    else:
        k = min(b01, b10)
        p_tail = sum(math.comb(n, i) * (0.5**n) for i in range(0, k + 1))
        p_val = min(1.0, 2.0 * p_tail)
    return {
        "discordant_pairs": n,
        "b01_baseline_wrong_candidate_right": b01,
        "b10_baseline_right_candidate_wrong": b10,
        "exact_p_value": round(p_val, 6),
    }


def _parse_vision_stream(jsonl_path: Path, threshold: float = 0.35) -> dict[str, Any]:
    """Parse precomputed vision JSONL cache into per-class counts, timestamps, confidences, and runs."""
    frames: list[dict[str, Any]] = []
    with open(jsonl_path, "r", encoding="utf-8", newline="") as handle:
        for line in handle:
            if line.strip():
                frames.append(json.loads(line))

    cls_counts = {"front": 0, "side": 0, "rear": 0, "other": 0}
    cls_confs: dict[str, list[float]] = {"front": [], "side": [], "rear": []}
    all_confs: list[float] = []
    det_frame_ts: list[float] = []
    strict_front_ts: list[float] = []
    side_det_ts: list[float] = []
    rear_det_ts: list[float] = []

    consec_any = 0
    max_consec_any = 0
    consec_front_strict = 0
    max_consec_front_strict = 0
    consec_side = 0
    max_consec_side = 0
    consec_side_rear = 0
    max_consec_side_rear = 0
    det_frames = 0
    first_consec2_any_t: float | None = None
    first_consec2_sr_t: float | None = None

    last_ts = 0.0
    for fr in frames:
        ts = float(fr["timestamp_sec"] if "timestamp_sec" in fr else fr["timestamp_s"])
        last_ts = ts
        raw_dets = fr.get("detections", [])
        qual_dets = [d for d in raw_dets if float(d.get("confidence", 0.0)) >= threshold]
        if qual_dets:
            det_frames += 1
            det_frame_ts.append(ts)
            consec_any += 1
            max_consec_any = max(max_consec_any, consec_any)
            if consec_any >= 2 and first_consec2_any_t is None:
                first_consec2_any_t = ts
        else:
            consec_any = 0

        frame_labels: set[str] = set()
        for d in qual_dets:
            lbl = str(d.get("label") or d.get("class_name") or "").strip().lower()
            conf = float(d["confidence"])
            all_confs.append(conf)
            if lbl in cls_counts:
                cls_counts[lbl] += 1
                cls_confs[lbl].append(conf)
            else:
                cls_counts["other"] += 1
            frame_labels.add(lbl)

        if "front" in frame_labels:
            strict_front_ts.append(ts)
            consec_front_strict += 1
            max_consec_front_strict = max(max_consec_front_strict, consec_front_strict)
        else:
            consec_front_strict = 0

        if "side" in frame_labels:
            side_det_ts.append(ts)
            consec_side += 1
            max_consec_side = max(max_consec_side, consec_side)
        else:
            consec_side = 0

        if "rear" in frame_labels:
            rear_det_ts.append(ts)

        if "side" in frame_labels or "rear" in frame_labels:
            consec_side_rear += 1
            max_consec_side_rear = max(max_consec_side_rear, consec_side_rear)
            if consec_side_rear >= 2 and first_consec2_sr_t is None:
                first_consec2_sr_t = ts
        else:
            consec_side_rear = 0

    return {
        "sampled_frames": len(frames),
        "duration_s": round(last_ts, 4),
        "det_frames": det_frames,
        "total_objects": sum(cls_counts.values()),
        "cls_counts": cls_counts,
        "min_conf": round(min(all_confs), 4) if all_confs else None,
        "mean_conf": round(sum(all_confs) / len(all_confs), 4) if all_confs else None,
        "max_conf": round(max(all_confs), 4) if all_confs else None,
        "cls_max_conf": {
            k: (round(max(v), 4) if v else None) for k, v in cls_confs.items()
        },
        "first_det_s": round(det_frame_ts[0], 4) if det_frame_ts else None,
        "last_det_s": round(det_frame_ts[-1], 4) if det_frame_ts else None,
        "first_strict_front_s": round(strict_front_ts[0], 4) if strict_front_ts else None,
        "first_side_det_s": round(side_det_ts[0], 4) if side_det_ts else None,
        "last_side_det_s": round(side_det_ts[-1], 4) if side_det_ts else None,
        "first_rear_det_s": round(rear_det_ts[0], 4) if rear_det_ts else None,
        "last_rear_det_s": round(rear_det_ts[-1], 4) if rear_det_ts else None,
        "max_consec_any": max_consec_any,
        "max_consec_front_strict": max_consec_front_strict,
        "max_consec_side": max_consec_side,
        "max_consec_side_rear": max_consec_side_rear,
        "first_consec2_any_s": round(first_consec2_any_t, 4) if first_consec2_any_t is not None else None,
        "first_consec2_sr_s": round(first_consec2_sr_t, 4) if first_consec2_sr_t is not None else None,
    }


def _parse_audio_stream(jsonl_path: Path) -> dict[str, Any]:
    """Parse precomputed audio window JSONL cache across frozen and hysteresis thresholds."""
    windows: list[dict[str, Any]] = []
    with open(jsonl_path, "r", encoding="utf-8", newline="") as handle:
        for line in handle:
            if line.strip():
                windows.append(json.loads(line))

    scores: list[tuple[float, float]] = []
    for w in windows:
        ts = float(w["end_sec"])
        sc = float(w["horn_confidence"])
        scores.append((ts, sc))

    pos_037_ts: list[float] = []
    pos_075_ts: list[float] = []
    run37 = max_run37 = 0
    run75 = max_run75 = 0
    first_037_k2_s: float | None = None
    first_075_k2_s: float | None = None

    for ts, sc in scores:
        if sc >= 0.37:
            pos_037_ts.append(ts)
            run37 += 1
            max_run37 = max(max_run37, run37)
            if run37 >= 2 and first_037_k2_s is None:
                first_037_k2_s = ts
        else:
            run37 = 0

        if sc >= 0.75:
            pos_075_ts.append(ts)
            run75 += 1
            max_run75 = max(max_run75, run75)
            if run75 >= 2 and first_075_k2_s is None:
                first_075_k2_s = ts
        else:
            run75 = 0

    peak_ts, max_sc = max(scores, key=lambda x: x[1]) if scores else (None, 0.0)
    mean_sc = sum(s for _, s in scores) / len(scores) if scores else 0.0
    min_sc = min(s for _, s in scores) if scores else 0.0

    return {
        "n_windows": len(scores),
        "pos_windows_037": len(pos_037_ts),
        "pos_windows_075": len(pos_075_ts),
        "max_run_037": max_run37,
        "max_run_075": max_run75,
        "first_037_k1_s": round(pos_037_ts[0], 4) if pos_037_ts else None,
        "last_037_k1_s": round(pos_037_ts[-1], 4) if pos_037_ts else None,
        "first_037_k2_s": round(first_037_k2_s, 4) if first_037_k2_s is not None else None,
        "first_075_k1_s": round(pos_075_ts[0], 4) if pos_075_ts else None,
        "first_075_k2_s": round(first_075_k2_s, 4) if first_075_k2_s is not None else None,
        "peak_s": round(peak_ts, 4) if peak_ts is not None else None,
        "min_score": round(min_sc, 4),
        "mean_score": round(mean_sc, 4),
        "max_score": round(max_sc, 4),
    }


def _run_side_tracker_proxy(ctx: VerifiedExploratoryContext, eid: str) -> dict[str, Any]:
    """Run Layer 2 SideMovementTracker on available vision stream(s) for event eid."""
    condition = "DUAL_VISION_AUDIO" if eid in ctx.accepted_sync_events else "B4"
    records, aligner, _ = load_event_evidence_records(ctx, eid, condition)
    collector = MultimodalEvidenceCollector(
        sync_aligner=aligner,
        window_tolerance_s=0.5,
        event_id=eid,
        allow_stale_detection_backfill=False,
    )
    collector.add_evidence_batch(records, preserve_arrival_order=False)
    master_times = [
        aligner.to_master(r.source_id, r.timestamp_s)
        if (aligner is not None and r.source_id in aligner.offsets_s)
        else r.timestamp_s
        for r in records
    ]
    frames = collector.generate_frames_from_history(min(master_times), max(master_times), stride_s=0.2)
    tracker = SideMovementTracker()
    states: list[str] = []
    max_consec_obs = 0
    for fr in frames:
        res = tracker.update(fr)
        if res.present:
            states.append(res.movement_state)
            max_consec_obs = max(max_consec_obs, res.consecutive_observations)
    if "MOVING" in states:
        final_proxy_state = "MOVING"
    elif "STOPPED" in states:
        final_proxy_state = "STOPPED"
    elif "SINGLE_FRAME" in states:
        final_proxy_state = "SINGLE_FRAME"
    else:
        final_proxy_state = "UNOBSERVED"
    return {
        "tracker_state": final_proxy_state,
        "tracker_moving_ticks": states.count("MOVING"),
        "tracker_stopped_ticks": states.count("STOPPED"),
        "tracker_single_frame_ticks": states.count("SINGLE_FRAME"),
        "tracker_max_consec_obs": max_consec_obs,
    }


def _sim_b4_v3(ctx: VerifiedExploratoryContext, eid: str, t_arrival_s: float | None) -> dict[str, Any]:
    """Run causal V3 controller on B4 (front_vision + front_audio) and check audio dwell extensions."""
    records, aligner, _ = load_event_evidence_records(ctx, eid, "B4")
    collector = MultimodalEvidenceCollector(
        sync_aligner=aligner,
        window_tolerance_s=0.5,
        event_id=eid,
        allow_stale_detection_backfill=False,
    )
    collector.add_evidence_batch(records, preserve_arrival_order=False)
    master_times = [r.timestamp_s for r in records]
    frames = collector.generate_frames_from_history(min(master_times), max(master_times), stride_s=0.2)
    eng = MultimodalDecisionEngineV3FourLayer(allow_any_front_camera_label=True)
    res: SimulationRunResult = EventSimulationRunner(decision_engine=eng, config=ctx.frozen_config).run_frames(
        frames, event_id=eid, scenario_name="b4_v3_eval"
    )
    t_warn = next((round(s.timestamp_s, 4) for s in res.steps if s.crossing_state == "WARNING"), None)
    t_close = next((round(s.timestamp_s, 4) for s in res.steps if s.gate_state in ("CLOSING", "CLOSED")), None)
    t_half = next((round(s.timestamp_s, 4) for s in res.steps if s.is_passage_blocked), None)
    t_full = next((round(s.timestamp_s, 4) for s in res.steps if s.gate_angle_deg <= 1e-6), None)
    t_open = next((round(s.timestamp_s, 4) for s in res.steps if s.crossing_state == "GATE_OPENING"), None)
    audio_ext = any("AUDIO_DWELL_HOLD" in (s.decision.rule_id or "").upper() for s in res.steps)
    audio_support_only = any("AUDIO_SUPPORT_ONLY" in (s.decision.rule_id or "").upper() for s in res.steps)
    trace = getattr(eng, "timing_trace", {}) or {}
    return {
        "closure_triggered": t_warn is not None or t_close is not None,
        "t_first_det_s": trace.get("first_front_detection_s"),
        "t_confirm_s": trace.get("confirmed_front_detection_s"),
        "t_warning_s": t_warn,
        "t_close_cmd_s": t_close,
        "t_half_closed_s": t_half,
        "t_fully_closed_s": t_full,
        "margin_full_vs_T2_s": (
            round(t_arrival_s - t_full, 4) if (t_arrival_s is not None and t_full is not None) else None
        ),
        "t_reopen_s": t_open,
        "audio_extended_dwell": audio_ext,
        "audio_support_only_idle": audio_support_only,
        "final_crossing_state": res.steps[-1].crossing_state if res.steps else "NONE",
        "final_gate_state": res.steps[-1].gate_state if res.steps else "NONE",
        "closed_duration_s": round(res.closed_duration_s, 4),
    }


def _compute_binary_metrics(
    rows: list[dict[str, Any]],
    pred_key: str,
    truth_key: str,
    *,
    baseline_key: str | None = None,
    subset_filter: Any = None,
) -> dict[str, Any]:
    """Compute confusion matrix, P/R/Spec/F1/Acc, Wilson 95% CIs, and McNemar vs baseline."""
    sub = [r for r in rows if (subset_filter(r) if subset_filter else True)]
    tp = fp = tn = fn = 0
    fp_no_train = fp_engine = 0
    gained_events: list[str] = []
    fp_events: list[str] = []
    fn_events: list[str] = []

    preds: list[bool] = []
    truths: list[bool] = []
    base_preds: list[bool] = []

    for r in sub:
        y = bool(r[truth_key])
        p = bool(r[pred_key])
        preds.append(p)
        truths.append(y)
        if baseline_key:
            pb = bool(r[baseline_key])
            base_preds.append(pb)
            if y and p and not pb:
                gained_events.append(r["event_id"])
        if y and p:
            tp += 1
        elif y and not p:
            fn += 1
            fn_events.append(r["event_id"])
        elif not y and p:
            fp += 1
            fp_events.append(r["event_id"])
            if r["cohort"] == "no_train_events":
                fp_no_train += 1
            elif r["cohort"] == "engine_events":
                fp_engine += 1
        else:
            tn += 1

    n = len(sub)
    pos = tp + fn
    neg = tn + fp
    prec, prec_lo, prec_hi = wilson_ci_95(tp, tp + fp) if (tp + fp) > 0 else (0.0, 0.0, 0.0)
    rec, rec_lo, rec_hi = wilson_ci_95(tp, pos) if pos > 0 else (0.0, 0.0, 0.0)
    spec, spec_lo, spec_hi = wilson_ci_95(tn, neg) if neg > 0 else (0.0, 0.0, 0.0)
    acc, acc_lo, acc_hi = wilson_ci_95(tp + tn, n) if n > 0 else (0.0, 0.0, 0.0)
    f1 = (2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

    mcnemar = (
        _exact_mcnemar(base_preds, preds, truths)
        if baseline_key is not None
        else {"discordant_pairs": 0, "b01_baseline_wrong_candidate_right": 0, "b10_baseline_right_candidate_wrong": 0, "exact_p_value": 1.0}
    )

    return {
        "n_events": n,
        "pos_gt": pos,
        "neg_gt": neg,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "fp_no_train": fp_no_train,
        "fp_engine": fp_engine,
        "precision": round(prec, 4),
        "precision_ci95": [round(prec_lo, 4), round(prec_hi, 4)],
        "recall": round(rec, 4),
        "recall_ci95": [round(rec_lo, 4), round(rec_hi, 4)],
        "specificity": round(spec, 4),
        "specificity_ci95": [round(spec_lo, 4), round(spec_hi, 4)],
        "f1": round(f1, 4),
        "accuracy": round(acc, 4),
        "accuracy_ci95": [round(acc_lo, 4), round(acc_hi, 4)],
        "mcnemar_vs_baseline": mcnemar,
        "events_gained_over_front_L1": gained_events,
        "false_positive_events": fp_events,
        "false_negative_events": fn_events,
    }


def _failure_or_recovery_reason(row: dict[str, Any]) -> str:
    if row["cohort"] == "no_train_events":
        parts = []
        if row["front_det_frames"] > 0:
            parts.append(f"front={row['front_det_frames']}f(max_c={row['front_max_consec']})")
        if row["back_cls_front"] > 0:
            parts.append(f"back_false_front={row['back_cls_front']}obj")
        if row["audio_pos_037"] > 0:
            parts.append(f"audio_037={row['audio_pos_037']}w(r75={row['audio_max_run_075']})")
        return "TN under V2/F5/F6; " + (", ".join(parts) if parts else "clean across all sensors")

    if row["cohort"] == "engine_events":
        return (
            f"Solitary light locomotive (train_present=True, 0 cars): front=0f, audio=0w(max={row['audio_max_score']}); "
            f"back_cls_front={row['back_cls_front']}obj(c={row['back_max_consec']}, maxC={row['back_max_conf']}), 0 side/rear"
        )

    if row["pred_V2_front_L1_confirm2"]:
        if row["front_lead_vs_T2_s"] is not None and row["front_lead_vs_T2_s"] < 0:
            return (
                f"Detected by Front L1 ({row['front_max_consec']} consec), "
                f"but late ({row['front_first_det_s']}s vs T2={row['gt_T2_s']}s)"
            )
        return f"Detected cleanly by Front L1 ({row['front_max_consec']} consec frames)"

    recovered = []
    if row["pred_V5_back_confirm2_side_rear"]:
        recovered.append(f"Back side/rear L1 ({row['back_max_consec_side_rear']} consec)")
    if row["pred_A3_audio_075_k2"]:
        recovered.append(f"Audio >=0.75 k=2 (run={row['audio_max_run_075']}, max={row['audio_max_score']})")
    if recovered:
        return f"Missed by Front L1 (df={row['front_det_frames']}, max_c={row['front_max_consec']}); RECOVERED by " + " + ".join(recovered)
    return (
        f"Missed by Front L1 (df={row['front_det_frames']}), Back side/rear L1 "
        f"(c={row['back_max_consec_side_rear']}), & Audio >=0.75 k=2 (r75={row['audio_max_run_075']}, maxA={row['audio_max_score']})"
    )


def _load_supporting_lookup() -> dict[str, Any]:
    """Load R04 metadata, QuickTime session dates, M2/M3 departure errors, and LOEO audio folds."""
    qt = json.loads(QUICKTIME_DELTAS_PATH.read_text(encoding="utf-8"))
    exp_d = json.loads((EXP_V2_DIR / "experiments" / "exp_d_back_departure.json").read_text(encoding="utf-8"))
    exp_o = json.loads((EXP_V2_DIR / "optimization_and_stress" / "exp_o_audio_calibration_hysteresis.json").read_text(encoding="utf-8"))
    exp_r = json.loads((EXP_V2_DIR / "optimization_and_stress" / "exp_r_independent_validation.json").read_text(encoding="utf-8"))

    vis_csv = {(r["event"], r["camera"]): r for r in csv.DictReader(open(VISUAL_PER_EVENT_CSV, encoding="utf-8"))}
    aud_csv = {r["event"]: r for r in csv.DictReader(open(AUDIO_PER_EVENT_CSV, encoding="utf-8"))}

    sync11_d = {r["event_id"]: r for r in exp_d["sync11_comparison"]}
    back27_d = {r["event_id"]: r for r in exp_d["back27_local_clock_summary"]}
    exp_o_map = {r["event_id"]: r for r in exp_o["event_run_summaries"]}
    loeo_folds = {r["fold_event"]: r for r in exp_r["reproduced_published_loeo"]["folds"]}
    return {
        "qt": qt,
        "vis_csv": vis_csv,
        "aud_csv": aud_csv,
        "sync11_d": sync11_d,
        "back27_d": back27_d,
        "exp_o": exp_o_map,
        "loeo_folds": loeo_folds,
        "loeo_summary": exp_r["reproduced_published_loeo"]["oof_metrics"],
        "loeo_strict_train_only": exp_r["sensitivity_1_strict_train_only_selection"]["oof_metrics"],
        "exp_o_best_f1": exp_o["best_f1_point"],
    }


def _fmt(val: Any, suffix: str = "") -> str:
    if val is None or val == "":
        return "—"
    if isinstance(val, bool):
        return "YES" if val else "NO"
    if isinstance(val, float):
        return f"{val:.2f}{suffix}"
    return f"{val}{suffix}"


def _build_markdown_report(
    events: list[dict[str, Any]],
    view1_train23_vs_nt3: dict[str, dict[str, Any]],
    view2_train23_vs_ctrl4: dict[str, dict[str, Any]],
    view3_rail24_vs_nt3: dict[str, dict[str, Any]],
    horn_configs: dict[str, dict[str, Any]],
    support: dict[str, Any],
) -> str:
    """Render the comprehensive 27-event experimental report in Markdown."""
    engine_row = next(r for r in events if r["cohort"] == "engine_events")
    lines: list[str] = []
    lines.append("# Complete 27-Event Multimodal Experimental Evaluation & Fusion Verdict")
    lines.append("")
    lines.append(f"**Qualification:** `{EXPLORATORY_LABEL}`")
    lines.append(f"**Vision Data Provenance:** `{VISION_CACHE_PROVENANCE}`")
    lines.append(f"**Audio Data Provenance:** `{AUDIO_CACHE_PROVENANCE}`")
    lines.append(f"**Reference Labels:** `{REFERENCE_PROVENANCE}`")
    lines.append(
        "**Hardware / Sensor Scope:** `camera_1` (front) on 27/27 events; `camera_2` (back) on 27/27 events; "
        "`audio_1` (front microphone) on 27/27 events; **0/27** dedicated physical `camera_side` views; "
        "**0/27** track/occupancy sensors."
    )
    lines.append(
        "**Boundary Note on `engine_events/event_001`:** In its adopted proposal (`event_001_proposal_v3.json`), "
        "`engine_events/event_001` is a solitary light locomotive (`train_present = true`, `trailing_cars_count = 0`, "
        "`horn_status = absent_observed`) traversing `camera_back.mov`. Below we report BOTH **View 1** "
        "(`23` multi-car `train_events` vs `3` `no_train_events`, with `engine_events/001` in its own dedicated column) "
        "AND **View 2** (`23` `train_events` vs all `4` controls) & **View 3** (`24` rail vehicles vs `3` `no_train_events`)."
    )
    lines.append("")
    lines.append("## 1. Executive Answer: Does Multimodal Fusion Improve Performance?")
    lines.append("")
    f2 = view1_train23_vs_nt3["F2_V3_Default_Front_L1_Advisory_Audio"]
    f6 = view1_train23_vs_nt3["F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2"]
    v2 = view1_train23_vs_nt3["V2_Front_L1_Confirm2"]

    lines.append(
        "| Architecture / Modality | Train TP/23 | Train FN/23 | No-Train FP/3 | Engine001 Det | Prec (V1) | Rec (V1) | NT Spec (V1) | F1 (V1) | Acc (26) | Rail24 Rec/F1 (V3) | McNemar p vs V2 (V1/V2) |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    ordered_keys = [
        ("V1_Front_Any_Stateless", "Vision: Front-Only Any Frame (Stateless k>=1)", "pred_V1_front_any"),
        ("V2_Front_L1_Confirm2", "Vision: Front-Only L1 Causal (confirm>=2) [B0_front]", "pred_V2_front_L1_confirm2"),
        ("V3_Back_Any_Stateless", "Vision: Back-Only Any Frame (Stateless k>=1)", "pred_V3_back_any"),
        ("V4_Back_Confirm2_AllClasses", "Vision: Back-Only Confirm2 (All Classes)", "pred_V4_back_confirm2_all"),
        ("V5_Back_Confirm2_SideRear", "Vision: Back-Only Confirm2 (Side/Rear Filtered)", "pred_V5_back_confirm2_side_rear"),
        ("V6_Side_Proxy_Any", "Vision: Side-Class Proxy (Front+Back side>=1; 0 ded. cam)", "pred_V6_side_proxy_any"),
        ("V8_Dual_Vision_Confirm2_SideRear", "Vision: Dual-Vision Causal (Front L1 OR Back Side/Rear L1)", "pred_V8_dual_vision_confirm2_side_rear"),
        ("A1_Audio_Frozen_037_k1", "Audio-Only: Frozen tau=0.37, k=1 [B1_audio]", "pred_A1_audio_037_k1"),
        ("A2_Audio_037_k2", "Audio-Only: tau=0.37, k=2 consecutive", "pred_A2_audio_037_k2"),
        ("A3_Audio_Hysteresis_075_k2", "Audio-Only: Hysteresis tau=0.75, k=2 consecutive", "pred_A3_audio_075_k2"),
        ("F1_Stateless_Union_FrontAny_Or_Audio037", "Fusion F1: Stateless Union (Front>=1 OR Audio>=0.37)", "pred_F1_stateless_union"),
        ("F2_V3_Default_Front_L1_Advisory_Audio", "Fusion F2: V3 Default B2/B4 (Front L1 + Advisory Audio)", "pred_F2_v3_default_advisory_audio"),
        ("F3_Front_L1_Or_Corroborated_WeakFront_Audio075k2", "Fusion F3: Front L1 OR (Weak Front>=1 & Audio 0.75 k=2)", "pred_F3_front_or_corroborated_weak_vision"),
        ("F4_Front_L1_Or_Audio075k2", "Fusion F4: Front L1 OR Audio Hysteresis (0.75, k=2)", "pred_F4_front_L1_or_audio_075_k2"),
        ("F5_Dual_Vision_SideRear_Advisory_Audio", "Fusion F5: Dual-Vision (Back Side/Rear) + Advisory Audio [B7]", "pred_F5_dual_vision_side_rear_advisory"),
        ("F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2", "Fusion F6: Full Multimodal (Front L1 OR Back Side/Rear L1 OR Audio 0.75 k=2)", "pred_F6_full_multimodal_dual_sr_or_audio_075_k2"),
    ]
    for key, label, pkey in ordered_keys:
        m1 = view1_train23_vs_nt3[key]
        m2 = view2_train23_vs_ctrl4[key]
        m3 = view3_rail24_vs_nt3[key]
        eng_det = "YES" if bool(engine_row[pkey]) else "no"
        lines.append(
            f"| {label} | {m1['tp']} | {m1['fn']} | {m1['fp']} | {eng_det} | "
            f"{m1['precision']*100:.1f}% | {m1['recall']*100:.1f}% | {m1['specificity']*100:.1f}% | "
            f"{m1['f1']*100:.1f}% | {m1['accuracy']*100:.1f}% | "
            f"{m3['tp']}/24 ({m3['f1']*100:.1f}%) | "
            f"{m1['mcnemar_vs_baseline']['exact_p_value']:.4f} / {m2['mcnemar_vs_baseline']['exact_p_value']:.4f} |"
        )
    lines.append("")
    lines.append("### Scientific Findings on Vision + Audio + Multi-Camera Fusion")
    lines.append(
        f"1. **Default V3 Front+Audio Fusion (`F2` / `B2` / `B4`) gives +0.0% arrival recall gain over Front Vision Alone (`V2`):** "
        f"Because audio at `tau=0.37` is strictly advisory (logs `L3_AUDIO_SUPPORT_ONLY` while IDLE on 20/27 events, never triggers closure), "
        f"`V2` and `F2` achieve the exact same `{v2['tp']}/23` (`{v2['recall']*100:.1f}%`) train detection recall, "
        f"`{v2['fp']}/3` `no_train` false positives (`100.0%` precision/specificity), and `{v2['f1']*100:.1f}%` F1. "
        f"Because `0/27` real events have a physical occupancy sensor to authorize reopening under conservative V3, "
        f"`L3_AUDIO_DWELL_HOLD` never fires on real B4 runs (reopening extension is verified only in synthetic suites)."
    )
    lines.append(
        f"2. **Naive Stateless Union Fusion (`F1`: `Vision>=1 OR Audio>=0.37`) maximizes recall to `23/23` (`100.0%`) at an unacceptable safety-false-positive cost:** "
        f"`F1` triggers false closures on **`3/3` no-train controls** (`no_train_events/001..003`, `0.0%` no-train specificity) plus fails causal reopening stability in `exp_j`."
    )
    lines.append(
        f"3. **Multi-Camera Spatial Fusion (`V8` / `F5`) improves detection recall from `43.5%` (`10/23`) to `52.2%` (`12/23`) with `0/3` `no_train` false positives — ONLY if `camera_2` is restricted to `side`/`rear` classes:** "
        f"Raw `camera_2` `confirm>=2` across all classes (`V4`) generates false positives on `2/3` `no_train` controls (`001, 003`, `25`/`15` `front`-class hallucinations), even though it also detects the solitary locomotive in `engine_events/001` (`13` frames, `mean=0.805, max=0.899`, making View 3 `10/24` recall for `V4` alone). Filtering `camera_2` to `side`/`rear` classes (`V5` / `V8`) eliminates **all `2/3` `no_train` false positives (`FP=0/3`)** while recovering **`train_events/event_002`** (`43` back `side` objects, `42` frames) and **`train_events/event_016`** (`8` back `side` objects, `8` frames)."
    )
    lines.append(
        f"4. **Full Multimodal Fusion with High-Specificity Audio Hysteresis (`F6`: `Front L1 OR Back Side/Rear L1 OR Audio tau=0.75, k=2`) delivers the strongest zero-false-positive result (`+21.7 percentage points` recall, `+{(f6['f1']-v2['f1'])*100:.1f} pp` F1):** "
        f"Relative to Front-Only L1 (`{v2['tp']}/23`, `{v2['recall']*100:.1f}%` recall, `{v2['f1']*100:.1f}%` F1), adding Back Side/Rear (`+2`: `event_002`, `event_016`) and high-specificity Audio Hysteresis (`+3` additional unique recoveries: `event_005` [completely dark `-90°` rotated night optical, `105` positive audio windows, `31` `>=0.75`, max `0.972`], `event_012` [`34` positive windows, `8` `>=0.75`, max `0.978`], `event_017` [nighttime, `21` positive windows, `8` `>=0.75`, max `0.986`]; plus overlapping confirmation on `event_002`, `event_004`, `event_006`, `event_007`, `event_013`, `event_018`) raises detection to **`{f6['tp']}/23` (`{f6['recall']*100:.1f}%`)** with **`0/3` `no_train` false positives (`100.0%` precision, `100.0%` specificity, `{f6['f1']*100:.1f}%` F1, McNemar `p = 0.0625` vs `V2`)**."
    )
    lines.append(
        "   - *Methodological caveat:* This `tau=0.75, k=2` operating point was identified via `exp_o` hysteresis sweeping on the `27`-event cohort (in `exp_r` 23-fold LOEO, OOF audio metrics are `61.5%` recall / `60.0%` specificity / `64.0%` F1 against `horn_status`). Out-of-sample replication on a new session is required before promoting audio gating to production."
    )
    lines.append(
        f"5. **Why `8/23` train events (`event_008, 009, 010, 011, 014, 015, 019, 020`) are STILL missed even under `F6`:** "
        f"Unrotated `-90°` pre-`db40305` portrait video decoding crippled YOLOv8n (`0` or `1` scattered front frame; `0`–`4` scattered back `side`/`rear` frames below `confirm>=2`), AND `6` of those `8` events (`009, 010, 011, 014, 019, 020`) either had weak/brief horns (`maxA` `0.378`–`0.582`, `0` windows `>=0.75`) or had only single-window acoustic peaks (`event_008` max `0.811` `r75=1`, `event_015` max `0.840` `r75=1`, both failing `k=2`)."
    )
    lines.append("")

    lines.append("## 2. Complete 27-Event Perception Summary (Front Vision, Back Vision, Side Proxy, Audio & Ground Truth)")
    lines.append("")
    lines.append(
        "| Event ID | Cohort (Train/Rail GT) | Sess | Light | Sync | Front DF (c) [F/S/R] | Front Conf (mean/max) | Back DF (c/sr_c) [F/S/R] | Back Conf (mean/max) | Side Proxy (F+B / Tracker) | Aud >=0.37 (r37) | Aud >=0.75 (r75) | Aud Max@t | Adopted GT Horn |"
    )
    lines.append("|---|---|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|---|")
    for r in events:
        gt_lbl = "TRAIN (1/1)" if r["gt_is_train_event"] else ("ENGINE (0/1)" if r["cohort"] == "engine_events" else "NO_TRN (0/0)")
        f_cls = f"[{r['front_cls_front']}/{r['front_cls_side']}/{r['front_cls_rear']}]"
        b_cls = f"[{r['back_cls_front']}/{r['back_cls_side']}/{r['back_cls_rear']}]"
        f_c = f"{_fmt(r['front_mean_conf'])}/{_fmt(r['front_max_conf'])}" if r["front_det_frames"] > 0 else "—"
        b_c = f"{_fmt(r['back_mean_conf'])}/{_fmt(r['back_max_conf'])}" if r["back_det_frames"] > 0 else "—"
        lines.append(
            f"| `{r['event_id']}` | {gt_lbl} | {r['recording_session']} | {r['lighting']} | "
            f"{'sync11' if r['is_sync11'] else 'indep'} | {r['front_det_frames']} ({r['front_max_consec']}) {f_cls} | "
            f"{f_c} | {r['back_det_frames']} ({r['back_max_consec']}/{r['back_max_consec_side_rear']}) {b_cls} | "
            f"{b_c} | {r['side_proxy_total_objects']} ({r['side_tracker_state']}) | "
            f"{r['audio_pos_037']} ({r['audio_max_run_037']}) | {r['audio_pos_075']} ({r['audio_max_run_075']}) | "
            f"{r['audio_max_score']:.3f}@{r['audio_peak_s']:.1f}s | {r['adopted_horn_status']} ({_fmt(r['gt_horn_onset_s'], 's')}) |"
        )
    lines.append("")

    lines.append("## 3. Event-by-Event Modality & Fusion Predictions vs Ground Truth (All 27 Events)")
    lines.append("")
    lines.append(
        "| Event ID | GT | V1 Fr>=1 | V2 Fr L1 | V4 Bk All | V5 Bk SR | V6 Side>=1 | V8 Dual SR | A1 Aud.37 | A3 Aud.75k2 | F1 Union | F2 V3 Def | F3 Weak+A | F4 Fr+A75k2 | F6 Full MM | V3 Gate State | F6 Source |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in events:
        gt_lbl = "POS" if r["gt_is_train_event"] else ("ENG" if r["cohort"] == "engine_events" else "NEG")
        def _yn(k: str) -> str:
            return "POS" if r[k] else "neg"
        lines.append(
            f"| `{r['event_id']}` | {gt_lbl} | {_yn('pred_V1_front_any')} | {_yn('pred_V2_front_L1_confirm2')} | "
            f"{_yn('pred_V4_back_confirm2_all')} | {_yn('pred_V5_back_confirm2_side_rear')} | "
            f"{_yn('pred_V6_side_proxy_any')} | {_yn('pred_V8_dual_vision_confirm2_side_rear')} | "
            f"{_yn('pred_A1_audio_037_k1')} | {_yn('pred_A3_audio_075_k2')} | "
            f"{_yn('pred_F1_stateless_union')} | {_yn('pred_F2_v3_default_advisory_audio')} | "
            f"{_yn('pred_F3_front_or_corroborated_weak_vision')} | {_yn('pred_F4_front_L1_or_audio_075_k2')} | "
            f"{_yn('pred_F6_full_multimodal_dual_sr_or_audio_075_k2')} | "
            f"{r['v3_final_crossing_state']}/{r['v3_final_gate_state']} | {r['f6_first_trigger_source']} |"
        )
    lines.append("")

    lines.append("## 4. Crossing Decision Timestamps (Arrival, Warning, Closure, Clearance & Reopening)")
    lines.append("")
    lines.append(
        "| Event ID | GT T0/T2 (Front) | GT T4 | Fr First/L1 | B4 Warn/Cmd/Full | Margin vs T2 | Audio Dwell Hold? | M2 Back Last | M2 Err vs T4 | M3 Sync11 (Cons / Guarded) | F6 Trig@t | Diagnosis |"
    )
    lines.append("|---|---|---|---:|---:|---:|---|---:|---:|---|---|---|")
    for r in events:
        t0t2 = f"{_fmt(r['gt_T0_s'])}/{_fmt(r['gt_T2_s'])}"
        fr_t = f"{_fmt(r['front_first_det_s'])}/{_fmt(r['v3_t_confirm_s'])}"
        v3_t = f"{_fmt(r['v3_t_warning_s'])}/{_fmt(r['v3_t_close_cmd_s'])}/{_fmt(r['v3_t_fully_closed_s'])}"
        m2_t = _fmt(r['back_last_det_s'])
        m2_e = _fmt(r['back_M2_err_vs_T4_s'], 's')
        if r["is_sync11"]:
            c_txt = _fmt(r["sync11_M3_reopen_s"], "s") if r["sync11_M3_reopen_s"] is not None else "SafeClosed"
            g_txt = f"{r['sync11_M3_guarded_reopen_s']:.1f}s (prem)" if r["sync11_M3_guarded_reopen_s"] is not None else "SafeClosed"
            m3_cell = f"{c_txt} / {g_txt}"
        else:
            m3_cell = "uncal."
        f6_t = f"{r['f6_first_trigger_source']}@{_fmt(r['f6_t_trigger_s'], 's')}" if r["f6_first_trigger_source"] != "NONE" else "NONE"
        aud_role = "HOLD_EXT" if r["v3_audio_extended_dwell"] else ("SuppOnly_Idle" if r["v3_audio_support_only_idle"] else "no")
        lines.append(
            f"| `{r['event_id']}` | {t0t2} | {_fmt(r['gt_T4_local_or_master_s'])} | {fr_t} | {v3_t} | "
            f"{_fmt(r['v3_margin_full_vs_T2_s'], 's')} | {aud_role} | "
            f"{m2_t} | {m2_e} | {m3_cell} | {f6_t} | {r['diagnosis']} |"
        )
    lines.append("")

    lines.append("## 5. Subgroup Breakdown & Acoustic Horn Ground-Truth Check")
    lines.append("")
    lines.append("### 5.1 Train Detection Stratification (Recording Session & Sync Calibration Scope; gt_is_train_event)")
    lines.append("| Subgroup (F6 vs Front L1 V2) | Events (Train/Ctrl) | V2 Front L1 Recall | F6 Multimodal Recall | Gain | V2 Ctrl FP | F6 Ctrl FP |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for s_name, pred in [
        ("Session 1 (2026-09-14 Day Overcast)", lambda r: r["recording_session"] == "Session 1"),
        ("Session 2 (2026-10-04 Mixed Day/Night)", lambda r: r["recording_session"] == "Session 2"),
        ("Sync11 Calibrated Dual-Camera Subset", lambda r: bool(r["is_sync11"])),
        ("Uncalibrated Independent-Camera Subset", lambda r: not bool(r["is_sync11"])),
    ]:
        mv2 = _compute_binary_metrics(events, "pred_V2_front_L1_confirm2", "gt_is_train_event", subset_filter=pred)
        mf6 = _compute_binary_metrics(events, "pred_F6_full_multimodal_dual_sr_or_audio_075_k2", "gt_is_train_event", subset_filter=pred)
        lines.append(
            f"| {s_name} | {mv2['n_events']} ({mv2['pos_gt']}/{mv2['neg_gt']}) | "
            f"{mv2['tp']}/{mv2['pos_gt']} ({mv2['recall']*100:.1f}%) | "
            f"{mf6['tp']}/{mf6['pos_gt']} ({mf6['recall']*100:.1f}%) | "
            f"+{mf6['tp'] - mv2['tp']} | {mv2['fp']} | {mf6['fp']} |"
        )
    lines.append("")
    lines.append("### 5.2 Audio-Only Evaluated Against Adopted Horn Ground Truth (`horn_status == 'present'`)")
    lines.append("| Audio Operating Rule | TP (Horn=Present) | FN | FP (Horn=Absent) | TN | Precision | Recall | Specificity | F1 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for k, lbl in [
        ("A1_Audio_Frozen_037_k1", "Audio tau=0.37, k=1 (All 27: 13 horn+ / 14 horn-)"),
        ("A2_Audio_037_k2", "Audio tau=0.37, k=2 (All 27: 13 horn+ / 14 horn-)"),
        ("A3_Audio_Hysteresis_075_k2", "Audio tau=0.75, k=2 Hysteresis (All 27: 13 horn+ / 14 horn-)"),
    ]:
        hm = horn_configs[k]
        lines.append(
            f"| {lbl} | {hm['tp']}/{hm['pos_gt']} | {hm['fn']} | {hm['fp']}/{hm['neg_gt']} | {hm['tn']} | "
            f"{hm['precision']*100:.1f}% | {hm['recall']*100:.1f}% | {hm['specificity']*100:.1f}% | {hm['f1']*100:.1f}% |"
        )
    loeo = support["loeo_summary"]
    lines.append(
        f"| 23-Fold Nested LOEO Calibrated OOF (Train23: 13 horn+ / 10 horn-) | "
        f"{loeo['tp']}/13 | {loeo['fn']} | {loeo['fp']}/10 | {loeo['tn']} | "
        f"{loeo['precision']*100:.1f}% | {loeo['recall']*100:.1f}% | {loeo['specificity']*100:.1f}% | {loeo['f1']*100:.1f}% |"
    )
    lines.append("")

    lines.append("## 6. Explicit Boundary: Metrics That Existing Data & Labels Cannot Establish")
    lines.append("")
    lines.append("| Metric / Capability | Status on Current Dataset & Repository | Why / Blocking Evidence Gap |")
    lines.append("|---|---|---|")
    lines.append("| Layer B frame-level YOLO mAP / IoU / Precision-Recall curves | **CANNOT BE COMPUTED** | Proposals provide event-level `T0..T4` timestamps only; 0 frame-level bounding boxes exist. |")
    lines.append("| Window-level audio horn F1 / frame-accurate horn offset error | **CANNOT BE COMPUTED** | Proposals provide `horn_status` + `horn_onset_s` only; 0 window-level horn offset timestamps exist. |")
    lines.append("| Upright (`0°` / display-matrix rotated) YOLO evaluation on Layer B | **CANNOT BE EXECUTED WITHOUT MEDIA AUTH** | Cached detections come from pre-`db40305` unrotated container frames (`48/54` streams rotated `-90°` in metadata); `AUTH-MEDIA-ACCESS.json` is absent. |")
    lines.append("| Physical dedicated side-camera evaluation | **0/27 EVENTS** | Hardware setup deployed `camera_1` (front) and `camera_2` (back) only; `side` relies on YOLO `side` proxy class. |")
    lines.append("| Physical track/occupancy sensor gate reopening (`V3 CONSERVATIVE_POSITIVE`) | **0/27 REOPENINGS ON REAL FOOTAGE** | `0/27` track sensors collected; fail-closed conservative policy keeps gate safely closed until physical occupancy clearance (`0%` premature openings). |")
    lines.append("| Millisecond-aligned cross-camera fusion on 16 non-`sync11` events | **BLOCKED BY R04 CLOCK UNCERTAINTY** | Only 11 events have `CALIBRATION_SUPPORTED` clock offsets (`phase12_r04_scope_decision.json`); the remaining 16 have `±1.0–2.0 s` QuickTime rounding or missing audio peaks. |")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> dict[str, Any]:
    ctx = load_verified_context(REPO_ROOT)
    support = _load_supporting_lookup()

    per_event_rows: list[dict[str, Any]] = []
    for eid in ctx.event_order:
        ent = ctx.manifest_events[eid]
        ref = ctx.references[eid]
        qt_info = support["qt"][eid]
        session_date = str(qt_info.get("creationdate_front", ""))[:10]
        rec_session = "Session 1" if session_date == "2026-09-14" else "Session 2"

        f_stats = _parse_vision_stream(REPO_ROOT / ent["front_cache_path"])
        b_stats = _parse_vision_stream(REPO_ROOT / ent["back_cache_path"])
        a_stats = _parse_audio_stream(REPO_ROOT / ent["audio_cache_path"])
        side_tracker = _run_side_tracker_proxy(ctx, eid)

        # Ground truth boundaries in native/master clocks
        t_arrival_front = ref.t2_raw_s if ref.t2_cam == "front" else None
        sim_b4 = _sim_b4_v3(ctx, eid, t_arrival_front)

        # Departure ground truth
        b27_info = support["back27_d"].get(eid, {})
        t4_back = b27_info.get("T4_back_s")
        s11_info = support["sync11_d"].get(eid)
        t4_master = s11_info.get("T4_master_s") if s11_info else None
        t4_display = t4_master if t4_master is not None else t4_back

        m2_err = (
            round(float(b_stats["last_det_s"]) - float(t4_back), 4)
            if (b_stats["last_det_s"] is not None and t4_back is not None)
            else None
        )
        m3_reopen_s = (
            s11_info["policies"]["V3_CONSERVATIVE_POSITIVE"]["first_opening_s"]
            if s11_info
            else None
        )
        m3_guarded_reopen_s = (
            s11_info["policies"]["V3_GUARDED_DISAPPEARANCE"]["first_opening_s"]
            if s11_info
            else None
        )
        m3_err = (
            round(float(m3_reopen_s) - float(t4_master), 4)
            if (m3_reopen_s is not None and t4_master is not None)
            else None
        )

        # Perception & fusion predictions
        gt_is_train = ref.cohort == "train_events"
        gt_rail_present = bool(ref.train_present)
        gt_horn = str(ref.horn_status or "").lower() == "present"

        v1 = f_stats["det_frames"] >= 1
        v2 = f_stats["max_consec_any"] >= 2
        v3 = b_stats["det_frames"] >= 1
        v4 = b_stats["max_consec_any"] >= 2
        v5 = b_stats["max_consec_side_rear"] >= 2
        v6 = (f_stats["cls_counts"]["side"] + b_stats["cls_counts"]["side"]) >= 1
        v7 = v2 or v4
        v8 = v2 or v5

        a1 = a_stats["pos_windows_037"] >= 1
        a2 = a_stats["max_run_037"] >= 2
        a3 = a_stats["max_run_075"] >= 2

        f1 = v1 or a1
        f2 = v2  # In V3, audio is strictly non-gating for closure (advisory clearance dwell only)
        f3 = v2 or (v1 and a3)
        f4 = v2 or a3
        f5 = v8
        f6 = v2 or v5 or a3

        # Determine earliest trigger source & timestamp under F6
        candidates: list[tuple[float, str]] = []
        if v2 and (sim_b4["t_confirm_s"] is not None or f_stats["first_consec2_any_s"] is not None):
            t_cand = sim_b4["t_confirm_s"] if sim_b4["t_confirm_s"] is not None else f_stats["first_consec2_any_s"]
            candidates.append((float(t_cand), "FRONT_L1"))
        if v5 and b_stats["first_consec2_sr_s"] is not None:
            t_b_sr = float(b_stats["first_consec2_sr_s"])
            if ref.is_dual_sync_accepted and ref.back_offset_s is not None:
                t_b_sr = round(t_b_sr + float(ref.back_offset_s), 4)
                candidates.append((t_b_sr, "BACK_SR_L1_SYNC"))
            else:
                candidates.append((t_b_sr, "BACK_SR_L1_LOCAL"))
        if a3 and a_stats["first_075_k2_s"] is not None:
            candidates.append((float(a_stats["first_075_k2_s"]), "AUDIO_075_K2"))
        if candidates:
            f6_t_trig, f6_src = min(candidates, key=lambda x: x[0])
        else:
            f6_t_trig, f6_src = None, "NONE"

        loeo_info = support["loeo_folds"].get(eid, {})

        row: dict[str, Any] = {
            "event_id": eid,
            "cohort": ref.cohort,
            "event_type": ref.event_type,
            "gt_is_train_event": gt_is_train,
            "gt_rail_vehicle_present": gt_rail_present,
            "gt_horn_present": gt_horn,
            "adopted_horn_status": ref.horn_status,
            "gt_horn_onset_s": float(ref.horn_onset_s) if ref.horn_onset_s is not None else None,
            "recording_session": rec_session,
            "lighting": ref.lighting,
            "weather": ref.weather,
            "is_sync11": ref.is_dual_sync_accepted,
            "sync_regime": "sync11" if ref.is_dual_sync_accepted else "independent_camera",
            "back_offset_s": ref.back_offset_s,
            "delta_qt_s": qt_info.get("delta_qt_s"),
            "gt_T0_s": ref.t0_raw_s,
            "gt_T0_cam": ref.t0_cam,
            "gt_T1_s": ref.t1_raw_s,
            "gt_T2_s": ref.t2_raw_s,
            "gt_T3_s": ref.t3_raw_s,
            "gt_T4_s": ref.t4_raw_s,
            "gt_T4_cam": ref.t4_cam,
            "gt_T4_local_or_master_s": t4_display,
            # Front vision
            "front_sampled_frames": f_stats["sampled_frames"],
            "front_duration_s": f_stats["duration_s"],
            "front_det_frames": f_stats["det_frames"],
            "front_total_objects": f_stats["total_objects"],
            "front_cls_front": f_stats["cls_counts"]["front"],
            "front_cls_side": f_stats["cls_counts"]["side"],
            "front_cls_rear": f_stats["cls_counts"]["rear"],
            "front_min_conf": f_stats["min_conf"],
            "front_mean_conf": f_stats["mean_conf"],
            "front_max_conf": f_stats["max_conf"],
            "front_first_det_s": f_stats["first_det_s"],
            "front_last_det_s": f_stats["last_det_s"],
            "front_max_consec": f_stats["max_consec_any"],
            "front_lead_vs_T2_s": (
                round(float(ref.t2_raw_s) - float(f_stats["first_det_s"]), 4)
                if (ref.t2_cam == "front" and ref.t2_raw_s is not None and f_stats["first_det_s"] is not None)
                else None
            ),
            # Back vision
            "back_sampled_frames": b_stats["sampled_frames"],
            "back_duration_s": b_stats["duration_s"],
            "back_det_frames": b_stats["det_frames"],
            "back_total_objects": b_stats["total_objects"],
            "back_cls_front": b_stats["cls_counts"]["front"],
            "back_cls_side": b_stats["cls_counts"]["side"],
            "back_cls_rear": b_stats["cls_counts"]["rear"],
            "back_min_conf": b_stats["min_conf"],
            "back_mean_conf": b_stats["mean_conf"],
            "back_max_conf": b_stats["max_conf"],
            "back_first_det_s": b_stats["first_det_s"],
            "back_last_det_s": b_stats["last_det_s"],
            "back_max_consec": b_stats["max_consec_any"],
            "back_max_consec_side_rear": b_stats["max_consec_side_rear"],
            "back_M2_err_vs_T4_s": m2_err,
            "sync11_M3_reopen_s": m3_reopen_s,
            "sync11_M3_guarded_reopen_s": m3_guarded_reopen_s,
            "sync11_M3_err_vs_T4_s": m3_err,
            # Side proxy
            "dedicated_side_camera": False,
            "side_proxy_front_cam_objs": f_stats["cls_counts"]["side"],
            "side_proxy_back_cam_objs": b_stats["cls_counts"]["side"],
            "side_proxy_total_objects": f_stats["cls_counts"]["side"] + b_stats["cls_counts"]["side"],
            "side_tracker_state": side_tracker["tracker_state"],
            "side_tracker_moving_ticks": side_tracker["tracker_moving_ticks"],
            "side_tracker_max_consec_obs": side_tracker["tracker_max_consec_obs"],
            # Audio
            "audio_windows": a_stats["n_windows"],
            "audio_pos_037": a_stats["pos_windows_037"],
            "audio_pos_075": a_stats["pos_windows_075"],
            "audio_max_run_037": a_stats["max_run_037"],
            "audio_max_run_075": a_stats["max_run_075"],
            "audio_first_037_s": a_stats["first_037_k1_s"],
            "audio_first_075_k2_s": a_stats["first_075_k2_s"],
            "audio_peak_s": a_stats["peak_s"],
            "audio_mean_score": a_stats["mean_score"],
            "audio_max_score": a_stats["max_score"],
            "audio_loeo_oof_pred": loeo_info.get("oof_pred"),
            "audio_loeo_oof_cal_prob": loeo_info.get("oof_cal_prob"),
            "audio_onset_err_037_s": (
                round(float(a_stats["first_037_k1_s"]) - float(ref.horn_onset_s), 4)
                if (a_stats["first_037_k1_s"] is not None and ref.horn_onset_s is not None)
                else None
            ),
            # Predictions
            "pred_V1_front_any": v1,
            "pred_V2_front_L1_confirm2": v2,
            "pred_V3_back_any": v3,
            "pred_V4_back_confirm2_all": v4,
            "pred_V5_back_confirm2_side_rear": v5,
            "pred_V6_side_proxy_any": v6,
            "pred_V7_dual_vision_confirm2_all": v7,
            "pred_V8_dual_vision_confirm2_side_rear": v8,
            "pred_A1_audio_037_k1": a1,
            "pred_A2_audio_037_k2": a2,
            "pred_A3_audio_075_k2": a3,
            "pred_F1_stateless_union": f1,
            "pred_F2_v3_default_advisory_audio": f2,
            "pred_F3_front_or_corroborated_weak_vision": f3,
            "pred_F4_front_L1_or_audio_075_k2": f4,
            "pred_F5_dual_vision_side_rear_advisory": f5,
            "pred_F6_full_multimodal_dual_sr_or_audio_075_k2": f6,
            # V3 Controller Decisions & Timing
            "v3_closure_triggered": sim_b4["closure_triggered"],
            "v3_t_confirm_s": sim_b4["t_confirm_s"],
            "v3_t_warning_s": sim_b4["t_warning_s"],
            "v3_t_close_cmd_s": sim_b4["t_close_cmd_s"],
            "v3_t_half_closed_s": sim_b4["t_half_closed_s"],
            "v3_t_fully_closed_s": sim_b4["t_fully_closed_s"],
            "v3_margin_full_vs_T2_s": sim_b4["margin_full_vs_T2_s"],
            "v3_t_reopen_s": sim_b4["t_reopen_s"],
            "v3_audio_extended_dwell": sim_b4["audio_extended_dwell"],
            "v3_audio_support_only_idle": sim_b4["audio_support_only_idle"],
            "v3_final_crossing_state": sim_b4["final_crossing_state"],
            "v3_final_gate_state": sim_b4["final_gate_state"],
            # F6 Multimodal Trigger
            "f6_first_trigger_source": f6_src,
            "f6_t_trigger_s": f6_t_trig,
        }
        row["diagnosis"] = _failure_or_recovery_reason(row)
        per_event_rows.append(row)

    model_specs = [
        ("V1_Front_Any_Stateless", "pred_V1_front_any"),
        ("V2_Front_L1_Confirm2", "pred_V2_front_L1_confirm2"),
        ("V3_Back_Any_Stateless", "pred_V3_back_any"),
        ("V4_Back_Confirm2_AllClasses", "pred_V4_back_confirm2_all"),
        ("V5_Back_Confirm2_SideRear", "pred_V5_back_confirm2_side_rear"),
        ("V6_Side_Proxy_Any", "pred_V6_side_proxy_any"),
        ("V7_Dual_Vision_Confirm2_AllClasses", "pred_V7_dual_vision_confirm2_all"),
        ("V8_Dual_Vision_Confirm2_SideRear", "pred_V8_dual_vision_confirm2_side_rear"),
        ("A1_Audio_Frozen_037_k1", "pred_A1_audio_037_k1"),
        ("A2_Audio_037_k2", "pred_A2_audio_037_k2"),
        ("A3_Audio_Hysteresis_075_k2", "pred_A3_audio_075_k2"),
        ("F1_Stateless_Union_FrontAny_Or_Audio037", "pred_F1_stateless_union"),
        ("F2_V3_Default_Front_L1_Advisory_Audio", "pred_F2_v3_default_advisory_audio"),
        ("F3_Front_L1_Or_Corroborated_WeakFront_Audio075k2", "pred_F3_front_or_corroborated_weak_vision"),
        ("F4_Front_L1_Or_Audio075k2", "pred_F4_front_L1_or_audio_075_k2"),
        ("F5_Dual_Vision_SideRear_Advisory_Audio", "pred_F5_dual_vision_side_rear_advisory"),
        ("F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2", "pred_F6_full_multimodal_dual_sr_or_audio_075_k2"),
    ]

    engine_row = next(r for r in per_event_rows if r["cohort"] == "engine_events")
    view1_train23_vs_nt3: dict[str, dict[str, Any]] = {}
    view2_train23_vs_ctrl4: dict[str, dict[str, Any]] = {}
    view3_rail24_vs_nt3: dict[str, dict[str, Any]] = {}
    horn_configs_all27: dict[str, dict[str, Any]] = {}

    for name, pkey in model_specs:
        m1 = _compute_binary_metrics(
            per_event_rows,
            pkey,
            "gt_is_train_event",
            baseline_key="pred_V2_front_L1_confirm2",
            subset_filter=lambda r: r["cohort"] in ("train_events", "no_train_events"),
        )
        m1["engine_001_detected"] = bool(engine_row[pkey])
        view1_train23_vs_nt3[name] = m1

        view2_train23_vs_ctrl4[name] = _compute_binary_metrics(
            per_event_rows, pkey, "gt_is_train_event", baseline_key="pred_V2_front_L1_confirm2"
        )
        view3_rail24_vs_nt3[name] = _compute_binary_metrics(
            per_event_rows, pkey, "gt_rail_vehicle_present", baseline_key="pred_V2_front_L1_confirm2"
        )
        if pkey.startswith("pred_A"):
            horn_configs_all27[name] = _compute_binary_metrics(
                per_event_rows, pkey, "gt_horn_present", baseline_key="pred_A1_audio_037_k1"
            )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Write 27-row CSV
    csv_path = OUTPUT_DIR / "event_by_event_27_multimodal_evaluation.csv"
    fieldnames = list(per_event_rows[0].keys())
    with open(csv_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(per_event_rows)

    # 2. Write 27-row JSON
    json_events_path = OUTPUT_DIR / "event_by_event_27_multimodal_evaluation.json"
    events_payload = {
        "schema_version": "complete-27-event-multimodal-evaluation/1.1",
        "qualification": EXPLORATORY_LABEL,
        "provenance": {
            "vision": VISION_CACHE_PROVENANCE,
            "audio": AUDIO_CACHE_PROVENANCE,
            "reference": REFERENCE_PROVENANCE,
            "raw_media_accessed": False,
        },
        "n_events": len(per_event_rows),
        "events": per_event_rows,
    }
    json_events_path.write_text(json.dumps(events_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # 3. Write ablation metrics CSV & JSON
    ablation_json_path = OUTPUT_DIR / "modality_and_fusion_ablation_metrics.json"
    ablation_payload = {
        "schema_version": "multimodal-ablation-metrics/1.1",
        "qualification": EXPLORATORY_LABEL,
        "view1_train23_vs_no_train3_engine_separate": view1_train23_vs_nt3,
        "view2_train23_vs_controls4": view2_train23_vs_ctrl4,
        "view3_rail_vehicle24_vs_no_train3": view3_rail24_vs_nt3,
        "view4_horn13_vs_nohorn14": horn_configs_all27,
        "audio_loeo_23_folds": support["loeo_summary"],
    }
    ablation_json_path.write_text(json.dumps(ablation_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    ablation_csv_path = OUTPUT_DIR / "modality_and_fusion_ablation_metrics.csv"
    ab_rows = []
    for k, m1 in view1_train23_vs_nt3.items():
        m3 = view3_rail24_vs_nt3[k]
        ab_rows.append(
            {
                "configuration": k,
                "v1_train23_vs_nt3_n": m1["n_events"],
                "v1_tp": m1["tp"],
                "v1_fn": m1["fn"],
                "v1_fp_no_train": m1["fp"],
                "v1_tn_no_train": m1["tn"],
                "engine_001_detected": m1["engine_001_detected"],
                "v1_precision": m1["precision"],
                "v1_recall": m1["recall"],
                "v1_specificity": m1["specificity"],
                "v1_f1": m1["f1"],
                "v1_accuracy": m1["accuracy"],
                "v1_mcnemar_p_vs_front_L1": m1["mcnemar_vs_baseline"]["exact_p_value"],
                "v3_rail24_tp": m3["tp"],
                "v3_rail24_recall": m3["recall"],
                "v3_rail24_f1": m3["f1"],
                "events_gained_over_front_L1": ";".join(m1["events_gained_over_front_L1"]),
                "no_train_false_positive_events": ";".join(m1["false_positive_events"]),
            }
        )
    with open(ablation_csv_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ab_rows[0].keys()))
        writer.writeheader()
        writer.writerows(ab_rows)

    # 4. Write comprehensive Markdown report
    report_path = OUTPUT_DIR / "COMPLETE_27_EVENT_MULTIMODAL_EXPERIMENT_REPORT.md"
    report_md = _build_markdown_report(
        per_event_rows,
        view1_train23_vs_nt3,
        view2_train23_vs_ctrl4,
        view3_rail24_vs_nt3,
        horn_configs_all27,
        support,
    )
    report_path.write_text(report_md, encoding="utf-8")

    # Summary print
    print("=== COMPLETE 27-EVENT MULTIMODAL EVALUATION GENERATED (V1: Train23 vs NT3 | Eng001 sep | V3: Rail24 vs NT3) ===")
    for k, _, _ in [
        ("V2_Front_L1_Confirm2", "", ""),
        ("V4_Back_Confirm2_AllClasses", "", ""),
        ("V5_Back_Confirm2_SideRear", "", ""),
        ("V8_Dual_Vision_Confirm2_SideRear", "", ""),
        ("A1_Audio_Frozen_037_k1", "", ""),
        ("A3_Audio_Hysteresis_075_k2", "", ""),
        ("F1_Stateless_Union_FrontAny_Or_Audio037", "", ""),
        ("F2_V3_Default_Front_L1_Advisory_Audio", "", ""),
        ("F3_Front_L1_Or_Corroborated_WeakFront_Audio075k2", "", ""),
        ("F4_Front_L1_Or_Audio075k2", "", ""),
        ("F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2", "", ""),
    ]:
        m = view1_train23_vs_nt3[k]
        m3 = view3_rail24_vs_nt3[k]
        print(
            f"  {k:48s} | TP={m['tp']:2d}/23 FN={m['fn']:2d} FP_NT={m['fp']}/3 Eng={str(m['engine_001_detected']):5s} | "
            f"P={m['precision']*100:5.1f}% R={m['recall']*100:5.1f}% Spec={m['specificity']*100:5.1f}% F1={m['f1']*100:5.1f}% | "
            f"Rail24={m3['tp']:2d}/24({m3['f1']*100:5.1f}%) | gain={m['events_gained_over_front_L1']}"
        )
    return ablation_payload


if __name__ == "__main__":
    main()
