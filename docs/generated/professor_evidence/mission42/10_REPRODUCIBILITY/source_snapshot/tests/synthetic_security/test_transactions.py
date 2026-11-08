import sqlite3
from dataclasses import replace

import pytest

from railway_detection.safety.constructed_authority import (
    PROFILE,
    ConstructedAuthority,
    Grant,
    canonical,
    decode_payload,
    encode_payload,
    sha,
)


@pytest.fixture
def service(tmp_path):
    path = tmp_path / "constructed.sqlite"
    db = sqlite3.connect(path)
    a = ConstructedAuthority(
        db,
        appointments=(
            ("synthetic:issuer", ("ISSUER",)),
            ("synthetic:reviewer", ("REVIEWER",)),
            ("synthetic:promoter", ("PROMOTER",)),
        ),
        expected_context="synthetic:execution:exact",
        profile=PROFILE,
    )
    g = Grant(
        "synthetic:grant",
        "synthetic:reviewer",
        "synthetic:event",
        ("READ",),
        ("synthetic:neutral",),
        "constructed only",
        "synthetic:execution:exact",
        0,
        100,
        2,
    )
    a.issue("synthetic:issuer", g)
    yield a, g, path
    db.close()


def args(now=1):
    return dict(
        actor="synthetic:reviewer",
        operation="READ",
        resource="synthetic:neutral",
        context="synthetic:execution:exact",
        purpose="constructed only",
        now=now,
    )


def start(a, g):
    return a.reserve(
        g.grant_id, session="synthetic:session", initial_body=encode_payload({"init": 1}), **args()
    )


def test_durable_payload_receipt_reopen_and_idempotence(service):
    a, g, path = service
    f = start(a, g)
    body = encode_payload({"constructed": 7})
    assert a.prepare("synthetic:session", "synthetic:tx", body, fence=f, **args()) == "PREPARED"
    receipt = a.commit("synthetic:session", "synthetic:tx", fence=f, **args())
    assert a.commit("synthetic:session", "synthetic:tx", fence=f, **args()) == receipt
    assert a.audit(expected_head=receipt.head, expected_count=1)
    other = ConstructedAuthority(
        sqlite3.connect(path),
        appointments=tuple(a.roles.items()),
        expected_context=a.context,
        profile=PROFILE,
    )
    assert other.audit(expected_head=receipt.head, expected_count=1)
    assert other.commit("synthetic:session", "synthetic:tx", fence=f, **args()) == receipt
    other.db.close()


@pytest.mark.parametrize(
    "field,value",
    [
        ("actor", "synthetic:alias"),
        ("operation", "HASH"),
        ("resource", "synthetic:other"),
        ("context", "synthetic:changed-runtime"),
        ("now", 100),
        ("now", None),
    ],
)
def test_wrong_scope_denies_before_reservation(service, field, value):
    a, g, _ = service
    kw = args()
    kw[field] = value
    with pytest.raises(ValueError):
        a.reserve(g.grant_id, session="synthetic:session", initial_body=encode_payload({}), **kw)
    assert a.db.execute("SELECT count(*) FROM sessions").fetchone()[0] == 0


def test_no_self_elevation_or_mixed_reviewer_issuer(service):
    a, g, _ = service
    with pytest.raises(ValueError):
        a.issue("synthetic:reviewer", replace(g, grant_id="synthetic:forged"))
    with pytest.raises(ValueError):
        ConstructedAuthority(
            a.db,
            appointments=(("synthetic:r", ("REVIEWER", "ISSUER")),),
            expected_context=a.context,
            profile=PROFILE,
        )


def test_reservation_quota_retry_and_terminal_consumption(service):
    a, g, _ = service
    f = start(a, g)
    assert start(a, g) == f
    with pytest.raises((ValueError, sqlite3.IntegrityError)):
        a.reserve(g.grant_id, session="synthetic:second", initial_body=encode_payload({}), **args())
    for i in range(2):
        tx = "synthetic:t" + str(i)
        a.prepare("synthetic:session", tx, encode_payload({"n": i}), fence=f, **args())
        a.commit("synthetic:session", tx, fence=f, **args())
    with pytest.raises(ValueError):
        a.prepare("synthetic:session", "synthetic:third", encode_payload({}), fence=f, **args())
    a.finalize("synthetic:session", fence=f, **args())
    with pytest.raises(ValueError):
        start(a, g)


