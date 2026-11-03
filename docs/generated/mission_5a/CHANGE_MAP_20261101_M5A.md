# Mission 5A — Change Map

> **Status: IMPLEMENTATION RECORD — nothing here is an approval or an authorization.**
> **Process deviation (disclosed):** the instruction was to create the change map *before* editing. The planned change set was reasoned out first, but this written map was produced **after** the Phase 2 production-code edits and before any document work. Every document change below is a *new* file; no existing document was edited.

## A. Existing files modified (all in the working tree; none staged)

| File | Tracked? | Change | Why (decision) |
|---|---|---|---|
| `src/railway_detection/evaluation/metrics.py` | untracked | `classify_m4`, `M4Classification`, status/reason constants; `m4_premature_opening` now a compatibility view; `resolve_event_cohort` + `UnqualifiedEventIdError`; new `SingleEventEvaluation` fields; `evaluate_run` identity check, M4 via `classify_m4`, optional lead-in screen; `CohortEvaluationSummary` new counts | RD-016, RD-021, RD-040/041, TF-02 |
| `src/railway_detection/evaluation/clock_aware.py` | untracked | pass `cohort=truth.cohort` to `evaluate_run` | TF-02 plumbing |
| `src/railway_detection/evaluation/evaluation_runner.py` | untracked | pass `cohort=truth.cohort` to `evaluate_run` | TF-02 plumbing |
| `src/railway_detection/evaluation/execution_gate.py` | untracked | stale text ("design M4, not implemented") corrected | TF-03 |
| `src/railway_detection/experiments/preflight_validator.py` | untracked | four **PENDING** register entries + five aliases added (no approvals) | TF-05, RD-009 |
| `src/railway_detection/annotation/batch_multimodal_annotator.py` | untracked | legacy v6 guard `LegacyAnnotatorGuardError`; constructor fails closed unless `allow_legacy_v6_generation=True` | TF-13 |
| `tests/unit/test_event_metrics.py`, `test_mission2_pipeline_integrity.py`, `test_phase12_documented_metrics.py`, `test_phase12_metric_arithmetic.py` | modified/untracked | bare fixture event ids made cohort-qualified (mechanical) | TF-02 consequence |
| `tests/unit/test_mission4e2_m4_occupancy_contract.py` | untracked | Part 1 expectations updated to corrected production behaviour; test-local Part 3 reference removed; reformatted | RD-016 |

None of the 19 originally-modified tracked files was touched (the two protocol files, `evaluation/__init__.py`, etc. are byte-identical to the baseline).

## B. New files

**Code:** `src/railway_detection/evaluation/lead_in_screen.py` · `src/railway_detection/annotation/stage2_1_schema_proposed.py` (inactive; imported by no gate — asserted by test) · `scripts/mission5a_build_preservation_manifest.py`
**Tests:** `tests/unit/test_mission5a_production.py`
**Documents (`docs/generated/mission_5a/`):** this map; the two PROPOSED protocol files and their diffs; reconciliation, M4/M5, screen, schema, experiment-design, paper, governance-draft, ratification-draft, RD-matrix, blocker-register, reproducibility-manifest, snapshot-proposal and execution-report documents.

## C. Not touched

Both in-place protocols; `EXPERIMENT_DESIGN_FINAL.md`; `OPEN_DECISIONS_AND_BLOCKERS.md`; `RESEARCH_DECISIONS.md`; the paper draft; every canonical approval/authorization/manifest/ground-truth/split/readiness file; all configs (including `decision_policy_v1.yaml`, frozen config); `.git/`.
