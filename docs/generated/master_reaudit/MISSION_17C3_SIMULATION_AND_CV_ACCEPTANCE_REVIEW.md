# Mission 17C-3 — Simulation and grouped-CV acceptance review

Date: 2026-11-03, America/New_York. Repository: `/Users/sayemuddin/Desktop/Train_automation`. Branch: `main`. Audited baseline: `a0c4b8ca259dafe8f059a8406c3019e361798574`.

**AUDIT ONLY. NOT APPROVAL FOR IMPLEMENTATION OR PROTECTED EXECUTION.** Same-assistant disclosure: this assistant also authored 17C-0, 17C-1 and 17C-2. This is a methodologically fresh challenge with new calculations and source checks, not an independent human or institutional audit. No human identity, credential, approval or signature is invented.

Companions: [acceptance challenge](MISSION_17C3_INDEPENDENT_ACCEPTANCE_CHALLENGE.md), [security review](MISSION_17C3_SECURITY_AND_AUTHORIZATION_ACCEPTANCE_REVIEW.md), [simulation/CV review](MISSION_17C3_SIMULATION_AND_CV_ACCEPTANCE_REVIEW.md), [decision/release gate](MISSION_17C3_RESEARCHER_DECISION_AND_RELEASE_GATE.md).

<a id="simulation"></a>
## 1. Causal time and source integration

**C2's commanded actuator mathematics is coherent under its explicit assumptions. Integrated runner and practical CV acceptance remain incomplete.** The historical runner evaluates y_k, derives the new target and then applies it over elapsed dt, crediting the full interval if its endpoint is blocked. It sorts offline unless arrival order is preserved; duplicate/out-of-order records are already rejected without advancing the accepted state/clock (`src/railway_detection/simulation/runner.py:165-233`; `src/railway_detection/fusion/decision_engine.py:113-147`). Do not confuse defects in old proposal pseudocode with those existing rejection paths.

Convention B instead uses theta_k=F(theta_(k−1),u_(k−1),dt_k), accounts for the just-completed interval, then evaluates y_k and issues u_k effective only after t_k. Initialization at the first valid timestamp has no prior actuation. Observation, evaluation, issue and effective times coincide only in the declared ideal zero-compute-latency profile. Positive compute/transport delay needs explicit future command events and segment propagation. The actual controller evaluate_frame API accepts a MultimodalFrame, not the physical gate angle; no implicit theta feedback interface is established (`src/railway_detection/fusion/decision_engine.py:103-111`; `docs/generated/master_reaudit/MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md:29-57`).

| Boundary | Correct meaning / acceptance consequence |
|---|---|
| Observation | Sensor timestamp on declared local simulation clock; cannot infer media duration or GT cross-camera alignment. |
| Propagation and state record | Record pre-angle, already-active command origin/effective time and post-angle over (previous,current]. Then evaluate the current observation. A timer/cutoff has no fabricated sensor observation. |
| Command mapping | CLOSED/CLOSING both LOWER; OPEN/OPENING both RAISE until physical endpoints. HOLD must be explicit. Current nested gate_command is optional intention, not proof of previously applied command. |
| Input domain | C2 proposes integer microseconds or finite exact decimal-seconds strings; rejects bool/missing/negative/nonfinite/off-grid. Existing floats require an explicit versioned adapter/rejection policy, not silent rounding (C3-N08; `src/railway_detection/fusion/collector.py:16-23`). |
| Order/rejection | ARRIVAL preserves delivery order; duplicate/older canonical times cannot change accepted clock/counters/angle/command/durations. OFFLINE sorts validated time/index and cannot demonstrate arrival faults. |
| Horizon | Default last accepted timestamp. Explicit cutoff truncates or extends under known commands/timer policy with no invented observation. Invalid prefix stops and excludes incomplete run from completed totals; empty/single behavior explicitly specified. |
| Fault/watchdog | Fault commands must be selected/mapped prospectively; timeouts cannot lower the gate retroactively across an already elapsed gap. No hardware safety conclusion follows. |

