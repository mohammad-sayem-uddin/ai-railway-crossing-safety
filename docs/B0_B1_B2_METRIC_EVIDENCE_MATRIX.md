# Metric-to-Code Evidence Matrix: Front-Camera B0 / B1 / B2 Evaluation

**Document Version:** 1.0.0  
**Status:** Proposed Evidence Matrix — Awaiting Researcher Review (Static Code Audit)  
**Governing Modules:**  
- `src/railway_detection/evaluation/metrics.py`
- `src/railway_detection/evaluation/clock_aware.py`
- `src/railway_detection/simulation/runner.py`
- `src/railway_detection/simulation/gate_model.py`
- `src/railway_detection/experiments/runner.py`
- `src/railway_detection/evaluation/protocol_choices.py`
- `src/railway_detection/evaluation/ground_truth_loader.py`
**Test Suites Inspected:**  
- `tests/unit/test_phase12_documented_metrics.py`
- `tests/unit/test_phase12_metric_arithmetic.py`
- `tests/unit/test_event_metrics.py`

---

## 1. Overview & Classification Schema

This matrix provides line-by-line verification for all railway crossing safety and operational metrics in the repository. Each metric is evaluated against its mathematical formula, code implementation, required sensory and ground-truth boundaries, missing-data handling, condition compatibility (B0, B1, B2), governance requirements, and scientific validity bounds.

### Evaluability Classifications:
1. **Replay-Autonomous (Tier 1):** Directly derived from simulation replay outputs. Requires zero ground-truth timestamps. Computable on unannotated raw or candidate detection streams.
2. **Front Ground-Truth Dependent (Tier 2):** Requires front-camera ground-truth boundary $T_1$ (`T1_danger_zone_entry`). Computable provisionally against candidate proposals, but requires approved Stage-2.1 ground truth (`ADJ-AUTH`) for official claims.
3. **Cross-Camera Dependent (Tier 3 - Excluded):** Requires back-camera boundary $T_4$ (`T4_tail_clearance`). Strictly non-computable on single-camera front replay due to `clock_mismatch`.

---

## 2. Comprehensive Metric Evidence Matrix

