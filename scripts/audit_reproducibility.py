#!/usr/bin/env python3
"""Read-only reproducibility audit: JSON + Markdown. Refuses to write inside repository trees.

    python scripts/audit_reproducibility.py --json out.json --md out.md [--results DIR ...]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from railway_detection.reproducibility import (  # noqa: E402
    render_markdown,
    run_reproducibility_audit,
)

PROTECTED = ("data", "configs", "models", "experiments", "results", "src", "tests", "docs")


def _check(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    for name in PROTECTED:
        guard = (root / name).resolve()
        if resolved == guard or guard in resolved.parents:
            raise SystemExit(f"refusing to write inside {name}/")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--json", dest="json_out", required=True)
    parser.add_argument("--md", dest="md_out", required=True)
    parser.add_argument("--results", action="append", default=[], help="Official result dir(s).")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    json_path, md_path = _check(Path(args.json_out), root), _check(Path(args.md_out), root)
    report = run_reproducibility_audit(root, result_dirs=[Path(r) for r in args.results])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["status_counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
