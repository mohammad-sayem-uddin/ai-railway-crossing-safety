"""Constructed readiness predicates, never genuine rights, grants or execution."""

from dataclasses import replace

import pytest

from railway_detection.annotation.evidence_review.contracts import canonical, digest
from railway_detection.application.preflight.engine import (
    DOCUMENTARY,
    FIXTURE,
    KINDS,
    Claim,
    ExternalReceipt,
    PreflightEngine,
    Request,
    State,
)


def fixture():
    decisions = tuple(
        (f"M19-PERM-{i:02}", "B" if i in (12, 13, 16, 18, 24, 25) else "A") for i in range(1, 28)
    )
    purposes = tuple((op, "synthetic:purpose:" + op) for op, _ in decisions)
    resources = (
        ("synthetic:resource:0", digest({"source": 0})),
        ("synthetic:resource:1", digest({"source": 1})),
    )
    engine = PreflightEngine(
        catalog_digest=digest({"catalog": "constructed"}),
        decisions=decisions,
        resources=resources,
        purposes=purposes,
        parents=tuple((resource, ("synthetic:parent:0",)) for resource, _ in resources),
    )
    request = Request(
        "synthetic:request:0",
        "M19-PERM-19",
        resources[0][0],
        resources[0][1],
        "synthetic:actor:0",
        "synthetic:qualified_operator",
        dict(purposes)["M19-PERM-19"],
        "synthetic:offline_runtime",
        "synthetic:protocol:v1",
        "synthetic:schema:v1",
        "synthetic:create_only_output",
        "synthetic:audit_log",
        ("synthetic:parent:0",),
        classification=FIXTURE,
    )
    return engine, request, claims(request)


def claims(q):
    facts = {
        "SOURCE_IDENTITY": {"resource_id": q.resource_id, "identity": q.resource_identity},
        "RESOURCE_RIGHTS": {
            "owner_or_license_reference": "synthetic:owner_or_license",
            "operation": q.operation,
            "conflicting_license_records": [],
        },
        "ACTOR_IDENTITY": {"actor": q.actor},
        "ROLE": {"role": q.role},
        "PURPOSE": {"purpose": q.purpose},
        "ENVIRONMENT": {"environment": q.environment},
        "PROTOCOL": {"protocol": q.protocol},
        "DATA_SCHEMA": {
            "schema": q.data_schema,
            "duration_compatibility": "CANONICAL_SCHEMA_TIMING_COMPATIBLE",
        },
        "PROVENANCE": {"parents": list(q.provenance_parents)},
        "LOGGING": {"audit_log": q.audit_log},
        "OUTPUT": {"destination": q.output_destination},
        "TECHNICAL": {
            "prerequisites_complete": True,
            "external_applicability": "NOT_APPLICABLE_WITH_EVIDENCE",
        },
        "HUMAN": {
            "qualified": True,
            "independent": True,
            "conflicts_resolved": True,
            "batch_complete": True,
            "review_parents_complete": True,
            "classification": FIXTURE,
        },
    }
    facts.update(
        {
            k: {"operation": q.operation, "resource_identity": q.resource_identity, "current": True}
            for k in ("PERMISSION_BASIS", "VALIDITY", "REVOCATION")
        }
    )
    return tuple(
        Claim(k, "synthetic:evidence:" + k, digest(q), 0, 100, False, canonical(facts[k]), FIXTURE)
        for k in KINDS
    )


def mutate(cs, kind, change):
    from railway_detection.application.contracts import closed_json

    return tuple(
        replace(c, facts_json=canonical(closed_json(c.facts_json) | change))
        if c.kind == kind
        else c
        for c in cs
    )


def test_constructed_complete_preflight_only_prepares_authorization_review():
    e, q, cs = fixture()
    assert e.initial_state() == State.NOT_STARTED
    ready = e.check(q, cs, now=10)
    assert ready.state == State.READY and not ready.execution_permitted and not ready.grant_issued
    assert e.submit_authorization_review(q, ready, cs, now=10) == State.PENDING
    assert e.submit_authorization_review(q, ready, cs, now=10) == State.PENDING
    with pytest.raises(PermissionError, match="no executor"):
        e.require_execution()
    assert not e._authorizations and not e._executions


@pytest.mark.parametrize("kind", KINDS)
def test_each_missing_mandatory_evidence_kind_blocks_before_authorization(kind):
    e, q, cs = fixture()
    cs = tuple(c for c in cs if c.kind != kind)
    result = e.check(q, cs, now=10)
    assert result.state == State.BLOCKED and any(i.boundary == kind for i in result.issues)
    with pytest.raises(PermissionError):
        e.submit_authorization_review(q, result, cs, now=10)
    assert not e._requests


