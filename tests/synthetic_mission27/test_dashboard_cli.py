"""Documentary CLI and fail-closed activation, with no actual evidence submissions."""

import io
import json
from pathlib import Path

import pytest

from railway_detection.annotation.evidence_review.contracts import canonical
from railway_detection.application.evidence_intake import cli, reporting
from railway_detection.application.evidence_intake.intake import EMPTY_HEAD, Scope
from railway_detection.application.evidence_intake.ports import ActivationPorts
from railway_detection.application.preflight.catalog import (
    ROOT,
    current_request,
    engine,
    load_catalog,
)
from railway_detection.application.preflight.engine import State
from railway_detection.cli.main import main


def test_dashboard_preserves_all_operation_selections_and_separates_evidence_stages():
    a = reporting.dashboard(now=1794009600)
    assert a == reporting.dashboard(now=1794009600)
    assert a["schema"] == "MISSION27_READINESS_DASHBOARD/1"
    assert len(a["documentary_evidence_found"]) == 15
    assert not any(a["evidence_stages"].values())
    assert sum(o["selection"] == "A" for o in a["operations"]) == 21
    assert sum(o["selection"] == "B" for o in a["operations"]) == 6
    assert sum(o["preflight"]["state"] == State.BLOCKED for o in a["operations"]) == 21
    assert sum(o["preflight"]["state"] == State.PROHIBITED for o in a["operations"]) == 6
    assert not a["human_review_ready"] and not a["trusted_adapters_enabled"]
    assert not a["operations_authorized"] and not a["operations_executed"]
    assert "submitted" in reporting.render(
        a
    ) and "Unknown is distinct from denied" in reporting.render(a)


def test_new_readiness_option_and_evidence_report_produce_identical_json(capsys):
    assert (
        main(
            [
                "application",
                "readiness",
                "report",
                "--mission",
                "27",
                "--format",
                "json",
                "--now",
                "0",
            ]
        )
        == 0
    )
    a = json.loads(capsys.readouterr().out)
    assert main(["application", "evidence", "report", "--format", "json", "--now", "0"]) == 0
    b = json.loads(capsys.readouterr().out)
    assert a == b and not a["operations_executed"]


def test_altered_documentary_binding_refuses_before_dashboard_composition(monkeypatch):
    original = reporting._metadata

    def changed(path):
        value = original(path)
        if path.name == reporting.FILES["evidence"]:
            return value.replace('"submitted_items": []', '"submitted_items": [{"verified": true}]')
        return value

    monkeypatch.setattr(reporting, "_metadata", changed)
    with pytest.raises(ValueError, match="binding"):
        reporting.dashboard(now=0)


def test_unreviewed_submission_is_never_assumed_accepted_by_dashboard(monkeypatch):
    package = reporting.load_package()
    package["evidence"]["submitted_items"] = [{"verified": True}]
    monkeypatch.setattr(reporting, "load_package", lambda: package)
    with pytest.raises(ValueError, match="independently reviewed"):
        reporting.dashboard(now=0)


@pytest.mark.parametrize(
    "candidate",
    [
        ROOT / "data/raw/source_documentary.sqlite",
        ROOT / "results/reviews_documentary.sqlite",
        ROOT / "experiments/cache_documentary.sqlite",
        ROOT / "models/weights_documentary.sqlite",
        ROOT / "outputs/review_documentary.sqlite",
        Path("/tmp/source.mp4"),
        Path("/tmp/documentary/../source_documentary.sqlite"),
    ],
)
def test_no_protected_path_is_probed_or_opened_as_documentary_journal(candidate, monkeypatch):
    monkeypatch.setattr(
        Path, "is_symlink", lambda *a: (_ for _ in ()).throw(AssertionError("probed"))
    )
    with pytest.raises(ValueError):
        cli.journal_path(str(candidate))


def test_journal_parent_alias_refuses_before_connect(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="aliases"):
        cli.journal_path(str(alias / "candidate_documentary.sqlite"))


