#!/usr/bin/env python3
"""EXP-G (missing modality), EXP-H (contradictory evidence), EXP-I (FailureInjector
fault stress across all 8 FailureModes), and EXP-K (fault recovery & multi-train interrupt)
executed deterministically on verified precomputed caches.

All real-data results carry the exploratory adoption qualification; constructed
perturbations are explicitly isolated and labeled.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
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
    simulate_frames,
    write_verified_json,
)

from railway_detection.evaluation.metrics import EventMetricsCalculator, classify_m4  # noqa: E402
from railway_detection.fusion.collector import MultimodalFrame  # noqa: E402
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality  # noqa: E402
from railway_detection.fusion.rules import CrossingState, GateState  # noqa: E402
from railway_detection.simulation.failure_injector import (  # noqa: E402
    FailureInjector,
    FailureMode,
    FailureSchedule,
)


def _mid_time(frames: list[MultimodalFrame]) -> float:
    if not frames:
        return 5.0
    t0 = frames[0].master_timestamp_s
    t1 = frames[-1].master_timestamp_s
    return round(t0 + 0.4 * (t1 - t0), 2)


def _unsafe_open_during_occupancy(
    sim_res: Any, entry_s: float | None, clearance_s: float | None
) -> bool:
    if entry_s is None or clearance_s is None:
        return False
    return any(
        entry_s <= step.timestamp_s < clearance_s
        and not step.is_passage_blocked
        and step.gate_state in (GateState.OPEN.value, GateState.OPENING.value)
        for step in sim_res.steps
    )


def _summarize_fault_run(
    *,
    group: str,
    scenario: str,
    is_constructed_perturbation: bool,
    event_id: str,
    policy: str,
    sim_res: Any,
    entry_s: float | None,
    clearance_s: float | None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    is_train_gt = event_id.startswith("train_events/")
    ev_eval = EventMetricsCalculator.evaluate_run(
        sim_res,
        entry_time_s=entry_s,
        clearance_time_s=clearance_s,
        has_train_ground_truth=is_train_gt,
        evaluable=(not event_id.startswith("engine_events/")),
        ground_truth_status="exploratory_researcher_adopted_ai_reference",
        cohort=event_id.split("/")[0],
        premature_opening_window="first_blocked_to_t4_clearance",
    )
    m4 = classify_m4(sim_res, clearance_s) if (clearance_s is not None and is_train_gt) else None

    fail_safe_steps = sum(
        1 for s in sim_res.steps if s.crossing_state == CrossingState.FAULT_FAIL_SAFE.value
    )
    blocked_steps = sum(1 for s in sim_res.steps if s.is_passage_blocked)
    direct_open_from_fault = any(
        s.decision.previous_state == CrossingState.FAULT_FAIL_SAFE.value
        and s.decision.resulting_gate_state == GateState.OPEN.value
        and s.decision.resulting_state != CrossingState.IDLE.value
        for s in sim_res.steps
    )
    rule_counts: dict[str, int] = {}
    for s in sim_res.steps:
        k = s.decision.rule_id or "NONE"
        rule_counts[k] = rule_counts.get(k, 0) + 1

    transitions = [
        {
            "t": round(float(s.timestamp_s), 6),
            "from": s.decision.previous_state,
            "to": s.decision.resulting_state,
            "rule_id": s.decision.rule_id,
        }
        for s in sim_res.steps
        if s.decision.previous_state != s.decision.resulting_state
    ]
    false_alarm = bool((ev_eval.closure_episodes or 0) > 0) if not is_train_gt else None
    row: dict[str, Any] = {
        "group": group,
        "scenario": scenario,
        "is_constructed_perturbation": is_constructed_perturbation,
        "event_id": event_id,
        "policy": policy,
        "step_count": len(sim_res.steps),
        "rejected_step_count": len(sim_res.rejected_steps),
        "fault_occurred": bool(sim_res.fault_occurred),
        "fail_safe_steps": fail_safe_steps,
        "direct_open_from_fault": direct_open_from_fault,
        "missed_train": ev_eval.missed_train,
        "false_alarm": false_alarm,
        "closure_episodes": ev_eval.closure_episodes,
        "premature_opening_m4": ev_eval.premature_opening,
        "m4_status": str(m4.status) if m4 is not None else None,
        "unsafe_open_during_occupancy": _unsafe_open_during_occupancy(sim_res, entry_s, clearance_s),
        "blocked_fraction": round(blocked_steps / len(sim_res.steps), 6) if sim_res.steps else 0.0,
        "closed_duration_s": round(float(sim_res.closed_duration_s), 6),
        "final_crossing_state": sim_res.steps[-1].crossing_state if sim_res.steps else None,
        "final_gate_state": sim_res.steps[-1].gate_state if sim_res.steps else None,
        "rule_counts": dict(sorted(rule_counts.items())),
        "transitions": transitions,
    }
    if extra:
        row.update(extra)
    return row


def run_exp_g_missing_modality(ctx: VerifiedExploratoryContext) -> list[dict[str, Any]]:
    """EXP-G: Missing-modality ablations & mid-event sensor dropouts across 11 sync + 3 controls."""
    rows: list[dict[str, Any]] = []
    for ev_id in sorted(ctx.accepted_sync_events):
        ref = ctx.references[ev_id]
        bounds = ref.boundaries_for_clock("master")
        t1, t4 = bounds["t1"], bounds["t4"]

        recs_full, aligner, _ = load_event_evidence_records(ctx, ev_id, "DUAL_VISION_AUDIO")
        frames_full = assemble_frames(recs_full, aligner, stride_s=0.2, window_tolerance_s=0.5)
        t_mid = _mid_time(frames_full)

        # G1: Front completely absent (back + audio only on master clock)
        recs_no_front = [r for r in recs_full if r.source_id != "camera_1"]
        frames_no_front = assemble_frames(recs_no_front, aligner, stride_s=0.2, window_tolerance_s=0.5)
        res, _ = simulate_frames(
            frames_no_front,
            event_id=ev_id,
            scenario_name="G1_front_absent_all",
            policy="v2",
            config=ctx.frozen_config,
            entry_time_s=t1,
            clearance_time_s=t4,
        )
        rows.append(
            _summarize_fault_run(
                group="EXP-G",
                scenario="G1_front_absent_all",
                is_constructed_perturbation=False,
                event_id=ev_id,
                policy="v2",
                sim_res=res,
                entry_s=t1,
                clearance_s=t4,
            )
        )

        # G2: Back completely absent (front + audio only, evaluated on master bounds)
        recs_no_back = [r for r in recs_full if r.source_id != "camera_2"]
        frames_no_back = assemble_frames(recs_no_back, aligner, stride_s=0.2, window_tolerance_s=0.5)
        res, _ = simulate_frames(
            frames_no_back,
            event_id=ev_id,
            scenario_name="G2_back_absent_all",
            policy="v2",
            config=ctx.frozen_config,
            entry_time_s=t1,
            clearance_time_s=t4,
        )
        rows.append(
            _summarize_fault_run(
                group="EXP-G",
                scenario="G2_back_absent_all",
                is_constructed_perturbation=False,
                event_id=ev_id,
                policy="v2",
                sim_res=res,
                entry_s=t1,
                clearance_s=t4,
            )
        )

        # G3: Audio completely absent (DUAL_VISION)
        recs_no_audio = [r for r in recs_full if r.modality != Modality.AUDIO]
        frames_no_audio = assemble_frames(recs_no_audio, aligner, stride_s=0.2, window_tolerance_s=0.5)
        res, _ = simulate_frames(
            frames_no_audio,
            event_id=ev_id,
            scenario_name="G3_audio_absent_all",
            policy="v2",
            config=ctx.frozen_config,
            entry_time_s=t1,
            clearance_time_s=t4,
        )
        rows.append(
            _summarize_fault_run(
                group="EXP-G",
                scenario="G3_audio_absent_all",
                is_constructed_perturbation=False,
                event_id=ev_id,
                policy="v2",
                sim_res=res,
                entry_s=t1,
                clearance_s=t4,
            )
        )

        # G4: Mid-event dual vision missing while audio stays healthy
        inj_dual = FailureInjector(
            [FailureSchedule(mode=FailureMode.DUAL_CAMERA_DROPOUT, start_time_s=t_mid, end_time_s=t_mid + 5.0)]
        )
        frames_dual_drop = inj_dual.inject_failures(frames_full)
        res, _ = simulate_frames(
            frames_dual_drop,
            event_id=ev_id,
            scenario_name="G4_dual_vision_dropout_mid",
            policy="v2",
            config=ctx.frozen_config,
            entry_time_s=t1,
            clearance_time_s=t4,
        )
        rows.append(
            _summarize_fault_run(
                group="EXP-G",
                scenario="G4_dual_vision_dropout_mid",
                is_constructed_perturbation=True,
                event_id=ev_id,
                policy="v2",
                sim_res=res,
                entry_s=t1,
                clearance_s=t4,
            )
        )

    # Idle-origin dual camera dropout on the 3 no_train controls (B0 frames)
    for ev_id in ("no_train_events/event_001", "no_train_events/event_002", "no_train_events/event_003"):
        recs, aligner, _ = load_event_evidence_records(ctx, ev_id, "B0")
        frames = assemble_frames(recs, aligner, stride_s=0.2, window_tolerance_s=0.5)
        inj = FailureInjector(
            [FailureSchedule(mode=FailureMode.DUAL_CAMERA_DROPOUT, start_time_s=3.0, end_time_s=8.0)]
        )
        mutated = inj.inject_failures(frames)
        res, _ = simulate_frames(
            mutated,
            event_id=ev_id,
            scenario_name="G5_idle_vision_dropout_confirm2",
            policy="v2",
            config=ctx.frozen_config,
        )
        rows.append(
            _summarize_fault_run(
                group="EXP-G",
                scenario="G5_idle_vision_dropout_confirm2",
                is_constructed_perturbation=True,
                event_id=ev_id,
                policy="v2",
                sim_res=res,
                entry_s=None,
                clearance_s=None,
            )
        )
    return rows


def run_exp_h_contradictory_evidence(ctx: VerifiedExploratoryContext) -> dict[str, Any]:
    """EXP-H: Audit real natural contradictions in clean caches + controlled perturbations."""
    natural_audit: list[dict[str, Any]] = []
    for ev_id in sorted(ctx.accepted_sync_events):
        ref = ctx.references[ev_id]
        recs, aligner, _ = load_event_evidence_records(ctx, ev_id, "DUAL_VISION_AUDIO")
        frames = assemble_frames(recs, aligner, stride_s=0.2, window_tolerance_s=0.5)
        sim_res, _ = simulate_frames(
            frames,
            event_id=ev_id,
            scenario_name="H0_natural_audit",
            policy="v2",
            config=ctx.frozen_config,
            entry_time_s=ref.boundaries_for_clock("master")["t1"],
            clearance_time_s=ref.boundaries_for_clock("master")["t4"],
        )

        sim_front_rear = 0
        vision_pos_audio_neg = 0
        audio_pos_vision_neg = 0
        subthresh_vision_only = 0
        subthresh_audio_only = 0
        for f in frames:
            cam1_front = any(
                d.label == "front" and d.confidence >= 0.35
                for r in f.vision_records
                if r.available and r.source_id == "camera_1"
                for d in r.detections
            )
            cam2_rear = any(
                d.label == "rear" and d.confidence >= 0.35
                for r in f.vision_records
                if r.available and r.source_id == "camera_2"
                for d in r.detections
            )
            any_vis_pos = any(
                d.confidence >= 0.35
                for r in f.vision_records
                if r.available
                for d in r.detections
            )
            any_vis_sub = (
                not any_vis_pos
                and any(
                    0.0 < d.confidence < 0.35
                    for r in f.vision_records
                    if r.available
                    for d in r.detections
                )
            )
            any_aud_pos = any(
                d.confidence >= 0.37
                for r in f.audio_records
                if r.available
                for d in r.detections
            )
            any_aud_sub = (
                not any_aud_pos
                and any(
                    0.0 < d.confidence < 0.37
                    for r in f.audio_records
                    if r.available
                    for d in r.detections
                )
            )
            if cam1_front and cam2_rear:
                sim_front_rear += 1
            if any_vis_pos and not any_aud_pos:
                vision_pos_audio_neg += 1
            if any_aud_pos and not any_vis_pos:
                audio_pos_vision_neg += 1
            if any_vis_sub:
                subthresh_vision_only += 1
            if any_aud_sub:
                subthresh_audio_only += 1

        natural_audit.append(
            {
                "event_id": ev_id,
                "horn_status": ref.horn_status,
                "frame_count": len(frames),
                "simultaneous_front_and_rear_ticks": sim_front_rear,
                "vision_pos_audio_neg_ticks": vision_pos_audio_neg,
                "audio_pos_vision_neg_ticks": audio_pos_vision_neg,
                "subthreshold_vision_only_ticks": subthresh_vision_only,
                "subthreshold_audio_only_ticks": subthresh_audio_only,
                "rule2_audio_delay_count": sum(
                    1
                    for s in sim_res.steps
                    if s.decision.rule_id == "RULE_2_AUDIO_SUPPORT_ONLY"
                ),
            }
        )

    # Controlled contradictory perturbations over clean cached streams
    perturbation_rows: list[dict[str, Any]] = []
    for ev_id in sorted(ctx.accepted_sync_events):
        ref = ctx.references[ev_id]
        bounds = ref.boundaries_for_clock("master")
        t1, t4 = bounds["t1"], bounds["t4"]
        t3 = bounds["t3"] or _mid_time([])
        recs, aligner, _ = load_event_evidence_records(ctx, ev_id, "DUAL_VISION_AUDIO")
        frames = assemble_frames(recs, aligner, stride_s=0.2, window_tolerance_s=0.5)

        # H1: Simultaneous front (cam1, 0.90) + rear (cam2, 0.90) during departure [t3, t3+4s]
        h1_frames: list[MultimodalFrame] = []
        w_start = t3
        w_end = t3 + 4.0
        for f in frames:
            if w_start <= f.master_timestamp_s <= w_end:
                v_recs = list(f.vision_records) + [
                    EvidenceRecord(
                        timestamp_s=f.master_timestamp_s,
                        source_id="camera_1",
                        modality=Modality.VISION,
                        available=True,
                        detections=(Detection(label="front", confidence=0.90),),
                    ),
                    EvidenceRecord(
                        timestamp_s=f.master_timestamp_s,
                        source_id="camera_2",
                        modality=Modality.VISION,
                        available=True,
                        detections=(Detection(label="rear", confidence=0.90),),
                    ),
                ]
                h1_frames.append(replace(f, vision_records=tuple(v_recs)))
            else:
                h1_frames.append(f)

        res_h1, _ = simulate_frames(
            h1_frames,
            event_id=ev_id,
            scenario_name="H1_conflicting_front_and_rear",
            policy="v2",
            config=ctx.frozen_config,
            entry_time_s=t1,
            clearance_time_s=t4,
        )
        perturbation_rows.append(
            _summarize_fault_run(
                group="EXP-H",
                scenario="H1_conflicting_front_and_rear",
                is_constructed_perturbation=True,
                event_id=ev_id,
                policy="v2",
                sim_res=res_h1,
                entry_s=t1,
                clearance_s=t4,
                extra={
                    "rule7_interrupt_count": sum(
                        1
                        for s in res_h1.steps
                        if s.decision.rule_id == "RULE_7_NEW_TRAIN_INTERRUPT"
                    )
                },
            )
        )

        # H2: Low-confidence cap (<0.35 vision) across whole event
        h2_frames: list[MultimodalFrame] = []
        for f in frames:
            capped_v = tuple(
                replace(
                    r,
                    detections=tuple(
                        replace(d, confidence=min(float(d.confidence), 0.34))
                        for d in r.detections
                    ),
                )
                for r in f.vision_records
            )
            h2_frames.append(replace(f, vision_records=capped_v))
        res_h2, _ = simulate_frames(
            h2_frames,
            event_id=ev_id,
            scenario_name="H2_subthreshold_vision_cap_034",
            policy="v2",
            config=ctx.frozen_config,
            entry_time_s=t1,
            clearance_time_s=t4,
        )
        perturbation_rows.append(
            _summarize_fault_run(
                group="EXP-H",
                scenario="H2_subthreshold_vision_cap_034",
                is_constructed_perturbation=True,
                event_id=ev_id,
                policy="v2",
                sim_res=res_h2,
                entry_s=t1,
                clearance_s=t4,
            )
        )

    # H3: High-confidence audio horn burst (0.95) in no_train IDLE controls (vs stateless_union)
    for ev_id in ("no_train_events/event_001", "no_train_events/event_002", "no_train_events/event_003"):
        recs, aligner, _ = load_event_evidence_records(ctx, ev_id, "B4")
        frames = assemble_frames(recs, aligner, stride_s=0.2, window_tolerance_s=0.5)
        burst_frames = [
            replace(
                f,
                audio_records=tuple(f.audio_records)
                + (
                    EvidenceRecord(
                        timestamp_s=f.master_timestamp_s,
                        source_id="audio_1",
                        modality=Modality.AUDIO,
                        available=True,
                        detections=(Detection(label="train_horn", confidence=0.95),),
                    ),
                ),
            )
            if 3.0 <= f.master_timestamp_s <= 6.0
            else f
            for f in frames
        ]
        for pol in ("v2", "stateless_union"):
            res_h3, _ = simulate_frames(
                burst_frames,
                event_id=ev_id,
                scenario_name=f"H3_audio_fp_burst_in_idle_{pol}",
                policy=pol,
                config=ctx.frozen_config,
            )
            perturbation_rows.append(
                _summarize_fault_run(
                    group="EXP-H",
                    scenario="H3_audio_fp_burst_in_idle",
                    is_constructed_perturbation=True,
                    event_id=ev_id,
                    policy=pol,
                    sim_res=res_h3,
                    entry_s=None,
                    clearance_s=None,
                )
            )

    return {"natural_audit_11_sync": natural_audit, "perturbations": perturbation_rows}


def run_exp_i_failure_modes(ctx: VerifiedExploratoryContext) -> list[dict[str, Any]]:
    """EXP-I: Systematic FailureInjector suite covering all 8 FailureMode enum modes."""
    rows: list[dict[str, Any]] = []
    for ev_id in sorted(ctx.accepted_sync_events):
        ref = ctx.references[ev_id]
        bounds = ref.boundaries_for_clock("master")
        t1, t4 = bounds["t1"], bounds["t4"]
        recs, aligner, _ = load_event_evidence_records(ctx, ev_id, "DUAL_VISION_AUDIO")
        frames = assemble_frames(recs, aligner, stride_s=0.2, window_tolerance_s=0.5)
        t_start = frames[0].master_timestamp_s
        t_end = frames[-1].master_timestamp_s
        t_mid = _mid_time(frames)
        dep_start = bounds["t3"] if bounds["t3"] is not None else t_mid
        cam1_stale_start = max(t_mid, 4.0)
        cam2_stale_start = max(dep_start, float(ref.back_offset_s or 0.0) + 3.5)

        schedules_map: list[tuple[str, list[FailureSchedule], bool]] = [
            (
                "I1_CAMERA_1_DROPOUT",
                [FailureSchedule(mode=FailureMode.CAMERA_1_DROPOUT, start_time_s=4.0, end_time_s=10.0)],
                False,
            ),
            (
                "I2_CAMERA_2_DROPOUT",
                [FailureSchedule(mode=FailureMode.CAMERA_2_DROPOUT, start_time_s=dep_start, end_time_s=dep_start + 5.0)],
                False,
            ),
            (
                "I3_DUAL_CAMERA_DROPOUT",
                [FailureSchedule(mode=FailureMode.DUAL_CAMERA_DROPOUT, start_time_s=t_mid, end_time_s=t_mid + 5.0)],
                False,
            ),
            (
                "I4_AUDIO_DROPOUT",
                [FailureSchedule(mode=FailureMode.AUDIO_DROPOUT, start_time_s=t_start, end_time_s=t_end)],
                False,
            ),
            (
                "I5_STALE_TIMESTAMPS_CAM1",
                [
                    FailureSchedule(
                        mode=FailureMode.STALE_TIMESTAMPS,
                        start_time_s=cam1_stale_start,
                        end_time_s=min(t_end, cam1_stale_start + 4.0),
                        target_source="camera_1",
                        parameters={"delay_s": 2.5},
                    )
                ],
                False,
            ),
            (
                "I6_STALE_TIMESTAMPS_CAM2",
                [
                    FailureSchedule(
                        mode=FailureMode.STALE_TIMESTAMPS,
                        start_time_s=cam2_stale_start,
                        end_time_s=min(t_end, cam2_stale_start + 4.0),
                        target_source="camera_2",
                        parameters={"delay_s": 2.5},
                    )
                ],
                False,
            ),
            (
                "I7_OUT_OF_ORDER_FRAMES",
                [
                    FailureSchedule(
                        mode=FailureMode.OUT_OF_ORDER_FRAMES,
                        start_time_s=t_mid,
                        end_time_s=min(t_end, t_mid + 3.0),
                    )
                ],
                True,
            ),
            (
                "I8_DROPPED_FRAMES_WINDOW",
                [
                    FailureSchedule(
                        mode=FailureMode.DROPPED_FRAMES,
                        start_time_s=t_mid,
                        end_time_s=min(t_end, t_mid + 1.6),
                    )
                ],
                False,
            ),
            (
                "I9_DROPPED_FRAMES_30PCT_SEED42",
                [
                    FailureSchedule(
                        mode=FailureMode.DROPPED_FRAMES,
                        start_time_s=t_start,
                        end_time_s=t_end,
                        parameters={"drop_rate": 0.30, "seed": 42},
                    )
                ],
                False,
            ),
        ]

        for scen_name, scheds, preserve_order in schedules_map:
            inj = FailureInjector(scheds)
            mutated = inj.inject_failures(frames)
            res, _ = simulate_frames(
                mutated,
                event_id=ev_id,
                scenario_name=scen_name,
                policy="v2",
                config=ctx.frozen_config,
                entry_time_s=t1,
                clearance_time_s=t4,
                preserve_arrival_order=preserve_order,
            )
            rows.append(
                _summarize_fault_run(
                    group="EXP-I",
                    scenario=scen_name,
                    is_constructed_perturbation=True,
                    event_id=ev_id,
                    policy="v2",
                    sim_res=res,
                    entry_s=t1,
                    clearance_s=t4,
                    extra={"preserve_arrival_order": preserve_order},
                )
            )

    # I10: FALSE_DETECTION single-tick spike on clean no_train controls (V2 vs Stateless)
    for ev_id in ("no_train_events/event_001", "no_train_events/event_002", "no_train_events/event_003"):
        recs, aligner, _ = load_event_evidence_records(ctx, ev_id, "B0")
        frames = assemble_frames(recs, aligner, stride_s=0.2, window_tolerance_s=0.5)
        inj_fd = FailureInjector(
            [
                FailureSchedule(
                    mode=FailureMode.FALSE_DETECTION,
                    start_time_s=4.0,
                    end_time_s=4.0,
                    parameters={"label": "front", "confidence": 0.99},
                )
            ]
        )
        mutated_fd = inj_fd.inject_failures(frames)
        for pol in ("v2", "stateless_vision_rule2"):
            res_fd, _ = simulate_frames(
                mutated_fd,
                event_id=ev_id,
                scenario_name=f"I10_FALSE_DETECTION_1TICK_{pol}",
                policy=pol,
                config=ctx.frozen_config,
            )
            rows.append(
                _summarize_fault_run(
                    group="EXP-I",
                    scenario="I10_FALSE_DETECTION_1TICK",
                    is_constructed_perturbation=True,
                    event_id=ev_id,
                    policy=pol,
                    sim_res=res_fd,
                    entry_s=None,
                    clearance_s=None,
                )
            )
    return rows


def run_exp_k_recovery_and_interrupt(ctx: VerifiedExploratoryContext) -> list[dict[str, Any]]:
    """EXP-K: Fault recovery (IDLE-origin vs active-crossing) + constructed multi-train interrupt."""
    rows: list[dict[str, Any]] = []

    # K1: IDLE-origin recovery on no_train_events (fault at [2.0, 5.0], clean frames through end >= 11s)
    for ev_id in ("no_train_events/event_001", "no_train_events/event_002", "no_train_events/event_003"):
        recs, aligner, _ = load_event_evidence_records(ctx, ev_id, "B0")
        frames = assemble_frames(recs, aligner, stride_s=0.2, window_tolerance_s=0.5)
        inj = FailureInjector(
            [FailureSchedule(mode=FailureMode.DUAL_CAMERA_DROPOUT, start_time_s=2.0, end_time_s=5.0)]
        )
        mutated = inj.inject_failures(frames)
        res, _ = simulate_frames(
            mutated,
            event_id=ev_id,
            scenario_name="K1_idle_fault_and_recovery",
            policy="v2",
            config=ctx.frozen_config,
        )
        entered_failsafe = any(
            s.crossing_state == CrossingState.FAULT_FAIL_SAFE.value for s in res.steps
        )
        recovered_to_idle = any(
            s.decision.previous_state == CrossingState.FAULT_FAIL_SAFE.value
            and s.decision.resulting_state == CrossingState.IDLE.value
            for s in res.steps
        )
        rows.append(
            _summarize_fault_run(
                group="EXP-K",
                scenario="K1_idle_fault_and_recovery",
                is_constructed_perturbation=True,
                event_id=ev_id,
                policy="v2",
                sim_res=res,
                entry_s=None,
                clearance_s=None,
                extra={
                    "entered_failsafe": entered_failsafe,
                    "recovered_to_idle": recovered_to_idle,
                    "rule9_recovery_steps": sum(
                        1 for s in res.steps if s.decision.rule_id == "RULE_9_SENSOR_RECOVERY"
                    ),
                },
            )
        )

    # K2: Active-crossing fault + sensor recovery while train remains present (all 11 sync events)
    # Also construct K3 multi-train re-interruption on the real prefixes that reach CROSSING_CLEAR
    for ev_id in sorted(ctx.accepted_sync_events):
        ref = ctx.references[ev_id]
        bounds = ref.boundaries_for_clock("master")
        t1, t4 = bounds["t1"], bounds["t4"]
        recs, aligner, _ = load_event_evidence_records(ctx, ev_id, "DUAL_VISION_AUDIO")
        frames = assemble_frames(recs, aligner, stride_s=0.2, window_tolerance_s=0.5)

        t_fault_start = (bounds["t2"] if bounds["t2"] is not None else 4.0) + 1.0
        t_fault_end = t_fault_start + 3.0
        inj = FailureInjector(
            [
                FailureSchedule(
                    mode=FailureMode.DUAL_CAMERA_DROPOUT,
                    start_time_s=t_fault_start,
                    end_time_s=t_fault_end,
                )
            ]
        )
        mutated = inj.inject_failures(frames)
        res_k2, _ = simulate_frames(
            mutated,
            event_id=ev_id,
            scenario_name="K2_active_fault_and_recovery",
            policy="v2",
            config=ctx.frozen_config,
            entry_time_s=t1,
            clearance_time_s=t4,
        )
        exited_failsafe_states = sorted(
            {
                s.decision.resulting_state
                for s in res_k2.steps
                if s.decision.previous_state == CrossingState.FAULT_FAIL_SAFE.value
                and s.decision.resulting_state != CrossingState.FAULT_FAIL_SAFE.value
            }
        )
        rows.append(
            _summarize_fault_run(
                group="EXP-K",
                scenario="K2_active_fault_and_recovery",
                is_constructed_perturbation=True,
                event_id=ev_id,
                policy="v2",
                sim_res=res_k2,
                entry_s=t1,
                clearance_s=t4,
                extra={
                    "entered_failsafe": any(
                        s.crossing_state == CrossingState.FAULT_FAIL_SAFE.value for s in res_k2.steps
                    ),
                    "exited_failsafe_to": exited_failsafe_states,
                    "rule9_recovery_steps": sum(
                        1 for s in res_k2.steps if s.decision.rule_id == "RULE_9_SENSOR_RECOVERY"
                    ),
                },
            )
        )

        # K3: Check if baseline event reaches CROSSING_CLEAR / GATE_OPENING; if so, inject second approach after clear
        res_base, _ = simulate_frames(
            frames,
            event_id=ev_id,
            scenario_name="K3_check_clear",
            policy="v2",
            config=ctx.frozen_config,
            entry_time_s=t1,
            clearance_time_s=t4,
        )
        clear_t = next(
            (
                s.timestamp_s
                for s in res_base.steps
                if s.crossing_state in (CrossingState.CROSSING_CLEAR.value, CrossingState.GATE_OPENING.value)
            ),
            None,
        )
        if clear_t is not None:
            # Append/overwrite 10 ticks (2.0s) starting immediately at clear_t with unambiguous 'front' detections
            prefix = [f for f in frames if f.master_timestamp_s <= clear_t]
            second_wave: list[MultimodalFrame] = []
            for k in range(15):
                tk = round(clear_t + (k + 1) * 0.2, 6)
                second_wave.append(
                    MultimodalFrame(
                        master_timestamp_s=tk,
                        vision_records=(
                            EvidenceRecord(
                                timestamp_s=tk,
                                source_id="camera_1",
                                modality=Modality.VISION,
                                available=True,
                                detections=(Detection(label="front", confidence=0.88),),
                            ),
                            EvidenceRecord(
                                timestamp_s=tk,
                                source_id="camera_2",
                                modality=Modality.VISION,
                                available=True,
                                detections=(),
                            ),
                        ),
                        audio_records=(
                            EvidenceRecord(
                                timestamp_s=tk,
                                source_id="audio_1",
                                modality=Modality.AUDIO,
                                available=True,
                                detections=(),
                            ),
                        ),
                        source_availability={"camera_1": True, "camera_2": True, "audio_1": True},
                        active_sources=("camera_1", "camera_2", "audio_1"),
                    )
                )
            res_k3, _ = simulate_frames(
                prefix + second_wave,
                event_id=ev_id,
                scenario_name="K3_constructed_multi_train_interrupt",
                policy="v2",
                config=ctx.frozen_config,
                entry_time_s=t1,
                clearance_time_s=None,  # Second train arrives after first clearance
            )
            reinterrupted = any(
                s.decision.rule_id == "RULE_7_NEW_TRAIN_INTERRUPT" and s.timestamp_s >= clear_t
                for s in res_k3.steps
            )
            reclosed = any(
                s.timestamp_s >= clear_t and s.is_passage_blocked
                for s in res_k3.steps
            )
            rows.append(
                _summarize_fault_run(
                    group="EXP-K",
                    scenario="K3_constructed_multi_train_interrupt",
                    is_constructed_perturbation=True,
                    event_id=ev_id,
                    policy="v2",
                    sim_res=res_k3,
                    entry_s=t1,
                    clearance_s=None,
                    extra={
                        "first_clear_t_s": round(float(clear_t), 6),
                        "reinterrupted_by_rule7": reinterrupted,
                        "reclosed_or_blocked_for_second_train": reclosed,
                    },
                )
            )
    return rows


def run_all_stress_suites(ctx: VerifiedExploratoryContext, *, output_dir: Path) -> dict[str, Any]:
    exp_g = run_exp_g_missing_modality(ctx)
    exp_h = run_exp_h_contradictory_evidence(ctx)
    exp_i = run_exp_i_failure_modes(ctx)
    exp_k = run_exp_k_recovery_and_interrupt(ctx)

    payload = {
        "exploratory_label": EXPLORATORY_LABEL,
        "manifest_sha256": ctx.manifest_sha256,
        "counts": {
            "exp_g_runs": len(exp_g),
            "exp_h_natural_audits": len(exp_h["natural_audit_11_sync"]),
            "exp_h_perturbation_runs": len(exp_h["perturbations"]),
            "exp_i_runs": len(exp_i),
            "exp_k_runs": len(exp_k),
        },
        "exp_g_missing_modality": exp_g,
        "exp_h_contradictory_evidence": exp_h,
        "exp_i_failure_modes": exp_i,
        "exp_k_recovery_and_interrupt": exp_k,
    }
    out_path = output_dir / "failure_injection" / "stress_and_recovery_results.json"
    sha = write_verified_json(out_path, payload)
    return {"output_path": str(out_path), "sha256": sha, **payload["counts"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run EXP-G/H/I/K robustness & recovery suite.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "results" / "exploratory_execution",
    )
    args = parser.parse_args(argv)
    ctx = load_verified_context(REPO_ROOT)
    summary = run_all_stress_suites(ctx, output_dir=args.output_dir)
    print(
        f"[DONE] EXP-G={summary['exp_g_runs']}, EXP-H_pert={summary['exp_h_perturbation_runs']}, "
        f"EXP-I={summary['exp_i_runs']}, EXP-K={summary['exp_k_runs']}, sha256={summary['sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
