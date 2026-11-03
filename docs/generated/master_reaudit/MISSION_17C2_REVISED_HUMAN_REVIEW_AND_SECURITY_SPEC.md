# Mission 17C-2 — Revised human review and security specification

Date: 2026-11-03. Repository: `/Users/sayemuddin/Desktop/Train_automation`. Baseline: `d4353ad9d49d427a129a9a4e83023fbd24e1a111` on `main`.

**PROPOSED SPECIFICATION — RESEARCHER REVIEW PENDING — NO IMPLEMENTATION OR REAL-DATA AUTHORIZATION.** Every future rule, interface, algorithm, transition and test in a section marked PROPOSED is proposed behavior, not implemented functionality or an adopted decision. VERIFIED facts below describe inspected source/text or exact document arithmetic only. PARTIALLY VERIFIED means support is conditional; CONTRADICTED means source/counterexample disagrees; UNSUPPORTED means evidence does not justify a claim; NOT VERIFIABLE means required evidence is unavailable or prohibited. NOT VERIFIED explicitly flags an unestablished fact without inventing a sixth claim classification.

Companion documents: [Human review/security](MISSION_17C2_REVISED_HUMAN_REVIEW_AND_SECURITY_SPEC.md) · [Simulation](MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md) · [Grouped CV](MISSION_17C2_REVISED_GROUPED_CV_SPLIT_SPEC.md) · [Decision/traceability register](MISSION_17C2_INTEGRATED_DECISION_AND_TRACEABILITY_REGISTER.md) · [Acceptance audit](MISSION_17C2_CROSS_DOCUMENT_ACCEPTANCE_AUDIT.md).

Historical 17B and C1 files are preserved unchanged. This document consolidates a candidate acceptance contract; it does not silently replace a historical record, adopt a protocol, approve Option C, appoint a person, issue/consume a token or authorize a next mission. R01–R08 and T01–T04 remain PENDING; X00–X07 remain NOT AUTHORIZED, with C1 qualifications preserved in the register.

Mission boundary: no raw-media inspection/preview/playback/decode/hash; no checkpoint or protected-cache access; no real inference/training/replay/evaluation/calibration/split generation; no annotation/adjudication/promotion; no source/test/config/protocol/governance edits. Only the five named documents and safe temporary documentation-validation scripts are created. Planned feature tests are not passing test results.

<a id="h1"></a>

## H1. VERIFIED source baseline and limits

| Scoped factual finding | Status | Exact evidence / qualification |
|---|---|---|
| `src/railway_detection/annotation/human_review_session.py` is a PROPOSED target, absent at this baseline | VERIFIED | Existence check in this mission; historical target is explicitly specification-only: `docs/generated/master_reaudit/MISSION_17B_HUMAN_REVIEW_CLI_TECHNICAL_SPEC.md:5-7`. Absence does not invalidate an alternative proposed namespace. |
| The existing adjudication component is a synthetic session API, with synthetic-ID and resolved temporary-path guards | VERIFIED | `src/railway_detection/annotation/adjudication_session.py:126-142`; `src/railway_detection/annotation/adjudication_session.py:231-249`. Preserve every guard; no human workflow is obtained by weakening it. |
| Media schema /2 checks enumerated operations, exact keys, recorded unsigned attestation, expiration/revocation fields and protocol bytes | VERIFIED | `src/railway_detection/safety/media_guard.py:72-77`; `src/railway_detection/safety/media_guard.py:113-151`; `src/railway_detection/safety/media_guard.py:389-456`; `src/railway_detection/safety/media_guard.py:530-546`. REVIEW_RAW_MEDIA is not an operation. The old 17B token example is incompatible with this schema. |
| Media guard is a Python call-site guard, not an OS sandbox or authenticated-signature service | VERIFIED | `src/railway_detection/safety/media_guard.py:48-54`. It does not bind HEAD or guarantee loaded-code integrity. |
| Reviewer allowlist membership is string validation; media issuer membership uses the same list | VERIFIED | `src/railway_detection/annotation/promotion_gate.py:66-140`; `src/railway_detection/safety/media_guard.py:449-456`. Rater onboarding must not implicitly confer issuer power; role separation is a proposed change, not present infrastructure. |
| Current evaluation authorization has seven artifact bindings and refuses signature-style attestations | VERIFIED | `src/railway_detection/evaluation/governance.py:52-76`; `src/railway_detection/evaluation/governance.py:424-501`. Its current record contract is distinct from a proposed expiring session grant. |
| Current promoter validates one Stage-2.1 record and caller-supplied state, live-hashes media, then writes a bare event_id filename | VERIFIED | `src/railway_detection/annotation/promotion_gate.py:253-310`; `src/railway_detection/annotation/promotion_gate.py:540-567`. It does not supply the proposed chain/role/batch-authorization boundary; overwrite/cohort collision is possible with a shared output directory. No promotion or raw hash is executed here. |
| Active8.1 schema is different from inactive8.2 proposal | VERIFIED | `src/railway_detection/annotation/stage2_1_schema.py:33-50`; `src/railway_detection/annotation/stage2_1_schema.py:279-350`; `src/railway_detection/annotation/stage2_1_schema_proposed.py:1-20`; `src/railway_detection/annotation/stage2_1_schema_proposed.py:33-60`. New ledger fields cannot be relabeled as active records. |
| v7.1.1 is proposed and its examples are explicitly mock | VERIFIED | `docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md:3-10`; `docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md:302-310`; `docs/generated/master_reaudit/MISSION_17C1_CORRECTION_COMPLETENESS_AUDIT.md:45-60`. Mock examples alone do not establish a protocol defect. |
| Full technical promotion readiness is established | UNSUPPORTED | `docs/generated/master_reaudit/MISSION_17C1_CORRECTION_COMPLETENESS_AUDIT.md:45-60`. Compatibility/acceptance evidence is incomplete; this does not itself prove technical incompatibility. |
| An applicable formal protocol adoption approval is established by the available record | NOT VERIFIABLE | `docs/generated/master_reaudit/MISSION_17C1_INDEPENDENT_CHALLENGE_OF_17C0.md:99-105`. Missing repository evidence is not proof that no external approval exists. |

