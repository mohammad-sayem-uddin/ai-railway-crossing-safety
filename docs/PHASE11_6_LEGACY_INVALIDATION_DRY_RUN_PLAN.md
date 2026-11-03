# Legacy Invalidation — Dry-Run Plan (Not Executed)

**Status: DRY RUN ONLY. NOTHING UNDER `data/ground_truth/reviews/` HAS BEEN CREATED, MOVED, OR MODIFIED.** This document shows exactly what would be written, and where, if the researcher separately and explicitly authorizes execution after reviewing this plan. Per the researcher's own instruction (2026-10-14): *"Do not execute invalidation or change the real records until I explicitly authorize execution after reviewing the dry-run plan."*

The structured, code-generated, read-only-against-real-files backing for this plan is `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json` (27 entries, produced via the existing, tested `propose_invalidation()`/`write_invalidation_proposal()` functions in `src/railway_detection/annotation/promotion_gate.py`, which read each real record only to capture its current SHA-256 and never write to it). Re-verified immediately after generation: all 27 real review records remain byte-identical to the Phase 11.1 baseline.

---

## 1. Decisions this plan implements

Per the researcher's explicit instruction (2026-10-14, `raihankabirrahu@gmail.com`):
- **Scope:** full invalidation, all 27 legacy review records (23 `train_events`, 3 `no_train_events`, 1 `engine_events`).
- **Mechanism:** sibling invalidation notices — one small new JSON file placed next to each original `*_review.json`, plus one directory-level summary notice. **Original files are preserved in place, byte-for-byte, never moved or edited.**

This supersedes the "archive-and-move" alternative that was also on the table in `docs/PHASE11_3_RESEARCHER_DECISIONS.md` / `docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md` — the researcher selected the notice-only approach, not the move approach.

---

## 2. What would be created if executed — 28 new files, 0 modified, 0 moved, 0 deleted

### 2.1 One directory-level summary notice

**Target path:** `data/ground_truth/reviews/_INTEGRITY_NOTICE.md` (new file, sibling to the cohort subdirectories)

**Exact content that would be written:**

```markdown
# INTEGRITY NOTICE — all records in this directory

Every review record in this directory (23 train_events, 3 no_train_events, 1
engine_events — 27 total) is marked INVALIDATED as of 2026-10-14, per the
researcher's explicit authorization. See the sibling
`<event>_review.INVALIDATION_NOTICE.json` file next to each record for the
specific evidence and disposition for that record, and
docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md for the full consolidated case.

These records must not be treated as evidence of genuine human review until
superseded by a real Stage-2.1 record (src/railway_detection/annotation/stage2_1_schema.py).

No file in this directory has been deleted or edited. Original content is
preserved byte-for-byte.
```

### 2.2 Twenty-seven per-record sibling notices

**Target path pattern:** `data/ground_truth/reviews/{cohort}/{event}_review.INVALIDATION_NOTICE.json` — one new file next to each existing `{event}_review.json`, same directory, never overwriting or renaming the original.

**Content template (every field except the four marked `<event-specific>` is identical across all 27):**

```json
{
  "notice_type": "LEGACY_REVIEW_INVALIDATION_NOTICE",
  "applies_to_file": "<event-specific: affected_record_path>",
  "applies_to_file_sha256_at_notice_time": "<event-specific: affected_record_sha256>",
  "disposition": "INVALIDATED",
  "proposed_by": "raihankabirrahu@gmail.com",
  "proposed_at_utc": "2026-10-14T20:00:00Z",
  "reason": "<event-specific: Thread 1 always; Thread 1 + Thread 2 for event_009/015/016 only>",
  "note": "This notice does not modify, move, or delete the file it describes. See docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md for full evidence and docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json for the complete, tamper-evident proposal log."
}
```

**Two fully worked examples** (full `reason` text as it would actually appear, taken verbatim from the generated proposal log):

<details><summary><strong>Example A — a Thread-1-only record: <code>train_events/event_001_review.INVALIDATION_NOTICE.json</code></strong></summary>

