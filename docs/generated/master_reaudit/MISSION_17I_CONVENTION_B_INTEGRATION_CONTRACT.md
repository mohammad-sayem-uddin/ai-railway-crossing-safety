# Mission 17I — Convention B integration contract

Date: 2026-11-04, America/New_York. Contract ID **17I-CB-V1**. Baseline `17cc6273544618f0b402a027b41eb527845d3252`; implementation references below describe the 17I revision. This freezes an engineering handoff for review, not a research protocol or operational safety policy. No production integration was executed. **Verified** denotes inspected implementation or passing synthetic cases; **Required** denotes future acceptance work; **Decision pending** denotes researcher selection. The same assistant prepared 17G/17H/17I; no independent human approval is claimed.

Companions: [remediation and caller trust](MISSION_17I_FINAL_ENGINEERING_REMEDIATION_REPORT.md), [CV contract](MISSION_17I_GROUPED_CV_INTEGRATION_CONTRACT.md), [18 acceptance register](MISSION_17I_MISSION18_ACCEPTANCE_AND_DEPENDENCY_REGISTER.md). Earlier [17F controller plan](MISSION_17F_CONVENTION_B_CONTROLLER_INTEGRATION_PLAN.md) remains historical proposed work.

## 1. Boundary and required inputs

**CB01 — synthetic command boundary.** `CausalRunner` accepts already-decided commands. It has no controller callback, media loader, file writer or incremental public actuator API. Required future integration must own a separately selected coordinator and retain frame-to-decision-to-command correspondence. A command fixture proves actuator behavior only. Keep the private reporting helper internal; arbitrary overlapping/gapped interval records are outside its preconditions.

| Parameter / field | Required representation and units | Current validation / origin and ownership |
|---|---|---|
| `CausalRunner(initial_angle=90)` | Exact integer, decimal string, or Fraction; degrees in [0,90] | Normalized to Fraction; caller selects synthetic starting state, no measured state inferred. |
| `closing_seconds=3`, `opening_seconds=3` | Positive exact integer/decimal/Fraction seconds | Rates 90/duration degrees per second. No binary-float acceptance or legacy minimum-duration clamp. |
| `watchdog=None` | Explicit Watchdog or None | None becomes normalized NONE snapshot. Timeout/response restrictions below. |
| `events` | In-memory list/tuple of exact SyntheticEvent records | Indexed copy retains event references; cooperative frozen objects, not tamper-proof. Retain original ordered input independently. |
| `SyntheticEvent.event_id` / `fixture_id` | String matching `synthetic:[A-Za-z0-9][A-Za-z0-9._:-]*` | IDs identify constructed examples only. They authenticate no source. Accepted event identity cannot recur at a later instant. |
| `SyntheticEvent.timestamp` | Exact nonnegative int = microseconds; unsigned plain decimal string = seconds exactly on µs grid | None, bool, floats, negative, scientific notation, extra sub-µs precision reject. No epsilon or rounding. |
| `target` / optional `nested_command` | Command enum or recognized string | H/HOLD→HOLD; L/LOWER/CLOSED/CLOSING→LOWER; R/RAISE/OPEN/OPENING→RAISE. Nested value must normalize identically. These are intentions, not measured physical states. |
| `mode='ARRIVAL'` | ARRIVAL or OFFLINE | Must be deliberately selected; ordering and lookahead differ. |
| `cutoff=None` | Same time grammar, normalized integer µs | Optional absolute horizon; never infer resource duration. |
| `report_times=None` | Contract requires tuple of time values or None | Normalized tuple, nonempty and strictly increasing when supplied. Runtime iterates supplied values and does not enforce the outer argument's tuple type; the future adapter must enforce this contract before consuming it. |
| `expected_configuration` | Separately retained exact RunConfiguration | Required for `verify_run_configuration`; never derive an expectation from a candidate result at its acceptance boundary. |

