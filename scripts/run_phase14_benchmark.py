#!/usr/bin/env python3
"""Reproducible Phase 14 benchmark report (synthetic workload; engineering measurement only).

Thin wrapper over ``railway_detection.optimization.benchmark_cli``. Example:

    python scripts/run_phase14_benchmark.py --output /tmp/phase14_bench.json [--vision-model]

The report records code revision, artifact fingerprints, host details, per-stage latency,
throughput, memory, an output fingerprint and limitations. It never makes a real-time or
safety claim; see docs/PHASE14_PROFILING_INFRASTRUCTURE.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from railway_detection.optimization.benchmark_cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
