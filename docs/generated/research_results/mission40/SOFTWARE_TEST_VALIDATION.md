# Software validation

Final retained full run: **3815 cases across 168 modules/53 groups;3700 passed,84 raw failures,31 raw errors,0 skipped.** The 115 nonpassing cases are blocked dependencies under the inherited validation policy and are a subset of raw failures/errors. Full passing acceptance is not claimed. No new regression versus Mission39; three of its118 baseline nonpassing cases are now fixed and passing.

Actual summed JUnit duration: **444.342s**. End-to-end wall time including orchestration: **462.598s**. [Exact commands/durations/hashes](software_validation/VALIDATION_SUMMARY.json), [full per-case receipt](software_validation/FULL_RUN_RECEIPT.json), [3815 outcomes](software_validation/TEST_CASE_OUTCOMES.csv), retained lossless group JUnit/stdout/stderr/policy logs under software_validation/groups/.

| Run | Passed | Failed | Errors | Skipped | Duration |
|---|---:|---:|---:|---:|---|
| Before-fix exact-three reproduction | 0 | 3 | 0 | 0 | Temporary timing not retained |
| First fixture implementation check | 1 | 2 | 0 | 0 | Temporary timing not retained |
| Corrected fixture schema check | 2 | 1 | 0 | 0 | Temporary timing not retained |
| Final exact-three focused check | 3 | 0 | 0 | 0 | Temporary timing not retained; these cases are also in full run |
| Completed pre-resumption full run | 3700 | 84 | 31 | 0 | Complete per-case receipt survived; temporary timing lost |
| Final retained full run | 3700 | 84 | 31 | 0 | JUnit 444.342s; wall 462.598s |

Runs/subsets overlap and are never added. The final full run was repeated because interruption removed temporary timing/reports required by this mission; it saves completed group artifacts incrementally. The earlier completed receipt remains [preserved](software_validation/COMPLETED_PRE_RESUMPTION_RUN_RECEIPT.json), not relabeled incomplete or silently discarded.

Two test modules were corrected: the synthetic pilot no longer assumes27 production files; controlled sentinel bytes are unchanged and actual production opens are refused. Two synthetic benchmark CLI tests use actual generated fixture-file hashes/configs through the existing repository-root argument; they no longer read production weights. Their unversioned fixture is truthfully reported with null revision, while the unchanged real-source environment test still requires a40-character HEAD. Real-artifact fingerprint tests and all assertions on false target/safety claims remain. No production runtime, gate, config, weight, scientific definition or existing real integration test is disabled.

The coarse inventory refresh marks changed tests UNKNOWN/unsafe; it is not an execution grant or automatic safe designation. The final per-case executed evidence is separate. All applicable unit/paired-input/PTS/audio clock/cache/model-config identity/serialization/metrics/human-schema/authorization/refusal/CLI/integration/regression modules were attempted through the inherited guarded runner, no module exclusions. Synthetic outcomes are not railway empirical results; Python hooks are not OS isolation. [Static checks](STATIC_VALIDATION.json) find no new lint issues;20 preexisting pilot-test findings remain, benchmark test has none. Dependency check passes.
