# Mission 17G — Five-defect remediation and synthetic regression hardening

Date: 2026-11-04, America/New_York. Repository: `/Users/sayemuddin/Desktop/Train_automation`; branch `main`. Verified starting HEAD, origin/main and live remote: `7c247716e390400421c4b0c293e37a90ec1b499e` (Mission 17F). Scope: the two existing synthetic components, directly related tests and this one report.

**Disposition: all five findings are fixed within the bounded synthetic contract; 216 tests pass, including all six former expected-failure cases as ordinary rejection regressions.** Staged-state acceptance passed: 216 total, 114 original, 22 migrated audit and 80 hardening cases, all without failures/errors/skips. The normal Git delivery hash and local/tracking/live/clean verification are supplied in the completion response. This is remediation-author evidence, not independent verification. Mission 17H has not begun; researcher review and a separate instruction precede it. No production or scientific readiness is inferred.

## 1. Starting-state recovery and inspected evidence

Before edits, the tree was clean including untracked files, branch main, local/tracking/live hashes equal the starting commit. `git merge-base --is-ancestor 7c247716e390400421c4b0c293e37a90ec1b499e HEAD` returned success; here the ancestor was HEAD itself. Relevant Git history confirmed the source delivered in 17D and the unchanged C4/D/E/final/17F chain. No reset, clean, forced update or overwrite of newer work occurred. The later resume continued only this mission's identified source/test changes; local/tracking/live still matched the original baseline.

All five 17F reports were inspected: [audit](MISSION_17F_INDEPENDENT_ENGINEERING_AUDIT.md), [controller plan](MISSION_17F_CONVENTION_B_CONTROLLER_INTEGRATION_PLAN.md), [CV/OOF plan](MISSION_17F_CV_PROVENANCE_AND_OOF_IMPLEMENTATION_PLAN.md), [human/security readiness](MISSION_17F_HUMAN_REVIEW_SECURITY_READINESS.md) and [gate register](MISSION_17F_IMPLEMENTATION_GATE_REGISTER.md). Current synthetic source/tests and their Git history were inspected. No production controller, real dataset, checkpoint or protected cache was executed or read to create fixtures.

The original 17F harness was recovered byte-for-byte from the audit's embedded blocks into its documented `/tmp/mission17f_audit/` paths. Existing matching files were preserved; existing result files were copied to `/tmp/mission17g_saved_*` before the documented command ran again. Recovered SHA256 values: pytest.ini `e426e9d19abc292755ba0193e87e40a93f26b61e87db8e131fe90288610e9aa7`; conftest.py `e51a59e2b0971d4e91577a8ee40bc40ca469f1eebe1c12c750a364179e7ebcf7`; test_audit.py `fe770f6bda0b76e5ebd7fca1a12a85951adc60e85bfc725acd8f7334db7b6f27`. These are safe test-source identities only.

## 2. Original evidence, root causes and corrections

