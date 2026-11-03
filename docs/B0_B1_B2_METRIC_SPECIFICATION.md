# Technical Metric Specification: Front-Camera B0 / B1 / B2 Offline Evaluation

**Document Version:** 1.0.0  
**Status:** Proposed Technical Specification — Awaiting Researcher Review (Read-Only Code Audit)  
**Target Scope:** Front-Camera Container Conditions (B0: Vision, B1: Audio, B2: Multimodal Fusion)  
**Governing Codebases:**  
- `src/railway_detection/experiments/runner.py`
- `src/railway_detection/experiments/layer_b_processor.py`
- `scripts/run_phase5_full_inference.py`
- `scripts/run_real_world_experiments.py`
- `src/railway_detection/evaluation/metrics.py`
- `src/railway_detection/evaluation/clock_aware.py`
- `src/railway_detection/simulation/runner.py`
- `src/railway_detection/evaluation/replay_producer.py`
- `src/railway_detection/evaluation/evaluation_runner.py`

---

## 1. Executive Summary & Purpose

This specification defines the exact mathematical and implementation boundaries for evaluating front-camera sensor conditions **B0**, **B1**, and **B2** on the 27-event railway crossing dataset (`crossing_A`). 

Based on rigorous static inspection of the repository's simulation engines, evaluation runners, metric calculators, and clock-aware evaluators, this document:
1. **Resolves the B2 architectural and naming discrepancy** across existing scripts.
2. **Audits the diagnostic harness** (`scripts/run_real_world_experiments.py`) for complete input sources, file-system side-effects, and governance firewall bypasses.
3. **Categorizes all proposed safety and operational metrics** into three distinct tiers of evaluability under front-camera constraints.
4. **Defines the minimum defensible descriptive report** that can be produced without violating data-leakage boundaries, fabricating ground truth, or making unverified claims of held-out generalization.

---

## 2. Resolution of the B2 Implementation & Naming Discrepancy

Static inspection reveals a discrepancy between the legacy diagnostic benchmark harness and the later production/evaluation architecture:

### 2.1 The Two Discrepant Code Paths

```
Script / Module                                     B2 Definition                               Input Streams                               Simulation Engine
-------------------------------------------------------------------------------------------------------------------------------------------------------------
1. src/railway_detection/experiments/runner.py      "Dual Vision + Audio"                       camera_1 + camera_2 + audio                 Stateless 3-frame persistence
   & scripts/run_real_world_experiments.py         (Stateless 3-frame persistence)             (Full frame unstripped)                     (Bypasses EventSimulationRunner)

2. scripts/run_phase5_full_inference.py             "Front Vision + Front Audio"                front_v_recs + front_a_recs                 EventSimulationRunner
   & src/railway_detection/evaluation/               (Container-native multimodal fusion)        (camera_2 strictly omitted)                 (Full state-machine with
     replay_producer.py                                                                                                                     dwell timers)
```

1. **Legacy Diagnostic Benchmark Path (`src/railway_detection/experiments/runner.py`):**
   - In `_prepare_frames_for_condition()` (lines 249–252), condition `B2` falls through to `prepared.append(frame)`, retaining all streams in `MultimodalFrame`—including `camera_2` (back camera) if present.
   - In `_execute_simulation()` (lines 420–492), `B2` is simulated under a **stateless baseline policy** with `confirm_needed = 3` (line 442) on `has_det = f.has_vision_evidence or f.has_audio_evidence` (lines 448–450). It completely bypasses `EventSimulationRunner` and `MultimodalDecisionEngine`. It actuates `GateState.CLOSING` when active and `GateState.OPENING` immediately when detection drops, intentionally demonstrating the vulnerability of stateless thresholding.
   - The resulting report generator (`scripts/run_real_world_experiments.py`, line 260) labels B2 as `"Dual Vision + Audio" | "Stateless 3-frame persistence"`.

2. **Production Inference & Evaluation Architecture Path (`scripts/run_phase5_full_inference.py` & `replay_producer.py`):**
   - In `scripts/run_phase5_full_inference.py` (lines 401–415), `B2` is defined as:
     `Condition B2: Front Vision + Front Audio Native Container Sync`.
     It ingests strictly `front_v_recs` and `front_a_recs` into `processor.build_multimodal_frames()`, with `camera_2` excluded, and executes `EventSimulationRunner(config=config).run_frames(...)` using the full state machine.
   - In `src/railway_detection/evaluation/replay_producer.py` (lines 275–276), the single-camera evaluation plan formalizes container-native front multimodal replay:
     ```python
     if mode == "single_camera":
         plan = [("front", ("front_vision", "front_audio"), {"front": 0.0}, None)]
     ```
     This plan feeds `MultimodalEvidenceCollector` with front vision and front audio on a single timeline ($\tau = 0.0\,\text{s}$ offset) into `EventSimulationRunner`.

