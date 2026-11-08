# Mission 18A — Convention B integration blocked at authorization gate

Date: 2026-11-04, America/New_York. **Mission status: BLOCKED. No integration implemented.**

The current Mission 18A instruction, §2, requires: “STOP before modifying implementation code” if a required researcher decision is absent, contradictory or ambiguous. It also explicitly excludes this coding prompt as approval of unresolved scientific policy choices. The repository does not establish those choices. This is the reason for stopping; no additional approval rule or credential requirement is invented here.

Companion: [integration acceptance record](MISSION_18A_INTEGRATION_ACCEPTANCE_RECORD.md).

**Mission 18A-R2 update:** all 14 Option A choices have now been submitted by the user. [Exact selection/adoption record](MISSION_18A_R2_RESEARCHER_SELECTION_AND_ADOPTION_RECORD.md). The earlier search and AG01–AG05 findings below describe the initial blocked attempt; missing option selections are no longer the issue. Decision-maker identity/project authority and formal scoped adoption remain unverified. No implementation is authorized by R2.

## Verified baseline and decision search

Branch `main`; local HEAD, `origin/main`, and live `git ls-remote origin refs/heads/main` all matched **`46ed0d6999cb04ce7be6d48bc2b3476641f86b94`**. That expected Mission 17I commit is present as HEAD and ancestor. The initial working tree was clean, including untracked files. Its parent is `17cc6273544618f0b402a027b41eb527845d3252`. No later commit supplies an approval.

Inspected the specified 17I contract/remediation/register, the 17H and 17G evidence, relevant researcher registers, and runner/gate source as text. A search of tracked text documentation/configuration found explicit `18A` mentions only in the 17I Convention B contract and Mission 18 dependency register. Both describe proposed work. The tracked legacy governance authorization record contains no reference to 18A or Convention B. This establishes what was found in the inspected repository; it does not assert that no private or external researcher decision exists.

Decisive records:

- `docs/generated/master_reaudit/MISSION_17I_MISSION18_ACCEPTANCE_AND_DEPENDENCY_REGISTER.md:22-37`: E01–E04 and A01–A07 retain scope, ownership, clock, metric, watchdog and workload dependencies.
- `docs/generated/master_reaudit/MISSION_17I_MISSION18_ACCEPTANCE_AND_DEPENDENCY_REGISTER.md:69-73`: 18A is conditional on researcher review, scoped authorization, selected policy and E03/E04 disposition.
- `docs/generated/master_reaudit/MISSION_17C3_RESEARCHER_DECISION_AND_RELEASE_GATE.md:42-42`: R04 outcome/estimator/reporting choices remain PENDING.
- `docs/generated/master_reaudit/MISSION_17C3_RESEARCHER_DECISION_AND_RELEASE_GATE.md:51-53`: T02 runner/timing/watchdog and T04 acceptance scope remain PENDING.
- `docs/generated/master_reaudit/MISSION_17E_RESEARCHER_RELEASE_GATE_CHECKLIST.md:32-34`: the relevant runner and acceptance selections are still pending.

The proposed contract defines behavior precisely, but its existence, a technical readiness label, a Git author identity, and historical passing tests do not establish researcher adoption. Older general simulation directions do not select this integration path or resolve its policy choices.

## Missing decisions and records that would resolve them

| ID | Missing or ambiguous decision | Required resolution / repository record |
|---|---|---|
| AG01 | Explicit adoption of Convention B for a named synthetic simulation entrypoint | Researcher-origin decision naming the actual path/class/method and adopting the applicable `17I-CB-V1` requirements for that bounded purpose. Resolve T02 and register A01; the prompt's phrase “appropriate simulation pipeline” does not select one. |
| AG02 | Exact permitted source/module changes and isolation boundary | Name the allowed existing files or new adapter location, and whether the shared `EventSimulationRunner` may change or a separately selected synthetic entrypoint is required. Bind the decision to the inspected baseline/contract and scope. Resolve E01/A01; no source allowlist has been inferred. |
| AG03 | Selected timing, dynamics and estimator profile for the integration | Record exact clock/conversion policy, ARRIVAL/OFFLINE behavior and mapping, origin/cutoff/horizon, effective configuration/rates, watchdog selection, endpoint/continuous/fixed-grid reporting choices and their mapping to existing metrics. Resolve relevant T02/R04 and A02–A05. Contract alternatives and recommended NONE watchdog are not adoption. |
| AG04 | Required compatibility behavior and intentional changes | Decide historical A routing/default preservation, explicit B selection, physical-state mapping, controller call/rejection/reset/fault behavior, result-schema/metric mapping, and which synthetic outputs are intentionally allowed to change. Resolve A01/A03/A04/A06 and CB11. |
| AG05 | Approved synthetic fixture and acceptance scope | Name permitted fixture/test modules and constructed input classes, required A01–A07/CB12 checks and stop conditions. Record ownership of independently retained inputs/configuration/code identity and a practical workload envelope. Resolve relevant T04 and E01/E02/E04. The prompt supplies minimum test expectations but no named path/fixture decision with researcher provenance. |

