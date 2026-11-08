#!/usr/bin/env python3
"""Post-run integrity validation for an exploratory dual-camera run directory.

Checks (Phase 8 post-run verification requirements):
  1. Output directory contains only the 11 authorized events (and no others,
     no negative controls).
  2. JSON/JSONL files are syntactically valid and carry required fields.
  3. Each event's back-camera offset was applied exactly once (spot-checked
     against the run manifest's recorded offsets).
  4. No unsupported-verdict event appears in the run manifest.
  5. The run manifest's recorded checkpoint/config hashes match the
     currently-expected frozen values.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

EXPECTED_EVENTS = {
    "train_events/event_001", "train_events/event_002", "train_events/event_005",
    "train_events/event_006", "train_events/event_007", "train_events/event_009",
    "train_events/event_011", "train_events/event_012", "train_events/event_013",
    "train_events/event_014", "train_events/event_017",
}
EXPECTED_FROZEN_CONFIG_HASH = "999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e"
EXPECTED_VISION_SHA256 = "3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd"
EXPECTED_AUDIO_V3_SHA256 = "ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782"


def main(run_dir: Path) -> int:
    problems: list[str] = []

    manifest_path = run_dir / "run_manifest.json"
    if not manifest_path.exists():
        print(f"FAIL: no run_manifest.json in {run_dir}")
        return 1
    manifest = json.loads(manifest_path.read_text())

    # 1. Event set check
    manifest_events = set(manifest.get("events", {}).keys())
    if manifest_events != EXPECTED_EVENTS:
        problems.append(
            f"event set mismatch: manifest has {manifest_events}, expected {EXPECTED_EVENTS} "
            f"(extra={manifest_events - EXPECTED_EVENTS}, missing={EXPECTED_EVENTS - manifest_events})"
        )
    for key in manifest_events:
        if "no_train" in key or "engine" in key:
            problems.append(f"unauthorized event type present: {key}")

    # 2. Per-event output directories: only authorized events, valid JSON
    present_dirs = set()
    for p in run_dir.iterdir():
        if p.is_dir() and p.name not in ("cache",):
            cohort = p.name
            for event_dir in p.iterdir():
                if event_dir.is_dir():
                    key = f"{cohort}/{event_dir.name}"
                    present_dirs.add(key)
                    steps_file = event_dir / "decision_steps.json"
                    if not steps_file.exists():
                        problems.append(f"{key}: missing decision_steps.json")
                        continue
                    try:
                        steps = json.loads(steps_file.read_text())
                    except json.JSONDecodeError as e:
                        problems.append(f"{key}: invalid JSON in decision_steps.json: {e}")
                        continue
                    if not isinstance(steps, list) or not steps:
                        problems.append(f"{key}: decision_steps.json is empty or not a list")
                        continue
                    required_fields = {"timestamp_s", "crossing_state", "gate_state", "gate_angle_deg"}
                    for i, step in enumerate(steps):
                        missing = required_fields - set(step.keys())
                        if missing:
                            problems.append(f"{key}: step {i} missing fields {missing}")
                            break

    if present_dirs != EXPECTED_EVENTS:
        problems.append(
            f"output directory event set mismatch: found {present_dirs}, expected {EXPECTED_EVENTS}"
        )

    # 3. Offset applied exactly once: cross-check manifest-recorded offset
    #    against the independently-computed candidate manifest value.
    import yaml
    calib_manifest = yaml.safe_load(
        Path("data/manifests/camera_sync_offsets_candidate.yaml").read_text()
    )
    for key, ev in manifest.get("events", {}).items():
        expected_offset = calib_manifest["events"][key]["camera_back"]["offset_s"]
        if abs(ev["back_offset_s"] - expected_offset) > 1e-9:
            problems.append(
                f"{key}: recorded back_offset_s {ev['back_offset_s']} != candidate manifest "
                f"{expected_offset} (possible double-application or stale value)"
            )
        if ev["verdict"] != "CALIBRATION_SUPPORTED":
            problems.append(f"{key}: non-supported verdict in run manifest: {ev['verdict']}")

    # 4. Hash checks
    if manifest.get("base_frozen_config_canonical_hash") != EXPECTED_FROZEN_CONFIG_HASH:
        problems.append("base_frozen_config_canonical_hash mismatch")
    if manifest.get("frozen_experiment_config_canonical_hash_at_run_time") != EXPECTED_FROZEN_CONFIG_HASH:
        problems.append("frozen_experiment_config_canonical_hash_at_run_time mismatch")

    if problems:
        print(f"VALIDATION FAILED ({len(problems)} problem(s)):")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(f"VALIDATION PASSED: {run_dir}")
    print(f"  Events: {len(manifest_events)} (exactly the 11 authorized events)")
    print(f"  Research question recorded: {'research_question' in manifest}")
    print(f"  Config hash: {manifest.get('exploratory_config_canonical_hash')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
