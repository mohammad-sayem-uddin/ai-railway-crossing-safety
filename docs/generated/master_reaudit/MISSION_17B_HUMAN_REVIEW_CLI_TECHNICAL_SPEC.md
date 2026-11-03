# MISSION 17B: HUMAN-OPERATED REVIEW CLI TECHNICAL SPECIFICATION

**Project:** Train Gate Automation — Bangladesh
**Subsystem:** Ground Truth Acquisition & Annotation Tooling
**Target Module:** `src/railway_detection/annotation/human_review_session.py` (SPECIFICATION ONLY — NOT IMPLEMENTED)
**Document ID:** `MISSION-17B-DELIV-01`
**Execution Authority:** NONE (Implementation Pending PI Approval of Decision D-02) **17C-0: corrected requirements are in the appended correction history; original body retained.**
**Governance Invariants:** RD-010, RD-011, RD-013, RD-042, RD-043, RD-045, RD-046, RD-047
**Date:** 2026-11-03

---

## 1. Executive Summary & Governance Scope

This document specifies the technical architecture, data structures, authorization protocols, threat model, and synthetic verification plan for the proposed human-operated ground-truth review interface: `src/railway_detection/annotation/human_review_session.py`.

Under researcher directional mandates **RD-042**, **RD-043**, and **RD-045**, artificial intelligence systems are strictly prohibited from generating, modifying, or adjudicating ground-truth annotations for real-world video or audio footage. True physical ground truth must derive solely from independently verified human visual observations.

> [!IMPORTANT]
> **Specification-Only Status:** This document provides the blueprint for future implementation. In accordance with Mission 17B constraints, no production code has been modified, no mock CLI has been placed into the production tree, and no media access tokens have been issued.

---

## 2. Assessment of Existing Repository Infrastructure

The current codebase contains several components governing adjudication and safety, which provide the foundation and boundaries for the proposed review CLI:

### 2.1 Existing Modules and Safeties
1. **Adjudication Session Harness ([`adjudication_session.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/adjudication_session.py)):**
   - Implements an interactive console session runner designed strictly for synthetic testing.
   - Enforces intentional tripwires at [`adjudication_session.py:126-142`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/adjudication_session.py#L126-L142):
     - `_require_synthetic_id(event_id)`: Rejects any event ID that does not match `^synthetic_[A-Za-z0-9_-]+$`.
     - `_require_temp_path(path)`: Refuses any file path not located within the operating system temporary directory (`tempfile.gettempdir()`).
     - `_check_model_firewall(path)`: Rejects paths containing model-output keywords (`yolo`, `checkpoint`, `inference`).
   - **Architectural Imperative:** These synthetic tripwires must **never** be weakened or bypassed in `adjudication_session.py`. Instead, `human_review_session.py` will be authored as a clean, separate module specifically designed for human operation under explicit authorization.

2. **Media Guard & Authorization ([`media_guard.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/safety/media_guard.py)):**
   - Enforces operation-boundary authorization on raw media files under `data/raw/`.
   - Requires valid `data/governance/AUTH-MEDIA-ACCESS.json` matching `MEDIA_ACCESS_SCHEMA_VERSION = "phase5-media-access-authorization/2"`.
   - Distinguishes operations (`READ_RAW_MEDIA`, `HASH_RAW_MEDIA`, `MEDIA_PROBE`, etc.).
   - Canonicalizes filesystem paths and refuses unauthorized access fail-closed.

