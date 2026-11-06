"""Constructed regression cases; never original evidence or real human qualifications."""

import io
import json
import sqlite3
from dataclasses import replace

import pytest
from tests.synthetic_mission27.test_documentary_intake import (
    ConstructedVerifier,
    advance,
    item,
    journal,
)

from railway_detection.annotation.evidence_review.contracts import canonical, digest
from railway_detection.application.evidence_intake.intake import (
    EMPTY_HEAD,
    DocumentaryJournal,
    Status,
)
from railway_detection.cli.main import main


def test_initialization_never_commits_an_existing_owner_transaction():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE owner_work (value TEXT)")
    connection.execute("INSERT INTO owner_work VALUES ('constructed-uncommitted')")
    assert connection.in_transaction
    with pytest.raises(ValueError, match="transaction"):
        DocumentaryJournal(connection, constructed=True)
    assert connection.in_transaction
    connection.rollback()
    assert connection.execute("SELECT * FROM owner_work").fetchall() == []
    assert (
        connection.execute("SELECT name FROM sqlite_master WHERE name='documentary_log'").fetchall()
        == []
    )


def test_explicit_nonexpiring_document_can_record_evidenced_verification_expiry():
    j = journal()
    e = item(valid_from=None, expires=None, expiry_not_applicable=True)
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    head = advance(j, e, head)
    assert (
        j.snapshot(expected_head=head, now=100)["evidence"][0]["effective_status"] == Status.EXPIRED
    )
    head = j.transition(
        e.evidence_id,
        Status.EXPIRED,
        request="synthetic:expire-verification",
        expected_head=head,
        now=100,
        reason="constructed attestation expired",
    )
    snapshot = j.snapshot(expected_head=head, now=100)
    assert snapshot["evidence"][0]["recorded_status"] == Status.EXPIRED
    assert not snapshot["evidence"][0]["genuine_permission"]


@pytest.mark.parametrize("retry_target", ["submit", "PARSED"])
def test_cli_exact_retry_after_later_write_returns_history_without_losing_current_head(
    tmp_path,
    monkeypatch,
    capsys,
    retry_target,
):
    path = tmp_path / "constructed_documentary.sqlite"
    prefix = ["application", "evidence"]
    assert main(prefix + ["init", "--journal", str(path), "--now", "20"]) == 0
    head = json.loads(capsys.readouterr().out)["head"]
    # Adversarial documentary-shaped fixture: explicitly marked and never authenticated.
    fixture = {
        "evidence_id": "CONSTRUCTED_TEST_NOT_GENUINE:retry",
        "evidence_type": "APPOINTMENT",
        "subject": "CONSTRUCTED_TEST_NOT_GENUINE:person",
        "source_reference": "CONSTRUCTED_TEST_NOT_GENUINE:unverified-reference",
        "issuing_authority": None,
        "scope": {
            "resource": "CONSTRUCTED_TEST_NOT_GENUINE:source",
            "operation": None,
            "actor": None,
            "role": None,
            "purpose": None,
            "environment": None,
        },
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(canonical(fixture)))
    submit = prefix + [
        "submit",
        "--journal",
        str(path),
        "--now",
        "20",
        "--request",
        "fixture:submit",
    ]
    assert main(submit + ["--expected-head", head]) == 0
    submit_head = json.loads(capsys.readouterr().out)["head"]
    parsed = prefix + [
        "advance",
        "--journal",
        str(path),
        "--now",
        "20",
        "--request",
        "fixture:parsed",
        "--evidence-id",
        fixture["evidence_id"],
        "--target",
        "PARSED",
        "--reason",
        "constructed parse",
    ]
    assert main(parsed + ["--expected-head", submit_head]) == 0
    parsed_head = json.loads(capsys.readouterr().out)["head"]
    valid = prefix + [
        "advance",
        "--journal",
        str(path),
        "--now",
        "20",
        "--request",
        "fixture:valid",
        "--evidence-id",
        fixture["evidence_id"],
        "--target",
        "STRUCTURALLY_VALID",
        "--reason",
        "constructed validation",
    ]
    assert main(valid + ["--expected-head", parsed_head]) == 0
    current_head = json.loads(capsys.readouterr().out)["head"]
    monkeypatch.setattr("sys.stdin", io.StringIO(canonical(fixture)))
    command = submit if retry_target == "submit" else parsed
    assert main(command + ["--expected-head", current_head]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["head"] == current_head and len(result["audit_history"]) == 3
    assert result["request_result_head"] == (
        submit_head if retry_target == "submit" else parsed_head
    )
    assert not result["authorized_operations"] and not result["human_review_ready"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("resource", "synthetic:other-source"),
        ("operation", "M19-PERM-03"),
        ("actor", "synthetic:other-actor"),
        ("role", "ADJUDICATOR"),
        ("purpose", "synthetic:other-purpose"),
        ("environment", "synthetic:other-environment"),
        ("rights", ("TRAINING",)),
    ],
)
def test_constructed_accepted_evidence_never_leaks_across_scope(field, value):
    j = journal()
    e = item()
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    head = advance(j, e, head, verifier=ConstructedVerifier())
    changed_scope = replace(e.scope, **{field: value})
    replacement = replace(
        e,
        evidence_id="synthetic:cross-scope-replacement",
        scope=changed_scope,
        parent_reference=digest(e),
        supersedes_reference=digest(e),
    )
    with pytest.raises(ValueError, match="cross-subject/scope"):
        j.submit(replacement, request="synthetic:cross-scope", expected_head=head)
    with pytest.raises(PermissionError):
        j.accepted_for(
            e.evidence_id,
            changed_scope,
            expected_head=head,
            now=20,
            verifier=ConstructedVerifier(),
        )
    assert not j.snapshot(expected_head=head, now=20)["evidence"][0]["genuine_permission"]


def test_historical_retry_does_not_reverify_or_resurrect_revoked_evidence():
    j = journal()
    e = item()
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    head = advance(j, e, head)
    revoked = j.transition(
        e.evidence_id,
        Status.REVOKED,
        request="synthetic:revoke",
        expected_head=head,
        now=21,
        reason="constructed local revocation",
    )
    assert j.submit(e, request="synthetic:submit", expected_head=revoked) != revoked
    assert (
        j.snapshot(expected_head=revoked, now=21)["evidence"][0]["recorded_status"]
        == Status.REVOKED
    )
    with pytest.raises(PermissionError):
        j.accepted_for(e.evidence_id, e.scope, expected_head=revoked, now=21)