```
========================================================================================================================
METRIC 1: Total Gate-Closed Duration (total_closed_s / blocked_seconds)
========================================================================================================================
• Intended Interpretation: Total cumulative duration during which the simulated gate barrier arm blocked vehicular road
  traffic (barrier boom lowered to angle <= 45.0 degrees).
• Source Implementation:
  - Tracking: src/railway_detection/simulation/runner.py (lines 203–204)
  - Gate Model: src/railway_detection/simulation/gate_model.py (lines 33–35)
  - Single Event: src/railway_detection/evaluation/metrics.py (lines 69, 284, 365)
  - Cohort Storage: src/railway_detection/evaluation/metrics.py (line 210)
• Relevant Line Numbers: runner.py:203-204; gate_model.py:33-35; metrics.py:284, 365
• Required Inputs: Simulation step sequence (SimulationStep.is_passage_blocked, dt). Zero ground truth boundaries required.
• Formula: Closed Duration = sum(dt_i * I(passage_blocked_i or fully_closed_i)) where passage_blocked is (theta <= 45.0 deg).
• Unit: Seconds (s), continuous float >= 0.0.
• Denominator / Exclusion Rules: Single event scalar. No cohort denominator. Evaluated across all completed replays.
• Missing-Data Behavior: Non-finite timestamps raise ValueError (metrics.py:267-273). Empty replays return 0.0s.
• Evaluability Classification: Replay-Autonomous (Tier 1).
• Condition Compatibility:
  - B0 (Front Vision): Computable. Reflects visual closure duration.
  - B1 (Front Audio): Computable. Reflects acoustic closure; audio locks gate closed until simulation termination.
  - B2 (Front Fusion): Computable. Reflects state-machine closure with 3.0s clearance dwell timer.
• Governance & Media Requirements: Zero media access required if pre-computed inference records are used. No ADJ-AUTH needed.
• Scientific Claims Supported: Quantifies simulated road obstruction time on recorded sensor inputs.
• Scientific Claims NOT Supported: Does NOT prove physical actuator reliability or field hydraulic behavior.
• Relevant Tests: tests/unit/test_phase12_metric_arithmetic.py (lines 84–94); test_phase12_documented_metrics.py (lines 43–60).
• Inconsistencies / Ambiguities: Named `total_closed_s` on SingleEventEvaluation, but `blocked_seconds` when reporting
  nuisance on no-train controls. Mathematically identical in code.

========================================================================================================================
METRIC 2: Contiguous Closure Episodes (closure_episodes)
========================================================================================================================
• Intended Interpretation: Frequency of discrete gate barrier closure cycles, counting transitions from unobstructed
  passage to blocked passage (rising edges of is_passage_blocked). Directly measures gate flapping / actuator chatter.
• Source Implementation: src/railway_detection/evaluation/metrics.py (lines 125–134, function `_closure_episodes`)
• Relevant Line Numbers: metrics.py:125-134; metrics.py:288, 415
• Required Inputs: Simulation step sequence (SimulationStep.is_passage_blocked). Ground truth is NOT required.
• Formula: Episodes = sum(I(is_passage_blocked_i and not is_passage_blocked_{i-1}) for i=1..N)
• Unit: Integer count (>= 0).
• Denominator / Exclusion Rules: Single event integer. Cohort sum: sum(closure_episodes for e in cohort).
• Missing-Data Behavior: If replay initializes in a blocked state, counts as 1 episode (test_phase12_documented_metrics.py:62).
• Evaluability Classification: Replay-Autonomous (Tier 1).
• Condition Compatibility:
  - B0 (Front Vision): Computable. Vital indicator of detection dropouts causing intermittent gate reopening.
  - B1 (Front Audio): Computable. Evaluates whether horn re-triggers cause multiple actuations.
  - B2 (Front Fusion): Computable. Demonstrates state-machine hysteresis preventing chatter.
• Governance & Media Requirements: Zero media access required. No authorization required.
• Scientific Claims Supported: Demonstrates whether decision policy successfully prevents hazardous barrier flapping.
• Scientific Claims NOT Supported: Cannot extrapolate chatter rate to continuous 24-hour operation from short recordings.
• Relevant Tests: tests/unit/test_phase12_documented_metrics.py (lines 43–67).
• Inconsistencies / Ambiguities: None. Implementation is clean and deterministic.

========================================================================================================================
METRIC 3: Replay Stream Exposure Duration (exposure_s / total_duration_s)
========================================================================================================================
• Intended Interpretation: Total physical temporal window of the replayed sensor stream from first frame to last frame.
• Source Implementation:
  - Runner: src/railway_detection/simulation/runner.py (line 245)
  - Metric Single: src/railway_detection/evaluation/metrics.py (lines 79, 289)
  - Cohort Sum: src/railway_detection/evaluation/metrics.py (line 417)
• Relevant Line Numbers: runner.py:245; metrics.py:255, 289, 417
• Required Inputs: Replay frame timestamps. Ground truth is NOT required.
• Formula: Exposure = t_last - t_first. Cohort Exposure = sum(e.exposure_s for e in cohort).
• Unit: Seconds (s), continuous float > 0.0.
• Denominator / Exclusion Rules: Used as exposure denominator for nuisance reporting.
• Missing-Data Behavior: Non-finite values raise ValueError.
• Evaluability Classification: Replay-Autonomous (Tier 1).
• Condition Compatibility: Computable for B0, B1, B2 across all cohorts.
• Governance & Media Requirements: Zero media access. Zero authorization.
• Scientific Claims Supported: Measures empirical recording duration.
• Scientific Claims NOT Supported: Combined front+back stream exposure (summed stream-seconds) must NOT be reported as
  concurrent wall-clock exposure (event_001 proposal v6 note).
• Relevant Tests: tests/unit/test_phase12_documented_metrics.py (line 56).
• Inconsistencies / Ambiguities: None.

========================================================================================================================
METRIC 4: System Fault Event Occurrences (fault_occurred / fault_event_count)
========================================================================================================================
• Intended Interpretation: Indicator of whether any sensor fault, heartbeat loss, timestamp disorder, or source timeout
  was recognized by the fusion engine during the event replay.
• Source Implementation:
  - Simulation Step: src/railway_detection/simulation/runner.py (lines 212–213)
  - Single Event: src/railway_detection/evaluation/metrics.py (lines 70, 285, 366)
  - Cohort Count: src/railway_detection/evaluation/metrics.py (line 488)
• Relevant Line Numbers: runner.py:212-213; metrics.py:285, 366, 488
• Required Inputs: DecisionRecord.fault_status emitted by MultimodalDecisionEngine.
• Formula: Event Fault = any(decision.fault_status_i not in ("none", "", None)). Cohort Count = sum(fault_occurred).
• Unit: Boolean per event; Count across cohort.
• Denominator / Exclusion Rules: Evaluated on all events.
• Missing-Data Behavior: Defaults to False if no fault emitted.
• Evaluability Classification: Replay-Autonomous (Tier 1).
• Condition Compatibility:
  - B0 / B1: Evaluated (returns False under normal operation; legacy stateless runner does not model SourceTracker).
  - B2: Fully evaluated via MultimodalDecisionEngine and SourceTracker.
• Governance & Media Requirements: Zero media access. Zero authorization.
• Scientific Claims Supported: Verifies software fault detection and fail-closed state latching.
• Scientific Claims NOT Supported: Does not simulate physical hardware or wiring failure.
• Relevant Tests: tests/unit/test_fault_injection_scenarios.py; tests/unit/test_collector_fail_closed_fusion.py.
• Inconsistencies / Ambiguities: None.

========================================================================================================================
METRIC 5: No-Train Control Actuation (false_alarm_count / false_alarm_ci95)
========================================================================================================================
• Intended Interpretation: Frequency of unwanted barrier closure during confirmed absence of trains (negative controls).
• Source Implementation: src/railway_detection/evaluation/metrics.py (lines 275–290, 400–417)
• Relevant Line Numbers: metrics.py:277, 400-417
• Required Inputs: Simulation steps for events where cohort == "no_train_events".
• Formula:
  - Event Actuated = (closed_duration_s > 0.0)
  - Count = sum(1 for e in no_train if e.notes == "false_alarm_evaluation")
  - Denominator = len([e for e in no_train if e.evaluable])
  - Wilson 95% CI = wilson_score_interval(false_alarm_count, denominator)
• Unit: Event: Boolean; Cohort: Count, Ratio, and 95% Confidence Interval tuple [lower, upper].
• Denominator / Exclusion Rules: Only events in cohort "no_train_events" are eligible. Engine-only records carry
  notes == "engine_event_excluded" and are strictly excluded from the false alarm denominator (metrics.py:388-399).
• Missing-Data Behavior: If zero eligible no-train events exist, returns None (not evaluable).
• Protocol Restriction: Protocol v9 (§11.2) and metrics.py (line 213) strictly prohibit extrapolating this metric to an
  hourly false alarm rate (`false_alarm_hourly_rate: "not_reported_by_protocol"`).
• Evaluability Classification: Replay-Autonomous (Tier 1).
• Condition Compatibility: Computable for B0, B1, B2 on no_train_events (N=3).
• Governance & Media Requirements: Zero media access. Zero authorization.
• Scientific Claims Supported: Demonstrates baseline nuisance trigger behavior on control recordings (e.g. insect/glare noise).
• Scientific Claims NOT Supported: Bounded by tiny sample size (3 events, ~60s exposure). CANNOT claim operational false
  alarm rates for field deployment.
• Relevant Tests: tests/unit/test_phase12_documented_metrics.py (lines 43–60).
• Inconsistencies / Ambiguities: None.

========================================================================================================================
METRIC 6: Missed-Train Rate (missed_train / missed_train_rate / missed_train_ci95)
========================================================================================================================
• Intended Interpretation: Safety-critical primary endpoint measuring whether the system failed to protect the crossing
  when a train entered the danger zone (barrier arm was NOT blocking traffic at entry boundary T1).
• Source Implementation:
  - Event Match: src/railway_detection/evaluation/metrics.py (lines 292–309)
  - Cohort Rate & CI: src/railway_detection/evaluation/metrics.py (lines 421–434)
• Relevant Line Numbers: metrics.py:297-309, 421-434; tests/unit/test_phase12_metric_arithmetic.py:68-81
• Required Inputs: Simulation steps + Approved ground-truth entry timestamp T1 (T1_danger_zone_entry).
• Formula:
  1. Find simulation step s* minimizing |s.timestamp_s - T1| subject to |s.timestamp_s - T1| <= 0.25s.
  2. If found: missed_train = not s*.is_passage_blocked (i.e. boom angle > 45.0 degrees).
  3. If no step within 0.25s: missed_train = None (not evaluable).
  Cohort MTR = missed_train_count / missed_train_evaluable_count. CI via wilson_score_interval().
• Unit: Event: Boolean; Cohort: Proportion [0.0, 1.0] and 95% CI tuple [lower, upper].
• Denominator / Exclusion Rules:
  - Denominator = len([e for e in eligible if e.missed_train is not None]).
  - Events with missing or unobservable T1 (e.g. event_005) return missed_train = None and are excluded from denominator.
• Missing-Data Behavior: Missing T1 records exclusion reason in summary.exclusions["missed_train"].
• Evaluability Classification: Front Ground-Truth Dependent (Tier 2).
• Condition Compatibility: Computable for B0, B1, B2 on train events with observable T1.
• Governance & Media Requirements:
  - In diagnostic mode: Can be computed against candidate proposals if explicitly labeled provisional.
  - In official evaluation: STRICTLY BLOCKED until candidate T1 timestamps are human-reviewed under ADJ-AUTH and promoted
    to Stage-2.1 ground truth.
• Scientific Claims Supported: Measures simulated gate blockage state when train reaches turnout frog.
• Scientific Claims NOT Supported: Does NOT measure detection latency from physical approach onset (left-censored T0).
• Relevant Tests: tests/unit/test_phase12_metric_arithmetic.py (lines 68–81).
• Inconsistencies / Ambiguities: Specification Table 1 originally hardcoded Evaluable Events: 23; corrected to N_eval <= 22
  due to unobservable T1 in event_005.

========================================================================================================================
METRIC 7: Warning Lead Time (warning_lead_time_s / mean_warning_lead_time_s)
========================================================================================================================
• Intended Interpretation: Operational advance warning time provided to highway traffic between warning actuation and
  locomotive entry into the crossing danger zone (T1).
• Source Implementation:
  - Runner: src/railway_detection/simulation/runner.py (lines 241–244)
  - Clock Aware: src/railway_detection/evaluation/clock_aware.py (lines 100–114)
  - Metrics Single: src/railway_detection/evaluation/metrics.py (line 331)
  - Cohort Mean: src/railway_detection/evaluation/metrics.py (lines 449–458)
• Relevant Line Numbers: runner.py:241-244; clock_aware.py:100-114; metrics.py:331, 449-458
• Required Inputs: Simulation step sequence + Approved ground-truth entry timestamp T1 (front camera clock).
• Formula:
  t_warn = min(s.timestamp_s for s in steps if s.crossing_state == "WARNING")
  warning_lead_time_s = max(0.0, T1 - t_warn) if t_warn and T1 else None
• Unit: Seconds (s), continuous float >= 0.0.
• Denominator / Exclusion Rules: Cohort mean computed strictly over events where warning_lead_time_s is not None.
• Missing-Data Behavior:
  - If warning actuates AFTER T1: (T1 - t_warn) < 0, clamped to 0.0s (runner.py:243; clock_aware.py:111).
  - If no warning triggered, or T1 is None: returns None (excluded from mean).
• Evaluability Classification: Front Ground-Truth Dependent (Tier 2).
• Condition Compatibility: Computable for B0, B1, B2 on events with observable T1.
• Governance & Media Requirements: Candidate T1 can be used provisionally; official evaluation requires Stage-2.1 GT.
• Scientific Claims Supported: Quantifies simulated warning advance before danger zone entry.
• Scientific Claims NOT Supported: ALL 23 train events are left-censored (T0 <= 0.0s). Warning lead time is bounded by
  recording start time, NOT physical approach onset. Cannot be claimed as true physical warning capability.
• Relevant Tests: tests/unit/test_phase12_documented_metrics.py; test_phase12_metric_arithmetic.py.
• Inconsistencies / Ambiguities: None in code. Clamping to 0.0s masks negative warning margins (warnings actuated late).

========================================================================================================================
METRIC 8: Premature Opening under Protocol v9 (premature_opening)
========================================================================================================================
• Intended Interpretation: Safety-critical hazard where the gate begins opening or is open while a train occupies the crossing.
• Source Implementation:
  - Runner: src/railway_detection/simulation/runner.py (lines 216–224)
  - Clock Aware: src/railway_detection/evaluation/clock_aware.py (lines 94–99)
• Relevant Line Numbers: runner.py:219-224; clock_aware.py:94-99; metrics.py:494
• Required Inputs: Approved T1 (front camera) AND Approved T4 (back camera) on a synchronized master timeline.
• Formula: Premature = any(T1 <= step.timestamp_s < T4 and gate_state in ("OPENING", "OPEN") and not is_passage_blocked)
• Unit: Boolean per event; Proportion and 95% Wilson CI across cohort.
• Denominator / Exclusion Rules: Events with unobservable T1 or T4 are excluded from denominator.
• Missing-Data Behavior: On single-camera front replay, T4 (annotated on back camera) is missing from replay clock offsets.
  clock_aware.py (line 224) marks `T4_tail_clearance:clock_mismatch` and returns None.
• Evaluability Classification: Cross-Camera Dependent (Tier 3 - EXCLUDED on front-camera replays).
• Condition Compatibility: Non-computable for single-camera B0, B1, B2. Requires dual-camera with accepted R04 sync.
• Governance & Media Requirements: Open decision in docs/PREMATURE_OPENING_DECISION_EVIDENCE.md. Requires Stage-2.1 GT.
• Scientific Claims Supported: Would measure clearance hazard if cross-camera timeline were calibrated.
• Scientific Claims NOT Supported: Cannot be evaluated on front-only stream.
• Relevant Tests: tests/unit/test_phase12_documented_metrics.py (lines 70–98).
• Inconsistencies / Ambiguities: Protocol choice between v9 and M4 remains undecided by researcher.

========================================================================================================================
METRIC 9: Premature Opening under Protocol M4 (m4_premature_opening)
========================================================================================================================
• Intended Interpretation: Design-document alternative hazard definition: failure if any transition from blocked to
  not-blocked or opening command occurs in (t_blocked, T4), where t_blocked is the first blocked simulation tick.
• Source Implementation: src/railway_detection/evaluation/metrics.py (lines 105–123, function `m4_premature_opening`)
• Relevant Line Numbers: metrics.py:105-123, 317-325
• Required Inputs: Simulation step t_blocked (replay-side) AND Approved T4 (back camera). Does NOT require T1.
• Formula:
  t_blocked = next(s.timestamp_s for s in steps if s.is_passage_blocked)
  If t_blocked is None or t_blocked >= T4: returns (None, True) -> Flagged as M5 never_protected.
  Otherwise: any((not s.is_passage_blocked) or s.gate_state in ("OPENING", "OPEN") for s in steps if t_blocked < s < T4)
• Unit: Boolean per event; Proportion across evaluable events.
• Denominator / Exclusion Rules: Events flagged as M5 (never_protected) are excluded from the M4 denominator.
• Missing-Data Behavior: Requires T4. On front-only replay, T4 is missing -> returns None (`clock_mismatch`).
• Evaluability Classification: Cross-Camera Dependent (Tier 3 - EXCLUDED on front-camera replays).
• Condition Compatibility: Non-computable on front camera alone because T4 is off-screen.
• Governance & Media Requirements: Researcher decision pending (D-10 in docs/PREMATURE_OPENING_DECISION_EVIDENCE.md).
• Scientific Claims Supported: Evaluates clearance holding without confounding approach detection latency.
• Scientific Claims NOT Supported: Non-computable on front camera.
• Relevant Tests: tests/unit/test_phase12_documented_metrics.py.
• Inconsistencies / Ambiguities: Undecided protocol status.

========================================================================================================================
METRIC 10: Under-Protection / Never Protected under Protocol M5 (never_protected)
========================================================================================================================
• Intended Interpretation: Operational hazard where the barrier never blocked vehicular traffic before the train cleared (T4).
• Source Implementation: src/railway_detection/evaluation/metrics.py (lines 105–123, 484–486)
• Relevant Line Numbers: metrics.py:116-117, 320-324, 484-486
• Required Inputs: Replay steps + Approved T4.
• Formula: never_protected = True if (t_blocked is None or t_blocked >= T4).
• Unit: Boolean per event; Count across cohort.
• Denominator / Exclusion Rules: Evaluated only under M4 window when T4 is present.
• Missing-Data Behavior: Non-computable without T4.
• Evaluability Classification: Cross-Camera Dependent (Tier 3 - EXCLUDED on front-camera replays).
• Condition Compatibility: Non-computable on front camera alone.
• Governance & Media Requirements: Tied to M4 decision.
• Scientific Claims Supported: Prevents missed detections from masquerading as safe zero-failure runs under M4.
• Scientific Claims NOT Supported: Non-computable on front camera.
• Relevant Tests: tests/unit/test_phase12_documented_metrics.py.
• Inconsistencies / Ambiguities: Only active when premature_opening_window == "first_blocked_to_t4_clearance".

========================================================================================================================
METRIC 11: Excess Closed Duration (excess_closed_duration_s / mean_excess_closed_s)
========================================================================================================================
• Intended Interpretation: Highway traffic delay penalty: closed duration in excess of physical train passage duration.
• Source Implementation: src/railway_detection/evaluation/metrics.py (lines 334–342, 459–468)
• Relevant Line Numbers: metrics.py:336-342, 459-468; tests/unit/test_phase12_metric_arithmetic.py:84-94
• Required Inputs: Simulation steps + Approved T1 (front) + Approved T4 (back).
• Formula:
  passage_duration = T4 - T1
  excess_closed_duration_s = max(0.0, closed_duration_s - passage_duration)
• Unit: Seconds (s), continuous float >= 0.0.
• Denominator / Exclusion Rules: Requires both T1 and T4, and T4 > T1. Cohort mean over non-null events.
• Missing-Data Behavior: If either T1 or T4 is missing, or they share no common timeline, returns None (clock_mismatch).
• Evaluability Classification: Cross-Camera Dependent (Tier 3 - EXCLUDED on front-camera replays).
• Condition Compatibility: Non-computable on front-camera replay alone.
• Governance & Media Requirements: Requires dual-camera synchronization and Stage-2.1 GT.
• Scientific Claims Supported: Quantifies economic traffic penalty.
• Scientific Claims NOT Supported: Non-computable on front camera.
• Relevant Tests: tests/unit/test_phase12_metric_arithmetic.py (lines 84–94).
• Inconsistencies / Ambiguities: None.

========================================================================================================================
METRIC 12: Clearance Verification Latency (clearance_latency_s / mean_clearance_latency_s)
========================================================================================================================
• Intended Interpretation: Operational delay between physical train rear clearance (T4) and the moment the gate began opening.
• Source Implementation: src/railway_detection/evaluation/metrics.py (lines 344–355, 469–478)
• Relevant Line Numbers: metrics.py:345-355, 469-478; tests/unit/test_phase12_metric_arithmetic.py:96-110
• Required Inputs: Simulation steps + Approved T4 (back camera).
• Formula:
  open_steps = [s for s in steps if s.timestamp_s >= T4 and s.crossing_state in ("GATE_OPENING", "CROSSING_CLEAR")]
  clearance_latency_s = max(0.0, open_steps[0].timestamp_s - T4) if open_steps else None
• Unit: Seconds (s), continuous float >= 0.0.
• Denominator / Exclusion Rules: Cohort mean over non-null events.
• Missing-Data Behavior: If T4 is missing or gate never opens, returns None. On front-only replay, returns None (clock_mismatch).
• Evaluability Classification: Cross-Camera Dependent (Tier 3 - EXCLUDED on front-camera replays).
• Condition Compatibility: Non-computable on front-camera replay alone.
• Governance & Media Requirements: Requires back-camera T4 and Stage-2.1 GT.
• Scientific Claims Supported: Measures sensor and dwell-timer recovery latency after train departure.
• Scientific Claims NOT Supported: Non-computable on front camera.
• Relevant Tests: tests/unit/test_phase12_metric_arithmetic.py (lines 96–110).
• Inconsistencies / Ambiguities: None.

========================================================================================================================
AUXILIARY METRICS: Detection & Inference Window Counts
========================================================================================================================
• Metrics:
  - `front_vision_frames`: Total sampled video frames processed at target FPS (integer count).
  - `front_vision_detections`: Total YOLO bounding boxes detected (confidence >= 0.35) (integer count).
  - `front_audio_windows`: Total windowed spectrograms processed (1.0s window, 0.5s hop) (integer count).
  - `front_audio_horns_detected`: Total windows exceeding acoustic threshold (>= 0.3700) (integer count).
• Source Implementation: scripts/run_phase5_full_inference.py (lines 438–446)
• Evaluability Classification: Replay-Autonomous (Tier 1). Computable for B0, B1, B2.
• Governance & Media Requirements: Derived from pre-computed inference JSONLs without raw media access.
========================================================================================================================
```

