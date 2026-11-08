#!/usr/bin/env python3
"""Audit, classify, validate and run source-bound Profile A. Profile B is not executable."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from railway_detection.safety.resource_free_acceptance import (  # noqa: E402
    bindings,
    build_register,
    inventory,
    selection,
    validate,
)

DEFAULT_REGISTER = (
    ROOT / "docs/generated/master_reaudit/MISSION_23_TEST_CLASSIFICATION_REGISTER.json"
)


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def destination(value):
    path = Path(value).absolute()
    if path == ROOT or ROOT in path.parents:
        raise ValueError("acceptance artifacts require a new external temporary directory")
    path = path.parent.resolve(strict=True) / path.name
    if path.is_symlink() or path == ROOT or ROOT in path.parents:
        raise ValueError("acceptance output alias enters checkout")
    path.mkdir(exist_ok=False)
    return path


def execute(out: Path, selected: list[str], *, audit: bool, exclusions: dict[str, list[str]]):
    captured = bindings(ROOT)
    write(out / "source_bindings.json", captured)
    site = out / "policy_site"
    site.mkdir()
    (site / "sitecustomize.py").write_text("from mission22_policy import install\ninstall()\n")
    groups: dict[str, list[str]] = {}
    legacy: dict[str, list[str]] = {}
    for node in selected:
        file = node.split("::", 1)[0]
        family = Path(file).parts[1]
        if family.startswith("synthetic_"):
            groups.setdefault(family, []).append(node)
        else:
            legacy.setdefault(file, []).append(node)
    files = sorted(legacy)
    for offset in range(0, len(files), 4):
        groups["legacy_" + str(offset // 4)] = [
            n for f in files[offset : offset + 4] for n in legacy[f]
        ]
    receipts: list[dict[str, Any]] = []
    for name, nodes in groups.items():
        work = out / name
        work.mkdir()
        env = os.environ | {
            "PYTHONPATH": os.pathsep.join(
                [str(site), str(ROOT / "tests"), str(ROOT / "src"), str(ROOT)]
            ),
            "MISSION22_POLICY_ROOT": str(work),
            "MISSION22_SITE_PATH": str(site),
            "MISSION23_COLLECTION_OUTPUT": str(work / "collected.json"),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "TMPDIR": str(work),
            "RUFF_CACHE_DIR": str(work / "ruff"),
            "MPLCONFIGDIR": str(work / "mpl"),
            "XDG_CACHE_HOME": str(work / "cache"),
        }
        conf = (
            ["--confcutdir=tests/" + name] if not name.startswith("legacy_") else ["--noconftest"]
        )
        command = [
            sys.executable,
            "-m",
            "pytest",
            *conf,
            "-p",
            "mission22_policy",
            "-p",
            "mission23_profile",
            "-p",
            "no:cacheprovider",
            "--import-mode=importlib",
            "--continue-on-collection-errors",
            "--basetemp=" + str(work / "temp"),
            "--junitxml=" + str(work / "pytest.xml"),
            "-q",
            *nodes,
        ]
        if shutil.disk_usage(out).free < 32 * 1024 * 1024:
            receipts.append(
                {
                    "group": name,
                    "files": sorted({n.split("::")[0] for n in nodes}),
                    "command": command,
                    "exit_code": None,
                    "status": "NOT_EXECUTED_HOST_DISK_LIMIT",
                    "tests": 0,
                    "failures": 0,
                    "errors": 0,
                    "skipped": 0,
                    "cases": [],
                    "policy_denials": [],
                }
            )
            break
        try:
            with (
                (work / "stdout.txt").open("w") as stdout,
                (work / "stderr.txt").open("w") as stderr,
            ):
                result = subprocess.run(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
            counts = dict.fromkeys(("tests", "failures", "errors", "skipped"), 0)
            cases = []
            xml = work / "pytest.xml"
            if xml.exists():
                tree = ElementTree.parse(xml)
                for suite in tree.iter("testsuite"):
                    for key in counts:
                        counts[key] += int(suite.get(key, "0"))
                for case in tree.iter("testcase"):
                    cases.append(
                        {
                            "class": case.get("classname"),
                            "name": case.get("name"),
                            "outcome": "failed"
                            if case.find("failure") is not None
                            else "error"
                            if case.find("error") is not None
                            else "skipped"
                            if case.find("skipped") is not None
                            else "passed",
                            "diagnostic": "".join(case.itertext())[:16000] if len(case) else "",
                        }
                    )
            collected = (
                json.loads((work / "collected.json").read_text())
                if (work / "collected.json").exists()
                else []
            )
            receipt = {
                "group": name,
                "files": sorted({n.split("::")[0] for n in nodes}),
                "selected": nodes,
                "command": command,
                "exit_code": result.returncode,
                **counts,
                "cases": cases,
                "collected_nodeids": collected,
                "policy_denials": (work / "policy_denials.jsonl").read_text().splitlines()
                if (work / "policy_denials.jsonl").exists()
                else [],
            }
            receipts.append(receipt)
            write(
                out / "receipt.json",
                {
                    "schema": "resource-free-execution/1",
                    "audit": audit,
                    "source_bindings": captured,
                    "all_test_files": inventory(ROOT),
                    "groups": receipts,
                    "not_executed": exclusions,
                    "requested": selected,
                },
            )
            print(name, result.returncode, counts, flush=True)
        finally:
            if (work / "temp").exists():
                shutil.rmtree(
                    work / "temp"
                )  # only this process's generated fixtures; keep receipts
    totals = {k: sum(g[k] for g in receipts) for k in ("tests", "failures", "errors", "skipped")}
    totals["passed"] = totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    attempted = {
        n for g in receipts if g.get("exit_code") is not None for n in g.get("selected", [])
    }
    complete = set(selected) == attempted
    process_errors = sum(g.get("exit_code") not in (0, None) for g in receipts)
    report = {
        "process_errors": process_errors,
        "schema": "resource-free-execution/1",
        "audit": audit,
        "source_bindings": captured,
        "all_test_files": inventory(ROOT),
        "groups": receipts,
        "totals": totals,
        "not_executed": exclusions,
        "requested": selected,
        "execution_complete": complete,
        "source_bindings_unchanged": captured == bindings(ROOT),
        "status": "NONPASSING"
        if totals["failures"] or totals["errors"] or process_errors
        else "INCOMPLETE"
        if not complete or exclusions.get("NOT_EXECUTED_UNKNOWN")
        else "PASSED_SELECTED_RESOURCE_FREE",
    }
    write(out / "receipt.json", report)
    print(
        json.dumps(
            {
                "totals": totals,
                "status": report["status"],
                "not_executed": {k: len(v) for k, v in exclusions.items()},
            }
        )
    )
    return int(
        report["status"] != "PASSED_SELECTED_RESOURCE_FREE"
        or not report["source_bindings_unchanged"]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("audit", "refresh", "validate", "run", "sync-inventory")
    )
    parser.add_argument("--output")
    parser.add_argument("--register", type=Path, default=DEFAULT_REGISTER)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--dependency-evidence", type=Path)
    args = parser.parse_args(argv)
    if args.command == "sync-inventory":
        import yaml

        path = ROOT / "tests/test_access_classification.yaml"
        manifest = yaml.safe_load(path.read_text())
        for file, sha in bindings(ROOT)["modules"].items():
            if manifest["test_files"].get(file, {}).get("sha256") != sha:
                manifest["test_files"][file] = {
                    "sha256": sha,
                    "category": "UNKNOWN",
                    "safe_for_synthetic_runner": False,
                    "reason": file
                    + ": changed/new source; UNKNOWN pending executed evidence review",
                    "access_paths": [],
                    "blocked_attempts": {},
                    "access_dirs": [],
                    "static_hints": [],
                    "spawns_child_process": False,
                    "child_processes_guarded": False,
                    "tests": {"passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                    "evidence": "source_inventory_only_no_dynamic_classification_claim",
                }
        categories = {e["category"] for e in manifest["test_files"].values()}
        manifest["summary"] = {
            "total_test_files": len(manifest["test_files"]),
            **{
                k.lower(): sum(e["category"] == k for e in manifest["test_files"].values())
                for k in categories
            },
            "safe_for_synthetic_runner": sum(
                e["safe_for_synthetic_runner"] for e in manifest["test_files"].values()
            ),
        }
        path.write_text(yaml.safe_dump(manifest, sort_keys=False, width=100))
        return 0
    if args.command == "audit":
        return execute(destination(args.output), inventory(ROOT), audit=True, exclusions={})
    if args.command == "refresh":
        evidence = json.loads(args.evidence.read_text())
        if not evidence.get("execution_complete") or not evidence.get("source_bindings_unchanged"):
            raise ValueError("incomplete/changed-source audit cannot classify tests")
        manual = (
            json.loads(args.dependency_evidence.read_text()) if args.dependency_evidence else {}
        )
        register = build_register(
            ROOT,
            evidence,
            evidence["source_bindings"],
            evidence_ref=str(args.evidence),
            dependency_evidence=manual,
        )
        write(args.register, register)
        return 0
    register = json.loads(args.register.read_text())
    issues = validate(ROOT, register)
    chosen = selection(register)
    if args.command == "validate":
        print(json.dumps({"issues": issues, "counts": {k: len(v) for k, v in chosen.items()}}))
        return 3 if issues else 2 if chosen["unknown"] else 0
    out = destination(args.output)
    if issues:
        write(
            out / "receipt.json",
            {
                "status": "CLASSIFICATION_UNTRUSTED",
                "issues": issues,
                "passed": 0,
                "not_executed": inventory(ROOT),
            },
        )
        return 3
    return execute(
        out,
        chosen["selected"],
        audit=False,
        exclusions={
            "NOT_EXECUTED_PROTECTED_DEPENDENCY": chosen["protected"],
            "NOT_EXECUTED_UNKNOWN": chosen["unknown"],
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
