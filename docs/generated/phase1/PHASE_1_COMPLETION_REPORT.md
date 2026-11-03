# Phase 1 Completion Report — Engineering and Metric-Contract Closure (Mission 5B)

**Status: PASS WITH CONDITIONS.** All five confirmed decisions (DEC-C01 … DEC-C05) and F-19 are implemented and covered by synthetic tests. Conditions: the plan's lint-cleanup work package was not done (Section 11, item 1), and four items need a researcher look (Section 11).

This report is a proposal for the researcher's review at Checkpoint Gate 1. It is not an approval, a signature, a protocol-hash binding or an execution authorization. Nothing here advances to Phase 2.

Written 2026-11-01. Authority: the researcher's acceptance of the five Gate 0 decisions in `MASTER_FIVE_PHASE_IMPLEMENTATION_PLAN_20261101.md`.

---

## 1. Initial repository state (read-only audit, before any edit)

| Item | Observed |
|---|---|
| Path / branch / HEAD | `/Users/sayemuddin/Desktop/Train_automation` · `main` · `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` |
| Staged files | **0** |
| Modified tracked files | **19** — identical to the plan's list (Section 2.1 of the plan) |
| Untracked entries (`git status --short`, `GIT_OPTIONAL_LOCKS=0`) | **359** |
| `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` / `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` SHA-256 | `d100c1e6…` / `7c183b32…` — match the plan |
| Manifest at start (`mission_5a/REPRODUCIBILITY_MANIFEST_20261101_M5A.json`) | `verify`: 855 ok · 0 missing · 0 refused · **3 changed** (`mission5a_build_preservation_manifest.py`, `metrics.py`, `test_mission5a_production.py`) — exactly the three files Mission 5A.1 documented as changed |
| Mission 5A.1 hashes | `metrics.py` `a4af9a79…`, manifest tool `41cc06e5…`, `test_mission5a_production.py` `c29e299d…`, `test_mission5a1_audit_regressions.py` `9b3bf0ba…` — all equal the values in the 5A.1 change log |
| Baseline tests (pre-edit) | `674 passed in 15.46s` (the 20-file synthetic set of Section 6) |
| Baseline Ruff (Phase 1 target files) | `All checks passed!` |

**Baseline match:** the repository matched the plan's baseline. No discrepancy required stopping.

Phase 1 target files, pre-edit SHA-256, are in Section 3.

## 2. Decision implementation status

| Decision | Status | Where |
|---|---|---|
| **DEC-C01 (C01-B)** zero-origin coverage before M5 | Implemented | `classify_m4` in `metrics.py`. First retained step ≥ T4 → `NOT_EVALUABLE` / `replay_started_at_or_after_T4`. Would-be M5 with first step > 0.0 → `NOT_EVALUABLE` / `replay_started_late`. M5 needs first step = 0.0 on the grid and last step ≥ T4. Witnessed violations inside `(t_blocked, T4)` stay `EVALUABLE`. M4 is not excluded for a late start. No tolerance. Historical shorthand fixture repaired. |
| **DEC-C02 (C02-A)** empty interval stays `NOT_EVALUABLE` | Implemented (behavior was already this; now pinned, with diagnostics) | Reason `no_steps_in_protection_interval`. `first_blocked_s`, `last_step_s`, `interior_step_count`, `max_step_gap_s` retained; new `first_step_s` added. No tick or gap is used to infer protection. |
| **DEC-C03 (C03-A)** physical screen primary, literal design M3 secondary | Implemented in `lead_in_screen.py` | `LeadInScreenResult.m3_design_literal_evaluable` added. `insufficient_lead_in` and `lead_in_unverifiable` stay distinct. Screen is still off by default and not used by the official runner. **Not** propagated onto `SingleEventEvaluation` or the summary (Section 11, item 5). |
| **DEC-C04 (C04-A)** accept the three 5A.1 fixes as baseline | Accepted | Baseline hashes verified (Section 1). The 68 5A.1 tests still pass. Six 5A.1/5A/pre-5A test assertions were intentionally updated because later decisions supersede them (Section 4). |
| **DEC-C05 (C05-A)** `round(float(t), 6)` grid | Implemented | New leaf module `evaluation/timebase.py`. Applied to both sides of each comparison in `classify_m4`, the `evaluate_run` ordering, entry-matching and clearance-latency checks, `clock_aware` boundary mapping and boundary flags, and the lead-in screen. |
| **F-19** multi-system propagation | Implemented | `clock_aware.evaluate_event_replay`. Details in Section 5. |
| F-07 / DEC-A01 config provenance | Implemented | Section 5. |
| F-08, F-09, F-10 record conventions | Implemented | Section 5. |
| DEC-A02 manifest pruning | Implemented | Section 7. |

