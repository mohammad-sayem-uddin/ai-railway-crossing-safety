# Experimental Results — Four-Layer Multimodal Railway Crossing Prototype

**Artifact Root:** `results/exploratory_v2/` (`23` deterministic JSON/CSV files, verified bit-identical across consecutive runs)  
**Aggregate Summary:** [`MASTER_V2_SUMMARY.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/MASTER_V2_SUMMARY.json)  
**Master Event Table:** [`exp_n_event_matrix.csv`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_n_event_matrix.csv)  

---

## 1. Synthetic Vision Orientation & Natural Log-Mel Verification

1. **7-Angle Display Rotation Normalization ([`vision_orientation_check.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/synthetic/vision_orientation_check.json)):**
   - Angles tested with real `ffmpeg` H.264 streams + PyAV + OpenCV + CPU `YOLOv8n` checkpoint ([`best.pt`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/vision/39f402dfe460/checkpoints/weights/best.pt), `sha256: 3f5bb5b23f82f5d9...`): `0°, 90°, -90°, 180°, -180°, 270°, -270°`.
   - All `7/7` angles passed (`all_angles_passed = true`), yielding upright `(80, 48, 3)` NumPy arrays, matching OpenCV `CAP_PROP_ORIENTATION_AUTO` (`MAE: 0.1806–0.1928`), matching upright reference (`MAE: 1.9626–2.0901` H.264 compression error), `yolo_inference_ok = true`, and deferred `video_demo` writer dimensions `[48, 80]` across `4` frames.
2. **Audio Transform Verification ([`audio_transform_check.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/synthetic/audio_transform_check.json)):**
   - Verified [`compute_log_mel_spectrogram(..., log_scale="natural")`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/audio/features.py) outputs shape `[64, 61]`, `natural_finite = true`, `db_finite = true`, `natural_differs_from_db_by_scale = true` (`horn_mean_natural_log_mel: -11.8693`, `noise_mean_natural_log_mel: 0.1541`).

---

## 2. Layer-by-Layer Real & Controlled Experimental Results (`Exp A` – `Exp E`)

### Exp A — Layer 1 Front Approach & Timing ([`exp_a_front_detection.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_a_front_detection.json), [fig09](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig09_detection_and_actuation_timing.png))
- **Train approach triggers:** `10 / 23` (`43.48%`, Wilson 95% CI `[0.2563, 0.6319]`) entered `WARNING`/`CLOSING` (`event_001, 003, 004, 006, 007, 013, 018, 021, 022, 023`). Note carefully that **`event_001` reached `WARNING` at `49.8 s`** when the `49.8 s` B4 front cache ended before completing `warning_dwell_s = 2.0 s`, so **`9 / 23`** issued a physical `close` command (`t_close_cmd_s != null`).
- **False closure controls:** `0 / 3` on `no_train_events` (`event_001` and `event_003` each had `1` isolated raw `front` frame suppressed by `confirm_frames = 2`), and `engine_only_triggered = false` on `engine_events/event_001`.
- **Arrival margin (`sync11`, `pre-db40305` unrotated caches):** `0 / 11` closed before reference arrival `T2_s`. Detection lead across `16` events with any `front` cache detection ranged from `-100.5 s` to `+3.6 s` (median `+0.05 s`, mean `-9.3812 s`). Full-closure margin (`n=9` physically closed events) ranged from `-105.5 s` (`event_006`) to `-1.4 s` (`event_013`), median `-5.1 s`, mean `-22.3 s`.

### Exp B — Layer 2 Side Movement ([`exp_b_side_detection.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_b_side_detection.json))
- **Real dataset audit:** `0 / 27` events include a physical side-mounted camera. `14 / 23` train events contain YOLO `side` class labels emitted opportunistically on `camera_1`/`camera_2`; `0 / 3` `no_train` events contain `side` labels.
- **Controlled `SideMovementTracker` verification:**
  - `moving_train_side`: `[SINGLE_FRAME, MOVING, MOVING, MOVING, MOVING, MOVING]` (`confirmed_moving = true`, `confirmed_stopped = false`).
  - `stopped_train_in_zone`: 8/8 `STOPPED` (`confirmed_moving = false`, `confirmed_stopped = true`).
  - `single_frame_false_side_glint`: `[SINGLE_FRAME, UNOBSERVED, ...]` (`both false`).
  - `negative_control_empty`: 8/8 `UNOBSERVED` (`both false`).

