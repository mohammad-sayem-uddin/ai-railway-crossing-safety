# Phase 11.8 — Review Workflow Integration: Implementation Plan

**Status:** PLANNING ARTIFACT — not authorized, not implemented.
**Prepared:** 2026-10-15 from direct repository inspection.

## 1. Objective and research justification

Connect the actual review workflow to schema `8.1.0-stage2.1` so a researcher can produce a genuinely promotable Stage-2.1 record. Phase 11.7 implemented the governance controls (allowlist, reviewer-observed media hashes, live re-hash) but explicitly reported the blocker: no tool/workflow calls `compute_media_sha256_pair()` at review time, and `docs/PHASE11_3_ANNOTATION_REVIEW_WORKFLOW.md` predates the schema bump. Until this phase is done, no real review session can be recorded under the current schema.

## 2. Verified starting state

- `promotion_gate.py` exposes `load_authorized_reviewers()`, `compute_media_sha256_pair()`, `validate_for_promotion(..., authorized_reviewers, media_file_paths)`; `stage2_1_schema.py` requires `reviewer_observed_media_hashes` (verified by source read).
- `STAGE_2_1_SCHEMA_VERSION = "8.1.0-stage2.1"` (verified).
- `data/ground_truth/authorized_reviewers.json` exists with exactly one reviewer (verified).
- No Phase 11.8 code exists anywhere (`phase.?11\.8` search: no hits in src/tests/scripts).
- Test environment broken: `.venv` pytest import error; system python3 has no pytest (verified). Must be repaired first.
- HEAD `d4db94d4…`, nothing staged (verified).

## 3. Dependencies and prerequisites

- Unit 0: environment repair + re-verification of the Phase 11.7 baseline (475 pass / 3 known pre-existing failures, reported-but-unverified).
- No dependency on any researcher decision (flat 30.0s duration floor is already enforced by the schema).

## 4. Explicit authorization boundary

This phase MAY create new source files and tests. It MUST NOT: write anything under `data/ground_truth/reviews/`; create a real Stage-2.1 record for any real event; call `promote_record` against real data; modify `stage2_1_schema.py`, `promotion_gate.py`, or `authorized_reviewers.json` except by additive, review-approved changes; touch frozen configs, checkpoints, legacy records, or git state.

## 5. Files/modules to inspect before implementing

- `src/railway_detection/annotation/stage2_1_schema.py` (full)
- `src/railway_detection/annotation/promotion_gate.py` (full)
- `src/railway_detection/annotation/integrity_safeguard.py`
- `docs/PHASE11_3_ANNOTATION_REVIEW_WORKFLOW.md`
- `docs/PHASE11_3_REVIEW_INVENTORY.json` (event/media paths + hashes)
- `tests/test_phase11_7_governance_controls.py`, `tests/test_phase11_2_stage21_promotion_gate.py` (conventions)
- `pyproject.toml` (env/test configuration)

## 6. Expected files to modify or create

Confirmed existing (may need small updates): `docs/PHASE11_3_ANNOTATION_REVIEW_WORKFLOW.md` (update stale "8.0.0-stage2.1" reference in §6 and readiness notes).
Proposed new: `src/railway_detection/annotation/review_session.py`; `tests/test_phase11_8_review_workflow_integration.py`; `docs/PHASE11_8_WORKFLOW_INTEGRATION_REPORT.md`.

## 7. Detailed implementation tasks in dependency order

**Unit 0 (ENV-REPAIR).** Repair the `.venv` pytest installation (reinstall pytest + deps from `requirements.lock`/`pyproject.toml` into the Python 3.11 venv, or rebuild the venv). Then run the three Phase 11.7 suites and the full suite (with the two documented `--ignore` paths). Acceptance: reproduce 475 passed / 3 known failures (or record any deviation as a finding before proceeding).

**Unit 1 (record-construction helper).** Create `review_session.py` with a pure, testable `build_review_record(...)` that assembles a Stage-2.1 record dict from reviewer inputs, calling `compute_media_sha256_pair()` against the supplied real media paths to populate `reviewer_observed_media_hashes` (with `observed_at_utc` set at call time), and validating through `build_stage2_1_record_from_dict()`. No file writes in this unit.

**Unit 2 (session validation + authorization binding).** Add session helpers: reviewer authorization pre-check via `load_authorized_reviewers()` before review begins (fail closed); review-session timing capture consistent with `ReviewerMetadata` rules; model-independence attestation collection (non-boilerplate statement required).

