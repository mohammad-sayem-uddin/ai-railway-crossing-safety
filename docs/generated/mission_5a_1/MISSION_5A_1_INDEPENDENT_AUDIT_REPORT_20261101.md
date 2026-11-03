# Mission 5A.1 — Independent Production Code Audit & Safety Verification

**Date:** 2026-11-01 · **Repo:** `/Users/sayemuddin/Desktop/Train_automation` · **Branch:** `main` · **HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (unchanged)
Supporting documents (same folder): `M4_M5_SIX_CASE_VERIFICATION`, `EVENT_IDENTITY_AND_ENGINE_ROUTING_AUDIT`, `LEAD_IN_SCREEN_TECHNICAL_AUDIT`, `PRESERVATION_MANIFEST_SAFETY_AUDIT`, `GOVERNANCE_BOUNDARY_AUDIT`, `MISSION_5A_1_TEST_RESULTS`, `MISSION_5A_1_CHANGE_LOG` (all `_20261101.md`).

## Phase 0 — baseline (matches the Mission 5A report on every item)
HEAD `d4db94d4…`; staged 0; modified tracked 19 (list recorded; identical at the end); v9 `7c183b32…8734c`; v7 `d100c1e6…49ecf4`; `metrics.py` `7d7083eb…7f87` (5A final); untracked porcelain entries 358 (total 377). `.git/lost-found`: 309 regular files (146 + 163; method table in the manifest audit). No stop condition triggered.

## A. Executive verdict

**PASS WITH CONDITIONS** — for Mission 5A *as corrected by 5A.1*.
As delivered (before 5A.1) Mission 5A would have been **REQUIRES CORRECTION**: it contained one regression that would abort the diagnostic runner on unannotated events, a verification path that could be steered onto media, and a routing gap that could pool an event into the wrong denominator. Those three were corrected here (minimal changes, synthetic regression tests, hashes recorded). Acceptance is conditional on the researcher deciding the open items in section D — most importantly **F-04** (replay *start* coverage), which still contradicts the claim that incomplete evidence is never counted as never-protected.

## B. Findings

