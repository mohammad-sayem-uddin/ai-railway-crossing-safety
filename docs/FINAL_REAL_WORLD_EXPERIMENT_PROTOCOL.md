# Final Real-World Experiment Protocol

## Multimodal Railway-Crossing Safety Architecture: Final Evaluation Design

**Document Version:** 8.0.0  
**Date:** 2026-10-09  
**Status:** FINAL MASTER PROTOCOL SPECIFICATION — AI-Assisted, Human-Verified Canonical Protocol  
**Authority:** This document supersedes `docs/REAL_WORLD_EXPERIMENT_PLAN.md`, `docs/EXPERIMENT_PROTOCOL_V2.md`, and legacy B0–B7 results in `docs/REAL_WORLD_EXPERIMENT_REPORT.md`.

---

## 1. Objective & Research Question

Determine whether the proposed multimodal, two-camera, audio-assisted, temporally persistent, state-aware and conservative decision architecture improves event-level train detection reliability and reduces unsafe gate behaviour compared with systematically isolated simpler perception and decision strategies, on unseen real-world recorded conditions.

This is a software replay evaluation. It does not validate physical railway control, hardware actuation, safety certification, or field deployment.

### 1.1 Central Research Question

> On temporally aligned, event-labeled recordings from unseen real-world video recordings (captured across 1 or 2 physical crossing sites), does the predefined two-camera, audio-assisted, temporal state policy produce better event-level missed-train and premature-opening outcomes relative to fair baselines that each differ by exactly one architectural component?

---

## 2. Repository Audit Findings

Before designing this protocol, the entire repository was audited. The following critical discrepancies were identified and resolved:

### 2.1 CRITICAL: Audio Model Mismatch

| Item | Legacy Preliminary Run (Report V2.0) | Target Final Real-World System |
|---|---|---|
| **Audio checkpoint** | `models/audio/best_checkpoint.pt`<br>SHA-256: `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5`<br>(**Audio V2** — trained on custom negatives; 100% test accuracy) | `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`<br>SHA-256: `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`<br>(**Audio V3** — trained on ESC-50 hard negative confusers) |
| **Operating threshold** | $T^* = 0.5184$ | $T^* = 0.3700$ (Calibrated on Validation Fold 4) |
| **Data Firewall / Guard** | References V2 hash and V2 threshold | **Must reference V3 full SHA-256 and threshold 0.3700** |

> [!CAUTION]
> The `leakage_guard.py` constants currently point to Audio V2. Loading `models/audio/best_checkpoint.pt` or any checkpoint matching the Audio V2 SHA-256 is **strictly prohibited and must raise a fatal error**.

### 2.2 Ablation Design Weakness in Previous Experiment
The legacy B0–B4 matrix had three critical methodological flaws:
1. **B0 was an unrealistic strawman:** A single camera with single-frame thresholding without temporal filtering or dwell time.
2. **Multiple components changed simultaneously:** Camera count, temporal filtering, state machine, and audio were varied all at once between B0 and B4.
3. **B2 was stateless:** Comparing stateless B2 to stateful B4 conflated acoustic contribution with state-machine hysteresis.

### 2.3 Configuration Discrepancies
Authoritative operational values:
- Vision approach confidence: `0.35`
- Vision departure confidence: `0.35`
- Audio operating threshold: `0.3700`
- Temporal confirmation frames: `2` (0.4 s @ 5 Hz)
- Temporal EMA $\alpha$: `0.50`
- Temporal miss tolerance: `2` frames
- Clearance hold dwell time: `3.0 s`

---

## 3. Frozen Models

### 3.1 Vision Model — FROZEN
- Architecture: YOLOv8n (3,157,200 parameters)
- Checkpoint: `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`
- Full SHA-256: `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`
- Classes: 0 = front, 1 = rear, 2 = side
- Operating threshold: 0.35
- Training dataset: Dataset V1 (~3,157 images, development_fallback split). No claim of cross-crossing geographical generalization is supported by V1 development metrics.

