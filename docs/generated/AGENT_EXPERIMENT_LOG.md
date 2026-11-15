# Agent Experiment Log

Records only **directly executed** commands, inputs, parameters, and verified outputs produced during this mission (`exp/four-layer-completion`). Existing historical runs (`Exp A–N` in `results/exploratory_v2/`) remain cleanly preserved and referenced separately.

---

## Verified Baseline Telemetry Check (Pre-Edit Verification)

- **EXP-BASE-01 (`evaluation status`, 2026-11-14):** `ready=false`, `blocker_count=7`, `blocker_codes=["COHORT_APPROVAL_MISSING", "EVAL_AUTH_NOT_GRANTED", "EVENT_SPLIT_DECISION_MISSING", "MANIFEST_MISSING", "STAGE21_RECORDS_MISSING"]`; `protocol_profile_sha256=6b5edb4852fc0d16a10ac1975f3f18d6feb28fe91638971da7d3761a7a6d42ca`, `r04_scope_decision_sha256=f6eabebaab9a925628c119feb9638ba108b7e0c3fbcb942efdf890c2d6e5fc08`.
- **EXP-BASE-02 (`audit reproducibility` pre-fix vs post-fix, 2026-11-14):**
  - Pre-fix: `{"FAIL": 1, "NOT_AVAILABLE": 2, "PASS": 6, "UNRESOLVED": 4}`.
  - Post-fix (`audit.py` Fix D-01): `{"FAIL": 1, "NOT_AVAILABLE": 2, "PASS": 7, "UNRESOLVED": 3}` (`protocol_version = PASS`).
- **EXP-BASE-03 (Checkpoint & Dataset Forensic Inspection, 2026-11-14):**
  - Vision `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`: `24,493,159` bytes (`24.49 MB`), `epoch=92`, `best_fitness=0.76841`, `DetectionModel` (`3,011,433` params, `6,044,122` weight+buffer bytes in FP16), includes `optimizer` & `ema` states.
  - Audio V3 `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`: `329,497` bytes (`0.33 MB`), `epoch=34`, `25,989` state params (`25,697` module params, `103,972` weight bytes), `has_optimizer=False`.

---

## Executed Mission Experiments (`exp/four-layer-completion`, 2026-11-14)

- **`EXP-SPLIT-AUDIT-01` (`scripts/run_leakage_and_split_audit.py` -> `results/dataset_audit/vision_audio_leakage_audit.json`):**
  - Vision V1 (`3,157` manifest entries, `1,315` unique `split_group_id`s across `13` dates; `29` sessions at `gap<=600 s`):
    - `705d388743ea`: `27/29` (`93.1%`) sessions cross splits; `447/447` (`100%`) timestamped test images & `458/458` val images share sessions with `train`; `411/472` (`87.1%`) `test` images originate from Roboflow `train/`.
    - Original Roboflow: `27/29` sessions cross splits; `127/127` timestamped test images overlap `train`.
    - Clean `data/splits/vision_v1_session_grouped/`: `train=1,776 (738 unique)`, `val=336 (336 unique)`, `test=241 (241 unique)`, `804` eval aug duplicates excluded, **`0/29` crossing sessions up to `gap=600 s`**, `0` multi-split groups. (`gap >= 1800 s` crosses on `2` sessions due to continuous `2026-07-08` screenshots.)
  - Audio V3 (`172` clips: `86` pos / `86` neg):
    - Original `audio/v3`: `0` cross-split ESC-50 folds, but **`5/57` unique YouTube horn stems (`28/86 = 32.56%` of pos clips)** cross splits.
    - Clean `data/splits/audio_v3_stem_grouped/`: balanced `60/60`, `13/13`, `13/13` with **`0/57` cross-split stems** and **`0` cross-split ESC-50 folds**.

- **`Exp O` (`scripts/run_optimization_and_robustness_suite.py` -> `exp_o_audio_calibration_hysteresis.json`):**
  - Evaluated across `2,600` `audio23` + `116` `no_train` + `14` `engine` = `2,730` cached windows:
    - Frozen `(tau=0.37, k=1)`: `Rec=0.9231`, `Spec=0.0000`, `Prec=0.5455`, `F1=0.6857`, `Acc=0.5217`, `no_train_fp=3/3`, `engine_fp=0/1`.
    - Run-length insight: `no_train` events `001, 002, 003` have `longest_run_ge_0_37 = 3, 5, 9` (defeating `k=2` at `0.37`), whereas `longest_run_ge_0_75 = 1` across all 3.
    - Best field Pareto `(tau=0.75, k=2)`: `TP=8, FP=1, TN=9, FN=5`, **`Spec=0.9000`, `Prec=0.8889`, `Acc=0.7391`, `F1=0.7273`, `no_train_fp=0/3`, `engine_fp=0/1`, `Rec=0.6154`**.
    - Exploratory 5-bin temperature scaling: `T=1.0 -> ECE 0.2955 (Brier 0.2724)`, `T=3.0 -> ECE 0.0709 (Brier 0.2246)`.

