# Master Implementation Roadmap

## Railway Crossing Multimodal Train Detection Research System

**Project status:** Scientific protocol revision complete; research-system implementation has not started.  
**Scope:** Research software and simulation only. This roadmap does not authorize or imply physical gate control, Raspberry Pi deployment, real-time guarantees, or safe use at live railway crossings.  
**Purpose:** This is the implementation roadmap. [`RESEARCH_PROTOCOL_V2.md`](RESEARCH_PROTOCOL_V2.md) is the scientific source of truth for research claims, data requirements, ground truth, system evaluation, and experimental design. Follow its P0/P1 gates before the relevant implementation phases.

---

## 1. Research objective and success boundary

### Research question

> On synchronized, event-labeled recordings from held-out represented crossings, does a two-camera, audio-assisted, temporal state policy change event-level railway-crossing detection outcomes relative to fair simpler baselines?

### What this project will build

- A reproducible three-class vision-detection pipeline: `front`, `side`, and `rear`.
- A reproducible binary audio-classification pipeline: `train_horn` and `non_train_sound`.
- A configurable temporal-evidence layer.
- A transparent rule-based multimodal decision engine.
- A state-machine-based software simulation of gate decisions.
- Evaluation, failure-injection, ablation, robustness, and graph-generation tooling.

### What this project will not claim or build in the initial phase

- A certified or physically safe railway-control system.
- Direct gate-controller, camera, microphone, Raspberry Pi, cloud, database, or microservice integration.
- Measured real-time performance without target hardware and an explicit benchmark.
- Research results before experiments have been run on real held-out data.
- Literature novelty claims without a separately verified literature review.

### Definition of completion

The project foundation is complete only when a newly supplied, correctly formatted dataset can be validated, split, trained, evaluated, inferred upon, simulated, compared in experiments, and reported through documented commands without restructuring the repository. System-level research completion additionally requires the synchronized Layer B event dataset and independent event ground truth specified in `RESEARCH_PROTOCOL_V2.md`; it cannot be inferred from Layer A image results or passing software tests.

---

## 2. Non-negotiable engineering and research rules

1. **Dataset facts come from files.** Never hard-code expected image, clip, crossing, weather, class, or split counts.
2. **Classes come from configuration or dataset metadata.** Code must not assume YOLO IDs `0/1/2` mean front/side/rear.
3. **Avoid leakage.** Split by crossing/location or session/group, never randomly by near-identical video frame when grouping data exists.
4. **Opening is evidence-driven.** A missing detection is never evidence that the crossing is clear.
5. **Closing is conservative.** When sufficient approach/train evidence occurs, transition toward a simulated closed gate; uncertainty while a train may be present must not cause an open-gate transition.
6. **Models provide evidence; the state machine makes decisions.** Keep these components independent and testable.
7. **All important behavior is configured.** No confidence threshold, timeout, SNR level, model choice, class mapping, seed, or path may live as an unexplained magic number in code.
8. **Every experiment is traceable.** Save immutable configuration, environment, dataset identity, seed, model identity, source code revision when available, outputs, and timestamps.
9. **Mock data stays mock data.** It is allowed for smoke tests only, must be visibly labeled, and must never enter research result tables.
10. **Start simple.** Use a YOLO-compatible detector, a baseline audio model, temporal rules, and explicit rule-based fusion before considering learned fusion or more complex architectures.

---

## 3. Existing repository and document ownership

The repository currently contains research documentation only. Preserve it; do not replace it with generated implementation outputs.

| Document | Ownership during implementation |
|---|---|
| `README.md` | Entry point, setup, workflow, safety/scope disclaimer, and links to current commands/results. |
| `docs/RESEARCH_CONCEPT.md` | Research scope, conceptual architecture, assumptions, and open scientific questions. |
| `docs/RESEARCH_DECISIONS.md` | Append-only architectural/research decision record. Record material decisions before implementing them. |
| `docs/EXPERIMENT_PLAN.md` | Scientific experiment design and status. Update after a planned experiment is concretely implemented or run. |
| `docs/IDEA_LOG.md` | Capture and disposition new ideas before they reshape implementation scope. |
| `docs/ANNOTATION_GUIDELINE.md` | To be created; definitive labeling and bounding-box guidance for annotators and reviewers. |
| This file | Ordered build roadmap, interfaces, quality gates, deliverables, and execution checklist. |

When this roadmap conflicts with a documented research decision, do not silently choose one. Add a new dated decision record explaining the change, update the affected document, and then implement.

---

## 4. Target architecture

```text
Dataset / metadata
    ├── validator ──> validation report and dataset statistics
    ├── split generator ──> immutable train / validation / test manifests
    ├── vision pipeline ──> detections by camera and timestamp
    └── audio pipeline ──> horn evidence by timestamp

Vision + audio evidence
    └── temporal evidence layer
            └── decision engine
                    └── isolated crossing state machine
                            └── simulator, event log, system metrics, figures

Experiment configuration + run metadata
    └── experiment registry, per-run artifacts, comparison tables
```

### Camera roles

