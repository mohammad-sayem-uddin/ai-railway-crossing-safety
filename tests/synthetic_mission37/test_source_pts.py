"""Native-PTS regressions: generated codec fixtures and constructed predictions only."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from railway_detection.config.exceptions import ConfigError
from railway_detection.experiments.cache_provenance import CacheProvenanceError
from railway_detection.experiments.frozen_config import load_frozen_config
from railway_detection.experiments.layer_b_processor import (
    LayerBEventProcessor,
    deserialize_evidence_record,
    serialize_evidence_record,
)
from railway_detection.fusion.collector import MultimodalEvidenceCollector
from railway_detection.vision import video

av = pytest.importorskip("av", minversion="18.1")


def generated_video(tmp_path: Path, *, audio_first=False):
    """Lossless lawful generated pixels; no original recording/model access."""
    path = tmp_path / "generated_pts.mkv"
    ticks = [900000, 900090, 903600, 909000]
    with av.open(str(path), "w", format="nut") as out:
        if audio_first:
            out.add_stream("pcm_s16le", rate=8000)
        stream = out.add_stream("ffv1", rate=30)
        stream.width = stream.height = 16
        stream.pix_fmt = "yuv420p"
        stream.time_base = Fraction(1, 90000)
        stream.codec_context.time_base = Fraction(1, 90000)
        for i, pts in enumerate(ticks):
            frame = av.VideoFrame.from_ndarray(
                np.full((16, 16, 3), i * 30, np.uint8), format="rgb24"
            )
            frame.pts = pts
            frame.time_base = Fraction(1, 90000)
            for packet in stream.encode(frame):
                out.mux(packet)
        for packet in stream.encode():
            out.mux(packet)
    return path, ticks


def test_real_generated_decode_keeps_nonzero_irregular_pts_and_nondefault_timebase(tmp_path):
    path, ticks = generated_video(tmp_path)
    frames = list(video.frame_generator(path, source_pts=True, source_id="synthetic:front"))
    assert [f.pts_ticks for f in frames] == ticks
    assert [f.timebase for f in frames] == [(1, 90000)] * 4
    assert [f.timestamp_s for f in frames] == [float(Fraction(p, 90000)) for p in ticks]
    assert frames[0].timestamp_s == 10.0  # Never silently normalize a nonzero origin.
    assert all(f.image.shape == (16, 16, 3) for f in frames)


def test_absolute_video_stream_index_one_is_selected_and_audio_refused(tmp_path):
    path, ticks = generated_video(tmp_path, audio_first=True)
    frames = list(video.frame_generator(path, source_pts=True, video_stream_index=1))
    assert [f.pts_ticks for f in frames] == ticks and all(f.stream_index == 1 for f in frames)
    with pytest.raises(ConfigError, match="video stream"):
        list(video.frame_generator(path, source_pts=True, video_stream_index=0))


def test_pts_sampling_uses_presentation_grid_not_nominal_fps(tmp_path):
    path, _ = generated_video(tmp_path)
    frames = list(video.frame_generator(path, source_pts=True, target_fps=20))
    assert [f.pts_ticks for f in frames] == [900000, 909000]
    stride = list(video.frame_generator(path, source_pts=True, stride=2))
    assert [f.pts_ticks for f in stride] == [900000, 903600]


def fake_container(monkeypatch, frames):
    stream = SimpleNamespace(index=1, start_time=450)

    class Container:
        streams = SimpleNamespace(video=[stream])

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def decode(self, selected):
            assert selected is stream
            return iter(frames)

    monkeypatch.setattr(av, "open", lambda *args, **kwargs: Container())


@pytest.mark.parametrize(
    "pts,timebase",
    [
        (None, Fraction(1, 600)),
        (1, None),
        (1, Fraction(0)),
        (-1, Fraction(1, 600)),
        (True, Fraction(1, 600)),
    ],
)
def test_missing_or_invalid_original_timestamp_is_not_fps_fallback(
    tmp_path, monkeypatch, pts, timebase
):
    path = tmp_path / "constructed.mkv"
    path.touch()
    fake_container(monkeypatch, [SimpleNamespace(pts=pts, time_base=timebase)])
    with pytest.raises(ConfigError, match="PTS|timebase|timestamps"):
        list(video.frame_generator(path, source_pts=True))


@pytest.mark.parametrize("ticks", [[450, 450], [450, 449]])
def test_duplicate_or_backwards_pts_refused_even_for_unsampled_frames(tmp_path, monkeypatch, ticks):
    path = tmp_path / "constructed.mkv"
    path.touch()
    frames = [
        SimpleNamespace(pts=p, time_base=Fraction(1, 600), to_ndarray=lambda **kw: None)
        for p in ticks
    ]
    fake_container(monkeypatch, frames)
    with pytest.raises(ConfigError, match="increasing"):
        list(video.frame_generator(path, source_pts=True, target_fps=1))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"target_fps": 0},
        {"target_fps": float("nan")},
        {"target_fps": True},
        {"target_fps": 5, "stride": 2},
        {"stride": 0},
        {"video_stream_index": True},
    ],
)
def test_pts_invalid_sampling_or_stream_parameters(tmp_path, kwargs):
    path = tmp_path / "constructed.mkv"
    path.touch()
    with pytest.raises(ConfigError):
        list(video.frame_generator(path, source_pts=True, **kwargs))


def processor(tmp_path, monkeypatch):
    # Avoid the production constructor: it verifies unrelated real checkpoints.
    p = object.__new__(LayerBEventProcessor)
    p.config = load_frozen_config()
    p.cache_dir = tmp_path / "cache"
    p.cache_dir.mkdir()
    p._get_yolo_model = lambda path: SimpleNamespace(names={}, predict=lambda *args, **kwargs: [])
    return p


def test_pts_survives_decode_inference_serialization_and_collector_output(tmp_path, monkeypatch):
    path, ticks = generated_video(tmp_path, audio_first=True)
    p = processor(tmp_path, monkeypatch)
    records = p.run_vision_inference(
        path,
        tmp_path / "not_a_model.pt",
        "camera_1",
        target_fps=1000,
        use_cache=False,
        source_pts=True,
        video_stream_index=1,
    )
    assert len(records) == 4
    restored = [
        deserialize_evidence_record(json.loads(json.dumps(serialize_evidence_record(r))))
        for r in records
    ]
    assert [r.timestamp_s for r in restored] == [float(Fraction(t, 90000)) for t in ticks]
    assert [r.metadata["pts_ticks"] for r in restored] == ticks
    assert all(
        r.metadata["timebase"] == [1, 90000] and r.metadata["stream_index"] == 1 for r in restored
    )
    collector = MultimodalEvidenceCollector()
    for r in restored:
        collector.add_evidence(r)
    # Existing evaluation frame contract retains the original evidence metadata;
    # its master grid is separate from the original observation clock.
    frames = [collector._build_frame_at(r.timestamp_s) for r in restored]
    assert [f.master_timestamp_s for f in frames] == [r.timestamp_s for r in restored]
    for frame in frames:
        assert frame.vision_records
        assert all(e.metadata.get("timestamp_basis") == "source_pts" for e in frame.vision_records)


def test_pts_missing_frame_clock_cannot_return_empty_success_or_write_cache(tmp_path, monkeypatch):
    path = tmp_path / "constructed.mkv"
    path.touch()
    p = processor(tmp_path, monkeypatch)

    def broken(*args, **kwargs):
        raise ConfigError("missing original PTS")
        yield

    monkeypatch.setattr("railway_detection.experiments.layer_b_processor.frame_generator", broken)
    with pytest.raises(ConfigError, match="PTS"):
        p.run_vision_inference(
            path, tmp_path / "not_a_model.pt", "camera_1", use_cache=False, source_pts=True
        )
    assert list(p.cache_dir.iterdir()) == []


def test_pts_prediction_failure_is_not_silently_a_negative_result(tmp_path, monkeypatch):
    path, _ = generated_video(tmp_path)
    p = processor(tmp_path, monkeypatch)

    def fail(*args, **kwargs):
        raise RuntimeError("constructed prediction failure")

    p._get_yolo_model = lambda path: SimpleNamespace(predict=fail)
    with pytest.raises(ConfigError, match="prediction failure"):
        p.run_vision_inference(
            path, tmp_path / "not_a_model.pt", "camera_1", use_cache=False, source_pts=True
        )


def test_pts_legacy_cache_identity_cannot_be_reused(tmp_path, monkeypatch):
    p = processor(tmp_path, monkeypatch)
    prov = p.build_stream_provenance(
        cohort="train_events",
        event_id="event_001",
        source_id="camera_1",
        modality="vision",
        run_id="synthetic:pts",
    )
    path = tmp_path / "constructed.mkv"
    with pytest.raises(CacheProvenanceError, match="PTS mode"):
        p.run_vision_inference(
            path,
            tmp_path / "not_a_model.pt",
            "camera_1",
            provenance=prov,
            source_pts=True,
            video_stream_index=1,
        )
    pts_prov = p.build_stream_provenance(
        cohort="train_events",
        event_id="event_001",
        source_id="camera_1",
        modality="vision",
        run_id="synthetic:pts",
        source_pts=True,
        video_stream_index=1,
    )
    assert pts_prov.configuration_sha256() != prov.configuration_sha256()
    assert pts_prov.preprocessing_config["video_stream_index"] == 1
    with pytest.raises(CacheProvenanceError, match="PTS mode"):
        p.run_vision_inference(
            path,
            tmp_path / "not_a_model.pt",
            "camera_1",
            provenance=pts_prov,
            source_pts=True,
            video_stream_index=0,
        )
    with pytest.raises(CacheProvenanceError, match="PTS cache"):
        p.run_vision_inference(path, tmp_path / "not_a_model.pt", "camera_1", source_pts=True)


def test_existing_media_authority_refusal_precedes_pts_decoder(tmp_path, monkeypatch):
    path = tmp_path / "constructed.mkv"

    def denied(*args, **kwargs):
        raise PermissionError("constructed denial")

    monkeypatch.setattr(video, "require_media_authorization", denied)
    monkeypatch.setattr(
        av, "open", lambda *args, **kwargs: pytest.fail("decoder opened before permission")
    )
    with pytest.raises(PermissionError, match="denial"):
        list(video.frame_generator(path, source_pts=True))


def test_empty_pts_stream_fails_closed(tmp_path, monkeypatch):
    path = tmp_path / "constructed.mkv"
    path.touch()
    fake_container(monkeypatch, [])
    with pytest.raises(ConfigError, match="no decoded"):
        list(video.frame_generator(path, source_pts=True))


def test_neutral_browser_navigation_uses_actual_pts_without_source_labels(tmp_path, monkeypatch):
    import cv2
    from scripts.review_source_pts import browse

    path, _ = generated_video(tmp_path, audio_first=True)
    keys = iter(map(ord, ["n", "f", "b", "r", "q"]))
    labels, titles = [], []
    monkeypatch.setattr(cv2, "namedWindow", lambda *args: None)
    monkeypatch.setattr(cv2, "resizeWindow", lambda *args: None)
    monkeypatch.setattr(cv2, "putText", lambda image, label, *args: labels.append(label))

    def show(title, image):
        assert image.shape == (64, 16, 3)  # Readout band is outside original pixels.
        titles.append(title)

    monkeypatch.setattr(cv2, "imshow", show)
    monkeypatch.setattr(cv2, "waitKey", lambda delay: next(keys))
    monkeypatch.setattr(cv2, "destroyWindow", lambda title: None)
    browse(path, 1, "Q001")
    assert all(title == "Source review Q001" for title in titles)
    assert all(str(path) not in label and "event_" not in label for label in labels)
    assert ["frame=0 ", "frame=1 ", "frame=3 ", "frame=2 ", "frame=0 "] == [
        label.split("Q001 ")[1].split("PTS=")[0] for label in labels
    ]
    assert "PTS=900000 tb=1/90000 stream=1" in labels[0]


def test_browser_refuses_unblinded_display_token_before_source_access(tmp_path):
    from scripts.review_source_pts import browse

    with pytest.raises(ValueError, match="neutral"):
        browse(tmp_path / "unopened.mov", 0, "no_train_event_001")
