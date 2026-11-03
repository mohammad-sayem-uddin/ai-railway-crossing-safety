# Phase 3: Sensor Health, Staleness, and Decision Policy Report

**Project:** Railway Crossing Vision–Audio Fusion Safety System  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Execution Date:** 2026-10-13  
**Status:** Complete — All 20 Targeted Scenarios and 46 Combined Regression Tests Verified  

---

## 1. Executive Summary

Phase 3 implements an explicit, deterministic sensor health state machine, timing-aware staleness evaluation, camera-clock isolation safeguards (R04), and a hardened multimodal decision policy covering degraded, missing, and recovering sensor evidence.

### Key Achievements:
1. **Explicit Sensor Health State Machine:** Defined and integrated `SensorHealth` (`HEALTHY`, `DEGRADED`, `STALE`, `MISSING`, `RECOVERING`) with granular reason codes (`HealthReason`) in `SourceTracker`.
2. **Negative Evidence Invariant (IMA-15 Resolved):** Verified that a valid frame with zero train detections or low audio probability is tracked as `HEALTHY` negative evidence (`OBSERVATION_NO_DETECTIONS`), eliminating false sensor dropout classifications.
3. **Staleness Boundary Enforcement:** Enforced strict boundary conditions around the frozen $2.0\text{s}$ timeout ($t_{\text{age}} \le 2.0\text{s}$ is fresh; $t_{\text{age}} > 2.0\text{s}$ is stale).
4. **Safety Rules Hardened:** Implemented `RULE_5_STALE_SOURCE_ABORT` (stale vision data aborts clearance dwell and clamps gate closed), `RULE_6_DEGRADED_SOURCE_HOLD` (degraded departure camera holds gate closed), and `RULE_9_SENSOR_RECOVERY` (2 confirmation frames required before clearing fail-safe).
5. **Actuator Kinematics Audited:** Proved sequential barrier boom timing: $2.0\text{s}$ warning dwell + $1.5\text{s}$ descent to $45^\circ$ vehicular obstruction ($3.5\text{s}$ total) + $1.5\text{s}$ descent to $0^\circ$ fully closed ($5.0\text{s}$ total).
6. **Authoritative Configuration Integrity Preserved:** `configs/frozen_experiment_v1.yaml` canonical hash preserved (`999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`). Versioned decision policy created at `configs/decision_policy_v1.yaml` with canonical hash `051c908d4db23687db33cbc8349945b241a0735b362413be876d7017a5eacc9d`.
7. **Full-Dataset Benchmark Guard:** Confirmed that full-dataset benchmark execution, model training, and candidate review approval remain strictly unexecuted in this phase.

---

## 2. Audit of Existing Implementation vs Changes Made

| Component | Pre-Phase 3 State | Phase 3 Upgraded State | Rationale & Defect Addressed |
|---|---|---|---|
| `fusion/source_tracker.py` | `SensorHealth` enum existed but was unused; binary boolean availability; no recovery frames | Full deterministic state machine (`HEALTHY`, `DEGRADED`, `STALE`, `MISSING`, `RECOVERING`); 2 confirmation frames for recovery; flapping counter | Resolves IMA-15. Distinguishes missing data from negative model evidence. Enforces $2.0\text{s}$ staleness timeout. |
| `fusion/rules.py` | Contained Rules 1–4, 7–8; Rules 5, 6, 9 missing from enum | Added `RULE_5_STALE_SOURCE_ABORT`, `RULE_6_DEGRADED_SOURCE_HOLD`, and `RULE_9_SENSOR_RECOVERY` | Formalizes clearance abortion on stale data, departure camera degradation hold, and recovery confirmation. |
| `fusion/evidence.py` | `DecisionRecord` lacked sensor health, reason codes, observation ages, and gate command | Added `source_health`, `health_reasons`, `observation_ages`, `gate_command` | Produces fully auditable decision records reconstructing sensor timelines. |
| `fusion/collector.py` | `MultimodalFrame` lacked health and age maps; ingested records via `record_heartbeat()` without detections | Added `source_health`, `health_reasons`, `observation_ages`; ingests via `record_observation()` passing detections | Differentiates zero-detection healthy frames from corrupted or missing inputs. |
| `fusion/decision_engine.py` | Relied solely on external boolean availability; no staleness checking during clearance; audio threshold defaulted to 0.50 if unconfigured | Integrated `SourceTracker`; evaluates staleness at tick $t$; enforces Rule 5 on stale clearance data, Rule 6 on departure camera degradation, Rule 9 on recovery | Prevents gate opening on stale observations; enforces fail-safe clamp when cameras fail. |
| `simulation/gate_model.py` | Physical barrier model existed with $30^\circ/\text{s}$ descent/ascent rate | Audited and verified against warning dwell progression | Formally documented and tested interaction between warning dwell and boom descent. |
| `experiments/layer_b_processor.py` | Enforced R04 check raising `TimingIntegrityError` | Re-verified and covered in targeted test suite | Guarantees unverified zero-offset cross-camera temporal fusion remains blocked. |

---

## 3. Targeted Test Results

