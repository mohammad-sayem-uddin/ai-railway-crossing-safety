# Error & Failure Analysis — Root Causes, Edge Cases & Fault Behavior

**Primary Evidence Files:** [`exp_a_front_detection.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_a_front_detection.json), [`exp_c_audio_horn.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_c_audio_horn.json), [`exp_d_back_departure.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_d_back_departure.json), [`exp_l_fault_injection.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/failure_injection/exp_l_fault_injection.json), [`exp_m_sensitivity.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/sensitivity/exp_m_sensitivity.json)

---

## 1. Root-Cause Breakdown of Real-Data Misses (`13 / 23` Non-Triggered Approach Events)

Across the `23` B4 `train_events`, `13` did not reach V3 `WARNING`/`CLOSING` (`14` did not reach `t_close_cmd_s`):

1. **Zero Cached Vision Detections (`7` events: `005, 008, 009, 012, 015, 017, 020`):**
   - `raw_front_det_counts` contains `{front: 0, side: 0, rear: 0, other: 0}` across the entire `camera_1` clip in frozen `pre-db40305` JSONL caches.
   - Root cause documented in Mission 44 ([`DISPLAY_ROTATION_DEFECT_REPRODUCTION.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/professor_evidence/mission44/DISPLAY_ROTATION_DEFECT_REPRODUCTION.json)): many raw `.mov` files contain `-90°` display-rotation matrices, causing unrotated `pre-db40305` inference to run on sideways frames where the `YOLOv8n` model fails to fire. Without `AUTH-MEDIA-ACCESS.json`, corrected upright inference cannot run on raw `.mov` files.
2. **Sparse Single-Frame / Gapped Front Detections Suppressed by Causal Filter (`5` events: `002, 010, 014, 016, 019`):**
   - `event_002` (`1` `front` frame), `event_010` (`1` `front` frame), `event_014` (`3` separated `front` frames), `event_016` (`5` separated `front` frames), `event_019` (`1` `rear` frame): detections separated by gaps larger than consecutive-frame confirmation (`confirm_frames = 2`, `temporal_tolerance_s = 0.5 s`) never establish consecutive confirmation once stale backfill is disabled. Under legacy `backfill=True` (`Exp I`), `16/23` appeared to trigger precisely because single frames persisted across gaps.
3. **Late Single-Class Misclassification Before Approach Confirmation (`event_011`):**
   - Contains `3` `rear` detections late at `~28.4 s` (`det_lead_vs_T2_s = -24.8 s`), non-consecutive on `pre-db40305` caches.
4. **Late Trigger Ending in `WARNING` (`event_001`):**
   - First front detection at `27.0 s` (`T2 = 6.5 s`), confirmed `WARNING` at `49.8 s`, when the `49.8 s` B4 front cache terminated before completing `warning_dwell_s = 2.0 s` (`t_close_cmd_s = null` in `Exp A`; in synced `sync11` `Exp I`, where total duration reaches `53.4 s`, `event_001` closes at `51.8 s`).

---

## 2. Camera Geometry & Geometry-Dependent Closure Timing

- Even among the `10` triggered `train_events`, `4` (`006, 007, 021, 022`) had `0` YOLO `front` class labels on `camera_1`, firing via `side` (`007: 5`, `021: 6`, `022: 14`) or `rear` (`006: 8`) classes once the train was already adjacent to or traversing the crossing.
- Because the prototype cameras sat near the crossing (`T2` median `~3.6 s`), even immediate detection at `t = 0.0 s` (`event_003, event_023`) cannot complete `2.0 s` warning + `3.0 s` gate closing before `T2 = 2.8–3.6 s`. This directly motivates the upstream camera placement design in `REAL_WORLD_INSTALLATION_CONCEPT.md`.

---

## 3. Acoustic False Positives & Road-Traffic Confounds (`Exp C`)

- At frozen threshold `0.37` (`audio23`), **`10 / 10` `absent_observed` train events** (`003, 007, 008, 009, 010, 011, 014, 016, 019, 023`) triggered `predicted_positive_037 = True` (`max_score` `0.447–0.990`, `2–18` positive windows each), giving `0.0%` specificity.
- All three **`no_train_events`** (`001: 0.8005` on `11/48` windows, `002: 0.8261` on `12/22` windows, `003: 0.8002` on `16/46` windows) crossed `0.80`, confirming severe confusion between road-traffic vehicle horns near the level crossing and locomotive horns (`engine_events/001` scored low at `0.1428`).
- `1` false negative occurred on `train_events/event_001` (`horn_status = present`, `max_score = 0.247488`, `0/98` windows `>= 0.37`).

---

## 4. Departure & Occupancy Gaps (`Exp D`, `Exp E`)

- **Unverified Tail Recognition:** Across `27` back camera streams, `YOLOv8n` produced **`0` `last_carriage` detections** and only `30` `rear` detections (`event_003, 004, 008, 021, 022, 023` — zero on any `sync11` event except `1` `front` frame on `007`). Consequently, `V1`, `V2`, and `V3_GUARDED_DISAPPEARANCE` prematurely reopened on `2/11`, `4/11`, and `3/11` `sync11` events (`event_001, 002, 006, 007, 013`) where flickering detections vanished mid-train.
- **No Physical Occupancy Hardware:** Only `1 / 27` events (`event_011 @ 32.5 s`) carries a documentary `T_scene_clear` marker. Therefore, `V3_CONSERVATIVE_POSITIVE` intentionally stays `CLOSED` / `FAULT_FAIL_SAFE` on real `sync11` runs until genuine tail detection and physical occupancy sensors are installed.

