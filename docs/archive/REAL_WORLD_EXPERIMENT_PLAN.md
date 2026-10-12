# Real-World Experiment Plan: Multimodal Railway Crossing Safety Evaluation

**Document Version:** 1.0.0
**Date:** 2026-09-23
**Author:** Senior Research Scientist, Experimental Methodologist, ML Systems Architect
**Executing Agent:** Gemini 3.8 Flash (implementation only; methodological decisions frozen herein)
**Authority:** Reconciled against `RESEARCH_PROTOCOL_V2.md`, `EXPERIMENT_PROTOCOL_V2.md`, `EVENT_LABEL_PROTOCOL.md`, `HAZARD_MODEL.md`, and audited source code.

---

## 1. Executive Summary

This document defines a rigorous, publication-quality experimental framework for evaluating a multimodal AI railway level-crossing safety system on 21 previously unseen real-world train-passage events. The framework spans eight benchmark conditions (B0-B7) testing vision-only, audio-only, multimodal fusion, temporal evidence processing, state-machine control, and fault-injection resilience.

**Primary research question:**
> On 21 synchronized, event-labeled, previously unseen real-world train-passage recordings, does a predefined two-camera, audio-assisted, temporal state policy change event-level missed-train and premature-opening outcomes relative to fair simpler baselines?

**Claim boundary:** Results apply only to represented recordings and conditions. No claim of certified safety, field deployment readiness, or crossing-independent generalization is permitted.

> [!CAUTION]
> **RESEARCH SOFTWARE & SIMULATION ONLY.** This system must never be connected to live railway infrastructure. The term "fail-safe" refers strictly to a software-simulated conservative closed-gate policy. No physical safety certification is claimed.

---

## 2. Research Questions

### Primary
**RQ-P:** Does the full multimodal policy (B4) reduce event-level missed-train rate and premature-opening rate compared to simpler baselines (B0-B3) on 21 unseen real-world events?

### Secondary
| ID | Question |
|---|---|
| RQ-1 | How reliably does the frozen YOLOv8n detect trains in unseen real-world video? |
| RQ-2 | How does the standalone audio classifier perform on audio extracted from unseen evaluation videos? |
| RQ-3 | Does a second camera improve event detection over single-camera operation? |
| RQ-4 | Does temporal filtering improve robustness over independent-frame detection? |
| RQ-5 | Does audio fusion improve event recall or warning lead time without unacceptable false alarms? |
| RQ-6 | Does the state-machine policy prevent premature gate opening compared to stateless baselines? |
| RQ-7 | Does the system behave conservatively under simulated sensor failures? |
| RQ-8 | What are the dominant failure modes and their frequencies? |

---

## 3. Hypotheses

| ID | Hypothesis | Test |
|---|---|---|
| H1 | The frozen YOLOv8n will detect front/side/rear in unseen video with per-class recall >= 0.50. | B0 per-class event-level recall |
| H2 | Temporal filtering (B3) will reduce false detections relative to independent-frame (B0) without increasing missed-train rate. | Paired B0 vs B3 |
| H3 | Dual-camera operation (B3) will detect more events than single-camera (B0). | Paired B0 vs B3 |
| H4 | The state-machine policy (B4) will reduce premature-opening rate relative to stateless (B2). | Paired B2 vs B4 |
| H5 | Multimodal fusion (B4) will achieve missed-train rate <= that of B3. | Paired B3 vs B4 |
| H6 | Under single-camera failure (B5), the system will not issue premature openings. | B5 fault scenarios |
| H7 | Under dual-camera failure (B6), the system will remain in FAULT_FAIL_SAFE with gate closed. | B6 fault scenarios |

> [!NOTE]
> With N=21 events, statistical power is limited. Hypotheses are stated for methodological clarity, not as formal power-calculated tests. Results will report descriptive statistics with uncertainty intervals.

---

## 4. Dataset Definitions

### 4.1 Dataset Inventory

| Dataset | Contents | Use | Location |
|---|---|---|---|
| **Dataset V1 (Layer A)** | ~3,157 annotated train images (Train: 2,218, Val: 467, Test: 472) | YOLOv8n training/development (FROZEN) | `data/raw/vision/v1/` |
| **Standalone Audio** | 87 positive + 87 negative recordings | Audio CNN training/development (FROZEN) | `data/raw/audio/train_horn/` |
| **Layer B Events** | 21 events x 2 cameras = 42 videos + embedded audio | **Final unseen evaluation only** | `data/raw/layer_b/videos/event_001/` - `event_021/` |
| **Layer B Extracted Audio** | Audio tracks extracted from 42 videos at evaluation time | **Final unseen audio evaluation only** | `data/processed/layer_b/audio/` (generated during experiment) |

### 4.2 Layer B Event Structure

Each event directory contains:
```
event_NNN/
  camera_front.mov     (approach/primary camera)
  camera_back.mov      (departure/secondary camera)
  camera_rear.mov      (symlink -> camera_back.mov)
```

Camera naming convention for the experiment runner:
- `camera_front.mov` -> `camera_1` (approach side, expected labels: front, side)
- `camera_back.mov` -> `camera_2` (departure side, expected labels: side, rear)

### 4.3 Event Metadata and Labels

Each event requires a `metadata.json` and `labels/event_labels.json` to be created during the annotation phase. Required fields per `EVENT_LABEL_PROTOCOL.md`:
- `crossing_entry` timestamp
- `tail_clearance` timestamp (or `clearance_unobservable`)
- `first_train_visual_appearance` timestamp
- `approach_confirmation` timestamp
- `direction`
- `lighting`, `weather` (when observable)

---

## 5. Data Separation Rules

> [!IMPORTANT]
> **ABSOLUTE ISOLATION INVARIANT:** No data from the 21 Layer B events may influence any model parameter, threshold, or hyperparameter.

### 5.1 Firewall Matrix

| Data Source | Train Model? | Tune Thresholds? | Calibrate? | Evaluate? |
|---|---|---|---|---|
| Dataset V1 (images) | YES YOLOv8n (already frozen) | YES Vision confidence (already frozen) | YES (already frozen) | NO Not for system eval |
| Standalone Audio | YES Audio CNN (already frozen) | YES Audio threshold (already frozen) | YES (already frozen) | NO Not for system eval |
| Layer B Videos | NEVER | NEVER | NEVER | YES Final evaluation |
| Layer B Extracted Audio | NEVER | NEVER | NEVER | YES Final evaluation |

### 5.2 Frozen Parameters

All parameters below were selected using development data only and are frozen before any Layer B evaluation:

| Parameter | Value | Source |
|---|---|---|
| YOLOv8n checkpoint | `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` | Dataset V1 validation |
| Vision confidence threshold | 0.35 (approach), 0.35 (departure) | `decision_engine.py` defaults |
| Audio CNN checkpoint | `models/audio/best_checkpoint.pt` | Standalone audio validation |
| Audio threshold | 0.5184 | Standalone audio validation F1 optimization |
| Temporal confirm_frames | 2 | `decision_engine.py` default |
| Warning dwell | 2.0s | `decision_engine.py` default |
| Gate closing duration | 3.0s | `decision_engine.py` default |
| Gate opening duration | 3.0s | `decision_engine.py` default |
| Clearance dwell | 3.0s | `decision_engine.py` default |
| EMA smoothing alpha | 0.5 | `temporal.py` default |
| Evidence expiry | 3.0s | `temporal.py` default |
| Miss tolerance frames | 2 | `temporal.py` default |

### 5.3 Threshold-Selection Policy

Since all 21 events are reserved for evaluation and no additional development events exist:
1. Vision thresholds use the frozen values from Dataset V1 validation (approach: 0.35, departure: 0.35).
2. Audio threshold uses the frozen value from standalone audio validation (T* = 0.5184).
3. Temporal parameters use the frozen defaults from TemporalConfig.
4. No leave-one-out or cross-validation on Layer B. All 21 events are evaluated with identical frozen parameters.

---

## 6. Experiment Matrix (B0-B7)

> [!IMPORTANT]
> **CRITICAL MISMATCH IDENTIFIED:** The existing `RESEARCH_PROTOCOL_V2.md` S19 defines B0-B7 differently from the user's prompt and from the current `ExperimentRunner` implementation. The table below reconciles all three into the authoritative definition for this experiment plan.

### 6.1 Reconciled Baseline Definitions

