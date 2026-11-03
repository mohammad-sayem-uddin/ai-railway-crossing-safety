# MISSION 17B: FORWARD-CAUSAL CONVENTION B SIMULATION REDESIGN

**Project:** Train Gate Automation — Bangladesh
**Subsystem:** Discrete-Time Simulation Engine & Physical Gate Actuation
**Target Architecture:** Forward-Causal Execution Semantics (Convention B)
**Document ID:** `MISSION-17B-DELIV-02`
**Execution Authority:** NONE (Implementation Pending PI Approval of Decision D-09 / Simulation Refactoring) **17C-0: corrected requirements are in the appended correction history; original body retained.**
**Governance Invariants:** RD-019, RD-031, RD-036
**Audited Sources:** [`runner.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L187-L229), [`gate_model.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/gate_model.py#L47-L75), [`state_machine.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/state_machine.py), Missions 16D, 16G, 16H
**Date:** 2026-11-03

---

## 1. Executive Summary & Defect Statement

This document specifies the mathematical formulation, discrete-time state-space semantics, pseudocode, edge-case behavior, and 14-case synthetic test matrix for the forward-causal **Convention B** simulation engine.

### 1.1 The Historical Convention A Defect
In the historical simulation runner ([`runner.py:187-229`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L187-L229)), the simulation loop operates as follows:

```python
for frame in sorted_frames:
    t = frame.master_timestamp_s
    dt = max(0.0, t - prev_t)

    # 1. Evaluate controller at current frame timestamp t
    decision = self.decision_engine.evaluate_frame(frame, ...)

    # 2. Extract new gate command generated at time t
    commanded_gate = GateState(decision.resulting_gate_state)

    # 3. Advance gate model by dt using the NEW command!
    angle = self.gate_model.step(dt, commanded_gate)

    # 4. Credit elapsed interval dt to total closed duration
    if self.gate_model.is_passage_blocked or self.gate_model.is_fully_closed:
        total_closed_time += dt

    prev_t = t
```

### 1.2 Physical and Causal Impossibility
1. **Retroactive Actuation:** The interval $\Delta t_k = t_k - t_{k-1}$ elapsed *before* the sensor frame at $t_k$ was acquired and processed.
2. The controller evaluates at time $t_k$ and decides a command $u_k$ (e.g., transition from `OPEN` to `CLOSING`).
3. Calling `gate_model.step(dt, commanded_gate)` applies command $u_k$ to the interval $[t_{k-1}, t_k]$, effectively instructing the physical motor to have begun moving at time $t_{k-1}$, **before the sensor frame existed**.
4. Furthermore, if the gate arm descends below $45.0^\circ$ at $t_k$, the entire elapsed duration $\Delta t_k$ is credited to closed duration, shifting gate closure exactly 1 tick ($0.20\,\text{s}$ at 5.0 Hz) too early.

---

## 2. Causal Execution Semantics (Convention B)

### 2.1 Fundamental Axioms of Convention B
1. **Zero Retroaction:** A control command computed at time $t_k$ can affect only the future interval $[t_k, t_{k+1}]$. It cannot mutate physical gate motion across $[t_{k-1}, t_k]$.
2. **Step Sequence:**
   - At boundary $t_k$, physical state $\theta_k$ is observed.
   - The elapsed interval $\Delta t_k = [t_{k-1}, t_k]$ is integrated using the command $u_{k-1}$ that was already active at time $t_{k-1}$.
   - The controller observes state at $t_k$ and computes a new command $u_k$.
   - Command $u_k$ is registered and becomes active for the subsequent interval $[t_k, t_{k+1}]$.
3. **No Hidden Look-Ahead:** Controller evaluation at $t_k$ has access strictly to sensor frames up to and including $t_k$.

### 2.2 Mathematical Discrete-Time State-Space Model

Let $t_0, t_1, \dots, t_N$ be the sequence of sensor timestamps.
For each step $k \in \{0, 1, \dots, N\}$:

- $\mathbf{x}_k = \begin{bmatrix} \theta_k \\ \omega_k \end{bmatrix}$: Physical gate state at timestamp $t_k$, where $\theta_k \in [0.0^\circ, 90.0^\circ]$ is the boom angle and $\omega_k$ is the angular velocity.
- $u_k \in \{\text{HOLD}, \text{LOWER}, \text{RAISE}\}$: Active gate actuator command.
- $y_k$: Multimodal sensor frame observed at $t_k$.
- $\Delta t_k = t_k - t_{k-1}$ (for $k \ge 1$; $\Delta t_0 = 0.0$).

#### Discrete Evolution Equations:
For interval $k \in \{1, \dots, N\}$ spanning $[t_{k-1}, t_k]$:

1. **Gate Position Update (Preceding Command):**
   $$\theta_k = \text{clamp}\Big( \theta_{k-1} + v(u_{k-1}) \cdot \Delta t_k, \; 0.0^\circ, \; 90.0^\circ \Big)$$
   where:
   $$v(u) = \begin{cases}
   -\frac{90.0^\circ}{T_{\text{close}}} & \text{if } u = \text{LOWER} \\
   +\frac{90.0^\circ}{T_{\text{open}}} & \text{if } u = \text{RAISE} \\
   0.0 & \text{if } u = \text{HOLD}
   \end{cases}$$

2. **Passage-Blocked State Indicator:**
   $$b_k = \mathbf{1}_{\{\theta_k \le 45.0^\circ\}}$$

3. **Closed Duration Accumulation:**
   $$T_{\text{closed}, k} = T_{\text{closed}, k-1} + \Delta t_k \cdot b_k$$

4. **Controller Decision Evaluation (Observation at $t_k$):**
   $$u_k = \mathcal{C}\big( y_k, \theta_k, \text{history}_{0:k} \big)$$
   The new command $u_k$ is now staged to govern the subsequent interval $[t_k, t_{k+1}]$.

---

## 3. Algorithmic Specification & Pseudocode

```python
"""Convention B forward-causal simulation execution loop."""

from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class ActuatorCommand(str, Enum):
    HOLD = "HOLD"
    LOWER = "LOWER"
    RAISE = "RAISE"


@dataclass
class CausalSimulationStep:
    timestamp_s: float
    dt_s: float
    observed_angle_deg: float
    is_passage_blocked: bool
    applied_command: ActuatorCommand  # Command active during [t_{k-1}, t_k]
    issued_command: ActuatorCommand   # New command evaluated at t_k
    cumulative_closed_time_s: float


def run_convention_b_simulation(
    frames: List[MultimodalFrame],
    closing_duration_s: float = 6.0,
    opening_duration_s: float = 6.0,
) -> List[CausalSimulationStep]:
    if not frames:
        return []

    # Sort frames chronologically
    sorted_frames = sorted(frames, key=lambda f: f.master_timestamp_s)

    # Initial physical conditions at t_0
    current_angle_deg = 90.0  # Fully open
    active_command = ActuatorCommand.HOLD
    prev_t = sorted_frames[0].master_timestamp_s
    total_closed_time = 0.0
    steps: List[CausalSimulationStep] = []

    # Frame 0: Boundary initialization
    f0 = sorted_frames[0]
    t0 = f0.master_timestamp_s
    decision_engine.reset(initial_time_s=t0)

    # Evaluate initial decision at t0
    initial_decision = decision_engine.evaluate_frame(f0)
    staged_command = map_decision_to_command(initial_decision)

    steps.append(
        CausalSimulationStep(
            timestamp_s=t0,
            dt_s=0.0,
            observed_angle_deg=current_angle_deg,
            is_passage_blocked=(current_angle_deg <= 45.0),
            applied_command=ActuatorCommand.HOLD,
            issued_command=staged_command,
            cumulative_closed_time_s=0.0,
        )
    )

    # Active command for interval [t_0, t_1] becomes staged_command
    active_command = staged_command
    prev_t = t0

    # Main forward-causal stepping loop
    for frame in sorted_frames[1:]:
        t = frame.master_timestamp_s
        dt = max(0.0, round(float(t - prev_t), 6))

        # Check for duplicate or out-of-order timestamps
        if dt == 0.0:
            # Rule 10: Duplicate frame rejection
            handle_duplicate_frame(frame)
            continue
        elif dt < 0.0:
            # Rule 8: Out-of-order rejection
            handle_out_of_order_frame(frame)
            continue

        # 1. Physical propagation across [prev_t, t] using active_command
        if active_command == ActuatorCommand.LOWER:
            rate = 90.0 / closing_duration_s
            current_angle_deg = max(0.0, current_angle_deg - rate * dt)
        elif active_command == ActuatorCommand.RAISE:
            rate = 90.0 / opening_duration_s
            current_angle_deg = min(90.0, current_angle_deg + rate * dt)

        is_blocked = (round(current_angle_deg, 4) <= 45.0)

        # 2. Accumulate closed duration
        if is_blocked:
            total_closed_time += dt

        # 3. Controller evaluation at time t
        decision = decision_engine.evaluate_frame(frame)
        new_command = map_decision_to_command(decision)

        # 4. Record step
        steps.append(
            CausalSimulationStep(
                timestamp_s=t,
                dt_s=dt,
                observed_angle_deg=round(current_angle_deg, 4),
                is_passage_blocked=is_blocked,
                applied_command=active_command,
                issued_command=new_command,
                cumulative_closed_time_s=round(total_closed_time, 6),
            )
        )

        # 5. Advance active command to govern next interval [t, t_{k+1}]
        active_command = new_command
        prev_t = t

    return steps
```

---

## 4. Rigorous Edge-Case Analysis

### 4.1 Uniform vs. Irregular Sampling
- **Uniform Cadence ($\Delta t = 0.20\,\text{s}$):** When all $\Delta t_k$ are identical, the displacement per tick is constant: $\Delta \theta = \frac{90^\circ}{6.0\,\text{s}} \times 0.20\,\text{s} = 3.0^\circ/\text{tick}$.
- **Irregular Cadence ($\Delta t_k \text{ variable}$):** If a sensor frame drops, $\Delta t_k$ may be $0.40\,\text{s}$ or $1.00\,\text{s}$.
  - Under Convention B, the motor integrates $v(u_{k-1}) \cdot \Delta t_k$.
  - If $\Delta t_k > \Delta t_{\text{cadence\_max}}$ (e.g., gap $> 2.0\,\text{s}$), a safety timeout must fire, clamping gate command to `LOWER` (fail-safe close).

### 4.2 Terminal Blocked Intervals vs. Complete Cycles
As proven in Missions 16D, 16G, and 16H:
- Let $b_k \in \{0, 1\}$ be the passage-blocked indicator.
- In Convention A: interval $[t_{k-1}, t_k]$ is credited using state $\theta_k^A$ (stepped with $u_k$).
- In Convention B: interval $[t_{k-1}, t_k]$ is credited using state $\theta_k^B$ (stepped with $u_{k-1}$).
- For a complete closure and reopening cycle terminating in `OPEN` state ($b_N = 0$):
  $$T_{\text{causal}} - T_{\text{retro}} \equiv 0.00\,\text{s}$$
  The delay in closing is exactly canceled by the delay in reopening.
- For a truncated recording terminating while the gate is still lowered ($b_N = 1$):
  $$T_{\text{causal}} - T_{\text{retro}} = -\Delta t \cdot b_N = -\Delta t$$
  At $5.0\,\text{Hz}$, this equals exactly $-0.2000\,\text{s}$.

### 4.3 Duplicate and Out-of-Order Timestamps
- If $t_k == t_{k-1}$ ($\Delta t = 0$): Rule 10 rejects the frame. The master clock does not advance, no gate movement occurs, and closed duration is not incremented.
- If $t_k < t_{k-1}$ ($\Delta t < 0$): Rule 8 rejects the frame. A clock fault is recorded, and the simulation state is preserved.

### 4.4 Floating-Point Comparison Rules
To avoid 64-bit IEEE-754 precision drift:
- All timestamps must be compared after rounding to microseconds: `round(float(t), 6)`.
- All angles must be compared using strict threshold tolerances:
  $$\text{is\_passage\_blocked} \iff \theta_k \le 45.000001^\circ$$
  $$\text{is\_fully\_closed} \iff \theta_k \le 0.000001^\circ$$
  $$\text{is\_fully\_open} \iff \theta_k \ge 89.999999^\circ$$

---

## 5. Relationship to Historical Table 11 & Reporting Policy

### 5.1 Preservation of Historical Baseline
Historical Table 11 from the original study must be preserved in scientific archives as published. It represents the historical output of the Convention A runner under baseline code commit `d4db94d4a4ea`.

### 5.2 Analytical Offset Conditionality
The $-0.2000\,\text{s}$ offset is **not** an unconditional universal law for all discrete simulations. It is strictly proven under the following three necessary and sufficient conditions:
1. Cadence is strictly uniform: $\Delta t_k = 0.200000\,\text{s}$ for all $k$.
2. Terminal state is blocked: $b_N = 1$ ($\theta_N \le 45.0^\circ$).
3. Exactly one closure cycle occurs during the recording.

Across all 27 B4 events, these conditions hold identically ($100\%$ verified in Mission 16G/16H).

### 5.3 Reporting Recommendation for Future Manuscripts
Future publications should report simulation duration using a transparent dual-column presentation:

| Event ID | Historical Convention A ($T_{\text{Table 11}}$) | Forward-Causal Convention B ($T_{\text{causal}}$) | Cadence Qualifier | Actuation Delta ($\Delta T$) |
| :---: | :---: | :---: | :---: | :---: |
| `event_001` | $38.40\,\text{s}$ | $38.20\,\text{s}$ | Uniform 5.0 Hz | $-0.20\,\text{s}$ |
| `event_002` | $42.60\,\text{s}$ | $42.40\,\text{s}$ | Uniform 5.0 Hz | $-0.20\,\text{s}$ |
| ... | ... | ... | ... | ... |

> [!NOTE]
> **No Execution in Mission 17B:** This mission does not alter historical tables or rerun production simulations. Dual reporting is a recommended standard for future evaluation work packages.

---

## 6. Comprehensive 14-Case Synthetic Test Matrix

The following test specifications define the verification suite required for the future Convention B runner implementation:

| Test ID | Test Name | Input Timeline & Scenario | Expected State Transition | Expected Closed Duration | Success Metric / Pass Criteria | Failure Condition |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-SIM-01** | `test_first_frame_causality` | $t = [0.0, 0.2]$, command issued at $t=0.0$ is `LOWER`. | At $t=0.0$, angle is $90.0^\circ$. At $t=0.2$, angle is $87.0^\circ$. | $0.00\,\text{s}$ (angle $> 45^\circ$). | Angle evolves only across $[0.0, 0.2]$. | Angle changes at $t=0.0$. |
| **TC-SIM-02** | `test_transition_lag` | $t = [0.0, 0.2, 0.4]$, command `LOWER` issued at $t=0.2$. | At $t=0.2$, angle remains $90.0^\circ$; starts descending at $t=0.2$; at $t=0.4$, angle is $87.0^\circ$. | $0.00\,\text{s}$. | Arm motion does not begin before $t=0.2$. | Motion occurs across $[0.0, 0.2]$. |
| **TC-SIM-03** | `test_uniform_5hz_stepping` | 50 frames at $\Delta t = 0.20\,\text{s}$; continuous `LOWER`. | Boom reaches $0.0^\circ$ at $t = 6.0\,\text{s}$ (tick 30); crosses $45.0^\circ$ at $t = 3.0\,\text{s}$ (tick 15). | Closed time tracks exact blocked duration. | Angle decreases by exactly $3.0^\circ \pm 10^{-6}$ per tick. | Angle delta deviates from $3.0^\circ$. |
| **TC-SIM-04** | `test_uniform_10hz_stepping` | 100 frames at $\Delta t = 0.10\,\text{s}$; continuous `LOWER`. | Boom reaches $0.0^\circ$ at $t = 6.0\,\text{s}$ (tick 60); crosses $45.0^\circ$ at $t = 3.0\,\text{s}$ (tick 30). | Closed time matches analytical integral. | Angle decreases by exactly $1.5^\circ \pm 10^{-6}$ per tick. | Stepping error at higher frequency. |
| **TC-SIM-05** | `test_irregular_cadence` | $\Delta t \in [0.10, 0.35, 0.05, 0.50]$; total $t = 5.0\,\text{s}$. | Position updates proportionally: $\Delta \theta = 15^\circ \times \Delta t_k$. | Closed duration matches sum of blocked $\Delta t_k$. | Total angle displacement matches integrated velocity. | Inaccurate dt integration. |
| **TC-SIM-06** | `test_complete_cycle_zero_delta` | Full close ($6\,\text{s}$), hold ($10\,\text{s}$), full open ($6\,\text{s}$); ends $90^\circ$. | Barrier descends to $0^\circ$, stays closed, then reopens to $90^\circ$ at end. | $\mathbf{T_{\text{causal}} \equiv T_{\text{retro}}}$. | Duration delta between Convention A and B is exactly $0.00\,\text{s}$. | Non-zero delta for complete cycle. |
| **TC-SIM-07** | `test_terminal_blocked_delta` | 100 frames at 5.0 Hz; barrier lowers and remains at $0.0^\circ$ at end. | Final angle $0.0^\circ$; $b_N = 1$. | $\mathbf{T_{\text{causal}} = T_{\text{retro}} - 0.20\,\text{s}}$. | Duration delta equals exactly $-0.2000\,\text{s}$. | Delta $\neq -0.20\,\text{s}$. |
| **TC-SIM-08** | `test_multiple_blocked_episodes` | Two distinct train passes separated by $20\,\text{s}$ open interval. | Closes, reopens, closes again, ends lowered. | First episode delta $= 0.0\,\text{s}$; second episode delta $= -0.20\,\text{s}$. | Net delta equals $-0.20\,\text{s}$. | Delta compound error. |
| **TC-SIM-09** | `test_partial_final_interval` | Final interval ends mid-motion at $\theta_N = 30.0^\circ$ ($b_N = 1$). | Gate is partially closed at recording cutoff. | $\Delta T = -\Delta t_{\text{final}}$. | Exact match with final interval duration. | Mismatch in partial accumulation. |
| **TC-SIM-10** | `test_duplicate_timestamp_rejection`| Sequence: $t = [1.0, 1.2, 1.2, 1.4]$. | Tick 2 rejected (Rule 10); gate angle does not step twice. | Closed duration does not double-count. | `SimulationStep` count is 3; 1 rejection logged. | Duplicate frame steps physical model. |
| **TC-SIM-11** | `test_out_of_order_rejection` | Sequence: $t = [1.0, 1.4, 1.2, 1.6]$. | Tick 2 rejected (Rule 8); clock does not step backwards. | Monotonicity preserved. | Fault flag raised; gate state frozen during fault. | Backward motion or crash. |
| **TC-SIM-12** | `test_missing_timestamp_gap` | Sequence: $t = [1.0, 1.2, 4.2]$ (3.0s sensor dropout). | Watchdog timeout fires; command clamped to `LOWER`. | Fail-safe closure triggered. | System detects gap $> 2.0\,\text{s}$ and commands close. | System ignores missing frame gap. |
| **TC-SIM-13** | `test_floating_point_boundary` | Boom angle reaches exactly $45.0000001^\circ$ vs $44.9999999^\circ$. | Strict thresholding correctly distinguishes blocked vs unblocked. | Boundary duration precision $\le 10^{-6}\,\text{s}$. | No jitter or state flipping at threshold. | Flapping state near $45.0^\circ$. |
| **TC-SIM-14** | `test_deterministic_replay` | Run identical synthetic timeline 100 times in sequence. | Identical state vectors across all runs. | Standard deviation $= 0.0\,\text{s}$. | Exact bit-for-bit repeatability across runs. | Non-deterministic outputs. |

---

## 7. Acceptance Criteria for Future Implementation

The future software implementation of Convention B must satisfy:
1. Implementation isolated in clean refactored module or parameter-flagged runner (`convention="B"`).
2. All 14 synthetic tests pass with zero regression in historical test suites.
3. No retroactive stepping: gate displacement across $[t_{k-1}, t_k]$ depends strictly on command active at $t_{k-1}$.
4. Historical Table 11 remains preserved in archives; new results reported in dual-column format.

---
*End of Mission 17B Deliverable 2.*

---

## Mission 17C-0 correction history — superseding causal contract

**2026-11-03; documentation correction only; implementation remains PENDING.** Original §§1–7 are retained as historical wording. This appendix supersedes conflicting pseudocode, equations, parameter defaults, claims and test oracles. Independent evidence: `MISSION_17C0_VERIFICATION_MATRIX.md` C046–C059; full proof/counterexamples and 27-file ledger in the 17C-0 audit.

### State, command and interval semantics

1. Set the initial state at the first valid timestamp; do not integrate before the recording origin. Evaluate observation y0 to issue u0 with zero elapsed actuation. For each subsequent valid boundary tk: validate the timestamp first; propagate the preceding active command u(k-1) across (t(k-1),tk]; account for that interval; then obtain/use the endpoint state and evaluate yk to issue uk for future time. This fixes §2.1's ambiguous instruction to observe theta_k before computing it. Controller access to physical state must be an explicit future interface, not an assumed existing argument.
2. Preserve frozen parity parameters: closing 3.0s/opening 3.0s, speed 30°/s, initial 90°. The original6.0s defaults and 3°/tick examples are a changed synthetic scenario, not the historical baseline (historical displacement is 6° per0.2s). Parameter changes need approval.
3. Existing `GateState.CLOSED` and `CLOSING` both lower until0; `OPEN` and `OPENING` both raise until90. The new HOLD/LOWER/RAISE mapping must preserve that target-state behavior; HOLD must not freeze a partly moving arm merely because a controller state became CLOSED/OPEN. Reset, rejected-frame and fault transitions need explicit mapping.
4. Log interval start/end, elapsed duration, state before/after propagation, actual applied command and effective time, endpoint observation/decision ID, newly issued command and activation time, blocked predicate and accumulated estimator. Keep rejected arrivals and watchdog events separate. Existing SimulationStep lacks an explicit applied-command field; logging a resulting controller/gate state alone does not prove interval command provenance.

### Correct mathematical relationship

For unchanged dynamics F, a common externally fixed command sequence and uniform interval h:

`theta_A[k] = F(theta_A[k-1], u[k], h)`

`theta_B[k] = F(theta_B[k-1], u[k-1], h)`

If the initial command leaves the initial state unchanged (`F(theta0,u0,h)=theta0`), induction gives `theta_B[k]=theta_A[k-1]`. With one identical blocked predicate and endpoint-weighted accumulation:

`T_B - T_A = h * (b_A[0] - b_A[N])`.

For the historical initially open case `b_A[0]=0`, this becomes `-h*b_A[N]`. No one-closure condition or symmetric opening/closing rates are needed for this shift proof; identical dynamics and command sequence are needed. Recomputed feedback commands, changed parameters/classifiers, initially active LOWER, irregular timing, different origins or cutoffs invalidate use of this shortcut without further proof. The “three necessary and sufficient conditions” claim in §5.2 is withdrawn.

For arbitrary intervals, the valid general comparison is `sum(dt[k]*(b_B[k]-b_A[k]))`. There is no general `-dt_final` rule. Counterexample: initial 90°, speed 30°/s, u0=OPEN then LOWER, ten0.2s intervals followed by 0.1 s: A=.7s, B=.5s, difference=-.2s although final interval=.1s. Initial u0=LOWER with uniform 0.2s and terminal closure gives difference0, refuting terminal-state/cadence sufficiency alone. Irregular dt=[1,2] with u=[OPEN,LOWER,RAISE] gives A=0s, B=2s.

An endpoint sum credits an entire interval from its final blocked state; it is not the continuous physical integral. If exact within-interval blockage is desired for constant-speed motion, calculate threshold-crossing time explicitly (including reversals/timer segments) and report a separate estimator/convention. Causality of actuation does not remove right-endpoint quadrature error. No microsecond timestamp grid implies microsecond physical-duration accuracy.

### Timestamps, faults, final horizon and numerical classification

- Declare offline chronological preprocessing or arrival-order simulation explicitly. Offline sorting cannot test arrival-order rejection. Arrival mode must not sort before order checks. Validate numeric finite nonnegative timestamps and a declared canonical comparison grid; reject missing/NaN/infinite timestamps without fabricating dt. Compare endpoints on that grid before taking their difference; do not clamp negative elapsed time into zero or conflate tiny intervals with duplicate input silently.
- Duplicate/out-of-order arrivals cannot advance the last accepted sensor clock or issue a replacement command. Record the rejected arrival and reason. If independent wall-clock/watchdog events continue, that separate timebase and its physical propagation must be explicit. This is not the unreachable `elif dt<0` branch in the withdrawn pseudocode.
- A missing-sensor watchdog is a prospective controller policy. Either schedule an explicit timer event at last-seen+approved_timeout and integrate old/new commands in their proper subintervals, or detect the gap at the next observation and make the new command effective only then. Never apply a newly discovered LOWER retroactively across the whole gap. The original pseudocode contains neither option. The2s source-staleness default is not scientific approval of a new timeout policy.
- State the observation horizon separately from media duration. Default sampled ledger ends at the last valid timestamp, with no extrapolation. A supplied cutoff after that timestamp needs an explicitly authorized terminal propagation interval using the still-active command (and any timer events), no fabricated sensor frame. A cutoff inside an interval is truncated at that cutoff; no complete-interval theorem automatically applies. Missing terminal time is not silently guessed.
- Use one documented internal angle predicate for blocked status. Original `theta<=45`, `round(theta,4)<=45` and `theta<=45.000001` are different definitions. Existing model uses45 exactly, fully closed<=.05, fully open>=89.95. Preserve those for historical reproduction; future numerical changes need explicit provenance, consistent classification and boundary tests, not display rounding. A tolerance-based numerical comparison does not prove physical accuracy.

### Historical reporting and corrected test oracles

- All27 canonical CSV grids have uniform Decimal0.2s, initial 90°, one blocked episode, terminal 0°, and sums matching Table 11/JSON. Actual totals are 6,737 rows and 6,710 intervals, not16H's6,681/6,654. Use cohort-qualified IDs to avoid counting21 extra bare-name timeline aliases as new events.
- Table 11 first two historical values are 46.0s and 28.8s, not38.4/42.6. Under the explicitly stated fixed-command lag model the respective derived values are 45.8/28.6. Preserve historical values and identify analytical assumptions/provenance, full input artifact, origin, cutoff, parameters and classifier. No corrected causal implementation was executed on real data here. A later documentation baseline commit does not prove the original run's source commit.
- TC-SIM01 is a valid causal first-command test with u0=LOWER; it must not be reused to assume the lag theorem's initial fixed-point condition. TC-SIM03/04 use the existing frozen 3s baseline or explicitly label6s alternate parameters and compute expectations accordingly. Endpoint blocked time must not be equated to an analytical continuous integral.
- TC-SIM05 must supply a complete explicit irregular timestamp sequence summing to its stated horizon (the listed four intervals total 1.0s, not5.0s). TC-SIM06/07/08 require identical command sequences, dynamics, classifier and initial fixed-point condition before using the boundary identity; multiple episodes do not compound the uniform boundary term.
- TC-SIM09's universal `-dt_final` expectation is withdrawn; use the counterexample and general formula. TC-SIM10/11 exercise declared preprocessing/arrival modes separately. TC-SIM12 must include actual timer semantics. TC-SIM13 must assert the chosen classifier consistently and report quantization limits; its1µs duration guarantee is withdrawn. TC-SIM14 establishes repeatability only for specified environment/serialization and fixed inputs, not physical correctness.
- Add missing/nonfinite timestamps, zero/negative durations, empty/single frame, cutoff before/after last observation, initial active command, different command sequences, threshold straddling and applied-versus-issued log checks before any implementation acceptance. A list of 14 proposed cases is not a passing suite.
