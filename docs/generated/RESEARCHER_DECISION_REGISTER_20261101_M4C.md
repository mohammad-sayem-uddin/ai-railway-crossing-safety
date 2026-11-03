# Researcher Decision Register & Experiment Authorization Preparation — Mission 4C

**Date:** 2026-11-01  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Status:** Decision preparation only; no decision made by Mission 4C.

## Executive summary

Mission 4C reconciled the canonical decision register against source code, configurations, governance artifacts, and prior reports without opening raw media or executing experiments. The canonical register remains the controlling status source. Approved scopes are preserved narrowly; pending decisions remain pending.

## Consolidated unresolved decision register

| ID | Exact unresolved question | Current status |
|---|---|---|
| `GOV-D1-PROTOCOL-AUTHORITY` | Select HEAD v8/v6 or worktree v9/v7 protocol pair and bind hashes. | Pending |
| `GOV-D2-EVALUATION-PROFILE` | Select implemented v9 or M4 premature-opening profile. | Pending |
| D3(a) | Define second-review triggers, independence, disagreement, and tolerance. | Pending |
| D3(c) | Define audit method/frequency for clear boundaries. | Pending |
| `AUTH-EVENT-SPLIT` | Approve official train/val/test event split. | Pending; artifact absent |
| `GOV-D4-R04-SYNCHRONIZATION` | Accept camera modes, offsets, uncertainty, and event scope. | Pending; artifact absent |
| `EXP-OPERATING-THRESHOLDS` | Scientifically approve threshold/fusion set. | Implemented, not scientifically approved |
| `EXP-ROI-GEOMETRY` | Approve ROI polygons and camera calibration. | Pending |
| `EXP-B7E-PARAMETERS` | Approve numerical delay, target source, and acceptance criteria. | Pending |
| `AUTH-STAGE21-ADJUDICATION` | Authorize genuine human review/pilot/full review. | Pending |
| `AUTH-PROMOTE-EXEC` | Authorize promotion and receipt creation. | Pending |
| `AUTH-EVAL-AUTH` | Authorize official evaluation after all prerequisites. | Pending |

Approved but scope-limited decisions include B7d delivery-layer disorder, B7e delayed-timestamp mechanism, descriptive-only isolation, engine isolation, ground-truth state separation, LEG-EXEC, and Stage-2.1 safeguards.

## Source files inspected

### Governance and gates

- `src/railway_detection/experiments/preflight_validator.py`
- `src/railway_detection/evaluation/protocol_choices.py`
- `src/railway_detection/evaluation/governance.py`
- `src/railway_detection/evaluation/execution_gate.py`
- `src/railway_detection/research_contracts.py`
- `src/railway_detection/annotation/stage2_1_schema.py`
- `src/railway_detection/annotation/promotion_gate.py`
- `src/railway_detection/annotation/evaluation_readiness_gate.py`
- `src/railway_detection/annotation/review_session.py`

### Configuration and synchronization

- `configs/frozen_experiment_v1.yaml`
- `configs/decision_policy_v1.yaml`
- `configs/decision_policy_v2_candidate.yaml`
- `configs/exploratory_dual_camera_v1_supported_subset.yaml`
- `configs/exploratory_dual_camera_v1.1.0_authorized_20261013.yaml`
- `data/manifests/camera_sync_offsets_candidate.yaml`
- `src/railway_detection/data/sync.py`
- `src/railway_detection/data/sync_calibration.py`
- `src/railway_detection/experiments/frozen_config.py`

### Decision/review reports

- `docs/generated/GOVERNANCE_DECISION_RECONCILIATION_20261101_M4A.md`
- `docs/generated/RESEARCHER_DECISION_REGISTER_20261101_M2.md`
- `docs/generated/RESEARCHER_DECISIONS_REQUIRED_20261030_R1.md`
- `docs/generated/PROTOCOL_AUTHORITY_COMPARISON_20261030.md`
- `docs/generated/M4_V9_EVALUATION_PROFILE_COMPARISON_20261030.md`
- `docs/generated/R04_CAMERA_SYNCHRONIZATION_DECISION_20261030.md`
- `docs/generated/R04_EVENT_EVIDENCE_MATRIX_20261029.md`
- `docs/generated/B7D_B7E_PERTURBATION_CONTRACTS_20261030.md`
- `docs/generated/B7D_B7E_END_TO_END_VERIFICATION_20261101_M2.md`
- `docs/generated/RESEARCH_PROTOCOL_DEPENDENCY_MAP_20261030.md`
- `docs/generated/MISSION_4A_HANDOFF_20261101.md`
- `docs/generated/MISSION_4B_HANDOFF_20261101.md`

No raw media was inspected.

## Contradictions requiring researcher awareness

1. Worktree protocol documents use “final/authoritative” language while canonical D1 remains pending.
2. R04 candidate manifest counts 12 supported events, while authorized exploratory configuration contains 11; governance helper reports inconsistency.
3. Historical M4A/readiness prose mentions `delay_s=2.0`, `target_source=camera_front`; canonical B7e numerical parameters remain pending.
4. Preflight parameter classification has compatibility fallbacks that can overclassify thresholds/ROI/B7e parameter presence as approved; this was not changed.
5. `dual_report` appears in historical descriptions but is not currently implemented as a protocol-choice option.
6. Some reproducibility prose records stale timing/threshold values inconsistent with live frozen YAML; live configuration and canonical register were not changed.

## Researcher approval ledger

| Decision | Approval statement | Identity/date |
|---|---|---|
| D1 | __________________________________________ | __________________ |
| D2 | __________________________________________ | __________________ |
| D3(a) | ________________________________________ | __________________ |
| D3(c) | ________________________________________ | __________________ |
| D4 | __________________________________________ | __________________ |
| Thresholds | ___________________________________ | __________________ |
| ROI | __________________________________________ | __________________ |
| B7e parameters | _______________________________ | __________________ |
| Pilot authorization | ___________________________ | __________________ |
| Promotion authorization | _______________________ | __________________ |
| EVAL-AUTH | ____________________________________ | __________________ |

Mission 4C leaves every field blank.