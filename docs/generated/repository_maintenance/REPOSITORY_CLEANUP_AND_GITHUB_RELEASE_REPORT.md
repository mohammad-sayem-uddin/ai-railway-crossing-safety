# Repository Cleanup and GitHub Release Report

**Project:** Train Gate Automation (`Train_automation`)
**GitHub:** https://github.com/mohammad-sayem-uddin/ai-railway-crossing-safety
**Maintenance date:** 2026-11-08
**Scope:** repository cleanup, `.gitignore` rebuild, README rewrite, documentation-integrity
corrections, commit of all legitimate outstanding changes, and fast-forward push to GitHub.
No research experiments were run and no scientific methodology, threshold, or
configuration *value* was changed by this maintenance.

---

## 1. Executive summary

The repository was inventoried (5,125 tracked files, 8.8 GB working tree), cleaned of
regenerable tool clutter only, given an accurate README and a project-structure /
documentation index, and synchronised with GitHub. All outstanding legitimate work —
the researcher's uncommitted Mission 44 changes, Mission 39–44 evidence and caches, the
research-recovery package, and this maintenance's documentation — was committed in
**8 descriptive commits (422 files)** and pushed as a **clean fast-forward**
(`fc3c29a..6aa7fd1`). Final local and remote HEADs are identical (item 16/17). No force
push, reset, rebase, or amend was used at any point; no `git add .` was used — every
commit was staged by explicit path after review.

## 2. Initial repository state

- Size: 8.8 GB total (`.git` 508 MB; `data/` 4.1 GB; `venv/` 1.3 GB; `ESC-50-master/`
  846 MB; `scratch/` 248 MB; `docs/` 172 MB; `experiments/` 157 MB; `results/` 133 MB).
- Tracked files: 5,125. Ignored files: 75,647 (virtual environments, third-party corpus,
  local media, tool caches).
- Largest tracked file: 6.3 MB — **Git LFS is not needed** and was not introduced
  (no `.gitattributes`, no LFS-tracked files).

## 3. Initial branch, HEAD and remote

- Branch: `main` (only branch; tracks `origin/main`).
- Local HEAD: `0454e38d49495e362a82ca7e725be7b1cb43ff9a` (Mission 43).
- Remote `main`: `fc3c29a761deaa9e36eca1e5eea4e0205b1f9a74` (Mission 32), verified live
  with `git ls-remote` before any change.
- Relationship: local was **ahead by exactly 13 commits**; the remote HEAD was the
  merge-base, so the push was guaranteed to be a fast-forward. No divergence existed.

## 4. Initial working tree

- **3 modified tracked files** (researcher's Mission 44 work, reviewed by full diff
  before committing): `src/railway_detection/vision/video.py` (+13/−1),
  `src/railway_detection/experiments/layer_b_processor.py` (+14/−3) — source
  display-rotation provenance handling — and
  `docs/generated/master_reaudit/MISSION_17I_MISSION18_ACCEPTANCE_AND_DEPENDENCY_REGISTER.md`
  (+16, appended §7 recording 18A-R2 selections as *submitted, authority unverified*).
- **~400 untracked files** in 13 top-level entries: Mission 44 evidence package (270
  files), Mission 39/43 prediction caches (`data/cache/` 57 files, 5.5 MB;
  `results/experiments/cache/`, 12 MB), research-recovery deliverables (11 files),
  Mission 18A/19 reaudit records (6 files), one synthetic test file. All assessed
  legitimate project artifacts (item 5) and committed.
- Nothing was staged at mission start.

## 5. Inventory summary

Tracked content by area: `docs/` 2,970 files; `results/` 1,363; `tests/` 190; `data/`
187; `src/` 176; `experiments/` 92; `research/` 66; `scripts/` 51; `configs/` 9;
`reports/` 7; plus root files (README, pyproject.toml, requirements.lock, .env.example,
the 2026-08-31 .docx report, recovery reports, demo utilities). The pre-existing
`.gitignore` (141 lines) was already comprehensive (OS/editor artifacts, bytecode,
venvs, test/typing/lint caches, `.env*` with `!.env.example`, key files, scratch,
local media, all `*.pt` weights, ESC-50, Unseen_Video); only narrow gaps were found
(item 8).

## 6. Files and directories removed

Removed **to the macOS Trash (recoverable, not permanently deleted)** — all regenerable
tool clutter containing no evidence, data, or researcher work:

| Item | Reason |
|---|---|
| `.DS_Store` (1 file) | macOS Finder artifact |
| `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/` | Tool caches; regenerated on demand |
| `.probe_write_test` | Leftover write-probe file |
| 26 × `__pycache__/` dirs (under `src/`, `tests/`, `scripts/`, `research/`) | Python bytecode caches |

Nothing else was deleted.

## 7. Files and directories preserved