| Track / finding | Original evidence reproduced before edits | Root cause | Implemented correction / disposition |
|---|---|---|---|
| A / F17-01 HIGH | Coherent control↔training swap plus an updated development union passed fit-membership validation. | RolePlan described only caller-supplied membership lists; no original dataset/outer-plan binding or independent expected input. | FIXED: bind dataset ID/version/digest, policy digest, allocation digest, all canonical original roles and outer fold. Require separate original RoleContext, revalidate the full source/derivative registry and allocation, reconstruct roles and compare every plan field before membership acceptance. |
| B / F17-02 HIGH | A weak-support candidate shared the strong request's corpus digest, placed both r events together and passed its own-policy verification. | Corpus identity excluded allocation policy and the verifier had no expected-request input. | FIXED: canonical AllocationPolicy includes K/support/budget/profile/search limit/objective/role policy/no-fallback/schema. Every receipt binds its digest; verification requires a separate expected policy and rejects missing, inconsistent or substituted bindings. |
| C / F17-03 MEDIUM | Zero integer objectives could be replaced with bool/float zeros; negative greedy work and FEASIBLE_SEARCH with zero visited nodes passed. | Equality accepted equal-valued wrong types; receipt shape/work/status checks were incomplete. | FIXED: exact closed typed receipt checks before comparison/serialization, including every field, status/work relationships and canonical assignments. Recompute the deterministic bounded synthetic operation against original dataset/expected policy and compare the complete receipt, including reasons/counters/limitations. |
| D / F17-04 MEDIUM | H@0,H@1s logs were identical for close 3s versus 6s and NONE versus an unfired scheduled watchdog. | Output omitted actuator/watchdog configuration and had no complete run-setting binding. | FIXED: immutable exact RunConfiguration plus digest in every result, including EMPTY/INCOMPLETE. Actual motion, watchdog and reporting use the same captured configuration. External expected-configuration verification rejects absence/mismatch; canonical serialization checks internal consistency. |
| E / F17-05 MEDIUM | Default N-interval reporting made 136/528/2080/8256 interval comparisons for N=16/32/64/128. | Each endpoint rescanned all preceding trajectory intervals. | FIXED: default reporting reuses the already-computed event endpoint total; explicit fixed grids use a monotone interval/report merge. Output ordering, threshold, origin/cutoff and incomplete/failure semantics are retained. |

Original evidence remains in `docs/generated/master_reaudit/MISSION_17F_INDEPENDENT_ENGINEERING_AUDIT.md:25-38` and its complete reproduction harness. Historical reports are preserved, not rewritten as though these fixes already existed. The findings describe synthetic interface reliance; no protected-data incident was reproduced or asserted.

## 3. Source changes and precise contracts

### A. Original roles and complete lineage

`src/railway_detection/synthetic/grouped_cv.py:670-687` (RolePlan); `src/railway_detection/synthetic/grouped_cv.py:691-700` (RoleContext); `src/railway_detection/synthetic/grouped_cv.py:703-739` (role_plan); `src/railway_detection/synthetic/grouped_cv.py:742-807` (validate_fit_membership).

PhysicalEvent.role remains mandatory and typed; no role is inferred from a filename, alias or derived record and no default role was added. Existing validate_dataset still resolves canonical aliases, validates every original/annotation join and traverses the entire derivative DAG, rejecting orphans/cycles/multi-event parents. Its AST is unchanged. Every descendant resolves to the same canonical original event and therefore inherits its prospective role. Plan provenance binds that fully validated registry; original_roles covers all canonical groups, including reserved groups.

The caller retains RoleContext from its original dataset/allocation/policy/outer-fold/inner-tuning/calibration/refit inputs, separately from the proposed plan. The fit checker reconstructs the expected plan from these inputs, verifies source/version/role/allocation bindings and only then checks FIT/SELECT/producer membership. Missing context fails closed. A coherent swap, changed original registry, missing role binding or foreign outer/inner plan rejects. A three-generation reserved-control derivative fixture with an alias retains the control role; changing its event cannot silently grant development eligibility.

This is consistency with caller-retained original synthetic inputs. It does not authenticate a curator or protect against an actor who deliberately replaces both candidate and expected source. No identity/authorization service was added. Regression evidence: `tests/synthetic_mission17d/test_mission17g_hardening.py:43-48` (test_role_plan_requires_complete_original_bindings); `tests/synthetic_mission17d/test_mission17g_hardening.py:51-65` (test_missing_original_context_and_changed_original_registry_reject); `tests/synthetic_mission17d/test_mission17g_hardening.py:68-105` (test_alias_and_multigeneration_derivatives_inherit_original_role).

### B. Allocation policy binding

`src/railway_detection/synthetic/grouped_cv.py:383-415` (AllocationPolicy); `src/railway_detection/synthetic/grouped_cv.py:418-422` (allocation_policy); `src/railway_detection/synthetic/grouped_cv.py:476-576` (allocate); `src/railway_detection/synthetic/grouped_cv.py:643-666` (verify_allocation).

