# Phase 11.2 — Stage-2.1 Schema and Ground-Truth Promotion Gate: Implementation Report

**Status:** Implementation complete, fully tested against synthetic fixtures. No annotation approved or invalidated. No model inference. No performance metric. No existing record modified. Phase 12 not begun.

**Builds on:** `docs/PHASE11_1_ANNOTATION_INTEGRITY_AUDIT.md` (the investigation), `docs/PHASE11_1_REMEDIATION_PLAN.md` (the design this phase implements), `docs/PHASE11_GROUND_TRUTH_PROTOCOL.md` (the four-state censoring taxonomy, reused unchanged).

---

## 1. Preservation verification

- All 27 real review records (`data/ground_truth/reviews/*/event_XXX_review.json`): re-hashed against the Phase 11.1 preservation baseline at the end of this phase — **byte-identical, 27/27**, confirmed via `diff`.
- Phase 8 output (46 files): byte-identical to the baseline preserved since Phase 9. Phase 9/10/10.1 outputs: untouched.
- `configs/frozen_experiment_v1.yaml` (`999a7970...`), `configs/decision_policy_v1.yaml` (`051c908d...`), `configs/decision_policy_v2_candidate.yaml` (`143782d1...`): all unchanged, none modified.
- No checkpoint, model weight, or threshold touched. No new model inference. No performance metric computed anywhere in this phase.
- No existing proposal, snapshot, or raw media file modified.
- Git HEAD unchanged at `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`; nothing staged or committed.
- **No record was promoted to evaluation-ready status.** The one promotion call made against real data in this phase (Section 5) was read-only validation that writes nothing and modifies nothing — confirmed by hash re-verification immediately after.

---

## 2. Design decisions requiring researcher approval (flagged, not silently decided)

Per the brief's instruction to surface rather than silently invent defaults:

1. **`MIN_PLAUSIBLE_REVIEW_DURATION_S = 30.0`** — reused unchanged from Phase 11.1's `integrity_safeguard.py`, where it was derived as a floor consistent with the invalidated records' own stated frame-by-frame/spectral-audio methodology, not tuned to any outcome. **This is a sanity floor, not a claim that 30 seconds is sufficient for a genuine review** — the researcher may wish to set a stricter, event-complexity-aware threshold (e.g. scaled by `trailing_cars_count` or event duration) before real use; this phase did not invent such a scaling rule, since doing so would itself be an unapproved default.
2. **`REVIEWER_ID_BLOCKLIST`** — contains the exact string found in all 27 fabricated records (`"human_researcher_lead"`) plus a small set of generic role/placeholder terms. This list is necessarily incomplete (it cannot anticipate every possible future placeholder); the researcher may want to extend it, or replace it with an allowlist of known, real reviewer identities instead of a denylist, which would be a stronger but more operationally demanding control. This phase implements the denylist as the minimal viable version, not the final word.
3. **The annotation-level disagreement-resolution tolerance** (Section 5 of the remediation plan) was explicitly left unspecified by this phase, consistent with Phase 11.1's own caution that it must not be the Phase 11 evaluation protocol's ±0.4s system-resolution tolerance reused without a separately stated rationale. No numeric agreement tolerance is implemented anywhere in this phase's code — `DISPUTED` vs. resolved-agreement is a status the researcher (or a future tool under their direction) must set explicitly; nothing here infers it from a numeric comparison.
4. **Media-hash verification depth**: `validate_for_promotion` requires a caller-supplied `media_sha256_registry` with non-empty `front`/`back` entries, but does not itself re-derive those hashes from raw video files (that independent verification already exists, from Phase 11, in `data/manifests/layer_b_v2_annotation_inventory.json`). The researcher should decide whether a future promotion script should re-verify media hashes from the raw files at promotion time (stronger, slower) or trust the pre-verified manifest (faster, already independently checked in Phase 11) — this phase implements the interface generically enough to support either, without choosing.

---

## 3. The Stage-2.1 schema

**File:** `src/railway_detection/annotation/stage2_1_schema.py`. `STAGE_2_1_SCHEMA_VERSION = "8.0.0-stage2.1"` — a record with any other `schema_version` (including every one of the invalidated `"7.0.0"` records) is never accepted as a valid Stage-2.1 record by any code path in this module.

