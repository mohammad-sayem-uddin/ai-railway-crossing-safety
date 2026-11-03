# Phase 11.10 — Researcher Decision Closure Package

**Status:** `IMPLEMENTED_AND_TESTED` for the engineering; two decisions remain
`BLOCKED_ON_EXPLICIT_RESEARCH_DECISION`.

**Date:** 2026-10-16
**Git HEAD at authoring:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
**Authority:** This document **selects nothing**. It presents evidence and the
exact action required of the researcher. No `Selected option` field in
`docs/PHASE11_3_RESEARCHER_DECISIONS.md` was changed by this phase, and no
numeric threshold, trigger rule, or audit frequency was introduced into `src/`.

> **Supersession note.** This file is the deliverable that
> `docs/PHASE11_10_REPORT.md` (correction dated 2026-10-16) and
> `docs/PHASE11_10_RECONCILIATION.md` recorded as **absent**. Those documents
> were correct at the time they were written. This package now exists; the
> earlier reports' statements about its absence describe the state before
> 2026-10-16 and should be read as historical, not current.

---

## 1. Evidence classification

Each claim below carries one of these labels, used strictly:

| Label | Meaning |
|---|---|
| **VERIFIED-REAL** | Re-derived from actual repository artifacts in this phase |
| **SYNTHETIC-ONLY** | Holds for deterministic synthetic fixtures; no real-corpus equivalent exists |
| **MISSING-EXTERNAL** | Requires evidence that software cannot generate (human review, field work) |
| **UNRESOLVED-DECISION** | Awaits a researcher choice that no model may make |

---

## 2. Decision inventory

`PENDING_RESEARCHER_DECISION` markers found across `docs/`, `src/`, `tests/`,
and `configs/`: **21**, unchanged before and after this phase.

| ID | Decision | Mechanism | Numeric/parameter value | Status |
|---|---|---|---|---|
| **D1** | Minimum review-session duration | Confirmed 2026-10-14: option **(D)**, band + auto second review | **Not set** — pilot-derived | `BLOCKED_ON_EXPLICIT_RESEARCH_DECISION` |
| **D2** | Reviewer authorization policy | Confirmed 2026-10-14: option **(B)**, mandatory allowlist | n/a | `IMPLEMENTED_AND_TESTED` |
| **D3(a)/(b)** | Disagreement and adjudication rules | Confirmed 2026-10-14: **B+C** trigger, **(A)** no tolerance | n/a | `IMPLEMENTED_NOT_FULLY_VERIFIED` |
| **D3(c)** | Audit of boundaries marked clear | Researcher-added requirement, mechanism unspecified | **Not set** | `BLOCKED_ON_EXPLICIT_RESEARCH_DECISION` |
| **D4** | Media-hash verification | Confirmed 2026-10-14: **(B)+(C)** combined | n/a | `IMPLEMENTED_AND_TESTED` |

### 2.1 D2 — closed since the decision was recorded

The decision entry's "remaining action" said the allowlist artifact did not yet
exist. It now does. **VERIFIED-REAL:**

- `data/ground_truth/authorized_reviewers.json` exists and lists exactly one
  identity, `raihankabirrahu@gmail.com`.
- `promotion_gate.load_authorized_reviewers()` fails closed on a missing file,
  invalid JSON, wrong shape, empty list, blank or duplicate entry, or an entry
  that is itself on `REVIEWER_ID_BLOCKLIST`. It never returns a partial subset.
- `validate_for_promotion()` takes `authorized_reviewers` as a **required
  keyword argument with no default**, so a caller cannot silently skip the
  check. Verified by calling it against all 27 legacy records in this phase.

**Researcher action required:** none for the mechanism. Adding any further
reviewer identity remains a manual, explicit act.

### 2.2 D4 — closed since the decision was recorded

Both "remaining actions" in the decision entry are now implemented.
**VERIFIED-REAL:**

- `ReviewerObservedMediaHashes` is a **required** field on
  `Stage21ReviewRecord`; schema version is `8.1.0-stage2.1`.
