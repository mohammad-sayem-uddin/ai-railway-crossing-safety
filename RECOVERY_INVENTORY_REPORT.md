# Recovery Inventory Report
## Railway Crossing Vision-Audio Fusion Safety System

**Report Date:** 2026-10-13  
**Auditor Role:** Senior ML Research Scientist, Computer-Vision Engineer, Forensic Recovery Specialist  
**Recovery Repository Path:** `/Users/sayemuddin/Projects/Train_automation`  
**Discovered Local Archive Path:** `/Users/sayemuddin/iCloud Drive (Archive)/Desktop/Train_automation`  
**Remote Source:** `https://github.com/mohammad-sayem-uddin/ai-railway-crossing-safety.git`  
**Status:** COMPLETE FORENSIC INVENTORY — NO LOSS OF CERTIFIED ASSETS  

---

## 7.1 Executive Summary

Following an iCloud sync operation that removed `/Users/sayemuddin/Desktop/Train_automation`, an urgent forensic recovery audit was executed across GitHub and local storage.

### Key Audit Findings:

1. **GitHub Status:**
   - The remote repository at `https://github.com/mohammad-sayem-uddin/ai-railway-crossing-safety.git` was successfully cloned into `/Users/sayemuddin/Projects/Train_automation` (HEAD commit `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` on branch `main`).
   - GitHub tracked 223 core files (foundational source code, documentation, figure generators, configs, and unit tests).
   - **Crucially, GitHub NEVER tracked large binary assets.** The repository's `.gitignore` explicitly excluded `*.pt`, `data/raw/layer_b/`, `data/raw/audio/`, `data/raw/vision/`, `ESC-50-master/`, and `scratch/`. Git LFS was never configured (0 LFS objects), and no GitHub Releases or tags exist.
   - Consequently, GitHub alone restores code up to Phase 0 / early Phase 2 documentation consolidation, but contains **zero trained weights, zero raw videos, and zero ground-truth proposals**.

2. **Discovery of Local Recovery Source:**
   - Forensic disk inspection revealed that the local project was **not wiped out**.
   - During the macOS iCloud Drive sync modification, macOS archived the entire Desktop directory into:
     `/Users/sayemuddin/iCloud Drive (Archive)/Desktop/Train_automation` (6.5 GB).
   - A secondary iCloud shadow directory also exists at:
     `/Users/sayemuddin/Library/Mobile Documents/com~apple~CloudDocs/Desktop/Train_automation`.
   - The `iCloud Drive (Archive)` directory is **100% physically intact** and was modified as recently as today (`Oct 13 04:04`).

3. **Model Checkpoint Recovery Verdict:**
   - **Vision Checkpoint:** `PRESENT_AND_VERIFIED`. The exact checkpoint at `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` exists in the local archive. File size is exactly `24,493,159 bytes`, and SHA-256 matches `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` bit-for-bit.
   - **Audio V3 Checkpoint:** `PRESENT_AND_VERIFIED`. The exact checkpoint at `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt` exists in the local archive. File size is exactly `329,497 bytes`, and SHA-256 matches `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782` bit-for-bit.
   - **Prohibited Audio V2:** Identified at `models/audio/best_checkpoint.pt` (SHA-256: `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5`). It is confirmed present but flagged as strictly quarantined.
   - **Neither model needs retraining.** Both frozen, certified checkpoints are fully recovered.

4. **Dataset Completeness Verdict:**
   - **Real Crossing Videos:** 56 video files (3.6 GB) across all 27 active events (23 train + 3 no-train + 1 engine-only = 54 streams) plus the 1 historical duplicate event (2 streams) are 100% intact, readable, and verified via `ffprobe`.
   - **ESC-50 Dataset:** 2,000 audio files + metadata CSV (846 MB) are 100% intact.
   - **Train Horn Audio Dataset:** 276 WAV files (91 positive, 185 negative, 66 MB) are 100% intact.
   - **Vision Training Dataset:** 3,157 images across train/valid/test are intact. All 3,267 bounding-box annotations are 100% preserved in `results/dataset_validation/dataset_manifest.jsonl` (tracked in Git) and Roboflow metadata.

5. **Ground Truth & Research Code Verdict:**
   - All 27 candidate review sheets and proposal versions (v1–v6), review JSONs, and verification reports are intact in `data/ground_truth/`.
   - All subsequent Python modules (fusion collector, decision engine, state machine, layer B processor, test suites) developed locally after commit `d4db94d` survive in the archive.

6. **Overall Readiness:**
   - The project is fully recoverable without loss of research work or data.
   - Immediate migration from the fragile iCloud directory to the clean, non-synced `~/Projects/Train_automation` repository is required.

---

## 7.2 Asset Inventory

