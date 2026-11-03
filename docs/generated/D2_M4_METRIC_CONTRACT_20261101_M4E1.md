# D2 M4 Metric Contract

**Identifier:** `first_blocked_to_t4_clearance`  
**Status:** Conditional technical contract; not frozen or approved.

## Exact metric

For an eligible train event with an observable T4:

1. Find the first replay step where `is_passage_blocked=True`: `t_blocked`.
2. Consider strictly the interval `t_blocked < t < T4`.
3. M4 premature opening is true if any step in that interval is unblocked or has gate state `OPENING`/`OPEN`.
4. If no blocked step exists before T4, return M4 `None` and `never_protected=True` (M5).

This is not a duration value by itself; it is a premature-opening predicate over the protection interval. A future latency report must not invent a duration from the predicate.

## Sources and units

- Start: replay `SimulationStep.timestamp_s` seconds.
- End: human-approved `T4_tail_clearance.value_s` seconds on back-camera local clock.
- The replay timeline must be finite and strictly increasing.
- No front-camera timestamp is required by M4's boundary function.

## Validity conditions

- `premature_opening_window` explicitly equals `first_blocked_to_t4_clearance`.
- T4 is observable and approved.
- At least one blocked replay step occurs before T4 for an M4-evaluable event.
- Event is a train event, not engine or no-train.
- Ground-truth record is valid and promoted before official use.

## Missing/censoring/uncertainty

- Missing, censored, or uncertain T4: M4 not evaluable.
- No blocked step before T4: M5 `never_protected`, excluded from M4 premature-opening denominator and reported separately through `never_protected_count`.
- Missing/uncertain replay state: not evaluable; no substitution with T1/T2/T0.

## Cohort behavior

- No-train events: false-alarm path; not M4 train-event denominator.
- Engine event: explicitly excluded (`engine_event_excluded`).
- Train events: eligible only when approved GT and replay conditions hold.

## Aggregation

`aggregate_cohort()` counts only `evaluable` train events with non-null `premature_opening`. It rejects mixing multiple premature-opening window identifiers. M5 counts are tracked separately (`never_protected_evaluable_count`, `never_protected_count`).

## Technical conclusion

The M4 implementation is internally coherent and fail-closed. Final freezing still requires explicit researcher approval of this contract, its M5 reporting, and the D1/R04 conditions governing the surrounding evaluation.