| Logical source | Configurable role | Primary evidence |
|---|---|---|
| `camera_1` | `approach_side` | `front`, `side` |
| `camera_2` | `departure_side` | `side`, `rear` |
| `microphone_1` | audio source | `train_horn` confidence |

Physical geometry, including the provisional 5–6 metre spacing, belongs in scenario/config metadata only. It must not affect core logic as an implicit constant.

### State and gate model

Use explicit enums rather than free-text states. Initial states are:

`IDLE` → `TRAIN_APPROACHING` → `WARNING` → `GATE_CLOSING` → `TRAIN_PRESENT` → `CROSSING_OCCUPIED` → `TRAIN_DEPARTING` → `REAR_CONFIRMED` → `CROSSING_CLEAR` → `GATE_OPENING` → `IDLE`

`FAULT_FAIL_SAFE` is reachable from any active train-related state when configured fault rules require it. It represents a simulated safe/closed behavior, not a claim of physical safety.

The gate state must be modeled independently (for example: `OPEN`, `CLOSING`, `CLOSED`, `OPENING`) so that timing and state transitions can be evaluated.

---

## 5. Planned repository layout

Create this progressively. Empty runtime-output directories should contain `.gitkeep` only when version control requires it; data, trained models, and generated results must not be committed unless explicitly intended.

```text
Train_automation/
├── configs/
│   ├── vision.yaml
│   ├── audio.yaml
│   ├── fusion.yaml
│   ├── simulation.yaml
│   ├── experiments/
│   └── schemas/                    # optional configuration schemas
├── data/
│   ├── raw/
│   │   ├── vision/
│   │   └── audio/
│   ├── interim/                    # generated, never hand-edited
│   ├── processed/
│   │   ├── vision/
│   │   └── audio/
│   ├── metadata/
│   └── splits/
├── src/railway_detection/
│   ├── __init__.py
│   ├── cli/
│   ├── config/
│   ├── data/
│   ├── vision/
│   ├── audio/
│   ├── fusion/
│   ├── simulation/
│   ├── evaluation/
│   └── utils/
├── scripts/                        # thin backward-compatible command wrappers only
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── smoke/
├── experiments/
│   ├── vision/
│   ├── audio/
│   ├── multimodal/
│   └── system/
├── models/                         # trained/exported model artifacts; ignored by default
├── results/
│   ├── dataset_validation/
│   ├── figures/
│   ├── tables/
│   ├── logs/
│   ├── failure_analysis/
│   ├── simulations/
│   └── experiment_registry.jsonl
├── docs/
├── pyproject.toml
├── requirements.txt                # only if project convention needs it
├── README.md
└── .gitignore
```

### Module responsibilities

| Module | Responsibility | Must not do |
|---|---|---|
| `data` | Dataset discovery, validation, metadata parsing, grouping, manifest creation, statistics. | Train models or decide gate state. |
| `vision` | YOLO-compatible dataset adaptation, training, evaluation, model loading, image/video inference. | Know gate-transition policy. |
| `audio` | Audio validation, preprocessing, feature extraction, training, evaluation, inference, optional noise mixing. | Know camera-specific state rules. |
| `fusion` | Typed evidence records, smoothing, temporal confirmation, configured fusion policy, state machine. | Load raw images/audio or call hardware. |
| `simulation` | Replay evidence/scenarios, inject faults, advance a simulated clock, create event logs. | Embed model-specific thresholds. |
| `evaluation` | Metrics, error/failure analysis, tables, plots, aggregate comparisons. | Invent missing labels or results. |
| `config` | Parse, validate, freeze, and resolve paths for YAML configuration. | Hide defaults outside versioned configs. |
| `cli` | Stable user-facing commands and clear errors. | Hold business logic. |
| `utils` | Logging, hashing, reproducibility capture, I/O helpers. | Become a catch-all for unrelated logic. |

---

## 6. Data contracts before implementation

Define these contracts in typed models/dataclasses (or an equivalent validated schema) before model code. Store serialized records as JSON/JSONL/CSV where appropriate.

### 6.1 Vision dataset contract

Minimum required per image:

| Field | Requirement |
|---|---|
| `image_id` | Stable unique identifier, not merely a basename. |
| `image_path` | Path relative to configured dataset root. |
| `label_path` | Annotation path or explicit negative-image marker. |
| `split_group_id` | Crossing/location/session group when available. |
| `class_mapping` | Versioned mapping from source IDs to semantic class names. |

Optional, strongly recommended metadata: `crossing_id`, `session_id`, `video_id`, `frame_index`, `captured_at`, `camera_id`, `weather`, `lighting`, `occlusion`, `distance_band`, annotation-review status, and provenance.

Support a standard YOLO label format initially. The import adapter must expose a normalized internal annotation format rather than spreading YOLO-specific parsing throughout the project.

### 6.2 Audio dataset contract

Minimum required per clip:

| Field | Requirement |
|---|---|
| `clip_id` | Stable unique identifier. |
| `audio_path` | Path relative to configured audio root. |
| `label` | Semantic label from configured mapping. |
| `split_group_id` | Source recording/session group when available. |

