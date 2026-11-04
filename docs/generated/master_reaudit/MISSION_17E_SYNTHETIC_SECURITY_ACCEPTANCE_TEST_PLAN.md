# Mission 17E — Synthetic security acceptance test plan

Date: 2026-11-04, America/New_York. Phase baseline: `fbc60aa1e54f7fa69c824e6a73d2d52e3c7a1375`; branch main. Scope: blueprint/readiness preparation only. No human-review CLI, authorization service, identity enrollment, token, observation, adjudication or promotion is implemented or executed here. Technical requirements are candidate specifications; researcher/governance/protected-execution decisions remain pending. The user authorized these six documents and normal exact-path Git delivery, not protected operations or a future17F mission.

Companions: [human workflow](MISSION_17E_HUMAN_REVIEW_IMPLEMENTATION_BLUEPRINT.md), [security architecture](MISSION_17E_AUTHORIZATION_SECURITY_IMPLEMENTATION_BLUEPRINT.md), [synthetic security plan](MISSION_17E_SYNTHETIC_SECURITY_ACCEPTANCE_TEST_PLAN.md), [dependencies](MISSION_17E_IMPLEMENTATION_DEPENDENCY_REGISTER.md), [researcher gate](MISSION_17E_RESEARCHER_RELEASE_GATE_CHECKLIST.md), [readiness](MISSION_17E_READINESS_REPORT.md).

<a id="tests"></a>
## 1. Planned evidence and isolated fixture rules

**All 32 ES cases below are PLANNED — NOT IMPLEMENTED — NOT EXECUTED.** They refine C4 SEC01–SEC20 without claiming security completion from17D's114 actuator/CV/isolation tests. Test code/service implementation requires a separately authorized future task after relevant researcher/technical contract decisions. No real grant, identity, signature, token reservation/consumption, annotation, adjudication or GT publication occurs in 17E.

Fixtures must use newly constructed synthetic principals, fake transport/stores, in-memory neutral media surrogates and explicit temporary paths; never real media/checkpoints/caches, governance folders or credentials. Synthetic proof bytes cannot be represented as genuine signatures/approvals or copied to researcher records. Event/player timing fixtures must be verifiably synthetic; no resource inspection is permitted to create them. Deterministic schedulers enumerate every specified interleaving and fault cut; nondeterministic stress supplements, not replaces, the exact oracles.

