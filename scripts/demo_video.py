#!/usr/bin/env python3
"""CLI driver for the standalone Railway Train Detection Video Demo.

Usage:
    python scripts/demo_video.py
    python scripts/demo_video.py --input path/to/video.mp4
    python scripts/demo_video.py --input video.mp4 --model path/to/best.pt --device mps
    python scripts/demo_video.py --preview --temporal
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from railway_detection.config.exceptions import ConfigError  # noqa: E402
from railway_detection.demo.video_demo import (  # noqa: E402
    create_output_directory,
    process_video,
    render_terminal_progress,
    resolve_device,
    select_input_video,
)
from railway_detection.utils.logging import configure_logging, get_logger  # noqa: E402

logger = get_logger("demo.cli")

DEFAULT_MODEL_PATH = PROJECT_ROOT / "experiments/vision/39f402dfe460/checkpoints/weights/best.pt"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="demo_video",
        description="AI Railway Crossing Safety — Video Inference & Demonstration Tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="input_video",
        default=None,
        help="Path to input video. If omitted, opens native picker or prompt.",
    )
    parser.add_argument(
        "-m",
        "--model",
        dest="model_path",
        default=str(DEFAULT_MODEL_PATH),
        help="Path to trained YOLO weights file (.pt).",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        dest="output_dir",
        default=None,
        help="Base directory for output runs (defaults to outputs/video_tests/<name>_<timestamp>).",
    )
    parser.add_argument(
        "-c",
        "--conf",
        dest="conf_threshold",
        type=float,
        default=0.25,
        help="Confidence threshold for bounding box detection.",
    )
    parser.add_argument(
        "--iou",
        dest="iou_threshold",
        type=float,
        default=0.45,
        help="NMS IoU threshold.",
    )
    parser.add_argument(
        "-d",
        "--device",
        dest="device",
        choices=["auto", "mps", "cuda", "cpu"],
        default="auto",
        help="Inference compute device.",
    )
    parser.add_argument(
        "-p",
        "--preview",
        action="store_true",
        help="Show live graphical preview window during processing (press Q to stop early).",
    )
    parser.add_argument(
        "-t",
        "--temporal",
        action="store_true",
        help="Apply optional temporal evidence smoothing buffer across consecutive frames.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        input_video_path = select_input_video(args.input_video)
    except ConfigError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        return 1

    model_path = Path(args.model_path).expanduser().resolve()
    if not model_path.exists():
        print(f"\nError: Model checkpoint not found at: {model_path}", file=sys.stderr)
        return 1

    if args.output_dir:
        base_out = Path(args.output_dir).expanduser()
    else:
        base_out = PROJECT_ROOT / "outputs/video_tests"
    run_output_dir = create_output_directory(input_video_path, base_output_dir=base_out)

    resolved_dev = resolve_device(args.device)

    print("\n" + "=" * 60)
    print("AI RAILWAY CROSSING SAFETY — VIDEO INFERENCE DEMO")
    print("=" * 60)
    print(f"Input Video : {input_video_path.name}")
    print(f"Full Path   : {input_video_path}")
    print(f"Model       : {model_path.name}")
    print(f"Model Path  : {model_path}")
    print(f"Device      : {resolved_dev.upper()}")
    print(f"Conf / IoU  : {args.conf_threshold} / {args.iou_threshold}")
    print(f"Temporal    : {'Enabled' if args.temporal else 'Disabled'}")
    print(f"Preview     : {'Enabled' if args.preview else 'Disabled'}")
    print(f"Output Dir  : {run_output_dir}")
    print("=" * 60)
    print("Processing video frames...\n")

    def on_progress(current: int, total: int, counts: dict[str, int]) -> None:
        render_terminal_progress(current, total, counts)

    try:
        summary = process_video(
            input_path=input_video_path,
            output_dir=run_output_dir,
            model_path=model_path,
            conf_threshold=args.conf_threshold,
            iou_threshold=args.iou_threshold,
            device=resolved_dev,
            live_preview=args.preview,
            temporal_smoothing=args.temporal,
            progress_callback=on_progress,
        )
    except ConfigError as exc:
        print(f"\n\nProcessing Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n\nProcessing cancelled by user.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"\n\nUnexpected error during processing: {exc}", file=sys.stderr)
        return 1

    dur_str = f"{summary.processing_duration_s:.2f}s"
    print("\n\n" + "=" * 60)
    print("VIDEO PROCESSING COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(f"Processed Video : {summary.output_video}")
    print(f"Markdown Summary: {run_output_dir / 'summary.md'}")
    print(f"JSON Summary    : {run_output_dir / 'summary.json'}")
    print("-" * 60)
    print(f"Frames Processed: {summary.processed_frames} / {summary.total_frames}")
    print(f"Inference Speed : {summary.inference_fps:.2f} FPS (Duration: {dur_str})")
    print(f"Total Detections: {summary.total_detections}")
    print(f"Detections Rate : {summary.frames_with_detections_pct:.1f}% of frames with trains")
    print("Class Breakdown :")
    for cls_name in ("front", "rear", "side"):
        st = summary.class_stats.get(cls_name)
        if st:
            c_avg = f"{st.avg_confidence:.2f}"
            c_max = f"{st.max_confidence:.2f}"
            print(
                f"  - {cls_name.upper():5s}: {st.total_detections:4d} detections across "
                f"{st.frames_with_class:4d} frames (avg conf: {c_avg}, max: {c_max})"
            )
    print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