## 3. Exact files changed, with before/after SHA-256

Backups (outside the repository, created with `cp -n`, none pre-existing, each verified byte-identical to its pre-edit file at copy time):
`/private/tmp/claude-501/-Users-sayemuddin-Desktop-Train-automation/81212977-2b5d-4682-b8f7-e0d4af9a2e08/scratchpad/phase1_backup/` (path separators in the original path replaced by `_`; the file name is the original path with `/` → `_`).

### 3.1 Existing files edited (7)

| File | Before (= backup) | After |
|---|---|---|
| `src/railway_detection/evaluation/metrics.py` | `a4af9a79289f493b8b627831434301f981d29b430a56b6c4e210c01e3082c2f7` | `69f473022ee97ded8d2728be47718159c4fb11d3260e8821b86c2a4ef562874b` |
| `src/railway_detection/evaluation/clock_aware.py` | `681b217a3a0595a5a31d8da1aa986e351a7cc5edb47eade5ceedb5d3281301bf` | `2c2054c3aeeaafd7570d9eef8016ab56fde15cead2c53f641a588c3bc73f5a4b` |
| `src/railway_detection/evaluation/lead_in_screen.py` | `781b22f21d172d93f689ffd433dea43c59c15f028223f45acd9313cf3f42fde3` | `9a317c1865f7a39b27ed767c7b015ffba86a7ca4cc34e003ae5580c933616ac7` |
| `scripts/mission5a_build_preservation_manifest.py` | `41cc06e5322fb6b36586e0d389784a2e38b53624a9f139c9910a8f95e4d0f3e5` | `0b547c041df1c8782a897f9d2fafa22f4ee62e5ee3b4203b0a555e8775b6935c` |
| `tests/unit/test_phase12_metric_arithmetic.py` | `8e3bd57975a5971cc1ed906db7df70ae1375b28ea62000758a899cf426130e1d` | `e8edd1fbf63ca36f6f5320860183fd8b2d67948f8b6c5700ee229b502291e3e5` |
| `tests/unit/test_mission5a_production.py` | `c29e299dba562b4ee8504ffe8603a0609ed5d8adac1dc7b3888297bea870d89b` | `68bbe1db68fe5ffebfaabfca15d23bed9ad51468bf5e40aa051ffb9c0fc941bd` |
| `tests/unit/test_mission5a1_audit_regressions.py` | `9b3bf0ba77e5d253a1beef73a4e554e95e8a4ba85d647f7190e1cd6c29adf61c` | `d8b8f42c226fdbfa9625fdf8cd5c5c8ccc92f7682d0005a0604ef303ff61d22d` |

Two further files were backed up as precaution but **not edited** (hashes identical to backup): `tests/unit/test_phase12_official_replay.py`, `tests/unit/test_mission4e2_m4_occupancy_contract.py`.

### 3.2 New files (4)

| File | SHA-256 |
|---|---|
| `src/railway_detection/evaluation/timebase.py` | `0aaf6a03ad9a750d56427a7ae2b24c283858dd4cf7e9d6b9a25d00540f40cc5e` |
| `tests/unit/test_phase1_metric_closure.py` | `2ce6bac3d858071da093739d7ae0e5e06978670c85f1929d3bf488545304c225` |
| `docs/generated/phase1/REPRODUCIBILITY_MANIFEST_PHASE1.json` | `6db2364a346c8026598625ff050cfd50bbad83934f2ea92f9d7be9f9f59dd13a` |
| `docs/generated/phase1/PHASE_1_COMPLETION_REPORT.md` | this file (not hashed, to avoid self-reference; it is also not in the manifest) |

**Rollback:** restore any edited file by byte copy from the backup directory (no Git command needed). Delete `timebase.py` only together with the edits that import it.

**Not touched:** all 19 modified tracked files (list verified identical after the work), `configs/**`, `data/**`, `.git/**` (including `lost-found`), `authorized_reviewers.json`, every governance record.

## 4. Existing assertions intentionally changed (and why)

