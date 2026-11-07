# Complete applicable software validation

All **167 current test modules** were attempted through the existing inherited guarded runner, with no excluded module list and no skipped/blocked test counted as passed. Initial full run exposed two maintenance defects; after fixing them, one final full run validated stable test code. No extra historical subset was rerun solely for a larger count.

| Run | Cases | Passed | Raw failed | Raw errors | Skipped | Known blocked dependency cases | Pytest duration, seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| Initial full | 3806 | 3658 | 88 | 60 | 0 | 118 | 438.637 |
| Final full | 3807 | 3689 | 87 | 31 | 0 | 118 | 438.295 |

The **118 blocked cases are exactly the same case IDs as Mission29's protected-dependency failures/errors**, a subset of the raw failure/error counts, not additional tests. Final distinct outcomes are 3689 passed + 118 blocked = 3807. There are no new unresolved software failures and no whole-repository passing claim. Raw JUnit failures/errors remain recorded, not relabeled as passes. Durations sum actual JUnit suite times and exclude orchestration overhead. The runner's process_errors field counts nonzero child groups, not extra failed tests.

Fix 1: Mission29's semantic mutation fixture called a live loader whose historical source fingerprints correctly became stale after legitimate Mission37/38 changes. It now reads and verifies the original document hashes for in-memory unit mutation tests. The real loader and historical binding are unchanged; an added regression explicitly requires changed-source refusal. All old adversarial tests remain.

Fix 2: the coarse manifest lacked the two Mission37/38 test files. Existing inventory synchronization adds/refreshes entries as **UNKNOWN/unsafe**, preserving earlier evidence and avoiding automatic namespace-safe classification. The actual final per-case guarded execution is separate evidence.

Exact commands, case IDs/outcomes, source fingerprints, log/JUnit hashes and actual durations are in [the validation receipt](SOFTWARE_VALIDATION_RECEIPT.json), [initial raw receipt](software_validation/INITIAL_FULL_TEST_RECEIPT.json), [final raw receipt](software_validation/FINAL_FULL_TEST_RECEIPT.json) and [case table](software_validation/TEST_CASE_OUTCOMES.csv). The [software outcome graph](software_validation/SOFTWARE_TEST_OUTCOMES.png) is software evidence, not model accuracy.

Unit/video/PTS/vision/audio/cache/serialization/metrics/human-schema/authorization/refusal/orchestration/CLI/regression/reproducibility and synthetic integrations are covered where present in those modules. Protected data/checkpoint/registry dependencies are blocked by the inherited audit policy; their attempted cases remain nonpassing, not disabled. Root registry writes are redirected by the guard fixtures. Python hooks are not OS isolation, and software checks do not establish source correctness, accepted GT, permissions or real-world safety.
