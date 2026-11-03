# Regression Test Results Report (Mission 4A)

**Date:** 2026-11-01  
**Mission:** 4A — Governance Reconciliation, Authorization Integrity & Stage-2.1 Safety Verification  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Branch / HEAD:** `main` @ `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Status:** ALL PASSING (`1,409 passed in 29.31s` across `tests/unit` + `tests/test_phase11_*.py`)

---

## 1. Executive Summary

Mission 4A added the dedicated synthetic regression suite `tests/unit/test_mission4a_governance_and_stage21_safety.py` (13 comprehensive multi-assertion tests covering Objectives A through G) and executed the complete unit and Phase 11 governance test suites.

- **Mission 4A + Mission 3 Targeted Suite:** `46 passed in 1.53s`
- **Full `tests/unit` + `tests/test_phase11_*.py` Suite:** `1,409 passed in 29.31s` (`0` failures, `0` errors, `0` skipped)
- **Raw Media Safety Verification:** Zero `.mov`, `.mp4`, or `.wav` files were opened, decoded, or hashed during any test execution. All file-writing tests ran inside isolated pytest `tmp_path` directories.

---

## 2. Mission 4A Test Suite Breakdown (`tests/unit/test_mission4a_governance_and_stage21_safety.py`)

| Test Function | Mission 4A Objective Covered | Key Invariants Verified | Result |
|---|---|---|---|
| `test_canonical_decision_register_statuses_and_historical_reconciliation` | Objective A (§4) | Verifies all 6 permitted `DECISION_STATUSES`, all 17 canonical entries in `CANONICAL_DECISION_REGISTER`, and exact resolution of historical `D1`–`D4`, `D3_SPLIT`, `B7d`, `B7e`, `ENGINE_ISOLATION`, `GT_SEPARATION`, `LEG_EXEC`, `STAGE21_SAFEGUARDS`, `EVAL_AUTH`, plus superseded M3 overload aliases (`M3_D1_OVERLOAD_OPERATING_THRESHOLDS`, `M3_D2_OVERLOAD_ROI_GEOMETRY`) | **PASSED** |
| `test_preflight_validator_separates_d1_d2_from_thresholds_and_roi` | Objective A (§4) | Verifies `classify_experiment_parameters()` and `run_experiment_preflight()` emit distinct blockers for `DECISION_D1_PENDING`, `DECISION_D2_PENDING`, `DECISION_EXP_OPERATING_THRESHOLDS_PENDING`, `DECISION_EXP_ROI_GEOMETRY_PENDING`, and `DECISION_D4_PENDING`, and that approving operating thresholds/ROI does not clear `D1`/`D2` (and vice versa) | **PASSED** |
| `test_repository_engine_event_scope_is_exactly_one_event` | Objective B (§5) | Verifies `data/manifests/layer_b_v2_annotation_inventory.json`, `data/ground_truth/proposals/`, `data/ground_truth/reviews/`, and `docs/generated/STAGE21_REVIEW_QUEUE.json` all contain `1` engine event (`engine_events/event_001`, with 3 proposal versions `v1..v3`), `3` no-train events (`event_001..003`), and `23` train events (`event_001..023`) = `27` total events | **PASSED** |
| `test_single_engine_event_isolated_from_train_and_negative_control_denominators` | Objective B (§5) | Verifies `EventMetricsCalculator.aggregate_cohort()` and `aggregate_descriptive_only()` isolate `engine_events/event_001` from train sensitivity (`missed_train_count`) and negative-control (`false_alarm_count`) denominators | **PASSED** |
| `test_adjudication_session_and_timing_pilot_enforce_synthetic_and_path_isolation` | Objective C (§6) | Verifies `AdjudicationSession` and `_require_preparation_isolation` reject non-`synthetic_` IDs and canonical `data/ground_truth` output paths, while emitting `NEEDS_SECOND_REVIEW` records in `tmp_path` | **PASSED** |
| `test_promotion_and_readiness_gates_reject_synthetic_records_when_enforced` | Objective C (§6) | Verifies `validate_non_synthetic_record()`, `validate_for_promotion(..., disallow_synthetic_identifiers=True)`, `promote_record(..., disallow_synthetic_identifiers=True)`, and `evaluate_readiness(..., disallow_synthetic_identifiers=True)` reject `synthetic_` reviewer/session/review IDs, `@synthetic.` domains, and `tmp_path` media paths with `SYNTHETIC_RECORD_NOT_PROMOTABLE` | **PASSED** |
| `test_leg_exec_dry_run_on_repository_is_non_destructive_and_all_27_notices_verify` | Objective D (§7) | Verifies `load_and_verify_proposal()` and `plan_invalidation_notices()` on the real repository in read-only mode, confirming all 27 `.INVALIDATION_NOTICE.json` sidecars pass `scan_notices()`, `invalid_notices() == []`, `len(excused_legacy_records()) == 27`, and all 54 review+notice files on disk have identical SHA-256 digests before and after | **PASSED** |
| `test_invalidation_notice_writer_fails_closed_on_tampering_in_tmp_path` | Objective D (§7) | Verifies in `tmp_path` that wrong proposal hash, missing target review file, tampered target review file hash, existing sidecar collision, and post-notice review tampering all fail closed | **PASSED** |
| `test_allowlist_rejects_missing_empty_blocklisted_duplicate_and_revoked_entries` | Objective E (§8) | Verifies `load_authorized_reviewers()` rejects missing files, empty lists, blocklisted IDs (`"human_annotator"`, `"human_researcher_lead"`), duplicates, and `revoked_reviewers` / `inactive_reviewers` overlaps | **PASSED** |
| `test_stage21_schema_rejects_short_duration_forged_duration_and_bad_history` | Objective E (§8) | Verifies `<30.0s` duration rejection (even with forged `review_duration_s=999.0`), missing/short model-independence attestation rejection, boundary state taxonomy enforcement, duplicate `adjudication_history` rejection, blocklisted history `by` rejection, self-referential `second_review_of` rejection, and same-reviewer second-review history rejection | **PASSED** |
| `test_promotion_gate_and_receipt_detect_media_tampering_disputes_and_batch_collisions` | Objective E (§8) | Verifies valid promotion in `tmp_path`, live media tampering detection (`MEDIA_HASH_CHANGED_SINCE_REGISTRY` & `MEDIA_HASH_CHANGED_SINCE_REVIEW`), stale proposal rejection (`STALE_OR_MISMATCHED_PROPOSAL_HASH`), unresolved dispute rejection (`UNRESOLVED_DISPUTE_HISTORY`), cross-record `BATCH_SAME_REVIEWER_SECOND_REVIEW` detection, and `verify_promotion_receipt()` tamper detection | **PASSED** |
| `test_controlled_cache_integration_across_processor_and_preflight` | Objective F (§9) | Verifies `LayerBEventProcessor` controlled cache write/read round-trip in `tmp_path`, refusal to fall back to legacy `.jsonl` cache when `require_controlled_cache=True`, refusal on parameter perturbation (`conf_threshold` `0.25 -> 0.35`), and `run_experiment_preflight()` validation of controlled cache directories | **PASSED** |
| `test_official_phase12_readiness_and_execution_gate_fail_closed_on_repo` | Objective G (§10) | Verifies `evaluate_readiness()`, `assess_official_phase12_readiness()`, `verify_promotion_receipt()`, `Phase12EvaluationRunner.run()`, and `run_experiment_preflight()` all fail closed on the live repository with consistent blocker codes | **PASSED** |

---

## 3. Command Execution Log

```text
$ PYTHONPATH=src .venv/bin/pytest tests/unit/test_mission4a_governance_and_stage21_safety.py tests/unit/test_mission3_reproducibility_and_provenance.py -v
============================== 46 passed in 1.53s ==============================

$ PYTHONPATH=src .venv/bin/pytest tests/unit tests/test_phase11_*.py -q
1409 passed in 29.31s
```
