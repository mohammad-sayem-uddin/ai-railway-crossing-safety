# System Architecture — V3 Four-Layer Causal Multimodal Crossing Protection Prototype

**Primary Architecture Visuals:**
- [Figure 1: Architecture Diagram](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig01_system_architecture.png)
- [Figure 2: 11-State FSM & Transitions](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig02_four_layer_workflow.png)

---

## 1. Modular Software Architecture

The prototype maintains strict separation between media decoding/normalization, causal evidence aggregation, pure rule evaluation, occupancy verification, finite-state arbitration, gate boom kinematics, and simulation logging:

| Subsystem | Module Path | Responsibility | Key Contracts / Classes |
| --- | --- | --- | --- |
| **Media Decoding & Orientation** | [`src/railway_detection/vision/video.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/vision/video.py) | Orthogonal display-matrix rotation (`0, ±90, ±180, ±270, ±360°`), native PTS preservation, `media_guard` boundary enforcement | `normalize_orthogonal_rotation`, `apply_display_rotation`, `frame_generator`, `VideoFrame` |
| **Visual Demo Writer** | [`src/railway_detection/demo/video_demo.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/demo/video_demo.py) | Defers `cv2.VideoWriter` creation until post-orientation frame shape is decoded | `process_video`, `VideoDemoSummary`, `ClassStats` |
| **Audio Feature Extraction** | [`src/railway_detection/audio/features.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/audio/features.py) | 16 kHz STFT (`n_fft=512`, `hop=256`, `64` Mel bands) supporting V3 `natural` log-Mel (`log(E + eps)`) and legacy `db` scale | `compute_log_mel_spectrogram`, `create_mel_filterbank` |
| **Typed Evidence Contracts** | [`src/railway_detection/fusion/evidence.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/evidence.py) | Immutable detection, audio/vision records, occupancy records, evidence status classification | `Detection`, `EvidenceRecord`, `OccupancyEvidence`, `OccupancyState`, `EvidenceStatus`, `DecisionRecord`, `classify_evidence_status` |
| **Causal Evidence Collector** | [`src/railway_detection/fusion/collector.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/collector.py) | Master-clock window alignment, monotone timestamp & cross-event leakage guards, single-consumption causal snapshots (`allow_stale_detection_backfill=False`) | `MultimodalEvidenceCollector`, `MultimodalFrame` |
| **Source Health Tracking** | [`src/railway_detection/fusion/source_tracker.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/source_tracker.py) | Per-source heartbeat timeout (`2.0 s`), staleness & recovery confirmation | `SourceTracker` |
| **Occupancy Verification** | [`src/railway_detection/fusion/occupancy.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/occupancy.py) | Resolves explicit 5-state zone occupancy & detects conflicts between crossing-zone vision detections and reported `CLEAR` | `OccupancyVerifier`, `OccupancyAssessment` |
| **Layer Rule Evaluators** | [`src/railway_detection/fusion/rules_v3_four_layer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/rules_v3_four_layer.py) | Source role grouping, L1/L2/L3/L4 evidence extractors, `SideMovementTracker`, `RuleIdV3` & `DeparturePolicyMode` | `extract_layer1_front_evidence`, `SideMovementTracker`, `extract_layer3_audio_evidence`, `extract_layer4_departure_evidence` |
| **Four-Layer Safety Arbiter** | [`src/railway_detection/fusion/decision_engine_v3_four_layer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/decision_engine_v3_four_layer.py) | 11-state causal state machine driver integrating L1 early closure, L2/L3 transit supervision, L4 departure + Occupancy AND-gate reopening, and fail-safe overrides | `MultimodalDecisionEngineV3FourLayer` |
| **FSM & Barrier Kinematics** | [`src/railway_detection/simulation/`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/) | Enforced state transition table, 90°↔0° gate boom actuation, simulation replay runner | `CrossingStateMachine`, `ALLOWED_TRANSITIONS`, `PhysicalGateModel`, `EventSimulationRunner` |

---

## 2. Preserved Legacy & Frozen Boundary

- **Frozen V1 Engine (`MultimodalDecisionEngine` / `rules.py`)** and **V2 Candidate Engine (`MultimodalDecisionEngineV2Candidate` / `rules_v2_candidate.py`)** along with `configs/frozen_experiment_v1.yaml`, `configs/decision_policy_v1.yaml`, and `configs/decision_policy_v2_candidate.yaml` remain byte-identical to baseline `d1032756de80963130e1cbd3d2334cb32139b996`.
- `MultimodalEvidenceCollector` defaults `allow_stale_detection_backfill=False` for V3 causal replay, while historical comparison helpers (`scripts/exploratory_common.py` and `src/railway_detection/experiments/diagnostic_trace.py`) explicitly pass `allow_stale_detection_backfill=True` to preserve exact historical V1/V2 baseline behavior.

---

## 3. Formal 11-State Finite State Machine

Transitions are governed by `ALLOWED_TRANSITIONS` in [`state_machine.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/state_machine.py#L31-L96):

1. `IDLE`: Gate open (`90.0°`). Enters `TRAIN_APPROACHING` (1st L1 qualifying detection), `WARNING`, or `FAULT_FAIL_SAFE`.
2. `TRAIN_APPROACHING`: Awaits `confirm_frames=2` consecutive front-camera frames (`conf >= 0.35`). Resets to `IDLE` on unconfirmed single-frame glitch (`RULE_L1_APPROACH_UNCONFIRMED_RESET`).
3. `WARNING`: Pre-closure warning siren/lights dwell (`warning_dwell_s=2.0 s`), then commands `GATE_CLOSING`.
4. `GATE_CLOSING`: `PhysicalGateModel` drives barrier boom `90.0° -> 0.0°` over `closing_duration_s=3.0 s` (`30.0°/s`); passage becomes blocked at `<= 45.0°` (`1.5 s` into actuation).
5. `TRAIN_PRESENT`: Boom horizontal (`0.0°`, fully closed). Advances to `CROSSING_OCCUPIED` on L2 side movement/presence, L4 back presence, or `OCCUPIED` occupancy sensor.
6. `CROSSING_OCCUPIED`: Active train passage monitored by Layer 2 (`MOVING` / `STOPPED`), Layer 3 horn extension, and Occupancy.
7. `TRAIN_DEPARTING`: Layer 4 observes locomotive/carriage/rear departure activity (`rear` onset or guarded disappearance tracking).
8. `REAR_CONFIRMED`: Positive L4 rear (and `last_carriage` when required) verified. Awaits `OccupancyState.CLEAR` + healthy required sources + zero contradictions; can re-enter `TRAIN_PRESENT` / `WARNING` / `GATE_CLOSING` if a second train triggers L1 or reverses.
9. `CROSSING_CLEAR`: Occupancy `CLEAR` verified; executes quiet `clearance_dwell_s=1.5 s` (default V3) extended by any active L3 horn detection (`audio_hold_s=1.5 s`).
10. `GATE_OPENING`: Boom raises `0.0° -> 90.0°` (`gate_opening_s=2.0 s` in V3; `3.0 s` in frozen V1 config). Any new L1 trigger, crossing-zone vision detection, or `OCCUPIED` reading immediately aborts opening and transitions back to `GATE_CLOSING` / `WARNING`.
11. `FAULT_FAIL_SAFE`: Entered from any active or idle state upon critical sensor outage, stale clearance source, crossing contradiction, stream EOF during passage, or prolonged timeout. Forces `CLOSED` until fault clears (and holds permanently if `require_manual_reset_after_active_fault=True` or during active crossing faults).

---

## 4. Discrete-Time Convention Note

`EventSimulationRunner.run_frames()` advances `PhysicalGateModel.step(dt, commanded_state)` immediately at tick `t` using the decision issued at tick `t` (**Convention A**). Under uniform `0.20 s` cadence, physical closure milestones recorded by `EventSimulationRunner` occur exactly `-0.20 s` earlier relative to strict post-tick actuation (**Convention B**, where the command issued at tick `t` moves the gate across `(t, t + dt]`), matching the repository's Table 11 forensic audit (`Missions 16G/16H`). All replay trace files under `results/exploratory_v2/replays/` carry explicit `convention_note` metadata documenting this `+0.20 s` Convention A/B offset.
