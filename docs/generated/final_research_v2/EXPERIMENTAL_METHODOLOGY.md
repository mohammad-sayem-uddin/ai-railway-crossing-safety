# Experimental Methodology — Four-Layer Multimodal Railway Crossing Prototype

**Execution Script:** [`run_v2_experiments.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/run_v2_experiments.py)  
**Shared Baseline Helpers:** [`exploratory_common.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/exploratory_common.py)  
**Qualification Boundary:** Cached real-data replays (`pre-db40305` unrotated Mission 43/39 JSONL vision detections + Mission 44 `ALL_AUDIO_WINDOW_SCORES.csv`) evaluated against researcher-adopted AI-assisted reference annotations, paired with controlled synthetic closed-loop & fault-injection suites. Raw media under `data/` was never opened (`data/governance/AUTH-MEDIA-ACCESS.json` absent; enforced fail-closed by [`media_guard.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/safety/media_guard.py)).

---

## 1. Anti-Tuning Discipline & Pre-Registered Parameters

Zero post-hoc threshold retuning was performed against the test cohorts (`all27`, `sync11`, `audio23`). All inference and decision thresholds were locked from frozen baseline configurations ([`frozen_experiment_v1.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/configs/frozen_experiment_v1.yaml), [`decision_policy_v1.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/configs/decision_policy_v1.yaml), and [`decision_policy_v2_candidate.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/configs/decision_policy_v2_candidate.yaml)) and architectural V3 conservative parameters in [`rules_v3_four_layer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/rules_v3_four_layer.py) and [`decision_engine_v3_four_layer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/decision_engine_v3_four_layer.py):

- **Audio horn threshold:** `0.3700` (locked in Mission 44 on natural log-Mel scale).
- **Approach detection confidence:** `0.35`, **confirmation window:** `confirm_frames = 2`, **warning dwell:** `warning_dwell_s = 2.0 s`, **gate closing stroke:** `closing_duration_s = 3.0 s` (`half_closed` reached after `closing_duration_s / 2`, i.e., `1.5 s` from close command — note `1.4 s` after discrete `0.20 s` step boundary in fixed-step simulation logs).
- **Evidence freshness & cadence tolerance:** `temporal_tolerance_s = 0.50 s`, `evidence_freshness_timeout_s = 2.0 s`, **clearance dwell:** `clearance_dwell_s = 1.5 s`.
- **Gate step resolution:** Uniform `0.200000 s` discrete Convention A simulation cadence via [`EventSimulationRunner.run_frames()`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L88) with strictly non-backfilling causal [`MultimodalEvidenceCollector`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/collector.py) snapshots (`step_count = 121` over `24.0 s` synthetic runs; `step_count = 60` for `16_false_train_detection_glitch`; [`run_frames_convention_b()`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L82) remains preserved explicitly for constructed Convention B checks).

---

## 2. Evaluation Cohorts & Data Provenance

| Cohort Name | Events Included | Purpose in Programme |
| --- | --- | --- |
| **`all27` (B4)** | `train_events/001..023` (`23`), `no_train_events/001..003` (`3`), `engine_events/001` (`1`) | Approach closure trigger evaluation (`Exp A`), fusion progression (`Exp F–H`), causal vs legacy backfill (`Exp I`), temporal vs stateless (`Exp J`), sensitivity sweeps (`Exp M`), full matrix (`Exp N`) |
| **`sync11`** | `11` train events with synced `camera_1`/`camera_2` offsets ([`camera_sync_offsets_candidate.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/camera_sync_offsets_candidate.yaml)): `001, 002, 005, 006, 007, 009, 011, 012, 013, 014, 017` | Closed-loop arrival-before-`T2`, departure premature-opening comparison vs `T4_master` (`Exp D`, `Exp I`), real modality ablation (`Exp K`) |
| **`audio23`** | `23` `train_events` (`13` `present`, `10` `absent_observed` horn labels; `2,600` windows total across all audio events) | Event-level acoustic recall/precision/specificity/ROC-AUC/AP evaluation (`Exp C`); `no_train_events/001..003` (`horn_status=None`, road traffic horns present) and `engine_events/event_001` (`absent_observed`) reported separately |
| **Synthetic Suites** | Multi-angle `ffmpeg` videos (`0, ±90°, ±180°, ±270°`), natural vs dB log-Mel check, 4-layer nominal + `SideMovementTracker` + `OccupancyVerifier` + 18 scenarios + `sparse_dropout` | Functional verification of display-rotation normalization, log-Mel scaling, Layer 2 motion logic, Occupancy gate, 4-layer nominal cycle, and fail-safe fault handling (`Exp B, D, E, K, L, M`) |

---

## 3. Causal Collector & Policy Comparison Design

1. **Causal Collector Semantics ([`collector.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/collector.py)):**
   - With `allow_stale_detection_backfill=False`, an ingested observation is emitted at most once on the snapshot consuming its `source_timestamp <= snapshot_time`. If a source skips a `0.20 s` frame (or misses a window > `temporal_tolerance_s`), subsequent frames observe `OBSERVED_EMPTY` / missing detection rather than re-emitting the previous frame's bounding box.
   - To measure the exact historical impact of stale backfill, `Exp I` compares the causal `V3` collector directly against `allow_stale_detection_backfill=True` across all `23` B4 train events.