| Asset Group / File | Expected Location | Actual Status | Count / Size | Hash Verified? | Recoverable Source | Required Action |
|---|---|---|---|---|---|---|
| **Git Foundation Code** | Root / `src/` / `tests/` | `PRESENT_AND_VERIFIED` | 223 files / 74 MB | Verified (Git HEAD `d4db94d`) | GitHub Remote | Base checkout in `~/Projects/Train_automation` |
| **Vision Model Checkpoint** | `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` | `PRESENT_AND_VERIFIED` | 1 file / 24,493,159 bytes | **YES** (`3f5bb5b2...`) | Local iCloud Archive | Copy to `~/Projects/Train_automation` |
| **Audio V3 Checkpoint** | `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt` | `PRESENT_AND_VERIFIED` | 1 file / 329,497 bytes | **YES** (`ea1bb81d...`) | Local iCloud Archive | Copy to `~/Projects/Train_automation` |
| **Prohibited Audio V2** | `models/audio/best_checkpoint.pt` | `PRESENT_AND_VERIFIED` | 1 file / 334,839 bytes | **YES** (`59b0785f...`) | Local iCloud Archive | Quarantine; do not use |
| **YOLOv8n Base Pretrained** | `yolov8n.pt` | `PRESENT_AND_VERIFIED` | 1 file / 6,549,796 bytes | Verified | Local iCloud Archive | Copy to project root |
| **Active Crossing Videos (V2)** | `data/raw/layer_b/v2/` | `PRESENT_AND_VERIFIED` | 54 streams (27 events) + 2 dupe / 3.6 GB | Verified via `ffprobe` | Local iCloud Archive | Copy to `~/Projects/Train_automation` |
| **Historical Duplicate Video** | `data/raw/layer_b/v2/engine_events/event_historical_duplicate_010/` | `PRESENT_AND_VERIFIED` | 2 streams (1 event) | Verified | Local iCloud Archive | Keep quarantined from active cohort |
| **Train Horn Audio Dataset** | `data/raw/audio/train_horn/` | `PRESENT_AND_VERIFIED` | 276 files (91 pos, 185 neg) / 66 MB | Verified | Local iCloud Archive | Copy to `~/Projects/Train_automation` |
| **ESC-50 Dataset** | `ESC-50-master/` | `PRESENT_AND_VERIFIED` | 2,000 WAV + meta / 846 MB | Verified | Local iCloud Archive | Copy to `~/Projects/Train_automation` |
| **Vision Dataset Images** | `data/raw/vision/v1/baler.v1i.yolov8/` | `PRESENT_AND_VERIFIED` | 3,157 JPG images / ~250 MB | Verified | Local iCloud Archive | Copy to `~/Projects/Train_automation` |
| **Vision Annotations/Labels** | `results/dataset_validation/dataset_manifest.jsonl` | `PRESENT_AND_VERIFIED` | 3,157 JSONL entries (3,267 boxes) | Verified in Git | GitHub Remote & Local | Native tracking in Git |
| **Vision Split Definitions** | `data/splits/705d388743ea/` | `PRESENT_AND_VERIFIED` | 5 files (`train`, `val`, `test.jsonl`) | Verified | Local iCloud Archive | Copy to `~/Projects/Train_automation` |
| **Ground Truth Proposals** | `data/ground_truth/proposals/` | `PRESENT_AND_VERIFIED` | 27 review sheets + v1–v6 proposals | Verified | Local iCloud Archive | Copy to `~/Projects/Train_automation` |
| **Ground Truth Reviews** | `data/ground_truth/reviews/` | `PRESENT_AND_VERIFIED` | 27 review JSONs + verification report | Verified | Local iCloud Archive | Copy to `~/Projects/Train_automation` |
| **Advanced Fusion Modules** | `src/railway_detection/fusion/` | `PRESENT_AND_VERIFIED` | 3 files (`collector`, `decision_engine`, `source_tracker`) | Verified | Local iCloud Archive | Integrate into `~/Projects` |
| **Simulation Modules** | `src/railway_detection/simulation/` | `PRESENT_AND_VERIFIED` | 4 files (`gate_model`, `state_machine`, `failure_injector`, `runner`) | Verified | Local iCloud Archive | Integrate into `~/Projects` |
| **Experiment Runner & Stats** | `src/railway_detection/experiments/` | `PRESENT_AND_VERIFIED` | 6 files (`runner`, `layer_b_processor`, `leakage_guard`, etc.) | Verified | Local iCloud Archive | Integrate into `~/Projects` |
| **Audio Architecture Modules** | `src/railway_detection/audio/` | `PRESENT_AND_VERIFIED` | 7 files (`model`, `pipeline`, `dataset`, `classifier_hierarchy`, etc.) | Verified | Local iCloud Archive | Integrate into `~/Projects` |
| **Evaluation Metrics Module** | `src/railway_detection/evaluation/` | `PRESENT_AND_VERIFIED` | 1 file (`metrics.py`) | Verified | Local iCloud Archive | Integrate into `~/Projects` |
| **Execution Scripts** | `scripts/` | `PRESENT_AND_VERIFIED` | 20 scripts (runners, audio trainers, figure generators) | Verified | Local iCloud Archive | Integrate into `~/Projects` |
| **Expanded Test Suite** | `tests/` | `PRESENT_AND_VERIFIED` | 19 test files (unit, integration, fault injection) | Verified | Local iCloud Archive | Integrate into `~/Projects` |
| **Canonical Test Results** | `results/testing/` | `PRESENT_AND_VERIFIED` | `FINAL_TEST_RESULTS.md` & `canonical_test_results.json` | Verified | Local iCloud Archive | Copy to `~/Projects/Train_automation` |
| **Methodology Documentation** | `docs/` | `PRESENT_AND_VERIFIED` | 10 protocol docs + `archive/` + `INDEPENDENT_RESEARCH_DESIGN_AUDIT.md` | Verified | Local iCloud Archive | Synchronize to `~/Projects` |
| **Python Virtual Environment** | `.venv/` | `PRESENT_AND_VERIFIED` | Python 3.14.4 virtualenv | Verified | Local iCloud Archive | Recreate or copy to `~/Projects` |

