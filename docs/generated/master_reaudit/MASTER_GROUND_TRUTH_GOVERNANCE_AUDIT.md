# MASTER GROUND TRUTH AND GOVERNANCE AUDIT

**Project:** Train Gate Automation — Bangladesh  
**Audit Mission:** Master Mission 16A  
**Auditor:** Independent Principal Research Auditor, Software Architect, and Governance Reviewer  
**Status:** COMPLETE AUDIT  
**Date:** 2026-11-02  
**Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Execution Authority:** NONE  
**Ground Truth Authorization:** NONE  

---

## 1. Executive Summary: The Ground-Truth Integrity Status

As of Master Mission 16A, **the repository contains exactly ZERO (0) approved, authoritative Stage-2.1 ground-truth event records.**

While historical evaluation pipelines from Phase 2 through Phase 10 reported empirical metrics based on 27 supposedly human-verified review records in `data/ground_truth/reviews/`, Phase 11 forensic auditing discovered that all 27 review records were generated synthetically in an automated burst with identical timestamps. Consequently, all 27 legacy review records were officially marked **INVALIDATED** via non-destructive sibling notices in Phase 11.6.

No real-data benchmark, metric computation, or model evaluation can be executed or cited as ground truth until human review and formal promotion are conducted under strict governance protocols.

---

## 2. Ground-Truth Protocol Architecture (`FINAL_GROUND_TRUTH_PROTOCOL.md` v7.0.0)

`docs/FINAL_GROUND_TRUTH_PROTOCOL.md` (Version 7.0.0, dated 2026-10-12) establishes an auditable three-stage lifecycle designed to balance scalable annotation drafting with rigorous, tamper-evident human verification.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: AI Proposal Generation (Drafting Only)                             │
│ - Offline proposal generator creates candidate boundary timestamps (T0-T4) │
│ - Flags visual/acoustic ambiguities and occlusion intervals                 │
│ - Output: data/ground_truth/proposals/ (IMMUTABLE, READ-ONLY ARCHIVE)       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: Human Verification & Adjudication (Strict Firewall)               │
│ - Frame-by-frame verification by authorized human reviewer                  │
│ - Adjudication session enforced by src/railway_detection/annotation/        │
│   adjudication_session.py                                                   │
│ - Minimum review duration: >= 30.0 seconds per event                        │
│ - Output: Stage-2.1 review records (schema version 8.1.0-stage2.1)          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: Promotion Gate Verification (Promotion Gate)                       │
│ - Enforced by src/railway_detection/annotation/promotion_gate.py            │
│ - Validates reviewer identity against authorized_reviewers.json allowlist   │
│ - Checks media SHA-256 pair integrity and schema conformance               │
│ - Generates cryptographic promotion receipt in data/ground_truth/promoted/ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Protocol Compliance Rules
1. **AI Offline Drafting Firewall:** Stage 1 AI models (Gemini / Claude / local scripts) may only propose candidates. No AI proposal can ever self-promote to ground truth.
2. **Reviewer Identity Binding:** The reviewing party must match an explicitly authorized human identity recorded in `data/ground_truth/authorized_reviewers.json`.
3. **Placename & Role Blocklist:** Generic IDs (`reviewer`, `researcher`, `assistant`, `ai`, `system`, `human_researcher_lead`, `tbd`, etc.) are unconditionally rejected by `promotion_gate.REVIEWER_ID_BLOCKLIST`.
4. **Plausible Human Review Duration:** Review duration must be $\ge 30.0\,\text{s}$ (`MIN_PLAUSIBLE_REVIEW_DURATION_S`), preventing automated bot submissions.
5. **Double Review Triggers:** Any boundary adjustment, engine event, or ambiguity triggers mandatory dual-reviewer concordance.

---

## 3. Forensic Deconstruction of Legacy Reviews & Sibling Invalidation

### 3.1 The Phase 11.1 Discovery
In Phase 11.1 (`docs/PHASE11_1_ANNOTATION_INTEGRITY_AUDIT.md`), a forensic examination of the 27 review records located in `data/ground_truth/reviews/` revealed the following critical defects:
1. **Identical Timestamp Across All Records:** Every single review file contained `review_date_utc: "2026-10-12T16:51:21Z"`.
2. **Sub-Second File System Creation Burst:** File system modification times showed that all 27 files were written within a ~5-second window (~0.2 seconds per record), proving they were created by an automated script, not by a human inspecting frame-by-frame video.
3. **Superseded Proposal Referencing:** All 27 records pointed to legacy proposal versions rather than active candidate proposals.
4. **Schema Incompatibility:** The records lacked Stage-2.1 schema compliance and could not pass the Phase 11.2 promotion gate.

