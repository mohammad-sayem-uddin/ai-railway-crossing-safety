# Real-World Dataset Organization & Directory Structure

**Project**: AI Railway Level-Crossing Safety Research  
**Document Version**: 1.0.0  
**Status**: ACTIVE

---

## 1. Directory Tree Architecture

The repository data structure has been organized to ensure clean isolation between development assets, evaluation bundles, and audio models.

```text
/Users/sayemuddin/Desktop/Train_automation/
│
├── Train_test_video_new/                     <-- [ORIGINAL UNTOUCHED SOURCE] 21 Front + 21 Back videos
│   ├── Front/ (1.mov .. 21.mov)
│   └── Back/  (1.mov .. 21.mov)
│
├── Train_Audio_new/                          <-- [ORIGINAL UNTOUCHED SOURCE] 87 audio files
│   ├── 1.mp3 .. 42.mp3
│   ├── 43.pdf .. 46.pdf (Valid MP3 streams)
│   └── BD train horn / locomotive recordings
│
├── data/
│   ├── raw/
│   │   ├── vision/
│   │   │   └── v1/                           <-- Dataset V1 (YOLO Training/Validation)
│   │   │       └── baler.v1i.yolov8/
│   │   │
│   │   ├── layer_b/
│   │   │   └── videos/                       <-- [ORGANIZED EVALUATION BUNDLES]
│   │   │       ├── event_001/
│   │   │       │   ├── camera_front.mov      <-- Front camera (1080p, HEVC, AAC audio)
│   │   │       │   ├── camera_back.mov       <-- Back camera (4K, HEVC, AAC audio)
│   │   │       │   └── camera_rear.mov       <-- Symlink -> camera_back.mov
│   │   │       ├── event_002/
│   │   │       │   ├── camera_front.mov
│   │   │       │   ├── camera_back.mov
│   │   │       │   └── camera_rear.mov
│   │   │       └── ... [event_003 through event_021]
│   │   │
│   │   └── audio/
│   │       └── train_horn/
│   │           ├── positive/                 <-- [ORGANIZED AUDIO DEVELOPMENT SAMPLES]
│   │           │   ├── 1.mp3 .. 42.mp3       (41.mp3 and 42.mp3 are bitwise duplicates)
│   │           │   ├── 43.pdf .. 46.pdf      (Preserved originals)
│   │           │   ├── 43.mp3 .. 46.mp3      (Symlinks to .pdf for standard audio loaders)
│   │           │   └── ... [87 total audio samples]
│   │           │
│   │           └── negative/                 <-- [MISSING - DOCUMENTED]
│   │               └── README.md             (Specification for acquiring background audio)
│   │
│   ├── manifests/                            <-- [DATASET AUDIT MANIFESTS]
│   │   ├── layer_b_video_manifest.jsonl      (42 records, role: real_world_evaluation)
│   │   ├── layer_b_video_manifest.json
│   │   ├── train_horn_audio_manifest.jsonl   (87 records, role: audio_model_development)
│   │   ├── train_horn_audio_manifest.json
│   │   └── dataset_inventory_summary.json    (Comprehensive aggregate metadata)
│   │
│   ├── metadata/
│   │   └── vision_v1_metadata.json
│   ├── interim/
│   ├── processed/
│   └── splits/
│
├── docs/
│   ├── REAL_DATASET_INVENTORY.md             <-- Comprehensive audit, pairing table, statistics
│   ├── REAL_DATASET_STRUCTURE.md             <-- This document
│   ├── PRE_REAL_DATA_COMPLETION_CHECKLIST.md
│   ├── RESEARCH_PROTOCOL_V2.md
│   └── EXPERIMENT_PROTOCOL_V2.md
│
└── tests/
    └── unit/
        └── test_real_dataset_inventory.py    <-- Automated validation of datasets & manifests
```

---

## 2. Naming Conventions & Loader Compatibility

### 2.1 Layer B Multi-Camera Bundles
- Each event folder is strictly named `event_XXX` (e.g. `event_001` through `event_021`).
- Inside each folder:
  - `camera_front.mov`: Primary approach viewpoint.
  - `camera_back.mov`: Departure / opposite-angle viewpoint.
  - `camera_rear.mov`: Relative symlink targeting `camera_back.mov`.
- **Loader Compatibility**: `railway_detection.data.layer_b.load_event_bundle` supports `camera_front.mov`, `camera_back.mov`, and `camera_rear.mov` directly in its candidate search tuple.

### 2.2 Audio Development Files
- Positive train-horn samples reside in `data/raw/audio/train_horn/positive/`.
- All 87 source files are copied with 100% SHA-256 hash preservation.
- The 4 misnamed files (`43.pdf`, `44.pdf`, `45.pdf`, `46.pdf`) maintain their exact original filenames, while companion symlinks (`43.mp3`, `44.mp3`, `45.mp3`, `46.mp3`) allow standard audio loaders filtering on `.mp3` to ingest them without destructive modification.
- Duplicate file `42.mp3` is documented in the manifest as a duplicate of `41.mp3`.

---

## 3. Verification & Auditing Commands

To re-verify the dataset integrity at any time:

```bash
# Verify all unit tests including real dataset inventory tests:
PYTHONDONTWRITEBYTECODE=1 /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -B -m pytest -q tests/unit/test_real_dataset_inventory.py

# Run the complete test suite (200 passing tests):
PYTHONDONTWRITEBYTECODE=1 /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -B -m pytest -q
```