Source: `src/railway_detection/synthetic/convention_b.py:84-88` (`SyntheticEvent`); `src/railway_detection/synthetic/convention_b.py:36-44` (`timestamp_us`); `src/railway_detection/synthetic/convention_b.py:47-55` (`legacy_float_to_us`); `src/railway_detection/synthetic/convention_b.py:314-488` (`CausalRunner`).

**CB02 — exact clock ownership.** Legacy float conversion is explicit: finite nonnegative float → shortest-round-trip decimal → exact-grid validator. 0.2 is accepted; `0.1+0.2` and `3*0.2` reject. Required adapter retains original lexical/tick/float representation and chosen conversion profile alongside normalized µs. Clock accuracy, synchronization and camera relationships are caller/researcher evidence, not established by exact arithmetic. No silent rounding or cross-camera synchronization is permitted.

## 2. Causal order, rejection and horizon

**CB03 — issue versus application.** At accepted origin t0 the configured angle is unchanged; issue u0 at t0 with effective time t0. For each next accepted boundary ti, integrate the previously active command over [t(i−1),ti], record its origin/effective time and resulting angle, then issue ui. Zero configured command latency means ui affects only future positive intervals. No pre-origin integration. A requested CLOSED command never means instant physical closure. A terminal command may be logged without contributing duration.

**CB04 — mode and failure contract.** ARRIVAL consumes in supplied order. A structurally valid ID/time with t≤last accepted sensor time produces DUPLICATE or OUT_OF_ORDER rejection and does not advance clocks, replace the command, rearm timers or enter accepted IDs. This ordering check precedes target validation, so even an invalid target on an otherwise recognized older/duplicate event is discarded as a rejection. Invalid time or identity is INCOMPLETE. Reused accepted ID at a new later instant is INCOMPLETE. OFFLINE prevalidates every input's type/time/ID/command before actuation, then stable-sorts by (time,input index); duplicate times retain input-order priority. Future invalid inputs can therefore invalidate an OFFLINE run even past cutoff. `reordered` records actual index order changes.

| Input situation | Current outcome and required downstream handling |
|---|---|
| Empty events, no fixed grid | EMPTY, no origin/horizon/physical angles, zero endpoint/continuous/report totals; retain actual config. |
| Empty events with fixed grid | ValueError: cannot span a fixed grid; no completed receipt. |
| Singleton | COMPLETE, origin=horizon, unchanged angle, zero durations; fixed singleton matching origin is valid. |
| Bad event during ARRIVAL | INCOMPLETE with reason and accepted prefix only; report total None. Prefix event/continuous totals are diagnostic, not a complete-run metric. |
| Bad event during OFFLINE prevalidation | INCOMPLETE before any interval/origin. |
| Cutoff before accepted origin | ValueError. Cutoff at origin logs that event, no interval. |
| Interior cutoff | Advance existing command/timer to cutoff; no future sensor issue. In ARRIVAL, timestamp of the next input is parsed before the cutoff branch; its ID/target need not be checked once t>cutoff. |
| Cutoff at a sensor | Process and log that accepted sensor; stop at same boundary. |
| Cutoff beyond final sensor | Extend existing command and selected scheduled timer to cutoff; never fabricate a sensor. |
| Bad configuration, unknown mode, malformed/nonincreasing grid | ValueError before producing a certified result. |
| Fixed grid partly overlapping/disjoint horizon, missing either endpoint | ValueError on COMPLETE; first/last must exactly equal accepted origin/horizon. Interior report endpoints need not coincide with sensor keys. |

Required adapters preserve explicit EMPTY/COMPLETE/INCOMPLETE/exception distinctions and never promote a prefix into success. Unsupported object shapes may raise ordinary Python errors outside the documented typed interface; there is no hostile JSON decoding API.

## 3. Estimators and configuration

