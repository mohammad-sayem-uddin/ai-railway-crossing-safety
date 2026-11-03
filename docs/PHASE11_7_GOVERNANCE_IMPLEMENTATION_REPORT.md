# Phase 11.7 — Complete Stage 2.1 Governance Controls and Review Readiness

**Authorization boundary honored:** no real Stage-2.1 adjudication record was written for any real event; the legacy invalidation writer was never invoked; no original legacy review record was touched; Stage 3/Phase 12 not begun; frozen configs, checkpoints, and Phase 8 outputs unchanged. One new real file was created — `data/ground_truth/authorized_reviewers.json`, the allowlist itself, explicitly authorized by this phase's Task 2 ("Implement the missing reviewer allowlist") and containing only the one already-confirmed researcher identity (`raihankabirrahu@gmail.com`) — no additional reviewer was invented.

---

## Task 1 — Implementation status, verified by source inspection

Re-read `docs/PHASE11_3_RESEARCHER_DECISIONS.md` v1.2.0 and the actual code (not assumed from memory):

| Decision | Selected option | Status BEFORE this phase | Status AFTER this phase |
|---|---|---|---|
| **D1** | (D), pilot-derived thresholds | Mechanism (band) real since Phase 11.2's `MIN_PLAUSIBLE_REVIEW_DURATION_S`; numeric floor/upper-threshold `PENDING` | **Unchanged — still `PENDING`.** No threshold invented. `tests/test_phase11_3_pending_decisions_not_defaulted.py::test_review_duration_floor_is_a_plain_flat_constant_not_a_scaling_function` still passes, confirming no scaling function was added. |
| **D2** | (B), mandatory allowlist | Not implemented — file didn't exist, no code enforced it | **Implemented.** `load_authorized_reviewers()`, real allowlist file, enforced in `validate_for_promotion`/`promote_record`. |
| **D3** | B+C (part a) / A (part b) / new 3(c) | Not implemented — no second-review trigger logic, no tolerance constant, 3(c) mechanism unspecified | **Unchanged — still not implemented**, and deliberately out of this phase's scope (see Task 4). `test_no_automated_tie_breaking_function_exists`, `test_no_numeric_agreement_tolerance_constant_exists`, `test_no_rule_determines_which_events_require_second_review` all still pass. |
| **D4** | (B)+(C) combined | Not implemented — no live re-hash, no reviewer-observed-hash schema field | **Implemented.** `compute_media_sha256_pair()`, `reviewer_observed_media_hashes` (new required schema field, schema version bumped to `8.1.0-stage2.1`), live re-verification wired into `validate_for_promotion`. |

**Decisions were not silently converted into defaults.** D2 and D4 were implemented strictly per the researcher's own already-recorded selected option (not a different, easier option); D1 and D3 were left exactly as pending, with the pre-existing Phase 11.3 "absence" tests re-run to confirm no scaling function, tolerance constant, or second-review-trigger rule crept in anywhere during this phase's work.

---

## Task 2 — D2: mandatory reviewer allowlist

**Design.** `load_authorized_reviewers(allowlist_path: Path) -> frozenset[str]` (new, `promotion_gate.py`) reads and validates the allowlist, raising `AuthorizedReviewersLoadError` (fail-closed, never a partial/empty-but-accepted result) for: a missing file; invalid JSON; the wrong top-level shape; an empty list; a non-string/blank entry; a duplicate entry; or an entry that is itself on the pre-existing `REVIEWER_ID_BLOCKLIST` denylist (an allowlist containing a known-fabricated placeholder is itself untrustworthy). `validate_for_promotion`/`validate_batch_for_promotion`/`promote_record` all gained a new **required** (no default) `authorized_reviewers: frozenset[str]` parameter — a caller cannot accidentally omit it, since Python raises `TypeError` rather than silently skipping the check.

**Enforcement point.** Inside `validate_for_promotion`, after full schema validation succeeds (so the reviewer_id is known to be well-formed and non-blocklisted first), a new check (`REVIEWER_NOT_AUTHORIZED`) requires `record.reviewer_metadata.reviewer_id` to be present in the caller-supplied `authorized_reviewers` set. This is a lookup against EXTERNAL state the record itself cannot alter — a record cannot "change a field" to pass this, because the thing being checked is not read from the record, only compared against it. A direct test (`test_injecting_fake_authorization_field_into_record_rejected`) confirms a record that invents its own `reviewer_metadata.authorized: true` field fails schema construction outright (no such field exists on `ReviewerMetadata`), not a successful bypass.

