# Dataset Specification V2

## Two-Layer Data Design

**Core rule:** Layer A develops perception models. Layer B evaluates the multimodal temporal/system claim. They must not be confused.

## 1. Layer A — vision image dataset

**Purpose:** Develop and evaluate train viewpoint/object-detection models.

Expected scale is approximately 4,000 real images from 30+ crossings, but these are targets, not facts. The validator must calculate actual counts. Expected conditions include day, night, rain, and fog only if actual metadata verifies them.

Required content:

- train images with `front`, `side`, and `rear` labels under `ANNOTATION_GUIDELINE_V2.md`;
- explicit no-train/hard-negative images;
- sample, source, crossing, session/video, camera, and annotation provenance when available;
- group hierarchy sufficient to prevent related data split leakage.

Permitted claims: held-out object/viewpoint detection performance within represented data. Not permitted: multimodal temporal/gate-policy reliability.

## 2. Layer B — synchronized train-passage event dataset

**Purpose:** Evaluate temporal evidence, two-camera evidence, audio support, state machine, and event-level policy outcomes.

Each event should contain:

```text
event_id/
├── camera_1.mp4
├── camera_2.mp4
├── audio.wav
├── metadata.json
├── geometry.json
└── labels/event_labels.json
```

Requirements:

- one identifiable train-passage event, source timestamps, synchronization method/uncertainty;
- camera roles/orientation/visible-zone geometry;
- independent event labels including crossing entry and, for the premature-opening endpoint, observable tail clearance;
- no-train context for false-alarm exposure;
- group hierarchy `crossing → session → recording → event → frame/audio window`;
- source availability and data-quality flags.

Layer B must be the source of all B0–B7 system comparisons. If only one modality is available for a sequence, it may contribute to the relevant unimodal analysis but not to a full multimodal comparison.

## 3. Partition rules

Assign all descendants of a crossing/session/recording/event group to a single partition. Prefer crossings unseen in training for the final test partition. Never split adjacent video frames or audio windows randomly. Keep held-out test data unavailable for threshold, calibration, policy, or model selection.

## 4. Dataset documentation

For both layers, maintain versioned manifests and a dataset card recording provenance, permissions, locations at a suitable privacy level, collection devices/settings, intended use, ODD, exclusions, demographic/privacy concerns, class/event distribution, known biases, annotation process, split logic, and limitations.

## 5. Data sufficiency decision

Before a multimodal paper is attempted, audit Layer B for number of events, crossings, clearance-observable events, no-train exposure, synchronization quality, represented conditions, and out-of-domain exclusions. If insufficient, narrow the study to Layer A rather than treating simulation as replacement evidence.
