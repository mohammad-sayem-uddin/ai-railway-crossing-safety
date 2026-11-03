# MISSION 16A-MTR-ARITHMETIC-AND-CENSORING-RECHALLENGE: INDEPENDENT CONTROLLER TIMING, SIMULATION SEMANTICS, AND CENSORING AUDIT

**Project:** Train Gate Automation — Bangladesh  
**Audit Mission:** Master Mission 16A — Rechallenge Audit  
**Auditor:** Independent Principal Temporal-Measurement Auditor, Simulation-Semantics Reviewer, and Railway-Safety Research Methodologist  
**Audit Target:** Controller Call Sequence, Discrete Simulation Timing, 3.6-Second Parity Provenance, Left-Censoring Semantics, and Missed-Train ($\text{MTR}$) Denominator Validity  
**Historical Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Execution Authority:** NONE  
**Research Authorization:** NONE  
**Audit Mode:** Strict read-only, synthetic-only, metadata-only, evidence-based  

---

## 1. Executive Summary

This independent rechallenge audit conducts an exhaustive, source-level mathematical and execution trace of the Missed-Train Lead-In Feasibility Screen ($\text{MTR}$), the simulated barrier actuator controller, and the temporal left-censoring conventions across the Train Gate Automation codebase.

### Primary Audit Findings:
1. **Mathematical Divergence in Continuous Theoretical Latency:**
   In pure continuous time, the theoretical minimum latency required to detect a train and lower the barrier arm to $45.0^\circ$ differs by cadence:
   $$\tau_{\text{continuous}}(10\,\text{Hz}) = 0.10\,\text{s} + 2.00\,\text{s} + 1.50\,\text{s} = \mathbf{3.60\,\text{s}}$$
   $$\tau_{\text{continuous}}(5\,\text{Hz}) = 0.20\,\text{s} + 2.00\,\text{s} + 1.50\,\text{s} = \mathbf{3.70\,\text{s}}$$
