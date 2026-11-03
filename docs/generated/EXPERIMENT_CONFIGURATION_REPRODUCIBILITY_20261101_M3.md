# EXPERIMENT CONFIGURATION REPRODUCIBILITY — MISSION 3 (`2026-11-01`)

**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Primary Modules:**
- `src/railway_detection/experiments/preflight_validator.py`
- `src/railway_detection/experiments/frozen_config.py`
- `src/railway_detection/experiments/runner.py`
- `src/railway_detection/experiments/layer_b_processor.py`

---

## 1. Audit of Frozen Configuration Loading & Parameter Flow

Mission 3 audited `FrozenExperimentConfig`, `ExperimentRunner`, `EventSimulationRunner`, and `LayerBEventProcessor`:

1. **`FrozenExperimentConfig` (`configs/frozen_experiment_v1.yaml`)**:
   - Computes a canonical SHA-256 hash (`canonical_hash`) over the entire configuration dictionary excluding `canonical_hash` itself.
   - Enforces Vision YOLOv8n (`3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`) and Audio V3 `CompactTrainHornCNN` (`ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`), and rejects prohibited Audio V2 (`59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5` / `models/audio/best_checkpoint.pt`).
2. **`LayerBEventProcessor` (`src/railway_detection/experiments/layer_b_processor.py`)**:
   - Previously had broken attribute references in `build_stream_provenance` (`self.config.vision.architecture`, `self.config.vision.confidence_threshold_clearance`, `self.config.audio.architecture`).
   - Now extracts all vision and audio preprocessing parameters deterministically via `build_vision_preprocessing_config` and `build_audio_preprocessing_config`, and enforces parameter consistency between `run_vision_inference` / `run_audio_inference` arguments (`target_fps`, `conf`, `threshold`, `source_id`, `cohort`, `event_id`) and the supplied `ControlledCacheProvenance`.
3. **`ExperimentRunner.run_condition` (`src/railway_detection/experiments/runner.py`)**:
   - Previously wrote only a 6-field summary in `frozen_config_meta.json`.
   - Now constructs and persists a complete `ExperimentConfigurationSpec` (`reconstructable_experiment_spec`) with its own `spec_sha256` digest in `frozen_config_meta.json`.

---

## 2. Explicit Separation of the Five Configuration Classes

Implemented in `classify_experiment_parameters` (`src/railway_detection/experiments/preflight_validator.py`). The pipeline explicitly separates and never conflates the five configuration classes:

| Configuration Class | Constant | Assigned Parameter Domains & Meaning |
|---|---|---|
| `researcher_approved` | `CONFIG_CLASS_RESEARCHER_APPROVED` | Frozen Vision YOLOv8n & Audio V3 checkpoints; `B7d` delivery-layer arrival disorder clock semantics; `B7e` delayed-timestamp staleness contract (`received_timestamp_s - frame_timestamp_s > source_staleness_s`); ground-truth state separation (`TRAIN_EVENT`, `NEGATIVE_CONTROL_SAFE_BASELINE`, `ENGINE_INSPECTION_EXCLUDED`); `engine_events` denominator isolation; descriptive-only evaluation isolation. |
| `software_default` | `CONFIG_CLASS_SOFTWARE_DEFAULT` | Engineering defaults not independently validated as final scientific constants: `tick_s=0.2`, `confirm_frames=2`, `miss_tolerance_frames=3`, `warning_dwell_s=2.0`, `gate_closing_s=4.0`, `gate_opening_s=4.0`, `clearance_dwell_s=3.0`, `source_staleness_s=2.0`, `fault_confirmation_frames=5`, `fault_recovery_hold_s=5.0`, `window_tolerance_s=0.25`. |
| `historical_configuration` | `CONFIG_CLASS_HISTORICAL` | Legacy diagnostic runs executed prior to complete cache provenance and Stage-2.1 adjudication (`HISTORICAL_DIAGNOSTIC_UNVERIFIED`). |
| `unresolved_configuration` | `CONFIG_CLASS_UNRESOLVED` | Parameters dependent on pending researcher decisions: `D1` (operating thresholds & multimodal fusion weights), `D2` (formal ROI polygon & camera calibration acceptance), `D4` (empirical cross-camera synchronization offset acceptance), and `B7e` numerical `delay_s` / `target_source` when not explicitly supplied. |
| `synthetic_test_configuration` | `CONFIG_CLASS_SYNTHETIC_TEST` | Synthetic configurations used exclusively in isolated unit and regression tests. |

**Strict Invariant**: `classify_experiment_parameters` and `build_experiment_configuration_spec` never label `software_default` or `unresolved_configuration` as `researcher_approved`. Whenever any parameter domain is `unresolved_configuration`, the top-level `configuration_class_summary` is `unresolved_configuration`.

---

## 3. Reconstructable `ExperimentConfigurationSpec` Schema (`experiment-spec/1.0`)

Every controlled run specification records:
- `spec_schema_version`: `"experiment-spec/1.0"`
- `experiment_family`: `B0`–`B8` (`B5a`–`B5c`, `B6a`–`B6c`, `B7a`–`B7f`)
- `condition_id` & `run_id`
- `evaluation_mode`: `"provisional_exploratory"`, `"descriptive_only"`, `"official_evaluation"`, or `"synthetic_verification"`
- `configuration_class_summary`: Overall configuration class
- `frozen_config_sha256`: Canonical SHA-256 of `FrozenExperimentConfig`
- `checkpoints`: Vision & Audio V3 paths, expected SHA-256 digests, and model names
- `preprocessing_config`: Complete `vision` and `audio` preprocessing dictionaries
- `roi_config`: Canonical ROI geometry or `{"roi_specified": False}`
- `fusion_config`: Approach/departure thresholds, audio operating threshold, confirm/miss frames, and safety constraints
- `state_machine_config`: Dwell times, gate closing/opening times, fault confirmation/recovery parameters
- `timing_and_clock_config`: `tick_s`, `source_staleness_s`, `window_tolerance_s`, `cross_camera_sync`, and `B7d`/`B7e` clock semantics
- `injector_config`: `failure_injector`, `injector_parameters`, `injector_version`
- `cohort_handling_rules`: Explicit denominator inclusion/exclusion rules for `train_events`, `negative_controls`, and `engine_events`
- `cache_reuse_policy` & `stream_cache_provenance_hashes`
- `parameter_classifications`: Full list of `ParameterClassification` entries
- `spec_sha256`: Deterministic canonical SHA-256 over the entire specification (`ExperimentConfigurationSpec.from_dict(spec.to_dict())` verified to round-trip with identical `spec_sha256`).