@pytest.mark.parametrize(
    "field,value",
    [
        ("resource_identity", "0" * 64),
        ("resource_id", "synthetic:unknown"),
        ("actor", "synthetic:wrong_actor"),
        ("role", "wrong_role"),
        ("purpose", "wrong_purpose"),
        ("environment", "wrong_runtime"),
        ("protocol", None),
        ("data_schema", None),
        ("provenance_parents", ()),
        ("audit_log", None),
        ("output_destination", None),
        ("acoustic_shift_us", 1),
        ("boundaries", ("T2",)),
    ],
)
def test_wrong_or_missing_exact_request_binding_refuses(field, value):
    e, q, cs = fixture()
    q = replace(q, **{field: value})
    result = e.check(q, cs, now=10)
    assert result.state == State.BLOCKED and not result.execution_permitted


@pytest.mark.parametrize(
    "kind,change,boundary",
    [
        ("RESOURCE_RIGHTS", {"owner_or_license_reference": None}, "RESOURCE_RIGHTS"),
        ("RESOURCE_RIGHTS", {"conflicting_license_records": ["A", "B"]}, "RESOURCE_RIGHTS"),
        ("RESOURCE_RIGHTS", {"conflicting_license_records": None}, "RESOURCE_RIGHTS"),
        ("TECHNICAL", {"external_applicability": "APPLICABLE_PENDING_EVIDENCE"}, "EXTERNAL"),
        ("TECHNICAL", {"external_applicability": "UNKNOWN_REQUIRES_VERIFICATION"}, "EXTERNAL"),
        ("TECHNICAL", {"prerequisites_complete": False}, "TECHNICAL"),
        ("HUMAN", {"qualified": False}, "HUMAN"),
        ("HUMAN", {"independent": False}, "HUMAN"),
        ("HUMAN", {"conflicts_resolved": False}, "HUMAN"),
        ("HUMAN", {"batch_complete": False}, "HUMAN"),
        (
            "DATA_SCHEMA",
            {"duration_compatibility": "INCOMPATIBLE_DURATION_SCHEMA"},
            "DURATION_SCHEMA",
        ),
        ("PROVENANCE", {"parents": ["synthetic:missing_parent"]}, "PROVENANCE"),
        ("OUTPUT", {"destination": "unapproved_destination"}, "OUTPUT"),
        ("LOGGING", {"audit_log": None}, "LOGGING"),
    ],
)
def test_unknown_owner_conflicting_license_human_schema_provenance_and_output_boundaries(
    kind, change, boundary
):
    e, q, cs = fixture()
    if "batch_complete" in change:
        q = replace(q, operation="M19-PERM-21", purpose=dict(e.purposes)["M19-PERM-21"])
        cs = claims(q)
    cs = mutate(cs, kind, change)
    result = e.check(q, cs, now=10)
    assert result.state == State.BLOCKED and any(i.boundary == boundary for i in result.issues)
    assert not result.execution_permitted


@pytest.mark.parametrize(
    "fault", ["expired", "revoked", "future", "wrong_binding", "false_genuine", "bool_clock"]
)
def test_current_claim_scope_time_and_classification_cannot_be_bypassed(fault):
    e, q, cs = fixture()
    c = cs[0]
    values = {
        "expired": {"expires": 10},
        "revoked": {"revoked": True},
        "future": {"valid_from": 11},
        "wrong_binding": {"request_digest": "0" * 64},
        "false_genuine": {"classification": DOCUMENTARY},
        "bool_clock": {"expires": True},
    }
    cs = (replace(c, **values[fault]),) + cs[1:]
    assert e.check(q, cs, now=10).state == State.BLOCKED


@pytest.mark.parametrize(
    "landmark", [None, "LENS_PLANE", "LEGACY_LENS_PLANE", "PHYSICAL_ROADWAY_ENTRY"]
)
def test_t2_and_occupancy_alias_require_actual_landmark_evidence(landmark):
    e, q, _ = fixture()
    q = replace(q, boundaries=("T2", "T_OCC_START"), landmark_kind=landmark)
    cs = claims(q)
    result = e.check(q, cs, now=10)
    assert result.state == State.BLOCKED and any(i.boundary == "LANDMARK" for i in result.issues)


@pytest.mark.parametrize("operation", [12, 13, 16, 18, 24, 25])
def test_every_denied_operation_stays_denied_even_with_complete_checklists(operation):
    e, q, _ = fixture()
    q = replace(q, operation=f"M19-PERM-{operation:02}")
    assert e.check(q, claims(q), now=10).state == State.PROHIBITED


