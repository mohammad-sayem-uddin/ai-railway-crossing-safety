# Pre-Real-Data Completion Checklist

**Document Version:** 1.0.0  
**Date:** 2026-09-21  
**Author:** Senior Research Software Architect & Methodology Reviewer  
**Status:** ARCHITECTURAL & METHODOLOGICAL AUDIT COMPLETED  
**Scope:** Engineering review of existing codebase and prerequisite checklist before ingesting 25 real-world Layer B train-passage events (50 videos) and 100 real train-audio recordings.

---

## Executive Architectural Summary

This document establishes the formal engineering and methodological audit of the **AI Railway Level-Crossing Safety Research Project**. The research objective is to develop and evaluate a multi-view computer vision, acoustic detection, temporal evidence, and conservative state-machine decision architecture for railway level crossings in Bangladesh.

The repository currently contains **117 passing unit/smoke/integration tests** and a functioning **Development Perception Baseline (YOLOv8n)** trained on Dataset V1 (100 epochs, Apple Silicon MPS). However, because Dataset V1 utilized a `development_fallback` split (`split_id: 705d388743ea`) due to unavailable crossing/session metadata, the perception baseline metrics ($\text{mAP@50} \approx 0.9946$, $\text{mAP@50:95} \approx 0.8550$, $\text{Precision} \approx 0.9843$, $\text{Recall} \approx 0.9700$) **must strictly not be interpreted as crossing-independent generalization or field safety validation**.

Furthermore, while video inference, temporal evidence filtering, audio preprocessing, and basic Layer B loader structures exist, the **state machine, gate simulation, multimodal decision engine, audio classification model, and system-level evaluation harness remain unimplemented or stubbed**. Ingesting real data today would result in immediate pipeline crashes or an inability to execute end-to-end evaluation.

---

## 1. Current Architecture Status

The repository components were inspected against `docs/EXECUTION_PLAN.md`, `docs/RESEARCH_PROTOCOL_V2.md`, `docs/EXPERIMENT_PROTOCOL_V2.md`, and the actual source tree under `src/railway_detection/`.

| Subsystem | Status | Responsible Files / Modules | Audit Findings & Current Limitations |
|---|---|---|---|
| **Dataset Ingestion (Layer A)** | **COMPLETE** | `src/railway_detection/data/validator.py`<br>`src/railway_detection/data/split.py`<br>`src/railway_detection/data/manifest.py`<br>`src/railway_detection/data/contracts.py` | Full validation, bounding box checks ($0 \le x,y \le 1$), label mapping (`0: front`, `1: rear`, `2: side`), SHA-256 deduplication, and group-aware splitting with `--allow-ungrouped` fallback. |
| **Dataset Ingestion (Layer B)** | **PARTIALLY COMPLETE** | `src/railway_detection/data/layer_b.py`<br>`src/railway_detection/data/contracts.py` | `load_event_bundle()` exists but hardcodes expectations for `camera_1.mp4`, `camera_2.mp4`, and `audio.wav`. It errors if `metadata.json` is missing and cannot automatically ingest `camera_front.mp4` / `camera_rear.mp4` or extract embedded audio from video containers. |
| **Vision Model & Training** | **COMPLETE** | `src/railway_detection/vision/adapter.py`<br>`src/railway_detection/vision/yolo_adapter.py`<br>`src/railway_detection/vision/trainer.py` | Abstract `VisionDetectorBackend` protocol and `UltralyticsYOLOAdapter` implemented. Successfully trained YOLOv8n baseline for 100 epochs (`experiments/vision/39f402dfe460/checkpoints/weights/best.pt`). |
| **Vision Evaluation & Diagnostics** | **COMPLETE** | `src/railway_detection/vision/evaluator.py`<br>`src/railway_detection/vision/failure_analysis.py` | Computes mAP@50, mAP@50:95, per-class PR curves, confusion matrix, optimal F1 thresholds, and error slices (`missed_front`, `front_side_confusion`, etc.). Generated figures saved in experiment directories. |
| **Vision Video Inference** | **COMPLETE** | `src/railway_detection/vision/video.py`<br>`src/railway_detection/demo/video_demo.py`<br>`scripts/demo_video.py`<br>`demo_video.py` | Frame generator with stride/target FPS; standalone full-video inference CLI tool with OpenCV annotation, BGR class coloring, temporal smoothing integration, and markdown/JSON statistics output. |
| **Temporal Evidence Layer** | **COMPLETE** | `src/railway_detection/vision/temporal.py` | `TemporalEvidenceBuffer` implements consecutive-frame confirmation ($N$ frames / window $W$), exponential moving average confidence smoothing, persistence decay, loss tolerance, timestamp monotonicity checking, and timeout expiry. |
| **Audio Preprocessing & SNR** | **PARTIALLY COMPLETE** | `src/railway_detection/audio/preprocessor.py`<br>`src/railway_detection/audio/noise_mixer.py` | WAV loading, 16 kHz mono standardization, sliding analysis windowing, and precise synthetic SNR noise mixing are implemented and unit tested. |
| **Audio Classifier & Features** | **MISSING** | `src/railway_detection/audio/features.py`<br>`src/railway_detection/audio/model.py`<br>`src/railway_detection/audio/pipeline.py` | Mel-spectrogram/MFCC feature extractors, train-horn classifier protocol, baseline classifier (CNN/spectral), and acoustic inference pipeline emitting `EvidenceRecord` do not exist. |
| **Multimodal Evidence Interface** | **PARTIALLY COMPLETE** | `src/railway_detection/fusion/evidence.py` | Data contracts (`Modality`, `Detection`, `EvidenceRecord`, `DecisionRecord`, `UnavailableSource`) are defined and frozen. However, `fusion/collector.py` and `fusion/source_tracker.py` are **MISSING**. |
| **Multimodal Decision Engine** | **MISSING** | `src/railway_detection/fusion/rules.py`<br>`src/railway_detection/fusion/decision_engine.py` | Declarative safety rules (R-APPROACH, R-OCCUPANCY, R-DEPARTURE, R-CLEARANCE, R-GUARD-OPENING) and the deterministic decision engine with explainability traces are completely unwritten. |
| **Two-Camera Stream Processing** | **PARTIALLY COMPLETE** | `src/railway_detection/vision/video.py`<br>`src/railway_detection/vision/temporal.py` | Video frame generator tags `source_id` and temporal buffer tracks evidence per source. However, concurrent two-camera frame reading, collation, and inter-camera handoff logic do not exist. |
| **Two-Camera Synchronization** | **PARTIALLY COMPLETE** | `src/railway_detection/data/sync.py` | `SyncAligner` applies static `offset_s` and verifies `uncertainty_s <= tolerance_s`. Automated offset estimation (via audio cross-correlation or visual event cue) is unwritten. |
| **State Machine & Gate Controller** | **MISSING** | `src/railway_detection/simulation/state_machine.py`<br>`src/railway_detection/simulation/gate_model.py`<br>`src/railway_detection/simulation/runner.py` | `src/railway_detection/simulation/__init__.py` contains only `NotSupportedInPhase0`. The formal crossing state machine, simulated gate dynamics, and scenario runner do not exist. |
| **Failure Injection Engine** | **MISSING** | `src/railway_detection/simulation/failure_injector.py` | Phase 10 failure injection harness (simulating camera dropouts, missed front, stale timestamps, false rear, conflicting streams) has not been implemented. |
| **Real-Event Evaluation Framework** | **MISSING** | `src/railway_detection/evaluation/metrics.py`<br>`src/railway_detection/evaluation/runner.py` | `src/railway_detection/evaluation/__init__.py` is empty (54 bytes). System-level event metrics (event-level missed-train rate, premature-opening rate, warning lead time) are not implemented. |
| **Research Artifact Generation** | **PARTIALLY COMPLETE** | `scripts/build_research_report_doc.py`<br>`scripts/generate_report_figures.py`<br>`src/railway_detection/vision/evaluator.py` | Layer A vision figures and documentation report generator exist. Automated B0–B7 system comparative tables and state transition timelines are missing. |
| **CLI Dispatcher** | **PARTIALLY COMPLETE** | `src/railway_detection/cli/main.py` | Supports `data validate`, `data split`, `vision train`. Subcommands for `vision evaluate`, `vision infer`, `audio`, `simulate`, `experiment`, and `report` abort with `Not implemented in Phase 0`. |
| **Configuration Management** | **COMPLETE** | `src/railway_detection/config/loader.py`<br>`configs/vision.yaml`<br>`configs/audio.yaml`<br>`configs/fusion.yaml`<br>`configs/simulation.yaml` | Strictly validated configuration classes (`VisionConfig`, `AudioConfig`, `FusionConfig`, `SimulationConfig`) with schema checking and path resolution. |
| **Logging & Reproducibility** | **COMPLETE** | `src/railway_detection/utils/logging.py`<br>`src/railway_detection/utils/reproducibility.py` | Structured logging, immutable run manifests (`run_manifest.json`), and append-only experiment registry (`results/experiment_registry.jsonl`). |
| **Test Suite** | **COMPLETE (117 Tests)** | `tests/unit/*`<br>`tests/integration/*`<br>`tests/smoke/*` | 117 unit, smoke, and mock integration tests covering all completed components. *(Note: Environment bug identified where iCloud Drive offloads `.venv` files with `dataless` flag, causing `Errno 89` on un-cached Python modules).* |

