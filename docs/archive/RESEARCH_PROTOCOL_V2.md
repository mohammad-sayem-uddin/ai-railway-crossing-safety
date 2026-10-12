# Research Protocol V2

## Multimodal Railway-Crossing Event Detection: Scientific Protocol

**Status:** Proposed protocol; no model training or system-performance conclusion has been made.  
**Date:** 2026-08-13  
**Authority:** This document supersedes earlier system-level experimental sections in `MASTER_IMPLEMENTATION_ROADMAP.md` and `EXPERIMENT_PLAN.md`. Those documents remain useful implementation/research-history records but must be reconciled with this protocol before coding.  
**Terminology:** This study uses *safety-oriented simulated decision policy*. It does not claim physical fail-safe operation, safe live operation, certification, or deployment readiness.

---

## 1. Research objective

Determine whether a **predefined**, two-camera, audio-assisted, temporal decision policy changes event-level crossing-detection outcomes relative to fair simpler baselines on synchronized, held-out train-passage recordings.

The objective is empirical comparison of software evidence policies. It is not validation of physical railway control.

## 2. Primary research question

> On synchronized, event-labeled recordings from held-out crossings, does a predefined two-camera, audio-assisted, temporal state policy change event-level missed-train and premature-opening outcomes relative to fair single-camera and vision-only baselines?

The word “change” is intentional. Improvement may not occur; direction and uncertainty must be reported from data.

## 3. Secondary research questions

1. Does a second camera improve approach, occupancy, or departure-event evidence over a single-camera temporal baseline?
2. Does supporting acoustic horn evidence improve event recall or warning lead time without unacceptable false alarms?
3. Does temporal filtering improve event-level behavior over independent-frame decisions?
4. Does the state-aware policy prevent simulated premature opening relative to non-state-aware fusion?
5. How do performance and uncertainty vary across held-out crossings and represented lighting, weather, occlusion, and fault conditions?
6. What viewpoint-label ambiguity and annotation disagreement exist for `front`, `side`, and `rear`?

## 4. Scope

### In scope

- Software-only analysis and replay/simulation of recorded train passages.
- Train viewpoint detection on a still-image dataset (Layer A).
- Multimodal temporal event evaluation on synchronized recordings (Layer B).
- Transparent rule-based temporal fusion and state-machine policies.
- Reproducible failure-sensitivity simulations explicitly labeled as simulations.

### Out of scope unless separately added by a documented decision

- Physical gate actuation, safety certification, live deployment, Raspberry Pi performance, and real-time latency claims.
- Simultaneous opposing trains, reversing, shunting, train splitting, stopped trains across the crossing, and other abnormal operations not represented and labeled in Layer B.
- Claims for all Bangladesh crossings, all weather, or all train types.

## 5. Operational design domain (ODD)

The initial ODD is **recorded, single-train-passage events** at represented Bangladeshi level crossings, with a known direction and two fixed cameras observing defined approach/departure/crossing zones plus an audio recording. Conditions may include day/night/rain/fog only when represented in sufficient held-out data.

Every Layer B event must be tagged as `in_domain`, `out_of_domain`, or `unknown_domain`. An unrepresented condition is not silently treated as supported. The eventual ODD must specify camera placement/orientation, track configuration, source synchronization quality, event direction, train movement assumptions, and exclusion conditions.

## 6. Primary research unit

The primary unit is one **train-passage event**: one identifiable train travelling in one direction through the defined crossing zone, represented by a synchronized multimodal recording bundle and independently labeled reference events.

The event begins at the earliest retained recording time and ends after tail clearance is observed/defined or the sequence is marked incomplete. Adjacent clips/frames of the same passage are not independent samples.

## 7. Secondary evaluation units

| Unit | Use | Not valid for |
|---|---|---|
| Annotated image/object | Vision detector development and viewpoint analysis. | Multimodal or gate-policy claim. |
| Audio window | Acoustic-event classifier development. | Train-passage independence claim. |
| Frame/time step | Temporal-model diagnostics. | Primary statistical sample. |
| Train-passage event | Primary system outcomes and paired baseline comparisons. | Independent evidence if same train is duplicated. |
| Crossing | Generalization cluster and uncertainty analysis. | Assumed representative national population. |

