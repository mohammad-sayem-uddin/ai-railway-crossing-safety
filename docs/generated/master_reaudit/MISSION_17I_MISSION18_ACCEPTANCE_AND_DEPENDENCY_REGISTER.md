# Mission 17I — Mission 18 acceptance and dependency register

Date: 2026-11-04, America/New_York. Register **17I-18-V1**, baseline `17cc6273544618f0b402a027b41eb527845d3252`. Scope is engineering remediation/contracts only. **Mission 18 has not started and is not authorized by this document.** The same assistant authored the related work; this is not independent human approval.

Sources: [17I remediation](MISSION_17I_FINAL_ENGINEERING_REMEDIATION_REPORT.md), [17I-CB-V1](MISSION_17I_CONVENTION_B_INTEGRATION_CONTRACT.md), [17I-CV-V1](MISSION_17I_GROUPED_CV_INTEGRATION_CONTRACT.md), [17E release checklist](MISSION_17E_RESEARCHER_RELEASE_GATE_CHECKLIST.md). Rows distinguish verified component prerequisites from unimplemented adapters and researcher decisions. Writing a contract does not satisfy its integration requirement.

## 1. Dependency map and scope

The staged sequence recommended for review is:

1. Researcher reviews 17I, selects bounded engineering scope and resolves the static-analysis environment gate or explicitly records a limited synthetic-stage disposition. No dependency installation or waiver is made here.
2. The future caller owns immutable constructed fixtures and retained expected inputs, explicit workload limits and deterministic failure handling. Shared engineering rows E01–E04 apply to both missions.
3. **Proposed 18A** implements/test-drives an isolated synthetic coordinator/adapter under CB01–CB12. **Proposed 18B** implements/test-drives constructed provenance adapters under CV01–CV12. Neither implies production default routing. These names define this proposed handoff; no separate accepted Mission 18 scope is assumed.
4. Scientific, governance, human-review and protected-data gates remain independent prerequisites for later use. A passing adapter cannot grant them.

Legend: **YES-component** = current helper behavior has executed evidence; **PARTIAL** = specified or some helper evidence, integration remains unimplemented; **NO** = missing implementation/external decision. Every future test ID Axx/Bxx/Exx/Pxx below is **planned and unexecuted** as an integration test unless explicitly identified as a current component test. No row claims integration completion.

## 2. Shared engineering prerequisites

| ID / category | Source contract | Target | Required input → output | Validation / failure behavior | Required synthetic test | Unresolved dependency / researcher decision | Currently satisfied? |
|---|---|---|---|---|---|---|---|
| E01 Engineering isolation | CB01,CV01,CV11 | Future test harness | Constructed objects → isolated adapter execution | Deny loader/file/network/process routes; unexpected IO fails | E01: guards plus absent production/decoder imports | Exact adapter/test scope must be authorized; no OS sandbox inferred | YES-component: six isolation cases; NO-adapter |
| E02 Engineering expectation ownership | CB09,CV09 | Owning fixture/coordinator | Independent ordered input, policy/config/code identity → bound candidate | Never derive expectation from candidate; substitution rejects | E02: replace candidate only and both candidate/expected; expose trust limit | Select owner/lifetime/nonmutation/bounds; authenticity external | PARTIAL: helper comparisons exist; owner absent |
| E03 Engineering static analysis | 17I remediation H-N02 | Existing tool environment | Scoped source/tests → lint/type results | Ruff zero; Mypy must actually analyze before type-pass claim | E03: exact tool commands on adapter changes | Mypy missing bogus_type; environment repair separately authorized, or explicit limited-stage researcher disposition | Ruff YES; Mypy NO |
| E04 Engineering workload/resource bounds | CB10,CV10 | Future orchestrator | Explicit N/S/R/registry/K/budget/query bounds → bounded chosen work | Exceed selected resource envelope explicitly; never silently relax scientific constraints | E04: operation counts, memory shape, repeated-call budget exhaustion | Researcher chooses intended scale; engineering selects explicit test envelope | PARTIAL: component scale evidence, no adopted integration envelope |

## 3. Proposed Mission 18A acceptance

