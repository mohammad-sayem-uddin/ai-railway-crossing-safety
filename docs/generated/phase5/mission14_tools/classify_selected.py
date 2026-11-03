#!/usr/bin/env python3
"""Mission 14 (WP14.7): incremental test-classification update for an explicit file list.

* ``--dynamic`` files are classified exactly the way ``scripts/classify_test_access.py`` classifies
  every file: run alone, in its own interpreter, under the read-blocking access guard (a protected
  read is *raised before it happens* and recorded).  Only files judged safe by prior static review
  are passed here.
* ``--static`` entries are recorded WITHOUT executing the file.  They are used for the two original
  Mission 12 test files that call the readiness gate on the real repository.

Nothing else in the manifest is touched.  Usage (from the repository root, repo venv):

    .venv/bin/python docs/generated/phase5/mission14_tools/classify_selected.py \
        --work-dir <outside-repo-dir> --dynamic tests/unit/test_x.py ... --static
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location(
    "classify_test_access", REPO_ROOT / "scripts/classify_test_access.py"
)
classifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(classifier)
am = classifier.am

STATIC_REASONS = {
    "tests/unit/test_phase12_governance.py": (
        "Static review by Mission 14 (file NOT executed): three tests (the real-repository "
        "readiness assessment, the blocker-diagnostics test and the real-repository blocker-class "
        "test) call assess_official_phase12_readiness(REPO_ROOT), which reaches "
        "execution_gate.verify_checkpoint_integrity and opens and hashes the vision, audio-v3 and "
        "prohibited audio-v2 checkpoints and reads review records. All other tests use the "
        "synthetic workspace fixture and are mirrored in test_phase12_governance_synthetic.py. "
        "Dynamic fields below are retained from the earlier guarded run (before Mission 12 edits)."
    ),
    "tests/unit/test_phase12_official_replay.py": (
        "Static review by Mission 14 (file NOT executed): test_real_repository_run_is_blocked_and_"
        "leaves_everything_untouched runs the official path on the real repository via cli_main and"
        " "
        "run_official_safe(repository_root=REPO_ROOT), reaching the readiness gate's checkpoint "
        "integrity check, reading results/experiment_registry.jsonl and every review record; the "
        "module also loads the real frozen configuration at import. All other tests use the "
        "synthetic workspace and are mirrored in test_phase12_official_replay_synthetic.py. "
        "Dynamic fields below are retained from the earlier guarded run (before Mission 12 edits)."
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--dynamic", nargs="*", default=[])
    parser.add_argument("--static", action="store_true")
    parser.add_argument("--manifest", type=Path, default=REPO_ROOT / am.MANIFEST_RELATIVE)
    args = parser.parse_args()
    work = args.work_dir.resolve()
    if work == REPO_ROOT or REPO_ROOT in work.parents:
        print("error: --work-dir must be outside the repository", file=sys.stderr)
        return 2
    work.mkdir(parents=True, exist_ok=True)
    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    entries = manifest["test_files"]
    for rel in args.dynamic:
        if rel in STATIC_REASONS:
            print(f"refusing to execute protected-classified {rel}", file=sys.stderr)
            return 2
        print(f"[dynamic] {rel}", flush=True)
        entries[rel] = classifier.classify(rel, classifier.run_one(rel, work))
        print(
            "   ->",
            entries[rel]["category"],
            entries[rel]["tests"],
            entries[rel]["blocked_attempts"],
        )
    if args.static:
        for rel, reason in STATIC_REASONS.items():
            previous = entries[rel]
            entries[rel] = {
                **previous,
                "sha256": am.sha256_of(REPO_ROOT / rel),
                "category": am.MODEL_CHECKPOINT_ACCESS,
                "safe_for_synthetic_runner": False,
                "reason": reason,
                "evidence": "static_review_mission14_not_executed",
            }
            print(f"[static] {rel} -> {am.MODEL_CHECKPOINT_ACCESS}")
    counts = Counter(e["category"] for e in entries.values())
    manifest["test_files"] = dict(sorted(entries.items()))
    manifest["summary"] = {
        "total_test_files": len(entries),
        **{c.lower(): counts.get(c, 0) for c in am.CATEGORIES},
        "safe_for_synthetic_runner": sum(e["safe_for_synthetic_runner"] for e in entries.values()),
    }
    amendments = manifest.setdefault("amendments", [])
    amendments.append(
        {
            "mission": 14,
            "tool": "docs/generated/phase5/mission14_tools/classify_selected.py",
            "dynamic_files": sorted(args.dynamic),
            "static_files": sorted(STATIC_REASONS) if args.static else [],
        }
    )
    args.manifest.write_text(
        yaml.safe_dump(manifest, sort_keys=False, width=100, allow_unicode=True), encoding="utf-8"
    )
    print(json.dumps(manifest["summary"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
