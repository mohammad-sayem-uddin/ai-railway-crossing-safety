# Mission 17C-4 — Synthetic test readiness matrix

Date: 2026-11-04, America/New_York. Baseline: `a809fa853e160161cf427a5b84ad96ba400fa92f`. Repository: `/Users/sayemuddin/Desktop/Train_automation`; branch `main`.

Status: candidate acceptance specification for the explicitly requested isolated synthetic work. This document issues no capability, adopts no research protocol, appoints no human and authorizes no protected operation. Researcher decisions R01–R08/T01–T04 remain pending. The current resume instruction separately authorizes the named 17D synthetic implementation after this phase's specification gate; historical C3's X00 status describes its earlier scope. X01–X07 remain unauthorized. Technical prototype choices below do not constitute scientific adoption.

Companions: [gap resolution](MISSION_17C4_ACCEPTANCE_GAP_RESOLUTION.md), [authorization/blinding](MISSION_17C4_AUTHORIZATION_AND_BLINDING_ACCEPTANCE_SPEC.md), [recovery/lineage](MISSION_17C4_RECOVERY_AND_CV_LINEAGE_ACCEPTANCE_SPEC.md), [simulation/calibration](MISSION_17C4_SIMULATION_AND_CALIBRATION_ACCEPTANCE_SPEC.md), [test readiness](MISSION_17C4_SYNTHETIC_TEST_READINESS_MATRIX.md).

<a id="readiness"></a>
## 1. Evidence classes and phase gates

At the 17C-4 boundary all feature cases below are PLANNED, NOT EXECUTED. Specification validation checks requirements, links, source citations and mapping completeness; it is not any security/simulation/CV test pass.17D's report must record exact test command, collected/passed counts, source/fixture scope and results before calling a case executed.17E supplies security blueprints/test plans only; it must not claim SEC execution. Mathematical derivations remain distinct from implemented-feature tests, researcher approval and production acceptance.

