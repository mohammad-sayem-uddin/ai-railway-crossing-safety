# Final Research Implementation Roadmap — Train Gate Automation

**Date:** 2026-10-21

**Repository:** `/Users/sayemuddin/Desktop/Train_automation`

**Decision status:** evidence-limited research completion package; not an official evaluation authorization
**Authority boundary:** This roadmap does not override ground-truth, evaluation, incident, source-media, or release controls.

> **Executive decision.** The repository can support a coherent paper about an evidence-bound multimodal railway-crossing research prototype, its software/governance controls, its still-image development evidence, and its synthetic validation. It cannot support a positive event-level railway-performance, field-safety, synchronization, or deployment conclusion. The highest-value completion path is to preserve historical outputs, retire unsupported claims, document re-entry requirements, and avoid manufacturing a result where independent ground truth is absent.

## 1. Research question and hypotheses

### 1.1 Precise research question

**RQ:** Under a pre-registered, event-level protocol with independent human ground truth and validated camera timing, does conservative fusion of approach/departure vision, supporting-only audio, temporal persistence, and a fail-closed state machine improve the correctness and timeliness of simulated crossing-gate decisions relative to simpler single-camera and stateless baselines?

The question is narrower than “is the system safe?” The implementation is a research prototype and simulated gate policy, not a railway interlocking controller. [evidence: docs/archive/RESEARCH_CONCEPT.md] [evidence: docs/FINAL_RESEARCH_HANDOVER_20261021.md]

### 1.2 Hypotheses registered for a future authorized evaluation

| ID | Hypothesis | Primary test | Current status |
|---|---|---|---|
| H1 | Temporal persistence and state-aware hysteresis reduce spurious transitions and premature-opening opportunities relative to a stateless detector. | Paired event-level comparison. | **Untested scientifically.** No approved Layer-B labels. |
| H2 | Validated multi-view evidence improves observable departure/clearance decisions without unsafe opening decisions. | Paired comparison with accepted camera timing. | **Untested.** R04 scope unresolved. |
| H3 | Supporting-only Audio V3 adds approach/presence evidence without authorizing clearance/opening. | Frozen-threshold modality analysis with independent labels. | **Untested on real events.** Human horn confirmation absent. |
| H4 | Source loss, stale data, disorder, and malformed evidence produce conservative hold/fail-safe behavior. | Synthetic fault-injection and contract tests. | **Software-contract evidence only.** |

### 1.3 Strongest defensible contribution

The strongest contribution supported now is **an evidence-bound research framework for conservative multimodal crossing perception**, not a validated detector or safety system. It combines frozen model interfaces, temporal/source-health controls, a conservative simulated state machine, human-independent ground-truth gates, hash/provenance and split controls, synchronization diagnostics, readiness/reproducibility gates, and explicit incident/release preservation. These are implementation and methodological contributions; novelty, superiority, deployment readiness, and railway safety are not established.

## 2. Repository assessment and status

| Area | What exists | Scientific classification |
|---|---|---|
| Vision perception | YOLO-compatible detector, frozen checkpoint, class metrics, image validation artifacts | Software and Layer-A image evidence; not event-level field performance. |
| Audio perception | Audio V3 pipeline/configuration; Audio V2 prohibited | Development evidence; field transfer and human labels unresolved. |
| Fusion and state | Temporal collector, source health, rules, decision engine, gate simulation | Synthetic/engineering verification; no physical safety case. |
| Synchronization | Candidate R04 diagnostics and fail-closed loader | Exploratory; full-cohort synchronization unestablished. |
| Ground truth | Candidate proposals, invalidated legacy records, Stage-2.1 schema/gates | Zero valid approved records; event metrics blocked. |
| Evaluation | Loader, manifest builder, replay/metrics contracts, readiness gate | Code paths tested; official evaluation unavailable. |
| Ablation/robustness | Synthetic-only engine with resume/comparability safeguards | Infrastructure ready; official run not executed. |
| Profiling | Synthetic development-host benchmark | Not target-hardware evidence; no real-time claim. |
| Worktree | Broad pre-existing modifications/untracked files | Preserved; no reset, cleanup, staging, or commit. |