| Brief requirement | Implementation |
|---|---|
| Stable event/media identifiers incl. media hashes | `event_id`, `cohort`; `ProposalBinding.proposal_sha256` (64-char hex, validated via the existing `validate_sha256` reused from `schemas.py`); media hashes cross-checked at promotion time (Section 4), not duplicated into the review record itself (the proposal already carries them). |
| Exact binding to current proposal version | `ProposalBinding` validates internal well-formedness; *currency* (is this still the active version) is checked externally at promotion time (Section 4), since "current" is a time-varying, promotion-time fact the record itself cannot self-certify. |
| Individually attributed human reviewers | `ReviewerMetadata.reviewer_id`, checked against `REVIEWER_ID_BLOCKLIST` — the exact string from all 27 fabricated records can never be accepted again. |
| Review-session timestamps with validation | `review_start_utc`/`review_end_utc`, both required valid timezone-aware ISO-8601; `end > start` enforced; derived `review_duration_s` must be `>= MIN_PLAUSIBLE_REVIEW_DURATION_S`. The derived field is never trusted if caller-supplied (`build_stage2_1_record_from_dict` discards any incoming `review_duration_s` and recomputes it). |
| Explicit model-independence attestation | `ModelIndependenceAttestation`: `attested` must be `True`; `statement` must be a specific (>=20 char) statement, not boilerplate; `attested_at_utc` must be a valid timestamp. |
| Observable/unobservable/censored/uncertain states | `BoundaryAdjudication.state` — a formal enum (`BOUNDARY_STATES`) matching `docs/PHASE11_GROUND_TRUTH_PROTOCOL.md` Section 2's taxonomy exactly, replacing the prior schema's implicit `applicable`/`candidate_observable`/`ambiguity_flag` combination with one explicit field; `OBSERVABLE` requires `value_s`+`reference_camera`, every other state forbids `value_s`. |
| Disagreement / second-review outcomes | `adjudication_status` is one of `APPROVED / REJECTED / NEEDS_SECOND_REVIEW / DISPUTED`; `Stage21ReviewRecord.is_resolved` is `False` for the latter two; `second_review_of` links a second review to the first. |
| Append-only audit history | `adjudication_history`: non-empty list, validated chronologically non-decreasing, and its most recent entry's `status_set` must match the record's current `adjudication_status` (catches a record whose top-level status was changed without a corresponding history entry). |
| Separation of completion / approval / invalidation / eligibility | Completion = non-null `review_end_utc`. Approval = `adjudication_status == "APPROVED"`. Invalidation = a separate, optional top-level `invalidation` object the schema itself does not define a constructor for (Section 5) — its mere *presence* is what the promotion gate checks, deliberately kept outside the reviewer-authored schema so a reviewer cannot self-invalidate or un-invalidate their own record. Evaluation eligibility is **never a stored field** — it is the return value of `validate_for_promotion`, computed fresh every time, never a claim the record makes about itself. |

---

## 4. The fail-closed promotion gate

**File:** `src/railway_detection/annotation/promotion_gate.py`. `validate_for_promotion()` is a pure function (no I/O); `promote_record()` is the **only** function that writes a file, and it unconditionally calls `validate_for_promotion()` first — there is no second, faster, or "trusted" write path. `output_dir` is a required parameter with no default pointing at any real `data/ground_truth/` path.

Rejection coverage (every item the brief listed "at minimum"):

| Required rejection | Code | Mechanism |
|---|---|---|
| Legacy records without adequate provenance | `LEGACY_OR_UNKNOWN_SCHEMA` | Checked first, before any other field is read; returns immediately. |
| Stale proposal version references | `STALE_PROPOSAL_REFERENCE` | Compares `record.proposal_reference.proposal_sha256` against caller-supplied `active_proposal_sha256_by_event`. |
| Missing media identity / mismatched hashes | `MISSING_MEDIA_IDENTITY` / `INCOMPLETE_MEDIA_IDENTITY` | Requires both `front` and `back` entries in caller-supplied `media_sha256_registry`. |
| Missing reviewer attribution / attestations | Raised as `SCHEMA_VALIDATION_FAILED` (wraps `SchemaValidationError`) | Schema-level — a record missing these fields never successfully builds, so it never reaches the provenance checks. |
| Invalid review-session timestamps | Same — `SCHEMA_VALIDATION_FAILED` | End-before-start, malformed ISO-8601, or sub-30s duration all raise at schema-construction time. |
| Unresolved disagreements | `UNRESOLVED_DISAGREEMENT` | `NEEDS_SECOND_REVIEW`/`DISPUTED` fail `record.is_resolved`. |
| Missing/inconsistent event and annotation versions | `SCHEMA_VALIDATION_FAILED` (missing fields) + `STALE_PROPOSAL_REFERENCE` (inconsistent version) | Both paths covered. |
| Any attempt to promote unverified/invalidated record | `LEGACY_OR_UNKNOWN_SCHEMA` (unverified = wrong schema) + `RECORD_INVALIDATED` (explicit marker) | Both checked, both block unconditionally, both before any other check runs. |

