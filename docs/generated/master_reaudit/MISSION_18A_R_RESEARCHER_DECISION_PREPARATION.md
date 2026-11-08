# Mission 18A-R — Researcher Decision Preparation

Prepared: 2026-11-04, America/New_York. Repository baseline: `46ed0d6999cb04ce7be6d48bc2b3476641f86b94`, branch `main`.

**Current status: all 14 Option A choices are SUBMITTED; decision-maker identity and project authority are UNVERIFIED. Formal adoption is NOT ESTABLISHED.** The user explicitly supplied the selection in Mission 18A-R2. This packet retains the original alternatives and recommendations; the updated choice column records the submission, not verified researcher approval. [Exact user statement and adoption status](MISSION_18A_R2_RESEARCHER_SELECTION_AND_ADOPTION_RECORD.md). Mission 18A remains BLOCKED, and this documentation task authorizes no implementation.

This packet concerns a bounded synthetic engineering experiment. It does not seek adoption of Convention B for official research results, operational safety, real media, training, CV integration or deployment. Those separate decisions remain outside this task. The proposed API names and new file paths below do not exist yet.

Sources: [18A blocker report](MISSION_18A_CONVENTION_B_SYNTHETIC_INTEGRATION_REPORT.md), [18A acceptance record](MISSION_18A_INTEGRATION_ACCEPTANCE_RECORD.md), [17I-CB-V1 contract](MISSION_17I_CONVENTION_B_INTEGRATION_CONTRACT.md), and [17I dependency register](MISSION_17I_MISSION18_ACCEPTANCE_AND_DEPENDENCY_REGISTER.md). The recommendations use inspected repository source; no integration implementation or tests were executed during this preparation.

## Quick decision sheet

The user submitted option A for every row in Mission 18A-R2. `A — SUBMITTED; AUTHORITY UNVERIFIED` records that choice without treating it as adopted permission. The original two-to-three options and recommendations below remain unchanged.

| ID | Decision | Recommendation | Your choice |
|---|---|---|---|
| R01 | Integration entrypoint | A — explicit B method on the existing runner | A — SUBMITTED; AUTHORITY UNVERIFIED |
| R02 | Permitted file changes | A — bounded runner/adapter/helper/test scope | A — SUBMITTED; AUTHORITY UNVERIFIED |
| R03 | Timestamp source and conversion | A — exact synthetic clock plus checked frame time | A — SUBMITTED; AUTHORITY UNVERIFIED |
| R04 | Arrival versus offline processing | A — ARRIVAL primary; explicit OFFLINE support | A — SUBMITTED; AUTHORITY UNVERIFIED |
| R05 | Command issue/application semantics | A — current zero-latency Convention B contract | A — SUBMITTED; AUTHORITY UNVERIFIED |
| R06 | Initial state and actuator dynamics | A — 90°, 3s closing, 3s opening baseline | A — SUBMITTED; AUTHORITY UNVERIFIED |
| R07 | Duration estimators and report grid | A — separately report event, continuous and fixed-grid durations | A — SUBMITTED; AUTHORITY UNVERIFIED |
| R08 | Watchdog selection | A — NONE for integrated baseline | A — SUBMITTED; AUTHORITY UNVERIFIED |
| R09 | Horizon and failure handling | A — last accepted input by default; explicit cutoff and diagnostic prefixes | A — SUBMITTED; AUTHORITY UNVERIFIED |
| R10 | Compatibility and result schema | A — preserve A; return a separate B result | A — SUBMITTED; AUTHORITY UNVERIFIED |
| R11 | Controller calls and rejected frames | A — current engine with constructed evidence and native rejection records | A — SUBMITTED; AUTHORITY UNVERIFIED |
| R12 | Configuration and result provenance | A — snapshot inputs/settings and verify the full detached result | A — SUBMITTED; AUTHORITY UNVERIFIED |
| R13 | Fixtures, acceptance and workload | A — full contract coverage within explicit synthetic test bounds | A — SUBMITTED; AUTHORITY UNVERIFIED |
| R14 | Mypy environment disposition | A — permit limited synthetic engineering with type analysis explicitly unresolved | A — SUBMITTED; AUTHORITY UNVERIFIED |

## R01 — Which simulation entrypoint should be integrated?