| ID | Condition | Cameras | Audio | Temporal | State Machine | Question Answered |
|---|---|---|---|---|---|---|
| **B0** | Vision Only (raw frames) | Front camera only | NO | NO | NO | Baseline single-camera frame-level detection |
| **B1** | Audio Only | NO | YES (extracted from Layer B) | NO | NO | Standalone audio detection capability |
| **B2** | Vision + Audio | Both cameras | YES | NO | NO | Multimodal fusion benefit (no temporal/state) |
| **B3** | Temporal Evidence | Both cameras | NO | YES | NO | Temporal filtering benefit |
| **B4** | Temporal + Multimodal | Both cameras | YES | YES | YES | Full proposed policy |
| **B5** | Camera 1 Failure | Camera 2 only | YES | YES | YES | Front/primary camera failure resilience |
| **B6** | Camera 2 / Dual Failure | Camera 1 only + Dual failure | YES | YES | YES | Departure camera and total camera failure |
| **B7** | Sensor/Timing Robustness | Both cameras (with faults) | YES (with faults) | YES | YES | Audio dropout, frame drops, false detections, timestamp disorder |

### 6.2 Mapping to RESEARCH_PROTOCOL_V2 Baselines

| This Plan | RESEARCH_PROTOCOL_V2 | Rationale |
|---|---|---|
| B0 (Vision Only) | B0 (single-cam independent-frame) | Equivalent |
| B1 (Audio Only) | B4 (audio-only) | Renumbered to match user prompt |
| B2 (Vision + Audio) | B5 (dual-cam + audio, no state) | Renumbered |
| B3 (Temporal Evidence) | B1+B2 (temporal + dual-cam) | Combined |
| B4 (Temporal + Multimodal) | B6 (full proposed policy) | Renumbered |
| B5 (Camera 1 Failure) | B7 subset (source removal) | Subset |
| B6 (Camera 2 / Dual Failure) | B7 subset (source removal) | Subset |
| B7 (Sensor Robustness) | B7 subset (perturbations) | Subset |

---

## 7. Detailed Experiment Specifications

---

### EXPERIMENT B0 -- VISION ONLY (Raw Frames)

#### 7.0.1 Experiment Card

| Field | Value |
|---|---|
| **Experiment ID** | `B0_VISION_ONLY` |
| **Research Question** | RQ-1: How reliably does frozen YOLOv8n detect trains in 21 unseen real-world events? |
| **Hypothesis** | H1: Per-class recall >= 0.50 on unseen video |
| **Dataset** | 21 Layer B events, front camera only (camera_front.mov) |
| **Inputs** | Video frames sampled at 5 FPS from camera_front.mov |
| **Model Version** | YOLOv8n checkpoint `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` |
| **Frozen Components** | YOLOv8n weights, confidence threshold (0.35), image size (640x640) |
| **Independent Variable** | Real-world event identity (event_001-event_021) |
| **Controlled Variables** | Model, threshold, sampling rate, image size |
| **Dependent Variables** | Detection counts, confidence values, class labels per frame |

#### 7.0.2 Evaluation Metrics

**Frame-Level:**
- Per-class detection count (front, side, rear)
- Per-frame confidence distribution
- Detection presence binary per frame
- False detection rate on empty frames

**Event-Level:**
- Event detection rate (was any train detected?)
- Per-event per-class detection presence
- Detection continuity (% of event frames with detection)
- Detection onset latency (first detection frame vs ground-truth first_train_visual_appearance)
- Front detection presence, side detection presence, rear detection presence
- Confidence distribution per event

**Temporal:**
- Detection timeline per event
- Front -> Side -> Rear temporal progression
- Detection gaps (consecutive frames without detection)
- Maximum detection gap duration (seconds)

#### 7.0.3 Failure Criteria
- Missed train event: zero detections across entire event
- Late detection: first detection > 5s after ground-truth visual appearance
- False detection: detection with confidence >= 0.35 during confirmed no-train interval

#### 7.0.4 Required Outputs
- `results/experiments/B0/per_frame_detections.jsonl`
- `results/experiments/B0/per_event_summary.json`
- `results/experiments/B0/confidence_distributions.json`
- `results/experiments/B0/detection_timelines.json`
- `results/experiments/B0/summary.json`

---

### EXPERIMENT B1 -- AUDIO ONLY

#### 7.1.1 Experiment Card

| Field | Value |
|---|---|
| **Experiment ID** | `B1_AUDIO_ONLY` |
| **Research Question** | RQ-2: How well does the audio classifier detect trains in unseen evaluation audio? |
| **Hypothesis** | Audio will detect horn events but cannot determine approach/departure/clearance |
| **Dataset** | Audio extracted from 21 Layer B events (42 videos) |
| **Inputs** | Extracted 16kHz mono WAV from each video, windowed at 1.0s/0.5s hop |
| **Model Version** | CompactTrainHornCNN checkpoint `models/audio/best_checkpoint.pt` |
| **Frozen Components** | CNN weights, threshold (T* = 0.5184), feature normalization |
| **Independent Variable** | Event identity, camera source (front audio vs back audio) |
| **Controlled Variables** | Model, threshold, window size, hop size, sample rate |
| **Dependent Variables** | Per-window prediction, confidence, event-level detection |

#### 7.1.2 Evaluation Metrics

**Window-Level:**
- Precision, Recall, F1 (requires ground-truth audio annotation)
- Confidence distribution (positive vs negative windows)
- Threshold sensitivity analysis at fixed thresholds [0.3, 0.4, 0.5, 0.5184, 0.6, 0.7]

**Event-Level:**
- Event-level horn detection rate (any window >= threshold)
- False alarm rate per hour of non-train audio (if no-train intervals exist)
- Detection onset latency relative to first_train_audible_evidence

**Safety Invariant Verification:**
- Confirm: audio NEVER authorizes gate opening
- Confirm: audio_safety_role: "supporting_only" in all records

#### 7.1.3 Failure Criteria
- Audio false negative: horn confirmed audible but no audio detection
- Audio false positive: confident detection during confirmed silence

#### 7.1.4 Important Methodological Note
Since the 21 events contain only train-present recordings, continuous no-train exposure is limited. False alarm rate per hour may not be evaluable from these events alone. This limitation must be stated.

#### 7.1.5 Required Outputs
- `results/experiments/B1/per_window_predictions.jsonl`
- `results/experiments/B1/per_event_audio_summary.json`
- `results/experiments/B1/audio_confidence_distribution.json`
- `results/experiments/B1/summary.json`

---

### EXPERIMENT B2 -- VISION + AUDIO (No Temporal, No State Machine)

#### 7.2.1 Experiment Card

| Field | Value |
|---|---|
| **Experiment ID** | `B2_VISION_AUDIO` |
| **Research Question** | RQ-5: Does combining vision + audio improve event detection? |
| **Hypothesis** | Multimodal fusion detects more events than either modality alone |
| **Dataset** | 21 Layer B events, both cameras + extracted audio |
| **Inputs** | Frame detections + audio evidence records, no temporal smoothing |
| **Frozen Components** | All model weights, all thresholds |
| **Independent Variable** | Event identity |
| **Dependent Variables** | Event detection rate, missed events, false alarms |

#### 7.2.2 Policy
Stateless detection: at each timestep, if vision OR audio detects train -> close gate. If neither detects train -> open gate (demonstrating the danger of stateless policy).

Audio invariant maintained: audio can trigger closure but NEVER opening.

#### 7.2.3 Evaluation Metrics
- Event detection rate, missed-train rate, premature-opening rate
- Warning lead time, excess closed duration
- Comparison: B0 (vision-only) vs B1 (audio-only) vs B2 (combined)

---

### EXPERIMENT B3 -- TEMPORAL EVIDENCE

#### 7.3.1 Experiment Card

| Field | Value |
|---|---|
| **Experiment ID** | `B3_TEMPORAL` |
| **Research Question** | RQ-4: Does temporal filtering improve robustness? |
| **Hypothesis** | H2-H3: Temporal confirmation reduces false detections |
| **Dataset** | 21 Layer B events, both cameras, no audio |
| **Inputs** | Frame detections processed through temporal confirmation logic |
| **Frozen Components** | All model weights, temporal parameters (confirm_frames=2, smoothing_alpha=0.5, miss_tolerance=2, evidence_expiry=3.0s) |
| **Independent Variable** | Event identity |
| **Controlled Variables** | Temporal config frozen from development defaults |
| **Dependent Variables** | Detection continuity, false detection rate, event metrics |

#### 7.3.2 Temporal Parameters Under Test
All frozen (no tuning on Layer B):

