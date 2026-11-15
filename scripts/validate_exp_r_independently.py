#!/usr/bin/env python3
"""Independently verify Exp R from non-raw cached data and audit methodological risks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from railway_detection.experiments.exp_r_validation import validate_exp_r_independently


def main() -> int:
    parser = argparse.ArgumentParser(description="Independent validation & sensitivity audit for Exp R")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/exploratory_v2/optimization_and_stress/exp_r_independent_validation.json"),
    )
    args = parser.parse_args()
    root = args.root.resolve()
    report = validate_exp_r_independently(root)
    out_path = args.output if args.output.is_absolute() else (root / args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(out_path.relative_to(root)),
                "corpus_verification": report["corpus_verification"],
                "published_artifact_reproduction": report["published_artifact_reproduction"],
                "methodological_audit_findings": report["methodological_audit_findings"],
                "reproduced_oof_f1": report["reproduced_published_loeo"]["oof_metrics"]["f1"],
                "strict_train_only_oof_f1": report["sensitivity_1_strict_train_only_selection"]["oof_metrics"]["f1"],
                "uncapped_temp_cal_brier": report["sensitivity_2_uncapped_temp_grid_to_15"]["calibration"]["oof_cal_brier"],
                "uncapped_temp_cal_ece_5bin": report["sensitivity_2_uncapped_temp_grid_to_15"]["calibration"]["oof_cal_ece_5bin"],
                "uncapped_temp_max_selected": report["sensitivity_2_uncapped_temp_grid_to_15"]["calibration"]["max_selected_temp"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