Existing SimulationStep stores nested decision but no explicit applied-command field; DecisionRecord has optional gate_command. C2 correctly requires retaining missing-intent provenance as DERIVED_FROM_TARGET and rejecting conflict, rather than inventing historically logged intention (`src/railway_detection/simulation/runner.py:26-35`; `src/railway_detection/fusion/evidence.py:39-79`; `docs/generated/master_reaudit/MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md:53-75`).

## 2. Independently derived three-second profile and 84° fixtures

P3 uses theta 0=90°, T_close=T_open=3s, v_down=v_up=90/3=30°/s, clipped to[0,90]. A .2s active LOWER interval displaces 6°;90−6=84°. TC01 has u0=L at 0 and sample at .2, so exactly that interval is active. TC02 has H at 0,L at .2,L at .4; theta(.2)=90 and only(.2,.4] lowers to84. They share final angle because each has exactly .2s effective lowering, with different origins/horizons. They do not share identical full state/command histories (`src/railway_detection/simulation/gate_model.py:19-26`; `src/railway_detection/simulation/gate_model.py:47-69`; `docs/generated/master_reaudit/MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md:110-111`).

At 6s closing the displacement is 3°, hence87°; that is a distinct P6 scenario. An initial state different from 90°, cadence other than .2s, a delayed command or a HOLD initial interval changes the result.84° is a derived exact oracle for a commanded fixture, corroborated by fresh arithmetic, not an empirical result or full-controller safety latency.

Frozen controller settings require 2 confirmation frames and 2s warning dwell (`configs/frozen_experiment_v1.yaml:55-61`). With qualified constant approach input from IDLE at exact times0,.2,..., no intervening fault and unchanged policy, confirmation enters WARNING at .2; earliest lowering is at 2.2 on the exact synthetic clock. Applying that command prospectively gives first sampled blockage at 3.8 (42°), not an integrated84° result after the first sensor interval. This is a conditional source-derived trace, not an executed controller test; binary floating-point comparisons may alter boundary scheduling unless T02 specifies the adapter. The controller transitions on internal timers rather than measured theta (`src/railway_detection/fusion/decision_engine.py:387-430`).

## 3. Endpoint and continuous duration

Let b(theta)=1 iff unrounded theta≤45°. For each accepted physical/report interval (t_(k−1),t_k], D_E=Σdt_k b(theta_k). This right-endpoint quadrature can credit a whole interval although the threshold was crossed partway through it. D_C=∫b(theta(t))dt is the exact blocked-time integral for the specified synthetic piecewise constant-speed model, not observed physical occupancy or hardware truth.

For a segment of length d, initial angle q and speed v>0: HOLD contributes d b(q); LOWER contributes d if q≤45, otherwise max(0,d−(q−45)/v); RAISE contributes 0 if q>45, otherwise min(d,max(0,(45−q)/v)). Clipping to0/90 does not change these blocked portions. Splitting at reversals/timers/application times and summing gives D_C. Equality is blocked for endpoint classification; isolated equality times have zero integral measure. At q=45 with HOLD, the whole positive interval is blocked. Display rounding or a numeric angle-comparison tolerance must not widen the predicate (`docs/generated/master_reaudit/MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md:79-85`).

At 5Hz closure from 90° over 3s, endpoints k8…15 are blocked, so D_E=8×.2=1.6; continuous crossing at 1.5 gives D_C=1.5. At 10Hz, inclusive45° at k15 credits16×.1=1.6, still not1.5. A finer grid is not automatically an exact integral. The strict threshold checks at 45.0000001/45/44.9999999 produce False/True/True independently of displayed rounding. A microsecond input grid is precision, not calibrated physical accuracy.