| Parameter | Value | Justification |
|---|---|---|
| confirm_frames | 2 | Minimum confirmation before upgrade to WARNING |
| smoothing_alpha | 0.5 | EMA balance between responsiveness and noise |
| miss_tolerance_frames | 2 | Brief occlusion tolerance |
| evidence_expiry_s | 3.0 | Maximum stale evidence age |
| confirm_window_s | 0.5 | Time-based confirmation alternative |

#### 7.3.3 Comparison Design
- B0 vs B3: Effect of temporal + dual-camera over raw single-camera
- Frame-level detection rates before/after temporal filtering
- Detection gap distribution before/after

---

### EXPERIMENT B4 -- TEMPORAL + MULTIMODAL (Full Policy)

#### 7.4.1 Experiment Card

| Field | Value |
|---|---|
| **Experiment ID** | `B4_FULL_POLICY` |
| **Research Question** | RQ-P: Does the full proposed policy improve event safety? |
| **Hypothesis** | H4-H5: State machine prevents premature opening; multimodal reduces missed events |
| **Dataset** | 21 Layer B events, both cameras + extracted audio |
| **Inputs** | Full pipeline: video -> YOLO -> temporal -> audio -> fusion -> decision engine -> state machine -> gate model |
| **Frozen Components** | All model weights, all thresholds, all temporal/state parameters |
| **Independent Variable** | Event identity |
| **Dependent Variables** | All primary and secondary safety endpoints |

#### 7.4.2 Complete Event Lifecycle Evaluation

For each event, trace the complete state progression:
```
IDLE -> TRAIN_APPROACHING -> WARNING -> GATE_CLOSING -> TRAIN_PRESENT
-> CROSSING_OCCUPIED -> TRAIN_DEPARTING -> REAR_CONFIRMED
-> CROSSING_CLEAR -> GATE_OPENING -> IDLE
```

Evaluate:
- Did the system detect the approaching train?
- Was the gate fully closed before ground-truth crossing_entry?
- Did the gate remain closed during occupancy?
- Was rear/departure evidence correctly identified?
- Was clearance properly verified before opening?
- Was the correct state sequence observed?

#### 7.4.3 Primary Safety Endpoints (Formal Definitions)

**Missed-Train Rate (MTR):**
```
numerator   = count of evaluable events where is_passage_blocked == False
              at the simulation step closest to crossing_entry_s (within +/-0.25s)
denominator = count of evaluable events with observable crossing_entry
MTR = numerator / denominator
```
Report Wilson 95% CI.

**Premature-Opening Rate (POR):**
```
numerator   = count of evaluable events where gate_state in {OPENING, OPEN}
              AND is_passage_blocked == False
              at any simulation step t where crossing_entry_s <= t < tail_clearance_s
denominator = count of evaluable events with observable tail_clearance
POR = numerator / denominator
```
Report Wilson 95% CI.

#### 7.4.4 Secondary Endpoints

| Metric | Definition | Unit |
|---|---|---|
| Warning Lead Time | crossing_entry_s - first_step_where(state == WARNING).timestamp_s. Positive = warning before entry. Report distribution (median, IQR, min, max). | seconds |
| Clearance Latency | first_step_where(state in {GATE_OPENING, CROSSING_CLEAR} AND t >= tail_clearance_s).timestamp_s - tail_clearance_s. Report distribution. | seconds |
| Excess Closed Duration | total_closed_s - max(0, tail_clearance_s - crossing_entry_s). Negative values clipped to 0. Report distribution. | seconds |
| Detection Latency | first_step_with_any_detection.timestamp_s - first_train_visual_appearance_s. Report distribution. | seconds |
| Event Completion Rate | events reaching IDLE after GATE_OPENING / total evaluable events. | proportion |
| Fault Recognition Latency | (B5-B7 only) first_step_where(state == FAULT_FAIL_SAFE).timestamp_s - fault_injection_start_s. | seconds |

---

### EXPERIMENT B5 -- CAMERA 1 (FRONT) FAILURE

#### 7.5.1 Experiment Card

| Field | Value |
|---|---|
| **Experiment ID** | `B5_CAMERA1_FAILURE` |
| **Research Question** | RQ-7: How does the system behave when the front camera fails? |
| **Hypothesis** | H6: System detects train via camera_2 and audio; no premature opening |
| **Dataset** | 21 Layer B events with camera_1 evidence removed |
| **Inputs** | Full pipeline with FailureMode.CAMERA_1_DROPOUT injected |

#### 7.5.2 Sub-Experiments

| Sub-ID | Failure Timing | Rationale |
|---|---|---|
| B5a | Camera 1 fails at event start (full duration) | Complete approach camera loss |
| B5b | Camera 1 fails midway through event | Degradation during passage |
| B5c | Camera 1 fails intermittently (2s on / 2s off) | Flapping sensor |

#### 7.5.3 Evaluation
- Missed-train rate under single-camera operation
- Premature-opening rate
- Gate state behavior trace
- Time from camera failure to fault recognition
- Degraded-mode detection capability

---

### EXPERIMENT B6 -- CAMERA 2 / DUAL SENSOR FAILURE

#### 7.6.1 Experiment Card

| Field | Value |
|---|---|
| **Experiment ID** | `B6_CAMERA2_DUAL_FAILURE` |
| **Research Question** | RQ-7: Does the system remain conservative when cameras fail? |
| **Hypothesis** | H7: System enters FAULT_FAIL_SAFE and never opens gate |
| **Dataset** | 21 Layer B events with camera_2 and/or all cameras removed |

#### 7.6.2 Sub-Experiments

| Sub-ID | Failure Mode | Rationale |
|---|---|---|
| B6a | Camera 2 dropout (full event) | Departure camera loss -> clearance unobservable |
| B6b | Both cameras fail simultaneously | Total vision loss |
| B6c | Both cameras fail sequentially (camera_1 at 30%, camera_2 at 60%) | Progressive degradation |

#### 7.6.3 Safety Invariant Tests
- CRITICAL: Gate must NEVER open when all vision sources have failed
- CRITICAL: Loss of visual evidence must NOT be interpreted as CLEAR
- System must enter FAULT_FAIL_SAFE with gate CLOSED
- Recovery behavior after sources restore (if applicable)

---

### EXPERIMENT B7 -- SENSOR / TIMING / FALSE-DETECTION ROBUSTNESS

#### 7.7.1 Experiment Card

| Field | Value |
|---|---|
| **Experiment ID** | `B7_ROBUSTNESS` |
| **Research Question** | RQ-7: How robust is the system to various sensor degradations? |
| **Dataset** | 21 Layer B events with specific perturbations applied |

#### 7.7.2 Sub-Experiments

| Sub-ID | FailureMode | Parameters | Rationale |
|---|---|---|---|
| B7a | AUDIO_DROPOUT | Full event duration | No acoustic evidence |
| B7b | DROPPED_FRAMES | 30% of frames dropped randomly | Frame loss |
| B7c | FALSE_DETECTION | Label=front, confidence=0.85, at random times | Spurious detection |
| B7d | OUT_OF_ORDER_FRAMES | Adjacent frame swaps in middle 20% | Timestamp disorder |
| B7e | STALE_TIMESTAMPS | Timestamps frozen for 2s midway | Stale evidence |
| B7f | Combined: AUDIO_DROPOUT + DROPPED_FRAMES (10%) | Simultaneous degradation | Multi-fault |

#### 7.7.3 Expected Behaviors per Sub-Experiment

| Sub-ID | Expected Gate Behavior | Expected State |
|---|---|---|
| B7a | Normal vision operation; audio supporting evidence absent | Normal lifecycle without audio boost |
| B7b | Degraded detection continuity; temporal persistence should compensate | Normal or delayed lifecycle |
| B7c | False closure triggered; system should maintain conservatively | May trigger WARNING/CLOSING spuriously |
| B7d | Out-of-order rejection by decision engine Rule 8 | Frame rejected; state unchanged |
| B7e | Stale evidence detected and rejected | Conservative hold |
| B7f | Compound degradation | Degraded but conservative |

---

## 8. Variables Summary

### 8.1 Independent Variables
- Event identity (event_001 - event_021)
- Benchmark condition (B0-B7)
- Failure injection mode and timing (B5-B7)

### 8.2 Controlled Variables (Frozen)
- YOLOv8n architecture and weights
- Audio CNN architecture and weights
- All confidence thresholds
- All temporal parameters
- All state-machine timing parameters
- Frame sampling rate (5 FPS)
- Audio window (1.0s) and hop (0.5s)
- Image input size (640x640)

### 8.3 Dependent Variables
- Per-frame detection presence and confidence
- Per-event safety outcomes (missed/premature/correct)
- Gate state timeline
- Crossing state timeline
- Warning lead time
- Clearance latency
- Excess closed duration
- Fault recognition latency
- Detection continuity

