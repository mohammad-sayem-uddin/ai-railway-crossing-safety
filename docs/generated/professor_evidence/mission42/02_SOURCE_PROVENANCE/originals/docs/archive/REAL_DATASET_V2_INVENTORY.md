# Real-World Dataset V2 Inventory & Technical Audit

**Project**: AI Railway Level-Crossing Safety Research  
**Document Version**: 2.0.0  
**Audit Date**: October 8, 2026  
**Status**: INVENTORY & V2 ORGANIZATION COMPLETE (TESTING FROZEN)

---

## 1. Executive Summary

This document establishes the authoritative inventory, cryptographic audit, and research separation protocol for the newly ingested **Dataset V2** (`TRAIN_VIDEO_AUDIO 2`).

### Core Inventory Summary
1. **Full Train Events (Layer B V2)**: **23 paired events** (46 videos: 23 front + 23 back).
   - Events 1 through 9, 11 through 21, plus 3 low-light/night events (22, 23, 24).
   - Event 10 was accounted for in the Engine camera set (see Section 6).
   - 100% paired (0 unpaired files).
   - Evaluation Eligible: **YES** (`REAL_WORLD_TRAIN_EVENT`).
2. **No-Train Events (Layer B V2)**: **3 paired events** (6 videos: 3 front + 3 back).
   - Events 1, 2, 3 representing daytime baseline crossings with no train passage.
   - 100% paired (0 unpaired files).
   - Evaluation Eligible: **YES** (`REAL_WORLD_NO_TRAIN`).
3. **Engine-Only Camera Material**: **2 paired events** (4 videos: 2 front + 2 back).
   - `event_001`: **1 NEW paired engine-only event** (recorded 2026-10-04, 7.87s front / 9.80s back).
     - Evaluation Eligible: **YES** (`REAL_WORLD_ENGINE_ONLY`).
   - `event_historical_duplicate_010`: **1 historical duplicate event** (former `event_010`, recorded 2026-09-14, 7.17s front / 7.80s back).
     - Identical byte and SHA-256 match with the retired Layer B `event_010`.
     - Evaluation Eligible: **NO** (`HISTORICAL_DUPLICATE_EXCLUDED`).
4. **Standalone Train Horn Audio Development Dataset**:
   - **Positive Audio**: **87 files** total, **86 unique recordings** (1 duplicate pair: `41.mp3` == `42.mp3`).
   - **Negative Audio**: **97 files** total, **95 unique recordings** (2 duplicate pairs: `5.mp3` == `6.mp3`, `27.mp3` == `28.mp3`).
   - Corrupt files: **0 files**.
   - Primary balanced training subset: **86 unique positive** + **86 selected unique negative** recordings.

---

## 2. Total Event & Camera Counts

| Dataset Partition | Events | Front Cameras | Back Cameras | Total Files | Pairing Confidence | Evaluation Status |
|---|---|---|---|---|---|---|
| **Full Train Events (Daytime)** | 20 | 20 | 20 | 40 | 100% Confirmed | Eligible (`REAL_WORLD_TRAIN_EVENT`) |
| **Full Train Events (Night/Low-light)** | 3 | 3 | 3 | 6 | 100% Confirmed | Eligible (`REAL_WORLD_TRAIN_EVENT`) |
| **Engine-Only Events (New)** | 1 | 1 | 1 | 2 | 100% Confirmed | Eligible (`REAL_WORLD_ENGINE_ONLY`) |
| **Engine-Only (Historical Duplicate)** | 1 | 1 | 1 | 2 | 100% Confirmed | **EXCLUDED** (`HISTORICAL_DUPLICATE_EXCLUDED`) |
| **No-Train Events (Baseline)** | 3 | 3 | 3 | 6 | 100% Confirmed | Eligible (`REAL_WORLD_NO_TRAIN`) |
| **Subtotal Real-World Video Media** | **28** | **28** | **28** | **56** | **100%** | **27 Eligible / 1 Excluded** |
| **Positive Audio (Train Horn)** | N/A | N/A | N/A | 87 | N/A | 86 Unique / 1 Duplicate |
| **Negative Audio (Background/Field)** | N/A | N/A | N/A | 97 | N/A | 95 Unique / 2 Duplicates |
| **Subtotal Audio Media** | **N/A** | **N/A** | **N/A** | **184** | **N/A** | **181 Unique / 3 Duplicates** |

---

## 3. Pairing Verification & Synchronization Analysis

Every dual-camera event was paired based on concurrent timestamps, synchronized file naming sequences, matching physical passage durations, and verified hardware metadata.

