#!/usr/bin/env python
"""Interactive Stage-2.1 review driver (Mission 3, 2026-11-09).

Walks ONE authorized reviewer through ONE event: they watch the raw
front/back videos themselves, mark the six canonical boundaries from their
own observation, and this script assembles a schema-valid Stage-2.1 record
via review_session.build_review_record (live media hashing, allowlist
check, full schema validation) and writes it to data/ground_truth/reviews/.

The script never shows model predictions or proposal values before the
reviewer records their own boundaries. It never promotes records.

Usage (from the repository root):
  PYTHONPATH=src:. .venv/bin/python scripts/run_stage21_review.py \
      --reviewer raihankabirrahu@gmail.com --cohort train_events --event event_001
  # independent second review of an existing primary record:
  ... --reviewer elaf85777@gmail.com --second-of review_event_001_v1_20261109
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from railway_detection.annotation.promotion_gate import load_authorized_reviewers
from railway_detection.annotation.review_session import build_review_record
from railway_detection.annotation.stage2_1_schema import (
    CANONICAL_TIMESTAMPS,
    build_stage2_1_record_from_dict,
)

BOUNDARY_HELP = {
    "T0_first_visible": "first moment any part of the train becomes visible",
    "T1_danger_zone_entry": "train enters the danger zone on approach",
    "T2_crossing_occupancy_start": "train starts occupying the crossing itself",
    "T3_locomotive_unit_clearance": "locomotive (front unit) has cleared the crossing",
    "T4_tail_clearance": "tail / last car has cleared the crossing",
    "T_scene_clear": "scene fully clear, normal road use resumed",
}
STOCK_ATTESTATION = (
    "I reviewed only the raw video/audio and did not consult any model prediction."
)


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def ask(prompt: str) -> str:
    return input(prompt).strip()


def resolve_active_proposal(cohort: str, event: str) -> tuple[str, str]:
    pdir = ROOT / "data/ground_truth/proposals" / cohort
    files = sorted(pdir.glob(f"{event}_proposal_v*.json"))
    if not files:
        raise SystemExit(f"No proposal found for {cohort}/{event} in {pdir}")

    def ver(p: Path) -> int:
        return int(p.stem.rsplit("_v", 1)[1])

    active = max(files, key=ver)
    sha = hashlib.sha256(active.read_bytes()).hexdigest()
    return f"data/ground_truth/proposals/{cohort}/{active.name}", sha


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reviewer", required=True)
    ap.add_argument("--cohort", required=True,
                    choices=["train_events", "no_train_events", "engine_events"])
    ap.add_argument("--event", required=True, help="e.g. event_001")
    ap.add_argument("--second-of", default=None,
                    help="review_id of the primary record (second review)")
    args = ap.parse_args()

    allow = load_authorized_reviewers(
        ROOT / "data/ground_truth/authorized_reviewers.json")
    if args.reviewer not in allow:
        raise SystemExit(
            f"REVIEWER_NOT_AUTHORIZED: {args.reviewer} is not on the allowlist "
            f"{sorted(allow)}. No session started.")

    media_dir = ROOT / "data/raw/layer_b/v2" / args.cohort / args.event
    front = media_dir / "camera_front.mov"
    back = media_dir / "camera_back.mov"
    for p in (front, back):
        if not p.exists():
            raise SystemExit(f"Media file missing: {p}")
    proposal_file, proposal_sha = resolve_active_proposal(args.cohort, args.event)

    print("=" * 70)
    print(f"STAGE-2.1 REVIEW — {args.cohort}/{args.event}")
    print(f"Reviewer: {args.reviewer}" + (" (SECOND review)" if args.second_of else ""))
    print(f"Bound proposal: {proposal_file}")
    print("\nOpen BOTH videos now and watch them fully, on your own:")
    print(f"  FRONT: {front}")
    print(f"  BACK:  {back}")
    print("\nDo not consult model outputs or the AI proposal values.")
    ask("Press Enter when you START watching (the review clock starts now)...")
    start = now_iso()

    boundaries: dict[str, dict] = {}
    print("\nFor each boundary: O = observable, N = not applicable, "
          "C = censored (recording ends first), U = uncertain")
    for b in CANONICAL_TIMESTAMPS:
        print(f"\n--- {b}: {BOUNDARY_HELP[b]} ---")
        while True:
            state = ask("State [O/N/C/U]: ").upper()
            if state in ("O", "N", "C", "U"):
                break
            print("Please enter O, N, C or U.")
        if state == "O":
            while True:
                try:
                    value = float(ask("Seconds into the video (e.g. 12.4): "))
                    if value >= 0:
                        break
                except ValueError:
                    pass
                print("Enter a non-negative number.")
            cam = ""
            while cam not in ("front", "back"):
                cam = ask("Reference camera [front/back]: ").lower()
            entry = {"state": "OBSERVABLE", "value_s": value,
                     "reference_camera": cam}
            why = ask("Rationale (optional, Enter to skip): ")
            if why:
                entry["rationale"] = why
        else:
            full = {"N": "UNOBSERVABLE_NOT_APPLICABLE",
                    "C": "CENSORED", "U": "UNCERTAIN"}[state]
            why = ""
            while not why:
                why = ask(f"Rationale for {full} (required): ")
            entry = {"state": full, "rationale": why}
        boundaries[b] = entry

    print("\nModel-independence attestation. Stock text:")
    print(f'  "{STOCK_ATTESTATION}"')
    att = ask("Press Enter to adopt it, or type your own statement: ") or STOCK_ATTESTATION
    tool = ask("Inspection tool [VLC media player (manual)]: ") or \
        "VLC media player (manual)"
    print("Status: A = APPROVED, S = NEEDS_SECOND_REVIEW, D = DISPUTED")
    status = {"A": "APPROVED", "S": "NEEDS_SECOND_REVIEW", "D": "DISPUTED"}.get(
        ask("Status [A]: ").upper() or "A", "APPROVED")

    end = now_iso()
    date_tag = datetime.now(UTC).strftime("%Y%m%d")
    review_id = (f"review_{args.event}_v2_{date_tag}" if args.second_of
                 else f"review_{args.event}_v1_{date_tag}")
    record = build_review_record(
        event_id=args.event,
        cohort=args.cohort,
        reviewer_id=args.reviewer,
        authorized_reviewers=allow,
        review_session_id=f"session_{args.event}_{date_tag}_{args.reviewer.split('@')[0]}",
        review_start_utc=start,
        review_end_utc=end,
        inspection_tool=tool,
        attestation_statement=att,
        attested_at_utc=end,
        front_media_path=front,
        back_media_path=back,
        observed_at_utc=start,
        proposal_file=proposal_file,
        proposal_sha256=proposal_sha,
        boundary_adjudications=boundaries,
        adjudication_status=status,
        review_id=review_id,
        second_review_of=args.second_of,
    )
    build_stage2_1_record_from_dict(record)  # re-validate before writing
    out = ROOT / "data/ground_truth/reviews" / f"{review_id}.json"
    if out.exists():
        raise SystemExit(f"Refusing to overwrite existing record: {out}")
    out.write_text(json.dumps(record, indent=2), encoding="utf-8")
    flagged = [b for b, e in boundaries.items()
               if e["state"] in ("CENSORED", "UNCERTAIN")]
    print("\n" + "=" * 70)
    print(f"RECORD WRITTEN + SCHEMA-VALID: {out.relative_to(ROOT)}")
    print(f"review_id: {review_id} | status: {status}")
    if flagged:
        print(f"Boundaries needing a second review: {flagged}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
