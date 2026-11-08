#!/usr/bin/env python3
"""Extract candidate-synchronized frame pairs for human visual-landmark review.

Given an event and a proposed offset_s, extracts the front-camera frame at
front_t_s and the back-camera frame at (front_t_s - offset_s) -- i.e. the
same physical instant under the candidate calibration -- so an independent human
reviewer can inspect both frames and judge whether physical visual landmarks match.

GOVERNANCE & MEDIA ACCESS RESTRICTION:
  Under the October 19-20, 2026 media-access hold, direct access to raw video
  files (`data/raw/layer_b/v2/*/*.mov`) is restricted. This script enforces that
  safeguard by default:
  - Running without authorization will raise a PermissionError and refuse to invoke ffmpeg.
  - To simulate and inspect frame timestamps safely without media access, use `--dry-run`.
  - To list the preconfigured prioritization queue, use `--list-queue`.
  - Access is governed only by a recorded on-disk `data/governance/AUTH-MEDIA-ACCESS.json`,
    verified at every file opener. No command-line flag or environment variable can grant it.

REVIEW RECORD CONTRACT:
  This script performs NO automated verification. It writes a template `review_record.json`
  with `human_verified: null` and `reviewer: null`. An identifiable human practitioner must
  inspect the extracted frames, verify physical alignment, and record their identity,
  determination (`human_verified: true|false`), and observation notes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from railway_detection.safety.media_guard import (  # noqa: E402
    precheck_operation_authorized,
    require_media_authorization,
)

LAYER_B_ROOT = REPO_ROOT / "data" / "raw" / "layer_b" / "v2"
OUT_ROOT = REPO_ROOT / "scratch" / "r04_visual_review"

# Preconfigured Visual Review Queue across all non-supported candidate events
# Prioritized by acoustic quality, failure taxonomy, and operational impact.
REVIEW_QUEUE: dict[str, dict[str, Any]] = {
    "train_events/event_010": {
        "priority": 1,
        "cohort": "train_events",
        "event_id": "event_010",
        "candidate_offset_s": 2.7158,
        "front_t_s": 3.500,
        "back_t_s": 0.784,
        "tolerance_s": 0.10,
        "expected_landmark": "Locomotive cowcatcher/pilot crossing roadway occupancy line on camera_front; entering frame on camera_back",
        "secondary_pair": {
            "front_t_s": 5.816,
            "back_t_s": 3.100,
            "expected_landmark": "Locomotive rear coupler clearing vegetable vendor stall clearance line on camera_back (T3)"
        },
        "taxonomy": "METADATA_CLOCK_DISCREPANCY",
        "rationale": "Rock-solid 0.1 ms acoustic stability (PSR 2.14, SNR 22.3 dB); blocked solely by QuickTime -17.0s container clock jump."
    },
    "train_events/event_008": {
        "priority": 2,
        "cohort": "train_events",
        "event_id": "event_008",
        "candidate_offset_s": 3.6479,
        "front_t_s": 6.848,
        "back_t_s": 3.200,
        "tolerance_s": 0.10,
        "expected_landmark": "Lead locomotive rear clearing departure roadway line (T3 on back camera)",
        "secondary_pair": {
            "front_t_s": 15.000,
            "back_t_s": 11.352,
            "expected_landmark": "Mid-train passenger coach window/door alignment across vertical reference stanchion"
        },
        "taxonomy": "HARMONIC_PERIODICITY",
        "rationale": "Session 1 container clock anomaly (-33.0s QT delta); stable 3.3 ms sub-window acoustic peak."
    },
    "no_train_events/event_003": {
        "priority": 3,
        "cohort": "no_train_events",
        "event_id": "event_003",
        "candidate_offset_s": -0.4022,
        "front_t_s": 10.000,
        "back_t_s": 10.402,
        "tolerance_s": 0.05,
        "expected_landmark": "Road vehicle (rickshaw / motorcycle) or pedestrian crossing physical track centerline",
        "secondary_pair": {
            "front_t_s": 15.000,
            "back_t_s": 15.402,
            "expected_landmark": "Pedestrian footstep or bicycle traversing roadway boundary"
        },
        "taxonomy": "ADJACENT_SHOULDER",
        "rationale": "Sub-millisecond (0.3 ms) acoustic window stability, PSR 1.96 misses 2.0 due to 51.3 ms reverberation shoulder."
    },
    "train_events/event_003": {
        "priority": 4,
        "cohort": "train_events",
        "event_id": "event_003",
        "candidate_offset_s": 3.7272,
        "front_t_s": 6.927,
        "back_t_s": 3.200,
        "tolerance_s": 0.10,
        "expected_landmark": "Lead locomotive rear clearing crossing roadway plane (T3 on back camera)",
        "secondary_pair": {
            "front_t_s": 15.000,
            "back_t_s": 11.273,
            "expected_landmark": "Passenger coach body panel alignment across track axis"
        },
        "taxonomy": "HARMONIC_PERIODICITY",
        "rationale": "Window spread 1.9 ms, SNR 18.5 dB; 712.9 ms harmonic periodicity."
    },
    "train_events/event_016": {
        "priority": 5,
        "cohort": "train_events",
        "event_id": "event_016",
        "candidate_offset_s": 3.2592,
        "front_t_s": 5.000,
        "back_t_s": 1.741,
        "tolerance_s": 0.10,
        "expected_landmark": "Locomotive pilot crossing front camera transverse roadway occupancy line (T2)",
        "secondary_pair": {
            "front_t_s": 6.659,
            "back_t_s": 3.400,
            "expected_landmark": "Locomotive rear coupler clearing vendor stall clearance line (T3)"
        },
        "taxonomy": "HARMONIC_PERIODICITY",
        "rationale": "Window spread 2.9 ms, SNR 17.1 dB, PSR 1.64; QuickTime delta +4.0s."
    },
    "train_events/event_018": {
        "priority": 6,
        "cohort": "train_events",
        "event_id": "event_018",
        "candidate_offset_s": 7.8752,
        "front_t_s": 11.675,
        "back_t_s": 3.800,
        "tolerance_s": 0.10,
        "expected_landmark": "Locomotive rear coupler clearing crossing departure boundary (T3 on back camera)",
        "secondary_pair": {
            "front_t_s": 20.000,
            "back_t_s": 12.125,
            "expected_landmark": "Mid-consist passenger coach window alignment"
        },
        "taxonomy": "HARMONIC_PERIODICITY",
        "rationale": "Window spread 12.8 ms, high SNR 28.5 dB; QuickTime delta +8.0s."
    },
    "train_events/event_019": {
        "priority": 7,
        "cohort": "train_events",
        "event_id": "event_019",
        "candidate_offset_s": 6.6558,
        "front_t_s": 9.956,
        "back_t_s": 3.300,
        "tolerance_s": 0.10,
        "expected_landmark": "Lead locomotive rear clearing vendor stall departure line (T3)",
        "secondary_pair": {
            "front_t_s": 20.000,
            "back_t_s": 13.344,
            "expected_landmark": "Passenger coach livery stripe registration across roadway"
        },
        "taxonomy": "HARMONIC_PERIODICITY",
        "rationale": "Window spread 3.0 ms, SNR 15.5 dB, PSR 1.53; QuickTime delta +7.0s."
    },
    "train_events/event_021": {
        "priority": 8,
        "cohort": "train_events",
        "event_id": "event_021",
        "candidate_offset_s": -2.8056,
        "front_t_s": 4.100,
        "back_t_s": 6.906,
        "tolerance_s": 0.10,
        "expected_landmark": "Locomotive pilot crossing front camera transverse roadway occupancy line (T2)",
        "secondary_pair": {
            "front_t_s": 0.794,
            "back_t_s": 3.600,
            "expected_landmark": "Locomotive rear coupler clearing departure boundary (T3 on back camera)"
        },
        "taxonomy": "HARMONIC_PERIODICITY",
        "rationale": "Session 2 reversed start order; window spread 4.9 ms, SNR 18.8 dB; QuickTime delta -3.0s."
    },
    "train_events/event_023": {
        "priority": 9,
        "cohort": "train_events",
        "event_id": "event_023",
        "candidate_offset_s": 1.2277,
        "front_t_s": 3.600,
        "back_t_s": 2.372,
        "tolerance_s": 0.10,
        "expected_landmark": "Locomotive pilot crossing front camera roadway occupancy line (T2)",
        "secondary_pair": {
            "front_t_s": 4.528,
            "back_t_s": 3.300,
            "expected_landmark": "Lead locomotive rear clearing vendor stall clearance line (T3)"
        },
        "taxonomy": "HARMONIC_PERIODICITY",
        "rationale": "Window spread 4.8 ms, 257.9 ms bogie axle spacing harmonic; QuickTime delta +1.0s."
    },
    "no_train_events/event_001": {
        "priority": 10,
        "cohort": "no_train_events",
        "event_id": "event_001",
        "candidate_offset_s": 1.4277,
        "front_t_s": 10.000,
        "back_t_s": 8.572,
        "tolerance_s": 0.05,
        "expected_landmark": "Road vehicle (motorcycle / car) or pedestrian crossing road boundary",
        "secondary_pair": {
            "front_t_s": 15.000,
            "back_t_s": 13.572,
            "expected_landmark": "Pedestrian traversing crossing plane"
        },
        "taxonomy": "ADJACENT_SHOULDER",
        "rationale": "Window spread 1.9 ms, SNR 15.6 dB; 55.7 ms shoulder proximity."
    },
    "engine_events/event_001": {
        "priority": 11,
        "cohort": "engine_events",
        "event_id": "event_001",
        "candidate_offset_s": 3.4964,
        "front_t_s": 6.200,
        "back_t_s": 2.704,
        "tolerance_s": 0.10,
        "expected_landmark": "Trailing buffer/coupler of single locomotive clearing front roadway lens plane (T3)",
        "secondary_pair": {
            "front_t_s": 4.500,
            "back_t_s": 1.004,
            "expected_landmark": "Locomotive cab center position across physical rail segment"
        },
        "taxonomy": "MODERATE_ACOUSTIC_MARGIN",
        "rationale": "Single locomotive shunt; 7.87s/9.80s clip with 4.38s physical overlap."
    },
    "train_events/event_004": {
        "priority": 12,
        "cohort": "train_events",
        "event_id": "event_004",
        "candidate_offset_s": 4.9001,
        "secondary_offset_s": 5.1398,
        "front_t_s": 15.000,
        "back_t_s": 10.100,
        "back_t_s_secondary": 9.860,
        "tolerance_s": 0.10,
        "expected_landmark": "Coach body panel registration: arbitrate between Hypothesis A (4.9001s -> t_back=10.100s) and Hypothesis B (5.1398s -> t_back=9.860s, delta 239.7 ms = 7.2 frames)",
        "taxonomy": "COMPETING_MULTIPATH",
        "rationale": "Acoustic multipath reflection causing window hopping; visual arbitration required to select true optical line-of-sight."
    },
}


def compute_sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    require_media_authorization(path, "HASH_RAW_MEDIA")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def check_media_access_authorization(repo_root: Path | None = None) -> None:
    """Verify that restricted media access has been formally authorized via on-disk AUTH-MEDIA-ACCESS."""
    root = repo_root or REPO_ROOT
    precheck_operation_authorized("FRAME_EXTRACTION", repo_root=root)


def extract_frame(video_path: Path, t_s: float, out_path: Path, dry_run: bool = False) -> bool:
    """Extract a single frame at timestamp t_s using ffmpeg."""
    require_media_authorization(video_path, "FRAME_EXTRACTION")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-ss", f"{max(t_s, 0.0):.3f}",
        "-i", str(video_path),
        "-frames:v", "1",
        str(out_path),
    ]
    if dry_run:
        print(f"[DRY-RUN] Would execute: {' '.join(cmd)}")
        return True

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and out_path.exists()


def list_queue() -> None:
    """Print the complete preconfigured visual review queue."""
    print("=" * 100)
    print("R04 VISUAL LANDMARK REVIEW QUEUE (12 EVENTS)")
    print("=" * 100)
    print(f"{'Pri':<4} {'Event Key':<26} {'Offset (s)':<12} {'Front t (s)':<12} {'Back t (s)':<12} {'Taxonomy':<24}")
    print("-" * 100)
    for key, item in sorted(REVIEW_QUEUE.items(), key=lambda x: x[1]["priority"]):
        print(
            f"{item['priority']:<4} {key:<26} {item['candidate_offset_s']:<+12.4f} "
            f"{item['front_t_s']:<12.3f} {item['back_t_s']:<12.3f} {item['taxonomy']:<24}"
        )
    print("=" * 100)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract candidate sync frame pairs for human visual-landmark review."
    )
    parser.add_argument("--list-queue", action="store_true", help="Print preconfigured review queue and exit")
    parser.add_argument("--event", type=str, help="Queue event key (e.g. train_events/event_010)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate extraction without opening video files")
    # Manual overrides / arbitrary inputs
    parser.add_argument("cohort", nargs="?", help="e.g. train_events")
    parser.add_argument("event_id", nargs="?", help="e.g. event_010")
    parser.add_argument("front_t_s", nargs="?", type=float, help="Front-camera local timestamp")
    parser.add_argument("offset_s", nargs="?", type=float, help="Candidate offset_s (t_front = t_back + offset_s)")

    args = parser.parse_args()

    if args.list_queue:
        list_queue()
        return

    # Determine execution parameters
    if args.event:
        if args.event not in REVIEW_QUEUE:
            print(f"Error: Unknown queue event '{args.event}'. Use --list-queue to view available events.", file=sys.stderr)
            sys.exit(1)
        q_item = REVIEW_QUEUE[args.event]
        cohort = q_item["cohort"]
        event_id = q_item["event_id"]
        candidate_offset_s = float(q_item["candidate_offset_s"])
        front_t_s = float(q_item["front_t_s"])
        expected_landmark = q_item["expected_landmark"]
        tolerance_s = float(q_item.get("tolerance_s", 0.10))
    elif args.cohort and args.event_id and args.front_t_s is not None and args.offset_s is not None:
        cohort = args.cohort
        event_id = args.event_id
        front_t_s = float(args.front_t_s)
        candidate_offset_s = float(args.offset_s)
        expected_landmark = "Manual frame extraction"
        tolerance_s = 0.10
    else:
        parser.print_help()
        print("\nError: Must specify either --event <key> or all positional arguments (cohort, event_id, front_t_s, offset_s).", file=sys.stderr)
        sys.exit(1)

    if not args.dry_run:
        check_media_access_authorization(REPO_ROOT)

    event_dir = LAYER_B_ROOT / cohort / event_id
    front_video = event_dir / "camera_front.mov"
    back_video = event_dir / "camera_back.mov"
    back_t_s = front_t_s - candidate_offset_s

    out_dir = OUT_ROOT / cohort / event_id
    front_out = out_dir / f"front_t{front_t_s:.3f}.jpg"
    back_out = out_dir / f"back_t{back_t_s:.3f}_candidate.jpg"
    manifest_path = out_dir / "review_record.json"

    print(f"Processing {cohort}/{event_id} (offset={candidate_offset_s:+.4f}s):")
    print(f"  Front Frame: t={front_t_s:.3f}s -> {front_out}")
    print(f"  Back Frame:  t={back_t_s:.3f}s -> {back_out}")
    print(f"  Expected Landmark: {expected_landmark}")

    front_ok = extract_frame(front_video, front_t_s, front_out, dry_run=args.dry_run)
    back_ok = extract_frame(back_video, back_t_s, back_out, dry_run=args.dry_run)

    front_hash = compute_sha256(front_out) if (front_ok and not args.dry_run and front_out.exists()) else None
    back_hash = compute_sha256(back_out) if (back_ok and not args.dry_run and back_out.exists()) else None

    record = {
        "schema_version": "1.0.0",
        "cohort": cohort,
        "event_id": event_id,
        "front_t_s": front_t_s,
        "candidate_offset_s": candidate_offset_s,
        "back_t_s_under_candidate_offset": back_t_s,
        "tolerance_s": tolerance_s,
        "expected_landmark": expected_landmark,
        "front_frame": str(front_out.relative_to(REPO_ROOT)),
        "back_frame": str(back_out.relative_to(REPO_ROOT)),
        "front_frame_sha256": front_hash,
        "back_frame_sha256": back_hash,
        "extraction_succeeded": front_ok and back_ok,
        "human_verified": None,
        "reviewer": None,
        "evidence_provenance": str(manifest_path.relative_to(REPO_ROOT)),
        "notes": None,
    }

    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"\nWrote {manifest_path}.\nNOTE: human_verified is null -- MUST be verified and signed by a human reviewer.")
    else:
        print("\n[DRY-RUN] Template record that would be generated:")
        print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
