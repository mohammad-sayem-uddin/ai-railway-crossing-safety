# M5 Never-Protected — Separate Safety Outcome (Reporting Definition)

> **PROPOSED — NOT APPROVED — NOT AUTHORIZATION.** The researcher decided M5 is kept as a separate safety outcome.
> This is the written reporting definition; it is not frozen or bound.

> **Revised in Mission 4E.3:** incomplete-replay handling corrected — see `M4_INCOMPLETE_REPLAY_CLASSIFICATION_CORRECTION_20261101_M4E3.md`. Superseded text is marked.

## Definition (matches `m4_premature_opening`, metrics.py:116-117)

For a train-cohort event with an observable, approved `T4` and a valid replay:

`never_protected = True` iff there is **no retained replay step with `is_passage_blocked=True` and `timestamp_s < T4`**.
(A first blocked step at exactly `T4` or after `T4` also counts as never protected.)

## Rules

| ID | Rule |
|---|---|
| M5-R1 | M5 is its own outcome. It is **excluded from the M4 denominator and numerator** and never counted as "not premature". |
| M5-R2 | M5 is evaluable only when T4 is usable **and the replay reaches T4** (`t_last ≥ T4`). If T4 is missing/censored/uncertain, or the replay is empty or ends before T4 with no blocked step observed, `never_protected=None` (reasons `replay_empty` / `replay_ended_before_T4`) — M5 is **not asserted** for an unobserved tail. *(Current code asserts M5 in the last two cases; corrected here in 4E.3.)* |
| M5-R3 | M5 denominator = train events with `never_protected is not None` (`never_protected_evaluable_count`). It is **larger than or equal to** the M4 denominator (M4 evaluable ⊂ M5 evaluable). The partition holds: `M5_evaluable = M4_evaluable + never_protected_count` (test `test_m5_is_reported_separately`). |
| M5-R4 | Engine and no-train events never enter M5. |
| M5-R5 | M5 is replay-relative. A back-only replay yields "never protected by that replay's sensing"; do not describe it as a dual-camera system miss unless the replay was a validated fused timeline (see M4 contract §3). |
| M5-R6 | M5 is not the same as `missed_train` (which tests the barrier state at T1 within ±0.25 s and needs T1). Never merge them. |
| M5-R7 | No rate or CI is defined by the current code for M5; only `never_protected_evaluable_count` and `never_protected_count` exist. Any M5 proportion/CI would be a new, unapproved reporting choice. |

## Report fields (existing → `CohortEvaluationSummary.to_dict()`)

`never_protected_evaluable_count`, `never_protected_count`, plus per-event reason strings under `exclusions["premature_opening"]`
(prefix `never_protected_before_T4 (M5)`).

## Not claimed

No M5 value exists for any real event. No approval of M5 handling in the repository.
