# Comprehensive Railway Crossing Safety System Test Plan

**Document Version:** 1.0.0  
**Date:** 2026-10-12  
**Status:** CANONICAL TEST STRATEGY & SPECIFICATION  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Referenced Protocols:**  
- `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` (v7.0.0)  
- `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` (v7.0.0)  
- `docs/FINAL_EXPERIMENT_DATA_FLOW.md` (v7.0.0)  
- `data/ground_truth/snapshots/candidate_annotation_manifest_20261012.json`

---

## 1. Executive Strategy & Testing Scope

### 1.1 Objective & Rationale
The primary objective of this testing strategy is to evaluate the technical robustness, schema compliance, data pipeline integrity, fault resilience, and operational safety behavior of the multimodal railway crossing safety monitoring software.

Testing is structured to provide rigorous, evidence-based verification across six discrete layers without violating research protocols or corrupting unapproved candidate annotations.

### 1.2 Mandatory Research Firewalls & Invariants
1. **Approval Firewall Invariant:** No candidate annotation in `data/ground_truth/proposals/` may be auto-approved, ingested by the evaluator, or written to `data/ground_truth/{train_events,no_train_events,engine_events}/` until verified and certified by the human researcher.
2. **Anti-Leakage Invariant:** No detector prediction (YOLO boxes), Audio V3 probability, fusion state, or FSM log may be used to create, modify, or bias annotation labels.
3. **Model Weight Immutability:** Frozen checkpoints (`experiments/vision/39f402dfe460/checkpoints/weights/best.pt` and `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`) and operating thresholds (Audio V3 $\theta = 0.3700$) must remain strictly unaltered.
4. **Camera-Local Timeline Segregation (R04):** Front and back cameras operate on independent media-local timelines. Fused false alarm rates per hour from summed camera exposures are strictly prohibited until empirical cross-camera synchronization is certified.
5. **Acoustic Honesty Invariant:** All 54 audio tracks remain designated `NOT_LISTENED` / `SPECTRAL_ANALYSIS_ONLY`. No human listening judgment is claimed.

---

## 2. Test Layer Architecture (Layers A through F)

