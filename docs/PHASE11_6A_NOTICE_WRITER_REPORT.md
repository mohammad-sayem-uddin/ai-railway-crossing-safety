# Phase 11.6A — Legacy Invalidation Notice Writer: Implementation and Testing

**Authorization boundary (verbatim from the researcher):** *"I authorize implementation and testing of the writer function using synthetic fixtures only. I do not authorize writing any files into the real `data/ground_truth/reviews/` directories. Do not execute the function against the real 27 records, create any of the 28 planned notices, or invalidate any real legacy approval."*

**This phase stayed inside that boundary.** The new module was never imported or called with a real path anywhere in this phase except for read-only, existence/hash verification of the real tree before and after the test run (standard `shasum`/`find`, not the new module itself). No file was created, moved, or modified under `data/ground_truth/reviews/`.

---

## 1. What was built

`src/railway_detection/annotation/invalidation_notice_writer.py` — a new, dedicated module that performs the write step `promotion_gate.py`'s `propose_invalidation()`/`write_invalidation_proposal()` deliberately never do (those two only read a real record to capture its hash, and write to a caller-chosen *proposal log* path, never into the reviews tree).

Two public entry points:
- `validate_proposal_for_application(proposal, *, reviews_root, protected_roots=None, expected_count=27)` — pure validation, never writes, raises `NoticeWriterValidationError` on the first violation and rejects the **whole batch**.
- `apply_invalidation_notices(proposal, *, reviews_root, protected_roots=None, expected_count=27, now_utc=None)` — validates (via the above), then writes, returning a `NoticeWriteReport` with one `NoticeWriteResult` per record plus a separate result for the directory-level notice.

### 1.1 Validation performed before any write (Requirement 1)

- Proposal shape: `disposition_events` must be a list of exactly `expected_count` (27 by default) well-formed entries, each with all seven required fields (`event_id`, `reason`, `actor`, `authorized_statement`, `at_utc`, `affected_record_path`, `affected_record_sha256`) non-blank.
- `affected_record_sha256` must be a syntactically valid 64-character hex SHA-256.
- Every target path must be **relative** (absolute paths rejected), contain no `..` component (path traversal rejected before any resolution), resolve to somewhere **inside** `reviews_root`, resolve to somewhere **outside** every caller-supplied `protected_roots` entry, end in `_review.json`, and sit exactly one cohort directory below `reviews_root`.
- No two events may share an `event_id`, an `affected_record_path`, or a derived output path; no output path may collide with its own target, with the directory-level notice path, or with *another* record's target.
- Any violation raises immediately — **nothing is written**, confirmed by a dedicated test (`test_duplicate_target_paths_rejected_and_nothing_written`) that asserts zero notice files exist anywhere after a rejected batch.

### 1.2 Per-record recheck immediately before writing (Requirement 2)

