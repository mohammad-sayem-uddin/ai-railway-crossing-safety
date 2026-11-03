# Mission 14 — Targeted Phase 5 Security Recovery: Report

**Date:** 2026-11-02 · **Repository:** `/Users/sayemuddin/Desktop/Train_automation` · **Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (unchanged)
**Implementer:** Claude Sonnet 5.5 · **Research execution authorization:** NONE · **Independent closure claimed:** NO

## 1. Executive summary

**Final disposition: `PARTIALLY_REMEDIATED`.**

Every Mission 13 finding that was a code or test defect inside the brief's scope was fixed and covered by synthetic tests that fail (or cannot import) on the old code: the media boundary (F13-03, C-02), the evaluation input loader (F13-01, F13-02), case/alias/path identity (F13-04), the dashboard (F13-05), the seven `scratch/` FFmpeg scripts (F13-06), swallowed guard denials (F13-07), the stale classification and the missing safe-set M-02 tests (F13-11, F13-12), and the order-blind tripwire (F13-13, F13-14). The safe runner is restored **without weakening it** and **PASSED twice: 2,198 tests, 100 files, 0 blocked accesses, 0 violations.** No critical finding remains open.

The disposition is B rather than A because:

1. **F13-08 is an unresolved incident.** Strong evidence (pytest bytecode stamped 10:36:45; test counts summing exactly to Mission 12's "300 passed") shows Mission 12 ran the two protected-classified test files directly. By code path that run probably hashed the production checkpoints, but this is **not established** and was not converted into a confirmed violation. Human review is required.
2. Git-preservation items (F13-17, N-06, BKP-01) cannot be fixed under this mission's no-Git-write rule.
3. Policy/design items need the researcher (F13-09 checkpoint-hashing policy, F13-10 EVAL-AUTH/receipt expiry-revocation, F13-15 context binding, M-03, M-08), and H-01…H-05 / manuscript corrections (F13-16, H-09) are not independently verified.

**Mission 15 must independently audit.** Real-data execution is **not authorized.**

## 2. Mission 13 finding crosswalk

Register: `MISSION_14_FINDING_REGISTER.json` (38 entries: the 34 from Mission 13 + 4 new). Counts: **14 fixed pending Mission 15 audit**, 1 resolved by evidence (F13-18), 3 unchanged-verified by Mission 13, 4 documented limits, 3 partially fixed, 5 open for researcher decision, 5 open/out of scope, 2 not verifiable by the author, **1 unresolved incident (F13-08)**.

| Finding | Sev | Mission 14 status |
|---|---|---|
| C-02 / R-H01 media readers | CRIT | fixed, pending audit |
| C-03 unsafe suite / runner | CRIT | fixed, pending audit (runner PASSED) |
| F13-01 loader hashes media, leaks digest | HIGH | fixed, pending audit |
| F13-02 REAL manifest read/hashed twice | MED | fixed, pending audit |
| F13-03 suffix-only guard | HIGH | fixed, pending audit |
| F13-04 case-variant paths | HIGH | fixed, pending audit |
| F13-05 dashboard traversal | HIGH | fixed, pending audit |
| F13-06 scratch FFmpeg scripts | MED | fixed, pending audit |
| F13-07 swallowed denials | MED | fixed, pending audit |
| F13-08 Mission 12 execution | HIGH | **UNRESOLVED INCIDENT** |
| F13-11 / F13-12 classification / M-02 tests | MED | fixed, pending audit |
| F13-13 / F13-14 tripwire / adjacent guard | MED/LOW | fixed, pending audit |
| F13-18 22→25 | LOW | resolved by evidence |
| F13-09, F13-10, F13-15, M-03, M-08 | MED/LOW | open — researcher decision |
| F13-16, H-09, M-06 | MED/HIGH | partially fixed (notices only) |
| F13-17, N-06, BKP-01 | HIGH/LOW | open — Git preservation not permitted here |
| H-01…H-05 | HIGH | not independently verified; regression path confirmed |

## 3. Initial repository baseline

HEAD `d4db94d…`, branch `main`, staged 0, modified tracked 25, untracked entries 379. Details, backups inspected, and the corrections to the brief's finding labels are in `MISSION_14_INITIAL_BASELINE.md`. **Final:** HEAD unchanged, staged 0, tracked-modified set **identical** (25), untracked entries 388 (+9 new test files; other new files fall inside already-untracked directories).

## 4. Files modified (40 created or changed)

See the matrix in §16 and `MISSION_14_ARTIFACT_MANIFEST.json` (SHA-256 of each). Untouched by design: `scripts/run_synthetic_tests.py`, `scripts/classify_test_access.py`, `safety/access_manifest.py`, `safety/access_guard_plugin.py`, and the two original Mission 12 protected test files.

## 5. Media-access boundary

Location-first classification (`classify_resource`) replaces suffix-first: anything under `data/raw` is guarded whatever its name (plain-text metadata excepted unless a reader declares media); aliases are classified by their resolved target; media suffixes widened to 78 and unrecognised external suffixes treated as possible media; synthetic only by real location in a fixed list of OS temp roots (never `TMPDIR`); unresolvable paths refused; `declared_media=True` at decode sites; `require_media_command_authorization` for ffmpeg/ffprobe; protected-output refusal. Full design, inventory and limits: `MISSION_14_MEDIA_BOUNDARY_DESIGN.md`.

## 6. Evaluation loader (F13-01, F13-02)

Guard runs before any open or hash at the lowest level; digest-free errors; a REAL request/manifest is refused by argument, location and header checks with **zero event-source reads** (Mission 13: six); private core demands the verified context before reading sources. `MISSION_14_EVALUATION_INPUT_SECURITY.md`.

## 7. Path and case canonicalisation (F13-03, F13-04)

`safety/path_identity.py`; identity (`samefile`) comparison used by the media guard, descriptive gate, protected-output checks, cache paths, manifest input, dashboard and pilot checkout test. `MISSION_14_PATH_CANONICALIZATION.md`.

## 8. Dashboard (F13-05)

Allowlisted `outputs/` and `experiments/vision/<run>/evaluation/` roots, suffix allowlists, full decoding, symlink- and case-aware containment, generic 404, static `translate_path`, `/api/process` guard. 50 tests + real-socket smoke test. `MISSION_14_DASHBOARD_SECURITY.md`.

## 9. Scratch FFmpeg scripts (F13-06)

Seven scripts, nine launch sites and one `wave.open` guarded immediately before use; none executed; none deleted. Observation: `run_phase2_verification.py` also writes review records (flagged, not changed). `MISSION_14_SCRATCH_MEDIA_SCRIPT_AUDIT.md`.

## 10. Mission 12 execution provenance (F13-08)

Levels: ran the files unguarded — **strong evidence (2)**; checkpoints opened/hashed — **possible, probable by code path, not established (3)**; Mission 12's transcript is **not available** on this machine. Incident recorded as **unresolved**; human review recommended; a correction notice is provided (historical reports untouched). Mission 14 did not execute those files and did not stat or hash any checkpoint. `MISSION_14_MISSION12_EXECUTION_PROVENANCE.md`.

## 11. Test classification changes

Four stale entries recovered: two media tests re-classified by guarded runs (`SYNTHETIC_ONLY`, `METADATA_ONLY`); the two protected Phase 12 files recorded `MODEL_CHECKPOINT_ACCESS` by static review (not run) and left untouched; two generated synthetic siblings (74 and 87 tests, 0 blocked) restore their safe tests to the safe set. Manifest 113 → 121 files, safe 92 → 100, protected files 21 → 21. `MISSION_14_TEST_CLASSIFICATION_RECOVERY.md`.

## 12. Safe-runner execution report

`scripts/run_synthetic_tests.py --report-path /tmp/mission14_synthetic_test_report.json` → **PASSED**, exit 0, **2,198 passed / 0 failed / 0 skipped**, 100 files executed (78 `SYNTHETIC_ONLY`, 22 `METADATA_ONLY`), guard events 2,601, **blocked 0**, violations none; 21 protected files not run; identical on a second execution. Archived: `mission14_evidence/mission14_synthetic_test_report.json`. Not run: the full suite, the 21 protected-access files, `test_dashboard_server.py`. The 1,801/1,802/21 arithmetic is explained in the classification report §6.

## 13. M-02 regression coverage

Forged `_OfficialPermit` (matching digest, REAL and SYNTHETIC labels), forged contexts (random, correct private token, string, wrong manifest), REAL via `run()` / `run_from_manifest()`, REAL manifest with omitted keyword, protected manifest locations — all refused with zero source reads, zero producer calls, zero cache-engine constructions, zero engaged media checks. Now in safe-classified files. `MISSION_14_SECURITY_REGRESSION_TESTS.md`.

## 14. Governance regression coverage

Receipt matrix (hash, review-record hash, bound inputs, producer, verdict, shapes, future date), EVAL-AUTH schema correction preserved (**no expiry/revocation invented**), AUTH-MEDIA/descriptive schemas assert expiry/revocation, allowlist loader, and name-pinned references to the existing duplicate-reviewer / non-allowlisted / missing-second-review / scope / timestamp tests. RD-043 is treated as proposed throughout. Receipt and EVAL-AUTH gaps (F13-10) are pinned as documented gaps.

## 15. Documentation corrections

Notices C1–C10 and manuscript replacement values: `MISSION_14_DOCUMENTATION_RECONCILIATION.md`. No historical report or manuscript text was edited.

## 16. Backup / preservation matrix

New in-repo backup set `docs/generated/phase5/mission14_pre_edit_backup/` (33 files, `SHA256SUMS.txt`) was copied **before** each edit. No existing backup was overwritten, restored or moved; no file deleted; Mission 13 probe artifacts preserved. **Exceptions (stated, not reconstructed): `execution_gate.py` (one catalogue entry) and `layer_b_processor.py` (one line) were edited without a backup.** Git status columns: `??` untracked, `M` tracked-modified, `!!` git-ignored, `NEW` created by Mission 14.

| File | Git before | Git final | Pre-edit backup | Purpose |
|---|---|---|---|---|
| `src/railway_detection/safety/path_identity.py` | NEW | ?? | n/a (new) | NEW shared path canonicalisation / identity containment / untrusted-pa |
| `src/railway_detection/safety/media_guard.py` | ?? | ?? | yes | location-first resource classification, widened suffix lists, declared |
| `src/railway_detection/evaluation/input_contracts.py` | ?? | ?? | yes | loader guard before open/hash, digest-free errors, identity containmen |
| `src/railway_detection/evaluation/evaluation_runner.py` | ?? | ?? | yes | public-API location+header refusal, private-core context check before  |
| `src/railway_detection/evaluation/execution_gate.py` | ?? | ?? | **NO** | one BLOCKER_CATALOGUE entry for SOURCE_MEDIA_ACCESS_DENIED |
| `src/railway_detection/evaluation/descriptive_exec_gate.py` | ?? | ?? | yes | gate by identity: real checkout in any spelling / containing / contain |
| `src/railway_detection/evaluation/cache_only_engine.py` | ?? | ?? | yes | cache path containment by identity |
| `src/railway_detection/evaluation/experiment_engine.py` | ?? | ?? | yes | official-tree output refusal by identity |
| `src/railway_detection/annotation/stage21_timing_pilot.py` | ?? | ?? | yes | checkout identity helper for two sites |
| `src/railway_detection/annotation/media_inspector.py` | ?? | ?? | yes | declared_media at probe / frame extraction |
| `src/railway_detection/data/audio_extractor.py` | ?? | ?? | yes | declared_media |
| `src/railway_detection/vision/video.py` |  M | M | yes | declared_media |
| `src/railway_detection/audio/preprocessor.py` |  M | M | yes | declared_media |
| `src/railway_detection/data/manifest.py` |  M | M | yes | guard outside try; denial propagates; declared_media (F13-07) |
| `src/railway_detection/data/validator.py` |  M | M | yes | guard outside try; denial propagates; declared_media (F13-07) |
| `src/railway_detection/demo/server.py` |  M | M | yes | allowlisted serving roots, canonical containment, static translate_pat |
| `src/railway_detection/demo/video_demo.py` |  M | M | yes | declared_media |
| `src/railway_detection/experiments/layer_b_processor.py` | ?? | ?? | **NO** | declared_media (one-line change) |
| `research/scripts/generate_qualitative_figures.py` |  M | M | yes | declared_media; adjacent guard before fallback predict (F13-14) |
| `research/scripts/generate_video_progression_figure.py` |  M | M | yes | declared_media |
| `scratch/analyze_train_events.py` |    | !! | yes | guard bootstrap + guard immediately before each ffmpeg launch / wave.o |
| `scratch/analyze_forensic_results.py` |    | !! | yes | guard bootstrap + guard immediately before each ffmpeg launch / wave.o |
| `scratch/analyze_audio.py` |    | !! | yes | guard bootstrap + guard immediately before each ffmpeg launch / wave.o |
| `scratch/extract_frames.py` |    | !! | yes | guard bootstrap + guard immediately before each ffmpeg launch / wave.o |
| `scratch/forensic_event_auditor.py` |    | !! | yes | guard bootstrap + guard immediately before each ffmpeg launch / wave.o |
| `scratch/measure_ground_truth_v7.py` |    | !! | yes | guard bootstrap + guard immediately before each ffmpeg launch / wave.o |
| `scratch/run_phase2_verification.py` |    | !! | yes | guard bootstrap + guard immediately before each ffmpeg launch / wave.o |
| `tests/unit/security_support.py` | NEW | ?? | n/a (new) | NEW shared synthetic fixtures |
| `tests/unit/test_security_media_boundary.py` | NEW | ?? | n/a (new) | NEW 55 tests |
| `tests/unit/test_security_evaluation_input.py` | NEW | ?? | n/a (new) | NEW 24 tests |
| `tests/unit/test_security_path_identity.py` | NEW | ?? | n/a (new) | NEW 52 tests |
| `tests/unit/test_security_dashboard.py` | NEW | ?? | n/a (new) | NEW 50 tests |
| `tests/unit/test_security_scratch_scripts.py` | NEW | ?? | n/a (new) | NEW 24 tests |
| `tests/unit/test_security_governance_regressions.py` | NEW | ?? | n/a (new) | NEW 25 tests |
| `tests/unit/test_phase12_governance_synthetic.py` | NEW | ?? | n/a (new) | NEW generated synthetic sibling (74 tests) |
| `tests/unit/test_phase12_official_replay_synthetic.py` | NEW | ?? | n/a (new) | NEW generated synthetic sibling (87 tests) |
| `tests/unit/test_media_opener_coverage.py` | ?? | ?? | yes | tripwire strengthened (order-aware, predict(source=path), full-path ff |
| `tests/test_access_classification.yaml` | ?? | ?? | yes | classification recovered: 113->121 files, safe 92->100, amendments rec |
| `docs/generated/phase5/mission14_tools/classify_selected.py` | NEW | ?? | n/a (new) | NEW incremental classification driver |
| `docs/generated/phase5/mission14_tools/smoke_http_dashboard.py` | NEW | ?? | n/a (new) | NEW real-socket dashboard smoke test (synthetic tree) |

## 17. Residual risks

1. **F13-08 incident unresolved** (possible read-only checkpoint hashing by Mission 12).
2. Security-critical packages still untracked; older backups in volatile `/private/tmp` (F13-17, N-06, BKP-01). Mission 14's in-repo backups cover only the files it edited.
3. Checkpoint reads have no authorization control; the readiness gate hashes checkpoints whether or not EVAL-AUTH exists (F13-09).
4. EVAL-AUTH and the promotion receipt cannot expire or be revoked and are tamper-evident only; the official-authorization flag is unsigned (F13-10, F13-15).
5. Python-level guards only: hard links, copies placed in temp by other means, TOCTOU, native/shell reads, no OS isolation. Text-suffixed files under `data/raw` are metadata unless a reader declares media.
6. Case-variant tests are skipped on a case-sensitive filesystem; no test exercised a real engine, cache or media file (prohibited).
7. The 21 protected files and the full suite were not run; `scratch/` is git-ignored; ~2,000 duplicated test lines (originals + siblings).
8. H-01…H-05 and the manuscript corrections are not independently verified.

## 18. Final disposition

`PARTIALLY_REMEDIATED`. In-scope critical and high *defects* are fixed and tested; the disposition cannot be A while an incident is unresolved and preservation is open. No bypass known to Mission 14 remains in the audited scope, but Mission 14 is the implementer: **that is a claim for Mission 15 to test, not a closure.**

## 19. Recommendations for Mission 15

1. Re-run the Mission 13 probes (`mission13_probes/`) and the Mission 14 before/after outputs; try to break `classify_resource`, `require_media_command_authorization`, `resolve_untrusted_relative` and `_touches_real_repository` with new synthetic cases (Unicode normalisation, firmlink spellings, dotted components, very long paths, concurrent swaps).
2. Re-verify the opener tripwire's blind spots (aliased imports such as `from cv2 import VideoCapture`, `getattr`, `os.open` raw reads, `io.open`).
3. Audit the split of the two Phase 12 test files (diff sibling vs original must show only the listed removals/addition) and the manifest amendments.
4. Independently probe H-01…H-05 (duplicate-reviewer, timestamp, allowlist paths) rather than relying on the referenced tests.
5. Review the F13-08 provenance reasoning; do **not** run the two protected files or hash checkpoints to "check".
6. Reproduce the safe-runner result; confirm the runner still rejects stale / unclassified / ghost / protected inputs.
7. Verify the dashboard over a real socket with a proxy that does not normalise `..`.
8. Check that no pycache or other artifact was left by Mission 14 beyond the files in the manifest.

## Explicit statements

* **No real media accessed.** All probes and tests used fake repository paths and temporary synthetic files.
* **No checkpoints accessed by Mission 14.** None opened, hashed, listed or `stat`-ed. (Mission 12 may have — F13-08.)
* **No protected processed data and no production caches accessed.**
* **No real inference, replay, training or evaluation.**
* **No authorizations, promotion receipts, human-review or adjudication artifacts created.** `data/governance/` and `data/ground_truth/` were not written.
* **No Git staging, commit, push, reset, clean, restore or checkout.**
* Qualification: these are statements about Mission 14's own actions as established from its command history and by diffing the Git status before and after; they are not OS-level audit evidence.
