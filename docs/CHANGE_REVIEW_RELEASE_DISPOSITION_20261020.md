# Change Review & Release Disposition Report

**Date:** 2026-10-20
**Git HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
**Worktree:** 18 modified tracked files, ~316 untracked files/dirs (334 total dirty entries)
**Status:** Review complete. No commits, no activation, no media access.

---

## 1. Implementation Review: Metadata-Only Audit

### Files Reviewed
- `src/railway_detection/evaluation/metadata_only_audit.py` (195 lines, untracked)
- `tests/unit/test_metadata_only_audit.py` (227 lines, untracked)
- `src/railway_detection/evaluation/input_contracts.py` (untracked, dependency)
- `src/railway_detection/evaluation/__init__.py` (modified, re-exports)
- `tests/conftest.py` (untracked, registry guard)

### Confirmed Guarantees

| Property | Status | Evidence |
|----------|--------|----------|
| Validates manifest structure only | ✅ | `verify_sources=False` passed to loader |
| No source-media byte access | ✅ | Tripwire + `verify_sources=False` |
| Cannot be mistaken for readiness | ✅ | `official_evaluation_readiness: "NOT_ASSESSED"`, `readiness_prohibition` |
| Rejects unauthorized path access | ✅ | Containment check + symlink refusal + canonical path |
| Rejects writes in execution scope | ✅ | Write-mode tripwire (blocks `wax+` modes) + snapshot test |
| Tracked-registry guard preserved | ✅ | `conftest.py` session fixture active |
| Tests fail on unexpected file access | ✅ | Parametrized tripwire tests for 5 APIs |
| Report self-identifies scope | ✅ | `audit_schema`, `source_media_verified: False`, `provenance_limitations` |

### Issues Found
None in the audit implementation itself. Minor note: the three new files do not
end with a trailing newline (cosmetic, not functional).

---

## 2. Tripwire Limitations (Honest Assessment)

The tripwire intercepts **only** these Python-level APIs:
1. `Path.open()`
2. `Path.read_bytes()`
3. `builtins.open()`
4. `io.open()`
5. `os.open()`

**NOT intercepted:**
- `subprocess` calls that read files externally
- C-extension file I/O (e.g., numpy, cv2, PIL, torch direct reads)
- `mmap` module
- `os.read()` on pre-existing file descriptors
- Network-based file access (NFS, FUSE)
- `ctypes` / `cffi` direct syscalls

**Indirectly covered** (because they call `builtins.open` internally):
- `Path.read_text()`
- `shutil.copy` / `shutil.copyfile`

**Scope of guarantee:** The tripwire is a defense-in-depth layer for the *current*
implementation path (`input_contracts` loader). It is NOT a kernel-level sandbox.
It catches accidental regressions in Python code that uses standard file APIs.
It cannot guarantee isolation against adversarial code, C extensions, or subprocess
spawns. Unit tests confirm the tripwire works for covered APIs; they do not prove
a global security property. Do not claim a global guarantee based on unit tests alone.

---

## 3. Test Results (This Session)

```
Metadata-only audit tests:     13/13 PASSED
Input contract tests:           4/4  PASSED
Documented metrics tests:       7/7  PASSED
Metric arithmetic tests:       22/22 PASSED
Evaluation runner tests:       18/18 PASSED
---------------------------------------------
Total:                         64/64 PASSED (exit 0)
```

- Compile (`py_compile`): PASS
- Changed-file whitespace: PASS (0 trailing spaces, 0 tabs in audit files)
- `git diff --check`: exits 2 due to **pre-existing** whitespace issues in OTHER
  tracked files (`docs/FINAL_*.md`, `tests/fixtures/mock_events.py`,
  `tests/unit/test_layer_b_loader.py`). Not introduced by this session.

**Excluded:** `test_phase12_governance.py`, `test_phase12_official_replay.py`
(invoke official readiness gate / CLI against real repository root).

---

## 4. Release Integrity: Timing Pilot Disposition

### Release Manifest
File: `docs/generated/stage21_timing_pilot_release.json`
Status: `PREPARED_NOT_ACTIVATED` | Version: `0.1.0`

### Hash Comparison (verified this session via `shasum -a 256`)

| Bound file | Release SHA-256 | Current SHA-256 | Match? |
|------------|----------------|-----------------|--------|
| `src/.../stage21_timing_pilot.py` | `38ec9017f26bc466...` | `24a4b704a1723c46...` | ❌ STALE |
| `tests/test_stage21_timing_pilot.py` | `aa8c585e62e162df...` | `2b74ead95ce4933d...` | ❌ STALE |
| `schemas/stage21_timing_pilot.schema.json` | `cef7f7ae7372c246...` | `cef7f7ae7372c246...` | ✅ |

### Why Stale
The implementation and test files were modified after the release manifest was
generated. Both files are untracked, so no git history records when or why they
changed. The schema file is unchanged.

### Disposition Recommendation

**HELD pending additional incident review.**

Rationale:
- The media-access incident remains unresolved (exact paths/times unknown).
- The implementation and tests have diverged from the release hashes.
- No independent review of the diverged code has been performed.
- The pilot must not be activated until the incident is resolved and a new
  release is prepared with correct hashes after independent review.