| Test | Change | Reason |
|---|---|---|
| `test_phase12_metric_arithmetic.py::test_m5_never_protected_…` | The shorthand fixture `late` gained unblocked steps at 0–4 s | It claims "first block exactly at T4" but had no pre-T4 steps; that is now correctly not M5. Now a genuine full-coverage scenario (DEC-C01, brief §7.1). |
| `5A1::test_open_replay_start_coverage_is_not_checked` → `test_replay_start_coverage_is_required_for_m5` | Flipped | It pinned the open question that DEC-C01 resolves. |
| `5A1::test_opening_exactly_at_t4_is_excluded_just_before_is_included` | T4 `5.0000001` → `5.000001` | A 0.1 µs difference collapses on the DEC-C05 grid by design; 1 µs stays distinct. |
| `5A1::test_no_timestamp_normalization_exact_comparison_documented` | Renamed/comment only (assertions unchanged) | Its name said "no normalization". |
| `5A1::test_screen_is_off_by_default_and_unwired_in_src` | Expected user list now includes `clock_aware.py` | `clock_aware.py` forwards an optional default-off argument (Section 5). Guard still requires the official runner and every other module to be free of it; Phase 1 test also asserts `evaluation_runner.py` contains no `lead_in`. |
| `5A1::test_build_opens_only_allowlisted_regular_files` and `5A::test_media_and_output_trees_are_never_opened_or_hashed` | `generated_output_tree` now absent by default; present only with `count_excluded_trees=True` | DEC-A02. |

## 5. What changed in the code

**`metrics.py`**
- `M4Classification` gains `first_step_s` (default `None`; backward compatible). New constants `M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4`, `M4_REASON_REPLAY_STARTED_LATE`, `REPLAY_ORIGIN_S = 0.0`; both reasons added to `M4_INCOMPLETE_REPLAY_REASONS`.
- `_validated_replay_timestamps` returns grid-normalized timestamps. Non-finite/negative raw values and non-strictly-increasing grid values raise `ValueError` as before. **New:** two raw-distinct steps that collapse onto one grid point are rejected.
- `SingleEventEvaluation.cohort` (DEC-B03), set on every `evaluate_run` return path. `evaluable=False` train records now carry `m4_status = m4_reason = m4_replay_complete = None` (DEC-B02).
- `CohortEvaluationSummary.unverified_ground_truth_count` and `excluded_train_events_count` (DEC-B04), also in `to_dict()`. Partition identity: `total = eligible + no_train + engine + unverified + excluded_train`. Priority engine > unverified > no-train > train. They add reporting only; no denominator changed.
- `aggregate_cohort` additionally refuses a record whose `cohort` contradicts its cohort-qualified id. Duplicate event ids (bare or qualified) are still refused exactly as before; I did **not** loosen that to allow bare ids that differ only by cohort.

**`clock_aware.py` (F-19)**
- The M4/M5 record (`premature_opening`, `never_protected`, `m4_status`, `m4_reason`, `m4_replay_complete`) is taken **as one unit** from a system that carries T4 on its clock: the first whose classification is definite, else the first T4-bearing system (carrying its `NOT_EVALUABLE` reason), else — T4 mappable nowhere — the primary system (`t4_missing`).
- Why not "first system with `m4_status` not None": every system gets an `m4_status`, and a front stream with no T4 returns `NOT_EVALUABLE / t4_missing`, which would overwrite the back stream's real answer. A mutation test reproduces exactly this failure (Section 8).
- `missed_train_screen` / `lead_in_available_s` come from the first T1-bearing system that ran the screen; a named replay-side reason (M5, incomplete replay, screen) replaces the generic `no_usable_replay_observation`.
- `evaluate_event_replay` gained optional keyword arguments `lead_in_min_block_latency_s` and `lead_in_latency_source` (default `None` = screen off). They exist so propagation can be exercised through the production function. T0 is mapped onto each clock like any boundary. A T0 that is censored, uncertain, unobservable or unmappable yields `lead_in_unverifiable`, never "visible from zero". `evaluation_runner.py` was not changed and does not pass them.
- Behavior change to note: in the M4 window, `premature_opening` now follows the same selected system as `never_protected`. Before F-19 it came from "first system with a non-None value". They differ only when two systems conflict (e.g. fused says M5, back says clean M4); the record no longer mixes both.
- Cohort is stamped on train, no-train and engine records.

