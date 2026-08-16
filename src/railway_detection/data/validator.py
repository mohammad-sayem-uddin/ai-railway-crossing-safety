"""Vision dataset validation."""

from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
LABEL_EXTENSIONS = {".txt"}


@dataclass(frozen=True)
class ValidationIssue:
    sample_id: str
    severity: str
    code: str
    message: str


@dataclass
class ValidationReport:
    dataset_root: str
    annotations_root: str
    mock_data: bool
    image_count: int = 0
    annotation_count: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)
    class_distribution: Counter[str] = field(default_factory=Counter)
    image_dimensions: list[tuple[int, int]] = field(default_factory=list)
    duplicate_basenames: list[dict[str, Any]] = field(default_factory=list)
    duplicate_hashes: list[dict[str, Any]] = field(default_factory=list)
    missing_group_metadata: list[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def passed(self) -> bool:
        return self.error_count == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_root": self.dataset_root,
            "annotations_root": self.annotations_root,
            "mock_data": self.mock_data,
            "image_count": self.image_count,
            "annotation_count": self.annotation_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "passed": self.passed,
            "class_distribution": dict(sorted(self.class_distribution.items())),
            "unique_image_sizes": sorted(set(self.image_dimensions)),
            "duplicate_basenames": self.duplicate_basenames,
            "duplicate_hashes": self.duplicate_hashes,
            "missing_group_metadata_count": len(self.missing_group_metadata),
            "issues": [
                {
                    "sample_id": issue.sample_id,
                    "severity": issue.severity,
                    "code": issue.code,
                    "message": issue.message,
                }
                for issue in self.issues
            ],
        }


def validate_vision_dataset(
    dataset_root: str | Path,
    annotations_root: str | Path,
    class_mapping: dict[str, int],
    *,
    mock_data: bool = False,
    metadata: dict[str, dict[str, Any]] | None = None,
    detect_duplicate_hashes: bool = True,
) -> ValidationReport:
    """Validate a YOLO-style vision dataset and produce a report.

    ``metadata`` is an optional mapping from stable image_id to a metadata
    record. Metadata values are never fabricated; missing records are reported.
    """
    dataset_root = Path(dataset_root)
    annotations_root = Path(annotations_root)
    report = ValidationReport(
        dataset_root=str(dataset_root),
        annotations_root=str(annotations_root),
        mock_data=mock_data,
    )

    image_paths = _discover_images(dataset_root)
    report.image_count = len(image_paths)
    report.class_distribution = Counter()

    if not image_paths:
        report.issues.append(
            ValidationIssue("*", "error", "no_images", f"no images found under {dataset_root}")
        )
        return report

    id_to_class = {class_id: name for name, class_id in class_mapping.items()}
    basename_groups: dict[str, list[Path]] = defaultdict(list)
    hash_groups: dict[str, list[Path]] = defaultdict(list)

    for image_path in image_paths:
        sample_id = _relative_stem(dataset_root, image_path)
        basename_groups[image_path.stem].append(image_path)

        image_result = _check_image(image_path)
        if image_result is not None:
            report.issues.append(ValidationIssue(sample_id, "error", *image_result))
            continue

        dimensions = _read_dimensions(image_path)
        if dimensions is not None:
            report.image_dimensions.append(dimensions)

        if metadata is not None and sample_id not in metadata:
            report.missing_group_metadata.append(sample_id)

        if detect_duplicate_hashes:
            digest = _file_sha256(image_path)
            hash_groups[digest].append(image_path)

        label_path = _label_path_for(annotations_root, image_path)
        if label_path is None or not label_path.exists():
            report.issues.append(
                ValidationIssue(
                    sample_id,
                    "warning",
                    "missing_label",
                    f"annotation file not found for {image_path.name}",
                )
            )
            continue

        label_errors = _parse_label_file(label_path, id_to_class)
        if label_errors:
            for code, message in label_errors:
                report.issues.append(ValidationIssue(sample_id, "error", code, message))
            continue

        report.annotation_count += 1
        classes, annotations = _parse_annotations(label_path, id_to_class)
        for class_name in classes:
            report.class_distribution[class_name] += 1
        for code, message in annotations:
            report.issues.append(ValidationIssue(sample_id, "error", code, message))

    for basename, paths in basename_groups.items():
        if len(paths) > 1:
            report.duplicate_basenames.append(
                {
                    "basename": basename,
                    "paths": [str(_relative(dataset_root, p)) for p in sorted(paths)],
                }
            )

    for digest, paths in hash_groups.items():
        if len(paths) > 1:
            report.duplicate_hashes.append(
                {
                    "sha256": digest,
                    "paths": [str(_relative(dataset_root, p)) for p in sorted(paths)],
                }
            )

    return report


