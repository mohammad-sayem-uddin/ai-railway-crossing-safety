# Mission 17F — Convention B controller integration plan

Date: 2026-11-04, America/New_York. Freshly verified baseline: `8221e96f8de48d995f4397a7e29255cdc8ec50f9`; branch `main`. Mission 17F authorizes source/metadata inspection, isolated synthetic audit tests, these five reports and normal exact-path Git delivery only. No implementation change or protected operation is authorized by this report.

**NOT INTEGRATED.** The actual controller owns research decision policy; the 17D helper accepts already-decided commands. A future selected adapter must preserve that distinction and resolve timestamp, physical-state, rejection, logging and estimator contracts before use. This plan is not permission to implement it.

Companions: [engineering audit](MISSION_17F_INDEPENDENT_ENGINEERING_AUDIT.md), [controller plan](MISSION_17F_CONVENTION_B_CONTROLLER_INTEGRATION_PLAN.md), [CV/OOF plan](MISSION_17F_CV_PROVENANCE_AND_OOF_IMPLEMENTATION_PLAN.md), [human/security readiness](MISSION_17F_HUMAN_REVIEW_SECURITY_READINESS.md), [gate register](MISSION_17F_IMPLEMENTATION_GATE_REGISTER.md).

## 1. Actual interfaces and ownership

| Existing interface | Inspected behavior | Future integration obligation |
|---|---|---|
| MultimodalFrame / collector | Float master timestamp plus vision/audio records, availability/health/age. Collector may use registered sync aligner. | Preserve local-camera versus explicitly aligned master time and evidence ages; no new cross-camera alignment inferred. |
| TrainGateDecisionEngine.evaluate_frame(frame, scenario_run_id) | Emits DecisionRecord, owns logical crossing state, target gate, counters, dwell/staleness/fault/recovery policy; receives no physical angle. | Exactly one evaluation per relevant frame under the selected clock/order policy. Do not infer a new decision from the actuator. |
| DecisionRecord | Float timestamp, previous/next logical states and gate targets, rule/fault/evidence/health fields, optional gate_command. | Map command and target consistently; preserve requested intention separately from applied physical command. Conflicting fields reject before actuation. |
| GateModel.step(dt_s,target_state) | Float constant-rate angle, duration clamp≥0.1s, physical OPENING/CLOSING/OPEN/CLOSED classification, blocked≤45. | Single owner of physical state under a selected versioned dynamics profile; distinguish logical target from physical motion. |
| SimulationRunner.run_frames | Sorts by default unless preserve_arrival_order, resets engine/gate, evaluates current frame then applies new target to preceding dt. Logs steps/results/rejected records. | This is the actual A ordering to preserve as the historical path. Future B ordering must be separately named and tested. |
| CausalRunner.run | Batch of SyntheticEvent target commands; no controller callback/streaming advancement API, synthetic-only identity; exact rational intervals/results. | A future pure coordinator/adapter is needed. Do not remove namespace restrictions and wire a real loader into this helper as an incidental edit. |

Sources: `src/railway_detection/fusion/collector.py:16-28`; `src/railway_detection/fusion/collector.py:50-109`; `src/railway_detection/fusion/decision_engine.py:65-167`; `src/railway_detection/fusion/evidence.py:39-79`; `src/railway_detection/simulation/gate_model.py:19-71`; `src/railway_detection/simulation/runner.py:165-300`; `src/railway_detection/synthetic/convention_b.py:188-229`.

## 2. Proposed precise coordinator contract

Future interfaces below are design names, not implemented code. A separately reviewed immutable RunSpec must bind source/code/config versions, convention, initial angle, close/open durations, timestamp conversion and tolerance policy, arrival/offline mode, origin/horizon, command latency, watchdog profile, estimator/report grid, controller config and decision-log schema. Solve F17-04 first so the receipt retains this complete recipe. Exact values and unknowns must survive serialization; a hash of caller-selected bytes is not researcher adoption.

