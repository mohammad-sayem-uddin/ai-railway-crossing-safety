# Mission 3 Final Governance, Independent Audit & Edge Readiness Report

**Project:** Train Gate Automation — Bangladesh (`exp/four-layer-completion`)  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Base Commit:** `baf585760f3e195f828dd397c81efaee07e8202e`  
**Date:** `2026-11-15`  
**Official Phase-12 Status:** **`ready: false` (`7` blocker instances / `5` blocker codes; NO fabricated approvals; `evaluation run` NOT executed)**  

---

## Executive Summary

Mission 3 completed every technically executable governance-preparation, test-isolation, reproducibility, independent `Exp R` statistical verification, documentation-accuracy, and Raspberry Pi 4B/5 deployment-preparation task while strictly respecting all human-only and raw-media boundaries:

1. **Unsigned PI Approval Package Prepared (`11` schema-verified files):** Deterministically built via [`scripts/prepare_pi_approval_package.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/prepare_pi_approval_package.py) under `docs/generated/approval_packages/` (`3/3` tests passing in [`test_pi_approval_package.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_pi_approval_package.py)). Zero human signatures, timestamps, reviews, or raw-media authorizations were invented, and zero files were created or modified under `data/governance/`, `data/splits/`, `data/manifests/`, or `data/ground_truth/reviews/`.
2. **All Full-Suite & Synthetic Pytest Failures Eliminated (`3,881 / 3,881` Full Pytest; `3,285 / 3,285` Safe Runner):** Replaced process-order-sensitive `sys.modules` and subprocess isolation checks with deterministic AST transitive closure auditing in [`_isolation_audit.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/synthetic/_isolation_audit.py), verified fail-closed `[AUTH_MEDIA_ACCESS_NOT_GRANTED]` behavior in [`test_exploratory_subset_authorization_gate.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_exploratory_subset_authorization_gate.py#L69-L88), guarded Mission 3 `_sha256_file` helpers via `require_media_authorization(..., "HASH_RAW_MEDIA")`, and updated [`tests/test_access_classification.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/tests/test_access_classification.yaml) (`179` files, `145` `safe_for_synthetic_runner`).
3. **Reproducibility & Zero-Blocker Checks Verified (`11/11` Technical Checks; `FAIL: 0`):** Live `audit_reproducibility.py` reports `PASS: 8, UNRESOLVED: 3, NOT_AVAILABLE: 2, FAIL: 0` with zero active manuscript findings (`historical_claim_audit_status: FAIL` preserved exclusively on immutable archival `Railway_Crossing_Automation_Research_Report.docx`).
4. **Independent `Exp R` Cache Audit & Documentation Fixes (`exp_r_independent_validation.json`):** Reproduced `exp_r_crossval_and_failsafe.json` from non-raw Mission 43/44 caches (`exact_match_within_published_4dp: true`, `max_oof_prob_abs_diff = 4.9e-05`, `n_events_verified = 27`, `n_total_windows = 2,600`), quantified calibration/recall/tiebreak sensitivities, and fixed the `2,730 -> 2,600` window-count error and `Exp R` statistical caveats across `9` active documents plus `AGENT_EXPERIMENT_LOG.md` and `README.md`.
5. **Raspberry Pi 4B/5 Deployment & Telemetry Package (`rpi-edge-benchmark/1.1`):** Implemented [`pi_telemetry.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/optimization/pi_telemetry.py) (`3/3` tests passing in [`test_pi_telemetry.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_pi_telemetry.py)), upgraded [`scripts/rpi_edge_benchmark.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/rpi_edge_benchmark.py), refreshed [`host_edge_scaling_benchmark.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/host_edge_scaling_benchmark.json) & [`table6`](file:///Users/sayemuddin/Desktop/Train_automation/results/publication_tables/table6_exp_r_loeo_wakeup_and_edge_scaling.csv), and authored [`RASPBERRY_PI_DEPLOYMENT_RUNBOOK.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/RASPBERRY_PI_DEPLOYMENT_RUNBOOK.md) while keeping `physical_raspberry_pi_tested = false`.

---

## A. Unsigned PI Human-Approval Preparation (`docs/generated/approval_packages/`)

Generated deterministically by [`scripts/prepare_pi_approval_package.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/prepare_pi_approval_package.py) with `HUMAN_PLACEHOLDER = "__HUMAN_APPROVAL_REQUIRED__"` preserved in every human-signature, timestamp, decision, and dynamic-binding field:

| Deliverable File | Governance Purpose & Schema | Key Verified Contents |
|---|---|---|
| [`PI_APPROVAL_EXECUTION_GUIDE.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/PI_APPROVAL_EXECUTION_GUIDE.md) | Ordered 6-step PI sign-off sequence | Pre-verified 4 static `live_bindings` hashes (`decision_policy`, `frozen_config`, `protocol_profile`, `r04_scope_decision`) |
| [`AUTH_MEDIA_ACCESS.template.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/AUTH_MEDIA_ACCESS.template.json) | `phase5-media-access-authorization/2` | All 27 event keys, 8 valid operations, `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` (`sha256: d100c1e6...`); unsigned placeholders |
| [`STAGE21_27_EVENT_REVIEW_CHECKLIST.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/STAGE21_27_EVENT_REVIEW_CHECKLIST.md) / [`.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/STAGE21_27_EVENT_REVIEW_CHECKLIST.json) | `8.1.0-stage2.1` (`>= 30.0s`) | All 27 events mapped to active proposal versions/hashes, expected front/back SHA-256 prefixes, exact `scripts/run_stage21_review.py` commands, and RD-043 dual-review rules (`elaf85777@gmail.com` / `raihankabirrahu@gmail.com`) |
| [`COHORT_APPROVAL_PACKAGES.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/COHORT_APPROVAL_PACKAGES.md) / [`.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/COHORT_APPROVAL_PACKAGES.json) | Cohort gate + receipt command | `train_events` (`23`), `no_train_events` (`3`), `engine_events` (`1`), all `0` approved currently; exact `readiness_cli` command |
| [`phase12_event_split_decision.candidate.template.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/phase12_event_split_decision.candidate.template.json) & [`SPLIT_OPTION_A_RECONCILIATION.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/SPLIT_OPTION_A_RECONCILIATION.md) | `phase12-event-split-decision/1` | 16/6/5 partition validated (`leakage_safe = false` warning preserved); explicitly documents active `SPLIT-DECISION-OPTION-A-2026-11-09` so split stays absent unless PI supersedes Option A |
| [`phase12_evaluation_inputs.template.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/phase12_evaluation_inputs.template.json) & [`EVALUATION_INPUT_MANIFEST_RUNBOOK.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/EVALUATION_INPUT_MANIFEST_RUNBOOK.md) | `phase12-evaluation-inputs/1` (`real`) | Documents post-Stage-2.1 `phase12-replay-evidence/1` build via `manifest_builder`; explains why synthetic fixtures / Mission 39 caches cannot substitute |
| [`eval_authorization.template.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/eval_authorization.template.json) | `phase12-eval-authorization/1` | Strict `_EVAL_AUTH_KEYS` schema (no extra keys); `field_or_physical_operations_authorized = false` |

Schema-compliance verification in [`test_pi_approval_package.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_pi_approval_package.py) (`3/3` passed) confirms zero forged files exist in the live repository AND proves that filling `__HUMAN_APPROVAL_REQUIRED__` fields inside `tmp_path` passes `media_guard.verify_authorization_record`, `governance.verify_decision_file`, and `governance.verify_eval_authorization`.

---

## B. Test Failure Elimination & Access Classification (`3,881 / 3,881` Passed)

1. **Isolation Refactor without Process-Order Flakes ([`_isolation_audit.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/synthetic/_isolation_audit.py)):** Replaced order-dependent `sys.modules` / subprocess assertions across [`synthetic_mission17d/test_isolation.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/synthetic_mission17d/test_isolation.py), [`synthetic_mission17d/test_mission17f_regressions.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/synthetic_mission17d/test_mission17f_regressions.py), [`synthetic_mission18a/test_isolation.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/synthetic_mission18a/test_isolation.py), and [`synthetic_mission18b/test_provenance.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/synthetic_mission18b/test_provenance.py) with deterministic AST transitive import closure verification, preserving `SYNTHETIC_ONLY` status.
2. **Fail-Closed Auth Gate Assertion ([`test_exploratory_subset_authorization_gate.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_exploratory_subset_authorization_gate.py#L69-L88)):** Verifies that `validate_all_included_events(cfg)` raises `MediaAccessAuthorizationError` (`AUTH_MEDIA_ACCESS_NOT_GRANTED`) while `AUTH-MEDIA-ACCESS.json` is absent, and still executes full 11-event validation automatically if the signed authorization exists.
3. **AST Raw-Media Opener Guard Coverage ([`test_media_opener_coverage.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_media_opener_coverage.py)):** Guarded `_sha256_file` in both [`exp_r_validation.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/experiments/exp_r_validation.py) and [`prepare_pi_approval_package.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/prepare_pi_approval_package.py) with `require_media_authorization(path, "HASH_RAW_MEDIA")` directly before file reads (`8/8` opener coverage tests pass).
4. **Access Registry & Suite Results (`tests/test_access_classification.yaml`):** `179` test files classified (`116` `synthetic_only`, `29` `metadata_only`, `15` `model_checkpoint_access`, `5` `processed_data_access`, `5` `raw_media_access`, `9` `unknown`, `145` `safe_for_synthetic_runner`). Safe synthetic runner executes `3,285 passed, 0 failed, 0 errors, 0 skipped, violations: []`; full `pytest -q tests/ --tb=line --import-mode=importlib` executes **`3,881 passed, 0 failed`**.

