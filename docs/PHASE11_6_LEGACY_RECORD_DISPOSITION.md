# Phase 11.6 — Consolidated Legacy-Record Disposition (Executed)

**Status: EXECUTED — NON-DESTRUCTIVE SIBLING NOTICES ONLY.** This document consolidates and restates the disposition first proposed in `docs/PHASE11_3_RESEARCHER_DECISIONS.md` Section 2, adding the Phase 11.5 evidence thread. The authorized operation created 27 sibling invalidation notices and one directory notice; it did not modify, move, or delete any original record. All 27 files below remain byte-identical to their Phase 11.1 baseline hashes, `schema_version: "7.0.0"`, `adjudication_status: "APPROVED"`, unmodified.

The operation-specific execution authorization was recorded before execution in `data/governance/leg_exec_authorization.json`; its unsigned recorded-statement body hash is `d4002a0a1367e7cd18cfb007eb89c3937583247f77804ff410d650d54a688363`.

---

## 1. Affected records — all 27, individually identified

| # | Cohort | Event | File path | SHA-256 (Phase 11.1 baseline, re-confirmed unchanged through Phase 11.6) |
|---|---|---|---|---|
| 1 | engine_events | event_001 | `data/ground_truth/reviews/engine_events/event_001_review.json` | `3493e125e86c7642d47dca13ddfe3a91fad926b6e6d0fd9e9662968d1bca3edd` |
| 2 | no_train_events | event_001 | `data/ground_truth/reviews/no_train_events/event_001_review.json` | `7387acbf17e6ca2eda6b814e3d9f30683aecffe863b14637cc4ff4bf51015243` |
| 3 | no_train_events | event_002 | `data/ground_truth/reviews/no_train_events/event_002_review.json` | `619efd3ec467f0f23f0b70ef885fd7771fb84dcd052b1175c4c9fca4745ace95` |
| 4 | no_train_events | event_003 | `data/ground_truth/reviews/no_train_events/event_003_review.json` | `8f163c525e32ddf4623718093b2909bcaf1b20b320d8a75985fd7310ee19ce2b` |
| 5 | train_events | event_001 | `data/ground_truth/reviews/train_events/event_001_review.json` | `a0edd4a670e1706391309392661559e93a310d5c9f39d17cf094173cfb5e1cc6` |
| 6 | train_events | event_002 | `data/ground_truth/reviews/train_events/event_002_review.json` | `437e0d2dec08179aa5194633bcca56bb2cb37c464048566fbe09b2745dcaa239` |
| 7 | train_events | event_003 | `data/ground_truth/reviews/train_events/event_003_review.json` | `308d22669e2bee899c3d621c66388e4753e0c0ba5d656a56d497ddf23944ab5b` |
| 8 | train_events | event_004 | `data/ground_truth/reviews/train_events/event_004_review.json` | `d47aabda3fa81f7c530e1603a89f8c5fb26ffe8103edd33ead00bfe7bd237f4d` |
| 9 | train_events | event_005 | `data/ground_truth/reviews/train_events/event_005_review.json` | `d79c5a4b4a3d6e0139ce300e6de4a6d34250fdef1495a69c3c60badc3d829af9` |
| 10 | train_events | event_006 | `data/ground_truth/reviews/train_events/event_006_review.json` | `d7f1d5594d4d1d6d8675e9f97140139d8a400d7081d315832a5b15c6195a6b5e` |
| 11 | train_events | event_007 | `data/ground_truth/reviews/train_events/event_007_review.json` | `ba40869a4abc7d9db8295782a15c5bd2c380f8d9c31afa9bfc3e07dfddb8a536` |
| 12 | train_events | event_008 | `data/ground_truth/reviews/train_events/event_008_review.json` | `d97bcc8d68630d9e886e34577c3622b83f5115c682c0d8dc5edfc5521cbf54cf` |
| 13 | train_events | **event_009** | `data/ground_truth/reviews/train_events/event_009_review.json` | `06660001cfa9299eb5d299b64089413c96df99284171648e0d0e0f43b0dd860e` |
| 14 | train_events | event_010 | `data/ground_truth/reviews/train_events/event_010_review.json` | `f64bbe72f11b17910f3d3cc98d08a7303b77ef37cdf2a2ca9b97509aae6c85b4` |
| 15 | train_events | event_011 | `data/ground_truth/reviews/train_events/event_011_review.json` | `28fcf1f5c8824a42782d964e012552e46e245bce67fb64c72a421276ef6ebb4c` |
| 16 | train_events | event_012 | `data/ground_truth/reviews/train_events/event_012_review.json` | `b369f6863f00212cbc9a988c5d42035fe540f150793f60b058731abeaf69eeba` |
| 17 | train_events | event_013 | `data/ground_truth/reviews/train_events/event_013_review.json` | `8d5dfc1f03b7bc2dd9bbc42199fda6c2935e60c9c1292de19d5df31bab7cce76` |
| 18 | train_events | event_014 | `data/ground_truth/reviews/train_events/event_014_review.json` | `2717a61b0a6d328ab6977aa9320a2c78990d76f4b6887203e675445844ab7d5a` |
| 19 | train_events | **event_015** | `data/ground_truth/reviews/train_events/event_015_review.json` | `9a90a1a6ed1eb77801b1250d2368ee6916508c38c08fb86f951682cf55bd9c8a` |
| 20 | train_events | **event_016** | `data/ground_truth/reviews/train_events/event_016_review.json` | `c25a8e4bb4f9667927a2c2e88d76aa40e09612baffd75a8bb8171ff4381db1af` |
| 21 | train_events | event_017 | `data/ground_truth/reviews/train_events/event_017_review.json` | `f2ee23c67348984283e30f18735d57feb1cedbd822056bfec12a5466eee8d859` |
| 22 | train_events | event_018 | `data/ground_truth/reviews/train_events/event_018_review.json` | `a954c637fc7430ba5fcaf1de98c3407f6f8a9f2cd984f7cb5fadaeef3e60efaf` |
| 23 | train_events | event_019 | `data/ground_truth/reviews/train_events/event_019_review.json` | `278b49f9c241b10189274c19a9634e58a5c8dfc4e45530239d2778f662fe29f2` |
| 24 | train_events | event_020 | `data/ground_truth/reviews/train_events/event_020_review.json` | `b98c257804fd2ba0acb21a10de90c9dc4595fc3a898ce1c41a86beedc3ccf9e9` |
| 25 | train_events | event_021 | `data/ground_truth/reviews/train_events/event_021_review.json` | `c6e689b00b5001191660b4b71c8df43d205b84f1b7d23af066298152d85b563f` |
| 26 | train_events | event_022 | `data/ground_truth/reviews/train_events/event_022_review.json` | `30f0ec6c8f2825a6644bebe3ce8ab97a9352cfeabb8a721da30a235403f134c4` |
| 27 | train_events | event_023 | `data/ground_truth/reviews/train_events/event_023_review.json` | `e19f917c28920161535e9322a984fa35fecd8fba552557a017062b727b3854d6` |

