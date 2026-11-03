#!/usr/bin/env python3
"""Classify every test file by the data it is observed to touch (Mission 10, WP10.3).

Each ``tests/**/test_*.py`` file is run **individually, in its own interpreter, under the
read-blocking access guard** (``railway_detection.safety.access_guard_plugin``). The guard raises on
any attempt to read raw media, model weights, processed data or results, so classifying a file never
reads them; the attempt itself is what is recorded. The manifest is rebuilt from those logs plus a
static scan, never from a template, and every entry carries test-specific reasons and access paths.

Usage::

    python scripts/classify_test_access.py --work-dir /tmp/classify_run          # rewrite manifest
    python scripts/classify_test_access.py --work-dir /tmp/classify_run --check  # verify only

``--work-dir`` must be outside the repository (logs and JUnit files are written there).
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_SRC = REPO_ROOT / "src"
sys.path.insert(0, str(PACKAGE_SRC))

from railway_detection.safety import access_manifest as am  # noqa: E402
from railway_detection.safety.access_guard_plugin import (  # noqa: E402
    CATEGORY_CHECKPOINT,
    CATEGORY_METADATA,
    CATEGORY_PROCESSED,
    CATEGORY_RAW,
)

TIMEOUT_S = 600
CATEGORY_OF = {
    CATEGORY_RAW: am.RAW_MEDIA_ACCESS,
    CATEGORY_CHECKPOINT: am.MODEL_CHECKPOINT_ACCESS,
    CATEGORY_PROCESSED: am.PROCESSED_DATA_ACCESS,
}
PRECEDENCE = [CATEGORY_RAW, CATEGORY_CHECKPOINT, CATEGORY_PROCESSED]
STATIC_PATTERNS = (
    "data/raw",
    "data/processed",
    "experiments/",
    "results/",
    "best.pt",
    ".mov",
    ".mp4",
)
SPAWN_CALLS = {
    ("subprocess", name) for name in ("run", "Popen", "check_output", "check_call", "call")
}
SPAWN_CALLS |= {("os", "system"), ("os", "popen"), ("runpy", "run_path"), ("runpy", "run_module")}


#: Files reviewed by hand whose child processes are all launched under the access guard. The
#: classifier still requires the guard plugin to be named in the file; the file hash binds
#: the review.
GUARDED_SPAWNERS: dict[str, str] = {
    "tests/unit/test_access_classification_tools.py": (
        "every child pytest it launches loads railway_detection.safety.access_guard_plugin "
        "(_run_probe, the runner tests via run_synthetic_tests.main, the log-location test)"
    ),
}


def static_scan(path: Path) -> tuple[list[str], bool]:
    """Protected-path string literals, and whether a child process is spawned."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hints: set[str] = set()
    spawns = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if any(p in node.value for p in STATIC_PATTERNS) and len(node.value) < 200:
                hints.add(node.value)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and (node.func.value.id, node.func.attr) in SPAWN_CALLS
            ):
                spawns = True
    return sorted(hints), spawns


def run_one(rel: str, work: Path) -> dict[str, Any]:
    stem = rel.replace("/", "__")
    log, junit = work / f"{stem}.jsonl", work / f"{stem}.xml"
    for stale in (log, junit):
        stale.unlink(missing_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "railway_detection.safety.access_guard_plugin",
        "--access-guard-log",
        str(log),
        "-p",
        "no:cacheprovider",
        "-q",
        "--no-header",
        f"--junitxml={junit}",
        rel,
    ]
    env = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(PACKAGE_SRC),
        "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
    }
    try:
        proc = subprocess.run(
            cmd, cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=TIMEOUT_S
        )
        exit_code, timed_out = proc.returncode, False
    except subprocess.TimeoutExpired:
        exit_code, timed_out = -1, True
    tests = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}
    if junit.is_file():
        suite = ET.parse(junit).getroot()
        suite = suite if suite.tag == "testsuite" else suite.find("testsuite")
        if suite is not None:
            total = int(suite.get("tests", 0))
            tests = {
                "failed": int(suite.get("failures", 0)),
                "errors": int(suite.get("errors", 0)),
                "skipped": int(suite.get("skipped", 0)),
                "passed": total
                - int(suite.get("failures", 0))
                - int(suite.get("errors", 0))
                - int(suite.get("skipped", 0)),
            }
    events = []
    if log.is_file():
        events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line]
    return {
        "exit_code": exit_code,
        "timed_out": timed_out,
        "tests": tests,
        "events": events,
        "armed": any(e["how"] == "armed" for e in events),
    }


