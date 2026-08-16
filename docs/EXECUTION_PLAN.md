# Execution Plan: Safety-Oriented Multimodal Railway-Crossing Train Detection Research System

**Document Version:** 1.0.0  
**Date:** 2026-08-16  
**Author:** Senior Software Architect, ML Engineering Lead, & Research Implementation Planner  
**Target Executing Agent:** DeepSeek V4 Pro  
**Authority & Source of Truth:** Reconciled against `docs/RESEARCH_PROTOCOL_V2.md`, `docs/EXPERIMENT_PROTOCOL_V2.md`, `docs/DATASET_SPECIFICATION_V2.md`, `docs/ANNOTATION_GUIDELINE_V2.md`, `docs/EVENT_LABEL_PROTOCOL.md`, `docs/HAZARD_MODEL.md`, and `docs/RESEARCH_DECISIONS.md`.

---

## 1. Executive Summary & Research Safety Boundary

### 1.1 Project Mission
This research project investigates whether a multi-view, audio-assisted, temporal, state-aware AI detection framework can improve event-level train approach, occupancy, and departure detection at railway level-crossings in Bangladesh.

The framework integrates:
1. **Camera 1 (Approach View):** Specialized in detecting approaching train viewpoints (`front`, `side`).
2. **Camera 2 (Departure View):** Specialized in monitoring passage and detecting departure viewpoints (`side`, `rear`).
3. **Microphone (Acoustic Evidence):** Independent supporting/fallback detection of train horns (`train_horn` vs `non_train_sound`).
4. **Temporal Evidence Engine:** Filters frame jitter, confirms persistence, tracks source health, and handles dropouts.
5. **Safety-Oriented Decision Engine:** Fuses multimodal evidence against conservative state-machine policies.
6. **Software Crossing Simulation:** Replays synchronized sensor streams, models gate transitions (`OPEN`, `CLOSING`, `CLOSED`, `OPENING`), and measures safety/efficiency metrics under normal and failure conditions.

### 1.2 Non-Negotiable Research Safety & Scope Disclaimer
> [!CAUTION]
> **RESEARCH SOFTWARE & SIMULATION ONLY — STRICT SAFETY BOUNDARIES**
> 1. **No Live Infrastructure Connection:** This software is an experimental research prototype and simulation framework. It must NEVER be connected to live railway signaling, physical gate actuators, or operational railway infrastructure.
> 2. **No Physical Fail-Safe Claims:** The term "fail-safe" in historical notes refers strictly to a *software-simulated conservative closed-gate policy*. It does NOT claim physical fail-safe operation, functional safety certification (e.g., SIL 4 / CENELEC EN 50126/50128/50129), or production readiness.
> 3. **No Embedded Hardware Claims:** Do not claim real-time performance or low-latency guarantees on Raspberry Pi / NVIDIA Jetson edge devices unless physical benchmark tests are formally conducted and recorded on target hardware.
> 4. **No Claim Fabrication:** Never invent performance numbers, metrics, or datasets. All claims in generated reports must be mathematically derived from immutable, recorded experiment outputs on held-out data.

### 1.3 Two-Layer Dataset Design & Current Data Status
The system architecture strictly decouples perception model training from multimodal system evaluation:

*   **Layer A (Vision Image Dataset — Perception Layer):**
    *   *Current Status (Dataset V1):* ~1,300 real annotated train images with 3 classes (`front`, `side`, `rear`). This dataset is available **NOW** for immediate development, validation, splitting, and baseline model training.
    *   *Target Status (Dataset V2):* ~4,000 real annotated images across 30+ crossings with diverse environmental conditions (day, night, rain, fog).
    *   *Architectural Invariant:* **The entire codebase MUST be dataset-size agnostic.** All validation, dataset splitting, training, and evaluation pipelines must dynamically discover dataset sizes and distributions without hard-coded thresholds or numbers.
*   **Layer B (Synchronized Train-Passage Event Dataset — System Layer):**
    *   *Current Status:* **DOES NOT EXIST YET.** Layer B is planned for future field collection (~20–30 complete train-passage events recorded via mobile phones with simple audiovisual clap/marker synchronization).
    *   *Structure:* Each event will contain `camera_1.mp4`, `camera_2.mp4`, and `audio.wav` (or embedded audio), plus minimal metadata (`event_id`, `crossing_id`, direction, weather, lighting).
    *   *Purpose:* Multimodal temporal evaluation, two-camera handoff, acoustic support validation, state-machine simulation, and failure injection.
    *   *Engineering Requirement:* **All multimodal, temporal, and simulation components must be developed against mock fixtures and synthetic event streams first, so that real Layer B ingestion is a plug-and-play operation when data arrives.**

---

## 2. Research Decisions & Conflict Resolution Register

Before implementing code, the executing agent must adhere to the following resolved methodological decisions:

| Topic | Historical / Preliminary Text | Resolved Authoritative Specification (`V2`) | Implementation Impact |
|---|---|---|---|
| **Primary Research Unit** | Frame-level bounding box detections (`RESEARCH_CONCEPT.md`). | One complete **train-passage event** on synchronized held-out recordings (`RESEARCH_PROTOCOL_V2.md`). | High-level metrics must aggregate per event (missed-train rate, premature-opening rate), not just per frame. |
| **Tail Clearance Ground Truth** | Inferred from detector predicting `rear` class (`RESEARCH_CONCEPT.md`). | `rear` detection is a **model evidence signal** only. Ground truth clearance requires independent scene observation or reference geometry (`EVENT_LABEL_PROTOCOL.md`). | Simulator must never treat `rear` detection as ground truth for tail clearance. If clearance cannot be observed, label as `clearance_unobservable`. |
| **Multimodal Fusion Policy** | Arithmetic confidence ORing: `front OR side OR rear OR horn` (`RESEARCH_CONCEPT.md`). | Predeclared, calibrated, source-specific rule conditions and state transitions (`RESEARCH_PROTOCOL_V2.md`). | Prevent naive ORing. High traffic noise makes uncalibrated horn ORing inflate false alarms. |
| **Audio Modality Role** | Independent primary trigger for gate opening/closing. | Supporting/fallback evidence for closure only. **Audio can NEVER authorize gate opening.** | Decision engine must enforce an explicit guard blocking audio from triggering `GATE_OPENING` or `CROSSING_CLEAR`. |
| **Camera Geometry** | Fixed assumption of 5–6 meters separation (`RESEARCH_CONCEPT.md`). | Configurable scenario metadata. Calibrated physical distance is optional (`SYNCHRONIZED_DATA_COLLECTION_PROTOCOL.md`). | Geometry spacing and view angles must reside in YAML configuration / event metadata, never hard-coded in Python logic. |
| **Data Leakage & Splitting** | Random image split (`RESEARCH_CONCEPT.md`). | Hierarchical group-aware split: `crossing → session → recording → event → frame` (`RESEARCH_PROTOCOL_V2.md`). | Split generator must enforce group disjointness. If crossing metadata is missing in Dataset V1, emit explicit warnings and require `--allow-ungrouped`. |

---

## 3. Global Dependency Graph & Implementation Architecture

