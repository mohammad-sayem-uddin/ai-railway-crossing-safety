# Mission 17C-2 — Revised Convention B simulation specification

Date: 2026-11-03. Repository: `/Users/sayemuddin/Desktop/Train_automation`. Baseline: `d4353ad9d49d427a129a9a4e83023fbd24e1a111` on `main`.

**PROPOSED SPECIFICATION — RESEARCHER REVIEW PENDING — NO IMPLEMENTATION OR REAL-DATA AUTHORIZATION.** Every future rule, interface, algorithm, transition and test in a section marked PROPOSED is proposed behavior, not implemented functionality or an adopted decision. VERIFIED facts below describe inspected source/text or exact document arithmetic only. PARTIALLY VERIFIED means support is conditional; CONTRADICTED means source/counterexample disagrees; UNSUPPORTED means evidence does not justify a claim; NOT VERIFIABLE means required evidence is unavailable or prohibited. NOT VERIFIED explicitly flags an unestablished fact without inventing a sixth claim classification.

Companion documents: [Human review/security](MISSION_17C2_REVISED_HUMAN_REVIEW_AND_SECURITY_SPEC.md) · [Simulation](MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md) · [Grouped CV](MISSION_17C2_REVISED_GROUPED_CV_SPLIT_SPEC.md) · [Decision/traceability register](MISSION_17C2_INTEGRATED_DECISION_AND_TRACEABILITY_REGISTER.md) · [Acceptance audit](MISSION_17C2_CROSS_DOCUMENT_ACCEPTANCE_AUDIT.md).

Historical 17B and C1 files are preserved unchanged. This document consolidates a candidate acceptance contract; it does not silently replace a historical record, adopt a protocol, approve Option C, appoint a person, issue/consume a token or authorize a next mission. R01–R08 and T01–T04 remain PENDING; X00–X07 remain NOT AUTHORIZED, with C1 qualifications preserved in the register.

Mission boundary: no raw-media inspection/preview/playback/decode/hash; no checkpoint or protected-cache access; no real inference/training/replay/evaluation/calibration/split generation; no annotation/adjudication/promotion; no source/test/config/protocol/governance edits. Only the five named documents and safe temporary documentation-validation scripts are created. Planned feature tests are not passing test results.

<a id="s1"></a>

## S1. VERIFIED baseline, terminology and historical preservation

VERIFIED: the current runner evaluates a decision, maps resulting_gate_state and applies that newly selected command across the preceding elapsed dt before endpoint accumulation (`src/railway_detection/simulation/runner.py:185-233`). This is historical **Convention A**, not a newly implemented B. Rejected arrivals are handled separately in current source (`src/railway_detection/simulation/runner.py:197-218`); the old proposed17B sort/clamp pseudocode is not the whole current rejection implementation. Existing SimulationStep embeds DecisionRecord (`src/railway_detection/simulation/runner.py:26-35`), which already has optional gate_command (`src/railway_detection/fusion/evidence.py:39-79`). The actually applied value comes from resulting_gate_state, so nested issued intent and applied action must not be assumed identical without checking.

VERIFIED: current opening/closing defaults are3.0s, initial angle90°, speed 30°/s; blockage is the unrounded predicate theta≤45° (`src/railway_detection/simulation/gate_model.py:19-45`; `configs/frozen_experiment_v1.yaml:55-61`). Current fully-closed≤.05 and fully-open≥89.95 flags are separate source properties, not an alternative blockage predicate. A future B runner, its logging contract and its acceptance suite remain PROPOSED. No production source/test/config is modified.

VERIFIED as historical report values: Table11 starts46.0s/28.8s, not 38.4s/42.6s (`results/experiments/tables/table11_per_event_summary.csv:1-3`). C1's report contains the 27-file arithmetic receipt and qualified historical6,737-row/6,710-interval total (`docs/generated/master_reaudit/MISSION_17C1_INDEPENDENT_CHALLENGE_OF_17C0.md:894-927`); C2 does not rerun a real simulation or recertify those outputs. The historical run's exact execution-source binding is NOT VERIFIABLE from the later documentation baseline alone (`docs/generated/master_reaudit/MISSION_17C1_INDEPENDENT_CHALLENGE_OF_17C0.md:662-671`). Keep every historical value/artifact unchanged. Any45.8/28.6 derived values require S5 assumptions and R04 (metric/reporting decision); they are not measured Convention B results.

