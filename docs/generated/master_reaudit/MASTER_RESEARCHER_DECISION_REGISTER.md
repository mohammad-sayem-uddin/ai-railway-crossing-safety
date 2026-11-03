# MASTER RESEARCHER DECISION REGISTER

**Project:** Train Gate Automation — Bangladesh  
**Audit Mission:** Master Mission 16A  
**Auditor:** Independent Principal Research and Governance Reviewer  
**Status:** COMPLETE AUDIT  
**Date:** 2026-11-02  
**Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Execution Authority:** NONE — AUDITOR DOES NOT DECIDE  

---

## 1. Notice of Auditor Non-Authority

In accordance with strict research integrity and governance rules:
- **The audit agent possesses ZERO governance authority.**
- No options presented below are adopted, signed, or executed by this audit.
- No schema or code has been modified.
- Directional research decisions (RD-001 through RD-055) and proposed schemas remain strictly proposals until formal human sign-off.
- This register serves as the authoritative, comprehensive dossier presented to the Principal Investigator (`raihankabirrahu@gmail.com`) for formal decision and execution.

---

## 2. The 13 Mandatory Researcher Decisions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 13 MANDATORY HUMAN RESEARCHER DECISIONS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ TECHNICAL & SECURITY POLICY                                                 │
│  1. Checkpoint Integrity Hashing Authorization (F13-09)                     │
│  2. EVAL-AUTH Token Lifecycle & Revocation (F13-10)                         │
│  3. Descriptive Back-Stream Cache Route (M-03)                              │
│  4. Process Context Token Binding (F13-15)                                  │
│  5. Crossing SM State Transition Bounds (DEC-B05)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ GROUND TRUTH & ADJUDICATION GOVERNANCE                                      │
│  6. Second-Review Protocol Adoption (RD-043)                                │
│  7. Disagreement Resolution Protocol Adoption (RD-045)                       │
│  8. Authorized Human Reviewer Appointment & Expansion                       │
│  9. Protocol & Schema Version Binding (v7.0.0 & v8.1.0-stage2.1)            │
│ 10. Stage-2.1 Promotion Gate Execution Authorization                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ HISTORICAL & PUBLICATION GOVERNANCE                                         │
│ 11. Mission 12 Execution Incident Administrative Review (F13-08)            │
│ 12. Manuscript Authorship Attribution & AI Reclassification                 │
│ 13. Future Real-Data Evaluation Authorization (EVAL-AUTH / AUTH-MEDIA-ACCESS)│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Decision 1: Model Checkpoint Integrity Hashing Authorization (F13-09)
- **Context:** Readiness preflights verify weights via SHA-256 (`best.pt`). Hashing reads checkpoint bytes.
- **Options:**
  - *Option 1A:* Maintain checkpoints as non-media system assets; allow read-only hashing during preflight.
  - *Option 1B:* Adopt detached, cryptographically signed SHA-256 sidecar hashes signed by the researcher, avoiding direct byte reads.
  - *Option 1C:* Require explicit `AUTH-CHECKPOINT-ACCESS` token before any checkpoint byte read.
- **Consequence:** Option 1B eliminates security recursion and prevents unauthenticated byte access.

---

### Decision 2: EVAL-AUTH Token Lifecycle, Expiration, and Revocation (F13-10)
- **Context:** `EVAL-AUTH` schema v1 lacks single-use nonces and automated revocation lists (CRL).
- **Options:**
  - *Option 2A:* Retain static JSON token model (v1.0.0).
  - *Option 2B:* Upgrade to `EVAL-AUTH` v2.0 requiring cryptographic nonces, single-run expiration, and HMAC/ECDSA signatures.
- **Consequence:** Option 2B prevents replay attacks and accidental token re-use.

---

### Decision 3: Descriptive Back-Stream Cache Route Architecture (M-03)
- **Context:** The descriptive benchmark evaluates front-camera and back-stream features. Must decide whether back-stream data is read from precomputed perceptual feature caches or decoded on-the-fly.
- **Options:**
  - *Option 3A:* Cache-only replay using static JSONL feature caches (zero raw media access required).
  - *Option 3B:* Dynamic on-the-fly video decoding requiring direct access to raw `.mov` video files.
- **Consequence:** Option 3A adheres strictly to the zero-media-exposure safety principle.

---

### Decision 4: Runtime Context Token Binding Across Processes (F13-15)
- **Context:** Authorization tokens are stored in process memory. If multi-processing is used for evaluation, tokens could fail to propagate or be inherited unintentionally.
- **Options:**
  - *Option 4A:* Enforce single-process, single-threaded execution for all official evaluations.
  - *Option 4B:* Implement environment-variable token passing verified by HMAC signature.
- **Consequence:** Option 4A is simple, fully deterministic, and requires no code changes.

---

### Decision 5: Crossing State Machine Hysteresis and Bounds (DEC-B05)
- **Context:** Formalization of state-machine parameters in `configs/decision_policy_v1.yaml`:
  - 2-frame optical confirmation (`RULE_1`),
  - 5-second acoustic dwell (`RULE_2`),
  - 2.0-second sensor staleness clamping (`RULE_8`),
  - 3.6-second minimum lead-in reaction threshold (`MTR`).
- **Options:**
  - *Option 5A:* Formally sign off on current parameter values as the official research benchmark configuration.
  - *Option 5B:* Revise dwell or staleness thresholds based on empirical field safety considerations.
