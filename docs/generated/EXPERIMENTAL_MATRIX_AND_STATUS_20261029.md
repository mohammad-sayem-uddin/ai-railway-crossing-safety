# Experimental Matrix and Status — Train Gate Automation

**Date:** 2026-10-29 UTC
**Status:** Diagnostic experiments COMPLETE; Official evaluation BLOCKED

## 1. Completed Diagnostic Experiments (B0–B7c)

All 14 conditions executed on 27 events using the diagnostic harness
(`scripts/run_real_world_experiments.py`). These are SOFTWARE SIMULATION results
on recorded data, not official Phase 12 evaluation.

### Main Results Table

| Cond | Description | Policy | Closed(s) | Mean Lead(s) | Premature | Faults | Episodes | False Alarms |
|---|---|---|---|---|---|---|---|---|
| B0 | Front Vision Only | stateless_1_frame | 342.85 | 2.008 | 2 | 0 | 14 | 1 |
| B1 | Audio Only | stateless_horn_threshold | 198.4 | 2.617 | 0 | 0 | 8 | 0 |
| B2 | Front Vision + Audio | stateless_3_frame | 356.2 | 2.092 | 1 | 0 | 13 | 1 |
| B3 | Temporal Persistence | temporal_2_frame | 361.5 | 2.104 | 1 | 0 | 12 | 0 |
| B4 | Full State Machine | frozen_decision_engine | 378.9 | 2.196 | 0 | 0 | 12 | 0 |
| B5a | Vision Dropout | frozen_decision_engine | 312.4 | 1.847 | 0 | 0 | 11 | 0 |
| B5b | Audio Dropout | frozen_decision_engine | 365.1 | 2.143 | 0 | 0 | 12 | 0 |
| B5c | Full Sensor Dropout | frozen_decision_engine | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| B6a | 10% Detection Jitter | frozen_decision_engine | 371.2 | 2.167 | 0 | 0 | 12 | 0 |
| B6b | 30% Detection Jitter | frozen_decision_engine | 348.7 | 2.054 | 1 | 0 | 13 | 0 |
| B6c | 50% Detection Jitter | frozen_decision_engine | 298.3 | 1.762 | 2 | 0 | 15 | 0 |
| B7a | ±0.1s Timing Jitter | frozen_decision_engine | 376.4 | 2.183 | 0 | 0 | 12 | 0 |
| B7b | ±0.3s Timing Jitter | frozen_decision_engine | 369.8 | 2.134 | 0 | 0 | 12 | 0 |
| B7c | ±0.5s Timing Jitter | frozen_decision_engine | 354.1 | 2.041 | 1 | 0 | 13 | 0 |

### Key Findings

1. **State machine eliminates premature openings**: B4 (full FSM) has 0 premature openings
   vs B0 (stateless) with 2. This validates the conservative dwell-timer design.

2. **Audio-only cannot open gates**: B1 closes gates on horn detection but never opens them
   (RULE_2_AUDIO_SUPPORT_ONLY). This is by design, not a failure.

3. **Vision dropout degrades protection**: B5a (no vision) reduces closure by 17.5% vs B4,
   demonstrating vision's primary role in approach detection.

4. **Detection jitter sensitivity**: 50% jitter (B6c) increases premature openings to 2 and
   reduces closure by 21.3%, showing the system's sensitivity to detector reliability.

5. **Timing jitter robustness**: ±0.5s jitter (B7c) causes only 6.5% closure reduction and
   1 premature opening, demonstrating reasonable temporal robustness.

6. **No false alarms in state machine**: B4 has 0 false alarms on 3 no-train controls,
   vs B0 with 1 false alarm.

### Cohort Breakdown

| Cohort | Count | Note |
|---|---|---|
| train_events | 23 | 2 sessions, left-censored T0 |
| no_train_events | 3 | ~60s total exposure |
| engine_events | 1 | Single locomotive, T3≡T4 |

## 2. Model Training Results

| Model | Dataset | Key Metric | Checkpoint SHA-256 |
|---|---|---|---|
| YOLOv8n (vision) | baler.v1i (3157 images) | mAP50=0.782, mAP50-95=0.521 | 3f5bb5b2... |
| CompactTrainHornCNN (audio) | train_horn + ESC50 | F1=0.869, AUC=0.961, thresh=0.37 | ea1bb81d... |

## 3. Official Evaluation Status

| Requirement | Status | Blocker |
|---|---|---|
| Protocol authority | UNRESOLVED | D1 decision needed |
| Metric profile | UNRESOLVED | D2 decision needed |
| Event split | UNRESOLVED | D3 decision needed |
| R04 scope | UNRESOLVED | D4 decision needed |
| Stage-2.1 ground truth | MISSING | Human review required |
| Input manifest | MISSING | Depends on split/R04 |
| EVAL-AUTH | MISSING | Depends on all above |
| Official evaluation | BLOCKED | All prerequisites |

## 4. Experiment Validity Boundaries

These results are:
- **Descriptive**: They characterize software behavior on recorded data.
- **Single-site**: All from crossing_A, Bangladesh.
- **Simulation**: Gate kinematics are modeled, not physical.
- **Left-censored**: T0 ≤ 0 for all train events.
- **NOT generalizable**: No cross-crossing or held-out claims.

They are NOT:
- Official Phase 12 evaluation results.
- Physical safety evidence.
- Deployment readiness claims.
- Statistical generalization to other crossings.

