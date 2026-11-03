# Phase 11 — Synthetic Engineering Status and Closure Boundary

**Status:** Synthetic-only runner/readiness engineering slice verified; Phase 11 research/governance closure remains OPEN.
**Verification date:** 2026-10-16.

## What engineering validation establishes

- The Phase 11.11 runner is restricted to synthetic-prefixed event IDs and paths
  resolving beneath OS temporary storage. It never promotes records.
- Media and proposal references are checked at session start, before preview,
  before writing, and media is checked again immediately before atomic
  create-only publication. Runtime media/proposal symlink resolution is
  revalidated so a path replaced after session construction cannot redirect a
  read outside temporary storage.
- Preview confirmation remains digest-bound; record staging is schema-checked;
  file creation uses a same-directory temporary file and atomic create-if-absent
  linking; concurrent duplicates do not overwrite existing output.
- Tests use synthetic event IDs, deterministic temporary media, synthetic
  reviewer identifiers, and pytest temporary output directories. A synthetic
  status string such as `APPROVED` in a test fixture is not a genuine approved
  annotation, human-review record, or ground-truth claim.
- The Phase 11.12 readiness gate and Phase 12 loader have synthetic regression
  coverage. That does not make the real repository READY or authorize evaluation.

## Independently rerun validation

```text
.venv/bin/python -m pytest tests/test_phase11_11_adjudication_session.py -q
26 passed

.venv/bin/python -m pytest tests/test_phase11_12_readiness_gate.py tests/test_phase12_ground_truth_loader.py -q
21 passed

.venv/bin/python -m pytest tests/test_phase11_1_annotation_integrity_safeguards.py tests/test_phase11_2_stage21_promotion_gate.py tests/test_phase11_3_pending_decisions_not_defaulted.py tests/test_phase11_8_review_workflow_integration.py tests/test_phase11_9_synthetic_pilot.py -q
80 passed

.venv/bin/python -m pytest tests/unit/test_phase14_profiler.py tests/unit/test_research_contracts.py -q
83 passed
```

Compilation of the changed Python modules succeeded. A repository-wide
`git diff --check` reports whitespace warnings in unrelated pre-existing dirty
files; those files were not normalized as part of this work.

## What remains open (not satisfied by engineering tests)

- The Phase 11.10 closure package cited by the old report is missing. The
  additive reconciliation is `docs/PHASE11_10_RECONCILIATION.md`; Phase 11.10
  remains incomplete until the package is reconstructed from source evidence
  and researcher-owned decisions are recorded through the required process.
- D1 numeric thresholds and D3(c) audit method/frequency remain unresolved.
- Legacy disposition remains unexecuted. The 27 legacy records remain untouched
  and are not approved ground truth.
- ADJ-AUTH and genuine human review have not been evidenced. No real
  Stage-2.1 adjudication is claimed.
- EVAL-AUTH, an event-level split decision, and R04 scope decisions remain
  necessary before Phase 12 evaluation. Synthetic gate READY fixtures are not
  repository readiness or permission to evaluate.

## Closure determination

**Phase 11 synthetic engineering work covered here: CLOSED for the tested scope.**
**Phase 11 overall: NOT CLOSED.** Research evidence, decision closure, genuine
adjudication, legacy disposition, and authorization gates are still outstanding.
No genuine ground truth or scientifically valid evaluation result is claimed.

---

## Additive update — 2026-10-16 (same day)

Appended; nothing above was altered. The four suite counts recorded above were
independently re-run and still hold exactly (26, 21, 80, 83 passed).

### Deliverable gap closed

The first bullet under "What remains open" said the Phase 11.10 closure package
was missing. **It is now present** at
`docs/PHASE11_10_DECISION_CLOSURE_PACKAGE.md`, reconstructed from traceable
repository evidence, and the schema-version citation inventory it required is
complete. Phase 11.10's *researcher-owned* items remain open; its *deliverable*
no longer does.

### Engineering added in this slice

| Change | Status |
|---|---|
| Experiment-registry path injection (`--registry-path`, `RAILWAY_EXPERIMENT_REGISTRY`) plus a session guard that fails the suite if the tracked registry is mutated | `IMPLEMENTED_AND_TESTED` |
| Readiness gate emits structured, machine-readable blockers (`ReadinessBlocker`, `to_dict()`, `blocker_codes`) | `IMPLEMENTED_AND_TESTED` |
| `check_review_batch_integrity` wired into the readiness gate as a blocking condition | `IMPLEMENTED_AND_TESTED` |
| Batch integrity made Stage-2.1-aware (reads provenance from `reviewer_metadata`, derives duration from the session window) | `IMPLEMENTED_AND_TESTED` |
| New `OVERLAPPING_REVIEW_SESSIONS` check — one reviewer cannot hold two simultaneous review windows | `IMPLEMENTED_AND_TESTED` |
| `railway-readiness` CLI: machine-readable Phase 12 handoff report, fail-closed exit codes | `IMPLEMENTED_AND_TESTED` |
| `plan_invalidation_notices()` dry-run planner for legacy disposition, writes nothing | `IMPLEMENTED_AND_TESTED` |

