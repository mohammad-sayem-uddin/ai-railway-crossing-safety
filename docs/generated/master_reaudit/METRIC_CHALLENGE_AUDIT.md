# MISSION 16A-METRIC-CHALLENGE: INDEPENDENT METRICS AND EXPERIMENT DESIGN AUDIT

**Project:** Train Gate Automation — Bangladesh  
**Mission:** Master Mission 16A Follow-up Challenge Audit  
**Auditor:** Independent Principal Research Methodologist, Statistical Auditor, Safety-Metric Reviewer, and Experimental Design Researcher  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Git Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Audit Standard:** Strict Read-Only, Evidence-Based, Adversarial  
**Execution Authority:** NONE  
**Research Authorization:** NONE  

---

## 1. Executive Verdict

This audit provides an independent mathematical, algorithmic, implementation, and scientific validity challenge of the safety metrics, temporal evaluation boundaries, statistical reporting, and experimental conditions across the Train Gate Automation project.

### Core Audit Determinations:
1. **Mathematical Coherence of $M4$:** The primary safety metric $M4$ (Premature Opening) is rigorously formulated on the strict open interval $(t_{\text{blocked}}, T_4)$ and correctly implemented in [`src/railway_detection/evaluation/metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) via a 6-case classification. It enforces an exact $1\,\mu\text{s}$ snapping grid (`DEC-C05`), retains witnessed violations regardless of replay completion, and separates incomplete replays into distinct `NOT_EVALUABLE` failure reasons.
2. **Deconstruction of the "M5 Companion Vehicle" Contradiction:** Early review documents and prompt narratives mischaracterized M5 as *"Companion Vehicle Intrusion"* (counting road vehicle intrusions into the crossing). In the primary mathematical and code implementation ([`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py), `RD-016`, `RD-017`), M5 is **`NEVER_PROTECTED_M5`** (*"Never Protected Before $T_4$"*). It is a **companion failure indicator to $M4$** indicating that the barrier failed to achieve a blocked state at any point during $[0, T_4)$. It has zero connection to road vehicles. Under **RD-017**, M5 is reported strictly as an integer count, never as a rate, and is excluded from the $M4$ denominator.
3. **Condition B1 Evaluability Contradiction:** Earlier project drafts proposed comparing $M4$, clearance latency, and gate closure duration across Conditions B0, B1, and B2. However, inspection of [`src/railway_detection/fusion/decision_engine.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/decision_engine.py) reveals that under `RULE_2_AUDIO_SUPPORT_ONLY`, acoustic horn detections in `IDLE` have **zero gate actuation authority** (`"Audio train noise observed in IDLE; supporting only, no gate actuation"`). In Condition B1 (vision masked), the barrier remains vertical at $90^\circ$ for 100% of simulation steps across all events. Evaluating B1 for premature opening, closure latency, or gate timing is architecturally and mathematically impossible.
4. **Physical Reality of the Lead-In Feasibility Screen ($\text{MTR}$):** With frozen barrier kinematics requiring $\approx 3.6\,\text{s}$ minimum block latency, and 20 of 23 train events being left-censored ($T_0 \le 0.0\,\text{s}$) with 18 events having $T_1 \le 3.2\,\text{s}$, the recording window is physically shorter than the time required for the gate to descend. Without the lead-in screen ([`src/railway_detection/evaluation/lead_in_screen.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/lead_in_screen.py)), missed-train rates approach 100% due to video truncation, not detector failure.
5. **Decoupling of $M4/M5$ from Deferred $T_2$ Landmark:** While the $T_2$ roadway-entry landmark definition remains officially **DEFERRED** under **RD-006**, $M4$ and $M5$ depend exclusively on $t_{\text{blocked}}$ and $T_4$. Consequently, the deferral of $T_2$ blocks roadway occupancy duration, but does **not** block $M4$ or $M5$ computation (once $T_4$ is certified).
6. **Descriptive Statistical Compliance:** Implementation in [`src/railway_detection/evaluation/descriptive_only.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/descriptive_only.py) strictly enforces **RD-023**, blocking inferential $p$-values, McNemar tests, Wilcoxon tests, and cross-site generalization claims.
7. **Empirical Execution Status:** Zero official metrics have been generated. All historical numbers in earlier reports were pre-Phase-5 exploratory checks on uncertified ground truth.

---

## 2. Audit Scope and Safety Declaration

In accordance with Section 2 of the Mission Charter, this audit was conducted under strict containment:
- **Zero Media Access:** No raw video (`.mov`), raw audio (`.wav`), or extracted frames were opened or decoded.
- **Zero Model Checkpoints:** Production PyTorch checkpoints (`best.pt`) were not loaded or hashed.
- **Zero Real-Data Evaluation:** No evaluation runners, simulations, or replays were executed against real event data.
- **Permitted Evidence:** Pure source code inspection, unit test definitions, frozen configuration schemas, and historical audit documentation.

---

## 3. Complete Repository Metric Inventory

| Metric Identifier | Mathematical Formulation | Source File & Symbol | Input Parameters | Required Boundaries | Evaluability Denominator | Output Units | Status / Role |
| :--- | :--- | :--- | :--- | :---: | :--- | :---: | :--- |
| **$M4$ (Premature Opening)** | Unblocked step inside $(t_{\text{blocked}}, T_4)$ | [`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) `classify_m4()` | `SimulationRunResult`, $T_4$ | $T_4$ | Replays that block before $T_4$ and reach $T_4$ (or witness violation) | Boolean / Rate with Wilson CI | **Primary Safety Metric (RD-022)** |
| **$M5$ (Never Protected)** | No blocked step observed on $[0, T_4)$ | [`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) `classify_m4()` | `SimulationRunResult`, $T_4$ | $T_4$ | Replays starting at $t=0$ and reaching $T_4$ | Integer Count | **Companion Failure Metric (RD-017)** |
| **$\text{MTR}$ (Missed Train Rate)** | Barrier not blocked at danger line $T_1$ | [`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) / [`lead_in_screen.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/lead_in_screen.py) | Simulation steps, $T_1, T_0$ | $T_1, T_0$ | Events passing lead-in feasibility screen ($\ge 3.6\,\text{s}$) | Boolean / Rate with Wilson CI | **Feasibility Screened (RD-021)** |
| **Warning Lead Time** | $T_1 - t_{\text{warning}}$ | [`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) `EventMetricsCalculator` | Simulation steps, $T_1$ | $T_1$ | Events with observable $T_1$ and active warning | Seconds ($\text{s}$) | Operational Diagnostic |
| **Clearance Latency** | $t_{\text{opened}} - T_4$ | [`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) `EventMetricsCalculator` | Simulation steps, $T_4$ | $T_4$ | Replays that open after $T_4$ | Seconds ($\text{s}$) | Operational Efficiency |
| **Excess Closed Time** | $t_{\text{open}} - t_{\text{blocked}} - \text{duration}_{\text{train}}$ | [`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) | Simulation steps, $T_1, T_4$ | $T_1, T_4$ | Replays with valid closure and reopening | Seconds ($\text{s}$) | Roadway Traffic Impact |
| **Roadway Occupancy** | $T_4 - T_2$ | [`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) | Ground-truth timestamps | $T_2, T_4$ | **0 events** ($T_2$ landmark deferred) | Seconds ($\text{s}$) | **DEFERRED (RD-006, RD-018)** |
| **Detection Latency** | $T_{\text{detect}} - T_0$ | [`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) | Detector trace, $T_0$ | $T_0$ | **3 events** (`009, 015, 016`; 20 left-censored) | Seconds ($\text{s}$) | Exploratory Diagnostic Only |
| **Nuisance Activation** | Gate closed during non-train passage | [`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) | Simulation steps | None (negative controls) | 3 negative control events (120.8 stream-sec) | Episode Count / Duration ($\text{s}$) | False Alarm Screening |

---

## 4. Mathematical and Implementation Audit of $M4$ (Premature Opening)

### 4.1 Strict Mathematical Formulation
Let $\mathcal{S} = \{(t_i, s_i)\}_{i=1}^N$ be the sequence of discrete simulation steps with timestamps $t_i$ and controller state $s_i$. Let $T_4 \in \mathbb{R}_{\ge 0}$ be the certified final train clearance timestamp.

All timestamps are first projected onto the $1\,\mu\text{s}$ discrete lattice:
$$t_i^* = \frac{\lfloor 10^6 \cdot t_i + 0.5 \rfloor}{10^6}, \quad T_4^* = \frac{\lfloor 10^6 \cdot T_4 + 0.5 \rfloor}{10^6}$$

The initial barrier-blocked timestamp is defined as:
$$t_{\text{blocked}} = \min \{ t_i^* \mid s_i.\text{is\_passage\_blocked} = \text{True} \}$$

The evaluation interval is the **strict open interval**:
$$I_{M4} = (t_{\text{blocked}}, T_4^*)$$

A step $(t_i^*, s_i)$ constitutes a **witnessed premature opening** if:
$$t_i^* \in I_{M4} \quad \text{AND} \quad \Big( s_i.\text{is\_passage\_blocked} = \text{False} \;\lor\; s_i.\text{gate\_state} \in \{\text{OPENING}, \text{OPEN}\} \Big)$$

### 4.2 The Six-Case Classification Matrix (RD-016)
Implementation in `classify_m4()` executes the exact 6-case state logic:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Witnessed Violation: Step inside (t_blocked, T4) is unblocked            │
│    -> EVALUABLE, premature = True, never_protected = False                  │
│    (Definite even if replay ends before T4 or starts after origin)          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Unbroken Protection, Replay Incomplete: last_step < T4                   │
│    -> NOT_EVALUABLE, reason = "replay_ended_before_T4"                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. Empty Interval: Covered, but zero steps fall strictly in (t_blocked, T4) │
│    -> NOT_EVALUABLE, reason = "no_steps_in_protection_interval"             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. Unbroken Continuous Protection: Covered, interior steps >= 1, no defect  │
│    -> EVALUABLE, premature = False, never_protected = False                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. Barrier Never Blocked, Incomplete Replay: first_step > 0 or last < T4    │
│    -> NOT_EVALUABLE, reason = "replay_started_late" / "ended_before_T4"     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 6. Barrier Never Blocked, Full Replay: first_step <= 0 AND last >= T4       │
│    -> NEVER_PROTECTED_M5, premature = None, never_protected = True          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Rigorous Guard Verification
- **Witnessed Violation Preservation:** If a violation occurs, `classify_m4` returns `status = EVALUABLE` and `premature = True`, even if `covered = False`. A system that dropped its barrier early is guilty of premature opening regardless of whether the video terminated before train exit.
- **Microsecond Grid Alignment:** Verified via `normalize_timestamp()` calling `round(val, 6)`. Eliminates IEEE 754 floating-point jitter across comparisons.
- **Start / End Step Exclusions:** The step at exactly $t = t_{\text{blocked}}$ and the step at exactly $t = T_4$ are strictly excluded from the interior window $(t_{\text{blocked}}, T_4)$.

---

## 5. Mathematical and Implementation Audit of $M5$ (Never Protected)

### 5.1 Resolution of the "Companion Vehicle" Myth
Task C explicitly requested investigating *"What constitutes a companion vehicle"* and *"What constitutes an intrusion"*.
Forensic audit of [`src/railway_detection/evaluation/metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) lines 96–255 and [`docs/generated/phase2/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL_v9.1.1_PROPOSED.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/phase2/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL_v9.1.1_PROPOSED.md) line 157 reveals:
> [!IMPORTANT]
> **M5 is NOT Companion Vehicle Intrusion.**
> In the primary repository architecture:
> - M5 is an abbreviation for **`NEVER_PROTECTED_M5`**.
> - It designates that the automated barrier **never achieved a passage-blocked state** before the train cleared ($T_4$).
> - It is termed a *"companion metric"* because it serves as the **companion failure mode to $M4$**:
>   - $M4$ captures premature ascension *after* protection initiated.
>   - $M5$ captures total absence of protection *before* clearance.
> - The term has zero connection to road automobiles, companion vehicles, or roadway intrusion tracking.

### 5.2 Mathematical Formulation of $M5$
A replay is classified as $M5$ if and only if all three conditions are satisfied:
1. **Full History Observed:** $t_{\text{first\_step}} \le 0.0\,\text{s}$ (the replay began at or before the zero origin).
2. **Full Duration Reached:** $t_{\text{last\_step}} \ge T_4^*$ (the replay covered the entire train passage).
3. **Zero Blocked Steps:** $\forall (t_i, s_i) \in \mathcal{S}$ where $t_i < T_4^*$, $s_i.\text{is\_passage\_blocked} = \text{False}$.

### 5.3 Denominator and Reporting Rules (RD-017)
- **Count-Only Reporting:** M5 is strictly an integer count of un-protected events ($N_{M5} \in \mathbb{N}_{\ge 0}$).
- **Exclusion from $M4$ Denominator:** Events classified as $M5$ are excluded from the $M4$ denominator because a barrier that never closed cannot prematurely open.

---

## 6. Missed-Train / Lead-In Feasibility Screen ($\text{MTR}$)

### 6.1 Mathematical Formulation
The lead-in feasibility screen implemented in [`src/railway_detection/evaluation/lead_in_screen.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/lead_in_screen.py) addresses video capture truncation.

