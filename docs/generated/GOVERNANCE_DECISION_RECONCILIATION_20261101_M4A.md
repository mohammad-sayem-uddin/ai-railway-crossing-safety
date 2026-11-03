# Governance Decision Register Reconciliation Report (Mission 4A)

**Date:** 2026-11-01  
**Mission:** 4A — Governance Reconciliation, Authorization Integrity & Stage-2.1 Safety Verification  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Branch / HEAD:** `main` @ `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Status:** RECONCILED (Programmatic & Documentary Canonicalization Complete)

---

## 1. Executive Summary

During Mission 3, a cross-mission decision-label collision was introduced in `src/railway_detection/experiments/preflight_validator.py` and `docs/generated/RESEARCH_GOVERNANCE_STATUS_20261101_M3.md`:
- Historical **`D1`** (Protocol Authority Reconciliation: `EXPERIMENT_PROTOCOL_V2.md` v9.0.0 vs `GROUND_TRUTH_DESIGN_DOCUMENT.md` v1.0.0) and historical **`D2`** (Premature-Opening Window & Gate-Metrics Profile: `v9` vs `M4` vs `dual_report`) were inadvertently overloaded with two experimental parameter domains: **`EXP-OPERATING-THRESHOLDS`** (vision/audio operating thresholds) and **`EXP-ROI-GEOMETRY`** (crossing ROI polygon geometry).
- In addition, **`D3`** carried two distinct historical scopes across Mission 1 and Mission 2 reports:
  1. `GOV-D3-DESCRIPTIVE-MODE` (Historical 27-event evaluation mode = `DESCRIPTIVE_ONLY`, **approved** in `RESEARCHER_DECISION_LOG_20261030.md` §3).
  2. `AUTH-EVENT-SPLIT` (Calibration-pilot vs held-out evaluation split among the 23 train events, **pending** in `RESEARCHER_DECISION_REGISTER_20261101_M2.md`).

Mission 4A resolves this ambiguity without inventing or assuming any researcher approval:
1. Every historical decision ID (`D1`–`D4`, `B7d`, `B7e`, `ENGINE_ISOLATION`, `GT_SEPARATION`, `LEG_EXEC`, `STAGE21_SAFEGUARDS`, `EVAL_AUTH`) and every Mission 3 experimental parameter domain (`EXP-OPERATING-THRESHOLDS`, `EXP-ROI-GEOMETRY`) now has a unique **Canonical ID**, an explicit **Historical ID Alias Map**, and a machine-verified **Decision Status** in `src/railway_detection/experiments/preflight_validator.py` (`CANONICAL_DECISION_REGISTER`).
2. `classify_experiment_parameters()`, `build_experiment_configuration_spec()`, and `run_experiment_preflight()` now track `D1` (`protocol_authority_d1_approved`) and `D2` (`evaluation_profile_d2_approved`) distinctly from `operating_thresholds_approved` (`DECISION_EXP_OPERATING_THRESHOLDS_PENDING`) and `roi_geometry_approved` (`DECISION_EXP_ROI_GEOMETRY_PENDING`), while preserving backward-compatible blocker codes (`DECISION_D1_PENDING`, `DECISION_D2_PENDING`, `DECISION_D4_PENDING`).

---

## 2. Permitted Decision Status Taxonomy

All entries in the Canonical Decision Register are restricted to the six statuses mandated by Mission 4A Section 4.4 (`DECISION_STATUSES` in `src/railway_detection/experiments/preflight_validator.py`):

| Status Token | Meaning |
|---|---|
| `APPROVED_BY_RESEARCHER` | Explicitly approved by the researcher in an authoritative governance log; safe for authorized scope. |
| `PENDING_RESEARCHER_DECISION` | Scientific/governance choice awaiting explicit researcher sign-off; fails closed in official/controlled gates. |
| `TECHNICAL_RECOMMENDATION_ONLY` | Engineering recommendation documented in decision packets (`R1`/`M2`), not an active researcher approval. |
| `IMPLEMENTED_BUT_NOT_SCIENTIFICALLY_APPROVED` | Code mechanism is implemented and unit-tested, but the underlying scientific policy/threshold is not yet approved. |
| `SUPERSEDED_WITH_EXPLICIT_RECORD` | Earlier label or formulation superseded by an explicit canonical ID and cross-reference record. |
| `NOT_APPLICABLE` | Not applicable to the given scope or cohort. |

---

## 3. Master Canonical Decision Register (17 Canonical Entries)

| Canonical ID | Historical ID(s) | Title / Scope | Authoritative Status | Technical Rec. / Implementation Note | Source Document(s) |
|---|---|---|---|---|---|
| `GOV-D1-PROTOCOL-AUTHORITY` | `D1` | Protocol Authority Reconciliation (`EXPERIMENT_PROTOCOL_V2.md` v9.0.0 vs `GROUND_TRUTH_DESIGN_DOCUMENT.md` v1.0.0) | `PENDING_RESEARCHER_DECISION` | `TECHNICAL_RECOMMENDATION_ONLY` (Option D1-A recommended in R1 packet; never auto-approved) | `RESEARCHER_DECISION_LOG_20261030.md` §1; `RESEARCHER_DECISION_PACKET_20261030_R1.md` §D1; `RESEARCHER_DECISION_REGISTER_20261101_M2.md` §2 |
| `GOV-D2-EVALUATION-PROFILE` | `D2` | Premature-Opening Window & Gate-Metrics Profile (`v9` `[T1, T4]` vs `M4` `[t_blocked, T4]` vs `dual_report`) | `PENDING_RESEARCHER_DECISION` | `IMPLEMENTED_BUT_NOT_SCIENTIFICALLY_APPROVED` (`v9`, `M4`, `dual_report` implemented in `metrics.py`; default `undecided`) | `RESEARCHER_DECISION_LOG_20261030.md` §2; `RESEARCHER_DECISION_PACKET_20261030_R1.md` §D2; `metrics.py` |
| `GOV-D3-DESCRIPTIVE-MODE` | `D3`, `D3_DESCRIPTIVE` | Historical 27-Event Evaluation Mode (`DESCRIPTIVE_ONLY` isolation) | `APPROVED_BY_RESEARCHER` | Implemented in `descriptive_only.py`; sets `official_evaluation_eligible=False` | `RESEARCHER_DECISION_LOG_20261030.md` §3; `RESEARCHER_DECISION_REGISTER_20261101_M2.md` §1 |
| `AUTH-EVENT-SPLIT` | `D3_SPLIT`, `EVENT_SPLIT` | Calibration-Pilot vs Held-Out Evaluation Split (among 23 `train_events`) | `PENDING_RESEARCHER_DECISION` | `TECHNICAL_RECOMMENDATION_ONLY` (Stratified split recommended; requires Stage-2.1 review completion first) | `RESEARCHER_DECISION_REGISTER_20261101_M2.md` §2 (`D3`) |
| `GOV-D4-R04-SYNCHRONIZATION` | `D4` | Dual-Camera Temporal Synchronization & Replay Clock Policy (`R-04`) | `PENDING_RESEARCHER_DECISION` | `IMPLEMENTED_BUT_NOT_SCIENTIFICALLY_APPROVED` (`clock_aware.py` defaults to `independent_camera_clocks`, abstains cross-camera metrics when `delta_t_cam == 0.0`) | `RESEARCHER_DECISION_LOG_20261030.md` §4; `RESEARCHER_DECISION_PACKET_20261030_R1.md` §D4; `clock_aware.py` |
| `EXP-OPERATING-THRESHOLDS` | `M3_D1_OVERLOAD_OPERATING_THRESHOLDS` | Vision & Audio Detector Operating Thresholds (`conf_threshold`, `enter_threshold`, `exit_threshold`, `audio_prob_threshold`) | `PENDING_RESEARCHER_DECISION` | `IMPLEMENTED_BUT_NOT_SCIENTIFICALLY_APPROVED` (Frozen baseline values in `configs/frozen_experiment.yaml` are historical defaults, not post-Stage-2.1 calibrated approvals) | `RESEARCH_GOVERNANCE_STATUS_20261101_M3.md`; `preflight_validator.py` |
| `EXP-ROI-GEOMETRY` | `M3_D2_OVERLOAD_ROI_GEOMETRY` | Crossing ROI Geometry & Polygon Calibration (`roi_polygon_normalized`) | `PENDING_RESEARCHER_DECISION` | `IMPLEMENTED_BUT_NOT_SCIENTIFICALLY_APPROVED` (Tracked in `ControlledCacheProvenance`; site-specific calibration pending) | `RESEARCH_GOVERNANCE_STATUS_20261101_M3.md`; `preflight_validator.py` |
| `MECH-B7D-DELIVERY-DISORDER` | `B7d` | Scenario B7d Delivery-Layer Packet Reordering (`apply_delivery_disorder`, `seed=42`) | `APPROVED_BY_RESEARCHER` | Implemented in `failure_injector.py`, `collector.py`, and `runner.py` | `RESEARCHER_DECISION_REGISTER_20261101_M2.md` §1 (`B7d`) |
| `MECH-B7E-DELAYED-TIMESTAMPS` | `B7e` | Scenario B7e Delayed-Timestamp Injection (`delay_s=2.0`, `target_source=camera_front`) | `APPROVED_BY_RESEARCHER` | Implemented in `failure_injector.py` and enforced in `cache_provenance.py` | `RESEARCHER_DECISION_REGISTER_20261101_M2.md` §1 (`B7e`) |
| `GOV-ENGINE-ISOLATION` | `ENGINE_ISOLATION` | Engine-Only Event (`engine_events/event_001`) Isolation from Train Sensitivity & Negative-Control FAR Denominators | `APPROVED_BY_RESEARCHER` | Implemented in `metrics.py` (`EventMetricsCalculator.aggregate_cohort`) and `descriptive_only.py` | `RESEARCHER_DECISION_REGISTER_20261101_M2.md` §1 (`ENGINE_ISOLATION`) |
| `GOV-GT-STATE-SEPARATION` | `GT_SEPARATION` | Ground-Truth State Separation (`OBSERVABLE`, `UNOBSERVABLE_NOT_APPLICABLE`, `CENSORED`, `UNCERTAIN`) | `APPROVED_BY_RESEARCHER` | Implemented in `stage2_1_schema.py` and `metrics.py` | `RESEARCHER_DECISION_REGISTER_20261101_M2.md` §1 (`GT_SEPARATION`) |
| `AUTH-LEG-EXEC-INVALIDATION` | `LEG_EXEC`, `LEG-EXEC` | Legacy 27-Record Sidecar Invalidation Notice Execution (`PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json`) | `APPROVED_BY_RESEARCHER` | Executed in Phase 11.6 (`27` `.INVALIDATION_NOTICE.json` sidecars present and verified; original `27` review files byte-preserved; re-execution in write mode prohibited) | `PHASE11_6_INVALIDATION_EXECUTION_REPORT.md`; `RESEARCHER_DECISION_REGISTER_20261101_M2.md` §1 (`LEG-EXEC`) |
| `GOV-STAGE21-SAFEGUARDS` | `STAGE21_SAFEGUARDS` | Stage-2.1 Anti-Fabrication Safeguards (`30.0s` duration floor, allowlist, blocklist, media-hash binding, model-independence attestation, `synthetic_` ID isolation) | `APPROVED_BY_RESEARCHER` | Implemented across `stage2_1_schema.py`, `promotion_gate.py`, `adjudication_session.py`, `stage21_timing_pilot.py`, `evaluation_readiness_gate.py` | `RESEARCHER_DECISION_REGISTER_20261101_M2.md` §1 (`STAGE21_SAFEGUARDS`) |
| `AUTH-STAGE21-ALLOWLIST` | `STAGE21_ALLOWLIST`, `REVIEWER_ALLOWLIST` | Population of `data/ground_truth/authorized_reviewers.json` with Real Named Human Reviewer IDs | `PENDING_RESEARCHER_DECISION` | File intentionally absent until researcher designates real human reviewers | `STAGE21_HUMAN_REVIEW_READINESS_20261101_M2.md`; `promotion_gate.py` |
| `AUTH-PILOT-EXEC` | `PILOT-EXEC`, `PILOT_EXEC` | Execution of Real 3-Event Stage-2.1 Timing Calibration Pilot | `PENDING_RESEARCHER_DECISION` | Blocked until researcher populates `authorized_reviewers.json` and runs real human review session | `STAGE21_REVIEW_WORKFLOW_FINAL_20261101_M3.md` |
| `AUTH-PROMOTE-EXEC` | `PROMOTE-EXEC`, `PROMOTE_EXEC` | Promotion of Approved Stage-2.1 Reviews into `data/ground_truth/approved/` and Creation of `PROMOTION_RECEIPT.json` | `PENDING_RESEARCHER_DECISION` | Blocked (`0/27` Stage-2.1 reviews completed; `PROMOTION_RECEIPT.json` absent) | `STAGE21_REVIEW_WORKFLOW_FINAL_20261101_M3.md` |
| `AUTH-EVAL-OFFICIAL` | `EVAL_AUTH`, `EVAL-AUTH` | Authorization to Execute Official Phase 12 B0–B7 Evaluation & Report Inferential Claims | `PENDING_RESEARCHER_DECISION` | Blocked by `execution_gate.py`, `evaluation_runner.py`, and `preflight_validator.py` (`ready_for_official_evaluation=False`) | `RESEARCHER_DECISION_REGISTER_20261101_M2.md`; `RESEARCH_GOVERNANCE_STATUS_20261101_M3.md` |

---

## 4. Explicit Record of Superseded / Overloaded Mission 3 Labels

| Overloaded Label in Mission 3 | Where It Appeared | Why It Was Ambiguous | Canonical Replacement in Mission 4A | Status of Overloaded Label |
|---|---|---|---|---|
| `D1` = "Detector operating thresholds (`conf_threshold`, `enter_threshold`, `exit_threshold`)" | `preflight_validator.py` (M3 version), `RESEARCH_GOVERNANCE_STATUS_20261101_M3.md` | Collided with historical `D1` = Protocol Authority Reconciliation (`EXPERIMENT_PROTOCOL_V2.md` v9.0.0 vs `GROUND_TRUTH_DESIGN_DOCUMENT.md` v1.0.0) from Mission 1 & Mission 2 | Historical `D1` restored to `GOV-D1-PROTOCOL-AUTHORITY`; operating thresholds assigned to `EXP-OPERATING-THRESHOLDS` (`M3_D1_OVERLOAD_OPERATING_THRESHOLDS` recorded as alias) | `SUPERSEDED_WITH_EXPLICIT_RECORD` |
| `D2` = "Crossing ROI polygon geometry (`roi_polygon_normalized`)" | `preflight_validator.py` (M3 version), `RESEARCH_GOVERNANCE_STATUS_20261101_M3.md` | Collided with historical `D2` = Premature-Opening Window & Gate-Metrics Profile (`v9` vs `M4` vs `dual_report`) from Mission 1 & Mission 2 | Historical `D2` restored to `GOV-D2-EVALUATION-PROFILE`; ROI geometry assigned to `EXP-ROI-GEOMETRY` (`M3_D2_OVERLOAD_ROI_GEOMETRY` recorded as alias) | `SUPERSEDED_WITH_EXPLICIT_RECORD` |
| `D3` (unqualified) | `RESEARCHER_DECISION_LOG_20261030.md` vs `RESEARCHER_DECISION_REGISTER_20261101_M2.md` | Used for both Historical 27-Event Descriptive Mode (Approved) and Calibration-vs-Test Split among 23 Train Events (Pending) | Split into `GOV-D3-DESCRIPTIVE-MODE` (`D3`, `APPROVED_BY_RESEARCHER`) and `AUTH-EVENT-SPLIT` (`D3_SPLIT`, `PENDING_RESEARCHER_DECISION`) | Reconciled with distinct canonical IDs |

---

## 5. Verification in Code and Unit Tests

- **Module:** `src/railway_detection/experiments/preflight_validator.py`
  - `CANONICAL_DECISION_REGISTER`: 17 `DecisionRegisterEntry` records.
  - `HISTORICAL_DECISION_ALIASES`: maps both historical short codes (`D1`, `D2`, `D3`, `D3_SPLIT`, `D4`, `B7d`, `B7e`, `ENGINE_ISOLATION`, `GT_SEPARATION`, `LEG_EXEC`, `STAGE21_SAFEGUARDS`, `EVAL_AUTH`) and superseded Mission 3 overload aliases (`M3_D1_OVERLOAD_OPERATING_THRESHOLDS`, `M3_D2_OVERLOAD_ROI_GEOMETRY`) to their canonical entries.
  - `lookup_decision_register(identifier)` resolves any canonical ID or historical alias deterministically and raises `KeyError` on unknown IDs.
- **Unit Tests (`tests/unit/test_mission4a_governance_and_stage21_safety.py`):**
  - `test_canonical_decision_register_statuses_and_historical_reconciliation`
  - `test_preflight_validator_separates_d1_d2_from_thresholds_and_roi`
