"""Synthetic unit tests for Linux / Raspberry Pi telemetry & preprocess helpers."""
# INPUT_CLASSIFICATION: SYNTHETIC_ONLY

from __future__ import annotations

from pathlib import Path

from railway_detection.optimization.pi_telemetry import (
    benchmark_synthetic_opencv_preprocess,
    collect_host_telemetry,
    read_cpu_governor,
    read_linux_vmhwm_mb,
    read_soc_thermal_celsius,
)


def test_read_linux_vmhwm_mb_parses_proc_status_and_handles_missing(tmp_path: Path) -> None:
    status = tmp_path / "status"
    status.write_text("Name:\tpython\nVmHWM:\t  409600 kB\nVmRSS:\t204800 kB\n", encoding="utf-8")
    assert read_linux_vmhwm_mb(status) == 400.0
    assert read_linux_vmhwm_mb(tmp_path / "missing") is None


def test_read_soc_thermal_celsius_and_cpu_governor(tmp_path: Path) -> None:
    temp_file = tmp_path / "temp"
    temp_file.write_text("54321\n", encoding="utf-8")
    assert read_soc_thermal_celsius(temp_file) == 54.32

    temp_deg = tmp_path / "temp_deg"
    temp_deg.write_text("48.5\n", encoding="utf-8")
    assert read_soc_thermal_celsius(temp_deg) == 48.5

    gov_file = tmp_path / "scaling_governor"
    gov_file.write_text("performance\n", encoding="utf-8")
    assert read_cpu_governor(gov_file) == "performance"

    snap = collect_host_telemetry(
        proc_status_path=tmp_path / "missing_status",
        thermal_path=temp_file,
        governor_path=gov_file,
    )
    assert snap == {"vmhwm_mb": None, "soc_temp_c": 54.32, "cpu_governor": "performance"}


def test_benchmark_synthetic_opencv_preprocess_in_memory_only() -> None:
    res = benchmark_synthetic_opencv_preprocess(
        src_height=240, src_width=320, dst_size=128, warmup=1, iters=3
    )
    assert res["available"] is True
    assert res["input_classification"] == "SYNTHETIC_ONLY"
    assert res["rotation_applied"] == "ROTATE_90_CLOCKWISE"
    assert res["dst_size"] == 128
    assert res["n_iters"] == 3
    assert res["mean_ms"] >= 0.0
    assert res["p95_ms"] >= res["p50_ms"] >= 0.0
