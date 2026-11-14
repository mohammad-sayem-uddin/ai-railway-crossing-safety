# Publication-Ready Summary Tables (`Exp A` – `Exp Q` & Dataset Leakage Audit)

Generated deterministically by `scripts/generate_master_publication_tables.py` from verified repository artifacts.

## Table 1 — Vision V1 & Audio V3 Dataset Split Leakage Audit vs Clean Candidates

| dataset | split_variant | train_n | val_n | test_n | cross_session_or_stem_leak | test_overlap_with_train | aug_or_fold_artifact |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Vision V1 (baler.v1i) | Original Roboflow folders | 2763 | 263 | 131 | 27/29 sessions (gap<=600s) | 127/127 timestamped test imgs | 0 rf_train in test; ungrouped bursts |
| Vision V1 (baler.v1i) | Active split 705d388743ea (leaked) | 2218 | 467 | 472 | 27/29 sessions (gap<=600s) | 447/447 timestamped test imgs | 411/472 test from rf_train (87.1%) |
| Vision V1 (baler.v1i) | Candidate vision_v1_session_grouped | 1776 | 336 | 241 | 0/29 sessions (gap<=600s) | 0/241 timestamped test imgs | 804 eval aug duplicates excluded |
| Audio V3 (TrainHorn + ESC-50) | Original audio/v3/dataset_split.json | 120 | 26 | 26 | 5/57 pos stems cross splits | 28/86 pos clips (32.56%) | 0 cross-split ESC-50 folds |
| Audio V3 (TrainHorn + ESC-50) | Candidate audio_v3_stem_grouped | 120 | 26 | 26 | 0/57 pos stems cross splits | 0/86 pos clips (0.00%) | 0 cross-split ESC-50 folds; 60/13/13 balanced |


## Table 2 — Decision Policy & Modality Ablation Summary (`Exp D`, `Exp J`, `Exp K`)

| experiment | policy_or_ablation | b4_train23_triggers | no_train3_fp | sync11_closures | sync11_premature_openings | all_transitions_legal | synthetic_4layer_outcome |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Exp J | stateless_union | 23/23 | 3/3 | 11/11 | 0/11 | False | N/A (no FSM statefulness) |
| Exp J | stateless_vision_rule2 | 16/23 | 2/3 | 9/11 | 0/11 | False | N/A (no FSM statefulness) |
| Exp D / J | V1 (RULE_3) | 9/23 (8 phys) | 0/3 | 5/11 | 2/11 | True | Legacy baseline |
| Exp D / J | V2 (RULE_3B_3C) | 10/23 (9 phys) | 0/3 | 5/11 | 4/11 | True | Reopens prematurely under sparse dropout (12.4s) |
| Exp D | V3_GUARDED_DISAPPEARANCE | 10/23 (9 phys) | 0/3 | 9/11 | 3/11 | True | Aborts under sparse dropout |
| Exp D / J / K | V3_CONSERVATIVE_POSITIVE (Full 4-Layer) | 10/23 (9 phys) | 0/3 | 9/11 | 0/11 | True | IDLE/OPEN (open@14.6s) |
| Exp K | Ablation: No Audio | 10/23 | 0/3 | 9/11 | 0/11 | True | IDLE/OPEN (open@14.6s) |
| Exp K | Ablation: No Back Camera | N/A | 0/3 | 4/11 | 0/11 | True | CROSSING_OCCUPIED/CLOSED (fails closed) |
| Exp K | Ablation: No Side Camera | 10/23 | 0/3 | N/A (no side cam) | 0/11 | True | IDLE/OPEN (open@14.6s) |
| Exp K | Ablation: No Occupancy Sensor | N/A | N/A | N/A | 0/11 | True | REAR_CONFIRMED/CLOSED (blocks reopen) |
| Exp K | Ablation: No Front / Audio Only | 0/23 | 0/3 | 0/11 | 0/11 | True | IDLE/OPEN (0 triggers) |


## Table 3 — `Exp O`: Field Audio Threshold & Consecutive-Window Hysteresis Pareto Frontier

| threshold | k_consecutive | tp | fp | tn | fn | recall | specificity | precision | f1 | accuracy | no_train_fp | engine_fp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.37 | 1 | 12 | 10 | 0 | 1 | 0.9231 | 0.0 | 0.5455 | 0.6857 | 0.5217 | 3/3 | 0/1 |
| 0.37 | 2 | 10 | 7 | 3 | 3 | 0.7692 | 0.3 | 0.5882 | 0.6667 | 0.5652 | 3/3 | 0/1 |
| 0.5 | 2 | 9 | 5 | 5 | 4 | 0.6923 | 0.5 | 0.6429 | 0.6667 | 0.6087 | 3/3 | 0/1 |
| 0.65 | 2 | 9 | 3 | 7 | 4 | 0.6923 | 0.7 | 0.75 | 0.72 | 0.6957 | 1/3 | 0/1 |
| 0.75 | 1 | 9 | 4 | 6 | 4 | 0.6923 | 0.6 | 0.6923 | 0.6923 | 0.6522 | 3/3 | 0/1 |
| 0.75 | 2 | 8 | 1 | 9 | 5 | 0.6154 | 0.9 | 0.8889 | 0.7273 | 0.7391 | 0/3 | 0/1 |
| 0.85 | 2 | 6 | 1 | 9 | 7 | 0.4615 | 0.9 | 0.8571 | 0.6 | 0.6522 | 0/3 | 0/1 |