**Real allowlist file.** `data/ground_truth/authorized_reviewers.json`, containing exactly one entry, `raihankabirrahu@gmail.com` — no additional reviewer was invented, per the task's explicit instruction.

**Tests** (in `tests/test_phase11_7_governance_controls.py` unless noted): authorized/unauthorized reviewer (`test_authorized_reviewer_passes`, `test_unauthorized_reviewer_rejected`); missing/malformed/wrong-shape/empty/blank/duplicate/blocklisted-entry allowlist (6 dedicated tests, each a distinct failure mode); an allowlist that revokes a previously-valid reviewer when updated (`test_altered_allowlist_revokes_a_previously_valid_reviewer`, proving the check is a live lookup, not a cached decision); the field-injection bypass attempt; a real-file sanity check (`test_real_allowlist_file_loads_and_contains_only_the_researcher`) confirming the actual repository file matches what was implemented.

---

## Task 3 — D4: media-hash verification

**Review-time.** `ReviewerObservedMediaHashes` (new dataclass, `stage2_1_schema.py`) is now a **required** field (`reviewer_observed_media_hashes`) on `Stage21ReviewRecord` — a record without it fails `build_stage2_1_record_from_dict` outright (schema version bumped `8.0.0-stage2.1` → `8.1.0-stage2.1`, following the exact same "old version is never valid" pattern that already rejects `7.0.0` records). `compute_media_sha256_pair(front_path, back_path)` (new, `promotion_gate.py`) is the utility a future review tool would call to populate this field from the actual files at review time.