The allocator's existing K/support/budget/fallback arguments remain. They construct the exact normalized policy that the operation actually uses; policy identity is not an unrelated reporting parameter. Support rules sort canonically without dropping requirements. Corpus and policy digests stay separate, while the receipt binds both. The allocator profile remains SYNTHETIC_GROUPED_V1 because its mathematical algorithm is unchanged; the changed receipt contract is explicitly SYNTHETIC_ALLOCATION_RECEIPT_V2. Policy schema is SYNTHETIC_ALLOCATION_POLICY_V1.

`verify_allocation(dataset, candidate, expected_policy=original_policy)` is required, as is expected_policy during role-plan construction. Missing expected policy is rejected. Consumers must retain the original request, not rebuild it from candidate fields. Changed K/support/budget/profile/role/objective/search-limit/fallback identity cannot silently validate as the original request. Serialization validates internal policy identity and includes the explicit digest; serialization alone does not establish acceptance against an external request. Old detached receipts without the new binding are not silently upgraded.

Tests: `tests/synthetic_mission17d/test_mission17g_hardening.py:108-126` (test_policy_binding_requires_expected_request_and_rejects_substitution); `tests/synthetic_mission17d/test_mission17g_hardening.py:129-136` (test_policy_normalization_is_deterministic_without_weakening_constraints). The migrated strong/weak regression additionally proves each candidate is valid under its own policy before rejecting the weak candidate against the strong expected request.

### C. Complete synthetic receipt validation

`src/railway_detection/synthetic/grouped_cv.py:426-445` (Allocation); `src/railway_detection/synthetic/grouped_cv.py:584-640` (_validate_receipt_shape); `src/railway_detection/synthetic/grouped_cv.py:643-666` (verify_allocation).

All receipt fields are checked: profile/schema, dataset identity/input digest, K, canonical support, positive budget, exact visited/greedy counters, status, immutable sorted unique event/fold assignments, three exact nonnegative integer objective values for feasible results, reason, policy binding and exact limitations. bool is distinct from integer; float zeros cannot pass as integer zeros. Search statuses require visited nodes, non-search statuses cannot claim them, and budget exhaustion must match the budget. Infeasible/undetermined records have a reason and no accepted assignment/objective.

Verification then reruns the same in-memory bounded allocator against the independently provided request and validated original registry, comparing every receipt field. This rejects plausible but false counters/reasons, stale corpus versions, altered balanced assignments and changed status claims as well as malformed shapes. It proves deterministic reproducibility under that operation, not authenticated historical execution. Verification may repeat up to the declared search budget and is intentionally stricter than accepting any feasible partition; receipts from another allocator/version are not compatible merely because their assignments are feasible.

The allocation algorithm's greedy/search body, objective, support predicate, status definitions, search limit and no-fallback restriction are unchanged (AST comparison). No global optimum or complete large-corpus feasibility guarantee is introduced. Tests: `tests/synthetic_mission17d/test_mission17g_hardening.py:159-165` (test_every_receipt_field_is_checked); `tests/synthetic_mission17d/test_mission17g_hardening.py:168-186` (test_duplicate_noncanonical_and_coherently_forged_receipts_reject); `tests/synthetic_mission17d/test_mission17g_hardening.py:201-217` (test_complete_receipt_contract_for_every_status).

### D. Actual configuration accompanies every run

`src/railway_detection/synthetic/convention_b.py:119-175` (RunConfiguration); `src/railway_detection/synthetic/convention_b.py:211-238` (RunResult); `src/railway_detection/synthetic/convention_b.py:241-266` (verify_run_configuration); `src/railway_detection/synthetic/convention_b.py:305-316` (CausalRunner.__init__); `src/railway_detection/synthetic/convention_b.py:334-476` (CausalRunner.run).

