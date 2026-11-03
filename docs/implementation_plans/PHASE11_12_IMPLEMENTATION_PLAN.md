# Phase 11.12 — Adjudication Closure and Evaluation-Readiness Gate: Implementation Plan

**Status:** PLANNING ARTIFACT — not authorized, not implemented. Ground truth is NOT approved automatically.

## 1. Objective and research justification

Reconcile and close the Phase 11.11 adjudication output, verify every integrity property of the produced records, document what remains unresolved, and implement the fail-closed evaluation-readiness gate that decides — with evidence — whether any named evaluation stage is justified. This is the boundary between ground-truth work and evaluation; getting it wrong poisons every downstream metric.

## 2. Verified starting state

Depends on Phase 11.11 completion: a known number of researcher-produced Stage-2.1 records exist; unresolved-boundary register exists; legacy disposition status known (executed or explicitly declined).

## 3. Dependencies and prerequisites

- 11.11 complete for the authorized scope.
- Legacy disposition resolved (LEG-EXEC) or explicitly declined — records carrying `supersedes` require it.
- D3(c) audit mechanism decided (11.10) if any clear-marked boundary is to be considered promotion-ready.

## 4. Explicit authorization boundary

MAY build reconciliation/verification tooling and the readiness gate. MUST NOT approve ground truth, name an evaluation stage, or start Phase 12 without separate EVAL-AUTH. The gate's default output is NOT_READY; only explicit researcher action flips it.

## 5. Files/modules to inspect

- `src/railway_detection/annotation/promotion_gate.py` (`validate_for_promotion`, `promote_record`, all rejection codes)
- `src/railway_detection/annotation/stage2_1_schema.py`, `integrity_safeguard.py`
- `docs/PHASE11_3_REVIEW_INVENTORY.json`, `docs/PHASE11_6G_EVALUATION_READINESS_REASSESSMENT.md` (prior verdict format)
- `docs/PHASE11_EVALUATION_READINESS_REPORT.md` + Addendum v1.1 (eligibility-table precedent)

## 6. Expected files to modify or create

Proposed: `src/railway_detection/annotation/evaluation_readiness_gate.py`; `tests/test_phase11_12_readiness_gate.py`; `docs/PHASE11_12_ADJUDICATION_CLOSURE_REPORT.md`; updated eligibility table (recomputed from approved records only).

## 7. Detailed implementation tasks in dependency order

**Unit 1 (reconciliation):** for every event in the 11.11 scope: record present? status resolved (APPROVED/REJECTED only)? media hashes re-verified live against both registry and `reviewer_observed_media_hashes`? reviewer in allowlist? history append-only and chronological? Produce a per-event reconciliation table.
**Unit 2 (unresolved register):** enumerate every boundary still UNCERTAIN/CENSORED/DISPUTED with reason; explicitly state which are site-survey-blocked vs resolvable; no unresolved label is silently dropped or force-resolved.
**Unit 3 (gate implementation):** `evaluate_readiness()` returns a structured verdict: READY_FOR_SPECIFIC_EVALUATION_STAGE(stage, evidence) | NOT_READY(blockers[]). Requirements: >=1 approved record per required cohort subset; all promoted records pass full `validate_for_promotion` with real media; legacy disposition resolved; D3(c) audit satisfied for clear-marked boundaries; no DISPUTED records in scope. Default: NOT_READY.
**Unit 4 (closure report):** closure statement + recomputed eligibility table + explicit list of what Phase 12 would still need.

## 8. Data, schema, and API changes

None to schema. New gate module. Promotion (`promote_record`) may be executed ONLY if the researcher authorizes promotion of specific records after seeing Unit 1's reconciliation table.

## 9. Tests and acceptance criteria

- Reconciliation covers 100% of in-scope events; table row count == scope size.
- Gate returns NOT_READY on an empty record set, on any DISPUTED record, on any hash mismatch, on a missing allowlist entry (parametrized negative tests).
- Gate returns READY only when ALL conditions hold (single positive test with fully valid synthetic records).
- Promoted-record count (if promotion authorized) == researcher-authorized count, verified by directory listing.

## 10. Negative tests and adversarial cases

Mutation tests: (a) tamper one byte of a reviewed media file → gate NOT_READY with MEDIA_HASH_CHANGED_SINCE_REVIEW; (b) delete one history entry → schema failure caught; (c) swap reviewer_id to a non-allowlisted identity → REVIEWER_NOT_AUTHORIZED; (d) remove the allowlist file → fail-closed load error; (e) inject a second APPROVED record for the same event → duplicate detected; (f) call the gate with a hand-built "all clear" dict bypassing reconciliation → structurally impossible (gate recomputes from records, never trusts caller claims). Each mutation must be demonstrated to flip the gate's verdict.

## 11. Scientific-validity safeguards

Eligibility table computed ONLY from approved Stage-2.1 records; candidate proposals never counted; no metric is produced in this phase.

## 12. Safety invariants and prohibited shortcuts

Gate has no override flag, no env-var bypass, no "force" parameter. Ground-truth approval is a researcher signature in the report, not a code return value. No Phase 12 scaffolding is started here.

## 13. Expected outputs and report paths

`docs/PHASE11_12_ADJUDICATION_CLOSURE_REPORT.md`; gate module + tests; readiness verdict recorded verbatim in the report and in `reports/progress.md` (append).

## 14. Rollback and recovery procedure

Gate module is additive; promotion outputs (if any) are per-record files listed in the report for rollback-by-deletion, but deletion of an approved record itself requires researcher authorization (it is ground truth once approved).

## 15. Integrity checks

Legacy records unchanged; media files unchanged (full re-hash of all reviewed media); frozen artifacts unchanged; git status limited to new files.

## 16. Definition of done

Reconciliation table complete; unresolved register complete; gate implemented with §10 mutations all demonstrated; closure report delivered with an explicit verdict; researcher informed that EVAL-AUTH is the next required action.

## 17. Stop conditions and escalation criteria

STOP if reconciliation finds a record whose hashes do not match (integrity incident — halt, do not repair silently); if >25% of in-scope events remain unresolved (readiness claim would be misleading); if any promotion-gate behavior differs from its documented rejection codes.

## 18. Recommended implementation model

**Qwen 3.8 Max** for Units 1+3 (fail-closed gate logic is high-consequence); **Gemini 3.8 Flash** for Unit 2 register mechanics; **Opus** reviews the gate design diff and the closure report before the verdict is recorded.

**Minimum viable implementation:** Units 1+3 core conditions. **Deferrable:** eligibility-table presentation polish. **Highest-risk failure mode:** a gate that trusts caller-supplied "already validated" claims instead of recomputing (defeated by mutation (f)). **Cheapest verification:** parametrized NOT_READY tests + one fully-synthetic READY test.