Explicitly preserved after review: `venv/` (1.3 GB) and `.venv/` — the project's active
environments (already git-ignored; deletion would harm the research environment with no
repository benefit); `scratch/` (248 MB) — the researcher's local analysis workspace,
documented in `.gitignore` as maintained locally for researcher review; `.commandcode/`
(local tool configuration); `ESC-50-master/` (third-party corpus, local-only);
`Unseen_Video/`; all of `data/` including original recordings (never modified);
`results/experiments/phase5_full_dataset_run_20261013/internal_cache` (empty historical
directory); the empty `docs/generated/professor_evidence/mission44/figures/` directory
(git does not track empty directories; left on disk as part of the package layout);
all historical reports, including superseded ones (marked, not deleted); the two
tracked copies of the 2026-08-31 `.docx` report (root and `results/`).

## 8. `.gitignore` changes

The existing file was verified section by section and **extended, not rewritten**: a
dated "Repository maintenance additions (2026-11-08)" section adds `.tox/`, `.nox/`,
`.AppleDouble`, `.LSOverride`, `*.tmp`, `*.temp`, `*.p12`, `*.pfx`, `id_rsa`,
`id_ed25519` (+26 lines, commit `c236e71`). Verification (`git check-ignore`) confirmed
no research artifact is hidden: README, PROJECT_STRUCTURE, the recovery report, the
Mission 44 package, the new test, `data/ground_truth/`, source, and frozen configs are
all **not ignored**. One pre-existing interaction was found and handled explicitly:
the generic `logs/` rule also matches `docs/generated/professor_evidence/mission44/logs/`
(13 execution-log files). Because those logs are Mission 44 evidence, they were
**force-added** (`git add -f`) in the Mission 44 commit and are now tracked; the ignore
rule itself was left unchanged for genuine runtime logs.

## 9. README changes