---

## 9. Evaluation Metrics -- Formal Definitions

### 9.1 Primary Safety Endpoints

#### Missed-Train Rate (MTR)
```
numerator   = count of evaluable events where is_passage_blocked == False
              at the simulation step closest to crossing_entry_s (within +/-0.25s)
denominator = count of evaluable events with observable crossing_entry
MTR = numerator / denominator
```
Report Wilson 95% CI.

#### Premature-Opening Rate (POR)
```
numerator   = count of evaluable events where gate_state in {OPENING, OPEN}
              AND is_passage_blocked == False
              at any simulation step t where crossing_entry_s <= t < tail_clearance_s
denominator = count of evaluable events with observable tail_clearance
POR = numerator / denominator
```
Report Wilson 95% CI.

### 9.2 Secondary Endpoints

| Metric | Computation |
|---|---|
| **Warning Lead Time** | crossing_entry_s - first_step_where(state == WARNING).timestamp_s. Positive = warning before entry. Report distribution (median, IQR, min, max). |
| **Clearance Latency** | first_step_where(state in {GATE_OPENING, CROSSING_CLEAR} AND t >= tail_clearance_s).timestamp_s - tail_clearance_s. Report distribution. |
| **Excess Closed Duration** | total_closed_s - max(0, tail_clearance_s - crossing_entry_s). Negative values clipped to 0. Report distribution. |
| **Detection Latency** | first_step_with_any_detection.timestamp_s - first_train_visual_appearance_s. Report distribution. |
| **Event Completion Rate** | events reaching IDLE after GATE_OPENING / total evaluable events. |
| **Fault Recognition Latency** | (B5-B7 only) first_step_where(state == FAULT_FAIL_SAFE).timestamp_s - fault_injection_start_s. |
| **False Alarm Rate** | false closure events / hours of no-train recording. May be not_evaluable if no no-train intervals exist. |

### 9.3 Frame-Level Vision Metrics (B0 Only)
- Per-class detection count per event
- Per-class detection rate (frames with class detected / total frames)
- Confidence distribution per class
- Detection continuity (longest uninterrupted detection run / total frames)

---

## 10. Statistical Analysis Plan

### 10.1 Primary Analysis Unit
The train-passage **event** (N=21). Frame-level or window-level metrics are diagnostic only and cannot substitute for event-level conclusions.

### 10.2 Confidence Intervals
- **Proportions** (missed-train rate, premature-opening rate): Wilson score 95% CI (already implemented in `evaluation/metrics.py`).
- **Continuous metrics** (lead time, latency): Bootstrap 95% CI with 10,000 resamples at event level, or report median +/- IQR when distribution is skewed.

### 10.3 Paired Comparisons
For B0-B4 comparisons, use paired event-level differences on the same 21 events:
- For each event, compute metric_B4[event_i] - metric_B0[event_i]
- Report mean paired difference and 95% bootstrap CI
- Report sign test p-value (non-parametric; appropriate for N=21)
- Do NOT claim statistical significance if CI crosses zero

### 10.4 Small-Sample Limitations
With N=21 events:
- Wilson CI for proportions near 0% or 100% will be wide (e.g., 0/21 -> CI [0.0%, 14.9%])
- Paired t-tests have limited power; report effect sizes
- Do not perform crossing-level hierarchical analysis (insufficient crossing diversity data)
- Label all analyses as **exploratory** given sample size

### 10.5 Multiple Comparisons
- Pre-specify primary comparisons: B0 vs B4, B3 vs B4
- All other comparisons are secondary/exploratory and labeled as such
- No Bonferroni correction applied (insufficient power; transparency preferred)

---

## 11. Failure Taxonomy

### 11.1 Failure Categories

| Code | Category | Modality | Severity | Description |
|---|---|---|---|---|
| F01 | Missed Approach | Vision | Critical | No front/side detection before crossing_entry |
| F02 | Missed Front | Vision | High | No front class detected during approach phase |
| F03 | Missed Side | Vision | Medium | No side class detected during passage |
| F04 | Missed Rear | Vision | High | No rear class detected during departure |
| F05 | Late Detection | Vision | High | First detection > 3s after ground-truth appearance |
| F06 | False Train Detection | Vision | Medium | Detection with conf >= 0.35 during confirmed no-train |
| F07 | Background False Positive | Vision | Low | Transient low-confidence false detection |
| F08 | Detection Dropout | Vision | Medium | >= 5 consecutive frames without detection during train presence |
| F09 | Incorrect Temporal State | Temporal | High | State machine in wrong state for current event phase |
| F10 | Incorrect Clearance | State Machine | Critical | Gate opens before tail clearance |
| F11 | Audio False Positive | Audio | Medium | Audio detection during confirmed no-horn interval |
| F12 | Audio False Negative | Audio | Medium | No audio detection during confirmed horn interval |
| F13 | Multimodal Disagreement | Fusion | Medium | Vision and audio provide conflicting evidence |
| F14 | Camera Failure Undetected | Sensor | Critical | Camera fails but system does not enter FAULT_FAIL_SAFE |
| F15 | Dual Camera Failure | Sensor | Critical | Both cameras fail; system must remain closed |
| F16 | Timestamp Disorder | Timing | Medium | Out-of-order evidence arrives |
| F17 | Premature Opening | Safety | Critical | Gate opens before ground-truth clearance |
| F18 | Unnecessary Prolonged Closure | Efficiency | Low | Gate remains closed > 30s after clearance |

### 11.2 Failure Record Schema

Every failure instance must be recorded with:
```json
{
  "failure_id": "F01_event_003_B4",
  "event_id": "event_003",
  "condition": "B4",
  "camera": "camera_1",
  "timestamp_s": 5.2,
  "modality": "vision",
  "system_state": "IDLE",
  "gate_state": "OPEN",
  "decision_explanation": "No qualified approach detected",
  "confidence": null,
  "failure_category": "F01",
  "severity": "critical",
  "evidence_snapshot": {"vision": [], "audio": []}
}
```

---

## 12. Safety Criteria

### 12.1 Absolute Safety Invariants (Must Pass for All Conditions)

| Invariant | Description | Verification |
|---|---|---|
| **INV-1** | Audio NEVER independently authorizes gate opening | Check: no state transition to GATE_OPENING where only audio evidence present |
| **INV-2** | Loss of sensor evidence NEVER implies CLEAR | Check: no transition to CROSSING_CLEAR when sources unavailable |
| **INV-3** | Dual camera failure -> FAULT_FAIL_SAFE | Check: all-vision-failed triggers FAULT_FAIL_SAFE in B6b/B6c |
| **INV-4** | Out-of-order timestamps are rejected | Check: Rule 8 fires; no unsafe state change |
| **INV-5** | Gate opening requires positive departure evidence + clearance dwell | Check: no GATE_OPENING without prior REAR_CONFIRMED -> CROSSING_CLEAR |
| **INV-6** | New train during opening cancels opening | Check: Rule 7 fires; transition to GATE_CLOSING |

### 12.2 Invariant Test Matrix

Each invariant is tested under the conditions where it is most likely to be violated. Failure of ANY invariant constitutes a system-level failure requiring code correction before reporting results.

---

## 13. Visualization Plan

### 13.1 Figure Specifications

#### Figure 1: Vision Per-Event Detection Heatmap
- X-axis: Event ID (event_001 - event_021)
- Y-axis: Detection class (front, side, rear)
- Cell value: Detection rate (% frames with class detected), color-coded
- Grouping: One row per class
- Data source: B0 per-frame detections
- Filename: `fig01_vision_event_heatmap.png`
- Publication: Suitable for IEEE full-page figure

#### Figure 2: Vision Confidence Distribution
- X-axis: Confidence score [0.0, 1.0]
- Y-axis: Density / count
- Grouping: One histogram per class (front, side, rear), overlaid
- Data source: B0 all-frame detections
- Filename: `fig02_vision_confidence_dist.png`
- Publication: Supplementary

#### Figure 3: Vision PR Curves (Per-Class)
- X-axis: Recall [0.0, 1.0]
- Y-axis: Precision [0.0, 1.0]
- Grouping: One curve per class, legend with AP values
- Units: Proportion
- Data source: B0 frame-level detections vs annotated ground truth
- Filename: `fig03_vision_pr_curves.png`
- Interpretation: Detection quality at various thresholds
- Publication: Main paper

