# Mission 5A.1 — Change Log

## 1. Files changed (all pre-existing files were already modified/untracked by Mission 5A; none of the 19 modified tracked files was touched)
| File | Tracked? | Before SHA-256 | After SHA-256 | Change |
|---|---|---|---|---|
| `src/railway_detection/evaluation/metrics.py` | untracked | `7d7083eb71d334615e8b2f1c673313055fe0d0028734e7c3ef915eef2d6e7f87` (5A final) | `a4af9a79289f493b8b627831434301f981d29b430a56b6c4e210c01e3082c2f7` | (1) cohort-vs-routing-flag fail-closed checks; (2) `UnresolvedCohortError` + `UNVERIFIED_GROUND_TRUTH_STATUSES`: unresolved cohort tolerated only for already-unverified ground-truth records; the inline status set now uses the shared constant. Net 50 changed lines vs the start of 5A.1. |
| `scripts/mission5a_build_preservation_manifest.py` | untracked | `0d3dec4b279550c01a046eeefa8449e82f088b6f21c928ea9dd6102e526e0697` | `41cc06e5322fb6b36586e0d389784a2e38b53624a9f139c9910a8f95e4d0f3e5` | `path_refusal()` guard; `verify` refuses and never opens unsafe entries and reports `refused`; frozen-checkpoint paths validated; symlinks counted as `symlink_not_followed` |
| `tests/unit/test_mission5a_production.py` | untracked | `7bae8cfe16a4189295d7e53963a2b2f6c2fc01903eb65fe5b62b9b3f988572bf` | `c29e299dba562b4ee8504ffe8603a0609ed5d8adac1dc7b3888297bea870d89b` | one fixture corrected: a `no_train_events` event was built with `has_train_ground_truth=True` (a contradiction the new check rightly rejects); now `False` for that cohort |
| `tests/unit/test_mission5a1_audit_regressions.py` | **new** | — | `9b3bf0ba77e5d253a1beef73a4e554e95e8a4ba85d647f7190e1cd6c29adf61c` | 68 tests |
| `docs/generated/mission_5a_1/*.md` | new | — | — | the eight audit documents (this log included) |

## 2. Corrections applied, with justification
| ID | Defect | Why no researcher decision was needed | Smallest correction | Regression test |
|---|---|---|---|---|
| C-1 | `verify_manifest` opened any listed path (media-like, binary, outside root, symlink) | pure safety hardening of a tool; no scientific meaning | `path_refusal()` | `TestManifestSafety` (7 tests) |
| C-2 | cohort could contradict `has_train_ground_truth` / `ground_truth_status`, silently pooling an event into the wrong denominator | consistency check; official callers already consistent | three `UnqualifiedEventIdError` raises | `test_cohort_versus_routing_flag_contradictions_fail_closed` |
| C-3 | **Regression from 5A:** unannotated events (`cohort=None`, bare id) raised and would abort `run_condition` | restores pre-5A behaviour for records that are already non-evaluable and enter no denominator; evaluable records still fail closed | `UnresolvedCohortError` tolerated only when GT is unverified | `TestUnannotatedEventsDoNotAbortAndDoNotLeak` (11 cases) |

## 3. Corrections considered and deliberately NOT applied
| Item | Why not |
|---|---|
| Treat "no retained step before T4" (and late replay start) as NOT_EVALUABLE (F-04) | A first attempt was made and **reverted**: it overrode an existing pre-5A test that pins "first block exactly at T4 → M5", and a narrow fix would leave an arbitrary discontinuity (first step 5.0 vs 4.9). Defining sufficient start coverage (and any tolerance) is a researcher decision. `metrics.py` was restored from the saved copy before C-2/C-3 were applied; the pin is documented by `test_open_replay_start_coverage_is_not_checked`. |
| Revert or keep `no_steps_in_protection_interval` (F-05) | pending researcher decision |
| Change the lead-in screen toward the design's M3 (F-06) | research decision |
| Make `derive_min_block_latency_s` take the frozen config (F-07) | no output change today; wiring decision |
| Add a `cohort` field to `SingleEventEvaluation`; null `m4_status` on `evaluable=False` (F-08, F-09) | API/schema changes; not defects of the stated claims |
| Edit "Final …" titles of the proposed protocols (W-1) | governance documents are not rewritten in this mission |
| Prune media-directory enumeration in the manifest tool (F-11) | behaviour change to counts; recommended, not required |

## 4. Mission 5A statements this audit supersedes (documents left unedited)
5A execution report deviation 5 (engine routing); 5A M4/M5 correction document ("never M5" holds for end-truncation only; identity rule now also checks cohort-vs-flag and tolerates unresolved cohort for unverified GT); 5A manifest entries for the three changed files (hashes above); my earlier "309 pointer files" (301 pointers + 8 blob dumps).

## 5. State accounting
* **Files inspected** (read): `metrics.py` (full diff vs pre-5A), `lead_in_screen.py`, `stage2_1_schema_proposed.py` (imports only), `clock_aware.py`, `evaluation_runner.py`, `experiments/runner.py` (ground-truth extraction), `data/contracts.py`, `data/layer_b.py` (id formation), `frozen_config.py`, `fusion/decision_engine.py` (constructor), the manifest script and manifest JSON, the three test files, all `mission_5a` documents, `configs/*` (two exploratory configs, frozen config values), `authorized_reviewers.json`.
* **Not touched:** both in-place protocols; the 19 originally-modified tracked files; `EXPERIMENT_DESIGN_FINAL.md` and other untracked authority documents; all configs, schemas, `data/`; `.git/` (incl. `lost-found`, 309 files unchanged).
* **Git:** HEAD `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`; staged 0; the modified-tracked list is identical to Phase 0 (19). No `add/commit/push/reset/clean/checkout/restore/revert/fsck`.
