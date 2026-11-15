"""Reusable calibration, hysteresis, edge-duty-cycle, and stress-testing utilities."""

from __future__ import annotations

import math
import random
from typing import Any

from railway_detection.fusion.collector import MultimodalEvidenceCollector
from railway_detection.fusion.decision_engine_v3_four_layer import (
    MultimodalDecisionEngineV3FourLayer,
)
from railway_detection.fusion.evidence import (
    Detection,
    EvidenceRecord,
    Modality,
    OccupancyEvidence,
    OccupancyState,
)
from railway_detection.simulation.runner import EventSimulationRunner
from railway_detection.simulation.state_machine import ALLOWED_TRANSITIONS, CrossingState


def _longest_consecutive_run(scores: list[float], threshold: float) -> int:
    best = 0
    cur = 0
    for s in scores:
        if s >= threshold:
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best


def _safe_div(num: float, den: float) -> float:
    return num / den if den > 0 else 0.0


def compute_binary_ece_and_brier(
    probs: list[float],
    labels: list[int],
    *,
    n_bins: int = 10,
) -> dict[str, Any]:
    """Compute binary Expected Calibration Error (ECE), MCE, and Brier score."""
    if len(probs) != len(labels) or not probs:
        raise ValueError("probs and labels must be non-empty and equal length")
    n = len(probs)
    brier = sum((p - y) ** 2 for p, y in zip(probs, labels, strict=True)) / n
    bins: list[dict[str, Any]] = []
    ece = 0.0
    mce = 0.0
    for b in range(n_bins):
        lo = b / n_bins
        hi = (b + 1) / n_bins
        idx = [
            i
            for i, p in enumerate(probs)
            if (p >= lo and p <= hi if b == n_bins - 1 else lo <= p < hi)
        ]
        if not idx:
            bins.append({"bin": b, "lo": round(lo, 2), "hi": round(hi, 2), "count": 0})
            continue
        mean_p = sum(probs[i] for i in idx) / len(idx)
        emp_acc = sum(labels[i] for i in idx) / len(idx)
        gap = abs(mean_p - emp_acc)
        ece += (len(idx) / n) * gap
        mce = max(mce, gap)
        bins.append(
            {
                "bin": b,
                "lo": round(lo, 2),
                "hi": round(hi, 2),
                "count": len(idx),
                "mean_prob": round(mean_p, 4),
                "empirical_rate": round(emp_acc, 4),
                "abs_gap": round(gap, 4),
            }
        )
    return {"n": n, "ece": round(ece, 4), "mce": round(mce, 4), "brier": round(brier, 4), "bins": bins}


def apply_temperature_scaling(probs: list[float], temperature: float) -> list[float]:
    """Apply logit temperature scaling p' = sigmoid(logit(p) / T) safely."""
    t = max(float(temperature), 1e-4)
    out: list[float] = []
    eps = 1e-6
    for p in probs:
        pc = min(max(float(p), eps), 1.0 - eps)
        logit = math.log(pc / (1.0 - pc))
        scaled = 1.0 / (1.0 + math.exp(-logit / t))
        out.append(scaled)
    return out


