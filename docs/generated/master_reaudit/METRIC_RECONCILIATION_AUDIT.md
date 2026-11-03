# MISSION 16A-METRIC-RECONCILIATION: INDEPENDENT METRIC CONTRACT AND TERMINOLOGY RECONCILIATION

**Project:** Train Gate Automation — Bangladesh  
**Mission:** Master Mission 16A Follow-up Metric Reconciliation Audit  
**Auditor:** Independent Principal Research Methodologist, Software Verification Auditor, and Experimental Design Reviewer  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Git Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Audit Standard:** Strict Read-Only, Evidence-Based, Adversarial  
**Execution Authority:** NONE  
**Research Authorization:** NONE  

---

## 1. Executive Summary

This audit independently reconciles the mathematical metric contracts, source implementations, frozen configurations, synthetic test evidence, historical reports, and manuscript terminology across the Train Gate Automation repository.

### Key Audit Findings:
1. **Canonical Metric Contract Verified:** The primary safety metric $M4$ (Premature Opening) is rigorously defined on the strict open interval $(t_{\text{blocked}}, T_4)$ and implemented in [`src/railway_detection/evaluation/metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) via `classify_m4()`. Witnessed violations are preserved unconditionally, incomplete replays are categorized by explicit failure reasons, and all timestamps snap to a $1\,\mu\text{s}$ grid (`DEC-C05`).
2. **M5 Semantic Reconciliation:** M5 is definitively verified as **`NEVER_PROTECTED_M5`** (*"Never Protected Before $T_4$"*). It is a **companion failure metric to $M4$** capturing replays covering $[0, T_4)$ where the barrier never blocked passage. It is reported as an integer count only (`RD-017`) and excluded from the $M4$ denominator. The phrase *"Companion Vehicle Intrusion"* was a semantic misinterpretation in early review prompts; zero lines of code or primary protocol define M5 as road vehicle tracking.
3. **B1 Architectural Boundary Reconciled:** Under `RULE_2_AUDIO_SUPPORT_ONLY` in [`src/railway_detection/fusion/decision_engine.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/decision_engine.py), acoustic horn detections in `IDLE` have **zero gate actuation authority** (`"no gate actuation"`). In Condition B1 (vision masked), the barrier remains vertical at $90^\circ$ for 100% of simulation steps across all events. Evaluating B1 for premature opening ($M4$), closure latency, or gate timing is an **architectural impossibility**. Condition B1 is valid strictly as an acoustic perceptual baseline (window precision/recall and false alarms).
4. **MTR Feasibility & Censoring Provenance:** The $\tau_{\text{min\_block}} \approx 3.6\,\text{s}$ feasibility screen threshold in [`src/railway_detection/evaluation/lead_in_screen.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/lead_in_screen.py) is **implementation-derived** from `configs/decision_policy_v1.yaml` (2 ticks confirm + 2.0s dwell + 1.5s descent to $45^\circ$). Censoring counts are reconciled: exactly **20 of 23 train events** have $T_0 \le 0.0\,\text{s}$ in active proposals; the historical "18 of 22" figure referred specifically to events with lead time $T_1 \le 3.2\,\text{s}$ that fail the 3.6s feasibility screen.
5. **Decoupling of $M4/M5$ from Deferred $T_2$ Landmark:** The deferral of the $T_2$ roadway-entry landmark (`RD-006`, `DEC-D01`) blocks Roadway Occupancy Duration ($T_4 - T_2$), but does **not** block $M4$ or $M5$. $M4$ and $M5$ depend strictly on $t_{\text{blocked}}$ and $T_4$.
6. **Descriptive Statistical Compliance:** The evaluation architecture in [`src/railway_detection/evaluation/descriptive_only.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/descriptive_only.py) programmatically blocks $p$-values, inferential hypothesis testing, and cross-site generalization claims in compliance with **RD-023**.
7. **Synthetic Test Verification:** 118 test cases across 5 dedicated unit test files pass with 100% compliance under synthetic isolation.

---

## 2. Canonical Metric Contract

