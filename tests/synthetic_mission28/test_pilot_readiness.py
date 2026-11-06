"""Read-only pilot diagnosis; all mutation scenarios are explicitly constructed tests."""

import copy
import json

import pytest

from railway_detection.application.evidence_intake import pilot
from railway_detection.application.preflight.engine import State
from railway_detection.cli.main import main


def test_exact_existing_pilot_is_not_ready_and_all_diagnostic_sources_remain_blocked():
    report = pilot.report(now=0)
    value = report["pilot"]
    assert value["state"] == "PILOT_NOT_READY"
    assert value["events"] == [
        "train_events/event_005",
        "train_events/event_021",
        "engine_events/event_001",
        "train_events/event_001",
        "no_train_events/event_001",
    ]
    assert tuple(s["source_id"] for s in value["sources"]) == pilot.SOURCE_IDS
    assert len(value["sources"]) == 10 and len(value["prerequisites"]) == 13
    assert all(s["preflight"]["state"] == State.BLOCKED for s in value["sources"])
    assert not value["authorization"] and not value["execution_receipt"]
    assert not value["grant_issued"] and not value["execution_permitted"]
    assert not report["new_original_evidence_received"]
    assert report["inventory"]["R04_count"] == 11 and not report["inventory"]["signoff"]
    assert sum(o["selection"] == "A" for o in report["operations"]) == 21
    assert sum(o["selection"] == "B" for o in report["operations"]) == 6


def test_pilot_diagnosis_is_deterministic_and_canonical_authorization_is_execution_only():
    a = pilot.report(now=0)
    assert a == pilot.report(now=0)
    entries = {r["id"]: r for r in a["pilot"]["prerequisites"]}
    assert entries["CANONICAL_AUTHORIZATION"]["required_for"] == "EXECUTION_ONLY"
    assert not a["pilot"]["optional_external_audit_is_universal_blocker"]
    assert not a["pilot"]["release_permission_required_for_private_pilot"]
    assert len(a["pilot"]["missing_services"]) == 6
    assert "DEFERRED" in a["pilot"]["T2"]
    assert a["pilot"]["canonical_plausibility_floor_seconds"] == 30


@pytest.mark.parametrize(
    "fault", ["missing_source", "wrong_event", "wrong_camera", "missing_rights"]
)
def test_substituted_documentary_pilot_source_is_not_silently_accepted(monkeypatch, fault):
    package = copy.deepcopy(pilot.load_package())
    source = next(s for s in package["sources"]["sources"] if s["source_id"] == pilot.SOURCE_IDS[0])
    if fault == "missing_source":
        package["sources"]["sources"].remove(source)
    if fault == "wrong_event":
        source["event"] = "CONSTRUCTED_TEST_NOT_GENUINE:wrong-event"
    if fault == "wrong_camera":
        source["camera"] = "back"
    if fault == "missing_rights":
        package["rights"]["sources"] = [
            s for s in package["rights"]["sources"] if s["source_id"] != pilot.SOURCE_IDS[0]
        ]
    monkeypatch.setattr(pilot, "load_package", lambda: package)
    with pytest.raises(ValueError, match="pilot|required"):
        pilot.report(now=0)


def test_changed_discovery_document_refuses_stale_binding(monkeypatch):
    original = pilot._metadata
    monkeypatch.setattr(
        pilot,
        "_metadata",
        lambda path: original(path) + " " if path.name == pilot.DISCOVERY else original(path),
    )
    with pytest.raises(ValueError, match="binding"):
        pilot.report(now=0)


def test_rehashed_unverified_original_submission_does_not_become_verification(monkeypatch):
    original = pilot._metadata
    document = json.loads(original(pilot.DOCS / pilot.DISCOVERY))
    document["actual_new_original_evidence_items"] = [
        {"source_reference": "CONSTRUCTED_TEST_NOT_GENUINE:forged-original", "verified": True}
    ]
    body = json.dumps(document)
    from railway_detection.safety.constructed_authority import sha

    binding = json.dumps({"schema": "MISSION28_BINDING/1", "discovery_sha256": sha(body)})
    monkeypatch.setattr(
        pilot, "_metadata", lambda path: body if path.name == pilot.DISCOVERY else binding
    )
    with pytest.raises(ValueError, match="independently verified intake"):
        pilot.report(now=0)


def test_rehashed_global_approval_flag_never_changes_pilot_readiness(monkeypatch):
    original = pilot._metadata
    document = json.loads(original(pilot.DOCS / pilot.DISCOVERY))
    document["approved"] = True
    document["qualified"] = True
    document["authorized"] = True
    body = json.dumps(document)
    from railway_detection.safety.constructed_authority import sha

    binding = json.dumps({"schema": "MISSION28_BINDING/1", "discovery_sha256": sha(body)})
    monkeypatch.setattr(
        pilot, "_metadata", lambda path: body if path.name == pilot.DISCOVERY else binding
    )
    value = pilot.report(now=0)["pilot"]
    assert value["state"] == "PILOT_NOT_READY" and not value["authorization"]
    assert not value["execution_permitted"]


def test_readiness_cli_exposes_diagnosis_without_executing_pilot(capsys):
    assert (
        main(
            [
                "application",
                "readiness",
                "report",
                "--mission",
                "28",
                "--now",
                "0",
                "--format",
                "json",
            ]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["pilot"]["state"] == "PILOT_NOT_READY"
    assert not report["operations_executed"]


def test_negative_clock_is_never_treated_as_current_authority_time():
    with pytest.raises(ValueError):
        pilot.report(now=-1)
