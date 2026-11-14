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
- **Added IEEE Manuscript & 13 Section 16 Reports (`docs/generated/`):** `IEEE_MANUSCRIPT_TRAIN_GATE_AUTOMATION.md`, `PROJECT_STATE_RECONSTRUCTION.md`, `COMPLETE_PROJECT_AUDIT.md`, `RESEARCH_GAP_AND_NOVELTY_AUDIT.md`, `DATASET_AND_GROUND_TRUTH_AUDIT.md`, `RESEARCH_DECISION_LOG.md`, `IMPLEMENTATION_ROADMAP.md`, `EXPERIMENTAL_PROTOCOL.md`, `EXPERIMENT_RESULTS.md`, `SAFETY_AND_STATE_MACHINE_AUDIT.md`, `REPRODUCIBILITY_REPORT.md`, `RASPBERRY_PI_READINESS_REPORT.md`, `PUBLICATION_READINESS_REPORT.md`, `FINAL_INDEPENDENT_REVIEW.md`, plus updated `AGENT_*.md` living logs.
