#!/usr/bin/env python3
"""Phase 10.1: restricted, explicitly authorized comparison of the frozen
decision policy and the v2.0.0-candidate policy on exactly the 11 existing
authorized events, using Phase 8's already-cached model evidence.

No new model inference is performed. No frozen configuration, frozen
policy, model weight, or ground-truth file is read for writing or modified.
Preconditions (candidate policy hash, event membership, cache completeness)
are verified before any replay runs; the script aborts with a clear message
rather than silently proceeding if any precondition fails.

Runs each of the 11 events through FOUR combinations for full rigor:
  - frozen policy,    naive (Phase 9/10-matching) replay duration
  - candidate policy, naive (Phase 9/10-matching) replay duration
  - frozen policy,    corrected (sync-offset-aware) replay duration
  - candidate policy, corrected (sync-offset-aware) replay duration

The "naive" duration reproduces exactly what Phase 9's and Phase 10's
scripts computed (max of RAW, UNALIGNED per-source local timestamps mixed
together) so this run's frozen/candidate results under that duration can be
validated against Phase 9's and Phase 10's prior results directly. The
"corrected" duration additionally accounts for each event's validated
back-camera offset, which Phase 10.1's investigation found the naive
computation to silently ignore -- truncating the replay window before some
sync-shifted back-camera evidence (already fully present in the cache) ever
gets a chance to be evaluated. This is a replay-INSTRUMENTATION correction,
not new inference: both policies see identically corrected evidence, so the
comparison between them remains fair at both duration settings.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

import yaml  # noqa: E402

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
PHASE9_OUTPUT_DIR = REPO_ROOT / "results" / "r04_sync_estimation" / "phase9_diagnostic_replay_20261014T040741Z"
PHASE10_OUTPUT_DIR = REPO_ROOT / "results" / "r04_sync_estimation" / "phase10_candidate_replay_20261014T053200Z"
CALIBRATION_MANIFEST_PATH = REPO_ROOT / "data" / "manifests" / "camera_sync_offsets_candidate.yaml"
CANDIDATE_POLICY_YAML_PATH = REPO_ROOT / "configs" / "decision_policy_v2_candidate.yaml"
EXPECTED_CANDIDATE_POLICY_HASH = "143782d15632d2d840e3c3a1d0437a113cd810356d8ce59757d1b6b97f55ea60"

INCLUDED_EVENTS = [
    "train_events/event_001", "train_events/event_002", "train_events/event_005",
    "train_events/event_006", "train_events/event_007", "train_events/event_009",
    "train_events/event_011", "train_events/event_012", "train_events/event_013",
    "train_events/event_014", "train_events/event_017",
]


def _canonical_hash_of_yaml(path: Path) -> str:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw.pop("canonical_hash", None)
    raw.pop("config_hash", None)
    cj = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(cj.encode("utf-8")).hexdigest()


def _verify_preconditions(config) -> None:
    """Fail loudly and stop, per Phase 10.1's explicit instruction, rather
    than silently proceeding, if any precondition does not hold."""
    problems = []

    if not PHASE8_CACHE_DIR.exists():
        problems.append(f"Phase 8 cache directory not found at {PHASE8_CACHE_DIR}")
    else:
        expected_cache_files = {
            f"train_events_{ev.split('/')[1]}_{suffix}"
            for ev in INCLUDED_EVENTS
            for suffix in (
                "camera_front_camera_1_vision.jsonl",
                "camera_back_camera_2_vision.jsonl",
                "audio_1_audio.jsonl",
            )
        }
        present = {p.name for p in PHASE8_CACHE_DIR.glob("*.jsonl")}
        missing = expected_cache_files - present
        if missing:
            problems.append(f"Missing {len(missing)} expected cache files: {sorted(missing)}")

    if not CANDIDATE_POLICY_YAML_PATH.exists():
        problems.append(f"Candidate policy document not found at {CANDIDATE_POLICY_YAML_PATH}")
    else:
        actual_hash = _canonical_hash_of_yaml(CANDIDATE_POLICY_YAML_PATH)
        if actual_hash != EXPECTED_CANDIDATE_POLICY_HASH:
            problems.append(
                f"Candidate policy hash MISMATCH against Phase 10 report: "
                f"expected {EXPECTED_CANDIDATE_POLICY_HASH}, got {actual_hash}. "
                "configs/decision_policy_v2_candidate.yaml may have changed since Phase 10 "
                "-- stopping rather than silently comparing against a different candidate."
            )

    if not PHASE9_OUTPUT_DIR.exists():
        problems.append(f"Phase 9 output directory not found at {PHASE9_OUTPUT_DIR} (cannot cross-validate)")
    if not PHASE10_OUTPUT_DIR.exists():
        problems.append(f"Phase 10 output directory not found at {PHASE10_OUTPUT_DIR} (cannot cross-validate)")

    if problems:
        print("BLOCKED: preconditions not satisfied, stopping rather than proceeding:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        sys.exit(1)

    print("Preconditions verified:")
    print(f"  - Phase 8 cache: all {len(INCLUDED_EVENTS) * 3} expected files present")
    print(f"  - Candidate policy hash matches Phase 10 report: {EXPECTED_CANDIDATE_POLICY_HASH}")
    print(f"  - Phase 9 output present: {PHASE9_OUTPUT_DIR.name}")
    print(f"  - Phase 10 output present: {PHASE10_OUTPUT_DIR.name}")


def _detection_counts_by_source_and_label(records) -> dict:
    counts: dict = defaultdict(lambda: defaultdict(int))
    for r in records:
        if not r.available:
            continue
        for d in r.detections:
            if d.confidence >= 0.35:
                counts[r.source_id][d.label.lower()] += 1
    return {src: dict(labels) for src, labels in counts.items()}


def main() -> int:
    config = load_frozen_config(REPO_ROOT / "configs" / "frozen_experiment_v1.yaml")
    config.verify_all_safeguards(repo_root=REPO_ROOT)

    _verify_preconditions(config)

    out_dir = (
        REPO_ROOT / "results" / "r04_sync_estimation"
        / f"phase10_1_restricted_comparison_{datetime.datetime.now(datetime.UTC):%Y%m%dT%H%M%SZ}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    processor = LayerBEventProcessor(repo_root=REPO_ROOT, config=config, cache_dir=PHASE8_CACHE_DIR)
    calib_manifest = yaml.safe_load(CALIBRATION_MANIFEST_PATH.read_text())

    run_manifest: dict = {
        "run_mode": "phase10_1_restricted_candidate_comparison",
        "authorization_scope": "Restricted to exactly the 11 existing CALIBRATION_SUPPORTED authorized events. "
        "No full-cohort B3/B4/B6/B7 execution. No deployment authorized by this run.",
        "timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "frozen_experiment_config_path": "configs/frozen_experiment_v1.yaml",
        "frozen_experiment_config_canonical_hash": config.canonical_hash,
        "frozen_policy_doc": "configs/decision_policy_v1.yaml",
        "candidate_policy_doc": "configs/decision_policy_v2_candidate.yaml",
        "candidate_policy_canonical_hash": EXPECTED_CANDIDATE_POLICY_HASH,
        "candidate_policy_version": CANDIDATE_POLICY_VERSION,
        "checkpoint_hashes": {
            "vision": getattr(config.checkpoints.vision, "expected_sha256", None) or "see configs/frozen_experiment_v1.yaml",
            "audio_v3": getattr(config.checkpoints.audio_v3, "expected_sha256", None) or "see configs/frozen_experiment_v1.yaml",
        },
        "source_evidence": "Phase 8's cached YOLOv8n/CompactTrainHornCNN output only -- no new model inference in this phase.",
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
        back_offset_s = calib_manifest["events"][event_key]["camera_back"]["offset_s"]

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

        # Naive duration: EXACTLY Phase 9's/Phase 10's computation (max of
        # raw, unaligned local timestamps mixed across sources) -- kept
        # identical on purpose so this run's results under it can be
        # directly cross-validated against those prior runs' results.
        naive_duration_s = max(
            [r.timestamp_s for r in all_v_recs] + [r.timestamp_s for r in front_a_recs], default=30.0
        )
        # Corrected duration: accounts for the back camera's validated
        # offset, so its full, already-cached evidence window is actually
        # included in the replay rather than silently truncated.
        front_max = max([r.timestamp_s for r in front_v_recs], default=0.0)
        back_max_local = max([r.timestamp_s for r in back_v_recs], default=0.0)
        audio_max = max([r.timestamp_s for r in front_a_recs], default=0.0)
        corrected_duration_s = max(front_max, back_max_local + back_offset_s, audio_max)

        event_out_dir = out_dir / cohort / event_id
        event_out_dir.mkdir(parents=True, exist_ok=True)

        event_entry: dict = {
            "back_offset_s": back_offset_s,
            "naive_duration_s": naive_duration_s,
            "corrected_duration_s": corrected_duration_s,
            "duration_truncation_s": corrected_duration_s - naive_duration_s,
            "detection_counts_by_camera_and_class": {
                "camera_1_front": _detection_counts_by_source_and_label(front_v_recs),
                "camera_2_back": _detection_counts_by_source_and_label(back_v_recs),
            },
            "runs": {},
        }

        for duration_label, duration_s in (("naive", naive_duration_s), ("corrected", corrected_duration_s)):
            for policy_label, engine_factory, approach_fn, departure_fn in (
                ("frozen", MultimodalDecisionEngine, None, None),
                ("candidate", MultimodalDecisionEngineV2Candidate, has_unambiguous_approach_label, has_unambiguous_departure_label),
            ):
                kwargs = dict(
                    vision_records=all_v_recs, audio_records=front_a_recs, duration_s=duration_s,
                    stride_s=config.timing.tick_s, event_id=event_id,
                    condition=f"{policy_label}_{duration_label}", config=config,
                    sync_aligner=validated_alignment.aligner, window_tolerance_s=0.25,
                    engine_factory=engine_factory,
                )
                if approach_fn is not None:
                    kwargs["approach_fn"] = approach_fn
                    kwargs["departure_fn"] = departure_fn
                result = run_with_diagnostics(**kwargs)

                run_key = f"{policy_label}_{duration_label}"
                (event_out_dir / f"{run_key}_diagnostic_ticks.jsonl").write_text(
                    "\n".join(json.dumps(tick_to_dict(tk)) for tk in result.ticks) + ("\n" if result.ticks else ""),
                    encoding="utf-8",
                )
                (event_out_dir / f"{run_key}_rejections.json").write_text(
                    json.dumps(asdict(result.rejections), indent=2), encoding="utf-8",
                )

                reached_clear = any(t.resulting_state == "CROSSING_CLEAR" for t in result.ticks)
                states = [t.resulting_state for t in result.ticks]
                rule_counts: dict[str, int] = {}
                new_train_interrupts = []
                for t in result.ticks:
                    if t.rule_id:
                        rule_counts[t.rule_id] = rule_counts.get(t.rule_id, 0) + 1
                    if t.rule_id and "NEW_TRAIN_INTERRUPT" in t.rule_id:
                        new_train_interrupts.append({"timestamp_s": t.timestamp_s, "previous_state": t.previous_state})
                stale_abort_count = sum(1 for t in result.ticks if t.rule_id and "STALE_SOURCE_ABORT" in t.rule_id)

                event_entry["runs"][run_key] = {
                    "tick_count": len(result.ticks),
                    "reached_crossing_clear": reached_clear,
                    "final_state": states[-1] if states else None,
                    "rejected_observations": result.rejections.total_rejected,
                    "rejections_by_reason": result.rejections.by_reason,
                    "rule_counts": rule_counts,
                    "new_train_interrupt_count": len(new_train_interrupts),
                    "new_train_interrupt_events": new_train_interrupts,
                    "stale_source_abort_count": stale_abort_count,
                    "fault_occurred": result.fault_occurred,
                    "closed_duration_s": result.closed_duration_s,
                    "total_duration_s": result.total_duration_s,
                }

        run_manifest["events"][event_key] = event_entry
        naive_frozen = event_entry["runs"]["frozen_naive"]["reached_crossing_clear"]
        naive_candidate = event_entry["runs"]["candidate_naive"]["reached_crossing_clear"]
        corrected_frozen = event_entry["runs"]["frozen_corrected"]["reached_crossing_clear"]
        corrected_candidate = event_entry["runs"]["candidate_corrected"]["reached_crossing_clear"]
        row = (
            f"  {event_key}: truncated_by={event_entry['duration_truncation_s']:.2f}s | "
            f"naive(frozen={naive_frozen},candidate={naive_candidate}) | "
            f"corrected(frozen={corrected_frozen},candidate={corrected_candidate})"
        )
        summary_rows.append(row)
        print(f"Processed {event_key}: {row.strip()}")

    # Cross-validate against Phase 9 (frozen, naive duration must match
    # exactly) and Phase 10 (candidate, naive duration must match exactly).
    validation: dict = {"exactly_11_events": len(run_manifest["events"]) == 11}
    phase9_mismatches = []
    phase10_mismatches = []
    for event_key in INCLUDED_EVENTS:
        _, event_id = event_key.split("/")
        p9_file = PHASE9_OUTPUT_DIR / "train_events" / event_id / "diagnostic_ticks.jsonl"
        if p9_file.exists():
            p9_ticks = [json.loads(l) for l in p9_file.read_text().splitlines() if l.strip()]
            p9_clear = any(t["resulting_state"] == "CROSSING_CLEAR" for t in p9_ticks)
            this_clear = run_manifest["events"][event_key]["runs"]["frozen_naive"]["reached_crossing_clear"]
            if p9_clear != this_clear:
                phase9_mismatches.append(event_key)
        p10_file = PHASE10_OUTPUT_DIR / "train_events" / event_id / "candidate_diagnostic_ticks.jsonl"
        if p10_file.exists():
            p10_ticks = [json.loads(l) for l in p10_file.read_text().splitlines() if l.strip()]
            p10_clear = any(t["resulting_state"] == "CROSSING_CLEAR" for t in p10_ticks)
            this_clear = run_manifest["events"][event_key]["runs"]["candidate_naive"]["reached_crossing_clear"]
            if p10_clear != this_clear:
                phase10_mismatches.append(event_key)
    validation["frozen_reproduces_phase9_naive_duration"] = not phase9_mismatches
    validation["frozen_phase9_mismatches"] = phase9_mismatches
    validation["candidate_reproduces_phase10_naive_duration"] = not phase10_mismatches
    validation["candidate_phase10_mismatches"] = phase10_mismatches
    run_manifest["validation"] = validation

    (out_dir / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")

    print(f"\nPhase 10.1 restricted comparison complete. Output: {out_dir}")
    print(f"\nValidation: exactly_11_events={validation['exactly_11_events']}")
    print(f"Validation: frozen reproduces Phase 9 (naive duration)={validation['frozen_reproduces_phase9_naive_duration']} (mismatches: {phase9_mismatches})")
    print(f"Validation: candidate reproduces Phase 10 (naive duration)={validation['candidate_reproduces_phase10_naive_duration']} (mismatches: {phase10_mismatches})")
    print("\nSummary:")
    for row in summary_rows:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
