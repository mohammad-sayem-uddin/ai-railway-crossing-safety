# GOV-D2: Evaluation Profile Recommendation

**Date:** 2026-11-01  
**Mission:** 4E — Researcher Decision Finalization  
**Status:** RECOMMENDATION ONLY — NOT APPROVED  
**Decision identifier:** `GOV-D2-EVALUATION-PROFILE`  
**Approval field:** ______________________________

## Implemented Alternatives

### Profile A — v9: `t1_entry_to_t4_clearance`

| Property | Value |
|---|---|
| Measurement start | T1 (danger-zone entry, front camera) |
| Measurement end | T4 (tail clearance, back camera) |
| Required GT | Approved T1 + T4 |
| Clock requirement | T1 front + T4 back on accepted common clock |
| No blocked step | Not applicable (v9 measures occupancy interval) |
| Front-only events | Not evaluable |
| Missing/censored T4 | Not evaluable |
| Implementation | `simulation/runner.py` lines 244-252 |

### Profile B — M4: `first_blocked_to_t4_clearance`

| Property | Value |
|---|---|
| Measurement start | First replay step where barrier is blocked (t_blocked) |
| Measurement end | T4 (tail clearance, back camera) |
| Required GT | Approved T4 only; t_blocked from replay |
| Clock requirement | T4 back clock + replay timeline |
| No blocked step | M5 `never_protected` outcome (not M4 zero) |
| Front-only events | Not evaluable |
| Missing/censored T4 | Not evaluable |
| Implementation | `metrics.py` lines 105-122 |

## Key Differences

| Aspect | v9 | M4 |
|---|---|---|
| Requires T1 | Yes | No |
| Requires T4 | Yes | Yes |
| Cross-camera | Yes (T1 front, T4 back) | No (T4 back + replay) |
| R04 dependency | Higher (needs front+back alignment) | Lower (back clock + replay only) |
| Measures | Occupancy interval | Protection interval |
| T1 censoring impact | Blocks evaluation | No impact |
| Never-blocked case | N/A | M5 separate outcome |

## Interaction with Current Dataset

- 20/23 train events are left-censored at T0.
- T1 is observable in most events but has ambiguity issues (Phase 11.5 findings).
- T4 is observable in 22/23 events.
- v9 requires both T1 AND T4 → more events excluded.
- M4 requires only T4 → fewer events excluded.

## Interaction with R04

- v9 requires front+back clock alignment (T1 on front, T4 on back).
- M4 uses only back clock + replay timeline (less R04-dependent).
- If R04 scope is restricted, M4 remains evaluable for more events.

## Unimplemented Options

- `t0_first_visible_to_t4_clearance`: Listed but NOT implemented. All 23 train events are left-censored at T0, making this almost never evaluable.
- `dual_report`: Mentioned in historical descriptions but NOT implemented in current evaluator.

## Recommendation

**Option B — M4 (`first_blocked_to_t4_clearance`)**

**Confidence:** MEDIUM

**Rationale:**
1. M4 avoids requiring T1, which has documented ambiguity issues.
2. M4 is less dependent on R04 cross-camera alignment.
3. M4 handles the never-blocked case explicitly (M5) rather than silently.
4. M4 aligns with the safety question: "was the barrier protecting the crossing?"
5. Fewer events are excluded due to missing/censored boundaries.
6. The v9 profile remains available for historical diagnostics.

**Caveat:** M4 requires system-side t_blocked computation from replay, which depends on the gate model producing blocked steps. If the gate never blocks (e.g., B0 front-only), M4 yields M5 `never_protected` rather than a premature-opening measurement.

**This recommendation is NOT an approval.**

## Researcher Response

**Chosen profile:** ______________________________  
**Rationale:** ______________________________  
**Decision-maker:** ______________________________  
**Date (UTC):** ______________________________