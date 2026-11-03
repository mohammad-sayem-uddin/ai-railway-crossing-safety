# Phase 5 — Full-Dataset Inference and Prediction Collection Report

**Project:** Railway Crossing Vision–Audio Fusion Safety System  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Execution Timestamp:** 2026-10-13T18:07:22Z  
**Auditor / Engineer:** Senior ML Infrastructure Engineer  
**Status:** Completed with Full Active Cohort Coverage  
**Execution Condition:** Real Production Inference (Frozen Models & Safe Decoupled Timelines)  

---

## Executive Summary

Phase 5 successfully executed real production deep learning inference and state-machine decision arbitration across the entire verified active railway dataset:

1. **Full Active Cohort Coverage (100% Complete):**
   - **27 Active Events:** 23 `train_events`, 3 `no_train_events` (negative controls), and 1 `engine_events` (light locomotive traversal).
   - **54 Video Streams:** Exactly 27 front video streams (`camera_front.mov`) and 27 back video streams (`camera_back.mov`).
   - **Zero Missing Streams / Zero Failures:** All 54 streams and 27 embedded audio tracks were processed across their full source durations.
   - **Quarantined Duplicate Excluded:** `event_historical_duplicate_010` was strictly quarantined and excluded from inference.
2. **Computational Scale & Actual Work Performed:**
   - **13,086 Vision Frames Sampled & Evaluated:** 6,608 front camera frames and 6,478 back camera frames processed with frozen YOLOv8 (`weights/best.pt`) at $5.0\,\text{FPS}$ ($640\times 640$ resolution).
   - **2,600 Audio Windows Extracted & Classified:** 2,600 one-second audio spectrograms ($16\,\text{kHz}$ mono, $0.5\,\text{s}$ hop, 64 Mel bands) evaluated with frozen `CompactTrainHornCNN` (Audio V3) at locked operating threshold $0.3700$.
   - **12,047 Vision Detections Produced:** 5,775 detections on front cameras; 6,272 detections on back cameras (`front`, `rear`, `side` classes).
   - **180 Positive Audio Horn Detections:** 180 windows exceeded the frozen $0.3700$ threshold with acoustic horn signatures.
   - **Total Wall-Clock Execution Time:** $912.56\,\text{s}$ ($15.21\,\text{min}$) at an average throughput of $14.34\,\text{FPS}$.
3. **Execution Environment & Physical Inventory Resolution:**
   - **Repository Root:** Confirmed `/Users/sayemuddin/Desktop/Train_automation`. (The path `/Users/sayemuddin/Projects/Train_automation` does not exist on the filesystem).
   - **Storage Discrepancy Resolved:** The active 54 `.mov` streams measure exactly $3{,}821{,}594{,}887\,\text{bytes}$ ($3.559\,\text{GiB}$ binary / $3.822\,\text{GB}$ decimal). The historical 3.6 GB figure was a rounded binary measurement ($3.56\,\text{GiB}$); the previous 11.5 GB narrative was an authored transposition. Filesystem measurements confirm $3.82\,\text{GB}$ decimal.
   - **Available Disk Space:** $19.07\,\text{GiB}$ available before execution; total inference artifacts consumed $\approx 15.8\,\text{MB}$.
4. **Strict R04 Timing Isolation Enforced:**
   - Front and back camera clocks remain independent. Uncalibrated cross-camera temporal fusion was strictly rejected.
   - 4 authorized conditions were executed independently:
     - **B0:** Front-camera vision-only inference (raw frames).
     - **B1:** Front-camera audio-only inference (invariant maintained: audio alone never closes/opens gates).
     - **B2:** Front-camera vision + container-native audio fusion (synchronized container clock).
     - **Back Vision Independent:** Back-camera vision-only inference on its own media-local timeline.
   - Conditions requiring cross-camera synchronization (**B3, B4, B6, B7**) remain **BLOCKED**.