| ID | Severity | Status | Where | Evidence | Impact | Recommended action |
|---|---|---|---|---|---|---|
| F-01 | MEDIUM | **FIXED** | `scripts/mission5a_build_preservation_manifest.py::verify_manifest` | probe: crafted manifest made `verify` open 6 dummy media-like/binary/symlinked/out-of-tree files; build was safe | a tampered manifest could make verification read media | `path_refusal()` guard (done); tests `TestManifestSafety` |
| F-02 | MEDIUM | **FIXED** (5A regression) | `metrics.py::evaluate_run`; `experiments/runner.py` ground-truth extraction | synthetic unannotated event, bare id, `cohort=None`: pre-5A `ground_truth_missing`; 5A raised `UnqualifiedEventIdError` | a diagnostic condition run would abort on any unannotated event | tolerate an unresolved cohort only for already-unverified ground truth (done); real Layer-B ids not examined |
| F-03 | MEDIUM | **FIXED** | `metrics.py::evaluate_run` | train+`has_train=False` → evaluable no-train record; no-train+`True` → evaluable train record; train+status `engine` → engine branch | wrong-denominator pooling reachable by a direct caller (official callers are consistent) | three fail-closed checks (done) |
| F-04 | **HIGH** | **OPEN — researcher decision** | `metrics.py::classify_m4` | only `last_step ≥ T4` is checked. First retained step after T4, or a late start (first step 4.0 unblocked, T4 5.0), is classified `NEVER_PROTECTED_M5`; an existing pre-5A test pins "first block exactly at T4 → M5" | M5 can be asserted from zero or partial observation of the pre-T4 interval (overstates never-protected) | decide a start-coverage rule (see D-1). **A fix was attempted and reverted** (it overrode an established test and left a discontinuity) |
| F-05 | MEDIUM | OPEN — researcher decision | `classify_m4` (`no_steps_in_protection_interval`) | a complete replay with no retained step inside `(t_blocked, T4)` → NOT_EVALUABLE; cannot distinguish "blocked in the last tick" from "never sampled" (use `max_step_gap_s`); not part of the original decision table | affects only very sparse replays; never enters M4 no-violation or M5 | keep (conservative) or revert; see D-2 |
| F-06 | MEDIUM | OPEN — researcher decision | `lead_in_screen.py` vs design M3 | two cells differ (observable T0 too close to T1; unknown T0 with T1 ≥ latency) | MTR denominator differs from literal M3 | D-3 |
| F-07 | LOW | OPEN | `derive_min_block_latency_s` | builds `EventSimulationRunner()` with constructor defaults, not the frozen config; equal today (3.6 s at 0.1/0.2 s ticks) but 3.5 s at 0.25/0.5 s | "frozen" provenance not enforced; 3.6 s must not be read as a threshold | pass config explicitly + record its hash when ever wired |
| F-08 | LOW | OPEN | `evaluate_run` return | `evaluable=False` train records keep `m4_status="EVALUABLE"` while `premature_opening=None` | per-event JSON could mislead; aggregation unaffected (uses `eligible`) | null M4 fields when not evaluable, or document |
| F-09 | LOW | OPEN | `SingleEventEvaluation` | no `cohort` field; bare ids from different cohorts collide in `aggregate_cohort` (fail closed) | provenance relies on id prefix/notes | add resolved cohort field when the artifact schema may change |
| F-10 | LOW (pre-existing) | OPEN | `aggregate_cohort` | events with unverified ground truth are outside `eligible`, in `total_events`, but not in `exclusions` or `m4_not_evaluable_*` | those events vanish from summary counts without a stated reason | add an "unverified ground truth" count |
| F-11 | LOW | OPEN | manifest `build` | enumerates and `lstat`s all names under `data/raw` etc. (nothing opened) | broader media-name enumeration than needed | prune output trees at directory level |
| F-12 | INFO | — | manifest | cannot detect added files; own integrity needs external digest; allowlisted text extensions trusted | scope limits | documented |
| F-13 | LOW | OPEN | proposed protocol titles | headline "# Final …" and `FINAL_` file names under a PROPOSED banner | possible finality inference | prefix titles with "PROPOSED —" when next edited |
| F-14 | INFO | — | 5A report deviation 5 | for cohort-qualified ids engine routing is **unchanged**; the change affects bare ids only (old: evaluable no-train negative control) | claim overstated; underlying 5A fix valuable | superseded by this audit |
| F-15 | INFO | — | `execution_gate.py` | edit is a message string (visible); no baseline exists to diff (untracked) | "no other gate edit" is only partially verifiable | researcher may commit a baseline |
| F-16 | INFO | — | `.git/lost-found` | 309 files = 301 pointer (41 B) + 8 blob dumps (5.5–62 KB) | my earlier "309 pointer files" imprecise; 309 total consistent | none; not modified |
| F-17 | LOW | OPEN | `classify_m4` | exact float comparison, no normalization (`0.1+0.2` vs `0.3`) | boundary-coincident steps can fall either side | researcher timestamp-rounding policy (D-5) |
| F-18 | INFO | — | `ExperimentRunner` artifacts | `asdict(e)` writes the new fields into `single_events.json`; `summary.json` gains new keys | artifact schema widened | note for downstream readers |

No CRITICAL finding.

## C. Claims — verified / partially / not verified / contradicted

**Independently verified:** baseline state; six confirmed rows (A1–A6) behave as specified; strict open interval and fail-closed timestamps; missing T4 is never safe; truncated/empty replays are never safe and never M5; denominator partitions and identities; engine/no-train/unverified events outside pooled train denominators; bare-id and id–cohort contradictions fail closed; lead-in screen default-off, unwired in `src`, insufficient lead-in not a failure, provenance required; `build` never opens media and skips symlinks; manifest counts (858 / 734 / 11,322 / checkpoints / clean verify at audit start); in-place protocols unchanged; proposed schema imported by no `src` file; no fabricated signature/identity/date; D1/D2/R04/B7e/thresholds/ROI still pending; exploratory scope still 11 events; occupancy not implemented; no split/EVAL-AUTH/receipt artifact; allowlist still one identity.
**Partially verified:** "incomplete evidence is never counted as safe or never-protected" (true for end-truncation, **not** for late/absent start — F-04); "callers cannot override a contradictory identity" (true for id-vs-cohort; cohort-vs-flag gap fixed — F-03); "3.6 s from the frozen engine" (numerically identical, but constructed from defaults — F-07); "engine events reach the engine branch earlier" (bare ids only — F-14); "no gate edited beyond a message" (cannot be baselined — F-15); "media excluded before opening" (true for build; verify fixed — F-01).
**Not verified (no authority/no data):** behaviour on real events or real Layer-B ids; the official readiness gate result; the diagnostic runner on real runs; any metric value.
**Contradicted by the code at baseline:** "verification does not read media" (F-01); the unstated assumption that 5A left the diagnostic runner working for unannotated events (F-02).