<a id="s2"></a>

## S2. PROPOSED time, command and state contract

All rules in S2–S8 and every TC-SIM case are PROPOSED, pending T02/T04/R04 and separate X00. Parameters selected here define the candidate **P3 parity test profile**, not an adopted production change: closing 3s/opening 3s, down/up speed 30°/s, angle clipped to[0,90], initial90° unless a case explicitly overrides it. Six-second examples are excluded from P3; any retained6s design is a separately named P6 experiment with 15°/s and recomputed oracles, not historical parity.

| Term (PROPOSED) | Exact meaning |
|---|---|
| observation timestamp t_k | Accepted sensor observation's local simulation clock; canonical integer microseconds, also displayed as exact decimal seconds. Original input representation retained. |
| decision evaluation time | Logical event time at which the controller evaluates the accepted observation after propagation. In the idealized zero-compute-latency profile it is t_k, not a measured wall-clock runtime. |
| command issue time | Logical time the validated decision emits u_k. Zero-latency test profile uses t_k; a future positive-latency profile must insert a later explicit command event. |
| command application time | The validated issue/effective time; u_k governs only time strictly after that boundary. It never applies to the preceding interval. |
| interval start/end | (t_(k−1),t_k] for a sensor-only grid, or successive boundaries of an explicitly merged sensor/timer/command/cutoff grid. |
| state before/after interval | theta_(k−1) before any propagation of that interval; theta_k after propagation by its already-active command(s), before the endpoint sensor issues a new command. |
| actual applied command | The command actually active over the logged interval or segment, with origin decision/event ID and effective time. Not inferred from the new endpoint decision. |
| nested decision-issued command | The validated command intention emitted by the endpoint decision, retained alongside resulting_gate_state and their mapping/provenance. It may differ from the interval's applied command because it affects future time. |
| simulation horizon | Default last accepted observation. An explicit cutoff is a separate input, never guessed from recording length or a future sensor frame. No actuation before the initial timestamp. |
| endpoint duration D_E | Sum of each propagated interval's length times its final blocked indicator; discrete right-endpoint estimator. |
| continuous duration D_C | Integral of blocked(theta(t)) over the same declared horizon under the specified constant-speed piecewise actuator model; optional separate mathematical output, not physical measurement. |

<a id="s2-1"></a>

### S2.1. PROPOSED update order

At the first accepted timestamp t0, validate/reset the initial state, append an initialization record with dt=0 and applied_command=NONE, then evaluate y0 and validate/issue u0. No hidden pre-recording motion occurs. For every later accepted boundary: validate time before subtraction; propagate the previous active command from the last accepted boundary to this one; account for that interval; expose the resulting theta to any explicitly supported controller interface; evaluate only observations available now; validate/record new u_k; activate it for future time. NONE denotes no elapsed initialization interval, not HOLD behavior for an actual interval.

An actual positive processing/actuation delay requires distinct observation/evaluation/issue/application timestamps and explicit propagation between them using the old command. It cannot be approximated by moving the new command into an already elapsed interval. Source wall-clock profiling does not automatically define these logical latencies. No new physical delay is invented.

<a id="s2-2"></a>

### S2.2. PROPOSED command mapping and consistency

CLOSED/CLOSING map to LOWER until 0; OPEN/OPENING map to RAISE until 90, preserving current target-state behavior (`src/railway_detection/simulation/gate_model.py:55-69`). HOLD is an explicit no-motion command, not an automatic mapping from a target state named CLOSED or OPEN. A proposed adapter records original resulting_gate_state and optional gate_command plus the normalized issued command. If the optional field is absent, derivation from the explicit target must be marked DERIVED_FROM_TARGET with the source decision ID. If both exist but conflict, abort before activating the inconsistent command; do not silently choose one. Unsupported reset/fault/rejected-frame command mapping is rejected pending an explicit T02 contract. A rejected sensor arrival does not issue a replacement command.

