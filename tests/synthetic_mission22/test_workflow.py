import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from railway_detection.data.constructed_manifest import manifest_digest
from railway_detection.synthetic.integration_contracts import join_lineage
from railway_detection.synthetic.integration_fixture import make_fixture
from railway_detection.synthetic.integration_workflow import run_demo

CODE = "0" * 40
ROOT = Path(__file__).resolve().parents[2]


def test_whole_demonstration_deterministic_all_packages(tmp_path):
    a = run_demo(tmp_path / "a", code_identity=CODE)
    b = run_demo(tmp_path / "b", code_identity=CODE)
    assert a == b
    assert a["classification"] == "CONSTRUCTED_EVENT_NOT_V2_OBSERVATION"
    assert not a["human_evidence"] and not a["promotion"] and not a["empirical_results"]
    assert a["B_metric_contracts"]["front"]["M4"] is False
    assert a["B_metric_contracts"]["back"]["M4"] is False
    assert a["simulations"]["front"]["result"]["causal"]["origin_us"] == 0
    assert a["simulations"]["back"]["result"]["causal"]["origin_us"] == 100_000
    assert a["separate_A_metric_receipt"]["runs"][0]["M4_M5_trajectory"].startswith("A_")
    assert a["lineage_CV"]["cv"]["score_count"] == 1
    assert a["mock_review"]["review_commit"]["count"] == 3
    assert a["mock_review"]["classification"] == "CONSTRUCTED_REVIEW_FIXTURE"
    assert "UNAVAILABLE" in (tmp_path / "a/results_absent_report.md").read_text()
    assert (tmp_path / "a/snapshot/SOURCE_MANIFEST.json").read_bytes() == (
        tmp_path / "b/snapshot/SOURCE_MANIFEST.json"
    ).read_bytes()
    assert run_demo(tmp_path / "a", code_identity=CODE, resume=True) == a


@pytest.mark.parametrize("stage", ["initialization", "review_commit", "review"])
def test_process_interruption_and_restart(tmp_path, stage):
    out = tmp_path / "interrupted"
    base = [
        sys.executable,
        str(ROOT / "scripts/run_mission22_demo.py"),
        "--output",
        str(out),
        "--code-identity",
        CODE,
    ]
    first = subprocess.run(base + ["--interrupt-after", stage], capture_output=True, text=True)
    assert first.returncode == 75, first.stdout + first.stderr
    assert not (out / "COMPLETE.json").exists()
    resumed = subprocess.run(base + ["--resume"], capture_output=True, text=True)
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    direct = run_demo(tmp_path / "uninterrupted", code_identity=CODE)
    assert json.loads((out / "execution.json").read_text()) == direct


@pytest.mark.parametrize("change", [{"seed": 23}, {"code_identity": "1" * 40}])
def test_stale_descriptor_denies(tmp_path, change):
    out = tmp_path / "run"
    run_demo(out, code_identity=CODE)
    kw = {"code_identity": CODE} | change
    with pytest.raises(ValueError, match="stale run"):
        run_demo(out, resume=True, **kw)


@pytest.mark.parametrize(
    "artifact",
    ["execution.json", "snapshot/docs/input_envelope.json", "snapshot/SOURCE_MANIFEST.json"],
)
def test_tampered_completed_artifacts_never_recertified(tmp_path, artifact):
    out = tmp_path / "run"
    run_demo(out, code_identity=CODE)
    (out / artifact).write_text("{}")
    with pytest.raises(ValueError, match="digest mismatch"):
        run_demo(out, code_identity=CODE, resume=True)


def test_completion_cannot_shrink_manifest_or_manufacture_human_evidence(tmp_path):
    out = tmp_path / "run"
    run_demo(out, code_identity=CODE)
    marker = json.loads((out / "COMPLETE.json").read_text())
    marker["artifacts"] = {}
    (out / "COMPLETE.json").write_text(json.dumps(marker))
    with pytest.raises(ValueError, match="closed complete"):
        run_demo(out, code_identity=CODE, resume=True)


@pytest.mark.parametrize(
    "fault",
    ["partial_write", "partial_snapshot", "missing_database", "corrupt_database", "old_schema"],
)
def test_incomplete_or_corrupt_state_is_quarantined(tmp_path, fault):
    out = tmp_path / "run"
    with pytest.raises(InterruptedError):
        run_demo(out, code_identity=CODE, stop_after="review")
    if fault == "partial_write":
        (out / "execution.json.pending").write_text("{")
    elif fault == "partial_snapshot":
        (out / "snapshot").mkdir()
    elif fault == "missing_database":
        (out / "constructed.sqlite").unlink()
    elif fault == "corrupt_database":
        (out / "constructed.sqlite").write_bytes(b"corrupt constructed state")
    else:
        import sqlite3

        db = sqlite3.connect(out / "constructed.sqlite")
        db.execute("UPDATE constructed_review_service SET version='CONSTRUCTED_REVIEW_FIXTURE/0'")
        db.commit()
        db.close()
    import sqlite3

    with pytest.raises((ValueError, sqlite3.Error)):
        run_demo(out, code_identity=CODE, resume=True)
    assert not (out / "COMPLETE.json").exists()


@pytest.mark.parametrize("fault", ["parent", "group", "source_hash", "fit_exposure"])
def test_lineage_cv_join_rejects_boundary_tampering(fault):
    f = make_fixture(code_identity=CODE)
    m = f["manifest"]
    records = list(m.records)
    if fault == "parent":
        records[-1] = replace(records[-1], parents=("synthetic:missing",))
    elif fault == "group":
        records[-1] = replace(records[-1], physical_event="synthetic:dev:0")
    elif fault == "source_hash":
        records[0] = replace(records[0], source_digest="f" * 64)
    else:
        records[-1] = replace(records[-1], fitted_exposure=())
    m = replace(m, records=tuple(records))
    with pytest.raises(ValueError):
        join_lineage(
            m,
            f["registry"],
            expected=f["expected_registry"],
            expected_manifest_digest=manifest_digest(m),
        )


def test_protected_output_path_denied_before_access(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("protected path must not reach resolution")

    monkeypatch.setattr(Path, "resolve", denied)
    # Module root resolution occurs first; use the lexical snapshot guard for
    # strict pre-stat enforcement, while CLI guard also checks canonical roots.
    from scripts.prepare_researcher_snapshot import SnapshotError, source_relative_path

    with pytest.raises(SnapshotError):
        source_relative_path("data/raw/source.json")