The old release manifest is preserved unchanged as a historical artifact.
It is NOT superseded, replaced, or deleted by this review.

---

## 5. Incident Evidence Summary

Source: `docs/STAGE21_TIMING_PILOT_INCIDENT_20261019.md` (preserved, unmodified).

### Reported by Operator (Not Independently Verified)
- Two official Phase-12 readiness-status commands ran on 2026-10-19.
- The operator reports these commands opened/hashed source-media bytes through
  the live input manifest.
- This is treated as an access incident for containment purposes.

### Confirmed by Filesystem Evidence (at containment time, 2026-10-19)
- `/tmp/stage21_official_status_audit.json` and `*_final.json` existed with
  mtimes 14:09:49 and 14:17:05 -0400. Contents: `ready: false`, 9 blockers
  across 7 codes, `MANIFEST_MISSING`.
  **These files no longer exist as of 2026-10-20.**
- The current checkout does NOT contain
  `data/manifests/phase12_evaluation_inputs.json`.
- Current source of `assess_official_phase12_readiness()` calls
  `load_evaluation_input_manifest(..., verify_sources=False)`. The source-byte
  read/hash helper is called only in the `verify_sources=True` branch. However,
  the same function calls `verify_checkpoint_integrity()`, which hashes
  checkpoint files. This describes the current snapshot only.

### Possible Code Paths (Source Inspection Only - Not Proven Causes)
- `input_contracts.sha256_file()` - hashes sources when `verify_sources=True`
- `input_contracts._read_source_bytes_and_hash()` - reads source bytes
- `stage21_timing_pilot._hash_file()` - hashes media in authorized sessions
- `verify_checkpoint_integrity()` - hashes checkpoint `.pt` files (not media)

### Unknown / Unresolved
- Exact source-media paths, event identities, and media files accessed
- Exact command start/end times and process/session identifiers
- Whether the live manifest at the time differed from the current absent manifest
- Whether the runtime code differed from the current checkout
- Whether any bytes were read beyond those reported
- Whether any downstream action used the read/hash result

### Evidence Preserved (Not Deleted)
- `docs/STAGE21_TIMING_PILOT_INCIDENT_20261019.md` - primary incident record
- `.probe_write_test` - write-probe artifact (empty content)
- `.commandcode/` - session metadata (session_log.jsonl is empty)
- `RECOVERY_INVENTORY_REPORT.md` - worktree state documentation
- `RECOVERY_RESTORATION_REPORT.md` - recovery actions documentation

**The incident is NOT resolved.** Independent evidence (filesystem/access logs,
process/session logs) is required. Do not claim resolution without it.

---

## 6. Repository & Research Integrity

### Git State
- HEAD: `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (unchanged)
- Modified tracked: 18 files (1,079 insertions, 138 deletions)
- Untracked: ~316 files/dirs
- No staged changes, no commits, no push, no reset, no clean performed

### Ground Truth Records (Verified This Session)
- 27 review records: all valid JSON, schema version `6.0.0` ✅
- 27 invalidation notices (`*_review.INVALIDATION_NOTICE.json`): all valid JSON,
  type `LEGACY_REVIEW_INVALIDATION_NOTICE`, disposition `INVALIDATED` ✅
- All 27 notices' `applies_to_file_sha256_at_notice_time` matches the current
  SHA-256 of the corresponding review file (**27/27 hash-verified**) ✅
- Total: 54 JSON files in `data/ground_truth/reviews/` ✅
- `_INTEGRITY_NOTICE.md` present, confirms non-destructive invalidation ✅
- Directory is untracked (never committed) - no git-level corruption risk

### Protected Files (Not Modified This Session)
- `data/ground_truth/reviews/` - unchanged (verified by hash)
- `configs/frozen_experiment_v1.yaml` - unchanged (untracked)
- `schemas/stage21_timing_pilot.schema.json` - unchanged (hash matches release)
- `docs/generated/stage21_timing_pilot_release.json` - unchanged

---

## 7. Required Next Steps Before Any New Release or Media Activation

1. **Resolve the media-access incident** with independent evidence (filesystem
   logs, process accounting, or session recordings - not self-report).
2. **Independent code review** of the diverged `stage21_timing_pilot.py` and
   `tests/test_stage21_timing_pilot.py` against the v0.1.0 release hashes.
3. **Prepare a new versioned release** (v0.2.0 or later) with correct hashes,
   only after steps 1-2 are complete and approved.
4. **Do NOT activate the timing pilot** until a new release is prepared AND
   explicit researcher authorization is granted.
5. **Commit the metadata-only audit files** when the reviewer approves.
6. **Optionally run excluded tests** (`test_phase12_governance.py`,
   `test_phase12_official_replay.py`) with explicit approval to access real
   repository paths.
7. **Do not regenerate the release manifest, activate the pilot, or create
   activation authorization** until steps 1-4 are satisfied.

---

*This review accessed no source-media bytes. No official readiness gate, annotation
readiness CLI, LEG-EXEC executor, or media operation was invoked. The timing pilot
remains inactive. No files were staged, committed, pushed, reset, cleaned, or reverted.*
