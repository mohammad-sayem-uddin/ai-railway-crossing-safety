"""Command for the reproducible Phase 14 benchmark report.

    python -m railway_detection benchmark run --output report.json [options]

Workload: deterministic synthetic multimodal evidence replayed through the frozen decision
engine (``frame_assembly`` then ``decision_replay`` per synthetic event), optionally plus
the frozen vision checkpoint on seeded noise split into preprocess/inference/postprocess.
Everything is classified ``synthetic``. The output path may not be inside an evidence,
config, model or results tree.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from railway_detection.experiments.frozen_config import load_frozen_config
from railway_detection.fusion.collector import MultimodalEvidenceCollector
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.optimization.benchmark import BenchmarkProtocol, BenchmarkProtocolError
from railway_detection.optimization.benchmark_suite import (
    InputDescription,
    run_staged_benchmark,
    vision_inference_stage_timings,
)
from railway_detection.simulation.runner import EventSimulationRunner

PROTECTED_OUTPUT_TREES = (
    "data",
    "configs",
    "models",
    "experiments",
    "results",
    "docs",
    "src",
    "tests",
)


def synthetic_events(count: int = 3) -> list[dict[str, Any]]:
    """Deterministic synthetic evidence streams (a train-like pass of varying length)."""
    events = []
    for index in range(count):
        length_s = 20.0 + 10.0 * index
        times = [round(0.2 * i, 1) for i in range(int(length_s / 0.2) + 1)]
        front, back = [], []
        for t in times:
            on_front = 2.0 <= t < length_s * 0.6
            on_back = length_s * 0.3 <= t < length_s * 0.9
            front.append(
                EvidenceRecord(
                    timestamp_s=t, source_id="camera_1", modality=Modality.VISION, available=True,
                    detections=(Detection(label="front", confidence=0.9),) if on_front else (),
                    metadata={"frame_index": len(front)},
                )
            )
            back.append(
                EvidenceRecord(
                    timestamp_s=t, source_id="camera_2", modality=Modality.VISION, available=True,
                    detections=(Detection(label="rear", confidence=0.9),) if on_back else (),
                    metadata={"frame_index": len(back)},
                )
            )
        events.append({"event": f"synthetic_{index}", "front": front, "back": back,
                       "duration_s": length_s})
    return events


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output", required=True, help="Report path (not inside a repo tree).")
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--vision-model", action="store_true",
                        help="Also time the frozen vision checkpoint on seeded noise.")
    parser.add_argument("--target-machine", default=None)
    parser.add_argument("--target-system", default=None)
    parser.add_argument("--target-cpu-model", default=None)
    parser.add_argument("--acceptance-statistic", default=None)
    parser.add_argument("--acceptance-limit-ms", type=float, default=None)
    parser.add_argument("--acceptance-doc", default=None,
                        help="Repository path of the document that defines the criterion.")
    parser.add_argument("--repository-root", default=".")


def _check_output(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    for name in PROTECTED_OUTPUT_TREES:
        guard = (root / name).resolve()
        if resolved == guard or guard in resolved.parents:
            raise BenchmarkProtocolError(f"refusing to write the report inside {name}/")
    return resolved


def run(args: argparse.Namespace) -> int:
    root = Path(args.repository_root).resolve()
    destination = _check_output(Path(args.output), root)
    target = {
        key: value
        for key, value in (
            ("machine", args.target_machine),
            ("system", args.target_system),
            ("cpu_model", args.target_cpu_model),
        )
        if value is not None
    } or None
    criterion = None
    if args.acceptance_statistic or args.acceptance_limit_ms or args.acceptance_doc:
        criterion = {
            "statistic": args.acceptance_statistic,
            "limit_ms": args.acceptance_limit_ms,
            "documented_in": args.acceptance_doc,
        }
    protocol = BenchmarkProtocol(
        warmup_iterations=args.warmup,
        measured_iterations=args.iterations,
        repetitions=args.repetitions,
        target_platform=target,
        workload_label="synthetic_event_replay_through_frozen_decision_engine",
        acceptance_criterion=criterion,
    )
    config = load_frozen_config(root / "configs/frozen_experiment_v1.yaml")
    events = synthetic_events()
    runner = EventSimulationRunner(config=config)

    def assemble(event: dict[str, Any]) -> dict[str, Any]:
        collector = MultimodalEvidenceCollector(window_tolerance_s=0.25)
        collector.add_evidence_batch(event["front"])  # single camera: no cross-camera fusion
        frames = collector.generate_frames_from_history(
            0.0, event["duration_s"], stride_s=config.timing.tick_s
        )
        return {"event": event["event"], "frames": frames}

    def replay(assembled: dict[str, Any]) -> dict[str, Any]:
        result = runner.run_frames(
            frames=list(assembled["frames"]), event_id=assembled["event"],
            scenario_name="phase14_benchmark",
        )
        return {
            "event": assembled["event"],
            "frames": len(assembled["frames"]),
            "final_state": result.steps[-1].crossing_state if result.steps else None,
            "closed_duration_s": round(result.closed_duration_s, 6),
        }

    report = run_staged_benchmark(
        "synthetic_event_replay",
        [("frame_assembly", assemble), ("decision_replay", replay)],
        events,
        protocol,
        InputDescription("synthetic", "deterministic synthetic evidence; not railway footage"),
        root=root,
    )
    total_frames = sum(len(assemble(e)["frames"]) for e in events)
    replay_mean_ms = report["stage_latency_ms"]["decision_replay"]["mean_ms"]
    passes = protocol.repetitions * protocol.measured_iterations
    wall_s = sum(report["repetition_wall_ms"]) / 1000.0
    report["derived_per_frame"] = {
        "frames_per_pass": total_frames,
        "throughput_frames_per_s": (total_frames * passes / wall_s) if wall_s > 0 else None,
        "decision_replay_mean_ms_per_frame": replay_mean_ms * len(events) / total_frames,
        "note": "mean per-event replay time divided by frames per event; not a per-frame sample",
    }
    if args.vision_model:
        report["vision_model_workload"] = vision_inference_stage_timings(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Do not leave a truncated report if the process is interrupted while
    # serializing/writing.  The temporary name stays beside the destination so
    # replace is atomic on the same filesystem.
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    print(json.dumps({
        "report": str(destination),
        "item_total_ms": report["stage_latency_ms"]["item_total"],
        "throughput_items_per_s": report["throughput_items_per_s"],
        "fingerprints_verified": report["fingerprints_verified"],
        "is_target_hardware_evidence": report["is_target_hardware_evidence"],
        "real_time_claim_permitted": report["real_time_claim_permitted"],
    }, indent=2, sort_keys=True))
    return 0 if report["fingerprints_verified"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