### 2.1 Evidence inventory

- Handover: `docs/FINAL_RESEARCH_HANDOVER_20261021.md`.
- Layer-A: `results/dataset_validation/report.json`, `results/dataset_validation/manifest_summary.json`, `experiments/vision/39f402dfe460/evaluation/metrics.json`.
- Split limitation: `data/splits/705d388743ea/split_summary.json` records `development_fallback` and `leakage_risk: true`; `run_manifest.json` records configuration/provenance.
- Synthetic evidence: `results/testing/FINAL_TEST_RESULTS.md`, `docs/PHASE11_9_SYNTHETIC_PILOT_REPORT.md`, `docs/PHASE13_ROBUSTNESS_ABLATION_REPORT.md`, `docs/generated/PHASE14_SYNTHETIC_BENCHMARK_20261016.json`.
- Audits/correction: `docs/PHASE16_MANUSCRIPT_CORRECTION_v1.md`, `docs/FORENSIC_EXPERIMENT_AUDIT.md`, `docs/CORRECTIVE_EXPERIMENT_AUDIT.md`, `docs/FINDINGS_REGISTER.csv`, `docs/INDEPENDENT_MASTER_AUDIT.md`.
- Governance: `docs/generated/OFFICIAL_EVALUATION_READINESS_20261019.json`, `docs/FINAL_GROUND_TRUTH_PROTOCOL.md`, `docs/R04_CALIBRATION_VALIDATION_REPORT.md`, `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`.
- Incident/release: `docs/INCIDENT_CLOSURE_REVIEW_20261020.md`, `docs/MEDIA_ACCESS_INCIDENT_INVESTIGATION_20261020.md`, `docs/STAGE21_TIMING_PILOT_INCIDENT_20261019.md`, `docs/STAGE21_TIMING_PILOT_RELEASE_20261019.md`.

## 3. Implementation invariants and corrections

These are acceptance conditions, not optional refinements:

1. **Independent labels:** only genuine `8.1.0-stage2.1` records, with human review history and explicit approval, may enter ground-truth evaluation. The 27 invalidated legacy records and all candidate proposals remain excluded; do not migrate, bulk-approve, or synthesize labels.
2. **Canonical event boundaries:** preserve `T3` as locomotive-unit rear clearance and `T4` as final-vehicle tail clearance. A `T0` at the recording start is left-censored, not physical onset. Preserve applicability, observability, uncertainty, and censoring separately.
3. **Clock scope:** front and back camera time axes remain independent unless R04 has an accepted researcher decision and empirically supported scope. Never calculate concurrent exposure by summing unsynchronized streams.
4. **Metric validity:** do not compute or publish event-level MTR, POR, warning lead time, clearance latency, or no-train rates without approved labels, fixed endpoint definitions, valid denominators, and observable boundaries. A null, censored, or unavailable value is never converted to zero.
5. **Audio boundary:** Audio V3 only; audio is supporting evidence and cannot establish clearance or authorize opening. Field horn status requires independent human review. Audio V2 remains prohibited.
6. **Frozen comparisons:** bind model/checkpoint, policy, configuration, protocol, event split, input manifest, seed, device, command, software revision, and outputs. No threshold/policy adjustment after outcomes are inspected.
7. **Operation-specific authority:** a ready-looking status or general engineering approval is not EVAL-AUTH, ADJ-AUTH, media-access permission, pilot activation, or field authorization. Require the exact artifact and scope for each operation.
8. **Preservation:** keep historical reports and contradictory findings auditable; correct claims additively. Do not modify incident records or regenerate/activate the held timing-pilot release as part of this plan.

## 4. Work packages and order of execution

The order is dependency-driven. P0–P3 below describe safe, documentation/software work; P4–P7 are future work and must remain stopped until their prerequisites and separate authorizations exist.