---

## 2. What Can Already Be Tested

The repository currently allows testing of individual perception, data processing, and visual inference components. It is critical to distinguish between **verified mock/unit testing** and **real-world system evaluation**.

### A. Unit Tests (Passing)
All 18 unit test suites can be executed (provided Python environment packages are locally resident on disk):
```bash
# Core schemas and configuration
.venv/bin/pytest tests/unit/test_contracts.py
.venv/bin/pytest tests/unit/test_config.py

# Dataset ingestion and splitting
.venv/bin/pytest tests/unit/test_validator.py
.venv/bin/pytest tests/unit/test_manifest.py
.venv/bin/pytest tests/unit/test_split.py

# Vision adapters, video readers, and evaluators
.venv/bin/pytest tests/unit/test_vision_adapter.py
.venv/bin/pytest tests/unit/test_yolo_adapter.py
.venv/bin/pytest tests/unit/test_video_reader.py
.venv/bin/pytest tests/unit/test_temporal_evidence.py
.venv/bin/pytest tests/unit/test_vision_evaluator.py
.venv/bin/pytest tests/unit/test_failure_analysis.py
.venv/bin/pytest tests/unit/test_video_demo.py

# Audio preprocessor and Layer B loader
.venv/bin/pytest tests/unit/test_audio_preprocessor.py
.venv/bin/pytest tests/unit/test_layer_b_loader.py

# Web UI and CLI
.venv/bin/pytest tests/unit/test_cli.py
.venv/bin/pytest tests/unit/test_dashboard_server.py
.venv/bin/pytest tests/unit/test_research_scripts.py
```

### B. Synthetic / Mock Integration Tests
```bash
# Phase 0 foundation verification
.venv/bin/pytest tests/integration/test_phase0_smoke.py

# Mock vision training loop (validates pipeline without GPU execution)
.venv/bin/pytest tests/integration/test_vision_train_mock.py

# CLI dispatch smoke test
.venv/bin/pytest tests/smoke/test_cli_smoke.py
```

### C. Vision Model & Perception Tests (Layer A)
Using the existing trained checkpoint `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`:
- Evaluated on held-out V1 test partition (`split_id: 705d388743ea`).
- Metrics generated and verified:
  - mAP@50: **0.9946**
  - mAP@50:95: **0.8550**
  - Precision: Front 0.9843, Rear 1.0000, Side 0.9565
  - Recall: Front 0.9472, Rear 1.0000, Side 0.9851
  - Artifacts: `experiments/vision/39f402dfe460/evaluation/pr_curves.png`, `confusion_matrix.png`, `failure_analysis.json`.

### D. Video Inference & Demonstration (Standalone)
Inference can be run immediately on arbitrary MP4/MOV test videos (e.g., recorded test footage in `Unseen_Video/`):
```bash
# Run YOLOv8n inference on sample video with Apple Silicon MPS acceleration
python demo_video.py --input "Unseen_Video/Screen Recording 2026-08-18 at 17.01.28.mov" --device mps --temporal

# Launch interactive web UI for inspecting video runs and metric reports
python dashboard.py
```

