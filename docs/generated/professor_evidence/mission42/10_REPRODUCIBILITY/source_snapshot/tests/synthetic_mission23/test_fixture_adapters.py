"""Constructed alternatives exercise application paths, never certify the real corpus."""

import hashlib
import json

import numpy as np
import pytest

from railway_detection.annotation.readiness_audit import (
    audit_ground_truth_readiness,
    leg_exec_preflight,
)
from railway_detection.audio.dataset import AudioDatasetLoader
from railway_detection.audio.training import (
    AudioTrainer,
    AudioTrainingConfig,
    AudioTrainingGatingError,
)
from railway_detection.cli.main import main as cli_main
from railway_detection.optimization import benchmark_cli, benchmark_suite


@pytest.fixture
def audio_manifest(tmp_path):
    rows = []
    for part in ("train", "val"):
        for index in range(12):
            name = f"synthetic:{part}:{index}"
            feature = f"constructed_{part}_{index}.npy"
            np.save(tmp_path / feature, np.zeros((64, 61), dtype=np.float32))
            rows.append(
                {
                    "window_id": name,
                    "source_file": name,
                    "source_sha256": hashlib.sha256(name.encode()).hexdigest(),
                    "split_group_id": name,
                    "class_name": "train_horn" if index < 10 else "background",
                    "class_id": int(index < 10),
                    "partition": part,
                    "window_index": 0,
                    "start_time_s": 0.0,
                    "end_time_s": 1.0,
                    "duration_s": 1.0,
                    "sample_rate": 16000,
                    "standardized_wav_path": "CONSTRUCTED_NOT_A_RECORDING.wav",
                    "feature_path": feature,
                    "feature_type": "log_mel_spectrogram",
                    "feature_shape": [64, 61],
                    "dataset_role": "audio_model_development",
                    "fixture_classification": "CONSTRUCTED_FEATURE_FIXTURE",
                }
            )
    path = tmp_path / "constructed_manifest.json"
    path.write_text(json.dumps(rows))
    return path


def test_real_audio_loader_and_batches_with_constructed_schema(audio_manifest):
    loader = AudioDatasetLoader(audio_manifest, workspace_root=audio_manifest.parent)
    batch = next(loader.generate_batches(batch_size=4, shuffle=False))
    assert batch.features.shape == (4, 64, 61) and np.isfinite(batch.features).all()
    assert all(s.startswith("synthetic:") for s in batch.source_files)
    assert loader.positive_count == 10 and loader.negative_count == 2


def test_pretraining_gate_validation_without_any_fit(audio_manifest):
    trainer = AudioTrainer(
        config=AudioTrainingConfig(manifest_path=str(audio_manifest)),
        workspace_root=audio_manifest.parent,
    )
    trainer.verify_pretraining_gates()  # validation only: no model/optimizer/training call
    rows = json.loads(audio_manifest.read_text())
    audio_manifest.write_text(json.dumps([r for r in rows if r["class_id"] == 1]))
    blocked = AudioTrainer(
        config=AudioTrainingConfig(manifest_path=str(audio_manifest)),
        workspace_root=audio_manifest.parent,
    )
    with pytest.raises(AudioTrainingGatingError, match="negative"):
        blocked.verify_pretraining_gates()


def test_constructed_review_corpus_is_counted_but_never_eligible(tmp_path):
    reviews = tmp_path / "data/ground_truth/reviews/train_events"
    reviews.mkdir(parents=True)
    for index in range(3):
        (reviews / f"synthetic_{index}_review.json").write_text(
            json.dumps(
                {
                    "schema_version": "6.0.0",
                    "event_id": f"synthetic:event:{index}",
                    "cohort": "train_events",
                    "reviewer_id": "synthetic:fixture-not-a-human",
                    "adjudication_status": "UNAVAILABLE",
                    "fixture_classification": "CONSTRUCTED_REVIEW_FIXTURE",
                    "timestamps": {},
                }
            )
        )
    result = audit_ground_truth_readiness(tmp_path)
    assert result["summary"]["record_count"] == 3
    assert result["summary"]["promotion_eligible_pending_media_rehash"] == 0
    preflight = leg_exec_preflight(tmp_path)
    assert not preflight["execution_authorized"] and not preflight["inputs_verified"]


def test_forged_active_schema_on_constructed_legacy_body_is_rejected(tmp_path):
    reviews = tmp_path / "data/ground_truth/reviews/train_events"
    reviews.mkdir(parents=True)
    (reviews / "synthetic_review.json").write_text(
        json.dumps(
            {
                "schema_version": "8.1.0-stage2.1",
                "event_id": "synthetic:not-an-event",
                "fixture_classification": "CONSTRUCTED_REVIEW_FIXTURE",
            }
        )
    )
    result = audit_ground_truth_readiness(tmp_path)
    assert result["summary"]["promotion_eligible_pending_media_rehash"] == 0
    assert not list((tmp_path / "data").glob("**/*promotion*"))


@pytest.mark.parametrize("target", [False, True])
def test_same_benchmark_cli_path_with_explicit_unverified_dependencies(
    tmp_path, monkeypatch, target
):
    from pathlib import Path

    import yaml

    from railway_detection.experiments.frozen_config import parse_config_dict

    # This fixture is configuration metadata only. No checkpoint content/hash is supplied.
    raw = yaml.safe_load(
        (Path(__file__).resolve().parents[2] / "configs/frozen_experiment_v1.yaml").read_text()
    )
    raw["experiment"]["name"] = "CONSTRUCTED_BENCHMARK_FIXTURE"
    config = parse_config_dict(raw)
    monkeypatch.setattr(benchmark_cli, "load_frozen_config", lambda *a, **k: config)
    monkeypatch.setattr(
        benchmark_suite,
        "artifact_fingerprints",
        lambda *a, **k: {
            "verified": False,
            "classification": "CONSTRUCTED_UNVERIFIED",
            "checkpoints": {},
            "reason": "production artifacts deliberately not inspected",
        },
    )
    host = {
        "system": "CONSTRUCTED_HOST",
        "machine": "CONSTRUCTED",
        "processor": "UNVERIFIED",
        "cpu_count": 1,
    }
    monkeypatch.setattr(benchmark_suite, "host_fingerprint", lambda: host)
    monkeypatch.setattr(benchmark_suite, "collect_host_environment", lambda root: host)
    output = tmp_path / "constructed_benchmark.json"
    args = [
        "benchmark",
        "run",
        "--output",
        str(output),
        "--warmup",
        "1",
        "--iterations",
        "1",
        "--repetitions",
        "1",
    ]
    if target:
        args += ["--target-machine", "CONSTRUCTED"]
    code = cli_main(args)
    assert code == 1  # existing CLI correctly refuses VERIFIED acceptance
    report = json.loads(output.read_text())
    assert not report["fingerprints_verified"] and not report["real_time_claim_permitted"]
    assert report["fingerprints"]["checkpoints"] == {}


def test_reproducibility_cli_on_empty_constructed_root_reports_missing_evidence(tmp_path):
    root = tmp_path / "constructed_project"
    root.mkdir()
    output = tmp_path / "constructed_audit.json"
    code = cli_main(
        ["audit", "reproducibility", "--repository-root", str(root), "--json", str(output)]
    )
    assert code == 0
    report = json.loads(output.read_text())
    assert report
    assert "MISSING" in output.read_text().upper() or "UNVERIFIED" in output.read_text().upper()
    assert not (root / "data").exists()
