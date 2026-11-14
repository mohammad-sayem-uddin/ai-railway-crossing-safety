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
) -> EvidenceRecord:
    return EvidenceRecord(
        timestamp_s=round(t, 3),
        source_id=source_id,
        modality=modality,
        available=available,
        detections=list(dets),
        metadata={},
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
    eng = MultimodalDecisionEngineV3FourLayer()
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
) -> tuple[list[EvidenceRecord], list[OccupancyEvidence]]:
    recs: list[EvidenceRecord] = []
    occs: list[OccupancyEvidence] = []
    n_steps = int(round(duration_s / dt_s))
    for i in range(n_steps + 1):
        t = round(i * dt_s, 3)
        # Attenuated confidences modeling rain/fog/low-light decay on true objects
        c_front = round(min(max(0.88 * alpha_conf, 0.05), 0.99), 4)
        c_side = round(min(max(0.86 * alpha_conf, 0.05), 0.99), 4)
        c_rear = round(min(max(0.88 * alpha_conf, 0.05), 0.99), 4)

        if rng.random() >= drop_prob:
            f_dets = (_make_det("front", c_front, (20.0, 40.0, 120.0, 140.0)),) if 1.0 <= t <= 5.0 else ()
            recs.append(_make_rec(t, "camera_1", Modality.VISION, f_dets))
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