<a id="s3"></a>

## S3. PROPOSED input modes, horizon and interval record

ARRIVAL mode preserves input order. Duplicate or older canonical timestamps are recorded as rejected arrivals without changing accepted time, theta, controller counters, active command or D_E/D_C. OFFLINE mode validates inputs then stable-sorts by (canonical timestamp, original input index) and discloses reordering; duplicates are rejected once, and this mode cannot establish arrival-order fault handling. Tests select their mode explicitly.

PROPOSED canonical timestamp input is a nonnegative integer microsecond value or finite decimal-seconds string exactly representable on that grid. Reject booleans, missing/nonfinite/negative values and off-grid values; do not silently round/clamp. An invalid numeric timestamp aborts the run without a fabricated dt or further actuation. This stricter proposed adapter is distinct from the current engine's1e−9 comparison logic (`src/railway_detection/fusion/decision_engine.py:113-147`); adopting it is T02, not a claim of compatibility or scientific accuracy.

PROPOSED cutoff: default horizon is the last accepted observation. An explicit cutoff before t0 is invalid; equal to t0 yields zero duration. For a cutoff inside a later interval, propagate only to it using commands that became effective at/before it; do not evaluate a later observation. A cutoff beyond the last observation permits only explicit terminal propagation under the still-active command and selected timer policy; it creates no sensor observation. Empty input returns no intervals, zero durations and null horizon; a single frame has zero duration unless an explicit authorized-profile cutoff extends it.

| Required interval/event field (PROPOSED) | Validation |
|---|---|
| run/profile/version, convention, parameters/classifier/estimator identifiers | Bind source/config/reference contract; A historical and B proposed remain distinct. |
| interval_id, start_us, end_us, dt_us; event_kind | Exact positive dt=end−start for propagated intervals; initialization uses dt0; timer/cutoff/rejection are explicitly typed. |
| pre_angle, post_angle, applied_command, effective_us, origin_decision_id | Exact reference angle rational or declared numeric representation; apply only an already-effective command. Split a timer/delayed-command interval into segments. |
| observation_id/time, decision_id/evaluation_us, issued_us/application_us | Null where no observation/decision exists; no fabricated frame at timer/cutoff. |
| original target and optional nested gate_command; normalized issued_command, mapping provenance | Consistency check precedes activation. Missing optional source intent is disclosed, not fabricated as historically logged. |
| blocked predicate/result, D_E increment/total; optional D_C increment/total | One strict unrounded theta≤45 predicate; display rounding cannot change the bit. Never merge the two estimators under “closed time.” |
| rejection/fault/timer reason, input index, selected horizon and command validity | Rejected arrivals live in a separate ledger; accepted physical intervals never overlap/double count. |

<a id="s4"></a>

## S4. PROPOSED actuator and duration mathematics

For positive dt and valid theta in[0,90], F(theta,LOWER,dt)=max(0,theta−v_down*dt), F(theta,RAISE,dt)=min(90,theta+v_up*dt), F(theta,HOLD,dt)=theta. v_down=90/T_close and v_up=90/T_open are positive. P3 uses30 for both, but asymmetric profiles must declare both rates. Physical direction/speed data are NOT VERIFIED; this is a constant-speed synthetic model.

Use exactly b(theta)=1 if theta≤45, otherwise0, on unrounded internal state. In the sensor-only B profile theta_k=F(theta_(k−1),u_(k−1),dt_k); D_E(B)=sum(dt_k*b(theta_k)). A's retrospective reference uses u_k instead. Timer/delayed-command profiles integrate consecutive actual command segments on their explicit event grid.

