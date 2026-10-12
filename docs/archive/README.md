# Historical & Archived Research Documentation

> **Archive Notice:**  
> The documents in this directory represent historical milestones, preliminary experiment plans, earlier model development reports, and initial checklists developed during prior phases of the project.  
> They are preserved strictly for scientific provenance, auditability, and methodological traceability.  
> For the current, active, and authoritative scientific specifications, refer to the master protocols in [`docs/`](../).

---

## Authoritative vs. Archived Document Index

| Archived Document | Original Scope / Historical Purpose | Initial Date / Version | Superseded / Governed By | Reason Retained in Archive |
|---|---|---|---|---|
| [`REAL_WORLD_EXPERIMENT_REPORT.md`](REAL_WORLD_EXPERIMENT_REPORT.md) | Preliminary B0–B7 benchmark run report | 2026-09-23 (v2.0.0) | [`docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`](../FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md) | Preserves original empirical results and metrics from preliminary software evaluation. |
| [`REAL_WORLD_EXPERIMENT_PLAN.md`](REAL_WORLD_EXPERIMENT_PLAN.md) | Initial benchmark evaluation plan | 2026-09-23 (v1.0.0) | [`docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`](../FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md) | Methodological provenance for early preliminary replay runs. |
| [`EXPERIMENT_PROTOCOL_V2.md`](EXPERIMENT_PROTOCOL_V2.md) | Proposed protocol draft | 2026-08-14 | [`docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`](../FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md) | Early timing rules and threshold proposal history. |
| [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md) | Early phase experiment roadmap | 2026-08-11 | [`docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`](../FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md) | Initial benchmark dependency mapping. |
| [`RESEARCH_PROTOCOL_V2.md`](RESEARCH_PROTOCOL_V2.md) | Phase 0 scientific protocol | 2026-08-13 | [`docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`](../FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md) | Early research claim boundaries and ODD definitions. |
| [`RESEARCH_CONCEPT.md`](RESEARCH_CONCEPT.md) | Initial conceptual system design | 2026-08-10 | [`README.md`](../../README.md) & [`docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`](../FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md) | Background context, literature foundation, and original crossing safety motivation. |
| [`AUDIO_MODEL_REPORT.md`](AUDIO_MODEL_REPORT.md) | Audio V1 development report | 2026-09-23 (`RUN_20260923_AUDIO_001`) | [`docs/AUDIO_MODEL_V3_ESC50_REPORT.md`](../AUDIO_MODEL_V3_ESC50_REPORT.md) | Baseline audio model training curves and confusion matrix. |
| [`AUDIO_MODEL_V2_REPORT.md`](AUDIO_MODEL_V2_REPORT.md) | Audio V2 research report | 2026-10-08 (`RUN_20261008_AUDIO_V2`) | [`docs/AUDIO_MODEL_V3_ESC50_REPORT.md`](../AUDIO_MODEL_V3_ESC50_REPORT.md) | Documents the legacy model that exhibited leakage, justifying the V2 prohibition. |
| [`AUDIO_MODEL_PRETRAINING_CHECKLIST.md`](AUDIO_MODEL_PRETRAINING_CHECKLIST.md) | Pre-training audit checklist | 2026-09-21 (v1.0.0) | [`docs/AUDIO_MODEL_V3_ESC50_REPORT.md`](../AUDIO_MODEL_V3_ESC50_REPORT.md) | Audio dataset auditing criteria prior to hard-negative collection. |
| [`DATASET_SPECIFICATION_V2.md`](DATASET_SPECIFICATION_V2.md) | Early two-layer data design | 2026-08-14 | [`docs/FINAL_GROUND_TRUTH_PROTOCOL.md`](../FINAL_GROUND_TRUTH_PROTOCOL.md) | Historical separation rule between Layer A and Layer B data. |
| [`REAL_DATASET_INVENTORY.md`](REAL_DATASET_INVENTORY.md) | Layer B V1 dataset inventory | 2026-09-21 (v1.0.0) | [`docs/FINAL_GROUND_TRUTH_PROTOCOL.md`](../FINAL_GROUND_TRUTH_PROTOCOL.md) | Technical audit of retired September 2026 recordings. |
| [`REAL_DATASET_STRUCTURE.md`](REAL_DATASET_STRUCTURE.md) | Layer B V1 directory layout | 2026-09-21 (v1.0.0) | [`docs/FINAL_GROUND_TRUTH_PROTOCOL.md`](../FINAL_GROUND_TRUTH_PROTOCOL.md) | Directory structure of retired V1 media. |
| [`OLD_TEST_DATA_DELETION_MANIFEST.md`](OLD_TEST_DATA_DELETION_MANIFEST.md) | Controlled dataset replacement log | 2026-10-07 | [`docs/REPOSITORY_CLEANUP_AUDIT.md`](../REPOSITORY_CLEANUP_AUDIT.md) | Cryptographic deletion manifest proving controlled retirement of uncalibrated V1 clips. |
| [`REAL_DATASET_STATUS.md`](REAL_DATASET_STATUS.md) | Post-retirement transition note | 2026-10-07 | [`docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`](../FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md) | Historical record of the transition between V1 retirement and V2 intake. |
| [`REAL_DATASET_V2_INVENTORY.md`](REAL_DATASET_V2_INVENTORY.md) | Layer B V2 technical audit | 2026-10-08 (v2.0.0) | [`docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`](../FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md) | Video duration, bitrate, and audio track audit for the 27 evaluation events. |
| [`REAL_DATASET_V2_STRUCTURE.md`](REAL_DATASET_V2_STRUCTURE.md) | Layer B V2 directory architecture | 2026-10-08 (v2.0.0) | [`docs/FINAL_GROUND_TRUTH_PROTOCOL.md`](../FINAL_GROUND_TRUTH_PROTOCOL.md) | Specifications for `train_events/`, `no_train_events/`, and `engine_events/`. |
| [`ANNOTATION_GUIDELINE_V2.md`](ANNOTATION_GUIDELINE_V2.md) | Preliminary annotation guide | 2026-08-14 | [`docs/FINAL_GROUND_TRUTH_PROTOCOL.md`](../FINAL_GROUND_TRUTH_PROTOCOL.md) | Proposed human-only double-annotation draft prior to AI-assisted pipeline. |
| [`EVENT_LABEL_PROTOCOL.md`](EVENT_LABEL_PROTOCOL.md) | Preliminary single-event labeling | 2026-08-14 | [`docs/FINAL_GROUND_TRUTH_PROTOCOL.md`](../FINAL_GROUND_TRUTH_PROTOCOL.md) | Early draft of passage event boundaries. |
| [`SYNCHRONIZED_DATA_COLLECTION_PROTOCOL.md`](SYNCHRONIZED_DATA_COLLECTION_PROTOCOL.md) | Early collection guidelines | 2026-08-14 | [`docs/FINAL_GROUND_TRUTH_PROTOCOL.md`](../FINAL_GROUND_TRUTH_PROTOCOL.md) | Historical field recording guidance. |
| [`EXECUTION_PLAN.md`](EXECUTION_PLAN.md) | Phase 0 architecture plan | 2026-08-16 (v1.0.0) | [`docs/FINAL_EXPERIMENT_DATA_FLOW.md`](../FINAL_EXPERIMENT_DATA_FLOW.md) | Initial software modularization plan. |
| [`MASTER_IMPLEMENTATION_ROADMAP.md`](MASTER_IMPLEMENTATION_ROADMAP.md) | Implementation roadmap | 2026-08-14 | [`docs/FINAL_EXPERIMENT_DATA_FLOW.md`](../FINAL_EXPERIMENT_DATA_FLOW.md) | Early multi-phase project roadmap. |
| [`PRE_CODING_CHECKLIST.md`](PRE_CODING_CHECKLIST.md) | Pre-implementation checklist | 2026-08-14 | [`docs/FINAL_EXPERIMENT_DATA_FLOW.md`](../FINAL_EXPERIMENT_DATA_FLOW.md) | Initial gate requirements before code implementation. |
| [`PRE_REAL_DATA_COMPLETION_CHECKLIST.md`](PRE_REAL_DATA_COMPLETION_CHECKLIST.md) | Pre-real-data intake checklist | 2026-09-21 (v1.0.0) | [`docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`](../FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md) | Audit criteria for completing Phase 0 software foundation. |
| [`IDEA_LOG.md`](IDEA_LOG.md) | Early ideas and dispositions | 2026-08-10 | [`docs/RESEARCH_DECISIONS.md`](../RESEARCH_DECISIONS.md) | Log of early concept evaluations. |
| [`VIDEO_TESTING.md`](VIDEO_TESTING.md) | Video demo tooling note | 2026-09-23 (v1.0.0) | [`src/railway_detection/demo/`](../../src/railway_detection/demo/) | Notes on video demonstration and UI testing scripts. |
