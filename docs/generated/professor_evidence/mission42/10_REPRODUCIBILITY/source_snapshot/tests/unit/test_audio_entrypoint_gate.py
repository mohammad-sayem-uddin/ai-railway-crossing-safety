"""Regression tests for the fail-closed pretraining gate in scripts/train_audio_model.py.

These tests verify that the training entry point refuses to initialize any
training state (run directories, data loaders, models) when the pretraining
integrity gates fail. The gate must be the very first action inside
``run_training_experiment``.
"""

from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

import pytest

from railway_detection.audio.training import AudioTrainingGatingError

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = WORKSPACE_ROOT / "scripts" / "train_audio_model.py"


def _load_train_script():
    """Import scripts/train_audio_model.py as a module without executing main."""
    spec = importlib.util.spec_from_file_location("train_audio_model_entrypoint", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_contaminated_manifest(tmp_path: Path) -> Path:
    """Create a manifest containing a Layer B source that must be rejected."""
    manifest = tmp_path / "contaminated_manifest.json"
    items = []
    items.append({
        "window_id": "pos_001_w000",
        "source_file": "layer_b/videos/event_001/camera_front.mov",
        "source_sha256": "fake_hash",
        "split_group_id": "g1",
        "class_name": "train_horn",
        "class_id": 1,
        "partition": "train",
        "window_index": 0,
        "start_time_s": 0.0,
        "end_time_s": 1.0,
        "duration_s": 1.0,
        "sample_rate": 16000,
        "standardized_wav_path": "data/processed/layer_b/event_001.wav",
        "feature_path": "dummy.npy",
        "feature_type": "log_mel_spectrogram",
        "feature_shape": [64, 61],
        "dataset_role": "real_world_evaluation",
    })
    for i in range(2, 12):
        items.append({
            "window_id": f"pos_{i:03d}_w000",
            "source_file": f"{i}.mp3",
            "source_sha256": f"hash_{i}",
            "split_group_id": f"g_{i}",
            "class_name": "train_horn",
            "class_id": 1,
            "partition": "train",
            "window_index": 0,
            "start_time_s": 0.0,
            "end_time_s": 1.0,
            "duration_s": 1.0,
            "sample_rate": 16000,
            "standardized_wav_path": f"{i}.wav",
            "feature_path": "dummy.npy",
            "feature_type": "log_mel_spectrogram",
            "feature_shape": [64, 61],
            "dataset_role": "audio_model_development",
        })
    for split in ("train", "val"):
        items.append({
            "window_id": f"neg_{split}_w000",
            "source_file": f"neg_{split}.wav",
            "source_sha256": f"fake_neg_{split}",
            "split_group_id": f"neg_g_{split}",
            "class_name": "non_train_horn",
            "class_id": 0,
            "partition": split,
            "window_index": 0,
            "start_time_s": 0.0,
            "end_time_s": 1.0,
            "duration_s": 1.0,
            "sample_rate": 16000,
            "standardized_wav_path": f"neg_{split}.wav",
            "feature_path": "dummy_neg.npy",
            "feature_type": "log_mel_spectrogram",
            "feature_shape": [64, 61],
            "dataset_role": "audio_model_development",
        })
    manifest.write_text(json.dumps(items), encoding="utf-8")
    return manifest


def test_entrypoint_gate_rejects_contaminated_manifest(tmp_path):
    """verify_audio_pretraining_gates must raise AudioTrainingGatingError."""
    module = _load_train_script()
    manifest = _make_contaminated_manifest(tmp_path)
    with pytest.raises(AudioTrainingGatingError) as exc_info:
        module.verify_audio_pretraining_gates(manifest, WORKSPACE_ROOT)
    assert "CRITICAL SAFETY VIOLATION" in str(exc_info.value)


def test_run_training_experiment_fails_closed_before_run_dir(tmp_path, monkeypatch):
    """run_training_experiment must abort before creating any run directory."""
    module = _load_train_script()
    fake_root = tmp_path / "workspace"
    (fake_root / "experiments" / "audio").mkdir(parents=True)
    monkeypatch.setattr(module, "WORKSPACE_ROOT", fake_root)

    def _raise(*args, **kwargs):
        raise AudioTrainingGatingError("SIMULATED GATE FAILURE")

    monkeypatch.setattr(module.AudioTrainer, "verify_pretraining_gates", _raise)

    with pytest.raises(AudioTrainingGatingError, match="SIMULATED GATE FAILURE"):
        module.run_training_experiment()

    audio_runs = list((fake_root / "experiments" / "audio").iterdir())
    assert audio_runs == [], f"Run directories created before gate: {audio_runs}"


def test_gate_call_precedes_training_initialization_in_source():
    """Structural guard: the gate call must appear before loader/model setup."""
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    run_fn = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "run_training_experiment"
        ),
        None,
    )
    assert run_fn is not None, "run_training_experiment not found in script"

    gate_line = None
    first_loader_line = None
    first_mkdir_line = None
    first_model_line = None

    for node in ast.walk(run_fn):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else (func.attr if isinstance(func, ast.Attribute) else "")
        if name == "verify_audio_pretraining_gates" and gate_line is None:
            gate_line = node.lineno
        elif name == "AudioDatasetLoader" and first_loader_line is None:
            first_loader_line = node.lineno
        elif name == "mkdir" and first_mkdir_line is None:
            first_mkdir_line = node.lineno
        elif name == "CompactTrainHornCNN" and first_model_line is None:
            first_model_line = node.lineno

    assert gate_line is not None, "verify_audio_pretraining_gates not called"
    assert first_loader_line is not None, "AudioDatasetLoader not found"
    assert first_mkdir_line is not None, "mkdir (run dir creation) not found"
    assert gate_line < first_loader_line, (
        f"Gate line {gate_line} must precede loader line {first_loader_line}"
    )
    assert gate_line < first_mkdir_line, (
        f"Gate line {gate_line} must precede mkdir line {first_mkdir_line}"
    )
    if first_model_line is not None:
        assert gate_line < first_model_line, (
            f"Gate line {gate_line} must precede model init line {first_model_line}"
        )
