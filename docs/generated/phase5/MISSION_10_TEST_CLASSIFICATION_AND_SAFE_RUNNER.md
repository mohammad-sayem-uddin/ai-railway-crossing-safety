# Mission 10 — Test Classification and Safe Runner (WP10.3)

> Written for: the researcher and the next auditor.

## Why the old classification was rejected
One boilerplate sentence per file, hand-written, unvalidated; "97 SYNTHETIC_ONLY" included a test that hashes
real source media and 13 files that read checkpoints/results. The old runner trusted that file without checking it.

## Method (reproducible)
`python scripts/classify_test_access.py --work-dir <dir outside repo>` runs **each of the 113 test files alone,
in its own interpreter**, under `railway_detection.safety.access_guard_plugin`, which *raises* on any Python-level
read of raw media, model weights, processed data/results, or write into the repository, logging every attempt
(JSONL, outside the repo). The operation-boundary media guard reports into the same log, so an attempt stopped there
is still counted. A static AST scan adds protected-path literals and child-process calls. Entries carry a
file SHA-256, test-specific reason, access paths/dirs, blocked-attempt counts and test outcome counts.

Categories: `SYNTHETIC_ONLY`, `METADATA_ONLY`, `MODEL_CHECKPOINT_ACCESS`, `PROCESSED_DATA_ACCESS`,
`RAW_MEDIA_ACCESS`, `UNKNOWN` (unsafe). Precedence RAW > CHECKPOINT > PROCESSED > METADATA > SYNTHETIC.

## Result (113 files)
| Category | Files |
|---|---|
| SYNTHETIC_ONLY | 73 |
| METADATA_ONLY | 19 |
| MODEL_CHECKPOINT_ACCESS | 14 |
| PROCESSED_DATA_ACCESS | 3 |
| RAW_MEDIA_ACCESS | 4 (`test_audio_leakage_and_preprocessing`, `test_exploratory_subset_authorization_gate`, `test_phase4_integration_preflight`, `test_real_dataset_inventory`) |
| UNKNOWN | 0 |

Safe set = 92. One file (`test_access_classification_tools.py`) spawns child pytest processes; it is allowed only
through a reviewed `GUARDED_SPAWNERS` entry and the classifier requires it to name the guard plugin.

## Safe runner (`scripts/run_synthetic_tests.py`)
Fail-closed: (1) manifest must match the tree exactly (no unclassified file, no ghost, no stale hash, valid
category, consistent flag, no unreviewed child-process spawner); (2) only `SYNTHETIC_ONLY`/`METADATA_ONLY` can be
requested; (3) one pytest process under the guard with the log outside the repo; (4) post-run verification: guard
armed and disarmed, zero blocked events, every metadata read inside a directory the manifest declared for that
file (a SYNTHETIC_ONLY file may read none) — otherwise exit 4 `CLASSIFICATION_VIOLATION`; (5) JSON report outside
the repo. Exit codes 0/1/2/3/4. Report limitations are embedded.

Observed run: 92 files, **1,802 passed**, 2,424 guard events, 0 blocked, 0 violations.

## Detection tests (`test_access_classification_tools.py`, 58)
Guard blocks raw/checkpoint/processed reads incl. `pathlib`, `os.open`, relative and absolute subprocess
arguments, symlinks, repo writes, boundary denials; allows metadata/tmp/code and logs it; classification precedence;
unknown on timeout/unarmed/zero-test; child-process spawners never safe; manifest defect cases (unclassified,
ghost, stale, bad category, flag mismatch, boilerplate reason); runner refuses an untrusted manifest, excludes
unsafe files, **detects a mis-classified file instead of trusting the manifest**, rejects unsafe category requests
and in-repo report paths.

## Disclosed limits
Python-level guard only; a file that fails early can hide later reads; classification is point-in-time (re-run the
generator after any test or code change — the hash makes staleness visible, not harmless).
