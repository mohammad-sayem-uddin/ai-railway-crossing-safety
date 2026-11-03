# Mission 15 — WP15.9 Researcher Decision Register

**Auditor:** Independent Principal Security Auditor and Research Reproducibility Auditor  
**Date:** 2026-11-02  
**Mission:** 15  
**Priority:** DECISION REQUIRED — AUDITOR MUST NOT DECIDE  
**Standard:** Neutral, comprehensive documentation of current state, options, risks, and trade-offs. No schema modification or policy adoption performed.

---

## Notice of Auditor Non-Authority

In accordance with Section 12 of the Mission 15 charter:
- The auditor does **not** decide governance policy or research architecture.
- No schema or implementation has been modified to adopt any option.
- No option is represented as preferred or adopted.
- This document exists solely to record the required decisions for the Principal Investigator and human research leads.

---

## Decision 1: Model Checkpoint Integrity Hashing Authorization (F13-09)

### 1. Context and Current Implementation
The production readiness gate (`src/railway_detection/evaluation/execution_gate.py`) and frozen configuration validator (`src/railway_detection/experiments/frozen_config.py`) verify model weights before running evaluations by computing the SHA-256 hash of production checkpoint files (e.g. `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`). This read is performed using `open(path, "rb")` in 1 MiB chunks.
Currently, this hashing does **not** require an `AUTH-MEDIA-ACCESS` or `AUTH-CHECKPOINT-ACCESS` governance record. The media guard excludes `.pt` and `.pth` files from `MEDIA_SUFFIXES` (listing them in `KNOWN_NON_MEDIA_SUFFIXES`), because weights are model parameters rather than recorded railway media.

### 2. Current Formal Schema
There is currently no formal authorization schema for checkpoint access in `data/governance/`.

### 3. Risks
- **Over-exposure:** If checkpoints are considered proprietary or sensitive research artifacts, reading them during preliminary readiness checks without explicit authorization exposes them to automated processes.
- **Ambiguity:** Missions 12, 13, and 14 debated whether read-only checkpoint hashing constitutes an unauthorized access event. Absent an explicit policy, the boundary between "system integrity verification" and "unauthorized research access" remains ambiguous.

### 4. Available Options
- **Option 1A (Maintain Non-Media Status):** Formally define checkpoint files (`.pt`, `.onnx`, `.safetensors`) as system weights, exempt from media access authorization, permitting read-only integrity hashing during readiness checks.
- **Option 1B (Introduce AUTH-CHECKPOINT-ACCESS):** Require an explicit on-disk authorization record (`AUTH-CHECKPOINT-ACCESS.json`) before any function may open, read, or hash checkpoint files.
- **Option 1C (Bind Checkpoint Hashing to EVAL-AUTH):** Prohibit checkpoint hashing until `EVAL-AUTH.json` is validated, deferring weight integrity checks until official evaluation time.

### 5. Consequences
- **Option 1A:** Simplifies preflight readiness audits; enables tests to verify checkpoint bindings without managing separate keys; requires clarifying that Mission 12's actions were not a policy breach.
- **Option 1B / 1C:** Maximizes data protection; requires updating `frozen_config.py` and `execution_gate.py`; blocks automated readiness preflights unless authorized.

### 6. Required Researcher Decision
*The Principal Investigator must decide whether reading/hashing production model checkpoints requires explicit governance authorization, and if so, under which governance schema.*

---

## Decision 2: Expiry and Revocation Fields in EVAL-AUTH and Promotion Receipt (F13-10)

### 1. Context and Current Implementation
`src/railway_detection/evaluation/governance.py` validates `EVAL-AUTH.json` (schema `phase12-eval-authorization/1`) and Stage-2.1 promotion receipts (schema `phase12-stage21-promotion-receipt/2`).
In both schemas, validation checks strict key presence, signer identity on the allowlist, and bound document hashes. Neither schema includes `expires_at_utc` or `revoked` fields. A recorded evaluation authorization or promotion receipt is valid indefinitely unless manually removed or altered (which invalidates `record_sha256`).

### 2. Current Formal Schema
Both `_EVAL_AUTH_KEYS` and `_PROMOTION_RECEIPT_KEYS` define exact key sets without expiry or revocation.

### 3. Risks
- **Indefinite Validity:** An `EVAL-AUTH` recorded today could theoretically be used to run an official evaluation in the distant future after code or research conditions have shifted.
- **No Revocation Mechanism:** If an authorized reviewer wishes to invalidate an approval without deleting the artifact, there is no standardized `revoked: true` flag.

### 4. Available Options
- **Option 2A (Maintain Schema Version 1 — Tamper-Evident Only):** Preserve the current schema where an authorization is a point-in-time recorded statement bound by document hashes. Revocation is handled by moving/removing the record.
- **Option 2B (Upgrade to Schema Version 2 with Expiry & Revocation):** Increment schema versions (`phase12-eval-authorization/2` and `phase12-stage21-promotion-receipt/3`), adding mandatory `expires_at_utc` and `revoked` fields, aligning them with `AUTH-MEDIA-ACCESS/2`.

