#!/usr/bin/env python3
"""Phase 10 Task 4: replay the 11 real Phase 8 events (from already-cached
evidence, no new model inference) through BOTH the frozen policy and the
Phase 10 candidate policy, and record every event whose state trajectory
changed.

Reads only the pre-existing cache JSONL files under
results/r04_sync_estimation/exploratory_live_run_20261013T194806Z/cache/
(the same cache Phase 9's replay used and verified complete). Writes to a
NEW, separate output directory; Phase 8's and Phase 9's original outputs are
never opened for writing.
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
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine  # noqa: E402
from railway_detection.fusion.decision_engine_v2_candidate import (  # noqa: E402
    MultimodalDecisionEngineV2Candidate,
)
from railway_detection.fusion.rules_v2_candidate import (  # noqa: E402
    CANDIDATE_POLICY_VERSION,
    has_unambiguous_approach_label,
    has_unambiguous_departure_label,
)

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
        / f"phase10_candidate_replay_{datetime.datetime.now(datetime.UTC):%Y%m%dT%H%M%SZ}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # Read-only reuse of Phase 8's existing cache; this processor instance
    # never writes into PHASE8_CACHE_DIR because every requested cache file
    # already exists for all 11 events (verified in Phase 9).
    processor = LayerBEventProcessor(repo_root=REPO_ROOT, config=config, cache_dir=PHASE8_CACHE_DIR)

    run_manifest: dict = {
        "run_mode": "phase10_candidate_vs_frozen_replay",
        "timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "purpose": "Compare the frozen decision policy against the Phase 10 candidate policy on "
        "Phase 8's cached real evidence. No new model inference. Does not use any synchronization "
        "mechanism beyond what load_validated_sync_aligner already validates per event.",
        "frozen_policy_doc": "configs/decision_policy_v1.yaml",
        "candidate_policy_doc": "configs/decision_policy_v2_candidate.yaml",
        "candidate_policy_version": CANDIDATE_POLICY_VERSION,
        "frozen_experiment_config_canonical_hash_at_run_time": config.canonical_hash,
        "events": {},
    }

    summary_rows = []
    changed_count = 0

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

        common_kwargs = dict(
            vision_records=all_v_recs, audio_records=front_a_recs, duration_s=duration_s,
            stride_s=config.timing.tick_s, event_id=event_id, config=config,
            sync_aligner=validated_alignment.aligner, window_tolerance_s=0.25,
        )
        frozen_result = run_with_diagnostics(condition="B4_frozen", engine_factory=MultimodalDecisionEngine, **common_kwargs)
        candidate_result = run_with_diagnostics(
            condition="B4_candidate_v2", engine_factory=MultimodalDecisionEngineV2Candidate,
            approach_fn=has_unambiguous_approach_label, departure_fn=has_unambiguous_departure_label,
            **common_kwargs,
        )

        event_out_dir = out_dir / cohort / event_id
        event_out_dir.mkdir(parents=True, exist_ok=True)
        for label, result in (("frozen", frozen_result), ("candidate", candidate_result)):
            (event_out_dir / f"{label}_diagnostic_ticks.jsonl").write_text(
                "\n".join(json.dumps(tick_to_dict(tk)) for tk in result.ticks) + ("\n" if result.ticks else ""),
                encoding="utf-8",
            )
            (event_out_dir / f"{label}_rejections.json").write_text(
                json.dumps(asdict(result.rejections), indent=2), encoding="utf-8",
            )

        frozen_reached_clear = any(t.resulting_state == "CROSSING_CLEAR" for t in frozen_result.ticks)
        candidate_reached_clear = any(t.resulting_state == "CROSSING_CLEAR" for t in candidate_result.ticks)
        frozen_states = [t.resulting_state for t in frozen_result.ticks]
        candidate_states = [t.resulting_state for t in candidate_result.ticks]
        # A tick-count mismatch can arise only from a frame/alignment
        # difference, which there is none of here (identical inputs to both
        # calls); state sequences are compared positionally where lengths match.
        trajectory_changed = (
            frozen_reached_clear != candidate_reached_clear
            or frozen_states != candidate_states
        )
        if trajectory_changed:
            changed_count += 1

        frozen_rule_counts: dict[str, int] = {}
        candidate_rule_counts: dict[str, int] = {}
        for t in frozen_result.ticks:
            if t.rule_id:
                frozen_rule_counts[t.rule_id] = frozen_rule_counts.get(t.rule_id, 0) + 1
        for t in candidate_result.ticks:
            if t.rule_id:
                candidate_rule_counts[t.rule_id] = candidate_rule_counts.get(t.rule_id, 0) + 1

        run_manifest["events"][event_key] = {
            "back_offset_s": validated_alignment.back_offset_s,
            "trajectory_changed": trajectory_changed,
            "frozen": {
                "tick_count": len(frozen_result.ticks),
                "reached_crossing_clear": frozen_reached_clear,
                "final_state": frozen_states[-1] if frozen_states else None,
                "rejected_observations": frozen_result.rejections.total_rejected,
                "rule_counts": frozen_rule_counts,
            },
            "candidate": {
                "tick_count": len(candidate_result.ticks),
                "reached_crossing_clear": candidate_reached_clear,
                "final_state": candidate_states[-1] if candidate_states else None,
                "rejected_observations": candidate_result.rejections.total_rejected,
                "rule_counts": candidate_rule_counts,
            },
        }
        summary_rows.append(
            f"  {event_key}: changed={trajectory_changed}  "
            f"frozen(clear={frozen_reached_clear}, final={frozen_states[-1] if frozen_states else None})  "
            f"candidate(clear={candidate_reached_clear}, final={candidate_states[-1] if candidate_states else None})"
        )
        print(
            f"Processed {event_key}: changed={trajectory_changed} "
            f"frozen_clear={frozen_reached_clear} candidate_clear={candidate_reached_clear}"
        )

    run_manifest["summary"] = {
        "total_events": len(INCLUDED_EVENTS),
        "events_with_changed_trajectory": changed_count,
        "frozen_reached_clear_count": sum(1 for e in run_manifest["events"].values() if e["frozen"]["reached_crossing_clear"]),
        "candidate_reached_clear_count": sum(1 for e in run_manifest["events"].values() if e["candidate"]["reached_crossing_clear"]),
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")
    print(f"\nPhase 10 candidate replay complete. Output: {out_dir}")
    print(f"\nEvents with changed trajectory: {changed_count}/{len(INCLUDED_EVENTS)}")
    print(f"Frozen reached CROSSING_CLEAR: {run_manifest['summary']['frozen_reached_clear_count']}/{len(INCLUDED_EVENTS)}")
    print(f"Candidate reached CROSSING_CLEAR: {run_manifest['summary']['candidate_reached_clear_count']}/{len(INCLUDED_EVENTS)}")
    print("\nSummary:")
    for row in summary_rows:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