Proposed `ControllerAdapter.decide(frame, clock_binding) -> DecisionEnvelope` wraps the existing engine once. Envelope binds source-frame identity, normalized master time, original lexical/float representation, controller state transition, requested target/nested command, rule/fault/health and issue boundary. Proposed `Actuator.advance_to(t)` applies only the previously active command and returns intervals; `issue(envelope)` validates and activates the new command after that boundary. Snapshot/reset semantics must make each run isolated and deterministic. Any reusable exact actuator extraction needs its own authorized source/test scope; it is not performed here.

Ordered B processing for a valid accepted boundary:

1. Validate the frame identity/time/order against the selected clock contract without mutating controller or actuator. Resolve any due synthetic timer only if that profile has been explicitly selected; keep timer events distinct from observations.
2. Advance physical state to t with the command that was active before t. At origin there is no pre-origin propagation.
3. Evaluate the actual controller once for that frame; retain full DecisionRecord. Validate target/nested command agreement. A failure after advancement produces an explicitly incomplete run and labeled prefix, not a completed result or fabricated decision.
4. Record requested command and activate it at its declared effective time. Default candidate zero latency means t, affecting only future positive intervals. Nonzero latency needs a separately specified queue, supersession/tie/cutoff policy and tests.
5. On terminal cutoff advance only existing commands/timers; do not create a sensor or call the controller with invented evidence. Produce separate event-grid, fixed-grid and continuous model durations with their grids/horizon.

A streaming coordinator must retain an event/interval ledger sufficient to calculate fixed-report endpoints without reevaluating policy. F17-05 calls for a monotone trajectory/report merge O(S+R), or indexed O(R log S), with event-grid total reused directly. Large exact rationals require bounded input sizes and measured resource limits in a separately selected runtime contract; no arbitrary hidden cap may alter valid scientific inputs.

## 3. Policy preservation and unresolved migration choices

Current controller takes no physical-angle feedback. Therefore, conditional on identical accepted frames, timestamps, configuration, call counts and state initialization, changing only actuation order should preserve its command stream. This is a source-derived conditional argument, **not an executed integration result**. Adding timer evaluations, rounding time, changing rejected-frame delivery or feeding angle back breaks its assumptions.

The actual path includes approach confirmation, warning dwell, closing time, positive rear clearance, audio-supported hold, departure-source staleness, new-train interruption and fail-safe recovery. With ideal exact 0.2s sampling and qualified approach at 0 and 0.2, the source indicates WARNING at 0.2, LOWER after the 2s warning at 2.2; a zero-latency B actuator first samples blocked at 3.8 with 42°. This illustrative conditional trace assumes continued valid evidence and no faults; it was not run through the controller and is not a Table 11 or hardware result. Sources: `src/railway_detection/fusion/decision_engine.py:387-430`; `src/railway_detection/fusion/decision_engine.py:461-609`.

| Migration risk | Required explicit choice / evidence |
|---|---|
| Float clock versus exact microseconds | Legacy duplicate epsilon 1e−9 and float dwell subtraction differ from exact µs. `legacy_float_to_us(3*0.2)` rejects. Prefer original exact tick index/decimal source if evidenced; otherwise approve a versioned mapping/rejection policy with error limits. Never silently round. Preserve original timestamps and conversion receipt. |
| Rejected frame semantics | Engine rules 8/10 early-return without ordinary state advance; runner logs rejected steps and sets aggregate fault_seen. Helper rejection alone does not reproduce those records/aggregates. Decide where engine rejection records are produced without evaluating accepted frames twice; test clock/state/command/metric equality on rejected inputs. |
| Offline versus arrival | Current default sort and explicit preserve_arrival_order must map to named modes. OFFLINE prevalidation/lookahead differs from live arrival and cannot certify live faults. Invalid future input/cutoff behavior must be explicit at the adapter. |
| Physical state versus logical target | Legacy duration clamp and OPEN/CLOSED tolerances differ from exact model and helper outputs. Define the shared allowed configuration and physical-state classifier, including initial non-90° angles; do not label a commanded CLOSED gate physically closed immediately. |
| Watchdog policy | Start policy-preservation candidates with helper watchdog NONE; retain actual source-staleness/fail-safe decisions on real frame boundaries. SCHEDULED/DETECT_ON_ARRIVAL adoption requires T02/R04 and dedicated evidence, not an engineering default. |
| Runtime errors and horizon | Empty/single/partial/incomplete results, configured cutoff and observed horizon must be distinct; no implicit media duration or pretending a prefix completed. Unknown command mapping is an error before issue. |
| Replay and profiling | Existing profiler metadata includes source/config/frame identity. A new log needs immutable RunSpec, exact decision/interval/rejection records and ordered input identity. Text inspection of profiling code is not permission to invoke its hashing/loaders. |
| Existing metrics | Keep warning lead time clipping, premature opening/fault counting and rejected-frame semantics explicitly versioned. Model blocked time is not observed train occupancy; continuous duration is not silently substituted for historical endpoint duration. |

