# REGRESSION TEST RESULTS — MISSION 2 (2026-11-01)

- **Document ID**: `REGRESSION_TEST_RESULTS_20261101_M2`
- **Mission**: `MISSION 2 — PIPELINE INTEGRITY VERIFICATION, SAFE REMEDIATION & STAGE-2.1 READINESS`
- **Environment**: `Python 3.11.15`, `pytest-9.1.1` (`.venv/bin/python`)
- **Safety Boundary**: 100% synthetic test fixtures in `tmp_path` or in-memory; zero raw `.mov`, `.mp4`, or `.wav` files opened, decoded, or hashed.

---

## 1. Focused Mission 2 Test Execution Summary

Command executed:
```bash
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/unit/test_mission2_pipeline_integrity.py \
  tests/unit/test_failure_injector.py \
  tests/unit/test_experiment_runner_v2.py \
  tests/unit/test_descriptive_only.py \
  tests/unit/test_event_metrics.py \
  tests/unit/test_phase12_metric_arithmetic.py \
  tests/unit/test_simulation_runner_profiling.py -q
```
- **Result**: **`113 passed in 0.55s` (`0 failed`, `0 skipped`)**

---

## 2. Broad Synthetic & Governance Regression Suite Summary

Command executed:
```bash
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/unit/test_mission2_pipeline_integrity.py \
  tests/unit/test_failure_injector.py \
  tests/unit/test_experiment_runner_v2.py \
  tests/unit/test_descriptive_only.py \
  tests/unit/test_event_metrics.py \
  tests/unit/test_phase12_metric_arithmetic.py \
  tests/unit/test_simulation_runner_profiling.py \
  tests/unit/test_collector_fail_closed_fusion.py \
  tests/unit/test_phase3_sensor_health_decision_policy.py \
  tests/unit/test_decision_engine.py \
  tests/unit/test_independent_safety_invariants.py \
  tests/unit/test_phase10_candidate_policy.py \
  tests/unit/test_cache_only_replay.py \
  tests/unit/test_cache_phase12_adapter.py \
  tests/unit/test_frozen_config_safeguards.py \
  tests/unit/test_phase12_official_replay.py \
  tests/unit/test_phase12_evaluation_runner.py \
  tests/unit/test_phase12_governance.py \
  tests/unit/test_phase12_input_contracts.py \
  tests/unit/test_readiness_audit.py \
  tests/test_fault_injection_scenarios.py \
  tests/test_phase11_2_stage21_promotion_gate.py \
  tests/test_phase11_8_review_workflow_integration.py \
  tests/test_phase11_9_synthetic_pilot.py \
  tests/test_phase11_11_adjudication_session.py \
  tests/test_phase11_12_readiness_gate.py \
  tests/test_phase12_ground_truth_loader.py -q
```
- **Result**: **`611 passed in 12.65s` (`0 failed`, `0 skipped`)**

---

## 3. Mission 2 Test Coverage Breakdown (`tests/unit/test_mission2_pipeline_integrity.py`)

| Test Class / Category | Test Cases | What Is Verified | Status |
| :--- | :---: | :--- | :---: |
| **`TestB7dEndToEnd`** | 4 | Injector swaps adjacent frames -> `EventSimulationRunner(preserve_arrival_order=True)` preserves arrival order -> `MultimodalDecisionEngine` fires `RULE_8_OUT_OF_ORDER_REJECTION` -> runner records frame in `SimulationRunResult.rejected_steps` without stepping `gate_model` or regressing `prev_t` -> `EventMetricsCalculator.evaluate_run` succeeds with `fault_occurred=True`; default `preserve_arrival_order=False` sorts frames; `MultimodalEvidenceCollector.add_evidence_batch(..., preserve_arrival_order=True)` rejects out-of-order observations; `EventMetricsCalculator.evaluate_run` still raises `ValueError("strictly increasing")` on raw unsorted steps. | **PASS (4/4)** |
| **`TestB7eDelayedTimestamps`** | 19 | Rejects missing `delay_s`, `0.0`, `-1.0`, `False`, `True`, `NaN`, `+inf`, `-inf`, non-numeric string; rejects missing/blank/non-string `target_source`; rejects unknown or ambiguous substring `target_source` (`"camera_99"`, `"camera"`, `"front"`, `"unknown_mic"`); verifies valid delay (`1.25s` on `"camera_1"`) shifts only `"camera_1"`, preserves `"camera_2"` and `"audio_1"`, preserves detections/availability, records `original_timestamp_s` in `metadata`, is deterministic, and does not compound under repeated application; verifies `ExperimentRunner.run_condition` fails closed before simulation when `B7e` lacks `failure_schedules`. | **PASS (19/19)** |
| **`TestCacheProvenance`** | 4 | Verifies all 14 `REQUIRED_PROVENANCE_FIELDS` exist and mutating any of the 14 fields changes `provenance_sha256()` and `cache_key()` and raises `CacheProvenanceError("PROVENANCE_MISMATCH")`; verifies controlled JSONL write/load round-trip and checkpoint mismatch rejection; verifies headerless legacy cache is rejected by `load_controlled_cache_jsonl` and `LayerBEventProcessor` (`HISTORICAL_UNVERIFIED_CACHE_REJECTED`) unless `allow_historical_unverified_cache=True` is explicitly passed; verifies raw media extensions (`.mov`, `.mp4`, `.wav`) in provenance are rejected (`RAW_MEDIA_REFERENCE_FORBIDDEN`). | **PASS (4/4)** |
| **`TestGroundTruthAndCohortIsolation`** | 8 | Verifies missing ground truth (`labels=()`) is marked `evaluable=False, notes="ground_truth_missing"` and excluded from both `eligible_events` and `no_train_events` / `false_alarm_evaluable_count`; verifies `censored`, `uncertain`, `unobservable`, `not_applicable`, and `unknown` boundary statuses are never fabricated into numeric timestamps and are recorded in `exclusion_reasons`; verifies multi-cohort run (`train_events`, `no_train_events`, `engine_events`, and missing GT) isolates denominators (`eligible_events=1`, `no_train_events=1`, `engine_events=1`); verifies `clock_aware.evaluate_event_replay` marks `engine_events/event_001` as `evaluable=False, notes="engine_event_excluded"`. | **PASS (8/8)** |
| **`TestDescriptiveOfficialIsolation`** | 4 | Verifies `aggregate_descriptive_only` rejects cross-site generalization and official test-set claims (`FORBIDDEN_CLAIM_SCOPE`); rejects pooling `engine_events/event_001` as evaluable train/no-train (`ENGINE_EVENT_POOLING_REFUSED`) while tracking isolated `engine_case_study_ids`; rejects historical diagnostic outputs claiming controlled experimental status (`HISTORICAL_AS_CONTROLLED_REFUSED`); verifies `load_evaluation_input_manifest` rejects serialized descriptive-only reports. | **PASS (4/4)** |
| **`TestStage21SyntheticValidation`** | 1 | Verifies `check_review_batch_integrity` rejects overlapping review windows under the same reviewer (`OVERLAPPING_REVIEW_SESSIONS`) and `validate_for_promotion` rejects post-review media tampering (`MEDIA_HASH_CHANGED_SINCE_REGISTRY`, `MEDIA_HASH_CHANGED_SINCE_REVIEW`). | **PASS (1/1)** |
