# Final Experiment Data Flow

**Document Version:** 6.0.0  
**Date:** 2026-10-09  
**Status:** REFERENCE ARCHITECTURAL GUIDE — Reconciled with Canonical Boundary Taxonomy & AI-Assisted Ground-Truth Workflow  
**Authority:** Referenced by `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        LAYER A: FROZEN DEVELOPMENT (DO NOT TOUCH)               │
│                                                                                 │
│  ┌─────────────────────┐         ┌──────────────────────────────┐              │
│  │ Dataset V1 (Images) │──train──▶│ YOLOv8n (3.2M params)       │              │
│  │ 3,157 frames        │         │ SHA: 3f5bb5b23f82f5d963d2... │              │
│  │ front/rear/side     │         │ Threshold: 0.35              │              │
│  └─────────────────────┘         └──────────────┬───────────────┘              │
│                                                  │ FROZEN                       │
│  ┌─────────────────────┐         ┌──────────────┴───────────────┐              │
│  │ 86 Horn + 86 ESC-50 │──train──▶│ CompactTrainHornCNN (25.7K) │              │
│  │ Audio V3 Dataset    │         │ SHA: ea1bb81d74230af71ba2... │              │
│  │ Fold-partitioned    │         │ Threshold: 0.3700           │              │
│  │ Norm: μ=-1.60 σ=5.12│         │ 16kHz mono, 64 mel bins      │              │
│  └─────────────────────┘         └──────────────┬───────────────┘              │
│                                                  │ FROZEN                       │
│ ═══════════════════════ FIREWALL ═══════════════╪══════════════════════════════ │
│                                                  │                              │
│   BLOCKED CHECKPOINT:                            │                              │
│   models/audio/best_checkpoint.pt (Audio V2)     │                              │
│   SHA: 59b0785f73b201dfd2fb335b98f6ddb764c8...  │                              │
│   [Hard-blocked: Loading raises fatal error]     │                              │
│                                                  │                              │
│                        LAYER B: EVALUATION ONLY  │                              │
│                                                  │                              │
│  ┌──────────────────────────────────────┐        │                              │
│  │ V2 Evaluation Cohort (27 Events)    │        │                              │
│  │ 23 Full Train + 3 No-Train + 1 Eng. │        │                              │
│  │ Unseen recordings (1-2 sites)       │        │                              │
│  │ 54 Video Streams (front + back)     │        │                              │
│  │ + Embedded Audio                    │────────┘                              │
│  └──────────────────────────────────────┘                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

> [!NOTE]
> **Authoritative Full Checksum Specifications:**
> - Frozen YOLOv8n Checkpoint: `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`  
>   Full SHA-256: `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`
> - Frozen Audio V3 Checkpoint: `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`  
>   Full SHA-256: `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`
> - Blocked Audio V2 Checkpoint: `models/audio/best_checkpoint.pt`  
>   Full SHA-256: `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5`


---

## 2. Per-Event Processing Pipeline & Canonical Boundary Evaluation

```
                 ┌────────────────────────────────────────┐
                 │       Event Directory (Layer B V2)     │
                 │   camera_front.mov / camera_back.mov   │
                 └──────────────────┬─────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     │                     ▼
    ┌──────────────────┐            │           ┌──────────────────┐
    │ Front Video      │            │           │ Back Video       │
    │ @ native fps     │            │           │ @ native fps     │
    └─────────┬────────┘            │           └─────────┬────────┘
              │                     │                     │
        Sample @ 5.0 Hz             │               Sample @ 5.0 Hz
              │                     │                     │
              ▼                     │                     ▼
    ┌──────────────────┐            │           ┌──────────────────┐
    │ YOLOv8n          │            │           │ YOLOv8n          │
    │ Inference        │            │           │ Inference        │
    │ conf >= 0.35     │            │           │ conf >= 0.35     │
    └─────────┬────────┘            │           └─────────┬────────┘
              │                     │                     │
              │              ┌──────┴──────┐              │
              │              │ Audio Stream│              │
              │              │ 16kHz mono  │              │
              │              └──────┬──────┘              │
              │                     │                     │
              │              ┌──────┴──────────────┐      │
              │              │ Audio V3 CNN        │      │
              │              │ 1.0s win, 0.5s hop  │      │
              │              │ μ=-1.601, σ=5.124   │      │
              │              │ T* = 0.3700         │      │
              │              └──────┬──────────────┘      │
              │                     │                     │
              ▼                     ▼                     ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                MultimodalEvidenceCollector                   │
    │  Merges per-camera visual detections + acoustic predictions  │
    │  Applies inter-camera offset Δt (measured per event)         │
    │  Output: List[MultimodalFrame]                               │
    └───────────────────────────────┬──────────────────────────────┘
                                    │
                                    ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                  Experiment Condition Filter                 │
    │  E1: Front only, confirm=1 (Stateless)                       │
    │  E2: Front only, confirm=2, EMA (Stateless)                  │
    │  E3: Dual cam, confirm=1 (Stateless)                         │
    │  E4: Dual cam, confirm=2, EMA (Stateless)                    │
    │  E5: Dual cam, confirm=2, EMA + State Machine (No Audio)     │
    │  E6: Dual cam + Audio, confirm=2, EMA (Stateless)            │
    │  E7: Full Proposed Architecture (Dual + Temporal + FSM + Aud)│
    │  E8: Standalone Audio (Audio only, Warning authority only)   │
    └───────────────────────────────┬──────────────────────────────┘
                                    │
                                    ▼
    ┌──────────────────────────────────────────────────────────────┐
    │               Decision Engine & Gate Simulation              │
    │                                                              │
    │  [Warning / Closing Channel] ◀── Vision OR Audio (T* >= 0.37)│
    │                                                              │
    │  ═══════════════ ZERO CLEARANCE AUTHORITY ═════════════════  │
    │  [Clearance / Opening Channel] ◀── Vision ONLY (INV-1)       │
    │  [Audio is physically disconnected from clearance logic]     │
    └───────────────────────────────┬──────────────────────────────┘
                                    │
                                    ▼
    ┌──────────────────────────────────────────────────────────────┐
    │       Event Evaluation vs Canonical Ground Truth (T0-T4)     │
    │                                                              │
    │  Validation: Event-Type-Aware (Full-Train vs No-Train vs Eng)│
    │  T0: First Visible (left-censored events excluded from lat.) │
    │  Hazard Interval: [T1, T4]                                   │
    │  T3: Locomotive Unit Clearance (rear end exits danger zone)  │
    │  T4: Tail Clearance (final vehicle exits danger zone)         │
    │  Premature Opening: Gate open initiated while t < T4         │
    │  Clearance Latency: T_open - T4                              │
    │  No-Train Denominators: Stream 120.79s (overlap unresolved) │
    └──────────────────────────────────────────────────────────────┘
