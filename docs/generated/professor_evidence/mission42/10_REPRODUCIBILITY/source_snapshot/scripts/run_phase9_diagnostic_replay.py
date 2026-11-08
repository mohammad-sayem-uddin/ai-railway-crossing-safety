#!/usr/bin/env python3
"""Phase 9 forensic replay: re-process Phase 8's ALREADY-CACHED raw vision/audio
evidence through the unmodified decision engine with full diagnostic
instrumentation (Task 4's `run_with_diagnostics`), for the same 11
CALIBRATION_SUPPORTED events Phase 8 ran.

This performs NO new model inference. It reads only the pre-existing cache
JSONL files under
results/r04_sync_estimation/exploratory_live_run_20261013T194806Z/cache/,
which already contain Phase 8's exact YOLOv8n and CompactTrainHornCNN
outputs for every event (front vision, back vision, front audio). It is
behaviorally equivalent to `scripts/run_exploratory_dual_camera_subset.py`'s
`run_live` per-event logic (same `LayerBEventProcessor` cache-read path,
same `load_validated_sync_aligner`, same frozen config, same duration/stride
computation), except it records a full `DiagnosticRunResult` instead of only
{timestamp_s, crossing_state, gate_state, gate_angle_deg}.

Output is written to a NEW, separate directory
(results/r04_sync_estimation/phase9_diagnostic_replay_<UTC timestamp>/) and
never touches Phase 8's original output directory
(exploratory_live_run_20261013T194806Z/) in any way -- it does not even
open files there for writing, only the shared `cache/` subdirectory for
reading.
"""

from __future__ import annotations

import datetime
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from railway_detection.data.sync_calibration import load_validated_sync_aligner  # noqa: E402
from railway_detection.experiments.diagnostic_trace import (  # noqa: E402
    run_with_diagnostics,
    tick_to_dict,
)
from railway_detection.experiments.frozen_config import load_frozen_config  # noqa: E402
from railway_detection.experiments.layer_b_processor import LayerBEventProcessor  # noqa: E402

PHASE8_OUTPUT_DIR = REPO_ROOT / "results" / "r04_sync_estimation" / "exploratory_live_run_20261013T194806Z"
PHASE8_CACHE_DIR = PHASE8_OUTPUT_DIR / "cache"
CALIBRATION_MANIFEST_PATH = REPO_ROOT / "data" / "manifests" / "camera_sync_offsets_candidate.yaml"

INCLUDED_EVENTS = [
    "train_events/event_001", "train_events/event_002", "train_events/event_005",
    "train_events/event_006", "train_events/event_007", "train_events/event_009",
    "train_events/event_011", "train_events/event_012", "train_events/event_013",
    "train_events/event_014", "train_events/event_017",
]


