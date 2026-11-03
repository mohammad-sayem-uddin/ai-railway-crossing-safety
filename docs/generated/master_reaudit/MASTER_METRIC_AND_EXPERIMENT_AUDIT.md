# Master Experimental Design and Metric Audit

**Project:** Train Gate Automation — Bangladesh  
**Auditor:** Independent Principal Research Auditor, Software Architect, Computer Vision Researcher, Security Auditor and Scientific Reproducibility Reviewer  
**Mission:** Master Mission 16A  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Audited Modules:** `src/railway_detection/evaluation/` (`metrics.py`, `lead_in_screen.py`, `timebase.py`, `clock_aware.py`), `configs/decision_policy_v1.yaml`  
**Standard:** Strict mathematical and algorithmic verification. Code-level metric trace.

---

## 1. Executive Summary

This audit rigorously evaluates the mathematical definitions, boundary conditions, censoring rules, and statistical validity of the evaluation metrics:
1. **M4 Premature Opening Rate (Primary Safety Metric):** Mathematically defined on the strict open interval $(t_{\text{blocked}}, T_4)$. The six-case classification in `metrics.py` is verified algorithmically. No arbitrary time tolerances or completeness relaxations exist.
2. **M5 Companion Count Metric:** Accurately isolates non-protected episodes where a replay observed the full interval $[0, T_4)$ but never blocked the passage.
3. **MTR Missed-Train Feasibility Screen:** `lead_in_screen.py` properly screens out events where available lead-in ($T_1 - \text{approach\_start}$) is below the physical barrier actuation latency ($\sim 3.6\text{–}3.9\,\text{s}$), preventing recording start cutoffs from being counted as detector failures.
4. **Canonical Boundary Taxonomy ($T_0\text{–}T_4$):**
   - $T_1$: Danger zone entry line.
   - $T_2$: Physical roadway boundary entry (deferred pending landmark calibration).
   - $T_3$: Locomotive lead unit clearance (isolates motive power exit).
   - $T_4$: Final vehicle tail clearance (end of roadway obstruction hazard).
   - Engine-only consist ($N=1$): $T_3 \equiv T_4$.
5. **One-Microsecond Snapping (DEC-C05):** All timestamps are snapped to a $1\,\mu\text{s}$ grid (`round(t, 6)`) in `timebase.py` to eliminate IEEE-754 floating-point representation noise without altering physical timing order.
6. **Statistical Boundary:** The study is strictly **descriptive**. Inferential statistical tests ($p$-values, McNemar, Wilcoxon, Holm adjustments) are scientifically invalid and strictly forbidden on this small 27-event cohort.

---

## 2. Metric M4: Premature Opening Formal Specification

### 2.1 Mathematical Definition and Interval Formulation
A premature opening occurs if the crossing barrier unblocks vehicular passage while the train is still occupying the roadway.
- **Protection Start ($t_{\text{blocked}}$):** The earliest simulation step timestamp $t$ where `is_passage_blocked == True` ($\theta \le 45.0^\circ$).
- **Hazard Termination ($T_4$):** Physical tail clearance timestamp of the final train car.
- **Protection Interval:** Strictly the open interval:
  $$\mathcal{I}_{\text{protect}} = (t_{\text{blocked}}, T_4)$$
- **Violation Condition:** Any simulation step within $\mathcal{I}_{\text{protect}}$ where `is_passage_blocked == False` or `gate_state` is `OPENING` or `OPEN`.

### 2.2 Six-Case Deterministic Classification (DEC-C01 through DEC-C05)
`classify_m4()` in `src/railway_detection/evaluation/metrics.py` implements a 6-case classification tree:

