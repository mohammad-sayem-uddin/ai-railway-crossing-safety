"""Fail-closed cache provenance identity, canonicalization, and validation for Layer B runs.

Defines a complete, deterministic provenance architecture for controlled experimental
caches and enforces strict separation between:
1. Historical diagnostic caches (legacy unverified JSONL files without provenance headers).
2. Controlled experimental caches (provenance-verified JSONL files with canonical header
   and payload SHA-256 integrity protection).
3. Descriptive-only evaluation artifacts (fixed-site descriptive reports, non-official).
4. Official evaluation artifacts (Stage-2.1 + EVAL-AUTH bound Phase 12 replay evidence).

Distinguishes three cryptographic identity levels:
- Configuration Identity (`configuration_sha256`): Model, checkpoint, preprocessing, ROI,
  experiment config, failure injector, injector parameters, timing, schema, and code version.
- Stream Cache Identity (`cache_identity_sha256`): Cohort, event, source, modality +
  Configuration Identity.
- Run Provenance Identity (`provenance_sha256`): Full 14-field identity including `run_id`.

Never opens, decodes, or hashes raw media files (.mov, .mp4, .wav).
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality

CONTROLLED_CACHE_SCHEMA_VERSION = "layer-b-controlled-cache/2.0.0"
CANONICAL_SERIALIZATION_VERSION = "canonical-json/1.0"
PROVENANCE_ENVELOPE_KEY = "__cache_provenance__"

HISTORICAL_DIAGNOSTIC_CACHE_CLASS = "historical_diagnostic"
HISTORICAL_DIAGNOSTIC_UNVERIFIED = "HISTORICAL_DIAGNOSTIC_UNVERIFIED"
CONTROLLED_EXPERIMENTAL_CACHE_CLASS = "controlled_experimental"
DESCRIPTIVE_ONLY_CACHE_CLASS = "descriptive_only"
OFFICIAL_EVALUATION_CACHE_CLASS = "official_evaluation"

CACHE_REUSE_ISOLATED_RUN = "isolated_run"
CACHE_REUSE_IDENTICAL_CONFIG = "allow_identical_config_reuse"
VALID_CACHE_REUSE_POLICIES = frozenset(
    {CACHE_REUSE_ISOLATED_RUN, CACHE_REUSE_IDENTICAL_CONFIG}
)

VALID_EXPERIMENT_FAMILIES = frozenset(
    {
        "B0",
        "B1",
        "B2",
        "B3",
        "B4",
        "B5",
        "B5a",
        "B5b",
        "B5c",
        "B6",
        "B6a",
        "B6b",
        "B6c",
        "B7",
        "B7a",
        "B7b",
        "B7c",
        "B7d",
        "B7e",
        "B7f",
        "B8",
    }
)

VALID_FAILURE_INJECTORS = frozenset(
    {
        "none",
        "B5a",
        "B5b",
        "B5c",
        "B6a",
        "B6b",
        "B6c",
        "B7a",
        "B7b",
        "B7c",
        "B7d",
        "B7e",
        "B7f",
        "CAMERA_DROPOUT",
        "AUDIO_DROPOUT",
        "INTERMITTENT_FLAPPING",
        "RANDOM_FRAME_DROPS",
        "FALSE_DETECTION_INJECTION",
        "OUT_OF_ORDER_FRAMES",
        "STALE_TIMESTAMPS",
        "camera_dropout",
        "audio_dropout",
        "intermittent_flapping",
        "random_frame_drops",
        "false_detection_injection",
        "out_of_order_frames",
        "stale_timestamps",
    }
)

PROHIBITED_AUDIO_V2_SHA256 = (
    "59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5"
)
PROHIBITED_AUDIO_V2_PATH_FRAGMENT = "models/audio/best_checkpoint.pt"
PROHIBITED_AUDIO_V2_PATH_SUFFIXES = (
    "models/audio/best_checkpoint.pt",
    "audio_v2/best_checkpoint.pt",
)
UNRESOLVED_CHECKPOINT_TOKENS = frozenset(
    {"unresolved", "missing", "unknown", "none", "null", "tbd", "pending", "placeholder"}
)

VALID_COHORTS = frozenset({"train_events", "no_train_events", "engine_events"})
VALID_MODALITIES = frozenset({"vision", "audio"})
FORBIDDEN_MEDIA_EXTENSIONS = frozenset(
    {".mov", ".mp4", ".wav", ".avi", ".mkv", ".flac", ".m4a", ".mp3"}
)

REQUIRED_PROVENANCE_FIELDS: tuple[str, ...] = (
    "cohort",
    "event_id",
    "source_id",
    "modality",
    "model_architecture",
    "checkpoint_sha256",
    "preprocessing_config",
    "experiment_config_sha256",
    "failure_injector",
    "injector_parameters",
    "timing_config",
    "cache_schema_version",
    "software_version",
    "run_id",
)

CONFIGURATION_IDENTITY_FIELDS: tuple[str, ...] = (
    "modality",
    "model_architecture",
    "checkpoint_sha256",
    "preprocessing_config",
    "experiment_config_sha256",
    "failure_injector",
    "injector_parameters",
    "timing_config",
    "cache_schema_version",
    "software_version",
)

CACHE_IDENTITY_FIELDS: tuple[str, ...] = (
    "cohort",
    "event_id",
    "source_id",
    "modality",
    "model_architecture",
    "checkpoint_sha256",
    "preprocessing_config",
    "experiment_config_sha256",
    "failure_injector",
    "injector_parameters",
    "timing_config",
    "cache_schema_version",
    "software_version",
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CacheProvenanceError(ValueError):
    """Raised when cache provenance is missing, malformed, mismatched, or unauthorized."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def _contains_raw_media_reference(text: str) -> bool:
    lower = text.strip().lower().replace("\\", "/")
    for ext in FORBIDDEN_MEDIA_EXTENSIONS:
        if lower.endswith(ext):
            return True
    parts = [p for p in lower.split("/") if p not in ("", ".")]
    return any(
        left == "data" and right == "raw"
        for left, right in zip(parts, parts[1:], strict=False)
    )