- **Consequence:** Option 5A enables immediate benchmark readiness without configuration churn.

---

### Decision 6: Adoption of Second-Review Protocol (RD-043)
- **Context:** `src/railway_detection/annotation/second_review.py` defines 5 deterministic triggers for dual-human review.
- **Options:**
  - *Option 6A:* Formally adopt the 5 triggers (`TRIGGER_CORRECTED`, `TRIGGER_ENGINE_T3_T4`, `TRIGGER_EXPLICIT_FLAG`, `TRIGGER_MEDIA_HASH`, `TRIGGER_UNCERTAIN_BOUNDARY`).
  - *Option 6B:* Restrict second-review triggers to boundary timestamp corrections only ($>0.5\,\text{s}$).
- **Consequence:** Option 6A maximizes scientific rigor for peer-reviewed journal submission.

---

### Decision 7: Adoption of Disagreement Resolution Protocol (RD-045)
- **Context:** When two human reviewers disagree on a boundary timestamp, a formal adjudication procedure is required.
- **Options:**
  - *Option 7A:* Lead Researcher adjudication session serves as final binding ground truth.
  - *Option 7B:* Mean/median timestamp averaging with recorded uncertainty bounds $[t_{\min}, t_{\max}]$.
- **Consequence:** Option 7A provides single-point authoritative provenance; Option 7B provides formal measurement variance.

---

### Decision 8: Authorized Human Reviewer Appointment and Expansion
- **Context:** `data/ground_truth/authorized_reviewers.json` currently contains only one reviewer: `raihankabirrahu@gmail.com`.
- **Options:**
  - *Option 8A:* Maintain single authorized reviewer for Stage 2.1 (permits single-review events; second-review events blocked).
  - *Option 8B:* Appoint and add a second qualified railway researcher email to the allowlist.
- **Consequence:** Option 8B is required to satisfy RD-043 second-review triggers.

---

### Decision 9: Protocol and Schema Version Binding
- **Context:** Multiple document versions exist in the repository (`FINAL_GROUND_TRUTH_PROTOCOL.md` v7.0.0, Stage-2.1 schema v8.1.0-stage2.1).
- **Options:**
  - *Option 9A:* Formally lock Protocol v7.0.0 and Schema v8.1.0-stage2.1 as immutable specifications for the official benchmark.
  - *Option 9B:* Re-version both documents to 8.0.0 for semantic alignment.
- **Consequence:** Option 9A requires zero document edits and avoids checksum churn.

---

### Decision 10: Stage-2.1 Promotion Gate Execution Authorization
- **Context:** Once human adjudication is completed, `promotion_gate.py` must be executed to write official promotion receipts in `data/ground_truth/promoted/`.
- **Options:**
  - *Option 10A:* Authorize automated promotion gate execution upon completion of valid human adjudication sessions.
  - *Option 10B:* Require separate, individual promotion approvals per event batch.
- **Consequence:** Option 10A streamlines pipeline progression once reviews are verified.

---

### Decision 11: Mission 12 Incident Administrative Review (F13-08)
- **Context:** Mission 12 executed protected Phase 12 tests (`EXECUTION_CONFIRMED_ACCESS_NOT_ESTABLISHED`).
- **Options:**
  - *Option 11A:* Sign formal administrative review memo closing the incident without penalty, noting that the code boundary has since been completely isolated and verified.
  - *Option 11B:* Request deeper operating-system-level audit logging if available.
- **Consequence:** Option 11A formally closes Finding F13-08 and unblocks governance progression.

---

### Decision 12: Manuscript Authorship and AI Reclassification
- **Context:** `docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md` currently lists `Antigravity Autonomous Research Engineering Agent` as co-author.
- **Options:**
  - *Option 12A:* Remove AI agent from author line; list human Principal Investigator(s) as sole authors; add AI disclosure to Acknowledgments per IEEE/COPE standards.
  - *Option 12B:* Retain current text until journal submission.
- **Consequence:** Option 12A brings manuscript into immediate academic compliance.

---

### Decision 13: Future Real-Data Evaluation Authorization (EVAL-AUTH)
- **Context:** Official Phase 5 real-data evaluation remains strictly unauthorized.
- **Options:**
  - *Option 13A:* Issue formal `EVAL-AUTH.json` and `AUTH-MEDIA-ACCESS.json` tokens ONLY AFTER Decisions 1–12 and all 27 human adjudication sessions are completed.
  - *Option 13B:* Issue descriptive-only evaluation authorization for static feature caches.
- **Consequence:** Option 13A guarantees complete scientific validity and prevents premature data exposure.

---

## 3. Recommended Action Plan for Human Researcher

```
STEP 1: Execute Decisions 8, 9, and 11 (Appoint Reviewer, Lock Protocols, Close M12 Incident).
STEP 2: Execute Human Adjudication Sessions for 27 Events using adjudication_session.py.
STEP 3: Execute Decision 10 (Run promotion_gate.py to generate Stage-2.1 Ground Truth).
STEP 4: Execute Decisions 1, 2, and 5 (Finalize Checkpoint Hashing and Policy Configs).
STEP 5: Execute Decision 13 (Issue EVAL-AUTH for Official Descriptive Benchmark Replay).
STEP 6: Execute Decision 12 (Populate Tables 1-3, Finalize Authorship, Submit Paper).
```
