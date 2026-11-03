# Regression Test Results — Remediation R1 — 2026-10-30

```text
PYTHONPATH=src .venv/bin/python -m pytest \
 tests/unit/test_failure_injector.py \
 tests/unit/test_experiment_runner_v2.py \
 tests/unit/test_event_metrics.py -q --tb=short
24 passed in 0.48s

PYTHONPATH=src .venv/bin/python -m pytest \
 tests/unit/test_descriptive_only.py \
 tests/unit/test_cache_phase12_adapter.py \
 tests/unit/test_cache_only_replay.py \
 tests/unit/test_phase12_governance.py \
 tests/unit/test_phase12_input_contracts.py \
 tests/unit/test_phase12_documented_metrics.py \
 tests/unit/test_phase12_metric_arithmetic.py -q --tb=line
226 passed in 1.60s

Python compilation: passed
Ruff on modified test/source set: legacy runner has pre-existing E501 only; no new runtime errors
git diff --check: passed
```

No raw media, inference, cache generation, rerun, promotion, EVAL-AUTH, or official evaluation was performed.
