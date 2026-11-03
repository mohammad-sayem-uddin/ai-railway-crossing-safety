# Forensic Audit of Completed Full-Dataset Multimodal Fusion Experiment

**Audit Document Version:** 1.0.0  
**Audit Date:** 2026-10-13  
**Auditor:** Independent Antigravity Forensic Evaluation System  
**Audit Scope:** Independent forensic verification of reported full-dataset execution outputs, metrics, synchronization, invariants, and experimental validity across all 27 active Layer B events and B0–B7 benchmark conditions.  
**Preservation Notice:** All original run outputs, 141 cache records in `results/experiments/cache/`, 54 synchronized timeline files in `results/experiments/B4/timelines/`, and existing condition outputs in `results/experiments/{B0..B7f}/` are 100% preserved. No files have been overwritten or deleted.

---

## Executive Summary of Audit Findings

The latest report (`docs/REAL_WORLD_EXPERIMENT_REPORT.md`) claimed full-dataset execution across 27 active events, 23,759 vision frames, 4,741 audio windows, 865 acoustic detections, and universal 0.0% Missed-Train Rate (MTR) and 0.0% Premature-Opening Rate (POR) across all conditions B0 through B7.

An exhaustive forensic investigation of the underlying execution artifacts, code implementations, cache files, and container streams demonstrates that **the reported summary claims diverge significantly from actual system execution:**

1. **Inflated Frame and Window Counts via Orphaned Cache Contamination:**
   - Actual vision frames evaluated in the 27 active events total **13,086 frames** (not 23,759).
   - Actual vision detections emitted total **12,047 detections** (not 22,291).
   - Actual audio windows evaluated total **2,600 sliding windows** (not 4,741).
   - Actual positive acoustic horn detections at canonical threshold $T^* = 0.3700$ total **9 windows** (not 865).
   - **Root Cause:** The reported figures mathematically equal the exact sum of the 27 active event caches PLUS 40 orphaned vision cache files (10,673 frames, 10,244 detections) and 20 orphaned audio cache files (2,141 windows, 856 detections) from superseded historical runs that remained in `results/experiments/cache/`.

2. **Mechanism of Identical 0.0% MTR and 0.0% POR Across B0–B7:**
   - Because candidate ground-truth annotations in `data/ground_truth/proposals/` remain unapproved under the R01/R02 firewall, raw Layer B event bundles contained no ground-truth files (`labels/event_labels.json` was absent).
   - In `runner.py`, `entry_time_s` and `clearance_time_s` evaluated to `None` for all 27 events.
   - In `metrics.py`, `missed_train` silently defaulted to `False` whenever `entry_time_s is None`, and `premature_opening` was set to `None` (not evaluable).
   - In `generate_publication_tables.py`, when POR was `None`, a formatting fallback substituted `"0.0% [0.0%, 12.5%]"`.
   - In reality, in condition B0 (stateless vision), premature openings occurred in **21 out of 23 train events (91.3%)**; in B2 and B3, premature openings occurred in **17 out of 23 train events (73.9%)**.

3. **Nuisance Closures on Negative Controls Disguised as Perfect Performance:**
   - In `runner.py`, `has_train_ground_truth=True` was hardcoded across all 27 events, forcing the 3 negative controls (`no_train_events`) into the train passage cohort where they were scored as non-missed trains.
   - In reality, under the proposed B4 policy, the gate closed on **3 out of 3 negative control events (100% False Activation Rate)**, remaining unnecessarily closed for **39.0 seconds** (64.7% of the total 60.3-second negative control exposure) due to road traffic visual confounders misclassified as train frontal aspects.

4. **Critical Failure of Dual Camera Fail-Safe (B6b):**
   - The report claimed that under complete dual camera loss (B6b), the system transitioned into `FAULT_FAIL_SAFE` within 0.20s, locking the gate barrier closed.
   - In reality, the state machine rule required `prev_state not in (IDLE, FAULT_FAIL_SAFE)` to trigger `FAULT_FAIL_SAFE`. Because cameras were dropped from $t=0.0\text{s}$ while in `IDLE`, the system **stayed in `IDLE` with the gate `OPEN` (angle=90°) for the entire duration of all 27 events** (closed duration = 0.0s). Trains passed through the crossing while the gate remained completely open.
   - The claimed "0.20s fail-safe response" was derived from a synthetic unit test where a train approach was pre-injected into the state machine, and reflects the discrete simulation step size ($1 / 5\text{ FPS} = 0.20\text{s}$), not real-world hardware performance.

5. **Unexecuted Benchmark Conditions (B7b and B7f):**
   - Due to a logic error in `FailureInjector` (`drop_frame = any(s.mode == FailureMode.DROPPED_FRAMES)`), 100% of frames were dropped instead of 30% or 10%. Conditions B7b and B7f executed on empty frame lists (closed duration = 0.0s for all 27 events).

6. **Unresolved Inter-Camera Synchronization (R04):**
   - `SyncAligner` was not passed to `MultimodalEvidenceCollector`, resulting in a default zero offset ($0.0\text{s}$) between `camera_front.mov` and `camera_back.mov`. Front and back camera timelines are independently timed video containers without empirical genlock or TDOA calibration.

---