**`lead_in_screen.py`**
- `m3_design_literal_evaluable` on `LeadInScreenResult` (T1 observable and (T0 observable or T1 ≥ latency)). The five-cell comparison is covered, including the two cells where the rules differ.
- `derive_min_block_latency_s(..., config=None)`: with a `FrozenExperimentConfig` the engine, gate model and tick come from it (`tick_s` defaults to `config.timing.tick_s`; contradicting values and `config` + `runner` together raise). `derive_min_block_latency_with_provenance(config)` returns `(latency, source)`, where `source` = `synthetic_replay_of_frozen_configuration:constant_front_detection_conf0.9:tick_s=0.2:config_canonical_sha256=<hash>`. It does not call the value a threshold. The hash is the canonical-content hash (`config.config_hash`), not the raw-file `shasum`; the label says so.
- Observed: at the frozen 0.2 s tick the derived value is 3.6 s (`pytest.approx(3.6)` in the new tests). It is a synthetic replay result, not an approved safety threshold.
- Timestamps and the available lead-in are compared on the grid (3.8 − 0.2 no longer fails 3.6 by float noise).

## 6. Test results

All commands run from the repository root with `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`, `.venv/bin/python`. Synthetic unit tests only.

**Final full applicable suite** (the 20-file set Mission 5A.1 used, plus the new file and two synthetic-declared files):
```
.venv/bin/python -m pytest tests/unit/test_event_metrics.py tests/unit/test_mission2_pipeline_integrity.py \
  tests/unit/test_mission3_reproducibility_and_provenance.py tests/unit/test_mission4a_governance_and_stage21_safety.py \
  tests/unit/test_mission4d_governance_integrity.py tests/unit/test_mission4e2_m4_occupancy_contract.py \
  tests/unit/test_mission5a_production.py tests/unit/test_mission5a1_audit_regressions.py \
  tests/unit/test_phase12_documented_metrics.py tests/unit/test_phase12_metric_arithmetic.py \
  tests/unit/test_phase12_governance.py tests/unit/test_phase12_input_contracts.py \
  tests/unit/test_phase12_official_replay.py tests/unit/test_phase12_evaluation_runner.py \
  tests/unit/test_reproducibility_audit.py tests/unit/test_research_contracts.py \
  tests/unit/test_cache_phase12_adapter.py tests/test_phase12_ground_truth_loader.py \
  tests/test_phase11_12_readiness_gate.py tests/test_phase11_cohort_qualified_identity.py \
  tests/unit/test_phase1_metric_closure.py tests/unit/test_descriptive_only.py \
  tests/unit/test_metadata_only_audit.py -p no:cacheprovider -q -rs
→ 804 passed in 12.09s      (0 failed, 0 skipped; `-rs` printed no skip lines)
```
Per-file: `test_phase1_metric_closure.py` 99 passed · `test_mission5a1_audit_regressions.py` 68 passed · `test_mission5a_production.py` 88 passed · `test_phase12_metric_arithmetic.py` 22 passed.

**Run history (not hidden):**
1. Pre-edit baseline, the 20-file set: `674 passed in 15.46s`.
2. After the production edits, before updating tests: `4 failed, 670 passed` — the three superseded pins in Section 4 plus the "unwired" guard.
3. After updating those: `1 failed, 673 passed` — `test_media_and_output_trees_are_never_opened_or_hashed` (DEC-A02 default flip). A first attempt at fixing it had a bug in my own test edit (`_tree()` called twice) and failed once more.
4. `674 passed`, then `804 passed` with the new file and the two added files.

**Not run, by the synthetic-only rule:** `test_readiness_audit.py` (reads the real `data/ground_truth` tree), the audio tests (reference the real corpus/manifests), `test_real_dataset_inventory.py`, `test_layer_b_loader.py`, vision/YOLO/pipeline tests, integration/smoke tests, the official readiness gate. The 20 files inherited from 5A.1's synthetic designation were not re-audited line by line for file reads in this mission; the two I added were screened by grep for media/real-path references.

**Coverage of your 18 required categories** (all in `tests/unit/test_phase1_metric_closure.py` unless noted): 1–6 `TestReplayStartCoverage`; 7–9 `TestEmptyProtectionInterval`; 10–13 `TestClockAwareM4M5Propagation` and `TestClockAwareLeadInPropagation`; 14 `TestTimestampNormalization`; 15 `TestUnevaluableRecordConsistency`; 16–17 `TestCohortIdentityAndAggregation`; 18 `TestMission5A1FailClosedBehaviourIsPreserved` plus the 68 existing 5A.1 tests. Added: `TestLeadInScreenAndLiteralM3` (DEC-C03/A01) and `TestManifestNoMediaEnumeration` (DEC-A02).

## 7. WP 1.6 — preservation manifest

