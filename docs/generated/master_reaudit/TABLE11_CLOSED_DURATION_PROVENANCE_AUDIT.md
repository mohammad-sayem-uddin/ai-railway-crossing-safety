# MISSION 16C: TABLE 11 CLOSED-DURATION PROVENANCE, ARITHMETIC AND QUANTIFICATION AUDIT

**Project:** Train Gate Automation — Bangladesh  
**Mission:** Master Mission 16C — Historical Table 11 Provenance & Timing Quantification Audit  
**Auditor:** Independent Simulation Timing Auditor, Metric-Provenance Reviewer, and Research Reproducibility Engineer  
**Audit Target:** Table 11 (`results/experiments/tables/table11_per_event_summary.md`), Duration Accumulation Semantics, Gate Transition Kinematics, Recording-Termination Effects, and Forward-Causal Discretization Bounds  
**Historical Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Execution Authority:** NONE  
**Research Authorization:** NONE  
**Audit Mode:** Strict read-only, synthetic-only, metadata-only, evidence-based  

---

## 1. Executive Summary

This independent audit conducts an exhaustive provenance, arithmetic, and implementation investigation into the 27 per-event `Closed Duration` measurements published in historical Table 11 ([`results/experiments/tables/table11_per_event_summary.md`](file:///Users/sayemuddin/Desktop/Train_automation/results/experiments/tables/table11_per_event_summary.md)).

### The Central Question:
> *Can the historical closed-duration values for the 27 events be quantitatively corrected or bounded under forward-causal timing using existing safe evidence, without accessing raw media or executing real-data evaluation?*

### Primary Audit Findings:
1. **Exact 1-to-1 Provenance Established:**  
   Every single closed duration in Table 11 was generated directly from the historical **Condition B4** execution record ([`results/experiments/B4/single_events.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/experiments/B4/single_events.json)). Every value is an exact integer multiple of the 5 Hz simulation tick ($\Delta t = 0.2000\,\text{s}$), with zero remainder across all 27 events.
2. **Post-Update Gate State Accumulation Verified:**  
   In [`EventSimulationRunner._run_frames()`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L223-L234), `total_closed_time` is accumulated *after* [`PhysicalGateModel.step()`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/gate_model.py#L42-L65) updates the boom angle. The accumulation condition `if self.gate_model.is_passage_blocked or self.gate_model.is_fully_closed: total_closed_time += dt` is evaluated on the post-update state.
3. **Refutation of the Symmetric "$\pm 0.20\,\text{s}$" Claim:**  
   Mathematical proof and synthetic traces disprove the assertion in Mission 16B that Table 11 closed durations are subject to a symmetric $\pm 0.20\,\text{s}$ uncertainty:
   - For an event with a **complete closure cycle** (gate closes and fully opens before video ends), the retroactive start shift ($-0.20\,\text{s}$) and retroactive end shift ($-0.20\,\text{s}$) **cancel each other out exactly**. The forward-causal closed duration is **identical** ($\Delta T_{\text{closed}} = \mathbf{0.00\,\text{s}}$).
   - For an event where the video **terminates while the gate is still closed**, retroactive stepping includes the initial transition interval that causal stepping excludes. The forward-causal closed duration is **shorter by exactly one tick** ($\Delta T_{\text{closed}} = \mathbf{-0.20\,\text{s}}$).
   - Under uniform ticks, forward-causal duration is **never longer** than retroactive duration.
   - **Rigorous Discretization Bound:**
     $$\mathbf{T_{\text{closed}}^{\text{causal}} \in [T_{\text{closed}}^{\text{Table 11}} - 0.20\,\text{s}, \; T_{\text{closed}}^{\text{Table 11}}]}$$
4. **Physical Terminology Realignment:**  
   The metric reported as "Closed Duration" in Table 11 is strictly **Simulated Passage-Blocked Duration** ($\theta \le 45.0^\circ$). It does not represent train roadway occupancy duration ($T_4 - T_2$) or full horizontal closure ($\theta \le 0.05^\circ$).
5. **Manuscript Retention Recommendation:**  
   Table 11 can safely remain in the descriptive benchmark documentation, provided it is qualified with an explicit note explaining the Condition B4 provenance, the retroactive interval stepping convention, and the one-sided $[-0.20\,\text{s}, 0.00\,\text{s}]$ timing bound.

---

## 2. Scope and Safety Boundary

This audit was conducted under absolute read-only safety restrictions:
- Zero raw video (`.mov`, `.mp4`) or audio (`.wav`) files were opened, previewed, decoded, or hashed.
- Zero production checkpoints (`best.pt`) or protected caches (`results/experiments/cache/`) were accessed.
- Zero real-data executions, inference runs, or timing pilots were initiated.
- Zero Git modifications, commits, checkouts, or staging operations were executed.
- All evidence was established from safe Python source code, synthetic traces, proposal metadata, and permitted JSON/markdown result summaries.

---

## 3. Repository Baseline

- **Repository HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (matches historical baseline).
- **Tracked Modifications:** Exactly 25 modified files preserved.
- **Untracked Porcelain Files:** Exactly 388 untracked entries preserved.
- **Staged Changes:** Exactly 0 files staged.
- **Audit File Created:** Exactly one new artifact: [`docs/generated/master_reaudit/TABLE11_CLOSED_DURATION_PROVENANCE_AUDIT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/TABLE11_CLOSED_DURATION_PROVENANCE_AUDIT.md).

---

## 4. Source-Level Accumulation Semantics

In [`src/railway_detection/simulation/runner.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L187-L267), the execution call sequence in `_run_frames()` governs closed duration accumulation:

```python
# Lines 188-234
t = frame.master_timestamp_s
dt = max(0.0, t - prev_t)

# 1. State machine transition evaluation at timestamp t
decision = stage("decision_evaluation", lambda: self.decision_engine.evaluate_frame(frame, ...))

# 2. Extract gate command decided at t
commanded_gate = GateState(decision.resulting_gate_state)

# 3. Gate model steps dt using the command decided at t
angle = stage("gate_model_step", lambda: self.gate_model.step(dt, commanded_gate))

# 4. Closed duration accumulation on POST-UPDATE state
if self.gate_model.is_passage_blocked or self.gate_model.is_fully_closed:
    total_closed_time += dt
```

### Exact Answers to Accumulation Questions:

| Investigation Question | Verified Source Behavior | Source Evidence |
| :--- | :--- | :--- |
| **Pre-update vs. Post-update?** | **Post-update.** Gate model `step(dt, commanded_gate)` runs on line 226; accumulation is evaluated on line 232. | `runner.py:226, 232` |
| **Interval Governance?** | Newly decided command governs the **elapsed interval** $[prev\_t, t]$. | `runner.py:189, 226` |
| **Initial Blockage Step?** | **`dt` is accumulated immediately** on the exact tick where the boom crosses $\theta \le 45.0^\circ$. | `runner.py:232-233` |
| **Unblocking Step?** | **`dt` is NOT accumulated** on the step where the boom crosses $\theta > 45.0^\circ$ (condition evaluates to `False`). | `runner.py:232` |
| **Partially Completed Intervals?** | No fractional integration exists. Simulation steps strictly in discrete increments of `dt`. | `runner.py:189` |
| **First Frame Treatment?** | Frame 0 sets `prev_t = t_0`, yielding `dt = 0.0`. Accumulates $0.0\,\text{s}$. | `runner.py:185, 189` |
| **`is_passage_blocked` vs `is_fully_closed`?** | Redundant. Since `is_fully_closed` ($\theta \le 0.05^\circ$) is a subset of `is_passage_blocked` ($\theta \le 45.0^\circ$), the check is strictly $\theta \le 45.0^\circ$. | `gate_model.py:27-33` |
| **Separate Episode Partitioning?** | A single cumulative scalar `total_closed_time` is incremented. Episodes are not partitioned. | `runner.py:186, 233` |
| **Angle vs. State Label?** | Evaluated strictly on **arm angle** ($\theta \le 45.0^\circ$). The `gate_state` label is not checked. | `gate_model.py:28` |

---

## 5. Gate-Transition Timing Arithmetic

We compare the timing mechanics between Convention A (Retroactive Interval) and Convention B (Forward-Causal):

### Case A: Transition into Blocked State
- At 5 Hz ($\Delta t = 0.20\,\text{s}$), the decision to enter `GATE_CLOSING` occurs at $t = 2.20\,\text{s}$.
- **Convention A:** Stepping with `CLOSING` over $[2.00, 2.20]$ drops the angle to $84.0^\circ$ at $t = 2.20\,\text{s}$. The arm reaches $42.0^\circ \le 45.0^\circ$ at $t = 3.60\,\text{s}$. The interval $[3.40, 3.60]$ is accumulated.
- **Convention B:** Motion begins at $t = 2.20\,\text{s}$ across subsequent intervals. The arm is at $48.0^\circ > 45.0^\circ$ at $t = 3.60\,\text{s}$ (not accumulated), and reaches $42.0^\circ \le 45.0^\circ$ at $t = 3.80\,\text{s}$. The interval $[3.60, 3.80]$ is accumulated.
- **Transition Delta:** Convention A accumulates interval $[3.40, 3.60]$ which Convention B does not.  
  $$\Delta T_{\text{start}} = +0.20\,\text{s}$$

---

## 6. Recording-Termination Analysis

### Case B: Gate Remains Blocked Until Recording End
- For any clip where the train passes and the recording terminates before the gate reopens:
  - Both conventions accumulate `dt = 0.20\,\text{s}` on every step from $t = 3.80\,\text{s}$ through $t_{\text{end}}$.
  - The initial lead of $+0.20\,\text{s}$ accumulated by Convention A during $[3.40, 3.60]$ is **never cancelled**.
  - **Result:**  
    $$\mathbf{T_{\text{closed}}^{\text{Conv A}} - T_{\text{closed}}^{\text{Conv B}} = +0.20\,\text{s}}$$

---

## 7. Multiple-Episode and Full-Cycle Analysis

### Case C: Gate Fully Reopens Before Recording End
- When the gate opens from $0.0^\circ$ to $90.0^\circ$ at $30^\circ/\text{s}$, unblocking requires $45.0^\circ$ of rotation ($1.50\,\text{s}$).
- **Convention A:** Unblocking occurs $\Delta t$ earlier. On the tick where $\theta > 45.0^\circ$, accumulation halts.
- **Convention B:** Unblocking occurs $\Delta t$ later. Convention B accumulates one additional tick.
- **Full Cycle Result:**  
  $$\Delta T_{\text{closed}} = \Delta T_{\text{start}} + \Delta T_{\text{end}} = (+0.20\,\text{s}) + (-0.20\,\text{s}) = \mathbf{0.00\,\text{s}}$$
- **Synthetic Sweep Proof:** An exhaustive sweep of 60 possible clip end times confirms:
  $$\Delta T_{\text{closed}} \in \{\mathbf{0.00\,\text{s}}, \; \mathbf{+0.20\,\text{s}}\}$$

### Case D: Multiple Separate Closure Episodes
- If an event experiences multiple closure episodes (e.g. false alarm chatter):
  - Each completed episode contributes exactly $\Delta T_i = 0.00\,\text{s}$.
  - The timing offset does **not** accumulate across episodes.
  - If the final episode terminates while closed, the total offset remains strictly $+0.20\,\text{s}$.

---

## 8. Irregular-Cadence Analysis

### Case F: Non-Uniform $\Delta t$
- If frame timestamps jitter (e.g. $\Delta t \in [0.18\,\text{s}, 0.22\,\text{s}]$), the start offset is governed by the specific frame interval $\Delta t_{\text{start}}$ at the $45^\circ$ crossing.
- **Empirical Reality of Table 11:**  
  Every single one of the 27 events in Table 11 has a duration that is an **exact integer multiple of $0.2000\,\text{s}$** (see Section 9). This proves that the underlying replay was executed on a strictly uniform 5.0 Hz timebase ($\Delta t = 0.2000\,\text{s}$).

---

## 9. Table 11 Event-Level Provenance Register

All 27 entries in Table 11 are traced to [`results/experiments/B4/single_events.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/experiments/B4/single_events.json) (Condition B4, $\Delta t = 0.20\,\text{s}$):

| Event ID in Table 11 | Cohort | Table 11 Value | Exact B4 Value (`single_events.json`) | Discrete Ticks ($N$) | Remainder ($|v - 0.2N|$) | Forward-Causal Bound $[T - 0.2, T]$ | Evidence Level |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `train_events_event_001` | Train ($N=23$) | $46.0\,\text{s}$ | $46.00000000000016\,\text{s}$ | 230 | $0.000000\,\text{s}$ | $[45.8\,\text{s}, 46.0\,\text{s}]$ | Level 1 |
| `train_events_event_002` | Train ($N=23$) | $28.8\,\text{s}$ | $28.79999999999992\,\text{s}$ | 144 | $0.000000\,\text{s}$ | $[28.6\,\text{s}, 28.8\,\text{s}]$ | Level 1 |
| `train_events_event_003` | Train ($N=23$) | $29.6\,\text{s}$ | $29.59999999999993\,\text{s}$ | 148 | $0.000000\,\text{s}$ | $[29.4\,\text{s}, 29.6\,\text{s}]$ | Level 1 |
| `train_events_event_004` | Train ($N=23$) | $74.4\,\text{s}$ | $74.40000000000057\,\text{s}$ | 372 | $0.000000\,\text{s}$ | $[74.2\,\text{s}, 74.4\,\text{s}]$ | Level 1 |
| `train_events_event_005` | Train ($N=23$) | $75.8\,\text{s}$ | $75.80000000000060\,\text{s}$ | 379 | $0.000000\,\text{s}$ | $[75.6\,\text{s}, 75.8\,\text{s}]$ | Level 1 |
| `train_events_event_006` | Train ($N=23$) | $122.4\,\text{s}$ | $122.40000000000126\,\text{s}$ | 612 | $0.000000\,\text{s}$ | $[122.2\,\text{s}, 122.4\,\text{s}]$ | Level 1 |
| `train_events_event_007` | Train ($N=23$) | $34.6\,\text{s}$ | $34.60000000000000\,\text{s}$ | 173 | $0.000000\,\text{s}$ | $[34.4\,\text{s}, 34.6\,\text{s}]$ | Level 1 |
| `train_events_event_008` | Train ($N=23$) | $59.0\,\text{s}$ | $59.00000000000035\,\text{s}$ | 295 | $0.000000\,\text{s}$ | $[58.8\,\text{s}, 59.0\,\text{s}]$ | Level 1 |
| `train_events_event_009` | Train ($N=23$) | $39.2\,\text{s}$ | $39.20000000000007\,\text{s}$ | 196 | $0.000000\,\text{s}$ | $[39.0\,\text{s}, 39.2\,\text{s}]$ | Level 1 |
| `train_events_event_010` | Train ($N=23$) | $20.2\,\text{s}$ | $20.19999999999995\,\text{s}$ | 101 | $0.000000\,\text{s}$ | $[20.0\,\text{s}, 20.2\,\text{s}]$ | Level 1 |
| `train_events_event_011` | Train ($N=23$) | $34.0\,\text{s}$ | $34.00000000000000\,\text{s}$ | 170 | $0.000000\,\text{s}$ | $[33.8\,\text{s}, 34.0\,\text{s}]$ | Level 1 |
| `train_events_event_012` | Train ($N=23$) | $71.4\,\text{s}$ | $71.40000000000000\,\text{s}$ | 357 | $0.000000\,\text{s}$ | $[71.2\,\text{s}, 71.4\,\text{s}]$ | Level 1 |
| `train_events_event_013` | Train ($N=23$) | $70.0\,\text{s}$ | $70.00000000000000\,\text{s}$ | 350 | $0.000000\,\text{s}$ | $[69.8\,\text{s}, 70.0\,\text{s}]$ | Level 1 |
| `train_events_event_014` | Train ($N=23$) | $51.2\,\text{s}$ | $51.20000000000000\,\text{s}$ | 256 | $0.000000\,\text{s}$ | $[51.0\,\text{s}, 51.2\,\text{s}]$ | Level 1 |
| `train_events_event_015` | Train ($N=23$) | $27.4\,\text{s}$ | $27.40000000000000\,\text{s}$ | 137 | $0.000000\,\text{s}$ | $[27.2\,\text{s}, 27.4\,\text{s}]$ | Level 1 |
| `train_events_event_016` | Train ($N=23$) | $43.2\,\text{s}$ | $43.20000000000000\,\text{s}$ | 216 | $0.000000\,\text{s}$ | $[43.0\,\text{s}, 43.2\,\text{s}]$ | Level 1 |
| `train_events_event_017` | Train ($N=23$) | $80.0\,\text{s}$ | $80.00000000000000\,\text{s}$ | 400 | $0.000000\,\text{s}$ | $[79.8\,\text{s}, 80.0\,\text{s}]$ | Level 1 |
| `train_events_event_018` | Train ($N=23$) | $55.2\,\text{s}$ | $55.20000000000000\,\text{s}$ | 276 | $0.000000\,\text{s}$ | $[55.0\,\text{s}, 55.2\,\text{s}]$ | Level 1 |
| `train_events_event_019` | Train ($N=23$) | $56.6\,\text{s}$ | $56.60000000000000\,\text{s}$ | 283 | $0.000000\,\text{s}$ | $[56.4\,\text{s}, 56.6\,\text{s}]$ | Level 1 |
| `train_events_event_020` | Train ($N=23$) | $26.2\,\text{s}$ | $26.20000000000000\,\text{s}$ | 131 | $0.000000\,\text{s}$ | $[26.0\,\text{s}, 26.2\,\text{s}]$ | Level 1 |
| `train_events_event_021` | Train ($N=23$) | $57.6\,\text{s}$ | $57.60000000000000\,\text{s}$ | 288 | $0.000000\,\text{s}$ | $[57.4\,\text{s}, 57.6\,\text{s}]$ | Level 1 |
| `train_events_event_022` | Train ($N=23$) | $42.6\,\text{s}$ | $42.60000000000000\,\text{s}$ | 213 | $0.000000\,\text{s}$ | $[42.4\,\text{s}, 42.6\,\text{s}]$ | Level 1 |
| `train_events_event_023` | Train ($N=23$) | $42.0\,\text{s}$ | $42.00000000000000\,\text{s}$ | 210 | $0.000000\,\text{s}$ | $[41.8\,\text{s}, 42.0\,\text{s}]$ | Level 1 |
| `no_train_events_001` | Control ($N=3$) | $18.8\,\text{s}$ | $18.80000000000000\,\text{s}$ | 94 | $0.000000\,\text{s}$ | $[18.6\,\text{s}, 18.8\,\text{s}]$ | Level 1 |
| `no_train_events_002` | Control ($N=3$) | $9.6\,\text{s}$ | $9.60000000000000\,\text{s}$ | 48 | $0.000000\,\text{s}$ | $[9.4\,\text{s}, 9.6\,\text{s}]$ | Level 1 |
| `no_train_events_003` | Control ($N=3$) | $10.6\,\text{s}$ | $10.60000000000000\,\text{s}$ | 53 | $0.000000\,\text{s}$ | $[10.4\,\text{s}, 10.6\,\text{s}]$ | Level 1 |
| `engine_events_001` | Engine ($N=1$) | $5.0\,\text{s}$ | $5.00000000000000\,\text{s}$ | 25 | $0.000000\,\text{s}$ | $[4.8\,\text{s}, 5.0\,\text{s}]$ | Level 1 |

---

## 10. Universal $\pm 0.20\,\text{s}$ Claim Challenge

### Refutation & Mathematical Correction:
- **Historical Claim (Mission 16B):** "Table 11 durations are subject to a $\pm 0.20\,\text{s}$ shift under forward-causal stepping."
- **Audit Refutation:**
  1. The shift is **strictly non-positive**: $T_{\text{closed}}^{\text{causal}} - T_{\text{closed}}^{\text{retro}} \le 0.00\,\text{s}$.
  2. A forward-causal simulation can **never produce a larger closed duration** than retroactive stepping under uniform ticks.
  3. The error does not vary continuously across $[-0.20, +0.20]$. It is binary: $\delta \in \{0.00\,\text{s}, 0.20\,\text{s}\}$.
- **Corrected Mathematical Bound:**
  $$T_{\text{closed}}^{\text{causal}} = T_{\text{closed}}^{\text{Table 11}} - \delta, \quad \delta \in \{0.00\,\text{s}, 0.20\,\text{s}\}$$
  $$\mathbf{T_{\text{closed}}^{\text{causal}} \in [T_{\text{closed}}^{\text{Table 11}} - 0.20\,\text{s}, \; T_{\text{closed}}^{\text{Table 11}}]}$$

---

## 11. Measurement Interpretation and Terminology

1. **What Table 11 Actually Represents:**  
   The cumulative simulated time during which the virtual barrier boom was lowered to $\theta \le 45.0^\circ$ under Condition B4 (Full Multimodal Policy).
2. **What Table 11 Does NOT Represent:**  
   - It is **not** train presence or occupancy ($T_4 - T_2$).
   - It is **not** horizontal barrier closure ($\theta \le 0.05^\circ$).
   - It is **not** an empirical measurement of a physical grade crossing gate in Bangladesh.
3. **Recommended Terminology:**  
   In all manuscript tables and references, the column heading must be qualified as:  
   **`Simulated Passage-Blocked Time (s)`** ($\theta \le 45.0^\circ$).

---

## 12. Manuscript Exposure and Recommendations

### Document Status:
- In [`docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md), Table 11 is not embedded directly in the main text; it resides in `results/experiments/tables/table11_per_event_summary.md` as an exploratory artifact.
- Table 3 of the manuscript uses `Fraction Closed Duration (FCD)` (currently `[RESULTS PENDING]`).

### Formal Audit Recommendation:
**Option 2: Retain Table 11 with a Defensible Timing Bound and Qualification.**
- Table 11 should not be withdrawn. The maximum possible discrepancy for any event is a single tick ($0.20\,\text{s}$), which represents a tiny relative error ($< 1\%$ across all train events, e.g. $0.16\%$ for `event_006` @ $122.4\,\text{s}$, $0.43\%$ for `event_001` @ $46.0\,\text{s}$).
- An explanatory note must be appended to Table 11:
  > *"Note: Values represent simulated passage-blocked duration ($\theta \le 45.0^\circ$) under Condition B4 using Version 1.x simulation stepping. Under forward-causal actuation, values are bounded within $[T - 0.20\,\text{s}, T]$."*

---

## 13. Researcher Decision Register

The following formal decisions are submitted for Principal Investigator review:

1. **`DEC-C25` (Table 11 Measurement Interpretation):**  
   Formally approve the definition of Table 11 closed duration as *Simulated Passage-Blocked Duration* ($\theta \le 45.0^\circ$), prohibiting its description as train occupancy or fully horizontal closure. (Status: `PENDING`)
2. **`DEC-C26` (Table 11 Provenance & Qualification):**  
   Append a formal caption to Table 11 clarifying that the values reflect Condition B4 under Convention A (retroactive interval stepping). (Status: `PENDING`)
3. **`DEC-C27` (Discretization Bound Adoption):**  
   Adopt the mathematically proven one-sided discretization bound $T_{\text{causal}} \in [T_{\text{Table 11}} - 0.20\,\text{s}, T_{\text{Table 11}}]$, formally deprecating the unverified "$\pm 0.20\,\text{s}$" claim. (Status: `PENDING`)
4. **`DEC-C28` (Historical Recomputation Policy):**  
   Confirm that Table 11 values are retained as a qualified baseline for Version 1.x descriptive benchmarks, deferring forward-causal recomputation to Version 2.0 when rear-camera Stage-2.1 ground truth is promoted. (Status: `PENDING`)

---

## 14. Limitations

1. **Determining Exact $\delta$ per Event Requires Step Inspection:**  
   Without running real-data evaluation or parsing step logs (which are not saved to disk in `results/experiments/B4/`), distinguishing whether a specific event has $\delta = 0.00\,\text{s}$ or $\delta = 0.20\,\text{s}$ requires inspecting whether the gate had fully opened before the clip's final frame.
2. **Strict Read-Only Preservation:**  
   No simulation code was executed and no result files were modified during this audit.

---

## 15. Final Statutory Disposition

$$\mathbf{TABLE11\_DURATION\_VERIFIED\_WITH\_LIMITATIONS}$$

### Formal Justification:
1. **Provenance 100% Verified:** Every single value in Table 11 matches the primary source record in `results/experiments/B4/single_events.json` identically as an exact integer multiple of $0.20\,\text{s}$.
2. **Mathematical Bounds Established:** The forward-causal duration is rigorously bounded within $[T - 0.20\,\text{s}, T]$, disproving the loose symmetric $\pm 0.20\,\text{s}$ conjecture.
3. **Operational Limitations Documented:** Table 11 represents Condition B4 under Convention A retroactive stepping, measuring simulated passage-blocked time rather than physical train occupancy.

---

REAL-DATA EXECUTION: NOT AUTHORIZED.