### E. Temporal Evidence Tests
`tests/unit/test_temporal_evidence.py` verifies:
- Single-frame spike rejection ($N=3$ consecutive confirmation requirement).
- Temporal smoothing of detection bounding boxes and confidence scores.
- Bridging 1–2 frame detection dropouts via persistence scoring.
- Expiration of evidence after timeout ($\tau_{\text{expiry}}$).
- Rejection of out-of-order timestamps.

### F. Audio Preprocessing Tests
`tests/unit/test_audio_preprocessor.py` verifies:
- Resampling arbitrary sample rates to 16,000 Hz mono.
- Sliding analysis window generation with 50% overlap.
- Zero-distortion SNR mixing under traffic/rain noise profiles.

### G. What CANNOT Be Tested Yet (Missing Subsystems)
- **Multimodal Fusion:** Cannot run because `fusion/collector.py` and `fusion/decision_engine.py` do not exist.
- **Crossing State Machine:** Cannot run because `simulation/state_machine.py` and `simulation/gate_model.py` do not exist.
- **Two-Camera Concurrent Processing:** Cannot replay paired front/rear streams into a unified state timeline.
- **System Safety Endpoints:** Cannot compute event-level missed-train rate or premature opening rate.

---

## 3. What MUST Be Finished Before Real Data Arrival

To ensure the architecture is "plug-and-test" when the 25 paired events (50 videos) and 100 audio files arrive, the following engineering tasks must be executed.

### Prioritized Checklist

```text
[P0] = ABSOLUTELY REQUIRED (Blocker for data ingestion or safety-critical execution)
[P1] = STRONGLY RECOMMENDED (Required for reproducible comparative baselines B0–B7)
[P2] = USEFUL BUT CAN WAIT (UI polish, publication artifact automation)
```

| Priority | Requirement | Current Status | Target File(s) | Architectural Necessity & Rationale | Acceptance Criteria (Definition of Done) | Required Verification Tests |
|:---:|---|---|---|---|---|---|
| **P0** | **Flexible Layer B Data Ingestion & Media Resolver** | Hardcoded to `camera_1.mp4`, `camera_2.mp4`, and `audio.wav`. Errors on missing metadata. | `src/railway_detection/data/layer_b.py`<br>`src/railway_detection/data/contracts.py` | Real data contains `camera_front.mp4` and `camera_rear.mp4`, with audio embedded in MP4 and no pre-existing `metadata.json`. Must load without crash. | 1. Ingests `camera_front.mp4` and `camera_rear.mp4` transparently.<br>2. Automatically extracts 16 kHz mono WAV from MP4 if standalone audio is absent.<br>3. Ingests folders without `metadata.json` or `geometry.json`, populating sensible defaults (`direction="unknown"`, `sync_offset=0.0`). | Unit test suite loading bare event folders with embedded audio only. |
| **P0** | **Multimodal Decision Engine & Explainability Trace** | MISSING (Only data structures exist). | `src/railway_detection/fusion/rules.py`<br>`src/railway_detection/fusion/decision_engine.py` | Core research engine. Must evaluate safety rules and output deterministic `DecisionRecord` with full audit trace. | 1. Implements rules R-APPROACH, R-OCCUPANCY, R-DEPARTURE, R-CLEARANCE, R-GUARD-OPENING.<br>2. Strictly blocks opening on missing evidence or audio alone.<br>3. Emits explainability string and rule ID for every decision. | Unit tests covering all rule predicates, priority conflict resolution, and invariant guards. |
| **P0** | **Crossing State Machine & Simulated Gate Model** | MISSING (Placeholder in Phase 0). | `src/railway_detection/simulation/state_machine.py`<br>`src/railway_detection/simulation/gate_model.py`<br>`src/railway_detection/simulation/runner.py` | State machine models safety policy (`IDLE` $\to$ `APPROACHING` $\to$ `WARNING` $\to$ `CLOSING` $\to$ `PRESENT` $\to$ `DEPARTING` $\to$ `REAR_CONFIRMED` $\to$ `CLEAR` $\to$ `OPENING`). | 1. Deterministic transitions adhering to `HAZARD_MODEL.md`.<br>2. Simulated gate travel times and safety dwell timers.<br>3. Enforces transition invariants (e.g., direct `TRAIN_PRESENT` $\to$ `IDLE` raises error). | Unit tests testing 100% of state transitions, prohibited transitions, and simulated gate angle dynamics. |
| **P0** | **Acoustic Classifier Interface & Baseline Model** | Preprocessor exists; classifier and feature extraction missing. | `src/railway_detection/audio/features.py`<br>`src/railway_detection/audio/model.py`<br>`src/railway_detection/audio/pipeline.py` | Required to utilize the 100 audio files as supporting acoustic evidence for approach confirmation. | 1. Mel-spectrogram feature extractor.<br>2. Modular `AudioClassifier` interface.<br>3. Emits `EvidenceRecord` with $P(\text{train\_horn}) \in [0, 1]$.<br>4. Hard guard: audio never triggers opening. | Unit tests for feature tensor dimensions, classifier inference, and probability calibration. |
| **P0** | **Two-Camera Stream Synchronizer & Alignment Engine** | Basic offset addition exists; stream collation missing. | `src/railway_detection/data/sync.py`<br>`src/railway_detection/fusion/collector.py` | Consumer phone videos have imperfect sync. Must normalize master timeline and handle stream lag. | 1. Interleaves frames from Camera 1 and Camera 2 by master timestamp.<br>2. Tolerates clock offsets ($\Delta t$) and drift.<br>3. Flags high-uncertainty intervals without crashing. | Integration test collating two asynchronous video streams into a chronological evidence buffer. |
| **P0** | **Event-Level Ground Truth Protocol & Ingestion** | Protocol written in markdown; parser missing. | `src/railway_detection/data/layer_b.py`<br>`src/railway_detection/data/contracts.py` | Real events require independent reference labeling of entry, exit, and tail clearance. | 1. Parses `labels/event_labels.json`.<br>2. Supports status `observed`, `estimated`, `unobservable`.<br>3. Treats `rear` detection as model evidence, NEVER ground truth. | Unit test verifying label parsing, missing label handling, and clearance unobservable flags. |
| **P1** | **Deterministic Failure Injection Engine** | MISSING. | `src/railway_detection/simulation/failure_injector.py` | Required for evaluating resilience under adverse and degraded conditions (Baselines B7). | 1. Deterministically drops Camera 1, Camera 2, or Audio.<br>2. Injects stale timestamps, out-of-order frames, false rear spikes.<br>3. Injects new train approaching during gate opening. | Unit tests verifying reproducible fault injection and conservative system reaction. |
| **P1** | **B0–B7 Baseline Experiment Runner** | MISSING. | `src/railway_detection/experiments/runner.py` | Automated comparison across B0 (Single-Cam), B1 (Temporal), B2 (Two-Cam), B3 (+State), B4 (Audio), B5 (Naive Fusion), B6 (Full Proposed). | 1. Replays identical held-out events through all 8 configurations.<br>2. Saves structured run logs to `experiments/system/<run_id>/`.<br>3. Appends summary to `experiment_registry.jsonl`. | Integration test running B0–B6 on synthetic mock event fixture. |
| **P1** | **Event-Level Evaluation Metrics Calculator** | MISSING (Only Layer A mAP evaluator exists). | `src/railway_detection/evaluation/metrics.py` | Primary research endpoints are event-level missed-train rate and premature-opening rate. | 1. Computes Missed-Train Rate with 95% Wilson CI.<br>2. Computes Premature-Opening Rate on evaluable clearance events.<br>3. Computes Warning Lead Time distribution and Late Closure Rate. | Unit test against pre-defined ground truth scenarios with intentional simulated violations. |
| **P1** | **CLI Subcommand Unification** | Subcommands return Phase 0 placeholder errors. | `src/railway_detection/cli/main.py` | Must provide single-command execution for pipeline evaluation and simulation. | 1. Implements `vision evaluate`, `simulate run`, and `experiment run`.<br>2. Connects CLI flags to underlying loaders and runners. | Smoke tests verifying CLI command execution without syntax or import errors. |
| **P1** | **Environment Package Residency Fix (macOS iCloud)** | Intermittent `OSError: Errno 89 Operation canceled` due to iCloud eviction of `.venv`. | `.venv/` configuration & environment docs | Prevents subprocess hangs during automated test discovery and batch evaluation. | 1. Pin `.venv` locally using `brctl download` or relocate project directory outside iCloud sync roots.<br>2. Verify `pytest` runs 100% cleanly without I/O timeouts. | Clean execution of `pytest tests/` in $< 30$ seconds. |
| **P2** | **Automated Publication Tables & Figures** | Basic scripts exist in `scripts/`; formal package missing. | `src/railway_detection/evaluation/tables.py`<br>`src/railway_detection/evaluation/plots.py` | Automated generation of camera-level metrics, state timelines, and SNR degradation curves. | 1. Outputs LaTeX/Markdown comparative tables.<br>2. Generates state transition timeline plots and PR curves. | Unit test verifying table formatting and figure generation. |