Resolves AG01 and register A01. Existing `EventSimulationRunner.run_frames` is in `src/railway_detection/simulation/runner.py`; `CausalRunner.run` in `src/railway_detection/synthetic/convention_b.py` consumes already-decided commands.

| Option | What you would choose | Trade-off |
|---|---|---|
| A | Add an explicitly selected `EventSimulationRunner.run_frames_convention_b(...)` method, delegating to a synthetic coordinator that reuses `CausalRunner`. Keep existing `run_frames(...)` as A. | Directly addresses the existing-runner integration objective while preserving its historical entrypoint. Requires a small change to the shared runner source. |
| B | Implement a separate `SyntheticConventionBPipeline.run(...)` in the synthetic package, using the current decision engine and causal helper; leave the shared runner untouched. | Stronger source separation, but it is a narrower standalone pipeline milestone. It would not complete the original request to expose B through the existing runner. |
| C | Defer integration and retain only the existing command helper. | No new execution path; 18A remains blocked. |

**Recommendation: A.** It makes the requested existing-runner integration concrete through an explicit method. No default switch, CLI route, real-data loader or production deployment is included. The method must require a constructed fixture envelope and reject ordinary unqualified inputs; a `synthetic:` prefix alone is not evidence of synthetic origin.

## R02 — Exactly which files may be changed?

Resolves AG02 and E01. The list is a proposed maximum scope, not permission already granted.

| Option | What you would choose | Trade-off |
|---|---|---|
| A | Permit the exact bounded implementation/test/report paths listed below. Existing runner changes are allowed only for R01-A; causal-helper changes only when necessary to reuse its timing implementation. | Sufficient room to complete and test the proposed integration without a broad refactor. |
| B | Permit only a new standalone synthetic coordinator, its new test directory and the two 18A reports; keep all existing source files unchanged. | Smaller change surface; requires R01-B and its narrower milestone description. |

**Recommendation: A.** Proposed permitted paths:

- `src/railway_detection/simulation/runner.py` — explicit B entrypoint/delegation only.
- `src/railway_detection/synthetic/convention_b.py` — minimal reusable actuator support only if needed; retain exact existing behavior and schemas unless a separately reviewed compatible extension is necessary.
- `src/railway_detection/synthetic/convention_b_pipeline.py` — new coordinator, input/result envelopes and verification support.
- `tests/synthetic_mission18a/conftest.py` — separate isolation harness; exclude the root conftest.
- `tests/synthetic_mission18a/test_convention_b_integration.py` — execution-path and compatibility cases.
- `tests/synthetic_mission18a/test_isolation.py` — guards and constructed-input boundary checks.
- `docs/generated/master_reaudit/MISSION_18A_CONVENTION_B_SYNTHETIC_INTEGRATION_REPORT.md` — replace the blocker disposition only when supported by actual evidence, preserving its starting-state history.
- `docs/generated/master_reaudit/MISSION_18A_INTEGRATION_ACCEPTANCE_RECORD.md` — update criteria from actual acceptance evidence.

The current decision engine, gate model, policy/configuration files, existing 238-test suite and governance records are outside this proposed edit list. If implementation needs another file, report the concrete reason before expanding scope. This packet's own creation is the present documentation task; it is not part of an already authorized integration commit.

## R03 — Which timestamp representation should govern the integration?

Resolves AG03/A02/CB02. Existing `MultimodalFrame.master_timestamp_s` and the controller use floats; the actuator accepts exact integer microseconds or decimal seconds on the microsecond grid.

| Option | What you would choose | Trade-off |
|---|---|---|
| A | Construct a synthetic input envelope containing the exact original timestamp and the frame. Normalize the exact timestamp once; construct/check the frame's float time from that same normalized value. Retain both representations. | Exact actuator clock and explicit float-controller boundary; fixtures must carry an additional clock field. |
| B | Accept existing constructed float frames through the current strict `legacy_float_to_us` conversion, retaining the original float representation. | Less fixture restructuring, but common accumulated float values such as `3*0.2` reject rather than round. |
| C | Defer clock migration until a separately specified conversion policy is supplied. | No silent precision choice; integration waits. |

**Recommendation: A.** Integer values mean microseconds; decimal strings mean seconds. Reject None, bool, negative/off-grid times and inconsistent exact/frame pairs. Fixture builders must derive evidence timestamps consistently from their declared synthetic clock; never silently retime evidence or alter its ages. Preserve the existing controller's float arithmetic and policy constants, documenting that exact actuator time does not make controller dwell arithmetic exact or establish physical clock accuracy.