---

## C. Reproducibility Audit Breakdown (`8 PASS, 3 UNRESOLVED, 2 NOT_AVAILABLE, 0 FAIL`)

Inspected directly via `scripts/audit_reproducibility.py` and `scripts/check_zero_blocker_readiness.py` (`11/11` `technical_checks: true`):

- **`PASS` (`8`):** `dataset_manifests`, `protocol_version`, `r04_scope_decision`, `model_checkpoint_fingerprints`, `config_and_policy_fingerprints`, `dependency_lock` (`50/50` packages match), `ultralytics_importable`, `manuscript_claims_vs_evidence` (`0` unsupported claims across `docs/PHASE16_MANUSCRIPT_DRAFT.md` and `docs/PHASE16_MANUSCRIPT_CORRECTION_v1.md`).
- **`UNRESOLVED` (`3` — Strictly Human Governance Gates):**
  1. `approved_ground_truth`: `0` valid Stage-2.1 records (`receipt: absent_or_invalid`); 27 legacy `6.0.0` records are excluded by invalidation notices and never substitute for Stage-2.1 ground truth.
  2. `event_split_decision`: no `phase12_event_split_decision.json` exists while `Option A` remains active; none is fabricated.
  3. `unresolved_decisions`: aggregates the remaining human-required decisions (`approved_ground_truth` & `event_split_decision`).