Rows 13, 19, 20 (bold) are the three events with additional, content-level evidence from Phase 11.5 — see Evidence Thread 2 below.

---

## 2. Evidence — two independent threads

### Thread 1 — process integrity (Phase 11.1, applies to all 27 equally)

1. All 27 records share one byte-identical `review_date_utc` (`2026-10-12T16:51:21Z`), with no individually-plausible `review_duration_s` distinguishing separate sessions.
2. Filesystem mtimes independently show all 27 written within a ~5-second span (~0.2s/record) — inconsistent with the claimed frame-by-frame review methodology.
3. All 27 reference a superseded (non-active) proposal version (`stale_reference_count: 27` in `docs/PHASE11_1_INTEGRITY_INVENTORY.json`).
4. No code path anywhere in the repository constructs a review record; the one real approval safeguard that exists checks a different field name than these records use.
5. The Phase 11.2 Stage-2.1 promotion gate, applied read-only to all 27, rejects every one on `LEGACY_OR_UNKNOWN_SCHEMA` grounds alone.

This thread makes no claim about whether the *content* any individual record approved is right or wrong — it establishes that the approval *process* itself could not have occurred as claimed, for all 27 without distinction.

### Thread 2 — content integrity (Phase 11.4/11.5, applies specifically to events 009, 015, 016)

Independent of Thread 1, direct frame-level video inspection (Phase 11.4) followed by the researcher's own personal review and confirmation (Phase 11.5) established that the T0 boundary these three records' underlying candidate proposals claimed — "late arrival, non-left-censored, T0=1.5s" — is factually wrong: the train is visible at frame zero in all three recordings. See `docs/PHASE11_5_ADJUDICATION_REPORT.md` Section 1 and `docs/PHASE11_5_FIELD_ADJUDICATIONS.json` for the full, attributed adjudication record.

This is evidence that even if the process defects in Thread 1 did not exist, at least 3 of these 27 approvals would still need to be revisited on pure content grounds. It does **not** extend to the other 24 records — no content-level review (by researcher or by the Phase 11.4 video audit) has concluded any of them are substantively wrong; the only evidence against the other 24 is Thread 1's process defect, which already independently applies to all 27.

---

## 3. Proposed scope of invalidation — unchanged from Phase 11.3