C3-N09 counterexample: q0=90, LOWER from 0, horizon2. Grid[0,2] gives endpoint30°, D_E=2; adding a no-op boundary at 1 gives endpoints60°/30° and D_E=1. Both have identical path and D_C=.5. C2 already cautions that union-grid refinement changes the historical endpoint estimator (`docs/generated/master_reaudit/MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md:98`). Required correction: freeze and bind the report grid/event set, or retain a separate fixed reporting grid; never interpret timer-grid-induced changes as solely physical protection changes. D_C comparisons must retain their own model/units/limits.

## 4. Conditional Table 11 proof and counterexamples

On a common uniform grid h with fixed common u, same initial state/dynamics/predicate/horizon and F(theta 0,u0,h)=theta 0, define A_k=F(A_(k−1),u_k,h), B_k=F(B_(k−1),u_(k−1),h). Base B1=A0, induction B_k=A_(k−1). Therefore:

```text
D_E(B) − D_E(A)
  = h Σ[k=1..N] (b(A_(k−1)) − b(A_k))
  = h (b(A0) − b(A_N)).
```

No one-episode or symmetric-speed condition is needed. Reopening and later episodes cancel internally; identical asymmetric dynamics still give the lag. Initially open and terminal A-blocked yields−h; both unblocked yields 0. Initially blocked and terminal A-open yields+h, independently checked here with q0=0,u0=H followed by R. An initial active L at 90 violates the fixed point: at 6s with .2 steps, A=B=4.6s, delta0 despite uniform grid and terminal closure. Feedback recomputation or changed dynamics invalidates the shared-command assumption. This proof is a discrete endpoint identity, not a D_C theorem (`docs/generated/master_reaudit/MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md:89-100`).

For a common irregular grid the general comparison is Σdt_k[b(B_k)−b(A_k)], not−dt_final. With q0=90, u0=H thenL, ten.2 intervals plus.1: A=.7,B=.5,delta−.2 though dt_final=.1. With dt=[1,2], u=[H,L,R]: A=0,B=2,delta+2. Partial cutoff creates its own endpoint and weighting; it cannot inherit the uniform proof silently. Different reporting grids require rederiving the stated estimator, not just summing refined samples as though unchanged.

Fresh historical arithmetic selected exactly27 qualified event IDs from `results/experiments/B4/single_events.json`, then their correspondingly named timeline CSV reports. Parsing only timestamp_s and gate_state outputs found 6,737 rows,6,710 intervals, every interval .2s, initial90°/terminal0° in all 27, and endpoint durations matching preserved Table 11 (JSON float differences below1e-9). This is recomputation of existing report arithmetic, not replay/evaluation or physical-media evidence. The first two preserved values 46.0/28.8 imply 45.8/28.6 **only under the fixed-command lag assumptions**, not measured B runs (`results/experiments/tables/table11_per_event_summary.csv:1-3`; `docs/generated/master_reaudit/MISSION_16G_TABLE11_INDEPENDENT_VERIFICATION.md:264-278`).

16H's6,681/6,654 totals are historical arithmetic errors (`docs/generated/master_reaudit/MISSION_16H_INDEPENDENT_CHALLENGE_OF_16G.md:144-148`). Current source reproduces retrospective order, but the exact source/environment used for the historical run is NOT VERIFIABLE from a later documentation commit. Logs alone do not establish unchanged feedback commands for a new B implementation. Preserve historical results and label any conditional column analytical; no real B result or universal correction is certified.

## 5. Fresh numerical audit receipt

All entries below are **executed exact arithmetic** using compressed command knots plus analytic threshold intersections, compared with C2 A3. They are not execution of TC-SIM features. Accepted-prefix rows test only the arithmetic after hypothesized rejection; watchdog rows only the stipulated command schedules. Cases 14/15/19 remain requirements rather than executed repeatability/input/adapter tests (`docs/generated/master_reaudit/MISSION_17C2_CROSS_DOCUMENT_ACCEPTANCE_AUDIT.md:85-119`).