`validate_batch_for_promotion()` additionally reuses Phase 11.1's `check_review_batch_integrity()` across the whole batch, catching cross-record issues (e.g. several records sharing an implausible timestamp) that no single-record check can see — directly reusing, not duplicating, the existing tested function.

---

## 5. Enforcement at the actual boundary — demonstrated, not asserted

The brief specifically warned against "a decorative validator that production code can bypass." This phase demonstrates, rather than merely claims, that the gate cannot be bypassed:

- `test_renaming_adjudication_status_to_approval_status_cannot_bypass`: a **valid** record has its `adjudication_status` key renamed to `approval_status` (mimicking the old Stage-1-only firewall's field name). Result: schema construction fails with a missing-field error; `validate_for_promotion` returns `SCHEMA_VALIDATION_FAILED`. It does not silently pass.
- `test_renaming_approval_status_variant_in_legacy_schema_still_rejected`: the reverse case — a legacy-schema (`7.0.0`) record that also happens to carry `adjudication_status: APPROVED` (i.e., structurally what the real 27 records look like) is rejected purely on `schema_version`, before `adjudication_status` is ever inspected.
- `test_invalidation_marker_blocks_promotion_even_if_otherwise_valid`: an otherwise-perfect record is still blocked the instant an `invalidation` object is present.
- `test_batch_level_identical_timestamp_bypass_blocked`: reproduces the real 27-record bulk-approval pattern at the batch level and confirms it is caught.
- **Applied read-only to the real 27 records** (no file written, no file modified — confirmed by re-hashing immediately after): every one of the 27 is rejected with `LEGACY_OR_UNKNOWN_SCHEMA`, since all carry `schema_version: "7.0.0"`. This is the gate functioning exactly as specified against the actual data it exists to protect, without ever touching that data.

---

## 6. Researcher-controlled invalidation (Task 5) — implemented, not executed

`propose_invalidation()` and `write_invalidation_proposal()` in `promotion_gate.py`. Builds a structured `InvalidationEvent` (event ID, reason, actor, authorized statement, timestamp, affected record's path and current SHA-256) by **reading** the affected record only to hash it — never writing to it. `write_invalidation_proposal()` appends to a caller-specified output file, preserving any prior entries.

**Authorization caveat, stated directly in the code's own docstring and here**: this repository has no real authentication or authorization system — no user accounts, no cryptographic signing, no role-based access control. `actor` and `authorized_statement` are a **documented convention**, not a security control. Anyone able to run this code can supply any string for either field. This phase does not pretend otherwise, and does not implement any stronger mechanism (e.g. a signing key, an external approval service) that this repository has no infrastructure to support honestly.

**Not executed against the real 27 records**: every test exercising these functions operates on synthetic `tmp_path` fixtures. No script in this phase calls `write_invalidation_proposal` with any real `data/ground_truth/reviews/` path. Confirmed structurally: `output_path` and `affected_record_path` are both required parameters with no default value in either function's signature (`test_invalidation_proposal_never_targets_the_real_reviews_directory`), so no accidental default could ever point at a real path.

---

## 7. Tests and exact commands run

```
venv/bin/python -m pytest tests/test_phase11_2_stage21_promotion_gate.py -v
# 33 passed

venv/bin/python -m pytest -q --ignore=tests/unit/test_audio_leakage_and_preprocessing.py --ignore=tests/unit/test_audio_training.py
# 390 passed, 3 failed, 1 warning
```

**33/33 new tests pass**, covering: 3 positive (valid record builds / validates / promotes), 14 schema-level negative cases (legacy schema, missing fields, blocklisted reviewer ID, short duration, end-before-start, failed attestation, boilerplate statement, observable-without-value, censored-with-value, empty/mismatched/out-of-order history), 5 promotion-level negative cases (stale proposal, missing/incomplete media, promotion raising and writing nothing), 4 disagreement cases (`NEEDS_SECOND_REVIEW`, `DISPUTED`, `REJECTED` distinctly handled, confirmed absence of any auto-resolution function), 4 bypass/mutation cases (field-renaming both directions, invalidation marker, batch-level collision), and 4 invalidation-proposal cases (missing reason/actor/authorization, never-modifies-affected-record, append-only, no default real path).

**Full project regression suite**: 390 passed (up from Phase 11.1's 357 by exactly the 33 new tests), **3 failed**. The 3 failures (`test_audio_v2_pipeline.py::test_v2_figures_and_report_artifacts`, `test_audio_v3_pipeline.py::test_v3_publication_figures_and_reports`, `test_real_dataset_inventory.py::test_audio_extension_anomaly_tracking`) are the **same pre-existing, environment-local failures** identified continuously since Phase 9 — re-confirmed unrelated to this phase via `git status`/`git diff --stat`, which show none of those three files touched. **No new test failures were introduced by this phase.**

---

## 8. Completion criteria, checked individually

1. ✅ Valid synthetic Stage-2.1 records pass validation — `test_valid_stage2_1_record_builds_successfully`, `test_valid_record_passes_promotion_validation`, `test_valid_record_can_be_promoted`.
2. ✅ Legacy and incomplete records fail closed — 14 dedicated schema-level tests, plus the real-27-records read-only pass (Section 5).
3. ✅ Stale proposal versions and mismatched media hashes rejected — `test_stale_proposal_reference_rejected`, `test_missing_media_registry_entry_rejected`, `test_incomplete_media_registry_entry_rejected`, `test_stale_proposal_promotion_raises_and_writes_nothing`.
4. ✅ Disagreement cannot be resolved automatically — `test_needs_second_review_status_rejected_from_promotion`, `test_disputed_status_rejected_from_promotion`, `test_no_automated_tie_breaking_function_exists` (confirms absence of any such function by name).
5. ✅ Promotion cannot bypass the full validator through alternate status-field names or entry points — `test_renaming_adjudication_status_to_approval_status_cannot_bypass`, `test_renaming_approval_status_variant_in_legacy_schema_still_rejected`; `promote_record` has exactly one code path, which always calls `validate_for_promotion` first.
6. ✅ The real 27 records and all protected experiment artifacts remain unchanged — re-verified in Section 1, including a post-investigation re-hash after the read-only gate pass against the real records.
7. ✅ No annotation approved or invalidated without explicit researcher authorization — nothing in this phase set any real record's status; `propose_invalidation`/`write_invalidation_proposal` were exercised only against synthetic data.
8. ✅ No inference or evaluation metrics produced — none anywhere in this phase.

---

## 9. Decision report

**Implemented**: a versioned Stage-2.1 schema (`stage2_1_schema.py`) enforcing individual reviewer attribution, timed and duration-validated review sessions, an explicit model-independence attestation, the formal four-state boundary taxonomy, and append-only adjudication history with internal consistency checks; a fail-closed promotion gate (`promotion_gate.py`) rejecting every category the brief specified, demonstrated (not merely asserted) to resist the specific field-renaming bypass found in Phase 11.1, and applied read-only against the real 27 records to confirm all are correctly rejected; a researcher-controlled, honestly-caveated invalidation-proposal mechanism, implemented and tested against synthetic data only.

**Remains unverified / explicitly deferred** (Section 2): the appropriate review-duration floor for events of varying complexity; whether the reviewer-ID control should be a denylist (implemented) or allowlist (not implemented); the numeric tolerance, if any, for reconciling two independent reviewers' boundary values; whether a future promotion script should re-verify media hashes from raw files or trust the existing Phase 11 manifest.

**Exact human actions required before genuine annotation review and Phase 12**:
1. Review and decide on the four open design questions in Section 2 (or explicitly accept this phase's defaults).
2. Execute one of the two non-destructive invalidation options from `docs/PHASE11_1_REMEDIATION_PLAN.md` Section 2 for the real 27 records (still not done — this phase implemented the *tooling* for invalidation proposals but did not apply it to the real records, per the brief's explicit constraint).
3. Begin genuine, individually-attributed re-review of all 27 events, producing real Stage-2.1 records via the schema this phase implements.
4. Only once real Stage-2.1 `APPROVED` records exist: build the actual Stage 3 writer (this phase built only the promotion *gate*, not a Stage 3 directory populator, per "build only the smallest well-defined promotion interface necessary").
5. Only then does `docs/PHASE11_EVALUATION_READINESS_REPORT.md`'s evaluation protocol become applicable to real, approved ground truth, and only then should Phase 12 begin.