A dedicated regression test suite was created in [`tests/unit/test_phase3_sensor_health_decision_policy.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_phase3_sensor_health_decision_policy.py) covering all 20 required scenarios:

| # | Test Scenario | Verified Invariant | Result |
|---|---|---|:---:|
| 1 | Healthy camera with 0 detections | Classified as `HEALTHY` (`OBSERVATION_NO_DETECTIONS`); crossing remains `IDLE` | **PASSED** |
| 2 | Healthy audio with low probability | High availability, no spurious gate trigger in `IDLE` | **PASSED** |
| 3 | Missing video input | Active crossing clamps to `FAULT_FAIL_SAFE` (`RULE_4_FAIL_SAFE_CLAMP`) | **PASSED** |
| 4 | Missing audio input | Audio marked `MISSING`; vision-based safety functions unimpeded | **PASSED** |
| 5 | Staleness timeout boundary | Fresh at $1.9\text{s}$ and $2.0\text{s}$; strictly `STALE` at $2.01\text{s}$ | **PASSED** |
| 6 | Inference latency vs media time | $0.8\text{s}$ processing latency tracked in metadata without false staleness | **PASSED** |
| 7 | Out-of-order timestamps | Frame $t < t_{\text{last}}$ rejected under `RULE_8_OUT_OF_ORDER_REJECTION` | **PASSED** |
| 8 | Duplicate observations | Idempotent handling; no double-counting of confirmation counters | **PASSED** |
| 9 | Front camera stale, back healthy | Explicitly isolated in health maps; crossing avoids false full clamp | **PASSED** |
| 10 | Back camera stale in departure | Departure camera lost $\implies$ holds `TRAIN_DEPARTING` (`RULE_6`) | **PASSED** |
| 11 | Independent camera timelines | Front and back timestamps tracked independently; no raw cross-comparison | **PASSED** |
| 12 | Unsynced cross-camera fusion | Raises `TimingIntegrityError` enforcing R04 cross-camera safeguard | **PASSED** |
| 13 | Detection dropout during transit | Disappearance without rear confirmation holds gate closed | **PASSED** |
| 14 | Stale data attempting clearance | Stale camera during `REAR_CONFIRMED` triggers `RULE_5_STALE_SOURCE_ABORT` | **PASSED** |
| 15 | Video termination while occupied | Media end without rear confirmation clamps in `FAULT_FAIL_SAFE` | **PASSED** |
| 16 | Recovery confirmation | Resumed source requires $2$ frames before becoming `HEALTHY` | **PASSED** |
| 17 | Flapping oscillation tracking | Rapid fail/recover toggling increments `flapping_count`, holds in `RECOVERING` | **PASSED** |
| 18 | Actuator barrier kinematics | Arm reaches $45^\circ$ obstruction at $1.5\text{s}$, fully closed $0^\circ$ at $3.0\text{s}$ | **PASSED** |
| 19 | Engine-only traversal | Single locomotive executes clean approach, closure, departure, clearance, open | **PASSED** |
| 20 | Audio horn confounder | High audio horn confidence without vision is support-only (`RULE_2`); gate `OPEN` | **PASSED** |

### Combined Test Execution:
```bash
venv/bin/pytest tests/unit/test_phase3_sensor_health_decision_policy.py tests/unit/test_frozen_config_safeguards.py tests/unit/test_decision_engine.py -v
============================== 46 passed in 1.39s ==============================
```

---

## 4. Actuator Boom Kinematics Timeline

```
Approach Confirmed
    │
    ▼ (t = 0.0s)
Warning Dwell Begins: Bells & Flashers Activated, Gate Commanded OPEN
    │
    ▼ (t = 2.0s)  ── [2.0s elapsed]
Warning Dwell Ends: Gate Commanded CLOSING, Boom Arm Begins Descent at 30°/s
    │
    ▼ (t = 3.5s)  ── [1.5s descent]
Arm Reaches 45°: Vehicular Road Traffic Obstructed (is_passage_blocked = True)
    │
    ▼ (t = 5.0s)  ── [3.0s descent total]
Arm Reaches 0°: Barrier Fully Lowered (is_fully_closed = True) -> TRAIN_PRESENT
```

- Total time from approach confirmation to road obstruction: **$3.5\text{s}$**.
- Total time from approach confirmation to fully closed barrier: **$5.0\text{s}$**.
- Warning dwell ($2.0\text{s}$) and physical barrier descent ($3.0\text{s}$) occur sequentially.

---

## 5. Configuration and Checkpoint Integrity Verification

| Artifact | File Path | Canonical / File SHA-256 Digest | Status |
|---|---|---|:---:|
| Frozen Experiment Base | `configs/frozen_experiment_v1.yaml` | `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e` | **VERIFIED UNCHANGED** |
| Phase 3 Decision Policy | `configs/decision_policy_v1.yaml` | `051c908d4db23687db33cbc8349945b241a0735b362413be876d7017a5eacc9d` | **AUTHORITATIVE GENERATED** |
| YOLO Vision Weights | `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` | `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` | **VERIFIED UNCHANGED** |
| Audio V3 Weights | `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt` | `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782` | **VERIFIED UNCHANGED** |
| Prohibited Audio V2 | `models/audio/best_checkpoint.pt` | `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5` | **BLOCKED & UNMODIFIED** |

---

## 6. Known Risks and Decisions Requiring Researcher Approval

1. **R04 Empirical Synchronization Required for Multicamera Fusion:**
   - Front and back camera start times differ by up to $33\text{s}$.
   - Cross-camera temporal fusion remains blocked by default. Fusing front and back cameras in benchmark runs requires researcher decision: either provide empirical audio cross-correlation offsets per event via `SyncAligner`, or evaluate cameras independently.
2. **Ground Truth Candidate Approval Pending:**
   - `data/ground_truth/reviews/**` candidate annotations have not been approved. Ground truth cannot be used for formal benchmark evaluation until independently reviewed and signed off.
3. **Full-Dataset Benchmark Execution Pending:**
   - Preflight verification is complete. Full-dataset batch processing remains deferred to subsequent integration phases.

---

## 7. Next Steps: Phase 4 Preflight Readiness

Phase 3 is complete with all safety policies, sensor health state machines, staleness boundaries, and regression invariants passing. The repository is ready to proceed to **Phase 4: Integration Verification and Preflight Validation**.