## 1. Full-Dataset Execution Coverage & Traceable Counts

### 1.1 Source Stream Accounting

Layer B v2 (`data/raw/layer_b/v2/`) comprises 28 event directories across three cohort folders:
- `train_events`: 23 directories (`event_001` to `event_023`).
- `no_train_events`: 3 directories (`event_001` to `event_003`).
- `engine_events`: 2 directories (`event_001` and `event_historical_duplicate_010`).

The historical duplicate `engine_events/event_historical_duplicate_010` (identical file content to `event_010`) was correctly excluded by `run_real_world_experiments.py` line 82, leaving **27 active evaluation events**.

Each active event directory contains exactly two video files: `camera_front.mov` (assigned as `camera_1`) and `camera_back.mov` (assigned as `camera_2`). Both video files contain embedded stereo/mono audio tracks.

- **Total active video streams:** 27 events × 2 cameras = **54 streams**.
- **Historical duplicate streams:** 1 event × 2 cameras = **2 streams** (excluded).
- **Total physical streams on disk:** **56 streams**.

### 1.2 Stream Execution Completeness & Video Skips

Of the 54 active source streams:
- **53 streams** were processed completely, decoding 100% of sampled frames at 5 FPS without skips or errors.
- **1 stream** (`train_events_event_010/camera_back.mov`) encountered container EOF truncation on its final two frames:
  ```
  failed to advance to frame 708 from data/raw/layer_b/v2/train_events/event_010/camera_back.mov; skipping
  failed to advance to frame 714 from data/raw/layer_b/v2/train_events/event_010/camera_back.mov; skipping
  ```
  The stream decoded 118 of 120 expected frames (98.3% completeness).
- **0 streams** failed or were skipped.

### 1.3 Event-by-Event Media Inventory Table

The following table documents the empirical ground truth for all 27 active evaluation events across both camera streams:

| Full Event Identifier | Cohort | Stream Durations (Front / Back) | Sampled Frames (5 FPS) | Skipped Frames | Audio Windows | Audio Detections ($T^*=0.3700$) | Vision Detections (Front/Side/Rear) | Processing Status |
|---|---|---|---|---|---|---|---|---|
| `engine_events_event_001` | `engine_events` | 8.0s / 9.8s | 89 | 0 | 15 | 0 | 22 (22/0/0) | Complete |
| `no_train_events_event_001` | `no_train_events` | 24.6s / 24.4s | 246 | 0 | 48 | 0 | 28 (28/0/0) | Complete |
| `no_train_events_event_002` | `no_train_events` | 11.9s / 13.3s | 127 | 0 | 22 | 0 | 60 (1/59/0) | Complete |
| `no_train_events_event_003` | `no_train_events` | 23.8s / 22.7s | 233 | 0 | 46 | 0 | 13 (12/0/1) | Complete |
| `train_events_event_001` | `train_events` | 49.6s / 46.8s | 483 | 0 | 98 | 0 | 437 (18/418/1) | Complete |
| `train_events_event_002` | `train_events` | 33.1s / 30.2s | 318 | 0 | 65 | 0 | 336 (20/314/2) | Complete |
| `train_events_event_003` | `train_events` | 32.8s / 28.1s | 306 | 0 | 65 | 0 | 300 (15/283/2) | Complete |
| `train_events_event_004` | `train_events` | 75.3s / 74.3s | 749 | 0 | 150 | 4 | 741 (48/683/10) | Complete |
| `train_events_event_005` | `train_events` | 79.1s / 78.1s | 787 | 0 | 158 | 0 | 799 (5/791/3) | Complete |
| `train_events_event_006` | `train_events` | 126.8s / 125.7s | 1,264 | 0 | 251 | 0 | 1,168 (46/1107/15) | Complete |
| `train_events_event_007` | `train_events` | 38.0s / 37.0s | 376 | 0 | 75 | 0 | 386 (44/339/3) | Complete |
| `train_events_event_008` | `train_events` | 58.4s / 57.3s | 580 | 0 | 116 | 0 | 545 (32/508/5) | Complete |
| `train_events_event_009` | `train_events` | 42.4s / 41.3s | 420 | 0 | 84 | 0 | 400 (45/347/8) | Complete |
| `train_events_event_010` | `train_events` | 7.0s / 24.3s | 154 | 2 (EOF) | 13 | 0 | 136 (12/123/1) | 2 Frames Skipped |
| `train_events_event_011` | `train_events` | 24.0s / 33.7s | 289 | 0 | 47 | 0 | 290 (20/266/4) | Complete |
| `train_events_event_012` | `train_events` | 37.4s / 36.3s | 370 | 0 | 74 | 0 | 362 (24/335/3) | Complete |
| `train_events_event_013` | `train_events` | 75.1s / 74.0s | 747 | 0 | 149 | 0 | 722 (38/676/8) | Complete |
| `train_events_event_014` | `train_events` | 73.4s / 72.3s | 730 | 0 | 146 | 0 | 694 (36/651/7) | Complete |
| `train_events_event_015` | `train_events` | 55.0s / 53.9s | 546 | 0 | 109 | 0 | 509 (41/461/7) | Complete |
| `train_events_event_016` | `train_events` | 31.0s / 29.8s | 305 | 0 | 61 | 0 | 291 (30/256/5) | Complete |
| `train_events_event_017` | `train_events` | 81.3s / 80.3s | 809 | 0 | 162 | 1 | 794 (51/731/12) | Complete |
| `train_events_event_018` | `train_events` | 58.5s / 57.5s | 581 | 0 | 116 | 4 | 558 (29/520/9) | Complete |
| `train_events_event_019` | `train_events` | 58.7s / 57.7s | 583 | 0 | 116 | 0 | 549 (34/507/8) | Complete |
| `train_events_event_020` | `train_events` | 60.1s / 59.1s | 597 | 0 | 119 | 0 | 569 (31/531/7) | Complete |
| `train_events_event_021` | `train_events` | 28.2s / 27.2s | 278 | 0 | 56 | 0 | 266 (25/236/5) | Complete |
| `train_events_event_022` | `train_events` | 36.9s / 35.8s | 364 | 0 | 73 | 0 | 338 (29/303/6) | Complete |
| `train_events_event_023` | `train_events` | 42.6s / 41.5s | 422 | 0 | 84 | 0 | 400 (37/357/6) | Complete |
| **Active Cohort Total (N=27)** | — | **1,320.2s / 1,294.8s** | **13,086** | **2** | **2,600** | **9** | **12,047 (716/11179/152)** | **53/54 100% Complete** |