#### Figure 4: Detection Timeline (Representative Event)
- X-axis: Time (seconds)
- Y-axis: Top panel: detected classes as categorical markers; Bottom panel: confidence
- Grouping: Stacked panels for camera_1 and camera_2
- Data source: B0 or B4 per-frame detections for one representative event
- Filename: `fig04_detection_timeline_example.png`
- Publication: Main paper

#### Figure 5: Front -> Side -> Rear Temporal Progression
- X-axis: Normalized event time [0%, 100%]
- Y-axis: Mean detection rate across events
- Grouping: Three lines (front, side, rear)
- Data source: B0 per-frame detections, all 21 events averaged
- Filename: `fig05_viewpoint_temporal_progression.png`
- Interpretation: Validates expected approach (front->side) and departure (side->rear) sequence
- Publication: Main paper

#### Figure 6: Audio Confidence Distribution (Layer B)
- X-axis: Prediction confidence [0.0, 1.0]
- Y-axis: Count / density
- Grouping: Separate colors for horn-present vs horn-absent windows (if annotated)
- Data source: B1 audio window predictions
- Filename: `fig06_audio_confidence_layerb.png`
- Publication: Supplementary

#### Figure 7: Audio ROC Curve (Standalone + Layer B)
- X-axis: False Positive Rate
- Y-axis: True Positive Rate
- Grouping: Two curves: standalone test set (already generated), Layer B audio
- Data source: B1 predictions + standalone test predictions
- Filename: `fig07_audio_roc_comparison.png`
- Interpretation: Generalization gap from curated audio to real-world embedded audio
- Publication: Main paper

#### Figure 8: Audio PR Curve (Layer B)
- X-axis: Recall
- Y-axis: Precision
- Data source: B1 predictions on Layer B audio
- Filename: `fig08_audio_pr_layerb.png`
- Publication: Supplementary

#### Figure 9: Vision vs Audio vs Fusion Comparison
- X-axis: Condition (B0, B1, B2, B3, B4)
- Y-axis: Event-level metrics (detection rate, missed-train rate)
- Grouping: Grouped bar chart with error bars (Wilson CI)
- Data source: All condition summaries
- Filename: `fig09_modality_comparison.png`
- Publication: Main paper

#### Figure 10: Multimodal Evidence Timeline (Representative Event)
- X-axis: Time (seconds)
- Y-axis: Panel 1: Vision evidence (front/side/rear confidence); Panel 2: Audio evidence (horn confidence); Panel 3: Crossing state; Panel 4: Gate angle (degrees)
- Grouping: 4-panel stacked figure
- Data source: B4 simulation for one event
- Filename: `fig10_multimodal_timeline.png`
- Publication: Main paper (full page)

#### Figure 11: Gate State Timeline Comparison
- X-axis: Time (seconds)
- Y-axis: Gate angle (0-90 degrees)
- Grouping: Overlaid lines for B0, B3, B4 on same event
- Data source: Simulation results for one representative event
- Filename: `fig11_gate_comparison_timeline.png`
- Interpretation: Visual proof that state machine prevents premature opening
- Publication: Main paper

#### Figure 12: Temporal Smoothing Comparison
- X-axis: Time (seconds)
- Y-axis: Raw confidence vs smoothed confidence
- Grouping: Two lines (raw, smoothed) for one class on one event
- Data source: B0 raw detections vs B3 temporal-filtered detections
- Filename: `fig12_temporal_smoothing.png`
- Publication: Supplementary

#### Figure 13: B0-B7 Benchmark Comparison (Primary Endpoints)
- X-axis: Condition ID
- Y-axis: Rate (%)
- Grouping: Dual bars: Missed-Train Rate (red), Premature-Opening Rate (orange)
- Error bars: Wilson 95% CI
- Data source: All condition cohort summaries
- Filename: `fig13_benchmark_comparison.png`
- Publication: Main paper

#### Figure 14: Warning Lead-Time Distribution
- X-axis: Warning lead time (seconds)
- Y-axis: Count / density
- Grouping: One histogram per condition (B0, B3, B4)
- Data source: Per-event warning lead times
- Filename: `fig14_warning_leadtime_dist.png`
- Publication: Main paper

#### Figure 15: Clearance Latency Distribution
- X-axis: Clearance latency (seconds)
- Y-axis: Count / density
- Grouping: One histogram for B4
- Data source: Per-event clearance latency
- Filename: `fig15_clearance_latency_dist.png`
- Publication: Main paper

#### Figure 16: Per-Event Safety Outcome Matrix
- X-axis: Event ID (event_001-event_021)
- Y-axis: Condition (B0-B7)
- Cell value: Color-coded outcome (correct, missed, premature, not evaluable)
- Data source: All per-event evaluations
- Filename: `fig16_safety_outcome_matrix.png`
- Publication: Main paper

#### Figure 17: Failure Injection Results
- X-axis: Failure scenario (B5a-B7f)
- Y-axis: Missed-train rate (%) and premature-opening rate (%)
- Grouping: Stacked bars
- Data source: B5-B7 evaluations
- Filename: `fig17_failure_injection_results.png`
- Publication: Main paper

#### Figure 18: Failure Category Distribution
- X-axis: Failure category (F01-F18)
- Y-axis: Occurrence count
- Grouping: By condition
- Data source: Failure analysis records
- Filename: `fig18_failure_taxonomy_dist.png`
- Publication: Supplementary

#### Figure 19: Fault Recognition Latency
- X-axis: Fault scenario
- Y-axis: Time to FAULT_FAIL_SAFE (seconds)
- Data source: B5-B6 fault experiments
- Filename: `fig19_fault_recognition_latency.png`
- Publication: Supplementary

#### Figure 20: Failure Case Visualizations
- Grid of annotated video frames showing representative failure cases
- Overlaid bounding boxes with confidence values
- One column per failure category
- Filename: `fig20_failure_case_gallery.png`
- Publication: Main paper

All figures: 300 DPI, matplotlib, bbox_inches='tight'.

---

## 14. Publication Table Plan

### Table 1 -- Dataset Composition

| Column | Content |
|---|---|
| Dataset Layer | A (Vision Images) / A (Audio) / B (Events) |
| Total Samples | Image count / recording count / event count |
| Classes | front/side/rear or positive/negative |
| Split | Train/Val/Test counts |
| Use | Model development / Final evaluation |
| Leakage Protection | Group-disjoint / fully held-out |

### Table 2 -- Vision Model Configuration

| Column | Content |
|---|---|
| Architecture | YOLOv8n |
| Image Size | 640x640 |
| Epochs | 100 |
| Classes | front (0), rear (1), side (2) |
| Training Data | Dataset V1: 2,218 train / 467 val |
| Checkpoint | SHA-256 hash of best.pt |
| Dev Baseline mAP@50 | 0.9946 (development_fallback split, NOT generalization claim) |

### Table 3 -- Audio Model Configuration

| Column | Content |
|---|---|
| Architecture | CompactTrainHornCNN (25,697 params) |
| Input | 64-band Log-Mel (64x61) |
| Window | 1.0s, hop 0.5s, 16kHz mono |
| Positive/Negative | 87/87 recordings |
| Split | 61/13/13 (group-disjoint) |
| Operating Threshold | T* = 0.5184 |
| Dev Test ROC-AUC | 0.8868 |

### Table 4 -- Vision Performance on Layer B (B0)

| Column | Content |
|---|---|
| Event ID | event_001-event_021 |
| Front Detected | Yes/No |
| Side Detected | Yes/No |
| Rear Detected | Yes/No |
| Detection Onset (s) | First detection time |
| Detection Continuity (%) | % frames with any detection |
| Mean Confidence | Mean detection confidence |

### Table 5 -- Audio Performance on Layer B (B1)

| Column | Content |
|---|---|
| Metric | Value |
| Total Windows | Count |
| Detection Rate (>= threshold) | % |
| Mean Confidence | Value |
| Event-Level Detection | X/21 events |

### Table 6 -- Modality Comparison (B0-B4)

| Column | Content |
|---|---|
| Condition | B0, B1, B2, B3, B4 |
| Events | 21 |
| Missed-Train Rate [95% CI] | % |
| Premature-Opening Rate [95% CI] | % or not_evaluable |
| Mean Warning Lead Time | seconds |
| Mean Excess Closed | seconds |

### Table 7 -- Temporal Evidence Comparison

| Column | Content |
|---|---|
| Metric | B0 (no temporal) vs B3 (temporal) |
| Mean Detection Gaps | Before / after |
| Max Gap Duration | Before / after |
| Detection Continuity | Before / after |
| Missed Events | Before / after |

### Table 8 -- Multimodal Fusion Results (B4 Full Policy)

