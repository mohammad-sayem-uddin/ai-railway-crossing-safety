# Experimental Protocol — Controlled V3, Exploratory `Exp A–Q` & Leakage Audits

**Reference Protocols & Evidence Bounds:**
- **Official Phase 12 Profile:** `M4` primary (`T4_master` end boundary, `11` synced events) + `v9` sensitivity (`phase12_protocol_decision.json`, `sha256: 6b5edb4852fc0d16...`).
- **Official Status:** Strictly blocked (`ready: false`, `blocker_count: 7`, `STAGE21_RECORDS_MISSING`, `AUTH-MEDIA-ACCESS.json` absent).
- **Exploratory Boundary:** All real-video evaluations (`Exp A–D, F–J, N, O`) operate solely on frozen `pre-db40305` vision/audio inference caches evaluated against researcher-adopted AI-assisted schema-`7.0.0` proposals (`RESEARCHER_ANNOTATION_ADOPTION.json`), with explicit synthetic isolation on `Exp E, K (synthetic), L, M (synthetic), P, Q`.

---

## 1. Cohort Structure & Access Classification

| Cohort | Size / Composition | Classification | Purpose & Constraints |
|---|---|---|---|
| **Layer B `train23`** | `23` train crossing events (`day/overcast`, `crossing_A`) | `CACHE_ONLY_EXPLORATORY` | Approach closure detection (`Exp A, F–J`), `audio23` horn metrics (`13` `present`, `10` `absent_observed`, `2,470` windows across `audio23` / `2,600` across all `27` events in `Exp C, O`). |
| **Layer B `sync11`** | `11` dual-camera synced events (`camera_1 + camera_2` offsets) | `CACHE_ONLY_EXPLORATORY` | End-to-end closure margin vs `T2` and premature opening vs `T4_master_s` (`Exp D, I, J, K`). |
| **Layer B `no_train3` & `engine1`** | `3` train-free + `1` stationary engine event (`night/clear`) | `CACHE_ONLY_EXPLORATORY` | False-closure and road-horn specificity controls (`130` audio windows across `no_train_001..003` + `engine_001`). |
| **Vision V1 (`baler.v1i`) & Audio V3** | `3,157` image manifests (`1,315` groups); `172` audio split records | `METADATA_ONLY` | Session/stem leakage measurement & non-destructive split construction (`leakage_audit.py`). |
| **Closed-Loop Stress (`Exp L, P, Q`)** | `18` fault scenarios, `YOLOv8n`/`CNN` CPU tensors, `100` attenuation×drop runs | `SYNTHETIC_ONLY` | Transition legality (`0` unsafe opens), CPU throughput/RSS (`Apple M1`), duty-cycle projection, and stress margins. |

---

## 2. Protocol Specifications Across `Exp A` – `Exp Q`

### 2.1 Existing Exploratory Multimodal Suite (`Exp A–N`, [`EXPERIMENTAL_METHODOLOGY.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/EXPERIMENTAL_METHODOLOGY.md))
- **Master Cadence:** `dt = 0.20 s` (`5 Hz`), causal [`MultimodalEvidenceCollector`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/collector.py) (`allow_stale_detection_backfill=False` for V3; `True` reserved for legacy comparison in `Exp I`), `temporal_tolerance_s = 0.50 s`, `heartbeat_timeout_s = 2.0 s`.
- **Gate Kinematics:** `warning_dwell_s = 2.0 s`, `closing_duration_s = 3.0 s` (`90.0° -> 0.0°`, passage blocked `<= 45.0°`), `opening_duration_s = 2.0 s` (`0.0° -> 90.0°`), `clearance_dwell_s = 1.5 s`, `audio_hold_s = 1.5 s`. Note `EventSimulationRunner` executes Convention A stepping (`-0.20 s` vs post-tick Convention B, documented via `convention_note`).
- **Statistics:** Two-sided **95% Wilson score confidence intervals** for small-sample proportions and **two-sided exact binomial McNemar tests** for paired policy comparisons (`V2` vs `V3`, `stateless_union` vs `V3`).

### 2.2 New Deepening Studies Added in This Mission (`Exp O, P, Q` — [`optimization_and_stress.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/experiments/optimization_and_stress.py))
1. **`Exp O` (Field Audio Threshold × Consecutive-Window Hysteresis & Calibration):**
   - Evaluates exact threshold grid `tau in [0.37, 0.50, 0.65, 0.75, 0.80, 0.85, 0.90, 0.95]` × persistence `k in {1, 2, 3, 4}` over all `2,600` Layer-B windows (`2,470` in `audio23` `13` `present` / `10` `absent_observed`, plus `116` in `no_train3` and `14` in `engine1`) without modifying raw media or frozen thresholds.
   - Evaluates post-hoc temperature scaling `T in {0.5, 1.0, 1.5, 2.0, 3.0}` via 5-bin ECE and Brier score across event-max probabilities (`strictly labeled exploratory`: real data lacks window-level onset timestamps).
2. **`Exp P` (CPU Edge Profiling, Weight Stripping, Quantization & Duty Cycle):**
   - Inspects checkpoint byte decomposition (`best.pt` with/without optimizer & EMA); benchmarks synthetic-input `YOLOv8n` FP32 forward & TorchScript at `640`, `416`, `320` (`20` iters after warmup), end-to-end `YOLO.predict` at `640` vs `416` (`15` iters), `log_mel_1s_numpy` (`60` iters), `CompactTrainHornCNN` eager/TorchScript/dynamic INT8 `Linear` (`80` iters, `qnnpack` ARM engine), `V3 FSM` `121`-tick cycle (`30` iters), and peak process RSS.
   - Evaluates analytical event-triggered duty cycle (`60 s` active dual-camera `5 FPS` per train + `0.033 Hz` [every `30 s`] health watchdog + continuous `2 Hz` audio `0.881 ms`) vs continuous `24/7` `5-FPS` dual-camera execution (`864,000 frames/day`) for `10/20/40` trains/day, applying explicit **`ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE`** slowdown factors (`5.5x` RPi 4B Cortex-A72, `2.4x` RPi 5 Cortex-A76).
3. **`Exp Q` (Weather Optical Attenuation × Burst Dropout & Interlocking Stress):**
   - Sweeps optical confidence multiplier `alpha_conf in {1.0, 0.8, 0.6, 0.45, 0.35}` (`0.88 * alpha_conf`) × frame burst-drop probability `p_drop in {0.0, 0.15, 0.30, 0.50}` × `5` deterministic seeds (`100` runs total) alongside three closed-loop hazard scenarios: `healthy_subthreshold_optical_attenuation` (`0.35` alpha, no dropout), `stalled_obstacle_during_departure` (obstacle occupying `[4.0..20.8 s]`), and `multi_train_reopen_interrupt` (second approach during gate opening at `14.8 s`).