Optional metadata: sample rate, duration, channel count, crossing/session, recording device, weather, noise type, estimated SNR, and provenance.

### 6.3 Inference evidence contract

Every adapter must emit normalized records, even when the source is an image, video, mock stream, or later live stream abstraction.

```json
{
  "timestamp_s": 123.45,
  "source_id": "camera_1",
  "modality": "vision",
  "available": true,
  "detections": [
    {
      "label": "front",
      "confidence": 0.91,
      "bbox_xyxy": [10, 20, 300, 400]
    }
  ],
  "metadata": {"frame_id": "..."}
}
```

Audio evidence should use the same envelope with an audio classification prediction. Invalid, delayed, unavailable, and empty observations must be representable without abusing a confidence value.

### 6.4 Decision output contract

At each simulated time step, record:

- timestamp and scenario/run ID;
- raw and temporally processed evidence;
- active configuration version;
- previous and resulting system state;
- previous and resulting gate state;
- transition reason(s) and rule identifier(s);
- fault status and availability of each component.

This record is the source for event logs, explainability, system-level metrics, and regression tests.

---

## 7. Configuration and reproducibility standards

Use human-readable YAML configuration files with typed validation. A command must copy the resolved configuration into its output directory before work begins.

### Required configuration groups

| File | Minimum contents |
|---|---|
| `configs/vision.yaml` | Dataset adapter/root, class mapping, model family/name, image size, epochs, batch size, learning rate when supported, device, workers, augmentation, thresholds, seed, output name. |
| `configs/audio.yaml` | Dataset adapter/root, label mapping, resample rate, normalization/segmentation, feature settings, model choice, optimizer/training values, seed, threshold. |
| `configs/fusion.yaml` | Source roles, allowed labels per source, evidence thresholds, temporal windows, weights/rules, fault policy, all opening/closing criteria. |
| `configs/simulation.yaml` | Scenarios, simulated timing, gate timing, streams/events, default fault injections, output location. |
| `configs/experiments/*.yaml` | One immutable experiment specification: input runs/models, protocol, conditions, metrics, output name. |

### Configuration rules

- Use relative paths resolved from the project root or config file, then store absolute resolved paths in the run manifest.
- Validate every config before expensive work begins.
- Reject an unknown class name, invalid threshold range, inconsistent source role, missing file, or opening rule without positive rear/clearance criteria.
- Support command-line overrides only when each override is written into the frozen run configuration.
- Define a seed policy for Python, NumPy, PyTorch, and framework-specific RNGs where installed; record limits to determinism from device/framework behavior.

### Required run manifest

Each training, evaluation, simulation, and experiment run must write a manifest containing at least:

- run ID, timestamp, command, and resolved config;
- source-code revision (git commit when available; otherwise explicit `unavailable`);
- Python/package versions, OS, device, and available accelerator information;
- dataset path, manifest version, sample counts, and a practical content/manifest hash;
- random seed;
- model checkpoint identity and checksum where applicable;
- input artifact references and output artifact paths;
- mock-data indicator.

Append a summary record to `results/experiment_registry.jsonl`; never overwrite historical run records.

---

## 8. Implementation phases and quality gates

Complete a phase only after its quality gate passes. Mark a phase as blocked rather than working around a missing dataset, dependency, or scientific decision.

### Phase 0 — Repository foundation and contracts

**Goal:** Establish a maintainable Python project without implementing research claims.

Tasks:

- Create the planned package layout, dependency manifest, formatting/lint/test configuration, and `.gitignore`.
- Choose a supported Python version and document it.
- Add configuration parser/validation, project-root/path utilities, structured logging, typed domain models, and reproducibility manifest writer.
- Create small, clearly marked synthetic fixtures for unit/integration/smoke tests only.
- Add a CLI command help surface and conventional non-zero exit handling.
- Create `docs/ANNOTATION_GUIDELINE.md` from the approved front/side/rear and box rules.

Deliverables:

- Installable package and documented environment setup.
- Valid example configs that point only to fixtures/mock inputs.
- First unit tests for config validation and domain models.

Quality gate:

- Static checks and unit tests pass in a clean environment.
- `--help` works for each planned command.
- A smoke run creates an isolated output directory and manifest marked `mock_data: true`.

### Phase 1 — Vision data ingestion, validation, and split generation

**Goal:** Make real image data auditable before any training occurs.

Tasks:

- Implement the YOLO-format import adapter and normalized manifest generator.
- Verify image existence/readability and detect corrupted/unreadable images.
- Verify label existence according to configured negative-image policy.
- Validate label syntax, finite numeric values, class IDs, normalized box bounds, positive width/height, and boxes outside image bounds.
- Detect duplicate basenames and report duplicate/near-duplicate candidates separately. Perceptual hashing may be optional/configurable due to runtime.
- Calculate actual class counts, image sizes, annotation counts, and metadata distributions.
- Parse and validate grouping metadata; warn prominently when no crossing/session grouping exists.
- Generate deterministic group-aware train/validation/test manifests, verify group disjointness, and report class balance.
- Refuse training on critical validation errors unless an explicit, recorded override policy permits exclusions.

