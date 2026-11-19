"""Pure synthetic end-to-end tests for Mission 10 upright vision + audio pipeline."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import wave
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

av = pytest.importorskip("av", minversion="18.1")

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import run_complete_27_event_multimodal_evaluation as m10  # noqa: E402

from railway_detection.audio.model import PyTorchTrainHornClassifier  # noqa: E402
from railway_detection.audio.pipeline import AudioEvidencePipeline  # noqa: E402
from railway_detection.experiments.frozen_config import load_frozen_config  # noqa: E402
from railway_detection.experiments.layer_b_processor import LayerBEventProcessor  # noqa: E402
from railway_detection.safety.media_guard import MediaAccessAuthorizationError  # noqa: E402
from railway_detection.vision.video import SOURCE_DISPLAY_ROTATION_POLICY  # noqa: E402


def _make_synthetic_rotated_av_mov(tmp_path: Path, name: str, rotation: int) -> Path:
    """Create a generated 1.5s video (-90 deg display matrix) muxed with a 16kHz sine WAV."""
    base_vid = tmp_path / f"{name}_base.mp4"
    wav_path = tmp_path / f"{name}.wav"
    out_mov = tmp_path / f"{name}.mov"

    # Coded portrait 80x48 pixels which become upright 48x80 after -90 deg display rotation.
    pixels = np.zeros((48, 80, 3), dtype=np.uint8)
    pixels[:, :] = [30, 120, 210]
    with av.open(str(base_vid), "w") as container:
        stream = container.add_stream("libx264", rate=5)
        stream.width = 80
        stream.height = 48
        stream.pix_fmt = "yuv420p"
        for i in range(8):
            frame = av.VideoFrame.from_ndarray(pixels, format="bgr24")
            frame.pts = i
            frame.time_base = Fraction(1, 5)
            for pkt in stream.encode(frame):
                container.mux(pkt)
        for pkt in stream.encode():
            container.mux(pkt)

    sr = 16000
    n_samples = int(1.6 * sr)
    pcm = (0.25 * 32767.0 * np.sin(2.0 * math.pi * 440.0 * np.arange(n_samples) / sr)).astype("<i2")
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-nostdin",
            "-v",
            "error",
            "-display_rotation:v:0",
            str(rotation),
            "-i",
            str(base_vid),
            "-i",
            str(wav_path),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(out_mov),
        ],
        check=True,
        capture_output=True,
    )
    return out_mov


def test_upright_event_pipeline_rotates_frames_extracts_audio_and_parses_cleanly(tmp_path: Path) -> None:
    cfg = load_frozen_config()
    mov = _make_synthetic_rotated_av_mov(tmp_path, "synth_event", rotation=-90)
    pred_dir = tmp_path / "predictions"
    pred_dir.mkdir(parents=True, exist_ok=True)

    proc = object.__new__(LayerBEventProcessor)
    proc.config = cfg
    proc.repo_root = REPO_ROOT
    proc.cache_dir = tmp_path / "cache"
    proc.cache_dir.mkdir(parents=True, exist_ok=True)
    proc.vision_only = False

    observed_shapes: list[tuple[int, ...]] = []

    class _Box:
        def __init__(self) -> None:
            self.cls = [0]
            self.conf = [0.91]
            self.xyxy = [[4.0, 5.0, 30.0, 45.0]]

    def fake_predict(image: np.ndarray, **kwargs):
        observed_shapes.append(tuple(image.shape))
        return [SimpleNamespace(boxes=[_Box()])]

    proc._get_yolo_model = lambda _ckpt: SimpleNamespace(names={0: "front", 1: "rear", 2: "side"}, predict=fake_predict)
    audio_clf = PyTorchTrainHornClassifier(
        mean=float(cfg.audio.normalization.mean),
        std=float(cfg.audio.normalization.std),
        threshold=float(cfg.audio.operating_threshold),
    )
    proc._get_audio_pipeline = lambda _ckpt, threshold=None: AudioEvidencePipeline(
        classifier=audio_clf,
        source_id="audio_1",
        window_s=float(cfg.audio.window_s),
        hop_s=float(cfg.audio.hop_s),
        target_sample_rate=int(cfg.audio.sample_rate),
        require_classifier=True,
    )

    entry = m10._process_upright_event_streams(
        proc,
        cfg,
        eid="train_events/synth_001",
        cohort="train_events",
        event_id="synth_001",
        front_mov=mov,
        back_mov=mov,
        pred_dir=pred_dir,
        expected_front_rot=-90,
        expected_back_rot=-90,
        repo_root=tmp_path,
    )

    assert entry["front_frames"] == 8
    assert entry["back_frames"] == 8
    assert entry["audio_windows"] >= 2
    assert all(shape == (80, 48, 3) for shape in observed_shapes)
    assert entry["front_orientation"]["orientation_verified"] is True
    assert entry["front_orientation"]["image_coordinate_basis"] == [SOURCE_DISPLAY_ROTATION_POLICY]
    assert entry["front_orientation"]["input_image_sizes_observed"] == [[48, 80]]

    f_path = tmp_path / entry["front_path"]
    b_path = tmp_path / entry["back_path"]
    a_path = tmp_path / entry["audio_path"]
    assert hashlib.sha256(f_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest() == entry["front_sha256"]
    assert hashlib.sha256(a_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest() == entry["audio_sha256"]

    f_stats = m10._parse_vision_stream(f_path)
    b_stats = m10._parse_vision_stream(b_path)
    a_stats = m10._parse_audio_stream(a_path)
    assert f_stats["sampled_frames"] == 8
    assert f_stats["det_frames"] == 8
    assert f_stats["cls_counts"]["front"] == 8
    assert b_stats["det_frames"] == 8
    assert a_stats["n_windows"] == entry["audio_windows"]

    first_audio_row = json.loads(a_path.read_text(encoding="utf-8").splitlines()[0])
    assert {"window_index", "start_sec", "end_sec", "horn_confidence", "is_horn_detected"} <= set(first_audio_row)


def test_run_upright_raw_inference_fails_closed_without_owner_auth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty_repo = tmp_path / "isolated_repo"
    empty_repo.mkdir()
    monkeypatch.setattr(m10, "REPO_ROOT", empty_repo)
    with pytest.raises(MediaAccessAuthorizationError, match="AUTH_MEDIA_ACCESS_NOT_GRANTED"):
        m10.run_upright_raw_inference(SimpleNamespace(event_order=()), output_dir=tmp_path)  # type: ignore[arg-type]