Let $T_1$ be the frog-line entry timestamp. The approach start is defined as:
$$\text{approach\_start} = \begin{cases} T_0 & \text{if } T_0 \text{ is observable and uncensored} \\ 0.0 & \text{if } T_0 \text{ is left-censored (train present at frame 0)} \\ \text{None} & \text{if } T_0 \text{ is uncertain / missing} \end{cases}$$

The available physical lead-in time is:
$$\Delta t_{\text{lead\_in}} = T_1 - \text{approach\_start}$$

An event passes the screen if and only if:
$$\Delta t_{\text{lead\_in}} \ge \tau_{\text{min\_block}}$$

### 6.2 Derivation of $\tau_{\text{min\_block}} \approx 3.6\,\text{s}$
Under the frozen policy (`configs/decision_policy_v1.yaml`):
- Tick interval: $\Delta t_{\text{tick}} = 0.20\,\text{s}$.
- Optical confirmation: $N_{\text{confirm}} = 2$ consecutive ticks ($0.4\,\text{s}$).
- Warning dwell: $\tau_{\text{warn}} = 2.0\,\text{s}$ (bells/flashers active; barrier stationary at $90^\circ$).
- Barrier descent: Arm moves from $90^\circ$ to $0^\circ$ at $\omega = 30^\circ/\text{s}$. Passage is blocked when angle $\theta \le 45^\circ$, requiring $\frac{90 - 45}{30} = 1.5\,\text{s}$.
- Total minimum kinematic latency:
$$\tau_{\text{min\_block}} = (2 \times 0.2) + 2.0 + 1.5 - \epsilon \approx 3.60\,\text{s}$$
As derived in `derive_min_block_latency_s()`, the barrier physically cannot block passage prior to $t = 3.6\,\text{s}$ from the earliest possible sensory detection.