Outputs:

```text
results/dataset_validation/<run_id>/
├── report.json
├── report.md
├── invalid_samples.csv
├── duplicate_candidates.csv
├── dataset_manifest.jsonl
├── class_distribution.png
├── split_distribution.png
└── run_manifest.json

data/splits/<split_id>/
├── train.jsonl
├── val.jsonl
├── test.jsonl
└── split_summary.json
```

Quality gate:

- Test fixtures demonstrate each validator failure mode and a valid-data pass.
- A group-aware split has no group intersection across train/validation/test.
- If grouping metadata is absent, output contains a clear leakage warning and requires an explicit config acknowledgement to create a fallback split.
- Dataset statistics are calculated from manifests, not entered manually.

### Phase 2 — Vision training, evaluation, inference, and error analysis

**Goal:** Provide a configurable YOLO-compatible baseline without binding the whole project to a single version.

Tasks:

- Implement a framework adapter interface: prepare dataset, train, validate, evaluate, export/load, infer.
- Implement an Ultralytics-compatible adapter as the first supported backend. Keep model family/name in config.
- Generate backend-specific dataset descriptors only from immutable split manifests.
- Create unique experiment output directories; never overwrite prior runs.
- Save framework logs/checkpoints plus normalized metrics and artifacts.
- Evaluate only against the held-out test manifest after model selection is completed on validation data.
- Report precision, recall, F1, mAP@50, mAP@50:95, per-class precision/recall/AP, confusion matrix, PR/F1 curves when backend support permits.
- Implement image/video inference that emits the normalized evidence contract with source ID and timestamps.
- Implement failure analysis: missed trains, wrong viewpoint, false positives, low-confidence cases, and metadata slices (rain/fog/night/occlusion/distance) only when labels exist.

Outputs per run:

```text
experiments/vision/<run_id>/
├── resolved_config.yaml
├── run_manifest.json
├── training_logs/
├── checkpoints/
├── metrics.json
├── metrics.md
├── figures/
├── predictions.jsonl
├── evaluation/
└── failure_analysis/
```

Quality gate:

- Mock smoke training/evaluation runs are clearly marked and separated from research outputs.
- A real dataset run cannot silently evaluate on training images.
- Model selection uses validation data only; test evaluation is an explicit final action.
- Test suite validates class mapping, output normalization, threshold behavior, missing/corrupt model errors, and artifact isolation.

### Phase 3 — Audio data, baseline model, and noise robustness

**Goal:** Build an independently testable horn-evidence pipeline.

Tasks:

- Implement audio discovery/validation: readability, duration, sample rate/channels, labels, group metadata, clip duplication candidates.
- Add configurable resampling, mono conversion, normalization, segmentation, feature extraction (mel spectrogram as initial baseline), and deterministic split generation by recording/session group.
- Implement at least one understandable baseline model. Begin with a simple configured approach (for example CNN on mel features or MFCC/SVM); do not add pretrained/complex models until justified by experiment.
- Implement training, held-out evaluation, inference, calibration/threshold selection on validation data, and normalized audio evidence outputs.
- Implement a separate optional noise-mixing test protocol with configured SNR levels and held-out clean clips/noise sources. Keep synthetic-noise results separate from clean and real-noise evaluations.
- Report precision, recall, F1, false-positive rate, false-negative rate, confusion matrix, ROC/PR curves where meaningful, and SNR results.

Quality gate:

- Audio data and group split validation have coverage equivalent to vision validation.
- Noise mixer verifies duration, clipping prevention, reproducible noise selection, and SNR calculation.
- Audio failures/unavailability create explicit unavailable evidence, never fabricated confidence.
- No audio performance wording is added to research docs before an actual held-out run.

### Phase 4 — Temporal evidence and rule-based fusion

**Goal:** Convert intermittent model outputs into transparent, configurable evidence without making gate decisions in model adapters.

Tasks:

- Implement per-source/per-label confidence smoothing and consecutive-frame/segment confirmation.
- Model temporary loss, evidence expiry, maximum age, source unavailability, timestamp disorder, and delayed evidence.
- Define a declarative initial fusion policy for approach, occupancy, departure, uncertainty, and safety-oriented conservative rules.
- Ensure source-role awareness: Camera 1 front/side and Camera 2 side/rear are configured evidence sources, not assumptions hard-coded in the model.
- Write transition explanations showing which evidence and rule caused each decision.
- Implement ablation switches for front-only, front+side, front+side+rear, vision-only, audio-only, vision+audio, and full state-aware rules.

Quality gate:

- Unit tests cover smoothing, confirmation, expiry, loss, malformed input, ordering, and source availability.
- Tests prove that an audio event alone does not bypass opening safeguards.
- Each fusion output is explainable from versioned rules and evidence history.

### Phase 5 — State machine and gate-decision simulation

**Goal:** Demonstrate safety-oriented system behavior using only software simulation.

