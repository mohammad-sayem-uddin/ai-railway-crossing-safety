# CACHE COLLISION & REPRODUCIBILITY TESTS — MISSION 3 (`2026-11-01`)

**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Test Module:** `tests/unit/test_mission3_reproducibility_and_provenance.py`  
**Companion Suite:** `tests/unit/test_mission2_pipeline_integrity.py`  
**Safety Compliance:** 100% synthetic in-memory and `tmp_path` fixtures; zero raw media (`.mov`, `.mp4`, `.wav`) access.

---

## 1. Collision Matrix Summary

Every required identity dimension and failure mode specified in Mission 3 Section 4 has been verified via automated synthetic collision tests:

| Section | Collision / Reproducibility Scenario | Test Function(s) | Verified Outcome |
|---|---|---|---|
| **4.1** | Identical config dicts with permuted nested key order | `test_provenance_hash_deterministic_across_nested_key_ordering` | Identical `provenance_sha256`, `configuration_sha256`, `cache_identity_sha256` |
| **4.1** | `-0.0` vs `+0.0` normalization & unknown config key preservation | `test_canonicalization_negative_zero_and_unknown_keys_preserved` | Identical canonical JSON string; unknown nested keys preserved |
| **4.1** | Non-finite floats (`NaN`, `Inf`, `-Inf`) | `test_canonicalization_rejects_non_finite_floats` | Rejected with `PROVENANCE_NONFINITE_NUMBER` |
| **4.1** | Raw media paths/extensions (`.mov`, `.mp4`, `.wav`) in provenance | `test_canonicalization_rejects_raw_media_paths_in_provenance` | Rejected with `RAW_MEDIA_REFERENCE_FORBIDDEN` |
| **4.2** | Vision checkpoint SHA-256 change | `test_checkpoint_hash_change_produces_collision_miss` | Distinct digests; `load_controlled_cache_jsonl` rejects with `PROVENANCE_MISMATCH` |
| **4.2** | Prohibited Audio V2 checkpoint hash & path (`models/audio/best_checkpoint.pt`) | `test_prohibited_audio_v2_checkpoint_hash_and_path_rejected` | Rejected with `PROHIBITED_CHECKPOINT_REJECTED` |
| **4.2** | Filename-only or unresolved checkpoint (`yolov8n.pt`, `best.pt`, `pending`, `unknown`) | `test_unresolved_or_filename_only_checkpoint_rejected`, `test_resolve_checkpoint_identity_and_raw_media_guard` | Rejected with `PROVENANCE_CHECKPOINT_UNRESOLVED` / `PROVENANCE_CHECKPOINT_DIGEST_INVALID` |
| **4.3** | Vision `sampling_fps`, `confidence_threshold_approach`, `confidence_threshold_departure`, `image_size`, `roi_config` polygon/enabled changes | `test_vision_preprocessing_and_roi_collisions` | 7/7 distinct `provenance_sha256` and `configuration_sha256` digests |
| **4.3** | Audio `operating_threshold`, `window_s`, `n_mels` changes | `test_audio_preprocessing_collisions` | 4/4 distinct `provenance_sha256` digests |
| **4.4** | Failure injector mode (`none` vs `B5a`, `B6b`, `B7d`, `B7e`), `B7d` seed (`42` vs `99`), `B7e` `delay_s` (`3.0` vs `5.0`) & `target_source` (`camera_1` vs `camera_2`), `source_staleness_s` (`2.0` vs `4.0`) | `test_injector_and_timing_collisions_across_b5_b6_b7` | 9/9 distinct `provenance_sha256` digests |
| **4.4** | `B7e` missing or invalid `delay_s` or `target_source` | `test_b7e_without_delay_s_or_target_source_fails_closed` | Fails closed with `PROVENANCE_INJECTOR_INVALID` |
| **4.5** | Cohort (`train_events` vs `no_train_events` vs `engine_events`), source (`camera_1` vs `camera_2` vs `audio_1`), modality (`vision` vs `audio`) | `test_event_cohort_source_modality_and_run_id_separation` | 5/5 distinct `cache_identity_sha256` digests |
| **4.5** | Different `run_id` under `CACHE_REUSE_ISOLATED_RUN` (default) vs `CACHE_REUSE_IDENTICAL_CONFIG` | `test_event_cohort_source_modality_and_run_id_separation` | Isolated mode rejects cross-run reuse (`PROVENANCE_MISMATCH`); identical-config mode permits reuse only when all 13 config/stream fields match |
| **4.6** | Empty file, missing header, duplicate JSON key, unsupported schema, tampered payload line, truncated record count | `test_envelope_and_payload_corruption_rejected` | Rejected with `CACHE_EMPTY`, `HISTORICAL_UNVERIFIED_CACHE_REJECTED`, `CACHE_DUPLICATE_JSON_KEY`, `PROVENANCE_SCHEMA_VERSION_INVALID`, `CACHE_PAYLOAD_CORRUPTED` |
| **4.7** | Legacy unverified cache rejection in controlled mode & explicit tagging in diagnostic mode | `test_historical_cache_compatibility_and_descriptive_only_enforcement` | Controlled loader rejects (`HISTORICAL_UNVERIFIED_CACHE_REJECTED`); diagnostic loader tags `HISTORICAL_DIAGNOSTIC_UNVERIFIED` & `official_evaluation_eligible=False` |
| **4.7** | Descriptive-only mode provenance enforcement | `test_historical_cache_compatibility_and_descriptive_only_enforcement` | Refuses `controlled_experimental` claim without valid `ControlledCacheProvenance` (`CONTROLLED_PROVENANCE_REQUIRED` / `CACHE_PROVENANCE_INVALID`) |

---

## 2. Execution Results

```text
.venv/bin/pytest tests/unit/test_mission3_reproducibility_and_provenance.py tests/unit/test_mission2_pipeline_integrity.py -v
73 passed in 0.49s
```