| C2 vector | D_E(B) | D_C(B) | Final theta(B) | D_E(A), if compared |
|---|---|---|---|---|
| 01 | 0 | 0 | 84 | not compared |
| 02 | 0 | 0 | 84 | not compared |
| 03 | 8/5 | 3/2 | 0 | not compared |
| 04 | 8/5 | 3/2 | 0 | not compared |
| 05 | 71/20 | 7/2 | 0 | not compared |
| 06 | 8 | 8 | 90 | 8 |
| 07 | 22/5 | 43/10 | 0 | 23/5 |
| 08 | 52/5 | 103/10 | 0 | 53/5 |
| 09 | 1/2 | 2/5 | 33 | 7/10 |
| 10-accepted-prefix | 0 | 0 | 78 | not compared |
| 11-accepted-prefix | 0 | 0 | 72 | not compared |
| 12-W1 | 0 | 0 | 60 | not compared |
| 12-W2 | 0 | 0 | 90 | not compared |
| 13-above | 0 | 0 | 450000001/10000000 | not compared |
| 13-equal | 1/5 | 1/5 | 45 | not compared |
| 13-below | 1/5 | 1/5 | 449999999/10000000 | not compared |
| 16 | 7/10 | 3/5 | 27 | not compared |
| 17 | 28/5 | 11/2 | 57 | 28/5 |
| 18 | 23/5 | 9/2 | 0 | 23/5 |
| 20-CLOSED | 2 | 3/2 | 0 | not compared |
| 20-OPEN | 0 | 1/2 | 90 | not compared |

Additional executed mathematical checks: identical-path no-op subdivision (2 versus1 endpoint seconds;.5 continuous in both), irregular positive delta+2, initially-blocked delta+.2, and closed-form full-tree counts below. No runner/controller feature or attack was executed. The inspected profiling test preserves current runner behavior only; its text does not validate proposed B semantics (`tests/unit/test_simulation_runner_profiling.py:47-100`).

## 6. Watchdog acceptance remains conditional

W1 schedules a future timer at last accepted sensor+selected timeout; old command integrates to that instant, response only after it. W2 discovers a gap only at a later valid observation; old command governs the elapsed gap. If no later observation arrives, W2 produces no timeout event. C2 TC12 with H at 1/1.2, responseL at 4.2, plus W1 timerL at 3.2 gives theta 60° for W1 and 90° for W2; both durations0. That is exact stipulated arithmetic, not selection or proof of fail-safe behavior (`docs/generated/master_reaudit/MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md:121`; `docs/generated/master_reaudit/MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md:144-148`).

T02/R04 must choose independent timer source/timebase, equal-time sensor priority, cancellation/generation, recurrence, fault response and horizon handling. Test stale timers, out-of-order sensor rejection with independently advancing timers, revoked/expired command policy, cutoff exactly at timeout and no next sensor. Missing/invalid timestamps abort under S3; a later fault response may not retroactively fabricate dt. No simulated closed angle is evidence of physical railway fail-safe hardware.

<a id="cv"></a>
## 7. Dataset foundations, lineage and missing evidence

V1 metadata identifies 3,157 development_baseline Roboflow images. Its import counts 2763/263/131 (`data/metadata/vision_v1_metadata.json:26-59`) differ from the separate historical 705d summary2218/467/472; these are distinct partition artifacts, not interchangeable counts. The latter contains 1,315 source-hint groups with fallback/risk flags and no warnings. Current splitter reads split_group_id, not a dynamic lookup of group_field. The flags do not prove its random ungrouped branch ran, physical-event leakage, near duplicates or causal memorization. Historical mAP50=.9946 is a preserved artifact value only (`data/metadata/vision_v1_metadata.json:1-28`; `src/railway_detection/data/split.py:40-54`; `src/railway_detection/data/split.py:93-152`; `experiments/vision/39f402dfe460/evaluation/metrics.json:29-40`).

