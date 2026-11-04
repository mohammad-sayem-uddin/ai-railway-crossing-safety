# Mission 17F — Human-review and security readiness

Date: 2026-11-04, America/New_York. Freshly verified baseline: `8221e96f8de48d995f4397a7e29255cdc8ec50f9`; branch `main`. Mission 17F authorizes source/metadata inspection, isolated synthetic audit tests, these five reports and normal exact-path Git delivery only. No implementation change or protected operation is authorized by this report.

**NOT READY for protected human review, security deployment or GT publication.** All six 17E blueprints were inspected and retain their planned-only status. The 17D components and newly reproduced tests do not implement those services. No human/security feature test or protected operation was executed in 17F.

Companions: [engineering audit](MISSION_17F_INDEPENDENT_ENGINEERING_AUDIT.md), [controller plan](MISSION_17F_CONVENTION_B_CONTROLLER_INTEGRATION_PLAN.md), [CV/OOF plan](MISSION_17F_CV_PROVENANCE_AND_OOF_IMPLEMENTATION_PLAN.md), [human/security readiness](MISSION_17F_HUMAN_REVIEW_SECURITY_READINESS.md), [gate register](MISSION_17F_IMPLEMENTATION_GATE_REGISTER.md).

## 1. Six-document consistency review

| Inspected 17E document | Checked against actual implementation / C4 | Current finding |
|---|---|---|
| [Human workflow](MISSION_17E_HUMAN_REVIEW_IMPLEMENTATION_BLUEPRINT.md) | Typed neutral assignment, seals, monotone exposure, informed corrections, adjudication and separate promotion | Consistent as a future workflow; actuator/CV namespace cannot authenticate actor or resource. No CLI/player/domain service implemented by 17D. |
| [Authorization/security](MISSION_17E_AUTHORIZATION_SECURITY_IMPLEMENTATION_BLUEPRINT.md) | Independent role/approval/project/session/broker/journal/publication services and selected threat profile | Correctly discloses missing enforcement and cooperative versus protected trust. Existing local guards are not those services. |
| [Security test plan](MISSION_17E_SYNTHETIC_SECURITY_ACCEPTANCE_TEST_PLAN.md) | ES01–ES32 and C4 SEC obligations versus actual 114 cases | All 32 remain planned/unexecuted; none becomes executed through 17F's actuator/CV fixtures. |
| [Dependency register](MISSION_17E_IMPLEMENTATION_DEPENDENCY_REGISTER.md) | DEP01–DEP14: full OOF and controller integration explicitly deferred | Consistent; F17-01…05 add concrete interface/performance prerequisites to DEP10–12, not approval or removal of dependencies. |
| [Researcher checklist](MISSION_17E_RESEARCHER_RELEASE_GATE_CHECKLIST.md) | R01–R08/T01–T04 pending; X01–X07 separate | Still pending/unauthorized; current audit request authorizes this technical audit only. |
| [Readiness report](MISSION_17E_READINESS_REPORT.md) | Blueprint PASS versus protected-use NOT READY; source/test and disclosure limits | 114-test claim independently rerun successfully. Security/human/OOF/actual-controller claims remain unestablished. Historical stop text is preserved. |

The security source corroborates the boundaries: media_guard rereads recorded authorization at the concrete operation but declares no OS sandbox; governance only verifies recorded statements with null signature; promoter takes caller-supplied expected state/registries and writes one event-named JSON. None provides the proposed independently controlled authority, authenticated expected anchors or atomic batch-manifest publication. These were text inspections, not executions or bypass attempts: `src/railway_detection/safety/media_guard.py:48-54`; `src/railway_detection/safety/media_guard.py:333-379`; `src/railway_detection/safety/media_guard.py:559-601`; `src/railway_detection/evaluation/governance.py:487-501`; `src/railway_detection/annotation/promotion_gate.py:540-567`.

## 2. Shared contracts and identities that must stay separate

| Contract to share through reviewed versioned interfaces | Separation that must remain explicit |
|---|---|
| Canonical physical event/cohort/alias/capture provenance and exact registry bindings | Human principal/appointment is not a dataset event ID. Review session ID is not capture session ID. CV event grouping is not human independence. |
| Time representation with value, clock domain, origin/timebase/precision and conversion evidence | Camera-local observation PTS, controller master µs, trusted authority UTC and lease/monotone clocks are different domains. Do not compare them without selected mappings. |
| Closed schema/canonical bytes and detached digests/attestations | `RunResult.canonical_json` and `Allocation.canonical_json` are deterministic synthetic strings, not the complete RC01 codec or signed authority records. F17-03/04 demonstrate why identity/typing needs additional enforcement. |
| Trusted expected binding resolver and immutable input-reference DAG | Candidate self-hash is not expected authority. Dataset/role truth, code execution identity, approval and grant scope each need their own authenticated expected source. F17-01/02 cannot serve as role/approval verification. |
| Immutable records, status vocabulary and independently verified receipts | A simulation interval is not a human observation; model calibration is not rater calibration/pilot; fitted-model evidence is not a grant to access a checkpoint. |
| Neutral resource identity and point-of-use check/result receipt | A research manifest path is not a broker handle; allocation success does not grant read/probe/hash/train/evaluate/publish. Protected operations remain individually scoped. |
| Policy/version references and qualified publication IDs | Schema compatibility is not protocol adoption. Eligibility, authentic approval, execution capability and completed operation are distinct states. |

Shared utilities should be small pure contracts with injected resolvers; import direction must not cause the synthetic modules to load production media, models or authority files. Domain-specific typed bindings prevent a hash or ID from one domain being accepted in another. Independent human identity/qualification/conflict checks remain external facts, not fields an assistant can fill credibly.

