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

### Live CLI Reproducibility Summary After Technical Remediation

| Audit Status | Count | Items Reported by `cli.main audit reproducibility` |
|---|---|---|
| **`PASS`** | **`8`** *(was `6` -> `7` -> `8`)* | `dataset_manifests`, `protocol_version`, `r04_scope_decision`, `model_checkpoint_fingerprints`, `config_and_policy_fingerprints`, **`dependency_lock` (`50/50` pinned packages match)**, `ultralytics_importable`, `manuscript_claims_vs_evidence` (`0` unsupported claims) |
| **`UNRESOLVED`** | **`3`** *(human gates)* | `approved_ground_truth` (`0` Stage-2.1 records; `27` retired schema `6.0.0`), `event_split_decision` (Option A descriptive mode), `unresolved_decisions` (contains `approved_ground_truth` & `event_split_decision`, while `premature_opening_window` is `recorded`) |
| **`FAIL`** | **`0`** *(was `1`)* | *None (`dependency_lock` reconciled; `requirements.lock` `sha256: 21ee159c...`)* |
| **`NOT_AVAILABLE`** | **`2`** | `evaluation_result_provenance`, `experiment_manifest_completeness` (blocked until official Phase 12 executes) |

---

## 2. Determinism & Environment Pinning Verification

1. **Bit-Identical Exploratory Outputs (`Exp A–N`):** `23/23` artifacts in [`results/exploratory_v2/`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/FILE_HASH_MANIFEST.sha256) verified byte-identical across consecutive runs via `shasum -a 256 -c` (including normalized `\n` line endings in `exp_n_event_matrix.csv`).
2. **Deterministic Audit, Optimization & Edge Scripts:**
   - `scripts/run_leakage_and_split_audit.py` -> deterministic JSON/JSONL splits under [`results/dataset_audit/`](file:///Users/sayemuddin/Desktop/Train_automation/results/dataset_audit/vision_audio_leakage_audit.json) and `data/splits/{vision_v1_session_grouped,audio_v3_stem_grouped}/`.
   - `scripts/run_optimization_and_robustness_suite.py` -> fixed-seed `Exp O, P, Q, R` outputs under [`results/exploratory_v2/optimization_and_stress/`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/exp_r_crossval_and_failsafe.json); `scripts/rpi_edge_benchmark.py` -> TorchScript/FP16 & thread-scaling benchmark ([`host_edge_scaling_benchmark.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/host_edge_scaling_benchmark.json), `physical_raspberry_pi_tested = false`).
   - `scripts/generate_master_publication_tables.py` & `scripts/generate_new_audit_and_edge_figures.py` -> reproducible tables (`results/publication_tables/`, `table1..table6.csv`) and 300-DPI figures (`docs/generated/figures/fig11..fig15.png`).
3. **Preserved Digests (Byte-Identical Throughout Mission):**
   - Vision `39f402dfe460/checkpoints/weights/best.pt`: `24,493,159 B`, `sha256: 3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`.
   - Audio `RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`: `329,497 B`, `sha256: ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`.
   - Frozen `frozen_experiment_v1.yaml` (`b8ef5da0...`), `decision_policy_v1.yaml` (`c87c1432...`), `decision_policy_v2_candidate.yaml` (`d90828b2...`), while `MISSION_26_CATALOG_BINDING.json` `"README.md"` digest was intentionally synced (`fc1a746e...`).
4. **Access-Classification Hygiene & Zero Technical Blockers:** All `179` test files classified cleanly via [`classify_test_access.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/classify_test_access.py) (`--check` = `manifest OK`; `116` `synthetic_only`, `29` `metadata_only`, `15` `model_checkpoint_access`, `5` `processed_data_access`, `5` `raw_media_access`, `9` subprocess-spawning `unknown`, `145` `safe_for_synthetic_runner`). [`check_zero_blocker_readiness.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/check_zero_blocker_readiness.py) confirms `all_technical_checks_passed = true` (`11/11`).
5. **Pytest Invocation Note:** Full `pytest tests/` uses `--import-mode=importlib` because of `4` pre-existing duplicate test module basenames (`test_cli.py`, `test_contracts.py`, `test_isolation.py`, `test_manifest.py`), and `scripts/run_synthetic_tests.py` automatically isolates `--confcutdir` batches (`3,285 passed, 0 failed, 0 skipped`, `guard.blocked = 0`); full `pytest -q tests/ --import-mode=importlib` passes `3,881 passed, 0 failed`.
