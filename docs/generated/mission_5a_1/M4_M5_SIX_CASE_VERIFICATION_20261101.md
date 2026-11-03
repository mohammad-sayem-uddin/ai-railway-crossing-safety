# M4 / M5 Six-Case Verification (Mission 5A.1)

> Independent code-level audit. Evidence = the actual `classify_m4` (src/railway_detection/evaluation/metrics.py) exercised on synthetic steps, plus the saved pre-5A copy for before/after. **Nothing here approves the M4/M5 contract.**

## 1. Which "six cases"?
Two six-item lists exist and they **do not coincide**:
* **List A — Mission 5A decision matrix** (what was implemented): (1) violation observed before replay ends; (2) protected through valid T4, no violation; (3) no blocked step, replay reaches T4; (4) no blocked step, replay short/empty; (5) blocked, no violation, replay ends before T4; (6) violation witnessed, then replay ends before T4.
* **List B — this mission's brief**: (1) blocked interval + observed premature opening; (2) blocked interval, no violation, valid T4; (3) no valid blocking onset before T4; (4) missing/censored T4; (5) replay truncated; (6) sparse/incomplete replay.
Items 4 and 6 of List B (missing T4; sparse) are **not rows of the decision table**; they are covered by implementation choices (`t4_missing`, `no_steps_in_protection_interval`). The table below keeps List A's rows and adds the List-B/other situations as separate rows. Nothing was inferred beyond what the code does.

## 2. Verified behaviour (production code, current)

| # | Situation (T4 approved unless stated) | Status | premature | never_protected | Reason | M4 denominator | M5 denominator | Interpretation |
|---|---|---|---|---|---|---|---|---|
| A1 / B1 | violation inside `(t_blocked, T4)` | EVALUABLE | True | False | — | in (premature) | in (not M5) | premature |
| A2 / B2 | blocked, ≥1 retained step inside, no violation, last step ≥ T4 | EVALUABLE | False | False | — | in (no-violation) | in (not M5) | protected |
| A3 / B3 | no blocked step before T4, last step ≥ T4, ≥1 earlier step | NEVER_PROTECTED_M5 | None | True | — | **out** | in (M5) | never protected (counts only) |
| A4a | no blocked step, last step < T4 | NOT_EVALUABLE | None | **None** | `replay_ended_before_T4` | out | out | not evaluable — never safe, never M5 |
| A4b | empty replay | NOT_EVALUABLE | None | None | `replay_empty` | out | out | not evaluable |
| A5 / B5 | blocked, no violation, last step < T4 | NOT_EVALUABLE | None | None | `replay_ended_before_T4` | out | out | not evaluable |
| A6 | violation witnessed, replay then ends < T4 | EVALUABLE | True | False | — (`replay_complete=False`) | in (premature) | in | premature (definite) |
| B4 | T4 missing (`None`) | NOT_EVALUABLE | None | None | `t4_missing` | out | out | not evaluable; reason for censoring comes from `exclusion_reasons` |
| B4′ | T4 censored via `ground_truth_status="censored"` | (early return, **no M4 classification**) | None | None | `notes=ground_truth_censored` | out | out | outside the eligible set entirely (see finding F-10) |
| B6 | blocked, complete, **no retained step inside the interval** | NOT_EVALUABLE | None | None | `no_steps_in_protection_interval` | out | out | not an original row — implementation choice (finding F-05) |
| X1 | invalid T4 (NaN/inf/negative/bool) or non-increasing/NaN/negative replay timestamps | raises `ValueError` | — | — | — | — | — | fail closed |
| X2 | **first retained step after T4 (nothing observed before T4)** | NEVER_PROTECTED_M5 | None | True | — | out | in (M5) | **asserts M5 from zero evidence — OPEN finding F-04** |
| X3 | replay starts late (first step 4.0 unblocked, T4 = 5.0, last 6.0) | NEVER_PROTECTED_M5 | None | True | — | out | in | start coverage unchecked — **OPEN finding F-04** |

Rows A1–A6 and B4 match the confirmed matrix exactly. Disagreements with the confirmed intent: **X2/X3** (the code checks only that the replay *ends* at/after T4, never where it *starts*) and the undecided **B6** choice.

## 3. Strict interval (verified)
`(t_blocked, T4)` is open at both ends: the first-blocked step (even carrying an `OPENING` label) and any step exactly at T4 are excluded (A: opening at T4 → not premature; 5.0000001 → premature). Duplicate, reversed, NaN, infinite or negative timestamps raise `ValueError`; a boolean or non-finite T4 raises. **No normalization is applied**: comparisons are exact floating-point (`0.1+0.2` ≠ `0.3`), consistent with the accepted no-tolerance rule but a latent boundary hazard (finding F-17).

## 4. Aggregation — exact definitions (`aggregate_cohort`, over `eligible` = evaluable ∧ has_train_ground_truth ∧ not engine ∧ not unverified-GT)
* **M4-evaluable** (`premature_opening_evaluable_count`) = eligible events with `premature_opening is not None`.
* **premature** (`premature_opening_count`) = M4-evaluable with `premature_opening == True`.
* **no-violation** (`m4_no_violation_count`) = eligible with `m4_status == EVALUABLE ∧ premature_opening == False`. Partition: `premature + no-violation = M4-evaluable` (tested).
* **M5-evaluable** = eligible with `never_protected is not None`; **M5 count** = those `True`. Identity `M5-evaluable = M4-evaluable + M5 count` (tested).
* **not evaluable** (`m4_not_evaluable_count/_reasons`) = eligible with `m4_status == NOT_EVALUABLE`, by reason. They appear in **neither** denominator and are listed in `summary.exclusions`.
* Never in any train denominator: engine events (excluded by id/cohort/notes), no-train events, and events with unverified ground truth.
* **Not reported anywhere in the summary:** events outside `eligible` because of unverified ground truth (finding F-10, pre-existing).
No new statistic or test was introduced.

## 5. Recommendation summary
Keep rows A1–A6/B4 as they are. Researcher decisions are needed for X2/X3 (start coverage) and B6 — see the main report. No behaviour was changed for these rows in 5A.1.