V2 inventory contains 23 train-category,3 no-train-category and 1 engine-category events, distinct from approved training eligibility. Correct keys are train_events/event_001…023, no_train_events/event_001…003 and engine_events/event_001. Train event021 is not engine, and train003/009/016 are not controls. Inventory sign-off/physical content and a trustworthy V1 image→event join remain unverified; absence in the inspected metadata is not proof that no curator could supply it. None of weather/lighting/direction occurs as a top-level key of the 27 V2 entries; this does not establish absence in all possible records (`docs/generated/phase2/EXPERIMENT_DESIGN_CONSOLIDATED.md:24-29`; `docs/generated/master_reaudit/MISSION_17C2_REVISED_GROUPED_CV_SPLIT_SPEC.md:19-49`; `docs/generated/master_reaudit/MISSION_17C2_REVISED_GROUPED_CV_SPLIT_SPEC.md:84`).

| Required lineage | C2 requirement / actual acceptance gap |
|---|---|
| Physical event and aliases | Canonical pass identity across views/versions, with all aliases collapsed before counting. Group member IDs alone do not define an alias→canonical identity map; event_count must not count aliases as independent events. |
| Recording / original capture | Asset.source_capture_id resolves a bound identity record, possibly containing multiple events. C5 does not type the capture/event join or mandatory evidence roles/resolver. An independent still need not invent a video. |
| Camera / crossing / session | Must be traceable, or explicitly unknown with reason/claim limit. Camera/session appear in C2 prose; C5 has no explicit typed registry for them or crossing. Generic provenance bindings could carry them but required fields/validation are unspecified. |
| Weather / lighting / direction, if known | Preselected feature counts need per-event values, evidence, vocabulary and unknown dispositions. Group aggregates cannot establish individual lineage or support provenance. Never infer weather/direction from filenames. |
| Frame / PTS / timebase | VIDEO_FRAME needs exact frame/PTS/origin provenance; STILL_CAPTURE needs documented capture/event. Missing precision restricts claims; no raw media opened to establish it. |
| Derivatives / clips / augmentations | Every parent/transform/version/parameters and inherited component/role must be bound. No orphan/cycle or cross-role descendant. Multi-event policy exception lacks plural Asset origins (C3-N07). |
| Annotations | Exact asset identity, label vocabulary/policy/version, eligibility and legitimate empty-negative disposition. Missing label is not confirmed absence. |
| Duplicate evidence / camera overlap | Same physical pass across cameras must be linked; near-duplicate uncertainty blocks certified independence. Shared camera alone does not prove same event and grouping events does not prove independence from site/session background. |
| Fitted artifacts / caches | Per-fold base model/preprocessing/calibrator/checkpoint/cache provenance, exact fit/selection groups and parameters are required to certify no leakage; current generic exposure bindings do not fully type them. A precomputed train+test fitted normalizer leaks even when assignments are disjoint. |
| Role / exposure / source authority | Prospective corpus/eligibility/role plan and actual model-initialization exposure. UNKNOWN prohibits independent held-out/generalization claims; a new split cannot erase historical exposure. Evidence status labels/hashes are not approval/authenticity. |

C2's must-link connected components, strict absent/blank/unknown/ambiguous identity rejection and no fallback are correct requirements. Existing source/test evidence does not implement that full lineage validator: manifest can infer source names; split verification scans a dictionary of unique assignment keys, not full asset lineage (`src/railway_detection/data/manifest.py:183-213`; `src/railway_detection/data/split.py:159-167`; `tests/unit/test_split.py:25-72`). These tests were inspected, not executed; no split of any kind was generated.

## 8. Dataset-role and leakage acceptance