## 8. Dataset requirements

Two non-interchangeable layers are required.

1. **Layer A — vision image dataset:** labeled images for viewpoint/object-detection model development. It may contain approximately 4,000 images from 30+ crossings, but all actual counts must be measured.
2. **Layer B — synchronized train-passage event dataset:** event bundles containing Camera 1, Camera 2, audio, timestamps/synchronization metadata, and independent event ground truth. Layer B is mandatory for multimodal temporal or state-machine claims.

Layer A may support a publishable viewpoint-detection study alone. It cannot support a claim that multimodal state policy improves crossing-event reliability. Layer B must include empty/no-train periods and realistic negative acoustic/visual contexts sufficient to estimate false alarms.

## 9. Ground-truth requirements

Ground truth is independent reference labeling, not a detector output. At minimum, each evaluable Layer B event requires labels defined in `EVENT_LABEL_PROTOCOL.md` for approach confirmation, crossing entry, crossing occupancy, crossing exit, and tail clearance—or explicit missing/uncertain status.

`rear` detection is always a model signal. It is never ground truth for tail clearance. If tail clearance cannot be observed independently from camera geometry, the event must be labeled `clearance_unobservable`; it cannot contribute to the primary premature-opening endpoint.

## 10. Annotation protocol

Use the rules in `ANNOTATION_GUIDELINE_V2.md` and retain raw annotation provenance. Before full labeling, run a representative double-annotation pilot. Two annotators independently assign viewpoint labels and boxes; disagreements are categorized and adjudicated by a named reviewer.

The pilot must report viewpoint agreement, box agreement for matched objects, ambiguity rate, reasons for disagreement, and whether the three-class taxonomy is retained. A fourth class is not introduced without a decision record and evidence that the existing taxonomy is unusable.

## 11. Multimodal synchronization protocol

Use the collection and synchronization requirements in `SYNCHRONIZED_DATA_COLLECTION_PROTOCOL.md`.

Preferred method: start all sources from a common clock or record a shared audiovisual synchronization cue; retain original media timestamps. If exact synchronization is unavailable, estimate an offset with a documented method, record its uncertainty, and use a predeclared tolerance window. Do not label estimated alignment as perfect synchronization.

Events exceeding the configured alignment uncertainty threshold are excluded from timing/fusion primary analyses but may be retained for Layer A model development where appropriate.

## 12. Camera geometry definition

Each crossing/event must have a geometry record containing, at minimum: camera ID and role, viewing direction, approximate location relative to the crossing reference line, visible approach/departure/crossing zones, track direction, and known blind spots. Calibrated physical distances are optional but must not be invented.

The study must define a **crossing reference zone** in image space or using identifiable scene landmarks. The zone definition is used for event annotation; a whole-train bounding box alone does not establish occupancy or clearance.

## 13. Audio protocol

Audio is **train-horn/supporting acoustic evidence**, not automatically train presence. Its protocol must use continuous recordings or windows from continuous recordings, with labels for horn occurrence, train-present-without-horn where observable, vehicle-horn/non-train confusions, and unavailable/poor-quality audio.

Audio may independently trigger simulated closure only if a validation-only policy decision and held-out event analysis justify it. Until then, it is supporting closure evidence. Audio can never independently authorize simulated opening.

Report event recall, false alarms per hour of evaluable non-train audio, detection latency, vehicle-horn false positives, and train-present-without-horn cases. Curated clip accuracy is secondary diagnostic evidence only.

## 14. Vision protocol

The first vision baseline may use a configurable YOLO-compatible detector. Class IDs are read from versioned configuration/dataset metadata. Training, threshold selection, augmentation choices, and checkpoint selection are performed solely on training/validation data.

Layer A reports object-level metrics such as AP, precision, recall, class confusion, calibration, and failure slices. Layer B replays model outputs at original/equivalent temporal cadence and reports event-level outcomes. No image-level metric is presented as a gate-decision metric.