```
                    ┌────────────────────────────────────────┐
                    │ Does interval (t_blocked, T4) contain  │
                    │   any unblocked / opening step?        │
                    └──────────────────┬─────────────────────┘
                                       │
                         YES ──────────┴────────── NO
                          │                        │
                          ▼                        ▼
                 [CASE 1: VIOLATION]     ┌───────────────────┐
                Definite M4 Premature    │ Does replay reach │
                       Opening           │   step >= T4?     │
                                         └─────────┬─────────┘
                                                   │
                                     NO ───────────┴─────────── YES
                                      │                          │
                                      ▼                          ▼
                           [CASE 2: NOT_EVALUABLE]     ┌───────────────────┐
                           (Replay ended before T4)    │ Was passage EVER  │
                                                       │ blocked before T4?│
                                                       └─────────┬─────────┘
                                                                 │
                                                   NO ───────────┴─────────── YES
                                                    │                          │
                                                    ▼                          ▼
                                          ┌───────────────────┐     ┌─────────────────────┐
                                          │ Did replay start  │     │ Are there retained  │
                                          │   at t = 0.0s?    │     │ steps in interval?  │
                                          └─────────┬─────────┘     └──────────┬──────────┘
                                                    │                          │
                                      NO ───────────┴─────────── YES           │
                                       │                          │      NO ───┴─── YES
                                       ▼                          ▼       │          │
                            [CASE 3: NOT_EVALUABLE]        [CASE 5: M5]   │          ▼
                            (Replay started late)         (Never Blocked) │   [CASE 6: CLEAN]
                                                                          │  Protected Continuously
                                                                          ▼
                                                               [CASE 4: NOT_EVALUABLE]
                                                               (No steps in interval)
```

1. **Case 1 (`VIOLATION_WITNESSED`):** A step inside $(t_{\text{blocked}}, T_4)$ is unblocked. Witnessed violation; definite M4 regardless of start/end boundaries.
2. **Case 2 (`REPLAY_ENDED_BEFORE_T4`):** Replay cut off before $T_4$ with no violation witnessed. Evaluated as `NOT_EVALUABLE`; cannot be scored as clean protection.
3. **Case 3 (`REPLAY_STARTED_LATE`):** Replay began after recording origin and never blocked. Evaluated as `NOT_EVALUABLE` for M5.
4. **Case 4 (`NO_STEPS_IN_PROTECTION_INTERVAL`):** Protection interval contains zero simulation steps. Evaluated as `NOT_EVALUABLE` (insufficient evidence of continuous protection).
5. **Case 5 (`NEVER_PROTECTED` / M5):** Replay observed full interval $[0, T_4)$ but never blocked the passage. M5 count incremented.
6. **Case 6 (`PROTECTED_CONTINUOUS`):** Replay reached $T_4$ with steps throughout $(t_{\text{blocked}}, T_4)$ and zero unblocked states. Scored as clean protection.

---

## 3. Metric M5: Non-Protected Episode Companion Count

- **Purpose:** M4 measures premature opening *after* the barrier has initially lowered. If a system fails to detect the train entirely and never lowers the gate, M4's interval $(t_{\text{blocked}}, T_4)$ is undefined.
- **M5 Definition:** Integer count of train events where a fully observed replay ($[0, T_4)$) experienced **zero barrier closure** prior to $T_4$.
- **Independence:** M5 captures complete non-activations (catastrophic misses), ensuring that an inactive system does not achieve a falsely perfect M4 score of 0.0.

---

## 4. Metric MTR: Missed-Train Rate and Feasibility Screening

### 4.1 The Lead-In Feasibility Dilemma
In field video recordings, camera operators frequently start recording only when the train is already near the crossing.
- If a train is only $1.5\,\text{s}$ from the crossing danger zone ($T_1$) at video start, and the mechanical gate requires $3.5\,\text{s}$ to close, the gate will inevitably be open when the train reaches $T_1$.
- Labeling this an autonomous system failure would penalize the software for a physical impossibility caused by recording truncation.

### 4.2 Lead-In Feasibility Screen Algorithm (`lead_in_screen.py`)
- **Approach Start ($t_{\text{approach}}$):**
  - If $T_0$ is observable: $t_{\text{approach}} = T_0$.
  - If $T_0$ is left-censored ($T_0 \le 0.0\,\text{s}$): $t_{\text{approach}} = 0.0\,\text{s}$ (replay origin).
- **Available Lead-In:**
  $$\Delta t_{\text{available}} = T_1 - t_{\text{approach}}$$
