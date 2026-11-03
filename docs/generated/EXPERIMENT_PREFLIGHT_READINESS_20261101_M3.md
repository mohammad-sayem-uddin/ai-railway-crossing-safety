# EXPERIMENT PREFLIGHT READINESS — MISSION 3 (`2026-11-01`)

**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Module:** `src/railway_detection/experiments/preflight_validator.py`  
**Entry Point:** `run_experiment_preflight(...) -> ExperimentPreflightReport`  
**Authority Status:** Strictly diagnostic and non-authoritative (`grants_eval_auth=False`, `grants_official_readiness=False`, `is_diagnostic_only=True`).

---

## 1. Non-Authoritative Synthetic Preflight Validator Design

`run_experiment_preflight` inspects a candidate `FrozenExperimentConfig` and experiment condition specification without touching raw media, modifying repository state, or granting any governance authorization. It categorizes findings into five structured diagnostic tuples:

1. **`structural_errors`**:
   - Invalid `experiment_family`, `evaluation_mode`, `cache_reuse_policy`, or `failure_injector`.
   - Prohibited legacy Audio V2 checkpoint hash (`59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5`) or path (`models/audio/best_checkpoint.pt`) $\rightarrow$ `PROHIBITED_AUDIO_V2_CHECKPOINT`.
   - Malformed or unresolved checkpoint digests.
2. **`missing_configuration_blockers`**:
   - `B7e` / `STALE_TIMESTAMPS` without explicit positive finite `delay_s` and non-empty `target_source` $\rightarrow$ `B7E_PARAMETERS_MISSING` (blocker).
   - Multi-camera vision sources without `SyncAligner` while `allow_unverified_zero_offset=False` $\rightarrow$ `R04_CROSS_CAMERA_SYNC_MISSING` (blocker).
   - Unspecified `roi_config` geometry $\rightarrow$ `ROI_GEOMETRY_UNSPECIFIED` (warning in `provisional_exploratory`, blocker in `official_evaluation`).
3. **`unresolved_scientific_decision_blockers`**:
   - `DECISION_D1_PENDING`: Operating thresholds and multimodal fusion weights remain provisional.
   - `DECISION_D2_PENDING`: Formal ROI polygon and camera calibration acceptance remain pending.
   - `DECISION_D4_PENDING`: Empirical cross-camera synchronization offset acceptance remains pending.
   - `DECISION_B7E_NUMERICAL_PARAMETERS_PENDING`: `B7e` numerical `delay_s` and `target_source` require researcher specification.
4. **`missing_authorization_blockers`**:
   - `STAGE2_1_HUMAN_ADJUDICATION_MISSING`: Independent human Stage-2.1 review records are not completed.
   - `GROUND_TRUTH_PROMOTION_RECEIPT_MISSING`: `data/ground_truth/canonical/` contains zero promoted records.
   - `OFFICIAL_EVENT_SPLIT_MISSING`: No locked official event split exists.
   - `OFFICIAL_EVALUATION_MANIFEST_MISSING`: No official Phase 12 evaluation input manifest exists.
   - `EVAL_AUTH_NOT_GRANTED`: Explicit researcher `EVAL-AUTH` has not been granted.
5. **`required_cache_identities` & `cache_provenance_incompatibilities`**:
   - Enumerates every stream cache required for `(cohort, event_id, source_id, modality)` along with its expected filename, `configuration_sha256`, `cache_identity_sha256`, and `provenance_sha256`.
   - If `cache_dir` is supplied, inspects existing cache files and flags any provenance mismatch, payload corruption, or legacy unverified cache (`HISTORICAL_UNVERIFIED_CACHE_PRESENT`).

---

## 2. Fail-Closed Verification Matrix for Experiment Families `B0`–`B8`

| Experiment Family / Condition | Structural Validity | Current Preflight Readiness (Exploratory / Controlled) | Current Preflight Readiness (Official Evaluation) | Active Blockers |
|---|---|---|---|---|
| **B0** (Vision Only — Front Camera) | VALID | Blocked on controlled cache generation (requires researcher run authorization) | **NOT READY** | `DECISION_D1_PENDING`, `DECISION_D2_PENDING`, `STAGE2_1_HUMAN_ADJUDICATION_MISSING`, `GROUND_TRUTH_PROMOTION_RECEIPT_MISSING`, `EVAL_AUTH_NOT_GRANTED` |
| **B1** (Audio Only — V3 Supporting) | VALID (Audio V3) | Blocked on controlled cache generation | **NOT READY** | Same as B0; Audio V2 strictly blocked (`PROHIBITED_AUDIO_V2_CHECKPOINT`) |
| **B2 / B3 / B4** (Dual-Camera / Multimodal Fusion) | VALID | **BLOCKED (`R04_CROSS_CAMERA_SYNC_MISSING`)** unless `SyncAligner` or `D4` accepted | **NOT READY** | `R04_CROSS_CAMERA_SYNC_MISSING`, `DECISION_D1_PENDING`, `DECISION_D2_PENDING`, `DECISION_D4_PENDING`, Stage-2.1 & `EVAL-AUTH` |
| **B5a–B5c / B6a–B6c** (Camera Failure Injectors) | VALID | Blocked on `R04` (dual-cam) & controlled cache generation | **NOT READY** | `R04_CROSS_CAMERA_SYNC_MISSING`, `D1`, `D2`, `D4`, Stage-2.1 & `EVAL-AUTH` |
| **B7a–B7d, B7f** (Audio Dropout, Frame Drops, False Conf, Delivery Disorder) | VALID (`B7d` arrival-order contract approved) | Blocked on `R04` (dual-cam) & controlled cache generation | **NOT READY** | `R04_CROSS_CAMERA_SYNC_MISSING`, `D1`, `D2`, `D4`, Stage-2.1 & `EVAL-AUTH` |
| **B7e** (Delayed / Stale Timestamps) | VALID contract | **FAIL-CLOSED (`B7E_PARAMETERS_MISSING`)** until `delay_s` and `target_source` are specified | **NOT READY** | `B7E_PARAMETERS_MISSING`, `DECISION_B7E_NUMERICAL_PARAMETERS_PENDING`, `D1`, `D2`, `D4`, Stage-2.1 & `EVAL-AUTH` |
| **B8** (Sensitivity / Threshold Sweep) | VALID | Blocked on `D1` sweep grid & controlled cache generation | **NOT READY** | `DECISION_D1_PENDING`, `DECISION_D2_PENDING`, `DECISION_D4_PENDING`, Stage-2.1 & `EVAL-AUTH` |
