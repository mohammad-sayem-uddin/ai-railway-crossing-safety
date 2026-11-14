#!/usr/bin/env python3
"""Verify bit-for-bit reproducibility of the complete exploratory pipeline.

Re-executes all five exploratory replay and analysis scripts into a fresh
temporary directory, verifies that every generated trace, stress, CSV, and JSON
output matches the baseline `results/exploratory_execution/` directory byte-for-byte
via UTF-8 SHA-256 comparison, cleans up the temporary directory, and writes
`analysis/reproducibility_verification.json`.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SCRIPTS_DIR = REPO_ROOT / "scripts"
for p in (str(SRC_DIR), str(SCRIPTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import compute_ablation_matrix  # noqa: E402
import compute_safety_metrics  # noqa: E402
import evaluate_departure_reopening  # noqa: E402
import run_exploratory_replay  # noqa: E402
import run_failure_injection_replays  # noqa: E402
from exploratory_common import EXPLORATORY_LABEL, write_verified_json  # noqa: E402

SELF_RECEIPT_RELPATH = "analysis/reproducibility_verification.json"


def _sha256_utf8_text_file(path: Path) -> str:
    """Compute SHA-256 of a generated JSON/CSV text file using UTF-8 text mode."""
    with open(path, "r", encoding="utf-8", newline="") as f:
        return hashlib.sha256(f.read().encode("utf-8")).hexdigest()


def _collect_text_hashes(root: Path) -> dict[str, str]:
    """Collect relative path -> SHA-256 for all JSON/CSV artifacts under `root`."""
    hashes: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if rel == SELF_RECEIPT_RELPATH:
            continue
        if p.suffix.lower() not in {".json", ".csv"}:
            continue
        hashes[rel] = _sha256_utf8_text_file(p)
    return hashes


def verify_exploratory_reproducibility(
    *,
    baseline_dir: Path,
    keep_temp: bool = False,
) -> dict[str, Any]:
    """Run full exploratory pipeline in a temporary directory and verify SHA-256 equality."""
    if not baseline_dir.is_dir():
        raise FileNotFoundError(f"Baseline directory does not exist: {baseline_dir}")

    baseline_hashes = _collect_text_hashes(baseline_dir)
    if not baseline_hashes:
        raise RuntimeError(f"No JSON/CSV baseline outputs found in {baseline_dir}")

    started = time.perf_counter()
    tmp_dir = Path(tempfile.mkdtemp(prefix="exploratory_repro_"))
    step_results: list[dict[str, Any]] = []
    try:
        stages = [
            ("run_exploratory_replay", run_exploratory_replay.main),
            ("run_failure_injection_replays", run_failure_injection_replays.main),
            ("evaluate_departure_reopening", evaluate_departure_reopening.main),
            ("compute_safety_metrics", compute_safety_metrics.main),
            ("compute_ablation_matrix", compute_ablation_matrix.main),
        ]
        for stage_name, fn in stages:
            t0 = time.perf_counter()
            rc = fn(["--output-dir", str(tmp_dir)])
            dt = round(time.perf_counter() - t0, 4)
            step_results.append({"stage": stage_name, "exit_code": rc, "elapsed_s": dt})
            if rc != 0:
                raise RuntimeError(f"Stage {stage_name} failed with exit code {rc}")

        repro_hashes = _collect_text_hashes(tmp_dir)
        baseline_keys = set(baseline_hashes.keys())
        repro_keys = set(repro_hashes.keys())

        missing_in_repro = sorted(baseline_keys - repro_keys)
        extra_in_repro = sorted(repro_keys - baseline_keys)
        mismatches = [
            {
                "relpath": rel,
                "baseline_sha256": baseline_hashes[rel],
                "repro_sha256": repro_hashes[rel],
            }
            for rel in sorted(baseline_keys & repro_keys)
            if baseline_hashes[rel] != repro_hashes[rel]
        ]
    finally:
        if not keep_temp and tmp_dir.exists():
            shutil.rmtree(tmp_dir)

    verified_identical = (
        not missing_in_repro and not extra_in_repro and not mismatches and len(repro_hashes) > 0
    )
    key_outputs = {
        rel: baseline_hashes[rel]
        for rel in sorted(baseline_hashes)
        if not rel.startswith("replays/traces/")
    }
    trace_count = sum(1 for rel in baseline_hashes if rel.startswith("replays/traces/"))

    receipt = {
        "exploratory_label": EXPLORATORY_LABEL,
        "schema": "exploratory-reproducibility-verification/1",
        "verified_bit_identical": verified_identical,
        "total_files_compared": len(baseline_hashes),
        "trace_files_compared": trace_count,
        "summary_and_analysis_files_compared": len(key_outputs),
        "missing_in_repro": missing_in_repro,
        "extra_in_repro": extra_in_repro,
        "mismatches": mismatches,
        "stage_exit_codes": [{k: v for k, v in s.items() if k != "elapsed_s"} for s in step_results],
        "key_output_sha256": key_outputs,
    }
    receipt_sha = write_verified_json(baseline_dir / SELF_RECEIPT_RELPATH, receipt)
    total_wall_s = round(time.perf_counter() - started, 3)

    if not verified_identical:
        raise RuntimeError(
            f"Reproducibility check FAILED: missing={len(missing_in_repro)}, "
            f"extra={len(extra_in_repro)}, mismatches={len(mismatches)}"
        )

    return {
        "verified_bit_identical": verified_identical,
        "total_files_compared": len(baseline_hashes),
        "trace_files_compared": trace_count,
        "summary_and_analysis_files_compared": len(key_outputs),
        "wall_s": total_wall_s,
        "receipt_sha256": receipt_sha,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify bit-for-bit reproducibility of exploratory outputs.")
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        default=REPO_ROOT / "results" / "exploratory_execution",
        help="Baseline exploratory output directory to verify against.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Preserve the temporary directory instead of deleting it.",
    )
    args = parser.parse_args(argv)
    res = verify_exploratory_reproducibility(baseline_dir=args.baseline_dir, keep_temp=args.keep_temp)
    print(
        f"[VERIFIED] bit_identical={res['verified_bit_identical']} "
        f"files={res['total_files_compared']} traces={res['trace_files_compared']} "
        f"summary_files={res['summary_and_analysis_files_compared']} "
        f"wall_s={res['wall_s']} receipt_sha256={res['receipt_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