```json
{
  "notice_type": "LEGACY_REVIEW_INVALIDATION_NOTICE",
  "applies_to_file": "data/ground_truth/reviews/train_events/event_001_review.json",
  "applies_to_file_sha256_at_notice_time": "a0edd4a670e1706391309392661559e93a310d5c9f39d17cf094173cfb5e1cc6",
  "disposition": "INVALIDATED",
  "proposed_by": "raihankabirrahu@gmail.com",
  "proposed_at_utc": "2026-10-14T20:00:00Z",
  "reason": "THREAD 1 (process integrity, Phase 11.1, applies to all 27 equally): identical review_date_utc (2026-10-12T16:51:21Z) shared across all 27 records; filesystem mtimes showing a ~5-second write burst (~0.2s/record), inconsistent with the claimed frame-by-frame review methodology; all 27 reference a superseded (non-active) proposal version; no code path anywhere in the repository constructs a review record; the Phase 11.2 Stage-2.1 promotion gate rejects all 27 on LEGACY_OR_UNKNOWN_SCHEMA grounds alone. See docs/PHASE11_1_ANNOTATION_INTEGRITY_AUDIT.md.",
  "note": "This notice does not modify, move, or delete the file it describes."
}
```
</details>

<details><summary><strong>Example B — a Thread-1 + Thread-2 record: <code>train_events/event_009_review.INVALIDATION_NOTICE.json</code></strong></summary>

```json
{
  "notice_type": "LEGACY_REVIEW_INVALIDATION_NOTICE",
  "applies_to_file": "data/ground_truth/reviews/train_events/event_009_review.json",
  "applies_to_file_sha256_at_notice_time": "06660001cfa9299eb5d299b64089413c96df99284171648e0d0e0f43b0dd860e",
  "disposition": "INVALIDATED",
  "proposed_by": "raihankabirrahu@gmail.com",
  "proposed_at_utc": "2026-10-14T20:00:00Z",
  "reason": "THREAD 1 (process integrity, Phase 11.1, applies to all 27 equally): [... same Thread 1 text as Example A ...]. THREAD 2 (content integrity, Phase 11.4/11.5, specific to this record): direct video inspection plus the researcher's own personal confirmation established that the T0 boundary this record's underlying candidate proposal claimed (late arrival, non-left-censored, T0=1.5s) is factually wrong -- the train is visible at frame zero of the recording. See docs/PHASE11_5_FIELD_ADJUDICATIONS.json.",
  "note": "This notice does not modify, move, or delete the file it describes."
}
```
</details>

### 2.3 Full list of the 27 target sibling-notice paths

| Cohort | Event | Original (unmodified) | Sibling notice (would be created) |
|---|---|---|---|
| engine_events | event_001 | `.../engine_events/event_001_review.json` | `.../engine_events/event_001_review.INVALIDATION_NOTICE.json` |
| no_train_events | event_001 | `.../no_train_events/event_001_review.json` | `.../no_train_events/event_001_review.INVALIDATION_NOTICE.json` |
| no_train_events | event_002 | `.../no_train_events/event_002_review.json` | `.../no_train_events/event_002_review.INVALIDATION_NOTICE.json` |
| no_train_events | event_003 | `.../no_train_events/event_003_review.json` | `.../no_train_events/event_003_review.INVALIDATION_NOTICE.json` |
| train_events | event_001 … event_023 (all 23) | `.../train_events/event_0NN_review.json` | `.../train_events/event_0NN_review.INVALIDATION_NOTICE.json` |

(Full per-event paths and current SHA-256 hashes for all 27: `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json`, each `disposition_events[i].affected_record_path` / `.affected_record_sha256`.)

---

## 3. What this dry run deliberately does NOT do

- Does not create, move, rename, or edit any file under `data/ground_truth/reviews/`.
- Does not change `adjudication_status`, `schema_version`, or any other field inside any of the 27 original records.
- Does not touch `data/ground_truth/proposals/` at all.
- Does not constitute execution. Re-running the generation script (`propose_invalidation`/`write_invalidation_proposal`) is idempotent and append-only against its own output log; it has no code path that writes into `data/ground_truth/reviews/`.

## 4. What executing this plan would require

1. The researcher's separate, explicit instruction to execute (distinct from the scope/mechanism selection already given and from this dry-run review).
2. Writing the 28 files listed in Section 2 at their exact target paths, verified against this plan.
3. Immediately re-hashing all 27 original records to confirm they remain byte-identical to the Phase 11.1 baseline (the sibling-notice mechanism should produce zero diffs on the originals).
4. Updating `docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md` Section 7 (`Execution status`) from `NOT EXECUTED` to the actual execution record, and appending a progress.md entry.

**None of step 1–4 has occurred. This phase ends with the plan prepared and reviewable, execution still pending.**
