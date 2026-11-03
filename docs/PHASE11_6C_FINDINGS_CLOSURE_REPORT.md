# Phase 11.6C — Findings Closure Report

**Authorization boundary honored throughout:** focused code/test changes using synthetic fixtures only. `apply_invalidation_notices()` was never called against the real `data/ground_truth/reviews/` tree. The one real-data interaction in this phase was computing the raw-byte SHA-256 of a **docs file** (`docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json`) via plain `hashlib` — read-only, not a call into the writer module, not a path under `data/ground_truth/reviews/`. **Real execution was not performed. No real notice was created. No real review record was touched.**

---

## Finding-by-finding disposition

### F3 — Mandatory regression coverage: **CLOSED**

25 new tests added (`tests/test_phase11_6c_notice_writer_hardening.py`), covering every item the brief listed:

1. **`FileExistsError` race-handling branch**: `test_race_matching_content_classified_skipped_not_retryable`, `test_race_unparseable_content_classified_retryable_via_lost_open`, `test_race_conflicting_but_parseable_content_remains_permanent_mismatch` — all deterministic (a monkeypatched `Path.exists` forces the exact race window, no timing dependency), plus `test_genuine_concurrent_threads_never_produce_permanent_mismatch`, which uses **real OS threads** (not mocked) as the brief's "if practical, use a controlled synchronization barrier or injected test hook" alternative — run 15 times back-to-back during this phase with zero flakes.
2. **Output-path symlink → source record itself**: `test_symlink_output_to_source_record_itself_refused_low_level` (direct `_atomic_exclusive_write` call) and `..._refused_full_api` (full `apply_invalidation_notices` call) — both assert the record's hash and byte content are identical before/after.
3. **Output-path symlink → a different protected file**: `test_symlink_output_to_different_protected_file_refused` (a decoy file standing in for a proposal) — asserts the decoy's content is untouched and the *other*, unaffected record in the same batch still proceeds normally.
4. **Symlink target outside the permitted tree**: `test_symlink_target_outside_permitted_output_tree_refused`.
5. **Existing symlinks / malformed / unreadable outputs**: `test_dangling_output_symlink_refused`, `test_dangling_symlink_at_output_never_classified_retryable`, `test_directory_notice_truncated_prefix_classified_retryable`, `test_unreadable_existing_output_real_permission_denied` (a **real** `chmod 0o000`, not mocked).
6. **Never overwrites/modifies a protected target**: `test_symlink_scenarios_never_modify_any_protected_target` consolidates four simultaneous symlink attacks (self-target, different-protected-file, outside-tree, dangling) in one batch and asserts every candidate file's hash/content is byte-identical before and after — not just that the batch "succeeded."

Both the low-level primitive (`_atomic_exclusive_write`, `_process_one_record` called directly) and the public API (`apply_invalidation_notices`) are exercised, per the brief's instruction, in the source-record-symlink pair of tests and throughout.

**A genuine bug was found and fixed while writing this coverage**, not merely confirmed-safe as hoped. See "An unplanned finding" below — this is the main substantive result of closing F3, not just paperwork around the audit's existing evidence.

### F2 — Reviewed-proposal binding: **CLOSED**

Added `compute_proposal_sha256(proposal_path) -> str` and `load_and_verify_proposal(proposal_path, *, expected_sha256: str) -> dict` to `invalidation_notice_writer.py`.

- **Rule, clearly documented**: **raw-byte SHA-256** of the proposal file exactly as it sits on disk — deliberately *not* a canonical/semantic hash. The docstring explains why this differs from the frozen-config case: a human reviewed this exact file, including the precise wording of every `reason`/`authorized_statement` string, so a canonical hash (which would accept any semantically-equivalent reformatting as "the same reviewed proposal") would reopen exactly the gap F2 identified.
- **`expected_sha256` is a required keyword argument with no default** — `test_load_and_verify_proposal_never_defaults_to_computed_hash` proves calling without it is a `TypeError`, never a silent pass; the function never computes "the hash of whatever is on disk" and treats that as correct.
- **Rejects changed, substituted, and altered-scope content, before any output is written**: `test_load_and_verify_proposal_modified_content_rejected` (one field changed after the hash was recorded), `test_load_and_verify_proposal_substituted_file_rejected` (a totally different file at the same path), `test_load_and_verify_proposal_altered_scope_rejected` (an extra event added, changing the count). `test_load_and_verify_proposal_failure_writes_nothing` diffs the full fixture directory's file listing before/after a rejected call and confirms it is empty — nothing is written anywhere on a binding failure.
- **Still subject to full structural validation downstream**: `test_load_and_verify_proposal_matching_hash_succeeds` feeds the returned dict into the existing `validate_proposal_for_application` and confirms it is still independently checked (27-count, path structure, etc.) — the hash binding is an *additional* gate, not a replacement for the existing one.
- **Documented, as required**: `docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md` Section 6 now records the real, computed raw-byte SHA-256 of `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json` (`41cbbba3e9d587b9972c3baca1b39f09d478d408d9c60fd538c249c4600113d4`) and states explicitly that any real-execution preflight must call `load_and_verify_proposal` with this value and abort on `ProposalBindingError`.
- **Hash ≠ authorization, stated explicitly** in the function's docstring, in the disposition document, and in the closure summary below, per the brief's explicit instruction not to conflate the two.

