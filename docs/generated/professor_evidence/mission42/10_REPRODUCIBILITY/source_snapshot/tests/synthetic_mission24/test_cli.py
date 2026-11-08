import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from railway_detection.application import cli
from railway_detection.cli.main import main


def test_architecture_and_error_codes_have_no_live_route(tmp_path, capsys):
    assert main(["application", "architecture"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert len(result["components"]) == 10 and not result["live_resource_route"]
    assert (
        main(["application", "demo", "--output", str(tmp_path / "x"), "--enable-comparator"]) == 2
    )
    assert not (tmp_path / "x").exists()
    assert main(["application", "verify", "--output", str(tmp_path / "absent")]) == 2
    assert (
        main(
            [
                "application",
                "acceptance",
                "--output",
                str(tmp_path / "out"),
                "--register",
                str(tmp_path / "missing.json"),
            ]
        )
        == 2
    )


def test_acceptance_cli_delegates_existing_runner(monkeypatch):
    seen = []
    runner = SimpleNamespace(main=lambda args: seen.append(args) or 0)
    monkeypatch.setattr(cli, "_runner", lambda: runner)
    args = SimpleNamespace(
        application_command="acceptance",
        output="/tmp/constructed-app-tests",
        register=Path("CONSTRUCTED_TEST_CLASSIFICATION_REGISTER.json"),
    )
    assert cli.run_acceptance(args) == 0
    assert seen == [["run", "--output", args.output, "--register", str(args.register)]]


def test_synthetic_test_selection_is_explicit_and_never_runs_protected_cases(tmp_path, monkeypatch):
    path = tmp_path / "CONSTRUCTED_TEST_CLASSIFICATION_REGISTER.json"
    path.write_text("{}")
    selected = "tests/synthetic_mission24/test_cli.py::test_contract"
    protected = "tests/unit/test_real.py::test_real"
    seen = []
    runner = SimpleNamespace(
        validate=lambda *a: [],
        selection=lambda *a: {
            "selected": [selected, "tests/unit/test_other.py::test_other"],
            "protected": [protected],
            "unknown": [],
        },
        destination=lambda p: p,
        execute=lambda *a, **k: seen.append((a, k)) or 0,
    )
    monkeypatch.setattr(cli, "_runner", lambda: runner)
    args = SimpleNamespace(
        application_command="synthetic-test", output=str(tmp_path / "new"), register=path
    )
    assert cli.run_acceptance(args) == 0
    assert seen[0][0][1] == [selected]
    assert seen[0][1]["exclusions"]["NOT_EXECUTED_PROTECTED_DEPENDENCY"] == [protected]


def test_validation_receipt_inspection_preserves_exclusion_counts(tmp_path, capsys):
    path = tmp_path / "receipt.json"
    record = {
        "schema": "resource-free-execution/1",
        "status": "PASSED_SELECTED_RESOURCE_FREE",
        "execution_complete": True,
        "source_bindings_unchanged": True,
        "totals": {"tests": 1, "passed": 1, "failures": 0, "errors": 0, "skipped": 0},
        "groups": [{"tests": 1, "failures": 0, "errors": 0, "skipped": 0, "exit_code": 0}],
        "not_executed": {"NOT_EXECUTED_PROTECTED_DEPENDENCY": ["test_protected"]},
    }
    path.write_text(json.dumps(record))
    assert main(["application", "validation", "--receipt", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["not_executed"] == {
        "NOT_EXECUTED_PROTECTED_DEPENDENCY": 1
    }
    record["totals"]["passed"] = 2
    path.write_text(json.dumps(record))
    assert main(["application", "validation", "--receipt", str(path)]) == 2


def test_validation_metadata_cannot_open_protected_tree_before_read(monkeypatch):
    from pathlib import Path

    monkeypatch.setattr(
        Path, "read_text", lambda *a, **k: (_ for _ in ()).throw(AssertionError("opened"))
    )
    with pytest.raises(ValueError, match="protected"):
        cli.inspect_validation_receipt(cli.ROOT / "data/raw/receipt.json")


def test_benchmark_keeps_actual_memory_measurements_in_reports(monkeypatch):
    from types import SimpleNamespace

    from railway_detection.optimization import benchmark_suite
    from railway_detection.optimization.benchmark import BenchmarkProtocol

    class Clock:
        now = 0.0

        def __call__(self):
            self.now += 0.001
            return self.now

    memory = iter([1024, 2048])
    monkeypatch.setattr(
        benchmark_suite.resource, "getrusage", lambda _: SimpleNamespace(ru_maxrss=next(memory))
    )
    reports = [
        benchmark_suite.run_staged_benchmark(
            "constructed-memory-contract",
            [("identity", lambda value: value)],
            [1],
            BenchmarkProtocol(warmup_iterations=0, measured_iterations=1, repetitions=1),
            benchmark_suite.InputDescription("synthetic", "CONSTRUCTED memory measurement fixture"),
            root=cli.ROOT,
            clock=Clock(),
            host={"system": "CONSTRUCTED"},
            fingerprints={"verified": False, "checkpoints": {}},
        )
        for _ in range(2)
    ]
    assert (
        reports[0]["memory"]["process_peak_rss_bytes"] * 2
        == reports[1]["memory"]["process_peak_rss_bytes"]
    )
    assert reports[0]["stage_latency_ms"] == reports[1]["stage_latency_ms"]
    assert reports[0]["output_fingerprint_sha256"] == reports[1]["output_fingerprint_sha256"]
    assert all(not r["real_time_claim_permitted"] and not r["is_safety_evidence"] for r in reports)
