#!/usr/bin/env python3
"""Exploratory cache-only replay driver covering B0, B1 (BACK_VISION), B2 (DUAL_VISION),
B3 (AUDIO_ONLY), B4 (FRONT_AUDIO), B7 (DUAL_VISION_AUDIO), and EXP-E Stateless comparators.

Strictly bound to researcher-adopted AI-assisted annotations under
`RESEARCHER_ANNOTATION_ADOPTION.json`. Never reads raw media or bypasses canonical Stage-2.1 gates.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Allow running directly from repo root or script directory without editable install
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SCRIPTS_DIR = REPO_ROOT / "scripts"
for p in (str(SRC_DIR), str(SCRIPTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from exploratory_common import (  # noqa: E402
    DUAL_CONDITIONS,
    EXPLORATORY_LABEL,
    ExploratoryValidationError,
    VerifiedExploratoryContext,
    assemble_frames,
    load_event_evidence_records,
    load_verified_context,
    serialize_simulation_result,
    simulate_frames,
    write_verified_json,
)

from railway_detection.evaluation.metrics import (  # noqa: E402
    EventMetricsCalculator,
    classify_m4,
)
from railway_detection.fusion.rules import CrossingState  # noqa: E402

DEFAULT_RUN_SPECS: list[tuple[str, str, str, str]] = [
    # (run_label, condition, policy, scope_mode)
    ("B0__v2", "B0", "v2", "all27"),
    ("B0__v1", "B0", "v1", "all27"),
    ("B0__stateless_rule2", "B0", "stateless_vision_rule2", "all27"),
    ("BACK_VISION__v2", "BACK_VISION", "v2", "all27"),
    ("BACK_VISION__v1", "BACK_VISION", "v1", "all27"),
    ("AUDIO_ONLY__v2", "AUDIO_ONLY", "v2", "all27"),
    ("FRONT_AUDIO__v2", "B4", "v2", "all27"),
    ("FRONT_AUDIO__v1", "B4", "v1", "all27"),
    ("FRONT_AUDIO__stateless_rule2", "B4", "stateless_vision_rule2", "all27"),
    ("FRONT_AUDIO__stateless_union", "B4", "stateless_union", "all27"),
    ("DUAL_VISION__v2", "DUAL_VISION", "v2", "sync11"),
    ("DUAL_VISION__v1", "DUAL_VISION", "v1", "sync11"),
    ("DUAL_VISION_AUDIO__v2", "DUAL_VISION_AUDIO", "v2", "sync11"),
    ("DUAL_VISION_AUDIO__v1", "DUAL_VISION_AUDIO", "v1", "sync11"),
    ("DUAL_VISION_AUDIO__stateless_rule2", "DUAL_VISION_AUDIO", "stateless_vision_rule2", "sync11"),
    ("DUAL_VISION_AUDIO__stateless_union", "DUAL_VISION_AUDIO", "stateless_union", "sync11"),
]


def _verify_fail_closed_dual_guard(ctx: VerifiedExploratoryContext) -> dict[str, Any]:
    """Prove that uncalibrated/unaccepted events fail closed under DUAL_* conditions."""
    checks = []
    for test_ev in ("train_events/event_010", "train_events/event_003", "no_train_events/event_001"):
        blocked = False
        err_msg = ""
        try:
            load_event_evidence_records(ctx, test_ev, "DUAL_VISION_AUDIO")
        except ExploratoryValidationError as exc:
            blocked = True
            err_msg = str(exc)
        if not blocked:
            raise ExploratoryValidationError(
                f"Fail-closed check failed: {test_ev} was unexpectedly allowed in DUAL mode"
            )
        checks.append({"event_id": test_ev, "blocked": blocked, "reason": err_msg})
    return {"all_unaccepted_blocked": True, "checks": checks}


def _evaluate_event_metrics(
    sim_res: Any,
    *,
    ref: Any,
    mapped_bounds: dict[str, float | None],
    condition: str,
) -> dict[str, Any]:
    is_train = ref.cohort == "train_events"
    is_engine = ref.cohort == "engine_events"
    evaluable = not is_engine
    has_train_gt = is_train

    eval_obj = EventMetricsCalculator.evaluate_run(
        sim_res,
        entry_time_s=mapped_bounds["t1"] if is_train else None,
        clearance_time_s=mapped_bounds["t4"] if is_train else None,
        has_train_ground_truth=has_train_gt,
        evaluable=evaluable,
        ground_truth_status="exploratory_researcher_adopted_ai_reference",
        cohort=ref.cohort,
        premature_opening_window="first_blocked_to_t4_clearance",
        first_visible_time_s=mapped_bounds["t0"] if is_train else None,
        first_visible_left_censored=ref.t0_ambiguity,
    )
    m4_obj = (
        classify_m4(sim_res, mapped_bounds["t4"])
        if is_train and mapped_bounds["t4"] is not None
        else None
    )

    first_blocked_t = next(
        (round(float(s.timestamp_s), 6) for s in sim_res.steps if s.is_passage_blocked),
        None,
    )
    first_close_cmd_t = next(
        (
            round(float(s.timestamp_s), 6)
            for s in sim_res.steps
            if s.crossing_state in (CrossingState.WARNING.value, CrossingState.GATE_CLOSING.value, CrossingState.TRAIN_PRESENT.value)
        ),
        None,
    )
    first_clear_t = next(
        (
            round(float(s.timestamp_s), 6)
            for s in sim_res.steps
            if s.crossing_state == CrossingState.CROSSING_CLEAR.value
        ),
        None,
    )
    first_open_after_clear_t = None
    if first_clear_t is not None:
        first_open_after_clear_t = next(
            (
                round(float(s.timestamp_s), 6)
                for s in sim_res.steps
                if s.timestamp_s >= first_clear_t and not s.is_passage_blocked
            ),
            None,
        )

    first_open_after_block_t = None
    if m4_obj is not None and m4_obj.first_blocked_s is not None:
        first_open_after_block_t = next(
            (
                round(float(s.timestamp_s), 6)
                for s in sim_res.steps
                if s.timestamp_s > m4_obj.first_blocked_s and not s.is_passage_blocked
            ),
            None,
        )
    m4_margin_s = (
        round(first_open_after_block_t - float(mapped_bounds["t4"]), 6)
        if (first_open_after_block_t is not None and mapped_bounds["t4"] is not None)
        else None
    )

    blocked_steps = sum(1 for s in sim_res.steps if s.is_passage_blocked)
    false_alarm = bool((eval_obj.closure_episodes or 0) > 0) if not has_train_gt else None
    blocked_sec_val = (
        round(float(eval_obj.blocked_seconds), 6)
        if eval_obj.blocked_seconds is not None
        else round(float(sim_res.closed_duration_s), 6)
    )
    closed_total_val = (
        round(float(eval_obj.total_closed_s), 6)
        if eval_obj.total_closed_s is not None
        else round(float(sim_res.closed_duration_s), 6)
    )
    return {
        "evaluable": eval_obj.evaluable,
        "has_train_ground_truth": eval_obj.has_train_ground_truth,
        "missed_train": eval_obj.missed_train,
        "false_alarm": false_alarm,
        "closure_episodes": eval_obj.closure_episodes,
        "blocked_seconds": blocked_sec_val,
        "premature_opening_m4": eval_obj.premature_opening,
        "premature_opening_status": eval_obj.m4_status,
        "premature_opening_reason": eval_obj.m4_reason,
        "m4_status_detail": str(m4_obj.status) if m4_obj is not None else "NO_T4_ON_CLOCK",
        "m4_margin_s": m4_margin_s,
        "m4_first_open_s": first_open_after_block_t,
        "never_protected": eval_obj.never_protected,
        "warning_lead_time_s": (
            round(float(eval_obj.warning_lead_time_s), 6)
            if eval_obj.warning_lead_time_s is not None
            else None
        ),
        "first_close_cmd_s": first_close_cmd_t,
        "first_blocked_s": first_blocked_t,
        "first_crossing_clear_s": first_clear_t,
        "first_unblocked_after_clear_s": first_open_after_clear_t,
        "closed_duration_s": closed_total_val,
        "total_duration_s": round(float(sim_res.total_duration_s), 6),
        "blocked_fraction": round(blocked_steps / len(sim_res.steps), 6) if sim_res.steps else 0.0,
        "condition": condition,
    }


def _clock_for_boundaries(condition: str, is_dual_sync_accepted: bool) -> str:
    if condition in DUAL_CONDITIONS:
        return "master"
    if condition == "BACK_VISION":
        return "back"
    # For single-camera front / front+audio runs on the 11 sync-supported events,
    # front local clock IS the master clock, so T4_back + back_offset_s CAN be placed on master!
    if is_dual_sync_accepted:
        return "master"
    return "front"


def run_all_exploratory_replays(
    ctx: VerifiedExploratoryContext,
    *,
    output_dir: Path,
    run_specs: list[tuple[str, str, str, str]] | None = None,
    stride_s: float = 0.2,
    window_tolerance_s: float = 0.5,
) -> dict[str, Any]:
    specs = run_specs or DEFAULT_RUN_SPECS
    guard_check = _verify_fail_closed_dual_guard(ctx)
    traces_dir = output_dir / "replays" / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, Any]] = []
    trace_hashes: dict[str, str] = {}

    for run_label, condition, policy, scope_mode in specs:
        target_events = (
            [ev for ev in ctx.event_order if ev in ctx.accepted_sync_events]
            if scope_mode == "sync11"
            else list(ctx.event_order)
        )
        for ev_id in target_events:
            ref = ctx.references[ev_id]
            records, aligner, stream_clock = load_event_evidence_records(ctx, ev_id, condition)
            frames = assemble_frames(
                records,
                aligner,
                stride_s=stride_s,
                window_tolerance_s=window_tolerance_s,
            )
            bound_clock = _clock_for_boundaries(condition, ref.is_dual_sync_accepted)
            mapped_bounds = ref.boundaries_for_clock(bound_clock)

            sim_res, _ = simulate_frames(
                frames,
                event_id=ev_id,
                scenario_name=f"exploratory_{run_label}",
                policy=policy,
                config=ctx.frozen_config,
                entry_time_s=mapped_bounds["t1"] if ref.cohort == "train_events" else None,
                clearance_time_s=mapped_bounds["t4"] if ref.cohort == "train_events" else None,
            )
            trace_payload = serialize_simulation_result(
                sim_res,
                event_id=ev_id,
                condition=condition,
                policy=policy,
                clock_mode=stream_clock,
                ref=ref,
                mapped_bounds=mapped_bounds,
                window_tolerance_s=window_tolerance_s,
                stride_s=stride_s,
            )
            eval_metrics = _evaluate_event_metrics(
                sim_res, ref=ref, mapped_bounds=mapped_bounds, condition=condition
            )
            trace_payload["evaluation_metrics"] = eval_metrics

            rel_trace = f"replays/traces/{run_label}__{ref.event_key}.json"
            trace_sha = write_verified_json(output_dir / rel_trace, trace_payload)
            trace_hashes[rel_trace] = trace_sha

            summary_rows.append(
                {
                    "run_label": run_label,
                    "condition": condition,
                    "policy": policy,
                    "scope_mode": scope_mode,
                    "event_id": ev_id,
                    "event_key": ref.event_key,
                    "cohort": ref.cohort,
                    "is_dual_sync_accepted": ref.is_dual_sync_accepted,
                    "boundary_clock": bound_clock,
                    "trace_relpath": rel_trace,
                    "trace_sha256": trace_sha,
                    "final_crossing_state": trace_payload["final_crossing_state"],
                    "final_gate_state": trace_payload["final_gate_state"],
                    "reached_crossing_clear": trace_payload["reached_crossing_clear"],
                    "reached_gate_opening": trace_payload["reached_gate_opening"],
                    "transition_count": len(trace_payload["transitions"]),
                    "rule_counts": trace_payload["rule_counts"],
                    "mapped_boundaries": mapped_bounds,
                    **eval_metrics,
                }
            )

    # Sensitivity check at window_tolerance_s = 0.25 (matching historical Phase 10.1 parameter)
    wt_sensitivity: list[dict[str, Any]] = []
    for ev_id in sorted(ctx.accepted_sync_events):
        ref = ctx.references[ev_id]
        records, aligner, _ = load_event_evidence_records(ctx, ev_id, "DUAL_VISION_AUDIO")
        frames_025 = assemble_frames(records, aligner, stride_s=stride_s, window_tolerance_s=0.25)
        bounds = ref.boundaries_for_clock("master")
        for pol in ("v1", "v2"):
            res_025, _ = simulate_frames(
                frames_025,
                event_id=ev_id,
                scenario_name=f"wt025_{pol}",
                policy=pol,
                config=ctx.frozen_config,
                entry_time_s=bounds["t1"],
                clearance_time_s=bounds["t4"],
            )
            ev_025 = _evaluate_event_metrics(
                res_025, ref=ref, mapped_bounds=bounds, condition="DUAL_VISION_AUDIO"
            )
            wt_sensitivity.append(
                {
                    "event_id": ev_id,
                    "policy": pol,
                    "window_tolerance_s": 0.25,
                    "reached_crossing_clear": any(
                        s.crossing_state == CrossingState.CROSSING_CLEAR.value for s in res_025.steps
                    ),
                    "premature_opening_m4": ev_025["premature_opening_m4"],
                    "m4_margin_s": ev_025["m4_margin_s"],
                    "closed_duration_s": ev_025["closed_duration_s"],
                }
            )

    manifest_out = {
        "exploratory_label": EXPLORATORY_LABEL,
        "manifest_sha256": ctx.manifest_sha256,
        "stride_s": stride_s,
        "window_tolerance_s": window_tolerance_s,
        "fail_closed_dual_guard": guard_check,
        "total_runs": len(summary_rows),
        "runs": summary_rows,
        "window_tolerance_025_sensitivity": wt_sensitivity,
        "trace_hashes": dict(sorted(trace_hashes.items())),
    }
    manifest_sha = write_verified_json(output_dir / "replays" / "replay_summary.json", manifest_out)
    return {
        "replay_summary_sha256": manifest_sha,
        "total_runs": len(summary_rows),
        "trace_count": len(trace_hashes),
        "output_dir": str(output_dir),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run exploratory precomputed cache replays.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "results" / "exploratory_execution",
        help="Destination directory for replay outputs.",
    )
    parser.add_argument(
        "--conditions",
        type=str,
        default="",
        help="Optional comma-separated run_labels filter (e.g., B0__v2,DUAL_VISION_AUDIO__v2).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Verify cryptographic manifests only.")
    args = parser.parse_args(argv)

    ctx = load_verified_context(REPO_ROOT)
    print(f"[VERIFIED] {EXPLORATORY_LABEL}")
    print(f"[VERIFIED] 27 events, {len(ctx.accepted_sync_events)} sync-accepted, manifest={ctx.manifest_sha256[:12]}...")

    if args.dry_run:
        guard = _verify_fail_closed_dual_guard(ctx)
        print(f"[DRY-RUN] Fail-closed DUAL guard checks passed: {len(guard['checks'])}")
        return 0

    specs = DEFAULT_RUN_SPECS
    if args.conditions.strip():
        wanted = {c.strip() for c in args.conditions.split(",") if c.strip()}
        specs = [s for s in DEFAULT_RUN_SPECS if s[0] in wanted]
        if not specs:
            raise SystemExit(f"No matching run_labels for: {wanted}")

    out = run_all_exploratory_replays(ctx, output_dir=args.output_dir, run_specs=specs)
    print(f"[DONE] total_runs={out['total_runs']}, trace_count={out['trace_count']}, sha256={out['replay_summary_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
