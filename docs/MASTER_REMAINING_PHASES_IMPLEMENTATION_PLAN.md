# Master Remaining-Phases Implementation Plan — Phase 11.11 through Phase 16

**Status:** Planning artifact only. This document authorizes no adjudication, record disposition, promotion, evaluation, field activity, publication, Git staging, or implementation. It records repository state observed on **2026-10-16** and consolidates the existing phase plans with the governing research design. Re-verify mutable state immediately before any later execution.

**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Observed branch / HEAD:** `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Scope:** bounded closure of Phase 11.11–11.12 preparation and execution gates, followed by Phases 12–16. Prior completed engineering is not to be reimplemented merely because it appears in an older phase plan.

---

## 1. Executive summary

The next substantive research activity is **not evaluation**. The repository has review-support code, a synthetic pilot, a schema, promotion/readiness controls, and an approved-records-only loader, but it has **no genuine Stage-2.1 review record** and no researcher authorization to begin adjudication. The 27 existing review JSON files are schema `6.0.0` (not `7.0.0`), say `APPROVED`, and are not valid Stage-2.1 ground truth. The readiness gate correctly blocks them.

The practical critical path is:

1. Reconcile stale/missing Phase 11 closure artifacts and preserve the existing local worktree.
2. Obtain the remaining researcher decisions and explicit, separately scoped authorizations; do not interpret this plan or a prior broad campaign authorization as any of them.
3. Complete and test a human-operated adjudication session runner using **synthetic fixtures only** before it can write a real record.
4. If separately authorized, perform researcher-led review; keep uncertain/censored/site-survey-blocked boundaries explicit and preserve all 27 legacy files.
5. Reconcile records and legacy disposition; satisfy the clear-boundary audit decision; obtain a mechanically evidenced readiness verdict naming the evaluation stage.
6. Only after a separate `EVAL-AUTH`, freeze the event split, synchronization scope, metric preregistration, and run manifest, then execute Phase 12.
7. Run Phases 13 and 14 as separately authorized, evidence-dependent software studies. Phase 15 remains passive-observation planning only unless extensive independent approvals are obtained. Phase 16 communicates only claims traceable to verified artifacts and requires a separate release decision.

No numeric review-time threshold, second-review tolerance, audit sampling rate, event split, synchronization acceptance, or safety criterion is chosen by this plan.

---

## 2. Repository audit snapshot and evidence boundaries

### 2.1 Directly verified in this planning run

| Item | Observed state | Evidence / interpretation |
|---|---|---|
| Git state | HEAD `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`, branch `main`, tracking `origin/main`; 14 modified tracked entries and 230 untracked entries; no changes staged | `git rev-parse`, `git status --short --branch`, porcelain count. All are pre-existing and must be preserved. This plan is intended to be the only new file from this planning run. |
| Existing master-plan target | Absent before this run | `docs/MASTER_REMAINING_PHASES_IMPLEMENTATION_PLAN.md` did not exist at audit time. |
| Legacy review records | Exactly 27 JSON review records: 23 train, 3 no-train, 1 engine. Spot checks and a full JSON field count showed `schema_version: "6.0.0"`, `adjudication_status: "APPROVED"`, reviewer metadata `human_researcher_lead`; none is a Stage-2.1 record | The status string in a legacy file is not human approval evidence and does not pass the current `8.1.0-stage2.1` schema/loader. Three sampled file hashes match the Phase 11.1 baseline hashes in the decision register. No Stage-2.1 record or invalidation notice was found. |
| Phase 11.8 / 11.9 | `annotation/review_session.py`, integration/pilot tests, and pilot report exist. The helper validates constructed records and computes observed media hashes; it is a **record-construction helper**, not a human-operated session runner. Pilot uses synthetic media and is not genuine review-duration evidence. | Source, tests, and `docs/PHASE11_9_SYNTHETIC_PILOT_REPORT.md`. |
| Phase 11.10 | **Resolved 2026-10-16.** The report's original claim was inaccurate when written, but `docs/PHASE11_10_DECISION_CLOSURE_PACKAGE.md` has since been reconstructed from traceable repository evidence and is present. The on-disk legacy schema discrepancy is reconciled as `6.0.0`, with all 9 affected citations inventoried by file and line. | Deliverable gap closed; the report and reconciliation were corrected additively. D1's numeric values and D3(c)'s audit mechanism remain `PENDING_RESEARCHER_DECISION`. |
| Research decisions | Decision register v1.2.0 records D1 mechanism (fast-session second review) but leaves its numeric floor/band unset; D3(a) conceptual B+C triggers are recorded but concrete workflow mechanics remain to be implemented; D3(c) clear-case audit mechanism/frequency remains pending. Allowlist and review/promotion-time media re-hashing controls are implemented. | `docs/PHASE11_3_RESEARCHER_DECISIONS.md`, Phase 11.7 report, code, and absence tests. |
| Phase 11.11 | Protocol exists; explicitly says no adjudication, no Stage-2.1 records, no ADJ-AUTH. No `adjudication_session.py`, review-order manifest, or Phase 11.11 execution report is present. | Source/script/test search and protocol. |
| Phase 11.12 | `evaluation_readiness_gate.py` and tests exist; report says gate is NOT_READY on repository records. No real record was promoted. | Gate source, `tests/test_phase11_12_readiness_gate.py`, closure report. Existing interface accepts supplied record data/registries; future integration must never treat self-reported metadata as proof. |
| Phase 12 | Approved-only loader and its tests exist. No Phase 12 evaluation runner, Phase 12 event-metric implementation tied to the approved loader, or Phase 12 output run was found. The report correctly says no evaluation/metrics have run. | `ground_truth_loader.py`, `tests/test_phase12_ground_truth_loader.py`, Phase 12 report, source/script inventory. Existing generic `metrics.py` and `ExperimentRunner` are not proof of a valid Phase 12 evaluation. |
| Phases 13–16 | Phase 13/14 reports say blocked; no dedicated Phase 13/14 execution modules or runners were found. Phase 15 protocol and Phase 16 manuscript are drafts/skeletons, not completed validation or publication. | Phase reports and source/script inventory. |
| Split artifact | `data/splits/705d388743ea/` exists, but identifies itself as `development_fallback`, `leakage_risk: true`, and permits ungrouped fallback. It is an image-development split, **not** a researcher-approved event-level evaluation split. | `split_summary.json`, `run_manifest.json`. Never reuse as Phase 12 split. |
| Frozen artifacts | `configs/frozen_experiment_v1.yaml` loads to canonical hash `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`; configured vision and audio V3 checkpoint hashes verify. Audio V2 hash is separately marked prohibited. | Canonical config loader and live checkpoint-integrity check passed. Do not infer that all old reports/cache outputs are valid from this verification. |
| R04 synchronization | Frozen config retains `independent_or_unverified`, `R04_UNRESOLVED_REQUIRES_EMPIRICAL_OFFSETS`, and `allow_unverified_zero_offset: false`. Candidate offset manifest has not received human visual-landmark review. | Config and `data/manifests/camera_sync_offsets_candidate.yaml`. Do not merge streams or claim fused results on an unaccepted offset. |
| Existing test environment | `.venv` Python 3.11.15 is available. A focused 57-test baseline passed across decision-default absence, Phase 11.8 integration, Phase 11.9 pilot, Phase 11.12 gate, and Phase 12 loader tests. The entire suite was **not** run in this plan-only audit. | `PYTHONPATH=src .venv/bin/python -m pytest ... -q` → 57 passed. |
| Existing local change risk | Many project/config/data/experiment files are untracked or modified; this includes the frozen configs and numerous research artifacts. Their presence does not make them safe to overwrite, stage, or attribute to this plan. | The worktree has a substantial pre-existing recovery state. Preserve exact bytes and scope all later work to explicit paths. |

### 2.2 Important source-of-truth rules

1. The governing endpoint and scientific design is `docs/EXPERIMENT_DESIGN_FINAL.md`, subject to still-pending researcher-only decisions. Its scope is a software replay study on these recordings, **not** a physical safety or certification study.
2. The canonical frozen experiment identity is the loader-computed canonical hash, not the raw YAML byte hash quoted by older documents. Every later run must record both the exact file hash and canonical config hash and explain which is used for integrity checks.
3. The existing `metrics.py`, B0–B7 runner, caches, summaries, reports, and figures predate the approved-ground-truth Phase 12 contract. Treat their results as historical/diagnostic, not Phase 12 evidence, unless a separately authorized audit proves a specific artifact usable under the metric contract.
4. `docs/PHASE12_16_RESEARCH_CONTRACTS.md` explicitly describes metadata-only checks. A passing helper or caller-supplied boolean is not evidence of a real prerequisite, human approval, or authorization.
5. `docs/INDEPENDENT_MASTER_AUDIT.md` and `docs/FINDINGS_REGISTER.csv` identify substantial evaluation, fusion, cache, synchronization, and claim-validity defects. Those are relevant design constraints and must be checked against current code before the affected experiment; they do not grant authority to redesign the frozen policy or claim that every finding remains unchanged.

---

## 3. Scope, invariants, and non-authorizations

### In scope for the coordinated campaign

- Prepare and verify a real-researcher-operated Phase 11.11 workflow, perform adjudication only under a distinct, explicit `ADJ-AUTH`, and perform Phase 11.12 reconciliation/readiness work.
- Build and test evaluation tooling without computing formal Phase 12 metrics before a distinct `EVAL-AUTH` and readiness verdict.
- Following separate authorization at each phase boundary, run Phases 12–14 software experiments; prepare Phase 15 passive-observation documents; prepare Phase 16 evidence-grounded manuscript/release materials.

### Invariants that every work package must preserve

- No model output, proposal timestamp, existing legacy review value, or generated candidate is substituted for the researcher's own raw-media observation.
- No edit, rename, deletion, or disposition of the 27 legacy review files. The recorded researcher selection is full-scope sibling invalidation notices with originals preserved, but execution remains separately gated by `LEG-EXEC` and the reviewed hash-bound dry run.
- No Stage-2.1 record is auto-approved, no batch stamping, no gate override, and no “force” path. A software gate can report mechanical readiness; only the researcher can approve records or authorize evaluation.
- Preserve all four boundary states, censoring direction, reviewer rationale, provenance, history, and exact reviewer-observed media hashes. Do not turn censored/uncertain/not-applicable into numeric values.
- Do not change the frozen configuration, checkpoints, frozen thresholds, or baseline policy as part of Phases 12–14. Candidate policy work stays separately named, scoped, and authorized; it is not silently substituted for the frozen baseline.
- Never use Audio V2. Never use a zero-offset or unreviewed camera offset as if verified. Keep independent-camera and R04-supported analyses distinct; publish no dual-camera conclusion without the prespecified human acceptance.
- No live railway control, actuator connection, deployment, unsupervised field test, or safety-certification claim. Phase 15 planning is passive-observation only and does not authorize site access or data capture.
- No staging, commits, pushes, or cleanup of existing user changes as part of the campaign unless separately and explicitly authorized.

This planning run created no authorization token, record, notice, model output, evaluation result, or site permission. A plan, prior “engineering scope” authorization, test pass, or metadata checklist is not ADJ-AUTH, LEG-EXEC, EVAL-AUTH, human record approval, or site permission.

---

## 4. Researcher-only decisions and external gates

These are intentionally **not resolved** here. Technical work can make options and evidence reviewable; it cannot choose on the researcher's behalf.

| ID / decision | Current state | What must happen / what it blocks |
|---|---|---|
| R-D1: review-duration mechanism values | Mechanism selected in the register: pilot-derived hard floor plus “fast but passing” second-review band. Numeric values are unset; the synthetic pilot did not measure human review. | Researcher reviews initial genuine-session timing evidence and explicitly sets or defers the values before relying on duration-based promotion. No numeric value is invented by the runner. |
| R-D3(a): concrete second-review workflow | Conceptual B+C recorded: second review for UNCERTAIN boundaries and the fixed issue-register subset; no tolerance. Concrete state transitions, assignment, matching, and resolution remain to be tested/operationalized. | Researcher confirms implementation semantics before triggered real reviews. No numeric agreement tolerance or automated tie-breaker. |
| R-D3(c): audit of clear boundaries | Pending; no audit mechanism or frequency exists. | Researcher selects the auditable sampling/check mechanism and frequency before any affected clear-marked boundary is treated as promotion-ready. |
| R-DISC1: schema-version discrepancy | Phase 11.10 report correctly says on-disk legacy record version is `6.0.0`; several older documents still state `7.0.0`. | Make a read-only citation inventory and additive correction/supersession memo. Required before executing any hash-bound legacy disposition; do not silently rewrite historical documents or baseline evidence. |
| R-LEG / LEG-EXEC: legacy disposition | Scope/mechanism selection is documented (all 27; sibling notices; originals untouched). Execution is explicitly **not authorized**. | Researcher reviews the exact dry-run proposal/hash and separately authorizes execution. If declined, record that choice and treat legacy records as unusable; never imply they are Stage-2.1. |
| R-ADJ / ADJ-AUTH: genuine adjudication | Not granted; scope must name events/boundaries and review arrangement. | Separate affirmative authorization, with scope, reviewer(s), and participation. No real session, review-order manifest, or review record before it. Repository identity strings are not cryptographic authentication. |
| R-SPLIT: evaluation split | No event-level split selected. The existing `705d388743ea` split is a leakage-risk development image split. | Researcher approves disjoint event ID assignments and intended estimand before Phase 12 preregistration/execution. Never split frames or reuse the existing development split. |
| R-R04SCOPE / D-3: synchronization | Current R04 evidence is candidate-only and lacks visual landmark acceptance; frozen config forbids unverified zero-offset fusion. | Researcher determines dual-camera event scope using the governing protocol's calibration and human-review requirements. Until accepted, use only protocol-permitted independent-stream analyses and label cross-stream metrics not evaluable. |
| R-EVAL / EVAL-AUTH | Not granted; no formal stage has been named. | After 11.12 evidence, researcher separately names the stage, population, conditions, endpoints, and authorized execution window. No metrics/replay on ground truth before this gate. |
| D-7 / negative-control status | The three no-train clips require researcher confirmation if claims depend on them being truly train-free. | Confirm from raw media and document the signed/researcher-attributed conclusion before nuisance-closure evaluation; otherwise report them as unconfirmed and do not count them as negatives. |
| D-8: annotation agreement/tolerance | Governing design specifies a second annotator on at least 8 train events or a disclosed 0.5 s fallback; this is a researcher choice, not automatically satisfied. | Decide before interpreting timing agreement. If no second annotator, explicitly document the fallback and its limitation. |
| Site survey / new data | Fourteen issue-register rows are described as site-survey-blocked; no site operation is authorized. Dataset is short and left/right-censored for many endpoints. | External site/landowner/rail authority permission and researcher decision are required before any survey or collection. Keep rows UNCERTAIN/CENSORED when evidence is absent; do not fabricate observability. |
| Phase 14 target hardware | No target platform specification supplied. | Researcher supplies a target or explicitly authorizes an assumption. Otherwise report only measurements on the inspected host; no real-time feasibility claim for another platform. |
| R-PUB / release choices | Venue, authorship, public data/code scope, and privacy/ethics decisions are open. | Researcher approval before public release or publication. No raw video, personal data, or site-identifying detail is released by default. |
| Phase 15 data capture | Protocol draft is not site authorization; site access, approved safety case, and ethics/privacy requirements are not evidenced. | No field capture until every required external permission and researcher go/no-go is documented. Scope remains passive and offline; no actuator/control interface. |

---

## 5. Work packages, dependencies, deliverables, and acceptance

“Engineering-ready” means only that bounded code/docs/tests can be worked on after implementation authorization; it never means the underlying research operation is authorized.

### WP0 — Planning artifact and baseline preservation (this run)

- **Work:** Create this consolidated plan only; preserve all pre-existing tracked modifications and untracked files.
- **Acceptance:** This file is readable; `git status` shows no staging and the same pre-existing changes plus only this new plan; no other repository path changed by this planning run.
- **Status:** In progress until this plan and preservation check are verified.

### WP1 — 11.10/11.11 protocol and authorization closure

- **Dependencies:** WP0; read-only inventory of the actual 27-event review inventory, active proposal versions/hashes, issue register, media, and current decisions.
- **Work:** Reconcile the missing Phase 11.10 decision package and outdated `7.0.0` references additively; close researcher decisions that block the intended review path; specify review scope and exact gates. Resolve ambiguity between the protocol's “tooling may be built” language and its runner's “deferred until ADJ-AUTH” table by obtaining an explicit engineering-only authorization boundary if the synthetic runner is to be built before ADJ-AUTH.
- **Deliverables:** Additive 11.10 closure/supersession memo; a versioned, human-reviewed Phase 11.11 protocol amendment if needed; decision/authorization checklist (no signatures fabricated).
- **Acceptance:** All pending decision markers inventoried; exact researcher actions and stop conditions enumerated; legacy record `6.0.0` truth consistently distinguished from Stage-2.1 schema `8.1.0-stage2.1`; zero legacy file mutations; no selection/default inserted without researcher confirmation.

### WP2 — 11.11 synthetic-only session runner and workflow audit

- **Dependencies:** WP1 design; implementation authorization for code changes. No real adjudication authority implied. If ADJ-AUTH is not granted, use synthetic fixtures/temp directories only.
- **Work:** Implement a human-operated, one-event-at-a-time session tool around `annotation/review_session.py`; load only an allowlisted event and its currently active proposal reference; live-hash the exact raw media before and after review; use monotonic timing and attributable UTC timestamps; keep media viewer/manual boundary entry separate from model outputs; validate a full schema record; show a preview and require an explicit human confirmation before any permitted write. Enforce atomic per-record writes to an explicitly supplied test or authorized output root. Implement the researcher-confirmed D3(a) trigger/state flow only after its concrete semantics are approved. Do not silently implement D1 numeric thresholds or D3(c) audit frequency.
- **Expected additive artifacts:** `src/railway_detection/annotation/adjudication_session.py`; focused tests under `tests/`; synthetic workflow fixture/report. Real review-order manifest or record writes only under their separate authorization and human action.
- **Acceptance:** Synthetic event only can be exercised end-to-end; no real review path writable by default; no duplicate event/session write; unknown event/proposal rejected; allowlist failure rejected before session; media change aborts; model-output paths are inaccessible/refused; four-state completeness/rationale enforced; left/right censoring retained; no proposal numeric field copied into adjudication; write cancellation leaves no partial file; history/record schema validation passes. Run existing 11.8/11.9 and absence tests.
- **Stop:** Any path that can ingest model outputs into the review UI, any hash mismatch, or any unconfirmed policy value blocks real-event use.

### WP3 — 11.11 researcher-led review (human execution, not autonomous implementation)

- **Dependencies:** WP2 acceptance; D1 interim/approved handling and D3(a) behavior specified for the review scope; researcher ADJ-AUTH naming scope; current reviewer allowlist; researcher participation; legacy disposition handled according to explicit decision. These conditions are not met in the audit snapshot.
- **Work:** Researcher reviews raw media personally in the documented order (engine event, three negatives, then train events by duration, unless the authorized scope says otherwise). For each event independently choose OBSERVABLE / UNOBSERVABLE_NOT_APPLICABLE / CENSORED / UNCERTAIN for T0–T4 and scene clear, provide rationale and frame/camera evidence, listen for audio only if in the approved scope, and attest to independence. Apply the researcher-selected disagreement procedure; retain unresolved states rather than forcing consensus. Record genuine session duration to inform, not automatically determine, D1.
- **Deliverables:** Individually confirmed Stage-2.1 records and a per-batch session/integrity log, only as a direct result of researcher action under ADJ-AUTH.
- **Acceptance:** Each record corresponds to one authorized event; reviewer allowlisted; live media hashes match at review and later promotion; no model output consulted; schema/history valid; exact original legacy hashes preserved; all unresolved boundaries remain in the register; review count equals authorized completed sessions.
- **Stop:** Authorization withdrawal; hash mismatch; workflow/firewall defect; disagreement trigger undefined; >50% UNCERTAIN in a batch per current protocol stop rule; any record not personally confirmed.

### WP4 — 11.12 reconciliation, disposition, and readiness gate

- **Dependencies:** WP3 records for authorized scope; R-D3(c) resolved for any clear boundary to be promotion-ready; R-DISC1 reconciliation; R-LEG executed under separate authorization or explicitly declined; independent hashes/provenance available.
- **Work:** Reconcile every in-scope event against the event inventory and session log; verify schema, status/history, current allowlist, active proposal hash, reviewer-observed and live media hashes, duplicates, legacy references/supersedes, and unresolved/censored states. Produce a complete unresolved-boundary register, including the 14 site-survey-blocked rows without upgrading them. Run the gate against actual evidence; fix interface gaps only in a separately authorized change, not by caller assertions. Promotion, if needed, is per-record and separately confirmed; a READY verdict is not itself approval.
- **Deliverables:** Complete Phase 11.12 closure report, event-level reconciliation and unresolved register, independently evidenced gate verdict for a **named stage**, and append-only integrity record.
- **Acceptance:** 100% of authorized event IDs have a reconciliation row; no duplicate event approvals; all promoted records pass actual `validate_for_promotion`; each failure has a stable blocker; gate remains NOT_READY on empty/legacy/missing-cohort/disputed/hash-mismatch/unauthorized cases; synthetic positive path passes. No metric run. Preserve legacy originals and frozen artifacts.
- **Stop:** Any provenance/hash mismatch, unresolved record represented as resolved, missing audit evidence, inconsistent gate rejection code, or incomplete scope accounting.

### WP5 — Phase 12 evaluation/benchmarking

- **Dependencies:** WP4 mechanically complete; stage-specific READY evidence; separate EVAL-AUTH; researcher-approved event split and R04 scope; negative controls confirmed if used; metric preregistration signed/frozen before computation; current frozen config/checkpoint verification; current code/findings audit demonstrating the replay path can produce interpretable outputs.
- **Workstreams (parallel only after shared preregistration):**
  1. Harden integration of `ground_truth_loader.py` so it consumes only exact approved/promotion-validated Stage-2.1 records; reconcile loader and gate source boundaries; fail closed on legacy files, unexpected JSON, duplicates, unapproved/disputed records, and non-observable metric inputs.
  2. Implement event-metric records from `EXPERIMENT_DESIGN_FINAL.md` §8: value/status/reason, total/applicable/evaluable denominators, excluded-event reasons, censoring, no clamping, signed lead times, and undefined zero-denominator representation. Existing generic metrics are not accepted without demonstrating contract conformance.
  3. Create immutable event-level split manifest and leakage audit. The existing image split is explicitly disallowed. Freeze train/validation/test event IDs before metrics; no frame-level split.
  4. Resolve run identity, cache contamination, source failures/timeouts, expected-stream registration, and current fusion defects insofar as they affect the preregistered condition. Every output directory must be unique and keyed to config/checkpoint/media/condition/split identity. No cache reuse absent exact identity match.
  5. Replay only authorized canonical conditions, one evaluator for every condition. Use independent camera timelines unless human-accepted R04 alignment supports a prespecified fused subset. Produce per-event trace and reproducible manifest.
  6. Report exact denominators/censoring and event-level uncertainty per the governing design; separate sessions; negatives as `k/3`, blocked seconds and exposure, never a false-alarm-per-hour estimate from these clips; simulated gate behavior is software characterization, not safety evidence.
- **Expected additive artifacts:** `src/railway_detection/evaluation/event_metrics.py` or compatible tested extension; `scripts/run_phase12_evaluation.py`; split/run manifests; focused tests; timestamped `results/experiments/phase12_<run_id>/`; report update after results.
- **Acceptance:** Loader negative tests; denominator/censoring mutation tests; split disjointness and event-only assertions; trace-to-number audit; deterministic repeated replay; exact frozen hash/checkpoint hashes/HEAD/command/runtime in manifest; every reported number regenerates from logs; no output under legacy B0–B7 paths; no Audio V2; no unverified camera fusion; user-visible limitations and exclusions.
- **Stop:** Readiness not READY for named stage; EVAL-AUTH absent; split or R04 ambiguous; leakage; non-determinism; metric not computable but coerced to a number; baseline findings that invalidate preregistered assumptions.

### WP6 — Phase 13 robustness and ablations

- **Dependencies:** Phase 12 accepted baseline and trace artifacts; approved records/split unchanged; separate phase authorization and preregistered hypotheses/conditions.
- **Work:** Reconcile older `PHASE13_IMPLEMENTATION_PLAN.md`'s broad multi-factor grid with canonical E1–E7 and the governing experiment design before execution. Do not claim a causal “one factor at a time” result from a grid that changes multiple factors. Run primary contrasts E5 vs E4 for M4/M7 and E7 vs E5 for M2 as specified in the governing design, plus only predeclared, identifiable secondary conditions. Apply dropout/noise/timing perturbations to replay inputs under explicit manifests; do not alter labels or frozen artifacts. Keep stress runs distinct from natural-event denominators.
- **Acceptance:** Baseline condition reproduces Phase 12 traces/metrics exactly; per-run perturbation seed/parameters recorded; one-factor claim verified per contrast; all planned/null results reported; event is unit of analysis; repeated perturbations do not inflate n; frozen hashes unchanged; robust tests against unauthorized event/config use.
- **Stop:** Baseline mismatch, unapproved events, label perturbation, changed frozen config, or discovery of a defect that invalidates Phase 12 claims. Escalate before continuing.

### WP7 — Phase 14 real-time profiling and bounded optimization

- **Dependencies:** accepted Phase 12 baseline; separate Phase 14 authorization; researcher target hardware or explicit assumption; predeclared workload, warmup, repetitions, and equivalence contract. Phase 13 is optional unless a particular profile depends on it.
- **Work:** First measure and report current-host per-stage/tick latency distributions with actual device/environment identity and reproducible traces. Separate cold-start, warm inference, decoding, and decision logic; measure memory/resource use only with available, declared instrumentation. Compare against the 200 ms configured tick as engineering characterization, not a safety criterion. Only after profiling and a researcher-approved bounded scope, prototype optimizations in isolated modules/artifacts; no weight, threshold, timing, or frozen-config changes.
- **Acceptance:** Per-stage p50/p95/p99 and workload metadata; baseline trace reproducible; each optimization passes exact per-tick output equivalence over authorized approved events and synthetic edge cases; no Audio V2; unchanged frozen/checkpoint hashes. Report rejected optimizations too. Do not assert target-device performance from the current Mac host.
- **Stop:** Any output divergence or hardware assumption that is not accepted. Optimization is not adopted merely because it is faster.

### WP8 — Phase 15 controlled validation planning (no field operation)

- **Dependencies:** defensible Phases 12–14 evidence for any claims the protocol proposes to validate; separate researcher authorization for planning scope; site-specific hazard/privacy/ethics review. Site access is an external, not code, dependency.
- **Work:** Replace draft success criteria with measurable, non-overclaiming observational research objectives; hazard analysis covers observer location, equipment, power, data, privacy, weather, communications, and emergency/stop procedure. Specify hardware based on a researcher-selected target and site survey. Any data-collection script is passive, disconnected from actuators/control networks, lab-tested, and separately authorized.
- **Acceptance:** Safety-case draft explicitly says not a certification; defines exclusion zones and responsible site authority without instructing track access; no actuator/GPIO/serial/control interfaces; consent/privacy/data-retention plan; protocol identifies what cannot be concluded; site and ethics permissions documented before capture.
- **Stop:** Any live-control connection, absent site permission, unacceptable hazard, or request to represent passive observation as safe deployment. No field capture is part of this plan.

### WP9 — Phase 16 manuscript and release

- **Dependencies:** accepted Phase 12 report; Phase 13/14/15 only if performed and accepted; evidence audit; researcher decisions on venue/authorship/data release/privacy/ethics; separate publication/release approval.
- **Workstreams:** build a claim-to-artifact ledger; draft methods/results only from accepted manifests/logs; report one site/two sessions, censoring, small n, single-annotator limitations (or accepted agreement study), R04 scope, policy revision after pilot, audio limitations, and simulated barrier semantics. Reproduce all figures/tables from result artifacts. Build a release inventory that excludes raw video/PII unless explicitly approved. Keep manuscript draft distinct from submission and public release.
- **Acceptance:** 100% of factual claims have a human-reviewed supporting artifact and exact path/identifier; all reported figures regenerate; environment/config/checkpoint/split/seed/command provenance included; no unsupported safety or certification claim; Audio V2 not presented as valid; no unsupported cross-camera/generalization/hourly-rate claim; researcher signs final release decision.
- **Stop:** Unsupported claim, unreproducible result, authorship dispute, disclosure/privacy issue, or no publication authorization.

---

## 6. Dependency graph and safe parallelization

```text
WP0 plan/preservation
  └─ WP1 decision + protocol/artifact reconciliation
       └─ WP2 synthetic-only runner implementation/test
            └─ [ADJ-AUTH + reviewer participation] WP3 genuine review batches
                 └─ [D3(c), R-DISC1, LEG-EXEC or documented decline]
                      WP4 11.12 reconciliation/readiness
                       └─ [EVAL-AUTH + R-SPLIT + R-R04SCOPE]
                            WP5 Phase 12 preregistration → replay → accepted report
                             ├─ [Phase-specific authorization] WP6 Phase 13
                             ├─ [Phase-specific authorization + target hardware] WP7 Phase 14
                             └─ [evidence + site approvals] WP8 Phase 15 planning
                                  └─ [R-PUB] WP9 Phase 16 manuscript/release
