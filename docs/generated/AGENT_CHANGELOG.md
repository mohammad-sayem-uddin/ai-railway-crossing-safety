# Agent Changelog

Tracks every file created, edited, verified, or deprecated during this mission on branch `exp/four-layer-completion` (starting commit `62191ef6d8047e204f439c5cd3cc24f526fd04f8`).

---

## [Committed Target — 2026-11-14]

### Code Fixes & New Modules (`src/railway_detection/`)
- **Modified `src/railway_detection/reproducibility/audit.py`:** Synchronized `run_reproducibility_audit()` and `unresolved_register` with live `data/manifests/phase12_protocol_decision.json` via `governance.verify_protocol_override()` while preserving fail-closed `UNRESOLVED` (missing) and `FAIL` (tampered/malformed) semantics.
- **Added `src/railway_detection/data/leakage_audit.py`:** Forensic timestamp/session extractor for Vision V1 (`baler.v1i.yolov8`), canonical YouTube stem extractor for Audio V3, and deterministic non-destructive session-grouped & stem-grouped split builders.
- **Added `src/railway_detection/experiments/optimization_and_stress.py`:** Reproducible engines for `Exp O` (audio calibration & consecutive-window hysteresis), `Exp P` (CPU benchmarking, weight stripping, TorchScript, CNN dynamic INT8, RSS, duty-cycle modeling), and `Exp Q` (synthetic optical attenuation × burst dropout & interlocking stress matrix).

### Tests & Access Classification (`tests/`)
- **Updated `tests/unit/test_reproducibility_audit.py`:** Updated stale Oct-29 live-repo expectations (`protocol_version == "PASS"`, `r04_scope_decision == "PASS"`, `premature_opening_window.startswith("recorded (")`) and added `test_protocol_version_fails_closed_when_override_tampered`.
- **Added `tests/unit/test_leakage_free_splits.py`:** `4` automated invariant tests verifying session/source/stem isolation without touching raw media.
- **Added `tests/unit/test_optimization_and_stress_suite.py`:** `3` synthetic unit tests verifying hysteresis, checkpoint byte reduction, duty cycle, and optical attenuation invariants.
- **Updated `tests/test_access_classification.yaml`:** Classified all `174` test files (`classify_test_access.py --check` -> `manifest OK`).

### Scripts, Clean Candidate Splits, Results & Figures
- **Added `scripts/run_leakage_and_split_audit.py`**, **`scripts/run_optimization_and_robustness_suite.py`**, **`scripts/generate_new_audit_and_edge_figures.py`**, **`scripts/generate_master_publication_tables.py`**.
- **Added non-destructive clean candidate splits:** `data/splits/vision_v1_session_grouped/{split_summary.json,train.jsonl,val.jsonl,test.jsonl}` and `data/splits/audio_v3_stem_grouped/{dataset_split.json,split_summary.json}` (`705d388743ea` and `audio/v3` left untouched).
- **Added reproducible result artifacts:** `results/dataset_audit/vision_audio_leakage_audit.json`, `results/exploratory_v2/optimization_and_stress/` (`exp_o*`, `exp_p*`, `exp_q*`), and `results/publication_tables/` (`PUBLICATION_TABLES.md` + `table1..table5.csv`).
- **Added 300-DPI figures (`docs/generated/figures/`):** `fig11_dataset_leakage_comparison.png`, `fig12_audio_hysteresis_and_calibration.png`, `fig13_cpu_edge_benchmark_and_duty_cycle.png`, `fig14_weather_attenuation_stress_heatmap.png`.