### 2.2 Authoritative Resolution (Without Code Modification)
To evaluate the proposed **front-camera-only** descriptive benchmark without cross-camera dependency:
- **Condition B2 must strictly refer to the container-native front multimodal stream** (`front_vision` + `front_audio`) evaluated through the deterministic state-machine simulation engine (`EventSimulationRunner`), as formalized in `scripts/run_phase5_full_inference.py` (lines 401–415) and `src/railway_detection/evaluation/replay_producer.py` (lines 275–276).
- The legacy stateless runner definition in `runner.py` (lines 420–492) is an exploratory baseline test demonstrating stateless chatter, and must not be confused with the proposed front-container fusion benchmark.

---

## 3. Diagnostic Harness Input, Side-Effect, and Governance Audit

A comprehensive static audit of `scripts/run_real_world_experiments.py` and its dependencies (`src/railway_detection/experiments/layer_b_processor.py`) was performed:

### 3.1 Input Sources & Media-Access Risk
- **Directory Traversal:** Reads `data/raw/layer_b/v2/{train_events, no_train_events, engine_events}/*` (lines 71–89).
- **Video Decoding Risk:** In `layer_b_processor.py` (lines 172–239, `run_vision_inference`):
  - Checks cache file: `results/experiments/cache/{cohort}_{event_id}_{source_id}_vision.jsonl`.
  - **Critical Behavior:** If `use_cache=False` or if any cache file is missing, it calls `frame_generator(video_path, target_fps=...)` (line 200), which directly opens and decodes raw `.mov` video files (`camera_front.mov`, `camera_back.mov`).
- **Audio Extraction Risk:** In `layer_b_processor.py` (lines 135–170, `extract_audio`):
  - If `data/processed/layer_b/audio/{cohort}/{event_id}/camera_front.wav` does not exist or has zero size, it calls `extract_audio_from_video(...)`, launching `ffmpeg` subprocesses on `camera_front.mov`.
- **Checkpoint Ingestion:** Loads weights from `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` and `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`.

### 3.2 Side-Effect Paths (Filesystem Writes)
When executed, `scripts/run_real_world_experiments.py` writes to numerous repository paths:
1. `data/processed/layer_b/audio/`: Writes extracted WAV files.
2. `results/experiments/cache/`: Writes JSONL inference caches.
3. `results/experiments/{B0..B7}/`: Overwrites `summary.json` and `single_events.json`.
4. `results/experiments/B4/timelines/`: Writes per-event timeline `.json` and `.csv` files.
5. `results/experiments/statistical_analysis/`: Writes `comprehensive_statistics.json`.
6. `results/experiments/figures/`: Writes 20 PNG figures at 300 DPI.
7. `results/experiments/tables/`: Writes 12 publication tables in MD, CSV, and LaTeX.
8. `docs/REAL_WORLD_EXPERIMENT_REPORT.md`: **Overwrites** the markdown report file (lines 234–236, 393).

### 3.3 Governance & Validation Bypasses
The diagnostic script operates entirely outside the repository's formal evaluation firewall:
1. **Split Contract Bypass:** It evaluates all 27 discovered events without checking `data/splits/phase12_event_split_decision.json`. It does not enforce partition isolation.
2. **Ground-Truth Adjudication Bypass:** It does not load `data/ground_truth/phase12_ground_truth.json` or verify `ADJ-AUTH` approval status. It computes metrics without reference to an approved Stage-2.1 ground truth artifact.
3. **Cross-Camera Timing Guard Bypass:** In lines 101–112 and 390–400 of `layer_b_processor.py`, it merges `v1_records` (front) and `v2_records` (back) into `build_multimodal_frames()` with `sync_aligner=None`. In `build_multimodal_frames()` (lines 301–316), unless `allow_unverified_zero_offset: true` is configured in `configs/frozen_experiment_v1.yaml`, it raises a fatal `TimingIntegrityError`.

---

## 4. Evaluability Taxonomy: Three Metric Tiers

Under the front-camera-only evaluation scope, metrics divide into three distinct operational tiers:

