"""Audio dataset loader and batch generation infrastructure for training and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np


@dataclass(frozen=True)
class AudioWindowRecord:
    """Metadata record for a single processed audio window."""

    window_id: str
    source_file: str
    source_sha256: str
    split_group_id: str
    class_name: str
    class_id: int
    partition: str
    window_index: int
    start_time_s: float
    end_time_s: float
    duration_s: float
    sample_rate: int
    standardized_wav_path: str
    feature_path: str
    feature_type: str
    feature_shape: tuple[int, int]
    dataset_role: str


@dataclass(frozen=True)
class AudioBatch:
    """Mini-batch of audio feature tensors and binary labels."""

    features: np.ndarray  # shape (B, n_mels, n_frames) or (B, feature_dim)
    labels: np.ndarray  # shape (B,) int64 in {0, 1}
    window_ids: tuple[str, ...]
    source_files: tuple[str, ...]


class AudioDatasetLoader:
    """Loads window records from manifest and yields batches for training/evaluation."""

    def __init__(
        self,
        manifest_path: str | Path,
        partition: str = "train",
        workspace_root: str | Path = "/Users/sayemuddin/Desktop/Train_automation",
    ) -> None:
        self.manifest_path = Path(manifest_path)
        self.partition = partition
        self.workspace_root = Path(workspace_root)
        self.records: list[AudioWindowRecord] = self._load_records()

    def _load_records(self) -> list[AudioWindowRecord]:
        if not self.manifest_path.exists():
            return []

        with open(self.manifest_path, encoding="utf-8") as f:
            data = json.load(f)

        records: list[AudioWindowRecord] = []
        for item in data:
            if item.get("partition") == self.partition:
                rec = AudioWindowRecord(
                    window_id=item["window_id"],
                    source_file=item["source_file"],
                    source_sha256=item["source_sha256"],
                    split_group_id=item["split_group_id"],
                    class_name=item["class_name"],
                    class_id=int(item["class_id"]),
                    partition=item["partition"],
                    window_index=int(item["window_index"]),
                    start_time_s=float(item["start_time_s"]),
                    end_time_s=float(item["end_time_s"]),
                    duration_s=float(item["duration_s"]),
                    sample_rate=int(item["sample_rate"]),
                    standardized_wav_path=item["standardized_wav_path"],
                    feature_path=item["feature_path"],
                    feature_type=item["feature_type"],
                    feature_shape=tuple(item["feature_shape"]),
                    dataset_role=item["dataset_role"],
                )
                records.append(rec)
        return records

    def __len__(self) -> int:
        return len(self.records)

    @property
    def positive_count(self) -> int:
        return sum(1 for r in self.records if r.class_id == 1)

    @property
    def negative_count(self) -> int:
        return sum(1 for r in self.records if r.class_id == 0)

    @property
    def class_ratio(self) -> float:
        if self.negative_count == 0:
            return float("inf")
        return float(self.positive_count) / float(self.negative_count)

    def load_feature(self, record: AudioWindowRecord) -> np.ndarray:
        """Load the precomputed .npy log-mel feature tensor for a window."""
        feat_path = self.workspace_root / record.feature_path
        if not feat_path.exists():
            raise FileNotFoundError(f"Feature file not found: {feat_path}")
        return np.load(feat_path)

    def generate_batches(
        self,
        batch_size: int = 32,
        shuffle: bool = True,
        flatten_features: bool = False,
        rng: np.random.Generator | None = None,
    ) -> Iterator[AudioBatch]:
        """Yield mini-batches of audio features and labels."""
        if len(self.records) == 0:
            return

        indices = np.arange(len(self.records))
        if shuffle:
            if rng is None:
                rng = np.random.default_rng(42)
            rng.shuffle(indices)

        for start_idx in range(0, len(indices), batch_size):
            batch_indices = indices[start_idx : start_idx + batch_size]
            features_list = []
            labels_list = []
            window_ids = []
            source_files = []

            for idx in batch_indices:
                rec = self.records[idx]
                feat = self.load_feature(rec)
                if flatten_features:
                    feat = feat.flatten()
                features_list.append(feat)
                labels_list.append(rec.class_id)
                window_ids.append(rec.window_id)
                source_files.append(rec.source_file)

            batch_features = np.stack(features_list, axis=0)
            batch_labels = np.array(labels_list, dtype=np.int64)

            yield AudioBatch(
                features=batch_features,
                labels=batch_labels,
                window_ids=tuple(window_ids),
                source_files=tuple(source_files),
            )
