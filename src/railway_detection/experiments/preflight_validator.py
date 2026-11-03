"""Experiment Configuration Reproducibility & Non-Authoritative Preflight Validator.

Implements Mission 3 Sections 5 and 6:
1. Explicit separation of the five configuration classes:
   - ``researcher_approved``
   - ``software_default``
   - ``historical_configuration``
   - ``unresolved_configuration``
   - ``synthetic_test_configuration``
2. Complete, reconstructable ``ExperimentConfigurationSpec`` for controlled runs
   across families ``B0``–``B8``.
3. Non-authoritative diagnostic preflight validator (``run_experiment_preflight``)
   that reports structural validity, missing configuration parameters, unresolved
   scientific decision dependencies (``D1``, ``D2``, ``D4``, ``B7e``), missing
   governance/human-review authorizations (Stage-2.1, promotion receipt, split,
   manifest, ``EVAL-AUTH``), and cache provenance incompatibilities.

Crucial Governance Invariant:
This module is strictly diagnostic and non-authoritative. It NEVER grants
``EVAL-AUTH``, NEVER promotes ground truth, NEVER accesses raw media, and NEVER
marks official evaluation ready.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from railway_detection.experiments.cache_provenance import (
    CACHE_REUSE_ISOLATED_RUN,
    CONTROLLED_CACHE_SCHEMA_VERSION,
    PROHIBITED_AUDIO_V2_PATH_SUFFIXES,
    PROHIBITED_AUDIO_V2_SHA256,
    VALID_CACHE_REUSE_POLICIES,
    VALID_EXPERIMENT_FAMILIES,
    VALID_FAILURE_INJECTORS,
    CacheProvenanceError,
    ControlledCacheProvenance,
    _validate_injector_contract,
    build_audio_preprocessing_config,
    build_vision_preprocessing_config,
    canonicalize_config,
    compute_canonical_digest,
    load_controlled_cache_jsonl,
)
from railway_detection.experiments.frozen_config import FrozenExperimentConfig

# ---------------------------------------------------------------------------
# Section 5.2: Explicit Configuration Classes
# ---------------------------------------------------------------------------

CONFIG_CLASS_RESEARCHER_APPROVED = "researcher_approved"
CONFIG_CLASS_SOFTWARE_DEFAULT = "software_default"
CONFIG_CLASS_HISTORICAL = "historical_configuration"
CONFIG_CLASS_UNRESOLVED = "unresolved_configuration"
CONFIG_CLASS_SYNTHETIC_TEST = "synthetic_test_configuration"

CONFIGURATION_CLASSES = frozenset(
    {
        CONFIG_CLASS_RESEARCHER_APPROVED,
        CONFIG_CLASS_SOFTWARE_DEFAULT,
        CONFIG_CLASS_HISTORICAL,
        CONFIG_CLASS_UNRESOLVED,
        CONFIG_CLASS_SYNTHETIC_TEST,
    }
)

VALID_EVALUATION_MODES = frozenset(
    {
        "provisional_exploratory",
        "descriptive_only",
        "official_evaluation",
        "synthetic_verification",
    }
)

# ---------------------------------------------------------------------------
# Mission 4A Section 4: Canonical Research Decision Register & Statuses
# ---------------------------------------------------------------------------

DECISION_STATUS_APPROVED = "APPROVED_BY_RESEARCHER"
DECISION_STATUS_PENDING = "PENDING_RESEARCHER_DECISION"
DECISION_STATUS_RECOMMENDATION_ONLY = "TECHNICAL_RECOMMENDATION_ONLY"
DECISION_STATUS_IMPLEMENTED_NOT_APPROVED = "IMPLEMENTED_BUT_NOT_SCIENTIFICALLY_APPROVED"
DECISION_STATUS_SUPERSEDED = "SUPERSEDED_WITH_EXPLICIT_RECORD"
DECISION_STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"

DECISION_STATUSES = frozenset(
    {
        DECISION_STATUS_APPROVED,
        DECISION_STATUS_PENDING,
        DECISION_STATUS_RECOMMENDATION_ONLY,
        DECISION_STATUS_IMPLEMENTED_NOT_APPROVED,
        DECISION_STATUS_SUPERSEDED,
        DECISION_STATUS_NOT_APPLICABLE,
    }
)


@dataclass(frozen=True)
class DecisionRegisterEntry:
    """Authoritative governance record for a scientific, protocol, or experimental decision."""

    canonical_id: str
    historical_id: str
    title: str
    status: str
    approval_date_or_state: str
    authoritative_documents: tuple[str, ...]
    code_bindings: tuple[str, ...]
    technical_recommendation_status: str
    notes: str

    def __post_init__(self) -> None:
        if self.status not in DECISION_STATUSES:
            raise ValueError(
                f"Invalid decision status {self.status!r}; must be one of {sorted(DECISION_STATUSES)}"
            )
        if self.technical_recommendation_status not in DECISION_STATUSES:
            raise ValueError(
                f"Invalid technical_recommendation_status {self.technical_recommendation_status!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "historical_id": self.historical_id,
            "title": self.title,
            "status": self.status,
            "approval_date_or_state": self.approval_date_or_state,
            "authoritative_documents": list(self.authoritative_documents),
            "code_bindings": list(self.code_bindings),
            "technical_recommendation_status": self.technical_recommendation_status,
            "notes": self.notes,
        }


CANONICAL_DECISION_REGISTER: dict[str, DecisionRegisterEntry] = {
    "GOV-D1-PROTOCOL-AUTHORITY": DecisionRegisterEntry(
        canonical_id="GOV-D1-PROTOCOL-AUTHORITY",
        historical_id="D1",
        title="Protocol and Ground-Truth Authority (v8.0.0/v6.0.0 vs v9.0.0/v7.0.0)",
        status=DECISION_STATUS_PENDING,
        approval_date_or_state="UNDECIDED (Pending Researcher Sign-Off)",
        authoritative_documents=(
            "docs/generated/RESEARCHER_MINIMUM_REQUIRED_DECISIONS_20261029.md",
            "docs/generated/PROTOCOL_AUTHORITY_COMPARISON_20261030.md",
            "docs/generated/RESEARCHER_DECISIONS_REQUIRED_20261030_R1.md",
            "docs/generated/RESEARCHER_DECISION_PACKET_20261030_R1.md",
            "docs/generated/RESEARCHER_DECISION_REGISTER_20261101_M2.md",
        ),
        code_bindings=(
            "src/railway_detection/research_contracts.py",
            "src/railway_detection/annotation/stage2_1_schema.py",
        ),
        technical_recommendation_status=DECISION_STATUS_RECOMMENDATION_ONLY,
        notes=(
            "Historical Decision D1: Choose between committed HEAD protocol v8.0.0 / GT v6.0.0 "
            "and worktree protocol v9.0.0 / GT v7.0.0 with Stage-2.1 2.1.0 remediation. "
            "Option B (v9.0.0/v7.0.0 + Stage-2.1 2.1.0) is TECHNICAL_RECOMMENDATION_ONLY."
        ),
    ),
    "GOV-D2-EVALUATION-PROFILE": DecisionRegisterEntry(
        canonical_id="GOV-D2-EVALUATION-PROFILE",
        historical_id="D2",
        title="Premature-Opening Evaluation Profile (M4 first_blocked vs v9 t1_entry)",
        status=DECISION_STATUS_PENDING,
        approval_date_or_state="UNDECIDED (Blocked in research_contracts.yaml & governance.py)",
        authoritative_documents=(
            "configs/research_contracts.yaml",
            "docs/generated/M4_V9_EVALUATION_PROFILE_COMPARISON_20261030.md",
            "docs/generated/RESEARCHER_DECISIONS_REQUIRED_20261030_R1.md",
            "docs/generated/RESEARCHER_DECISION_PACKET_20261030_R1.md",
            "docs/generated/RESEARCHER_DECISION_REGISTER_20261101_M2.md",
        ),
        code_bindings=(
            "src/railway_detection/research_contracts.py",
            "src/railway_detection/evaluation/governance.py",
            "src/railway_detection/evaluation/metrics.py",
        ),
        technical_recommendation_status=DECISION_STATUS_RECOMMENDATION_ONLY,
        notes=(
            "Historical Decision D2: Choose between M4 (first_blocked_to_t4_clearance) and "
            "v9 (t1_entry_to_t4_clearance) premature-opening window definition. Enforced "
            "fail-closed by PREMATURE_OPENING_DEFINITION_UNDECIDED in governance.py."
        ),
    ),
    "GOV-D3-DESCRIPTIVE-MODE": DecisionRegisterEntry(
        canonical_id="GOV-D3-DESCRIPTIVE-MODE",
        historical_id="D3",
        title="Descriptive-Only Evaluation Mode Isolation (full_cohort_descriptive)",
        status=DECISION_STATUS_APPROVED,
        approval_date_or_state="APPROVED 2026-10-30",
        authoritative_documents=(
            "docs/generated/DESCRIPTIVE_VS_OFFICIAL_EVALUATION_DECISION_20261030.md",
            "docs/generated/RESEARCHER_DECISIONS_REQUIRED_20261030_R1.md",
            "docs/generated/RESEARCHER_DECISION_REGISTER_20261101_M2.md",
        ),
        code_bindings=(
            "src/railway_detection/evaluation/descriptive_only.py",
            "src/railway_detection/evaluation/execution_gate.py",
        ),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes=(
            "Approved 2026-10-30: Full-cohort descriptive aggregation is permitted strictly "
            "through aggregate_descriptive_only with official_evaluation_eligible=False and "
            "cannot enter official Phase 12 confirmatory evaluation."
        ),
    ),
    "AUTH-EVENT-SPLIT": DecisionRegisterEntry(
        canonical_id="AUTH-EVENT-SPLIT",
        historical_id="D3_CONFIRMATORY_SPLIT",
        title="Official Locked Phase 12 Event Split (train/val/test)",
        status=DECISION_STATUS_PENDING,
        approval_date_or_state="ABSENT (data/splits/phase12_event_split_decision.json missing)",
        authoritative_documents=(
            "docs/generated/DESCRIPTIVE_VS_OFFICIAL_EVALUATION_DECISION_20261030.md",
            "docs/generated/RESEARCHER_DECISION_REGISTER_20261101_M2.md",
        ),
        code_bindings=(
            "src/railway_detection/evaluation/governance.py",
            "src/railway_detection/evaluation/execution_gate.py",
        ),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes=(
            "Official confirmatory Phase 12 evaluation requires a locked, researcher-signed "
            "event split at data/splits/phase12_event_split_decision.json (checked by "
            "EVENT_SPLIT_DECISION_MISSING in governance.py)."
        ),
    ),
    "GOV-D4-R04-SYNCHRONIZATION": DecisionRegisterEntry(
        canonical_id="GOV-D4-R04-SYNCHRONIZATION",
        historical_id="D4",
        title="R04 Camera Synchronization Scope and Acceptance Criteria",
        status=DECISION_STATUS_PENDING,
        approval_date_or_state="UNDECIDED (data/manifests/phase12_r04_scope_decision.json missing)",
        authoritative_documents=(
            "data/manifests/camera_sync_offsets_candidate.yaml",
            "docs/generated/R04_CAMERA_SYNCHRONIZATION_DECISION_20261030.md",
            "docs/generated/RESEARCHER_DECISIONS_REQUIRED_20261030_R1.md",
            "docs/generated/RESEARCHER_DECISION_PACKET_20261030_R1.md",
            "docs/generated/RESEARCHER_DECISION_REGISTER_20261101_M2.md",
        ),
        code_bindings=(
            "src/railway_detection/evaluation/governance.py",
            "src/railway_detection/evaluation/execution_gate.py",
            "src/railway_detection/fusion/collector.py",
            "src/railway_detection/fusion/sync.py",
        ),
        technical_recommendation_status=DECISION_STATUS_RECOMMENDATION_ONLY,
        notes=(
            "Historical Decision D4: Candidate offsets classify 27 events into 12 CALIBRATION_SUPPORTED, "
            "7 PROVISIONAL, and 8 AMBIGUOUS. Option 1 (Conservative 12-event subset for dual-camera claims) "
            "is TECHNICAL_RECOMMENDATION_ONLY; enforced fail-closed by R04_SCOPE_DECISION_MISSING."
        ),
    ),
    "GOV-B7D-DELIVERY-DISORDER": DecisionRegisterEntry(
        canonical_id="GOV-B7D-DELIVERY-DISORDER",
        historical_id="B7d",
        title="B7d Out-of-Order Frame Delivery Perturbation Semantics",
        status=DECISION_STATUS_APPROVED,
        approval_date_or_state="APPROVED 2026-10-30",
        authoritative_documents=(
            "docs/generated/B7D_B7E_PERTURBATION_CONTRACTS_20261030.md",
            "docs/generated/RESEARCHER_DECISIONS_REQUIRED_20261030_R1.md",
            "docs/generated/RESEARCHER_DECISION_REGISTER_20261101_M2.md",
        ),
        code_bindings=(
            "src/railway_detection/simulation/failure_injector.py",
            "src/railway_detection/simulation/runner.py",
            "src/railway_detection/fusion/collector.py",
        ),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes=(
            "Approved 2026-10-30: B7d perturbs delivery arrival order (received_timestamp_s) "
            "before collector ingestion while preserving original frame_timestamp_s."
        ),
    ),
    "GOV-B7E-MECHANISM": DecisionRegisterEntry(
        canonical_id="GOV-B7E-MECHANISM",
        historical_id="B7e_MECHANISM",
        title="B7e Delayed Frame Timestamps Staleness Detection Mechanism",
        status=DECISION_STATUS_APPROVED,
        approval_date_or_state="APPROVED 2026-10-30",
        authoritative_documents=(
            "docs/generated/B7D_B7E_PERTURBATION_CONTRACTS_20261030.md",
            "docs/generated/RESEARCHER_DECISIONS_REQUIRED_20261030_R1.md",
            "docs/generated/RESEARCHER_DECISION_REGISTER_20261101_M2.md",
        ),
        code_bindings=(
            "src/railway_detection/simulation/failure_injector.py",
            "src/railway_detection/simulation/runner.py",
            "src/railway_detection/fusion/collector.py",
        ),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes=(
            "Approved 2026-10-30: Staleness is evaluated via received_timestamp_s - frame_timestamp_s > "
            "source_staleness_s, and B7e fails closed when delay_s or target_source is omitted."
        ),
    ),
    "EXP-B7E-PARAMETERS": DecisionRegisterEntry(
        canonical_id="EXP-B7E-PARAMETERS",
        historical_id="B7e_PARAMETERS",
        title="B7e Numerical Delay Parameters (delay_s, target_source) and Acceptance Criteria",
        status=DECISION_STATUS_PENDING,
        approval_date_or_state="UNDECIDED (Fails closed without explicit parameters)",
        authoritative_documents=(
            "docs/generated/B7D_B7E_PERTURBATION_CONTRACTS_20261030.md",
            "docs/generated/RESEARCHER_DECISIONS_REQUIRED_20261030_R1.md",
            "docs/generated/RESEARCHER_DECISION_REGISTER_20261101_M2.md",
        ),
        code_bindings=(
            "src/railway_detection/simulation/failure_injector.py",
            "src/railway_detection/experiments/cache_provenance.py",
            "src/railway_detection/experiments/preflight_validator.py",
        ),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes=(
            "Numerical delay_s (> source_staleness_s = 2.0s), target_source, and fault acceptance "
            "criteria remain pending researcher decision."
        ),
    ),
    "GOV-GT-STATE-SEPARATION": DecisionRegisterEntry(
        canonical_id="GOV-GT-STATE-SEPARATION",
        historical_id="GT_SEPARATION",
        title="Ground-Truth State Separation (TRAIN_EVENT vs NEGATIVE_CONTROL vs ENGINE_INSPECTION)",
        status=DECISION_STATUS_APPROVED,
        approval_date_or_state="APPROVED 2026-10-30",
        authoritative_documents=(
            "docs/generated/RESEARCHER_DECISIONS_REQUIRED_20261030_R1.md",
            "docs/generated/RESEARCHER_DECISION_REGISTER_20261101_M2.md",
        ),
        code_bindings=(
            "src/railway_detection/evaluation/metrics.py",
            "src/railway_detection/evaluation/clock_aware.py",
        ),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes=(
            "Approved 2026-10-30: Explicit 4-state ground-truth classification prevents missing "
            "T1/T4 labels from collapsing into negative-control state."
        ),
    ),
    "GOV-ENGINE-EVENT-ISOLATION": DecisionRegisterEntry(
        canonical_id="GOV-ENGINE-EVENT-ISOLATION",
        historical_id="ENGINE_ISOLATION",
        title="Engine-Event Denominator Isolation (Single Case Study engine_events/event_001)",
        status=DECISION_STATUS_APPROVED,
        approval_date_or_state="APPROVED 2026-10-30",
        authoritative_documents=(
            "data/manifests/layer_b_v2_annotation_inventory.json",
            "docs/generated/RESEARCHER_DECISIONS_REQUIRED_20261030_R1.md",
            "docs/generated/RESEARCHER_DECISION_REGISTER_20261101_M2.md",
        ),
        code_bindings=(
            "src/railway_detection/evaluation/metrics.py",
            "src/railway_detection/evaluation/descriptive_only.py",
            "src/railway_detection/experiments/runner.py",
        ),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes=(
            "Approved 2026-10-30: The repository's single engine event (engine_events/event_001) "
            "is excluded from train sensitivity and negative-control FAR denominators and reported "
            "in an isolated engine_case_study_report section."
        ),
    ),
    "GOV-LEG-EXEC-INVALIDATION": DecisionRegisterEntry(
        canonical_id="GOV-LEG-EXEC-INVALIDATION",
        historical_id="LEG_EXEC",
        title="Full-Scope Non-Destructive Legacy Review Invalidation (27 Sibling Notices)",
        status=DECISION_STATUS_APPROVED,
        approval_date_or_state="APPROVED 2026-10-14 (Executed 2026-10-17T07:44:53Z)",
        authoritative_documents=(
            "docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json",
            "docs/PHASE11_6E_LEGACY_DISPOSITION_EXECUTION_REPORT.md",
            "docs/generated/LEG_EXEC_OPERATION_REPORT.json",
            "docs/LEGACY_REVIEW_RECONCILIATION.json",
        ),
        code_bindings=(
            "src/railway_detection/annotation/invalidation_notice_writer.py",
            "src/railway_detection/annotation/notices.py",
        ),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes=(
            "Approved 2026-10-14 and executed 2026-10-17T07:44:53Z: All 27 legacy review records "
            "have verified sibling *.INVALIDATION_NOTICE.json files and _INTEGRITY_NOTICE.md "
            "while preserving all 27 original *_review.json files byte-identical."
        ),
    ),
    "GOV-STAGE21-SAFEGUARDS": DecisionRegisterEntry(
        canonical_id="GOV-STAGE21-SAFEGUARDS",
        historical_id="STAGE21_SAFEGUARDS",
        title="Stage-2.1 Review & Promotion Integrity Safeguards (Phase 11.7 Decisions 1-4)",
        status=DECISION_STATUS_APPROVED,
        approval_date_or_state="APPROVED 2026-10-15",
        authoritative_documents=(
            "docs/PHASE11_GROUND_TRUTH_PROTOCOL.md",
            "docs/PHASE11_6G_EVALUATION_READINESS_REASSESSMENT.md",
        ),
        code_bindings=(
            "src/railway_detection/annotation/stage2_1_schema.py",
            "src/railway_detection/annotation/promotion_gate.py",
            "src/railway_detection/annotation/evaluation_readiness_gate.py",
            "src/railway_detection/annotation/adjudication_session.py",
        ),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes=(
            "Approved 2026-10-15: Enforces 30.0s minimum review duration, mandatory external "
            "authorized_reviewers.json allowlist, promotion-time live media SHA-256 verification, "
            "4-state boundary taxonomy, append-only history, and synthetic ID isolation."
        ),
    ),
    "EXP-OPERATING-THRESHOLDS": DecisionRegisterEntry(
        canonical_id="EXP-OPERATING-THRESHOLDS",
        historical_id="EXP_THRESHOLDS",
        title="Vision & Audio Operating Thresholds and Multimodal Fusion Weights",
        status=DECISION_STATUS_IMPLEMENTED_NOT_APPROVED,
        approval_date_or_state="PROVISIONAL_IMPLEMENTED (Pending Researcher Calibration Freeze)",
        authoritative_documents=(
            "configs/frozen_experiment_v1.yaml",
            "docs/generated/EXPERIMENT_CONFIGURATION_REPRODUCIBILITY_20261101_M3.md",
        ),
        code_bindings=(
            "src/railway_detection/experiments/frozen_config.py",
            "src/railway_detection/experiments/preflight_validator.py",
        ),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes=(
            "Configured in configs/frozen_experiment_v1.yaml (vision approach=0.35, departure=0.25, "
            "audio=0.2966) for exploratory/diagnostic runs, but not scientifically approved as "
            "calibrated constants for official Phase 12 claims. Reconciled in Mission 4A to "
            "eliminate collision with GOV-D1-PROTOCOL-AUTHORITY."
        ),
    ),
    "EXP-ROI-GEOMETRY": DecisionRegisterEntry(
        canonical_id="EXP-ROI-GEOMETRY",
        historical_id="EXP_ROI",
        title="Danger-Zone ROI Polygon Geometry and Camera Calibration Acceptance",
        status=DECISION_STATUS_PENDING,
        approval_date_or_state="UNDECIDED (Pending Researcher Calibration & ROI Sign-Off)",
        authoritative_documents=(
            "configs/frozen_experiment_v1.yaml",
            "docs/generated/EXPERIMENT_CONFIGURATION_REPRODUCIBILITY_20261101_M3.md",
        ),
        code_bindings=(
            "src/railway_detection/experiments/cache_provenance.py",
            "src/railway_detection/experiments/preflight_validator.py",
        ),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes=(
            "Explicit danger-zone ROI polygon geometry and camera calibration acceptance remain "
            "pending researcher sign-off. Reconciled in Mission 4A to eliminate collision with "
            "GOV-D2-EVALUATION-PROFILE."
        ),
    ),
    "AUTH-STAGE21-ADJUDICATION": DecisionRegisterEntry(
        canonical_id="AUTH-STAGE21-ADJUDICATION",
        historical_id="STAGE21_ADJUDICATION",
        title="Stage-2.1 Independent Human Ground-Truth Review & Promotion (27 Events)",
        status=DECISION_STATUS_PENDING,
        approval_date_or_state="NOT_STARTED (0/27 events adjudicated; canonical/ empty)",
        authoritative_documents=(
            "docs/generated/STAGE21_REVIEW_QUEUE.json",
            "docs/PHASE11_6G_EVALUATION_READINESS_REASSESSMENT.md",
        ),
        code_bindings=(
            "src/railway_detection/annotation/review_session.py",
            "src/railway_detection/annotation/promotion_gate.py",
            "src/railway_detection/annotation/receipt.py",
        ),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes=(
            "All 27 events (23 train_events, 3 no_train_events, 1 engine_events) require "
            "real human Stage-2.1 review and canonical promotion with receipt."
        ),
    ),
    "AUTH-EVAL-AUTH": DecisionRegisterEntry(
        canonical_id="AUTH-EVAL-AUTH",
        historical_id="EVAL_AUTH",
        title="Explicit Researcher Phase 12 Evaluation Authorization (EVAL-AUTH)",
        status=DECISION_STATUS_PENDING,
        approval_date_or_state="NOT_GRANTED (docs/PHASE12_EVALUATION_AUTHORIZATION.json absent)",
        authoritative_documents=(
            "docs/PHASE11_6G_EVALUATION_READINESS_REASSESSMENT.md",
            "docs/generated/RESEARCHER_DECISION_REGISTER_20261101_M2.md",
        ),
        code_bindings=(
            "src/railway_detection/evaluation/governance.py",
            "src/railway_detection/evaluation/execution_gate.py",
            "src/railway_detection/evaluation/evaluation_runner.py",
        ),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes=(
            "Final human researcher signature granting permission to execute official Phase 12 "
            "evaluation after all mechanical and scientific prerequisites are satisfied."
        ),
    ),
    "GOV-REVIEW-SECOND-REVIEW-TRIGGERS": DecisionRegisterEntry(
        canonical_id="GOV-REVIEW-SECOND-REVIEW-TRIGGERS",
        historical_id="D3A",
        title="Stage-2.1 Second-Review Trigger Policy (formerly D3(a))",
        status=DECISION_STATUS_PENDING,
        approval_date_or_state=(
            "FORMAL APPROVAL PENDING (researcher direction RD-043: risk-based mandatory triggers; "
            "no approval artifact)"
        ),
        authoritative_documents=(
            "docs/generated/GOV_D3A_SECOND_REVIEW_POLICY_RECOMMENDATION_20261101_M4E.md",
            "docs/generated/MISSION_4E4_DECISION_DISCOVERY_REPORT_20261101.md",
        ),
        code_bindings=("src/railway_detection/annotation/stage2_1_schema.py",),
        technical_recommendation_status=DECISION_STATUS_RECOMMENDATION_ONLY,
        notes=(
            "Register identifier added by Mission 5A (TF-05) so the pending policy is traceable. "
            "Previously 'D3(a)'; renamed to avoid collision with the approved descriptive-only "
            "mode (GOV-D3-DESCRIPTIVE-MODE). Not an approval."
        ),
    ),
    "GOV-REVIEW-CLEAR-BOUNDARY-AUDIT": DecisionRegisterEntry(
        canonical_id="GOV-REVIEW-CLEAR-BOUNDARY-AUDIT",
        historical_id="D3C",
        title="Stage-2.1 Clear-Boundary Audit Mechanism (formerly D3(c))",
        status=DECISION_STATUS_PENDING,
        approval_date_or_state=(
            "FORMAL APPROVAL PENDING (researcher direction RD-044: risk-based audit, no fixed "
            "percentage; no approval artifact)"
        ),
        authoritative_documents=(
            "docs/generated/GOV_D3C_CLEAR_BOUNDARY_AUDIT_RECOMMENDATION_20261101_M4E.md",
            "docs/generated/MISSION_4E4_DECISION_DISCOVERY_REPORT_20261101.md",
        ),
        code_bindings=("src/railway_detection/annotation/stage2_1_schema.py",),
        technical_recommendation_status=DECISION_STATUS_RECOMMENDATION_ONLY,
        notes="Register identifier added by Mission 5A (TF-05). Not an approval.",
    ),
    "AUTH-PILOT-EXEC": DecisionRegisterEntry(
        canonical_id="AUTH-PILOT-EXEC",
        historical_id="PILOT_EXEC",
        title="Stage-2.1 Human-Review Timing Pilot Execution Authorization",
        status=DECISION_STATUS_PENDING,
        approval_date_or_state="NOT_AUTHORIZED (authorization sheet blank; no artifact)",
        authoritative_documents=(
            "docs/generated/THREE_EVENT_PILOT_AUTHORIZATION_SHEET_20261101_M4C.md",
        ),
        code_bindings=("src/railway_detection/annotation/stage21_timing_pilot.py",),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes="Register identifier added by Mission 5A (TF-05). No pilot is authorized.",
    ),
    "AUTH-PROMOTE-EXEC": DecisionRegisterEntry(
        canonical_id="AUTH-PROMOTE-EXEC",
        historical_id="PROMOTE_EXEC",
        title="Ground-Truth Promotion and Promotion-Receipt Authorization",
        status=DECISION_STATUS_PENDING,
        approval_date_or_state=(
            "NOT_AUTHORIZED (data/governance/stage21_promotion_receipt.json absent)"
        ),
        authoritative_documents=(
            "docs/generated/STAGE21_REVIEW_PROMOTION_INTEGRITY_20261101_M4A.md",
        ),
        code_bindings=("src/railway_detection/annotation/promotion_gate.py",),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes="Register identifier added by Mission 5A (TF-05). No promotion is authorized.",
    ),
    "AUTH-MEDIA-ACCESS": DecisionRegisterEntry(
        canonical_id="AUTH-MEDIA-ACCESS",
        historical_id="MEDIA_ACCESS",
        title="Administrative Authorization for Decoupled Raw Media Access",
        status=DECISION_STATUS_PENDING,
        approval_date_or_state=(
            "NOT_GRANTED (data/governance/AUTH-MEDIA-ACCESS.json absent)"
        ),
        authoritative_documents=(
            "docs/generated/phase5/WP_5_0_EXECUTION_READINESS_AUDIT.md",
        ),
        code_bindings=("src/railway_detection/safety/media_guard.py",),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes="Required for raw audio/video decoding, frame extraction, or real inference.",
    ),
    "AUTH-DESCRIPTIVE-EVAL-EXEC": DecisionRegisterEntry(
        canonical_id="AUTH-DESCRIPTIVE-EVAL-EXEC",
        historical_id="DESCRIPTIVE_EVAL_EXEC",
        title="Explicit Researcher Descriptive Evaluation Execution Authorization",
        status=DECISION_STATUS_PENDING,
        approval_date_or_state=(
            "NOT_GRANTED (data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json absent)"
        ),
        authoritative_documents=(
            "docs/generated/phase5/WP_5_0_EXECUTION_READINESS_AUDIT.md",
        ),
        code_bindings=("src/railway_detection/evaluation/descriptive_exec_gate.py",),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes="Required for descriptive evaluation execution on real-data cohorts.",
    ),
    "M3-OVERLOADED-D1-D2-LABELS": DecisionRegisterEntry(
        canonical_id="M3-OVERLOADED-D1-D2-LABELS",
        historical_id="M3_D1_D2_OVERLOAD",
        title="Mission 3 Overloaded D1/D2 Shorthand Labels for Thresholds and ROI Geometry",
        status=DECISION_STATUS_SUPERSEDED,
        approval_date_or_state="SUPERSEDED 2026-11-01 (Mission 4A Reconciliation)",
        authoritative_documents=(
            "docs/generated/GOVERNANCE_DECISION_RECONCILIATION_20261101_M4A.md",
        ),
        code_bindings=("src/railway_detection/experiments/preflight_validator.py",),
        technical_recommendation_status=DECISION_STATUS_NOT_APPLICABLE,
        notes=(
            "Mission 3 temporarily overloaded D1 (for operating thresholds) and D2 (for ROI "
            "geometry). Superseded in Mission 4A by EXP-OPERATING-THRESHOLDS and EXP-ROI-GEOMETRY "
            "so D1 and D2 strictly denote GOV-D1-PROTOCOL-AUTHORITY and GOV-D2-EVALUATION-PROFILE."
        ),
    ),
}

HISTORICAL_DECISION_ALIASES: dict[str, str] = {
    "D1": "GOV-D1-PROTOCOL-AUTHORITY",
    "D2": "GOV-D2-EVALUATION-PROFILE",
    "D3": "GOV-D3-DESCRIPTIVE-MODE",
    "D3_SPLIT": "AUTH-EVENT-SPLIT",
    "D4": "GOV-D4-R04-SYNCHRONIZATION",
    "B7d": "GOV-B7D-DELIVERY-DISORDER",
    "B7e": "GOV-B7E-MECHANISM",
    "B7e_PARAMETERS": "EXP-B7E-PARAMETERS",
    "GT_SEPARATION": "GOV-GT-STATE-SEPARATION",
    "ENGINE_ISOLATION": "GOV-ENGINE-EVENT-ISOLATION",
    "LEG_EXEC": "GOV-LEG-EXEC-INVALIDATION",
    "STAGE21_SAFEGUARDS": "GOV-STAGE21-SAFEGUARDS",
    "EVAL_AUTH": "AUTH-EVAL-AUTH",
    "AUTH-EVAL-OFFICIAL": "AUTH-EVAL-AUTH",  # spelling used in the Mission 4E decision sheet
    "D3A": "GOV-REVIEW-SECOND-REVIEW-TRIGGERS",
    "D3C": "GOV-REVIEW-CLEAR-BOUNDARY-AUDIT",
    "PILOT_EXEC": "AUTH-PILOT-EXEC",
    "PROMOTE_EXEC": "AUTH-PROMOTE-EXEC",
    "MEDIA_ACCESS": "AUTH-MEDIA-ACCESS",
    "AUTH-MEDIA-ACCESS": "AUTH-MEDIA-ACCESS",
    "DESCRIPTIVE_EVAL_EXEC": "AUTH-DESCRIPTIVE-EVAL-EXEC",
    "AUTH-DESCRIPTIVE-EVAL-EXEC": "AUTH-DESCRIPTIVE-EVAL-EXEC",
}


def lookup_decision_register(decision_id: str) -> DecisionRegisterEntry:
    """Resolve either a canonical ID or a historical shorthand ID to its register entry."""
    key = decision_id.strip()
    if key in CANONICAL_DECISION_REGISTER:
        return CANONICAL_DECISION_REGISTER[key]
    if key in HISTORICAL_DECISION_ALIASES:
        return CANONICAL_DECISION_REGISTER[HISTORICAL_DECISION_ALIASES[key]]
    raise KeyError(
        f"Unknown decision identifier {decision_id!r}; expected one of "
        f"{sorted(set(CANONICAL_DECISION_REGISTER) | set(HISTORICAL_DECISION_ALIASES))}"
    )


@dataclass(frozen=True)
class ParameterClassification:
    """Explicit classification of an experiment parameter or subsystem contract."""

    parameter_key: str
    classification: str
    value_summary: Any
    decision_reference: str
    notes: str

    def __post_init__(self) -> None:
        if self.classification not in CONFIGURATION_CLASSES:
            raise ValueError(
                f"Invalid configuration classification {self.classification!r}; "
                f"must be one of {sorted(CONFIGURATION_CLASSES)}"
            )
        object.__setattr__(
            self, "value_summary", canonicalize_config(self.value_summary, "value_summary")
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter_key": self.parameter_key,
            "classification": self.classification,
            "value_summary": copy.deepcopy(self.value_summary),
            "decision_reference": self.decision_reference,
            "notes": self.notes,
        }


def classify_experiment_parameters(
    config: FrozenExperimentConfig,
    *,
    experiment_family: str = "B1",
    failure_injector: str = "none",
    injector_parameters: Mapping[str, Any] | None = None,
    roi_config: Mapping[str, Any] | None = None,
    is_synthetic_test: bool = False,
    is_historical: bool = False,
    d1_approved: bool = False,
    d2_approved: bool = False,
    d4_approved: bool = False,
    protocol_authority_d1_approved: bool | None = None,
    evaluation_profile_d2_approved: bool | None = None,
    operating_thresholds_approved: bool | None = None,
    roi_geometry_approved: bool | None = None,
    b7e_parameters_approved: bool = False,
) -> tuple[ParameterClassification, ...]:
    """Classify every parameter domain into one of the 5 explicit configuration classes.

    Never labels ``software_default`` or ``unresolved_configuration`` as
    ``researcher_approved``. Reconciled in Mission 4A so historical D1
    (``GOV-D1-PROTOCOL-AUTHORITY``) and D2 (``GOV-D2-EVALUATION-PROFILE``) are
    never conflated with experimental operating thresholds
    (``EXP-OPERATING-THRESHOLDS``) or ROI geometry (``EXP-ROI-GEOMETRY``).

    Mission 4D: Parameter presence alone never grants approval. The
    ``d1_approved``/``d2_approved`` legacy flags no longer implicitly propagate
    to threshold/ROI approval. B7e numerical parameters require an explicit
    ``b7e_parameters_approved=True`` flag, not mere presence.
    """
    eff_d1_protocol = d1_approved if protocol_authority_d1_approved is None else protocol_authority_d1_approved
    eff_d2_profile = d2_approved if evaluation_profile_d2_approved is None else evaluation_profile_d2_approved
    eff_thresholds = operating_thresholds_approved if operating_thresholds_approved is not None else False
    eff_roi = roi_geometry_approved if roi_geometry_approved is not None else False
    inj_params = dict(injector_parameters or {})
    if is_historical:
        return (
            ParameterClassification(
                parameter_key="overall_run_profile",
                classification=CONFIG_CLASS_HISTORICAL,
                value_summary={
                    "name": config.experiment.name,
                    "version": config.experiment.version,
                },
                decision_reference="HISTORICAL_DIAGNOSTIC_UNVERIFIED",
                notes="Historical diagnostic configuration prior to complete provenance & Stage-2.1.",
            ),
        )

    classifications: list[ParameterClassification] = [
        # Researcher-approved invariants (2026-10-30 & frozen checkpoints)
        ParameterClassification(
            parameter_key="checkpoints.vision",
            classification=(
                CONFIG_CLASS_SYNTHETIC_TEST
                if is_synthetic_test
                else CONFIG_CLASS_RESEARCHER_APPROVED
            ),
            value_summary={
                "path": config.checkpoints.vision.path,
                "expected_sha256": config.checkpoints.vision.expected_sha256,
                "model_name": config.checkpoints.vision.model_name,
            },
            decision_reference="FROZEN_CHECKPOINT_VISION_YOLOV8N",
            notes="Frozen YOLOv8n vision detector checkpoint and SHA-256.",
        ),
        ParameterClassification(
            parameter_key="checkpoints.audio_v3",
            classification=(
                CONFIG_CLASS_SYNTHETIC_TEST
                if is_synthetic_test
                else CONFIG_CLASS_RESEARCHER_APPROVED
            ),
            value_summary={
                "path": config.checkpoints.audio_v3.path,
                "expected_sha256": config.checkpoints.audio_v3.expected_sha256,
                "model_name": config.checkpoints.audio_v3.model_name,
            },
            decision_reference="FROZEN_CHECKPOINT_AUDIO_V3",
            notes="Frozen Audio V3 CompactTrainHornCNN checkpoint; legacy Audio V2 prohibited.",
        ),
        ParameterClassification(
            parameter_key="clock_semantics.b7d_delivery_disorder",
            classification=CONFIG_CLASS_RESEARCHER_APPROVED,
            value_summary={
                "perturbation_layer": "delivery_layer",
                "separates_clocks": [
                    "frame_timestamp_s",
                    "received_timestamp_s",
                    "processing_timestamp_s",
                ],
            },
            decision_reference="GOV-B7D-DELIVERY-DISORDER",
            notes="Approved 2026-10-30: B7d represents delivery-layer frame arrival disorder.",
        ),
        ParameterClassification(
            parameter_key="clock_semantics.b7e_delayed_timestamps",
            classification=CONFIG_CLASS_RESEARCHER_APPROVED,
            value_summary={
                "staleness_formula": "received_timestamp_s - frame_timestamp_s > source_staleness_s",
                "fail_closed_without_parameters": True,
            },
            decision_reference="GOV-B7E-MECHANISM",
            notes="Approved 2026-10-30: B7e staleness contract approved; numerical delay_s/target_source require explicit spec.",
        ),
        ParameterClassification(
            parameter_key="ground_truth_and_cohort_separation",
            classification=CONFIG_CLASS_RESEARCHER_APPROVED,
            value_summary={
                "train_events": "TRAIN_EVENT",
                "negative_controls": "NEGATIVE_CONTROL_SAFE_BASELINE",
                "engine_events": "ENGINE_INSPECTION_EXCLUDED",
            },
            decision_reference="GOV-GT-STATE-SEPARATION",
            notes="Approved 2026-10-30: Distinct ground-truth states and single engine event (engine_events/event_001) denominator isolation.",
        ),
        ParameterClassification(
            parameter_key="evaluation.descriptive_only_isolation",
            classification=CONFIG_CLASS_RESEARCHER_APPROVED,
            value_summary={"official_evaluation_eligible": False},
            decision_reference="GOV-D3-DESCRIPTIVE-MODE",
            notes="Approved 2026-10-30: Descriptive-only aggregation isolated from official Phase 12 path.",
        ),
        # Historical D1: Protocol and Ground-Truth Authority
        ParameterClassification(
            parameter_key="protocol_and_ground_truth_authority",
            classification=(
                CONFIG_CLASS_RESEARCHER_APPROVED
                if eff_d1_protocol
                else (
                    CONFIG_CLASS_SYNTHETIC_TEST
                    if is_synthetic_test
                    else CONFIG_CLASS_UNRESOLVED
                )
            ),
            value_summary={
                "head_baseline": "protocol_v8.0.0_gt_v6.0.0",
                "worktree_remediation": "protocol_v9.0.0_gt_v7.0.0_stage21_2.1.0",
            },
            decision_reference="GOV-D1-PROTOCOL-AUTHORITY",
            notes=(
                "Approved D1 protocol and ground-truth authority."
                if eff_d1_protocol
                else "Pending researcher decision D1 (GOV-D1-PROTOCOL-AUTHORITY) on protocol v8.0.0/v6.0.0 vs v9.0.0/v7.0.0."
            ),
        ),
        # Historical D2: Premature-Opening Evaluation Profile
        ParameterClassification(
            parameter_key="premature_opening_evaluation_profile",
            classification=(
                CONFIG_CLASS_RESEARCHER_APPROVED
                if eff_d2_profile
                else (
                    CONFIG_CLASS_SYNTHETIC_TEST
                    if is_synthetic_test
                    else CONFIG_CLASS_UNRESOLVED
                )
            ),
            value_summary={
                "candidate_m4": "first_blocked_to_t4_clearance",
                "candidate_v9": "t1_entry_to_t4_clearance",
            },
            decision_reference="GOV-D2-EVALUATION-PROFILE",
            notes=(
                "Approved D2 premature-opening evaluation profile."
                if eff_d2_profile
                else "Pending researcher decision D2 (GOV-D2-EVALUATION-PROFILE) on M4 vs v9 premature-opening window."
            ),
        ),
        # Experimental Parameter Domains (distinct from historical D1 and D2)
        ParameterClassification(
            parameter_key="fusion_and_operating_thresholds",
            classification=(
                CONFIG_CLASS_RESEARCHER_APPROVED
                if eff_thresholds
                else (
                    CONFIG_CLASS_SYNTHETIC_TEST
                    if is_synthetic_test
                    else CONFIG_CLASS_UNRESOLVED
                )
            ),
            value_summary={
                "vision_confidence_threshold_approach": config.vision.confidence_threshold_approach,
                "vision_confidence_threshold_departure": config.vision.confidence_threshold_departure,
                "audio_operating_threshold": config.audio.operating_threshold,
            },
            decision_reference="EXP-OPERATING-THRESHOLDS",
            notes=(
                "Approved EXP-OPERATING-THRESHOLDS operating thresholds and fusion weights."
                if eff_thresholds
                else "Provisional values in frozen_experiment_v1.yaml; pending researcher calibration freeze (EXP-OPERATING-THRESHOLDS)."
            ),
        ),
        ParameterClassification(
            parameter_key="roi_and_calibration_geometry",
            classification=(
                CONFIG_CLASS_RESEARCHER_APPROVED
                if eff_roi
                else (
                    CONFIG_CLASS_SYNTHETIC_TEST
                    if is_synthetic_test
                    else CONFIG_CLASS_UNRESOLVED
                )
            ),
            value_summary={
                "roi_config_supplied": roi_config is not None,
                "roi_config": dict(roi_config) if roi_config is not None else None,
            },
            decision_reference="EXP-ROI-GEOMETRY",
            notes=(
                "Approved EXP-ROI-GEOMETRY ROI and calibration geometry."
                if eff_roi
                else "Pending researcher decision EXP-ROI-GEOMETRY on formal ROI polygon and calibration acceptance."
            ),
        ),
        ParameterClassification(
            parameter_key="timing.cross_camera_sync",
            classification=(
                CONFIG_CLASS_RESEARCHER_APPROVED
                if d4_approved
                else (
                    CONFIG_CLASS_SYNTHETIC_TEST
                    if is_synthetic_test
                    else CONFIG_CLASS_UNRESOLVED
                )
            ),
            value_summary={
                "mode": config.timing.cross_camera_sync.mode,
                "status": config.timing.cross_camera_sync.status,
                "allow_unverified_zero_offset": config.timing.cross_camera_sync.allow_unverified_zero_offset,
            },
            decision_reference="GOV-D4-R04-SYNCHRONIZATION",
            notes=(
                "Approved D4 cross-camera synchronization policy."
                if d4_approved
                else "Pending researcher decision D4 (GOV-D4-R04-SYNCHRONIZATION) on empirical cross-camera offset calibration acceptance."
            ),
        ),
        # Software engineering defaults
        ParameterClassification(
            parameter_key="temporal_and_state_machine_defaults",
            classification=(
                CONFIG_CLASS_SYNTHETIC_TEST
                if is_synthetic_test
                else CONFIG_CLASS_SOFTWARE_DEFAULT
            ),
            value_summary={
                "tick_s": config.timing.tick_s,
                "confirm_frames": config.timing.confirm_frames,
                "miss_tolerance_frames": config.timing.miss_tolerance_frames,
                "warning_dwell_s": config.timing.warning_dwell_s,
                "gate_closing_s": config.timing.gate_closing_s,
                "gate_opening_s": config.timing.gate_opening_s,
                "clearance_dwell_s": config.timing.clearance_dwell_s,
                "source_staleness_s": config.timing.source_staleness_s,
                "fault_confirmation_frames": config.timing.fault_confirmation_frames,
                "fault_recovery_hold_s": config.timing.fault_recovery_hold_s,
                "window_tolerance_s": 0.25,
            },
            decision_reference="ENGINEERING_SOFTWARE_DEFAULTS",
            notes="Software engineering defaults not independently validated as final scientific constants.",
        ),
    ]

    norm_inj = failure_injector.strip() if failure_injector else "none"
    if norm_inj in ("B7e", "STALE_TIMESTAMPS", "stale_timestamps") or experiment_family == "B7e":
        has_b7e_params = (
            inj_params.get("delay_s") is not None
            and isinstance(inj_params.get("target_source"), str)
            and bool(str(inj_params.get("target_source")).strip())
        )
        b7e_class = (
            CONFIG_CLASS_SYNTHETIC_TEST
            if (is_synthetic_test and has_b7e_params)
            else (
                CONFIG_CLASS_RESEARCHER_APPROVED
                if (has_b7e_params and not is_synthetic_test and b7e_parameters_approved)
                else CONFIG_CLASS_UNRESOLVED
            )
        )
        classifications.append(
            ParameterClassification(
                parameter_key="injector.b7e_parameters",
                classification=b7e_class,
                value_summary={
                    "delay_s": inj_params.get("delay_s"),
                    "target_source": inj_params.get("target_source"),
                },
                decision_reference="EXP-B7E-PARAMETERS",
                notes=(
                    "Explicit B7e numerical parameters supplied"
                    + (" and researcher-approved." if b7e_parameters_approved else " (approval pending).")
                    if has_b7e_params
                    else "B7e numerical delay_s and target_source are unresolved and fail closed."
                ),
            )
        )

    return tuple(classifications)


# ---------------------------------------------------------------------------
# Section 5.3: Reconstructable Experiment Configuration Specification
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExperimentConfigurationSpec:
    """Complete, deterministic, reconstructable specification for an experiment condition."""

    spec_schema_version: str
    experiment_family: str
    condition_id: str
    run_id: str
    evaluation_mode: str
    configuration_class_summary: str
    frozen_config_sha256: str
    checkpoints: Mapping[str, Any]
    preprocessing_config: Mapping[str, Any]
    roi_config: Mapping[str, Any]
    fusion_config: Mapping[str, Any]
    state_machine_config: Mapping[str, Any]
    timing_and_clock_config: Mapping[str, Any]
    injector_config: Mapping[str, Any]
    cohort_handling_rules: Mapping[str, Any]
    cache_reuse_policy: str
    stream_cache_provenance_hashes: Mapping[str, str]
    parameter_classifications: tuple[ParameterClassification, ...]
    spec_sha256: str = ""

    def __post_init__(self) -> None:
        if self.experiment_family not in VALID_EXPERIMENT_FAMILIES:
            raise ValueError(
                f"Invalid experiment_family {self.experiment_family!r}; "
                f"expected one of {sorted(VALID_EXPERIMENT_FAMILIES)}"
            )
        if self.evaluation_mode not in VALID_EVALUATION_MODES:
            raise ValueError(
                f"Invalid evaluation_mode {self.evaluation_mode!r}; "
                f"expected one of {sorted(VALID_EVALUATION_MODES)}"
            )
        if self.configuration_class_summary not in CONFIGURATION_CLASSES:
            raise ValueError(
                f"Invalid configuration_class_summary {self.configuration_class_summary!r}; "
                f"expected one of {sorted(CONFIGURATION_CLASSES)}"
            )
        if self.cache_reuse_policy not in VALID_CACHE_REUSE_POLICIES:
            raise ValueError(
                f"Invalid cache_reuse_policy {self.cache_reuse_policy!r}; "
                f"expected one of {sorted(VALID_CACHE_REUSE_POLICIES)}"
            )
        computed = self.compute_spec_sha256()
        if not self.spec_sha256:
            object.__setattr__(self, "spec_sha256", computed)
        elif self.spec_sha256 != computed:
            raise ValueError(
                f"spec_sha256 mismatch: expected {computed}, got {self.spec_sha256}"
            )

    def identity_dict(self) -> dict[str, Any]:
        return canonicalize_config(
            {
                "spec_schema_version": self.spec_schema_version,
                "experiment_family": self.experiment_family,
                "condition_id": self.condition_id,
                "run_id": self.run_id,
                "evaluation_mode": self.evaluation_mode,
                "configuration_class_summary": self.configuration_class_summary,
                "frozen_config_sha256": self.frozen_config_sha256,
                "checkpoints": dict(self.checkpoints),
                "preprocessing_config": dict(self.preprocessing_config),
                "roi_config": dict(self.roi_config),
                "fusion_config": dict(self.fusion_config),
                "state_machine_config": dict(self.state_machine_config),
                "timing_and_clock_config": dict(self.timing_and_clock_config),
                "injector_config": dict(self.injector_config),
                "cohort_handling_rules": dict(self.cohort_handling_rules),
                "cache_reuse_policy": self.cache_reuse_policy,
                "stream_cache_provenance_hashes": dict(self.stream_cache_provenance_hashes),
                "parameter_classifications": [
                    p.to_dict() for p in self.parameter_classifications
                ],
            }
        )

    def compute_spec_sha256(self) -> str:
        return compute_canonical_digest(self.identity_dict())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_dict()
        payload["spec_sha256"] = self.spec_sha256
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ExperimentConfigurationSpec:
        raw_classifications = data.get("parameter_classifications", ())
        classifications = tuple(
            ParameterClassification(
                parameter_key=str(item["parameter_key"]),
                classification=str(item["classification"]),
                value_summary=item.get("value_summary"),
                decision_reference=str(item.get("decision_reference", "")),
                notes=str(item.get("notes", "")),
            )
            for item in raw_classifications
        )
        return cls(
            spec_schema_version=str(data.get("spec_schema_version", "experiment-spec/1.0")),
            experiment_family=str(data["experiment_family"]),
            condition_id=str(data["condition_id"]),
            run_id=str(data["run_id"]),
            evaluation_mode=str(data["evaluation_mode"]),
            configuration_class_summary=str(data["configuration_class_summary"]),
            frozen_config_sha256=str(data["frozen_config_sha256"]),
            checkpoints=dict(data["checkpoints"]),
            preprocessing_config=dict(data["preprocessing_config"]),
            roi_config=dict(data["roi_config"]),
            fusion_config=dict(data["fusion_config"]),
            state_machine_config=dict(data["state_machine_config"]),
            timing_and_clock_config=dict(data["timing_and_clock_config"]),
            injector_config=dict(data["injector_config"]),
            cohort_handling_rules=dict(data["cohort_handling_rules"]),
            cache_reuse_policy=str(data.get("cache_reuse_policy", CACHE_REUSE_ISOLATED_RUN)),
            stream_cache_provenance_hashes=dict(
                data.get("stream_cache_provenance_hashes", {})
            ),
            parameter_classifications=classifications,
            spec_sha256=str(data.get("spec_sha256", "")),
        )


def build_experiment_configuration_spec(
    config: FrozenExperimentConfig,
    *,
    experiment_family: str = "B1",
    condition_id: str = "B1_multimodal_ablation",
    run_id: str = "run_001",
    evaluation_mode: str = "provisional_exploratory",
    failure_injector: str = "none",
    injector_parameters: Mapping[str, Any] | None = None,
    injector_version: str = "1.0.0",
    roi_config: Mapping[str, Any] | None = None,
    cache_reuse_policy: str = CACHE_REUSE_ISOLATED_RUN,
    stream_cache_provenance_hashes: Mapping[str, str] | None = None,
    is_synthetic_test: bool = False,
    is_historical: bool = False,
    d1_approved: bool = False,
    d2_approved: bool = False,
    d4_approved: bool = False,
    protocol_authority_d1_approved: bool | None = None,
    evaluation_profile_d2_approved: bool | None = None,
    operating_thresholds_approved: bool | None = None,
    roi_geometry_approved: bool | None = None,
) -> ExperimentConfigurationSpec:
    """Construct a complete, reconstructable ``ExperimentConfigurationSpec`` from ``FrozenExperimentConfig``."""
    classifications = classify_experiment_parameters(
        config,
        experiment_family=experiment_family,
        failure_injector=failure_injector,
        injector_parameters=injector_parameters,
        roi_config=roi_config,
        is_synthetic_test=is_synthetic_test,
        is_historical=is_historical,
        d1_approved=d1_approved,
        d2_approved=d2_approved,
        d4_approved=d4_approved,
        protocol_authority_d1_approved=protocol_authority_d1_approved,
        evaluation_profile_d2_approved=evaluation_profile_d2_approved,
        operating_thresholds_approved=operating_thresholds_approved,
        roi_geometry_approved=roi_geometry_approved,
    )
    class_set = {c.classification for c in classifications}
    if is_historical:
        summary_class = CONFIG_CLASS_HISTORICAL
    elif is_synthetic_test:
        summary_class = CONFIG_CLASS_SYNTHETIC_TEST
    elif CONFIG_CLASS_UNRESOLVED in class_set:
        summary_class = CONFIG_CLASS_UNRESOLVED
    elif CONFIG_CLASS_SOFTWARE_DEFAULT in class_set:
        summary_class = CONFIG_CLASS_SOFTWARE_DEFAULT
    else:
        summary_class = CONFIG_CLASS_RESEARCHER_APPROVED

    vision_preproc = build_vision_preprocessing_config(config, roi_config=roi_config)
    audio_preproc = build_audio_preprocessing_config(config)
    effective_roi = (
        canonicalize_config(dict(roi_config))
        if roi_config is not None
        else {"roi_specified": False}
    )
    norm_inj = failure_injector.strip() if failure_injector else "none"
    inj_payload = {
        "failure_injector": norm_inj,
        "injector_parameters": canonicalize_config(dict(injector_parameters or {})),
        "injector_version": injector_version,
    }

    return ExperimentConfigurationSpec(
        spec_schema_version="experiment-spec/1.0",
        experiment_family=experiment_family,
        condition_id=condition_id,
        run_id=run_id,
        evaluation_mode=evaluation_mode,
        configuration_class_summary=summary_class,
        frozen_config_sha256=config.canonical_hash,
        checkpoints={
            "vision": {
                "path": config.checkpoints.vision.path,
                "expected_sha256": config.checkpoints.vision.expected_sha256,
                "model_name": config.checkpoints.vision.model_name,
            },
            "audio_v3": {
                "path": config.checkpoints.audio_v3.path,
                "expected_sha256": config.checkpoints.audio_v3.expected_sha256,
                "model_name": config.checkpoints.audio_v3.model_name,
            },
        },
        preprocessing_config={
            "vision": vision_preproc,
            "audio": audio_preproc,
        },
        roi_config=effective_roi,
        fusion_config={
            "confidence_threshold_approach": config.vision.confidence_threshold_approach,
            "confidence_threshold_departure": config.vision.confidence_threshold_departure,
            "audio_operating_threshold": config.audio.operating_threshold,
            "confirm_frames": config.timing.confirm_frames,
            "miss_tolerance_frames": config.timing.miss_tolerance_frames,
            "safety_constraints": {
                "audio_can_trigger_occupied_alone": True,
                "audio_can_trigger_clear": False,
                "require_vision_for_clear": True,
            },
        },
        state_machine_config={
            "warning_dwell_s": config.timing.warning_dwell_s,
            "gate_closing_s": config.timing.gate_closing_s,
            "gate_opening_s": config.timing.gate_opening_s,
            "clearance_dwell_s": config.timing.clearance_dwell_s,
            "fault_confirmation_frames": config.timing.fault_confirmation_frames,
            "fault_recovery_hold_s": config.timing.fault_recovery_hold_s,
        },
        timing_and_clock_config={
            "tick_s": config.timing.tick_s,
            "source_staleness_s": config.timing.source_staleness_s,
            "window_tolerance_s": 0.25,
            "cross_camera_sync": {
                "mode": config.timing.cross_camera_sync.mode,
                "status": config.timing.cross_camera_sync.status,
                "allow_unverified_zero_offset": config.timing.cross_camera_sync.allow_unverified_zero_offset,
            },
            "clock_semantics": {
                "b7d_delivery_disorder": "received_timestamp_s arrival order distinct from frame_timestamp_s",
                "b7e_staleness_rule": "received_timestamp_s - frame_timestamp_s > source_staleness_s",
            },
        },
        injector_config=inj_payload,
        cohort_handling_rules={
            "train_events": {
                "ground_truth_state": "TRAIN_EVENT",
                "included_in_sensitivity_denominator": True,
                "included_in_far_denominator": False,
            },
            "negative_controls": {
                "ground_truth_state": "NEGATIVE_CONTROL_SAFE_BASELINE",
                "included_in_sensitivity_denominator": False,
                "included_in_far_denominator": True,
            },
            "engine_events": {
                "ground_truth_state": "ENGINE_INSPECTION_EXCLUDED",
                "included_in_sensitivity_denominator": False,
                "included_in_far_denominator": False,
                "isolated_case_study_only": True,
            },
        },
        cache_reuse_policy=cache_reuse_policy,
        stream_cache_provenance_hashes=dict(stream_cache_provenance_hashes or {}),
        parameter_classifications=classifications,
    )


# ---------------------------------------------------------------------------
# Section 6: Non-Authoritative Synthetic Preflight Validator
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PreflightFinding:
    """Single structured diagnostic finding from the experiment preflight validator."""

    code: str
    category: str
    severity: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "category": self.category,
            "severity": self.severity,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ExperimentPreflightReport:
    """Non-authoritative diagnostic preflight report for an experiment specification.

    Invariants:
    - ``grants_eval_auth`` is ALWAYS ``False``.
    - ``grants_official_readiness`` is ALWAYS ``False``.
    - ``is_diagnostic_only`` is ALWAYS ``True``.
    """

    experiment_family: str
    condition_id: str
    evaluation_mode: str
    structurally_valid: bool
    ready_for_requested_mode: bool
    structural_errors: tuple[PreflightFinding, ...]
    missing_configuration_blockers: tuple[PreflightFinding, ...]
    unresolved_scientific_decision_blockers: tuple[PreflightFinding, ...]
    missing_authorization_blockers: tuple[PreflightFinding, ...]
    cache_provenance_incompatibilities: tuple[PreflightFinding, ...]
    required_cache_identities: tuple[dict[str, Any], ...]
    parameter_classifications: tuple[ParameterClassification, ...]
    grants_eval_auth: bool = False
    grants_official_readiness: bool = False
    is_diagnostic_only: bool = True

    def __post_init__(self) -> None:
        if self.grants_eval_auth is not False or self.grants_official_readiness is not False:
            raise ValueError(
                "ExperimentPreflightReport is strictly diagnostic and cannot grant "
                "EVAL-AUTH or official readiness."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_family": self.experiment_family,
            "condition_id": self.condition_id,
            "evaluation_mode": self.evaluation_mode,
            "structurally_valid": self.structurally_valid,
            "ready_for_requested_mode": self.ready_for_requested_mode,
            "structural_errors": [f.to_dict() for f in self.structural_errors],
            "missing_configuration_blockers": [
                f.to_dict() for f in self.missing_configuration_blockers
            ],
            "unresolved_scientific_decision_blockers": [
                f.to_dict() for f in self.unresolved_scientific_decision_blockers
            ],
            "missing_authorization_blockers": [
                f.to_dict() for f in self.missing_authorization_blockers
            ],
            "cache_provenance_incompatibilities": [
                f.to_dict() for f in self.cache_provenance_incompatibilities
            ],
            "required_cache_identities": copy.deepcopy(list(self.required_cache_identities)),
            "parameter_classifications": [
                p.to_dict() for p in self.parameter_classifications
            ],
            "grants_eval_auth": False,
            "grants_official_readiness": False,
            "is_diagnostic_only": True,
        }


def run_experiment_preflight(
    config: FrozenExperimentConfig,
    *,
    experiment_family: str = "B1",
    condition_id: str = "B1_multimodal_ablation",
    run_id: str = "run_001",
    evaluation_mode: str = "provisional_exploratory",
    failure_injector: str = "none",
    injector_parameters: Mapping[str, Any] | None = None,
    roi_config: Mapping[str, Any] | None = None,
    events: Sequence[tuple[str, str]] = (("train_events", "event_001"),),
    sources: Sequence[tuple[str, str]] = (
        ("camera_1", "vision"),
        ("camera_2", "vision"),
        ("audio_1", "audio"),
    ),
    cache_dir: Path | None = None,
    cache_reuse_policy: str = CACHE_REUSE_ISOLATED_RUN,
    has_sync_aligner: bool = False,
    d1_approved: bool = False,
    d2_approved: bool = False,
    d4_approved: bool = False,
    protocol_authority_d1_approved: bool | None = None,
    evaluation_profile_d2_approved: bool | None = None,
    operating_thresholds_approved: bool | None = None,
    roi_geometry_approved: bool | None = None,
    stage2_1_completed: bool = False,
    promotion_receipt_present: bool = False,
    official_split_present: bool = False,
    official_manifest_present: bool = False,
    eval_auth_granted: bool = False,
    is_synthetic_test: bool = False,
    b7e_parameters_approved: bool = False,
) -> ExperimentPreflightReport:
    """Inspect an experiment specification and report readiness blockers without side effects.

    Never reads raw media, never grants ``EVAL-AUTH``, and never modifies governance state.
    """
    eff_d1_protocol = d1_approved if protocol_authority_d1_approved is None else protocol_authority_d1_approved
    eff_d2_profile = d2_approved if evaluation_profile_d2_approved is None else evaluation_profile_d2_approved
    eff_thresholds = operating_thresholds_approved if operating_thresholds_approved is not None else False
    eff_roi = roi_geometry_approved if roi_geometry_approved is not None else False
    structural_errors: list[PreflightFinding] = []
    missing_config: list[PreflightFinding] = []
    unresolved_decisions: list[PreflightFinding] = []
    missing_auth: list[PreflightFinding] = []
    cache_incompatibilities: list[PreflightFinding] = []
    required_caches: list[dict[str, Any]] = []

    # 1. Structural & Checkpoint validation
    if experiment_family not in VALID_EXPERIMENT_FAMILIES:
        structural_errors.append(
            PreflightFinding(
                code="INVALID_EXPERIMENT_FAMILY",
                category="structural",
                severity="blocker",
                detail=f"Unknown experiment_family {experiment_family!r}",
            )
        )
    if evaluation_mode not in VALID_EVALUATION_MODES:
        structural_errors.append(
            PreflightFinding(
                code="INVALID_EVALUATION_MODE",
                category="structural",
                severity="blocker",
                detail=f"Unknown evaluation_mode {evaluation_mode!r}",
            )
        )
    if cache_reuse_policy not in VALID_CACHE_REUSE_POLICIES:
        structural_errors.append(
            PreflightFinding(
                code="INVALID_CACHE_REUSE_POLICY",
                category="structural",
                severity="blocker",
                detail=f"Unknown cache_reuse_policy {cache_reuse_policy!r}",
            )
        )

    norm_inj = failure_injector.strip() if failure_injector else "none"
    if norm_inj not in VALID_FAILURE_INJECTORS:
        structural_errors.append(
            PreflightFinding(
                code="INVALID_FAILURE_INJECTOR",
                category="structural",
                severity="blocker",
                detail=f"Unknown failure_injector {failure_injector!r}",
            )
        )

    # Check prohibited Audio V2 checkpoint
    audio_sha = config.checkpoints.audio_v3.expected_sha256.strip().lower()
    audio_path_norm = config.checkpoints.audio_v3.path.replace("\\", "/").strip().lower()
    if audio_sha == PROHIBITED_AUDIO_V2_SHA256 or any(
        audio_path_norm.endswith(sfx) for sfx in PROHIBITED_AUDIO_V2_PATH_SUFFIXES
    ):
        structural_errors.append(
            PreflightFinding(
                code="PROHIBITED_AUDIO_V2_CHECKPOINT",
                category="structural",
                severity="blocker",
                detail=(
                    f"Prohibited legacy Audio V2 checkpoint detected "
                    f"(path={config.checkpoints.audio_v3.path!r}, sha256={audio_sha!r})."
                ),
            )
        )

    # 2. Missing configuration parameters (including B7e fail-closed & ROI config)
    inj_params = dict(injector_parameters or {})
    if norm_inj in ("B7e", "STALE_TIMESTAMPS", "stale_timestamps") or experiment_family == "B7e":
        try:
            _validate_injector_contract("B7e", inj_params)
        except CacheProvenanceError as exc:
            missing_config.append(
                PreflightFinding(
                    code="B7E_PARAMETERS_MISSING",
                    category="missing_configuration",
                    severity="blocker",
                    detail=str(exc),
                )
            )
            unresolved_decisions.append(
                PreflightFinding(
                    code="DECISION_B7E_NUMERICAL_PARAMETERS_PENDING",
                    category="unresolved_scientific_decision",
                    severity="blocker",
                    detail=(
                        "B7e delayed-timestamp contract requires explicit researcher-approved "
                        "numerical delay_s and target_source parameters (EXP-B7E-PARAMETERS)."
                    ),
                )
            )

    if roi_config is None and not eff_roi and not is_synthetic_test:
        missing_config.append(
            PreflightFinding(
                code="ROI_GEOMETRY_UNSPECIFIED",
                category="missing_configuration",
                severity="warning" if evaluation_mode == "provisional_exploratory" else "blocker",
                detail="No explicit roi_config polygon/geometry was provided (EXP-ROI-GEOMETRY pending).",
            )
        )

    # Check cross-camera fusion R04
    vision_sources = [src for src, mod in sources if mod == "vision"]
    if (
        len(vision_sources) > 1
        and not has_sync_aligner
        and not config.timing.cross_camera_sync.allow_unverified_zero_offset
    ):
        missing_config.append(
            PreflightFinding(
                code="R04_CROSS_CAMERA_SYNC_MISSING",
                category="missing_configuration",
                severity="blocker",
                detail=(
                    f"Multiple vision sources {vision_sources} configured without SyncAligner "
                    "while allow_unverified_zero_offset is False (R04 Timing Integrity)."
                ),
            )
        )

    # 3. Unresolved scientific decisions (Historical D1, D2, D4 + Experimental Thresholds & ROI)
    if not eff_d1_protocol and not is_synthetic_test:
        unresolved_decisions.append(
            PreflightFinding(
                code="DECISION_D1_PENDING",
                category="unresolved_scientific_decision",
                severity="blocker" if evaluation_mode == "official_evaluation" else "advisory",
                detail=(
                    "Decision D1 (GOV-D1-PROTOCOL-AUTHORITY: protocol v8.0.0/v6.0.0 vs "
                    "v9.0.0/v7.0.0 authority) remains pending researcher decision."
                ),
            )
        )
    if not eff_d2_profile and not is_synthetic_test:
        unresolved_decisions.append(
            PreflightFinding(
                code="DECISION_D2_PENDING",
                category="unresolved_scientific_decision",
                severity="blocker" if evaluation_mode == "official_evaluation" else "advisory",
                detail=(
                    "Decision D2 (GOV-D2-EVALUATION-PROFILE: premature-opening evaluation "
                    "profile M4 vs v9) remains pending researcher decision."
                ),
            )
        )
    if not eff_thresholds and not is_synthetic_test:
        unresolved_decisions.append(
            PreflightFinding(
                code="DECISION_EXP_OPERATING_THRESHOLDS_PENDING",
                category="unresolved_scientific_decision",
                severity="blocker" if evaluation_mode == "official_evaluation" else "advisory",
                detail=(
                    "Experimental parameter domain EXP-OPERATING-THRESHOLDS (vision/audio "
                    "operating thresholds and fusion weights in frozen_experiment_v1.yaml) "
                    "remains provisional and unapproved for official claims."
                ),
            )
        )
    if not eff_roi and not is_synthetic_test:
        unresolved_decisions.append(
            PreflightFinding(
                code="DECISION_EXP_ROI_GEOMETRY_PENDING",
                category="unresolved_scientific_decision",
                severity="blocker" if evaluation_mode == "official_evaluation" else "advisory",
                detail=(
                    "Experimental parameter domain EXP-ROI-GEOMETRY (danger-zone ROI polygon "
                    "geometry and camera calibration acceptance) remains pending."
                ),
            )
        )
    if not d4_approved and len(vision_sources) > 1 and not is_synthetic_test:
        unresolved_decisions.append(
            PreflightFinding(
                code="DECISION_D4_PENDING",
                category="unresolved_scientific_decision",
                severity="blocker" if not has_sync_aligner else "advisory",
                detail=(
                    "Decision D4 (GOV-D4-R04-SYNCHRONIZATION: empirical cross-camera "
                    "synchronization scope and acceptance criteria) remains pending."
                ),
            )
        )

    # 4. Governance & Human-Review Authorizations
    if not stage2_1_completed and not is_synthetic_test:
        missing_auth.append(
            PreflightFinding(
                code="STAGE2_1_HUMAN_ADJUDICATION_MISSING",
                category="missing_authorization",
                severity="blocker" if evaluation_mode == "official_evaluation" else "advisory",
                detail="Stage-2.1 independent dual-reviewer ground-truth adjudication is not completed.",
            )
        )
    if not promotion_receipt_present and not is_synthetic_test:
        missing_auth.append(
            PreflightFinding(
                code="GROUND_TRUTH_PROMOTION_RECEIPT_MISSING",
                category="missing_authorization",
                severity="blocker" if evaluation_mode == "official_evaluation" else "advisory",
                detail="Canonical ground-truth promotion receipt is absent (`data/ground_truth/canonical/` empty).",
            )
        )
    if evaluation_mode == "official_evaluation":
        if not official_split_present:
            missing_auth.append(
                PreflightFinding(
                    code="OFFICIAL_EVENT_SPLIT_MISSING",
                    category="missing_authorization",
                    severity="blocker",
                    detail="Official locked event split is missing.",
                )
            )
        if not official_manifest_present:
            missing_auth.append(
                PreflightFinding(
                    code="OFFICIAL_EVALUATION_MANIFEST_MISSING",
                    category="missing_authorization",
                    severity="blocker",
                    detail="Official Phase 12 evaluation input manifest is missing.",
                )
            )
        if not eval_auth_granted:
            missing_auth.append(
                PreflightFinding(
                    code="EVAL_AUTH_NOT_GRANTED",
                    category="missing_authorization",
                    severity="blocker",
                    detail="Explicit researcher authorization EVAL-AUTH has not been granted.",
                )
            )

    # 5. Required cache identities & existing cache compatibility check
    vision_preproc = build_vision_preprocessing_config(config, roi_config=roi_config)
    audio_preproc = build_audio_preprocessing_config(config)
    timing_cfg = {
        "tick_s": float(config.timing.tick_s),
        "confirm_frames": int(config.timing.confirm_frames),
        "miss_tolerance_frames": int(config.timing.miss_tolerance_frames),
        "warning_dwell_s": float(config.timing.warning_dwell_s),
        "gate_closing_s": float(config.timing.gate_closing_s),
        "gate_opening_s": float(config.timing.gate_opening_s),
        "clearance_dwell_s": float(config.timing.clearance_dwell_s),
        "source_staleness_s": float(config.timing.source_staleness_s),
        "fault_confirmation_frames": int(config.timing.fault_confirmation_frames),
        "fault_recovery_hold_s": float(config.timing.fault_recovery_hold_s),
        "cross_camera_sync_mode": str(config.timing.cross_camera_sync.mode),
        "cross_camera_sync_status": str(config.timing.cross_camera_sync.status),
        "allow_unverified_zero_offset": bool(
            config.timing.cross_camera_sync.allow_unverified_zero_offset
        ),
    }

    if not structural_errors and not any(
        f.code == "B7E_PARAMETERS_MISSING" for f in missing_config
    ):
        for cohort, event_id in events:
            for source_id, modality in sources:
                try:
                    prov = ControlledCacheProvenance(
                        cohort=cohort,
                        event_id=event_id,
                        source_id=source_id,
                        modality=modality,
                        model_architecture=(
                            config.checkpoints.vision.model_name
                            if modality == "vision"
                            else config.checkpoints.audio_v3.model_name
                        ),
                        checkpoint_sha256=(
                            config.checkpoints.vision.expected_sha256
                            if modality == "vision"
                            else config.checkpoints.audio_v3.expected_sha256
                        ),
                        preprocessing_config=(
                            vision_preproc if modality == "vision" else audio_preproc
                        ),
                        experiment_config_sha256=config.canonical_hash,
                        failure_injector=norm_inj,
                        injector_parameters=inj_params,
                        timing_config=timing_cfg,
                        cache_schema_version=CONTROLLED_CACHE_SCHEMA_VERSION,
                        software_version=config.experiment.version,
                        run_id=run_id,
                        roi_config=roi_config,
                    )
                    required_caches.append(
                        {
                            "cohort": cohort,
                            "event_id": event_id,
                            "source_id": source_id,
                            "modality": modality,
                            "expected_filename": prov.cache_filename(),
                            "configuration_sha256": prov.configuration_sha256(),
                            "cache_identity_sha256": prov.cache_identity_sha256(),
                            "provenance_sha256": prov.provenance_sha256(),
                        }
                    )
                    if cache_dir is not None and cache_dir.exists():
                        candidate_file = cache_dir / prov.cache_filename()
                        legacy_vision_matches = list(
                            cache_dir.glob(f"{cohort}_{event_id}_*_{source_id}_vision.jsonl")
                        )
                        legacy_audio_file = (
                            cache_dir / f"{cohort}_{event_id}_{source_id}_audio.jsonl"
                        )
                        if candidate_file.exists():
                            try:
                                load_controlled_cache_jsonl(
                                    candidate_file, prov, reuse_policy=cache_reuse_policy
                                )
                            except CacheProvenanceError as exc:
                                cache_incompatibilities.append(
                                    PreflightFinding(
                                        code=exc.code,
                                        category="cache_provenance",
                                        severity="blocker",
                                        detail=f"{candidate_file.name}: {exc.detail}",
                                    )
                                )
                        else:
                            prefix = f"{cohort}__{event_id.replace('/', '__')}__{source_id}__{modality}__"
                            conflicting = [
                                p
                                for p in cache_dir.glob(f"{prefix}*.jsonl")
                                if p != candidate_file
                            ]
                            for conflict_path in conflicting:
                                try:
                                    load_controlled_cache_jsonl(
                                        conflict_path, prov, reuse_policy=cache_reuse_policy
                                    )
                                except CacheProvenanceError as exc:
                                    cache_incompatibilities.append(
                                        PreflightFinding(
                                            code=exc.code,
                                            category="cache_provenance",
                                            severity="blocker",
                                            detail=f"{conflict_path.name}: {exc.detail}",
                                        )
                                    )
                            if modality == "vision" and legacy_vision_matches:
                                cache_incompatibilities.append(
                                    PreflightFinding(
                                        code="HISTORICAL_UNVERIFIED_CACHE_PRESENT",
                                        category="cache_provenance",
                                        severity="blocker",
                                        detail=(
                                            f"Legacy unverified vision cache {legacy_vision_matches[0].name} "
                                            "cannot be used as a controlled experiment cache."
                                        ),
                                    )
                                )
                            elif modality == "audio" and legacy_audio_file.exists():
                                cache_incompatibilities.append(
                                    PreflightFinding(
                                        code="HISTORICAL_UNVERIFIED_CACHE_PRESENT",
                                        category="cache_provenance",
                                        severity="blocker",
                                        detail=(
                                            f"Legacy unverified audio cache {legacy_audio_file.name} "
                                            "cannot be used as a controlled experiment cache."
                                        ),
                                    )
                                )
                except CacheProvenanceError as exc:
                    structural_errors.append(
                        PreflightFinding(
                            code=exc.code,
                            category="structural",
                            severity="blocker",
                            detail=exc.detail,
                        )
                    )

    classifications = classify_experiment_parameters(
        config,
        experiment_family=experiment_family,
        failure_injector=norm_inj,
        injector_parameters=inj_params,
        roi_config=roi_config,
        is_synthetic_test=is_synthetic_test,
        d1_approved=d1_approved,
        d2_approved=d2_approved,
        d4_approved=d4_approved,
        protocol_authority_d1_approved=eff_d1_protocol,
        evaluation_profile_d2_approved=eff_d2_profile,
        operating_thresholds_approved=eff_thresholds,
        roi_geometry_approved=eff_roi,
        b7e_parameters_approved=b7e_parameters_approved,
    )

    structurally_valid = len(structural_errors) == 0
    all_blockers = [
        f
        for group in (
            structural_errors,
            missing_config,
            unresolved_decisions,
            missing_auth,
            cache_incompatibilities,
        )
        for f in group
        if f.severity == "blocker"
    ]
    ready_for_requested_mode = structurally_valid and len(all_blockers) == 0

    return ExperimentPreflightReport(
        experiment_family=experiment_family,
        condition_id=condition_id,
        evaluation_mode=evaluation_mode,
        structurally_valid=structurally_valid,
        ready_for_requested_mode=ready_for_requested_mode,
        structural_errors=tuple(structural_errors),
        missing_configuration_blockers=tuple(missing_config),
        unresolved_scientific_decision_blockers=tuple(unresolved_decisions),
        missing_authorization_blockers=tuple(missing_auth),
        cache_provenance_incompatibilities=tuple(cache_incompatibilities),
        required_cache_identities=tuple(required_caches),
        parameter_classifications=classifications,
        grants_eval_auth=False,
        grants_official_readiness=False,
        is_diagnostic_only=True,
    )


__all__ = [
    "CANONICAL_DECISION_REGISTER",
    "CONFIG_CLASS_HISTORICAL",
    "CONFIG_CLASS_RESEARCHER_APPROVED",
    "CONFIG_CLASS_SOFTWARE_DEFAULT",
    "CONFIG_CLASS_SYNTHETIC_TEST",
    "CONFIG_CLASS_UNRESOLVED",
    "CONFIGURATION_CLASSES",
    "DECISION_STATUSES",
    "DECISION_STATUS_APPROVED",
    "DECISION_STATUS_IMPLEMENTED_NOT_APPROVED",
    "DECISION_STATUS_NOT_APPLICABLE",
    "DECISION_STATUS_PENDING",
    "DECISION_STATUS_RECOMMENDATION_ONLY",
    "DECISION_STATUS_SUPERSEDED",
    "HISTORICAL_DECISION_ALIASES",
    "VALID_EVALUATION_MODES",
    "DecisionRegisterEntry",
    "ExperimentConfigurationSpec",
    "ExperimentPreflightReport",
    "ParameterClassification",
    "PreflightFinding",
    "build_experiment_configuration_spec",
    "classify_experiment_parameters",
    "lookup_decision_register",
    "run_experiment_preflight",
]
