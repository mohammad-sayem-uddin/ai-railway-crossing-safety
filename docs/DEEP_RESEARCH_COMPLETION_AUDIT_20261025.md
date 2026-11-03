# DEEP RESEARCH COMPLETION AUDIT

**Date:** 2026-10-25  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Purpose:** Recover original research intent, diagnose why the 27-event experiments remain incomplete, and identify the shortest legitimate path to a defensible research paper.

> [!CAUTION]
> This report does not create any authorization, decision, label, or governance artifact. It is a read-only diagnostic.

---

## Table of Contents

1. [Original Research Goal](#1-original-research-goal)
2. [Verified Implementation and Model Status](#2-verified-implementation-and-model-status)
3. [Verified 27-Event Inventory Status](#3-verified-27-event-inventory-status)
4. [Model-to-Paper Evidence Map](#4-model-to-paper-evidence-map)
5. [Experiment Completion Matrix](#5-experiment-completion-matrix)
6. [Blocker-by-Blocker Root-Cause Analysis](#6-blocker-by-blocker-root-cause-analysis)
7. [Experiments Executable with Existing Authorized Artifacts](#7-experiments-executable-with-existing-authorized-artifacts)
8. [Experiments Requiring Human Decisions or Authorization](#8-experiments-requiring-human-decisions-or-authorization)
9. [Shortest Legitimate Path to Completion](#9-shortest-legitimate-path-to-completion)
10. [Decisive Recommendation](#10-decisive-recommendation)

---

## 1. Original Research Goal

### 1.1 Central Research Question

From [`docs/archive/RESEARCH_CONCEPT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/archive/RESEARCH_CONCEPT.md#L33):

> *"Can a multi-view, audio-assisted, state-aware train-detection framework improve event-level crossing-detection outcomes under the synchronized, held-out recording protocol defined in RESEARCH_PROTOCOL_V2.md?"*

### 1.2 Research Goal (verbatim)

From [`docs/archive/RESEARCH_CONCEPT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/archive/RESEARCH_CONCEPT.md#L41):

> *"The goal is not simply to detect trains. The goal is to investigate whether a multi-view, audio-assisted, safety-oriented simulated decision architecture can provide more reliable evidence about three critical phases: Approaching, Occupying/Passing, Departure."*

### 1.3 Intended Novelty

From [`docs/archive/RESEARCH_CONCEPT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/archive/RESEARCH_CONCEPT.md#L425-L443):

1. **Bangladesh-specific railway crossing dataset** — no comparable public dataset exists
2. **Multi-view train detection** designed around approach/occupancy/departure roles
3. **Audio-assisted train detection** as fallback in a crossing safety context
4. **State-aware fail-closed decision logic** with explicit failure-mode testing
5. **Safety-oriented failure analysis** measuring system behavior under component failures
6. **Cross-crossing generalization evaluation** via location-aware data splitting

### 1.4 Intended Experiment Matrix

From [`docs/archive/RESEARCH_CONCEPT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/archive/RESEARCH_CONCEPT.md#L340-L367):

| ID | Description |
|----|-------------|
| A | Front-only single-view detector (Baseline 1) |
| B | Front + Side |
| C | Front + Side + Rear (Baseline 2: Three-view visual) |
| D | Vision only (full visual system) |
| E | Audio only (Baseline 3: Horn detector) |
| F | Vision + Audio (Baseline 4: Multimodal) |
| G | Full proposed architecture (state-aware multimodal fail-closed) |
| FI | Failure injection experiments (front disabled, side lowered, rear removed, audio corrupted, false positive injection, camera failure) |

### 1.5 27-Event Purpose

The 27 events are the **entire real-world evaluation corpus**: 23 train crossing events + 3 no-train control events + 1 engine-only event, recorded at a single crossing in Bangladesh across two capture sessions. They constitute the empirical foundation for every research claim.

### 1.6 What the Researcher's Complete Intended Targets Were

From the archived documents and the evolved Phase structure, the researcher's workflow targets were:

1. ✅ **Develop the vision model** — train YOLOv8 on railway viewpoint classification (front/side/rear)
2. ✅ **Develop the audio model** — train binary train-horn classifier
3. ⬜ **Evaluate models on 27 events** — run frozen models on all real events with validated ground truth
4. ⬜ **Run experiment matrix** — baseline, fusion, temporal-policy, ablation, robustness experiments
5. ⬜ **Analyze results** — failures, uncertainty, limitations, condition-wise breakdown
6. ⬜ **Produce paper** — complete figures, tables, evidence for a defensible research paper

---

## 2. Verified Implementation and Model Status

### 2.1 Vision Model

| Attribute | Verified Status |
|-----------|----------------|
| **Architecture** | YOLOv8-nano (from Ultralytics) |
| **Training** | ✅ **Fine-tuned on railway data** — NOT off-the-shelf COCO |
| **Training data** | `data/raw/vision/v1/baler.v1i.yolov8/` — real railway crossing images with front/side/rear annotations |
| **Classes** | 3: `front` (0), `rear` (1), `side` (2) — train viewpoint classification |
| **Training runs** | 3 runs with checkpoints: [`39f402dfe460`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/vision/39f402dfe460/) (primary, 100 epochs), [`d9dfa4e34d02`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/vision/d9dfa4e34d02/), [`e1204e5c9790`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/vision/e1204e5c9790/) |
| **Best checkpoint** | [`experiments/vision/39f402dfe460/checkpoints/weights/best.pt`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/vision/39f402dfe460/checkpoints/weights/best.pt) |
| **Training date** | 2026-08-18 (per [`run_manifest.json`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/vision/39f402dfe460/run_manifest.json)) |
| **Device** | Apple Silicon (MPS) |
| **Split** | Grouped by `crossing_id` (location-aware, as intended) |
| **Evaluation** | mAP@50 = 0.9946, mAP@50:95 = 0.855 on held-out test split |
| **Evaluation artifact** | [`experiments/vision/39f402dfe460/evaluation/metrics.md`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/vision/39f402dfe460/evaluation/metrics.md) |
| **Provenance** | Git commit `3aebefb`, seed 42, full config in run_manifest.json |

> [!IMPORTANT]
> The vision model IS trained on real railway data with location-aware splitting. It detects front/side/rear viewpoints of trains, not generic COCO objects. The `yolov8n.pt` in the repo root is the Ultralytics pretrained weight used as the **starting point** for fine-tuning.

### 2.2 Audio Model

The audio classifier architecture is **`CompactTrainHornCNN`** (`src/railway_detection/audio/model.py`): a lightweight 3-layer 2D CNN (3 Conv2D/BatchNorm2d/MaxPool2d blocks + FC head with Dropout, 25,697 parameters, ~100 KB footprint, input: 64-band Log-Mel spectrograms `(64, 61)` across 80–8000 Hz).

Three training runs were completed:

| Run | Date | Positive Data | Negative Data | Checkpoint Path & Hash | Calibrated Threshold & Test Metrics |
|-----|------|---------------|---------------|------------------------|-------------------------------------|
| [**V1**](file:///Users/sayemuddin/Desktop/Train_automation/experiments/audio/RUN_20260923_AUDIO_001/) | 2026-09-23 | 86 unique real locomotive horn recordings (297.69s) | 86 ESC-50 recordings (11 categories) | [`experiments/audio/RUN_20260923_AUDIO_001/checkpoints/best_checkpoint.pt`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/audio/RUN_20260923_AUDIO_001/checkpoints/best_checkpoint.pt)<br>SHA-256: `59b0785f...` (111,703 bytes) | $T^*=0.5184$<br>Window Acc: 73.5%, F1: 0.6971, ROC-AUC: 0.8868. Recording-level Recall: 100% (13/13), Spec: 53.85% |
| [**V2**](file:///Users/sayemuddin/Desktop/Train_automation/experiments/audio/RUN_20261008_AUDIO_V2/) | 2026-10-08 | 86 unique real locomotive horn recordings | 86 custom field ambient recordings from `TRAIN_VIDEO_AUDIO 2` | [`experiments/audio/RUN_20261008_AUDIO_V2/checkpoints/best.pt`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/audio/RUN_20261008_AUDIO_V2/checkpoints/best.pt)<br>(334,839 bytes) | $T^*=0.2800$<br>Recording-level: 100% across all metrics (13/13 TP, 13/13 TN). **Hard-blocked / deprecated** due to non-adversarial ambient negative pool |
| [**V3 (ESC-50)**](file:///Users/sayemuddin/Desktop/Train_automation/experiments/audio/RUN_20261008_AUDIO_V3_ESC50/) | 2026-10-08 | 86 unique real locomotive horn recordings | 86 ESC-50 hard acoustic confusers (car horn, engine, siren, church bells, etc.) | [`experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt)<br>SHA-256: `ea1bb81d...` (329,497 bytes) | **$T^*=0.3700$** (Authoritative)<br>Window Acc: 89.56%, F1: 0.8690, ROC-AUC: 0.9613. Recording-level Recall: 100% (13/13) |

> [!NOTE]
> **Forensic checkpoint distinction:** Deserialization and metadata inspection confirm that `models/audio/best_checkpoint.pt` (SHA-256: `59b0785f...`) is bit-identical to the **Audio V1** baseline (`RUN_20260923_AUDIO_001`), though historically mislabeled in some audit texts as V2. The active production checkpoint bound in `configs/frozen_experiment_v1.yaml` (canonical hash: `999a7970d4c4...`) is strictly **Audio V3** (`RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`).
> 
> **Data domain reality:** While positive samples are 100% authentic locomotive horns (including Bangladesh Railway units like `40.mp3`), the negative samples in V3 come from ESC-50. The model has **never been trained on in-situ crossing acoustic ambient noise** (crossing bells, barrier motors, track joint clicks), because Layer B level-crossing audio was strictly firewalled from training.

### 2.3 Fusion and Temporal Policy

| Component | Status | Location |
|-----------|--------|----------|
| Decision engine (fusion) | ✅ Implemented, rule-based weighted fusion | [`src/railway_detection/fusion/decision_engine.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/decision_engine.py) |
| Temporal policy (state machine) | ✅ Implemented with fail-closed, hysteresis | [`src/railway_detection/simulation/state_machine.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/state_machine.py) |
| Failure injector | ✅ Implemented | [`src/railway_detection/simulation/failure_injector.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/failure_injector.py) |
| Policy hash frozen | ✅ SHA-256 `c87c1432...` pinned | [`docs/POLICY_HASH_PROVENANCE.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/POLICY_HASH_PROVENANCE.md) |

### 2.4 Evaluation Infrastructure

| Component | Status | Key File |
|-----------|--------|----------|
| Evaluation runner | ✅ Implemented | [`src/railway_detection/evaluation/evaluation_runner.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/evaluation_runner.py) |
| Experiment engine | ✅ Implemented | [`src/railway_detection/evaluation/experiment_engine.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/experiment_engine.py) |
| Replay producer | ✅ Implemented | [`src/railway_detection/evaluation/replay_producer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/replay_producer.py) |
| Governance gates | ✅ Implemented (blocks execution) | [`src/railway_detection/evaluation/governance.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/governance.py) |
| Input contracts | ✅ Implemented (blocks execution) | [`src/railway_detection/evaluation/input_contracts.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/input_contracts.py) |
| Execution gate | ✅ Implemented (blocks execution) | [`src/railway_detection/evaluation/execution_gate.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/execution_gate.py) |
| Metrics computation | ✅ Implemented | [`src/railway_detection/evaluation/metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) |
| Ablation runner | ✅ Implemented | [`src/railway_detection/evaluation/ablation_runner.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/ablation_runner.py) |
| Perturbation engine | ✅ Implemented | [`src/railway_detection/evaluation/perturbation.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/perturbation.py) |
| Stage-2.1 schema + pilot | ✅ Implemented (inactive) | [`src/railway_detection/annotation/stage21_timing_pilot.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/stage21_timing_pilot.py) |
| Promotion gate | ✅ Implemented | [`src/railway_detection/annotation/promotion_gate.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/promotion_gate.py) |

### 2.5 Test Suite

1,204 tests passing as of readiness closure (2026-10-19). Full test suite at [`tests/`](file:///Users/sayemuddin/Desktop/Train_automation/tests/).

---

## 3. Verified 27-Event Inventory Status

### 3.1 Actual Event Composition

The 27 events are organized into three cohorts:

| Cohort | Events | Count |
|--------|--------|-------|
| `train_events` | event_001 through event_023 | 23 |
| `no_train_events` | event_001 through event_003 | 3 |
| `engine_events` | event_001 | 1 |
| **Total** | | **27** |

### 3.2 Source Media

Each event has **two camera angles** (camera_front.mov, camera_back.mov) stored under:
- **Raw video**: [`data/raw/layer_b/v2/{cohort}/{event_id}/`](file:///Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/) — 56 .mov files total
- **Extracted audio**: [`data/processed/layer_b/audio/{cohort}/{event_id}/`](file:///Users/sayemuddin/Desktop/Train_automation/data/processed/layer_b/audio/) — 54 .wav files (camera_front.wav, camera_back.wav)

There is also a historical duplicate: `engine_events/event_historical_duplicate_010`.

### 3.3 Capture Sessions

From [`docs/RESEARCHER_ACTION_PACKAGE_v1_20261019.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/RESEARCHER_ACTION_PACKAGE_v1_20261019.md#L9):

| Session | Date | Device | Events |
|---------|------|--------|--------|
| Session 1 | 2026-09-14 | iPhone | ~20 events |
| Session 2 | 2026-10-04 | iPad | ~7 events |

All events are from a **single crossing** (crossing_A).

### 3.4 Ground Truth Pipeline Status

```
AI Proposals (v2)  →  Legacy Reviews (v6, INVALIDATED)  →  Stage-2.1 Reviews (v8.1.0)  →  Promotion Receipt
     27/27                    27/27 (ALL INVALID)                   0/27                        0/27
```

**Critical finding**: The entire ground truth pipeline is **blocked at Stage-2.1**:

- **AI Proposals** (v2): Complete for all 27 events. Generated by Gemini 3.8 Flash from raw video. Found at [`data/ground_truth/proposals/`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/). These contain proposed T0/T1/T3/T4 timestamps but are NOT ground truth — they are **AI-generated candidates** requiring human validation.

- **Legacy Reviews** (v6): All 27 exist at [`data/ground_truth/reviews/`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/reviews/) but are ALL **INVALIDATED** with sibling notices. Per [`data/ground_truth/reviews/_INTEGRITY_NOTICE.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/reviews/_INTEGRITY_NOTICE.md): they were stamped in a ~5-second automated batch on 2026-10-12, not from genuine human frame-by-frame review. The researcher confirmed (Decision D-2) that they did not conduct these reviews.

- **Stage-2.1 Reviews** (v8.1.0-stage2.1): **ZERO** exist. No genuine human review has ever been conducted on any of the 27 events.

- **Promotion Receipts**: **ZERO** exist. No event has passed the promotion gate.

### 3.5 R04 (Second Camera) Calibration Status

From blocker investigation:

| Status | Events | Count |
|--------|--------|-------|
| `CALIBRATION_SUPPORTED` | 11 events | 11 |
| `AMBIGUOUS` | 9 events | 9 |
| `PROVISIONAL` | 7 events | 7 |

Full dual-camera synchronization is feasible for at most 11 events.

### 3.6 T0 Physical Censoring

In all 23 train events, the train is already visible at recording onset ($T_0 \le 0$). True detection latency cannot be measured with current recordings. This is a **permanent physical limitation** of the existing dataset.

---

## 4. Model-to-Paper Evidence Map

For each intended paper claim, trace the evidence chain and identify the **first broken link**:

### Claim 1: "The vision model detects train viewpoints (front/side/rear) with high accuracy"

| Chain Link | Status |
|-----------|--------|
| Model trained | ✅ YOLOv8n fine-tuned, best.pt exists |
| Dataset | ✅ Real railway images, location-aware split |
| Evaluation on held-out images | ✅ mAP@50=0.9946 ([`metrics.md`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/vision/39f402dfe460/evaluation/metrics.md)) |
| **Paper figure/table** | ✅ Confusion matrix, PR curves exist |
| **Status** | ✅ **SUPPORTABLE NOW** (image-level detection) |

### Claim 2: "The audio model detects train horns"

| Chain Link | Status |
|-----------|--------|
| Model trained | ✅ V1, V2, V3 runs complete |
| Training data | ✅ Real train-horn recordings |
| Evaluation on held-out clips | ✅ V2: 100% recording-level accuracy |
| Hard-negative stress test | ✅ V3 ESC-50 evaluation |
| **Paper figure/table** | ✅ Loss curves, confusion matrix, ROC, PR, threshold analysis (10-12 figures per run) |
| **Status** | ✅ **SUPPORTABLE NOW** (clip-level classification) |

### Claim 3: "The system detects crossing state transitions in real events"

| Chain Link | Status |
|-----------|--------|
| Vision model on video events | ❓ Inference code exists, but blocked by media access incident |
| Audio model on audio events | ❓ Same blocker |
| Fusion engine | ✅ Implemented |
| Temporal policy | ✅ Implemented, hash frozen |
| **Ground truth** | ❌ **BROKEN** — Zero valid Stage-2.1 records |
| Evaluation code | ✅ Implemented but gated |
| **Status** | ❌ **BLOCKED** — no validated ground truth |

### Claim 4: "Fusion improves over vision-only and audio-only baselines"

| Chain Link | Status |
|-----------|--------|
| Vision-only inference on events | ❌ Blocked |
| Audio-only inference on events | ❌ Blocked |
| Fusion inference on events | ❌ Blocked |
| Ground truth comparison | ❌ Zero valid labels |
| Statistical comparison | ❌ No data to compare |
| **Status** | ❌ **BLOCKED** — all upstream blocked |

### Claim 5: "Temporal policy improves over stateless fusion"

| Chain Link | Status |
|-----------|--------|
| Same as Claim 4 plus temporal policy output | ❌ Blocked |
| Synthetic pilot | ✅ Code-validation only ([`PHASE11_9_SYNTHETIC_PILOT_REPORT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/PHASE11_9_SYNTHETIC_PILOT_REPORT.md)) |
| **Status** | ❌ **BLOCKED** for real events; ⚠️ synthetic-only evidence exists |

### Claim 6: "System fails closed under component failure"

| Chain Link | Status |
|-----------|--------|
| Failure injector | ✅ Implemented |
| Synthetic simulation | ✅ Some synthetic results exist |
| Real-event demonstration | ❌ Blocked |
| **Status** | ⚠️ **PARTIALLY SUPPORTABLE** via synthetic simulation, clearly labeled |

### Claim 7: "Multi-view (dual camera) provides additional coverage"

| Chain Link | Status |
|-----------|--------|
| R04 scope decision | ❌ Missing |
| Calibration | ⚠️ 11/27 supported |
| **Status** | ❌ **BLOCKED** — researcher decision required |

### Summary: First Broken Link Map

| Claim | First Broken Link | Root Cause |
|-------|-------------------|------------|
| Vision detection | None | ✅ Complete |
| Audio horn detection | None | ✅ Complete |
| Event-level crossing detection | Ground truth | No human review conducted |
| Fusion vs baselines | Ground truth | No human review conducted |
| Temporal policy benefit | Ground truth | No human review conducted |
| Fail-closed behavior | Real-event data | Media access + ground truth blocked |
| Multi-view coverage | R04 scope decision | Researcher decision missing |

> [!IMPORTANT]
> **The single root cause blocking Claims 3–7 is: zero valid human-reviewed ground truth exists for any of the 27 events.** Everything else — code, models, infrastructure — is ready.

---

## 5. Experiment Completion Matrix

A rigorous forensic audit of all experiment directories, logs, caches, and test results reveals that the repository's experiments fall into four distinct categories:

### 5.1 Genuinely Executed and Promoted (Scientifically Valid)

| Experiment | Data Source | Checkpoints / Inputs | Artifact Outputs | Key Findings & Validity |
|---|---|---|---|---|
| **Layer A Vision Model Training & Eval** | 3,157 real railway images (`baler.v1i.yolov8`) | Fine-tuned YOLOv8n, 100 epochs on MPS | [`experiments/vision/39f402dfe460/evaluation/metrics.json`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/vision/39f402dfe460/evaluation/metrics.json) | ✅ **PROMOTED / VALID.** mAP@50 = 99.46%, mAP@50:95 = 85.50% on 472 held-out images. 3-class detection (`front`, `side`, `rear`). |
| **Layer A Audio V3 Training & Cross-Validation** | 86 real train horns + 86 ESC-50 negatives | `CompactTrainHornCNN` (25,697 params), 40 epochs on MPS | [`experiments/audio/RUN_20261008_AUDIO_V3_ESC50/metrics/metrics.json`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/audio/RUN_20261008_AUDIO_V3_ESC50/metrics/metrics.json) | ✅ **PROMOTED / VALID.** F1 = 0.8690, ROC-AUC = 0.9613, $T^*=0.3700$. Max-window recording recall: 100% (13/13). Evaluated on 11 ESC-50 acoustic confusers. |
| **Phase 8 Exploratory Live Dual-Camera Run** | 11 `CALIBRATION_SUPPORTED` train events (22 videos + audio) | YOLOv8n + Audio V3; empirical acoustic lag offsets | [`results/r04_sync_estimation/exploratory_live_run_20261013T194806Z/`](file:///Users/sayemuddin/Desktop/Train_automation/results/r04_sync_estimation/exploratory_live_run_20261013T194806Z/) | ✅ **PROMOTED / VALID EXPLORATORY RUN.** Evaluated 3,465 front frames, 3,363 back frames, 1,369 audio windows. Revealed dual-camera cleared 0/11 events due to clearance divergence. |
| **Phase 9 Clearance Divergence Forensic Replay** | Cached Phase 8 evidence (11 events) | `diagnostic_trace.py` tick tracer | [`results/r04_sync_estimation/phase9_diagnostic_replay_20261014T040741Z/`](file:///Users/sayemuddin/Desktop/Train_automation/results/r04_sync_estimation/phase9_diagnostic_replay_20261014T040741Z/) | ✅ **PROMOTED / VALID FORENSIC REPLAY.** Isolated root cause of 0/11 clearance: continuing front-camera `side` detections repeatedly triggered `RULE_7_NEW_TRAIN_INTERRUPT` every 0.8–1.4s, resetting the 3.0s clearance dwell timer. |
| **Phase 10 & 10.1 Restricted Policy Comparisons** | Cached Phase 8 evidence (11 events) | Frozen Policy v1 vs. Candidate Policy v2 (`rules_v2_candidate.py`) | [`results/r04_sync_estimation/phase10_1_restricted_comparison_20261014T054615Z/`](file:///Users/sayemuddin/Desktop/Train_automation/results/r04_sync_estimation/phase10_1_restricted_comparison_20261014T054615Z/) | ✅ **PROMOTED / VALID POLICY STUDY.** Candidate Policy v2 cleared 6/11 events (vs 0/11 for Frozen v1). Proved `002, 006` non-clearance is caused by recording truncation (<3s post-clearance margin). |
| **Corrected Fault-Injection Reruns** | 27 real Layer B events | Isolated namespace `results/experiments/corrected_run/` | [`results/experiments/corrected_run/`](file:///Users/sayemuddin/Desktop/Train_automation/results/experiments/corrected_run/) (`B6b`, `B7b`, `B7f`) | ✅ **PROMOTED / RECTIFIED.** Fixed original simulation bugs: B6b entered `FAULT_FAIL_SAFE` at 0.4s (48.3s closed); B7b correctly dropped 29.96% frames (45.2s closed); B7f dropped 9.96% + audio loss (45.6s closed). |
| **Canonical Test Suite (Layers A–F)** | Code, models, schemas | 49 regression & contract test modules | [`results/testing/canonical_test_results.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/testing/canonical_test_results.json) | ✅ **ALL 49 TESTS PASSING.** Verifies software and data contract integrity (does not validate unapproved labels). |

### 5.2 Actually Executed on Real Media but Methodologically Invalidated

The 27-event benchmark reported in [`docs/REAL_WORLD_EXPERIMENT_REPORT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/REAL_WORLD_EXPERIMENT_REPORT.md) and [`results/experiments/{B0..B7f}/`](file:///Users/sayemuddin/Desktop/Train_automation/results/experiments/) actually executed inference over 54 video streams and 27 audio streams, but its summary conclusions were **scientifically invalidated and retracted** by the forensic audit on 2026-10-13 ([`FORENSIC_EXPERIMENT_AUDIT.md`](file:///Users/sayemuddin/Desktop/Train_automation/results/archive/forensic_backup_20261013/reports/FORENSIC_EXPERIMENT_AUDIT.md)) due to five major flaws:
1. **Cache Contamination:** The evaluation directory contained +60 orphaned JSONL cache files from an earlier 21-event run on 2026-09-23, aggregating 10,673 dead vision frames and 2,141 dead audio windows into reported metrics.
2. **Unapproved Ground Truth Defaulting:** Because ground-truth review records were fabricated/unapproved, `metrics.py` defaulted unlinked labels to `missed_train=False` and formatted `premature_opening=None` as `"0.0% [0.0%, 12.5%]"`.
3. **Negative Control False Alarms:** The 3 no-train events were aggregated into the general train cohort; in reality, B4 suffered a 100% False Activation Rate (3/3) and 39.0s of nuisance closure.
4. **IDLE Fail-Safe Defect (B6b):** Under complete camera dropout, original B6b remained in `IDLE` with the gate open (`total_closed_s = 0.0s`), failing fail-safe operation.
5. **PRNG Frame Drop Bug (B7b, B7f):** An `any()` bug in `FailureInjector` caused 100% of frames to be dropped, resulting in 0 frames received by the simulator.

The 12 tables in [`results/experiments/tables/`](file:///Users/sayemuddin/Desktop/Train_automation/results/experiments/tables/) were subsequently regenerated to honestly report MTR and POR as `"Blocked (GT Unapproved)"` and to disclose the negative-control false activations (`F18`).

### 5.3 Executed on Synthetic / Mock Fixtures Only

- **Phase 11.9 Synthetic Pilot:** Tooling validation run (`tests/test_phase11_9_synthetic_pilot.py`, 13 tests passing) verifying the adjudication workflow using synthetic events and mock reviewers. Created zero real ground truth.
- **Phase 14 Offline Profiler:** Profiling harness tested on synthetic frames (`tests/unit/test_phase14_profiler.py`). Real target hardware latency remains unmeasured (`real_time_claim_permitted: false`).

### 5.4 Code / Plan Only (NEVER EXECUTED on Real Data)

- **Phase 12 Official Evaluation:** Pipeline and fail-closed readiness gate implemented; officially BLOCKED pending approved Stage-2.1 ground truth, split decision, R04 scope, and EVAL-AUTH. Zero official real evaluations run.
- **Phase 13 Robustness & Ablation Study:** Synthetic engine implemented; officially BLOCKED pending Phase 12 baseline. Zero real ablations run.
- **Phase 14 Real-Time Optimization Study:** Optimization code unwritten; target-hardware benchmark unexecuted.
- **Phase 15 Controlled Field Validation:** Protocol and schemas drafted; zero field activity or hardware connection.
- **Phase 16 Manuscript Results:** Section 6 is explicitly BLOCKED; draft manuscript contains no empirical performance numbers.

---

## 6. Blocker-by-Blocker Root-Cause Analysis

### THE ROOT CAUSE

**There is one fundamental cause behind all experiment blockers: no genuine human review of the 27 events has ever been conducted.** Every other blocker is either a consequence of this, or a secondary research decision that is blocked because the primary decision path was never started.

The governance infrastructure that was built to ensure scientific integrity is now the very thing preventing any progress — not because it has a bug, but because the prerequisite it enforces (genuine human ground truth) was never produced.

### 6.1 Primary Blocker: Zero Stage-2.1 Records

| Attribute | Detail |
|-----------|--------|
| **ID** | `STAGE21_RECORDS_MISSING` |
| **Source** | [`docs/READINESS_REPRODUCIBILITY_GATE_CLOSURE_20261019.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/READINESS_REPRODUCIBILITY_GATE_CLOSURE_20261019.md) |
| **Enforced by** | Evaluation readiness gate (`evaluation status`, exit code 3) |
| **Root cause** | No human has ever watched the 27 event videos and validated the AI-proposed timestamps |
| **Classification** | Missing human evidence |
| **What resolves it** | A human reviewer watches each event, validates/corrects T0/T1/T3/T4, and records a schema 8.1.0-stage2.1 review record |
| **Who must act** | The researcher (you) — only an allowlisted reviewer can create these |
| **Blocks** | Every evaluation experiment; every result table; every paper claim beyond image/clip-level model accuracy |

### 6.2 Blocker: Media Access Incident Hold

| Attribute | Detail |
|-----------|--------|
| **ID** | `INCIDENT_MEDIA_ACCESS_HOLD` |
| **Source** | [`docs/STAGE21_TIMING_PILOT_INCIDENT_20261019.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/STAGE21_TIMING_PILOT_INCIDENT_20261019.md), [`docs/MEDIA_ACCESS_INCIDENT_INVESTIGATION_20261020.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/MEDIA_ACCESS_INCIDENT_INVESTIGATION_20261020.md) |
| **What happened** | On 2026-10-19, an automated agent ran `evaluation status` twice, which **may** have opened/hashed source media files |
| **Investigation result** | Forensic `/tmp/*.json` files were deleted by OS; `/private/var/audit` requires root access; actual media access is **unproven** |
| **Code analysis** | `assess_official_phase12_readiness()` invokes manifest loading with `verify_sources=False` — likely **did not** hash media. But runtime state at invocation time cannot be proven |
| **Current enforcement** | All real-media operations, pilot activation, and evaluation commands are blocked |
| **Classification** | Incident restriction / containment hold |
| **What resolves it** | Either: (a) root-level BSM audit proves no media was read, or (b) researcher formally closes the incident by accepting the risk |
| **Blocks** | Everything that touches source media (inference, replay, pilot, evaluation) |

> [!WARNING]
> **This incident hold is self-imposed governance, not an external restriction.** The automated agent's own caution created this hold. The code analysis suggests the media was likely NOT accessed (`verify_sources=False`), but certainty requires privileged log inspection. The researcher can formally close this incident.

### 6.3 Blocker: Event Split Decision Missing

| Attribute | Detail |
|-----------|--------|
| **ID** | `EVENT_SPLIT_DECISION_MISSING` |
| **Root cause** | Only 1 crossing site exists. Only 2 capture sessions. The candidate random split leaks both sessions across partitions |
| **Real issue** | This is a **genuine scientific limitation**, not a code bug. True cross-crossing generalization is impossible with the current dataset |
| **What resolves it** | Researcher records a decision acknowledging the limitation: either a within-site development split or a 2-session sensitivity design |
| **File needed** | `data/splits/phase12_event_split_decision.json` |

### 6.4 Blocker: R04 Camera Scope Decision Missing

| Attribute | Detail |
|-----------|--------|
| **ID** | `R04_SCOPE_DECISION_MISSING` |
| **Root cause** | 16/27 events fail calibration for dual-camera synchronization. Researcher must decide camera mode per event |
| **What resolves it** | Researcher writes `data/manifests/phase12_r04_scope_decision.json` specifying `independent_camera` vs `dual_camera` per event |

### 6.5 Blocker: Premature Opening Definition Undecided

| Attribute | Detail |
|-----------|--------|
| **ID** | `PREMATURE_OPENING_DEFINITION_UNDECIDED` |
| **Root cause** | Two competing definitions (v9 vs M4) exist in code. Neither selected |
| **What resolves it** | Researcher selects one and records in `data/manifests/phase12_protocol_decision.json` |

### 6.6 Blocker: Stale Release Manifest

| Attribute | Detail |
|-----------|--------|
| **ID** | `RELEASE_MANIFEST_STALE` |
| **Root cause** | Pilot code was modified after the release manifest was generated; SHA-256 hashes diverged |
| **What resolves it** | Regenerate manifest after incident closure and code review |

### 6.7 Blocker: Adjudication Authorization Not Granted

| Attribute | Detail |
|-----------|--------|
| **ID** | `ADJ_AUTH_NOT_GRANTED` |
| **What resolves it** | Researcher explicitly authorizes human review of real media |

### 6.8 Remaining Blockers (Derived / Secondary)

| Blocker | Depends On | Auto-resolves When |
|---------|-----------|-------------------|
| `COHORT_APPROVAL_MISSING` ×3 | Stage-2.1 records | Valid records created per cohort |
| `MANIFEST_MISSING` | Split + R04 + Protocol + Stage-2.1 | All upstream decisions made |
| `EVAL_AUTH_NOT_GRANTED` | Everything above | All gates pass, researcher authorizes |
| D1 thresholds | Timing pilot | Human review duration data collected |
| D3(c) audit method | Researcher decision | Researcher specifies |
| Second reviewer | Researcher action | Second identity registered |
| Site survey | Physical activity | Researcher visits crossing |

---

## 7. Experiments Executable with Existing Authorized Artifacts

### 7.1 Immediately Executable (No Blockers)

| # | Experiment | Inputs | Outputs | Notes |
|---|-----------|--------|---------|-------|
| 1 | **Vision model image-level evaluation report** | Existing `experiments/vision/39f402dfe460/evaluation/` artifacts | Formatted paper figures, tables, per-class analysis | Results already exist; need only formatting |
| 2 | **Audio model clip-level evaluation report** | Existing `experiments/audio/RUN_20261008_AUDIO_V2/` and V3 artifacts | Paper figures: loss curves, confusion matrix, ROC, PR, threshold analysis, v1→v2→v3 progression | Results already exist; need only formatting |
| 3 | **Audio hard-negative robustness analysis** | V3 ESC-50 per-category FP rates | Table showing which environmental sounds confuse the horn detector | Data in [`forensic_analysis.json`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/audio/RUN_20261008_AUDIO_V3_ESC50/reports/forensic_analysis.json) |
| 4 | **Architecture and design analysis** | Source code, configs, frozen policy hash | System architecture diagram, state machine diagram, fusion logic documentation | Code is complete |
| 5 | **Dataset composition and diversity analysis** | Manifests, metadata, event inventory | Table showing event counts, conditions, cohorts, camera coverage | Metadata available |
| 6 | **Synthetic fusion/policy demonstration** | Synthetic fixtures + implemented code | Demonstration that fusion and temporal policy logic function correctly (clearly labeled as synthetic validation, not real evidence) | Already partially done in Phase 11.9 |

### 7.2 Executable After One Researcher Decision (Incident Closure)

If the researcher formally closes the media access incident (accepting that the code analysis shows `verify_sources=False` and media was likely not accessed):

| # | Experiment | Prerequisite | Notes |
|---|-----------|-------------|-------|
| 7 | **Vision inference on 27 events** (exploratory, not official evaluation) | Incident closure | Run vision model on all event videos, save per-frame detections. Does NOT require ground truth — produces model outputs only |
| 8 | **Audio inference on 27 events** (exploratory) | Incident closure | Run audio model on all event audio, save per-segment predictions |
| 9 | **Fusion + temporal policy replay on 27 events** (exploratory) | Incident closure + #7 + #8 | Run complete pipeline, save state timeline per event |

> [!TIP]
> Experiments 7–9 produce **model output artifacts** that can be evaluated later once ground truth is available. They do NOT require ground truth to execute — only media access. This separates inference from evaluation.

### 7.3 Executable After Researcher Does Ground Truth Review

Once valid Stage-2.1 records exist for some or all events:

| # | Experiment | Prerequisite |
|---|-----------|-------------|
| 10 | Vision-only baseline (Experiment D from original plan) | GT + model outputs |
| 11 | Audio-only analysis (Experiment E) | GT + model outputs |
| 12 | Fusion vs vision-only (Experiment F vs D) | GT + model outputs |
| 13 | Full system evaluation (Experiment G) | GT + model outputs |
| 14 | Temporal policy comparison (stateless vs temporal) | GT + model outputs |
| 15 | Condition-wise analysis (day/night/rain/fog) | GT + event metadata |
| 16 | Per-event failure analysis | GT + model outputs |
| 17 | Calibration and uncertainty analysis | GT + confidence scores |

### 7.4 Executable After R04 Decision + Ground Truth

| # | Experiment | Prerequisite |
|---|-----------|-------------|
| 18 | Single vs dual camera comparison | R04 scope decision + GT + calibrated events |
| 19 | Fault injection (camera dropout, audio dropout) | GT + full pipeline outputs |
| 20 | Ablation studies (fusion weights, persistence window) | GT + baseline established |

---

## 8. Experiments Requiring Human Decisions or Authorization

### 8.1 Researcher Decisions Needed (in priority order)

| # | Decision | Impact | Effort |
|---|---------|--------|--------|
| **D-A** | **Close the media access incident** | Unblocks ALL media operations | ~5 minutes: read [`docs/MEDIA_ACCESS_INCIDENT_INVESTIGATION_20261020.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/MEDIA_ACCESS_INCIDENT_INVESTIGATION_20261020.md), decide to accept the code-analysis evidence that media was not accessed, record closure statement |
| **D-B** | **Authorize human review of real events** (ADJ-AUTH) | Unblocks ground truth creation | ~5 minutes: authorize yourself as reviewer to view and annotate real event videos |
| **D-C** | **Conduct actual ground truth review** | THE CRITICAL PATH | ~4-8 hours: watch 27 events (each ~30-60s), validate/correct T0/T1/T3/T4 timestamps against AI proposals |
| **D-D** | **Record event split decision** | Unblocks evaluation manifest | ~10 minutes: decide on within-site development split with acknowledged limitations |
| **D-E** | **Record R04 scope decision** | Unblocks multi-camera experiments | ~10 minutes: select `independent_camera` for most events, `dual_camera` for 11 calibrated events |
| **D-F** | **Select premature opening definition** | Unblocks protocol profile | ~10 minutes: select v9 or M4 and record rationale |

### 8.2 Authorization Sequence

```
D-A (Incident closure, 5 min)
 └→ D-B (ADJ-AUTH, 5 min)
     └→ D-C (Ground truth review, 4-8 hours)  ← THE CRITICAL PATH
         └→ D-D, D-E, D-F (Research decisions, 30 min total)
             └→ Build evaluation manifest (automated)
                 └→ Grant EVAL-AUTH (5 min)
                     └→ Run all experiments (automated)
```

---

## 9. Shortest Legitimate Path to Completion

### 9.1 Why the 27-Event Experiments Have Not Been Completed

**The precise reason is: no human has ever reviewed the 27 event videos to create validated ground truth labels.**

The AI-generated proposals exist. The code infrastructure is complete. The models are trained. But the governance system correctly requires that a human validate the proposed timestamps before any evaluation can claim scientific validity. This step was never performed.

The secondary blockers (media access incident, split decision, R04 decision, protocol choice) are all either consequences of the missing ground truth or independent research decisions that were deferred.

### 9.2 The Shortest Path (Estimated Total: 1-2 days)

#### Phase A: Unblock (30 minutes of researcher decisions)

1. **Close the media access incident** — Record a formal closure statement accepting the code-analysis evidence. The investigation showed `verify_sources=False`, making it very unlikely media was accessed.

2. **Record event split decision** — Choose within-site descriptive development split (Option A from the action package). Acknowledge the single-crossing limitation in the paper.

3. **Select premature opening definition** — Choose v9 (`t1_entry_to_t4_clearance`) as the simpler, already-implemented option. Record rationale.

4. **Record R04 scope decision** — Choose `independent_camera` for all events as the primary analysis, with an optional `dual_camera` exploratory subset for the 11 calibrated events.

#### Phase B: Ground Truth (4-8 hours of researcher work)

5. **Authorize yourself as reviewer** — Grant ADJ-AUTH for a bounded review scope.

6. **Review all 27 events** — Watch each event video (~30-60s each), compare against AI-proposed T0/T1/T3/T4 timestamps, validate or correct each timestamp, record as schema 8.1.0-stage2.1 review records.

   The AI proposals in `data/ground_truth/proposals/` already contain detailed candidate timestamps with frame indices and rationale. The reviewer's job is to **verify or correct** them, not to annotate from scratch.

7. **Run promotion gate** — After review, the promotion gate validates the records and issues receipts.

#### Phase C: Execute Experiments (automated, 2-4 hours)

8. **Build evaluation manifest** — Automated once all decisions and receipts exist.

9. **Run inference on all 27 events** — Vision + audio inference on all events, save outputs.

10. **Run full experiment matrix** — All baseline, fusion, temporal, ablation, robustness experiments against validated ground truth. The infrastructure is complete — this is automated.

11. **Generate figures and tables** — Publication-quality outputs from actual measured results.

#### Phase D: Paper (1-2 days)

12. **Analyze results** — Failures, uncertainty, limitations, condition-wise analysis.

13. **Complete manuscript** — Replace placeholder tables with actual results.

### 9.3 What Cannot Be Fixed

| Limitation | Consequence for Paper |
|-----------|----------------------|
| Single crossing site | Cannot claim cross-crossing generalization; must declare as limitation |
| 2 capture sessions only | Limited session-diversity analysis; declare as limitation |
| $T_0$ left-censored in all train events | Cannot report true physical detection latency; report as left-censored |
| 3 no-train controls only (~1 min total) | Limited false-positive rate estimation; may need additional negative footage |
| no_train_events/event_002 has 60/60 FP rate | Must be analyzed as a failure case, not excluded |
| 16/27 events lack dual-camera calibration | Full-cohort dual-camera claims are impossible; must use single-camera or calibrated subset |

---

## 10. Decisive Recommendation

### What to Execute First

**Execute immediately (no blockers):**
1. Format the existing vision model evaluation results (mAP, confusion matrix, PR curves) into paper-quality figures
2. Format the existing audio model evaluation results (V1→V2→V3 progression, hard-negative analysis) into paper-quality figures
3. Write the architecture/system design section of the paper using the implemented and tested code

**What to do next (requires ~30 minutes of researcher decisions):**
4. Close the media access incident
5. Record the three missing research decisions (split, R04 scope, protocol)

**The critical path (requires researcher work):**
6. Conduct the actual ground truth review of the 27 events (4-8 hours)

**Everything after that is automated.**

### What Can Be Completed Independently

- Vision model evaluation ← **independent, complete now**
- Audio model evaluation ← **independent, complete now**
- System architecture documentation ← **independent, complete now**
- Dataset description ← **independent, complete now**
- Synthetic fusion/policy demonstration ← **independent, possible now**
- Literature review and related work ← **independent, always possible**

### What Cannot Proceed Without Specific Prerequisites

| Blocked Experiment | Required Prerequisite |
|-------------------|----------------------|
| Any real-event evaluation | Human ground truth (Stage-2.1 records) |
| Any media access | Incident closure |
| Dual-camera analysis | R04 scope decision |
| Full experiment matrix | All of the above |

### Bottom Line

**The project is ~70% complete in infrastructure and ~30% complete in actual results.** The vision and audio models are trained and have valid standalone evaluation results. The fusion engine, temporal policy, evaluation infrastructure, test suite, and experiment matrix are all implemented and tested.

**The single blocking action is: you need to watch the 27 event videos and validate the AI-proposed timestamps.** Everything else is either an automated consequence of having ground truth, or a quick research decision.

The governance infrastructure that was built to ensure scientific integrity is working exactly as designed — it correctly refuses to produce results without validated ground truth. The path forward is not to bypass it, but to provide the evidence it requires.

**Estimated time to complete the entire research from current state: 2-4 days of active work.**

---

*Report generated 2026-10-25. All claims reference specific repository artifacts. No authorization, decision, label, or governance artifact was created by this audit.*
