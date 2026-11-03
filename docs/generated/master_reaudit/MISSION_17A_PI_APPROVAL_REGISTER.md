# MISSION 17A: MASTER PI APPROVAL AND DECISION REGISTER

**Project:** Train Gate Automation — Bangladesh  
**Document ID:** `docs/generated/master_reaudit/MISSION_17A_PI_APPROVAL_REGISTER.md`  
**Mission ID:** `17A-PI-DECISION-RECONCILIATION`  
**Document Role:** Exhaustive Governance Traceability, Evidence Mapping, and Action Ledger  
**Auditor:** Independent Principal Research, Systems, and Governance Auditor  
**To:** Principal Investigator, Raihan Kabir Rahu (`raihankabirrahu@gmail.com`)  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Baseline Git HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Companion Briefing:** [`docs/generated/master_reaudit/MISSION_17A_PI_DECISION_RECONCILIATION.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/MISSION_17A_PI_DECISION_RECONCILIATION.md)  
**Execution Authority:** NONE — READ-ONLY INDEPENDENT REGISTER  
**Date:** 2026-11-03  

---

## 1. Master Decision Tracking Ledger (D-01 through D-10)

This ledger details the ten primary decisions, their underlying evidence, authorities, and multi-tier dependencies:

| ID | Decision Title | Status | Approval Authority | Relevant RD References | Primary Evidence Paths | Technical Dependencies | Human-Review Dependencies | Governance Dependencies | Outstanding Questions for PI |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **D-01** | Ground Truth Protocol Authority | `DECISION_READY_FOR_PI` | PI (`raihankabirrahu@gmail.com`) | RD-001, RD-002, RD-004, RD-005, RD-006, RD-008, RD-049 | [`docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md), `v7.0.0` | UTF-8 diff validation; SHA-256 computation | None | PI sign-off; Administrative git commit | Does PI endorse promoting v7.1.1-PROPOSED over v7.1.0-PROPOSED? |
| **D-02** | Human Review CLI Architecture | `SPEC_READY_IMPL_PENDING` | PI (approval) + Agent (code) | RD-042, RD-043, RD-045, RD-046, RD-047 | [`src/railway_detection/annotation/adjudication_session.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/adjudication_session.py#L126), `review_session.py` | CLI software build; non-destructive JSON writer | Human CLI interaction; review session tests | Reviewer identity allowlist expansion | Does PI approve Option D2 implementing `human_review_session.py`? |
| **D-03** | Security Token & Hash Binding | `DESIGN_READY_FOR_PI` | PI + Maintainer | RD-003, RD-009, RD-039, RD-050 | [`src/railway_detection/safety/media_guard.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/safety/media_guard.py#L333), `governance.py` | `git status --porcelain` check; composite hash builder | None | Administrative commit cleaning 25 modified files | Does PI authorize composite token binding and `PROMOTION` permit scope? |
| **D-04** | Execution Roadmap Structure | `DECISION_READY_FOR_PI` | PI (`raihankabirrahu@gmail.com`) | RD-001 through RD-055 | [`MISSION_17_PI_DECISION_BRIEFING.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/MISSION_17_PI_DECISION_BRIEFING.md), Section 8 Roadmap | Decoupled 4-track execution harness | None | Gate 1, Gate 2, Gate 3 stage authorizations | Does PI approve the decoupled 4-track plan over the linear waterfall? |
| **D-05** | Review Calibration & Tolerances | `PILOT_PROTOCOL_PENDING` | PI + Authorized Reviewers | RD-010, RD-012, RD-013, RD-043, RD-044, RD-047 | `tests/test_mission10_second_review.py`, Mission 16E/16F | Absolute timestamp conversion (`frame / fps`) | Blind first-pass dual review on 5 events | Reviewer permit `AUTH-MEDIA-ACCESS (PILOT)` | Does PI approve Option T3 landmark-specific pilot tolerances? |
| **D-06** | Camera Scope & Metric Alignment | `CRITICAL_CONFLICT_PENDING` | PI (`raihankabirrahu@gmail.com`) | RD-014, RD-015, RD-020, RD-022, RD-026, RD-028, RD-035 | [`src/railway_detection/simulation/cache_only_engine.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/cache_only_engine.py#L77), Mission 16F | Front-stream cache validation; B0–B2 feature replay | None (for V1.0 front stream) | Formal PI Governance Amendment Memo for RD-015 | Does PI adopt Option C (Phased Scope: V1.0 front-cam, V2.0 dual-cam)? |
| **D-07** | CV Dataset Split Restructuring | `DESIGN_READY_IMPL_PENDING` | PI + Machine Learning Lead | RD-006, RD-032, RD-033, RD-037 | [`data/splits/705d388743ea/split_summary.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/705d388743ea/split_summary.json), `manifest.py` | Stratified GroupKFold partitioning script | None | Dataset split hash binding in `governance.py` | Does PI approve 5-fold stratified cross-validation on event IDs? |
| **D-08** | Manuscript Scope & Reframing | `DECISION_READY_FOR_PI` | PI + Co-Authors | RD-051, RD-052, RD-053, RD-054, RD-055 | [`docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md), Mission 13 | Manuscript draft revision; figure updates | None | Author list approval; COPE AI disclosure endorsement | Does PI approve reframing draft to Descriptive Field Benchmark? |
| **D-09** | Table 11 Presentation Standard | `PROVEN_READY_TO_REPORT` | PI + Lead Author | RD-019, RD-036 | Missions 16D, 16G, 16H, B4 timeline CSVs | Analytical offset formula $\Delta T = -0.2000\,\text{s}$ | None | None | Does PI approve dual-column reporting of Historical vs Causal values? |
| **D-10** | MTR Reporting Standard | `DECISION_READY_FOR_PI` | PI + Safety Methodologist | RD-011, RD-020, RD-021, RD-022, RD-040 | `lead_in.py`, `evaluate_run.py`, Proposal metadata | Censored reason aggregation in `metrics.py` | None | None | Does PI approve reclassifying MTR as Lead-In Feasibility Screen? |

---

## 2. Additional Researcher Decisions Ledger (AD-01 through AD-10)

This ledger tracks the ten critical researcher directional decisions omitted from Mission 17's primary briefing:

| ID | Origin RD | Decision Topic | Status | Authority | Primary Evidence Path | Operational Consequence |
| :---: | :---: | :--- | :---: | :---: | :--- | :--- |
| **AD-01** | **RD-024** | Engine-Only Pass Treatment | `IMPLEMENTED` | PI | [`tests/unit/test_phase11_cohort_qualified_identity.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_phase11_cohort_qualified_identity.py) | `event_021` (engine only) excluded from pooled metrics; published as case study. |
| **AD-02** | **RD-025** | No-Train False Alarm Reporting | `DIRECTION_RECORDED` | PI | `docs/FINAL_EXPERIMENT_DATA_FLOW.md` | False alarms reported per exposure hour; no claim of permanent "train-free" state. |
| **AD-03** | **RD-026** | R04 Dual-Camera Scope Freeze | `DIRECTION_RECORDED` | PI | `data/manifests/exploratory_dual_camera_v1.1.0_manifest.json` | Scope locked to 11 verified events; `event_010` permanently barred from dual scope. |
| **AD-04** | **RD-027** | Acoustic Timestamps & GT Invariance | `IMPLEMENTED` | PI | `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` | Acoustic cross-correlation offsets cannot alter physical video clock ground truth. |
| **AD-05** | **RD-031** | Controller Heuristics Lockdown | `DIRECTION_RECORDED` | PI | [`configs/decision_policy_v1.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/configs/decision_policy_v1.yaml) | Controller locked to 2-tick confirm, 2-tick drop, zero EMA smoothing. |
| **AD-06** | **RD-037** | Prohibition on New Field Data | `DIRECTION_RECORDED` | PI | `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` | Version 1.0 restricted to 27 existing events; no new video collection permitted. |
| **AD-07** | **RD-041** | Historical Event Inventory Sign-off| `VERIFIED` | PI | `data/manifests/train_events_manifest.json` | 27 events formally certified (23 train passes, 3 negative events, 1 engine pass). |
| **AD-08** | **RD-048** | Annotation Landmark Priority | `DIRECTION_RECORDED` | PI | `docs/PHASE11_11_ADJUDICATION_PROTOCOL.md` | Raters prioritize visual track lines ($T_1, T_3, T_4$) over acoustic horn ($T_{\text{horn}}$). |
| **AD-09** | **RD-054** | Human Authorship & AI Disclosure | `DRAFTED` | PI | [`docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md) | AI co-authorship removed; formal COPE-compliant AI tool disclosure inserted. |
| **AD-10** | **RD-055** | Data Governance & Public Release | `DIRECTION_RECORDED` | PI | `docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md` §6 | Data release controlled; pedestrian face blurring; venue targeted to IEEE ITS. |

---

## 3. Detailed Evidence and Path Traceability Matrix

Every decision is linked to exact repository artifacts, line numbers, and cryptographic digests:

| Decision ID | Target Module / Document | Exact Repository Path | Line References | Cryptographic / Forensic Digest |
| :---: | :--- | :--- | :--- | :--- |
| **D-01** | Proposed Protocol v7.1.1 | `docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md` | Lines 1–877 | `d21a84fa5129c82d6d4202f34d539a4f3f24da4151df09912d53f0996e5cde22` (v7.1.0 base) |
| **D-01** | In-place Protocol v7.0.0 | `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` | Lines 1–847 | `d100c1e6a63280c375f94e297416efb0cf7dd3c15c9aa8df076ede052d49ecf4` |
| **D-02** | Synthetic Tripwires | `src/railway_detection/annotation/adjudication_session.py` | Lines 126–142 | Verified `_require_synthetic_id()` & `_require_temp_path()` |
| **D-02** | Stage-2.1 Schema | `src/railway_detection/annotation/stage2_1_schema.py` | Lines 45–95 | `MIN_PLAUSIBLE_REVIEW_DURATION_S = 30.0` |
| **D-03** | Media Access Guard | `src/railway_detection/safety/media_guard.py` | Lines 333–377 | `verify_authorization_record()` reading `AUTH-MEDIA-ACCESS.json` |
| **D-03** | Promotion Gate Hash | `src/railway_detection/annotation/promotion_gate.py` | Line 219 | Live raw media call `compute_media_sha256_pair()` |
| **D-03** | Working-Tree State | Git working tree | Tracked modified | Exactly 25 modified tracked files in working tree |
| **D-05** | Second Review Triggers | `src/railway_detection/annotation/second_review.py` | Lines 40–85 | `check_second_review_triggers()` |
| **D-06** | Cache-Only Engine | `src/railway_detection/simulation/cache_only_engine.py` | Lines 75–88 | Enforces `front` only; raises `BackStreamReplayNotSupported` |
| **D-07** | Split Summary JSON | `data/splits/705d388743ea/split_summary.json` | Lines 1–472 | `leakage_risk: true`, `allow_ungrouped_fallback: true` |
| **D-08** | Paper Draft | `docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md` | Lines 1–350 | RQ1, RQ2, RQ3 defined; descriptive framing |
| **D-09** | B4 Event Timelines | `B4/*_timeline.csv` | 27 CSV files | Uniform $\Delta t = 0.200000\,\text{s}$; terminal angle $\theta_N = 0.0^\circ$ |
| **D-10** | Lead-in Screen Code | `src/railway_detection/evaluation/lead_in.py` | Lines 30–65 | Threshold $3.6\,\text{s} = 0.2 + 2.0 + 1.5 - 0.1\,\text{s}$ |

---

## 4. Multi-Tier Governance and Implementation Dependency Graph

The table below maps the strict gating relationships governing project execution:

```
[Governance Sign-Off] ---> [Gate 1: Preflight] ---> [Review Tooling Impl] ---> [Pilot Review]
                                                             |
                                                             v
[Promotion Gate Token] ---> [Gate 2: Promotion] <--- [Full 27-Event Review]
                                   |
                                   v
[Clean Commit & Tree] ---> [Gate 3: Eval Token] ---> [Official Evaluation] ---> [Manuscript]
```

| Gate / Phase | Gate Name & Objective | Upstream Prerequisites | Downstream Activities Unlocked | Blocked Under Fail-Closed Invariants |
| :---: | :--- | :--- | :--- | :--- |
| **Gate 0** | **PI Strategic Endorsement** | D-01, D-02, D-03, D-04, D-06 | Authorizes software implementation & protocol promotion. | Real data access prohibited; codebase remains read-only. |
| **Gate 1** | **Human Review Preflight** | Protocol v7.1.1 promoted; `human_review_session.py` built; `AUTH-MEDIA-ACCESS (PILOT)` issued. | Unlocks 5-event human calibration pilot (Track D). | Raw video playback blocked without valid token. |
| **Gate 2** | **Ground Truth Promotion** | 27 events reviewed & adjudicated; `AUTH-MEDIA-ACCESS (PROMOTION)` issued. | Unlocks execution of `promotion_gate.py`; generates Stage-2.1 promotion receipt. | Promotion receipt missing; evaluation runner refuses execution. |
| **Gate 3** | **Official Evaluation Preflight** | Gate 2 receipt; clean working tree (`porcelain == 0`); Convention B runner verified; `EVAL-AUTH` token issued. | Unlocks official evaluation replay (`cache_only_engine.py` / `evaluation_runner.py`). | Evaluator raises `EVAL_AUTH_NOT_GRANTED` or `BINDING_MISMATCH`. |
| **Gate 4** | **Manuscript Finalization** | Official evaluation metrics produced; dual Table 11 generated; COPE AI disclosure signed. | Unlocks peer-review submission to IEEE ITS or TR-C. | Paper draft retains unverified or non-computable claims. |

---

## 5. Technical Requirements Specification for `human_review_session.py` (Option D2)

This specification defines the software requirements for implementing Option D2 without compromising synthetic safeguards:

### 5.1 Architecture & Module Identity
- **File Location:** `src/railway_detection/review/human_review_session.py`
- **Module Nature:** Standalone, human-facing CLI application.
- **Safety Firewalls:**
  - Preserves `src/railway_detection/annotation/adjudication_session.py` entirely untouched for synthetic unit test execution.
  - Connects to `media_guard.py` via `require_media_authorization(path, "REVIEW_RAW_MEDIA")`.
  - Disallows any automated model inference, bounding box overlay, or proposal generation.

### 5.2 Input Validation
- Loads event list strictly from verified manifests (`data/manifests/train_events_manifest.json`, `no_train_events_manifest.json`).
- Rejects unverified or unknown event identifiers.
- Reads AI proposals from `data/ground_truth/proposals/` in **read-only mode**, verifying file SHA-256 digests against manifest entries.
- Verifies that the human rater's username is registered in `data/governance/authorized_reviewers.json`.

### 5.3 Review Workflow & Blinding
- **Blind Pass Enforcement (RD-013):** During the initial review pass, the rater is presented with the video stream and track geometry landmarks without displaying AI proposal timestamps or previous reviewer entries.
- **Continuous Timestamp Representation:** The UI captures continuous video time in seconds ($t = \text{frame} / \text{fps}$), recorded to 3 decimal places.
- **Directional Ground Truth (RD-010):** Forces explicit rater selection of travel direction (`DOWN_APPROACH`, `UP_DEPARTURE`, or `UNKNOWN`).
- **Censoring Flagging (RD-011):** If the train is already present at video start, forces rater to mark $T_0$ as `CENSORED` with direction `LEFT`.

### 5.4 Output & Audit Ledger Storage
- Produces individual, atomic, timestamped session JSON records:
  `data/ground_truth/reviews/{event_id}_review_{rater_id}_{timestamp}.json`
- Stores rater username, session duration, video hash, proposal hash, confirmed boundaries ($T_0, T_1, T_3, T_4, T_{\text{horn}}$), and rationale text.
- **Immutable Log:** The CLI appends entries and never overwrites, truncates, or deletes prior review records.

### 5.5 Disagreement & Adjudication Protocol
- When two reviewer records exist for an event, computes temporal discrepancies for each boundary:
  $$\Delta t_{\text{landmark}} = |t_{\text{reviewer\_1}} - t_{\text{reviewer\_2}}|$$
- If $\Delta t > \tau_{\text{landmark}}$ (calibrated pilot tolerance), flags the event for researcher adjudication (RD-043).
- Adjudications are written to `data/ground_truth/adjudications/{event_id}_adjudication.json`. If unresolvable, marks the boundary as `UNCERTAIN` (RD-045). Averaging timestamps is strictly prevented.

---

## 6. Formal Risk Register for Implementation Execution

| Risk ID | Risk Description | Severity | Likelihood | Impacted Phase | Mitigation Strategy | Owner |
| :---: | :--- | :---: | :---: | :---: | :--- | :---: |
| **R-01** | Reviewer fatigue causes temporal drift during 27-event review. | High | Medium | Track D (WP-4) | Enforce 30s review floor (RD-046); limit to 5 events per session. | Lead Reviewer |
| **R-02** | Rear camera desync cannot be resolved via audio cross-correlation. | High | High | Version 2.0 | Decouple front V1.0 (Option C); publish V1.0 without M4/M5 claims. | PI |
| **R-03** | Working-tree modifications compromise official evaluation hashes. | Critical | High | Gate 3 (WP-7) | Enforce `git status --porcelain == 0` check prior to token issuance. | Maintainer |
| **R-04** | Model retraining on grouped splits reduces mAP below historical 99.46%. | Medium | High | Track C (WP-5) | Transparently report true generalization; document historical split leakage. | ML Lead |
| **R-05** | Peer reviewers reject manuscript due to 20/23 left-censored lead-in. | High | Low | Track E (WP-8) | Frame paper as observational benchmark; highlight censoring as field reality. | Lead Author |

---

## 7. PI Action Checklist and Execution Hand-off

Principal Investigator Raihan Kabir Rahu should execute the following sequence to unblock the research program:

- [ ] **Step 1:** Review and sign the Decision Sheet in [`MISSION_17A_PI_DECISION_RECONCILIATION.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/MISSION_17A_PI_DECISION_RECONCILIATION.md) §9.
- [ ] **Step 2:** Formally issue the Governance Memo adopting **Option C for D-06** (Phased Scope).
- [ ] **Step 3:** Promote [`docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md) to `docs/FINAL_GROUND_TRUTH_PROTOCOL.md`.
- [ ] **Step 4:** Execute administrative Git commit to clean the 25 modified files in the working tree.
- [ ] **Step 5:** Authorize Gemini to implement `human_review_session.py` (Track B) and grouped CV split scripts (Track C).

---
*Register completed under Master Mission 17A guidelines. Evidentiary records verified against codebase files, manifests, and git history.*