## R04 — How should input ordering be handled?

Resolves AG03/A02/CB04.

| Option | What you would choose | Trade-off |
|---|---|---|
| A | Require the caller to name ARRIVAL or OFFLINE. Use ARRIVAL as the primary experiment; provide explicitly selected OFFLINE with the contract's stable sorting and prevalidation. | Covers both existing contract modes; requires testing their different lookahead/failure behavior. |
| B | Support ARRIVAL only in the first integration milestone; reject requests for OFFLINE in the new entrypoint. | Smaller adapter surface; integrated OFFLINE acceptance remains deferred and must be reported as such. |

**Recommendation: A.** ARRIVAL preserves delivery order. OFFLINE prevalidates the declared batch before controller execution and stable-sorts by exact time and original index. Neither mode is silently selected from an input file or inferred from an existing runner default. Duplicate and older frames must not change the accepted actuator clock or active command. R11 determines how their native controller rejection records are retained.

## R05 — When does a newly issued command act?

Resolves AG03/A01/CB03. This is adoption or deferral of the existing contract, not a choice between equally valid implementations of B.

| Option | What you would choose | Trade-off |
|---|---|---|
| A | Adopt the existing zero-latency B semantics: advance the old command to the new boundary, then issue the new command effective at that boundary for future positive intervals. | Matches `17I-CB-V1`; preserves exact issue/effective/interval provenance. |
| B | Defer integrated B until the researcher requests a different latency contract. | Any nonzero latency/queue/supersession design requires a separate contract revision and acceptance scope. |

**Recommendation: A.** Reuse the existing actuator implementation. Do not reproduce its propagation or timer rules in the runner. No pre-origin motion, retroactive command application or invented processing latency is allowed. A command issued at the terminal boundary may have no subsequent movement interval.

## R06 — What actuator settings should define the baseline?

Resolves AG03/A04/CB05–CB06. The strict blocked predicate remains exactly theta≤45° in every option that proceeds under the current contract.

| Option | What you would choose | Trade-off |
|---|---|---|
| A | Baseline initial angle 90°, closing 3s and opening 3s, with explicit configuration and separate boundary/asymmetric-rate test fixtures. | Matches current nominal settings and makes baseline A/B comparisons easier to interpret. |
| B | Select an explicitly experimental baseline, for example initial90°, closing 3s and opening 6s, and record the controller-versus-actuator configuration relationship. | Useful for asymmetric dynamics, but intentionally changes the baseline experiment and its expected outputs; no historical parity claim follows. |

**Recommendation: A.** Record actual exact values, not an assumed default reconstructed after the run. Additional 0°,45°±delta,45°,90° and asymmetric-rate cases are labeled tests of the configured model. They do not alter the existing controller's constants or establish an adopted operational policy. Both options retain clipping to [0,90] and reject invalid durations without importing the legacy minimum-duration clamp.

## R07 — Which duration estimates should be reported?

Resolves AG03/R04/A04/CB05. “Primary” below means the main synthetic comparison column, not selection of a scientific publication metric.

| Option | What you would choose | Trade-off |
|---|---|---|
| A | Report all three separately: event-grid endpoint duration as the main A/B comparison column, exact continuous duration as a separate model integral, and an optional fixed-report-grid endpoint duration. | Preserves comparison with the historical estimator while showing grid effects explicitly. Event-grid A/B numerical equality is not expected. |
| B | Report the same three estimates but make continuous duration the main synthetic comparison column; retain both endpoint columns with clear labels. | Highlights within-interval model blockage and reduces dependence on observation segmentation; differs from the historical main-column convention. |

**Recommendation: A.** Proposed optional fixed grid: 200000µs steps from accepted origin, append the exact horizon once if it is a partial final step. Empty runs have no fixed grid; singleton runs use their one-point grid. Also test arbitrary valid grids. Reuse the event total when no fixed grid is requested. Never overwrite legacy `closed_duration_s` with a different estimator or apply a universal one-tick correction. All durations remain model estimates; no train-occupancy claim is created.

## R08 — Which watchdog should the integrated baseline use?

Resolves AG03/A05/CB07.

