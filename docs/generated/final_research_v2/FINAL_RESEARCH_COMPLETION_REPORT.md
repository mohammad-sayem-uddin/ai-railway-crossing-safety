# Final Research Completion Report — Four-Layer Multimodal Railway Crossing Protection Prototype

**Branch:** `exp/four-layer-completion` (from `d1032756de80963130e1cbd3d2334cb32139b996`)  
**Results Package:** `results/exploratory_v2/` (`23` deterministic SHA-256-verified artifacts, `BIT_IDENTICAL_2X_OK`)  
**Figures Package:** `docs/generated/final_research_v2/figures/` (`fig01`–`fig10`)  
**Evaluation Status:** **EXPLORATORY PROTOTYPE VERIFICATION** (cached `pre-db40305` unrotated vision inference + `ALL_AUDIO_WINDOW_SCORES.csv` against researcher-adopted AI-assisted reference annotations + controlled synthetic multi-orientation & fault-injection suites). **Not certified for live railway operation.**

---

## 1. Executive Summary

This report documents the completion of the four-layer causal multimodal railway crossing protection prototype (Layers 1–4 + dedicated crossing occupancy verification) built on top of the verified baseline `d1032756de80963130e1cbd3d2334cb32139b996`. All frozen baseline configurations, prior experimental packages (`results/exploratory_execution/`, `docs/generated/final_research/`), Mission 43/44 provenance records, and raw-media governance boundaries (`src/railway_detection/safety/media_guard.py`) were preserved without modification or bypass.

### Core Technical Corrections Delivered

1. **Video Orientation Normalization & Demo Writer Deferral** ([`video.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/vision/video.py), [`video_demo.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/demo/video_demo.py)):
   - Normalized orthogonal display-matrix rotations (`0`, `±90°`, `±180°`, `±270°`, `±360°`) fail-closed across both OpenCV (`CAP_PROP_ORIENTATION_AUTO`) and PyAV (`np.rot90(image, k=(rotation // 90) % 4)`).
   - Deferred `cv2.VideoWriter` initialization in `process_video()` to the post-rotation frame dimensions `(height, width)` of the first decoded frame.
   - Verified end-to-end across all 7 orthogonal container rotations with `ffmpeg` + PyAV + OpenCV + real CPU `YOLOv8n` checkpoint inference (`results/exploratory_v2/synthetic/vision_orientation_check.json`: `all_angles_passed = true`, MAE PyAV vs OpenCV `0.1806–0.1928` uint8 pixel units).

