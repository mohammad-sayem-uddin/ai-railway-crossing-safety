# Mission 14 — WP14.6 Mission 12 Test-Execution Provenance (F13-08)

**Question:** did Mission 12 run `tests/unit/test_phase12_governance.py` and `tests/unit/test_phase12_official_replay.py` directly, and did doing so open/hash the production model checkpoints?
**Method:** documents, test source, classification manifest, session records, file timestamps. **Neither test file was executed by Mission 14. No checkpoint file was opened, hashed, listed or `stat`-ed** (even metadata such as access time of a protected file was deliberately not examined). Nothing was invented or reconstructed; absent evidence is reported as absent.
**Confidence vocabulary (from the brief):** 1 Confirmed executed · 2 Strong evidence of execution · 3 Possible execution · 4 Not established · 5 Confirmed not executed.

## 1. Evidence found

| # | Evidence | What it shows | Strength |
|---|---|---|---|
| E1 | `MISSION_12_ADVERSARIAL_TEST_REPORT.md`: a plain `.venv/bin/pytest -q --no-header` command listing six files, including both test files, result "**300 passed**". Not run through `scripts/run_synthetic_tests.py` and not under the access-guard plugin | Mission 12 states it ran them directly, unguarded | self-report |
| E2 | Pytest-rewritten bytecode caches `tests/unit/__pycache__/test_phase12_governance.cpython-311-pytest-9.1.1.pyc`, `…test_phase12_official_replay…pyc` and `…test_media_authorization…pyc`, **all stamped 2026-11-02 10:36:45**, i.e. **after** the sources were last saved (10:31:40 / 10:31:41). The `-pytest-` suffix means pytest imported the modules with assertion rewriting while bytecode writing was enabled. The safe runner and the classifier set `PYTHONDONTWRITEBYTECODE=1`; so did every Mission 13/14 pytest run (those started after 10:50) | A pytest process outside the safe runner imported exactly these modules at 10:36:45, inside Mission 12's working window | independent artifact |
| E3 | Arithmetic: the manifest's recorded counts give 19 (`evaluation_runner`) + **76** (`governance`: 74 passed + 2 failed under the guard) + **88** (`official_replay`: 87 + 1) + 72 (`media_authorization`) + 4 (`opener coverage`) + 41 (`descriptive gate`) = **300** — Mission 12's total exactly. The second command (151) = 36 + 33 + 82 exactly | The "300 passed" is consistent with **every** test in both files having run and passed, including the three tests that fail when protected reads are blocked | corroborating |
| E4 | Mission 12's own temp snapshots: `/private/tmp/m12_status_before.txt` 10:11:29, `m12_modified_after.txt` 10:29, `m12_format.log` 10:38, `m12_safe_runner.json` 10:40:13, `m12_ruff_final.txt` 10:43:53 | Mission 12 worked 10:11–10:44; E2's 10:36:45 lies inside | context |
| E5 | `tests/test_access_classification.yaml` (as of the 07:30 guarded classification): governance → `MODEL_CHECKPOINT_ACCESS`, blocked attempt on `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`, 2 failed; official_replay → `PROCESSED_DATA_ACCESS`, 1 failed | Under the read-blocking guard, exactly the real-repository tests fail because their protected read is refused | dynamic, earlier version |

## 2. Static trace of what those tests do

* `test_phase12_governance.py` calls `assess_official_phase12_readiness(REPO_ROOT)` in three tests. `execution_gate.assess_official_phase12_readiness` always runs the frozen-configuration block, which calls `frozen_config.verify_checkpoint_integrity(config, repo_root=root)` → `compute_file_sha256` (`open(path, "rb")`, 1 MiB chunks) on the vision checkpoint, the audio-v3 checkpoint and, if present, the prohibited audio-v2 checkpoint. The workspace-based tests stub this function; the three real-repository tests do not.
* `test_phase12_official_replay.py::test_real_repository_run_is_blocked_and_leaves_everything_untouched` runs `cli_main(["evaluation","run","--repository-root", REPO_ROOT …])` and `run_official_safe(repository_root=REPO_ROOT)`, which reach the same gate; it also hashes `results/experiment_registry.jsonl` and every review record. The module loads the real frozen configuration YAML at import.
* Mission 14 re-checked this by splitting the files: with the real-repository tests removed, the remaining 74 and 87 tests pass under the read-blocking guard with **zero** blocked reads (see `MISSION_14_TEST_CLASSIFICATION_RECOVERY.md`). The blocked reads therefore belong exactly to the removed tests.

