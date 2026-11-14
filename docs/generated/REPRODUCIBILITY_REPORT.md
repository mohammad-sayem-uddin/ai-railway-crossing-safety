# Reproducibility & CLI Governance Audit Report

**Primary References:** [`docs/generated/final_research_v2/REPRODUCIBILITY.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/REPRODUCIBILITY.md), [`BASELINE_SNAPSHOT.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/BASELINE_SNAPSHOT.json), [`src/railway_detection/reproducibility/audit.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/reproducibility/audit.py)

---

## 1. Reproducibility Audit Fix Applied (`audit.py` Synchronized with Live Governance)

Prior to this mission, two official CLI commands disagreed on the same repository snapshot:
- `railway_detection.cli.main evaluation status` verified `data/manifests/phase12_protocol_decision.json` via [`verify_protocol_override()`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/governance.py#L273-L303) (`PASS`, `protocol_profile_sha256: 6b5edb48...`).
- [`run_reproducibility_audit()`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/reproducibility/audit.py#L393-L520) called `unresolved_decisions(None)` and returned a hardcoded string marking `protocol_version` and `premature_opening_window` as `UNRESOLVED`.

**Implemented Fix:** Updated `run_reproducibility_audit()` and `unresolved_register` to validate `phase12_protocol_decision.json` using `governance.verify_protocol_override()`, returning:
- `PASS` when cryptographically verified (`M4` / `v9`),
- `UNRESOLVED` fail-closed when the decision JSON is absent (verified in synthetic temp-root unit tests),
- `FAIL` fail-closed when the decision JSON is malformed, tampered, or selects an invalid profile (`test_protocol_version_fails_closed_when_override_tampered`).

### Live CLI Reproducibility Summary After Fix

| Audit Status | Count | Items Reported by `cli.main audit reproducibility` |
|---|---|---|
| **`PASS`** | **`7`** *(was `6`)* | `dataset_manifests`, `protocol_version` *(newly synced)*, `r04_scope_decision`, `model_checkpoint_fingerprints`, `config_and_policy_fingerprints`, `ultralytics_importable`, `manuscript_claims_vs_evidence` (`0` unsupported claims) |
| **`UNRESOLVED`** | **`3`** *(was `4`)* | `approved_ground_truth` (`0` Stage-2.1 records; `27` retired schema `6.0.0`), `event_split_decision` (Option A descriptive mode), `unresolved_decisions` (contains `approved_ground_truth` & `event_split_decision`, while `premature_opening_window` is `recorded (M4 / v9 sensitivity)`) |
| **`FAIL`** | **`1`** | `dependency_lock` (`11` minor package version drifts between `.venv` and `requirements.lock`) |
| **`NOT_AVAILABLE`** | **`2`** | `evaluation_result_provenance`, `experiment_manifest_completeness` (blocked until official Phase 12 executes) |

---

## 2. Determinism & Environment Pinning Verification

1. **Bit-Identical Exploratory Outputs (`Exp A–N`):** `23/23` artifacts in [`results/exploratory_v2/`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/FILE_HASH_MANIFEST.sha256) verified byte-identical across consecutive runs via `shasum -a 256 -c` (including normalized `\n` line endings in `exp_n_event_matrix.csv`).
2. **Deterministic New Scripts:**
   - `scripts/run_leakage_and_split_audit.py` -> deterministic JSON/JSONL splits under [`results/dataset_audit/`](file:///Users/sayemuddin/Desktop/Train_automation/results/dataset_audit/vision_audio_leakage_audit.json) and `data/splits/{vision_v1_session_grouped,audio_v3_stem_grouped}/`.
   - `scripts/run_optimization_and_robustness_suite.py` -> fixed-seed deterministic `Exp O, P (statistical timing excluded from deterministic hashes), Q` outputs under [`results/exploratory_v2/optimization_and_stress/`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/exp_o_audio_calibration_hysteresis.json).
   - `scripts/generate_master_publication_tables.py` & `scripts/generate_new_audit_and_edge_figures.py` -> reproducible tables (`results/publication_tables/`) and 300-DPI figures (`docs/generated/figures/fig11..fig14.png`).
3. **Preserved Digests (Byte-Identical Throughout Mission):**
   - Vision `39f402dfe460/checkpoints/weights/best.pt`: `24,493,159 B`, `sha256: 3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`.
   - Audio `RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`: `329,497 B`, `sha256: ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`.
   - Frozen `frozen_experiment_v1.yaml` (`b8ef5da0...`), `decision_policy_v1.yaml` (`c87c1432...`), `decision_policy_v2_candidate.yaml` (`d90828b2...`), and historical `MISSION_26_CATALOG_BINDING.json` (`catalog.py`).
4. **Access-Classification Hygiene:** All `174` test files classified cleanly via [`classify_test_access.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/classify_test_access.py) (`--check` = `manifest OK`; `113` `synthetic_only`, `29` `metadata_only`, `14` `model_checkpoint_access`, `4` `processed_data_access`, `4` `raw_media_access`, `10` `unknown`, `142` `safe_for_synthetic_runner`).
5. **Known Residual Reproducibility Debt:**
   - `.venv` vs `requirements.lock` drift (`11` packages) triggers expected `FAIL: dependency_lock`.
   - Full `pytest tests/` requires `--import-mode=importlib` because of `4` pre-existing duplicate test module basenames, and `8` pre-existing child-process tests assume `PYTHONPATH=src` is exported externally.
