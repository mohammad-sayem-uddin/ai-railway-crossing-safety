import sqlite3
from dataclasses import replace

import pytest

from railway_detection.annotation.human_review_domain import (
    BOUNDARIES,
    Observation,
    SyntheticReviewer,
)
from railway_detection.annotation.human_review_service import ConstructedReviewService, ReviewScope
from railway_detection.annotation.human_review_store import ConstructedReviewStore
from railway_detection.safety.constructed_authority import (
    PROFILE,
    ConstructedAuthority,
    Grant,
    encode_payload,
)

OBS = tuple(
    Observation(k, "front", "NOT_OBSERVABLE", "CONSTRUCTED_REVIEW_FIXTURE") for k in BOUNDARIES
)


def setup(connection, anchor=(0, None), existing=False):
    a = ConstructedAuthority(
        connection,
        appointments=(("synthetic:i", ("ISSUER",)), ("synthetic:r", ("REVIEWER",))),
        expected_context="synthetic:runtime",
        profile=PROFILE,
    )
    scope = ReviewScope(
        "synthetic:s",
        1,
        "synthetic:r",
        "synthetic:resource",
        "synthetic:runtime",
        "CONSTRUCTED_REVIEW_FIXTURE",
        1,
    )
    if not existing:
        a.issue(
            "synthetic:i",
            Grant(
                "synthetic:g",
                scope.actor,
                "synthetic:event",
                ("REVIEW",),
                (scope.resource,),
                scope.purpose,
                scope.context,
                0,
                10,
                5,
            ),
        )
        a.reserve(
            "synthetic:g", session=scope.session, initial_body=encode_payload({}), **scope.current()
        )
    s = ConstructedReviewStore(
        connection,
        reviewers=(SyntheticReviewer(scope.actor, ("REVIEWER",)),),
        events=("synthetic:event",),
        expected_anchor=anchor,
    )
    return a, s, ConstructedReviewService(a, s), scope


def test_atomic_result_retry_and_wrong_purpose():
    db = sqlite3.connect(":memory:")
    a, s, service, scope = setup(db)
    result = service.execute(
        scope, "SEAL", "synthetic:event", request_id="synthetic:r1", observations=OBS
    )
    assert (
        result["classification"] == "CONSTRUCTED_REVIEW_FIXTURE"
        and not result["real_human_evidence"]
    )
    assert (
        service.execute(
            scope, "SEAL", "synthetic:event", request_id="synthetic:r1", observations=OBS
        )
        == result
    )
    assert db.execute("SELECT uses FROM sessions").fetchone()[0] == 1
    with pytest.raises(ValueError):
        service.execute(
            replace(scope, purpose="other"),
            "SEAL",
            "synthetic:event",
            request_id="synthetic:r2",
            observations=OBS,
        )
    assert s.anchor[0] == 1
    a.audit(expected_head=result["authority_receipt"]["head"], expected_count=1)
    db.close()


@pytest.mark.parametrize(
    "change",
    [
        {"actor": "synthetic:bad"},
        {"resource": "synthetic:other"},
        {"purpose": "wrong"},
        {"context": "wrong"},
        {"now": 10},
        {"now": None},
        {"fence": 2},
        {"classification": "GENUINE_HUMAN_REVIEW"},
    ],
)
def test_unauthorized_review_never_writes(change):
    db = sqlite3.connect(":memory:")
    a, s, service, scope = setup(db)
    with pytest.raises(ValueError):
        service.execute(
            replace(scope, **change),
            "SEAL",
            "synthetic:event",
            request_id="synthetic:r1",
            observations=OBS,
        )
    assert (
        s.anchor == (0, None)
        and db.execute("SELECT count(*) FROM constructed_review_log").fetchone()[0] == 0
    )
    db.close()


def test_revocation_and_atomic_rollback():
    db = sqlite3.connect(":memory:")
    a, s, service, scope = setup(db)
    db.execute(
        "CREATE TRIGGER fail BEFORE INSERT ON entries BEGIN SELECT RAISE(ABORT,'injected'); END"
    )
    with pytest.raises(sqlite3.IntegrityError):
        service.execute(
            scope, "SEAL", "synthetic:event", request_id="synthetic:r1", observations=OBS
        )
    assert (
        s.anchor == (0, None)
        and db.execute("SELECT count(*) FROM constructed_review_log").fetchone()[0] == 0
    )
    db.execute("DROP TRIGGER fail")
    a.revoke("synthetic:i", "synthetic:g")
    with pytest.raises(ValueError):
        service.execute(
            scope, "SEAL", "synthetic:event", request_id="synthetic:r1", observations=OBS
        )
    db.close()


def test_use_checks_persisted_context_and_schema():
    for sql in [
        "UPDATE constructed_review_context SET body='{}'",
        "UPDATE constructed_review_service SET version='CONSTRUCTED_REVIEW_FIXTURE/0'",
    ]:
        db = sqlite3.connect(":memory:")
        a, s, service, scope = setup(db)
        db.execute(sql)
        with pytest.raises(ValueError):
            service.execute(
                scope, "SEAL", "synthetic:event", request_id="synthetic:r1", observations=OBS
            )
        assert db.execute("SELECT count(*) FROM tx").fetchone()[0] == 0
        db.close()


def test_lost_response_recovery_bound_to_previous_anchor(tmp_path):
    path = tmp_path / "fixture.sqlite"
    db = sqlite3.connect(path)
    a, s, service, scope = setup(db)
    service.execute(scope, "SEAL", "synthetic:event", request_id="synthetic:r1", observations=OBS)
    db.close()
    db = sqlite3.connect(path)
    a = ConstructedAuthority(
        db,
        appointments=(("synthetic:i", ("ISSUER",)), ("synthetic:r", ("REVIEWER",))),
        expected_context=scope.context,
        profile=PROFILE,
    )
    fresh = a.recover(scope.session, **scope.current())
    scope = replace(scope, fence=fresh)
    anchor = ConstructedReviewService.recover_anchor(
        a,
        scope,
        request_id="synthetic:r1",
        operation="SEAL",
        event="synthetic:event",
        args={"observations": OBS},
        previous_anchor=(0, None),
    )
    a, s, service, scope2 = setup(db, anchor, existing=True)
    scope2 = replace(scope2, fence=fresh)
    assert (
        service.execute(
            scope2, "SEAL", "synthetic:event", request_id="synthetic:r1", observations=OBS
        )["review_commit"]["count"]
        == 1
    )
    db.close()