- `validate_for_promotion()` performs a live full-file re-hash via
  `compute_media_sha256_pair()` rather than trusting the caller's registry.
- The readiness gate inherits this: tampering with a reviewed media file after
  review produces `MEDIA_HASH_CHANGED_SINCE_REVIEW`
  (`tests/test_phase11_12_readiness_gate.py::test_live_media_tampering_blocks_readiness`).

**Researcher action required:** none.

### 2.3 D1 — mechanism authorized, numbers still blocked

**What is decided:** the mechanism (option D — a "fast but passing" band that
routes borderline-fast sessions to `NEEDS_SECOND_REVIEW`).

**What is not decided:** the hard floor and the band's upper threshold.

**Evidence available — SYNTHETIC-ONLY.** The Phase 11.9 pilot is synthetic. Its
session durations are fixture constants (600 s per session, now staggered
sequentially so one reviewer never holds two simultaneous windows), not
observations of human review. They establish that the schema and gate accept a
plausible session; they are **not** timing evidence and cannot justify a
threshold.

**Evidence missing — MISSING-EXTERNAL.** No genuine Stage-2.1 review has ever
been conducted, so no real `review_duration_s` observation exists. D1's own
"unresolved concerns" note already says this.

**Current code state:** `MIN_PLAUSIBLE_REVIEW_DURATION_S = 30.0` remains the
Phase 11.1 forensic sanity constant in both `stage2_1_schema.py` and
`integrity_safeguard.py`. This phase did not change it and did not add a second
threshold. **No band upper threshold exists anywhere in `src/`** — the mechanism
D1 authorizes is therefore not yet implemented, which is correct: implementing
it requires the number.

**Exact researcher action required:**
1. Run a small pilot of genuine Stage-2.1 reviews (blocked on D-REVIEW below).
2. Record the observed `review_duration_s` values.
3. Write the chosen hard floor and band upper threshold, with rationale, into
   `docs/PHASE11_3_RESEARCHER_DECISIONS.md` Decision 1 as a numbered update.

**Downstream effect either way:** until these numbers exist, the band cannot be
implemented and every genuine review is accepted on the flat 30 s floor alone.

### 2.4 D3 — trigger and tolerance decided; audit mechanism blocked

**Parts (a) and (b) — `IMPLEMENTED_NOT_FULLY_VERIFIED`.** The schema carries
`NEEDS_SECOND_REVIEW` and `DISPUTED`; the readiness gate refuses any record that
is not resolved (`UNRESOLVED_DISAGREEMENT`), and no tolerance constant exists
(part (b)(A) is satisfied by absence, which
`tests/test_phase11_3_pending_decisions_not_defaulted.py` enforces). What is
**not** verified is the B+C *trigger*: no code reads
`docs/PHASE11_6_OPEN_ISSUE_REGISTER.csv` to require second review for the fixed
subset. The states exist and are enforced; the rule that assigns them does not.

**Part (c) — `BLOCKED_ON_EXPLICIT_RESEARCH_DECISION`.** The researcher added a
requirement that every boundary marked clear receive a documented audit, and
explicitly left the mechanism and frequency unspecified. No audit frequency
value exists in `src/` — verified by grep in this phase, and deliberately so.

**Exact researcher action required:** state the audit mechanism (spot-check a
percentage, or a single lightweight pass over every clear boundary) and its
frequency. Both are scientifically consequential and are not inferable from the
repository.

---

## 3. DISC-1 reconciliation — legacy record schema version

**Finding (VERIFIED-REAL, re-derived in this phase):** all 27 records under
`data/ground_truth/reviews/` carry `"schema_version": "6.0.0"` and
`"adjudication_status": "APPROVED"`. Not one carries `"7.0.0"`.

Verification method: every `*.json` under the reviews tree parsed and its
`schema_version` tallied — 27/27 `6.0.0`. The tree was re-hashed immediately
afterwards and is byte-identical.

### 3.1 Documents stating the legacy record field is `7.0.0`