PROPOSED optional D_C for one constant-command segment starting at theta and lasting dt: HOLD contributes dt if theta≤45 else0; LOWER contributes dt if theta≤45 else max(0,dt−(theta−45)/v_down); RAISE contributes0 if theta>45 else min(dt,max(0,(45−theta)/v_up)). Sum segments including clipping/reversals. Isolated equality instants have zero measure for D_C while an endpoint equality can credit a full D_E interval. The exact threshold integral is mathematically defined for this model, not an estimate of physical-media truth.

<a id="s5"></a>

## S5. Mathematical proof and limits of an analytical correction

VERIFIED by the following derivation, conditional on **fixed common commands**, common theta0, the same uniform grid/horizon, same deterministic F (including both rates), same predicate and F(theta0,u0,h)=theta0. A_k=F(A_(k−1),u_k,h); B_k=F(B_(k−1),u_(k−1),h). Then B1=A0 and induction yields B_k=A_(k−1). Therefore for the endpoint estimator:

    D_E(B) − D_E(A) = h * sum(b(A_(k−1)) − b(A_k))
                     = h * (b(A0) − b(A_N)).

For initially open and terminal A-blocked this is−h. It equals−dt_final only in this uniform setting where dt_final=h and all other stated assumptions hold; it is **not a universal −dt_final rule**. Multiple episodes do not multiply the boundary term. Equal upward/downward rates are unnecessary if the same asymmetric F is used in A and B; if the dynamics differ, the lag proof does not apply. Initial LOWER at 90 violates the fixed-point condition. An initially blocked state changes b(A0). Recomputed feedback may change commands; no fixed-command shortcut certifies that closed-loop run.

For irregular grids, changed dynamics/commands or mismatched origins/cutoffs use the general comparison sum(dt_k*(b(B_k)−b(A_k))) on a common explicitly partitioned horizon, deriving both state sequences. If time grids differ, refine their union into actual command segments and state which estimator is being compared; do not call an arbitrary refined endpoint sum the unchanged historical estimator. D_C uses its own segment integral and has no automatic D_E boundary identity. Source challenge/proof basis: `docs/generated/master_reaudit/MISSION_17B_CONVENTION_B_SIMULATION_DESIGN.md:330-344`; `docs/generated/master_reaudit/MISSION_17C1_INDEPENDENT_CHALLENGE_OF_17C0.md:824-855`.

Counterexamples (VERIFIED exact arithmetic): ten.2s intervals plus.1s with theta0=90,u0=HOLD,u1…11=LOWER give A=.7,B=.5, delta−.2 despite dt_final=.1. dt=[1,2], u=[HOLD,LOWER,RAISE] gives A=0,B=2. Initial LOWER with 30 uniform.2s intervals gives A=B=4.6. These are document arithmetic, not feature tests or real-data results.

<a id="s6"></a>

## S6. PROPOSED definitive TC-SIM test-oracle matrix

All cases are NOT EXECUTED future tests. Commands H/L/R mean HOLD/LOWER/RAISE, issued at the corresponding boundary. Every sequence explicitly includes u0 and uN (the final issue has no effect before the horizon). Unless overridden, parameters are P3, theta0=90, zero logical processing latency, strict theta≤45, mode ARRIVAL with increasing valid times and no watchdog. Each mathematical oracle uses exact rational arithmetic; future angle/duration numeric checks may use absolute error≤1e−9 degrees/seconds, but the blocked bit must match the strict reference exactly and cannot be excused by that tolerance. Display rounding and an epsilon-expanded predicate are excluded. Equality comparisons on canonical timestamps are exact integer checks.

