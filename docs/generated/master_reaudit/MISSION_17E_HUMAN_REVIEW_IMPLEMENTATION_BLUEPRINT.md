# Mission 17E — Human-review implementation blueprint

Date: 2026-11-04, America/New_York. Phase baseline: `fbc60aa1e54f7fa69c824e6a73d2d52e3c7a1375`; branch main. Scope: blueprint/readiness preparation only. No human-review CLI, authorization service, identity enrollment, token, observation, adjudication or promotion is implemented or executed here. Technical requirements are candidate specifications; researcher/governance/protected-execution decisions remain pending. The user authorized these six documents and normal exact-path Git delivery, not protected operations or a future17F mission.

Companions: [human workflow](MISSION_17E_HUMAN_REVIEW_IMPLEMENTATION_BLUEPRINT.md), [security architecture](MISSION_17E_AUTHORIZATION_SECURITY_IMPLEMENTATION_BLUEPRINT.md), [synthetic security plan](MISSION_17E_SYNTHETIC_SECURITY_ACCEPTANCE_TEST_PLAN.md), [dependencies](MISSION_17E_IMPLEMENTATION_DEPENDENCY_REGISTER.md), [researcher gate](MISSION_17E_RESEARCHER_RELEASE_GATE_CHECKLIST.md), [readiness](MISSION_17E_READINESS_REPORT.md).

<a id="workflow"></a>
## 1. Implementation boundary and proposed modules

The planned interface is a human observation recorder with neutral authorized resource handles and no prediction-generation function. A future separately authorized synthetic implementation may place review_domain.py, review_cli.py and player_adapter.py under a new review package; these are proposed names, not existing/created files. Keep the existing synthetic adjudication harness, active schema, promoter, guards and real-data entrypoints intact. Do not repurpose the 17D actuator/CV helpers as a human-review authorization mechanism.

Domain transitions are pure functions over typed assignment, knowledge, observation and adjudication records. An injected identity provider and authority client supply current authenticated roles/approval/operation leases. The broker/player is the only future protected resource path; presentation code cannot accept arbitrary local paths or bypass point-of-use checks. Ledger storage receives exact validated bodies and commits through the independently protected transaction boundary. The chosen host/trust profile must match the claimed protection.