| ID | Source contract | Target component | Required input → expected output | Validation / failure behavior | Required synthetic test | Unresolved dependency / researcher decision | Currently satisfied? |
|---|---|---|---|---|---|---|---|
| A01 | CB01,CB03,CB11 | Future B coordinator | Constructed decisions/frames + previous active command → advance-before-issue ledger | One controller call at selected boundary; preserve historical A; reject unmapped/conflicting command | A01: A/B command parity and independently derived angles/call counts | E01–E04; select actual runner, call boundary and state ownership; pending researcher choice | NO adapter; actuator YES |
| A02 | CB02,CB04 | Time/order adapter | Original tick/decimal/float + chosen mode → exact µs, accepted/rejected sequence | No silent rounding; preserve input identity and rejection priority; invalid conversion fails | A02: 0.2,3*0.2,None,bool,duplicate/older/equal,OFFLINE future invalid | Clock/migration and rejected-decision mapping pending | PARTIAL: helper conversion/rejection tested |
| A03 | CB04 | Horizon/failure coordinator | Empty/single/partial/extended input + cutoff → correct status/prefix/horizon | No fabricated sensor or successful prefix; reject nonspanning grid | A03: each horizon and failure row, interruptions | Select adapter exception propagation and partial-ledger retention | PARTIAL: helper tested, coordinator absent |
| A04 | CB05,CB06 | Dynamics/metric adapter | Exact rates/angle/config/report grid → separate endpoint/continuous/fixed metrics | Strict≤45,clipping,correct origin/effective times; unsupported config fails | A04: thresholds,asymmetric rates,no-op subdivision,A/B counterexamples | Scientific estimator and physical-state mapping pending; no threshold changes | PARTIAL: helper oracles pass |
| A05 | CB07 | Timer/decision mapping | Explicit selected profile → priority/generation/requested/applied log | NONE baseline; nonadopted timers cannot become automatic policy | A05: equality,cutoff,reject,one-shot,detect/no-next | Researcher adoption of watchdog policy remains pending | PARTIAL: synthetic profiles tested; adoption NO |
| A06 | CB08,CB09 | Run evidence adapter | Retained code/input/config + candidate result → complete verified envelope | Configuration-only pass insufficient; detached fake values reject at adapter | A06: fake angle/duration,swapped settings,input/order/code mismatch,reset | Full run envelope/verifier not implemented; expected owner required | NO; config verifier only |
| A07 | CB10,CB12 | Synthetic integration harness | Sized constructed cases → deterministic outputs/work receipts | Default reuse; fixed O(S+R),O(1) helper objects; no prohibited IO | A07: grids,repeat runs,scaling,independent numeric oracle | Adapter and E04 scale limits; no real replay | YES-component; NO integration |

## 4. Proposed Mission 18B acceptance

| ID | Source contract | Target component | Required input → expected output | Validation / failure behavior | Required synthetic test | Unresolved dependency / researcher decision | Currently satisfied? |
|---|---|---|---|---|---|---|---|
| B01 | CV01–CV03 | Constructed registry adapter | Event/capture/camera/crossing/assets/annotations/transforms → canonical registry | Reject missing/ambiguous/orphan/cyclic/cross-event duplicate joins; no silent merge | B01: identity aliases,duplicate contents,multi-generation lineage,unknown metadata | E01–E04; authentic real identity evidence later; corpus decisions pending | YES-component; NO adapter |
| B02 | CV04,CV08 | Role/provenance adapter | Independently retained original roles/outer/inner choices → RolePlan | Exact roles,nonempty training,disjoint reserved sets; coherent swap rejects | B02: reserved derivative,all sibling roles,selection/producer contamination | Prospective scientific roles/independence decisions pending | YES-component; no scientific approval |
| B03 | CV05,CV07 | Allocation request/receipt adapter | Original policy + source + receipt → deterministic acceptance/False/error | No candidate-derived expectations,policy reuse,bool counters or fallback | B03: all six outcomes,forged assignments/objective/work,foreign policy | Explicit K/support/budget/profile selection, no official split writer | YES-component; NO adapter |
| B04 | CV06,CV10 | Verification orchestration | Sized registry + Q proposals → fresh validation/recompute per call | One registry/solver per call; budget stop stays undetermined; mutation rejects | B04: per-call counts,stale context,tiny exhaustive oracle,large greedy input | Repeated solver cost remains; workload choice E04 | YES-component; NO integration |
| B05 | CV08,CV09,CV11 | Future fitted-artifact/exposure registry | Constructed producer/fit/selection/initialization DAG → complete exposure evidence | Unknown or missing producer lineage denies; metadata claim alone insufficient | B05: ancestor contamination,initialization reuse,selection and cache producer swaps | Registry not implemented; scope and schema separately authorized; real evidence later | NO |
| B06 | CV08,CV11 | Future inner-OOF provenance verifier | Constructed held-out scores + producing models/fit memberships → verified OOF lineage | Reject self-predictions,outer influence,foreign score/model,unverified calibration | B06: each score held out from full producing ancestry | No OOF verifier/score registry or calibrator fitting; future scope required | NO; current denial YES |
| B07 | CV12 | Synthetic-only integration harness | Controlled registry/policy/evidence → reproducible in-memory output | No real loader,writer,fit,predict,calibrate or official-manifest route | B07: all negatives/positive controls,determinism,IO guards | Adapter engineering authorization pending; no protected authority | YES-component; NO integration |

