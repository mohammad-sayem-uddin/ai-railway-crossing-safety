# Safety & State Machine Audit (`CrossingStateMachine` V3 & Interlocking Invariants)

**Audited Code Paths:** [`state_machine.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/state_machine.py), [`gate_model.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/gate_model.py), [`collector.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/collector.py), [`occupancy.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/occupancy.py), [`source_tracker.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/source_tracker.py), [`rules_v3_four_layer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/rules_v3_four_layer.py), [`decision_engine_v3_four_layer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/decision_engine_v3_four_layer.py), [`runner.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py)

---

## 1. Verified 11-State Deterministic Transition Graph

Transitions are strictly validated against `ALLOWED_TRANSITIONS` at every `0.20 s` tick:

1. `IDLE` -> `{IDLE, TRAIN_APPROACHING, WARNING, FAULT_FAIL_SAFE}` (`gate: OPEN`, `90.0°`)
2. `TRAIN_APPROACHING` -> `{IDLE, TRAIN_APPROACHING, WARNING, FAULT_FAIL_SAFE}` (`confirm_frames = 2` consecutive L1 frames >= `0.35`, else `RULE_L1_APPROACH_UNCONFIRMED_RESET` -> `IDLE`)
3. `WARNING` -> `{WARNING, GATE_CLOSING, FAULT_FAIL_SAFE}` (`warning_dwell_s = 2.0 s` before physical boom actuation)
4. `GATE_CLOSING` -> `{GATE_CLOSING, TRAIN_PRESENT, FAULT_FAIL_SAFE}` (`30.0°/s`, `3.0 s` stroke, passage physically blocked `<= 45.0°` at `1.5 s`)
5. `TRAIN_PRESENT` -> `{TRAIN_PRESENT, CROSSING_OCCUPIED, TRAIN_DEPARTING, FAULT_FAIL_SAFE}`
6. `CROSSING_OCCUPIED` -> `{CROSSING_OCCUPIED, TRAIN_DEPARTING, FAULT_FAIL_SAFE}` (held active by L2 `MOVING`/`STOPPED`, L3 audio support, or `OCCUPIED`)
7. `TRAIN_DEPARTING` -> `{TRAIN_DEPARTING, CROSSING_OCCUPIED, REAR_CONFIRMED, CROSSING_CLEAR, FAULT_FAIL_SAFE}`
8. `REAR_CONFIRMED` -> `{REAR_CONFIRMED, TRAIN_PRESENT, CROSSING_OCCUPIED, CROSSING_CLEAR, WARNING, GATE_CLOSING, FAULT_FAIL_SAFE}`
9. `CROSSING_CLEAR` -> `{CROSSING_CLEAR, TRAIN_PRESENT, CROSSING_OCCUPIED, GATE_OPENING, WARNING, GATE_CLOSING, FAULT_FAIL_SAFE}` (`clearance_dwell_s = 1.5 s`, extended by L3 horn `audio_hold_s = 1.5 s`)
10. `GATE_OPENING` -> `{GATE_OPENING, IDLE, WARNING, GATE_CLOSING, FAULT_FAIL_SAFE}` (**immediate abort & re-closure** verified in `Exp Q` `multi_train_reopen_interrupt`)
11. `FAULT_FAIL_SAFE` -> `{FAULT_FAIL_SAFE, IDLE}` (**recovery forbidden** under active faults or `require_manual_reset_after_active_fault = True`)

---

## 2. Safety Invariants Audited & Stress-Tested

| Safety Property | Verification Source | Result / Bound |
|---|---|---|
| **Transition Graph Legality** | `Exp A–Q` + [`test_v3_four_layer_system.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_v3_four_layer_system.py) | **`100%` legal** across all 27 real clips, 18 fault injections (`Exp L`), and 100 weather stress runs (`Exp Q`) — vs `stateless_union` & `stateless_vision_rule2` (`False` in `Exp J`). |
| **Non-Reopening Without Verified Clearance (AND-Gate)** | `Exp D`, `Exp E`, `Exp L`, `Exp Q` | Reopening requires BOTH L4 conservative departure (`rear` / `last_carriage` as configured) **AND** explicit `OccupancyState.CLEAR` + quiet L3 dwell + all clearance sources healthy (`0 / 11` premature openings vs `4/11` in `V2`). |
| **Audio Isolation Invariant** | `Exp C`, `Exp K`, `Exp O` | Layer 3 horn detection **never triggers closure alone** (`0/3` `no_train` FPs despite `0.800–0.826` road-horn scores) and **never opens barriers**; only reinforces active dwell/hold. |
| **Stalled Train / Crossing Obstacle Latch** | `Exp B`, `Exp L #14`, `Exp Q` | `SideMovementTracker` (`STOPPED`) and `OccupancyState.OCCUPIED` hold crossing `CLOSED` past `20.8 s` until physical obstacle clears (`reopen @ 22.6 s` in `Exp Q`). |
| **Contradiction & False-Clear Rejection** | `Exp L #08, #17` | [`OccupancyVerifier`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/occupancy.py) detects active vision box contradicting `OccupancyState.CLEAR` -> `CONTRADICTORY` -> enters `FAULT_FAIL_SAFE` / holds `CLOSED`. |
| **Causal Snapshot Consumption** | `Exp I`, [`collector.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/collector.py) | `allow_stale_detection_backfill=False` rejects out-of-order/duplicate timestamps (`Exp L #07`) and prevents single-frame phantom persistence across dropped frames (`16 -> 10` B4 triggers). |

---

## 3. Residual Hazard Boundaries Discovered During Audit (Do Not Hide)

1. **Healthy Sub-Threshold Optical Attenuation Blind Spot (`Exp Q` Critical Finding):**
   - Heartbeat supervision (`SourceTracker`) catches *missing, dropped, or frozen* camera packets (`FAULT_FAIL_SAFE`), **but when heavy rain/fog/night attenuates detection confidence below `0.35` (`alpha = 0.35 -> eff_conf = 0.308`) while `camera_1` continues streaming valid empty frames (`0` stale timeout), V3 stays in `IDLE/OPEN` (`100%` `miss_open_rate` at `alpha = 0.35`).**
   - *Mitigation:* Multimodal trigger diversity (e.g., low-cost trackside vibration/radar approach sensor in upstream redundancy, image blur/visibility estimator flagging degraded optical quality into `DEGRADED -> FAULT_FAIL_SAFE`).
2. **Staleness Cadence Floor (`Exp M`):** `temporal_tolerance_s` (`0.50 s` default) must strictly exceed sensor frame period (`0.20 s` at `5 Hz`); configuring `0.15 s` locks all `26/26` B4 clips into continuous `FAULT_FAIL_SAFE`.
3. **Discrete Stepping Convention (`Convention A` vs `Convention B`):** [`runner.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py) steps actuator kinematics inside the issuing tick (`-0.20 s` vs strict forward-causal post-tick actuation), explicitly annotated in all replay trace JSONs.
4. **Software Simulation Only:** [`PhysicalGateModel`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/gate_model.py) is an ideal piecewise-linear software kinematics proxy (`30.0°/s`); electro-mechanical boom inertia, relay contact bounce, and hardware limit-switch feedback remain unvalidated on physical barrier hardware.