### 1.4 Cache Accounting & Discrepancy Breakdown

The directory `results/experiments/cache/` contains 141 JSONL files. The forensic decomposition between active evaluation files and historical orphaned files is as follows:

| Cache Sub-Category | File Count | Record Count | Train Detections Emitted | Status in Experiment |
|---|---|---|---|---|
| **Active Vision Caches** (`{cohort}_{event}_*vision.jsonl`) | 54 | **13,086** | 12,047 (front: 716, side: 11,179, rear: 152) | Active Evaluation Data |
| **Historical Orphaned Vision Caches** (`event_0*vision.jsonl`) | 40 | **10,673** | 10,244 (front: 383, side: 9,747, rear: 114) | Superseded (Prior 20-Event Run) |
| *Sum of All Vision Caches in Directory* | *94* | ***23,759*** | ***22,291*** *(front: 1,099, side: 20,926, rear: 266)* | *Reported Value (Contaminated)* |
| **Active Audio Caches** (`{cohort}_{event}_audio_1_audio.jsonl`) | 27 | **2,600** | **9** positive windows ($T^*=0.3700$) | Active Evaluation Data |
| **Historical Orphaned Audio Caches** (`event_0*audio.jsonl`) | 20 | **2,141** | **856** positive windows (Audio V1/V2) | Superseded (Prior Run) |
| *Sum of All Audio Caches in Directory* | *47* | ***4,741*** | ***865*** *detections* | *Reported Value (Contaminated)* |

> [!CAUTION]
> **Definitive Accounting Proof:** The reported numbers of 23,759 vision frames, 22,291 vision detections, 4,741 audio windows, and 865 acoustic detections are the exact mathematical sum of active caches and orphaned cache artifacts from prior runs. The actual active execution comprised **13,086 vision frames** and **2,600 audio windows**.

---

## 2. Investigation of Identical MTR/POR Results Across B0–B7

Every reported condition from B0 through B7 was presented with identical safety endpoints:
$$\text{MTR} = 0.0\% \; [0.0\%, 12.5\%], \quad \text{POR} = 0.0\% \; [0.0\%, 12.5\%]$$

### 2.1 The Technical Root Causes

The identical rates did not arise from equivalent real-world safety behavior. They were produced by four interconnected software implementation artifacts:

1. **Unlinked Ground-Truth Labels:**
   In [`runner.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/experiments/runner.py) lines 89–96, ground-truth timestamps were extracted from `event.labels`:
   ```python
   for lbl in event.labels:
       if lbl.name in ("crossing_entry", "approach_entry") and lbl.timestamp_s is not None:
           entry_time_s = float(lbl.timestamp_s)
       elif lbl.name in ("tail_clearance", "clearance") and lbl.timestamp_s is not None:
           clearance_time_s = float(lbl.timestamp_s)
   ```
   Because candidate annotations in `data/ground_truth/proposals/` were unapproved under the R01/R02 firewall, no `event_labels.json` files existed in `data/raw/layer_b/v2/`. Consequently, `load_event_bundle` returned `event.labels = ()`, resulting in `entry_time_s = None` and `clearance_time_s = None` for **all 27 events**.

2. **Silent Fallback in Single Event Evaluation:**
   In [`metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) lines 137–156:
   ```python
   missed = False
   if entry_time_s is not None:
       # Check passage blocking at entry
       ...
       elif sim_result.closed_duration_s == 0.0:
           missed = True

   premature = None
   if clearance_time_s is not None and entry_time_s is not None:
       premature = sim_result.premature_opening_detected
   ```
   When `entry_time_s is None`, the entire block checking missed trains was bypassed. `missed` defaulted to `False` even when `sim_result.closed_duration_s == 0.0`! `premature` was set to `None` (not evaluable).

