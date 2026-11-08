import hashlib
import sqlite3
from dataclasses import replace

import pytest

from railway_detection.safety.constructed_authority import (
    PROFILE,
    ConstructedAuthority,
    Grant,
    canonical,
    encode_payload,
    sha,
)
from railway_detection.safety.constructed_broker import (
    ConstructedResource,
    ConstructedResourceBroker,
    resource_digest,
)


@pytest.fixture
def fixture():
    db = sqlite3.connect(":memory:")
    authority = ConstructedAuthority(
        db,
        appointments=(("synthetic:issuer", ("ISSUER",)), ("synthetic:r", ("REVIEWER",))),
        expected_context="synthetic:runtime",
        profile=PROFILE,
    )
    resource = ConstructedResource("synthetic:resource", "synthetic:v1", b"constructed bytes")
    grant = Grant(
        "synthetic:g",
        "synthetic:r",
        "synthetic:event",
        ("READ", "HASH", "PROBE"),
        (resource.resource_id,),
        "constructed only",
        "synthetic:runtime",
        0,
        10,
        3,
    )
    authority.issue("synthetic:issuer", grant)
    registry = sha(canonical(((resource.resource_id, resource_digest(resource)),)))
    broker = ConstructedResourceBroker(
        authority, resources=(resource,), expected_registry_digest=registry
    )
    kw = dict(
        actor=grant.actor,
        operation="READ",
        resource=resource.resource_id,
        context=grant.context,
        purpose=grant.purpose,
        now=1,
    )
    fence = authority.reserve(
        grant.grant_id, session="synthetic:s", initial_body=encode_payload({}), **kw
    )
    yield authority, broker, resource, fence, kw
    db.close()


def test_distinct_use_results_exact_binding_quota_and_receipt_retry(fixture):
    a, broker, resource, fence, kw = fixture
    for n, operation in enumerate(("READ", "HASH", "PROBE"), 1):
        payload, receipt = broker.use(
            "synthetic:s",
            "synthetic:t" + str(n),
            fence=fence,
            **(kw | {"operation": operation}),
            expected_resource_digest=resource_digest(resource),
        )
        expected = {
            "READ": resource.contents.hex(),
            "HASH": hashlib.sha256(resource.contents).hexdigest(),
            "PROBE": len(resource.contents),
        }[operation]
        assert payload["result"] == expected
        assert a.audit(expected_head=receipt.head, expected_count=n)
    assert (
        broker.use(
            "synthetic:s",
            "synthetic:t3",
            fence=fence,
            **(kw | {"operation": "PROBE"}),
            expected_resource_digest=resource_digest(resource),
        )[1]
        == receipt
    )
    with pytest.raises(ValueError, match="quota"):
        broker.use(
            "synthetic:s",
            "synthetic:t4",
            fence=fence,
            **kw,
            expected_resource_digest=resource_digest(resource),
        )


@pytest.mark.parametrize(
    "change",
    [
        {"operation": "MODEL"},
        {"operation": "CACHE"},
        {"operation": "EVALUATE"},
        {"purpose": "other"},
        {"now": 10},
        {"actor": "synthetic:alias"},
    ],
)
def test_missing_operation_or_current_scope_never_reaches_byte_use(fixture, change):
    a, broker, resource, fence, kw = fixture
    with pytest.raises(ValueError):
        broker.use(
            "synthetic:s",
            "synthetic:t",
            fence=fence,
            **(kw | change),
            expected_resource_digest=resource_digest(resource),
        )
    assert a.db.execute("SELECT uses FROM sessions").fetchone()[0] == 0
    assert a.audit(expected_head=None, expected_count=0)


def test_version_substitution_revocation_and_stale_owner_deny(fixture):
    a, broker, resource, fence, kw = fixture
    wrong = replace(resource, version_id="synthetic:v2")
    with pytest.raises(ValueError, match="version/content"):
        broker.use(
            "synthetic:s",
            "synthetic:t",
            fence=fence,
            **kw,
            expected_resource_digest=resource_digest(wrong),
        )
    fresh = a.recover("synthetic:s", **kw)
    with pytest.raises(ValueError, match="stale fence"):
        broker.use(
            "synthetic:s",
            "synthetic:t",
            fence=fence,
            **kw,
            expected_resource_digest=resource_digest(resource),
        )
    a.revoke("synthetic:issuer", "synthetic:g")
    with pytest.raises(ValueError):
        broker.use(
            "synthetic:s",
            "synthetic:t",
            fence=fresh,
            **kw,
            expected_resource_digest=resource_digest(resource),
        )
    assert a.audit(expected_head=None, expected_count=0)


def test_no_ambient_path_or_real_provenance_route(fixture):
    a, broker, resource, fence, kw = fixture
    with pytest.raises(ValueError):
        resource_digest("/unopened/raw.mov")
    with pytest.raises(ValueError):
        resource_digest(replace(resource, provenance="REAL_MEDIA"))
    with pytest.raises(ValueError, match="registry binding"):
        ConstructedResourceBroker(a, resources=(resource,), expected_registry_digest="0" * 64)


def test_failure_at_publication_keeps_bytes_unacknowledged_and_quota_unused(fixture):
    a, broker, resource, fence, kw = fixture
    a.db.execute(
        "CREATE TRIGGER fail BEFORE INSERT ON entries BEGIN SELECT RAISE(ABORT,'injected'); END"
    )
    with pytest.raises(sqlite3.IntegrityError):
        broker.use(
            "synthetic:s",
            "synthetic:t",
            fence=fence,
            **kw,
            expected_resource_digest=resource_digest(resource),
        )
    assert a.db.execute("SELECT uses FROM sessions").fetchone()[0] == 0
    assert a.db.execute("SELECT count(*) FROM tx").fetchone()[0] == 0


def test_read_does_not_implicitly_perform_hash_and_hash_needs_own_scope(fixture, monkeypatch):
    import json

    a, broker, resource, fence, kw = fixture
    expected = resource_digest(resource)
    body = json.loads(a.db.execute("SELECT body FROM grants").fetchone()[0])
    body["operations"] = ["READ"]  # trusted fixture authority narrows current scope
    a.db.execute("UPDATE grants SET body=?", (canonical(body),))
    original = hashlib.sha256

    def checked(payload=b""):
        if payload == resource.contents:
            raise AssertionError("READ must not hash the resource bytes")
        return original(payload)

    monkeypatch.setattr(hashlib, "sha256", checked)
    assert (
        broker.use(
            "synthetic:s", "synthetic:read", fence=fence, **kw, expected_resource_digest=expected
        )[0]["result"]
        == resource.contents.hex()
    )
    with pytest.raises(ValueError, match="scope/runtime"):
        broker.use(
            "synthetic:s",
            "synthetic:hash",
            fence=fence,
            **(kw | {"operation": "HASH"}),
            expected_resource_digest=expected,
        )


def test_retry_validates_acknowledged_body_not_only_request_binding(fixture):
    a, broker, resource, fence, kw = fixture
    expected = resource_digest(resource)
    broker.use("synthetic:s", "synthetic:t", fence=fence, **kw, expected_resource_digest=expected)
    a.db.execute(
        "UPDATE tx SET body=?",
        (encode_payload({"classification": PROFILE, "result": "substituted"}),),
    )
    with pytest.raises(ValueError, match="receipt/body"):
        broker.use(
            "synthetic:s", "synthetic:t", fence=fence, **kw, expected_resource_digest=expected
        )
