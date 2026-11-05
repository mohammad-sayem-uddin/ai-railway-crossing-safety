"""Expected refusals assert no assignment, source mutation or genuine upgrade."""

from dataclasses import replace

import pytest

from railway_detection.annotation.evidence_review.contracts import (
    CANDIDATE,
    CANDIDATE_EVENTS,
    R04_EVENTS,
    BoundaryObservation,
    ReviewerStatus,
    digest,
)
from railway_detection.annotation.evidence_review.integration import fixture_contracts
from railway_detection.annotation.evidence_review.lifecycle import Assignment, ReviewLifecycle
from railway_detection.annotation.human_review_domain import Observation

CODE = "4" * 40


@pytest.fixture
def contracts():
    return fixture_contracts(CODE)


def assignment(batch, reviewer, permission, role="REVIEWER"):
    return Assignment(
        "synthetic:assignment:test",
        digest(batch),
        batch.events[0][0],
        reviewer.reviewer_id,
        role,
        tuple(s.source_id for s in batch.sources),
        permission.reference,
    )


def point(batch, reviewer, boundary="T1"):
    return BoundaryObservation(
        "synthetic:observation:test",
        reviewer.reviewer_id,
        batch.sources[0].source_id,
        batch.boundary_version,
        Observation(
            boundary,
            "front",
            "OBSERVABLE",
            "constructed test",
            1_000_000,
            pts_ticks=1_000_000,
            timebase=(1, 1_000_000),
        ),
    )


@pytest.mark.parametrize(
    "fault",
    [
        "qualification",
        "expired",
        "not_yet_valid",
        "role",
        "event",
        "conflict",
        "independence",
        "consent",
        "verified_mock_upgrade",
        "unverified",
        "pending",
        "string_status",
    ],
)
def test_reviewer_assignment_refuses_missing_expired_conflicted_or_upgraded_evidence(
    contracts, fault
):
    _, batch, roster, permissions = contracts
    r = roster[0]
    if fault == "qualification":
        r = replace(r, qualification=None)
    elif fault in ("expired", "not_yet_valid", "role", "event"):
        change = {
            "expired": {"expires": 10},
            "not_yet_valid": {"valid_from": 11},
            "role": {"roles": ("ADJUDICATOR",)},
            "event": {"events": ("synthetic:other",)},
        }[fault]
        r = replace(r, qualification=replace(r.qualification, **change))
    elif fault == "conflict":
        r = replace(r, conflicts=(batch.events[0][0],))
    elif fault == "independence":
        r = replace(r, independence_reference=None)
    elif fault == "consent":
        r = replace(r, consent_reference=None)
    else:
        r = replace(
            r,
            status={
                "verified_mock_upgrade": ReviewerStatus.VERIFIED,
                "unverified": ReviewerStatus.UNVERIFIED,
                "pending": ReviewerStatus.PENDING,
                "string_status": "MOCK_REVIEWER_FIXTURE",
            }[fault],
        )
    engine = ReviewLifecycle(batch, (r,) + roster[1:])
    with pytest.raises((ValueError, PermissionError)):
        engine.assign(assignment(batch, r, permissions[0]), permissions[0], now=10)
    assert engine.history == ()
    assert engine.assignments == ()


@pytest.mark.parametrize("status", list(ReviewerStatus))
def test_genuine_reviewer_cannot_be_verified_by_status_or_reference_only(contracts, status):
    _, batch, roster, _ = contracts
    r = replace(roster[0], status=status, identity_evidence="unverified-reference")
    with pytest.raises(PermissionError):
        r.principal(event=batch.events[0][0], role="REVIEWER", now=10, fixture=False, verifier=None)


@pytest.mark.parametrize(
    "fault", ["actor", "batch", "event", "operation", "expiry", "future", "revoked", "bool_clock"]
)
def test_current_permission_refuses_scope_expiry_revocation_or_invalid_clock(contracts, fault):
    _, batch, roster, permissions = contracts
    changes = {
        "actor": {"actor": roster[1].reviewer_id},
        "batch": {"batch_digest": "0" * 64},
        "event": {"events": ("synthetic:other",)},
        "operation": {"operations": ("SUBMIT",)},
        "expiry": {"expires": 10},
        "future": {"valid_from": 11},
        "revoked": {"revoked": True},
        "bool_clock": {"expires": True},
    }
    p = replace(permissions[0], **changes[fault])
    with pytest.raises((ValueError, PermissionError)):
        ReviewLifecycle(batch, roster).assign(assignment(batch, roster[0], p), p, now=10)