---

## 4. Real Layer B Data Contract

The pipeline must support consumer phone recordings without professional genlock or studio timecode.

### Directory Structure Contract
The system shall expect event bundles organized under `data/raw/layer_b/videos/`:

```text
data/raw/layer_b/videos/
├── event_001/
│   ├── camera_front.mp4           # Approach/front viewpoint (Camera 1)
│   ├── camera_rear.mp4            # Departure/rear viewpoint (Camera 2)
│   ├── metadata.json              # [OPTIONAL] Minimal field context
│   └── labels/
│       └── event_labels.json      # [OPTIONAL / GROUND TRUTH] Human reference timestamps
├── event_002/
│   ├── camera_front.mp4
│   └── camera_rear.mp4
└── ...
```

### Ingestion Specifications & Tolerances

1. **Naming Conventions & Aliases:**
   - Approach Camera: `camera_front.mp4`, `camera_front.mov`, `camera_1.mp4`, `camera_1.mov`.
   - Departure Camera: `camera_rear.mp4`, `camera_rear.mov`, `camera_2.mp4`, `camera_2.mov`.
   - Event ID: Inferred strictly from the enclosing directory name (`event_001` through `event_025`).

2. **Embedded Audio Extraction:**
   - Phone recordings embed audio directly within the MP4/MOV container.
   - The loader must automatically extract the embedded audio stream to a standardized 16 kHz mono WAV buffer/scratch file upon load.
   - If audio is absent or corrupted in one camera container, the system shall fall back to audio extracted from the paired camera.

3. **Video Format & FPS Handling:**
   - Supported containers: `.mp4`, `.mov`, `.avi`, `.mkv`.
   - Supported codecs: H.264 (AVC), H.265 (HEVC), ProRes.
   - Frame Rate Invariant: Consumer phone cameras frequently record at variable frame rates (VFR) or non-integer rates (29.97, 30.0, 59.94, 60.0 FPS).
   - The video reader must dynamically query `CAP_PROP_FPS` and calculate true timestamps:
     $$t_i = \frac{i}{\text{native\_fps}}$$
   - **Never hardcode FPS assumptions** in temporal smoothing or gate timers.

4. **Duration & Memory Management:**
   - Videos are 3–4 minutes in length (~5,400 to 7,200 frames at 30 FPS).
   - Loading all frames into RAM simultaneously would consume $>15\text{ GB}$ per event.
   - The loader must yield frames via an **iterator/generator stream** with configurable stride or target sampling rate (default: sample at 10 FPS for temporal efficiency).

5. **Graceful Degradation on Missing Metadata:**
   - If `metadata.json` is missing:
     - `direction`: set to `"unknown"`.
     - `weather`: set to `"unknown"`.
     - `lighting`: set to `"unknown"`.
     - `sync_offset_s`: set to `0.0`.
     - `sync_uncertainty_s`: set to `1.0`.
   - If `labels/event_labels.json` is missing:
     - Event is flagged as `unlabeled_inference_only`.
     - System executes full perception, fusion, and simulation replay, but excludes the event from ground-truth metric calculation (Missed Train / Premature Opening).