<a id="h2"></a>

## H2. PROPOSED actor responsibilities and separation of duties

Actor means a verified human principal, not a typed handle. The role registry, identity provider, enrollment evidence, independence/conflict declarations, issuer trust, multi-role policy and revocation mechanism are NOT VERIFIED; R05/T01 must select them. No actual identities, keys or credentials appear in this specification. Existing RD-042 keeps the allowlist unchanged pending an appointable reviewer (`docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:49-52`). A technical administrator may not approve their own role elevation.

| Role (PROPOSED) | Permitted responsibility only after appointment and scoped authorization | Separation / conflict rule | Evidence required before use |
|---|---|---|---|
| Human reviewer | Make and attest a blind first-pass observation; append a separately linked correction | Cannot perform their own independent second review, issue grants or promote merely by being a reviewer | Researcher appointment, authenticated stable principal, qualification, session/resource scope, conflict declaration |
| Independent second reviewer | Make an independent sealed observation for a triggered/audit case | Must be a different verified human from the first reviewer; aliases or a shared account do not establish independence; cannot read first-pass judgments before sealing their own | Independent appointment/qualification, conflict check, recorded trigger/assignment and separate session evidence |
| Adjudicator | Researcher, or human explicitly permitted by researcher role policy, records a separate evidence-based resolution | Self-adjudication/overlapping roles are blocked until R05 explicitly defines allowed combinations and recusal; no overwrite, averaging-as-evidence or forced agreement | Appointment/delegation, conflicts/recusal, exact source hashes, rationale, applicable media permissions |
| Promotion operator | Human submits an eligible batch and initiates only the authorized deterministic publication operation | Review/adjudication status never grants promotion; batch approval must come from an explicitly authorized issuer under the adopted role policy | X03 batch authority, role, adapter/policy verification, source anchors; separate live-hash permission if needed |
| Authorization issuer | Create/authenticate narrowly scoped grants after administrative approval | A rater is not automatically an issuer; allowed multiple roles require explicit R05 policy and auditable independent approval of elevation | Researcher appointment, protected issuer trust/enrollment, delegation limits and revocation evidence |
| Technical administrator | Maintain the approved tooling/authority deployment within an authorized change scope | Administration is not scientific approval, reviewer appointment, GT authorship or data access; privileged access remains a separate threat | Bounded change authorization, access/audit controls and explicit trust model |

PROPOSED: one human may hold multiple roles only under an explicit researcher-approved role policy, with case-specific conflicts/recusal recorded. No multi-role permission exists here. AI may not generate/edit observations, adjudicate disagreements, approve or initiate promotion of human GT. Deterministic validation/storage may mechanically execute a future authorized human submission; it may not invent judgments, attestations or authority. No candidate generation or raw-media AI access is enabled by a discussion of offline candidates.

<a id="h3"></a>

## H3. PROPOSED observation contract and blind phases

Use these exact terms across the five specifications. Session states describe resource access; record sealing describes evidence preservation; review statuses describe case handling. None means researcher approval or promotion.

| Dimension (PROPOSED) | Vocabulary / invariant |
|---|---|
| Session state | RESERVED, ACTIVE, RECOVERY_REQUIRED, COMPLETED, ABORTED (H6) |
| Observation preservation | DRAFT is editable private working input; SEALED is an immutable original record. A correction is a new SEALED record referencing its predecessor, never a rewritten original. |
| Review status | SUBMITTED, NEEDS_SECOND_REVIEW, DISPUTED, ADJUDICATED_UNCERTAIN, ADJUDICATED_RESOLVED; DRAFT belongs only to pre-submission work. No APPROVED/PROMOTED status is produced by the review workflow. |
| Boundary state | OBSERVABLE, CENSORED, UNCERTAIN, NOT_OBSERVABLE; the latter requires not_applicable_for_cohort, not_visible_in_recording or landmark_not_defined. |
| Censor direction | LEFT or RIGHT required iff CENSORED; no invented point timestamp for a censored boundary. |
| Evidence status | PRESENT, MISSING, INSUFFICIENT. OBSERVABLE requires PRESENT and a supported timestamp/camera/clock. |
| Batch eligibility | Derived ELIGIBLE or INELIGIBLE with reasons; not approval, execution authority or a rewrite of a review status. An UNCERTAIN result cannot become a point estimate merely to satisfy a gate. |

