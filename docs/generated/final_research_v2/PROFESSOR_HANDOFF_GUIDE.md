# Professor Handoff Guide — Evidence-Grounded Academic Supervision Summary

**Branch:** `exp/four-layer-completion` (cleanly branched from `d1032756de80963130e1cbd3d2334cb32139b996`)  
**Deliverables Root:** `docs/generated/final_research_v2/` (`13` reports, `10` figures, `BASELINE_SNAPSHOT.json`, `MISSION_LOG.md`, `FILE_HASH_MANIFEST.sha256`)  
**Results Root:** `results/exploratory_v2/` (`23` SHA-256-verified bit-identical JSON/CSV artifacts + `replays/` trace archives)

---

## 1. Original Research Objective & Technical Defects Found

The objective of the **Train Gate Automation — Bangladesh** prototype is to evaluate whether low-cost roadside multimodal perception (vision + audio + exit monitoring + crossing occupancy verification) combined with a fail-closed temporal state machine can safely automate level-crossing gate warning, closure, and post-departure reopening.

Prior audits and engineering inspection established five critical root defects preventing complete four-layer operation:
1. **Container Display-Rotation Defect (`-90°` sideways frames):** Unrotated `YOLOv8n` decoding in legacy `pre-db40305` runs caused missed train detections, and `cv2.VideoWriter` initialized before frame rotation risked corrupted geometry ([`video.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/vision/video.py), [`video_demo.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/demo/video_demo.py)).
2. **Stale-Detection Backfill in Evidence Collector:** Legacy snapshot assembly re-emitted old detections across empty frames, inflating apparent temporal persistence (`16/23` legacy vs `10/23` causal trigger) ([`collector.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/collector.py)).
3. **Disappearance-Based Premature Gate Openings:** V1/V2 departure rules allowed gates to reopen simply because back-camera detections vanished mid-train (`2/11` under V1, `4/11` under V2 on `sync11`).
4. **Audio Log-Mel Transform Mismatch & Road-Horn Confound:** Audio required strict natural log-Mel scaling (`log(mel_spec + eps)`) vs dB conversion ([`features.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/audio/features.py)), and Bangladesh road traffic horns triggered `0.800–0.826` scores on `no_train` clips.
5. **Missing Layer 2/4/Occupancy Integration:** No explicit side movement tracker, positive tail departure + occupancy clear AND-gate, or fail-safe fault state machine existed in integrated closed-loop form.

---

## 2. What Was Implemented

Preserving all frozen baselines (`configs/frozen_experiment_v1.yaml`, `decision_policy_v1.yaml`, `decision_policy_v2_candidate.yaml`, `results/exploratory_execution/`, `docs/generated/final_research/`, and `media_guard.py`) untouched:
- **Orientation Hardening & Deferred Writer:** PyAV `np.rot90(..., k=(rotation // 90) % 4)` aligned with OpenCV `CAP_PROP_ORIENTATION_AUTO` + fail-closed non-orthogonal rejection + deferred `VideoWriter`.
- **Causal Collector:** `allow_stale_detection_backfill=False` default, per-event `.reset()`, explicit `OccupancyEvidence` & `EvidenceStatus`, and preserved `allow_stale_detection_backfill=True` in legacy scripts (`exploratory_common.py`, `diagnostic_trace.py`).
- **Four-Layer V3 Decision Architecture ([`occupancy.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/occupancy.py), [`rules_v3_four_layer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/rules_v3_four_layer.py), [`decision_engine_v3_four_layer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/decision_engine_v3_four_layer.py), [`state_machine.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/state_machine.py), [`gate_model.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/gate_model.py), [`runner.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py)):**
  - Layer 1 independent `confirm_frames=2` (`conf >= 0.35`) approach trigger.
  - Layer 2 `SideMovementTracker` (`MOVING`, `STOPPED`, `SINGLE_FRAME`, `UNOBSERVED`).
  - Layer 3 advisory audio horn (`0.3700` natural log-Mel) extending clearance dwell without gating closure.
  - Layer 4 `CONSERVATIVE_POSITIVE` departure + explicit `OccupancyVerifier` AND-gate (`CLEAR` + healthy sensors + zero contradictions + dwell).

---

## 3. What Was Tested & What the Results Show