Hard negative images/video periods are mandatory for operational false-alarm measurement. Data from related frames, recordings, passages, crossings, or collection sessions must never span partitions.

## 15. Temporal evidence protocol

Temporal processing is a predeclared, configurable policy with source-specific confirmation windows, smoothing, evidence age/expiry, loss handling, and timestamp ordering rules. It consumes timestamped normalized evidence and emits explainable evidence states.

Temporal hyperparameters are chosen on validation events only. The final test sequences are not used to tune consecutive-frame counts, smoothing, confidence thresholds, alignment tolerance, or timeouts. Evidence that is stale, out of order, unavailable, or outside alignment tolerance must be explicitly represented rather than silently accepted.

## 16. Decision-engine specification

The initial engine is a transparent rule-based policy. It must state for every rule: inputs, source roles, calibrated evidence thresholds, temporal condition, resulting state action, priority, and explanation identifier.

Raw confidence values across front/side/rear/audio are not treated as numerically comparable without calibration. Calibration and threshold selection are validation-only. The decision engine must separate: (a) observation availability, (b) model evidence, (c) temporal evidence, and (d) state/gate command.

Opening is protected by an invariant: **missing evidence alone cannot authorize simulated opening.** A policy may begin opening only after its predeclared positive departure and independent/operational clearance conditions are satisfied.

## 17. State-machine specification

Initial conceptual states are `IDLE`, `TRAIN_APPROACHING`, `WARNING`, `GATE_CLOSING`, `TRAIN_PRESENT`, `CROSSING_OCCUPIED`, `TRAIN_DEPARTING`, `REAR_CONFIRMED`, `CROSSING_CLEAR`, `GATE_OPENING`, and `FAULT_FAIL_SAFE`.

Before implementation, `HAZARD_MODEL.md` and the state-transition table in `EXPERIMENT_PROTOCOL_V2.md` must define each permitted transition, guard, timeout, priority, prohibited transition, and handling of new evidence while opening. Gate state is independently represented as `OPEN`, `CLOSING`, `CLOSED`, or `OPENING`.

`FAULT_FAIL_SAFE` describes a simulated conservative closed-gate policy under stated detectable faults. It does not demonstrate physical fail-safe behavior or protect against unobservable faults.

## 18. Failure model

The study distinguishes:

- **observed source failures:** explicitly unavailable camera/audio stream, known dropped frames, malformed/stale/out-of-order evidence;
- **model errors:** false positive/negative/misclassification measured against ground truth;
- **simulated perturbations:** seeded, declared manipulations of recorded evidence used for sensitivity analysis only;
- **unobservable failures:** lens contamination, undetected clock drift, silent model degradation, or hardware/control failures not visible to software.

Failure injection cannot establish real-world resilience. Each injection must state the causal assumption, affected source, severity, detectability, expected simulated behavior, and metric.

## 19. Experimental baselines

All system variants are tested on the identical held-out Layer B event set, timing protocol, reference labels, and output rules:

- **B0:** Single-camera vision; independent-frame/no temporal logic.
- **B1:** Single-camera vision plus temporal filtering.
- **B2:** Two-camera vision plus temporal filtering.
- **B3:** Two-camera vision plus temporal filtering and state machine.
- **B4:** Audio-only continuous acoustic event detector.
- **B5:** Two-camera vision plus audio fusion without state-aware policy.
- **B6:** Two-camera vision plus audio, temporal processing, and state-aware policy.
- **B7:** B6 with each source removed in turn, plus predeclared detectable-fault simulations.

B0–B7 are information-content comparisons, not proof that a component is intrinsically necessary. Differences in available sources must be declared.

## 20. Ablation design

Use paired event-level comparisons on identical test events. Planned ablations are:

1. temporal filtering: B0 vs B1;
2. second camera: B1 vs B2;
3. state policy: B2 vs B3;
4. audio contribution: B2/B3 vs B5/B6 as protocol permits;
5. state-aware multimodal policy: B5 vs B6;
6. source dependence/fault sensitivity: B6 vs B7.

