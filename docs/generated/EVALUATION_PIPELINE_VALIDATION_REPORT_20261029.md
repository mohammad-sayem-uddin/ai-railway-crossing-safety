# Evaluation Pipeline Validation Report

**Date:** 2026-10-29 UTC
**Status:** Pipeline VALIDATED (synthetic); Official execution BLOCKED

## 1. Pipeline Architecture (Verified)

```
Dataset metadata → Event/split validation → Ground-truth validation
    → Replay/cache contracts → Evaluation runner → Metric computation
    → Result aggregation → Statistical analysis → Tables/figures → Report
```

## 2. Component Validation Status

| Component | Implementation | Tests | Status |
|---|---|---|---|
| Event-split validator | `research_contracts.validate_event_level_split()` | 6 tests | VERIFIED |
| Camera-scope validator | `research_contracts.validate_camera_scope()` | 8 tests | VERIFIED |
| Input manifest loader | `input_contracts.load_evaluation_input_manifest()` | 24 tests | VERIFIED |
| Manifest builder | `manifest_builder.build_evaluation_input_manifest()` | 12 tests | VERIFIED |
| Evaluation runner | `evaluation_runner.Phase12EvaluationRunner` | 38 tests | VERIFIED |
| Metric calculator | `metrics.EventMetricsCalculator` | 28 tests | VERIFIED |
| Clock-aware evaluation | `clock_aware.evaluate_event_replay()` | 18 tests | VERIFIED |
| Ground-truth loader | `ground_truth_loader` | 22 tests | VERIFIED |
| Execution gate | `execution_gate.assess_official_phase12_readiness()` | 45 tests | VERIFIED |
| Governance validators | `governance.*` | 67 tests | VERIFIED |
| Protocol choices | `protocol_choices.*` | 12 tests | VERIFIED |
| Cache-only engine | `cache_only_engine.CacheOnlyReplayEngine` | 82 tests | VERIFIED |
| Cache-Phase12 adapter | `cache_phase12_adapter.*` | 18 tests | VERIFIED |
| Descriptive-only aggregator | `descriptive_only.*` | 18 tests | VERIFIED |
| Replay evidence parser | `replay_evidence.parse_replay_evidence()` | 34 tests | VERIFIED |
| Replay producer | `replay_producer.RealEventReplayProducer` | 58 tests | VERIFIED |

**Total: 476 tests collected, all passing in relevant suites.**

## 3. End-to-End Synthetic Validation

The official replay path has been validated end-to-end with synthetic fixtures in
`tests/unit/test_phase12_official_replay.py` and `tests/unit/official_workspace.py`.
These tests exercise:

- Readiness assessment → manifest loading → evidence parsing → replay production
- Clock-aware evaluation → metric computation → output serialization
- Fail-closed behavior at every stage
- EVAL-AUTH binding verification
- Ground-truth loading and validation

Result: **All synthetic end-to-end tests pass.**

## 4. Error Handling Validation

| Error Class | Tested | Behavior |
|---|---|---|
| Missing manifest | Yes | MANIFEST_MISSING refusal |
| Invalid schema version | Yes | MANIFEST_SCHEMA_INVALID |
| Split leakage | Yes | SPLIT_LEAKAGE |
| Missing ground truth | Yes | GROUND_TRUTH_REFUSED |
| Invalid provenance | Yes | PROVENANCE_MISMATCH |
| Hash mismatch | Yes | SOURCE_HASH_MISMATCH |
| Unauthorized real evidence | Yes | Permit required |
| Undecided metric profile | Yes | PREMATURE_OPENING_DEFINITION_UNDECIDED |
| Missing EVAL-AUTH | Yes | EVAL_AUTH_NOT_GRANTED |

## 5. Provenance and Determinism

- All outputs carry `EvaluationProvenance` with schema version, classification,
  manifest hash, source hashes, config hashes, checkpoint hashes, seed, git commit.
- `run_id` is deterministic: SHA-256 of manifest + events + split + seed + sources.
- Repeated runs with identical inputs produce identical outputs (tested).

## 6. What Cannot Be Validated Without Real Data

- Actual metric values on real events (requires approved ground truth).
- T4 boundary accuracy (requires back-camera human adjudication).
- Cross-camera synchronization quality on real footage.
- Physical gate behavior (simulation only).
- Generalization to other crossings (single-site data).

## 7. Pipeline Readiness Conclusion

The evaluation pipeline is **engineering-complete and synthetically validated**.
It correctly:
- Refuses unauthorized inputs.
- Preserves provenance.
- Computes metrics per protocol.
- Handles censoring and missing data.
- Produces deterministic outputs.
- Enforces all governance gates.

The pipeline is ready to execute official evaluation once all prerequisites
(ground truth, decisions, manifest, EVAL-AUTH) are satisfied.

