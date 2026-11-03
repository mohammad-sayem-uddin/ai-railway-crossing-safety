# REGRESSION TEST RESULTS — MISSION 3 (`2026-11-01`)

**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Branch / HEAD:** `main` @ `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Python Environment:** Python `3.11.15`, `pytest-9.1.1`, `ruff`  
**Safety Verification:** Zero raw media files (`.mov`, `.mp4`, `.wav`) accessed, decoded, or hashed.

---

## 1. Test Execution Summary

| Suite / Verification Step | Command | Result | Duration |
|---|---|---|---|
| **Mission 3 + Mission 2 Focused Suite** | `.venv/bin/pytest tests/unit/test_mission3_reproducibility_and_provenance.py tests/unit/test_mission2_pipeline_integrity.py -v` | **73 passed, 0 failed** (`33` Mission 3 + `40` Mission 2) | `0.49s` |
| **Full Synthetic Unit Test Suite** | `.venv/bin/pytest tests/unit -q` | **1170 passed, 0 failed** | `28.08s` |
| **Bytecode Compilation Check** | `.venv/bin/python -m py_compile ...` | **PASSED (exit code 0)** | `<0.2s` |
| **Git Whitespace / Conflict Marker Check** | `git diff --check -- <mission3_files>` | **PASSED (exit code 0)** | `<0.1s` |
| **Ruff Linter Verification** | `.venv/bin/ruff check --ignore E501 <mission3_files>` | **All checks passed! (exit code 0)** | `<0.2s` |

---

## 2. Breakdown of New Mission 3 Tests (`tests/unit/test_mission3_reproducibility_and_provenance.py`)

1. **`test_provenance_14_required_fields_contract_preserved`**: Verifies `REQUIRED_PROVENANCE_FIELDS` length (`14`), `CANONICAL_SERIALIZATION_VERSION == "canonical-json/1.0"`, and serialized field presence.
2. **`test_provenance_hash_deterministic_across_nested_key_ordering`**: Verifies identical `provenance_sha256()`, `configuration_sha256()`, and `cache_identity_sha256()` across arbitrary nested key permutations.
3. **`test_canonicalization_negative_zero_and_unknown_keys_preserved`**: Verifies `-0.0` normalizes to `0.0` and custom nested researcher keys are preserved.
4. **`test_canonicalization_rejects_non_finite_floats[nan|inf|-inf]`** (3 parametrized cases): Verifies `NaN`, `+Inf`, and `-Inf` raise `PROVENANCE_NONFINITE_NUMBER`.
5. **`test_canonicalization_rejects_raw_media_paths_in_provenance[.mov|.mp4|.wav]`** (3 parametrized cases): Verifies raw media extensions/paths raise `RAW_MEDIA_REFERENCE_FORBIDDEN`.
6. **`test_checkpoint_hash_change_produces_collision_miss`**: Verifies vision checkpoint SHA-256 mutation changes digests and causes `load_controlled_cache_jsonl` to reject with `PROVENANCE_MISMATCH`.
7. **`test_prohibited_audio_v2_checkpoint_hash_and_path_rejected`**: Verifies Audio V2 SHA-256 (`59b078...`) and path (`models/audio/best_checkpoint.pt`) raise `PROHIBITED_CHECKPOINT_REJECTED`.
8. **`test_unresolved_or_filename_only_checkpoint_rejected[...]`** (6 parametrized cases): Verifies `yolov8n.pt`, `best.pt`, `pending`, `unknown`, `unresolved`, and invalid hex raise `PROVENANCE_CHECKPOINT_UNRESOLVED` / `PROVENANCE_CHECKPOINT_DIGEST_INVALID`.
9. **`test_resolve_checkpoint_identity_and_raw_media_guard`**: Verifies `resolve_checkpoint_identity` resolution, unresolved rejection, and raw media path rejection.
10. **`test_vision_preprocessing_and_roi_collisions`**: Verifies 7 vision preprocessing and ROI polygon/enabled variations produce 7 distinct `provenance_sha256()` and `configuration_sha256()` digests.
11. **`test_audio_preprocessing_collisions`**: Verifies 4 audio preprocessing variations (`operating_threshold`, `window_s`, `n_mels`) produce 4 distinct digests.
12. **`test_injector_and_timing_collisions_across_b5_b6_b7`**: Verifies 9 failure injector (`none`, `B5a`, `B6b`, `B7d` seeds, `B7e` delays/targets) and timing (`source_staleness_s`) variations produce 9 distinct digests.
13. **`test_b7e_without_delay_s_or_target_source_fails_closed[...]`** (5 parametrized cases): Verifies missing, negative, or blank `delay_s`/`target_source` for `B7e` raises `PROVENANCE_INJECTOR_INVALID`.
14. **`test_event_cohort_source_modality_and_run_id_separation`**: Verifies stream separation across cohorts/sources/modalities and verifies `CACHE_REUSE_ISOLATED_RUN` (rejects cross-run reuse) vs `CACHE_REUSE_IDENTICAL_CONFIG` (allows reuse only when all 13 config/stream fields match).
15. **`test_envelope_and_payload_corruption_rejected`**: Verifies fail-closed rejection of empty files (`CACHE_EMPTY`), missing headers (`HISTORICAL_UNVERIFIED_CACHE_REJECTED`), duplicate JSON keys (`CACHE_DUPLICATE_JSON_KEY`), unsupported schemas (`PROVENANCE_SCHEMA_VERSION_INVALID`), tampered detection payload lines (`CACHE_PAYLOAD_CORRUPTED`), and truncated record counts (`CACHE_PAYLOAD_CORRUPTED`).
16. **`test_historical_cache_compatibility_and_descriptive_only_enforcement`**: Verifies legacy unverified cache handling and `aggregate_descriptive_only` enforcement of `ControlledCacheProvenance` (`CONTROLLED_PROVENANCE_REQUIRED` / `CACHE_PROVENANCE_INVALID`).
17. **`test_layer_b_processor_build_stream_provenance_and_parameter_checks`**: Verifies `LayerBEventProcessor.build_stream_provenance`, controlled cache round-trip in `run_vision_inference`, and `PROVENANCE_PREPROCESSING_MISMATCH` when `target_fps` disagrees with provenance.
18. **`test_experiment_configuration_classes_and_reconstructable_spec`**: Verifies `classify_experiment_parameters` across the 5 configuration classes, `ExperimentConfigurationSpec` round-trip serialization, and `ExperimentRunner.run_condition` writing `reconstructable_experiment_spec` into `frozen_config_meta.json`.
19. **`test_preflight_validator_blocks_missing_prerequisites_and_never_grants_eval_auth`**: Verifies `run_experiment_preflight` reports missing authorizations, pending decisions (`D1`, `D2`, `D4`, `B7e`), and prohibited Audio V2 checkpoints while keeping `grants_eval_auth=False` and `grants_official_readiness=False`.
20. **`test_stage21_and_readiness_gates_fail_closed_on_synthetic_checks`**: Verifies `build_review_record`, `build_stage2_1_record_from_dict`, `validate_for_promotion`, and `evaluate_readiness` fail-closed behavior on synthetic fixtures.