```
+----------------------------------------------------------------------------------------------------+
| TIER 1: Replay-Autonomous Metrics (Ground-Truth Independent)                                      |
| -> Computable directly from simulation steps on front-camera replay. Requires NO ground truth.     |
| Metrics: total_closed_s, closure_episodes, exposure_s, fault_occurred, false_alarm_actuation.      |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| TIER 2: Front-Camera Ground-Truth Dependent Metrics                                               |
| -> Computable using front-camera ground-truth boundary T1 (danger zone entry).                     |
| -> Requires approved Stage-2.1 ground truth (ADJ-AUTH) for official evaluation.                     |
| Metrics: missed_train (MTR), warning_lead_time_s.                                                   |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| TIER 3: Cross-Camera Dependent Metrics (NON-COMPUTABLE on Front Camera)                           |
| -> Strictly requires T4 (tail clearance), which is annotated on camera_2 (back camera).            |
| -> Under clock_aware.py (lines 128-130), missing camera_2 produces clock_mismatch -> returns None.  |
| Metrics: premature_opening (v9 & M4), never_protected (M5), excess_closed_duration, clearance_lat. |
+----------------------------------------------------------------------------------------------------+
```

---

## 5. Detailed Metric Catalog

### 5.1 Tier 1: Replay-Autonomous Metrics (Ground-Truth Independent)

#### 1. Total Gate Closed Duration (`total_closed_s` / `blocked_seconds`)
- **Code Reference:** `src/railway_detection/simulation/runner.py` (lines 203–204); `src/railway_detection/evaluation/metrics.py` (lines 69, 284, 365).
- **Mathematical Definition:**
  $$\text{Closed Duration} = \sum_{i=1}^{N} \Delta t_i \cdot \mathbb{I}(\text{passage\_blocked}_i \lor \text{fully\_closed}_i)$$
  where $\text{passage\_blocked}_i$ is true when gate barrier angle $\theta_i \le 45.0^\circ$.
- **Units:** Seconds ($s$), float $\ge 0.0$.
- **Event-Level Inputs:** Simulation step records (`SimulationStep.is_passage_blocked`, `SimulationStep.gate_state`). Ground-truth boundaries are **not required**.
- **Condition Applicability:**
  - **B0:** Computable. Reflects visual actuation and persistence closure.
  - **B1:** Computable. Reflects acoustic horn closure; invariant locks gate closed until reset.
  - **B2:** Computable. Reflects multimodal state-machine closure with 3.0s clearance dwell timer.
- **Missing Data / Exclusion:** Always evaluable if replay steps exist. Replay steps with invalid timestamps raise `ValueError`.
- **Scientific Classification:** **Descriptive Characterization.** Measures physical gate obstruction simulated under recorded sensor inputs.

#### 2. Contiguous Closure Episodes (`closure_episodes`)
- **Code Reference:** `src/railway_detection/evaluation/metrics.py` (lines 125–134, `_closure_episodes`).
- **Mathematical Definition:**
  $$\text{Episodes} = \sum_{i=1}^{N} \mathbb{I}(\text{passage\_blocked}_i \land \neg \text{passage\_blocked}_{i-1})$$
  Counts rising edges of passage blockage.
- **Units:** Integer count ($\ge 0$).
- **Event-Level Inputs:** Simulation step sequence (`SimulationStep.is_passage_blocked`). Ground truth is **not required**.
- **Condition Applicability:**
  - **B0:** Computable. Measures gate flapping/chatter caused by visual detection dropouts.
  - **B1:** Computable. Typically 1 episode if horn is detected.
  - **B2:** Computable. Verifies that state-machine hysteresis prevents gate oscillation.
- **Missing Data / Exclusion:** Always evaluable. If replay starts in a blocked state, counts as 1 episode (`test_phase12_documented_metrics.py` line 62).
- **Scientific Classification:** **Descriptive Characterization.** Essential metric for detecting dangerous gate oscillation.

#### 3. Stream Exposure Duration (`exposure_s` / `total_duration_s`)
- **Code Reference:** `src/railway_detection/simulation/runner.py` (line 245); `src/railway_detection/evaluation/metrics.py` (lines 79, 289, 417).
- **Mathematical Definition:**
  $$\text{Exposure} = t_{\text{last\_step}} - t_{\text{first\_step}}$$
- **Units:** Seconds ($s$), float $> 0.0$.
- **Event-Level Inputs:** Replay frame timestamps. Ground truth is **not required**.
- **Condition Applicability:** Computable for B0, B1, B2.
- **Missing Data / Exclusion:** Always evaluable for completed replays.
- **Scientific Classification:** **Descriptive Denominator.** Used to normalize nuisance activations across cohorts.