@pytest.mark.parametrize("order", ["revoke_before_commit", "commit_before_revoke"])
def test_revoke_commit_linearization(service, order):
    a, g, _ = service
    f = start(a, g)
    a.prepare("synthetic:session", "synthetic:tx", encode_payload({}), fence=f, **args())
    if order == "revoke_before_commit":
        a.revoke("synthetic:issuer", g.grant_id)
        with pytest.raises(ValueError):
            a.commit("synthetic:session", "synthetic:tx", fence=f, **args())
        assert a.audit(expected_head=None, expected_count=0)
    else:
        receipt = a.commit("synthetic:session", "synthetic:tx", fence=f, **args())
        a.revoke("synthetic:issuer", g.grant_id)
        assert a.audit(expected_head=receipt.head, expected_count=1)


def test_clock_rollback_and_recovery_fence(service):
    a, g, _ = service
    f = start(a, g)
    a.prepare("synthetic:session", "synthetic:tx", encode_payload({}), fence=f, **args(10))
    with pytest.raises(ValueError):
        a.prepare("synthetic:session", "synthetic:other", encode_payload({}), fence=f, **args(2))
    with pytest.raises(ValueError):
        a.recover("synthetic:session", **(args(10) | {"actor": "synthetic:other"}))
    new = a.recover("synthetic:session", **args(10))
    with pytest.raises(ValueError):
        a.commit("synthetic:session", "synthetic:tx", fence=f, **args(10))
    assert a.commit("synthetic:session", "synthetic:tx", fence=new, **args(10))


def test_unknown_effect_blocks_commit_and_finalization(service):
    a, g, _ = service
    f = start(a, g)
    a.prepare("synthetic:session", "synthetic:tx", encode_payload({}), fence=f, **args())
    with pytest.raises(ValueError, match="BUSY"):
        a.finalize("synthetic:session", fence=f, **args())
    a.mark_unknown("synthetic:session", "synthetic:tx", fence=f, **args())
    with pytest.raises(ValueError):
        a.commit("synthetic:session", "synthetic:tx", fence=f, **args())
    with pytest.raises(ValueError, match="BUSY"):
        a.finalize("synthetic:session", fence=f, **args())


@pytest.mark.parametrize(
    "body",
    [
        '{"schema":"CONSTRUCTED_ONLY","kind":"CONSTRUCTED_PAYLOAD","payload":0,"payload":1}',
        '{"schema":"CONSTRUCTED_ONLY","kind":"CONSTRUCTED_PAYLOAD","payload":1.0}',
        '{"schema":"CONSTRUCTED_ONLY","kind":"CONSTRUCTED_PAYLOAD","payload":"\\ud800"}',
        '{"schema":"CONSTRUCTED_ONLY","kind":"CONSTRUCTED_PAYLOAD","payload":"\\u0000"}',
        '{"schema":"APPROVED","kind":"CONSTRUCTED_PAYLOAD","payload":{}}',
    ],
)
def test_strict_codec_negatives(body):
    with pytest.raises(ValueError):
        decode_payload(body)


def test_anchor_truncation_and_recomputed_chain_quarantined(service):
    a, g, _ = service
    f = start(a, g)
    a.prepare("synthetic:session", "synthetic:tx", encode_payload({}), fence=f, **args())
    receipt = a.commit("synthetic:session", "synthetic:tx", fence=f, **args())
    a.db.execute("DELETE FROM entries")
    with pytest.raises(ValueError, match="anchor"):
        a.audit(expected_head=receipt.head, expected_count=1)


