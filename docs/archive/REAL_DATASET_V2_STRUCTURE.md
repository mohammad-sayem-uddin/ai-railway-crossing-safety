# Real-World Dataset V2 Directory Specification & Architecture

**Project**: AI Railway Level-Crossing Safety Research  
**Document Version**: 2.0.0  
**Specification Date**: October 8, 2026  
**Status**: ACTIVE PRODUCTION SPECIFICATION

---

## 1. Directory Tree

```
data/
├── raw/
│   ├── vision/
│   │   └── v1/
│   │       └── baler.v1i.yolov8/            # FROZEN YOLOv8n Training/Validation Data
│   │
│   ├── layer_b/
│   │   └── v2/                              # UNSEEN MULTIMODAL EVALUATION DATASET
│   │       ├── train_events/                # Full train passage events
│   │       │   ├── event_001/
│   │       │   │   ├── camera_front.mov
│   │       │   │   ├── camera_back.mov
│   │       │   │   └── camera_rear.mov -> camera_back.mov
│   │       │   ├── ...
│   │       │   └── event_023/
│   │       │
│   │       ├── engine_events/               # Engine-only train passages
│   │       │   ├── event_001/               # NEW engine-only event (ELIGIBLE)
│   │       │   │   ├── camera_front.mov
│   │       │   │   ├── camera_back.mov
│   │       │   │   └── camera_rear.mov -> camera_back.mov
│   │       │   └── event_historical_duplicate_010/ # Old Event 010 (EXCLUDED)
│   │       │       ├── camera_front.mov
│   │       │       ├── camera_back.mov
│   │       │       └── camera_rear.mov -> camera_back.mov
│   │       │
│   │       └── no_train_events/             # Negative baseline crossing sessions
│   │           ├── event_001/
│   │           │   ├── camera_front.mov
│   │           │   ├── camera_back.mov
│   │           │   └── camera_rear.mov -> camera_back.mov
│   │           ├── event_002/
│   │           └── event_003/
│   │
│   └── audio/
│       └── train_horn/                      # STANDALONE AUDIO MODEL DEVELOPMENT
│           ├── positive/                    # 87 files (86 unique locomotive horn recordings)
│           └── negative/                    # 97 files (95 unique background recordings)
│
├── manifests/
│   ├── real_world_v2_video_manifest.json    # Machine-readable video manifest
│   ├── real_world_v2_video_manifest.jsonl
│   ├── audio_training_v2_manifest.json      # Machine-readable raw audio manifest
│   ├── audio_training_v2_manifest.jsonl
│   └── audio_training_v2_selection.json     # Balanced 86/86 audio selection manifest
│
└── processed/
    ├── audio/
    │   └── v2/                              # Standardized 16kHz WAVs and Log-Mel features
    └── layer_b/
```

---

## 2. Ingestion & Loading Protocol

1. **Layer B Loader Compatibility**:
   - The event bundle loader `src/railway_detection/data/layer_b.py` seamlessly supports `camera_front.mov` and `camera_back.mov` (with `camera_rear.mov` symlink provided).
   - Audio extraction from evaluation videos is strictly disabled during audio model training.
2. **Metadata Contract**:
   - Manifest files `data/manifests/real_world_v2_video_manifest.json` specify `evaluation_eligible: true` for real-world benchmark evaluations, and `evaluation_eligible: false` for `event_historical_duplicate_010`.