Right before each individual notice is created, the function re-reads the target file and recomputes its SHA-256 — never trusting the pre-flight validation (which doesn't touch file contents at all) or the hash the proposal recorded at proposal-generation time. A missing target → `SKIPPED_TARGET_MISSING`. A changed hash → `SKIPPED_TARGET_HASH_MISMATCH`. Neither ever writes a notice for that record, and neither touches the target file itself.

### 1.3 Safe partial-failure and resume behavior (Requirement 3)

Records are processed in an ordinary Python loop with no shared transaction — one record's outcome (success, skip, or failure) cannot affect another's. `NoticeWriteReport.summary_counts()` tallies all nine possible outcomes across the batch. An existing output is never silently overwritten: it is read back and compared **by exact content equality** against what would be written now; a match is reported `SKIPPED_ALREADY_DONE_MATCHING` (safe, idempotent resume), a mismatch is reported `CONFLICT_EXISTING_OUTPUT_MISMATCH` and left untouched. The notice content is a pure function of the proposal event only (no write-time wall-clock field baked in), which is what makes exact-equality resume comparisons meaningful across separate runs. The operation's non-atomicity is stated plainly in `apply_invalidation_notices`'s docstring, including the documented recovery procedure for a `FAILED_WRITE_ERROR` possibly leaving a partial file (manual inspection/removal of that one file, then retry).

### 1.4 Concurrent-change protection (Requirement 4)

Destination-overwrite races are eliminated outright: notices are created with `os.open(..., O_CREAT | O_EXCL)`, so the OS itself refuses a second writer, and a caught `FileExistsError` is reconciled exactly like a pre-existing output (read back, compare, report match/conflict) rather than silently treated as success. The one race this implementation does **not** eliminate — stated explicitly in the docstring, not hidden — is between recomputing a target's hash and opening its notice for exclusive creation: no cross-platform file lock is taken on the target, so a target modified in that narrow window could still result in a notice written against a hash that was correct a moment earlier. The window is minimized (no other I/O happens between the hash check and the write) but not zero.

---

## 2. Tests — 18/18 passing, synthetic fixtures only

`tests/test_phase11_6a_invalidation_notice_writer.py`. Every test `monkeypatch.chdir()`s into its own `tmp_path` and builds relative paths there (matching exactly how the real proposal's `affected_record_path` values are stored — repo-relative strings) — none ever constructs or references a path under the real `data/ground_truth/reviews/`.

| Requirement (brief) | Test(s) |
|---|---|
| All expected notices generated | `test_all_expected_notices_generated` |
| Target hash mismatch / missing target | `test_target_hash_mismatch_skipped`, `test_missing_target_skipped` |
| Existing matching output / conflicting output | `test_existing_matching_output_is_idempotent_resume`, `test_existing_conflicting_output_reported_not_overwritten` |
| Duplicate paths / path traversal | `test_duplicate_target_paths_rejected_and_nothing_written`, `test_path_traversal_rejected`, `test_absolute_target_path_rejected` |
| Partial failures / resume after partial completion | `test_partial_failure_then_resume` (monkeypatches the write primitive to fail for one of three records, confirms the other two still complete, then confirms a clean resume writes exactly the one that failed and skips the two already done), `test_batch_continues_after_one_ordinary_failure_not_aborted` |
| Directory-level notice conflicts | `test_directory_level_notice_conflict` |
| Proof originals remain byte-identical | `test_originals_byte_identical_through_mixed_outcomes` |
| Proof nothing is written outside the fixture | `test_no_path_written_outside_fixture_root` (diffs the full file listing of the fixture root before/after, asserts the new-file set is *exactly* the expected 4 outputs, and separately confirms the sibling, never-targeted `proposals/` directory received nothing) |
| (additional, beyond the brief's list) | `test_expected_count_mismatch_rejected`, `test_missing_required_field_rejected`, `test_malformed_sha256_rejected`, `test_protected_root_rejected_even_if_also_inside_reviews_root` (a misconfiguration-safety test — if a caller accidentally marks `reviews_root` itself as protected, the writer fails closed rather than silently permitting it), `test_target_not_ending_in_review_json_suffix_rejected` |

**Result:** `venv/bin/python3 -m pytest tests/test_phase11_6a_invalidation_notice_writer.py -v` → **18 passed**.

One test bug found and fixed during development: `test_partial_failure_then_resume` initially compared the monkeypatched write path against a *relative* `failing_output` while the real code path passes the *resolved (absolute)* output path into the write primitive — the monkeypatch's equality check silently never matched, so the simulated failure never fired and the test passed for the wrong reason (vacuously). Fixed by resolving `failing_output` the same way the module does before comparing. No production code was affected by this fix.

---

## 3. Full regression suite

`venv/bin/python3 -m pytest tests/ -q --ignore=tests/unit/test_audio_leakage_and_preprocessing.py --ignore=tests/unit/test_audio_training.py` (same exclusions as every phase since Phase 9, both still fail to collect — missing `railway_detection.audio.training`):

**423 passed** (405 + the 18 new tests), **3 failed** — the same pre-existing, confirmed-unrelated failures seen continuously since Phase 9: `test_audio_v2_pipeline.py::test_v2_figures_and_report_artifacts`, `test_audio_v3_pipeline.py::test_v3_publication_figures_and_reports`, `test_real_dataset_inventory.py::test_audio_extension_anomaly_tracking`. No new failures introduced.

---

## 4. Integrity re-verification

- All 27 real review records re-hashed immediately after running the full test suite: **byte-identical** to the Phase 11.1 baseline.
- `find data/ground_truth/reviews -iname "*notice*" -o -iname "*invalidat*"`: **empty** — no stray notice file of any kind exists anywhere in the real tree.
- The new module was never invoked with `reviews_root` pointing anywhere under the real `data/ground_truth/` tree in this phase.
- Git HEAD unchanged; nothing staged or committed.

---

## 5. What this phase explicitly did not do

- Did not call `apply_invalidation_notices` (or even the read-only `validate_proposal_for_application`) against the real `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json` or the real `data/ground_truth/reviews/` tree, even though `validate_proposal_for_application` itself never writes — out of an abundance of caution relative to the researcher's explicit "do not execute the function against the real 27 records," read strictly.
- Did not create any of the 28 planned real notices.
- Did not invalidate any real legacy approval.
- Did not approve any annotation, promote anything to Stage 3, or begin Phase 12.

---

## 6. Real-execution preflight proposal (proposed only — not run)

If and when the researcher gives separate, explicit execution authorization, the proposed preflight sequence is:

1. **Read-only validation pass**: call `validate_proposal_for_application(proposal, reviews_root=Path("data/ground_truth/reviews"), protected_roots=[Path("data/ground_truth/proposals"), Path("configs"), Path("results"), Path("data/raw")], expected_count=27)` against the real `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json`. This step touches no file contents (it resolves paths and checks string-level structure only) and would surface any validation failure before anything is written. **Section 2 of this report's pre-execution checklist (run against the real data in the prior turn) already confirmed: 27/27 target hashes match current files and the Phase 11.1 baseline; all 28 output paths unique; none pre-exist; none collide with originals or with `data/ground_truth/proposals/`.**
2. **Apply pass**: call `apply_invalidation_notices(...)` with the same arguments. Expected outcome given the current, re-confirmed state of the real tree: 27× `WRITTEN` + 1× `WRITTEN` (directory notice) = 28/28 written, 0 skips, 0 conflicts, 0 failures — but the function must actually be run to confirm this, not assumed from the dry-run alone (the per-record hash recheck happens live, at write time, which is the entire point of Requirement 2).
3. **Immediate re-verification**: re-hash all 27 original review records and confirm byte-identical to the Phase 11.1 baseline (proves the apply pass, like every test, never touched an original); list the 28 new files and spot-check two or three against the dry-run plan's worked examples.
4. **Documentation update**: update `docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md` Section 7 (`Execution status`) from `NOT EXECUTED` to the actual `NoticeWriteReport` summary, and append a progress.md entry recording the real outcome.

**None of steps 1–4 has been run. This phase ends with the writer implemented, tested, and documented; the real `data/ground_truth/reviews/` tree is exactly as it was at the start of this phase.**