### 3.1 Full Train Events (`train_events/`)
- `event_001` (`1.mov`): Front 49.84s (1080p @ 29.97fps) ↔ Back 46.06s (4K @ 59.94fps), Delta: 3.77s
- `event_002` (`2.mov`): Front 32.49s (1080p @ 29.97fps) ↔ Back 30.20s (1080p @ 30.00fps), Delta: 2.29s
- `event_003` (`3.mov`): Front 33.32s (1080p @ 29.97fps) ↔ Back 32.53s (1080p @ 30.00fps), Delta: 0.79s
- `event_004` (`4.mov`): Front 75.59s (1080p @ 29.97fps) ↔ Back 78.07s (1080p @ 30.00fps), Delta: 2.48s
- `event_005` (`5.mov`): Front 79.56s (1080p @ 29.97fps) ↔ Back 78.11s (1080p @ 30.00fps), Delta: 1.45s
- `event_006` (`6.mov`): Front 126.19s (1080p @ 29.97fps) ↔ Back 126.98s (1080p @ 30.00fps), Delta: 0.79s
- `event_007` (`7.mov`): Front 38.26s (1080p @ 29.97fps) ↔ Back 34.54s (1080p @ 30.00fps), Delta: 3.72s
- `event_008` (`8.mov`): Front 58.88s (1080p @ 29.97fps) ↔ Back 62.72s (1080p @ 30.00fps), Delta: 3.84s
- `event_009` (`9.mov`): Front 42.90s (1080p @ 29.97fps) ↔ Back 37.60s (1080p @ 30.00fps), Delta: 5.29s
- `event_010` (`11.mov`): Front 24.02s (1080p @ 29.97fps) ↔ Back 23.52s (1080p @ 30.00fps), Delta: 0.50s
- `event_011` (`12.mov`): Front 37.69s (1080p @ 29.97fps) ↔ Back 37.37s (1080p @ 30.00fps), Delta: 0.32s
- `event_012` (`13.mov`): Front 75.19s (1080p @ 29.97fps) ↔ Back 70.74s (1080p @ 30.00fps), Delta: 4.45s
- `event_013` (`14.mov`): Front 73.69s (1080p @ 29.97fps) ↔ Back 73.24s (1080p @ 30.00fps), Delta: 0.45s
- `event_014` (`15.mov`): Front 55.04s (1080p @ 29.97fps) ↔ Back 53.50s (1080p @ 30.00fps), Delta: 1.54s
- `event_015` (`16.mov`): Front 31.16s (1080p @ 29.97fps) ↔ Back 22.23s (1080p @ 30.00fps), Delta: 8.92s
- `event_016` (`17.mov`): Front 46.87s (1080p @ 29.97fps) ↔ Back 45.27s (1080p @ 30.00fps), Delta: 1.60s
- `event_017` (`18.mov`): Front 81.66s (1080p @ 29.97fps) ↔ Back 83.77s (1080p @ 30.00fps), Delta: 2.11s
- `event_018` (`19.mov`): Front 58.94s (1080p @ 29.97fps) ↔ Back 52.64s (1080p @ 30.00fps), Delta: 6.30s
- `event_019` (`20.mov`): Front 60.31s (1080p @ 29.97fps) ↔ Back 51.13s (1080p @ 30.00fps), Delta: 9.18s
- `event_020` (`21.mov`): Front 28.55s (1080p @ 29.97fps) ↔ Back 29.87s (1080p @ 30.00fps), Delta: 1.32s
- `event_021` (`22(night)`): Front 53.41s (1080p @ 29.97fps) ↔ Back 61.37s (4K @ 30.00fps), Delta: 7.96s
- `event_022` (`23(night)`): Front 43.64s (1080p @ 29.97fps) ↔ Back 46.34s (4K @ 30.00fps), Delta: 2.70s
- `event_023` (`24(night)`): Front 44.84s (1080p @ 29.97fps) ↔ Back 45.77s (4K @ 30.00fps), Delta: 0.93s

### 3.2 No-Train Events (`no_train_events/`)
- `event_001`: Front 24.64s (4K @ 30.00fps) ↔ Back 24.42s (1080p @ 29.97fps), Delta: 0.22s
- `event_002`: Front 11.88s (1080p @ 29.97fps) ↔ Back 13.33s (4K @ 30.00fps), Delta: 1.45s
- `event_003`: Front 23.79s (1080p @ 29.97fps) ↔ Back 22.73s (4K @ 30.00fps), Delta: 1.06s

---

## 4. Engine Camera Findings & Resolution of Event 10

The investigative audit revealed the origin and nature of the two pairs in `Engine_front_camera` and `Engine_back_camera`:
1. **Engine Event 2 (`2.MOV`)**:
   - Front Camera: iPhone 12 Pro, 7.17s, recorded 2026-09-14 16:18:06 (SHA `feda74d909d5a888c3467f51b92366f2f2686a1b0a49c0c7e0357c6d23b68f06`)
   - Back Camera: iPhone 15 Pro Max, 7.80s, recorded 2026-09-14 16:18:07 (SHA `f9a1beb31578cd705d21c709a57e98abfed94d4e0078c65179522d26340a79b8`)
   - **Conclusion**: This is the exact historical copy of `event_010` from the retired test dataset. It explains why `10.mov` was omitted from `Train_front` and `Train_backk`. It is preserved under `engine_events/event_historical_duplicate_010/` with `evaluation_eligible = false`.