3. **Cohort Aggregation Artifact:**
   In `metrics.py` lines 208–228:
   - `eligible_events = len([e for e in evaluations if e.evaluable and e.has_train_ground_truth])` = 27.
   - `missed_train_count = sum(1 for e in eligible if e.missed_train)` = 0.
   - `missed_train_rate = 0 / 27 = 0.0%` with Wilson 95% CI `[0.0%, 12.5%]`.
   - `premature_evaluable = [e for e in eligible if e.premature_opening is not None]` = 0.
   - `premature_opening_rate` was returned as `None`, with CI `"not_evaluable"`.

4. **Table Formatting Substitution:**
   In [`scripts/generate_publication_tables.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/generate_publication_tables.py) lines 317–318:
   ```python
   por_val = sdata.get("premature_opening_rate")
   por = f"{por_val:.1%}" if por_val is not None else "0.0% [0.0%, 12.5%]"
   ```
   Whenever POR was `None`, the script substituted `"0.0% [0.0%, 12.5%]"` into publication tables.

---

## 3. Recomputed Metrics Table Across All Benchmark Conditions

The following master table recomputes performance across all 17 benchmark conditions using true event-level numerators, correct eligible cohort populations, and provisional candidate timestamps (marked strictly as provisional under the R01/R02 firewall):

| Condition ID | Configuration Description | Eligible Cohorts & Events | Excluded Events & Reason | MTR Num / Denom (Rate) | POR Num / Denom (Rate) | Negative Control Unnecessary Closures (Count & Dur) | Gate Closed State Reached? | Gate Reopened Appropriately Post-Clearance? | Liveness & Indefinite Closure Assessment | Raw Output Files Supporting Calculation |
|---|---|---|---|---|---|---|---|---|---|---|
| **B0** | Front Vision Only (Stateless 1-frame threshold, conf $\ge 0.35$) | Train: 22 events (obs $T_1, T_4$) | `event_005` (left/right-censored), Controls, Engine | 0 / 22 (**0.0%**) | **20 / 22 (90.9%)** | **1 / 3 (33.3%)**, 11.8s closed | Reached (23/23 trains) | **No** (Chattered open during passage on 21/23 trains) | Liveness preserved, severe chattering & safety hazard | `results/experiments/B0/single_events.json`, `summary.json` |
| **B1** | Audio Only (Horn threshold $T^* = 0.3700$, latch closed, never open) | Train: 22 events (obs $T_1$) | `event_005` (unobservable), Controls, Engine | **19 / 22 (86.4%)** | 0 / 3 (**0.0%**) | **0 / 3 (0.0%)**, 0.0s closed | **No** (Gate stayed open for 20/23 trains) | **No** (3 actuated events locked closed indefinitely) | **Zero Liveness:** When actuated, gate NEVER opens. 87% missed trains. | `results/experiments/B1/single_events.json`, `summary.json` |
| **B2** | Dual Vision + Audio (Stateless 3-frame persistence) | Train: 22 events (obs $T_1, T_4$) | `event_005` (censored), Controls, Engine | 0 / 22 (**0.0%**) | **16 / 22 (72.7%)** | **1 / 3 (33.3%)**, 11.6s closed | Reached (23/23 trains) | **No** (Prematurely reopened during mid-train dropout) | Liveness preserved, severe chattering hazard | `results/experiments/B2/single_events.json`, `summary.json` |
| **B3** | Dual Vision Only (Stateless 2-frame persistence, no audio) | Train: 22 events (obs $T_1, T_4$) | `event_005` (censored), Controls, Engine | 0 / 22 (**0.0%**) | **16 / 22 (72.7%)** | **1 / 3 (33.3%)**, 11.8s closed | Reached (23/23 trains) | **No** (Prematurely reopened during mid-train dropout) | Liveness preserved, severe chattering hazard | `results/experiments/B3/single_events.json`, `summary.json` |
| **B4** | Full Proposed Policy (Deterministic State Machine + Dwell Timers) | Train: 22 events (obs $T_1, T_4$) | `event_005` (censored), Controls, Engine | 0 / 22 (**0.0%**) | **0 / 22 (0.0%)** | **3 / 3 (100.0%)**, **39.0s closed** | Reached (23/23 trains) | **Yes** (Reopened after 3.0s dwell on 22/22 trains) | Liveness preserved on trains; severe nuisance closures on controls | `results/experiments/B4/single_events.json`, `summary.json`, `timelines/` |
| **B5a** | Camera 1 Full Loss ($t=0..\text{end}$) | Train: 22 events | `event_005`, Controls, Engine | 0 / 22 (**0.0%**) | **0 / 22 (0.0%)** | **2 / 3 (66.7%)**, 29.4s closed | Reached (23/23 trains) | Yes (via Camera 2 departure tracking) | Degraded single-camera operation | `results/experiments/B5a/single_events.json`, `summary.json` |
| **B5b** | Camera 1 Midway Loss ($t=0.3..0.7$) | Train: 22 events | `event_005`, Controls, Engine | 0 / 22 (**0.0%**) | **0 / 22 (0.0%)** | **3 / 3 (100.0%)**, 39.0s closed | Reached (23/23 trains) | Yes (State machine latched closed) | Normal liveness | `results/experiments/B5b/single_events.json`, `summary.json` |
| **B5c** | Camera 1 Flapping (2s on / 2s off) | Train: 22 events | `event_005`, Controls, Engine | 0 / 22 (**0.0%**) | **0 / 22 (0.0%)** | **3 / 3 (100.0%)**, 39.0s closed | Reached (23/23 trains) | Yes | Normal liveness | `results/experiments/B5c/single_events.json`, `summary.json` |
| **B6a** | Camera 2 Rear Loss ($t=0..\text{end}$) | Train: 22 events | `event_005`, Controls, Engine | 0 / 22 (**0.0%**) | **0 / 22 (0.0%)** | **1 / 3 (33.3%)**, 9.6s closed | Reached (23/23 trains) | **No** (Gate held closed until video end on 5 events) | Conservative hold: lack of rear confirmation delays opening | `results/experiments/B6a/single_events.json`, `summary.json` |
| **B6b** | Complete Dual Camera Blackout | Train: 22 events | `event_005`, Controls, Engine | **22 / 22 (100.0%)** | 0 / 0 (**N/A**) | **0 / 3 (0.0%)**, 0.0s closed | **NO (0/23 reached closed state)** | **NO** (Gate remained wide open at 90° entire time) | **COMPLETE SAFETY COLLAPSE:** Stayed in `IDLE`; gate never closed | `results/experiments/B6b/single_events.json`, `summary.json` |
| **B6c** | Sequential Camera Loss (30% / 60%) | Train: 22 events | `event_005`, Controls, Engine | 0 / 22 (**0.0%**) | **0 / 22 (0.0%)** | **3 / 3 (100.0%)**, 39.0s closed | Reached (23/23 trains) | **No** (Entered `FAULT_FAIL_SAFE`, locked closed) | **Zero Liveness post-fault:** Gate clamped closed permanently | `results/experiments/B6c/single_events.json`, `summary.json` |
| **B7a** | Audio Full Loss ($t=0..\text{end}$) | Train: 22 events | `event_005`, Controls, Engine | 0 / 22 (**0.0%**) | **0 / 22 (0.0%)** | **3 / 3 (100.0%)**, 39.0s closed | Reached (23/23 trains) | Yes | Identical to B4 (proves audio had zero effect) | `results/experiments/B7a/single_events.json`, `summary.json` |
| **B7b** | Dropped Frames (30% Random) | Train: 22 events | `event_005`, Controls, Engine | **UNEXECUTED** | **UNEXECUTED** | 0 / 3 (0.0s closed) | **NO** (0/23 reached closed state) | **NO** (100% of frames dropped due to code bug) | **Broken Experiment:** Empty frame input to simulation | `results/experiments/B7b/single_events.json`, `summary.json` |
| **B7c** | Spurious Vision False Injection | Train: 22 events | `event_005`, Controls, Engine | 0 / 22 (**0.0%**) | **0 / 22 (0.0%)** | **3 / 3 (100.0%)**, **49.0s closed** | Reached (23/23 trains) | Yes | Nuisance closed duration increased by 10.0s | `results/experiments/B7c/single_events.json`, `summary.json` |
| **B7d** | Out-of-Order Timestamps | Train: 22 events | `event_005`, Controls, Engine | 0 / 22 (**0.0%**) | **0 / 22 (0.0%)** | **3 / 3 (100.0%)**, 39.0s closed | Reached (23/23 trains) | Yes | Rule 8 rejected unordered frames; identical to B4 | `results/experiments/B7d/single_events.json`, `summary.json` |
| **B7e** | Stale Timestamps (2.0s midway) | Train: 22 events | `event_005`, Controls, Engine | 0 / 22 (**0.0%**) | **0 / 22 (0.0%)** | **3 / 3 (100.0%)**, 39.0s closed | Reached (23/23 trains) | Yes | Handled by state latching; identical to B4 | `results/experiments/B7e/single_events.json`, `summary.json` |
| **B7f** | Audio Loss + 10% Dropped Frames | Train: 22 events | `event_005`, Controls, Engine | **UNEXECUTED** | **UNEXECUTED** | 0 / 3 (0.0s closed) | **NO** (0/23 reached closed state) | **NO** (100% of frames dropped due to code bug) | **Broken Experiment:** Empty frame input to simulation | `results/experiments/B7f/single_events.json`, `summary.json` |

---

## 4. Liveness and Nuisance-Closure Findings

### 4.1 Achieving Zero MTR / Zero POR by Permanent Barrier Clamp

A crossing protection system can trivially achieve zero Missed-Train Rate and zero Premature-Opening Rate by simply clamping the barrier arm permanently in the CLOSED position ($0^\circ$). Under such a degenerative policy:
- No train can ever enter an open crossing ($\text{MTR} = 0.0\%$).
- The barrier never opens prematurely ($\text{POR} = 0.0\%$).
- However, crossing liveness is completely destroyed: highway traffic is permanently blocked, inducing extreme traffic delay, public non-compliance, and pedestrians climbing over barriers.

In our audit, three conditions exhibited variants of this failure:
1. **B1 (Audio Only):** Latch rule commands `CLOSING` upon audio detection and never commands `OPENING`. In the 3 events where audio triggered, the gate remained closed indefinitely until the video recording ended.
2. **B6c (Sequential Camera Loss):** Transitioned into `FAULT_FAIL_SAFE` at $t = 0.6 \times \text{duration}$. Because `FAULT_FAIL_SAFE` has zero outbound transitions in `decision_engine.py`, the gate remained closed permanently.
3. **B6a (Camera 2 Loss):** Because positive rear confirmation was missing on camera 2, Rule 3 delayed clearance, keeping the gate closed for the remainder of recording on 5 train events.

### 4.2 Nuisance Closures on Negative Controls ($N=3$)

The negative control cohort consists of three video pairs depicting road and pedestrian crossing traffic with **no train present**:
- `no_train_events_event_001`: 24.6s duration. Road vehicles, motorcycles, and pedestrians.
- `no_train_events_event_002`: 11.9s duration. Dense street traffic and visual clutter.
- `no_train_events_event_003`: 23.8s duration. Roadway traffic and pedestrian movement.

#### Empirical Findings on Negative Controls:
- **Audio Classifier:** Zero false positives across all 116 analyzed audio windows.
- **Vision Classifier:** Severe false positive activations. Road traffic was misclassified as train frontal and side aspects:
  - `event_001`: 28 frames with false `'front'` detections (conf 0.360–0.688).
  - `event_002`: 60 out of 60 frames (100%) with false `'front'` and `'side'` detections (conf up to 0.859).
  - `event_003`: 13 frames with false `'front'` and `'rear'` detections.
- **System Policy Response (B4):** Because the state machine triggers `WARNING` upon two consecutive approach detections, the system closed the gate on **all three negative control events (3/3, 100% False Activation Rate)**:
  - `event_001`: Closed for **18.8s** (76.4% of total video duration).
  - `event_002`: Closed for **9.6s** (80.7% of total video duration).
  - `event_003`: Closed for **10.6s** (44.5% of total video duration).
  - **Total unnecessary closure duration:** **39.0 seconds** out of 60.3 seconds total exposure (**64.7% nuisance duty cycle**).

> [!IMPORTANT]
> **Evaluation Correction:** Negative control events must never be included in the MTR denominator. Under a statistically defensible formulation, the False Alarm / Nuisance Activation Rate for B4 is **3/3 (100.0%)**, with an exact 95% Wilson score confidence interval of **[43.9%, 100.0%]**. Given the short total exposure (60.3 seconds) at a single crossing, no claim of operational readiness against visual false alarms is justifiable.

---

## 5. Audit of Synchronization and Timing Claims (R04)

### 5.1 Inspection of `SyncAligner` and Ingestion Pipeline

Research requirement R04 mandates that observations from independently timed cameras must not be merged on an unverified shared clock without empirical calibration.

Inspection of the code reveals:
1. In `src/railway_detection/data/sync.py`, `SyncAligner` provides methods `add_source(source_id, offset_s=0.0, uncertainty_s=0.0)` and `to_master(source_id, timestamp_s)`.
2. In `src/railway_detection/fusion/collector.py`, `MultimodalEvidenceCollector` accepts an optional `sync_aligner`. However, in `src/railway_detection/experiments/layer_b_processor.py` line 279:
   ```python
   collector = MultimodalEvidenceCollector(window_tolerance_s=0.25)
   collector.add_evidence_batch(vision_records)
   collector.add_evidence_batch(audio_records)
   ```
   `SyncAligner` was **not passed** (`aligner = None`).
3. Consequently, in `MultimodalEvidenceCollector.add_evidence`:
   ```python
   master_t = record.timestamp_s
   ```
   Timestamps from `camera_front.mov` and `camera_back.mov` were directly mapped onto the master timeline using an **unverified static zero offset ($0.0\text{s}$)**.

### 5.2 Forensic Impact on Cross-Camera Claims

- `camera_front.mov` and `camera_back.mov` were recorded on separate consumer cameras without hardware genlock, SMPTE timecode, or NTP synchronization.
- No empirical acoustic time-difference-of-arrival (TDOA) or visual cross-correlation calibration was performed.
- Cross-camera timing subtractions (e.g., claiming front-to-back transit times or simultaneous multi-angle exposure) are scientifically invalid.
- Audiovisual fusion *within* a single video stream is permissible because audio and video tracks share container presentation timestamps. Cross-camera fusion timelines must be classified as operating on **unverified camera-local timelines**.

---

## 6. Audit of Safety Invariants (INV-1 through INV-6)

The following taxonomy classifies the evidence source for each of the six claimed safety invariants:

| Invariant Code | Claimed Safety Property | Software Mechanism | Empirical Evidence Grade | Actual Observed Behavior in Experiment | Real Hardware Prerequisite |
|---|---|---|---|---|---|
| **INV-1** | Audio never independently commands gate opening | Audio excluded from `CROSSING_CLEAR` and `GATE_OPENING` rules | **Grade A (Simulation & Logic)** | Adhered to in 100% of frames across B0–B7. B1 never commanded opening. | Physical wiring check: verify audio processor has no physical actuator relay line. |
| **INV-2** | Sensor loss never authorizes crossing clearance | Rule 3 mandates positive departure observation; loss maintains closure | **Grade B (Simulation Replay)** | Maintained in B5a, B5b, B6a. Disappearance held gate closed. | Fail-safe watchdog on video loss (loss of SDI/RTSP signal). |
| **INV-3** | Dual camera blackout triggers `FAULT_FAIL_SAFE` within 0.20s | Rule 4 clamps gate closed upon total vision blackout | **Grade C (Synthetic Unit Test ONLY)** | **FAILED in natural replay B6b!** Gate stayed in `IDLE` with barrier OPEN for all 27 events. Succeeded ONLY in unit test when pre-transitioned to `WARNING`. | Certified hardware watchdog relay circuit dropping barrier upon loss of edge compute heartbeat. |
| **INV-4** | Out-of-order timestamps are rejected | Rule 8 discards frames with $t < t_{\text{last}}$ | **Grade B (Synthetic Injection in B7d)** | Replayed successfully in B7d; injected unordered frames were discarded without state corruption. | PTP (IEEE 1588) hardware timestamp validation in network ingestion NIC. |
| **INV-5** | Clearance requires positive rear confirmation and dwell timer | Rule 3 requires `'rear'` detection and 3.0s dwell before opening | **Grade A (Real Media Inference)** | Verified on 22 train events in B4. Reopening appropriately prevented on `engine_events_event_001` where rear was absent. | Independent axle counters / certified track circuits verifying physical train clearance. |
| **INV-6** | New train arrival immediately aborts gate opening phase | Rule 7 aborts `GATE_OPENING` to `GATE_CLOSING` upon approach detection | **Grade C (Synthetic Unit Test ONLY)** | Verified in unit test `test_regression_new_train_aborts_gate_opening`. Zero multi-train sequences exist in Layer B dataset. | Hardware interlock aborting gate motor opening circuit upon radar/inductive loop trigger. |

### 6.1 Detailed Deconstruction of the 0.20s Dual-Camera Fail-Safe Claim

- **Claim in Previous Report:** "Under complete dual camera loss (B6b), the system transitioned into `FAULT_FAIL_SAFE` within 0.20s, locking the gate barrier in the closed position and satisfying Safety Invariant INV-3."
- **Actual Code Path in Unit Test:**
  In [`tests/unit/test_decision_engine.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_decision_engine.py) lines 144–163:
  1. Synthetic frame at $t=1.0\text{s}$ with detection $\to$ `TRAIN_APPROACHING`.
  2. Synthetic frame at $t=1.1\text{s}$ with detection $\to$ `WARNING`.
  3. Synthetic frame at $t=1.2\text{s}$ with `c1_avail=False, c2_avail=False` $\to$ Rule 4 fired: `FAULT_FAIL_SAFE`, gate `CLOSED`.
  4. The elapsed time from warning confirmation ($t=1.1\text{s}$) to fault detection ($t=1.2\text{s}$) or frame step was $0.1\text{s}$ to $0.20\text{s}$.
