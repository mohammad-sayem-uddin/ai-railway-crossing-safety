"""Unit tests for the abstract vision detector backend protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from railway_detection.data.split import SplitSummary
from railway_detection.fusion.evidence import Detection
from railway_detection.vision.adapter import VisionDetectorBackend


@dataclass
class FakeBackend:
    """Minimal protocol implementation used to exercise structural typing."""

    backend_name: str = "fake"
    calls: list[str] = field(default_factory=list)

    def prepare_dataset(self, split_summary: SplitSummary, output_dir: Path) -> Path:
        self.calls.append("prepare_dataset")
        return output_dir / "data.yaml"

    def train(self, config: object, data_descriptor: Path, output_dir: Path) -> Path:
        self.calls.append("train")
        return output_dir / "best.pt"

    def evaluate(self, checkpoint_path: Path, split_manifest: Path) -> dict[str, float]:
        self.calls.append("evaluate")
        return {"mAP50": 0.5}

    def load(self, checkpoint_path: Path) -> None:
        self.calls.append("load")

    def predict(self, image: object, conf: float, iou: float) -> list[Detection]:
        self.calls.append("predict")
        return [Detection("front", 0.9, (0.0, 0.0, 10.0, 10.0))]

    def predict_batch(
        self, images: list[object], conf: float, iou: float
    ) -> list[list[Detection]]:
        self.calls.append("predict_batch")
        return [[Detection("front", 0.9, (0.0, 0.0, 10.0, 10.0))] for _ in images]


def test_fake_backend_is_protocol_instance():
    backend = FakeBackend()
    assert isinstance(backend, VisionDetectorBackend)


def test_protocol_methods_callable(tmp_path):
    backend = FakeBackend()
    split = SplitSummary(
        split_id="s1",
        group_field="crossing_id",
        seed=1,
        ratios={"train": 0.7, "val": 0.15, "test": 0.15},
        require_grouping=True,
        allow_ungrouped_fallback=False,
        partitions={
            "train": ["a1"],
            "val": ["b1"],
            "test": ["c1"],
        },
    )
    descriptor = backend.prepare_dataset(split, tmp_path)
    assert descriptor.name == "data.yaml"

    checkpoint = backend.train(object(), descriptor, tmp_path)
    assert checkpoint.name == "best.pt"

    metrics = backend.evaluate(checkpoint, tmp_path / "test.jsonl")
    assert metrics["mAP50"] == 0.5

    backend.load(checkpoint)
    detections = backend.predict(object(), conf=0.25, iou=0.45)
    assert detections[0].label == "front"

    batch = backend.predict_batch([object(), object()], conf=0.25, iou=0.45)
    assert len(batch) == 2

    assert backend.calls == [
        "prepare_dataset",
        "train",
        "evaluate",
        "load",
        "predict",
        "predict_batch",
    ]


def test_detection_contract_used_by_protocol():
    """Protocol emits the shared evidence contract, not backend raw types."""
    detection = Detection("rear", 0.8, (1.0, 2.0, 3.0, 4.0))
    assert detection.label == "rear"
    assert detection.confidence == 0.8
    assert detection.bbox_xyxy == (1.0, 2.0, 3.0, 4.0)
