# Real-World Dataset Status

**Last Updated:** 2026-10-07  
**Project:** AI Railway Level-Crossing Safety Research Project  
**Status Audit:** Post-Retirement / Pre-Ingestion  

---

## Current Real-World Dataset Status

### OLD REAL-WORLD TEST DATASET:
**RETIRED / DELETED**

- **Dataset Identifier:** Layer B Real-World Train Passage Evaluation Dataset (Initial 21-Event Collection)
- **Previous Location:** `data/raw/layer_b/videos/` and `Train_test_video_new/`
- **Extracted Audio Location:** `data/processed/layer_b/audio/`
- **Current Status:** All 84 raw video files (42 in `data/raw/layer_b/videos/`, 42 in `Train_test_video_new/`), 21 camera symlinks, and 42 extracted audio files have been safely and intentionally deleted.
- **Metadata & Manifest Preservation:** Full historical event metadata (`metadata.json`), ground truth reference labels (`event_labels.json`), and video manifests have been archived to `results/archive/old_test_dataset/` marked `HISTORICAL — OLD TEST DATASET — RETIRED`.
- **Historical Benchmark Preservation:** All historical experiment outputs, metrics, figures, state timelines, and comparative benchmarks (B0–B7) in `results/experiments/` remain preserved for research traceability and reproducibility.

> [!NOTE]
> *The previous real-world evaluation media was intentionally retired before ingestion of a replacement evaluation dataset.*

---

### NEW REAL-WORLD TEST DATASET:
**NOT YET INGESTED**

- **Status:** Pending ingestion.
- **Active Ingestion Directory:** `data/raw/layer_b/videos/` (currently empty and ready for new data).
- **Active Processed Audio Directory:** `data/processed/layer_b/audio/` (currently empty and ready for new data).
- **Manifest Status:** Active manifests in `data/manifests/` will be generated once the new dataset is introduced.
- **Specification:** The new evaluation dataset does not exist in the repository yet and must not be assumed to have predetermined structure, filenames, or counts until formally ingested and validated.

---

## Active Repository Data Invariants

| Dataset / Asset | Role | Status | Path |
|---|---|---|---|
| **Dataset V1** | Vision Training & Validation Baseline (YOLOv8n) | **PROTECTED / ACTIVE** | `data/raw/vision/v1/` |
| **Train Horn Audio** | Acoustic Horn Model Development (Positive & Negative) | **PROTECTED / ACTIVE** | `data/raw/audio/train_horn/` |
| **Audio Staging** | Train Horn Staging Copy | **PROTECTED / ACTIVE** | `Train_Audio_new/` |
| **YOLO Checkpoint** | Trained Vision Detector Weights (`best.pt`) | **PROTECTED / ACTIVE** | `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` |
| **Audio Checkpoint** | Trained Audio Classifier Weights | **PROTECTED / ACTIVE** | `models/audio/best_checkpoint.pt` |
| **Layer B Videos** | Real-World Held-Out Evaluation | **EMPTY / READY FOR NEW DATA** | `data/raw/layer_b/videos/` |
| **Layer B Audio** | Real-World Extracted Test Audio | **EMPTY / READY FOR NEW DATA** | `data/processed/layer_b/audio/` |
| **Historical Results** | Research History & Baseline Records (B0–B7) | **PRESERVED** | `results/experiments/` |