### F1 — Concurrency behavior: **CLOSED, with a corrected and strengthened fix**

Preserved the no-overwrite guarantee (nothing in this phase weakened it — `O_CREAT|O_EXCL` is unchanged). Added `CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE` to `NOTICE_WRITE_STATUSES`, distinct from the permanent-looking `CONFLICT_EXISTING_OUTPUT_MISMATCH`, exactly as the brief asked: a losing writer that observes unparseable or truncated content is now classified retryable rather than as a permanent mismatch.

**An unplanned, genuine bug was found and fixed during this closure work, via the real-thread stress test used to validate the fix**: the first implementation classified retryable-vs-permanent based on *how* the conflict was discovered (`came_from_race`: did we lose the `O_CREAT|O_EXCL` attempt ourselves, or did our upfront `.exists()` check already see the file?). That distinction turned out to be **false** under genuine concurrency — a 3-thread stress test (40 identical records, deliberately higher contention than the 2-thread test used in the Phase 11.6B audit) reproduced a `CONFLICT_EXISTING_OUTPUT_MISMATCH` for content that, moments later, was complete and correct: the upfront `.exists()` branch can observe a concurrent writer's in-progress file every bit as easily as a lost `os.open()` race can, and the original design had silently assumed otherwise. **This would have been a real, user-visible regression had F1 only been "closed" by the originally-planned, narrower fix** — a spurious permanent-conflict report for a perfectly healthy concurrent run, exactly the "misleading failure classification" the audit was trying to eliminate, just moved to a different code path rather than removed.

The corrected design classifies purely on *what is read*, not on which branch led there:
- Nothing readable at all (`FileNotFoundError`) → **not** retryable (a dangling symlink will never resolve itself with a retry) — `test_dangling_symlink_at_output_never_classified_retryable` pins this distinction so the fix for the concurrency bug doesn't inadvertently make dangling symlinks look retryable too.
- Readable but unparseable, or a truncated prefix of the expected text → `CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE`.
- Readable, parseable, genuinely different → `CONFLICT_EXISTING_OUTPUT_MISMATCH` (a real disagreement).

**Residual limitation, per the brief's explicit allowance to document rather than over-engineer**: in a genuinely single-sequential execution (the only model actually planned for real use — see the execution checklist below), there is no concurrent writer, so an unparseable pre-existing file there is *not* actually "possibly in progress" — it is a stale or corrupted leftover. The implementation cannot distinguish "pre-existing from a previous run" from "a live concurrent writer" by content alone, and does not attempt to (the brief's "if reliable classification cannot be implemented without broadening scope, document the limitation" clause applies directly here). The status name uses "POSSIBLY" deliberately, and the operational recommendation — in the step-5 execution checklist below — is: a `CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE` that persists across a retry is not actually in progress and should then be treated exactly like `CONFLICT_EXISTING_OUTPUT_MISMATCH` (manual inspection required). No-overwrite behavior holds identically either way, regardless of which status is reported.

### F4 — Cosmetic wording: **CLOSED**

`_build_notice_content` now carries the proposal's `authorized_statement` verbatim (previously present in the proposal but not surfaced in the durable notice artifact), and its `note` field states explicitly: *"[the notice] does NOT, by itself, independently constitute or prove human authorization beyond the 'authorized_statement' recorded above; the full, separately-signed authorization record is docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md Section 6."* The directory-level notice's wording was updated identically. `test_notice_content_includes_authorized_statement`, `test_notice_wording_clarifies_not_independent_proof_of_authorization`, and `test_directory_notice_wording_clarifies_not_independent_proof_of_authorization` pin both files' wording. No change was made to anything not specifically identified by F4 (the `disposition: "INVALIDATED"` field itself is unchanged, since it is an accurate statement of what a *written* notice represents — only the fields that could be misread as independently proving authorization were touched).

### F5 — Dead code: **CLOSED (documented, not removed)**

A comment was added at the structurally-unreachable "output path collides with another record's target" validation branch, explaining precisely why it is currently unreachable (the enforced suffix patterns make it so) and why it is being *kept* rather than deleted: it becomes a real safeguard, not vacuous, the moment either suffix constant changes. No functional code was altered.