3. **Promotion Gate ([`promotion_gate.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/promotion_gate.py)):**
   - Enforces human-only ground-truth promotion rules.
   - Validates that annotations derive from reviewers listed in `data/ground_truth/authorized_reviewers.json`.
   - Rejects synthetic IDs in production ground truth (`validate_non_synthetic_record`).
   - Requires two independent reviews before promotion.

4. **Annotation Schemas ([`schemas.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/schemas.py), [`stage2_1_schema.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/stage2_1_schema.py)):**
   - Defines schema contracts for proposal documents, landmark timestamps ($T_0, T_1, T_2, T_3, T_4$), camera alignment markers, and environmental tags.
   - Version `8.1.0-stage2.1` establishes formal types for reviewer identity, timestamp entries, confidence scores, and occlusion notes.

---

## 3. Human Reviewer Session Lifecycle

The proposed `human_review_session.py` governs the complete interactive workflow for human raters:

```
[1. Preflight & Auth] ──> [2. Reviewer Login] ──> [3. Event Queue Selection]
                                                              │
┌─────────────────────────────────────────────────────────────┘
▼
[4. Media Access & Verification] ──> [5. Blind First-Pass Review Form]
                                                      │
┌─────────────────────────────────────────────────────┘
▼
[6. Ledger Persistence] ──> [7. Disagreement Check] ──> [8. Session Termination]
```

### 3.1 Preflight & Authorization
1. **Working Tree Verification:** Checks `git status --porcelain` to verify the working tree is clean and uncorrupted.
2. **Authorization Token Inspection:** Reads and parses `data/governance/AUTH-MEDIA-ACCESS.json`.
   - Confirms token status is `APPROVED` and not expired (`now_utc < expires_at_utc`).
   - Confirms token scope includes `READ_RAW_MEDIA` and `REVIEW` purpose.
   - Re-hashes the active protocol document specified in the token bindings and confirms match.
3. **Reviewer Allowlist Verification:** Loads `data/ground_truth/authorized_reviewers.json` and verifies that the logged-in reviewer handle is an authorized, qualified individual.

### 3.2 Reviewer Identity & Blinding (RD-013)
- Reviewers authenticate using their registered handle (e.g., `rater_01`, `rater_02`, `lead_researcher`).
- **Strict Blinding Rule (RD-013):** First-pass reviewers are never presented with model predictions, AI proposal timestamps, or prior reviewer judgments. The CLI provides a blank slate for landmark entry.
- The interface records:
  - `reviewer_id`: Verified string handle.
  - `session_id`: Unique UUIDv4 generated at session startup.
  - `start_time_utc`: ISO 8601 timestamp.
  - `client_git_head`: Commit hash of repository at session invocation.

### 3.3 Event Selection & Media Presentation
- CLI displays an event queue based on the review matrix:
  - Phase 1: 5-event calibration pilot.
  - Phase 2: 27-event comprehensive review.
- Media Guard authorizes access to the raw video stream (`front` and/or `back` stream according to camera scope).
- Rater uses external certified media player (or wrapped frame-accurate playback window) displaying exact millisecond timecodes.

### 3.4 Interactive Review Form & Schema Validation
The CLI presents structured prompts requesting the following mandatory fields:

1. **Travel Direction (RD-010):**
   - Prompt: `Train travel direction [towards_camera | away_from_camera | stationary | unknown]:`
   - Strict validation: Free-form text rejected. Must match enum.

2. **Landmark Timestamps (in seconds from video start):**
   - $T_0$: Entry into field of view (or `LEFT_CENSORED` if train is already visible at recording onset per RD-011).
   - $T_1$: Train nose crosses outer boundary / warning threshold.
   - $T_2$: Train nose reaches crossing roadway boundary.
   - $T_3$: Train nose passes crossing island.
   - $T_4$: Train tail clears crossing roadway boundary (or `RIGHT_CENSORED` / `UNOBSERVABLE` if rear view obstructed).
   - Horn Audio ($T_{\text{horn}}$): Audible acoustic horn onset (or `NOT_AUDIBLE` per RD-027).

3. **Gate Operation Landmarks:**
   - $T_{\text{gate\_start\_descend}}$: Boom starts downward motion.
   - $T_{\text{gate\_fully\_closed}}$: Boom reaches horizontal stop ($0^\circ$).
   - $T_{\text{gate\_start\_ascend}}$: Boom starts upward motion.
   - $T_{\text{gate\_fully\_open}}$: Boom reaches vertical stop ($90^\circ$).

4. **Environmental & Visual Metadata:**
   - Weather: `[clear | rain | fog | overcast | night]`
   - Occlusions: `[none | vehicle_in_way | vegetation | lens_flare | glare | heavy_shadow]`
   - Rater Confidence: `[high | medium | low]`

5. **Schema Validation:**
   - Monotonicity check: $T_0 \le T_1 \le T_2 \le T_3 \le T_4$.
   - Plausibility bounds: All timestamps must be non-negative and $\le$ media duration.
   - Instant validation: If rater enters $T_2 < T_1$, CLI rejects input, displays explanatory error, and prompts for re-entry.

### 3.5 Immutable Ledger Persistence
- Rater observations are appended immediately to a per-session JSONL ledger:
  `data/ground_truth/reviews/session_<session_id>.jsonl`
- Each record contains:
  - Complete observation payload.
  - SHA-256 hash of previous record (hash-chaining).
  - Reviewer signature / attestation block.
  - Timestamp of submission.
- **Non-Destructive Invariant:** Original rater submissions are never modified, edited, or overwritten. If a rater corrects a mistake before session exit, a correction record referencing the original record ID is appended.

---

## 4. Disagreement Handling & Adjudication Workflow

Under **RD-043** and **RD-045**, two independent reviews are required for every event before ground truth can be promoted.

### 4.1 Disagreement Detection
When Reviewer 1 ($R_1$) and Reviewer 2 ($R_2$) have both submitted observations for event $e$:
1. The system computes timestamp deltas for all shared visual landmarks:
   $$\Delta T_k = |T_{k, R_1} - T_{k, R_2}| \quad (k \in \{0, 1, 2, 3, 4\})$$
2. Disagreement Trigger Thresholds:
   - Direction disagreement: $R_1.\text{direction} \neq R_2.\text{direction}$ $\implies$ **MANDATORY ADJUDICATION**.
   - Landmark delta: $\Delta T_k > \tau_k$ (where $\tau_k$ is the landmark-specific tolerance defined by PI in Decision D-05) $\implies$ **MANDATORY ADJUDICATION**.
   - Occlusion / Landmark Visibility Disagreement: One rater marks landmark observable, other marks censored $\implies$ **MANDATORY ADJUDICATION**.

### 4.2 Adjudication Interface
- When disagreement occurs, the event enters the adjudication queue.
- Only the Principal Investigator or Lead Researcher listed on the adjudication allowlist may run the adjudication workflow.
- The adjudication interface displays:
  - Side-by-side comparison of $R_1$ and $R_2$ observations.
  - Timecode deltas highlighted in red.
  - Rater notes and confidence ratings.
- The adjudicator may:
  1. **Adopt Observation A ($R_1$):** With recorded scientific justification.
  2. **Adopt Observation B ($R_2$):** With recorded scientific justification.
  3. **Record Resolved Intermediate Value:** Only if visual re-inspection of the exact video frame provides definitive evidence.
  4. **Declare State UNCERTAIN (RD-045):** If the landmark cannot be resolved with high scientific confidence, it is marked `UNCERTAIN`.

> [!CAUTION]
> **Zero Averaging Invariant:** The system strictly prohibits automated mathematical averaging:
> $$T_{\text{adjudicated}} \neq \frac{T_{R_1} + T_{R_2}}{2}$$
> Physical boundaries represent real-world physical events at discrete frames, not statistical interpolations.

---

## 5. Granular Multi-Tier Authorization Architecture

To resolve the security findings of Missions 16E, 16F, and 17A, authorization must be partitioned into four strictly non-interchangeable tiers:

| Tier | Authorization Class | Scope & Permissions | Permitted Roles | Target Resources |
| :---: | :--- | :--- | :--- | :--- |
| **Tier 1** | `AUTH-MEDIA-ACCESS (REVIEW)` | Read raw video frames; probe duration; display timecodes. | Authorized Raters | `data/raw/**/*.mp4`, `*.mov` |
| **Tier 2** | `AUTH-MODEL-CHECKPOINT` | Read YOLO weights; load PyTorch state dicts. | CV Researchers | `experiments/**/weights/*.pt` |
| **Tier 3** | `AUTH-PROMOTION` | Sign off and promote reviewed ledger to canonical `data/ground_truth/`. | Principal Investigator | `data/ground_truth/canonical_gt.json` |
| **Tier 4** | `AUTH-EVALUATION` | Run end-to-end benchmark evaluation against promoted ground truth. | Lead Methodologist | `results/benchmarks/` |

### 5.1 Token Isolation Invariants
- Possessing `AUTH-MEDIA-ACCESS (REVIEW)` grants **zero** permission to load model weights or promote ground truth.
- Possessing `AUTH-MODEL-CHECKPOINT` grants **zero** permission to view raw media (strict model-data firewall).
- Possessing `AUTH-PROMOTION` is restricted solely to the PI (`raihankabirrahu@gmail.com`).

### 5.2 Token Data Contract (`data/governance/AUTH-MEDIA-ACCESS.json`)
```json
{
  "schema_version": "phase5-media-access-authorization/2",
  "authorization_id": "AUTH-REV-20261103-001",
  "authorization_class": "AUTH-MEDIA-ACCESS",
  "authorization_tier": "REVIEW",
  "status": "APPROVED",
  "authorized_by": "raihankabirrahu@gmail.com",
  "authorized_at_utc": "2026-11-03T07:00:00Z",
  "expires_at_utc": "2026-11-03T19:00:00Z",
  "revoked": false,
  "scope": {
    "operations": ["READ_RAW_MEDIA", "MEDIA_PROBE"],
    "datasets": ["B4_DATASET"],
    "events": ["event_001", "event_002", "event_004", "event_005", "event_006"],
    "media_types": ["video"],
    "purpose": "HUMAN_GROUND_TRUTH_REVIEW"
  },
  "bindings": {
    "protocol_document": "docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md",
    "protocol_sha256": "3e9b...",
    "git_head_commit": "b372239378122758375bd40ec34a9786180670c6",
    "allowed_reviewers": ["rater_01", "rater_02"]
  },
  "security": {
    "nonce": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "composite_signature": null
  }
}
```

---

## 6. Threat Model & Security Analysis

### 6.1 Vulnerabilities in Unauthenticated Local JSON Nonce Ledgers
Missions 16E and 16F highlighted critical vulnerabilities in the historical token design:
1. **Unsigned Local File:** Any process running as the local OS user can write or modify `AUTH-MEDIA-ACCESS.json`.
2. **Replay Vulnerability:** Re-using an expired nonce across multiple sessions if nonce consumption is not atomically locked.
3. **Time-of-Check to Time-of-Use (TOCTOU):** A clean git tree at preflight does not prevent file modification while the CLI process is running.

### 6.2 Mitigations Designed for `human_review_session.py`
1. **Atomic Nonce Retirement:**
   - Nonces are recorded upon first open in an append-only consumed nonce ledger:
     `data/governance/.consumed_nonces.jsonl`
   - File locking (`fcntl.flock`) guarantees atomic check-and-retire. A replayed nonce immediately causes fail-closed session termination.
2. **Continuous Code Integrity Binding:**
   - The CLI hashes its own execution code (`Path(__file__).read_bytes()`) and all loaded safety modules on startup.
   - Any runtime tampering with `media_guard.py` or `promotion_gate.py` immediately aborts execution.
3. **Reviewer Identity Impersonation Protection:**
   - Reviewer handles are verified against `authorized_reviewers.json`.
   - All session ledger records are hash-chained: tampering with any previous record invalidates the entire session file.
4. **Failure-Closed Architecture:**
   - If any check fails (missing token, expired timestamp, dirty git tree, unknown reviewer, hash mismatch), the system refuses to initialize and logs a security audit event to `data/governance/security_audit.log`.

---

## 7. Proposed Module Interface Specification

The following class and function signatures define the API contract for `src/railway_detection/annotation/human_review_session.py`:

```python
"""Human review session runner specification (Do not modify without PI approval)."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class ReviewerRole(str, Enum):
    PRIMARY_RATER = "primary_rater"
    SECONDARY_RATER = "secondary_rater"
    PI_ADJUDICATOR = "pi_adjudicator"


class TrainDirection(str, Enum):
    TOWARDS = "towards_camera"
    AWAY = "away_from_camera"
    STATIONARY = "stationary"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ReviewObservation:
    record_id: str
    event_id: str
    session_id: str
    reviewer_id: str
    reviewer_role: ReviewerRole
    timestamp_utc: str
    train_direction: TrainDirection
    t0_entry_s: Optional[float]
    t0_censored: bool
    t1_warning_s: Optional[float]
    t2_island_entry_s: Optional[float]
    t3_island_mid_s: Optional[float]
    t4_island_exit_s: Optional[float]
    t4_censored: bool
    horn_sounded: bool
    horn_timestamp_s: Optional[float]
    weather_condition: str
    occlusions: list[str]
    confidence: str
    notes: str
    prev_record_hash: str
    record_hash: str


class HumanReviewSession:
    """Orchestrates human review workflow under strict authorization."""

    def __init__(
        self,
        repo_root: Path,
        reviewer_id: str,
        auth_token_path: Path,
        review_ledger_dir: Path,
    ) -> None: ...

    def preflight_check(self) -> dict[str, Any]:
        """Validate git working tree, auth token, and reviewer identity."""
        ...

    def list_pending_events(self) -> list[str]:
        """Return list of events requiring review by this rater."""
        ...

    def start_event_review(self, event_id: str) -> dict[str, Any]:
        """Verify media authorization and return event metadata."""
        ...

    def submit_observation(self, observation: ReviewObservation) -> Path:
        """Validate schema, hash-chain, and append to session ledger."""
        ...

    def close_session(self) -> dict[str, Any]:
        """Retire token nonce, record session audit trail, and exit cleanly."""
        ...
```

---

## 8. Comprehensive Synthetic Verification Plan

Before deploying `human_review_session.py` to human raters, it must pass a comprehensive synthetic-only test suite:

| Test ID | Test Name | Purpose / Setup | Expected Outcome | Failure Condition |
| :---: | :--- | :--- | :--- | :--- |
| **TEST-CLI-01** | `test_preflight_clean_repo` | Clean git repo, valid synthetic auth token, registered reviewer. | Preflight returns `OK: True`. | False rejection or exception. |
| **TEST-CLI-02** | `test_preflight_dirty_repo` | Modified file in working tree (`git status --porcelain != 0`). | Session halts with `WorkingTreeDirtyError`. | Session starts despite dirty repo. |
| **TEST-CLI-03** | `test_token_expiry_enforcement` | Auth token with `expires_at_utc` in the past. | Session halts with `TokenExpiredError`. | Token accepted after expiry. |
| **TEST-CLI-04** | `test_token_scope_firewall` | Auth token with `tier: "CHECKPOINT"` attempting media review. | Rejection with `InsufficientScopeError`. | Cross-tier token usage permitted. |
| **TEST-CLI-05** | `test_unregistered_reviewer` | Reviewer handle not in `authorized_reviewers.json`. | Halts with `ReviewerNotAuthorizedError`. | Unregistered reviewer allowed. |
| **TEST-CLI-06** | `test_ai_blinding_enforcement` | Inspect CLI state during first-pass review. | Zero model predictions or prior rater timestamps present in state. | Leakage of prior rater/model data. |
| **TEST-CLI-07** | `test_monotonicity_validation` | Submit invalid landmark timestamps ($T_2 < T_1$). | CLI rejects input; ledger remains untouched; prompt re-issued. | Invalid timestamp appended. |
| **TEST-CLI-08** | `test_ledger_hash_chaining` | Submit 3 observations; verify SHA-256 chain. | Record $N$ hash incorporates Record $N-1$ digest; verifiable tamper trail. | Hash chain broken or constant. |
| **TEST-CLI-09** | `test_nonce_replay_protection` | Attempt to run two sessions with same token nonce. | First session succeeds; second session fails with `NonceAlreadyConsumedError`. | Token replayed successfully. |
| **TEST-CLI-10** | `test_crash_recovery_resume` | Terminate process mid-session; restart with same session ID. | Session recovers previous uncommitted state without duplicating ledger rows. | Duplicate records or corrupted ledger. |

---

## 9. Statutory Acceptance Criteria

The technical specification of `human_review_session.py` is deemed complete and ready for PI consideration when:
1. No production code is modified in Mission 17B.
2. Synthetic tripwires in `adjudication_session.py` are fully preserved.
3. Blinding, non-destructive ledgering, and human-only promotion rules are strictly specified.
4. Granular four-tier authorization and threat mitigations are rigorously documented.
5. All 10 synthetic test specifications have clear pass/fail definitions.

---
*End of Mission 17B Deliverable 1.*

---

## Mission 17C-0 correction history — superseding technical requirements

**2026-11-03; documentation correction only; NOT APPROVED FOR IMPLEMENTATION OR EXECUTION.** Original §§1–9 above are retained as historical specification wording. This appendix supersedes their conflicting claims, pseudocode contracts and test expectations. Evidence and original claims: `MISSION_17C0_VERIFICATION_MATRIX.md` C007–C028, F01–F03/F21/F22. No authorization token is issued by any example above.

### Correct repository integration and authority

- `adjudication_session.py` is a synthetic session API, not an implemented interactive console CLI. Preserve its synthetic/temp safeguards. Proposed human module location is `src/railway_detection/annotation/human_review_session.py`; no such production implementation exists at this audit baseline. 17A's alternative `review/` path was not implemented.
- Actual allowlist: `data/ground_truth/authorized_reviewers.json`. It currently lists one identity. Membership is neither login authentication nor proof of credentials/independence. Reviewer appointment, qualification and authentication mechanisms remain researcher decisions; example handles are not appointed reviewers.
- Existing media operations are `READ_RAW_MEDIA`, `HASH_RAW_MEDIA`, `MEDIA_PROBE` and the other enumerated operations in `media_guard.py`. `REVIEW_RAW_MEDIA` is invalid. If review verifies live media hashes, a read/probe-only grant is insufficient: hashing must also be explicitly authorized. A promotion authorization does not itself permit raw hashing.
- Four conceptual capability classes are proposed, not implemented schemas. Existing media `/2` bindings contain exactly `protocol_document: {path, sha256}`. The example in §5.2 is **invalid against the active schema**: extra tier/security fields, missing required attestation/record/restriction fields, bare event IDs and incorrect binding shape. Do not copy it into governance or repair it into an approval. A future incompatible contract needs a distinct version, validator migration and researcher approval.
- The example's12-hour lease also conflicts with 17A's proposed maximum 4-hour lease; neither is an adopted lifetime policy. Its fixed empty-string-hash nonce is illustrative, not a generated one-use capability. Any approved nonce design needs specified entropy, uniqueness and lifecycle, not reuse of a constant.
- Checkpoint access, protected feature-cache reads/replay, split generation, human review, promotion and evaluation need explicit operation/resource/purpose/actor mappings. A token for one class must never substitute for another; granting a model read does not grant data, cache or evaluation access. Current EVAL-AUTH is an unsigned recorded statement with seven live artifact bindings; cryptographic signatures and the proposed new token classes do not exist.
- Existing `promotion_gate.py` validates one Stage-2.1 record plus caller-supplied state and live media hashes. It does not verify JSONL hash chains, a PI-signed AUTH-PROMOTION, or universal two-review coverage. Its current write uses event_id.json and can overwrite; new ledger data must stay non-promotable until a versioned adapter and create-only, cohort-qualified publication boundary are approved and implemented.

### Physical meaning, schema and blind first pass

- T1 means leading end reaches the documented approach frog/pedestrian line; T2 means leading end crosses physical roadway entry, whose landmark remains DEFERRED (RD-005/006). Do not require an observed T2 or invent an island plane. T3 is the trailing coupler/rear of the lead locomotive clearing the departure exit boundary; T4 is the final vehicle tail clearing that boundary. T3 is not nose passage or island midpoint.
- Record cohort-qualified physical identity, stream/camera and clock ID for every observation. The same bare `event_001` occurs in three cohorts. Keep raw camera-local times immutable. Global T0≤…≤T4 validation is invalid across unsynchronized camera clocks; compare only applicable observable finite values on a common documented clock. Censored/uncertain/not-applicable/landmark-undefined states require explicit typed representation and rationale, not only booleans/nulls.
- Preserve frame index and presentation timestamp/timebase; frame_idx/fps is only valid where constant frame rate and origin are established. Millisecond display precision does not establish millisecond accuracy. No “certified media player” or timing accuracy is evidenced; player/wrapper and seek/frame behavior need prospective synthetic verification and approval.
- The §7 dataclass is an incomplete concept, not a compatible Stage-2.1 schema. Specify the protocol/schema version, safe event/media identity binding, per-boundary reference camera/clock, PTS/frame, censor direction/state/rationale, reviewer identity/attestation, start/end/duration, and immutable observation/adjudication links. Gate-operation fields requested in §3.4 need a corresponding approved schema if retained. Horn fields apply only if acoustic reporting is approved; visual-only approval cannot silently authorize audio. Weather/lighting are separate metadata, with unknown allowed and provenance recorded.
- First-pass process receives only an approved neutral event queue, required raw resource handles and neutral geometry metadata. It must not load AI predictions/proposals, prior reviewer observations or model-derived timestamps into UI/process state, logs, overlays or exception output. Candidate comparison and adjudication occur only after first-pass observation submission, with an explicit phase transition. Shared OS account or unrestricted external player/file access cannot enforce global blinding; disclose and govern that boundary.
- §1's cited RD042/043/045 directions do not themselves establish a blanket prohibition on all offline AI candidates: the current protocol describes offline proposals that never become GT without human verification. This audit authorizes no candidate generation or raw-media AI access. Human-only authoritative judgments, first-pass blinding and separate applicable authorization remain mandatory.
- RD-043 is risk-based mandatory second review, not a universal two-review mandate. Preserve all documented triggers, including human-flagged front/back conflicts. Universal dual review of all 27 is a proposed policy requiring explicit PI adoption and a second appointed reviewer. RD-046 keeps the existing 30 s software plausibility floor; it is not scientifically calibrated review sufficiency or authorization for a five-event session cap.
- Five-event pilot and numerical rater-spread ranges are unvalidated proposals. Hard-case selection, scope, blinding, timing capture, consent/roles where applicable, stop rules and tolerance-analysis method need researcher approval before any pilot. No scientific tolerance is set here. Different camera fps does not itself invalidate a tolerance expressed in seconds; it invalidates assuming a fixed frame equivalence and does not supply calibration evidence.
- Preserve RD-045: originals remain immutable; corrections and adjudications append separately and reference exact original hashes. Unresolved remains UNCERTAIN. Prohibit automatic averaging as the basis for resolution; an independently observed timestamp may coincidentally equal an arithmetic midpoint, so §4.2's numeric inequality is withdrawn. Keep raw observations distinct from the resolved decision.

### Durability, authentication, nonce lifecycle and point-of-use checks

- A local hash chain detects alteration only against a trusted anchor. A writer can recompute it, replace genesis or truncate a suffix. Define canonical UTF-8 serialization, stable session/record IDs, strict sequence numbers, previous/current digest calculation, explicit genesis and externally protected committed tail/length. Hashes do not authenticate reviewers.
- Use create-only per-session files and one serialized writer per ledger; lock the entire read-head/validate/append/flush transaction, not just the append. Acknowledgement follows durable write (file fsync and directory durability for new files). Define idempotent submission IDs, crash recovery, torn-tail quarantine/recovery records, and refusal of mid-file corruption, duplicates or rollback. Never silently truncate acknowledged history. Promotion must verify source anchors and all correction/adjudication links, including the retained original observations.
- Nonce lifecycle must be one durable atomic reservation before the first protected operation, followed by ACTIVE and COMPLETED/ABORTED state. Close records completion, not first consumption. Expired, revoked and previously consumed authorizations are denied. Resume must authenticate the same actor, session, approved bindings and ledger tail, recheck expiry/revocation, and never grant a second concurrent process. A different session cannot reuse the nonce. The crash-resume oracle must not bypass one-use semantics.
- `fcntl.flock` coordinates cooperating processes on a specified ledger inode/filesystem. It does not stop same-user rewrites, unlink/replacement, ledger rollback or a process ignoring the lock. Trust/rollback protection needs an independently protected authority or an explicitly accepted limitation. No such protection is claimed implemented.
- Clean `git status`, HEAD and index tree are preflight evidence only. They do not authenticate ignored modules, external dependencies, current loaded bytecode or post-check changes. Hashing whatever is present at startup is not verification against an approved expected digest. A composite digest is not a signature. Media guard currently binds protocol bytes, not HEAD.
- Future execution must specify approved code/config/dependency digests, trusted validator and authority origin, protected immutable execution inputs, and revalidation immediately before every protected read/write/promotion. Scope, expiry, revocation and identity must be checked on use. Disk-file checks alone do not verify running code and cannot promise immediate detection or malicious-local-user resistance. Python guards are not OS-level isolation.
- Extend the ten proposed synthetic checks to cover wrong schema/cohort/purpose, hash-only versus read-only scope, forged handles, proposal/log leakage, symlink/file replacement, simultaneous nonce races, crash-before/after-durable-ack, resume after expiry/revocation, chain rewrite/tail truncation and duplicate correction/adjudication links. None of the proposed ten CLI tests is claimed executed by 17C-0.