```text
================================================================================================
                                   SYSTEM DEPENDENCY GRAPH
================================================================================================

[configs/*.yaml] ──► [config/loader.py] ──► [data/contracts.py]
                                                    │
               ┌────────────────────────────────────┴────────────────────────────────────┐
               ▼                                                                         ▼
     [Layer A: Vision Pipeline]                                                [Layer B: Event Pipeline]
┌──────────────────────────────────────┐                                 ┌──────────────────────────────────────┐
│ [data/validator.py] (Dataset V1)     │                                 │ [data/layer_b_loader.py] (Mock/Real) │
│               ▼                      │                                 │               ▼                      │
│ [data/split.py] (Group-Aware Split)  │                                 │ [data/sync_aligner.py]               │
│               ▼                      │                                 └──────────────────┬───────────────────┘
│ [vision/yolo_adapter.py]             │                                                    │
│               ▼                      │                                                    │
│ [vision/trainer.py] (YOLO Training)  │                                                    │
│               ▼                      │                                                    │
│ [vision/evaluator.py] (Metrics/mAP)  │                                                    │
│               ▼                      │                                                    │
│ [vision/inference.py] (Frame/Video)  │                                                    │
└──────────────────┬───────────────────┘                                                    │
                   │                                                                        │
                   ▼                                                                        ▼
        [vision/temporal.py] ◄────────────── [audio/pipeline.py] ◄────────────── [audio/detector.py]
                   │                                   (Horn Classifier)
                   ▼
        [fusion/evidence.py] ◄────────────── [fusion/collector.py]
                   │
                   ▼
        [fusion/decision_engine.py]
                   │
                   ▼
        [simulation/state_machine.py] ◄───── [simulation/hazard_guards.py]
                   │
                   ▼
        [simulation/crossing_simulator.py] ◄ [simulation/failure_injector.py]
                   │
                   ▼
        [experiments/runner.py] (Baselines B0–B7 & Ablations)
                   │
                   ▼
        [evaluation/metrics.py] ──► [evaluation/tables.py] ──► [evaluation/plots.py]
                                                 │
                                                 ▼
                                   [results/ & Final Reports]
================================================================================================
```

### Parallelizable Workstreams
Once Phase 0 and Phase 1 data contracts are verified, development can proceed along three parallel tracks:
*   **Track 1 (Vision):** Phase 2 (Vision Training) → Phase 3 (Vision Evaluation) → Phase 4 (Video Inference & Temporal Buffer).
*   **Track 2 (Audio & Layer B Ingestion):** Phase 5 (Layer B Mock/Real Ingestion) → Phase 6 (Audio Feature & Baseline Model).
*   **Track 3 (Fusion & Simulation Engine):** Phase 7 (Multimodal Interface) → Phase 8 (Decision Engine) → Phase 9 (State Machine) → Phase 10 (Failure Injector).

---

## 4. Phase-by-Phase Implementation Specifications

---

### PHASE 0: Repository & Engineering Foundation
*Status: IMPLEMENTED & VERIFIED (Maintain as baseline)*

#### Goal
Establish a reproducible, typed, tested Python 3.11+ foundation with configuration parsing, structured logging, run manifests, experiment registry, and basic CLI commands.

#### Current Repository Assets
*   `pyproject.toml`: Configured with `setuptools`, dependencies (`PyYAML`, `Pillow`), dev tools (`pytest`, `ruff`, `mypy`).
*   `src/railway_detection/config/loader.py`: Validates `vision.yaml`, `audio.yaml`, `fusion.yaml`, `simulation.yaml`.
*   `src/railway_detection/data/contracts.py`: Dataclasses for `BoundingBox`, `VisionAnnotation`, `VisionSample`, `AudioSample`, `LayerBEvent`, `EventLabel`.
*   `src/railway_detection/fusion/evidence.py`: Enums (`Modality`), `Detection`, `EvidenceRecord`, `DecisionRecord`, `UnavailableSource`.
*   `src/railway_detection/utils/reproducibility.py`: Run manifest builder and experiment registry recorder.
*   `src/railway_detection/cli/main.py`: CLI dispatcher with `data validate` and `data split`.

#### File-by-File Specification Table
| File Path | Purpose | Inputs | Outputs | Dependencies | Tests |
|---|---|---|---|---|---|
| `src/railway_detection/config/loader.py` | Parse & validate YAML configs | YAML file path | `VisionConfig`, `AudioConfig`, `FusionConfig`, `SimulationConfig` | PyYAML | `tests/unit/test_config.py` |
| `src/railway_detection/data/contracts.py` | Typed domain schemas | Dict/primitive data | Immutable dataclass instances | stdlib | `tests/unit/test_contracts.py` |
| `src/railway_detection/utils/reproducibility.py` | Traceability & manifests | Run parameters, git commit | `run_manifest.json`, registry records | stdlib | `tests/integration/test_phase0_smoke.py` |
| `src/railway_detection/cli/main.py` | Top-level CLI entry point | CLI arguments | Command execution & exit codes | argparse | `tests/smoke/test_cli_smoke.py` |

#### Acceptance Criteria (Definition of Done)
1. `pytest` executes 31+ tests with 100% pass rate.
2. `ruff check src tests` reports 0 linting errors.
3. `mypy src` passes with 0 type errors.
4. CLI `--help` displays all top-level command groups.

---

### PHASE 1: Current 1,300-Image Dataset Pipeline (Dataset V1)
*Status: READY TO EXECUTE IMMEDIATELY*

#### Goal
Build a robust, dataset-size agnostic data ingestion and validation pipeline for the ~1,300 annotated real train images. The pipeline must validate image readability, label syntax, bounding box normalization, class IDs, duplicate candidates, calculate class/metadata distributions, and generate group-aware leakage-safe splits.

#### Technical Requirements
1. **Dynamic Size Discovery:** Never hardcode 1,300. The pipeline must discover all images (`.jpg`, `.jpeg`, `.png`, `.webp`) in `data/raw/vision/images/` and corresponding labels in `data/raw/vision/labels/`.
2. **Annotation Validation:**
   * Verify YOLO format: `<class_id> <x_center> <y_center> <width> <height>`.
   * Verify $0 \le \text{class\_id} \le 2$ mapping to `0: front`, `1: side`, `2: rear`.
   * Verify all coordinates are finite numbers in $[0.0, 1.0]$ with $\text{width} > 0$ and $\text{height} > 0$.
   * Verify normalized bounding box $[x_{\min}, y_{\min}, x_{\max}, y_{\max}] \subseteq [0.0, 1.0]$.
   * Support configured negative policy: missing label or empty text file is treated as explicit background negative.
3. **Duplicate Detection:**
   * Calculate SHA-256 hashes to catch exact byte-level duplicates.
   * Check basename collisions across nested directories.
   * Provide extensible interface for perceptual hash (`dHash`/`pHash`) candidate flagging.
4. **Group-Aware Splitting & Leakage Fallback:**
   * Read `data/metadata/vision_metadata.json` if present.
   * If `crossing_id` or `session_id` is available, group all frames by `split_group_id`.
   * Enforce partition ratios (default: 70% train, 15% val, 15% test) at the group level.
   * **Leakage Fallback Protocol:** If grouping metadata is unavailable for Dataset V1 images:
     * Emit prominent CLI and log warnings: `WARNING: No grouping metadata found. Split is NOT guaranteed leakage-safe.`
     * Require `--allow-ungrouped` flag (or `allow_ungrouped_fallback: true` in config).
     * Output `split_summary.json` explicitly tagged with `leakage_risk: true` and `split_type: "development_fallback"`.
5. **Artifact Outputs:** Generate machine-readable `report.json`, human-readable `report.md`, and partition manifests (`train.jsonl`, `val.jsonl`, `test.jsonl`).

#### File-by-File Specification Table
| File Path | Purpose | Inputs | Outputs | Dependencies | Tests |
|---|---|---|---|---|---|
| `src/railway_detection/data/validator.py` | Validate vision dataset integrity | Image & label root paths, class mapping | `ValidationReport`, `report.json`, `report.md` | Pillow | `tests/unit/test_validator.py` |
| `src/railway_detection/data/split.py` | Deterministic group-aware splitter | Samples with `split_group_id`, ratios, seed | `SplitSummary`, partition manifests (`train.jsonl`, etc.) | hashlib, random | `tests/unit/test_split.py` |
| `src/railway_detection/data/manifest.py` | Generate normalized dataset manifest | Validated image/label pairs & metadata | `dataset_manifest.jsonl` | stdlib | `tests/unit/test_manifest.py` |

