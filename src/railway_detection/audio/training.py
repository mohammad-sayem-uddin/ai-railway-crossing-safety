"""Audio model training infrastructure, checkpointing, and pretraining gates.

Implements the training configuration, checkpoint serialization, and safety
gating logic for the train-horn audio classifier. This module enforces
critical data-integrity gates BEFORE any training can begin:

- Layer B evaluation audio must never appear in training manifests.
- Both positive and negative samples must be present in train and val splits.
- Minimum positive sample count is met.

This module does NOT perform actual gradient-based training; that lives in
scripts/train_audio_model.py. It provides the reusable, testable infrastructure
and fail-closed safety gates that the training scripts depend on.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from railway_detection.audio.dataset import AudioDatasetLoader


class AudioTrainingGatingError(RuntimeError):
    """Raised when a pretraining safety gate fails. Training must NOT proceed."""


@dataclass
class AudioTrainingConfig:
    """Configuration for audio model training runs."""

    model_name: str = "train_horn_classifier"
    batch_size: int = 32
    max_epochs: int = 50
    learning_rate: float = 0.001
    seed: int = 42
    manifest_path: str | Path = "data/manifests/audio_training_dataset.json"
    feature_type: str = "log_mel_spectrogram"
    n_mels: int = 64
    n_fft: int = 512
    sample_rate: int = 16000


@dataclass
class AudioModelCheckpoint:
    """Serializable metadata checkpoint for a trained audio model.

    Stores model identity, operating threshold, feature parameters, and
    evaluation metrics. Does NOT store model weights (those are .pt files
    managed by the training scripts).
    """

    model_name: str
    model_level: str
    operating_threshold: float
    feature_params: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_level": self.model_level,
            "operating_threshold": self.operating_threshold,
            "feature_params": self.feature_params,
            "metrics": self.metrics,
        }

    def save(self, path: Path | str) -> Path:
        """Serialize checkpoint metadata to JSON."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return out

    @classmethod
    def load(cls, path: Path | str) -> "AudioModelCheckpoint":
        """Deserialize checkpoint metadata from JSON."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {p}")
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls(
            model_name=data["model_name"],
            model_level=data["model_level"],
            operating_threshold=data["operating_threshold"],
            feature_params=data.get("feature_params", {}),
            metrics=data.get("metrics", {}),
        )


class AudioTrainer:
    """Training orchestrator with fail-closed pretraining safety gates.

    Loads train and val partitions from the manifest and verifies:
    1. No Layer B evaluation audio contamination in any partition.
    2. Both positive and negative samples exist in train and val.
    3. Minimum positive sample count is met.

    Training is BLOCKED (AudioTrainingGatingError) if any gate fails.
    """

    def __init__(
        self,
        config: AudioTrainingConfig | None = None,
        workspace_root: str | Path | None = None,
    ) -> None:
        if config is None:
            config = AudioTrainingConfig()
        self.config = config

        if workspace_root is None:
            workspace_root = Path.cwd()
        self.workspace_root = Path(workspace_root)

        manifest_path = Path(config.manifest_path)
        if not manifest_path.is_absolute():
            manifest_path = self.workspace_root / manifest_path

        self.train_loader = AudioDatasetLoader(
            manifest_path=manifest_path,
            partition="train",
            workspace_root=self.workspace_root,
        )
        self.val_loader = AudioDatasetLoader(
            manifest_path=manifest_path,
            partition="val",
            workspace_root=self.workspace_root,
        )

    def verify_pretraining_gates(self) -> None:
        """Run all pretraining safety gates. Raises AudioTrainingGatingError on failure."""
        self._check_layer_b_contamination()
        self._check_negative_samples_present()
        self._check_minimum_positive_count()

    def _check_layer_b_contamination(self) -> None:
        """CRITICAL: Layer B evaluation audio must NEVER appear in training data."""
        for loader, partition_name in [
            (self.train_loader, "train"),
            (self.val_loader, "val"),
        ]:
            for record in loader.records:
                source_lower = record.source_file.lower()
                wav_lower = record.standardized_wav_path.lower()
                if "layer_b" in source_lower or "layer_b" in wav_lower:
                    raise AudioTrainingGatingError(
                        f"CRITICAL SAFETY VIOLATION: Layer B evaluation audio detected in "
                        f"'{partition_name}' partition! Record '{record.window_id}' references "
                        f"source_file='{record.source_file}'. Layer B data is reserved exclusively "
                        f"for real-world evaluation and must NEVER be used for training. "
                        f"AUDIO TRAINING BLOCKED."
                    )

    def _check_negative_samples_present(self) -> None:
        """Both train and val must contain negative (non-train-horn) samples."""
        if self.train_loader.negative_count == 0:
            raise AudioTrainingGatingError(
                "AUDIO TRAINING BLOCKED: Missing negative background audio in train partition. "
                "A binary classifier requires both positive and negative examples."
            )
        if self.val_loader.negative_count == 0:
            raise AudioTrainingGatingError(
                "AUDIO TRAINING BLOCKED: Missing negative background audio in val partition. "
                "A binary classifier requires both positive and negative examples for validation."
            )

    def _check_minimum_positive_count(self) -> None:
        """Ensure sufficient positive samples for meaningful training."""
        if self.train_loader.positive_count < 10:
            raise AudioTrainingGatingError(
                f"AUDIO TRAINING BLOCKED: Insufficient positive samples in train partition "
                f"({self.train_loader.positive_count} < 10 minimum required)."
            )