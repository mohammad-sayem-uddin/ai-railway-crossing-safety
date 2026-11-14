# Architecture Final Status — Exploratory Verification & Defect Registry

**Status Banner:** Canonical production modules (`decision_engine.py`, `decision_engine_v2_candidate.py`, `execution_gate.py`, `descriptive_exec_gate.py`, `media_guard.py`, `sync_calibration.py`) and frozen configs/checkpoints remain completely unmodified and intact. All exploratory runs executed via isolated scripts importing canonical engines in cache-only mode.

---

## 1. Frozen Pipeline & Component Inventory

| Layer | Canonical Implementation | Status / Hash (HEAD `c35d133f...`) |
|---|---|---|
| **Visual Detector** | YOLOv8n (`experiments/vision/39f402dfe460/checkpoints/weights/best.pt`, `conf=0.35`) | Frozen (`3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`) |
| **Acoustic Classifier** | CompactTrainHornCNN V3 (`experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`, `16kHz`, `n_fft=1024`, `hop=512`, `n_mels=64`, `ln(E+1e-10)`, `conf=0.37`) | Frozen (`ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`) |
| **Legacy Policy V1** | [`decision_engine.py`](../../../../src/railway_detection/fusion/decision_engine.py) (`configs/frozen_experiment_v1.yaml`) | Intact (`3f5e3521...` / `b8ef5da0...`) |
| **Candidate Policy V2** | [`decision_engine_v2_candidate.py`](../../../../src/railway_detection/fusion/decision_engine_v2_candidate.py) (`configs/decision_policy_v2_candidate.yaml`) | Intact (`41063a75...` / `d90828b2...`) |
| **Safety & Execution Gates** | [`media_guard.py`](../../../../src/railway_detection/safety/media_guard.py), `execution_gate.py`, `descriptive_exec_gate.py` | Intact & fail-closed (never bypassed) |
| **Exploratory Harness** | `scripts/exploratory_common.py`, `run_exploratory_replay.py`, `run_failure_injection_replays.py`, `evaluate_departure_reopening.py`, `compute_safety_metrics.py`, `compute_ablation_matrix.py`, `verify_exploratory_reproducibility.py`, `generate_exploratory_figures.py`, `build_final_research_deliverables.py` | Complete, AST-compliant, deterministic |

---

## 2. Proven Divergence Root Cause: Oct 13 Legacy Caches vs Nov 7–8 `m3_multimodal_replay_manifest.json`

Earlier Phase 10.1 docs showed different baseline detection volume (`0/11`–`6/11`) than Mission 39/43 (`329` front + `1,020` back vision detections across `13,092` records; `445/2,600` positive audio windows). Cross-verifying [`CORRECTIVE_EXPERIMENT_AUDIT.md`](../../../CORRECTIVE_EXPERIMENT_AUDIT.md), [`AUDIO_MODEL_EXPERIMENT_REPORT.md`](../professor_evidence/mission43/AUDIO_MODEL_EXPERIMENT_REPORT.md), and Mission 44 diagnostics proved **both cache sets used identical frozen YOLOv8n and Audio V3 checkpoints**, differing in two upstream preprocessing changes:

1. **Acoustic Feature Align Fix (`ln(E + 1e-10)`):** Mission 39/43 corrected the log-mel feature representation from legacy dB mismatch, raising positive acoustic windows (`>= 0.37`) from `9` (legacy active cache) to `445/2,600`.
2. **PyAV `DISPLAYMATRIX` Rotation Drop (`44/54` Sources Unrotated):** Oct 13 caches (`results/experiments/cache/train_events_event_001_camera_front_camera_1_vision.jsonl`: `194/249` nonempty frames, portrait bbox `[402.5, 925.8, ...]`) used OpenCV auto-rotation (`CAP_PROP_ORIENTATION_AUTO`). Mission 37/38 (`5067d76`, `70e6c1e`) migrated video decode to PyAV (`source_pts=True`), inadvertently dropping `DISPLAYMATRIX` orthogonal rotation on **`44/54` video sources (`24 front, 20 back`)** (`DISPLAY_ROTATION_DEFECT_REPRODUCTION.json`). Mission 39/43 ran YOLOv8n over those sideways landscape frames (`train_events_event_001_front.jsonl`: `6/250` nonempty frames, landscape bbox `[1121.6, 749.6, ...]`). Mission 44 (`db40305`) repaired `video.py` but did not re-run raw video inference (`no_model_forward_or_raw_source_access: True`), so `m3_multimodal_replay_manifest.json` permanently reflects pre-fix unrotated decode.

---

## 3. Architectural Defects Discovered in Replay Fusion & State Machine

### 3.1 `MultimodalEvidenceCollector.generate_frames_from_history` Availability Leak
In `src/railway_detection/fusion/collector.py:243`, calling `generate_frames_from_history` queries `self.tracker.get_availability_map(t)` **after** the full history buffer has been ingested. Consequently, if a stream ends in `available=False`, `MISSING` status leaks backward onto earlier timestamps (`t = 0.0 s`) unless frames are assembled sequentially one tick at a time (verified by `test_clock_aware_boundary_and_availability_isolation` in `tests/unit/test_exploratory_pipeline.py`).

### 3.2 `window_tolerance_s = 0.50 > stride_s = 0.20` Single-Frame Backfill Bug
Under default `window_tolerance_s = 0.50 s` and `stride_s = 0.20 s`, a single isolated YOLO frame detection (`t = k`) falls within `|t - t_det| <= 0.50` across **three consecutive `0.20 s` ticks** (`t = k, k+0.2, k+0.4`). This satisfies `confirm_frames = 2` (`0.40 s`) from a single frame, generating false closures on `no_train_events/event_001` & `event_003` (`14.2 s` in `B0`) and triggering `SourceTracker` out-of-order warnings. Tightening `window_tolerance_s` to `0.25 s` prevents 1-frame backfill (`test_window_tolerance_backfill_stops_at_025`), eliminating false approaches from isolated ticks while dropping `B7__v2` sync clearances (`8/11 -> 5/11`) and doubling zero-protection (`2/11 -> 4/11`).

### 3.3 `RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE` Premature Clearance Hazard
Policy V2 permits transition `TRAIN_DEPARTING -> REAR_CONFIRMED` after `2.0 s` absence of vision detections (`RULE_3C`), even when front/back detectors are merely sparse (`0.76%–5.07%` `cam2` qualifying density on `9/10` `T4` sync events). In `B7__v2`, **`8/8` clearances fired via `RULE_3C`** (`0` via `RULE_3B`), causing `7/9` (`77.78%`) M4 premature openings.

### 3.4 Fail-Safe & Monotonicity Controls Verified Clean
Despite perceptual sparsity, fail-closed engine guards operated without fault-to-open violations (`0/202` runs), `11/11` out-of-order timestamp streams rejected, `14/14` idle/active dual-dropout injections cleanly clamped (`RULE_4_FAIL_SAFE_CLAMP`) and recovered (`RULE_9_SENSOR_RECOVERY`), `DUAL_*` refused non-`CALIBRATION_SUPPORTED` events (`event_010` + `16` independent events), and `AUDIO_ONLY__v2` obeyed `RULE_2_AUDIO_SUPPORT_ONLY` (`0` closures across `23` train + `3` no-train events).
