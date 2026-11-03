# Phase 13 — Robustness and Ablation Studies: Report

**Status:** BLOCKED. Depends on Phase 12 completion (baseline metrics against approved ground truth).
**Date:** 2026-10-15.

---

## 1. Summary

Phase 13 cannot proceed because Phase 12 has not produced baseline metrics (no approved ground truth exists). This report documents the preparation state and what will be done when unblocked.

## 2. Prerequisites

| Prerequisite | Status |
|---|---|
| Phase 12 baseline metrics | ❌ Not computed (no approved ground truth) |
| Event-level split fixed | ❌ Not decided |
| Frozen config intact | ✅ Verified |
| Researcher authorization for ablation scope | ❌ Not granted |

## 3. Planned Work (When Unblocked)

Per `docs/implementation_plans/PHASE13_IMPLEMENTATION_PLAN.md`:

1. **Ablation matrix:** vision-only, audio-only, fusion; confirmation=1/2/3; miss_tolerance=0/1/2/3.
2. **Perturbation suite:** sensor dropout, Gaussian noise on confidences, timing jitter.
3. **Analysis:** per-condition metric tables with deltas from baseline.
4. **Report:** pre-registered hypotheses, results, limitations.

## 4. Safety Invariants (Always in Force)

- No Audio V2.
- No frozen-config modification.
- No post-hoc threshold adjustment.
- No safety claims from simulation.

## 5. Blocked Operations

All Phase 13 operations are blocked pending Phase 12 completion and researcher authorization.

---

## Additive update — 2026-10-16 (engine hardening; no experiment run)

**Status:** The synthetic experiment engine is hardened. **No official or real-data experiment has been conducted; no result is claimed.** The engine still refuses any non-synthetic data provider.

- **Baseline/treatment comparability.** A plan now rejects a treatment that applies neither an override nor a perturbation (it would equal the baseline) and one that applies both (more than the one declared factor). Baseline and treatment are shown to receive the identical (event, seed, input-fingerprint) grid. A comparison is reported only when both conditions completed the full event x seed grid (`unavailable_incomplete_coverage` otherwise); manifests record `expected_cells_per_condition` and `completed_cells_by_condition`.
- **Partial-run reporting.** A failed baseline (`FAILED_BASELINE`) or an abort with `continue_on_error` disabled (`FAILED`) now persists an `experiment_manifest.json` with the failures, per-condition completed cell counts and empty metric/comparison maps before raising; incomplete conditions are never aggregated.
- Tests: `tests/unit/test_phase13_experiment_engine.py` (11, four new).

---

## Additive update — 2026-10-16 (overnight)

Still **no official ablation or robustness experiment has been run**; the legacy empirical entry point remains blocked regardless of caller flags. Engine additions: a treatment must override exactly its declared factor (or perturb with a matching `kind`) — extra keys are "hidden configuration changes" and refused; condition parameters must be plain finite data; each inference call receives its own copy of the event input and a call that mutates it is a recorded failure; comparisons require the identical metric set as well as the full event × seed grid; synthetic experiments cannot write under `results/`, `experiments/`, `data/`, `configs/` or `models/`. Tests: `tests/unit/test_phase13_experiment_engine.py` (29).

## Additive update — 2026-10-19 (checkpointed synthetic resume)

No official or real-data run was started. The synthetic-only engine now writes
each successful event × seed × condition cell to an atomically replaced
`cell_results.json` checkpoint and atomically writes final manifests and metric
files. `resume=True` requires the prior plan, run identity, and all input
SHA-256 fingerprints to match; altered or malformed checkpoints are refused.
Successful cells are skipped and absent/failed cells may be retried, while
comparison output still requires complete, matching event × seed coverage and
metric names. This is recovery infrastructure only and does not authorize an
experiment or create empirical findings. Regression coverage includes partial
resume/retry and altered-input refusal (`tests/unit/test_phase13_experiment_engine.py`).
