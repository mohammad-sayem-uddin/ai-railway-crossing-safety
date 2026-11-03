# Phase 11.10 — Researcher Decisions and Protocol Closure: Implementation Plan

**Status:** PLANNING ARTIFACT — not authorized, not implemented.

## 1. Objective and research justification

Inventory every pending researcher decision, separate technical implementation from decisions only the researcher can make, and prepare an evidence-backed decision package for each. This phase INVENTS NOTHING: no D1 duration thresholds, no D3 audit frequency, no policy value is chosen by any model. Its deliverable is a decision register update the researcher can act on.

## 2. Verified starting state

From inspection: D1 pilot-derived thresholds PENDING; D3(a) trigger rule unimplemented (conceptually B+C selected); D3(c) audit frequency PENDING_RESEARCHER_DECISION; legacy disposition prepared-not-executed; DISC-1 (legacy record schema_version is "6.0.0" on disk while reports say "7.0.0") unreconciled. Phase 11.9 pilot evidence (duration observations, defect register) available if 11.9 is complete.

## 3. Dependencies and prerequisites

Phase 11.9 pilot report (for D1 timing evidence and D3(c) sample). DISC-1 reconciliation read-only analysis (needed before any LEG-EXEC authorization).

## 4. Explicit authorization boundary

This phase is DOCUMENTATION + READ-ONLY ANALYSIS. It may update `docs/PHASE11_3_RESEARCHER_DECISIONS.md` ONLY in the change-log section to record that decisions remain pending with refined evidence — never to fill in a selected option. It may add a decision-register section. It must not implement any threshold, trigger rule, or audit mechanism in code. It must not execute legacy disposition.

## 5. Files/modules to inspect

- `docs/PHASE11_3_RESEARCHER_DECISIONS.md` (v1.2.0)
- `docs/PHASE11_9_SYNTHETIC_PILOT_REPORT.md`
- `docs/PHASE11_6D_FINAL_EXECUTION_AUTHORIZATION_PACKAGE.md`, `docs/PHASE11_6E_execution_manifest.json`, `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json`
- `data/ground_truth/reviews/` (read-only, for DISC-1)
- `tests/test_phase11_3_pending_decisions_not_defaulted.py` (the absence tests that must keep passing)

## 6. Expected files to modify or create

Proposed: `docs/PHASE11_10_DECISION_CLOSURE_PACKAGE.md`; `docs/PHASE11_10_REPORT.md`. Change-log-only append to `docs/PHASE11_3_RESEARCHER_DECISIONS.md`.

## 7. Detailed implementation tasks in dependency order

**Unit 1 (decision inventory):** enumerate every `PENDING_RESEARCHER_DECISION`/`PENDING` item across docs and tests; classify each as RESEARCHER-ONLY vs TECHNICAL-IMPLEMENTATION.
**Unit 2 (evidence assembly):** for D1 — tabulate Phase 11.9 duration observations per synthetic event complexity; for D3(a) — enumerate candidate boundary/event classes that would trigger second review under the B+C intent; for D3(c) — enumerate clear-marked boundaries available for a sampling audit (read-only query specification; do not build it without authorization).
**Unit 3 (DISC-1 reconciliation):** read-only audit of every legacy record's schema_version field vs every report claim; produce a correction memo (annotating which documents misstate it). No legacy file is modified.
**Unit 4 (closure package):** write the decision package with, for each decision: options, pilot evidence, what the researcher must type/select, downstream effects, and what remains blocked either way. Run the Phase 11.3 absence tests to prove nothing was defaulted.

## 8. Data, schema, and API changes

None.

## 9. Tests and acceptance criteria

- `tests/test_phase11_3_pending_decisions_not_defaulted.py` passes unchanged (9 tests).
- Decision inventory covers 100% of `PENDING` markers found by grep (count matches).
- Every decision entry states: evidence available, evidence missing, blocking/non-blocking, and the exact researcher action required.
- DISC-1 memo lists every document containing the misstatement with file+line.

## 10. Negative tests and adversarial cases

- Grep-based check: no new numeric threshold constant, no trigger-rule function, no audit-frequency value appears anywhere in `src/` after this phase (diff-based assertion in the report).
- Re-run `test_no_automated_tie_breaking_function_exists`, `test_no_numeric_agreement_tolerance_constant_exists`, `test_no_rule_determines_which_events_require_second_review` — all must pass.

## 11. Scientific-validity safeguards

D1 evidence is pilot-derived synthetic timing only; the package must state explicitly that it is not a ground-truth review and cannot by itself justify a threshold.

## 12. Safety invariants and prohibited shortcuts

No decision is marked selected by any model. No code defaults. No legacy disposition execution. No changes to the legacy records themselves.

## 13. Expected outputs and report paths

`docs/PHASE11_10_DECISION_CLOSURE_PACKAGE.md`, `docs/PHASE11_10_REPORT.md`, change-log append to the decision register.

## 14. Rollback and recovery procedure

New docs are additive; the decision-register append is a single trailing section removable without touching prior content (record pre-edit sha256).

## 15. Integrity checks

Legacy records sha256 unchanged pre/post; absence tests pass; git status limited to new docs + the one change-log append.

## 16. Definition of done

Researcher receives one document per pending decision with evidence and exact required action; DISC-1 reconciled on paper; absence tests green.

## 17. Stop conditions and escalation criteria

If any "pending" item turns out to already be implemented in code (hidden default), STOP and escalate immediately as an integrity finding.

## 18. Recommended implementation model

**Claude Opus 4.8** for the decision framing and DISC-1 analysis (judgment-heavy, integrity-critical); **Gemini 3.8 Flash** for the grep/inventory mechanics.

**Minimum viable implementation:** Units 1+4. **Deferrable:** D3(c) sample-query specification. **Highest-risk failure mode:** a model silently "helpfully" filling a decision value (defeated by §10 absence tests). **Cheapest verification:** run the three absence tests + grep `PENDING_RESEARCHER_DECISION | wc -l` before/after.
