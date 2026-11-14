# Experimental Methodology — Cache-Only Exploratory Replay & Stress Programme

**Evaluation Basis:** *Exploratory evaluation against researcher-adopted AI-assisted reference annotations.*  
All runs execute strictly from JSONL perception caches (`m3_multimodal_replay_manifest.json`) without calling `torch`, `cv2`, `av`, `ultralytics`, `load_validated_sync_aligner`, or bypassing repository governance gates.

---

## 1. Discrete-Tick Simulation & Policy Comparison

Replay executes at `stride_s = 0.2 s` (`5 Hz`), default `window_tolerance_s = 0.50 s`, sequentially ingesting cached observations per step so `SourceTracker` availability state never leaks backward across future timestamps:

| Component / Parameter | Policy V1 (Frozen `v1`) | Policy V2 Candidate (`v2`) | Stateless Baselines (`EXP-E`) |
|---|---|---|---|
| **Config Source** | `configs/frozen_experiment_v1.yaml` | `configs/decision_policy_v2_candidate.yaml` | Same thresholds (`0.35` vis, `0.37` aud), zero temporal state |
| **Approach Confirm** | `2` ticks (`0.4 s`) | `2` ticks (`0.4 s`) | Immediate `1`-tick reaction (`0` hysteresis) |
| **Warning -> Gate Closing** | `T_warn = 2.0 s`, `T_travel_down = 3.0 s` | Same actuation timing (`3.4–3.6 s` warn->blocked on trace) | Immediate `CLOSED` when active |
| **Hold Persistence** | `miss_tolerance` ticks | `miss_tolerance` + `RULE_2` audio delay extension | Zero hold memory (`stateless_vision_rule2` / `stateless_union`) |
| **Clearance Trigger** | Sustains absence (`T_clear = 3.0 s`) without `RULE_3C` departure shortcut | Adds `RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE` (`2.0 s` absent vision) + `RULE_3_POSITIVE_CLEARANCE` | Immediate `OPEN` on inactive tick |
| **Fail-Safe Clamp** | `RULE_4_FAIL_SAFE_CLAMP` & `RULE_9_SENSOR_RECOVERY` | `RULE_4_FAIL_SAFE_CLAMP` & `RULE_9_SENSOR_RECOVERY` + `RULE_7_NEW_TRAIN_INTERRUPT` | None (`0` state protection) |

---

## 2. Unperturbed Ablation Matrix (`336` Primary + `22` Sensitivity Runs)

1. **Single-Camera / Single-Modality Conditions (`27` events each):**  
   - `B0` (`camera_front` vision only) under `v2`, `v1`, `stateless_vision_rule2` (`81` runs)
   - `FRONT_AUDIO` / `B4` (front vision + audio) under `v2`, `v1`, `stateless_vision_rule2`, `stateless_union` (`108` runs)
   - `BACK_VISION` (`camera_back` on local clock) under `v2`, `v1` (`54` runs)
   - `AUDIO_ONLY` (audio only, `RULE_2` non-actuation test) under `v2` (`27` runs)
2. **Calibrated Dual-Camera Conditions (`11` `CALIBRATION_SUPPORTED` sync events ONLY):**  
   - `DUAL_VISION` / `B2` (calibrated front+back vision, audio off) under `v2`, `v1` (`22` runs)
   - `DUAL_VISION_AUDIO` / `B7` (full dual vision + audio) under `v2`, `v1`, `stateless_vision_rule2`, `stateless_union` (`44` runs)
   - **Scope Guard Verification:** Any attempt to run `DUAL_*` on `train_events/event_010` or the `16` independent-camera events raises `DualScopeAuthorizationError` (tested in `tests/unit/test_exploratory_pipeline.py`).
3. **`window_tolerance_s` Backfill Sensitivity (`22` runs):** Re-ran `DUAL_VISION_AUDIO` (`v2` & `v1`) across the `11` sync events with `window_tolerance_s = 0.25 s` vs default `0.50 s`.

---

## 3. Endpoint Definitions & Timing Conventions

- **Convention A vs Convention B Gate Duration:** Convention A sums blocked ticks $\times \Delta t$ (`[0, N-1]`); Convention B measures continuous physical interval $[t_{\text{block}}, t_{\text{open}})$ terminating at $(N-1)\Delta t$, yielding exact theorem $T_{\text{ConvB}} - T_{\text{ConvA}} = -\Delta t \cdot b_N \in \{-0.2\text{ s}, 0.0\text{ s}\}$.
- **Missed Train:** Evaluable when `t1_s != null` (`22/23` train, `10/11` sync). Marked `True` if `first_blocked_s is None` or `first_blocked_s > t1_s`. **`zero_protection`** (`closed_duration_s == 0.0`) isolates complete non-activation from late-closing left-censoring misses.
- **M4 Premature Opening (`m4_premature_opening`):** Evaluable when protected (`!never_protected`) and master-aligned `T4` exists (`m4_evaluable`); marked `True` if gate unblocks or commands opening inside $(t_{\text{blocked}}, T_4)$ (computed on `B7`/`B2`/`B0`/`B4` sync11 & `BACK_VISION` local `T4`). Legacy **V9 `[T1, T4)`** is reported alongside M4 for methodological contrast (penalizing pre-closure approach window as premature even when never closed).

---

## 4. Failure-Injection & Recovery Stress Programme (`202` Perturbation Runs + `11` Natural Audits)

Implemented in `scripts/run_failure_injection_replays.py` and strictly separated from unperturbed headline tables:
- **`EXP-G` (`47` runs):** Whole-modality ablation (`G1` front absent, `G2` back absent, `G3` audio absent — natural cache subsets), mid-passage dual vision dropout (`G4`, `n=11`), idle dual vision dropout (`G5`, `n=3`).
- **`EXP-H` (`11` natural audits + `28` perturbations):** Conflicting front vs rear (`H1`, `n=11`), subthreshold vision capped at `0.34 < 0.35` with active audio (`H2`, `n=11`), idle audio FP burst (`H3`, `3` no-train $\times$ `{v2, stateless_union}`).
- **`EXP-I` (`105` runs):** Single/dual dropouts (`I1–I4`), `2.5 s` stale timestamp injection (`I5–I6`), out-of-order frame reversal (`I7`), burst window drops (`I8`), seeded 30% random frame drops (`I9`, `seed=42`), idle 1-tick false injection (`I10`, `n=6` on `no_train` with `B0__v2` vs `Stateless_RULE2` delta).
- **`EXP-K` (`22` runs):** Fault+recovery cycles in idle (`K1`, `n=3`) and active crossing (`K2`, `n=11`), plus constructed second-train arrival during `REAR_CONFIRMED`/`GATE_OPENING` on clearing events (`K3`, `n=8`).