- **`Exp P` (`scripts/run_optimization_and_robustness_suite.py` -> `exp_p_cpu_edge_benchmark.json`, `SYNTHETIC_ONLY` on Apple M1 CPU, `threads=4`, `physical_raspberry_pi_tested=false`):**
  - Weight stripping: `24,493,159 B` -> `6,145,232 B` FP16 (`-74.91%`) / `12,188,432 B` FP32. Peak RSS: `491.52 MB`.
  - Vision forward FP32 eager (`640/416/320`): `39.938 / 19.141 / 13.217 ms`; TorchScript (`diff=0.0`): `38.603 / 18.253 / 13.155 ms`.
  - E2E `YOLO.predict`: `640px` `54.658 ms` (`18.30 FPS`) -> `416px` **`23.605 ms` (`42.36 FPS`, `2.32×` speedup)**.
  - Audio `log_mel` (`0.410 ms`) + `CNN TorchScript` (`0.471 ms`, `diff=0.0`, `134,358 B`) = `0.881 ms/window`; `CNN INT8 Linear` = `0.563 ms` (`109,005 B`, `diff=0.0601`).
  - `V3 FSM + Collector + Gate` (`121` ticks): **`4.737 ms` (`0.0391 ms/tick`, `25,575 Hz`)**.
  - Duty-cycle daily frames: `864,000` (continuous `5-FPS` dual-cam) -> `11,760 / 17,760 / 29,760` (`10/20/40` trains/d, `-96.56% to -98.64%`), lowering `ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE` (`5.5×`) Pi 4B `416px` load `1.308 -> 0.0274–0.0544` cores (`640px`: `3.0159 -> 0.0506–0.1132` cores).

- **`Exp Q` (`scripts/run_optimization_and_robustness_suite.py` -> `exp_q_weather_and_interlocking_stress.json`, `SYNTHETIC_ONLY`):**
  - `100` runs (`alpha_conf in [1.0, 0.8, 0.6, 0.45, 0.35]` × `p_drop in [0.0, 0.15, 0.30, 0.50]` × `5` seeds): **`0` unsafe openings, `0` illegal transitions**.
  - `alpha >= 0.45` (`eff_conf >= 0.396`): `100%` closure; `alpha = 0.35` (`eff_conf = 0.308 < 0.35`): sharp cliff to `0%` closure (`1.0` `miss_open_rate`, `0.0` `failsafe_rate` via healthy empty frames).
  - Stalled obstacle (`[4.0..20.8 s]`) holds gate safely closed until `t_reopen = 22.6 s`; multi-train interrupt at `14.8 s` safely reverses `GATE_OPENING -> GATE_CLOSING`.

- **`Exp R` (`scripts/run_optimization_and_robustness_suite.py` -> `exp_r_crossval_and_failsafe.json`, `exp_r_loeo_folds.csv`, `exp_r_optical_wakeup_ablation.csv`):**
  - 23-fold Nested LOEO CV on Batch-4 `audio23` + `2,000`-resample stratified bootstrap: baseline frozen `(tau=0.37, k=1)` `F1=0.6857, Acc=0.5217, Spec=0.0000, Rec=0.9231, Brier=0.2724, ECE=0.2955` -> **OOF calibrated+hysteresis `(tau=0.75, k=2 in 20/23 folds)`**: `F1=0.6400 [CI95 0.4167..0.8148]`, `Acc=0.6087`, `Spec=0.6000 [0.3000..0.9000]`, `Prec=0.6667`, `Rec=0.6154 [0.3846..0.8462]`, `OOF Brier=0.2366` (Δ CI `[-0.0839..+0.0104]`), `ECE=0.0999`.
  - Opt-in `RULE_L3_OPTICAL_DEGRADED_AUDIO_WAKEUP` (`enable_optical_degradation_audio_wakeup=False` by default, active `visibility<0.45`, `score>=0.75` x `3` frames, occupancy != `CLEAR`): closes `alpha=0.35` (`eff_conf=0.308`) fog cliff (`0% -> 100%` at `4.0 s`, `0` unsafe opens), with `0/2` false closures on clear-sky ambient horn & degraded-optics single-impulse controls.
- **`EXP-EDGE-SCALE-01` (`scripts/rpi_edge_benchmark.py` -> `host_edge_scaling_benchmark.json`, `Apple M1 arm64`, `torch 2.13.0`, `physical_raspberry_pi_tested=false`):**
  - Exported bundles: `vision_416_torchscript=12,602,738 B` (`diff=0.0`), `vision_320_torchscript=12,578,214 B` (`diff=0.0`), `vision_stripped_fp16=6,154,766 B`, `audio_torchscript=131,596 B` (`diff=0.0`), `RSS=364.67 MB`.
  - Thread scaling (`1 / 2 / 4` threads): `416px` `28.790 / 20.729 / 17.361 ms` (`57.60 FPS` @ 4T); `320px` `17.860 / 13.402 / 11.787 ms` (`84.84 FPS` @ 4T); `Audio TS` `0.456 / 0.414 / 0.388 ms` (`2,579 win/s` @ 4T).
- **Access Manifest, Zero-Blocker Check & Tables/Figures Verification:**
  - `scripts/classify_test_access.py --check`: `175` files (`114` `synthetic_only`, `29` `metadata_only`, `14` `model_checkpoint_access`, `4` `processed_data_access`, `5` `raw_media_access`, `9` subprocess-spawning `unknown`, `143` `safe_for_synthetic_runner`) -> `manifest OK`.
  - `scripts/check_zero_blocker_readiness.py`: `all_technical_checks_passed = true` (`11/11`); `audit reproducibility`: `PASS: 8, FAIL: 0, UNRESOLVED: 3, NOT_AVAILABLE: 2`.
  - `scripts/run_synthetic_tests.py`: **`3,279 passed, 0 failed, 0 skipped, 0 violations` (`status: PASSED`)**.
  - `scripts/generate_master_publication_tables.py` -> `PUBLICATION_TABLES.md` + `table1..table6.csv`; `scripts/generate_new_audit_and_edge_figures.py` -> `fig11..fig15.png`.