- **Actual Outcome in Real-Media Benchmark B6b:**
  1. In `runner.py`, `DUAL_CAMERA_DROPOUT` was scheduled from $t=0.0\text{s}$ to $t=\text{duration}+1.0\text{s}$.
  2. The system initialized in `IDLE`.
  3. At $t=0.0\text{s}$, both cameras were unavailable.
  4. Rule 4 evaluated: `if all_vision_failed and prev_state not in (IDLE, FAULT_FAIL_SAFE):`. Because `prev_state == IDLE`, Rule 4 **did not trigger**.
  5. The system stayed in `IDLE` with `gate_state = OPEN` (angle $90^\circ$) across all 249 simulation steps.
  6. The barrier **never closed**. Real trains traversed the crossing while the simulated gate remained wide open.
- **Verdict:** Describing passing a synthetic unit test as observed real-world safety performance is scientifically false. In natural-media replay, condition B6b experienced an unhandled blind passage failure.

---

## 7. Audit of B0–B7 Benchmark Design & Confounded Comparisons

### 7.1 Confounded Comparisons

1. **B0 vs. B4 (Single Camera Stateless vs. Dual Camera Full Policy):**
   This comparison changed three independent experimental factors simultaneously:
   - Camera count (1 camera vs. 2 cameras).
   - Sensory modality (vision only vs. vision + audio).
   - Control policy (stateless single-frame threshold vs. state machine with dwell timers).
   Attributing performance gains (e.g. elimination of premature opening) to audio or dual cameras is invalid; forensic analysis demonstrates that the state machine latching logic alone accounts for 100% of the premature opening reduction.

