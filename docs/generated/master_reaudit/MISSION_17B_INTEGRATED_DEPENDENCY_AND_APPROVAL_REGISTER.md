# MISSION 17B: INTEGRATED DEPENDENCY, SECURITY RISK & APPROVAL REGISTER

**Project:** Train Gate Automation — Bangladesh
**Subsystem:** Project Governance, Technical Roadmapping & Security Architecture
**Document ID:** `MISSION-17B-DELIV-04`
**Execution Authority:** NONE (All Roadmap Actions and PI Decisions Marked PROPOSED / PENDING) **17C-0: corrected requirements are in the appended correction history; original body retained.**
**Governance Invariants:** RD-001 through RD-055
**Audited Sources:** [`MISSION_17A_PI_DECISION_RECONCILIATION.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/MISSION_17A_PI_DECISION_RECONCILIATION.md), [`MISSION_17A_PI_APPROVAL_REGISTER.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/MISSION_17A_PI_APPROVAL_REGISTER.md), [`MISSION_17_PI_DECISION_BRIEFING.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/MISSION_17_PI_DECISION_BRIEFING.md), [`MISSION_17_MASTER_ACTION_AND_DEPENDENCY_REGISTER.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/MISSION_17_MASTER_ACTION_AND_DEPENDENCY_REGISTER.md), Missions 16E, 16F, 16G, 16H
**Date:** 2026-11-03

---

## 1. Executive Summary & Governance Scope

This register provides the overarching integration framework connecting the technical design specifications produced in Mission 17B (Human Review CLI, Convention B Simulation, Event-Grouped CV Partitioning) with project governance, security threat modeling, and Principal Investigator (PI) decision authorities.

> [!IMPORTANT]
> **Strict Governance Mandate:** In accordance with Mission 17B constraints, no pending PI decision is represented as approved. All recommendations are explicitly marked as `PROPOSED` or `PENDING_PI_APPROVAL`. Zero real-data execution is authorized by this document.

---

## 2. Camera Scope & PI Decision Reconciliation (Phase E)

A central finding of Missions 16E, 16F, and 17A is the direct tension between historical researcher directions establishing camera roles and the proposed single-camera V1.0 benchmark:

### 2.1 Preserved Historical Mandates
1. **RD-015 (Back-Stream Primary for M4/M5):** The rear-facing camera stream is established as primary for gate clearance landmarks ($T_4$) and metrics M4/M5; the front-facing stream is primary for train approach ($T_0, T_1$); fused stream is exploratory only.
2. **RD-028 (Independent-Camera Analysis Primary):** Front-camera and back-camera pipelines must be evaluated independently first; multi-camera sensor fusion is strictly secondary and exploratory.
3. **RD-026 (R04 Dual-Camera Scope Frozen at 11 Events):** Dual-camera synchronization is physically verified on exactly 11 events; `event_010` is permanently excluded due to timestamp misalignment.
4. **RD-027 (Acoustic Invariance):** Acoustic onset times ($T_{\text{horn}}$) must never shift physical video clock ground-truth timestamps.
5. **RD-035 (B0–B2 Back-Stream Conditions):** Back-camera baseline evaluation requires separate feature extraction; no execution is authorized.
6. **RD-039 (Descriptive Full-Cohort Scope):** Full 27-event descriptive analysis is authorized in principle, subject to rigorous governance approval and execution tokens.

### 2.2 The V1.0 Camera Conflict
The proposed V1.0 benchmark relies exclusively on front-camera footage because back-camera footage has unresolved exposure, lighting, and sync gaps across the full 27 events. However, because the front camera faces the approaching train, it cannot observe the train tail clearing the crossing roadway ($T_4$). Consequently:
- In a front-camera-only V1.0 benchmark, Metrics **M4** (Total Gate Closed Duration) and **M5** (Clearance Safety Buffer) **cannot be computed directly from video ground truth**.
- **Reconciliation Status:** Option C (Phased Scope) has been recommended to the PI:
  - **Phase V1.0:** Front-camera descriptive benchmark focused on Train Arrival ($T_0, T_1, T_2$), Warning Time (M1), and Gate Reaction (M2/M3).
  - **Phase V2.0:** Dual-camera multi-sensor benchmark covering clearance ($T_4$) and safety buffer (M4/M5) on the verified 11-event cohort.
