# Event Identity and Engine Routing Audit (Mission 5A.1)

> Evidence: `resolve_event_cohort`, `evaluate_run`, `aggregate_cohort`, the two official callers, the diagnostic runner, and a before/after comparison against the saved pre-5A `metrics.py`. Synthetic inputs only.

## 1. Identity resolution (`resolve_event_cohort`) — verified
Accepts `<cohort>/<event>` (cohort ∈ train_events / no_train_events / engine_events) or a bare id **with** an explicit cohort. Rejects (raises `UnqualifiedEventIdError`): bare id without cohort (`UnresolvedCohortError`, subclass), unknown cohort, unknown prefix, empty tail, extra separator, empty/`None` id, id–cohort contradiction. The same event number in three cohorts is distinct when qualified; with **bare** ids the aggregator's uniqueness check fails closed (`ValueError`). `SingleEventEvaluation` does **not** record the resolved cohort (F-09).

## 2. Contradictions the Mission 5A code did NOT catch (found and fixed in 5A.1)
Reproduced before the fix (synthetic):
| Input | Pre-5A.1 result | Consequence |
|---|---|---|
| `train_events/…`, `has_train_ground_truth=False` | evaluable **no-train** record (`no_false_alarm`) | a train event pooled into the false-alarm denominator |
| `no_train_events/…`, `has_train_ground_truth=True` | evaluable **train** record, M4 EVALUABLE | a no-train event pooled into train M4 |
| `train_events/…`, `ground_truth_status="engine"` | silently routed to the engine branch | contradiction accepted |
**Fix (5A.1, `metrics.py::evaluate_run`):** three fail-closed checks raise `UnqualifiedEventIdError`. The official callers (`clock_aware`, `evaluation_runner`) derive `has_train` from `truth.cohort == "train_events"` and pass `cohort=truth.cohort`, so they cannot produce these combinations, and `evaluation_runner` additionally refuses a replay/ground-truth cohort mismatch (`MANIFEST_COHORT_MISMATCH`). The Mission 5A claim "callers cannot silently override a contradictory identity" was therefore **true for id-vs-cohort and untrue for cohort-vs-flag** before this fix.

## 3. Regression introduced by Mission 5A and fixed in 5A.1 — unannotated events
`LayerBEvent.event_id` is the bare directory name. `ExperimentRunner._extract_event_ground_truth` returns `cohort=None, has_train_ground_truth=None, ground_truth_status="missing"` for unlabelled/unannotated events. Pre-5A: recorded as `ground_truth_missing`, non-evaluable. 5A: `evaluate_run` **raised**, which would have aborted `run_condition` for that condition. **Fix:** an *unresolved cohort* is tolerated **only** when the record is already unverified (`has_train_ground_truth is None` or status in `UNVERIFIED_GROUND_TRUTH_STATUSES`); such a record is non-evaluable and enters no denominator. Anything that could be evaluated, and any malformed/contradictory identity, still fails closed. Not verified against real Layer-B events (no real data read).

## 4. Engine routing — what actually changed
Compared old vs current `evaluate_run` (synthetic):
| Input | Pre-5A | Current |
|---|---|---|
| `engine_events/event_001`, cohort `None` | engine branch (`engine_event_excluded`) | same |
| `engine_events/event_001`, cohort `engine_events` | engine branch | same |
| **bare** `event_001`, cohort `None`, `has_train=False` | **no-train branch, evaluable (`no_false_alarm`)** | raises `UnqualifiedEventIdError` |
| bare `event_001`, cohort `engine_events` | engine branch | same |
So Mission 5A's statement that engine events "now reach the engine branch earlier" is **only true for bare ids with no cohort**; for the cohort-qualified form used officially there is no behaviour change. The old bare-id behaviour was materially worse: an engine event would have been an *evaluable no-train negative control*.

## 5. Engine branch correctness (verified)
Engine events return `evaluable=False`, `notes="engine_event_excluded"`, `has_train_ground_truth=False`, `premature_opening=None`, `never_protected=None`, `m4_status=None`, `missed_train_screen="not_screened"`; `evaluable=True` passed by a caller is ignored. In `aggregate_cohort` they are counted only in `engine_events`, not in `eligible_events`, M4, M5, missed-train or false-alarm denominators. `evaluation_runner` and `clock_aware` later set `notes="engine_event_excluded"`/`evaluable=False` again; nothing overwrites the engine classification into a train/no-train one. No engine outcome is computed or approved.

## 6. Residual items
`SingleEventEvaluation` lacks a `cohort` field (F-09); events with unverified ground truth are in no denominator but also unlisted in `summary.exclusions` (F-10); `evaluable=False` train records keep `m4_status="EVALUABLE"` (F-08). Tests: see the test-results document.
