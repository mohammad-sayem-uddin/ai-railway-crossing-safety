"""Scoped B0 integration tests: temporary weights/media and constructed predictions."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from railway_detection.config.exceptions import ConfigError
from railway_detection.evaluation.cache_only_engine import (
    CacheOnlyReplayEngine,
    CacheReplayRefusal,
    _validate_visual_record,
)
from railway_detection.experiments.frozen_config import (
    CheckpointIntegrityError,
    load_frozen_config,
    parse_config_dict,
)
from railway_detection.experiments.layer_b_processor import (
    LayerBEventProcessor,
    serialize_front_visual_record,
)


def config_and_weights(root):
    raw = copy.deepcopy(load_frozen_config().raw_dict)
    path = root / raw["checkpoints"]["vision"]["path"]
    path.parent.mkdir(parents=True)
    payload = b"constructed-test-weights-not-a-model"
    path.write_bytes(payload)
    raw["checkpoints"]["vision"]["expected_sha256"] = hashlib.sha256(payload).hexdigest()
    return parse_config_dict(raw), path


def test_vision_constructor_checks_only_selected_fixture_weights(tmp_path):
    config, _ = config_and_weights(tmp_path)
    processor = LayerBEventProcessor(tmp_path, config=config, vision_only=True)
    assert not processor.processed_audio_dir.exists()
    with pytest.raises(ConfigError, match="cannot extract audio"):
        processor.extract_audio(tmp_path / "unopened_event")
    with pytest.raises(ConfigError, match="cannot initialize audio"):
        processor._get_audio_pipeline(tmp_path / "unopened.pt")
    # The unchanged default still enforces the multimodal checkpoint contract.
    with pytest.raises(CheckpointIntegrityError, match="Audio V3 checkpoint missing"):
        LayerBEventProcessor(tmp_path, config=config)


def test_vision_constructor_still_refuses_changed_selected_weights(tmp_path):
    config, path = config_and_weights(tmp_path)
    path.write_bytes(b"tampered")
    with pytest.raises(CheckpointIntegrityError, match="SHA-256 mismatch"):
        LayerBEventProcessor(tmp_path, config=config, vision_only=True)


def front_records(tmp_path, monkeypatch):
    # Reuse the lawful codec fixture; none of the Mission37 test cases is rerun.
    from tests.synthetic_mission37.test_source_pts import generated_video

    config, _ = config_and_weights(tmp_path)
    generated, _ = generated_video(tmp_path, audio_first=True)
    event = tmp_path / "data/raw/layer_b/v2/train_events/event_005"
    event.mkdir(parents=True)
    generated.rename(event / "camera_front.mov")
    p = LayerBEventProcessor(tmp_path, config=config, vision_only=True)
    calls = []
    box = SimpleNamespace(cls=[0], conf=[0.8], xyxy=[[1, 2, 5, 6]])

    def predict(image, **kwargs):
        calls.append(kwargs)
        return [SimpleNamespace(boxes=[box])]

    monkeypatch.setattr(
        p,
        "_get_yolo_model",
        lambda path: SimpleNamespace(names={0: "front", 1: "rear", 2: "side"}, predict=predict),
    )
    records = p.process_front_vision(
        event, video_stream_index=1, run_id="synthetic:B0", git_commit="synthetic:code"
    )
    return p, records, calls


def test_front_entrypoint_binds_frozen_arguments_and_controlled_cache(tmp_path, monkeypatch):
    import torch

    p, records, calls = front_records(tmp_path, monkeypatch)
    assert calls and torch.initial_seed() == 42
    assert calls[0] == dict(
        conf=0.35,
        verbose=False,
        imgsz=[640, 640],
        device="cpu",
        seed=42,
        rect=False,
        half=False,
        save=False,
        save_txt=False,
        save_crop=False,
    )
    assert records[0].timestamp_s == 10.0
    assert records[0].metadata["pts_ticks"] == 900000
    assert records[0].metadata["stream_index"] == 1
    assert records[0].detections[0].metadata["class_id"] == 0
    assert len(list(p.cache_dir.glob("*.jsonl"))) == 1
    assert not list(tmp_path.rglob("camera_back.mov"))
    assert not p.processed_audio_dir.exists()


def make_engine(root, rows):
    cache = root / "data/cache/front.jsonl"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text("".join(json.dumps(row) + "\n" for row in rows))
    body = dict(
        manifest_version="1.0.0",
        created_at="2026-11-07T00:00:00Z",
        cohort="constructed",
        events={
            "synthetic:event": dict(
                event_id="synthetic:event",
                front_vision_cache=dict(
                    path="data/cache/front.jsonl",
                    sha256=hashlib.sha256(cache.read_bytes()).hexdigest(),
                    line_count=len(rows),
                    byte_size=cache.stat().st_size,
                ),
            )
        },
    )
    manifest = root / "data/cache/manifest.json"
    manifest.write_text(json.dumps(body))
    return CacheOnlyReplayEngine(manifest, repo_root=root)


def test_pts_survives_actual_descriptive_cache_reader_and_b0_replay(tmp_path, monkeypatch):
    _, records, _ = front_records(tmp_path, monkeypatch)
    rows = [serialize_front_visual_record(record) for record in records]
    engine = make_engine(tmp_path, rows)
    loaded = engine.load_visual_records("synthetic:event")
    assert loaded[0].timestamp_s == records[0].timestamp_s
    for key in ["pts_ticks", "timebase", "stream_index", "stream_start_pts", "timestamp_basis"]:
        assert loaded[0].metadata[key] == records[0].metadata[key]
    result = engine.execute_replay("synthetic:event", "B0")
    assert result.evidence_records_loaded == len(records)
    assert result.condition == "B0" and result.frames_produced > 0
    assert result.result.steps[0].timestamp_s == records[0].timestamp_s


@pytest.mark.parametrize(
    "changes",
    [
        {"pts_ticks": None},
        {"pts_ticks": True},
        {"timebase": [0, 600]},
        {"timebase": [1]},
        {"stream_index": True},
        {"stream_start_pts": "0"},
        {"frame_index": 999},
        {"pts_ticks": 900001},
    ],
)
def test_cache_reader_rejects_corrupted_original_clock(tmp_path, monkeypatch, changes):
    _, records, _ = front_records(tmp_path, monkeypatch)
    row = serialize_front_visual_record(records[0])
    row["metadata"].update(changes)
    with pytest.raises(CacheReplayRefusal):
        _validate_visual_record(row, 0)


def test_export_does_not_relabel_back_or_unavailable_or_legacy_evidence(tmp_path, monkeypatch):
    _, records, _ = front_records(tmp_path, monkeypatch)
    for bad in [
        replace(records[0], source_id="camera_2"),
        replace(records[0], available=False, detections=()),
        replace(records[0], metadata={"frame_index": 0}),
    ]:
        with pytest.raises(ValueError):
            serialize_front_visual_record(bad)


def test_front_operation_refusal_precedes_model_or_decoder(tmp_path, monkeypatch):
    config, _ = config_and_weights(tmp_path)
    p = LayerBEventProcessor(tmp_path, config=config, vision_only=True)

    def deny(*args, **kwargs):
        raise PermissionError("constructed operation refusal")

    monkeypatch.setattr(
        "railway_detection.experiments.layer_b_processor.require_media_authorization", deny
    )
    monkeypatch.setattr(
        p, "_get_yolo_model", lambda path: pytest.fail("model accessed before permission")
    )
    with pytest.raises(PermissionError, match="operation refusal"):
        p.process_front_vision(
            tmp_path / "train_events/event_001",
            video_stream_index=0,
            run_id="synthetic:denial",
            git_commit="synthetic:code",
        )


def test_front_only_manifest_does_not_fabricate_audio_for_b1(tmp_path, monkeypatch):
    _, records, _ = front_records(tmp_path, monkeypatch)
    engine = make_engine(tmp_path, [serialize_front_visual_record(r) for r in records])
    with pytest.raises(CacheReplayRefusal, match="actual audio cache"):
        engine.execute_replay("synthetic:event", "B1")
