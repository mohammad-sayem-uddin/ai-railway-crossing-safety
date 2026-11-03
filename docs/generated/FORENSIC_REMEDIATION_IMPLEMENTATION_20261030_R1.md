# Forensic Remediation Implementation R1 — 2026-10-30

## Changes

1. `src/railway_detection/simulation/runner.py`: optional `preserve_arrival_order` flag. Default
   sorting remains unchanged; B7d can preserve delivery order for Rule 8.
2. `src/railway_detection/experiments/runner.py`: B7d requests arrival-order preservation;
   B7e without explicit schedules is refused; new diagnostic evaluations no longer silently choose
   v9 or assume ground truth.
3. `src/railway_detection/simulation/failure_injector.py`: explicit delayed timestamp branch,
   requiring finite positive `delay_s` and `target_source`, preserving content and shifting record
   timestamps only.
4. `tests/unit/test_failure_injector.py` and `tests/unit/test_experiment_runner_v2.py`: regression
   tests for explicit B7e parameters, content preservation/determinism, B7d boundary behavior,
   and undecided profile semantics.

## Scientific preservation

No scientific parameter was selected. B7e delay magnitude/scope remains configuration-required;
D1/D2/D4 remain unresolved. Historical artifacts are untouched and no empirical rerun occurred.