- **Statutory Authority:** This recommendation remains **PENDING EXPLICIT PI AMENDMENT** to RD-015.

---

## 3. Comprehensive Master PI Decision Reconciliation Matrix

The following ledger reconciles all ten primary decisions (D-01 through D-10) and additional researcher decisions (AD-01 through AD-10), detailing authority, status, and required approvals:

| ID | Decision Topic | Existing Authority | Mission 17A Recommendation | Current Status in 17B | Required Approval Authority |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **D-01** | Ground Truth Protocol Authority | Protocol v7.0.0 active; v7.1.0 proposed. | Promote `v7.1.1-PROPOSED` as definitive authority (`FINAL_GROUND_TRUTH_PROTOCOL.md`). | `PROPOSED_PENDING_PI` | PI (`raihankabirrahu@gmail.com`) sign-off. |
| **D-02** | Human Review CLI Architecture | `adjudication_session.py` (synthetic only). | Implement `src/railway_detection/annotation/human_review_session.py` per Deliverable 1. | `SPECIFIED_IMPL_PENDING` | PI approval of Deliverable 1 spec. |
| **D-03** | Security Token & Hash Binding | `media_guard.py` (unsigned JSON token). | Adopt four-tier scoped tokens, atomic nonce locking, and working-tree code hashing. | `PROPOSED_PENDING_PI` | PI authorization of token contract. |
| **D-04** | Execution Roadmap Structure | Strict waterfall sequencing proposed in 16E. | Adopt 4-Track decoupled parallel execution model (Section 4). | `PROPOSED_PENDING_PI` | PI endorsement of decoupled tracks. |
| **D-05** | Review Calibration & Tolerances | Uncalibrated heuristic tolerances. | Conduct 5-event calibration pilot before setting final tolerances ($\tau_k$). | `PROPOSED_PENDING_PI` | PI + Lead Rater sign-off on pilot protocol. |
| **D-06** | Camera Scope & Metric Alignment | RD-015 (back camera mandatory for M4/M5). | Adopt Option C: Phased Scope (V1.0 front-cam arrival, V2.0 dual-cam clearance). | `CRITICAL_CONFLICT_PENDING` | Formal PI Governance Amendment Memo for RD-015. |
| **D-07** | CV Dataset Split Restructuring | Split `705d388743ea` (`leakage_risk: true`). | Adopt 5-fold Stratified GroupKFold grouped strictly by `event_id` per Deliverable 3. | `SPECIFIED_IMPL_PENDING` | PI + ML Lead approval of Deliverable 3 spec. |
| **D-08** | Manuscript Scope & Reframing | Legacy draft with causal overclaims. | Reframe paper as "Descriptive Benchmark at Level Crossing in Bangladesh" per RD-051–055. | `PROPOSED_PENDING_PI` | PI + Co-Authors approval of paper outline. |
| **D-09** | Historical Table 11 Reporting | Convention A historical results in archives. | Dual-column reporting: Historical ($T_{\text{Table 11}}$) vs Forward-Causal ($T_{\text{causal}}$) per Deliv 2. | `PROVEN_READY_TO_REPORT` | PI approval of dual-column manuscript format. |
| **D-10** | Metric MTR Reporting Standard | Ambiguous MTR metric interpretation. | Reclassify MTR as "Lead-In Feasibility Screen" with explicit censoring qualifiers. | `PROPOSED_PENDING_PI` | PI + Lead Methodologist endorsement. |
| **AD-01** | Engine-Only Pass Treatment | RD-024: Excluded from pooled metrics. | Maintain RD-024; report `event_021` strictly as out-of-distribution case study. | `PRESERVED_ACTIVE` | Pre-approved by PI in RD-024. |
| **AD-02** | No-Train False Alarm Reporting | RD-025: Dedicated false alarm analysis. | Evaluate `event_003`, `009`, `016` for FAR per hour; zero mixed precision curves. | `PRESERVED_ACTIVE` | Pre-approved by PI in RD-025. |
| **AD-03** | R04 Dual-Camera Scope Freeze | RD-026: Scope locked to 11 events. | Enforce 11-event lock; permanent exclusion of `event_010`. | `PRESERVED_ACTIVE` | Pre-approved by PI in RD-026. |
| **AD-04** | Acoustic Ground-Truth Invariance| RD-027: Acoustic offsets cannot shift GT. | Audio cross-correlation used strictly for sensor latency, never video GT clock. | `PRESERVED_ACTIVE` | Pre-approved by PI in RD-027. |
| **AD-05** | Controller Heuristics Lockdown | RD-031: 2-tick confirm, 2-tick drop locked. | Preserve baseline controller heuristics; zero parameter tuning on test events. | `PRESERVED_ACTIVE` | Pre-approved by PI in RD-031. |
| **AD-06** | Prohibition on New Field Data | RD-037: Scope restricted to 27 events. | Lock dataset to existing 27 events; no new field collection for Version 1.0. | `PRESERVED_ACTIVE` | Pre-approved by PI in RD-037. |
| **AD-07** | Historical Event Inventory | RD-041: 27 events certified. | Maintain official registry (23 full passes, 3 controls, 1 engine pass). | `PRESERVED_ACTIVE` | Pre-approved by PI in RD-041. |
| **AD-08** | Annotation Landmark Priority | RD-048: Visual track lines prioritized. | Raters prioritize visual line crossing over audio horn onset. | `PRESERVED_ACTIVE` | Pre-approved by PI in RD-048. |
| **AD-09** | Human Authorship & AI Disclosure | RD-054: COPE-compliant AI disclosure. | AI co-authorship barred; formal transparency statement included in manuscript. | `PRESERVED_ACTIVE` | Pre-approved by PI in RD-054. |
| **AD-10** | Disagreement Adjudication Rule | RD-045: Unresolved discrepancy UNCERTAIN. | Bar automated averaging; mark disputed landmarks `UNCERTAIN`. | `PRESERVED_ACTIVE` | Pre-approved by PI in RD-045. |

