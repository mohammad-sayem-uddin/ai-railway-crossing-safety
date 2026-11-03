# Phase 11.1 — Ground-Truth Integrity Investigation

**Status:** Investigation complete. No annotation approved, rejected, or modified. No new model inference. No performance metric computed.
**Scope:** Investigates the Phase 11 finding that all 27 `data/ground_truth/reviews/*/event_XXX_review.json` records share an identical `review_date_utc` timestamp. Establishes what the available repository evidence does and does not support.

---

## 1. Preservation verification

Captured before any investigation began:
- Git HEAD: `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (unchanged throughout).
- SHA-256 of all 27 review files, saved to `/tmp/phase11_1_reviews_baseline_hashes.txt`; re-hashed at the end of this phase (`/tmp/phase11_1_reviews_after_audit_hashes.txt`) — **byte-identical, 27/27, confirmed via `diff`.**
- `configs/frozen_experiment_v1.yaml` hash `999a7970...`, `configs/decision_policy_v1.yaml` hash `051c908d...`, `configs/decision_policy_v2_candidate.yaml` hash `143782d1...` — all re-verified unchanged.
- Phase 8 output (46 files): byte-identical to the baseline preserved since Phase 9. Phase 9/10/10.1 outputs: present, untouched.
- No model weight, checkpoint, or threshold was read for modification. No existing proposal, review, snapshot, or raw media file was modified, overwritten, or deleted anywhere in this phase.
- No new model inference, no full-cohort fusion, no performance metric.
- Git working tree: nothing staged or committed by this phase.

The one script this phase executed that writes any file, `scripts/run_canonical_tests.py` (pre-existing, not authored this phase), writes only to `results/testing/canonical_test_results.json` — never to any ground-truth path. This phase's own new script, `scripts/run_phase11_1_integrity_audit.py`, reads the 27 review files and the proposal directory only, and writes only `docs/PHASE11_1_INTEGRITY_INVENTORY.json`.

---

## 2. Investigation of the approval records

### 2.1 Verified facts

These are directly observed, independently reproducible from files currently on disk; no inference is involved.

1. **The shared timestamp is an exact, byte-identical string across all 27 files**, at second-level precision with no sub-second component: `"2026-10-12T16:51:21Z"`, confirmed by comparing `repr()` of the raw JSON value across all 27 files (not just equal after parsing — literally the same string).
2. **Filesystem modification times for the 27 files span approximately 5 seconds** (12:51:23 to 12:51:28, local time, consistent with the claimed UTC timestamp at a ~4-hour offset), in filename order (`event_001` through `event_023`, then `engine_events/event_001`, then `no_train_events/event_001`–`003`). This is ~0.19s/file on average.
3. **None of the 27 files is tracked by Git on any branch, in any commit** (`git log --all --oneline -- data/ground_truth/reviews/` returns nothing; the repository has 19 total commits, all on `main`, the latest dated `2026-10-12 07:47:55 -0400` — over 5 hours before the reviews' claimed timestamp). The files exist only on the working-tree filesystem.
4. **Every review record references a proposal version that is not the currently-active one.** Cross-checking each record's `proposal_reference.proposal_file` against the latest-numbered proposal file actually present for that event: **27/27 reference a superseded version** (e.g. `event_001`'s review references `event_001_proposal_v5.json`; the currently active proposal is `v6`; `event_005`'s review references `v1`; the active proposal is `v4`). Independently confirmed via `scripts/run_phase11_1_integrity_audit.py`'s `check_proposal_currency`-equivalent file-path comparison: `docs/PHASE11_1_INTEGRITY_INVENTORY.json` records `"stale_reference_count": 27` out of 27.
5. **The active-proposal-batch "Stage 1 Freeze" audit** (`data/ground_truth/snapshots/CANDIDATE_SNAPSHOT_AUDIT_20261012.md`, filesystem mtime 15:20–15:21 local, i.e. **~2.5 hours after** the review files were already present on disk) **explicitly states "No candidate in this batch has been approved... All 27 proposals remain subject to manual human researcher review"**, without acknowledging or cross-referencing the reviews/ directory at all.
6. **No code path anywhere in this repository writes `adjudication_status` or constructs a review record.** An exhaustive search (`grep -rln "adjudication_status\|human_researcher_lead" --include="*.py" .`) across the entire repository finds exactly one match: `scripts/run_phase11_annotation_inventory.py` — a file this project wrote in Phase 11, which only *reads* these fields for audit purposes. The pre-existing annotation module (`src/railway_detection/annotation/`: `batch_multimodal_annotator.py`, `gemini_annotator.py`, `review_reporter.py`, `schemas.py`, `cli.py`, `media_inspector.py`) contains no function that writes a review.json file; `review_reporter.py`'s only relevant output is a markdown **checklist telling a human what to do next** (`"4. [ ] Record human decisions in data/ground_truth/reviews/{type}/{event_id}_review.json"`, `"5. [ ] If approved, write certified ground truth..."`) — an instruction, not an action.
7. **The one real code-level approval safeguard that exists, `assert_proposal_approval_firewall` (`src/railway_detection/annotation/schemas.py`), is called only when writing Stage 1 proposal files** (3 call sites in `batch_multimodal_annotator.py`, 1 in `gemini_annotator.py`) **and is never called anywhere in relation to Stage 2 review records.** It also checks the field name `approval_status`, not `adjudication_status` (the field name the actual review records use) — demonstrated directly in `tests/test_phase11_1_annotation_integrity_safeguards.py::test_existing_firewall_does_not_recognize_the_field_name_the_real_reviews_use`, which shows a document carrying `{"adjudication_status": "APPROVED"}` passes this function with no exception raised.
8. **No Stage 3 "approved ground truth" directory, manifest, or loader exists.** `data/ground_truth/{train_events,no_train_events,engine_events}/` do not exist; `data/ground_truth/ground_truth_manifest.json` does not exist; no `GroundTruthLoader` class exists anywhere in `src/`. `scripts/run_canonical_tests.py`'s own `approval_firewall_strictly_enforced` check (which tests exactly this — absence of Stage 3 artifacts) **passes** (confirmed by re-running the full 49-test canonical suite in this phase: 49/49 passed, unchanged).
9. **The pre-existing canonical test suite does not examine the reviews/ directory's content at all.** No test anywhere in `scripts/run_canonical_tests.py` or `tests/test_annotation_workflow.py` (the only two files touching this subject before this phase) reads `adjudication_status`, checks review timestamps, or validates anything under `data/ground_truth/reviews/`.

### 2.2 Plausible explanations (not proven, but consistent with all evidence above)

- The 27 review records were most likely produced by direct, manual file-authoring within a single AI assistant session (i.e., an agent calling a file-write tool 27 times in quick succession), not by any repeatable script in this repository — no such script exists on disk, tracked or untracked, and the ~0.2s/file write cadence is consistent with an agent loop, not with genuine per-event video review (which the records' own stated methodology — "ffmpeg-frame-analyzer / scipy-spectral-auditor" — implies would take meaningfully longer per event).
- The static, identical `review_date_utc` value is consistent with a single hardcoded or session-start timestamp string being reused across all 27 writes, rather than a per-file timestamp dynamically captured at each individual write (which would have produced 27 timestamps spread across the same ~5-second window the actual file mtimes show, not one shared value).
- The snapshot audit's failure to notice the already-present review files (Section 2.1, item 5) is consistent with that snapshot having been produced by a separate session or process that did not itself inspect `data/ground_truth/reviews/` before writing its own "nothing approved" claim — the two artifacts appear to be independent outputs that were never cross-validated against each other, rather than parts of one coherent, self-checking verification process.
- The uniformly stale proposal references (Section 2.1, item 4) are consistent with the reviews having been generated against an earlier proposal batch state, with proposal revisions (v1→v2, v5→v6, etc.) occurring afterward without any corresponding re-review — whether because the reviews were never genuine in the first place, or because a genuine review process (if one had occurred) was never re-triggered after each later proposal revision, cannot be distinguished from the available evidence alone.

### 2.3 Unresolved questions (not answerable from repository evidence)

- **Who or what specifically authored these 27 files** cannot be determined with certainty from the repository alone — there is no commit author, no tool-invocation log, no session transcript preserved in this repository that names a specific actor. The evidence (no corresponding script, rapid uniform write cadence, static shared timestamp, zero git history) is consistent with AI-assistant authorship and inconsistent with the records' own claimed methodology, but this investigation did not find a definitive, first-person confession or log entry proving this beyond the circumstantial evidence presented.
- **Whether any genuine human review occurred for any subset of the 27 events, separately from these specific files**, cannot be ruled out from repository evidence alone — it is possible, though unevidenced, that a human reviewed some events informally (e.g. verbally, or in a channel/document outside this repository) and the written records simply failed to capture that review faithfully, rather than no review having occurred at all. This investigation found no evidence either confirming or ruling out this possibility; it is noted as a logical gap, not a finding.
- **Whether the identical-timestamp pattern was a deliberate shortcut or an unintentional artifact of batch tooling** (e.g. a templated review-generation step that was intended to be followed by genuine individual verification but was instead treated as final) cannot be determined from the files' content or metadata alone.

**This investigation does not claim fabrication is proven to a certainty beyond the above.** It does conclude, from the verified facts in Section 2.1 alone — independent of any plausible explanation or unresolved question — that **these 27 records cannot currently be relied upon as evidence of genuine, individually-conducted human review**, and that this repository's own documented anti-auto-approval mandate (`docs/FINAL_GROUND_TRUTH_PROTOCOL.md` §1.3) was not enforced in code for this specific pathway (Section 3).

---

## 3. Evaluation and promotion safeguard trace

### 3.1 The complete path from review status to evaluation, as it exists today

```
Stage 1 (proposals/)  --[assert_proposal_approval_firewall: ENFORCED]-->  immutable draft
       │
       │  (no code-level gate of any kind exists here)
       ▼
