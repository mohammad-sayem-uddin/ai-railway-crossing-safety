import hashlib
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from railway_detection.application.contracts import (
    ApplicationRequest,
    EvidenceClass,
    EvidenceEnvelope,
    MetricContract,
)
from railway_detection.application.workflow import ConstructedApplication

ROOT = Path(__file__).resolve().parents[2]
CODE = "4" * 40


def request():
    return ApplicationRequest.constructed(code_identity=CODE)


def test_single_workflow_two_destinations_full_resume_and_typed_contracts(tmp_path):
    service = ConstructedApplication()
    a = service.run(tmp_path / "one", request())
    b = service.run(tmp_path / "two", request())
    assert a.to_json() == b.to_json() == service.verify(tmp_path / "one").to_json()
    assert [c.origin_us for c in a.cameras] == [0, 100_000]
    assert a.review.classification == "CONSTRUCTED_REVIEW_FIXTURE"
    assert not a.genuine_evidence and not a.authorization.genuine_evidence
    assert all(type(m.never_protected_m5) is int for m in a.metric_contracts)
    assert all(
        not o["active"] and o["logical_command"] is None
        for o in json.loads(a.inactive_comparator_json)
    )
    assert (tmp_path / "one/workflow/snapshot/SOURCE_MANIFEST.json").read_bytes() == (
        tmp_path / "two/workflow/snapshot/SOURCE_MANIFEST.json"
    ).read_bytes()
    assert "UNAVAILABLE" in (tmp_path / "one/workflow/results_absent_report.md").read_text()


@pytest.mark.parametrize(
    "change",
    [
        {"classification": EvidenceClass.EXTERNAL},
        {"classification": EvidenceClass.PENDING},
        {"seed": True},
        {"crossing": "crossing_B"},
        {"event": "synthetic:other"},
        {"schema": "CONSTRUCTED_APPLICATION/0"},
    ],
)
def test_invalid_application_identity_refuses_before_persistence(tmp_path, change):
    out = tmp_path / "never_created"
    with pytest.raises(ValueError):
        ConstructedApplication().run(out, replace(request(), **change))
    assert not out.exists()


@pytest.mark.parametrize(
    "stage", ["initialization", "review_commit", "review", "workflow", "application_receipt"]
)
def test_actual_cli_interruption_restart_and_duplicate_recovery(tmp_path, stage):
    output = tmp_path / "interrupted"
    base = [
        sys.executable,
        "-m",
        "railway_detection",
        "application",
        "demo",
        "--output",
        str(output),
        "--code-identity",
        CODE,
    ]
    child = subprocess.run(
        base + ["--interrupt-after", stage], cwd=ROOT, text=True, capture_output=True
    )
    assert child.returncode == 75, child.stdout + child.stderr
    assert not (output / "APPLICATION_COMPLETE.json").exists()
    resumed = subprocess.run(base + ["--resume"], cwd=ROOT, text=True, capture_output=True)
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    direct = ConstructedApplication().run(tmp_path / "direct", request())
    assert (output / "APPLICATION.json").read_text() == direct.to_json()
    assert ConstructedApplication().verify(output).to_json() == direct.to_json()


@pytest.mark.parametrize(
    "fault", ["application", "marker", "pending", "core", "missing_parent", "schema", "alias"]
)
def test_substituted_stale_incomplete_or_aliased_artifact_refuses(tmp_path, fault):
    out = tmp_path / "run"
    service = ConstructedApplication()
    service.run(out, request())
    if fault == "application":
        p = out / "APPLICATION.json"
        body = json.loads(p.read_text())
        body["genuine_evidence"] = True
        p.write_text(json.dumps(body))
        marker = json.loads((out / "APPLICATION_COMPLETE.json").read_text())
        marker["artifacts"]["APPLICATION.json"] = hashlib.sha256(p.read_bytes()).hexdigest()
        (out / "APPLICATION_COMPLETE.json").write_text(json.dumps(marker))
    elif fault == "marker":
        (out / "APPLICATION_COMPLETE.json").write_text('{"schema":"unknown"}')
    elif fault == "pending":
        (out / "APPLICATION.json.pending").write_text("{")
    elif fault == "core":
        (out / "workflow/execution.json").write_text("{}")
    elif fault == "missing_parent":
        (out / "workflow").rename(out / "saved_workflow")
    elif fault == "schema":
        body = json.loads((out / "APPLICATION_REQUEST.json").read_text())
        body["schema"] = "CONSTRUCTED_APPLICATION/0"
        (out / "APPLICATION_REQUEST.json").write_text(json.dumps(body))
    else:
        (out / "APPLICATION.json").unlink()
        (out / "APPLICATION.json").symlink_to(tmp_path / "UNREADABLE")
    with pytest.raises((ValueError, OSError)):
        service.verify(out)


def test_protected_output_and_genuine_record_fences(tmp_path):
    with pytest.raises(ValueError, match="protected"):
        ConstructedApplication().run(ROOT / "data/raw/never_created", request())
    for classification in EvidenceClass:
        with pytest.raises(PermissionError):
            EvidenceEnvelope(
                classification, "synthetic:event", "synthetic:source"
            ).require_genuine()
    assert MetricContract("back", None, None, reason="censored").never_protected_m5 is None
    with pytest.raises(ValueError):
        MetricContract("back", False, True)
    with pytest.raises(ValueError):
        MetricContract("back", None, None)
    body = json.loads(request().to_json())
    body["approved"] = True
    with pytest.raises(ValueError):
        ApplicationRequest.from_json(json.dumps(body))


def test_duplicate_request_fields_are_not_silently_overwritten():
    duplicate = request().to_json().rstrip()[:-1] + ',"seed":22}'
    with pytest.raises(ValueError, match="duplicate JSON"):
        ApplicationRequest.from_json(duplicate)


def test_injected_workflow_must_return_typed_constructed_contract(tmp_path):
    from railway_detection.application.workflow import ExistingWorkflowAdapter

    class SubstitutingAdapter:
        def execute(self, *args, **kwargs):
            value = ExistingWorkflowAdapter().execute(*args, **kwargs)
            return replace(
                value, review=replace(value.review, classification="MOCK_PRINCIPAL_ONLY")
            )

    with pytest.raises(ValueError, match="classifications must remain separate"):
        ConstructedApplication(SubstitutingAdapter()).run(tmp_path / "substituted", request())
    assert not (tmp_path / "substituted/APPLICATION_COMPLETE.json").exists()


@pytest.mark.parametrize(
    "fault", ["corrupt_database", "old_service_schema", "missing_checkpoint_parent"]
)
def test_interrupted_application_does_not_repair_invalid_persisted_state(tmp_path, fault):
    import sqlite3

    output = tmp_path / "interrupted"
    application = ConstructedApplication()
    with pytest.raises(InterruptedError):
        application.run(output, request(), stop_after="review")
    if fault == "corrupt_database":
        (output / "workflow/constructed.sqlite").write_bytes(b"CORRUPT_CONSTRUCTED_DB")
    elif fault == "missing_checkpoint_parent":
        (output / "workflow/constructed.sqlite").unlink()
    else:
        db = sqlite3.connect(output / "workflow/constructed.sqlite")
        db.execute("UPDATE constructed_review_service SET version='CONSTRUCTED_REVIEW_FIXTURE/0'")
        db.commit()
        db.close()
    with pytest.raises((ValueError, sqlite3.Error)):
        application.run(output, request(), resume=True)
    assert not (output / "APPLICATION_COMPLETE.json").exists()
