# MISSION 2 HANDOFF REPORT (2026-11-01)

- **Document ID**: `MISSION_2_HANDOFF_20261101`
- **Mission**: `MISSION 2 — PIPELINE INTEGRITY VERIFICATION, SAFE REMEDIATION & STAGE-2.1 READINESS`
- **Repository**: `/Users/sayemuddin/Desktop/Train_automation`
- **Branch / HEAD**: `main` @ `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`

---

## 1. Executive Summary

Mission 2 verified the actual code implementation against the `2026-10-30` (`R1`) handoff reports, identified four substantive architectural and scientific-safety defects that remained in the simulation, perturbation, ground-truth, and cache layers, implemented minimal fail-closed remediations, verified all fixes with 611 passing synthetic unit/integration tests, recorded the `2026-10-30` approved researcher decisions in an append-only register, and prepared the Stage-2.1 human-review readiness workflow without violating any research safety boundary.

---

## 2. Key Architectural Findings and Remediations

1. **B7d End-to-End Fault Handling (`src/railway_detection/simulation/runner.py`, `src/railway_detection/fusion/collector.py`)**:
   - **Finding**: While `MultimodalDecisionEngine.evaluate_frame` triggered `RULE_8_OUT_OF_ORDER_REJECTION`, `EventSimulationRunner._run_frames` previously appended the rejected out-of-order frame into `SimulationRunResult.steps` and overwrote `prev_t = t` with the regressed timestamp, double-counting `dt` on the next frame and crashing `EventMetricsCalculator.evaluate_run` with `ValueError("simulation steps must have finite, strictly increasing timestamps")`.
   - **Remediation**: `EventSimulationRunner._run_frames` now records `RULE_8_OUT_OF_ORDER_REJECTION` and `RULE_10_DUPLICATE_FRAME_REJECTION` frames in `SimulationRunResult.rejected_steps` without stepping `gate_model`, adding to `total_closed_time`, or regressing `prev_t`. `MultimodalEvidenceCollector.add_evidence_batch` also supports `preserve_arrival_order: bool = False`. `EventMetricsCalculator.evaluate_run` retains its strict monotonic step check and evaluates B7d runs cleanly.
2. **B7e Delayed Timestamp Hardening (`src/railway_detection/simulation/failure_injector.py`, `src/railway_detection/experiments/runner.py`)**:
   - **Finding**: `FailureMode.STALE_TIMESTAMPS` previously used substring matching (`target_source in r.source_id`), allowing `target_source="camera"` to mutate multiple cameras and unknown sources to no-op; compounded delays on repeated invocation; did not trace `original_timestamp_s`; and checked `failure_schedules` in `ExperimentRunner.run_condition` only after running simulation.
   - **Remediation**: `FailureInjector.inject_failures` validates all `STALE_TIMESTAMPS` schedules upfront, rejects unknown or substring `target_source`, matches exact `r.source_id == target_source`, records `original_timestamp_s` in `r.metadata`, and shifts `orig_ts - delay_s` idempotently. `ExperimentRunner` fails closed upfront when `B7e` lacks explicit `failure_schedules`.
3. **Ground-Truth State & Cohort Isolation (`src/railway_detection/evaluation/metrics.py`, `src/railway_detection/evaluation/clock_aware.py`, `src/railway_detection/experiments/runner.py`)**:
   - **Finding**: `ExperimentRunner.run_condition` previously passed `has_train_ground_truth=bool(event.labels)`, turning missing ground truth (`event.labels == ()`) into `has_train_ground_truth=False` (a confirmed no-train negative control!), extracted non-observable boundary timestamps (`censored`, `uncertain`, `unobservable`), and `clock_aware.evaluate_event_replay` labeled `engine_events` as `"no_false_alarm"` / `"false_alarm_evaluation"` instead of `"engine_event_excluded"`.
   - **Remediation**: Implemented `ExperimentRunner._extract_event_ground_truth`, updated `EventMetricsCalculator.evaluate_run` and `aggregate_cohort`, and updated `clock_aware.evaluate_event_replay` so confirmed train, confirmed no-train, engine, missing, unknown, censored, unobservable, uncertain, and not-applicable states are strictly distinguished and `engine_events/event_001` and missing-ground-truth events never leak into train or negative-control denominators.
