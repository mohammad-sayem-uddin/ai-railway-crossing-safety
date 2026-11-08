"""Actual SQLite rollback, lost-response recovery, quota and tamper refusals."""

import sqlite3
from dataclasses import asdict, replace

import pytest
from tests.synthetic_mission25.test_contracts import CODE, assignment

from railway_detection.annotation.evidence_review.contracts import digest
from railway_detection.annotation.evidence_review.integration import (
    fixture_contracts,
    open_fixture_journal,
)
from railway_detection.annotation.evidence_review.journal import ConstructedGovernanceJournal


def setup(db):
    _, b, r, p = fixture_contracts(CODE)
    j, scopes = open_fixture_journal(db, b, r, p, anchor=(0, None))
    args = {"assignment": asdict(assignment(b, r[0], p[0]))}
    return j, scopes, b, r, p, args


def perform(j, scopes, p, args, **extra):
    return j.perform(
        scopes[0],
        request_id="synthetic:request:assign",
        operation="ASSIGN",
        arguments=args,
        permission=p[0],
        **extra,
    )


def test_atomic_governance_assignment_quota_authority_journal_and_duplicate(tmp_path):
    with sqlite3.connect(tmp_path / "constructed.sqlite") as db:
        j, scopes, _, _, p, args = setup(db)
        result = perform(j, scopes, p, args)
        anchor = j.anchor
        assert perform(j, scopes, p, args) == result
        assert j.anchor == anchor
        assert db.execute("SELECT count(*) FROM governance_log").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM entries").fetchone()[0] == 1
        assert (
            db.execute("SELECT uses FROM sessions WHERE id=?", (scopes[0].session,)).fetchone()[0]
            == 1
        )
        assert len(j.restore().assignments) == 1
        args["assignment"]["role"] = "ADJUDICATOR"
        with pytest.raises(ValueError, match="substitution"):
            perform(j, scopes, p, args)
        assert j.anchor == anchor


@pytest.mark.parametrize("interruption", ["before_commit", "after_commit"])
def test_real_sqlite_crash_boundary_preserves_prefix_and_requires_exact_recovery(
    tmp_path, interruption
):
    db_path = tmp_path / "constructed.sqlite"
    with sqlite3.connect(db_path) as db:
        j, scopes, b, r, p, args = setup(db)
        with pytest.raises(InterruptedError):
            perform(j, scopes, p, args, interrupt=interruption)
        assert j.anchor == (0, None)
        if interruption == "before_commit":
            assert db.execute("SELECT count(*) FROM governance_log").fetchone()[0] == 0
            assert db.execute("SELECT count(*) FROM entries").fetchone()[0] == 0
            assert not j.restore().assignments
            perform(j, scopes, p, args)
        else:
            assert db.execute("SELECT count(*) FROM governance_log").fetchone()[0] == 1
            with pytest.raises(ValueError, match="prefix"):
                j.restore()
            with pytest.raises(ValueError, match="exact next"):
                j.recover(scopes[0], request_id="synthetic:wrong-request")
            j.recover(scopes[0], request_id="synthetic:request:assign")
            perform(j, scopes, p, args)
        anchor = j.anchor
    with sqlite3.connect(db_path) as db:
        reopened, _ = open_fixture_journal(db, b, r, p, anchor=anchor)
        assert reopened.restore().assignments[0].batch_digest == digest(b)
        assert reopened.anchor == anchor


@pytest.mark.parametrize(
    "fault",
    [
        "body",
        "result",
        "head",
        "parent",
        "sequence",
        "context",
        "missing_context",
        "authority_receipt",
        "authority_missing",
    ],
)
def test_tampered_governance_or_authority_history_cannot_be_replayed_or_recovered(fault):
    with sqlite3.connect(":memory:") as db:
        j, scopes, _, _, p, args = setup(db)
        perform(j, scopes, p, args)
        commands = {
            "body": "UPDATE governance_log SET body='{}'",
            "result": "UPDATE governance_log SET result='substituted'",
            "head": "UPDATE governance_log SET head='substituted'",
            "parent": "UPDATE governance_log SET previous='other'",
            "sequence": "UPDATE governance_log SET seq=2",
            "context": "UPDATE governance_context SET body='{}'",
            "missing_context": "DELETE FROM governance_context",
            "authority_receipt": "UPDATE tx SET receipt='{}'",
            "authority_missing": "DELETE FROM tx",
        }
        db.execute(commands[fault])
        with pytest.raises((ValueError, TypeError, KeyError)):
            if fault.startswith("authority"):
                perform(j, scopes, p, args)
            else:
                j.restore()


@pytest.mark.parametrize(
    "fault", ["revocation", "expiry", "fence", "actor", "event", "quota", "runtime", "purpose"]
)
def test_point_of_use_denies_before_governance_journal_mutation(fault):
    with sqlite3.connect(":memory:") as db:
        j, scopes, b, _, p, args = setup(db)
        scopes = list(scopes)
        permissions = list(p)
        if fault == "revocation":
            j.authority.revoke("synthetic:issuer", "synthetic:grant:0")
        elif fault == "expiry":
            scopes[0] = replace(scopes[0], now=1000)
        elif fault == "fence":
            scopes[0] = replace(scopes[0], fence=2)
        elif fault == "actor":
            scopes[0] = replace(scopes[0], actor=scopes[1].actor)
        elif fault == "event":
            args["assignment"]["event"] = "synthetic:other-event"
        elif fault == "quota":
            db.execute("UPDATE sessions SET uses=100")
        elif fault == "runtime":
            permissions[0] = replace(p[0], environment="other-runtime")
        elif fault == "purpose":
            permissions[0] = replace(p[0], purpose="other-purpose")
        with pytest.raises((ValueError, PermissionError)):
            perform(j, scopes, permissions, args)
        assert db.execute("SELECT count(*) FROM governance_log").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM entries").fetchone()[0] == 0
        assert j.anchor == (0, None)
        assert b.batch_id == "synthetic:mission25:batch"


def test_genuine_persistence_and_unknown_schema_never_silently_initialize():
    with sqlite3.connect(":memory:") as db:
        j, _, b, r, _, _ = setup(db)
        with pytest.raises(ValueError, match="genuine persistence disabled"):
            ConstructedGovernanceJournal(
                j.authority,
                replace(b, classification="UNVERIFIED_EXTERNAL_INPUT"),
                r,
                expected_anchor=(0, None),
            )
        db.execute("ALTER TABLE governance_log ADD COLUMN hidden TEXT")
        with pytest.raises(ValueError, match="schema changed"):
            ConstructedGovernanceJournal(j.authority, b, r, expected_anchor=(0, None))