| Operation / role | Required separation and evidence |
|---|---|
| Base-model training | Only approved INNER_TRAIN or final outer training complement under frozen policy; no OUTER_EVAL, reserved control or incompatible final descriptive member. Record initialization and all fit memberships. |
| Inner-fold validation / model selection | INNER_TUNE inside current OUTER_TRAIN_POOL; early stopping, architecture, thresholds and checkpoint selection never inspect outer outcomes. Inner/outer subsets are compared within each iteration; training overlap across iterations is expected. |
| Preprocessing / augmentation / caches | Learned normalization/feature selection fits permitted training inputs only. Any cached fitted features bind exact model/transform/version/training groups; per-sample deterministic transforms still inherit event role/ancestry. Precomputed multi-event composites need versioned rejection/representation rule. |
| Score calibration | INNER_OOF only from properly out-of-fold inner predictions within outer training; reserved calibration only from explicitly reserved CALIBRATION_ONLY with no independent-evaluation reuse. Define base-model versus preprocessing versus calibrator fitting (C3-N06). |
| Development / outer evaluation | Frozen eligible DEVELOPMENT_POOL; exactly-once OUTER_EVAL across outer folds. Parent pool includes inner subsets intentionally. Repeated manual choices using outer outcomes are selection exposure even without code-level overlap. |
| Reserved controls / no-train analysis | RD025: confirmation pending, event-level counts/blocked seconds/episodes/per-stream exposure. Three short controls cannot become tuned thresholds then independent controls; no FAR/hour or permanent train-free claim. |
| Engine-only case study | RD024 excludes pooled M4/M5/occupancy/train outcomes; one physical event across versions. Does not establish detector-training ban/eligibility or zero-shot status; separate R03/R06 choice. |
| Final descriptive scope | Recorded V2 full-cohort design is not an approved new split or model-unseen set. Retain per-metric exclusions and prior-exposure limitations; no train-category event is transferred into model training here. |

No observed leakage experiment is alleged. These are necessary prospective controls. RD024/025 source directions remain unchanged (`docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:31-32`; `docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:46-48`; `docs/generated/phase2/EXPERIMENT_DESIGN_CONSOLIDATED.md:64-66`).

## 9. Determinism, feasibility, scaling and manifests

C2 defines exact lexicographic minimization of (event imbalance, preselected-feature imbalance, frame imbalance, assignment vector in sorted group order), using integer sums of squared deviations. Aligned records eliminate separately sorted-label misalignment; hard constraints dominate objectives; K/support/coverage are frozen prospectively. Minimum K supporting components for an every-fold stratum is necessary, not sufficient. Approximate grouped coverage may legitimately miss a rare stratum and must disclose that. No fallback, implicit K reduction, changed role or convenient label is allowed (`docs/generated/master_reaudit/MISSION_17C2_REVISED_GROUPED_CV_SPLIT_SPEC.md:76-103`).

The full K-ary prefix tree has N(M,K)=Σ[d=0..M]K^d=(K^(M+1)−1)/(K−1). C2 counts root and forbids pruning/symmetry/early incumbent acceptance; therefore its specified visited-node count for complete success or exhaustive infeasibility is this full number, regardless of hard-constraint failures detected only at leaves. For K=5: M=6→19,531; M=23→14,901,161,193,847,656; M=1315→a 920-digit number beginning 1747695286176400. Even at an unrealistically generous 10^9 nodes/second, M=23 exceeds 1.49×10^7 seconds (about 172 days) for the outer search alone, excluding inner searches and overhead. This is a mathematical lower-bound illustration, not a measured runtime .23 is hypothetical;1,315 source hints are not verified physical components. Actual approved development M is unknown.

C2 explicitly acknowledges this scaling limit. T03 must choose a bounded reference scope or approve a scalable deterministic solver with proof/verification of hard constraints, objective and canonical ties, or explicitly revise the optimization guarantee. Budget exhaustion correctly returns UNDETERMINED_BUDGET without accepted manifest even after finding an incumbent. It must never be called scientific infeasibility. No allocation was executed here.