**CB05 — distinct metrics.** Let di=(ti−t(i−1))/1,000,000, qi be the end angle, and b(q)=1 iff q≤45 exactly. Event endpoint duration is `Σ di*b(qi)` over emitted sensor/timer/cutoff intervals. The continuous estimator integrates b(q(t)) under the declared clipped linear dynamics. LOWER from q>45 contributes max(0,d−(q−45)/vdown), otherwise d; RAISE from q≤45 contributes min(d,max(0,(45−q)/vup)), otherwise 0; HOLD contributes d*b(q). Clip angles to [0,90]. A single equality instant has zero continuous measure; HOLD at45 contributes all its duration. No epsilon broadens θ≤45°.

Fixed-report estimator uses each report interval's duration and exact trajectory angle at its right endpoint. It never introduces a sensor, decision or issue. Default reporting reuses event endpoint total. No-op subdivision may change event endpoint duration; continuous and the same fixed-grid estimator remain invariant. These are model durations, not measured train occupancy. A/B comparison has no universal one-tick correction on irregular/partial/different-command paths. Source: `src/railway_detection/synthetic/convention_b.py:277-288` (`_motion`); `src/railway_detection/synthetic/convention_b.py:291-311` (`_report_endpoint_seconds`).

**CB06 — effective configuration.** Every status stores the same RunConfiguration snapshot consumed by the run: exact initial/closing/opening values; normalized watchdog; mode; cutoff_us; report_times_us; profile `SYNTHETIC_CONVENTION_B_V1`; schema `SYNTHETIC_RUN_CONFIGURATION_V1`; timestamp_policy `INTEGER_US_OR_EXACT_GRID_DECIMAL_SECONDS_V1`; dynamics `CLIPPED_LINEAR_0_90_STRICT_BLOCKED_LE_45_V1`; command_latency_us=0; watchdog_priority `SENSOR_FIRST_ONE_SHOT_V1`. Unsupported identifiers/latency reject. Constructor defaults must be explicitly recorded as effective defaults. A later runner reconfiguration cannot alter the local active snapshot. Frozen objects do not protect against hostile same-process mutation. Source: `src/railway_detection/synthetic/convention_b.py:124-180` (`RunConfiguration`).

**CB07 — non-adopted watchdog profiles.** NONE has no timeout or response. SCHEDULED and DETECT_ON_ARRIVAL require positive exact integer timeout_us and normalized response. SCHEDULED triggers once per accepted-sensor generation at last_sensor+timeout, splitting the trajectory; a valid sensor at equality wins and rearms, while cutoff at equality permits the timer. Rejected sensors do not rearm. DETECT_ON_ARRIVAL acts only on a later accepted sensor with strictly greater gap than timeout; prior motion retains old command, requested intent stays logged, selected response replaces only future command. No later sensor means no detect action, even at extended cutoff. No timer evaluates a controller or proves safety. Researcher adoption is **pending**; future policy-preservation experiments should explicitly select NONE unless separately authorized.

## 4. Output schema and provenance

**CB08 — typed output.** RunResult fields are frozen dataclass fields, not a versioned hostile-input JSON decoder. Exact canonical serialization emits fractions as `{numerator,denominator}`, enum values as strings, tuples as arrays, sorted keys, compact separators and no NaN.

| Fields | Meaning / expected shape |
|---|---|
| profile, fixture_id, status, reason, mode, reordered | Profile/constructed identity; status above; reason optional; actual mode and reorder flag. |
| origin_us, horizon_us, initial_angle, final_angle | int µs and Fraction degrees or None for uninitialized physical state. |
| intervals | Tuple of Interval(start_us,end_us,applied_command,effective_us,origin_event_id,pre_angle,post_angle,blocked,continuous_seconds,end_kind); chronological positive-length contiguous producer intervals. |
| issues | Tuple of CommandIssue(timestamp_us,event_id,command,requested_command,kind,mapping_provenance); chronological issue log, including timer and gap distinctions. |
| rejections | Tuple of Rejection(input_index,event_id,timestamp_us,reason), preserving processing order; index refers to original input even in OFFLINE. |
| accepted_event_ids | Ordered accepted synthetic sensor IDs; timers are separate issues. |
| event_grid_us, report_grid_us, report_grid_kind | Stored tuples, with EVENT_GRID or FIXED_GRID explicitly distinguished. |
| endpoint_seconds, continuous_seconds, report_endpoint_seconds | Fractions; report endpoint None on INCOMPLETE. |
| configuration, configuration_digest | Exact effective RunConfiguration and unkeyed SHA256 of canonical config. |