2. **Simulation Parity at 3.60 s is an Artifact of Two Compensating Implementation Effects:**
   The empirical observation that both 5 Hz and 10 Hz simulations report $\tau_{\text{discrete}} = 3.60\,\text{s}$ from [`derive_min_block_latency_s()`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/lead_in_screen.py#L159-L226) is **not** a fundamental physical invariant. It is a mathematical coincidence arising from:
   - **Retroactive Interval Actuation in [`EventSimulationRunner._run_frames()`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L49-L85):** The runner evaluates the decision engine before stepping the gate model, immediately applying the newly commanded `CLOSING` state across the past interval $[t - \Delta t, t]$. This effectively accelerates barrier motion by $\Delta t$, shifting continuous arrival from $3.70\,\text{s}$ to $3.50\,\text{s}$ at 5 Hz, which discretizes onto the next sample grid at $t = 3.60\,\text{s}$.
   - **Floating-Point Roundoff at 10 Hz:** At 10 Hz, the same retroactive stepping reaches the $45.0^\circ$ boundary at $t = 3.50\,\text{s}$. However, cumulative IEEE 754 floating-point arithmetic calculates the arm angle at $t = 3.50\,\text{s}$ as $45.00000000000004^\circ$. Because `is_passage_blocked` requires `angle <= 45.0`, the blocked state evaluates to `False` at $t = 3.50\,\text{s}$ by $4 \times 10^{-14}$ degrees, forcing the simulator to wait until tick $t = 3.60\,\text{s}$ ($42.0^\circ$) to declare blockage.
3. **Left-Censoring Semantics ($T_0 \le 0.0\,\text{s}$):**
   In 20 of 23 candidate train events, setting $T_0 = 0.0\,\text{s}$ reflects video recording onset, not physical train arrival. Consequently, $T_1 - 0.0$ measures **available recording pre-roll duration**, not physical train approach lead time.
4. **Reclassification of the 21/22 Screen Failures:**
   The historical claim that 21 of 22 events "failed the feasibility screen" conflates two distinct cohorts:
   - **18 events** are `RECORDING_TRUNCATED_LEAD_IN` ($T_0 \le 0.0\,\text{s}$, $T_1 \le 3.20\,\text{s}$), where the true physical approach is unobservable and pre-roll was truncated.
   - **3 events** (`event_009`, `event_015`, `event_016`) are `PHYSICAL_SHORT_LEAD_IN`, where visual emergence is fully observed at $T_0 = 1.50\,\text{s}$ and danger-zone entry occurs at $T_1 = 4.20\,\text{s}$, giving a true physical visual lead-in of $2.70\,\text{s} < 3.60\,\text{s}$.
5. **Degeneracy of the $N = 1$ Denominator:**
   Only `event_001` passes the lead-in screen ($T_1 = 5.80\,\text{s}$), solely because the videographer started recording earlier. A sample size of $N = 1$ is statistically meaningless for empirical rate estimation. Scientifically, $\text{MTR}$ must be classified as **`NOT_ESTIMABLE`** on this dataset.

---

## 2. Exact Controller Call Sequence

In [`src/railway_detection/simulation/runner.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L49-L105), the simulation loop processes sequential multimodal frames as follows:

```python
for frame in sorted_frames:
    t = frame.master_timestamp_s
    dt = max(0.0, t - prev_t)

    # 1. State Machine / Decision Evaluation
    decision = stage(
        "decision_evaluation",
        lambda frame=frame: self.decision_engine.evaluate_frame(
            frame, scenario_run_id=f"{event_id}_{scenario_name}"
        ),
    )

    # 2. Gate Command Extraction
    commanded_gate = GateState(decision.resulting_gate_state)

    # 3. Gate Kinematics Update
    angle = stage(
        "gate_model_step",
        lambda dt=dt, commanded_gate=commanded_gate: self.gate_model.step(
            dt, commanded_gate
        ),
    )

    # 4. Simulation Step Recording
    stage(
        "step_recording",
        lambda t=t, decision=decision, angle=angle: steps.append(
            SimulationStep(
                timestamp_s=t,
                crossing_state=decision.resulting_state,
                gate_state=self.gate_model.current_state.value,
                gate_angle_deg=angle,
                is_passage_blocked=self.gate_model.is_passage_blocked,
                decision=decision,
            )
        ),
    )
    prev_t = t
```

### Call Ordering and Execution Semantics:
1. **Dwell Evaluation precedes Gate Model Stepping:** In [`MultimodalDecisionEngine.evaluate_frame()`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/decision_engine.py), the dwell condition `elapsed = t - self.state_entry_time_s >= self.warning_dwell_s` is evaluated before any gate model logic runs.
2. **Gate Angle Update Occurs on the Same Tick as the State Transition:** When the state transitions from `WARNING` to `GATE_CLOSING` at timestamp $t$, `decision.resulting_gate_state` is set to `CLOSING` on that exact tick.
3. **Retroactive Interval Application:** In `gate_model.step(dt, commanded_gate)`, `dt = t - prev_t` represents the time elapsed *since the last frame*. Because `commanded_gate` is the *newly transitioned* state (`CLOSING`), the actuator model applies the closing rate ($30^\circ/\text{s}$) over the interval $[t - \Delta t, t]$ that has already passed.
4. **Blocked Status is Checked After the Update:** In `SimulationStep`, `self.gate_model.is_passage_blocked` is evaluated immediately after `gate_model.step()` mutates `current_angle_deg`.

---

## 3. 5 Hz Timing Trace ($\Delta t = 0.20\,\text{s}$)

Below is the exact step-by-step trace from $t = 0.00\,\text{s}$ through $t = 4.00\,\text{s}$ under the frozen configuration (`confirm_frames = 2`, `warning_dwell_s = 2.0`, `closing_duration_s = 3.0`):

| Step | Simulation Time ($t$) | Controller State | Confirm Count | Gate Angle Before | Gate Angle After | Blocked Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | $0.00\,\text{s}$ | `TRAIN_APPROACHING` | 1 | $90.00^\circ$ | $90.00^\circ$ | `False` |
| **1** | $0.20\,\text{s}$ | `WARNING` | 2 | $90.00^\circ$ | $90.00^\circ$ | `False` |
| **2** | $0.40\,\text{s}$ | `WARNING` | 2 | $90.00^\circ$ | $90.00^\circ$ | `False` |
| **3** | $0.60\,\text{s}$ | `WARNING` | 2 | $90.00^\circ$ | $90.00^\circ$ | `False` |
| **4** | $0.80\,\text{s}$ | `WARNING` | 2 | $90.00^\circ$ | $90.00^\circ$ | `False` |
| **5** | $1.00\,\text{s}$ | `WARNING` | 2 | $90.00^\circ$ | $90.00^\circ$ | `False` |
| **6** | $1.20\,\text{s}$ | `WARNING` | 2 | $90.00^\circ$ | $90.00^\circ$ | `False` |
| **7** | $1.40\,\text{s}$ | `WARNING` | 2 | $90.00^\circ$ | $90.00^\circ$ | `False` |
| **8** | $1.60\,\text{s}$ | `WARNING` | 2 | $90.00^\circ$ | $90.00^\circ$ | `False` |
| **9** | $1.80\,\text{s}$ | `WARNING` | 2 | $90.00^\circ$ | $90.00^\circ$ | `False` |
| **10** | $2.00\,\text{s}$ | `WARNING` | 2 | $90.00^\circ$ | $90.00^\circ$ | `False` |
| **11** | $2.20\,\text{s}$ | `GATE_CLOSING` | 2 | $90.00^\circ$ | $\mathbf{84.00^\circ}$ | `False` |
| **12** | $2.40\,\text{s}$ | `GATE_CLOSING` | 2 | $84.00^\circ$ | $78.00^\circ$ | `False` |
| **13** | $2.60\,\text{s}$ | `GATE_CLOSING` | 2 | $78.00^\circ$ | $72.00^\circ$ | `False` |
| **14** | $2.80\,\text{s}$ | `GATE_CLOSING` | 2 | $72.00^\circ$ | $66.00^\circ$ | `False` |
| **15** | $3.00\,\text{s}$ | `GATE_CLOSING` | 2 | $66.00^\circ$ | $60.00^\circ$ | `False` |
| **16** | $3.20\,\text{s}$ | `GATE_CLOSING` | 2 | $60.00^\circ$ | $54.00^\circ$ | `False` |
| **17** | $3.40\,\text{s}$ | `GATE_CLOSING` | 2 | $54.00^\circ$ | $48.00^\circ$ | `False` |
| **18** | $\mathbf{3.60\,\text{s}}$ | `GATE_CLOSING` | 2 | $48.00^\circ$ | $\mathbf{42.00^\circ}$ | $\mathbf{True}$ |
| **19** | $3.80\,\text{s}$ | `GATE_CLOSING` | 2 | $42.00^\circ$ | $36.00^\circ$ | `True` |
| **20** | $4.00\,\text{s}$ | `GATE_CLOSING` | 2 | $36.00^\circ$ | $30.00^\circ$ | `True` |

---

## 4. 10 Hz Timing Trace ($\Delta t = 0.10\,\text{s}$)

Below is the exact step-by-step trace from $t = 0.00\,\text{s}$ through $t = 4.00\,\text{s}$ under 10 Hz simulation:

| Step | Simulation Time ($t$) | Controller State | Confirm Count | Gate Angle Before | Gate Angle After | Blocked Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | $0.00\,\text{s}$ | `TRAIN_APPROACHING` | 1 | $90.00^\circ$ | $90.00^\circ$ | `False` |
| **1** | $0.10\,\text{s}$ | `WARNING` | 2 | $90.00^\circ$ | $90.00^\circ$ | `False` |
| **2–20** | $0.20\dots 2.00\,\text{s}$ | `WARNING` | 2 | $90.00^\circ$ | $90.00^\circ$ | `False` |
| **21** | $2.10\,\text{s}$ | `GATE_CLOSING` | 2 | $90.00^\circ$ | $\mathbf{87.00^\circ}$ | `False` |
| **22** | $2.20\,\text{s}$ | `GATE_CLOSING` | 2 | $87.00^\circ$ | $84.00^\circ$ | `False` |
| **23** | $2.30\,\text{s}$ | `GATE_CLOSING` | 2 | $84.00^\circ$ | $81.00^\circ$ | `False` |
| **24** | $2.40\,\text{s}$ | `GATE_CLOSING` | 2 | $81.00^\circ$ | $78.00^\circ$ | `False` |
| **25** | $2.50\,\text{s}$ | `GATE_CLOSING` | 2 | $78.00^\circ$ | $75.00^\circ$ | `False` |
| **26** | $2.60\,\text{s}$ | `GATE_CLOSING` | 2 | $75.00^\circ$ | $72.00^\circ$ | `False` |
| **27** | $2.70\,\text{s}$ | `GATE_CLOSING` | 2 | $72.00^\circ$ | $69.00^\circ$ | `False` |
| **28** | $2.80\,\text{s}$ | `GATE_CLOSING` | 2 | $69.00^\circ$ | $66.00^\circ$ | `False` |
| **29** | $2.90\,\text{s}$ | `GATE_CLOSING` | 2 | $66.00^\circ$ | $63.00^\circ$ | `False` |
| **30** | $3.00\,\text{s}$ | `GATE_CLOSING` | 2 | $63.00^\circ$ | $60.00^\circ$ | `False` |
| **31** | $3.10\,\text{s}$ | `GATE_CLOSING` | 2 | $60.00^\circ$ | $57.00^\circ$ | `False` |
| **32** | $3.20\,\text{s}$ | `GATE_CLOSING` | 2 | $57.00^\circ$ | $54.00^\circ$ | `False` |
| **33** | $3.30\,\text{s}$ | `GATE_CLOSING` | 2 | $54.00^\circ$ | $51.00^\circ$ | `False` |
| **34** | $3.40\,\text{s}$ | `GATE_CLOSING` | 2 | $51.00^\circ$ | $48.00000000000004^\circ$ | `False` |
| **35** | $3.50\,\text{s}$ | `GATE_CLOSING` | 2 | $48.00000000000004^\circ$ | $\mathbf{45.00000000000004^\circ}$ | $\mathbf{False}$ *(Float overshoot)* |
| **36** | $\mathbf{3.60\,\text{s}}$ | `GATE_CLOSING` | 2 | $45.00000000000004^\circ$ | $\mathbf{42.00000000000004^\circ}$ | $\mathbf{True}$ |
| **37** | $3.70\,\text{s}$ | `GATE_CLOSING` | 2 | $42.00000000000004^\circ$ | $39.00000000000004^\circ$ | `True` |
| **38** | $3.80\,\text{s}$ | `GATE_CLOSING` | 2 | $39.00000000000004^\circ$ | $36.00000000000004^\circ$ | `True` |
| **39** | $3.90\,\text{s}$ | `GATE_CLOSING` | 2 | $36.00000000000004^\circ$ | $33.00000000000004^\circ$ | `True` |
| **40** | $4.00\,\text{s}$ | `GATE_CLOSING` | 2 | $33.00000000000004^\circ$ | $30.00000000000004^\circ$ | `True` |

---

## 5. Independent Arithmetic Reconstruction & Discrepancy Analysis

### 5.1 Arithmetic Comparison Across Modalities

| Timing Component | Theoretical Continuous (10 Hz) | Causal Forward Discrete (10 Hz) | Actual Simulation Runner (10 Hz) | Theoretical Continuous (5 Hz) | Causal Forward Discrete (5 Hz) | Actual Simulation Runner (5 Hz) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Confirmation Delay** | $0.10\,\text{s}$ | $0.10\,\text{s}$ | $0.10\,\text{s}$ | $0.20\,\text{s}$ | $0.20\,\text{s}$ | $0.20\,\text{s}$ |
| **Warning Dwell** | $2.00\,\text{s}$ | $2.00\,\text{s}$ | $2.00\,\text{s}$ | $2.00\,\text{s}$ | $2.00\,\text{s}$ | $2.00\,\text{s}$ |
| **Descent to $45.0^\circ$** | $1.50\,\text{s}$ | $1.50\,\text{s}$ | $1.40\,\text{s}$ *(retroactive)* | $1.50\,\text{s}$ | $1.60\,\text{s}$ *(next tick)* | $1.40\,\text{s}$ *(retroactive)* |
| **Float Boundary Error** | None | None | $+0.10\,\text{s}$ ($+4\times 10^{-14}$) | None | None | None |
| **Resulting Latency** | $\mathbf{3.60\,\text{s}}$ | $\mathbf{3.60\,\text{s}}$ | $\mathbf{3.60\,\text{s}}$ | $\mathbf{3.70\,\text{s}}$ | $\mathbf{3.80\,\text{s}}$ | $\mathbf{3.60\,\text{s}}$ |

### 5.2 Resolution of the 3.6-Second Parity Paradox
Why did previous audits report that 5 Hz and 10 Hz produced identical 3.60 s results?
1. **The 5 Hz Derivation:**
   In causal continuous time, 5 Hz requires $0.20 + 2.00 + 1.50 = 3.70\,\text{s}$. If discretized strictly forward in time, the arm reaches $48^\circ$ at $t = 3.60\,\text{s}$ and triggers blockage at the next sample tick $t = 3.80\,\text{s}$. However, because [`EventSimulationRunner`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py) steps the actuator retroactively across the interval $[2.00, 2.20]$, the arm already has $6^\circ$ of descent at $t = 2.20\,\text{s}$. Continuous descent crosses $45^\circ$ at $t = 3.50\,\text{s}$. The next available 5 Hz sample tick is $t = 3.60\,\text{s}$ (where angle is $42.0^\circ$), yielding $\mathbf{3.60\,\text{s}}$.
2. **The 10 Hz Derivation:**
   At 10 Hz, the same retroactive stepping advances descent so that continuous crossing reaches $45.0^\circ$ exactly at $t = 3.50\,\text{s}$. In exact mathematics, the 10 Hz runner would have reported $\mathbf{3.50\,\text{s}}$. However, IEEE 754 floating-point accumulation leaves `angle = 45.00000000000004` at $t = 3.50\,\text{s}$. Since $45.00000000000004 \le 45.0$ is `False`, the simulator misses the $t = 3.50\,\text{s}$ detection and reports the next tick at $t = \mathbf{3.60\,\text{s}}$.
3. **Formal Threshold Classification:**
   The threshold is strictly **`IMPLEMENTATION_DERIVED`** and **`SIMULATION_DISCRETIZATION_SENSITIVE`**. Sweeping other tick sizes proves it is not invariant:
   $$\Delta t = 0.50\,\text{s} \to 3.50\,\text{s} \quad\mid\quad \Delta t = 0.25\,\text{s} \to 3.50\,\text{s} \quad\mid\quad \Delta t = 0.20\,\text{s} \to 3.60\,\text{s}$$
   $$\Delta t = 0.10\,\text{s} \to 3.60\,\text{s} \quad\mid\quad \Delta t = 0.05\,\text{s} \to 3.55\,\text{s}$$

---

## 6. Left-Censoring Semantic Analysis

### 6.1 Distinction Between Physical Reality and Clip Recording
In temporal event analysis, four boundaries must be kept distinct:
1. **Actual Physical Approach Start ($T_{\text{phys}}$):** The physical instant when the locomotive begins its approach or enters the sightline of the grade crossing. For clips where the train was already in motion before filming, $T_{\text{phys}} < 0.0\,\text{s}$ (unknown and unmeasured).
2. **Recording Start ($t_{\text{rec}} = 0.0\,\text{s}$):** The arbitrary timestamp of Frame 0 in the recorded media file.
3. **First Visible Appearance ($T_0$):** The timestamp within the video where the locomotive becomes visually observable. When the train is already visible in Frame 0, the annotator assigns $T_0 = 0.0\,\text{s}$.
4. **Danger-Zone Entry ($T_1$):** The timestamp where the locomotive nose crosses the roadway entry / frog line.

### 6.2 Semantics of Assigning $T_0 = 0.0\,\text{s}$
Assigning $T_0 = 0.0\,\text{s}$ represents an **operational recording-onset reference**, NOT a measured physical arrival.
- **What $T_1 - 0.0$ Measures:** The available duration of pre-danger-zone video footage captured by the camera operator.
- **Mathematical Relation:** Because $T_{\text{phys}} \le 0.0\,\text{s}$, the quantity $T_1 - 0.0$ is a **mathematical lower bound** on the true physical lead time:
  $$\Delta t_{\text{physical}} = T_1 - T_{\text{phys}} \ge T_1 - 0.0$$
- **What CANNOT Be Inferred:**
  - One cannot infer that the train approached with less than 3.6 seconds of physical warning.
  - One cannot infer that the crossing geometry or train velocity makes automated protection impossible.
  - One cannot infer that the computer vision detector or fusion algorithm "failed" to detect the train.

### 6.3 Exhaustive Event Categorization (23 Candidate Train Events)

| Category | Definition | Event Count | Event Identifiers | Evaluability Status |
| :--- | :--- | :---: | :--- | :--- |
| **1. Uncensored Observable $T_0$** | Locomotive visual emergence observed at $t > 0$. | **3** | `event_009`, `event_015`, `event_016` ($T_0 = 1.50\,\text{s}$) | Evaluable lead-in ($2.70\,\text{s}$); physically insufficient for 3.6 s barrier |
| **2. Left-Censored $T_0$, Observable $T_1$** | Locomotive present in Frame 0 ($T_0 = 0.0\,\text{s}$); $T_1$ observed. | **19** | `event_001` ($T_1 = 5.8\,\text{s}$),<br>`002`–`004`, `006`–`008`, `010`–`014`, `017`–`023` ($T_1 \le 3.2\,\text{s}$) | Pre-roll truncated; physical lead-in unobservable |
| **3. Left-Censored $T_0$, Unobservable $T_1$** | Train already spanning crossing in Frame 0; locomotive past $T_1$. | **1** | `event_005` ($T_0 = 0.0\,\text{s}$, $T_1 = \text{None}$) | Excluded from all lead-in evaluations |
| **4. Missing / Uncertain $T_0$** | Unannotated or ambiguous arrival. | **0** | None (all active candidate proposals populated) | N/A |

---

## 7. Reclassification of Screen Outcomes

Under the operational implementation of [`screen_missed_train_lead_in()`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/lead_in_screen.py#L81-L156):
- When $T_0$ is left-censored, the function sets `start = 0.0` (basis `"replay_start_left_censored"`).
- If $T_1 - 0.0 < 3.60\,\text{s}$, it assigns `outcome = SCREEN_INSUFFICIENT_LEAD_IN`.

### Reclassification of the "21/22" Result:
The aggregate count of 21 events failing the screen is composed of two fundamentally different physical phenomena:
1. **`RECORDING_TRUNCATED_LEAD_IN` (18 events):**
   Events `002, 003, 004, 006, 007, 008, 010, 011, 012, 013, 014, 017, 018, 019, 020, 021, 022, 023`.
   These events fail solely because the video recording began less than 3.2 seconds before the train entered the frog line. The physical lead time is unknown.
2. **`PHYSICAL_SHORT_LEAD_IN` (3 events):**
   Events `009, 015, 016`.
   These events have verified, uncensored optical emergence at $T_0 = 1.50\,\text{s}$ and danger-zone entry at $T_1 = 4.20\,\text{s}$. The true physical visual lead-in is $2.70\,\text{s}$, which is physically shorter than the $3.60\,\text{s}$ barrier closing latency.
3. **`RECORDING_SUFFICIENT_LEAD_IN` (1 event):**
   `event_001` ($T_0 = 0.0\,\text{s}$, $T_1 = 5.80\,\text{s}$). Available recorded lead-in is $5.80\,\text{s} \ge 3.60\,\text{s}$.

### Assessment of Classification Alternatives:

| Classification Scheme | Handling of Left-Censored Events | Resulting Evaluable Denominator ($N$) | Scientific Defensibility |
| :--- | :--- | :---: | :--- |
| **Option A: Current Code Convention** | Treat $T_1 - 0.0 < 3.6\,\text{s}$ as `INSUFFICIENT_LEAD_IN`. | $N = 1$ (`event_001`) | **Weak.** Equates video clip truncation with operational railway infeasibility. |
| **Option B: Strict Censoring Pruning** | Classify left-censored events as `UNVERIFIABLE_LEAD_IN` and prune from screen. | $N = 0$ (all 3 uncensored events fail $2.7 < 3.6$) | **Coherent.** Explicitly recognizes that physical lead-in is unmeasured in censored clips. |
| **Option C: Explicit Split Classification** | Partition screen outcomes into `TRUNCATED_RECORDING` vs. `PHYSICAL_SHORT_LEAD_IN`. | $N = 1$ (recorded) / $N = 0$ (physical) | **Strongest.** Fully discloses the provenance of clip duration versus train dynamics. |

---

## 8. $\text{MTR}$ Denominator Implications & Scientific Validity

### 8.1 Why `event_001` Alone Passes
`event_001` is identical in structure to the other 19 left-censored events: the locomotive is already visible in the distance under the metro flyover at Frame 0 ($t = 0.00\,\text{s}$). It passes the screen solely because the videographer began recording 5.80 seconds before the train reached the frog line, whereas other clips began 2.1 to 3.2 seconds before the frog line.

### 8.2 Scientific Invalidity of an $N = 1$ Metric
In scientific publications, reporting a statistical rate (such as Missed-Train Rate $\text{MTR} = \text{Misses} / N$) over an evaluable denominator of $N = 1$ is degenerate:
- An empirical rate of $0/1 = 0\%$ or $1/1 = 100\%$ provides zero statistical confidence.
- The standard binomial confidence interval for $N = 1$ spans $[0.00, 0.975]$ (Clopper-Pearson $95\%$).
- Concluding that an automated crossing system has a validated Missed-Train Rate based on a single video clip violates experimental design standards.

### 8.3 Recommended Disposition
The manuscript and project documentation must formally state:
$$\mathbf{MTR\text{ is NOT ESTIMABLE on the Current Dataset.}}$$
Primary safety verification must be grounded strictly on **$M4$ (Premature Opening)** and **$M5$ (Never Protected Before $T_4$)**, which evaluate the full consist traversal over $[t_{\text{blocked}}, T_4)$ and are completely unaffected by pre-arrival lead-in truncation.

---

## 9. Manuscript Wording Review & Proposed Revision

### 9.1 Review of Previously Proposed Section 6.2 Text
The draft proposed in prior audit missions stated:
> *"Given the system's kinematic minimum barrier descent time of approximately 3.60 s (comprising 2 confirmation ticks at 5 Hz, 2.0s flasher warning dwell, and barrier descent at 30°/s to 45°), 21 of the 22 observable events provide insufficient physical lead time for the barrier to block passage prior to T1."*

**Critical Audit Deficiencies in Prior Text:**
1. **Overclaims Physical Infeasibility:** It claims that 21 events provide "insufficient physical lead time". In reality, 18 of those events had unknown physical lead times because the video clip was truncated.
2. **Conflates Continuous and Discrete Physics:** It presents 3.60 s as a direct continuous sum ($0.2 + 2.0 + 1.5$), which arithmetically equals $3.70\,\text{s}$, masking the simulation stepping and discretization effects.
3. **Legitimizes $N = 1$ Reporting:** It suggests reporting missed-train rates with disclosure of $N=1$, rather than acknowledging that the metric is fundamentally unestimable.

### 9.2 Safer Proposed Revision for Manuscript Section 6.2 (PROPOSED ONLY)

> [!TIP]
> **Proposed Replacement Text for Section 6.2 of `docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`:**
> *"Evaluation of approach detection latency and conventional missed-train rates ($\text{MTR}$) is fundamentally constrained by recording-onset left-censoring across the dataset. In 20 of the 23 train events, the approaching locomotive is already present within the camera field of view at Frame 0 ($T_0 \le 0.00\,\text{s}$). In 18 of the 22 events with observable roadway entry ($T_1$), the duration of recorded pre-entry footage is $T_1 \le 3.20\,\text{s}$. In the remaining 3 events with observable emergence ($T_0 = 1.50\,\text{s}, T_1 = 4.20\,\text{s}$), the visual lead-in duration is $2.70\,\text{s}$.*
> 
> *Under the simulated controller policy, the minimum latency to confirm detection, execute a 2.0 s flasher dwell, and lower the barrier arm to $45.0^\circ$ at $30^\circ/\text{s}$ requires $3.70\,\text{s}$ in continuous time ($3.60\,\text{s}$ under 5 Hz discrete runner stepping). Because 21 of the 22 events offer less than $3.60\,\text{s}$ of recorded pre-entry observation, attributing unblocked barrier states at $T_1$ to algorithmic detection failure would confound clip truncation with software performance. Furthermore, because only a single event (`event_001`, $T_1 = 5.80\,\text{s}$) provides sufficient pre-entry footage, Missed-Train Rate cannot be estimated with statistical validity ($N \le 1$). Consequently, Missed-Train Rate is reported as unestimable on this dataset, and safety evaluation is grounded on continuous crossing protection metrics ($M4$ Premature Opening and $M5$ Consist Non-Protection) across the full consist traversal."*

---

## 10. Unresolved Issues Requiring Researcher Decisions

The following mandatory decisions are registered for formal researcher resolution prior to benchmark publication:

1. **`DEC-C14` (MTR Estimability Disposition):**  
   Formally approve the disposition that Missed-Train Rate ($\text{MTR}$) is **`NOT_ESTIMABLE`** on the 23-event dataset due to clip truncation, prohibiting the publication of degenerate $N=1$ percentage figures.
2. **`DEC-C15` (Censoring Taxonomy in Stage-2.1 Schema):**  
   Update the proposal taxonomy to formally distinguish `RECORDING_TRUNCATED_LEAD_IN` (pre-roll truncated) from `PHYSICAL_SHORT_LEAD_IN` (observed emergence with short clearance) to prevent misinterpreting videography limits as crossing safety defects.
3. **`DEC-C16` (Simulation Stepping Causality Convention):**  
   Document in `docs/` that `EventSimulationRunner` operates under a *retroactive interval update* convention, where gate actuation begins during the interval $[t - \Delta t, t]$ that satisfied the transition condition, or refactor to strict forward-causal stepping in a future major version.

---

## 11. Git and Safety Preservation Statement

- **Historical Git Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
- **Working Tree Integrity:** Exactly 25 modified tracked files preserved; zero files staged; 388 untracked porcelain files preserved.
- **Protected Data Boundary:** Zero raw video (`.mov`, `.mp4`) or audio (`.wav`) files opened, previewed, decoded, or hashed. Zero production checkpoints (`best.pt`) accessed. Zero real-data evaluations executed.

---

## 12. Final Statutory Disposition

$$\mathbf{MTR\_TIMING\_AND\_CENSORING\_CONTRADICTIONS\_FOUND}$$

### Formal Justification:
1. **Mathematical Contradiction:** Stated component arithmetic ($0.2 + 2.0 + 1.5 = 3.7\,\text{s}$) contradicts the continuous theoretical interpretation of the 3.60 s threshold at 5 Hz.
2. **Implementation Artifact:** The 3.60 s parity between 5 Hz and 10 Hz is demonstrated to be an artifact of retroactive interval stepping and floating-point overshoot, rather than an invariant physical constant.
3. **Semantic Conflation:** Assigning $T_0 = 0.0\,\text{s}$ conflates recording onset with physical arrival, causing 18 recording-truncated events to be misclassified as controller-infeasible short lead-in events.
4. **Denominator Degeneracy:** Reporting $\text{MTR}$ over $N = 1$ is scientifically invalid and must be replaced with an unestimable disposition.

---

REAL-DATA EXECUTION: NOT AUTHORIZED.