#### 4. System Fault Event Occurrences (`fault_occurred` / `fault_event_count`)
- **Code Reference:** `src/railway_detection/simulation/runner.py` (lines 212–213); `src/railway_detection/evaluation/metrics.py` (lines 70, 285, 366, 488).
- **Mathematical Definition:**
  $$\text{Fault Flag} = \bigvee_{i=1}^{N} (\text{decision.fault\_status}_i \notin \{\text{"none"}, \text{""}, \text{None}\})$$
- **Units:** Boolean (Single Event); Count (Cohort).
- **Event-Level Inputs:** `DecisionRecord.fault_status` emitted by `MultimodalDecisionEngine`.
- **Condition Applicability:**
  - **B0 / B1:** Evaluated as `False` in legacy stateless runners.
  - **B2:** Evaluated via `MultimodalDecisionEngine` (monitors heartbeat loss, source timeouts, stale frames).
- **Missing Data / Exclusion:** Always evaluable.
- **Scientific Classification:** **Descriptive Reliability Metric.**

#### 5. No-Train Control Actuation (`false_alarm_count` / `false_alarm_ci95`)
- **Code Reference:** `src/railway_detection/evaluation/metrics.py` (lines 275–290, 400–417).
- **Mathematical Definition:**
  $$\text{Actuated} = \mathbb{I}(\text{closed\_duration\_s} > 0.0) \quad \text{for events in cohort } \text{"no\_train\_events"}$$
  Cohort Wilson 95% Confidence Interval is calculated via `wilson_score_interval(false_alarm_count, total_no_train)`.
- **Units:** Boolean (Event); Count, Ratio, and 95% CI tuple `[lower, upper]` (Cohort).
- **Event-Level Inputs:** Event cohort label (`cohort == "no_train_events"`), simulation steps. Ground-truth timestamps are **not required**.
- **Condition Applicability:** Computable for B0, B1, B2 across the 3 negative control events (`no_train_events`).
- **Missing Data / Exclusion:** Only evaluated on events explicitly declared as `no_train_events`. Engine-only events are excluded from the false-alarm denominator (`metrics.py` lines 388–399).
- **Protocol Constraint:** Protocol v9 (§11.2) strictly forbids reporting a "false-alarm hourly rate" by extrapolation (`false_alarm_hourly_rate: "not_reported_by_protocol"`). Only raw counts, blocked seconds, episodes, and Wilson CIs may be reported.
- **Scientific Classification:** **Exploratory Characterization.** Severely bounded by sample size ($N=3$ events, ~60s exposure).

---

### 5.2 Tier 2: Front-Camera Ground-Truth Dependent Metrics

#### 6. Missed Train Rate (`missed_train` / `missed_train_rate`)
- **Code Reference:** `src/railway_detection/evaluation/metrics.py` (lines 292–309, 421–434); `tests/unit/test_phase12_metric_arithmetic.py` (lines 68–81).
- **Mathematical Definition:**
  For an event with ground-truth entry time $T_1$:
  1. Find the simulation step $s^*$ minimizing $|s.\text{timestamp\_s} - T_1|$ subject to $|s.\text{timestamp\_s} - T_1| \le 0.25\,\text{s}$.
  2. If such $s^*$ exists:
     $$\text{missed\_train} = \neg s^*.\text{is\_passage\_blocked} \quad (\text{i.e., gate angle } \theta > 45.0^\circ)$$
  3. If no step exists within $\pm 0.25\,\text{s}$:
     $$\text{missed\_train} = \text{None} \quad (\text{not evaluable})$$
  Cohort rate is:
  $$\text{MTR} = \frac{\sum \text{missed\_train}}{\text{missed\_train\_evaluable\_count}}$$
  with Wilson score 95% CI.
- **Units:** Boolean (Event); Proportion $[0.0, 1.0]$ and 95% CI tuple (Cohort).
- **Event-Level Inputs:**
  - Front camera video/audio simulation steps.
  - Ground-truth timestamp $T_1$ (`T1_danger_zone_entry`).
- **Camera Dependency:** **Front camera native.** $T_1$ is annotated directly on `camera_front.mov` (turnout frog / danger-zone entry plane).
- **Condition Applicability:**
  - **B0:** Computable. Measures if visual detection closed the barrier prior to locomotive crossing entry line.
  - **B1:** Computable. Measures if horn acoustics closed the barrier before $T_1$. (Note: Events lacking audible horn whistle will be recorded as misses under B1).
  - **B2:** Computable. Measures multimodal fusion barrier closure at $T_1$.
