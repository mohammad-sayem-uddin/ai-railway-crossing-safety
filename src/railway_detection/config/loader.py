"""Configuration parsing and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from railway_detection.config.exceptions import ConfigError


@dataclass(frozen=True)
class VisionConfig:
    adapter: str
    mock_data: bool
    dataset_root: Path
    annotations_root: Path
    metadata_path: Path | None
    class_mapping: dict[str, int]
    negative_policy: str
    seed: int
    device: str
    image_size: tuple[int, int]
    output_root: Path
    split_output_root: Path
    detect_duplicate_hashes: bool
    split: dict[str, Any]
    source_path: Path
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AudioConfig:
    adapter: str
    mock_data: bool
    dataset_root: Path
    metadata_path: Path | None
    label_mapping: dict[str, int]
    sample_rate: int
    seed: int
    device: str
    output_root: Path
    split_output_root: Path
    split: dict[str, Any]
    source_path: Path
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FusionConfig:
    policy_version: str
    source_roles: dict[str, Any]
    confidence_thresholds: dict[str, float]
    temporal: dict[str, Any]
    opening_criteria: dict[str, Any]
    source_path: Path
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SimulationConfig:
    scenario_name: str
    mock_data: bool
    timing: dict[str, Any]
    output_root: Path
    source_path: Path
    raw: dict[str, Any] = field(default_factory=dict)


class ConfigLoader:
    """Load and validate YAML configuration from a project-root-relative path."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or _find_project_root()

    def load_vision(self, path: str | Path) -> VisionConfig:
        raw = self._load_yaml(path)
        self._require_keys(
            raw,
            "vision",
            path,
            {
                "adapter",
                "dataset_root",
                "annotations_root",
                "class_mapping",
                "seed",
                "output_root",
                "split_output_root",
            },
        )
        mapping = self._validate_class_mapping(raw["class_mapping"], "vision")
        return VisionConfig(
            adapter=str(raw["adapter"]),
            mock_data=bool(raw.get("mock_data", False)),
            dataset_root=self._resolve(raw["dataset_root"]),
            annotations_root=self._resolve(raw["annotations_root"]),
            metadata_path=self._resolve_optional(raw.get("metadata_path")),
            class_mapping=mapping,
            negative_policy=str(raw.get("negative_policy", "missing_label_is_negative")),
            seed=_as_int(raw["seed"], "seed"),
            device=str(raw.get("device", "cpu")),
            image_size=_as_int_pair(raw.get("image_size", [640, 640]), "image_size"),
            output_root=self._resolve(raw["output_root"]),
            split_output_root=self._resolve(raw["split_output_root"]),
            detect_duplicate_hashes=bool(raw.get("detect_duplicate_hashes", True)),
            split=self._validate_split(raw.get("split", {}), "vision"),
            source_path=self._abs_path(path),
            raw=raw,
        )

    def load_audio(self, path: str | Path) -> AudioConfig:
        raw = self._load_yaml(path)
        self._require_keys(
            raw,
            "audio",
            path,
            {
                "adapter",
                "dataset_root",
                "label_mapping",
                "sample_rate",
                "seed",
                "output_root",
                "split_output_root",
            },
        )
        mapping = self._validate_class_mapping(raw["label_mapping"], "audio")
        return AudioConfig(
            adapter=str(raw["adapter"]),
            mock_data=bool(raw.get("mock_data", False)),
            dataset_root=self._resolve(raw["dataset_root"]),
            metadata_path=self._resolve_optional(raw.get("metadata_path")),
            label_mapping=mapping,
            sample_rate=_as_int(raw["sample_rate"], "sample_rate"),
            seed=_as_int(raw["seed"], "seed"),
            device=str(raw.get("device", "cpu")),
            output_root=self._resolve(raw["output_root"]),
            split_output_root=self._resolve(raw["split_output_root"]),
            split=self._validate_split(raw.get("split", {}), "audio"),
            source_path=self._abs_path(path),
            raw=raw,
        )

    def load_fusion(self, path: str | Path) -> FusionConfig:
        raw = self._load_yaml(path)
        self._require_keys(
            raw,
            "fusion",
            path,
            {
                "policy_version",
                "source_roles",
                "confidence_thresholds",
                "temporal",
                "opening_criteria",
            },
        )
        thresholds = raw["confidence_thresholds"]
        if not isinstance(thresholds, dict):
            raise ConfigError("fusion confidence_thresholds must be a mapping")
        validated: dict[str, float] = {}
        for name, value in thresholds.items():
            number = _as_float(value, f"confidence_thresholds.{name}")
            if number < 0.0 or number > 1.0:
                raise ConfigError(
                    f"fusion confidence_thresholds.{name} must be between 0 and 1, got {number}"
                )
            validated[str(name)] = number
        opening = raw["opening_criteria"]
        if not isinstance(opening, dict):
            raise ConfigError("fusion opening_criteria must be a mapping")
        if bool(opening.get("audio_cannot_authorize_opening")) is False:
            raise ConfigError(
                "fusion opening_criteria.audio_cannot_authorize_opening must be true in Phase 0"
            )
        return FusionConfig(
            policy_version=str(raw["policy_version"]),
            source_roles=raw["source_roles"],
            confidence_thresholds=validated,
            temporal=raw["temporal"],
            opening_criteria=opening,
            source_path=self._abs_path(path),
            raw=raw,
        )

    def load_simulation(self, path: str | Path) -> SimulationConfig:
        raw = self._load_yaml(path)
        self._require_keys(raw, "simulation", path, {"scenario_name", "timing", "output_root"})
        return SimulationConfig(
            scenario_name=str(raw["scenario_name"]),
            mock_data=bool(raw.get("mock_data", False)),
            timing=raw["timing"],
            output_root=self._resolve(raw["output_root"]),
            source_path=self._abs_path(path),
            raw=raw,
        )

    def _load_yaml(self, path: str | Path) -> dict[str, Any]:
        resolved = self._resolve(path)
        if not resolved.exists():
            raise ConfigError(f"configuration file not found: {resolved}")
        try:
            data = yaml.safe_load(resolved.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ConfigError(f"invalid YAML in {resolved}: {exc}") from exc
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise ConfigError(f"configuration must be a mapping: {resolved}")
        return data

    def _require_keys(
        self, raw: dict[str, Any], kind: str, path: str | Path, keys: set[str]
    ) -> None:
        missing = sorted(keys - raw.keys())
        if missing:
            raise ConfigError(
                f"{kind} config {path} missing required field(s): {', '.join(missing)}"
            )

    def _validate_class_mapping(self, mapping: Any, kind: str) -> dict[str, int]:
        if not isinstance(mapping, dict):
            raise ConfigError(f"{kind} class mapping must be a mapping")
        names = [str(k) for k in mapping.keys()]
        ids = [_as_int(v, f"{kind} class mapping id for {k}") for k, v in mapping.items()]
        if len(set(names)) != len(names):
            raise ConfigError(f"{kind} class mapping has duplicate class names")
        if len(set(ids)) != len(ids):
            raise ConfigError(f"{kind} class mapping has duplicate numeric IDs")
        return {name: class_id for name, class_id in zip(names, ids, strict=True)}

    def _validate_split(self, split: Any, kind: str) -> dict[str, Any]:
        if not isinstance(split, dict):
            raise ConfigError(f"{kind} split must be a mapping")
        ratios = split.get("ratios")
        if not isinstance(ratios, dict):
            raise ConfigError(f"{kind} split.ratios must be a mapping")
        required = {"train", "val", "test"}
        missing = required - ratios.keys()
        if missing:
            raise ConfigError(f"{kind} split.ratios missing: {', '.join(sorted(missing))}")
        total = 0.0
        for name in sorted(required):
            value = _as_float(ratios[name], f"{kind} split.ratios.{name}")
            if value < 0 or value > 1:
                raise ConfigError(f"{kind} split.ratios.{name} must be between 0 and 1")
            total += value
        if abs(total - 1.0) > 1e-6:
            raise ConfigError(f"{kind} split ratios must sum to 1.0, got {total}")
        return split

    def _resolve(self, value: Any) -> Path:
        path = Path(str(value))
        if path.is_absolute():
            return path
        return (self.project_root / path).resolve()

    def _resolve_optional(self, value: Any) -> Path | None:
        if value is None or value == "":
            return None
        return self._resolve(value)

    def _abs_path(self, path: str | Path) -> Path:
        return self._resolve(path)


def _as_int(value: Any, label: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{label} must be an integer, got {value!r}") from exc


def _as_float(value: Any, label: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{label} must be a number, got {value!r}") from exc


def _as_int_pair(value: Any, label: str) -> tuple[int, int]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ConfigError(f"{label} must be a two-element list")
    return (_as_int(value[0], f"{label}[0]"), _as_int(value[1], f"{label}[1]"))


def _find_project_root() -> Path:
    path = Path.cwd()
    for candidate in (path, *path.parents):
        if (candidate / "pyproject.toml").exists() or (candidate / "configs").exists():
            return candidate
    return path
