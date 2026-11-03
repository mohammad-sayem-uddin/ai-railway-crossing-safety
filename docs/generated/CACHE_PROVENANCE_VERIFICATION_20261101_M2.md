# CACHE PROVENANCE VERIFICATION — MISSION 2 (2026-11-01)

- **Document ID**: `CACHE_PROVENANCE_VERIFICATION_20261101_M2`
- **Mission**: `MISSION 2 — PIPELINE INTEGRITY VERIFICATION, SAFE REMEDIATION & STAGE-2.1 READINESS`

---

## 1. Audit of Cache Creation and Loading Paths

All cache and replay evidence paths in the repository were inspected without opening or hashing any raw `.mov`, `.mp4`, or `.wav` files:

| Component | File Path | Role & Provenance Status |
| :--- | :--- | :--- |
| **`LayerBEventProcessor`** | `src/railway_detection/experiments/layer_b_processor.py` | Ingests/caches per-stream vision and audio `EvidenceRecord` JSONL files. **Historical defect**: previously used bare `{cohort}_{event}_{stem}_{source_id}_vision.jsonl` and `{cohort}_{event_id}_{source_id}_audio.jsonl` filenames with no provenance envelope and loaded them unconditionally when `use_cache=True`. **Remediated in Mission 2**. |
| **`ControlledCacheProvenance`** | `src/railway_detection/experiments/cache_provenance.py` | **New in Mission 2**: Defines the 14-field canonical provenance identity, SHA-256 digesting, deterministic cache key generation, fail-closed controlled JSONL reader/writer, and explicit historical diagnostic cache loader. |
| **`CacheOnlyReplayEngine`** | `src/railway_detection/evaluation/cache_only_engine.py` | Manifest-bound offline replay engine (`manifest_version == "1.0.0"`). Verifies SHA-256, `byte_size`, `line_count`, and duplicate JSON keys on every JSONL stream and forbids raw media references (`MediaAccessViolationError`). |
| **`CachePhase12Adapter`** | `src/railway_detection/evaluation/cache_phase12_adapter.py` | Non-authoritative synthetic adapter mapping `ReplayOutput` to `EventReplay` (`EvidenceClassification.SYNTHETIC` only; refuses `EvidenceClassification.REAL` with `OFFICIAL_CONVERSION_REFUSED`). |
| **`ReplayEvidence` & `RealEventReplayProducer`** | `src/railway_detection/evaluation/replay_evidence.py`, `src/railway_detection/evaluation/replay_producer.py` | Official Phase 12 replay evidence contract (`phase12-replay-evidence/1`). Requires `frozen_config_canonical_sha256`, `checkpoint_sha256` (`vision` and `audio_v3`, blocking prohibited `audio_v2`), thresholds, `media_sha256` cross-checked against Stage-2.1 `reviewer_observed_media_hashes`, `inference_run_id`, and `annotation_labels_used == False`. |

---

## 2. The 14-Field Controlled Cache Provenance Contract

Implemented in `ControlledCacheProvenance` (`src/railway_detection/experiments/cache_provenance.py`), every controlled experimental cache stream is bound to all 14 required identity fields:

1. `cohort`: `train_events` | `no_train_events` | `engine_events`
2. `event_id`: Event identifier (e.g., `event_001`)
3. `source_id`: Sensor/camera stream identifier (`camera_1`, `camera_2`, `audio_1`)
4. `modality`: `vision` | `audio`
5. `model_architecture`: Architecture identifier (e.g., `yolov8n`, `CompactTrainHornCNN`)
6. `checkpoint_sha256`: 64-character lowercase hex SHA-256 digest of the model checkpoint
7. `preprocessing_config`: Canonical mapping of sampling FPS, confidence thresholds, audio window/hop/sample rate/operating threshold
8. `experiment_config_sha256`: 64-character lowercase hex canonical SHA-256 digest of `FrozenExperimentConfig`
9. `failure_injector`: Perturbation/injector mode identity (e.g., `none`, `B7d_out_of_order_frames`, `B7e_stale_timestamps`)
10. `injector_parameters`: Canonical mapping of injector parameters (e.g., `delay_s`, `target_source`, `drop_rate`, `seed`)
11. `timing_config`: Canonical mapping of `tick_s`, `gate_closing_s`, `gate_opening_s`, and `allow_unverified_zero_offset`
12. `cache_schema_version`: `layer-b-controlled-cache/2.0.0`
13. `software_version`: Package/code version string
14. `run_id`: Explicit controlled run identifier

### Deterministic Digest and Filename Generation
- **Canonical Serialization**: `json.dumps(identity_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=True)`
- **Provenance Digest**: `provenance_sha256 = sha256(canonical_json).hexdigest()`
- **Cache Key & Filename**: `{cohort}__{safe_event_id}__{source_id}__{modality}__{provenance_sha256[:16]}.jsonl`
- **Serialized Envelope**: Line 1 of every controlled JSONL cache file stores `{"__cache_provenance__": provenance.to_dict()}` containing all 14 fields, `cache_classification: "controlled_experimental"`, `official_evaluation_eligible: false`, and `provenance_sha256`.

---

## 3. Fail-Closed Validation and Historical Cache Isolation

1. **Missing Provenance Rejected**:
   - `load_controlled_cache_jsonl` inspects line 1 for `"__cache_provenance__"`. Any legacy headerless JSONL file raises `CacheProvenanceError("HISTORICAL_UNVERIFIED_CACHE_REJECTED")`.
   - `ControlledCacheProvenance.from_dict` raises `CacheProvenanceError("PROVENANCE_FIELD_MISSING")` if any of the 14 fields is absent or blank.
2. **Mismatched Provenance Rejected**:
   - `validate_controlled_cache_provenance(actual, expected)` compares all 14 fields and `provenance_sha256`, raising `CacheProvenanceError("PROVENANCE_MISMATCH")` if any field differs.
3. **Raw Media Isolation**:
   - `_assert_finite_json_value` rejects any `.mov`, `.mp4`, `.wav`, `.avi`, `.mkv`, or `.flac` reference in provenance metadata with `CacheProvenanceError("RAW_MEDIA_REFERENCE_FORBIDDEN")`.
4. **Historical Diagnostic Cache Separation**:
   - All existing legacy files under `outputs/cache/layer_b/` remain untouched on disk.
   - `LayerBEventProcessor.run_vision_inference` and `run_audio_inference` default to `allow_historical_unverified_cache: bool = False`, raising `HISTORICAL_UNVERIFIED_CACHE_REJECTED` if a legacy unverified cache is encountered without `allow_historical_unverified_cache=True`.
   - When explicitly loaded via `load_historical_diagnostic_cache_jsonl` (or `allow_historical_unverified_cache=True`), every `EvidenceRecord.metadata` is tagged with `cache_classification="historical_diagnostic"`, `controlled_run_verified=False`, and `official_evaluation_eligible=False`.
