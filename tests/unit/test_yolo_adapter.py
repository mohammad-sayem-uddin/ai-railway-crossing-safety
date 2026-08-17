"""Unit tests for the Ultralytics YOLO adapter.

All framework calls are exercised through a fake ``ultralytics`` module so no
network access or model download happens in tests.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from railway_detection.config.exceptions import ConfigError
from railway_detection.data.split import SplitSummary
from railway_detection.vision.yolo_adapter import (
    UltralyticsYOLOAdapter,
    copy_split_manifests,
    read_split_manifest,
    write_yolo_descriptor,
)


class _FakeBoxes:
    def __init__(self, cls_id: int, conf: float, xyxy: list[float], names: dict[int, str]):
        self.cls = [cls_id]
        self.conf = [conf]
        self.xyxy = [xyxy]
        self.names = names


class _FakeResult:
    def __init__(self, boxes: list[_FakeBoxes], names: dict[int, str] | None = None):
        self.boxes = boxes
        self.names = names if names is not None else {0: "front"}


class _FakeYOLOModel:
    def __init__(self, results=None):
        self._results = results or []

    def train(self, **kwargs):
        save_dir = Path(kwargs["project"]) / kwargs["name"]
        weights = save_dir / "weights"
        weights.mkdir(parents=True, exist_ok=True)
        (weights / "best.pt").write_bytes(b"mock-weights")
        return types.SimpleNamespace(save_dir=str(save_dir))

    def val(self, **kwargs):
        return types.SimpleNamespace(box=types.SimpleNamespace(map50=0.81, map=0.62))

    def predict(self, **kwargs):
        return self._results


@pytest.fixture
def fake_ultralytics(monkeypatch):
    module = types.ModuleType("ultralytics")
    module.YOLO = _FakeYOLOModel
    monkeypatch.setitem(sys.modules, "ultralytics", module)
    return module


def make_split(tmp_path) -> SplitSummary:
    manifests = tmp_path / "splits"
    manifests.mkdir()
    for name, ids in {
        "train": ["a1", "a2"],
        "val": ["b1"],
        "test": ["c1"],
    }.items():
        (manifests / f"{name}.jsonl").write_text(
            "\n".join(f'{{"sample_id": "{i}"}}' for i in ids) + "\n",
            encoding="utf-8",
        )
    return SplitSummary(
        split_id="s_test",
        group_field="crossing_id",
        seed=7,
        ratios={"train": 0.5, "val": 0.25, "test": 0.25},
        require_grouping=True,
        allow_ungrouped_fallback=False,
        partitions={"train": ["a1", "a2"], "val": ["b1"], "test": ["c1"]},
    )


def test_prepare_dataset_writes_descriptor(tmp_path, fake_ultralytics):
    adapter = UltralyticsYOLOAdapter()
    descriptor = adapter.prepare_dataset(make_split(tmp_path), tmp_path / "desc")
    assert descriptor.exists()
    content = descriptor.read_text(encoding="utf-8")
    assert "split_id: s_test" in content


def test_train_returns_best_checkpoint(tmp_path, fake_ultralytics):
    adapter = UltralyticsYOLOAdapter()

    class Cfg:
        model_name = "yolov8n.pt"
        image_size = 640
        epochs = 1
        batch_size = 2
        device = "cpu"
        seed = 42

    descriptor = tmp_path / "data.yaml"
    descriptor.write_text("names: []\n", encoding="utf-8")
    checkpoint = adapter.train(Cfg(), descriptor, tmp_path / "run_1")
    assert checkpoint.exists()
    assert checkpoint.name == "best.pt"


def test_train_requires_ultralytics(tmp_path, monkeypatch):
    monkeypatch.delitem(sys.modules, "ultralytics", raising=False)
    import builtins

    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "ultralytics":
            raise ImportError("blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    adapter = UltralyticsYOLOAdapter()
    with pytest.raises(ConfigError):
        adapter.train(object(), tmp_path / "d.yaml", tmp_path)


def test_evaluate_returns_metrics(tmp_path, fake_ultralytics):
    adapter = UltralyticsYOLOAdapter()
    metrics = adapter.evaluate(tmp_path / "best.pt", tmp_path / "test.jsonl")
    assert metrics == {"mAP50": 0.81, "mAP50_95": 0.62}


def test_load_and_predict_emits_normalized_detections(tmp_path, fake_ultralytics):
    adapter = UltralyticsYOLOAdapter()
    adapter.load(tmp_path / "best.pt")

    fake_result = _FakeResult(
        [_FakeBoxes(0, 0.93, [1.0, 2.0, 3.0, 4.0], {0: "front"})]
    )
    adapter._model = _FakeYOLOModel([fake_result, fake_result])

    detections = adapter.predict(object(), conf=0.5, iou=0.45)
    assert len(detections) == 1
    assert detections[0].label == "front"
    assert detections[0].confidence == 0.93
    assert detections[0].bbox_xyxy == (1.0, 2.0, 3.0, 4.0)

    batch = adapter.predict_batch([object(), object()], conf=0.5, iou=0.45)
    assert len(batch) == 2


def test_predict_without_loaded_model_raises(tmp_path, fake_ultralytics):
    adapter = UltralyticsYOLOAdapter()
    with pytest.raises(ConfigError):
        adapter.predict(object(), conf=0.5, iou=0.45)


def test_read_split_manifest(tmp_path):
    path = tmp_path / "m.jsonl"
    path.write_text('{"sample_id": "x"}\n{"sample_id": "y"}\n', encoding="utf-8")
    records = read_split_manifest(path)
    assert [r["sample_id"] for r in records] == ["x", "y"]


def test_write_yolo_descriptor_content(tmp_path):
    split = make_split(tmp_path)
    descriptor = write_yolo_descriptor(
        split,
        tmp_path / "out",
        dataset_root=tmp_path / "raw",
        class_names=["front", "side", "rear"],
    )
    content = descriptor.read_text(encoding="utf-8")
    assert "nc: 3" in content
    assert "names: ['front', 'side', 'rear']" in content
    assert f"path: {tmp_path / 'raw'}" in content
    assert "train: train.jsonl" in content


def test_copy_split_manifests(tmp_path):
    split = make_split(tmp_path)
    out = tmp_path / "out"
    copy_split_manifests(split, tmp_path / "splits", out)
    assert (out / "train.jsonl").exists()
    assert (out / "val.jsonl").exists()
    assert (out / "test.jsonl").exists()
    assert "a1" in (out / "train.jsonl").read_text(encoding="utf-8")
