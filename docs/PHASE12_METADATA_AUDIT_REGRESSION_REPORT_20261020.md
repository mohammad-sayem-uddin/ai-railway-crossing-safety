# Phase-12 Metadata-Only Audit: Regression Review & Hardening Report

**Date:** 2026-10-20
**Git HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
**Status:** VERIFIED — no commit made; awaiting separate review.

---

## 1. Scope of This Task

Recovery verification and hardening of the metadata-only manifest audit after a
connection interruption. No source-media bytes were accessed. No official readiness
gate, annotation readiness CLI, LEG-EXEC executor, or real-media operation was invoked.

---

## 2. Changed Files

| File | Status | Role |
|------|--------|------|
| `src/railway_detection/evaluation/metadata_only_audit.py` | New (untracked) | Metadata-only audit with tripwire isolation |
| `tests/unit/test_metadata_only_audit.py` | New (untracked) | Synthetic tests proving isolation and scope |
| `src/railway_detection/evaluation/__init__.py` | Modified | Phase-12 module re-exports (pre-existing) |
| `src/railway_detection/evaluation/input_contracts.py` | New (untracked) | Typed hash-bound manifest contracts |
| `tests/conftest.py` | New (untracked) | Tracked-registry guard |

### Implementation changes this session (`metadata_only_audit.py`):
1. Added `AUDIT_MODE_VERSION = "1"` and `AUDIT_SCHEMA` constant.
2. Fixed `candidate.resolve()` before containment check (macOS symlink parity).
3. Removed redundant second `.resolve()`; pass `candidate` directly to loader.
4. Added scope-contract fields: `audit_schema`, `audit_mode_version`,
   `manifest_structurally_valid`, `source_media_verified`, `readiness_prohibition`,
   `provenance_limitations`.
5. Fixed stale variable reference (`path` → `candidate`) in OSError handler.

### Test changes this session (`test_metadata_only_audit.py`):
1. Fixed all `repository_root=` arguments to pass the scenario directory.
2. Added `test_metadata_only_report_declares_the_explicit_scope_contract`.
3. Added `test_metadata_only_audit_creates_no_files_and_leaves_the_tree_untouched`.

---

## 3. Test Results

### Metadata-only audit + input contracts (17/17 PASSED)
```
Command: .venv/bin/python -m pytest tests/unit/test_metadata_only_audit.py tests/unit/test_phase12_input_contracts.py -v
Result:  17 passed in 0.12s | Exit: 0
```

### Safe synthetic Phase-12 regression (64/64 PASSED)
```
Command: .venv/bin/python -m pytest \
  tests/unit/test_metadata_only_audit.py \
  tests/unit/test_phase12_input_contracts.py \
  tests/unit/test_phase12_documented_metrics.py \
  tests/unit/test_phase12_metric_arithmetic.py \
  tests/unit/test_phase12_evaluation_runner.py -v
Result:  64 passed in 0.30s | Exit: 0
```

### Compilation & lint
```
py_compile: COMPILE_OK
git diff --check: Exit 0 (no whitespace errors)
Trailing whitespace: NONE
Note: ruff/flake8/pyflakes not installed; lint limited to py_compile + diff --check.
```

---

## 4. Excluded Tests and Rationale

| Test file | Reason |
|-----------|--------|
| `test_phase12_governance.py` | Calls `assess_official_phase12_readiness(REPO_ROOT)` (lines 672, 962, 987) — invokes official gate on real repo. |
| `test_phase12_official_replay.py` | Calls `cli_main(["evaluation","run","--repository-root",str(REPO_ROOT),...])` (line 815) — official CLI on real repo. |

Both are otherwise synthetic-fixture-based. Exclusion is conservative per task constraints.

---

## 5. Scope Guarantees Verified

| Guarantee | Evidence |
|-----------|----------|
| Only metadata/manifest parsing | `verify_sources=False`; tripwire blocks non-manifest reads |
| No source-byte/GT/annotation/inference imports | Static: only `input_contracts` imported |
| Canonical symlink-safe containment | `candidate.resolve()` + component-walk symlink refusal |
| Tripwire: 5 file-open APIs + write-mode | Parametrized tests + write-blocking test |
| Tracked-registry guard active | `conftest.py` session fixture unchanged |
| No writes to evaluation/GT dirs | Snapshot test confirms zero files created |
| Report self-identifies as metadata-only | `audit_mode`, `readiness_prohibition`, `source_media_verified: False` |
| Structure validation ≠ media integrity | Explicit in `provenance_limitations` and `checks_not_performed` |

---

## 6. Release State: `PREPARED_NOT_ACTIVATED`

File: `docs/generated/stage21_timing_pilot_release.json`

| File | Release hash | Current hash | Match? |
|------|-------------|--------------|--------|
| `stage21_timing_pilot.py` | `38ec9017f26b…` | `24a4b704a172…` | ❌ STALE |
| `test_stage21_timing_pilot.py` | `aa8c585e62e1…` | `2b74ead95ce4…` | ❌ STALE |

**The release manifest is stale.** Not overwritten per instructions. Timing pilot
remains inactive pending separate review.

---

## 7. Incident Documentation (Preserved Uncertainty)

The interruption left no persisted logs. Exact paths/invocation times unknown.
Known code paths that *could* access source media (possible routes, not proven causes):

- `input_contracts.sha256_file()` — hashes sources when `verify_sources=True`
- `input_contracts._read_source_bytes_and_hash()` — reads source bytes
- `stage21_timing_pilot._hash_file()` — hashes media in authorized sessions

No evidence confirms which (if any) was invoked or when.

---

## 8. Remaining Work

1. Review diffs for the two corrected files.
2. Commit when approved (not done here).
3. Optionally run excluded governance/replay tests with explicit approval.
4. Do NOT proceed to release activation or real-media work.
5. Timing pilot remains inactive pending separate review.

---

*No source-media bytes were accessed during this verification session.*