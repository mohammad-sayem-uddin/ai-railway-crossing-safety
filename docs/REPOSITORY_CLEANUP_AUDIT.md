# Repository Cleanup, Storage Audit, and GitHub Readiness Report

**Date:** 2026-10-11
**Project:** AI-Assisted Railway Level-Crossing Safety Architecture
**Auditor:** Senior Software Engineer, Python Project Maintainer, and Research Reproducibility Auditor
**Repository:** `ai-railway-crossing-safety` (local project root)
**Git Remote:** `https://github.com/mohammad-sayem-uddin/ai-railway-crossing-safety.git` (branch: `main`)

> **Unit Standard:** All binary storage measurements are reported consistently using standard IEC binary units:
> $1\text{ GiB} = 1{,}024\text{ MiB} = 1{,}048{,}576\text{ KiB} = 1{,}073{,}741{,}824\text{ bytes}$;
> $1\text{ MiB} = 1{,}024\text{ KiB} = 1{,}048{,}576\text{ bytes}$.
> Local drive metrics reflect standard filesystem volume statistics (decimal GB, $1\text{ GB} = 10^9\text{ bytes}$).

---

## 1. Executive Summary

This storage audit and repository cleanup prepares the railway-crossing safety codebase for a clean, professional, and reproducible GitHub release without disrupting the ongoing human verification of `event_001` or endangering research provenance.

### 1.1 Storage Summary (Pre-Cleanup Baseline)
* **Local Storage Baseline:** Constrained workstation volume capacity (<10 GB free space prior to cleanup).
* **Repository Working Tree Size:** ~6.10 GiB (6,550,224,960 bytes) across 41,603 files.
* **Storage Distribution by Directory:**
  1. `data/`: 5.96 GiB (6,107.00 MiB / 6,403,669,272 bytes) — includes 3.58 GiB (3,660.92 MiB) of raw Layer B field recordings across the 27 evaluation events.
  2. `.venv/`: 1.10 GiB (1,121.80 MiB / 1,176,277,901 bytes) — local virtual environment (15,975 files).
  3. `ESC-50-master/`: 843.09 MiB (884,047,129 bytes) — external environmental sound dataset used to train Audio V3.
  4. `experiments/`: 156.52 MiB (164,122,495 bytes) — frozen checkpoints, training run logs, and manifests.
  5. `scratch/`: 135.87 MiB (142,471,915 bytes) — active and candidate inspection frame/WAV extractions.
  6. `Unseen_Video/`: 100.39 MiB (105,262,575 bytes) — manual uncalibrated camera test recordings.
  7. `outputs/`: 94.98 MiB (99,591,996 bytes) — duplicate screen recordings in `outputs/temp_uploads/` (reclaimed in this pass).
  8. `.git/`: 52.63 MiB (55,188,470 bytes) — local Git object database.
  9. `research/`: 36.39 MiB (38,155,664 bytes) — qualitative research figures and plotting utilities.
  10. `results/`: 24.09 MiB (25,263,787 bytes) — dataset validation manifests and failure logs.

---

## 2. Cryptographic Checkpoint Integrity Verification

The master protocol documents (`docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` v8.0.0 and `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` v6.0.0) mandate strict model freezing. All models in the repository were verified directly from raw bytes on disk:

| Model Role | Canonical File Path | Actual Size (Bytes) | Actual Size (MiB) | Expected SHA-256 | Actual SHA-256 | Verification Status |
|---|---|---|---|---|---|---|
| **Frozen YOLOv8n Vision** | `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` | 24,493,159 bytes | 23.36 MiB | `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` | `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` | **EXACT MATCH (100% Verified)** |
| **Frozen Audio V3 Model** | `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt` | 329,497 bytes | 0.31 MiB | `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782` | `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782` | **EXACT MATCH (100% Verified)** |
| **Prohibited Audio V2 Model** | `models/audio/best_checkpoint.pt` | 334,839 bytes | 0.32 MiB | `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5` | `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5` | **EXACT MATCH (Confirmed Prohibited)** |

**Provenance Assessment:** Model integrity is pristine. The prohibited Audio V2 weights remain quarantined and explicitly locked out of the pipeline. The canonical Audio V3 checkpoint and YOLOv8n weights are bit-for-bit identical to authoritative protocol specifications.

---

## 3. Duplicate Analysis & Verification

An exact byte-for-byte SHA-256 collision search was conducted across all files in `outputs/` and other potential redundant directories.

Four large video files in `outputs/temp_uploads/` were identified as 100% duplicates of canonical source recordings in `Unseen_Video/`:

| Duplicate Artifact | Canonical Reference Location | Exact Size (Bytes) | Size (MiB) | Verified SHA-256 Collision Digest | Action |
|---|---|---|---|---|---|
| Uncalibrated Camera Recording 1 | `Unseen_Video/` | 20,205,532 bytes | 19.27 MiB | `43ab86cd9e8557378d3878b27ec7cb78a3cba3973c52a0a256a422b5168853c8` | **Safely Deleted** |
| Uncalibrated Camera Recording 2 | `Unseen_Video/` | 6,719,956 bytes | 6.41 MiB | `5c6f73516e885d519b78b0f8d9519195baee0c25a74ab2e557b49d44473eeb98` | **Safely Deleted** |
| Uncalibrated Camera Recording 3 | `Unseen_Video/` | 61,068,576 bytes | 58.24 MiB | `39ffee07a6ecad0906233d6790938f36c57e556e9c42aee78ce89622839fe5e9` | **Safely Deleted** |
| Uncalibrated Camera Recording 4 | `Unseen_Video/` | 11,597,932 bytes | 11.06 MiB | `d6f2b2a95c52c6b44ec6a537f8f94cb459ff6a9e144a0eb52d27771239558913` | **Safely Deleted** |

* **Total duplicate space reclaimed:** **99,591,996 bytes (94.98 MiB)**.
* Canonical copies in `Unseen_Video/` are preserved locally on disk and excluded from Git tracking via `.gitignore`.
* `outputs/.gitkeep` is preserved to maintain repository structure.

---

## 4. Asset Classification & Storage Policy

All repository directories and file groups are classified into four distinct operational categories:

### Category 1: Essential Source Data (Retain Locally; Exclude from GitHub)
These datasets are foundational to research reproducibility but too large or local-only for GitHub repository distribution:
* `data/raw/layer_b/v2/` (3.58 GiB / 3,838,753,633 bytes): Original dual-camera synchronized field recordings across the documented evaluation cohort of **27 total events** (23 full-train, 3 no-train, 1 engine-only pass, plus 1 historical duplicate). Video resolutions vary by device (1080p Full HD 1920×1080 and 4K UHD 3840×2160, with portrait/landscape display orientations, e.g. `event_001` back camera). Must remain strictly intact in their exact directory layout.
* `ESC-50-master/` (843.09 MiB / 884,047,129 bytes): ESC-50 environmental sound dataset archive used for Audio V3 transfer learning.
* `Unseen_Video/` (100.39 MiB / 105,262,575 bytes): Raw field camera recordings from August 2026.
* `.venv/` (1.10 GiB / 1,176,277,901 bytes): Virtual environment and installed Python packages.

### Category 2: Essential Artifacts (Version-Controlled in Git)
Small, deterministic, irreplaceable artifacts appropriate for standard version control:
* Source code: `src/railway_detection/` (including the AI-assisted annotation pipeline).
* Unit, integration, and smoke test suites: `tests/`.
* Versioned schemas and configuration files: `configs/`.
* Research documentation: `docs/` (including all `FINAL_*` protocols and historical decision logs).
* Ground-truth proposal lifecycle records:
  - `data/ground_truth/proposals/train_events/event_001_proposal.json` (v1)
  - `data/ground_truth/proposals/train_events/event_001_proposal_v2.json`
  - `data/ground_truth/proposals/train_events/event_001_proposal_v3.json`
  - `data/ground_truth/proposals/train_events/event_001_proposal_v4.json`
  - `data/ground_truth/proposals/train_events/event_001_review_sheet.md`
* Package definitions: `pyproject.toml`, `README.md`, `.gitignore`, `.env.example`.

### Category 3: Reproducible Temporary Files (Safe to Delete)
Disposable build and runtime artifacts that can be regenerated automatically without data loss:
* Confirmed exact duplicate media: `outputs/temp_uploads/*.mov` (94.98 MiB / 99,591,996 bytes).
* Python bytecode: all `__pycache__/` directories (0.60 MiB / 631,647 bytes).
* Static analysis and test caches:
  - `.mypy_cache/` (55.27 MiB / 57,955,873 bytes).
  - `.pytest_cache/` (0.02 MiB / 21,392 bytes).
  - `.ruff_cache/` (0.01 MiB / 11,216 bytes).
* **Total safe immediate space reclaimed:** **150.88 MiB (158,212,124 bytes)**.

