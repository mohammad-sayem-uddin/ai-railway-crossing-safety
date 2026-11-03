# Mission 4E.2 Report — D1 Binding Preparation and Dual-Outcome Metric Contract

**Date:** 2026-11-01 · **Repo:** `/Users/sayemuddin/Desktop/Train_automation` · **Branch:** `main` · **HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`

> Everything in this mission is **proposed**. D1 is **not bound**, D2 is **not approved**, the occupancy metric is **not validated**,
> and **no experiment is authorized**.

## 0. Git integrity check (done before any write)

- `git reflog`: one entry — `d4db94d HEAD@{2026-10-16 11:58:32}: reset: moving to HEAD` (a no-op reset; old = new = `d4db94d`). `ORIG_HEAD` = `d4db94d`.
- Mission 4E and 4E.1 handoffs both record HEAD `d4db94d…` and "HEAD unchanged". Branch, HEAD, `git log -1` agree (commit dated 2026-10-12).
- **The "old/new HEAD discrepancy" from 4E.1 could not be reproduced from repository evidence.** The old/new hashes 4E.1 allegedly reported were not provided and appear in no file. Treated as not-reproducible; researcher authorized proceeding.
- Porcelain count at start: 373 (= 4E.1's initial figure). 0 staged. After this mission: 374 (the 8 new documents sit inside the already-untracked `docs/generated/`; the one new test file adds 1 entry); the 19 modified tracked files are the same 19 as at the start (see §6).
- **My slip:** `git fsck --lost-found` wrote 309 pointer files to `.git/lost-found/` (HEAD/refs/index/worktree unaffected). Disclosed earlier; left in place.

## A. Researcher decisions (as supplied; not repository records)

1. D1 = real-world protocol v9.0.0 + ground-truth v7.0.0.
2. D2 outcomes = both premature gate opening **and** train-clearance duration.
3. M4 = `first_blocked_to_t4_clearance` (premature-opening safety metric).
4. M5 never-protected = separate safety outcome.
5. Duration metric = full crossing occupancy = physical crossing-blocked onset → T4.

## B. Technical findings

| # | Finding |
|---|---|
| B1 | v9/v7 working-tree hashes `7c183b32…8734c` / `d100c1e6…49ecf4`; HEAD holds v8/v6 (`dbc7ab78…`, `1fe64500…`). Both selected files are **uncommitted**. |
| B2 | v9↔v7 are compatible at documentary level but contain issues 4E.1 did not report: **T2 has two definitions**; T1-based POR text coexists with selected M4; "physical occupancy" already means `T4−T1` in v9. |
| B3 | M4/M5 implementation matches the stated definition (strict open interval; M5 separate; engine/no-train excluded). `metrics.py` is **untracked** in git. |
| B4 | M4 has no replay-coverage check: a replay ending before T4 reads as "not premature" (characterized by a passing test, not fixed). |
| B5 | **No physical crossing-blocked onset field exists.** `T2_crossing_occupancy_start` is the closest supported boundary but is undesignated, doubly defined, and front-camera-only, while T4 is back-camera-only ⇒ cross-clock; R04 unresolved. **Every event is currently NOT_EVALUABLE for occupancy duration** (also: 0 approved GT records). |
| B6 | The main Stage-2.1 schema cannot record censoring direction, timestamp uncertainty or onset provenance as structured fields. |
| B7 | The protocol-choice envelope rejects unknown keys ⇒ the occupancy metric cannot be bound there without new code/governance. |
| B8 | `execution_gate.py` message calling M4 "not implemented" is stale. |
| B9 | No raw media opened; no proposal T2/T4 values read; no result computed from real data. |

## C. Proposed definitions (all unapproved)

- M4 contract → `M4_SAFETY_METRIC_CONTRACT_20261101_M4E2.md` (rules M4-R1…R10, proposed M4-V6).
- M5 reporting → `M5_NEVER_PROTECTED_REPORTING_DEFINITION_20261101_M4E2.md`.
- Occupancy `D = T4 − T_physical_block_onset` (seconds; working id `full_crossing_occupancy_s`) → `OCCUPANCY_DURATION_METRIC_CONTRACT_20261101_M4E2.md` (OCC-E1…E9).
- Reporting specs → `REPORTING_SPECIFICATIONS_20261101_M4E2.md`.
- D1 proposed binding (not activated) → `D1_V9_V7_PROPOSED_BINDING_NOT_ACTIVATED_20261101_M4E2.md`.
- Gap register → `EVIDENCE_SCHEMA_GAP_REGISTER_20261101_M4E2.md`; checklist → `PREREQUISITE_CHECKLIST_20261101_M4E2.md`.

## D. Formal approvals still pending

D1 binding envelope with hashes · register update · approval of M4/M5/occupancy contracts · designation of the physical-onset boundary ·
T2-definition resolution · M4-supersedes-POR wording · R04 scope (if fused/cross-camera) · genuine Stage-2.1 review + promotion · official split/manifest.

## E. Execution authorizations still pending

EVAL-AUTH · production replay/cache/inference · media inspection for adjudication · timing pilot · any experiment.

## Synthetic tests (Task E)

File: `tests/unit/test_mission4e2_m4_occupancy_contract.py` (new). Synthetic data only; no media/GT/cache/checkpoint/inference.
Part 1 runs the *existing* M4/M5/`evaluate_run`/`aggregate_cohort`; Part 2 runs a **test-local** reference of the *proposed* occupancy rules (nothing added to `src/`).

Command:
```
cd /Users/sayemuddin/Desktop/Train_automation && .venv/bin/python -m pytest tests/unit/test_mission4e2_m4_occupancy_contract.py -p no:cacheprovider -q
```
Result: **57 passed in 0.16s** (run twice; the second after removing one redundant assertion).

Coverage: strict-interval boundaries (start/T4 excluded, OPENING/OPEN, reopen, empty interval) · M5 variants · missing/censored/uncertain T4 ·
invalid (NaN/inf/negative/non-increasing) timestamps · engine/no-train exclusion · mixed-window refusal · duplicate ids ·
M4 vs M5 vs missing-T4 denominator partition · occupancy missing/censored/uncertain/invalid/non-positive/replay-sourced onset ·
same- vs cross-camera with `aligned`/`partially_aligned`/`unaligned`/no-uncertainty · summary statistics · M4/occupancy denominators differ and no combined score.
Not run: the repository's wider suites (they were not needed and may touch real artifacts); `ruff` is not installed in the venv (not run).

## 6. Files written (all new; nothing existing was modified)

`tests/unit/test_mission4e2_m4_occupancy_contract.py` and eight documents in `docs/generated/` (seven `_M4E2` documents plus this report) — nine new files in total.
No canonical approval, register, authorization, readiness, config, schema, ground-truth, or governance file was touched. No stage/commit/push/reset/clean.

## Questions the researcher must answer next

1. Which boundary is the "physical crossing-blocked onset": T1, T2 (under §2.1 or §2.4 wording), or a new boundary?
2. Same-camera landmark convention, or accept cross-camera and depend on R04?
3. Should engine events be in the occupancy population?
4. Should M4 be stated as superseding the T1-based POR text in v9/v7?