### 6.3 Scientific Role of the Screen
In the 27-event cohort, **18 of the 22 train events with candidate $T_1$ have $T_1 \le 3.2\,\text{s}$**.
If an un-screened missed-train metric ($s(T_1).\text{is\_passage\_blocked} = \text{True}$) were computed, the failure rate would be near 90% simply because the recording commenced after the train had already passed the point of no return. The screen properly classifies these events as `SCREEN_INSUFFICIENT_LEAD_IN`, excluding them from the missed-train denominator.

---

## 7. Temporal-Boundary Dependency Matrix

| Metric Endpoint | Dependencies | Impact of Deferred $T_2$ Landmark | Impact of Left-Censored $T_0$ | Impact of Missing $T_4$ |
| :--- | :---: | :--- | :--- | :--- |
| **Premature Opening ($M4$)** | $(t_{\text{blocked}}, T_4)$ | **NO IMPACT.** $M4$ is independent of $T_2$. | **NO IMPACT.** Replay start can occur after $T_0$. | **FATAL.** Missing $T_4$ makes event `t4_missing` (`NOT_EVALUABLE`). |
| **Never Protected ($M5$)** | $[0, T_4)$ | **NO IMPACT.** $M5$ is independent of $T_2$. | Requires recording origin $t=0.0$. | **FATAL.** Missing $T_4$ makes event `NOT_EVALUABLE`. |
| **Lead-In Screen ($\text{MTR}$)** | $T_1, T_0$ | **NO IMPACT.** Uses $T_1$ and $T_0$. | Uses $0.0$ as surrogate for left-censored $T_0$. | **NO IMPACT.** Independent of $T_4$. |
| **Roadway Occupancy** | $T_2, T_4$ | **FATAL BLOCKED.** $T_2$ deferred (RD-006, RD-018). | **FATAL.** Cannot impute $T_2 = 0.0$. | **FATAL.** Requires departure tail clearance. |
| **Physical Detection Latency**| $T_0, T_{\text{detect}}$ | **NO IMPACT.** Independent of $T_2$. | **FATAL (20/23).** True arrival is unobservable. | **NO IMPACT.** Independent of $T_4$. |

