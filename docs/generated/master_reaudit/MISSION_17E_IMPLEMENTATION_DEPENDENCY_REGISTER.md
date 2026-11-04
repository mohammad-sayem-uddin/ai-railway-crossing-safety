# Mission 17E — Implementation dependency register

Date: 2026-11-04, America/New_York. Phase baseline: `fbc60aa1e54f7fa69c824e6a73d2d52e3c7a1375`; branch main. Scope: blueprint/readiness preparation only. No human-review CLI, authorization service, identity enrollment, token, observation, adjudication or promotion is implemented or executed here. Technical requirements are candidate specifications; researcher/governance/protected-execution decisions remain pending. The user authorized these six documents and normal exact-path Git delivery, not protected operations or a future17F mission.

Companions: [human workflow](MISSION_17E_HUMAN_REVIEW_IMPLEMENTATION_BLUEPRINT.md), [security architecture](MISSION_17E_AUTHORIZATION_SECURITY_IMPLEMENTATION_BLUEPRINT.md), [synthetic security plan](MISSION_17E_SYNTHETIC_SECURITY_ACCEPTANCE_TEST_PLAN.md), [dependencies](MISSION_17E_IMPLEMENTATION_DEPENDENCY_REGISTER.md), [researcher gate](MISSION_17E_RESEARCHER_RELEASE_GATE_CHECKLIST.md), [readiness](MISSION_17E_READINESS_REPORT.md).

<a id="dependencies"></a>
## 1. Dependency states and current implemented scope

17C-4 documents candidate requirements;17D implements only in-memory synthetic actuator/grouping helpers with 114 passing tests.17E adds six blueprints. None implements the human/security service/broker/codec/publication machinery below. “Documented” does not mean implemented, researcher approved, governance authorized or protected execution authorized. A synthetic prototype can be explicitly scoped before unrelated real-data artifacts, but may not make unavailable real-world claims.

| Dependency | Required input / contract | Current state | Blocks |
|---|---|---|---|
| DEP01 Research decisions | R01–R08 exact protocol/schema, camera/metric/corpus/role/pilot/claims choices; D-01…D-10 formal action. | PENDING; no approvals created. | Scientific/protocol/role/corpus claims and real use dependent on those decisions. |
| DEP02 Accepted threat profile | T01 COOPERATIVE_LOCAL or PROTECTED_BROKER, independently controlled authority/broker/runtime, time/lease/delegation policies. | Candidate design only; deployment NOT VERIFIED. | Security enforcement claims and protected resource integration. |
| DEP03 Genuine roles/qualification | R05 actual appointments, principal enrollment/qualification, independent second reviewer, issuer/PI/operator/admin conflicts/recusal and elevation oversight. | No new role/identity/allowlist entry. | Human annotation/adjudication, issuance and publication. |
| DEP04 Adopted protocol/schema/adapter | R01 exact final byte adoption/version/compatibility and typed observation→active schema/publication adapter. | v7.1.1 remains proposed; active8.1/inactive8.2 reconciliation pending. | Real review, GT promotion and protocol-dependent evaluation. |
| DEP05 Blind domain/player | AB09–AB14 monotone actor/event phases, seals/exposure/corrections/trigger/adjudication; synthetic seek/PTS/player/input-boundary evidence. | Blueprint; no human CLI/player implemented. | Blind workflow acceptance and actual review/pilot. |
| DEP06 Auth/project/session authority | AB03–AB08 authentic approval/project/execution bindings, scope/quota/reservation/time/revocation/fence and point-of-use broker. | Blueprint; no real grant/authority. | Protected operations and security lifecycle acceptance. |
| DEP07 Ledger and transaction durability | RC01–RC09 codec/kind schemas, genesis/attestation, payload-before-ACK, revocation/finalize linearization and fenced recovery. | Blueprint; no ledger/transaction implementation. | Immutable observation acceptance, acknowledged data recovery and promotion traceability. |
| DEP08 Security test implementation | ES01–ES32/C4 SEC cases with synthetic transports, deterministic fault schedules, negative outcomes and receipts. | PLANNED; zero ES/SEC cases executed. | Any human/security implementation acceptance claim. |
| DEP09 Exact publication boundary | AB15 exact approved source batch, create-only qualified objects, protected atomic manifest and receipt, current X03/livehash scope. | Blueprint; no batch or promotion. | GT publication; not a circular prerequisite to initial review. |
| DEP10 Scientific development evidence | R03/R06 complete actual event/capture/alias/transform/annotation/exposure registries and eligibility, practical adopted T03 solver and roles. | Synthetic subset implemented; actual corpus/approval/lineage unknown. | Any real split/training, independent-held-out/generalization claim or corpus-specific acceptance. |
| DEP11 Fitted-artifact/OOF registry | CVL05 full trusted artifact DAG and per-inner-model score/fit/selection/cache/initialization provenance. | DEFERRED;17D rejects unverified INNER_OOF calibration. | Model calibration/independence certification; no fitting or cache access occurred. |
| DEP12 Actual runner integration | Selected T02/R04 controller adapter, sensing/confirmation/dwell/fault/latency and estimator/grid/profile evidence. | Commanded actuator helper implemented; actual research-controller integration DEFERRED. | Production runner adoption or real causal evaluation claims. |
| DEP13 Protected execution records | Exact X01 read/probe/hash, X02 checkpoint, X03 publication, X04 EVAL-AUTH, X05 cache, X06 split/training, X07 humanpilot as applicable. | NOT AUTHORIZED; no tokens/records created. | Every corresponding protected action independently. |
| DEP14 Publication/release scope | R07 human authors/disclosure/claims/venue/privacy/license and actual authorized evidence. | PENDING; no manuscript/release change. | External submission, publication or data/code/annotation release. |

## 2. Legal ordering without circular evidence

Future researcher review selects relevant contracts and separately authorizes any next synthetic engineering; that work may implement pure domain/codec/adapters before media or GT exists. Synthetic test fixtures do not need production credentials. Actual review then needs genuine adopted schema/roles/working interface and X01; pilot additionally needs R08/X07. Review must not require its own future promotion receipt. Promotion later needs required independent sources/adapter/current exact batch approval and hash permission. Evaluation later requires its own canonical records/frozen inputs/promoted GT/resource capabilities; a model/cache or publication permit cannot substitute.

Input evidence DAG precedes deterministic payload, verification receipt and authenticated execution receipt; no receipt hashes itself indirectly. Human knowledge, quota and ledger commit advance in the same authoritative transaction, not via independent local files that can diverge. Source/execution trust cannot be supplied by mutable client hashes alone. Unknown artifact availability/trust stops the relevant claim/action; it does not mandate accessing prohibited resources to finish a blueprint.

## 3. Allowed handoff and stop

The current authorization ends after these six documents, the final consolidated report and requested normal Git workflow. No next implementation step or 17F is started. Future scope must name exact modules/tests/fixtures/stop conditions and required researcher choices; protected roles/grants are separate. The dependency register is not an authorization form.

Source status: `docs/generated/master_reaudit/MISSION_17C3_RESEARCHER_DECISION_AND_RELEASE_GATE.md:12-123`; [17D actual evidence](MISSION_17D_IMPLEMENTATION_AND_SYNTHETIC_VALIDATION_REPORT.md).