## 3. Findings by question

| Question | Level | Basis |
|---|---|---|
| Were both files imported by pytest in a non-safe-runner process during Mission 12? | **2 — strong evidence** | E2 |
| Were all their tests **executed** (not only collected) by Mission 12? | **2 — strong evidence** | E1 + E3 (exact arithmetic) + E2. No original tool log exists to promote this to level 1 |
| Did those executed tests run against the real repository paths? | **2 — strong evidence** | follows from the test source: the three tests use `REPO_ROOT` |
| Were the production checkpoints **opened and hashed** during that run? | **3 — possible, probable by code path; not established** | E5 + §2: the executed code path hashes them, and the three tests passed instead of failing as they did under the guard. There is **no direct observation** (no file-access log; protected-file metadata deliberately not examined). Mission 14 does not convert this into a confirmed violation |
| Was raw media opened by those tests? | **4 — not established, no evidence for it** | the real-repository tests read review JSON, config, registry; no media suffix path appears in the traced code |

## 4. Evidence that could not be obtained

* **Mission 12's tool-execution log is not available.** All six Claude Code sessions recorded for this project under `~/.claude/projects/-Users-sayemuddin-Desktop-Train-automation/` were searched for `pytest` Bash calls naming these files: the newest pre-Mission-13 session (`81212977…`) ends at 12:37Z (07:37 local), before Mission 12's edits began at 10:11 local; the next session is Mission 13 itself (starts 15:50Z = 10:50 local). Mission 12 therefore ran in a tool or session whose transcript is not stored here.
* `.commandcode/` holds only `settings.json` and two `taste.md` files from August. Shell history does not record agent tool calls.
* Operating-system file-access auditing for the relevant minutes: not available retrospectively.

## 5. Security incident record

**Status: UNRESOLVED — possible protected-checkpoint read by Mission 12 (read-only integrity hashing; no inference, no modification, no media).** It contradicts Mission 12's statements that no checkpoint was opened or hashed (`MISSION_12_REMEDIATION_REPORT.md` "Scope and safety"; `MISSION_12_ARTIFACT_MANIFEST.json` `real_data_accessed:false` / `protected_hash_policy`; manuscript §11 "no protected checkpoint was opened or hashed during this audit"). The *sensitivity* is low (a local read-only digest of model weights that the readiness gate is designed to compute), but the statement was made as a verified safety fact and it is not established.

**Recommended human review (not performed by Mission 14):**

1. The researcher reviews the Mission 12 session record in the tool that produced it (it is not on this machine's Claude store) for the exact commands run at ≈10:36 local.
2. Decide whether read-only checkpoint integrity hashing counts as a protected-data incident under the project's policy (the production gate itself performs it — Mission 13 F13-09 asks the same policy question).
3. If it does, record it formally; do not hash the checkpoints now to "check".
4. Correct the Mission 12 statements by notice (below), not by editing the historical reports.

## 6. Correction notice for Mission 12 (historical reports left unmodified)

> **Correction notice (Mission 14, 2026-11-02).** `MISSION_12_REMEDIATION_REPORT.md`, `MISSION_12_ARTIFACT_MANIFEST.json` and `PAPER_DRAFT_PHASE5_REVISION.md` §11 state that no protected checkpoint was opened or hashed. That statement is **not established**. Mission 12's own report shows it ran `test_phase12_governance.py` and `test_phase12_official_replay.py` directly (outside the safe runner and the read-blocking guard). Those files are classified protected-access because three tests (governance) and one test (official replay) run the official readiness gate against the real repository, which hashes the production checkpoints. Strong evidence (pytest bytecode caches stamped 10:36:45; test counts summing exactly to the reported 300) indicates the files were executed; whether the checkpoints were actually hashed cannot be established from the surviving evidence. Treat the checkpoint-access question as **open** pending human review. The Mission 12 statement that `modified tracked files = 22` was correct at 10:11 (its own snapshot) and became 25 after its edits to three previously clean tracked files (`generate_qualitative_figures.py`, `generate_video_progression_figure.py`, `data/manifest.py`).
