#!/usr/bin/env python3
"""Audit the 27-event Layer-B dataset split problem and generate a collection plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from railway_detection.data.split_audit import run_split_audit  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results/dataset_audit/layer_b_split_audit_and_collection_plan.json",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.output if args.output.is_absolute() else (root / args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    report = run_split_audit(root)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary = {
        "output": str(out.relative_to(root)) if root in out.parents else str(out),
        "can_27_events_produce_leakage_safe_3way_split": report[
            "can_27_events_produce_leakage_safe_3way_split"
        ],
        "prior_16_6_5_leakage_safe": report["candidate_splits_evaluated"][
            "prior_hash_candidate_16_6_5"
        ]["leakage_safe"],
        "chrono_15_5_7_leakage_safe": report["candidate_splits_evaluated"][
            "chrono_temporal_block_15_5_7"
        ]["leakage_safe"],
        "proposal_metadata_inconsistencies_count": report[
            "proposal_metadata_inconsistencies_count"
        ],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