---

## 8. Censoring and Per-Metric Evaluability Assessment

In accordance with **RD-011** and **RD-040**, the repository enforces per-metric denominators rather than global event exclusion:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 27 TOTAL RECORDED EVENTS                                                    │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ 23 Full Train Passages               │ - 20 Left-Censored (T0 <= 0.0s)      │
│                                      │ - 3 Observable Entry (009, 015, 016) │
│                                      │ - 1 Unobservable Bounds (event_005)  │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ 3 Negative Controls (No-Train)       │ - False Alarm / Nuisance Denominator │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ 1 Engine-Only Passage                │ - Isolated Case Study (RD-024)       │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

### Evaluability Rules:
1. **Engine Event Isolation (RD-024):** `engine_events/event_001` is strictly excluded from pooled train aggregates. Because $T_3 \equiv T_4$, it is analyzed as an isolated exploratory case study.
2. **Left-Censored Latency Exclusion (RD-011):** Left-censored events ($T_0 \le 0.0$) are strictly excluded from physical approach latency point estimates.
3. **No Zero-Imputation:** A missing or unobservable boundary is never imputed as $0.0$. Incomplete replays receive explicit typed refusal reasons (`replay_ended_before_T4`, `replay_started_late`).

---

## 9. Front-Stream, Back-Stream, and Fused Applicability Matrix