def _assert_finite_json_value(value: Any, field_name: str) -> Any:
    """Validate and normalize a mapping/list/scalar for deterministic canonical JSON."""
    if value is None or isinstance(value, (str, bool, int)):
        if isinstance(value, str):
            if _contains_raw_media_reference(value):
                raise CacheProvenanceError(
                    "RAW_MEDIA_REFERENCE_FORBIDDEN",
                    f"{field_name} contains raw media reference {value!r}",
                )
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CacheProvenanceError(
                "PROVENANCE_NONFINITE_NUMBER",
                f"{field_name} contains non-finite float {value!r}",
            )
        # Normalize -0.0 to +0.0 so equivalent zeros produce identical JSON strings
        if value == 0.0:
            return 0.0
        return value
    if isinstance(value, Mapping):
        raw_items = list(value.items())
        for k, _ in raw_items:
            if not isinstance(k, str) or not k.strip():
                raise CacheProvenanceError(
                    "PROVENANCE_FIELD_INVALID",
                    f"{field_name} mapping keys must be non-empty strings, got {k!r}",
                )
        out: dict[str, Any] = {}
        for k, v in sorted(raw_items, key=lambda item: item[0]):
            out[k] = _assert_finite_json_value(v, f"{field_name}.{k}")
        return out
    if isinstance(value, (list, tuple)):
        return [
            _assert_finite_json_value(item, f"{field_name}[{idx}]")
            for idx, item in enumerate(value)
        ]
    raise CacheProvenanceError(
        "PROVENANCE_FIELD_INVALID",
        f"{field_name} has unsupported type {type(value).__name__}",
    )


def canonicalize_config(value: Any, field_name: str = "config") -> Any:
    """Recursively validate and canonicalize a configuration structure."""
    return _assert_finite_json_value(value, field_name)


def canonical_json_str(payload: Mapping[str, Any]) -> str:
    """Deterministic canonical JSON string with sorted keys, finite numbers, and no whitespace."""
    if not isinstance(payload, Mapping):
        raise CacheProvenanceError(
            "PROVENANCE_FIELD_INVALID",
            f"canonical_json_str requires a mapping, got {type(payload).__name__}",
        )
    normalized = _assert_finite_json_value(payload, "payload")
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def compute_canonical_digest(payload: Mapping[str, Any]) -> str:
    """Compute deterministic SHA-256 hex digest of a canonicalized configuration mapping."""
    return hashlib.sha256(canonical_json_str(payload).encode("utf-8")).hexdigest()


def _loads_strict_json(raw_line: str, *, context: str) -> Any:
    """Parse JSON while rejecting duplicate keys and non-finite constants."""

    def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in pairs:
            if k in out:
                raise CacheProvenanceError(
                    "CACHE_DUPLICATE_JSON_KEY",
                    f"Duplicate JSON key {k!r} in {context}",
                )
            out[k] = v
        return out

    def _reject_constant(const: str) -> Any:
        raise CacheProvenanceError(
            "PROVENANCE_NONFINITE_NUMBER",
            f"Non-finite JSON constant {const!r} in {context}",
        )

    try:
        return json.loads(
            raw_line,
            object_pairs_hook=_no_duplicates,
            parse_constant=_reject_constant,
        )
    except CacheProvenanceError:
        raise
    except json.JSONDecodeError as exc:
        raise CacheProvenanceError(
            "CACHE_MALFORMED_JSON", f"Invalid JSON in {context}: {exc}"
        ) from exc


def _validate_roi_config(roi_config: Any, field_name: str = "roi_config") -> dict[str, Any]:
    """Validate an ROI configuration mapping (bounding box or polygon)."""
    if not isinstance(roi_config, Mapping) or not roi_config:
        raise CacheProvenanceError(
            "PROVENANCE_ROI_INVALID",
            f"{field_name} must be a non-empty mapping when provided",
        )
    normalized = _assert_finite_json_value(roi_config, field_name)
    if all(k in normalized for k in ("x1", "y1", "x2", "y2")):
        for coord in ("x1", "y1", "x2", "y2"):
            val = normalized[coord]
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                raise CacheProvenanceError(
                    "PROVENANCE_ROI_INVALID",
                    f"{field_name}.{coord} must be numeric",
                )
        if float(normalized["x2"]) <= float(normalized["x1"]) or float(
            normalized["y2"]
        ) <= float(normalized["y1"]):
            raise CacheProvenanceError(
                "PROVENANCE_ROI_INVALID",
                f"{field_name} bounding box requires x2 > x1 and y2 > y1, got {normalized}",
            )
    if "polygon" in normalized:
        poly = normalized["polygon"]
        if not isinstance(poly, list) or len(poly) < 3:
            raise CacheProvenanceError(
                "PROVENANCE_ROI_INVALID",
                f"{field_name}.polygon must contain at least 3 vertices",
            )
        for idx, pt in enumerate(poly):
            if (
                not isinstance(pt, list)
                or len(pt) != 2
                or any(isinstance(c, bool) or not isinstance(c, (int, float)) for c in pt)
            ):
                raise CacheProvenanceError(
                    "PROVENANCE_ROI_INVALID",
                    f"{field_name}.polygon[{idx}] must be a [x, y] numeric pair",
                )
    return normalized


