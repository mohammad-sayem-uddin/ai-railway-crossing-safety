# Multimodal Railway Level-Crossing Safety Research Framework

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Status: Research Prototype](https://img.shields.io/badge/status-research--prototype-orange.svg)]()
[![Evaluation Status: Pre-Evaluation Audit](https://img.shields.io/badge/Layer%20B%20Evaluation-Pending%20Ground%20Truth-yellow.svg)]()

> **Research Prototype Notice & Safety Disclaimer:**
> This software is an academic research prototype and simulation framework developed for studying computer vision and audio evidence fusion at railway level-crossings in Bangladesh. It is **not** certified railway signaling or interlocking software and must **never** be connected to live railway infrastructure or used for physical railway gate actuation. All empirical claims are strictly limited to offline software replay on held-out recordings under defined protocol boundaries.

---

## 1. Project Overview

Level-crossings in Bangladesh and developing railway corridors face high accident frequencies due to manual gate operations, informal crossings, dense non-lane road traffic, and limited line-of-sight. This project investigates an automated, multi-sensor safety architecture designed to reliably detect approaching trains and train clearance while minimizing false closures and dangerous premature gate reopenings.

The core framework integrates:
* **Dual-Camera Synchronized Computer Vision:** Monitoring complementary crossing approaches (front and rear angles) to overcome occlusions by heavy road vehicles.
* **Acoustic Train Horn Detection:** An independent sensory modality using deep audio representations to provide early warning before the train enters camera sightlines and to retain presence evidence during severe optical obstructions.
* **Temporal Evidence Persistence:** Multi-frame confirmation windows and decay filters that eliminate transient detector flicker.
* **Conservative State-Machine Decision Engine:** A fail-safe finite state machine (FSM) enforcing conservative gate transitions: rapid closure upon verified approach evidence, strict multi-sensor hold intervals, and multi-frame clearance confirmation before gate ascent.
* **Simulated Crossing Gate Dynamics:** High-fidelity software modeling of physical gate warning times, descent speeds, locked states, and ascent delays.

---

## 2. Current Project Status

| Milestone / Component | Current Status | Description |
|---|---|---|
| **Perception Foundation** | **Completed** | YOLOv8n fine-tuned on train visual classes; Audio V3 CNN trained on train horns & ESC-50. |
| **Methodology Protocols** | **Frozen (v8.0.0 / v6.0.0)** | Authoritative specifications in [`docs/`](docs/): [`FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`](docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md), [`FINAL_GROUND_TRUTH_PROTOCOL.md`](docs/FINAL_GROUND_TRUTH_PROTOCOL.md), [`FINAL_EXPERIMENT_DATA_FLOW.md`](docs/FINAL_EXPERIMENT_DATA_FLOW.md), and [`FINAL_ABLATION_MATRIX.md`](docs/FINAL_ABLATION_MATRIX.md). |
| **Annotation Infrastructure** | **Operational** | Offline AI proposal tooling (`railway_detection.annotation`) with schema validation. |
| **Ground-Truth Calibration** | **In Review (`event_001`)** | Candidate proposals v1–v4 generated; researcher review sheet active. **Pending final human sign-off.** |
| **Real-World Layer B Evaluation** | **NOT AUTHORIZED** | Final batch replay across the Layer B evaluation cohort (27 events: 23 full-train, 3 no-train, 1 engine-only) is strictly locked out until ground truth is certified. |

---

## 3. System Architecture

```
                                  ┌───────────────────────────────┐
                                  │      Crossing Environment     │
                                  └───────────────┬───────────────┘
                                                  │
                 ┌────────────────────────────────┼────────────────────────────────┐
                 ▼                                ▼                                ▼
       ┌────────────────────┐           ┌────────────────────┐           ┌───────────────────┐
       │ Front Camera Stream│           │  Rear Camera Stream│           │ Audio Stream (MIC)│
       └─────────┬──────────┘           └─────────┬──────────┘           └─────────┬─────────┘
                 │                                │                                │
                 ▼                                ▼                                ▼
       ┌────────────────────┐           ┌────────────────────┐           ┌───────────────────┐
       │   YOLOv8n Vision   │           │   YOLOv8n Vision   │           │  Audio V3 CNN     │
       │  (Threshold: 0.35) │           │  (Threshold: 0.35) │           │ (Threshold: 0.37) │
       └─────────┬──────────┘           └─────────┬──────────┘           └─────────┬─────────┘
                 │                                │                                │
                 └────────────────┬───────────────┴────────────────────────────────┘
                                  ▼
                 ┌────────────────────────────────────────────────┐
                 │          Temporal Evidence Collector           │
                 │   - Multi-view visual bounding box fusion      │
                 │   - Acoustic horn persistence buffer           │
                 │   - Frame-window confirmation filters          │
                 └───────────────────────┬────────────────────────┘
                                         ▼
                 ┌────────────────────────────────────────────────┐
                 │       Conservative Safety State Machine        │
                 │   State: NO_TRAIN → APPROACHING → OCCUPYING    │
                 │          → CLEARING → HELD_CLOSED → SAFE       │
                 └───────────────────────┬────────────────────────┘
                                         ▼
                 ┌────────────────────────────────────────────────┐
                 │         Simulated Gate Actuation Model         │
                 │   - Pre-warning signal & siren delay           │
                 │   - Mechanical descent & locked hold           │
                 │   - Conservative ascent validation             │
                 └────────────────────────────────────────────────┘
```

### 3.1 Vision Model (YOLOv8n)
* **Architecture:** Ultralytics YOLOv8n single-class (`train`) detector.
* **Input Resolution:** 640×640 px.
* **Operating Threshold:** `0.35` (frozen in `configs/vision.yaml` and master protocol).
* **Role:** Detects locomotive front, rail cars, and rear caboose from both approaching and departing camera perspectives.

### 3.2 Audio Model (Audio V3 CNN)
* **Architecture:** 4-layer 2D convolutional neural network with log-mel spectrogram front-end (128 mel bands, 16 kHz mono sampling, 1.0 s window, 0.5 s hop).
* **Training Corpus:** Curated railway horn events mixed with the ESC-50 environmental acoustic dataset (50 non-target noise categories including traffic, weather, domestic sounds).
* **Operating Threshold:** `0.3700` (calibrated on held-out validation curve for high-precision horn onset).
* **Prohibited Model Notice:** An earlier legacy Audio V2 checkpoint (`59b0785f73b2...`) was identified during protocol auditing as exhibiting non-target acoustic leakage; its loading is cryptographically locked out in the pipeline.

### 3.3 Conservative State Engine
The state machine implements a strict safety bias:
1. **Low Ingress Latency:** Rapid transition from `NO_TRAIN` to `APPROACHING` / `OCCUPYING` when visual confidence exceeds threshold or horn acoustic evidence persists.
2. **Persistence Buffer:** Temporary visual dropouts (such as steam, dust, or partial occlusions behind road vehicles) do not trigger premature gate opening.
3. **Dual-Check Egress Confirmation:** Clearance is recognized only after both front and rear camera views confirm `T4` tail clearance followed by a configurable safety clearance buffer (minimum 3.0 s).

---

## 4. Repository Structure

```
Train_automation/
├── configs/                     # Versioned YAML configurations (vision, audio, fusion, sim)
├── data/
│   ├── ground_truth/            # Ground-truth proposal lifecycle and certified annotations
│   │   └── proposals/           # Stage 1 AI proposals (v1-v4) and review sheets
│   ├── metadata/                # Dataset sample metadata and split definitions
│   └── raw/                     # [Local Only] Raw multi-gigabyte recordings
│       ├── layer_b/v2/          # Real-world paired recordings (23 train_events, 3 no_train_events, 1 engine_event)
│       └── audio/, vision/      # Raw perception training datasets (train_horn/, esc50/, baler.v1i.yolov8/)
├── docs/                        # Research documentation and protocols (Source of Truth)
│   ├── FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md # Master Evaluation Protocol (v8.0.0)
│   ├── FINAL_GROUND_TRUTH_PROTOCOL.md          # Ground-Truth Annotation Protocol (v6.0.0)
│   ├── FINAL_EXPERIMENT_DATA_FLOW.md           # Evaluation Data Flow Architecture (v5.1.0)
│   ├── FINAL_ABLATION_MATRIX.md                # Fair Single-Factor Ablation Plan (v5.1.0)
│   ├── AUDIO_MODEL_V3_ESC50_REPORT.md          # Audio V3 CNN model & ESC-50 training report
│   ├── HAZARD_MODEL.md                         # Formal hazard taxonomy and safety invariants
│   ├── RESEARCH_DECISIONS.md                   # Chronological research decisions log
│   ├── REPOSITORY_CLEANUP_AUDIT.md             # Storage and integrity audit log
│   └── archive/                                # Preserved historical protocols & legacy plans
├── experiments/                 # Reproducibility records, manifests, and checkpoints
│   ├── vision/39f402dfe460/     # YOLOv8n frozen weights and training run manifest
│   └── audio/RUN_20261008.../   # Audio V3 CNN frozen weights and evaluation curves
├── models/                      # Model directories and legacy quarantine
├── outputs/                     # Temporary runtime exports (git-ignored)
├── research/                    # Analytical figures, qualitative plots, and helper scripts
├── results/                     # Dataset validation manifests and failure analysis logs
├── scratch/                     # [Local Only] Active inspection frames and audio extracts
├── src/railway_detection/       # Core package source code
│   ├── annotation/              # AI-assisted ground-truth proposal & review engine
│   ├── audio/                   # Feature extraction, audio loader, and inference
│   ├── cli/                     # Command-line interface definitions
│   ├── config/                  # Strict YAML configuration parsers and validators
│   ├── data/                    # Dataset validation, integrity hashing, group splitter
│   ├── evaluation/              # Event-level evaluation metrics and reporting
│   ├── fusion/                  # Multi-sensor temporal evidence collectors
│   ├── simulation/              # FSM decision engine and gate dynamics model
│   └── vision/                  # YOLOv8n inference adapter and multi-camera handlers
├── tests/                       # Unit, integration, and smoke test suites
├── .env.example                 # Sanitized template for environment variables
├── pyproject.toml               # Package build specifications and dependencies
└── README.md                    # Primary repository overview (this document)
```

### 4.1 Authoritative Research Documentation

The `docs/` directory is organized into active, governing methodology documents and a historical archive:

| Document | Version / Role | Scope & Summary |
|---|---|---|
| [`FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`](docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md) | **v8.0.0 (Master)** | Governing master protocol for real-world evaluation, dual-camera roles, performance metrics, and strict safety constraints. |
| [`FINAL_GROUND_TRUTH_PROTOCOL.md`](docs/FINAL_GROUND_TRUTH_PROTOCOL.md) | **v6.0.0 (Ground Truth)** | Ground-truth annotation protocol defining physical boundary events ($T_0$ to $T_4$), locomotive clearance ($T_3$), tail clearance ($T_4$), and horn windows. |
| [`FINAL_EXPERIMENT_DATA_FLOW.md`](docs/FINAL_EXPERIMENT_DATA_FLOW.md) | **v5.1.0 (Data Flow)** | Multi-stage streaming data pipeline from raw video/audio ingestion to perception, temporal fusion, state engine, and evaluation. |
| [`FINAL_ABLATION_MATRIX.md`](docs/FINAL_ABLATION_MATRIX.md) | **v5.1.0 (Ablations)** | Single-factor ablation plan evaluating visual-only, acoustic-only, fused modalities, and temporal window parameters. |
| [`AUDIO_MODEL_V3_ESC50_REPORT.md`](docs/AUDIO_MODEL_V3_ESC50_REPORT.md) | **Diagnostic Report** | Pretraining and evaluation report for the frozen Audio V3 CNN model trained on curated horn audio and ESC-50 negative sounds. |
| [`HAZARD_MODEL.md`](docs/HAZARD_MODEL.md) | **Safety Policy** | Formal hazard definitions, failure classifications (Type I/II/III), and conservative gate state invariants. |
| [`RESEARCH_DECISIONS.md`](docs/RESEARCH_DECISIONS.md) | **Decisions Log** | Chronological record of architectural decisions (D-001 through D-010), design trade-offs, and protocol governance. |
| [`REPOSITORY_CLEANUP_AUDIT.md`](docs/REPOSITORY_CLEANUP_AUDIT.md) | **Audit Baseline** | Pre-publication storage audit, disk footprint measurements, file deduplication, and repository hygiene verification. |
| [`docs/archive/`](docs/archive/) | **Historical Archive** | Preserved preliminary roadmaps, legacy protocols (V1/V2), deprecated dataset inventories, and execution checklists. See [`docs/archive/README.md`](docs/archive/README.md). |

---

## 5. Installation & Environment Setup

Supported Python Version: **Python 3.11 or newer** (tested on Python 3.11.15).

```bash
# 1. Clone repository
git clone https://github.com/mohammad-sayem-uddin/ai-railway-crossing-safety.git
cd ai-railway-crossing-safety

# 2. Create and activate a clean virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Upgrade pip and build tools
pip install --upgrade pip setuptools wheel

# 4. Install package in editable mode with development dependencies
pip install -e ".[dev]"
```

### Core Dependencies
* **Core & Configuration:** `PyYAML`, `pydantic` (>=2.0), `pillow`
* **Deep Learning & Computer Vision:** `torch`, `torchvision`, `torchaudio`, `ultralytics`
* **Signal Processing & Analysis:** `numpy`, `scipy`, `matplotlib`
* **AI-Assisted Annotation:** `google-genai` (or compatible Gemini API client)
* **Testing & Linting:** `pytest`, `ruff`, `mypy`

---

## 6. Configuration & Environment Variables

Copy the provided sanitized template to configure your local environment:

```bash
cp .env.example .env
```

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `GEMINI_API_KEY` | Optional | *None* | Used exclusively for Stage 1 offline annotation drafting. Never committed to Git. |
| `GEMINI_MODEL` | Optional | `gemini-2.5-pro` | Model endpoint for multi-modal frame and audio boundary drafting. |
| `LOG_LEVEL` | Optional | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## 7. AI-Assisted Ground-Truth Annotation Workflow

To eliminate manual annotation bottlenecks while strictly preserving research validity, ground truth is created using a three-stage verified lifecycle governed by [`docs/FINAL_GROUND_TRUTH_PROTOCOL.md`](docs/FINAL_GROUND_TRUTH_PROTOCOL.md):

```
┌─────────────────────────────────┐
│ Stage 1: AI Proposal Generation │
│ - Gemini Multimodal Assistant   │
│ - Ingests native video + audio  │
│ - Emits structured proposal JSON│
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ Stage 2: Human Adjudication     │
│ - Researcher inspects frames/WAV│
│ - Reviews review_sheet.md       │
│ - Corrects boundary timestamps  │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ Stage 3: Certified Ground Truth │
│ - Cryptographic SHA-256 sealing │
│ - Read-only manifest generation │
│ - Prerequisite for evaluation   │
└─────────────────────────────────┘
```

### 7.1 Key Boundary Definitions
* **`T0` (First Observed Visual Presence):** Timestamp of the earliest video frame in which any part of the train becomes visible.
* **`T1` (Danger Zone Entry):** Front of the locomotive crosses the physical crossing boundary.
* **`T2` (Roadway Obstruction Onset):** Train begins physically blocking road vehicle movement.
* **`T3` (Locomotive Unit Clearance):** Trailing edge of the leading locomotive unit completely clears the danger zone (trailing freight/passenger cars may still occupy the crossing).
* **`T4` (Complete Train Clearance):** Trailing coupler of the final rail vehicle exits the crossing boundary.
* **Horn Windows:** Exact start/end timestamps and confidence of acoustic horn blasts.

---

## 8. Cryptographic Reproducibility Register

Every model weight file in this repository is cryptographically tracked to guarantee scientific reproducibility:

| Asset Name | Canonical Relative Path | Verified SHA-256 Hex Digest | Policy |
|---|---|---|---|
| **YOLOv8n Train Detector** | `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` | `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` | **Frozen (Threshold 0.35)** |
| **Audio V3 CNN Classifier** | `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt` | `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782` | **Frozen (Threshold 0.3700)** |
| **Legacy Audio V2 (Prohibited)** | `models/audio/best_checkpoint.pt` | `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5` | **Prohibited from Inference** |

---

## 9. Testing & Quality Verification

Run the verified test suites to validate software integrity:

```bash
# Run annotation workflow unit tests
PYTHONPATH=src pytest -c /dev/null -p no:cacheprovider tests/test_annotation_workflow.py

# Check Gemini annotation environment
python -m railway_detection.annotation.cli --check-env

# Generate AI proposal draft for a specific event
python -m railway_detection.annotation.cli --event-id event_001 --event-type train_events

# Run static linting checks
ruff check src tests

# Run type consistency checks
mypy src
```

> **Testing vs. Evaluation Distinction:**
> Running `pytest` validates software contracts, schema parsing, and decision logic on mock fixtures. It does **not** execute the real-world Layer B evaluation on actual video recordings. Real-world evaluation replay is restricted until ground truth is signed off by the researcher.

---

## 10. Local Dataset Reproduction Setup

Due to privacy, copyright, and storage constraints, multi-gigabyte raw media files are not hosted in the Git repository. Researchers replicating this study should place source files into the following directory tree:

```
data/
└── raw/
    ├── layer_b/
    │   └── v2/
    │       ├── train_events/
    │       │   ├── event_001/
    │       │   │   ├── camera_front.mov    # Front crossing view (resolutions vary by event, e.g. 1080p / 4K)
    │       │   │   ├── camera_back.mov     # Rear/Back view (e.g. event_001 is native 3840×2160 portrait display)
    │       │   │   └── camera_rear.mov     # Symlink -> camera_back.mov
    │       │   ├── event_002/
    │       │   └── ... (event_001 through event_023; 23 full-train events)
    │       ├── engine_events/
    │       │   ├── event_001/              # Single locomotive passage without railcars (1 engine event)
    │       │   │   ├── camera_front.mov
    │       │   │   ├── camera_back.mov
    │       │   │   └── camera_rear.mov
    │       │   └── event_historical_duplicate_010/ # Preserved historical duplicate (excluded from evaluation cohort)
    │       └── no_train_events/
    │           ├── event_001/              # Baseline negative exposure without train presence
    │           │   ├── camera_front.mov
    │           │   ├── camera_back.mov
    │           │   └── camera_rear.mov
    │           ├── event_002/
    │           └── event_003/              # 3 no-train events total
    ├── vision/
    │   └── v1/
    │       └── baler.v1i.yolov8/           # YOLOv8 format: images/ and labels/
    └── audio/
        ├── train_horn/                     # Positive and negative railway horn WAVs
        └── external/
            └── esc50/                      # ESC-50 environmental acoustic dataset
```

External audio training data can alternatively reside at `ESC-50-master/` in the project root if reproducing the Audio V3 CNN transfer learning pipeline.

---

## 11. Scientific Scope & Research Limitations

1. **Varying Optical Resolutions & Display Orientations:** Source recordings were captured in natural field settings using diverse consumer mobile recording hardware. Native stream resolutions vary across events, encompassing 1080p Full HD (1920×1080) and 4K UHD (3840×2160) streams with differing landscape/portrait display metadata (e.g., `event_001` back camera has a native coded raster of 3840×2160 with portrait display orientation). Downstream inference adapters normalize resolution scaling and aspect ratios.
2. **Uncalibrated Optical Geometry:** Real-world recordings were collected in natural field settings without metric camera calibration or LiDAR ground truth. Visual danger zone boundaries represent image-space coordinate thresholds.
3. **Inter-Camera Clock Skew:** Front and rear camera streams were recorded on independent consumer devices. Synchronization offsets are estimated via audio-visual alignment markers and carry residual uncertainty.
4. **Limited Crossing Locations:** Field recordings originate from a limited number of level-crossing locations in Bangladesh; cross-site domain generalization across diverse weather conditions (e.g., monsoon rain, fog) requires further validation.
5. **No-Train Negative Exposure:** The real-world test split contains bounded baseline no-train recording durations; false-alarm rates over extended multi-hour continuous monitoring cannot be extrapolated from short clips alone.
6. **Software Simulation Only:** No physical PLC controllers, relay interlocks, or hardware actuator circuits were deployed in live railway corridors.

---

## 12. License & Attribution

* **Software Codebase:** Copyright (c) 2026 Mohammad Sayem Uddin et al. Developed as part of academic research on railway level-crossing safety.
* **YOLOv8 Weights:** Pretrained vision backbones provided by [Ultralytics](https://github.com/ultralytics/ultralytics) under AGPL-3.0 / Enterprise licensing.
* **ESC-50 Dataset:** Acoustic background samples sourced from the ESC-50 Environmental Sound Classification dataset by Karol J. Piczak, distributed under the Creative Commons Attribution-NonCommercial 3.0 license.
