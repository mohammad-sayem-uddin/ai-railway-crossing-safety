#!/usr/bin/env python3
"""CLI runner for the Interactive AI Railway Crossing Safety Web Dashboard.

Usage:
    python scripts/dashboard.py
    python scripts/dashboard.py --port 8501 --no-browser
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from railway_detection.demo.server import run_dashboard_server  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dashboard",
        description="Interactive Web Dashboard for AI Railway Crossing Safety Vision Testing",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address to bind the dashboard web server.",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8501,
        help="Port to run the dashboard server on.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the web browser on startup.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    run_dashboard_server(
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
