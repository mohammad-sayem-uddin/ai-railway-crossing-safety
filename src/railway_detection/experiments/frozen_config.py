"""Authoritative frozen experiment configuration loader and runtime safeguards.

Enforces:
1. Deterministic canonical SHA-256 configuration hashing (excluding the hash field itself).
2. Strict verification of Vision and Audio V3 checkpoint hashes.
3. Hard prohibition and rejection of legacy Audio V2 checkpoint (by path and by hash).
4. Audio V3 threshold (0.3700) and normalization contracts.
5. Explicit blocking of unverified zero-offset cross-camera synchronization (R04).
6. Traceable, explicit experiment condition overrides without silent base mutation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from railway_detection.utils.logging import get_logger

logger = get_logger("experiments.frozen_config")

# Canonical reference checkpoint hashes
EXPECTED_VISION_SHA256 = (
    "3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd"
)
EXPECTED_AUDIO_V3_SHA256 = (
    "ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782"
)
PROHIBITED_AUDIO_V2_SHA256 = (
    "59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5"
)
PROHIBITED_AUDIO_V2_PATH = "models/audio/best_checkpoint.pt"

DEFAULT_CONFIG_PATH = Path("configs/frozen_experiment_v1.yaml")


class ConfigurationIntegrityError(ValueError):
    """Raised when configuration values violate frozen specifications or schemas."""


class CheckpointIntegrityError(RuntimeError):
    """Raised when model checkpoint files are missing, mutated, or unauthorized."""


class ProhibitedCheckpointError(CheckpointIntegrityError):
    """Raised when an attempt is made to reference or load a prohibited checkpoint (e.g. Audio V2)."""


class TimingIntegrityError(ConfigurationIntegrityError):
    """Raised when cross-camera timing violates synchronization constraints (R04)."""


@dataclass(frozen=True)
class ExperimentMetadataConfig:
    name: str
    version: str
    description: str
    seed: int
    device: str
    condition: str | None = None
    scenario_id: str | None = None


@dataclass(frozen=True)
class VisionCheckpointConfig:
    path: str
    expected_sha256: str
    model_name: str
    class_mapping: dict[int, str]


@dataclass(frozen=True)
class AudioV3CheckpointConfig:
    path: str
    expected_sha256: str
    model_name: str
    operating_threshold: float


@dataclass(frozen=True)
class ProhibitedCheckpointConfig:
    path: str
    sha256: str


@dataclass(frozen=True)
class CheckpointsConfig:
    vision: VisionCheckpointConfig
    audio_v3: AudioV3CheckpointConfig
    prohibited_audio_v2: ProhibitedCheckpointConfig


@dataclass(frozen=True)
class AudioNormalizationConfig:
    mean: float
    std: float
    source: str


@dataclass(frozen=True)
class AudioConfig:
    sample_rate: int
    window_s: float
    hop_s: float
    n_fft: int
    hop_length: int
    n_mels: int
    f_min: float
    f_max: float
    expected_feature_shape: tuple[int, int]
    operating_threshold: float
    normalization: AudioNormalizationConfig


@dataclass(frozen=True)
class VisionConfig:
    sampling_fps: float
    image_size: tuple[int, int]
    confidence_threshold_approach: float
    confidence_threshold_departure: float


@dataclass(frozen=True)
class CrossCameraSyncConfig:
    mode: str
    status: str
    allow_unverified_zero_offset: bool


@dataclass(frozen=True)
class TimingConfig:
    tick_s: float
    confirm_frames: int
    miss_tolerance_frames: int
    warning_dwell_s: float
    gate_closing_s: float
    gate_opening_s: float
    clearance_dwell_s: float
    source_staleness_s: float
    fault_confirmation_frames: int
    fault_recovery_hold_s: float
    cross_camera_sync: CrossCameraSyncConfig

    @property
    def gate_closing_time_s(self) -> float:
        return self.gate_closing_s

    @property
    def gate_opening_time_s(self) -> float:
        return self.gate_opening_s


@dataclass(frozen=True)
class FrozenExperimentConfig:
    """Immutable authoritative experiment configuration with cryptographic integrity."""

    experiment: ExperimentMetadataConfig
    checkpoints: CheckpointsConfig
    audio: AudioConfig
    vision: VisionConfig
    timing: TimingConfig
    canonical_hash: str
    raw_dict: dict[str, Any]
    condition_overrides: dict[str, Any] = field(default_factory=dict)

    @property
    def config_hash(self) -> str:
        return self.canonical_hash

    @property
    def metadata(self) -> ExperimentMetadataConfig:
        return self.experiment

    def verify_all_safeguards(
        self, repo_root: Path | str = ".", *, vision_only: bool = False
    ) -> None:
        """Execute full battery of checkpoint integrity and timing checks."""
        if vision_only:
            verify_checkpoint_integrity(self, repo_root=repo_root, vision_only=True)
        else:
            verify_checkpoint_integrity(self, repo_root=repo_root)
        verify_timing_safeguards(self)


def compute_file_sha256(path: Path | str) -> str:
    """Compute SHA-256 hexadecimal digest for a file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found for SHA-256 calculation: {p}")
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def compute_canonical_config_hash(payload: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash using canonical JSON serialization.

    The hash field itself (if present) is excluded from the payload before hashing.
    """
    clean_dict = _clean_payload_for_hashing(payload)
    canonical_json = json.dumps(clean_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def _clean_payload_for_hashing(item: Any) -> Any:
    if isinstance(item, dict):
        return {
            k: _clean_payload_for_hashing(v)
            for k, v in item.items()
            if k not in ("canonical_hash", "config_hash")
        }
    if isinstance(item, (list, tuple)):
        return [_clean_payload_for_hashing(x) for x in item]
    return item


def parse_config_dict(
    raw: dict[str, Any], condition_overrides: dict[str, Any] | None = None
) -> FrozenExperimentConfig:
    """Parse a validated configuration dictionary into a FrozenExperimentConfig."""
    # Validate required sections
    for sec in ("experiment", "checkpoints", "audio", "vision", "timing"):
        if sec not in raw:
            raise ConfigurationIntegrityError(f"Missing required configuration section: '{sec}'")

    # Experiment metadata
    exp_raw = raw["experiment"]
    for field_name in ("name", "version", "description", "seed", "device"):
        if field_name not in exp_raw:
            raise ConfigurationIntegrityError(f"Missing field in experiment: '{field_name}'")
    exp_cfg = ExperimentMetadataConfig(
        name=str(exp_raw["name"]),
        version=str(exp_raw["version"]),
        description=str(exp_raw["description"]),
        seed=int(exp_raw["seed"]),
        device=str(exp_raw["device"]),
        condition=str(exp_raw.get("condition")) if exp_raw.get("condition") else None,
        scenario_id=str(exp_raw.get("scenario_id")) if exp_raw.get("scenario_id") else None,
    )

    # Checkpoints
    ckpt_raw = raw["checkpoints"]
    if "vision" not in ckpt_raw or "audio_v3" not in ckpt_raw or "prohibited" not in ckpt_raw:
        raise ConfigurationIntegrityError("checkpoints section missing vision, audio_v3, or prohibited")

    v_raw = ckpt_raw["vision"]
    class_map = {int(k): str(v) for k, v in v_raw.get("class_mapping", {}).items()}
    v_ckpt = VisionCheckpointConfig(
        path=str(v_raw["path"]),
        expected_sha256=str(v_raw["expected_sha256"]),
        model_name=str(v_raw.get("model_name", "YOLOv8n")),
        class_mapping=class_map,
    )

    a_raw = ckpt_raw["audio_v3"]
    a_ckpt = AudioV3CheckpointConfig(
        path=str(a_raw["path"]),
        expected_sha256=str(a_raw["expected_sha256"]),
        model_name=str(a_raw.get("model_name", "CompactTrainHornCNN")),
        operating_threshold=float(a_raw["operating_threshold"]),
    )

    prohib_raw = ckpt_raw["prohibited"].get("audio_v2", {})
    prohib_ckpt = ProhibitedCheckpointConfig(
        path=str(prohib_raw.get("path", PROHIBITED_AUDIO_V2_PATH)),
        sha256=str(prohib_raw.get("sha256", PROHIBITED_AUDIO_V2_SHA256)),
    )

    ckpts_cfg = CheckpointsConfig(
        vision=v_ckpt,
        audio_v3=a_ckpt,
        prohibited_audio_v2=prohib_ckpt,
    )

    # Audio preprocessing
    aud_raw = raw["audio"]
    norm_raw = aud_raw.get("normalization", {})
    norm_cfg = AudioNormalizationConfig(
        mean=float(norm_raw.get("mean", -1.600999355316162)),
        std=float(norm_raw.get("std", 5.1239728927612305)),
        source=str(norm_raw.get("source", "checkpoint")),
    )
    shape_raw = aud_raw.get("expected_feature_shape", [64, 61])
    aud_cfg = AudioConfig(
        sample_rate=int(aud_raw["sample_rate"]),
        window_s=float(aud_raw["window_s"]),
        hop_s=float(aud_raw["hop_s"]),
        n_fft=int(aud_raw["n_fft"]),
        hop_length=int(aud_raw["hop_length"]),
        n_mels=int(aud_raw["n_mels"]),
        f_min=float(aud_raw["f_min"]),
        f_max=float(aud_raw["f_max"]),
        expected_feature_shape=(int(shape_raw[0]), int(shape_raw[1])),
        operating_threshold=float(aud_raw["operating_threshold"]),
        normalization=norm_cfg,
    )

    # Vision preprocessing
    vis_raw = raw["vision"]
    img_size = vis_raw.get("image_size", [640, 640])
    vis_cfg = VisionConfig(
        sampling_fps=float(vis_raw["sampling_fps"]),
        image_size=(int(img_size[0]), int(img_size[1])),
        confidence_threshold_approach=float(vis_raw["confidence_threshold_approach"]),
        confidence_threshold_departure=float(vis_raw["confidence_threshold_departure"]),
    )

    # Timing policy
    tim_raw = raw["timing"]
    sync_raw = tim_raw.get("cross_camera_sync", {})
    sync_cfg = CrossCameraSyncConfig(
        mode=str(sync_raw.get("mode", "independent_or_unverified")),
        status=str(sync_raw.get("status", "R04_UNRESOLVED")),
        allow_unverified_zero_offset=bool(sync_raw.get("allow_unverified_zero_offset", False)),
    )
    tim_cfg = TimingConfig(
        tick_s=float(tim_raw["tick_s"]),
        confirm_frames=int(tim_raw["confirm_frames"]),
        miss_tolerance_frames=int(tim_raw["miss_tolerance_frames"]),
        warning_dwell_s=float(tim_raw["warning_dwell_s"]),
        gate_closing_s=float(tim_raw["gate_closing_s"]),
        gate_opening_s=float(tim_raw["gate_opening_s"]),
        clearance_dwell_s=float(tim_raw["clearance_dwell_s"]),
        source_staleness_s=float(tim_raw["source_staleness_s"]),
        fault_confirmation_frames=int(tim_raw["fault_confirmation_frames"]),
        fault_recovery_hold_s=float(tim_raw["fault_recovery_hold_s"]),
        cross_camera_sync=sync_cfg,
    )

    canonical_hash = compute_canonical_config_hash(raw)

    return FrozenExperimentConfig(
        experiment=exp_cfg,
        checkpoints=ckpts_cfg,
        audio=aud_cfg,
        vision=vis_cfg,
        timing=tim_cfg,
        canonical_hash=canonical_hash,
        raw_dict=raw,
        condition_overrides=dict(condition_overrides or {}),
    )


def load_frozen_config(config_path: Path | str | None = None) -> FrozenExperimentConfig:
    """Load, validate, and compute the canonical hash of the frozen experiment configuration."""
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Frozen configuration file missing: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ConfigurationIntegrityError(f"Configuration file at {path} must parse to a dictionary")

    return parse_config_dict(raw)


def verify_checkpoint_integrity(
    config: FrozenExperimentConfig, repo_root: Path | str = ".", *, vision_only: bool = False
) -> None:
    """Strictly verify checkpoint presence, expected hashes, and hard prohibition of Audio V2."""
    root = Path(repo_root)

    # 0. Check configured paths and expected hashes against prohibited Audio V2
    prohibited_hash = config.checkpoints.prohibited_audio_v2.sha256
    prohibited_path = root / config.checkpoints.prohibited_audio_v2.path

    if (
        config.checkpoints.vision.expected_sha256 == prohibited_hash
        or config.checkpoints.audio_v3.expected_sha256 == prohibited_hash
        or config.checkpoints.audio_v3.path == config.checkpoints.prohibited_audio_v2.path
        or "models/audio" in config.checkpoints.audio_v3.path
    ):
        raise ProhibitedCheckpointError(
            f"FATAL: Prohibited Audio V2 checkpoint hash ({prohibited_hash}) or path detected in configuration!"
        )

    # 1. Vision checkpoint verification
    v_path = root / config.checkpoints.vision.path
    if not v_path.exists():
        raise CheckpointIntegrityError(f"Frozen YOLO vision checkpoint missing: {v_path}")
    v_hash = compute_file_sha256(v_path)
    if v_hash != config.checkpoints.vision.expected_sha256:
        raise CheckpointIntegrityError(
            f"YOLO vision checkpoint SHA-256 mismatch! "
            f"Expected {config.checkpoints.vision.expected_sha256}, got {v_hash}"
        )

    if vision_only:
        # A visual-only run must not open unrelated audio or retired weights.
        return

    # 2. Audio V3 checkpoint verification
    a_path = root / config.checkpoints.audio_v3.path
    if not a_path.exists():
        raise CheckpointIntegrityError(f"Frozen Audio V3 checkpoint missing: {a_path}")
    a_hash = compute_file_sha256(a_path)
    if a_hash != config.checkpoints.audio_v3.expected_sha256:
        raise CheckpointIntegrityError(
            f"Audio V3 checkpoint SHA-256 mismatch! "
            f"Expected {config.checkpoints.audio_v3.expected_sha256}, got {a_hash}"
        )

    # 3. Audio V2 hard prohibition check
    prohibited_hash = config.checkpoints.prohibited_audio_v2.sha256
    prohibited_path = root / config.checkpoints.prohibited_audio_v2.path

    if v_hash == prohibited_hash or a_hash == prohibited_hash:
        raise ProhibitedCheckpointError(
            f"FATAL: Prohibited Audio V2 checkpoint hash ({prohibited_hash}) detected in configured checkpoints!"
        )

    # Also check if prohibited checkpoint file exists and verify its prohibited identity
    if prohibited_path.exists():
        p_hash = compute_file_sha256(prohibited_path)
        if p_hash != prohibited_hash:
            logger.warning(
                "Prohibited checkpoint on disk has unexpected hash: %s (expected %s)",
                p_hash,
                prohibited_hash,
            )

    # 4. Threshold invariant
    if abs(config.audio.operating_threshold - 0.3700) > 1e-6:
        raise ConfigurationIntegrityError(
            f"Audio operating threshold violation: {config.audio.operating_threshold} != 0.3700"
        )


def verify_timing_safeguards(config: FrozenExperimentConfig) -> None:
    """Enforce R04 timing constraints: prevent unverified zero-offset cross-camera temporal fusion."""
    sync = config.timing.cross_camera_sync
    if sync.allow_unverified_zero_offset:
        raise TimingIntegrityError(
            "CRITICAL: Unverified zero-offset cross-camera synchronization (R04) cannot be enabled. "
            "Front and back camera start times differ by up to 33 seconds. "
            "Temporal fusion across cameras is blocked until justified empirical offsets exist."
        )


def create_condition_config(
    base_config: FrozenExperimentConfig,
    condition_name: str,
    scenario_id: str | None = None,
    overrides: dict[str, Any] | None = None,
) -> FrozenExperimentConfig:
    """Create an explicitly derived condition configuration, logging overrides without mutating base."""
    import copy

    if isinstance(scenario_id, dict) and overrides is None:
        actual_overrides = scenario_id
        actual_scenario_id = condition_name
    else:
        actual_overrides = overrides or {}
        actual_scenario_id = scenario_id or condition_name

    new_dict = copy.deepcopy(base_config.raw_dict)
    new_dict["experiment"]["condition"] = condition_name
    new_dict["experiment"]["scenario_id"] = actual_scenario_id

    if actual_overrides:
        logger.info(
            "Applying explicit condition overrides for %s (%s): %s",
            condition_name,
            actual_scenario_id,
            actual_overrides,
        )
        for k, v in actual_overrides.items():
            keys = k.split(".")
            d = new_dict
            for sub_k in keys[:-1]:
                d = d.setdefault(sub_k, {})
            d[keys[-1]] = v

    condition_hash = compute_canonical_config_hash(new_dict)
    new_dict["canonical_hash"] = condition_hash

    return parse_config_dict(new_dict, condition_overrides=actual_overrides)