---

## 5. Audio Dataset Contract

The user has collected **100 train-audio recordings** for acoustic train-horn detection.

### Standardized Audio Specifications
- **Container / Format:** WAV (preferred), MP3, M4A, FLAC.
- **Sample Rate:** Standardized automatically to **16,000 Hz** via `audio.preprocessor.standardize_audio()`.
- **Channels:** Single-channel mono (stereo streams downmixed via channel averaging).
- **Bit Depth:** 16-bit linear PCM.
- **Analysis Window:** Sliding windows of **1.0 second duration** with **50% overlap (0.5s hop)**.
- **Feature Representation:** 64-band Log-Mel Spectrogram (FFT window 25ms, hop length 10ms).

### Methodological Critical Warning: 100 Audio Files Are Insufficient Alone
> [!WARNING]
> **SAMPLE SIZE & NEGATIVE CLASS LIMITATION**
> A dataset consisting exclusively of 100 positive train-horn audio clips is **scientifically insufficient** to train a deployable or generalizable acoustic classifier.
> 
> 1. **Zero Negative Exposure:** If trained only on positive train-horn clips, the model cannot learn the decision boundary against ambient noise.
> 2. **High False-Alarm Risk:** In Bangladeshi level-crossing environments, acoustic interference is extreme: truck horns, bus horns, auto-rickshaw (CNG) horns, crowd chatter, engine idling, generator noise, and monsoon rain.
> 3. **Overfitting:** 100 clips represent very few distinct acoustic recording sessions, risking acoustic memorization.

### Mandatory Dataset Expansion Requirements
Before training an acoustic classifier, the audio dataset must be structured as:
1. **Positive Class (`train_horn`):**
   - 100 real train-horn clips (diverse distances: near, medium, distant; diverse horn types: air horn, dual-tone electric horn).
2. **Negative Class (`non_train_sound`):**
   - **Minimum 200–300 negative audio segments** collected from crossing environments.
   - Must include:
     - Road vehicle horns (truck, bus, motorcycle, auto-rickshaw).
     - Railway ambient noise without train (track hum, chatter, street vendors).
     - Environmental noise (heavy rain, wind gusts on phone microphone).
     - Train passage without horn (rumble, wheel clatter).
3. **Partitioning Policy:**
   - Must be split by **recording session / crossing location**, never random clip splitting.

### Non-Negotiable Acoustic Safety Guard
> [!CAUTION]
> **SAFETY INVARIANT R-GUARD-OPENING**
> - Acoustic evidence is **SUPPORTING EVIDENCE ONLY**.
> - Audio detection may accelerate gate closure (e.g., approach confirmation when vision is low-confidence).
> - **Audio must NEVER independently authorize gate opening or crossing clearance.**
> - The absence of audio must NEVER be interpreted as the absence of a train.

---

## 6. Two-Camera Synchronization Strategy

Because consumer phone recordings lack hardware genlock, NTP synchronization, or SMPTE timecodes, the architecture must adopt a scientifically defensible synchronization strategy.

### Multi-Tiered Alignment Protocol

```text
Tier 1: Audio Cross-Correlation (Automated Primary Alignment)
   │
   ▼ (Fallback if audio correlation peak is ambiguous)
Tier 2: Visual Event Onset Alignment (Landmark Passage)
   │
   ▼ (Fallback if visual onset is unobservable)
Tier 3: Manual Synchronization Marker / Time Offset
   │
   ▼
Tier 4: Tolerance-Windowed Asynchronous Collation
```

### 1. Tier 1: Acoustic Cross-Correlation (Recommended Primary Method)
- Both phones record ambient audio simultaneously.
- Audio contains sharp, shared acoustic markers: train horn blasts, initial rail clatter, or a deliberate clap/shout at the beginning of recording.
- **Algorithm:**
  1. Extract audio from `camera_front.mp4` and `camera_rear.mp4` at 16 kHz.
  2. Bandpass filter between 500 Hz and 4,000 Hz to isolate horns and transient impacts.
  3. Compute generalized cross-correlation with phase transform (GCC-PHAT):
     $$R_{xy}(\tau) = \mathcal{F}^{-1}\left( \frac{X(f) Y^*(f)}{|X(f) Y^*(f)|} \right)$$
  4. The peak location $\tau_{\text{peak}}$ defines the temporal offset $\Delta t_{\text{offset}}$.
  5. If the correlation peak prominence exceeds threshold $\gamma_{\text{prominence}}$, mark alignment as `automated_audio_sync` with `uncertainty_s = 0.05` (50 ms).

### 2. Tier 2: Visual Event Onset Alignment (Secondary Fallback)
- When acoustic correlation fails, identify a visible train landmark crossing a known reference line visible in both cameras (e.g., front locomotive edge entering the crossing road boundary).
- Offset: $\Delta t_{\text{offset}} = t_{\text{cam2\_entry}} - t_{\text{cam1\_entry}} - \Delta t_{\text{travel}}$, where $\Delta t_{\text{travel}}$ is estimated from observed train velocity.
- Marked with `uncertainty_s = 0.2` to `0.5` seconds.

### 3. Tier 3: Manual Offset Specification
- Allow entering manual offset in `metadata.json`:
  ```json
  {
    "sync_method": "manual_marker",
    "sync_offset_s": 2.34,
    "sync_uncertainty_s": 0.25
  }
  ```

### 4. Architectural Resilience: Tolerance-Windowed Reasoning
- **Do NOT design the architecture assuming frame-accurate (1/30s) alignment.**
- The temporal evidence engine and decision state machine must operate on a **confirmation window** (e.g., $W = 1.0\text{s}$ to $2.0\text{s}$) rather than instantaneous multi-camera AND gates.
- Approach evidence on Camera 1 and departure evidence on Camera 2 are naturally separated in time by train transit duration ($10\text{s} - 60\text{s}$). Sub-second synchronization uncertainty has negligible impact on crossing-level safety decisions if the confirmation window is calibrated properly.

---

## 7. Safety-Critical State Machine Review

