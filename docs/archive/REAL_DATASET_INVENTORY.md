# Real-World Dataset Inventory & Technical Audit

**Project**: AI Railway Level-Crossing Safety Research  
**Document Version**: 1.0.0  
**Audit Date**: September 21, 2026  
**Status**: INVENTORY & ORGANIZATION COMPLETE (TRAINING FROZEN)

---

## 1. Executive Summary

This document provides a formal inventory, technical audit, and separation specification for the two newly added empirical datasets:
1. **Layer B Real-World Video Dataset** (`Train_test_video_new`): 21 dual-camera train-passage events (42 video files) designated strictly for **unseen real-world evaluation**.
2. **Standalone Train Horn Audio Dataset** (`Train_Audio_new`): 87 recordings (83 `.mp3` + 4 misnamed `.pdf` containing valid MP3 audio) designated as the positive class for **audio model development**.

> [!IMPORTANT]
> **Strict Research Separation Enforced**:
> - Dataset V1 remains the sole development/training dataset for the baseline YOLOv8n vision model.
> - Layer B video events are held out for zero-leakage multimodal evaluation.
> - Embedded audio from test videos is preserved for event-level evaluation and must NEVER be mixed into audio training.
> - Negative/background audio is currently missing and must be acquired before audio classifier training.

---

## 2. Dataset A: Layer B Real-World Video Evaluation Dataset

### 2.1 Overview & Role
- **Source Directory**: `Train_test_video_new/`
- **Organized Target Directory**: `data/raw/layer_b/videos/`
- **Dataset Role**: `real_world_evaluation`
- **Total Passage Events**: 21 events (`event_001` through `event_021`)
- **Total Video Files**: 42 files (21 front-camera + 21 back-camera)
- **Container Format**: QuickTime Movie (`.mov`)

### 2.2 Technical Video & Audio Metadata
| Property | Front Camera (`camera_front.mov`) | Back Camera (`camera_back.mov`) | Notes |
|---|---|---|---|
| **File Count** | 21 files (`1.mov` .. `21.mov`) | 21 files (`1.mov` .. `21.mov`) | 100% paired |
| **Resolution** | 1920×1080 (1080p Full HD) across all 21 files | 1920×1080 (20 files); 3840×2160 (4K UHD, 1 file: `event_001`) | Back camera in event 1 recorded in 4K |
| **Video Codec** | HEVC / H.265 (`hev1`) | HEVC / H.265 (`hev1`) | High efficiency modern video |
| **Frame Rate (FPS)**| 29.97 fps (constant) | 29.97 – 30.0 fps (20 files); 59.94 fps (`event_001`) | Smooth temporal sampling |
| **Embedded Audio** | Present on 100% of files | Present on 100% of files | Both views capture ambient audio |
| **Audio Codec** | AAC (`mp4a`) | AAC (`mp4a`) | Stereo |
| **Audio Sample Rate**| 48,000 Hz | 48,000 Hz | Broadcast quality |
| **Audio Channels** | 2 channels (stereo) | 2 channels (stereo) | Spatial channel availability |
| **Min Duration** | 7.17 s (`event_010`) | 7.80 s (`event_010`) | Shortest passage |
| **Max Duration** | 126.19 s (`event_006`) | 126.98 s (`event_006`) | Longest freight train passage |
| **Mean Duration**| 53.21 s | 51.33 s | Consistent recording window |
| **Total Duration**| 1,117.33 s (18.62 min) | 1,077.90 s (17.97 min) | Cumulative: 2,195.23 s (36.59 min) |

### 2.3 Camera Event Pairing Table
Every event is unambiguously matched by filename index (`Front/{i}.mov` ↔ `Back/{i}.mov`). Duration deltas range from 0.3s to 9.2s, consistent with manual camera start/stop synchronization in field operations.

| Event ID | Original Front File | Original Back File | Front Res / FPS | Back Res / FPS | Front Dur (s) | Back Dur (s) | Offset Delta (s) | Audio Streams | Pairing Confidence |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `event_001` | `1.mov` | `1.mov` | 1920×1080 @ 29.97 | 3840×2160 @ 59.94 | 49.84 | 46.07 | 3.77 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_002` | `2.mov` | `2.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 32.49 | 30.20 | 2.29 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_003` | `3.mov` | `3.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 33.32 | 32.54 | 0.79 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_004` | `4.mov` | `4.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 75.59 | 78.07 | 2.49 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_005` | `5.mov` | `5.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 79.56 | 78.11 | 1.45 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_006` | `6.mov` | `6.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 126.19 | 126.98 | 0.79 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_007` | `7.mov` | `7.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 38.26 | 34.54 | 3.72 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_008` | `8.mov` | `8.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 58.88 | 62.72 | 3.84 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_009` | `9.mov` | `9.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 42.90 | 37.60 | 5.30 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_010` | `10.mov` | `10.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 7.17 | 7.80 | 0.63 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_011` | `11.mov` | `11.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 24.02 | 23.52 | 0.50 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_012` | `12.mov` | `12.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 37.69 | 37.37 | 0.32 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_013` | `13.mov` | `13.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 75.19 | 70.74 | 4.45 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_014` | `14.mov` | `14.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 73.69 | 73.24 | 0.45 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_015` | `15.mov` | `15.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 55.04 | 53.50 | 1.54 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_016` | `16.mov` | `16.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 31.16 | 22.23 | 8.92 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_017` | `17.mov` | `17.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 46.87 | 45.27 | 1.60 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_018` | `18.mov` | `18.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 81.66 | 83.77 | 2.12 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_019` | `19.mov` | `19.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 58.94 | 52.64 | 6.30 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_020` | `20.mov` | `20.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 60.31 | 51.13 | 9.18 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |
| `event_021` | `21.mov` | `21.mov` | 1920×1080 @ 29.97 | 1920×1080 @ 29.97 | 28.55 | 29.87 | 1.32 | Front (AAC 48k) + Back (AAC 48k) | Confirmed (100%) |

