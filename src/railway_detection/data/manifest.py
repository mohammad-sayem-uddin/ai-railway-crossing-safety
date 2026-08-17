"""Normalized dataset manifest generation.

The manifest is a flat ``dataset_manifest.jsonl`` file: one normalized record
per discovered image. It is the single auditable bridge between raw dataset
files and downstream consumers (splitting, training descriptors, evaluation).

No field is fabricated: metadata that is unavailable is recorded as ``None``
(serialized ``null``), and the manifest itself is versioned.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image

from railway_detection.data.contracts import VisionSample
from railway_detection.data.validator import (
    IMAGE_EXTENSIONS,
    label_path_for,
    parse_label_annotations,
)

MANIFEST_VERSION = "1.0.0"

# Roboflow augmentation suffix: <basename>.rf.<32-hex-chars>.<ext>. The source
# identifier is the part before ".rf.", derived conservatively and only used as
# a grouping hint; it never becomes ground-truth metadata.
_AUGMENTATION_RE = re.compile(r"^(?P<source>.+?)\.rf\.[0-9a-fA-F]{32}$")


@dataclass
class ManifestBuildResult:
    records: list[VisionSample] = field(default_factory=list)
    excluded_unreadable: list[str] = field(default_factory=list)
    excluded_invalid_labels: list[str] = field(default_factory=list)
    missing_group_metadata: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def record_count(self) -> int:
        return len(self.records)

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": MANIFEST_VERSION,
            "record_count": self.record_count,
            "excluded_unreadable": self.excluded_unreadable,
            "excluded_invalid_labels": self.excluded_invalid_labels,
            "missing_group_metadata": self.missing_group_metadata,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class ManifestSummary:
    manifest_version: str
    sample_count: int
    class_distribution: Counter[str]
    split_dir_distribution: Counter[str]
    negative_sample_count: int
    ungrouped_sample_count: int
    excluded_unreadable_count: int
    excluded_invalid_label_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "sample_count": self.sample_count,
            "class_distribution": dict(sorted(self.class_distribution.items())),
            "split_dir_distribution": dict(sorted(self.split_dir_distribution.items())),
            "negative_sample_count": self.negative_sample_count,
            "ungrouped_sample_count": self.ungrouped_sample_count,
            "excluded_unreadable_count": self.excluded_unreadable_count,
            "excluded_invalid_label_count": self.excluded_invalid_label_count,
        }


def discover_images(dataset_root: str | Path) -> list[Path]:
    """Discover images under ``dataset_root``, sorted for determinism."""
    root = Path(dataset_root)
    if not root.exists():
        return []
    return sorted(
        p for p in root.rglob("*") if p.suffix.lower() in IMAGE_EXTENSIONS and p.is_file()
    )


def split_dir_for(root: Path, image_path: Path) -> str:
    """Infer the Roboflow split directory an image belongs to, or "unknown"."""
    try:
        rel = image_path.relative_to(root)
    except ValueError:
        return "unknown"
    parts = rel.parts
    for known in ("train", "valid", "test"):
        if known in parts:
            return known
    return "unknown"


def infer_split_group_id(sample_id: str) -> str | None:
    """Derive a conservative grouping hint from a Roboflow-style sample id.

    Augmented exports carry the source identifier before the ``.rf.<hash>``
    suffix, so augmented variants of one source image share a group. For
    un-augmented names the full sample id is used. The result is a hint only —
    it is not crossing metadata and never becomes a leakage-safe claim.
    """
    match = _AUGMENTATION_RE.match(sample_id)
    if match:
        return f"source:{match.group('source')}"
    return f"source:{sample_id}"


def build_vision_manifest(
    dataset_root: str | Path,
    annotations_root: str | Path,
    class_mapping: dict[str, int],
    *,
    metadata: dict[str, dict[str, Any]] | None = None,
    image_id_stem: str | None = None,
    group_hint: str = "inferred",
) -> tuple[ManifestBuildResult, ManifestSummary]:
    """Build a normalized manifest over a YOLO-style vision dataset.

    ``metadata`` maps an image_id to a metadata record; ``image_id_stem``, when
    provided, is a known metadata key prefix (e.g. ``"data/raw/vision/v1/"``)
    used to join dataset images to metadata records. ``group_hint`` names the
    grouping provenance used when metadata lacks a ``split_group_id``.
    """
    dataset_root = Path(dataset_root)
    annotations_root = Path(annotations_root)
    id_to_class = {class_id: name for name, class_id in class_mapping.items()}

    result = ManifestBuildResult()
    image_paths = discover_images(dataset_root)
    if not image_paths:
        result.warnings.append(f"no images found under {dataset_root}")
        return result, _summarize(result)

    for image_path in image_paths:
        sample_id = _relative_stem(dataset_root, image_path)
        record = metadata.get(sample_id) if metadata else None

        try:
            with Image.open(image_path) as img:
                img.verify()
        except Exception:
            result.excluded_unreadable.append(sample_id)
            result.warnings.append(
                f"excluding unreadable image {image_path.name}; run validation for details"
            )
            continue

        label_path = label_path_for(annotations_root, image_path)
        if label_path is None or not label_path.exists():
            annotations: tuple[Any, ...] = ()
            label_rel: str | None = None
        else:
            parsed = parse_label_annotations(label_path, id_to_class)
            if not parsed and label_path.stat().st_size > 0:
                result.excluded_invalid_labels.append(sample_id)
                result.warnings.append(
                    f"excluding sample {sample_id}: label has no parseable annotations"
                )
                continue
            annotations = tuple(parsed)
            label_rel = _relative_str(annotations_root, label_path)

        split_dir = split_dir_for(dataset_root, image_path)
        image_rel = _relative_str(dataset_root, image_path)

        split_group_id = None
        if record is not None:
            group_value = record.get("split_group_id")
            if isinstance(group_value, str) and group_value:
                split_group_id = group_value
        if split_group_id is None and group_hint != "none":
            split_group_id = infer_split_group_id(Path(sample_id).name)
            result.missing_group_metadata.append(sample_id)

        provenance: dict[str, Any] = {"split_dir": split_dir, "group_hint": group_hint}
        if record is not None:
            provenance["metadata_record"] = record

        sample = VisionSample(
            image_id=sample_id,
            image_path=image_rel,
            label_path=label_rel,
            split_group_id=split_group_id,
            annotations=annotations,
            crossing_id=_optional_str(record, "crossing_id"),
            session_id=_optional_str(record, "session_id"),
            video_id=_optional_str(record, "video_id"),
            frame_index=_optional_int(record, "frame_index"),
            camera_id=_optional_str(record, "camera_id"),
            weather=_optional_str(record, "weather"),
            lighting=_optional_str(record, "lighting"),
            occlusion=_optional_str(record, "occlusion"),
            distance_band=_optional_str(record, "distance_band"),
            train_type=_optional_str(record, "train_type"),
            annotation_status=_optional_str(record, "annotation_status"),
            provenance=provenance,
        )
        result.records.append(sample)

    return result, _summarize(result)


def _summarize(result: ManifestBuildResult) -> ManifestSummary:
    class_distribution: Counter[str] = Counter()
    split_distribution: Counter[str] = Counter()
    ungrouped = 0
    for record in result.records:
        for annotation in record.annotations:
            class_distribution[annotation.label] += 1
        split_dir = record.provenance.get("split_dir")
        if isinstance(split_dir, str):
            split_distribution[split_dir] += 1
        if record.split_group_id is None:
            ungrouped += 1
    negative_count = sum(1 for record in result.records if not record.annotations)
    return ManifestSummary(
        manifest_version=MANIFEST_VERSION,
        sample_count=result.record_count,
        class_distribution=class_distribution,
        split_dir_distribution=split_distribution,
        negative_sample_count=negative_count,
        ungrouped_sample_count=ungrouped,
        excluded_unreadable_count=len(result.excluded_unreadable),
        excluded_invalid_label_count=len(result.excluded_invalid_labels),
    )


def write_manifest(
    result: ManifestBuildResult,
    output_dir: str | Path,
    *,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Write ``dataset_manifest.jsonl`` and ``manifest_summary.json``."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "dataset_manifest.jsonl"
    with manifest_path.open("w", encoding="utf-8") as handle:
        for record in result.records:
            handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")
    summary = _summarize(result)
    summary_path = output_dir / "manifest_summary.json"
    payload: dict[str, Any] = summary.to_dict()
    payload["build"] = result.to_dict()
    if metadata:
        payload["extra"] = metadata
    summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def read_manifest(manifest_path: str | Path) -> list[VisionSample]:
    """Read a previously written ``dataset_manifest.jsonl``."""
    records: list[VisionSample] = []
    with Path(manifest_path).open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid JSON in manifest line {line_no}: {exc}"
                ) from exc
            records.append(VisionSample(
                image_id=str(data["image_id"]),
                image_path=str(data["image_path"]),
                label_path=data.get("label_path"),
                split_group_id=data.get("split_group_id"),
                annotations=tuple(
                    _annotation_from_dict(item) for item in data.get("annotations", [])
                ),
                crossing_id=data.get("crossing_id"),
                session_id=data.get("session_id"),
                video_id=data.get("video_id"),
                frame_index=data.get("frame_index"),
                camera_id=data.get("camera_id"),
                weather=data.get("weather"),
                lighting=data.get("lighting"),
                occlusion=data.get("occlusion"),
                distance_band=data.get("distance_band"),
                train_type=data.get("train_type"),
                annotation_status=data.get("annotation_status"),
                provenance=data.get("provenance", {}),
            ))
    return records


def _annotation_from_dict(data: dict[str, Any]) -> Any:
    from railway_detection.data.contracts import BoundingBox, VisionAnnotation

    bbox_data = data.get("bbox")
    bbox = None
    if isinstance(bbox_data, dict):
        bbox = BoundingBox(
            xmin=float(bbox_data["xmin"]),
            ymin=float(bbox_data["ymin"]),
            xmax=float(bbox_data["xmax"]),
            ymax=float(bbox_data["ymax"]),
        )
    return VisionAnnotation(
        label=str(data["label"]),
        bbox=bbox,
        metadata=dict(data.get("metadata", {})),
    )


def _optional_str(record: dict[str, Any] | None, key: str) -> str | None:
    if record is None:
        return None
    value = record.get(key)
    return str(value) if isinstance(value, str) and value else None


def _optional_int(record: dict[str, Any] | None, key: str) -> int | None:
    if record is None:
        return None
    value = record.get(key)
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else None


def _relative_str(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _relative(root: Path, path: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path


def _relative_stem(root: Path, path: Path) -> str:
    return str(_relative(root, path).with_suffix(""))
