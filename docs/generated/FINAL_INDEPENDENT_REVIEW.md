# Final Independent Technical Review — `exp/four-layer-completion`

**Reviewer Scope:** Independent end-to-end audit across codebase edits, data governance, new leakage/stress experiments, manuscript consistency, and test verification status after completing Phases 0–5 of this mission.

---

## 1. Verification of Engineering Fixes & New Contributions

1. **Reproducibility Audit Synchronization (`src/railway_detection/reproducibility/audit.py`):**
   - *Verified Behavior:* Correctly inspects `data/manifests/phase12_protocol_decision.json` via `governance.verify_protocol_override()`. `audit reproducibility` now reports `PASS: 7, UNRESOLVED: 3, FAIL: 1, NOT_AVAILABLE: 2` (`protocol_version = PASS` matching `evaluation status`), while tamper and missing-file tests (`23/23 passed` in `test_reproducibility_audit.py`) confirm strict fail-closed integrity.
2. **Forensic Dataset Leakage Audit & Candidate Split Generation (`src/railway_detection/data/leakage_audit.py`):**
   - *Verified Behavior:* Non-destructive audit & split creation preserving `705d388743ea` and `audio/v3/dataset_split.json`. Verified `0/29` session crossings (`gap <= 600 s`), `0` multi-split source groups, `0` val/test augmentation duplicates (`804` removed) in `data/splits/vision_v1_session_grouped/`, and `0/57` positive stem crossings + `0` ESC-50 fold crossings (`60/13/13` balanced) in `data/splits/audio_v3_stem_grouped/`. (`4/4` unit tests pass in `test_leakage_free_splits.py`.)
3. **Exploratory Optimization & Stress Programme (`src/railway_detection/experiments/optimization_and_stress.py`):**
   - **`Exp O`:** Reconciles the road-horn mechanism cleanly—`no_train` controls persist `3–9` windows `>= 0.37` (beating simple `k=2` at `0.37`) but drop to `longest_run = 1` at `0.75`, making `(tau=0.75, k=2)` achieve `0/3` `no_train` FP & `0.90` `audio23` specificity (while quantifying the `0.9231 -> 0.6154` recall cost).
   - **`Exp P`:** Provides reproducible Apple M1 CPU stage latencies (`54.66 ms` @ `640` -> `23.61 ms` @ `416`, `-74.91%` weight strip, `0.881 ms` audio TS, `0.0391 ms/tick` FSM, `491.52 MB` peak RSS) and transparently segregates **analytical** Pi 4B/5 duty-cycle projections (`96.6%–98.6%` frame reduction).
   - **`Exp Q`:** Proves **`0/100` unsafe openings** and **`100%` legal FSM transitions** across weather optical attenuation × dropout (`alpha=1.0..0.35`), stalled obstacles (`reopen @ 22.6 s`), and multi-train opening interrupts, while exposing the **healthy empty-frame sub-threshold optical cliff (`alpha = 0.35 -> 0%` closure, `0%` failsafe)**. (`3/3` unit tests pass in `test_optimization_and_stress_suite.py`.)
4. **Access-Classification & Visual Assets:** `scripts/classify_test_access.py --check` passed on all `174` test files (`manifest OK`, `142` `safe_for_synthetic_runner`). Figures `fig11`–`fig14` and tables `results/publication_tables/` are visual-checked and free of overlapping text or broken links.

---

## 2. Independent Scrutiny: Remaining Defects & Honest Weaknesses

1. **No Raw Media Retraining Possible Under Present Sandbox Governance:** Because `AUTH-MEDIA-ACCESS.json` is absent, neither rotated raw `.mov` re-extraction nor model retraining on `vision_v1_session_grouped` / `audio_v3_stem_grouped` can execute yet.
2. **Pre-Existing Repository Test Debt Left Deliberately Isolated:** As recorded in [`SOFTWARE_TESTING_REPORT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/SOFTWARE_TESTING_REPORT.md), `41` pre-existing test failures exist across `17` historical files (`23` from post-Mission-26 `README.md` hash drift in `catalog.py`, `8` requiring exported `PYTHONPATH=src`, `4` single-process import-order collisions, and `6` strict environment/reviewer/auth gates including `AUTH-MEDIA-ACCESS` absent and `.venv` vs `requirements.lock` drift). Note our `audit.py` fix resolves the `test_reproducibility_audit.py` failure while preserving all governance fail-closed invariants.
3. **Final Verification Sweep Results:**
   - Targeted verification (`test_reproducibility_audit.py`, `test_leakage_free_splits.py`, `test_optimization_and_stress_suite.py`, `test_v3_four_layer_system.py`): **`50 passed in 3.89s`**.
   - `scripts/classify_test_access.py --check`: **`174` test files classified (`manifest OK`, `142` `safe_for_synthetic_runner`)**.
   - `scripts/run_synthetic_tests.py`: **`3,259 passed, 17 pre-existing failed` (`guard.blocked: 0` across `2,929` guard events)** — failures consist exclusively of `13` pre-existing stale `README.md` hash catalog checks (`test_dashboard_cli` `5`, `test_pilot_readiness` `8`), `2` same-process import-order checks (`test_mission17f_regressions`, `test_provenance`), `1` dual-reviewer allowlist check (`test_phase11_7_governance_controls`), and `1` legacy opener coverage check (`test_media_opener_coverage`).
   - Full `pytest tests/ -q --tb=line --import-mode=importlib`: **`3,836 passed, 32 pre-existing failed`** (improved from baseline `3,819 passed, 41 failed` via the `audit.py` fix, exported `PYTHONPATH=src:.`, and `7` new tests; remaining `32` failures are `23` `MISSION_26` `README.md` hash catalog assertions + `4` same-process import-order collisions + `5` strict governance/auth/prereq gates).
   - Live Governance CLIs: `evaluation status` -> `ready: false` (`7` blockers); `audit reproducibility` -> `PASS: 7, UNRESOLVED: 3, FAIL: 1, NOT_AVAILABLE: 2`.
   - `results/exploratory_v2/FILE_HASH_MANIFEST.sha256`: all `23` historical `Exp A–N` artifacts remain byte-identical.