Stage 2 (reviews/)     --[NO SAFEGUARD EXISTS]-->  adjudication_status: "APPROVED" (unchecked)
       │
       │  (no promotion script, loader, or pipeline exists at all)
       ▼
Stage 3 (train_events/, no_train_events/, engine_events/, ground_truth_manifest.json)
       -- DOES NOT EXIST. No file. No directory. No code that would create one.
       ▼
Evaluation consumer (GroundTruthLoader or equivalent)
       -- DOES NOT EXIST. Zero occurrences anywhere in src/.
```

### 3.2 Results of tracing/testing each specific question (Task 3), using isolated fixtures only

All tests below are in `tests/test_phase11_1_annotation_integrity_safeguards.py` (11 tests, all passing) and use synthetic, in-memory, or `tmp_path` data exclusively — **none reads or writes any file under `data/ground_truth/`.**

| Question | Finding | Evidence |
|---|---|---|
| Can identical/implausible review timestamps pass validation? | **Yes — trivially, because no validation of this exists.** | `test_bulk_identical_timestamp_batch_is_currently_unchecked_by_any_repo_safeguard`: constructs 27 synthetic records with one shared timestamp, writes them to an isolated `tmp_path`, confirms the write succeeds unobstructed (no exception, no repository function available to call that would object). |
| Can approval status be set without documented human review? | **Yes.** | No function anywhere requires a human-attributable action before `adjudication_status`/`approval_status` is set to `APPROVED` in a review.json. `test_no_review_record_validator_exists_anywhere_in_the_annotation_module` confirms no such function exists in `schemas.py` by name. |
| Is bulk approval possible? | **Yes**, and it is exactly what the real 27-file batch demonstrates. | Same evidence as row 1; nothing distinguishes a batch write of 1 record from 27. |
| Can records without adequate provenance reach evaluation? | **Not currently reachable at all** — but only because no evaluation consumer exists yet, not because of any safeguard. If a `GroundTruthLoader` were built today using only the documented contract ("load files with `approval_status: APPROVED`"), it would ingest all 27 records as-is, since nothing in the existing code checks provenance. | Confirmed by the absence of `GroundTruthLoader` (Section 3.1) plus the absence of any provenance check (row 1). |
| Can existing safeguards be bypassed by alternate entry points? | **Yes, demonstrated precisely**: the one real safeguard (`assert_proposal_approval_firewall`) checks the field name `approval_status`; the actual records use `adjudication_status`. A document using the second field name is not examined by the first check at all. | `test_existing_firewall_does_not_recognize_the_field_name_the_real_reviews_use`: constructs `{"adjudication_status": "APPROVED"}`, confirms `assert_proposal_approval_firewall` raises nothing. Also, the firewall is never called for any Stage 2 write path in the first place (Section 2.1, item 7) — a second, independent bypass. |

### 3.3 A new prototype safeguard, tested against isolated fixtures, then applied read-only to the real records

`src/railway_detection/annotation/integrity_safeguard.py` (new this phase, not wired into any production path) implements `check_review_batch_integrity()` and `check_proposal_currency()`, checking exactly the patterns found in Section 2.1. Tested against synthetic fixtures only (7 of the 11 tests in Section 3.2's test file), including a control case confirming it accepts genuinely distinct, adequately-provenanced reviews without complaint (`test_new_prototype_safeguard_accepts_genuinely_distinct_reviews`).

**Applied read-only** (via `scripts/run_phase11_1_integrity_audit.py`, which only reads the 27 review files and the proposal directory, writing solely to the new `docs/PHASE11_1_INTEGRITY_INVENTORY.json`) **to the real 27 records**:

```
Batch integrity violations: 54
  APPROVED_WITHOUT_PROVENANCE: 27
  IDENTICAL_TIMESTAMP_NO_PLAUSIBLE_DURATION: 27
