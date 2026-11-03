#!/usr/bin/env python3
"""Write the read-only ground-truth readiness audit (JSON + Markdown).

    python scripts/audit_ground_truth_readiness.py --json out.json --md out.md

Refuses to write inside data/ground_truth, configs, models or experiments.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from railway_detection.annotation.readiness_audit import (  # noqa: E402
    audit_ground_truth_readiness,
    render_markdown,
)

PROTECTED = (
    "data/ground_truth",
    "data/manifests",
    "data/splits",
    "configs",
    "models",
    "experiments",
)


def _check(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    for item in PROTECTED:
        guard = (root / item).resolve()
        if resolved == guard or guard in resolved.parents:
            raise SystemExit(f"refusing to write inside protected path {item}")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--json", dest="json_out", required=True)
    parser.add_argument("--md", dest="md_out", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    json_path, md_path = _check(Path(args.json_out), root), _check(Path(args.md_out), root)
    report = audit_ground_truth_readiness(root)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
