# Scientific Claims & Experiment Design Review: Offline Descriptive Benchmark

**Document Version:** 1.0.0  
**Review Type:** Methodological, Statistical, and Epistemological Review  
**Target Benchmark:** Front-Camera B0 / B1 / B2 Offline Descriptive Benchmark  
**Dataset Under Review:** 27 Active Events (`crossing_A`, Bangladesh)  
**Governing Documents:**  
- [`docs/RESEARCHER_DECISION_BRIEF.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/RESEARCHER_DECISION_BRIEF.md)  
- [`docs/B0_B1_B2_METRIC_SPECIFICATION.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/B0_B1_B2_METRIC_SPECIFICATION.md)  
- [`docs/EXPERIMENT_DESIGN_FINAL.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/EXPERIMENT_DESIGN_FINAL.md)  

---

## 1. Executive Methodological Assessment

This review evaluates the scientific defensibility of running an offline, front-camera descriptive benchmark (Conditions B0, B1, B2) across the 27 real-world events recorded at `crossing_A`. 

### Methodological Verdict:
* **Scientifically Defensible as a Fixed-Site Descriptive Characterization:** The benchmark is scientifically valid if presented strictly as an empirical, fixed-site characterization of multimodal sensory actuations, temporal state-machine filtering, and simulated fail-closed kinematics on a recorded real-world dataset.
* **Scientifically Invalid as an Out-of-Sample Generalization Benchmark:** Any claim that this experiment demonstrates cross-crossing generalization, held-out statistical validation, or physical field readiness is scientifically unsupportable and would be rejected during rigorous peer review.

---

## 2. Dataset Limitations & Environmental Leakage

### 2.1 Single Physical Site ($N=1$ Crossing)
All 27 events were recorded at a single physical railway crossing (`crossing_A`) in Bangladesh:
- **Spatial Invariance:** Camera mounting height, lens focal length, optical viewpoint angle, track geometry, turnout frog placement, pedestrian approach lines, and background infrastructure (concrete viaduct pillars, red pedestrian overpass) are identical across all 27 events.
- **Acoustic Invariance:** Roadbed acoustic absorption, viaduct reverberation characteristics, and microphone directivity patterns are constant.
- **Scientific Consequence:** Zero geographic, geometric, or infrastructural diversity exists in the dataset. The data cannot establish that the system would operate reliably at any other level crossing.

### 2.2 Two Capture Sessions & Partition Leakage
The dataset was gathered during only two distinct field sessions:
- **Session 1 (2026-09-14, 14:13–17:26 local):** 20 events (Daylight, overcast, high ambient humidity).
- **Session 2 (2026-10-04, 19:22–19:59 local):** 7 events (Dusk/night, artificial trackside illumination).

Attempting to construct an out-of-sample "train/val/test" split from 27 events across 2 sessions creates severe environmental leakage:
- If events from Session 1 are partitioned into both training and testing, the test set leaks the identical afternoon sun angle, cloud cover, and background scenery.
- If Session 2 (7 events) is held out as a test set, sensor hardware differences (iPad rear camera vs. iPhone front camera) and severe diurnal shift (night vs. day) are confounded with small-sample imbalance (only 3 train events in Session 2).
- **Recommendation:** Do not fabricate a train/val/test split. Frame the analysis as a full-cohort descriptive system characterization.

### 2.3 Hyperparameter & Threshold Tuning Leakage
The YOLO confidence threshold ($T_{\text{conf}} = 0.35$), acoustic operating threshold ($T^* = 0.3700$), clearance dwell timer ($3.0\,\text{s}$), and persistence window ($0.25\,\text{s}$) were tuned, debugged, and verified on these exact 27 recordings during earlier project phases. Claiming "zero-shot" or "held-out" generalization on events that informed heuristic development constitutes tuning leakage.

---

## 3. Left-Censoring & Temporal Truncation

In all 23 train events, locomotives are already in the visual approach corridor at recording start ($T_0 \le 0.0\,\text{s}$ for 20 events; $T_0 = 1.5\,\text{s}$ for 3 events):
- **Unobservable Approach Onset:** Physical train arrival (when the train first enters the audible or visible zone 500m down the track) is completely unrecorded.
- **Invalid Latency Metric:** "Detection latency from approach onset" cannot be calculated.
- **Valid Operational Metric:** The only mathematically valid temporal metric is **Warning Lead Time Relative to Entry Boundary $T_1$** ($\max(0.0, T_1 - t_{\text{warn}})$).
- **Mandatory Caveat:** Warning lead time is fundamentally bounded by recording duration ($T_1 \approx 2.1\,\text{s} - 5.8\,\text{s}$). It reflects advance notice achieved within the available video window, not the maximum theoretical advance notice of a trackside installation.

---

## 4. Statistical Independence & Unit of Analysis

### 4.1 Frame-Level vs. Event-Level Independence
- **The Pseudo-Replication Fallacy:** Aggregating video frames into a pool of $N \approx 5,000$ "frame observations" and calculating standard errors or $p$-values treats adjacent frames as independent observations. Frames sampled at 5 FPS ($\Delta t = 0.2\,\text{s}$) exhibit extreme temporal autocorrelation ($\rho > 0.95$).
- **Unit of Analysis:** The legitimate statistical unit of analysis is the **Event Passage** ($N=23$ train events, $N=3$ control events). All safety-critical proportions must be computed over events, not frames.

### 4.2 Statistical Significance & Hypothesis Testing
- **Small-Sample Wilson Score Intervals:** Proportions such as Missed-Train Rate ($0/22$) must be accompanied by 95% Wilson score intervals ($[0.0\%, 14.9\%]$). The width of the interval frankly communicates the statistical uncertainty of a 22-event sample.
- **Paired Condition Comparisons:**
  - *Valid Paired Test:* Comparing premature gate openings or chatter episodes between B0 (stateless) and B2 (state machine) using a two-sided sign test on paired event outcomes ($N=22$).
  - *Invalid Comparison:* Comparing total gate-closed duration between B1 (audio) and B0/B2. Condition B1 is architecturally forbidden from ever opening the gate (`RULE_2_AUDIO_SUPPORT_ONLY`); once closed, B1 stays closed until simulation end. A statistical $t$-test or Wilcoxon test on closed duration between B1 and B0/B2 is scientifically meaningless because the clearance mechanism was deliberately suppressed in B1 by safety invariant design.

---

## 5. Negative Control Cohort Limitations

The negative control cohort consists of only **3 events** (`no_train_events/event_001`–`event_003`), providing ~60 seconds of cumulative exposure:
- **Qualitative Value:** High. It empirically proves that visual false positives exist (e.g., `event_002` exhibits visual detections on flying insects and trackside foliage motion).
- **Quantitative Limitation:** Severely underpowered. Extrapolating a false-alarm rate per operational year or per hour from 60 seconds of quiet footage is statistically invalid. Protocol v9 (§11.2) correctly requires setting `false_alarm_hourly_rate: "not_reported_by_protocol"`.

---

## 6. Simulated Gate Kinematics vs. Physical Actuation

The benchmark evaluates software commands passed to `PhysicalGateModel` (`src/railway_detection/simulation/gate_model.py`):
- **Model Assumptions:** Assumes an idealized constant angular velocity boom ($90^\circ / 3.0\,\text{s} = 30^\circ/\text{s}$) with instantaneous electrical command transfer.
- **Real-World Actuator Realities:** Physical level-crossing barriers experience motor spin-up inertia, hydraulic valve lag, mechanical backlash, bounce upon descent, and wind resistance.
- **Claim Boundary:** The benchmark measures *commanded kinematic gate state*, not physical obstacle clearance.

---

## 7. Prohibited Claims vs. Defensible Claims

### 7.1 Claims the Research Paper MUST AVOID
1. **NO Cross-Crossing Generalization:** Do NOT claim the system is "generalized", "robust across railway networks", or "ready for deployment at level crossings".
2. **NO Out-of-Sample Performance:** Do NOT claim an "independent held-out test evaluation" on this dataset.
3. **NO Physical Safety Certification:** Do NOT use terms like "certified fail-safe", "SIL 4 compliant", or "guarantees crossing protection".
4. **NO Absolute Detection Latency:** Do NOT report detection latency from physical corridor arrival.
5. **NO False-Alarm Rates Per Hour:** Do NOT report extrapolated hourly or yearly nuisance alarm rates.
6. **NO Clearance Hazard Zero-Failure Claims on Front Camera:** Do NOT claim "0% premature openings" under conditions where clearance was omitted due to back-camera clock absence.

### 7.2 Defensible Scientific Claims
1. **Empirical Sensor Characterization:** Characterizes raw detector recall and detection continuity of frozen YOLOv8n and CompactTrainHornCNN models on recorded real-world crossing events.
2. **State-Space Hysteresis Proof:** Proves that deterministic state-machine logic with dwell timers eliminates the severe gate barrier flapping (closure episodes) observed under stateless thresholding (B0 vs. B2).
3. **Multimodal Redundancy:** Demonstrates that acoustic horn detection provides early approach warning during daylight and dusk, but confirms that visual verification is required for safe gate opening.
4. **Transparent Failure Accounting:** Discloses failure modes including unobservable entry boundaries (`event_005`), visual dropouts during mid-consist passage, and silent approaches without horn whistle.
