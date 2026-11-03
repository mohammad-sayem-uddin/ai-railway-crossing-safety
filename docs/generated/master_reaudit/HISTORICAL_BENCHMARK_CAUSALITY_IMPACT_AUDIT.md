# MISSION 16B: HISTORICAL BENCHMARK CAUSALITY IMPACT AND METRIC RECLASSIFICATION AUDIT

**Project:** Train Gate Automation — Bangladesh  
**Mission:** Master Mission 16B — Benchmark Causality Impact Audit  
**Auditor:** Independent Benchmark Auditor, Simulation Verification Engineer, Temporal-Semantics Researcher, and Research Methodology Reviewer  
**Audit Target:** Historical Benchmark Results, Retroactive Simulation Causality Defect, Metric Reclassification ($M4, M5$, Closed Duration, Clearance Latency, WLT), Table 11 Historical Outcomes, and Manuscript Exposure  
**Historical Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Execution Authority:** NONE  
**Research Authorization:** NONE  
**Audit Mode:** Strict read-only, synthetic-only, metadata-only, evidence-based  

---

## 1. Executive Summary

This independent audit evaluates how the temporal-semantics defect identified in Mission 16A—specifically, the retroactive interval gate actuation in [`EventSimulationRunner._run_frames()`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L187-L267)—affects historical benchmark records, reported safety metrics ($M4, M5$), empirical duration measurements, and manuscript claims.

### The Central Research Question:
> *If the historical simulation had used forward-causal gate actuation instead of the existing retroactive interval convention, which historical metric results would actually change?*

