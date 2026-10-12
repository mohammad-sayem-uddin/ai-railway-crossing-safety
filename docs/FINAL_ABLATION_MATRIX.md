# Final Ablation Matrix & Experimental Taxonomy

**Document Version:** 6.0.0  
**Date:** 2026-10-09  
**Status:** REFERENCE SPECIFICATION — Reconciled with Ground Truth v6.0.0 & Protocol v8.0.0  
**Companion to:** `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`

---

## 1. Primary Ablation Design Rationale

In the preliminary evaluation (Report V2.0, B0–B7), baseline B0 (Single-Cam Naive) to B4 (Full Multimodal) changed four architectural variables simultaneously:
1. Camera count (1 → 2)
2. Temporal persistence / EMA filtering (None → Active)
3. Crossing state machine & conservative hysteresis (None → Active)
4. Acoustic train-horn detection & multimodal fusion (None → Active)

This conflated the individual contributions of these subsystems. Specifically, the elimination of premature gate openings could not be definitively attributed to audio fusion versus the crossing state machine. 

The redesigned **E1–E7 matrix** establishes a clean single-degree-of-freedom progression where each step isolates exactly one component.

---

## 2. Core Experiment Matrix (E1–E7)

| Experiment ID | Condition Name | Camera Channels | Temporal Filtering | State Machine | Audio Modality ($T^*=0.3700$) | Primary Architectural Role |
|---|---|---|---|---|---|---|
| **E1** | Single-Cam Naive | Front only (Cam 1) | None (`confirm=1`) | None (Stateless) | Disabled | Lower-bound baseline (analogous to legacy B0) |
| **E2** | Single-Cam Temporal | Front only (Cam 1) | Active (`confirm=2`, EMA) | None (Stateless) | Disabled | Evaluates temporal smoothing on single stream ($E_2 - E_1$) |
| **E3** | Dual-Cam Naive | Front + Back | None (`confirm=1`) | None (Stateless) | Disabled | Evaluates spatial redundancy without temporal logic ($E_3 - E_1$) |
| **E4** | Dual-Cam Temporal | Front + Back | Active (`confirm=2`, EMA) | None (Stateless) | Disabled | Evaluates spatial + temporal without state machine ($E_4 - E_2$, $E_4 - E_3$) |
| **E5** | Dual-Cam State-Aware | Front + Back | Active (`confirm=2`, EMA) | Active (FSM + Hysteresis) | Disabled | Isolates crossing state machine & conservative dwell ($E_5 - E_4$) |
| **E6** | Multimodal Stateless | Front + Back | Active (`confirm=2`, EMA) | None (Stateless) | Active (Audio V3, $T^*=0.37$) | Evaluates audio fusion without state-machine hysteresis ($E_6 - E_4$) |
| **E7** | **Full Proposed System** | Front + Back | Active (`confirm=2`, EMA) | Active (FSM + Hysteresis) | Active (Audio V3, $T^*=0.37$) | Evaluates the full integrated safety architecture ($E_7 - E_5$) |

---

## 3. Canonical Boundary Definitions & Safety Metrics

