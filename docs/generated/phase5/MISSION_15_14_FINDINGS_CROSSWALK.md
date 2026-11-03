# Mission 15 — WP15.2 Fourteen Claimed Fixes Crosswalk & Verification

**Auditor:** Independent Principal Security Auditor and Research Reproducibility Auditor  
**Date:** 2026-11-02  
**Mission:** 15  
**Priority:** CRITICAL  
**Verification Scope:** All 14 remediations claimed fixed by Mission 14, plus F13-18.  
**Standard:** Independent reproduction using synthetic fixtures and adversarial code-level inspection.

---

## 1. Summary of Claimed Fixes Verification

| Finding ID | Title / Vulnerability Description | Mission 13 Severity | Mission 14 Claim | Mission 15 Verified Status |
|---|---|---|---|---|
| **C-02 / R-H01** | Alternate media readers unguarded | CRITICAL | FIXED_PENDING_AUDIT | **FIXED_VERIFIED** |
| **C-03** | Unsafe routine suite / raw-media access | CRITICAL | FIXED_PENDING_AUDIT | **FIXED_VERIFIED** (Engineering Harness) |
| **F13-01** | Evaluation input loader reads/hashes media-suffixed sources; digest leaks | HIGH | FIXED_PENDING_AUDIT | **FIXED_VERIFIED** |
| **F13-02** | Public `run_from_manifest` reads/hashes sources before refusing REAL manifest | MEDIUM | FIXED_PENDING_AUDIT | **FIXED_VERIFIED** |
| **F13-03** | Suffix-only `media_guard`: symlinks, aliases, and unlisted suffixes bypass | HIGH | FIXED_PENDING_AUDIT | **FIXED_VERIFIED** |
| **F13-04** | Case-variant paths evade descriptive gate and output protection | HIGH | FIXED_PENDING_AUDIT | **FIXED_VERIFIED** |
| **F13-05** | Dashboard `/outputs/` and `/experiments/` serve files via `..` traversal | HIGH | FIXED_PENDING_AUDIT | **FIXED_VERIFIED** |
| **F13-06** | `scratch/` holds seven unguarded ffmpeg/wave scripts outside scan root | MEDIUM | FIXED_PENDING_AUDIT | **FIXED_VERIFIED** |
| **F13-07** | Guard denial swallowed by broad `except Exception` in data manifest/validator | MEDIUM | FIXED_PENDING_AUDIT | **FIXED_VERIFIED** |
| **F13-11** | Four stale classification entries; safe runner not reproducible | MEDIUM | FIXED_PENDING_AUDIT | **FIXED_VERIFIED** |
| **F13-12** | M-02 regression tests exist only in protected-access classified files | MEDIUM | FIXED_PENDING_AUDIT | **FIXED_VERIFIED** |
| **F13-13** | Opener tripwire is function-level, order-blind; allowlist hides F13-01 | MEDIUM | FIXED_PENDING_AUDIT | **FIXED_VERIFIED** |
| **F13-14** | `predict(source=path)` with no adjacent guard in qualitative figures script | LOW | FIXED_PENDING_AUDIT | **FIXED_VERIFIED** |
| **MR12-01** | Safe runner unexecuted after remediation | MEDIUM | FIXED_PENDING_AUDIT | **FIXED_VERIFIED** |
| **F13-18** | Discrepancy in modified tracked files count (22 vs 25) | LOW | RESOLVED_BY_EVIDENCE | **FIXED_VERIFIED** |

---

## 2. Detailed Finding-by-Finding Verification

---

### Finding 1: C-02 / R-H01 — Alternate Media Readers Unguarded
- **Original Vulnerability:** Mission 13 (§5) established that while Mission 11B guarded four specific media readers, other media entry points (e.g. `data/manifest.py`, `data/validator.py`, `experiments/layer_b_processor.py`, `demo/video_demo.py`, `annotation/media_inspector.py`, `audio/preprocessor.py`, `data/audio_extractor.py`, and research scripts) were unguarded, lacked `declared_media=True`, or could be bypassed with non-standard suffixes.
- **Mission 14 Implementation:** 
  1. `safety/media_guard.py` enforces location-first classification via `classify_resource`: any file under `data/raw/` is guarded regardless of extension (except plain-text metadata).
  2. Suffix allowlists expanded to 78 distinct audio/video/image extensions.
  3. Added `declared_media=True` at all low-level reader call sites (`vision/video.py`, `demo/video_demo.py`, `data/audio_extractor.py`, `annotation/media_inspector.py`, `audio/preprocessor.py`, `data/manifest.py`, `data/validator.py`, `experiments/layer_b_processor.py`, and research scripts).