```

Safe parallel work after explicit implementation authorization: (a) additive artifact reconciliation and decision inventory; (b) synthetic-only session-runner tests; (c) Phase 12 metric/split test design against synthetic Stage-2.1 fixtures; and (d) claim/evidence ledger template. These may proceed independently only if they do not create real review records, touch frozen artifacts, execute evaluation, assert researcher decisions, or modify one another's files.

Not safe to parallelize: real adjudication and promotion; readiness determination before record reconciliation; Phase 12 split/preregistration against an evolving ground-truth set; metrics before the preregistration is frozen; Phase 13/14 results before an accepted Phase 12 baseline; public manuscript claims before artifacts are reviewed; any site planning that implies access or physical activity.

---

## 7. First implementation batch after this planning run

This is a recommendation for a later, separately authorized **engineering** batch; this document itself performs none of it.

1. **Read-only preflight:** snapshot Git status, HEAD, hashes of the 27 review records, frozen config/checkpoints, active proposals/media inventory, issue register, and existing output roots. Never reset, checkout, clean, stage, or rewrite the present worktree.
2. **Reconcile 11.10 artifacts additively:** write a concise correction/supersession memo for the missing closure package and `6.0.0`/`7.0.0` documentation mismatch. Do not rewrite old reports or execute disposition.
3. **Implement only a synthetic/temp-path Phase 11.11 session runner** once its engineering boundary is explicitly authorized. Prefer modules/tests isolated to `annotation/adjudication_session.py` and dedicated tests. Make real output impossible by default; run no real review. Do not encode pending D1 numbers, invent D3(c), or silently choose D3(a) semantics.
4. **Run focused regression tests** for Phase 11.3 absence-of-defaults, 11.8 workflow, 11.9 pilot, promotion, readiness gate, and Phase 12 loader. Then run the full test suite only if authorized and if tests are configured not to mutate tracked/shared result paths; capture exit status without shell-pipeline masking.
5. **Review the diff and preservation boundary:** only files explicitly authorized for this batch should change; all 27 legacy hashes, frozen config/checkpoint hashes, existing results and pre-existing worktree entries must match the preflight snapshot. Stop before any real adjudication or evaluation.

**First batch is complete only when** synthetic-runner acceptance passes, the preservation manifest matches, and the researcher has received a clear list of decisions/authorizations still blocking real review. It does not create ADJ-AUTH or start Phase 11.11 human sessions.

---

## 8. Execution controls and reporting convention

For every future implementation/execution batch, record: (1) the exact authorization and scope relied on; (2) pre/post Git state and hashes; (3) changed/created paths; (4) commands and unmasked exit codes; (5) tests, including known failures; (6) data and frozen-artifact integrity; (7) evidence-backed phase status; (8) unresolved questions and stop events. Separate **engineering implemented**, **synthetic tested**, **researcher performed**, **evaluation authorized**, **evaluation executed**, and **scientifically accepted** statuses. Never compress them into “phase complete.”

Use only a fresh, uniquely identified output directory for each authorized experiment. Registry writes must be append-only and owned by the authorized runner; tests must use temporary output roots rather than mutate `results/experiment_registry.jsonl`. A report is not evidence that a command ran; preserve the run manifest and source logs.

---

## 9. Reference index

### Governing decisions and audit

- `docs/EXPERIMENT_DESIGN_FINAL.md`
- `docs/PHASE11_3_RESEARCHER_DECISIONS.md`
- `docs/PHASE11_10_REPORT.md` (with missing-package discrepancy noted above)
- `docs/RESEARCHER_DECISION_REGISTER_REMAINING_PHASES.md`
- `docs/OPEN_DECISIONS_AND_BLOCKERS.md`
- `docs/INDEPENDENT_MASTER_AUDIT.md`
- `docs/FINDINGS_REGISTER.csv`

### Phase protocol, reports, and plans

- `docs/PHASE11_11_ADJUDICATION_PROTOCOL.md`
- `docs/PHASE11_12_ADJUDICATION_CLOSURE_REPORT.md`
- `docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md`
- `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PLAN.md`
- `docs/PHASE12_EVALUATION_REPORT.md`
- `docs/PHASE13_ROBUSTNESS_ABLATION_REPORT.md`
- `docs/PHASE14_REALTIME_OPTIMIZATION_REPORT.md`
- `docs/PHASE15_VALIDATION_PROTOCOL.md`
- `docs/PHASE16_MANUSCRIPT_DRAFT.md`
- `docs/PHASE12_16_RESEARCH_CONTRACTS.md` (metadata-only boundary)
- `docs/implementation_plans/PHASE11_10_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE11_11_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE11_12_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE12_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE13_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE14_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE15_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE16_IMPLEMENTATION_PLAN.md`

### Key current implementation/test anchors

- `src/railway_detection/annotation/review_session.py`
- `src/railway_detection/annotation/stage2_1_schema.py`
- `src/railway_detection/annotation/promotion_gate.py`
- `src/railway_detection/annotation/evaluation_readiness_gate.py`
- `src/railway_detection/evaluation/ground_truth_loader.py`
- `src/railway_detection/evaluation/metrics.py` (generic/historical; not yet Phase 12 contract-complete)
- `src/railway_detection/experiments/{frozen_config,layer_b_processor,runner,leakage_guard}.py`
- `configs/frozen_experiment_v1.yaml`
- `data/manifests/camera_sync_offsets_candidate.yaml`
- `data/ground_truth/authorized_reviewers.json`
- `tests/test_phase11_3_pending_decisions_not_defaulted.py`
- `tests/test_phase11_8_review_workflow_integration.py`
- `tests/test_phase11_9_synthetic_pilot.py`
- `tests/test_phase11_12_readiness_gate.py`
- `tests/test_phase12_ground_truth_loader.py`

---

## 10. Final state for this planning run

The only intended repository write in this resumed planning run is this file: `docs/MASTER_REMAINING_PHASES_IMPLEMENTATION_PLAN.md`. No implementation, adjudication, record disposition, promotion, evaluation, metric computation, physical-control activity, site operation, staging, commit, or push is authorized or performed by this plan. Re-check the worktree and artifact hash after creation; preserve the 14 tracked modifications and 230 untracked entries observed at the start of the resumed audit.