The proposed boundary/review vocabulary follows the recorded inactive schema proposal (`docs/generated/mission_5a/STAGE21_SCHEMA_AND_REVIEW_GOVERNANCE_PROPOSAL_20261101_M5A.md:8-21`; `src/railway_detection/annotation/stage2_1_schema_proposed.py:33-60`; `src/railway_detection/annotation/stage2_1_schema_proposed.py:96-149`). SEALED/session/eligibility dimensions are C2 PROPOSED storage/workflow concepts, not existing schema fields. Active8.1 instead uses UNOBSERVABLE_NOT_APPLICABLE and its own adjudication statuses (`src/railway_detection/annotation/stage2_1_schema.py:65-79`); no silent field/state coercion is permitted.

<a id="h3-1"></a>

### H3.1. PROPOSED field and validation contract

| Record family / required fields (PROPOSED) | Type / validation / rationale |
|---|---|
| Envelope | Distinct schema/version; nonempty record_id/session_id; positive sequence; record_kind; actor principal/role reference; detached attestation in the envelope; event key with dataset/version/cohort/physical-event identity; exact protocol/schema references/digests; policy version; operation_id; prior/current digests; UTC submission and authentication-attestation references. IDs never stand in for a verified person. |
| Resource provenance | Per actually inspected stream: media identity, expected authorized metadata digest, independently verified live observation receipt when authorized, camera_id and clock_id. No guessed media hash or inferred front/back identity. First-pass queue carries only neutral required metadata. |
| Boundary payload | Boundary name, state, nonempty human rationale, evidence_status, and preserved raw_entry_text; OBSERVABLE has canonical nonnegative finite decimal-seconds string value_s_decimal on the named local clock. Other states have null point value. Optional censor bound is a separate bound field with direction/origin, never a point estimate. |
| Frame/timebase | frame_index is a nonnegative integer when established; PTS ticks and positive rational timebase appear together if known; frame-to-PTS/origin mapping must be evidenced. If unavailable, mark NOT VERIFIED with a reason and restrict accuracy/promotion claims. frame_index/fps is not substituted without verified CFR/origin. |
| Uncertainty/direction | Nullable nonnegative decimal uncertainty with measurement provenance, no default tolerance. Per-event direction is a human observation with its own state/evidence/reference camera; vocabulary/geometry mapping needs R01/R05, never copying candidates or inventing environmental labels. |
| Session timing | Timezone-aware UTC start/end plus monotonic elapsed inspection record; clock anomalies preserved. Current30s schema plausibility floor is not scientific sufficiency and cannot be replaced here by a new session cap or accuracy rule. |
| Correction | New record identifies original record_id/digest, correction reason and actual human actor; a selected latest-effective view keeps the entire correction lineage. No delete, in-place edit or stale-head correction. |
| Second review / disagreement | Links exact sealed primary and independent secondary digests, trigger policy/version and per-boundary state/clock/value differences. Comparison logs never feed an unsealed first pass. |
| Adjudication | Separate adjudicator attestation, original/correction/second-review hashes, per-boundary resolution/rationale and supporting frame/clock provenance; unresolved stays UNCERTAIN. Candidate adjudication resolution states are OBSERVABLE with evidenced value or UNCERTAIN, matching the inactive proposal; any extension to newly adjudicated censored/not-observable states needs R01 schema review rather than implicit coercion. Uncontested original typed censor/deferred states remain preserved. Numeric midpoint equality is allowed only when independently observed evidence supports the chosen frame; automatic averaging is not evidence. |
| Optional gate/horn/environment fields | A versioned, researcher-selected extension with the same provenance/type rules. Horn/audio needs explicit acoustic scope. T2/full occupancy and scientific tolerance remain deferred; no required guessed landmark or default weather/lighting/direction. |

PROPOSED temporal validation compares only observable values on the same established clock and applicable physical order; no global T0≤…≤T4 across cameras. T1 is the approach frog/pedestrian reference; T2 physical roadway entry remains deferred; T3 is the rear/trailing coupler of the lead locomotive clearing the departure boundary; T4 is the final vehicle tail clearing it. Offsets never edit human local timestamps. Sources for those recorded meanings: `docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md:106-114`; `docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md:176-185`; `docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:11-14`; `docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:34-35`. An unestablished entry landmark is NOT_OBSERVABLE/landmark_not_defined, not a model-derived T2.

<a id="h3-2"></a>

### H3.2. PROPOSED first-pass data boundary

The first-pass process receives an approved neutral queue, authorized resource handles and neutral geometry. Candidate files, predictions, earlier reviews, model-derived queue ordering, revealing filenames/overlays, logs and error messages are excluded. First and second reviewers each seal their own independent pass before comparison. A separate post-seal comparison/adjudication phase receives the authorized candidate/prior-observation references. Human disclosures record prior exposure. A shared unrestricted OS account/external player cannot establish global blinding; T01 must state the deployment limit. Timing/player precision is NOT VERIFIED pending synthetic seek/PTS tests and R05/R08 acceptance. Recorded blinding direction: `docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:20`; `docs/generated/mission_5a/STAGE21_SCHEMA_AND_REVIEW_GOVERNANCE_PROPOSAL_20261101_M5A.md:27-31`.

<a id="h4"></a>

## H4. PROPOSED observation-to-batch lifecycle

