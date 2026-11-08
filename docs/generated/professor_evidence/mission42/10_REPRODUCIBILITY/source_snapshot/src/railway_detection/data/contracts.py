"""Normalized data contracts for vision, audio, and Layer B events.

All records use explicit ``unknown``/``None`` for missing metadata; no field is
fabricated. Contracts are intentionally independent of any specific label
format so that import adapters can translate source data into these types.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# Sentinel for explicitly-missing metadata. Serialized to None.
UNKNOWN = None


@dataclass(frozen=True)
class BoundingBox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def width(self) -> float:
        return self.xmax - self.xmin

    def height(self) -> float:
        return self.ymax - self.ymin

    def is_normalized(self) -> bool:
        return 0.0 <= self.xmin <= self.xmax <= 1.0 and 0.0 <= self.ymin <= self.ymax <= 1.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class VisionAnnotation:
    label: str
    bbox: BoundingBox | None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VisionSample:
    image_id: str
    image_path: str
    label_path: str | None
    split_group_id: str | None
    annotations: tuple[VisionAnnotation, ...] = ()
    crossing_id: str | None = None
    session_id: str | None = None
    video_id: str | None = None
    frame_index: int | None = None
    camera_id: str | None = None
    weather: str | None = None
    lighting: str | None = None
    occlusion: str | None = None
    distance_band: str | None = None
    train_type: str | None = None
    annotation_status: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "image_id": self.image_id,
            "image_path": self.image_path,
            "label_path": self.label_path,
            "split_group_id": self.split_group_id,
            "annotations": [
                {
                    "label": ann.label,
                    "bbox": ann.bbox.to_dict() if ann.bbox is not None else None,
                    "metadata": ann.metadata,
                }
                for ann in self.annotations
            ],
        }
        for key in (
            "crossing_id",
            "session_id",
            "video_id",
            "frame_index",
            "camera_id",
            "weather",
            "lighting",
            "occlusion",
            "distance_band",
            "train_type",
            "annotation_status",
        ):
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        if self.provenance:
            data["provenance"] = self.provenance
        return data


@dataclass(frozen=True)
class AudioSample:
    clip_id: str
    audio_path: str
    label: str
    split_group_id: str | None
    duration_s: float | None = None
    sample_rate: int | None = None
    channels: int | None = None
    crossing_id: str | None = None
    session_id: str | None = None
    recording_device: str | None = None
    weather: str | None = None
    noise_type: str | None = None
    snr_db: float | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "clip_id": self.clip_id,
            "audio_path": self.audio_path,
            "label": self.label,
            "split_group_id": self.split_group_id,
        }
        for key in (
            "duration_s",
            "sample_rate",
            "channels",
            "crossing_id",
            "session_id",
            "recording_device",
            "weather",
            "noise_type",
            "snr_db",
        ):
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        if self.provenance:
            data["provenance"] = self.provenance
        return data


@dataclass(frozen=True)
class EventLabel:
    name: str
    timestamp_s: float | None
    label_status: str
    uncertainty_s: float | None = None
    annotator: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class LayerBEvent:
    event_id: str
    crossing_id: str | None = None
    session_id: str | None = None
    camera_1_path: str | None = None
    camera_2_path: str | None = None
    audio_source: str | None = None
    sync_method: str | None = None
    sync_uncertainty_s: float | None = None
    direction: str | None = None
    weather: str | None = None
    lighting: str | None = None
    train_type: str | None = None
    geometry_reference: str | None = None
    metadata_status: str = "unknown"
    labels: tuple[EventLabel, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "event_id": self.event_id,
            "metadata_status": self.metadata_status,
        }
        for key in (
            "crossing_id",
            "session_id",
            "camera_1_path",
            "camera_2_path",
            "audio_source",
            "sync_method",
            "sync_uncertainty_s",
            "direction",
            "weather",
            "lighting",
            "train_type",
            "geometry_reference",
        ):
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        if self.labels:
            data["labels"] = [asdict(label) for label in self.labels]
        return data