2. **B3 vs. B4 (Dual Vision Only vs. Dual Vision + Audio):**
   This comparison properly isolates the addition of the audio modality:
   - B3: Dual vision, temporal state machine (confirm=2), no audio.
   - B4: Dual vision, temporal state machine (confirm=2), with Audio V3 ($T^* = 0.3700$).
   - **Empirical Result:**
     - Train closures: 23/23 in B3 vs. 23/23 in B4.
     - Total closed duration: 1,227.4s in B3 vs. 1,231.4s in B4 ($\Delta = +4.0\text{s}$, a 0.3% difference).
     - Acoustic detections: Audio fired in only 3 of 23 train events.
     - **Conclusion:** Under canonical threshold $T^* = 0.3700$, audio provided near-zero incremental safety benefit over dual vision alone.

3. **B7b and B7f (Unexecuted Conditions Due to Frame Dropping Bug):**
   In `src/railway_detection/simulation/failure_injector.py` lines 68–72:
   ```python
   drop_frame = any(s.mode == FailureMode.DROPPED_FRAMES for s in active_scheds)
   if drop_frame:
       continue
   ```
   Instead of dropping 30% or 10% of frames randomly using `drop_rate`, the implementation dropped **100% of frames**. B7b and B7f executed on empty frame arrays. Claims that B7b and B7f proved resilience to dropped frames are invalid.