### 3.2 Audio Model — FROZEN
- Architecture: `CompactTrainHornCNN` (25,697 parameters)
- Checkpoint: `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`
- Full SHA-256: `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`
- Operating threshold ($T^*$): **0.3700** (Calibrated strictly on Validation Fold 4; Val F1 = 0.9942)
- Input: 16,000 Hz mono PCM WAV, 64-band log-mel spectrogram ($N_{\text{fft}}=512$, hop $=256$, Hann window, $f_{\text{min}}=80\text{ Hz}$, $f_{\text{max}}=8000\text{ Hz}$, $\log(E+10^{-10})$)
- Tensor shape: `(64, 61)` per 1.0s window
- Normalization: $\mu_{\text{train}} = -1.6010, \sigma_{\text{train}} = 5.1240$
- Windowing: 1.0s window, 0.5s hop

---

## 4. Dataset Definition & Site Clustering

### 4.1 Layer B Real-World Evaluation Cohort (27 Events)
The evaluation cohort consists strictly of real-world video recordings from Layer B V2:
```
V2 Real-World Evaluation Cohort (27 Total Events)
├── Train Events Cohort (N = 23 paired events)
│   ├── 23 Full-Train Events (Front + Back cameras = 46 video streams)
│   └── Historical duplicate (old Event 010) explicitly quarantined
├── Negative Control Cohort (N = 3 events)
│   └── 3 No-Train Recordings (normal road/railway traffic; concurrent overlap unresolved)
└── Edge-Case Cohort (N = 1 event)
    └── 1 Engine-Only Event (short locomotive pass without railcars)
```

### 4.2 Crossing and Session Clustering Clarification
- **Geographic Reality:** The 27 recordings represent **only 1 or 2 distinct physical crossing sites** across a limited number of recording sessions.
- **Terminology Rule:** The evaluation cohort MUST be described as **"unseen real-world video recordings"**, NEVER as "held-out crossings" or "cross-site geographic validation".
- **Clustering:** Events recorded at the same crossing and session share camera angles, road geometry, background clutter, and lighting. They cannot be treated as statistically independent observations of global railway environments.

---

## 5. Canonical Train-Boundary Definitions ($T_0$ through $T_4$)

