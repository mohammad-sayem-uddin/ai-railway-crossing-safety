"""Lightweight Linux / Raspberry Pi telemetry & synthetic preprocess helpers.

All helpers in this module inspect OS telemetry strictly read-only (with
injectable ``proc_root`` / ``sys_root`` paths for unit testing) and operate
strictly on in-memory synthetic numpy/OpenCV buffers when benchmarking frame
rotation and resize preprocessing. Physical Raspberry Pi hardware must still be
verified via ``/proc/device-tree/model`` (`is_physical_raspberry_pi = True`).
"""

from __future__ import annotations

import statistics
import time
from pathlib import Path
from typing import Any


def read_linux_vmhwm_mb(proc_status_path: Path | None = None) -> float | None:
    """Read Linux ``VmHWM`` (peak RSS in MB) from ``/proc/self/status`` when present."""
    path = proc_status_path or Path("/proc/self/status")
    if not path.is_file():
        return None
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("VmHWM:"):
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    return round(int(parts[1]) / 1024.0, 2)
    except OSError:
        return None
    return None


def read_soc_thermal_celsius(thermal_path: Path | None = None) -> float | None:
    """Read SoC temperature (deg C) from ``/sys/class/thermal/thermal_zone0/temp``."""
    path = thermal_path or Path("/sys/class/thermal/thermal_zone0/temp")
    if not path.is_file():
        return None
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not raw:
            return None
        val = float(raw)
        # Linux thermal sysfs reports millidegrees C (e.g. 54200 -> 54.2 C).
        return round(val / 1000.0 if val > 1000.0 else val, 2)
    except (OSError, ValueError):
        return None


def read_cpu_governor(governor_path: Path | None = None) -> str | None:
    """Read active cpufreq scaling governor when exposed by Linux sysfs."""
    path = governor_path or Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        return text or None
    except OSError:
        return None


def collect_host_telemetry(
    *,
    proc_status_path: Path | None = None,
    thermal_path: Path | None = None,
    governor_path: Path | None = None,
) -> dict[str, Any]:
    """Capture non-spoofing OS memory/thermal/governor telemetry snapshot."""
    return {
        "vmhwm_mb": read_linux_vmhwm_mb(proc_status_path),
        "soc_temp_c": read_soc_thermal_celsius(thermal_path),
        "cpu_governor": read_cpu_governor(governor_path),
    }


def benchmark_synthetic_opencv_preprocess(
    *,
    src_height: int = 1080,
    src_width: int = 1920,
    dst_size: int = 416,
    warmup: int = 2,
    iters: int = 10,
) -> dict[str, Any]:
    """Time in-memory synthetic JPEG decode + 90-deg rotation + resize via OpenCV."""
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        return {"available": False, "reason": str(exc)}

    rng = np.random.default_rng(20261115)
    frame = rng.integers(0, 255, size=(src_height, src_width, 3), dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        return {"available": False, "reason": "cv2.imencode failed"}

    def _step() -> None:
        decoded = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        rotated = cv2.rotate(decoded, cv2.ROTATE_90_CLOCKWISE)
        _ = cv2.resize(rotated, (dst_size, dst_size), interpolation=cv2.INTER_LINEAR)

    for _ in range(warmup):
        _step()
    times_ms: list[float] = []
    for _ in range(iters):
        t0 = time.perf_counter()
        _step()
        times_ms.append((time.perf_counter() - t0) * 1000.0)
    ordered = sorted(times_ms)
    mean_ms = statistics.fmean(ordered)
    return {
        "available": True,
        "input_classification": "SYNTHETIC_ONLY",
        "src_shape": [src_width, src_height],
        "rotation_applied": "ROTATE_90_CLOCKWISE",
        "dst_size": dst_size,
        "n_iters": iters,
        "mean_ms": round(mean_ms, 3),
        "p50_ms": round(ordered[len(ordered) // 2], 3),
        "p95_ms": round(ordered[min(len(ordered) - 1, max(0, int(0.95 * (len(ordered) - 1))))], 3),
    }
