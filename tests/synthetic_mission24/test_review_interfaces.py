import sqlite3
from dataclasses import replace

import pytest

from railway_detection.annotation.human_review_domain import (
    BOUNDARIES,
    RISK_SUBJECTS,
    Observation,
    SyntheticReviewer,
)
from railway_detection.annotation.human_review_service import ReviewScope
from railway_detection.annotation.human_review_store import ConstructedReviewStore
from railway_detection.application.contracts import EvidenceClass
from railway_detection.application.review import (
    ReviewOperation,
    ReviewRequest,
    TypedConstructedReviewService,
)
from railway_detection.safety.constructed_authority import (
    PROFILE,
    ConstructedAuthority,
    Grant,
    encode_payload,
)

EVENT = "synthetic:m24:event"
OBSERVATIONS = tuple(
    Observation(k, "back", "NOT_OBSERVABLE", "CONSTRUCTED_REVIEW_FIXTURE: no human viewing")
    for k in BOUNDARIES
)


@pytest.fixture
def service():
    db = sqlite3.connect(":memory:")
    appointments = (
        ("synthetic:issuer", ("ISSUER",)),
        ("synthetic:first", ("REVIEWER",)),
        ("synthetic:second", ("REVIEWER",)),
        ("synthetic:adjudicator", ("ADJUDICATOR",)),
    )
    authority = ConstructedAuthority(
        db,
        appointments=tuple(
            (actor, ("REVIEWER",) if roles == ("ADJUDICATOR",) else roles)
            for actor, roles in appointments
        ),
        expected_context="synthetic:context",
        profile=PROFILE,
    )
    scopes = {}
    for actor, _role in appointments[1:]:
        scope = ReviewScope(
            "synthetic:session:" + actor,
            1,
            actor,
            "synthetic:observations",
            "synthetic:context",
            "CONSTRUCTED_REVIEW_FIXTURE",
            1,
        )
        grant = Grant(
            "synthetic:grant:" + actor,
            actor,
            EVENT,
            ("REVIEW",),
            (scope.resource,),
            scope.purpose,
            scope.context,
            0,
            10,
            24,
        )
        authority.issue("synthetic:issuer", grant)
        authority.reserve(
            grant.grant_id,
            session=scope.session,
            initial_body=encode_payload({}),
            **scope.current(),
        )
        scopes[actor] = scope
    store = ConstructedReviewStore(
        db,
        reviewers=tuple(SyntheticReviewer(a, r) for a, r in appointments[1:]),
        events=(EVENT,),
        expected_anchor=(0, None),
    )
    yield authority, store, TypedConstructedReviewService(authority, store), scopes
    db.close()


def seal(service, actor="synthetic:first", request_id="synthetic:seal:first"):
    _, _, facade, scopes = service
    return facade.execute(
        scopes[actor], "SEAL", EVENT, request_id=request_id, observations=OBSERVATIONS
    )


def test_typed_closed_requests_immutable_history_and_genuine_boundary(service):
    authority, store, facade, scopes = service
    first = seal(service)
    assert first == seal(service)
    assert store.anchor[0] == 1 and len(facade.events) == 1
    assert facade.readiness(scopes["synthetic:first"], EVENT).genuine_complete is False
    with pytest.raises(PermissionError):
        facade.require_genuine_complete_record(first)
    with pytest.raises(ValueError):
        facade.perform(
            ReviewRequest(
                scopes["synthetic:first"],
                ReviewOperation.SEAL,
                EVENT,
                "synthetic:extra",
                '{"observations":[],"approved":true}',
            )
        )
    with pytest.raises(ValueError):
        facade.perform(
            ReviewRequest(
                scopes["synthetic:first"],
                ReviewOperation.SEAL,
                EVENT,
                "synthetic:external",
                "{}",
                EvidenceClass.PENDING,
            )
        )
    assert store.anchor[0] == 1
    authority.audit(expected_count=1, expected_head=first["authority_receipt"]["head"])


@pytest.mark.parametrize(
    "change",
    [
        {"actor": "synthetic:other"},
        {"resource": "synthetic:other"},
        {"purpose": "other"},
        {"context": "other"},
        {"now": 10},
        {"fence": 2},
        {"classification": "GENUINE_EVIDENCE_PENDING"},
    ],
)
def test_current_scope_refuses_before_history_or_quota_write(service, change):
    a, store, facade, scopes = service
    with pytest.raises(ValueError):
        facade.execute(
            replace(scopes["synthetic:first"], **change),
            "SEAL",
            EVENT,
            request_id="synthetic:bad",
            observations=OBSERVATIONS,
        )
    assert store.anchor == (0, None) and a.db.execute("SELECT count(*) FROM tx").fetchone()[0] == 0


def test_revocation_blocks_even_readiness_and_duplicate_requests(service):
    a, store, facade, scopes = service
    seal(service)
    a.revoke("synthetic:issuer", "synthetic:grant:synthetic:first")
    with pytest.raises(ValueError):
        facade.readiness(scopes["synthetic:first"], EVENT)
    with pytest.raises(ValueError):
        seal(service)
    assert store.anchor[0] == 1


def test_required_independent_second_review_and_unresolved_disagreement(service):
    a, store, facade, scopes = service
    seal(service)
    risks = tuple((k, k == "EXPLICIT_REVIEWER_FLAG") for k in RISK_SUBJECTS)
    with pytest.raises(ValueError, match="independent seals"):
        facade.execute(
            scopes["synthetic:first"],
            "COMPARE",
            EVENT,
            request_id="synthetic:compare",
            risk_inputs=risks,
        )
    seal(service, "synthetic:second", "synthetic:seal:second")
    facade.execute(
        scopes["synthetic:first"],
        "COMPARE",
        EVENT,
        request_id="synthetic:compare",
        risk_inputs=risks,
    )
    before = store._restore()._seals["synthetic:first", EVENT]
    facade.execute(
        scopes["synthetic:first"],
        "CORRECT",
        EVENT,
        request_id="synthetic:correction",
        observations=OBSERVATIONS,
        reason="CONSTRUCTED informed correction",
    )
    assert store._restore()._seals["synthetic:first", EVENT] == before
    sources = tuple(sorted(s.digest for s in store._restore()._seals.values()))
    facade.execute(
        scopes["synthetic:adjudicator"],
        "ADJUDICATE",
        EVENT,
        request_id="synthetic:uncertain",
        source_digests=sources,
        state="UNCERTAIN",
        rationale="CONSTRUCTED unresolved fixture dispute",
    )
    history = store._restore().history
    assert history[-1][-2] == "UNCERTAIN"
    with pytest.raises(ValueError):
        facade.execute(
            scopes["synthetic:adjudicator"],
            "ADJUDICATE",
            EVENT,
            request_id="synthetic:invented",
            source_digests=sources,
            state="OBSERVABLE",
            rationale="not actual human evidence",
        )


def test_readiness_refuses_stale_schema_and_wrong_domain_role(service):
    a, store, facade, scopes = service
    # Authority access alone is insufficient: adjudicator is not a domain reviewer.
    with pytest.raises(ValueError, match="role"):
        facade.execute(
            scopes["synthetic:adjudicator"],
            "SEAL",
            EVENT,
            request_id="synthetic:bad-role",
            observations=OBSERVATIONS,
        )
    assert store.anchor == (0, None)
    a.db.execute("UPDATE constructed_review_service SET version='CONSTRUCTED_REVIEW_FIXTURE/0'")
    with pytest.raises(ValueError, match="schema"):
        facade.readiness(scopes["synthetic:first"], EVENT)