Reference: [`docs/FINAL_GROUND_TRUTH_PROTOCOL.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FINAL_GROUND_TRUTH_PROTOCOL.md) v6.0.0.

### 5.1 Canonical Boundary Table

| Marker | Canonical Name | Physical Definition | Camera Role | Safety Criticality |
|:---:|---|---|:---:|---|
| **$T_0$** | **First Visual Appearance** | Earliest frame train is visually identifiable approaching. (If train is already visible at recording start $t=0.00\text{s}$, candidate is recording-relative and excluded from physical latency denominator; see §5.3). | Front (Approach) | Baseline for Detection Latency ($T_{\text{detect}} - T_0$). Subject to left-censoring rules. |
| **$T_1$** | **Danger Zone Entry** | Earliest frame locomotive front bumper crosses into road danger zone. | Front (Approach) | Baseline for Warning Lead Time ($T_1 - T_{\text{detect}}$). |
| **$T_2$** | **Crossing Occupancy Start** | Earliest frame locomotive fully occupies road danger zone. | Front / Back | Road crossing danger zone is actively blocked. |
| **$T_3$** | **Locomotive Unit Clearance (rear end exits danger zone)** | Frame where trailing edge / rear coupler of leading locomotive unit(s) clears danger zone boundary while railcars continue. | Back (Departure) | **Diagnostic Marker:** Tests detector continuity from locomotive to cars. Distinguishes lead unit clearance from intermediate front exit. |
| **$T_4$** | **Tail Clearance (Last Vehicle Exit)** | Frame where final railcar trailing edge completely exits danger zone. | Back (Departure) | **Primary Safety Boundary:** End of physical road hazard. Baseline for POR and Clearance Latency. |
| **$T_{\text{scene\_clear}}$** | **Scene Clear** | Earliest frame train completely vacates all camera views. | Both Cameras | Scene verification; optical recovery. |
| **$T_{\text{horn}}$** | **Acoustic Horn Onset** | Earliest timestamp of audible horn sound on audio track. | Embedded Audio | Acoustic warning lead-time baseline. |

### 5.2 Physical Hazard Interval and Metric Formulas
- **Physical Boundary Distinction (Front Exit vs. Unit Clearance):**
  - When the locomotive traverses the crossing, the front bumper exiting the danger zone is an intermediate crossing state during traversal and does **not** constitute locomotive clearance.
  - Complete **Locomotive Unit Clearance ($T_3$)** occurs strictly when the *trailing edge / rear coupler* of the leading locomotive unit clears the danger zone.
  - **Tail Clearance ($T_4$):** Strictly preserved for the trailing edge of the *final vehicle* of the consist.
- **Physical Hazard Occupancy:** The crossing danger zone is actively blocked during:
  $$t \in [T_1, T_4]$$
- **Premature Opening Rate (POR):** Any gate opening commanded while $t < T_4$ (and $t \ge T_1$).
  - *Diagnostic Isolation:* Gate opening between $T_3$ and $T_4$ directly measures detector dropout on trailing cars after locomotive departs. Events with unobservable $T_4$ are excluded from the denominator.
- **Clearance Latency:** Delay from physical tail clearance to gate opening:
  $$\text{Clearance Latency} = T_{\text{open}} - T_4$$
- **Engine-Only Event ($N=1$):** Because an engine-only train has no trailing railcars:
  $$T_3 \equiv T_4 \quad (\text{Locomotive Unit Clearance} \equiv \text{Tail Clearance})$$

### 5.3 Left-Censored $T_0$ Metric Rules

When a train is already present and advancing at recording start ($t = 0.00\,\text{s}$, e.g. `event_001`):
1. **Left-Censored Reality:** Physical onset occurred at $T_{0,\text{physical}} \le 0.00\,\text{s}$.
2. **Detection Latency Denominator Rule:** True physical detection latency ($T_{\text{detect}} - T_{0,\text{physical}}$) cannot be measured. Such events **MUST BE EXCLUDED** from the true physical detection-latency denominator (`not_evaluable` / `left_censored`).
3. **Lower-Bound Exception:** Any reporting of observed latency against $0.00\,\text{s}$ must be explicitly labeled as an exploratory right-censored / lower-bound metric with prominent disclosure, never pooled into standard latency statistics.

### 5.4 Crossing Geometry Landmark Separation (Prerequisite R03)

Visual landmarks (turnout frog for $T_1$, camera transverse plane for $T_2$, vendor cart line for $T_4$) are provisional reference points, not certified physical boundaries. Equating visual landmarks with formal danger-zone boundaries without surveyed evidence under Prerequisite R03 is strictly prohibited. All such candidate timestamps remain provisional with `ambiguity_flag: true`.

---

## 6. AI-Assisted, Human-Verified Ground Truth Validation

Ground truth creation follows the three-stage lifecycle defined in `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` §1:
1. **AI Proposal Stage (Gemini Offline Assistant):** Ingests raw video and audio to propose candidate timestamps, horn classifications, and ambiguity notes into `data/ground_truth/proposals/`. AI proposals are immutable drafts.
2. **Human Verification Stage (Researcher):** Qualified researcher inspects raw frames and audio, verifies/corrects every boundary, records decisions in `data/ground_truth/reviews/`, and signs off.
3. **Approved Ground Truth Stage:** Files in `data/ground_truth/{train_events,no_train_events,engine_events}/` must carry `"approval_status": "APPROVED"` and valid SHA-256 hashes matching `data/ground_truth/ground_truth_manifest.json` (Prerequisite R02).

**Anti-Leakage Firewall:** The AI annotation assistant (Gemini) is strictly an offline annotator and must NEVER access, ingest, or condition labels upon YOLO predictions, Audio V3 inferences, state machine decisions, or legacy evaluation results.

Validation in `GroundTruthLoader` must be strictly aware of event type and fail fast on incomplete or unapproved data:
1. **Full-Train Events ($N=23$):** Timestamps $T_0$ through $T_4$ and $T_{\text{scene\_clear}}$ are evaluated. If any boundary cannot be observed, it must be marked `observable: false`, `not_evaluable: true`, with mandatory `reason`. Events with unobservable $T_4$ are excluded from POR and clearance latency denominators.
2. **No-Train Events ($N=3$):** All train timestamps ($T_0$–$T_4$, $T_{\text{scene\_clear}}$) are **`applicable: false`** (`value_s: null`). Validation MUST NOT require train timestamps for negative recordings. Activity logs and exact exposure durations are required.
3. **Engine-Only Event ($N=1$):** Trailing railcars count is `applicable: false` (or 0). $T_3$ and $T_4$ are coincident ($T_3 \equiv T_4$).
4. **Fail-Fast Ingestion Enforcement:** Evaluation immediately halts if any file is missing, unapproved, fails checksum validation, or is an unreviewed draft.

---

## 7. Camera Alignment Protocol

1. **No Assumed Uncertainties:** Blanket assumptions (e.g. $\pm 0.033\text{s}$ or $\pm 0.1\text{s}$) are prohibited.
2. **Per-Event Measured Offset:** $\Delta t = t_{\text{back}} - t_{\text{front}}$ and justified uncertainty $\delta$.
3. **Alignment Status Eligibility:**
   - `aligned` ($\delta \le 0.5\text{s}$): Eligible for all cross-camera temporal metrics.
   - `partially_aligned` ($0.5\text{s} < \delta \le 2.0\text{s}$): Eligible for event-level detection; latencies reported with error bounds.
   - `unaligned` ($\delta > 2.0\text{s}$ or unmeasured): **Strictly excluded** from joint Warning Lead Time and Clearance Latency metrics.

---

## 8. Redesigned Experiment Matrix: Single-Component Ablations (E1–E7)

| ID | Condition Name | Cameras | Temporal Filter | State Machine | Audio V3 ($T^*=0.37$) | Primary Purpose / What It Isolates |
|---|---|---|---|---|---|---|
| **E1** | Single-Cam Naive | Front only | None (`confirm=1`) | None (Stateless) | Disabled | Lower-bound baseline (legacy B0 equivalent) |
| **E2** | Single-Cam Temporal | Front only | Active (`confirm=2`, EMA) | None (Stateless) | Disabled | **Isolates temporal smoothing on single view** ($E_2 - E_1$) |
| **E3** | Dual-Cam Naive | Front + Back | None (`confirm=1`) | None (Stateless) | Disabled | **Isolates spatial camera redundancy** ($E_3 - E_1$) |
| **E4** | Dual-Cam Temporal | Front + Back | Active (`confirm=2`, EMA) | None (Stateless) | Disabled | **Isolates combined spatiotemporal baseline** ($E_4 - E_2$, $E_4 - E_3$) |
| **E5** | Dual-Cam State-Aware | Front + Back | Active (`confirm=2`, EMA) | Active (FSM + Hysteresis) | Disabled | **Directly isolates Crossing State Machine** ($E_5 - E_4$) |
| **E6** | Multimodal Stateless | Front + Back | Active (`confirm=2`, EMA) | None (Stateless) | Active | **Isolates audio contribution without state FSM** ($E_6 - E_4$) |
| **E7** | **Full Architecture** | Front + Back | Active (`confirm=2`, EMA) | Active (FSM + Hysteresis) | Active | **Full Proposed System; isolates audio synergy** ($E_7 - E_5$) |

### Supplementary Conditions (E8–E10)
- **E8:** Standalone Acoustic Baseline (Warning authority only; INV-1 verification).
- **E9a–c:** Sensor dropout matrix (Camera 1 loss, Camera 2 loss, Dual camera loss).
- **E10a–g:** System robustness perturbations (correlated repeated-measures stress tests).

---

## 9. Train-Event Evaluation (23 Full-Train Events)
- Evaluated across the 23 paired full-train events (46 video files).
- Native video playback sampled at 5.0 Hz.
- Primary safety endpoints: Missed Train Rate (MTR) and Premature Opening Rate (POR).

---

## 10. Engine-Only Event ($N=1$)
- Evaluated as an isolated qualitative edge-case study (`engine_event_001`).
- Assesses whether a short locomotive pass without trailing cars triggers proper occupancy tracking.
- Evaluates $T_3 \equiv T_4$ transition behavior. Reported in a dedicated Case Study section.

---

## 11. No-Train Negative Exposure & Nuisance-Alarm Counting

### 11.1 Physical File Exposure Audit
Video container analysis of `data/raw/layer_b/v2/no_train_events/`:
- `event_001`: Front = 24.635s, Back = 24.422s
- `event_002`: Front = 11.877s, Back = 13.333s
- `event_003`: Front = 23.788s, Back = 22.733s
- **Individual Camera Stream Totals:** Front: 60.300s, Back: 60.488s.
- **Total Stream Exposure ($T_{\text{sensor}}$):** **120.788 camera-stream-seconds** (sum of all 6 individual streams).

> [!WARNING]
> **Concurrent Overlap Is Unresolved.** The previous formula `min(front, back)` yielding 59.032s assumes the shorter stream is fully contained within the longer on a shared timeline. However, creation-time metadata across the front and back cameras shows dates on different days (e.g., event_001: front = 2026-10-06, back = 2026-10-04), indicating container timestamps are unreliable for establishing recording start offsets. No measured inter-camera temporal offset ($\Delta t$) exists for any no-train event. Until per-event offset measurements are completed (Prerequisite **R04**), the true concurrent overlap **cannot be determined**.
>
> **Usable denominators:** Per-camera stream durations and aggregate stream exposure ($T_{\text{sensor}} = 120.788\text{ s}$) are directly measured from video containers and are reliable. They must be used as the primary reporting denominators. If concurrent overlap is later resolved, it may be reported as a secondary denominator.

### 11.2 Multi-Level Nuisance Counting Rules
Evaluator reports three distinct metrics from completed replay:
1. **Camera-Level False Detections ($N_{\text{cam\_FP}}$):** Unaggregated frame count exceeding threshold per camera stream.
2. **Acoustic False Detections ($N_{\text{audio\_FP}}$):** Count of 1.0s audio windows with $p_{\text{audio}} \ge 0.3700$ in no-train audio.
3. **System Nuisance Episodes ($N_{\text{nuisance\_episodes}}$):** Contiguous episodes where fused system triggered false warning or gate closure.
- **Reporting Rule:** Primary metric is observed raw counts and per-stream durations. All nuisance counts ($N_{\text{cam\_FP}}$, $N_{\text{audio\_FP}}$, $N_{\text{nuisance\_episodes}}$) are populated exclusively from completed evaluation replay — never predetermined. Extrapolated hourly rates must be labeled: **"Exploratory pilot extrapolation under ≈120.8 stream-seconds exposure; highly uncertain."**

---

## 12. Audio V3 Real-World Evaluation & Authority Boundaries

### 12.1 Explicit Decision Authority Boundaries
- **Warning / Closing Authority:** Confirmed acoustic horn detection ($p_{\text{audio}} \ge 0.3700$) CAN trigger `IDLE` $\to$ `APPROACHING` and transition to `CLOSING` if sustained.
- **ZERO Clearance Authority (INV-1):** Acoustic evidence CANNOT trigger `OCCUPIED` $\to$ `CLEARING`, `CLEARING` $\to$ `IDLE`, or `CLOSED` $\to$ `OPENING`. Audio silence does NOT imply crossing clearance.
- **Nuisance Logging:** Evaluates whether passing road vehicles, horns, or engine rumbles trigger false acoustic warnings.

---

## 13. State Machine Evaluation
Evaluates transition legality, dwell time enforcement, and state progression:
$$\text{IDLE} \longrightarrow \text{APPROACHING} \longrightarrow \text{OCCUPIED} \longrightarrow \text{CLEARING} \longrightarrow \text{IDLE}$$

---

## 14. Temporal Evidence Evaluation
Evaluates EMA smoothing ($\alpha = 0.50$), 2-frame confirmation, and 2-frame miss tolerance in suppressing single-frame false negatives and false positives.

---

## 15. Safety Verification Architecture: Three-Tiered Separation
- **Tier 1 (Software Unit Invariants):** Automated tests in `tests/test_safety_invariants.py` verify mathematical safety rules (INV-1 to INV-8) on synthetic harness inputs.
- **Tier 2 (Real-World Observational Replay):** Natural unperturbed recordings (23 full-train, 3 no-train, 1 engine-only).
- **Tier 3 (Controlled Synthetic Fault Injection):** Repeated software perturbations (E9a–c, E10a–g). Formally treated as **correlated repeated-measures stress tests**, NOT independent field events.

---

## 16. Formal Safety Invariants (INV-1 through INV-8)

- **INV-1 (Acoustic Clearance Prohibition):** Gate clearance ($T_{\text{open}}$) shall never occur on audio evidence alone.
- **INV-2 (Single-Modality Warning):** Confirmed vision OR confirmed audio can initiate Warning/Closing.
- **INV-3 (Zero Premature Clearance):** Gate shall not open while train occupies crossing danger zone ($t \in [T_1, T_4]$).
- **INV-4 (Monotonic State Safety):** State transitions must follow legal directed graph paths.
- **INV-5 (Minimum Clearance Hold):** Gate clearance hold-time must satisfy $t_{\text{hold}} \ge 3.0\text{s}$ after $T_4$.
- **INV-6 (Dynamic Re-Approach Abort):** Train detection during opening phase must immediately command `CLOSED`.
- **INV-7 (Chatter Boundedness):** Gate direction reversals bounded to $\le 1$ cycle per event.
- **INV-8 (Fail-Safe on Total Blackout):** Total visual sensor loss must trigger immediate fail-safe gate closure.

---

## 17. Fusion Conflict Analysis
Classifies episodes where visual and acoustic modalities disagree:
- Vision Positive, Audio Negative: Train visible but silent (vision maintains gate closure).
- Vision Negative, Audio Positive: Horn audible before visual arrival (provides advance warning lead time).
- Nuisance Acoustic Conflict: Spurious audio detection during no-train recording.

---

## 18. Primary and Secondary Safety Endpoints
- **MTR:** Percentage of evaluable events where gate failed to close by $T_1$. (Goal: 0.0%).
- **POR:** Percentage of evaluable events where gate opened while $t < T_4$ (and $t \ge T_1$). (Goal: 0.0%).
- **Detection Latency:** $T_{\text{detect}} - T_0$.
- **Warning Lead Time:** $T_1 - T_{\text{detect}}$.
- **Clearance Latency:** $T_{\text{open}} - T_4$.
- **Excess Closed Duration:** Gate closed time minus physical occupancy time ($T_4 - T_1$).
- **Gate Chatter Count:** Open/close reversals per event.

---

## 19. Statistical Analysis Plan
- Primary analysis unit: train-passage event ($N=23$).
- Planned tests: McNemar's exact test for binary proportions; Wilcoxon signed-rank test for latencies. Significance is not guaranteed a priori.
- Wilson 95% CIs reported with documented site clustering caveat.
- Achieving $0/23$ failures yields Wilson 95% CI $[0.0\%, 14.3\%]$ under independence; does not prove 100% safety.

---

## 20. Crossing and Session Dependence
Document `crossing_id` and `session_id` for every event. Shared camera geometry across sessions limits claims of environmental invariance.

---

## 21. No-Train Negative Analysis (Detailed Protocol)
Quantifies visual and acoustic false alarms on road traffic across 120.8 camera-stream-seconds (concurrent overlap unresolved; see §11.1). Reports unaggregated camera counts and system nuisance episodes.

---

## 22. Publication Figures Plan (12 Figures)
1. Architecture Overview
2. E1–E7 Ablation Matrix
3. Audio V3 Compact CNN & ESC-50 Selectivity
4. Crossing Danger Zone & $T_0$–$T_4$ Markers
5. FSM Transition Graph & Invariant Boundaries
6. Event-Level MTR & POR across Ablations
7. Warning Lead Time Distributions
8. Clearance Latency vs Excess Closed Duration
9. Fusion Conflict Temporal Trace
10. No-Train Exposure Trace on Road Traffic
11. Engine-Only Case Study ($T_3 \equiv T_4$)
12. Synthetic Fault Resilience Profiles

---

## 23. Publication Tables Plan (12 Tables)
1. Cohort Composition & Site Clustering
2. Frozen Model Checkpoints & Hashes
3. Single-Degree-of-Freedom Matrix
4. Primary Endpoints (MTR & POR with Wilson CIs)
5. Timing Metrics (Lead Time, Latencies, Chatter)
6. Planned Hypothesis Tests & Effect Sizes
7. Audio V3 Selectivity on Native Audio
8. No-Train Exposure & Raw Nuisance Counts
9. Engine-Only Case Study Metrics
10. Safety Invariant Verification (Tiers 1–3)
11. Synthetic Fault-Injection Outcomes
12. Methodological Comparison: Legacy vs Final Protocol

---

## 24. Supported and Unsupported Claims
- **Supported:** Feasibility; state-machine elimination of premature openings; acoustic warning lead time; software fail-safe resilience.
- **Unsupported:** Cross-site geographic generalization; certified zero-failure safety; commercial false-alarm rate; adverse weather robustness; physical hardware certification.

---

## 25. Reproducibility Requirements
All models, configs, ground-truth JSONs, and scripts must be bitwise verifiable via SHA-256 manifests. Single entry-point execution.

---

## 26. Final Execution Order (22 Steps)
```
1. Verify Video Checksums
2. Verify AI-Assisted, Human-Verified Ground Truth Annotations & Manifest (R01, R02)
3. Freeze Checkpoints (YOLO & Audio V3)
4. Freeze Operational Parameters in leakage_guard.py
5. Verify Measured Camera Alignment Records
6. Run No-Train Baselines (E1–E7)
7. Run Naive Baselines (E1, E3)
8. Run Temporal Baselines (E2, E4)
9. Run State-Aware Vision Baseline (E5)
10. Run Stateless Multimodal Baseline (E6)
11. Run Full Proposed Architecture (E7)
12. Run Standalone Acoustic Baseline (E8)
13. Run Engine-Only Case Study (N=1)
14. Run Synthetic Fault Injections (E9–E10)
15. Verify Safety Invariants (Tiers 1–3)
16. Compute Statistical Metrics & Wilson CIs
17. Compute No-Train Exposure & Nuisance Counts
18. Generate 12 Publication Tables
19. Generate 12 Publication Figures
20. Compile Final Report
21. Conduct Reproducibility Audit
22. Permanently Freeze Evaluation Artifacts
```

---

## 27. Methodological Self-Critique (12 Core Inquiries)
1. Weaknesses fixed: Clean ablations; Audio V3 ESC-50 negatives; negative controls; canonical $T_0$–$T_4$ boundaries; 3-tier safety separation.
2. Weaknesses remaining: Small sample ($N=23$); ≈120.8 stream-seconds negative exposure (concurrent overlap unresolved); single engine pass; 1–2 crossing sites; smartphone replay.
3. Cohort sufficiency: Defensible as pilot study; insufficient for commercial certification.
4. No-train sufficiency: Insufficient for operational false-alarm rate estimation.
5. Statistically supported conclusions: Large effect sizes in POR reduction; planned paired differences in lead time.
6. Descriptive conclusions: Night stratum ($N=3$); engine-only pass ($N=1$); negative false-alarm rate; cross-site invariance.
7. Ablation power: Clean single-component attribution.
8. Leakage prevention: Pre-evaluation parameter and manifest freeze.
9. Synthetic vs real: Segregated across Tier 2 and Tier 3.
10. Highest value data: Multi-hour negative video; additional geographic sites; adverse weather.
11. Supportive pattern: E7 achieves 0 MTR, 0 POR; E1/E3 show premature openings; E5 eliminates them; E7 adds lead time; invariants hold.
12. Non-supportive pattern: E4 eliminates premature openings without FSM; E7 adds no lead time; Audio V3 causes frequent false closures.

---

## 28. Implementation Handoff for Gemini 3.8 Flash

### 28.1 Researcher Prerequisites (Before Execution) — All Currently INCOMPLETE (NO-GO)
- **R01 (AI-Assisted Annotation & Human Approval) — INCOMPLETE:** For all 27 events (23 train, 3 no-train, 1 engine), candidate annotations must be generated by Gemini into `data/ground_truth/proposals/`, manually verified and corrected frame-by-frame by the human researcher with audit records in `data/ground_truth/reviews/`, and certified with `"approval_status": "APPROVED"` in `data/ground_truth/`. Currently, no ground-truth files exist in `data/ground_truth/`.
- **R02 (Cryptographic Manifest Freeze) — INCOMPLETE:** Researcher freezes `data/ground_truth/ground_truth_manifest.json` locking SHA-256 hashes of all 27 approved ground-truth files, 27 review logs, and 27 raw proposals. Currently, no manifest exists.
- **R03 (Crossing Geographic & Alignment Documentation) — INCOMPLETE:** Researcher documents crossing geographic landmarks, physical road boundaries, and measured camera alignments for all sessions. Currently, no landmark, boundary, or geometry documentation exists in the repository.
- **R04 (Inter-Camera Offset for No-Train Events) — INCOMPLETE:** Researcher measures inter-camera temporal offset ($\Delta t$) for each no-train event using audio cross-correlation, visual landmark, or other justified method. Record offset, uncertainty, and method in each no-train ground-truth JSON. Without R04, concurrent overlap denominators remain unresolved and must not be used.

### 28.2 Implementation Tasks for Gemini 3.8 Flash
- **T01 (P0):** Update `leakage_guard.py` to Audio V3 (full SHA-256: `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`), threshold `0.3700`, and hard-block Audio V2 hash `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5`.
- **T02 (P0):** Implement `GroundTruthLoader` supporting event-type-aware validation (full-train vs no-train vs engine-only), verifying `"approval_status": "APPROVED"`, asserting full 64-character SHA-256 against `ground_truth_manifest.json`, and failing fast on unreviewed proposals, placeholders, or missing files.
- **T03 (P0):** Export `configs/frozen_parameters_v3.json`.
- **T04 (P0):** Implement condition filters for E1 through E7 in `runner.py`.
- **T05 (P0):** Orchestrate master evaluation pipeline `run_final_real_world_evaluation.py`.
- **T06 (P0):** Compute event metrics against canonical boundaries ($T_0$–$T_4$).
- **T07 (P0):** Compute no-train metrics with per-stream exposure reporting and multi-level counts (concurrent overlap pending R04).
- **T08 (P0):** Implement Tier 1 unit invariant test suite `tests/test_safety_invariants.py`.
- **T09 (P1):** Generate publication tables and figures.

---

## 29. Document Change Log

| Version | Date | Changes Made |
|---|---|---|
| 4.0.0 | 2026-10-09 | Methodological correction pass: Resolved crossing clustering terminology; enforced anti-synthesis ground truth integrity and `not_evaluable` schema; established 59s no-train exposure caveats; decoupled planned statistics from promised significance; clarified Audio V3 authority boundaries; established 3-tier safety verification; specified full Audio V3 SHA-256 and anti-V2 firewall. |
| 5.0.0 | 2026-10-09 | Canonical Train-Boundary Harmonization Pass: Resolved T0–T4 definitions with T3 as Locomotive Head Exit and T4 as Tail Clearance (Final Vehicle Clearance); established physical hazard interval $[T_1, T_4]$; defined clearance latency as $T_{\text{open}} - T_4$; integrated event-type-aware validation matrix (Full-Train vs No-Train vs Engine-Only); audited no-train file durations (59.03s concurrent overlap, 120.79s combined stream-seconds); established multi-level nuisance alarm counting rules. |
| 6.0.0 | 2026-10-09 | Exposure & Nuisance Integrity Pass: (1) Concurrent overlap reclassified as UNRESOLVED — creation-time metadata shows different dates across paired cameras, no measured offset exists; per-stream exposure (120.788 stream-seconds) is the reliable denominator. (2) All predetermined nuisance counts (`N_episodes = 0`) removed; evaluator must populate from completed replay. (3) Prerequisite R04 added: researcher must measure inter-camera temporal offset for no-train events. (4) Horn ground-truth schema updated: replaced legacy `horn_audible` with canonical `horn_status` enum (`present`, `absent_observed`, `unobservable`) and `horn_not_applicable` flag for no-train events. |
| 7.0.0 | 2026-10-09 | AI-Assisted Ground-Truth Methodology Pass: Formally integrated the three-stage annotation lifecycle (AI proposal → human frame-by-frame review → approved ground truth); established anti-leakage firewall separating annotation assistant from evaluated YOLO/Audio/FSM systems; preserved immutable proposals and human review logs; updated R01 (AI-assisted annotation & human approval) and R02 (manifest freeze of approved files, reviews, and proposals); enforced loader fail-fast on unreviewed drafts. |
| 8.0.0 | 2026-10-09 | Canonical Terminology & Left-Censoring Harmonization Pass: Resolved T3 canonical name as **Locomotive Unit Clearance (rear end exits danger zone)** with explicit physical definition (trailing edge of lead motive power clears danger zone while railcars continue); distinguished locomotive front exit during traversal from complete unit clearance; preserved T4 as tail clearance of final vehicle; established left-censored $T_0$ definition and detection latency denominator exclusion; reinforced provisional status of visual landmarks under Prerequisite R03; preserved proposal draft history v1–v4 with schema compatibility mapping. |
