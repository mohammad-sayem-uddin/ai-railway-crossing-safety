#!/usr/bin/env python3
"""Run only the constructed Mission22 integration demonstration."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from railway_detection.synthetic.integration_workflow import run_demo  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=22)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--code-identity")
    parser.add_argument("--interrupt-after", choices=("initialization", "review_commit", "review"))
    args = parser.parse_args()
    code = (
        args.code_identity
        or subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    )
    try:
        result = run_demo(
            args.output,
            seed=args.seed,
            code_identity=code,
            resume=args.resume,
            stop_after=args.interrupt_after,
        )
    except InterruptedError as error:
        print(json.dumps({"classification": "CONSTRUCTED_INTERRUPTION", "error": str(error)}))
        return 75
    except (ValueError, OSError, RuntimeError, sqlite3.Error) as error:
        print(
            json.dumps({"classification": "CONSTRUCTED_DEMONSTRATION_REFUSED", "error": str(error)})
        )
        return 2
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "output": args.output,
                "complete": True,
                "live_operations": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