- **Minimum Block Latency ($t_{\text{min\_block}}$):** Derived from frozen kinematics ($\sim 3.6\text{–}3.9\,\text{s}$).
- **Screen Outcome:**
  - If $\Delta t_{\text{available}} \ge t_{\text{min\_block}}$: Event **PASSES** screen; eligible for MTR evaluation.
  - If $\Delta t_{\text{available}} < t_{\text{min\_block}}$: Event is **SCREENED OUT** as `SCREEN_INSUFFICIENT_LEAD_IN` (`NOT_EVALUABLE`).
  - If $T_0$ or $T_1$ is unobservable: Event is marked `SCREEN_UNVERIFIABLE`.

---

## 5. Canonical Boundary Taxonomy ($T_0\text{–}T_4$) and Physical Grounding

Inspection of `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` §2 confirms physical scene definitions:

| Boundary | Event Time Meaning | Primary Camera View | Role in Evaluation | Grounding Status |
|:---:|---|:---:|---|---|
| **$T_0$** | First Visual Appearance | Front | Detection Latency ($T_{\text{detect}} - T_0$) | Observable in 5 events; left-censored in 18 events |
| **$T_1$** | Danger Zone Entry | Front | Warning Lead Time ($T_1 - T_{\text{detect}}$) | Observable at physical frog/track boundary |
| **$T_2$** | Crossing Occupancy Start | Front / Back | Roadway blockage onset | **DEFERRED.** Requires physical road landmark calibration |
| **$T_3$** | Lead Locomotive Unit Clearance | Back | Diagnostic: Lead motive power exits | Observable in all multi-car consists; isolates unit exit |
| **$T_4$** | Final Vehicle Tail Clearance | Back | Primary Clearance Baseline for M4/POR | Observable in 22 of 23 train events (event 005 cut off) |
| **$T_3 \equiv T_4$** | Engine-Only Consist Clearance | Front / Back | Single locomotive unit ($N=1$) | Verified identity in `engine_events/event_001` |

**Crucial Finding on $T_2$:** Early proposals attempted to define $T_2$ as "camera lens-plane entry". This was rejected because lens-plane passage depends on camera focal length and mounting position, not roadway boundary. Reconciled physical $T_2$ requires a physical roadway landmark, which remains formally deferred.

---

## 6. Timestamp Precision and Snapping (DEC-C05)

- In `src/railway_detection/evaluation/timebase.py`:
  ```python
  TIMESTAMP_ROUND_DIGITS = 6
  def normalize_timestamp(value: float) -> float:
      return round(float(value), TIMESTAMP_ROUND_DIGITS)
  ```
- **Rationale:** Strict inequalities ($t < T_4$) in Python can be corrupted by IEEE-754 floating-point inaccuracies (e.g. $0.1 + 0.2 = 0.30000000000000004 > 0.3$).
- **Audit Verification:** Snapping to 6 decimal places ($1\,\mu\text{s}$) resolves representation noise while preserving chronological ordering down to microsecond resolution. It is a numerical representation fix, not an empirical tolerance.

---

## 7. Statistical Validity: Strict Descriptive Boundaries

The research project is structured exclusively as a **single-site descriptive benchmark**.

### Prohibited Inferential Procedures
The following statistical techniques are **methodologically invalid** for this study and are strictly prohibited in reporting:
1. **$p$-Values & Significance Testing:** Hypothesis tests against arbitrary null models are invalid given the non-random, single-site sampling.
2. **McNemar & Wilcoxon Paired Tests:** Paired non-parametric tests on $N=23$ non-independent train events violate exchangeability assumptions.
3. **Holm-Bonferroni Family-Wise Corrections:** False-discovery corrections cannot compensate for structural sample deficits.
4. **Generalization Claims:** Any claim that the system improves railway crossing safety across Bangladesh or general crossings is scientifically unsupported.

### Valid Reporting Framework
- **Point Estimates:** Proportions (e.g. $\text{POR} = k / n$) and medians / interquartile ranges for continuous delays.
- **Wilson Score 95% Confidence Intervals:** Explicitly computed via `wilson_score_interval()` in `metrics.py` to transparently expose wide uncertainty bounds on small denominators.

---

## 8. Audit Conclusion

The experimental design and metric formulations in `metrics.py` and `lead_in_screen.py` are mathematically rigorous, deterministic, and free of arbitrary tolerances. They establish a sound framework for descriptive offline benchmarking.

**Metric and Experiment Audit Status: VERIFIED — MATHEMATICALLY SOUND.**