def test_documentary_cli_refuses_attribution_of_constructed_adversarial_reference(
    tmp_path, monkeypatch, capsys
):
    path = tmp_path / "candidate_documentary.sqlite"
    # Deliberately non-synthetic strings represent unverified adversarial input, not real evidence.
    e = {
        "evidence_id": "adversarial-input-1",
        "evidence_type": "APPOINTMENT",
        "subject": "CONSTRUCTED_TEST_NOT_GENUINE:unverified-person",
        "source_reference": "CONSTRUCTED_TEST_NOT_GENUINE:forged-appointment-reference",
        "issuing_authority": None,
        "scope": {
            "resource": "CONSTRUCTED_TEST_NOT_GENUINE:unverified-resource",
            "operation": None,
            "actor": None,
            "role": None,
            "purpose": None,
            "environment": None,
            "rights": [],
        },
    }
    prefix = ["application", "evidence"]
    assert main(prefix + ["init", "--journal", str(path), "--now", "20"]) == 0
    head = json.loads(capsys.readouterr().out)["head"]
    assert head == EMPTY_HEAD
    monkeypatch.setattr("sys.stdin", io.StringIO(canonical(e)))
    assert (
        main(
            prefix
            + [
                "submit",
                "--journal",
                str(path),
                "--now",
                "20",
                "--request",
                "adversarial-submit",
                "--expected-head",
                head,
            ]
        )
        == 0
    )
    head = json.loads(capsys.readouterr().out)["head"]
    for target in ["PARSED", "STRUCTURALLY_VALID"]:
        assert (
            main(
                prefix
                + [
                    "advance",
                    "--journal",
                    str(path),
                    "--now",
                    "20",
                    "--request",
                    target,
                    "--expected-head",
                    head,
                    "--evidence-id",
                    e["evidence_id"],
                    "--target",
                    target,
                    "--reason",
                    "adversarial document test",
                ]
            )
            == 0
        )
        head = json.loads(capsys.readouterr().out)["head"]
    assert (
        main(
            prefix
            + [
                "advance",
                "--journal",
                str(path),
                "--now",
                "20",
                "--request",
                "attribution",
                "--expected-head",
                head,
                "--evidence-id",
                e["evidence_id"],
                "--target",
                "ATTRIBUTABLE",
                "--reason",
                "unverified reference is insufficient",
            ]
        )
        == 3
    )
    assert json.loads(capsys.readouterr().out)["status"] == "BLOCKED"
    assert (
        main(prefix + ["inspect", "--journal", str(path), "--now", "20", "--expected-head", head])
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert not result["evidence"][0]["genuine_permission"] and not result["human_review_ready"]
    assert not result["authorized_operations"]
    assert main(prefix + ["init", "--journal", str(path), "--now", "20"]) == 2


def test_absent_adapters_never_activate_source_player_or_human_review():
    ports = ActivationPorts()
    assert len(ports.missing()) == 6
    with pytest.raises(PermissionError, match="inactive"):
        ports.require_genuine_activation()


def test_preflight_receives_no_fabricated_claims_from_documentary_intake():
    catalog = load_catalog()
    q = current_request(catalog, "M19-PERM-19", catalog["sources"][0]["source_id"])
    result = engine(catalog).check(q, (), now=20)
    assert (
        result.state == State.BLOCKED and not result.grant_issued and not result.execution_permitted
    )


@pytest.mark.parametrize(
    "change",
    [
        {"operation": "unknown"},
        {"rights": ("ANNOTATION", "ANNOTATION")},
        {"rights": ("INVENTED_PERMISSION",)},
    ],
)
def test_invalid_operation_and_rights_scopes_refuse(change):
    scope = Scope("documentary-source", None, None, None, None, None)
    from dataclasses import replace

    with pytest.raises(ValueError):
        replace(scope, **change).validate()