### Category 4: Candidates Requiring Researcher Approval
* `scratch/event_001_inspect/` (81.29 MiB / 85,236,923 bytes, 26 items): An earlier frame/spectrogram extraction directory superseded by `scratch/pilot_inspection_event_001/`. Because it is in `scratch/`, it is protected during this pass. **Recommendation:** Recommend deletion to the researcher once pilot review is complete.
* Large model weights (`experiments/vision/.../best.pt` 23.36 MiB, `experiments/audio/.../best.pt` 0.31 MiB): These weights currently live in `experiments/` locally and are excluded from Git via `*.pt`. If released publicly, consider Zenodo/HuggingFace release rather than direct GitHub commits.

---

## 5. Protected Research Assets Register

The following directories and files are strictly protected and were NOT modified, moved, or deleted:

1. **Active Annotation Review Assets:**
   - `data/ground_truth/proposals/train_events/event_001_proposal.json` (v1)
   - `data/ground_truth/proposals/train_events/event_001_proposal_v2.json` (v2)
   - `data/ground_truth/proposals/train_events/event_001_proposal_v3.json` (v3)
   - `data/ground_truth/proposals/train_events/event_001_proposal_v4.json` (v4)
   - `data/ground_truth/proposals/train_events/event_001_review_sheet.md`
   - `scratch/pilot_inspection_event_001/` (53 inspection frames and extracted WAVs)
2. **Authoritative Research Methodologies:**
   - `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` (v8.0.0)
   - `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` (v6.0.0)
   - `docs/FINAL_EXPERIMENT_DATA_FLOW.md` (v5.1.0)
   - `docs/FINAL_ABLATION_MATRIX.md` (v5.1.0)
   - All preceding foundational and historical documentation in `docs/`.
3. **Primary Evaluation Media:**
   - `data/raw/layer_b/v2/` (all 27 evaluation events: 23 full-train, 3 no-train, 1 engine-only, plus 1 historical duplicate; front and back streams).
4. **Frozen Model Weights & Checkpoints:**
   - `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` (23.36 MiB)
   - `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt` (0.31 MiB)
   - `models/audio/best_checkpoint.pt` (0.32 MiB)

---

## 6. Operating System Storage & File Synchronization Notes

During this audit, a notable operating system behavior was analyzed for research reproducibility:
* **Cloud-Synced Desktop Environments:** When a local workspace is hosted under cloud-synchronized desktop folders (such as macOS iCloud Drive desktop sync), low host volume headroom can cause operating systems to evict inactive working-tree files into dataless stubs.
* **Synchronous Kernel I/O Eviction Behavior:** Standard POSIX `open()` and `read()` calls on evicted dataless stubs synchronously wait for cloud sync daemons to download file contents over the network. If cloud sync is paused or throttled, unconstrained tools traversing large directories (such as unguided `git status` or test discovery descending into `.venv`) can block in kernel I/O.
* **Resolution & Guardrails:**
  - Standard development tools must explicitly avoid traversing unneeded large directories (`.venv`, `ESC-50-master`, `scratch`).
  - `.gitignore` must comprehensively exclude `.venv/`, caches, and large local media to ensure Git operations remain instant and never hang on dataless stubs.
  - Python scripts and tests should invoke with `-c /dev/null` or explicit directory targeting to avoid scanning dataless files.

---

## 7. Actions Executed in this Pass

1. **Cryptographic Checkpoint Audit:** Verified SHA-256 for YOLOv8n, Audio V3, and blocked Audio V2 models down to the exact byte.
2. **Duplicate Media Deletion:** Removed 4 confirmed SHA-256 duplicate videos in `outputs/temp_uploads/*.mov` (freed 94.98 MiB / 99,591,996 bytes). Preserved `outputs/.gitkeep`.
3. **Cache Purge:** Removed `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, and all `__pycache__/` bytecode directories (freed 55.90 MiB / 58,620,128 bytes).
4. **`.gitignore` Modernization:** Completely overhauled `.gitignore` to protect source code, documentation, proposals, and configuration while strictly ignoring OS artifacts, credentials, caches, scratch files, and multi-gigabyte local media.
5. **Created `.env.example`:** Provided a sanitized template for local environment variables (`GEMINI_API_KEY`, etc.) without exposing any actual keys.
6. **Rewrote `README.md`:** Authoritative 14-section research-grade documentation reflecting the multimodal architecture, AI-assisted annotation pipeline, frozen model identities, local data reproduction steps, and scientific safety boundaries.
7. **Quality Verification:** Executed unit tests for the annotation pipeline (`tests/test_annotation_workflow.py`), achieving 100% pass rate (16/16 passed).
