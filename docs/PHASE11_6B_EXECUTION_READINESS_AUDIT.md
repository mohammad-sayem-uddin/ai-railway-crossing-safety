# Phase 11.6B — Independent Audit of Legacy Invalidation Execution Readiness

**Repository path (explicit, per instruction):** `/Users/sayemuddin/Desktop/Train_automation`
**Git HEAD throughout this phase:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (unchanged)

**Authorization boundary honored:** this phase performed an independent audit and a read-only preflight only. `apply_invalidation_notices()` — the one function that writes anything — was **never called against the real `data/ground_truth/reviews/` tree or the real proposal**, anywhere in this phase. The zero-write `validate_proposal_for_application()` function **was** run against the real proposal and real `reviews_root` (Task 2 explicitly permits inspection that doesn't call the apply function or write anything; `validate_proposal_for_application` is provably read-only — see Section 2.1). All adversarial/empirical probes in Section 1 ran exclusively against synthetic fixtures in an isolated scratch directory (`/private/tmp/.../scratchpad/audit11_6b/`, itself inside a temp directory per probe, never any path under the repository). **Real execution was not performed. No real notice was created. No real record was touched.**

---

## 1. Independent inspection of the implementation (Task 1)

Inspected directly: `src/railway_detection/annotation/invalidation_notice_writer.py` (full file, 401 lines) and `tests/test_phase11_6a_invalidation_notice_writer.py` (full file, 338 lines) — read fresh in this phase, not taken on the prior report's word. Where a claim in `docs/PHASE11_6A_NOTICE_WRITER_REPORT.md` could be checked empirically rather than just logically, it was: five adversarial probe scripts were written and run against synthetic fixtures (symlink attacks, a true `FileExistsError` race via a mocked `Path.exists`, malformed JSON, a real OS permission error, and genuine multi-threaded concurrent execution).

### 1.1 — Schema, scope, duplicates, traversal, destinations, symlinks, original-record targeting

| Check | Finding |
|---|---|
| Invalid schema (missing/wrong-typed fields) | **Rejected**, confirmed by code reading (`validate_proposal_for_application` lines 127–154) and by the existing `test_missing_required_field_rejected`, `test_malformed_sha256_rejected`. |
| Incorrect scope (wrong record count) | **Rejected** — exact `expected_count` match required (line 132–135); `test_expected_count_mismatch_rejected` passes. |
| Duplicate paths (event_id / target / output) | **Rejected.** Verified the incremental "seen so far" sets correctly catch every pairwise duplicate in a single forward pass (any duplicate pair (i, j) with i<j is caught when j is processed, since i's data is already recorded) — confirmed by re-derivation, not just by the one existing `test_duplicate_target_paths_rejected_and_nothing_written` test. |
| Path traversal | **Rejected**, doubly: a literal `".."` component check runs before any resolution (line 162), and the resolved path is independently required to be `is_relative_to(reviews_root_resolved)` (line 173) — so even an input that evaded the literal check would still be caught by the resolved-path check. Confirmed by `test_path_traversal_rejected` and by probe reasoning. |
| Unexpected destinations / protected artifacts | **Rejected** via the caller-supplied `protected_roots` list (line 178–183) plus the structural requirement that every target end in `_review.json` and sit exactly one cohort directory below `reviews_root` (lines 184–193). `test_protected_root_rejected_even_if_also_inside_reviews_root` specifically proves a misconfiguration (protected root overlapping `reviews_root` itself) fails safe rather than silently permitting everything. |
| Symlink escapes (target) | **Empirically probed, not just read.** A symlink placed at a target path pointing outside `reviews_root` is followed by `Path.resolve()` and then correctly rejected by the `is_relative_to` check (confirmed by code logic; the existing tests don't construct this exact case, so this is a **documented but untested** safeguard — see Section 5, Finding F3). A symlink pointing to **another valid target inside `reviews_root`** is not explicitly rejected by an `is_symlink()` check; protection instead relies on the downstream per-record hash recheck, which would almost certainly mismatch and safely skip rather than misfire — see Finding F1 below for the residual risk this leaves. |
| Symlink escapes (output / targeting an original record) | **Empirically probed and confirmed safe, including the worst case.** Probe 1 and Probe 2 placed a symlink at the computed output path **pointing directly at the real review record itself** and called both the low-level write primitive and the full public `apply_invalidation_notices()` API. Result in both cases: `O_CREAT | O_EXCL` refused the pre-existing symlink (`FileExistsError`, POSIX-standard behavior for `O_EXCL` on a symlink regardless of what it points to), the code correctly fell into the race-reconciliation path, read the real record's content through the symlink, found it did not match the expected notice content, and reported `CONFLICT_EXISTING_OUTPUT_MISMATCH` — **the real record's hash was confirmed unchanged before and after**. This is the single most safety-critical scenario this audit could construct, and it held. |
| Targeting an original record directly as an output | **Rejected** at validation time (`output_path == target_resolved` check, line 201–204) for the straightforward case; the symlink variant above confirms the write-time path is also safe even if this check were somehow bypassed. |

### 1.2 — Binding to the exact approved proposal (Task 1, item 2)

**Partial gap, documented as Finding F2.** The function validates the proposal's *structure* (27 well-formed events) but does **not** verify that the `proposal` dict handed to it is byte-identical to — or otherwise cryptographically bound to — the specific, researcher-reviewed `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json` file. Any structurally-valid 27-event dict with correct hashes would pass validation, regardless of whether its `reason`/`actor`/`authorized_statement` text matches what the researcher actually reviewed. This is not a currently-exploitable defect (there is no adversary in this single-researcher project's threat model who could substitute a different proposal file undetected), but it is a real gap relative to "bound to the exact approved proposal" — see the recommended preflight hash-pin in Section 6.

### 1.3 — Pre-write source re-hash (Task 1, item 3)

**Confirmed, both by code reading and by test.** `_process_one_record` (lines 254–266) re-reads and re-hashes the target immediately before any write decision, independent of the pre-flight validation (which never touches file contents at all — see Section 2.1). Missing file → `SKIPPED_TARGET_MISSING`; hash mismatch → `SKIPPED_TARGET_HASH_MISMATCH`; neither writes anything. `test_target_hash_mismatch_skipped` and `test_missing_target_skipped` both pass and were re-run fresh in this phase.

### 1.4 — `O_CREAT | O_EXCL` correctness and concurrent creation (Task 1, item 4)

**Confirmed for the destination-overwrite guarantee; one genuine, safe-direction race found under true concurrency (Finding F1, see Section 5).** Probe 5 launched two real OS threads calling `apply_invalidation_notices()` against the identical `reviews_root`/proposal simultaneously (10 records). Combined result across both threads: exactly 10 `WRITTEN` + 8 `SKIPPED_ALREADY_DONE_MATCHING` + **2 `CONFLICT_EXISTING_OUTPUT_MISMATCH`**. Diagnosis (Probe 5b, 20 records, same pattern): the conflicting reads failed with `Expecting value: line 1 column 1 (char 0)` — the classic `json.JSONDecodeError` for an **empty file**. This confirms `O_CREAT | O_EXCL` does exactly what its docstring claims (no two writers can ever both "win" the exclusive-create call, so there is never a double-write or corrupted interleave), but the docstring's framing — that the destination-overwrite race is "fully eliminated" — is incomplete: a concurrent reader can observe the brief window between the winning thread's `os.open()` (file now exists, empty) and its `f.write()` completing, and will then report a **spurious** `CONFLICT_EXISTING_OUTPUT_MISMATCH` for what is, at steady state, actually a success. Critically: **final on-disk state after both threads finished was verified complete and correct for all 20 records, every time** — this is never data corruption and never a false "success," only an occasionally over-pessimistic status report under genuine concurrency, which the real execution model (a single sequential script invocation, per Section 6) does not trigger.

### 1.5 — Idempotent skip vs. reported conflict (Task 1, item 5)

**Confirmed exact, whole-content equality, not partial/field-level matching.** `_reconcile_existing` (lines 288–307) compares the fully parsed existing JSON object against the fully-built expected dict with Python `==`, which is a complete structural comparison, not e.g. just checking the `disposition` field. Verified by reading and by the existing `test_existing_matching_output_is_idempotent_resume` / `test_existing_conflicting_output_reported_not_overwritten`, plus Probe 4(a) with genuinely malformed JSON (handled by the `except (OSError, json.JSONDecodeError)` branch, reported as a conflict, never crashes, never overwrites).

### 1.6 — Partial failure / resume determinism (Task 1, item 6)

**Confirmed deterministic by design and by test.** `_build_notice_content` is a pure function of the proposal event alone (explicitly does not embed a write-time wall-clock field — line 234–237 docstring and implementation), which is exactly what makes exact-equality resume comparisons meaningful run-to-run. `test_partial_failure_then_resume` (re-run fresh, passing) proves a monkeypatched transient failure on 1 of 3 records leaves the other 2 written, and a subsequent resume completes exactly the failed one while skipping the two already done. Probe 4(b) reproduced the same pattern with a **real** OS permission error (chmod'd read-only directory, not a mock) on a 2-record batch mixed with an already-conflicting record, confirming the per-record independence and non-crash behavior under a genuine OS-level failure, not just a simulated one.

### 1.7 — Notice content: proposed vs. completed/authorized (Task 1, item 7)

**Minor clarity gap, Finding F4.** The written notice's `disposition` field is a flat `"INVALIDATED"` string, while its provenance fields are named `proposed_by`/`proposed_at_utc`. Once this notice genuinely exists on disk (i.e., real execution has occurred), its existence *is* the applied disposition mechanism — so `"INVALIDATED"` is an accurate statement of what this file represents at that point. But the field naming (`proposed_*`) could read to a future, uninformed reader as "this is still just a proposal," when in fact a written notice is the actual, now-applied marker. The `note` field does clarify non-destructiveness ("does not modify, move, or delete the file it describes") but does not clarify the proposed-vs-applied distinction. Not a safety defect — a documentation/wording clarity issue in a durable artifact.

### 1.8 — Output path derivation safety (Task 1, item 8)

**Confirmed safe by construction, verified by re-derivation.** `output_path = target_resolved.parent / (target_path.stem + NOTICE_SUFFIX)` can never resolve outside `reviews_root` because `target_resolved` was already proven to be inside it (Section 1.1), and the output is placed in the *same* (already-validated) parent directory. One additional observation from re-deriving the collision logic by hand: the `"output path collides with another record's target"` check (line 211–214) is **structurally unreachable** given the mandatory `_review.json` target suffix and the fixed `.INVALIDATION_NOTICE.json` output suffix — no string can simultaneously satisfy both, so no valid target can ever equal a derived output. This is over-defensive dead code, not a bug — noted for completeness (Finding F5, cosmetic only).

### 1.9 — Exceptions, permission errors, malformed JSON, filesystem races → misleading reports? (Task 1, item 9)

**No misleading SUCCESS report was producible under any probe in this audit.** Every adversarial scenario tried (symlink-to-original-record, real permission denial, malformed existing JSON, genuine thread-level race) either correctly skipped, correctly failed with a specific status, or — in the one race case (Finding F1) — reported an unnecessarily pessimistic `CONFLICT` rather than a wrong `WRITTEN`. The failure mode this implementation has, where it has one, is conservative (reports a problem that isn't really one), never the reverse (claims success when something is actually wrong). This is the right direction for a tool whose job is to avoid silently damaging 27 irreplaceable-provenance records.

### 1.10 — Do the tests genuinely exercise the claimed protections? (Task 1, item 10)

**No, not fully — this is the audit's main actionable gap, Finding F3.** Reading `tests/test_phase11_6a_invalidation_notice_writer.py` line-by-line: every "existing output" test (`test_existing_matching_output_is_idempotent_resume`, `test_existing_conflicting_output_reported_not_overwritten`, `test_directory_level_notice_conflict`) pre-creates the conflicting/matching file **before** calling `apply_invalidation_notices()`, which only exercises the `if output_path.exists():` branch (line 271) — never the `except FileExistsError:` branch (lines 276–281, 333–334) that handles a **true** TOCTOU race (file created *after* the `.exists()` check but before/during the exclusive-create call). That branch existed, untested, in the checked-in suite before this audit. This phase's Probe 3 (mocking `Path.exists` to lie) and Probe 5/5b (genuine threading) are the first evidence — in this audit, not in the permanent suite — that this branch behaves correctly. **No existing test constructs a symlink of any kind** (output-path symlink to the original record, or target-path symlink escaping `reviews_root`) — Probes 1 and 2 are, similarly, the first evidence of correct behavior here, and it is not locked in by a regression test.

---

## 2. Read-only real-data preflight (Task 2)

### 2.1 — Confirmation that the validation call is genuinely read-only

Re-read the full `validate_proposal_for_application` function (lines 114–219): it calls `Path.resolve()` and performs string/set comparisons only. Every file-content-touching call in the module (`.exists()`, `.read_bytes()`, `.read_text()`, `os.open()`) lives exclusively in `_atomic_exclusive_write`, `_process_one_record`, `_reconcile_existing`, and `_process_directory_notice` — none of which `validate_proposal_for_application` calls. Confirmed via `grep` that none of those four call sites appear inside the validation function's line range. On this basis, this phase ran it directly against the real proposal and real `reviews_root`:

```
$ venv/bin/python3 -c "... validate_proposal_for_application(real_proposal, reviews_root=Path('data/ground_truth/reviews'),
      protected_roots=[proposals, configs, results, data/raw, data/manifests, data/splits, data/processed], expected_count=27) ..."
VALIDATION PASSED: 27 records validated, 0 writes performed.
```

**Result: 27/27 real records pass the actual shipped validation logic** — not re-derived by hand, the real code — with no protected-root collision, no duplicate, no traversal, no suffix/depth violation.

### 2.2 — Source hash re-verification

Recomputed SHA-256 for all 27 real records and compared against **both** `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json`'s recorded hashes **and** the independent Phase 11.1 baseline (`/tmp/phase11_1_reviews_baseline_hashes.txt`): **0 errors, 0 mismatches, the same 27 paths in both sets.**

### 2.3 — Output paths / existing notices / collisions

`find data/ground_truth/reviews -iname "*notice*" -o -iname "*invalidat*"` → **empty.** `find data/ground_truth/reviews -type l` (symlinks) → **empty** — the real tree contains no symlinks of any kind, so the symlink-escape scenarios probed in Section 1.1 are hypothetical for this tree today, not a currently-present condition.

### 2.4 — Proposal vs. recorded researcher decisions

Cross-checked `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json`'s `actor` (`raihankabirrahu@gmail.com`) and `authorized_statement` text against `docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md` Section 6 (`Authorized decision-maker: raihankabirrahu@gmail.com`, scope = full 27, mechanism = sibling notices, originals preserved in place, dated 2026-10-14). **Consistent across all three documents.** No missing, changed, ambiguous, or unexpected files were found. Nothing was repaired or regenerated — this preflight only read and compared.

---

## 3. Integrity verification (Task 3)

| Check | Result |
|---|---|
| 27 original review records vs. Phase 11.1 baseline | **Byte-identical, 27/27.** |
| Real invalidation notices created | **Zero** — confirmed by filesystem search. |
| `configs/frozen_experiment_v1.yaml`, `decision_policy_v1.yaml`, `decision_policy_v2_candidate.yaml` canonical hashes | **Unchanged** — verified via the project's own `compute_canonical_config_hash`/`load_frozen_config` functions (`999a7970...`, `051c908d...`, `143782d1...`), not raw file bytes (per the Phase 11.5 lesson about these being semantically-normalized hashes). |
| Phase 8 exploratory output (46 files, `results/r04_sync_estimation/exploratory_live_run_20261013T194806Z/`) | **Byte-identical.** |
| Model checkpoints | Unreferenced and untouched by anything this phase did (no checkpoint path appears anywhere in `invalidation_notice_writer.py` or in this audit's probes). |
| Git HEAD | **Unchanged**, `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`, confirmed at both the start and end of this phase. |
| Staging state | Nothing staged or committed by this phase. |

---

## 4. Test commands and results

```
$ venv/bin/python3 -m pytest tests/test_phase11_6a_invalidation_notice_writer.py -v
...18 passed in 0.09s
```

Five new adversarial probe scripts were written and run in this phase (synthetic fixtures only, isolated temp directories, never the repository): symlink-at-output-path (low-level + full API), a true `FileExistsError` race via mocked `Path.exists`, malformed-JSON + real permission-denied, and genuine two-thread concurrent execution (10 and 20 records). None of these probes are part of the checked-in test suite — they are audit evidence, documented here, not new regression tests (per this phase's restriction against expanding scope; see Section 7 for the recommended follow-up to formalize them).

Full project suite was not re-run in this phase since no source file was modified; the Phase 11.6A baseline (423 passed, 3 pre-existing unrelated failures) stands unchanged.

---

## 5. Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| **F1** | Low (safe-direction only) | Under genuine concurrent execution, a losing writer can observe a transient empty file and report a spurious `CONFLICT_EXISTING_OUTPUT_MISMATCH` for what becomes, at steady state, a correct success. Never produces corruption or a false success; self-resolves on a later sequential re-run. | Probe 5 / 5b, §1.4 |
| **F2** | Low | The function validates proposal *structure* but does not cryptographically bind to a specific, pre-approved proposal file (e.g. by hash-pin) — any structurally valid 27-event dict is accepted. | §1.2 |
| **F3** | Low–Medium (test-coverage gap, not a code defect) | The `except FileExistsError` race-reconciliation branch and all symlink-escape scenarios have **zero coverage in the checked-in test suite** — this audit's manual probes are the only evidence they work, and that evidence lives in this report, not in a re-runnable regression test. | §1.4, §1.10 |
| **F4** | Cosmetic | Notice content's `proposed_by`/`proposed_at_utc` field names could be read as "still just a proposal" even once the notice is a real, applied disposition marker. | §1.7 |
| **F5** | Cosmetic / dead code | The "output path collides with another record's target" validation branch is structurally unreachable given the enforced suffix patterns — harmless, over-defensive. | §1.8 |
| — | None found | No path to real-record modification, corruption, or silent overwrite was found under any probe, including the worst-case symlink-to-original-record scenario. | §1.1, §2 |

---

## 6. Verdict

# `READY_FOR_SEPARATE_AUTHORIZATION`

Every safety-critical claim this audit could test — including ones the prior self-report did not explicitly empirically verify (symlink-to-original-record, a true TOCTOU race, a real OS permission error, genuine thread-level concurrency) — held under adversarial pressure. The one genuine race condition found (F1) is conservative in direction (spurious failure report, never spurious success, never data loss) and is not triggered by the planned real-execution model (a single sequential invocation, not concurrent processes). Findings F2–F5 are real but non-blocking: they do not create a path to damaging the real 27 records, and are better addressed as a focused follow-up than as a precondition to the one-time, carefully-staged execution this project has been building toward since Phase 11.3.

This verdict is **not** execution authorization. It states that the tool is ready to be *given* that authorization, should the researcher choose to provide it separately.

---

## 7. Exact consequences of partial success, if real execution is eventually authorized

Given the current real-data state (27/27 clean, no existing notices, no collisions — §2):

- A fully successful single run would produce exactly **28 `WRITTEN`** results (27 sibling notices + 1 directory notice), 0 skips, 0 conflicts, 0 failures — this is the expected outcome and should be verified, not assumed.
- If the run is interrupted partway (process killed, disk full, permission revoked mid-batch): every notice written before the interruption remains **correct and final** (content is deterministic and complete by the time `O_CREAT|O_EXCL` succeeds — confirmed in §1.4's concurrency probe, which showed final state is always valid even under contention). Every **un-attempted** record is simply absent — no partial, corrupt, or misleading file is left for those. The one record that failed **mid-write** (if any) may leave a transient empty or partial file at its specific output path (an OS-level write-interruption scenario, distinct from F1's read-side race) — on the documented resume, this would be read back, fail JSON parsing, and correctly surface as `CONFLICT_EXISTING_OUTPUT_MISMATCH`, not silently retried or overwritten. **The original 27 review records themselves are never at risk in any partial-success scenario** — nothing in this codepath ever opens one of them for writing.
- Resuming after partial success: re-running with the same proposal will report `SKIPPED_ALREADY_DONE_MATCHING` for everything already correctly written, and attempt only what remains — this is the documented, now-triply-verified (unit test, mocked race, real thread race) recovery procedure.
- The one scenario requiring a human, not a re-run: a `CONFLICT_EXISTING_OUTPUT_MISMATCH` left over from a genuinely **different**, non-matching prior write at that exact path (as opposed to F1's self-resolving transient case) — the documented procedure is to inspect that one specific file and decide whether to manually remove it before retrying that one record. No automatic resolution is attempted, by design.

---

## 8. Proposed execution checklist (proposed only — not run by this phase)

1. **Preflight.** Re-run Section 2's read-only checks immediately before execution, not relying on this report's point-in-time results: re-hash all 27 real records, re-run `validate_proposal_for_application` against the real proposal, re-confirm zero existing notices/collisions. (Recommended addition per F2: hash-pin and verify the proposal JSON file itself matches the exact artifact the researcher reviewed.)
2. **Apply.** Single sequential invocation of `apply_invalidation_notices()` against the real `reviews_root` and real proposal — not run concurrently or from multiple processes (sidesteps F1 entirely). Capture the full `NoticeWriteReport`.
3. **Post-write verification.** Immediately re-hash all 27 original records and confirm byte-identical to the Phase 11.1 baseline (proves the apply step, like every probe in this audit, never touched an original). Confirm the report shows 28/28 `WRITTEN` (or investigate every non-`WRITTEN` entry individually before declaring completion). Spot-check 2–3 written notices' content against the dry-run plan's worked examples.
4. **Recovery handling.** If the report shows anything other than 28/28 `WRITTEN`: for each `SKIPPED_TARGET_MISSING`/`SKIPPED_TARGET_HASH_MISMATCH`, investigate why the real record changed or vanished since the proposal was generated (should not happen given §2's preflight, but must not be silently retried without understanding why). For each `CONFLICT_EXISTING_OUTPUT_MISMATCH`, inspect the specific file manually per Section 7's last bullet before any further action. For each `FAILED_WRITE_ERROR`, resolve the underlying OS issue (permissions, disk space) and re-run — already-written records will correctly skip as `SKIPPED_ALREADY_DONE_MATCHING`.
5. **Documentation.** Update `docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md` Section 7 from `NOT EXECUTED` to the real `NoticeWriteReport` outcome, and append a progress.md entry with the actual result — not a restatement of this plan.

**None of the above has been run. This phase ends with the implementation audited, the real data independently re-verified clean, and a documented verdict — the real `data/ground_truth/reviews/` tree is exactly as it was at the start of this phase.**