Under **RD-015** and **RD-022**, sensor streams possess asymmetric metric applicability:

| Metric Category | Front-Camera Stream | Back-Camera Stream | Fused Dual-Camera Stream | Methodological Justification |
| :--- | :---: | :---: | :---: | :--- |
| **Approach & Lead-In ($\text{MTR}, T_1$)** | **PRIMARY** | Inapplicable | Exploratory | Front camera has direct line of sight to approaching corridor. |
| **Tail Clearance ($M4, M5, T_4$)** | Inadequate / Occluded | **PRIMARY** | Exploratory | Consist tail clears crossing in direct view of rear departure camera. |
| **Acoustic Horn Response ($T_{\text{horn}}$)** | **PRIMARY** | Secondary | Exploratory | Front microphone captures approaching locomotive horn sequence. |
| **Roadway Occupancy Duration** | Incomplete | Incomplete | **PRIMARY (BLOCKED)** | Requires synchronized front entry and rear exit; clocks un-genlocked. |

---

## 10. B0–B2 Experiment Definition Matrix

Reconstruction of the three front-sensor benchmark conditions from source and configuration:

| Dimension | Condition B0 | Condition B1 | Condition B2 |
| :--- | :--- | :--- | :--- |
| **Condition Name** | Front Vision Only | Front Audio Only | Front Container-Native Fusion |
| **Perceptual Sensor** | Front Camera Video (`camera_front.mov`) | Front Camera Microphone (`audio.wav`) | Front Camera Video + Audio |
| **Perceptual Model** | YOLOv8n (front/rear/side, conf $\ge 0.35$) | CompactTrainHornCNN V3 ($\theta = 0.3700$) | YOLOv8n + CompactTrainHornCNN V3 |
| **Acoustic Authority** | Masked / Inactive | Active (Supporting Only, `RULE_2`) | Active (Supporting Only, `RULE_2`) |
| **Vision Authority** | Active (Approach & Clearance) | Masked / Inactive | Active (Approach & Clearance) |
| **Clock Alignment** | Hardware Native ($\tau = 0.0\,\text{s}$) | Hardware Native ($\tau = 0.0\,\text{s}$) | Container-Native ($\tau = 0.0\,\text{s}$) |
| **State Machine** | Frozen 10-State SM (`confirm=2`) | Frozen 10-State SM (`confirm=2`) | Frozen 10-State SM (`confirm=2`) |
| **Gate Actuation?** | **YES** (Actuates on visual approach) | **NO (NEVER ACTUATES OUT OF IDLE)** | **YES** (Actuates on visual approach) |
| **Measurable Endpoints**| $M4$, $\text{MTR}$, False Alarms, Chattering | Horn Window F1, Audio False Alarms | $M4$, $\text{MTR}$, Dwell Extension, Chattering |
| **Fatal Limitation** | Severe Chattering / Mid-Consist Dropout | **Cannot evaluate $M4$, closure, or latency** | Front camera cannot observe rear tail ($T_4$) |
| **Execution Status** | **UNEXECUTED (Awaiting EVAL-AUTH)** | **UNEXECUTED (Awaiting EVAL-AUTH)** | **UNEXECUTED (Awaiting EVAL-AUTH)** |