- **Missing Data / Exclusion:**
  - If $T_1$ is missing, unobservable, or marked `censored`: `missed_train = None` and excluded from denominator with reason `T1_danger_zone_entry:<reason>` (`metrics.py` lines 517–531).
  - If replay timeline has a gap $> 0.25\,\text{s}$ spanning $T_1$: `missed_train = None`.
- **Governance Gate:** Calculating an official MTR requires $T_1$ to be ingested from an approved Stage-2.1 ground-truth record (`phase12_ground_truth.json`). In diagnostic/exploratory runs, candidate $T_1$ timestamps from proposals may be used if explicitly documented as provisional.
- **Scientific Classification:** **Descriptive / Exploratory Safety Metric.** Bounded by left-censoring: because trains are already approaching at $t=0.0\,\text{s}$, this measures gate closure state at $T_1$, not detection latency from initial entry into the corridor.

#### 7. Warning Lead Time (`warning_lead_time_s` / `mean_warning_lead_time_s`)
- **Code Reference:** `src/railway_detection/simulation/runner.py` (lines 241–244); `src/railway_detection/evaluation/clock_aware.py` (lines 100–114); `src/railway_detection/evaluation/metrics.py` (lines 331, 449–458).
- **Mathematical Definition:**
  $$t_{\text{warn}} = \min \{ s.\text{timestamp\_s} \mid s.\text{crossing\_state} == \text{"WARNING"} \}$$
  $$\text{Warning Lead Time} = \max(0.0, T_1 - t_{\text{warn}}) \quad \text{if } t_{\text{warn}} \text{ exists and } T_1 \text{ exists, else None}$$
- **Units:** Seconds ($s$), float $\ge 0.0$.
- **Event-Level Inputs:**
  - Simulation step timestamps and crossing states.
  - Ground-truth timestamp $T_1$ (`T1_danger_zone_entry`).
- **Camera Dependency:** **Front camera native.** Both $t_{\text{warn}}$ and $T_1$ reside on the front camera clock.
- **Condition Applicability:**
  - **B0:** Computable. Measures lead time provided by visual detection prior to $T_1$.
  - **B1:** Computable. Measures acoustic warning lead time (horn onset prior to $T_1$).
  - **B2:** Computable. Measures fused warning actuation lead time.
- **Missing Data / Exclusion:**
  - If no warning state is triggered prior to end of replay: returns `None`.
  - If $T_1$ is missing or unobservable: returns `None`.
  - If warning triggers *after* $T_1$: $(T_1 - t_{\text{warn}}) < 0$, which the code clamps to `0.0s` (`runner.py` line 243; `clock_aware.py` line 111).
- **Scientific Classification:** **Descriptive Operational Metric.** **Caution:** Because recording starts after the train has already begun its approach in all 23 train events ($T_0 \le 0.0\,\text{s}$), the observed lead time is left-censored by recording start time. It cannot be interpreted as the maximum achievable physical warning time.

---

### 5.3 Tier 3: Cross-Camera Dependent Metrics (NON-COMPUTABLE on Front Camera)

The following metrics are defined in the repository protocol but **cannot be computed** for single-camera front evaluations:

```
Metric Identifier          Required Boundaries         Clock Source                Front-Camera Status             Exclusion Reason in Code
-------------------------------------------------------------------------------------------------------------------------------------------------------------
premature_opening (v9)     T1, T4                      Front (T1) & Back (T4)      NON-COMPUTABLE                  T4_tail_clearance:clock_mismatch
premature_opening (M4)     t_blocked, T4               Replay (t_b) & Back (T4)    NON-COMPUTABLE                  T4_tail_clearance:clock_mismatch
never_protected (M5)       t_blocked, T4               Replay (t_b) & Back (T4)    NON-COMPUTABLE                  T4_tail_clearance:clock_mismatch
excess_closed_duration_s   T1, T4                      Front (T1) & Back (T4)      NON-COMPUTABLE                  clock_mismatch (T1 & T4 share no timeline)
clearance_latency_s        T4                          Back (T4)                   NON-COMPUTABLE                  T4_tail_clearance:clock_mismatch
```

#### Detailed Rationale for Non-Computability:
1. **Physical Camera Placement:**
   - Ground-truth protocol v7.0.0 (§2.4) and candidate proposal records (`data/ground_truth/proposals/train_events/event_*_proposal_v*.json`) establish that $T_4$ (`T4_tail_clearance`) is visible and annotated **exclusively on `camera_back.mov`** (the departure clearance line across the tracks).
   - The front camera views the approach zone and turnout frog; the rear buffer of departing trains cannot be reliably observed on the front camera.