### Definitive Audit Findings:
1. **Historical Real-Data $M4$ and $M5$ Were Never Computed ($N = 0$):**  
   Primary evidence from all 17 historical benchmark result packages (`results/experiments/*/summary.json`) and active candidate proposals (`data/ground_truth/proposals/`) demonstrates that **roadway clearance timestamp $T_4$ has never been approved or populated for any train event** ($T_4 = \text{null}$ across all 23 train events). Consequently, in historical benchmark execution, $M4$ (Premature Opening) and $M5$ (`NEVER_PROTECTED_M5`) were **never evaluable on real events** (`premature_opening_evaluable_count: 0`, `premature_opening_rate: null`). Table 3 of the draft manuscript ([`docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md#L180-L210)) explicitly records both metrics as **`NON-COMPUTABLE`**. Therefore, **zero real-data $M4$ or $M5$ classifications change**, because no empirical classifications ever existed.
2. **Table 11 Closed-Duration Measurements Are Confirmed Affected (Level 1 / Level 2):**  
   The per-event `Closed Duration` reported for all 27 events in [`results/experiments/tables/table11_per_event_summary.md`](file:///Users/sayemuddin/Desktop/Train_automation/results/experiments/tables/table11_per_event_summary.md) was directly computed by summing `dt` on retroactively stepped gate states. Retroactive stepping advances initial blockage by $\Delta t$ ($0.20\,\text{s}$ at 5 Hz) and unblocking by $\Delta t$. For events where the gate remained closed at recording termination, the reported duration is increased by exactly $+0.20\,\text{s}$. For events with complete opening cycles, duration is shifted by discrete sample quantization ($\pm 0.20\,\text{s}$).
3. **Missed-Train Feasibility Screen Threshold Derived Incorrectly (Level 1):**  
   The 3.60 s screen threshold derived via [`derive_min_block_latency_s()`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/lead_in_screen.py#L159-L226) shifted from the forward-causal discrete value of $3.80\,\text{s}$ (at 5 Hz) to $3.60\,\text{s}$ due to retroactive stepping. While the threshold value changes by $-0.20\,\text{s}$, the screening outcome over the 22 observable train events remains invariant: 21 of 22 events continue to fail the screen because their recorded lead-in is $\le 3.20\,\text{s}$ (or net visual lead-in $2.70\,\text{s}$).
4. **Warning Lead Time Is Confirmed Independent (Level 4):**  
   Warning lead time is calculated from `first_warning_time`, which is recorded when the controller enters `CrossingState.WARNING` inside `decision_engine.evaluate_frame()` *prior* to gate model stepping. It is strictly independent of gate kinematics.

---

## 2. Scope and Safety Boundary

This mission was conducted under strict read-only audit restrictions:
- Zero raw video (`.mov`, `.mp4`) or audio (`.wav`) files were opened, previewed, decoded, or hashed.
- Zero production checkpoints (`best.pt`) or protected production caches (`results/experiments/cache/`) were loaded or accessed.
- Zero real-data evaluations, inference runs, or timing pilots were executed.
- Zero Git modifications, commits, checkouts, or staging operations were performed.
- All evidence was established from permitted safe source code, test suites, historical markdown/JSON result summaries, and proposal metadata.

---

## 3. Historical Baseline and Repository Integrity

- **Repository HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (verified matching historical baseline).
- **Tracked Modifications:** Exactly 25 modified tracked files preserved without alteration.
- **Untracked Files:** Exactly 388 porcelain untracked entries preserved.
- **Staged Changes:** Exactly 0 staged files.
- **Audit File Created:** Exactly one new audit deliverable: [`docs/generated/master_reaudit/HISTORICAL_BENCHMARK_CAUSALITY_IMPACT_AUDIT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/HISTORICAL_BENCHMARK_CAUSALITY_IMPACT_AUDIT.md).

---

## 4. Independent Source-Level Causality Verification

In [`src/railway_detection/simulation/runner.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L187-L267), the execution order inside the frame loop is:
```python
# Lines 188-229
t = frame.master_timestamp_s
dt = max(0.0, t - prev_t)

# 1. Decision engine evaluates frame at t and mutates crossing_state
decision = stage("decision_evaluation", lambda: self.decision_engine.evaluate_frame(frame, ...))

# 2. Extract commanded gate state from the decision evaluated at t
commanded_gate = GateState(decision.resulting_gate_state)

# 3. Gate model steps dt using the NEW command decided at t
angle = stage("gate_model_step", lambda: self.gate_model.step(dt, commanded_gate))
```

### Causality Defect Mechanics:
- `dt` represents the duration of the *elapsed* interval $[prev\_t, t]$.
- During that interval, the crossing was in the *previous* state (e.g. `WARNING`), and the gate was commanded `OPEN`.
- At timestamp $t$, the dwell condition is met, and `decision.resulting_gate_state` becomes `CLOSING`.
- Passing `dt` and `CLOSING` to `gate_model.step()` causes [`PhysicalGateModel`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/gate_model.py#L42-L65) to integrate angular motion over $[prev\_t, t]$ using the new command.
- The gate is simulated as having closed at $30^\circ/\text{s}$ during the preceding interval.
- **Conclusion:** Actuator motion is retroactively applied, shifting physical barrier position backward in time by $\Delta t$.

---

## 5. $M4$ (Premature Opening) Dependency and Impact Analysis

### 5.1 Metric Definition & Implementation
In [`src/railway_detection/evaluation/metrics.py:688-750`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py#L688-L750), $M4$ is defined over the strict open interval $(t_{\text{blocked}}, T_4)$ on the 1-$\mu$s snapped grid (`DEC-C05`):
- `t_blocked`: Timestamp of the first retained simulation step where `is_passage_blocked == True` ($\theta \le 45.0^\circ$).
- `T4`: Ground-truth roadway clearance timestamp.
- Violation condition: Any step $s$ with $t_{\text{blocked}} < t < T_4$ where `not s.is_passage_blocked` or `s.gate_state in ("OPENING", "OPEN")`.

### 5.2 Theoretical Exposure Conditions
Under forward-causal stepping:
1. **Closure Boundary ($t_{\text{blocked}}$):** Occurs $\Delta t$ later ($3.80\,\text{s}$ vs $3.60\,\text{s}$ at 5 Hz).
2. **Opening Boundary ($t_{\text{unblock}}$):** Occurs $\Delta t$ later.
3. **Potential Metric Divergence:** If an opening command is issued near $T_4$:
   - *Retroactive Stepping:* The gate unblocks during $[T_4 - \Delta t, T_4]$, recording an unblocked step inside the protection window ($M4 = \text{True}$).
   - *Forward-Causal Stepping:* The gate begins opening at $T_4$, remaining blocked until $T_4 + 1.5\,\text{s}$, recording zero unblocked steps before $T_4$ ($M4 = \text{False}$).

### 5.3 Empirical Reality in Historical Benchmark Data
- **Primary Evidence:** In all 17 historical experiment summaries (`results/experiments/*/summary.json`):
  ```json
  "premature_opening_evaluable_count": 0,
  "premature_opening_count": 0,
  "premature_opening_rate": null
  ```
- **Manuscript Table 3:** Explicitly lists Premature-Opening Rate as **`NON-COMPUTABLE`**.
- **Root Cause:** $T_4$ requires camera 2 (back camera) and R04 audio-visual synchronization, which was deferred under Decision RD-006.
- **Audit Verdict:** **`NO HISTORICAL METRIC CHANGE`** (Level 3 theoretical exposure, Level 4 empirical impact). Zero empirical $M4$ classifications were ever published or evaluated on real events.

---

## 6. $M5$ (`NEVER_PROTECTED_M5`) Dependency and Impact Analysis

### 6.1 Metric Definition & Implementation
In [`src/railway_detection/evaluation/metrics.py:734-758`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py#L734-L758), $M5$ is defined as:
- A companion safety failure indicator asserting that an approaching train was never protected before clearing the roadway.
- Asserted over $[0, T_4)$ if:
  1. The replay begins at origin ($t_0 \le 0.0\,\text{s}$).
  2. The replay covers $T_4$ ($t_{\text{last}} \ge T_4$).
  3. Zero retained steps before $T_4$ have `is_passage_blocked == True`.

### 6.2 Theoretical Exposure Conditions
If a train cleared the crossing extremely quickly such that $T_4 \in [3.60\,\text{s}, 3.80\,\text{s}]$:
- *Retroactive Stepping (5 Hz):* Gate reaches $42.0^\circ$ at $t = 3.60\,\text{s} < T_4$. The crossing is protected ($M5 = \text{False}$).
- *Forward-Causal Stepping (5 Hz):* At $t = 3.60\,\text{s}$, gate is at $48.0^\circ > 45.0^\circ$ (unblocked). At $t = 3.70\,\text{s}$, train clears ($T_4$). No blocked step exists before $T_4$ ($M5 = \text{True}$).

### 6.3 Empirical Reality in Historical Benchmark Data
- In all candidate proposals (`data/ground_truth/proposals/train_events/`), $T_4$ is unpopulated (`None`).
- In historical benchmark summaries, $M5$ was never evaluated.
- **Audit Verdict:** **`NO HISTORICAL METRIC CHANGE`** (Level 3 theoretical exposure). No historical $M5$ results exist to be altered.

---

## 7. Closed-Duration Impact Analysis

### 7.1 Accumulation Implementation
In [`src/railway_detection/simulation/runner.py:231-233`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L231-L233):
```python
if self.gate_model.is_passage_blocked or self.gate_model.is_fully_closed:
    total_closed_time += dt
```
`total_closed_time` accumulates `dt` on every step where the gate is lowered to $\le 45.0^\circ$.

### 7.2 Quantitative Impact on Historical Table 11
In Table 11 ([`results/experiments/tables/table11_per_event_summary.md`](file:///Users/sayemuddin/Desktop/Train_automation/results/experiments/tables/table11_per_event_summary.md)), empirical closed durations are tabulated for all 27 events (e.g. `event_001`: 46.0s, `event_004`: 74.4s, `event_006`: 122.4s).
- **Start of Closure:** Retroactive stepping triggers `is_passage_blocked` one tick ($0.20\,\text{s}$) earlier.
- **End of Closure:** For clips where the gate reopens before recording end, unblocking also occurs one tick earlier. The net closed duration difference depends on discrete tick boundaries ($\pm 0.20\,\text{s}$).
- **Clips Terminating While Closed:** If the video terminates while the gate is closed, the advanced start adds $+0.20\,\text{s}$ to `Closed Duration`.
- **Audit Verdict:** **`CONFIRMED_AFFECTED`** (Level 1 / Level 2). Every recorded value in Table 11 is subject to a $\pm 0.20\,\text{s}$ discretization shift under forward-causal stepping.

---

## 8. Clearance-Latency Impact Analysis

### 8.1 Definition & Call Path
Clearance latency measures the duration from train departure ($T_4$) until the barrier unblocks ($\theta > 45.0^\circ$) or reaches fully open ($90.0^\circ$):
$$\text{CL} = t_{\text{unblock}} - T_4$$
- Forward-causal opening delays $t_{\text{unblock}}$ by $+0.20\,\text{s}$.

### 8.2 Historical Empirical Status
- In historical benchmark summaries (`summary.json`), `mean_clearance_latency_s` is recorded as `null`.
- In manuscript Table 3, Clearance Latency is explicitly listed as **`NON-COMPUTABLE`**.
- **Audit Verdict:** **`NO HISTORICAL METRIC CHANGE`** (Level 3 theoretical exposure; zero empirical calculations exist).

---

## 9. Warning Lead-Time Independence Analysis

### 9.1 Verification of Independence
In [`src/railway_detection/simulation/runner.py:235-239`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L235-L239):
```python
if (
    decision.resulting_state == CrossingState.WARNING.value
    and first_warning_time is None
):
    first_warning_time = t
```
And in [`src/railway_detection/evaluation/clock_aware.py:38-48`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/clock_aware.py#L38-L48):
```python
lead = max(0.0, normalize_timestamp(entry_s - first_warning))
```
- `first_warning_time` is stamped directly from `decision.resulting_state == WARNING`.
- State `WARNING` is triggered inside `MultimodalDecisionEngine.evaluate_frame()` based strictly on sensory confirmation frame counts (`consecutive_approach_count >= 2`).
- This evaluation occurs **before** `gate_model.step()` is invoked and does **not** consume `gate_angle_deg`.
- **Audit Verdict:** **`NOT_AFFECTED`** (Level 4). Warning lead time is completely decoupled from gate kinematics and retroactive stepping.

---

## 10. Event-Level Historical Impact Register

The following register audits all 27 events from Table 11 of the historical benchmark:

| Event ID | Cohort | Table 11 Closed Duration | Historical $T_4$ | Historical $M4$ | Historical $M5$ | Potential Timing Exposure | Forward-Causal Verdict | Reason & Evidence Level |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `train_events_001` | Train ($N=23$) | $46.0\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_002` | Train ($N=23$) | $28.8\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_003` | Train ($N=23$) | $29.6\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_004` | Train ($N=23$) | $74.4\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_005` | Train ($N=23$) | $75.8\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_006` | Train ($N=23$) | $122.4\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_007` | Train ($N=23$) | $34.6\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_008` | Train ($N=23$) | $59.0\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_009` | Train ($N=23$) | $39.2\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_010` | Train ($N=23$) | $20.2\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_011` | Train ($N=23$) | $34.0\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_012` | Train ($N=23$) | $71.4\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_013` | Train ($N=23$) | $70.0\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_014` | Train ($N=23$) | $51.2\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_015` | Train ($N=23$) | $27.4\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_016` | Train ($N=23$) | $43.2\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_017` | Train ($N=23$) | $80.0\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_018` | Train ($N=23$) | $55.2\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_019` | Train ($N=23$) | $56.6\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_020` | Train ($N=23$) | $26.2\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_021` | Train ($N=23$) | $57.6\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_022` | Train ($N=23$) | $42.6\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `train_events_023` | Train ($N=23$) | $42.0\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |
| `no_train_events_001` | Negative Control | $18.8\,\text{s}$ | `None` | `N/A` | `N/A` | **YES** | **False alarm duration shifted** | Level 2: Nuisance closure duration shifted |
| `no_train_events_002` | Negative Control | $9.6\,\text{s}$ | `None` | `N/A` | `N/A` | **YES** | **False alarm duration shifted** | Level 2: Nuisance closure duration shifted |
| `no_train_events_003` | Negative Control | $10.6\,\text{s}$ | `None` | `N/A` | `N/A` | **YES** | **False alarm duration shifted** | Level 2: Nuisance closure duration shifted |
| `engine_events_001` | Engine ($N=1$) | $5.0\,\text{s}$ | `None` | `null` | `null` | **YES** | **Closed Duration shifted $\pm 0.2\text{s}$** | Level 2: Duration affected; M4/M5 non-computable |

---

## 11. Forward-Causal Comparison (Convention A vs. Convention B)

| Analysis Dimension | Convention A (Retroactive Interval) | Convention B (Forward-Causal) | Quantitative Difference |
| :--- | :--- | :--- | :---: |
| **1. Affected Time Interval** | Preceding interval $[t - \Delta t, t]$ | Subsequent interval $[t, t + \Delta t]$ | Reversal of actuation direction |
| **2. Gate Angle at Transition Tick** | Arm drops to $84.0^\circ$ at transition tick ($t=2.20\,\text{s}$) | Arm remains at $90.0^\circ$ at transition tick ($t=2.20\,\text{s}$) | $\Delta \theta = 6.0^\circ$ at transition tick |
| **3. First Blocked Timestamp ($\tau$)** | $t = 3.60\,\text{s}$ (at 5 Hz) | $t = 3.80\,\text{s}$ (at 5 Hz) | $+0.20\,\text{s}$ delay to block |
| **4. First Unblocked Timestamp** | Unblocks $\Delta t$ earlier during opening | Unblocks $\Delta t$ later during opening | $+0.20\,\text{s}$ delay to unblock |
| **5. $M4$ (Premature Opening)** | `NON-COMPUTABLE` on real events | `NON-COMPUTABLE` on real events | **Zero change** ($N=0$) |
| **6. $M5$ (`NEVER_PROTECTED_M5`)** | `NON-COMPUTABLE` on real events | `NON-COMPUTABLE` on real events | **Zero change** ($N=0$) |
| **7. Closed Duration** | Stamped on retroactively closed angles | Stamped on forward-causal angles | Shift of $\pm 0.20\,\text{s}$ per episode |
| **8. Clearance Latency** | `NON-COMPUTABLE` on real events | `NON-COMPUTABLE` on real events | **Zero change** ($N=0$) |

---

## 12. Historical Claim Exposure Register

| Historical Claim Description | Document & Location | Source Result | Audit Evidence & Exposure | Recommended Disposition |
| :--- | :--- | :---: | :--- | :--- |
| **"First-block latency is 3.6 s at both tick sizes"** | `docs/generated/mission_5a/EXPERIMENT_DESIGN_RECONCILIATION_20261101_M5A.md:28` | Synthetic run | **INVALIDATED.** Parity is an artifact of retroactive stepping and IEEE 754 float overshoot. Causal latency is 3.80 s at 5 Hz. | **`INVALIDATED_BY_DIRECT_EVIDENCE`** |
| **"Kinematic minimum barrier descent time of approx 3.60 s"** | `docs/generated/master_reaudit/MTR_PROVENANCE_CHALLENGE_AUDIT.md:235` | Narrative proposal | **OVERCLAIM.** Threshold is a discrete simulation artifact, not an AREMA physical standard. | **`REQUIRES_QUALIFICATION`** |
| **Table 11 Closed Duration figures (e.g. 46.0s, 28.8s)** | `results/experiments/tables/table11_per_event_summary.md` | Empirical run | **AFFECTED.** Numbers incorporate retroactive interval stepping ($\pm 0.20\,\text{s}$). | **`POTENTIALLY_INVALIDATED`** |
| **Premature-Opening Rate is 0%** | Informal historical developer summaries | Assumption | **MISATTRIBUTED.** M4 was non-computable (`evaluable_count = 0`), not a measured 0% failure rate. | **`REQUIRES_QUALIFICATION`** |
| **Warning Lead Time Distribution** | Table 3, manuscript draft | Diagnostic | **UNAFFECTED.** Warning state is recorded from sensory evidence before gate stepping. | **`SUPPORTED_UNDER_LEGACY_CONVENTION`** |

---

## 13. Test Coverage and Gaps

Audit of the test suites ([`test_mission5a1_audit_regressions.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_mission5a1_audit_regressions.py), [`test_phase3_sensor_health_decision_policy.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_phase3_sensor_health_decision_policy.py)) identifies critical verification gaps:

### Missing Test Cases (Proposals Only):
1. **`test_simulation_actuator_causality_zero_retroactive_displacement`:** Verify that when a command changes at timestamp $t_k$, the displacement across $[t_{k-1}, t_k]$ is strictly computed from $u(t_{k-1})$, and $u(t_k)$ produces zero displacement before $t_k$.
2. **`test_m4_clearance_boundary_causal_invariance`:** Verify that synthetic test cases with $T_4$ falling inside $[t_{\text{unblock}} - \Delta t, t_{\text{unblock}}]$ do not trigger spurious premature opening violations under forward-causal stepping.
3. **`test_closed_duration_interval_continuity`:** Verify that closed duration accumulation correctly accounts for interval boundaries under non-uniform frame cadences.

---

## 14. Confirmed vs. Potential Impact Summary

| Evidence Level | Classification Criteria | Affected Historical Artifacts & Metrics |
| :--- | :--- | :--- |
| **LEVEL 1 — CONFIRMED CHANGE** | Safe evidence proves historical result changes. | • `derive_min_block_latency_s()` threshold shifted from $3.80\,\text{s}$ (causal 5 Hz) to $3.60\,\text{s}$.<br>• 3.60 s tick invariance claim disproven. |
| **LEVEL 2 — CONFIRMED EXPOSURE** | Result depends on affected boundary; exact delta subject to recomputation. | • Table 11 `Closed Duration` for all 27 events (shifted by $\pm 0.20\,\text{s}$). |
| **LEVEL 3 — THEORETICAL EXPOSURE** | Implementation could affect metric, but no real-data result existed historically. | • $M4$ (Premature Opening): non-computable historically ($N=0$).<br>• $M5$ (`NEVER_PROTECTED_M5`): non-computable historically ($N=0$).<br>• Clearance Latency: non-computable historically ($N=0$). |
| **LEVEL 4 — NO IDENTIFIED DEPENDENCY** | Metric is provably independent of gate kinematics. | • Warning Lead Time (WLT): stamped prior to gate stepping. |

---

## 15. Researcher Decision Register

The following formal decisions are submitted for Principal Investigator adjudication:

1. **`DEC-C21` (Table 11 Closed Duration Historical Qualification):**  
   Append an explanatory note to Table 11 in `docs/` and archive reports stating that reported closed durations reflect Convention A (retroactive interval stepping) with a discrete quantization uncertainty of $\pm 0.20\,\text{s}$.
2. **`DEC-C22` (M4/M5 Non-Computability Formal Confirmation):**  
   Formally ratify that historical benchmark runs had zero evaluable events for $M4$ and $M5$ due to unpopulated $T_4$, confirming that retroactive stepping caused zero empirical metric changes on real data.
3. **`DEC-C23` (Simulation Runner Versioning Roadmap):**  
   Maintain Convention A for Version 1.x descriptive benchmarks to preserve reproducibility of existing baseline runs, while establishing Convention B (Strict Forward-Causal) as the required architecture for Version 2.0.
4. **`DEC-C24` (Screening Threshold Deprecation):**  
   Deprecate the narrative claim that 3.60 s is a physical railway constant, qualifying it as an implementation-derived discrete simulation quantity.

---

## 16. Limitations and Unresolved Questions

1. **Real-Data Recomputation Prohibited:** Under strict safety restrictions, no real-data simulation reruns were performed. Quantifying the exact millisecond shifts for Table 11 closed durations requires an authorized offline re-run once Stage-2.1 is promoted.
2. **Back-Camera $T_4$ Dependency:** Complete evaluation of $M4$ and $M5$ on real events remains strictly blocked until human review and promotion of rear-camera Stage-2.1 ground truth is authorized by the researcher.

---

## 17. Final Statutory Disposition

$$\mathbf{HISTORICAL\_METRICS\_PARTIALLY\_AFFECTED}$$

### Formal Justification:
1. **Partially Affected Confirmed:**  
   Historical metrics are **partially affected**:
   - `Closed Duration` in Table 11 (27 events) and the synthetic lead-in derivation threshold are **confirmed affected** (Level 1 / Level 2) by retroactive interval stepping.
   - Conversely, primary safety metrics $M4$ (Premature Opening) and $M5$ (`NEVER_PROTECTED_M5`) have **zero empirical changes on real data**, because neither metric was ever computed historically ($T_4 = \text{null}$, evaluable count = 0).
   - Warning Lead Time is **completely unaffected** (Level 4), being stamped prior to actuator integration.

---

REAL-DATA EXECUTION: NOT AUTHORIZED.
