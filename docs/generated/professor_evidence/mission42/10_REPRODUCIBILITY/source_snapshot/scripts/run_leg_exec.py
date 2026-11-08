#!/usr/bin/env python3
"""LEG-EXEC: record the operation-specific authorization (transcription) and/or execute.

    # transcribe the researcher's statement into a bound, UNSIGNED record (never overwrites):
    python scripts/run_leg_exec.py record-authorization --statement-file S.txt \\
        --authorized-by researcher@example.org --source "where the statement was given"
    # verify everything and write the 28 sibling notices (resumable, idempotent):
    python scripts/run_leg_exec.py execute --report docs/generated/LEG_EXEC_OPERATION_REPORT.json

Nothing is written unless the recorded authorization verifies against the live repository.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from railway_detection.annotation.leg_exec import (  # noqa: E402
    LEG_EXEC_AUTH_RELATIVE,
    LegExecError,
    build_authorization_record,
    execute_leg_exec,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--root", default=str(ROOT))
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("record-authorization")
    rec.add_argument("--statement-file", required=True)
    rec.add_argument("--authorized-by", required=True)
    rec.add_argument("--source", required=True)
    ex = sub.add_parser("execute")
    ex.add_argument("--report", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        if args.command == "record-authorization":
            target = root / LEG_EXEC_AUTH_RELATIVE
            if target.exists():
                print(f"refusing to overwrite {target}", file=sys.stderr)
                return 2
            record = build_authorization_record(
                root=root,
                authorized_by=args.authorized_by,
                authorized_at_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                statement=Path(args.statement_file).read_text(encoding="utf-8").strip(),
                recorded_by={
                    "kind": "agent_transcription",
                    "identity": "claude-code engineering agent",
                    "transcription_source": args.source,
                },
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"recorded {target} sha256-body {record['record_sha256']}")
            return 0
        report = execute_leg_exec(root)
        destination = Path(args.report)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    k: report[k]
                    for k in ("completed", "originals_byte_identical", "source_record_count")
                },
                indent=2,
            )
        )
        return 0 if report["completed"] else 1
    except LegExecError as exc:
        print(f"BLOCKED {exc.code}: {exc.detail}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
