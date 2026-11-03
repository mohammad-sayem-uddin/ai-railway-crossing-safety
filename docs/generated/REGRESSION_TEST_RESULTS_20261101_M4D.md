# Mission 4D Regression Test Results

**Date:** 2026-11-01  
**Scope:** Synthetic fixtures and read-only governance checks only.

## Safety

No test opened, decoded, played, or hashed repository `.mov`, `.mp4`, or `.wav` files. No inference, training, cache generation, experiment rerun, human review, ground-truth modification, promotion, or official evaluation was performed.

## Exact Commands and Results

### New M4D tests (focused)

```bash
PYTHONPATH=src .venv/bin/python -m pytest -xvs tests/unit/test_mission4d_governance_integrity.py
```

Result: **15 passed in 0.42s**

### M4A governance tests (regression)

```bash
PYTHONPATH=src .venv/bin/python -m pytest -xvs tests/unit/test_mission4a_governance_and_stage21_safety.py::test_preflight_validator_separates_d1_d2_from_thresholds_and_roi
```

Result: **1 passed in 0.38s**

### M3 reproducibility tests (regression)

```bash
PYTHONPATH=src .venv/bin/python -m pytest -xvs tests/unit/test_mission3_reproducibility_and_provenance.py::test_experiment_configuration_classes_and_reconstructable_spec tests/unit/test_mission3_reproducibility_and_provenance.py::test_preflight_validator_blocks_missing_prerequisites_and_never_grants_eval_auth
```

Result: **2 passed in 0.51s**

### Combined M4A + M3 + M4D (broad regression)

```bash
PYTHONPATH=src .venv/bin/python -m pytest -x tests/unit/test_mission4a_governance_and_stage21_safety.py tests/unit/test_mission3_reproducibility_and_provenance.py tests/unit/test_mission4d_governance_integrity.py
```

Result: **47 passed in 1.24s**

### Syntax and diff checks

```bash
PYTHONPATH=src .venv/bin/python -m compileall -q src/railway_detection/experiments/preflight_validator.py tests/unit/test_mission4d_governance_integrity.py
git diff --check -- src/railway_detection/experiments/preflight_validator.py tests/unit/test_mission4d_governance_integrity.py
```

Result: **PASS** (both)

### Official readiness gate (read-only)

```python
assess_official_phase12_readiness(Path('.'))
```

Result: `ready=False`, `blockers=9`

## Interpretation

All tests validate software behavior against synthetic fixtures. They do not constitute human review, media inspection, ground-truth approval, or scientific validity. The remediation ensures governance integrity without changing any approved research scope.