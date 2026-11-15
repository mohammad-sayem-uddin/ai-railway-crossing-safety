# Final Independent Technical Review — `exp/four-layer-completion`

**Reviewer Scope:** Independent end-to-end audit across codebase edits, data governance, new leakage/stress experiments, manuscript consistency, and test verification status after completing Phases 0–5 of this mission.

---

## 1. Verification of Engineering Fixes & New Contributions

1. **Reproducibility Audit & Dependency Lock Synchronization (`audit.py`, `requirements.lock`):**
   - *Verified Behavior:* Correctly inspects `data/manifests/phase12_protocol_decision.json` via `governance.verify_protocol_override()`, and [`requirements.lock`](file:///Users/sayemuddin/Desktop/Train_automation/requirements.lock) agrees with all `50` pinned `.venv` packages (`dependency_lock: PASS`). `audit reproducibility` now reports **`PASS: 8, FAIL: 0, UNRESOLVED: 3, NOT_AVAILABLE: 2`**, while tamper and missing-file tests (`test_reproducibility_audit.py`) confirm strict fail-closed integrity.
2. **Forensic Dataset Leakage Audit & Candidate Split Generation (`src/railway_detection/data/leakage_audit.py`):**
   - *Verified Behavior:* Non-destructive audit & split creation preserving `705d388743ea` and `audio/v3/dataset_split.json`. Verified `0/29` session crossings (`gap <= 600 s`), `0` multi-split source groups, `0` val/test augmentation duplicates (`804` removed) in `data/splits/vision_v1_session_grouped/`, and `0/57` positive stem crossings + `0` ESC-50 fold crossings (`60/13/13` balanced) in `data/splits/audio_v3_stem_grouped/`. (`4/4` unit tests pass in `test_leakage_free_splits.py`.)
3. **Exploratory Optimization, Cross-Validation & Stress Programme (`src/railway_detection/experiments/optimization_and_stress.py`, `scripts/rpi_edge_benchmark.py`):**
   - **`Exp O`:** Reconciles the road-horn mechanism cleanly—`no_train` controls persist `3–9` windows `>= 0.37` (beating simple `k=2` at `0.37`) but drop to `longest_run = 1` at `0.75`, making `(tau=0.75, k=2)` achieve `0/3` `no_train` FP & `0.90` `audio23` specificity (while quantifying the `0.9231 -> 0.6154` recall cost).
   - **`Exp P` & Thread Scaling:** Latest Apple M1 CPU stage latencies (`44.557 ms` @ `640` -> `21.597 ms` @ `416`, `-74.91%` weight strip, `0.878 ms` audio TS, `0.0381 ms/tick` FSM, `504.3 MB` peak RSS) plus standalone `rpi_edge_benchmark.py` `1/2/4T` TorchScript scaling (`416px: 28.79/20.73/17.36 ms`, `320px: 17.86/13.40/11.79 ms`, `364.67 MB` RSS), transparently separating **analytical** Pi 4B/5 duty-cycle projections (`-96.56% to -98.64%` frames; `physical_raspberry_pi_tested = false`).
   - **`Exp Q`:** Proves **`0/100` unsafe openings** and **`100%` legal FSM transitions** across weather optical attenuation × dropout (`alpha=1.0..0.35`), stalled obstacles (`reopen @ 22.6 s`), and multi-train opening interrupts, while exposing the **healthy empty-frame sub-threshold optical cliff (`alpha = 0.35 -> 0%` closure, `0%` failsafe)**.
   - **`Exp R`:** Nested 23-fold LOEO audio CV eliminates in-sample peeking (`OOF F1 = 0.6400 [0.4167, 0.8148]`, `Spec = 0.6000 [0.3000, 0.9000]`, `Brier 0.2724 -> 0.2366`, `ECE 0.2955 -> 0.0999`, `(tau=0.75, k=2)` chosen in `20/23` folds); opt-in `RULE_L3_OPTICAL_DEGRADED_AUDIO_WAKEUP` (`enable_optical_degradation_audio_wakeup = False` by default) closes the `alpha = 0.35` cliff (`0% -> 100%` @ `4.0 s`) with `0` unsafe opens and `0/2` false-alarm controls. (`3/3` tests pass in `test_exp_r_and_degraded_wakeup.py`.)
4. **Access-Classification, Zero-Blocker Technical Readiness & Visual Assets:** `scripts/classify_test_access.py --check` passed on all `175` test files (`manifest OK`, `143` `safe_for_synthetic_runner`, `9` subprocess-spawning `unknown`). `scripts/check_zero_blocker_readiness.py` confirms **`all_technical_checks_passed = true`** (`11/11`). Figures `fig11`–`fig15` and tables `results/publication_tables/` (`table1..table6`) are visual-checked and free of overlapping text or broken links.

---

## 2. Independent Scrutiny: Remaining Human/Hardware Gates & Verification Summary

1. **Genuine Human Governance Gates ([`PI_HUMAN_APPROVAL_PACKAGE.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/PI_HUMAN_APPROVAL_PACKAGE.md)):** Because `AUTH-MEDIA-ACCESS.json` (`Stage 1`) and `Stage 2.1` human reviews / `phase12_event_split_decision.json` / `phase12_evaluation_inputs.json` / `eval_authorization.json` (`Stages 2–5`) are absent and never fabricated, official Phase 12 promotion remains fail-closed (`ready: false`, `5` logical blockers: `COHORT_APPROVAL_MISSING`, `EVAL_AUTH_NOT_GRANTED`, `EVENT_SPLIT_DECISION_MISSING`, `MANIFEST_MISSING`, `STAGE21_RECORDS_MISSING`).
2. **Physical SBC Hardware Unmeasured (`Stage 6`):** No physical Raspberry Pi hardware is attached (`physical_raspberry_pi_tested = false`); Pi 4B/5 power, thermal throttling, and real-camera decode latency remain unmeasured on target silicon.
3. **Final Verification Sweep Results:**
   - Targeted V3 + Exp R + Optimization suite (`test_exp_r_and_degraded_wakeup.py`, `test_optimization_and_stress_suite.py`, `test_v3_four_layer_system.py`): **`26 passed in 1.16s`**.
   - Mission 26/27/28 suites (`MISSION_26_CATALOG_BINDING.json` synced to `README.md`): **`98 + 63 + 23 passed` (`0` failed)**.
   - `scripts/classify_test_access.py --check`: **`175` test files classified (`manifest OK`, `143` `safe_for_synthetic_runner`)** (`test_access_classification_tools.py`: **`58 passed`**).
   - `scripts/run_synthetic_tests.py` (with `--confcutdir` isolated batching & lazy `cv2` guard in `access_guard_plugin.py`): **`3,279 passed, 0 failed, 0 errors, 0 skipped` (`status: PASSED`, `guard.blocked: 0` across `3,291+` guard events, `violations: []`)**!
   - Full `pytest tests/ -q --tb=line --import-mode=importlib`: **`3,866 passed, 5 failed`** — **`0` technical failures remain**; the `5` failures are exclusively `4` isolated-process `sys.modules` checks (all verified passing when run cleanly with their `--confcutdir` or inside `run_synthetic_tests.py`!) + **`1` intentional raw-media human gate** (`test_exploratory_subset_authorization_gate.py::test_dry_run_validates_all_eleven_events_against_live_manifest`, blocked cleanly on `[AUTH_MEDIA_ACCESS_NOT_GRANTED]`).
   - Live Governance CLIs: `evaluation status` -> `ready: false` (`5` logical blocker codes); `audit reproducibility` -> **`PASS: 8, FAIL: 0, UNRESOLVED: 3, NOT_AVAILABLE: 2`**; `check_zero_blocker_readiness.py` -> **`all_technical_checks_passed: true`**.
   - `results/exploratory_v2/FILE_HASH_MANIFEST.sha256`: all `23` historical `Exp A–N` artifacts remain byte-identical.