def classify(rel: str, result: dict[str, Any]) -> dict[str, Any]:
    path = REPO_ROOT / rel
    hints, spawns = static_scan(path)
    blocked = [e for e in result["events"] if e["blocked"]]
    by_cat = Counter(e["category"] for e in blocked)
    metadata = sorted({e["path"] for e in result["events"] if e["category"] == CATEGORY_METADATA})
    blocked_paths = sorted({e["path"] for e in blocked})
    executed = sum(result["tests"].values())
    entry: dict[str, Any] = {
        "sha256": am.sha256_of(path),
        "blocked_attempts": dict(sorted(by_cat.items())),
        "access_paths": (blocked_paths + metadata)[:40],
        "access_dirs": sorted({str(Path(x).parent) for x in blocked_paths + metadata}),
        "static_hints": hints[:20],
        "spawns_child_process": spawns,
        "tests": result["tests"],
        "evidence": "dynamic_run_under_read_blocking_guard",
    }
    if (
        result["timed_out"]
        or not result["armed"]
        or executed == 0
        or result["exit_code"] in (2, 3, 4, 5)
    ):
        why = (
            "timed out"
            if result["timed_out"]
            else "guard never armed"
            if not result["armed"]
            else f"no test executed (pytest exit {result['exit_code']})"
        )
        entry.update(category=am.UNKNOWN, reason=f"Access could not be established: {why}.")
    elif by_cat:
        top = next(c for c in PRECEDENCE if c in by_cat)
        first = next(e for e in blocked if e["category"] == top)
        entry.update(
            category=CATEGORY_OF[top],
            reason=(
                f"Attempted {sum(by_cat.values())} blocked read(s) of {'/'.join(sorted(by_cat))} "
                f"locations; e.g. {first['path']} via {first['how']} in "
                f"{first['node'].split('::', 1)[-1]}."
            ),
        )
    elif metadata:
        sample = ", ".join(metadata[:3])
        entry.update(
            category=am.METADATA_ONLY,
            reason=f"Reads {len(metadata)} repository metadata file(s) (e.g. {sample}); no media, "
            "weights, processed data or results were requested.",
        )
    else:
        entry.update(
            category=am.SYNTHETIC_ONLY,
            reason=f"{executed} test(s) executed; no repository file outside source/test code was "
            "read; all data is created in temporary directories.",
        )
    guarded = (
        spawns
        and rel in GUARDED_SPAWNERS
        and "access_guard_plugin" in path.read_text(encoding="utf-8")
    )
    entry["child_processes_guarded"] = bool(guarded)
    if spawns and entry["category"] in am.SAFE_CATEGORIES:
        if guarded:
            entry["reason"] += f" Child processes are reviewed as guarded: {GUARDED_SPAWNERS[rel]}."
        else:
            entry["reason"] += " NOTE: the file spawns a child process the guard cannot observe."
            entry["category"] = am.UNKNOWN
    entry["safe_for_synthetic_runner"] = entry["category"] in am.SAFE_CATEGORIES
    return dict(sorted(entry.items()))


def build_manifest(work: Path, reuse: dict[str, Any] | None = None) -> dict[str, Any]:
    """Classify every test file; ``reuse`` (incremental) keeps entries of unchanged files."""
    files = am.discover_test_files(REPO_ROOT)
    entries: dict[str, Any] = {}
    for index, rel in enumerate(files, 1):
        previous = (reuse or {}).get(rel)
        if previous and previous.get("sha256") == am.sha256_of(REPO_ROOT / rel):
            print(f"[{index}/{len(files)}] {rel} (unchanged, reused)", flush=True)
            entries[rel] = previous
            continue
        print(f"[{index}/{len(files)}] {rel}", flush=True)
        entries[rel] = classify(rel, run_one(rel, work))
    counts = Counter(e["category"] for e in entries.values())
    return {
        "schema_version": am.MANIFEST_SCHEMA,
        "generator": "scripts/classify_test_access.py",
        "method": (
            "Each file run alone under railway_detection.safety.access_guard_plugin, which blocks "
            "reads of raw media, model weights, processed data and results and records "
            "every attempt; "
            "plus an AST scan for protected-path literals and child-process calls."
        ),
        "categories_definition": am.CATEGORY_DEFINITIONS,
        "limitations": [
            "Python-level guard only: native code that opens files without builtins.open, io.open, "
            "os.open, os.scandir/listdir, subprocess arguments or cv2.VideoCapture is "
            "not observed.",
            "A test that fails early on its first blocked read may hide later reads; the "
            "category is "
            "still at least what was observed. Re-run the generator after any test change.",
            "The classification is bound to each file's SHA-256; a changed file is STALE "
            "and not run.",
            "Reads performed by the repository's tests/conftest.py registry fingerprint are exempt "
            "(results/experiment_registry.jsonl, a text run-log).",
        ],
        "summary": {
            "total_test_files": len(entries),
            **{c.lower(): counts.get(c, 0) for c in am.CATEGORIES},
            "safe_for_synthetic_runner": sum(
                e["safe_for_synthetic_runner"] for e in entries.values()
            ),
        },
        "test_files": entries,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--work-dir", type=Path, required=True, help="scratch dir OUTSIDE the repo")
    parser.add_argument(
        "--check", action="store_true", help="verify the manifest instead of rewriting"
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="reuse entries of unchanged files (iteration aid; do a full run for the "
        "final manifest)",
    )
    parser.add_argument("--manifest", type=Path, default=REPO_ROOT / am.MANIFEST_RELATIVE)
    args = parser.parse_args(argv)
    work = args.work_dir.resolve()
    if work == REPO_ROOT or REPO_ROOT in work.parents:
        print("error: --work-dir must be outside the repository", file=sys.stderr)
        return 2
    work.mkdir(parents=True, exist_ok=True)
    if args.check:
        try:
            problems = am.verify_manifest_against_tree(am.load_manifest(args.manifest), REPO_ROOT)
        except am.ManifestError as exc:
            problems = [str(exc)]
        for problem in problems:
            print(problem)
        print("manifest OK" if not problems else f"{len(problems)} problem(s)")
        return 0 if not problems else 1
    reuse = None
    if args.incremental and args.manifest.is_file():
        reuse = am.load_manifest(args.manifest)["test_files"]
    manifest = build_manifest(work, reuse)
    args.manifest.write_text(
        yaml.safe_dump(manifest, sort_keys=False, width=100, allow_unicode=True), encoding="utf-8"
    )
    print(json.dumps(manifest["summary"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