| Option | What you would choose | Trade-off |
|---|---|---|
| A | NONE for the integrated baseline. Retain existing controller fault/recovery rules on actual constructed frames. | Isolates the timing integration from new timer-driven decisions. Existing helper watchdog tests remain valid evidence about that helper only. |
| B | SCHEDULED with explicitly selected timeout 2000000µs and response LOWER for a synthetic experiment. | Inserts one-shot timer boundaries between frames; requires timer priority/generation/cutoff tests and intentionally different outputs. |
| C | DETECT_ON_ARRIVAL with explicitly selected timeout 2000000µs and response LOWER for a synthetic experiment. | Changes only the future command when the next accepted frame reveals an excessive gap; cannot respond when no later frame arrives. |

**Recommendation: A.** Options B/C are proposed experimental values, not empirically justified safety limits. Selecting either authorizes only the named synthetic profile and requires its full contract tests; it does not adopt a research or operational fail-safe policy. Do not implement a second watchdog in the coordinator.

## R09 — Where should a run end, and how should failures appear?

Resolves AG03/A03/CB04.

| Option | What you would choose | Trade-off |
|---|---|---|
| A | Default to the last accepted input, with an optional explicit exact cutoff for origin/interior/extended horizons. Retain incomplete accepted prefixes as clearly labeled diagnostics. | Uses the existing contract and supports all requested trajectory boundaries. |
| B | Require an explicit cutoff for every run, using the same prefix and failure rules. | More explicit experiment setup; fixtures must declare a horizon even when it equals their last accepted input. |

**Recommendation: A.** Empty/singleton behavior and cutoff-before-origin errors follow CB04. Controller or command failures must produce a labeled incomplete envelope/prefix or the specified validation exception, never a completed result. Fixed-grid totals on incomplete trajectories remain uncertified/None. No controller evaluation is invented at cutoff. No default media duration is inferred. A partial prefix cannot enter the successful-run aggregate as though it completed.

## R10 — What compatibility and output schema should be promised?

Resolves AG04/A04/A06/CB08/CB11.

| Option | What you would choose | Trade-off |
|---|---|---|
| A | Preserve existing A entrypoint/results; return a separately named B result containing the causal result, decision/rejection correspondence and provenance envelope. Expose logical target, applied command, exact angle and blocked flag separately. | Clear estimator/state meaning; B callers adopt an explicit new result type. |
| B | Provide a legacy-shaped B compatibility view in addition to the full causal result, with explicitly documented field, estimator and physical-state tolerance mappings. | Easier migration for old consumers; adds semantic translation work and more acceptance tests. |

**Recommendation: A.** Do not force exact actuator state into legacy OPEN/CLOSED tolerance labels. Report the command and angle directly. A requested CLOSED target is not instant physical closure. Existing A defaults, gate model and historical results stay intact. Every intentional B angle/duration difference must be derived from the selected timing/configuration and tested. Common controller decision sequences are compared only under matching input/configuration/reset assumptions.

## R11 — Which controller and rejection behavior should be exercised?

Resolves AG04/A01/A02/CB01/CB11.

| Option | What you would choose | Trade-off |
|---|---|---|
| A | Exercise the existing `MultimodalDecisionEngine` on constructed `MultimodalFrame`/`EvidenceRecord` objects; use scripted decision fixtures additionally for boundary/error injection. | Covers the actual decision-to-command-to-actuator path and permits focused numerical oracles. |
| B | Use a scripted decision provider only in this milestone. | Simpler isolated experiment, but leaves actual controller integration untested and cannot justify full original 18A acceptance. |

**Recommendation: A.** Keep existing decision policy and thresholds. Evaluate each eligible supplied frame once in the producing run, including well-formed duplicate/older frames so native rejection decisions can be logged. Rejected decisions issue no new actuator command and advance no accepted clock. Validate malformed/missing time before invoking the engine. For OFFLINE, prevalidate and sort first. Stop before evaluating frames beyond the selected cutoff. Reset state for each independent run.

The controller currently receives no physical angle, so a batch coordinator may collect the command ledger then call `CausalRunner.run` without duplicating actuator logic, provided call order, failure-prefix handling and all correspondence are tested. This is a proposed design choice, not an executed equivalence result. Adding physical feedback later requires a new contract. A separate verification replay has its own call-count receipt and must not be confused with duplicate calls in the producing run.

