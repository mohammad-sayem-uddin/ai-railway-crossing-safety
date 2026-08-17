"""Abstract vision detector backend protocol.

Every vision backend (e.g. Ultralytics YOLO) must implement this protocol so
training, evaluation, and inference pipelines stay backend-agnostic. Backends
emit normalized :class:`Detection` records defined in the evidence contract;
they never make gate or policy decisions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from railway_detection.data.split import SplitSummary
from railway_detection.fusion.evidence import Detection


@runtime_checkable
class VisionDetectorBackend(Protocol):
    """Contract implemented by vision detector backends."""

    backend_name: str

    def prepare_dataset(
        self, split_summary: SplitSummary, output_dir: Path
    ) -> Path:
        """Create a backend-specific dataset descriptor for training.

        The descriptor must be derived exclusively from the immutable split
        manifests; it must never reference raw dataset files directly.
        """
        ...

    def train(
        self, config: object, data_descriptor: Path, output_dir: Path
    ) -> Path:
        """Execute training and return the best checkpoint path.

        Checkpoint selection is driven by validation performance only; the
        test split must never be touched during training or model selection.
        """
        ...

    def evaluate(self, checkpoint_path: Path, split_manifest: Path) -> dict[str, float]:
        """Evaluate a checkpoint against a held-out split manifest."""
        ...

    def load(self, checkpoint_path: Path) -> None:
        """Load a trained checkpoint and prepare the backend for inference."""
        ...

    def predict(
        self, image: object, conf: float, iou: float
    ) -> list[Detection]:
        """Run inference on a single image and emit normalized detections."""
        ...

    def predict_batch(
        self, images: list[object], conf: float, iou: float
    ) -> list[list[Detection]]:
        """Run inference on a batch of images, one detection list each."""
        ...