### Exp C — Layer 3 Audio Horn ([`exp_c_audio_horn.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_c_audio_horn.json), [fig06](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig06_closure_performance.png))
- **Cohort `audio23` (`23` events; `13` `present`, `10` `absent_observed`; `2,470` windows across `audio23` / `2,600` total across all `27` Layer-B events at threshold `0.37`):**
  - `TP = 12`, `FP = 10`, `TN = 0`, `FN = 1` (`event_001`, max score `0.247488`, `0` windows `>= 0.37`).
  - **Recall:** `0.9231` `[0.6669, 0.9863]` | **Precision:** `0.5455` `[0.3466, 0.7308]` | **Specificity:** `0.0000` `[0.0000, 0.2775]` | **F1:** `0.6857` | **Accuracy:** `0.5217` `[0.3296, 0.7076]`.
  - **Continuous ranking:** Event-max `ROC-AUC = 0.6846`, `Average Precision = 0.7739`.
- **External specificity controls (road-traffic horn confound):**
  - `no_train_events/001`: max `0.800453` (`11/48` positive windows).
  - `no_train_events/002`: max `0.826141` (`12/22` positive windows).
  - `no_train_events/003`: max `0.800207` (`16/46` positive windows).
  - `engine_events/001`: max `0.142823` (`0/14` positive windows).
- This directly confirms why Layer 3 must strictly remain a **confirmatory / dwell-extension layer**, never a standalone closure trigger.

### Exp D — Layer 4 Departure Policy Comparison ([`exp_d_back_departure.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_d_back_departure.json), [fig07](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig07_premature_opening_analysis.png))
- Across all `27` back camera streams: `30` `rear` detections (`0` `last_carriage` class detections).
- **`sync11` Premature Openings vs `T4_master_s`:**

| Policy | Premature Openings (`sync11`) | Specific Premature Opening Events (`first_opening_s` vs `T4_master_s`) |
| --- | --- | --- |
| `V1_RULE_3` | `2 / 11` | `event_006` (`107.6 < 130.3124`), `event_013` (`61.4 < 74.078`) |
| `V2_RULE_3B_3C` | `4 / 11` | `event_001` (`46.8 < 52.406`), `event_002` (`18.8 < 32.9867`), `event_006` (`107.6`), `event_013` (`49.2`) |
| `V3_GUARDED_DISAPPEARANCE` | `3 / 11` | `event_006` (`114.4`), `event_007` (`38.2 < 42.3801`), `event_013` (`48.2`) |
| **`V3_CONSERVATIVE_POSITIVE`** | **`0 / 11`** | **None (`0` premature openings; holds `CLOSED` / `FAULT_FAIL_SAFE` on unverified tail & `UNKNOWN` occupancy)** |

- Paired exact McNemar (`V2_RULE_3B_3C` vs `V3_CONSERVATIVE_POSITIVE`): `b01=4, b10=0, p = 0.125`.

### Exp E — Occupancy Interface ([`exp_e_occupancy.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_e_occupancy.json))
- **Real data:** `0 / 27` events have physical crossing occupancy hardware; `1 / 27` has annotation timestamp `T_scene_clear = 32.5 s` (`train_events/event_011`). V3 evaluates `OccupancyState.UNKNOWN` and blocks reopening rather than fabricating `CLEAR`.
- **Synthetic closed-loop:** Verified full 10-state nominal cycle (`00_nominal_4layer_full_cycle`, `121` steps, `first_warning_s = 1.2`, `first_close_cmd_s = 3.2`, `reopened = true`, `returned_idle = true`), plus `05_occupancy_sensor_failure` (`final_state = REAR_CONFIRMED/CLOSED`) and `08_contradictory_detections` (`final_state = TRAIN_PRESENT/CLOSED`).