### Documentation & Manuscript Deliverables
- **Updated `README.md`:** Synchronized badges, V3 Four-Layer summary, `Exp A–Q` results, dataset leakage audit summary, live governance status, and reproduction commands.
- **Added IEEE Manuscript & Governance/Research Reports (`docs/generated/`):** `IEEE_MANUSCRIPT_TRAIN_GATE_AUTOMATION.md`, `PROJECT_STATE_RECONSTRUCTION.md`, `COMPLETE_PROJECT_AUDIT.md`, `RESEARCH_GAP_AND_NOVELTY_AUDIT.md`, `DATASET_AND_GROUND_TRUTH_AUDIT.md`, `RESEARCH_DECISION_LOG.md`, `IMPLEMENTATION_ROADMAP.md`, `EXPERIMENTAL_PROTOCOL.md`, `EXPERIMENT_RESULTS.md`, `SAFETY_AND_STATE_MACHINE_AUDIT.md`, `REPRODUCIBILITY_REPORT.md`, `RASPBERRY_PI_READINESS_REPORT.md`, `PUBLICATION_READINESS_REPORT.md`, `FINAL_INDEPENDENT_REVIEW.md`, `PI_HUMAN_APPROVAL_PACKAGE.md`, plus updated `AGENT_*.md` living logs.

---

## [Zero-Blocker Remediation & `Exp R` — 2026-11-14]

### Technical Blocker Fixes (`src/`, `scripts/`, `tests/`, `requirements.lock`, `docs/generated/master_reaudit/`)
- **Synchronized `requirements.lock`:** Updated pinned versions to match `.venv` (`50/50` packages pass `dependency_lock` -> `audit reproducibility` `PASS: 8, FAIL: 0`).
- **Extracted [`src/railway_detection/config/constants.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/config/constants.py):** Decoupled `DEFAULT_EXPERIMENT_REGISTRY` / `EXPERIMENT_REGISTRY_ENV` from `cli/main.py` and `tests/conftest.py` so root test discovery stays clean.
- **Lazy `cv2` Wrapping in [`src/railway_detection/safety/access_guard_plugin.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/safety/access_guard_plugin.py):** Replaced eager `import cv2` during guard installation with lazy wrapping via `builtins.__import__` so pure-isolation suites keep `cv2` out of `sys.modules`.
- **Automated `--confcutdir` Subprocess Isolation in [`scripts/run_synthetic_tests.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/run_synthetic_tests.py):** Automatically isolates test subdirectories specifying `--confcutdir=` while preserving full guard log verification (`3,279 passed, 0 failed, 0 skipped`).
- **Guarded Legacy Non-Media Utilities & Registered Metadata Helpers:** Added raw-path refusal guards in `build_m3_mm_manifest.py::cache_info`, `build_m3_mm_manifest_v2.py::sha256_of`, `fix_m3_classification.py::sha256_of`, `run_stage21_review.py::resolve_active_proposal` and registered the `6` verified non-media helpers in `tests/unit/test_media_opener_coverage.py::REVIEWED_METADATA_ONLY`.
- **Synchronized Stale Assertions & Documentary Binding:** Updated `tests/test_phase11_7_governance_controls.py` (dual reviewers), `tests/unit/test_mission4a_governance_and_stage21_safety.py`, `tests/unit/test_phase12_governance.py`, and `"README.md"` SHA-256 in [`MISSION_26_CATALOG_BINDING.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/MISSION_26_CATALOG_BINDING.json) (`98+63+23` M26–28 tests pass).