#### Acceptance Criteria (Definition of Done)
1. Running `python -m railway_detection data validate --config configs/vision.yaml` against Dataset V1 parses all ~1,300 images without crash and writes `results/dataset_validation/report.json`.
2. Running `python -m railway_detection data split --config configs/vision.yaml` produces `data/splits/<split_id>/` containing `train.jsonl`, `val.jsonl`, `test.jsonl`, and `split_summary.json`.
3. Unit tests cover: corrupted images, out-of-bounds coordinates, non-integer class IDs, negative dimensions, duplicate hashes, and group disjointness verification.

---

### PHASE 2: Initial Vision Model Training
*Status: READY TO EXECUTE ONCE PHASE 1 DATA SPLIT IS FROZEN*

#### Goal
Implement a modular, configurable YOLO-compatible object detection training pipeline. Train baseline vision models on Dataset V1 using validation data for checkpoint selection.

#### Technical Requirements
1. **Framework Adapter Interface:** Define an abstract `VisionDetectorBackend` protocol:
   * `prepare_dataset(split_summary: SplitSummary, output_dir: Path) -> Path`: Creates a backend-specific `data.yaml` descriptor.
   * `train(config: VisionConfig, data_descriptor: Path, output_dir: Path) -> Path`: Executes training and returns best checkpoint path.
   * `evaluate(checkpoint_path: Path, split_manifest: Path) -> dict[str, float]`: Computes validation/test metrics.
   * `load(checkpoint_path: Path)`: Prepares model for inference.
   * `predict(image: Image/ndarray, conf: float, iou: float) -> list[Detection]`: Emits typed detections.
2. **Ultralytics YOLO Backend:**
   * Implement `UltralyticsYOLOAdapter` supporting YOLOv8 / YOLOv11 / YOLOv9 models (e.g., `yolov8n.pt`, `yolov8s.pt`, `yolo11n.pt`).
   * Read all hyperparameters from `configs/vision.yaml`: `model_name`, `image_size` (default 640), `epochs` (default 50-100), `batch_size`, `device` (`cpu`, `cuda`, `mps`), `seed`, `workers`, `optimizer`, `lr0`, `augmentations` (mosaic, hsv, fliplr).
3. **Training Execution & Checkpoint Selection:**
   * Create unique experiment run directory: `experiments/vision/<run_id>/`.
   * Save `resolved_config.yaml`, `run_manifest.json`, framework training logs, and model checkpoints (`best.pt`, `last.pt`).
   * **Strict Model Selection Invariant:** Checkpoint selection must be driven exclusively by validation set performance (`val mAP@50` or `val loss`). **Never evaluate on the test split during hyperparameter tuning.**
4. **CLI Integration:**
   * Implement `python -m railway_detection vision train --config configs/vision.yaml [--override key=value]`.
   * Implement `--dry-run` to generate dataset descriptors and verify configs without starting GPU training.

#### File-by-File Specification Table
| File Path | Purpose | Inputs | Outputs | Dependencies | Tests |
|---|---|---|---|---|---|
| `src/railway_detection/vision/adapter.py` | Abstract vision backend protocol | Raw images, configs | Standardized detection outputs | ABC | `tests/unit/test_vision_adapter.py` |
| `src/railway_detection/vision/yolo_adapter.py` | Ultralytics YOLO implementation | Configs, split manifests | YOLO `data.yaml`, trained weights | ultralytics (or mock) | `tests/unit/test_yolo_adapter.py` |
| `src/railway_detection/vision/trainer.py` | Training loop orchestration | `VisionConfig`, split manifests | Checkpoints, `training_metrics.json` | vision adapter | `tests/integration/test_vision_train_mock.py` |

#### Acceptance Criteria (Definition of Done)
1. Training command runs end-to-end on mock/real data and saves weights to `experiments/vision/<run_id>/checkpoints/best.pt`.
2. Experiment registry records the training run ID, git revision, seed, dataset hash, and validation metrics.
3. Tests verify adapter instantiation, mock training loop execution, and checkpoint loading without external network calls.

---

### PHASE 3: Vision Evaluation & Failure Analysis
*Status: READY TO EXECUTE AFTER PHASE 2*

#### Goal
Implement comprehensive evaluation and error-analysis tooling for trained vision models. Generate standard detection metrics and diagnostic failure slices across viewpoint classes and environmental conditions.

#### Technical Requirements
1. **Metrics Calculation Engine:**
   * Calculate overall and per-class metrics: `mAP@50`, `mAP@50:95`, `Precision`, `Recall`, `F1-Score` at standard confidence threshold (0.5) and optimal F1 threshold.
   * Special emphasis on per-class recall: **Front Recall** (approach safety), **Side Recall** (presence monitoring), **Rear Recall** (departure clearance).
   * Generate Confusion Matrix (including background / false positives and missed ground truth / false negatives).
   * Generate Precision-Recall (PR) curves and F1 vs. Confidence curves.
2. **Systematic Failure Slicing:**
   * Categorize errors into:
     * `missed_front`: Train front present in ground truth, detector emitted background.
     * `front_side_confusion`: Train front classified as side or vice-versa.
     * `rear_side_confusion`: Train rear classified as side or vice-versa.
     * `false_train_detection`: High-confidence train detection on background/negative scene.
     * `low_confidence_detection`: Correct class detected but $\text{confidence} < \text{threshold}$.
   * If metadata is available, slice metrics across: `lighting` (day, night, dawn/dusk), `weather` (clear, rain, fog), `distance_band` (near, medium, far), and `occlusion` (none, partial, severe).
3. **Artifact Generation:**
   * Write `metrics.json` and human-readable `metrics.md`.
   * Export figures: `confusion_matrix.png`, `pr_curves.png`, `f1_confidence_curve.png`, `failure_samples_grid.png`.

#### File-by-File Specification Table
| File Path | Purpose | Inputs | Outputs | Dependencies | Tests |
|---|---|---|---|---|---|
| `src/railway_detection/vision/evaluator.py` | Compute mAP, confusion matrix, PR curves | Model checkpoint, test split manifest | `metrics.json`, evaluation dict | numpy, matplotlib | `tests/unit/test_vision_evaluator.py` |
| `src/railway_detection/vision/failure_analysis.py` | Classify detection failures & metadata slices | Predictions, ground truth, metadata | `failure_analysis.json`, `failure_report.md` | stdlib | `tests/unit/test_failure_analysis.py` |
| `src/railway_detection/cli/main.py` | Add `vision evaluate` CLI command | `--config`, `--checkpoint`, `--split` | Console summary & report files | evaluator | `tests/smoke/test_cli_smoke.py` |

#### Acceptance Criteria (Definition of Done)
1. `python -m railway_detection vision evaluate --config configs/vision.yaml --checkpoint <path>` computes all metrics against the held-out test split and writes structured outputs to `experiments/vision/<run_id>/evaluation/`.
2. Failure analysis correctly isolates false positives and class confusions on fixture test sets.
3. Unit tests verify metric calculations against known synthetic ground truth / prediction pairs.

---

### PHASE 4: Video Inference & Temporal Evidence Layer
*Status: READY TO EXECUTE AFTER PHASE 2*

#### Goal
Bridge static frame-level detections and temporal reasoning. Ingest video files, extract sequential frames, perform inference with camera source tagging, and apply temporal filtering (confidence smoothing, consecutive-frame confirmation, persistence, loss tolerance, and timeout).

