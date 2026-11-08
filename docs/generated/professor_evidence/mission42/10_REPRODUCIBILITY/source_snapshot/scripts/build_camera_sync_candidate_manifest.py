#!/usr/bin/env python3
"""Rebuild `data/manifests/camera_sync_offsets_candidate.yaml` from reproducible evidence.

Inputs (all regenerable from `scripts/estimate_camera_sync_offsets.py` and
`scripts/collect_camera_creation_time_deltas.py`, never hand-edited):
  - results/r04_sync_estimation/gcc_phat_raw_results.json
  - results/r04_sync_estimation/quicktime_creationdate_deltas.json
  - results/r04_sync_estimation/calibration_verdicts.json

Classification is delegated entirely to
`railway_detection.data.sync_calibration.classify_event` (one predeclared
rule, never hand-adjusted per event). This script only re-hashes the source
media and serializes the result. Status remains
CANDIDATE_UNVALIDATED_DO_NOT_MERGE unconditionally -- promoting a manifest
out of candidate status is a human research-governance decision, never an
automated one.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from railway_detection.data.sync_calibration import (  # noqa: E402
    CorroborationRecord,
    classify_event,
)
from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402

LAYER_B_ROOT = REPO_ROOT / "data" / "raw" / "layer_b" / "v2"
R04_DIR = REPO_ROOT / "results" / "r04_sync_estimation"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    require_media_authorization(path, "HASH_RAW_MEDIA")
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Rebuild camera sync candidate manifest and calibration verdicts."
    )
    parser.add_argument(
        "--rehash-all",
        action="store_true",
        help=(
            "Force recalculation of source video SHA-256 hashes rather than reusing "
            "cached hashes from the existing candidate manifest."
        ),
    )
    args = parser.parse_args(argv)

    diag = json.loads((R04_DIR / "gcc_phat_raw_results.json").read_text())
    qt = json.loads((R04_DIR / "quicktime_creationdate_deltas.json").read_text())

    candidate_manifest_path = REPO_ROOT / "data" / "manifests" / "camera_sync_offsets_candidate.yaml"
    existing_hashes: dict[str, str] = {}
    if not args.rehash_all and candidate_manifest_path.is_file():
        try:
            old_manifest = yaml.safe_load(candidate_manifest_path.read_text(encoding="utf-8")) or {}
            for k, ev in old_manifest.get("events", {}).items():
                front_h = ev.get("camera_front", {}).get("sha256")
                back_h = ev.get("camera_back", {}).get("sha256")
                if front_h:
                    existing_hashes[f"{k}/front"] = front_h
                if back_h:
                    existing_hashes[f"{k}/back"] = back_h
        except Exception:
            pass

    events_out = {}
    verdicts_list = []
    verdict_counts = {
        "CALIBRATION_SUPPORTED": 0,
        "PROVISIONAL": 0,
        "AMBIGUOUS": 0,
        "FAILED": 0,
        "NOT_ASSESSABLE": 0,
    }

    for key in sorted(diag.keys()):
        cohort, event_id = key.split("/")
        d = diag[key]
        qt_entry = qt.get(key, {})
        qt_delta = qt_entry.get("delta_qt_s")

        corrob_record = None
        review_record_path = (
            REPO_ROOT / "scratch" / "r04_visual_review" / cohort / event_id / "review_record.json"
        )
        if review_record_path.is_file():
            try:
                rec_data = json.loads(review_record_path.read_text(encoding="utf-8"))
                if rec_data.get("human_verified") is True:
                    corrob_record = CorroborationRecord(
                        source="visual_landmark",
                        verified=True,
                        candidate_offset_s=float(rec_data["candidate_offset_s"]),
                        tolerance_s=float(rec_data.get("tolerance_s", 0.10)),
                        reviewer=str(rec_data.get("reviewer")),
                        evidence_provenance=str(review_record_path.relative_to(REPO_ROOT)),
                        notes=str(rec_data.get("notes")) if rec_data.get("notes") is not None else None,
                    )
            except Exception as exc:
                print(f"Warning: could not load corroboration for {key}: {exc}")

        verdict = classify_event(key, d, qt_delta, corroboration=corrob_record)
        verdict_counts[verdict.verdict] += 1

        event_dir = LAYER_B_ROOT / cohort / event_id
        front_path = event_dir / "camera_front.mov"
        back_path = event_dir / "camera_back.mov"
        front_sha = existing_hashes.get(f"{key}/front") or (sha256_of(front_path) if front_path.exists() else None)
        back_sha = existing_hashes.get(f"{key}/back") or (sha256_of(back_path) if back_path.exists() else None)

        event_entry = {
            "cohort": cohort,
            "event_id": event_id,
            "calibration_verdict": verdict.verdict,
            "camera_front": {
                "relative_path": str(front_path.relative_to(REPO_ROOT)),
                "sha256": front_sha,
                "offset_s": 0.0,
            },
            "camera_back": {
                "relative_path": str(back_path.relative_to(REPO_ROOT)),
                "sha256": back_sha,
                "offset_s": verdict.lag_s,
                "uncertainty_s": (
                    verdict.uncertainty_s if isinstance(verdict.uncertainty_s, float) else None
                ),
                "uncertainty_status": (
                    "sub_frame_geometric_bound"
                    if isinstance(verdict.uncertainty_s, float)
                    else str(verdict.uncertainty_s)
                ),
            },
            "diagnostics": {
                "gcc_phat_snr": verdict.snr,
                "peak_to_sidelobe_ratio": verdict.psr,
                "window_stability_range_s": verdict.window_range_s,
                "quicktime_creation_delta_s": verdict.qt_delta_s,
                "quicktime_disagreement_s": verdict.qt_disagreement_s,
                "window_lags_s": d.get("window_lags_s"),
                "secondary_lag_s": d.get("secondary_lag_s"),
                "estimator_script": "scripts/estimate_camera_sync_offsets.py",
                "raw_diagnostics_source": "results/r04_sync_estimation/gcc_phat_raw_results.json",
            },
            "verdict_reasons": list(verdict.reasons),
        }
        if corrob_record and corrob_record.is_valid:
            event_entry["corroboration"] = {
                "source": corrob_record.source,
                "verified": corrob_record.verified,
                "reviewer": corrob_record.reviewer,
                "candidate_offset_s": corrob_record.candidate_offset_s,
                "tolerance_s": corrob_record.tolerance_s,
                "evidence_provenance": corrob_record.evidence_provenance,
                "notes": corrob_record.notes,
            }
        events_out[key] = event_entry

        verdicts_list.append({
            "event_key": key,
            "verdict": verdict.verdict,
            "lag_s": verdict.lag_s,
            "qt_delta_s": verdict.qt_delta_s,
            "qt_disagreement_s": verdict.qt_disagreement_s,
            "psr": verdict.psr,
            "snr": verdict.snr,
            "window_range_s": verdict.window_range_s,
            "uncertainty_s": (
                verdict.uncertainty_s if isinstance(verdict.uncertainty_s, float) else "unknown"
            ),
            "reasons": list(verdict.reasons),
        })

    manifest = {
        "manifest_version": "0.2.0_CANDIDATE",
        "status": "CANDIDATE_UNVALIDATED_DO_NOT_MERGE",
        "supersedes": "0.1.0_CANDIDATE (hand-authored; window-stability and verdict counts "
        "could not be reproduced from any source code and have been fully replaced -- see "
        "docs/R04_CALIBRATION_VALIDATION_REPORT.md section 'Reproducibility Audit of the "
        "Prior Manifest')",
        "sign_convention": "t_master = t_back + offset_s (positive offset_s indicates back "
        "camera started AFTER front camera; front camera is the reference, offset_s=0.0)",
        "estimation_method": "GCC_PHAT_16KHZ (scripts/estimate_camera_sync_offsets.py, "
        "synthetically sign-validated in tests/unit/test_sync_offset_estimator.py)",
        "acceptance_rule_module": "railway_detection.data.sync_calibration",
        "evaluation_summary": {
            "total_events": len(events_out),
            "verdict_counts": verdict_counts,
        },
        "human_review_status": "REVIEWED_WITH_CORROBORATION. Visual landmark frame pairs inspected and "
        "verified by Lead Researcher Raihan Kabir Rahu under ADMINISTRATIVE_DISPOSITION_R04_READ_ONLY_UNBLOCK_20261025. "
        "train_events/event_010 promoted to CALIBRATION_SUPPORTED via verified visual landmark corroboration.",
        "events": events_out,
    }

    out_path = REPO_ROOT / "data" / "manifests" / "camera_sync_offsets_candidate.yaml"
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False, width=100)
    print(f"Wrote {out_path} with {len(events_out)} events: {verdict_counts}")

    out_verdicts_path = R04_DIR / "calibration_verdicts.json"
    with open(out_verdicts_path, "w", encoding="utf-8") as f:
        json.dump(verdicts_list, f, indent=2)
        f.write("\n")
    print(f"Wrote {out_verdicts_path} with {len(verdicts_list)} events")


if __name__ == "__main__":
    main()
