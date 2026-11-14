"""Deterministic synthetic scenarios, fault injections (17 scenarios), and CPU media-pipeline verification."""

from __future__ import annotations

import math
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from railway_detection.audio.features import compute_log_mel_spectrogram
from railway_detection.config.exceptions import ConfigError
from railway_detection.data.sync import SyncAligner
from railway_detection.demo.video_demo import process_video
from railway_detection.experiments.frozen_config import load_frozen_config
from railway_detection.fusion.collector import MultimodalEvidenceCollector, MultimodalFrame
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.decision_engine_v2_candidate import MultimodalDecisionEngineV2Candidate
from railway_detection.fusion.decision_engine_v3_four_layer import MultimodalDecisionEngineV3FourLayer
from railway_detection.fusion.evidence import (
    Detection,
    EvidenceRecord,
    Modality,
    OccupancyEvidence,
    OccupancyState,
)
from railway_detection.fusion.rules import CrossingState, GateState, RuleId
from railway_detection.fusion.rules_v3_four_layer import DeparturePolicyMode
from railway_detection.safety.media_guard import require_media_command_authorization
from railway_detection.simulation.runner import EventSimulationRunner, SimulationRunResult
from railway_detection.simulation.state_machine import ALLOWED_TRANSITIONS
from railway_detection.vision.video import SOURCE_DISPLAY_ROTATION_POLICY, frame_generator


def check_transition_legality(result: SimulationRunResult) -> dict[str, Any]:
    """Verify every adjacent state transition obeys ALLOWED_TRANSITIONS."""
    illegal: list[dict[str, Any]] = []
    for step in result.steps:
        prev_s = CrossingState(step.decision.previous_state)
        next_s = CrossingState(step.decision.resulting_state)
        if next_s not in ALLOWED_TRANSITIONS.get(prev_s, set()):
            illegal.append(
                {
                    "timestamp_s": round(step.timestamp_s, 6),
                    "from": prev_s.value,
                    "to": next_s.value,
                    "rule_id": step.decision.rule_id,
                }
            )
    return {
        "legal": len(illegal) == 0,
        "illegal_transitions": illegal,
        "step_count": len(result.steps),
    }


