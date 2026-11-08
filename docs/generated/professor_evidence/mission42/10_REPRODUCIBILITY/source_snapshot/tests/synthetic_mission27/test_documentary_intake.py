"""Explicit constructed, non-promotable evidence and malicious-input regressions."""

import json
import sqlite3
from dataclasses import asdict, replace

import pytest

from railway_detection.annotation.evidence_review.contracts import canonical, digest
from railway_detection.application.evidence_intake.intake import (
    CONSTRUCTED,
    DOCUMENTARY,
    EMPTY_HEAD,
    Attestation,
    DocumentaryJournal,
    Evidence,
    Scope,
    Status,
    parse_evidence,
)


def item(**changes):
    base = Evidence(
        "synthetic:permission",
        "RIGHTS",
        "synthetic:source",
        "synthetic:original-reference",
        "synthetic:owner",
        Scope(
            "synthetic:source",
            "M19-PERM-02",
            "synthetic:reviewer",
            "PRIMARY_REVIEWER",
            "blind review",
            "synthetic:workspace",
            ("ANNOTATION",),
        ),
        "2026-11-06",
        10,
        100,
        classification=CONSTRUCTED,
    )
    return replace(base, **changes)


class ConstructedVerifier:
    """Fixture only; cannot satisfy genuine acceptance or create observations."""

    def inspect(self, evidence, stage, now):
        return Attestation(
            digest(evidence),
            stage,
            digest(evidence.scope),
            evidence.issuing_authority,
            "synthetic:independent-verifier",
            "synthetic:verification-reference",
            10,
            100,
            False,
            CONSTRUCTED,
        )


def journal():
    return DocumentaryJournal(sqlite3.connect(":memory:"), constructed=True)


def advance(j, evidence, head, through=Status.ACCEPTED, verifier=None):
    for target in (
        Status.PARSED,
        Status.VALID,
        Status.ATTRIBUTABLE,
        Status.VERIFIED,
        Status.ACCEPTED,
    ):
        head = j.transition(
            evidence.evidence_id,
            target,
            request="synthetic:" + target,
            expected_head=head,
            now=20,
            reason="constructed software test",
            verifier=verifier or ConstructedVerifier(),
        )
        if target == through:
            break
    return head


def test_stages_are_distinct_and_constructed_acceptance_never_becomes_genuine():
    j = journal()
    e = item()
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    assert j.snapshot(expected_head=head, now=20)["evidence"][0]["effective_status"] == "SUBMITTED"
    head = advance(j, e, head)
    snapshot = j.snapshot(expected_head=head, now=20)
    assert len(snapshot["audit_history"]) == 6
    assert snapshot["evidence"][0]["effective_status"] == Status.ACCEPTED
    assert not snapshot["evidence"][0]["genuine_permission"]
    assert not snapshot["human_review_ready"] and snapshot["new_grants"] == 0
    with pytest.raises(PermissionError, match="genuine"):
        j.accepted_for(
            e.evidence_id, e.scope, expected_head=head, now=20, verifier=ConstructedVerifier()
        )


@pytest.mark.parametrize("target", [Status.ATTRIBUTABLE, Status.VERIFIED, Status.ACCEPTED])
def test_forged_appointment_reference_cannot_skip_verification_stages(target):
    j = journal()
    e = item(evidence_type="APPOINTMENT", source_reference="synthetic:forged-letter")
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    with pytest.raises(ValueError, match="skipped"):
        j.transition(
            e.evidence_id,
            target,
            request="synthetic:forge",
            expected_head=head,
            now=20,
            reason="constructed forged reference",
        )
    assert len(j.snapshot(expected_head=head, now=20)["audit_history"]) == 1


