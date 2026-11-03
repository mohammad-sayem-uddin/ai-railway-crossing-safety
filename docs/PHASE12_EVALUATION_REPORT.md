# Phase 12 — Evaluation and Benchmarking: Report

**Status:** PARTIAL ENGINEERING (approved-record loader and readiness gate only). Evaluation BLOCKED on EVAL-AUTH, approved ground truth, split, and R04 scope.
**Original date:** 2026-10-15. **Status clarified:** 2026-10-16.

> **Current status clarification — 2026-10-19:** The initial status and sections below record the
> 2026-10-15 implementation snapshot and are retained as history. Since then, the official
> readiness gate, evidence-derived execution workflow, replay producer, metrics/report pipeline,
> and fail-closed CLI have been implemented and tested with synthetic fixtures. They are wired
> through `python -m railway_detection evaluation status` and `evaluation run`; the live gate
> still refuses the official run until the researcher-controlled evidence and authorization
> listed in `docs/generated/OFFICIAL_EVALUATION_READINESS_20261019.json` exist. No real-data
> evaluation or official result has been produced. The readiness CLI's separate `NO_RECORDS`
> result is also expected: all 27 legacy records are invalidated and zero Stage-2.1 records exist.

---

## 1. Summary

The following narrow preparation components are implemented and tested:
- **Ground truth loader** (`src/railway_detection/evaluation/ground_truth_loader.py`): fail-closed, approved-records-only.
- **Evaluation-readiness gate** (Phase 11.12): implemented and verified.

The Phase 12 evaluation runner, authorized event-level split manifest, and complete censoring-aware metrics/report pipeline are not implemented or executed. **No evaluation has been run.** No metrics have been computed against ground truth. This is correct: zero genuine approved Stage-2.1 records exist.

## 2. Ground Truth Loader

**File:** `src/railway_detection/evaluation/ground_truth_loader.py`

**Rejections verified by tests:**
- Legacy records (schema_version ≠ 8.1.0-stage2.1) → `LegacyRecordRefused` (alias: `LegacyRecordError`) ✅
- Candidate proposal files → `CandidateProposalRefused` ✅
- Non-APPROVED records → `NotApprovedRefused` (alias: `UnapprovedRecordError`) ✅
- UNCERTAIN/CENSORED boundaries as observable → `BoundaryNotComputable` (alias: `UncertainBoundaryError`) ✅
- Mixed review/candidate directories and duplicate event IDs → refused ✅

**Test results:** 9 passed.

## 3. Metric Pre-Registration (for future evaluation)

The following proposed metric definitions are planning notes, not a researcher-approved preregistration. Any metric whose definition, denominator, censoring rule, population, or R04 scope remains unsettled must be resolved before computation. No metric is computed by this report.

| Metric | Definition | Denominator | Censoring Rule |
|---|---|---|---|
| Boundary MAE | Mean absolute error of predicted vs GT boundary time | Observable boundaries only | Censored/UNCERTAIN excluded |
| Warning lead time | T1_danger_zone_entry - gate_warning_start | Events with observable T1 | Censored T1 excluded |
| Premature opening count | Gate opens before T0 | All train events | — |
| Failure to reopen count | Gate fails to reopen after T4 | All train events | — |
| FAR (no-train) | False alarm rate on 3 no-train events | 3 events (counts + Wilson CI) | — |

**Small-n reporting:** All 3 negative controls → counts + Wilson CI only, never a point-estimate rate presented alone.

## 4. Blocked Operations

| Operation | Blocker |
|---|---|
| Metric computation | No approved ground truth (zero Stage-2.1 records) |
| Event-level split | Requires researcher decision |
| Deterministic replay | Requires EVAL-AUTH |
| Report with numbers | Requires all of the above |

## 5. What Phase 12 Did NOT Do

- ❌ Did not compute any metric.
- ❌ Did not evaluate against unapproved ground truth.
- ❌ Did not retune frozen thresholds.
- ❌ Did not use Audio V2.
- ❌ Did not modify frozen config.
- ❌ Did not claim any performance number.

## 6. Integrity