`README.md` was rewritten in full (24,537 B; old version preserved in git history) under
the accurate title **"Train Gate Automation: A Multimodal, Temporal, Safety-Oriented
Railway-Crossing Decision Architecture"**. It now: leads with the Protocol V2 primary
question (the policy's effect is to be measured as **change**, not assumed improvement);
describes the implemented architecture (parallel vision + audio evidence, temporal
collector, deterministic rule-based fusion RULE_1–RULE_10, 11-state decision engine,
sensor-health tracking, simulated gate); corrects the old README's false "single-class
(train)" detector claim — the frozen detector is a **three-class viewpoint detector**
(front/rear/side, threshold 0.35) and the Audio V3 CNN operates at frozen threshold
0.3700 with 64-band log-mel features; distinguishes frozen **v1** policy from the
unauthorised **v2 candidate** and discloses the v1 label-overlap defect; reports the
dataset truthfully (27 events, single site `crossing_A`, daytime-only, annotations are
researcher-adopted AI-assisted references, no bounding boxes/audio window labels);
reports Mission 43 exactly (B0_front 6,613 records/329 objects; B0_back 6,479/1,020;
B1_audio 2,600 windows/445 positive; B2 assembly 6,614 frames/3,897 paired; **decision
replay not executed**; exploratory audio comparison TP 12/FP 10/FN 1/TN 0, precision
54.55%, recall 92.31%, specificity 0%); and lists the blockers (item 18). No cascade,
weighted/neural fusion, cross-site generalisation, or deployment-readiness claim appears
anywhere. The authors' citation block (Uddin & Rahu), AI-assistance disclosure, and the
checkpoint SHA-256 weights register were preserved.

## 10. PROJECT_STRUCTURE.md and documentation index

New root `PROJECT_STRUCTURE.md` (14,513 B): a verified map of every major directory and
of the 170-module `src/railway_detection/` package (including the warning that
`safety/` holds governance/access control, not gate fail-safe logic); a configuration
table identifying the authoritative frozen configs vs the superseded placeholders; a
research documentation index (founding documents, audit-era methodology, mission
record, historical records to handle with care); and the experiment taxonomy map
(item 11). All relative links were verified against the actual `docs/` contents.

## 11. Documentation corrections

- `configs/fusion.yaml` and `configs/simulation.yaml`: header comments replaced with an
  explicit **SUPERSEDED Phase-0 placeholder** banner naming the executed configuration
  (`frozen_experiment_v1.yaml` + `decision_policy_v1.yaml`). **No values were changed.**
- `src/railway_detection/vision/__init__.py`: stale "Phase 0 placeholder / not
  implemented yet" docstring replaced with an accurate package description;
  `NotImplementedInPhase0` class retained for compatibility (verified importable).
- v1-vs-v2 policy relationship documented in README §4 and the PROJECT_STRUCTURE
  configuration table (v2 remains a non-authorised candidate; it was not promoted).
- Experiment taxonomy map (PROJECT_STRUCTURE §3): concept-era A–G ladder, Protocol V2
  B0–B7 decision conditions, audit-era E1–E10, and Mission 39–43 usage
  (B0_front/B0_back/B1_audio/B2 as perception/assembly labels) are explicitly
  distinguished, per Independent Audit CF-03.

## 12. Sensitive-file review

- Tracked files with sensitive names: only `.env.example`, which contains placeholder
  values only (verified by reading it).
- Pattern scan over all tracked files for GitHub tokens (`ghp_`, `github_pat_`), AWS
  keys (`AKIA`), private-key headers, and `sk-` keys: **zero matches**.
- Untracked sensitive-name files: none. No credential value was printed, copied, or
  committed at any point. Push authentication used the Mac's existing macOS-keychain
  git credentials; nothing new was stored.

## 13. Validation performed

- Link verification: every relative link in the new README and PROJECT_STRUCTURE was
  checked against the repository contents — all resolve.
- `git check-ignore` spot checks (item 8): no evidence-bearing path is ignored.
- Staged-content review: every commit was staged by explicit paths and its
  `git diff --cached --stat` reviewed before committing; file counts and sizes match
  the inventory (largest committed file 1.7 MB).
- Lightweight tests: `tests/synthetic_mission44/` (the test covering the committed
  Mission 44 code change) — **9 passed** (Python 3.11.15, `.venv`). Import check of the
  edited `vision` package passed.
- Honest suite status: the full guarded suite was **not** re-run in this maintenance;
  its last full run (Mission 43) recorded 3,815 cases — 3,700 passed, 84 failed,
  31 errors, all non-passing cases triaged as protected-dependency policy exceptions.
  The suite is not described as passing anywhere in the updated documentation.

## 14. Commits created

All commits are on `main`, on top of the pre-existing Mission 43 HEAD `0454e38`
(itself the last of the 13 previously-unpushed local commits, Missions 33–43):

| # | Hash | Message | Files |
|---|---|---|---|
| 1 | `db403058d469ed51e49cee199c38bc046c2771ba` | Add source display-rotation provenance handling (Mission 44) | 3 |
| 2 | `ee5699864532754fa3e45f092ea35241cd312870` | docs: add Mission 18A/19 reaudit records and 17I register update | 7 |
| 3 | `348bacf91827c578650cf4656c9321997ba01181` | docs: add Mission 44 professor evidence package | 283 |
| 4 | `dd42975cd09086c4eafcb9926ab8924ff770227c` | data: add Mission 39/43 experiment prediction caches | 112 |
| 5 | `318f50fd541260d0e731b0f631f36217eee7abdc` | docs: add research recovery report and evidence matrices | 11 |
| 6 | `c236e71027cc1062c8dad262fce2445f0442512d` | chore: improve repository hygiene and gitignore | 1 |
| 7 | `544b63c27bd91b5502b77af01202628fe4038ad1` | docs: rebuild research project README and architecture documentation | 2 |
| 8 | `6aa7fd18809fef7c45e578f1bebb419e13159386` | docs: correct configuration and experiment status descriptions | 3 |

This report is committed in one final follow-up commit after the verified push
(see git log); it is the only file that post-dates item 15's verification.

## 15. Push result

**Success.** `git push origin main` exited 0: `fc3c29a..6aa7fd1  main -> main` — a pure
fast-forward of 21 commits (13 pre-existing + 8 from item 14). No force, no rejection,
no divergence. Independently verified through the GitHub API (Muse GitHub connector,
connected 2026-11-08 at the owner's request): `list_commits` shows `6aa7fd1` as the
remote head commit.

## 16. Final local HEAD

`6aa7fd18809fef7c45e578f1bebb419e13159386` at push verification (working tree clean;
advances by one commit when this report is committed — see item 14 note).

## 17. Final remote HEAD

`6aa7fd18809fef7c45e578f1bebb419e13159386` (`refs/heads/main`, via `git ls-remote` and
the GitHub API — identical to local at verification).

## 18. Remaining issues

These are **research** matters deliberately untouched by this maintenance:

1. **B2 decision replay remains blocked** by missing researcher governance records
   (`AUTH-DESCRIPTIVE-EVAL-EXEC.json`, Stage 2.1 promotion receipt, protocol-choice
   record) and the undecided `premature_opening_window`. Next step per the research
   recovery report §12: researcher records the governance package → add the back
   camera to the B2 assembly → pilot replay on 5 events.
2. **v1/v2 canonical-policy decision is open** (v1 label-overlap defect documented;
   v2 candidate not authorised).
3. **Full test suite is not fully passing** (84 failed / 31 errors at last full run,
   triaged as protected-dependency policy exceptions).
4. The Mission 44 `figures/` directory is empty and therefore untracked (git does not
   version empty directories); it remains on disk.
5. Git LFS was assessed and **not** adopted (largest tracked file 6.3 MB); revisit only
   if large binary artifacts are ever to be versioned.
6. The Muse GitHub connector is connected for API-level repository access; it was
   *not* used for this push because its snapshot mechanism cannot carry local git
   history — the push ran from the Mac, as git requires.

*Report generated 2026-11-08 as part of the repository cleanup and GitHub release
mission. Companion document: `docs/generated/research_recovery/ORIGINAL_RESEARCH_TARGET_AND_BLOCKER_REPORT.md`.*
