# MISSION 16A-SIMULATION-CAUSALITY-AUDIT: INDEPENDENT SIMULATION TIMING, CAUSALITY AND METRIC-IMPACT AUDIT

**Project:** Train Gate Automation — Bangladesh  
**Audit Mission:** Master Mission 16A — Simulation Causality Challenge Audit  
**Auditor:** Independent Simulation-Systems Auditor, Temporal-Semantics Researcher, Software Verification Engineer, and Railway-Safety Methodology Reviewer  
**Audit Target:** `EventSimulationRunner`, Temporal Update Semantics, Gate Kinematics Causality, Metric Impact (M4, M5, MTR, Lead Time, Closed Duration), Historical Claim Exposure, and Alternative Conventions  
**Historical Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Execution Authority:** NONE  
**Research Authorization:** NONE  
**Audit Mode:** Strict read-only, synthetic-only, metadata-only, evidence-based  

---

## 1. Executive Summary

This independent audit conducts a rigorous investigation of the temporal update loop in [`EventSimulationRunner`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L150-L304), the physical gate kinematics model in [`PhysicalGateModel`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/gate_model.py#L1-L75), and the downstream safety evaluation metrics in [`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) and [`clock_aware.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/clock_aware.py).

### Core Audit Findings:
1. **Retroactive Interval Actuation Confirmed:**  
   In [`EventSimulationRunner._run_frames()`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L190-L265), the simulation loop evaluates incoming sensory evidence and computes state machine transitions *before* advancing the physical gate model. When a transition occurs at timestamp $t$ (e.g. entering `GATE_CLOSING`), the runner takes the newly commanded gate state and applies it across the *preceding* elapsed interval `dt = max(0.0, t - prev_t)`. The simulated actuator therefore moves across the interval $[t - \Delta t, t]$ under a command that was not issued until timestamp $t$.
2. **Causality Classification: `RETROACTIVE`:**  
   Physical causality requires that an actuator command issued at timestamp $t$ affects motion only during $[t, t + \Delta t]$ (or after an actuation delay). The current implementation models backward-in-time actuation across $[t - \Delta t, t]$.
3. **Disproof of Cadence Invariance:**  
   Historical claims (e.g. in Mission 5A reports) asserting that 3.60 s is an invariant physical minimum latency across cadences are factually contradicted:
   - In causal continuous physics: $\tau(10\,\text{Hz}) = 0.10 + 2.00 + 1.50 = \mathbf{3.60\,\text{s}}$, whereas $\tau(5\,\text{Hz}) = 0.20 + 2.00 + 1.50 = \mathbf{3.70\,\text{s}}$.
   - In causal forward discrete simulation: $\tau_{\text{discrete}}(10\,\text{Hz}) = \mathbf{3.60\,\text{s}}$ and $\tau_{\text{discrete}}(5\,\text{Hz}) = \mathbf{3.80\,\text{s}}$.
   - Parity at 3.60 s in the existing runner is an artifact of retroactive stepping shifting 5 Hz arrival to 3.50 s continuous (discretizing to 3.60 s), combined with IEEE 754 floating-point roundoff at 10 Hz delaying detection from 3.50 s to 3.60 s.
4. **Metric-Specific Impact Bounds:**  
   - **$M4$ (Premature Opening):** `POTENTIALLY_AFFECTED`. Retroactive opening across $[t - \Delta t, t]$ accelerates arm unblocking by $\Delta t$. If clearance $T_4$ occurs near unblocking, retroactive stepping could shift an unblocked step across the $T_4$ boundary.
   - **$M5$ (Never Protected Before $T_4$):** `POTENTIALLY_AFFECTED`. Retroactive closing accelerates initial blockage by $\Delta t$. If $T_4$ falls in $[3.60\,\text{s}, 3.80\,\text{s}]$ at 5 Hz, retroactive stepping reports protection at $3.60\,\text{s}$, whereas causal stepping would report unblocked until $3.80\,\text{s}$, creating an $M5$ divergence.
   - **$\text{MTR}$ (Missed-Train Lead-In Screen):** `CONFIRMED_AFFECTED`. The derived threshold is directly shifted from $3.80\,\text{s}$ (causal 5 Hz) to $3.60\,\text{s}$ (runner).
   - **Closed Duration & Clearance Latency:** `CONFIRMED_AFFECTED`. `total_closed_time` accumulates `dt` based on the retroactively stepped angle.
   - **Warning Lead Time:** `NOT_AFFECTED`. Grounded on `first_warning_time`, which is stamped from sensory state transitions before gate stepping.

---

## 2. Source-Level Execution Call Sequence

The execution loop in [`src/railway_detection/simulation/runner.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L187-L267) executes sequentially for each multimodal frame:

```python
# File: src/railway_detection/simulation/runner.py, lines 187-267
for frame in sorted_frames:
    t = frame.master_timestamp_s
    dt = max(0.0, t - prev_t)

    # Step 1: Decision engine evaluates frame at timestamp t
    decision = stage(
        "decision_evaluation",
        lambda frame=frame: self.decision_engine.evaluate_frame(
            frame, scenario_run_id=f"{event_id}_{scenario_name}"
        ),
    )

    # Step 2: Extract gate command from newly evaluated decision
    commanded_gate = GateState(decision.resulting_gate_state)

    # Step 3: Step physical gate model using dt (elapsed since prev_t)
    angle = stage(
        "gate_model_step",
        lambda dt=dt, commanded_gate=commanded_gate: self.gate_model.step(
            dt, commanded_gate
        ),
    )

    # Step 4: Metric tracking using newly mutated gate state
    if self.gate_model.is_passage_blocked or self.gate_model.is_fully_closed:
        total_closed_time += dt

    # Step 5: Record simulation step stamped with t
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
        )
    )
    prev_t = t