---

## 4. Integrated Dependency Architecture & Parallel Execution Tracks

Rather than imposing a rigid linear waterfall where software engineering is blocked on human review, future implementation is partitioned into **four decoupled, parallelizable tracks**:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│              TRACK A: RESEARCH GOVERNANCE & PROTOCOL PROMOTION (PI)              │
│  - Review D-01..D-10       - Sign Protocol v7.1.1       - Issue Reviewer Permits │
└───────────────────────┬──────────────────────────────────┬───────────────────────┘
                        │                                  │
      ┌─────────────────┴─────────────────┐                │
      ▼                                   ▼                ▼
┌───────────────────────────┐ ┌──────────────────────────┐ ┌───────────────────────┐
│ TRACK B: SOFTWARE & SIM   │ │ TRACK C: CV & SENSOR     │ │ TRACK D: HUMAN REVIEW │
│ - Convention B Runner     │ │ - GroupedSplitter Script │ │ - Implement CLI       │
│ - 14-Case Synthetic Suite │ │ - 5-Fold Stratified Split│ │ - 5-Event Pilot       │
│ - Table 11 Dual Reporting │ │ - Synthetic Leakage Test │ │ - 27-Event Dual Review│
└─────────────┬─────────────┘ └────────────┬─────────────┘ └───────────┬───────────┘
              │                            │                           │
              └─────────────────────┐      │      ┌────────────────────┘
                                    ▼      ▼      ▼
                        ┌──────────────────────────────────────────┐
                        │ TRACK E: CONTROLLED EVALUATION & PAPER   │
                        │ - Verified Ground Truth Promotion        │
                        │ - End-to-End Benchmark Evaluation       │
                        │ - Manuscript Revision (Descriptive Bench)│
                        └──────────────────────────────────────────┘
