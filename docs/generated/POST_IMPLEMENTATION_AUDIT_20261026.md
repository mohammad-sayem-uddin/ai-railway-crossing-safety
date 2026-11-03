# Train Gate Automation — Post-Implementation Audit

**Date:** 2026-10-26  
**Audit scope:** static repository audit plus synthetic-only validation  
**Labels:** `IMPLEMENTED`, `TESTED_SYNTHETICALLY`, `NOT_VERIFIED`, `BLOCKED_BY_AUTHORITY`, `BLOCKED_BY_MISSING_EVIDENCE`

## Verified repository state

- Repository root: `/Users/sayemuddin/Desktop/Train_automation`
- Branch / HEAD: `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
- Staged entries: 0. No commits, pushes, resets, clean operations, restores, or deletions were performed.
- The worktree remains materially dirty (tracked changes and a large set of untracked research artifacts). It was preserved. The earlier baseline remains at `docs/generated/AUTONOMOUS_IMPLEMENTATION_BASELINE_20261026.md`.
- The committed protocol set (v8/v6) and worktree set (v9/v7) still conflict. `NOT_VERIFIED`: no authority selection was made.

## This-pass changes — `IMPLEMENTED`

1. `sync_calibration.load_validated_sync_aligner()` now refuses a calibration-manifest path outside the supplied repository root and maps YAML/read errors to `CalibrationNotAcceptedError`.
2. Clock fields now require native finite numeric values. Numeric strings, booleans, NaN, infinity, missing values, and negative uncertainty are refused. Explicit `0.0` offset/uncertainty remains valid.
3. Synthetic tests now cover malformed YAML, manifest and media path traversal, absolute paths, symlink escape, malformed event/camera objects, and invalid clock values.

## Synchronization audit — `TESTED_SYNTHETICALLY`

| Requirement | Result |
| --- | --- |
| Missing offset / uncertainty | Refused; missing uncertainty retains `SYNC_UNALIGNED`. |
| Malformed numeric values | Refused before an aligner is constructed. |
| Explicit zero | Accepted when declared as a numeric value. |
| Negative / NaN / infinite uncertainty | Refused as unaligned. |
| Calibration manifest outside repository | Refused. |
| Absolute, traversal, and symlink media paths | Refused before file hashing. |
| Invalid YAML | Refused as a calibration error. |
| Replay refusal-code propagation | `RealEventReplayProducer` preserves the calibration-specific code. |

## Work-package audit

| WP | Status | Direct evidence / remaining gap |
| --- | --- | --- |
| WP-0 | `IMPLEMENTED` | Baseline and contradiction inventory exist; worktree preserved. |
| WP-1 | `TESTED_SYNTHETICALLY` | Governance refusal tests pass; researcher authority remains required. |
| WP-2 | `TESTED_SYNTHETICALLY` | Hash-bound manifest and replay-input contract tests pass. |
| WP-3 | `BLOCKED_BY_AUTHORITY` | No candidate annotation was promoted and no approved ground truth was created. |
| WP-4 | `NOT_VERIFIED` | Phase-12 replay consumes serialized evidence and has no tested cache-miss raw fallback; however the proposed cache-only engine is not implemented/authorized, and legacy Layer-B paths still decode media. |
| WP-5 | `TESTED_SYNTHETICALLY` | Existing evidence contracts, parsing, and scope checks were exercised. |
| WP-6 | `TESTED_SYNTHETICALLY` | Collector and decision-engine ordering/fail-closed tests pass. |
| WP-7 | `TESTED_SYNTHETICALLY` | Metric tests preserve M4 as `first_blocked_to_t4_clearance`, M5 handling, and no-default protocol choice. |
| WP-8 | `TESTED_SYNTHETICALLY` | Official-shaped readiness/refusal paths pass without real execution. |
| WP-9 | `TESTED_SYNTHETICALLY` | 282 selected synthetic tests passed. |
| WP-10 | `BLOCKED_BY_AUTHORITY` | No official benchmark run. |

## Raw-media boundary audit — `NOT_VERIFIED` for legacy paths

No project raw media was opened, decoded, previewed, played, inferred on, or hashed during this audit. All tests used temporary synthetic bytes only.

Static tracing found:

- `RealEventReplayProducer` consumes manifest-bound serialized evidence; a missing/invalid payload is refused through the input/replay contract, with no raw-media inference fallback in that route.
- The dual-camera synchronization branch calls `load_validated_sync_aligner`, which intentionally hashes raw media only after the official readiness gate has passed. This is not a cache-miss fallback, but it means this route is not a strict no-media-access execution path.
- `LayerBEventProcessor`, `scripts/run_phase5_full_inference.py`, and `scripts/run_real_world_experiments.py` retain raw video/audio routes. The latter two are not cache-only entrypoints and were not run.
- `docs/CACHE_ONLY_REPLAY_DESIGN.md` labels `CacheOnlyReplayEngine` as proposed and not authorized. No implementation or activation was performed.

## Validation — `TESTED_SYNTHETICALLY`

Executed command:

```text
.venv/bin/python -m pytest -q \
  tests/unit/test_layer_b_loader.py \
  tests/unit/test_validated_sync_aligner.py \
  tests/unit/test_collector_fail_closed_fusion.py \
  tests/unit/test_decision_engine.py \
  tests/unit/test_phase12_input_contracts.py \
  tests/unit/test_phase12_evaluation_runner.py \
  tests/unit/test_phase12_documented_metrics.py \
  tests/unit/test_phase12_official_replay.py \
  tests/unit/test_metadata_only_audit.py \
  tests/unit/test_phase12_governance.py \
  tests/test_phase12_ground_truth_loader.py \
  tests/test_phase11_9_synthetic_pilot.py
```

Result: **282 passed, 0 failed, 0 skipped** in 10.18 seconds. This is a selected synthetic-only suite, not a repository-wide pass.

Ruff was run on the synchronization files and touched tests. It reported 13 existing style violations (long lines and delayed imports in already-modified/untracked files). No broad formatting rewrite was applied; no newly observed behavioral-test failure remains.

## Remaining blockers and next actions

`BLOCKED_BY_AUTHORITY`:

- Select the effective protocol version and the premature-opening definition.
- Approve ground truth, valid synchronization scope, and official evaluation authorization before real execution.
- Authorize any implementation of the proposed cache-only replay design before it is created or activated.

Safe future work without research authorization is limited to additional synthetic contract/regression tests and narrowly scoped static hardening. It cannot produce empirical results, establish field safety, promote labels, or make the benchmark executable.

## Completion assessment

The synchronization hardening audited here is implemented and synthetically tested. The repository is **not benchmark-ready**: cache-only replay remains an unimplemented proposed design, legacy raw-media paths remain present, and required scientific/governance authority is unresolved.