@pytest.mark.parametrize(
    "fault",
    [
        "missing_issuer",
        "unattributable_permission",
        "conflicting_rights",
        "expired_permission",
        "invalid_scope",
        "incomplete_package",
        "empty_rights",
        "false_qualification",
    ],
)
def test_unattributable_or_incomplete_evidence_never_reaches_attribution(fault):
    e = item()
    if fault == "missing_issuer":
        e = replace(e, issuing_authority=None)
    if fault == "unattributable_permission":
        e = replace(e, source_reference="synthetic:unknown")
    if fault == "conflicting_rights":
        e = replace(e, unresolved_conflicts=("synthetic:conflict",))
    if fault == "expired_permission":
        e = replace(e, expires=20)
    if fault == "invalid_scope":
        e = replace(e, scope=replace(e.scope, purpose=None))
    if fault == "incomplete_package":
        e = replace(e, valid_from=None, expires=None)
    if fault == "empty_rights":
        e = replace(e, scope=replace(e.scope, rights=()))
    if fault == "false_qualification":
        e = replace(e, evidence_type="QUALIFICATION")
    j = journal()
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    head = advance(j, e, head, through=Status.VALID)
    with pytest.raises((PermissionError, ValueError)):
        j.transition(
            e.evidence_id,
            Status.ATTRIBUTABLE,
            request="synthetic:invalid",
            expected_head=head,
            now=20,
            reason="constructed negative",
            verifier=None
            if fault in ("unattributable_permission", "false_qualification")
            else ConstructedVerifier(),
        )
    assert j.snapshot(expected_head=head, now=20)["evidence"][0]["recorded_status"] == Status.VALID


@pytest.mark.parametrize(
    "fault",
    [
        "wrong_source",
        "wrong_purpose",
        "wrong_stage",
        "wrong_digest",
        "revoked_permission",
        "expired_verification",
        "wrong_issuer",
        "same_person",
        "wrong_classification",
        "forged_qualification",
    ],
)
def test_malicious_verification_attestation_is_rejected(fault):
    j = journal()
    e = item(evidence_type="QUALIFICATION" if fault == "forged_qualification" else "RIGHTS")
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    head = advance(j, e, head, through=Status.VALID)

    class BadVerifier(ConstructedVerifier):
        def inspect(self, evidence, stage, now):
            a = super().inspect(evidence, stage, now)
            if fault == "wrong_source":
                return replace(a, scope_digest=digest(replace(e.scope, resource="synthetic:other")))
            if fault == "wrong_purpose":
                return replace(a, scope_digest=digest(replace(e.scope, purpose="other")))
            if fault == "wrong_stage":
                return replace(a, stage=Status.ACCEPTED)
            if fault == "wrong_digest":
                return replace(a, evidence_digest="f" * 64)
            if fault == "revoked_permission":
                return replace(a, revoked=True)
            if fault == "expired_verification":
                return replace(a, expires=20)
            if fault == "wrong_issuer":
                return replace(a, issuer="synthetic:forged-owner")
            if fault == "same_person":
                return replace(a, verifier_principal=e.scope.actor)
            if fault == "wrong_classification":
                return replace(a, classification=DOCUMENTARY)
            return replace(a, verifier_principal=e.issuing_authority)

    with pytest.raises(PermissionError):
        j.transition(
            e.evidence_id,
            Status.ATTRIBUTABLE,
            request="synthetic:bad",
            expected_head=head,
            now=20,
            reason="constructed malicious receipt",
            verifier=BadVerifier(),
        )
    assert j.snapshot(expected_head=head, now=20)["evidence"][0]["recorded_status"] == Status.VALID


def test_unknown_dates_are_not_expired_and_do_not_mean_valid_permission():
    j = journal()
    e = item(valid_from=None, expires=None, documented_date=None)
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    assert (
        j.snapshot(expected_head=head, now=10000)["evidence"][0]["effective_status"]
        == Status.SUBMITTED
    )
    with pytest.raises(ValueError, match="inferred"):
        j.transition(
            e.evidence_id,
            Status.EXPIRED,
            request="synthetic:expiry",
            expected_head=head,
            now=10000,
            reason="unknown dates",
        )


@pytest.mark.parametrize("terminal", [Status.REVOKED, Status.REJECTED, Status.EXPIRED])
def test_terminal_evidence_cannot_be_reaccepted_or_overwritten(terminal):
    j = journal()
    e = item()
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    head = j.transition(
        e.evidence_id,
        terminal,
        request="synthetic:terminal",
        expected_head=head,
        now=100,
        reason="constructed terminal status",
    )
    with pytest.raises(ValueError, match="terminal"):
        j.transition(
            e.evidence_id,
            Status.PARSED,
            request="synthetic:resurrect",
            expected_head=head,
            now=101,
            reason="invalid resurrection",
        )
    assert j.snapshot(expected_head=head, now=101)["evidence"][0]["effective_status"] == terminal


