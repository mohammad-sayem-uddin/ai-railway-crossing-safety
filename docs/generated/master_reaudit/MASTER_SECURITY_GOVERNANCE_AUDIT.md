# MASTER SECURITY AND GOVERNANCE AUDIT

**Project:** Train Gate Automation — Bangladesh  
**Audit Mission:** Master Mission 16A  
**Auditor:** Independent Principal Security Auditor and Software Architect  
**Status:** COMPLETE AUDIT  
**Date:** 2026-11-02  
**Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Execution Authority:** NONE  
**Security Bypass Authority:** NONE  

---

## 1. Executive Summary

This audit provides the retrospective and technical security evaluation of the Train Gate Automation repository from the initial conception of data-access restrictions (Mission 10) through the security remediation of Mission 14 and independent verification of Mission 15.

The core conclusions are:
1. **The central media security boundary is intact and defensive.** The path canonicalization engine (`path_identity.py`) and media guard (`media_guard.py`) reliably intercept and block unauthorized file opening, decoding, hashing, copying, and subprocess invocations against protected production data.
2. **The test execution boundary is fully restored.** The synthetic test runner operates under a fail-closed pytest plugin (`access_guard_plugin.py`) backed by an explicit test classification manifest (`test_access_manifest.yaml`). Exactly 2,198 tests pass across 100 safe files with 0 access violations, and 21 protected test files are strictly quarantined.
3. **Historical security breaches have been mitigated.** Critical vulnerabilities, including M-02 permit forgery, dashboard directory traversal (F13-05), scratch script subshell invocations (F13-06), and reader bypasses, have been verified as remediated.
4. **Policy-level governance gaps remain.** Checkpoint hashing authorization policy (F13-09), EVAL-AUTH token lifecycle enhancements (F13-10), process context token binding (F13-15), and Git preservation tracking (F13-17 / N-06) await explicit human researcher decisions.
5. **Real-data execution remains strictly unauthorized.**

---

## 2. Chronological Evolution of the Security Boundary (Missions 10–15)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ MISSION 10 — Initial Security Boundary Inception                            │
│ - Introduced basic access_guard.py and mock permit mechanisms               │
│ - Flaw: Permissions relied on unverified in-memory flags; bypassable        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ MISSION 11–12 — Incidents and Flawed Isolation                              │
│ - Mission 12 ran protected test files directly (F13-08 incident)            │
│ - Permit forgery vulnerability (M-02) allowed fabricated permits to pass    │
│ - Raw media readers invoked OpenCV/FFmpeg without pre-flight security check │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ MISSION 13 — Comprehensive Adversarial Security Audit                       │
│ - Uncovered 18 findings (F13-01 through F13-18)                             │
│ - Proved test runner was executing against production checkpoints           │
│ - Discovered path traversal in dashboard and unescaped scratch scripts      │
│ - Disposition: FAILED / SEVERELY COMPROMISED                                │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ MISSION 14 — Remediation and Engineering Recovery                           │
│ - Authored centralized path canonicalization (path_identity.py)             │
│ - Hardened media_guard.py: pre-flight authorization before any OS read      │
│ - Reclassified 121 test files: 100 safe (78 synthetic, 22 metadata), 21 quarantine│
│ - Eliminated M-02 permit forgery: fail-closed JSON schema verification      │
│ - Fixed dashboard traversal and scratch script wrappers                     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ MISSION 15 — Independent Adversarial Verification                           │
│ - Re-ran safe runner twice: 2,198 passed tests, 0 failures, 0 violations    │
│ - Adversarial path traversal tests verified blocked                         │
│ - Verified pre-edit backups (33 files preserved with authentic timestamps)  │
│ - Disposition: PHASE_5_ENGINEERING_RECOVERY_VERIFIED                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technical Verification of Security Modules

### 3.1 Path Identity and Canonicalization (`src/railway_detection/safety/path_identity.py`)
- **Canonicalization Mechanism:** Implements `canonical_path(p)` using `os.path.realpath(os.path.abspath(...))` combined with Unicode normalization (`unicodedata.normalize('NFC', ...)`).
- **Path Traversal Defense:** `resolve_untrusted_relative(base, untrusted_rel)` prevents `..` directory escapes and null-byte injection.
- **Location Matching:** `is_within(candidate, parent)` performs strict relative-path decomposition rather than brittle string prefix matching, preventing attacks such as `/data/raw_fake` bypassing `/data/raw`.
- **Verdict:** Robust, standard-compliant, and cryptographically sound path normalization.

### 3.2 Media Guard (`src/railway_detection/safety/media_guard.py`)
- **Pre-Flight Authorization:** Any call to `require_media_authorization(path, operation)` intercepts operations before disk access occurs:
  - Valid operations: `open`, `read`, `decode`, `hash`, `copy`, `inspect`.
  - Checks if path is classified as synthetic via `is_synthetic_location(path)`.
  - For non-synthetic paths, verifies existence of an authentic `AUTH-MEDIA-ACCESS` token in `data/governance/authorizations/`.
- **Permit Forgery Defense (Fixing M-02):**
  - Requires valid JSON token conforming to `MEDIA_ACCESS_SCHEMA_VERSION = "1.0.0"`.
  - Validates cryptographic SHA-256 signatures and checks token expiration dates.
  - Rejects mock or unsigned permits unconditionally.