def _validate_injector_contract(
    failure_injector: str, injector_parameters: Mapping[str, Any]
) -> None:
    """Enforce fail-closed injector identity and B7e parameter requirements."""
    inj_lower = failure_injector.strip().lower()
    if inj_lower == "none":
        return

    is_b7e = inj_lower in ("b7e", "stale_timestamps")
    schedules = injector_parameters.get("schedules")
    has_stale_schedule = False
    if isinstance(schedules, list):
        for sched in schedules:
            if isinstance(sched, Mapping) and str(sched.get("mode", "")).lower() in (
                "stale_timestamps",
                "b7e",
            ):
                has_stale_schedule = True
                delay_s = sched.get("delay_s", sched.get("parameters", {}).get("delay_s") if isinstance(sched.get("parameters"), Mapping) else None)
                target_src = sched.get("target_source") or (
                    sched.get("parameters", {}).get("target_source")
                    if isinstance(sched.get("parameters"), Mapping)
                    else None
                )
                if (
                    isinstance(delay_s, bool)
                    or not isinstance(delay_s, (int, float))
                    or not math.isfinite(float(delay_s))
                    or float(delay_s) <= 0.0
                ):
                    raise CacheProvenanceError(
                        "PROVENANCE_INJECTOR_INVALID",
                        "STALE_TIMESTAMPS schedule in injector_parameters requires positive finite delay_s",
                    )
                if not isinstance(target_src, str) or not target_src.strip():
                    raise CacheProvenanceError(
                        "PROVENANCE_INJECTOR_INVALID",
                        "STALE_TIMESTAMPS schedule in injector_parameters requires non-empty target_source",
                    )

    if is_b7e and not has_stale_schedule:
        delay_s = injector_parameters.get("delay_s")
        target_src = injector_parameters.get("target_source")
        if (
            isinstance(delay_s, bool)
            or not isinstance(delay_s, (int, float))
            or not math.isfinite(float(delay_s))
            or float(delay_s) <= 0.0
        ):
            raise CacheProvenanceError(
                "PROVENANCE_INJECTOR_INVALID",
                f"failure_injector={failure_injector!r} requires explicit positive finite delay_s in injector_parameters",
            )
        if not isinstance(target_src, str) or not target_src.strip():
            raise CacheProvenanceError(
                "PROVENANCE_INJECTOR_INVALID",
                f"failure_injector={failure_injector!r} requires explicit non-empty target_source in injector_parameters",
            )


def resolve_checkpoint_identity(
    checkpoint_path: Path | str | None,
    expected_sha256: str | None = None,
    *,
    require_resolved: bool = True,
) -> dict[str, Any]:
    """Resolve and validate checkpoint identity without touching raw media.

    Rejects filename-only checkpoint specifications when a cryptographic SHA-256
    digest is absent or unresolved, and blocks prohibited Audio V2 checkpoints.
    """
    path_str = str(checkpoint_path).strip() if checkpoint_path is not None else ""
    if path_str and _contains_raw_media_reference(path_str):
        raise CacheProvenanceError(
            "RAW_MEDIA_REFERENCE_FORBIDDEN",
            f"Checkpoint path cannot reference raw media: {path_str!r}",
        )
    norm_path = path_str.replace("\\", "/").lower()
    if PROHIBITED_AUDIO_V2_PATH_FRAGMENT in norm_path:
        raise CacheProvenanceError(
            "PROHIBITED_CHECKPOINT_REJECTED",
            f"Prohibited Audio V2 checkpoint path rejected: {path_str!r}",
        )

    sha_str = (expected_sha256 or "").strip().lower()
    if sha_str == PROHIBITED_AUDIO_V2_SHA256:
        raise CacheProvenanceError(
            "PROHIBITED_CHECKPOINT_REJECTED",
            f"Prohibited Audio V2 checkpoint SHA-256 rejected: {sha_str}",
        )

    if not sha_str or sha_str in UNRESOLVED_CHECKPOINT_TOKENS:
        if require_resolved:
            raise CacheProvenanceError(
                "PROVENANCE_CHECKPOINT_UNRESOLVED",
                f"Checkpoint identity for {path_str or '<missing>'} is unresolved; "
                "a human-readable filename without an immutable SHA-256 digest cannot "
                "masquerade as a fully identified model checkpoint.",
            )
        return {
            "path": path_str or None,
            "checkpoint_sha256": None,
            "status": "UNRESOLVED",
        }

    if not _SHA256_RE.match(sha_str) or sha_str == "0" * 64:
        raise CacheProvenanceError(
            "PROVENANCE_CHECKPOINT_DIGEST_INVALID",
            f"Expected 64-char non-zero lowercase hex SHA-256 digest, got {expected_sha256!r}",
        )

    return {
        "path": path_str or None,
        "checkpoint_sha256": sha_str,
        "status": "RESOLVED",
    }