| File | Line | Nature of the statement |
|---|---|---|
| `docs/PHASE11_1_REMEDIATION_PLAN.md` | 27 | Describes existing review records as `schema_version: "7.0.0"` |
| `docs/PHASE11_1_REMEDIATION_PLAN.md` | 90 | Same, as the category to exclude from promotion |
| `docs/PHASE11_1_REMEDIATION_PLAN.md` | 122 | Same, in the no-auto-conversion guarantee |
| `docs/PHASE11_2_STAGE21_IMPLEMENTATION_REPORT.md` | 34 | "every one of the invalidated `7.0.0` records" |
| `docs/PHASE11_2_STAGE21_IMPLEMENTATION_REPORT.md` | 76 | Test description citing a legacy-schema `7.0.0` record |
| `docs/PHASE11_2_STAGE21_IMPLEMENTATION_REPORT.md` | 79 | **Most consequential:** states the 27 are rejected "since all carry `schema_version: "7.0.0"`" |
| `docs/PHASE11_3_RESEARCHER_DECISIONS.md` | 127 | Describes the 27 on-disk records as `7.0.0` |
| `docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md` | 3 | Same, in the disposition preamble |
| `docs/PHASE11_6G_EVALUATION_READINESS_REASSESSMENT.md` | 9 | Same, in the "left untouched" statement |

