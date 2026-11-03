# Mission 13 — WP13.1 M-02 Official-Evaluation Security Audit

**Auditor:** independent, read-only. **Date:** 2026-11-02. **HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`.
**Method:** static review of `src/railway_detection/evaluation/{evaluation_runner,replay_producer,input_contracts,governance,execution_gate,output_contracts}.py` plus synthetic-only probes (`mission13_probes/probe_m02.py`, `probe_receipt.py`, `probe_outdir.py`). No repository data was opened.

## 1. Verdict

| Question | Result |
|---|---|
| Does the original Mission 11B exploit (caller-built `_OfficialPermit` + matching digest) still work? | **No — verified closed** |
| Can a caller manufacture `official_authorization_verified` through the runner API? | **No — verified** |
| Does public REAL evidence get rejected *before any producer / cache / media / source read*? | **Not in every case — see F13-02 and F13-01** |
| Is the Mission 12 description of EVAL-AUTH ("expiration/revocation rechecked") accurate? | **No — EVAL-AUTH has no expiry or revocation field (F13-10)** |

M-02 itself is **FIXED_VERIFIED** for the exploit it described. Three related defects were found on the same boundary; they are listed in §5.

## 2. Source map

| Element | Location |
|---|---|
| `_OfficialPermit` (legacy, inert) | `evaluation_runner.py:79-92` |
| `_OFFICIAL_CONTEXT_TOKEN`, `_VerifiedOfficialAuthorization` | `evaluation_runner.py:95-111` |
| public `run_from_manifest` (classification check) | `evaluation_runner.py:206-230` |
| private `_run_from_manifest_verified` | `evaluation_runner.py:232-325` |
| `run_official` (only context issuer) | `evaluation_runner.py:362-469` |
| public `run` | `evaluation_runner.py:565-584` |
| `_run_verified` (context gate for REAL) | `evaluation_runner.py:586-640` |
| result marker `official_authorization_verified` | `evaluation_runner.py:793-797`; type `output_contracts.py:31` |
| readiness before any replay | `replay_producer.py:119-134` → `execution_gate.assess_official_phase12_readiness` |
| EVAL-AUTH verifier | `governance.py:421-531` |

## 3. Adversarial matrix (all synthetic; reproduce with `probe_m02.py`)

| # | Case | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | Caller-built `_OfficialPermit` into `run(REAL)` | refuse | `OFFICIAL_AUTHORIZATION_CONTEXT_REQUIRED` | PASS |
| 2a | Forged `_VerifiedOfficialAuthorization` (own token) into `run()` | refuse | same code | PASS |
| 2b | Forged context into `run_from_manifest()` | refuse | same code | PASS |
| 2c | Forged context (wrong token) into private `_run_from_manifest_verified` | refuse | same code | PASS |
| 3 | Permit whose `manifest_sha256` equals the real manifest digest | refuse, no reads | refused; 0 source reads | PASS |
| 4 | Caller-supplied "authorization context" of any shape | refuse | refused by presence check (`run`) and by token identity (`_run_verified`) | PASS |
| 5 | REAL via public `run()` | refuse | refused before computation | PASS |
| 6 | REAL via `run_from_manifest(evidence_classification=REAL)` | refuse, no reads | refused; 0 source reads | PASS |
| **6b** | REAL **manifest**, `evidence_classification` kwarg **omitted** | refuse **before any read** | refused only *after* every declared source file was opened, hashed and JSON-parsed **twice** | **FAIL (F13-02)** |
| **6c** | kwarg = SYNTHETIC but manifest says REAL | refuse before any read | `MANIFEST_BINDING_MISMATCH` after the same double read | **FAIL (F13-02)** |
| 7 | Permit applied to a synthetic manifest | refuse | refused | PASS |
| 8 | Context from another runner instance | not reusable | Contexts are **not bound to an instance, operation, dataset scope or time**; they are protected only by the module-private token and by never being returned to callers | NOT AS DESIGNED (residual, F13-15) |
| 9 | Context from a previous evaluation reused on another manifest | refuse | refused by `context.manifest_sha256 != input_manifest_sha256` (digest binding) | PASS for a different manifest; nothing prevents reuse on the *same* manifest |
| 10 | Context reused for a different operation / dataset scope | refuse | the context carries no operation/dataset/event fields; scope is checked only once, inside the producer, at issue time | NOT AS DESIGNED (residual, F13-15) |
| 11 | Failure before producer/cache/media/protected operation | yes | public REAL APIs: yes (producer never called, probe tripwire empty). 6b/6c: no. `run_official` on the real repository hashes the production checkpoints inside the readiness gate *before* concluding EVAL-AUTH is absent (`execution_gate.py:869`) | PARTIAL |
| 12a | Make `official_authorization_verified=True` through the runner | impossible | impossible without the private token | PASS |
| 12b | Make it true by constructing the object | impossible | `EvaluationProvenance(..., official_authorization_verified=True)` is a plain frozen dataclass and constructs freely; no consumer verifies it | residual (F13-15) |

Residual probe R1: importing `_OFFICIAL_CONTEXT_TOKEN` by name from the module and calling the private `_run_from_manifest_verified` passes the authorization gate. This is the documented same-process limit (private names, no OS isolation) and is **not** treated as a defect.

## 4. What the official path independently validates

`run_official` → `RealEventReplayProducer.produce` → `assess_official_phase12_readiness` re-reads the on-disk state on every call (no caching). Validated against live artifacts: EVAL-AUTH record, `authorized_by` on the allowlist, record SHA-256, exact `operation` and `stage`, physical-operations flag false, seven binding hashes (`decision_policy`, `event_split_decision`, `frozen_config`, `input_manifest`, `protocol_profile`, `r04_scope_decision`, `stage21_promotion_receipt`), promotion receipt and review-record hashes, event/cohort/split/camera scope, protocol profile.

| Item requested | Status in code |
|---|---|
| Authorization identity | present (`authorization_id`, record hash) |
| Signer | allowlist membership only; no signature (`signature: null` is *required*) |
| **Expiry** | **absent from EVAL-AUTH** (`governance.py:_EVAL_AUTH_KEYS`, no `expires_at_utc`) |
| **Revocation** | **absent from EVAL-AUTH** (no `revoked`, no `status`); the only revocation is deleting the file or letting a binding drift |
| Operation scope | present (`scope.operation`) |
| Dataset / event scope | indirect, via manifest and receipt hash bindings |
| Protocol / manifest / model-configuration binding | present |
| Promotion receipt binding | present |
| Current state at execution | yes, re-read on each call |

`AUTH-MEDIA-ACCESS` and `AUTH-DESCRIPTIVE-EVAL-EXEC` do carry `expires_at_utc` and `revoked`; EVAL-AUTH does not. Mission 12's design note (`MISSION_12_M02_SECURITY_DESIGN.md`, "expiration/revocation") overstates this.

## 5. New and related findings

| ID | Sev | Summary | Evidence |
|---|---|---|---|
| F13-02 | MEDIUM | Public `run_from_manifest` decides "real or not" from the *kwarg*, but `_run_from_manifest_verified` derives the class from the *manifest*. A REAL manifest with the kwarg omitted triggers `load_evaluation_input_manifest(verify_sources=True)` **twice** (`evaluation_runner.py:257-269`) before `_run_verified` refuses (`:622-638`). | `probe_m02.py` cases 6b/6c: 6 source reads, then refusal |
| F13-01 | HIGH | The loader that this path calls opens and hashes any in-root `source_path` with **no media guard** (`input_contracts.py:82-92`, `:213-216`), reports the actual SHA-256 inside `SOURCE_HASH_MISMATCH`, and is allowlisted in the opener tripwire as "reads the evidence manifest JSON". Details in the media-reader audit. | `probe_media.py` I1 |
| F13-10 | MEDIUM | EVAL-AUTH and the promotion receipt have no expiry/revocation; a hand-computed receipt passes `verify_promotion_receipt` (probe R0). | `probe_receipt.py` R0, R7, R8 |
| F13-15 | LOW | Context not instance/operation/time bound; result marker is an unsigned bool; `assert` at `evaluation_runner.py:405` is stripped by `python -O` (compensated by the later `not context.authorization_sha256` check). | probe 12b, R1 |

## 6. Trust-boundary assessment

Mission 12 states the guard is a Python-level API boundary, not a cryptographic or OS boundary. That is accurate and is not held against it. The audit applied the narrower standard: *an ordinary caller of the public API must not be able to create authorization*. That standard is met for the M-02 exploit. It is **not** met for the "fails before any protected operation" requirement in cases 6b/6c, and the unsigned result marker cannot be used by a downstream reader as proof of authorization.

## 7. Disposition

- M-02 original finding: **FIXED_VERIFIED** (independent probes, not only the Mission 12 tests).
- WP13.1 overall: **PARTIALLY_VERIFIED** — F13-01 (HIGH) and F13-02 (MEDIUM) remain on the same boundary.
- This audit does not authorize real-data execution. No EVAL-AUTH, AUTH-MEDIA-ACCESS, AUTH-DESCRIPTIVE-EVAL-EXEC or promotion receipt exists in the repository.