def verify_synthetic_video_orientation_and_yolo(
    repo_root: Path,
) -> dict[str, Any]:
    """Verify FFmpeg display_rotation {0,90,-90,180,-180,270,-270} across PyAV, OpenCV, video_demo, and YOLOv8n."""
    from ultralytics import YOLO

    angles = [0, 90, -90, 180, -180, 270, -270]
    ckpt = repo_root / "experiments/vision/39f402dfe460/checkpoints/weights/best.pt"
    if not ckpt.exists():
        raise FileNotFoundError(f"Missing YOLO checkpoint at {ckpt}")

    model = YOLO(str(ckpt.resolve()))
    results_per_angle: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="ta_rot_verify_") as tmp:
        tmp_dir = Path(tmp)
        # Target upright display portrait (48x80 wxh -> H=80, W=48): distinct marker in top-left quadrant
        upright_h, upright_w = 80, 48
        upright_ref = np.full((upright_h, upright_w, 3), 24, dtype=np.uint8)
        upright_ref[6:22, 6:18] = (20, 40, 235)   # Top-left bright red block (BGR)
        upright_ref[56:72, 28:42] = (30, 220, 40) # Bottom-right green block (BGR)
        upright_ref[34:46, 10:38] = (220, 180, 30)

        for deg in angles:
            # Generate pre-rotated coded stream so after applying FFmpeg display_rotation `deg`,
            # the displayed upright frame matches upright_ref cleanly.
            # PyAV applies np.rot90(raw, k=(deg // 90) % 4). So raw = np.rot90(upright_ref, k=(-(deg // 90)) % 4).
            k_inv = (-(deg // 90)) % 4
            coded_img = np.ascontiguousarray(np.rot90(upright_ref, k=k_inv))
            coded_h, coded_w = coded_img.shape[:2]

            raw_avi = tmp_dir / f"raw_{deg}.avi"
            out_mp4 = tmp_dir / f"rotated_{deg}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            writer = cv2.VideoWriter(str(raw_avi), fourcc, 10.0, (coded_w, coded_h))
            for _ in range(4):
                writer.write(coded_img)
            writer.release()

            cmd = [
                "ffmpeg",
                "-y",
                "-display_rotation:v:0",
                str(deg),
                "-i",
                str(raw_avi),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(out_mp4),
            ]
            require_media_command_authorization(cmd, "READ_RAW_MEDIA")
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                raise RuntimeError(f"ffmpeg failed for deg={deg}: {proc.stderr[-300:]}")

            pyav_frames = list(
                frame_generator(
                    out_mp4,
                    source_pts=True,
                )
            )
            cv_frames = list(
                frame_generator(
                    out_mp4,
                    source_pts=False,
                )
            )
            assert len(pyav_frames) == 4 and len(cv_frames) == 4
            py_img = pyav_frames[0].image
            cv_img = cv_frames[0].image
            mae_py_vs_cv = float(np.mean(np.abs(py_img.astype(np.float32) - cv_img.astype(np.float32))))
            mae_py_vs_ref = float(
                np.mean(np.abs(py_img.astype(np.float32) - upright_ref.astype(np.float32)))
            )

            # Verify YOLOv8n executes cleanly on oriented tensor (CPU)
            t0 = time.perf_counter()
            yolo_out = list(model.predict(source=py_img, conf=0.25, device="cpu", verbose=False))
            yolo_ms = (time.perf_counter() - t0) * 1000.0

            # Also verify video_demo handles rotated stream without VideoWriter dimension mismatch
            demo_dir = tmp_dir / f"demo_{deg}"
            demo_dir.mkdir(parents=True, exist_ok=True)
            demo_summary = process_video(
                input_path=out_mp4,
                output_dir=demo_dir,
                model_path=ckpt,
                conf_threshold=0.35,
                device="cpu",
                temporal_smoothing=True,
                live_preview=False,
            )

            results_per_angle.append(
                {
                    "display_rotation_deg": deg,
                    "coded_wh": [coded_w, coded_h],
                    "pyav_shape_hwc": list(py_img.shape),
                    "cv_shape_hwc": list(cv_img.shape),
                    "mae_pyav_vs_opencv": round(mae_py_vs_cv, 4),
                    "mae_pyav_vs_upright_ref": round(mae_py_vs_ref, 4),
                    "orientation_matches_upright": py_img.shape[:2] == (upright_h, upright_w)
                    and cv_img.shape[:2] == (upright_h, upright_w)
                    and mae_py_vs_cv < 3.0
                    and mae_py_vs_ref < 15.0,
                    "yolo_inference_ok": len(yolo_out) == 1,
                    "video_demo_wh": [demo_summary.width, demo_summary.height],
                    "video_demo_frames": demo_summary.processed_frames,
                    "video_demo_orientation_ok": (demo_summary.width, demo_summary.height)
                    == (upright_w, upright_h),
                }
            )

    return {
        "classification": "SYNTHETIC_PIPELINE_VERIFICATION",
        "rotation_policy": SOURCE_DISPLAY_ROTATION_POLICY,
        "checkpoint": str(ckpt.relative_to(repo_root)),
        "angles_tested": angles,
        "all_angles_passed": all(
            r["orientation_matches_upright"] and r["yolo_inference_ok"] and r["video_demo_orientation_ok"]
            for r in results_per_angle
        ),
        "results": results_per_angle,
        "real_raw_media_status": "BLOCKED_BY_DESIGN_MISSING_AUTH_MEDIA_ACCESS_JSON",
    }


def verify_audio_v3_transform_and_scenarios(repo_root: Path) -> dict[str, Any]:
    """Verify V3 natural log-Mel transform invariant and synthetic audio scenarios."""
    sr = 16000
    duration_s = 1.0
    t = np.linspace(0.0, duration_s, int(sr * duration_s), endpoint=False, dtype=np.float32)
    # Two-tone synthetic locomotive horn (370 Hz + 440 Hz + harmonic) vs silence & broadband noise
    horn_wave = (0.4 * np.sin(2 * np.pi * 370 * t) + 0.35 * np.sin(2 * np.pi * 440 * t)).astype(
        np.float32
    )
    rng = np.random.default_rng(42)
    noise_wave = (0.05 * rng.standard_normal(len(t))).astype(np.float32)

    nat_horn = compute_log_mel_spectrogram(horn_wave, sample_rate=sr, log_scale="natural")
    db_horn = compute_log_mel_spectrogram(horn_wave, sample_rate=sr, log_scale="db")
    nat_noise = compute_log_mel_spectrogram(noise_wave, sample_rate=sr, log_scale="natural")

    return {
        "classification": "SYNTHETIC_AUDIO_TRANSFORM_VERIFICATION",
        "sample_rate_hz": sr,
        "window_s": duration_s,
        "natural_shape": list(nat_horn.shape),
        "natural_finite": bool(np.all(np.isfinite(nat_horn))),
        "db_finite": bool(np.all(np.isfinite(db_horn))),
        "natural_differs_from_db_by_scale": float(np.mean(np.abs(db_horn - nat_horn))) > 5.0,
        "horn_mean_natural_log_mel": round(float(np.mean(nat_horn)), 4),
        "noise_mean_natural_log_mel": round(float(np.mean(nat_noise)), 4),
        "checkpoint_present": (
            repo_root / "experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt"
        ).exists(),
    }


def _collect_causal(
    records: list[EvidenceRecord],
    *,
    occupancy: list[OccupancyEvidence] | None = None,
    t_end: float = 20.0,
    stride_s: float = 0.2,
    window_tolerance_s: float = 0.5,
    aligner: SyncAligner | None = None,
    event_id: str | None = None,
) -> tuple[list[MultimodalFrame], list[dict[str, object]]]:
    collector = MultimodalEvidenceCollector(
        sync_aligner=aligner,
        window_tolerance_s=window_tolerance_s,
        event_id=event_id,
        allow_stale_detection_backfill=False,
    )
    collector.add_evidence_batch(records, preserve_arrival_order=True)
    if occupancy:
        for occ in occupancy:
            collector.add_occupancy(occ)
    frames = collector.generate_frames_from_history(0.0, t_end, stride_s=stride_s)
    return frames, list(collector.rejected_observations)


def _run_v3(
    frames: list[MultimodalFrame],
    *,
    name: str,
    entry_time_s: float | None = None,
    clearance_time_s: float | None = None,
    engine_kwargs: dict[str, Any] | None = None,
    preserve_arrival_order: bool = False,
) -> tuple[SimulationRunResult, MultimodalDecisionEngineV3FourLayer, float]:
    engine = MultimodalDecisionEngineV3FourLayer(**(engine_kwargs or {}))
    runner = EventSimulationRunner(decision_engine=engine)
    t0 = time.perf_counter()
    res = runner.run_frames(
        frames,
        event_id=f"synthetic/{name}",
        scenario_name=name,
        entry_time_s=entry_time_s,
        clearance_time_s=clearance_time_s,
        preserve_arrival_order=preserve_arrival_order,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return res, engine, round(elapsed_ms, 3)


def _baseline_nominal_streams(
    *,
    include_side: bool = True,
    include_last_carriage: bool = True,
    include_occupancy: bool = True,
    t_end: float = 24.0,
) -> tuple[list[EvidenceRecord], list[OccupancyEvidence]]:
    """Nominal 4-layer synthetic crossing:
    - Approach [1.0, 5.0]
    - Side moving [4.0, 11.0]
    - Audio horn [1.4, 9.0]
    - Back train + rear [8.0, 12.6], last_carriage [12.2, 12.6]
    - Occupancy OCCUPIED [4.0, 12.8], CLEAR [13.0, t_end]
    Ground-truth occupancy/danger interval: entry=3.0s, clearance=13.0s.
    """
    records: list[EvidenceRecord] = []
    occ: list[OccupancyEvidence] = []
    n_ticks = int(round(t_end / 0.2)) + 1
    for i in range(n_ticks):
        t = round(i * 0.2, 4)
        front_dets: tuple[Detection, ...] = (
            (Detection("front", 0.90, (100.0, 50.0, 220.0, 180.0)),)
            if 1.0 <= t <= 5.0
            else ()
        )
        records.append(EvidenceRecord(t, "camera_1", Modality.VISION, True, front_dets))

        if include_side:
            if 4.0 <= t <= 11.0:
                shift = (t - 4.0) * 18.0
                side_dets: tuple[Detection, ...] = (
                    Detection("side", 0.88, (40.0 + shift, 60.0, 140.0 + shift, 160.0)),
                )
            else:
                side_dets = ()
            records.append(EvidenceRecord(t, "camera_side", Modality.VISION, True, side_dets))

        back_dets: list[Detection] = []
        if 8.0 <= t <= 12.0:
            shift_b = (t - 8.0) * 18.0
            back_dets.append(
                Detection("side", 0.84, (80.0 + shift_b, 50.0, 175.0 + shift_b, 145.0))
            )
        if 11.8 <= t <= 12.6:
            back_dets.append(Detection("rear", 0.89, (90.0, 55.0, 195.0, 165.0)))
        if include_last_carriage and 12.2 <= t <= 12.6:
            back_dets.append(
                Detection("last_carriage", 0.91, (100.0, 60.0, 185.0, 160.0), {"last_carriage": True})
            )
        records.append(EvidenceRecord(t, "camera_2", Modality.VISION, True, tuple(back_dets)))

        if include_occupancy:
            if 4.0 <= t < 13.0:
                occ.append(OccupancyEvidence(t, "occ_loop_1", OccupancyState.OCCUPIED, True, 0.98))
            else:
                occ.append(OccupancyEvidence(t, "occ_loop_1", OccupancyState.CLEAR, True, 0.99))

    # Audio stream at realistic 0.5 s hop matching Layer 3 cache cadence
    n_audio = int(round(t_end / 0.5)) + 1
    for k in range(n_audio):
        ta = round(k * 0.5, 4)
        audio_dets = (Detection("train_horn", 0.78),) if 1.4 <= ta <= 9.0 else ()
        records.append(EvidenceRecord(ta, "audio_1", Modality.AUDIO, True, audio_dets))

    return records, occ


def run_synthetic_suite(*, include_traces: bool = False) -> dict[str, Any]:
    """Run controlled synthetic experiments for Exp B, Exp D, Exp E, Exp I, and all 17 Exp L scenarios."""
    aligner = SyncAligner()
    for src in ("camera_1", "camera_side", "camera_2"):
        aligner.add_source(src, offset_s=0.0, uncertainty_s=0.0)

    traces_by_scenario: dict[str, Any] = {}

    def summarize(
        scenario_id: str,
        res: SimulationRunResult,
        engine: MultimodalDecisionEngineV3FourLayer,
        latency_ms: float,
        rejected_collector: list[dict[str, object]],
        expected: dict[str, Any],
    ) -> dict[str, Any]:
        legal = check_transition_legality(res)
        states_seen = sorted({s.crossing_state for s in res.steps})
        gate_states = sorted({s.gate_state for s in res.steps})
        first_warn = next((round(s.timestamp_s, 3) for s in res.steps if s.crossing_state == "WARNING"), None)
        first_close_cmd = next((round(s.timestamp_s, 3) for s in res.steps if s.gate_state in ("CLOSING", "CLOSED")), None)
        first_fault = next(
            (round(s.timestamp_s, 3) for s in res.steps if s.crossing_state == "FAULT_FAIL_SAFE" or s.decision.fault_status not in ("none", "")),
            None,
        )
        if include_traces:
            traces_by_scenario[scenario_id] = {
                "scenario_id": scenario_id,
                "classification": "SYNTHETIC_CONTROLLED_SCENARIO",
                "step_count": len(res.steps),
                "rejected_step_count": len(res.rejected_steps),
                "transitions": [
                    {
                        "t": round(float(s.timestamp_s), 6),
                        "from": s.decision.previous_state,
                        "to": s.decision.resulting_state,
                        "gate_state": s.gate_state,
                        "gate_angle_deg": round(float(s.gate_angle_deg), 4),
                        "rule_id": s.decision.rule_id,
                        "fault_status": s.decision.fault_status,
                    }
                    for s in res.steps
                    if s.decision.previous_state != s.decision.resulting_state
                ],
                "steps": [
                    {
                        "t": round(float(s.timestamp_s), 6),
                        "crossing_state": s.crossing_state,
                        "gate_state": s.gate_state,
                        "gate_angle_deg": round(float(s.gate_angle_deg), 4),
                        "rule_id": s.decision.rule_id,
                        "fault_status": s.decision.fault_status,
                        "source_availability": dict(sorted(s.decision.source_availability.items())),
                        "source_health": dict(sorted(s.decision.source_health.items())),
                    }
                    for s in res.steps
                ],
            }
        reopened = any(
            i > 0 and s.crossing_state == "GATE_OPENING"
            for i, s in enumerate(res.steps)
        )
        returned_idle = any(
            i > 5 and res.steps[i - 1].crossing_state == "GATE_OPENING" and s.crossing_state == "IDLE"
            for i, s in enumerate(res.steps)
        )
        fault_held_closed = all(
            s.gate_state in ("CLOSED", "CLOSING") or s.is_passage_blocked
            for s in res.steps
            if s.crossing_state == "FAULT_FAIL_SAFE"
        )
        return {
            "scenario_id": scenario_id,
            "classification": "SYNTHETIC_CONTROLLED_SCENARIO",
            "expected": expected,
            "closure_triggered": any(s.gate_state in ("CLOSING", "CLOSED") for s in res.steps),
            "premature_opening_detected": res.premature_opening_detected,
            "reopened": reopened,
            "returned_idle": returned_idle,
            "final_crossing_state": res.steps[-1].crossing_state if res.steps else "NONE",
            "final_gate_state": res.steps[-1].gate_state if res.steps else "NONE",
            "first_warning_s": first_warn,
            "first_close_cmd_s": first_close_cmd,
            "first_fault_detected_s": first_fault,
            "fault_held_closed_invariant": fault_held_closed,
            "states_visited": states_seen,
            "gate_states_visited": gate_states,
            "transition_legality": legal,
            "collector_rejected_count": len(rejected_collector),
            "runner_rejected_count": len(res.rejected_steps),
        }

    scenarios_out: list[dict[str, Any]] = []

    # 0. Nominal 4-layer baseline (Exp I synthetic clean full pass)
    rec0, occ0 = _baseline_nominal_streams()
    f0, r0 = _collect_causal(rec0, occupancy=occ0, aligner=aligner, t_end=24.0)
    res0, eng0, ms0 = _run_v3(f0, name="nominal_4layer", entry_time_s=6.5, clearance_time_s=13.0)
    scenarios_out.append(
        summarize("00_nominal_4layer_full_cycle", res0, eng0, ms0, r0, {"closure": True, "reopened": True, "premature": False})
    )

    # Helper to drop or alter streams from nominal
    def mutate_records(filter_fn, extra_occ=None, t_end=24.0, entry=6.5, clr=13.0, engine_kwargs=None, name="s", expected=None, reorder_frames=False):
        recs, occ = _baseline_nominal_streams(t_end=t_end)
        recs_m, occ_m = filter_fn(recs, occ)
        if extra_occ is not None:
            occ_m = extra_occ
        frames, rej = _collect_causal(recs_m, occupancy=occ_m, aligner=aligner, t_end=t_end)
        if reorder_frames and len(frames) > 15:
            # Inject an out-of-order and duplicate frame directly into runner
            frames = list(frames)
            frames.insert(15, frames[10])  # OOO
            frames.insert(12, frames[12])  # duplicate
        res, eng, ms = _run_v3(
            frames,
            name=name,
            entry_time_s=entry,
            clearance_time_s=clr,
            engine_kwargs=engine_kwargs,
            preserve_arrival_order=reorder_frames,
        )
        scenarios_out.append(summarize(name, res, eng, ms, rej, expected or {}))

    # 17 Part-6 Fault & Adversarial Scenarios
    # 1. Front-camera failure mid-IDLE / pre-approach
    mutate_records(
        lambda recs, occ: (
            [r for r in recs if r.source_id != "camera_1"]
            + [EvidenceRecord(round(i * 0.2, 4), "camera_1", Modality.VISION, False, ()) for i in range(121)],
            occ,
        ),
        name="01_front_camera_failure",
        entry=None,
        clr=None,
        expected={"fault_safe_clamp": True, "reopened": False},
    )
    # 2. Back-camera failure after approach & crossing (must NOT reopen!)
    mutate_records(
        lambda recs, occ: (
            [
                EvidenceRecord(r.timestamp_s, r.source_id, r.modality, False, ())
                if (r.source_id == "camera_2" and r.timestamp_s >= 9.0)
                else r
                for r in recs
            ],
            occ,
        ),
        name="02_back_camera_failure",
        expected={"closure": True, "reopened": False, "premature": False},
    )
    # 3. Side-camera failure during crossing (gate stays safely closed; back+occ handle rest cleanly or fail-safe)
    mutate_records(
        lambda recs, occ: (
            [
                EvidenceRecord(r.timestamp_s, r.source_id, r.modality, False, ())
                if (r.source_id == "camera_side" and 5.0 <= r.timestamp_s <= 10.0)
                else r
                for r in recs
            ],
            occ,
        ),
        name="03_side_camera_failure",
        expected={"closure": True, "premature": False},
    )
    # 4. Audio failure (stream unavailable; closure still works from front; silence doesn't falsely reopen)
    mutate_records(
        lambda recs, occ: (
            [
                EvidenceRecord(r.timestamp_s, r.source_id, r.modality, False, ())
                if r.source_id == "audio_1"
                else r
                for r in recs
            ],
            occ,
        ),
        name="04_audio_failure",
        expected={"closure": True, "premature": False},
    )
    # 5. Occupancy sensor failure / missing after crossing (must hold gate CLOSED, NEVER reopen)
    mutate_records(
        lambda recs, occ: (
            recs,
            [
                OccupancyEvidence(o.timestamp_s, o.source_id, OccupancyState.MISSING, False, None)
                if o.timestamp_s >= 10.0
                else o
                for o in occ
            ],
        ),
        name="05_occupancy_sensor_failure",
        expected={"closure": True, "reopened": False, "premature": False},
    )
    # 6. Stale observations (back & occupancy stop refreshing at t=11.0 before departure/clear)
    mutate_records(
        lambda recs, occ: (
            [r for r in recs if not (r.source_id == "camera_2" and r.timestamp_s > 11.0)],
            [o for o in occ if o.timestamp_s <= 11.0],
        ),
        name="06_stale_observations",
        expected={"closure": True, "reopened": False, "premature": False},
    )
    # 7. Out-of-order & duplicate timestamps
    mutate_records(
        lambda recs, occ: (recs, occ),
        name="07_out_of_order_and_duplicate_timestamps",
        reorder_frames=True,
        expected={"closure": True, "runner_rejected": 2, "premature": False},
    )
    # 8. Contradictory detections (Occupancy reports CLEAR while active vision & horn exist!)
    mutate_records(
        lambda recs, occ: (
            recs,
            [OccupancyEvidence(o.timestamp_s, o.source_id, OccupancyState.CLEAR, True, 0.99) for o in occ],
        ),
        name="08_contradictory_detections",
        expected={"closure": True, "reopened": False, "premature": False},
    )
    # 9. Model inference timeout (metadata inference_timeout=True during passage & departure)
    mutate_records(
        lambda recs, occ: (
            [
                EvidenceRecord(
                    r.timestamp_s,
                    r.source_id,
                    r.modality,
                    r.available,
                    r.detections,
                    {**r.metadata, "inference_timeout": True},
                )
                if (r.source_id == "camera_2" and r.timestamp_s >= 11.0)
                else r
                for r in recs
            ],
            occ,
        ),
        name="09_model_inference_timeout",
        expected={"closure": True, "reopened": False, "premature": False},
    )
    # 10. Missing frames / sparse back dropout (1 back frame then silent gap -> RULE_L4_BACK_SPARSE_DROPOUT_HOLD)
    mutate_records(
        lambda recs, occ: (
            [
                EvidenceRecord(r.timestamp_s, "camera_2", Modality.VISION, True, ())
                if (r.source_id == "camera_2" and r.timestamp_s > 12.0)
                else r
                for r in recs
                if not (r.source_id == "camera_2" and 8.2 <= r.timestamp_s <= 11.8)
            ],
            [OccupancyEvidence(o.timestamp_s, o.source_id, OccupancyState.CLEAR, True, 0.99) if o.timestamp_s >= 13.0 else o for o in occ],
        ),
        name="10_missing_frames_sparse_dropout",
        expected={"closure": True, "reopened": False},
    )
    # 11. Video stream termination mid-crossing
    mutate_records(
        lambda recs, occ: (
            [
                EvidenceRecord(r.timestamp_s, r.source_id, r.modality, True, (), {"stream_terminated": True})
                if (r.source_id == "camera_2" and abs(r.timestamp_s - 10.0) < 1e-6)
                else r
                for r in recs
                if not (r.source_id == "camera_2" and r.timestamp_s > 10.0)
            ],
            occ,
        ),
        name="11_video_stream_termination",
        expected={"closure": True, "reopened": False},
    )

    # 12. Multiple trains (second train arrives right as rear confirms / crossing clear at t=14.0!)
    def multi_train_mod(recs, occ):
        out_r = []
        for r in recs:
            if r.source_id == "camera_1" and 14.0 <= r.timestamp_s <= 18.0:
                out_r.append(
                    EvidenceRecord(
                        r.timestamp_s,
                        "camera_1",
                        Modality.VISION,
                        True,
                        (Detection("front", 0.93, (110.0, 50.0, 230.0, 180.0)),),
                    )
                )
            else:
                out_r.append(r)
        out_o = [
            OccupancyEvidence(o.timestamp_s, o.source_id, OccupancyState.OCCUPIED, True, 0.98)
            if 14.0 <= o.timestamp_s <= 20.0
            else o
            for o in occ
        ]
        return out_r, out_o

    mutate_records(
        multi_train_mod,
        name="12_multiple_trains",
        entry=6.5,
        clr=20.2,
        expected={"closure": True, "reopened": False, "premature": False},
    )

    # 13. Train reversal or unexpected movement during departure
    mutate_records(
        lambda recs, occ: (
            [
                EvidenceRecord(
                    r.timestamp_s,
                    "camera_2",
                    Modality.VISION,
                    True,
                    (Detection("rear", 0.85, (90.0, 55.0, 195.0, 165.0), {"reversing": True}),),
                )
                if (r.source_id == "camera_2" and r.timestamp_s >= 11.8)
                else r
                for r in recs
            ],
            [OccupancyEvidence(o.timestamp_s, o.source_id, OccupancyState.OCCUPIED, True, 0.95) if o.timestamp_s >= 12.0 else o for o in occ],
        ),
        name="13_train_reversal",
        entry=6.5,
        clr=23.9,
        expected={"closure": True, "reopened": False, "premature": False},
    )

    # 14. Train stopping inside observation zone (zero bbox displacement >= 2.0s + stopped flag)
    mutate_records(
        lambda recs, occ: (
            [
                EvidenceRecord(
                    r.timestamp_s,
                    "camera_side",
                    Modality.VISION,
                    True,
                    (Detection("side", 0.90, (100.0, 60.0, 200.0, 160.0), {"stopped": True}),),
                )
                if (r.source_id == "camera_side" and r.timestamp_s >= 6.0)
                else (
                    EvidenceRecord(r.timestamp_s, "camera_2", Modality.VISION, True, ())
                    if (r.source_id == "camera_2" and r.timestamp_s >= 11.0)
                    else r
                )
                for r in recs
            ],
            [OccupancyEvidence(o.timestamp_s, o.source_id, OccupancyState.OCCUPIED, True, 0.98) if o.timestamp_s >= 6.0 else o for o in occ],
        ),
        name="14_train_stopped_in_zone",
        entry=6.5,
        clr=23.9,
        expected={"closure": True, "reopened": False, "premature": False},
    )

    # 15. Partial visibility and occlusion (intermittent front+side detections during crossing, recovered before clear)
    mutate_records(
        lambda recs, occ: (
            [
                EvidenceRecord(r.timestamp_s, r.source_id, r.modality, True, ())
                if (r.source_id == "camera_side" and int(round(r.timestamp_s * 5)) % 2 == 1)
                else r
                for r in recs
            ],
            occ,
        ),
        name="15_partial_visibility_occlusion",
        expected={"closure": True, "reopened": True, "premature": False},
    )

    # 16. False train detection (1 isolated spurious single-frame front detection -> must NOT close gate!)
    false_recs = [
        EvidenceRecord(
            round(i * 0.2, 4),
            "camera_1",
            Modality.VISION,
            True,
            (Detection("front", 0.85),) if abs(round(i * 0.2, 4) - 2.0) < 1e-6 else (),
        )
        for i in range(60)
    ]
    f_false, rej_false = _collect_causal(false_recs, t_end=11.8)
    res_false, eng_false, ms_false = _run_v3(f_false, name="16_false_train_single_frame_glitch")
    scenarios_out.append(
        summarize("16_false_train_detection_glitch", res_false, eng_false, ms_false, rej_false, {"closure": False, "reopened": False})
    )

    # 17. False clear detection (Occupancy sensor claims CLEAR at t=9.0 while train is actively visible on side/back!)
    mutate_records(
        lambda recs, occ: (
            recs,
            [OccupancyEvidence(o.timestamp_s, o.source_id, OccupancyState.CLEAR, True, 0.99) if o.timestamp_s >= 8.0 else o for o in occ],
        ),
        name="17_false_clear_detection",
        expected={"closure": True, "reopened": False, "premature": False},
    )

    # Dedicated Exp D departure comparator test on synthetic sparse-dropout scenario (V1 vs V2 vs V3-Guarded vs V3-Conservative)
    sparse_recs: list[EvidenceRecord] = []
    sparse_occ: list[OccupancyEvidence] = []
    for i in range(121):
        t = round(i * 0.2, 4)
        sparse_recs.append(
            EvidenceRecord(
                t,
                "camera_1",
                Modality.VISION,
                True,
                (Detection("front", 0.90),) if 1.0 <= t <= 3.0 else (),
            )
        )
        # Single brief "rear" or "side" blip on back camera at 8.0-8.4 (train middle), then dropped/occluded until 14.0, true T4=15.0!
        if 8.0 <= t <= 8.2:
            b_dets: tuple[Detection, ...] = (Detection("side", 0.72),)
        else:
            b_dets = ()
        sparse_recs.append(EvidenceRecord(t, "camera_2", Modality.VISION, True, b_dets))
        sparse_recs.append(EvidenceRecord(t, "audio_1", Modality.AUDIO, True, ()))
        sparse_occ.append(
            OccupancyEvidence(
                t,
                "occ_loop_1",
                OccupancyState.OCCUPIED if 3.0 <= t < 15.0 else OccupancyState.CLEAR,
                True,
                0.98,
            )
        )

    f_sparse, _ = _collect_causal(sparse_recs, occupancy=sparse_occ, aligner=aligner, t_end=24.0)
    frozen_cfg = load_frozen_config()
    dep_comp: dict[str, Any] = {}
    for pol_name, eng in [
        ("V1_RULE_3", MultimodalDecisionEngine(config=frozen_cfg)),
        ("V2_RULE_3C_DISAPPEARANCE", MultimodalDecisionEngineV2Candidate(config=frozen_cfg)),
        ("V3_GUARDED_DISAPPEARANCE", MultimodalDecisionEngineV3FourLayer(departure_mode=DeparturePolicyMode.GUARDED_DISAPPEARANCE)),
        ("V3_CONSERVATIVE_POSITIVE", MultimodalDecisionEngineV3FourLayer(departure_mode=DeparturePolicyMode.CONSERVATIVE_POSITIVE)),
    ]:
        runner = EventSimulationRunner(decision_engine=eng)
        rr = runner.run_frames(f_sparse, event_id="synthetic/sparse_dropout", scenario_name=pol_name, entry_time_s=6.5, clearance_time_s=15.0)
        dep_comp[pol_name] = {
            "closure_triggered": any(s.gate_state in ("CLOSING", "CLOSED") for s in rr.steps),
            "premature_opening_detected": rr.premature_opening_detected,
            "reopened_at_all": any(s.crossing_state == "GATE_OPENING" for s in rr.steps),
            "first_opening_s": next((round(s.timestamp_s, 3) for s in rr.steps if s.crossing_state == "GATE_OPENING"), None),
            "final_state": rr.steps[-1].crossing_state if rr.steps else "NONE",
        }

    out = {
        "classification": "SYNTHETIC_EXPERIMENT_SUITE",
        "fault_and_operational_scenarios": scenarios_out,
        "all_transitions_legal": all(s["transition_legality"]["legal"] for s in scenarios_out),
        "unsafe_opening_count": sum(1 for s in scenarios_out if s["premature_opening_detected"]),
        "false_train_glitch_closed": scenarios_out[16]["closure_triggered"],
        "sparse_dropout_departure_comparison": dep_comp,
    }
    if include_traces:
        out["traces"] = traces_by_scenario
    return out