#### Technical Requirements
1. **Video Ingestion & Frame Extraction:**
   * Ingest video streams/files (`.mp4`, `.avi`, `.mov`) with configurable sampling frame rate (FPS) or stride (e.g., sample at 5–10 Hz instead of native 30 Hz for efficiency).
   * Preserve source frame index, original timestamp in seconds ($t \ge 0.0$), and logical camera identifier (`camera_1` for approach side, `camera_2` for departure side).
2. **Temporal Evidence Engine (`TemporalEvidenceBuffer`):**
   * Maintain a sliding time-window buffer of raw `EvidenceRecord`s per camera source.
   * **Confidence Smoothing:** Apply moving-average or exponential smoothing over active detections.
   * **Consecutive-Frame Confirmation:** A viewpoint class (`front`, `side`, `rear`) is upgraded from `LOW_CONFIDENCE` / `PROVISIONAL` to `CONFIRMED` only if detected in $N$ consecutive frames or within $W$ seconds (configurable, e.g., $N=3$ frames, $W=0.5\text{s}$).
   * **Detection Persistence & Miss Tolerance:** If a confirmed train is briefly occluded or dropped for $\le M$ frames (e.g., $M=2$ frames / $0.4\text{s}$), maintain active occupancy state with a decayed persistence score.
   * **Evidence Expiry / Timeout:** If no detection occurs for $> \tau_{\text{expiry}}$ seconds (configurable, e.g., $3.0\text{s}$), mark observation as expired/absent.
3. **Output Interface:**
   * Emit timestamped, normalized `EvidenceRecord` instances containing filtered detections and source availability status.
   * **Critical Safety Rule:** The temporal engine only emits *evidence*; it **must not** make gate open/close decisions.

#### File-by-File Specification Table
| File Path | Purpose | Inputs | Outputs | Dependencies | Tests |
|---|---|---|---|---|---|
| `src/railway_detection/vision/video.py` | Sequential video frame extractor | Video file path, target FPS | Frame generator `(frame_idx, timestamp_s, ndarray)` | cv2 / Pillow | `tests/unit/test_video_reader.py` |
| `src/railway_detection/vision/temporal.py` | Confidence smoothing & confirmation buffer | Raw frame detections, timestamps, camera ID | Filtered `EvidenceRecord` stream | stdlib | `tests/unit/test_temporal_evidence.py` |
| `src/railway_detection/vision/inference.py` | High-level inference pipeline for images/videos | Video path, detector, config | `predictions.jsonl`, evidence stream | video, temporal | `tests/integration/test_video_inference.py` |

#### Acceptance Criteria (Definition of Done)
1. Video inference processes sample video clips and emits chronological `EvidenceRecord` sequences with exact source IDs and timestamps.
2. Temporal buffer correctly rejects single-frame false-positive spikes when confirmation threshold $N > 1$.
3. Temporal buffer bridges brief 1–2 frame detection dropouts without dropping confirmed status.
4. Unit tests verify timestamp ordering, out-of-order timestamp rejection, smoothing mathematics, and buffer expiry.

---

### PHASE 5: Layer B Event-Data Ingestion & Synchronization
*Status: READY TO IMPLEMENT VIA FIXTURES; REAL DATA INGESTION READY UPON COLLECTION*

#### Goal
Design and implement the data ingestion interface for Layer B synchronized train-passage event bundles (`event_001/camera_1.mp4`, `camera_2.mp4`, `audio.wav`). Support minimal field metadata, synchronization offset calculation, and geometry records.

#### Technical Requirements
1. **Event Bundle Layout:**
   ```text
   data/raw/events/event_001/
   ├── camera_1.mp4               # Approach-side video
   ├── camera_2.mp4               # Departure-side video
   ├── audio.wav                  # Synchronized audio (or extracted from mp4)
   ├── metadata.json              # Minimal field metadata
   ├── geometry.json              # Crossing geometry reference
   └── labels/
       └── event_labels.json      # Ground truth reference event timestamps
   ```
2. **Minimal Metadata Schema (`contracts.LayerBEvent`):**
   * `event_id`: Unique string identifier (e.g., `event_001`).
   * `crossing_id`: String identifier or `None`.
   * `direction`: `approach_to_departure`, `departure_to_approach`, or `unknown`.
   * `weather`: `clear`, `rain`, `fog`, `overcast`, or `None`.
   * `lighting`: `day`, `night`, `dusk`, `dawn`, or `None`.
   * `sync_method`: `audiovisual_clap`, `common_clock`, `landmark_event`, or `uncalibrated`.
   * `sync_offset_s`: Estimated alignment offset in seconds (float).
   * `sync_uncertainty_s`: Estimated alignment uncertainty in seconds (float).
3. **Synchronization & Alignment Engine:**
   * Time normalization: Master clock $t_{\text{master}} = t_{\text{source}} + \Delta t_{\text{offset}}$.
   * Alignment uncertainty guard: If `sync_uncertainty_s` > configured tolerance (e.g., $> 0.5\text{s}$), flag event with `timing_uncertainty_high: true` and exclude from primary millisecond-level timing endpoints.
4. **Mock Event Generator:** Build high-fidelity synthetic Layer B event fixtures to allow complete development of downstream fusion and simulation phases before real events are collected in the field.

#### File-by-File Specification Table
| File Path | Purpose | Inputs | Outputs | Dependencies | Tests |
|---|---|---|---|---|---|
| `src/railway_detection/data/layer_b.py` | Ingest and validate Layer B event bundles | Event directory path | `LayerBEvent`, source media handles | contracts | `tests/unit/test_layer_b_loader.py` |
| `src/railway_detection/data/sync.py` | Apply synchronization offsets and master clock | Raw source streams, offset metadata | Synchronized multimodal stream generator | stdlib | `tests/unit/test_sync_alignment.py` |
| `tests/fixtures/mock_events.py` | Generate synthetic 2-camera + audio event fixtures | Event parameters | Mock event bundle directory on disk | cv2, wave | `tests/unit/test_mock_events.py` |

#### Acceptance Criteria (Definition of Done)
1. `LayerBLoader` loads valid event bundles, validates existence of media files, and parses metadata without errors.
2. Synchronizer accurately aligns two asynchronous streams given an offset $\Delta t$.
3. Missing metadata fields gracefully serialize to `None` / `null` without crashing.
4. Test suite verifies synchronization alignment, missing file handling, and malformed label validation.

---

### PHASE 6: Audio Pipeline
*Status: READY TO IMPLEMENT MODULAR ARCHITECTURE VIA FIXTURES; REAL MODEL TRAINING WHEN AUDIO IS COLLECTED*

#### Goal
Build a modular audio processing and classification pipeline for train horn detection (`train_horn` vs `non_train_sound`). Provide feature extraction, baseline model, inference engine, and an isolated synthetic noise-robustness testing harness.

#### Technical Requirements
1. **Audio Validation & Preprocessing:**
   * Ingest audio files (`.wav`, `.flac`, `.mp3`) or extract audio tracks from video files via standard libraries.
   * Standardize to configured format: **16,000 Hz, Single-Channel (Mono), 16-bit PCM WAV**.
   * Split continuous audio into sliding analysis windows (e.g., $1.0\text{s}$ to $2.0\text{s}$ duration with $50\%$ overlap / $0.5\text{s}$ hop).
2. **Feature Extraction:**
   * Compute Log-Mel Spectrograms (e.g., 64 or 128 mel bins, FFT window 25ms, hop length 10ms) or MFCCs.
3. **Acoustic Classifier Backend:**
   * Implement modular `AudioClassifier` interface.
   * Baseline model: Lightweight 2D CNN on mel-spectrograms or 1D CNN / Random Forest on spectral features.
   * Output: Calibrated probability $P(\text{train\_horn}) \in [0.0, 1.0]$.
