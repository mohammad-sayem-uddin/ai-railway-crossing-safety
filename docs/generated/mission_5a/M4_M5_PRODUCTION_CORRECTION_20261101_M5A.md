# M4 / M5 Production Correction (RD-016) — IMPLEMENTED in code; formal approval of the contract still PENDING

> **Implemented ≠ approved.** The classification below is implemented in `src/railway_detection/evaluation/metrics.py` following your confirmed decision RD-016. The metric contract itself still needs a researcher-authored approval (`GOV-D2-EVALUATION-PROFILE` is pending) before any official use.

## 1. What changed

| Item | Before | After |
|---|---|---|
| Core function | `m4_premature_opening` → `(bool|None, bool)` | `classify_m4(sim_result, T4)` → `M4Classification` (status, premature, never_protected, reason, replay_complete, first_blocked_s, last_step_s, interior_step_count, max_step_gap_s) |
| Legacy view | — | `m4_premature_opening` kept as a view: `(premature, never_protected)`; `never_protected` is `None` (not `False`) when evidence is incomplete |
| `evaluate_run` (M4 window) | inline call, no reason | uses `classify_m4`; sets `m4_status`, `m4_reason`, `m4_replay_complete`; incomplete evidence recorded in `metric_exclusions["premature_opening"]` |
| Aggregation | M4/M5 counts only | adds `m4_no_violation_count`, `m4_not_evaluable_count`, `m4_not_evaluable_reasons` (all in `to_dict()`) |
| Identity (TF-02) | bare id silently a train event | `resolve_event_cohort` / `UnqualifiedEventIdError`: fail closed |

## 2. The six confirmed cases — behaviour of the production code (all asserted in `tests/unit/test_mission5a_production.py`)

| # | Case (T4 approved) | Classification | premature | never_protected | Reason | Previously |
|---|---|---|---|---|---|---|
| 1 | Violation observed before replay ends | EVALUABLE | True | False | — | correct |
| 2 | Protected through valid T4, no violation | EVALUABLE | False | False | — | correct |
| 3 | No blocked step; replay reaches T4 | NEVER_PROTECTED_M5 | None | True | — (excluded from M4 denominator) | correct |
| 4 | No blocked step; replay short or empty | NOT_EVALUABLE | None | **None** | `replay_ended_before_T4` / `replay_empty` | **wrong: M5** |
| 5 | Blocked, no violation, replay ends before T4 | NOT_EVALUABLE | None | None | `replay_ended_before_T4` | **wrong: clean "not premature"** |
| 6 | Violation witnessed, then replay ends before T4 | EVALUABLE | True | False | — (`replay_complete=False` recorded) | correct |

## 3. Rules implemented

- **Strict open interval** `(t_blocked, T4)`: the first-blocked step and any step at `T4` are excluded.
- **No timestamp tolerance** (accepted rule): complete ⇔ `last retained step ≥ T4`; a replay ending 0.01 s short is incomplete.
- **Missing T4** → `NOT_EVALUABLE / t4_missing`; neither M4 nor M5 is asserted. Non-finite or negative T4, or non-increasing replay timestamps → `ValueError`.
- **Sparse replay:** a gap between retained steps is reported (`max_step_gap_s`) but **no gap tolerance is applied**.
- **Engine events** stay excluded from M4/M5 and from every pooled train aggregate.
- **Partition identities** (tested): `M4-evaluable = premature + no-violation`; `M5-evaluable = M4-evaluable + never-protected`; incomplete events appear in **neither** denominator and are listed with reasons.

## 4. One implementation choice that needs your confirmation (possible deviation)

**`no_steps_in_protection_interval`.** For a *complete* replay with a blocked step before T4 but **no retained step strictly inside** `(t_blocked, T4)` (e.g. steps at 0 s and 5 s, T4 = 5 s), no evidence of continuous protection exists. The previous code called this "not premature". The corrected code returns `NOT_EVALUABLE` with that reason, consistent with "do not treat incomplete evidence as safe" and "handle sparse replay steps". It is a stricter reading than the six-case table states; it introduces **no numeric tolerance**. If you prefer the old vacuous-safe reading, it is a one-branch change.

## 5. Callers and fixtures

`clock_aware.evaluate_event_replay` and `Phase12EvaluationRunner` now pass `cohort=truth.cohort` so the strict identity rule is satisfied from ground truth, and engine events reach the engine branch directly. Mechanical fixture edits (bare ids → `train_events/…` / `no_train_events/…`) in four existing test files are listed in the change map.

## 6. Not done / not claimed

No real replay, cache or event was evaluated. No metric value for any real event exists. The M4/M5 contract is not formally approved. `dual_report` (M4 + v9 side by side) is not implemented.