---

## 3. Fusion, Causality, Ablation, Faults & Sensitivity (`Exp F` – `Exp M`)

1. **Multimodal Fusion Progression (`Exp F`, `G`, `H`, `I`):**
   - `Exp F` (Front + Side Proxy), `Exp G` (Front + Audio), and `Exp H` (Full Presence) all match B4 closure metrics of `10 / 23` train triggers (`9` physical `t_close_cmd_s`), `0 / 3` `no_train` FP, and `0 / 1` `engine` FP — because Layer 1 leads approach triggering while Side/Audio strengthen confirmation/dwell rather than lowering entry safety thresholds.
   - **`Exp I` Collector Causality Delta:** On B4 `train23`, causal non-backfilling (`allow_stale_detection_backfill=False`) yields **`10`** engine triggers vs **`16`** under `legacy_backfill=True` (by eliminating false persistence across sparse single-frame gaps on `event_002, 010, 011, 014, 016, 019` — wait: note causal prevented stale gap carry-over; see [`exp_i_complete_system.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_i_complete_system.json)).
   - **`Exp I` Real `sync11` Closed-Loop:** `9 / 11` closed (`event_001, 006, 007, 013` via L1 confirmation; `event_005 @ 81.8 s`, `event_009 @ 45.2 s`, `event_011 @ 40.0 s`, `event_014 @ 57.4 s`, `event_017 @ 84.0 s` via `FAULT_FAIL_SAFE` on camera EOF) with `0` premature openings; only `event_002` and `event_012` remained `IDLE/OPEN` (`1` single isolated frame on `event_002`, `0` frames on `event_012`).
   - **`Exp I` Synthetic Full 4-Layer Cycle:** `t_first_front_det_s = 1.0`, `t_warning_s = 1.2`, `t_close_cmd_s = 3.2`, `t_half_closed_s = 4.6`, `t_fully_closed_s = 6.0` (`margin_full_vs_T2_s = +0.5 s`), `first_opening_s = 14.6`, `closed_duration_s = 11.4 s`, `final_state = IDLE / OPEN`.

2. **Temporal vs Stateless (`Exp J`, [fig06](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig06_closure_performance.png)):**

| Policy | B4 Train23 Trig (Phys) | No-Train3 FP | Sync11 Premature | All Transitions Legal |
| --- | --- | --- | --- | --- |
| `stateless_union` | `23 / 23` (`23`) | **`3 / 3`** | `0` | `False` |
| `stateless_vision_rule2` | `16 / 23` (`16`) | **`2 / 3`** | `0` | `False` |
| `v1` | `9 / 23` (`8`) | `0 / 3` | `2` | `True` |
| `v2` | `10 / 23` (`9`) | `0 / 3` | `4` | `True` |
| **`v3_conservative`** | **`10 / 23` (`9`)** | **`0 / 3`** | **`0`** | **`True`** |

3. **Modality Ablation (`Exp K`, [fig05](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig05_modality_ablation.png)):**
   - **Real `sync11` closures / reopen / premature:** `full=9/0/0`, `no_audio=9/0/0`, `no_back=4/0/0` (loses back-camera EOF fail-safe!), `no_front=0/0/0`, `audio_only=0/0/0`.
   - **Synthetic 4-layer ablation:** `full`, `no_audio`, `no_side` complete full safe round trip (`close_cmd = 3.2 s`, `fully_closed = 6.0 s`, `margin +0.5 s`, `reopen = 14.6 s`, `IDLE/OPEN`); `no_back` holds `CROSSING_OCCUPIED / CLOSED`; `no_occupancy` holds `REAR_CONFIRMED / CLOSED`; `no_front` never triggers closure (`IDLE/OPEN`).

4. **18-Scenario Fault Injection (`Exp L`, [fig08](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig08_fault_injection_outcomes.png)):**
   - Across all `18` scenarios (`00_nominal` + `01..17`): **`all_transitions_legal = true`**, **`unsafe_opening_count = 0`**, **`false_train_glitch_closed = false`**, `fault_held_closed_invariant = true` for every scenario.
   - Fault-resilient safe openings occurred only when redundant primary closure/clearance sensors remained intact (`03_side_camera_failure`, `04_audio_failure`, `07_out_of_order_and_duplicate_timestamps`, `15_partial_visibility_occlusion` -> all safely completed `IDLE / OPEN`). Every front, back, occupancy, timeout, contradiction, reversal, stopped-in-zone, false-clear, and multiple-train failure held safely **`CLOSED`**!
   - **Sparse Dropout Departure Check (`exp_l`):** `V2_RULE_3C_DISAPPEARANCE` reopened prematurely at `12.4 s` (`IDLE`), whereas `V1_RULE_3` (`TRAIN_DEPARTING`), `V3_GUARDED_DISAPPEARANCE` (`CROSSING_OCCUPIED`), and `V3_CONSERVATIVE_POSITIVE` (`CROSSING_OCCUPIED`) all held safely closed (`reopened = false`).

5. **Sensitivity Sweeps (`Exp M`, [`exp_m_sensitivity.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/sensitivity/exp_m_sensitivity.json)):**
   - Note `Exp M` counts physical closures (`t_close_cmd_s != None`, baseline `9 / 23` train, `0 / 3` FP, synthetic `full_close = 6.0 s`, `first_open = 14.6 s`):
   - `confirm_frames`: `1 -> 16/23 + 2/3 FP`, **`2 -> 9/23 + 0 FP`**, `3 -> 7/23 + 0 FP`, `4 -> 3/23 + 0 FP`.
   - `temporal_tolerance_s`: **`0.15 s (< 0.20 s cadence)` triggers immediate stale fail-safe closure on `23/23` train + `3/3` no_train**; `0.25..1.00 s` stable at `9/23 + 0 FP`.
   - `detection_confidence`: `0.20..0.35 -> 9/23`, `0.45 -> 8/23`, `0.55 -> 7/23`, `0.65 -> 5/23` (`0/3` FP across all).
   - `audio_threshold`: `0.25..0.80 -> 9/23 + 0 FP` unchanged (confirms audio never drives closure).
   - `clearance_dwell_s`: linear shift of synthetic reopening from `13.6 s` (`dwell=0.5`) to `17.2 s` (`dwell=4.0`).
   - `source_latency_s`: linear shift of synthetic full closure from `6.0 s` (`0.0 s`) to `7.6 s` (`1.5 s`).