Outer optimality is not nested feasibility. C2 explicitly freezes the outer optimum then solves its complements and blocks publication if any inner run fails. An illustrative mathematical witness: six equal-sized abstract groups p1…p6, a class in p1…p4, outer K=2 with balanced counts and no selected feature term, inner K=2 requiring that class in every INNER_TUNE. Lexicographically first balanced outer vector 000111 leaves one complement with only one supporting group, so it cannot satisfy inner coverage. An abstract alternative balancing the supporting groups 2/2 would meet that necessary inner support condition. This is a hand-stated bin-count witness, not generated split data or an allocator run. C2 correctly says failure of its frozen outer candidate does not prove all nested plans impossible (`docs/generated/master_reaudit/MISSION_17C2_REVISED_GROUPED_CV_SPLIT_SPEC.md:107-111`). Select full nested feasibility or explicit stop-and-reconsider behavior under T03; do not claim nested completeness.

Closed-world C5 lists fields and rejects unknown keys; it is a typed proposal, not an implemented JSON Schema. Group IDs/counts/objectives and whole-join receipts must be recomputed against verified evidence. C3-N05 requires typed capture/event/alias/feature/transform/fitted-artifact registries, mandatory binding roles and resolution rules. C3-N07 requires explicit rejection or versioned multi-event origins. Deterministic payloads must not contain volatile receipt timestamps; separate authenticated execution receipts bind the final payload digest, real code/config/eligibility/label/exposure/approval evidence and actual search status (`docs/generated/master_reaudit/MISSION_17C2_REVISED_GROUPED_CV_SPLIT_SPEC.md:115-145`).

C5 full detached digest and domain-separated outer subpayload correctly exclude inner self-reference while final digest binds inner_runs and verification. No intrinsic self-hash contradiction exists. However input evidence, output verification receipts and final execution receipt need a typed acyclic reference graph/resolver: do not require the final receipt digest inside its own input payload indirectly. Generic artifact references do not establish availability, authenticity or semantic evidence. No manifest digest or split artifact is created here.

## 10. Testable future acceptance gates

| Area | Required objective evidence after relevant decisions and X00 |
|---|---|
| Simulation contract | Adopted T02 version with legacy timestamp adapter, causal issue/application events, horizons, fault/timer ordering, fixed report grid and one strict predicate. |
| Actuator versus controller | Retain exact TC01/02 commanded84°; separately execute full-controller confirmation/dwell/fault traces and applied-versus-issued logs. Tests must reveal changes in conventions without changing other policy unnoticed. |
| Numerics / durations | Exact reference agreement for 21 vectors and boundary/initial-active/partial/irregular/asymmetric cases; test duplicate/order counters, invalid incomplete prefixes and no-op D_E/D_C grid behavior, not just printed values. |
| Watchdog | Choose W1/W2 and freeze source/priority/generation/fault/cutoff contract. Execute equal-time/cancellation/no-next-observation cases; no physical hardware claim. |
| CV inputs / roles | Approved corpus/lineage/exposure/eligibility/feature registries with complete typed joins and unknown restrictions before corpus-specific certification. No need to use real data to test generic synthetic validators. |
| CV algorithm | Resource-feasible deterministic reference/solver and nested feasibility policy; later small synthetic oracle comparisons, permutation/tie/budget/infeasibility receipts. No silent substitution for exact objective or no-fallback rules. |
| Leakage / canonical payload | Synthetic alias/multi-view/derivative/annotation/role/calibrator/cache/outer-selection negatives, typed canonical byte vectors, detached digest/reference-DAG verifier and recomputed counts. |
| Production / publication | Separate X06 split-only versus training, X02 checkpoint, X05 cache and X04 evaluation with genuine expected artifacts and resource permits. Feature cases and arithmetic do not create these permissions. |

All 20 TC-SIM and 14 CV-T cases remain proposed feature cases; none was run by this mission. The arithmetic receipt does not satisfy them. **STOP before any runner, splitter, training, replay or evaluation implementation/execution.**