4. **Synthetic Noise Robustness Harness:**
   * Implement SNR mixer: $s_{\text{mixed}}(t) = s_{\text{signal}}(t) + \alpha \cdot s_{\text{noise}}(t)$ to achieve exact target SNRs ($+10\text{dB}, +5\text{dB}, 0\text{dB}, -5\text{dB}, -10\text{dB}$).
   * Evaluate classifier degradation curves under diverse noise sources (traffic, crowd, heavy rain, wind).
5. **Acoustic Safety Boundary:**
   * Audio horn detection is **supporting evidence only**.
   * The audio pipeline outputs timestamped `EvidenceRecord` with `modality: Modality.AUDIO`. It never executes gate logic.

#### File-by-File Specification Table
| File Path | Purpose | Inputs | Outputs | Dependencies | Tests |
|---|---|---|---|---|---|
| `src/railway_detection/audio/preprocessor.py` | Audio resampling, mono conversion, windowing | Raw audio files / streams | Standardized audio chunks (ndarray) | numpy, wave/scipy | `tests/unit/test_audio_preprocessor.py` |
| `src/railway_detection/audio/features.py` | Mel-spectrogram / MFCC extraction | Audio chunks | 2D feature tensors | numpy / scipy | `tests/unit/test_audio_features.py` |
| `src/railway_detection/audio/model.py` | Acoustic horn classifier baseline | Feature tensors | Horn probability $P(\text{horn})$ | PyTorch / scikit-learn | `tests/unit/test_audio_model.py` |
| `src/railway_detection/audio/noise_mixer.py` | Mix background noise at precise SNR levels | Clean audio, noise audio, target SNR | Augmented audio clip | numpy | `tests/unit/test_noise_mixer.py` |

#### Acceptance Criteria (Definition of Done)
1. Audio preprocessor converts arbitrary sample rates to 16kHz mono WAV chunks reproducibly.
2. Noise mixer produces verifiable SNR mixtures without numerical clipping or distortion.
3. Audio classifier outputs valid probabilities and structured `EvidenceRecord`s.
4. Unit tests verify audio loading, feature tensor dimensions, SNR calculations, and empty/silent audio handling.

---

### PHASE 7: Multimodal Evidence Interface & Fusion Engine
*Status: READY TO EXECUTE*

#### Goal
Create a unified, typed multimodal evidence interface that ingests filtered evidence from Camera 1, Camera 2, and the Microphone. Maintain per-source evidence health and status states (`AVAILABLE`, `UNAVAILABLE`, `LOW_CONFIDENCE`, `CONFIRMED`) and strictly decouple evidence representation from decision logic.

#### Technical Requirements
1. **Source Status Matrix:**
   * Maintain an explicit health and availability register for each configured sensor:
     * `camera_1` (Approach): `is_available`, `last_heartbeat_s`, `active_detections` (`front`, `side`).
     * `camera_2` (Departure): `is_available`, `last_heartbeat_s`, `active_detections` (`side`, `rear`).
     * `microphone_1` (Audio): `is_available`, `last_heartbeat_s`, `horn_confidence`.
2. **Evidence Qualification State:**
   * Categorize source evidence into discrete qualification levels:
     * `UNAVAILABLE`: Stream lost, corrupted frame, or heartbeat timeout.
     * `NO_DETECTION`: Source active, no train features observed.
     * `LOW_CONFIDENCE`: Detections present but below threshold or unconfirmed across time.
     * `CONFIRMED`: High-confidence, temporally consistent detection meeting persistence criteria.
3. **Safety Invariants for Multimodal Evidence:**
   * **No Uncalibrated ORing:** Do NOT implement `front OR side OR rear OR horn` as a raw boolean.
   * **Explicit Missingness:** Distinguish between a source reporting zero confidence vs. a source being offline/unavailable.
   * **Temporal Alignment:** Evidence records are synchronized to the master timeline with explicit latency tracking.

#### File-by-File Specification Table
| File Path | Purpose | Inputs | Outputs | Dependencies | Tests |
|---|---|---|---|---|---|
| `src/railway_detection/fusion/source_tracker.py` | Track sensor availability & heartbeats | Incoming raw evidence timestamps | Sensor health & availability matrix | stdlib | `tests/unit/test_source_tracker.py` |
| `src/railway_detection/fusion/collector.py` | Aggregate & synchronize multi-source evidence | Evidence records from Cam 1, Cam 2, Mic | Unified `MultimodalEvidenceSnapshot` | evidence contracts | `tests/unit/test_evidence_collector.py` |

#### Acceptance Criteria (Definition of Done)
1. `EvidenceCollector` aggregates asynchronous camera and audio records into coherent time-sliced snapshots.
2. Dropping a camera stream immediately transitions that source's status to `UNAVAILABLE` without corrupting other active sources.
3. Unit tests verify multi-source collation, out-of-order timestamp handling, and status categorization.

---

### PHASE 8: Decision Engine
*Status: READY TO EXECUTE*

#### Goal
Implement a transparent, rule-based, deterministic decision engine. The engine consumes unified multimodal evidence snapshots and the current system state, evaluates safety-oriented rules, and outputs state transition directives with complete explainability traces.

#### Technical Requirements
1. **Rule Evaluation Protocol:**
   * Every decision must be traceable to a specific declarative rule ID, evidence references, and rationale string.
2. **Core Policy Rules:**
   * **Rule R-APPROACH (Approach Confirmation):**
     * *Condition:* Camera 1 confirms `front` OR Camera 1 confirms `side` OR (Camera 1 reports `LOW_CONFIDENCE front` AND Microphone confirms `train_horn`).
     * *Action:* Direct transition toward warning and gate closure.
   * **Rule R-OCCUPANCY (Crossing Occupancy):**
     * *Condition:* Camera 1 or Camera 2 confirms `side` OR persistent train detection active.
     * *Action:* Maintain closed gate; block opening.
   * **Rule R-DEPARTURE (Departure Indication):**
     * *Condition:* Camera 2 confirms `rear` AND Camera 1 detects no `front` or `side`.
     * *Action:* Transition to `TRAIN_DEPARTING` / `REAR_CONFIRMED`.
   * **Rule R-CLEARANCE (Positive Clearance):**
     * *Condition:* `REAR_CONFIRMED` satisfied AND clear dwell time $\tau_{\text{dwell}}$ elapsed AND Camera 2 reports crossing clear AND no new approach evidence on Camera 1.
     * *Action:* Authorize `CROSSING_CLEAR` → `GATE_OPENING`.
   * **Rule R-GUARD-OPENING (Opening Guard Invariant):**
     * *Condition:* Loss of detection, missing evidence, camera failure, or audio silence alone.
     * *Action:* **NEVER authorize opening.** Maintain conservative state or transition to `FAULT_FAIL_SAFE`.
3. **Explainability Contract:**
   * Emit `DecisionRecord` detailing `timestamp_s`, `previous_state`, `resulting_state`, `rule_id`, `explanation`, and `evidence_references`.

#### File-by-File Specification Table
| File Path | Purpose | Inputs | Outputs | Dependencies | Tests |
|---|---|---|---|---|---|
| `src/railway_detection/fusion/rules.py` | Declarative decision rules & condition predicates | `MultimodalEvidenceSnapshot`, system state | Rule match result & directive | stdlib | `tests/unit/test_decision_rules.py` |
| `src/railway_detection/fusion/decision_engine.py` | Orchestrate rule evaluation & audit logging | Evidence snapshots, current state | `DecisionRecord` | rules, contracts | `tests/unit/test_decision_engine.py` |

