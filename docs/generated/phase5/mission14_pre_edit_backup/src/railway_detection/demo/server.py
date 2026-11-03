"""Interactive Web Dashboard Server for Railway Train Detection.

Provides a multi-threaded HTTP server with REST APIs for:
- Video upload and frame-by-frame YOLO inference
- Real-time Server-Sent Events (SSE) progress broadcasting
- Single-image instant detection
- Benchmark metrics and failure analysis visualization
- Past test runs exploration and video streaming
"""

from __future__ import annotations

import json
import mimetypes
import shutil
import socketserver
import sys
import threading
import time
import urllib.parse
import uuid
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any

import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from railway_detection.demo.video_demo import (  # noqa: E402
    CANONICAL_CLASSES,
    create_output_directory,
    draw_detection_box,
    normalize_class_name,
    process_video,
    resolve_device,
)
from railway_detection.utils.logging import configure_logging, get_logger  # noqa: E402

logger = get_logger("demo.server")

DEFAULT_MODEL_PATH = PROJECT_ROOT / "experiments/vision/39f402dfe460/checkpoints/weights/best.pt"
STATIC_WEB_DIR = Path(__file__).resolve().parent / "web"
UPLOAD_TEMP_DIR = PROJECT_ROOT / "outputs/temp_uploads"
OUTPUTS_DIR = PROJECT_ROOT / "outputs/video_tests"

# Global active jobs registry
active_jobs: dict[str, dict[str, Any]] = {}
jobs_lock = threading.Lock()


@dataclass(frozen=True)
class MultipartField:
    """One parsed multipart form field, with file bytes kept binary-safe."""

    name: str
    content: bytes
    filename: str | None = None
    content_type: str | None = None

    def text(self) -> str:
        """Decode a text field using its declared charset or UTF-8."""
        charset = "utf-8"
        if self.content_type:
            message = BytesParser(policy=policy.default).parsebytes(
                f"Content-Type: {self.content_type}\r\n\r\n".encode("ascii")
            )
            charset = message.get_content_charset() or charset
        return self.content.decode(charset)


def parse_multipart_form(content_type: str, body: bytes) -> dict[str, MultipartField]:
    """Parse a multipart/form-data body without the deprecated ``cgi`` module."""
    headers = (
        b"MIME-Version: 1.0\r\nContent-Type: "
        + content_type.encode("ascii")
        + b"\r\n\r\n"
    )
    message = BytesParser(policy=policy.default).parsebytes(headers + body)
    if not message.is_multipart():
        raise ValueError("request body is not valid multipart form data")

    fields: dict[str, MultipartField] = {}
    for part in message.iter_parts():
        if part.get_content_disposition() != "form-data":
            continue
        name = part.get_param("name", header="content-disposition")
        if not isinstance(name, str) or not name:
            raise ValueError("multipart field is missing its name")
        if name in fields:
            raise ValueError(f"duplicate multipart field {name!r}")
        fields[name] = MultipartField(
            name=name,
            content=part.get_payload(decode=True) or b"",
            filename=part.get_filename(),
            content_type=part.get_content_type() if part.get("Content-Type") else None,
        )
    return fields


def _read_multipart_form(handler: Any, content_type: str) -> dict[str, MultipartField]:
    """Read and parse the declared request body, rejecting malformed lengths."""
    try:
        content_length = int(handler.headers.get("Content-Length", ""))
    except (TypeError, ValueError) as exc:
        raise ValueError("missing or invalid Content-Length") from exc
    if content_length < 0:
        raise ValueError("invalid Content-Length")
    body = handler.rfile.read(content_length)
    if len(body) != content_length:
        raise ValueError("incomplete multipart request body")
    return parse_multipart_form(content_type, body)


def _display_path(path: Path) -> str:
    """Render a project-relative path when possible, otherwise an absolute path."""
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


class DashboardHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler serving the dashboard SPA and REST APIs."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC_WEB_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy standard HTTP access logs in console
        pass

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self._handle_api_status()
        elif path == "/api/benchmark":
            self._handle_api_benchmark()
        elif path == "/api/runs":
            self._handle_api_runs()
        elif path.startswith("/api/progress/"):
            job_id = path.split("/api/progress/")[-1]
            self._handle_api_progress(job_id)
        elif path.startswith("/outputs/"):
            self._handle_serve_output_file(path)
        elif path.startswith("/experiments/"):
            self._handle_serve_experiment_file(path)
        elif path == "/" or not (STATIC_WEB_DIR / path.lstrip("/")).exists():
            # SPA fallback: serve index.html
            self.path = "/index.html"
            return super().do_GET()
        else:
            return super().do_GET()

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/upload":
            self._handle_api_upload()
        elif path == "/api/process":
            self._handle_api_process()
        elif path == "/api/predict_image":
            self._handle_api_predict_image()
        else:
            self._send_json({"error": "Endpoint not found"}, status=HTTPStatus.NOT_FOUND)

    def _handle_api_status(self) -> None:
        """Return system status, device capabilities, and available models."""
        try:
            import torch
            mps_available = bool(
                torch.backends.mps.is_available() and torch.backends.mps.is_built()
            )
            cuda_available = bool(torch.cuda.is_available())
        except Exception:
            mps_available = False
            cuda_available = False

        models: list[dict[str, Any]] = []
        weights_candidates = list(PROJECT_ROOT.glob("experiments/vision/**/weights/*.pt"))
        for p in weights_candidates:
            run_name = p.parent.parent.name
            models.append({
                "name": f"{run_name} - {p.name}",
                "path": str(p.relative_to(PROJECT_ROOT)),
                "is_default": str(p.resolve()) == str(DEFAULT_MODEL_PATH.resolve()),
            })

        if not models and DEFAULT_MODEL_PATH.exists():
            models.append({
                "name": "YOLOv8n Baseline (39f402dfe460)",
                "path": str(DEFAULT_MODEL_PATH.relative_to(PROJECT_ROOT)),
                "is_default": True,
            })

        data = {
            "status": "online",
            "device_capabilities": {
                "mps_available": mps_available,
                "cuda_available": cuda_available,
                "default_device": resolve_device("auto"),
            },
            "canonical_classes": CANONICAL_CLASSES,
            "available_models": models,
            "default_model": str(DEFAULT_MODEL_PATH) if DEFAULT_MODEL_PATH.exists() else None,
        }
        self._send_json(data)

    def _handle_api_benchmark(self) -> None:
        """Return baseline evaluation metrics and failure analysis summary."""
        eval_dir = PROJECT_ROOT / "experiments/vision/39f402dfe460/evaluation"
        metrics_json_path = eval_dir / "metrics.json"
        failure_json_path = eval_dir / "failure_analysis.json"

        metrics_data = {}
        failure_data = {}

        if metrics_json_path.exists():
            try:
                metrics_data = json.loads(metrics_json_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        if failure_json_path.exists():
            try:
                failure_data = json.loads(failure_json_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        cm_url = "/experiments/vision/39f402dfe460/evaluation/confusion_matrix.png"
        pr_url = "/experiments/vision/39f402dfe460/evaluation/pr_curves.png"
        data = {
            "run_id": "39f402dfe460",
            "model_name": "YOLOv8n Baseline V1",
            "split_id": "705d388743ea",
            "split_type": "development_fallback",
            "leakage_risk": True,
            "metrics": metrics_data,
            "failure_analysis": failure_data,
            "confusion_matrix_url": cm_url,
            "pr_curves_url": pr_url,
        }
        self._send_json(data)

    def _handle_api_runs(self) -> None:
        """List past test runs with summaries from outputs/video_tests."""
        runs: list[dict[str, Any]] = []
        if OUTPUTS_DIR.exists():
            dirs = sorted(
                [d for d in OUTPUTS_DIR.iterdir() if d.is_dir()],
                key=lambda d: d.stat().st_mtime,
                reverse=True,
            )
            for d in dirs:
                summary_file = d / "summary.json"
                if summary_file.exists():
                    try:
                        sum_data = json.loads(summary_file.read_text(encoding="utf-8"))
                        runs.append({
                            "run_id": d.name,
                            "summary": sum_data,
                            "video_url": f"/outputs/video_tests/{d.name}/processed_video.mp4",
                            "created_at": d.stat().st_mtime,
                        })
                    except Exception:
                        continue
        self._send_json({"runs": runs})

    def _handle_api_progress(self, job_id: str) -> None:
        """Return real-time job progress status."""
        with jobs_lock:
            job = active_jobs.get(job_id)
        if not job:
            self._send_json({"error": "Job not found"}, status=HTTPStatus.NOT_FOUND)
            return
        self._send_json(job)

    def _handle_api_upload(self) -> None:
        """Handle multipart form video upload and save to temporary directory."""
        UPLOAD_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            self._send_json(
                {"error": "Expected multipart/form-data"}, status=HTTPStatus.BAD_REQUEST
            )
            return

        try:
            form = _read_multipart_form(self, content_type)
        except (ValueError, UnicodeError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        if "video" not in form:
            self._send_json(
                {"error": "No video file provided in field 'video'"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        file_item = form["video"]
        filename = file_item.filename or "uploaded_video.mp4"
        stem = Path(filename).stem.replace(" ", "_")
        suffix = Path(filename).suffix.lower() or ".mp4"
        safe_name = f"{stem}_{int(time.time())}{suffix}"
        dest_path = UPLOAD_TEMP_DIR / safe_name

        with open(dest_path, "wb") as f:
            f.write(file_item.content)

        self._send_json({
            "message": "Upload successful",
            "filename": filename,
            "saved_path": _display_path(dest_path),
            "full_path": str(dest_path),
            "size_bytes": dest_path.stat().st_size,
        })

    def _handle_api_process(self) -> None:
        """Start asynchronous video inference job and return job_id."""
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        try:
            req = json.loads(body)
        except Exception:
            self._send_json({"error": "Invalid JSON body"}, status=HTTPStatus.BAD_REQUEST)
            return

        video_path_raw = req.get("video_path")
        if not video_path_raw:
            self._send_json({"error": "Missing video_path"}, status=HTTPStatus.BAD_REQUEST)
            return

        input_video = Path(video_path_raw).expanduser()
        if not input_video.is_absolute():
            input_video = (PROJECT_ROOT / input_video).resolve()

        if not input_video.exists():
            self._send_json(
                {"error": f"Video file not found: {input_video}"}, status=HTTPStatus.BAD_REQUEST
            )
            return

        model_path_raw = req.get("model_path") or str(DEFAULT_MODEL_PATH)
        model_path = Path(model_path_raw).expanduser()
        if not model_path.is_absolute():
            model_path = (PROJECT_ROOT / model_path).resolve()

        conf = float(req.get("conf", 0.25))
        iou = float(req.get("iou", 0.45))
        device = str(req.get("device", "auto"))
        temporal = bool(req.get("temporal", False))

        job_id = uuid.uuid4().hex[:12]
        output_dir = create_output_directory(input_video, base_output_dir=OUTPUTS_DIR)

        with jobs_lock:
            active_jobs[job_id] = {
                "job_id": job_id,
                "status": "processing",
                "progress_pct": 0.0,
                "current_frame": 0,
                "total_frames": 0,
                "active_counts": {"front": 0, "rear": 0, "side": 0},
                "output_dir": str(output_dir),
                "summary": None,
                "error": None,
            }

        def worker() -> None:
            def on_progress(current: int, total: int, counts: dict[str, int]) -> None:
                with jobs_lock:
                    if job_id in active_jobs:
                        pct = round((current / total) * 100.0, 1) if total > 0 else 0.0
                        active_jobs[job_id]["current_frame"] = current
                        active_jobs[job_id]["total_frames"] = total
                        active_jobs[job_id]["progress_pct"] = pct
                        active_jobs[job_id]["active_counts"] = counts

            try:
                summary = process_video(
                    input_path=input_video,
                    output_dir=output_dir,
                    model_path=model_path,
                    conf_threshold=conf,
                    iou_threshold=iou,
                    device=device,
                    live_preview=False,
                    temporal_smoothing=temporal,
                    progress_callback=on_progress,
                )
                with jobs_lock:
                    if job_id in active_jobs:
                        v_url = f"/outputs/video_tests/{output_dir.name}/processed_video.mp4"
                        active_jobs[job_id]["status"] = "completed"
                        active_jobs[job_id]["progress_pct"] = 100.0
                        active_jobs[job_id]["summary"] = summary.to_dict()
                        active_jobs[job_id]["video_url"] = v_url
            except Exception as exc:
                logger.error("Job %s failed: %s", job_id, exc)
                with jobs_lock:
                    if job_id in active_jobs:
                        active_jobs[job_id]["status"] = "failed"
                        active_jobs[job_id]["error"] = str(exc)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

        self._send_json({"job_id": job_id, "status": "started", "output_dir": str(output_dir)})

    def _handle_api_predict_image(self) -> None:
        """Run instant YOLO inference on a single uploaded frame or picture."""
        try:
            import cv2
            from ultralytics import YOLO
        except ImportError as exc:
            self._send_json(
                {"error": f"Required packages missing: {exc}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return

        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            self._send_json(
                {"error": "Expected multipart/form-data"}, status=HTTPStatus.BAD_REQUEST
            )
            return

        try:
            form = _read_multipart_form(self, content_type)
        except (ValueError, UnicodeError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        if "image" not in form:
            self._send_json(
                {"error": "No image file provided in field 'image'"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        file_item = form["image"]
        image_bytes = file_item.content
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            self._send_json({"error": "Could not decode image"}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            conf = float(form["conf"].text()) if "conf" in form else 0.25
            iou = float(form["iou"].text()) if "iou" in form else 0.45
            requested_device = form["device"].text() if "device" in form else "auto"
        except (UnicodeError, ValueError) as exc:
            self._send_json(
                {"error": f"Invalid inference option: {exc}"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        device = resolve_device(requested_device)

        model_path = DEFAULT_MODEL_PATH
        if not model_path.exists():
            self._send_json(
                {"error": "Default model weights not found"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return

        model = YOLO(str(model_path.resolve()))
        t0 = time.time()
        raw_results: Any = model.predict(
            source=img, conf=conf, iou=iou, device=device, verbose=False
        )
        inf_time_ms = (time.time() - t0) * 1000.0

        detections = []
        annotated_img = img.copy()
        results_list: list[Any] = list(raw_results) if raw_results is not None else []

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
                    box = (
                        float(xyxy_arr[i][0]),
                        float(xyxy_arr[i][1]),
                        float(xyxy_arr[i][2]),
                        float(xyxy_arr[i][3]),
                    )
                    det_dict = {
                        "label": canon_label,
                        "confidence": round(confidence, 4),
                        "bbox_xyxy": [round(v, 2) for v in box],
                    }
                    detections.append(det_dict)

                    from railway_detection.demo.video_demo import FrameDetection
                    frame_det = FrameDetection(
                        label=canon_label,
                        confidence=confidence,
                        bbox_xyxy=box,
                    )
                    draw_detection_box(annotated_img, frame_det)

        _ok, encoded_jpeg = cv2.imencode(".jpg", annotated_img)
        import base64
        jpg_as_text = base64.b64encode(encoded_jpeg).decode("utf-8")

        self._send_json({
            "detections": detections,
            "total_detections": len(detections),
            "inference_time_ms": round(inf_time_ms, 2),
            "annotated_image_base64": f"data:image/jpeg;base64,{jpg_as_text}",
        })

    def _handle_serve_output_file(self, path: str) -> None:
        """Serve generated MP4 video files and output artifacts with byte range support."""
        rel_path = path.lstrip("/")
        full_path = (PROJECT_ROOT / rel_path).resolve()
        if not full_path.exists() or not full_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        mime_type, _ = mimetypes.guess_type(str(full_path))
        mime_type = mime_type or "application/octet-stream"

        file_size = full_path.stat().st_size
        range_header = self.headers.get("Range")

        if range_header and range_header.startswith("bytes="):
            # Byte-range video streaming support for HTML5 video players
            try:
                parts = range_header.replace("bytes=", "").split("-")
                start = int(parts[0])
                end = int(parts[1]) if parts[1] else file_size - 1
                length = end - start + 1

                self.send_response(HTTPStatus.PARTIAL_CONTENT)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                with open(full_path, "rb") as f:
                    f.seek(start)
                    self.wfile.write(f.read(length))
                return
            except Exception:
                pass

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        with open(full_path, "rb") as f:
            shutil.copyfileobj(f, self.wfile)

    def _handle_serve_experiment_file(self, path: str) -> None:
        """Serve experiment evaluation plots (confusion matrix, PR curves)."""
        rel_path = path.lstrip("/")
        full_path = (PROJECT_ROOT / rel_path).resolve()
        if not full_path.exists() or not full_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return
        mime_type, _ = mimetypes.guess_type(str(full_path))
        mime_type = mime_type or "image/png"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(full_path.stat().st_size))
        self.end_headers()
        with open(full_path, "rb") as f:
            shutil.copyfileobj(f, self.wfile)

    def _send_json(self, data: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def run_dashboard_server(
    host: str = "127.0.0.1",
    port: int = 8501,
    open_browser: bool = True,
) -> None:
    """Launch the multi-threaded Dashboard HTTP server."""
    configure_logging()
    STATIC_WEB_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    server = ThreadedHTTPServer((host, port), DashboardHTTPRequestHandler)
    url = f"http://{host}:{port}"

    print("\n" + "=" * 65)
    print("🚂 AI RAILWAY CROSSING SAFETY — INTERACTIVE DASHBOARD")
    print("=" * 65)
    print(f"Server URL  : {url}")
    print("Status      : ONLINE & READY")
    print(f"Device Auto : {resolve_device('auto').upper()}")
    print(f"Web Static  : {STATIC_WEB_DIR}")
    print("=" * 65)
    print("Opening web interface in your browser... (Press Ctrl+C to stop)\n")

    if open_browser:
        import webbrowser
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard server gracefully...")
    finally:
        server.server_close()
        print("Dashboard server stopped.")


if __name__ == "__main__":
    run_dashboard_server()