def test_atomic_create_only_qualified_publication_and_retry(service):
    a, g, _ = service
    objects = (("synthetic:train:event:1", encode_payload({"x": 1})),)
    receipt = a.publish_constructed_batch(
        promoter="synthetic:promoter",
        batch_id="synthetic:batch",
        objects=objects,
        approved_digest=sha(canonical(objects)),
    )
    assert (
        a.publish_constructed_batch(
            promoter="synthetic:promoter",
            batch_id="synthetic:batch",
            objects=objects,
            approved_digest=sha(canonical(objects)),
        )
        == receipt
    )
    conflicting = objects + (("synthetic:train:event:2", encode_payload({"x": 2})),)
    with pytest.raises(sqlite3.IntegrityError):
        a.publish_constructed_batch(
            promoter="synthetic:promoter",
            batch_id="synthetic:another",
            objects=conflicting,
            approved_digest=sha(canonical(conflicting)),
        )
    assert a.db.execute("SELECT count(*) FROM objects").fetchone()[0] == 1
    assert a.db.execute("SELECT count(*) FROM batches").fetchone()[0] == 1
    with pytest.raises(ValueError):
        a.publish_constructed_batch(
            promoter="synthetic:reviewer",
            batch_id="synthetic:bad",
            objects=objects,
            approved_digest=sha(canonical(objects)),
        )


def test_prepare_crash_reopen_and_failure_before_ack(service):
    a, g, path = service
    f = start(a, g)
    body = encode_payload({"value": 11})
    a.prepare("synthetic:session", "synthetic:tx", body, fence=f, **args())
    other = ConstructedAuthority(
        sqlite3.connect(path),
        appointments=tuple(a.roles.items()),
        expected_context=a.context,
        profile=PROFILE,
    )
    other.db.execute(
        "CREATE TRIGGER injected BEFORE INSERT ON entries "
        "BEGIN SELECT RAISE(ABORT,'constructed crash'); END"
    )
    with pytest.raises(sqlite3.IntegrityError):
        other.commit("synthetic:session", "synthetic:tx", fence=f, **args())
    assert other.audit(expected_head=None, expected_count=0)
    assert other.db.execute("SELECT state FROM tx").fetchone()[0] == "PREPARED"
    other.db.execute("DROP TRIGGER injected")
    receipt = other.commit("synthetic:session", "synthetic:tx", fence=f, **args())
    assert a.audit(expected_head=receipt.head, expected_count=1)
    a.db.execute("DELETE FROM tx")
    with pytest.raises(ValueError, match="acknowledged journal"):
        a.audit(expected_head=receipt.head, expected_count=1)
    other.db.close()


def test_transaction_scope_cannot_change_between_prepare_and_commit(service):
    a, g, _ = service
    g = replace(g, grant_id="synthetic:multi", operations=("READ", "HASH"))
    a.issue("synthetic:issuer", g)
    f = start(a, g)
    a.prepare("synthetic:session", "synthetic:tx", encode_payload({}), fence=f, **args())
    kw = args()
    kw["operation"] = "HASH"
    with pytest.raises(ValueError, match="binding changed"):
        a.commit("synthetic:session", "synthetic:tx", fence=f, **kw)
    assert a.audit(expected_head=None, expected_count=0)


def test_two_connections_one_reservation_winner(service):
    from concurrent.futures import ThreadPoolExecutor

    a, g, path = service

    def reserve(i):
        c = ConstructedAuthority(
            sqlite3.connect(path),
            appointments=tuple(a.roles.items()),
            expected_context=a.context,
            profile=PROFILE,
        )
        try:
            c.reserve(
                g.grant_id,
                session="synthetic:race:" + str(i),
                initial_body=encode_payload({}),
                **args(),
            )
            return "WIN"
        except sqlite3.IntegrityError:
            return "DENY"
        finally:
            c.db.close()

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(reserve, [0, 1])) == ["DENY", "WIN"]
    assert a.db.execute("SELECT count(*) FROM sessions").fetchone()[0] == 1


def test_constructed_service_rejects_real_profile_and_real_principal(service):
    a, g, _ = service
    with pytest.raises(ValueError):
        ConstructedAuthority(
            a.db,
            appointments=tuple(a.roles.items()),
            expected_context=a.context,
            profile="PROTECTED_BROKER",
        )
    with pytest.raises(ValueError):
        a.issue("synthetic:issuer", replace(g, grant_id="real:grant"))