`docs/PHASE11_7_GOVERNANCE_IMPLEMENTATION_REPORT.md:36` also mentions `7.0.0`,
but as the name of the *rejection pattern* ("the same 'old version is never
valid' pattern that already rejects `7.0.0` records"), not as a claim about the
on-disk field. It is listed here for completeness and needs no correction.

### 3.2 Behavioural impact: none

**VERIFIED-REAL.** The gate rejects on *inequality* with
`STAGE_2_1_SCHEMA_VERSION = "8.1.0-stage2.1"`, not on a match against `7.0.0`.
Re-running `validate_for_promotion()` against all 27 real records in this phase
produced **27/27 `LEGACY_OR_UNKNOWN_SCHEMA`** violations and zero acceptances.
The documents' *conclusion* (these records are ineligible) is correct; only the
cited field value is wrong.

### 3.3 Required correction, and why it was not applied here

Every document in §3.1 is a **historical phase report**. Editing the body of a
completed report would rewrite the evidence record, which §12 of the Phase 11.10
implementation plan prohibits. The correct remedy is an additive annotation in
each, or a single supersession note cited from each. This package is that
single, citable correction: **wherever a Phase 11 document states the legacy
record `schema_version` is `"7.0.0"`, the on-disk value is `"6.0.0"`; the
rejection behaviour those documents describe is unaffected.**

Any hash-pinned disposition citation must use `6.0.0`. **This is a precondition
for LEG-EXEC authorization and is now satisfied on paper.**

---

## 4. Legacy disposition — dry run complete, execution still unauthorized

**Status:** `IMPLEMENTED_AND_TESTED` (tooling); execution
`BLOCKED_ON_EXPLICIT_RESEARCH_DECISION`.

This phase added `plan_invalidation_notices()` — a dry-run planner that runs the
same `validate_proposal_for_application` pre-flight and the same per-record
integrity rechecks as the writer, and **writes nothing**. Its statuses are
prefixed `WOULD_` and are kept disjoint from the applied statuses, so a plan can
never be read as evidence that a notice was written.

**Dry run against the real proposal (VERIFIED-REAL):**

```
proposal: docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json
reviews_root: data/ground_truth/reviews
planned records: 27 → 27 WOULD_WRITE
directory notice: WOULD_WRITE
```

The entire `data/ground_truth/` tree was re-hashed before and after: **byte-identical**.

**Execution was not performed.** The Phase 11.6D authorization rule requires a
statement covering the exact pinned proposal hash, exactly the 27 sources,
exactly the 28 outputs, and the precise write operation. No such statement
exists in the repository or in this phase's instruction. General engineering
authorization is explicitly not authorization to apply a disposition to
irreplaceable evidence, so the gate remains **CLOSED** and `docs/PHASE11_6E`'s
`BLOCKED_NOT_AUTHORIZED` status stands and is confirmed accurate.

**Note on reversibility:** the mechanism is non-destructive by construction — it
writes sibling notices and never modifies, moves, or deletes a review record.
The 27 records would remain byte-identical after execution.

---

## 5. What the 27 legacy records are, and are not

**VERIFIED-REAL, re-confirmed in this phase:**

- 27 records, all `schema_version: "6.0.0"`, all `adjudication_status: "APPROVED"`.
- All 27 rejected by `validate_for_promotion()` with `LEGACY_OR_UNKNOWN_SCHEMA`.
- All 27 flagged by `check_review_batch_integrity()` with **both**
  `APPROVED_WITHOUT_PROVENANCE` and `IDENTICAL_TIMESTAMP_NO_PLAUSIBLE_DURATION`
  (54 violations over 27 records).
- The readiness CLI reports them as 27 `LEGACY_OR_UNKNOWN_SCHEMA` blockers.

**They are not Stage-2.1 ground truth and must not be described as approved,
valid, or promotable.** Their `APPROVED` field is a product of the short-burst
workflow Phase 11.1 identified, not of genuine independent review.

**There are zero genuine Stage-2.1 review records in this repository.**

---

## 6. Remaining blockers that software cannot close

| ID | Blocker | Why no code can close it |
|---|---|---|
| **D-REVIEW** | No genuine Stage-2.1 review record exists | Requires a human to actually review raw media and record boundaries. Fabricating one would be evidence fraud. |
| **D1-NUM** | Hard floor and band upper threshold unset | Requires real timing data from D-REVIEW, then a researcher's judgement. |
| **D3(c)** | Audit mechanism and frequency unspecified | A scientifically consequential choice the researcher explicitly reserved. |
| **D3(a)-TRIGGER** | B+C trigger rule not implemented in code | Implementable, but only once the fixed subset's authority (`PHASE11_6_OPEN_ISSUE_REGISTER.csv`) is confirmed as the binding list. |
| **LEG-EXEC** | Legacy disposition execution unauthorized | Requires the four-part authorization statement. Dry run is complete and clean; nothing else blocks it technically. |

---

## 7. Phase 12 handoff status

**`BLOCKED_ON_EXTERNAL_EVIDENCE`.** Not blocked on engineering.

The readiness gate and its CLI are implemented and tested. Run against the real
corpus they report, correctly:

```
ready: false
blockers: 30
  27  LEGACY_OR_UNKNOWN_SCHEMA
   3  MISSING_COHORT_APPROVAL
exit code: 2
```

This is the **correct and expected** result: there is no approved ground truth,
so readiness must be refused. A READY verdict would indicate a defect, not
progress.

The gate reports `researcher_approval_still_required: true` and
`ground_truth_approval_authority: "human_researcher_only"` on **every** verdict,
including READY. Mechanical validity is never represented as researcher
approval.

---

## 8. Acceptance criteria for this phase

| Criterion (Phase 11.10 plan §9–§10) | Result |
|---|---|
| `test_phase11_3_pending_decisions_not_defaulted.py` passes unchanged (9 tests) | **9 passed** |
| Decision inventory covers 100% of `PENDING` markers | **21 before, 21 after** |
| Every entry states evidence available, evidence missing, blocking status, exact action | §2 |
| DISC-1 memo lists every document with file+line | §3.1, 9 citations + 1 non-defect |
| No new numeric threshold constant in `src/` | **grep: none** |
| No trigger-rule function in `src/` | **none added** |
| No audit-frequency value in `src/` | **none added** |
| `test_no_automated_tie_breaking_function_exists` | **passed** |
| `test_no_numeric_agreement_tolerance_constant_exists` | **passed** |
| `test_no_rule_determines_which_events_require_second_review` | **passed** |
| Legacy records SHA-256 unchanged pre/post | **27/27 byte-identical** |

---

## 9. What this document does not claim

- It does **not** select any pending decision.
- It does **not** claim Phase 11 is `COMPLETE`; two decisions and one external
  evidence blocker remain open.
- It does **not** claim genuine Stage-2.1 ground truth exists. None does.
- It does **not** authorize legacy disposition execution or Phase 12 evaluation.
- It does **not** treat a clean dry run as authorization to write.