| Case | Requirements | Objective oracle | 17C-4 state |
|---|---|---|---|
| SEC01 | AB02/AB08 | Forged handle, alias or missing appointment/elevation approval denies. | PLANNED — NOT EXECUTED |
| SEC02 | AB03–AB06 | Wrong approval digest/project/deployment/protocol/loaded-code manifest denies. | PLANNED — NOT EXECUTED |
| SEC03 | AB05/AB06 | Grant scope not a subset of real approval or missing hash/probe/model/cache privilege denies. | PLANNED — NOT EXECUTED |
| SEC04 | AB07/RC04 | Concurrent reserve/duplicate initialization has one session/winner and exact retry receipt. | PLANNED — NOT EXECUTED |
| SEC05 | AB07/RC06 | Consumed grant after close/abort cannot reserve new session; quotas never reset. | PLANNED — NOT EXECUTED |
| SEC06 | AB06/RC06 | Expired/revoked active/recovered session denies protected use; committed-before-revoke history retained. | PLANNED — NOT EXECUTED |
| SEC07 | AB09 | Actor/event exposure survives alias/session restart; no exposed→blind transition. | PLANNED — NOT EXECUTED |
| SEC08 | AB10 | No candidate/prior-review/queue/log/player leak before permitted independent seals. | PLANNED — NOT EXECUTED |
| SEC09 | AB11/AB12 | Correction keeps original digest/phase, post-comparison correction remains informed. | PLANNED — NOT EXECUTED |
| SEC10 | AB13/AB14 | Distinct second reviewer, all triggers/unknown inputs, separate adjudication and unresolvedUNCERTAIN. | PLANNED — NOT EXECUTED |
| SEC11 | RC01–RC03 | Canonical golden bytes/genesisnull/count/frame/attestation digest directions validate. | PLANNED — NOT EXECUTED |
| SEC12 | RC04/RC05 | Crash at every prepare/journal/append/fsync/commit/ACK boundary has exact durable outcome. | PLANNED — NOT EXECUTED |
| SEC13 | RC06 | Prepare→revoke→commit aborts; commit→revoke preserves history; finalize with prepared returnsBUSY. | PLANNED — NOT EXECUTED |
| SEC14 | RC07 | Fresh fence recovery rejects stale owner; receipt retry never repeats commit. | PLANNED — NOT EXECUTED |
| SEC15 | RC03/RC07 | Rollback/rechain/truncate or mismatched protected count/length quarantines. | PLANNED — NOT EXECUTED |
| SEC16 | RC05/RC07 | Missing local committed body restores only exact trusted bytes; missing journal stops. | PLANNED — NOT EXECUTED |
| SEC17 | RC08 | Unknown external effect blocks finalize; no fabricated exactly-once outcome. | PLANNED — NOT EXECUTED |
| SEC18 | AB15/RC08 | Partial staging never visible GT; exact batch retry idempotent/different-content conflict. | PLANNED — NOT EXECUTED |
| SEC19 | AB01/AB04/AB06 | Alternate direct opener tests selected broker profile; cooperative limitation explicit. | PLANNED — NOT EXECUTED |
| SEC20 | AB01/RC09 | Authority compromise/unavailability never repaired by trusting its own local rewrite. | PLANNED — NOT EXECUTED |
| SIM01 | SC03/SC08 | TC01/02 exact84° commanded fixtures and applied/issued provenance. | PLANNED — NOT EXECUTED |
| SIM02 | SC06/SC08 | All21 C2 exact numeric vectors, including irregular/asymmetric/threshold/cutoff. | PLANNED — NOT EXECUTED |
| SIM03 | SC02/SC04 | Missing/NaN/infinite/bool/negative/off-grid/float timestamp rejects with correct prefix. | PLANNED — NOT EXECUTED |
| SIM04 | SC04 | Duplicate and older arrivals never change accepted count/clock/commands/durations. | PLANNED — NOT EXECUTED |
| SIM05 | SC04 | OFFLINE stable sort and reordering flag; invalid prevalidation has no prefix. | PLANNED — NOT EXECUTED |
| SIM06 | SC05 | Empty/single/origin/before/inside/after cutoff and no future decision activation. | PLANNED — NOT EXECUTED |
| SIM07 | SC02/SC06 | Exact threshold±1e-7/equality and strict float policy/legacy repr adapter. | PLANNED — NOT EXECUTED |
| SIM08 | SC07 | No-op event changes event estimator but leaves fixed-report D_E and D_C unchanged. | PLANNED — NOT EXECUTED |
| SIM09 | SC03 | TargetCLOSED/OPEN continues physical movement; nested-command conflict aborts. | PLANNED — NOT EXECUTED |
| SIM10 | SC09 | Fixed-command identity, initial active command and irregular positive-delta counterexamples. | PLANNED — NOT EXECUTED |
| SIM11 | SC10/SC11 | NONE/scheduled/detect-now profiles, equal-time priority and no next observation. | PLANNED — NOT EXECUTED |
| SIM12 | SC10/SC11 | Rejected-arrival timer behavior, generation cancellation, one-shot and cutoff at due. | PLANNED — NOT EXECUTED |
| SIM13 | SC01/SC07 | Repeated in-memory runs yield identical records/serialization with no IO. | PLANNED — NOT EXECUTED |
| SIM14 | SC01 | No actual controller integration/policy/production result mutation or new protected imports. | PLANNED — NOT EXECUTED |
| CV01 | CVL02/CVL08 | Canonical event aliases, all views/versions/derivatives same indivisible group. | PLANNED — NOT EXECUTED |
| CV02 | CVL03/CVL04 | Capture/camera/crossing/known-or-unknown features and transform/annotation joins preserved. | PLANNED — NOT EXECUTED |
| CV03 | CVL08 | Missing/blank/ambiguous/conflicting/duplicate identities and fallback requests reject. | PLANNED — NOT EXECUTED |
| CV04 | CVL04 | Orphan/cyclic/multi-event derivative and cross-event duplicate identity reject. | PLANNED — NOT EXECUTED |
| CV05 | CVL06/CVL12 | Development/inner train/tune/calibration/control/case/final sibling roles disjoint. | PLANNED — NOT EXECUTED |
| CV06 | CVL09 | M<K and rare required support return INFEASIBLE_NECESSARY without assignments. | PLANNED — NOT EXECUTED |
| CV07 | CVL10/CVL11 | Permutation determinism, label alignment and explicit status/objective semantics. | PLANNED — NOT EXECUTED |
| CV08 | CVL11 | Mixed-label impossible triangle proves exhaustive infeasibility against independent oracle. | PLANNED — NOT EXECUTED |
| CV09 | CVL11 | Budget/size exhaustion never becomes infeasibility/optimality and accepts no assignment. | PLANNED — NOT EXECUTED |
| CV10 | CVL10 | Large constructed synthetic metadata follows greedy work bound without exponential search. | PLANNED — NOT EXECUTED |
| CV11 | CVL12 | Inner subset cannot contain outer evaluation/reserved groups; empty/failed inner plan rejects. | PLANNED — NOT EXECUTED |
| CV12 | SC12–SC15 | Base/preprocessor/calibrator fit and control/outer leakage membership checks. | PLANNED — NOT EXECUTED |
| CV13 | CVL13 | Recomputed asset/annotation/group/coverage validation detects forged result/role changes. | PLANNED — NOT EXECUTED |
| CV14 | CVL07/SC15 | Synthetic IDs only, no real loader/writer; RD024/025 roles/limits preserved. | PLANNED — NOT EXECUTED |
| CV15 | CVL05 | Full general fitted-artifact/OOF evidence DAG is specified for future acceptance;17D subset limitations explicit. | PLANNED — NOT EXECUTED |