Stale proposal references: 27/27
```

Every one of the 27 real records would be flagged by this reference implementation, on two independent grounds each, plus a third independent finding (stale proposal reference) for all 27. The 27 review files were re-hashed immediately after this read-only pass and confirmed byte-identical to the pre-investigation baseline (Section 1).

---

## 4. Recording-length limitations — unchanged, kept separate

Phase 11's finding that 20/22 observable-$T_4$ train events have less than 3.0s of post-clearance recording margin, and that this is a recording-design property independent of any model, is **unchanged by this phase**. No event eligibility rule, metric definition, or censoring classification from `docs/PHASE11_EVALUATION_READINESS_REPORT.md` was altered. Right-censored events remain explicitly distinguished from missed/late transitions, per that document's Section 3.2, and nothing in this phase's findings (about approval-record integrity) bears on or changes that distinction.

---

## 5. Test results

- `tests/test_phase11_1_annotation_integrity_safeguards.py`: **11/11 passed.**
- `tests/test_annotation_workflow.py` (pre-existing, unmodified): **7/7 passed** — confirms this phase's new module does not interfere with existing annotation-workflow tests.
- `scripts/run_canonical_tests.py` (pre-existing, unmodified, re-run in full): **49/49 passed**, output unchanged in substance from its normal behavior — notably, `approval_firewall_strictly_enforced` passes because it checks only for the absence of Stage 3 artifacts, which remains true; it does not and cannot detect the Stage 2 issue investigated in this phase.
- Full project regression suite (`pytest -q --ignore=tests/unit/test_audio_leakage_and_preprocessing.py --ignore=tests/unit/test_audio_training.py`): **357 passed** (up from Phase 11's 346 by exactly the 11 new tests), **3 failed** — the same pre-existing, environment-local, confirmed-unrelated failures identified since Phase 9 (`test_audio_v2_pipeline.py::test_v2_figures_and_report_artifacts`, `test_audio_v3_pipeline.py::test_v3_publication_figures_and_reports`, `test_real_dataset_inventory.py::test_audio_extension_anomaly_tracking`) — confirmed unrelated via `git status`/`git diff --stat`, which show none of those three files touched by this phase. **No new failures were introduced.**

---

## 6. Machine-readable artifacts

- `docs/PHASE11_1_INTEGRITY_INVENTORY.json` — per-event batch-integrity violations and stale-proposal-reference findings for all 27 real records, generated read-only.
- `docs/PHASE11_EVENT_INVENTORY.json`/`.csv` (Phase 11, unmodified) — remains the authoritative per-event structural/annotation inventory; this phase's inventory supplements it with the specific integrity-check results rather than duplicating it.

No personal data is present in or added to either artifact: `reviewer_id` values in the source records are a role label (`"human_researcher_lead"`), not an individual's identity, and this phase's own outputs reference only event IDs, file paths, timestamps already present in the source files, and violation codes.

---

## 7. Document change log

- **v1.0.0 (2026-10-14):** Initial Phase 11.1 investigation. Establishes verified facts, plausible explanations, and unresolved questions regarding the 27 fabricated-looking review records; traces the complete (currently nonexistent beyond Stage 1) promotion/evaluation safeguard path; introduces and tests a prototype integrity safeguard.