```

### Exact Temporal Mapping of Variables:

| Variable / Operation | Exact Temporal Definition | Source Line |
| :--- | :--- | :--- |
| **`t` (`frame.master_timestamp_s`)** | Observation instant of current sensory frame. | `runner.py:188` |
| **`prev_t`** | Observation instant of previous frame ($0.0\,\text{s}$ at frame 0). | `runner.py:185, 267` |
| **`dt`** | Duration of preceding elapsed interval $[prev\_t, t]$. | `runner.py:189` |
| **Decision Evaluation** | Evaluated at time $t$ using evidence up to time $t$. | `runner.py:192-194` |
| **State Transition Time** | Recorded as `state_entry_time_s = float(timestamp_s) = t`. | `decision_engine.py:465` |
| **Gate Command Extraction** | Command decided at $t$ reflecting state at $t$. | `runner.py:221` |
| **Gate Model Stepping** | Applies `commanded_gate` over `dt = t - prev_t`. | `runner.py:226-228` |
| **Gate Angle Interval** | **Preceding interval $[prev\_t, t]$** (retroactive). | `gate_model.py:42-53` |
| **Recorded Step Timestamp** | Stamped as $t$, but arm position reflects motion over $[prev\_t, t]$. | `runner.py:258-264` |

---

## 3. Temporal Semantics and Causality Classification

### 3.1 The Canonical Causal Order
In an idealized, physically causal cyber-physical control system:
1. **$t_k$:** Sensory evidence arrives and is ingested.
2. **$t_k$:** Controller evaluates evidence and makes a state transition.
3. **$t_k$:** Controller issues actuator command $u(t_k)$.
4. **$[t_k, t_{k+1}]$:** Actuator physically responds to $u(t_k)$ over the future interval.
5. **$t_{k+1}$:** Sensor observes physical position $\theta(t_{k+1}) = \theta(t_k) + \int_{t_k}^{t_{k+1}} \dot{\theta}(u(t)) dt$.

### 3.2 Evaluation of Implementation Call Steps

| Simulation Component | Implemented Behavior | Causal Expectation | Classification |
| :--- | :--- | :--- | :---: |
| **Frame Sorting & Delivery** | Delivered in ascending timestamp order. | Monotonic increasing time. | **`CAUSAL`** |
| **Rule 8 / 10 Guards** | Rejects disordered or duplicate timestamps. | Protects clock monotonicity. | **`CAUSAL`** |
| **Source Health & Staleness** | Evaluates age $t - t_{\text{obs}}$ at current $t$. | Retrospective health audit. | **`CAUSAL`** |
| **Decision Engine Transitions** | Transitions when dwell condition $t - t_{\text{entry}} \ge \tau$ holds. | Transition triggered at instant condition met. | **`CAUSAL`** |
| **Gate Model Actuation Integration** | Steps actuator with new command across preceding $[t - \Delta t, t]$. | Motion should occur over subsequent interval $[t, t + \Delta t]$. | **`RETROACTIVE`** |
| **SimulationStep Angle Binding** | Angle at $t$ reflects motion that occurred before $t$. | Angle at $t$ should reflect past commands up to $t$. | **`RETROACTIVE`** |
| **`is_passage_blocked` Timestamp** | Evaluated on retroactively stepped angle. | True at $t$ even though closing only started at $t$. | **`RETROACTIVE`** |

### 3.3 Core Question Resolution
> *When a controller decision at time $t$ changes the gate command, does the simulator apply that command only from $t$ forward, or does it apply it over an interval that began before $t$?*

**Definitive Audit Answer:**  
The simulator applies the command over an interval that began **before $t$**. Specifically, in Step 11 at 5 Hz ($t = 2.20\,\text{s}$), the controller transitions to `GATE_CLOSING` at $t = 2.20\,\text{s}$. The runner immediately calls `gate_model.step(dt=0.2, commanded_gate=CLOSING)`, decrementing the arm angle by $6.0^\circ$ (from $90.0^\circ$ to $84.0^\circ$). The gate is treated as having closed at $30^\circ/\text{s}$ across $[2.00\,\text{s}, 2.20\,\text{s}]$, an interval during which the controller was actually in `WARNING` and the gate was commanded `OPEN`.

---

## 4. Gate Kinematics and Cadence Analysis

### 4.1 Kinematic Governing Equations
In [`PhysicalGateModel.step()`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/gate_model.py#L42-L65):
$$\dot{\theta} = \frac{90.0^\circ}{\tau_{\text{closing}}} = \frac{90.0^\circ}{3.0\,\text{s}} = 30.0^\circ/\text{s}$$
$$\theta(t) = \max\left(0.0, \theta(t - \Delta t) - 30.0 \times \Delta t\right)$$
- Movement is strictly linear with $\Delta t$.
- Target angle for passage blockage is $\theta \le 45.0^\circ$.
- There is **no tolerance band**, **no angle quantization**, and **no hysteresis**.
- The evaluation `self.current_angle_deg <= 45.0` is an exact IEEE 754 floating-point comparison.

### 4.2 Cadence Sensitivity Matrix (Theoretical vs. Synthetic Observed)

| Simulation Cadence & Model | First Detection ($T_0$) | Confirmation (2 Ticks) | Warning Dwell (2.0s) | Closing Command Issued | First Physical Movement | First Blocked Step ($\le 45^\circ$) | Causality Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **10 Hz Theoretical Continuous** | $0.00\,\text{s}$ | $0.10\,\text{s}$ | $2.10\,\text{s}$ | $2.10\,\text{s}$ | $2.10\,\text{s}$ | $\mathbf{3.60\,\text{s}}$ | `CAUSAL` |
| **10 Hz Causal Forward Discrete** | $0.00\,\text{s}$ | $0.10\,\text{s}$ | $2.10\,\text{s}$ | $2.10\,\text{s}$ | $2.20\,\text{s}$ | $\mathbf{3.60\,\text{s}}$ | `CAUSAL` |
| **10 Hz Actual Runner (Observed)** | $0.00\,\text{s}$ | $0.10\,\text{s}$ | $2.10\,\text{s}$ | $2.10\,\text{s}$ | $2.10\,\text{s}$ *(retroactive)* | $\mathbf{3.60\,\text{s}}^\dagger$ | `RETROACTIVE` |
| **5 Hz Theoretical Continuous** | $0.00\,\text{s}$ | $0.20\,\text{s}$ | $2.20\,\text{s}$ | $2.20\,\text{s}$ | $2.20\,\text{s}$ | $\mathbf{3.70\,\text{s}}$ | `CAUSAL` |
| **5 Hz Causal Forward Discrete** | $0.00\,\text{s}$ | $0.20\,\text{s}$ | $2.20\,\text{s}$ | $2.20\,\text{s}$ | $2.40\,\text{s}$ | $\mathbf{3.80\,\text{s}}$ | `CAUSAL` |
| **5 Hz Actual Runner (Observed)** | $0.00\,\text{s}$ | $0.20\,\text{s}$ | $2.20\,\text{s}$ | $2.20\,\text{s}$ | $2.20\,\text{s}$ *(retroactive)* | $\mathbf{3.60\,\text{s}}$ | `RETROACTIVE` |

$^\dagger$*Note on 10 Hz Actual Runner:* Continuous crossing occurs at $t = 3.50\,\text{s}$. However, cumulative floating-point subtraction leaves `angle = 45.00000000000004` at $t = 3.50\,\text{s}$. The condition $45.00000000000004 \le 45.0$ evaluates to `False`, delaying the observed blocked step to $t = 3.60\,\text{s}$ ($42.0^\circ$).

---

## 5. Metric Dependency and Impact Matrix

| Evaluation Metric | Consumed Timestamps | State Source (Recorded vs Reconstructed) | Gate Command Dependency | Retroactive Stepping Effect | Impact Status | Required Evidence to Quantify |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **M4 Premature Opening** | $t_{\text{blocked}}$, interior steps, $T_4$ | Recorded `is_passage_blocked` & `gate_state` | Indirect (via arm unblocking) | Retroactive opening unblocks $\Delta t$ earlier; could trigger premature opening if $T_4$ falls in unblocked interval. | **`POTENTIALLY_AFFECTED`** | Event consist clearance timestamps ($T_4$) near gate opening. |
| **M5 Never Protected Before $T_4$** | $t_{\text{blocked}}$, $T_4$, replay origin | Recorded `is_passage_blocked` | Direct (initial blocking timestamp) | Retroactive closing blocks $\Delta t$ earlier ($3.60\,\text{s}$ vs $3.80\,\text{s}$). If $T_4 \in [3.6, 3.8]$, event is marked protected instead of M5. | **`POTENTIALLY_AFFECTED`** | Consist clearance timestamps ($T_4$) falling between 3.6s and 3.8s. |
| **MTR Lead-In Screen** | $T_0$, $T_1$, $\tau_{\text{min\_block}}$ | Synthetic trace of runner | Direct (defines $\tau_{\text{min\_block}}$) | Derived latency shifted from $3.80\,\text{s}$ to $3.60\,\text{s}$ at 5 Hz. | **`CONFIRMED_AFFECTED`** | Comparison of $T_1 - T_0$ against $3.80\,\text{s}$ vs $3.60\,\text{s}$. |
| **Warning Lead Time** | $T_1$, $t_{\text{warning}}$ | Recorded `crossing_state` | None (depends on optical confirm) | Zero effect; $t_{\text{warning}}$ is stamped before gate model steps. | **`NOT_AFFECTED`** | N/A |
| **Closed Duration** | All $t_k$ where blocked/closed | Cumulative sum of $\Delta t$ | Direct (integration interval) | Shifts start of closed duration earlier by $\Delta t$; shifts end earlier by $\Delta t$. | **`CONFIRMED_AFFECTED`** | Step-by-step gate angle integration traces. |
| **Clearance Latency** | $T_4$, $t_{\text{open}}$ | Recorded `crossing_state` / gate angle | Direct (opening command timing) | Unblocking occurs $\Delta t$ earlier. | **`CONFIRMED_AFFECTED`** | Timing comparison of clearance to gate open. |

---

## 6. Historical Result and Claim Exposure Register

| Historical Result or Claim | Primary Source Document | Depends on Affected Behavior? | Impact Status | Safe Interpretation | Further Evidence Required |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **"First-block latency is 3.6 s at both tick sizes"** | `docs/generated/mission_5a/EXPERIMENT_DESIGN_RECONCILIATION_20261101_M5A.md:28` | **YES** | **`CONFIRMED_AFFECTED`** | Parity is an artifact of retroactive stepping + float roundoff. Causal continuous latency is 3.70 s at 5 Hz. | Synthetic trace analysis (completed in this audit). |
| **"18 of 22 events fail the 3.6s feasibility screen"** | `docs/generated/master_reaudit/MTR_PROVENANCE_CHALLENGE_AUDIT.md:18` | **YES** | **`CONFIRMED_AFFECTED`** | Evaluated against an implementation-derived 3.60 s threshold. At causal 3.80 s, the exact same 21 events still fail ($T_1 \le 3.20\,\text{s}$). | Screening recomputation against causal threshold. |
| **"Kinematic minimum barrier descent time of approx 3.60 s"** | `docs/generated/master_reaudit/MTR_PROVENANCE_CHALLENGE_AUDIT.md:235` | **YES** | **`CONFIRMED_AFFECTED`** | Overclaims physical justification. Threshold is discrete controller property. | Manuscript revision to replace physical claim. |
| **M4 Premature Opening 0% Violation Rate** | Historical benchmark execution reports | **POSSIBLE** | **`POTENTIALLY_AFFECTED`** | If any event had gate opening within $[T_4 - 0.2, T_4]$, retroactive stepping could alter the verdict. | Re-check clearance timestamps against opening step traces. |
| **M5 Consist Non-Protection Count = 0** | Historical benchmark execution reports | **POSSIBLE** | **`POTENTIALLY_AFFECTED`** | If any consist cleared between 3.6 s and 3.8 s, causal stepping would classify it as M5. | Inspect all 23 candidate $T_4$ timestamps. |
| **Warning Lead Time Distribution** | Historical descriptive tables | **NO** | **`NOT_AFFECTED`** | Warning state is entered before gate movement; unaffected by kinematics. | None. |

---

## 7. Synthetic Test Coverage and Gaps

An audit of the unit test suites reveals significant blind spots regarding simulation causality:

### 7.1 Existing Assertions That Mask Non-Causality:
1. **`test_derivation_is_deterministic_and_tick_dependent` ([`tests/unit/test_mission5a1_audit_regressions.py:355-361`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_mission5a1_audit_regressions.py#L355-L361)):**
   ```python
   assert derive_min_block_latency_s(tick_s=0.2) == derive_min_block_latency_s(tick_s=0.1)
   assert derive_min_block_latency_s(tick_s=0.5) != derive_min_block_latency_s(tick_s=0.2)
   ```
   *Audit Finding:* This test explicitly enforces parity between 0.2 s and 0.1 s, treating the artifact as an intentional design invariant without verifying causality.
2. **`test_scenario_18_gate_command_timing_vs_physical_kinematics` ([`tests/unit/test_phase3_sensor_health_decision_policy.py:475-492`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_phase3_sensor_health_decision_policy.py#L475-L492)):**  
   Steps `PhysicalGateModel` directly with `gate.step(1.5, GateState.CLOSING)`, testing the gate model in complete isolation from the simulation runner. It never tests the coupling in `EventSimulationRunner._run_frames()`.
3. **`test_scenario_19_engine_only_traversal` ([`tests/unit/test_phase3_sensor_health_decision_policy.py:496-520`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_phase3_sensor_health_decision_policy.py#L496-L520)):**  
   Tests `MultimodalDecisionEngine` in isolation from `PhysicalGateModel`.

### 7.2 Critical Test Gaps:
- **Zero tests verify causal actuator ordering:** No test asserts that a gate command issued at timestamp $t$ produces zero angular displacement between $t - \Delta t$ and $t$.
- **Zero tests verify irregular frame step behavior:** No test verifies gate stepping when frame timestamps have varying $\Delta t$.
- **Zero tests verify floating-point boundary robustness:** No test checks whether `angle <= 45.0` is robust against IEEE 754 precision overshoot around $45.0^\circ$.

---

## 8. Alternative Temporal Conventions

To resolve the identified causality contradiction, three architectural conventions are formally characterized:

### Convention A: Current Retroactive Interval Convention (As Implemented)
- **Semantics:** Command decided at $t_k$ is applied to the actuator across $[t_{k-1}, t_k]$.
- **Kinematics:** $\theta(t_k) = \max(0.0, \theta(t_{k-1}) - \dot{\theta}(u(t_k)) \cdot (t_k - t_{k-1}))$.
- **Latencies:** 5 Hz yields $3.60\,\text{s}$; 10 Hz yields $3.60\,\text{s}$ (with float error).
- **Pros/Cons:** Simple implementation; violates physical causality; produces cadence artifacts.

### Convention B: Strict Forward-Causal Convention (Next-Interval Actuation)
- **Semantics:** Command decided at $t_k$ takes effect at $t_k$ and governs motion across $[t_k, t_{k+1}]$. At timestamp $t_k$, the arm position reflects only commands active up to $t_k$.
- **Kinematics:**
  - In loop iteration $k$: Step gate using *previous* command $u(t_{k-1})$ over $[t_{k-1}, t_k]$.
  - Evaluate decision engine to determine new command $u(t_k)$ for the next interval.
- **Latencies:**
  - 10 Hz: Confirmation $0.10\,\text{s}$ + Dwell $2.00\,\text{s}$ + Descent $1.50\,\text{s} = \mathbf{3.60\,\text{s}}$.
  - 5 Hz: Confirmation $0.20\,\text{s}$ + Dwell $2.00\,\text{s}$ + Descent $1.60\,\text{s} = \mathbf{3.80\,\text{s}}$.
- **Pros/Cons:** Completely causal; physically defensible; eliminates retroactive motion; increases 5 Hz latency to $3.80\,\text{s}$.

### Convention C: Explicit Delayed-Actuation Convention (Hardware Realism)
- **Semantics:** Command decided at $t_k$ is delayed by an explicit actuator relay latency $\delta_{\text{relay}}$ (e.g. $100\,\text{ms}$) before motor torque is applied.
- **Kinematics:** Continuous ODE integration of arm dynamics with delay: $\dot{\theta}(t) = f(u(t - \delta_{\text{relay}}))$.
- **Latencies:** Adds $\delta_{\text{relay}}$ to all blocking latencies.
- **Pros/Cons:** Maximum physical fidelity to real railway PLC/relay hardware; requires continuous or sub-tick integration.

---

## 9. Researcher Decisions Required

The following formal decisions must be adjudicated by the Principal Investigator:

1. **`DEC-C17` (Simulation Stepping Convention Disposition):**  
   Formally classify the current simulation timing in Version 1.x as **`CONVENTION_A_RETROACTIVE_INTERVAL`** for all historical and exploratory benchmark results, documenting that reported gate latencies are subject to retroactive stepping.
2. **`DEC-C18` (Deprecation of 3.6-Second Invariance Claim):**  
   Deprecate the claim in project documentation and manuscripts that 3.60 s is a cadence-invariant physical constant. Acknowledge that in forward-causal physics, 5 Hz latency is 3.80 s.
3. **`DEC-C19` (Forward-Causal Refactor Scope):**  
   Decide whether to retain Convention A for the frozen B0–B2 descriptive benchmark (to preserve baseline stability) and schedule Convention B (Strict Forward-Causal) for Version 2.0.
4. **`DEC-C20` (MTR Final Disposition):**  
   Affirm that $\text{MTR}$ is **`NOT_ESTIMABLE`** regardless of whether the threshold is 3.60 s or 3.80 s, because 21 of 22 events have $T_1 \le 3.20\,\text{s}$ (or net lead-in $2.70\,\text{s}$), leaving $N \le 1$.

---

## 10. Proposed Remediation Priorities (PROPOSALS ONLY)

> [!IMPORTANT]
> The following remediation steps are proposals for researcher consideration. No code, configuration, or test modifications have been executed during this read-only audit.

1. **Priority 1 (Documentation & Manuscript Integrity):**  
   Update Section 6.2 of [`docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md) to replace claims of "kinematic 3.6s physical barrier descent" with precise wording describing the implementation-derived simulation stepping convention.
