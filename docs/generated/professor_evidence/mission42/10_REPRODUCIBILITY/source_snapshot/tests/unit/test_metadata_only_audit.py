"""Synthetic tests proving the explicitly metadata-only audit stays isolated."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from railway_detection.cli.main import main as cli_main
from railway_detection.evaluation import metadata_only_audit
from railway_detection.evaluation.input_contracts import (
    EvaluationInputError,
    load_evaluation_input_manifest,
)


def _write_manifest(root: Path, *, source_exists: bool = False) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    manifest_root = root / "data" / "manifests"
    manifest_root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "phase12-evaluation-inputs/1",
        "evidence_classification": "synthetic",
        "partitions": {"train": ["train"], "val": ["val"], "test": ["test"]},
        "events": [
            {
                "event_id": event_id,
                "cohort": "synthetic",
                "split_role": role,
                "source_path": f"{event_id}.bin",
                "source_sha256": hashlib.sha256(event_id.encode()).hexdigest(),
            }
            for role, event_id in (("train", "train"), ("val", "val"), ("test", "test"))
        ],
    }
    if source_exists:
        for event_id in ("train", "val", "test"):
            (manifest_root / f"{event_id}.bin").write_bytes(
                b"synthetic media-like payload; never read by the audit"
            )
    path = manifest_root / "phase12_evaluation_inputs.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_metadata_only_audit_accepts_metadata_without_sources(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path / "missing-sources")

    report = metadata_only_audit.audit_input_manifest_metadata_only(
        manifest,
        repository_root=tmp_path / "missing-sources",
    )

    assert report["audit_mode"] == metadata_only_audit.AUDIT_MODE
    assert report["overall_status"] == "METADATA_CONTRACT_VALID_ONLY"
    assert report["official_evaluation_readiness"] == "NOT_ASSESSED"
    assert len(report["source_bindings"]) == 3
    assert all(not item["source_bytes_opened"] for item in report["source_bindings"])
    assert any("source-file existence" in item for item in report["checks_not_performed"])


def test_metadata_only_audit_tripwire_blocks_source_open(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path / "synthetic-sources", source_exists=True)
    source = manifest.parent / "train.bin"
    original = load_evaluation_input_manifest

    def regressed_loader(path, *, verify_sources=True):
        with source.open("rb") as handle:
            handle.read(1)
        return original(path, verify_sources=verify_sources)

    # Patch the audit's loader to simulate a regression. The tripwire must stop
    # the attempted open before any synthetic source bytes are returned.
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(metadata_only_audit, "load_evaluation_input_manifest", regressed_loader)
    try:
        with pytest.raises(metadata_only_audit.MetadataOnlyIsolationError, match="non-manifest"):
            metadata_only_audit.audit_input_manifest_metadata_only(
                manifest,
                repository_root=tmp_path / "synthetic-sources",
            )
    finally:
        monkeypatch.undo()


@pytest.mark.parametrize("api", ["path_open", "path_read_bytes", "builtin_open", "os_open"])
def test_metadata_only_tripwire_guards_common_byte_apis(tmp_path: Path, api: str) -> None:
    manifest = _write_manifest(tmp_path / api)
    source = manifest.parent / "train.bin"
    with metadata_only_audit._deny_non_manifest_byte_access(manifest):
        with pytest.raises(metadata_only_audit.MetadataOnlyIsolationError):
            if api == "path_open":
                source.open("rb")
            elif api == "path_read_bytes":
                source.read_bytes()
            elif api == "builtin_open":
                open(source, "rb")
            else:
                os.open(source, os.O_RDONLY)


def test_metadata_only_loader_does_not_require_source_files(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path / "missing-sources")

    loaded = load_evaluation_input_manifest(manifest, verify_sources=False)

    assert len(loaded.events) == 3
    assert all(event.source_payload == {} for event in loaded.events)


def test_metadata_only_audit_rejects_invalid_manifest(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path / "invalid")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["schema_version"] = "unexpected"
    manifest.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvaluationInputError, match="MANIFEST_SCHEMA_INVALID"):
        metadata_only_audit.audit_input_manifest_metadata_only(
            manifest,
            repository_root=tmp_path / "invalid",
        )


def test_metadata_only_audit_rejects_noncanonical_manifest_path(tmp_path: Path) -> None:
    arbitrary = tmp_path / "manifest.json"
    arbitrary.write_text("{}", encoding="utf-8")

    with pytest.raises(EvaluationInputError, match="MANIFEST_PATH_NOT_ALLOWED"):
        metadata_only_audit.audit_input_manifest_metadata_only(
            arbitrary,
            repository_root=tmp_path,
        )


def test_metadata_only_audit_tripwire_blocks_write_attempts(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path / "write-attempt")
    target = manifest.parent / "unexpected-output.json"
    original = load_evaluation_input_manifest

    def regressed_loader(path, *, verify_sources=True):
        target.write_text("unexpected", encoding="utf-8")
        return original(path, verify_sources=verify_sources)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(metadata_only_audit, "load_evaluation_input_manifest", regressed_loader)
    try:
        with pytest.raises(metadata_only_audit.MetadataOnlyIsolationError, match="non-manifest"):
            metadata_only_audit.audit_input_manifest_metadata_only(
                manifest,
                repository_root=tmp_path / "write-attempt",
            )
    finally:
        monkeypatch.undo()
    assert not target.exists()


def test_named_cli_mode_does_not_assess_official_readiness(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    manifest = _write_manifest(tmp_path / "cli")

    def forbidden(*args, **kwargs):
        raise AssertionError("official readiness function must not be called")

    from railway_detection.evaluation import execution_gate

    monkeypatch.setattr(execution_gate, "assess_official_phase12_readiness", forbidden)
    result = cli_main(
        [
            "evaluation",
            "metadata-only-audit",
            "--repository-root",
            str(tmp_path / "cli"),
            "--input-manifest",
            str(manifest),
        ]
    )

    report = json.loads(capsys.readouterr().out)
    assert result == 0
    assert report["audit_mode"] == metadata_only_audit.AUDIT_MODE
    assert report["official_evaluation_readiness"] == "NOT_ASSESSED"


def test_metadata_only_report_declares_the_explicit_scope_contract(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path / "scope")

    report = metadata_only_audit.audit_input_manifest_metadata_only(
        manifest,
        repository_root=tmp_path / "scope",
    )

    assert report["audit_schema"] == metadata_only_audit.AUDIT_SCHEMA
    assert report["audit_mode_version"] == metadata_only_audit.AUDIT_MODE_VERSION
    assert report["manifest_structurally_valid"] is True
    assert report["source_media_verified"] is False
    assert report["manifest"]["sha256"] == hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert "must not be interpreted as" in report["readiness_prohibition"]
    limitations = report["provenance_limitations"]
    assert any("no source bytes were opened" in item for item in limitations)
    assert any("not source-media integrity verification" in item for item in limitations)


def test_metadata_only_audit_creates_no_files_and_leaves_the_tree_untouched(
    tmp_path: Path,
) -> None:
    root = tmp_path / "no-writes"
    manifest = _write_manifest(root)
    (root / "data" / "ground_truth").mkdir(parents=True)
    (root / "data" / "evaluation").mkdir(parents=True)

    def snapshot(base: Path) -> set[str]:
        return {str(path.relative_to(base)) for path in base.rglob("*")}

    before = snapshot(root)

    report = metadata_only_audit.audit_input_manifest_metadata_only(
        manifest,
        repository_root=root,
    )

    assert snapshot(root) == before
    assert report["source_media_verified"] is False
    assert report["official_evaluation_readiness"] == "NOT_ASSESSED"