2. **Clock Isolation Enforcement:**
   - In `src/railway_detection/evaluation/clock_aware.py` (lines 117–132, `_boundary_in_system`), the evaluator checks whether the boundary's reference camera exists in the replay configuration's `clock_offsets_s`.
   - On a front-only replay (`cameras_available = {"camera_1"}` or `{"front"}`), $T_4$ has `reference_camera = "camera_2"`. The offset lookup returns `None`.
   - In lines 222–226, the evaluator records:
     `T4_tail_clearance:clock_mismatch(annotated on camera_2; replay clocks ['front'])`.
   - The metric attribute is set to `None`, excluded from cohort aggregation, and reported in `summary.exclusions`.
3. **M4 Endpoint Clock Limitation:**
   - While protocol M4 eliminates dependence on $T_1$ by using replay-side $t_{\text{blocked}}$, it still strictly requires $T_4$ as the upper interval boundary: $(t_{\text{blocked}}, T_4)$ (`metrics.py` lines 118–121). Because $T_4$ is on the back camera clock, M4 is equally non-computable on front-only replays.

---

## 6. Summary Matrix: Metric Evaluability by Condition

| Metric Code Identifier | Metric Display Name | Units | B0 (Vision) | B1 (Audio) | B2 (Fusion) | Evaluability Tier | Boundary Dependencies |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `missed_train` | Missed-Train Flag | bool | Evaluabled | Evaluabled | Evaluabled | **Tier 2** | $T_1$ (Front) |
| `missed_train_rate` | Missed-Train Rate (MTR) | ratio | Evaluabled | Evaluabled | Evaluabled | **Tier 2** | $T_1$ (Front) |
| `missed_train_ci95` | MTR 95% Wilson CI | $[lo, hi]$ | Evaluabled | Evaluabled | Evaluabled | **Tier 2** | $T_1$ (Front) |
| `warning_lead_time_s` | Warning Lead Time | s | Evaluabled | Evaluabled | Evaluabled | **Tier 2** | $T_1$ (Front) |
| `total_closed_s` | Total Closed Duration | s | Evaluabled | Evaluabled | Evaluabled | **Tier 1** | None (Replay only) |
| `closure_episodes` | Gate Closure Episodes | count | Evaluabled | Evaluabled | Evaluabled | **Tier 1** | None (Replay only) |
| `exposure_s` | Total Stream Duration | s | Evaluabled | Evaluabled | Evaluabled | **Tier 1** | None (Replay only) |
| `fault_occurred` | System Fault Flag | bool | Evaluabled | Evaluabled | Evaluabled | **Tier 1** | None (Replay only) |
| `false_alarm_count` | Control Gate Actuations | count | Evaluabled | Evaluabled | Evaluabled | **Tier 1** | None (Cohort only) |
| `false_alarm_ci95` | Control Actuation 95% CI | $[lo, hi]$ | Evaluabled | Evaluabled | Evaluabled | **Tier 1** | None (Cohort only) |
| `premature_opening` | Premature Opening (v9) | bool | **Excluded** | **Excluded** | **Excluded** | **Tier 3** | $T_1$ (Front) & $T_4$ (Back) |
| `premature_opening` | Premature Opening (M4) | bool | **Excluded** | **Excluded** | **Excluded** | **Tier 3** | $T_4$ (Back) |
| `never_protected` | Under-Protected (M5) | bool | **Excluded** | **Excluded** | **Excluded** | **Tier 3** | $T_4$ (Back) |
| `excess_closed_duration_s` | Excess Closed Duration | s | **Excluded** | **Excluded** | **Excluded** | **Tier 3** | $T_1$ (Front) & $T_4$ (Back) |
| `clearance_latency_s` | Clearance Latency | s | **Excluded** | **Excluded** | **Excluded** | **Tier 3** | $T_4$ (Back) |

---

## 7. Recommended Minimum Defensible Descriptive Report

For an offline, front-camera descriptive characterization across the 27 events, the following report structure is mathematically defensible and preserves repository governance:

### 7.1 Proposed Tabular Formats

