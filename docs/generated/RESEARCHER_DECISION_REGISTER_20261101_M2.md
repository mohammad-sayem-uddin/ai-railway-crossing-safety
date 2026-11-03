# RESEARCHER DECISION REGISTER — MISSION 2 (2026-11-01)

- **Document ID**: `RESEARCHER_DECISION_REGISTER_20261101_M2`
- **Mission**: `MISSION 2 — PIPELINE INTEGRITY VERIFICATION, SAFE REMEDIATION & STAGE-2.1 READINESS`
- **Repository**: `/Users/sayemuddin/Desktop/Train_automation`
- **Branch / HEAD**: `main` @ `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
- **Audit Mode**: Append-only researcher decision record

---

## 1. Purpose and Verification Summary

Per Section 3 of the Mission 2 specification, the repository was inspected to determine whether the four researcher decisions approved on `2026-10-30` were already recorded as approved in existing governance or documentation files.

### Verification Finding
In `docs/generated/RESEARCHER_DECISION_PACKET_20261030_R1.md`, `docs/generated/RESEARCHER_DECISIONS_REQUIRED_20261030_R1.md`, `docs/generated/B7D_B7E_PERTURBATION_CONTRACTS_20261030.md`, `docs/generated/DESCRIPTIVE_VS_OFFICIAL_EVALUATION_DECISION_20261030.md`, and `docs/generated/ENGINE_EVENT_TREATMENT_DECISION_20261030.md`, those items were still listed as `PROPOSED — NOT APPROVED` or pending confirmation. No existing file under `docs/` or `data/governance/` recorded the `2026-10-30` researcher approvals.

Accordingly, this append-only register records the exact approved researcher decisions and wording as of `2026-10-30` without overwriting any historical decision packet, and explicitly preserves all remaining pending decisions as unresolved.

---

## 2. Approved Researcher Decisions (Approved Date: 2026-10-30)

### Decision 1 — `B7d = delivery-layer disorder`
- **Approval Date**: `2026-10-30`
- **Status**: **APPROVED (Researcher Decision)**
- **Approved Wording**:
  > **B7d = delivery-layer disorder**
  >
  > The B7d perturbation represents delivery-layer frame-order disorder.
  >
  > The actual frame arrival order must be preserved so that the downstream system can observe the disorder.
  >
  > Do not sort the frames before the relevant collector or Rule 8 ordering-validation logic receives them.
- **Software Implementation Binding**:
  - `src/railway_detection/simulation/failure_injector.py` (`FailureMode.OUT_OF_ORDER_FRAMES`)
  - `src/railway_detection/fusion/collector.py` (`MultimodalEvidenceCollector.add_evidence_batch(..., preserve_arrival_order=True)`)
  - `src/railway_detection/experiments/runner.py` (`ExperimentRunner._execute_simulation` passes `preserve_arrival_order=(scenario_id == "B7d")`)
  - `src/railway_detection/simulation/runner.py` (`EventSimulationRunner._run_frames` preserves arrival order when `preserve_arrival_order=True`, routes frames to `MultimodalDecisionEngine.evaluate_frame` where `RULE_8_OUT_OF_ORDER_REJECTION` rejects out-of-order frames, and records rejected frames in `SimulationRunResult.rejected_steps` without corrupting `prev_t` or `SimulationRunResult.steps`)

### Decision 2 — `B7e = delayed timestamp`
- **Approval Date**: `2026-10-30`
- **Status**: **APPROVED (Researcher Decision — Mechanism Only; Numerical Parameters Pending)**
- **Approved Wording**:
  > **B7e = delayed timestamp**
  >
  > The B7e perturbation represents delayed frame timestamps.
  >
  > Frame content remains unchanged while timestamps are shifted according to explicitly configured parameters.
  >
  > Do not invent numerical delay values, ranges, camera scopes, or operational acceptance thresholds.
- **Software Implementation Binding**:
  - `src/railway_detection/simulation/failure_injector.py` (`FailureMode.STALE_TIMESTAMPS` requires explicit positive finite `delay_s` and explicit known `target_source`, matches exact `r.source_id == target_source`, preserves frame and detection content, records `original_timestamp_s` in `r.metadata`, and is idempotent under repeated invocation)
  - `src/railway_detection/experiments/runner.py` (`ExperimentRunner.run_condition` and `_get_failure_schedules` fail closed when `B7e` is invoked without explicit `failure_schedules`)

### Decision 3 — `D3 = descriptive-only evaluation`
- **Approval Date**: `2026-10-30`
- **Status**: **APPROVED (Researcher Decision)**
- **Approved Wording**:
  > **D3 = descriptive-only evaluation**
  >
  > A separate descriptive-only evaluation mode is approved.
  >
  > It must remain isolated from the official evaluation workflow.
  >
  > It must not create an artificial train/validation/test split or be described as official test-set performance.
  >
  > Claims must remain fixed-site descriptive claims. No cross-site generalization claims.
- **Software Implementation Binding**:
  - `src/railway_detection/evaluation/descriptive_only.py` (`DescriptiveOnlyInput`, `DescriptiveOnlyReport`, `aggregate_descriptive_only`)
  - Enforces `official_evaluation_eligible = False`, requires `EvidenceClassification.SYNTHETIC`, rejects cross-site generalization or official test-set claims (`FORBIDDEN_CLAIM_SCOPE`), isolates `engine_events/event_001` (`engine_case_study_ids`), and is rejected by all official Phase 12 manifest and runner entry points.

### Decision 4 — `Engine event = isolated case study`
- **Approval Date**: `2026-10-30`
- **Status**: **APPROVED (Researcher Decision)**
- **Approved Wording**:
  > **Engine event = isolated case study**
  >
  > `engine_events/event_001` must remain separate from train-event denominators and train-event aggregates.
  >
  > It may be discussed as a separate case study.
  >
  > Do not pool it into train-event results without a separate future researcher decision.
- **Software Implementation Binding**:
  - `src/railway_detection/evaluation/metrics.py` (`EventMetricsCalculator.evaluate_run`, `EventMetricsCalculator.aggregate_cohort`)
  - `src/railway_detection/evaluation/clock_aware.py` (`evaluate_event_replay`)
  - `src/railway_detection/experiments/runner.py` (`ExperimentRunner._extract_event_ground_truth`)
  - `src/railway_detection/evaluation/descriptive_only.py` (`aggregate_descriptive_only`)
  - `src/railway_detection/evaluation/evaluation_runner.py` (`Phase12EvaluationRunner.run`)

---

## 3. Pending Researcher Decisions (Do Not Resolve Without Researcher Authorization)

The following scientific and governance decisions remain **PENDING** as of `2026-11-01` and have NOT been resolved or defaulted in code:

| Decision ID | Topic | Current Status | Code Enforcement |
| :--- | :--- | :--- | :--- |
| **D1** | Protocol authority: committed `v8.0.0` / ground truth `v6.0.0` vs worktree `v9.0.0` / ground truth `v7.0.0` | **PENDING RESEARCHER DECISION** | Unmodified; both committed and worktree protocol states are preserved and documented. |
| **D2** | Premature opening definition: `M4` (`first_blocked_to_t4_clearance`) vs `v9` (`t1_entry_to_t4_clearance`) | **PENDING RESEARCHER DECISION** | `premature_opening_window` defaults to `None` (`"undecided"`); `Phase12EvaluationRunner` blocks with `PREMATURE_OPENING_DEFINITION_UNDECIDED` until `data/manifests/phase12_protocol_decision.json` is recorded by the researcher. |
| **D4** | R04 camera synchronization scope and acceptance criteria (`12` `CALIBRATION_SUPPORTED`, `7` `PROVISIONAL`, `8` `AMBIGUOUS`) | **PENDING RESEARCHER DECISION** | `data/manifests/phase12_r04_scope_decision.json` is absent; `SyncAligner` is required for cross-camera fusion; `R04_SCOPE_DECISION_MISSING` blocks official dual-camera execution. |
| **B7e Parameters** | Numerical delay magnitude/range (`delay_s`), target source/camera scope (`target_source`), and operational acceptance criteria | **PENDING RESEARCHER DECISION** | No default `delay_s` or `target_source` exists in code; `B7e` fails closed unless explicit parameters are supplied. |
| **Stage-2.1 Human Review** | Human adjudication of the 27 Layer B events under schema `8.1.0-stage2.1` and issuance of `data/governance/stage21_promotion_receipt.json` | **PENDING HUMAN REVIEW** | 0 valid `8.1.0-stage2.1` records exist in `data/ground_truth/reviews/`; all 27 legacy `7.0.0` records are rejected (`LEGACY_OR_UNKNOWN_SCHEMA`). |
| **Official Event Split & EVAL-AUTH** | `data/splits/phase12_event_split_decision.json`, `data/manifests/phase12_evaluation_inputs.json`, and `data/governance/eval_authorization.json` | **PENDING RESEARCHER AUTHORIZATION** | All three files are absent; `assess_official_phase12_readiness` returns `ready=False` with 5 blockers. |
