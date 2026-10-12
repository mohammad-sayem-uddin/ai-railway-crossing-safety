# Pre-Coding Checklist

## Gate for DeepSeek V4 Pro Implementation

**Purpose:** Do not start research-system coding until all P0 items are complete. Generic repository/tooling setup is allowed only after the research lead records the decisions it depends on.

## 1. Research decisions — P0 required

- [ ] Primary research unit is frozen as one train-passage event, or the project is formally narrowed to Layer A vision only.
- [ ] Research claim and ODD are approved and exclude unsupported operations.
- [ ] Layer B synchronized-event feasibility is confirmed by a collection pilot, or system-level claim is removed.
- [ ] Independent tail-clearance/zone reference method is approved, or premature-opening endpoint is removed.
- [ ] Audio role is decided: supporting closure evidence by default; any independent closure trigger requires evidence and recorded decision.
- [ ] Three-class annotation pilot and adjudication plan are approved.
- [ ] Leakage hierarchy and final test partition policy are approved.
- [ ] Event deadlines, conservative clearance margin, and simulated-gate timing are defined or explicitly deferred with corresponding endpoint restrictions.

## 2. Dataset requirements

- [ ] Layer A and Layer B are documented as separate datasets with distinct purposes.
- [ ] Layer A has explicit positives, no-train negatives, provenance, grouping metadata, and annotation versioning.
- [ ] Layer B event bundle structure, metadata schema, geometry sheet, and source-quality flags are finalized.
- [ ] Permissions, privacy handling, and provenance requirements are documented.
- [ ] Split groups are available at crossing/session/recording/event/window levels or limitations are accepted in writing.

## 3. Annotation requirements

- [ ] `ANNOTATION_GUIDELINE_V2.md` is reviewed by annotators.
- [ ] Ambiguous, truncated, occluded, small, overlapping, and multi-train cases have a review disposition.
- [ ] Double-annotation pilot subset is selected before bulk annotation.
- [ ] Agreement, disagreement categorization, adjudication, and annotation-version retention are planned.
- [ ] `EVENT_LABEL_PROTOCOL.md` is piloted; `rear` is not used as tail-clearance ground truth.

## 4. Synchronized-data requirements

- [ ] Camera 1, Camera 2, and audio source roles and geometry are recorded per collection setup.
- [ ] Synchronization method, offsets/drift, and uncertainty are captured per event.
- [ ] A defined crossing reference zone and downstream tail-clearance boundary are visible or events are marked clearance-unobservable.
- [ ] Event context includes no-train intervals for false-alarm measurement.
- [ ] Exact synchronization limitations and exclusion thresholds are stated.

## 5. State-machine and hazard requirements

- [ ] `HAZARD_MODEL.md` is reviewed and ownership assigned for each hazard assumption.
- [ ] State-transition table has numeric/timing parameters, priorities, timeouts, recovery rules, and prohibited transitions.
- [ ] Invariant is frozen: missing detection alone never authorizes opening.
- [ ] New-train-during-opening, false/delayed rear, stale/out-of-order evidence, conflicts, and source loss have specified behavior.
- [ ] Fault injection is explicitly labeled a sensitivity simulation, not real-world validation.

## 6. Experiment and evaluation requirements

- [ ] B0–B7 variants use identical held-out Layer B events where they are comparable.
- [ ] Primary endpoints, denominators, eligibility, and exclusions are frozen.
- [ ] Calibration and threshold tuning are validation-only.
- [ ] Event-level uncertainty/paired comparison plan is approved.
- [ ] Image-level, audio-window-level, and system-level results are reported separately.
- [ ] Final-test data is protected from model, threshold, and policy iteration.

## 7. Reproducibility requirements

- [ ] Data manifests, annotation versions, group splits, configurations, seeds, environment, checkpoints, and output registry requirements are accepted.
- [ ] Mock fixtures are explicitly separated from research data/results.
- [ ] Reports will retain exclusions, missingness, and data-quality flags.

## Start condition

DeepSeek V4 Pro should begin **generic implementation only after all P0 boxes are checked and recorded in `RESEARCH_DECISIONS.md`**. It may then build data contracts, validators, split controls, configuration/reproducibility tooling, and mock-only software tests.

It must not implement or present a multimodal decision engine, state-machine evaluation, system-level experiment runner, or scientific performance workflow until Layer B data schema, event-label protocol, geometry/clearance method, synchronization policy, and transition parameters are finalized.