def test_coherently_rebound_wrong_resource_still_refuses_independent_catalog_identity():
    e, q, _ = fixture()
    q = replace(q, resource_identity="0" * 64)
    result = e.check(q, claims(q), now=10)
    assert any(i.classification == "MISSING_RESOURCE_IDENTITY" for i in result.issues)


def test_stale_or_modified_readiness_and_duplicate_request_substitution_refuse():
    e, q, cs = fixture()
    ready = e.check(q, cs, now=10)
    for bad in (
        replace(ready, catalog_digest="0" * 64),
        replace(ready, request_digest="0" * 64),
        replace(ready, evaluated_at=9),
    ):
        with pytest.raises(PermissionError):
            e.submit_authorization_review(q, bad, cs, now=10)
    e.submit_authorization_review(q, ready, cs, now=10)
    other = replace(
        q,
        resource_id="synthetic:resource:1",
        resource_identity=dict(e.resources)["synthetic:resource:1"],
    )
    other_claims = claims(other)
    other_ready = e.check(other, other_claims, now=10)
    assert other_ready.state == State.READY
    with pytest.raises(ValueError, match="duplicate"):
        e.submit_authorization_review(other, other_ready, other_claims, now=10)


def test_constructed_review_and_receipts_cannot_be_upgraded_or_certify_execution():
    e, q, cs = fixture()
    ready = e.check(q, cs, now=10)
    e.submit_authorization_review(q, ready, cs, now=10)
    receipt = ExternalReceipt(
        "synthetic:receipt",
        digest(q),
        e.catalog_digest,
        None,
        0,
        100,
        False,
        "synthetic:canonical_ref",
        "synthetic:external_ref",
        FIXTURE,
    )
    for _ in range(2):
        with pytest.raises(PermissionError):
            e.record_authorization(q, ready, cs, receipt, now=10)
        with pytest.raises(PermissionError):
            e.record_execution(q, receipt, now=10)
    assert not e._authorizations and not e._executions
    with pytest.raises(ValueError, match="constructed"):
        e.check(replace(q, classification=DOCUMENTARY), cs, now=10)


def test_duplicate_evidence_and_global_approval_flags_do_not_create_authority():
    e, q, cs = fixture()
    assert e.check(q, cs + (cs[0],), now=10).state == State.BLOCKED
    forged = replace(cs[0], facts_json=canonical({"approved": True}))
    assert e.check(q, (forged,) + cs[1:], now=10).state == State.BLOCKED
    assert not e._authorizations


@pytest.mark.parametrize("fault", ["expired_permission", "revoked_permission"])
def test_expired_or_revoked_operation_permission_evidence_refuses(fault):
    e, q, cs = fixture()
    cs = tuple(
        replace(c, expires=10)
        if c.kind == "PERMISSION_BASIS" and fault == "expired_permission"
        else replace(c, revoked=True)
        if c.kind == "PERMISSION_BASIS"
        else c
        for c in cs
    )
    result = e.check(q, cs, now=10)
    assert result.state == State.BLOCKED and any(
        i.boundary == "PERMISSION_BASIS" for i in result.issues
    )
    assert not e._authorizations


def test_coherently_rebound_missing_parent_still_refuses_retained_provenance_registry():
    e, q, _ = fixture()
    q = replace(q, provenance_parents=("synthetic:missing_parent",))
    result = e.check(q, claims(q), now=10)
    assert result.state == State.BLOCKED and any(i.boundary == "PROVENANCE" for i in result.issues)


@pytest.mark.parametrize("operation", [19, 26])
def test_first_review_and_pilot_do_not_require_future_gt_completion_or_a_scientific_floor(
    operation,
):
    e, q, _ = fixture()
    op = f"M19-PERM-{operation:02}"
    q = replace(q, operation=op, purpose=dict(e.purposes)[op])
    cs = claims(q)
    cs = mutate(cs, "HUMAN", {"batch_complete": False})
    cs = mutate(cs, "DATA_SCHEMA", {"duration_compatibility": "NOT_APPLICABLE_NO_REVIEW_RECORD"})
    ready = e.check(q, cs, now=10)
    assert ready.state == State.READY and not ready.execution_permitted
    assert e.submit_authorization_review(q, ready, cs, now=10) == State.PENDING
    assert not e._authorizations and not e._executions


def test_adjudication_preflight_requires_existing_independent_parent_reviews():
    e, q, _ = fixture()
    q = replace(q, operation="M19-PERM-20", purpose=dict(e.purposes)["M19-PERM-20"])
    cs = mutate(claims(q), "HUMAN", {"review_parents_complete": False})
    assert e.check(q, cs, now=10).state == State.BLOCKED