| Phase | Work package and implementation | Deliverable / verification | Gate |
|---|---|---|---|
| P0 — Preserve and bound | Record baseline worktree, protected release hash/status, and incident state from existing records. Make no source-media or restricted-workflow calls. Keep user-existing changes intact. | This roadmap; explicit evidence classes and no-go boundaries. | Stop if an operation might read/hash/decode source media, change protected records, or perform evaluation without authorization. |
| P1 — Evidence inventory | Map code, configs, checkpoints, protocols, datasets, split metadata, synthetic artifacts, historical claims, test evidence, and governance prerequisites to exact repository paths. Mark each as current, historical, synthetic, candidate, blocked, or not established. | Evidence inventory and claim-to-artifact map in the paper/report if later requested; this roadmap provides the working index. | Do not treat old prose or a JSON status field as proof unless supported by the underlying artifact and method. |
| P2 — Safe software verification | Use only synthetic fixtures and permitted metadata/code checks. Verify tests, compile, dependency consistency, and document whitespace without invoking official readiness/evaluation, promotion, LEG-EXEC, media review, or source-media tools. Record exact command, environment, exit code, and actual output. | Reproducible safe-check ledger; failures remain failures and are not silently repaired or omitted. | A passing software suite supports only tested contracts, not model/field/safety performance. |
| P3 — Evidence-limited research package | Freeze claims to Layer-A image results, synthetic workflow/fault evidence, and implementation/governance description. Clearly label historical exploratory replays and omit unavailable event-level results. Link every quantitative statement to its artifact and caveat. | If separately requested: manuscript and completion report; not part of this roadmap-only deliverable. | No field, safety, synchronization, target-hardware, readiness, or deployment claim. |
| P4 — Human ground truth (blocked) | Researcher independently resolves review policy and conducts human Stage-2.1 review/adjudication, including applicable boundaries, horn status, uncertainty, and unobservable/censored fields. Preserve append-only review history. | Genuine approved records for train, no-train, and engine cohorts plus verified provenance and ground-truth manifest. | Requires authorized human/media workflow. Current evidence: zero valid Stage-2.1 records; do not start now. |
| P5 — Researcher decisions and evaluation binding (blocked) | Researcher authors event-level split, premature-opening endpoint choice, and R04 camera-scope decision. Build derived evaluation input manifest and bind exact split/protocol/config/policy/checkpoint hashes. | Decision artifacts and reproducible manifest with verified fingerprints. | All scientific decisions are human-owned; no default or assistant-selected values. Then obtain recorded EVAL-AUTH bound to these artifacts. |
| P6 — Official event-level baseline (blocked) | Only after every readiness prerequisite and EVAL-AUTH: run the frozen protocol on the approved cohort, with camera-local analysis where R04 is not approved. Preserve per-event outcomes, exclusions, censoring, and logs. | Frozen run manifest, per-event ledger, numerator/denominator tables, uncertainty estimates, independent review. | Do not start unless readiness is independently verified and authorization exactly covers the operation/inputs. Current readiness artifact is `ready: false`. |
| P7 — Ablation, robustness, and hardware study (blocked/separate) | After a valid baseline and separate scope authorization, execute preregistered one-factor ablations and fault perturbations; target-hardware profiling is a distinct study with declared platform and acceptance criterion. | Complete event×seed×condition grid, comparability checks, condition-wise failures, platform fingerprint, CI/limits. | Phase 13 currently states blocked; synthetic engine availability does not authorize empirical runs. No deployment or certification inference. |

## 5. Experimental design for any future authorized evaluation

### 5.1 Conditions and fair baselines

Use a frozen baseline and change one declared factor per treatment. The final matrix must match the approved protocol and not exceed authorization scope; examples of factors to preregister are:

- **B0 / E1:** front-camera vision with the frozen stateless decision baseline.
- **Temporal-only:** same vision inputs and thresholds, with persistence/confirmation added as the sole planned factor.
- **State-policy:** same perception evidence, with the specified hysteresis/state policy as the sole factor.
- **Multi-view:** add back-camera evidence only for events in an accepted R04 scope; keep unsupported events camera-local.
- **Audio-supporting:** add frozen Audio V3 evidence at threshold `0.3700`; audio must not independently authorize clearance/opening.
- **Fault conditions:** preregister dropout, stale-source, timestamp-order, malformed-input, and timing-jitter cases; label synthetic versus authorized real-evidence perturbations explicitly.

