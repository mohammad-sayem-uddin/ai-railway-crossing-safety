"""Standalone video inference and testing tool for railway train detection.

Performs frame-by-frame inference using trained YOLO models, annotates detection
bounding boxes with canonical class labels (front, rear, side), records complete
per-frame detection statistics, and generates processed MP4 output and summaries.

This tool is strictly an engineering visual verification and demonstration utility.
It does not claim real-world safety certification or crossing-independent generalization.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from railway_detection.config.exceptions import ConfigError
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.utils.logging import get_logger
from railway_detection.vision.temporal import TemporalConfig, TemporalEvidenceBuffer

logger = get_logger("demo.video")

CANONICAL_CLASSES = ["front", "rear", "side"]
SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}

# Visual annotation color palette in BGR format for OpenCV
CLASS_COLORS_BGR = {
    "front": (0, 140, 255),    # Vibrant Amber / Orange for approach
    "rear": (180, 0, 220),     # Magenta / Purple for departure
    "side": (255, 180, 0),     # Azure / Sky Blue for crossing passage
}
DEFAULT_BOX_COLOR = (0, 255, 0)


@dataclass(frozen=True)
class FrameDetection:
    """Individual frame-level detection bounding box."""

    label: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]
    temporal_confirmed: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 4),
            "bbox_xyxy": [round(v, 2) for v in self.bbox_xyxy],
            "temporal_confirmed": self.temporal_confirmed,
        }


@dataclass
class ClassStats:
    """Class-wise detection statistics across a video."""

    frames_with_class: int = 0
    total_detections: int = 0
    confidences: list[float] = field(default_factory=list)

    @property
    def avg_confidence(self) -> float:
        if not self.confidences:
            return 0.0
        return float(sum(self.confidences) / len(self.confidences))

    @property
    def max_confidence(self) -> float:
        if not self.confidences:
            return 0.0
        return float(max(self.confidences))

    def to_dict(self) -> dict[str, Any]:
        return {
            "frames_with_class": self.frames_with_class,
            "total_detections": self.total_detections,
            "avg_confidence": round(self.avg_confidence, 4),
            "max_confidence": round(self.max_confidence, 4),
        }


@dataclass
class VideoDemoSummary:
    """Complete summary of video processing and inference statistics."""

    input_video: str
    output_video: str
    model_path: str
    model_name: str
    device_used: str
    width: int
    height: int
    fps: float
    total_frames: int
    processed_frames: int
    processing_duration_s: float
    inference_fps: float
    total_detections: int
    confidence_threshold: float
    iou_threshold: float
    temporal_smoothing: bool
    class_stats: dict[str, ClassStats] = field(default_factory=dict)
    frames_with_no_detections: int = 0

    @property
    def frames_with_detections(self) -> int:
        return max(0, self.processed_frames - self.frames_with_no_detections)

    @property
    def frames_with_detections_pct(self) -> float:
        if self.processed_frames == 0:
            return 0.0
        return float((self.frames_with_detections / self.processed_frames) * 100.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "disclaimer": (
                "These results are inference statistics only and do not represent "
                "ground-truth evaluation metrics."
            ),
            "input_video": self.input_video,
            "output_video": self.output_video,
            "model_path": self.model_path,
            "model_name": self.model_name,
            "device_used": self.device_used,
            "video_metadata": {
                "width": self.width,
                "height": self.height,
                "native_fps": round(self.fps, 2),
                "total_frames": self.total_frames,
                "processed_frames": self.processed_frames,
            },
            "performance": {
                "duration_seconds": round(self.processing_duration_s, 2),
                "average_inference_fps": round(self.inference_fps, 2),
                "confidence_threshold": self.confidence_threshold,
                "iou_threshold": self.iou_threshold,
                "temporal_smoothing": self.temporal_smoothing,
            },
            "detection_overview": {
                "total_detections": self.total_detections,
                "frames_with_detections": self.frames_with_detections,
                "frames_with_no_detections": self.frames_with_no_detections,
                "detection_frame_percentage": round(self.frames_with_detections_pct, 2),
            },
            "class_statistics": {
                cls_name: self.class_stats[cls_name].to_dict()
                for cls_name in CANONICAL_CLASSES
                if cls_name in self.class_stats
            },
        }

    def to_markdown(self) -> str:
        lines = [
            "# Railway Crossing Video Inference Summary",
            "",
            "> **Research & Validation Notice**  ",
            (
                "> These results are inference statistics only and do not represent "
                "ground-truth evaluation metrics."
            ),
            "",
            "## 1. Video & Environment Metadata",
            f"- **Input Video:** `{self.input_video}`",
            f"- **Output Video:** `{self.output_video}`",
            f"- **Model Path:** `{self.model_path}`",
            f"- **Model Name:** `{self.model_name}`",
            f"- **Compute Device Used:** `{self.device_used}`",
            f"- **Resolution:** {self.width} × {self.height}",
            f"- **Native Video FPS:** {self.fps:.2f}",
            f"- **Total Frames in Video:** {self.total_frames}",
            f"- **Successfully Processed Frames:** {self.processed_frames}",
            f"- **Processing Duration:** {self.processing_duration_s:.2f} seconds",
            f"- **Average Inference Throughput:** {self.inference_fps:.2f} FPS",
            f"- **Confidence Threshold:** {self.confidence_threshold}",
            f"- **IoU Threshold:** {self.iou_threshold}",
            f"- **Temporal Smoothing:** `{'Enabled' if self.temporal_smoothing else 'Disabled'}`",
            "",
            "## 2. Detection Overview",
            f"- **Total Detected Instances:** **{self.total_detections}**",
            (
                "- **Frames with At Least One Detection:** "
                f"{self.frames_with_detections} ({self.frames_with_detections_pct:.1f}%)"
            ),
            f"- **Frames with No Detection:** {self.frames_with_no_detections}",
            "",
            "## 3. Class-Wise Detection Statistics",
            "",
            "| Class | Frames Present | Total Detections | Avg Confidence | Max Confidence |",
            "|:---:|:---:|:---:|:---:|:---:|",
        ]
        for cls_name in CANONICAL_CLASSES:
            stats = self.class_stats.get(cls_name, ClassStats())
            lines.append(
                f"| **{cls_name.upper()}** | {stats.frames_with_class} | "
                f"{stats.total_detections} | {stats.avg_confidence:.4f} | "
                f"{stats.max_confidence:.4f} |"
            )
        lines.extend([
            "",
            "## 4. Audio Preservation Note",
            (
                "Processed output video is encoded via OpenCV MP4 container. Audio tracks "
                "(if present in source) are omitted during visual frame reconstruction."
            ),
            "",
        ])
        return "\n".join(lines)


def normalize_class_name(raw_name: str | int) -> str:
    """Normalize raw class labels or IDs into canonical class names.

    Maps 'rare' (Roboflow typo) or index 1 to canonical 'rear'.
    0 -> 'front', 1 -> 'rear', 2 -> 'side'.
    """
    if isinstance(raw_name, int):
        mapping = {0: "front", 1: "rear", 2: "side"}
        return mapping.get(raw_name, str(raw_name))

    name = str(raw_name).strip().lower()
    if name in ("rare", "1"):
        return "rear"
    if name in ("0", "front"):
        return "front"
    if name in ("2", "side"):
        return "side"
    return name


def resolve_device(device_arg: str = "auto") -> str:
    """Resolve target compute device with hardware fallback."""
    dev = device_arg.strip().lower()
    if dev in ("auto", ""):
        try:
            import torch

            if torch.backends.mps.is_available() and torch.backends.mps.is_built():
                return "mps"
            if torch.cuda.is_available():
                return "cuda"
        except Exception:
            pass
        return "cpu"

    if dev == "mps":
        try:
            import torch

            if not (torch.backends.mps.is_available() and torch.backends.mps.is_built()):
                logger.warning("MPS device requested but unavailable; falling back to CPU")
                return "cpu"
        except Exception:
            return "cpu"
        return "mps"

    if dev == "cuda":
        try:
            import torch

            if not torch.cuda.is_available():
                logger.warning("CUDA device requested but unavailable; falling back to CPU")
                return "cpu"
        except Exception:
            return "cpu"
        return "cuda"

    return "cpu"


def create_output_directory(
    input_path: Path, base_output_dir: Path = Path("outputs/video_tests")
) -> Path:
    """Generate a unique timestamped output directory for this test run."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem.replace(" ", "_")
    output_dir = base_output_dir / f"{stem}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def select_input_video(cli_input: str | None = None) -> Path:
    """Obtain a single valid video file path via CLI argument, native dialog, or prompt."""
    if cli_input:
        path = Path(cli_input).expanduser().resolve()
        if not path.exists():
            raise ConfigError(f"Specified input video does not exist: {path}")
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise ConfigError(f"Unsupported video format '{path.suffix}'. Supported: {supported}")
        return path

    # Option A: Attempt native OS file picker dialog on macOS
    if platform.system() == "Darwin":
        try:
            osascript_cmd = (
                "osascript -e 'POSIX path of (choose file of type "
                '{"mp4", "mov", "avi", "mkv", "public.movie"} '
                'with prompt "Select a Railway Crossing Video")\''
            )
            proc = subprocess.run(
                osascript_cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=False,
            )
            selected = proc.stdout.strip()
            if selected and Path(selected).exists():
                path = Path(selected).resolve()
                if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    print(f"Selected video via file dialog: {path.name}")
                    return path
        except Exception:
            pass

    # Option B: Terminal Interactive Prompt
    print("\n" + "=" * 60)
    print("AI RAILWAY CROSSING SAFETY — VIDEO SELECTOR")
    print("=" * 60)
    print(f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")

    try:
        user_input = input("Enter the path to the video file: ").strip()
    except (EOFError, KeyboardInterrupt):
        raise ConfigError("Video selection cancelled by user.") from None

    if not user_input:
        raise ConfigError("No video path provided.")

    # Remove enclosing quotes if pasted with drag-and-drop
    cleaned_input = user_input.strip("\"'")
    path = Path(cleaned_input).expanduser().resolve()
    if not path.exists():
        raise ConfigError(f"Video file does not exist: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ConfigError(f"Unsupported video format '{path.suffix}'. Supported: {supported}")
    return path


def draw_detection_box(
    image: Any,
    detection: FrameDetection,
    *,
    thickness: int = 2,
    font_scale: float = 0.6,
) -> None:
    """Draw a clean, aesthetic bounding box and badge label on the image in-place."""
    import cv2

    x1, y1, x2, y2 = [int(round(v)) for v in detection.bbox_xyxy]
    h, w = image.shape[:2]
    x1, x2 = max(0, min(w - 1, x1)), max(0, min(w - 1, x2))
    y1, y2 = max(0, min(h - 1, y1)), max(0, min(h - 1, y2))

    color = CLASS_COLORS_BGR.get(detection.label, DEFAULT_BOX_COLOR)
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)

    # Format label text
    conf_str = f"{detection.confidence:.2f}"
    label_text = f"{detection.label.upper()} {conf_str}"
    if not detection.temporal_confirmed:
        label_text += " [?]"

    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_w, text_h), _baseline = cv2.getTextSize(label_text, font, font_scale, 1)

    # Text badge background
    badge_y1 = max(0, y1 - text_h - 8)
    badge_y2 = y1
    badge_x2 = min(w, x1 + text_w + 10)

    # Draw solid contrast background behind text
    cv2.rectangle(image, (x1, badge_y1), (badge_x2, badge_y2), color, -1)
    # Draw dark readable text
    text_y = y1 - 4
    cv2.putText(
        image,
        label_text,
        (x1 + 5, text_y),
        font,
        font_scale,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
    )


