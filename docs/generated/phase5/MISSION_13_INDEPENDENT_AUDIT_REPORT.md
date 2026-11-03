# Mission 13 — Independent Phase 5 Security, Engineering and Reproducibility Closure Audit

**Auditor:** independent, read-only. **Date:** 2026-11-02. **Repository:** `/Users/sayemuddin/Desktop/Train_automation`. **Baseline:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`.
**Implementation authority:** none exercised. **Real-data execution authorized by this report:** **NO**.

Companion reports (same directory): `MISSION_13_M02_SECURITY_AUDIT.md`, `MISSION_13_MEDIA_READER_AUDIT.md`, `MISSION_13_SAFE_RUNNER_AUDIT.md`, `MISSION_13_GOVERNANCE_GATE_AUDIT.md`, `MISSION_13_MANUSCRIPT_CLAIM_REAUDIT.md`, `MISSION_13_REPRODUCIBILITY_AUDIT.md`, `MISSION_13_PRESERVATION_AUDIT.md`, `MISSION_13_FINAL_FINDING_REGISTER.json`, and the synthetic probes in `mission13_probes/`.

---

## 1. Executive summary

**Final disposition: `PHASE_5_ENGINEERING_RECOVERY_BLOCKED`**

Mission 12's headline fix is real. The Mission 11B M-02 exploit (a caller-built `_OfficialPermit` plus a matching manifest digest) no longer produces a REAL, "verified" result through any public API; I reproduced the rejection with synthetic probes rather than relying on Mission 12's tests. The four media readers Mission 11B named are guarded immediately before the reader call.

Phase 5 engineering recovery cannot be closed, because independent probing found paths on which protected data can still be read or an authorization gate skipped without authorization:

| # | Finding | Sev |
|---|---|---|
| F13-01 | The evaluation input loader opens and hashes any in-root file, including media suffixes, with no media guard, and returns the digest in an error message | HIGH |
| F13-03 | `media_guard` decides "is this media" from the suffix of the path it is given; symlink/rename aliases and unlisted suffixes pass | HIGH |
| F13-04 | On this case-insensitive volume a case-variant repo path skips the descriptive-evaluation gate and the protected-output check | HIGH |
| F13-05 | The dashboard's `/outputs/` and `/experiments/` routes serve any file under the project root via `..` | HIGH |
| F13-08 | Mission 12 ran protected-classified test files directly; its "no checkpoint was hashed" statement is unverifiable and probably wrong | HIGH |
| F13-17 | The security-critical code is untracked and the only backups are in volatile `/private/tmp` | HIGH |

Unresolved findings: **2 CRITICAL** (both roll-ups of Mission 11B findings now `PARTIALLY_FIXED`: C-02/R-H01, C-03) and **9 HIGH** (F13-01, -03, -04, -05, -08, -17; N-06; H-09/R-H05 partially fixed; H-01..H-05 not independently verifiable). Details: `MISSION_13_FINAL_FINDING_REGISTER.json` (34 entries).

This is an engineering verdict, not a research one. It does not authorize human annotation, Stage-2.1 promotion, real-data inference or replay, official evaluation, or publication of empirical claims.

---

## 2. Initial repository baseline

| Item | Value |
|---|---|
| Location | `/Users/sayemuddin/Desktop/Train_automation` |
| HEAD | `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` |
| Branch | `main` |
| Staged | 0 |
| Modified tracked | **25** (Mission 12 reported 22 at its baseline; difference not reconciled) |
| Untracked status entries | 379 (directory-collapsed) |
| Reports present | Mission 10 (8), 11 (3), 11B (5), 12 (8) in `docs/generated/phase5/` |
| Mission 12 manifest | `MISSION_12_ARTIFACT_MANIFEST.json`: disposition `…COMPLETE_PENDING_INDEPENDENT_AUDIT`, `governance_created:false`, `real_data_accessed:false`, `safe_runner: REFUSED_STALE_MANIFEST` — all expected files exist |
| Authorization records in repo | `data/governance/` holds only `leg_exec_authorization.json`; **no** AUTH-MEDIA-ACCESS, AUTH-DESCRIPTIVE-EVAL-EXEC, EVAL-AUTH, promotion receipt |

---

## 3. Mission 11B finding crosswalk

| 11B ID | 11B status | Sev | Mission 13 status | Where |
|---|---|---|---|---|
| M-02 | UNRESOLVED | MEDIUM | **FIXED_VERIFIED** (original exploit) | §4 |
| C-02 / R-H01 | PARTIALLY_FIXED | CRITICAL | **PARTIALLY_FIXED** | §5 |
| C-01 | FIXED_PENDING_EXTERNAL_AUDIT | CRITICAL | **FIXED_VERIFIED** within documented tamper-evident model; F13-10 added | §7 |
| C-03 | FIXED_AND_VERIFIED | CRITICAL | **PARTIALLY_FIXED** (fail-closed verified; not reproducible; F13-08/11/12) | §6 |
| H-01…H-05 | FIXED_AND_VERIFIED | HIGH | **NOT_VERIFIABLE** independently (code-reviewed, current tests pass; no adversarial probe written) | §7 |
| M-03 | REQUIRES_RESEARCHER_DECISION | MEDIUM | OPEN (researcher) | – |
| M-06 | UNRESOLVED | MEDIUM | PARTIALLY_FIXED | §9 |
| M-08 | UNRESOLVED | MEDIUM | PARTIALLY_FIXED | §8 |
| L-03 | UNRESOLVED | LOW | **FIXED_VERIFIED** | §8 |
| H-09 / R-H05 | PARTIALLY_FIXED | HIGH | PARTIALLY_FIXED | §8 |
| N-06 | UNRESOLVED | HIGH | OPEN | §10 |
| BKP-01 | UNRESOLVED | LOW | OPEN | §10 |

---

## 4. M-02 adversarial audit (detail: `MISSION_13_M02_SECURITY_AUDIT.md`)

Passed (synthetic): forged `_OfficialPermit`; forged `_VerifiedOfficialAuthorization`; matching digest; caller context of any shape; REAL via `run()` and via `run_from_manifest(evidence_classification=REAL)`; permit on synthetic data; marker cannot be set through the runner without the module-private token.

Failed or qualified:
- **F13-02 (MEDIUM):** a REAL *manifest* passed to public `run_from_manifest` with the classification kwarg omitted (or set to SYNTHETIC) is opened, hashed and JSON-parsed twice before it is refused. The refusal keys on the kwarg, not the manifest.
- **F13-10 (MEDIUM):** EVAL-AUTH has no expiry, revocation or status field. Mission 12's design note says expiry/revocation are rechecked; for EVAL-AUTH they are not (AUTH-MEDIA-ACCESS and AUTH-DESCRIPTIVE-EVAL-EXEC do have them).
- **F13-15 (LOW):** the authorization context is not bound to a runner instance, operation or time; `official_authorization_verified` is an unsigned bool that any code can construct; no downstream code reads it.
- Residual, accepted: same-process access to private names. That is the documented Python-level limit, not a defect.

---

## 5. Media-reader coverage audit (detail: `MISSION_13_MEDIA_READER_AUDIT.md`)

Verified guarded, immediately before the reader: `data/manifest.py:154`, `data/validator.py:193,203,210`, `generate_qualitative_figures.py:95,156,247,253`, `generate_video_progression_figure.py:89,134`, plus the pre-existing video, audio, ffmpeg/ffprobe and raw-hash sites.

Verified **unguarded or bypassable**: F13-01 (loader), F13-03 (suffix/alias), F13-05 (dashboard file serving), F13-06 (seven `scratch/` scripts, medium, git-ignored), plus F13-07 (guard denial swallowed by `except Exception` in `manifest.py`/`validator.py`), F13-13 (the Mission 12 static tripwire is order-blind and its allowlist hides F13-01), F13-14 (one predict call without an adjacent guard).

Environment-variable overrides: none exist; setting six candidate variables did not change the guard. Direct calls into `validator._check_image/_read_dimensions/_file_sha256` open nothing without authorization. **Coverage is not complete.**

---

## 6. Safe-runner and classification audit (detail: `MISSION_13_SAFE_RUNNER_AUDIT.md`)

| Quantity | Value |
|---|---|
| Files in manifest | 113 (73 SYNTHETIC_ONLY, 19 METADATA_ONLY = 92 safe; 14 + 3 + 4 = 21 excluded **files**) |
| Tests recorded passed in the 92 safe files | 1,801 |
| Accepted by the runner | 0 |
| Rejected | whole manifest (exit 3, `MANIFEST_UNTRUSTED`) |
| Executed by the runner | 0 |
| Guard events / blocked / protected-access attempts by the runner | 0 / 0 / 0 |
| Reproducible | refusal: yes; execution: **no** |

The four stale files are untracked and edited by Mission 12. Two of them (`test_phase12_governance.py`, `test_phase12_official_replay.py`) are classified MODEL_CHECKPOINT_ACCESS / PROCESSED_DATA_ACCESS and are excluded; the code path they call hashes the three production checkpoints (F13-08). `test_media_opener_coverage.py` now reads 24 `research/` source files, so a mere hash refresh would still fail the runner's post-run check (F13-11). The M-02 regression tests live only in the two excluded files (F13-12).

I did not run the two protected-classified files. After static inspection I ran the two media tests (76 passed) and seven current, safe-classified gate test files (262 passed) through the read-blocking guard plugin: 0 blocked, metadata reads only in declared directories (and `research/` sources for the opener-coverage test). These runs do **not** reproduce "1,802" and are not a substitute for the runner.

---

## 7. Promotion and descriptive authorization audit (detail: `MISSION_13_GOVERNANCE_GATE_AUDIT.md`)

- Receipt checks reject: bad hash, wrong review-record hash, wrong bound input, wrong producer, not-READY verdict, future date. A hand-computed receipt passes (documented tamper-evident-only design); there is no expiry or revocation (F13-10).
- Allowlist, non-allowlisted reviewer and same-reviewer second review: refused in code (read; not independently attacked).
- Descriptive authorization is evaluated before cache path resolution and before replay — **but** the gate returns without checking whenever `repo_root.resolve()` differs from the real root as a string; a case-variant spelling of this repository defeats it (F13-04).
- The official readiness gate always hashes the three production checkpoints, authorization or not (F13-09).
- None of RD-043, RD-045, DEC-B05 is adopted; the reviewer appointment is not established; no authorization or receipt exists.

---

## 8. Manuscript claim re-audit (detail: `MISSION_13_MANUSCRIPT_CLAIM_REAUDIT.md`)

All 36 Mission 11B claims were rechecked. Framing is now accurate: methodology/specification, results pending, RD-043/DEC-B05/RD-045 shown as proposed/pending, no invented results, affordability and fatality statistics removed, macOS and tool versions correct. Remaining inaccuracies (**F13-16**): modified-file count (22 vs 25); "1,802 tests passed … verified"; "21 tests" (it is 21 files); wrong receipt path (`data/ground_truth/…` vs `data/governance/…`); an audio class list the repository does not support (the classifier is binary horn/non-horn); a limitation that claims "valuable empirical evidence"; an unchecked 120.8 s exposure; and the "no checkpoint hashed" sentence. Citations: [1]–[3] bibliographic details present but unverified; [4]–[9] unverified; no reference list.

---

## 9. Reproducibility audit (detail: `MISSION_13_REPRODUCIBILITY_AUDIT.md`)

Versions re-observed: Python 3.11.15, torch 2.13.0, ultralytics 8.4.121 (importable), ruff 0.16.3, pytest 9.1.1, macOS 26.6.2 (25G83), Darwin 25.6.0 arm64. Decision-policy hash verified. Mission 12's "frozen configuration SHA-256" is the raw-file hash, whereas the gates bind the canonical hash (`999a7970…`). Code reproducibility is not demonstrated (untracked implementation, runner refusal); data and model reproducibility are not demonstrated and were not attempted.

---

## 10. Backup and preservation audit (detail: `MISSION_13_PRESERVATION_AUDIT.md`)

No Git write, staging, restore, clean or overwrite occurred during this audit; the porcelain listing was identical before and after each probe (final check in §14). Mission 12's backup report is accurate as far as it goes: 64 files, none newer than 07:32, none created by Mission 12. But the files Mission 12 changed (`media_guard.py`, `evaluation_runner.py`, `manifest.py`, `validator.py`, two research scripts, four tests) have no pre-edit backup, the security-critical packages are untracked, and the backup directory is in `/private/tmp`. **F13-17 (HIGH).**

---

## 11. Test evidence

| What | Result |
|---|---|
| Safe runner `--dry-run` | refused, exit 3, 4 STALE |
| Media guard + tripwire tests under read-blocking guard | 76 passed, 0 blocked |
| Seven gate/engine test files under read-blocking guard | 262 passed, 0 blocked |
| Synthetic probes (`mission13_probes/`) | M-02 matrix, media-guard matrix, receipt matrix, case-variant gate, case-variant output dir, dashboard traversal — results in the work-package reports |
| Not run, deliberately | the four stale files' protected-classified pair; the 21 protected-access files; the full suite; anything touching media, checkpoints, caches or processed data |

---

## 12. Residual risks

1. Protected media readable without authorization via F13-01, F13-03, F13-05, and unguarded `scratch/` scripts.
2. Descriptive-evaluation and output-protection gates skippable by path-case variation on this machine.
3. Possible past hashing of production checkpoints by Mission 12 (unverified either way).
4. No expiry/revocation for EVAL-AUTH or the promotion receipt; governance artifacts are tamper-evident only; there is no signature infrastructure.
5. All security-critical code untracked; backups volatile.
6. Python-level guards are not OS isolation; hard links and native/shell reads remain outside the guard.
7. RD-043, RD-045, DEC-B05 and reviewer appointment remain researcher decisions; no approvals exist.

---

## 13. Final disposition

**`PHASE_5_ENGINEERING_RECOVERY_BLOCKED`** — chosen under rule C because protected data can still be read, and an authorization gate skipped, without authorization (F13-01, F13-03, F13-04, F13-05), and because preservation is not verified (F13-17). It is not chosen because M-02 regressed: it did not.

Distinctions this report relies on: engineering remediation (Mission 12) ≠ independent verification (this audit) ≠ researcher approval ≠ execution authorization ≠ real-data execution; synthetic test success ≠ real-data evaluation; proposed protocols ≠ adopted protocols; Python-level guards ≠ OS-level isolation; code-level implementation ≠ an empirically evaluated system.

---

## 14. Exact next actions (each needs a separate implementation instruction; none was performed here)

1. **Researcher:** review the Mission 12 session for whether `test_phase12_governance.py` / `test_phase12_official_replay.py` ran against the real repository and hashed checkpoints (F13-08); correct the "no checkpoint hashed" claim accordingly.
2. **Fix F13-01 / F13-02:** apply the media guard (suffix- and location-based) in the evaluation input loader; decide REAL vs SYNTHETIC from the manifest header before opening any source; stop returning digests of unverified sources.
3. **Fix F13-03:** make `media_guard` decide by resolved location (anything under `data/raw`/the repository) rather than by suffix of the given name; widen the suffix list as defense in depth.
4. **Fix F13-04:** replace string equality of resolved paths with a real identity comparison (`os.path.samefile`/case-normalized real path) in the descriptive gate, protected-output check, and `experiment_engine`/`stage21_timing_pilot`.
5. **Fix F13-05:** contain and guard the dashboard file routes.
6. **Quarantine or guard `scratch/` (F13-06)**; let guard denials propagate in `manifest.py`/`validator.py` (F13-07); strengthen the opener tripwire (F13-13) and add an adjacent guard at `generate_qualitative_figures.py:139` (F13-14).
7. **Researcher decisions:** whether checkpoint hashing needs authorization (F13-09); whether EVAL-AUTH/receipt gain expiry and revocation (F13-10); RD-043, RD-045, DEC-B05; bibliography and authors.
8. **Safe runner:** move the synthetic M-02 tests to a safe-classified file (F13-12), then regenerate the classification manifest through the researcher-approved procedure and obtain a runner-executed count (F13-11).
9. **Preservation:** researcher-directed durable preservation of `safety/`, `annotation/`, `evaluation/` and the Mission 12 changes (F13-17, N-06, BKP-01).
10. **Manuscript/provenance:** correct the items in F13-16 after the numbers above are re-established.
11. Re-run an independent audit after items 2–6 and 8.

---

## Self-check (end of audit)

- No source, test, configuration, manifest, classification, manuscript or governance file was modified or deleted.
- No authorization, receipt, review, adjudication or annotation artifact was created; RD-001–RD-055 were treated as directional.
- No raw media, checkpoint, processed dataset, production cache or real annotation was opened, listed, decoded or hashed. Only fake (non-existent) repository paths, temporary synthetic files and small configuration/documentation files (policy, frozen config, protocol document) were used.
- No real inference, replay, evaluation or timing pilot ran. No Git write command was executed; nothing is staged.
- New files: the reports above and `mission13_probes/` under `docs/generated/phase5/`; temporary files in the session scratchpad.
- Not completed: independent adversarial probes for duplicate-reviewer and timestamp controls; execution of the two protected-classified test files and of the full safe set (refused/forbidden); a reader-level (real-media) demonstration of F13-03 and F13-04 (would require touching protected data); external literature verification (out of scope).
