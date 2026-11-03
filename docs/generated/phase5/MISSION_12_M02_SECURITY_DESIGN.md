# Mission 12 — M-02 Security Design

## Problem closed

Mission 11B demonstrated that a caller could instantiate `_OfficialPermit`, supply a matching manifest digest, and obtain a result marked REAL/verified through public `run()` and `run_from_manifest()`.

## New boundary

1. `run()` is public synthetic-only and rejects REAL classification, `_OfficialPermit`, and authorization context arguments.
2. `run_from_manifest()` is public synthetic-only and rejects the same inputs.
3. `_run_verified()` and `_run_from_manifest_verified()` are private computation paths.
4. `run_official()` alone invokes the private manifest path.
5. `run_official()` first calls `RealEventReplayProducer.produce()`.
6. The producer independently assesses on-disk official readiness before loading official inputs.
7. The private `_VerifiedOfficialAuthorization` records the verified authorization digest, attestation level and manifest digest and carries a module-private token.
8. The result marker `official_authorization_verified` is true only for that private context.

## Required bindings rechecked by the existing producer/gate

- actual EVAL-AUTH record, signer/allowlist, status and attestation form;
- expiration/revocation and exact operation/stage;
- promotion receipt and live review-record hashes;
- event, cohort, split and camera scope;
- evaluation manifest digest;
- protocol profile digest;
- frozen configuration and checkpoint provenance;
- model-independent replay evidence;
- metric/condition scope and synchronization decisions.

## Adversarial outcomes

| Case | Result |
|---|---|
| Direct `_OfficialPermit` construction | Object may be constructed, but public REAL APIs reject it |
| Matching digest alone | Rejected with `OFFICIAL_AUTHORIZATION_CONTEXT_REQUIRED` |
| Wrong digest | Rejected |
| Missing/fake authorization record | Rejected by official producer before input consumption |
| Expired/revoked/wrong-scope authorization | Rejected by readiness/authorization gates |
| Wrong protocol/config/model/receipt/manifest | Rejected by live bindings |
| Public `run()` REAL invocation | Rejected before computation |
| Public `run_from_manifest()` REAL invocation | Rejected before computation |
| Synthetic fixture with permit | Rejected |
| Official result marker | Derived from independently verified private context, never permit presence |

## Trust boundary

This is a Python-level API boundary, not cryptographic authorization or an OS sandbox. Arbitrary malicious code already executing in the same process could inspect or monkey-patch Python objects. The remediation requirement is narrower and met: ordinary public callers cannot create official authorization merely by constructing a Python object or matching a manifest digest.