| Step (PROPOSED) | Preconditions | Transition / durable evidence | Rejection / unresolved behavior |
|---|---|---|---|
| 1. Open session | Authenticated appointed human, correct role/scope/current bindings; H6 reservation | RESERVED→ACTIVE with exclusive owner/fence; neutral event assignment | No actual grant exists here; failure denies every protected operation. |
| 2. Record observation | ACTIVE, fresh operation check, independent phase | Private DRAFT human entry; validate H3 fields/local clocks | Invalid draft is rejected without a SEALED record; no automatic timestamp repair. |
| 3. Seal original | Human explicitly submits, validated content, current session fence/head | DRAFT→SEALED, case SUBMITTED; H7 transaction; acknowledgment only after protected commit | Preserve original forever by policy; later correction appends. Crash cannot silently replace or drop acknowledged content. |
| 4. Assess required second review | Sealed first pass, complete adopted trigger inputs and policy | Triggered→NEEDS_SECOND_REVIEW; independently assigned human seals own record. No-trigger finding retains reason/policy evidence. | A missing reviewer, missing trigger input or unknown mandatory trigger is a blocker, not a “no trigger.” Universal review is not inferred. |
| 5. Record differences | Two independent sealed entries, same event/clock mapping | Agreement receipt or DISPUTED case with explicit differences | Censored/state/camera differences are not averaged. No adopted scientific tolerance is available. |
| 6. Adjudicate separately | Permitted human/recusal, exact source links and authorized re-inspection if needed | New adjudication record; ADJUDICATED_RESOLVED or ADJUDICATED_UNCERTAIN | Unresolved remains UNCERTAIN; never rewrite original observations or create consensus to pass a gate. |
| 7. Assess eligible batch | Every required review/adjudication covered, sources/anchors valid, compatible schema and metric-specific state rules | ELIGIBLE or INELIGIBLE receipt with per-record reasons and exact manifest digest | UNCERTAIN may be retained/reported only under an adopted profile; no fabricated point value or outcome-dependent global exclusion. |
| 8. Submit promotion request | ELIGIBLE assessment and separately approved human batch request | Human promotion operator requests X03-bound publication; H8 adapter/write checks | Eligibility is not X03. No promotion occurs from this document, a review grant or an AI action. |

RD-045 preservation and unresolved-state direction is recorded, not new approval (`docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:52`; `docs/generated/mission_5a/STAGE21_SCHEMA_AND_REVIEW_GOVERNANCE_PROPOSAL_20261101_M5A.md:17-18`). The current second-review module cannot clear disagreement through an adopted adjudication format (`src/railway_detection/annotation/second_review.py:24-28`). A new adapter/write workflow is therefore PROPOSED and unavailable, not a claimed current feature.

<a id="h4-1"></a>

### H4.1. PROPOSED risk-trigger contract, preserving RD-043

VERIFIED: source applies a named trigger proposal conservatively while explicitly saying researcher adoption is pending (`src/railway_detection/annotation/second_review.py:6-28`; `docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:50-51`). PROPOSED: preserve the six trigger categories for R05 review: explicit flag; any UNCERTAIN boundary; engine T3/T4 interpretation; human front/back conflict flag; missing/inconsistent media hashes; corrected/unverifiable candidate binding. CENSORED or NOT_OBSERVABLE alone is not a trigger. No fixed audit percentage or universal dual-review mandate is adopted.

PROPOSED: front/back conflict must be a structured human flag in the new ledger. Candidate comparison runs only after independent sealing; absence of candidate authorization/input is recorded as NOT VERIFIED and blocks declaring that trigger evaluated. Integrity/hash mismatch also blocks promotion; obtaining a second signature cannot cure a mismatched resource. Until a scientific tolerance is adopted, comparison reports exact typed differences and the current one-microsecond comparator only as a software rule, never a calibrated agreement threshold. Agreement satisfies a second-review precondition, not researcher adjudication/approval. Exact current trigger/independence behavior: `src/railway_detection/annotation/second_review.py:170-216`; `src/railway_detection/annotation/second_review.py:271-328`.

<a id="h5"></a>

## H5. PROPOSED threat model and guarantee boundaries

Threat classes: COOPERATIVE_PROCESS follows the APIs/locks but may race/crash; MALICIOUS_SAME_USER can edit/replace local files and use alternate local opens; PRIVILEGED_ADMIN can alter host execution/storage; EXTERNAL_AUTHORITY_COMPROMISE can corrupt the issuer/anchor service. No single profile defeats all four.

