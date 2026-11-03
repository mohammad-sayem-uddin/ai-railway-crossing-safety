#!/usr/bin/env python3
"""Phase 11, Task 2 & 5: builds an independent, structurally-verified
event-level annotation inventory for all 27 active Layer B v2 events
(23 train, 3 no-train, 1 engine-only), cross-checking the existing
AI-generated candidate proposals' claims against independently-measured
video stream facts (duration, fps, SHA-256) -- never against any model
prediction.

This script does NOT approve, correct, or re-derive any T0-T4 timestamp
judgment itself (that requires a human watching the footage). It reports
the existing candidate proposals' claimed values, clearly labeled as
unapproved AI-generated drafts, flags the review-record integrity issue
found during this phase's audit, and performs objective, mechanical
consistency/margin checks (e.g. does a claimed T4 fall within the
independently-measured stream duration; how much stream remains after a
claimed or right-censored boundary).

Reads only; writes only new files under docs/ and data/ground_truth/ (the
inventory JSON/CSV deliverables), never touches any existing proposal,
review, or raw media file.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STRUCTURAL_INVENTORY = REPO_ROOT / "data" / "manifests" / "layer_b_v2_annotation_inventory.json"
PROPOSALS_DIR = REPO_ROOT / "data" / "ground_truth" / "proposals"
REVIEWS_DIR = REPO_ROOT / "data" / "ground_truth" / "reviews"

COHORTS = {
    "train_events": [f"event_{i:03d}" for i in range(1, 24)],
    "no_train_events": [f"event_{i:03d}" for i in range(1, 4)],
    "engine_events": ["event_001"],
}


def _latest_proposal_file(cohort: str, event_id: str) -> Path | None:
    candidates = sorted((PROPOSALS_DIR / cohort).glob(f"{event_id}_proposal*.json"))
    if not candidates:
        return None

    def _version_key(p: Path) -> int:
        name = p.stem
        if name.endswith("_proposal"):
            return 0
        suffix = name.rsplit("_v", 1)[-1]
        try:
            return int(suffix)
        except ValueError:
            return 0

    return max(candidates, key=_version_key)


def _review_file(cohort: str, event_id: str) -> Path | None:
    p = REVIEWS_DIR / cohort / f"{event_id}_review.json"
    return p if p.exists() else None


def main() -> int:
    structural = json.loads(STRUCTURAL_INVENTORY.read_text())
    inventory: dict = {}
    review_timestamps_seen: set[str] = set()
    flagged_fabricated_reviews: list[str] = []
    missing_structural: list[str] = []
    duration_mismatches: list[dict] = []

    for cohort, event_ids in COHORTS.items():
        for event_id in event_ids:
            key = f"{cohort}/{event_id}"
            struct_entry = structural.get(key)
            if struct_entry is None:
                missing_structural.append(key)
                continue

            proposal_path = _latest_proposal_file(cohort, event_id)
            proposal = json.loads(proposal_path.read_text()) if proposal_path else None
            review_path = _review_file(cohort, event_id)
            review = json.loads(review_path.read_text()) if review_path else None

            front_duration = struct_entry["front"]["meta"]["duration_s"]
            back_duration = struct_entry["back"]["meta"]["duration_s"]

            # Cross-check proposal's self-reported media duration/hash
            # against the independently-measured structural inventory.
            if proposal:
                for media in proposal["ai_assistant_metadata"]["input_media_files"]:
                    cam = "front" if "front" in media["file_name"] else "back"
                    measured = struct_entry[cam]["meta"]["duration_s"]
                    measured_hash = struct_entry[cam]["sha256"]
                    if abs(media["duration_s"] - measured) > 0.01 or media["sha256"] != measured_hash:
                        duration_mismatches.append({
                            "event": key, "camera": cam,
                            "proposal_duration_s": media["duration_s"], "measured_duration_s": measured,
                            "proposal_sha256": media["sha256"], "measured_sha256": measured_hash,
                        })

            review_status_raw = review.get("adjudication_status") if review else None
            review_timestamp = review.get("reviewer_metadata", {}).get("review_date_utc") if review else None
            if review_timestamp:
                review_timestamps_seen.add(review_timestamp)
            review_status_trusted = None
            fabrication_flag = False
            if review_status_raw == "APPROVED":
                # See Section 1 of docs/PHASE11_GROUND_TRUTH_PROTOCOL.md:
                # every one of these 27 records shares a single identical
                # review_date_utc timestamp, which is not possible for
                # genuinely independent, per-event human video review, and
                # directly violates this repository's own documented
                # anti-auto-approval mandate (FINAL_GROUND_TRUTH_PROTOCOL.md
                # Sec 1.3). Treated as INVALID regardless of its claimed
                # status; never treated as approved ground truth.
                review_status_trusted = "INVALID_FABRICATED_APPROVAL"
                fabrication_flag = True
                flagged_fabricated_reviews.append(key)
            elif review_status_raw is not None:
                review_status_trusted = f"UNRECOGNIZED_STATUS:{review_status_raw}"
            else:
                review_status_trusted = "NO_REVIEW_RECORD"

            timestamps = {}
            left_censored = False
            right_censored_fields = []
            if proposal:
                for field, data in proposal["proposed_timestamps"].items():
                    timestamps[field] = {
                        "applicable": data["applicable"],
                        "candidate_observable": data["candidate_observable"],
                        "value_s": data["value_s"],
                        "reference_camera": data["reference_camera"],
                        "ambiguity_flag": data["ambiguity_flag"],
                        "rationale": data["rationale"],
                    }
                    rationale_lower = (data["rationale"] or "").lower()
                    if field == "T0_first_visible" and data["value_s"] == 0.0 and (
                        "left-censored" in rationale_lower or "left_censored" in rationale_lower
                    ):
                        left_censored = True
                    if data["applicable"] and not data["candidate_observable"] and (
                        "ends" in rationale_lower or "right" in rationale_lower or "recording terminates" in rationale_lower
                    ):
                        right_censored_fields.append(field)

            # Margin check: for observable T4 values, how much back-camera
            # stream remains after it (objective arithmetic, not a visual
            # judgment) -- relevant to whether this event's recording
            # could even in principle support post-T4 evaluation (e.g. a
            # clearance-dwell-completion check), independent of any model.
            t4_margin_s = None
            if proposal:
                t4 = proposal["proposed_timestamps"]["T4_tail_clearance"]
                if t4["applicable"] and t4["candidate_observable"] and t4["value_s"] is not None:
                    t4_margin_s = round(back_duration - t4["value_s"], 3)

            inventory[key] = {
                "cohort": cohort,
                "event_id": event_id,
                "event_type": proposal["event_type"] if proposal else struct_entry.get("event_type"),
                "streams": {
                    "front": {"duration_s": front_duration, "sha256": struct_entry["front"]["sha256"],
                               "fps": struct_entry["front"]["meta"]["video"]["fps"]},
                    "back": {"duration_s": back_duration, "sha256": struct_entry["back"]["sha256"],
                              "fps": struct_entry["back"]["meta"]["video"]["fps"]},
                },
                "recording_window": {"front": [0.0, front_duration], "back": [0.0, back_duration],
                                       "note": "Media-local clocks; R04 cross-camera offset unresolved except for "
                                               "the 11 events validated in configs/exploratory_dual_camera_v1.1.0_authorized_20261013.yaml."},
                "candidate_proposal": {
                    "file": str(proposal_path.relative_to(REPO_ROOT)) if proposal_path else None,
                    "version": proposal["proposal_id"].rsplit("_v", 1)[-1] if proposal else None,
                    "status": "UNAPPROVED_AI_GENERATED_DRAFT",
                    "model_name": proposal["ai_assistant_metadata"]["model_name"] if proposal else None,
                },
                "review_record": {
                    "file": str(review_path.relative_to(REPO_ROOT)) if review_path else None,
                    "claimed_status": review_status_raw,
                    "trusted_status": review_status_trusted,
                    "fabrication_flag": fabrication_flag,
                    "review_date_utc_claimed": review_timestamp,
                },
                "left_censored": left_censored,
                "right_censored_fields": right_censored_fields,
                "t4_margin_s_after_claimed_value": t4_margin_s,
                "timestamps": timestamps,
            }

    out = {
        "generated_by": "scripts/run_phase11_annotation_inventory.py",
        "purpose": "Independent, structurally-verified event-level annotation inventory (Phase 11, Tasks 2 & 5). "
        "Candidate proposal T0-T4/T_scene_clear values are AI-generated drafts, NOT approved ground truth. "
        "All 27 existing review records claiming APPROVED status are INVALID (see fabrication_flag) and require "
        "genuine human re-review before any use as ground truth.",
        "total_events": len(inventory),
        "integrity_findings": {
            "distinct_review_timestamps_across_all_27_records": sorted(review_timestamps_seen),
            "events_with_fabricated_approval": flagged_fabricated_reviews,
            "proposal_vs_measured_media_mismatches": duration_mismatches,
            "events_missing_from_structural_inventory": missing_structural,
        },
        "events": inventory,
    }

    out_json = REPO_ROOT / "docs" / "PHASE11_EVENT_INVENTORY.json"
    out_json.write_text(json.dumps(out, indent=2), encoding="utf-8")

    out_csv = REPO_ROOT / "docs" / "PHASE11_EVENT_INVENTORY.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "cohort", "event_id", "front_duration_s", "back_duration_s", "left_censored",
            "right_censored_fields", "t0_s", "t1_s", "t2_s", "t3_s", "t4_s", "t4_margin_s",
            "t_scene_clear_s", "review_trusted_status", "fabrication_flag",
        ])
        for key, e in inventory.items():
            ts = e["timestamps"]
            def v(field):
                return ts.get(field, {}).get("value_s") if ts else None
            writer.writerow([
                e["cohort"], e["event_id"], e["streams"]["front"]["duration_s"], e["streams"]["back"]["duration_s"],
                e["left_censored"], ";".join(e["right_censored_fields"]),
                v("T0_first_visible"), v("T1_danger_zone_entry"), v("T2_crossing_occupancy_start"),
                v("T3_locomotive_unit_clearance"), v("T4_tail_clearance"), e["t4_margin_s_after_claimed_value"],
                v("T_scene_clear"), e["review_record"]["trusted_status"], e["review_record"]["fabrication_flag"],
            ])

    print(f"Wrote {out_json} ({len(inventory)} events)")
    print(f"Wrote {out_csv}")
    print(f"\nIntegrity findings:")
    print(f"  Distinct review timestamps across all 27 'APPROVED' records: {sorted(review_timestamps_seen)}")
    print(f"  Events with fabricated approval: {len(flagged_fabricated_reviews)}/27")
    print(f"  Proposal-vs-measured media mismatches: {len(duration_mismatches)}")
    print(f"  Events missing from structural inventory: {missing_structural}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