@pytest.mark.parametrize(
    "fault",
    [
        "duplicate_event",
        "source_missing",
        "source_event",
        "source_manifest",
        "duplicate_source",
        "source_camera",
        "source_digest",
        "source_clock",
        "schema",
        "boundary",
        "lineage",
        "unknown_event",
        "historical_role",
    ],
)
def test_batch_rejects_incomplete_or_substituted_identity(contracts, fault):
    _, b, _, _ = contracts
    s = b.sources[0]
    changes = {
        "duplicate_event": {"events": b.events * 2},
        "source_missing": {"sources": ()},
        "source_event": {"sources": (replace(s, event="synthetic:other"),)},
        "source_manifest": {"sources": (replace(s, manifest_reference="other"),)},
        "duplicate_source": {"sources": b.sources * 2},
        "source_camera": {"sources": (replace(s, camera="side"),)},
        "source_digest": {"sources": (replace(s, content_digest="absent"),)},
        "source_clock": {"sources": (replace(s, origin_us=True),)},
        "schema": {"schema": "UNKNOWN"},
        "boundary": {"boundaries": ("EXIT_INVENTED",)},
        "lineage": {"lineage_digest": "missing"},
        "unknown_event": {
            "classification": CANDIDATE,
            "events": (("unindexed_duplicate", "TRAIN"),),
        },
        "historical_role": {
            "classification": CANDIDATE,
            "events": ((CANDIDATE_EVENTS[0], "DEVELOPMENT"),),
        },
    }
    with pytest.raises(ValueError):
        replace(b, **changes[fault]).validate()


def test_inventory_direction_preserved_without_signoff_and_no_r04_event010():
    assert len(CANDIDATE_EVENTS) == 27
    assert sum(e.startswith("train_events/") for e in CANDIDATE_EVENTS) == 23
    assert sum(e.startswith("no_train_events/") for e in CANDIDATE_EVENTS) == 3
    assert len(R04_EVENTS) == 11
    assert "train_events/event_010" not in R04_EVENTS


@pytest.mark.parametrize(
    "fault",
    [
        "negative",
        "float",
        "bool",
        "pts",
        "timebase",
        "origin",
        "range",
        "camera",
        "source",
        "version",
        "acoustic",
        "correction_parent",
    ],
)
def test_observation_rejects_invalid_clock_source_or_acoustic_shift(contracts, fault):
    _, b, roster, _ = contracts
    p = point(b, roster[0])
    if fault in ("negative", "float", "bool", "pts", "timebase", "origin", "range", "camera"):
        changes = {
            "negative": {"value_us": -1},
            "float": {"value_us": 1.0},
            "bool": {"value_us": True},
            "pts": {"pts_ticks": 1},
            "timebase": {"timebase": (1, 10)},
            "origin": {"origin_us": 100},
            "range": {"value_us": 11_000_000, "pts_ticks": 11_000_000},
            "camera": {"camera": "back"},
        }
        p = replace(p, observation=replace(p.observation, **changes[fault]))
    else:
        p = replace(
            p,
            **{
                "source": {"source_id": "missing"},
                "version": {"boundary_version": "other"},
                "acoustic": {"acoustic_shift_us": 1},
                "correction_parent": {"previous": "0" * 64},
            }[fault],
        )
    with pytest.raises(ValueError):
        p.validate(b)


@pytest.mark.parametrize("landmark", [None, "LENS_PLANE", "LEGACY_LENS_PLANE", "invented_exit"])
def test_t2_physical_entry_remains_deferred_and_cannot_be_lens_plane(contracts, landmark):
    _, b, roster, _ = contracts
    p = point(b, roster[0], "T2")
    p = replace(
        p,
        observation=replace(p.observation, landmark="legacy"),
        landmark_kind=landmark,
        landmark_evidence="unverified",
    )
    with pytest.raises(ValueError, match="physical entry"):
        p.validate(b)


@pytest.mark.parametrize(
    "state,direction",
    [("CENSORED", "LEFT"), ("CENSORED", "RIGHT"), ("UNCERTAIN", None), ("NOT_OBSERVABLE", None)],
)
def test_null_uncertainty_and_censoring_remain_nonpoint(contracts, state, direction):
    _, b, roster, _ = contracts
    p = replace(
        point(b, roster[0]),
        observation=Observation(
            "T2",
            "front",
            state,
            "missing physical landmark remains deferred",
            censoring_direction=direction,
        ),
    )
    p.validate(b)
    assert p.observation.value_us is None
    assert p.observation.censoring_direction == direction


def test_deep_mutable_batch_input_refused_before_lifecycle_creation(contracts):
    _, batch, roster, _ = contracts
    with pytest.raises(ValueError, match="immutable"):
        ReviewLifecycle(replace(batch, events=list(batch.events)), roster)