---

## 11. Historical B0–B7 to B0–B2 Mapping Assessment

### Historical Progression:
- **Phase 1 (Legacy B0–B7):** Changed camera count, temporal smoothing, state machines, and audio simultaneously. Highly conflated.
- **Phase 2 (E1–E7 Single-DOF Matrix):** [`FINAL_ABLATION_MATRIX.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FINAL_ABLATION_MATRIX.md) established single-variable ablations (E1 naive, E2 temporal, E3 dual naive, E4 dual temporal, E5 state machine, E6 audio stateless, E7 full system).
- **Phase 16 (Paper Scope B0–B2):** Streamlined into a container-native front-sensor benchmark to bypass cross-camera synchronization blockers:
  - B0 $\equiv$ Single-Camera Vision with State Machine (analogous to E2/E5 front).
  - B1 $\equiv$ Single-Camera Audio Baseline.
  - B2 $\equiv$ Container-Native Multimodal Fusion ($\tau_{\text{sync}} = 0.0\,\text{s}$).
  - Exploratory Back-Stream (B3/B4) restricted to the 11 R04 dual-camera events.

---

## 12. Descriptive-Statistics Compliance Audit (RD-023)

Audit of [`src/railway_detection/evaluation/descriptive_only.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/descriptive_only.py):
- **Inferential Statistical Tests Prohibited:** The codebase strictly excludes $p$-values, Student's $t$-tests, McNemar tests, Wilcoxon signed-rank tests, and ANOVA.
- **Allowed Descriptive Statistics:** Proportions, integer counts, medians, interquartile ranges, explicit denominators, and Wilson score confidence intervals for binomial endpoints.
- **Forbidden Claims Enforcement:** Function `_is_forbidden_claim()` programmatically rejects terms:
  `"cross-site"`, `"generalization"`, `"official test"`, `"official evaluation"`, `"held-out test"`.

---

## 13. Historical Results Provenance Matrix

| Historical Result Claim | Source Document | Claimed Value | Evidentiary Reality | Status |
| :--- | :--- | :--- | :--- | :--- |
| **B0 Premature Opening Rate** | `FORENSIC_EXPERIMENT_AUDIT.md` L190 | 20 / 22 (90.9%) | Diagnostic run on legacy ground truth | Unverified Diagnostic |
| **B0 Chattering Rate** | `FORENSIC_EXPERIMENT_AUDIT.md` L190 | 21 / 23 trains | Frequent detector dropout inside consist | Unverified Diagnostic |
| **B1 Gate Closed Duration** | `PHASE5_OUTPUT_AUDIT.md` L18 | 0.0s (Gate at $90^\circ$) | Exact behavior of `RULE_2` in IDLE | Verified Architectural Invariant |
| **Full Multimodal Safety** | Early Progress Report | 0.0% Premature Opening | Evaluated on invalidated synthetic reviews | **INADMISSIBLE** |
| **YOLOv8n Still-Image mAP** | `experiments/vision/39f402dfe460/` | 99.46% mAP@50 | Evaluated on static split with data leakage | Supported (Layer A Only) |

---

## 14. Synthetic Test Coverage Matrix