---

## 4. Complete 27-Event Outcomes Matrix (`Exp N`)

Sourced directly from [`exp_n_event_matrix.csv`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_n_event_matrix.csv):

| Event | Type | Sync11 | Front Det | Side Proxy | Audio Adopted / Max | Back `rear`/`last` | Closure Trig (`t_close`) | V2 Premature (`T4`) | V3 Premature | T2 / Margin vs T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `train_events/event_001` | TRAIN | Yes | True | 12 | `present` / `0.247` | 0 / 0 | True (`None`; WARN@49.8) | **True** | False | 6.5 / `—` |
| `train_events/event_002` | TRAIN | Yes | True | 42 | `present` / `0.983` | 0 / 0 | False | **True** | False | 3.6 / `—` |
| `train_events/event_003` | TRAIN | No | True | 52 | `absent_obs` / `0.914` | 1 / 0 | True (`2.4`) | `—` | `—` | 2.8 / `-2.4` |
| `train_events/event_004` | TRAIN | No | True | 4 | `present` / `0.999` | 4 / 0 | True (`5.2`) | `—` | `—` | 2.9 / `-5.1` |
| `train_events/event_005` | TRAIN | Yes | False | 0 | `present` / `0.971` | 0 / 0 | False (sync EOF fail-safe) | False | False | `—` / `—` |
| `train_events/event_006` | TRAIN | Yes | True | 3 | `present` / `0.816` | 0 / 0 | True (`106.0`) | **True** | False | 3.3 / `-105.5` |
| `train_events/event_007` | TRAIN | Yes | True | 10 | `absent_obs` / `0.990` | 0 / 0 | True (`18.6`) | False | False | 3.4 / `-18.0` |
| `train_events/event_008` | TRAIN | No | False | 0 | `absent_obs` / `0.811` | 2 / 0 | False | `—` | `—` | 3.2 / `—` |
| `train_events/event_009` | TRAIN | Yes | False | 0 | `absent_obs` / `0.582` | 0 / 0 | False (sync EOF fail-safe) | False | False | 5.0 / `—` |
| `train_events/event_010` | TRAIN | No | True | 0 | `absent_obs` / `0.447` | 0 / 0 | False | `—` | `—` | 3.5 / `—` |
| `train_events/event_011` | TRAIN | Yes | True | 0 | `absent_obs` / `0.450` | 0 / 0 | False (sync EOF fail-safe) | False | False | 3.6 / `—` |
| `train_events/event_012` | TRAIN | Yes | False | 0 | `present` / `0.978` | 0 / 0 | False | False | False | 3.9 / `—` |
| `train_events/event_013` | TRAIN | Yes | True | 3 | `present` / `0.914` | 0 / 0 | True (`2.6`) | **True** | False | 4.0 / `-1.4` |
| `train_events/event_014` | TRAIN | Yes | True | 3 | `absent_obs` / `0.517` | 0 / 0 | False (sync EOF fail-safe) | False | False | 3.4 / `—` |
| `train_events/event_015` | TRAIN | No | False | 0 | `present` / `0.840` | 0 / 0 | False | `—` | `—` | 5.0 / `—` |
| `train_events/event_016` | TRAIN | No | True | 9 | `absent_obs` / `0.709` | 0 / 0 | False | `—` | `—` | 5.0 / `—` |
| `train_events/event_017` | TRAIN | Yes | False | 4 | `present` / `0.985` | 0 / 0 | False (sync EOF fail-safe) | False | False | 3.6 / `—` |
| `train_events/event_018` | TRAIN | No | True | 1 | `present` / `0.998` | 0 / 0 | True (`52.6`) | `—` | `—` | 3.5 / `-51.9` |
| `train_events/event_019` | TRAIN | No | True | 0 | `absent_obs` / `0.550` | 0 / 0 | False | `—` | `—` | 3.8 / `—` |
| `train_events/event_020` | TRAIN | No | False | 0 | `present` / `0.378` | 0 / 0 | False | `—` | `—` | 3.1 / `—` |
| `train_events/event_021` | TRAIN | No | True | 231 | `present` / `0.578` | 4 / 0 | True (`11.8`) | `—` | `—` | 4.1 / `-10.5` |
| `train_events/event_022` | TRAIN | No | True | 217 | `present` / `0.602` | 5 / 0 | True (`4.8`) | `—` | `—` | 3.3 / `-4.3` |
| `train_events/event_023` | TRAIN | No | True | 376 | `absent_obs` / `0.786` | 14 / 0 | True (`2.4`) | `—` | `—` | 3.6 / `-1.6` |
| `no_train_events/001` | NO_TRAIN | No | True | 0 | `None` / `0.800` | 0 / 0 | **False** | `—` | `—` | `—` |
| `no_train_events/002` | NO_TRAIN | No | False | 0 | `None` / `0.826` | 0 / 0 | **False** | `—` | `—` | `—` |
| `no_train_events/003` | NO_TRAIN | No | True | 0 | `None` / `0.800` | 0 / 0 | **False** | `—` | `—` | `—` |
| `engine_events/001` | ENGINE | No | False | 0 | `absent_obs` / `0.143` | 0 / 0 | **False** | `—` | `—` | 0.0 / `—` |