def test_expiry_boundary_is_exclusive_and_original_state_is_retained():
    j = journal()
    e = item()
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    head = advance(j, e, head)
    assert (
        j.snapshot(expected_head=head, now=99)["evidence"][0]["effective_status"] == Status.ACCEPTED
    )
    row = j.snapshot(expected_head=head, now=100)["evidence"][0]
    assert row["recorded_status"] == Status.ACCEPTED and row["effective_status"] == Status.EXPIRED


@pytest.mark.parametrize(
    "fault", ["duplicate_id", "altered_parent", "wrong_subject", "wrong_scope"]
)
def test_duplicate_or_substituted_lineage_rolls_back_without_partial_append(fault):
    j = journal()
    e = item()
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    replacement = replace(
        e, evidence_id="synthetic:new", parent_reference=digest(e), supersedes_reference=digest(e)
    )
    if fault == "duplicate_id":
        replacement = replace(replacement, evidence_id=e.evidence_id)
    if fault == "altered_parent":
        replacement = replace(replacement, parent_reference="f" * 64)
    if fault == "wrong_subject":
        replacement = replace(replacement, subject="synthetic:other")
    if fault == "wrong_scope":
        replacement = replace(replacement, scope=replace(e.scope, purpose="other"))
    with pytest.raises(ValueError):
        j.submit(replacement, request="synthetic:replacement", expected_head=head)
    assert len(j.snapshot(expected_head=head, now=20)["audit_history"]) == 1


def test_exact_retry_and_changed_request_are_distinguished():
    j = journal()
    e = item()
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    assert j.submit(e, request="synthetic:submit", expected_head=head) == head
    with pytest.raises(ValueError, match="substitution"):
        j.submit(
            replace(e, source_reference="synthetic:altered"),
            request="synthetic:submit",
            expected_head=head,
        )
    next_head = j.transition(
        e.evidence_id,
        Status.PARSED,
        request="synthetic:parse",
        expected_head=head,
        now=20,
        reason="constructed parse",
    )
    assert (
        j.transition(
            e.evidence_id,
            Status.PARSED,
            request="synthetic:parse",
            expected_head=next_head,
            now=20,
            reason="constructed parse",
        )
        == next_head
    )
    with pytest.raises(ValueError, match="substitution"):
        j.transition(
            e.evidence_id,
            Status.PARSED,
            request="synthetic:parse",
            expected_head=next_head,
            now=20,
            reason="changed request",
        )


@pytest.mark.parametrize("fault", ["truncate", "alter", "rehash"])
def test_replay_detects_tamper_against_retained_head(fault):
    j = journal()
    e = item()
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    if fault == "truncate":
        j.db.execute("DELETE FROM documentary_log")
    else:
        body = json.loads(j.db.execute("SELECT body FROM documentary_log").fetchone()[0])
        body["evidence"]["source_reference"] = "synthetic:altered"
        body = canonical(body)
        j.db.execute("UPDATE documentary_log SET body=?", (body,))
        if fault == "rehash":
            altered_head = digest(
                {"seq": 1, "request": "synthetic:submit", "body": body, "previous": EMPTY_HEAD}
            )
            j.db.execute("UPDATE documentary_log SET head=?", (altered_head,))
    j.db.commit()
    with pytest.raises(ValueError, match="lineage|head"):
        j.snapshot(expected_head=head, now=20)


def test_sqlite_failure_rolls_back_and_lost_response_retry_preserves_exact_record():
    j = journal()
    e = item()
    j.db.execute(
        "CREATE TRIGGER interrupt BEFORE INSERT ON documentary_log "
        "BEGIN SELECT RAISE(ABORT,'constructed interrupt'); END"
    )
    with pytest.raises(sqlite3.IntegrityError):
        j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    assert not j.snapshot(expected_head=EMPTY_HEAD, now=20)["evidence"]
    j.db.execute("DROP TRIGGER interrupt")
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    # Simulated lost response: same request and retained committed head retrieves history.
    assert j.submit(e, request="synthetic:submit", expected_head=head) == head
    assert len(j.snapshot(expected_head=head, now=20)["audit_history"]) == 1


