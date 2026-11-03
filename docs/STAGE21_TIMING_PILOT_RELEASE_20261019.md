# Stage-2.1 Human Timing Pilot Workflow Release

Version: `0.1.0`  
Release manifest SHA-256: `9e6d990a3676f4473a5cb8cc2cc6471df3ce8e02b6566d03b38142bb190e1abf`  
Status: **PREPARED — NOT ACTIVATED FOR REAL MEDIA**

This release is a human-only, non-evaluative timing-pilot workflow. It is
not the synthetic adjudication runner, does not approve or promote ground
truth, and cannot authorize official evaluation or field activity. The
record/hash envelope is unsigned; SHA-256 binds content but does not
authenticate who authored it.

No source media was opened, decoded, viewed, or processed to prepare this
release. No activation authorization, genuine pilot record, ADJ-AUTH,
EVAL-AUTH, or approval was created.

## Bound files

- `src/railway_detection/annotation/stage21_timing_pilot.py` — `38ec9017f26bc466ec62a58a1511bb11e73ffff21e74de36b4a6a16283ae1c13` (implementation)
- `schemas/stage21_timing_pilot.schema.json` — `cef7f7ae7372c246a64aac4928d52b6f5048ceccac8ea045bf7ed729be154521` (schema)
- `tests/test_stage21_timing_pilot.py` — `aa8c585e62e162df149ad4ad242a53324e7db5ae9ac6cd8e688fddd2e14f314f` (tests)

## Validation

- Focused tests: `passed` (`PYTHONPATH=src venv/bin/python -m pytest -q tests/test_stage21_timing_pilot.py`).
- Full suite: `passed`.
- Compile: `passed`.
- Targeted Ruff lint (pilot implementation and tests): `passed`.
- Repository-wide Ruff check: not clean; reported violations outside this release scope.

## Researcher action required

Inspect the bound implementation, schema, tests, and this manifest. If
later authorizing media use, provide a separate exact-scope, allowlisted
researcher statement binding event keys, reviewers, source inventory,
media/proposal hashes, permitted operations, output path, purpose, and
this release hash. A second, separate activation statement must bind the
authorization hash, release hash, scope hash, and validity window.
Neither statement can approve labels or evaluation. Formal ADJ-AUTH remains
separately required for Stage-2.1 adjudication.
