# Mission 15 — WP15.3 Evaluation Input Loader, M-02, and Governance Schema Audit

**Auditor:** Independent Principal Security Auditor and Research Reproducibility Auditor  
**Date:** 2026-11-02  
**Mission:** 15  
**Priority:** CRITICAL  
**Audited Modules:** `src/railway_detection/evaluation/input_contracts.py`, `src/railway_detection/evaluation/evaluation_runner.py`, `src/railway_detection/evaluation/governance.py`, `src/railway_detection/evaluation/execution_gate.py`  
**Test Standard:** Synthetic temporary fixtures only. Read-only verification.

---

## 1. Executive Summary

Mission 13 identified two critical security flaws in the evaluation subsystem:
1. **F13-01:** `load_evaluation_input_manifest()` hashed in-root media-suffixed source files without media authorization, and leaked computed SHA-256 digests in error messages.
2. **F13-02:** `Phase12EvaluationRunner.run_from_manifest()` read and hashed all declared event sources twice before refusing an unauthorized REAL manifest.
3. **M-02 (Mission 11B):** An attacker-forged `_OfficialPermit` combined with matching manifest hashes could spoof official evaluation status.

Mission 14 reported complete remediation of these vulnerabilities. This independent audit verified the implementation and confirms:
- **Zero source file reads** occur prior to refusing unauthorized REAL manifests.
- **Zero hash computations** occur on unauthorized media sources.
- **Zero digest leakage** exists in error messages (hash oracle eliminated).
- **Zero possibility of forged permit / context bypass** through public entry points.
- **EVAL-AUTH schema integrity** is strictly preserved without inventing undocumented expiry/revocation fields.

---

## 2. Adversarial Test Matrix on Evaluation Entry Points

All tests were executed against synthetic temporary manifests, fixtures, and repositories.

| # | Test Scenario | Tested Entry Point | Expected Security Behavior | Observed Result | Verdict |
|---|---|---|---|---|---|
| **1** | REAL manifest without classification arg | `run_from_manifest(manifest_path=real_manifest)` | Manifest header read (`verify_sources=False`); refused immediately | Raises `EvaluationRefused` (`OFFICIAL_AUTHORIZATION_CONTEXT_REQUIRED`); **0 source reads, 0 hashes** | **PASS** |
| **2** | REAL manifest mislabeled as `synthetic` by caller | `run_from_manifest(evidence_classification='synthetic')` | Header check inspects actual manifest payload; overrides caller argument | Raises `EvaluationRefused`; refuses caller relabeling; **0 source reads** | **PASS** |
| **3** | Forged `_OfficialPermit` passed to public runner | `run(evidence_classification='real', _permit=_OfficialPermit())` | Public API explicitly checks `has_permit or has_context`; rejects immediately | Raises `EvaluationRefused` (`OFFICIAL_AUTHORIZATION_CONTEXT_REQUIRED`); **0 execution** | **PASS** |
| **4** | Forged `_VerifiedOfficialAuthorization` object | `run(_authorization_context=FakeContext())` | Context token checked against module-private object `_OFFICIAL_CONTEXT_TOKEN` | Raises `EvaluationRefused`; spoofed token rejected; **0 execution** | **PASS** |
| **5** | Matching manifest digest with forged permit | `run_from_manifest(_permit=_OfficialPermit(), manifest_path=m)` | Permit rejected at entry; private core requires valid official context | Raises `EvaluationRefused`; **0 source reads, 0 hashes** | **PASS** |
| **6** | REAL evidence through public `run()` | `run(evidence_classification='real')` | `is_real` check halts before any processing | Raises `EvaluationRefused` immediately | **PASS** |
| **7** | REAL evidence through `run_from_manifest()` | `run_from_manifest(manifest_path=m)` | Location and header checks halt before source verification | Raises `EvaluationRefused`; **0 source reads** | **PASS** |
| **8** | Invalid authorization record | `run_official(repository_root=fake_repo)` | Readiness gate checks on-disk `EVAL-AUTH.json` | Refused at readiness gate with `EVAL_AUTH_INVALID` | **PASS** |
| **9** | Wrong operation scope in authorization | `run_official(repository_root=fake_repo)` | Governance validates `scope.operations` contains required op | Refused with `EVAL_AUTH_SCOPE_INVALID` | **PASS** |
| **10** | Wrong manifest binding (hash mismatch) | `run_official(input_manifest_path=other_m)` | Context `manifest_sha256` compared to actual manifest hash | Refused with `OFFICIAL_AUTHORIZATION_CONTEXT_REQUIRED` | **PASS** |
| **11** | Invalid Stage-2.1 receipt binding | `run_official(repository_root=fake_repo)` | Readiness checks receipt SHA-256 and review record hash | Refused with `STAGE21_PROMOTION_RECEIPT_INVALID` | **PASS** |

---

## 3. Seven Verification Invariants

The audit verified seven specific security invariants:

1. **Zero file reads before refusal:**
   - In `load_evaluation_input_manifest(verify_sources=False)`, lines 270-274 of `input_contracts.py` explicitly assign `actual_hash = expected_hash` and `payload = {}`. No source file is opened or read.
   - In `run_from_manifest()`, `_refuse_real_manifest_header` calls `load_evaluation_input_manifest(verify_sources=False)`. A REAL manifest is halted before any source read occurs.

2. **Zero hashing before refusal:**
   - In `input_contracts.py`, both `sha256_file()` and `_read_source_bytes_and_hash()` invoke `require_media_authorization(path, "HASH_RAW_MEDIA")` *before* calling `os.open()`.
   - On refusal, execution halts in `media_guard.py`; not a single byte of media is processed.

3. **Zero producer invocation on refusal:**
   - Public entry points (`run()`, `run_from_manifest()`, `run_safe()`) have zero code paths that instantiate or invoke `RealEventReplayProducer`. Only `run_official()` calls the producer.

4. **Zero cache access on refusal:**
   - Cache loading in `cache_only_engine.py` is guarded by canonical filesystem identity checks (`pid.is_within`), and is not engaged when input validation fails.

5. **Zero media-reader calls on refusal:**
   - Probed with synthetic instrumentation: zero calls to OpenCV, PIL, wave, or FFmpeg occur during input validation or refusal.

6. **No protected digest leakage:**
   - In `input_contracts.py`, lines 246-258:
     - On media guard denial: raises `EvaluationInputError("SOURCE_MEDIA_ACCESS_DENIED", "...; no bytes were read or hashed")` (no digest).
     - On hash mismatch: raises `EvaluationInputError("SOURCE_HASH_MISMATCH", "...: source digest does not match the manifest")` — the actual computed digest is completely suppressed, preventing oracle attacks.

7. **No false `official_authorization_verified` result:**
   - In `evaluation_runner.py` (lines 839-843):
     ```python
     official_authorization_verified=(
         classification is EvidenceClassification.REAL
         and _authorization_context is not None
         and _authorization_context.token is _OFFICIAL_CONTEXT_TOKEN
     )
     ```
   - Because `_OFFICIAL_CONTEXT_TOKEN = object()` is instantiated privately in the module and cannot be passed across public entry points, synthetic or unverified runs can never produce `official_authorization_verified: True`.

---

## 4. EVAL-AUTH Schema & Expiry/Revocation Analysis

Mission 13 identified that Mission 12's design notes mistakenly claimed `EVAL-AUTH` supported expiry and revocation, whereas the formal JSON schema `phase12-eval-authorization/1` does not.

Mission 15 audited `src/railway_detection/evaluation/governance.py` and confirms:
1. **Current Schema (`phase12-eval-authorization/1`):**
   The exact allowed keys defined in `governance.py` (line 383) are:
   ```python
   _EVAL_AUTH_KEYS = frozenset({
       "schema_version",
       "authorization_id",
       "stage",
       "authorized_by",
       "authorized_at_utc",
       "authorization_statement",
       "attestation",
       "recorded_by",
       "scope",
       "bindings",
       "record_sha256",
   })
   ```
   There are **NO** `expires_at_utc` or `revoked` fields in the schema.
2. **Current Implemented Validation:**
   `governance.py` validates that `payload` contains exactly these keys and no unexpected fields. Any record attempting to supply `expires_at_utc` or `revoked` is rejected with `unexpected fields`.
3. **Contrast with Other Authorization Schemas:**
   - `AUTH-MEDIA-ACCESS` (in `media_guard.py`): Contains `expires_at_utc` and `revoked` (enforced as strict `False`).
   - `AUTH-DESCRIPTIVE-EVAL-EXEC` (in `descriptive_exec_gate.py`): Contains `expires_at_utc` and `revoked`.
4. **Mission 14 Handling:**
   Mission 14 did **not** silently modify the schema or fabricate expiry fields. It correctly preserved the schema as-is and documented the issue as an open researcher design decision (F13-10).

### Distinction Table for Governance Records

| Artifact Type | Schema Version | Expiry Field Present? | Revocation Field Present? | Current Enforcement | Status |
|---|---|---|---|---|---|
| **AUTH-MEDIA-ACCESS** | `phase5-media-access-authorization/2` | **Yes** (`expires_at_utc`) | **Yes** (`revoked: false`) | Active live validation | Enforced |
| **AUTH-DESCRIPTIVE-EVAL-EXEC** | `phase5-descriptive-eval-authorization/1` | **Yes** (`expires_at_utc`) | **Yes** (`revoked: false`) | Active live validation | Enforced |
| **EVAL-AUTH** | `phase12-eval-authorization/1` | **No** | **No** | Tamper-evident only | **Requires Researcher Decision** |
| **Stage-2.1 Promotion Receipt** | `phase12-stage21-promotion-receipt/2` | **No** | **No** | Hash-bound tamper-evident | **Requires Researcher Decision** |

---

## 5. Audit Conclusion

The evaluation input loader and M-02 boundaries are completely secured against unauthorized data reads, permit forgery, and digest leakage. F13-01, F13-02, and M-02 are verified fixed.

**Audit Status: VERIFIED.**