Sources: `src/railway_detection/fusion/decision_engine.py:113-167`; `src/railway_detection/simulation/runner.py:185-233`; `src/railway_detection/simulation/runner.py:267-360`; `src/railway_detection/simulation/gate_model.py:19-71`; `src/railway_detection/synthetic/convention_b.py:30-49`.

## 4. Future synthetic acceptance cases — all planned, unexecuted integration

| Case | Required stimulus | Objective acceptance |
|---|---|---|
| CB01 | Same constructed frames/config through historical A and proposed B coordinator | Identical controller decision sequence under declared assumptions, exactly one call per frame; only declared actuator/metric differences. |
| CB02 | Qualified approach confirmation and warning/closing/clearance/opening boundaries | Full expected logical-state/target timeline plus separately derived physical angles; do not substitute the 84° commanded fixture for controller coverage. |
| CB03 | All-vision failure in IDLE/active, rear-source stale with another camera healthy, audio hold, new train and recovery | Preserve inspected rule precedence, dwell reset and fail-safe closure; sensor recovery alone does not invent clearance. |
| CB04 | Float 0.2, 3*0.2, off-grid, missing/duplicate/older/equal-epsilon events in each mode | Exact selected conversion/rejection, unchanged counters on rejects, full rule 8/10 audit and declared aggregate metrics. |
| CB05 | Empty/single/origin/interior/beyond-last cutoff, invalid future event and interrupted processing | Explicit status/origin/horizon; no future command or certified complete total from invalid prefix. |
| CB06 | Initial 0/45±δ/90, clipping, asymmetric rates and legacy duration limits | Exact threshold/dynamics and selected physical-state classification; mismatch outside shared profile rejects rather than claims parity. |
| CB07 | No-op boundaries, arbitrary fixed report grids, uniform A/B identity and irregular/partial counterexamples | Continuous/fixed-grid subdivision invariance; event-grid differences labeled; no universal correction. |
| CB08 | Explicitly selected optional timer profiles, equality/reject/generation/cutoff; default NONE | Deterministic priority, no fabricated observation, no retroactive response; default controller policy unchanged. |
| CB09 | Two runs/reset, invalid command, interrupted output, config changes and identical no-motion trajectories | No state leakage; complete config/input binding, distinct config identity, immutable audit, deterministic exact output. |
| CB10 | Growing interval/report grids with operation counters | Default report O(S), explicit-grid declared O(S+R) or O(R log S); same exact numerical oracle. |
| CB11 | Pure synthetic adapter with forbidden resource hooks | Zero media/model/cache/file-loader use; production routing remains disabled until separate gates. |

These cases supplement the freshly reproduced 114 tests and 17F audit fixtures. Existing historical A/known result bytes must be preserved with explicit expected checksums in a future implementation acceptance receipt. No real replay is needed for this synthetic stage. All CB cases are **PLANNED — NOT EXECUTED** here.

## 5. Dependency order and handoff

Researcher T02/R04 selects actual runner, clock/fault/latency/estimator contract; relevant R02 camera scope stays unchanged unless separately amended. Future explicit engineering scope then covers F17-04/05, a pure adapter/coordinator and CB tests. Review exact source/config diffs and synthetic evidence before any default-routing decision. Research adoption and authentic X01/X02/X04/X05 plus applicable approved data/GT/evaluation records remain separate gates for any real execution. No current authorization permits even that integration implementation. STOP at these plans and wait for researcher review.
