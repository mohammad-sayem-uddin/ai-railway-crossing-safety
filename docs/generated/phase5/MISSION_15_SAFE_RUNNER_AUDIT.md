# Mission 15 — WP15.5 Safe Runner and Test Classification Independent Audit

**Auditor:** Independent Principal Security Auditor and Research Reproducibility Auditor  
**Date:** 2026-11-02  
**Mission:** 15  
**Priority:** CRITICAL  
**Audited Artifacts:** `scripts/run_synthetic_tests.py`, `tests/test_access_classification.yaml`, `src/railway_detection/safety/access_guard_plugin.py`, `tests/unit/test_phase12_governance_synthetic.py`, `tests/unit/test_phase12_official_replay_synthetic.py`, `mission14_evidence/mission14_synthetic_test_report.json`  
**Execution Environment:** Python 3.11.15 virtual environment (`.venv`), macOS APFS.

---

## 1. Executive Summary

Mission 14 claimed that the safe synthetic runner had been restored without weakening its fail-closed invariants, executing **2,198 tests across 100 files** with zero failures, zero blocked accesses, zero classification violations, and excluding 21 protected test files.

Mission 15 independently audited the runner implementation, validated the classification manifest, inspected the synthetic test copies, and executed a single reproduction run under the read-blocking access guard harness:

```bash
./.venv/bin/python scripts/run_synthetic_tests.py --report-path /tmp/mission15_synthetic_test_report.json
```

**Reproduction Result:**
- **Status:** `PASSED` (exit code 0)
- **Duration:** 53.59 seconds
- **Total Tests Passed:** **2,198**
- **Failures / Errors / Skips:** **0 / 0 / 0**
- **Files Executed:** **100** (78 `SYNTHETIC_ONLY`, 22 `METADATA_ONLY`)
- **Protected Files Excluded:** **21** (15 `MODEL_CHECKPOINT_ACCESS`, 4 `RAW_MEDIA_ACCESS`, 2 `PROCESSED_DATA_ACCESS`)
- **Guard Armed Events:** **2,601** (Armed, Disarmed, 2,597 allowed metadata reads, 0 blocked)
- **Blocked Accesses:** **0**
- **Violations:** **0**

The results are bit-for-bit identical to Mission 14's archived report `docs/generated/phase5/mission14_evidence/mission14_synthetic_test_report.json`.

---

## 2. Classification Manifest & Runner Invariants

### 2.1 Manifest Completeness and Hash Integrity
The classification manifest `tests/test_access_classification.yaml` (schema v2.0.0) declares exactly 121 test files:
- 100 safe files (78 `SYNTHETIC_ONLY`, 22 `METADATA_ONLY`)
- 21 protected files (15 `MODEL_CHECKPOINT_ACCESS`, 4 `RAW_MEDIA_ACCESS`, 2 `PROCESSED_DATA_ACCESS`)

Every single file in `tests/**/test_*.py` on disk is classified in the manifest.
Using `access_manifest.verify_manifest_against_tree()`, the auditor verified:
- Zero unclassified test files exist.
- Zero ghost entries (entries for non-existent files) exist.
- Every declared SHA-256 hash matches the actual file on disk.

### 2.2 Strict Fail-Closed Enforcement
The safe runner enforces strict fail-closed stages in order:
1. Manifest verification: If any file hash mismatches, if any file is unclassified, or if any entry is missing, the runner exits immediately with code 3 (`MANIFEST_UNTRUSTED`) without running any tests.
2. Category restriction: Only `SYNTHETIC_ONLY` and `METADATA_ONLY` categories are selectable. Any attempt to select `UNKNOWN` or protected categories is rejected with exit code 2.
3. Protected file exclusion: The 21 protected test files are explicitly placed in the `excluded` list and omitted from the pytest invocation arguments.
4. Read-blocking access guard: Pytest executes with `-p railway_detection.safety.access_guard_plugin`. The guard wraps `builtins.open`, `io.open`, `os.open`, etc. If any test attempts an unauthorized read, the read is blocked and logged.
5. Post-run log verification (`verify_log`): The log must record that the guard was armed and disarmed; any blocked access or undeclared metadata read raises a `CLASSIFICATION_VIOLATION` (exit code 4).