- `scripts/mission5a_build_preservation_manifest.py`: `build_manifest(..., count_excluded_trees=False)`. By default `os.walk` drops directories equal to an `OUTPUT_TREES` entry (`data/raw`, `data/processed`, `results`, `experiments`, `outputs`, `models`, `scratch`, `reports`, `research/figures`) from `dirnames`, so they are never listed. `--count-excluded-trees` restores the old counting. The manifest records `count_excluded_trees` and `pruned_output_trees`. Test spies on `os.scandir`/`os.listdir` and shows no listing under those trees.
- Build (a new file; the tool refuses to overwrite):
```
python3 scripts/mission5a_build_preservation_manifest.py build --root . \
  --out docs/generated/phase1/REPRODUCIBILITY_MANIFEST_PHASE1.json --frozen-config /nonexistent/no_checkpoint_hashing.yaml
→ wrote docs/generated/phase1/REPRODUCIBILITY_MANIFEST_PHASE1.json: 872 entries
python3 scripts/mission5a_build_preservation_manifest.py verify --root . --manifest docs/generated/phase1/REPRODUCIBILITY_MANIFEST_PHASE1.json
→ ok 872 · missing 0 · changed 0 · refused 0 · clean: true
```
- 872 entries = 858 (Mission 5A) + 14 new governing files: the master plan, the 5A execution report, the 5A manifest, the eight 5A.1 documents, `timebase.py`, the 5A.1 test file, the Phase 1 test file (the list in the tool output sums to 14). Six pre-existing entries changed hash — exactly the files in Section 3.1 other than the 5A.1 test file (which was not in the 5A manifest). No entries removed. The other 852 hashes match the 5A manifest.
- The old tool counted 11,322 files under the output trees to produce its tally; the new default build lists none of them.
- Disclosures: (a) I passed a non-existent `--frozen-config` so the two binary model checkpoints were **not** read or hashed; `frozen_checkpoints` is `[]`. Phase 1 has no checkpoint involvement; the earlier manifest did hash them. (b) The tool does read and SHA-256-hash text files under `data/governance`, `data/ground_truth`, `data/manifests`, `data/splits` (181 `data/*` entries: 138 json, 31 md, 11 jsonl, 1 yaml) — the same behavior as Mission 5A. Contents were not parsed or inspected. (c) This report is not in the manifest. (d) `git ls-files` / `git status --porcelain`, which the tool runs, are Git's own enumeration and are unchanged by the pruning. Names stay in memory; nothing is printed or opened.
- `docs/generated/mission_5a/REPRODUCIBILITY_MANIFEST_20261101_M5A.json` was left unedited; it now verifies with the 6 changed paths above.

## 8. Mutation check (does the suite actually fail when the rule is broken?)

On a scratch copy of `src/` (not in the repository), each of these single changes was applied and `test_phase1_metric_closure.py` re-run (pytest `-o pythonpath` override):

| Mutant | Result |
|---|---|
| Control (unmodified copy) | 99 passed |
| `normalize_timestamp` returns the raw float | 12 failed |
| `classify_m4` without the replay-start checks | 13 failed |
| `clock_aware` takes M4 from the first system ("naive merge") | 9 failed |
| `never_protected` not propagated | 4 failed |
| `m4_status` not nulled for unevaluable records | 1 failed |

One further mutant (a "screen exclusion cannot be re-admitted by another clock" branch) caused no failure. I determined it could not change behavior for any reachable input (a second clock cannot map T0 and is itself unverifiable), so I **removed that code** instead of keeping an untestable branch.

## 9. Ruff

