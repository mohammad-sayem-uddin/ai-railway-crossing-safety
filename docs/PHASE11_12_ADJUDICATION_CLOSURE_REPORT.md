# Phase 11.12 — Adjudication Closure and Evaluation-Readiness Gate: Report

**Status:** READINESS-GATE ENGINEERING IMPLEMENTED; research closure and approval NOT COMPLETE.
**Original date:** 2026-10-15. **Status corrected:** 2026-10-16.

---

## 1. Summary

The readiness-gate implementation is present and its synthetic-only tests pass. The default gate output is NOT_READY. This verifies code behavior only, not the completion of researcher adjudication, policy closure, or valid ground truth. No ground truth has been approved. No evaluation stage has been named. EVAL-AUTH has not been granted. The Phase 11.10 closure package was missing when this report was written; it is **now present** at `docs/PHASE11_10_DECISION_CLOSURE_PACKAGE.md` as of 2026-10-16 (see `docs/PHASE11_10_RECONCILIATION.md`, additive update). That deliverable gap is closed; the approval and research-closure statements in this report are unaffected and still stand.

## 2. Gate Implementation

**File:** `src/railway_detection/annotation/evaluation_readiness_gate.py`

**API:** `evaluate_readiness(*, records or reviews_dir, allowlist_path, active_proposal_sha256_by_event, media_sha256_registry, media_file_paths, required_cohorts, stage) -> ReadinessVerdict`

**Conditions (ALL must hold for READY):**
1. ≥1 APPROVED Stage-2.1 record per required cohort.
2. All records pass full schema validation.
3. All APPROVED records pass `validate_for_promotion` with real media.
4. No DISPUTED or NEEDS_SECOND_REVIEW records in scope.
5. Allowlist loads successfully.
6. No legacy (non-8.1.0-stage2.1) records present.

**Safety properties:**
- No override flag. No env-var bypass. No "force" parameter.
- Gate recomputes from records; never trusts caller claims.
- Default is NOT_READY.

## 3. Test Results

```text
$ PYTHONPATH=src .venv/bin/python -m pytest tests/test_phase11_12_readiness_gate.py -q
12 passed
```

| Test | Verdict |
|---|---|
| Empty reviews dir | NOT_READY ✅ |
| Valid synthetic reviews directory | READY ✅ |
| Missing allowlist | NOT_READY ✅ |
| DISPUTED record | NOT_READY ✅ |
| Legacy records present | NOT_READY ✅ |
| Missing cohort | NOT_READY ✅ |
| Media tampered | NOT_READY ✅ |
| Fully valid synthetic | READY ✅ |
| Duplicate approved event | NOT_READY ✅ |
| Unauthorized reviewer | NOT_READY ✅ |
| Deleted history entry | NOT_READY ✅ |

## 4. Current Repository State

The gate, run against the actual repository, would return **NOT_READY** because:
- Zero Stage-2.1 records exist (all 27 are legacy `schema_version: "6.0.0"`).
- No ADJ-AUTH has been granted.
- No adjudication has occurred.

This is the correct and expected state.

## 5. Blocked Operations

| Operation | Blocker |
|---|---|
| Adjudication (Phase 11.11 Unit 5) | ADJ-AUTH not granted |
| Legacy disposition (LEG-EXEC) | Researcher decision pending |
| Evaluation (Phase 12) | EVAL-AUTH not granted; no approved ground truth |
| Gate READY verdict | Requires approved Stage-2.1 records |

## 6. Integrity

- No legacy records modified.
- No frozen artifacts modified.
- No genuine ground truth approval is evidenced by the synthetic test fixtures.
- 27 legacy review files remain unchanged; no invalidation or promotion was performed.
- Prior worktree inventory and attribution text are historical and not an exhaustive current diff report.