```
┌────────────────────────────────────────────────────────────────────────┐
│ TEST LAYER F: Frozen Model Integrity & Cryptographic Checkpoint Audit  │
│ - Vision best.pt SHA-256 (3f5bb5b2...) & size (24,493,159 B)          │
│ - Audio V3 best.pt SHA-256 (ea1bb81d...) & size (329,497 B)           │
│ - Prohibited Audio V2 (59b0785f...) hard-blocking check               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ TEST LAYER A: Unit Tests & Regression Verification                     │
│ - Annotation schema validation (Draft 2020-12)                         │
│ - Canonical timestamp rules (T0–T4), ordering & causality              │
│ - Censoring semantics (left-censored, right-censored, unobservable)    │
│ - Engine-only coincidence rule (T3 = T4)                               │
│ - Horn status schema & acoustic metadata                               │
│ - Proposal immutability & SHA-256 validation                           │
│ - Approval firewall enforcement & GroundTruthLoader rejection          │
│ - Regression tests for forensic audit defects                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ TEST LAYER B: Dataset & Annotation Integrity Checks                    │
│ - 27-event active cohort presence & structure (23 full, 3 no, 1 eng)   │
│ - Historical duplicate (event_historical_duplicate_010) exclusion     │
│ - Raw media references & timestamp/frame math at native FPS            │
│ - Master review index vs candidate proposal synchronization            │
│ - Provenance lineage & snapshot hash verification                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ TEST LAYER C: Pipeline & Integration Tests                             │
│ - Video ingestion & frame sampling pipelines                           │
│ - Audio preprocessing & spectrogram extraction                         │
│ - Frozen model loader instantiation & inference smoke testing          │
│ - State management (State Machine / FSM transitions)                   │
│ - Alarm dispatch logic & clearance timing                              │
│ - Error handling: truncated, missing, corrupted, or unsupported media  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ TEST LAYER D: Synthetic & Fault-Injection Safety Tests (12 Scenarios)  │
│ - Scenario 1: Train present at frame zero (T0 left-censoring)          │
│ - Scenario 2: Crossing already occupied at t=0 (T1/T2 unobservable)   │
│ - Scenario 3: Video truncated before tail clearance (T4 right-censored)│
│ - Scenario 4: Engine-only passage (0 cars, T3 = T4)                    │
│ - Scenario 5: Road traffic horns in no-train environment               │
│ - Scenario 6: Engine rumble without confirmed horn                     │
│ - Scenario 7: Corrupted or missing audio/video streams                 │
│ - Scenario 8: Asymmetric camera start offsets (independent clocks)     │
│ - Scenario 9: Repeated timestamps from simulated fallback defect       │
│ - Scenario 10: Out-of-order or duplicate timestamp markers             │
│ - Scenario 11: Intermittent optical detection dropout during traversal │
│ - Scenario 12: Degraded lighting & acoustic background noise           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ TEST LAYER E: Natural-Media Replay & Operational FSM Behavior          │
│ - Exploratory execution on raw sensor media (front/back streams)       │
│ - End-to-end state transitions (APPROACHING -> OCCUPYING -> CLEARING)  │
│ - False trigger monitoring on negative control recordings (001-003)    │
│ - Strict separation from ground truth: NO accuracy/recall metrics      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Specifications by Layer

### Layer A — Unit Tests & Forensic Regressions
- **Scope:** Unit-level verification of core logic in `railway_detection` package.
- **Components Tested:**
  - `railway_detection.annotation.schema`: Full-train, no-train, and engine-only JSON schemas.
  - `railway_detection.annotation.firewall`: Rejection of unapproved candidate proposals by evaluator loaders.
  - `railway_detection.annotation.timestamp`: Timestamp ordering ($T_0 \le T_1 \le T_2 \le T_3 \le T_4$).
  - `railway_detection.annotation.engine`: Engine-only coincidence invariant ($T_3 \equiv T_4$).
  - `railway_detection.annotation.horn`: Validation of `horn_status` enum (`present`, `absent_observed`, `unobservable_noise`, `uncertain_poor_quality`).
  - `railway_detection.annotation.immutability`: Invariant preventing overwriting of earlier proposal versions without updating version number and lineage pointer.
  - `railway_detection.annotation.sha256`: SHA-256 checksum string validator (64 lowercase hexadecimal characters).
- **Forensic Regression Tests:**
  - *Regression 1:* Prevent hardcoded fallback timestamp formulas (`T1=3.0s, T2=3.7s, T3=3.5s`).
  - *Regression 2:* Prevent conflating internal trackside landmarks (e.g., relay cabinet at 5.60s) with the canonical exit boundary plane (6.00s).
  - *Regression 3:* Prevent treating linear power ratio (156.4) as calibrated decibels without logarithmic conversion ($10 \log_{10}(P) \approx 21.94\text{ dB}$).
  - *Regression 4:* Prevent pooling summed camera-stream seconds as concurrent wall-clock exposure.

### Layer B — Dataset & Annotation Integrity Tests
- **Scope:** Complete verification of all 27 candidate proposals, review sheets, and raw media records.
- **Checks:**
  - Active cohort size: strictly 27 events.
  - Exclusion check: `event_historical_duplicate_010` is absent from active proposals.
  - Media reference check: Every referenced `.mov` file exists on disk and matches recorded SHA-256.
  - Native FPS math: Frame indices match $f = \text{round}(t \times \text{FPS})$ within 1 frame tolerance.
  - Schema parity across retained historical proposals (`v1` through `v6`).
  - Master index synchrony: `ANNOTATION_BATCH_REVIEW_INDEX.md` entries match proposal JSON contents exactly.
  - Unapproved status check: All proposals declare `raw_proposal_immutable: true` and lack approval certification.

### Layer C — Pipeline & Integration Tests
- **Scope:** Execution of ingestion, model loading, feature extraction, and state machine components.
- **Checks:**
  - Video stream decoding via FFmpeg / OpenCV without frame loss.
  - Audio extraction and log-mel spectrogram generation at $16\text{ kHz}$.
  - Vision model loading from `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`.
  - Audio V3 model loading from `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`.
  - State machine transitions: `IDLE` $\rightarrow$ `APPROACHING` $\rightarrow$ `OCCUPIED` $\rightarrow$ `CLEARING` $\rightarrow$ `IDLE`.
  - Gate control command generation: asserting warning on danger-zone entry, releasing warning on verified clearance.
  - Error recovery: pipeline handles missing audio tracks, truncated video files, and unreadable containers gracefully without crashing.

### Layer D — Synthetic & Fault-Injection Tests (12 Scenarios)
- **Scope:** Controlled fault injection simulating extreme railway crossing operational edge cases.
- **12 Test Scenarios:**
  1. *Frame 0 Train Presence:* Train present in frame 0; system initiates warning immediately and flags latency as left-censored.
  2. *Crossing Already Occupied:* Train blocking crossing at $t=0$; system enters `OCCUPIED` state immediately without waiting for approach sequence.
  3. *Premature Truncation:* Recording ends while train is still in crossing; system maintains safe `OCCUPIED` state and logs truncation alert rather than opening gates.
  4. *Engine-Only Passage:* Traversal with 0 trailing cars; system handles identical $T_3 / T_4$ exit timing without dropout or false clearance re-triggers.
  5. *Acoustic Road Traffic Noise:* Heavy road traffic horns in no-train recording; system correctly discriminates via multimodal visual confirmation, avoiding false alarms.
  6. *Engine Rumble Without Horn:* Low-frequency diesel rumble without horn blast; system relies on visual gating to trigger warning.
  7. *Media Corruption:* Ingestion of corrupted or zero-byte audio/video file; pipeline catches `CorruptedMediaError` and fails safely without unhandled exception.
  8. *Asymmetric Camera Clocks:* Simulating 5.0s offset between front and back streams; pipeline processes streams independently without invalid cross-camera latency inference.
  9. *Repeated Timestamps:* Proposal validator detects and rejects duplicated fallback timestamps across distinct physical events.
  10. *Out-of-Order Timestamps:* Validator detects and rejects invalid timestamps violating physical causality ($T_4 < T_3$ or $T_2 < T_1$).
  11. *Visual Detection Dropout:* Simulated 3-frame optical dropout while train traverses crossing; temporal smoothing (EMA / hangover timer) maintains `OCCUPIED` state, preventing premature gate opening.
  12. *Degraded Visibility & Noise:* Low-light synthetic noise injection; system maintains robust state tracking.

### Layer E — Natural-Media Replay & Operational Behavior
- **Scope:** Exploratory end-to-end replay on raw sensor recordings from `data/raw/layer_b/v2/`.
- **Operating Constraints:**
  - No model training, fine-tuning, or threshold modification.
  - Outputs evaluated strictly for operational stability, runtime performance, and FSM transition health.
  - Zero performance claims (accuracy, recall, POR, latency against ground truth) are derived, as ground truth remains unapproved.
  - Front and back cameras replayed on separate camera-local timelines.

### Layer F — Frozen Model Integrity & Checkpoint Verification
- **Scope:** Cryptographic verification of all model checkpoints before test execution.
- **Checkpoints Verified:**
  - Vision: `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`
    - SHA-256: `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`
    - Expected Size: `24,493,159` bytes
  - Audio V3: `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`
    - SHA-256: `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`
    - Expected Size: `329,497` bytes
    - Operating Threshold: `0.3700`
  - Prohibited Audio V2: `models/audio/best_checkpoint.pt`
    - Prohibited SHA-256: `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5`
    - Hard-blocked: Execution halts if this checkpoint is selected.

---

## 4. Execution Sequence & Acceptance Criteria

### 4.1 Execution Sequence
1. Layer F Checkpoint Integrity Audit.
2. Layer A Unit & Forensic Regression Suite.
3. Layer B Dataset & Annotation Integrity Suite.
4. Layer C Pipeline & Integration Suite.
5. Layer D Synthetic & Fault-Injection Suite (12 Scenarios).
6. Layer E Natural-Media Replay Smoke Suite.
7. Bug Investigation & Remediation (if failures occur).
8. Re-testing & Final Results Compilation (`results/testing/FINAL_TEST_RESULTS.md`).

### 4.2 Layer Acceptance Criteria
- **Pass Criterion (Layers A, B, C, D, F):** 100% of defined assertions pass. Zero unhandled exceptions.
- **Safety Criterion (Layer D Fault Injection):** In every simulated hazardous scenario (dropout, truncation, frame 0 presence), the safety system defaults to the safe state (`WARNING_ACTIVE` / `OCCUPIED`). Zero simulated premature gate openings.
- **Firewall Criterion:** Zero candidate proposals auto-approved. Zero approved ground truth files written.