The formal, executable contract implemented in [`src/railway_detection/evaluation/metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) establishes the following specifications:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ CANONICAL SAFETY & PERFORMANCE METRIC CONTRACT                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. TIMEBASE & COMPARISON GRID (DEC-C05)                                     │
│    - Timestamps snapped to 1-microsecond lattice: round(t, 6)               │
│    - Strict inequalities: open interval (t_blocked, T4)                    │
│    - Explicit exclusion of boundary steps at t = t_blocked and t = T4       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. M4: PREMATURE OPENING (RD-016, RD-022)                                   │
│    - Interval: (t_blocked, T4)                                              │
│    - Witnessed violation: unblocked or OPENING/OPEN step inside interval    │
│    - Replay completeness: last_step >= T4 required for clean non-violation  │
│    - Denominator: Replays that block before T4 and cover T4 (or violation)  │
│    - Exclusions: M5 events, t4_missing, replay_ended_before_T4, empty       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. M5: NEVER PROTECTED (RD-016, RD-017)                                     │
│    - Universal negative condition over [0, T4)                              │
│    - Criteria: first_step <= 0.0 AND last_step >= T4 AND zero blocked steps │
│    - Reporting form: Integer count only (never rate/percentage)             │
│    - Denominator: Excluded from M4 denominator                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. MTR: LEAD-IN FEASIBILITY SCREEN (RD-021)                                 │
│    - Available lead-in: Delta_t = T1 - approach_start (T0 or 0.0)           │
│    - Screen condition: Delta_t >= tau_min_block (approx 3.6 s)              │
│    - Outcome: SCREEN_INSUFFICIENT_LEAD_IN excludes event from missed train  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. M4/M5 Traceability Matrix

| Metric | Canonical Definition | Source Location | Synthetic Test Evidence | Conflicts & Misconceptions | Required Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **$M4$ (Premature Opening)** | Any step in $(t_{\text{blocked}}, T_4)$ where barrier is unblocked or state is `OPENING`/`OPEN`. | [`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) `classify_m4()` L230–338 | `test_mission10_m4_m5_differential.py` L18–90; `test_mission4e2_m4_occupancy_contract.py` L15–85 | Historical v9 protocol defined POR starting at $T_1$; conflated late warning with premature opening. | Maintain canonical $t_{\text{blocked}}$ start boundary; preserve historical text in marked blocks. |
| **$M5$ (Never Protected)** | Replay covering $[0, T_4)$ where barrier never achieves passage-blocked state. | [`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) L245–338; `M4_STATUS_NEVER_PROTECTED` | `test_mission4e2_m4_occupancy_contract.py` L90–120 (`TestM5NeverProtected`) | Erroneously labeled *"Companion Vehicle Intrusion"* in review prompt narratives. | Formally correct terminology to *"Never Protected Before $T_4$"*; report as count only. |
| **$M4$ Denominator** | Count of events with witnessed violation OR valid complete non-violation. | [`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) `EventMetricsCalculator` L650–710 | `test_mission4e2_m4_occupancy_contract.py` L170–210 (`TestM4M5DenominatorSeparation`) | Early drafts attempted to include $M5$ in $M4$ denominator, creating invalid rates. | Enforce strict exclusion of $M5$, missing $T_4$, and engine events from $M4$ denominator. |

---

## 4. Condition B1 Architecture and Valid Evaluation Scope

### 4.1 Architectural Impossibility vs. Missing Implementation
Analysis of [`src/railway_detection/fusion/decision_engine.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/decision_engine.py) lines 390–420 and [`configs/decision_policy_v1.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/configs/decision_policy_v1.yaml):
- In state `IDLE`:
  ```python
  if audio_train_detected:
    rule_id = RuleId.RULE_2_AUDIO_SUPPORT_ONLY.value
    explanation = (
        "Audio train noise observed in IDLE; supporting only, no gate actuation"
    )
```
- Transition to `WARNING` or `CLOSING` requires `consecutive_approach_count >= confirm_frames`, which is driven **exclusively by visual detection**.
- Under Condition B1, visual inputs are masked (`vision_active = False`).
- Consequently, the gate **never actuates out of IDLE** across the entire simulation duration.