```

### 4.1 Track A: Research Governance & Administrative Sign-Off
- **Scope:** Human researcher decisions, formal protocol promotion, allowlist expansion.
- **Key Inputs:** Mission 17A decision package, Mission 17B technical specifications.
- **Key Deliverables:** Signed PI Decision Memo, promoted `FINAL_GROUND_TRUTH_PROTOCOL.md`, issued `AUTH-MEDIA-ACCESS (PILOT)` token.
- **Responsible Role:** Principal Investigator (`raihankabirrahu@gmail.com`).
- **Dependencies:** None (unblocked).

### 4.2 Track B: Software Engineering & Simulation Remediation
- **Scope:** Synthetic-only implementation of forward-causal Convention B runner.
- **Key Inputs:** Deliverable 2 (`MISSION_17B_CONVENTION_B_SIMULATION_DESIGN.md`).
- **Key Deliverables:** Refactored simulation module (`src/railway_detection/simulation/causal_runner.py`), passing 14-case synthetic test suite.
- **Responsible Role:** Software Systems Engineer.
- **Dependencies:** Zero real-data dependencies; zero human-review dependencies. Fully unblocked for synthetic execution.

### 4.3 Track C: Computer Vision Partitioning & Sensor Hardening
- **Scope:** Synthetic-only implementation of event-grouped stratified cross-validation splitter.
- **Key Inputs:** Deliverable 3 (`MISSION_17B_GROUPED_CV_SPLIT_DESIGN.md`).
- **Key Deliverables:** Partitioning script (`src/railway_detection/data/grouped_split.py`), partition manifest `cv-event-grouped-split/1.0`, passing synthetic leakage suite.
- **Responsible Role:** Machine Learning Engineer.
- **Dependencies:** Event metadata manifests. Zero raw media access required. Fully unblocked for synthetic execution.

### 4.4 Track D: Human Review & Ground Truth Acquisition
- **Scope:** Implementation of `human_review_session.py`, calibration pilot, 2-rater review of 27 events, PI adjudication.
- **Key Inputs:** Deliverable 1 (`MISSION_17B_HUMAN_REVIEW_CLI_TECHNICAL_SPEC.md`), Track A approval and tokens.
- **Key Deliverables:** Session review ledgers (`data/ground_truth/reviews/`), adjudication reports, candidate canonical ground truth.
- **Responsible Role:** Human Raters ($R_1, R_2$) + PI Adjudicator.
- **Dependencies:** Requires PI token issuance (`AUTH-MEDIA-ACCESS (REVIEW)`). Blocked until Track A approval.

### 4.5 Track E: Controlled Scientific Evaluation & Manuscript Revision
- **Scope:** Ground-truth promotion gate, end-to-end benchmark evaluation, dual-column simulation reporting, final manuscript text.
- **Key Inputs:** Outputs of Tracks B, C, and D; `AUTH-PROMOTION` token.
- **Key Deliverables:** Final benchmark tables, published dataset split, revised manuscript draft.
- **Responsible Role:** Lead Methodologist + PI.
- **Dependencies:** Strictly blocked until Tracks A, B, C, and D are complete.

---

## 5. Security Threat Model & Failure-Closed Mitigations

The project's security architecture addresses the following critical threat vectors:

| Threat ID | Threat Vector | Mechanism / Vulnerability | Severity | Mandatory Mitigation |
| :---: | :--- | :--- | :---: | :--- |
| **SEC-01** | Unauthorized Media Access | Rogue process opens raw video under `data/raw/` without token. | CRITICAL | `media_guard.py` enforces fail-closed path canonicalization at OS-open boundary. |
| **SEC-02** | Token Replay Attack | Re-using a previously approved `AUTH-MEDIA-ACCESS.json` across sessions. | HIGH | Atomic nonce consumption locked via `fcntl.flock` into `.consumed_nonces.jsonl`. |
| **SEC-03** | Token Scope Escalation | Review token (`AUTH-MEDIA-ACCESS`) used to load PyTorch checkpoints. | HIGH | Strict tier partitioning; model checkers reject review-tier tokens. |
| **SEC-04** | Post-Auth Code Mutation (TOCTOU) | Malicious modification of python code after initial git status preflight. | HIGH | Runtime module hashing: CLI validates SHA-256 of loaded safety libraries on each step. |
| **SEC-05** | Reviewer Impersonation | Forging rater handle to bypass two-rater independent review requirement. | HIGH | Rater handle validated against `authorized_reviewers.json`; all records hash-chained. |
| **SEC-06** | Ground-Truth Tampering | Modifying existing review JSONL files to force consensus. | CRITICAL | Hash-chained ledgers; `promotion_gate.py` recalculates cryptographic digest from source. |
| **SEC-07** | Automated Promotion Bypass | Script promoting unadjudicated review records into canonical GT. | CRITICAL | `promotion_gate.py` requires cryptographic `AUTH-PROMOTION` token signed by PI. |
| **SEC-08** | CV Dataset Leakage | Frames from same event appearing in both train and validation sets. | HIGH | Strict `event_id` grouping; `allow_ungrouped_fallback: false` enforced fail-closed. |
| **SEC-09** | Simulation Look-Ahead | Gate actuator stepped retroactively using newly computed decision. | MEDIUM | Convention B enforces forward-causal stepping: $[t_{k-1}, t_k]$ stepped with $u_{k-1}$. |
| **SEC-10** | Accidental Real-Data Execution | Running real-data pipelines during synthetic-only research phases. | CRITICAL | Synthetic tripwires in test fixtures (`_require_synthetic_id`, `_require_temp_path`). |

---

## 6. Formal Project Acceptance Gates

To ensure research integrity, progression through the roadmap is governed by three non-bypassable gates:

```
[Track B & C Complete] ──> ┌────────────────────────────────────────┐
                           │ GATE 1: TOOLING & SIMULATION PASS      │