1. **Software Verification:** `20/20` tests pass in [`test_v3_four_layer_system.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_v3_four_layer_system.py); `1,857 passed, 1 pre-existing METADATA_ONLY failure` ([`test_phase11_7_governance_controls.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/test_phase11_7_governance_controls.py)) in `scripts/run_synthetic_tests.py` (`94` safe files, `guard.blocked = 0`, `0` violations); `3,819 passed, 41 pre-existing failed` in full `pytest tests/` (`0` regressions from this work). See [`SOFTWARE_TESTING_REPORT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/SOFTWARE_TESTING_REPORT.md).
2. **Real-Data Exploratory Findings (`all27` / `sync11` / `audio23` on cached `pre-db40305` detections):**
   - Approach trigger: `10/23` (`43.48%`, Wilson `[0.2563, 0.6319]`; `9/23` reached `CLOSING`/`CLOSED`), `0/3` `no_train` FP (`stateless_union`: `3/3` FP), `0/1` `engine` FP.
   - Timing before arrival `T2`: `0/11` `sync11` closed before `T2` (`n=9` full-closure margin `-105.5 s` to `-1.4 s`, median `-5.1 s`) due to close-range cameras + unrotated `pre-db40305` misses.
   - Audio (`audio23`, `2,600` windows): Recall `0.9231`, Precision `0.5455`, Specificity `0.0000`, ROC-AUC `0.6846`, AP `0.7739`; `no_train` road horns peak `0.800–0.826`.
   - Departure (`sync11`): Premature openings dropped from `2/11` (`V1`) and `4/11` (`V2`) to **`0/11` (`V3_CONSERVATIVE_POSITIVE`)** (exact McNemar `p=0.125`), closing `9/11` (`4` L1 + `5` back-camera EOF fail-safe).
3. **Controlled & Synthetic Verification (`Exp K, L, M` + Vision/Audio Checks):**
   - `7/7` orthogonal display rotations decoded upright + ran CPU `YOLOv8n` (`all_angles_passed=true`).
   - `18/18` fault scenarios passed with `all_transitions_legal=true` and **`0` unsafe openings**; only `V2_RULE_3C` opened prematurely (`12.4 s`) under sparse dropout (`exp_l`).
   - `8` parameter sweeps identified key boundaries (`confirm_frames >= 2`, `temporal_tolerance_s >= 0.25 > 0.20 s` cadence).

---

## 4. What Remains Uncertain (Explicit Supervision Qualification)

- **True upright YOLO recall on raw `.mov` files:** Blocked until researcher authorization (`AUTH-MEDIA-ACCESS.json`) permits re-decoding the `54` `.mov` streams with our corrected `video.py`.
- **Real-world automated reopening:** Blocked on hardware absence (`0/27` physical occupancy sensors, `0/27` physical side cameras, `0/27` `last_carriage` back labels) and small `n=11`/`n=3` cohort power.
- **Safety boundary:** This repository demonstrates a verified software prototype and experimental evidence — **it is NOT certified or ready for live field railway gate control**.

---

## 5. Claim-to-Evidence Traceability Map

| Conclusion Claim | Supporting Verification Files |
| --- | --- |
| Orientation & writer fix works across `0, ±90°, ±180°, ±270°` + `YOLOv8n` | [`vision_orientation_check.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/synthetic/vision_orientation_check.json), [`video.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/vision/video.py) |
| Natural log-Mel scale (`-11.8693` horn mean) verified vs dB | [`audio_transform_check.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/synthetic/audio_transform_check.json), [`features.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/audio/features.py) |
| Approach recall `10/23` (`9` physical close), `0/3` FP, `0/11` before `T2` | [`exp_a_front_detection.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_a_front_detection.json), [`fig09_detection_and_actuation_timing.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig09_detection_and_actuation_timing.png) |
| Audio confirms road-horn confounds (`0.0%` spec, `no_train` `0.80–0.83`) | [`exp_c_audio_horn.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_c_audio_horn.json), [`exp_k_ablation.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_k_ablation.json) |
| `V3_CONSERVATIVE` eliminates premature openings (`0/11` vs `4/11`) | [`exp_d_back_departure.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_d_back_departure.json), [`fig07_premature_opening_analysis.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig07_premature_opening_analysis.png) |
| Causal collector delta (`10` vs `16`) & stateless FP elimination (`0/3` vs `3/3`) | [`exp_i_complete_system.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_i_complete_system.json), [`exp_j_temporal_vs_stateless.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_j_temporal_vs_stateless.json), [`fig06_closure_performance.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig06_closure_performance.png) |
| `18/18` fault scenarios `100%` legal, `0` unsafe openings | [`exp_l_fault_injection.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/failure_injection/exp_l_fault_injection.json), [`fig08_fault_injection_outcomes.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig08_fault_injection_outcomes.png) |
| Upstream distance requirements (`46.67–283.33 m`) | [`exp_a_front_detection.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_a_front_detection.json), [`fig10_real_world_installation_concept.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig10_real_world_installation_concept.png) |
| Bit-identical reproducibility & full event trace matrix | [`FILE_HASH_MANIFEST.sha256`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/FILE_HASH_MANIFEST.sha256), [`exp_n_event_matrix.csv`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_n_event_matrix.csv), [`REPRODUCIBILITY.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/REPRODUCIBILITY.md) |
