# Statistical Analysis — Approach and Reported Quantities

## Design principles

1. **The event is the unit of analysis** (Protocol V2; design §9). Two camera
   recordings of one event are one sample. The engine-only event is always
   reported separately and never pooled with train events.
2. **Paired comparisons.** Policy and condition comparisons (v1 vs v2;
   vision vs vision+audio; temporal vs stateless) run on byte-identical
   cached inputs per event. Reported differences are exact paired outcome
   counts over the same events — the strongest design this dataset supports.
3. **Census, not sample.** The 27 events (11 for dual-camera claims) are the
   complete available record of one crossing, not a random sample of
   crossings. Accordingly this programme reports counts, proportions with
   explicit denominators, and per-event tables. **No p-values and no
   confidence intervals are reported for decision outcomes**: inventing
   inferential machinery for a single-site census would overclaim, and the
   mission guardrails prohibit invented statistics.
4. **Evaluability before arithmetic.** Per Protocol v9 §5.3, an event whose
   required boundary is censored or unobservable is `not_evaluable` for that
   metric, excluded from that denominator, and listed with its reason.
   Missing is never converted to zero; null annotation fields stay null.
5. **Pre-declared scope.** Experiments, conditions and the 9-metric frozen
   descriptive scope are fixed in EXPERIMENT_REGISTRY.csv before execution.
   No event, definition, or threshold was selected by looking at outcomes;
   the one open tuning question (RULE_3C gap length) is explicitly left
   undecided rather than fitted to clearance counts.

## Quantities reported in this programme

| Quantity | Value / form | Basis |
|---|---|---|
| Audio event agreement (M43) | TP 12 / FP 10 / FN 1 / TN 0; precision 54.55%, recall 92.31%, F1 0.6857, specificity 0%, accuracy 52.17% | 23 train events with adopted horn status; frozen max-window rule @ 0.37 |
| Audio ranking summaries (M43) | ROC-AUC 0.6846, AP 0.7739 | Descriptive summaries of the same 23-event comparison; not population estimates |
| Policy clearance outcomes (Phase 10.1) | v1: 0/11 events reach CROSSING_CLEAR; v2: 6/11; identical under naive and sync-corrected durations | Paired trajectories on the 11 CALIBRATION_SUPPORTED events |
| Frozen descriptive metrics (when gated replay runs) | Per-event values for the 9 DESCRIPTIVE_METRIC_SCOPE metrics + per-metric evaluable denominators | Hash-bound metric scope `1e10c02d…c36`; premature_opening under the definition **decided 2026-11-09: M4 (`first_blocked_to_t4_clearance`) primary, v9 as sensitivity on the 11 sync events** |
| Synthetic battery | Pass/fail per pre-declared expectation, per engine, with full traces | Behavioural validation only; no performance interpretation |

## Threats to validity (summary; full text in LIMITATIONS)

Single site and daytime-only recording; small and imbalanced cohort;
adopted AI-assisted references instead of canonical ground truth;
synchronization validated for 11/27 events only; recording lengths that
truncate the departure phase for 2 events; an audio event rule whose
aggregation brittleness is measurable only at event level because window
labels do not exist.
