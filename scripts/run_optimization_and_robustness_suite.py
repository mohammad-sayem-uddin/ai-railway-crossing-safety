#!/usr/bin/env python
"""Run Exp O (audio hysteresis/calibration), Exp P (CPU/edge profile), and Exp Q (stress suite).

Outputs reproducible JSON and CSV files under ``results/exploratory_v2/optimization_and_stress/``.
Writes temporary stripped/TorchScript models only under ``/tmp/`` and never opens raw media.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from ultralytics import YOLO

from railway_detection.audio.features import compute_log_mel_spectrogram
from railway_detection.audio.model import CompactTrainHornCNN
from railway_detection.experiments.optimization_and_stress import (
    compute_event_triggered_duty_cycle,
    evaluate_acoustic_hysteresis_and_calibration,
    evaluate_weather_and_interlocking_stress,
)
from railway_detection.fusion.collector import MultimodalEvidenceCollector
from railway_detection.fusion.decision_engine_v3_four_layer import (
    MultimodalDecisionEngineV3FourLayer,
)
from railway_detection.fusion.evidence import (
    Detection,
    EvidenceRecord,
    Modality,
    OccupancyEvidence,
    OccupancyState,
)
from railway_detection.simulation.runner import EventSimulationRunner

ROOT = Path(__file__).resolve().parent.parent


class _YoloOutputWrapper(torch.nn.Module):
    """Wrap Ultralytics DetectionModel to return the primary prediction tensor for TorchScript."""

    def __init__(self, model: torch.nn.Module) -> None:
        super().__init__()
        self.model = model

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.model(x)
        return out[0] if isinstance(out, (tuple, list)) else out


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _latency_stats(samples_s: list[float]) -> dict[str, float]:
    arr = np.asarray(samples_s, dtype=np.float64) * 1000.0
    mean_ms = float(np.mean(arr))
    return {
        "n_iters": len(samples_s),
        "mean_ms": round(mean_ms, 3),
        "p50_ms": round(float(np.percentile(arr, 50)), 3),
        "p95_ms": round(float(np.percentile(arr, 95)), 3),
        "p99_ms": round(float(np.percentile(arr, 99)), 3),
        "min_ms": round(float(np.min(arr)), 3),
        "max_ms": round(float(np.max(arr)), 3),
        "fps_equivalent": round(1000.0 / mean_ms, 2) if mean_ms > 0 else 0.0,
    }


def _benchmark_fn(fn, *, warmup: int = 8, iters: int = 30) -> dict[str, float]:
    for _ in range(warmup):
        fn()
    times: list[float] = []
    for _ in range(iters):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return _latency_stats(times)


def _load_exp_o_event_records(root: Path) -> list[dict[str, Any]]:
    # Read event-level audio scores from ALL_AUDIO_WINDOW_SCORES.csv + m3 caches for no_train/engine
    scores_csv = root / "docs/generated/professor_evidence/mission44/ALL_AUDIO_WINDOW_SCORES.csv"
    by_event: dict[str, dict[str, Any]] = {}
    with scores_csv.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            ev = row["event"]
            rec = by_event.setdefault(
                ev,
                {
                    "event_id": ev,
                    "cohort": row["cohort"],
                    "adopted_status": row["adopted_event_horn_status"],
                    "binary_label": 1 if row["adopted_event_horn_status"] == "present" else (0 if row["adopted_event_horn_status"] == "absent_observed" else None),
                    "scores": [],
                },
            )
            rec["scores"].append(float(row["score"]))

    m3 = json.loads((root / "data/manifests/m3_multimodal_replay_manifest.json").read_text(encoding="utf-8"))
    for entry in m3["events"]:
        ev = entry["event_id"]
        if ev in by_event:
            continue
        cache_path = root / entry["audio_cache_path"]
        scores = [
            float(json.loads(line)["horn_confidence"])
            for line in cache_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        by_event[ev] = {
            "event_id": ev,
            "cohort": ev.split("/", 1)[0],
            "adopted_status": "external_control",
            "binary_label": None,
            "scores": scores,
        }
    return [by_event[k] for k in sorted(by_event)]


def _host_cpu_brand() -> str:
    try:
        return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    except Exception:
        return platform.processor() or platform.machine()


def _run_exp_p_cpu_benchmark(root: Path, *, num_threads: int = 4) -> dict[str, Any]:
    prev_threads = torch.get_num_threads()
    torch.set_num_threads(num_threads)
    try:
        vision_ckpt_path = root / "experiments/vision/39f402dfe460/checkpoints/weights/best.pt"
        audio_ckpt_path = root / "experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt"

        yolo = YOLO(str(vision_ckpt_path))
        inner_yolo = yolo.model.float().eval()
        yolo_params = sum(p.numel() for p in inner_yolo.parameters())

        ac_ckpt = torch.load(audio_ckpt_path, map_location="cpu", weights_only=False)
        acnn = CompactTrainHornCNN().float().eval()
        acnn.load_state_dict(ac_ckpt["model_state_dict"])
        audio_params = sum(p.numel() for p in acnn.parameters())

        # Fixed-seed synthetic inputs (strictly SYNTHETIC_ONLY)
        rng = np.random.default_rng(42)
        syn_wave = rng.normal(0.0, 0.05, size=(16000,)).astype(np.float32)
        syn_img_640 = rng.integers(0, 255, size=(640, 640, 3), dtype=np.uint8)
        syn_img_416 = rng.integers(0, 255, size=(416, 416, 3), dtype=np.uint8)

        size_audit: dict[str, Any] = {
            "vision_raw_unstripped_bytes": vision_ckpt_path.stat().st_size,
            "audio_raw_bytes": audio_ckpt_path.stat().st_size,
        }
        vision_benchmarks: dict[str, Any] = {}
        audio_benchmarks: dict[str, Any] = {}

        with tempfile.TemporaryDirectory(prefix="tga_opt_") as tmp_dir:
            tmp = Path(tmp_dir)
            # Save stripped checkpoints into /tmp only
            torch.save({"model": {k: v.half() for k, v in inner_yolo.state_dict().items()}}, tmp / "v_fp16.pt")
            torch.save({"model": {k: v.float() for k, v in inner_yolo.state_dict().items()}}, tmp / "v_fp32.pt")
            size_audit["vision_stripped_fp16_bytes"] = (tmp / "v_fp16.pt").stat().st_size
            size_audit["vision_stripped_fp32_bytes"] = (tmp / "v_fp32.pt").stat().st_size
            size_audit["vision_strip_reduction_pct"] = round(
                (1.0 - size_audit["vision_stripped_fp16_bytes"] / size_audit["vision_raw_unstripped_bytes"]) * 100.0,
                2,
            )

            # Benchmark YOLOv8n backbone/head forward across resolutions + TorchScript
            for sz in (640, 416, 320):
                xt = torch.from_numpy(rng.normal(0.5, 0.1, size=(1, 3, sz, sz)).astype(np.float32))
                wrap = _YoloOutputWrapper(inner_yolo).eval()
                with torch.no_grad():
                    eager_out = wrap(xt)
                    stats_eager = _benchmark_fn(lambda: wrap(xt), warmup=5, iters=20)
                    traced = torch.jit.trace(wrap, xt)
                    ts_path = tmp / f"v_{sz}.torchscript"
                    traced.save(str(ts_path))
                    trace_out = traced(xt)
                    stats_ts = _benchmark_fn(lambda: traced(xt), warmup=5, iters=20)
                vision_benchmarks[f"yolov8n_forward_{sz}_fp32"] = stats_eager
                vision_benchmarks[f"yolov8n_torchscript_{sz}_fp32"] = {
                    **stats_ts,
                    "torchscript_bytes": ts_path.stat().st_size,
                    "max_abs_diff_vs_eager": float((eager_out - trace_out).abs().max()),
                }

            # End-to-end Ultralytics YOLO.predict() pipeline (preprocess + CNN + NMS)
            vision_benchmarks["yolo_predict_e2e_640"] = _benchmark_fn(
                lambda: yolo.predict(syn_img_640, imgsz=640, device="cpu", verbose=False),
                warmup=4,
                iters=15,
            )
            vision_benchmarks["yolo_predict_e2e_416"] = _benchmark_fn(
                lambda: yolo.predict(syn_img_416, imgsz=416, device="cpu", verbose=False),
                warmup=4,
                iters=15,
            )

            # Audio log-Mel + CNN Eager / TorchScript / Dynamic INT8
            mel_stats = _benchmark_fn(
                lambda: compute_log_mel_spectrogram(syn_wave, sample_rate=16000, log_scale="natural"),
                warmup=10,
                iters=60,
            )
            ax = torch.randn(1, 1, 64, 61)
            with torch.no_grad():
                ay_eager = acnn(ax)
                a_eager_stats = _benchmark_fn(lambda: acnn(ax), warmup=10, iters=80)
                a_ts = torch.jit.trace(acnn, ax)
                a_ts_path = tmp / "audio_v3.torchscript"
                a_ts.save(str(a_ts_path))
                ay_ts = a_ts(ax)
                a_ts_stats = _benchmark_fn(lambda: a_ts(ax), warmup=10, iters=80)
                torch.backends.quantized.engine = "qnnpack"
                a_q = torch.ao.quantization.quantize_dynamic(acnn, {torch.nn.Linear}, dtype=torch.qint8)
                a_q_path = tmp / "audio_v3_dyn_int8.pt"
                torch.save(a_q.state_dict(), a_q_path)
                ay_q = a_q(ax)
                a_q_stats = _benchmark_fn(lambda: a_q(ax), warmup=10, iters=80)
            audio_benchmarks = {
                "log_mel_1s_numpy": mel_stats,
                "cnn_eager_fp32": a_eager_stats,
                "cnn_torchscript_fp32": {
                    **a_ts_stats,
                    "torchscript_bytes": a_ts_path.stat().st_size,
                    "max_abs_diff_vs_eager": float((ay_eager - ay_ts).abs().max()),
                },
                "cnn_dynamic_int8_linear": {
                    **a_q_stats,
                    "state_dict_bytes": a_q_path.stat().st_size,
                    "max_abs_diff_vs_eager": float((ay_eager - ay_q).abs().max()),
                },
            }

        # V3 Four-Layer Collector + Decision Engine + Gate step latency on synthetic 121-tick episode
        recs = [
            EvidenceRecord(round(i * 0.2, 3), "camera_1", Modality.VISION, True, [Detection("front", 0.9)] if 1.0 <= i * 0.2 <= 5.0 else [])
            for i in range(121)
        ] + [
            EvidenceRecord(round(i * 0.2, 3), "camera_2", Modality.VISION, True, [Detection("rear", 0.9)] if 11.2 <= i * 0.2 <= 12.6 else [])
            for i in range(121)
        ]
        occs = [
            OccupancyEvidence(round(i * 0.2, 3), "occ_sensor_1", OccupancyState.OCCUPIED if 4.0 <= i * 0.2 <= 12.8 else OccupancyState.CLEAR, True, 0.95)
            for i in range(121)
        ]
        col = MultimodalEvidenceCollector(window_tolerance_s=0.5, event_id="bench", allow_stale_detection_backfill=False)
        col.add_evidence_batch(recs)
        for o in occs:
            col.add_occupancy(o)
        frames = col.generate_frames_from_history(0.0, 24.0, stride_s=0.2)

        def _run_episode() -> None:
            runner = EventSimulationRunner(decision_engine=MultimodalDecisionEngineV3FourLayer())
            runner.run_frames(frames, event_id="bench", scenario_name="bench")

        ep_stats = _benchmark_fn(_run_episode, warmup=5, iters=30)
        tick_mean_ms = ep_stats["mean_ms"] / len(frames)

        # Peak RSS (macOS ru_maxrss is in bytes; Linux is KiB)
        ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak_rss_mb = ru / (1024.0 * 1024.0) if sys.platform == "darwin" else ru / 1024.0

        # Analytical Event-Triggered Duty Cycle based on measured YOLO e2e 640 & 416 + Audio total
        audio_total_ms = audio_benchmarks["log_mel_1s_numpy"]["mean_ms"] + audio_benchmarks["cnn_torchscript_fp32"]["mean_ms"]
        duty_640 = compute_event_triggered_duty_cycle(
            vision_benchmarks["yolo_predict_e2e_640"]["mean_ms"],
            audio_total_ms,
        )
        duty_416 = compute_event_triggered_duty_cycle(
            vision_benchmarks["yolo_predict_e2e_416"]["mean_ms"],
            audio_total_ms,
        )

        return {
            "schema_version": "cpu-edge-benchmark/1.0",
            "input_classification": "SYNTHETIC_ONLY",
            "host_environment": {
                "platform": platform.platform(),
                "machine": platform.machine(),
                "cpu_brand": _host_cpu_brand(),
                "python_version": platform.python_version(),
                "torch_version": torch.__version__,
                "torch_num_threads": num_threads,
                "physical_raspberry_pi_tested": False,
                "peak_process_rss_mb": round(peak_rss_mb, 2),
            },
            "model_parameters": {
                "yolov8n_params": yolo_params,
                "audio_v3_params": audio_params,
            },
            "checkpoint_size_audit": size_audit,
            "vision_cpu_benchmarks_ms": vision_benchmarks,
            "audio_cpu_benchmarks_ms": audio_benchmarks,
            "v3_fsm_closed_loop_121_ticks_ms": {
                **ep_stats,
                "per_tick_mean_ms": round(tick_mean_ms, 4),
            },
            "event_triggered_duty_cycle_640": duty_640,
            "event_triggered_duty_cycle_416": duty_416,
        }
    finally:
        torch.set_num_threads(prev_threads)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--threads", type=int, default=4)
    args = ap.parse_args()
    root: Path = args.root
    out_dir = root / "results/exploratory_v2/optimization_and_stress"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Exp O
    exp_o_records = _load_exp_o_event_records(root)
    exp_o = evaluate_acoustic_hysteresis_and_calibration(exp_o_records)
    _write_json(out_dir / "exp_o_audio_calibration_hysteresis.json", exp_o)
    _write_csv(out_dir / "exp_o_hysteresis_grid.csv", exp_o["hysteresis_grid"])
    _write_csv(out_dir / "exp_o_event_run_lengths.csv", exp_o["event_run_summaries"])

    # Exp P
    exp_p = _run_exp_p_cpu_benchmark(root, num_threads=args.threads)
    _write_json(out_dir / "exp_p_cpu_edge_benchmark.json", exp_p)

    # Exp Q
    exp_q = evaluate_weather_and_interlocking_stress()
    _write_json(out_dir / "exp_q_weather_and_interlocking_stress.json", exp_q)
    _write_csv(out_dir / "exp_q_weather_dropout_grid.csv", exp_q["weather_dropout_grid"])

    print(
        json.dumps(
            {
                "status": "OK",
                "output_dir": str(out_dir),
                "exp_o_best_f1": exp_o["best_f1_point"],
                "exp_p_yolo_e2e_640_ms": exp_p["vision_cpu_benchmarks_ms"]["yolo_predict_e2e_640"]["mean_ms"],
                "exp_p_yolo_e2e_416_ms": exp_p["vision_cpu_benchmarks_ms"]["yolo_predict_e2e_416"]["mean_ms"],
                "exp_p_audio_cnn_ts_ms": exp_p["audio_cpu_benchmarks_ms"]["cnn_torchscript_fp32"]["mean_ms"],
                "exp_p_fsm_tick_ms": exp_p["v3_fsm_closed_loop_121_ticks_ms"]["per_tick_mean_ms"],
                "exp_p_peak_rss_mb": exp_p["host_environment"]["peak_process_rss_mb"],
                "exp_q_runs": exp_q["total_grid_runs"],
                "exp_q_unsafe_openings": exp_q["total_unsafe_openings"],
                "exp_q_illegal_transitions": exp_q["total_illegal_transitions"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
