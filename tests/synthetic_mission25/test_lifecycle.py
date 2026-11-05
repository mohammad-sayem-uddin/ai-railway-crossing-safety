"""Expected/actual state transitions use explicit non-promotable constructed inputs."""

from dataclasses import replace

import pytest
from tests.synthetic_mission25.test_contracts import CODE, assignment, point

from railway_detection.annotation.evidence_review.contracts import (
    CANDIDATE,
    RISKS,
    ReadinessStatus,
    digest,
)
from railway_detection.annotation.evidence_review.integration import fixture_contracts
from railway_detection.annotation.evidence_review.lifecycle import (
    Adjudication,
    PromotionReceipt,
    ReviewLifecycle,
)


def engine_one():
    _, batch, roster, permissions = fixture_contracts(CODE)
    engine = ReviewLifecycle(batch, roster)
    a = assignment(batch, roster[0], permissions[0])
    engine.assign(a, permissions[0], now=10)
    engine.open_session(a.assignment_id, permissions[0], now=10)
    return engine, a, roster, permissions


def complete(engine, a, roster, permissions, reviewer=0, delta=0):
    p = permissions[reviewer]
    for boundary in engine.batch.boundaries:
        o = point(engine.batch, roster[reviewer], boundary)
        o = replace(o, observation_id=f"synthetic:obs:{reviewer}:{boundary}")
        if boundary == "T2":
            o = replace(
                o,
                observation=replace(
                    o.observation, state="UNCERTAIN", value_us=None, pts_ticks=None, timebase=None
                ),
            )
        else:
            o = replace(
                o,
                observation=replace(
                    o.observation, value_us=1_000_000 + delta, pts_ticks=1_000_000 + delta
                ),
            )
        engine.submit(a.assignment_id, o, p, now=10)
    engine.complete(a.assignment_id, tuple((r, False) for r in RISKS), p, now=10)


def test_duplicate_assignment_and_observation_are_exactly_idempotent():
    e, a, roster, p = engine_one()
    history = e.history
    e.assign(a, p[0], now=10)
    assert e.history == history
    o = point(e.batch, roster[0])
    e.submit(a.assignment_id, o, p[0], now=10)
    history = e.history
    e.submit(a.assignment_id, o, p[0], now=10)
    assert e.history == history
    with pytest.raises(ValueError, match="overwritten"):
        e.submit(
            a.assignment_id,
            replace(o, observation=replace(o.observation, value_us=2_000_000, pts_ticks=2_000_000)),
            p[0],
            now=10,
        )
    assert e.observations == (o,)
    with pytest.raises(ValueError, match="duplicate assignment"):
        e.assign(replace(a, assignment_id="synthetic:different"), p[0], now=10)


@pytest.mark.parametrize("fault", ["revoked", "expired", "actor", "event", "reference"])
def test_submission_rechecks_current_permission_before_any_mutation(fault):
    e, a, roster, permissions = engine_one()
    change = {
        "revoked": {"revoked": True},
        "expired": {"expires": 10},
        "actor": {"actor": roster[1].reviewer_id},
        "event": {"events": ("synthetic:other",)},
        "reference": {"reference": "synthetic:other"},
    }
    p = replace(permissions[0], **change[fault])
    history = e.history
    with pytest.raises((ValueError, PermissionError)):
        e.submit(a.assignment_id, point(e.batch, roster[0]), p, now=10)
    assert e.history == history and not e.observations


def test_incomplete_batch_and_omitted_risk_assessment_never_complete():
    e, a, _, p = engine_one()
    with pytest.raises(ValueError, match="incomplete"):
        e.complete(a.assignment_id, tuple((r, False) for r in RISKS), p[0], now=10)
    with pytest.raises(ValueError, match="all explicit risk"):
        e.complete(a.assignment_id, (), p[0], now=10)
    assert "NO_COMPLETE_REVIEW" in e.readiness(now=10, permissions=p).reasons
    assert e.readiness(now=10, permissions=p).status == ReadinessStatus.CONSTRUCTED


