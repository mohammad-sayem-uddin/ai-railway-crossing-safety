# RESEARCH GOVERNANCE STATUS — MISSION 3 (`2026-11-01`)

**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Branch / HEAD:** `main` @ `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Audit Date:** `2026-11-01`

---

## 1. Preserved Researcher Decisions (`2026-10-30`)

All five researcher decisions approved on `2026-10-30` and recorded in `docs/generated/RESEARCHER_DECISION_REGISTER_20261101_M2.md` remain intact and enforced in code:

| Decision ID | Summary | Code Enforcement Location | Status |
|---|---|---|---|
| **B7d (`DECISION_20261030_B7D`)** | Delivery-layer frame arrival disorder (`received_timestamp_s` arrival order distinct from payload `frame_timestamp_s` and `processing_timestamp_s`; `EventMetricsCalculator` unweakened). | `src/railway_detection/simulation/failure_injector.py`, `src/railway_detection/simulation/runner.py`, `src/railway_detection/fusion/collector.py` | **APPROVED & ENFORCED** |
| **B7e (`DECISION_20261030_B7E`)** | Delayed-timestamp staleness contract (`received_timestamp_s - frame_timestamp_s > source_staleness_s`); fails closed when `delay_s` or `target_source` is omitted. | `src/railway_detection/simulation/failure_injector.py`, `src/railway_detection/experiments/cache_provenance.py`, `src/railway_detection/experiments/runner.py`, `src/railway_detection/experiments/preflight_validator.py` | **CONTRACT APPROVED; NUMERICAL PARAMS PENDING** |
| **Ground-Truth State Separation** | `TRAIN_EVENT`, `NEGATIVE_CONTROL_SAFE_BASELINE`, `ENGINE_INSPECTION_EXCLUDED`, plus non-observable boundary states (`censored`, `unobservable`, `uncertain`, `not_applicable`, `unknown`) never fabricated into timestamps. | `src/railway_detection/experiments/runner.py`, `src/railway_detection/evaluation/metrics.py` | **APPROVED & ENFORCED** |
| **Engine-Event Isolation** | `engine_events` (`Engine_001`–`Engine_003`) isolated as case studies (`has_train_ground_truth=False`, `evaluable=False`, `notes="engine_event_excluded"`) and excluded from train sensitivity and negative-control FAR denominators. | `src/railway_detection/experiments/runner.py`, `src/railway_detection/evaluation/clock_aware.py`, `src/railway_detection/evaluation/descriptive_only.py`, `src/railway_detection/evaluation/metrics.py` | **APPROVED & ENFORCED** |
| **Descriptive-Only Evaluation Isolation** | Fixed-site descriptive summaries (`aggregate_descriptive_only`) isolated from official Phase 12 evaluation (`official_evaluation_eligible=False`, cross-site/generalization claims refused, controlled provenance validated). | `src/railway_detection/evaluation/descriptive_only.py`, `src/railway_detection/evaluation/input_contracts.py` | **APPROVED & ENFORCED** |

---

## 2. Pending Researcher Scientific Decisions (Unresolved)

Mission 3 did **not** make any scientific decisions on the researcher's behalf. The following decisions remain explicitly classified as `unresolved_configuration` in `preflight_validator.py`:

| Decision ID | Decision Scope | Current Software State | Required Researcher Action |
|---|---|---|---|
| **D1** | Final operating thresholds (`confidence_threshold_approach`, `confidence_threshold_departure`, `audio.operating_threshold`) and multimodal fusion weights (`w_v1`, `w_v2`, `w_a`). | Provisional values in `configs/frozen_experiment_v1.yaml`; tagged `unresolved_configuration`. | Approve final operating thresholds and fusion weights after exploratory/validation analysis. |
| **D2** | Formal danger-zone ROI polygon geometry and camera calibration acceptance. | Optional `roi_config` validated and hashed in `ControlledCacheProvenance`; tagged `unresolved_configuration` when absent. | Define and approve per-camera ROI polygons and calibration parameters. |
| **D4** | Empirical cross-camera synchronization offset calibration acceptance (`camera_1` vs `camera_2` start-time offsets up to 33 s). | `allow_unverified_zero_offset: False` blocks uncalibrated dual-camera fusion (`R04 TimingIntegrityError`). | Complete timing calibration pilot and approve per-event `SyncAligner` offsets or synchronization policy. |
| **B7e Numerical Parameters** | Specific `delay_s` value(s) and `target_source` (`camera_1`, `camera_2`, `audio_1`) for the official B7e delayed-timestamp experiment. | Fails closed (`PROVENANCE_INJECTOR_INVALID` / `B7E_PARAMETERS_MISSING`) when omitted. | Specify exact `delay_s` and `target_source` schedule(s) for B7e. |

---

## 3. Four-Category Evidence Classification & Governance Boundaries

All modules strictly distinguish four evidence categories and prevent any category from masquerading as another:

1. **Historical Diagnostic Outputs (`historical_diagnostic` / `HISTORICAL_DIAGNOSTIC_UNVERIFIED`)**:
   - Legacy caches in `results/cache/` without `__cache_provenance__` headers and historical experiment artifacts in `results/layer_b_experiments/` and `results/phase8_complete/`.
   - Preserved untouched; rejected by `load_controlled_cache_jsonl` unless loaded via `load_historical_diagnostic_cache_jsonl` with `official_evaluation_eligible=False`.
2. **Synthetic Test Outputs (`synthetic_test_configuration` / `EvidenceClassification.SYNTHETIC`)**:
   - Generated exclusively in temporary test directories (`tmp_path`) during unit/regression testing.
3. **Future Controlled Experiment Outputs (`controlled_experimental`)**:
   - Require `ControlledCacheProvenance` (`layer-b-controlled-cache/2.0.0`) with verified 14-field identity, `configuration_sha256`, `cache_identity_sha256`, `provenance_sha256`, `record_count`, and `payload_sha256`, plus reconstructable `ExperimentConfigurationSpec` (`experiment-spec/1.0`) in `frozen_config_meta.json`.
   - Still carry `official_evaluation_eligible=False` until Stage-2.1, split, manifest, and `EVAL-AUTH` are satisfied.
4. **Official Evaluation Outputs (`official_evaluation`)**:
   - Currently **BLOCKED** fail-closed (`ready=False`). Requires completed Stage-2.1 human review records (`8.1.0-stage2.1`), canonical ground-truth promotion receipts (`data/ground_truth/canonical/`), locked official event split, official Phase 12 evaluation manifest, and explicit `EVAL-AUTH`.