---

## Verification

```
$ venv/bin/python3 -m pytest tests/test_phase11_6c_notice_writer_hardening.py -v
...25 passed in 0.11s

$ venv/bin/python3 -m pytest tests/test_phase11_6a_invalidation_notice_writer.py tests/test_phase11_6c_notice_writer_hardening.py tests/test_phase11_5_adjudication.py -q
49 passed in 0.11s

$ venv/bin/python3 -m pytest tests/ -q --ignore=tests/unit/test_audio_leakage_and_preprocessing.py --ignore=tests/unit/test_audio_training.py
3 failed, 448 passed in 11.35s
```

The 3 failures are the same pre-existing, confirmed-unrelated failures seen continuously since Phase 9 (`test_audio_v2_pipeline.py::test_v2_figures_and_report_artifacts`, `test_audio_v3_pipeline.py::test_v3_publication_figures_and_reports`, `test_real_dataset_inventory.py::test_audio_extension_anomaly_tracking`), reported separately as instructed. 448 = 423 (Phase 11.6A/11.6B baseline) + 25 new. No new failures. The 15-run repeat of the one real-thread test showed zero flakes.

**Integrity**: all 27 real review records re-hashed byte-identical to the Phase 11.1 baseline; zero real notice files exist anywhere under `data/ground_truth/reviews/`; all three canonical config hashes unchanged (via the project's own hashing function); Phase 8 exploratory output (46 files) byte-identical; Git HEAD unchanged at `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` throughout; nothing staged or committed by this phase — confirmed via `git status --porcelain`, all new/changed files show as untracked (`??`), none staged.

---

## Residual risks (after closure)

- **F1's single-sequential-vs-concurrent ambiguity** (documented above): a persistent `CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE` after a retry in the real, single-run execution model should be treated as requiring human review, not auto-retried indefinitely. Reflected in the execution checklist below.
- **F2 binds to file content, not to a live human action**: a correct hash proves the file wasn't altered since review; it does not and cannot prove a human actually looked at it before authorizing. This is stated explicitly, not glossed over.
- **F5's defensive branch remains intentionally present but currently unreachable** — if `REVIEW_FILE_SUFFIX`/`NOTICE_SUFFIX` are ever changed, this should be re-examined to confirm it's still correctly positioned.
- No new residual risk was introduced by this phase's changes; the one genuinely new risk this phase discovered (the `came_from_race` misclassification) was fixed, not merely documented.

---

## Proposed execution checklist (updated from Phase 11.6B §8 — proposed only, not run)

1. **Preflight — proposal binding (new, F2).** `load_and_verify_proposal(Path("docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json"), expected_sha256="41cbbba3e9d587b9972c3baca1b39f09d478d408d9c60fd538c249c4600113d4")`. Abort on `ProposalBindingError` — do not proceed, do not recompute a new expected hash from whatever is found.
2. **Preflight — structural + real-data re-verification.** Re-run `validate_proposal_for_application` against the bound proposal and real `reviews_root`; re-hash all 27 real records against both the proposal and the Phase 11.1 baseline; re-confirm zero existing notices/collisions in the real tree (Phase 11.6B §2, re-confirmed clean again in this phase, Section "Verification" above).
3. **Apply — single sequential invocation.** Call `apply_invalidation_notices()` once, not concurrently (sidesteps F1's single-run ambiguity entirely — the planned execution model never needs the retryable-vs-permanent distinction to be perfect, since nothing else will be racing it). Capture the full `NoticeWriteReport`.
4. **Post-write verification.** Re-hash all 27 original records, confirm byte-identical to baseline. Confirm 28/28 `WRITTEN`. Spot-check 2–3 notices for the new `authorized_statement` field and clarified `note` wording.
5. **Recovery handling, updated for the new status.** `SKIPPED_TARGET_MISSING`/`SKIPPED_TARGET_HASH_MISMATCH` → investigate why a real record changed (should not happen given step 2). `CONFLICT_EXISTING_OUTPUT_MISMATCH` → manual inspection of that one file, per the existing procedure. `CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE` → since this is a single sequential run, this status should not occur; if it does, wait briefly and retry that one record once — if it recurs, treat it exactly as `CONFLICT_EXISTING_OUTPUT_MISMATCH` (manual inspection), since persistence across a retry in a non-concurrent run means it was never actually "in progress." `FAILED_WRITE_ERROR` → resolve the OS issue, re-run (already-written records correctly skip).
6. **Documentation.** Update `docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md` Section 7 from `NOT EXECUTED` to the real outcome; append a progress.md entry with the actual result.

**None of the above has been run. This phase ends with the findings closed, the implementation and its new tests verified, and the real `data/ground_truth/reviews/` tree exactly as it was at the start of this phase.**