| Column | Content |
|---|---|
| Event ID | event_001-event_021 |
| Detected | Yes/No |
| Premature Opening | Yes/No/Not evaluable |
| Warning Lead Time (s) | Value |
| Clearance Latency (s) | Value |
| Lifecycle Complete | Yes/No |
| Failure Codes | F01-F18 |

### Table 9 -- Primary Safety Endpoint Results

| Column | Content |
|---|---|
| Condition | B0-B7 |
| MTR [95% CI] | Missed-train rate |
| POR [95% CI] | Premature-opening rate |
| Events | Total / Eligible |

### Table 10 -- Failure Injection Results (B5-B7)

| Column | Content |
|---|---|
| Scenario | B5a-B7f |
| Failure Mode | Description |
| Events | 21 |
| MTR | % |
| POR | % |
| Fault Detected | Yes/No per event |
| FAULT_FAIL_SAFE Entered | Yes/No per event |
| Invariant Violations | Count |

### Table 11 -- Per-Event Evaluation Summary

| Column | Content |
|---|---|
| Event ID | event_001-event_021 |
| Duration (s) | Video duration |
| Direction | Direction of train |
| B0 Outcome | correct/missed/premature |
| B4 Outcome | correct/missed/premature |
| B5 Outcome | correct/missed/premature |
| Failure Codes | List |

### Table 12 -- Failure Analysis Summary

| Column | Content |
|---|---|
| Failure Category | F01-F18 |
| Total Occurrences | Count across all conditions |
| Most Affected Condition | Condition ID |
| Most Affected Event | Event ID |
| Root Cause | Brief description |

---

## 15. Artifact Directory Structure

```
results/experiments/
  manifests/
    experiment_manifest.json
    layer_b_event_manifest.json
    frozen_parameters.json
    evaluation_labels.json
  B0/
    per_frame_detections.jsonl
    per_event_summary.json
    confidence_distributions.json
    detection_timelines.json
    summary.json
    single_events.json
  B1/
    per_window_predictions.jsonl
    per_event_audio_summary.json
    audio_confidence_distribution.json
    summary.json
  B2/
    simulation_traces/
    summary.json
    single_events.json
  B3/
    temporal_filtered_detections.jsonl
    simulation_traces/
    summary.json
    single_events.json
  B4/
    simulation_traces/
    state_timelines/
    summary.json
    single_events.json
    failure_analysis.json
  B5/
    B5a/ B5b/ B5c/
    summary.json
    single_events.json
  B6/
    B6a/ B6b/ B6c/
    summary.json
    single_events.json
  B7/
    B7a/ B7b/ B7c/ B7d/ B7e/ B7f/
    summary.json
    single_events.json
  figures/
    fig01_vision_event_heatmap.png
    ... (20 figures total)
    fig20_failure_case_gallery.png
  tables/
    table01_dataset_composition.md
    table01_dataset_composition.csv
    table01_dataset_composition.tex
    ... (12 tables, each in md/csv/tex)
    table12_failure_analysis.md
  statistical_analysis/
    paired_comparisons.json
    confidence_intervals.json
    bootstrap_results.json
  report/
    experiment_report.md
```

---

## 16. Reproducibility Requirements

Every experiment run must record:

| Item | Source | Storage |
|---|---|---|
| Git commit hash | `git rev-parse HEAD` | experiment_manifest.json |
| Experiment ID | UUID or formatted ID | experiment_manifest.json |
| YOLOv8n checkpoint SHA-256 | `sha256sum best.pt` | experiment_manifest.json |
| Audio checkpoint SHA-256 | `sha256sum best_checkpoint.pt` | experiment_manifest.json |
| Layer B video manifest SHA-256 | SHA-256 of all 42 video files | layer_b_event_manifest.json |
| Configuration hash | SHA-256 of frozen_parameters.json | experiment_manifest.json |
| Random seed | 42 (deterministic) | experiment_manifest.json |
| Python version | `python --version` | experiment_manifest.json |
| Package versions | `pip freeze` | experiment_manifest.json |
| Timestamp (UTC) | ISO-8601 | experiment_manifest.json |
| Command used | Full command line | experiment_manifest.json |
| All parameters | Frozen parameter dump | frozen_parameters.json |
| Output paths | Relative to repo root | experiment_manifest.json |

---

## 17. Parameter-Freezing Policy

1. All model weights are frozen before any Layer B data is accessed.
2. All confidence thresholds are frozen from development-data optimization.
3. All temporal parameters use development defaults.
4. All state-machine timing parameters use development defaults.
5. No parameter may be modified after inspecting any Layer B result.
6. If a parameter change is necessary due to a discovered bug, a new experiment run must be created with a new run ID; the previous run must not be overwritten.

---

## 18. Threshold-Selection Policy

Since the 21 Layer B events constitute the entirety of available real-world evaluation data:

1. **No threshold tuning on Layer B.** All thresholds are frozen from development data.
2. **Sensitivity analysis is exploratory.** Threshold sensitivity curves are presented for insight but do not influence the reported primary results.
3. **If future events become available,** a calibration/validation subset may be created. Until then, the honest limitation is that thresholds were not optimized for the real-world distribution.

---

## 19. Leakage-Prevention Policy

### 19.1 Forbidden Operations
1. Training any model on Layer B video frames
2. Training audio model on Layer B extracted audio
3. Selecting thresholds to optimize Layer B metrics
4. Tuning temporal parameters using Layer B events
5. Adding Layer B frames to Dataset V1
6. Using Layer B audio in the standalone audio dataset
7. Examining Layer B results before freezing parameters

### 19.2 Verification Checks
- SHA-256 manifest of all 42 Layer B videos must match pre-experiment baseline
- YOLOv8n checkpoint must match frozen SHA-256
- Audio checkpoint must match frozen SHA-256
- frozen_parameters.json must be written before first evaluation run
- All parameter values must be logged with timestamps proving freeze-before-evaluation

---

## 20. Final Execution Sequence

```
Phase 0: Pre-Execution Verification
  Step 0.1: Verify all 42 videos present and accessible
  Step 0.2: Generate SHA-256 manifest of Layer B videos
  Step 0.3: Verify YOLOv8n checkpoint loads correctly
  Step 0.4: Verify Audio CNN checkpoint loads correctly
  Step 0.5: Write frozen_parameters.json
  Step 0.6: Create event ground-truth labels (annotation)
  Step 0.7: Run pre-execution checklist

Phase 1: Data Preparation
  Step 1.1: Extract audio from all 42 videos -> data/processed/layer_b/audio/
  Step 1.2: Validate extracted audio files
  Step 1.3: Create experiment_manifest.json
  Step 1.4: Verify no overlap with standalone audio training data

Phase 2: B0 -- Vision Only
  Step 2.1: Run YOLOv8n on camera_front.mov for all 21 events at 5 FPS
  Step 2.2: Collect per-frame detections
  Step 2.3: Compute event-level metrics
  Step 2.4: Generate B0 artifacts
  Step 2.5: Run stateless simulation for B0

Phase 3: B1 -- Audio Only
  Step 3.1: Run audio CNN on all extracted Layer B audio
  Step 3.2: Collect per-window predictions
  Step 3.3: Compute audio metrics
  Step 3.4: Generate B1 artifacts
  Step 3.5: Run audio-only simulation for B1

Phase 4: B2 -- Vision + Audio (Stateless)
  Step 4.1: Combine vision + audio evidence (no temporal, no state machine)
  Step 4.2: Run stateless simulation for B2
  Step 4.3: Compute event-level metrics
  Step 4.4: Generate B2 artifacts

Phase 5: B3 -- Temporal Evidence
  Step 5.1: Run YOLOv8n on both cameras at 5 FPS
  Step 5.2: Process through temporal confirmation logic
  Step 5.3: Run stateless dual-camera temporal simulation
  Step 5.4: Compute event-level metrics
  Step 5.5: Generate B3 artifacts

Phase 6: B4 -- Full Policy
  Step 6.1: Assemble full pipeline for each event
  Step 6.2: Run EventSimulationRunner with full decision engine
  Step 6.3: Record complete state/gate timelines
  Step 6.4: Compute primary and secondary safety endpoints
  Step 6.5: Run failure analysis
  Step 6.6: Generate B4 artifacts

Phase 7: B5 -- Camera 1 Failure
  Step 7.1: Run B5a (full camera_1 dropout)
  Step 7.2: Run B5b (midway camera_1 dropout)
  Step 7.3: Run B5c (intermittent camera_1)
  Step 7.4: Verify safety invariants
  Step 7.5: Generate B5 artifacts

Phase 8: B6 -- Camera 2 / Dual Failure
  Step 8.1: Run B6a (full camera_2 dropout)
  Step 8.2: Run B6b (dual camera dropout)
  Step 8.3: Run B6c (sequential camera failure)
  Step 8.4: Verify FAULT_FAIL_SAFE invariant
  Step 8.5: Generate B6 artifacts

Phase 9: B7 -- Robustness
  Step 9.1: Run B7a-B7f sub-experiments
  Step 9.2: Verify safety invariants
  Step 9.3: Generate B7 artifacts

Phase 10: Analysis and Reporting
  Step 10.1: Compute paired comparisons (B0 vs B4, B3 vs B4, etc.)
  Step 10.2: Compute bootstrap confidence intervals
  Step 10.3: Generate all 20 figures
  Step 10.4: Generate all 12 tables (markdown, CSV, LaTeX)
  Step 10.5: Compile failure analysis
  Step 10.6: Write experiment_report.md
  Step 10.7: Final integrity verification
```