The system state machine controls simulated gate movement. An audit of historical documentation identified several dangerous potential failure modes that must be strictly guarded in code.

### Audit of Dangerous Assumptions & Required Guard Logic

```text
================================================================================
CRITICAL SAFETY AUDIT: DANGEROUS ASSUMPTIONS vs. REQUIRED CONSERVATIVE GUARDS
================================================================================
```

| ID | Dangerous Assumption | Hazard & Failure Mode | Required Conservative Guard Logic |
|:---:|---|---|---|
| **D-1** | **"Rear detection means crossing is clear."** | **FATAL HAZARD:** Detector predicts `rear` on a coach or mid-train flatcar, or train stops with rear over the crossing. Gate opens directly into passing or stopped train. | **Guard G-CLEARANCE:** Rear detection is *model evidence only*, never clearance. Opening requires: (1) `rear` confirmed on Camera 2, (2) zero detections on Camera 1, (3) clear dwell time $\tau_{\text{dwell}} \ge 3.0\text{s}$ with zero train evidence across both cameras, and (4) independent reference clearance condition satisfied. |
| **D-2** | **"Absence of detection means no train is present."** | **FATAL HAZARD:** Dense fog, darkness, dirty lens, temporary camera disconnection, or extreme occlusion causes detector output to drop to zero. Gate opens while train is occupying crossing. | **Guard G-OCCUPANCY-PERSISTENCE:** Loss of visual detection while in `TRAIN_PRESENT` or `CROSSING_OCCUPIED` must hold gate closed under persistence decay and transition to `FAULT_FAIL_SAFE`. **Absence never authorizes opening.** |
| **D-3** | **"Absence of audio means no train is approaching."** | **FATAL HAZARD:** Train driver does not sound horn, horn is broken, or phone microphone clips. System assumes track is empty. | **Guard G-AUDIO-SUPPORT-ONLY:** Audio is supporting approach evidence only. Audio absence has zero weight in clearance decisions. |
| **D-4** | **"Single-frame detection triggers gate action."** | **EFFICIENCY HAZARD:** Bird, truck, shadow, or false-positive box on background triggers premature closure; single false-positive rear box triggers early opening. | **Guard G-TEMPORAL-CONFIRMATION:** Every viewpoint class requires $N \ge 3$ consecutive confirmed frames within window $W \le 0.5\text{s}$ before changing state qualification level from `PROVISIONAL` to `CONFIRMED`. |
| **D-5** | **"Stream loss or sync failure defaults to normal clear."** | **FATAL HAZARD:** Camera freezes or cable disconnects; system defaults to empty background and opens gate. | **Guard G-HEARTBEAT-FAIL-SAFE:** Loss of stream heartbeat ($> 1.0\text{s}$) transitions system immediately to `FAULT_FAIL_SAFE`, commanding simulated gate closed and logging an unresolvable fault. |
| **D-6** | **"Gate completes opening even if a new train appears."** | **FATAL HAZARD:** Second train approaches on opposite track while gate is in `GATE_OPENING`. | **Guard G-ABORT-OPENING:** If qualified approach evidence appears while in `GATE_OPENING`, the state machine immediately aborts opening and transitions directly to `WARNING` $\to$ `GATE_CLOSING`. |

### Formal State Machine Architecture

```text
                     ┌─────────────────────────────────────────────────────────────┐
                     ▼                                                             │
                  [IDLE] (Gate OPEN)                                               │
                     │                                                             │
                     │ Qualified Approach (Cam 1 front/side OR Cam 1 low + Audio)  │
                     ▼                                                             │
            [TRAIN_APPROACHING]                                                    │
                     │                                                             │
                     │ Confirmation window satisfied (N >= 3 frames)               │
                     ▼                                                             │
                 [WARNING] (Warning dwell tau_warn >= 2.0s)                        │
                     │                                                             │
                     │ Warning dwell elapsed                                       │
                     ▼                                                             │
               [GATE_CLOSING] (Travel time tau_close >= 4.0s)                      │
                     │                                                             │
                     │ Gate closed feedback                                        │
                     ▼                                                             │
              [TRAIN_PRESENT] ◄────────────────────────────────────────┐           │
                     │                                                 │           │
                     │ Crossing occupancy confirmed (Cam 1/2 side)     │           │
                     ▼                                                 │           │
            [CROSSING_OCCUPIED]                                        │           │
                     │                                                 │           │
                     │ Departure viewpoint observed (Cam 2 rear)       │ Persistence│
                     ▼                                                 │ Holding   │
             [TRAIN_DEPARTING]                                         │           │
                     │                                                 │           │
                     │ Rear confirmed (N >= 3 frames on Cam 2)         │           │
                     ▼                                                 │           │
             [REAR_CONFIRMED]                                          │           │
                     │                                                 │           │
                     │ Positive clearance dwell (tau_dwell >= 3.0s)    │           │
                     │ AND zero detections on Cam 1 & Cam 2            │           │
                     ▼                                                 │           │
             [CROSSING_CLEAR]                                          │           │
                     │                                                 │           │
                     │ Clearance verified; command opening             │           │
                     ▼                                                 │           │
               [GATE_OPENING] ──(New Approach Detected)──► [WARNING]   │           │
                     │                                                 │           │
                     │ Gate fully opened (tau_open >= 4.0s)            │           │
                     └─────────────────────────────────────────────────┘           │
                                                                                   │
     [ANY ACTIVE STATE] ──(Stream Loss / Sensor Fault / Timeout)──► [FAULT_FAIL_SAFE]
                                                                     (Gate CLOSED)
```

---

## 8. Evaluation Design (The 25 Real Events)

The 25 real-world train-passage events (50 phone videos) constitute the **Held-Out System-Level Evaluation Benchmark**.

### Strict Partitioning & Data Isolation
> [!IMPORTANT]
> **ZERO LEAKAGE INVARIANT**
> 1. The 25 paired events **must NEVER enter model training**. They are not training data.
> 2. The 25 events must **NEVER be used for iterative threshold tuning**.
> 3. Partitioning:
>    - **Development / Tuning Cohort (5 events):** Used once to calibrate temporal confirmation windows, persistence decay, and noise thresholds.
>    - **Frozen Held-Out Evaluation Cohort (20 events):** Evaluated strictly once with all hyperparameters frozen.