2. **Departure Policy Comparison (`Exp D`, `sync11` + `sparse_dropout`):**
   - **`V1_RULE_3`:** Baseline rear-disappearance departure rule.
   - **`V2_RULE_3B_3C`:** Candidate disappearance rule (`rule_3b` / `rule_3c`).
   - **`V3_GUARDED_DISAPPEARANCE`:** Explicit comparison mode allowing disappearance departure when occupancy clear + timeout guards pass.
   - **`V3_CONSERVATIVE_POSITIVE` (Default Prototype Policy):** Requires positive Layer 4 departure evidence (`rear` and optional `last_carriage`) AND explicit `OccupancyState.CLEAR` AND healthy sensors AND zero contradictions AND `clearance_dwell_s`. On real `sync11` events (where physical occupancy hardware is absent and `OccupancyState == UNKNOWN`), V3 holds `CLOSED` / `FAULT_FAIL_SAFE` rather than guessing `CLEAR`.
3. **Temporal vs Stateless Baselines (`Exp J`, `all27`):**
   - **`stateless_union`:** Triggers immediate closure on any single frame with vision (`conf >= 0.35`) or audio (`score >= 0.37`) above threshold.
   - **`stateless_vision_rule2`:** Triggers closure on any single frame with vision `conf >= 0.35`.
   - Compared against temporal `V1`, `V2`, and `V3_CONSERVATIVE` state machines for `train23` triggers, `no_train3` false closures, `sync11` premature openings, and FSM transition legality (`transition_legal`).

---

## 4. Statistical & Engineering Calculations

- **Confidence Intervals:** Two-sided **95% Wilson score intervals** computed on binomial proportions (`train23` closure rate in `Exp A`; `audio23` recall, precision, specificity, and accuracy in `Exp C`).
- **Paired Nominal Hypothesis Tests:** Two-sided **exact McNemar tests** (`discordant pairs = b01 + b10`) comparing:
  - `V2_RULE_3B_3C` vs `V3_CONSERVATIVE_POSITIVE` on `sync11` premature openings (`Exp D`).
  - `stateless_union` vs `V3_CONSERVATIVE` on `no_train3` false closures (`Exp J`).
- **Continuous Discrimination (`Exp C`):** Event-level maximum window score `ROC-AUC` and `Average Precision (AP)` over `audio23` (`n=23`, `13` positive, `10` negative). Note that frame/window-level acoustic labels do not exist in adopted metadata, precluding valid window-level ROC/PR reporting.
- **Required Upstream Warning Distance (`Exp A`):** Evaluated parametrically for speeds $v \in \{30, 40, 60, 80, 100\}\text{ km/h}$ under three latency/margin profiles (`fast_close_0s_warning` `5.6 s`, `baseline_with_2s_warning` `7.6 s`, `conservative_high_margin` `10.2 s`):

$$
d_{\mathrm{req}}(v) = \frac{v_{\mathrm{km/h}}}{3.6}\,(t_{\mathrm{det}} + t_{\mathrm{confirm}} + t_{\mathrm{warning}} + t_{\mathrm{close}} + t_{\mathrm{margin}})
$$

---

## 5. Experiment Matrix (`Exp A` – `Exp N`)

| ID | Artifact Path | Focus |
| --- | --- | --- |
| **Synthetic** | `synthetic/vision_orientation_check.json`, `synthetic/audio_transform_check.json` | 7-angle rotation normalization + CPU `YOLOv8n` + natural log-Mel scale check |
| **Exp A** | `experiments/exp_a_front_detection.json` | Layer 1 front approach trigger, warning/closing timing decomposition, upstream distance |
| **Exp B** | `experiments/exp_b_side_detection.json` | Real proxy `side` labels (`camera_1`/`camera_2`) + synthetic `SideMovementTracker` |
| **Exp C** | `experiments/exp_c_audio_horn.json` | Acoustic horn classification (`audio23`) + `no_train3` + `engine1` |
| **Exp D** | `experiments/exp_d_back_departure.json` | Departure policy comparison (`V1`, `V2`, `V3_GUARDED`, `V3_CONSERVATIVE`) on `sync11` & sparse dropout |
| **Exp E** | `experiments/exp_e_occupancy.json` | Occupancy hardware gap (`0/27`) + synthetic 5-state `OccupancyVerifier` checks |
| **Exp F–I** | `experiments/exp_f..exp_i*.json` | Incremental sensor combinations, causal vs stale-backfill comparison, synced 4-layer V3 run |
| **Exp J** | `experiments/exp_j_temporal_vs_stateless.json` | Stateless (`union`, `vision_rule2`) vs temporal state machines (`V1`, `V2`, `V3`) |
| **Exp K** | `experiments/exp_k_ablation.json` | Layer ablation on real `sync11` and controlled synthetic 4-layer cycle |
| **Exp L** | `failure_injection/exp_l_fault_injection.json` | 18 closed-loop nominal + fault scenarios & transition legality audit |
| **Exp M** | `sensitivity/exp_m_sensitivity.json` | 8 one-at-a-time parameter sweeps on real `all27` and synthetic nominal |
| **Exp N** | `experiments/exp_n_event_matrix.csv`, `.json` | Complete 27-event provenance & outcome matrix |