RunConfiguration records exact initial angle/closing/opening durations, normalized watchdog mode/timeout/response, ARRIVAL/OFFLINE mode, normalized cutoff/report grid, profile/schema, timestamp rule, clipped-linear strict≤45 dynamics, existing zero command latency and sensor-first/one-shot timer semantics. Existing threshold and scientific constants are unchanged. At run start the constructor settings and actual run arguments form one immutable snapshot; all actuation/timer/report computations consume its local values. There is no separate caller-selected reporting configuration that can disagree with used settings.

Every returned status retains this snapshot and digest; empty/uninitialized physical output stays distinct from configured initial angle. Missing settings fail at construction/verification rather than receiving retrospective defaults. `verify_run_configuration(result, expected_configuration=retained_settings)` checks against a separate expected record. Result canonicalization also rejects absent/broken internal bindings and result mode/grid/initial-angle contradictions. A coherent forged replacement of configuration and digest rejects against the retained expected settings. It is not a complete re-execution proof of the trajectory or a source-code signature; preserve input fixtures and tested code identities too.

Before→after: close 3s and 6s on the same all-H fixture still have identical angles/durations, but configuration records/digests and serialized results now differ. Equivalent command aliases normalize to the same watchdog response. A mutation probe changes the runner's future settings during motion and demonstrates the current run still uses/logs its original 3s snapshot; the next run uses/logs 6s. Tests: `tests/synthetic_mission17d/test_mission17g_hardening.py:242-260` (test_complete_configuration_snapshot_and_equivalent_representations); `tests/synthetic_mission17d/test_mission17g_hardening.py:263-280` (test_missing_mismatched_or_substituted_configuration_rejects); `tests/synthetic_mission17d/test_mission17g_hardening.py:298-314` (test_run_consumes_one_snapshot_even_if_runner_is_reconfigured_during_motion).

### E. Reporting complexity and numerical equivalence

`src/railway_detection/synthetic/convention_b.py:283-299` (_report_endpoint_seconds); `src/railway_detection/synthetic/convention_b.py:334-476` (CausalRunner.run); `tests/synthetic_mission17d/test_mission17g_hardening.py:318-351` (test_fixed_report_grid_uses_linear_interval_accesses); `tests/synthetic_mission17d/test_mission17g_hardening.py:354-371` (test_fixed_grid_merge_matches_separate_slow_geometric_lookup).

Previously, default report endpoints each started at interval 0: S(S+1)/2 comparisons, Θ(S²). An arbitrary R-endpoint fixed grid had worst-case O(S*R) lookups. Now default reporting performs zero extra trajectory lookups and reuses D_E_event. Existing grid construction and event/integral totals remain O(S). For a fixed grid, the interval index never decreases: at most S−1 advances and R endpoint evaluations give O(S+R) reporting work and O(1) extra traversal state, apart from stored input/output grids. This is an arithmetic-operation bound; exact-rational bit costs and OFFLINE input sorting are additional costs. No whole-run wall-clock or hardware-speed guarantee is claimed.

The merge uses the same inclusive segment endpoint convention and exact `_motion` arithmetic; `_motion` itself is unchanged. Single-point grids yield 0; invalid/nonspanning/empty grids still reject and incomplete runs still have no certified fixed-grid total. A separate slow geometric endpoint lookup agrees on 50 additional deterministic nontrivial trajectories. Default-grid tests use a failing lookup stub, so merely changing an instrumented source line cannot hide a rescan.

Fixed-grid scaling instruments actual interval sequence `len`/index accesses through the runner, not elapsed time. Every case asserts accesses≤8*(S+R), and verifies blocked-time output independently for its all-LOWER fixture. Observed counts from JUnit properties:

| S intervals | R report intervals | Observed interval sequence accesses |
|---|---|---|
| 16 | 16 | 94 |
| 32 | 128 | 574 |
| 128 | 128 | 766 |
| 512 | 2048 | 9214 |
| 2048 | 2048 | 12286 |

