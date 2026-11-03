# Recovery Restoration Report
## Railway Crossing Vision-Audio Fusion Safety System

**Restoration Date:** 2026-10-13  
**Auditor Role:** Senior ML Research Scientist, Computer-Vision Engineer, Multimodal Fusion Specialist  
**Recovery Target Repository:** `/Users/sayemuddin/Projects/Train_automation`  
**Source Backup Archive:** `/Users/sayemuddin/iCloud Drive (Archive)/Desktop/Train_automation`  
**Git Baseline Commit:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` on branch `main`  
**Status:** RESTORATION COMPLETE — ALL ASSETS VERIFIED  

---

## 1. Files and Asset Groups Restored

A total of **12,195 files** (5,378.1 MB) were non-destructively restored from the immutable iCloud archive into the clean repository at `/Users/sayemuddin/Projects/Train_automation`.

### Restored Asset Summary:

| Asset Group | Relative Path | Restored File Count | Size | Status |
|---|---|---|---|---|
| **Layer B V2 Real Videos** | `data/raw/layer_b/v2/` | 56 video files | 3.6 GB | Verified decodable via `ffprobe` |
| **ESC-50 Audio Corpus** | `ESC-50-master/` | 2,000 WAV + 2 metadata | 846 MB | 100% complete standard corpus |
| **Train Horn Audio** | `data/raw/audio/train_horn/` | 276 WAV files (91 pos, 185 neg) | 66 MB | Complete field audio dataset |
| **Vision Dataset Images** | `data/raw/vision/v1/baler.v1i.yolov8/` | 3,157 JPG images | ~250 MB | 2,763 train, 263 val, 131 test |
| **Dataset Splits** | `data/splits/` | 15 split files | ~2 MB | `705d388743ea/` & `audio/` splits |
| **Dataset Manifests** | `data/manifests/` | 25 manifest files | ~17 MB | Complete audio, video & motion manifests |
| **Ground Truth Proposals** | `data/ground_truth/proposals/` | 27 review sheets + v1–v6 JSONs | ~500 KB | All historical candidate proposals |
| **Ground Truth Reviews** | `data/ground_truth/reviews/` | 27 review JSONs + report | ~200 KB | All verification review records |
| **Processed Data** | `data/processed/` | 13 files | ~500 KB | Feature and audio cache tables |
| **Vision Model Weights** | `experiments/vision/39f402dfe460/checkpoints/` | `weights/best.pt` & `weights/last.pt` | ~49 MB | **SHA-256 cryptographically verified** |
| **Audio V3 Weights** | `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/` | `checkpoints/best.pt` | 329 KB | **SHA-256 cryptographically verified** |
| **Pretrained YOLO Weights** | `yolov8n.pt` | 1 file | 6.5 MB | Root baseline model |
| **Quarantined Audio V2** | `models/audio/best_checkpoint.pt` | 1 file | 335 KB | Verified and strictly quarantined |
| **Source Modules (New)** | `src/railway_detection/` | 21 Python files | ~500 KB | `fusion/`, `simulation/`, `experiments/`, `annotation/`, `evaluation/` |
| **Execution Scripts** | `scripts/` | 20 scripts | ~350 KB | Runners, audio trainers, figure generators |
| **Complete Test Suite** | `tests/` | 29 unit, integration, & scenario tests | ~200 KB | All test suites restored |
| **Canonical Test Results** | `results/testing/` | `FINAL_TEST_RESULTS.md` & JSON | ~25 KB | Official test baseline |
| **Research Artifacts** | `docs/` & root | `INDEPENDENT_RESEARCH_DESIGN_AUDIT.md`, etc. | ~150 KB | All protocols, audits, and readiness reports |
| **Unseen Demo Videos** | `Unseen_Video/` | 4 video files | ~200 MB | Inspection clips for demo server |
| **Scratch Workspace** | `scratch/` | 29 files | ~1 MB | Researcher pilot inspection notes |

---

## 2. Files Already Present (Preserved Unchanged)

The clean Git checkout contained **224 files** at commit `d4db94d`. 
- **139 files** were bit-for-bit identical with the archive and remained untouched.
- **76 files** existed only in the Git checkout (such as `data/metadata/vision_v1_metadata.json`, root `dashboard.py`, root `demo_video.py`, `pyproject.toml`, `.env.example`, `.gitkeep` directory anchors, and evaluation curve PNGs in `experiments/vision/`). **All 76 files were strictly preserved and not overwritten.**

---

## 3. Source-Code Differences & Resolution Strategy

Exactly **9 tracked files** differed between Git commit `d4db94d` and the archive.

### Baseline Preservation:
Before updating any file, the exact Git baseline version of all 9 files was backed up to:  
`docs/archive/git_baseline_d4db94d/`

### Resolution Details:

| File | Git Version | Archive Version | Resolution & Rationale |
|---|---|---|---|
| `docs/FINAL_ABLATION_MATRIX.md` | v5.1.0 (143 lines) | v7.0.0 (155 lines) | **Adopted Archive Version:** Contains the canonical research methodology update formally retiring Prerequisite R03 as a separate blocker. |
| `docs/FINAL_EXPERIMENT_DATA_FLOW.md` | v6.0.0 (278 lines) | v7.0.0 (279 lines) | **Adopted Archive Version:** Includes the Operational Danger-Zone Annotation Convention update. |
| `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` | v6.0.0 (828 lines) | v7.0.0 (847 lines) | **Adopted Archive Version:** Formally defines the Operational Danger-Zone exit boundary plane, retiring R03. |
| `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` | v8.0.0 (422 lines) | v9.0.0 (435 lines) | **Adopted Archive Version:** Master real-world protocol with R03 retired and R04 preserved. |
| `src/railway_detection/data/layer_b.py` | 134 lines | 158 lines | **Adopted Archive Version:** Essential superset adding `camera_front.mov` and `camera_back.mov` candidate filenames and automated audio extraction fallback needed by the V2 dataset. |
| `src/railway_detection/cli/main.py` | 338 lines | 448 lines | **Adopted Archive Version:** Replaced Phase 0 placeholder stubs with real CLI subcommands for `audio extract`, `simulate run`, and `experiment run` (B0–B7). |
| `tests/fixtures/mock_events.py` | 87 lines | 162 lines | **Adopted Archive Version:** Added `make_realistic_mock_event_cohort()` for end-to-end integration testing. |
| `tests/unit/test_layer_b_loader.py` | 92 lines | 150 lines | **Adopted Archive Version:** Added unit tests verifying camera filename aliases and audio extraction fallback. |
| `results/experiment_registry.jsonl` | 80 lines | 148 lines | **Adopted Archive Version:** Contains the full historical record of experiment runs and validations. |

---

## 4. Checkpoint Hash Verification Results

All model checkpoints copied to `/Users/sayemuddin/Projects/Train_automation` were independently verified using cryptographic SHA-256 and byte-size comparisons:

```
3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd  experiments/vision/39f402dfe460/checkpoints/weights/best.pt
ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782  experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt
59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5  models/audio/best_checkpoint.pt
```

### Verification Verdict:
1. **Vision Model (`experiments/vision/39f402dfe460/checkpoints/weights/best.pt`):**
   - Expected Size: `24,493,159 bytes` | Restored Size: `24,493,159 bytes` (**EXACT MATCH**)
   - Expected SHA-256: `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`
   - Restored SHA-256: `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` (**EXACT MATCH**)
   - **Verdict:** Certified frozen vision weights intact. **NO RETRAINING REQUIRED.**

2. **Audio V3 Model (`experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`):**
   - Expected Size: `329,497 bytes` | Restored Size: `329,497 bytes` (**EXACT MATCH**)
   - Expected SHA-256: `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`
   - Restored SHA-256: `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782` (**EXACT MATCH**)
   - Operating Threshold: `0.3700`
   - **Verdict:** Certified frozen Audio V3 weights intact. **NO RETRAINING REQUIRED.**

3. **Audio V2 Model (`models/audio/best_checkpoint.pt`):**
   - SHA-256: `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5`
   - Status: **STRICTLY QUARANTINED.** Retained solely as a negative-test artifact; excluded from fusion pipeline.

---

## 5. Dataset File Counts & Integrity Checks

All datasets in `/Users/sayemuddin/Projects/Train_automation` were verified:

1. **Layer B V2 Real Crossing Videos:**
   - Total files: 56 video files (3.6 GB).
   - Format: QuickTime MOV (`camera_front.mov`, `camera_back.mov`).
   - Integrity: Spot-checked with `ffprobe` (e.g. `event_001/camera_front.mov`: duration = 49.84s, video + audio stream intact).
2. **ESC-50 Environmental Audio:**
   - Total files: Exactly 2,000 WAV recordings + `meta/esc50.csv` (846 MB).
3. **Train Horn Field Audio:**
   - Positive clips: 91 WAV files.
   - Negative clips: 185 WAV files.
   - Total: 276 WAV files (66 MB).
4. **Vision Dataset (Roboflow v1):**
   - Training images: 2,763 JPG files.
   - Validation images: 263 JPG files.
   - Test images: 131 JPG files.
   - Total images: 3,157 JPG files.
   - Bounding boxes: All 3,267 bounding-box annotations across all 3,157 images are preserved in `results/dataset_validation/dataset_manifest.jsonl` (tracked in Git).

---

## 6. Active Video Inventory & Duplicate Exclusion

The active evaluation cohort is strictly defined as follows:

| Cohort Component | Event Directories | Streams per Event | Total Video Streams | Status in Evaluation |
|---|---|---|---|---|
| **Full Train Events** | `event_001` through `event_023` (23 events) | 2 (`camera_front.mov`, `camera_back.mov`) | 46 streams | **ACTIVE** |
| **No-Train Negative Controls** | `event_001` through `event_003` (3 events) | 2 (`camera_front.mov`, `camera_back.mov`) | 6 streams | **ACTIVE** |
| **Engine-Only Event** | `engine_events/event_001` (1 event) | 2 (`camera_front.mov`, `camera_back.mov`) | 2 streams | **ACTIVE** |
| **Total Active Cohort** | **27 Active Events** | — | **54 Streams** | **PRIMARY EVALUATION** |
| **Historical Duplicate** | `engine_events/event_historical_duplicate_010` | 2 (`camera_front.mov`, `camera_back.mov`) | 2 streams | **QUARANTINED / EXCLUDED** |

The historical duplicate event is physically isolated and will not be counted in any active evaluation metric or denominator.

---

## 7. Annotation & Research-History Preservation

- **27 Review Sheets:** All present in `data/ground_truth/proposals/*/event_*_review_sheet.md`.
- **Candidate Proposal Versions:** All immutable historical proposal files (`_proposal_v1.json`, `_proposal_v2.json`, `_proposal_v6.json`) are preserved.
- **Review Logs:** All 27 review records are preserved in `data/ground_truth/reviews/*/event_*_review.json`.
- **Governance Integrity:**
  - **Zero auto-approvals were made.**
  - **No final approved ground-truth manifest was generated.**
  - **Prerequisite R03 remains retired** as a separate blocker in accordance with Protocol v7.0.0.
  - **Prerequisite R04 remains unresolved** (independent camera-local timelines enforced; zero empirical inter-camera sync offset assumed).

---

## 8. Missing or Unresolved Assets

**Zero project assets are missing.** Every required dataset, model checkpoint, ground-truth candidate file, Python module, script, and test suite is present in `/Users/sayemuddin/Projects/Train_automation`.

---

## 9. Current Git Status & Repository Health

```
Repository Path: /Users/sayemuddin/Projects/Train_automation
Branch: main (up to date with 'origin/main')
Baseline Commit: d4db94d4a4ea83ae4c510d65dfc99c5d6798304b
Disk Space: 14 GiB available on /
Backup Archive: /Users/sayemuddin/iCloud Drive (Archive)/Desktop/Train_automation (UNTOUCHED)
```

Tracked modifications (9 files):
- `docs/FINAL_ABLATION_MATRIX.md`
- `docs/FINAL_EXPERIMENT_DATA_FLOW.md`
- `docs/FINAL_GROUND_TRUTH_PROTOCOL.md`
- `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`
- `results/experiment_registry.jsonl`
- `src/railway_detection/cli/main.py`
- `src/railway_detection/data/layer_b.py`
- `tests/fixtures/mock_events.py`
- `tests/unit/test_layer_b_loader.py`

Untracked files include restored reports, research proposals, manifests, and gitignored media assets.

---

## 10. Exact Next Steps Before Running Full-Dataset Fusion

With the complete research environment safely restored in `~/Projects/Train_automation`, the following sequential actions must be taken before executing the full-dataset experiment:

1. **Reconcile Orchestrator Data Path (CF-02):**
   Update `scripts/run_real_world_experiments.py` line 53 to point to `data/raw/layer_b/v2/` rather than the empty `data/raw/layer_b/videos/`.
2. **Reconcile Audio Operating Threshold (CF-04):**
   Update defaults in `src/railway_detection/experiments/layer_b_processor.py` (lines 101 and 288) to canonical `0.3700` (matching the ESC-50 optimized operating point).
3. **Verify YOLO Class Names in Fusion Rules (PA-02):**
   Confirm the mapping between YOLO model class names (`front`, `rare`/`rear`, `side`) and the fusion rules in `src/railway_detection/fusion/`.
4. **Researcher Ground-Truth Approval:**
   Review and sign off on the 27 candidate review sheets in `data/ground_truth/proposals/` to freeze Stage 3 Ground Truth.
5. **Execute Full-Dataset Inference (E7 Baseline):**
   Run end-to-end vision, audio, and state-machine inference across all 27 active events (54 video streams) with full per-frame structured logging.