### 3.2 Phase 11.6 Sibling Invalidation Mechanism
Under researcher direction dated 2026-10-14 (`raihankabirrahu@gmail.com`), Phase 11.6 implemented non-destructive sibling invalidation:
- Original legacy files (`event_*_review.json`) were preserved untouched to prevent data loss or history erasure.
- For each file, a sibling notice was authored: `event_*_review.INVALIDATION_NOTICE.json`.
- A directory-level marker `data/ground_truth/reviews/_INTEGRITY_NOTICE.md` was established.
- Each notice records:
  - `disposition: "INVALIDATED"`
  - `applies_to_file_sha256_at_notice_time`
  - `reason: "THREAD 1 (process integrity, Phase 11.1...)"`
- Total invalidated records: **23 train events, 3 no-train events, 1 engine event = 27 total.**

---

## 4. Software Implementation Audit of Annotation Modules

### 4.1 Promotion Gate (`src/railway_detection/annotation/promotion_gate.py`)
- **Reviewer Allowlist Verification:** `load_authorized_reviewers()` parses `data/ground_truth/authorized_reviewers.json`.
  - Current authorized reviewer list: `["raihankabirrahu@gmail.com"]`.
  - Blocklist enforcement: `REVIEWER_ID_BLOCKLIST = frozenset({'', 'reviewer', 'researcher', 'assistant', 'ai', 'system', 'n/a', 'human_researcher_lead', 'human_annotator', 'annotator', 'na', 'tbd', 'human', 'unknown'})`.
- **Validation Rules in `validate_for_promotion()`:**
  - Enforces schema version `STAGE_2_1_SCHEMA_VERSION = "8.1.0-stage2.1"`.
  - Verifies presence and valid formatting of timestamps ($T_0, T_1, T_3, T_4$).
  - For non-synthetic runs, calls `require_media_authorization()` and checks media SHA-256 pairs against raw footage.
  - Rejects any file accompanied by an `INVALIDATION_NOTICE`.
  - Status: **Fully implemented and unit tested synthetically.**

### 4.2 Second Review Engine (`src/railway_detection/annotation/second_review.py`)
- Implements 5 deterministic second-review triggers:
  1. `TRIGGER_CORRECTED`: Human reviewer modified AI proposal timestamp by $>0.5\,\text{s}$.
  2. `TRIGGER_ENGINE_T3_T4`: Engine event requiring structural $T_3 \equiv T_4$ verification.
  3. `TRIGGER_EXPLICIT_FLAG`: Reviewer or AI flagged visual/acoustic ambiguity.
  4. `TRIGGER_MEDIA_HASH`: Media file hash changed or exhibits boundary anomaly.
  5. `TRIGGER_UNCERTAIN_BOUNDARY`: Boundary interval uncertainty flagged.
- Status: **Implemented; formal adoption pending under RD-043 and RD-045.**

### 4.3 Adjudication Session Runner (`src/railway_detection/annotation/adjudication_session.py`)
- Manages real-time human verification workflow.
- Enforces `MIN_PLAUSIBLE_REVIEW_DURATION_S = 30.0`. If a reviewer attempts to submit an event review in $<30.0\,\text{s}$, `ReviewDurationTooShortError` is raised.
- Prevents concurrent duplicate submissions (`DuplicateRecordError`).
- Ensures researcher confirmation is explicitly recorded.
- Status: **Fully implemented; zero production sessions recorded.**

---

## 5. Reviewer Allowlist and Human Review Requirements Checklist

Before any real-data evaluation can proceed, the following governance milestones must be satisfied:

| Prerequisite ID | Requirement Description | Governance Authority | Current Status |
| :--- | :--- | :--- | :--- |
| **GT-REQ-01** | Formal appointment of authorized human reviewers in `authorized_reviewers.json` | Lead Researcher | Partially Satisfied (1 reviewer on list) |
| **GT-REQ-02** | Adoption of Second-Review Protocol (RD-043) | Lead Researcher | **PENDING** |
| **GT-REQ-03** | Adoption of Disagreement Resolution Protocol (RD-045) | Lead Researcher | **PENDING** |
| **GT-REQ-04** | Execution of human adjudication sessions for all 27 events ($\ge 30\,\text{s}$/event) | Authorized Human Reviewers | **UNEXECUTED (0/27)** |
| **GT-REQ-05** | Second-review adjudication for triggered events | Second Human Reviewer | **UNEXECUTED** |
| **GT-REQ-06** | Promotion gate pass and promotion receipt generation | Automated Gate (`promotion_gate.py`) | **UNEXECUTED (0 receipts)** |
| **GT-REQ-07** | Creation of promoted dataset split manifest (`data/ground_truth/promoted/`) | Governance Pipeline | **UNEXECUTED** |

---

## 6. Audit Conclusion

The ground-truth governance architecture of the Train Gate Automation project is **technically sound, defensively designed, and highly robust against automated tampering**.

However, because all 27 legacy reviews were invalidated and zero Stage-2.1 reviews have been conducted by human reviewers:
1. **There is currently zero certified ground truth in the repository.**
2. **All historical metrics (Phase 2–10) are unverified historical artifacts.**
3. **No real-data evaluation is authorized or methodologically possible at this time.**