These finite scaling checks support the inspected monotone-loop bound; they do not prove all future implementation versions retain it.

## 4. Six former expected failures — exact recovery and final dispositions

The original fixture bodies and parameter values were recovered from 17F, not guessed. They were first executed without expected-failure handling and all six failed specifically with `DID NOT RAISE InvalidInput`, not fixture errors. Their migrated counterparts are committed ordinary tests with explicit original request/context and positive controls; no xfail/skip marker remains in the current suite.

| Original test / parameter | Invalid input preserved | Final disposition |
|---|---|---|
| test_context_bound_fit_gate_should_reject_coherent_control_to_train_swap | Control/train exchange and coherent changed development union | PASS: rejects against original RoleContext; valid original plan first succeeds. |
| test_context_bound_allocation_gate_should_reject_weakened_request | Same corpus, weak policy places both r events together | PASS: both original candidates validate under their own policy; weak candidate rejects against original strong policy. |
| test_receipt_validator_should_reject_invalid_types_and_work_semantics[bool_objective] | `(False,False,False)` in place of integer zeros | PASS: exact objective type rejection. |
| test_receipt_validator_should_reject_invalid_types_and_work_semantics[float_objective] | `(0.0,0.0,0.0)` in place of integer zeros | PASS: exact objective type rejection. |
| test_receipt_validator_should_reject_invalid_types_and_work_semantics[negative_work] | greedy_choices=−1 | PASS: work-counter rejection. |
| test_receipt_validator_should_reject_invalid_types_and_work_semantics[search_without_nodes] | FEASIBLE_SEARCH and visited_nodes=0 | PASS: search/visited-node contradiction rejection. |

Current source/test names: `tests/synthetic_mission17d/test_mission17f_regressions.py:150-164` (test_context_bound_fit_gate_should_reject_coherent_control_to_train_swap); `tests/synthetic_mission17d/test_mission17f_regressions.py:167-179` (test_context_bound_allocation_gate_should_reject_weakened_request); `tests/synthetic_mission17d/test_mission17f_regressions.py:183-198` (test_receipt_validator_should_reject_invalid_types_and_work_semantics).

The 22 migrated 17F cases retain the 200 geometric trajectories, 2704 tiny exhaustive CV inputs, 50 dense greedy-objective comparisons, known-feasible budget/size-undetermined examples, timestamp/cutoff/watchdog and import isolation checks. Necessary API edits supply independently chosen expected inputs. Two old configuration-collision characterizations now require distinct provenance with identical numerical output; four old quadratic-characterization cases now prohibit any extra default-grid lookup. Those were intentionally changed from assertions that diagnosed the bugs into positive fix requirements. Historical originals and baseline results are retained; no failed requirement was removed or weakened to obtain a pass.

The original 17D test module's assertion conditions and parameterized cases are preserved; only expected-policy/context arguments and local original context construction changed. Some conjunctions were split for readability without dropping either condition. AST comparison confirms all original assertion conditions remain after stripping only the new binding keywords. The 70 simulation tests, original conftest and 6 isolation tests are byte-identical to 17F.

## 5. Exact commands and executed results

Environment: repository `.venv/bin/python` 3.11.15, plugin autoload/cache/bytecode disabled. Only the constructed synthetic directory is collected, with root conftest excluded. No legacy/root suite or production/resource entrypoint is executed.

The exact command required by 17G (same selector as 17D):

```sh
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest --confcutdir=tests/synthetic_mission17d -p no:cacheprovider --import-mode=importlib tests/synthetic_mission17d -q
```

Before edits: 114 passed in 0.55s (`/tmp/mission17g_baseline_17d.txt`). After fixes, this directory includes the original 114 plus 22 migrated audit and 80 new hardening cases. Development runs passed 114, then 22 migrated cases, then 80 hardening cases; the complete final development receipt records **216 passed in 4.51s**, 0 failures/errors/skips. JUnit gives 70 original simulation, 38 original CV, 6 isolation, 22 migrated 17F and 80 hardening. No feature assertion failed during these correction runs; the only deliberate feature failures were the reproduced six pre-fix witnesses.

