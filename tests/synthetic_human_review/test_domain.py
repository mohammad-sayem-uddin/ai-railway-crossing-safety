from dataclasses import replace

import pytest

from railway_detection.annotation.human_review_domain import (
    BOUNDARIES,
    RISK_SUBJECTS,
    ConstructedPlayer,
    Observation,
    ReviewWorkflow,
    SyntheticReviewer,
)


def workflow():
    return ReviewWorkflow(
        (
            SyntheticReviewer("synthetic:a", ("REVIEWER",)),
            SyntheticReviewer("synthetic:b", ("REVIEWER",)),
            SyntheticReviewer("synthetic:judge", ("ADJUDICATOR",)),
        ),
        aliases=(("synthetic:alias", "synthetic:a"),),
    )


def observations():
    return tuple(
        Observation(k, "front", "NOT_OBSERVABLE", "constructed unknown") for k in BOUNDARIES
    )


def risk(**kw):
    return tuple((k, kw.get(k, False)) for k in RISK_SUBJECTS)


def test_blind_seals_exposure_alias_and_informed_append():
    w = workflow()
    a = w.seal("synthetic:a", "synthetic:event", observations())
    w.seal("synthetic:b", "synthetic:event", observations())
    assert (
        len(w.compare("synthetic:a", "synthetic:event", risk_inputs=risk(UNCERTAIN_BOUNDARY=True)))
        == 2
    )
    with pytest.raises(ValueError):
        w.seal("synthetic:alias", "synthetic:event", observations())
    correction = w.correct(
        "synthetic:a", "synthetic:event", observations(), reason="constructed correction"
    )
    assert correction.kind == "INFORMED_CORRECTION" and correction.previous == a.digest
    assert w.history[0] == a
    assert w.draft()["active_schema_satisfied"] is False


@pytest.mark.parametrize("subject", RISK_SUBJECTS)
def test_all_six_risk_subjects_and_missing_second(subject):
    w = workflow()
    w.seal("synthetic:a", "synthetic:event", observations())
    with pytest.raises(ValueError):
        w.compare("synthetic:a", "synthetic:event", risk_inputs=risk(**{subject: True}))


def test_unknown_trigger_and_hash_identity_fail_closed():
    w = workflow()
    for actor in ["synthetic:a", "synthetic:b"]:
        w.seal(actor, "synthetic:event", observations())
    for value in [None, True]:
        with pytest.raises(ValueError):
            w.compare(
                "synthetic:a",
                "synthetic:event",
                risk_inputs=risk(MEDIA_HASH_MISSING_OR_INCONSISTENT=value),
            )


def test_no_second_required_and_uncertain_adjudication():
    w = workflow()
    w.seal("synthetic:a", "synthetic:event", observations())
    assert len(w.compare("synthetic:a", "synthetic:event", risk_inputs=risk())) == 1
    w.seal("synthetic:b", "synthetic:event", observations())
    sources = tuple(
        s.digest for s in w.compare("synthetic:a", "synthetic:event", risk_inputs=risk())
    )
    assert (
        w.adjudicate(
            "synthetic:judge",
            "synthetic:event",
            source_digests=sources,
            state="UNCERTAIN",
            rationale="unresolved constructed disagreement",
        )[-2]
        == "UNCERTAIN"
    )
    with pytest.raises(ValueError):
        w.adjudicate(
            "synthetic:judge",
            "synthetic:event",
            source_digests=sources,
            state="OBSERVABLE",
            rationale="no automatic averaging",
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"state": "CENSORED", "value_us": 2, "censoring_direction": "LEFT"},
        {"state": "OBSERVABLE", "value_us": True},
        {"state": "APPROVED"},
        {"boundary": "T2", "state": "OBSERVABLE", "value_us": 0},
        {"state": "OBSERVABLE", "value_us": 1000000, "pts_ticks": 1, "timebase": (1, 2)},
    ],
)
def test_boundary_no_point_or_landmark_invention(changes):
    with pytest.raises(ValueError):
        replace(observations()[0], **changes).validate()


def test_pts_player_and_cross_camera_clocks():
    p = ConstructedPlayer(((0, "NEUTRAL_CONSTRUCTED_FRAME"), (40000, "NEUTRAL_CONSTRUCTED_FRAME")))
    assert p.seek(1)[0] == 40000
    for bad in [True, -1, 2]:
        with pytest.raises(ValueError):
            p.seek(bad)
    with pytest.raises(ValueError):
        ConstructedPlayer(((0, "MODEL_PREDICTION"),))
    o = Observation(
        "T1", "front", "OBSERVABLE", "constructed", 1000000, pts_ticks=25, timebase=(1, 25)
    )
    o.validate()
    assert (
        Observation("T2", "back", "CENSORED", "missing", censoring_direction="RIGHT").value_us
        is None
    )