| Property / asset | Actor capability | Current source behavior (VERIFIED) | PROPOSED control | Residual risk / required verification |
|---|---|---|---|---|
| Authentication / human session | Impersonated handle or shared account | String allowlist, not human login (`src/railway_detection/annotation/promotion_gate.py:66-140`) | Researcher-verified enrollment plus authenticated human/session attestation; no invented mechanism/keys | Identity provider/qualification/independence NOT VERIFIED; H-T01/H-T02 and R05 evidence required. |
| Authorization / resources and roles | Rater attempts issuer/promotion authority | Shared issuer/reviewer list (`src/railway_detection/safety/media_guard.py:449-456`) | Role-specific issuer registry, explicit delegated capabilities, per-operation scope | Multi-role/escalation policy PENDING; H-T03/H-T04 must reject rater-as-issuer without role evidence. |
| Integrity / approved execution bytes | Same-user edits after preflight | Protocol bytes only; Python limitations (`src/railway_detection/safety/media_guard.py:48-54`; `src/railway_detection/safety/media_guard.py:530-546`) | Trusted expected code/config/dependency digests and protected immutable execution inputs | Disk hashes do not authenticate loaded objects; admin can change runtime. H-T05; no “immediate tamper detection” guarantee. |
| Authenticity / grant and observation origin | Local writer recomputes digests | Unsigned recorded statements (`src/railway_detection/evaluation/governance.py:487-501`) | Independently protected issuer/actor attestations selected by T01 | Hash≠signature; cryptographic enrollment/keys NOT VERIFIABLE here. H-T06; no authenticity claim without a trusted mechanism. |
| Revocation / active grants and roles | Uses a cached positive preflight | Current media revoked/expiry fields (`src/railway_detection/safety/media_guard.py:404-447`) | Authoritative fresh check at each operation start, scope/role/binding validation and stop on lost authority | Long-lived handles need revocation-aware broker/leases; cannot claw back already read bytes. H-T07. |
| Replay / grant reservation | Copies a token or rolls back consumed history | Proposed17B local ledger, not implemented authority (`docs/generated/master_reaudit/MISSION_17B_HUMAN_REVIEW_CLI_TECHNICAL_SPEC.md:230-241`) | One durable grant→session reservation; same-session recovery with new fence; external monotonic state | Same-user rollback defeats unprotected local state. H-T08/H-T09. |
| Concurrency / session and append head | Two cooperating workers reserve/append simultaneously | No claimed current session implementation; flock proposed (`docs/generated/master_reaudit/MISSION_17B_HUMAN_REVIEW_CLI_TECHNICAL_SPEC.md:230-233`) | Full stable-inode local transaction plus authoritative compare-and-set and fencing | Lock replacement/ignoring lock remains possible locally; H-T09/H-T10 require single winner and stale-owner refusal. |
| Point of use / protected open or write | Alternate call path or source changes after check | Per-file cooperating API plus disclosed bypass limits (`src/railway_detection/safety/media_guard.py:549-564`; `src/railway_detection/safety/media_guard.py:48-54`) | Trusted broker verifies current actor/operation/resource and opens approved object under protected execution | Unwrapped direct access is not prevented by Python; H-T05/H-T11; broker/host deployment NOT VERIFIED. |
| OS isolation / raw bytes and keys | Malicious same-user or privileged admin | Explicitly not an OS sandbox (`src/railway_detection/safety/media_guard.py:48-54`) | Separate account/service/storage boundary if T01 requires that threat resistance | Privileged admin/external-authority compromise remains outside this local guarantee; deployment/incident tests H-T11/H-T12. |
| Administrative approval / scientific scope | Forged memo or draft treated as permit | Canonical evaluation artifact required; documents/chat are insufficient (`src/railway_detection/evaluation/governance.py:424-427`) | Verify genuine applicable approval reference, adopted role policy and separate operation authorization | External approvals unavailable here remain NOT VERIFIABLE, not disproved. H-T13 and R/T/X record review. |

PROPOSED deployment alternatives, both still T01 PENDING: a cooperative local prototype can test state/race logic but cannot certify malicious-local-user rollback resistance, global blinding, identity authenticity or OS isolation; a protected-authority/broker deployment may claim only the resistance its independent boundary and verification actually support. Privileged administrator and authority compromise require separate administration, audit replication/recovery and explicit accepted residual risk. No host hardening, keys or service is implemented here.

<a id="h6"></a>

## H6. PROPOSED grant and session lifecycle

<a id="h6-1"></a>

### H6.1. PROPOSED semantics: single-use per session

PROPOSED grant contract: required grant_id and unique nonce; contract_version; authenticated issuer reference; bound human principal and allowed role references; purpose plus explicit operation/resource sets; protocol/code/config/dependency/policy bindings; not_before_utc and expires_at_utc; adopted lease/nonce-policy reference. Canonical UTC timestamps must satisfy not_before < expires; the trusted authority permits use only when not_before ≤ authority_now < expires and current revocation/role checks pass. Local wall-clock rollback cannot replace authority time; unavailable/untrusted authority time denies use. Nonce uniqueness is enforced by authoritative allocation; entropy/lease parameters remain T01 policy choices, not generated values. Possession alone is not authority: the authenticated principal and role must match.

A grant is consumed **once to reserve one session**, not once per media frame/operation. Repeated permitted operations inside that same active session do not reconsume it. A different session can never reuse its grant_id/nonce. Closing or aborting does not reset consumption. Recovery retains the same session_id and reservation; it is not a new grant or a second session. Per-operation authority/idempotency checks remain mandatory. Current /2 records do not implement this conceptual contract; an incompatible future schema needs R01/R05/T01 review and an explicit version/migration decision.