**Full invalidation of all 27 records, not a partial subset.** Thread 1's process defects (items 1–5 above) apply identically and independently to every one of the 27; there remains no principled basis to invalidate some but not others on process grounds alone. Thread 2 adds *additional* justification for 3 specific records but does not weaken the case for the other 24 — it was never the sole basis for proposing full-scope invalidation in the first place.

---

## 4. Proposed mechanism — unchanged from Phase 11.3

One of the two non-destructive options in `docs/PHASE11_1_REMEDIATION_PLAN.md` Section 2 (a sibling notice file in `reviews/`, or an archive-and-move preserving byte-for-byte content), executed as a structured disposition event via `propose_invalidation()` / `write_invalidation_proposal()` (`src/railway_detection/annotation/promotion_gate.py`, implemented and tested in Phase 11.2 against synthetic fixtures only — never invoked against any of the 27 real records by any phase to date).

## 5. Preservation strategy

- Neither proposed mechanism deletes or overwrites any of the 27 files. Both are additive (a sibling notice) or content-preserving (archive-and-move retains the original bytes under a new path).
- Original candidate proposals (`data/ground_truth/proposals/`) are never touched by this disposition regardless of which mechanism or scope is chosen — invalidation concerns only the *review* records, not the proposals they reviewed.
- `docs/PHASE11_1_INTEGRITY_INVENTORY.json`, `docs/PHASE11_4_FINAL_VIDEO_ANNOTATION_AUDIT.csv`, `docs/PHASE11_5_ADJUDICATION_LEDGER.csv`, and `docs/PHASE11_5_FIELD_ADJUDICATIONS.json` remain the historical evidentiary record regardless of execution status and are not altered by this document.

## 6. Authorization

**Authorized decision-maker:** `raihankabirrahu@gmail.com` (documented attestation per the researcher's explicit instruction, 2026-10-14; this repository has no authentication system, so this is not a verified credential — same caveat stated throughout Phases 11.2–11.6).
**Date of authorization (of scope and mechanism, NOT of execution — see below):** 2026-10-14
**Scope confirmed by researcher:** Full invalidation, all 27 records — matches Section 3's proposed scope, no narrowing requested.
**Mechanism selected by researcher:** Sibling invalidation notices, originals preserved in place (NOT archive-and-move).

The 2026-10-14 scope/mechanism authorization above was distinct from execution authorization. On 2026-10-17, the researcher gave a separate, operation-specific execution statement naming the pinned proposal, exactly 27 source records, exactly 28 outputs, preservation of originals, and fail-closed preconditions. The verbatim statement is stored in `data/governance/leg_exec_authorization.json` and carried into the generated operation report.

**Reviewed-proposal binding (Phase 11.6C, Finding F2 closure):** the raw-byte SHA-256 of `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json`, exactly as reviewed and authorized above, is:

```
41cbbba3e9d587b9972c3baca1b39f09d478d408d9c60fd538c249c4600113d4
```

Any real-execution preflight script MUST call `load_and_verify_proposal(proposal_path, expected_sha256="41cbbba3e9d587b9972c3baca1b39f09d478d408d9c60fd538c249c4600113d4")` (`src/railway_detection/annotation/invalidation_notice_writer.py`) before doing anything else, and must abort if it raises `ProposalBindingError` -- this proves the file being applied is byte-for-byte the one the researcher reviewed, not a changed, regenerated, or substituted one. **This hash check is proof of file-content integrity only, not of human authorization** -- authorization is the scope/mechanism/decision-maker/date fields above, which this hash does not itself attest to.

## 7. Execution status

**EXECUTED SUCCESSFULLY** at `2026-10-17T07:44:53Z` by the existing fail-closed command:

```text
PYTHONPATH=/Users/sayemuddin/Desktop/Train_automation/src \
  python3 scripts/run_leg_exec.py execute \
  --report docs/generated/LEG_EXEC_OPERATION_REPORT.json
```

The live preflight verified the raw-byte proposal hash `41cbbba3e9d587b9972c3baca1b39f09d478d408d9c60fd538c249c4600113d4`, 27/27 source hashes, the exact source inventory, and the exact 28-output inventory before writing. The operation report records **27 sibling notices written + 1 directory notice written = 28/28**, zero failures, zero missing outputs, zero invalid notices, `ground_truth_created: false`, and `originals_byte_identical: true`. A subsequent execution rerun was idempotent: all 27 record notices and the directory notice were `SKIPPED_ALREADY_DONE_MATCHING`, with no tree changes.

The complete machine-readable result, including source and output hashes and per-target statuses, is `docs/generated/LEG_EXEC_OPERATION_REPORT.json`. The pre-existing `data/ground_truth/reviews/PHASE2_VERIFICATION_REPORT.md` was not an operation target and was not changed.