def test_first_pass_cannot_be_silently_corrected_and_sealed_correction_keeps_original():
    e, a, roster, p = engine_one()
    o = point(e.batch, roster[0])
    e.submit(a.assignment_id, o, p[0], now=10)
    correction = replace(
        o, observation_id="synthetic:correction", previous=digest(o), correction_reason="informed"
    )
    with pytest.raises(ValueError, match="before seal"):
        e.submit(a.assignment_id, correction, p[0], now=10)
    for b in ("T2", "T3", "T4"):
        v = point(e.batch, roster[0], b)
        v = replace(v, observation_id="synthetic:obs:" + b)
        if b == "T2":
            v = replace(
                v,
                observation=replace(
                    v.observation, state="UNCERTAIN", value_us=None, pts_ticks=None, timebase=None
                ),
            )
        e.submit(a.assignment_id, v, p[0], now=10)
    e.complete(a.assignment_id, tuple((r, False) for r in RISKS), p[0], now=10)
    e.submit(a.assignment_id, correction, p[0], now=10)
    assert e.observations[0] == o
    assert e.observations[-1].previous == digest(o)
    assert "CORRECTED_FROM_CANDIDATE" in e.compare(a.event)["risk_reasons"]
    stale = replace(correction, observation_id="synthetic:stale-correction")
    with pytest.raises(ValueError, match="parent"):
        e.submit(a.assignment_id, stale, p[0], now=10)


def test_uncertainty_forces_second_review_even_if_caller_declares_no_risks():
    e, a, roster, p = engine_one()
    complete(e, a, roster, p)
    comparison = e.compare(a.event)
    assert comparison["required_second_review"]
    assert "UNCERTAIN_BOUNDARY" in comparison["risk_reasons"]
    assert "INDEPENDENT_SECOND_REVIEW_REQUIRED" in e.readiness(now=10, permissions=p).reasons


def two_reviews():
    e, a, roster, p = engine_one()
    complete(e, a, roster, p)
    b = replace(assignment(e.batch, roster[1], p[1]), assignment_id="synthetic:assignment:second")
    e.assign(b, p[1], now=10)
    e.open_session(b.assignment_id, p[1], now=10)
    complete(e, b, roster, p, reviewer=1, delta=200_000)
    return e, a, b, roster, p


def test_distinct_ids_with_same_physical_principal_cannot_satisfy_second_review():
    _, batch, roster, p = fixture_contracts(CODE)
    roster = (
        roster[0],
        replace(roster[1], principal_reference=roster[0].principal_reference),
        roster[2],
    )
    e = ReviewLifecycle(batch, roster)
    for n in (0, 1):
        a = replace(assignment(batch, roster[n], p[n]), assignment_id=f"synthetic:assignment:{n}")
        e.assign(a, p[n], now=10)
        e.open_session(a.assignment_id, p[n], now=10)
        complete(e, a, roster, p, reviewer=n)
    assert "INDEPENDENT_SECOND_REVIEW_REQUIRED" in e.readiness(now=10, permissions=p).reasons


def test_disagreement_retains_every_original_and_never_averages():
    e, a, _, _, p = two_reviews()
    originals = e.observations
    c = e.compare(a.event)
    assert len(c["disagreements"]) == 3
    assert all(
        d["state"] == "UNCERTAIN" and len(d["contributors"]) == 2 for d in c["disagreements"]
    )
    assert not c["automatic_adjudication"]
    assert e.observations == originals
    assert any(
        r.startswith("UNRESOLVED_DISAGREEMENT") for r in e.readiness(now=10, permissions=p).reasons
    )