| Stage (PROPOSED) | Authoritative transition / operation | Required checks / rejection |
|---|---|---|
| Grant creation | Issuer prepares DRAFT; only genuine approved scope/role references can yield an ISSUED grant | Explicit actor/purpose/operation/resource sets, protocol/code/config/policy bindings, expiry, nonce uniqueness/entropy policy. No real values/grant exist here; lifetime/entropy values are NOT VERIFIED pending T01. |
| Grant authentication | Verify approved issuer/attestation and exact canonical content before trusting scope | Reject altered, unverifiable, unknown-version/issuer records; a current local self-hash is not authentication. |
| Reservation | Atomic compare-and-set from unreserved grant to one RESERVED session, exclusive owner and monotonic fence | Bind human principal/session/bindings; commit durable authority state before first protected access. Two contenders cannot both succeed. |
| Activation | RESERVED→ACTIVE after session/ledger anchor initialization | Recheck role/scope/expiry/revocation; owner lease/fence valid; an abandoned reservation cannot be transferred into a different session. |
| Each operation | ACTIVE stays ACTIVE; operation_id and exact request digest recorded | Check actor, required role, operation/resource/purpose, grant/session/fence, validity/expiry, current revocation and approved bindings immediately before use. Deny unknown authority state; no startup-only cache of permission. |
| Reuse request | Same ACTIVE session may issue an allowed new operation; a retry with same operation_id must have identical content | A new session is denied even if the grant is otherwise valid. Same operation_id with changed content is rejected. A receipt retry never repeats an irreversible side effect. |
| Revocation/expiration | Grant becomes unusable; ACTIVE/RESERVED session cannot perform further protected operations | Stop/invalidate broker handles and deny new operations. Preserve history. Already read bytes cannot be revoked; check-before-start does not promise cancellation of all in-flight IO without a selected broker contract. |
| Normal closure | ACTIVE→COMPLETED after durable final head/count/session outcome receipt | Reservation remains consumed. No new protected operation. Close records completion, not first consumption. |
| Abort | RESERVED/ACTIVE/RECOVERY_REQUIRED→ABORTED with durable reason and final known head | Consumed reservation stays consumed; partial/unresolved work remains preserved and non-promotable. |
| Crash | Lost owner/lease→RECOVERY_REQUIRED, never automatically unreserved | Authority fences old owner. New process may recover only the same principal/session/bindings, with a fresh exclusive fence and still-valid grant/roles. |
| Recovery | RECOVERY_REQUIRED→ACTIVE only after H7 reconciliation; otherwise ABORTED/quarantined | Expired/revoked grant cannot resume. Never silently replay a protected external side effect of unknown outcome; require its idempotent receipt or quarantine. |
| Audit | Separately permitted read-only verifier checks committed authority state and retained ledgers/receipts | Audit permission is not review or promotion. No new session is created by reading an audit receipt. |

PROPOSED trusted authority interface: authenticate_grant; reserve_once(grant,session,principal); acquire_or_recover_owner(session,expected_fence); check_operation(request,fence,current_policy); commit_record(expected_head,count,record_digest,operation_id); revoke; finalize; read_committed_anchor. State must be durable, monotonically versioned and outside the attacker's declared write capability for rollback resistance. These are interface obligations, not existing functions. Authority failure denies protected operations. A compromise of this authority invalidates its authenticity/rollback guarantees until an approved external recovery checkpoint is established; the client cannot repair that trust by recomputing hashes.

<a id="h7"></a>

## H7. PROPOSED ledger serialization, commit, recovery and audit

PROPOSED canonical record encoding: UTF-8 JSON, no BOM/whitespace/final newline in the hashed body; lexicographically sorted ASCII field names; integers/booleans/null/strings/arrays/objects only, no JSON floating numbers or NaN/infinity. Object field names and identity keys are printable ASCII. Human text values may contain any Unicode scalar value; reject unpaired surrogates. Preserve text exactly with no normalization. JSON strings escape quote and backslash with their two-character escapes; U+0000…U+001F use lowercase six-character \u00xx escapes, never short escapes; slash and all other Unicode scalars are emitted directly as UTF-8. Integers use minimal base10 with no plus/leading zeros/negative zero; booleans/null use the standard lowercase JSON literals. Exact decimal seconds use nonnegative decimal strings with no exponent, leading zeros or trailing fractional zeros (zero is 0); raw_entry_text retains the original human lexical entry/precision. Rational PTS/timebase values use integer numerator/positive-denominator pairs reduced to lowest terms where a rational value is encoded. No numeric normalization changes an already SEALED record. Arrays retain their declared order; set-valued arrays use the explicitly prescribed exact-key sort. Unknown/duplicate keys, invalid encoding and noncanonical bytes are rejected. A future encoder/version and cross-language golden vectors need T01/T04 acceptance; this is not a claim about current schema serialization.

PROPOSED digest rule: record_body includes schema/session/record_id/sequence/kind/human principal, role-policy/authentication-session references, exact content/provenance and previous_record_digest. It excludes the actor attestation and both computed digests. Compute body_sha256 over those canonical body bytes. A detached actor_attestation binds body_sha256 through the selected trusted mechanism. Form the canonical envelope with exactly body, body_sha256 and actor_attestation; record_digest is SHA-256 of that complete envelope. Append the canonical wrapper with exactly envelope and record_digest plus one newline. The next record links this envelope-derived record_digest. This two-level construction avoids a signature/self-hash cycle while binding the complete attestation into the chain and protected anchor. The genesis binds session/grant/policy/protocol identity; every later record links its actual predecessor. A trusted committed anchor binds session_id, last sequence, record count, byte length, final digest and monotonic authority version; trusted genesis alone cannot detect suffix truncation. Actor attestations bind the body, not merely an untrusted handle. A digest's integrity meaning never becomes an authenticated signature by naming it “signature.”

