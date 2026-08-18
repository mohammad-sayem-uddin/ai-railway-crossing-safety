#!/usr/bin/env python3
"""Convenience root wrapper to launch the Interactive Web Dashboard.

Runs the local server and opens your browser:
    python dashboard.py
"""

from __future__ import annotations

import sys
from pathlib import Path

scripts_dir = Path(__file__).resolve().parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from dashboard import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