Viewpoint-class and detector-architecture comparisons are separate Layer A model-development experiments. Do not call a three-class detector versus a one-class detector a multimodal ablation.

## 21. Primary endpoints

Definitions in this section are provisional until `EVENT_LABEL_PROTOCOL.md` is finalized.

1. **Event-level missed-train rate:** number of evaluable train-passage events for which the policy fails to issue the predeclared simulated train/warning/closure indication by the defined event deadline, divided by evaluable train-passage events.
2. **Premature-opening rate:** number of evaluable train-passage events in which the policy issues simulated opening before independently labeled tail-clearance time (plus any predeclared conservative margin), divided by evaluable events with observable tail clearance.

Both endpoints must be reported separately; neither may be hidden by an aggregate score.

## 22. Secondary endpoints

- Train-event recall and false-event rate.
- False alarms per hour of evaluable no-train recording.
- Warning lead time relative to independently labeled crossing entry, reported as a distribution.
- Late-closure rate under a predeclared simulated timing model.
- Unnecessary-closure rate and closure-duration burden.
- Rear/departure confirmation latency relative to reference events.
- Calibration metrics: Brier score and expected calibration error, where appropriate.
- Recovery/behavior after modeled detectable component failure.
- Object-level vision and clip/window-level audio metrics, explicitly separated from primary system endpoints.

## 23. Statistical analysis plan

The primary analysis unit is train-passage event. Report event-level point estimates and confidence intervals; use event-level or hierarchical/cluster-aware resampling with crossing as a clustering factor where sample size permits. Do not derive significance from thousands of correlated frames.

Compare variants on the same event set using paired outcome differences and paired confidence intervals. Report exact event counts, crossings, exclusions, missing labels, and unpaired cases. Repeat model training over multiple seeds when computationally feasible and report variation; do not treat seeds as independent field events.

All primary endpoints, thresholds, comparisons, exclusions, and analysis code/configurations are frozen before inspecting final-test outcomes. Exploratory analyses must be labeled exploratory. Small samples require descriptive uncertainty, not strong generalization claims.

## 24. Leakage prevention

Partition by the highest available hierarchy:

`crossing → session → recording/video → train-passage event → frame/audio window`.

No descendant of any group may appear in more than one train/validation/test partition. The preferred test set contains unseen crossings. If this is impossible, use held-out sessions/events and state the weaker generalization claim. Prevent leakage from duplicate frames, resized/cropped copies, same recording audio windows, same train event, shared augmentation sources, and calibration/tuning on test data.

## 25. Reproducibility requirements

Version all data manifests, split assignments, annotations, source media identifiers/checksums where practical, code revision, environment/package versions, random seeds, trained checkpoints, calibration mapping, threshold values, state-policy configuration, and generated metrics/figures.

Every report row must trace to immutable input artifacts. Training data, validation data, test data, and mock fixtures remain visibly distinct. The full test set is evaluated only through versioned final runs; corrected analyses create a new run rather than overwriting history.

## 26. Limitations

- Results apply only to represented recordings, crossings, conditions, and assumptions.
- A horn is not guaranteed during train approach; audio can be absent or confused by traffic.
- Video-only clearance labels may be uncertain without a suitable independent view or calibrated geometry.
- Software replay cannot validate hardware faults, real actuation, communications latency, or physical safety.
- Small numbers of crossings/events may yield wide uncertainty and limited generalization.
- Rule-based policies are sensitive to the predeclared thresholds and ODD assumptions.

## 27. Claim boundaries

The strongest permitted claim, if the protocol is executed successfully, is:

> On synchronized, event-labeled recordings from the held-out represented crossings, the predefined two-camera, audio-assisted temporal state policy produced the reported event-level outcomes relative to the specified baselines.

The study must not claim certified safety, physical fail-safe operation, production readiness, hardware real-time performance, field deployment success, nationwide Bangladesh performance, or weather robustness beyond adequately represented held-out conditions.

## 28. Conference-level minimum viable study

For a normal/mid-tier international conference, the minimum credible study requires:

- Layer A plus a nontrivial Layer B synchronized event dataset;
- independent event labels, including evaluable tail clearance or an explicit narrowed endpoint;
- group-disjoint, preferably unseen-crossing, held-out sequences;
- documented annotation-quality pilot;
- B0–B6 fair comparisons on the same events;
- event-level primary outcomes, false-alarm exposure, uncertainty intervals, and failure analysis;
- clear software-simulation and ODD limitations.

If Layer B or independent clearance labels are unavailable, narrow the paper to viewpoint-aware vision detection (Layer A) and do not publish multimodal/state-policy reliability claims.

## 29. Optional stronger extensions

- Additional independently sensed crossing-clearance reference.
- More crossings/seasons and prospective held-out collection.
- Explicit multi-train/abnormal-operation dataset and policy.
- Real adverse-weather stratification with adequate test samples.
- Prospective field observation without actuation.
- A pre-registered analysis plan and external annotation audit.

---

## Decisions that must be finalized before implementation

| Priority | Question | Why it matters | Current best option | Alternative | Evidence required | Decider | Status |
|---|---|---|---|---|---|---|---|
| P0 | What is the study’s primary claim/unit? | Determines data, metrics, and validity. | Train-passage event; bounded held-out-crossing claim. | Narrow to Layer A viewpoint study. | Feasibility of Layer B collection. | PI/research lead. | Unresolved. |
| P0 | Can synchronized Layer B be collected? | Without it, system claim is invalid. | Collect two videos + audio per event. | Do not make system claim. | Pilot synchronized recordings. | Data-collection lead. | Unresolved. |
| P0 | How is tail clearance independently observed? | Required for premature-opening endpoint. | Annotated crossing zone from suitable geometry/independent view. | Omit premature-opening endpoint and narrow claim. | Geometry pilot and annotation review. | PI + annotators. | Unresolved. |
| P0 | What is the ODD/exclusion policy? | Prevents unsupported safety/generalization claims. | Single direction, single moving train events only initially. | Expand with labeled data and policy. | Dataset audit. | PI. | Proposed. |
| P0 | Is audio closure-triggering or supporting only? | Changes hazard behavior and baseline fairness. | Supporting evidence until held-out analysis supports independent closure. | Independent closure trigger under validation-only policy. | Audio pilot and false-alarm analysis. | PI. | Unresolved. |
| P0 | Is three-class viewpoint annotation reliable? | Taxonomy may inject label noise. | Pilot then retain only if agreement is acceptable. | Revise protocol after documented evidence. | Double annotation/adjudication study. | Annotation lead + PI. | Unresolved. |
| P0 | What is the leakage grouping hierarchy? | Invalid split inflates results. | Crossing→session→recording→event→window. | Stronger grouping where provenance permits. | Metadata audit. | Data lead. | Proposed. |
| P0 | What are primary deadlines/margins? | Needed to define missed/late/premature outcomes. | Predeclare from observed geometry and simulated policy. | Report event recall only if timing reference insufficient. | Label/geometry pilot. | PI. | Unresolved. |
| P1 | What calibration and threshold protocol applies? | Raw confidences cannot be fused fairly. | Validation-only calibration and tuning. | Class/source-specific non-comparable rules, disclosed. | Validation data. | ML lead. | Unresolved. |
| P1 | What state transition/fault semantics apply? | Prevents arbitrary simulated conclusions. | Formal transition/hazard tables in companion docs. | Narrow to temporal event detector. | Scenario review. | PI + systems lead. | Proposed. |
| P1 | What model baselines and seeds are feasible? | Ensures fair/replicable comparison. | One configurable YOLO baseline and simple audio baseline, repeated seeds if feasible. | Single-seed exploratory study, labeled limitation. | Compute/data audit. | ML lead. | Unresolved. |
| P2 | Is learned fusion justified? | Adds opacity and overfitting risk. | Start rule-based only. | Compare learned fusion after baseline evidence. | B0–B6 results with sufficient events. | PI. | Deferred. |
| P2 | Add hardware/extra sensors/more cameras? | Outside current claim and data. | Defer. | New separately scoped study. | New ODD/hazard/data plan. | PI. | Deferred. |