---

## 3. Dataset B: Standalone Train Horn Audio Dataset

### 3.1 Overview & Role
- **Source Directory**: `Train_Audio_new/`
- **Organized Target Directory**: `data/raw/audio/train_horn/positive/`
- **Dataset Role**: `audio_model_development`
- **Ground Truth Positive Label**: `train_horn`
- **Negative Background Directory**: `data/raw/audio/train_horn/negative/` (documented missing)
- **Total Physical Files in Source**: 87 files

### 3.2 Key Technical Findings & Anomalies
1. **Misnamed PDF Files (Extension Anomaly)**:
   - 4 files in `Train_Audio_new` (`43.pdf`, `44.pdf`, `45.pdf`, `46.pdf`) are genuine MPEG Layer III (MP3) audio files with valid ID3v2.4 headers and 44.1 kHz stereo audio streams.
   - Durations: `43.pdf` (2.91s), `44.pdf` (3.00s), `45.pdf` (4.00s), `46.pdf` (4.00s).
   - In accordance with the non-destructive research protocol, original files are preserved with their exact filenames in `data/raw/audio/train_horn/positive/`, and non-destructive symlinks (`43.mp3` → `43.pdf`, etc.) have been provided so standard audio libraries can load them seamlessly.
2. **Duplicate Audio Detection**:
   - Exactly **1 pair of duplicate files** was detected: `41.mp3` and `42.mp3` share the exact same SHA-256 hash (`17f81c16ee65f38e7d05089395e0005b8c75663f7b9470bec864274b76cf314a`) and size (79,484 bytes).
   - Both files are retained, but `42.mp3` is explicitly flagged in the manifest with `is_duplicate: true` and `duplicate_of: "41.mp3"`.
3. **Corrupted or Unreadable Files**:
   - **0 unreadable or corrupted files**. All 87 files were probed by `ffprobe` and validated.

### 3.3 Audio Technical Summary Table
| Metric | Value | Notes |
|---|---|---|
| **Total Audio Files** | 87 files (86 unique audio recordings) | 83 `.mp3`/`.MP3` + 4 misnamed `.pdf` |
| **Audio Format / Codec** | MPEG Audio Layer III (`mp3`) | 100% of files |
| **Sample Rate** | 44,100 Hz | Constant across 100% of files |
| **Channels** | 2 channels (Stereo) | 100% of files |
| **Bitrate Range** | 64 kbps to 136 kbps | Typical compressed web audio |
| **Min Duration** | 1.00 s (`22.MP3`) | Short blast |
| **Max Duration** | 12.00 s (`40.mp3`) | Sustained horn sequence |
| **Mean Duration** | 3.42 s | Standard horn blast duration |
| **Total Audio Runtime** | 297.69 s (~4.96 minutes) | Sufficient initial positive training pool |

### 3.4 Critical Prerequisite: Missing Negative Audio
> [!WARNING]
> **Negative / Background Audio is Currently Missing**:
> To train a reliable binary audio detector (`train_horn` vs `background`), a balanced negative set is strictly required. Training on positive samples alone or relying on pure synthetic Gaussian noise will cause catastrophic false-alarm rates during quiet crossing intervals.
> Negative recordings must include:
> - Road traffic (cars, trucks, motorcycles)
> - Ambient wind, rain, and environmental noise
> - Level-crossing bell chimes and warning signals
> - Pedestrian speech and distant industrial sounds

---

## 4. Strict Data Separation Rules

To prevent data contamination and preserve scientific integrity, the following rules are permanently binding:

1. **Dataset V1 Isolation**:
   - `data/raw/vision/v1/` remains the sole training/validation dataset for the YOLO vision model.
   - No frames from the 21 Layer B test videos may be added to Dataset V1 prior to unseen evaluation.
2. **Layer B Zero-Leakage Protocol**:
   - `data/raw/layer_b/videos/` is strictly reserved for `real_world_evaluation`.
   - Test videos must NOT be seen during YOLO feature training or hyperparameter tuning.
3. **Audio Domain Separation**:
   - `data/raw/audio/train_horn/positive/` is designated for `audio_model_development`.
   - Embedded audio from the 21 Layer B video recordings must NOT be extracted and mixed into audio classifier training before the final multimodal benchmark evaluation.
4. **Auditability**:
   - All machine-readable manifests (`layer_b_video_manifest.jsonl` and `train_horn_audio_manifest.jsonl`) maintain permanent cryptographic SHA-256 links to source media.