4. **14-Field Controlled Cache Provenance (`src/railway_detection/experiments/cache_provenance.py`, `src/railway_detection/experiments/layer_b_processor.py`)**:
   - **Finding**: `LayerBEventProcessor` previously constructed cache filenames without model, checkpoint, preprocessing, config, injector, timing, schema, software, or run identity and reused legacy caches unconditionally.
   - **Remediation**: Implemented `ControlledCacheProvenance` binding all 14 required identity fields with canonical SHA-256 digests and JSONL provenance envelopes. `LayerBEventProcessor` now rejects headerless legacy caches by default (`HISTORICAL_UNVERIFIED_CACHE_REJECTED`) unless `allow_historical_unverified_cache=True` is explicitly requested for historical diagnostic inspection.
5. **Descriptive-Only vs. Official Evaluation Isolation (`src/railway_detection/evaluation/descriptive_only.py`)**:
   - **Remediation**: Strengthened `descriptive_only.py` to reject cross-site generalization or official test-set claims (`FORBIDDEN_CLAIM_SCOPE`), reject `engine_events` pooling (`ENGINE_EVENT_POOLING_REFUSED`), expose `engine_case_study_ids`, and reject historical-as-controlled misrepresentations (`HISTORICAL_AS_CONTROLLED_REFUSED`).

---

## 3. Mission 2 Generated Documentation Index

1. `docs/generated/PIPELINE_INTEGRITY_AUDIT_20261101_M2.md`
2. `docs/generated/CACHE_PROVENANCE_VERIFICATION_20261101_M2.md`
3. `docs/generated/B7D_B7E_END_TO_END_VERIFICATION_20261101_M2.md`
4. `docs/generated/GROUND_TRUTH_AND_COHORT_ISOLATION_20261101_M2.md`
5. `docs/generated/DESCRIPTIVE_OFFICIAL_ISOLATION_AUDIT_20261101_M2.md`
6. `docs/generated/STAGE21_HUMAN_REVIEW_READINESS_20261101_M2.md`
7. `docs/generated/REGRESSION_TEST_RESULTS_20261101_M2.md`
8. `docs/generated/RESEARCHER_DECISION_REGISTER_20261101_M2.md`
9. `docs/generated/MISSION_2_HANDOFF_20261101.md`

---

## 4. Exact Next Actions Required from the Researcher

1. **Resolve Pending Scientific Decisions**:
   - **D1**: Select authoritative protocol baseline (`v8.0.0` / GT `v6.0.0` vs. worktree `v9.0.0` / GT `v7.0.0`).
   - **D2**: Select premature opening definition (`M4: first_blocked_to_t4_clearance` vs. `v9: t1_entry_to_t4_clearance`) and record `data/manifests/phase12_protocol_decision.json`.
   - **D4**: Decide R04 camera synchronization scope (`single_camera`, `independent_camera`, or `dual_camera` for the 12 `CALIBRATION_SUPPORTED` events) and record `data/manifests/phase12_r04_scope_decision.json`.
   - **B7e Numerical Parameters**: Specify `delay_s` magnitude/sweep values, `target_source` camera scope, and operational acceptance criteria for controlled B7e runs.
2. **Execute Stage-2.1 Human Ground-Truth Review**:
   - Authorize `LEG-EXEC` (if excusing the 27 invalidated `7.0.0` records in-place) and conduct human frame-by-frame / spectral-audio adjudication of the 27 Layer B events under schema `8.1.0-stage2.1` following `docs/generated/STAGE21_HUMAN_REVIEW_READINESS_20261101_M2.md`.
   - Run `railway_detection.annotation.readiness_cli` to verify live media hashes and generate `data/governance/stage21_promotion_receipt.json`.
3. **Authorize Controlled Reruns or Official Evaluation**:
   - For descriptive-only fixed-site analysis: run controlled cache generation with `ControlledCacheProvenance` and aggregate via `aggregate_descriptive_only`.
   - For official Phase 12 evaluation: record `data/splits/phase12_event_split_decision.json`, build `data/manifests/phase12_evaluation_inputs.json`, and record `data/governance/eval_authorization.json` (`EVAL-AUTH`).