## 3. Missing trusted services and deployment evidence

| Required service / infrastructure | Evidence before reliance | Current state |
|---|---|---|
| Principal/appointment/qualification/delegation service | Genuine identities, independent appointment/elevation, conflict/recusal and role expiration/revocation records | Not supplied or created here; R05 pending. |
| Approval/project/protocol/execution resolver | Exact authentic subject/version/scope, independently expected code/runtime/deployment identity; no trusting client-selected local state | Blueprint only; R01/T01 pending. |
| Grant/session authority | Atomic unique nonce reservation, scope/quota/phase checks, trusted current time/revocation, durable terminal consumption and monotone fencing | Blueprint only; no tokens issued/consumed. |
| Resource broker / isolated runtime | Selected host/process/filesystem/credential boundaries, non-bypassable check-and-use handles for protected profile, independent administration | Not deployed or tested. Local Python guards cannot resist an actor controlling the same process/filesystem. |
| Review knowledge/player/input boundary | Stable actor/event exposure across aliases/sessions, independent seals, neutral queue/player/log/errors, synthetic seek/PTS accuracy evidence | No implemented 17E review CLI/player or proof of external human blindness. |
| Codec/attestation/protected journal/anchor | Closed schemas, cross-language byte vectors, current trusted anchors and recoverable protected payloads before ACK | Not implemented. Self-consistent local hash chain does not establish absence of rollback. |
| Transaction/recovery/availability services | Linearizable prepare/revoke/commit/finalize, fenced ownership, exact outcome query, durable backups/recovery and UNKNOWN_EXTERNAL quarantine | Not implemented or fault-tested. Unknown authority state denies protected use; no global exactly-once IO promise. |
| Batch publication/schema adapter | Adopted active schema, immutable source/approval bindings, create-only qualified objects and single protected atomic visibility/receipt point | Existing single-record promoter is not this blueprint. No GT promotion occurred. |

T01 must choose COOPERATIVE_LOCAL with explicit hostile-user/rollback limits, or PROTECTED_BROKER with independently controlled authority/broker/runtime and actual deployment tests. A second local writable file is not an independent trust root. Root/authority compromise exceeds the selected guarantees and requires external approved recovery; passing Python tests cannot resolve it. Authentication mechanism/key custody, time/lease policy, service reachability, durable storage, backup/fencing and administration separation need actual selected infrastructure. No such services are installed or credentialed by 17F.

## 4. Security tests remain planned

| Existing case group | Required evidence still absent |
|---|---|
| ES01–ES05 | Principal/role elevation, approval/project/runtime binding and operation-specific resource denial. |
| ES06–ES08 | Concurrent reservation, terminal replay/quota and expiry/revocation/time/availability behavior. |
| ES09–ES15 | Actor/event exposure re-entry, prediction leak paths, independent seals/triggers, typed observation/correction/adjudication/conflict boundaries. |
| ES16–ES17 | Canonical numeric/Unicode/schema and body/envelope/attestation/genesis/anchor golden vectors. |
| ES18–ES25 | Every journal/append/fsync/commit/ACK crash cut, revocation/finalize ordering, fresh fences, ACK loss, rollback/body loss and unknown outcomes. |
| ES26–ES27 | Atomic batch visibility, qualified IDs, immutable exact approved content and crash/idempotent retry. |
| ES28–ES30 | Actual selected broker/OS boundary, alternate opener/runtime mutation, authority compromise and unavailable/stale authority. |
| ES31–ES32 | Schema/adoption mismatch and refusal to infer real permission from tests/documents. |

All 32 are **PLANNED — NOT EXECUTED**. C4 SEC01–SEC20 likewise remain unexecuted. Future negative tests must assert zero forbidden broker uses/accepted records and exact preserved head/count/quota/knowledge; race tests need allowed linearizations, and crash tests must compare acknowledged bytes with protected journal and authority anchors. The 17F six xfails concern CV interface context/receipt validation, not execution of these ES security requirements. A future implementation cannot count expected failures as accepted controls.

## 5. Research decisions and legal ordering

R01 exact protocol/schema/adapter, R05 genuine roles/conflicts/qualification, T01 deployment/trust and T04 scoped acceptance block reliance on human/security services. R08 must define prospective pilot purpose, raters/cases/measurement/analysis/stop rules; usability testing alone cannot justify scientific time tolerances. R02 preserves independent cameras unless genuinely amended; T1/T3/T4 landmark meaning and deferred T2, censor/uncertainty/local clock rules cannot be “repaired” by UI defaults. Active 8.1 versus proposed 8.2 compatibility remains unresolved, v7.1.1 PROPOSED and OptionC unapproved.

R03/R06/T03 govern corpus/role/exposure/allocator/calibration; R04/T02 govern controller/outcomes/estimators. R07 governs human authors/disclosure/claims/release scope. D-01…D-10 formal decisions and RD001–RD055 remain unchanged. Writing a technically complete plan makes none approved. A newly authorized bounded synthetic service task could use fake identities/transports before real credentials or GT exist; do not invent a circular requirement that initial review already have its own future promotion receipt.

After selected contracts and separately authorized implementation: synthetic domain/codec tests precede service integration and deployment evidence; genuine appointments and exact X01 permit relevant human review; R08/X07 additionally gate pilot; exact source-bound approval and X03 gate later promotion; evaluation requires its separate X04 and adopted GT/input/split/model/cache records with X02/X05 as applicable. X06 split and training remain separately scoped. No stage retroactively creates facts required by an earlier stage, and no grant authorizes a different operation.

STOP after this audit delivery. Do not implement review/security services, issue or consume tokens, view resources, annotate/adjudicate or publish GT. Wait for researcher review.
