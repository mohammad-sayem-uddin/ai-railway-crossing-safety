# GROUND TRUTH AND COHORT ISOLATION — MISSION 2 (2026-11-01)

- **Document ID**: `GROUND_TRUTH_AND_COHORT_ISOLATION_20261101_M2`
- **Mission**: `MISSION 2 — PIPELINE INTEGRITY VERIFICATION, SAFE REMEDIATION & STAGE-2.1 READINESS`

---

## 1. Ground-Truth State Taxonomy and Handling

Across `src/railway_detection/evaluation/metrics.py`, `src/railway_detection/evaluation/clock_aware.py`, `src/railway_detection/evaluation/ground_truth_loader.py`, `src/railway_detection/experiments/runner.py`, and `src/railway_detection/evaluation/descriptive_only.py`, the pipeline distinguishes the following ground-truth states:

| Ground-Truth State | Representation & Semantics | Train Denominator (`eligible_events`) | Negative-Control Denominator (`no_train_events` / `false_alarm_evaluable_count`) | Engine Case-Study Count (`engine_events`) |
| :--- | :--- | :--- | :--- | :--- |
| **1. Confirmed Train (`OBSERVABLE`)** | `cohort == "train_events"`, `has_train_ground_truth=True`, `evaluable=True`; observable boundary timestamps (`T1`, `T4`) used for metrics. | **Included (`+1`)** | Excluded (`0`) | Excluded (`0`) |
| **2. Confirmed No-Train (`no_train_events`)** | `cohort == "no_train_events"`, `has_train_ground_truth=False`, `evaluable=True`, `notes in {"no_false_alarm", "false_alarm_evaluation"}`. | Excluded (`0`) | **Included (`+1`)** | Excluded (`0`) |
| **3. Engine Event (`engine_events/event_001`)** | `cohort == "engine_events"`, `has_train_ground_truth=False`, `evaluable=False`, `notes="engine_event_excluded"`. `T3_locomotive_unit_clearance` observable; `T4_tail_clearance` `UNOBSERVABLE_NOT_APPLICABLE`. | Excluded (`0`) | Excluded (`0`) | **Included (`+1`)** |
| **4. Missing Ground Truth** | `has_train_ground_truth=None` (or `event.labels == ()` without explicit `no_train`/`engine` cohort); stored as `has_train_ground_truth=False`, `evaluable=False`, `notes="ground_truth_missing"`. | Excluded (`0`) | **Excluded (`0`)** *(Fixed in Mission 2)* | Excluded (`0`) |
| **5. Unknown Ground Truth** | `ground_truth_status="unknown"`, `evaluable=False`, `notes="ground_truth_unknown"`. | Excluded (`0`) | **Excluded (`0`)** | Excluded (`0`) |
| **6. Censored Boundary (`CENSORED`)** | Boundary timestamp is `None` (`SchemaValidationError` if non-`None` in Stage-2.1); recorded in `exclusion_reasons[marker] = "censored"`. Never fabricated. | Excluded from boundary-dependent metric denominator | Excluded (`0`) | Excluded (`0`) |
| **7. Unobservable / Not Applicable (`UNOBSERVABLE_NOT_APPLICABLE`)** | Boundary timestamp is `None`; recorded in `exclusion_reasons[marker] = "not_applicable"` or `"unobservable"`. | Excluded from boundary-dependent metric denominator | Excluded (`0`) | Excluded (`0`) |
| **8. Uncertain Boundary (`UNCERTAIN`)** | Boundary timestamp is `None`; recorded in `exclusion_reasons[marker] = "uncertain"`. If `>50%` boundaries in an event are `UNCERTAIN`, `AdjudicationSession` halts with `StopConditionTriggeredError`. | Excluded from boundary-dependent metric denominator | Excluded (`0`) | Excluded (`0`) |

---

## 2. Critical Defect Fixed in Mission 2: Missing Ground Truth vs. Negative Control