| Test / PROPOSED contract | Initial / parameters | Complete command input | Time grid / horizon | State transitions and interval accounting | Expected final state | Expected D_E(B); A comparison if used | Optional D_C(B) | Exact/numeric scope; claim it can/cannot establish |
|---|---|---|---|---|---|---|---|---|
| TC-SIM-01 first-frame causality | theta0=90; P3 | u0=u1=L | t=[0,.2]; horizon.2 | Initialization leaves90; only(0,.2] applies L, post84; no blocked interval | angle=84°, lowering |0 |0 | Exact reference84° (not 87°); numeric angle check only; no lag-theorem assertion because u0 is active. |
| TC-SIM-02 delayed issue | theta0=90; P3 | [H,L,L] | t=[0,.2,.4]; horizon.4 | theta=[90,90,84]; u1 does not act on(0,.2] | angle=84°, lowering |0 |0 | Exact; establishes issue/application separation, not a6s actuator. |
| TC-SIM-03 5Hz closure | theta0=90; P3 | u0…u15=L | t=k/5,k=0…15; horizon3 | theta_k=max(0,90−6k); first blocked k8 at 1.6/42°; intervals k8…15 credited | angle=0° fully closed at 3 |1.6 |1.5 | Exact reference; D_E differs from integral; numeric checks do not prove physical accuracy. |
| TC-SIM-04 10Hz closure | theta0=90; P3 | u0…u30=L | t=k/10,k=0…30; horizon3 | theta_k=max(0,90−3k); k15 at 1.5/45° is blocked;16 intervals of.1 credited | angle=0° fully closed at 3 |1.6 |1.5 | Exact inclusive threshold oracle; no assumption an endpoint sum equals integral at a finer grid. |
| TC-SIM-05 explicit irregular sequence | theta0=90; P3 | u0…u20=L | dt=[.10,.35,.05,.50] repeated exactly 5 times; t0=0; horizon5 |20 intervals; first blocked at 1.5/45°, whose.05 interval is fully credited; subsequent3.5s credited | angle=0° fully closed |3.55 |3.5 | Exact; repairs ambiguous allowed-value notation and 15°/s rate; does not test all irregular patterns. |
| TC-SIM-06 complete cycle | theta0=90; P3 | u0=H;u1…20=L;u21…40=H;u41…70=R | t=.2k,k=0…70; horizon14 | Common A/B commands; initial fixed point; B begins lowering at.2, reaches0° at 3.2, raises at 8.2 and reaches90° at 11.2; episode boundaries telescope | A/B angle=90° open |8; A=8; delta0 |8 | Exact conditional boundary identity; not every closed-loop controller or every “complete cycle.” |
| TC-SIM-07 terminal blocked | theta0=90; P3 | u0=H;u1…30=L | t=.2k,k=0…30; horizon6 | B first blocked at 1.8/42°;22 intervals credited; A has 23 | A/B angle=0° closed |4.4; A=4.6; delta−.2 |4.3 | Exact under S5 assumptions; no unconditional−dt_final or real Table11 execution. |
| TC-SIM-08 multiple episodes | theta0=90; P3 | u0=H;u1…20=L;u21…40=R;u41…60=H;u61…100=L | t=.2k,k=0…100; horizon20 | B first blocks at 1.8, becomes unblocked at 5.8, blocks again at 13.8; endpoint episode4s plus terminal6.4s; intermediate transitions cancel | A/B angle=0° closed |10.4; A=10.6; delta−.2 |10.3 | Exact; two episodes do not compound uniform boundary shift. |
| TC-SIM-09 partial terminal interval | theta0=90; P3 | u0=H;u1…11=L | dt=ten×.2 then.1; horizon2.1 | B blocked endpoint intervals.2+.2+.1; no terminal-only shortcut | theta_B=33°,theta_A=27°, both blocked |.5; A=.7; delta−.2 |.4 | Exact counterexample to universal−.1 result; no extrapolation after cutoff. |
| TC-SIM-10 duplicate arrival | theta0=90; P3; ARRIVAL | Accepted issues L; duplicate payload tries R and must never evaluate/issue it | Arrivals[1,1.2,1.2,1.4]; horizon1.4 | Accepted angles90,84,78;2 propagated.2 intervals;3 accepted boundary records and 1 separate rejection | angle=78°, activeL |0 |0 | Exact rejection/count oracle; no clock/counter/command advancement on duplicate. |
| TC-SIM-11 out-of-order arrival | theta0=90; P3; ARRIVAL | Accepted issues L; rejected1.2 payload tries R | Arrivals[1,1.4,1.2,1.6]; horizon1.6 | Accepted angles90,78,72; intervals.4 then.2 from last accepted1.4; one rejection | angle=72°, activeL |0 |0 | Exact; sorting first would change this test and is not allowed in ARRIVAL. |
| TC-SIM-12 watchdog alternatives | theta0=90; P3; conditional W1/W2, timeout2s only a synthetic fixture | Sensor fixtures issue H at 1,1.2; both profiles issue endpoint response L at 4.2; W1 also has timer-issuedL at 3.2, W2 has no earlier timer | Sensors[1,1.2,4.2]; W1 adds3.2; horizon4.2 | W1 oldH until 3.2 then1s L; W2 oldH over entire gap and L affects only later time | W1 angle=60°/L; W2 angle=90°/L |0 in both profiles |0 in both profiles | Exact conditional alternatives, neither selected/adopted; cannot establish a fail-safe implementation or approved timeout. |
| TC-SIM-13 threshold boundaries | Three theta0 overrides:45.0000001 /45 /44.9999999; P3 speeds | [H,H] for each independent subcase | t=[0,.2]; horizon.2 | Angles unchanged; strict bits False/True/True for both endpoints; no rounding/epsilon | Same angle as each initial state |0 /.2 /.2 |0 /.2 /.2 | Exact predicate result; future numeric angle tolerance never permits wrong blocked bit or a1µs physical-accuracy claim. |
| TC-SIM-14 repeatability | Exactly TC05 profile/inputs | Exactly TC05 command vector,100 separate fresh runs | Exactly TC05 grid/horizon | Canonical result records, resets, states and both sums identical on every repetition | angle=0°; same as TC05 |3.55 each |3.5 each | Exact canonical-byte repeatability requirement; no runs executed here, no physical/general correctness conclusion from zero variation. |