## 5. External prerequisites, separated by domain

| ID / category | Source | Target | Required input → expected output | Validation / failure behavior | Synthetic test required | Unresolved dependency / researcher decision | Currently satisfied? |
|---|---|---|---|---|---|---|---|
| P01 Scientific | CB02,CB05,CB07,CB11 | Research protocol/runner adoption | Researcher selected time/order/dynamics/estimators/watchdog → adopted versioned choices | Missing decision blocks scientific adoption; do not infer from defaults | P01: synthetic parity demonstrates only selected behavior | Actual runner/clock/estimator/safety choices pending | NO |
| P02 Scientific | CV02–CV06,CV09 | Corpus/split eligibility | Actual identity/labels/roles/exposure and chosen policy → justified scientific eligibility | Missing evidence blocks official split/evaluation; event grouping alone insufficient | P02: mock missing-evidence refusal, no real corpus access | Corpus/camera independence,duplicate handling,prospective roles and exposure pending | NO |
| P03 Governance | 17E checklist; CB09,CV09 | Approvals/appointments | Authentic researcher decisions,adopted protocol/schema,qualified appointments → valid governed scope | No self-created approval; unadopted proposal blocks release | P03: planned security/dependency checks only | v7.1.1 proposed; OptionC unapproved; pending R/T subjects and RD001–RD055 unchanged | NO |
| P04 Human-review | 17E checklist | Review/blinding/adjudication/publication | Genuine reviewer qualifications/roles,blind process,ledger/recovery → governed review workflow | Missing blinding/authority/recovery services blocks human review | P04: 17E security cases remain planned/unexecuted | Human-review infrastructure/appointments not implemented here | NO |
| P05 Protected-data authorization | 17E checklist | Any real-resource access or execution | Authentic scoped authority,verified runtime/resource binding → permitted named operation | Missing authorization denies before media/checkpoint/cache access | P05: future deny-before-access tests, no credentials issued here | X01–X07 remain unauthorized; no reusable capability | NO |

All protected work also requires applicable scientific/governance/human prerequisites; the table does not imply each protected operation requires an identical workflow. Researcher decisions must specify its exact dependencies. No approval, signature or identity is fabricated.

## 6. Test strategy, readiness and stop

Current executed evidence is the 17I component suite: 238 passing cases, including 22 new cases, all original 216 retained, six isolation tests and six former rejection failures still ordinary tests. Ruff scoped check passes; Mypy startup fails, so static type analysis is unresolved. These facts satisfy bounded 17I investigation/remediation gates, not an integration pass. Exact staged receipt belongs in the remediation report.

Proposed synthetic acceptance: start with positive fixtures and deliberately mismatched expected inputs, assert exact exceptions/status and no accepted output on rejection, compare independent numerical/tiny exhaustive oracles, instrument actual validation/scoring/traversal operations, test fresh calls/reset and changed contexts, and preserve no-IO safeguards. Run staged-state tests and explicit diff review at each future delivery. Do not replace selected failure assertions with missing-argument errors. Human/security cases and authentic real-resource tests are outside these executed counts.

**18A readiness:** contract-defined and conditionally implementable using constructed fixtures after researcher review, explicit scoped authorization, selected coordinator/clock/metric policy and recorded disposition of E03/E04. No production readiness or controller integration acceptance.

**18B readiness:** current constructed grouping/receipt/role adapters are conditionally implementable under the same review/authorization/ownership/static/workload conditions. Full fitted-artifact and OOF provenance readiness is NO until B05/B06 are separately designed, implemented and tested. No official split, fitting or real calibration is authorized.

**Mission 18 may not begin automatically.** Deliver 17I, stop for researcher review, retain all pending decisions and protected boundaries. Document completeness freezes the engineering questions and expected tests; it does not turn pending external facts into completed requirements.