| Transaction step (PROPOSED) | Durability / crash outcome |
|---|---|
| Validate and reserve operation | Authority checks current fence/authorization and stores operation_id, request/body digest and expected committed head as PREPARED; at most one prepared append may own that session head. Same ID/different bytes fails. |
| Append under one stable-inode lock | Lock covers read/verify-head, schema/link/role checks, append and fsync; create session files exclusively, reject symlink/replacement, fsync directory on creation. Stale owners cannot commit at authority. |
| Commit protected anchor | Authority compare-and-set validates PREPARED content and expected head, durably advances sequence/count/byte-length/digest and operation receipt. Protected payload journal or trusted immutable backup is required for acknowledged data recovery. A hash alone cannot reconstruct lost content. |
| Acknowledge submission | Return success only after local durable append and protected authority commit. A client crash after commit but before response returns the same receipt on an authenticated, appropriately permitted query; never appends a duplicate. |
| Recover uncommitted suffix | Verify PREPARED receipt/body exactly; preserve/quarantine unacknowledged bytes. Continue only through an explicitly authorized recovery transaction while current checks pass. Do not truncate acknowledged history or silently adopt arbitrary trailing bytes. |
| Reconcile committed mismatch | Fewer rows/bytes than protected head/count, rewritten chain, missing committed body or inconsistent backup is rollback/truncation/data loss: quarantine, stop access/promotion and record an incident through the independent authority. Never reset the anchor from local content. |
| Verify audit | Read committed anchor independently; verify exact canonical bytes, sequences, IDs, links, role/attestation/protocol/source/correction/adjudication dependencies and operation receipts; report uncommitted suffix separately. A full valid local chain alone is insufficient. |

PROPOSED external side effects require their own idempotent operation_id/commit protocol. Local logging cannot promise exactly-once promotion or external IO across a crash. Without protected authority/backup, only cooperative-process serialization and relative chain checks are potentially testable; malicious rewrite, rollback/truncation detection and authenticated attribution remain NOT VERIFIED and cannot be claimed. C1 basis: `docs/generated/master_reaudit/MISSION_17C1_CRITICAL_SECURITY_AND_DATA_GOVERNANCE_REVIEW.md:24-39`; `docs/generated/master_reaudit/MISSION_17B_HUMAN_REVIEW_CLI_TECHNICAL_SPEC.md:394-400`.

<a id="h8"></a>

## H8. PROPOSED schema adapter, permissions and promotion boundary

PROPOSED: sealed observations stay non-promotable until R01 selects a target schema/version and an audited adapter can preserve every relevant state and link. Keep protocol target digest separate from a correctly labeled ancestry/base digest (C1 F21); never copy illustrative hashes. Current8.1 requires proposal binding, a model-independence attestation, front/back observed-media hashes and its fixed boundary/status taxonomy (`src/railway_detection/annotation/stage2_1_schema.py:94-108`; `src/railway_detection/annotation/stage2_1_schema.py:163-207`; `src/railway_detection/annotation/stage2_1_schema.py:279-350`). A one-stream observation, missing actual observed hash, censored direction, deferred landmark or new adjudication link must not be silently coerced/lost to satisfy it. Versioned target change or explicit lossless extension remains R01/T01 PENDING; fabricated proposals, second reviewers, hashes or APPROVED statuses are forbidden.

PROPOSED publication: recheck exact approved batch digest and X03 at the actual write boundary, adopted schema/protocol, source chain/anchors/roles and all required review/adjudication links; use cohort-qualified collision-free identifiers and create-only outputs. Publish an immutable staged batch and atomically expose a batch commit manifest only when every record validates; incomplete staging is not a published batch. Repeated identical batch_id returns its committed receipt only; changed content or existing mismatched output rejects. Live media verification needs separate HASH_RAW_MEDIA scope and a vetted boundary. Promotion state does not imply X04 evaluation authority.

| Permission family (PROPOSED; none issued) | Required scope and separation | C1 execution dependency |
|---|---|---|
| Media review/read | Human/purpose/qualified media and READ_RAW_MEDIA | X01; no implied probe/hash/audio/model/cache/promotion |
| Media probe/hash | MEDIA_PROBE and HASH_RAW_MEDIA are distinct explicitly granted operations | X01 where scoped; X03 does not itself allow a raw hash |
| Checkpoint access | Named model resource/operation/purpose | X02; grants no media/cache/inference/evaluation |
| Protected-cache access | Named cache/condition and allowed read/replay purpose | X05; X04 also needed for real evaluation |
| Ground-truth promotion | Exact approved batch, protocol/schema/roles/output boundary | X03 plus every separately needed resource permission |
| Real-data evaluation | Frozen profile/conditions/model/GT/artifact bindings and operation permissions | X04 plus X02/X05/X03 where needed; scientific approval alone is insufficient |
| Training/split generation | Corpus/lineage, split-only versus training purpose and resources explicitly separated | X06; generating a split does not authorize training |
| Pilot execution / implementation | Actual pilot needs its own bounded plan; synthetic implementation is a separate mission | X07 with X01; X00 remains NOT AUTHORIZED |

<a id="h9"></a>

## H9. PROPOSED synthetic verification and evidence needed

Every H-T case below is a future synthetic unit/integration specification, NOT EXECUTED. Abstract actors are mathematical test variables, not reviewer identities or allowlist entries. Fixtures must use invented non-media bytes and isolated temporary storage with no production imports that read protected resources. T04 and X00 must define the later safe implementation mission.