Do not describe the historical 11-event exploratory replay as a controlled ablation or full-cohort synchronization result. Do not change multiple factors at once and attribute the difference to one component.

### 5.2 Endpoints and statistics

Before any run, the researcher must choose the premature-opening definition (the readiness record identifies an unresolved conflict between protocol v9 and design M4), fix the system-output timestamp definition, and specify inclusion rules.

| Endpoint | Required definition / rule | Current status |
|---|---|---|
| MTR | Event-level miss against the prespecified closing/warning outcome by observable `T1`; report raw count and denominator. | Not estimable: no approved Stage-2.1 labels. |
| POR | Opening outcome in the researcher-selected premature-opening window; do not choose v9 or M4 implicitly. | Blocked: endpoint unresolved and labels absent. |
| Clearance latency | Signed difference from final-tail `T4` to the prespecified opening decision; never substitute `T3`; exclude/report unobservable or censored `T4`. | Not estimable. |
| Warning lead time | Signed `T1 − warning_time`; distinguish delayed/early outcomes and exclude left-censored `T0` from onset latency. | Not estimable. |
| No-train nuisance behavior | Episodes, duration, and source attribution per stream; only calculate rates with approved exposure and valid clock scope. | No valid event-level denominator. |
| Perception | AP/precision/recall/F1/mAP with class, IoU/confidence thresholds, image split and unit stated. | Layer-A only; not an event or field endpoint. |

Analyze independent events, not frames as independent samples. Report numerator, denominator, exclusions, censoring, and the exact CI method. Use Wilson intervals for proportions; use paired estimates/tests only when the same complete event set is evaluated under each condition. Bootstrap continuous outcomes only under a prespecified event-level resampling plan. No post-hoc significance claims; null/unavailable is not zero.

## 6. Dataset, split, and ground-truth implementation requirements

1. **Separate evidence tiers.** Layer-A images, synthetic fixtures, exploratory replay, approved event evaluation, and operational/field evidence are distinct categories. No tier inherits the claims of another.
2. **Image split limitation.** The existing split summary states `split_type: development_fallback` and `leakage_risk: true`; its image-level metrics may be described only with that limitation and their exact threshold/split provenance. A visually high image score does not validate train-event timing or gate behavior.
3. **Ground-truth lifecycle.** Candidate proposals are not labels. Human review must be independent of model output and create valid Stage-2.1 review history. Approved records need exact source/proposal/review hashes, reviewer authority, event identity/cohort, timestamp semantics, and manifest binding. Existing invalidated legacy records stay excluded.
4. **Event split.** Require a researcher-authored split artifact grouped to prevent session/event leakage. Do not infer an event split from the image-level development split or make one in assistant code.
5. **Boundary states.** For each T marker preserve value, uncertainty, applicability, observability, reason, and censoring. T0 at frame zero is left-censored; T3 is lead locomotive unit clearance; T4 is last-vehicle tail clearance.
6. **Camera timing.** Keep separate clock domains without accepted R04 scope. Report stream-local denominators and avoid concurrent-overlap/no-train rate calculations until their time basis is supported.
7. **Audio labels.** Record `present`, `absent_observed`, `unobservable`, or not-applicable as defined by protocol; obtain human acoustic review for field horn claims. Audio classification output is never itself ground truth.
8. **Input immutability.** Future run manifest must fingerprint every authorized input and artifact before/after use, configuration, model, code, policy, environment, command, seed, device, and output. A mismatch invalidates comparability and blocks result promotion.

## 7. Evidence ledger and permitted reporting language