def test_concurrent_writer_stale_head_refuses_and_reopen_replay_is_deterministic(tmp_path):
    path = tmp_path / "synthetic_documentary.sqlite"
    j = DocumentaryJournal(sqlite3.connect(path), constructed=True)
    other = DocumentaryJournal(sqlite3.connect(path), constructed=True)
    e = item()
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    with pytest.raises(ValueError, match="head"):
        other.submit(
            replace(e, evidence_id="synthetic:other"),
            request="synthetic:other",
            expected_head=EMPTY_HEAD,
        )
    assert j.snapshot(expected_head=head, now=20) == other.snapshot(expected_head=head, now=20)


@pytest.mark.parametrize(
    "body",
    [
        '{"scope":{},"evidence_id":"x","evidence_id":"y"}',
        '{"scope":{},"verified":true}',
        '{"scope":{},"evidence_type":"HUMAN_OBSERVATION"}',
    ],
)
def test_closed_json_cannot_assert_verification_or_inject_observations(body):
    with pytest.raises((ValueError, TypeError)):
        parse_evidence(body)


def test_constructed_observation_or_reviewer_evidence_cannot_be_promoted_as_genuine():
    e = item()
    body = asdict(e)
    body["classification"] = DOCUMENTARY
    with pytest.raises(ValueError, match="relabeled"):
        parse_evidence(canonical(body))
    with pytest.raises(PermissionError, match="separation"):
        DocumentaryJournal(sqlite3.connect(":memory:")).submit(
            e, request="synthetic:submit", expected_head=EMPTY_HEAD
        )
    with pytest.raises(ValueError, match="documentary evidence only"):
        replace(e, evidence_type="HUMAN_OBSERVATION").validate()


def test_linked_supersession_and_revocation_are_append_only():
    j = journal()
    e = item()
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    correction = replace(
        e, evidence_id="synthetic:new", parent_reference=digest(e), supersedes_reference=digest(e)
    )
    head = j.submit(correction, request="synthetic:correction", expected_head=head)
    revoke = replace(
        e, evidence_id="synthetic:revoke", evidence_type="REVOCATION", revokes_reference=digest(e)
    )
    head = j.submit(revoke, request="synthetic:revocation", expected_head=head)
    head = advance(j, revoke, head)
    rows = {r["evidence_id"]: r for r in j.snapshot(expected_head=head, now=20)["evidence"]}
    assert rows[e.evidence_id]["recorded_status"] == Status.REVOKED
    assert rows[e.evidence_id]["item"] == asdict(e)


def test_verification_expiry_is_effective_even_before_document_expiry():
    j = journal()
    e = item(expires=200)
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    head = advance(j, e, head)
    row = j.snapshot(expected_head=head, now=100)["evidence"][0]
    assert row["effective_status"] == Status.EXPIRED
    assert row["recorded_status"] == Status.ACCEPTED
    assert not row["currently_usable_for_operation"]


def test_explicit_nonexpiring_document_still_requires_current_independent_verification():
    j = journal()
    e = item(valid_from=None, expires=None, expiry_not_applicable=True)
    head = j.submit(e, request="synthetic:submit", expected_head=EMPTY_HEAD)
    head = advance(j, e, head, through=Status.VALID)
    with pytest.raises(PermissionError, match="unavailable"):
        j.transition(
            e.evidence_id,
            Status.ATTRIBUTABLE,
            request="synthetic:absent",
            expected_head=head,
            now=20,
            reason="constructed no-expiry claim",
        )
    head = advance_from_valid(j, e, head)
    assert (
        j.snapshot(expected_head=head, now=100)["evidence"][0]["effective_status"] == Status.EXPIRED
    )


def advance_from_valid(j, evidence, head):
    for target in (Status.ATTRIBUTABLE, Status.VERIFIED, Status.ACCEPTED):
        head = j.transition(
            evidence.evidence_id,
            target,
            request="synthetic:nonexpiring:" + target,
            expected_head=head,
            now=20,
            reason="constructed independent test",
            verifier=ConstructedVerifier(),
        )
    return head


def test_conflicting_expiry_applicability_is_rejected():
    with pytest.raises(ValueError, match="conflicting expiry"):
        item(expiry_not_applicable=True).validate()