---

## 7.3 Dataset Completeness Matrix

| Dataset Category | Expected Location | Actual Location in Archive | Expected Count | Actual Count | Size | Manifest / Split Intact? | Reconstruction Possible? | New Labeling Needed? |
|---|---|---|---|---|---|---|---|---|
| **Layer B V2 Real Videos** | `data/raw/layer_b/v2/` | `data/raw/layer_b/v2/` | 27 events (54 streams) | 27 events (54 streams) + 1 dupe (2 streams) | 3.6 GB | YES (`real_world_v2_video_manifest.jsonl`) | Not needed; originals present | **NO** |
| **ESC-50 Environmental Audio** | `ESC-50-master/` | `ESC-50-master/` | 2,000 WAV | 2,000 WAV | 846 MB | YES (`meta/esc50.csv`, `audio_v3_esc50_manifest.jsonl`) | Complete standard dataset | **NO** |
| **Train Horn Field Audio** | `data/raw/audio/train_horn/` | `data/raw/audio/train_horn/` | Positive + Negative | 91 positive, 185 negative WAV | 66 MB | YES (`train_horn_audio_manifest.jsonl`) | Complete audio dataset | **NO** |
| **Vision Roboflow v1 Images** | `data/raw/vision/v1/baler.v1i.yolov8/` | `data/raw/vision/v1/baler.v1i.yolov8/` | 3,157 images | 2,763 train, 263 val, 131 test (3,157 total) | ~250 MB | YES (`vision_v1_metadata.json`, `split_summary.json`) | Complete images present | **NO** |
| **Vision Annotations (Bboxes)** | `data/raw/vision/v1/baler.v1i.yolov8/*/labels/` | In Git: `results/dataset_validation/dataset_manifest.jsonl` | 3,157 files | 3,157 labeled records (3,267 bboxes) | 1.8 MB | YES (all normalized bboxes stored per image) | Fully recoverable from manifest or Roboflow | **NO** |
| **Ground Truth Candidate Annotations** | `data/ground_truth/proposals/` | `data/ground_truth/proposals/` | 27 event review sheets | 27 review sheets + v1–v6 proposal JSONs | ~500 KB | YES (`ANNOTATION_BATCH_REVIEW_INDEX.md`) | All historical versions preserved | **NO** (Pending sign-off) |

---

## 7.4 Model Recovery Verdict

### 1. Vision Model Checkpoint
- **Expected Path:** `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`
- **Expected SHA-256:** `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`
- **Expected Size:** `24,493,159 bytes`
- **Actual Status in Archive:** Present at exact relative path.
- **Computed SHA-256:** `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` (**EXACT MATCH**)
- **Computed Size:** `24,493,159 bytes` (**EXACT MATCH**)
- **Training Config:** `experiments/vision/39f402dfe460/checkpoints/args.yaml` and `configs/vision.yaml` are present.
- **Verdict:** **RESTORE ORIGINAL CHECKPOINT — NO RETRAINING REQUIRED.**

### 2. Audio V3 Model Checkpoint
- **Expected Path:** `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`
- **Expected SHA-256:** `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`
- **Expected Size:** `329,497 bytes`
- **Operating Threshold:** `0.3700`
- **Actual Status in Archive:** Present at exact relative path.
- **Computed SHA-256:** `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782` (**EXACT MATCH**)
- **Computed Size:** `329,497 bytes` (**EXACT MATCH**)
- **Training Script & Report:** `scripts/train_audio_model_v3_esc50.py` and `docs/AUDIO_MODEL_V3_ESC50_REPORT.md` are present.
- **Verdict:** **RESTORE ORIGINAL CHECKPOINT — NO RETRAINING REQUIRED.**