### Ground Truth Annotations Realistically Possible from Phone Video
Professional railway track circuits and wheel sensors are unavailable. Ground truth must be derived from rigorous human reference annotation according to `docs/EVENT_LABEL_PROTOCOL.md`:

```text
labels/event_labels.json
├── event_id: "event_001"
├── annotator_id: "annotator_01"
├── reference_geometry:
│   ├── approach_line_y: 350       # Landmark line in Camera 1 frame
│   └── departure_line_y: 420      # Landmark line in Camera 2 frame
├── reference_events:
│   ├── first_visual_appearance: {"timestamp_s": 12.4, "camera": "front"}
│   ├── crossing_entry:          {"timestamp_s": 18.2, "camera": "front"}
│   ├── crossing_occupied_start: {"timestamp_s": 19.5, "camera": "front"}
│   ├── crossing_exit:           {"timestamp_s": 42.1, "camera": "rear"}
│   ├── tail_clearance:          {"timestamp_s": 44.0, "camera": "rear", "status": "observed"}
│   └── audible_horn_events:     [{"start_s": 14.1, "end_s": 16.2}]
```
*Note on Clearance Ground Truth:* If the downstream camera angle does not show the tail clearing the crossing boundary, mark `tail_clearance.status = "unobservable"`. The event is retained for approach analysis but excluded from the premature opening denominator.

### Quantitative Evaluation Metrics

#### 1. Primary Safety Endpoints
- **Event-Level Missed-Train Rate ($R_{\text{miss}}$):**
  $$R_{\text{miss}} = \frac{\text{Events where gate was not fully CLOSED before crossing entry}}{\text{Total evaluable train events}}$$
  *Target: 0.0% on evaluable events.*
- **Premature-Opening Rate ($R_{\text{premature}}$):**
  $$R_{\text{premature}} = \frac{\text{Events where gate began opening before ground-truth tail clearance}}{\text{Total events with observable tail clearance}}$$
  *Target: 0.0% (Zero tolerance for premature opening).*

#### 2. Secondary Operational Endpoints
- **Warning Lead Time ($T_{\text{lead}}$):**
  $$T_{\text{lead}} = t_{\text{crossing\_entry}} - t_{\text{warning\_initiated}}$$
  Report mean, median, and 95% bootstrap confidence interval.
- **Late Closure Rate:** Percentage of events where $T_{\text{lead}} < \tau_{\text{minimum\_warning}}$ (e.g., $< 20.0\text{s}$).
- **Departure Confirmation Latency:** Time delta between reference tail clearance and state transition to `GATE_OPENING`.
- **False Alarm Rate:** False simulated closures per hour of evaluable empty-track recording.

---

## 9. Research Claims We Can and Cannot Make

To preserve academic integrity and avoid rejection during peer review, the research boundaries must be clearly delineated.

### Supported Claims (Scientifically Justifiable)
1. **Multi-View Perception Advantage:** Empirical evidence that dual-camera orientation (approach + departure views) provides superior temporal viewpoint continuity compared to a single approach camera.
2. **Temporal Smoothing Efficacy:** Quantitative proof that consecutive-frame confirmation and persistence buffers eliminate single-frame false-positive gate actuations without compromising detection lead time.
3. **Conservative Decision Logic:** Demonstration that formal state-machine guards prevent premature simulated opening under rear-viewpoint misclassifications.
4. **Multimodal Audio Support:** Empirical demonstration that acoustic horn features provide supporting evidence during adverse optical conditions (simulated or observed occlusion).
5. **Reproducible Simulation Benchmark:** A standardized, open evaluation harness for replaying synchronized multi-camera railway crossings.

### Unsupported Claims (Strictly Prohibited)
1. ❌ **"Crossing-Independent Generalization":** Dataset V1 was trained with `development_fallback` grouping. We cannot claim the vision baseline generalizes to all crossings across Bangladesh.
2. ❌ **"Railway-Grade Safety / Fail-Safe System":** The software is a simulated prototype. It has not been formally verified under CENELEC EN 50126 / EN 50128 / EN 50129 standards or SIL-4 safety integrity requirements.
3. ❌ **"Zero-Error Operational Deployment":** 25 events are statistically insufficient to demonstrate 99.999% field reliability. Statistical uncertainty must always be reported via confidence intervals.
4. ❌ **"Universal Weather & Lighting Robustness":** Unless the 25 events contain statistically significant subsets of heavy monsoon rain, thick fog, and pitch-black night, claims must be restricted to represented conditions.
5. ❌ **"Edge Hardware Real-Time Certified":** Latency on an Apple Silicon Mac development machine does not prove real-time execution on an edge Raspberry Pi or Jetson Nano without target hardware benchmarking.

---

## 10. Exact Remaining Implementation Roadmap

To transition from the current state to **"Plug-and-Test Ready"**, implementation must proceed through the following ordered engineering phases.

```text
================================================================================
PRE-REAL-DATA ENGINEERING ROADMAP: PHASES A THROUGH F
================================================================================
```

### Phase A: Layer B Media Resolver & Flexible Loader
- **Objective:** Ingest bare event folders containing `camera_front.mp4` and `camera_rear.mp4` with embedded audio and optional metadata.
- **Modules:** `src/railway_detection/data/layer_b.py`, `src/railway_detection/data/contracts.py`.
- **Key Logic:**
  - Auto-alias `camera_front` / `camera_rear` and `camera_1` / `camera_2`.
  - Extract embedded audio track to 16 kHz mono WAV via `wave` / `subprocess` (ffmpeg).
  - Default fallbacks for missing `metadata.json` and `geometry.json`.
- **Tests:** `tests/unit/test_layer_b_loader.py` (add tests for un-annotated bundles, MP4-embedded audio extraction, and alias resolution).
- **Acceptance Criteria:** `load_event_bundle()` loads a bare two-video folder without errors.