## D. Researcher decisions required (not resolvable by engineering)
* **D-1 (F-04) Replay start coverage.** Options: (a) require the first retained step to be at/before a stated offset from replay start, else NOT_EVALUABLE `replay_started_late` (zero tolerance = first step at 0.0); (b) minimum: require ≥ 1 retained step before T4, else NOT_EVALUABLE (and update the pre-5A test that pins M5 for "block exactly at T4"); (c) keep and disclose M5 as "replay-relative, start unchecked". *Recommendation:* (b) now, (a) when replay start behaviour is characterised.
* **D-2 (F-05)** keep `no_steps_in_protection_interval` as NOT_EVALUABLE, or revert to "vacuously not premature". *Recommendation:* keep (conservative); report `max_step_gap_s`.
* **D-3 (F-06)** which M3 semantics for the missed-train screen (literal design vs implemented physical rule vs report both). *Recommendation:* report both until chosen.
* **D-4** whether to approve the three 5A.1 corrections (C-1…C-3) as the accepted baseline.
* **D-5 (F-17)** timestamp rounding/normalization policy for boundary-coincident steps.
* **D-6** record-level conventions (F-08/F-09/F-10): null M4 fields when not evaluable; add `cohort`; count unverified-ground-truth events.
* **D-7** wording (F-13) and media-enumeration scope (F-11).
No approval or authorization was requested or assumed.

## E. Changed-file accounting
**Changed:** `src/railway_detection/evaluation/metrics.py` (`7d7083eb…` → `a4af9a79…`); `scripts/mission5a_build_preservation_manifest.py` (`0d3dec4b…` → `41cc06e5…`); `tests/unit/test_mission5a_production.py` (`7bae8cfe…` → `c29e299d…`, one fixture). **New:** `tests/unit/test_mission5a1_audit_regressions.py` (`9b3bf0ba…`); the eight documents in `docs/generated/mission_5a_1/`. **Not touched:** in-place protocols, the 19 modified tracked files, all configs/schemas/`data/`, `.git/`. Outside the repo (scratchpad only): probe scripts and saved copies of the pre-edit `metrics.py`/tool. Full table: change log. **Git:** HEAD unchanged; staged 0; modified-tracked list identical to Phase 0.

## F. Safety declaration
* **Raw media accessed:** No. No `.mov/.mp4/.wav` or other media was opened, previewed, decoded or hashed. Media-like behaviour was tested only with dummy temp files. The manifest `verify` run hashed the 858 recorded **text-like** governing files. No new media-name enumeration was performed (the manifest JSON was read, the tree was not re-walked; `git status` lists untracked paths as before).
* **Real-data processing:** None. No replay, cache, inference, training, experiment, or timing pilot. `load_frozen_config` read the YAML only. The official readiness gate and real dataset-inventory tests were **not** run.
* **Human review / ground truth / Stage-2.1 / promotion / split:** none occurred; no record created or changed.
* **Official evaluation:** not run. **Any approval created:** No (register unchanged: 12 pending, 7 approved, 1 implemented-not-approved, 1 superseded). No EVAL-AUTH, no signature, no identity added.
* **Git:** read-only commands with `GIT_OPTIONAL_LOCKS=0`; no add/commit/push/reset/clean/checkout/restore/revert/fsck. `.git/lost-found/` unmodified.
* **Process note:** a first draft of a replay-start fix (F-04) was applied and then reverted from a saved copy; the final `metrics.py` contains only C-2 and C-3.

I do not claim Mission 5A is accepted. The researcher retains all authority over scientific interpretation, protocol approval, governance, media access and experiment authorization.