---

## 5. Deepening Studies (`Exp O` – `Exp R`) & Host Edge Scaling ([`PUBLICATION_TABLES.md`](file:///Users/sayemuddin/Desktop/Train_automation/results/publication_tables/PUBLICATION_TABLES.md))

- **`Exp O` (`exp_o_audio_calibration_hysteresis.json`, `fig12`):** Across all `2,600` cached Layer-B audio windows (`2,470` `audio23` + `116` `no_train` + `14` `engine`), `no_train` road-vehicle horns sustain `3–9` consecutive windows `>= 0.37` (defeating simple hysteresis at `0.37`) but collapse to `1` window at `>= 0.75`. `(tau=0.75, k=2)` suppresses `3/3` `no_train` FPs (`0/1` `engine` FP) with `Spec=0.9000`, `Prec=0.8889`, `F1=0.7273`, `Rec=0.6154`.
- **`Exp P` (`exp_p_cpu_edge_benchmark.json`, `fig13`):** Apple M1 CPU (`SYNTHETIC_ONLY`, `physical_raspberry_pi_tested = false`): weight stripping shrinks `best.pt` `-74.91%` (`24,493,159 -> 6,145,232 B` FP16); `416px` E2E `YOLO.predict` reaches `21.597 ms` (`46.30 FPS`, `2.06×` vs `44.557 ms` @ `640px`), Audio `log_mel + TorchScript CNN` takes `0.878 ms/window`, `V3 FSM` takes `0.0381 ms/tick` (`26,247 Hz`), and event-triggered wakeup cuts daily frames `-96.56% to -98.64%` (`864,000 -> 11,760–29,760/d`).
- **`Exp Q` (`exp_q_weather_and_interlocking_stress.json`, `fig14`):** Across `100` synthetic attenuation × burst-drop runs: `0` unsafe openings, `100%` legal transitions, `100%` closure at `alpha >= 0.45`, and a cliff to `0%` closure at `alpha = 0.35` (`eff_conf = 0.308 < 0.35`).
- **`Exp R` (`exp_r_crossval_and_failsafe.json`, `fig15`; independent check [`exp_r_independent_validation.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/exp_r_independent_validation.json)):**
  - **23-Fold Nested LOEO Acoustic CV:** Out-of-fold `Spec = 0.6000` (bootstrap `[0.3000, 0.9000]` / Wilson `[0.3127, 0.8318]` vs `0.0000` frozen baseline) and `Acc = 0.6087` come with a drop in `F1 = 0.6400` (`[0.4167, 0.8148]` vs `0.6857` baseline) and `Rec = 0.6154` (Wilson `[0.3552, 0.8229]` vs `0.9231` baseline); `OOF Brier = 0.2366` (paired Δ vs raw CI `[-0.0839, +0.0104]` crosses `0`), `ECE = 0.0999` (`0` samples in `[0.0, 0.4)` and `9/23` folds at `T=4.0` ceiling; uncapped `T <= 15` gives `max T = 4.2`, `Brier = 0.2379`, `ECE = 0.1007`), and `(tau=0.75, k=2)` selected in `20/23` original folds (`18/23` strict train-only).
  - **Opt-In Optical-Degradation Audio Wakeup (`RuleIdV3.RULE_L3_OPTICAL_DEGRADED_AUDIO_WAKEUP`, `SYNTHETIC_ONLY`, `enable_optical_degradation_audio_wakeup=False` by default):** Closes the `alpha = 0.35` synthetic fog cliff (`0% -> 100%` closure at `t = 4.0 s`, `0` unsafe opens) while preserving `0/2` false closures on clear-sky sustained ambient horns and single-impulse degraded-optics controls.
- **Standalone Multi-Thread Edge Benchmark ([`host_edge_scaling_benchmark.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/host_edge_scaling_benchmark.json)):** `1/2/4`-thread TorchScript `416px` (`28.025 -> 20.921 -> 16.839 ms`, `59.39 FPS` @ 4T) and `320px` (`17.150 -> 13.537 -> 11.523 ms`, `86.78 FPS` @ 4T), `4T Audio TS = 0.384 ms`, OpenCV `1080p->rotate90->416px` preprocess `16.980 ms`, `RSS = 452.45 MB`, explicitly marked `physical_raspberry_pi_tested = false`.
