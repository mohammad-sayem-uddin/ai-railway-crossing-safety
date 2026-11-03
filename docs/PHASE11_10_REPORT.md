# Phase 11.10 — Researcher Decisions and Protocol Closure: Report

**Status:** Deliverable now present; researcher-owned items still open.
**Date:** 2026-10-15; deliverable reconciled 2026-10-16.

> **Correction (2026-10-16):** This report originally claimed
> `docs/PHASE11_10_DECISION_CLOSURE_PACKAGE.md` had been created when it had not.
> That claim was inaccurate and the correction stands as a record of the error.
>
> **Second update (2026-10-16, same day):** the closure package has since been
> written and is now present at `docs/PHASE11_10_DECISION_CLOSURE_PACKAGE.md`.
> The deliverable gap is closed. Neither correction closes or decides any
> researcher-owned item: D1's numeric values and D3(c)'s audit mechanism remain
> `PENDING_RESEARCHER_DECISION`, and LEG-EXEC remains unauthorized.

---

## 1. Summary

Phase 11.10 is a documentation + read-only analysis phase. It invents nothing. Its deliverable is a decision register update the researcher can act on.

## 2. Deliverables

| Artifact | Path | Status |
|---|---|---|
| Decision closure package | `docs/PHASE11_10_DECISION_CLOSURE_PACKAGE.md` | ✅ Present as of 2026-10-16; decides nothing |
| This report | `docs/PHASE11_10_REPORT.md` | ✅ Created |
| Absence tests | `tests/test_phase11_3_pending_decisions_not_defaulted.py` | ✅ 9 passed |

## 3. Key Findings

1. **6 PENDING_RESEARCHER_DECISION items** remain (D1, D3(a), D3(c), LEG-EXEC, DISC-1, ADJ-AUTH).
2. **2 decisions are IMPLEMENTED** (D2, D4 — Phase 11.7).
3. **DISC-1 factual check:** The 27 review JSON files currently present carry `schema_version: "6.0.0"`. This verifies the on-disk value but does not prove that every historical `"7.0.0"` statement referred to a protocol-document version. **Resolved 2026-10-16:** the document-by-document correction now exists — see `docs/PHASE11_10_DECISION_CLOSURE_PACKAGE.md` §3.1, which cites all 9 affected statements with file and line, and §3.2, which re-verifies that rejection behaviour is unaffected (27/27 `LEGACY_OR_UNKNOWN_SCHEMA`).
4. **No code defaults exist.** All absence tests pass.
5. **Phase 11.9 pilot evidence** is available for D1 timing context (synthetic, not human).

## 4. Verification Commands

```bash
# Absence tests
.venv/bin/python -m pytest tests/test_phase11_3_pending_decisions_not_defaulted.py -q
# Result: 9 passed

# PENDING count
grep -c 'PENDING_RESEARCHER_DECISION\|PENDING' docs/PHASE11_3_RESEARCHER_DECISIONS.md
# Result: 8

# Legacy schema versions
python3 -c "
import json; from pathlib import Path
versions = set()
for f in Path('data/ground_truth/reviews').rglob('*.json'):
    versions.add(json.loads(f.read_text()).get('schema_version'))
print(versions)
"
# Result: {'6.0.0'}
```

## 5. Integrity

- No legacy records modified.
- No frozen artifacts modified.
- No code changes in this phase.
- Git status: only new documentation files.

## 6. Next Steps for Researcher

See `docs/PHASE11_10_RECONCILIATION.md` for verified findings and the remaining researcher decision path. D1 numeric thresholds, D3(c) audit mechanism/frequency, legacy disposition execution, and genuine adjudication authorization must not be inferred from synthetic engineering tests.