Tasks:

- Implement a pure, deterministic state-machine transition function that takes current state, gate state, time, processed evidence, and config and returns a typed decision.
- Implement explicit transition guards and simulated timing for warning, closing, closed, opening, and clear states.
- Require positive departure evidence (`rear` in the configured departure role), temporal confirmation, and a configured crossing-clear condition before opening can begin.
- Add safety-oriented conservative policies for evidence degradation/faults while a train may be present; record policy rationale in outputs.
- Build a terminal simulation/replay runner for synthetic scenarios and recorded prediction streams.
- Display current state, gate state, camera/audio confidence, availability, fault status, and chronological event timeline.
- Write JSON and CSV event logs and calculate system metrics from them.

Mandatory behavioral tests:

| Scenario | Required expected behavior |
|---|---|
| `rear` disappears or all detections disappear | Gate does **not** immediately open. |
| Front/side approach evidence persists | System moves toward warning and simulated closure according to timing. |
| Rear confirmation + temporal condition + clear condition | System may move toward opening according to timing. |
| Train evidence while in `IDLE` | The state machine may not move directly to an open-gate state. |
| Camera/audio loss while train may be present | System does not transition to opening based on loss alone. |
| Malformed evidence input | Safe validation failure or explicit fault behavior; no undefined transition. |

Quality gate:

- State transition table has complete tests, including prohibited transitions.
- Normal scenario and each key adverse scenario create deterministic event logs from the same fixture/config/seed.
- Simulator makes no hardware/network calls.

### Phase 6 — Failure injection and system-level evaluation

**Goal:** Quantify how the simulated decision system behaves when evidence sources degrade or fail.

Tasks:

- Implement composable, seeded injections: source unavailable, detector unavailable, confidence reduction, false positive, false negative, temporary frame loss, delayed evidence, camera obstruction, and weather-tag-conditioned degradation.
- Preserve the original evidence stream and emit a separate faulted stream with fault metadata.
- Add scenario configs including `normal`, `front_failure`, `front_side_failure`, `vision_failure_audio_only`, `audio_failure`, `camera_1_failure`, and additional combinations only when explicitly defined.
- Implement system metrics: detection success, missed-train rate, false-alarm rate, false-positive/negative rate, arrival detection time, warning lead time, departure confirmation time, premature-opening rate, correct closure/opening rate, and recovery after component failure.
- Flag false negatives and premature opening as safety-critical in tables and figures. Do not collapse them into one aggregate accuracy score.

Quality gate:

- Injection tests confirm both intended changed behavior and unaffected evidence components.
- Reports distinguish simulation scenario failures from ML model failures.
- Results contain run/model/dataset references sufficient to reproduce each row.

### Phase 7 — Experiment runner, comparisons, and publication artifacts

**Goal:** Make research comparisons routine, consistent, and auditable.

Tasks:

- Implement a runner that resolves an experiment config, validates prerequisite artifacts, executes or reuses runs, and writes a complete comparison record.
- Implement tables in CSV, JSON, and Markdown for vision, audio, fusion, robustness, failure injection, cross-crossing generalization, and system performance.
- Implement reusable plotting with data-driven labels, color palette config, accessible legends, high-resolution output, and no fake/missing values.
- Produce dataset distribution, split distribution, training/validation curves, confusion matrix, PR/F1/ROC where appropriate, per-class/model comparisons, failures, weather slices, SNR curves, and state-transition/system metrics.
- Require the plot/table generator to state sample counts, excluded/unknown metadata, confidence interval method when used, and run IDs.
- Maintain an experiment status register: planned, blocked, ready, running, completed, invalidated, superseded.

Quality gate:

- A comparison fails clearly if inputs are incomparable (different test split, missing dataset identity, incompatible metric definition) unless explicitly designated as exploratory.
- All summary tables trace back to saved normalized metrics and manifests.
- Figures can be regenerated from stored inputs/configurations.

### Phase 8 — Documentation, handoff, and final research execution

**Goal:** Make the project usable by another researcher and ready for credible interpretation.

Tasks:

- Update README with installation, dataset placement, command sequence, expected outputs, troubleshooting, and scope disclaimer.
- Update `RESEARCH_DECISIONS.md`, `EXPERIMENT_PLAN.md`, and `IDEA_LOG.md` as decisions/experiments change.
- Create a dataset card and model cards from actual run outputs; label assumptions and limitations.
- Add a reproducibility guide, result interpretation guide, and known-limitations section.
- Re-run a clean-environment test/smoke workflow.
- When final data arrives, run the full workflow in Section 12 and record every deviation from plan.

Quality gate:

- A new collaborator can reproduce a selected run from documented inputs and config.
- No documentation states unmeasured accuracy, latency, real-world safety, or novelty claims as fact.

---

## 9. Dataset arrival protocol

Do not begin real training immediately when annotation arrives. Complete this intake checklist first.