The metric implementations were evaluated against safe unit tests in `tests/unit/`:

| Module Under Test | Test Suite File | Test Count | Key Invariants Covered |
| :--- | :--- | :---: | :--- |
| `classify_m4` | `test_mission10_m4_m5_differential.py` | 6 tests | Full 6-case coverage, independent oracle agreement, 1 $\mu\text{s}$ grid preservation. |
| $M4/M5$ Contracts | `test_mission4e2_m4_occupancy_contract.py` | 37 tests | Strict open interval, start boundary exclusion, $M5$ universal negative, denominator isolation. |
| Lead-In Screen | `test_event_metrics.py` | 18 tests | $\ge 3.6\,\text{s}$ screen logic, left-censored fallback, insufficient lead-in exclusion. |
| Descriptive Guard | `test_descriptive_only.py` | 12 tests | Refusal of forbidden claims, engine pooling rejection, schema validation. |
| Arithmetic & Wilson | `test_phase12_metric_arithmetic.py` | 14 tests | Wilson score zero-denominator protection, IEEE 754 nan/inf handling. |

Total synthetic metric tests: **87 tests** (100% passing).

---

## 15. Scientific Validity Assessment

1. **Construct Validity ($M4$):** **HIGH.** Directly measures whether an automated barrier ascends while a train physically occupies the crossing zone.
2. **Construct Validity ($M5$):** **HIGH.** Captures total sensor failure where the gate fails to close prior to train departure.
3. **Construct Validity ($\text{MTR}$):** **HIGH with Feasibility Screen; LOW without Screen.** Without screening for available lead-in, $\text{MTR}$ measures camera recording start times rather than algorithm performance.
4. **Criterion Validity (B1 Audio Only):** **INVALID for Gate Timing.** Audio cannot actuate the gate from IDLE; evaluating B1 for closure duration is a methodological error.
5. **Statistical Validity:** **HIGH.** Adhering to descriptive reporting avoids misleading $p$-values on a 27-event cohort.

---

## 16. Manuscript Claim Audit

| Manuscript Draft Statement | Section | Evidentiary Assessment | Required Revision |
| :--- | :---: | :--- | :--- |
| *"Evaluates premature opening ($M4$) across B0, B1, and B2."* | Abstract / Sec 4 | **CONTRADICTED.** B1 never closes; $M4$ cannot be evaluated on B1. | State clearly: *"$M4$ evaluated on B0 and B2; B1 evaluated for acoustic detection response only."* |
| *"Companion vehicle intrusions tracked under M5."* | Early Drafts | **CONTRADICTED.** M5 is barrier non-protection, not traffic intrusion. | Correct description to: *"M5 records events where the barrier never achieved a closed state before train clearance."* |
| *"Demonstrates zero premature opening in full deployment."* | Historical Docx | **INDEFENSIBLE.** Physical barrier is simulated; ground truth unapproved. | Retract claim; report descriptive results with confidence intervals. |
| *"Approach latency measured under 1.0 second."* | Historical Docx | **CONTRADICTED.** 20 of 23 train events are left-censored; unobservable. | Replace with lead-in feasibility screen results. |

---

## 17. Comprehensive Contradiction Register

| ID | Issue Description | Historical / Prompt Claim | Verified Source Reality | Evidence Source | Severity |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **METRIC-C01** | **M5 Semantic Definition** | "M5 — Companion Vehicle Intrusion" (traffic entering crossing) | M5 is `NEVER_PROTECTED_M5`: barrier never blocked before $T_4$. Companion metric to M4, zero traffic connection. | `metrics.py` L96–255; `v9.1.1_PROPOSED.md` L157 | **CRITICAL** |
| **METRIC-C02** | **Condition B1 Evaluability** | B1 can be evaluated for gate closure and premature opening | Audio in IDLE has zero actuation authority (`RULE_2`); gate never closes in B1. | `decision_engine.py` L402–405; `PHASE5_OUTPUT_AUDIT.md` L18 | **HIGH** |
| **METRIC-C03** | **Unscreened Missed-Train Rate** | Early reports claimed ~100% or 0% missed-train rates | Recordings are shorter than the 3.6s physical barrier descent time; screen is mandatory. | `lead_in_screen.py` L12–45 | **HIGH** |
| **METRIC-C04** | **Occupancy vs M4 Independence** | Assumed deferral of $T_2$ blocked all metric evaluation | $M4$ and $M5$ depend on $t_{\text{blocked}}$ and $T_4$; deferred $T_2$ blocks only occupancy duration. | `metrics.py` L230–280; `test_mission4e2_m4_occupancy_contract.py` | **MEDIUM** |