def test_purpose_is_exact_at_every_use_boundary(service):
    a, g, _ = service
    wrong = args() | {"purpose": "unrelated analysis"}
    with pytest.raises(ValueError, match="scope/runtime"):
        a.reserve(g.grant_id, session="synthetic:session", initial_body=encode_payload({}), **wrong)
    fence = start(a, g)
    with pytest.raises(ValueError, match="scope/runtime"):
        a.prepare("synthetic:session", "synthetic:tx", encode_payload({}), fence=fence, **wrong)
    a.prepare("synthetic:session", "synthetic:tx", encode_payload({}), fence=fence, **args())
    with pytest.raises(ValueError, match="binding changed"):
        a.commit("synthetic:session", "synthetic:tx", fence=fence, **wrong)
    with pytest.raises(ValueError):
        a.recover("synthetic:session", **wrong)
    with pytest.raises(ValueError):
        a.mark_unknown("synthetic:session", "synthetic:tx", fence=fence, **wrong)


def test_issuer_cannot_grant_own_unappointed_review_role(service):
    a, g, _ = service
    with pytest.raises(ValueError, match="role unavailable"):
        a.issue("synthetic:issuer", replace(g, actor="synthetic:issuer"))
    g = replace(g, grant_id="synthetic:publish", operations=("PUBLISH",))
    with pytest.raises(ValueError, match="role unavailable"):
        a.issue("synthetic:issuer", g)


@pytest.mark.parametrize(
    "change", [{"now": 100}, {"now": None}, {"context": "synthetic:runtime:other"}]
)
def test_recovery_requires_current_scope_and_clock(service, change):
    a, g, _ = service
    start(a, g)
    with pytest.raises(ValueError):
        a.recover("synthetic:session", **(args() | change))
    assert a.db.execute("SELECT fence FROM sessions").fetchone()[0] == 1


def test_fresh_recovery_fences_finalization_and_unknown_effect(service):
    a, g, _ = service
    old = start(a, g)
    fresh = a.recover("synthetic:session", **args())
    with pytest.raises(ValueError, match="stale fence"):
        a.finalize("synthetic:session", fence=old, **args())
    a.prepare("synthetic:session", "synthetic:tx", encode_payload({}), fence=fresh, **args())
    with pytest.raises(ValueError, match="stale fence"):
        a.mark_unknown("synthetic:session", "synthetic:tx", fence=old, **args())
    a.commit("synthetic:session", "synthetic:tx", fence=fresh, **args())
    a.finalize("synthetic:session", fence=fresh, **args())
    with pytest.raises(ValueError, match="recovery only"):
        a.recover("synthetic:session", **args())


def test_operation_roles_rechecked_after_appointment_change(service):
    a, g, _ = service
    fence = start(a, g)
    a.roles[g.actor] = ("ISSUER",)
    with pytest.raises(ValueError, match="scope/runtime"):
        a.prepare("synthetic:session", "synthetic:tx", encode_payload({}), fence=fence, **args())
    assert a.audit(expected_head=None, expected_count=0)


def test_unknown_effect_cannot_quarantine_a_different_prepared_operation(service):
    a, g, _ = service
    g = replace(g, operations=("READ", "HASH"), grant_id="synthetic:both")
    a.issue("synthetic:issuer", g)
    fence = start(a, g)
    a.prepare("synthetic:session", "synthetic:tx", encode_payload({}), fence=fence, **args())
    with pytest.raises(ValueError, match="exact prepared operation"):
        a.mark_unknown(
            "synthetic:session", "synthetic:tx", fence=fence, **(args() | {"operation": "HASH"})
        )
    assert a.db.execute("SELECT state FROM tx").fetchone()[0] == "PREPARED"


def test_historical_receipt_retrieval_refuses_missing_acknowledged_entry(service):
    a, g, _ = service
    fence = start(a, g)
    a.prepare("synthetic:session", "synthetic:t", encode_payload({}), fence=fence, **args())
    a.commit("synthetic:session", "synthetic:t", fence=fence, **args())
    a.db.execute("DELETE FROM entries")
    with pytest.raises(ValueError, match="receipt ledger"):
        a.commit("synthetic:session", "synthetic:t", fence=fence, **args())