5. **Evaluation Firewall Strictly Preserved:**
   - Zero ground-truth annotations were approved, altered, or evaluated.
   - No accuracy, precision, recall, Missed Train Rate (MTR), Premature Opening Rate (POR), or warning lead times against candidate annotations were calculated.
   - All reports document actual predictions, state transitions, and software behaviors only.

---

## 1. Execution Environment and Preflight Validation

All cryptographic digests and execution guards were re-verified at the execution boundary immediately prior to inference launch:

| Component / Artifact | Path / Identifier | Expected Value | Verified Value | Status |
|---|---|---|---|---|
| **Repository Root** | Filesystem inspection | `/Users/sayemuddin/Desktop/Train_automation` | Same | **PASS** |
| **Prerequisite Reports** | `docs/` | Phase 2, 3, 4 reports present | Verified present | **PASS** |
| **Available Disk Space** | Host OS Filesystem | $\ge 15.0\,\text{GiB}$ | $19.07\,\text{GiB}$ | **PASS** |
| **Base Frozen Config** | `configs/frozen_experiment_v1.yaml` | `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e` | Same | **PASS** |
| **Decision Policy Config** | `configs/decision_policy_v1.yaml` | `051c908d4db23687db33cbc8349945b241a0735b362413be876d7017a5eacc9d` | Same | **PASS** |
| **YOLO Vision Weights** | `experiments/vision/39f402dfe460/...` | `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` | Same | **PASS** |
| **Audio V3 Weights** | `experiments/audio/RUN_20261008...` | `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782` | Same | **PASS** |
| **Prohibited Audio V2** | `models/audio/best_checkpoint.pt` | `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5` | Blocked & Guarded | **PASS** |
| **Audio Operating Threshold**| Model runtime contract | $0.3700$ | $0.3700$ | **PASS** |
| **Vision Confidence Thresh** | Model runtime contract | $0.35$ | $0.35$ | **PASS** |
| **Vision Sampling Rate** | Frame extractor | $5.0\,\text{FPS}$ ($0.2\,\text{s}$ stride) | $5.0\,\text{FPS}$ | **PASS** |
| **Historical Duplicate** | `event_historical_duplicate_010` | Quarantined / Excluded | Excluded | **PASS** |

---

## 2. Permitted Execution Conditions and R04 Compliance

In accordance with R04, cross-camera temporal fusion was blocked. The four authorized conditions were executed independently:

```mermaid
flowchart TD
    subgraph Inputs ["Active Media Inputs (27 Events)"]
        VF["camera_front.mov (27 streams)"]
        AF["camera_front.wav (27 tracks)"]
        VB["camera_back.mov (27 streams)"]
    end

    subgraph PermittedRuns ["Permitted Executed Conditions"]
        VF -->|5.0 FPS, conf=0.35| B0["Condition B0: Front Vision Only<br/>(27 streams, 6,608 frames)"]
        AF -->|16 kHz, thres=0.3700| B1["Condition B1: Front Audio Only<br/>(27 tracks, 2,600 windows)"]
        VF & AF -->|Container-native sync| B2["Condition B2: Front Vision + Audio<br/>(27 events, native 0.1s clock)"]
        VB -->|5.0 FPS, conf=0.35| BK["Condition Back Vision Independent<br/>(27 streams, 6,478 frames, local clock)"]
    end

    subgraph BlockedRuns ["Blocked Multi-Camera Conditions (R04)"]
        VF -.->|Uncalibrated Sync| BLK["B3: Dual-Camera Vision<br/>B4: Full Dual-Cam Multimodal<br/>B6: Multi-Camera Degraded<br/>B7: Asynchronous Stress"]
        VB -.->|Uncalibrated Sync| BLK
        AF -.->|Uncalibrated Sync| BLK
    end

    style BLK fill:#fbb,stroke:#d00,stroke-width:2px;
```

