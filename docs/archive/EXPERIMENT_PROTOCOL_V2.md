# Experiment Protocol V2

## Fair, Event-Level Evaluation of the Proposed Software Policy

**Status:** Proposed; final thresholds, timing rules, and test cohort must be frozen before final evaluation.  
**Prerequisite:** Layer B synchronized, event-labeled data as defined in `DATASET_SPECIFICATION_V2.md`.

## 1. Experimental principles

- The train-passage event is the primary analysis unit.
- Every B0–B7 system variant uses the same held-out Layer B events, event labels, source timing, output definitions, and predeclared timing rules.
- Model architecture, calibration, thresholds, temporal windows, and state rules are chosen using training/validation data only.
- Differences in information content are stated plainly; they are not evidence of causal necessity without the paired ablation.
- Layer A object-detection experiments remain separate from system-policy experiments.

## 2. Data partitions and freeze point

Partition using `crossing → session → recording → train-passage event → frame/audio window`. Hold out final test crossings where possible. Freeze: event manifest, labels, exclusions, model checkpoints, calibration mappings, thresholds, timing rules, state policy, and analysis configuration before final test execution.

Report all exclusions: unavailable modality, poor synchronization, clearance unobservable, ODD violation, corrupted source, or missing label. Do not substitute model-derived labels for missing reference labels.

## 3. Baseline comparison matrix

| ID | Inputs and policy | Question answered |
|---|---|---|
| B0 | One designated camera; independent-frame decision; no temporal filtering. | Does temporal processing change single-camera event behavior? |
| B1 | Same camera and detector as B0; temporal filtering. | Effect of temporal filtering. |
| B2 | Both cameras; temporal filtering; no state-machine policy. | Incremental second-camera evidence. |
| B3 | B2 plus state machine; no audio. | Incremental state-aware policy for vision. |
| B4 | Continuous audio/train-horn evidence only. | Acoustic evidence capability and false alarms. |
| B5 | Both cameras + audio fusion, with temporal filtering but no state-aware policy. | Incremental fusion before state policy. |
| B6 | Both cameras + audio + temporal filtering + state-aware policy. | Full proposed software policy. |
| B7 | B6 with one source removed at a time and with declared detectable-fault perturbations. | Source dependence and simulated fault sensitivity. |

If B4’s acoustic task cannot define crossing-entry timing or clearance, it is evaluated only on acoustic/event endpoints that it can support. It must never issue an opening decision.

## 4. Layer A perception experiments

Run separately from B0–B7:

- V-A1: three-class front/side/rear object detection on group-disjoint images;
- V-A2: one-class train detector on the same eligible image/event source, if desired;
- V-A3: taxonomy/threshold/calibration comparison on validation data.

Report AP, precision, recall, class confusion, calibration, negative-scene false positives, and metadata slices only when adequate held-out sample counts exist. Do not interpret mAP as a crossing-control outcome.

## 5. Primary endpoints

| Endpoint | Numerator | Denominator | Eligibility |
|---|---|---|---|
| Event-level missed-train rate | Evaluable events where the variant fails to issue the defined simulated warning/closure indication by the predeclared deadline. | Evaluable train-passage events with observable deadline reference. | Synchronization and entry/approach labels sufficient. |
| Premature-opening rate | Evaluable events where simulated opening begins before ground-truth tail clearance plus any frozen conservative margin. | Evaluable events with independently observable tail clearance. | Clearance reference must be observed/estimated under protocol; no `rear` model proxy. |

The exact simulated deadline/margin is a P0 decision. It may not be selected after looking at test outcomes.

## 6. Secondary endpoints

- Train-event recall: qualifying simulated train indication / evaluable events.
- False alarms per hour: false simulated train/warning/closure indications divided by evaluable no-train recording hours.
- Warning lead time: crossing-entry timestamp minus first qualifying warning timestamp; report distribution and negative values.
- Late-closure rate: closures occurring later than the frozen timing requirement under the explicitly simulated gate model.
- Unnecessary-closure rate/duration: closure decisions without a corresponding ground-truth event, with stated no-train exposure.
- Departure confirmation latency: qualifying positive departure indication relative to independently labeled exit/clearance reference.
- Calibration: Brier score and ECE for relevant probabilistic outputs, with calibration cohort separate from test.
- Fault behavior: scenario-specific endpoint values and whether invariants were violated.

## 7. Calibration and threshold protocol

Fit calibration mappings and choose class/source thresholds on validation partitions only. Keep calibration procedure, bins, metric definitions, and temporal/fusion thresholds fixed before final test. If scores are insufficiently calibrated, do not present arithmetic cross-modality confidence fusion as a validated method; use source-specific rule conditions instead.

## 8. Failure-sensitivity protocol

Simulated perturbations are secondary sensitivity experiments, not field reliability evidence. Each scenario specifies source, onset, duration, severity, detectability, random seed, expected policy response, and affected metric. Required scenarios: front failure, side failure, camera 1/2 failure, audio failure, stale evidence, delayed rear, false rear, out-of-order timestamp, conflicting sources, and new train while opening.