def _discover_images(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        p for p in root.rglob("*") if p.suffix.lower() in IMAGE_EXTENSIONS and p.is_file()
    )


def _check_image(path: Path) -> tuple[str, str] | None:
    try:
        with Image.open(path) as img:
            img.verify()
    except Exception as exc:
        return ("unreadable_image", f"cannot read image {path.name}: {exc}")
    return None


def _read_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with Image.open(path) as img:
            return img.size
    except Exception:
        return None


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _label_path_for(annotations_root: Path, image_path: Path) -> Path | None:
    direct = annotations_root / (image_path.stem + ".txt")
    if direct.exists():
        return direct
    if image_path.parent.name == "images":
        split_label = image_path.parent.parent / "labels" / (image_path.stem + ".txt")
        if split_label.exists():
            return split_label
    return direct


def _parse_label_file(path: Path, id_to_class: dict[int, str]) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        return [("label_read_error", f"cannot read label {path.name}: {exc}")]
    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 5:
            errors.append(
                ("malformed_label", f"line {line_no}: expected 5 fields, got {len(parts)}")
            )
            continue
        try:
            class_id = int(float(parts[0]))
        except ValueError:
            errors.append(("invalid_class_id", f"line {line_no}: class id is not an integer"))
            continue
        if class_id not in id_to_class:
            errors.append(("unknown_class", f"line {line_no}: unknown class id {class_id}"))
            continue
        try:
            values = [float(part) for part in parts[1:]]
        except ValueError:
            errors.append(("non_numeric_coordinate", f"line {line_no}: non-numeric coordinate"))
            continue
        if any(not math.isfinite(value) for value in values):
            errors.append(("non_finite_coordinate", f"line {line_no}: non-finite coordinate"))
            continue
        if values[2] <= 0 or values[3] <= 0:
            errors.append(
                ("invalid_box_size", f"line {line_no}: box width/height must be positive")
            )
        if not _normalized_box_valid(values):
            errors.append(
                ("box_out_of_range", f"line {line_no}: box exceeds normalized [0,1] range")
            )
    return errors


def _parse_annotations(
    path: Path, id_to_class: dict[int, str]
) -> tuple[list[str], list[tuple[str, str]]]:
    classes: list[str] = []
    errors: list[tuple[str, str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        return classes, [("label_read_error", f"cannot read label {path.name}: {exc}")]
    for _line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 5:
            continue
        try:
            class_id = int(float(parts[0]))
        except ValueError:
            continue
        if class_id in id_to_class:
            classes.append(id_to_class[class_id])
    return classes, errors


def _normalized_box_valid(values: list[float]) -> bool:
    x_center, y_center, width, height = values
    xmin = x_center - width / 2
    ymin = y_center - height / 2
    xmax = x_center + width / 2
    ymax = y_center + height / 2
    return 0.0 <= xmin <= xmax <= 1.0 and 0.0 <= ymin <= ymax <= 1.0


def _relative(root: Path, path: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path


def _relative_stem(root: Path, path: Path) -> str:
    rel = _relative(root, path)
    return str(rel.with_suffix(""))
