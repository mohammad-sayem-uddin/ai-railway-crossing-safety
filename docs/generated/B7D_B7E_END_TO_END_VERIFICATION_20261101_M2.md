# B7D & B7E END-TO-END VERIFICATION — MISSION 2 (2026-11-01)

- **Document ID**: `B7D_B7E_END_TO_END_VERIFICATION_20261101_M2`
- **Mission**: `MISSION 2 — PIPELINE INTEGRITY VERIFICATION, SAFE REMEDIATION & STAGE-2.1 READINESS`

---

## 1. Objective A1 — B7d Delivery-Layer Disorder End-to-End Verification

### 1.1 Approved Researcher Contract (2026-10-30)
- **B7d = delivery-layer disorder**: The B7d perturbation represents delivery-layer frame-order disorder. The actual frame arrival order must be preserved so that the downstream system can observe the disorder. Do not sort the frames before the relevant collector or Rule 8 ordering-validation logic receives them.

### 1.2 End-to-End Path Trace
1. **Failure Injector (`src/railway_detection/simulation/failure_injector.py:222-233`)**:
   - `FailureMode.OUT_OF_ORDER_FRAMES` swaps two adjacent `MultimodalFrame` objects within `[s.start_time_s, s.end_time_s]` (for `B7d`, `[0.4 * duration, 0.6 * duration]`), producing arrival sequence `[..., frame(t_{k+1}), frame(t_k), frame(t_{k+2}), ...]` where `t_k < t_{k+1}`.
2. **Collector (`src/railway_detection/fusion/collector.py:135-160`)**:
   - `MultimodalEvidenceCollector.add_evidence` tracks `self._last_ingested_master_t[record.source_id]` and rejects any record with `master_t < last_t - 1e-9` into `self.rejected_observations` with `reason="out_of_order_observation"`.
   - `MultimodalEvidenceCollector.add_evidence_batch(records, preserve_arrival_order=False)` preserves historical sorting by default (`preserve_arrival_order=False`) and ingests in exact arrival order when `preserve_arrival_order=True`.
3. **Experiment Runner (`src/railway_detection/experiments/runner.py:310-325`)**:
   - `ExperimentRunner._execute_simulation` sets `preserve_arrival_order = (scenario_id == "B7d")` and passes it to `EventSimulationRunner.run_frames`. All other conditions (`B0`–`B6`, `B7a`–`B7c`, `B7e`, `B7f`) retain `preserve_arrival_order=False`.
4. **Simulation Runner (`src/railway_detection/simulation/runner.py:167-298`)**:
   - When `preserve_arrival_order=True`, `EventSimulationRunner._run_frames` skips `frame_sorting` and feeds frames in delivery order to `self.decision_engine.evaluate_frame`.
5. **Rule 8 Ordering Validation (`src/railway_detection/fusion/decision_engine.py:114-133`)**:
   - When `frame(t_{k+1})` arrives, `self.last_master_time_s` advances to `t_{k+1}`.
   - When the delayed `frame(t_k)` (`t_k < t_{k+1} - 1e-9`) arrives next, `MultimodalDecisionEngine.evaluate_frame` fires `RuleId.RULE_8_OUT_OF_ORDER_REJECTION`:
     - Does **not** advance `self.last_master_time_s` (remains `t_{k+1}`).
     - Does **not** mutate `self.current_state` or dwell counters.
     - Returns `DecisionRecord` with `rule_id="RULE_8_OUT_OF_ORDER_REJECTION"`, `fault_status="out_of_order"`, `timestamp_s=t_k`.