1. Place vision files under the configured `data/raw/vision/` root and audio files under `data/raw/audio/`; do not rename/move source files until provenance is recorded.
2. Copy or create metadata manifests in `data/metadata/` with stable sample and group IDs.
3. Check the annotation export/version, class names/IDs, negative-image policy, and labeling tool/source.
4. Run dataset validation and fix or explicitly exclude critical errors through a recorded policy.
5. Review class distribution, image/clip quality, duplicate candidates, and missing metadata.
6. Confirm crossing/session grouping; if unavailable, choose a documented fallback split strategy and add its limitation to the research documentation.
7. Generate and freeze the split manifests. Do not hand-edit split files after training begins.
8. Record the dataset version/hash and archive the validation report with the experiment inputs.
9. Only then launch baseline training.

### Vision annotation guideline requirements

`docs/ANNOTATION_GUIDELINE.md` must state:

- `front`: leading locomotive/head/nose is clearly identifiable facing the camera, including a partly side-visible front.
- `side`: body is predominantly side-on and neither endpoint is the dominant identifiable viewpoint.
- `rear`: last coach/end is clearly identifiable facing the camera.
- One box represents one continuous visible train target; do not create a box per coach.
- Side boxes should be reasonably tight and should not intentionally include unrelated scenery, sky, ground, track, or grass merely to include distant coaches.
- A box may touch an image edge when the train naturally extends beyond the frame.
- Ambiguous cases must follow a documented review/escalation process. Do not add a fourth class without a decision record and an experiment.

---

## 10. Experiment roadmap

Every experiment requires a dedicated config, frozen input manifests, stated hypothesis, predefined primary/secondary metrics, validity checks, and a result record. Do not automatically run experiments whose model/data dependencies are absent.

| ID | Experiment | Inputs | Primary comparison | Status prerequisite |
|---|---|---|---|---|
| D-EXP-1 | Dataset audit and deduplication | Raw vision/audio + metadata | Dataset composition and duplicate candidates | Dataset available |
| D-EXP-2 | Location/session-aware split | Validated manifest | Group-disjoint split and balance | D-EXP-1 |
| V-EXP-1 | Single-view/front-only baseline | Vision split | Detection baseline | D-EXP-2 |
| V-EXP-2 | Three-class vision baseline | Vision split | Per-class performance and viewpoint confusion | V-EXP-1 or independently declared baseline |
| A-EXP-1 | Audio horn baseline | Audio split | Horn vs non-train classification | Validated audio split |
| M-EXP-1 | Vision + audio baseline | Aligned/replayable evidence | Vision-only vs fused metrics | V-EXP-2 + A-EXP-1 |
| DE-EXP-1 | State-machine correctness | Labeled/replayable sequences | Correctness and transition latency | Evidence streams + state labels/scenarios |
| DE-EXP-2 | Failure injection | Baseline evidence streams | Safe behavior/recovery by fault | DE-EXP-1 |
| DE-EXP-3 | Fusion policy comparison | Same evidence/test protocol | Transparent fusion-rule ablation | M-EXP-1 |
| R-EXP-1 | Weather/lighting robustness | Metadata-tagged held-out data | Per-condition degradation | Sufficient real metadata |
| R-EXP-2 | Audio SNR robustness | Held-out audio + noise | Metrics by configured SNR | A-EXP-1 |
| R-EXP-3 | Cross-crossing generalization | Group-held-out test split | Unseen-crossing performance | D-EXP-2 |

### Ablation matrix

Use one shared evaluation protocol and identical comparable test sequences wherever possible.

| Variant | Active evidence/policy | Purpose |
|---|---|---|
| A | Front only | Approach baseline. |
| B | Front + side | Occupancy contribution. |
| C | Front + side + rear | Departure-evidence contribution. |
| D | Vision only | Multiview visual baseline. |
| E | Audio only | Independent modality baseline. |
| F | Vision + audio | Multimodal contribution without full state policy. |
| G | Full state-aware multimodal system | Complete proposed simulated framework. |

All variants must report both ordinary ML/system scores and safety-critical outcomes. A higher aggregate score never compensates for an unreported premature-opening or missed-train outcome.

---

## 11. Testing and quality strategy

### Test levels

| Level | Purpose | Examples |
|---|---|---|
| Unit | Pure small components, fast and deterministic. | Class mapping, box validation, thresholds, temporal smoothing, transition guards. |
| Integration | Multiple modules with fixture data. | Dataset manifest → split → YOLO descriptor; prediction stream → fusion → event log. |
| Smoke | End-user commands with tiny labeled mock data. | Validate, train/evaluate mock baseline, infer, simulate, plot. |
| Regression | Preserve discovered bug/failure behavior. | Rear disappearance must not trigger opening; source loss follows the conservative simulated policy. |
| Manual review | Human inspection of artifacts and scientific validity. | Annotation ambiguity, duplicate candidates, failure-image ranking, plot readability. |

### Minimum automated coverage targets