```
.venv/bin/ruff check src/railway_detection/evaluation/metrics.py src/railway_detection/evaluation/clock_aware.py \
  src/railway_detection/evaluation/lead_in_screen.py src/railway_detection/evaluation/timebase.py \
  scripts/mission5a_build_preservation_manifest.py tests/unit/test_phase1_metric_closure.py \
  tests/unit/test_mission5a_production.py tests/unit/test_mission5a1_audit_regressions.py \
  tests/unit/test_phase12_metric_arithmetic.py --no-cache
→ All checks passed!
```
Pre-existing findings in files **not** edited (not fixed): `preflight_validator.py` 36 · `batch_multimodal_annotator.py` 16 · `test_mission2_pipeline_integrity.py` 7 (the plan's 59) · `descriptive_only.py` 1 (E501) · `metadata_only_audit.py` 1 (E501).

## 10. Final Git state

`HEAD` unchanged `d4db94d4…`; **staged: 0**; modified tracked: **19** (name-for-name identical to the original list; the two protocol hashes unchanged); untracked entries: **361** (359 + `timebase.py` + `test_phase1_metric_closure.py`; `docs/generated/` was already an untracked directory). No `git add/commit/push/reset/clean/checkout/restore/revert/stash/fsck` was run. `.git/lost-found/` was not touched. Only the read-only `git status`, `diff --cached --name-only`, `rev-parse`, `ls-files` (via the manifest tool) were used.

## 11. Unresolved issues and their impact

1. **Lint work package not done (condition).** The plan's WP 1.4 included clearing 59 pre-existing Ruff findings in three untouched files; your instruction redefined WP 1.4 as timestamp normalization and forbade touching unrelated files, so I did not touch them. The plan's acceptance criterion "zero Ruff across the three previously lint-dirty files" is therefore unmet. No behavior impact. Needs your decision whether to authorize it.
2. **M5 does not require dense pre-T4 sampling (needs a decision).** DEC-C01 requires zero-origin start and reaching T4 only. A sparse replay such as steps at 0.0 and 30.0, never blocked, with T4 = 5.0 is classified M5 because nothing in `[0, 5)` was witnessed. This is the M5 analogue of DEC-C02. Official replays are produced at the 0.2 s tick from 0.0 (per the plan's reading of `replay_producer.py`), so the practical risk is low; I did not invent a density rule.
3. **M4 with a late start.** M4 begins at the observed first blocked step (your instruction). A replay starting already blocked cannot reveal an earlier close-and-reopen. Accepted by the decision; recorded so it is not mistaken for coverage of `[0, T4)`.
4. **Censored T0 without a direction is treated as unverifiable.** The ground-truth loader has `censored_boundaries` but no censoring direction, so the clock-aware screen cannot declare "left-censored" and refuses to assume visibility from 0. Fixing this needs the Stage-2.1 direction field to reach the loader — Phase 3/4.
5. **Literal design M3 is on `LeadInScreenResult` only.** It is not on `SingleEventEvaluation` and there is no summary count, so a side-by-side MTR denominator table is not yet available. Deferred to Phase 4 WP 4.2, together with wiring the screen into evaluation manifests (still not wired).
6. **Behavior changes with real but small blast radius:** steps that collapse onto one microsecond now raise; `max_step_gap_s` and `clearance_latency_s` are grid-rounded; the entry-step match (`≤ 0.25 s`, a pre-existing matching window) compares on the grid; the M4-window `premature_opening` merge follows the selected system (Section 5). `summary.to_dict()` has two new keys, so canonical hashes of serialized summaries differ from earlier runs — expected for DEC-B04, and no real result had been produced yet.
7. **New file `timebase.py` is outside the plan's file list.** Needed to avoid a circular import (`metrics` imports `lead_in_screen`). Easy to relocate.
8. **Lead-in argument added to `evaluate_event_replay`** (not in the plan's file list) so F-19 screen propagation is testable without a test-local reimplementation. It is off by default and unused by the official runner.
9. **The prior checkpoint hashing is absent from the Phase 1 manifest** (Section 7a).
10. **Existing-suite provenance:** the 20-file synthetic set was taken from Mission 5A.1; this mission did not independently re-audit each for file reads.
11. **3.6 s** is stated only as the synthetic-replay value of the frozen configuration at its 0.2 s tick. No approval is implied.

## 12. Prohibited-operations confirmation

Not performed: opening, previewing, decoding or hashing any `.mov/.mp4/.wav/.mp3` (the old output-tree counting that enumerated them was disabled by default and not run); inference, training, real replay, cache generation, timing pilot or experiment rerun; real dataset processing or human review; Stage-2.1 promotion, review records or ground-truth edits; split/manifest promotion; EVAL-AUTH or descriptive-evaluation authorization; creation/signing/approval of any GOV/EXP/AUTH record; edits to `authorized_reviewers.json`, governance validators or readiness checks; changes to the 11-event R04 scope or addition of `train_events/event_010`; B7e numerics, ROI approval or threshold calibration; occupancy-duration implementation; paper claims.

Read-only accesses that did occur, stated for accuracy: Git metadata; text files of the repository (including SHA-256 hashing of governance/ground-truth/manifest/split *metadata* text files by the manifest tool, Section 7b); `configs/frozen_experiment_v1.yaml` parsed by `load_frozen_config` in tests (YAML only; no checkpoint verification was called).

**Phase 2 has not been started.** Awaiting the researcher's inspection and explicit acceptance of this report and the code diffs.