def process_video(
    input_path: Path,
    output_dir: Path,
    *,
    model_path: Path,
    conf_threshold: float = 0.25,
    iou_threshold: float = 0.45,
    device: str = "auto",
    live_preview: bool = False,
    temporal_smoothing: bool = False,
    progress_callback: Callable[[int, int, dict[str, int]], None] | None = None,
) -> VideoDemoSummary:
    """Execute frame-by-frame inference, visual annotation, and summary generation."""
    try:
        import cv2
    except ImportError as exc:
        raise ConfigError("opencv-python is required to run video inference") from exc

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise ConfigError("ultralytics is required to load the YOLO model") from exc

    if not model_path.exists():
        raise ConfigError(f"Model checkpoint not found at: {model_path}")
    if not input_path.exists():
        raise ConfigError(f"Input video file not found at: {input_path}")

    resolved_device = resolve_device(device)
    logger.info("loading YOLO model from %s on %s...", model_path, resolved_device)
    model = YOLO(str(model_path.resolve()))

    cap = cv2.VideoCapture(str(input_path.resolve()))
    if not cap.isOpened():
        raise ConfigError(f"Failed to open video file with OpenCV: {input_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames <= 0 or width <= 0 or height <= 0:
        cap.release()
        raise ConfigError(
            f"Video contains invalid metadata (frames={total_frames}, {width}x{height})"
        )

    if fps <= 0 or fps > 240:
        fps = 30.0

    output_video_path = output_dir / "processed_video.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore[attr-defined]
    writer = cv2.VideoWriter(str(output_video_path.resolve()), fourcc, fps, (width, height))
    if not writer.isOpened():
        fourcc_fallback = cv2.VideoWriter_fourcc(*"avc1")  # type: ignore[attr-defined]
        writer = cv2.VideoWriter(
            str(output_video_path.resolve()), fourcc_fallback, fps, (width, height)
        )
        if not writer.isOpened():
            cap.release()
            raise ConfigError(f"Failed to initialize video writer at: {output_video_path}")

    temporal_buffer = TemporalEvidenceBuffer(TemporalConfig()) if temporal_smoothing else None

    class_stats = {cls_name: ClassStats() for cls_name in CANONICAL_CLASSES}
    total_detections = 0
    frames_with_no_detections = 0
    processed_frames = 0

    start_time = time.time()
    preview_window_name = "AI Railway Crossing Safety — Video Preview (Press Q to quit)"

    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                break

            timestamp_s = float(processed_frames) / fps
            raw_results: Any = model.predict(
                source=frame,
                conf=conf_threshold,
                iou=iou_threshold,
                device=resolved_device,
                verbose=False,
            )
            results_list: list[Any] = list(raw_results) if raw_results is not None else []

            current_detections: list[FrameDetection] = []
            if results_list:
                result: Any = results_list[0]
                boxes: Any = getattr(result, "boxes", None)
                if boxes is not None and len(boxes) > 0:
                    xyxy_arr = boxes.xyxy.cpu().numpy()
                    conf_arr = boxes.conf.cpu().numpy()
                    cls_arr = boxes.cls.cpu().numpy().astype(int)

                    for i in range(len(conf_arr)):
                        raw_name = result.names.get(cls_arr[i], str(cls_arr[i]))
                        canon_label = normalize_class_name(raw_name)
                        confidence = float(conf_arr[i])
                        box_tuple = (
                            float(xyxy_arr[i][0]),
                            float(xyxy_arr[i][1]),
                            float(xyxy_arr[i][2]),
                            float(xyxy_arr[i][3]),
                        )
                        current_detections.append(
                            FrameDetection(
                                label=canon_label,
                                confidence=confidence,
                                bbox_xyxy=box_tuple,
                            )
                        )

            # Optional temporal smoothing
            if temporal_buffer is not None:
                evidence = EvidenceRecord(
                    timestamp_s=timestamp_s,
                    source_id="camera_demo",
                    modality=Modality.VISION,
                    available=True,
                    detections=tuple(
                        Detection(
                            label=d.label,
                            confidence=d.confidence,
                            bbox_xyxy=d.bbox_xyxy,
                        )
                        for d in current_detections
                    ),
                )
                filtered_evidence = temporal_buffer.process(evidence)
                confirmed_labels = {
                    d.label for d in filtered_evidence.detections
                    if d.metadata.get("temporal_confirmed", True)
                }
                active_detections: list[FrameDetection] = []
                for d in current_detections:
                    is_confirmed = d.label in confirmed_labels
                    active_detections.append(
                        FrameDetection(
                            label=d.label,
                            confidence=d.confidence,
                            bbox_xyxy=d.bbox_xyxy,
                            temporal_confirmed=is_confirmed,
                        )
                    )
                current_detections = active_detections

            # Update per-class and total statistics
            seen_classes_in_frame: set[str] = set()
            for det in current_detections:
                total_detections += 1
                if det.label in class_stats:
                    class_stats[det.label].total_detections += 1
                    class_stats[det.label].confidences.append(det.confidence)
                    seen_classes_in_frame.add(det.label)

            for cls_name in seen_classes_in_frame:
                class_stats[cls_name].frames_with_class += 1

            if not current_detections:
                frames_with_no_detections += 1

            # Draw visual bounding box annotations
            for det in current_detections:
                draw_detection_box(frame, det)

            writer.write(frame)
            processed_frames += 1

            counts_by_class = {cls_name: 0 for cls_name in CANONICAL_CLASSES}
            for det in current_detections:
                if det.label in counts_by_class:
                    counts_by_class[det.label] += 1

            if progress_callback:
                progress_callback(processed_frames, total_frames, counts_by_class)

            if live_preview:
                cv2.imshow(preview_window_name, frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q") or key == 27:
                    logger.info("live preview interrupted by user (Q pressed)")
                    break

    finally:
        cap.release()
        writer.release()
        if live_preview:
            cv2.destroyAllWindows()

    duration = max(0.001, time.time() - start_time)
    avg_fps = float(processed_frames / duration)

    summary = VideoDemoSummary(
        input_video=str(input_path.resolve()),
        output_video=str(output_video_path.resolve()),
        model_path=str(model_path.resolve()),
        model_name=model_path.name,
        device_used=resolved_device,
        width=width,
        height=height,
        fps=fps,
        total_frames=total_frames,
        processed_frames=processed_frames,
        processing_duration_s=duration,
        inference_fps=avg_fps,
        total_detections=total_detections,
        confidence_threshold=conf_threshold,
        iou_threshold=iou_threshold,
        temporal_smoothing=temporal_smoothing,
        class_stats=class_stats,
        frames_with_no_detections=frames_with_no_detections,
    )

    (output_dir / "summary.json").write_text(
        json.dumps(summary.to_dict(), indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "summary.md").write_text(summary.to_markdown() + "\n", encoding="utf-8")

    return summary


def render_terminal_progress(
    current: int, total: int, current_counts: dict[str, int]
) -> None:
    """Print an updated ASCII progress indicator with active detection counts."""
    pct = (current / total) * 100.0 if total > 0 else 0.0
    bar_len = 24
    filled = int(round((current / total) * bar_len)) if total > 0 else 0
    bar = "█" * filled + "-" * (bar_len - filled)
    counts_str = ", ".join(f"{k}: {v}" for k, v in current_counts.items())
    sys.stdout.write(
        f"\r[{bar}] {pct:5.1f}% | Frame {current:4d}/{total:4d} | Active [{counts_str}]"
    )
    sys.stdout.flush()
