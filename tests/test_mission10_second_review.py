"""Mission 10 / WP10.4: RD-043 second-review enforcement on actual Stage-2.1 records.

Every fixture is synthetic and lives under pytest's tmp_path. No media outside tmp is opened.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from railway_detection.annotation import second_review as sr
from railway_detection.annotation.evaluation_readiness_gate import evaluate_readiness
from second_review_support import SECOND_REVIEWER, independent_second_review
from test_phase11_9_synthetic_pilot import PILOT_REVIEWER, SYNTHETIC_EVENTS, _build_pilot_record

ALLOW = frozenset({PILOT_REVIEWER, SECOND_REVIEWER})


def _record(tmp_path: Path, index: int) -> dict:
    return _build_pilot_record(tmp_path, SYNTHETIC_EVENTS[index])


def _registry_for(record: dict) -> dict:
    return {
        f"{record['cohort']}/{record['event_id']}": {
            "front": record["reviewer_observed_media_hashes"]["front_sha256"],
            "back": record["reviewer_observed_media_hashes"]["back_sha256"],
        }
    }


def _assess(records, *, registry=None, root=None, allow=ALLOW):
    return sr.assess_second_reviews(
        records, authorized_reviewers=allow, repository_root=root, media_sha256_registry=registry
    )


def _triggers(record, registry=None, candidates=None, problem=None):
    return sr.evaluate_record_triggers(
        record, candidates=candidates, candidate_problem=problem, media_registry_entry=registry
    ).triggers


# ---- individual triggers -------------------------------------------------------------------


def test_train_event_with_nothing_unusual_fires_no_trigger(tmp_path: Path):
    record = _record(tmp_path, 0)
    registry = _registry_for(record)[f"train_events/{record['event_id']}"]
    assert _triggers(record, registry) == ()


def test_censored_alone_is_not_a_trigger(tmp_path: Path):
    record = _record(tmp_path, 0)  # fixture already has T_scene_clear CENSORED
    assert record["boundary_adjudications"]["T_scene_clear"]["state"] == "CENSORED"
    registry = _registry_for(record)[f"train_events/{record['event_id']}"]
    assert sr.TRIGGER_UNCERTAIN_BOUNDARY not in _triggers(record, registry)
    assert _triggers(record, registry) == ()


def test_unobservable_not_applicable_alone_is_not_a_trigger(tmp_path: Path):
    record = _record(tmp_path, 1)  # no-train event: five UNOBSERVABLE_NOT_APPLICABLE boundaries
    registry = _registry_for(record)[f"no_train_events/{record['event_id']}"]
    assert _triggers(record, registry) == ()


@pytest.mark.parametrize("status", ["DISPUTED", "NEEDS_SECOND_REVIEW"])
def test_explicit_status_flag_is_a_trigger(tmp_path: Path, status: str):
    record = _record(tmp_path, 0)
    record["adjudication_status"] = status
    assert sr.TRIGGER_EXPLICIT_FLAG in _triggers(
        record, _registry_for(record)[f"train_events/{record['event_id']}"]
    )


def test_any_uncertain_boundary_is_a_trigger(tmp_path: Path):
    record = _record(tmp_path, 0)
    record["boundary_adjudications"]["T1_danger_zone_entry"] = {
        "state": "UNCERTAIN",
        "rationale": "x",
        "value_s": None,
        "reference_camera": None,
    }
    assert sr.TRIGGER_UNCERTAIN_BOUNDARY in _triggers(
        record, _registry_for(record)[f"train_events/{record['event_id']}"]
    )


def test_engine_event_t3_t4_interpretation_is_a_trigger_but_not_for_train_events(tmp_path: Path):
    engine = _record(tmp_path, 2)
    train = _record(tmp_path, 0)
    assert sr.TRIGGER_ENGINE_T3_T4 in _triggers(
        engine, _registry_for(engine)[f"engine_events/{engine['event_id']}"]
    )
    assert sr.TRIGGER_ENGINE_T3_T4 not in _triggers(
        train, _registry_for(train)[f"train_events/{train['event_id']}"]
    )


def test_engine_event_with_not_applicable_t3_t4_does_not_fire(tmp_path: Path):
    engine = _record(tmp_path, 2)
    for name in ("T3_locomotive_unit_clearance", "T4_tail_clearance"):
        engine["boundary_adjudications"][name] = {
            "state": "UNOBSERVABLE_NOT_APPLICABLE",
            "rationale": "no rear end",
            "value_s": None,
            "reference_camera": None,
        }
    assert sr.TRIGGER_ENGINE_T3_T4 not in _triggers(
        engine, _registry_for(engine)[f"engine_events/{engine['event_id']}"]
    )


def test_missing_or_inconsistent_media_hashes_are_a_trigger(tmp_path: Path):
    record = _record(tmp_path, 0)
    assert sr.TRIGGER_MEDIA_HASH in _triggers(record, None)
    wrong = {"front": "0" * 64, "back": record["reviewer_observed_media_hashes"]["back_sha256"]}
    assert sr.TRIGGER_MEDIA_HASH in _triggers(record, wrong)


def test_boundary_corrected_from_candidate_is_a_trigger(tmp_path: Path):
    record = _record(tmp_path, 0)
    registry = _registry_for(record)[f"train_events/{record['event_id']}"]
    same = {
        name: (e["state"] == "OBSERVABLE", e["value_s"])
        for name, e in record["boundary_adjudications"].items()
    }
    assert _triggers(record, registry, candidates=same) == ()
    moved = dict(same)
    moved["T1_danger_zone_entry"] = (True, 5.9)
    assert sr.TRIGGER_CORRECTED in _triggers(record, registry, candidates=moved)
    flipped = dict(same)
    flipped["T0_first_visible"] = (False, None)
    assert sr.TRIGGER_CORRECTED in _triggers(record, registry, candidates=flipped)


def test_unverifiable_proposal_is_treated_as_a_trigger(tmp_path: Path):
    record = _record(tmp_path, 0)
    registry = _registry_for(record)[f"train_events/{record['event_id']}"]
    assert sr.TRIGGER_CORRECTED in _triggers(record, registry, problem="proposal missing")


def test_front_back_conflict_is_disclosed_as_not_mechanically_evaluable():
    assert "FRONT_BACK_CONFLICT" in sr.NOT_MECHANICALLY_EVALUABLE
    assert "FRONT_BACK_CONFLICT" not in sr.EVALUATED_TRIGGERS


# ---- proposal binding ----------------------------------------------------------------------


def _write_proposal(root: Path, record: dict, mutate=None) -> None:
    candidates = {
        name: {"candidate_observable": e["state"] == "OBSERVABLE", "value_s": e["value_s"]}
        for name, e in record["boundary_adjudications"].items()
    }
    if mutate:
        mutate(candidates)
    path = root / record["proposal_reference"]["proposal_file"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"proposed_timestamps": candidates}), encoding="utf-8")
    record["proposal_reference"]["proposal_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()


def test_candidate_loader_verifies_hash_and_location(tmp_path: Path):
    record = _record(tmp_path, 0)
    _write_proposal(tmp_path, record)
    values, problem = sr.load_candidate_values(record, repository_root=tmp_path)
    assert problem is None and values is not None
    assert values["T1_danger_zone_entry"] == (True, 5.8)

    tampered = copy.deepcopy(record)
    tampered["proposal_reference"]["proposal_sha256"] = "a" * 64
    assert sr.load_candidate_values(tampered, repository_root=tmp_path)[1] is not None

    escaping = copy.deepcopy(record)
    escaping["proposal_reference"]["proposal_file"] = "../outside.json"
    assert "outside" in (sr.load_candidate_values(escaping, repository_root=tmp_path)[1] or "")


def test_legacy_t3_alias_in_proposal_is_mapped(tmp_path: Path):
    record = _record(tmp_path, 0)

    def rename(c):
        c["T3_locomotive_exit"] = c.pop("T3_locomotive_unit_clearance")

    _write_proposal(tmp_path, record, rename)
    values, _ = sr.load_candidate_values(record, repository_root=tmp_path)
    assert "T3_locomotive_unit_clearance" in values


# ---- corpus-level enforcement --------------------------------------------------------------


def test_triggered_record_without_a_second_review_is_a_blocker(tmp_path: Path):
    engine = _record(tmp_path, 2)
    findings, _ = _assess([engine], registry=_registry_for(engine))
    assert [f.code for f in findings] == ["INDEPENDENT_SECOND_REVIEW_MISSING"]


def test_agreeing_independent_second_review_satisfies_the_precondition(tmp_path: Path):
    engine = _record(tmp_path, 2)
    second = independent_second_review(engine)
    findings, evidence = _assess([engine, second], registry=_registry_for(engine))
    assert findings == []
    assert any("does not replace researcher adjudication" in line for line in evidence)


def test_same_reviewer_cannot_second_review_their_own_record(tmp_path: Path):
    engine = _record(tmp_path, 2)
    clone = independent_second_review(engine, reviewer=PILOT_REVIEWER)
    findings, _ = _assess([engine, clone], registry=_registry_for(engine))
    assert [f.code for f in findings] == ["INDEPENDENT_SECOND_REVIEW_MISSING"]


def test_case_variant_of_same_identity_is_not_independent(tmp_path: Path):
    engine = _record(tmp_path, 2)
    clone = independent_second_review(engine, reviewer=PILOT_REVIEWER.upper())
    findings, _ = _assess(
        [engine, clone], registry=_registry_for(engine), allow=ALLOW | {PILOT_REVIEWER.upper()}
    )
    assert [f.code for f in findings] == ["INDEPENDENT_SECOND_REVIEW_MISSING"]


def test_second_reviewer_must_be_allowlisted(tmp_path: Path):
    engine = _record(tmp_path, 2)
    stranger = independent_second_review(engine, reviewer="stranger@example.com")
    findings, _ = _assess([engine, stranger], registry=_registry_for(engine))
    assert [f.code for f in findings] == ["INDEPENDENT_SECOND_REVIEW_MISSING"]


def test_non_approved_second_review_does_not_count(tmp_path: Path):
    engine = _record(tmp_path, 2)
    second = independent_second_review(engine)
    second["adjudication_status"] = "REJECTED"
    findings, _ = _assess([engine, second], registry=_registry_for(engine))
    assert [f.code for f in findings] == ["INDEPENDENT_SECOND_REVIEW_MISSING"]


def test_disagreement_stays_unresolved_and_no_tolerance_is_applied(tmp_path: Path):
    engine = _record(tmp_path, 2)
    second = independent_second_review(engine)
    second["boundary_adjudications"]["T4_tail_clearance"]["value_s"] = 45.000001  # 1 microsecond
    findings, _ = _assess([engine, second], registry=_registry_for(engine))
    assert [f.code for f in findings] == ["SECOND_REVIEW_DISAGREEMENT_UNRESOLVED"]
    assert "UNCERTAIN" in findings[0].detail


def test_sub_microsecond_representation_noise_is_not_a_disagreement(tmp_path: Path):
    engine = _record(tmp_path, 2)
    second = independent_second_review(engine)
    second["boundary_adjudications"]["T4_tail_clearance"]["value_s"] = 45.0 + 1e-12
    findings, _ = _assess([engine, second], registry=_registry_for(engine))
    assert findings == []


def test_state_or_camera_difference_is_a_disagreement(tmp_path: Path):
    engine = _record(tmp_path, 2)
    second = independent_second_review(engine)
    second["boundary_adjudications"]["T0_first_visible"]["reference_camera"] = "back"
    findings, _ = _assess([engine, second], registry=_registry_for(engine))
    assert [f.code for f in findings] == ["SECOND_REVIEW_DISAGREEMENT_UNRESOLVED"]


def test_orphan_second_review_target_is_a_blocker(tmp_path: Path):
    train = _record(tmp_path, 0)
    orphan = independent_second_review(train)
    orphan["second_review_of"] = "no-such-review"
    findings, _ = _assess([train, orphan], registry=_registry_for(train))
    assert "SECOND_REVIEW_TARGET_MISSING" in {f.code for f in findings}


def test_second_review_for_a_different_event_does_not_satisfy_the_trigger(tmp_path: Path):
    engine = _record(tmp_path, 2)
    other = _record(tmp_path, 0)
    wrong = independent_second_review(other)
    wrong["second_review_of"] = engine["review_id"]
    registry = {**_registry_for(engine), **_registry_for(other)}
    findings, _ = _assess([engine, other, wrong], registry=registry)
    assert "INDEPENDENT_SECOND_REVIEW_MISSING" in {f.code for f in findings}


def test_without_repository_root_trigger_six_is_disclosed_not_silently_passed(tmp_path: Path):
    train = _record(tmp_path, 0)
    findings, evidence = _assess([train], registry=_registry_for(train), root=None)
    assert findings == []
    assert any(sr.TRIGGER_CORRECTED in line and "not evaluated" in line for line in evidence)


def test_with_repository_root_an_unverifiable_proposal_blocks(tmp_path: Path):
    train = _record(tmp_path, 0)  # proposal file does not exist under tmp_path
    findings, _ = _assess([train], registry=_registry_for(train), root=tmp_path)
    assert [f.code for f in findings] == ["INDEPENDENT_SECOND_REVIEW_MISSING"]


# ---- the readiness gate consumes the enforcement -------------------------------------------


def _gate(tmp_path: Path, records: list[dict], reviewers=(PILOT_REVIEWER, SECOND_REVIEWER)):
    allow = tmp_path / "allow.json"
    allow.write_text(json.dumps({"authorized_reviewers": list(reviewers)}), encoding="utf-8")
    registry, paths, active = {}, {}, {}
    for record in records:
        eid, cohort = record["event_id"], record["cohort"]
        registry.update(_registry_for(record))
        paths[f"{cohort}/{eid}"] = {
            "front": str(tmp_path / f"{eid}_front.mov"),
            "back": str(tmp_path / f"{eid}_back.mov"),
        }
        active[eid] = record["proposal_reference"]["proposal_sha256"]
    return evaluate_readiness(
        records=records,
        active_proposal_sha256_by_event=active,
        media_sha256_registry=registry,
        allowlist_path=allow,
        media_file_paths=paths,
        required_cohorts=tuple({r["cohort"] for r in records}),
    )


def test_gate_refuses_engine_event_without_second_review(tmp_path: Path):
    verdict = _gate(tmp_path, [_record(tmp_path, 2)])
    assert not verdict.ready
    assert any(b.startswith("INDEPENDENT_SECOND_REVIEW_MISSING") for b in verdict.blockers)


def test_gate_accepts_engine_event_with_agreeing_independent_review(tmp_path: Path):
    engine = _record(tmp_path, 2)
    verdict = _gate(tmp_path, [engine, independent_second_review(engine)])
    assert verdict.ready, verdict.blockers


def test_gate_does_not_count_a_second_review_as_a_duplicate_primary(tmp_path: Path):
    engine = _record(tmp_path, 2)
    verdict = _gate(tmp_path, [engine, independent_second_review(engine)])
    assert not any("DUPLICATE_APPROVED_RECORD" in b for b in verdict.blockers)


def test_gate_still_flags_a_true_duplicate_primary(tmp_path: Path):
    engine = _record(tmp_path, 2)
    twin = copy.deepcopy(engine)
    twin["review_id"] = "twin"
    verdict = _gate(tmp_path, [engine, twin, independent_second_review(engine)])
    assert any("DUPLICATE_APPROVED_RECORD" in b for b in verdict.blockers)


def test_ground_truth_loader_counts_an_independent_second_review_once(tmp_path: Path):
    from railway_detection.evaluation.ground_truth_loader import load_approved_ground_truth

    engine = _record(tmp_path, 2)
    second = independent_second_review(engine)
    loaded = load_approved_ground_truth([engine, second], qualify_event_ids=True)
    assert [g.event_id for g in loaded] == [f"engine_events/{engine['event_id']}"]
    assert loaded[0].review_id == engine["review_id"]  # truth comes from the primary record


def test_ground_truth_loader_still_validates_the_second_review_record(tmp_path: Path):
    from railway_detection.evaluation.ground_truth_loader import (
        NotApprovedRefused,
        load_approved_ground_truth,
    )

    engine = _record(tmp_path, 2)
    second = independent_second_review(engine)
    second["adjudication_status"] = "REJECTED"
    second["adjudication_history"][-1]["status_set"] = "REJECTED"
    with pytest.raises(NotApprovedRefused):
        load_approved_ground_truth([engine, second], qualify_event_ids=True)
