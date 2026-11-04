# Mission 17F — CV provenance and OOF implementation plan

Date: 2026-11-04, America/New_York. Freshly verified baseline: `8221e96f8de48d995f4397a7e29255cdc8ec50f9`; branch `main`. Mission 17F authorizes source/metadata inspection, isolated synthetic audit tests, these five reports and normal exact-path Git delivery only. No implementation change or protected operation is authorized by this report.

**NOT READY for an official split, fitting or OOF calibration.** The synthetic helper validates supplied metadata and feasible assignments. The actual data/training/cache architecture does not provide the full trusted event/role/artifact/score evidence contract required for independent evaluation. Proposed interfaces and cases below are unimplemented.

Companions: [engineering audit](MISSION_17F_INDEPENDENT_ENGINEERING_AUDIT.md), [controller plan](MISSION_17F_CONVENTION_B_CONTROLLER_INTEGRATION_PLAN.md), [CV/OOF plan](MISSION_17F_CV_PROVENANCE_AND_OOF_IMPLEMENTATION_PLAN.md), [human/security readiness](MISSION_17F_HUMAN_REVIEW_SECURITY_READINESS.md), [gate register](MISSION_17F_IMPLEMENTATION_GATE_REGISTER.md).

## 1. Safe metadata and actual architecture inspected

| Artifact / interface | Observed fact | What it cannot establish |
|---|---|---|
| `data/metadata/vision_v1_metadata.json` | Existing metadata declares 3157 images, estimated 1315 original source images, export augmentation settings and an old validation summary. Dataset role says development_baseline. | Counts and export recipes are not a per-image physical-pass/transform/role/exposure registry. These old counts were read, not independently confirmed from media. |
| `data/splits/705d388743ea/split_summary.json` | Existing split_type=development_fallback, leakage_risk=true, allow_ungrouped_fallback=true, group_field=crossing_id, 1315 group assignments, empty warnings and no error. | Neither field names nor warning absence prove physical-event independence. Its 1315 groups must not be called 1315 known physical passes. No split was regenerated or adopted. |
| `data/manifests/dataset_inventory_summary.json` | Aggregate video/audio inventory and separation rules, version 1.1.0 with recorded 2026-10-07 date. | An inventory is not trusted per-event identity, human confirmation or model exposure evidence. No referenced resource was opened. |
| VisionSample / manifest builder | Optional camera/crossing/session/video/frame/provenance fields. Filename `.rf.` stripping supplies source-image grouping hints; missing grouping may fall back to such a hint. Builder would access images if executed. | A common source image is not necessarily the whole physical pass; nominal augmentation recipe does not reconstruct each applied transform. Builder was text-inspected only. |
| generate_group_split / SplitSummary | Legacy seeded train/val/test ratio splitter over split_group_id, with explicit fallback option; no nested OOF registry. | Cannot be substituted for 17D's canonical-event validator/constraint allocator or an adopted scientific nested-CV plan. |
| train_vision(config, split_summary, backend, ...) | Prepares descriptors, run manifests and backend training/checkpoint paths. Even dry_run writes a dataset descriptor. | Comments about validation-only selection are not authenticated per-artifact fit/selection/initialization evidence. No dry-run/training was invoked. |
| ControlledCacheProvenance | Binds event/source/modality/checkpoint identity/preprocessing/config/injector/timing/schema/software/run and compares candidate with explicit expected identity. | Useful expected-context pattern, but not the complete model initialization/fit/selection/parent artifact and per-inner-model exclusion proof. No cache bytes or checkpoint bytes were accessed. |
| Leakage/preflight checks | Existing path-token/checkpoint/frozen-parameter checks and official-evaluation gates. | Naming/path separation cannot prove unknown upstream exposure or OOF. Preserve existing guards; do not bypass them because a new registry validates. |

Sources: `src/railway_detection/data/contracts.py:43-98`; `src/railway_detection/data/manifest.py:115-156`; `src/railway_detection/data/manifest.py:180-218`; `src/railway_detection/data/split.py:18-172`; `src/railway_detection/vision/trainer.py:45-118`; `src/railway_detection/experiments/cache_provenance.py:625-646`; `src/railway_detection/experiments/cache_provenance.py:923-974`; `src/railway_detection/experiments/leakage_guard.py:118-151`; `src/railway_detection/experiments/preflight_validator.py:1576-1620`.