#### Acceptance Criteria (Definition of Done)
1. Decision engine evaluates all defined rules deterministically for any given evidence snapshot.
2. Disappearance of all detections while in `TRAIN_PRESENT` results in holding closed state or safe fault, never an opening directive.
3. Complete explainability string and rule ID are attached to every emitted decision.
4. Unit tests verify every rule predicate, conflict resolution, and invariant enforcement.

---

### PHASE 9: State Machine & Crossing Simulation
*Status: READY TO EXECUTE*

#### Goal
Implement the formal research crossing simulation state machine and simulated gate controller. Advance simulation time, execute state transitions, enforce timing parameters, and generate chronological event logs.

#### Technical Requirements
1. **Formal System States:**
   ```text
   IDLE ──► TRAIN_APPROACHING ──► WARNING ──► GATE_CLOSING ──► TRAIN_PRESENT
                                                                    │
   IDLE ◄── GATE_OPENING ◄── CROSSING_CLEAR ◄── REAR_CONFIRMED ◄─── CROSSING_OCCUPIED / TRAIN_DEPARTING
     ▲                                                              │
     └─────────────────────── FAULT_FAIL_SAFE ◄─────────────────────┘
   ```
2. **Independent Simulated Gate Model:**
   * Gate states: `OPEN`, `CLOSING`, `CLOSED`, `OPENING`.
   * Timing parameters (configurable in `simulation.yaml`):
     * `warning_dwell_s` (e.g., $2.0\text{s}$): Duration of audible/visual warning before gate starts moving.
     * `gate_closing_s` (e.g., $4.0\text{s}$): Time required for physical gate to close.
     * `gate_opening_s` (e.g., $4.0\text{s}$): Time required for physical gate to open.
     * `clearance_dwell_s` (e.g., $2.0\text{s}$): Safety buffer after tail clearance before opening begins.
3. **Simulation Replay Runner:**
   * Feed time-stamped evidence streams into the state machine step-by-step ($\Delta t$).
   * Display real-time console status dashboard showing active states, gate position, source confidence meters, and event log.
   * Export execution trace to `simulation_log.json` and `simulation_log.csv`.

#### File-by-File Specification Table
| File Path | Purpose | Inputs | Outputs | Dependencies | Tests |
|---|---|---|---|---|---|
| `src/railway_detection/simulation/state_machine.py` | Pure deterministic state machine | `DecisionRecord`, current state, elapsed time | New `SystemState`, state transition event | stdlib | `tests/unit/test_state_machine.py` |
| `src/railway_detection/simulation/gate_model.py` | Model physical gate movement & timing | Gate commands, elapsed $\Delta t$ | `GateState`, angle/percentage | stdlib | `tests/unit/test_gate_model.py` |
| `src/railway_detection/simulation/runner.py` | Replay simulation scenarios & log outputs | Multimodal evidence stream, configs | Simulation trace files, summary metrics | state_machine, gate_model | `tests/integration/test_simulation_runner.py` |

#### Acceptance Criteria (Definition of Done)
1. Normal train passage sequence executes from `IDLE` through `GATE_OPENING` back to `IDLE` with correct timing delays.
2. Direct prohibited transitions (e.g., `IDLE → GATE_OPENING`, `TRAIN_PRESENT → IDLE`) raise runtime exceptions or are blocked.
3. Simulation runner executes a complete recorded or mock scenario and writes verifiable `simulation_log.json`.
4. 100% of state transitions and gate timing dynamics covered by unit tests.

---

### PHASE 10: Failure Injection Engine
*Status: READY TO EXECUTE*

#### Goal
Build a deterministic, reproducible failure injection harness that perturbs clean multimodal evidence streams to evaluate system resilience under degraded conditions.

#### Technical Requirements
1. **Supported Failure Modes:**
   * `camera_1_failure`: Drop Camera 1 video stream completely at timestamp $t_{\text{start}}$.
   * `camera_2_failure`: Drop Camera 2 video stream completely at timestamp $t_{\text{start}}$.
   * `front_missed`: Suppress `front` detections on Camera 1 (simulate heavy fog / dark / occlusion).
   * `side_missed`: Suppress `side` detections during crossing passage.
   * `rear_missed`: Suppress `rear` detections on departure camera.
   * `audio_failure`: Audio stream unavailable or corrupted.
   * `audio_false_positive`: Inject high-confidence horn detections during clear/empty track intervals.
   * `temporary_dropout`: Suppress detections for a burst of $K$ seconds (e.g., $1.5\text{s}$).
   * `stale_evidence`: Freeze timestamps to simulate network/thread hang.
   * `out_of_order_evidence`: Invert timestamp order of incoming frames.
   * `conflicting_evidence`: Camera 1 reports approaching front while Camera 2 reports departing rear simultaneously.
   * `new_train_while_opening`: Inject fresh approaching front detection on Camera 1 while gate is in `GATE_OPENING`.
2. **Reproducibility:**
   * All injections must be configurable via YAML scenario files and parameterized by seed, onset timestamp, duration, and severity.
   * Original clean stream and perturbed stream must both be logged for comparative evaluation.

#### File-by-File Specification Table
| File Path | Purpose | Inputs | Outputs | Dependencies | Tests |
|---|---|---|---|---|---|
| `src/railway_detection/simulation/failure_injector.py` | Perturb clean evidence streams deterministically | Clean `EvidenceRecord` stream, fault spec | Faulted `EvidenceRecord` stream, fault log | random | `tests/unit/test_failure_injector.py` |
| `configs/simulation.yaml` | Define named failure scenarios | User configs | Scenario configurations | YAML | `tests/unit/test_config.py` |

#### Acceptance Criteria (Definition of Done)
1. Every defined failure scenario executes reproducibly with identical seeds producing identical perturbed streams.
2. Injected failures trigger the expected conservative simulation response (e.g., holding gate closed or entering `FAULT_FAIL_SAFE`) without crashing.
3. New train during opening immediately aborts opening and transitions back toward closing/warning.
4. Unit tests verify every single fault injection type independently.

---

### PHASE 11: Experiment Framework (Baselines B0–B7)
*Status: READY TO IMPLEMENT RUNNER; EVALUATION OF B0-B7 USES SYNTHETIC FIXTURES UNTIL LAYER B ARRIVES*

#### Goal
Build an automated experiment runner that executes standardized baseline comparisons (B0 through B7) on identical held-out event sets with immutable logging and central registry recording.

#### Technical Requirements
1. **Standard Baseline Matrix (B0–B7):**
   * **B0:** Single-Camera Vision (`camera_1`), independent frame detections, no temporal logic.
   * **B1:** Single-Camera Vision (`camera_1`) with temporal filtering.
   * **B2:** Two-Camera Vision (`camera_1` + `camera_2`) with temporal filtering, no state machine.
   * **B3:** Two-Camera Vision with temporal filtering and state machine (no audio).
   * **B4:** Audio-Only horn detector (evaluated on acoustic detection & false alarms).
   * **B5:** Two-Camera Vision + Audio fusion without state-aware policy.
   * **B6:** Full Proposed System: Two-Camera Vision + Audio + Temporal Engine + State Machine.
   * **B7:** Robustness & Failure Ablations: B6 with individual sensor channels removed or faulted.
2. **Experiment Execution & Registry:**
   * Unique experiment directory: `experiments/system/<experiment_id>/`.
   * Save `resolved_config.yaml`, `run_manifest.json`, raw predictions, simulation traces, and computed metrics.
   * Append summary record to `results/experiment_registry.jsonl`.
   * CLI: `python -m railway_detection experiment run --config configs/experiments/<exp>.yaml`.

