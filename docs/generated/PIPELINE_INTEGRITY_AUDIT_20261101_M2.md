# PIPELINE INTEGRITY AUDIT — MISSION 2 (2026-11-01)

- **Document ID**: `PIPELINE_INTEGRITY_AUDIT_20261101_M2`
- **Mission**: `MISSION 2 — PIPELINE INTEGRITY VERIFICATION, SAFE REMEDIATION & STAGE-2.1 READINESS`
- **Repository**: `/Users/sayemuddin/Desktop/Train_automation`
- **Branch / HEAD**: `main` @ `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`

---

## 1. Initial Repository and Working-Tree State

Before any Mission 2 inspection or modification:
- **Git Branch**: `main`
- **HEAD Commit**: `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (`Initial baseline commit: railway crossing perception, audio-visual fusion, and layer B annotation framework`)
- **Tracked Modified Files**: `19` (`1174 insertions(+), 157 deletions(-)`)
  - `README.md`
  - `docs/FINAL_ABLATION_MATRIX.md`
  - `docs/FINAL_EXPERIMENT_DATA_FLOW.md`
  - `docs/FINAL_GROUND_TRUTH_PROTOCOL.md`
  - `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`
  - `pyproject.toml`
  - `src/railway_detection/audio/__init__.py`
  - `src/railway_detection/cli/main.py`
  - `src/railway_detection/data/layer_b.py`
  - `src/railway_detection/data/sync.py`
  - `src/railway_detection/demo/server.py`
  - `src/railway_detection/evaluation/__init__.py`
  - `src/railway_detection/fusion/evidence.py`
  - `src/railway_detection/vision/video.py`
  - `tests/fixtures/mock_events.py`
  - `tests/unit/test_audio_v2_pipeline.py`
  - `tests/unit/test_dashboard_server.py`
  - `tests/unit/test_layer_b_loader.py`
  - `tests/unit/test_real_dataset_inventory.py`
- **Untracked Paths**: `349` top-level `??` entries (`10,305` total untracked files with `git status --porcelain=v1 -uall`).
- **Preservation Verification**: All `19` tracked user-modified files and all pre-existing untracked files, datasets, and historical reports were left 100% intact. None of the 19 tracked modified files required edits during Mission 2.

---

## 2. Audit of Previous Mission (`2026-10-30` / `R1`) Claims vs. Actual Code

All eight previous mission reports (`CORE_PIPELINE_IMPLEMENTATION_HANDOFF_20261030.md`, `REGRESSION_TEST_RESULTS_20261030_R1.md`, `FORENSIC_REMEDIATION_IMPLEMENTATION_20261030_R1.md`, `EXPERIMENT_RECOVERY_AND_RERUN_PLAN_20261030_R1.md`, `EXPERIMENT_DEFECT_IMPACT_MATRIX_20261030_R1.md`, `RESEARCHER_DECISIONS_REQUIRED_20261030_R1.md`, `RESEARCHER_DECISION_PACKET_20261030_R1.md`, `IMPLEMENTATION_READINESS_PLAN_20261030_R1.md`) were cross-checked against the actual implementation in `src/` and `tests/`.

| Audit Area | Previous Report Claim | Actual Code Finding Prior to Mission 2 Remediation | Mission 2 Action Taken |
| :--- | :--- | :--- | :--- |
| **A1. B7d Arrival-Order Preservation** | Claimed `preserve_arrival_order` allowed B7d to reach Rule 8 and that raising `ValueError("simulation steps must have finite, strictly increasing timestamps")` in `EventMetricsCalculator` proved end-to-end B7d handling. | **Architectural Defect Found**: `MultimodalDecisionEngine.evaluate_frame` correctly triggered `RULE_8_OUT_OF_ORDER_REJECTION`, but `EventSimulationRunner._run_frames` (`src/railway_detection/simulation/runner.py:183-243`) still appended the rejected out-of-order frame to `SimulationRunResult.steps` and overwrote `prev_t = t` with the regressed timestamp, corrupting subsequent `dt` calculations and causing `EventMetricsCalculator.evaluate_run` to crash. Additionally, `MultimodalEvidenceCollector.add_evidence_batch` (`src/railway_detection/fusion/collector.py:154-157`) unconditionally sorted batches. | **Remediated & Verified**: `EventSimulationRunner._run_frames` now isolates Rule 8 (`RULE_8_OUT_OF_ORDER_REJECTION`) and Rule 10 (`RULE_10_DUPLICATE_FRAME_REJECTION`) frames in `SimulationRunResult.rejected_steps` without stepping `gate_model`, accumulating `total_closed_time`, or regressing `prev_t`. `MultimodalEvidenceCollector.add_evidence_batch` now supports `preserve_arrival_order: bool = False`. `EventMetricsCalculator.evaluate_run` remains strict and evaluates B7d runs cleanly. |
| **A2. B7e Delayed Timestamps (`STALE_TIMESTAMPS`)** | Claimed `FailureMode.STALE_TIMESTAMPS` was hardened to fail closed and isolate `target_source`. | **Three Gaps Found**: (1) `failure_injector.py:170-181` used substring matching (`target_source in r.source_id`) instead of exact equality (`r.source_id == target_source`), allowing `target_source="camera"` to mutate both cameras and unknown sources to silently no-op; (2) repeated invocation compounded delays (`t - 2 * delay_s`) and did not record `original_timestamp_s`; (3) `ExperimentRunner._get_failure_schedules` still returned an unparameterized `STALE_TIMESTAMPS` schedule and `run_condition` checked `failure_schedules` only after simulation. | **Remediated & Verified**: `FailureInjector.inject_failures` validates all `STALE_TIMESTAMPS` schedules upfront, rejects unknown or substring `target_source`, matches exact `r.source_id == target_source`, records `original_timestamp_s` in `r.metadata`, and computes `orig_ts - delay_s` idempotently. `ExperimentRunner` fails closed immediately when `B7e` lacks explicit `failure_schedules`. |
| **A3 & C. Ground-Truth State Safety & Cohort Isolation** | Claimed `premature_opening_window=None` prevented profile assumptions and that cohorts were separated. | **Critical Defect Found**: In `ExperimentRunner.run_condition` (`src/railway_detection/experiments/runner.py:114-144`), `has_train_ground_truth=bool(event.labels)` converted events with **missing** ground truth (`event.labels == ()`) into `has_train_ground_truth=False`, causing `EventMetricsCalculator.evaluate_run` to evaluate missing ground truth as a **confirmed no-train negative control** (`false_alarm_evaluation` / `no_false_alarm`)! Furthermore, non-observable label statuses (`censored`, `uncertain`, `unobservable`) were not filtered out when `timestamp_s` was present, and `clock_aware.evaluate_event_replay` labeled `engine_events` as `"no_false_alarm"` / `"false_alarm_evaluation"` instead of `"engine_event_excluded"`. | **Remediated & Verified**: `EventMetricsCalculator.evaluate_run`, `EventMetricsCalculator.aggregate_cohort`, `clock_aware.evaluate_event_replay`, and `ExperimentRunner._extract_event_ground_truth` now distinguish confirmed train, confirmed no-train, engine, missing, unknown, censored, unobservable, uncertain, and not-applicable states. Missing/unknown ground truth is marked `evaluable=False, notes="ground_truth_missing"` and excluded from both train and negative-control denominators. `engine_events/event_001` is isolated across all paths. |
| **B. Cache Provenance & Reproducibility** | Previous audit noted `LayerBEventProcessor` cache key omissions as a defect (`D-02`) but did not implement controlled-run cache provenance verification. | **Gap Confirmed**: `LayerBEventProcessor` (`src/railway_detection/experiments/layer_b_processor.py:183, 252`) used bare `{cohort}_{event}_{stem}_{source_id}_vision.jsonl` filenames with no provenance header and reused them by default (`use_cache=True`). | **Remediated & Verified**: Created `src/railway_detection/experiments/cache_provenance.py` implementing the 14-field `ControlledCacheProvenance` contract, canonical JSON SHA-256 digesting, deterministic cache filenames, header validation (`load_controlled_cache_jsonl`), and fail-closed rejection of unverified historical caches in `LayerBEventProcessor` unless `allow_historical_unverified_cache=True` is explicitly requested. |
| **D. Descriptive-Only vs. Official Isolation** | `src/railway_detection/evaluation/descriptive_only.py` was created as an isolated synthetic aggregator. | **Verified & Strengthened**: Module was isolated from official runners, but did not yet inspect `permitted_claims` for forbidden cross-site generalization / official benchmark claims, or explicitly block pooling of `engine_events/event_001` and historical-as-controlled misrepresentations. | **Remediated & Verified**: Enhanced `descriptive_only.py` to reject cross-site generalization / official test-set claims (`FORBIDDEN_CLAIM_SCOPE`), reject `engine_events` pooling (`ENGINE_EVENT_POOLING_REFUSED`), track `engine_case_study_ids`, and reject historical-as-controlled provenance claims (`HISTORICAL_AS_CONTROLLED_REFUSED`). |
| **E. Stage-2.1 Human Review Readiness** | Phase 11 modules (`stage2_1_schema.py`, `promotion_gate.py`, `review_session.py`, `adjudication_session.py`, `evaluation_readiness_gate.py`, `readiness_cli.py`) were implemented. | **Verified**: Schema `8.1.0-stage2.1`, reviewer allowlist/blocklist, live media SHA-256 verification, 30s floor, non-overlapping batch session check, and promotion receipt binding are all fail-closed and intact. | **Verified & Documented**: Audited all Stage-2.1 modules and documented the complete human-review workflow in `STAGE21_HUMAN_REVIEW_READINESS_20261101_M2.md`. |

---

## 3. Summary of Files Modified and Created in Mission 2

### Source Files Remediated
1. `src/railway_detection/fusion/collector.py`: Added `preserve_arrival_order: bool = False` to `MultimodalEvidenceCollector.add_evidence_batch`.
2. `src/railway_detection/simulation/runner.py`: Added `SimulationRunResult.rejected_steps` and updated `EventSimulationRunner._run_frames` to isolate `RULE_8_OUT_OF_ORDER_REJECTION` and `RULE_10_DUPLICATE_FRAME_REJECTION` frames without stepping `gate_model` or regressing `prev_t`.
3. `src/railway_detection/simulation/failure_injector.py`: Hardened `FailureMode.STALE_TIMESTAMPS` with upfront validation, unknown/substring `target_source` rejection, exact `r.source_id == target_source` matching, `original_timestamp_s` metadata tracing, and idempotent non-compounding timestamp shifting.
4. `src/railway_detection/evaluation/metrics.py`: Updated `EventMetricsCalculator.evaluate_run` and `aggregate_cohort` to distinguish confirmed train, confirmed no-train, engine, and missing/unknown/non-observable ground-truth states without leaking missing ground truth or engine events into train or negative-control denominators.
5. `src/railway_detection/evaluation/clock_aware.py`: Updated `evaluate_event_replay` so `engine_events` natively produces `evaluable=False, notes="engine_event_excluded"`.
6. `src/railway_detection/experiments/runner.py`: Added `_extract_event_ground_truth` to classify cohorts and boundary states safely and fail closed upfront on unparameterized `B7e`.
7. `src/railway_detection/experiments/cache_provenance.py` *(new module)*: Implemented 14-field `ControlledCacheProvenance`, deterministic key/digest computation, controlled JSONL writer/loader, and explicit historical diagnostic loader.
8. `src/railway_detection/experiments/layer_b_processor.py`: Integrated `ControlledCacheProvenance` and fail-closed rejection of unverified legacy caches unless `allow_historical_unverified_cache=True`.
9. `src/railway_detection/evaluation/descriptive_only.py`: Added fixed-site claim validation (`FORBIDDEN_CLAIM_SCOPE`), `engine_events` pooling refusal (`ENGINE_EVENT_POOLING_REFUSED`), `engine_case_study_ids` tracking, and historical-as-controlled refusal (`HISTORICAL_AS_CONTROLLED_REFUSED`).

### Test Files Updated and Created
1. `tests/unit/test_experiment_runner_v2.py`: Updated `test_b7d_preserves_delivery_order_for_rule8` to verify end-to-end B7d fault handling (`fault_occurred=True`, `total_events=1`).
2. `tests/unit/test_mission2_pipeline_integrity.py` *(new suite)*: Added 39 synthetic unit and integration test cases covering Objectives A1, A2, A3, B, C, D, and E.