The additional exact 17F command was discovered in the audit and run against recovered original bytes before edits:

```sh
PYTHONPATH=/Users/sayemuddin/Desktop/Train_automation/src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -c /tmp/mission17f_audit/pytest.ini --confcutdir=/tmp/mission17f_audit --import-mode=importlib -p no:cacheprovider /tmp/mission17f_audit -q --tb=short --junitxml=/tmp/mission17f_additional.xml > /tmp/mission17f_additional_console.txt 2>&1
```

Observed baseline: 16 passed, 6 xfailed in 2.63s, exit 0. Copies are `/tmp/mission17g_baseline_additional.xml` and `/tmp/mission17g_baseline_additional_console.txt`. The subsequent exact six-case diagnostic was:

```sh
PYTHONPATH=/Users/sayemuddin/Desktop/Train_automation/src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -c /tmp/mission17f_audit/pytest.ini --confcutdir=/tmp/mission17f_audit --import-mode=importlib -p no:cacheprovider /tmp/mission17f_audit -q --runxfail -k 'context_bound or receipt_validator' --tb=short --junitxml=/tmp/mission17g_baseline_six.xml > /tmp/mission17g_baseline_six.txt 2>&1
```

Observed: **6 failed, 16 deselected in 0.08s**, exit 1; each exact required rejection was missing. These are historical reproduction failures, not accepted regressions. The original harness's session-end observation JSON is per invocation and was overwritten by the witness-only run; full baseline console/JUnit remain preserved. No receipt from 17F's previous execution was substituted for these fresh 17G runs.

Current reproducible selectors (append `--junitxml=/tmp/<receipt>.xml -o junit_family=legacy` when recording JUnit/properties):

```sh
# Original test modules plus unchanged conftest: 114 cases, with explicit binding API.
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest --confcutdir=tests/synthetic_mission17d -p no:cacheprovider --import-mode=importlib tests/synthetic_mission17d/test_convention_b.py tests/synthetic_mission17d/test_grouped_cv.py tests/synthetic_mission17d/test_isolation.py -q
# Recovered and migrated audit: 22 ordinary cases, zero xfail/skip markers.
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest --confcutdir=tests/synthetic_mission17d -p no:cacheprovider --import-mode=importlib tests/synthetic_mission17d/test_mission17f_regressions.py -q
# New hardening: 80 cases.
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest --confcutdir=tests/synthetic_mission17d -p no:cacheprovider --import-mode=importlib tests/synthetic_mission17d/test_mission17g_hardening.py -q
```

The required full-directory command and these three selectors were run again against exact staged code/test bytes. Observed staged results: **216 passed in 4.41s; original 114 passed in 0.57s; migrated audit 22 passed in 3.75s; new hardening 80 passed in 0.26s**. All exit codes were 0, with zero failures/errors/skips/expected failures. These overlap: the 216-case full suite contains the 114+22+80 subsets; they are not additional unique cases. Receipts `/tmp/mission17g_staged_tests.json` and `/tmp/mission17g_staged_*.xml` retain exact argv/env/results/counts and source hashes. Syntax/AST/diff checks also passed against staged bytes. This report-only receipt update changes no tested source/test bytes; the exact required full-directory command runs once more after its staging. Local receipt paths are not extra repository deliverables.

## 6. Static inspection and isolation evidence

Syntax/AST compilation passed for all nine current synthetic package/test Python files without writing bytecode. Component imports remain standard-library-only. Inspected component AST contains no file/network/process/dynamic-code entrypoint; named-call scan distinguishes regex `re.compile` from code compilation. No dependency was installed. AST comparison verifies unchanged core motion/timestamp/command functions, full dataset-lineage validator, allocation objective/predicate and greedy/search body. The prior synthetic namespace, no-fallback and INNER_OOF denial boundaries are preserved.

