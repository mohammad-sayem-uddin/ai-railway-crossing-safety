"""Mission 4A Synthetic Regression Suite: Governance Reconciliation,
Authorization Integrity, LEG-EXEC Dry-Run Safety, and Stage-2.1 Verification.

Safety invariants enforced by this test suite:
- Never opens, decodes, or hashes raw `.mov`, `.mp4`, or `.wav` files.
- All file-writing tests execute strictly inside pytest `tmp_path`.
- Repository-level checks are strictly read-only metadata / dry-run checks.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from railway_detection.annotation.adjudication_session import (
    AdjudicationSession,
    AdjudicationSessionError,
    EventNotInManifestError,
    SessionEvent,
)
from railway_detection.annotation.evaluation_readiness_gate import evaluate_readiness
from railway_detection.annotation.invalidation_notice_writer import (
    ProposalBindingError,
    apply_invalidation_notices,
    load_and_verify_proposal,
    plan_invalidation_notices,
)
from railway_detection.annotation.notices import (
    excused_legacy_records,
    invalid_notices,
    scan_notices,
)
from railway_detection.annotation.promotion_gate import (
    AuthorizedReviewersLoadError,
    PromotionRejected,
    load_authorized_reviewers,
    promote_record,
    validate_batch_for_promotion,
    validate_for_promotion,
    validate_non_synthetic_record,
)
from railway_detection.annotation.receipt import (
    PROMOTION_RECEIPT_PRODUCER,
    PROMOTION_RECEIPT_SCHEMA,
    receipt_body_sha256,
    sha256_file,
)
from railway_detection.annotation.review_session import build_review_record
from railway_detection.annotation.schemas import SchemaValidationError
from railway_detection.annotation.stage2_1_schema import (
    CANONICAL_TIMESTAMPS,
    build_stage2_1_record_from_dict,
)
from railway_detection.annotation.stage21_timing_pilot import (
    PilotWorkflowError,
    _require_preparation_isolation,
)
from railway_detection.evaluation.descriptive_only import (
    DescriptiveOnlyInput,
    aggregate_descriptive_only,
)
from railway_detection.evaluation.evaluation_runner import (
    EvaluationRefused,
    Phase12EvaluationRunner,
)
from railway_detection.evaluation.execution_gate import (
    assess_official_phase12_readiness,
)
from railway_detection.evaluation.governance import (
    PROMOTION_RECEIPT_RELATIVE,
    GovernanceError,
    verify_promotion_receipt,
)
from railway_detection.evaluation.metrics import (
    EventMetricsCalculator,
    SingleEventEvaluation,
)
from railway_detection.experiments.cache_provenance import (
    CACHE_REUSE_ISOLATED_RUN,
    CONTROLLED_CACHE_SCHEMA_VERSION,
    PROHIBITED_AUDIO_V2_SHA256,
    CacheProvenanceError,
    ControlledCacheProvenance,
    load_controlled_cache_jsonl,
    write_controlled_cache_jsonl,
)
from railway_detection.experiments.frozen_config import load_frozen_config
from railway_detection.experiments.layer_b_processor import LayerBEventProcessor
from railway_detection.experiments.preflight_validator import (
    CANONICAL_DECISION_REGISTER,
    CONFIG_CLASS_RESEARCHER_APPROVED,
    CONFIG_CLASS_UNRESOLVED,
    DECISION_STATUS_APPROVED,
    DECISION_STATUS_IMPLEMENTED_NOT_APPROVED,
    DECISION_STATUS_PENDING,
    DECISION_STATUS_RECOMMENDATION_ONLY,
    DECISION_STATUS_SUPERSEDED,
    DECISION_STATUSES,
    HISTORICAL_DECISION_ALIASES,
    classify_experiment_parameters,
    lookup_decision_register,
    run_experiment_preflight,
)
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality

REPO_ROOT = Path(__file__).resolve().parents[2]


def _make_valid_boundaries() -> dict[str, dict[str, Any]]:
    return {
        "T0_first_visible": {
            "state": "OBSERVABLE",
            "rationale": "First visible appearance of locomotive on front stream.",
            "value_s": 2.0,
            "reference_camera": "front",
            "frame_index": 10,
        },
        "T1_danger_zone_entry": {
            "state": "OBSERVABLE",
            "rationale": "Train nose enters crossing danger zone on front stream.",
            "value_s": 3.0,
            "reference_camera": "front",
            "frame_index": 15,
        },
        "T2_crossing_occupancy_start": {
            "state": "OBSERVABLE",
            "rationale": "Crossing occupancy begins.",
            "value_s": 3.6,
            "reference_camera": "front",
            "frame_index": 18,
        },
        "T3_locomotive_unit_clearance": {
            "state": "OBSERVABLE",
            "rationale": "Locomotive unit clears danger zone on rear stream.",
            "value_s": 9.0,
            "reference_camera": "back",
            "frame_index": 45,
        },
        "T4_tail_clearance": {
            "state": "OBSERVABLE",
            "rationale": "Train tail clears crossing danger zone on rear stream.",
            "value_s": 12.0,
            "reference_camera": "back",
            "frame_index": 60,
        },
        "T_scene_clear": {
            "state": "OBSERVABLE",
            "rationale": "Crossing scene clear after tail passage.",
            "value_s": 13.0,
            "reference_camera": "back",
            "frame_index": 65,
        },
    }


def _make_stage21_fixture(
    tmp_path: Path,
    *,
    event_id: str = "event_001",
    cohort: str = "train_events",
    reviewer_id: str = "dr.rahman@buet.ac.bd",
    review_id: str | None = None,
    session_id: str = "session_real_001",
    start_utc: str = "2026-11-01T09:00:00Z",
    end_utc: str = "2026-11-01T09:04:00Z",
    status: str = "APPROVED",
) -> tuple[dict[str, Any], dict[str, str], dict[str, dict[str, str]], dict[str, dict[str, str]], Path]:
    media_dir = tmp_path / "fixture_blobs"
    media_dir.mkdir(parents=True, exist_ok=True)
    front_blob = media_dir / f"{cohort}_{event_id}_front.bin"
    back_blob = media_dir / f"{cohort}_{event_id}_back.bin"
    front_blob.write_bytes(f"front-bytes-{cohort}-{event_id}".encode())
    back_blob.write_bytes(f"back-bytes-{cohort}-{event_id}".encode())

    front_sha = hashlib.sha256(front_blob.read_bytes()).hexdigest()
    back_sha = hashlib.sha256(back_blob.read_bytes()).hexdigest()
    prop_sha = hashlib.sha256(f"proposal-{cohort}-{event_id}".encode()).hexdigest()

    allowlist_path = tmp_path / "authorized_reviewers.json"
    allowlist_path.write_text(
        json.dumps(
            {
                "authorized_reviewers": [
                    reviewer_id,
                    "dr.karim@buet.ac.bd",
                    "dr.chowdhury@buet.ac.bd",
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    rec = build_review_record(
        event_id=event_id,
        cohort=cohort,
        reviewer_id=reviewer_id,
        authorized_reviewers=frozenset(
            {reviewer_id, "dr.karim@buet.ac.bd", "dr.chowdhury@buet.ac.bd"}
        ),
        review_session_id=session_id,
        review_start_utc=start_utc,
        review_end_utc=end_utc,
        inspection_tool="mpv_frame_step_v2",
        attestation_statement=(
            "I independently stepped through both camera streams and recorded each "
            "boundary state without consulting model outputs."
        ),
        attested_at_utc=end_utc,
        front_media_path=front_blob,
        back_media_path=back_blob,
        observed_at_utc=start_utc,
        proposal_file=f"data/ground_truth/proposals/{cohort}_{event_id}.json",
        proposal_sha256=prop_sha,
        boundary_adjudications=_make_valid_boundaries(),
        adjudication_status=status,
        review_id=review_id,
    )
    qualified = f"{cohort}/{event_id}"
    proposals = {qualified: prop_sha, event_id: prop_sha}
    registry = {
        qualified: {"front": front_sha, "back": back_sha},
        event_id: {"front": front_sha, "back": back_sha},
    }
    paths = {
        qualified: {"front": str(front_blob), "back": str(back_blob)},
        event_id: {"front": str(front_blob), "back": str(back_blob)},
    }
    return rec, proposals, registry, paths, allowlist_path


# ===========================================================================
# Objective A: Governance Decision Register Reconciliation Tests
# ===========================================================================


def test_canonical_decision_register_statuses_and_historical_reconciliation() -> None:
    expected_statuses = {
        "APPROVED_BY_RESEARCHER",
        "PENDING_RESEARCHER_DECISION",
        "TECHNICAL_RECOMMENDATION_ONLY",
        "IMPLEMENTED_BUT_NOT_SCIENTIFICALLY_APPROVED",
        "SUPERSEDED_WITH_EXPLICIT_RECORD",
        "NOT_APPLICABLE",
    }
    assert DECISION_STATUSES == expected_statuses

    # Historical D1..D4 resolve to their exact historical meanings, never to overloaded M3 meanings
    d1 = lookup_decision_register("D1")
    assert d1.canonical_id == "GOV-D1-PROTOCOL-AUTHORITY"
    assert d1.status == DECISION_STATUS_PENDING
    assert d1.technical_recommendation_status == DECISION_STATUS_RECOMMENDATION_ONLY

    d2 = lookup_decision_register("D2")
    assert d2.canonical_id == "GOV-D2-EVALUATION-PROFILE"
    assert d2.status == DECISION_STATUS_PENDING
    assert d2.technical_recommendation_status == DECISION_STATUS_RECOMMENDATION_ONLY

    d3 = lookup_decision_register("D3")
    assert d3.canonical_id == "GOV-D3-DESCRIPTIVE-MODE"
    assert d3.status == DECISION_STATUS_APPROVED

    d3_split = lookup_decision_register("D3_SPLIT")
    assert d3_split.canonical_id == "AUTH-EVENT-SPLIT"
    assert d3_split.status == DECISION_STATUS_PENDING

    d4 = lookup_decision_register("D4")
    assert d4.canonical_id == "GOV-D4-R04-SYNCHRONIZATION"
    assert d4.status == DECISION_STATUS_PENDING
    assert d4.technical_recommendation_status == DECISION_STATUS_RECOMMENDATION_ONLY

    # Approved 2026-10-30 & Phase 11 decisions
    assert lookup_decision_register("B7d").status == DECISION_STATUS_APPROVED
    assert lookup_decision_register("B7e").status == DECISION_STATUS_APPROVED
    assert lookup_decision_register("B7e_PARAMETERS").status == DECISION_STATUS_PENDING
    assert lookup_decision_register("GT_SEPARATION").status == DECISION_STATUS_APPROVED
    assert lookup_decision_register("ENGINE_ISOLATION").status == DECISION_STATUS_APPROVED
    assert lookup_decision_register("LEG_EXEC").status == DECISION_STATUS_APPROVED
    assert lookup_decision_register("STAGE21_SAFEGUARDS").status == DECISION_STATUS_APPROVED
    assert lookup_decision_register("EVAL_AUTH").status == DECISION_STATUS_PENDING

    # Reconciled experimental parameter domains
    exp_thresh = lookup_decision_register("EXP-OPERATING-THRESHOLDS")
    assert exp_thresh.status == DECISION_STATUS_IMPLEMENTED_NOT_APPROVED
    exp_roi = lookup_decision_register("EXP-ROI-GEOMETRY")
    assert exp_roi.status == DECISION_STATUS_PENDING
    superseded = lookup_decision_register("M3-OVERLOADED-D1-D2-LABELS")
    assert superseded.status == DECISION_STATUS_SUPERSEDED

    for alias, target in HISTORICAL_DECISION_ALIASES.items():
        assert lookup_decision_register(alias) == CANONICAL_DECISION_REGISTER[target]


def test_preflight_validator_separates_d1_d2_from_thresholds_and_roi() -> None:
    frozen = load_frozen_config()
    classifications = classify_experiment_parameters(
        frozen,
        experiment_family="B4",
        protocol_authority_d1_approved=False,
        evaluation_profile_d2_approved=False,
        operating_thresholds_approved=True,
        roi_geometry_approved=False,
        d4_approved=False,
    )
    by_key = {c.parameter_key: c for c in classifications}
    assert (
        by_key["protocol_and_ground_truth_authority"].decision_reference
        == "GOV-D1-PROTOCOL-AUTHORITY"
    )
    assert (
        by_key["protocol_and_ground_truth_authority"].classification
        == CONFIG_CLASS_UNRESOLVED
    )
    assert (
        by_key["premature_opening_evaluation_profile"].decision_reference
        == "GOV-D2-EVALUATION-PROFILE"
    )
    assert (
        by_key["fusion_and_operating_thresholds"].decision_reference
        == "EXP-OPERATING-THRESHOLDS"
    )
    assert (
        by_key["fusion_and_operating_thresholds"].classification
        == CONFIG_CLASS_RESEARCHER_APPROVED
    )
    assert (
        by_key["roi_and_calibration_geometry"].decision_reference
        == "EXP-ROI-GEOMETRY"
    )
    assert (
        by_key["timing.cross_camera_sync"].decision_reference
        == "GOV-D4-R04-SYNCHRONIZATION"
    )

    report = run_experiment_preflight(
        frozen,
        experiment_family="B4",
        evaluation_mode="official_evaluation",
        protocol_authority_d1_approved=False,
        evaluation_profile_d2_approved=False,
        operating_thresholds_approved=False,
        roi_geometry_approved=False,
        d4_approved=False,
    )
    decision_codes = {f.code for f in report.unresolved_scientific_decision_blockers}
    assert "DECISION_D1_PENDING" in decision_codes
    assert "DECISION_D2_PENDING" in decision_codes
    assert "DECISION_EXP_OPERATING_THRESHOLDS_PENDING" in decision_codes
    assert "DECISION_EXP_ROI_GEOMETRY_PENDING" in decision_codes
    assert "DECISION_D4_PENDING" in decision_codes


# ===========================================================================
# Objective B: Engine-Event Scope Reconciliation Tests
# ===========================================================================


def test_repository_engine_event_scope_is_exactly_one_event() -> None:
    # 1. Inventory manifest
    inv_path = REPO_ROOT / "data" / "manifests" / "layer_b_v2_annotation_inventory.json"
    inv_data = json.loads(inv_path.read_text(encoding="utf-8"))
    cohorts: dict[str, list[str]] = {}
    for ev in inv_data.values():
        cohorts.setdefault(ev["category"], []).append(ev["event_id"])
    assert cohorts["engine_events"] == ["event_001"]
    assert sorted(cohorts["no_train_events"]) == ["event_001", "event_002", "event_003"]
    assert len(cohorts["train_events"]) == 23
    assert sum(len(v) for v in cohorts.values()) == 27

    # 2. Proposals directory (3 proposal versions v1..v3 all belong to event_001)
    proposals_dir = REPO_ROOT / "data" / "ground_truth" / "proposals"
    engine_proposals = sorted(p.name for p in (proposals_dir / "engine_events").glob("*.json"))
    assert engine_proposals == [
        "event_001_proposal_v1.json",
        "event_001_proposal_v2.json",
        "event_001_proposal_v3.json",
    ]
    assert all(name.startswith("event_001_") for name in engine_proposals)

    # 3. Reviews directory
    reviews_dir = REPO_ROOT / "data" / "ground_truth" / "reviews"
    engine_reviews = sorted(p.name for p in (reviews_dir / "engine_events").glob("*_review.json"))
    assert engine_reviews == ["event_001_review.json"]
    assert not (reviews_dir / "engine_events" / "event_002_review.json").exists()
    assert not (reviews_dir / "engine_events" / "event_003_review.json").exists()

    # 4. Stage-2.1 Review Queue
    queue_path = REPO_ROOT / "docs" / "generated" / "STAGE21_REVIEW_QUEUE.json"
    queue_data = json.loads(queue_path.read_text(encoding="utf-8"))
    assert queue_data["summary"]["total_events"] == 27
    engine_queue_items = [
        item for item in queue_data["items"] if item["cohort"] == "engine_events"
    ]
    notrain_queue_items = [
        item for item in queue_data["items"] if item["cohort"] == "no_train_events"
    ]
    train_queue_items = [
        item for item in queue_data["items"] if item["cohort"] == "train_events"
    ]
    assert len(engine_queue_items) == 1
    assert len(notrain_queue_items) == 3
    assert len(train_queue_items) == 23
    assert engine_queue_items[0]["event_key"] == "engine_events/event_001"


def test_single_engine_event_isolated_from_train_and_negative_control_denominators() -> None:
    train_eval = SingleEventEvaluation(
        event_id="train_events/event_001",
        scenario_name="synth",
        has_train_ground_truth=True,
        missed_train=False,
        evaluable=True,
    )
    notrain_eval = SingleEventEvaluation(
        event_id="no_train_events/event_001",
        scenario_name="synth",
        has_train_ground_truth=False,
        blocked_seconds=0.0,
        closure_episodes=0,
        exposure_s=360.0,
        evaluable=True,
    )
    engine_eval = SingleEventEvaluation(
        event_id="engine_events/event_001",
        scenario_name="synth",
        has_train_ground_truth=False,
        notes="engine_event_excluded",
        blocked_seconds=12.0,
        closure_episodes=2,
        missed_train=True,
        evaluable=False,
    )
    agg = EventMetricsCalculator.aggregate_cohort([train_eval, notrain_eval, engine_eval])
    assert agg.total_events == 3
    assert agg.eligible_events == 1
    assert agg.no_train_events == 1
    assert agg.engine_events == 1
    assert agg.missed_train_count == 0
    assert agg.false_alarm_count == 0

    desc = aggregate_descriptive_only(
        DescriptiveOnlyInput(
            event_evaluations=(train_eval, notrain_eval, engine_eval),
            population_label="synthetic_27_event_structure",
            provenance={"cache_classification": "historical_diagnostic"},
            limitations=("Synthetic test only",),
            permitted_claims=("Descriptive summary only",),
        )
    )
    assert desc.summary.engine_events == 1
    assert desc.engine_case_study_ids == ("engine_events/event_001",)
    assert desc.official_evaluation_eligible is False


# ===========================================================================
# Objective C: Stage-2.1 Synthetic ID Guard & Real-vs-Synthetic Boundary Tests
# ===========================================================================


def test_adjudication_session_and_timing_pilot_enforce_synthetic_and_path_isolation(
    tmp_path: Path,
) -> None:
    # AdjudicationSession refuses real event_id without synthetic_ prefix
    front = tmp_path / "front.bin"
    back = tmp_path / "back.bin"
    front.write_bytes(b"front")
    back.write_bytes(b"back")
    front_sha = hashlib.sha256(front.read_bytes()).hexdigest()
    back_sha = hashlib.sha256(back.read_bytes()).hexdigest()
    proposal = tmp_path / "prop.json"
    proposal.write_text("{}", encoding="utf-8")
    prop_sha = hashlib.sha256(proposal.read_bytes()).hexdigest()

    real_id_event = SessionEvent(
        event_key="train_events/event_001",
        event_id="event_001",
        cohort="train_events",
        front_media_path=front,
        back_media_path=back,
        expected_front_sha256=front_sha,
        expected_back_sha256=back_sha,
        proposal_file=str(proposal),
        proposal_sha256=prop_sha,
    )
    with pytest.raises(EventNotInManifestError, match="beginning with 'synthetic_'"):
        AdjudicationSession(
            event=real_id_event,
            reviewer_id="synthetic_reviewer_01",
            authorized_reviewers=frozenset({"synthetic_reviewer_01"}),
            output_dir=tmp_path / "out",
        )

    # AdjudicationSession refuses non-temp output_dir even with synthetic_ IDs
    synth_event = SessionEvent(
        event_key="train_events/synthetic_event_001",
        event_id="synthetic_event_001",
        cohort="train_events",
        front_media_path=front,
        back_media_path=back,
        expected_front_sha256=front_sha,
        expected_back_sha256=back_sha,
        proposal_file=str(proposal),
        proposal_sha256=prop_sha,
    )
    with pytest.raises(AdjudicationSessionError, match="SYNTHETIC_ONLY_PATH_REQUIRED"):
        AdjudicationSession(
            event=synth_event,
            reviewer_id="synthetic_reviewer_01",
            authorized_reviewers=frozenset({"synthetic_reviewer_01"}),
            output_dir=REPO_ROOT / "data" / "ground_truth" / "canonical",
        )

    # stage21_timing_pilot refuses non-temp root or real repository paths in preparation mode
    with pytest.raises(PilotWorkflowError, match="PREPARATION_ISOLATION_REQUIRED"):
        _require_preparation_isolation(
            REPO_ROOT,
            (REPO_ROOT / "data" / "ground_truth" / "canonical",),
        )


def test_promotion_and_readiness_gates_reject_synthetic_records_when_enforced(
    tmp_path: Path,
) -> None:
    rec, proposals, registry, paths, allowlist_path = _make_stage21_fixture(
        tmp_path,
        event_id="synthetic_event_001",
        reviewer_id="pilot.reviewer@synthetic.example.com",
        session_id="synthetic_session_001",
    )
    direct_violations = validate_non_synthetic_record(rec, media_file_paths=paths)
    assert any(v.code == "SYNTHETIC_RECORD_NOT_PROMOTABLE" for v in direct_violations)

    # When disallow_synthetic_identifiers=True, validate_for_promotion rejects synthetic record
    authorized = load_authorized_reviewers(allowlist_path)
    promo_violations = validate_for_promotion(
        rec,
        active_proposal_sha256_by_event=proposals,
        media_sha256_registry=registry,
        authorized_reviewers=authorized,
        media_file_paths=paths,
        disallow_synthetic_identifiers=True,
    )
    assert any(v.code == "SYNTHETIC_RECORD_NOT_PROMOTABLE" for v in promo_violations)

    # promote_record with disallow_synthetic_identifiers=True refuses to write file
    out_dir = tmp_path / "canonical_attempt"
    with pytest.raises(PromotionRejected) as exc_info:
        promote_record(
            rec,
            output_dir=out_dir,
            active_proposal_sha256_by_event=proposals,
            media_sha256_registry=registry,
            authorized_reviewers=authorized,
            media_file_paths=paths,
            disallow_synthetic_identifiers=True,
        )
    assert any(
        v.code == "SYNTHETIC_RECORD_NOT_PROMOTABLE" for v in exc_info.value.violations
    )
    assert not out_dir.exists()

    # evaluate_readiness with disallow_synthetic_identifiers=True rejects synthetic records
    rec_notrain, p2, r2, m2, _ = _make_stage21_fixture(
        tmp_path,
        event_id="synthetic_event_002",
        cohort="no_train_events",
        reviewer_id="pilot.reviewer@synthetic.example.com",
        session_id="synthetic_session_002",
        start_utc="2026-11-01T10:00:00Z",
        end_utc="2026-11-01T10:04:00Z",
    )
    rec_engine, p3, r3, m3, _ = _make_stage21_fixture(
        tmp_path,
        event_id="synthetic_event_003",
        cohort="engine_events",
        reviewer_id="pilot.reviewer@synthetic.example.com",
        session_id="synthetic_session_003",
        start_utc="2026-11-01T11:00:00Z",
        end_utc="2026-11-01T11:04:00Z",
    )
    verdict = evaluate_readiness(
        records=[rec, rec_notrain, rec_engine],
        active_proposal_sha256_by_event={**proposals, **p2, **p3},
        media_sha256_registry={**registry, **r2, **r3},
        allowlist_path=allowlist_path,
        media_file_paths={**paths, **m2, **m3},
        disallow_synthetic_identifiers=True,
    )
    assert verdict.ready is False
    assert "PROMOTION_FAILED" in verdict.blocker_codes


# ===========================================================================
# Objective D: LEG-EXEC Invalidation Notice Safety & Dry-Run Verification
# ===========================================================================


PINNED_PROPOSAL_SHA256 = "41cbbba3e9d587b9972c3baca1b39f09d478d408d9c60fd538c249c4600113d4"


def test_leg_exec_dry_run_on_repository_is_non_destructive_and_all_27_notices_verify() -> None:
    proposal_path = REPO_ROOT / "docs" / "PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json"
    reviews_root = REPO_ROOT / "data" / "ground_truth" / "reviews"

    proposal = load_and_verify_proposal(
        proposal_path,
        expected_sha256=PINNED_PROPOSAL_SHA256,
    )
    assert len(proposal["disposition_events"]) == 27

    # Non-destructive dry-run plan against data/ground_truth/reviews
    plan = plan_invalidation_notices(
        proposal,
        reviews_root=reviews_root,
    )
    assert len(plan.results) == 27
    assert all(
        r.status == "WOULD_SKIP_ALREADY_DONE_MATCHING" for r in plan.results
    )
    assert plan.directory_notice_result.status == "WOULD_SKIP_ALREADY_DONE_MATCHING"

    # Verify all 27 sibling notices on disk via notices.py
    statuses = scan_notices(reviews_root)
    assert len(statuses) == 27
    assert all(s.valid for s in statuses)
    assert invalid_notices(reviews_root) == []
    assert len(excused_legacy_records(reviews_root)) == 27


def test_invalidation_notice_writer_fails_closed_on_tampering_in_tmp_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    reviews_dir = tmp_path / "data" / "ground_truth" / "reviews"
    (reviews_dir / "train_events").mkdir(parents=True)
    rec_path = reviews_dir / "train_events" / "event_001_review.json"
    rec_bytes = b'{"schema_version": "7.0.0", "event_id": "event_001"}\n'
    rec_path.write_bytes(rec_bytes)
    rec_sha = hashlib.sha256(rec_bytes).hexdigest()

    proposal_payload = {
        "disposition_events": [
            {
                "event_id": "train_events/event_001",
                "affected_record_path": "data/ground_truth/reviews/train_events/event_001_review.json",
                "affected_record_sha256": rec_sha,
                "reason": "Synthetic test invalidation reason.",
                "at_utc": "2026-10-14T12:00:00Z",
                "actor": "sayem_uddin",
                "authorized_statement": "Test non-destructive invalidation in tmp_path.",
            }
        ],
    }
    prop_file = tmp_path / "proposal.json"
    prop_file.write_text(json.dumps(proposal_payload, indent=2), encoding="utf-8")
    prop_sha = hashlib.sha256(prop_file.read_bytes()).hexdigest()

    # 1. Wrong expected_sha256 fails closed
    with pytest.raises(ProposalBindingError, match="does not match the expected reviewed hash"):
        load_and_verify_proposal(prop_file, expected_sha256="0" * 64)

    # 2. Dry-run plans 1 notice without writing any files
    loaded_prop = load_and_verify_proposal(prop_file, expected_sha256=prop_sha)
    dry_plan = plan_invalidation_notices(
        loaded_prop,
        reviews_root=reviews_dir,
        expected_count=1,
    )
    assert dry_plan.results[0].status == "WOULD_WRITE"
    assert not (
        reviews_dir / "train_events" / "event_001_review.INVALIDATION_NOTICE.json"
    ).exists()

    # 3. Apply in tmp_path creates sibling notice and preserves original record byte-identical
    report = apply_invalidation_notices(
        loaded_prop,
        reviews_root=reviews_dir,
        expected_count=1,
    )
    assert report.results[0].status == "WRITTEN"
    assert rec_path.read_bytes() == rec_bytes

    # 4. Tampering with original record after notice creation causes scan_notices to fail closed
    rec_path.write_bytes(b'{"schema_version": "7.0.0", "event_id": "event_001", "tampered": true}\n')
    bad = invalid_notices(reviews_dir)
    assert len(bad) == 1
    assert "the record changed after the notice was written" in (bad[0].problem or "")

    # And plan_invalidation_notices reports WOULD_SKIP_TARGET_HASH_MISMATCH
    mismatch_plan = plan_invalidation_notices(
        loaded_prop,
        reviews_root=reviews_dir,
        expected_count=1,
    )
    assert mismatch_plan.results[0].status == "WOULD_SKIP_TARGET_HASH_MISMATCH"


# ===========================================================================
# Objective E: Stage-2.1 Review-to-Promotion Integrity Tests
# ===========================================================================


def test_allowlist_rejects_missing_empty_blocklisted_duplicate_and_revoked_entries(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "nonexistent.json"
    with pytest.raises(AuthorizedReviewersLoadError):
        load_authorized_reviewers(missing)

    empty_file = tmp_path / "empty.json"
    empty_file.write_text(json.dumps({"authorized_reviewers": []}), encoding="utf-8")
    with pytest.raises(AuthorizedReviewersLoadError):
        load_authorized_reviewers(empty_file)

    blocklisted_file = tmp_path / "blocklisted.json"
    blocklisted_file.write_text(
        json.dumps({"authorized_reviewers": ["human_annotator"]}), encoding="utf-8"
    )
    with pytest.raises(AuthorizedReviewersLoadError, match="blocklisted identifier"):
        load_authorized_reviewers(blocklisted_file)

    dup_file = tmp_path / "dup.json"
    dup_file.write_text(
        json.dumps({"authorized_reviewers": ["dr.a@buet.ac.bd", "dr.a@buet.ac.bd"]}),
        encoding="utf-8",
    )
    with pytest.raises(AuthorizedReviewersLoadError, match="duplicate"):
        load_authorized_reviewers(dup_file)

    revoked_overlap_file = tmp_path / "revoked.json"
    revoked_overlap_file.write_text(
        json.dumps(
            {
                "authorized_reviewers": ["dr.a@buet.ac.bd", "dr.b@buet.ac.bd"],
                "revoked_reviewers": ["dr.b@buet.ac.bd"],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(AuthorizedReviewersLoadError, match="revoked_reviewers"):
        load_authorized_reviewers(revoked_overlap_file)


def test_stage21_schema_rejects_short_duration_forged_duration_and_bad_history(
    tmp_path: Path,
) -> None:
    rec, _, _, _, _ = _make_stage21_fixture(tmp_path)

    # 1. Duration < 30.0s rejected even if caller supplies forged review_duration_s=999.0
    short_rec = copy.deepcopy(rec)
    short_rec["reviewer_metadata"]["review_start_utc"] = "2026-11-01T09:00:00Z"
    short_rec["reviewer_metadata"]["review_end_utc"] = "2026-11-01T09:00:29.900000Z"
    short_rec["reviewer_metadata"]["review_duration_s"] = 999.0
    with pytest.raises(SchemaValidationError, match="below the minimum plausible threshold"):
        build_stage2_1_record_from_dict(short_rec)

    # 2. Missing or short model independence attestation rejected
    no_attest = copy.deepcopy(rec)
    no_attest["model_independence_attestation"]["attested"] = False
    with pytest.raises(SchemaValidationError, match="attested must be true"):
        build_stage2_1_record_from_dict(no_attest)

    short_stmt = copy.deepcopy(rec)
    short_stmt["model_independence_attestation"]["statement"] = "ok"
    with pytest.raises(SchemaValidationError, match=">= 20 characters"):
        build_stage2_1_record_from_dict(short_stmt)

    # 3. Boundary state taxonomy violations rejected
    obs_no_val = copy.deepcopy(rec)
    obs_no_val["boundary_adjudications"]["T1_danger_zone_entry"]["value_s"] = None
    with pytest.raises(SchemaValidationError, match="value_s is required"):
        build_stage2_1_record_from_dict(obs_no_val)

    unobs_with_val = copy.deepcopy(rec)
    unobs_with_val["boundary_adjudications"]["T1_danger_zone_entry"] = {
        "state": "UNCERTAIN",
        "rationale": "Heavy rain obscured exact crossing line entry frame.",
        "value_s": 3.0,
        "reference_camera": "front",
        "frame_index": 15,
    }
    with pytest.raises(SchemaValidationError, match="value_s must be None"):
        build_stage2_1_record_from_dict(unobs_with_val)

    missing_boundary = copy.deepcopy(rec)
    missing_boundary["boundary_adjudications"].pop(CANONICAL_TIMESTAMPS[0])
    with pytest.raises(SchemaValidationError, match="missing required keys"):
        build_stage2_1_record_from_dict(missing_boundary)

    # 4. Duplicate adjudication_history entry rejected
    dup_hist = copy.deepcopy(rec)
    dup_hist["adjudication_history"].append(copy.deepcopy(dup_hist["adjudication_history"][0]))
    with pytest.raises(SchemaValidationError, match="duplicate entry"):
        build_stage2_1_record_from_dict(dup_hist)

    # 5. Blocklisted actor in adjudication_history rejected
    block_hist = copy.deepcopy(rec)
    block_hist["adjudication_history"][0]["by"] = "human_annotator"
    with pytest.raises(SchemaValidationError, match="blocklist"):
        build_stage2_1_record_from_dict(block_hist)

    # 6. Same reviewer claiming second_review step in adjudication_history rejected
    same_rev_hist = copy.deepcopy(rec)
    same_rev_hist["adjudication_history"] = [
        {
            "event": "initial_review",
            "by": "dr.rahman@buet.ac.bd",
            "at_utc": "2026-11-01T09:04:00Z",
            "status_set": "NEEDS_SECOND_REVIEW",
        },
        {
            "event": "second_review",
            "by": "dr.rahman@buet.ac.bd",
            "at_utc": "2026-11-01T09:10:00Z",
            "status_set": "APPROVED",
        },
    ]
    with pytest.raises(SchemaValidationError, match="independent second review requires a distinct reviewer"):
        build_stage2_1_record_from_dict(same_rev_hist)

    # 7. Self-referential second_review_of rejected
    self_sec = copy.deepcopy(rec)
    self_sec["second_review_of"] = self_sec["review_id"]
    with pytest.raises(SchemaValidationError, match="cannot reference the record's own review_id"):
        build_stage2_1_record_from_dict(self_sec)


def test_promotion_gate_and_receipt_detect_media_tampering_disputes_and_batch_collisions(
    tmp_path: Path,
) -> None:
    rec, proposals, registry, paths, allowlist_path = _make_stage21_fixture(tmp_path)
    authorized = load_authorized_reviewers(allowlist_path)

    # 1. Valid record passes promotion validation
    assert (
        validate_for_promotion(
            rec,
            active_proposal_sha256_by_event=proposals,
            media_sha256_registry=registry,
            authorized_reviewers=authorized,
            media_file_paths=paths,
        )
        == []
    )

    # 2. Tampering with live media file on disk triggers MEDIA_HASH_CHANGED_SINCE_REGISTRY & _SINCE_REVIEW
    front_file = Path(paths["event_001"]["front"])
    original_bytes = front_file.read_bytes()
    front_file.write_bytes(b"corrupted-live-media-bytes")
    media_violations = validate_for_promotion(
        rec,
        active_proposal_sha256_by_event=proposals,
        media_sha256_registry=registry,
        authorized_reviewers=authorized,
        media_file_paths=paths,
    )
    m_codes = {v.code for v in media_violations}
    assert "MEDIA_HASH_CHANGED_SINCE_REGISTRY" in m_codes
    assert "MEDIA_HASH_CHANGED_SINCE_REVIEW" in m_codes
    front_file.write_bytes(original_bytes)

    # 3. Unresolved status (DISPUTED / NEEDS_SECOND_REVIEW) rejected
    disputed_rec = copy.deepcopy(rec)
    disputed_rec["adjudication_status"] = "DISPUTED"
    disputed_rec["adjudication_history"][-1]["status_set"] = "DISPUTED"
    disp_violations = validate_for_promotion(
        disputed_rec,
        active_proposal_sha256_by_event=proposals,
        media_sha256_registry=registry,
        authorized_reviewers=authorized,
        media_file_paths=paths,
    )
    assert any(v.code == "UNRESOLVED_DISAGREEMENT" for v in disp_violations)

    # 4. Batch check detects same reviewer performing second_review_of across two records
    rec2 = copy.deepcopy(rec)
    rec2["review_id"] = "rev_second_001"
    rec2["second_review_of"] = rec["review_id"]
    rec2["reviewer_metadata"]["review_session_id"] = "session_real_002"
    rec2["reviewer_metadata"]["review_start_utc"] = "2026-11-01T09:10:00Z"
    rec2["reviewer_metadata"]["review_end_utc"] = "2026-11-01T09:15:00Z"
    batch_violations = validate_batch_for_promotion(
        [rec, rec2],
        active_proposal_sha256_by_event=proposals,
        media_sha256_registry=registry,
        authorized_reviewers=authorized,
        media_file_paths=paths,
    )
    assert any(v.code == "BATCH_SAME_REVIEWER_SECOND_REVIEW" for v in batch_violations)

    # 5. Promotion receipt verification detects tampered record / input hashes
    canon_dir = tmp_path / "canonical_out"
    promoted_path = promote_record(
        rec,
        output_dir=canon_dir,
        active_proposal_sha256_by_event=proposals,
        media_sha256_registry=registry,
        authorized_reviewers=authorized,
        media_file_paths=paths,
    )
    rec_sha = sha256_file(promoted_path)
    live_inputs = {
        "inventory_sha256": "1" * 64,
        "active_proposals_sha256": "2" * 64,
        "allowlist_sha256": "3" * 64,
    }
    receipt_payload: dict[str, Any] = {
        "schema_version": PROMOTION_RECEIPT_SCHEMA,
        "produced_by": PROMOTION_RECEIPT_PRODUCER,
        "produced_at_utc": "2026-11-01T09:30:00Z",
        "stage": "stage3_single_camera_baseline",
        "verdict": {"ready": True, "blocker_count": 0},
        "review_record_sha256": {"train_events/event_001_review.json": rec_sha},
        "inputs": live_inputs,
        "media_hashes_verified_live": True,
    }
    receipt_payload["receipt_sha256"] = receipt_body_sha256(receipt_payload)
    receipt_path = tmp_path / PROMOTION_RECEIPT_RELATIVE
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt_payload, indent=2), encoding="utf-8")

    verified_receipt = verify_promotion_receipt(
        tmp_path,
        review_record_sha256={"train_events/event_001_review.json": rec_sha},
        live_inputs=live_inputs,
    )
    assert verified_receipt.payload["stage"] == "stage3_single_camera_baseline"

    # Tamper with live record hash -> verify_promotion_receipt raises GovernanceError
    with pytest.raises(GovernanceError, match="review records differ from the receipt"):
        verify_promotion_receipt(
            tmp_path,
            review_record_sha256={"train_events/event_001_review.json": "f" * 64},
            live_inputs=live_inputs,
        )


# ===========================================================================
# Objective F & G: Controlled Cache Integration & Official Readiness Matrix
# ===========================================================================


def test_controlled_cache_integration_across_processor_and_preflight(
    tmp_path: Path,
) -> None:
    processor = LayerBEventProcessor(cache_dir=tmp_path)
    prov = processor.build_stream_provenance(
        cohort="train_events",
        event_id="event_001",
        source_id="camera_1",
        modality="vision",
        run_id="run_m4a_01",
    )
    records = [
        EvidenceRecord(
            timestamp_s=0.2,
            source_id="camera_1",
            modality=Modality.VISION,
            available=True,
            detections=(
                Detection(
                    label="train",
                    confidence=0.91,
                    bbox_xyxy=(15.0, 25.0, 210.0, 310.0),
                ),
            ),
            metadata={"frame_index": 1},
        )
    ]
    cache_file = write_controlled_cache_jsonl(tmp_path, prov, records)

    # Loading with different run_id under default CACHE_REUSE_ISOLATED_RUN fails closed
    other_run_prov = processor.build_stream_provenance(
        cohort="train_events",
        event_id="event_001",
        source_id="camera_1",
        modality="vision",
        run_id="run_m4a_02",
    )
    with pytest.raises(CacheProvenanceError) as exc_info:
        load_controlled_cache_jsonl(
            cache_file, other_run_prov, reuse_policy=CACHE_REUSE_ISOLATED_RUN
        )
    assert exc_info.value.code == "PROVENANCE_MISMATCH"

    # Prohibited Audio V2 hash rejected when constructing provenance
    with pytest.raises(CacheProvenanceError) as v2_exc:
        ControlledCacheProvenance(
            cohort="train_events",
            event_id="event_001",
            source_id="audio_1",
            modality="audio",
            model_architecture="Audio_V2_Legacy",
            checkpoint_sha256=PROHIBITED_AUDIO_V2_SHA256,
            preprocessing_config={"sample_rate_hz": 16000},
            experiment_config_sha256=processor.config.canonical_hash,
            failure_injector="none",
            injector_parameters={},
            timing_config={"tick_s": 0.2},
            cache_schema_version=CONTROLLED_CACHE_SCHEMA_VERSION,
            software_version="1.0.0-frozen",
            run_id="run_m4a_01",
        )
    assert v2_exc.value.code == "PROHIBITED_CHECKPOINT_REJECTED"


def test_official_phase12_readiness_and_execution_gate_fail_closed_on_repo() -> None:
    report = assess_official_phase12_readiness(REPO_ROOT)
    assert report.ready is False
    codes = set(report.blocker_codes)
    assert "STAGE21_RECORDS_MISSING" in codes
    assert "COHORT_APPROVAL_MISSING" in codes
    assert "PREMATURE_OPENING_DEFINITION_UNDECIDED" in codes
    assert "R04_SCOPE_DECISION_MISSING" in codes
    assert "EVENT_SPLIT_DECISION_MISSING" in codes
    assert "MANIFEST_MISSING" in codes
    assert "EVAL_AUTH_NOT_GRANTED" in codes

    runner = Phase12EvaluationRunner()
    with pytest.raises(EvaluationRefused):
        runner.run_official(repository_root=REPO_ROOT)
