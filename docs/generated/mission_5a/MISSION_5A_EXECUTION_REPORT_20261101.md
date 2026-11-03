# Mission 5A — Execution Report

**Date:** 2026-11-01 · **Repo:** `/Users/sayemuddin/Desktop/Train_automation` · **Branch:** `main` · **HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (unchanged)
**Mode:** implementation of confirmed decisions only. **Nothing in this mission is an approval or an authorization.** Please review and accept Mission 5A before any further phase.

## 1. What was implemented (code, tested)

| Item | Where | Decision |
|---|---|---|
| Corrected six-case M4/M5 classification in production (`classify_m4`, `M4Classification`, reasons; strict interval; no tolerance; empty/short/sparse/missing-T4 handled; aggregation separates M4-evaluable / premature / no-violation / M5 / not-evaluable) | `src/railway_detection/evaluation/metrics.py` | RD-016, 017, 040 |
| Bare/contradictory event ids fail closed (`resolve_event_cohort`, `UnqualifiedEventIdError`); cohort passed from ground truth in the two official callers | `metrics.py`, `clock_aware.py`, `evaluation_runner.py` | TF-02, RD-024, 041 |
| Missed-train lead-in feasibility screen (insufficient lead-in ≠ system failure; provenance required; synthetic derivation of the minimum block latency = 3.6 s) | new `evaluation/lead_in_screen.py`; `evaluate_run` options; summary counts | RD-021 |
| Stale gate text corrected | `execution_gate.py` | TF-03 |
| Four governance identifiers added as **PENDING** (+ aliases); none approved | `preflight_validator.py` | TF-05, RD-009 |
| Legacy v6 annotator fails closed unless explicitly allowed | `batch_multimodal_annotator.py` | TF-13 |
| Preservation-manifest tool (build/verify, never opens media) | `scripts/mission5a_build_preservation_manifest.py` | RD-003 |

## 2. What remains only a proposal (documents or inactive module)

- **Proposed protocols** `…v9.1.0_PROPOSED.md`, `…v7.1.0_PROPOSED.md` (+ diffs). The in-place v9.0.0/v7.0.0 files are **byte-identical** to the baseline (hashes below). Applying the wording to the in-place files, committing, re-hashing and binding are left to you (RD-002/003).
- **Proposed Stage-2.1 schema** `stage2_1_schema_proposed.py` (inactive; imported by no gate — tested) and review-governance/hard-case pilot proposal.
- Protocol reconciliation report; experiment-design reconciliation; paper revision proposal (human authors only; AI-use disclosure **DRAFT**; no names invented); governance approval **drafts** (all blank); ratification **draft** for the 2026-10-30 items; RD-001…055 matrix; deferred/blocker register; preservation manifest and snapshot proposal.

## 3. Approvals still pending (researcher-authored artifacts do not exist)
D1 (`GOV-D1-PROTOCOL-AUTHORITY`) · D2/M4–M5 contract (`GOV-D2-EVALUATION-PROFILE`) · second-review triggers · clear-boundary audit · R04 scope (`GOV-D4-R04-SYNCHRONIZATION`) · thresholds · ROI · B7e parameters · event-split posture · descriptive real-data pathway · engine-exclusion record · inventory sign-off · **ratification of the 2026-10-30 transcribed items** · confirmation of one implementation choice (`no_steps_in_protection_interval`, §8).

## 4. Execution authorizations still pending
Media access · three-event/hard-case pilot · record writing · full Stage-2.1 review · promotion receipt · production replay/cache generation · inference · controlled experiments · real-data descriptive evaluation · official evaluation (EVAL-AUTH) · environment repair · Git commit/snapshot (yours).

## 5. Technical blockers remaining
Entry landmark (RD-006); full occupancy duration (RD-018); per-event direction; human confirmation of no-train clips; R04 official scope; B7e numerics; review tolerance; duration floor; audit criteria; reviewer identities; real-data descriptive pathway; wiring the screen into the official runner (provenance location undecided). Full list with unblock conditions: `DEFERRED_ITEMS_BLOCKER_REGISTER_20261101_M5A.md` (20 items).

## 6. Exact tests and results (all synthetic-only; run with `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`)