#### Table 1: Primary Safety Actuation & Detection (Train Events, $N=23$)
| Condition ID | Sensory Modalities | Policy Architecture | Eligible Events | Observable $T_1$ Candidate Events | Evaluable Events ($N_{\text{eval}}$)* | Missed Train Count ($k$) | Missed Train Rate (MTR) [95% Wilson CI] | Mean Warning Lead Time ($s$) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **B0** | Front Vision | 1-frame detection threshold | 23 | 22† | $N_{\text{eval, B0}} \le 22$ | $k_{\text{B0}}$ | $k_{\text{B0}} / N_{\text{eval, B0}}$ $[lo, hi]$ | $\bar{t}_{\text{lead, B0}}$ |
| **B1** | Front Audio | Horn acoustic threshold | 23 | 22† | $N_{\text{eval, B1}} \le 22$ | $k_{\text{B1}}$ | $k_{\text{B1}} / N_{\text{eval, B1}}$ $[lo, hi]$ | $\bar{t}_{\text{lead, B1}}$ |
| **B2** | Front Vision + Audio | Multimodal State Machine | 23 | 22† | $N_{\text{eval, B2}} \le 22$ | $k_{\text{B2}}$ | $k_{\text{B2}} / N_{\text{eval, B2}}$ $[lo, hi]$ | $\bar{t}_{\text{lead, B2}}$ |

\* *Evaluable Denominator Note:* Per `src/railway_detection/evaluation/metrics.py` (lines 298–304, 421–422), an event is evaluable for MTR only if $T_1$ is observable AND a simulation step exists within $|t - T_1| \le 0.25\,\text{s}$. If no step exists within this tolerance, `missed_train` returns `None` and the event is excluded from the denominator. The final denominator must be calculated from valid execution outputs and cannot be assumed to equal 23 or 22 prior to replay.  
† *Event 005 Exclusion:* In candidate proposal records (`data/ground_truth/proposals/train_events/event_005_proposal_v4.json`), `event_005` has $T_1 = \text{null}$ (`candidate_observable: false`) because the train occupied the crossing corridor prior to recording start. It is excluded from the MTR and warning lead time denominators with reason `T1_danger_zone_entry:censored`.

#### Table 2: Gate Kinematics & Stability (Train Events, $N=23$)
| Condition ID | Total Replay Exposure ($s$) | Mean Closed Duration ($s$) | Total Closure Episodes | Mean Closure Episodes per Event | Fault Events |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **B0** | $\sum t_{\text{exp}}$ | $\bar{t}_{\text{closed, B0}}$ | $E_{\text{B0}}$ | $\bar{E}_{\text{B0}}$ | $F_{\text{B0}}$ |
| **B1** | $\sum t_{\text{exp}}$ | $\bar{t}_{\text{closed, B1}}$ | $E_{\text{B1}}$ | $\bar{E}_{\text{B1}}$ | $F_{\text{B1}}$ |
| **B2** | $\sum t_{\text{exp}}$ | $\bar{t}_{\text{closed, B2}}$ | $E_{\text{B2}}$ | $\bar{E}_{\text{B2}}$ | $F_{\text{B2}}$ |

#### Table 3: Negative Control & Nuisance Characterization (No-Train Controls, $N=3$)
| Condition ID | Control Events | Total Exposure ($s$) | Actuated Events | Actuation Rate [95% CI] | Total Blocked Time ($s$) | Closure Episodes |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **B0** | 3 | ~60.0 | $a_{\text{B0}}$ | $a_{\text{B0}}/3$ $[lo, hi]$ | $T_{\text{block, B0}}$ | $E_{\text{ctrl, B0}}$ |
| **B1** | 3 | ~60.0 | $a_{\text{B1}}$ | $a_{\text{B1}}/3$ $[lo, hi]$ | $T_{\text{block, B1}}$ | $E_{\text{ctrl, B1}}$ |
| **B2** | 3 | ~60.0 | $a_{\text{B2}}$ | $a_{\text{B2}}/3$ $[lo, hi]$ | $T_{\text{block, B2}}$ | $E_{\text{ctrl, B2}}$ |

#### Table 4: Engine-Only Edge-Case Characterization (`engine_events/event_001`, $N=1$)
| Condition ID | Event ID | Consist Type | Candidate $T_1$ ($s$) | Passage Blocked at $T_1$ | Warning Lead Time ($s$) | Total Closed Time ($s$) | Closure Episodes |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **B0** | `event_001` | Light Locomotive (0 cars) | 0.00* | $\text{blocked}_{\text{B0}}$ | $t_{\text{lead, B0}}$ | $t_{\text{closed, B0}}$ | $E_{\text{eng, B0}}$ |
| **B1** | `event_001` | Light Locomotive (0 cars) | 0.00* | $\text{blocked}_{\text{B1}}$ | $t_{\text{lead, B1}}$ | $t_{\text{closed, B1}}$ | $E_{\text{eng, B1}}$ |
| **B2** | `event_001` | Light Locomotive (0 cars) | 0.00* | $\text{blocked}_{\text{B2}}$ | $t_{\text{lead, B2}}$ | $t_{\text{closed, B2}}$ | $E_{\text{eng, B2}}$ |

