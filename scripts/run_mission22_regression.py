#!/usr/bin/env python3
"""Account for the complete test inventory under a constructed-only access policy.

Independent Mission suites require fresh processes for their import/IO guards.
Root tests receive per-test registry redirects without reading the real registry.
Policy blocks and collection errors are failures, never invented passes/skips.
"""

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


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    out = Path(args.output).absolute()
    if out == ROOT or ROOT in out.parents:
        raise ValueError("regression artifacts require an external constructed directory")
    out = out.parent.resolve(strict=True) / out.name
    if out == ROOT or ROOT in out.parents or out.is_symlink():
        raise ValueError("regression output alias enters checkout")
    out.mkdir(exist_ok=False)
    site = out / "policy_site"
    site.mkdir()
    (site / "sitecustomize.py").write_text("from mission22_policy import install\ninstall()\n")
    files = sorted(ROOT.joinpath("tests").rglob("test*.py"))
    grouped: dict[str, list[str]] = {}
    legacy = []
    for file in files:
        relative = file.relative_to(ROOT)
        if len(relative.parts) > 2 and relative.parts[1].startswith("synthetic_"):
            grouped.setdefault(relative.parts[1], []).append(str(relative))
        else:
            legacy.append(str(relative))
    for i in range(0, len(legacy), 12):
        grouped["legacy_inventory_batch_" + str(i // 12)] = legacy[i : i + 12]
    receipts: list[dict[str, Any]] = []
    for group, paths in grouped.items():
        work = out / group
        work.mkdir()
        (work / "tmp").mkdir()
        xml = work / "pytest.xml"
        env = os.environ | {
            "PYTHONPATH": os.pathsep.join(
                [str(site), str(ROOT / "tests"), str(ROOT / "src"), str(ROOT)]
            ),
            "MISSION22_POLICY_ROOT": str(work),
            "MISSION22_SITE_PATH": str(site),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "TMPDIR": str(work),
            "RUFF_CACHE_DIR": str(work / "ruff_cache"),
            "MPLCONFIGDIR": str(work / "mpl"),
            "XDG_CACHE_HOME": str(work / "cache"),
        }
        conf = (
            ["--noconftest"]
            if group.startswith("legacy_inventory_batch_")
            else ["--confcutdir=tests/" + group]
        )
        command = [
            sys.executable,
            "-m",
            "pytest",
            *conf,
            "-p",
            "mission22_policy",
            "-p",
            "no:cacheprovider",
            "--import-mode=importlib",
            "--continue-on-collection-errors",
            "--basetemp=" + str(work / "temp"),
            "--junitxml=" + str(xml),
            "-q",
            *paths,
        ]
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
        (work / "stdout.txt").write_text(result.stdout)
        (work / "stderr.txt").write_text(result.stderr)
        counts = {k: 0 for k in ("tests", "failures", "errors", "skipped")}
        cases = []
        if xml.exists():
            tree = ElementTree.parse(xml)
            for s in tree.iter("testsuite"):
                for k in counts:
                    counts[k] += int(s.get(k, "0"))
            for c in tree.iter("testcase"):
                cases.append(
                    {
                        "class": c.get("classname"),
                        "name": c.get("name"),
                        "outcome": "failed"
                        if c.find("failure") is not None
                        else "error"
                        if c.find("error") is not None
                        else "skipped"
                        if c.find("skipped") is not None
                        else "passed",
                        "diagnostic": "".join(c.itertext())[:12000] if len(c) else "",
                    }
                )
        receipt = {
            "group": group,
            "files": paths,
            "command": command,
            "exit_code": result.returncode,
            **counts,
            "cases": cases,
            "policy_denials": (work / "policy_denials.jsonl").read_text().splitlines()
            if (work / "policy_denials.jsonl").exists()
            else [],
        }
        receipts.append(receipt)
        (out / "regression.json").write_text(
            json.dumps(
                {
                    "classification": "CONSTRUCTED_REGRESSION_EXECUTION",
                    "all_test_files": [str(f.relative_to(ROOT)) for f in files],
                    "groups": receipts,
                },
                indent=2,
            )
            + "\n"
        )
        print(group, result.returncode, counts, flush=True)
        if (work / "temp").exists():
            shutil.rmtree(
                work / "temp"
            )  # only this runner's generated test fixtures; receipts retained
    assert set(x for r in receipts for x in r["files"]) == set(
        str(f.relative_to(ROOT)) for f in files
    )
    return int(any(r["exit_code"] != 0 for r in receipts))


if __name__ == "__main__":
    raise SystemExit(main())