| Case | Requirements | Synthetic stimulus | Objective oracle | State |
|---|---|---|---|---|
| ES01 | AB02/AB08 | Known string/alias/shared account without authenticated independent appointment | Deny identity/independent coverage; zero protected uses. | PLANNED — NOT EXECUTED |
| ES02 | AB02/AB08 | Reviewer onboarding attempts to gain issuer or own role elevation | Separate registries; elevation requires independent permitted approval. | PLANNED — NOT EXECUTED |
| ES03 | AB03/AB05 | Wrong/missing approval subject,digest,delegation or widened scope | Deny before reservation/use; policy reference alone cannot stand in for approval. | PLANNED — NOT EXECUTED |
| ES04 | AB04/AB06 | Wrong project/repository/deployment/relocation/expected execution manifest | Deny; unchangedHEAD/disk self-hash cannot validate changed runtime. | PLANNED — NOT EXECUTED |
| ES05 | AB05/AB16 | Read-only attempts probe/hash/model/cache/promotion/evaluation | Each missing operation/resource denied at use. | PLANNED — NOT EXECUTED |
| ES06 | AB07/RC04 | Concurrent reserve and identical/different initialization retry | One durable session/winner; exact retry returns same result; conflicting content denies. | PLANNED — NOT EXECUTED |
| ES07 | AB07/RC06 | Grant replay after COMPLETED/ABORTED, new session or fresh quota ID | Consumption/quota state retained; no new session or semantic duplicate first pass. | PLANNED — NOT EXECUTED |
| ES08 | AB06/RC06 | Expiry/revocation/authority-clock rollback/unavailability during session | Current uses deny; no fabricated fresh authority or revived lease. | PLANNED — NOT EXECUTED |
| ES09 | AB09 | Expose comparison then change session/alias/assignment ID | Actor/event knowledge remains exposed; no reset to blind. | PLANNED — NOT EXECUTED |
| ES10 | AB10 | Prediction leak via queue,name,player,log,exception or API before seal | Boundary refuses/excludes leak; result not certified blind after exposure. | PLANNED — NOT EXECUTED |
| ES11 | AB10/AB14 | Missing second seal or missing no-second-required trigger decision | No comparison release or claimed independent coverage. | PLANNED — NOT EXECUTED |
| ES12 | AB11 | T2 deferred,cross-camera time order,invalidPTS,censored point value | Typed refusal/deferred/uncertain state; no invented landmark/time. | PLANNED — NOT EXECUTED |
| ES13 | AB12 | Post-comparison correction replaces original/claims new blind pass | Append informed correction with original/exposure links; original bytes/view retained. | PLANNED — NOT EXECUTED |
| ES14 | AB13 | Self/overlap adjudication without adopted policy,averaging or forced agreement | Deny unauthorized conflict; separate source-linked resolution; unresolved UNCERTAIN. | PLANNED — NOT EXECUTED |
| ES15 | AB14 | All six risk triggers,censored-only,unknown trigger evidence/hash mismatch | Correct pending-policy behavior; unknown/hash defects cannot be cured by agreement. | PLANNED — NOT EXECUTED |
| ES16 | RC01 | ControlUnicode/unpairedsurrogate/duplicatekeys/float/unknownfields golden vectors | Exact canonical bytes or rejection; declared Unicode/decimal/rational policy preserved. | PLANNED — NOT EXECUTED |
| ES17 | RC02/RC03 | Genesisnull predecessor/sequence/count/envelope/body/attestation alteration | Exact links/typed attestations/head/count/length checked; no self-hash cycle. | PLANNED — NOT EXECUTED |
| ES18 | RC04/RC05 | Crash before/afterPREPARED,protected journal,append,fsync,commit,ACK | Exact receipt/outcome; no lost acknowledged body or duplicate commit. | PLANNED — NOT EXECUTED |
| ES19 | RC06 | prepare→revoke→commit and commit→revoke interleavings | First aborts; latter preserves committed history then denies future use. | PLANNED — NOT EXECUTED |
| ES20 | RC06 | finalize races outstandingPREPARED/UNKNOWN_EXTERNAL and new prepare | BUSY until resolved; after terminal linearization all new uses/commits deny. | PLANNED — NOT EXECUTED |
| ES21 | RC04/RC07 | Owner dies,recovery acquires fresh fence,old owner continues | Only same permitted principal/session recovers; stale authoritative commit/use denies. | PLANNED — NOT EXECUTED |
| ES22 | RC07 | Crash-after-commit-before-response and identical/different-body retry | Same committed receipt only; no append/side-effect replay or content substitution. | PLANNED — NOT EXECUTED |
| ES23 | RC03/RC07 | Recompute chain,truncate suffix,restore old ledger/anchor snapshot | Independent committed digest/count/length/version mismatch quarantines. | PLANNED — NOT EXECUTED |
| ES24 | RC05/RC07 | Delete localCOMMITTED body or protected journal unavailable | Restore only exact trusted bytes under recovery; missing trust/body stops,never resetsanchor. | PLANNED — NOT EXECUTED |
| ES25 | RC07/RC08 | Torn suffix,mid-file corruption or unknown external effect | Preserve evidence/quarantine; unknown prevents normal finalization/publication. | PLANNED — NOT EXECUTED |
| ES26 | AB15/RC08 | Publish partial batch/cohort-colliding IDs or same batchID alteredbytes | No partial authoritative manifest; qualified create-only outputs; conflicting batch rejects. | PLANNED — NOT EXECUTED |
| ES27 | AB15/RC08 | Crash before/after atomic batch visibility and receipt response loss | Only exact committed manifest authoritative; idempotent receipt retry. | PLANNED — NOT EXECUTED |
| ES28 | AB01/AB06 | Alternate opener/symlink/source mutation ignores Python guard | Protected broker boundary tested separately; cooperative profile must disclose lack of resistance. | PLANNED — NOT EXECUTED |
| ES29 | AB01/RC09 | Trusted authority/admin/issuer root compromise | Stop guarantees; independently approved external recovery/re-enrollment,not self-repair by hash. | PLANNED — NOT EXECUTED |
| ES30 | AB01/AB06 | Authority/clock/revocation/backup service unavailable or stale | Fail closed for protected use; availability limitation recorded. | PLANNED — NOT EXECUTED |
| ES31 | AB11/AB13/AB15 | Inactive schema submitted to active promoter or fabricated APPROVED/proposalhash | Vetted versioned adapter required; no coercion/fake evidence/publication. | PLANNED — NOT EXECUTED |
| ES32 | AB16 | Passing suite or draft memo used as real review/model/promotion/evaluation permission | No permission/grant/appointment/approval inferred; separate applicable gates remain. | PLANNED — NOT EXECUTED |

## 2. Required receipts and pass criteria

Future acceptance receipt must identify exact requirement/profile/test IDs, selected threat model, synthetic fixture provenance, tested code/config/runtime/source hashes, command/environment, expected/observed outcomes, failures/skips and retained fault schedule. Schema/golden-byte tests, pure state-machine tests, service/broker integration and actual deployment isolation evidence are distinct. No passing pure Python suite proves OS isolation, real human truth/qualification, external blinding or compromised-root resistance.

Every negative test asserts zero forbidden broker operations/accepted records and the exact preserved committed head/count/quota/phase; race tests assert an allowed linearization/outcome rather than mere absence of exceptions. Crash tests compare protected journal, local acknowledged prefix and authority receipt; unknown external effects remain explicitly unresolved. Invalid proof/schema is rejected before committing visibility. Recovery tests retain acknowledged bytes and do not silently truncate history to pass.

All relevant requirements and negative/race/crash cases must pass before a future implementation acceptance claim. Any failure blocks that component/release, preserves work/evidence and must be fixed or honestly reported; no relaxed oracle, removed security assertion, fabricated receipt or unapproved fallback is allowed. Real use additionally requires actual independently verified roles/deployment/trust/permissions.32 proposed cases are a plan, not32 results.

Sources: [C4 readiness](MISSION_17C4_SYNTHETIC_TEST_READINESS_MATRIX.md#readiness), [C4 authority](MISSION_17C4_AUTHORIZATION_AND_BLINDING_ACCEPTANCE_SPEC.md#authority), [C4 recovery](MISSION_17C4_RECOVERY_AND_CV_LINEAGE_ACCEPTANCE_SPEC.md#recovery).