| Evidence class | Repository example | Permitted statement | Prohibited inference |
|---|---|---|---|
| Dataset integrity | `results/dataset_validation/report.json` | Artifact reports 3,157 image/annotation records, zero errors/warnings, and passed integrity checks. | General dataset quality, field representativeness, event-level validity. |
| Layer-A image performance | `experiments/vision/39f402dfe460/evaluation/metrics.json` | Artifact reports mAP@50 0.9946 and mAP@50:95 0.855 on its image evaluation; specify thresholds, counts, and split caveat. | Train detection reliability, tail clearance, MTR/POR, or safety. |
| Split provenance | `data/splits/705d388743ea/split_summary.json` | Existing split is `development_fallback`, `leakage_risk: true`. | Independent held-out-site or event-level generalization. |
| Synthetic workflow | `docs/PHASE11_9_SYNTHETIC_PILOT_REPORT.md` | Synthetic workflow tests exercised validation/rejection paths in temporary synthetic fixtures. | Human annotation validity, user-time measurement, media review, real-event correctness. |
| Synthetic robustness | `docs/PHASE13_ROBUSTNESS_ABLATION_REPORT.md` | Engine and safeguards exist; report says official/real-data Phase 13 study was not run and is blocked. | Ablation effects, real-scene robustness, safety. |
| Synthetic timing | `docs/generated/PHASE14_SYNTHETIC_BENCHMARK_20261016.json` | Timings describe the measuring host and synthetic inputs; artifact says not target-hardware or safety evidence and claim not permitted. | Real-time guarantee, worst-case latency, target device or railway performance. |
| Exploratory replay | Phase 8/9 reports | Historical exploration only, with exact caveats from its audit. | Confirmatory ablation, representative cohort, validated synchronization. |
| Official event evaluation | No approved Stage-2.1 data/manifest/authorization | No quantitative claim; mark blocked/not estimable. | Any positive or zero MTR/POR/performance assertion. |

The image metrics artifact records `total_gt: 487`, `total_tp: 480`, `total_fp: 94`, and `total_fn: 7` at its stated operating point. If these figures are repeated, label them as image-object counts from that artifact, not events. The correction document `docs/PHASE16_MANUSCRIPT_CORRECTION_v1.md` gives the intended qualification and preserves the historical DOCX rather than silently rewriting it.

## 8. Figures, tables, and qualitative material

Potentially reusable method/architecture figures, subject to checking each file and caption, are:

- `research/figures/architecture/fig01_system_architecture.{png,svg,pdf}`
- `research/figures/architecture/fig02_vision_pipeline.{png,svg,pdf}`
- `research/figures/system/fig06_gate_safety_state_machine.{png,svg,pdf}`
- `research/figures/temporal/fig04_multiframe_confirmation.{png,svg,pdf}`
- `research/figures/temporal/fig05_evidence_persistence.{png,svg,pdf}`
- `research/figures/evaluation/fig09_confusion_matrix_normalized.{png,svg,pdf}` and `fig11_per_class_metrics_comparison.{png,svg,pdf}` (image-level only).

For a future evidence-limited paper, include (a) a system/data-flow diagram, (b) a table mapping evidence tier to claim ceiling, (c) a Layer-A image-metric table with split limitations, and (d) a blocked-prerequisites table. Do not present real-media qualitative images or plots as evidence unless source, access authority, provenance, and exact status are independently cleared. Cite the safety-endpoint table only to document that MTR/POR are unavailable, not as positive results.

## 9. Reproducibility, verification, and output acceptance

- Use the repository’s declared canonical environment/lockfile where available; record exact Python executable/version and dependency check output. Do not assert that an earlier reported test total was rerun in this continuation.
- Safe checks may include synthetic-only focused tests, compile checks, dependency consistency, document link/path checks, and whitespace validation. Never invoke official readiness/evaluation, ground-truth promotion/adjudication, LEG-EXEC, real-media review, or pilot activation under this roadmap.
- Preserve command, working directory, environment variables relevant to execution, start/end status, exit code, stdout/stderr artifact path, and test counts. If a result is missing or a command failed, report it as missing/failed, not passed.
- Every quantitative claim in any future paper must map to the exact source artifact, metric key, unit, cohort/split, threshold, and evidence class. A reviewer should be able to reproduce the number without source-media access.
- A passing test suite confirms only the tested code contracts. It does not establish detection performance, label validity, generalization, synchronization, real-time operation, risk reduction, safety integrity, regulatory compliance, or certification.