def build_vision_preprocessing_config(
    config: Any,
    *,
    sampling_fps: float | None = None,
    confidence_threshold_approach: float | None = None,
    confidence_threshold_departure: float | None = None,
    image_size: tuple[int, int] | list[int] | None = None,
    roi_config: Mapping[str, Any] | None = None,
    color_conversion: str = "BGR_to_RGB",
    crop_config: Mapping[str, Any] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract canonical vision preprocessing identity from FrozenExperimentConfig."""
    vis = config.vision
    ckpt_vis = config.checkpoints.vision
    img_sz = list(image_size) if image_size is not None else list(vis.image_size)
    preproc: dict[str, Any] = {
        "sampling_fps": float(
            sampling_fps if sampling_fps is not None else vis.sampling_fps
        ),
        "image_size": [int(img_sz[0]), int(img_sz[1])],
        "confidence_threshold_approach": float(
            confidence_threshold_approach
            if confidence_threshold_approach is not None
            else vis.confidence_threshold_approach
        ),
        "confidence_threshold_departure": float(
            confidence_threshold_departure
            if confidence_threshold_departure is not None
            else vis.confidence_threshold_departure
        ),
        "class_mapping": {
            str(k): str(v) for k, v in sorted(ckpt_vis.class_mapping.items())
        },
        "color_conversion": str(color_conversion),
        "crop_config": dict(crop_config) if crop_config is not None else None,
        "roi_config": _validate_roi_config(roi_config) if roi_config is not None else None,
    }
    if extra:
        for k, v in extra.items():
            preproc[str(k)] = v
    return canonicalize_config(preproc, "preprocessing_config")


def build_audio_preprocessing_config(
    config: Any,
    *,
    sample_rate: int | None = None,
    window_s: float | None = None,
    hop_s: float | None = None,
    operating_threshold: float | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract canonical audio preprocessing identity from FrozenExperimentConfig."""
    aud = config.audio
    preproc: dict[str, Any] = {
        "sample_rate": int(sample_rate if sample_rate is not None else aud.sample_rate),
        "window_s": float(window_s if window_s is not None else aud.window_s),
        "hop_s": float(hop_s if hop_s is not None else aud.hop_s),
        "n_fft": int(aud.n_fft),
        "hop_length": int(aud.hop_length),
        "n_mels": int(aud.n_mels),
        "f_min": float(aud.f_min),
        "f_max": float(aud.f_max),
        "log_scale": "natural",
        "log_epsilon": 1e-10,
        "expected_feature_shape": [
            int(aud.expected_feature_shape[0]),
            int(aud.expected_feature_shape[1]),
        ],
        "operating_threshold": float(
            operating_threshold
            if operating_threshold is not None
            else aud.operating_threshold
        ),
        "normalization": {
            "mean": float(aud.normalization.mean),
            "std": float(aud.normalization.std),
            "source": str(aud.normalization.source),
        },
    }
    if extra:
        for k, v in extra.items():
            preproc[str(k)] = v
    return canonicalize_config(preproc, "preprocessing_config")


def build_injector_provenance(
    scenario_id: str = "none",
    schedules: Sequence[Any] | None = None,
    *,
    injector_version: str = "failure-injector/2.0.0",
    seed: int | None = None,
    modality: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Construct canonical (failure_injector, injector_parameters) from FailureSchedules."""
    clean_scenario = (scenario_id or "none").strip()
    if clean_scenario in ("", "none", "B0", "B1", "B2", "B3", "B4") and not schedules:
        return "none", {}

    if clean_scenario.lower() in ("b7e", "b7e_stale_timestamps", "stale_timestamps") and not schedules:
        raise CacheProvenanceError(
            "PROVENANCE_INJECTOR_INVALID",
            "B7e requires explicit STALE_TIMESTAMPS FailureSchedule with delay_s and target_source",
        )

    serialized_schedules: list[dict[str, Any]] = []
    for sched in schedules or ():
        mode_val = (
            sched.mode.value if hasattr(sched.mode, "value") else str(sched.mode)
        )
        end_t = float(sched.end_time_s)
        end_repr: float | str = "inf" if math.isinf(end_t) and end_t > 0 else end_t
        params = dict(sched.parameters or {})
        target_src = str(sched.target_source or params.get("target_source", "")).strip()
        if mode_val == "stale_timestamps":
            delay_s = params.get("delay_s")
            if (
                isinstance(delay_s, bool)
                or not isinstance(delay_s, (int, float))
                or not math.isfinite(float(delay_s))
                or float(delay_s) <= 0.0
            ):
                raise CacheProvenanceError(
                    "PROVENANCE_INJECTOR_INVALID",
                    "STALE_TIMESTAMPS requires positive finite delay_s",
                )
            if not target_src:
                raise CacheProvenanceError(
                    "PROVENANCE_INJECTOR_INVALID",
                    "STALE_TIMESTAMPS requires non-empty target_source",
                )
        sched_dict: dict[str, Any] = {
            "mode": mode_val,
            "start_time_s": float(sched.start_time_s),
            "end_time_s": end_repr,
            "target_source": target_src,
            "parameters": canonicalize_config(params, "schedule.parameters"),
        }
        serialized_schedules.append(sched_dict)

    out_params: dict[str, Any] = {
        "injector_version": str(injector_version),
        "scenario_id": clean_scenario,
        "schedules": serialized_schedules,
    }
    if seed is not None:
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise CacheProvenanceError(
                "PROVENANCE_INJECTOR_INVALID", "injector seed must be an integer"
            )
        out_params["seed"] = int(seed)
    if modality is not None:
        out_params["modality"] = str(modality)

    if len(serialized_schedules) == 1 and serialized_schedules[0]["mode"] == "stale_timestamps":
        out_params["delay_s"] = float(
            serialized_schedules[0]["parameters"]["delay_s"]
        )
        out_params["target_source"] = str(serialized_schedules[0]["target_source"])

    return clean_scenario, canonicalize_config(out_params, "injector_parameters")


@dataclass(frozen=True)
class ControlledCacheProvenance:
    """Complete 14-field provenance identity for a controlled experimental cache stream."""

    cohort: str
    event_id: str
    source_id: str
    modality: str
    model_architecture: str
    checkpoint_sha256: str
    preprocessing_config: Mapping[str, Any]
    experiment_config_sha256: str
    failure_injector: str
    injector_parameters: Mapping[str, Any]
    timing_config: Mapping[str, Any]
    cache_schema_version: str = CONTROLLED_CACHE_SCHEMA_VERSION
    software_version: str = "0.1.0"
    run_id: str = ""
    cache_classification: str = CONTROLLED_EXPERIMENTAL_CACHE_CLASS
    roi_config: Mapping[str, Any] | None = None
    git_commit: str | None = None
    injector_version: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "cohort",
            "event_id",
            "source_id",
            "modality",
            "model_architecture",
            "checkpoint_sha256",
            "experiment_config_sha256",
            "failure_injector",
            "cache_schema_version",
            "software_version",
            "run_id",
            "cache_classification",
        ):
            val = getattr(self, field_name)
            if not isinstance(val, str) or not val.strip():
                raise CacheProvenanceError(
                    "PROVENANCE_FIELD_MISSING",
                    f"Required provenance string field '{field_name}' must be non-empty",
                )
            _assert_finite_json_value(val, field_name)

        if self.cohort not in VALID_COHORTS:
            raise CacheProvenanceError(
                "PROVENANCE_COHORT_INVALID",
                f"cohort must be one of {sorted(VALID_COHORTS)}, got {self.cohort!r}",
            )
        if self.modality not in VALID_MODALITIES:
            raise CacheProvenanceError(
                "PROVENANCE_MODALITY_INVALID",
                f"modality must be one of {sorted(VALID_MODALITIES)}, got {self.modality!r}",
            )

        ckpt_lower = self.checkpoint_sha256.strip().lower()
        if ckpt_lower in UNRESOLVED_CHECKPOINT_TOKENS:
            raise CacheProvenanceError(
                "PROVENANCE_CHECKPOINT_UNRESOLVED",
                f"checkpoint_sha256 is marked unresolved ({self.checkpoint_sha256!r}); "
                "a missing or unresolved checkpoint cannot masquerade as a valid model.",
            )
        if ckpt_lower == PROHIBITED_AUDIO_V2_SHA256:
            raise CacheProvenanceError(
                "PROHIBITED_CHECKPOINT_REJECTED",
                f"Prohibited Audio V2 checkpoint SHA-256 ({PROHIBITED_AUDIO_V2_SHA256}) is forbidden.",
            )
        if not _SHA256_RE.match(ckpt_lower) or ckpt_lower == "0" * 64:
            raise CacheProvenanceError(
                "PROVENANCE_CHECKPOINT_DIGEST_INVALID",
                f"checkpoint_sha256 must be a non-zero 64-char hex SHA-256 digest, got {self.checkpoint_sha256!r}",
            )

        exp_lower = self.experiment_config_sha256.strip().lower()
        if not _SHA256_RE.match(exp_lower) or exp_lower == "0" * 64:
            raise CacheProvenanceError(
                "PROVENANCE_CONFIG_DIGEST_INVALID",
                f"experiment_config_sha256 must be a non-zero 64-char hex SHA-256 digest, got {self.experiment_config_sha256!r}",
            )
        if self.cache_schema_version != CONTROLLED_CACHE_SCHEMA_VERSION:
            raise CacheProvenanceError(
                "PROVENANCE_SCHEMA_VERSION_INVALID",
                f"cache_schema_version must be {CONTROLLED_CACHE_SCHEMA_VERSION!r}, got {self.cache_schema_version!r}",
            )
        if self.cache_classification != CONTROLLED_EXPERIMENTAL_CACHE_CLASS:
            raise CacheProvenanceError(
                "CACHE_CLASSIFICATION_MISMATCH",
                f"ControlledCacheProvenance requires cache_classification={CONTROLLED_EXPERIMENTAL_CACHE_CLASS!r}, "
                f"got {self.cache_classification!r}. Historical diagnostic or descriptive-only caches "
                "cannot masquerade as controlled experimental caches.",
            )

        for map_field in ("preprocessing_config", "injector_parameters", "timing_config"):
            raw_map = getattr(self, map_field)
            if not isinstance(raw_map, Mapping):
                raise CacheProvenanceError(
                    "PROVENANCE_FIELD_INVALID",
                    f"'{map_field}' must be a mapping, got {type(raw_map).__name__}",
                )
            normalized = _assert_finite_json_value(raw_map, map_field)
            object.__setattr__(self, map_field, normalized)

        if not self.preprocessing_config:
            raise CacheProvenanceError(
                "PROVENANCE_PREPROCESSING_MISSING",
                "preprocessing_config must be a non-empty mapping",
            )
        if not self.timing_config:
            raise CacheProvenanceError(
                "PROVENANCE_TIMING_MISSING",
                "timing_config must be a non-empty mapping",
            )

        # Normalize optional ROI configuration and bind into preprocessing_config
        preproc_copy = dict(self.preprocessing_config)
        if self.roi_config is not None:
            validated_roi = _validate_roi_config(self.roi_config, "roi_config")
            preproc_copy["roi_config"] = validated_roi
            object.__setattr__(self, "roi_config", validated_roi)
            object.__setattr__(self, "preprocessing_config", preproc_copy)
        elif preproc_copy.get("roi_config") is not None:
            validated_roi = _validate_roi_config(
                preproc_copy["roi_config"], "preprocessing_config.roi_config"
            )
            preproc_copy["roi_config"] = validated_roi
            object.__setattr__(self, "roi_config", validated_roi)
            object.__setattr__(self, "preprocessing_config", preproc_copy)

        # Normalize optional injector_version into injector_parameters when provided
        inj_params_copy = dict(self.injector_parameters)
        if self.injector_version is not None:
            if not isinstance(self.injector_version, str) or not self.injector_version.strip():
                raise CacheProvenanceError(
                    "PROVENANCE_INJECTOR_INVALID",
                    "injector_version must be a non-empty string when provided",
                )
            _assert_finite_json_value(self.injector_version, "injector_version")
            inj_params_copy["injector_version"] = self.injector_version.strip()
            object.__setattr__(self, "injector_parameters", _assert_finite_json_value(inj_params_copy, "injector_parameters"))

        # Validate failure injector & B7e contract
        _validate_injector_contract(self.failure_injector, self.injector_parameters)

        # Normalize optional git_commit into software_version if not already embedded
        if self.git_commit is not None:
            if not isinstance(self.git_commit, str) or not self.git_commit.strip():
                raise CacheProvenanceError(
                    "PROVENANCE_FIELD_INVALID",
                    "git_commit must be a non-empty string when provided",
                )
            _assert_finite_json_value(self.git_commit, "git_commit")
            commit_clean = self.git_commit.strip()
            object.__setattr__(self, "git_commit", commit_clean)
            if f"+git.{commit_clean}" not in self.software_version:
                object.__setattr__(
                    self, "software_version", f"{self.software_version}+git.{commit_clean}"
                )

        object.__setattr__(self, "checkpoint_sha256", ckpt_lower)
        object.__setattr__(self, "experiment_config_sha256", exp_lower)

    def configuration_identity_dict(self) -> dict[str, Any]:
        """Return the event-independent and run-independent scientific configuration identity."""
        full = self.identity_dict()
        return {k: full[k] for k in CONFIGURATION_IDENTITY_FIELDS}

    def configuration_sha256(self) -> str:
        """Compute deterministic SHA-256 digest of the scientific & software configuration."""
        return compute_canonical_digest(self.configuration_identity_dict())

    def cache_identity_dict(self) -> dict[str, Any]:
        """Return the stream cache identity (event + cohort + source + modality + config, excluding run_id)."""
        full = self.identity_dict()
        return {k: full[k] for k in CACHE_IDENTITY_FIELDS}

    def cache_identity_sha256(self) -> str:
        """Compute deterministic SHA-256 digest of the stream cache identity (independent of run_id)."""
        return compute_canonical_digest(self.cache_identity_dict())

    def identity_dict(self) -> dict[str, Any]:
        """Return the canonical 14-field identity dictionary."""
        return {
            "cohort": self.cohort,
            "event_id": self.event_id,
            "source_id": self.source_id,
            "modality": self.modality,
            "model_architecture": self.model_architecture,
            "checkpoint_sha256": self.checkpoint_sha256,
            "preprocessing_config": copy.deepcopy(dict(self.preprocessing_config)),
            "experiment_config_sha256": self.experiment_config_sha256,
            "failure_injector": self.failure_injector,
            "injector_parameters": copy.deepcopy(dict(self.injector_parameters)),
            "timing_config": copy.deepcopy(dict(self.timing_config)),
            "cache_schema_version": self.cache_schema_version,
            "software_version": self.software_version,
            "run_id": self.run_id,
        }

    def provenance_sha256(self) -> str:
        """Compute deterministic SHA-256 digest over all 14 identity fields (including run_id)."""
        return compute_canonical_digest(self.identity_dict())

    def validate(self) -> ControlledCacheProvenance:
        """Re-validate this ControlledCacheProvenance instance."""
        self.__post_init__()
        return self

    def cache_key(self) -> str:
        """Return deterministic cache key incorporating identity and provenance digest."""
        safe_event = self.event_id.replace("/", "__")
        digest_prefix = self.provenance_sha256()[:16]
        return f"{self.cohort}__{safe_event}__{self.source_id}__{self.modality}__{digest_prefix}"

    def cache_filename(self) -> str:
        """Return deterministic JSONL filename for this controlled cache stream."""
        return f"{self.cache_key()}.jsonl"

    def to_dict(self) -> dict[str, Any]:
        """Serialize full provenance record including multi-level digests and classification."""
        payload = self.identity_dict()
        payload["canonicalization_version"] = CANONICAL_SERIALIZATION_VERSION
        payload["cache_classification"] = self.cache_classification
        payload["official_evaluation_eligible"] = False
        payload["configuration_sha256"] = self.configuration_sha256()
        payload["cache_identity_sha256"] = self.cache_identity_sha256()
        payload["provenance_sha256"] = self.provenance_sha256()
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ControlledCacheProvenance:
        """Validate and construct ControlledCacheProvenance from a serialized dict."""
        if not isinstance(data, Mapping):
            raise CacheProvenanceError(
                "PROVENANCE_HEADER_INVALID", "Provenance header must be a JSON object"
            )
        missing = [f for f in REQUIRED_PROVENANCE_FIELDS if f not in data]
        if missing:
            raise CacheProvenanceError(
                "PROVENANCE_FIELD_MISSING",
                f"Provenance header missing required field(s): {missing}",
            )
        canon_ver = data.get("canonicalization_version")
        if canon_ver is not None and canon_ver != CANONICAL_SERIALIZATION_VERSION:
            raise CacheProvenanceError(
                "PROVENANCE_SCHEMA_VERSION_INVALID",
                f"Unsupported canonicalization_version {canon_ver!r}, expected {CANONICAL_SERIALIZATION_VERSION!r}",
            )
        classification = data.get(
            "cache_classification", CONTROLLED_EXPERIMENTAL_CACHE_CLASS
        )
        instance = cls(
            cohort=data["cohort"],
            event_id=data["event_id"],
            source_id=data["source_id"],
            modality=data["modality"],
            model_architecture=data["model_architecture"],
            checkpoint_sha256=data["checkpoint_sha256"],
            preprocessing_config=data["preprocessing_config"],
            experiment_config_sha256=data["experiment_config_sha256"],
            failure_injector=data["failure_injector"],
            injector_parameters=data["injector_parameters"],
            timing_config=data["timing_config"],
            cache_schema_version=data["cache_schema_version"],
            software_version=data["software_version"],
            run_id=data["run_id"],
            cache_classification=classification,
        )
        recorded_sha = data.get("provenance_sha256")
        if recorded_sha is not None and recorded_sha != instance.provenance_sha256():
            raise CacheProvenanceError(
                "PROVENANCE_DIGEST_MISMATCH",
                f"Recorded provenance_sha256 {recorded_sha!r} does not match recomputed "
                f"digest {instance.provenance_sha256()!r}",
            )
        recorded_cfg_sha = data.get("configuration_sha256")
        if (
            recorded_cfg_sha is not None
            and recorded_cfg_sha != instance.configuration_sha256()
        ):
            raise CacheProvenanceError(
                "PROVENANCE_DIGEST_MISMATCH",
                f"Recorded configuration_sha256 {recorded_cfg_sha!r} does not match recomputed "
                f"digest {instance.configuration_sha256()!r}",
            )
        recorded_cache_id_sha = data.get("cache_identity_sha256")
        if (
            recorded_cache_id_sha is not None
            and recorded_cache_id_sha != instance.cache_identity_sha256()
        ):
            raise CacheProvenanceError(
                "PROVENANCE_DIGEST_MISMATCH",
                f"Recorded cache_identity_sha256 {recorded_cache_id_sha!r} does not match recomputed "
                f"digest {instance.cache_identity_sha256()!r}",
            )
        return instance


def validate_controlled_cache_provenance(
    actual: Mapping[str, Any] | ControlledCacheProvenance,
    expected: ControlledCacheProvenance,
    *,
    reuse_policy: str = CACHE_REUSE_ISOLATED_RUN,
) -> ControlledCacheProvenance:
    """Validate that a loaded cache provenance header matches expected identity under reuse_policy."""
    if reuse_policy not in VALID_CACHE_REUSE_POLICIES:
        raise CacheProvenanceError(
            "CACHE_REUSE_POLICY_INVALID",
            f"Unsupported reuse_policy {reuse_policy!r}; must be one of {sorted(VALID_CACHE_REUSE_POLICIES)}",
        )
    parsed = (
        actual
        if isinstance(actual, ControlledCacheProvenance)
        else ControlledCacheProvenance.from_dict(actual)
    )
    actual_id = parsed.identity_dict()
    expected_id = expected.identity_dict()

    fields_to_check = (
        REQUIRED_PROVENANCE_FIELDS
        if reuse_policy == CACHE_REUSE_ISOLATED_RUN
        else CACHE_IDENTITY_FIELDS
    )
    mismatched = [
        field_name
        for field_name in fields_to_check
        if actual_id.get(field_name) != expected_id.get(field_name)
    ]
    if mismatched:
        raise CacheProvenanceError(
            "PROVENANCE_MISMATCH",
            f"Controlled cache provenance mismatch on field(s) {mismatched}: "
            f"expected { {k: expected_id[k] for k in mismatched} }, "
            f"got { {k: actual_id[k] for k in mismatched} }",
        )
    if parsed.cache_identity_sha256() != expected.cache_identity_sha256():
        raise CacheProvenanceError(
            "PROVENANCE_DIGEST_MISMATCH",
            "Controlled cache stream identity SHA-256 digest mismatch",
        )
    if (
        reuse_policy == CACHE_REUSE_ISOLATED_RUN
        and parsed.provenance_sha256() != expected.provenance_sha256()
    ):
        raise CacheProvenanceError(
            "PROVENANCE_DIGEST_MISMATCH",
            "Controlled cache provenance SHA-256 digest mismatch",
        )
    return parsed


def _serialize_record(record: EvidenceRecord) -> dict[str, Any]:
    ts = float(record.timestamp_s)
    if not math.isfinite(ts):
        raise CacheProvenanceError(
            "PROVENANCE_NONFINITE_NUMBER",
            f"EvidenceRecord timestamp_s must be finite, got {record.timestamp_s!r}",
        )
    dets_out: list[dict[str, Any]] = []
    for idx, d in enumerate(record.detections):
        conf = float(d.confidence)
        if not math.isfinite(conf) or conf < 0.0 or conf > 1.0:
            raise CacheProvenanceError(
                "RECORD_DETECTION_INVALID",
                f"Detection[{idx}] confidence must be finite in [0.0, 1.0], got {d.confidence!r}",
            )
        dets_out.append(
            {
                "label": str(d.label),
                "confidence": conf,
                "bbox_xyxy": [float(c) for c in d.bbox_xyxy] if d.bbox_xyxy else None,
                "metadata": _assert_finite_json_value(
                    dict(d.metadata or {}), f"detection[{idx}].metadata"
                ),
            }
        )
    return {
        "timestamp_s": 0.0 if ts == 0.0 else ts,
        "source_id": str(record.source_id),
        "modality": (
            record.modality.value
            if isinstance(record.modality, Modality)
            else str(record.modality)
        ),
        "available": bool(record.available),
        "detections": dets_out,
        "metadata": _assert_finite_json_value(
            dict(record.metadata or {}), "record.metadata"
        ),
    }


def _deserialize_record(data: Mapping[str, Any], *, line_no: int = 0) -> EvidenceRecord:
    if not isinstance(data, Mapping):
        raise CacheProvenanceError(
            "CACHE_MALFORMED_RECORD",
            f"Line {line_no}: record must be a JSON object",
        )
    for req_key in ("timestamp_s", "source_id", "modality", "available"):
        if req_key not in data:
            raise CacheProvenanceError(
                "CACHE_MALFORMED_RECORD",
                f"Line {line_no}: record missing required key {req_key!r}",
            )
    ts_raw = data["timestamp_s"]
    if isinstance(ts_raw, bool) or not isinstance(ts_raw, (int, float)) or not math.isfinite(float(ts_raw)):
        raise CacheProvenanceError(
            "PROVENANCE_NONFINITE_NUMBER",
            f"Line {line_no}: invalid timestamp_s {ts_raw!r}",
        )
    dets: list[Detection] = []
    for idx, d in enumerate(data.get("detections", [])):
        if not isinstance(d, Mapping) or "label" not in d or "confidence" not in d:
            raise CacheProvenanceError(
                "CACHE_MALFORMED_RECORD",
                f"Line {line_no}: malformed detection at index {idx}",
            )
        conf_raw = d["confidence"]
        if (
            isinstance(conf_raw, bool)
            or not isinstance(conf_raw, (int, float))
            or not math.isfinite(float(conf_raw))
            or float(conf_raw) < 0.0
            or float(conf_raw) > 1.0
        ):
            raise CacheProvenanceError(
                "RECORD_DETECTION_INVALID",
                f"Line {line_no}: detection[{idx}] confidence out of range: {conf_raw!r}",
            )
        dets.append(
            Detection(
                label=str(d["label"]),
                confidence=float(conf_raw),
                bbox_xyxy=tuple(float(c) for c in d["bbox_xyxy"]) if d.get("bbox_xyxy") else None,
                metadata=_assert_finite_json_value(
                    dict(d.get("metadata", {})), f"line[{line_no}].detection[{idx}].metadata"
                ),
            )
        )
    meta = _assert_finite_json_value(
        dict(data.get("metadata", {})), f"line[{line_no}].metadata"
    )
    return EvidenceRecord(
        timestamp_s=float(ts_raw),
        source_id=str(data["source_id"]),
        modality=Modality(data["modality"]),
        available=bool(data["available"]),
        detections=tuple(dets),
        metadata=meta,
    )


serialize_evidence_record = _serialize_record
deserialize_evidence_record = _deserialize_record


def compute_records_payload_sha256(serialized_record_lines: Sequence[str]) -> str:
    """Compute deterministic SHA-256 digest over the canonical JSONL record lines."""
    joined = "\n".join(serialized_record_lines)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def write_controlled_cache_jsonl(
    cache_dir: Path,
    provenance: ControlledCacheProvenance,
    records: Sequence[EvidenceRecord],
) -> Path:
    """Write a provenance-bound controlled experimental cache JSONL file with payload integrity."""
    if not isinstance(provenance, ControlledCacheProvenance):
        raise CacheProvenanceError(
            "PROVENANCE_REQUIRED",
            "write_controlled_cache_jsonl requires a validated ControlledCacheProvenance",
        )
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / provenance.cache_filename()

    record_lines: list[str] = []
    for idx, rec in enumerate(records):
        if rec.source_id != provenance.source_id:
            raise CacheProvenanceError(
                "RECORD_SOURCE_MISMATCH",
                f"Record {idx} source_id {rec.source_id!r} != provenance.source_id {provenance.source_id!r}",
            )
        rec_mod = (
            rec.modality.value if isinstance(rec.modality, Modality) else str(rec.modality)
        )
        if rec_mod != provenance.modality:
            raise CacheProvenanceError(
                "RECORD_MODALITY_MISMATCH",
                f"Record {idx} modality {rec_mod!r} != provenance.modality {provenance.modality!r}",
            )
        record_lines.append(canonical_json_str(_serialize_record(rec)))

    payload_sha256 = compute_records_payload_sha256(record_lines)
    header_dict = provenance.to_dict()
    header_dict["record_count"] = len(record_lines)
    header_dict["payload_sha256"] = payload_sha256
    envelope = {PROVENANCE_ENVELOPE_KEY: header_dict}

    lines = [canonical_json_str(envelope), *record_lines]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def load_controlled_cache_jsonl(
    cache_path: Path,
    expected_provenance: ControlledCacheProvenance,
    *,
    reuse_policy: str = CACHE_REUSE_ISOLATED_RUN,
) -> list[EvidenceRecord]:
    """Load and strictly verify a provenance-bound controlled experimental cache JSONL file."""
    if not isinstance(expected_provenance, ControlledCacheProvenance):
        raise CacheProvenanceError(
            "PROVENANCE_REQUIRED",
            "load_controlled_cache_jsonl requires an expected ControlledCacheProvenance",
        )
    if not cache_path.is_file():
        raise CacheProvenanceError(
            "CACHE_MISSING", f"Controlled cache file does not exist: {cache_path}"
        )
    raw_lines = [
        line.strip()
        for line in cache_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not raw_lines:
        raise CacheProvenanceError(
            "CACHE_EMPTY", f"Controlled cache file is empty: {cache_path}"
        )

    first_obj = _loads_strict_json(raw_lines[0], context=f"line 1 of {cache_path}")

    if not isinstance(first_obj, dict) or PROVENANCE_ENVELOPE_KEY not in first_obj:
        raise CacheProvenanceError(
            "HISTORICAL_UNVERIFIED_CACHE_REJECTED",
            f"Cache file {cache_path.name} lacks a '{PROVENANCE_ENVELOPE_KEY}' provenance "
            "header. Historical diagnostic caches cannot be loaded as provenance-verified "
            "controlled experimental caches.",
        )

    header = first_obj[PROVENANCE_ENVELOPE_KEY]
    verified_prov = validate_controlled_cache_provenance(
        header, expected_provenance, reuse_policy=reuse_policy
    )

    body_lines = raw_lines[1:]
    if isinstance(header, Mapping) and "record_count" in header:
        expected_count = header["record_count"]
        if (
            isinstance(expected_count, bool)
            or not isinstance(expected_count, int)
            or expected_count != len(body_lines)
        ):
            raise CacheProvenanceError(
                "CACHE_PAYLOAD_CORRUPTED",
                f"Record count mismatch in {cache_path.name}: header declares "
                f"{expected_count}, found {len(body_lines)} record line(s)",
            )

    records: list[EvidenceRecord] = []
    canonical_body_lines: list[str] = []
    for line_no, raw_line in enumerate(body_lines, start=2):
        obj = _loads_strict_json(raw_line, context=f"line {line_no} of {cache_path}")
        rec = _deserialize_record(obj, line_no=line_no)
        if rec.source_id != verified_prov.source_id:
            raise CacheProvenanceError(
                "RECORD_SOURCE_MISMATCH",
                f"Line {line_no}: record source_id {rec.source_id!r} != provenance {verified_prov.source_id!r}",
            )
        rec_mod = (
            rec.modality.value if isinstance(rec.modality, Modality) else str(rec.modality)
        )
        if rec_mod != verified_prov.modality:
            raise CacheProvenanceError(
                "RECORD_MODALITY_MISMATCH",
                f"Line {line_no}: record modality {rec_mod!r} != provenance {verified_prov.modality!r}",
            )
        records.append(rec)
        canonical_body_lines.append(canonical_json_str(_serialize_record(rec)))

    if isinstance(header, Mapping) and "payload_sha256" in header:
        recorded_payload_sha = header["payload_sha256"]
        actual_raw_sha = compute_records_payload_sha256(body_lines)
        actual_canon_sha = compute_records_payload_sha256(canonical_body_lines)
        if (
            not isinstance(recorded_payload_sha, str)
            or recorded_payload_sha != actual_raw_sha
            or recorded_payload_sha != actual_canon_sha
        ):
            raise CacheProvenanceError(
                "CACHE_PAYLOAD_CORRUPTED",
                f"Payload SHA-256 mismatch in {cache_path.name}: recorded "
                f"{recorded_payload_sha!r}, computed {actual_canon_sha!r}",
            )

    return records


def load_historical_diagnostic_cache_jsonl(
    cache_path: Path,
) -> tuple[list[EvidenceRecord], dict[str, Any]]:
    """Explicit historical diagnostic loader for legacy unverified JSONL caches.

    Tags all returned records and metadata as historical diagnostic only
    (HISTORICAL_DIAGNOSTIC_UNVERIFIED), never eligible for controlled experimental
    verification or official evaluation.
    """
    if not cache_path.is_file():
        raise CacheProvenanceError(
            "CACHE_MISSING", f"Historical cache file does not exist: {cache_path}"
        )
    raw_lines = [
        line.strip()
        for line in cache_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    records: list[EvidenceRecord] = []
    for line_no, raw_line in enumerate(raw_lines, start=1):
        obj = _loads_strict_json(raw_line, context=f"line {line_no} of {cache_path}")
        if isinstance(obj, dict) and PROVENANCE_ENVELOPE_KEY in obj:
            continue
        rec = _deserialize_record(obj, line_no=line_no)
        meta = dict(rec.metadata)
        meta["cache_classification"] = HISTORICAL_DIAGNOSTIC_CACHE_CLASS
        meta["provenance_status"] = "HISTORICAL_DIAGNOSTIC_UNVERIFIED"
        meta["controlled_run_verified"] = False
        meta["official_evaluation_eligible"] = False
        records.append(
            EvidenceRecord(
                timestamp_s=rec.timestamp_s,
                source_id=rec.source_id,
                modality=rec.modality,
                available=rec.available,
                detections=rec.detections,
                metadata=meta,
            )
        )
    diagnostic_meta = {
        "cache_path": str(cache_path),
        "cache_classification": HISTORICAL_DIAGNOSTIC_CACHE_CLASS,
        "provenance_status": "HISTORICAL_DIAGNOSTIC_UNVERIFIED",
        "controlled_run_verified": False,
        "official_evaluation_eligible": False,
        "record_count": len(records),
    }
    return records, diagnostic_meta