The existing IO-denial conftest and isolation test file remain byte-identical. The six isolation tests pass within the full suite, and every new test inherits the same file/Path/socket/Popen denial fixture. Production CLI/runner/splitter and model/decoder imports remain absent in the isolation check. This is Python-level test isolation; no OS sandbox or syscall-complete monitoring claim is made. Audit tooling, pytest imports and temporary result writing happen outside the per-test guards and touch source/tests/results only.

`git diff --check` passes. Ruff is unavailable (no executable or module), so no Ruff pass is claimed. Mypy could not analyze: `.venv/bin/python -m mypy ...` fails because the installed package has no `__main__`; trying `mypy.api.run(['--follow-imports=skip','--cache-dir=/tmp/mission17g_mypy_cache', 'src/railway_detection/synthetic/convention_b.py', 'src/railway_detection/synthetic/grouped_cv.py'])` fails during startup with `ModuleNotFoundError: No module named 'mypy.bogus_type'`. This is an unusable partial installation, not a completed type-check result or a code diagnostic. No dependency repair or installation was attempted in this bounded scope. Type/lint checks remain unexecuted; runtime/syntax/AST/isolation checks above were executed.

Unexecuted scope: unrelated legacy/root tests, real controller integration/CB cases, full trusted fitted-artifact/OOF/PV registry features, all 32 ES/C4 SEC security cases, deployment/OS isolation and all real-resource/scientific workflows. They are not counted as passes.

## 7. Exact files changed and tested byte identities

| Path | Change |
|---|---|
| `src/railway_detection/synthetic/convention_b.py` | Modified: actual configuration snapshot/log binding and linear report merge. |
| `src/railway_detection/synthetic/grouped_cv.py` | Modified: policy/role/receipt bindings and deterministic receipt verification. |
| `tests/synthetic_mission17d/test_grouped_cv.py` | Modified: mandatory expected-request/context arguments; original assertions/cases preserved. |
| `tests/synthetic_mission17d/test_mission17f_regressions.py` | Added: 22 migrated audit cases, six ordinary rejection regressions, updated configuration/scaling requirements. |
| `tests/synthetic_mission17d/test_mission17g_hardening.py` | Added: 80 focused missing/contradictory/stale/typed/lineage/config/scaling cases. |
| `docs/generated/master_reaudit/MISSION_17G_FIVE_DEFECT_REMEDIATION_REPORT.md` | Added: this one remediation report. |

No files are deleted. No existing historical report, source outside the synthetic package, controller, configuration, protocol, governance record, dataset, result, allowlist or adjudication_session.py is changed. Exact staged bytes must match these reviewed source/test identities:

| Safe source/test path | SHA256 |
|---|---|
| `src/railway_detection/synthetic/__init__.py` | `a269b30d6399436161dc863db33fd4dccb7d243926ea6c1fd505adabec278f02` |
| `src/railway_detection/synthetic/convention_b.py` | `654ba0d93ef05c0fa25f37c8424c0ba2dd7c4d413c98f8c48174045a2de0ee5c` |
| `src/railway_detection/synthetic/grouped_cv.py` | `dfc88ffbdff31f5db8339a5b799aa1f6fd6228efdcf775e243de8b6addc1339e` |
| `tests/synthetic_mission17d/conftest.py` | `e64acca4d8d4a390bf1c6eb07fbba3ad16827f839bba60c922a5f85793dc3438` |
| `tests/synthetic_mission17d/test_convention_b.py` | `2dfe06cb537a27f4d45cf4d2bda7d5722b25e7b935bdbca2a789e244e187f4da` |
| `tests/synthetic_mission17d/test_grouped_cv.py` | `4785409852b179154c9d454f4568127e5a1e6535ee63e14f4547d5e6b8a67e08` |
| `tests/synthetic_mission17d/test_isolation.py` | `5d9424894bb70979695114bb72b9955885b6448874f6c8eddbfddf8622c52986` |
| `tests/synthetic_mission17d/test_mission17f_regressions.py` | `4dc90466b9185a7d8a84df5ea8e6867174db551dccad948a4ae5f8fb659a8898` |
| `tests/synthetic_mission17d/test_mission17g_hardening.py` | `996e80263645cad239e3c56590ef333472554182e6234e04210f8664c3336d51` |