---

## 3. Summary Matrix of Evaluability by Condition

| Metric Identifier | Mathematical Units | B0 (Vision) | B1 (Audio) | B2 (Fusion) | Evaluability Tier | Boundary Dependencies | Official Authorization Gate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `total_closed_s` | s | **Evaluable** | **Evaluable** | **Evaluable** | **Tier 1 (Replay)** | None | None (Replay derived) |
| `closure_episodes` | count | **Evaluable** | **Evaluable** | **Evaluable** | **Tier 1 (Replay)** | None | None (Replay derived) |
| `exposure_s` | s | **Evaluable** | **Evaluable** | **Evaluable** | **Tier 1 (Replay)** | None | None (Replay derived) |
| `fault_occurred` | bool | **Evaluable** | **Evaluable** | **Evaluable** | **Tier 1 (Replay)** | None | None (Replay derived) |
| `false_alarm_count` | count | **Evaluable** | **Evaluable** | **Evaluable** | **Tier 1 (Replay)** | None | None (Cohort label only) |
| `false_alarm_ci95` | [lo, hi] | **Evaluable** | **Evaluable** | **Evaluable** | **Tier 1 (Replay)** | None | None (Cohort label only) |
| `missed_train` | bool | **Evaluable** | **Evaluable** | **Evaluable** | **Tier 2 (Front GT)** | $T_1$ (Front) | `ADJ-AUTH` / Stage-2.1 GT |
| `missed_train_rate` | ratio | **Evaluable** | **Evaluable** | **Evaluable** | **Tier 2 (Front GT)** | $T_1$ (Front) | `ADJ-AUTH` / Stage-2.1 GT |
| `missed_train_ci95` | [lo, hi] | **Evaluable** | **Evaluable** | **Evaluable** | **Tier 2 (Front GT)** | $T_1$ (Front) | `ADJ-AUTH` / Stage-2.1 GT |
| `warning_lead_time_s` | s | **Evaluable** | **Evaluable** | **Evaluable** | **Tier 2 (Front GT)** | $T_1$ (Front) | `ADJ-AUTH` / Stage-2.1 GT |
| `premature_opening` (v9) | bool | **EXCLUDED** | **EXCLUDED** | **EXCLUDED** | **Tier 3 (Cross-Cam)** | $T_1$ (Front) & $T_4$ (Back) | Protocol Decision + R04 Sync |
| `premature_opening` (M4) | bool | **EXCLUDED** | **EXCLUDED** | **EXCLUDED** | **Tier 3 (Cross-Cam)** | $T_4$ (Back) | Protocol Decision + R04 Sync |
| `never_protected` (M5) | bool | **EXCLUDED** | **EXCLUDED** | **EXCLUDED** | **Tier 3 (Cross-Cam)** | $T_4$ (Back) | Protocol Decision + R04 Sync |
| `excess_closed_duration_s` | s | **EXCLUDED** | **EXCLUDED** | **EXCLUDED** | **Tier 3 (Cross-Cam)** | $T_1$ (Front) & $T_4$ (Back) | R04 Sync + Stage-2.1 GT |
| `clearance_latency_s` | s | **EXCLUDED** | **EXCLUDED** | **EXCLUDED** | **Tier 3 (Cross-Cam)** | $T_4$ (Back) | Stage-2.1 GT |