## R12 — How should configuration and detached results be verified?

Resolves AG05/E02/A06/CB06/CB09.

| Option | What you would choose | Trade-off |
|---|---|---|
| A | Retain a deep canonical snapshot of constructed inputs, selected actuator/controller settings, mode/grid/horizon, fixture identity and producing code version; verify a detached candidate by full deterministic replay against independently retained expectations, with independent numerical test oracles. | Supports substitution tests and reproducibility; verification adds work and shares possible implementation bugs with replay. |
| B | Limit acceptance to results produced directly in the trusted test process, retaining snapshots and independent test oracles; reject detached candidate acceptance as unsupported. | Smaller verification surface, but the planned detached-result acceptance capability remains deferred and must be excluded from completion claims. |

**Recommendation: A.** Snapshot actual settings used, including the controller's effective fields; reject contradictions with an expected record. Copy mutable nested input/config dictionaries before execution and preserve canonical bytes so later caller mutation cannot rewrite history. Reset/use a fresh controller for replay. Test altered angles, durations, inputs, settings and producer version. Configuration-only verification is insufficient. Hashes establish consistency of declared synthetic content, not authentic researcher authority or protection from hostile same-process mutation. No general trajectory authenticity or security certification is claimed.

## R13 — Which fixture scope, acceptance tests and workload should be permitted?

Resolves AG05/T04/E01/E04/A07/CB10/CB12.

| Option | What you would choose | Trade-off |
|---|---|---|
| A | New isolated constructed integration suite covering CB01–CB12 and A01–A07, plus the existing 238-case suite in its own fresh process. Proposed scale envelope:≤8192 supplied frames,≤8192 emitted intervals,≤32768 report intervals and an absolute exact clock from0 to3600000000µs. | Covers the complete recommended scope and meaningful finite scaling, with extra test effort. |
| B | Use the same acceptance coverage with a smaller integration envelope:≤2048 frames/intervals and≤8192 report intervals, on the same one-hour clock range. | Faster initial acceptance; larger integrated workloads remain unvalidated. |

**Recommendation: A.** These are proposed engineering test and supported integration limits, not measured capacity, scientific sample sizes or hard real-time guarantees. They do not add limits to the existing helper. The selected adapter must report an unsupported workload explicitly; never truncate, drop records or weaken checks to fit a limit. If R08 selects timers, count their intervals against the same limit and test limit failures.

Use only constructed in-memory evidence, exact microsecond/decimal clocks and safe synthetic metadata. Add positive controls, invalid-time/command/config cases, all horizon boundaries, strict 45° checks, actual controller transitions, rejection/call-count/reset checks, config-mutation and detached-result substitution checks, A compatibility, deterministic outputs and operation/storage scaling. Retain independent exact numerical oracles. Rational operand sizes and metadata also affect work; the count envelope is not an adversarial CPU/memory guarantee.

Run the original 238 tests and new 18A tests in separate processes: the original isolation tests deliberately assert that the existing simulation runner is not imported, while the new integration suite intentionally exercises it. Preserve that assertion and guard. New guards must deny file/network/process resource operations during component execution, and an independent source check must audit imports before collection. Test runner imports and temporary pytest receipts are distinct from component execution; no OS sandbox claim follows. Existing unit-test files are candidates for source review, not a blanket authorization to run root/legacy suites or access their resources.

Acceptance requires actual evidence, not a promised test count:238 existing cases must reproduce, every selected requirement must be covered and pass, and the new unique collection count must be reported without adding overlapping totals. No assertion removal or protected-data fixture is allowed. If selected scope cannot meet a required gate, report PARTIAL/BLOCKED.

## R14 — What should happen about the incomplete Mypy installation?

Resolves E03. Historical 17I evidence records `ModuleNotFoundError: No module named 'mypy.bogus_type'` before analysis and zero scoped Ruff diagnostics. Neither check was rerun for this documentation task.

| Option | What you would choose | Trade-off |
|---|---|---|
| A | Explicitly permit this bounded synthetic integration stage to proceed with Mypy unavailable, requiring fresh Ruff/runtime/syntax checks and accurate disclosure of the unresolved type-analysis gate. Do not change dependencies. | Allows reversible engineering to proceed; supplies no Mypy/type-correctness acceptance or release readiness. |
| B | Keep implementation paused until a separately authorized environment repair restores Mypy and type analysis actually runs. | Stronger static-analysis prerequisite; requires another scoped environment task before integration. |

