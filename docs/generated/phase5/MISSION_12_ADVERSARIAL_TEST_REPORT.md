# Mission 12 — Adversarial Test Report

## Commands and results

### M-02 / promotion / descriptive security

```text
.venv/bin/pytest -q --no-header \
  tests/unit/test_phase12_evaluation_runner.py \
  tests/unit/test_phase12_governance.py \
  tests/unit/test_phase12_official_replay.py \
  tests/unit/test_media_authorization.py \
  tests/unit/test_media_opener_coverage.py \
  tests/unit/test_descriptive_exec_gate.py
```

**300 passed.**

### Promotion, second review and cache regression

```text
.venv/bin/pytest -q --no-header \
  tests/unit/test_phase5_review_tooling.py \
  tests/test_mission10_second_review.py \
  tests/unit/test_cache_only_replay.py
```

**151 passed.**

### Ruff

`ruff check` passed on changed implementation/security files. `ruff format` was run on the two changed research scripts; `ruff format --check` still reports formatting differences in those scripts and several pre-existing test files. This is reported transparently and is not represented as repository-wide formatting cleanliness.

### Safe runner

```text
.venv/bin/python scripts/run_synthetic_tests.py --report-path /tmp/m12_safe_runner.json
```

The runner exited **3 (refused)** because four changed test files are stale against the existing classification manifest:

- `tests/unit/test_media_authorization.py`
- `tests/unit/test_media_opener_coverage.py`
- `tests/unit/test_phase12_governance.py`
- `tests/unit/test_phase12_official_replay.py`

No tests were executed by this stale-manifest invocation. The 21 protected-access tests remain excluded and were not run.

## Adversarial coverage

- Forged permit with matching digest: rejected.
- Forged permit with wrong digest: rejected.
- Public REAL `run()`: rejected.
- Public REAL `run_from_manifest()`: rejected.
- Synthetic permit use: rejected.
- Synthetic temporary image/video guard: allowed.
- Fake repository media path: denied without authorization.
- PIL/OpenCV reader boundaries: static tripwire and focused tests pass.
- Existing receipt, second-review and descriptive gates: regression tests pass.
- No authorization/receipt/approval created.

## Limitations

Tests are Python-level and synthetic. They do not establish an OS sandbox against arbitrary native code, shell commands or same-process monkey-patching. No real-data operation was attempted.