## Table 4 — `Exp P`: Measured CPU Stage Profiling (Apple M1) & Analytical SBC Duty-Cycle Projections

| stage_or_artifact | input_or_mode | measured_mean_ms_or_size | p95_ms_or_diff | fps_or_reduction | evidence_status |
| --- | --- | --- | --- | --- | --- |
| YOLOv8n checkpoint file | Raw unstripped vs stripped FP16 | 24,493,159 B -> 6,145,232 B | FP32: 12,188,432 B | -74.91% disk | Measured on repo artifact |
| YOLOv8n PyTorch eager | 1x3x640x640 / 416x416 / 320x320 | 39.938 / 19.141 / 13.217 ms | p95: 42.78 / 20.243 / 13.625 ms | 25.04 / 52.24 / 75.66 FPS | Measured Apple M1 CPU (SYNTHETIC_ONLY) |
| YOLOv8n TorchScript | 640x640 / 416x416 / 320x320 | 38.603 / 18.253 / 13.155 ms | max_abs_diff=0.0 | 25.9 / 54.79 / 76.02 FPS | Measured Apple M1 CPU (SYNTHETIC_ONLY) |
| Ultralytics YOLO.predict E2E | 640px vs 416px numpy RGB | 54.658 vs 23.605 ms | p95: 72.785 vs 28.017 ms | 18.3 vs 42.36 FPS (2.32x speedup) | Measured Apple M1 CPU (SYNTHETIC_ONLY) |
| Audio log-Mel + CNN (TorchScript) | 1s 16kHz window [64x61] | 0.41 + 0.471 ms (0.881 ms total) | diff=0.0; INT8 Linear=0.563 ms (diff=0.0601) | CNN TS=2123.33 win/s | Measured Apple M1 CPU (SYNTHETIC_ONLY) |
| V3 FSM + Collector + Gate | 121-tick full cycle | 4.737 ms total (0.0391 ms/tick) | p95=4.919 ms | 25,575 Hz tick rate | Measured Apple M1 CPU (SYNTHETIC_ONLY) |
| Raspberry Pi 4B Duty Cycle (416px) | 24/7 5-FPS vs Event-Triggered (10/20/40 trains/d) | 864,000 vs 11,760 / 17,760 / 29,760 frames/d | Continuous: 1.308 cores -> Gated: 0.0274 / 0.0364 / 0.0544 cores | -96.56% to -98.64% frames (-95.84% to -97.91% compute) | ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE (5.5x M1) |
| Raspberry Pi 4B Duty Cycle (640px) | 24/7 5-FPS vs Event-Triggered (10/20/40 trains/d) | 864,000 vs 11,760 / 17,760 / 29,760 frames/d | Continuous: 3.0159 cores -> Gated: 0.0506 / 0.0715 / 0.1132 cores | -96.25% to -98.32% compute | ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE (5.5x M1) |


## Table 5 — `Exp Q`: Synthetic Optical Attenuation x Burst-Dropout Stress Grid (`100` runs)

| alpha_conf | effective_front_conf | burst_drop_prob_range | runs_count | closure_rate | reopen_rate | failsafe_rate | miss_open_rate | unsafe_opening_count | all_transitions_legal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.0 | 0.88 | 0.00 to 0.50 (4 levels x 5 seeds) | 20 | 1.0 | 1.0 | 0.0 | 0.0 | 0 | True |
| 0.8 | 0.704 | 0.00 to 0.50 (4 levels x 5 seeds) | 20 | 1.0 | 1.0 | 0.0 | 0.0 | 0 | True |
| 0.6 | 0.528 | 0.00 to 0.50 (4 levels x 5 seeds) | 20 | 1.0 | 0.95 | 0.0 | 0.0 | 0 | True |
| 0.45 | 0.396 | 0.00 to 0.50 (4 levels x 5 seeds) | 20 | 1.0 | 1.0 | 0.0 | 0.0 | 0 | True |
| 0.35 | 0.308 | 0.00 to 0.50 (4 levels x 5 seeds) | 20 | 0.0 | 0.0 | 0.0 | 1.0 | 0 | True |