#### File-by-File Specification Table
| File Path | Purpose | Inputs | Outputs | Dependencies | Tests |
|---|---|---|---|---|---|
| `src/railway_detection/experiments/runner.py` | Orchestrate B0–B7 baseline execution | Experiment config, event manifests | Experiment run directory, metrics summary | simulation, fusion, vision | `tests/integration/test_experiment_runner.py` |
| `src/railway_detection/experiments/registry.py` | Manage append-only experiment registry | Run summaries | `results/experiment_registry.jsonl` | stdlib | `tests/unit/test_registry.py` |

#### Acceptance Criteria (Definition of Done)
1. Experiment runner executes baselines B0 through B7 across test scenarios without manual intervention.
2. Every run generates an immutable manifest linking code commit, config, dataset hash, seed, and outputs.
3. Unit and integration tests verify baseline execution against mock event datasets.

---

### PHASE 12: Ablation Studies & Sensitivity Analysis
*Status: READY TO EXECUTE AFTER PHASE 11*

#### Goal
Implement automated ablation studies to isolate and quantify the marginal contribution of each system component: viewpoint classes (`front`, `side`, `rear`), sensor modalities (vision vs audio), temporal smoothing, and state-machine guards.

#### Technical Requirements
1. **Ablation Dimensions:**
   * **Viewpoint Ablation:** Train & evaluate without `front` (measure approach detection delay), without `side` (measure occupancy tracking stability), and without `rear` (measure departure confirmation failure).
   * **Modality Ablation:** Compare Vision-Only (B3) vs Audio-Only (B4) vs Fused (B6).
   * **Temporal Ablation:** Compare raw frame decisions (B0) vs smoothed decisions (B1).
   * **Policy Ablation:** Compare naive threshold ORing (B5) vs state-aware guarded transitions (B6).
2. **Output Reports:** Generate comparative Markdown tables and paired differential metric plots.

#### File-by-File Specification Table
| File Path | Purpose | Inputs | Outputs | Dependencies | Tests |
|---|---|---|---|---|---|
| `src/railway_detection/experiments/ablation.py` | Automated ablation suite runner | Base config, ablation parameter grid | `ablation_summary.json`, `ablation_table.md` | experiment runner | `tests/integration/test_ablation.py` |

#### Acceptance Criteria (Definition of Done)
1. Ablation suite runs the complete matrix and exports cleanly formatted comparative tables.
2. Tests verify parameter isolation: changing one ablation parameter does not alter unrelated components.

---

### PHASE 13: Expanded ~4,000-Image Dataset Integration (Dataset V2)
*Status: BLOCKED UNTIL EXPANDED DATASET ARRIVES — SPECIFICATION READY*

#### Goal
Integrate the future ~4,000-image dataset (Dataset V2) seamlessly without requiring any architectural changes or source code rewrites.

#### Technical Requirements
1. **Intake & Revalidation:**
   * Place new images into `data/raw/vision/images/` and labels into `data/raw/vision/labels/`.
   * Update `data/metadata/vision_metadata.json` with geographical crossing IDs across 30+ locations.
   * Run validation: `python -m railway_detection data validate --config configs/vision.yaml`.
2. **Group-Aware Split Regeneration:**
   * Run `python -m railway_detection data split --config configs/vision.yaml`.
   * Ensure strict crossing-level isolation (unseen crossings in validation and test partitions).
3. **Retraining & Comparative Benchmark:**
   * Train models on Dataset V2: `python -m railway_detection vision train --config configs/vision.yaml`.
   * Compute comparative metrics: **Dataset V1 (~1,300 images) vs. Dataset V2 (~4,000 images)**.
   * Evaluate generalization improvements on adverse weather slices (rain, fog, night).

#### Acceptance Criteria (Definition of Done)
1. Zero modifications to Python source code in `src/railway_detection/` are required to process Dataset V2.
2. Comparative report `v1_vs_v2_comparison.md` is generated, showing delta in mAP, per-class recall, and generalization.

---

### PHASE 14: Final Layer B System Evaluation (20–30 Real Events)
*Status: BLOCKED UNTIL 20–30 LAYER B EVENTS ARE COLLECTED — SPECIFICATION READY*

#### Goal
Evaluate the full proposed multimodal framework (B6) and all baselines on 20–30 real-world, synchronized train-passage events collected across Bangladeshi level-crossings.

#### Technical Requirements
1. **Partition Protocol:**
   * Split 20–30 events by crossing location into: Development/Tuning Events (e.g., 60%), Validation Events (e.g., 20%), and Held-Out Test Events (e.g., 20%).
   * **Strict Freeze:** All model weights, confidence thresholds, temporal windows, and state rules must be frozen BEFORE evaluating on held-out test events.
2. **Primary Research Endpoints:**
   * **Event-Level Missed-Train Rate:** Evaluable events where system fails to trigger warning/closure before the deadline $\div$ Total evaluable train events.
   * **Premature-Opening Rate:** Evaluable events where gate opens before ground-truth tail clearance $\div$ Total events with observable tail clearance.
3. **Secondary Research Endpoints:**
   * Warning Lead Time distribution (mean, median, 95% CI).
   * Late-Closure Rate.
   * False Alarms per hour of evaluable non-train recording.
   * Departure Confirmation Latency.
4. **Statistical Uncertainty Reporting:**
   * Given small sample size (20–30 events), report exact point estimates with 95% bootstrap / Wilson confidence intervals.
   * Explicitly state sample size limitations in all summaries; do not make broad nationwide generalization claims.

#### Acceptance Criteria (Definition of Done)
1. Full evaluation script executes across all held-out Layer B events and outputs `system_evaluation_report.md`.
2. Both primary endpoints (missed-train rate, premature-opening rate) are prominently reported with confidence intervals.
3. Excluded/unobservable events are explicitly listed with reasons.

---

### PHASE 15: Research Results, Figures, Tables & Reproducibility
*Status: READY TO EXECUTE (TOOLING) / FINAL POPULATION UPON EXPERIMENT COMPLETION*

#### Goal
Generate publication-quality figures, LaTeX/Markdown tables, and comprehensive reproducibility bundles for the research paper.

#### Technical Requirements
1. **Automated Figure Generation:**
   * Dataset class distribution and split distribution charts.
   * Training / validation loss and mAP curves.
   * Viewpoint confusion matrices and Precision-Recall curves.
   * Audio classification SNR degradation curves.
   * Chronological state transition timeline & gate trajectory diagrams.
   * Safety vs. efficiency tradeoff curves (Missed Trains vs. False Alarms).
2. **Automated Table Generation:**
   * Dataset Composition & Metadata Table.
   * Vision Detection Baseline & Per-Class Metric Table (`front`, `side`, `rear`).
   * Audio Classification & Noise Robustness Table.
   * System-Level B0–B7 Baseline Comparison Table.
   * Failure Injection Resilience & Invariant Verification Table.
3. **Reproducibility Verification:**
   * One-command end-to-end verification script: `python -m railway_detection report generate --config configs/experiments/full_study.yaml`.

#### File-by-File Specification Table
| File Path | Purpose | Inputs | Outputs | Dependencies | Tests |
|---|---|---|---|---|---|
| `src/railway_detection/evaluation/tables.py` | Generate Markdown/LaTeX comparison tables | Experiment registry, `metrics.json` | `tables/*.md`, `tables/*.tex` | tabulate / pandas | `tests/unit/test_table_generator.py` |
| `src/railway_detection/evaluation/plots.py` | Generate publication-ready figures | Simulation logs, metric files | `figures/*.png`, `figures/*.pdf` | matplotlib, seaborn | `tests/unit/test_plot_generator.py` |

#### Acceptance Criteria (Definition of Done)
1. Running report generation produces all required figures and tables in `results/figures/` and `results/tables/`.
2. All figures are high-resolution ($\ge 300\text{ DPI}$) with clear legends, units, and sample sizes.
3. Every reported number links to an immutable run manifest and experiment registry entry.