- Frozen config hash: unchanged.
- Checkpoint hashes: unchanged.
- Legacy records: unchanged (27 files, schema_version 6.0.0).
- Git status: pre-existing modified/untracked research artifacts remain; no evaluation outputs were created.

## 7. Next Steps

1. Researcher grants ADJ-AUTH → Phase 11.11 adjudication produces approved records.
2. Researcher grants EVAL-AUTH → Phase 12 evaluation runs against approved records.
3. Metrics are computed per the pre-registered definitions above.

---

## Additive update — 2026-10-16 (engineering; still no evaluation run)

**Status:** The synthetic-capable evaluator, input-manifest contracts, execution gate and an official-run entry point (`Phase12EvaluationRunner.run_official`) are implemented and tested. **No official or real-data evaluation has been run and no metric has been computed against ground truth.**

**Correction to section 3.** The planning table above lists "Premature opening count: Gate opens before T0". That matches neither the authoritative protocol (`FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` section 5.2: opening commanded while T1 <= t < T4) nor the code. The table is a historical planning note and is left as written; the operative definition is the protocol's. The design document's M4 alternative (first blocked tick < t < T4) is pending `[D-10]` and not implemented.

**Correction to this correction (2026-10-16, later).** The preceding sentence calls the protocol's window "operative". That overstated the record: no researcher-attributed document accepts either window (see `docs/PREMATURE_OPENING_DECISION_EVIDENCE.md`). The evaluator now has no default for it and an official run is blocked until the researcher records a choice.

**What is implemented beyond the earlier report**
- Protocol profile with provenance (`evaluation/protocol_choices.py`), bound by hash into EVAL-AUTH.
- Per-metric exclusion reporting: each eligible event a metric could not use is listed with the censored/uncertain boundary that excluded it.
- No-train nuisance reporting per protocol v9 section 11.2: blocked seconds, closure episodes and exposure seconds; deliberately no hourly rate. Camera- and audio-level false-detection counts remain unimplemented (the replay result does not carry detection-level data).
- `run_official` re-assesses live evidence on every call and loads ground truth from the repository; callers cannot inject labels, permits or flags.
- Manifest builder (`evaluation/manifest_builder.py`) deriving the input manifest from verified decisions.

**Blockers (35), all external to the code:** 27 legacy records (invalid evidence), no Stage-2.1 records, 3 derived cohort blockers, no event-split decision, no R04 scope decision, no input manifest, no recorded EVAL-AUTH. See `docs/APPROVAL_RECONCILIATION_REPORT.md`.

**Verification:** `tests/unit/test_phase12_governance.py` (59), `test_phase12_documented_metrics.py` (6), `test_legacy_reconciliation.py` (5), plus the existing Phase 12 suites, all synthetic.

---

## Additive update — 2026-10-16 (real-event replay producer; still no evaluation run)

The missing replay producer is implemented and tested on synthetic fixtures only; see `docs/OFFICIAL_REPLAY_PRODUCER.md`. `run_official` no longer accepts caller-supplied replays: it produces them from the verified, authorized manifest, evaluates them clock-aware, and writes outputs atomically or writes only a structured failure report. Against the real repository the run is blocked at readiness (36 blockers, including the undecided premature-opening window); no replay, metric or output was produced.

---

## Additive update — 2026-10-16 (overnight)

Still **no official or real-data evaluation has been run.** Engineering added: premature opening is *not computed* unless an explicit implemented window is supplied (no default to v9 or M4; official runs additionally require the researcher's choice); hand-calculated tests for Wilson intervals, missed-train matching, excess closure, clearance latency, lead time and cohort denominators (`tests/unit/test_phase12_metric_arithmetic.py`); fake-backend producer scenarios (single-event and multi-event cohorts, missing/corrupted/mis-hashed payloads, unsupported camera modes, wrong config/checkpoint, invalid alignment, replay exception, write failure, staging cleanup, failure-report integrity, determinism); run manifests record `contract_versions`, the protocol profile and the window used.

Known discrepancy left undecided: the evaluator clamps warning lead time at 0 (`max(0, T1 − t_warn)`), whereas `EXPERIMENT_DESIGN_FINAL.md` §8.1 asks for signed, unclamped lead times. The design is pending `[D-10]`, so the code was not changed.