Authoritative contracts are [C4 authorization/blinding](MISSION_17C4_AUTHORIZATION_AND_BLINDING_ACCEPTANCE_SPEC.md#authority) AB01–AB16 and [C4 recovery](MISSION_17C4_RECOVERY_AND_CV_LINEAGE_ACCEPTANCE_SPEC.md#recovery) RC01–RC09. This blueprint does not change their role, schema, hashing, session/quota or phase semantics.

## 2. Appointed human workflow

| Step | Actor / permitted inputs | Required transition and evidence | Blocking condition |
|---|---|---|---|
| Appointment/readiness | Researcher or independently authorized delegate | Named authenticated stable principal, role/qualification/training/conflict evidence, adopted review plan/protocol/schema and player timing/PTS evidence. External audit reviewer if appointable; no invented identity. | R01/R05/R08/T01/T04 and resource permissions pending. One allowlist string is not identity/qualification. |
| Neutral assignment | FIRST_REVIEWER or SECOND_REVIEWER | Canonical physical event/cohort, neutral geometry, appointed review round, no model-derived queue/filename hints. Check actor/event exposure across aliases and sessions. | Prior exposure cannot reset to unexposed; unknown assignment/scope or quota denies. |
| Reserve/open | Authenticated reviewer within current permitted purpose | Durable unique grant/session reservation and fence before first protected use; adopted clock/protocol/execution/resource bindings checked. | No X01 means no player/resource access. Review does not need its own future promotion receipt. |
| Blind observation | Reviewer sees only authorized neutral material | ASSIGNED_UNEXPOSED→BLIND_DRAFT→BLIND_SEALED; per-boundary local camera clock, raw lexical input, exact value, PTS/frame/uncertainty/censor/provenance and rationale. | Candidate/prior judgment/log/overlay/error/player leakage; unknown timing accuracy limits claims. No automatic timestamp/point repair. |
| Independent second pass | Different appointed verified human | Separate sealed observations and case-conflict/trigger assignment; aliases/shared accounts do not establish independence. | Required second reviewer unavailable means unresolved/blocked, never fabricated coverage. |
| Comparison exposure | Explicitly permitted post-seal workflow | Both required seals or adopted no-second-required evidence; atomically append EXPOSURE with monotone actor/event knowledge version. | No transition back to blind and no fresh-session workaround. |
| Correction | Original author under permitted correction scope | Append AB12 correction referencing original/superseded digests and capture phase/exposure/reason. Keep original blind view and distinguish informed corrections. | Overwrite/retagged blind claim or fresh operation ID bypass of assignment quota denies. |
| Adjudication | Appointed researcher/adjudicator under conflict policy | Separate AB13 entry links exact independent sources/evidence/rationale. Unresolved remainsUNCERTAIN; no numeric averaging/forced agreement. | Self-adjudication/overlap not allowed without adopted R05 policy; missing source links or required media permission denies. |
| Session closure/recovery | Current owner or explicitly permitted same-principal recovery | Durable terminal receipt or fresh-fence reconciliation; grant stays consumed. Preserve unknown effects/quarantine. | Revoked/expired/unavailable authority or pending unknown effects prevents normal completion. |
| Promotion request | Permitted batch operator/approver roles | Separate exact content-bound batch approval, vetted schema adapter, all source anchors/reviews/conflicts, create-only qualified atomic publication and receipt. | X03 and any live hash scope absent; eligibility/session completion never grants promotion or evaluation. |

## 3. Boundary semantics and human integrity

T1 is the documented approach frog/line, T2 entry landmark remains deferred, T3 is trailing coupler/rear of the leading locomotive, and T4 is final vehicle tail clearance. Preserve independent camera-local clocks; cross-camera sorting/subtraction requires explicit adopted alignment. OBSERVABLE has evidence and value; CENSORED/UNCERTAIN/NOT_OBSERVABLE retain reasons and no invented point. PTS/timebase/origin or missing precision is explicit; frame/fps is not assumed valid for variable rate media. Horn/audio work is separate scope if reported.

Risk-based second-review triggers remain the pending recorded six-category policy; censored alone is not a trigger, unknown trigger input cannot be marked evaluated, and second agreement cannot repair media identity. Mandatory triggered cases require real independent coverage. The proposed8.2 adjudication restriction to OBSERVABLE/UNCERTAIN is preserved; an extension to disputed censor/not-observable outcomes needs R01 review/adapter acceptance. Active8.1 cannot receive fabricated APPROVED/proposal hashes to simulate compatibility.

Blindness software can enforce selected-process input boundaries, not prove that a human never saw the event externally. Qualification and conflict attestations must be genuine, independently checked and scoped; an assistant cannot create them. A30s legacy plausibility floor is not scientific review sufficiency, and a small usability pilot cannot establish a numerical tolerance without an approved measurement study. Pilot purpose, sample/rater plan, timing capture, consent/governance as applicable and stop rules precede X07.

## 4. UI and verification requirements before real use

UI must expose case identity/role/phase, boundary state/reason, local clock and evidence uncertainty clearly, with explicit seal/correction/adjudication actions. It must not present proposals in the blind pane or expose implementation hashes as a substitute for a human decision. Accessible input validation rejects errors without suggesting a scientifically unsupported point. Debug logging uses neutral identifiers and protected audit policy; it cannot leak a candidate through an exception. Player seeking/frame presentation needs synthetic PTS fixtures and bounded timing claims.

Future synthetic tests must exercise queue/player/log/error blinding, two independent seals, alias/session re-entry, informed correction persistence, conflict/trigger/adjudication/adapter negatives and immutable history under crash. These tests are planned in the companion security plan; none was executed in 17E. Current17D's114 tests validate in-memory actuator/CV helpers only.

Sources: `docs/generated/master_reaudit/MISSION_17C3_SECURITY_AND_AUTHORIZATION_ACCEPTANCE_REVIEW.md:85-101`; `docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md:106-114`; `docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md:176-185`; `src/railway_detection/annotation/second_review.py:6-28`.