Source: `src/railway_detection/synthetic/convention_b.py:216-243` (`RunResult`); `src/railway_detection/synthetic/convention_b.py:184-194` (`Interval`); `src/railway_detection/synthetic/convention_b.py:198-204` (`CommandIssue`); `src/railway_detection/synthetic/convention_b.py:208-212` (`Rejection`).

**CB09 — acceptance of results.** `verify_run_configuration` checks typed expected/current settings, config digest, profile/mode/initial angle/report binding. It does **not** recompute trajectory, validate every result field, authenticate execution or bind event inputs/source code. `canonical_json` uses the result's own settings and is weaker than independent expected-settings acceptance. Required future adapter must retain ordered input + selected configuration + producing code identity + fixture/run identity independently, obtain output from the controlled producer, and compare full deterministic output/recomputed trajectory or independent numerical oracle before accepting detached results. A forged angle/duration with unchanged config can pass config-only verification. A coherently replaced expectation and candidate can also agree. These limitations are acceptable only for trusted synthetic fixtures with that external ownership; no detached result is an authority. Source: `src/railway_detection/synthetic/convention_b.py:246-274` (`verify_run_configuration`).

## 5. Scale, compatibility and future gates

**CB10 — complexity.** N input events, S emitted intervals, R report intervals. Fixed merge: O(S+R) arithmetic work and O(1) auxiliary objects; no report slice or sort. Default total reuse adds no lookups. Whole producer: O(N+S+R) stored/temporary objects, including indexed inputs, accepted/rejected/issue logs, intervals, grids, normalized fixed input and canonical configuration copies/JSON. OFFLINE adds O(N log N) sorting and O(N) sort storage; ARRIVAL does not sort. Exact rational operation cost and memory grow with operand bit lengths. The helper is not a bounded-memory whole-run streamer. Finite measurements and no-slice regression support the implementation; callers must bound workload deliberately.

**CB11 — compatibility risks, verified by source only.** Existing `EventSimulationRunner._run_frames` evaluates the current frame then applies its newly selected target to preceding dt (`src/railway_detection/simulation/runner.py:165-245`). It uses floats, sorts by default, resets state, and retains distinct rejected-step/fault metrics. `PhysicalGateModel` clamps durations to≥0.1s and uses 0.05/89.95/89.9 physical-state tolerances (`src/railway_detection/simulation/gate_model.py:19-78`). A B adapter is not a drop-in replacement. Preserve historical A routing/results; select explicit exact-time, logical/physical-state, reset, rejection, failure and metric mappings. No production module was imported or executed here.

**CB12 — future acceptance, not implemented.** Required 18A tests include controller call-count/order parity on constructed frames, separate actuator oracle, clock migration and invalid/rejected frames, cutoff/partial/empty behavior, all selected timer boundaries, fresh-run reset, config/input/output substitution, deterministic serialization, strict threshold/no-op invariants, large-grid work/storage checks and zero protected IO. Existing actuator evidence: `test_all_21_exact_reference_vectors`, `test_independent_geometric_oracle_200_trajectories`, `test_fixed_command_boundary_identity_and_limits`, `test_fixed_grid_merge_matches_separate_slow_geometric_lookup`, and all `test_17i_*` reporting tests. They do not satisfy controller integration acceptance. See the register for prerequisite status and researcher decisions. **Stop for review; Mission 18 not started.**
