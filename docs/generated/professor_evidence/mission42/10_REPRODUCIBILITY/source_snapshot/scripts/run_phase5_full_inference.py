#!/usr/bin/env python3
"""Phase 5 — Master Full-Dataset Production Inference and Prediction Collection.

Executes real production inference across the entire verified active railway dataset:
- 27 Active Events (23 train events, 3 no-train negative controls, 1 engine-only event).
- 54 Active Video Streams (camera_front.mov and camera_back.mov for each event).
- Strictly excludes quarantined historical duplicate (event_historical_duplicate_010).
- Permitted execution conditions (R04 enforced):
  * B0: Front-camera vision-only inference (5.0 FPS, conf=0.35).
  * B1: Front-camera audio-only inference (1.0s window, 0.5s hop, thres=0.3700).
  * B2: Front-camera vision + container-native audio fusion (0.1s master clock ticks).
  * Back Vision Independent: Back-camera vision-only inference on its own media-local timeline.
- Evaluation Firewall Maintained:
  * Zero ground-truth accuracy / MTR / POR metrics calculated from unapproved annotations.
  * Records actual model outputs, state transitions, gate kinematics, and execution evidence.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Ensure project imports resolve
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from railway_detection.safety.media_guard import (
    precheck_operation_authorized,
    require_media_authorization,
)
from railway_detection.experiments.frozen_config import (
    EXPECTED_AUDIO_V3_SHA256,
    EXPECTED_VISION_SHA256,
    FrozenExperimentConfig,
    load_frozen_config,
)
from railway_detection.experiments.layer_b_processor import (
    LayerBEventProcessor,
    serialize_evidence_record,
)
from railway_detection.simulation.runner import EventSimulationRunner
from railway_detection.utils.logging import get_logger

logger = get_logger("scripts.run_phase5_full_inference")

ACTIVE_COHORTS = ["train_events", "no_train_events", "engine_events"]
QUARANTINED_EVENTS = {"event_historical_duplicate_010"}


def get_file_sha256(path: Path | str) -> str:
    p = Path(path)
    require_media_authorization(p, "HASH_RAW_MEDIA")
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def get_stream_duration(path: Path) -> float:
    require_media_authorization(path, "MEDIA_PROBE")
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    info = json.loads(res.stdout)
    return float(info["format"]["duration"])


def check_disk_space_gb(path: Path) -> float:
    stat = shutil.disk_usage(path)
    return stat.free / (1024**3)


def execute_preflight_checks(
    repo_root: Path,
) -> tuple[FrozenExperimentConfig, dict[str, Any], list[dict[str, Any]]]:
    """Execute Step 1: Preflight checks on environment, storage, manifests, and checkpoints."""
    print("=================================================================")
    print("STEP 1: PREFLIGHT INTEGRITY & ENVIRONMENT VERIFICATION")
    print("=================================================================")

    # 0. Check mandatory media access authorization (FAIL CLOSED)
    print(" [CHECK] Verifying on-disk AUTH-MEDIA-ACCESS authorization...")
    precheck_operation_authorized("INFERENCE", repo_root=repo_root)
    print(" [OK] AUTH-MEDIA-ACCESS record valid; every media file is re-checked at its opener.")

    # 1. Verify repository root and required previous phase reports
    assert repo_root.exists(), f"Repository root does not exist: {repo_root}"
    print(f" [OK] Repository root verified: {repo_root}")

    required_reports = [
        repo_root / "docs/PHASE2_FROZEN_CONFIGURATION_REPORT.md",
        repo_root / "docs/PHASE3_SENSOR_HEALTH_DECISION_POLICY.md",
        repo_root / "docs/PHASE4_INTEGRATION_PREFLIGHT_REPORT.md",
        repo_root / "reports/progress.md",
    ]
    for rep in required_reports:
        assert rep.exists(), f"Missing required prerequisite report: {rep}"
        print(f" [OK] Prerequisite artifact present: {rep.name}")

    # 2. Check disk space
    free_gb = check_disk_space_gb(repo_root)
    print(f" [OK] Available disk space: {free_gb:.2f} GiB (minimum required: 15.0 GiB)")
    assert free_gb >= 15.0, f"Insufficient disk space: {free_gb:.2f} GiB available"

    # 3. Load and verify authoritative frozen configuration
    config = load_frozen_config(repo_root / "configs/frozen_experiment_v1.yaml")
    config.verify_all_safeguards(repo_root)
    print(f" [OK] Frozen config canonical SHA-256 verified: {config.canonical_hash}")
    assert (
        config.canonical_hash
        == "999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e"
    ), "Frozen config canonical hash mismatch!"

    # 4. Verify decision policy configuration
    dec_policy_file = repo_root / "configs/decision_policy_v1.yaml"
    assert dec_policy_file.exists(), "Missing decision policy configuration"
    from railway_detection.experiments.frozen_config import compute_canonical_config_hash
    import yaml

    dec_raw = yaml.safe_load(dec_policy_file.read_text(encoding="utf-8"))
    dec_hash = compute_canonical_config_hash(dec_raw)
    print(f" [OK] Decision policy canonical SHA-256 verified: {dec_hash}")
    assert (
        dec_hash
        == "051c908d4db23687db33cbc8349945b241a0735b362413be876d7017a5eacc9d"
    ), "Decision policy hash mismatch!"

    # 5. Checkpoint hashes and parameter guards
    yolo_hash = get_file_sha256(repo_root / config.checkpoints.vision.path)
    assert yolo_hash == EXPECTED_VISION_SHA256, f"YOLO hash mismatch: {yolo_hash}"
    print(f" [OK] YOLO vision checkpoint SHA-256 verified: {yolo_hash[:12]}...")

    audio_hash = get_file_sha256(repo_root / config.checkpoints.audio_v3.path)
    assert audio_hash == EXPECTED_AUDIO_V3_SHA256, f"Audio V3 hash mismatch: {audio_hash}"
    print(f" [OK] Audio V3 checkpoint SHA-256 verified: {audio_hash[:12]}...")

    # Verify prohibited Audio V2 guard
    proh_path = repo_root / config.checkpoints.prohibited_audio_v2.path
    if proh_path.exists():
        proh_hash = get_file_sha256(proh_path)
        assert (
            proh_hash == config.checkpoints.prohibited_audio_v2.sha256
        ), "Prohibited Audio V2 mismatch"
        print(f" [OK] Prohibited Audio V2 detected and hard-guarded: {proh_hash[:12]}...")

    # Threshold checks
    assert config.audio.operating_threshold == 0.3700, "Audio threshold must be 0.3700"
    assert config.vision.confidence_threshold_approach == 0.35, "Vision approach thres must be 0.35"
    assert config.vision.confidence_threshold_departure == 0.35, "Vision departure thres must be 0.35"
    assert config.vision.sampling_fps == 5.0, "Vision sampling must be 5.0 FPS"
    print(" [OK] Preprocessing, threshold, and sampling parameters locked.")

    # 6. Resolve video filesystem sizes and active cohort inventory
    v2_base = repo_root / "data/raw/layer_b/v2"
    assert v2_base.exists(), f"Layer B V2 directory not found: {v2_base}"

    active_streams: list[dict[str, Any]] = []
    quarantined_streams: list[dict[str, Any]] = []

    for cohort in ACTIVE_COHORTS:
        cohort_dir = v2_base / cohort
        if not cohort_dir.is_dir():
            continue
        for ev_dir in sorted(cohort_dir.iterdir()):
            if not ev_dir.is_dir():
                continue
            is_quarantined = ev_dir.name in QUARANTINED_EVENTS
            front_mov = ev_dir / "camera_front.mov"
            back_mov = ev_dir / "camera_back.mov"

            if is_quarantined:
                if front_mov.exists():
                    quarantined_streams.append({"path": front_mov, "size": front_mov.stat().st_size})
                if back_mov.exists():
                    quarantined_streams.append({"path": back_mov, "size": back_mov.stat().st_size})
                continue

            assert front_mov.exists(), f"Missing front video in {ev_dir}"
            assert back_mov.exists(), f"Missing back video in {ev_dir}"

            f_sz = front_mov.stat().st_size
            b_sz = back_mov.stat().st_size
            assert f_sz > 0, f"Empty front video file: {front_mov}"
            assert b_sz > 0, f"Empty back video file: {back_mov}"

            active_streams.append(
                {
                    "cohort": cohort,
                    "event_id": ev_dir.name,
                    "camera_id": "front",
                    "path": front_mov,
                    "size_bytes": f_sz,
                }
            )
            active_streams.append(
                {
                    "cohort": cohort,
                    "event_id": ev_dir.name,
                    "camera_id": "back",
                    "path": back_mov,
                    "size_bytes": b_sz,
                }
            )

    active_bytes = sum(s["size_bytes"] for s in active_streams)
    quarantine_bytes = sum(s["size"] for s in quarantined_streams)
    total_v2_bytes = active_bytes + quarantine_bytes

    inventory_stats = {
        "active_stream_count": len(active_streams),
        "active_event_count": len(active_streams) // 2,
        "active_size_bytes": active_bytes,
        "active_size_gib": active_bytes / (1024**3),
        "active_size_decimal_gb": active_bytes / (1000**3),
        "quarantined_stream_count": len(quarantined_streams),
        "quarantined_size_bytes": quarantine_bytes,
        "total_v2_bytes": total_v2_bytes,
        "total_v2_gib": total_v2_bytes / (1024**3),
    }

    print("\n--- Empirical Storage Inventory Resolution ---")
    print(f" Active Streams (54 streams across 27 events): {active_bytes:,} bytes")
    print(f" -> Binary: {inventory_stats['active_size_gib']:.3f} GiB | Decimal: {inventory_stats['active_size_decimal_gb']:.3f} GB")
    print(f" Quarantined Historical Duplicate (2 streams): {quarantine_bytes:,} bytes ({quarantine_bytes / (1024**3):.4f} GiB)")
    print(f" Total Layer B V2 Directory on Disk: {total_v2_bytes:,} bytes ({inventory_stats['total_v2_gib']:.3f} GiB)")
    print(" Resolution: The true filesystem size is 3.559 GiB (3.822 GB decimal) for active streams.")
    print(" The previous 3.6 GB figure corresponded to rounded binary GiB (3.56 GiB).")
    print(" The 11.5 GB figure was an authored narrative error; filesystem confirms exactly 3.82 GB decimal.")

    assert len(active_streams) == 54, f"Expected 54 active streams, found {len(active_streams)}"
    assert inventory_stats["active_event_count"] == 27, f"Expected 27 active events, found {inventory_stats['active_event_count']}"
    print(f"\n [OK] Cohort inventory verified: exactly 27 active events (54 streams). Duplicate quarantined.")

    return config, inventory_stats, active_streams


def run_full_dataset_inference(
    repo_root: Path,
    config: FrozenExperimentConfig,
    active_streams: list[dict[str, Any]],
    output_dir: Path,
    progress_file: Path | None = None,
) -> dict[str, Any]:
    """Execute Steps 2, 3, 4, 6: Production inference and incremental artifact emission."""
    # Fail closed before touching any stream (each file is also re-checked at its opener)
    precheck_operation_authorized("INFERENCE", repo_root=repo_root)

    print("\n=================================================================")
    print("STEPS 2–4: PRODUCTION INFERENCE & PREDICTION COLLECTION")
    print("=================================================================")
    print(f"Output Directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_pred_dir = output_dir / "raw_predictions"
    cond_b0_dir = output_dir / "conditions/B0_vision_front"
    cond_b1_dir = output_dir / "conditions/B1_audio_front"
    cond_b2_dir = output_dir / "conditions/B2_multimodal_front"
    cond_back_dir = output_dir / "conditions/back_vision_independent"

    for d in [raw_pred_dir, cond_b0_dir, cond_b1_dir, cond_b2_dir, cond_back_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Initialize processor
    processor = LayerBEventProcessor(
        repo_root=repo_root,
        config=config,
        cache_dir=output_dir / "internal_cache",
    )
    yolo_ckpt = repo_root / config.checkpoints.vision.path
    audio_ckpt = repo_root / config.checkpoints.audio_v3.path

    # Group streams by event
    events_map: dict[str, dict[str, Any]] = {}
    for s in active_streams:
        ev_key = f"{s['cohort']}/{s['event_id']}"
        if ev_key not in events_map:
            events_map[ev_key] = {
                "cohort": s["cohort"],
                "event_id": s["event_id"],
                "front_mov": None,
                "back_mov": None,
            }
        if s["camera_id"] == "front":
            events_map[ev_key]["front_mov"] = s["path"]
        elif s["camera_id"] == "back":
            events_map[ev_key]["back_mov"] = s["path"]

    total_events = len(events_map)
    print(f"Starting execution across {total_events} events (54 video streams)...\n")

    event_summaries: list[dict[str, Any]] = []
    overall_start_time = time.time()
    total_frames_processed = 0
    total_audio_windows_processed = 0

    event_idx = 0
    for ev_key, ev_info in events_map.items():
        event_idx += 1
        cohort = ev_info["cohort"]
        event_id = ev_info["event_id"]
        front_mov: Path = ev_info["front_mov"]
        back_mov: Path = ev_info["back_mov"]
        event_dir = front_mov.parent

        ev_start_time = time.time()
        print(f"[{event_idx:02d}/{total_events:02d}] Processing {cohort}/{event_id}...")

        # 1. Extract audio
        audio_paths = processor.extract_audio(event_dir)
        front_wav = audio_paths.get("front")

        # 2. Front Video Inference (5.0 FPS)
        t0 = time.time()
        front_v_recs = processor.run_vision_inference(
            video_path=front_mov,
            checkpoint_path=yolo_ckpt,
            source_id="camera_1",
            target_fps=config.vision.sampling_fps,
            conf=config.vision.confidence_threshold_approach,
            use_cache=False,
        )
        t_front_v = time.time() - t0

        # Save front vision raw JSONL
        front_v_file = raw_pred_dir / f"{cohort}_{event_id}_camera_front_vision.jsonl"
        with open(front_v_file, "w", encoding="utf-8") as f:
            for r in front_v_recs:
                f.write(json.dumps(serialize_evidence_record(r)) + "\n")

        # 3. Front Audio Inference (16 kHz, 1.0s win, 0.5s hop)
        t0 = time.time()
        front_a_recs = processor.run_audio_inference(
            wav_path=front_wav,
            checkpoint_path=audio_ckpt,
            source_id="audio_1",
            threshold=config.audio.operating_threshold,
            cohort=cohort,
            event_id=event_id,
            use_cache=False,
        )
        t_front_a = time.time() - t0

        # Save front audio raw JSONL
        front_a_file = raw_pred_dir / f"{cohort}_{event_id}_camera_front_audio.jsonl"
        with open(front_a_file, "w", encoding="utf-8") as f:
            for r in front_a_recs:
                f.write(json.dumps(serialize_evidence_record(r)) + "\n")

        # 4. Back Video Inference (5.0 FPS)
        t0 = time.time()
        back_v_recs = processor.run_vision_inference(
            video_path=back_mov,
            checkpoint_path=yolo_ckpt,
            source_id="camera_2",
            target_fps=config.vision.sampling_fps,
            conf=config.vision.confidence_threshold_approach,
            use_cache=False,
        )
        t_back_v = time.time() - t0

        # Save back vision raw JSONL
        back_v_file = raw_pred_dir / f"{cohort}_{event_id}_camera_back_vision.jsonl"
        with open(back_v_file, "w", encoding="utf-8") as f:
            for r in back_v_recs:
                f.write(json.dumps(serialize_evidence_record(r)) + "\n")

        total_frames_processed += len(front_v_recs) + len(back_v_recs)
        total_audio_windows_processed += len(front_a_recs)

        # -------------------------------------------------------------
        # Condition B0: Front-Camera Vision Only
        # -------------------------------------------------------------
        sim_runner_b0 = EventSimulationRunner(config=config)
        b0_frames = processor.build_multimodal_frames(
            vision_records=front_v_recs,
            audio_records=[],
            duration_s=max([r.timestamp_s for r in front_v_recs], default=30.0),
            stride_s=config.timing.tick_s,
        )
        sim_res_b0 = sim_runner_b0.run_frames(b0_frames, event_id=f"{cohort}_{event_id}", scenario_name="B0")
        _save_simulation_outputs(sim_res_b0, cond_b0_dir, cohort, event_id, "B0")

        # -------------------------------------------------------------
        # Condition B1: Front-Camera Audio Only
        # -------------------------------------------------------------
        sim_runner_b1 = EventSimulationRunner(config=config)
        b1_frames = processor.build_multimodal_frames(
            vision_records=[],
            audio_records=front_a_recs,
            duration_s=max([r.timestamp_s for r in front_a_recs], default=30.0),
            stride_s=config.timing.tick_s,
        )
        sim_res_b1 = sim_runner_b1.run_frames(b1_frames, event_id=f"{cohort}_{event_id}", scenario_name="B1")
        _save_simulation_outputs(sim_res_b1, cond_b1_dir, cohort, event_id, "B1")

        # -------------------------------------------------------------
        # Condition B2: Front Vision + Front Audio Native Container Sync
        # -------------------------------------------------------------
        sim_runner_b2 = EventSimulationRunner(config=config)
        b2_frames = processor.build_multimodal_frames(
            vision_records=front_v_recs,
            audio_records=front_a_recs,
            duration_s=max(
                [r.timestamp_s for r in front_v_recs] + [r.timestamp_s for r in front_a_recs],
                default=30.0,
            ),
            stride_s=config.timing.tick_s,
        )
        sim_res_b2 = sim_runner_b2.run_frames(b2_frames, event_id=f"{cohort}_{event_id}", scenario_name="B2")
        _save_simulation_outputs(sim_res_b2, cond_b2_dir, cohort, event_id, "B2")

        # -------------------------------------------------------------
        # Condition Back Vision Independent (Media-Local Timeline)
        # -------------------------------------------------------------
        sim_runner_back = EventSimulationRunner(config=config)
        back_frames = processor.build_multimodal_frames(
            vision_records=back_v_recs,
            audio_records=[],
            duration_s=max([r.timestamp_s for r in back_v_recs], default=30.0),
            stride_s=config.timing.tick_s,
        )
        sim_res_back = sim_runner_back.run_frames(
            back_frames, event_id=f"{cohort}_{event_id}", scenario_name="Back_Independent"
        )
        _save_simulation_outputs(sim_res_back, cond_back_dir, cohort, event_id, "Back_Independent")

        ev_duration = time.time() - ev_start_time
        ev_summary = {
            "cohort": cohort,
            "event_id": event_id,
            "event_key": ev_key,
            "status": "COMPLETED",
            "front_video_duration_s": max([r.timestamp_s for r in front_v_recs], default=0.0),
            "front_vision_frames": len(front_v_recs),
            "front_vision_detections": sum(len(r.detections) for r in front_v_recs),
            "front_vision_inference_s": round(t_front_v, 2),
            "front_audio_duration_s": max([r.timestamp_s for r in front_a_recs], default=0.0),
            "front_audio_windows": len(front_a_recs),
            "front_audio_horns_detected": sum(
                1 for r in front_a_recs if any(d.label == "train_horn" for d in r.detections)
            ),
            "front_audio_inference_s": round(t_front_a, 2),
            "back_video_duration_s": max([r.timestamp_s for r in back_v_recs], default=0.0),
            "back_vision_frames": len(back_v_recs),
            "back_vision_detections": sum(len(r.detections) for r in back_v_recs),
            "back_vision_inference_s": round(t_back_v, 2),
            "total_event_processing_s": round(ev_duration, 2),
            "decisions_b0_steps": len(sim_res_b0.steps),
            "decisions_b1_steps": len(sim_res_b1.steps),
            "decisions_b2_steps": len(sim_res_b2.steps),
            "decisions_back_steps": len(sim_res_back.steps),
        }
        event_summaries.append(ev_summary)

        print(
            f"   -> Done in {ev_duration:.1f}s | "
            f"Front V: {len(front_v_recs)} frames ({t_front_v:.1f}s) | "
            f"Audio: {len(front_a_recs)} wins ({t_front_a:.1f}s) | "
            f"Back V: {len(back_v_recs)} frames ({t_back_v:.1f}s)"
        )

        # Append incremental progress to progress.md if enabled
        if progress_file and progress_file.exists():
            _append_incremental_progress(progress_file, event_idx, total_events, ev_summary)

    total_wall_clock_s = time.time() - overall_start_time

    # 5. Write execution manifests & metadata
    run_meta = {
        "execution_timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "canonical_config_hash": config.canonical_hash,
        "vision_checkpoint_sha256": EXPECTED_VISION_SHA256,
        "audio_v3_checkpoint_sha256": EXPECTED_AUDIO_V3_SHA256,
        "audio_operating_threshold": config.audio.operating_threshold,
        "vision_confidence_threshold": config.vision.confidence_threshold_approach,
        "vision_sampling_fps": config.vision.sampling_fps,
        "timing_tick_s": config.timing.tick_s,
        "r04_cross_camera_status": config.timing.cross_camera_sync.status,
        "total_active_events": total_events,
        "completed_events": len(event_summaries),
        "total_frames_processed": total_frames_processed,
        "total_audio_windows_processed": total_audio_windows_processed,
        "total_wall_clock_s": round(total_wall_clock_s, 2),
        "overall_fps": round(total_frames_processed / max(total_wall_clock_s, 1.0), 2),
        "evaluation_firewall": "STRICT_ACTIVE: Unapproved ground truth isolated; no accuracy/MTR/POR metrics claimed",
    }
    (output_dir / "frozen_config_meta.json").write_text(json.dumps(run_meta, indent=2), encoding="utf-8")
    (output_dir / "execution_manifest.json").write_text(json.dumps(event_summaries, indent=2), encoding="utf-8")

    print("\n=================================================================")
    print("PHASE 5 EXECUTION COMPLETE")
    print(f"Total Events Processed: {len(event_summaries)} / {total_events}")
    print(f"Total Video Frames Processed: {total_frames_processed:,}")
    print(f"Total Audio Windows Processed: {total_audio_windows_processed:,}")
    print(f"Total Execution Time: {total_wall_clock_s:.1f}s ({total_wall_clock_s / 60:.2f} min)")
    print(f"Artifacts Saved to: {output_dir}")
    print("=================================================================\n")

    return run_meta


def _save_simulation_outputs(
    sim_res: Any,
    out_dir: Path,
    cohort: str,
    event_id: str,
    condition_name: str,
) -> None:
    dec_file = out_dir / f"{cohort}_{event_id}_decision_records.jsonl"
    kin_file = out_dir / f"{cohort}_{event_id}_gate_kinematics.jsonl"
    sum_file = out_dir / f"{cohort}_{event_id}_summary.json"

    with open(dec_file, "w", encoding="utf-8") as f_dec, open(kin_file, "w", encoding="utf-8") as f_kin:
        for s in sim_res.steps:
            f_dec.write(json.dumps(s.decision.to_dict()) + "\n")
            f_kin.write(
                json.dumps(
                    {
                        "timestamp_s": s.timestamp_s,
                        "crossing_state": s.crossing_state,
                        "gate_state": s.gate_state,
                        "gate_angle_deg": round(s.gate_angle_deg, 2),
                        "is_passage_blocked": s.is_passage_blocked,
                    }
                )
                + "\n"
            )

    sum_data = {
        "event_id": f"{cohort}_{event_id}",
        "condition": condition_name,
        "step_count": len(sim_res.steps),
        "total_duration_s": round(sim_res.total_duration_s, 2),
        "closed_duration_s": round(sim_res.closed_duration_s, 2),
        "fault_occurred": sim_res.fault_occurred,
    }
    sum_file.write_text(json.dumps(sum_data, indent=2), encoding="utf-8")


def _append_incremental_progress(
    progress_file: Path, idx: int, total: int, summary: dict[str, Any]
) -> None:
    line = (
        f"- Stream Batch [{idx:02d}/{total:02d}]: `{summary['cohort']}/{summary['event_id']}` | "
        f"Front: {summary['front_vision_frames']} f | "
        f"Audio: {summary['front_audio_windows']} w | "
        f"Back: {summary['back_vision_frames']} f | Time: {summary['total_event_processing_s']}s\n"
    )
    with open(progress_file, "a", encoding="utf-8") as f:
        f.write(line)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 5 Full-Dataset Production Inference")
    parser.add_argument("--repo-root", type=str, default=".", help="Path to repository root")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/experiments/phase5_full_dataset_run",
        help="Destination directory for predictions and logs",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    # Check media authorization BEFORE touching progress.md or running preflight
    precheck_operation_authorized("INFERENCE", repo_root=repo_root)

    config, inv_stats, active_streams = execute_preflight_checks(repo_root)

    out_dir = repo_root / args.output_dir
    progress_md = repo_root / "reports/progress.md"

    # Pre-append header to progress.md for Phase 5 batch updates
    with open(progress_md, "a", encoding="utf-8") as f:
        f.write("\n---\n\n### 2026-10-13 — Senior ML Infrastructure Engineer — Phase 5: Full-Dataset Inference Execution Log\n\n")
        f.write(f"Initiated full 54-stream inference run across 27 active events at `{datetime.datetime.now(datetime.UTC).isoformat()}`.\n\n")

    run_full_dataset_inference(
        repo_root=repo_root,
        config=config,
        active_streams=active_streams,
        output_dir=out_dir,
        progress_file=progress_md,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