## 10. Risks, dependencies, and fallback decisions

| Risk/dependency | Consequence | Safe fallback |
|---|---|---|
| Zero valid Stage-2.1 records; legacy reviews invalidated | No event-level ground truth or official metrics | Limit deliverable to prototype/governance and supported image/synthetic evidence. |
| Researcher split, endpoint, and R04 scope decisions absent | Cohort, POR, and multi-view comparisons not defined | Leave all dependent results blocked; do not select defaults. |
| No derived input manifest or EVAL-AUTH | Official evaluation not authorized/ready | Metadata-only documentation and permitted synthetic checks only. |
| October 19 media-access incident is closed unresolved | Whether source bytes were read/hashed cannot be stated | Preserve exact uncertainty; do not repeat implicated access/status procedures absent new authority. |
| Held pilot release, pilot inactive | No genuine timing-pilot data or activation | Describe release as prepared/not activated; keep manifest unchanged. |
| Historical manuscripts/reports contain overclaims | Risk of propagating invalid safety/performance statements | Preserve originals; cite additive correction/audits; exclude unsupported numbers. |
| Broad pre-existing dirty worktree | Risk of overwriting unrelated/user changes | Limit writes to the requested roadmap; no reset, cleanup, staging, or commit. |
| Benchmark has no acceptance criterion and host does not match target | Timing measurements lack deployment interpretation | Report only as synthetic development-host observations with explicit no-claim boundary. |

## 11. Go/no-go gates and completion criteria

### Current decision

**GO:** finish and review this evidence-limited implementation roadmap; preserve existing code/artifacts; use only already-recorded and independently traceable evidence.

**NO-GO:** official evaluation, readiness reruns, annotation review/adjudication/promotion, LEG-EXEC, source-media reads/hashes/decodes/previews/playback, pilot activation, release regeneration, target-hardware or field tests, and safety/deployment claims.

### Future evaluation gates (all required, no implied authorization)

1. Independent reviewer confirms incident-compatible authorization scope and allowed operations.
2. Genuine approved Stage-2.1 records exist across required cohorts with valid review/provenance hashes; invalidated legacy records remain excluded.
3. Researcher-authored split, premature-opening endpoint, and R04 scope decisions exist and are internally consistent with protocol and implementation.
4. Hash-bound derived input manifest and frozen protocol/config/policy/checkpoint identities are verified.
5. Official readiness is assessed only by an authorized operator under the applicable scope; every blocker is resolved, and recorded EVAL-AUTH binds the exact current artifacts.
6. Baseline run is complete, reproducible, and independently reviewed before any ablation or robustness expansion.
7. Separate authorization and safety review are obtained for any media access, pilot, hardware, site, or operational work.

### Roadmap completion checklist

- [x] State the narrow research question and distinguish prototype research from safety validation.
- [x] Inventory current evidence and identify claim ceilings and missing prerequisites.
- [x] Define non-negotiable ground-truth, timestamp, clock, audio, metric, reproducibility, and release invariants.
- [x] Give an ordered implementation plan with dependencies, artifacts, and explicit gates.
- [x] Specify future baselines, metrics, dataset requirements, and statistical handling without inventing outcomes.
- [x] Verify this final roadmap’s structure, paths, figures, numbers, cross-references, whitespace, and preservation boundaries.

## 12. Stop condition and handover

This roadmap-only task is complete when the document is structurally verified, all claims are traceable to repository artifacts or clearly labeled as proposed future methods, all blockers remain explicit, and the protected release/incident/worktree state has not been changed. No further engineering sprint is implied. Any future data collection, annotation, official evaluation, pilot, hardware, or field work is a separately scoped and authorized research activity—not a continuation authorized by this document.