6. **Simulation Runner Rejection Handling (Remediated in Mission 2)**:
   - **Previous Defect**: Prior to Mission 2, `EventSimulationRunner._run_frames` appended the Rule-8-rejected frame into `SimulationRunResult.steps` and executed `prev_t = t_k`, regressing the simulation clock, double-counting `dt = t_{k+2} - t_k` on the next frame, and causing `EventMetricsCalculator.evaluate_run` to crash with `ValueError("simulation steps must have finite, strictly increasing timestamps")`.
   - **Mission 2 Fix**: When `decision.rule_id in (RuleId.RULE_8_OUT_OF_ORDER_REJECTION.value, RuleId.RULE_10_DUPLICATE_FRAME_REJECTION.value)`, `EventSimulationRunner._run_frames`:
     - Sets `fault_seen = True`.
     - Records the `SimulationStep` in `SimulationRunResult.rejected_steps` (and increments `metrics["rejected_step_count"]` and `metrics["out_of_order_rejected_count"]`).
     - Does **not** step `gate_model`, does **not** add to `total_closed_time`, does **not** append to `SimulationRunResult.steps`, and does **not** overwrite `prev_t` (`prev_t` stays at `t_{k+1}`).
7. **Metric Layer (`src/railway_detection/evaluation/metrics.py:266-273`)**:
   - `EventMetricsCalculator.evaluate_run` retains its strict monotonic timestamp invariant on `sim_result.steps` and evaluates the B7d run cleanly (`fault_occurred=True`).

---

## 2. Objective A2 — B7e Delayed Timestamp (`STALE_TIMESTAMPS`) Verification

### 2.1 Approved Researcher Contract (2026-10-30)
- **B7e = delayed timestamp**: Frame content remains unchanged while timestamps are shifted according to explicitly configured parameters. Do not invent numerical delay values, ranges, camera scopes, or operational acceptance thresholds.

### 2.2 Verification Matrix for `FailureMode.STALE_TIMESTAMPS`

| Requirement | Implementation in `src/railway_detection/simulation/failure_injector.py` | Synthetic Test Coverage |
| :--- | :--- | :--- |
| 1. `delay_s` explicitly supplied | `_validate_stale_timestamps_schedule` checks `sched.parameters.get("delay_s")` upfront before frame iteration. | `test_invalid_or_missing_delay_rejected[None]` |
| 2. `target_source` explicitly supplied | Checks `sched.target_source or sched.parameters.get("target_source")`; must be a non-empty string. | `test_missing_or_invalid_target_source_rejected` |
| 3. Missing values fail closed | Raises `ValueError` both in `FailureInjector.inject_failures` and in `ExperimentRunner.run_condition`. | `test_experiment_runner_b7e_without_schedule_fails_closed_before_simulation` |
| 4. Non-finite values rejected | Rejects `NaN`, `+inf`, `-inf`, `bool`, and non-numeric values via `math.isfinite`. | `test_invalid_or_missing_delay_rejected[nan/inf/-inf/True/False]` |
| 5. Zero and negative delays rejected | Enforces `delay_val > 0.0`. | `test_invalid_or_missing_delay_rejected[0.0/-1.0]` |
| 6. Unknown / substring `target_source` rejected | Validates `target_source in known_sources` and matches records by exact equality `r.source_id == target_source`. Substrings like `"camera"` or `"front"` are rejected. | `test_unknown_or_ambiguous_substring_source_rejected` |
| 7. Only timestamps changed; frame & detection content preserved | `_shift_record_timestamp` uses `dataclasses.replace` on matching `EvidenceRecord`s only; `detections`, `available`, `modality`, `frame.master_timestamp_s`, and other sources remain identical. | `test_valid_delay_shifts_only_target_source_and_preserves_content_and_trace` |
| 8. Deterministic transformation | Pure function of `(frames, schedule)` with no PRNG involvement. | `test_valid_delay_shifts_only_target_source_and_preserves_content_and_trace` |
| 9. Repeated invocation does not compound delay | Reads `orig_ts = float(record.metadata.get("original_timestamp_s", record.timestamp_s))` and sets `timestamp_s = orig_ts - delay_s`. | `test_valid_delay_shifts_only_target_source_and_preserves_content_and_trace` |
| 10. Original timestamps traceable in synthetic fixtures | Stores `record.metadata["original_timestamp_s"] = orig_ts` and `record.metadata["stale_timestamp_delay_s"] = delay_s`. | `test_valid_delay_shifts_only_target_source_and_preserves_content_and_trace` |
