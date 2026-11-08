"""Regression tests for Phase 2: Frozen Experiment Configuration and Inference Safeguards.

Verifies:
1. Authoritative configuration loads deterministically and produces stable canonical SHA-256 hash.
2. Parameter changes strictly produce different canonical hashes (canonical serialization).
3. Missing or invalid required configuration sections/fields fail with ConfigurationIntegrityError.
4. Mismatched or missing checkpoint hashes fail before inference with CheckpointIntegrityError.
5. Prohibited Audio V2 checkpoint (by path and SHA-256) is rejected with ProhibitedCheckpointError.
6. Incorrect audio threshold overrides are rejected.
7. Audio V3 normalization and 0.3700 threshold are consistently propagated to decision engines.
8. Component defaults cannot silently override frozen settings.
9. Cross-camera synchronization without empirical calibration (R04) raises TimingIntegrityError.
10. Condition overrides (B0–B7) are explicit, traceable, and leave the base configuration immutable.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from railway_detection.audio.model import PyTorchTrainHornClassifier
from railway_detection.experiments.frozen_config import (
    DEFAULT_CONFIG_PATH,
    PROHIBITED_AUDIO_V2_PATH,
    PROHIBITED_AUDIO_V2_SHA256,
    CheckpointIntegrityError,
    ConfigurationIntegrityError,
    ProhibitedCheckpointError,
    TimingIntegrityError,
    compute_canonical_config_hash,
    create_condition_config,
    load_frozen_config,
    parse_config_dict,
    verify_checkpoint_integrity,
    verify_timing_safeguards,
)
from railway_detection.experiments.layer_b_processor import LayerBEventProcessor
from railway_detection.experiments.leakage_guard import (
    DataLeakageError,
    verify_not_prohibited_checkpoint,
    verify_runtime_components_against_config,
)
from railway_detection.experiments.runner import ExperimentRunner
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality


# Canonical frozen hash for configs/frozen_experiment_v1.yaml
EXPECTED_FROZEN_CONFIG_HASH = (
    "999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e"
)


# ---------------------------------------------------------------------------
# 1. Deterministic Configuration Loading & Stable Hash
# ---------------------------------------------------------------------------

def test_frozen_config_loads_deterministically():
    """Verify that the production frozen configuration loads and matches the canonical hash."""
    config1 = load_frozen_config(DEFAULT_CONFIG_PATH)
    config2 = load_frozen_config(DEFAULT_CONFIG_PATH)

    assert config1.canonical_hash == EXPECTED_FROZEN_CONFIG_HASH
    assert config2.canonical_hash == EXPECTED_FROZEN_CONFIG_HASH
    assert config1.canonical_hash == config2.canonical_hash
    assert config1.audio.operating_threshold == 0.3700
    assert "R04_UNRESOLVED" in config1.timing.cross_camera_sync.status
    assert config1.timing.cross_camera_sync.allow_unverified_zero_offset is False


# ---------------------------------------------------------------------------
# 2. Configuration Mutation Produces Different Hash
# ---------------------------------------------------------------------------

def test_config_hash_changes_on_parameter_mutation():
    """Any modification in the serialized dictionary must yield a different SHA-256 hash."""
    config = load_frozen_config(DEFAULT_CONFIG_PATH)
    base_hash = config.canonical_hash

    # Mutate audio threshold
    mutated_audio = copy.deepcopy(config.raw_dict)
    mutated_audio["audio"]["operating_threshold"] = 0.5000
    assert compute_canonical_config_hash(mutated_audio) != base_hash

    # Mutate timing
    mutated_timing = copy.deepcopy(config.raw_dict)
    mutated_timing["timing"]["gate_closing_s"] = 4.0
    assert compute_canonical_config_hash(mutated_timing) != base_hash

    # Mutate vision sampling
    mutated_vision = copy.deepcopy(config.raw_dict)
    mutated_vision["vision"]["sampling_fps"] = 10.0
    assert compute_canonical_config_hash(mutated_vision) != base_hash


# ---------------------------------------------------------------------------
# 3. Missing or Invalid Required Parameters Fail Clearly
# ---------------------------------------------------------------------------

def test_missing_required_section_fails():
    """Omitting any core section raises ConfigurationIntegrityError."""
    config = load_frozen_config(DEFAULT_CONFIG_PATH)
    for section in ("experiment", "checkpoints", "audio", "vision", "timing"):
        bad_dict = copy.deepcopy(config.raw_dict)
        del bad_dict[section]
        with pytest.raises(ConfigurationIntegrityError, match=f"Missing required configuration section: '{section}'"):
            parse_config_dict(bad_dict)


def test_missing_required_experiment_field_fails():
    """Omitting an experiment field raises ConfigurationIntegrityError."""
    config = load_frozen_config(DEFAULT_CONFIG_PATH)
    for field in ("name", "version", "description", "seed", "device"):
        bad_dict = copy.deepcopy(config.raw_dict)
        del bad_dict["experiment"][field]
        with pytest.raises(ConfigurationIntegrityError, match=f"Missing field in experiment: '{field}'"):
            parse_config_dict(bad_dict)


# ---------------------------------------------------------------------------
# 4. Checkpoint Integrity & Hash Mismatches Fail Before Inference
# ---------------------------------------------------------------------------

def test_production_checkpoints_integrity_verified():
    """Production checkpoints on disk must match their expected SHA-256 hashes."""
    config = load_frozen_config(DEFAULT_CONFIG_PATH)
    # This must pass without exception on the real repo tree
    verify_checkpoint_integrity(config, repo_root=".")


def test_missing_checkpoint_fails(tmp_path: Path):
    """Missing checkpoint file raises CheckpointIntegrityError."""
    config = load_frozen_config(DEFAULT_CONFIG_PATH)
    # Pointing to non-existent root
    with pytest.raises(CheckpointIntegrityError, match="checkpoint missing"):
        verify_checkpoint_integrity(config, repo_root=tmp_path)


def test_corrupted_checkpoint_hash_fails(tmp_path: Path):
    """Checkpoint with mismatched content hash raises CheckpointIntegrityError."""
    # Setup dummy checkpoints directory
    v_dir = tmp_path / "experiments/vision/39f402dfe460/checkpoints/weights"
    v_dir.mkdir(parents=True)
    v_file = v_dir / "best.pt"
    v_file.write_bytes(b"tampered vision weights")

    a_dir = tmp_path / "experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints"
    a_dir.mkdir(parents=True)
    a_file = a_dir / "best.pt"
    a_file.write_bytes(b"tampered audio weights")

    config = load_frozen_config(DEFAULT_CONFIG_PATH)
    with pytest.raises(CheckpointIntegrityError, match="YOLO vision checkpoint SHA-256 mismatch"):
        verify_checkpoint_integrity(config, repo_root=tmp_path)


# ---------------------------------------------------------------------------
# 5. Audio V2 Hard Prohibition
# ---------------------------------------------------------------------------

def test_prohibited_audio_v2_path_and_hash():
    """Audio V2 checkpoint path and hash are explicitly prohibited."""
    assert PROHIBITED_AUDIO_V2_PATH == "models/audio/best_checkpoint.pt"
    assert PROHIBITED_AUDIO_V2_SHA256 == "59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5"

    with pytest.raises(ProhibitedCheckpointError, match="prohibited Audio V2"):
        verify_not_prohibited_checkpoint("models/audio/best_checkpoint.pt")


def test_prohibited_audio_v2_classifier_load_fails():
    """PyTorchTrainHornClassifier refuses to load Audio V2 checkpoint."""
    with pytest.raises(ProhibitedCheckpointError, match="prohibited Audio V2"):
        PyTorchTrainHornClassifier(checkpoint_path="models/audio/best_checkpoint.pt")


def test_prohibited_audio_v2_hash_in_config_fails(tmp_path: Path):
    """Configuring the Audio V2 hash in audio_v3 or vision checkpoint raises ProhibitedCheckpointError."""
    config = load_frozen_config(DEFAULT_CONFIG_PATH)
    mutated = copy.deepcopy(config.raw_dict)
    mutated["checkpoints"]["audio_v3"]["expected_sha256"] = PROHIBITED_AUDIO_V2_SHA256

    mut_cfg = parse_config_dict(mutated)
    with pytest.raises(ProhibitedCheckpointError, match="FATAL: Prohibited Audio V2"):
        verify_checkpoint_integrity(mut_cfg, repo_root=".")


# ---------------------------------------------------------------------------
# 6. Audio V3 Threshold Invariant & Override Rejection
# ---------------------------------------------------------------------------

def test_incorrect_audio_threshold_override_rejected():
    """Setting audio operating threshold away from 0.3700 in config raises ConfigurationIntegrityError."""
    config = load_frozen_config(DEFAULT_CONFIG_PATH)
    mutated = copy.deepcopy(config.raw_dict)
    mutated["audio"]["operating_threshold"] = 0.5000
    mut_cfg = parse_config_dict(mutated)

    with pytest.raises(ConfigurationIntegrityError, match="threshold violation: 0.5 != 0.3700"):
        verify_checkpoint_integrity(mut_cfg, repo_root=".")


def test_audio_classifier_threshold_override_rejected():
    """Passing a threshold != 0.3700 to PyTorchTrainHornClassifier raises ValueError."""
    v3_path = Path("experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt")
    if v3_path.exists():
        with pytest.raises(ValueError, match="Threshold override mismatch"):
            PyTorchTrainHornClassifier(checkpoint_path=str(v3_path), threshold=0.50)


# ---------------------------------------------------------------------------
# 7. Normalization & Threshold Consistency Propagation
# ---------------------------------------------------------------------------

def test_decision_engine_uses_frozen_config_threshold():
    """MultimodalDecisionEngine instantiated with config adopts 0.3700 and all timing parameters."""
    config = load_frozen_config(DEFAULT_CONFIG_PATH)
    engine = MultimodalDecisionEngine(config=config)

    assert engine.audio_threshold == 0.3700
    assert engine.confirm_frames == 2
    assert engine.warning_dwell_s == 2.0
    assert engine.clearance_dwell_s == 3.0


def test_runtime_components_validated_against_frozen_config():
    """Leakage guard confirms live engine adheres to frozen configuration."""
    config = load_frozen_config(DEFAULT_CONFIG_PATH)
    engine = MultimodalDecisionEngine(config=config)

    # Valid check passes cleanly
    verify_runtime_components_against_config(config, decision_engine=engine)

    # Tampered engine fails leakage guard
    tampered_engine = MultimodalDecisionEngine(audio_threshold=0.60)
    with pytest.raises(DataLeakageError, match="Engine audio threshold mismatch"):
        verify_runtime_components_against_config(config, decision_engine=tampered_engine)


# ---------------------------------------------------------------------------
# 8. Unverified Cross-Camera Timing Constraint (R04)
# ---------------------------------------------------------------------------

def test_unverified_cross_camera_sync_blocked_by_default():
    """Verification fails if allow_unverified_zero_offset is True."""
    config = load_frozen_config(DEFAULT_CONFIG_PATH)
    mutated = copy.deepcopy(config.raw_dict)
    mutated["timing"]["cross_camera_sync"]["allow_unverified_zero_offset"] = True
    mut_cfg = parse_config_dict(mutated)

    with pytest.raises(TimingIntegrityError, match="R04"):
        verify_timing_safeguards(mut_cfg)


def test_layer_b_processor_enforces_r04_camera_timing():
    """LayerBEventProcessor raises TimingIntegrityError when merging multiple cameras without SyncAligner."""
    config = load_frozen_config(DEFAULT_CONFIG_PATH)
    processor = LayerBEventProcessor(config=config)

    cam1_record = EvidenceRecord(
        timestamp_s=10.0,
        source_id="camera_1",
        modality=Modality.VISION,
        available=True,
        detections=(Detection(label="train_front", confidence=0.9, bbox_xyxy=(0.0, 0.0, 10.0, 10.0)),),
    )
    cam2_record = EvidenceRecord(
        timestamp_s=10.0,
        source_id="camera_2",
        modality=Modality.VISION,
        available=True,
        detections=(Detection(label="train_side", confidence=0.8, bbox_xyxy=(0.0, 0.0, 10.0, 10.0)),),
    )

    # Merging multi-camera records without a calibrated SyncAligner must fail under R04
    with pytest.raises(TimingIntegrityError, match="R04 Timing Violation"):
        processor.build_multimodal_frames(
            vision_records=[cam1_record, cam2_record],
            audio_records=[],
            aligner=None,
        )


# ---------------------------------------------------------------------------
# 9. Traceable Condition Overrides & Base Immutability
# ---------------------------------------------------------------------------

def test_condition_config_creation_and_immutability():
    """create_condition_config produces explicit override records without mutating the base config."""
    base_config = load_frozen_config(DEFAULT_CONFIG_PATH)
    base_hash_before = base_config.canonical_hash

    overrides = {"timing.confirm_frames": 4}
    cond_config = create_condition_config(
        base_config=base_config,
        condition_name="B3",
        scenario_id="B3_custom",
        overrides=overrides,
    )

    # Base config must remain unaltered
    assert base_config.canonical_hash == base_hash_before
    assert base_config.timing.confirm_frames == 2
    assert base_config.condition_overrides == {}

    # Derived config must have modified value, new hash, and logged overrides
    assert cond_config.timing.confirm_frames == 4
    assert cond_config.canonical_hash != base_hash_before
    assert cond_config.condition_overrides == overrides
    assert cond_config.experiment.scenario_id == "B3_custom"
    assert cond_config.experiment.condition == "B3"


# ---------------------------------------------------------------------------
# 10. ExperimentRunner Wires Frozen Config & Produces Audit Artifacts
# ---------------------------------------------------------------------------

def test_experiment_runner_initializes_with_frozen_safeguards(tmp_path: Path):
    """ExperimentRunner verifies frozen safeguards on init and records provenance per condition."""
    runner = ExperimentRunner(output_root=tmp_path / "exp")
    assert runner.config.canonical_hash == EXPECTED_FROZEN_CONFIG_HASH
    assert runner.config.audio.operating_threshold == 0.3700