## 8. Protected activity account

Raw media opened/previewed/decoded/probed/hashed: 0. Real dataset records/resources processed: 0; only newly constructed synthetic metadata were allocated. Production checkpoints/protected caches accessed: 0/0. Real training/inference/replay/evaluation: 0. Base/preprocessor/calibrator fits: 0. Official split generation/promotion: 0/0. Human annotation/adjudication/GT modification: 0. Authorization tokens issued/consumed: 0/0. Reviewer identities/appointments/allowlists changed: 0. Research protocol/governance/camera-scope/metric definitions changed: 0. Researcher scientific/governance approvals created: 0. No guard was changed or bypassed, and no production module was wired to these helpers.

The actual existing gate-controller defaults, threshold definitions, independent-camera directions, proposed protocol status, RD001–RD055 and all pending researcher/protected execution decisions remain unchanged. Synthetic metadata bindings and passing tests grant no resource capability or scientific eligibility.

## 9. Limits and remaining questions

All five named defects have implemented corrections with targeted passing evidence; no known unresolved failure remains in their bounded synthetic contract. The complete original request/context must be independently retained by the synthetic caller. Hashes establish byte consistency, not human truth, identity, trusted deployment or protection against a caller replacing both candidate and expected inputs. Canonical strings are not signed authority records or a general hostile-input JSON codec.

Allocation verification deliberately recomputes the bounded operation, including search up to node_budget; this adds CPU work. It preserves polynomial greedy behavior but does not make budgeted search polynomial or guarantee a large feasible problem is solved. First-feasible/undetermined/global-optimum distinctions and scientific exposure limitations remain. Same-implementation replay alone cannot rule out correlated allocator bugs; the retained 2704 exhaustive-oracle checks provide finite additional evidence, not an all-input proof.

Configuration verification checks the settings binding, not every trajectory datum or authenticity of executing code. Exact input fixtures and source receipts remain needed for full reproduction. Legacy detached receipts/logs require explicit migration; missing bindings are rejected instead of silently defaulted. CausalRunner's read-only public configuration properties and explicit expected policy/context are intentional API hardening. No production consumer integration was attempted.

The 80 added cases and migrated 22 cases were authored in this remediation phase; they do not constitute independent 17H challenge. Ruff/mypy checks could not complete in this environment. Independent engineering challenge should examine receipt-policy/context trust assumptions, replay cost, configuration schema and reporting merge on additional adversarial fixtures. Real OOF provenance, human/security services, actual-controller adoption and protected permissions remain outside this task.

## 10. Commit gate and stop

Review the complete worktree and staged diff; permit only the six paths above, exactly three modifications and three additions. Validate this report's references/equations/test counts and all source/test hashes. Run the required tests again against the staged state and preserve source hashes before/after. Check secrets/protected-path/unrelated-change exclusions. Recheck live origin/main remains the verified baseline; divergence or any failed safety gate stops delivery and preserves work.

After these checks pass, commit `fix: remediate mission 17F synthetic engineering findings`, push normally to origin/main, verify exact changed paths, local HEAD=origin/main=live remote and clean tree. No force/reset/clean/amend/rebase/history rewrite or broad staging is permitted. Actual resulting commit and delivery verification are supplied in the final response; a report cannot contain its own commit hash without self-reference.

**STOP after delivery.** The work is ready to be considered for a separately authorized Mission 17H engineering challenge after researcher review. Do not begin 17H automatically, integrate a controller, implement OOF/human-review infrastructure or conduct real-data work.