- **Regression Test Evidence:** `tests/unit/test_security_media_boundary.py` (26 test functions, 55 test assertions) and `tests/unit/test_media_opener_coverage.py`.
- **Independent Reproduction:** Probed with synthetic files across all reader sites. Every decode/probe attempt without `AUTH-MEDIA-ACCESS.json` raises `MediaAccessAuthorizationError` before file descriptor allocation.
- **Bypass / Side-Effect Check:** No alternate reader bypass identified; legitimate synthetic test media in `/tmp` continues to pass without hindrance.
- **Verified Status:** `FIXED_VERIFIED`.

---

### Finding 2: C-03 — Unsafe Routine Suite / Raw-Media Access
- **Original Vulnerability:** Routine safe test execution was broken (exit 3) due to stale manifest hashes, preventing automated verification; Mission 12 had executed protected tests directly.
- **Mission 14 Implementation:** Restored `scripts/run_synthetic_tests.py` functionality by reclassifying and refreshing hashes of safe tests, moving protected Phase 12 tests to synthetic siblings (`test_phase12_governance_synthetic.py`, `test_phase12_official_replay_synthetic.py`), and keeping the 21 protected test files strictly excluded.
- **Regression Test Evidence:** Executed `scripts/run_synthetic_tests.py` twice during Mission 14 with 2,198 tests passing across 100 files, 0 blocked accesses, 0 violations.
- **Independent Reproduction:** Independently executed `scripts/run_synthetic_tests.py` in Mission 15. Exactly 2,198 tests passed across 100 files in 53.59s, with 0 errors, 0 failures, 0 blocked accesses, and 0 violations.
- **Bypass / Side-Effect Check:** Read-blocking harness remained fully armed throughout the execution. No protected checkpoint or raw media file was accessed. (Note: The historical execution incident from Mission 12 is addressed separately under F13-08).
- **Verified Status:** `FIXED_VERIFIED`.

---

### Finding 3: F13-01 — Evaluation Input Loader Reads and Hashes Media-Suffixed Sources; Digest Leaks
- **Original Vulnerability:** `src/railway_detection/evaluation/input_contracts.py` opened and hashed source files using `sha256_file` without calling `require_media_authorization`. If a hash mismatched, the computed digest was leaked in the error message.
- **Mission 14 Implementation:**
  1. Added `require_media_authorization(path, "HASH_RAW_MEDIA")` inside `sha256_file` and `_read_source_bytes_and_hash` before `os.open()`.
  2. Caught `MediaAccessAuthorizationError` in `load_evaluation_input_manifest` and raised `EvaluationInputError("SOURCE_MEDIA_ACCESS_DENIED", ...)` with a sanitised message containing zero digests.
  3. In `SOURCE_HASH_MISMATCH`, removed the computed digest from the exception detail string to prevent hash oracle leakage.
- **Regression Test Evidence:** `tests/unit/test_security_evaluation_input.py::test_loader_refuses_a_media_source_before_opening_or_hashing_it`, `test_refusal_is_by_location_and_never_leaks_a_digest`, `test_hash_mismatch_message_has_no_digest_at_all`.
- **Independent Reproduction:** Executed synthetic test cases creating manifest pointing to a synthetic media file under simulated repo structure. Verified refusal occurs with 0 bytes read and 0 bytes hashed; error message contains no digest.
- **Bypass / Side-Effect Check:** Plain-text metadata files under `data/raw` remain readable as JSON unless declared as media.
- **Verified Status:** `FIXED_VERIFIED`.

---

### Finding 4: F13-02 — Public `run_from_manifest` Reads and Hashes All Declared Sources Twice Before Refusing REAL Manifest
- **Original Vulnerability:** When `run_from_manifest(manifest_path=...)` was called with a REAL manifest without authorization, it invoked `load_evaluation_input_manifest(verify_sources=True)` twice before reaching `_require_official_context()`, causing unauthorized reads of all declared event sources.
- **Mission 14 Implementation:**
  1. `Phase12EvaluationRunner.run_from_manifest` immediately inspects `manifest_path` location using `_refuse_protected_manifest_location` (refusing evidence trees before reading).
  2. Calls `_refuse_real_manifest_header` which invokes `load_evaluation_input_manifest(manifest_path, verify_sources=False)` to check `evidence_classification` without opening or hashing any source files.
  3. In `_run_from_manifest_verified`, `_require_official_context` is enforced on the manifest header *before* `verify_sources=True` is ever called.