[Track A Approval]     ──> └───────────────────┬────────────────────┘
                                               │
                                               ▼
[Track D Complete]     ──> ┌────────────────────────────────────────┐
                           │ GATE 2: GROUND TRUTH INTEGRITY PASS    │
[Zero Disagreements]   ──> └───────────────────┬────────────────────┘
                                               │
                                               ▼
[Track E Complete]     ──> ┌────────────────────────────────────────┐
                           │ GATE 3: PUBLICATION READINESS PASS     │
[PI Co-Author Signoff] ──> └────────────────────────────────────────┘
```

1. **Gate 1 (Tooling & Simulation Acceptance):**
   - Convention B passes all 14 synthetic tests.
   - Event-Grouped CV splitter passes all 8 synthetic leakage tests.
   - Human Review CLI passes all 10 synthetic session tests.
   - Working tree remains clean; no production regression.

2. **Gate 2 (Ground-Truth Integrity Acceptance):**
   - 100% of 27 events reviewed by two independent authorized raters.
   - All direction, landmark, and occlusion disagreements adjudicated by PI.
   - Zero unresolved disputes; all edge cases resolved or marked `UNCERTAIN`.
   - `promotion_gate.py` verifies hash integrity and promotes canonical ground truth.

3. **Gate 3 (Publication & Evaluation Acceptance):**
   - End-to-end evaluation executed under `AUTH-EVALUATION` token.
   - Simulation results presented with dual-column Convention A / Convention B format.
   - YOLO metrics reported with 5-fold cross-validation out-of-fold generalization.
   - Manuscript reframed as descriptive field benchmark; COPE AI disclosure signed.

---

## 7. Next Recommendations for Researcher Review

Upon conclusion of Mission 17B, the following actions are recommended to the Principal Investigator:
1. **Review and Adopt Deliverables 1 through 4:** Endorse the technical architectures for the Human Review CLI, Convention B simulation, and Event-Grouped CV splitting.
2. **Issue PI Governance Memo on Decision D-06 (Camera Scope):** Formally endorse Option C (Phased Scope) to resolve the RD-015 conflict for Version 1.0.
3. **Authorize Track B & Track C Synthetic Implementation:** Permit the software engineering team to implement `causal_runner.py` and `grouped_split.py` under synthetic-only testing without issuing media access tokens.

---
*End of Mission 17B Deliverable 4.*

---

## Mission 17C-0 correction history — superseding dependency and approval status

**2026-11-03; documentation correction only.** Original §§1–7 remain visible as historical specification wording. This appendix and the 17C-0 PI register supersede conflicting labels, mandates, gates, examples and recommendations. No protocol, reviewer, token or implementation is approved here.

### Correct scope and decision status

1. The diagram lists **five tracks A–E**. Synthetic engineering in B/C and some CLI work can be technically independent of real-media review, but “fully unblocked” is only technical feasibility. D-01–D-10 remain **PENDING** formal researcher action. Track implementation must not start from this register; 17C-0 explicitly stops before 17C-B/C or other implementation.
2. Existing directions and code behavior are not “pre-approved” execution artifacts. AD rows must be read as recorded directions with formal adoption/ratification pending where required. D-09's “PROVEN_READY_TO_REPORT” is withdrawn as approval/readiness: its mathematical result is conditional and reporting remains a PI decision.
3. M4 means premature opening, M5 means never protected (counts only). They require approved observable T4 on the replay clock and appropriate retained replay evidence, not a duration/safety-buffer substitution. MTR is an outcome metric with a separate eligibility screen. The front-only M1–M3/T2 expansion is not adopted; RD-020 scope and RD-006 deferral remain.
4. Preserve independent-camera primary analysis: front-stream approach outcomes and back-stream M4/M5. Back-local replay plus back-local T4 does not require inter-camera R04 synchronization. A current software/cache pathway gap is a missing implementation, not proof that the research must become front-only. The existing cache-only engine supports front B0/B1/B2 in evaluation/cache_only_engine.py; the 17A simulation/ path is wrong. No protected cache existence/completeness or bytes were verified here.
5. Option C front-only V1/dual-camera V2 remains a proposal requiring explicit researcher amendment of affected RD014/015/020/022/028/035/052 directions. Independent-back analysis remains a competing option. The11-event R04 scope is exploratory; no new formal physical-sync certification exists, and event_010 is not permanently barred from a future authorized amendment. No silent scope expansion or shifting of human GT clocks is permitted.
6. Cohort identities: engine_events/event_001 and no_train_events/event_001..003, not engine event_021 or controls003/009/016 from the train cohort. 27=23+3+1 is inventory metadata, with formal sign-off pending. RD024 pooled exclusion does not dictate model-training eligibility. No-train policy is event-level counts, blockage/episodes and per-stream exposure; FAR/hour is not adopted.
7. The V1 still-image development corpus must not be replaced by the 27-event evaluation cohort. D-07 requires verified development physical-event lineage and label/stratum feasibility before choosing K or generating any actual split. Future out-of-fold performance requires disjoint tuning/evaluation and model exposure controls. No real split is generated here.

### Correct security and human-review dependencies

- SEC01's “OS-open boundary” guarantee is false: media_guard.py is a Python operation-boundary guard, explicitly not an OS sandbox. SEC02 nonce locking, SEC03 token tiers, SEC04 runtime hashing, SEC05 identity authentication and SEC06/07 ledger/signature verification are proposed requirements or incomplete mitigations, not existing verified enforcement. The current promoter does not verify PI cryptographic tokens/JSONL chains. Consult corrected CLI appendix for threat limitations and required durable state.
- Model/checkpoint, raw read/probe/hash, protected-cache read/replay, human review, promotion, real evaluation and split-generation privileges must be separately mapped; review cannot authorize promotion/evaluation, and promotion cannot authorize evaluation. Existing EVAL-AUTH and media records are unsigned recorded statements, not cryptographic credentials. A future incompatible token needs a versioned approved contract. Expiry/revocation require checks at use, and host trust limitations must remain explicit.
- Reviewer handle allowlisting is not authentication or qualification. One identity currently exists. RD043 is risk-based mandatory second review; a universal27-event two-rater policy is not established. Adopted triggers, reviewer appointment and schema/adjudication interoperability remain prerequisites. Do not weaken the synthetic harness to create a real-review path.
- Five-event pilot, tolerance ranges and session caps are proposals. The active 30 s floor is a software plausibility check, not scientific review-duration approval. RD045 requires immutable original observations, separate adjudication and unresolved UNCERTAIN. “Zero disagreements” cannot require inventing consensus or excluding inconvenient cases without metric-specific reasons.
- Gate 1 cannot treat the 14/8/10 test plans as already executed or sufficient evidence of complete security. They require corrected oracles, additional negative/concurrency cases and actual synthetic-only implementation results in a later authorized mission.
- Human review needs scoped media authorization before its own promotion receipt exists. Promotion later needs applicable promotion authority plus raw hash permission and a vetted ledger/schema adapter. Evaluation later needs its own canonical authorization, promoted evidence and code/config/protocol/split/condition bindings; an AUTH-PROMOTION alone is insufficient. Technical gate completion does not issue any capability.
- Publication readiness is pending researcher-owned RQs/claims, correct human author roster, accurate AI disclosure, venue selection and actual authorized results. The current manuscript still names an agent; venue is undecided; no publication dates are evidenced. Future code/approved-annotation release requires privacy/license review and excludes raw media. No raw-media anonymization/release policy or venue is adopted here.

### Correct acceptance disposition

Read the four 17C-0 audit documents and corrected companion specifications before any approval. All material production changes, scientific tolerances, protocol promotion, camera amendment, reviewer appointment, actual split generation and real-data operations remain pending. The only completed actions in 17C-0 are safe independent checks and authorized documentation corrections, followed by the requested documentation-only commit/push workflow. **STOP for researcher review.**