```

---

## 3. Ground Truth Data Flow & Event-Type Validation

```
         [Raw Sensor Media: Front & Back MOV, 16 kHz Mono Audio]
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ STAGE 1: AI Proposal Generation (Gemini Offline Tool)  │
       │ - Offline assistance ONLY; zero runtime model leakage  │
       │ - Proposes candidate T0–T4, horn_status, metadata      │
       │ - Writes immutable raw drafts:                         │
       │   data/ground_truth/proposals/                         │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ STAGE 2: Human Frame-by-Frame Review & Adjudication    │
       │ - Researcher inspects original video & audio frames    │
       │ - Accepts, corrects, or marks unobservable per field   │
       │ - Writes auditable review history:                     │
       │   data/ground_truth/reviews/                           │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ STAGE 3: Approved Ground Truth Certification           │
       │ - Explicit approval_status: "APPROVED" required        │
       │ - Writes approved files to data/ground_truth/          │
       │   (23 train, 3 no-train, 1 engine-only)                │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ Checksum Freeze & Manifest Generation (Prereq R02)     │
       │ data/ground_truth/ground_truth_manifest.json           │
       │ - Locks SHA-256 for: approved, reviews, proposals      │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ GroundTruthLoader & Validator (src/data/...loader.py)  │
       │                                                        │
       │ - Event-type-aware validation (Train vs No-Train vs    │
       │   Engine-Only)                                         │
       │ - Verifies approval_status: "APPROVED"                 │
       │ - Verifies SHA-256 against ground_truth_manifest.json  │
       │ - STRICTLY BLOCKS unreviewed drafts from proposals/   │
       │ - NEVER synthesizes labels or auto-approves            │
       │ - Fail-fast fatal error if missing, invalid, or unapp. │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ Evaluator Metrics Engine (Layer B Pipeline)            │
       │                                                        │
       │ - MTR: Warning commanded by T1                         │
       │ - POR: Gate open commanded before T4                   │
       │ - Clearance Latency: T_open - T4                       │
       │ - No-train: Reports raw counts and exact per-stream    │
       │   exposure (120.79s stream-seconds; overlap unresolved)│
       └────────────────────────────────────────────────────────┘