<a id="s6-1"></a>

### S6.1. PROPOSED additional boundary/integration cases

The same parameter/predicate/numeric rules apply unless explicitly overridden. These cases supplement the original 14 without representing a completed suite.

| Test (PROPOSED) | Initial / commands / grid / mode | Required transitions/accounting/final state and duration | Exact/numeric claim and limit |
|---|---|---|---|
| TC-SIM-15 invalid/empty/single | P3; invalid initial or later timestamp in {missing,NaN,infinity,negative,bool,off-grid}; empty input; or one frame at 0 issuingL | Invalid input aborts before its propagation with no fabricated dt; preserve any prior committed prefix, mark run incomplete and exclude from completed totals. Empty: no steps, theta absent, D_E=D_C=0,horizon null. Single: theta90 unchanged, u0L future only, D_E=D_C=0,horizon0. | Exact state/error oracle; no broad production input-validation result. |
| TC-SIM-16 explicit terminal cutoff | theta0=90,P3,u0…u10=L,t=.2k,k0…10,explicit cutoff2.1 | Propagate finalL for.1 with CUTOFF event and no sensor/decision; final27°; D_E=.7,D_C=.6. Cutoff before origin rejects; at origin gives0 and 90°. | Exact reference; extension is an explicit synthetic profile, not guessed media duration or a real authorized replay. |
| TC-SIM-17 common asymmetric dynamics | theta0=90,down30/up15 (close 3/open 6),u0H,u1…20L,u21…40R,t=.2k,k0…40,horizon8 | A final60°,B57°,both unblocked; D_E(A)=D_E(B)=5.6; D_C(B)=5.5. Initial fixed point and same asymmetric F preserve the lag proof. | Exact separately named asymmetric experiment; does not change P3 or prove identity when A/B dynamics differ. |
| TC-SIM-18 initial active command | theta0=90,P3,u0…u30=L,t=.2k,k0…30,horizon6 | A/B both final0°,D_E=4.6,D_C(B)=4.5; delta0. S5 fixed-point assumption fails. | Exact counterexample; cannot apply−.2 merely from uniform cadence/terminal blockage. |
| TC-SIM-19 conflicting nested issue | theta0=90,P3,t=[0,.2]; initial decision targetCLOSING but nested gate_commandOPEN | Abort before activation/any interval; theta90, D_E=D_C=0 for the committed zero-length prefix; no completed-run result. | Exact adapter rejection; does not establish provenance of historical exports that omit this field. |
| TC-SIM-20 target-state mapping | Two subcases:theta0=60,targetCLOSED→L throughout;theta0=30,targetOPEN→R throughout. P3,t=[0,1,2],horizon2 | CLOSED case60→30→0,D_E2,D_C1.5; OPEN case30→60→90,D_E0,D_C.5. Target label never forces HOLD prematurely. | Exact reference plus numeric checks; not a physical motor test or a changed controller policy. |