### 4.2 Distinguishing Evaluation Categories for B1
| Evaluation Metric | Evaluability Under B1 | Scientific Reason | Category |
| :--- | :---: | :--- | :--- |
| **Premature Opening ($M4$)** | **NOT EVALUABLE** | Barrier never achieves blocked state; interval $(t_{\text{blocked}}, T_4)$ does not exist. | **Architectural Impossibility** |
| **Clearance Latency** | **NOT EVALUABLE** | Gate never closes, so it never executes a reopening transition. | **Architectural Impossibility** |
| **Excess Closed Duration** | **NOT EVALUABLE** | Gate closed duration is identically $0.0\,\text{s}$. | **Architectural Impossibility** |
| **Gate-Level MTR** | **NOT EVALUABLE** | Gate fails to block by $T_1$ by invariant design, not detector failure. | **Architectural Impossibility** |
| **Audio Window Precision/Recall**| **EVALUABLE** | Evaluates CompactTrainHornCNN V3 detection against labeled horn timestamps. | **Valid Perceptual Endpoint** |
| **Audio Nuisance Rate** | **EVALUABLE** | Measures false positive horn windows during negative control passages. | **Valid Perceptual Endpoint** |
| **Time-to-First-Horn ($T_{\text{horn}}$)**| **EVALUABLE** | Measures latency from audio onset to first confident horn classification. | **Valid Perceptual Endpoint** |

---

## 5. MTR Feasibility Screen Threshold and Censoring Provenance

### 5.1 Provenance of the 3.6-Second Threshold
Inspection of [`src/railway_detection/evaluation/lead_in_screen.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/lead_in_screen.py) lines 20–45 and 150–220:
- Function `derive_min_block_latency_s()` derives the threshold by executing a constant synthetic visual detection through `EventSimulationRunner`:
  $$\tau_{\text{confirm}} = 2 \times 0.20\,\text{s} = 0.40\,\text{s}$$
  $$\tau_{\text{warn\_dwell}} = 2.00\,\text{s}$$
  $$\tau_{\text{descent\_to\_45}} = \frac{90^\circ - 45^\circ}{30^\circ/\text{s}} = 1.50\,\text{s}$$
  $$\tau_{\text{min\_block}} = 0.40 + 2.00 + 1.50 - \epsilon \approx 3.60\,\text{s}$$
- **Provenance Classification:** It is an **implementation-derived kinematic threshold**, not an externally ratified railway standard (`AREMA` or `FRA`). It reflects the immutable physical behavior of the frozen software gate model.

### 5.2 Forensic Re-Evaluation of Historical Censoring Counts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ RECONCILIATION OF CENSORING NUMBERS (18/23 vs 20/23 vs 23/23)               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. 20 of 23 Train Events (VERIFIED_SAFE_METADATA):                          │
│    Active proposals in data/ground_truth/proposals/train_events/ prove that │
│    exactly 20 events have T0 = 0.0 s (locomotive already in frame at start).│
│    Only 3 events (009, 015, 016) have observable arrival (T0 = 1.5 s).      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. 18 of 22 Train Events (HISTORICAL_REPORT_CONFLATION):                    │
│    In finding IMA-31, 22 events had candidate T1 (excluding unobservable   │
│    event_005). Exactly 18 of those 22 had T1 <= 3.2 s (< 3.6 s threshold). │
│    Subsequent reports mistakenly called this "18 left-censored events".     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. 23 of 23 Train Events (HISTORICAL_REPORT_ONLY):                          │
│    Early informal reports assumed 100% of train recordings were truncated.  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Temporal-Boundary Dependency Matrix

| Metric Endpoint | $T_0$ | $T_1$ | $T_2$ | $T_3$ | $T_4$ | $t_{\text{blocked}}$ | Computable with Deferred $T_2$? | Blocked by Ground-Truth Hold? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Premature Opening ($M4$)** | — | — | — | Diagnostic | **Required** | **Required** | **YES (Independent of $T_2$)** | **YES (Awaiting Stage-2.1 $T_4$)** |
| **Never Protected ($M5$)** | Origin ($0.0$) | — | — | — | **Required** | Replay steps | **YES (Independent of $T_2$)** | **YES (Awaiting Stage-2.1 $T_4$)** |
| **Lead-In Screen ($\text{MTR}$)**| **Required** | **Required** | — | — | — | — | **YES (Independent of $T_2$)** | **YES (Awaiting Stage-2.1 $T_1$)** |
| **Warning Lead Time** | — | **Required** | — | — | — | Controller | **YES (Independent of $T_2$)** | **YES (Awaiting Stage-2.1 $T_1$)** |
| **Clearance Latency** | — | — | — | — | **Required** | Controller | **YES (Independent of $T_2$)** | **YES (Awaiting Stage-2.1 $T_4$)** |
| **Roadway Occupancy Duration** | — | — | **Required** | — | **Required** | — | **NO (BLOCKED BY DEFERRED $T_2$)** | **YES (Blocked by $T_2$ and Hold)** |

> [!NOTE]
> **Verification of $T_2$ Deferral Impact:** Source inspection of [`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) lines 230–338 confirms that `classify_m4` takes only `sim_result` and `clearance_time_s` ($T_4$). It never accesses $T_2$. The claim that $T_2$ deferral does not block $M4$ or $M5$ is **VERIFIED**.