### Phase B: Audio Feature Extractor & Classifier Interface
- **Objective:** Compute Mel-spectrogram features and establish modular classifier protocol.
- **Modules:** `src/railway_detection/audio/features.py`, `src/railway_detection/audio/model.py`, `src/railway_detection/audio/pipeline.py`.
- **Key Logic:**
  - Log-Mel spectrogram extraction (64 bins, 16 kHz).
  - Abstract `AudioClassifier` interface with lightweight CNN or spectral random-forest implementation.
  - Generates `EvidenceRecord` with `modality = Modality.AUDIO`.
- **Tests:** `tests/unit/test_audio_features.py`, `tests/unit/test_audio_model.py`.
- **Acceptance Criteria:** Audio pipeline processes WAV window and emits calibrated $P(\text{train\_horn})$.

### Phase C: Multimodal Evidence Collector & Source Tracker
- **Objective:** Aggregate asynchronous streams from Camera 1, Camera 2, and Microphone into unified, time-stamped snapshots.
- **Modules:** `src/railway_detection/fusion/source_tracker.py`, `src/railway_detection/fusion/collector.py`.
- **Key Logic:**
  - Track sensor heartbeats and flag `UNAVAILABLE` when frame intervals exceed timeout.
  - Collate Camera 1, Camera 2, and Audio evidence records into a coherent time-indexed snapshot.
- **Tests:** `tests/unit/test_evidence_collector.py`, `tests/unit/test_source_tracker.py`.
- **Acceptance Criteria:** Dropping one camera stream marks that source `UNAVAILABLE` while other streams continue cleanly.

### Phase D: Deterministic Decision Engine & Safety Policy Rules
- **Objective:** Evaluate declarative safety rules and generate explainable state transition directives.
- **Modules:** `src/railway_detection/fusion/rules.py`, `src/railway_detection/fusion/decision_engine.py`.
- **Key Logic:**
  - Rule R-APPROACH: Cam 1 front confirmed OR (Cam 1 low conf + Audio confirmed).
  - Rule R-OCCUPANCY: Cam 1 or Cam 2 side confirmed $\to$ maintain closed gate.
  - Rule R-DEPARTURE: Cam 2 rear confirmed AND zero Cam 1 approach evidence.
  - Rule R-CLEARANCE: Positive dwell elapsed AND both cameras clear.
  - Invariant Guard: Audio or detection disappearance alone CANNOT command opening.
- **Tests:** `tests/unit/test_decision_rules.py`, `tests/unit/test_decision_engine.py`.
- **Acceptance Criteria:** 100% rule condition coverage and verified invariant blocking.

### Phase E: Crossing State Machine & Simulation Replay Runner
- **Objective:** Replay multimodal evidence through formal crossing states with simulated gate dynamics.
- **Modules:** `src/railway_detection/simulation/state_machine.py`, `src/railway_detection/simulation/gate_model.py`, `src/railway_detection/simulation/runner.py`.
- **Key Logic:**
  - Formal states: `IDLE`, `APPROACHING`, `WARNING`, `CLOSING`, `PRESENT`, `OCCUPIED`, `DEPARTING`, `REAR_CONFIRMED`, `CLEAR`, `OPENING`, `FAULT_FAIL_SAFE`.
  - Gate positions: `OPEN`, `CLOSING`, `CLOSED`, `OPENING`.
  - Export chronological replay log (`simulation_log.json`, `simulation_log.csv`).
- **Tests:** `tests/unit/test_state_machine.py`, `tests/unit/test_gate_model.py`, `tests/integration/test_simulation_runner.py`.
- **Acceptance Criteria:** Normal event sequence executes cleanly from IDLE to OPENING to IDLE with correct dwell timings. Direct prohibited transitions throw errors.

### Phase F: Real-Event System Evaluator & Baseline Matrix (B0–B6)
- **Objective:** Execute full event evaluation and compute primary safety endpoints on held-out events.
- **Modules:** `src/railway_detection/evaluation/metrics.py`, `src/railway_detection/experiments/runner.py`.
- **Key Logic:**
  - Evaluates B0, B1, B2, B3, B4, B5, B6 baselines.
  - Calculates Event-Level Missed-Train Rate and Premature-Opening Rate with 95% Wilson score confidence intervals.
  - Calculates Warning Lead Time distribution.
- **Tests:** `tests/unit/test_event_metrics.py`, `tests/integration/test_experiment_runner.py`.
- **Acceptance Criteria:** Running the evaluation script against mock/real event bundles generates `system_evaluation_report.md` with complete metrics and confidence intervals.

---

## 11. Final GO / NO-GO Decision

```text
================================================================================
REAL-DATA READINESS VERDICT: CONDITIONAL (NO-GO FOR IMMEDIATE INGESTION)
================================================================================
```

### Verdict Explanation
The project is **PERCEPTION READY** but **SYSTEM EVALUATION UNREADY**.
- You **CAN** immediately run single-video detection demonstrations on any raw video using `python demo_video.py`.
- You **CANNOT** ingest the 25 paired events and 100 audio files for system evaluation, because the two-camera collation, state machine, decision engine, audio classifier, and event metrics calculators are not yet implemented. Ingesting the data today would produce load errors or dead-end at static detections without system-level results.

### Exact Blocking Tasks (The P0 Must-Complete List)
Before dropping the 25 paired folders into `data/raw/layer_b/videos/` and running the evaluation, complete:
1. **Task P0-A:** Update `src/railway_detection/data/layer_b.py` to support `camera_front.mp4` / `camera_rear.mp4`, auto-extract audio from MP4, and handle missing metadata without erroring.
2. **Task P0-B:** Implement `src/railway_detection/fusion/decision_engine.py` and `src/railway_detection/fusion/rules.py` with the non-negotiable opening guard.
3. **Task P0-C:** Implement `src/railway_detection/simulation/state_machine.py` and `src/railway_detection/simulation/gate_model.py`.
4. **Task P0-D:** Implement `src/railway_detection/audio/features.py` and modular classifier interface in `src/railway_detection/audio/model.py`.
5. **Task P0-E:** Implement `src/railway_detection/evaluation/metrics.py` for event-level missed train and premature opening endpoints.

Once these 5 core modules are implemented and verified via unit tests against synthetic fixtures, the verdict immediately becomes **FULL GO**. Adding the 25 events and 100 audio recordings will then be a true **plug-and-test** operation.
