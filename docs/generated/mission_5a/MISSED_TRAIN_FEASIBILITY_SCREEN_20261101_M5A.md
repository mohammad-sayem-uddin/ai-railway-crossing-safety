# Missed-Train Lead-In Feasibility Screen (RD-021) — IMPLEMENTED; not wired into the official runner

> Implemented in `src/railway_detection/evaluation/lead_in_screen.py` and optionally invoked by `EventMetricsCalculator.evaluate_run`. **No real event was screened.** Nothing here is an approval.

## 1. Purpose
A "missed train" is attributable to the system only if the recording gave the frozen decision policy enough physical time to detect, warn and close the arm before T1. Otherwise the event is **`insufficient_lead_in`**: *not evaluable* for missed-train reporting, **not a system failure**.

## 2. Calculation
```
approach_start = first_visible_time_s     if T0 is an OBSERVABLE boundary
               = 0.0 (replay start)       if T0 is left-censored (train already present)
               = UNKNOWN                  otherwise  -> outcome lead_in_unverifiable
available_lead_in_s = T1 - approach_start
passed  iff  available_lead_in_s >= min_block_latency_s
```
`min_block_latency_s` is an **explicit input with a provenance string** (no default). It is the first moment the frozen policy and gate model can physically be blocking after train evidence first appears. `derive_min_block_latency_s()` derives it by replaying a *synthetic* constant `front`-detection trace through the real decision engine and gate model (no ground truth, media, checkpoint or cache): **3.6 s** at both 0.1 s and 0.2 s ticks in this repository state (the design document's "about 3.6 s" is thereby reproduced, not typed in).

## 3. Outcomes and effect on reporting
| Outcome | Evaluable | `missed_train` | Reason / exclusion |
|---|---|---|---|
| `passed` | yes | True/False from the barrier state near T1 | — |
| `insufficient_lead_in` | **no** | `None` | `metric_exclusions["missed_train"]="insufficient_lead_in"` |
| `lead_in_unverifiable` (T0 unknown/uncertain) | no | `None` | named, never guessed |
| `t1_missing` | no | `None` | T1 not fabricated |
| `not_screened` (default, no latency supplied) | per old behaviour | unchanged | screen is **off by default** |

Aggregation adds `missed_train_insufficient_lead_in_count` and `missed_train_screen_excluded_count`; screened-out events are outside `missed_train_evaluable_count`, so the MTR denominator excludes them, and the counts are reported beside it.

## 4. Assumptions (all open to your correction)
1. The replay can first act on train evidence at T0 (observable) or at replay start (left-censored). A train visible only after some further delay would shorten the true lead-in; that is not modelled.
2. The synthetic derivation uses one front-camera source with an unambiguous `front` label at confidence 0.9 and the engine/gate defaults. A different policy, source count or confirmation setting changes the value — hence the provenance string.
3. `available ≥ latency` (equality passes). No safety margin is added.
4. T0 observability comes from approved ground truth only; none exists today.
5. This is stricter than the design document's M3 rule (which marks an event evaluable whenever T0 is observable); here an observable T0 that is *too close to T1* is also insufficient.

## 5. Not done
The screen is available to callers but the official `Phase12EvaluationRunner` and `clock_aware` do **not** yet supply `lead_in_min_block_latency_s`; wiring requires deciding where its provenance is recorded (suggested: the evaluation manifest). No real result exists. T0/T1 values are not approved for any event.
