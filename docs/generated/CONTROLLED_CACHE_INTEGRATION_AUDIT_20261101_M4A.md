# Controlled Cache Provenance Integration Audit (Mission 4A)

**Date:** 2026-11-01  
**Mission:** 4A — Governance Reconciliation, Authorization Integrity & Stage-2.1 Safety Verification  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Branch / HEAD:** `main` @ `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Status:** VERIFIED END-TO-END (Zero Silent Fallback; Historical Diagnostic Caches Isolated from Official Evaluation)

---

## 1. Executive Summary

Mission 4A Section 9 required verifying that the controlled cache provenance architecture (`src/railway_detection/experiments/cache_provenance.py`) is not merely an isolated utility, but is actively wired into and enforced across:
1. `src/railway_detection/experiments/layer_b_processor.py` (`LayerBEventProcessor`).
2. `src/railway_detection/experiments/runner.py` (`ScenarioRunner` / experiment execution).
3. `src/railway_detection/evaluation/descriptive_only.py` (`aggregate_descriptive_only`).
4. `src/railway_detection/experiments/preflight_validator.py` (`run_experiment_preflight`).

---

## 2. Cross-Module Integration Verification Matrix

| Module & Entrypoint | Controlled Cache Integration Mechanism | Failure / Refusal Behavior on Violation | Verified by Unit Test |
|---|---|---|---|
| `cache_provenance.py` (`ControlledCacheProvenance`, `write_controlled_cache_jsonl`, `load_controlled_cache_jsonl`) | Enforces 14 required fields, `schema_version = "controlled-cache-v1"`, recursive canonicalization (`-0.0 -> 0.0`, NaN/Inf rejection, raw `.mov`/`.mp4`/`.wav` path rejection), 64-hex checkpoint SHA-256 requirement, prohibited `v2/audio_pretrained.pt` (`06e56128...9750d89`) rejection, B7e `delay_s`/`target_source` requirement, and `.meta.json` sidecar + JSONL line#1 envelope parity | Raises `CacheProvenanceError` on any missing field, hash mismatch, prohibited checkpoint, raw media path, or corrupt record | `test_mission3_reproducibility_and_provenance.py` + `test_controlled_cache_integration_across_processor_and_preflight` |
| `layer_b_processor.py` (`LayerBEventProcessor.build_stream_provenance`, `_load_controlled_cached_records`, `_save_controlled_cached_records`) | When `require_controlled_cache=True`, constructs a `ControlledCacheProvenance` per `(event_id, cohort, source, modality)` stream and calls `load_controlled_cache_jsonl(cache_path, expected_provenance=expected_prov)` | Never falls back to legacy `.jsonl` caches when `require_controlled_cache=True`; raises `CacheProvenanceError` if controlled cache is missing (`allow_cache_generation_if_missing=False`) or if any provenance field mismatches | `test_controlled_cache_integration_across_processor_and_preflight` |
| `runner.py` (`ScenarioRunner`) | Propagates `require_controlled_cache` and scenario failure-injection parameters (`B5`–`B7e`, including `apply_delivery_disorder` for `B7d` and `delay_s=2.0, target_source="camera_front"` for `B7e`) into processor and simulation runner | Refuses unverified cache reuse in controlled mode | `test_mission2_pipeline_integrity.py` + `test_mission3_reproducibility_and_provenance.py` |
| `descriptive_only.py` (`aggregate_descriptive_only`, `HISTORICAL_27_EVENT_POPULATION`) | Accepts legacy/historical diagnostic caches (`cache_classification="historical_diagnostic"`) only when `population_label` is non-official and explicitly marks `official_evaluation_eligible = False` and `mode = "DESCRIPTIVE_ONLY"` | Raises `DescriptiveOnlyRefusal` if `population_label` claims `"official"` / `"inferential"`, if `event_evaluations` is empty, or if `limitations` / `permitted_claims` are omitted | `test_historical_cache_compatibility_and_descriptive_only_enforcement` |
| `preflight_validator.py` (`run_experiment_preflight`) | Inspects `controlled_cache_dir` for `.controlled.jsonl` envelopes, validates each envelope via `ControlledCacheProvenance.from_dict()`, and checks checkpoint SHA-256 readiness | Emits `CONTROLLED_CACHE_DIR_MISSING`, `CONTROLLED_CACHE_EMPTY`, `CONTROLLED_CACHE_INVALID`, or `CHECKPOINT_PROVENANCE_UNRESOLVED`, setting `ready_for_controlled_execution=False` and `ready_for_official_evaluation=False` | `test_controlled_cache_integration_across_processor_and_preflight` |

---

## 3. Verified Non-Negotiable Cache Safety Invariants

1. **No Silent Fallback from Controlled to Legacy Cache:** In `LayerBEventProcessor.process_event()`, when `require_controlled_cache=True`, `_load_cached_records()` (the legacy `.jsonl` loader) is unreachable.
2. **Parameter Perturbation Forces Cache Key Separation:** Changing any vision parameter (`conf_threshold`, `enter_threshold`, `exit_threshold`, `img_size`, `roi_polygon_normalized`), audio parameter (`sample_rate`, `n_fft`, `hop_length`, `n_mels`, `window_duration_s`), injector parameter (`scenario_id`, `seed`, `delay_s`, `target_source`), checkpoint SHA-256, or `cache_reuse_policy="isolated_run"` with a different `run_id` deterministically changes `provenance_sha256()` and raises `CacheProvenanceError` if loaded against the prior cache file.
3. **Prohibited Audio Checkpoint Blocked:** `06e5612826c1dc7fd7fb7ae2ffbe0cf909beddc6ee1f7bf5bf72dc9ad9750d89` (`models/Lock_All_Model/v2/audio_pretrained.pt`) is rejected immediately by `ControlledCacheProvenance.validate()`.
