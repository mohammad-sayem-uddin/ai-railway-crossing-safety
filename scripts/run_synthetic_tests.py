#!/usr/bin/env python3
"""Safe test runner (Mission 10, WP10.3): runs only tests PROVEN not to touch protected data.

Fail-closed, in order:

1. The classification manifest must load and match the tree exactly: every ``tests/**/test_*.py``
   classified, no ghost entries, no file changed since it was classified, categories valid, safety
   flags consistent, no safe-marked file that spawns an unobservable child process.
2. Only categories in the allowlist (default ``SYNTHETIC_ONLY`` and ``METADATA_ONLY``) are selected;
   ``UNKNOWN`` and every data-access category can never be selected.
3. The selection runs in ONE pytest process under the read-blocking access guard, with the guard log
   written outside the repository. Afterwards the log is verified: the guard must have been armed,
   no read may have been blocked, and every metadata read must fall in a directory the manifest
   declared for that file (a ``SYNTHETIC_ONLY`` file may read none). Any deviation is a
   classification violation (exit 4) -- the manifest was wrong and must be regenerated.
4. A machine-readable report is written outside the repository (or under ``reports/``).

Exit codes: 0 all selected tests passed with a clean guard log; 1 test failures; 3 manifest not
trustworthy; 4 guard violation; 2 usage error.

Limitations are disclosed in the report: the guard observes Python-level access only (no OS
sandbox).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_SRC = REPO_ROOT / "src"  # fixed at import: the package under test, whatever tree is run
sys.path.insert(0, str(PACKAGE_SRC))

import subprocess  # noqa: E402

from railway_detection.safety import access_manifest as am  # noqa: E402

RUNNER_VERSION = "2.0.0"
LIMITATIONS = [
    "Python-level access guard only; native code or shell tools outside Python are not observed.",
    "The manifest reflects what tests did when classified; the post-run log check detects drift.",
    "Excluded files are not executed here; they require their own authorization to run.",
]


def _outside_repo_or_reports(path: Path) -> bool:
    path = path.resolve()
    if path == REPO_ROOT or REPO_ROOT not in path.parents:
        return True
    return (REPO_ROOT / "reports") in path.parents


def verify_log(
    events: list[dict[str, Any]], manifest: dict[str, Any], selected: list[str]
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    if not any(e["how"] == "armed" for e in events):
        violations.append({"kind": "GUARD_NOT_ARMED"})
    if not any(e["how"] == "disarmed" for e in events):
        violations.append({"kind": "GUARD_NOT_DISARMED"})
    selected_set = set(selected)
    for event in events:
        if event["blocked"]:
            violations.append({"kind": "BLOCKED_ACCESS", **event})
            continue
        if event["category"] != "METADATA":
            continue
        node = event["node"].split("::", 1)[0]
        if node not in selected_set:
            continue  # session-level / fixture reads are not attributable to a file
        entry = manifest["test_files"][node]
        directory = str(Path(event["path"]).parent)
        if entry["category"] == am.SYNTHETIC_ONLY or directory not in entry["access_dirs"]:
            violations.append(
                {"kind": "UNDECLARED_METADATA_READ", "declared": entry["category"], **event}
            )
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report-path", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=REPO_ROOT / am.MANIFEST_RELATIVE)
    parser.add_argument(
        "--categories",
        default=",".join(sorted(am.SAFE_CATEGORIES)),
        help="comma list; may only contain SYNTHETIC_ONLY and/or METADATA_ONLY",
    )
    parser.add_argument("--dry-run", action="store_true", help="validate and select; run nothing")
    parser.add_argument("extra", nargs="*", help="extra pytest args (e.g. -k expression)")
    args = parser.parse_args(argv)

    requested = frozenset(c.strip() for c in args.categories.split(",") if c.strip())
    if not requested or not requested <= am.SAFE_CATEGORIES:
        print(
            f"error: categories must be a subset of {sorted(am.SAFE_CATEGORIES)}", file=sys.stderr
        )
        return 2
    if not _outside_repo_or_reports(args.report_path):
        print(
            "error: --report-path must be outside the repository or under reports/", file=sys.stderr
        )
        return 2

    report: dict[str, Any] = {"runner_version": RUNNER_VERSION, "limitations": LIMITATIONS}
    try:
        manifest = am.load_manifest(args.manifest)
        problems = am.verify_manifest_against_tree(manifest, REPO_ROOT)
    except am.ManifestError as exc:
        manifest, problems = None, [str(exc)]
    if problems or manifest is None:
        report.update(status="MANIFEST_UNTRUSTED", problems=problems)
        _write(args.report_path, report)
        print("\n".join(problems), file=sys.stderr)
        print(f"refusing to run: {len(problems)} manifest problem(s)", file=sys.stderr)
        return 3

    selected = am.select_files(manifest, requested)
    excluded: dict[str, list[str]] = {}
    for rel, entry in manifest["test_files"].items():
        if rel not in selected:
            excluded.setdefault(entry["category"], []).append(rel)
    report.update(
        manifest_sha256=am.sha256_of(args.manifest),
        selected_count=len(selected),
        selected=selected,
        excluded={k: sorted(v) for k, v in sorted(excluded.items())},
    )
    if args.dry_run or not selected:
        report["status"] = "DRY_RUN" if args.dry_run else "NOTHING_SELECTED"
        _write(args.report_path, report)
        print(f"{report['status']}: {len(selected)} file(s) selected")
        return 0 if selected or args.dry_run else 2

    work = Path(tempfile.mkdtemp(prefix="synthetic_run_"))
    log, junit = work / "guard.jsonl", work / "junit.xml"
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
        *args.extra,
        *selected,
    ]
    env = os.environ | {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": os.pathsep.join(
            filter(None, [str(PACKAGE_SRC), os.environ.get("PYTHONPATH", "")])
        ),
        "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
    }
    proc = subprocess.run(cmd, cwd=REPO_ROOT, env=env, capture_output=True, text=True)
    events = (
        [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line]
        if log.is_file()
        else []
    )
    violations = verify_log(events, manifest, selected)
    counts = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}
    if junit.is_file():
        root = ET.parse(junit).getroot()
        suite = root if root.tag == "testsuite" else root.find("testsuite")
        if suite is not None:
            total = int(suite.get("tests", 0))
            counts = {
                "failed": int(suite.get("failures", 0)),
                "errors": int(suite.get("errors", 0)),
                "skipped": int(suite.get("skipped", 0)),
            }
            counts["passed"] = total - counts["failed"] - counts["errors"] - counts["skipped"]
    report.update(
        pytest_exit_code=proc.returncode,
        tests=counts,
        guard={
            "events": len(events),
            "blocked": sum(1 for e in events if e["blocked"]),
            "metadata_reads": sum(1 for e in events if e["category"] == "METADATA"),
        },
        violations=violations,
        status="CLASSIFICATION_VIOLATION"
        if violations
        else ("PASSED" if proc.returncode == 0 else "TESTS_FAILED"),
    )
    _write(args.report_path, report)
    print(proc.stdout[-2000:])
    if violations:
        print(f"{len(violations)} guard violation(s); see {args.report_path}", file=sys.stderr)
        return 4
    return 0 if proc.returncode == 0 else 1


def _write(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
