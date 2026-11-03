# Mission 13 — WP13.3 Safe Test Runner and Classification Manifest Audit

**Date:** 2026-11-02. No manifest was edited or regenerated. No stale classification was bypassed by editing; the runner's refusal was reproduced and then left intact.

## 1. Runner refusal reproduced

Command (dry run, so nothing could execute even if the manifest had been trusted):

```
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_synthetic_tests.py --dry-run --report-path <scratchpad>/m13_synth_dryrun.json
```

Result: **exit 3, `MANIFEST_UNTRUSTED`**, four problems, no test selected or executed:

```
STALE: tests/unit/test_media_authorization.py changed since it was classified
STALE: tests/unit/test_media_opener_coverage.py changed since it was classified
STALE: tests/unit/test_phase12_governance.py changed since it was classified
STALE: tests/unit/test_phase12_official_replay.py changed since it was classified
```

This is correct fail-closed behavior and is reproducible. The full (non-dry) run was not attempted because the manifest is untrusted. The 21 protected-access files were not run.

## 2. Manifest facts (`tests/test_access_classification.yaml`, schema 2.0.0)

| Quantity | Value |
|---|---|
| Test files classified | 113 (113 on disk; 0 unclassified; 0 ghost entries) |
| SYNTHETIC_ONLY / METADATA_ONLY | 73 / 19 → **92 safe-eligible files** |
| MODEL_CHECKPOINT_ACCESS / PROCESSED_DATA_ACCESS / RAW_MEDIA_ACCESS | 14 / 3 / 4 → **21 excluded files** (not 21 *tests*) |
| Tests recorded as passed, 92 safe files | **1,801** |
| Tests recorded as passed / failed, all 113 files (at classification time) | 2,162 / 66 |
| Tests accepted for execution today | 0 (manifest rejected as a whole) |
| Tests actually executed by the runner | 0 |
| Guard events / blocked / protected-access attempts by the runner | 0 / 0 / 0 (never launched) |

## 3. Why the four entries are stale

All four files are untracked, so there is no git baseline to diff; the recorded SHA-256 simply no longer matches the file (`access_manifest.verify_manifest_against_tree`, STALE check). Mission 12 edited all four (mtimes 10:20–10:31 on 2026-11-02; manifest 07:30).

| File | Recorded class | Current inspection | Safe to run? |
|---|---|---|---|
| `test_media_authorization.py` | SYNTHETIC_ONLY, 71 passed | Uses a `FakeRepo` in `tmp_path` and monkeypatches `guard.REAL_REPO_ROOT`; only touch of the real tree is `.exists()` on the AUTH-MEDIA-ACCESS path. Now 72 tests. | Yes by static inspection; run under guard (below) |
| `test_media_opener_coverage.py` | SYNTHETIC_ONLY, 4 passed, `access_dirs: []` | Reads source text under `src/`, `scripts/` and — **new in Mission 12** — `research/`. Under the guard that is **24 METADATA reads in `research/` and `research/scripts/`**. | Yes (source text only); but see below |
| `test_phase12_governance.py` | **MODEL_CHECKPOINT_ACCESS**, 74 passed / **2 failed**, excluded | Calls `assess_official_phase12_readiness(REPO_ROOT)` (`:674, :964, :989`) which, via `execution_gate.py:869` → `frozen_config.verify_checkpoint_integrity` (`:360-420`), **opens and SHA-256-hashes the vision checkpoint, the Audio-V3 checkpoint and the prohibited Audio-V2 checkpoint**; also reads `results/experiment_registry.jsonl`. | **No — not run by this audit** |
| `test_phase12_official_replay.py` | **PROCESSED_DATA_ACCESS**, 87 passed / **1 failed**, excluded | Reads `configs/` and `results/experiment_registry.jsonl`; also loads the frozen config via the real-repo path. | **No — not run by this audit** |

### 3.1 Hash refresh alone would not make the manifest trustworthy

Under the guard, `test_media_opener_coverage.py` now performs 24 METADATA reads in `research/`. The manifest declares `access_dirs: []` and category SYNTHETIC_ONLY, and `run_synthetic_tests.verify_log` flags every METADATA read for a SYNTHETIC_ONLY entry as `UNDECLARED_METADATA_READ` (exit 4). The entry therefore needs *reclassification* to METADATA_ONLY with `research` directories declared — a regeneration by `scripts/classify_test_access.py`, which this audit was forbidden to run.

### 3.2 The M-02 security tests are outside the safe set

The only tests of the forged `_OfficialPermit` are `test_phase12_official_replay.py:647-651` and `test_phase12_governance.py:736-740`. Both files are classified as protected-access and excluded. Even after regeneration they will probably remain excluded because they call the real-repository readiness gate. The safe runner can therefore never exercise the M-02 regression tests (F13-12).