def main() -> int:
    if not PHASE8_CACHE_DIR.exists():
        print(f"BLOCKED: Phase 8 cache directory not found at {PHASE8_CACHE_DIR}", file=sys.stderr)
        return 1

    config = load_frozen_config(REPO_ROOT / "configs" / "frozen_experiment_v1.yaml")
    config.verify_all_safeguards(repo_root=REPO_ROOT)

    out_dir = (
        REPO_ROOT / "results" / "r04_sync_estimation"
        / f"phase9_diagnostic_replay_{datetime.datetime.now(datetime.UTC):%Y%m%dT%H%M%SZ}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # cache_dir points at Phase 8's EXISTING cache. use_cache=True means
    # run_vision_inference/run_audio_inference below take the early
    # cache-hit return path (deserialize-and-return) and never reach any
    # model-loading or video-decode code -- verified cache completeness
    # (33 files = 11 events x {front vision, back vision, audio}) before
    # this script was written. This processor instance never writes into
    # PHASE8_CACHE_DIR because every requested cache file already exists.
    processor = LayerBEventProcessor(repo_root=REPO_ROOT, config=config, cache_dir=PHASE8_CACHE_DIR)

    run_manifest: dict = {
        "run_mode": "phase9_diagnostic_replay",
        "timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "purpose": "Forensic replay of Phase 8 cached evidence with full diagnostic instrumentation. "
        "No new model inference. Reads only results/r04_sync_estimation/"
        "exploratory_live_run_20261013T194806Z/cache/.",
        "source_phase8_output_dir": str(PHASE8_OUTPUT_DIR.relative_to(REPO_ROOT)),
        "frozen_experiment_config_canonical_hash_at_run_time": config.canonical_hash,
        "events": {},
    }

    summary_rows = []

    for event_key in INCLUDED_EVENTS:
        cohort, event_id = event_key.split("/")
        event_dir = REPO_ROOT / "data" / "raw" / "layer_b" / "v2" / cohort / event_id
        front_mov = event_dir / "camera_front.mov"
        back_mov = event_dir / "camera_back.mov"

        validated_alignment = load_validated_sync_aligner(
            CALIBRATION_MANIFEST_PATH, event_key, repo_root=REPO_ROOT, allow_candidate_status=True,
        )

        front_v_recs = processor.run_vision_inference(
            video_path=front_mov, checkpoint_path=REPO_ROOT / config.checkpoints.vision.path,
            source_id=validated_alignment.front_source_id, target_fps=config.vision.sampling_fps,
            conf=config.vision.confidence_threshold_approach, use_cache=True,
        )
        back_v_recs = processor.run_vision_inference(
            video_path=back_mov, checkpoint_path=REPO_ROOT / config.checkpoints.vision.path,
            source_id=validated_alignment.back_source_id, target_fps=config.vision.sampling_fps,
            conf=config.vision.confidence_threshold_approach, use_cache=True,
        )
        front_a_recs = processor.run_audio_inference(
            wav_path=None, checkpoint_path=REPO_ROOT / config.checkpoints.audio_v3.path,
            source_id="audio_1", threshold=config.audio.operating_threshold,
            cohort=cohort, event_id=event_id, use_cache=True,
        )

        all_v_recs = list(front_v_recs) + list(back_v_recs)
        duration_s = max(
            [r.timestamp_s for r in all_v_recs] + [r.timestamp_s for r in front_a_recs], default=30.0
        )

        result = run_with_diagnostics(
            vision_records=all_v_recs,
            audio_records=front_a_recs,
            duration_s=duration_s,
            stride_s=config.timing.tick_s,
            event_id=event_id,
            condition="B4_phase9_diagnostic_replay",
            config=config,
            sync_aligner=validated_alignment.aligner,
            window_tolerance_s=0.25,
        )

        event_out_dir = out_dir / cohort / event_id
        event_out_dir.mkdir(parents=True, exist_ok=True)
        (event_out_dir / "diagnostic_ticks.jsonl").write_text(
            "\n".join(json.dumps(tick_to_dict(tk)) for tk in result.ticks) + ("\n" if result.ticks else ""),
            encoding="utf-8",
        )
        (event_out_dir / "rejections.json").write_text(
            json.dumps(asdict(result.rejections), indent=2), encoding="utf-8",
        )

        reached_clear = any(tk.resulting_state == "CROSSING_CLEAR" for tk in result.ticks)
        final_state = result.ticks[-1].resulting_state if result.ticks else None
        last_rule_before_end = next(
            (tk.rule_id for tk in reversed(result.ticks) if tk.rule_id), None
        )
        run_manifest["events"][event_key] = {
            "front_sha256": validated_alignment.front_sha256,
            "back_sha256": validated_alignment.back_sha256,
            "back_offset_s": validated_alignment.back_offset_s,
            "tick_count": len(result.ticks),
            "total_duration_s": result.total_duration_s,
            "reached_crossing_clear": reached_clear,
            "final_resulting_state": final_state,
            "fault_occurred": result.fault_occurred,
            "total_rejected_observations": result.rejections.total_rejected,
            "rejections_by_reason": result.rejections.by_reason,
            "last_rule_id_in_run": last_rule_before_end,
        }
        summary_rows.append(
            f"  {event_key}: reached_clear={reached_clear}  final_state={final_state}  "
            f"fault={result.fault_occurred}  rejected={result.rejections.total_rejected}  "
            f"last_rule={last_rule_before_end}"
        )
        print(f"Processed {event_key}: reached_clear={reached_clear} final_state={final_state}")

    (out_dir / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")
    print(f"\nPhase 9 diagnostic replay complete. Output: {out_dir}")
    print("\nSummary:")
    for row in summary_rows:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