```

---

## 4. Multi-Level Nuisance Alarm Flow for No-Train Events

```
        ┌─────────────────────────────────────────────────────────────┐
        │                 No-Train Event Video & Audio                │
        │           Total Stream Exposure: 120.788 stream-seconds    │
        │           Concurrent Overlap: UNRESOLVED (no offset data)  │
        └──────────────────────────────┬──────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
  [Camera 1 Frames]             [Camera 2 Frames]             [Audio Windows]
  Front Stream (60.30s)         Back Stream (60.49s)          Audio Track
         │                             │                             │
         ▼                             ▼                             ▼
  [YOLO Conf >= 0.35]           [YOLO Conf >= 0.35]           [Audio p >= 0.3700]
         │                             │                             │
         ▼                             ▼                             ▼
  Front False Frames            Back False Frames             Audio False Windows
  (Camera-Level FP 1)           (Camera-Level FP 2)           (Acoustic-Level FP)
         │                             │                             │
         └──────────────────────┬──────┴─────────────────────────────┘
                                │
                                ▼
         ┌────────────────────────────────────────────────────────────┐
         │             Multimodal Fusion Engine Replay                │
         │                                                            │
         │  Fuses overlapping visual/acoustic triggers within 0.4s   │
         │  into unified System State transitions                     │
         └──────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
         ┌────────────────────────────────────────────────────────────┐
         │       System Nuisance Warning / Closure Episodes           │
         │                                                            │
         │  Count: N_nuisance_episodes (distinct contiguous periods   │
         │  where gate erroneously moved to WARNING or CLOSING)       │
         │                                                            │
         │  Rule: Report observed raw counts alongside per-stream   │
         │  exposure (120.79s); overlap unresolved pending R04.      │
         │  Hourly extrapolation flagged as exploratory/uncertain.   │
         └────────────────────────────────────────────────────────────┘
```

---

## 5. Key Code Modules & Authoritative Roles

| Module | File | Authoritative Role |
|---|---|---|
| **`LeakageGuard`** | `src/railway_detection/experiments/leakage_guard.py` | Enforces parameter freeze, validates YOLO and Audio V3 hashes, and hard-rejects legacy Audio V2 checkpoint. |
| **`GroundTruthLoader`** | `src/railway_detection/data/ground_truth_loader.py` | Event-type-aware parser; validates schema and manifest; verifies `approval_status == "APPROVED"`; rejects unreviewed drafts from `proposals/`; enforces fail-fast abort on missing data; parses canonical `T3_locomotive_unit_clearance` with backward-compatibility alias `T3_locomotive_exit`. |
| **`LayerBEventProcessor`** | `src/railway_detection/experiments/layer_b_processor.py` | Extracts frames (5.0 Hz) and audio (16 kHz mono), runs frozen models, outputs raw evidence streams. |
| **`MultimodalEvidenceCollector`** | `src/railway_detection/fusion/collector.py` | Synchronizes multi-sensor evidence using measured per-event offset $\Delta t$. |
| **`ExperimentRunner`** | `src/railway_detection/experiments/runner.py` | Applies architectural filters for conditions E1 through E8; routes to appropriate engine. |
| **`CrossingStateMachine`** | `src/railway_detection/simulation/state_machine.py` | Formal FSM transition matrix; enforces clearance dwell ($t_{\text{hold}} \ge 3.0\text{s}$) after $T_4$. |
| **`MultimodalDecisionEngine`** | `src/railway_detection/fusion/decision_engine.py` | Connects multimodal evidence to FSM; enforces zero acoustic clearance authority (INV-1). |
| **`EventMetricsCalculator`** | `src/railway_detection/metrics/event_metrics.py` | Computes MTR, POR, latency, lead time against canonical ground truth boundaries ($T_0$–$T_4$); excludes left-censored $T_0$ events from true physical detection-latency denominator. |
| **`NoTrainMetricsCalculator`** | `src/railway_detection/metrics/no_train_metrics.py` | Computes camera-level false frames, acoustic false windows, and system nuisance episodes against audited per-stream exposure (120.79s stream-seconds; concurrent overlap pending R04). |

---

## 6. Document Change Log

| Version | Date | Changes Made |
|---|---|---|
| 4.0.0 | 2026-10-09 | Architectural data flow specification: Established 3-tier safety verification, full SHA-256 for YOLO/Audio V3, hard-blocked Audio V2 checkpoint, and decoupled data flow stages. |
| 5.0.0 | 2026-10-09 | AI-assisted ground-truth integration: Embedded 3-stage lifecycle into data flow; integrated GroundTruthLoader manifest verification; added multi-level nuisance alarm flow. |
| 6.0.0 | 2026-10-09 | Canonical Terminology & Left-Censoring Harmonization Pass: Resolved T3 as **Locomotive Unit Clearance (rear end exits danger zone)**; distinguished locomotive front exit from complete unit clearance; preserved T4 as tail clearance; defined left-censored $T_0$ representation and detection latency denominator exclusion; documented schema key compatibility mapping (`T3_locomotive_unit_clearance` / `T3_locomotive_exit`) preserving proposals v1–v4; reinforced R03 visual landmark provisional status. |