Resolution may be recorded through the project's accepted researcher decision process and referenced from the existing R04/T02/T04 records and 17I dependency register. It must preserve the genuine original decision, decision-maker/authority, recorded date, selected values and exact scope; an assistant-authored approval label or placeholder signature is insufficient. No new token, signing mechanism, human-review service or unrelated real-data approval is required by this blocker report.

The existing E03 type-analysis issue also needs the scoped disposition already requested by 17I: separately authorized environment repair and actual analysis, or a genuine limited synthetic-stage researcher disposition. This report grants neither and makes no dependency changes.

## Source observations only; no integrated execution path

The candidate existing path is `EventSimulationRunner.run_frames` → `_run_frames` in `src/railway_detection/simulation/runner.py:82-300`. It takes frames, optionally sorts them, resets controller/gate, computes preceding `dt`, evaluates the current frame, handles rejected decisions, maps the current target, steps `PhysicalGateModel`, records trajectory steps and constructs aggregate results. Its current new-target-over-preceding-dt ordering appears at `src/railway_detection/simulation/runner.py:185-231`.

The separate exact helper `CausalRunner.run` at `src/railway_detection/synthetic/convention_b.py:346-488` takes already-decided synthetic commands. It advances the previous command before issuing the new one. CB11 documents the float/exact-time, physical-state, ordering and result compatibility differences. Source identification is not selection or authorization of either a shared-runner change or a new adapter.

Existing test references were identified by source search, including `tests/unit/test_simulation_runner_profiling.py`, `tests/unit/test_phase3_sensor_health_decision_policy.py`, `tests/unit/test_phase1_metric_closure.py` and the isolated `tests/synthetic_mission17d/` suite. These are references for later scoped review, not authorization to execute root or legacy suites. No implementation plan was adopted, no alternate timing logic was added, and no before/after integration example or command-timing/configuration/compatibility verification is claimed.

## Execution, isolation and delivery account

**Fresh test executions: 0. New integration tests: 0. Ruff executions: 0. Mypy analyses: 0.** The mandatory authorization stop precedes implementation/testing. Historical 17I evidence reports 238 passing cases, zero scoped Ruff diagnostics, and Mypy startup failure `ModuleNotFoundError: No module named 'mypy.bogus_type'`; these were not freshly reproduced or represented as 18A acceptance.

All tracked source/test/configuration bytes were compared with HEAD and remained identical. No production module was imported or executed, and no guard, configuration, dependency or researcher record was changed. No new runtime isolation test or OS sandbox result is claimed. No raw media access/preview/playback/decoding/hashing, checkpoint/cache access, real inference/training/replay/evaluation, official split, human annotation/adjudication/GT change, token issuance, CV integration or deployment occurred.

Exactly two local Markdown reports are added:

- `docs/generated/master_reaudit/MISSION_18A_CONVENTION_B_SYNTHETIC_INTEGRATION_REPORT.md`
- `docs/generated/master_reaudit/MISSION_18A_INTEGRATION_ACCEPTANCE_RECORD.md`

No implementation/test file is changed. No staging, commit or push is performed because the authorization/acceptance gate failed. HEAD remains the verified 17I commit; the reports are preserved as untracked files for review. A clean final tree is therefore not claimed. Mission 18B has not begun and requires its own authorization.

## Mission 18A-R2 — current authorization blockers

