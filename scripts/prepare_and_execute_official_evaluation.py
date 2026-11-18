#!/usr/bin/env python3
"""Preflight validator and fail-closed post-approval execution procedure (Tasks 2 & 6).

In default ``--mode preflight-check``, inspects all 11 approval-package files,
schemas, live hashes, and current readiness blockers without modifying or
bypassing any governance or raw-media gate.

In ``--mode execute-after-approval``, strictly refuses unless genuine human
approvals exist on disk under ``data/governance/``, ``data/ground_truth/reviews/``,
``data/splits/``, and ``data/manifests/``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from railway_detection.evaluation.official_handoff import (  # noqa: E402
    OfficialHandoffError,
    run_post_approval_official_evaluation,
    run_post_approval_option_a_descriptive_evaluation,
    validate_approval_package_bundle,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--mode",
        choices=("preflight-check", "execute-option-a-descriptive", "execute-after-approval"),
        default="preflight-check",
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--package-dir", type=Path, default=Path("docs/generated/approval_packages"))
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument(
        "--input-manifest",
        type=Path,
        default=Path("data/manifests/phase12_evaluation_inputs.json"),
    )
    parser.add_argument(
        "--descriptive-manifest",
        type=Path,
        default=Path("docs/generated/professor_evidence/mission43/B2_EVALUATION_INPUT_MANIFEST.json"),
    )
    parser.add_argument("--condition", type=str, default="B2")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    try:
        preflight = validate_approval_package_bundle(root, args.package_dir)
    except OfficialHandoffError as exc:
        print(json.dumps({"status": "PREFLIGHT_INVALID", "code": exc.code, "detail": exc.detail}, indent=2))
        return 2

    if args.mode == "preflight-check":
        print(json.dumps(preflight, indent=2))
        return 0

    if args.output_dir is None:
        print(
            json.dumps(
                {
                    "status": "USAGE_ERROR",
                    "code": "OUTPUT_DIR_REQUIRED",
                    "detail": "--output-dir (new/empty directory outside data/configs/results/docs) is required",
                },
                indent=2,
            )
        )
        return 2

    try:
        if args.mode == "execute-option-a-descriptive":
            receipt = run_post_approval_option_a_descriptive_evaluation(
                root,
                output_dir=args.output_dir,
                manifest_path=args.descriptive_manifest,
                condition=args.condition,
            )
        else:
            receipt = run_post_approval_official_evaluation(
                root,
                output_dir=args.output_dir,
                input_manifest_path=args.input_manifest,
                seed=args.seed,
            )
    except OfficialHandoffError as exc:
        print(
            json.dumps(
                {"status": "BLOCKED", "code": exc.code, "detail": exc.detail},
                indent=2,
            )
        )
        return 3

    print(json.dumps({"status": "COMPLETED", **receipt}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
