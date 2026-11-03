# D2 — M4 versus v9 Evaluation Profile

**Status:** `PROPOSED — NOT APPROVED`

| Property | v9 `t1_entry_to_t4_clearance` | M4 `first_blocked_to_t4_clearance` |
|---|---|---|
| Boundary | T1 ≤ t < T4 | first blocked tick < t < T4 |
| Required GT | T1 + T4 | T4; replay supplies t_blocked |
| Clock | T1 front + T4 back on accepted common clock | T4 back clock plus replay timeline |
| No blocked step | not applicable | M5 `never_protected`, not M4 zero |
| Front-only | not evaluable | not evaluable |
| Missing/censored/uncertain T4 | not evaluable | not evaluable |

Source: `metrics.py:92-122`, `docs/PREMATURE_OPENING_DECISION_EVIDENCE.md`. Current runner
uses v9 only for historical diagnostics (`experiments/runner.py:131-140`); official profile has
no default and readiness refuses undecided choice. M4 is the proposed researcher preference but
requires decision binding and approved T4 evidence. M4 implementation follow-up would require
system-side t_blocked computation/tests; do not change it now.

**PROPOSED recommendation:** M4, because it avoids requiring T1 while retaining explicit M5;
this remains researcher choice.

**Response:** profile __________; rationale __________; decision-maker/date __________.