The user supplied R01=A through R14=A. These selections specify the proposed resolutions of AG01–AG05 and the limited-stage E03 choice; they are recorded as **SUBMITTED — AUTHORITY UNVERIFIED**, not missing or approved. Formal adoption is **NOT_ADOPTED_PENDING_AUTHORITY_VERIFICATION**. See the [R2 record](MISSION_18A_R2_RESEARCHER_SELECTION_AND_ADOPTION_RECORD.md) for the verbatim source and metadata.

Remaining verification: establish the actual decision-maker and applicable project authority/delegation for the submitted statement; obtain the genuine decision date or explicitly record its absence under the accepted process; preserve the actual source reference and bind any verified adoption to this exact packet/scope. The current conversation supplies the selection source, but no external reference, authenticated named researcher connection or scoped adoption was supplied. Do not infer these from filesystem names, Git authorship or a PI name mentioned in older registers. No new signing/token mechanism is required by this report.

Mission 18A-R2 authorizes documentation/verification only and explicitly prohibits implementation. The initial delivery account above belongs to the initial blocked attempt; the current documentation update changes this report, the acceptance record, the decision packet and the 17I dependency register, and adds one R2 selection/adoption record. All implementation/tests and protected records remain unchanged. No staging, commit or push occurs.

**Next action:** verify the remaining authority/adoption metadata against the actual researcher-origin evidence; do not ask for the 14 choices again. Mission 18A remains BLOCKED. A later explicit implementation instruction is required before resuming implementation; R2 grants none. Mission 18B is not started.


## Mission 18A-R3 — authorization recheck; implementation stopped

**Latest mission status: BLOCKED at R3 §2.** The R3 user instruction requests full integration if the authorization gate passes and expressly requires stopping before implementation if authority remains unverified. This supplies the later **conditional implementation instruction** missing during R2; the separate authority/adoption condition remains unsatisfied. R2's documentation-only prohibition is a historical scope, not the reason the new conditional task stops.

Rechecked current main/local HEAD/origin/main/live remote: all remain `46ed0d6999cb04ce7be6d48bc2b3476641f86b94`. Existing work comprises the known local decision/report files and appended 17I register amendment; it is preserved. The latest [R2 adoption record](MISSION_18A_R2_RESEARCHER_SELECTION_AND_ADOPTION_RECORD.md) still explicitly states **SUBMITTED — AUTHORITY UNVERIFIED** and **NOT_ADOPTED_PENDING_AUTHORITY_VERIFICATION**. No later commit or local superseding decision establishes authority. No R01–R14 selection is missing or changed.

**Exact missing evidence:** a genuine source identifying the actual original decision-maker and their applicable project authority/delegation, linked to the submitted all-A statement and its adoption for the exact bounded 18A scope. The R3 prompt repeats the choices and scope but supplies no named decision-maker, verified role/delegation or verified scoped adoption. A Git identity, filesystem name or historical PI name cannot supply that link. The actual decision date remains unsupplied and is recorded as unknown; no timestamp or external reference is invented. This report imposes no new signature format, credential service, token or unrelated protected-data prerequisite.

Checked the eight R3 proposed source/test/report paths against R02-A; they match. Scope/path confirmation does not resolve authority. All 14 choices remain A and are **BLOCKED for implementation**, including the submitted R14 limited-stage Mypy disposition. CB01–CB12/A01–A07 implementation and verification remain NOT TESTED. There is no new integration path or timing/estimator/configuration/detached-result/compatibility result to report.

R3 actions: read-only repository/decision/scope checks and updates to the two already named 18A reports only. New implementation files/tests:0. Fresh runtime tests:0. Ruff runs:0. Mypy analyses:0. Historical17I 238-test/Ruff/Mypy findings are not fresh R3 results. No production execution, protected-resource access or safeguard change occurred. Existing source/tests, packet selections, R2 adoption record and 17I register amendment are preserved without changes by R3.

No staging, commit or push: the required authorization gate failed, so no partial implementation or empty commit is delivered. HEAD/tracking/live stay at the baseline; the preserved local documentation means the tree is not clean. **Do not request the 14 choices again. Verify the remaining authority/adoption evidence before acting on R3's conditional implementation instruction. Mission 18B has not started.**