### 3.3 Mission 12 ran the excluded files directly

`MISSION_12_ADVERSARIAL_TEST_REPORT.md` lists `test_phase12_governance.py` and `test_phase12_official_replay.py` in a plain `pytest` invocation ("300 passed"), not through the safe runner or under the guard plugin. The manifest and the code path in §3 indicate that running them against the real repository hashes the three production checkpoints. Mission 12 and the manuscript state that no protected checkpoint was opened or hashed. This audit cannot confirm or refute that without running the tests (forbidden). **Status: NOT_VERIFIABLE — the researcher should review the Mission 12 session before relying on the claim (F13-08).** Note also the manifest records 3 failing tests in those two files at classification time, whereas Mission 12 reports all 300 passing; the difference is unexplained.

## 4. Runner validation logic — confirmed by reading `access_manifest.py` and `run_synthetic_tests.py`

| Requirement | Evidence |
|---|---|
| Stale classification rejected | reproduced (§1) |
| Missing classification rejected | `UNCLASSIFIED:` problem (`access_manifest.py:111`) |
| Ghost entry rejected | `GHOST_ENTRY:` (`:113`) |
| Changed file cannot keep old classification | SHA-256 per file, `STALE:` (`:125`) |
| Unclassified test cannot enter the safe set | `select_files` only returns manifest entries in `SAFE_CATEGORIES`, after verification |
| Protected-access tests excluded | `SAFE_CATEGORIES = {SYNTHETIC_ONLY, METADATA_ONLY}`; UNKNOWN never selected |
| Safe file with blocked attempts / unobservable child process rejected | `SAFE_BUT_BLOCKED`, child-process check (`:136-140`) |
| Post-run verification | `verify_log` requires armed+disarmed, zero blocked, metadata reads inside declared dirs |
| Report outside repo | `_outside_repo_or_reports` |

Limits (disclosed by the repository): the guard covers `open`, `io.open`, `os.open`, `os.scandir/listdir`, `subprocess` path arguments and `cv2.VideoCapture` only; its own media-suffix list (`access_guard_plugin.py:41-54`) is shorter than `media_guard`'s and has no image suffixes (the `data/raw/` path rule compensates inside the repository).

## 5. Targeted guarded runs performed by this audit

The runner refused, so no "full safe set" figure can be produced. To obtain *some* independent evidence I ran only files that the manifest classifies as safe **and** that are not stale (or, for the two media tests, that I inspected as source and found to use temporary trees only), through the same read-blocking plugin the runner uses, with a clean environment (`env -i`), no bytecode writes and no cache provider.

| Run | Files | Result | Guard log |
|---|---|---|---|
| A | `test_media_authorization.py`, `test_media_opener_coverage.py` | **76 passed** (72 + 4), 0 failed | 28 events, **0 blocked**; 24 METADATA reads, all `research/**` source files from `test_media_opener_coverage.py`; 2 exempt registry reads by `conftest.py` |
| B | `test_descriptive_exec_gate`, `test_cache_only_replay`, `test_phase5_review_tooling`, `test_mission10_second_review`, `test_phase11_2_stage21_promotion_gate`, `test_phase12_evaluation_runner`, `test_descriptive_only` | **262 passed**, 0 failed | 14 events, **0 blocked**; 10 `configs/` metadata reads, 2 exempt registry reads |

These are **not** a reproduction of the 1,802 figure and are not a substitute for the runner.

## 6. Reproducibility of "1,802 tests passed"

The manifest's recorded pass counts for the 92 safe files sum to **1,801**. Adding the one extra test now present in `test_media_authorization.py` (72 vs 71) gives 1,802, which is probably the origin of the number, but it is arithmetic over recorded counts, not an executed result. The runner cannot currently execute, so **1,802 is not independently reproducible and must not be reported as "verified"** (manuscript line 202). The older 1,902 figure is contradicted (Mission 11B CL-035) and was not reused.

## 7. Findings

| ID | Sev | Finding | Blocks closure |
|---|---|---|---|
| F13-11 | MEDIUM | Four stale entries; two (`opener_coverage`, plus the research/ scan) also need reclassification, not just a hash refresh. Safe runner not reproducible. | yes |
| F13-12 | MEDIUM | M-02 regression tests live only in protected-access-classified files; not in the safe set. | yes |
| F13-08 | HIGH | Mission 12 executed protected-access-classified files directly; its "no checkpoint hashed" statement is unverifiable and probably wrong. | yes (claim integrity) |

## 8. Disposition

**Runner design: fail-closed behavior VERIFIED. Runner execution: NOT REPRODUCIBLE** (correctly refusing). Mission 11B **C-03** is therefore **PARTIALLY_FIXED**.