\* *Isolation Note:* Per `src/railway_detection/evaluation/metrics.py` (lines 388–399), engine-only records carry `notes = "engine_event_excluded"` and are strictly excluded from both the train-event denominator (Table 1) and the no-train control denominator (Table 3) to prevent cohort contamination. They are reported as an isolated edge-case characterization.

#### Table 5: Excluded Endpoints Accounting
| Metric Name | Intended Endpoint | Exclusion Status | Formal Exclusion Reason |
| :--- | :--- | :---: | :--- |
| **Premature-Opening Rate** | Safety Hazard (Opening during train passage) | **EXCLUDED** | `T4_tail_clearance:clock_mismatch(annotated on camera_2; replay clocks ['front'])` |
| **Clearance Verification Latency** | Operational Recovery Latency | **EXCLUDED** | `T4_tail_clearance:clock_mismatch(annotated on camera_2; replay clocks ['front'])` |
| **Excess Closed Duration** | Road Traffic Delay Penalty | **EXCLUDED** | `clock_mismatch(T1 on camera_1 & T4 on camera_2 share no replay timeline)` |

---

## 8. Mandatory Scientific Boundaries & Disclaimers

Any report generated under this specification must prominently state:
1. **Descriptive, Single-Site Scope:** All metrics describe empirical software simulation results on recordings collected at a single crossing (`crossing_A`). They do not represent an out-of-sample benchmark or proof of crossing-independent generalization.
2. **No Claim of Leakage-Safe Generalization:** Because recordings stem from two consecutive sessions at one physical location, the data cannot support a split-based test set claim without severe environmental leakage.
3. **Calculability Does Not Equal Physical Safety:** A metric being mathematically calculable on replay simulation does NOT prove physical safety, field reliability, or deployment readiness. Simulated gate kinematics assume ideal motor torque without mechanical wear, relay delay, or wind resistance. No physical functional safety certification (e.g., SIL 4 / CENELEC EN 50126/50128/50129) is claimed.
4. **Distinction Across Evidence Stages:** Results must explicitly distinguish:
   - *Replay-derived simulation behavior:* Raw kinematics and gate states under recorded detections.
   - *Candidate-annotation diagnostic metrics:* Provisional measurements against unapproved proposals.
   - *Human-reviewed labels:* Candidate timestamps audited by an allowlisted human reviewer.
   - *Approved official evaluation results:* Metrics computed under signed researcher authorization (`ADJ-AUTH`, `EVAL-AUTH`).
5. **Left-Censored Arrival Times:** In all 23 train events, locomotives are already in the approach corridor at recording start ($T_0 \le 0.0\,\text{s}$). True detection latency from visual corridor entry is unobservable; warning lead time is bounded by recording duration.
6. **Control Event Statistical Limits:** The negative control cohort consists of only 3 events (~60 seconds of exposure). Nuisance actuations provide qualitative evidence of sensor chatter (e.g., insect/lighting false triggers in `event_002`), but cannot establish continuous operational false-alarm rates per hour.
7. **Clearance Endpoints Omitted:** Clearance latency and premature gate opening are omitted by mathematical necessity due to the absence of back-camera clock synchronization on front-camera replays.

---

## 9. Unresolved Governance & Researcher Decisions

Before executing the front-camera descriptive benchmark, the following items require formal researcher action:

1. **Adjudication of Candidate Ground Truth (`ADJ-AUTH`):**
   - The candidate timestamps in `data/ground_truth/snapshots/candidate_annotation_manifest_20261012.json` must be human-verified and promoted to an approved Stage-2.1 ground-truth artifact before Tier 2 metrics (`missed_train`, `warning_lead_time_s`) can be published with official status.
2. **Descriptive Execution Authorization vs. Split Contract:**
   - The official runner (`Phase12EvaluationRunner.run_official()`) is hardcoded to execute only `partitions["test"]` under a 3-way split. The researcher must decide whether to:
     - (a) Authorize execution via the diagnostic experiment harness (`scripts/run_real_world_experiments.py` / `runner.py`) as a purely descriptive research cohort; or
     - (b) Amend `research_contracts.py` to formally recognize an unpartitioned descriptive evaluation manifest.
3. **Protocol Endpoint Selection for Future Dual-Camera Work:**
   - Formal selection between protocol v9 and M4 premature opening definitions remains open in `docs/PREMATURE_OPENING_DECISION_EVIDENCE.md` and will govern any subsequent dual-camera evaluations.