def evaluate_acoustic_hysteresis_and_calibration(
    event_records: list[dict[str, Any]],
    *,
    thresholds: tuple[float, ...] = (0.37, 0.50, 0.65, 0.75, 0.80, 0.85, 0.90, 0.95),
    k_values: tuple[int, ...] = (1, 2, 3, 4),
    temperatures: tuple[float, ...] = (0.5, 1.0, 1.5, 2.0, 3.0),
) -> dict[str, Any]:
    """Evaluate threshold + k-consecutive hysteresis Pareto tradeoffs and calibration.

    Expects each item in ``event_records`` to contain:
    ``event_id``, ``cohort`` (``train_events`` / ``no_train_events`` / ``engine_events``),
    ``binary_label`` (1 for horn present, 0 for horn absent; ``None`` if unlabeled),
    and ``scores`` (list[float]).
    """
    labeled_train = [r for r in event_records if r["cohort"] == "train_events" and r["binary_label"] in (0, 1)]
    no_train = [r for r in event_records if r["cohort"] == "no_train_events"]
    engine = [r for r in event_records if r["cohort"] == "engine_events"]

    grid_rows: list[dict[str, Any]] = []
    for tau in thresholds:
        for k in k_values:
            tp = fp = tn = fn = 0
            for r in labeled_train:
                pred = _longest_consecutive_run(r["scores"], tau) >= k
                y = r["binary_label"]
                if pred and y == 1:
                    tp += 1
                elif pred and y == 0:
                    fp += 1
                elif (not pred) and y == 0:
                    tn += 1
                else:
                    fn += 1
            nt_fp = sum(1 for r in no_train if _longest_consecutive_run(r["scores"], tau) >= k)
            eng_fp = sum(1 for r in engine if _longest_consecutive_run(r["scores"], tau) >= k)
            recall = _safe_div(tp, tp + fn)
            specificity = _safe_div(tn, tn + fp)
            precision = _safe_div(tp, tp + fp)
            f1 = _safe_div(2.0 * precision * recall, precision + recall)
            acc = _safe_div(tp + tn, tp + fp + tn + fn)
            grid_rows.append(
                {
                    "threshold": tau,
                    "k_consecutive": k,
                    "tp": tp,
                    "fp": fp,
                    "tn": tn,
                    "fn": fn,
                    "recall": round(recall, 4),
                    "specificity": round(specificity, 4),
                    "precision": round(precision, 4),
                    "f1": round(f1, 4),
                    "accuracy": round(acc, 4),
                    "no_train_fp": nt_fp,
                    "no_train_total": len(no_train),
                    "engine_fp": eng_fp,
                    "engine_total": len(engine),
                }
            )

    event_run_summaries = [
        {
            "event_id": r["event_id"],
            "cohort": r["cohort"],
            "binary_label": r["binary_label"],
            "n_windows": len(r["scores"]),
            "max_score": round(max(r["scores"]) if r["scores"] else 0.0, 6),
            "windows_ge_0_37": sum(1 for s in r["scores"] if s >= 0.37),
            "windows_ge_0_75": sum(1 for s in r["scores"] if s >= 0.75),
            "longest_run_ge_0_37": _longest_consecutive_run(r["scores"], 0.37),
            "longest_run_ge_0_75": _longest_consecutive_run(r["scores"], 0.75),
        }
        for r in event_records
    ]

    max_probs = [max(r["scores"]) if r["scores"] else 0.0 for r in labeled_train]
    y_train = [int(r["binary_label"]) for r in labeled_train]
    temp_sweep = []
    for temp in temperatures:
        scaled = apply_temperature_scaling(max_probs, temp)
        cal = compute_binary_ece_and_brier(scaled, y_train, n_bins=5)
        temp_sweep.append(
            {
                "temperature": temp,
                "ece_5bin": cal["ece"],
                "mce_5bin": cal["mce"],
                "brier": cal["brier"],
            }
        )

    best_f1_row = max(
        grid_rows,
        key=lambda row: (row["f1"], row["specificity"], -row["no_train_fp"], -row["threshold"]),
    )
    return {
        "schema_version": "acoustic-hysteresis-calibration/1.0",
        "train_labeled_count": len(labeled_train),
        "no_train_count": len(no_train),
        "engine_count": len(engine),
        "hysteresis_grid": grid_rows,
        "best_f1_point": best_f1_row,
        "event_run_summaries": event_run_summaries,
        "calibration_temperature_sweep_exploratory": temp_sweep,
    }