### `Exp R`, Optical Wakeup & Edge Tooling
- **Modified [`rules_v3_four_layer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/rules_v3_four_layer.py) & [`decision_engine_v3_four_layer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/decision_engine_v3_four_layer.py):** Added `RuleIdV3.RULE_L3_OPTICAL_DEGRADED_AUDIO_WAKEUP` and opt-in `enable_optical_degradation_audio_wakeup: bool = False`.
- **Extended [`optimization_and_stress.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/experiments/optimization_and_stress.py) & [`run_optimization_and_robustness_suite.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/run_optimization_and_robustness_suite.py):** Added 23-fold LOEO audio CV + 2,000-resample bootstrap & optical-wakeup ablation (`Exp R` JSON/CSVs) plus [`test_exp_r_and_degraded_wakeup.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_exp_r_and_degraded_wakeup.py).
- **Added [`scripts/rpi_edge_benchmark.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/rpi_edge_benchmark.py), [`scripts/check_zero_blocker_readiness.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/check_zero_blocker_readiness.py), `fig15`, `table6`, & [`docs/generated/PI_HUMAN_APPROVAL_PACKAGE.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/PI_HUMAN_APPROVAL_PACKAGE.md).**
- **Rebuilt [`tests/test_access_classification.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/tests/test_access_classification.yaml):** Full `175`-file non-incremental classification (`manifest OK`).

---

## [Mission 3 — Governance Completion, Independent `Exp R` Audit & Pi Runbook — 2026-11-15]

### Governance Preparation & Guarded Test Remediation
- **Added [`scripts/prepare_pi_approval_package.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/prepare_pi_approval_package.py) & `docs/generated/approval_packages/` (`11` files):** Deterministically generates unsigned, schema-validated PI human-approval templates & checklists (`AUTH_MEDIA_ACCESS.template.json`, `STAGE21_27_EVENT_REVIEW_CHECKLIST.{json,md}`, `COHORT_APPROVAL_PACKAGES.{json,md}`, `phase12_event_split_decision.candidate.template.json`, `SPLIT_OPTION_A_RECONCILIATION.md`, `EVALUATION_INPUT_MANIFEST_RUNBOOK.md`, `phase12_evaluation_inputs.template.json`, `eval_authorization.template.json`, `PI_APPROVAL_EXECUTION_GUIDE.md`) with `0` fabricated approvals (`tests/unit/test_pi_approval_package.py`: `3/3` passed).
- **Added [`src/railway_detection/synthetic/_isolation_audit.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/synthetic/_isolation_audit.py) & remediated test failures (`32 -> 5 -> 0`):** Replaced order-sensitive `sys.modules` checks in `synthetic_mission17d` & `synthetic_mission18a/b` with deterministic AST transitive closure checks; verified fail-closed `[AUTH_MEDIA_ACCESS_NOT_GRANTED]` behavior in `test_exploratory_subset_authorization_gate.py`; updated `tests/test_access_classification.yaml` (`179` files, `145` `safe_for_synthetic_runner`; `run_synthetic_tests.py`: `3,285 passed, 0 failed`; full `pytest`: `3,881 passed, 0 failed`).

### Independent `Exp R` Audit & Raspberry Pi Runbook
- **Added [`src/railway_detection/experiments/exp_r_validation.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/experiments/exp_r_validation.py) & [`scripts/validate_exp_r_independently.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/validate_exp_r_independently.py):** Reproduced `exp_r_crossval_and_failsafe.json` cleanly from non-raw Mission 43/44 caches (`exact_match_within_published_4dp: true`, `max_oof_prob_abs_diff = 4.9e-5`, `n_events_verified = 27`, `n_total_windows = 2,600`), audited methodological/calibration caveats, and corrected `2,730 -> 2,600` audio window counts across active docs.
- **Added [`src/railway_detection/optimization/pi_telemetry.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/optimization/pi_telemetry.py) & [`docs/generated/RASPBERRY_PI_DEPLOYMENT_RUNBOOK.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/RASPBERRY_PI_DEPLOYMENT_RUNBOOK.md), upgraded [`scripts/rpi_edge_benchmark.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/rpi_edge_benchmark.py) (`v1.1`):** Captures Linux `VmHWM`, SoC temperature, `cpu_governor`, and in-memory OpenCV `1080p->Rotate90->416px` preprocessing (`16.980 ms`); regenerated `host_edge_scaling_benchmark.json` & `table6`.
- **Authored [`docs/generated/MISSION_3_FINAL_GOVERNANCE_REPORT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/MISSION_3_FINAL_GOVERNANCE_REPORT.md), synced `README.md` & `MISSION_26_CATALOG_BINDING.json` (`fc1a746e...`).**