| Test ID (PROPOSED) | Setup / action | Required oracle | Scope / cannot establish |
|---|---|---|---|
| H-T01 | Present a known handle without authenticated principal/appointment | Deny; zero protected operations/SEALED writes | Handle membership is not identity; cannot establish real credentials. |
| H-T02 | Same verified principal with two aliases attempts first/second roles for one case; conflict declaration missing | Deny independent coverage; case NEEDS_SECOND_REVIEW | Tests role policy, not actual human independence. |
| H-T03 | Rater role attempts issuer/promoter action | Deny absent explicit independently approved role grant; no registry mutation | Must detect shared-list privilege expansion, not merely rename fields. |
| H-T04 | Read-only grant attempts hash/probe/model/cache/promotion/evaluation or wrong cohort/purpose | Each missing operation/resource denied before access | Capability separation only, not OS protection. |
| H-T05 | Approved expected source/dependency differs, disk replaced after preflight or loaded code provenance unavailable | Deny new protected operation under protected profile; disclose local-only limitation | A disk hash cannot prove loaded-object authenticity. |
| H-T06 | Recompute an altered local record/grant chain; protected origin/anchor mismatches | Deny/quarantine despite internally valid hashes | Requires synthetic trusted authority; does not validate a real signing deployment. |
| H-T07 | Revoke/expire role/grant between operations and during recovery | Next protected use denied, history retained, no new session or duplicate side effect | Already exposed bytes cannot be revoked. |
| H-T08 | Close/abort then reuse same grant in a new session | Reservation remains consumed; new session denied | Same-session retry/recovery is tested separately. |
| H-T09 | Two workers reserve one grant or replace a locally locked ledger inode | Exactly one authoritative reservation; protected profile rejects stale/replaced state; local-only bypass limitation explicit | No claim that flock resists a malicious same-user writer. |
| H-T10 | Crash before append, after fsync, after anchor commit and before ACK; retry same/different content ID | Only committed exact content returns same receipt; no duplicate SEALED records; differing content rejected; stale fence denied | External exactly-once effects require their own protocol. |
| H-T11 | Alternate opener ignores Python guard / symlink target changes | Protected broker test denies unscoped handle; local-only profile must report lack of OS protection | Does not prove privileged-admin resistance. |
| H-T12 | Roll back/truncate ledger or authority/backup becomes unavailable/compromised | Protected expected head/count/length mismatch stops processing; fail closed, quarantine and incident evidence | A fully compromised authority cannot authenticate its own recovery. |
| H-T13 | Draft memo or missing applicable approval presented as authority | Deny execution/publication; keep R/T/X statuses unchanged | Correct paperwork processing, not genuine researcher approval. |
| H-T14 | Prediction/prior-review/candidate leak through queue, logs, exception or player state before seal | First-pass boundary rejects/excludes it; independent pass remains separated | Cannot prove a human never saw information outside the boundary. |
| H-T15 | T2 deferred, cross-camera clocks, invalid PTS, missing values, nonfinite/negative time or observed point on censored state | Typed rejection/deferred state; no invented time or global ordering; exact original bytes retained | Does not validate physical landmarks/media. |
| H-T16 | Each six-category trigger plus no-trigger/censored-only and missing-trigger-input cases | Required independent review blocks until satisfied; unknown input not silently passed; no universal policy | Named policy still needs R05 adoption; comparison grid is not a tolerance study. |
| H-T17 | Differing sealed observations, independent frame equals numeric midpoint, unresolved case | Separate adjudication source links; observed equality allowed; unresolved UNCERTAIN; originals byte-identical | Does not supply an actual human decision. |
| H-T18 | Incompatible schema/protocol, forged hashes, cohort collision, partial batch, duplicate publication | Adapter refuses loss; no publication on failure; exact approved batch/create-only boundary/idempotent receipt | No active schema migration, promotion or GT is produced. |

The original ten TEST-CLI intents remain traceable:01/02→H-T05/H-T13 (preflight evidence, never a complete integrity guarantee);03→H-T07 (expiry);04→H-T04 (operations, not an invented implemented tier);05→H-T01/H-T03 (identity/roles);06→H-T14 (blind data flow);07→H-T15 (typed local clocks);08→H-T06/H-T10/H-T12 (anchored integrity/recovery);09→H-T08/H-T09 (reservation/replay);10→H-T10 (same-session recovery). This replaces ambiguous planned oracles without modifying their historical source: `docs/generated/master_reaudit/MISSION_17B_HUMAN_REVIEW_CLI_TECHNICAL_SPEC.md:333-359`.

<a id="h10"></a>

## H10. Acceptance boundary and unresolved facts

PROPOSED documentary acceptance requires complete H2–H9 contracts and cross-document consistency; future synthetic acceptance requires actual H-T evidence under T04/X00. Authentication/role deployment, protected authority/anchors/backup, reviewer appointments/qualification/independence, player accuracy, actual media identity, pilot timing/tolerances and protocol/schema adoption are NOT VERIFIED or NOT VERIFIABLE under present restrictions. No human approval or protected operation is created. F01/F02/F03/F20/F21/F22 remain open beyond corrected wording; see the integrated F01–F24 register. STOP at documentation review.
