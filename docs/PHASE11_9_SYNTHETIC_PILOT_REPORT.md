# Phase 11.9 — Synthetic Pilot and Workflow Audit: Report

**Status:** COMPLETE.
**Date:** 2026-10-15.
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`.

---

## 1. Objective

Exercise the complete Phase 11.8 workflow end-to-end with synthetic records and synthetic media, before any real event is reviewed. Purpose: find workflow defects, measure usability, collect session-duration observations that will inform the researcher's D1 decision, and verify append-only history, media integrity, reviewer attribution, and recovery behavior — without creating a single real adjudication record.

---

## 2. Pilot Configuration

- **Synthetic events:** 3 (train_events, no_train_events, engine_events).
- **Reviewer:** `pilot.reviewer@synthetic.example.com` (synthetic, not in real allowlist).
- **Media:** Deterministic synthetic files (content = `SYNTHETIC_{FRONT|BACK}_{event_id}_seed42` × 100).
- **Session duration:** 600s (synthetic).
- **All fixtures in `tmp_path`:** No production paths touched.

---

## 3. Happy-Path Results (Unit 2)

| Event | Cohort | Schema Valid | Dry-Run Promotion | Reviewer Attribution |
|---|---|---|---|---|
| synthetic_pilot_event_001 | train_events | ✅ | 0 violations | ✅ pilot.reviewer |
| synthetic_pilot_event_002 | no_train_events | ✅ | 0 violations | ✅ pilot.reviewer |
| synthetic_pilot_event_003 | engine_events | ✅ | 0 violations | ✅ pilot.reviewer |

**3/3 synthetic records pass dry-run promotion with zero violations.**

---

## 4. Failure-Mode Results (Unit 3)

| Induced Failure | Expected Rejection | Actual Result |
|---|---|---|
| Media swapped after hashing | MEDIA_HASH violation | ✅ Detected |
| Unauthorized reviewer | ReviewerNotAuthorizedError | ✅ Rejected before assembly |
| Sub-30s session | SchemaValidationError | ✅ Rejected |
| Tampered media at promotion | PromotionRejected | ✅ No file written |
| Valid record promotion | File written | ✅ Exactly one file |

**All induced failures are correctly rejected. No partial artifacts survive.**

---

## 5. Duration Observations (D1 Pilot Evidence)

**IMPORTANT:** These are synthetic pilot timing observations for the record-construction helper, NOT ground-truth review durations. They measure API call latency, not human review time.

| Event | Wall-clock (s) | Schema Duration (s) |
|---|---|---|
| synthetic_pilot_event_001 | <0.01 | 600.0 |
| synthetic_pilot_event_002 | <0.01 | 600.0 |
| synthetic_pilot_event_003 | <0.01 | 600.0 |

**Note for D1:** The schema enforces a 30.0s minimum floor. Actual human review durations will be measured during Phase 11.11 adjudication. This pilot confirms the tooling does not add measurable overhead to the review process.

---

## 6. Defect Register

| # | Severity | Description | Status |
|---|---|---|---|
| — | — | No defects found | — |

The workflow operated correctly for all tested scenarios.

---

## 7. Integrity Verification

- **Legacy records:** `find data/ground_truth/reviews -name '*.json' | wc -l` = **27** (unchanged).
- **No pilot artifacts outside tmp_path:** Verified by test.
- **Append-only history:** Schema enforces chronological, non-empty `adjudication_history`.
- **Reviewer attribution:** All pilot records carry the synthetic reviewer ID; no blocklisted or empty IDs.

---

## 8. Test Results

```
$ .venv/bin/python -m pytest tests/test_phase11_9_synthetic_pilot.py -v
13 passed in 0.58s
```

---

## 9. Readiness Statement for Phase 11.11

The Phase 11.8 workflow (record construction → schema validation → dry-run promotion) is **operationally ready** for researcher-led adjudication:

1. The helper correctly computes live media hashes.
2. Unauthorized reviewers are rejected before any record assembly.
3. Schema validation catches all structural defects.
4. Dry-run promotion correctly identifies valid and invalid records.
5. No partial artifacts survive failed operations.

**Remaining prerequisites for Phase 11.11:**
- Researcher ADJ-AUTH authorization (naming scope).
- D1/D3 decisions (or explicit deferral with interim floor documented).
- Legacy disposition decision (LEG-EXEC or decline).

---

## 10. Files Created

| File | Purpose |
|---|---|
| `tests/test_phase11_9_synthetic_pilot.py` | Pilot test suite (13 tests) |
| `docs/PHASE11_9_SYNTHETIC_PILOT_REPORT.md` | This report |