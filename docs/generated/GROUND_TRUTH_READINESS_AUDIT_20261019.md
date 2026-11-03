# Ground-Truth Readiness Audit (read-only)

Generated from repository files only; nothing was written to evidence trees.

## Summary
- Review records: **27**; schema versions: {'6.0.0': 27}
- Valid Stage-2.1 records: **0**
- Promotion-eligible (pending live media re-hash): **0**
- Bare event ids shared across cohorts: ['event_001', 'event_002', 'event_003']
- Duplicate cohort/event identities: none

## Reviewer allowlist
- Loaded: True (entries: ['raihankabirrahu@gmail.com'])
- Records with blocklisted reviewer id: 27
- Records with reviewer not on allowlist: 27

## Legacy records
- 27 legacy-shaped records; 27 reference a superseded proposal
- Shared review timestamps: {'2026-10-12T16:51:21Z': 27}

## Cohort requirements
| Cohort | Records | Stage-2.1 | Eligible | Missing |
|---|---:|---:|---:|---|
| train_events | 23 | 0 | 0 | at least one approved, valid Stage-2.1 record with an allowlisted reviewer |
| no_train_events | 3 | 0 | 0 | at least one approved, valid Stage-2.1 record with an allowlisted reviewer |
| engine_events | 1 | 0 | 0 | at least one approved, valid Stage-2.1 record with an allowlisted reviewer |

## Promotion receipt
- Status: **absent_or_invalid** (STAGE21_PROMOTION_RECEIPT_MISSING: /Users/sayemuddin/Desktop/Train_automation/data/governance/stage21_promotion_receipt.json)

## LEG-EXEC preflight (verification only)
- Execution authorized: **True** — recorded unsigned researcher statement bound to the pinned hash, the 27 sources and the 28 outputs (record d4002a0a1367…)
- Pinned proposal hash: `41cbbba3e9d587b9972c3baca1b39f09d478d408d9c60fd538c249c4600113d4`; matches file: True
- Inputs verified: True; planned sources/outputs: 27/28 (expected 27/28); writes performed: 0

## Notes
- Eligibility is metadata-only: live media re-hashing (Decision 4) is performed only by the readiness CLI, never here.
- No record is promoted, invalidated, approved or migrated by this audit.
