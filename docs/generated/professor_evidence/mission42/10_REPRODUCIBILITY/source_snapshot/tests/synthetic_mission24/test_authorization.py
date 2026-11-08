import json
import sqlite3
from dataclasses import replace

import pytest

from railway_detection.application.authorization import (
    FixtureOperation,
    ResourceUseRequest,
    TypedConstructedResourceBroker,
)
from railway_detection.application.contracts import EvidenceClass
from railway_detection.safety.constructed_authority import (
    PROFILE,
    ConstructedAuthority,
    Grant,
    canonical,
    encode_payload,
    sha,
)
from railway_detection.safety.constructed_broker import ConstructedResource, resource_digest


@pytest.fixture
def access():
    db = sqlite3.connect(":memory:")
    a = ConstructedAuthority(
        db,
        appointments=(("synthetic:issuer", ("ISSUER",)), ("synthetic:actor", ("REVIEWER",))),
        expected_context="synthetic:context",
        profile=PROFILE,
    )
    source = ConstructedResource("synthetic:frames", "synthetic:v1", b"CONSTRUCTED_INPUT_BYTES")
    digest = resource_digest(source)
    g = Grant(
        "synthetic:grant",
        "synthetic:actor",
        "synthetic:event",
        ("READ", "PROBE", "HASH"),
        (source.resource_id,),
        "CONSTRUCTED_REVIEW_FIXTURE",
        "synthetic:context",
        0,
        10,
        4,
    )
    a.issue("synthetic:issuer", g)
    request = ResourceUseRequest(
        "synthetic:session",
        "synthetic:read",
        1,
        g.actor,
        FixtureOperation.READ,
        source.resource_id,
        g.context,
        g.purpose,
        1,
        digest,
    )
    a.reserve(
        g.grant_id,
        session=request.session,
        actor=request.actor,
        operation="READ",
        resource=request.resource,
        context=request.context,
        purpose=request.purpose,
        now=request.now,
        initial_body=encode_payload({}),
    )
    service = TypedConstructedResourceBroker(
        a,
        resources=(source,),
        expected_registry_digest=sha(canonical(((source.resource_id, digest),))),
    )
    yield a, source, service, request
    db.close()


def test_exact_resource_access_retry_and_audit_history(access):
    a, source, service, request = access
    first = service.perform(request)
    assert service.perform(request) == first
    assert bytes.fromhex(json.loads(first.payload_json)["result"]) == source.contents
    assert len(service.events) == 1 and a.db.execute("SELECT uses FROM sessions").fetchone()[0] == 1
    receipt = json.loads(first.receipt_json)
    a.audit(expected_count=receipt["sequence"], expected_head=receipt["head"])
    with pytest.raises(ValueError):
        service.perform(replace(request, operation=FixtureOperation.HASH))


@pytest.mark.parametrize(
    "change",
    [
        {"actor": "synthetic:other"},
        {"resource": "synthetic:other"},
        {"context": "wrong"},
        {"purpose": "wrong"},
        {"now": 10},
        {"now": True},
        {"fence": 2},
        {"expected_resource_digest": "0" * 64},
        {"classification": EvidenceClass.EXTERNAL},
    ],
)
def test_scope_mismatch_never_returns_bytes_or_success(access, change):
    a, source, service, request = access
    with pytest.raises(ValueError):
        service.perform(replace(request, **change))
    assert not service.events and a.db.execute("SELECT count(*) FROM tx").fetchone()[0] == 0
    assert a.db.execute("SELECT uses FROM sessions").fetchone()[0] == 0


def test_revocation_clock_and_modified_registry_fail_closed(access):
    a, source, service, request = access
    service.perform(request)
    with pytest.raises(ValueError):
        service.perform(replace(request, transaction="synthetic:oldclock", now=0))
    with pytest.raises(ValueError, match="registry binding"):
        TypedConstructedResourceBroker(
            a,
            resources=(replace(source, contents=b"CHANGED"),),
            expected_registry_digest=sha(
                canonical(((source.resource_id, resource_digest(source)),))
            ),
        )
    a.revoke("synthetic:issuer", "synthetic:grant")
    with pytest.raises(ValueError):
        service.perform(request)
    assert a.db.execute("SELECT count(*) FROM tx").fetchone()[0] == 1