@pytest.mark.parametrize(
    "fault",
    [
        "unqualified",
        "same_principal",
        "missing_parent",
        "missing_reason",
        "automatic_average",
        "unresolved_numeric",
        "missing_resolution",
    ],
)
def test_separate_adjudication_requires_qualification_all_parents_and_explicit_human_contract(
    fault,
):
    e, a, _, roster, p = two_reviews()
    if fault == "unqualified":
        from types import MappingProxyType

        e.roster = MappingProxyType(
            dict(e.roster) | {roster[2].reviewer_id: replace(roster[2], qualification=None)}
        )
    if fault == "same_principal":
        from types import MappingProxyType

        e.roster = MappingProxyType(
            dict(e.roster)
            | {
                roster[2].reviewer_id: replace(
                    roster[2], principal_reference=roster[0].principal_reference
                )
            }
        )
    adjudicator = replace(
        assignment(e.batch, roster[2], p[2], "ADJUDICATOR"), assignment_id="synthetic:adjudicator"
    )
    d = e.compare(a.event)["disagreements"][0]
    record = Adjudication(
        "synthetic:adjudication",
        a.event,
        d["source_id"],
        d["boundary"],
        roster[2].reviewer_id,
        d["contributors"],
        "UNCERTAIN",
        "explicit constructed unresolved fixture",
    )
    if fault == "missing_parent":
        record = replace(record, contributors=record.contributors[:1])
    if fault == "missing_reason":
        record = replace(record, reason="")
    if fault == "automatic_average":
        record = replace(record, state="AUTO_AVERAGED")
    if fault == "unresolved_numeric":
        record = replace(record, resolution=point(e.batch, roster[2]))
    if fault == "missing_resolution":
        record = replace(record, state="HUMAN_RESOLVED")
    old = e.observations
    with pytest.raises((ValueError, PermissionError)):
        e.assign(adjudicator, p[2], now=10)
        e.open_session(adjudicator.assignment_id, p[2], now=10)
        e.adjudicate(adjudicator.assignment_id, record, p[2], now=10)
    assert e.observations == old
    assert e.readiness(now=10, permissions=p).status == ReadinessStatus.CONSTRUCTED


def test_unresolved_adjudication_is_separate_immutable_idempotent_and_never_resolves_batch():
    e, a, _, roster, p = two_reviews()
    adjudicator = replace(
        assignment(e.batch, roster[2], p[2], "ADJUDICATOR"), assignment_id="synthetic:adjudicator"
    )
    e.assign(adjudicator, p[2], now=10)
    e.open_session(adjudicator.assignment_id, p[2], now=10)
    d = e.compare(a.event)["disagreements"][0]
    record = Adjudication(
        "synthetic:adjudication",
        a.event,
        d["source_id"],
        d["boundary"],
        roster[2].reviewer_id,
        d["contributors"],
        "UNCERTAIN",
        "constructed unresolved entry",
    )
    before = e.observations
    e.adjudicate(adjudicator.assignment_id, record, p[2], now=10)
    history = e.history
    e.adjudicate(adjudicator.assignment_id, record, p[2], now=10)
    assert e.history == history and e.observations == before
    with pytest.raises(ValueError, match="immutable"):
        e.adjudicate(adjudicator.assignment_id, replace(record, reason="overwrite"), p[2], now=10)
    assert any(r.startswith("UNRESOLVED") for r in e.readiness(now=10, permissions=p).reasons)


@pytest.mark.parametrize(
    "fault", ["fixture", "expired", "revoked", "wrong_batch", "missing_event", "duplicate"]
)
def test_constructed_or_invalid_permission_cannot_validate_any_promotion_receipt(fault):
    e, _, _, _, p = two_reviews()
    promoter = replace(p[2], operations=("PROMOTE_GT",))
    receipt = PromotionReceipt(
        "synthetic:receipt:never-issued",
        digest(e.batch),
        digest(e.history),
        e.batch.lineage_digest,
        "0" * 64,
        promoter.actor,
        promoter.reference,
        "unverified",
    )
    if fault == "expired":
        promoter = replace(promoter, expires=10)
    elif fault == "revoked":
        promoter = replace(promoter, revoked=True)
    elif fault == "wrong_batch":
        receipt = replace(receipt, batch_digest="0" * 64)
    elif fault == "missing_event":
        promoter = replace(promoter, events=())
    for _ in range(2 if fault == "duplicate" else 1):
        with pytest.raises((ValueError, PermissionError)):
            e.validate_promotion_receipt(receipt, promoter, now=10, review_permissions=p)
    assert not e._publications


def test_external_metadata_incomplete_status_has_precise_missing_human_and_source_reasons():
    _, b, roster, _ = fixture_contracts(CODE)
    source = replace(b.sources[0], event="train_events/event_001")
    b = replace(
        b,
        classification=CANDIDATE,
        events=(("train_events/event_001", "TRAIN"),),
        sources=(source,),
    )
    e = ReviewLifecycle(b, roster)
    ready = e.readiness(now=10)
    assert ready.status == ReadinessStatus.INCOMPLETE
    assert "NO_COMPLETE_REVIEW" in ready.reasons
    assert any("SOURCE_IDENTITY" in reason for reason in ready.reasons)
    assert any("CANONICAL_SCHEMA_ACCEPTANCE" in reason for reason in ready.reasons)
    assert not ready.genuine_evidence_accepted