Read-only metadata inspection is not validation of actual media, annotations, event truth, appointments, scientific eligibility or previous training exposure. No inferred source hash, filename component or synthetic prefix upgrades that status. Full candidate contracts remain [C4 lineage](MISSION_17C4_RECOVERY_AND_CV_LINEAGE_ACCEPTANCE_SPEC.md#lineage) and [C4 calibration](MISSION_17C4_SIMULATION_AND_CALIBRATION_ACCEPTANCE_SPEC.md#calibration).

## 2. Proposed versioned evidence interfaces

| Proposed record / resolver | Required binding and invariant | Rejection boundary |
|---|---|---|
| ExpectedDatasetBinding | Dataset/version/cohort, exact registry digest, evidence authority/provenance/status and adopted role/label/grouping policy | Missing/conflicting/untrusted expected version denies scientific eligibility; caller VERIFIED flag is insufficient. |
| Event/Capture registry | Canonical pass and functional aliases; capture/session/camera/crossing/clock/timebase; labels with confirmed-empty distinction; explicit unknowns | Ambiguous alias, unresolved identity/required metadata or falsely merged separate passes deny affected allocation/claim. |
| Asset/Transform DAG | Original/derivative/annotation joins, frame/PTS, exact applied transform params/version, all parents, generation basis, fitted artifact refs, inclusion/exclusion reason | Orphan/cycle/multi-event composite rejects under current schema; exclusions inherit; no guessed single primary parent. |
| DuplicateEvidence | Exact duplicate or near-duplicate relation, method/version/confidence/evidence/status, approved resolution and canonical event linkage | Cross-event exact conflict rejects; unresolved near-duplicate uncertainty blocks independence. Do not run similarity/media hashing merely to populate this plan. |
| ExpectedAllocationPolicy | K, label support, algorithm/profile/version, objective, limits, grouping/cohesion/role policy and dataset binding | F17-02: compare expected policy independently; no silent relaxed K/label/support/fallback or success-status laundering. |
| AllocationReceipt | Typed assignment/status/objective/work counts, input/policy digest, implementation identity; detached verification/execution receipts | F17-03: bool/float counters/objectives and contradictory status/work reject. Feasible partition verification alone does not prove actual search execution or infeasibility. |
| BoundRolePlan | Dataset+policy+outer assignment digest, outer iteration, inner plan, prospective calibration/refit rule; exact derived sibling roles | F17-01: reconstruct against trusted original inputs; reject internally consistent swaps, foreign-plan reuse or invented development union. |
| FittedArtifact | Kind/model initialization/version/parameters, direct FIT and SELECT event sets, parents, fit execution/evidence status and role plan | Resolve transitive inherited exposure, including preprocessing/early stopping/feature producer. Unknown exposure cannot yield independent-held-out claim. |
| InnerPrediction | Exact scored event/asset and score, generating model/artifact digest, preprocessing and parent refs, outer iteration/inner fold, prediction schema/vocabulary/version | Registry proves model/parent FIT and SELECT exclude scored event; no self-declared OOF boolean or “model trained on another filename” shortcut. |
| Calibration / final composition | Chosen NONE, RESERVED_CALIBRATION or INNER_OOF, frozen method/selection and all contributing score/artifact/event refs; final refit rule | Wrong calibration mode/role/producer or outer outcome use rejects. Final composition must retain full exposure union. |

All record IDs are domain-specific references, not authentication. Codec/schema versions, strict unknown/duplicate-key handling and exact numeric representation require a reviewed common contract; the current ordinary canonical_json is not the complete security RC01 codec. Do not add arbitrary hidden fields to the existing frozen synthetic classes. A new registry/adapter version should leave the bounded prototype and old manifests reproducible until explicit migration is accepted.

Evidence DAG ordering must avoid self-reference: preexisting trusted input evidence→allocation/role payload→validation receipt→authenticated execution/approval receipt. Artifact parents and score-producer references must be acyclic and available. Detached signatures or digests prove only what the independently selected trust service actually authenticates. Import adapters translate safe metadata only after required completeness checks; no default path resolution, fitting or model loading belongs in the pure verifier.

## 3. Nested CV, fitting and OOF acceptance logic

For each outer fold o, independently reconstruct E_o from the frozen assignment and T_o=development minus E_o. Verify exact once-only outer coverage over canonical eligible components. Reserve calibration/control/case/final sets outside that development domain. Inside T_o, derive each prospective inner train/tune pair with complete group/ancestor disjointness and required support. Failure of one inner plan blocks that candidate, not a claim that every nested plan is impossible.

BASE_MODEL_FIT and PREPROCESSOR_FIT use the current inner training set; selection includes tuning outcomes, early stopping/checkpoint selection, threshold/hyperparameter search and any learned preprocessing choice. No outer evaluation event or independent control may enter these operations. Frozen final refit may use the selected outer complement only under a recorded prospective rule; its exposure union remains explicit. Reserved calibration-only data may train the declared calibrator, but not the base/preprocessor or independent evaluation while retaining that role.

For each accepted OOF score on event e, verify: e belongs to the designated inner held-out/tuning role within T_o; producing model and every inherited model/preprocessor/feature parent exclude e from FIT and SELECT; initialization exposure is verified under the adopted claim policy; prediction event/asset/vocabulary/value/version and producer match; and the exact outer/inner assignment and frozen generation procedure match expected bindings. Reject missing, duplicate, foreign-fold or in-sample scores. Repeated-CV scores require a separately declared multiplicity/aggregation contract; do not silently deduplicate or count extra predictions as extra physical events.

Selecting a generating model using e's outcome and then calling its prediction on e “OOF” violates the stated C4 exclusion even if e was not used for gradient fitting. To avoid this, freeze model generation prospectively or use a nested selection scheme whose model for e has no e-dependent selection. Calibrator fitting may use the valid OOF scores/labels as explicitly allowed calibration exposure; that does not make those same cases independent final evaluation. Outer outcomes stay sealed from every development/model-selection/calibration decision until the frozen final pipeline is evaluated once under separate authority.

Reserved-calibration mode uses independently designated calibration-only events and verifies base/preprocessor/producer exposure exclusion and expected policy. NONE fits no calibrator. Case study, reserved control and final descriptive records remain separate; RD024 pooled engine exclusion is not a new detector-training ban or zero-shot claim. RD025 still needs no-train confirmation and event/exposure reporting, not automatic FAR/hour. Unknown historical initialization/training exposure must be reported as unknown and restrict independence claims; access authorization cannot solve missing provenance.

17D currently rejects unverified INNER_OOF calibration, appropriately. It neither produces predictions nor implements the above registries: `src/railway_detection/synthetic/grouped_cv.py:625-667`. No OOF score, fit or real split was created in 17F.

## 4. Future synthetic acceptance plan — planned, not executed

| Case | Challenge | Required result |
|---|---|---|
| PV01 | Wrong registry version/digest/authority, unavailable evidence, self-asserted VERIFIED | Deny trusted eligibility; preserve exact unknown status. |
| PV02 | Alias collision, two views of one pass, multiple passes in one capture | Single canonical group for same pass; reject ambiguity without overmerging unrelated passes. |
| PV03 | Orphan/cycle/excluded ancestor/multi-event derivative, transform-param substitution | Reject; complete immutable DAG and inherited exclusions verified. |
| PV04 | Cross-event exact duplicate and unresolved near-duplicate relation | No independence acceptance until adopted merge/exclusion evidence resolves conflict. |
| PV05 | Weakened support/K/role/cohesion policy with same corpus digest | Reject against expected request, closing F17-02; no automatic fallback. |
| PV06 | Bool/float objective, negative counters, search with 0 nodes, bogus infeasibility receipt | Strict schema/status rejection and separate proof requirements, closing F17-03. |
| PV07 | Coherent control↔training swap or plan from another outer iteration | Recompute original roles and reject, closing F17-01. |
| PV08 | Tiny exhaustive feasibility; known feasible budget/size stops; large greedy fixture | Correct feasible/infeasible/undetermined distinction; no OPTIMAL or complete-search claim beyond evidence. |
| PV09 | Parent model/preprocessor/cache trained or selected on outer/control event | Transitive exposure rejects; sample-ID-only cache checks cannot pass. |
| PV10 | OOF model fitted on e, early-stopped using e, inherited exposed init or unknown parent | Reject each violation/unknown claim; score producer excludes e from FIT/SELECT closure. |
| PV11 | Missing/duplicate/foreign-fold scores, changed vocabulary/model, repeated-score policy absent | Exact coverage/producer/schema checks; no in-sample substitute or silent multiplicity. |
| PV12 | Reserved calibrator, NONE, OOF and final-refit compositions | Enforce mode-specific fit/selection/role exposure and prospective frozen rule. |
| PV13 | Hyperparameter/calibrator choice reads outer outcomes or relabels final descriptive data | Reject; final evaluation remains separated and no approval inferred. |
| PV14 | Serialization roundtrip, stale receipt, expected-policy tamper, IO hook attempts | Canonical schema/domain binding, deterministic identity and zero protected loading in pure verifiers. |

The 17F finite oracles and six negative witnesses are already executed audit evidence, not execution of these fuller future PV cases. Acceptance needs immutable fixtures, exact code/config/commands/results and defect closure review. Implement pure metadata resolvers first only under new scoped authorization; training/backend/resource integration is later and separately gated. R03/R06/T03 select actual eligible corpus, exposure/role/coverage/methodology and claim policy; genuine X06 split and separate training authority plus any X02/X05 resources remain necessary. STOP before implementation or real work.