def compute_event_triggered_duty_cycle(
    vision_ms_per_frame: float,
    audio_ms_per_window: float,
    *,
    avg_active_vision_window_s: float = 60.0,
    trains_per_day_list: tuple[int, ...] = (10, 20, 40),
    active_fps: float = 5.0,
    num_cameras: int = 2,
    watchdog_check_interval_s: float = 30.0,
    arm_slowdown_factors: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Compute analytical daily compute duty cycle and Raspberry Pi projections.

    Compares Continuous 24/7 dual-camera vision at ``active_fps`` against
    Audio/Vibration Event-Triggered Vision (continuous 2 Hz audio monitoring +
    ``watchdog_check_interval_s`` single-frame camera health check + ``active_fps``
    vision active only during ``avg_active_vision_window_s`` per train passage).
    """
    seconds_per_day = 86_400.0
    slowdowns = arm_slowdown_factors or {"rpi4b_4gb_cortex_a72": 5.5, "rpi5_8gb_cortex_a76": 2.4}
    continuous_vision_frames_day = int(round(seconds_per_day * active_fps * num_cameras))
    continuous_audio_windows_day = int(round(seconds_per_day * 2.0))  # 0.5 s hop -> 2 windows/s
    cont_compute_s_day = (
        continuous_vision_frames_day * (vision_ms_per_frame / 1000.0)
        + continuous_audio_windows_day * (audio_ms_per_window / 1000.0)
    )
    cont_cpu_core_frac = cont_compute_s_day / seconds_per_day

    duty_rows: list[dict[str, Any]] = []
    watchdog_frames_day = int(round((seconds_per_day / watchdog_check_interval_s) * num_cameras))
    for n_trains in trains_per_day_list:
        active_frames = int(round(n_trains * avg_active_vision_window_s * active_fps * num_cameras))
        tot_frames = active_frames + watchdog_frames_day
        gated_compute_s_day = (
            tot_frames * (vision_ms_per_frame / 1000.0)
            + continuous_audio_windows_day * (audio_ms_per_window / 1000.0)
        )
        gated_cpu_core_frac = gated_compute_s_day / seconds_per_day
        frame_reduction = 1.0 - (tot_frames / continuous_vision_frames_day)
        compute_reduction = 1.0 - (gated_compute_s_day / max(cont_compute_s_day, 1e-9))

        sbc_proj = {}
        for dev, factor in slowdowns.items():
            est_vision_ms = vision_ms_per_frame * factor
            est_audio_ms = audio_ms_per_window * factor
            est_cont_core = (
                continuous_vision_frames_day * (est_vision_ms / 1000.0)
                + continuous_audio_windows_day * (est_audio_ms / 1000.0)
            ) / seconds_per_day
            est_gated_core = (
                tot_frames * (est_vision_ms / 1000.0)
                + continuous_audio_windows_day * (est_audio_ms / 1000.0)
            ) / seconds_per_day
            sbc_proj[dev] = {
                "projection_type": "ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE",
                "assumed_slowdown_vs_host": factor,
                "projected_vision_ms": round(est_vision_ms, 2),
                "projected_continuous_core_fraction": round(est_cont_core, 4),
                "projected_event_triggered_core_fraction": round(est_gated_core, 4),
            }

        duty_rows.append(
            {
                "trains_per_day": n_trains,
                "active_vision_frames_day": active_frames,
                "watchdog_vision_frames_day": watchdog_frames_day,
                "total_gated_vision_frames_day": tot_frames,
                "continuous_vision_frames_day": continuous_vision_frames_day,
                "vision_frame_reduction_pct": round(frame_reduction * 100.0, 2),
                "host_continuous_cpu_core_fraction": round(cont_cpu_core_frac, 4),
                "host_gated_cpu_core_fraction": round(gated_cpu_core_frac, 4),
                "total_compute_time_reduction_pct": round(compute_reduction * 100.0, 2),
                "sbc_analytical_projections": sbc_proj,
            }
        )
    return {
        "host_vision_ms_per_frame": round(vision_ms_per_frame, 3),
        "host_audio_ms_per_window": round(audio_ms_per_window, 3),
        "active_vision_window_s": avg_active_vision_window_s,
        "continuous_vision_frames_day": continuous_vision_frames_day,
        "duty_cycle_scenarios": duty_rows,
    }


def _make_det(label: str, conf: float, bbox: tuple[float, float, float, float] | None = None) -> Detection:
    return Detection(label=label, confidence=conf, bbox_xyxy=bbox)


def _make_rec(
    t: float,
    source_id: str,
    modality: Modality,
    dets: tuple[Detection, ...] = (),
    *,
    available: bool = True,
    metadata: dict[str, Any] | None = None,
) -> EvidenceRecord:
    return EvidenceRecord(
        timestamp_s=round(t, 3),
        source_id=source_id,
        modality=modality,
        available=available,
        detections=list(dets),
        metadata=dict(metadata) if metadata else {},
    )


def _make_occ(t: float, state: OccupancyState) -> OccupancyEvidence:
    return OccupancyEvidence(
        timestamp_s=round(t, 3),
        source_id="occ_sensor_1",
        state=state,
        available=True,
        confidence=0.95 if state in (OccupancyState.CLEAR, OccupancyState.OCCUPIED) else None,
        metadata={},
    )


def _run_synthetic_event(
    recs: list[EvidenceRecord],
    occs: list[OccupancyEvidence],
    *,
    duration_s: float = 24.0,
    dt_s: float = 0.2,
    event_id: str = "stress_event",
    engine_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    collector = MultimodalEvidenceCollector(
        window_tolerance_s=0.5,
        event_id=event_id,
        allow_stale_detection_backfill=False,
    )
    collector.add_evidence_batch(recs)
    for o in occs:
        collector.add_occupancy(o)
    frames = collector.generate_frames_from_history(0.0, duration_s, stride_s=dt_s)
    eng = MultimodalDecisionEngineV3FourLayer(**(engine_kwargs or {}))
    runner = EventSimulationRunner(decision_engine=eng)
    res = runner.run_frames(frames, event_id=event_id, scenario_name="stress")

    states = [step.crossing_state for step in res.steps]
    all_legal = True
    for i in range(1, len(states)):
        prev_s = CrossingState(states[i - 1])
        next_s = CrossingState(states[i])
        if next_s != prev_s and next_s not in ALLOWED_TRANSITIONS.get(prev_s, frozenset()):
            all_legal = False
            break

    closed_steps = [s for s in res.steps if s.gate_state in ("CLOSING", "CLOSED")]
    failsafe_steps = [s for s in res.steps if s.crossing_state == CrossingState.FAULT_FAIL_SAFE.value]
    opening_during_hazard = any(
        4.0 <= s.timestamp_s <= 12.8 and s.gate_state == "OPENING" for s in res.steps
    )
    first_warning_s = next(
        (s.timestamp_s for s in res.steps if s.crossing_state == CrossingState.WARNING.value), None
    )
    first_close_cmd_s = eng.timing_trace.get("gate_close_command_s")
    first_reopen_s = eng.timing_trace.get("gate_opening_s")
    return {
        "all_transitions_legal": all_legal,
        "closed_or_closing": bool(closed_steps),
        "entered_failsafe": bool(failsafe_steps),
        "unsafe_opening_during_train": opening_during_hazard,
        "premature_opening_detected": bool(res.premature_opening_detected),
        "first_warning_s": first_warning_s,
        "first_close_cmd_s": first_close_cmd_s,
        "first_reopen_s": first_reopen_s,
        "final_crossing_state": states[-1],
        "final_gate_state": res.steps[-1].gate_state,
    }


def _build_weather_stress_streams(
    *,
    alpha_conf: float,
    drop_prob: float,
    rng: random.Random,
    duration_s: float = 24.0,
    dt_s: float = 0.2,
    include_visibility_telemetry: bool = False,
) -> tuple[list[EvidenceRecord], list[OccupancyEvidence]]:
    recs: list[EvidenceRecord] = []
    occs: list[OccupancyEvidence] = []
    n_steps = int(round(duration_s / dt_s))
    vis_meta = (
        {"optical_visibility_score": round(float(alpha_conf), 4), "optical_degraded": alpha_conf < 0.45}
        if include_visibility_telemetry
        else None
    )
    for i in range(n_steps + 1):
        t = round(i * dt_s, 3)
        # Attenuated confidences modeling rain/fog/low-light decay on true objects
        c_front = round(min(max(0.88 * alpha_conf, 0.05), 0.99), 4)
        c_side = round(min(max(0.86 * alpha_conf, 0.05), 0.99), 4)
        c_rear = round(min(max(0.88 * alpha_conf, 0.05), 0.99), 4)

        if rng.random() >= drop_prob:
            f_dets = (_make_det("front", c_front, (20.0, 40.0, 120.0, 140.0)),) if 1.0 <= t <= 5.0 else ()
            recs.append(_make_rec(t, "camera_1", Modality.VISION, f_dets, metadata=vis_meta))
        if rng.random() >= drop_prob:
            s_dets = (
                (_make_det("side", c_side, (40.0 + (t - 4.0) * 18.0, 50.0, 140.0 + (t - 4.0) * 18.0, 150.0)),)
                if 4.0 <= t <= 11.4
                else ()
            )
            recs.append(_make_rec(t, "camera_side", Modality.VISION, s_dets))
        if round(t * 10) % 5 == 0:
            a_conf = 0.80 * alpha_conf if (1.5 <= t <= 4.5 or 6.0 <= t <= 9.5) else 0.08
            recs.append(_make_rec(t, "audio_1", Modality.AUDIO, (_make_det("train", a_conf),)))
        if rng.random() >= drop_prob:
            if 11.2 <= t <= 12.6:
                b_dets = (_make_det("rear", c_rear, (30.0, 40.0, 110.0, 140.0)),)
            else:
                b_dets = ()
            recs.append(_make_rec(t, "camera_2", Modality.VISION, b_dets))
        occs.append(_make_occ(t, OccupancyState.OCCUPIED if 4.0 <= t <= 12.8 else OccupancyState.CLEAR))
    return recs, occs


def evaluate_weather_and_interlocking_stress(
    *,
    alphas: tuple[float, ...] = (1.0, 0.8, 0.6, 0.45, 0.35),
    drop_probs: tuple[float, ...] = (0.0, 0.15, 0.30, 0.50),
    seeds: tuple[int, ...] = (11, 22, 33, 44, 55),
) -> dict[str, Any]:
    """Run controlled synthetic weather attenuation x packet-drop grid and interlocking checks."""
    grid_summary: list[dict[str, Any]] = []
    total_runs = 0
    total_unsafe_openings = 0
    total_illegal_transitions = 0

    for alpha in alphas:
        for p_drop in drop_probs:
            runs = []
            for seed in seeds:
                rng = random.Random(seed * 1000 + int(round(alpha * 100)) + int(round(p_drop * 100)))
                recs, occs = _build_weather_stress_streams(alpha_conf=alpha, drop_prob=p_drop, rng=rng)
                out = _run_synthetic_event(recs, occs, event_id=f"wx_a{alpha}_d{p_drop}_s{seed}")
                runs.append(out)
                total_runs += 1
                if out["unsafe_opening_during_train"]:
                    total_unsafe_openings += 1
                if not out["all_transitions_legal"]:
                    total_illegal_transitions += 1
            n = len(runs)
            grid_summary.append(
                {
                    "alpha_conf": alpha,
                    "burst_drop_prob": p_drop,
                    "effective_front_conf": round(0.88 * alpha, 4),
                    "n_seeds": n,
                    "closure_rate": round(sum(1 for r in runs if r["closed_or_closing"]) / n, 4),
                    "failsafe_rate": round(sum(1 for r in runs if r["entered_failsafe"]) / n, 4),
                    "miss_open_rate": round(sum(1 for r in runs if not r["closed_or_closing"]) / n, 4),
                    "reopen_rate": round(sum(1 for r in runs if r["first_reopen_s"] is not None) / n, 4),
                    "unsafe_opening_count": sum(1 for r in runs if r["unsafe_opening_during_train"]),
                    "all_transitions_legal": all(r["all_transitions_legal"] for r in runs),
                }
            )

    # Named complex interlocking scenarios (deterministic)
    interlocking_results: dict[str, Any] = {}

    # 1. Stalled vehicle inside crossing after rear departs [12.8..20.8], then clears at 21.0
    recs_stall, occs_stall = _build_weather_stress_streams(alpha_conf=1.0, drop_prob=0.0, rng=random.Random(1), duration_s=28.0)
    occs_stall = [
        _make_occ(o.timestamp_s, OccupancyState.OCCUPIED if 4.0 <= o.timestamp_s <= 20.8 else OccupancyState.CLEAR)
        for o in occs_stall
    ]
    out_stall = _run_synthetic_event(recs_stall, occs_stall, duration_s=28.0, event_id="stalled_obstacle_hold")
    interlocking_results["stalled_obstacle_during_departure"] = {
        **out_stall,
        "held_closed_past_20_8s": (out_stall["first_reopen_s"] is not None and out_stall["first_reopen_s"] > 20.8),
    }

    # 2. Multi-train arrival during gate opening [14.8..20.0]
    recs_mt, occs_mt = _build_weather_stress_streams(alpha_conf=1.0, drop_prob=0.0, rng=random.Random(2), duration_s=28.0)
    recs_mt = [
        _make_rec(r.timestamp_s, "camera_1", Modality.VISION, (_make_det("front", 0.90),))
        if (r.source_id == "camera_1" and 14.8 <= r.timestamp_s <= 20.0)
        else r
        for r in recs_mt
    ]
    occs_mt = [
        _make_occ(o.timestamp_s, OccupancyState.OCCUPIED if (4.0 <= o.timestamp_s <= 12.8 or 15.2 <= o.timestamp_s <= 22.0) else o.state)
        for o in occs_mt
    ]
    interlocking_results["multi_train_reopen_interrupt"] = _run_synthetic_event(
        recs_mt, occs_mt, duration_s=28.0, event_id="multi_train_interrupt"
    )

    # 3. Healthy optical attenuation below 0.35 threshold (0.35 * 0.88 = 0.308 < 0.35, 0% drop)
    recs_att, occs_att = _build_weather_stress_streams(alpha_conf=0.35, drop_prob=0.0, rng=random.Random(3), duration_s=24.0)
    interlocking_results["healthy_subthreshold_optical_attenuation"] = _run_synthetic_event(
        recs_att, occs_att, duration_s=24.0, event_id="subthreshold_optical"
    )

    return {
        "schema_version": "weather-and-interlocking-stress/1.0",
        "input_classification": "SYNTHETIC_ONLY",
        "total_grid_runs": total_runs,
        "total_unsafe_openings": total_unsafe_openings,
        "total_illegal_transitions": total_illegal_transitions,
        "weather_dropout_grid": grid_summary,
        "interlocking_scenarios": interlocking_results,
    }


def _classification_metrics(preds: list[bool], labels: list[int]) -> dict[str, Any]:
    tp = sum(1 for p, y in zip(preds, labels, strict=True) if p and y == 1)
    fp = sum(1 for p, y in zip(preds, labels, strict=True) if p and y == 0)
    tn = sum(1 for p, y in zip(preds, labels, strict=True) if (not p) and y == 0)
    fn = sum(1 for p, y in zip(preds, labels, strict=True) if (not p) and y == 1)
    rec = _safe_div(tp, tp + fn)
    spec = _safe_div(tn, tn + fp)
    prec = _safe_div(tp, tp + fp)
    f1 = _safe_div(2.0 * prec * rec, prec + rec)
    acc = _safe_div(tp + tn, tp + fp + tn + fn)
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "recall": round(rec, 4),
        "specificity": round(spec, 4),
        "precision": round(prec, 4),
        "f1": round(f1, 4),
        "accuracy": round(acc, 4),
    }


def _binary_nll(probs: list[float], labels: list[int]) -> float:
    eps = 1e-6
    total = 0.0
    for p, y in zip(probs, labels, strict=True):
        pc = min(max(p, eps), 1.0 - eps)
        total -= (y * math.log(pc)) + ((1 - y) * math.log(1.0 - pc))
    return total / len(probs)


def _stratified_bootstrap_ci(
    preds: list[bool],
    probs_raw: list[float],
    probs_cal: list[float],
    labels: list[int],
    *,
    n_boot: int = 2000,
    seed: int = 20261114,
) -> dict[str, dict[str, float]]:
    rng = random.Random(seed)
    pos_idx = [i for i, y in enumerate(labels) if y == 1]
    neg_idx = [i for i, y in enumerate(labels) if y == 0]
    f1s: list[float] = []
    recalls: list[float] = []
    specs: list[float] = []
    brier_deltas: list[float] = []
    for _ in range(n_boot):
        sample = [rng.choice(pos_idx) for _ in pos_idx] + [rng.choice(neg_idx) for _ in neg_idx]
        s_preds = [preds[i] for i in sample]
        s_labels = [labels[i] for i in sample]
        s_raw = [probs_raw[i] for i in sample]
        s_cal = [probs_cal[i] for i in sample]
        m = _classification_metrics(s_preds, s_labels)
        f1s.append(m["f1"])
        recalls.append(m["recall"])
        specs.append(m["specificity"])
        raw_brier = sum((p - y) ** 2 for p, y in zip(s_raw, s_labels, strict=True)) / len(sample)
        cal_brier = sum((p - y) ** 2 for p, y in zip(s_cal, s_labels, strict=True)) / len(sample)
        brier_deltas.append(cal_brier - raw_brier)

    def _ci(vals: list[float]) -> dict[str, float]:
        s = sorted(vals)
        n = len(s)
        lo = s[int(0.025 * (n - 1))]
        hi = s[int(0.975 * (n - 1))]
        mean = sum(s) / n
        return {"mean": round(mean, 4), "ci95_low": round(lo, 4), "ci95_high": round(hi, 4)}

    return {
        "n_bootstrap": n_boot,
        "f1": _ci(f1s),
        "recall": _ci(recalls),
        "specificity": _ci(specs),
        "cal_minus_raw_brier": _ci(brier_deltas),
    }


def evaluate_loeo_acoustic_crossval(
    event_records: list[dict[str, Any]],
    *,
    thresholds: tuple[float, ...] = (0.37, 0.50, 0.65, 0.75, 0.80, 0.85, 0.90, 0.95),
    k_values: tuple[int, ...] = (1, 2, 3, 4),
    temperatures: tuple[float, ...] = tuple(round(0.5 + 0.1 * i, 2) for i in range(36)),
    n_bootstrap: int = 2000,
) -> dict[str, Any]:
    """Leave-One-Event-Out cross-validation for acoustic hysteresis + temperature scaling."""
    labeled = [r for r in event_records if r["cohort"] == "train_events" and r["binary_label"] in (0, 1)]
    no_train = [r for r in event_records if r["cohort"] == "no_train_events"]
    engine = [r for r in event_records if r["cohort"] == "engine_events"]
    if len(labeled) < 4:
        raise ValueError("Need at least 4 labeled train_events for LOEO CV")

    fold_rows: list[dict[str, Any]] = []
    oof_preds: list[bool] = []
    oof_labels: list[int] = []
    oof_probs_raw: list[float] = []
    oof_probs_cal: list[float] = []
    selected_pairs: dict[str, int] = {}
    selected_temps: list[float] = []

    for i, held in enumerate(labeled):
        train_sub = [r for j, r in enumerate(labeled) if j != i]
        best_choice: tuple[tuple[float, float, int, float], float, int] | None = None
        for tau in thresholds:
            for k in k_values:
                tr_preds = [_longest_consecutive_run(r["scores"], tau) >= k for r in train_sub]
                tr_labels = [int(r["binary_label"]) for r in train_sub]
                m = _classification_metrics(tr_preds, tr_labels)
                nt_fp = sum(1 for r in no_train if _longest_consecutive_run(r["scores"], tau) >= k)
                score_key = (m["f1"], m["specificity"], -nt_fp, -tau)
                if best_choice is None or score_key > best_choice[0]:
                    best_choice = (score_key, tau, k)
        assert best_choice is not None
        tau_star, k_star = best_choice[1], best_choice[2]

        tr_max_probs = [max(r["scores"]) if r["scores"] else 0.0 for r in train_sub]
        tr_labels = [int(r["binary_label"]) for r in train_sub]
        best_temp = 1.0
        best_nll = float("inf")
        for temp in temperatures:
            cal = apply_temperature_scaling(tr_max_probs, temp)
            nll = _binary_nll(cal, tr_labels)
            if nll < best_nll:
                best_nll = nll
                best_temp = temp

        held_pred = _longest_consecutive_run(held["scores"], tau_star) >= k_star
        held_label = int(held["binary_label"])
        held_raw_p = max(held["scores"]) if held["scores"] else 0.0
        held_cal_p = apply_temperature_scaling([held_raw_p], best_temp)[0]

        oof_preds.append(held_pred)
        oof_labels.append(held_label)
        oof_probs_raw.append(held_raw_p)
        oof_probs_cal.append(held_cal_p)
        pair_key = f"tau={tau_star:.2f},k={k_star}"
        selected_pairs[pair_key] = selected_pairs.get(pair_key, 0) + 1
        selected_temps.append(best_temp)
        fold_rows.append(
            {
                "fold_event": held["event_id"],
                "true_label": held_label,
                "selected_tau": tau_star,
                "selected_k": k_star,
                "selected_temp": best_temp,
                "oof_pred": held_pred,
                "oof_raw_prob": round(held_raw_p, 4),
                "oof_cal_prob": round(held_cal_p, 4),
            }
        )

    base_preds = [_longest_consecutive_run(r["scores"], 0.37) >= 1 for r in labeled]
    base_metrics = _classification_metrics(base_preds, oof_labels)
    oof_metrics = _classification_metrics(oof_preds, oof_labels)
    raw_cal = compute_binary_ece_and_brier(oof_probs_raw, oof_labels, n_bins=5)
    oof_cal = compute_binary_ece_and_brier(oof_probs_cal, oof_labels, n_bins=5)
    ci = _stratified_bootstrap_ci(oof_preds, oof_probs_raw, oof_probs_cal, oof_labels, n_boot=n_bootstrap)

    return {
        "schema_version": "loeo-acoustic-crossval/1.0",
        "n_labeled_train": len(labeled),
        "n_no_train_controls": len(no_train),
        "n_engine_controls": len(engine),
        "baseline_frozen_tau037_k1": base_metrics,
        "loeo_oof_hysteresis_metrics": oof_metrics,
        "oof_calibration": {
            "uncalibrated_ece_5bin": raw_cal["ece"],
            "uncalibrated_brier": raw_cal["brier"],
            "oof_temp_scaled_ece_5bin": oof_cal["ece"],
            "oof_temp_scaled_brier": oof_cal["brier"],
            "selected_temperature_min": min(selected_temps),
            "selected_temperature_max": max(selected_temps),
            "selected_temperature_mean": round(sum(selected_temps) / len(selected_temps), 3),
        },
        "fold_selection_frequency": dict(sorted(selected_pairs.items(), key=lambda kv: (-kv[1], kv[0]))),
        "bootstrap_95_ci": ci,
        "folds": fold_rows,
    }


def evaluate_optical_degradation_wakeup_ablation(
    *,
    alphas: tuple[float, ...] = (1.0, 0.8, 0.6, 0.45, 0.35),
) -> dict[str, Any]:
    """Compare baseline V3 vs optical-degradation-aware audio wakeup across degraded/clear controls."""
    rows: list[dict[str, Any]] = []
    wakeup_kwargs = {
        "enable_optical_degradation_audio_wakeup": True,
        "optical_visibility_floor": 0.45,
        "degraded_audio_wakeup_threshold": 0.75,
        "degraded_audio_wakeup_frames": 3,
    }
    for alpha in alphas:
        recs, occs = _build_weather_stress_streams(
            alpha_conf=alpha,
            drop_prob=0.0,
            rng=random.Random(900 + int(round(alpha * 100))),
            include_visibility_telemetry=True,
        )
        # Ensure sustained horn windows while train approaches under heavy fog
        recs_with_horn = [
            _make_rec(r.timestamp_s, "audio_1", Modality.AUDIO, (_make_det("train", 0.84),))
            if (r.source_id == "audio_1" and 1.5 <= r.timestamp_s <= 4.5)
            else r
            for r in recs
        ]
        base_out = _run_synthetic_event(recs_with_horn, occs, event_id=f"base_a{alpha}")
        wake_out = _run_synthetic_event(
            recs_with_horn, occs, event_id=f"wake_a{alpha}", engine_kwargs=wakeup_kwargs
        )
        rows.append(
            {
                "alpha_conf": alpha,
                "effective_front_conf": round(0.88 * alpha, 4),
                "optical_degraded_telemetry": alpha < 0.45,
                "baseline_v3_closed": base_out["closed_or_closing"],
                "baseline_v3_unsafe_open": base_out["unsafe_opening_during_train"],
                "wakeup_v3_closed": wake_out["closed_or_closing"],
                "wakeup_v3_unsafe_open": wake_out["unsafe_opening_during_train"],
                "wakeup_v3_all_legal": wake_out["all_transitions_legal"],
                "wakeup_v3_trigger_s": wake_out["first_warning_s"],
            }
        )

    # Control 1: Clear healthy optics + strong ambient highway/engine horn -> must NEVER close gate
    recs_clear_horn, occs_clear = _build_weather_stress_streams(
        alpha_conf=0.95, drop_prob=0.0, rng=random.Random(1001), include_visibility_telemetry=True
    )
    recs_clear_horn = [
        _make_rec(r.timestamp_s, "camera_1", Modality.VISION, (), metadata={"optical_visibility_score": 0.95, "optical_degraded": False})
        if r.source_id == "camera_1"
        else (
            _make_rec(r.timestamp_s, "audio_1", Modality.AUDIO, (_make_det("train", 0.95),))
            if (r.source_id == "audio_1" and 2.0 <= r.timestamp_s <= 6.0)
            else (_make_rec(r.timestamp_s, r.source_id, r.modality, ()) if r.modality == Modality.VISION else r)
        )
        for r in recs_clear_horn
    ]
    ctrl_clear_horn = _run_synthetic_event(
        recs_clear_horn,
        [_make_occ(o.timestamp_s, OccupancyState.CLEAR) for o in occs_clear],
        event_id="ctrl_clear_ambient_horn",
        engine_kwargs=wakeup_kwargs,
    )

    # Control 2: Degraded optics + single impulse horn glitch (1 window < k=3) -> must NEVER close gate
    recs_impulse, _ = _build_weather_stress_streams(
        alpha_conf=0.35, drop_prob=0.0, rng=random.Random(1002), include_visibility_telemetry=True
    )
    recs_impulse = [
        _make_rec(r.timestamp_s, "audio_1", Modality.AUDIO, (_make_det("train", 0.92 if abs(r.timestamp_s - 3.0) < 1e-6 else 0.05),))
        if r.source_id == "audio_1"
        else (_make_rec(r.timestamp_s, r.source_id, r.modality, (), metadata=r.metadata) if r.modality == Modality.VISION else r)
        for r in recs_impulse
    ]
    ctrl_impulse = _run_synthetic_event(
        recs_impulse,
        [_make_occ(o.timestamp_s, OccupancyState.CLEAR) for o in occs_clear],
        event_id="ctrl_degraded_single_impulse",
        engine_kwargs=wakeup_kwargs,
    )

    return {
        "schema_version": "optical-degradation-wakeup-ablation/1.0",
        "input_classification": "SYNTHETIC_ONLY",
        "attenuation_sweep": rows,
        "controls": {
            "clear_optics_sustained_ambient_horn_closed": ctrl_clear_horn["closed_or_closing"],
            "degraded_optics_single_impulse_horn_closed": ctrl_impulse["closed_or_closing"],
        },
    }