- **`NOT_AVAILABLE` (`2` — Pre-Execution Boundary):**
  1. `evaluation_result_provenance`: no official Phase-12 evaluation result exists yet (`ready: false`).
  2. `experiment_manifest_completeness`: no official Phase-13 experiment manifest exists yet.
- **Preserved Archival Source (`FAIL` retained as audit record):** `Railway_Crossing_Automation_Research_Report.docx` (`historical_claim_audit_status: FAIL`, `disposition: preserved_with_findings`).

---

## D. Independent Non-Raw `Exp R` Cache Validation & Documentation Accuracy Audit

[`src/railway_detection/experiments/exp_r_validation.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/experiments/exp_r_validation.py) and [`scripts/validate_exp_r_independently.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/validate_exp_r_independently.py) re-computed 23-fold LOEO CV directly from non-raw Mission 44 `ALL_AUDIO_WINDOW_SCORES.csv` + Mission 43 JSONLs ([`exp_r_independent_validation.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/exp_r_independent_validation.json); `4/4` tests passing across `test_exp_r_independent_validation.py` & `test_exp_r_live_corpus_parity.py`):

1. **Non-Raw Cache & Artifact Parity:** `manifest_sha256_all_match: true`, `n_events_verified: 27`, `n_total_windows: 2,600` (`2,470` `audio23` + `116` `no_train` + `14` `engine`), `max_csv_vs_jsonl_abs_diff: 0.0`, `exact_match_within_published_4dp: true`, `oof_metrics_match_within_4dp: true`, `calibration_match_within_4dp: true`, `fold_mismatches: []`, `max_oof_prob_abs_diff: 4.9e-05`.
2. **Methodological & Statistical Caveats Propagated:**
   - **Recall vs Specificity Trade-Off:** OOF specificity improves (`0.0000 -> 0.6000`) while point `F1` drops (`0.6857 -> 0.6400`, bootstrap 95% CI `[0.4167, 0.8148]`) and point `Recall` drops sharply (`0.9231 -> 0.6154`, Wilson CI `[0.3552, 0.8229]`).
   - **Calibration Brier Uncertainty:** OOF Brier point reduction (`0.2724 -> 0.2366`, Δ `-0.0358`) has 95% bootstrap CI `[-0.0839, +0.0104]` crossing `0` (`n=23`, not statistically significant at `alpha=0.05`).
   - **`no_train` Tiebreak Sensitivity:** Removing the external `no_train` tiebreak (`use_no_train_tiebreak=False`) alters tiebreak choices on `train_events/event_003` & `event_023` to `(tau=0.37, k=3)` with identical OOF metrics (`F1=0.64, Spec=0.60, Recall=0.6154, Brier=0.2366, ECE=0.0999`).
   - **Temperature Grid Ceiling Sensitivity:** Expanding `temp` grid from `4.0` to `15.0` eliminates the `9/23` fold ceiling clamp (`temps_hitting_ceiling_count = 0`, `mean T = 3.7217`, `max T = 4.2`), yielding essentially identical `Brier = 0.2379` (Δ CI `[-0.0826, +0.0120]`) and `ECE = 0.1007`.
   - **Window-Count & Synthetic Corrections:** Corrected `2,730 -> 2,600` total audio window count errors across `9` active documents + `AGENT_EXPERIMENT_LOG.md` + `README.md`, and labeled `RULE_L3_OPTICAL_DEGRADED_AUDIO_WAKEUP` (`enable_optical_degradation_audio_wakeup = False` default) explicitly as `SYNTHETIC_ONLY`.

---

## E. Raspberry Pi 4B / 5 Installation & Telemetry Readiness (`physical_raspberry_pi_tested = false`)

- **New Modules & Runbook:** [`pi_telemetry.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/optimization/pi_telemetry.py) (`read_linux_vmhwm_mb`, `read_soc_thermal_celsius`, `read_cpu_governor`, `collect_host_telemetry`, `benchmark_synthetic_opencv_preprocess`; `3/3` tests passing), [`scripts/rpi_edge_benchmark.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/rpi_edge_benchmark.py) (`schema_version: "rpi-edge-benchmark/1.1"`), and [`RASPBERRY_PI_DEPLOYMENT_RUNBOOK.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/RASPBERRY_PI_DEPLOYMENT_RUNBOOK.md).
- **Updated Host Reference Baseline ([`host_edge_scaling_benchmark.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/host_edge_scaling_benchmark.json), Darwin Apple M1 `arm64`, `physical_raspberry_pi_tested = false`):**
  - `416px` TorchScript (`1/2/4T`): `28.025 / 20.921 / 16.839 ms` (`59.39 FPS` @ 4T).
  - `320px` TorchScript (`1/2/4T`): `17.150 / 13.537 / 11.523 ms` (`86.78 FPS` @ 4T).
  - Audio (`4T`): `0.384 ms` TS (`2,602.27 win/s`), `0.405 ms` log-Mel.
  - Synthetic OpenCV `1080p -> ROTATE_90_CLOCKWISE -> 416px` (`SYNTHETIC_ONLY`): `16.980 ms` (`p50 16.994`, `p95 17.029`).
  - Peak RSS: `452.45 MB`; stripped FP16 `6,154,766 B` (`6.15 MB`); `max_abs_diff = 0.0`.
- Physical SBC benchmarks (`Pi 4B / Pi 5`) MUST still be measured directly on Raspberry Pi hardware per Section 4 of the runbook before promoting any hardware latency claim from analytical projection to measured evidence.

---

## F. Official Phase-12 Execution Gate Confirmation (`evaluation run` Blocked)

Running `PYTHONPATH=src:. .venv/bin/python -m railway_detection evaluation status` exits `3` with `ready: false` and `7` remaining human blocker instances across `5` codes:
- `STAGE21_RECORDS_MISSING`
- `COHORT_APPROVAL_MISSING` (`3` cohorts: `train_events`, `no_train_events`, `engine_events`)
- `EVENT_SPLIT_DECISION_MISSING`
- `MANIFEST_MISSING`
- `EVAL_AUTH_NOT_GRANTED`

Accordingly, official `railway_detection evaluation run` was **NOT** executed. Full integrity verification confirms all `23/23` historical `Exp A–N` artifacts under [`results/exploratory_v2/FILE_HASH_MANIFEST.sha256`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/FILE_HASH_MANIFEST.sha256) remain SHA-256 bit-identical.