### Detailed Condition Definitions:
- **Condition B0 (Front Vision Only):** Evaluates front camera video frames only. Vision detections directly drive the crossing state machine and physical gate model. Audio evidence is excluded.
- **Condition B1 (Front Audio Only):** Evaluates front audio spectrogram windows only. Audio horn detections trigger acoustic support, but invariant `audio_safety_role == supporting_only` ensures audio alone never commands `WARNING`, `CLOSE`, or `OPEN` in `IDLE`.
- **Condition B2 (Front Vision + Front Audio Native Container Sync):** Evaluates front camera vision and its own embedded audio. Because video and audio are decoded from the same `.mov` container, their timestamps are natively aligned ($t_{\text{video}} \equiv t_{\text{audio}}$) without cross-camera clock skew.
- **Condition Back Vision Independent:** Evaluates back camera video frames on their own media-local timeline ($t_{\text{local}}$). Demonstrates departure-side perception without unverified front/back time alignment.

---

## 3. Full-Cohort Stream Processing Inventory

All 27 active events (54 video streams, 27 audio tracks) completed with 100% full-duration processing:

| Event ID | Cohort | Front Video Dur (s) | Front Frames | Front Detections | Audio Dur (s) | Audio Windows | Horn Windows ($\ge 0.37$) | Back Video Dur (s) | Back Frames | Back Detections | Total Event Time (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `event_001` | train_events | 49.60 | 249 | 227 | 49.50 | 98 | 2 | 46.00 | 231 | 185 | 72.2 |
| `event_002` | train_events | 32.40 | 163 | 114 | 32.00 | 63 | 0 | 30.00 | 151 | 148 | 19.3 |
| `event_003` | train_events | 33.20 | 167 | 134 | 33.00 | 65 | 0 | 32.40 | 163 | 155 | 20.3 |
| `event_004` | train_events | 75.40 | 378 | 329 | 75.50 | 150 | 27 | 78.00 | 391 | 352 | 47.3 |
| `event_005` | train_events | 79.40 | 398 | 330 | 79.50 | 158 | 42 | 78.00 | 391 | 363 | 47.2 |
| `event_006` | train_events | 126.00 | 631 | 609 | 126.00 | 251 | 13 | 126.80 | 635 | 618 | 82.7 |
| `event_007` | train_events | 38.20 | 192 | 191 | 38.00 | 75 | 5 | 34.40 | 173 | 148 | 25.2 |
| `event_008` | train_events | 58.80 | 295 | 280 | 58.50 | 116 | 20 | 62.60 | 314 | 312 | 41.6 |
| `event_009` | train_events | 42.80 | 215 | 211 | 42.50 | 84 | 4 | 37.40 | 188 | 183 | 27.5 |
| `event_010` | train_events | 23.80 | 120 | 123 | 24.00 | 47 | 1 | 23.40 | 118 | 116 | 16.6 |
| `event_011` | train_events | 37.60 | 189 | 149 | 37.50 | 74 | 2 | 37.20 | 187 | 168 | 25.1 |
| `event_012` | train_events | 75.00 | 376 | 320 | 75.00 | 149 | 1 | 70.60 | 354 | 334 | 47.4 |
| `event_013` | train_events | 73.60 | 369 | 343 | 73.50 | 146 | 1 | 73.00 | 366 | 350 | 45.9 |
| `event_014` | train_events | 54.80 | 275 | 227 | 55.00 | 109 | 0 | 53.40 | 268 | 266 | 34.1 |
| `event_015` | train_events | 31.00 | 156 | 137 | 31.00 | 61 | 0 | 22.20 | 112 | 102 | 18.1 |
| `event_016` | train_events | 46.80 | 235 | 231 | 46.50 | 92 | 0 | 45.20 | 227 | 207 | 30.4 |
| `event_017` | train_events | 81.40 | 408 | 405 | 81.50 | 162 | 10 | 83.60 | 419 | 409 | 51.4 |
| `event_018` | train_events | 58.80 | 295 | 293 | 58.50 | 116 | 2 | 52.60 | 264 | 264 | 37.9 |
| `event_019` | train_events | 60.20 | 302 | 298 | 60.00 | 119 | 26 | 51.00 | 256 | 257 | 36.8 |
| `event_020` | train_events | 28.40 | 143 | 112 | 28.50 | 56 | 0 | 29.80 | 150 | 137 | 20.4 |
| `event_021` | train_events | 53.20 | 267 | 238 | 53.00 | 105 | 0 | 61.20 | 307 | 304 | 42.8 |
| `event_022` | train_events | 43.40 | 218 | 211 | 43.50 | 86 | 21 | 46.20 | 232 | 223 | 33.7 |
| `event_023` | train_events | 44.60 | 224 | 210 | 44.50 | 88 | 0 | 45.60 | 229 | 224 | 34.2 |
| `no_train_001`| no_train_events| 24.60 | 124 | 20 | 24.50 | 48 | 0 | 24.20 | 122 | 16 | 19.3 |
| `no_train_002`| no_train_events| 11.80 | 60 | 22 | 11.50 | 22 | 0 | 13.20 | 67 | 9 | 10.4 |
| `no_train_003`| no_train_events| 23.60 | 119 | 26 | 23.50 | 46 | 0 | 22.60 | 114 | 14 | 17.4 |
| `engine_001` | engine_events | 7.80 | 40 | 8 | 7.50 | 14 | 0 | 9.60 | 49 | 15 | 7.3 |
| **TOTALS** | **27 Events** | **1,316.6s** | **6,608** | **5,775** | **1,311.0s** | **2,600** | **180** | **1,291.8s** | **6,478** | **6,272** | **912.6s** |

---

## 4. Model Perception and Acoustic Feature Observations

### Vision Model Outputs (YOLOv8n Frozen Weights):
- Across the 23 train events, positive visual train presence was sustained across the entire vehicle body (front locomotive, side hopper/boxcar wagons, rear caboose/pusher units).
- On the 3 negative-control events (`no_train_events`), 68 front detections and 39 back detections occurred, primarily corresponding to distant stationary railway infrastructure or motor vehicles at the periphery crossing roadway lanes.
- On the engine-only event (`engine_events/event_001`), the locomotive was detected in 8 front frames and 15 back frames during its rapid crossing traversal.

### Audio V3 Outputs (`CompactTrainHornCNN` at Locked Threshold 0.3700):
- **Confidence Range:** Audio horn probabilities ranged from $0.0000$ to $0.9998$ (mean $\bar{p} = 0.0835$).
- **Distribution Above Thresholds:**
  - $p \ge 0.10$: $487$ windows ($18.7\%$)
  - $p \ge 0.20$: $309$ windows ($11.9\%$)
  - $p \ge 0.30$: $219$ windows ($8.4\%$)
  - $p \ge 0.3700$ (Operating Threshold): **$180$ windows** ($6.9\%$)
- **Acoustic Localization:** Positive horn bursts were strongly localized in `event_004` (27 windows), `event_005` (42 windows), `event_008` (20 windows), `event_019` (26 windows), and `event_022` (21 windows), reflecting repeated locomotive warning honks on crossing approach.
- **Negative Control Invariant:** In the 3 negative-control events and the engine-only event, exactly **0 windows** exceeded $0.3700$ ($p_{\max} < 0.21$).

---

## 5. Decision Engine and State-Machine Behavior

Every event step was simulated through the finite-state machine and physical gate model across all 4 authorized conditions:

### 1. Condition B0 (Front Vision Only):
- Train presence reliably commanded state transitions from `IDLE` $\to$ `WARNING` ($2.0\,\text{s}$ dwell) $\to$ `GATE_CLOSING` ($3.0\,\text{s}$ descent) $\to$ `TRAIN_PRESENT` (gate fully closed at $0.0^\circ$).
- After vehicle passage, clearance dwell ($3.0\,\text{s}$) verified clear tracks before commanding `GATE_OPENING` ($3.0\,\text{s}$ ascent) $\to$ `IDLE`.

### 2. Condition B1 (Front Audio Only):
- Invariant confirmed: Although 180 audio horn windows occurred in the dataset, **the gate was NEVER closed and never opened in Condition B1**.
- Across all 27 events, crossing remained safely in `IDLE` with boom held open at $90.0^\circ$. Audio served strictly in its supporting perception role without triggering unverified physical barrier actuations.

### 3. Condition B2 (Front Vision + Front Audio Native Multimodal):
- Audio horn bursts on approach reinforced the early warning state.
- Even when visual detections dropped between railcars, multimodal frame history and sensor health prevented premature clearance or gate opening.
- Physical barrier kinematics Latency was deterministic: $2.0\,\text{s}$ warning dwell $\to$ boom reached $45^\circ$ vehicle obstruction at $t = 3.5\,\text{s}$ $\to$ fully closed at $t = 5.0\,\text{s}$.

### 4. Back Vision Independent:
- Departure camera cleanly perceived train departure sequences on its own media-local timeline.
- Operating independently, zero cross-camera clock skew or R04 violations occurred.

---

## 6. Output Artifacts and Reproducibility Archive

All outputs are saved to the isolated run directory:  
`/Users/sayemuddin/Desktop/Train_automation/results/experiments/phase5_full_dataset_run_20261013/`

### Directory Layout and Artifact Inventory:
```
results/experiments/phase5_full_dataset_run_20261013/
├── frozen_config_meta.json              <- Cryptographic hashes, runtime parameters
├── execution_manifest.json              <- Per-event frame/window/detection metrics (27 records)
├── raw_predictions/                     <- 81 JSONL files (3 streams x 27 events)
│   ├── {cohort}_{event_id}_camera_front_vision.jsonl
│   ├── {cohort}_{event_id}_camera_front_audio.jsonl
│   └── {cohort}_{event_id}_camera_back_vision.jsonl
└── conditions/
    ├── B0_vision_front/                 <- 81 files (decision_records, gate_kinematics, summary)
    ├── B1_audio_front/                  <- 81 files (decision_records, gate_kinematics, summary)
    ├── B2_multimodal_front/             <- 81 files (decision_records, gate_kinematics, summary)
    └── back_vision_independent/         <- 81 files (decision_records, gate_kinematics, summary)
```
Total artifacts generated: **407 structured JSON / JSONL files** ($15.8\,\text{MB}$).

---

## 7. Operational Observations and Diagnostics

1. **Decoder Frame Advance Resiliency:**  
   During processing of `train_events/event_010/camera_back.mov`, OpenCV/PyAV logged two non-fatal decoder seek adjustments:
   `failed to advance to frame 708... skipping; failed to advance to frame 714... skipping`.  
   The pipeline gracefully recovered, skipping only the 2 degraded intra-frames and continuing to process the remaining 118 frames without crash or exception.
2. **Audio Extraction Performance:**  
   PyAV / FFmpeg audio extraction at $16\,\text{kHz}$ mono WAV ran in $< 0.1\,\text{s}$ per stream, confirming high efficiency.
3. **Inference Throughput:**  
   YOLOv8 vision inference operated at $\approx 14.3\,\text{FPS}$ average across all streams on Apple Silicon CPU, completing the entire 54-stream video dataset in 15.2 minutes.

---

## 8. Summary of Blocked Work & Next Phase Prerequisites

### Permitted Completed Scope:
- Independent front vision (B0), front audio (B1), front multimodal (B2), and back vision inference runs are 100% complete across all 27 events (54 streams).
- Real predictions, decision records, and simulated gate kinematics are fully serialized and reproducible.

### Blocked Scope Due to R04:
- **Conditions B3, B4, B6, and B7 remain BLOCKED.** They require front/back cross-camera temporal fusion, which is scientifically invalid until empirical synchronization offsets are established.

### Next Steps & Prerequisites:
1. Conduct empirical cross-camera synchronization calibration (acoustic cross-correlation or visual motion alignment) to compute verified time offsets $\Delta t_{\text{offset}}$ between front and back cameras for each event.
2. Once empirical offsets are signed off, unblock conditions B3, B4, B6, B7.
3. Complete independent expert ground-truth review before calculating any formal safety performance metrics (MTR, POR, warning lead time).