2. **Priority 2 (Censoring Taxonomy Realignment):**  
   Update ground-truth schemas in Stage-2.1 to formally distinguish `RECORDING_TRUNCATED_LEAD_IN` from `PHYSICAL_SHORT_LEAD_IN`.
3. **Priority 3 (Simulation Stepping Architecture in v2.0):**  
   When Version 2.0 development opens, refactor `EventSimulationRunner._run_frames()` to adopt Convention B:
   ```python
   # Proposed Convention B structure for v2.0:
   for frame in sorted_frames:
       t = frame.master_timestamp_s
       dt = max(0.0, t - prev_t)
       # 1. Step gate model using PREVIOUSLY commanded state
       angle = self.gate_model.step(dt, self.current_commanded_gate)
       # 2. Evaluate decision engine at t
       decision = self.decision_engine.evaluate_frame(frame)
       # 3. Update commanded gate for NEXT interval
       self.current_commanded_gate = GateState(decision.resulting_gate_state)
   ```
4. **Priority 4 (Floating-Point Threshold Robustness):**  
   Add an explicit epsilon tolerance (`angle <= 45.0 + 1e-6`) to `PhysicalGateModel.is_passage_blocked` to eliminate IEEE 754 precision overshoot jitter.

---

## 11. Git and Safety Preservation Statement