- **Fail-Closed Subprocess Guarding:** `require_media_command_authorization(cmd)` parses shell and CLI arguments, intercepting `ffmpeg`, `ffprobe`, `opencv`, or `pil` commands before subprocess launch.

### 3.3 Test Suite Access Guard Plugin (`src/railway_detection/safety/access_guard_plugin.py`)
- Hooks directly into pytest runtime (`pytest_runtest_setup`, `pytest_runtest_call`).
- Inspects active file against `tests/test_access_manifest.yaml`.
- Rejects execution of any test not marked `SYNTHETIC_ONLY` or `METADATA_ONLY` unless a valid execution token is present.
- Blocks real media directory access dynamically during test runs.

---

## 4. Deep-Dive Audit of Remaining Findings and Gaps

The four unresolved findings from Mission 13–15 were evaluated:

### 4.1 F13-08: Mission 12 Execution Incident
- **Historical Event:** On 2026-10-13 at 10:36:45, Mission 12 ran `test_phase12_governance.py` and `test_phase12_official_replay.py`.
- **Forensic Assessment:**
  - Python bytecode cache (`__pycache__`) timestamps confirm the test modules were loaded and run.
  - However, no system-level disk read trace exists establishing that raw checkpoint bytes were loaded into memory or hashed.
  - Mission 15 formally classified this incident as:  
    `EXECUTION_CONFIRMED_ACCESS_NOT_ESTABLISHED`
  - **Verdict:** This incident does not represent an active vulnerability in the current codebase. It requires formal human incident acknowledgement prior to official Phase 5 authorization.

### 4.2 F13-09: Production Checkpoint Hashing Policy
- **Issue:** The system readiness gate seeks to verify the SHA-256 hash of production model weights (`experiments/vision/39f402dfe460/checkpoints/weights/best.pt`) prior to evaluation. However, reading the checkpoint bytes to compute its hash is itself a media access operation prohibited under default safety rules.
- **Current Status:** Circular dependency unresolved.
- **Recommended Solution:** Adopt pre-computed detached SHA-256 sidecar verification signed by the lead researcher, avoiding runtime weight reads during readiness checks.

### 4.3 F13-10: EVAL-AUTH Token Lifecycle & Revocation
- **Issue:** The `EVAL-AUTH` token specification lacks automated revocation lists (CRL), nonce tracking for single-use execution, and automatic time-to-live (TTL) expiration enforcement.
- **Impact:** An authorized token, once issued, could theoretically be re-used multiple times.
- **Recommended Solution:** Upgrade schema to `EVAL-AUTH` v2.0 incorporating cryptographic nonces and explicit execution lease times.

### 4.4 F13-15: Process Context Token Binding
- **Issue:** The runtime authorization context is passed via in-memory thread-local variables. In multi-processing or distributed worker environments, the context could be lost or inadvertently inherited.
- **Impact:** Low risk in single-process synchronous pipelines; potential risk if parallel evaluation runners are introduced.

### 4.5 F13-17 & N-06: Untracked Implementation Code
- **Issue:** Packages under `src/railway_detection/safety/` and `src/railway_detection/annotation/` are untracked in Git (`??` in `git status`).
- **Root Cause:** Absolute Git write prohibition imposed on all audit and remediation agents (`git add`, `git commit` strictly prohibited).
- **Risk Assessment:** High operational risk if workspace is cleaned or cloned without porcelain files. Zero runtime vulnerability in the active environment.
- **Recommended Action:** Repository maintainer must perform a clean, authenticated administrative Git commit to track all verified safety modules.

---

## 5. Security Summary Table

| Subsystem / Control | Verification Standard | Implementation Status | Operational Readiness |
| :--- | :--- | :--- | :--- |
| **Path Identity** | Unicode NFC, realpath, no prefix hacks | Verified in `path_identity.py` | **OPERATIONAL** |
| **Media Guard** | Pre-flight check before open/read/decode | Verified in `media_guard.py` | **OPERATIONAL** |
| **Test Access Guard** | 100 safe files, 21 quarantined | Verified via Pytest plugin | **OPERATIONAL** |
| **M-02 Permit Forgery** | Fail-closed token validation | Blocked with 0 source reads | **OPERATIONAL** |
| **Dashboard Traversal** | Path identity resolution | Verified blocked | **OPERATIONAL** |
| **Scratch Script Guard** | CLI subprocess interceptor | Verified wrapped | **OPERATIONAL** |
| **Checkpoint Integrity** | Cryptographic hash validation | Blocked by safety guard | **AWAITING DECISION (F13-09)** |
| **EVAL-AUTH Token** | Lifecycle and revocation | Token format v1 defined | **AWAITING ENHANCEMENT (F13-10)** |
| **Git Preservation** | Repository version tracking | 25 modified, 388 untracked | **AWAITING MAINTAINER COMMIT** |

---

## 6. Audit Verdict

The security architecture of the Train Gate Automation project has undergone a complete, verifiable recovery. The engineering boundary is fully isolated, safe synthetic testing is repeatable and robust, and all code-level access paths to protected research media are defended by fail-closed guards.

However, because policy-level governance gates (F13-09, F13-10) remain open and no human authorization tokens exist:

**REAL-DATA ACCESS AND EXECUTION REMAIN STRICTLY PROHIBITED.**
