# Phase 12 — Evaluation and Benchmarking: Implementation Plan

**Status:** PLANNING ARTIFACT — not authorized, not implemented. No performance claim is made or implied by this plan.

## 1. Objective and research justification

Evaluate the frozen baseline system against researcher-approved Stage-2.1 ground truth only, with leakage controls, event-level splits, reproducibility, and honest limitations. This phase exists to replace the current zero-approved-ground-truth state with defensible numbers — and it must not run until the Phase 11.12 gate passes and EVAL-AUTH is given.

## 2. Verified starting state

Frozen config verified intact this session: checkpoints (vision `3f5bb5b2…`, audio_v3 `ea1bb81d…`, audio_v2 prohibited `59b0785f…`), thresholds, timing, R04 restriction (`allow_unverified_zero_offset: false`). Phase 8 exploratory outputs exist for the 11-event supported subset; Phase 10.1 candidate comparison outputs exist. No approved ground truth exists yet (verified: zero Stage-2.1 records).

## 3. Dependencies and prerequisites

- 11.12 verdict READY_FOR_SPECIFIC_EVALUATION_STAGE naming the stage + EVAL-AUTH.
- Explicit researcher decision on event-level split (train/validation/test partition by EVENT, never by frame).
- R04 scope decision: which events' dual-camera claims are in scope (11 supported vs 16 unresolved).

## 4. Explicit authorization boundary

MAY compute metrics against approved ground truth within the authorized stage. MUST NOT retune frozen thresholds, retrain checkpoints, use Audio V2, merge cross-camera timelines beyond R04-supported events, or present simulated gate behavior as safety evidence.

## 5. Files/modules to inspect

- `configs/frozen_experiment_v1.yaml`, `configs/decision_policy_v1.yaml`, `configs/decision_policy_v2_candidate.yaml`
- `src/railway_detection/evaluation/metrics.py`, `src/railway_detection/experiments/` (runner, layer_b_processor, timeline_generator)
- `scripts/run_phase5_full_inference.py`, `scripts/run_phase10_candidate_replay.py`
- `docs/EXPERIMENT_DESIGN_FINAL.md` §5, `docs/FINAL_ABLATION_MATRIX.md`, `docs/FINAL_EXPERIMENT_DATA_FLOW.md`
- `results/experiment_registry.jsonl`

## 6. Expected files to modify or create

Proposed: `src/railway_detection/evaluation/ground_truth_loader.py` (loads ONLY approved Stage-2.1 records; refuses legacy/candidate sources); `src/railway_detection/evaluation/event_metrics.py` extensions; `scripts/run_phase12_evaluation.py`; `docs/PHASE12_EVALUATION_REPORT.md`; outputs under `results/experiments/phase12_<timestamp>/`. Confirmed existing: `metrics.py`, experiment runner scaffolding.

## 7. Detailed implementation tasks in dependency order

**Unit 1 (ground-truth loader):** approved-records-only loader with fail-closed refusal of any `schema_version` != `8.1.0-stage2.1`, any non-APPROVED status, any UNCERTAIN boundary used as if observable.
**Unit 2 (metric definitions):** pre-register metrics and their formulas in the report BEFORE computing: event-level boundary metrics respecting censoring (left-censored T0 excluded from latency denominators per protocol), warning-lead-time, premature-opening count, failure-to-reopen count, FAR on the 3 no-train events (counts, with Wilson CIs), MTR/POR as defined in `EXPERIMENT_DESIGN_FINAL.md`. Every metric states its denominator and censoring rule.
**Unit 3 (splits + leakage controls):** event-level split manifest (researcher-approved); leakage test asserting no test event appears in any train/val artifact; single-camera vs R04-supported-subset separation.
**Unit 4 (execution):** deterministic replay (frozen seed 42, cpu device per config) of the baseline; record full tick logs as in Phase 5/10.1.
**Unit 5 (reporting):** numbers with CIs where n is small (all 3 negative controls → counts + Wilson CI only, never a point-estimate rate presented alone); limitations section mandatory; explicit statement that simulated gate kinematics are not safety evidence.

## 8. Data, schema, and API changes

None to schema. New loader/metric modules. No change to frozen config (hash-checked before and after).

## 9. Tests and acceptance criteria

- Loader rejects: legacy records, candidate proposals, UNCERTAIN-as-observable (3 unit tests minimum).
- Leakage test passes: disjoint event sets across split roles.
- Determinism: two runs of the same event produce byte-identical tick logs.
- Reproducibility: report includes exact config hashes, checkpoint hashes, git HEAD, and command lines.
- Every reported number traceable to a log file in the output directory.

## 10. Negative tests and adversarial cases

Loader given a `7.0.0`/`6.0.0` record → refusal; loader given a candidate proposal path → refusal; metric function given an all-censored boundary set → returns explicit NOT_COMPUTABLE, never 0.0 or NaN-as-zero; attempt to compute a dual-camera metric for an R04-unsupported event → refusal.

## 11. Scientific-validity safeguards

Pre-registration before computation; censoring-aware denominators; small-n reporting with CIs; no post-hoc threshold movement; R04 restriction enforced in code, not just policy.

## 12. Safety invariants and prohibited shortcuts

No Audio V2. No frozen-config edits. No retraining. No "temporary" relaxation of the R04 flag. No publishing a metric before the report's limitations section exists.

## 13. Expected outputs and report paths

`docs/PHASE12_EVALUATION_REPORT.md`; `results/experiments/phase12_<timestamp>/`; registry entry appended to `results/experiment_registry.jsonl` (append-only).

## 14. Rollback and recovery procedure

Outputs are in a fresh timestamped directory; rollback = delete directory + truncate the one appended registry line (record line count before/after). Frozen artifacts are never modified, so no rollback is needed there.

## 15. Integrity checks

Frozen config sha256 pre/post; checkpoint hashes pre/post; legacy records unchanged; Phase 8 output directory unchanged; git status limited to new evaluation files.

## 16. Definition of done

All authorized metrics computed against approved ground truth only, with CIs and limitations; leakage tests green; report reviewed by Opus for overclaim language before acceptance.

## 17. Stop conditions and escalation criteria

STOP if any metric requires ground truth not yet approved (do not approximate); if a leakage violation is detected; if determinism fails; if R04 scope is ambiguous for a requested metric.

## 18. Recommended implementation model

**Qwen 3.8 Max** (Units 1–4: leakage and censoring logic are subtle and high-consequence); **Gemini 3.8 Flash** for report figure/table generation; **Opus** reviews the pre-registration and the final report language.

**Minimum viable implementation:** Units 1–2 + single-camera baseline on the approved subset. **Deferrable:** candidate-policy comparison (Phase 12.5, separate authorization). **Highest-risk failure mode:** evaluating against candidate proposals instead of approved records because the loader is permissive (defeated by Unit 1 negative tests). **Cheapest verification:** loader refusal tests + leakage disjointness assertion.
