import copy

from railway_detection.safety.resource_free_acceptance import (
    bindings,
    build_register,
    selection,
    validate,
)


def fixture(tmp_path):
    (tmp_path / "tests").mkdir()
    path = tmp_path / "tests/test_constructed.py"
    path.write_text("def test_constructed(): pass\ndef test_blocked(): pass\n")
    captured = bindings(tmp_path)
    evidence = {
        "groups": [
            {
                "group": "constructed",
                "files": ["tests/test_constructed.py"],
                "collected_nodeids": [
                    "tests/test_constructed.py::test_constructed",
                    "tests/test_constructed.py::test_blocked",
                ],
                "cases": [
                    {
                        "class": "tests.test_constructed",
                        "name": "test_constructed",
                        "outcome": "passed",
                        "diagnostic": "",
                    },
                    {
                        "class": "tests.test_constructed",
                        "name": "test_blocked",
                        "outcome": "error",
                        "diagnostic": "MISSION22_POLICY: protected_project_path: data/raw/fixture",
                    },
                ],
            }
        ]
    }
    return path, captured, evidence


def test_resource_free_and_protected_results_never_added_together(tmp_path):
    path, captured, evidence = fixture(tmp_path)
    register = build_register(tmp_path, evidence, captured, evidence_ref="CONSTRUCTED_UNIT_RECEIPT")
    assert validate(tmp_path, register) == []
    chosen = selection(register)
    assert len(chosen["selected"]) == 1 and len(chosen["protected"]) == 1
    assert not chosen["unknown"]
    assert register["modules"][str(path.relative_to(tmp_path))]["classification"] == "MIXED"


def test_modified_test_or_shared_loader_defaults_unknown(tmp_path):
    path, captured, evidence = fixture(tmp_path)
    path.write_text(path.read_text() + "# modified\n")
    register = build_register(tmp_path, evidence, captured, evidence_ref="OLD_RECEIPT")
    assert len(selection(register)["unknown"]) == 2
    src = tmp_path / "src"
    src.mkdir()
    (src / "loader.py").write_text("DEFAULT_RESOURCE = 'never-read'\n")
    assert any("shared dependency changed" in e for e in validate(tmp_path, register))


def test_missing_module_and_unexecuted_collected_case_are_visible(tmp_path):
    _, captured, evidence = fixture(tmp_path)
    evidence["groups"][0]["cases"].pop()
    register = build_register(tmp_path, evidence, captured, evidence_ref="INCOMPLETE_CASE_RESULT")
    assert selection(register)["unknown"] == ["tests/test_constructed.py::test_blocked"]
    (tmp_path / "tests/test_new.py").write_text("def test_new(): pass\n")
    assert any("missing module" in e for e in validate(tmp_path, register))


def test_forged_node_binding_and_missing_evidence_refuse(tmp_path):
    _, captured, evidence = fixture(tmp_path)
    register = build_register(tmp_path, evidence, captured, evidence_ref="CONSTRUCTED_UNIT_RECEIPT")
    bad = copy.deepcopy(register)
    entry = bad["modules"]["tests/test_constructed.py"]["cases"][0]
    entry["nodeid"] = "other.py::test_constructed"
    entry["evidence"] = {}
    assert len(validate(tmp_path, bad)) == 2


def test_config_dependency_change_requires_fresh_review(tmp_path):
    _, captured, evidence = fixture(tmp_path)
    register = build_register(tmp_path, evidence, captured, evidence_ref="CONSTRUCTED_UNIT_RECEIPT")
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs/loader.json").write_text('{"resource":"CONSTRUCTED"}')
    assert any("shared dependency changed" in e for e in validate(tmp_path, register))


def test_source_and_config_aliases_refuse_before_hashing(tmp_path):
    import pytest

    fixture(tmp_path)
    (tmp_path / "configs").mkdir()
    target = tmp_path / "unreadable.txt"
    target.write_text("MUST_NOT_BE_HASHED")
    (tmp_path / "configs/alias.json").symlink_to(target)
    with pytest.raises(ValueError, match="alias refused"):
        bindings(tmp_path)


def test_protected_inventory_root_refuses_before_enumeration(monkeypatch):
    from pathlib import Path

    import pytest

    from railway_detection.safety.resource_free_acceptance import inventory

    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(
        Path, "rglob", lambda *a: (_ for _ in ()).throw(AssertionError("enumerated"))
    )
    with pytest.raises(ValueError, match="protected root"):
        inventory(root / "data/raw")


def test_manual_dependency_claim_needs_matching_source_and_fresh_denial(tmp_path):
    _, captured, evidence = fixture(tmp_path)
    evidence["groups"][0]["cases"][1]["diagnostic"] = "unavailable downstream"
    manual = {
        "tests/test_constructed.py::test_blocked": {
            "module_sha256": captured["modules"]["tests/test_constructed.py"],
            "reference": "CONSTRUCTED_TRIAGE",
            "reason": "fixture dependency",
            "resource_anchor": "data/raw/fixture",
        }
    }
    register = build_register(
        tmp_path,
        evidence,
        captured,
        evidence_ref="CONSTRUCTED_UNIT_RECEIPT",
        dependency_evidence=manual,
    )
    assert selection(register)["unknown"]
    evidence["groups"][0]["policy_denials"] = [
        '{"event":"protected_project_path","detail":"data/raw/fixture"}'
    ]
    register = build_register(
        tmp_path,
        evidence,
        captured,
        evidence_ref="CONSTRUCTED_UNIT_RECEIPT",
        dependency_evidence=manual,
    )
    assert len(selection(register)["protected"]) == 1


def test_failed_child_without_junit_cannot_be_reported_as_passing(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path
    from subprocess import CompletedProcess

    script = Path(__file__).resolve().parents[2] / "scripts/run_resource_free_acceptance.py"
    spec = importlib.util.spec_from_file_location("m23_runner_unit", script)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    fixture(tmp_path)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: CompletedProcess(a, 1))
    output = tmp_path / "output"
    output.mkdir()
    assert runner.execute(output, ["tests/test_constructed.py"], audit=True, exclusions={}) == 1
    import json

    receipt = json.loads((output / "receipt.json").read_text())
    assert receipt["status"] == "NONPASSING" and receipt["totals"]["passed"] == 0