| # | Command (from repo root) | Result |
|---|---|---|
| 1 | `.venv/bin/python -m pytest tests/unit/test_mission5a_production.py -p no:cacheprovider -q` | **88 passed** |
| 2 | `.venv/bin/python -m pytest tests/unit/test_mission4e2_m4_occupancy_contract.py -p no:cacheprovider -q` | **57 passed** (expectations updated; test-local Part 3 reference removed) |
| 3 | `.venv/bin/python -m pytest tests/unit/test_event_metrics.py tests/unit/test_mission2_pipeline_integrity.py tests/unit/test_mission3_reproducibility_and_provenance.py tests/unit/test_mission4a_governance_and_stage21_safety.py tests/unit/test_mission4d_governance_integrity.py tests/unit/test_mission4e2_m4_occupancy_contract.py tests/unit/test_mission5a_production.py tests/unit/test_phase12_documented_metrics.py tests/unit/test_phase12_metric_arithmetic.py tests/unit/test_phase12_governance.py tests/unit/test_phase12_input_contracts.py tests/unit/test_phase12_official_replay.py tests/unit/test_phase12_evaluation_runner.py tests/unit/test_reproducibility_audit.py tests/unit/test_research_contracts.py tests/unit/test_cache_phase12_adapter.py tests/test_phase12_ground_truth_loader.py tests/test_phase11_12_readiness_gate.py tests/test_phase11_cohort_qualified_identity.py -p no:cacheprovider -q` | **606 passed** (run before the final one-line lint fix to a fixture and the manifest rebuild; re-run after it: tests 1 and 2 together **145 passed**; `test_phase12_documented_metrics.py` **6 passed**) |
| 4 | `.venv/bin/ruff check <changed files> --no-cache` | **All checks passed** for every new or wholly-owned file and for every region I edited. Pre-existing, untouched lint remains in `preflight_validator.py` (36), `batch_multimodal_annotator.py` (16 fixable) and `test_mission2_pipeline_integrity.py` (7 fixable); not fixed (unrelated code). ruff (0.16.3) was already in `.venv`; nothing was installed. |

The 88 production tests cover: all six cases and edge cases (empty, truncated, sparse, missing T4, strict boundaries, witnessed violation before truncation, invalid timestamps); M5 eligibility and M4 denominator identities; engine exclusion; bare-id fail-closed and cohort-qualified identity; the lead-in screen (pure, integrated, aggregated); censoring handling; proposed-schema validation; decision-register consistency (nothing newly approved); proposed-protocol wording consistency; provenance preservation; the manifest tool on a synthetic tree. **Not run:** the integration/smoke tests, tests that read real dataset inventories (`test_real_dataset_inventory`, `test_layer_b_loader`, audio/vision pipelines), and the official readiness gate against the real repository.

## 7. Git state

| | Before | After |
|---|---|---|
| Branch / HEAD | `main` / `d4db94d4…` | unchanged |
| Staged | 0 | 0 |
| Modified tracked | 19 (identical list) | 19 (identical list) |
| Porcelain entries | 374 | 377 (new untracked files/dirs) |
| `v9` protocol SHA-256 | `7c183b32…8734c` | unchanged |
| `v7` GT SHA-256 | `d100c1e6…49ecf4` | unchanged |
| `metrics.py` SHA-256 | `8e38992c…a673` | `7d7083eb71d334615e8b2f1c673313055fe0d0028734e7c3ef915eef2d6e7f87` (intentionally edited) |
| `.git/lost-found/` | 146 / 163 | untouched |

No `git add/commit/push/reset/clean/checkout/restore/fsck` ran; git was read with `GIT_OPTIONAL_LOCKS=0`. A pre-edit copy of `metrics.py` was saved in the scratchpad.