---

## 8. Corrected Results Tables & Explicitly Invalidated Claims

### 8.1 Invalidated Publication Claims

| Claim ID | Text in Previous Report (`REAL_WORLD_EXPERIMENT_REPORT.md`) | Forensic Finding | Corrected Scientific Reality |
|---|---|---|---|
| **C-01** | "Across 23,759 video frames, the detector emitted 22,291 detections." | Derived by summing active cache files with 40 orphaned historical cache files from a superseded 20-event run. | Across the 27 active evaluation events, the detector evaluated **13,086 frames** and emitted **12,047 detections**. |
| **C-02** | "Audio V3 evaluated 4,741 sliding windows, detecting acoustic train signatures in 865 windows (18.2%)." | Derived by summing active audio caches with 20 orphaned historical caches from Audio V1/V2 runs. | Audio V3 evaluated **2,600 sliding windows**, detecting horn signatures in **9 windows (0.35%)** across 3 events. |
| **C-03** | "Event-Level Acoustic Recall (train): 23/23 events (100.0%)." | Table 5 row was hardcoded to "23/23 (100.0%)" despite only 9 positive windows existing in the dataset. | True event-level acoustic recall is **3 / 23 events (13.0%)**. |
| **C-04** | "B0–B7 all achieved Missed-Train Rate (MTR) = 0.0% [0.0%, 12.5%]." | Ground-truth labels were unlinked (`entry_time_s = None`), causing `missed_train` to silently default to `False`. | In B1, the gate missed **20 / 23 trains (87.0% MTR)**. In B6b, the gate missed **23 / 23 trains (100% MTR)**. |
| **C-05** | "B0–B7 all achieved Premature-Opening Rate (POR) = 0.0% [0.0%, 12.5%]." | Unlinked labels caused POR to be `None`, which was formatted as "0.0% [0.0%, 12.5%]" by fallback code. | In B0, premature openings occurred in **20 / 22 trains (90.9%)**. In B2 and B3, premature openings occurred in **16 / 22 trains (72.7%)**. |
| **C-06** | "Under complete dual camera loss (B6b), the system transitioned into `FAULT_FAIL_SAFE` within 0.20s." | In B6b replay, the system remained in `IDLE` with the gate open for 100% of frames. 0.20s timing came from synthetic unit test. | Condition B6b suffered a complete unhandled blind passage failure. The gate never closed. |
| **C-07** | "B7b (30% dropped frames) and B7f (combined stress) achieved 0.0% MTR/POR." | Code bug dropped 100% of frames; simulation ran on empty inputs. | Experiments B7b and B7f were unexecuted. |
| **C-08** | "Negative control performance demonstrates robust safety." | Negative controls were forced into the train cohort; false alarms were never penalized. | B4 caused **100% False Activation Rate (3/3)** with **39.0s of unnecessary closure** (64.7% duty cycle). |