**Recommendation: A for this synthetic-only stage.** The existing passing runtime evidence and lint tooling justify preparing and testing a reversible adapter while the type-analysis limitation remains explicit. This is a recommendation for a researcher-recorded limited-stage disposition, not a waiver already issued. Require B or another explicit resolution before any later stage whose acceptance requires a completed type check. No installation, upgrade, global rule change or suppression is authorized by preparing or selecting A.

## Coverage of the blockers

| Existing blocker / dependency | Decisions that resolve its relevant scope |
|---|---|
| AG01 named path and bounded adoption | R01, R05 |
| AG02 exact permitted changes | R02, consistent with R01 |
| AG03 time/dynamics/estimators/watchdog/horizon | R03–R09 |
| AG04 historical compatibility and controller behavior | R10–R11, supported by R04–R09 |
| AG05 fixtures, expectation ownership, acceptance and scale | R12–R13 and the selected scope above |
| E01 isolation | R02, R13 |
| E02 independently retained expectations | R03, R12 |
| E03 static-analysis disposition | R14 |
| E04 workload envelope | R13 |

Consistency rules: R01-A requires R02-A. R01-B/R02-B is a narrower standalone milestone and cannot silently replace the original existing-runner objective. R01-C, R03-C or R05-B defers integration. R04-B, R10-B, R11-B or R12-B needs an explicit acceptance-scope interpretation; a deferred original criterion cannot be marked PASS. R08-B/C requires its additional timer cases. Any departure from the fixed `17I-CB-V1` semantics needs a visible contract amendment before implementation; none is prepared or adopted here.

## Researcher response and adoption record

You can reply with the option letters, for example `R01=A, R02=A, ... R14=A`, or say that you select all 14 recommendations. That records your requested choices for review; it does not invent your identity or authority. If you want implementation to resume as well, explicitly state that separately with the actual authority/provenance required by the existing project process. Questions and unselected rows remain pending.

Suggested response format — **unsubmitted draft, not an approval**:

```text
Mission 18A-R choices: R01=__, R02=__, R03=__, R04=__, R05=__, R06=__,
R07=__, R08=__, R09=__, R10=__, R11=__, R12=__, R13=__, R14=__.
Changes or conditions: [actual conditions, or none].
Decision-maker and project authority: [actual details supplied by the researcher].
Decision date and original decision reference: [actual record].
Implementation instruction: [resume the selected bounded synthetic scope, or keep paused].
Git delivery scope if resuming: [retain the original 18A normal commit/push procedure,
or explicitly state a different delivery instruction].
```

The later adoption record should preserve the original response and selected exact scope, rather than replacing it with an assistant-generated APPROVED banner. A verifiable researcher-origin statement through the accepted project process is required; this packet does not invent a signature format, token or new identity service. Do not copy the draft into a live approval record with blanks or substitute a known PI's name without their decision.

## Preparation and preservation receipt

Local HEAD, `origin/main` and live remote matched the baseline during preparation. The two preexisting untracked 18A blocker reports were preserved unchanged. This task adds only this Markdown packet. No source, test, configuration, dependency, protocol, decision register or historical approval was modified. No integration, runtime tests, protected-resource activity, staging, commit or push occurred. Document checks cover the 14 unique decision IDs, two-to-three options per decision, one explicit recommendation per decision, complete blocker mapping and valid file links.

## Mission 18A-R2 status update

The selections are now recorded: R01–R14 are all A, status **SUBMITTED — AUTHORITY UNVERIFIED**. The preparation/response instructions above describe the original packet and are retained as history. The exact user-originated selection is preserved in the [R2 record](MISSION_18A_R2_RESEARCHER_SELECTION_AND_ADOPTION_RECORD.md); no name, role, decision date, PI approval, signature or external message identifier has been inferred. Formal adoption remains **NOT_ADOPTED_PENDING_AUTHORITY_VERIFICATION**. This update does not change any option, threshold, scope or historical approval.

**Mission 18A remains BLOCKED pending verification of the actual decision-maker/project authority and a valid scoped adoption record. All 14 choices have been supplied; they do not need to be selected again. Mission 18A-R2 explicitly prohibits implementation; Mission 18B is not started.**
