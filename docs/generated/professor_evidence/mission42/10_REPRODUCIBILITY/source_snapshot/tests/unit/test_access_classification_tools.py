# ruff: noqa: E501
"""Classification-detection tests for the access guard, manifest and safe runner (Mission 10, WP10.3).

The guard is exercised in child pytest processes that attempt protected reads. Every attempted path
is blocked *before* any open happens (the guard raises first), so the attempts are safe even where
the named file exists. Nothing here writes into the repository.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

from railway_detection.safety import access_guard_plugin as plugin
from railway_detection.safety import access_manifest as am

REPO = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


classify_mod = _load_script("classify_test_access")
runner_mod = _load_script("run_synthetic_tests")


# --------------------------------------------------------------------------- categorize()


@pytest.mark.parametrize(
    ("rel", "expected"),
    [
        ("data/raw/layer_b/v2/train_events/event_001/camera_front.mov", plugin.CATEGORY_RAW),
        ("data/raw/layer_b", plugin.CATEGORY_RAW),
        ("anything/clip.mp4", plugin.CATEGORY_RAW),
        ("data/processed/layer_b/audio/x.json", plugin.CATEGORY_PROCESSED),
        ("results/experiment_registry.jsonl", plugin.CATEGORY_PROCESSED),
        ("experiments/vision/abc/report.json", plugin.CATEGORY_PROCESSED),
        ("experiments/vision/abc/checkpoints/weights/best.pt", plugin.CATEGORY_CHECKPOINT),
        ("models/yolov8n.pt", plugin.CATEGORY_CHECKPOINT),
        ("configs/frozen_experiment_v1.yaml", plugin.CATEGORY_METADATA),
        ("data/ground_truth/authorized_reviewers.json", plugin.CATEGORY_METADATA),
        ("data/governance/stage21_promotion_receipt.json", plugin.CATEGORY_METADATA),
        ("docs/FINAL_ABLATION_MATRIX.md", plugin.CATEGORY_METADATA),
    ],
)
def test_categorize_repository_paths(rel: str, expected: str):
    assert plugin.categorize(REPO / rel)[0] == expected


@pytest.mark.parametrize(
    "rel",
    ["src/railway_detection/cli/main.py", "tests/conftest.py", "scripts/x.py", ".venv/lib/x.py"],
)
def test_code_directories_are_not_guarded(rel: str):
    assert plugin.categorize(REPO / rel)[0] is None


def test_paths_outside_the_repository_are_not_guarded(tmp_path: Path):
    assert plugin.categorize(tmp_path / "clip.mov")[0] is None


def test_symlink_into_protected_data_is_categorized_by_its_target(tmp_path: Path):
    link = tmp_path / "innocent.txt"
    link.symlink_to(REPO / "data/raw")
    assert plugin.categorize(link)[0] == plugin.CATEGORY_RAW


# --------------------------------------------------------------------------- live guard


def _run_probe(tmp_path: Path, body: str) -> tuple[subprocess.CompletedProcess, list[dict]]:
    test = tmp_path / "test_probe.py"
    test.write_text(
        f"import os, subprocess\nfrom pathlib import Path\nREPO = Path({str(REPO)!r})\n"
        + textwrap.dedent(body),
        encoding="utf-8",
    )
    log = tmp_path / "guard.jsonl"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "railway_detection.safety.access_guard_plugin",
            "--access-guard-log",
            str(log),
            "-p",
            "no:cacheprovider",
            "-q",
            "--no-header",
            "--rootdir",
            str(tmp_path),
            str(test),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=os.environ
        | {
            "PYTHONPATH": os.pathsep.join(
                filter(None, [str(REPO / "src"), os.environ.get("PYTHONPATH", "")])
            ),
            "PATH": "/usr/bin:/bin",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )
    events = (
        [json.loads(line) for line in log.read_text().splitlines() if line] if log.is_file() else []
    )
    return proc, events


def _blocked(events: list[dict]) -> list[dict]:
    return [e for e in events if e["blocked"]]


def test_guard_blocks_raw_media_read_before_opening(tmp_path: Path):
    proc, events = _run_probe(
        tmp_path,
        """
        def test_it():
            open(REPO / "data/raw/layer_b/v2/train_events/event_001/camera_front.mov", "rb")
    """,
    )
    assert proc.returncode == 1
    assert [e["category"] for e in _blocked(events)] == ["RAW_MEDIA"]


def test_guard_blocks_checkpoint_and_processed_reads(tmp_path: Path):
    proc, events = _run_probe(
        tmp_path,
        """
        def test_checkpoint():
            open(REPO / "experiments/vision/x/checkpoints/weights/best.pt", "rb")
        def test_processed():
            (REPO / "data/processed/layer_b/a.json").read_text()
        def test_results():
            os.listdir(REPO / "results")
    """,
    )
    assert proc.returncode == 1
    assert {e["category"] for e in _blocked(events)} == {"MODEL_CHECKPOINT", "PROCESSED_DATA"}
    assert len(_blocked(events)) == 3


def test_guard_blocks_pathlib_and_os_open_variants(tmp_path: Path):
    proc, events = _run_probe(
        tmp_path,
        """
        def test_pathlib():
            (REPO / "data/raw/x.wav").read_bytes()
        def test_os_open():
            os.open(str(REPO / "data/raw/x.wav"), os.O_RDONLY)
    """,
    )
    assert proc.returncode == 1
    assert len(_blocked(events)) == 2


def test_guard_blocks_subprocess_media_arguments_including_relative_ones(tmp_path: Path):
    proc, events = _run_probe(
        tmp_path,
        """
        def test_abs():
            subprocess.run(["ffprobe", str(REPO / "data/raw/layer_b/c.mov")])
        def test_rel():
            subprocess.run(["ffprobe", "data/raw/layer_b/c.mov"], cwd=REPO)
    """,
    )
    assert proc.returncode == 1
    assert len(_blocked(events)) == 2 and all(
        e["how"] == "subprocess-arg" for e in _blocked(events)
    )


def test_guard_records_attempts_stopped_at_the_media_operation_boundary(tmp_path: Path):
    """A denial raised by the operation-boundary guard must still be classified as a raw-media attempt."""
    proc, events = _run_probe(
        tmp_path,
        """
        def test_boundary():
            from railway_detection.safety.media_guard import require_media_authorization
            require_media_authorization(REPO / "data/raw/layer_b/v2/train_events/event_001/camera_front.mov", "READ_RAW_MEDIA")
    """,
    )
    assert proc.returncode == 1
    blocked = _blocked(events)
    assert [e["category"] for e in blocked] == ["RAW_MEDIA"]
    assert blocked[0]["how"] == "media-guard:READ_RAW_MEDIA"


def test_guard_blocks_writes_into_the_repository(tmp_path: Path):
    proc, events = _run_probe(
        tmp_path,
        """
        def test_write():
            open(REPO / "zz_guard_probe.txt", "w").write("x")
    """,
    )
    assert proc.returncode == 1
    assert [e["category"] for e in _blocked(events)] == ["REPO_WRITE"]
    assert not (REPO / "zz_guard_probe.txt").exists()


def test_guard_logs_but_allows_metadata_reads(tmp_path: Path):
    proc, events = _run_probe(
        tmp_path,
        """
        def test_meta():
            assert (REPO / "pyproject.toml").read_text()
    """,
    )
    assert proc.returncode == 0
    assert not _blocked(events)
    assert any(e["category"] == "METADATA" and e["path"] == "pyproject.toml" for e in events)


def test_guard_allows_temp_files_and_code(tmp_path: Path):
    proc, events = _run_probe(
        tmp_path,
        """
        def test_tmp(tmp_path):
            (tmp_path / "a.mov").write_bytes(b"x"); assert (tmp_path / "a.mov").read_bytes()
            import railway_detection.cli.main
    """,
    )
    assert proc.returncode == 0 and not _blocked(events)


def test_guard_requires_a_log_outside_the_repository():
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "railway_detection.safety.access_guard_plugin",
            "--access-guard-log",
            str(REPO / "guard.jsonl"),
            "--collect-only",
            "-q",
            "tests/conftest.py",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        env=os.environ
        | {
            "PYTHONPATH": os.pathsep.join(
                filter(None, [str(REPO / "src"), os.environ.get("PYTHONPATH", "")])
            ),
            "PATH": "/usr/bin:/bin",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )
    assert proc.returncode != 0 and "outside the repository" in (proc.stdout + proc.stderr)
    assert not (REPO / "guard.jsonl").exists()


# --------------------------------------------------------------------------- classification logic


def _result(events=None, *, exit_code=0, tests=None, armed=True, timed_out=False):
    return {
        "events": events or [],
        "exit_code": exit_code,
        "timed_out": timed_out,
        "armed": armed,
        "tests": tests or {"passed": 3, "failed": 0, "skipped": 0, "errors": 0},
    }


def _event(category, path, blocked=True, how="open"):
    return {
        "category": category,
        "path": path,
        "blocked": blocked,
        "how": how,
        "node": "t::test_x (call)",
    }


@pytest.fixture
def sample_test_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    f = tmp_path / "tests" / "test_sample.py"
    f.parent.mkdir()
    f.write_text("def test_a():\n    assert True\n", encoding="utf-8")
    monkeypatch.setattr(classify_mod, "REPO_ROOT", tmp_path)
    return "tests/test_sample.py"


def test_classification_precedence_raw_over_checkpoint_over_processed(sample_test_file):
    events = [
        _event("PROCESSED_DATA", "results/a.json"),
        _event("MODEL_CHECKPOINT", "models/m.pt"),
        _event("RAW_MEDIA", "data/raw/x.mov"),
    ]
    entry = classify_mod.classify(sample_test_file, _result(events))
    assert entry["category"] == am.RAW_MEDIA_ACCESS and not entry["safe_for_synthetic_runner"]
    assert "data/raw/x.mov" in entry["reason"]
    entry = classify_mod.classify(sample_test_file, _result(events[:2]))
    assert entry["category"] == am.MODEL_CHECKPOINT_ACCESS
    entry = classify_mod.classify(sample_test_file, _result(events[:1]))
    assert entry["category"] == am.PROCESSED_DATA_ACCESS


def test_metadata_only_and_synthetic_only(sample_test_file):
    meta = [_event("METADATA", "configs/a.yaml", blocked=False)]
    entry = classify_mod.classify(sample_test_file, _result(meta))
    assert entry["category"] == am.METADATA_ONLY and entry["safe_for_synthetic_runner"]
    assert entry["access_dirs"] == ["configs"]
    entry = classify_mod.classify(sample_test_file, _result())
    assert entry["category"] == am.SYNTHETIC_ONLY and entry["safe_for_synthetic_runner"]


@pytest.mark.parametrize(
    "result",
    [
        _result(timed_out=True, exit_code=-1),
        _result(armed=False),
        _result(tests={"passed": 0, "failed": 0, "skipped": 0, "errors": 0}),
        _result(exit_code=2),
    ],
)
def test_undetermined_runs_are_unknown_and_unsafe(sample_test_file, result):
    entry = classify_mod.classify(sample_test_file, result)
    assert entry["category"] == am.UNKNOWN and not entry["safe_for_synthetic_runner"]


def test_a_child_process_spawner_is_never_safe(monkeypatch, tmp_path):
    f = tmp_path / "tests" / "test_spawn.py"
    f.parent.mkdir()
    f.write_text(
        "import subprocess\ndef test_a():\n    subprocess.run(['true'])\n", encoding="utf-8"
    )
    monkeypatch.setattr(classify_mod, "REPO_ROOT", tmp_path)
    entry = classify_mod.classify("tests/test_spawn.py", _result())
    assert (
        entry["category"] == am.UNKNOWN
        and entry["spawns_child_process"]
        and not entry["safe_for_synthetic_runner"]
    )


def test_unreviewed_spawner_with_the_plugin_named_is_still_unknown(monkeypatch, tmp_path):
    f = tmp_path / "tests" / "test_spawn2.py"
    f.parent.mkdir()
    f.write_text(
        "import subprocess\n# access_guard_plugin\ndef test_a():\n    subprocess.run(['true'])\n"
    )
    monkeypatch.setattr(classify_mod, "REPO_ROOT", tmp_path)
    entry = classify_mod.classify("tests/test_spawn2.py", _result())
    assert entry["category"] == am.UNKNOWN and entry["child_processes_guarded"] is False


def test_reviewed_guarded_spawner_stays_safe_and_says_why(monkeypatch, tmp_path):
    f = tmp_path / "tests" / "test_spawn3.py"
    f.parent.mkdir()
    f.write_text(
        "import subprocess\n# access_guard_plugin\ndef test_a():\n    subprocess.run(['true'])\n"
    )
    monkeypatch.setattr(classify_mod, "REPO_ROOT", tmp_path)
    monkeypatch.setitem(
        classify_mod.GUARDED_SPAWNERS, "tests/test_spawn3.py", "children run under the guard"
    )
    entry = classify_mod.classify("tests/test_spawn3.py", _result())
    assert entry["category"] == am.SYNTHETIC_ONLY and entry["child_processes_guarded"] is True
    assert "reviewed as guarded" in entry["reason"]


def test_static_scan_reports_protected_literals_but_not_mere_mentions_of_subprocess(tmp_path: Path):
    f = tmp_path / "test_x.py"
    f.write_text(
        'import subprocess\nP = "data/raw/layer_b/a.mov"\nsubprocess_name = "subprocess"\n'
    )
    hints, spawns = classify_mod.static_scan(f)
    assert hints == ["data/raw/layer_b/a.mov"] and spawns is False


# --------------------------------------------------------------------------- manifest verification


def _entry(path: Path, category=am.SYNTHETIC_ONLY, **over):
    entry = {
        "sha256": am.sha256_of(path),
        "category": category,
        "safe_for_synthetic_runner": category in am.SAFE_CATEGORIES,
        "reason": "specific reason that is long enough",
        "access_paths": [],
        "access_dirs": [],
        "blocked_attempts": {},
        "static_hints": [],
        "spawns_child_process": False,
        "child_processes_guarded": False,
        "tests": {"passed": 1, "failed": 0, "skipped": 0, "errors": 0},
        "evidence": "dynamic",
    }
    entry.update(over)
    return entry


@pytest.fixture
def tree(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("def test_a(): pass\n")
    (tmp_path / "tests" / "test_b.py").write_text("def test_b(): pass\n")
    manifest = {
        "schema_version": am.MANIFEST_SCHEMA,
        "test_files": {
            "tests/test_a.py": _entry(tmp_path / "tests/test_a.py"),
            "tests/test_b.py": _entry(tmp_path / "tests/test_b.py", am.METADATA_ONLY),
        },
    }
    return tmp_path, manifest


def test_complete_manifest_verifies(tree):
    root, manifest = tree
    assert am.verify_manifest_against_tree(manifest, root) == []


def test_unclassified_file_is_reported(tree):
    root, manifest = tree
    (root / "tests" / "test_new.py").write_text("def test_n(): pass\n")
    assert any(
        p.startswith("UNCLASSIFIED") for p in am.verify_manifest_against_tree(manifest, root)
    )


def test_ghost_entry_is_reported(tree):
    root, manifest = tree
    (root / "tests/test_b.py").unlink()
    assert any(p.startswith("GHOST_ENTRY") for p in am.verify_manifest_against_tree(manifest, root))


def test_changed_file_is_stale(tree):
    root, manifest = tree
    (root / "tests/test_a.py").write_text("def test_a(): open('data/raw/x.mov')\n")
    assert any(p.startswith("STALE") for p in am.verify_manifest_against_tree(manifest, root))


@pytest.mark.parametrize(
    ("mutation", "prefix"),
    [
        (lambda e: e.update(category="SAFE_ISH"), "BAD_CATEGORY"),
        (lambda e: e.update(safe_for_synthetic_runner=False), "INCONSISTENT_SAFETY_FLAG"),
        (lambda e: e.update(reason="same"), "GENERIC_REASON"),
        (lambda e: e.update(spawns_child_process=True), "UNOBSERVED_CHILD_PROCESS"),
        (
            lambda e: e.update(spawns_child_process=True, child_processes_guarded="yes"),
            "UNOBSERVED_CHILD_PROCESS",
        ),
        (lambda e: e.update(blocked_attempts={"RAW_MEDIA": 1}), "SAFE_BUT_BLOCKED"),
        (lambda e: e.pop("access_dirs"), "MALFORMED"),
    ],
)
def test_manifest_entry_defects_are_reported(tree, mutation, prefix):
    root, manifest = tree
    mutation(manifest["test_files"]["tests/test_a.py"])
    assert any(p.startswith(prefix) for p in am.verify_manifest_against_tree(manifest, root))


def test_unsafe_categories_can_never_be_selected(tree):
    root, manifest = tree
    manifest["test_files"]["tests/test_a.py"] = _entry(
        root / "tests/test_a.py", am.RAW_MEDIA_ACCESS
    )
    assert am.select_files(manifest) == ["tests/test_b.py"]
    with pytest.raises(am.ManifestError):
        am.select_files(manifest, frozenset({"NOT_A_CATEGORY"}))


def test_the_committed_manifest_matches_the_tree():
    manifest = am.load_manifest(REPO / am.MANIFEST_RELATIVE)
    assert am.verify_manifest_against_tree(manifest, REPO) == []


def test_every_committed_entry_has_a_specific_reason_not_boilerplate():
    manifest = am.load_manifest(REPO / am.MANIFEST_RELATIVE)
    reasons = [e["reason"] for e in manifest["test_files"].values()]
    assert len(set(reasons)) > len(reasons) * 0.5, "reasons look templated"
    assert not any("Uses in-memory objects, mock fixtures" in r for r in reasons)


def test_summary_counts_match_entries():
    manifest = am.load_manifest(REPO / am.MANIFEST_RELATIVE)
    entries = manifest["test_files"].values()
    assert manifest["summary"]["total_test_files"] == len(list(entries))
    for category in am.CATEGORIES:
        assert manifest["summary"][category.lower()] == sum(
            e["category"] == category for e in entries
        )


# --------------------------------------------------------------------------- runner


def test_runner_verify_log_flags_blocked_unarmed_and_undeclared_reads():
    manifest = {
        "test_files": {
            "tests/a.py": {"category": am.SYNTHETIC_ONLY, "access_dirs": []},
            "tests/b.py": {"category": am.METADATA_ONLY, "access_dirs": ["configs"]},
        }
    }
    armed = [
        {"how": "armed", "blocked": False, "category": "GUARD", "node": "<session>", "path": "-"},
        {
            "how": "disarmed",
            "blocked": False,
            "category": "GUARD",
            "node": "<session>",
            "path": "-",
        },
    ]
    selected = ["tests/a.py", "tests/b.py"]
    assert runner_mod.verify_log(armed, manifest, selected) == []
    kinds = lambda ev: {v["kind"] for v in runner_mod.verify_log(armed + ev, manifest, selected)}  # noqa: E731
    assert kinds([_event("RAW_MEDIA", "data/raw/x.mov")]) == {"BLOCKED_ACCESS"}
    assert kinds(
        [{**_event("METADATA", "configs/a.yaml", False), "node": "tests/a.py::t (call)"}]
    ) == {"UNDECLARED_METADATA_READ"}
    assert (
        kinds([{**_event("METADATA", "configs/a.yaml", False), "node": "tests/b.py::t (call)"}])
        == set()
    )
    assert kinds([{**_event("METADATA", "docs/a.md", False), "node": "tests/b.py::t (call)"}]) == {
        "UNDECLARED_METADATA_READ"
    }
    assert {v["kind"] for v in runner_mod.verify_log([], manifest, selected)} == {
        "GUARD_NOT_ARMED",
        "GUARD_NOT_DISARMED",
    }


def _runner_tree(
    tmp_path: Path, monkeypatch, body_by_file: dict[str, str], declared: dict[str, str]
):
    root = tmp_path / "tree"
    (root / "tests").mkdir(parents=True)
    entries = {}
    for name, body in body_by_file.items():
        f = root / "tests" / name
        f.write_text(textwrap.dedent(body), encoding="utf-8")
        entries[f"tests/{name}"] = _entry(f, declared[name])
    (root / "tests/test_access_classification.yaml").write_text(
        yaml.safe_dump({"schema_version": am.MANIFEST_SCHEMA, "test_files": entries}),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner_mod, "REPO_ROOT", root)
    return root


def test_runner_refuses_an_untrusted_manifest(tmp_path: Path, monkeypatch):
    root = _runner_tree(
        tmp_path,
        monkeypatch,
        {"test_ok.py": "def test_ok(): pass\n"},
        {"test_ok.py": am.SYNTHETIC_ONLY},
    )
    (root / "tests/test_extra.py").write_text("def test_x(): pass\n")  # unclassified
    report = tmp_path / "r.json"
    code = runner_mod.main(
        [
            "--report-path",
            str(report),
            "--manifest",
            str(root / "tests/test_access_classification.yaml"),
        ]
    )
    assert code == 3 and json.loads(report.read_text())["status"] == "MANIFEST_UNTRUSTED"


def test_runner_runs_only_safe_files_and_passes(tmp_path: Path, monkeypatch):
    root = _runner_tree(
        tmp_path,
        monkeypatch,
        {"test_ok.py": "def test_ok(): assert 1\n", "test_raw.py": "def test_raw(): open('x')\n"},
        {"test_ok.py": am.SYNTHETIC_ONLY, "test_raw.py": am.RAW_MEDIA_ACCESS},
    )
    report = tmp_path / "r.json"
    code = runner_mod.main(
        [
            "--report-path",
            str(report),
            "--manifest",
            str(root / "tests/test_access_classification.yaml"),
        ]
    )
    data = json.loads(report.read_text())
    assert code == 0 and data["status"] == "PASSED"
    assert data["selected"] == ["tests/test_ok.py"] and data["excluded"] == {
        "RAW_MEDIA_ACCESS": ["tests/test_raw.py"]
    }
    assert data["guard"]["blocked"] == 0 and data["tests"]["passed"] == 1


def test_runner_detects_a_misclassified_file_instead_of_trusting_the_manifest(
    tmp_path: Path, monkeypatch
):
    root = _runner_tree(
        tmp_path,
        monkeypatch,
        {
            "test_liar.py": f"def test_liar():\n    open({str(REPO / 'data/raw/layer_b/c.mov')!r}, 'rb')\n"
        },
        {"test_liar.py": am.SYNTHETIC_ONLY},
    )
    report = tmp_path / "r.json"
    code = runner_mod.main(
        [
            "--report-path",
            str(report),
            "--manifest",
            str(root / "tests/test_access_classification.yaml"),
        ]
    )
    data = json.loads(report.read_text())
    assert code == 4 and data["status"] == "CLASSIFICATION_VIOLATION"
    assert data["violations"][0]["kind"] == "BLOCKED_ACCESS" and data["guard"]["blocked"] == 1


def test_runner_rejects_unsafe_category_requests_and_in_repo_report_paths(tmp_path: Path):
    assert (
        runner_mod.main(
            ["--report-path", str(tmp_path / "r.json"), "--categories", "RAW_MEDIA_ACCESS"]
        )
        == 2
    )
    assert runner_mod.main(["--report-path", str(REPO / "r.json")]) == 2
    assert not (REPO / "r.json").exists()


def test_runner_dry_run_runs_nothing(tmp_path: Path, monkeypatch):
    root = _runner_tree(
        tmp_path,
        monkeypatch,
        {"test_ok.py": "def test_ok(): raise SystemExit(9)\n"},
        {"test_ok.py": am.SYNTHETIC_ONLY},
    )
    report = tmp_path / "r.json"
    code = runner_mod.main(
        [
            "--dry-run",
            "--report-path",
            str(report),
            "--manifest",
            str(root / "tests/test_access_classification.yaml"),
        ]
    )
    assert code == 0 and json.loads(report.read_text())["status"] == "DRY_RUN"
