#!/usr/bin/env python3
"""Build event-level R04 evidence and the v9/M4 comparison record.

This command only reads existing evidence and writes additive candidate reports.
It never runs inference, edits annotations, promotes calibration, or records a
protocol choice.  Use ``--output-dir`` to write to a separate directory during
review; the default is ``docs/generated/r04``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from railway_detection.data.r04_evidence import (  # noqa: E402
    build_r04_evidence,
    render_comparison_markdown,
    render_scope_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "docs" / "generated" / "r04",
        help="Directory for additive JSON/Markdown reports (default: docs/generated/r04)",
    )
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else REPO_ROOT / args.output_dir
    evidence = build_r04_evidence(REPO_ROOT)
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = output_dir / "R04_EVENT_EVIDENCE.json"
    scope_path = output_dir / "R04_EVENT_SCOPE_REPORT.md"
    comparison_path = output_dir / "PREMATURE_OPENING_V9_M4_COMPARISON.md"
    evidence_path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    scope_path.write_text(render_scope_markdown(evidence), encoding="utf-8")
    comparison_path.write_text(render_comparison_markdown(evidence), encoding="utf-8")
    print(f"Wrote {evidence_path}")
    print(f"Wrote {scope_path}")
    print(f"Wrote {comparison_path}")
    print(json.dumps(evidence["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
