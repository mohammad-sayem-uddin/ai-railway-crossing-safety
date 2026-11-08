"""Injected temporary SQLite fixtures only; no real player or human records."""

import sqlite3
from dataclasses import replace

import pytest

from railway_detection.annotation.human_review_domain import (
    BOUNDARIES,
    RISK_SUBJECTS,
    Observation,
    SyntheticReviewer,
)
from railway_detection.annotation.human_review_store import ConstructedReviewStore

ROSTER = (
    SyntheticReviewer("synthetic:a", ("REVIEWER",)),
    SyntheticReviewer("synthetic:b", ("REVIEWER",)),
)
OBS = tuple(Observation(k, "front", "NOT_OBSERVABLE", "constructed unknown") for k in BOUNDARIES)
RISKS = tuple((k, False) for k in RISK_SUBJECTS)


@pytest.fixture(scope="module")
def constructed_root(tmp_path_factory):
    # Allocate the explicit test-store directory before function IO tripwires.
    return tmp_path_factory.mktemp("constructed_review_store")


@pytest.fixture
def sqlite_path(constructed_root, request):
    return constructed_root / (request.node.name + ".sqlite")


def store(path, anchor=(0, None), **overrides):
    config = dict(
        reviewers=ROSTER,
        events=("synthetic:event",),
        principal_aliases=(("synthetic:person-alias", "synthetic:a"),),
        event_aliases=(("synthetic:event-alias", "synthetic:event"),),
        expected_anchor=anchor,
    )
    return ConstructedReviewStore(sqlite3.connect(path), **(config | overrides))


def test_exit_restart_alias_and_assignment_cannot_reset_blindness(sqlite_path):
    path = sqlite_path
    w = store(path)
    first = w.execute(
        "SEAL", "synthetic:a", "synthetic:event", request_id="synthetic:r1", observations=OBS
    )
    w.execute(
        "COMPARE", "synthetic:a", "synthetic:event", request_id="synthetic:r2", risk_inputs=RISKS
    )
    anchor = w.anchor
    w.db.close()
    w = store(path, anchor)
    for event in ("synthetic:event", "synthetic:event-alias"):
        with pytest.raises(ValueError, match="seal consumed"):
            w.execute(
                "SEAL",
                "synthetic:person-alias",
                event,
                request_id="synthetic:fresh",
                observations=OBS,
            )
    correction = w.execute(
        "CORRECT",
        "synthetic:a",
        "synthetic:event",
        request_id="synthetic:correction",
        observations=OBS,
        reason="informed fixture correction",
    )
    assert correction.count == 3
    current = w.anchor
    assert (
        w.execute(
            "SEAL", "synthetic:a", "synthetic:event", request_id="synthetic:r1", observations=OBS
        )
        == first
    )
    assert w.anchor == current
    rows = w.db.execute("SELECT body FROM constructed_review_log ORDER BY seq").fetchall()
    assert len(rows) == 3 and "SEAL" in rows[0][0] and "CORRECT" in rows[2][0]
    with pytest.raises(ValueError, match="substitution"):
        w.execute(
            "SEAL",
            "synthetic:a",
            "synthetic:event",
            request_id="synthetic:r1",
            observations=(replace(OBS[0], rationale="changed"),) + OBS[1:],
        )
    w.db.close()


def test_stale_restart_anchor_and_mutated_history_deny(sqlite_path):
    path = sqlite_path
    w = store(path)
    w.execute("SEAL", "synthetic:a", "synthetic:event", request_id="synthetic:r1", observations=OBS)
    anchor = w.anchor
    with pytest.raises(ValueError, match="anchor"):
        store(path)
    w.db.execute("DELETE FROM constructed_review_log")
    w.db.close()
    with pytest.raises(ValueError, match="anchor"):
        store(path, anchor)


def test_two_sessions_cannot_advance_from_stale_knowledge(sqlite_path):
    path = sqlite_path
    a = store(path)
    b = store(path)
    a.execute("SEAL", "synthetic:a", "synthetic:event", request_id="synthetic:r1", observations=OBS)
    with pytest.raises(ValueError, match="anchor"):
        b.execute(
            "SEAL", "synthetic:a", "synthetic:event", request_id="synthetic:r2", observations=OBS
        )
    a.db.close()
    b.db.close()


def test_registry_role_substitution_and_unmapped_event_deny(sqlite_path):
    path = sqlite_path
    w = store(path)
    with pytest.raises(ValueError, match="context substitution"):
        store(path, events=("synthetic:other",), event_aliases=())
    with pytest.raises(ValueError, match="unknown event"):
        w.execute(
            "SEAL", "synthetic:a", "synthetic:unknown", request_id="synthetic:r1", observations=OBS
        )
    assert w.anchor == (0, None)
    w.db.close()


def test_commit_failure_leaves_no_seal_or_consumption(sqlite_path):
    path = sqlite_path
    w = store(path)
    w.db.execute(
        "CREATE TRIGGER fail BEFORE INSERT ON constructed_review_log "
        "BEGIN SELECT RAISE(ABORT,'injected'); END"
    )
    with pytest.raises(sqlite3.IntegrityError, match="injected"):
        w.execute(
            "SEAL", "synthetic:a", "synthetic:event", request_id="synthetic:r1", observations=OBS
        )
    assert w.anchor == (0, None)
    w.db.execute("DROP TRIGGER fail")
    assert (
        w.execute(
            "SEAL", "synthetic:a", "synthetic:event", request_id="synthetic:r1", observations=OBS
        ).count
        == 1
    )
    w.db.close()


@pytest.mark.parametrize("anchor", [(True, "a" * 64), (1.0, "a" * 64), (0, "a" * 64), (1, None)])
def test_anchor_types_cannot_launder_sequence(sqlite_path, anchor):
    with pytest.raises(ValueError, match="typed independent"):
        store(sqlite_path, anchor)


def test_corrupt_result_and_missing_context_refuse_without_reset(sqlite_path):
    w = store(sqlite_path)
    w.execute("SEAL", "synthetic:a", "synthetic:event", request_id="synthetic:r1", observations=OBS)
    anchor = w.anchor
    w.db.execute("UPDATE constructed_review_log SET result_digest=?", ("0" * 64,))
    with pytest.raises(ValueError, match="result substitution"):
        store(sqlite_path, anchor)
    w.db.execute("DELETE FROM constructed_review_context")
    w.db.close()
    with pytest.raises(ValueError, match="missing review context"):
        store(sqlite_path, anchor)