Report original evidence, perturbed evidence, and decision trace. Do not combine synthetic-fault performance with normal recorded-data performance.

## 9. State-transition table

This is the initial formal policy template. “Qualified” means calibrated, timestamp-valid, temporally confirmed evidence under frozen validation-selected rules. It must be completed with numeric/temporal parameter values before coding the decision engine.

| Current state | Required evidence/condition | Guard and timeout | Next state | Forbidden transition/rationale |
|---|---|---|---|---|
| `IDLE` | Qualified approach evidence from permitted source(s). | Input is in-order and within ODD. | `TRAIN_APPROACHING` | `IDLE → GATE_OPENING`: gate is already modeled open; no new opening command. |
| `IDLE` | No evidence. | None. | `IDLE` | No inference that a camera failure means normal/clear. |
| `TRAIN_APPROACHING` | Qualified approach persists. | Confirmation window satisfied. | `WARNING` | Direct `TRAIN_APPROACHING → CROSSING_CLEAR/GATE_OPENING`. |
| `WARNING` | Warning dwell elapsed and no prohibiting fault. | Frozen warning duration. | `GATE_CLOSING` | Opening because evidence temporarily drops. |
| `GATE_CLOSING` | Simulated close duration elapsed. | Gate feedback is a simulation variable. | `TRAIN_PRESENT` | `GATE_CLOSING → GATE_OPENING` without explicit new policy; train remains unresolved. |
| `TRAIN_PRESENT` | Train intersects/reference occupancy evidence or persistence continues. | Until qualified departure conditions begin. | `CROSSING_OCCUPIED` or remain. | Opening on loss of side/front evidence. |
| `CROSSING_OCCUPIED` | Qualified downstream/departure evidence begins. | Direction/geometry consistent; no unresolved conflict. | `TRAIN_DEPARTING` | Direct open from occupancy. |
| `TRAIN_DEPARTING` | Qualified `rear` model evidence in configured departure role. | Rear temporal confirmation; evidence fresh/in order. | `REAR_CONFIRMED` | Treating rear model evidence as ground-truth clearance. |
| `REAR_CONFIRMED` | Independent/operational clearance condition is positively satisfied. | Clearance reference/zone condition and margin; no new train/conflict. | `CROSSING_CLEAR` | `REAR_CONFIRMED → GATE_OPENING` without clearance guard. |
| `CROSSING_CLEAR` | Dwell/verification condition complete. | Frozen clear dwell; no new qualified approach. | `GATE_OPENING` | Open while stale/conflicting/new train evidence unresolved. |
| `GATE_OPENING` | Simulated opening duration elapsed and no new train evidence. | New approach causes configured cancellation/conservative transition. | `IDLE` | Completion to `IDLE` when a new train event is unresolved. |
| Any active state | Detected source fault, malformed/stale/out-of-order conflict requiring conservative response. | Configured fault detector; distinguish detectable from unknown fault. | `FAULT_FAIL_SAFE` or remain conservatively closed. | Opening due to unavailable/stale evidence. |
| `FAULT_FAIL_SAFE` | Explicit recovery requirements met and no unresolved event remains. | Frozen recovery evidence/dwell; may require manual simulation reset. | `TRAIN_PRESENT`, `CROSSING_CLEAR`, or `IDLE` only by explicit rule. | Automatic open solely because time passed or source silence persisted. |

### Required regression scenarios

1. Rear disappears: no opening from absence.
2. Front fails: system behavior follows predeclared degraded policy.
3. Side fails: no disappearance-to-clear inference.
4. Both cameras fail: no opening based on loss; report fault limitation.
5. Audio fails: no fabricated confidence or clearance.
6. Stale evidence: rejected/flagged per policy.
7. Delayed rear: old evidence cannot create a current clearance decision.
8. False rear: rear alone cannot satisfy clearance.
9. New train while opening: opening is cancelled/handled by explicit conservative rule.
10. Conflicting cameras: no unresolved-conflict opening.
11. Out-of-order timestamps: no unsafe state reversal.

## 10. Statistical analysis

Use the train-passage event as the primary cluster. Report event counts, crossing counts, point estimates, and confidence intervals. For paired B0–B7 comparisons, report paired differences on common eligible events and their uncertainty. Use crossing-aware/hierarchical resampling where sample size supports it. Do not use independent-frame tests as evidence of system-level significance.

Multiple training seeds quantify training variability, not additional field-event sample size. Pre-specify primary comparisons; label all others exploratory. Report failures and missing/unobservable labels rather than excluding them without accounting.

## 11. Minimum reporting table

Every B0–B7 row must state: test event count, test crossings, eligibility/exclusions, missed-train rate, premature-opening rate when evaluable, false alarms/hour, timing definitions, threshold/calibration version, state-policy version, and confidence interval. Tables must mark `not_evaluable` rather than `0` where clearance or timing references are unavailable.