---

## 21. Expected Outputs

### 21.1 Machine-Readable Artifacts
- 1 master experiment manifest (JSON)
- 1 frozen parameters file (JSON)
- 1 Layer B video manifest with SHA-256 hashes (JSON)
- 8+ condition summary files (JSON)
- 21 x 8 = 168+ per-event evaluation records (JSON)
- Per-frame detection logs (JSONL)
- Per-window audio predictions (JSONL)
- Simulation traces per event per condition (JSONL)
- Failure analysis records (JSON)
- Statistical analysis results (JSON)

### 21.2 Publication Artifacts
- 20 figures (300 DPI PNG)
- 12 tables (Markdown + CSV + LaTeX)
- 1 comprehensive experiment report (Markdown)

---

## 22. Limitations

1. **Small Sample Size:** N=21 events provides limited statistical power. Confidence intervals will be wide. No crossing-level stratification is possible without crossing metadata.

2. **No Independent Crossings:** All events are from an unknown number of crossings (metadata unavailable). Crossing-independent generalization cannot be claimed.

3. **Dataset V1 Leakage Risk:** The YOLOv8n was trained with a development_fallback split lacking crossing/session grouping. Frame-level development metrics may overestimate generalization.

4. **No Negative Events:** The 21 events all contain train passages. False alarm rate during no-train periods cannot be evaluated from Layer B alone.

5. **Audio Domain Shift:** The standalone audio training data and Layer B embedded audio come from different recording devices, environments, and acoustic conditions. Performance degradation is expected.

6. **Threshold Mismatch Risk:** All thresholds were frozen from development data. They may be suboptimal for the real-world distribution.

7. **Temporal Synchronization:** Camera synchronization method is unknown. Timing metrics may have systematic bias from sync uncertainty.

8. **No Physical Safety Claim:** All results are from software simulation on recorded data. No claim of physical safety, real-time performance, or deployment readiness is permitted.

9. **Single Model Seed:** YOLOv8n was trained with seed=42 only. Training variability is not quantified.

10. **Ground-Truth Dependency:** Event-level evaluation requires human-annotated labels that do not yet exist. Results quality depends on annotation quality.

---

## 23. Exact Commands for Gemini Implementation

These are specification-level pseudocommands. Gemini 3.8 Flash should implement the corresponding Python scripts and CLI commands.

```bash
# Phase 0: Pre-execution
python -m railway_detection experiment verify-prerequisites
python -m railway_detection experiment create-manifests

# Phase 1: Data preparation
python -m railway_detection layer-b extract-audio \
  --input data/raw/layer_b/videos/ \
  --output data/processed/layer_b/audio/ \
  --sample-rate 16000 --mono

# Phase 2-9: Execute benchmarks
python -m railway_detection experiment run-benchmark \
  --condition B0 \
  --events data/raw/layer_b/videos/ \
  --labels data/raw/layer_b/labels/ \
  --vision-checkpoint experiments/vision/39f402dfe460/checkpoints/weights/best.pt \
  --audio-checkpoint models/audio/best_checkpoint.pt \
  --output results/experiments/B0/ \
  --fps 5 \
  --seed 42

# Repeat for B1-B7 with appropriate --condition flag

# Phase 10: Analysis and reporting
python -m railway_detection experiment analyze \
  --results-dir results/experiments/ \
  --output results/experiments/report/

python -m railway_detection experiment generate-figures \
  --results-dir results/experiments/ \
  --output results/experiments/figures/

python -m railway_detection experiment generate-tables \
  --results-dir results/experiments/ \
  --output results/experiments/tables/ \
  --format markdown,csv,latex
```

---

## 24. Pre-Execution Checklist

- [ ] All 21 event directories exist under `data/raw/layer_b/videos/`
- [ ] Each event has camera_front.mov and camera_back.mov (or equivalents)
- [ ] YOLOv8n checkpoint exists and loads: `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`
- [ ] Audio CNN checkpoint exists and loads: `models/audio/best_checkpoint.pt`
- [ ] frozen_parameters.json has been written and timestamped
- [ ] SHA-256 manifest of all 42 Layer B videos has been computed
- [ ] SHA-256 of both model checkpoints has been recorded
- [ ] ffmpeg is available for audio extraction
- [ ] opencv-python is installed for video frame extraction
- [ ] torch is available for model inference
- [ ] ultralytics is available for YOLOv8n inference
- [ ] Ground-truth event labels exist for all 21 events (or annotation plan is ready)
- [ ] No Layer B data has been used in any model training or threshold selection
- [ ] Python environment recorded (pip freeze)
- [ ] Git commit recorded
- [ ] All 224 existing tests still pass
- [ ] data/processed/layer_b/audio/ directory is empty (audio not yet extracted)

---

## 25. Identified Mismatches Between Protocol and Implementation

> [!WARNING]
> The following mismatches between documented protocol and actual implementation must be resolved before experiment execution.

### Mismatch 1: B0-B7 Numbering Inconsistency

**Protocol (RESEARCH_PROTOCOL_V2.md S19):** B0=single-cam-raw, B1=single-cam-temporal, B2=dual-cam-temporal, B3=dual-cam+state, B4=audio-only, B5=dual+audio-no-state, B6=full-policy, B7=faults.

**User Prompt:** B0=vision-only, B1=audio-only, B2=vision+audio, B3=temporal, B4=temporal+multimodal, B5=cam1-fail, B6=cam2/dual-fail, B7=robustness.

**Current ExperimentRunner:** Uses the Protocol V2 numbering but implements all conditions.

**Resolution:** This plan adopts the user's numbering. The ExperimentRunner must be refactored to match.

### Mismatch 2: has_qualified_approach() Includes side and train as Approach Labels

**Issue:** rules.py line 56 defines approach_labels = ("front", "side", "train"). This means side detections trigger approach transitions. For the departure camera, side detections would incorrectly signal approach.

**Resolution:** Approach and departure evidence should be camera-role-aware. Camera_1 approach evidence should use ("front", "side"). Camera_2 departure evidence should use ("rear", "side"). The current implementation does not distinguish camera roles in the rule functions.

### Mismatch 3: has_qualified_departure() Also Includes side and train

**Issue:** rules.py line 71 defines departure_labels = ("rear", "side", "train"). The side label appears in both approach AND departure, which is intentional but means side alone can satisfy both conditions. This is acceptable for the current architecture but must be documented.

### Mismatch 4: No Real Video Inference Pipeline Exists

**Issue:** The ExperimentRunner.run_condition() accepts pre-constructed list[MultimodalFrame] objects. There is no end-to-end pipeline that:
1. Reads a .mov video file
2. Samples frames at target FPS
3. Runs YOLOv8n inference on each frame
4. Extracts audio from the video
5. Runs audio CNN inference on audio windows
6. Constructs MultimodalFrame objects
7. Feeds them to the runner

**Resolution:** Gemini must implement a LayerBEventProcessor class that performs this complete pipeline.

### Mismatch 5: B7 Failure Injection is Hardcoded

**Issue:** ExperimentRunner._prepare_frames_for_condition() line 188-203 hardcodes a single CAMERA_1_DROPOUT failure for B7. The protocol requires multiple distinct failure scenarios.

**Resolution:** B7 must be refactored to accept a FailureSchedule parameter, with sub-experiments B7a-B7f.

### Mismatch 6: Ground-Truth Labels Do Not Exist

**Issue:** No metadata.json or labels/event_labels.json files exist in any event directory. The EventMetricsCalculator.evaluate_run() requires entry_time_s and clearance_time_s for primary endpoints.