### 5. Consequences
- **Option 2A:** Requires zero code changes; keeps schemas clean and minimal; avoids introducing time-sensitive test failures in reproducible test environments.
- **Option 2B:** Strengthens long-term governance; requires updating `governance.py`, validation tests, and documentation; requires researchers to specify expiration windows for all future authorizations.

### 6. Required Researcher Decision
*The Principal Investigator must decide whether to retain the current tamper-evident point-in-time schema (v1) or upgrade the governance schemas (v2) to require expiration timestamps and revocation flags.*

---

## Decision 3: Descriptive Back-Stream Cache Route (M-03)

### 1. Context and Current Implementation
The descriptive evaluation route evaluates candidate gate policy performance against historical detection logs. Mission 11B identified that descriptive evaluation could benefit from an optimized cache route for back-stream camera data. Mission 13 and 14 confirmed that while the front-stream cache route is fully implemented in `cache_only_engine.py`, the descriptive back-stream route remains architecturally undefined.

### 2. Current Formal Schema / Implementation
`src/railway_detection/evaluation/cache_only_engine.py` operates on defined cache directories. No dedicated back-stream cache schema is adopted.

### 3. Risks
- **Performance:** Descriptive evaluation on dual-camera events may experience latency if back-stream features are not pre-cached.
- **Specification Gap:** Unclear whether the descriptive benchmark requires dual-camera back-stream data or focuses strictly on primary camera streams.

### 4. Available Options
- **Option 3A (Single-Camera Primary Scope):** Formally define the descriptive benchmark scope as primary-camera only, closing M-03 as not required.
- **Option 3B (Implement Back-Stream Cache Architecture):** Design and implement a dual-stream cache provider in `cache_only_engine.py` supporting both primary and secondary camera streams.

### 5. Consequences
- **Option 3A:** Closes the open design question immediately without additional code complexity.
- **Option 3B:** Enhances dual-camera research capability; requires new cache schemas and integration tests.

### 6. Required Researcher Decision
*The research leads must decide whether descriptive evaluation requires a back-stream cache implementation or whether primary-stream caching satisfies research requirements.*

---

## 4. Decision 4: Manuscript Author and Citation Reconciliation (M-08)

### 1. Context and Current Implementation
`docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md` contains placeholder references and citations (e.g. `[Author et al., 2026]`, `[citation needed]`).

### 2. Current State
Mission 14 drafted notice C9 in `docs/generated/phase5/MISSION_14_DOCUMENTATION_RECONCILIATION.md` listing missing bibliographic entries. The manuscript text remains untouched.

### 3. Required Researcher Decision
*The authors must supply formal bibliographic citations and author affiliations prior to journal/conference submission.*

---

## 5. Decision 5: Authorization Context Binding & Signature Model (F13-15)

### 1. Context and Current Implementation
In `src/railway_detection/evaluation/evaluation_runner.py`, `_VerifiedOfficialAuthorization` uses an in-memory sentinel object (`_OFFICIAL_CONTEXT_TOKEN = object()`) to pass verified authorization context from `run_official` to `_run_from_manifest_verified`.

### 2. Available Options
- **Option 5A (In-Memory Sentinel — Current):** Rely on Python module encapsulation and object identity (`is _OFFICIAL_CONTEXT_TOKEN`).
- **Option 5B (Cryptographic HMAC / Public Key):** Issue a cryptographically signed authorization token using an ephemeral or configured key.

### 3. Consequences
- **Option 5A:** Simple, zero-overhead, completely effective against external callers within the same Python process; cannot survive cross-process IPC.
- **Option 5B:** Supports distributed execution across multiple machines or microservices; introduces key management complexity.

### 4. Required Researcher Decision
*The engineering leads must determine whether in-memory token encapsulation is sufficient for the single-node research runner, or if a cryptographic signing layer is required.*

---

## 6. Summary Matrix of Decisions Required

| # | Topic | Finding Ref | Impacted Modules | Decision Authority |
|---|---|---|---|---|
| **1** | Checkpoint Hashing Authorization | F13-09 | `frozen_config.py`, `execution_gate.py` | Principal Investigator |
| **2** | EVAL-AUTH Expiry / Revocation | F13-10 | `governance.py` | Principal Investigator / Governance Lead |
| **3** | Descriptive Back-Stream Cache | M-03 | `cache_only_engine.py` | Research Team Lead |
| **4** | Manuscript Citations | M-08 | `PAPER_DRAFT_*.md` | Lead Authors |
| **5** | Context Cryptographic Binding | F13-15 | `evaluation_runner.py` | Lead Software Architect |