- **Regression Test Evidence:** `tests/unit/test_security_evaluation_input.py::test_explicit_real_request_is_refused_with_zero_reads`, `test_real_manifest_with_the_classification_argument_omitted_reads_no_source`, `test_caller_declaring_synthetic_cannot_relabel_a_real_manifest`.
- **Independent Reproduction:** Verified with synthetic manifests marked `real`. Refusal raises `EvaluationRefused` immediately with zero source file reads and zero hash computations.
- **Bypass / Side-Effect Check:** Valid synthetic manifests continue to load and verify sources normally.
- **Verified Status:** `FIXED_VERIFIED`.

---

### Finding 5: F13-03 — `media_guard` Suffix-Only Classification Bypassed by Symlink/Hardlink Aliases and Unlisted Suffixes
- **Original Vulnerability:** `media_guard.looks_like_media(path)` checked only `Path(path).suffix.lower() in MEDIA_SUFFIXES`. A symlink with an innocent name (`data.txt`) pointing to an MP4 video or an unlisted/extensionless file evaded the guard.
- **Mission 14 Implementation:**
  1. Introduced `classify_resource(path, declared_media=...)` which canonicalizes the path first (resolving symlinks) and determines zone based on filesystem identity.
  2. All files under `data/raw/` are classified as `REPO_RAW` regardless of extension (excluding verified plain-text metadata).
  3. External unknown suffixes default to `EXTERNAL_MEDIA_LIKE` (fail-closed).
- **Regression Test Evidence:** `tests/unit/test_security_media_boundary.py::test_any_name_under_data_raw_is_denied_not_only_known_suffixes`, `test_symlink_alias_with_a_non_media_name_to_raw_media_is_denied`.
- **Independent Reproduction:** Created symlinks in temporary directories pointing to media files. Probed with `.txt`, extensionless names, and `.xyz` extensions. All correctly classified as `guarded=True`.
- **Bypass / Side-Effect Check:** Verified that symlink chains and directory symlinks are recursively resolved and properly guarded.
- **Verified Status:** `FIXED_VERIFIED`.

---

### Finding 6: F13-04 — Case-Variant Paths Defeat Descriptive Gate, Protected-Output Check, and Related Guards
- **Original Vulnerability:** On macOS APFS filesystems, path comparisons using standard string equality or `Path.is_relative_to()` failed when paths used case variants (e.g. `DATA/RAW` vs `data/raw`), bypassing security checks.
- **Mission 14 Implementation:**
  1. Created `safety/path_identity.py` implementing `canonical_path`, `is_within`, and `is_same_location` using `os.path.samefile` on existing ancestors, with Unicode NFC normalization and casefolding fallback for non-existent reference trees.
  2. Applied identity-based checks across `media_guard.py`, `descriptive_exec_gate.py`, `evaluation_runner.py` (`_checked_output_dir`), `cache_only_engine.py`, `experiment_engine.py`, and `stage21_timing_pilot.py`.
- **Regression Test Evidence:** `tests/unit/test_security_path_identity.py` (27 tests), `tests/unit/test_security_media_boundary.py::test_case_variant_repository_path_gets_the_same_decision`.
- **Independent Reproduction:** Probed uppercase, mixed-case, and Unicode variants of repository paths against `is_within` and `media_guard.classify_resource`. All variants correctly resolve to identical filesystem identities and enforce containment.
- **Bypass / Side-Effect Check:** Synthetic test paths outside the repository on case-insensitive volumes remain distinguishable and do not collide with repo paths.
- **Verified Status:** `FIXED_VERIFIED`.

---

### Finding 7: F13-05 — Dashboard `/outputs/` and `/experiments/` Handlers Serve Any File Under Project Root via `..`
- **Original Vulnerability:** `src/railway_detection/demo/server.py` handled GET requests to `/outputs/` and `/experiments/` by direct concatenation without path traversal sanitization, allowing arbitrary repository file reads (e.g. `/outputs/../../data/governance/...`).
- **Mission 14 Implementation:**
  1. Rewrote path resolution in `demo/server.py` using `resolve_served_file()`, which delegates to `pid.resolve_untrusted_relative()`.
  2. Enforces strict root boundaries (`outputs/` and `experiments/vision/<run>/evaluation/`) and allowed suffix sets (`OUTPUT_SERVE_SUFFIXES`, `EXPERIMENT_SERVE_SUFFIXES`).
  3. Rejects parent directory traversal (`..`), backslashes, NUL bytes, control characters, and multiple percent-decoding rounds with generic HTTP 404.
  4. Hardened `translate_path` for static assets.