- **Historical Git Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
- **Working Tree Integrity:** Exactly 25 modified tracked files preserved; zero staged changes; 388 untracked porcelain entries preserved.
- **Protected Data Boundary:** Zero raw video (`.mov`, `.mp4`) or audio (`.wav`) files accessed, previewed, decoded, or hashed. Zero production checkpoints loaded. Zero real-data evaluations executed.

---

## 12. Final Statutory Disposition

$$\mathbf{SIMULATION\_CAUSALITY\_CONTRADICTIONS\_FOUND}$$

### Formal Justification:
1. **Retroactive Motion Proven:** The simulation runner applies newly transitioned gate commands to the preceding interval $[t - \Delta t, t]$, violating physical causality.
2. **Cadence Parity Disproven:** The reported 3.60 s parity between 5 Hz and 10 Hz is an artifact of retroactive stepping combined with floating-point roundoff, directly contradicting theoretical continuous physics ($3.70\,\text{s}$ at 5 Hz vs $3.60\,\text{s}$ at 10 Hz) and causal discrete physics ($3.80\,\text{s}$ at 5 Hz vs $3.60\,\text{s}$ at 10 Hz).
3. **Historical Claim Contradiction:** Historical reports asserted that the 3.60 s threshold proved tick invariance between 0.1 s and 0.2 s, which is disproven by source-level execution traces.

---

REAL-DATA EXECUTION: NOT AUTHORIZED.
