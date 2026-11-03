#!/usr/bin/env python3
"""Exploratory Dual-Camera Fusion — CALIBRATION_SUPPORTED Subset Only.

THIS IS NOT THE PRIMARY FROZEN EXPERIMENT. It executes dual-camera vision
fusion (the B3/B4-style condition) for ONLY the events whose calibration
candidate currently carries a `CALIBRATION_SUPPORTED` verdict, using a
manifest-backed, event-scoped, fail-closed `SyncAligner` loaded fresh for
every event. It is driven by
`configs/exploratory_dual_camera_v1_supported_subset.yaml`, a separately
versioned configuration with its own canonical hash that neither modifies
nor is referenced by `configs/frozen_experiment_v1.yaml`.

Safety gates, all of which must pass before any inference runs:
  1. The exploratory configuration file's `authorized_for_execution` field
     must be `true` (it ships as `false`).
  2. The CLI flag `--authorize-exploratory-run` must be passed explicitly.
  3. For every included event, `load_validated_sync_aligner` must succeed
     against the CURRENT state of `data/manifests/camera_sync_offsets_candidate.yaml`
     and the CURRENT bytes of the source video files on disk -- a static
     inclusion list in the exploratory config is re-validated live, every
     run, and is never trusted by itself.

Without `--execute`, this script runs in `--dry-run` mode (the default): it
performs every one of the above checks, builds the per-event
`ValidatedAlignment` objects, and reports exactly what it would do, WITHOUT
touching any video file, running any model, or writing any inference
output. This lets the wiring be exercised and verified without ever
executing the dual-camera experiment itself -- which this script's
docstring and every one of its gates exist specifically to prevent until a
human has explicitly authorized it.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

import yaml  # noqa: E402

from railway_detection.data.sync_calibration import (  # noqa: E402
    CalibrationNotAcceptedError,
    load_validated_sync_aligner,
)
from railway_detection.experiments.frozen_config import load_frozen_config  # noqa: E402
from railway_detection.experiments.layer_b_processor import LayerBEventProcessor  # noqa: E402
from railway_detection.simulation.runner import EventSimulationRunner  # noqa: E402
from railway_detection.utils.logging import get_logger  # noqa: E402

logger = get_logger("scripts.run_exploratory_dual_camera_subset")

EXPLORATORY_CONFIG_PATH = REPO_ROOT / "configs" / "exploratory_dual_camera_v1_supported_subset.yaml"
CALIBRATION_MANIFEST_PATH = REPO_ROOT / "data" / "manifests" / "camera_sync_offsets_candidate.yaml"


def _canonical_hash_of_yaml(path: Path) -> str:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    cj = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(cj.encode("utf-8")).hexdigest()


def gate_check_authorization(exploratory_cfg: dict[str, Any], cli_authorized: bool) -> None:
    """Both the config file's flag AND the CLI flag must independently agree
    this run is authorized. Either one being false blocks execution."""
    meta = exploratory_cfg["exploratory_metadata"]
    config_authorized = bool(meta.get("authorized_for_execution", False))
    if not (config_authorized and cli_authorized):
        raise PermissionError(
            "Exploratory dual-camera run is NOT authorized. "
            f"configs/exploratory_dual_camera_v1_supported_subset.yaml "
            f"authorized_for_execution={config_authorized}; "
            f"--authorize-exploratory-run passed={cli_authorized}. "
            "Both must be true. This is intentional: a human researcher must "
            "explicitly flip the config file's flag (recording who and when) "
            "AND pass the CLI flag before any inference runs."
        )


def validate_all_included_events(
    exploratory_cfg: dict[str, Any],
) -> dict[str, Any]:
    """Re-validate calibration for every included event against the LIVE
    manifest and LIVE source media, never trusting the static inclusion
    list in the exploratory config by itself. Returns {event_key: ValidatedAlignment}.
    Raises CalibrationNotAcceptedError on first event that fails to
    re-validate -- this is deliberately fail-closed and deliberately not
    "skip the bad ones and continue", since a changed verdict for even one
    event means the static config is stale and must be regenerated and
    reviewed, not silently worked around.
    """
    included = exploratory_cfg["included_events_calibration_supported"]
    results: dict[str, Any] = {}
    for event_key in included:
        results[event_key] = load_validated_sync_aligner(
            CALIBRATION_MANIFEST_PATH,
            event_key,
            repo_root=REPO_ROOT,
            allow_candidate_status=True,  # this IS the explicitly-labeled exploratory path
        )
    return results


def build_run_manifest(
    exploratory_cfg: dict[str, Any],
    exploratory_cfg_hash: str,
    validated: dict[str, Any],
    mode: str,
    config_path: Path,
) -> dict[str, Any]:
    return {
        "run_mode": mode,
        "timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "exploratory_config_path": str(config_path.relative_to(REPO_ROOT)),
        "exploratory_config_canonical_hash": exploratory_cfg_hash,
        "exploratory_config_version": exploratory_cfg["exploratory_metadata"]["version"],
        "base_frozen_config_canonical_hash": exploratory_cfg["exploratory_metadata"][
            "base_config_canonical_hash"
        ],
        "calibration_manifest_path": str(CALIBRATION_MANIFEST_PATH.relative_to(REPO_ROOT)),
        "calibration_manifest_version": exploratory_cfg["exploratory_metadata"][
            "calibration_manifest_version"
        ],
        "included_event_count": len(validated),
        "events": {
            event_key: {
                "verdict": v.verdict,
                "manifest_version": v.manifest_version,
                "front_source_id": v.front_source_id,
                "back_source_id": v.back_source_id,
                "front_offset_s": v.front_offset_s,
                "back_offset_s": v.back_offset_s,
                "uncertainty_s": v.uncertainty_s,
                "front_sha256": v.front_sha256,
                "back_sha256": v.back_sha256,
            }
            for event_key, v in validated.items()
        },
    }


def run_dry(exploratory_cfg: dict[str, Any], exploratory_cfg_hash: str, config_path: Path) -> int:
    print("=== DRY RUN: exploratory dual-camera subset ===")
    print(f"Config: {config_path}")
    print(f"Config canonical hash: {exploratory_cfg_hash}")
    print(
        f"authorized_for_execution (config): "
        f"{exploratory_cfg['exploratory_metadata'].get('authorized_for_execution', False)}"
    )
    print("\nRe-validating calibration for every included event against the LIVE manifest "
          "and LIVE source media (no inference, no model load, no video decode)...")

    validated = validate_all_included_events(exploratory_cfg)
    print(f"\nAll {len(validated)} included events re-validated as CALIBRATION_SUPPORTED:")
    for event_key, v in sorted(validated.items()):
        print(
            f"  {event_key}: offset_s={v.back_offset_s:+.4f}  uncertainty_s={v.uncertainty_s}  "
            f"front_sha256={v.front_sha256[:12]}...  back_sha256={v.back_sha256[:12]}..."
        )

    manifest = build_run_manifest(
        exploratory_cfg, exploratory_cfg_hash, validated, mode="dry_run", config_path=config_path
    )
    out_dir = REPO_ROOT / "results" / "r04_sync_estimation" / "exploratory_dry_run"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "dry_run_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nDry-run manifest written to {out_path}")
    print(
        "\nNo video was decoded, no model was loaded, and no inference was executed. "
        "To actually run, pass --execute --authorize-exploratory-run AND set "
        "authorized_for_execution: true in the exploratory config file."
    )
    return 0


def run_live(
    exploratory_cfg: dict[str, Any],
    exploratory_cfg_hash: str,
    cli_authorized: bool,
    config_path: Path,
    research_question: str | None = None,
) -> int:
    gate_check_authorization(exploratory_cfg, cli_authorized)
    validated = validate_all_included_events(exploratory_cfg)

    config = load_frozen_config(REPO_ROOT / "configs" / "frozen_experiment_v1.yaml")
    config.verify_all_safeguards(repo_root=REPO_ROOT)

    out_dir = (
        REPO_ROOT
        / "results"
        / "r04_sync_estimation"
        / f"exploratory_live_run_{datetime.datetime.now(datetime.UTC):%Y%m%dT%H%M%SZ}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_run_manifest(
        exploratory_cfg, exploratory_cfg_hash, validated, mode="live_execution", config_path=config_path
    )
    if research_question:
        manifest["research_question"] = research_question
        manifest["research_question_note"] = (
            "Acoustic-lag reproducibility (the basis of the CALIBRATION_SUPPORTED verdict) is "
            "NOT independent validation of true camera hardware synchronization. See "
            "docs/R04_CALIBRATION_VALIDATION_REPORT.md and the Phase 7 section of "
            "docs/R04_IMPLEMENTATION_AND_UNBLOCK_REPORT.md."
        )
    manifest["frozen_experiment_config_canonical_hash_at_run_time"] = config.canonical_hash
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    processor = LayerBEventProcessor(repo_root=REPO_ROOT, config=config, cache_dir=out_dir / "cache")
    yolo_ckpt = REPO_ROOT / config.checkpoints.vision.path
    audio_ckpt = REPO_ROOT / config.checkpoints.audio_v3.path

    for event_key, validated_alignment in sorted(validated.items()):
        cohort, event_id = event_key.split("/")
        event_dir = REPO_ROOT / "data" / "raw" / "layer_b" / "v2" / cohort / event_id
        front_mov = event_dir / "camera_front.mov"
        back_mov = event_dir / "camera_back.mov"
        print(f"Processing {event_key} with validated offset {validated_alignment.back_offset_s:+.4f}s ...")

        audio_paths = processor.extract_audio(event_dir)
        front_wav = audio_paths.get("front")

        front_v_recs = processor.run_vision_inference(
            video_path=front_mov,
            checkpoint_path=yolo_ckpt,
            source_id=validated_alignment.front_source_id,
            target_fps=config.vision.sampling_fps,
            conf=config.vision.confidence_threshold_approach,
            use_cache=True,
        )
        back_v_recs = processor.run_vision_inference(
            video_path=back_mov,
            checkpoint_path=yolo_ckpt,
            source_id=validated_alignment.back_source_id,
            target_fps=config.vision.sampling_fps,
            conf=config.vision.confidence_threshold_approach,
            use_cache=True,
        )
        front_a_recs = processor.run_audio_inference(
            wav_path=front_wav,
            checkpoint_path=audio_ckpt,
            source_id="audio_1",
            threshold=config.audio.operating_threshold,
            cohort=cohort,
            event_id=event_id,
            use_cache=True,
        )

        all_v_recs = list(front_v_recs) + list(back_v_recs)
        duration_s = max(
            [r.timestamp_s for r in all_v_recs] + [r.timestamp_s for r in front_a_recs], default=30.0
        )
        frames = processor.build_multimodal_frames(
            vision_records=all_v_recs,
            audio_records=front_a_recs,
            duration_s=duration_s,
            stride_s=config.timing.tick_s,
            sync_aligner=validated_alignment.aligner,
        )
        sim_runner = EventSimulationRunner(config=config)
        sim_result = sim_runner.run_frames(
            frames, event_id=event_key, scenario_name="B4_exploratory_supported_subset"
        )

        event_out_dir = out_dir / cohort / event_id
        event_out_dir.mkdir(parents=True, exist_ok=True)
        (event_out_dir / "decision_steps.json").write_text(
            json.dumps(
                [
                    {
                        "timestamp_s": s.timestamp_s,
                        "crossing_state": s.crossing_state,
                        "gate_state": s.gate_state,
                        "gate_angle_deg": s.gate_angle_deg,
                    }
                    for s in sim_result.steps
                ],
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"  -> {len(sim_result.steps)} decision steps written to {event_out_dir}")

    print(f"\nExploratory live execution complete. Outputs in {out_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Exploratory dual-camera fusion on the CALIBRATION_SUPPORTED subset only."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run inference (default is --dry-run validation only).",
    )
    parser.add_argument(
        "--authorize-exploratory-run",
        action="store_true",
        help="Explicit human opt-in. Required, together with the config file's own "
        "authorized_for_execution flag, for --execute to do anything.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to the exploratory configuration file. Defaults to the unauthorized "
        "v1.0.0 config (configs/exploratory_dual_camera_v1_supported_subset.yaml), which "
        "always ships with authorized_for_execution: false and can never itself launch "
        "inference. To run, point this at a separately versioned, explicitly authorized "
        "config file (e.g. one with its own authorization_record) -- the default config "
        "is never edited in place for this purpose.",
    )
    parser.add_argument(
        "--research-question",
        type=str,
        default="Does event-scoped acoustic-lag alignment of the selected front/back camera "
        "streams change multimodal evidence and state-machine behavior relative to "
        "independent camera processing?",
        help="Recorded verbatim into the run manifest; not used to alter execution.",
    )
    args = parser.parse_args()

    config_path = (args.config if args.config is not None else EXPLORATORY_CONFIG_PATH).resolve()
    exploratory_cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    exploratory_cfg_hash = _canonical_hash_of_yaml(config_path)

    try:
        if args.execute:
            return run_live(
                exploratory_cfg,
                exploratory_cfg_hash,
                args.authorize_exploratory_run,
                config_path=config_path,
                research_question=args.research_question,
            )
        return run_dry(exploratory_cfg, exploratory_cfg_hash, config_path=config_path)
    except (PermissionError, CalibrationNotAcceptedError) as exc:
        print(f"\nBLOCKED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
