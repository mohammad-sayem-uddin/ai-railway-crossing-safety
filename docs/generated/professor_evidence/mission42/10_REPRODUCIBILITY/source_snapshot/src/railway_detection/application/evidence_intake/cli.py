"""Reference-only documentary CLI. No live verifier or human review route."""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

from railway_detection.annotation.evidence_review.contracts import canonical, integer
from railway_detection.application.preflight.catalog import ROOT

from .intake import EMPTY_HEAD, DocumentaryJournal, Status, parse_evidence


def journal_path(value: str) -> Path:
    path = Path(value).absolute()
    if ".." in path.parts or not path.name.endswith("_documentary.sqlite"):
        raise ValueError("named _documentary.sqlite journal required")
    for root in (ROOT, Path.home() / ".codex"):
        if path == root or root in path.parents:
            raise ValueError("journal requires a dedicated external documentary workspace")
    for parent in reversed((path, *path.parents)):
        if parent.is_symlink():
            raise ValueError("documentary journal aliases refused")
    return path


def add_arguments(commands):
    parser = commands.add_parser("evidence", help="Document-reference intake; no source access")
    sub = parser.add_subparsers(dest="evidence_command", required=True)
    for name in ("init", "submit", "advance", "inspect"):
        command = sub.add_parser(name)
        command.add_argument("--journal", required=True)
        command.add_argument("--now", type=int, required=True)
        if name != "init":
            command.add_argument("--expected-head", required=True)
        if name in ("submit", "advance"):
            command.add_argument("--request", required=True)
        if name == "advance":
            command.add_argument("--evidence-id", required=True)
            command.add_argument("--target", choices=[s.value for s in Status], required=True)
            command.add_argument("--reason", required=True)
        command.set_defaults(func=dispatch)
    report = sub.add_parser("report")
    report.add_argument("--now", type=int, required=True)
    report.add_argument("--format", choices=("json", "markdown"), default="markdown")
    report.set_defaults(func=dispatch)


def dispatch(args):
    try:
        integer(args.now)
        if args.evidence_command == "report":
            from .reporting import dashboard, render

            result = dashboard(now=args.now)
            print(canonical(result) if args.format == "json" else render(result))
            return 0
        path = journal_path(args.journal)
        if args.evidence_command == "init":
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        elif not path.is_file():
            raise ValueError("existing documentary journal required")
        # Input is only bounded stdin JSON; no evidence/resource file is opened.
        with sqlite3.connect(path) as connection:
            journal = DocumentaryJournal(connection)
            head = EMPTY_HEAD if args.evidence_command == "init" else args.expected_head
            retry = False
            if args.evidence_command in ("submit", "advance"):
                before = journal.snapshot(expected_head=head, now=args.now)
                retry = any(row["request"] == args.request for row in before["audit_history"])
            if args.evidence_command == "submit":
                item = parse_evidence(sys.stdin.read(64 * 1024 + 1))
                head = journal.submit(item, request=args.request, expected_head=head)
            elif args.evidence_command == "advance":
                head = journal.transition(
                    args.evidence_id,
                    Status(args.target),
                    request=args.request,
                    expected_head=head,
                    now=args.now,
                    reason=args.reason,
                )  # verifier intentionally unavailable; high-trust stages refuse
            result_head = head
            # An exact retry returns its original receipt, while later committed
            # entries must remain visible under the caller's current retained head.
            if retry:
                head = args.expected_head
            report = journal.snapshot(expected_head=head, now=args.now)
            if args.evidence_command in ("submit", "advance"):
                report["request_result_head"] = result_head
            print(canonical(report))
        return 0
    except PermissionError as error:
        print(
            canonical({"schema": "DOCUMENTARY_ERROR/1", "status": "BLOCKED", "reason": str(error)})
        )
        return 3
    except (ValueError, TypeError, KeyError, OSError, sqlite3.Error) as error:
        print(
            canonical({"schema": "DOCUMENTARY_ERROR/1", "status": "REFUSED", "reason": str(error)})
        )
        return 2