PROPOSED precision means timestamp representation/resolution; numerical accuracy means agreement with the exact model reference; physical accuracy requires independent observed/calibrated evidence and is NOT VERIFIABLE here. The1e−9 numeric acceptance bound is a candidate software comparison tolerance, not a scientific boundary-agreement tolerance, expanded angle threshold or physical timing guarantee. Reference arithmetic is exact rational; any future floating implementation must meet state and classification oracles, including exact-threshold cases, rather than round state to manufacture agreement.

<a id="s7"></a>

## S7. PROPOSED watchdog choices requiring decisions

W1: independent scheduled timer at last accepted sensor time+selected timeout; integrate old command to that timer, apply its prospective command only after it, then integrate onward. New valid sensor input cancels/reschedules the prior generation; stale timer events cannot fire. Sensor-versus-timer priority at an exactly equal timestamp, timer event source, missing-data/fault command, recurrence and horizon policy must be frozen under T02/R04 before acceptance. TC12 deliberately has no equal-time collision; it supplies exact conditional oracles without choosing that priority.

W2: detect a gap only when the next valid observation arrives; integrate the old command over the elapsed gap, then issue the selected response at that current time for future actuation. It cannot retrospectively close through the gap. With no later observation, it supplies no independent timeout event. A “freeze unknown time” model would be a different declared model, not silent physical propagation. Neither W1 nor W2 is selected by C2;2s fixture timeout is not an adopted safety policy. Existing source-staleness/default warning logic is not a new watchdog implementation (`configs/frozen_experiment_v1.yaml:55-61`; `src/railway_detection/fusion/decision_engine.py:391-430`).

<a id="s8"></a>

## S8. PROPOSED acceptance tiers and current outcome

| Evidence tier | C2 scope / status | What may be concluded |
|---|---|---|
| Mathematical proof / document oracle arithmetic | VERIFIED conditional derivation and safe text-only arithmetic checks in the acceptance audit | Only stated mathematical/contract consistency; no implementation acceptance. |
| Synthetic unit tests | PROPOSED TC-SIM fixtures; NOT EXECUTED | Future isolated actuator/time/adapter verification after T02/T04/X00. |
| Synthetic integration tests | PROPOSED combinations of controller stub, merged timer grid, logs and cutoff; NOT EXECUTED | Must verify applied/issued distinction, no look-ahead, reset, rejection and selected W1/W2 contract using synthetic inputs only. Actual controller integration remains unverified. |
| Production implementation tests | OUT OF SCOPE; no acceptance plan executed or specified here | No production acceptance claim. |
| Real-data evaluation | NOT AUTHORIZED (X04); no run or execution plan here | No new results, Table11 replacement or physical validation. |

T02/R04 must choose the actual numeric/input/horizon/watchdog/reporting policy; T04 must accept test coverage and later results; X00 must authorize any implementation. F11–F16/F23 are not closed by a corrected oracle table. F19 screen/censor reporting remains R04: MTR is an outcome with a separate lead-in screen;3.6s is not an approved physical threshold,2 ticks are not 2s, and candidate20/23 is not promoted GT (`src/railway_detection/evaluation/lead_in_screen.py:15-27`; `docs/generated/master_reaudit/MISSION_17C1_INDEPENDENT_CHALLENGE_OF_17C0.md:870-874`). STOP at researcher review.