Reference: [`docs/FINAL_GROUND_TRUTH_PROTOCOL.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FINAL_GROUND_TRUTH_PROTOCOL.md) v6.0.0 (AI-Assisted, Human-Verified Ground-Truth Architecture).

### 3.1 Boundary Definitions
- **$T_0$:** First Visual Appearance (train approaching). If train is already in frame at recording start ($t=0.00\text{s}$, e.g. `event_001`), the event is left-censored and excluded from physical latency calculations.
- **$T_1$:** Danger Zone Entry (locomotive front bumper enters road danger zone).
- **$T_2$:** Crossing Occupancy Start (crossing road actively blocked).
- **$T_3$:** Locomotive Unit Clearance (rear end exits danger zone; trailing edge / rear coupler of lead locomotive unit clears danger zone while railcars continue traversing). Note: Intermediate front-bumper exit during traversal does not constitute locomotive clearance.
- **$T_4$:** Tail Clearance / Final Vehicle Clearance (last railcar of entire consist completely exits danger zone).
- **$T_{\text{scene\_clear}}$:** Scene Clear (train completely out of view).
- **$T_{\text{horn}}$:** Acoustic Horn Onset.
- **Engine-Only Event ($N=1$):** $T_3 \equiv T_4$ (Locomotive Unit Clearance $\equiv$ Tail Clearance).

### 3.2 Safety Endpoint Formulas
1. **Missed Train Rate (MTR):** Percentage of evaluable train events where gate failed to close by $T_1$. (Safety Goal: 0.0%).
2. **Premature Opening Rate (POR):** Percentage of evaluable events where gate opened while $t < T_4$ (and $t \ge T_1$).
   - *Diagnostic Isolation:* Gate opening between $T_3$ (Locomotive Unit Clearance) and $T_4$ (Tail Clearance) directly measures detector dropout on trailing cars after the locomotive departs. Events with unobservable $T_4$ are excluded from the denominator. (Safety Goal: 0.0%).
3. **Detection Latency:** $T_{\text{detect}} - T_0$.
   - *Left-Censoring Denominator Rule:* For events where the train is already visible at $t=0.00\text{s}$ (left-censored, e.g. `event_001`), true physical latency cannot be calculated. Such events are **excluded from the primary physical latency denominator** (`not_evaluable` / `left_censored`). Reporting of recording-relative latency ($T_{\text{detect}} - 0.00\text{s}$) is permitted only as an exploratory lower bound with explicit disclosure.
4. **Warning Lead Time:** $T_1 - T_{\text{detect}}$.
5. **Clearance Latency:** $T_{\text{open}} - T_4$. (Requires $T_{\text{open}} - T_4 \ge 3.0\text{s}$).

---

## 4. Pairwise Attribution Equations & Planned Statistical Contrasts

All contrasts are formulated as **planned empirical tests**; statistical significance is not guaranteed a priori. Proportions are reported with 95% Wilson confidence intervals, acknowledging that event clustering within 1 or 2 crossing sites reduces effective sample size below nominal $N=23$.

| Contrast | Subsystem Isolated | Mathematical Contrast | Planned Research Hypothesis | Expected Failure Mode if Subsystem Omitted |
|---|---|---|---|---|
| **Temporal on Single Stream** | Temporal Persistence | $\Delta_{\text{temporal}} = E_2 - E_1$ | Temporal smoothing buffers transient single-frame misses during transit. | Transient detector flicker causes gate chatter and premature opening mid-train. |
| **Camera Viewpoint Redundancy** | Dual Camera Coverage | $\Delta_{\text{cam}} = E_3 - E_1$ | Back camera maintains visual evidence during occlusion or departure blind spots. | Field-of-view exit causes early clearance before train fully vacates crossing. |
| **Joint Spatial + Temporal** | Spatiotemporal Baseline | $\Delta_{\text{spatiotemporal}} = E_4 - E_1$ | Dual views combined with temporal filtering outperform either in isolation. | Combined blind spots and detector fluctuation. |
| **Crossing State Machine** | Conservative FSM | $\Delta_{\text{state}} = E_5 - E_4$ | Explicit crossing phase tracking and holding dwell eliminates premature openings. | Stateless gate reopens whenever instantaneous/smoothed detection drops below threshold. |
| **Audio Fusion (Stateless)** | Acoustic Evidence | $\Delta_{\text{audio\_stateless}} = E_6 - E_4$ | Acoustic horn detection provides early warning before visual entry. | Visual occlusion delays gate activation; no acoustic confirmation. |
| **Full Architecture Synergy** | Multimodal + State | $\Delta_{\text{full}} = E_7 - E_5$ | Audio provides advance warning lead time while state machine enforces zero premature openings. | Warning lead time restricted strictly to camera line-of-sight visual onset. |
| **Necessity of State Machine** | FSM Necessity | $\Delta_{\text{state\_multimodal}} = E_7 - E_6$ | Audio fusion alone cannot replace state-machine hysteresis for safety clearance. | Gate reopens during quiet inter-horn intervals or visual occlusions. |

---

## 5. Controlled Standalone & Stress Conditions (E8–E10)

Safety evaluation is partitioned into three strictly segregated tiers:
- **Tier 1 (Software Unit Invariants):** Automated tests in `tests/test_safety_invariants.py` verify mathematical safety invariants (INV-1 to INV-8) on synthetic harness inputs.
- **Tier 2 (Real-World Observational Replay):** Natural unperturbed recordings (23 full-train, 3 no-train, 1 engine-only).
- **Tier 3 (Controlled Synthetic Fault Injection):** Repeated software perturbations of recorded events (E9a–c, E10a–g). These are **correlated repeated measures**, NOT independent real-world field events.

### 5.1 Standalone Acoustic Baseline (E8)
* **E8 (Audio-Only Baseline):** 
  * Acoustic model inference standalone on native real-world audio tracks.
  * Evaluates acoustic true positive rate, acoustic lead time, and false alarm rate on negative recordings.
  * Verifies Safety Invariant **INV-1** (Audio evidence alone can trigger Warning/Closing, but CANNOT authorize Clearance).

### 5.2 Fault-Injection & Robustness Matrix (Tier 3)
| Experiment ID | Fault Injected | Injection Point | Safety Invariant Tested | Expected Behavior |
|---|---|---|---|---|
| **E9a** | Cam 1 Dropout | Front camera loss at $t=0$ | INV-2, INV-8 | Fallback to Cam 2; safe closure maintained. |
| **E9b** | Cam 2 Dropout | Back camera loss at $t=0$ | INV-2, INV-8 | Fallback to Cam 1; safe closure maintained. |
| **E9c** | Dual Camera Loss | Total visual sensor blackout | INV-8 (`FAULT_FAIL_SAFE`) | Immediate fail-safe emergency gate closure. |
| **E10a** | Audio Loss | Full audio stream zeroed | INV-2, INV-4 | Vision-only fallback; safe closure via visual track. |
| **E10b** | Frame Degradation | 30% uniform random frame drop | INV-4, INV-7 | Temporal EMA absorbs dropout; zero premature openings. |
| **E10c** | Timestamp Disorder | Random out-of-order delivery | Monotonic time guard | Rejection of stale/disordered evidence packets. |
| **E10d** | Stale Timestamps | 2.0s evidence delay | Sensor health monitor | Stale sensor flagged; conservative fail-safe state. |
| **E10e** | False Positive Injection | Spurious front detection (conf=0.85) | INV-4, Temporal filter | Filter suppression if transient; safe state if persistent. |
| **E10f** | Compound Fault | Audio loss + 10% frame loss | Graceful degradation | Safe closure maintained; lead time reduced to visual baseline. |
| **E10g** | Dynamic Re-Approach | New train arrives during gate opening | INV-6 (Dynamic abort) | Gate aborts opening and immediately closes. |

---

## 6. No-Train Exposure Denominators & Nuisance Metrics

Evaluated across the 3 no-train negative control recordings:
- **Audited Denominators:**
  - Per-camera stream exposure: Front = 60.300s, Back = 60.488s.
  - Combined sensor stream exposure: **120.788 stream-seconds** (sum of 6 individual streams).
  - Concurrent wall-clock overlap: **UNRESOLVED** — no measured inter-camera offset exists for any no-train event; `min(front, back)` overlap formula is not valid without confirming temporal containment (see Prerequisite R04).
- **Multi-Level Nuisance Reporting:**
  1. Camera-level false frames on Camera 1 and Camera 2 unaggregated.
  2. Acoustic false windows ($p_{\text{audio}} \ge 0.3700$) on embedded audio.
  3. System nuisance warning / closure episodes ($N_{\text{nuisance\_episodes}}$) on fused state machine.
- **Data-Driven Mandate:** All nuisance counts are populated exclusively from completed evaluation replay — never predetermined. Zero is reported only when the evaluation observes zero.
- **Limitation Rule:** Per-stream durations are primary. Extrapolated hourly rates are flagged as exploratory pilot estimates with extreme uncertainty.

---

## 7. Ground Truth Dependency & Evaluation Integrity

Execution of evaluation replay across conditions E1–E10 strictly requires satisfaction of all four research prerequisites (R01 through R04), which are currently **INCOMPLETE (NO-GO)**:
1. **Certified Ground Truth (R01 — Incomplete):** Evaluation ingests exclusively Stage 3 approved ground truth (`data/ground_truth/{train_events,no_train_events,engine_events}/`) where `approval_status == "APPROVED"`. Ingestion of raw AI proposals (`data/ground_truth/proposals/`) is strictly prohibited.
2. **Cryptographic Integrity (R02 — Incomplete):** Hashes of all 27 approved ground truth files, review logs, and raw proposals must match `data/ground_truth/ground_truth_manifest.json`.
3. **Geographic Documentation (R03 — Incomplete):** Physical crossing boundaries and visual landmarks must be formally documented.
4. **Inter-Camera Synchronization (R04 — Incomplete):** Inter-camera temporal offsets for no-train events must be empirically measured before concurrent overlap denominators can be evaluated.
5. **Strict Decoupling:** Ground truth is created independently via raw sensor inspection; evaluated models (YOLO, Audio V3, FSM) have zero involvement in label generation.

---

## 8. Document Change Log

| Version | Date | Changes Made |
|---|---|---|
| 4.0.0 | 2026-10-09 | Methodological correction pass: Established E1–E7 single-DOF matrix; decoupled planned contrasts from guaranteed significance; integrated full 64-character SHA-256 validation; reinforced zero acoustic clearance authority (INV-1). |
| 5.0.0 | 2026-10-09 | AI-assisted ground-truth integration: Reconciled ablation matrix with Protocol v7.0.0 and Ground Truth v5.0.0; added multi-level nuisance reporting flow and R01–R04 gate enforcement. |
| 6.0.0 | 2026-10-09 | Canonical Terminology & Left-Censoring Harmonization Pass: Resolved T3 as **Locomotive Unit Clearance (rear end exits danger zone)**; distinguished locomotive front exit from complete unit clearance; preserved T4 as tail clearance; defined left-censored $T_0$ representation and detection latency denominator exclusion; documented schema key compatibility mapping (`T3_locomotive_unit_clearance` / `T3_locomotive_exit`) preserving proposals v1–v4; reinforced R03 visual landmark provisional status. |


