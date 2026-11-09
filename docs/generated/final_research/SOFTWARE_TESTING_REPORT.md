# Software Testing Report

All figures are from executions on the current tree (HEAD 25bab63 plus the
Mission 3 additions), run 2026-11-08/09. Full outputs retained in the
mission working records.

## Suites

| Suite | Result |
|---|---|
| Full guarded suite (`pytest tests/`, importlib mode) | **3,787 passed / 37 failed / 0 errors** (3,824 collected, 104.6 s) |
| Policy & fusion tests (Phase 9/10/10.1, decision engine, collector fail-closed, sensor health) | **60/60 passed** |
| Mission 3 synthetic battery (`m3_synthetic_battery/2`, 13 scenarios × 2 engines) | **46/46 checks passed** (run 1: 35/42 — the 7 failures were harness expectation errors about v1, corrected against source and traces; run 1 preserved) |
| Mission 3 multimodal engine unit tests (new) | **8/8 passed** |

Historical comparison: Mission 43 reported 3,700 passed / 84 failed /
31 errors of 3,815 under its own runner. The current run collects 9 more
tests and produces materially fewer non-passing results; the difference is
runner environment, not code change (no production code was modified by
the historical missions between those runs, and Mission 3's only
production-code change is one additive module).

## Classification of the 37 failures (zero are code defects)

1. **Stale sealed-catalog bindings — 23.** Missions 26/27/28 tests consume
   the Mission 26 documentary catalog, which binds README.md by hash.
   Mission 2 (user-authorized repository cleanup) rewrote README.md, so
   the catalog correctly reports `stale source-document manifest:
   README.md`. These are frozen historical fixtures detecting an
   authorized change. Disposition: disclosed here; the catalogs are NOT
   rebound (rebinding would rewrite sealed evidence).
2. **Process-isolation assumptions — 4.** Tests asserting that torch /
   CLI / decoder modules are absent from `sys.modules` hold only in a
   bare interpreter; verified 2026-11-09 that they fail even in a
   single-file pytest run, because the repository's conftest imports
   production modules into the session. Harness-dependent by
   construction.
3. **Child-process environment — 8 (pass on re-run).** Tests spawning
   `sys.executable -c "import railway_detection…"` need `PYTHONPATH=src:.`
   in the environment; pytest's `pythonpath` config covers only the
   parent process. With the variable set, the mission 22/24/25 clusters
   pass (562 passed in the triage re-runs).
4. **Access-classification manifest gap — 1 (FIXED by this mission).**
   The committed manifest had no entry for
   `tests/synthetic_mission44/test_display_rotation.py` (pre-existing)
   or for Mission 3's new test file. Mission 3 added both entries
   (category UNKNOWN, pending executed review, per the generator's
   convention for new sources; summary counts updated to 170 files) —
   after which the classification tools suite passes **58/58**
   (verified 2026-11-09). In a post-commit full-suite run this failure
   therefore disappears (expected: 3,788 passed / 36 failed).
5. **Media-authorization policy exception — 1.**
   `test_dry_run_validates_all_eleven_events_against_live_manifest`
   requires an AUTH-MEDIA-ACCESS record to hash raw media;
   `AUTH_MEDIA_ACCESS_NOT_GRANTED` is the designed behaviour when no such
   record exists. It can pass only after a genuine media-access
   authorization is recorded.

## New tests added by Mission 3

- `tests/unit/test_m3_cache_only_engine_multimodal.py` (8 tests):
  back-record validation in both serializations, source stamping
  (camera_2), PTS-mismatch and wrong-source rejection, DUAL_* refusal
  without a two-camera SyncAligner, master-time window extension
  (frames produced beyond the raw-timestamp bound), DUAL_VISION_AUDIO
  execution, and B0 delegation to the frozen engine — all on synthetic
  temp trees.
- `scripts/run_m3_synthetic_battery.py` is an executable scenario battery
  (not a pytest suite); its traces and summaries are the evidence for the
  failure-injection and fail-safe deliverables.