**Promotion-time.** `validate_for_promotion` gained a second new **required** parameter, `media_file_paths: dict[str, dict[str, str]]`. When processing an event, it now live-re-hashes the actual raw files at the supplied paths and checks the result against **both**: (a) `media_sha256_registry`'s pre-computed entry (`MEDIA_HASH_CHANGED_SINCE_REGISTRY` if it disagrees — the file changed since the trusted manifest was built) and (b) the record's own `reviewer_observed_media_hashes` (`MEDIA_HASH_CHANGED_SINCE_REVIEW` if it disagrees — the file changed since this specific review happened, or the reviewer's recorded value was simply wrong). Missing files (`MEDIA_FILE_MISSING`) and missing/incomplete path entries (`MISSING_MEDIA_FILE_PATHS`/`INCOMPLETE_MEDIA_FILE_PATHS`) are separately, explicitly rejected.

**Binding, not just presence.** The check compares actual file *content* hashes, not path strings or registry entries alone — `test_path_substitution_with_different_content_rejected` proves that leaving a path unchanged but replacing the bytes at that path is caught; `test_media_hash_bound_to_specific_event_not_reusable_across_events` proves one event's real, valid media hashes cannot satisfy a different event's verification even when the files genuinely exist and hash correctly for *something* — binding is per-event, not "any valid hash somewhere."

**Never confused with the legacy-invalidation proposal hash.** `ReviewerObservedMediaHashes`'s docstring states explicitly that this is a separate hash from Phase 11.6C's `load_and_verify_proposal`/pinned proposal SHA-256 — one binds a disposition proposal to the document a human reviewed, the other binds a ground-truth review to the raw video a human watched. No code path or constant is shared between them.

**Tests**: correct hashes pass; incorrect registry hash rejected; media changed between review and promotion rejected (both `MEDIA_HASH_CHANGED_SINCE_REVIEW` and `MEDIA_HASH_CHANGED_SINCE_REGISTRY` fire together, since both references are now stale); missing media file rejected; path substitution with different content rejected; a tampered/fabricated `reviewer_observed_media_hashes` value cannot bypass verification (the live file simply doesn't match it); cross-event binding; `compute_media_sha256_pair` unit tests (missing file, and matches manual `hashlib` computation independently).

---

## Task 4 — D3 clear-case audit: documented, not implemented

**Status: still `PENDING_RESEARCHER_DECISION`, exactly as recorded in `docs/PHASE11_3_RESEARCHER_DECISIONS.md`'s existing Decision 3(c) entry ("Remaining action before implementation — Decision 3(c) specifically: the exact audit mechanism and frequency... is not specified... must be defined before the review workflow can enforce it").** This phase did not invent a frequency, a sampling rate, or an audit mechanism for boundaries a first reviewer marks clear/observable and that are not otherwise covered by the mandatory-second-review rule (uncertainty-flagged, or the fixed high-risk subset). No code in this phase implements or partially implements 3(c) — confirmed by the unchanged `test_no_rule_determines_which_events_require_second_review`.

**A safe, non-blocking preparation step, described but not built in this phase:** the schema and promotion gate already have everything needed to track *which* boundaries were adjudicated `OBSERVABLE` without `NEEDS_SECOND_REVIEW`/`DISPUTED` and outside the fixed subset — a future, narrowly-scoped addition could simply enumerate these from a batch of promoted records (a pure read/query function, no new schema field, no gate behavior change) to give the researcher a concrete list to sample from once they decide the audit frequency. This is deliberately **not implemented here**, since doing so would require making at least one small design choice (what counts as "the fixed subset" at code level, beyond the CSV it currently lives in) that is not this phase's to make — it is offered as a documented option for a future, explicitly-scoped follow-up, not a partial implementation of 3(c) itself.

---

## Task 5 — Synthetic test coverage

`tests/test_phase11_7_governance_controls.py` — **27 new tests**, all against `tmp_path` fixtures (the one exception: a single read-only load of the real `data/ground_truth/authorized_reviewers.json`, never a write, never a path under `data/ground_truth/reviews/`). Every item in Task 5's list is covered: authorized/unauthorized reviewers; missing/altered allowlist; correct/incorrect media hashes; media changed between review and promotion; missing media and path substitution; tampered review records (both the reviewer-id and the media-hash fields); bypass attempts (`no default value` structural proof via `inspect.signature`, plus `TypeError` on omission); no writes when validation fails (`promote_record` raising before any file touches disk, for both the allowlist and the media-hash failure modes).

`tests/test_phase11_2_stage21_promotion_gate.py` — all **33 pre-existing tests updated and still passing**: the new required `reviewer_observed_media_hashes` field added to the shared `_valid_record_dict()` fixture; new `authorized_reviewers`/`media_file_paths` arguments threaded through all 14 call sites. Exactly 2 tests (`test_valid_record_passes_promotion_validation`, `test_valid_record_can_be_promoted`) needed genuinely real, matching synthetic media files on disk, since they assert zero violations / successful promotion; the other 12 call sites' assertions check for a *specific* violation code (not an exact count), so deliberately non-existent placeholder paths were sufficient — several of them return early (legacy schema, invalidation marker, schema-validation failure) before the media check is ever reached at all.

`tests/test_phase11_3_pending_decisions_not_defaulted.py` — **updated, not broken**. Two of its original nine tests proved the ABSENCE of an allowlist; two proved the ABSENCE of media re-hashing/the new schema field. Since D2 and D4 are now genuinely, deliberately implemented (the opposite of a silent default — a recorded researcher choice, visibly built, separately tested), those four tests were replaced with their mirror-image equivalents confirming the implementation matches the *specific* selected option. The five Decision-1 and Decision-3 tests are **untouched and still pass**, correctly continuing to prove those two decisions remain unimplemented.

### Test results

```
$ venv/bin/python3 -m pytest tests/test_phase11_7_governance_controls.py -v
...27 passed

$ venv/bin/python3 -m pytest tests/test_phase11_2_stage21_promotion_gate.py -v
...33 passed

$ venv/bin/python3 -m pytest tests/test_phase11_3_pending_decisions_not_defaulted.py -v
...9 passed

$ venv/bin/python3 -m pytest tests/ -q --ignore=tests/unit/test_audio_leakage_and_preprocessing.py --ignore=tests/unit/test_audio_training.py
3 failed, 475 passed
```

The 3 failures are the **same pre-existing, confirmed-unrelated failures** seen continuously since Phase 9, reported separately as instructed: `test_audio_v2_pipeline.py::test_v2_figures_and_report_artifacts`, `test_audio_v3_pipeline.py::test_v3_publication_figures_and_reports`, `test_real_dataset_inventory.py::test_audio_extension_anomaly_tracking`. 475 = 448 (prior baseline) + 27 new (`test_phase11_7_governance_controls.py`); `test_phase11_2`/`test_phase11_3`'s counts are unchanged (33 and 9 respectively), just updated in place.

---

## Task 6 — Integrity and readiness audit

| Check | Result |
|---|---|
| 27 original legacy review records byte-identical to Phase 11.1 baseline | **Confirmed**, re-hashed fresh |
| No invalidation notices created anywhere | **Confirmed**, `find ... -iname "*notice*" -o -iname "*invalidat*"` empty |
| No real Stage-2.1 adjudication records written for any real event | **Confirmed** — no script or test in this phase called `promote_record` or any record-construction function against a real event_id or wrote to `data/ground_truth/` other than the one new, explicitly-authorized allowlist file |
| Frozen configs, checkpoints, Phase 8 outputs unchanged | **Confirmed** — three canonical config hashes unchanged, `verify_all_safeguards()` passed, Phase 8's 46-file output byte-identical |
| Git HEAD and staging unchanged | **Confirmed**, `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`, nothing staged |

---

## Updated Stage 2.1 readiness checklist

| Control | Status |
|---|---|
| Reviewer attribution (denylist) | ✅ Implemented since Phase 11.2, unweakened |
| Reviewer attribution (**mandatory allowlist**, Decision 2) | ✅ **Implemented this phase** |
| Minimum review-session duration (flat floor) | ✅ Implemented since Phase 11.2 (`30.0s`) |
| Minimum review-session duration (**pilot-derived exact thresholds**, Decision 1) | ⏳ Still `PENDING` — requires a pilot of genuine reviews, out of scope here |
| Model-independence attestation | ✅ Implemented since Phase 11.2, unweakened |
| Media-hash verification (registry presence check) | ✅ Implemented since Phase 11.2 |
| Media-hash verification (**live re-hash at promotion + reviewer-observed hash at review**, Decision 4) | ✅ **Implemented this phase** |
| Append-only adjudication history | ✅ Implemented since Phase 11.2, unweakened |
| Four-state boundary uncertainty taxonomy | ✅ Implemented since Phase 11.2, unweakened |
| Disagreement/second-review trigger rules (Decision 3, part a) | ⏳ Still not implemented — explicitly out of scope this phase |
| Numeric disagreement tolerance (Decision 3, part b — none selected) | ✅ Correctly absent (option A, no tolerance, requires no code) |
| Clear-case audit mechanism/frequency (Decision 3(c)) | ⏳ Still `PENDING_RESEARCHER_DECISION` — documented, not invented (Task 4) |
| Legacy-record disposition execution | ⏳ Prepared, hash-pinned, researcher-scoped — execution authorization not given (Phase 11.6D–F) |

---

# Verdict: `READY_WITH_BLOCKERS`

**What changed from Phase 11.6G's `READY_FOR_RESEARCHER_ADJUDICATION`:** the two governance controls that were previously selected-but-unimplemented (Decisions 2 and 4) are now genuinely implemented and tested. This closes real gaps, but it does not itself clear the bar to an unqualified `READY_FOR_RESEARCHER_ADJUDICATION` restatement, because new, concrete prerequisites exist for the *first* formal review session specifically:

**Blockers to the first formal review session:**
1. A reviewer attempting to construct a real Stage-2.1 record today must supply `reviewer_observed_media_hashes` — meaning the review tool/workflow (not yet built; `docs/PHASE11_3_ANNOTATION_REVIEW_WORKFLOW.md` predates this schema change) must be updated to call `compute_media_sha256_pair()` against the real raw media at review time and populate this field, or review sessions cannot be recorded at all under the current (correct, intentional) schema.
2. Decision 1's exact pilot-derived duration thresholds remain unset — the existing flat `30.0s` floor still applies and is sufficient to *begin*, but is not the researcher's actually-selected final mechanism.
3. Decision 3(c)'s audit mechanism/frequency remains open — does not block beginning review of boundaries that ARE covered by the mandatory-second-review rule, but review of "clear" boundaries outside that rule has no defined audit process yet.
4. The legacy 27-record disposition remains unexecuted (Phase 11.6D–F, `NOT_AUTHORIZED`) — does not block beginning NEW Stage-2.1 review, but should be resolved (executed or explicitly declined) before any new record is positioned as *replacing* a specific legacy one.

**None of these four is a defect in what was built this phase** — D2 and D4 are fully implemented, tested, and fail-closed exactly as specified. They are the next, now more concretely scoped, steps before a human can sit down and actually produce the first real, promotable Stage-2.1 record.

**This verdict does not authorize Stage 3, Phase 12, legacy invalidation execution, or formal adjudication of any real event.**
