#!/usr/bin/env python3
"""Standalone Raspberry Pi / ARM-Linux deployment packager & CPU scaling benchmark CLI.

Strictly SYNTHETIC_ONLY: never opens raw media. Exports TorchScript & stripped
FP16/FP32 weight bundles to an external directory or temporary workspace and
profiles multi-thread CPU scaling on synthetic tensors while honestly detecting
whether execution is running on physical Raspberry Pi hardware vs host dev CPU.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from railway_detection.audio.features import compute_log_mel_spectrogram  # noqa: E402
from railway_detection.audio.model import CompactTrainHornCNN  # noqa: E402


class _YoloWrapper(torch.nn.Module):
    def __init__(self, model: torch.nn.Module) -> None:
        super().__init__()
        self.model = model

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.model(x)
        return out[0] if isinstance(out, (tuple, list)) else out


def detect_hardware_target() -> dict[str, Any]:
    """Identify host vs Raspberry Pi ARM Linux honestly without spoofing."""
    model_path = Path("/proc/device-tree/model")
    dt_model = model_path.read_text(encoding="utf-8", errors="ignore").strip("\x00\n ") if model_path.is_file() else None
    is_linux_arm = sys.platform.startswith("linux") and platform.machine() in {"aarch64", "arm64", "armv7l"}
    is_rpi = bool(dt_model and "raspberry pi" in dt_model.lower()) and is_linux_arm
    return {
        "os": platform.system(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "device_tree_model": dt_model,
        "is_physical_raspberry_pi": is_rpi,
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "cpu_count": os.cpu_count(),
    }


def _time_fn(fn, *, warmup: int, iters: int) -> dict[str, float]:
    for _ in range(warmup):
        fn()
    samples = []
    for _ in range(iters):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000.0)
    arr = np.asarray(samples, dtype=np.float64)
    mean_ms = float(np.mean(arr))
    return {
        "n_iters": iters,
        "mean_ms": round(mean_ms, 3),
        "p50_ms": round(float(np.percentile(arr, 50)), 3),
        "p95_ms": round(float(np.percentile(arr, 95)), 3),
        "fps_equivalent": round(1000.0 / mean_ms, 2) if mean_ms > 0 else 0.0,
    }


def run_edge_package_and_benchmark(
    root: Path,
    *,
    export_dir: Path,
    thread_counts: tuple[int, ...] = (1, 2, 4),
    imgszs: tuple[int, ...] = (320, 416),
    iters: int = 12,
) -> dict[str, Any]:
    export_dir.mkdir(parents=True, exist_ok=True)
    vision_ckpt = root / "experiments/vision/39f402dfe460/checkpoints/weights/best.pt"
    audio_ckpt = root / "experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt"

    yolo = YOLO(str(vision_ckpt)).model.float().eval()
    wrap = _YoloWrapper(yolo).eval()
    ac_state = torch.load(audio_ckpt, map_location="cpu", weights_only=False)
    acnn = CompactTrainHornCNN().float().eval()
    acnn.load_state_dict(ac_state["model_state_dict"])

    bundles: dict[str, Any] = {}
    torch.save({"model": {k: v.half() for k, v in yolo.state_dict().items()}}, export_dir / "vision_stripped_fp16.pt")
    bundles["vision_stripped_fp16_bytes"] = (export_dir / "vision_stripped_fp16.pt").stat().st_size

    rng = np.random.default_rng(20261114)
    syn_wave = rng.normal(0.0, 0.05, size=(16000,)).astype(np.float32)
    ax = torch.from_numpy(rng.normal(0.0, 1.0, size=(1, 1, 64, 61)).astype(np.float32))
    with torch.no_grad():
        a_eager = acnn(ax)
        a_ts = torch.jit.trace(acnn, ax)
        a_ts_path = export_dir / "audio_v3_cnn.torchscript"
        a_ts.save(str(a_ts_path))
        a_diff = float((a_eager - a_ts(ax)).abs().max())
        bundles["audio_torchscript_bytes"] = a_ts_path.stat().st_size
        bundles["audio_torchscript_max_abs_diff"] = round(a_diff, 8)

        vision_inputs: dict[int, tuple[torch.Tensor, torch.jit.ScriptModule]] = {}
        for sz in imgszs:
            xt = torch.from_numpy(rng.normal(0.5, 0.1, size=(1, 3, sz, sz)).astype(np.float32))
            v_eager = wrap(xt)
            v_ts = torch.jit.trace(wrap, xt)
            v_ts_path = export_dir / f"yolov8n_{sz}.torchscript"
            v_ts.save(str(v_ts_path))
            v_diff = float((v_eager - v_ts(xt)).abs().max())
            bundles[f"vision_{sz}_torchscript_bytes"] = v_ts_path.stat().st_size
            bundles[f"vision_{sz}_torchscript_max_abs_diff"] = round(v_diff, 8)
            vision_inputs[sz] = (xt, v_ts)

    scaling_by_threads: dict[str, Any] = {}
    prev_threads = torch.get_num_threads()
    try:
        for n_t in thread_counts:
            torch.set_num_threads(n_t)
            entry: dict[str, Any] = {
                "log_mel_ms": _time_fn(
                    lambda: compute_log_mel_spectrogram(syn_wave, sample_rate=16000, log_scale="natural"),
                    warmup=4,
                    iters=max(iters, 20),
                ),
                "audio_ts_ms": _time_fn(lambda: a_ts(ax), warmup=4, iters=max(iters, 20)),
            }
            for sz, (xt, v_ts) in vision_inputs.items():
                entry[f"vision_{sz}_ts_ms"] = _time_fn(
                    lambda m=v_ts, inp=xt: m(inp), warmup=3, iters=iters
                )
            scaling_by_threads[f"threads_{n_t}"] = entry
    finally:
        torch.set_num_threads(prev_threads)

    ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss_mb = ru / (1024.0 * 1024.0) if sys.platform == "darwin" else ru / 1024.0
    hw = detect_hardware_target()
    return {
        "schema_version": "rpi-edge-benchmark/1.0",
        "input_classification": "SYNTHETIC_ONLY",
        "hardware": hw,
        "physical_raspberry_pi_tested": hw["is_physical_raspberry_pi"],
        "peak_process_rss_mb": round(peak_rss_mb, 2),
        "exported_bundles": bundles,
        "thread_scaling_ms": scaling_by_threads,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--export-dir", type=Path, default=None)
    ap.add_argument("--iters", type=int, default=12)
    args = ap.parse_args()

    out = args.output.resolve()
    root = args.root.resolve()
    for protected in ("data", "configs", "models", "experiments", "src", "tests"):
        guard = (root / protected).resolve()
        if out == guard or guard in out.parents:
            raise SystemExit(f"Refusing to write output inside protected tree {protected}/")

    with tempfile.TemporaryDirectory(prefix="tga_rpi_bundle_") as tmp_dir:
        exp_dir = args.export_dir.resolve() if args.export_dir else Path(tmp_dir)
        report = run_edge_package_and_benchmark(root, export_dir=exp_dir, iters=args.iters)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "OK", "output": str(out), "physical_raspberry_pi_tested": report["physical_raspberry_pi_tested"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