def test_control_characters_cannot_partially_mutate_observation_state(contracts):
    _, batch, roster, permissions = contracts
    engine = ReviewLifecycle(batch, roster)
    a = assignment(batch, roster[0], permissions[0])
    engine.assign(a, permissions[0], now=10)
    engine.open_session(a.assignment_id, permissions[0], now=10)
    item = point(batch, roster[0])
    item = replace(item, observation=replace(item.observation, rationale="invalid\x00rationale"))
    history = engine.history
    with pytest.raises(ValueError):
        engine.submit(a.assignment_id, item, permissions[0], now=10)
    assert engine.history == history and not engine.observations


def test_occupancy_alias_remains_unavailable_for_constructed_physical_landmark(contracts):
    _, batch, roster, _ = contracts
    item = point(batch, roster[0], "T2")
    item = replace(
        item,
        observation=replace(item.observation, landmark="constructed geometry"),
        landmark_kind="PHYSICAL_ROADWAY_ENTRY",
        landmark_evidence="synthetic:landmark",
    )
    value, reason = ReviewLifecycle(batch, roster).occupancy_start(item, now=10)
    assert value is None and reason == "PHYSICAL_ENTRY_DEFERRED_OR_CONSTRUCTED"


@pytest.mark.parametrize("fault", ["timebase", "range"])
def test_uncertain_original_pts_still_must_match_its_source_clock(contracts, fault):
    _, batch, roster, _ = contracts
    item = point(batch, roster[0])
    o = replace(
        item.observation,
        state="UNCERTAIN",
        value_us=None,
        **({"timebase": (1, 10)} if fault == "timebase" else {"pts_ticks": 11_000_000}),
    )
    with pytest.raises(ValueError, match="source contract"):
        replace(item, observation=o).validate(batch)


@pytest.mark.parametrize(
    "returned", [None, "", "synthetic:forged-principal", "different-unverified-principal"]
)
def test_external_statement_port_cannot_authenticate_a_different_or_mock_signer(
    contracts, returned
):
    # Deliberately contradictory verifier output exercises refusal only. No
    # deployment verifier or positive genuine evidence is created by this test.
    class ContradictoryPort:
        def verify(self, kind, subject_digest, reference, now):
            return returned

    from railway_detection.annotation.evidence_review.contracts import CANDIDATE

    _, batch, roster, _ = contracts
    source = replace(
        batch.sources[0], source_id="unverified-source-reference", event="train_events/event_001"
    )
    candidate = replace(
        batch,
        classification=CANDIDATE,
        events=(("train_events/event_001", "TRAIN"),),
        sources=(source,),
    )
    engine = ReviewLifecycle(candidate, roster, verifier=ContradictoryPort())
    with pytest.raises((ValueError, PermissionError)):
        engine._verify_statement(
            "HUMAN_OBSERVATION",
            {"classification": "UNVERIFIED_TEST_ONLY"},
            "unverified-statement-reference",
            "expected-unverified-principal",
            10,
        )
    assert not engine.observations
    assert not engine.readiness(now=10).genuine_evidence_accepted


def test_t2_adjudication_requires_landmark_attestation_separate_from_human_statement(contracts):
    class LandmarkRefusingPort:
        def __init__(self):
            self.calls = []

        def verify(self, kind, subject_digest, reference, now):
            self.calls.append(kind)
            if kind == "PHYSICAL_ENTRY_LANDMARK":
                raise PermissionError("no actual physical landmark evidence")
            if kind == "HUMAN_ADJUDICATION":
                return "unverified-expected-principal"
            raise PermissionError("all genuine evidence absent in this negative fixture")

    from railway_detection.annotation.evidence_review.contracts import CANDIDATE
    from railway_detection.annotation.evidence_review.lifecycle import Adjudication

    _, batch, roster, _ = contracts
    source = replace(
        batch.sources[0], source_id="unverified-source-reference", event="train_events/event_001"
    )
    candidate = replace(
        batch,
        classification=CANDIDATE,
        events=(("train_events/event_001", "TRAIN"),),
        sources=(source,),
    )
    port = LandmarkRefusingPort()
    engine = ReviewLifecycle(candidate, roster, verifier=port)
    resolution = replace(
        point(batch, roster[0], "T2"),
        landmark_kind="PHYSICAL_ROADWAY_ENTRY",
        landmark_evidence="unverified-landmark-reference",
    )
    record = Adjudication(
        "unverified-test-adjudication",
        source.event,
        source.source_id,
        "T2",
        "unverified-adjudicator-reference",
        (),
        "HUMAN_RESOLVED",
        "negative verification fixture, never stored",
        resolution,
        "unverified-human-statement-reference",
    )
    with pytest.raises(PermissionError, match="physical landmark"):
        engine._verify_adjudication(record, "unverified-expected-principal", 10)
    assert port.calls == ["HUMAN_ADJUDICATION", "PHYSICAL_ENTRY_LANDMARK"]
    assert not engine._adjudications and not engine.observations