### 2.1 Defect Identified
Prior to Mission 2, `ExperimentRunner.run_condition` (`src/railway_detection/experiments/runner.py:114-144`) passed:
```python
has_train_ground_truth=bool(event.labels)
```
When an event had **missing** ground-truth labels (`event.labels == ()`), `bool(event.labels)` evaluated to `False`, and `EventMetricsCalculator.evaluate_run` (`src/railway_detection/evaluation/metrics.py:275-290`) treated `has_train_ground_truth=False` as a **confirmed no-train negative control**, setting `notes="false_alarm_evaluation"` or `"no_false_alarm"`, `evaluable=True`, and incrementing `summary.no_train_events` and `summary.false_alarm_evaluable_count`.

Additionally, `ExperimentRunner.run_condition` previously extracted `lbl.timestamp_s` whenever `lbl.timestamp_s is not None` without checking `lbl.label_status`, allowing non-observable labels (`censored`, `uncertain`, `unobservable`, `not_applicable`, `unknown`) to be treated as `observed` timestamps.

### 2.2 Remediation Implemented
1. **`ExperimentRunner._extract_event_ground_truth` (`src/railway_detection/experiments/runner.py`)**:
   - Explicitly classifies `engine_events` (`ground_truth_status="engine"`, `cohort="engine_events"`, `evaluable=False`).
   - Explicitly classifies confirmed `no_train_events` (`ground_truth_status="confirmed_no_train"`, `cohort="no_train_events"`).
   - Classifies events with empty/missing labels as `has_train_ground_truth=None`, `ground_truth_status="missing"`, `evaluable=False`, `exclusion_reasons={"ground_truth": "missing"}`.
   - Extracts `entry_time_s` and `clearance_time_s` **only** when `lbl.label_status.lower() in {"observed", "observable"}`; non-observable statuses are recorded in `exclusion_reasons` and never used as numeric boundary timestamps.
2. **`EventMetricsCalculator.evaluate_run` & `aggregate_cohort` (`src/railway_detection/evaluation/metrics.py`)**:
   - When `has_train_ground_truth is None` or `ground_truth_status in {"missing", "unknown", "unobservable", "not_applicable", "censored", "uncertain"}`, returns `evaluable=False` and `notes=f"ground_truth_{status_tag}"`.
   - `aggregate_cohort` excludes all `notes.startswith("ground_truth_")` records from both `eligible` (train denominator) and `no_train` / `false_alarm` (negative-control denominator).

---

## 3. Engine Event (`engine_events/event_001`) Isolation Verification

Per the researcher decision approved on `2026-10-30` (**Engine event = isolated case study**), `engine_events/event_001` is isolated across every evaluation and aggregation layer:

1. **`EventMetricsCalculator.evaluate_run` (`src/railway_detection/evaluation/metrics.py:275-295`)**:
   - Any event with `cohort == "engine_events"`, `ground_truth_status == "engine"`, or `event_id.startswith("engine_events/")` returns `has_train_ground_truth=False`, `missed_train=False`, `evaluable=False`, `notes="engine_event_excluded"`.
2. **`EventMetricsCalculator.aggregate_cohort` (`src/railway_detection/evaluation/metrics.py:438-485`)**:
   - Excludes `_is_engine(e)` from `eligible` (train-event denominator, missed-train rate, premature-opening rate, warning lead time, excess closed duration, clearance latency) and from `no_train` / `false_alarm` (negative-control denominator and false-alarm rate).
   - Counts `_is_engine(e)` exclusively in `summary.engine_events` and retains the event record in `summary.single_events` for isolated case-study inspection.
3. **`clock_aware.evaluate_event_replay` (`src/railway_detection/evaluation/clock_aware.py:174-194`)**:
   - When `truth.cohort == "engine_events"`, natively sets `evaluable=False` and `notes="engine_event_excluded"`.
4. **`descriptive_only.aggregate_descriptive_only` (`src/railway_detection/evaluation/descriptive_only.py:170-235`)**:
   - Rejects any attempt to pass an `engine_events/...` record with `has_train_ground_truth=True` or `evaluable=True` (`ENGINE_EVENT_POOLING_REFUSED`).
   - Surfaces `engine_case_study_ids = ("engine_events/event_001",)` separately on `DescriptiveOnlyReport`.