2. **Causal Multimodal Evidence Collector** ([`collector.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/collector.py), [`evidence.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/evidence.py)):
   - Changed the causal default to `allow_stale_detection_backfill=False` (each ingested observation is emitted once on the snapshot that consumes it), while explicitly preserving `allow_stale_detection_backfill=True` inside legacy baseline scripts ([`exploratory_common.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/exploratory_common.py#L531) and [`diagnostic_trace.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/experiments/diagnostic_trace.py#L192-L196)) so historical V1/V2 baselines remain regression-compatible.
   - Added `OccupancyEvidence` channel, `EvidenceStatus` taxonomy, `.reset(event_id=...)` cross-event cleanup, and a guard against `SourceTracker.get_age()` returning `float("inf")` at `t = 0.0` before a detection arrives.

3. **V3 Four-Layer + Occupancy Architecture** ([`occupancy.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/occupancy.py), [`rules_v3_four_layer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/rules_v3_four_layer.py), [`decision_engine_v3_four_layer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/decision_engine_v3_four_layer.py)):
   - **Layer 1 (Front Camera):** Independent early approach trigger (`confirm_frames=2` at `conf >= 0.35`, no waiting for back/side/audio).
   - **Layer 2 (Side Crossing View):** `SideMovementTracker` distinguishing `MOVING`, `STOPPED`, `SINGLE_FRAME`, and `UNOBSERVED` states to suppress transient glints and hold stopped trains.
   - **Layer 3 (Trackside Audio Horn):** Operating at threshold `0.3700` on natural log-Mel (`log(mel_spec + eps)`), strictly supporting presence and extending `clearance_dwell_s` — never gating closure or proving train absence.
   - **Layer 4 (Back Exit Camera):** Evaluates `CONSERVATIVE_POSITIVE` (requires positive `rear` and optional `last_carriage`) alongside an explicitly guarded disappearance comparison mode (`GUARDED_DISAPPEARANCE`).
   - **Final Clearance (`OccupancyVerifier`):** Resolves explicit `OCCUPIED`, `CLEAR`, `UNKNOWN`, `MISSING`, or `CONTRADICTORY` state. Reopening requires the full 4-way AND-gate: positive L4 departure + `OccupancyState.CLEAR` + healthy required clearance sources + zero contradictions + completed clearance dwell.

---

## 2. Summary of Experimental Outcomes (`Exp A` – `Exp N`)

| Experiment / Scope | Key Finding (Direct Output Trace) | Source File |
| --- | --- | --- |
| **Synthetic Orientation & Audio** | `7/7` rotation angles (`0, ±90, ±180, ±270°`) upright + `YOLOv8n` OK; natural log-Mel verified (`[64, 61]`, distinct from dB scale) | [vision_orientation_check.json](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/synthetic/vision_orientation_check.json), [audio_transform_check.json](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/synthetic/audio_transform_check.json) |
| **Exp A (Front Approach, B4/all27)** | `10/23` (`43.48%`, Wilson CI `[0.2563, 0.6319]`) train events triggered V3 `WARNING`/`CLOSING`; `9/23` reached `GATE_CLOSING`/`CLOSED`; `0/3` `no_train` FP; `engine_only` `False`; `0/11` `sync11` closed before `T2` on `pre-db40305` unrotated caches (`n=9` full-closure margin vs `T2`: min `-105.5 s`, median `-5.1 s`, max `-1.4 s`) | [exp_a_front_detection.json](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_a_front_detection.json) |
| **Exp B (Side View + Movement)** | `0/27` real events have a dedicated physical side camera (`14/23` show YOLO `side` class proxy labels on `camera_1`/`camera_2`, `0/3` `no_train`); synthetic `SideMovementTracker` separates moving, stopped, single-frame glint, and negative controls | [exp_b_side_detection.json](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_b_side_detection.json) |
| **Exp C (Audio Horn, `audio23`)** | At frozen `0.37` threshold (`2,600` windows): `TP=12, FP=10, TN=0, FN=1`; Recall `0.9231`, Precision `0.5455`, Specificity `0.0000`, F1 `0.6857`, Accuracy `0.5217`, ROC-AUC `0.6846`, AP `0.7739`; separate `no_train` road horns score `0.800–0.826`; `engine1` max `0.1428` | [exp_c_audio_horn.json](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_c_audio_horn.json) |
| **Exp D (Departure Policy, `sync11`)** | Premature openings before `T4_master`: `V1_RULE_3=2/11`, `V2_RULE_3B_3C=4/11`, `V3_GUARDED_DISAPPEARANCE=3/11`, **`V3_CONSERVATIVE_POSITIVE=0/11`** (McNemar exact `p=0.125`); `30` `rear` and `0` `last_carriage` detections across all 27 back streams | [exp_d_back_departure.json](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_d_back_departure.json) |
| **Exp E (Crossing Occupancy)** | `0/27` events have physical occupancy sensors; `1/27` has `T_scene_clear` (`event_011 @ 32.5 s`); V3 resolves `UNKNOWN` and holds closed rather than fabricating `CLEAR`; all 5 synthetic unit states verified | [exp_e_occupancy.json](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_e_occupancy.json) |
| **Exp F–I (Fusion & Collector Delta)** | Removing stale backfill reduces B4 train closures from `16/23` (legacy) to `10/23` (causal V3 engine trigger) by preventing single-frame detections from carrying across gaps; on `sync11`, causal V3 triggers closure on `9/11` (`4` via L1 approach confirmation + `5` via `FAULT_FAIL_SAFE` on camera EOF) with `0` premature openings | [exp_i_complete_system.json](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_i_complete_system.json) |
| **Exp J (Temporal vs Stateless)** | B4 train closures / `no_train` FP: `stateless_union` `23/23` (`3/3` FP); `stateless_vision_rule2` `16/23` (`2/3` FP); `V1` `9/23` (`0/3` FP); `V2` `10/23` (`0/3` FP); `V3` `10/23` (`0/3` FP, McNemar vs `stateless_union` `p=0.25`) | [exp_j_temporal_vs_stateless.json](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_j_temporal_vs_stateless.json) |
| **Exp K (Modality Ablations)** | Real `sync11` closures: `full=9`, `no_audio=9`, `no_back=4`, `no_front=0`, `audio_only=0`; synthetic 4-layer nominal opens safely at `14.6 s`, while removing back or occupancy safely holds closed (`CLOSED`) | [exp_k_ablation.json](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_k_ablation.json) |
| **Exp L (18 Fault Scenarios)** | `18/18` scenarios execute with `100%` legal state transitions (`all_transitions_legal=true`), **`0` unsafe openings** (`unsafe_opening_count=0`), `false_train_glitch_closed=false`; `00_nominal` completes full 10-state round trip with `first_fault_detected_s=null` and reopens at `14.6 s` | [exp_l_fault_injection.json](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/failure_injection/exp_l_fault_injection.json) |
| **Exp M (8 Sensitivity Sweeps)** | `temporal_tolerance_s=0.15 s` (`< 0.20 s` frame cadence) triggers fail-safe closure on `23/23` train + `3/3` `no_train`; `confirm_frames=1` triggers `2/3` `no_train` FP vs `0/3` for `confirm >= 2` | [exp_m_sensitivity.json](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/sensitivity/exp_m_sensitivity.json) |

---

## 3. Software Verification & Reproducibility

- **V3 Test Suite ([`test_v3_four_layer_system.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_v3_four_layer_system.py)):** `20/20` tests passing covering all 16 required categories and 8 safety invariants (`SYNTHETIC_ONLY` in [`tests/test_access_classification.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/tests/test_access_classification.yaml)).
- **Safe Synthetic Test Runner ([`run_synthetic_tests.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/run_synthetic_tests.py)):** `94/172` safe test files executed (`1,857` passed, `1` pre-existing `METADATA_ONLY` failure in [`test_phase11_7_governance_controls.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/test_phase11_7_governance_controls.py) allowlist check, `guard.blocked = 0`, `violations = []`).
- **Full Repository Suite (`pytest tests/`):** `3,819 passed, 41 failed` (`3,860` total) — `0` regressions introduced by this effort; all 41 failures are itemized pre-existing environment/governance/legacy-script issues (see [SOFTWARE_TESTING_REPORT.md](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/SOFTWARE_TESTING_REPORT.md)).
- **Bit-Identical Reproducibility:** Two consecutive executions of `scripts/run_v2_experiments.py` produced byte-identical SHA-256 manifests across all `23/23` deterministic artifacts (`diff -u` empty, `shasum -a 256 -c` `23/23 OK`).

---

## 4. Honest Unresolved Boundaries

1. `data/governance/AUTH-MEDIA-ACCESS.json` is not present on disk; therefore direct re-inference of the 54 raw `.mov` and 54 `.wav` files in `data/raw/layer_b/v2/` was not permitted and was not performed. Real-data metrics reflect `pre-db40305` unrotated YOLO caches (`43.48%` front closure trigger rate vs rotated synthetic media verification).
2. No physical dedicated side camera (`camera_side`), no physical crossing occupancy sensor (`0/27`), and zero `last_carriage` YOLO predictions (`0/27` back streams) exist in the Layer B v2 dataset.
3. Accepted `Stage 2.1` human-reviewed ground truth is pending; all real-data timings rest on researcher-adopted AI-assisted reference proposals.
4. `simulation/runner.py` uses discrete Convention A stepping (`+0.20 s` systematic shift relative to forward-causal Convention B).