- Vision/audio class mapping rejects missing, duplicate, and unknown semantic names.
- Dataset validators catch nonexistent/corrupt files, malformed labels, invalid boxes, unknown classes, duplicated basenames, and absent grouping metadata.
- Splitter produces reproducible group-disjoint results for a fixed seed.
- Inference adapters emit normalized typed evidence for empty and non-empty predictions.
- Temporal layer handles persistence, smoothing, expiry, temporary loss, timestamps, and unavailable sources.
- State machine permits valid transitions and blocks every unsafe/direct opening transition.
- Failure injector is reproducible and composable.
- Plot/table routines fail clearly when required inputs are absent and never generate fabricated placeholder values.
- CLI failures produce useful messages and non-zero exit status.

### CI/quality commands to add during Phase 0

Choose tools compatible with the final dependency stack, but the standard should include format checking, linting, type checking, unit/integration tests, and a smoke test. Pin or constrain dependency versions sufficiently for reproducibility, then record resolved versions in every run manifest.

---

## 12. Intended user workflow and stable CLI

Implement a package CLI as the primary interface; lightweight script wrappers may remain for convenience. Exact option names may evolve, but these workflows must stay stable.

```bash
# 0. Inspect expected config and command options
python -m railway_detection --help

# 1. Validate and describe the supplied datasets
python -m railway_detection data validate --config configs/vision.yaml
python -m railway_detection audio validate --config configs/audio.yaml

# 2. Create deterministic group-aware splits after reviewing validation
python -m railway_detection data split --config configs/vision.yaml
python -m railway_detection audio split --config configs/audio.yaml

# 3. Train and evaluate baselines
python -m railway_detection vision train --config configs/vision.yaml
python -m railway_detection vision evaluate --config configs/vision.yaml --checkpoint <best-checkpoint>
python -m railway_detection audio train --config configs/audio.yaml
python -m railway_detection audio evaluate --config configs/audio.yaml --checkpoint <best-checkpoint>

# 4. Run reusable inference
python -m railway_detection vision infer --config configs/vision.yaml --source <image-or-video> --source-id camera_1
python -m railway_detection audio infer --config configs/audio.yaml --source <audio-file> --source-id microphone_1

# 5. Replay the decision system and test faults
python -m railway_detection simulate run --config configs/simulation.yaml --scenario normal
python -m railway_detection simulate run --config configs/simulation.yaml --scenario front_failure

# 6. Run only a declared experiment after prerequisites exist
python -m railway_detection experiment run --config configs/experiments/<experiment>.yaml

# 7. Regenerate tables and figures from stored experiment artifacts
python -m railway_detection report generate --config configs/experiments/<experiment>.yaml
```

CLI requirements:

- Print the resolved output directory and run ID at start and completion.
- Never overwrite a prior run by default; an explicit resume mode must preserve provenance.
- Fail before expensive work for bad configuration, missing dependency, invalid dataset, incompatible checkpoint, or unresolved input artifact.
- Expose `--dry-run` for commands that can validate plan/inputs without executing training.

---

## 13. Output and reporting standards

### Required tables

- Vision model comparison and per-class metrics.
- Audio model comparison and threshold/calibration metrics.
- Multimodal/ablation comparison.
- Failure-injection scenarios and expected-vs-observed system behavior.
- Weather/lighting and cross-crossing generalization slices when metadata/sample size permits.
- Audio SNR robustness.
- System-level performance, emphasizing missed trains and premature openings.

### Required figures

1. Dataset class distribution.
2. Dataset split/group distribution.
3. Training and validation curves.
4. Precision/recall and F1 curves.
5. Confusion matrices.
6. PR and ROC curves where valid for the task.
7. Per-class and per-model comparisons.
8. Ranked failure analysis samples.
9. Weather/lighting performance.
10. Audio SNR performance.
11. System-state transitions/timeline and scenario outcomes.

### Artifact rules

- Save raw metrics as JSON, table-ready data as CSV/JSON, human summaries as Markdown, and figures as high-resolution PNG and/or vector PDF/SVG where supported.
- Every table/figure must include or link to run IDs, input split/model identity, metric definition, and sample count.
- Use `not_available`, not zero, for unavailable values. Explain why values are unavailable.
- Keep test-set results immutable once reported; corrections require a new run and explanation.

---

## 14. Risks, assumptions, and decision triggers

| Risk/assumption | Required mitigation or trigger |
|---|---|
| Missing crossing/session metadata | Warn before split; use documented fallback only with limitation stated. Seek metadata before strong generalization claims. |
| Near-duplicate video frames | Detect/report candidate duplicates and enforce grouping to avoid leakage. |
| Class ambiguity | Annotation guideline + review queue; reconsider class scheme only through documented evidence. |
| Imbalanced front/side/rear data | Report counts; use configured sampling/augmentation only on training data; preserve honest held-out distribution. |
| Sparse night/rain/fog samples | Report insufficient sample sizes; do not claim robustness from tiny slices. |
| Horn false positives in Bangladeshi traffic | Use realistic negatives and report false-positive rate; audio remains supporting evidence, not an unconditional open/close shortcut. |
| Vision/audio timestamps unaligned | Use an explicit synchronization/replay policy and record tolerance; do not silently pair unrelated observations. |
| No sequence state labels | Start with synthetic and manually curated replay scenarios for software correctness; label limitations in system-performance claims. |
| Dataset/model drift | Version/hash data, configs, checkpoints, and outputs. |
| Over-engineering | Keep first implementation rule-based/modular; require an experiment and decision record before learned fusion/transformers/new modalities. |
| Physical safety interpretation | Maintain scope disclaimers in README, simulator output, reports, and any presentation/publication. |

