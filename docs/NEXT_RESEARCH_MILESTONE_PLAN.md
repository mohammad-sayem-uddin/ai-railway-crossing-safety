# Next Research Milestone Plan — Dependency-Ordered Informational Reference

**Generated:** 2026-10-25
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`
**Repository HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
**Status:** INFORMATIONAL ONLY — This document grants, implies, or triggers **no** authorization.

---

## 0. Non-Authorization Declaration

This document is a **planning reference only**. It does not:

- Authorize any implementation, evaluation, adjudication, promotion, deployment, or media access.
- Constitute or imply EVAL-AUTH, ADJ-AUTH, timing-pilot authorization, activation, or any other gated approval.
- Override, modify, or relax any hold, blocker, stop condition, or governance constraint.
- Grant permission to run official readiness commands, evaluation runners, LEG-EXEC, or pilot workflows.
- Create, modify, or invalidate any record, decision, label, annotation, or governance artifact.

All actions described below remain **prohibited** until each is independently authorized through the governance mechanisms documented in the referenced files. This plan merely describes the dependency-ordered sequence in which those authorizations would need to occur, based on the current state of the repository.

---

## 1. Current State Summary (as of 2026-10-25)

| Domain | State | Source |
|--------|-------|--------|
| Official readiness gate | **NOT READY**, exit 3, 9 blocker instances / 7 codes | `docs/FINAL_READINESS_WORKSTREAM_REPORT_20261019.md` |
| Stage-2.1 readiness CLI | **NOT READY**, exit 2, `NO_RECORDS` | Same |
| Stage-2.1 timing pilot | **HELD / INACTIVE** | `docs/STAGE21_TIMING_PILOT_RELEASE_20261019.md` |
| Media-access incident | **UNRESOLVED** | `docs/MEDIA_ACCESS_INCIDENT_INVESTIGATION_20261020.md` |
| Ground truth pipeline | Blocked at Stage-2.1: 0/27 valid records, 0/27 promotion receipts | `docs/DEEP_RESEARCH_COMPLETION_AUDIT_20261025.md` |
| Legacy reviews (v6) | All 27 **INVALIDATED** | `data/ground_truth/reviews/_INTEGRITY_NOTICE.md` |
| EVAL-AUTH | **Absent** — not recorded | `docs/FINAL_READINESS_WORKSTREAM_REPORT_20261019.md` |
| ADJ-AUTH | **Absent** — not recorded | `docs/RESEARCHER_ACTION_PACKAGE_v1_20261019.md` |
| Event split decision | **Missing** (`null` binding) | Same |
| R04 scope decision | **Missing** (`null` binding) | Same |
| Protocol decision (v9 vs M4) | **Missing** (`null` binding) | Same |
| Input manifest | **Missing** (`null` binding) | Same |
| Promotion receipt | **Missing** (`null` binding) | Same |
| Reproducibility audit | 6 PASS / 0 FAIL / 5 UNRESOLVED / 2 NOT_AVAILABLE | `docs/FINAL_READINESS_WORKSTREAM_REPORT_20261019.md` |
| Test suite | 1,206 passed, 0 failed | Same |
| Live-media integrity | 54 files hashed, 0 mismatches against Layer-B inventory | Same |

### Live Bindings at Last Assessment

| Binding | SHA-256 | Status |
|---------|---------|--------|
| `decision_policy_sha256` | `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575` | Present |
| `frozen_config_sha256` | `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e` | Present |
| `event_split_decision_sha256` | — | **Missing** |
| `input_manifest_sha256` | — | **Missing** |
| `protocol_profile_sha256` | — | **Missing** |
| `r04_scope_decision_sha256` | — | **Missing** |
| `stage21_promotion_receipt_sha256` | — | **Missing** |

### Blocker Instance Breakdown (9 instances / 7 codes)

The nine instances consist of **six independent prerequisites** and **three derived `COHORT_APPROVAL_MISSING` diagnostics** (for engine/no-train/train cohorts). The cohort diagnostics clear only when genuine valid approved Stage-2.1 evidence exists; they are not independent decisions.

---

## 2. Dependency-Ordered Milestone Sequence

The following steps are ordered by dependency. No step may begin until all predecessor steps are complete and independently verified. **None of these steps are authorized by this document.**

### Step 1: Resolve the Media-Access Incident

**Owner:** Authorized independent reviewer with access to filesystem/audit evidence.
**Current state:** UNRESOLVED (investigation complete, central question unanswered).
**Reference:** `docs/MEDIA_ACCESS_INCIDENT_INVESTIGATION_20261020.md`, `docs/MEDIA_ACCESS_HOLD_RESOLUTION_PLAN.md`

**Prerequisites:**
- Access to `/private/var/audit` (BSM records) or equivalent filesystem audit trail, OR a documented researcher decision to close the incident based on available evidence.
- Filesystem audit logging enabled (Endpoint Security, `fs_usage`, or BSM) before any future official command execution.

**Required evidence for closure:**
- Determination of whether source-media bytes were read or hashed during the two 2026-10-19 invocations.
- If unable to determine: explicit researcher decision on acceptable residual risk and closure conditions.

**Stop condition:** If the incident reveals broader unauthorized access beyond the two documented invocations, halt all downstream steps and escalate to the researcher.

**Downstream effect:** The timing-pilot release remains HELD and the pilot INACTIVE until this is resolved. No media access, pilot activation, or official readiness command may proceed while the incident is open.

---

### Step 2: Close Remaining Researcher Decisions

**Owner:** Researcher (principal investigator).
**Reference:** `docs/PHASE11_3_RESEARCHER_DECISIONS.md`, `docs/OPEN_DECISIONS_AND_BLOCKERS.md`, `docs/RESEARCHER_ACTION_PACKAGE_v1_20261019.md`

**Decisions required (each is a separate, explicit researcher-authored record):**

| Decision ID | Subject | Options / Notes |
|-------------|---------|-----------------|
| D1 (numeric) | Review-duration hard floor and fast-band upper threshold | Requires genuine timing pilot data first (see Step 4–6). Mechanism D selected 2026-10-14; 30.0s schema floor is sanity-check only. |
| D3(a) | Second-review trigger | Already selected; implementation pending. |
| D3(c) | Clear-boundary audit mechanism and frequency | Must be recorded before formal review. |
| R-SPLIT | Event split / analysis design | Must account for one-crossing / two-session leakage finding. Deterministic hash allocation is candidate only, not leakage-safe. |
| R04-SCOPE | Per-event camera scope for dual-camera analysis | Calibration diagnostics do not approve scope. 11 events CALIBRATION_SUPPORTED, 9 AMBIGUOUS, 7 PROVISIONAL. |
| PROTOCOL | Endpoint selection: v9 or M4 | No default may be selected by engineering. |

**Stop condition:** If the researcher determines that the one-crossing limitation invalidates the intended held-out design, independent crossing/session data acquisition becomes a prerequisite (separate gate with site permission, safety, privacy/consent review).

**Downstream effect:** These decisions populate the `null` live bindings required for the manifest and EVAL-AUTH.

---

### Step 3: Authorize Engineering Preparation of the Timing Pilot

**Owner:** Researcher authorizes; engineering executes preparation only.
**Reference:** `docs/RESEARCHER_ACTION_PACKAGE_v1_20261019.md` §3, §9

**Scope of this authorization (when granted):**
- Engineering preparation only of the timing pilot for an exact event/reviewer scope.
- Deliver a focused, tested genuine-media pilot workflow.
- No media bytes are opened, hashed, or accessed during preparation.
- Output is a release artifact with verified hashes (already exists at v0.1.0 but is HELD).

**Evidence required:**
- Researcher's explicit written authorization naming: event(s), allowlisted reviewer(s), original-media use scope, output location (`data/ground_truth/review_pilots`), and explicit statement that no approval/promotion is granted.
- Schema conformance: `schemas/stage21_timing_pilot.schema.json` — authorization object.

**Stop condition:** If the release manifest hash verification fails or the workflow code has been modified since the last verified release, halt and re-verify before any further action.

**Not authorized by this step:** Media access, pilot activation, review execution, or any official record creation.

---

### Step 4: Engineering Delivers Tested Genuine-Media Pilot Workflow

**Owner:** Engineering (agent/developer).
**Reference:** `src/railway_detection/annotation/stage21_timing_pilot.py`, `schemas/stage21_timing_pilot.schema.json`

**Deliverables:**
- Tested, hash-verified pilot interaction workflow that uses real media only upon valid activation.
- Release manifest regenerated and hash-bound to implementation, schema, and test files.
- All tests passing (`tests/test_stage21_timing_pilot.py`).

**Constraints:**
- Synthetic/test mode only until activation. The module rejects the project checkout before reading any input in test mode.
- No model predictions or candidate boundaries exposed to the reviewer.
- No approval, promotion, or evaluation capability in the pilot code path.

**Stop condition:** Any test failure, hash mismatch, or schema validation error halts delivery.

---

### Step 5: Researcher Reviews and Activates via Hash-Bound Addendum

**Owner:** Researcher.
**Reference:** `docs/RESEARCHER_ACTION_PACKAGE_v1_20261019.md` §9, `schemas/stage21_timing_pilot.schema.json` — activation definition

**Prerequisites:**
- Step 1 (incident) resolved.
- Step 3 authorization in place.
- Step 4 deliverable verified by researcher (release version/hash reviewed).

**Activation record must include (per schema):**
- `schema_version`: `stage21-human-review-pilot-activation/1`
- Bound to exact `authorization_sha256` and `workflow_release_sha256`.
- `activated_by` must be on the researcher allowlist.
- Separate from the authorization — a distinct record.

**Stop condition:** If the researcher does not explicitly activate, the pilot remains INACTIVE indefinitely. No automatic or implied activation exists.

---

### Step 6: Reviewer Completes the Non-Approved Timing Pilot

**Owner:** Allowlisted human reviewer.
**Reference:** `src/railway_detection/annotation/stage21_timing_pilot.py`, `schemas/stage21_timing_pilot.schema.json` — draft definition

**Constraints during execution:**
- Output goes to `data/ground_truth/review_pilots` only.
- All records are `HUMAN_REVIEW_COMPLETED_UNAPPROVED_PILOT` with `ground_truth_eligible: false` and `official_approval: false`.
- `approval_transition` is `PROHIBITED_IN_TIMING_PILOT`.
- No model predictions or candidate boundaries visible.
- Source media accessed only via the activated, hash-bound workflow.

**Output:** Genuine timing observations (duration_monotonic_s, duration_wall_clock_s) for the pilot events. These inform D1 numeric thresholds but create no official labels.

**Stop condition:** If the reviewer encounters any technical failure, media integrity issue, or workflow anomaly, halt immediately and report to the researcher.

---

### Step 7: Researcher Records D1 Numbers from Genuine Timing Observations

**Owner:** Researcher.
**Prerequisite:** Step 6 complete with valid pilot timing data.

**Action:** Choose and record a hard floor and fast-band upper threshold from observed durations. The 30.0s flat schema floor remains a sanity check only.

---

### Step 8: Record D3(c) Audit Policy and Implement D3(a) Trigger

**Owner:** Researcher records; engineering implements.
**Prerequisite:** D1 numbers recorded (Step 7).

---

### Step 9: Issue Formal ADJ-AUTH (Distinct from Timing-Pilot Authorization)

**Owner:** Researcher.
**Reference:** `docs/RESEARCHER_ACTION_PACKAGE_v1_20261019.md` §7

**The ADJ-AUTH must name:**
- Exact Stage-2.1 operation.
- Event/cohort scope.
- Each reviewer identity.
- Boundaries/protocol version.
- Second-review obligations.
- Source-media inventory/hash.
- Allowed output path.
- Minimum/fast-band duration rules.
- Clear-boundary audit rule.
- Model-independence requirement.
- Record state/approval limits.
- Stop/withdrawal rules.
- Explicit statement that no evaluation, field work, or physical railway operation is authorized.

**Constraints:**
- ADJ-AUTH is NOT implied by engineering permission, the action package, EVAL-AUTH, LEG-EXEC, or timing-pilot authorization.
- Must be validated against live hashes.
- The existing `adjudication_session.py` is synthetic-only and cannot create real-event records.

**Stop condition:** If any prerequisite (Steps 1–8) is incomplete or the researcher does not issue ADJ-AUTH, formal review cannot begin.

---

### Step 10: Conduct Genuine Stage-2.1 Review

**Owner:** Allowlisted human reviewer(s).
**Prerequisite:** ADJ-AUTH issued and verified.

**Scope:** All 27 events (or researcher-defined subset). Estimated 4–8 hours of active researcher work.

**Requirements:**
- Human-controlled real-data review workflow (not the synthetic runner).
- Independent second reviewer if D3 requires one (must be in the maintained allowlist).
- Media-hashing readiness workflow must report READY before promotion receipt can be issued.

**Stop condition:** Any deviation from the ADJ-AUTH scope, reviewer withdrawal, or technical failure halts review.

---

### Step 11: Researcher Records Split, R04, and Protocol Decisions

**Owner:** Researcher.
**Prerequisite:** Can occur in parallel with Steps 9–10, but must be complete before manifest construction.

**Records:**
- R-SPLIT: Leakage-valid analysis design (considering one-crossing / two-session constraint).
- R04-SCOPE: Per-event camera scope.
- PROTOCOL: v9 or M4 endpoint selection.

---

### Step 12: Build Evaluation Input Manifest

**Owner:** Engineering.
**Prerequisite:** Steps 10 and 11 complete. Approved Stage-2.1 records exist. All decision hashes non-null.

**Constraints:**
- Built from verified decisions and real output payloads only.
- Binds decision hashes and raw source hashes.
- Must NOT be hand-authored or pre-created.
- Uses existing `build_evaluation_input_manifest` function.

---

### Step 13: Issue EVAL-AUTH (Final Gate)

**Owner:** Researcher.
**Prerequisite:** All seven live bindings non-null. All upstream artifacts validated. Readiness gate re-run reports READY.

**EVAL-AUTH is:**
- Bound to exact live hashes at time of recording.
- For one named official evaluation only.
- NOT field/safety authorization.
- NOT physical/operational authorization.
- The last authorization in the chain; it cannot precede any upstream artifact.

**Stop condition:** If the readiness gate does not report READY after all prerequisites are met, do not issue EVAL-AUTH. Investigate and resolve the remaining blocker(s) first.

---

## 3. What Can Proceed Independently (No Blockers)

Per `docs/DEEP_RESEARCH_COMPLETION_AUDIT_20261025.md`, the following work streams are **not blocked** by any current hold and require no additional authorization:

1. Format existing vision model evaluation results (mAP@50=0.9946, confusion matrix, PR curves) into paper-quality figures.
2. Format existing audio model evaluation results (V1→V2→V3 progression, hard-negative analysis) into paper-quality figures.
3. Write the architecture/system design section using implemented and tested code.
4. Dataset description.
5. Synthetic fusion/policy demonstration.
6. Literature review and related work.

These are independent of the gated path above and do not require media access, ground truth, or any authorization record.

---

## 4. What Cannot Be Fixed (Permanent Limitations)

| Limitation | Consequence |
|-----------|-------------|
| Single crossing site | Cannot claim cross-crossing generalization; declare as limitation |
| 2 capture sessions only | Limited session-diversity analysis |
| T0 left-censored in all 23 train events | Cannot report true physical detection latency; report as left-censored |
| 3 no-train controls (~1 min total) | Limited false-positive rate estimation |
| no_train_events/event_002: 60/60 FP rate | Must be analyzed as failure case, not excluded |
| 16/27 events lack dual-camera calibration | Full-cohort dual-camera claims impossible; use single-camera or calibrated subset |

---

## 5. Escalation Paths

| Condition | Escalation |
|-----------|-----------|
| Media-access incident reveals broader unauthorized access | Halt all downstream steps. Researcher determines remediation scope. |
| Timing pilot reveals workflow defect or security concern | Halt pilot. Engineering investigates. Re-release required before retry. |
| Reviewer withdraws or is unavailable | Researcher identifies replacement; update allowlist; re-issue ADJ-AUTH if scope changes. |
| Readiness gate reports unexpected blocker after all prerequisites met | Do not issue EVAL-AUTH. Investigate root cause. Document finding. |
| Researcher determines one-crossing limitation invalidates intended design | Acquire independent crossing/session data (separate gate: site permission, safety, privacy/consent). |
| Any hash mismatch detected in release/activation/authorization chain | Halt immediately. Do not proceed. Investigate tampering or corruption. |

---

## 6. Explicit Prohibitions (Unchanged by This Document)

- No evaluation, deployment, safety authorization, or downstream release is permitted.
- No official readiness command may be run without filesystem audit logging active.
- The timing pilot may not be activated, the release manifest regenerated, or activation authorization created until the media-access incident is resolved.
- The `evaluation status` command must not be re-run without audit logging.
- No source-media bytes may be opened, read, hashed, decoded, played, previewed, or inferred upon outside the activated pilot workflow.
- The synthetic adjudication runner (`adjudication_session.py`) must not be used for real-event records.
- No proposal values may be manually copied into official records.
- Engineering must not infer, default, or fabricate any researcher decision.
- This document does not authorize, imply, or schedule any of the above actions.

---

## 7. Cross-Reference Index

| Document | Relevance |
|----------|-----------|
| `docs/FINAL_READINESS_WORKSTREAM_REPORT_20261019.md` | Gate state, blocker mapping, engineering changes, verification results |
| `docs/FINAL_READINESS_EVIDENCE_PREREQUISITES_20261019.md` | Full dependency map and evidence requirements |
| `docs/RESEARCHER_ACTION_PACKAGE_v1_20261019.md` | Human actions, ADJ-AUTH template, pilot authorization path |
| `docs/RESEARCHER_READINESS_VERIFICATION_20261019T1456Z.md` | Session/crossing leakage evidence, hashes |
| `docs/MEDIA_ACCESS_INCIDENT_INVESTIGATION_20261020.md` | Incident evidence, gaps, disposition |
| `docs/MEDIA_ACCESS_HOLD_RESOLUTION_PLAN.md` | Hold resolution prerequisites |
| `docs/STAGE21_TIMING_PILOT_INCIDENT_20261019.md` | Containment record, confirmed facts, unknowns |
| `docs/STAGE21_TIMING_PILOT_RELEASE_20261019.md` | Release manifest, HELD status |
| `docs/PHASE11_3_RESEARCHER_DECISIONS.md` | Decision definitions and current status |
| `docs/PHASE11_11_ADJUDICATION_PROTOCOL.md` | ADJ-AUTH requirements |
| `docs/PHASE11_12_ADJUDICATION_CLOSURE_REPORT.md` | Adjudication state |
| `docs/OPEN_DECISIONS_AND_BLOCKERS.md` | Open items register |
| `docs/DEEP_RESEARCH_COMPLETION_AUDIT_20261025.md` | Full pipeline status, evidence map, limitations |
| `docs/FINAL_RESEARCH_HANDOVER_20261021.md` | Handover context |
| `docs/FINAL_RESEARCH_IMPLEMENTATION_ROADMAP_20261021.md` | Implementation roadmap |
| `docs/APPROVAL_RECONCILIATION_REPORT.md` | Approval state reconciliation |
| `docs/CHANGE_REVIEW_RELEASE_DISPOSITION_20261020.md` | Release disposition |
| `docs/INCIDENT_CLOSURE_REVIEW_20261020.md` | Incident closure criteria |
| `docs/PREMATURE_OPENING_DECISION_EVIDENCE.md` | Premature-opening evidence |
| `docs/R04_CALIBRATION_VALIDATION_REPORT.md` | R04 calibration status |
| `schemas/stage21_timing_pilot.schema.json` | Pilot authorization/activation/draft schemas |
| `src/railway_detection/annotation/stage21_timing_pilot.py` | Pilot implementation (fail-closed) |

---

## 8. Document Provenance

- **Created:** 2026-10-25
- **Created by:** Agent (informational synthesis)
- **Authorized by:** No one. This document is self-declaring as non-authorizing.
- **Review status:** Not reviewed.
- **Modification policy:** Any amendment must preserve the non-authorizing declaration and all stop conditions. Amendments do not constitute authorization.

---

*This document was generated as an informational planning reference. No authorization, decision, label, annotation, evaluation, deployment, or governance artifact was created, modified, or implied by its production.*