# Reporting Specifications (M4 · M5 · Occupancy Duration)

> **Revised in Mission 4E.3:** incomplete-replay handling corrected — see `M4_INCOMPLETE_REPLAY_CLASSIFICATION_CORRECTION_20261101_M4E3.md`. Superseded text is marked.

> **PROPOSED — NOT APPROVED — NOT AUTHORIZATION.** Specifications only. **No value below was calculated from real data.**
> Three independent reports; no combined score; each has its own denominator.

Common to all: ids are cohort-qualified (`train_events/event_NNN`); counts are integers; times are **seconds**; every excluded
event is listed with a reason (never silently dropped); the governing protocol hashes (D1 doc §1) and replay/GT provenance hashes
are printed in the report header **once D1 is actually bound** — until then the header must read `D1: SELECTED_NOT_BOUND`.

## Report 1 — M4 premature gate opening

| Field | Definition |
|---|---|
| `premature_opening_definition` | must equal `first_blocked_to_t4_clearance`; any other/mixed value ⇒ report refused |
| `train_events_total` | train-cohort events in the evaluated split |
| `m4_evaluable_n` (**denominator**) | train events with approved observable T4 **and** a valid replay **and** ≥1 blocked step before T4 (`premature_opening_evaluable_count`) |
| `premature_opening_count` | evaluable events with a non-blocked step or OPENING/OPEN state strictly inside `(t_blocked, T4)` |
| `premature_opening_rate` | `count / m4_evaluable_n`, with Wilson 95 % CI when `n>0`; `null` if `n=0` (existing behaviour) |
| `m4_unevaluable_n` | `train_events_total − m4_evaluable_n`, **split into** M5 events and the reason table below |
| Reason table | `never_protected_before_T4 (M5)` · `T4_tail_clearance:censored` · `:uncertain` · `:not_applicable_or_unknown` · `ground_truth_missing/unverified` · `premature_opening_window_undecided` · `replay_ended_before_T4` *(proposed, not implemented; never counted as M5)* · `replay_empty` *(proposed)* · `clock_mismatch(...)` |
| Replay scope line | `front` / `back` / `fused`; for `fused` list the R04-accepted event ids |
| Unit statement | "boolean predicate over a protection interval; not a duration" |

Engine events and no-train events are reported in their own lines (`engine_events`, `no_train_events`, false-alarm block) and never in Report 1's denominator.

## Report 2 — M5 never-protected (separate)

| Field | Definition |
|---|---|
| `never_protected_evaluable_count` | train events with usable T4 and computed replay (M5-evaluable) |
| `never_protected_count` | M5-evaluable events with no blocked step before T4 |
| Identity check | `never_protected_evaluable_count = m4_evaluable_n + never_protected_count` — report must print it and fail if violated |
| Not-evaluable for M5 | T4 censored/uncertain/missing; unverified GT; replay unavailable — each with count and reason |
| Proportion/CI | **not specified** by the current implementation; any proportion is a new reporting choice requiring approval |
| Scope caveat | replay-relative (M5-R5) |
| Replay-incomplete line | count of events NOT_EVALUABLE for M5 because the replay ended before T4 or was empty (not in either denominator) |

## Report 3 — Full crossing occupancy duration (proposed identifier `full_crossing_occupancy_s`)

| Field | Definition |
|---|---|
| `occ_train_events_total` | train events in the evaluated split |
| `occ_evaluable_n` (**denominator**) | OCC-E2 events (separate from Report 1/2 denominators) |
| Duration summary (seconds) | `mean`, `median`, `min`, `max` of `D_occupancy`; per-event table `(event_id, onset_s, onset_camera, t4_s, d_s, error_bound_s)`. No SD/CI is specified; with small N prefer the per-event table |
| Strata | same-camera · cross-camera `aligned` · cross-camera `partially_aligned` (with `error_bound_s`) — never pooled silently |
| Missing physical onset | count of `physical_onset_missing` |
| Missing T4 | count of `t4_missing` |
| Censoring | `onset_left_censored`, `t4_right_censored`, other `*_censored` counts, **excluded from point estimates** (default profile); no bound estimates unless `report_censored_as_bounds` is separately approved *and* implemented |
| NOT_EVALUABLE reasons | full table by code: `physical_onset_missing`, `onset_not_independently_established`, `onset_left_censored`, `onset_censored`, `onset_uncertain`, `onset_unobservable_or_not_applicable`, `t4_missing`, `t4_right_censored`, `t4_censored`, `t4_uncertain`, `t4_unobservable_or_not_applicable`, `invalid_timestamp`, `reference_camera_missing`, `clock_mismatch_r04_unresolved`, `nonpositive_duration`, `engine_event_excluded`, `no_train_event` |
| Header statement | "ground-truth-only quantity; independent of the replay; describes events, not system performance" |

## Prohibited in any report

Combined/composite M4+occupancy score; a duration derived from M4; occupancy computed from `first_blocked`; hourly rates; pooling
censored lower bounds into point means; filling missing events with zeros.
