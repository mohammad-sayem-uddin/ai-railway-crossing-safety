# Mission 13 — WP13.6 Backup and Preservation Audit

**Date:** 2026-11-02. Read-only: `git status`, `git diff --name-only`, `git ls-files`, `ls -lT`, `find` over the backup directory. No file was restored, deleted, renamed, staged, cleaned or overwritten.

## 1. Git state (this audit)

| | Start of audit | End of audit |
|---|---|---|
| HEAD | `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` | same |
| Branch | `main` | `main` |
| Staged | 0 | 0 |
| Modified tracked | 25 | 25 |
| Untracked status entries (directory-collapsed) | 379 | 379 (new Mission 13 files sit inside the already-untracked `docs/generated/` directory; the porcelain listing is byte-identical to the start snapshot, confirmed with `diff` after all reports were written) |

Mission 12 reported 22 modified tracked files at its baseline. The present figure is 25. Mission 12 lists four tracked files it edited (`data/manifest.py`, `data/validator.py`, and the two `research/scripts/generate_*_figure*.py`); I cannot reconcile 22 → 25 without Mission 12's file-level snapshot, so the difference is **recorded as an unexplained discrepancy, not as a violation**.

## 2. Mission 12's backup claims

| Claim | Check | Result |
|---|---|---|
| "No backups were created or overwritten during Mission 12" | newest file in `/private/tmp/claude-501/m10/backup/` is 07:32; Mission 12 source edits are 10:15–10:38 | consistent |
| "Existing backup directory has 64 files" | `find … -type f | wc -l` = 64 (10 phase5_docs, 13 scripts_pre_wp102, 36 untracked, plus 3 tracked-source copies and 2 audit reports at top level) | consistent |
| "3 tracked-source copies: cli/main, data/layer_b, vision/video" | present with `.pre_m10` names | consistent |
| "Other 19 modified tracked files have no same-path backup" | none of `README.md`, `pyproject.toml`, the five docs, `audio/*`, `data/{manifest,sync,validator}.py`, `demo/*`, `evaluation/__init__.py`, `fusion/evidence.py`, `tests/*`, `research/scripts/*` has a same-path backup (validator has an unrelated `validator.py.pre_wp102` that belongs to `experiments/…`; its path origin is ambiguous) | consistent |
| "No missing backup was reconstructed; nothing restored" | nothing in the backup directory is newer than 07:32 | consistent |

## 3. What is protected and what is not

| Group | Verified backup? | Notes |
|---|---|---|
| `cli/main.py`, `data/layer_b.py`, `vision/video.py` | copy of the pre-Mission-10 file exists | completeness of the copy not independently provable (agrees with Mission 12) |
| Phase 5 docs (10) | copies exist | |
| Scripts edited by WP10.2 (13) | `.pre_wp102` copies | |
| Untracked Mission-10 files (36) | `.orig` / `.pre_wp102` copies for a subset (e.g. `execution_gate.py.orig`, `input_contracts.py.pre_wp102`, `cache_only_engine.py.pre_wp102`, `test_media_authorization.py.orig`, `test_phase12_governance.py.orig`) | **older than the Mission 12 edits** |
| **`safety/media_guard.py`, `evaluation/evaluation_runner.py`** (the files that carry the M-02 and media fixes) | **no backup of the pre-Mission-12 content** | untracked → no git history either |
| **`data/manifest.py`, `data/validator.py`** (tracked, edited by M12) | HEAD version in git only; the pre-Mission-12 working-tree version is unrecoverable | |
| **`research/scripts/generate_*_figure*.py`** (tracked, edited and reformatted by M12) | HEAD version in git only | `ruff format` rewrote large unrelated blocks; the diff is formatting churn plus the guard calls |
| **`test_media_authorization.py`, `test_media_opener_coverage.py`, `test_phase12_governance.py`, `test_phase12_official_replay.py`** | `.orig` only for two, and older than M12 | |
| `PAPER_DRAFT_PHASE5_REVISION.md` | pre-M12 copy not seen | |

## 4. Structural preservation problems

1. **Security-critical code is untracked.** `git ls-files src/railway_detection/safety src/railway_detection/evaluation` returns one file (`evaluation/__init__.py`). The media guard, access manifest, runner, gates, governance code, annotation package, and the Mission 12 fixes exist only in the working tree. Mission 11B **N-06** is unchanged. A `git clean -fd`, `git checkout .`, or disk loss would destroy them.
2. **The only backups live in `/private/tmp/…`**, an OS temporary directory that macOS can clear on reboot or by periodic cleanup. They are not a durable preservation mechanism.
3. **Mission 12 changed security-critical files without taking backups**, although Mission 10 had established the practice.
4. `.commandcode/`, `.probe_write_test` and many generated artifacts are untracked at the repository root (pre-existing; not touched).

## 5. What Mission 13 did to the working tree

- Created only new files under `docs/generated/phase5/` (this report set and `mission13_probes/`) and temporary files in the session scratchpad.
- Wrote nothing under `data/`, `src/`, `tests/`, `configs/`, `scripts/`, `research/` or `docs/` outside `docs/generated/phase5/`.
- Ran no Git write command. Python was run with `PYTHONDONTWRITEBYTECODE=1` (the 76/262-test runs used `-p no:cacheprovider`). Between each probe the porcelain listing was diffed against the start snapshot and was identical.

## 6. Findings

| ID | Sev | Finding |
|---|---|---|
| F13-17 | HIGH | Security-critical implementation untracked; Mission 12 edits have no backup; the existing backups are in volatile `/private/tmp`. (Extends N-06 and BKP-01.) |
| F13-18 | LOW | Mission 12 reformatted two research scripts (`ruff format`), enlarging the diff beyond the security change; modified-file count 22 → 25 unexplained. |
| N-06 | HIGH | **OPEN** (unchanged). |
| BKP-01 | LOW→MEDIUM | **OPEN** (unchanged; worsened by M12 edits without backups). |

## 7. Disposition

No preservation breach was found during Mission 13 or attributable to a Mission 12 *action* on unrelated files. Preservation is nevertheless **not verified**: it depends on a working tree that contains the only copy of the security-critical code. Closure criterion "Git and data preservation verified" is **not met**.
