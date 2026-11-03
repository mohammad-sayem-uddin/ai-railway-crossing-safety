> **MISSION 10 CORRECTION NOTICE (2026-11-02).** This document was written by the Phase 5 implementation
> agent before two failed independent audits (`INDEPENDENT_AUDIT_FAIL`, `REMEDIATION_AUDIT_FAIL`). Statements
> below that contradict `MISSION_10_RECOVERY_REPORT.md` are **superseded** by it. Known-wrong claims in this
> file are corrected in place or listed in `MISSION_10_DOCUMENT_RECONCILIATION.md`. In particular: file hashes
> are not asserted here (they change with every edit; use `MISSION_10_ARTIFACT_MANIFEST.json`), "Remaining Risk:
> None" statements are withdrawn, and no authorization, receipt or ground-truth approval exists or is implied.
> The two Sonnet audit reports are unmodified and remain the independent record.

# Phase 5 Reproducibility Package Specification

**Project:** Bangladesh Train Gate Automation Research  
**Document:** `docs/generated/phase5/REPRODUCIBILITY_PACKAGE_SPECIFICATION.md`  
**Phase:** Phase 5 (Remediation Baseline)  
**Execution Agent:** Gemini 3.8 Flash High  
**Future Independent Auditor:** Claude Sonnet 5.5  
**Date:** 2026-11-02  

---

## 1. Specification Overview

This document specifies the observed runtime environment, permitted text/configuration hash bindings, execution manifests, and replication steps for the Phase 5 engineering artifacts without accessing raw media or unapproved data. It does not certify a committed release or authorize real-data execution. Protected checkpoint hashes are `NOT_VERIFIED — REQUIRES AUTHORIZED ACCESS`.

---

## 2. Environment Specification

| Component | Specification |
|---|---|
| **Operating System** | macOS 26.6.2 (Darwin Kernel Version 26.6.2, ARM64 / Apple Silicon) |
| **Python Runtime** | Python 3.11.15 (pinned `.venv/bin/python`) |
| **Virtual Environment Path** | `/Users/sayemuddin/Desktop/Train_automation/.venv` |
| **Package Manager / Build Tool** | Poetry / Pip (`pyproject.toml`) |
| **Key Runtime Dependencies** | `torch==2.13.0`, `ultralytics==8.4.121`, `pytest==9.1.1`, `ruff==0.16.3` |

---

## 3. Cryptographic Hash Bindings

### 3.1 Protocol Specifications

| Artifact | Location | Proposed Version | SHA-256 Digest |
|---|---|---|---|
| Real-World Experiment Protocol | `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` | `v9.1.1` (Canonical Baseline) | `7c183b323970591b68f0db692e70413e54dcacfc4bf78a358c28f1b1ed68734c` |
| Ground-Truth Protocol | `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` | `v7.1.1` (Canonical Baseline) | `d100c1e6a63280c375f94e297416efb0cf7dd3c15c9aa8df076ede052d49ecf4` |

### 3.2 Configurations and Policies

| Configuration File | Path | Status | SHA-256 Digest |
|---|---|---|---|
| Decision Policy v1 | `configs/decision_policy_v1.yaml` | Frozen Baseline | `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575` |
| Frozen Experiment v1 | `configs/frozen_experiment_v1.yaml` | Frozen Baseline | `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a` |
| Exploratory Dual-Cam Config | `configs/exploratory_dual_camera_v1.1.0_authorized_20261013.yaml` | Authorized Scope | `bf229529b234bdc252f5a74fb5f3868e34a085467856a2080250071dc7187d02` |

### 3.3 Phase 5 Remediation Software and Test Artifacts

| Source / Test File | Path | SHA-256 Digest |
|---|---|---|
| Phase 5 Review Tooling | `src/railway_detection/annotation/phase5_review_tooling.py` | `(not asserted - see MISSION_10_ARTIFACT_MANIFEST.json)` |
| Media Access Authorization Validator | `src/railway_detection/annotation/media_authorization.py` | `(not asserted - see MISSION_10_ARTIFACT_MANIFEST.json)` |
| Safe Synthetic Test Runner | `scripts/run_synthetic_tests.py` | `(not asserted - see MISSION_10_ARTIFACT_MANIFEST.json)` |
| Test Access Classification Matrix | `tests/test_access_classification.yaml` | `(not asserted - see MISSION_10_ARTIFACT_MANIFEST.json)` |
| Review Tooling Adversarial Tests | `tests/unit/test_phase5_review_tooling.py` | `(not asserted - see MISSION_10_ARTIFACT_MANIFEST.json)` |
| Synthetic Evaluation Boundary Tests | `tests/unit/test_phase5_synthetic_evaluation.py` | `1a8f4e14a23d554d4fc6e7620b42bd878c8224395de3106a671c7f461e2b51a1` |
| Media Access Gate Tests | `tests/unit/test_media_authorization.py` | `(not asserted - see MISSION_10_ARTIFACT_MANIFEST.json)` |

---

## 4. Execution Commands for Replication

### 4.1 Running the Safe Synthetic Test Suite

Running `pytest` blindly across the entire repository executes `tests/unit/test_phase4_integration_preflight.py`, which invokes `ffprobe` directly on real `.mov` files in `data/raw/layer_b/v2/`. To guarantee zero media access and prevent unmonitored disk probing, routine CI and audit replication must execute strictly via the canonical synthetic runner:

```bash
cd /Users/sayemuddin/Desktop/Train_automation
.venv/bin/python scripts/run_synthetic_tests.py
```

Expected output:
```text
=== Synthetic Test Suite Runner ===
Total repository test files: 107
Selected safe test files (SYNTHETIC_ONLY + METADATA_ONLY): 92 (see MISSION_10_TEST_CLASSIFICATION_AND_SAFE_RUNNER.md)
Blocked non-synthetic test files: 10

Executing pytest across 92 manifest-verified safe test files under the read-blocking guard...
Pytest exited with return code: 0
Test summary: 1902 passed in 33.42s
Execution wall-clock time: 34.40s
Execution report written to: /Users/sayemuddin/Desktop/Train_automation/reports/synthetic_test_report.json
```

### 4.2 Running Phase 5 Specific Remediation Unit Tests

To replicate the 76 focused Phase 5 remediation tests (47 review tooling + 17 synthetic evaluation + 12 media authorization):

```bash
cd /Users/sayemuddin/Desktop/Train_automation
export PYTHONPATH=src
.venv/bin/pytest tests/unit/test_phase5_review_tooling.py tests/unit/test_phase5_synthetic_evaluation.py tests/unit/test_media_authorization.py -v
```

Expected output:
```text
============================== 76 passed in 0.44s ==============================
```

### 4.3 Running Code Formatting and Linter Checks

```bash
.venv/bin/ruff check src/railway_detection/annotation/phase5_review_tooling.py src/railway_detection/annotation/media_authorization.py scripts/run_synthetic_tests.py tests/unit/test_phase5_review_tooling.py tests/unit/test_phase5_synthetic_evaluation.py tests/unit/test_media_authorization.py
.venv/bin/ruff format --check src/railway_detection/annotation/phase5_review_tooling.py src/railway_detection/annotation/media_authorization.py scripts/run_synthetic_tests.py tests/unit/test_phase5_review_tooling.py tests/unit/test_phase5_synthetic_evaluation.py tests/unit/test_media_authorization.py
```

Expected output:
```text
All checks passed!
```