---

## 18. Prioritized Findings

1. **CRITICAL (METRIC-F01):** The definition of M5 must be formally corrected across manuscript drafts: it is **`NEVER_PROTECTED_M5`** (barrier failed to block), not Companion Vehicle Intrusion.
2. **HIGH (METRIC-F02):** Condition B1 (Front Audio Only) cannot be evaluated for gate-timing or clearance endpoints ($M4$, clearance latency, excess closed time). B1 must be reported solely as an acoustic perceptual baseline.
3. **HIGH (METRIC-F03):** Missed-train reporting must strictly enforce the lead-in feasibility screen ($\tau \ge 3.6\,\text{s}$) to avoid conflating video truncation with system failure.
4. **MEDIUM (METRIC-F04):** Roadway occupancy duration ($T_4 - T_2$) must remain formally deferred until a physical roadway-entry landmark ($T_2$) is ratified.

---

## 19. Required Researcher Decisions

1. **Decision D-METRIC-01 (M5 Manuscript Text):** Formally ratify the correction of M5 text in `PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md` to designate `never_protected_before_T4`.
2. **Decision D-METRIC-02 (Condition B1 Scope):** Confirm that Table 1 will report B1 as `NOT_APPLICABLE` for gate-timing metrics ($M4$, closure duration), reporting acoustic detection performance in Table 2.
3. **Decision D-METRIC-03 (Lead-In Screen Threshold):** Formally ratify the $\tau_{\text{min\_block}} = 3.6\,\text{s}$ lead-in feasibility screen constant derived from `configs/decision_policy_v1.yaml`.
4. **Decision D-METRIC-04 (Occupancy Deferral):** Reaffirm the deferral of roadway occupancy duration pending future field trials with calibrated entry geometry.

---

## 20. Explicit List of Unverified Matters Due to Safety Restrictions

1. **Real Empirical Values for Tables 1–3:** Actual numeric values for $M4$, $M5$, $\text{MTR}$, and clearance latency across real events were not computed, as real-data evaluation is unauthorized.
2. **Raw Acoustic Spectrogram Verification:** Audio feature energies were not verified against raw `.wav` recordings.
3. **Raw Video Landmark Timing:** Exact timestamps of $T_1$ and $T_4$ were not verified on `.mov` frames.
4. **Production Model Weight Execution:** YOLOv8n and Audio V3 checkpoints were not loaded into memory.

---

## 21. Final Disposition

Under the statutory terms of the Master Mission 16A Metric-Challenge charter, the auditor assigns the official audit disposition:

```
========================================================================================
FINAL DISPOSITION:
METRIC_AUDIT_CONTRADICTIONS_FOUND
========================================================================================
```

### Statutory Justification:
The mathematical implementation of $M4$, $M5$, and the lead-in screen in source code is exceptionally rigorous and passes all 87 synthetic tests. However, the disposition **`METRIC_AUDIT_CONTRADICTIONS_FOUND`** is strictly mandated by major contradictions between project documentation and implementation reality:
1. The fundamental semantic contradiction misrepresenting $M5$ as *"Companion Vehicle Intrusion"* when it is actually **`NEVER_PROTECTED_M5`** (absence of gate protection).
2. The experimental design contradiction attempting to evaluate gate timing on Condition B1 when `RULE_2` strictly denies audio any gate actuation authority in `IDLE`.
3. The historical contradiction of reporting missed-train rates without accounting for the $\approx 3.6\,\text{s}$ video truncation barrier.

---

## 22. Concluding Statutory Statement

```
========================================================================================
                       REAL-DATA EXECUTION: NOT AUTHORIZED
========================================================================================
Zero approved Stage-2.1 ground-truth records exist.
Mission 16A-METRIC-CHALLENGE is audit-only. The stop condition is satisfied.
========================================================================================
```