---

## 5. Closed-Loop Fault-Injection Analysis (`Exp L` — All 18 Scenarios)

Measured from [`exp_l_fault_injection.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/failure_injection/exp_l_fault_injection.json) (`all_transitions_legal = true`, `unsafe_opening_count = 0`, `false_train_glitch_closed = false`):

| Scenario ID | Legal (`Steps`) | Warning (`s`) | Close (`s`) | Fault (`s`) | Final State (`Crossing` / `Gate`) | Reopen | Fault Behavior |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `00_nominal_4layer_full_cycle` | True (`121`) | `1.2` | `3.2` | `None` | `IDLE / OPEN` | **True** | Nominal L1->L2->L3->L4+OCC->`IDLE` |
| `01_front_camera_failure` | True (`121`) | `None` | `0.2` | `0.0` | `FAULT_FAIL_SAFE / CLOSED` | False | Immediate front fail-safe closure |
| `02_back_camera_failure` | True (`121`) | `1.2` | `3.2` | `9.0` | `CROSSING_OCCUPIED / CLOSED` | False | Blocks departure; holds closed |
| `03_side_camera_failure` | True (`121`) | `1.2` | `3.2` | `5.0` | `IDLE / OPEN` | **True** | Safe completion via L1+L4+OCC |
| `04_audio_failure` | True (`121`) | `1.2` | `3.2` | `0.0` | `IDLE / OPEN` | **True** | Audio non-gating; safe cycle via vision+OCC |
| `05_occupancy_sensor_failure` | True (`121`) | `1.2` | `3.2` | `10.0` | `REAR_CONFIRMED / CLOSED` | False | Reaches rear confirm; blocks open |
| `06_stale_observations` | True (`121`) | `1.2` | `3.2` | `13.2` | `CROSSING_OCCUPIED / CLOSED` | False | Freshness timeout holds closed |
| `07_out_of_order_and_duplicate_timestamps` | True (`121`) | `1.2` | `3.2` | `None` | `IDLE / OPEN` | **True** | Causal collector rejects OOO/dups safely |
| `08_contradictory_detections` | True (`121`) | `1.2` | `3.2` | `4.0` | `TRAIN_PRESENT / CLOSED` | False | Rejects conflicting CLEAR; holds closed |
| `09_model_inference_timeout` | True (`121`) | `1.2` | `3.2` | `11.0` | `CROSSING_OCCUPIED / CLOSED` | False | Timeout blocks premature clear |
| `10_missing_frames_sparse_dropout` | True (`121`) | `1.2` | `3.2` | `10.2` | `TRAIN_DEPARTING / CLOSED` | False | Disappearance gap never reopens |
| `11_video_stream_termination` | True (`121`) | `1.2` | `3.2` | `10.0` | `CROSSING_OCCUPIED / CLOSED` | False | EOF halts clearance & locks closed |
| `12_multiple_trains` | True (`121`) | `1.2` | `3.2` | `None` | `CROSSING_OCCUPIED / CLOSED` | False | Second approach re-latches occupied |
| `13_train_reversal` | True (`121`) | `1.2` | `3.2` | `11.8` | `CROSSING_OCCUPIED / CLOSED` | False | Reversal blocks departure clearance |
| `14_train_stopped_in_zone` | True (`121`) | `1.2` | `3.2` | `6.0` | `CROSSING_OCCUPIED / CLOSED` | False | L2 `STOPPED` locks zone occupied |
| `15_partial_visibility_occlusion` | True (`121`) | `1.2` | `3.2` | `None` | `IDLE / OPEN` | **True** | Safe completion once clear verified |
| `16_false_train_detection_glitch` | True (`60`) | `None` | `None` | `None` | `IDLE / OPEN` | False | Single-frame glint ignored (`0` closures) |
| `17_false_clear_detection` | True (`121`) | `1.2` | `3.2` | `8.0` | `TRAIN_PRESENT / CLOSED` | False | Contradiction (`OCC=CLEAR` + train) holds closed |

Additionally, in `Exp L` `sparse_dropout_departure_comparison`, `V2_RULE_3C_DISAPPEARANCE` reopened unsafely at `12.4 s` during dropout, whereas `V3_CONSERVATIVE_POSITIVE` safely held `CROSSING_OCCUPIED`.

---

## 6. Parameter Sensitivity Cliff (`Exp M`)

- **`temporal_tolerance_s = 0.15 s` (`< 0.20 s` frame cadence):** Because every inter-frame delta (`0.20 s`) exceeds `0.15 s`, V3 flags source staleness on the second step and triggers immediate fail-safe closure on `23 / 23` train events and `3 / 3` `no_train` events (`mean close = 3.1043 s`). Thus `temporal_tolerance_s` **must exceed the discrete stream cadence** (`>= 0.25 s`, baseline `0.50 s`).
- **`confirm_frames = 1`:** Degrades B4 false-positive immunity from `0 / 3` to `2 / 3` (`no_train_001, 003`). Baseline `confirm_frames = 2` is the minimum safe temporal confirmation setting.