## 8. Deviations from the confirmed decision matrix and process
1. **Change map written late:** after the Phase 2 code edits (disclosed in the map).
2. **`no_steps_in_protection_interval`:** a complete replay whose protection interval holds no retained step is `NOT_EVALUABLE`, a conservative reading of "handle sparse replay steps" not stated in the six-case table (no numeric tolerance). Needs your confirmation (BR-20).
3. **Protocols delivered as new proposed files**, not in-place edits, to avoid overwriting your uncommitted work and orphaning hash pins; RD-002's "apply wording before binding" is therefore a proposal until you adopt it. The same applies to `EXPERIMENT_DESIGN_FINAL.md`, `OPEN_DECISIONS_AND_BLOCKERS.md`, `RESEARCH_DECISIONS.md` and the paper draft: none edited; reconciliation is in new documents.
4. **Lead-in screen is stricter than the design's M3** (an observable T0 that is too close to T1 is also insufficient) and is **not wired** into the official runner.
5. **Behaviour change in the official path:** `clock_aware`/`evaluation_runner` now pass the cohort, so an engine event reaches the engine branch of `evaluate_run` (previously the no-train branch, with notes overwritten afterwards). Tests pass; flagged for your review.
6. **`m4_premature_opening` second return element** is now `None` (not `False`) when evidence is incomplete.
7. **Four existing test files** had bare fixture ids qualified (mechanical); one existing line was re-wrapped.
8. **TF-06:** documented only; `decision_policy_v1.yaml` (frozen) not edited.
9. The manifest tool **enumerates** directory entries (including media file *names*) but never opens, reads or hashes media; media/binary/model files are excluded by extension before any open.
10. The report you are reading, created after the final manifest build, is not itself in the manifest.

## 9. Changed-file list (exact)
**Modified (untracked source in the working tree):** `src/railway_detection/evaluation/{metrics,clock_aware,evaluation_runner,execution_gate}.py` · `src/railway_detection/experiments/preflight_validator.py` · `src/railway_detection/annotation/batch_multimodal_annotator.py`
**Modified tests:** `tests/unit/{test_event_metrics,test_mission2_pipeline_integrity,test_mission4e2_m4_occupancy_contract,test_phase12_documented_metrics,test_phase12_metric_arithmetic}.py`
**New code/tests/tools:** `src/railway_detection/evaluation/lead_in_screen.py` · `src/railway_detection/annotation/stage2_1_schema_proposed.py` · `scripts/mission5a_build_preservation_manifest.py` · `tests/unit/test_mission5a_production.py`
**New documents, `docs/generated/mission_5a/`:** `CHANGE_MAP`, `PROTOCOL_RECONCILIATION_REPORT`, `FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL_v9.1.0_PROPOSED.md`, `FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md`, `v9_working_tree_vs_v9.1.0_PROPOSED.diff`, `v7_working_tree_vs_v7.1.0_PROPOSED.diff`, `M4_M5_PRODUCTION_CORRECTION`, `MISSED_TRAIN_FEASIBILITY_SCREEN`, `STAGE21_SCHEMA_AND_REVIEW_GOVERNANCE_PROPOSAL`, `EXPERIMENT_DESIGN_RECONCILIATION`, `PAPER_REVISION_PROPOSAL`, `GOVERNANCE_APPROVAL_DRAFTS`, `RATIFICATION_DRAFT_20261030_DECISIONS`, `RD_IMPLEMENTATION_MATRIX`, `DEFERRED_ITEMS_BLOCKER_REGISTER`, `SNAPSHOT_PROPOSAL`, `REPRODUCIBILITY_MANIFEST_20261101_M5A.json` (SHA-256 `736e4031de7d6cb24b0b447212d0136261a6d89369bf8d910bdf8fedca611851`; 858 entries, **734 untracked**, 11,322 generated-output files counted not hashed; both frozen checkpoints match their expected hashes; self-verify clean), and this report.

## 10. Final safety audit
No raw media accessed (no `.mov/.mp4/.wav` opened, played, decoded, previewed or hashed) · no real human review, reviewer identity, signature or review record · no Stage-2.1 execution or GT promotion · no official split, no EVAL-AUTH · no experiment, replay of real data, inference, training, cache or timing pilot · no threshold, ROI, B7e or R04 approval · no full occupancy duration reported · no readiness gate bypassed or edited beyond one message string · no allowlist change · no Git history or staging action · existing modifications preserved · `.git/lost-found/` untouched. **No accidental violation occurred.** The official readiness gate was not re-run on the real repository.
