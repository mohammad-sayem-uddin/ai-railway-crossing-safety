"""Layer B synchronized event bundle ingestion and validation.

Loads train-passage event bundles with two cameras, audio, minimal field
metadata, geometry, and event labels. Missing fields serialize to None;
nothing is fabricated.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from railway_detection.data.contracts import EventLabel, LayerBEvent
from railway_detection.utils.logging import get_logger

logger = get_logger("data.layer_b")

REQUIRED_MEDIA = ("camera_1.mp4", "camera_2.mp4", "audio.wav")
OPTIONAL_MEDIA = ("camera_1.mov", "camera_2.mov", "audio.m4a")


@dataclass
class LayerBLoadResult:
    event: LayerBEvent | None = None
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


def load_event_bundle(event_dir: str | Path) -> LayerBLoadResult:
    """Load and validate one Layer B event bundle directory."""
    event_dir = Path(event_dir)
    result = LayerBLoadResult()
    if not event_dir.is_dir():
        result.issues.append(f"event directory not found: {event_dir}")
        return result

    event_id = event_dir.name
    metadata = _read_json(event_dir / "metadata.json")
    geometry = _read_json(event_dir / "geometry.json")
    labels = _read_json(event_dir / "labels" / "event_labels.json")

    camera_1 = _first_existing(
        event_dir / "camera_1.mp4", event_dir / "camera_1.mov"
    )
    camera_2 = _first_existing(
        event_dir / "camera_2.mp4", event_dir / "camera_2.mov"
    )
    audio = _first_existing(
        event_dir / "audio.wav", event_dir / "audio.m4a", event_dir / "audio.mp3"
    )

    for media_path in (camera_1, camera_2, audio):
        if media_path is None:
            continue
        if not media_path.exists():
            result.issues.append(f"media file missing: {media_path.name}")
        elif media_path.stat().st_size == 0:
            result.issues.append(f"media file empty: {media_path.name}")

    if camera_1 is None:
        result.warnings.append("camera_1 media not found")
    if camera_2 is None:
        result.warnings.append("camera_2 media not found")
    if audio is None:
        result.warnings.append("audio media not found")

    if metadata is None:
        result.issues.append("metadata.json missing or invalid")
    if geometry is None:
        result.warnings.append("geometry.json missing or invalid")
    if labels is None:
        result.warnings.append("event labels missing or invalid")

    parsed_labels: tuple[EventLabel, ...] = ()
    if labels is not None:
        parsed_labels = _parse_event_labels(labels, result)

    event = LayerBEvent(
        event_id=event_id,
        crossing_id=_str_or_none(metadata, "crossing_id"),
        session_id=_str_or_none(metadata, "session_id"),
        camera_1_path=str(camera_1) if camera_1 else None,
        camera_2_path=str(camera_2) if camera_2 else None,
        audio_source=str(audio) if audio else None,
        sync_method=_str_or_none(metadata, "synchronization_method")
        or _str_or_none(metadata, "sync_method"),
        sync_uncertainty_s=_float_or_none(metadata, "sync_uncertainty_s"),
        direction=_str_or_none(metadata, "train_direction")
        or _str_or_none(metadata, "direction"),
        weather=_str_or_none(metadata, "weather"),
        lighting=_str_or_none(metadata, "lighting"),
        train_type=_str_or_none(metadata, "train_type"),
        geometry_reference=(
            str(geometry.get("geometry_version"))
            if geometry and geometry.get("geometry_version")
            else None
        ),
        metadata_status="loaded" if metadata is not None else "missing",
        labels=parsed_labels,
    )
    result.event = event
    return result


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _parse_event_labels(
    data: dict[str, Any], result: LayerBLoadResult
) -> tuple[EventLabel, ...]:
    """Parse event_labels.json into EventLabel records."""
    entries = data.get("labels")
    if isinstance(entries, dict):
        entries = [
            {"name": name, **value} if isinstance(value, dict) else {"name": name}
            for name, value in entries.items()
        ]
    if not isinstance(entries, list):
        return ()
    labels: list[EventLabel] = []
    for entry in entries:
        if not isinstance(entry, dict):
            result.warnings.append("skipping non-dict label entry")
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            result.warnings.append("skipping label entry without a name")
            continue
        timestamp = entry.get("timestamp_s")
        labels.append(
            EventLabel(
                name=name,
                timestamp_s=float(timestamp) if isinstance(timestamp, (int, float)) else None,
                label_status=str(entry.get("label_status", "missing")),
                uncertainty_s=(
                    float(entry["uncertainty_s"])
                    if isinstance(entry.get("uncertainty_s"), (int, float))
                    else None
                ),
                annotator=_str_or_none(entry, "annotator"),
                notes=_str_or_none(entry, "notes"),
            )
        )
    return tuple(labels)


def _first_existing(*paths: Path) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _str_or_none(data: dict[str, Any] | None, key: str) -> str | None:
    if data is None:
        return None
    value = data.get(key)
    return str(value) if isinstance(value, str) and value else None


def _float_or_none(data: dict[str, Any] | None, key: str) -> float | None:
    if data is None:
        return None
    value = data.get(key)
    return float(value) if isinstance(value, (int, float)) else None
