#!/usr/bin/env python3
"""Convenience root wrapper for the Railway Train Detection Video Demo.

Executes scripts/demo_video.py directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Forward execution to scripts/demo_video.py
scripts_dir = Path(__file__).resolve().parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from demo_video import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
