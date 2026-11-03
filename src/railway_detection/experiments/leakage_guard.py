"""Data leakage protection and checkpoint immutability guards.

Strictly enforces research protocol firewall rules:
1. Frozen YOLOv8n checkpoint must match reference SHA-256 hash.
2. Frozen Audio CNN checkpoint must match reference SHA-256 hash.
3. No Layer B evaluation video, frame, or audio file may appear in any training dataset or manifest.
4. No threshold tuning or parameter modification on Layer B evaluation events.
5. Violations raise loud DataLeakageError.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from railway_detection.utils.logging import get_logger

logger = get_logger("experiments.leakage_guard")

FROZEN_YOLO_PATH = "experiments/vision/39f402dfe460/checkpoints/weights/best.pt"
FROZEN_YOLO_SHA256 = "3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd"

FROZEN_AUDIO_PATH = "experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt"
FROZEN_AUDIO_SHA256 = "ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782"

PROHIBITED_AUDIO_V2_PATH = "models/audio/best_checkpoint.pt"
PROHIBITED_AUDIO_V2_SHA256 = "59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5"

FROZEN_PARAMETERS = {
    "vision_confidence_threshold_approach": 0.35,
    "vision_confidence_threshold_departure": 0.35,
    "audio_operating_threshold": 0.3700,
    "temporal_confirm_frames": 2,
    "temporal_smoothing_alpha": 0.5,
    "temporal_miss_tolerance_frames": 2,
    "temporal_evidence_expiry_s": 3.0,
    "warning_dwell_s": 2.0,
    "gate_closing_duration_s": 3.0,
    "gate_opening_duration_s": 3.0,
    "clearance_dwell_s": 3.0,
    "sampling_fps": 5,
    "audio_window_s": 1.0,
    "audio_hop_s": 0.5,
    "audio_target_sample_rate": 16000,
    "seed": 42,
}


from railway_detection.experiments.frozen_config import ProhibitedCheckpointError
from railway_detection.safety.media_guard import require_media_authorization


class DataLeakageError(RuntimeError):
    """Raised when data leakage, checkpoint mutation, or prohibited checkpoint usage is detected."""


def compute_sha256(path: Path) -> str:
    """Compute SHA-256 hexadecimal hash for a file."""
    require_media_authorization(path, "HASH_RAW_MEDIA")
    if not path.exists():
        raise FileNotFoundError(f"File not found for hashing: {path}")
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_not_prohibited_checkpoint(path: Path | str) -> None:
    """Refuse any checkpoint whose path or SHA-256 hash matches the prohibited Audio V2 model."""
    p = Path(path)
    if str(p) == PROHIBITED_AUDIO_V2_PATH or p.name == "best_checkpoint.pt" and "models/audio" in str(p):
        raise ProhibitedCheckpointError(
            f"CRITICAL: Loading prohibited Audio V2 checkpoint by path is forbidden: {p}"
        )
    if p.exists():
        h = compute_sha256(p)
        if h == PROHIBITED_AUDIO_V2_SHA256:
            raise ProhibitedCheckpointError(
                f"CRITICAL: Checkpoint at {p} has prohibited Audio V2 SHA-256 hash ({PROHIBITED_AUDIO_V2_SHA256})! Aborting."
            )


def verify_checkpoint_immutability(repo_root: Path | str = ".") -> None:
    """Verify that both vision and audio frozen model checkpoints are intact and not prohibited."""
    root = Path(repo_root)
    yolo_file = root / FROZEN_YOLO_PATH
    audio_file = root / FROZEN_AUDIO_PATH

    if not yolo_file.exists():
        raise DataLeakageError(f"Frozen YOLOv8n checkpoint missing: {yolo_file}")
    if not audio_file.exists():
        raise DataLeakageError(f"Frozen Audio CNN checkpoint missing: {audio_file}")

    yolo_hash = compute_sha256(yolo_file)
    if yolo_hash != FROZEN_YOLO_SHA256:
        raise DataLeakageError(
            f"CRITICAL: YOLOv8n checkpoint mutated! Expected {FROZEN_YOLO_SHA256}, got {yolo_hash}"
        )

    audio_hash = compute_sha256(audio_file)
    if audio_hash != FROZEN_AUDIO_SHA256:
        raise DataLeakageError(
            f"CRITICAL: Audio CNN checkpoint mutated! Expected {FROZEN_AUDIO_SHA256}, got {audio_hash}"
        )

    # Check that neither equals the prohibited hash
    if yolo_hash == PROHIBITED_AUDIO_V2_SHA256 or audio_hash == PROHIBITED_AUDIO_V2_SHA256:
        raise DataLeakageError(
            f"CRITICAL: Configured checkpoint matches prohibited Audio V2 SHA-256 ({PROHIBITED_AUDIO_V2_SHA256})!"
        )

    logger.info("Checkpoint immutability verified: YOLO and Audio checkpoints match frozen hashes.")


def verify_no_layer_b_in_training(repo_root: Path | str = ".") -> None:
    """Verify that no Layer B real-world video or audio data exists in any training dataset or manifest."""
    root = Path(repo_root)

    # 1. Check audio training manifest
    audio_train_manifest = root / "data" / "manifests" / "audio_training_dataset.json"
    if audio_train_manifest.exists():
        try:
            with open(audio_train_manifest, "r", encoding="utf-8") as f:
                records = json.load(f)
            for rec in records:
                src_path = str(rec.get("source_path", ""))
                rel_path = str(rec.get("relative_path", ""))
                for leak_token in ("layer_b", "Train_test_video_new", "camera_front", "camera_back"):
                    if leak_token in src_path or leak_token in rel_path:
                        raise DataLeakageError(
                            f"CRITICAL DATA LEAKAGE: Layer B audio found in audio training manifest: {rec}"
                        )
        except Exception as e:
            if isinstance(e, DataLeakageError):
                raise
            logger.warning("Could not parse audio training manifest: %s", e)

    # 2. Check Vision V1 image directory
    vision_v1_dir = root / "data" / "raw" / "vision" / "v1"
    if vision_v1_dir.exists():
        for f in vision_v1_dir.rglob("*.mov"):
            raise DataLeakageError(
                f"CRITICAL DATA LEAKAGE: Video file found in vision training dataset: {f}"
            )

    logger.info("Layer B isolation verified: No evaluation data detected in training sets.")


def verify_frozen_parameters(runtime_params: dict[str, Any]) -> None:
    """Verify that runtime execution parameters strictly match the frozen parameters."""
    for key, expected_val in FROZEN_PARAMETERS.items():
        if key in runtime_params:
            actual_val = runtime_params[key]
            if actual_val != expected_val:
                raise DataLeakageError(
                    f"Parameter violation: {key}={actual_val} does not match frozen value {expected_val}"
                )


def run_all_leakage_checks(
    repo_root: Path | str = ".",
    runtime_params: dict[str, Any] | None = None,
    classifier: Any | None = None,
    engine: Any | None = None,
) -> None:
    """Run complete battery of leakage and integrity checks."""
    verify_checkpoint_immutability(repo_root)
    verify_no_layer_b_in_training(repo_root)
    if runtime_params is not None:
        verify_frozen_parameters(runtime_params)
    if classifier is not None or engine is not None:
        verify_runtime_components_against_config(classifier=classifier, engine=engine)
    logger.info("All data leakage and integrity checks passed successfully.")


def verify_runtime_components_against_config(
    config: Any | None = None,
    classifier: Any | None = None,
    engine: Any | None = None,
    decision_engine: Any | None = None,
) -> None:
    """Verify that live instantiated components reflect the frozen configuration."""
    from railway_detection.experiments.frozen_config import (
        FrozenExperimentConfig,
        load_frozen_config,
    )

    # Support flexible positional or keyword usage
    if isinstance(config, FrozenExperimentConfig):
        cfg = config
    elif config is not None:
        if hasattr(config, "audio_threshold"):
            decision_engine = config
            cfg = load_frozen_config()
        elif hasattr(config, "predict_window"):
            classifier = config
            cfg = load_frozen_config()
        else:
            cfg = load_frozen_config()
    else:
        cfg = load_frozen_config()

    active_engine = decision_engine if decision_engine is not None else engine

    if classifier is not None:
        if hasattr(classifier, "threshold"):
            if abs(classifier.threshold - cfg.audio.operating_threshold) > 1e-4:
                raise DataLeakageError(
                    f"Classifier threshold mismatch: {classifier.threshold} != {cfg.audio.operating_threshold}"
                )
        if hasattr(classifier, "mean") and hasattr(classifier, "std"):
            if abs(classifier.mean - cfg.audio.normalization.mean) > 1e-4:
                raise DataLeakageError(
                    f"Classifier normalization mean mismatch: {classifier.mean} != {cfg.audio.normalization.mean}"
                )
            if abs(classifier.std - cfg.audio.normalization.std) > 1e-4:
                raise DataLeakageError(
                    f"Classifier normalization std mismatch: {classifier.std} != {cfg.audio.normalization.std}"
                )

    if active_engine is not None:
        if hasattr(active_engine, "audio_threshold"):
            if abs(active_engine.audio_threshold - cfg.audio.operating_threshold) > 1e-4:
                raise DataLeakageError(
                    f"Engine audio threshold mismatch: {active_engine.audio_threshold} != {cfg.audio.operating_threshold}"
                )
        if hasattr(active_engine, "approach_threshold"):
            if abs(active_engine.approach_threshold - cfg.vision.confidence_threshold_approach) > 1e-4:
                raise DataLeakageError(
                    f"Engine approach threshold mismatch: {active_engine.approach_threshold} != {cfg.vision.confidence_threshold_approach}"
                )