Broad regression after these changes: **692 passed, 3 failed** (the three
pre-existing missing-artifact failures, unchanged), registry byte-identical.

### Defect found and corrected in the synthetic pilot fixture

The Phase 11.9 fixture gave all three synthetic records the **same** review
window under the **same** reviewer, i.e. one reviewer reviewing three events
simultaneously. That is internally implausible even as synthetic data, and it
only became visible once the batch-integrity check was wired into the gate. The
fixture now staggers sessions sequentially (`SESSION_GAP_S`). No assertion was
weakened; the fixtures remain explicitly synthetic.

### Readiness against the real corpus

```text
PYTHONPATH=src .venv/bin/python -m railway_detection.annotation.readiness_cli
ready: false   blockers: 30   exit code: 2
  27  LEGACY_OR_UNKNOWN_SCHEMA
   3  MISSING_COHORT_APPROVAL
```

This is the correct outcome, not a defect: no approved ground truth exists, so
readiness is refused. Every verdict — including READY — carries
`researcher_approval_still_required: true` and
`ground_truth_approval_authority: "human_researcher_only"`.

### Closure determination unchanged

**Phase 11 overall: NOT CLOSED.** D1's numeric values, D3(c)'s audit mechanism,
ADJ-AUTH, genuine human review, LEG-EXEC, and EVAL-AUTH all remain outstanding.
No genuine ground truth and no scientifically valid evaluation result is claimed.

---

## Additive update — 2026-10-16 (approval reconciliation)

Full analysis: `docs/APPROVAL_RECONCILIATION_REPORT.md`. Summary:

- The researcher's 2026-10-16 statement that annotations were approved and authorization granted is **recorded** but is not machine-verifiable and corresponds to no artifact. It conflicts with the repository's own researcher records (D-2: researcher did not write the 27 files; 2026-10-14 confirmation of full invalidation). The 27 legacy `6.0.0` records stay refused; no migration was added because Stage-2.1 evidence cannot be derived from them without fabrication (`docs/LEGACY_REVIEW_RECONCILIATION.json`, generated read-only).
- Verifier defects fixed: unconditional `EVAL_AUTH_*` blockers; unconditional `STAGE21_PROMOTION_VALIDATION_REQUIRED` (the gate could never become ready); blocker de-duplication that reported 27 legacy files as 23; decision artifacts accepting any `decided_by` string.
- Defined and implemented: EVAL-AUTH as a recorded, hash-bound, explicitly *unsigned* researcher statement; a promotion receipt issued by the media-hashing readiness CLI.
- Remaining blockers (35) are missing human evidence or research decisions, not verifier defects. **Phase 11 overall remains NOT CLOSED.**

---

## Additive update — 2026-10-16 (overnight): defects found in the corpus-shaped path

- **Cohort-qualified identity.** `event_001` exists in three cohorts (and `event_002` in two). The readiness gate counted three approved `event_001` records as a duplicate, and the readiness CLI's inventory/proposal loaders keyed by the bare id so the last cohort overwrote the others — a genuine, valid corpus would have been refused or mis-verified. Fixed with qualified keys (lookups prefer `cohort/event_id`; bare ids remain for single-cohort callers). Regression tests: `tests/test_phase11_cohort_qualified_identity.py`.
- **Promotion receipt v2** now binds the review records, allowlist, annotation inventory and active proposals plus its own content hash; editing any input after issue, a new proposal version, or a recomputed-self-hash forgery is refused (`tests/unit/test_phase12_governance.py`, receipt-lifecycle section).
- **Manifest cannot vouch for itself:** events must be inventory identities with matching cohort; test events need approved records.
- **Blockers explain themselves:** `cause_class`, `verification_evidence`, `insufficient_because`, `required_artifact`, `remedy`, `category`.
- **Read-only audit:** `scripts/audit_ground_truth_readiness.py` (legacy counts, schemas, reviewer matches, shared timestamps, superseded proposals, eligibility, record hashes, per-cohort requirements, receipt state, LEG-EXEC preflight). The preflight verified the pinned proposal hash (`41cbbba3…`), 27 sources and 28 output targets (all `WOULD_WRITE`) and performed **zero writes**; LEG-EXEC remains **not authorized**.
- Phase 11 overall remains **NOT CLOSED**.