- **Regression Test Evidence:** `tests/unit/test_security_dashboard.py` (50 unit tests), plus real-socket HTTP probe script `docs/generated/phase5/mission14_tools/smoke_http_dashboard.py`.
- **Independent Reproduction:** Tested traversal strings (`..`, `..%2f`, `%252e%252e`, absolute paths, backslashes). All attempts fail closed with `PathIdentityError` or HTTP 404; zero files outside allowlisted roots are retrievable.
- **Bypass / Side-Effect Check:** Normal static web assets and valid video outputs continue to serve with byte-range support.
- **Verified Status:** `FIXED_VERIFIED`.

---

### Finding 8: F13-06 — `scratch/` Holds Seven Unguarded FFmpeg/Wave Scripts Outside Every Scan Root
- **Original Vulnerability:** Seven utility scripts in `scratch/` directly invoked `ffmpeg`/`ffprobe` via `subprocess` or `wave.open` without calling media access guards.
- **Mission 14 Implementation:**
  1. Added `media_guard` bootstrap and authorization checks (`require_media_command_authorization` and `require_media_authorization`) immediately preceding all 9 `subprocess` launch sites and 1 `wave.open` call across all seven scripts.
  2. Enforced protected output destination refusal.
- **Regression Test Evidence:** `tests/unit/test_security_scratch_scripts.py` (24 AST and execution tests).
- **Independent Reproduction:** Analyzed AST structures and inspected all seven scripts. Every subprocess and wave call is preceded by a guard on the exact target arguments.
- **Bypass / Side-Effect Check:** None of the scratch scripts were executed during Mission 14 or Mission 15; guards ensure any future invocation will fail closed without `AUTH-MEDIA-ACCESS.json`.
- **Verified Status:** `FIXED_VERIFIED`.

---

### Finding 9: F13-07 — Guard Denial Swallowed by Broad `except Exception` in Image Manifest / Validator
- **Original Vulnerability:** In `src/railway_detection/data/manifest.py` and `validator.py`, media guard calls were placed inside `try: ... except Exception:` blocks, causing authorization denials to be swallowed and logged as image corruption warnings.
- **Mission 14 Implementation:**
  1. Moved `require_media_authorization(path, 'MEDIA_PROBE', declared_media=True)` outside and before the `try` block in both files.
  2. Ensures `MediaAccessAuthorizationError` propagates immediately up the stack.
- **Regression Test Evidence:** `tests/unit/test_security_media_boundary.py::test_validator_and_manifest_refuse_before_any_image_reader`.
- **Independent Reproduction:** Simulated image validation against protected synthetic path. Exception propagates cleanly without being swallowed.
- **Bypass / Side-Effect Check:** Genuine format corruptions on authorized media still catch `Exception` as intended.
- **Verified Status:** `FIXED_VERIFIED`.

---

### Finding 10: F13-11 — Four Stale Classification Entries; Safe Runner Not Reproducible
- **Original Vulnerability:** `tests/test_access_classification.yaml` contained four entries whose SHA-256 hashes differed from files on disk, causing `scripts/run_synthetic_tests.py` to exit 3 (refused).
- **Mission 14 Implementation:**
  1. Re-classified `test_media_authorization.py` as `SYNTHETIC_ONLY` and `test_media_opener_coverage.py` as `METADATA_ONLY` with updated SHA-256 hashes.
  2. Retained `test_phase12_governance.py` and `test_phase12_official_replay.py` as `MODEL_CHECKPOINT_ACCESS` with updated SHA-256 hashes, keeping them excluded.
  3. Added synthetic sibling test files to restore coverage.
- **Regression Test Evidence:** Safe runner passed 2,198 tests.
- **Independent Reproduction:** Verified all 121 file hashes in `tests/test_access_classification.yaml` match disk exactly (`am.verify_manifest_against_tree` returned 0 problems). Safe runner executed cleanly.
- **Bypass / Side-Effect Check:** No protected test file was re-classified as safe.
- **Verified Status:** `FIXED_VERIFIED`.

---

### Finding 11: F13-12 — M-02 Regression Tests Exist Only in Files Classified as Protected-Access
- **Original Vulnerability:** Mission 12's M-02 regression tests were placed inside `test_phase12_governance.py` and `test_phase12_official_replay.py`. Because these files touch real checkpoints and were classified as protected, they were never run by the safe synthetic runner.
- **Mission 14 Implementation:**
  1. Extracted safe tests into two synthetic sibling files: `tests/unit/test_phase12_governance_synthetic.py` (74 tests) and `tests/unit/test_phase12_official_replay_synthetic.py` (87 tests).
  2. Created `tests/unit/test_security_evaluation_input.py` (20 tests) specifically targeting M-02 entry points.
  3. Classified all three files as `SYNTHETIC_ONLY` / `METADATA_ONLY`.