## 2. Critical contradiction check

The following decisions are fixed only for the isolated synthetic profile: exact arithmetic/explicit repr float adapter; fixed separate report grid; NONE plus named conditional watchdog profiles with sensor-first equality and one-shot scheduled generations; strict rejection of multi-event descendants; declared heuristic-first/bounded-first-feasible allocator with no optimality claim; explicit base/preprocessor/calibrator fit distinctions. These choices remove ambiguity for that prototype without adopting a real research corpus, science policy, human-role overlap, timeout or protocol. General protected authority and human workflow remain future blueprint acceptance requirements.

The new profile does not promise C2 exhaustive lexicographic optimality: it declares FEASIBLE_GREEDY/FEASIBLE_SEARCH and exact infeasibility only when actually proved. It stops unresolved candidates rather than manufacturing a split. No circular prerequisite requires own future promotion receipt for initial review, nor a final output receipt as its own hashed input. No local hash/lock is called OS isolation. No critical unresolved design contradiction is identified within the bounded profile; future deployment/scientific decisions remain explicit blockers to protected use.

## 3. Exact implementation scope after specification acceptance

Current user instruction names17D and explicitly authorizes isolated synthetic simulation/grouping and their tests. Planned new paths only: `src/railway_detection/synthetic/__init__.py`, `src/railway_detection/synthetic/convention_b.py`, `src/railway_detection/synthetic/grouped_cv.py`, tests under `tests/synthetic_mission17d/`, and the named17D report. Existing runner/controller/splitter/guards/configs/tests/protocols/governance/manifests/results are preserved. No public real-data CLI, file loader or official split writer is added. Tests use objects constructed in code with synthetic namespaces and no image/audio/video/checkpoint/cache fixture.

Run the exact new test directory with plugin autoload disabled, bytecode writes disabled, pytest cache disabled and `--confcutdir=tests/synthetic_mission17d` to exclude repository-root conftest that imports the production CLI. New autouse test safeguards deny resource/file/network/subprocess calls while component tests execute. These safeguards constrain the tested code path and are not a production security sandbox. Inspect imports/source before execution; root/legacy suites are not automatically demonstrated synthetic and will not be run wholesale.

The phase gate requires all implemented module tests and static/source checks to pass; report deferred security/full registry/real integration cases honestly. If a component remains failing, preserve its work and report the valid component separately; do not mark both accepted or move into17E on a false full pass. No research approval/grant is inferred from a passing synthetic suite.