---

## 9. Remaining Blockers & Required Follow-Up Actions

To establish a defensible empirical research foundation, the following technical blockers must be resolved:

1. **Human Ground-Truth Adjudication (R01/R02 Firewall):**
   Candidate proposals in `data/ground_truth/proposals/` must be formally reviewed and signed off by the human researcher. Once approved, canonical `event_labels.json` files must be populated into `data/raw/layer_b/v2/` to allow automated metrics calculation without synthetic defaults.

2. **Fix `FailureInjector` Frame Dropping Bug:**
   In `src/railway_detection/simulation/failure_injector.py`, replace `any(s.mode == FailureMode.DROPPED_FRAMES)` with a pseudo-random Bernoulli sampling check using `s.parameters.get("drop_rate", 0.3)`. Re-run conditions B7b and B7f under valid dropped frame distributions.

3. **Fix `FAULT_FAIL_SAFE` State Machine Trigger in IDLE:**
   In `src/railway_detection/fusion/decision_engine.py`, modify Rule 4 so that complete vision failure transitions to `FAULT_FAIL_SAFE` regardless of whether the initial state is `IDLE` or active. If all cameras fail while in `IDLE`, the system must annunciate an equipment fault and command fail-safe barrier closure or safe-state signaling.

4. **Isolate and Purge Superseded Cache Files:**
   Move the 40 orphaned vision caches and 20 orphaned audio caches from `results/experiments/cache/` into a segregated archive directory (`results/archive/orphaned_caches_v1_v2/`) to prevent reporting scripts from aggregating dead data.

5. **Acknowledge R04 Synchronization Limitations:**
   Update research documentation and future manuscripts to state clearly that dual-camera evaluations operate on independent camera-local timelines with static zero offset, until physical genlock or empirical audio TDOA calibration can be performed on-site.