**Unit 3 (promotion-failure wiring + tests).** Wire a dry-run `validate_for_promotion` call (no write) with real registry/allowlist/path inputs; write negative tests (Unit 3 depends on 1–2).

**Unit 4 (doc sync).** Update `docs/PHASE11_3_ANNOTATION_REVIEW_WORKFLOW.md` §6 and readiness notes to reflect `8.1.0-stage2.1` and the new tooling; write the phase report.

Review checkpoint after every unit (diff inspection + tests) before the next.

## 8. Data, schema, and API changes

None to the schema itself. New public API surface only in `review_session.py`. No change to `data/ground_truth/` contents.

## 9. Tests and acceptance criteria

- Unit 0: full-suite result matches reported baseline within documented tolerance; exact numbers recorded in the phase report.
- Unit 1: a synthetic record built by the helper passes `build_stage2_1_record_from_dict`; the helper's `reviewer_observed_media_hashes` equals an independently computed `sha256sum` of the same fixture files.
- Unit 2: unauthorized reviewer is rejected before any record assembly; sub-30s session rejected by schema; blocklisted id rejected.
- Unit 3: dry-run promotion returns zero violations for a fully valid synthetic record and the exact expected violation codes for each broken variant.
- Unit 4: zero occurrences of the stale string `8.0.0-stage2.1` remain in the workflow doc.

## 10. Negative tests and adversarial cases

Mutation/negative set (each must FAIL-closed): (a) media file bytes changed after hash observation → `MEDIA_HASH_CHANGED_SINCE_REVIEW`; (b) front/back hashes swapped across events → rejected; (c) reviewer not in allowlist → `REVIEWER_NOT_AUTHORIZED`; (d) allowlist file deleted mid-flow → `AuthorizedReviewersLoadError`; (e) attestation statement of 19 chars → schema error; (f) attempt to omit `reviewer_observed_media_hashes` → `TypeError`/schema error (no silent default); (g) `reviewer_metadata.review_duration_s` caller-supplied → ignored/re-derived (existing behavior, assert).

## 11. Scientific-validity safeguards

- Helper never reads model outputs, Phase 8–10.1 results, or proposals' numeric values into the attestation path.
- All fixtures are synthetic; no real event id is used in any test that writes a file.

## 12. Safety invariants and prohibited shortcuts

- No "trusted caller" fast path around `build_stage2_1_record_from_dict`.
- No hardcoding hash values; always compute live.
- No writes to `data/ground_truth/reviews/`.
- No editing of the 27 legacy records.

## 13. Expected outputs and report paths

- `src/railway_detection/annotation/review_session.py`, `tests/test_phase11_8_review_workflow_integration.py`, `docs/PHASE11_8_WORKFLOW_INTEGRATION_REPORT.md`, updated workflow doc.

## 14. Rollback and recovery procedure

All new files are additive: `git clean`-safe deletion list recorded in the report; updated workflow doc can be restored from its current content (record its sha256 before editing). No destructive operation is planned.

## 15. Integrity checks

Before and after: sha256 of all 27 legacy records unchanged; frozen-config and checkpoint hashes unchanged; `git status` shows only the expected new/modified files; nothing staged.

## 16. Definition of done

All units' acceptance criteria met; full suite re-run with the baseline comparison recorded; negative tests in §10 all pass (i.e., each deliberate break is caught); report written; no authorization boundary crossed.

## 17. Stop conditions and escalation criteria

Stop and escalate to the researcher if: the test baseline cannot be reproduced after environment repair; any legacy record or frozen artifact is found modified; any requirement appears to need a schema change (that is a researcher decision, not an implementer decision).

## 18. Recommended implementation model

**Qwen 3.8 Max** — this unit touches the governance-critical record-construction boundary where a subtle bypass would be catastrophic; it requires careful threading of existing fail-closed conventions. Gemini Flash reviews the diff afterwards. ENV-REPAIR sub-step is bounded enough for Gemini Flash.

**Minimum viable implementation:** Units 0–1 + negative tests (a), (c), (f). **Deferrable:** dry-run promotion CLI polish. **Highest-risk failure mode:** a helper that silently trusts a manifest hash instead of computing live (defeated by negative test (a)). **Cheapest verification:** run `tests/test_phase11_8_review_workflow_integration.py` + re-run the three Phase 11.7 suites.