2. **Engine Event 1 (`1.MOV` / `1.mov`)**:
   - Front Camera: iPhone 12 Pro, 7.87s, recorded 2026-10-04 19:26:25 (SHA `847d04fef5ba...`)
   - Back Camera: iPad 10th gen, 9.80s, recorded 2026-10-04 19:26:28 (SHA `5f60e9d6d877...`)
   - **Conclusion**: A genuine new locomotive engine-only passage. Preserved under `engine_events/event_001/` with `evaluation_eligible = true` and `event_type = "engine_only"`.

---

## 5. Audio Inventory & Duplicate Elimination

### 5.1 Positive Audio (Train Horns)
- **Total Physical Files**: 87 files
- **Bitwise Duplicates**: Exactly 1 pair: `41.mp3` and `42.mp3` (SHA `17f81c16ee65f38e7d05089395e0005b8c75663f7b9470bec864274b76cf314a`).
- **Unique Positive Recordings**: **86 recordings**
- **Durations**: Mean 3.42s (Range: 1.00s to 12.00s; Cumulative: 297.37s)
- **Format**: MPEG Audio Layer III (MP3), 44.1 kHz / 48.0 kHz, Stereo

### 5.2 Negative Audio (Non-Horn Background / Ambience)
- **Total Physical Files**: 97 files
- **Bitwise Duplicates**: Exactly 2 pairs:
  - `5.mp3` == `6.mp3` (SHA `6e828ee65702...`)
  - `27.mp3` == `28.mp3` (SHA `c206554f8c92...`)
- **Unique Negative Recordings**: **95 recordings**
- **Durations**: Mean 11.96s (Range: 4.07s to 572.34s; Cumulative: 1,159.89s)
- **Special Case**: `14.mp3` is an extended 572.34s (~9.5 minute) continuous field ambient recording. It has been designated as the extended ambient baseline pool and held out from the primary 1-to-1 balanced training partition.

### 5.3 Balanced Selection Protocol (86 vs 86)
- **Selected Positive Class**: All 86 unique locomotive horn recordings.
- **Selected Negative Class**: Exactly 86 unique field acoustic recordings chosen deterministically across duration bins (excluding `14.mp3` and 8 evenly spaced held-out test clips).
- **Held-Out Negative Robustness Pool**: 9 unique recordings preserved for hard-negative evaluation.

---

## 6. Strict Research Separation Firewall

To preserve experimental validity and zero-leakage ML standards:
1. **YOLO Frozen**: `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` remains frozen.
2. **Dataset V1 Untouched**: `data/raw/vision/v1/` remains strictly unmodified.
3. **No Embedded Audio Leakage**: Embedded audio inside `data/raw/layer_b/v2/` test videos is NEVER extracted or mixed into the audio training pipeline.
4. **Recording-Level Audio Split**: Splitting is performed strictly at the source-recording level prior to windowing, guaranteeing 0% train/val/test data overlap.

---

## 7. Final Filesystem Structure

```
data/raw/
├── vision/
│   └── v1/                          [FROZEN YOLO TRAINING SET]
│
├── layer_b/
│   └── v2/                          [UNSEEN REAL-WORLD EVALUATION POOL]
│       ├── train_events/            [23 paired full-train events]
│       │   ├── event_001/
│       │   │   ├── camera_front.mov
│       │   │   ├── camera_back.mov
│       │   │   └── camera_rear.mov -> camera_back.mov
│       │   └── ... event_023/
│       ├── engine_events/           [Engine-only events]
│       │   ├── event_001/           [NEW engine-only event: ELIGIBLE]
│       │   └── event_historical_duplicate_010/ [Historical Event 010: EXCLUDED]
│       └── no_train_events/         [3 paired baseline events]
│           ├── event_001/
│           ├── event_002/
│           └── event_003/
│
└── audio/
    └── train_horn/                  [STANDALONE AUDIO DEVELOPMENT]
        ├── positive/                [87 files, 86 unique horn recordings]
        └── negative/                [97 files, 95 unique ambient recordings]
```

---

## 8. Authoritative Manifests
- Video Manifest: `data/manifests/real_world_v2_video_manifest.json` (and `.jsonl`)
- Audio Manifest: `data/manifests/audio_training_v2_manifest.json` (and `.jsonl`)
- Audio Selection Manifest: `data/manifests/audio_training_v2_selection.json`
