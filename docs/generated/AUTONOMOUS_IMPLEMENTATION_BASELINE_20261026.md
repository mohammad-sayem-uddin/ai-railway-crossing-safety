# Train Gate Automation — Autonomous Implementation Baseline

**Recorded:** 2026-10-26 (metadata/static inspection only)  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Git HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (`main`, tracking `origin/main`)

## Preservation snapshot

- Staged entries: 0. No commits, pushes, resets, clean operations, or restores were performed.
- At snapshot time, the worktree contained 19 tracked modified/deleted entries and 10,238 untracked files. They are pre-existing/user work unless explicitly identified below; no bulk cleanup was attempted.
- Raw media was not opened, decoded, previewed, inferred on, or hashed. Static source and metadata records were inspected only.
- No official real-data replay, inference, benchmark, timing pilot, annotation promotion, or evaluation was executed.

## Protocol-authority contradiction inventory

The committed protocol set and the unstaged worktree protocol set differ. This report records the conflict; it does not select an effective version.

| Artifact | HEAD | Worktree | Implementation effect |
| --- | --- | --- | --- |
| `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` | v8.0.0 | v9.0.0 | Revised R03 disposition and operational annotation convention require researcher authority confirmation. |
| `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` | v6.0.0 | v7.0.0 | Ground-truth prerequisite wording and R03 disposition differ. |
| `docs/FINAL_EXPERIMENT_DATA_FLOW.md` | v6.0.0 | v7.0.0 | Reference architecture reflects the worktree protocol update. |
| `docs/FINAL_ABLATION_MATRIX.md` | v6.0.0 | v7.0.0 | Evaluation-prerequisite wording reflects the worktree protocol update. |
| `README.md` | prior status/environment text | unstaged revised text | Supporting documentation has no versioned authority decision. |

The implemented protocol-choice contract remains fail-closed: both `t1_entry_to_t4_clearance` and `first_blocked_to_t4_clearance` (M4) are structurally supported, neither is defaulted, and an official profile requires an explicit researcher decision. M4 is retained as `first_blocked_to_t4_clearance`; it is not substituted with a presumed `[T2, T3]` interval.

## Authorized implementation in this session

Clock registration now requires explicit finite offset and uncertainty values. The calibration loader rejects missing/non-computable front offset, back offset, or back uncertainty instead of defaulting to zero or a tolerance. A missing uncertainty is surfaced as `SYNC_UNALIGNED`; other missing calibration fields are `SYNC_CALIBRATION_REJECTED`.

These changes are limited to structural clock-integrity enforcement and synthetic tests. They do not alter a frozen experiment configuration, policy, label, model weight, media file, or protocol choice.

## Validation evidence

Synthetic-only tests passed:

```text
.venv/bin/python -m pytest -q \
  tests/unit/test_layer_b_loader.py \
  tests/unit/test_validated_sync_aligner.py \
  tests/unit/test_collector_fail_closed_fusion.py \
  tests/unit/test_decision_engine.py \
  tests/unit/test_phase12_input_contracts.py \
  tests/unit/test_phase12_evaluation_runner.py \
  tests/unit/test_phase12_documented_metrics.py \
  tests/unit/test_phase12_official_replay.py
159 passed
```

```text
.venv/bin/python -m pytest -q \
  tests/unit/test_metadata_only_audit.py \
  tests/unit/test_phase12_governance.py \
  tests/test_phase12_ground_truth_loader.py \
  tests/test_phase11_9_synthetic_pilot.py
111 passed
```

The final combined re-run of those same 12 synthetic-only test modules passed: **273 passed in 8.37s**.

Ruff was also run on the touched safety modules and related tests. It reported existing style violations in already-modified/untracked files; no broad formatting rewrite was applied. This is a style follow-up, not evidence against the passing synthetic behavioral tests.

## Remaining gates

- Researcher authority must select the effective protocol version and resolve the premature-opening definition decision.
- Approved ground truth, valid synchronization evidence for any requested dual-camera event, and a live evaluation authorization remain required before official execution.
- Synthetic correctness does not establish field safety, empirical performance, or benchmark readiness.