**Resolution:** An annotation phase is required. If manual annotation is not feasible before experiments, event-level metrics must be computed with not_evaluable for timing-dependent endpoints, and B0 frame-level metrics become the primary diagnostic.

### Mismatch 7: Decision Engine Does Not Use TemporalEvidenceBuffer

**Issue:** The MultimodalDecisionEngine has its own internal consecutive_approach_count counter (line 148) but does not consume the output of TemporalEvidenceBuffer. The temporal buffer and decision engine are independent systems that are not integrated.

**Resolution:** For the B3/B4 conditions, frames should be processed through TemporalEvidenceBuffer before being passed to the decision engine, OR the decision engine's internal temporal logic should be documented as the operational temporal filter.

### Mismatch 8: confirm_frames in Decision Engine vs Temporal Buffer

**Issue:** MultimodalDecisionEngine defaults to confirm_frames=2, while TemporalConfig defaults to confirm_frames=3. These are independent parameters that could produce inconsistent behavior.

**Resolution:** Document that the decision engine's internal confirmation logic is the authoritative temporal filter for B3/B4 experiments. The standalone TemporalEvidenceBuffer may be used for B3 as a preprocessing step.

---

## 26. IMPLEMENTATION HANDOFF FOR GEMINI 3.8 FLASH

> [!IMPORTANT]
> Follow this checklist in exact order. Do NOT make methodological decisions. All methodological decisions are frozen in this document. If ambiguity is encountered, default to the more conservative option.

### Phase 0: Pre-Execution Setup

- [ ] **0.1** Verify virtual environment: `PYTHONPATH=src /tmp/test_venv/bin/pytest tests/` must pass 224 tests.
- [ ] **0.2** Create `scripts/run_real_world_experiments.py` -- the master orchestration script.
- [ ] **0.3** Create `results/experiments/manifests/frozen_parameters.json` containing all values from S5.2 of this document.
- [ ] **0.4** Create `results/experiments/manifests/layer_b_event_manifest.json` with SHA-256 hashes of all 42 video files.
- [ ] **0.5** Create `results/experiments/manifests/experiment_manifest.json` with git commit, timestamp, python version, package versions.

### Phase 1: Event Annotation Scaffolding

- [ ] **1.1** Create `scripts/create_event_label_templates.py` that generates empty metadata.json and labels/event_labels.json templates for all 21 events per EVENT_LABEL_PROTOCOL.md.
- [ ] **1.2** Run the template generator. The user will fill in ground-truth timestamps manually.
- [ ] **1.3** Create `src/railway_detection/data/event_annotator.py` with a function load_event_labels(event_dir) -> dict that reads and validates labels.

### Phase 2: Layer B Processing Pipeline

- [ ] **2.1** Create `src/railway_detection/experiments/layer_b_processor.py` containing class LayerBEventProcessor with methods:
  - extract_audio(event_dir, output_dir) -- extract mono 16kHz WAV from each video using audio_extractor.py
  - run_vision_inference(video_path, checkpoint_path, fps=5, conf=0.35) -> list[EvidenceRecord]
  - run_audio_inference(wav_path, checkpoint_path, threshold=0.5184) -> list[EvidenceRecord]
  - build_multimodal_frames(vision_records, audio_records, stride_s=0.2) -> list[MultimodalFrame]
  - process_event(event_dir, condition) -> list[MultimodalFrame] -- complete pipeline for one event

- [ ] **2.2** The vision inference must:
  - Use frame_generator() from vision/video.py with target_fps=5
  - Load YOLOv8n via ultralytics YOLO class
  - Convert YOLO detections to Detection objects with labels mapped to {0: "front", 1: "rear", 2: "side"}
  - Wrap in EvidenceRecord with source_id="camera_1" or "camera_2", modality=Modality.VISION

- [ ] **2.3** The audio inference must:
  - Use AudioEvidencePipeline with PyTorchTrainHornClassifier loaded from checkpoint
  - Set source_id="audio_1"
  - Verify audio_safety_role: "supporting_only" in all records

### Phase 3: Refactor ExperimentRunner

- [ ] **3.1** Rename existing BenchmarkCondition enum values to match this document's B0-B7 definitions.
- [ ] **3.2** Update _prepare_frames_for_condition() to support the new B0-B7 definitions.
- [ ] **3.3** For B0: use camera_front only, no audio, no temporal, stateless (1-frame threshold).
- [ ] **3.4** For B1: audio records only, no vision, invariant: audio NEVER opens gate.
- [ ] **3.5** For B2: both cameras + audio, stateless (3-frame persistence), no state machine.
- [ ] **3.6** For B3: both cameras, no audio, temporal filtering via decision engine's confirm_frames, stateless.
- [ ] **3.7** For B4: full pipeline -- both cameras + audio + temporal + decision engine + state machine + gate model.
- [ ] **3.8** For B5: inject FailureSchedule for camera_1 dropout. Implement sub-experiments B5a/B5b/B5c with different timing.
- [ ] **3.9** For B6: implement B6a (camera_2 dropout), B6b (dual dropout), B6c (sequential dropout).
- [ ] **3.10** For B7: implement B7a-B7f sub-experiments with FailureMode as specified in S7.7.2.

### Phase 4: Execute Experiments

- [ ] **4.1** Extract audio from all 42 videos.
- [ ] **4.2** Run B0 on all 21 events. Save per-frame detections and event summaries.
- [ ] **4.3** Run B1 on all 21 events. Save per-window audio predictions.
- [ ] **4.4** Run B2 on all 21 events. Save simulation traces.
- [ ] **4.5** Run B3 on all 21 events. Save temporal-filtered detections and simulation traces.
- [ ] **4.6** Run B4 on all 21 events. Save full simulation traces with state/gate timelines.
- [ ] **4.7** Run B5a/B5b/B5c on all 21 events. Verify safety invariants.
- [ ] **4.8** Run B6a/B6b/B6c on all 21 events. Verify FAULT_FAIL_SAFE invariant.
- [ ] **4.9** Run B7a-B7f on all 21 events. Verify all safety invariants.

### Phase 5: Analysis

- [ ] **5.1** Compute primary safety endpoints (MTR, POR) with Wilson 95% CI for each condition.
- [ ] **5.2** Compute secondary endpoints (warning lead time, clearance latency, etc.) for each condition.
- [ ] **5.3** Compute paired event-level differences: B0 vs B4, B3 vs B4, B0 vs B3.
- [ ] **5.4** Compute bootstrap 95% CI for continuous metrics (10,000 resamples).
- [ ] **5.5** Run failure analysis: classify every failure into taxonomy F01-F18.
- [ ] **5.6** Verify all 6 safety invariants (INV-1 through INV-6).

### Phase 6: Visualization

- [ ] **6.1** Generate all 20 figures per S13 specifications. Save at 300 DPI.
- [ ] **6.2** Ensure all figures have proper axis labels, units, legends, and titles.
- [ ] **6.3** Save to results/experiments/figures/.

### Phase 7: Tables

- [ ] **7.1** Generate all 12 tables per S14 specifications in markdown, CSV, and LaTeX.
- [ ] **7.2** Save to results/experiments/tables/.

### Phase 8: Report

- [ ] **8.1** Create results/experiments/report/experiment_report.md compiling all results, figures, tables, and analysis.
- [ ] **8.2** Include all limitations from S22.
- [ ] **8.3** Include claim boundary statement from RESEARCH_PROTOCOL_V2.md S27.

### Phase 9: Verification

- [ ] **9.1** Verify all existing 224 tests still pass.
- [ ] **9.2** Write new tests for LayerBEventProcessor in tests/unit/test_layer_b_processor.py.
- [ ] **9.3** Write new tests for refactored ExperimentRunner in tests/unit/test_experiment_runner_v2.py.
- [ ] **9.4** Verify SHA-256 manifests are unchanged (no data mutation).
- [ ] **9.5** Verify frozen_parameters.json timestamp precedes first experiment run timestamp.

### Critical Implementation Rules for Gemini

1. Do NOT change any model weights or checkpoints.
2. Do NOT change any threshold values.
3. Do NOT add Layer B data to any training dataset.
4. Do NOT tune parameters using Layer B results.
5. If ground-truth labels are missing, set timing metrics to not_evaluable, not to 0.
6. If ffmpeg fails on a video, log the error and mark that event's audio as not_available.
7. If YOLOv8n inference fails on a frame, log and skip the frame.
8. All new code must have corresponding unit tests.
9. Run PYTHONPATH=src /tmp/test_venv/bin/pytest tests/ after every major change.
10. Use /tmp/test_venv/bin/python for all execution (avoid iCloud-evicted .venv).
