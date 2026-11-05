"""Source-document consistency, safe metadata paths, CLI and canonical timing."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from railway_detection.application.preflight import catalog as module
from railway_detection.application.preflight.engine import duration_compatibility

ROOT = Path(__file__).resolve().parents[2]


def test_actual_documentary_inventory_preserves_sources_roles_scopes_and_rights():
    c = module.load_catalog()
    module.verify_catalog(c)
    assert (
        len(c["sources"]) == 63 and len(c["candidate_events"]) == 27 and len(c["R04_events"]) == 11
    )
    assert sum(s["eligibility"] == "CANDIDATE_ONLY" for s in c["sources"]) == 54
    assert sum(s["eligibility"] == "EXCLUDED" for s in c["sources"]) == 2
    assert all(not s["live_digest_verified"] for s in c["sources"])
    assert all(s["owner"] is None for s in c["sources"])
    assert all(len(s["rights"]) == 10 for s in c["sources"])
    assert sum(o["selection_preserved"] == "A" for o in c["operations"]) == 21
    assert sum(o["selection_preserved"] == "B" for o in c["operations"]) == 6


@pytest.mark.parametrize(
    "fault",
    [
        "event_count",
        "r04_expansion",
        "source_missing",
        "source_duplicate",
        "false_signoff",
        "false_live_hash",
        "missing_provenance",
    ],
)
def test_incomplete_or_substituted_inventory_never_becomes_signed_off(fault):
    c = module.load_catalog()
    if fault == "event_count":
        c["candidate_events"].pop()
    elif fault == "r04_expansion":
        c["R04_events"].append("train_events/event_010")
    elif fault == "source_missing":
        c["sources"].pop(0)
    elif fault == "source_duplicate":
        c["sources"].append(c["sources"][0])
    elif fault == "false_signoff":
        c["inventory_signoff"] = True
    elif fault == "false_live_hash":
        c["sources"][0]["live_digest_verified"] = True
    elif fault == "missing_provenance":
        c["sources"][0]["provenance"] = None
    with pytest.raises(ValueError):
        module.verify_catalog(c)


def test_dashboard_is_deterministic_and_separates_unknown_denied_selected_and_executed():
    c = module.load_catalog()
    a = module.dashboard(c, now=0)
    b = module.dashboard(c, now=0)
    assert a == b
    assert len(a["operations"]) == 27
    assert sum(r["preflight"]["state"] == "PREFLIGHT_BLOCKED" for r in a["operations"]) == 21
    assert sum(r["preflight"]["state"] == "EXECUTION_NOT_PERMITTED" for r in a["operations"]) == 6
    assert not a["authorized_but_not_executed"] and not a["executed_operations"]
    assert not a["new_grants"] and not a["protected_resources_accessed"]
    assert all(r["status"] == "UNKNOWN_REQUIRES_VERIFICATION" for r in a["external_requirements"])
    assert "Unknown is distinct from denied" in module.render(a)


@pytest.mark.parametrize(
    "end,status",
    [
        ("2026-11-05T00:00:29.999999Z", "INCOMPATIBLE_DURATION_SCHEMA"),
        ("2026-11-05T00:00:30Z", "CANONICAL_SCHEMA_TIMING_COMPATIBLE"),
        ("2026-11-05T00:00:30.000001Z", "CANONICAL_SCHEMA_TIMING_COMPATIBLE"),
        ("2026-11-05T00:00:00Z", "INCOMPATIBLE_DURATION_SCHEMA"),
        ("invalid", "INCOMPATIBLE_DURATION_SCHEMA"),
    ],
)
def test_timing_adapter_uses_existing_canonical_rule_without_changing_human_truth(end, status):
    result = duration_compatibility(
        reviewer_id="synthetic:timing_metadata_fixture",
        session_id="synthetic:session",
        start="2026-11-05T00:00:00Z",
        end=end,
        tool="constructed timing unit test",
    )
    assert result["status"] == status and not result["genuine_review_proven"]
    if status == "CANONICAL_SCHEMA_TIMING_COMPATIBLE":
        assert result["scientific_duration_floor"] == "DEFERRED" and not result["record_created"]


@pytest.mark.parametrize(
    "path",
    [
        "data/raw/source.mov",
        "models/weights.pt",
        "docs/../data/private.json",
        "/tmp/arbitrary.json",
    ],
)
def test_metadata_reader_refuses_protected_or_unreviewed_location_before_read(path, monkeypatch):
    monkeypatch.setattr(
        Path, "read_text", lambda *a, **k: (_ for _ in ()).throw(AssertionError("reader reached"))
    )
    with pytest.raises(ValueError):
        module._metadata(ROOT / path)


def copy_metadata(tmp_path, monkeypatch):
    docs = tmp_path / "docs/generated/master_reaudit"
    docs.mkdir(parents=True)
    binding = json.loads((module.DOCS / module.BINDING).read_text())
    for name in (module.CATALOG, module.BINDING):
        (docs / name).write_text((module.DOCS / name).read_text())
    for relative in binding["document_bindings"]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((ROOT / relative).read_text())
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "DOCS", docs)
    return docs, binding


@pytest.mark.parametrize(
    "fault", ["catalog", "source_manifest", "binding_schema", "escape", "alias", "manifest_type"]
)
def test_altered_source_manifest_catalog_binding_or_alias_refuses(tmp_path, monkeypatch, fault):
    docs, binding = copy_metadata(tmp_path, monkeypatch)
    if fault == "catalog":
        (docs / module.CATALOG).write_text("{}")
    elif fault == "source_manifest":
        (tmp_path / "docs/PHASE11_3_REVIEW_INVENTORY.json").write_text("{}")
    elif fault == "binding_schema":
        binding["schema"] = "unsupported"
    elif fault == "escape":
        binding["document_bindings"] = {"../data/source.json": "0" * 64}
    elif fault == "manifest_type":
        binding["document_bindings"] = []
    else:
        (docs / module.CATALOG).unlink()
        (docs / module.CATALOG).symlink_to(tmp_path / "NEVER_READ")
    (docs / module.BINDING).write_text(json.dumps(binding))
    with pytest.raises((ValueError, OSError)):
        module.load_catalog()


def test_actual_cli_reports_and_checks_never_execute_or_accept_a_resource_path():
    base = [sys.executable, "-m", "railway_detection", "application", "readiness"]
    a = subprocess.run(
        base + ["report", "--now", "0", "--format", "json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    b = subprocess.run(
        base + ["report", "--now", "0", "--format", "json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert a.returncode == b.returncode == 0 and a.stdout == b.stdout
    report = json.loads(a.stdout)
    assert not report["new_grants"]
    source = module.load_catalog()["sources"][0]["source_id"]
    for operation in ("M19-PERM-02", "M19-PERM-24"):
        p = subprocess.run(
            base + ["check", "--operation", operation, "--resource", source, "--now", "0"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert p.returncode == 3 and not json.loads(p.stdout)["execution_permitted"]
    p = subprocess.run(
        base
        + [
            "check",
            "--operation",
            "M19-PERM-02",
            "--resource",
            "data/raw/NEVER_OPEN",
            "--now",
            "0",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert p.returncode == 2


def test_acceptance_closure_detects_changed_documentary_catalog_without_touching_source_resources(
    tmp_path,
):
    from railway_detection.safety.resource_free_acceptance import bindings

    (tmp_path / "tests").mkdir()
    p = tmp_path / "docs/generated/master_reaudit/MISSION_26_READINESS_CATALOG.json"
    p.parent.mkdir(parents=True)
    p.write_text("{}")
    a = bindings(tmp_path)
    p.write_text('{"altered":true}')
    b = bindings(tmp_path)
    assert a["shared_digest"] != b["shared_digest"]
    assert not any("data/raw" in name for name in b["shared_source_sha256"])


@pytest.mark.parametrize("family", ["docs", "docs/generated/master_reaudit"])
def test_acceptance_closure_refuses_documentary_parent_alias_before_hash(tmp_path, family):
    from railway_detection.safety.resource_free_acceptance import bindings

    (tmp_path / "tests").mkdir()
    p = tmp_path / family
    p.parent.mkdir(parents=True, exist_ok=True)
    p.symlink_to(tmp_path / "NEVER_ENUMERATE")
    with pytest.raises(ValueError, match="alias"):
        bindings(tmp_path)
