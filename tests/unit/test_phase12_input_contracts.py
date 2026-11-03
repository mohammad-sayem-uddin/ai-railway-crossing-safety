"""Additional synthetic manifest contract edge and failure tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from railway_detection.evaluation.input_contracts import (
    EvaluationInputError,
    load_evaluation_input_manifest,
)


def _manifest(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    for event_id in ("train", "val", "test"):
        (tmp_path / f"{event_id}.json").write_text(
            json.dumps({"event_id": event_id}), encoding="utf-8"
        )
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "phase12-evaluation-inputs/1",
                "evidence_classification": "synthetic",
                "partitions": {
                    "train": ["train"],
                    "val": ["val"],
                    "test": ["test"],
                },
                "events": [
                    {
                        "event_id": event_id,
                        "cohort": "synthetic",
                        "split_role": role,
                        "source_path": f"{event_id}.json",
                        "source_sha256": hashlib.sha256(
                            (tmp_path / f"{event_id}.json").read_bytes()
                        ).hexdigest(),
                    }
                    for role, event_id in (
                        ("train", "train"),
                        ("val", "val"),
                        ("test", "test"),
                    )
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_manifest_refuses_missing_malformed_and_escaping_sources(tmp_path: Path):
    with pytest.raises(EvaluationInputError, match="MANIFEST_MISSING"):
        load_evaluation_input_manifest(tmp_path / "absent.json")

    path = _manifest(tmp_path / "valid")
    manifest = json.loads(path.read_text())
    manifest["events"][0]["source_path"] = "../outside.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(EvaluationInputError, match="SOURCE_PATH_ESCAPE"):
        load_evaluation_input_manifest(path)


def test_manifest_rejects_unknown_schema_classification_and_non_json_source(tmp_path: Path):
    path = _manifest(tmp_path / "manifest")
    manifest = json.loads(path.read_text())
    manifest["schema_version"] = "unknown"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(EvaluationInputError, match="MANIFEST_SCHEMA_INVALID"):
        load_evaluation_input_manifest(path)

    manifest["schema_version"] = "phase12-evaluation-inputs/1"
    manifest["evidence_classification"] = "maybe"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(EvaluationInputError, match="EVIDENCE_CLASSIFICATION_INVALID"):
        load_evaluation_input_manifest(path)

    path = _manifest(tmp_path / "not_json")
    source = path.parent / "train.json"
    source.write_text("not-json", encoding="utf-8")
    manifest = json.loads(path.read_text())
    manifest["events"][0]["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(EvaluationInputError, match="EVENT_INPUT_INVALID"):
        load_evaluation_input_manifest(path)


def test_manifest_refuses_unlisted_or_wrong_split_records(tmp_path: Path):
    path = _manifest(tmp_path / "split")
    manifest = json.loads(path.read_text())
    manifest["events"][0]["split_role"] = "test"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(EvaluationInputError, match="EVENT_SPLIT_MISMATCH"):
        load_evaluation_input_manifest(path)


def test_manifest_refuses_symlink_and_duplicate_source_identity(tmp_path: Path):
    path = _manifest(tmp_path / "symlink")
    root = path.parent
    (root / "alias.json").symlink_to(root / "train.json")
    manifest = json.loads(path.read_text())
    manifest["events"][0]["source_path"] = "alias.json"
    manifest["events"][0]["source_sha256"] = hashlib.sha256(
        (root / "train.json").read_bytes()
    ).hexdigest()
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(EvaluationInputError, match="SOURCE_SYMLINK_UNEXPECTED"):
        load_evaluation_input_manifest(path)

    path = _manifest(tmp_path / "duplicate")
    manifest = json.loads(path.read_text())
    manifest["events"][1]["source_path"] = manifest["events"][0]["source_path"]
    manifest["events"][1]["source_sha256"] = manifest["events"][0]["source_sha256"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(EvaluationInputError, match="DUPLICATE_SOURCE_IDENTITY"):
        load_evaluation_input_manifest(path)

    path = _manifest(tmp_path / "missing_event")
    manifest = json.loads(path.read_text())
    manifest["events"].pop()
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(EvaluationInputError, match="EVENT_SPLIT_MISMATCH"):
        load_evaluation_input_manifest(path)