# CACHE PROVENANCE ARCHITECTURE — MISSION 3 (`2026-11-01`)

**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Branch / HEAD:** `main` @ `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Schema Version:** `layer-b-controlled-cache/2.0.0`  
**Canonicalization Version:** `canonical-json/1.0`  
**Primary Modules:**
- `src/railway_detection/experiments/cache_provenance.py`
- `src/railway_detection/experiments/layer_b_processor.py`
- `src/railway_detection/evaluation/descriptive_only.py`

---

## 1. Executive Summary & Audit of the Mission 2 14-Field Contract

Mission 2 introduced `ControlledCacheProvenance` with 14 required identity fields (`REQUIRED_PROVENANCE_FIELDS`). Mission 3 audited the implementation against all 16 scientific identity dimensions required for multi-condition experimental reproducibility (`B0`–`B8`) and identified four concrete architectural gaps that have now been remediated:

1. **Broken Attribute References & Incomplete Preprocessing Extraction in `LayerBEventProcessor.build_stream_provenance`**:
   - *Gap found*: `LayerBEventProcessor.build_stream_provenance` previously referenced non-existent attributes on `FrozenExperimentConfig` (`self.config.vision.architecture`, `self.config.vision.confidence_threshold_clearance`, `self.config.audio.architecture`) and omitted critical preprocessing fields (`image_size`, `class_mapping`, `n_fft`, `hop_length`, `n_mels`, `f_min`, `f_max`, `expected_feature_shape`, `normalization`) as well as full timing parameters.
   - *Remediation*: Fixed `build_stream_provenance` to use `self.config.checkpoints.vision.model_name`, `self.config.checkpoints.audio_v3.model_name`, `build_vision_preprocessing_config`, `build_audio_preprocessing_config`, and the complete `timing_config` dictionary.
2. **Three-Level Cryptographic Identity Separation & Explicit Cache Reuse Policy**:
   - *Gap found*: Previously, `provenance_sha256` mixed `run_id` with stream and scientific configuration fields, providing no way to distinguish whether two runs had identical scientific configuration (`configuration_sha256`) and stream identity (`cache_identity_sha256`) versus distinct `run_id` (`provenance_sha256`).
   - *Remediation*: Implemented three distinct canonical SHA-256 digests (`configuration_sha256()`, `cache_identity_sha256()`, `provenance_sha256()`) and explicit reuse policies (`CACHE_REUSE_ISOLATED_RUN` default vs `CACHE_REUSE_IDENTICAL_CONFIG`).
3. **JSONL Envelope Payload Integrity Verification**:
   - *Gap found*: `write_controlled_cache_jsonl` previously hashed only the header (`provenance_sha256`) and did not bind the detection record lines (`line 2..N`) to a cryptographic digest, meaning a mutated or truncated detection line would not be caught if the header remained intact.
   - *Remediation*: Added `record_count` and `payload_sha256` (`compute_records_payload_sha256`) to the `__cache_provenance__` header and enforced fail-closed verification (`CACHE_PAYLOAD_CORRUPTED`) plus duplicate JSON key rejection (`CACHE_DUPLICATE_JSON_KEY`) in `load_controlled_cache_jsonl`.
4. **Descriptive-Only Provenance Enforcement**:
   - *Gap found*: `descriptive_only.py` checked string tags (`source_category == "historical_diagnostic"`), but did not cryptographically validate `ControlledCacheProvenance` when `cache_classification == "controlled_experimental"` or `controlled_run_verified=True` was claimed.
   - *Remediation*: Updated `_validate_input` in `src/railway_detection/evaluation/descriptive_only.py` to require and validate `ControlledCacheProvenance` whenever controlled experimental status is claimed (`CONTROLLED_PROVENANCE_REQUIRED` / `CACHE_PROVENANCE_INVALID`).

---

## 2. Complete 16-Dimension Identity Coverage Mapping

While preserving `len(REQUIRED_PROVENANCE_FIELDS) == 14` for full backward compatibility with Mission 2 tests, `ControlledCacheProvenance` covers all 16 required identity dimensions:

| # | Identity Dimension | Provenance Field / Carrier | Enforcement & Validation Contract |
|---|---|---|---|
| 1 | **Event identity** | `event_id` | Non-empty string (`event_001`); normalized in `cache_key()` (`/` $\rightarrow$ `__`). |
| 2 | **Cohort identity** | `cohort` | Must be in `{"train_events", "no_train_events", "engine_events"}` (`PROVENANCE_COHORT_INVALID`). |
| 3 | **Source identity** | `source_id` | Non-empty stream identifier (`camera_1`, `camera_2`, `audio_1`); cross-checked against every `EvidenceRecord.source_id`. |
| 4 | **Modality** | `modality` | Must be in `{"vision", "audio"}` (`PROVENANCE_MODALITY_INVALID`); cross-checked against every `EvidenceRecord.modality`. |
| 5 | **Detector / model architecture** | `model_architecture` | Non-empty architecture string (`YOLOv8n_COCO_Pretrained`, `CompactTrainHornCNN`). |
| 6 | **Checkpoint identity** | `checkpoint_sha256` | 64-char lowercase hex SHA-256 (`_SHA256_RE`). Rejects filename-only/unresolved tokens (`PROVENANCE_CHECKPOINT_UNRESOLVED`) and prohibited Audio V2 hash `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5` (`PROHIBITED_CHECKPOINT_REJECTED`). |
| 7 | **Preprocessing configuration** | `preprocessing_config` | Non-empty canonicalized mapping extracted by `build_vision_preprocessing_config` / `build_audio_preprocessing_config`. |
| 8 | **ROI / geometry configuration** | `roi_config` $\rightarrow$ `preprocessing_config["roi_config"]` | Validated by `_validate_roi_config` (bounding box `x2 > x1, y2 > y1` or polygon $\ge 3$ `[x, y]` vertices) and bound into `preprocessing_config`. |
| 9 | **Experiment configuration digest** | `experiment_config_sha256` | 64-char lowercase hex SHA-256 of the authoritative `FrozenExperimentConfig`. |
| 10 | **Failure injector identity** | `failure_injector` | Explicit injector mode (`none`, `B5a`–`B5c`, `B6a`–`B6c`, `B7a`–`B7f`, `STALE_TIMESTAMPS`, etc.). |
| 11 | **Failure injector parameters** | `injector_parameters` | Canonicalized schedule/seed/window/delay/target_source mapping (`build_injector_provenance`). Fails closed on `B7e` / `STALE_TIMESTAMPS` without positive finite `delay_s` and non-empty `target_source`. |
| 12 | **Timing / clock configuration** | `timing_config` | Non-empty canonicalized mapping including `tick_s`, `source_staleness_s`, `window_tolerance_s`, `cross_camera_sync` mode/status/policy. |
| 13 | **Software / code identity** | `software_version` (+ optional `git_commit`) | Non-empty version string; when `git_commit` is provided, normalizes to `<software_version>+git.<git_commit>`. |
| 14 | **Cache schema version** | `cache_schema_version` | Must match `CONTROLLED_CACHE_SCHEMA_VERSION = "layer-b-controlled-cache/2.0.0"`. |
| 15 | **Run identity** | `run_id` | Non-empty run identifier distinguishing isolated executions. |
| 16 | **Provenance digest** | `provenance_sha256()`, `cache_identity_sha256()`, `configuration_sha256()` | Deterministic SHA-256 over canonical JSON (`canonical-json/1.0`). |

---

## 3. Canonicalization & Serialization Rules (`canonical-json/1.0`)

Implemented in `_assert_finite_json_value`, `canonicalize_config`, `canonical_json_str`, and `_loads_strict_json`:

1. **Recursive Key Sorting**: All dictionary keys are validated as non-empty strings and sorted lexicographically at every nesting depth (`sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=True`).
2. **Numeric Normalization & Non-Finite Rejection**:
   - `NaN`, `+Inf`, and `-Inf` are rejected fail-closed (`PROVENANCE_NONFINITE_NUMBER`, `allow_nan=False`).
   - Negative zero (`-0.0`) is normalized to `0.0` so numerically identical floating-point values never produce divergent JSON strings.
3. **Strict JSON Parsing**:
   - `_loads_strict_json` uses `object_pairs_hook` to reject duplicate JSON keys (`CACHE_DUPLICATE_JSON_KEY`) and `parse_constant` to reject `NaN`/`Infinity` literals.
4. **Unknown Key Preservation**:
   - Arbitrary nested user/researcher configuration keys inside `preprocessing_config`, `injector_parameters`, `roi_config`, and `timing_config` are recursively canonicalized and preserved—never silently dropped.
5. **Raw Media Reference Guard**:
   - `_contains_raw_media_reference` rejects any string ending in `.mov`, `.mp4`, `.wav`, `.avi`, `.mkv`, `.flac`, `.m4a`, `.mp3` or referencing `data/raw` (`RAW_MEDIA_REFERENCE_FORBIDDEN`).

---

## 4. Three-Level Identity & Cache Reuse Policy

`ControlledCacheProvenance` computes three distinct cryptographic digests:

1. **Configuration Identity (`configuration_sha256`)**:
   - Covers `modality`, `model_architecture`, `checkpoint_sha256`, `preprocessing_config` (including `roi_config`), `experiment_config_sha256`, `failure_injector`, `injector_parameters`, `timing_config`, `cache_schema_version`, and `software_version`.
2. **Stream Cache Identity (`cache_identity_sha256`)**:
   - Covers `cohort`, `event_id`, `source_id` + all `CONFIGURATION_IDENTITY_FIELDS` (excludes `run_id`).
3. **Run Provenance Identity (`provenance_sha256`)**:
   - Covers all 14 `REQUIRED_PROVENANCE_FIELDS` including `run_id`.

### Reuse Policies (`validate_controlled_cache_provenance` & `load_controlled_cache_jsonl`)
- **`CACHE_REUSE_ISOLATED_RUN` (`"isolated_run"`, Default)**:
  - Requires exact match across all 14 fields including `run_id` and `provenance_sha256()`. A cache from `run_alpha` is rejected if loaded by `run_beta`.
- **`CACHE_REUSE_IDENTICAL_CONFIG` (`"allow_identical_config_reuse"`, Explicit Opt-In)**:
  - Permits reusing a controlled cache across different `run_id` values **if and only if** all 13 `CACHE_IDENTITY_FIELDS`, `configuration_sha256()`, and `cache_identity_sha256()` match identically. Any difference in checkpoint, preprocessing, ROI, injector, timing, event, cohort, source, or modality is rejected fail-closed (`PROVENANCE_MISMATCH`).
