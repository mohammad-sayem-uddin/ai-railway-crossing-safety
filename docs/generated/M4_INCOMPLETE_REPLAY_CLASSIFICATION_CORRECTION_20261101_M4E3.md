# M4 / M5 — Corrected Incomplete-Replay Classification

> **PROPOSED — NOT APPROVED — NOT AUTHORIZATION.** Corrects the *proposed* contract written in Mission 4E.2.
> `src/railway_detection/evaluation/metrics.py` is **unchanged**; the corrected rule is exercised only by a test-local reference
> (`tests/unit/test_mission4e2_m4_occupancy_contract.py`, Part 3). Nothing here modifies an evaluator or readiness gate.

## 1. What was wrong

4E.2 recorded the incomplete-replay case as a gap (G-M4-02) and proposed rule M4-V6 as a single sentence
("replay should reach T4, else M4-not-evaluable"). That was **incomplete and in one respect wrong**:

| 4E.2 statement | Problem |
|---|---|
| Replay ending before T4 with no violation is "silently not premature" in the current code | True of current code, but 4E.2 proposed only "not evaluable" and said nothing about the other branches. |
| (silent) | **Current code also labels a short replay with *no blocked step* as M5 `never_protected=True`** (`t_blocked is None → (None, True)`), and an **empty replay** as M5 — asserting "never protected" about a tail the replay never observed. 4E.2 missed this. Both are now pinned by tests. |
| (silent) | A **violation already witnessed** before the replay ends is a definite premature opening regardless of what follows; it should not be discarded as "incomplete". |

Direction of the current-code error (safety-relevant): an incomplete replay *without* a witnessed violation inflates the M4
**denominator** with a clean "not premature" (**understating** the premature-opening rate) and inflates the M5 **count** with an unobserved
tail (**overstating** never-protected).

## 2. Definitions

- `t_last` = timestamp of the last retained replay step. `covered ⇔ t_last ≥ T4`. **No tolerance is introduced**; a tolerance for sampling granularity, if wanted, is a researcher parameter (open).
- `t_blocked` = timestamp of the first retained step with `is_passage_blocked=True` (unchanged).
- Interval `(t_blocked, T4)` is open at both ends (unchanged).
- A **witnessed violation** is a retained step in `(t_blocked, T4)` that is unblocked or in `OPENING`/`OPEN`.

## 3. Corrected classification (T4 observable and approved; train cohort; valid timestamps)

| # | Replay state | Class | `premature` | `never_protected` | Reason |
|---|---|---|---|---|---|
| 1 | no retained steps | NOT_EVALUABLE | None | **None** | `replay_empty` |
| 2 | blocked step before T4, **violation witnessed** (any coverage) | EVALUABLE | **True** | False | — (record `replay_complete`) |
| 3 | blocked step before T4, no violation, **covered** | EVALUABLE | False | False | — |
| 4 | blocked step before T4, no violation, **not covered** | NOT_EVALUABLE | None | **None** | `replay_ended_before_T4` |
| 5 | **no** blocked step before T4, **covered** | M5 | None | **True** | — (excluded from M4 denominator) |
| 6 | **no** blocked step, **not covered** | NOT_EVALUABLE | None | **None** | `replay_ended_before_T4` — **M5 is not asserted** |

Why row 2 is safe: if a violation lies in the observed part of `(t_blocked, T4)` it lies in the full interval (monotone). Why rows 4 and 6
are not "clean": the unobserved tail `(t_last, T4)` could still contain a violation (row 4) or the first block (row 6).

For covered replays the corrected rule is **identical** to the existing function. This is checked exhaustively for all blocked/unblocked patterns of length 1–6 against a grid of T4 values
(`test_covered_replays_match_existing_code_exhaustively`, > 200 cases).

## 4. Rules (replace 4E.2's M4-V6)

| ID | Rule |
|---|---|
| M4-V6′ | Classify by the table in §3. `covered` is evaluated against the **approved T4 on the replay's own timeline** (back clock or accepted fused timeline). |
| M4-V7 | Rows 1, 4, 6 are excluded from the M4 denominator **and** from the M5 denominator, and listed with their reason. They are **not** M5. |
| M4-V8 | The partition identity holds unchanged: `M5-evaluable = M4-evaluable + never_protected_count` (test `test_incomplete_cases_never_enter_either_denominator`). |
| M4-V9 | Row 2 events with `replay_complete=False` are reported with the flag and counted in `premature_opening_count`; the report also prints how many premature events were witnessed on incomplete replays. |
| M4-V10 | Replay completeness is a property of the **replay**, not of ground truth; it must not be fixed by extending, interpolating or padding the replay after seeing T4. |
| M4-V11 | A step-spacing check for sparse retained steps (the "vacuous empty interval", G-M4-04) is a **separate** open item; this correction does not address it. |

## 5. Documents updated to match (4E.2 proposals, in place)

`M4_SAFETY_METRIC_CONTRACT_…M4E2.md` (M4-V6 superseded), `M5_NEVER_PROTECTED_REPORTING_DEFINITION_…M4E2.md` (M5-R2), `REPORTING_SPECIFICATIONS_…M4E2.md` (reason table),
`EVIDENCE_SCHEMA_GAP_REGISTER_…M4E2.md` (G-M4-02 reworded; G-M4-10/11 added).

## 6. Not done

No code change to `metrics.py`, `clock_aware.py`, `replay_producer.py` or any gate. Implementing this correction in the evaluator would be a separate, approved change.
