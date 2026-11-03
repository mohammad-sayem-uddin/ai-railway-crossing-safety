#!/usr/bin/env python3
"""Collect QuickTime `com.apple.quicktime.creationdate` metadata deltas per event.

This is a metadata-derived (not empirical-acoustic) sanity reference only. It is
explicitly NOT treated as ground truth for calibration (device wall clocks are
known to drift by tens of seconds; see R04_CALIBRATION_VALIDATION_REPORT.md).
It exists purely to provide a coarse, independent sanity bound for the acoustic
GCC-PHAT estimate, distinguishing "plausible, matches wall clock to within a
few seconds" from "nothing matches, including the physical direction of lag."

delta_qt_s = creationdate(back) - creationdate(front)
  (positive => back camera's clock recorded a LATER creation time than front,
   i.e. consistent with, but not proof of, back starting recording after front.)
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
LAYER_B_ROOT = REPO_ROOT / "data" / "raw" / "layer_b" / "v2"


def get_creationdate(video_path: Path) -> datetime | None:
    require_media_authorization(video_path, "MEDIA_PROBE")
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format_tags=com.apple.quicktime.creationdate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
    except subprocess.CalledProcessError:
        return None
    if not out:
        return None
    # Format: 2026-09-14T14:13:33+0600
    try:
        return datetime.strptime(out, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return None


def main() -> None:
    results = {}
    for cohort_dir in sorted(LAYER_B_ROOT.iterdir()):
        if not cohort_dir.is_dir():
            continue
        for event_dir in sorted(cohort_dir.iterdir()):
            if not event_dir.is_dir() or "historical_duplicate" in event_dir.name:
                continue
            front = event_dir / "camera_front.mov"
            back = event_dir / "camera_back.mov"
            if not (front.exists() and back.exists()):
                continue
            t_front = get_creationdate(front)
            t_back = get_creationdate(back)
            key = f"{cohort_dir.name}/{event_dir.name}"
            if t_front is None or t_back is None:
                results[key] = {"error": "creationdate missing"}
                continue
            delta_s = (t_back - t_front).total_seconds()
            results[key] = {
                "creationdate_front": t_front.isoformat(),
                "creationdate_back": t_back.isoformat(),
                "delta_qt_s": delta_s,
            }
            print(f"{key}: delta_qt_s={delta_s:+.1f}")

    out_path = REPO_ROOT / "results" / "r04_sync_estimation" / "quicktime_creationdate_deltas.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {len(results)} entries to {out_path}")


if __name__ == "__main__":
    main()