---

## 15. Decision log entries expected during implementation

Before or during the relevant phase, add a dated entry in `docs/RESEARCH_DECISIONS.md` for:

1. Python/package and configuration-validation approach.
2. Exact normalized dataset manifest schema and negative-image policy.
3. Group-metadata format and fallback split policy.
4. First supported YOLO-compatible backend and version strategy.
5. Audio baseline architecture and preprocessing defaults.
6. Temporal confirmation/expiry defaults and how they are tuned.
7. Initial fusion rules and opening-clearance condition.
8. Failure-injection semantics and system-metric definitions.
9. Any change to viewpoint taxonomy, camera roles, scope, or experimental protocol.

Every decision should include rationale, alternatives, evidence, status, and conditions that would cause reconsideration, following the existing decision-log format.

---

## 16. Definition-of-done checklists

### Foundation done

- [ ] Package layout, configurations, typed data contracts, structured logging, manifests, and CLI exist.
- [ ] Annotation guideline exists and matches research concept.
- [ ] Tests and mock smoke data are separate from research data/results.
- [ ] Installation and development commands are documented.

### Vision pipeline done

- [ ] Validation produces machine- and human-readable reports plus figures.
- [ ] Group-aware split manifests are deterministic and disjoint.
- [ ] Configurable YOLO-compatible training/evaluation/inference runs create unique reproducible artifacts.
- [ ] Metrics, class-specific results, and automated failure analysis are generated from actual predictions.

### Audio pipeline done

- [ ] Audio validation, grouped split, configurable preprocessing/model, evaluation, and inference exist.
- [ ] Optional noise-mixing study is isolated, reproducible, and reported separately.

### Fusion and simulation done

- [ ] Temporal evidence, fusion policy, state machine, gate model, and event logs are independently testable.
- [ ] Opening requires positive configured departure and clearance evidence.
- [ ] Core fault scenarios and all unsafe-transition regressions are tested.

### Experiment/reporting done

- [ ] Ablations, robustness, failure injection, and cross-crossing protocols are runnable only with declared prerequisites.
- [ ] Tables/figures link to immutable artifacts and can be regenerated.
- [ ] Experiment registry contains every research run.

### Research handoff done

- [ ] A fresh collaborator can follow the workflow from dataset placement to reports.
- [ ] Documentation distinguishes assumptions, mock tests, simulation outcomes, and real-data results.
- [ ] No unsupported safety, deployment, latency, novelty, or performance claims remain.

---

## 17. Ordered build checklist

Use this as the implementation sequence. Do not skip a quality gate merely to reach model training faster.

1. [ ] Read the current research documents and record any necessary implementation decisions.
2. [ ] Establish package/tooling/configuration/reproducibility foundation (Phase 0).
3. [ ] Create and review the annotation guideline.
4. [ ] Build vision manifest, validation, statistics, and group-aware split logic (Phase 1).
5. [ ] Build the YOLO-compatible vision adapter and mock smoke pipeline (Phase 2).
6. [ ] Build vision inference and failure analysis (Phase 2).
7. [ ] Build audio ingestion, baseline, and optional SNR harness (Phase 3).
8. [ ] Build normalized evidence models, temporal rules, and rule-based fusion (Phase 4).
9. [ ] Build the state machine, gate model, replay simulator, and event log (Phase 5).
10. [ ] Add failure injection and system-level metrics (Phase 6).
11. [ ] Add experiment runner, comparison tables, and figures (Phase 7).
12. [ ] Complete docs, handoff, clean-environment verification, and dataset-arrival workflow (Phase 8).
13. [ ] When final data arrives, follow the intake protocol and run planned experiments in dependency order.
14. [ ] Interpret results conservatively; update decisions, experiment status, limitations, and reports from evidence only.

---

## 18. Immediate next action

The next implementation task is **Phase 0: Repository foundation and contracts**. Do not create model-specific training code until the configuration/data-contract and validation foundation is in place. If the final annotated dataset arrives earlier, store it under the planned raw-data roots and execute the dataset-arrival protocol before changing the roadmap or launching training.

---

## 19. Change-control protocol

When changing this roadmap:

1. State the reason and affected phase/interfaces.
2. Update `RESEARCH_DECISIONS.md` if the change is material.
3. Update `EXPERIMENT_PLAN.md` if it changes a protocol, hypothesis, metric, or prerequisite.
4. Update `IDEA_LOG.md` when the change begins as a new untested idea.
5. Preserve past results and configs; never edit them to match a later plan.
6. Revise this document and README so the next implementer has one coherent path forward.

This keeps the repository a research laboratory: reproducible, measurable, traceable, and comparable.