### 3. Audio V2 Model Checkpoint (Prohibited)
- **Expected Path:** `models/audio/best_checkpoint.pt`
- **Known Prohibited SHA-256:** `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5`
- **Actual Status in Archive:** Present at `models/audio/best_checkpoint.pt` (334,839 bytes, SHA-256 `59b0785f...`).
- **Verdict:** **STRICTLY PROHIBITED FROM RESEARCH REUSE.** Kept solely as a negative-test artifact; Audio V3 is the sole valid checkpoint.

---

## 7.5 Research Recovery Checklist

### Priority 0 — Immediate Protection & Safe Migration
- [x] Create non-synced workspace: `/Users/sayemuddin/Projects/Train_automation`.
- [x] Clone remote GitHub repository to establish clean Git baseline.
- [ ] Safely copy uncommitted assets from `/Users/sayemuddin/iCloud Drive (Archive)/Desktop/Train_automation` into `/Users/sayemuddin/Projects/Train_automation`.
- [ ] Leave `/Users/sayemuddin/iCloud Drive (Archive)/` completely intact as an immutable read-only backup.
- [ ] Verify disk space remains healthy (>12 GB available).

### Priority 1 — Data & Asset Restoration
- [ ] Copy `data/raw/layer_b/v2/` (all 27 active event folders + historical duplicate folder).
- [ ] Copy `ESC-50-master/` and `data/raw/audio/train_horn/`.
- [ ] Copy `data/raw/vision/v1/baler.v1i.yolov8/`.
- [ ] Copy `data/splits/` and `data/manifests/`.
- [ ] Copy `data/ground_truth/proposals/` and `data/ground_truth/reviews/`.
- [ ] Verify SHA-256 hashes of copied media/datasets.

### Priority 2 — Model Weights Restoration
- [ ] Copy `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`.
- [ ] Copy `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`.
- [ ] Copy `yolov8n.pt`.
- [ ] Re-run cryptographic verification to certify target files match expected SHA-256.

### Priority 3 — Fusion Pipeline & Code Integration
- [ ] Copy missing `src/railway_detection/` submodules (`fusion/`, `simulation/`, `experiments/`, `annotation/`, updated `audio/`, `evaluation/`).
- [ ] Copy all 20 scripts in `scripts/`.
- [ ] Copy all test suites in `tests/`.
- [ ] Reconcile CF-02: Fix `LAYER_B_VIDEOS_DIR` in `scripts/run_real_world_experiments.py` to point to `data/raw/layer_b/v2/`.
- [ ] Reconcile CF-04: Align audio threshold defaults in `layer_b_processor.py` to canonical `0.3700`.
- [ ] Reconcile PA-02: Verify YOLO model class mappings (`front`, `rear`, `side`).

### Priority 4 — Ground Truth Verification & Researcher Approval
- [ ] Researcher inspects the 27 candidate review sheets in `data/ground_truth/proposals/`.
- [ ] Perform acoustic verification on the 10 horn-present events.
- [ ] Formally sign off and freeze Stage 3 Ground Truth manifest.

### Priority 5 — Full-Dataset Inference & Evaluation
- [ ] Run full baseline inference (E7/B4) across all 27 active events (54 streams).
- [ ] Generate per-frame prediction logs (`.jsonl`).
- [ ] Compute official evaluation metrics (MTR, POR, Warning Lead Time).
- [ ] Run ablation sweep across active conditions.

---

## 7.6 Missing Information and Honest Limitations

1. **GitHub Remote Limitations:**
   - GitHub contains only code up to commit `d4db94d` (Mon Oct 12 07:47:55 2026).
   - Remote GitHub does NOT contain Git LFS objects, releases, tags, model weights, raw videos, or ground-truth proposals.
   - Any recovery strictly dependent on GitHub alone would have required re-downloading videos and re-annotating.

2. **Local macOS iCloud Architecture:**
   - The original directory `/Users/sayemuddin/Desktop/Train_automation` ceased to exist because macOS iCloud Desktop & Documents sync moved/archived it to `/Users/sayemuddin/iCloud Drive (Archive)/Desktop/Train_automation`.
   - Direct Git commands in `~/Library/Mobile Documents/` hang due to iCloud daemon file-coordination locks.
   - Therefore, working directly inside Desktop or Mobile Documents is unsafe and causes data instability. All future work MUST occur in `~/Projects/Train_automation`.

3. **Ground Truth Status:**
   - All 27 event review sheets and candidate proposals are recovered. However, they remain **candidate proposals**, NOT final approved ground truth. Human review and sign-off remain required before evaluation.