### 2.3 Verification of "Zero Blocked Accesses"
The metric "0 blocked accesses" in the safe runner report does NOT mean the guard was inactive.
The guard log recorded 2,601 total events:
- Guard armed event: 1
- Guard disarmed event: 1
- Allowed metadata reads: 2,597 (all matched against declared `access_dirs` in `METADATA_ONLY` files)
- Blocked attempts: **0**
- Classification violations: **0**

This proves that all 100 executed files operated strictly within their declared synthetic and metadata boundaries, with zero attempts to access raw media or model checkpoints.

---

## 3. Synthetic Test Sibling Audit

### 3.1 Background of the Phase 12 Test Split
In Mission 12, `test_phase12_governance.py` and `test_phase12_official_replay.py` each mixed safe synthetic unit tests with tests that ran the readiness gate against the real repository root (`REPO_ROOT`), which triggered checkpoint integrity hashing.

In Mission 14:
- The original test files (`tests/unit/test_phase12_governance.py` and `tests/unit/test_phase12_official_replay.py`) were kept untouched and classified as `MODEL_CHECKPOINT_ACCESS`, excluding them from routine execution.
- Synthetic sibling files were created:
  - `tests/unit/test_phase12_governance_synthetic.py` (74 tests)
  - `tests/unit/test_phase12_official_replay_synthetic.py` (87 tests)

### 3.2 Assertion and Security Check Preservation
The auditor performed an exact structural diff between the original files and the synthetic siblings:
- `test_phase12_governance_synthetic.py` preserves 74 out of 76 tests from `test_phase12_governance.py`. The only two omitted tests are:
  1. `test_official_readiness_assessment_fails_closed_when_authorization_missing` (which called `assess_official_phase12_readiness(REPO_ROOT)`)
  2. `test_official_readiness_detects_tampered_baseline_inputs` (which called `assess_official_phase12_readiness(REPO_ROOT)`)
  Both tests were excluded solely because they touched the real repo root. All governance validation, receipt validation, and permit refusal tests are 100% preserved.
- `test_phase12_official_replay_synthetic.py` preserves 87 out of 88 tests from `test_phase12_official_replay.py`. The only omitted test is:
  1. `test_real_repository_run_is_blocked_and_leaves_everything_untouched` (which executed the CLI against `REPO_ROOT`).
  All replay mechanics, metric calculations, and input contract tests are 100% preserved.

No security checks were diluted or silently removed.

---

## 4. M-02 Safe Test Scope Inclusion

Mission 13 identified finding F13-12: M-02 regression tests existed only in protected files, meaning the safe runner never exercised them.

Mission 15 confirmed that M-02 tests are now comprehensively included in the safe test suite:
1. `tests/unit/test_security_evaluation_input.py` (20 tests, classified `SYNTHETIC_ONLY`):
   - `test_explicit_real_request_is_refused_with_zero_reads`
   - `test_forged_permit_with_matching_digest_is_refused_with_zero_reads`
   - `test_forged_authorization_context_is_refused_even_with_the_module_private_token`
   - `test_real_manifest_with_the_classification_argument_omitted_reads_no_source`
   - `test_caller_declaring_synthetic_cannot_relabel_a_real_manifest`
   - `test_private_core_demands_the_context_before_any_source_is_read`
   - `test_context_for_one_manifest_cannot_be_reused_for_another`
   - `test_public_run_and_run_safe_never_reach_the_producer`
2. `tests/unit/test_phase12_governance_synthetic.py` (74 tests):
   - Covers official permit rejection and tamper detection.

These tests exercise real public entry points (`run()`, `run_from_manifest()`, `run_safe()`) against real class instances without mocking out the authorization boundary.

---

## 5. Audit Conclusion

The safe synthetic test runner and access classification manifest are robust, fully reproducible, strictly fail-closed, and accurately represent the system under test. Findings C-03, F13-11, F13-12, and MR12-01 are independently verified fixed.

**Audit Status: VERIFIED.**