---

## 7. Manuscript and Document Contradiction Register

| # | File Path | Line / Section | Existing Wording | Canonical Evidence | Severity | Proposed Editorial Correction |
| :-: | :--- | :--- | :--- | :--- | :---: | :--- |
| **1** | [`docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md) | Table 1 (L290–300) | Displays B1 column under Gate-Timing and Clearance metrics ($M4$, Latency) | `decision_engine.py` L402; `RULE_2` forbids gate actuation in IDLE | **HIGH** | Mark B1 cells as `N/A (Audio Supporting Only, RD-030)`; move acoustic F1/nuisance to Table 2. |
| **2** | Historical Drafts & Prompts | Metric Descriptions | *"M5 — Companion Vehicle Intrusion"* | `metrics.py` L96; `FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL_v9.1.1_PROPOSED.md` L157 | **HIGH** | Replace with *"M5 — Never Protected Before $T_4$ (Companion Failure Metric to $M4$)"*. |
| **3** | [`docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md) | Sec 6.2 | *"18 of 23 train events are left-censored"* | Active proposals in `data/ground_truth/proposals/` prove 20/23 have $T_0 \le 0.0$ | **MEDIUM** | Update text to: *"20 of 23 train events are left-censored ($T_0 \le 0.0\,\text{s}$); 18 events fail the 3.6s lead-in screen"*. |
| **4** | Historical Word Report | Executive Summary | *"Eliminates premature opening risk entirely ($0.0\%$ failure)"* | Pre-Phase 5 diagnostic runs on invalidated reviews; barrier simulated | **CRITICAL** | Retract claim; replace with descriptive placeholder `[RESULTS PENDING - EVALUATION NOT AUTHORIZED]`. |
| **5** | [`docs/FINAL_ABLATION_MATRIX.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FINAL_ABLATION_MATRIX.md) | Sec 3.2 | Defines Premature Opening Rate (POR) as opening while $t \in [T_1, T_4]$ | `RD-016`; `metrics.py` defines $M4$ on $(t_{\text{blocked}}, T_4)$ | **MEDIUM** | Wrap historical POR text in `<!--HISTORICAL-->` blocks; state canonical $M4$ interval. |

---

## 8. Statistical and Scientific Claims Audit

1. **Compliance with RD-023 (Descriptive Statistics Only):**
   - Verified: [`descriptive_only.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/descriptive_only.py) enforces pure descriptive aggregation.
   - All inferential hypothesis tests ($p$-values, McNemar, Wilcoxon signed-rank tests) are strictly omitted from active reporting pipelines.
   - Uncertainty reporting is restricted to binomial Wilson score 95% confidence intervals with explicit non-zero denominators.
2. **Prohibited Overgeneralization Claims:**
   - Claims of cross-site generalization, all-weather robustness, or physical fail-safe certification are unsupported by repository evidence (single site, 27 events, daytime only, simulated barrier).

---

## 9. Synthetic Test Coverage Audit

Audit of the 118 collected test cases across the 5 primary metric test suites:

| Test File | Total Cases | Primary Coverage Areas | Verification Status |
| :--- | :---: | :--- | :---: |
| [`test_mission10_m4_m5_differential.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_mission10_m4_m5_differential.py) | 13 | Comprehensive comparison of production `classify_m4` against independent oracle; $1\,\mu\text{s}$ lattice snapping; float noise invariance. | **VERIFIED PASS** |
| [`test_mission4e2_m4_occupancy_contract.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_mission4e2_m4_occupancy_contract.py) | 57 | Strict open interval $(t_{\text{blocked}}, T_4)$; boundary point exclusion; $M5$ negative condition; denominator isolation; occupancy clock models. | **VERIFIED PASS** |
| [`test_event_metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_event_metrics.py) | 8 | Cohort aggregation; Wilson score calculations; engine event denominator exclusion; nearest-step matching. | **VERIFIED PASS** |
| [`test_descriptive_only.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_descriptive_only.py) | 18 | Enforcement of RD-023; rejection of inferential claims; cache provenance validation; non-mutation of caller objects. | **VERIFIED PASS** |
| [`test_phase12_metric_arithmetic.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_phase12_metric_arithmetic.py) | 22 | Wilson interval hand-calculation parity; zero-denominator safety; clearance latency and excess closed duration arithmetic. | **VERIFIED PASS** |

**Total Validated Metric Tests:** **118 test cases** (All classified as `SYNTHETIC_ONLY` in manifest; 0 access violations).

---

## 10. Proposed Corrections Separated from Verified Facts

### Verified Architectural Facts:
- $M4$ is implemented on $(t_{\text{blocked}}, T_4)$ with 6 explicit cases.
- $M5$ is implemented as `NEVER_PROTECTED_M5` over $[0, T_4)$ as a count only.
- Audio in `IDLE` has zero actuation authority under `RULE_2`.
- $\tau_{\text{min\_block}} \approx 3.6\,\text{s}$ is derived from the frozen configuration.
- 20 of 23 train events have $T_0 \le 0.0\,\text{s}$ in candidate proposals.

### Proposed Editorial Corrections (Awaiting Researcher Sign-Off):
- **Correction 1:** In `PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`, replace all occurrences of *"companion vehicle intrusion"* with *"never protected before $T_4$ ($M5$)"*.
- **Correction 2:** In `PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md` Table 1, replace B1 gate-timing cells with `N/A (RULE_2: Audio Supporting Only)`.
- **Correction 3:** Disambiguate censoring text: clarify that 20 events are left-censored ($T_0 \le 0$), while 18 events fail the 3.6s lead-in feasibility screen ($T_1 \le 3.2\,\text{s}$).

---

## 11. Unresolved Questions Requiring Researcher Decisions

The following open decisions must be confirmed by the Principal Investigator:
1. **Decision D-REC-01:** Formally approve the presentation format for Condition B1 in the manuscript (reporting B1 exclusively in Table 2 for acoustic perception).
2. **Decision D-REC-02:** Ratify the replacement of historical POR text in protocol specifications with canonical $M4$ $(t_{\text{blocked}}, T_4)$ wording.
3. **Decision D-REC-03:** Formally approve the text clarifying the 20/23 left-censored versus 18/22 short lead-in distinction in manuscript Section 6.

---

## 12. Git and Safety Preservation Statement

- **Output File Created:** [`docs/generated/master_reaudit/METRIC_RECONCILIATION_AUDIT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/METRIC_RECONCILIATION_AUDIT.md)
- **Git HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (Unchanged)
- **Staged Files:** `0`
- **Modified Tracked Files:** `25` (Unchanged)
- **Untracked Entries:** `388` (Unchanged)
- **Prohibited Media / Checkpoints Accessed:** `NONE`
- **Real-Data Replay / Evaluation Executed:** `NONE`

---

## 13. Final Statutory Disposition

Under the terms of the Master Mission 16A Metric Reconciliation Charter, the auditor assigns the official disposition:

```
========================================================================================
FINAL DISPOSITION:
METRIC_CONTRACT_RECONCILED_WITH_LIMITATIONS
========================================================================================
```

### Justification:
The mathematical metric contracts, source-code implementations (`metrics.py`, `lead_in_screen.py`, `descriptive_only.py`), and synthetic unit test suites (118 cases) are **mutually consistent, robustly tested, and fully reconciled**. The disposition carries the limitation designation because historical reports and manuscript drafts retain legacy terminology ("companion vehicle intrusion", B1 gate timing, ambiguous censoring counts) that must be updated via documented editorial corrections.

---

## 14. Concluding Statutory Statement

```
========================================================================================
                       REAL-DATA EXECUTION: NOT AUTHORIZED
========================================================================================
Zero approved Stage-2.1 ground-truth records exist.
Mission 16A-METRIC-RECONCILIATION is audit-only. The stop condition is satisfied.
========================================================================================
```
