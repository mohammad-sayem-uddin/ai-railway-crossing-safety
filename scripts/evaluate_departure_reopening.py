#!/usr/bin/env python3
"""EXP-J: Departure Confirmation, Clearance Dwell, and Reopening Evaluation (V1 vs V2).

Compares frozen V1 (RULE_3B) vs adopted V2 (RULE_3B + RULE_3C disappearance confirmation)
and Stateless comparators across:
  1) Strictly paired 11 CALIBRATION_SUPPORTED sync events (DUAL_VISION_AUDIO, DUAL_VISION)
  2) Independent-camera 27 events (BACK_VISION on local back clock, B0, FRONT_AUDIO)

Computes exact rule triggers, detection density diagnostics on camera_2, recording-length
margin analysis (identifying short-tail censoring like event_002 / event_006), clearance
latency relative to T4, and M4 premature-opening safety margins.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SCRIPTS_DIR = REPO_ROOT / "scripts"
for p in (str(SRC_DIR), str(SCRIPTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from exploratory_common import (  # noqa: E402
    EXPLORATORY_LABEL,
    VerifiedExploratoryContext,
    assemble_frames,
    load_event_evidence_records,
    load_verified_context,
    write_verified_json,
)

from railway_detection.fusion.rules import CrossingState  # noqa: E402


def _analyze_stream_detection_density(
    ctx: VerifiedExploratoryContext,
    event_id: str,
    condition: str,
) -> dict[str, Any]:
    """Measure back-camera class distribution and >=0.35 detection density/gaps."""
    recs, aligner, _ = load_event_evidence_records(ctx, event_id, condition)
    frames = assemble_frames(recs, aligner, stride_s=0.2, window_tolerance_s=0.5)
    cam2_ticks = 0
    cam2_any_qualifying = 0
    max_consec_cam2_silence = 0
    curr_silence = 0
    silence_windows: list[tuple[float, float, int]] = []
    sil_start: float | None = None
    label_counts = {"front": 0, "rear": 0, "side": 0, "train": 0}

    for f in frames:
        c2_recs = [r for r in f.vision_records if r.source_id == "camera_2" and r.available]
        if c2_recs:
            cam2_ticks += 1
        qual = [
            d
            for r in c2_recs
            for d in r.detections
            if d.confidence >= 0.35 and d.label in label_counts
        ]
        for d in qual:
            label_counts[d.label] += 1
        if qual:
            cam2_any_qualifying += 1
            if curr_silence > 0 and sil_start is not None:
                silence_windows.append((sil_start, round(f.master_timestamp_s - 0.2, 4), curr_silence))
            curr_silence = 0
            sil_start = None
        else:
            if curr_silence == 0:
                sil_start = round(f.master_timestamp_s, 4)
            curr_silence += 1
            if curr_silence > max_consec_cam2_silence:
                max_consec_cam2_silence = curr_silence

    if curr_silence > 0 and sil_start is not None and frames:
        silence_windows.append((sil_start, round(frames[-1].master_timestamp_s, 4), curr_silence))

    return {
        "total_frames": len(frames),
        "cam2_present_ticks": cam2_ticks,
        "cam2_qualifying_ticks": cam2_any_qualifying,
        "cam2_qualifying_density": round(cam2_any_qualifying / len(frames), 6) if frames else 0.0,
        "cam2_qualifying_label_counts": label_counts,
        "cam2_max_consecutive_empty_ticks": max_consec_cam2_silence,
        "cam2_ge2_tick_gaps_count": sum(1 for _, _, c in silence_windows if c >= 2),
        "cam2_last_empty_gap": silence_windows[-1] if silence_windows else None,
        "master_end_s": round(frames[-1].master_timestamp_s, 4) if frames else 0.0,
    }


def _load_trace(output_dir: Path, run_label: str, event_key: str) -> dict[str, Any]:
    path = output_dir / "replays" / "traces" / f"{run_label}__{event_key}.json"
    with open(path, "r", encoding="utf-8", newline="") as f:
        return json.load(f)


def _trace_summary_fields(trace: dict[str, Any]) -> dict[str, Any]:
    steps = trace["steps"]
    rc = trace["rule_counts"]
    em = trace["evaluation_metrics"]

    entered_departing = any(s["crossing_state"] == CrossingState.TRAIN_DEPARTING.value for s in steps)
    entered_rear_conf = any(s["crossing_state"] == CrossingState.REAR_CONFIRMED.value for s in steps)
    entered_clear = trace["reached_crossing_clear"]
    entered_opening = trace["reached_gate_opening"]
    returned_idle = any(
        t["to"] == CrossingState.IDLE.value and t["from"] == CrossingState.GATE_OPENING.value
        for t in trace["transitions"]
    )
    rear_conf_t = next(
        (s["t"] for s in steps if s["crossing_state"] == CrossingState.REAR_CONFIRMED.value), None
    )
    clear_t = em.get("first_crossing_clear_s")
    open_after_clear_t = em.get("first_unblocked_after_clear_s")
    t4 = trace["mapped_boundaries"].get("t4")
    clearance_latency_s = (
        round(open_after_clear_t - t4, 6)
        if (open_after_clear_t is not None and t4 is not None)
        else None
    )
    clear_to_t4_s = round(clear_t - t4, 6) if (clear_t is not None and t4 is not None) else None

    return {
        "final_crossing_state": trace["final_crossing_state"],
        "final_gate_state": trace["final_gate_state"],
        "entered_train_departing": entered_departing,
        "entered_rear_confirmed": entered_rear_conf,
        "first_rear_confirmed_s": rear_conf_t,
        "reached_crossing_clear": entered_clear,
        "first_crossing_clear_s": clear_t,
        "reached_gate_opening": entered_opening,
        "returned_to_idle": returned_idle,
        "first_unblocked_after_clear_s": open_after_clear_t,
        "clearance_latency_unblocked_minus_t4_s": clearance_latency_s,
        "crossing_clear_minus_t4_s": clear_to_t4_s,
        "rule_3b_count": rc.get("RULE_3B_DEPARTURE_CONFIRMED_UNAMBIGUOUS_REAR", 0),
        "rule_3c_count": rc.get("RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE", 0),
        "rule_2_audio_delay_count": rc.get("RULE_2_AUDIO_SUPPORT_ONLY", 0),
        "rule_7_interrupt_count": rc.get("RULE_7_NEW_TRAIN_INTERRUPT", 0),
        "rule_5_6_hold_abort_count": rc.get("RULE_5_STALE_SOURCE_ABORT", 0)
        + rc.get("RULE_6_DEGRADED_SOURCE_HOLD", 0),
        "premature_opening_m4": em["premature_opening_m4"],
        "m4_status_detail": em["m4_status_detail"],
        "m4_margin_s": em["m4_margin_s"],
        "closed_duration_s": trace["closed_duration_s"],
        "total_duration_s": trace["total_duration_s"],
    }


def run_departure_reopening_evaluation(
    ctx: VerifiedExploratoryContext, *, output_dir: Path
) -> dict[str, Any]:
    sync11_rows: list[dict[str, Any]] = []
    for ev_id in sorted(ctx.accepted_sync_events):
        ref = ctx.references[ev_id]
        density = _analyze_stream_detection_density(ctx, ev_id, "DUAL_VISION_AUDIO")
        t_v1 = _load_trace(output_dir, "DUAL_VISION_AUDIO__v1", ref.event_key)
        t_v2 = _load_trace(output_dir, "DUAL_VISION_AUDIO__v2", ref.event_key)
        t_st = _load_trace(output_dir, "DUAL_VISION_AUDIO__stateless_rule2", ref.event_key)

        s_v1 = _trace_summary_fields(t_v1)
        s_v2 = _trace_summary_fields(t_v2)
        s_st = _trace_summary_fields(t_st)
        t4_master = t_v2["mapped_boundaries"].get("t4")
        remaining_after_t4_s = (
            round(density["master_end_s"] - t4_master, 4) if t4_master is not None else None
        )
        # Classify V2 non-clearing root cause cleanly from measured numbers
        if s_v2["reached_crossing_clear"]:
            v2_mechanism = "CLEARED_VIA_RULE_3C" if s_v2["rule_3c_count"] > 0 else "CLEARED_VIA_RULE_3B"
            if s_v2["rule_3b_count"] > 0 and s_v2["rule_3c_count"] > 0:
                v2_mechanism = "CLEARED_VIA_RULE_3B_AND_3C"
        elif remaining_after_t4_s is not None and remaining_after_t4_s < 4.5:
            v2_mechanism = "RECORDING_LENGTH_CENSORED_SHORT_TAIL"
        elif t4_master is None and density["cam2_qualifying_density"] >= 0.85:
            v2_mechanism = "RIGHT_CENSORED_CONTINUOUS_TRAIN_AND_HIGH_DENSITY"
        elif density["cam2_qualifying_density"] >= 0.85 and density["cam2_ge2_tick_gaps_count"] == 0:
            v2_mechanism = "NO_2TICK_CAM2_SILENCE_HIGH_DENSITY"
        else:
            v2_mechanism = "HELD_BY_CONTINUING_EVIDENCE_OR_AUDIO_DWELL_RESET"

        row = {
            "cohort_scope": "11_sync_CALIBRATION_SUPPORTED",
            "event_id": ev_id,
            "condition": "DUAL_VISION_AUDIO",
            "t4_master_s": t4_master,
            "master_end_s": density["master_end_s"],
            "post_t4_recording_margin_s": remaining_after_t4_s,
            "cam2_qualifying_density": density["cam2_qualifying_density"],
            "cam2_label_counts": density["cam2_qualifying_label_counts"],
            "cam2_ge2_tick_gaps_count": density["cam2_ge2_tick_gaps_count"],
            "v1_reached_clear": s_v1["reached_crossing_clear"],
            "v1_reached_opening": s_v1["reached_gate_opening"],
            "v1_final_state": s_v1["final_crossing_state"],
            "v1_rule_7_interrupts": s_v1["rule_7_interrupt_count"],
            "v1_premature_m4": s_v1["premature_opening_m4"],
            "v1_closed_duration_s": s_v1["closed_duration_s"],
            "v2_reached_clear": s_v2["reached_crossing_clear"],
            "v2_first_rear_confirmed_s": s_v2["first_rear_confirmed_s"],
            "v2_first_clear_s": s_v2["first_crossing_clear_s"],
            "v2_first_unblocked_after_clear_s": s_v2["first_unblocked_after_clear_s"],
            "v2_clearance_latency_s": s_v2["clearance_latency_unblocked_minus_t4_s"],
            "v2_reached_opening": s_v2["reached_gate_opening"],
            "v2_returned_to_idle": s_v2["returned_to_idle"],
            "v2_final_state": s_v2["final_crossing_state"],
            "v2_rule_3b_count": s_v2["rule_3b_count"],
            "v2_rule_3c_count": s_v2["rule_3c_count"],
            "v2_rule_2_audio_delay_count": s_v2["rule_2_audio_delay_count"],
            "v2_rule_7_interrupts": s_v2["rule_7_interrupt_count"],
            "v2_premature_m4": s_v2["premature_opening_m4"],
            "v2_m4_status_detail": s_v2["m4_status_detail"],
            "v2_m4_margin_s": s_v2["m4_margin_s"],
            "v2_closed_duration_s": s_v2["closed_duration_s"],
            "v2_mechanism_class": v2_mechanism,
            "stateless_premature_m4": s_st["premature_opening_m4"],
            "stateless_m4_margin_s": s_st["m4_margin_s"],
            "stateless_closed_duration_s": s_st["closed_duration_s"],
        }
        sync11_rows.append(row)

    # Also evaluate BACK_VISION (B1) and B0 / FRONT_AUDIO on all 27 independent events
    indep27_rows: list[dict[str, Any]] = []
    for cond_prefix in ("BACK_VISION", "B0", "FRONT_AUDIO"):
        for ev_id in ctx.event_order:
            ref = ctx.references[ev_id]
            t_v1 = _load_trace(output_dir, f"{cond_prefix}__v1", ref.event_key)
            t_v2 = _load_trace(output_dir, f"{cond_prefix}__v2", ref.event_key)
            s_v1 = _trace_summary_fields(t_v1)
            s_v2 = _trace_summary_fields(t_v2)
            indep27_rows.append(
                {
                    "cohort_scope": "27_independent_camera",
                    "condition": cond_prefix,
                    "event_id": ev_id,
                    "cohort": ref.cohort,
                    "clock_mode": t_v2["clock_mode"],
                    "t4_on_clock_s": t_v2["mapped_boundaries"].get("t4"),
                    "v1_reached_clear": s_v1["reached_crossing_clear"],
                    "v1_final_state": s_v1["final_crossing_state"],
                    "v1_rule_7_interrupts": s_v1["rule_7_interrupt_count"],
                    "v1_premature_m4": s_v1["premature_opening_m4"],
                    "v2_reached_clear": s_v2["reached_crossing_clear"],
                    "v2_reached_opening": s_v2["reached_gate_opening"],
                    "v2_first_clear_s": s_v2["first_crossing_clear_s"],
                    "v2_final_state": s_v2["final_crossing_state"],
                    "v2_rule_3b_count": s_v2["rule_3b_count"],
                    "v2_rule_3c_count": s_v2["rule_3c_count"],
                    "v2_rule_7_interrupts": s_v2["rule_7_interrupt_count"],
                    "v2_premature_m4": s_v2["premature_opening_m4"],
                }
            )

    analysis_dir = output_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    csv_path = analysis_dir / "departure_reopening_analysis.csv"
    fieldnames = [
        "event_id",
        "t4_master_s",
        "master_end_s",
        "post_t4_recording_margin_s",
        "cam2_qualifying_density",
        "cam2_ge2_tick_gaps_count",
        "v1_reached_clear",
        "v1_final_state",
        "v1_rule_7_interrupts",
        "v1_premature_m4",
        "v1_closed_duration_s",
        "v2_reached_clear",
        "v2_reached_opening",
        "v2_returned_to_idle",
        "v2_first_rear_confirmed_s",
        "v2_first_clear_s",
        "v2_first_unblocked_after_clear_s",
        "v2_clearance_latency_s",
        "v2_final_state",
        "v2_rule_3b_count",
        "v2_rule_3c_count",
        "v2_rule_2_audio_delay_count",
        "v2_rule_7_interrupts",
        "v2_premature_m4",
        "v2_m4_margin_s",
        "v2_closed_duration_s",
        "v2_mechanism_class",
        "stateless_premature_m4",
        "stateless_m4_margin_s",
        "stateless_closed_duration_s",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in sync11_rows:
            writer.writerow({k: r[k] for k in fieldnames})

    summary = {
        "exploratory_label": EXPLORATORY_LABEL,
        "sync11_aggregates": {
            "total_events": len(sync11_rows),
            "v1_reached_clear_count": sum(1 for r in sync11_rows if r["v1_reached_clear"]),
            "v2_reached_clear_count": sum(1 for r in sync11_rows if r["v2_reached_clear"]),
            "v2_reached_opening_count": sum(1 for r in sync11_rows if r["v2_reached_opening"]),
            "v2_returned_to_idle_count": sum(1 for r in sync11_rows if r["v2_returned_to_idle"]),
            "v1_premature_m4_count": sum(1 for r in sync11_rows if r["v1_premature_m4"] is True),
            "v2_premature_m4_count": sum(1 for r in sync11_rows if r["v2_premature_m4"] is True),
            "stateless_premature_m4_count": sum(
                1 for r in sync11_rows if r["stateless_premature_m4"] is True
            ),
            "v2_non_clearing_breakdown": {
                r["event_id"]: r["v2_mechanism_class"]
                for r in sync11_rows
                if not r["v2_reached_clear"]
            },
        },
        "independent27_summary": {
            cond: {
                "train_events_total": sum(
                    1 for r in indep27_rows if r["condition"] == cond and r["cohort"] == "train_events"
                ),
                "train_v1_clear": sum(
                    1
                    for r in indep27_rows
                    if r["condition"] == cond
                    and r["cohort"] == "train_events"
                    and r["v1_reached_clear"]
                ),
                "train_v2_clear": sum(
                    1
                    for r in indep27_rows
                    if r["condition"] == cond
                    and r["cohort"] == "train_events"
                    and r["v2_reached_clear"]
                ),
                "train_v2_premature_m4": sum(
                    1
                    for r in indep27_rows
                    if r["condition"] == cond
                    and r["cohort"] == "train_events"
                    and r["v2_premature_m4"] is True
                ),
            }
            for cond in ("BACK_VISION", "B0", "FRONT_AUDIO")
        },
        "sync11_events": sync11_rows,
        "independent27_events": indep27_rows,
    }
    json_sha = write_verified_json(analysis_dir / "departure_reopening_analysis.json", summary)
    return {
        "json_sha256": json_sha,
        "v1_clear_11": summary["sync11_aggregates"]["v1_reached_clear_count"],
        "v2_clear_11": summary["sync11_aggregates"]["v2_reached_clear_count"],
        "v2_premature_11": summary["sync11_aggregates"]["v2_premature_m4_count"],
        "stateless_premature_11": summary["sync11_aggregates"]["stateless_premature_m4_count"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate EXP-J departure and reopening behavior.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "results" / "exploratory_execution",
    )
    args = parser.parse_args(argv)
    ctx = load_verified_context(REPO_ROOT)
    out = run_departure_reopening_evaluation(ctx, output_dir=args.output_dir)
    print(
        f"[DONE] V1_clear={out['v1_clear_11']}/11, V2_clear={out['v2_clear_11']}/11, "
        f"V2_M4_premature={out['v2_premature_11']}, Stateless_M4_premature={out['stateless_premature_11']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