---

## 5. Milestone Schedule & Acceptance Criteria

| Milestone | Target Scope | Immediate / Blocked | Core Acceptance Criteria |
|---|---|---|---|
| **M0** | Engineering Foundation | **COMPLETE** | 31+ unit/integration tests pass; `ruff` and `mypy` clean; CLI entry point working. |
| **M1** | Dataset V1 Pipeline | **IMMEDIATE** | Validation and group-aware splitting of ~1,300 images produces `report.json` and split manifests. |
| **M2** | Vision Baseline Training | **IMMEDIATE** | YOLO adapter trains on Dataset V1 splits; saves `best.pt` checkpoint to `experiments/vision/<run_id>/`. |
| **M3** | Vision Evaluation & Slices | **IMMEDIATE** | Evaluation generates mAP, per-class PR curves, confusion matrix, and failure analysis slices. |
| **M4** | Video Inference & Temporal Layer | **IMMEDIATE** | Video inference pipeline extracts frames and emits temporally smoothed/confirmed `EvidenceRecord`s. |
| **M5** | Layer B Ingestion (Mock Fixtures) | **IMMEDIATE** | Layer B loader and synchronizer parse event bundles and synchronize multi-camera streams. |
| **M6** | Audio Pipeline & SNR Harness | **IMMEDIATE** | 16kHz audio preprocessor, feature extractor, classifier baseline, and noise mixer pass all unit tests. |
| **M7** | Multimodal Evidence Interface | **IMMEDIATE** | Evidence collector collates multi-sensor inputs into unified health/qualification snapshots. |
| **M8** | Decision Engine | **IMMEDIATE** | Rule-based engine evaluates safety rules deterministically and emits explainable decision records. |
| **M9** | State Machine & Simulation | **IMMEDIATE** | Crossing state machine and gate simulator replay events and log chronological state transitions. |
| **M10** | Failure Injection Harness | **IMMEDIATE** | Failure injector reproduces all 12 fault scenarios; verifies conservative system responses. |
| **M11** | Experiment Runner & Baselines | **IMMEDIATE** | Runner executes B0–B7 baselines and records runs to `results/experiment_registry.jsonl`. |
| **M12** | Ablation Suite & Reporting | **IMMEDIATE** | Automated ablation runner and table/figure generation export publication artifacts. |
| **M13** | Dataset V2 Integration | **BLOCKED (Data)** | ~4,000 images validated, split, retrained, and evaluated without modifying Python code. |
| **M14** | Final Layer B System Evaluation | **BLOCKED (Data)** | 20–30 real train passage events evaluated on primary endpoints with confidence intervals. |

---

## 6. DeepSeek V4 Pro Implementation Workflow & Quality Protocol

To ensure flawless code quality, DeepSeek V4 Pro must follow this strict incremental workflow for **every single task**:

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│                        DEEPSEEK V4 PRO TASK WORKFLOW                           │
└────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
                   [Step 1: Inspect Code & Existing Tests]
                                        │
                                        ▼
                  [Step 2: Implement One Atomic File/Unit]
                                        │
                                        ▼
                    [Step 3: Write Comprehensive Unit Tests]
                                        │
                                        ▼
                    [Step 4: Execute Local Test Suite]
                         $ pytest tests/unit/test_xxx.py
                                        │
                                        ▼
                   [Step 5: Run Linter & Static Type Checks]
                         $ ruff check src tests
                         $ mypy src
                                        │
                                        ▼
                    [Step 6: Inspect Output Artifacts / Logs]
                                        │
                                        ▼
                      [Step 7: Commit Changes to Git]
                         $ git commit -m "feat(module): description"
                                        │
                                        ▼
                     [Step 8: Move to Next Sequential Task]
```

### Prohibited Actions for DeepSeek V4 Pro
*   ❌ **DO NOT** modify large portions of the codebase simultaneously without running intermediate tests.
*   ❌ **DO NOT** bypass failing tests with `xfail` or `# type: ignore` unless strictly documented and justified.
*   ❌ **DO NOT** hardcode dataset counts, class IDs, paths, or thresholds in source code.
*   ❌ **DO NOT** import heavy ML libraries (e.g., PyTorch, Ultralytics) inside lightweight modules (`data/contracts.py`, `fusion/evidence.py`).
*   ❌ **DO NOT** execute gate opening logic on missing evidence or audio signals.

---

## 7. Git Commit & Versioning Strategy

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

*   `feat(data): add dataset manifest generator and perceptual duplicate candidate checker`
*   `feat(vision): implement Ultralytics YOLO training and checkpoint management adapter`
*   `feat(vision): add temporal evidence buffer with confidence smoothing and persistence`
*   `feat(audio): implement 16kHz audio windowing and mel-spectrogram feature extractor`
*   `feat(fusion): build multimodal evidence collector and source availability tracker`
*   `feat(fusion): implement safety-oriented rule-based decision engine with explanation traces`
*   `feat(simulation): add crossing state machine and physical gate timing simulation model`
*   `feat(simulation): build deterministic failure injection engine for sensor dropouts`
*   `feat(experiments): implement B0-B7 baseline experiment runner and central registry`
*   `test(vision): add unit tests for temporal confirmation and detection dropouts`
*   `test(simulation): add invariant tests blocking opening transitions without clearance`
*   `docs(execution): update execution plan and record architectural decisions`

---

## 8. Immediate Next Action: The First 10 Coding Tasks for DeepSeek V4 Pro

When DeepSeek V4 Pro begins implementation, it must execute the following 10 tasks in exact numerical sequence:

1. **Task 1 (`feat(data)`):** Implement `src/railway_detection/data/manifest.py` to generate normalized `dataset_manifest.jsonl` from validated raw images and metadata. Add unit test `tests/unit/test_manifest.py`.
2. **Task 2 (`feat(vision)`):** Define the abstract vision adapter interface in `src/railway_detection/vision/adapter.py`. Add unit test `tests/unit/test_vision_adapter.py`.
3. **Task 3 (`feat(vision)`):** Implement `src/railway_detection/vision/yolo_adapter.py` supporting dataset descriptor formatting and Ultralytics YOLO execution. Add unit test `tests/unit/test_yolo_adapter.py`.
4. **Task 4 (`feat(vision)`):** Implement `src/railway_detection/vision/trainer.py` and connect `python -m railway_detection vision train` in CLI. Add integration test with mock weights.
5. **Task 5 (`feat(vision)`):** Implement `src/railway_detection/vision/evaluator.py` computing mAP@50, mAP@50:95, per-class PR curves, and confusion matrix. Add unit test `tests/unit/test_vision_evaluator.py`.
6. **Task 6 (`feat(vision)`):** Implement `src/railway_detection/vision/failure_analysis.py` for automated error slicing across weather and viewpoints. Add unit test `tests/unit/test_failure_analysis.py`.
7. **Task 7 (`feat(vision)`):** Implement sequential video frame reader in `src/railway_detection/vision/video.py`. Add unit test `tests/unit/test_video_reader.py`.
8. **Task 8 (`feat(vision)`):** Implement `src/railway_detection/vision/temporal.py` (temporal confidence smoothing, confirmation window, persistence). Add unit test `tests/unit/test_temporal_evidence.py`.
9. **Task 9 (`feat(data)`):** Implement `src/railway_detection/data/layer_b.py` and `src/railway_detection/data/sync.py` for Layer B event bundle ingestion. Add unit tests and synthetic event fixtures in `tests/fixtures/mock_events.py`.
10. **Task 10 (`feat(audio)`):** Implement `src/railway_detection/audio/preprocessor.py` (16kHz mono WAV conversion) and `src/railway_detection/audio/noise_mixer.py` (precise SNR mixing). Add unit tests.
