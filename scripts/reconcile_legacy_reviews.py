#!/usr/bin/env python3
"""Write the additive legacy-review reconciliation report (read-only on evidence).

Usage:
    python scripts/reconcile_legacy_reviews.py [--root .] \\
        [--output docs/LEGACY_REVIEW_RECONCILIATION.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from railway_detection.annotation.legacy_reconciliation import (  # noqa: E402
    write_reconciliation_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="docs/LEGACY_REVIEW_RECONCILIATION.json")
    args = parser.parse_args()
    report = write_reconciliation_report(args.root, args.output)
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