- **Regression Test Evidence:** Included in safe runner report; 181 safe tests executed and passed.
- **Independent Reproduction:** Confirmed these tests run under `scripts/run_synthetic_tests.py` and exercise all public entry points against permit forgery, context forgery, and unauthorized REAL manifests.
- **Bypass / Side-Effect Check:** The original protected files were kept intact and excluded.
- **Verified Status:** `FIXED_VERIFIED`.

---

### Finding 12: F13-13 — Opener Tripwire Is Function-Level, Order-Blind; Allowlist Hides F13-01
- **Original Vulnerability:** `test_media_opener_coverage.py` searched for guard strings anywhere in a function, meaning a guard placed *after* a reader would falsely pass; it did not detect `predict(source=path)`, missed module-level code, and allowlisted `input_contracts.py`.
- **Mission 14 Implementation:**
  1. Rewrote `test_media_opener_coverage.py` to check AST line offsets, requiring `guard_positions[0] <= first_reader`.
  2. Added regex for `.predict(source=path)`.
  3. Added module-level scope analysis and included `scratch/`.
  4. Removed `input_contracts.py` from `REVIEWED_METADATA_ONLY`.
  5. Added 4 self-tests demonstrating detection of synthetic late guards and unallowlisted openers.
- **Regression Test Evidence:** `test_media_opener_coverage.py` passed with 0 unguarded openers and all self-tests passing.
- **Independent Reproduction:** Verified that synthetic AST offenders with late guards or unallowlisted readers trigger test failures.
- **Bypass / Side-Effect Check:** Allowlist reasons are enforced to be specific (> 12 chars).
- **Verified Status:** `FIXED_VERIFIED`.

---

### Finding 13: F13-14 — `predict(source=path)` with No Adjacent Guard in Figure 14 Fallback Loop
- **Original Vulnerability:** In `research/scripts/generate_qualitative_figures.py`, a fallback loop called `model.predict(source=str(image_path))` without an adjacent guard call.
- **Mission 14 Implementation:** Added `require_media_authorization(image_path, "INFERENCE", declared_media=True)` immediately preceding the fallback predict call.
- **Regression Test Evidence:** `tests/unit/test_media_opener_coverage.py` static scan passes.
- **Independent Reproduction:** Inspected lines 250-265 of `generate_qualitative_figures.py`; verified guard call directly precedes the predict call.
- **Bypass / Side-Effect Check:** No other unshielded predict calls exist in research scripts.
- **Verified Status:** `FIXED_VERIFIED`.

---

### Finding 14: MR12-01 — Safe Runner Not Executed After Remediation
- **Original Vulnerability:** Mission 12 left the safe runner unexecuted because the classification manifest was stale.
- **Mission 14 Implementation:** Executed safe runner twice, producing 2,198 passed tests, 0 failures, 0 violations.
- **Regression Test Evidence:** Report `mission14_synthetic_test_report.json`.
- **Independent Reproduction:** Independently reproduced in Mission 15 (`/tmp/mission15_synthetic_test_report.json`): 2,198 passed, 0 failures, 0 blocked accesses, 0 violations.
- **Bypass / Side-Effect Check:** Harness operated strictly in read-blocking mode.
- **Verified Status:** `FIXED_VERIFIED`.

---

### Finding 15: F13-18 — Discrepancy in Modified Tracked Files Count (22 vs 25)
- **Original Context:** Mission 13 noted that Mission 12's baseline reported 22 modified tracked files, whereas 25 were observed at the end of Mission 12.
- **Mission 14 Resolution:** Reconciled from Mission 12's own snapshot artifacts (`/private/tmp/m12_status_before.txt` had 22 files at 10:11; during Mission 12, edits were made to `generate_qualitative_figures.py`, `generate_video_progression_figure.py`, and `data/manifest.py`, bringing the count from 22 to 25 before Mission 12 finished).
- **Independent Reproduction:** Verified file modifications and timestamps in git index and working tree. The 25 modified files have remained stable across Missions 13, 14, and 15.
- **Verified Status:** `FIXED_VERIFIED` (Resolved by evidence).

---

## 3. Crosswalk Conclusion

All 14 claimed remediations plus F13-18 are independently verified as genuinely fixed in the codebase and covered by robust, reproducible regression tests. Zero claimed fixes were found to be superficial or bypassable through audited code paths.
