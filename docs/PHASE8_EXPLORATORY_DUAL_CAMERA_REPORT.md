# Phase 8 — Exploratory 11-Event Dual-Camera Ablation: Execution Report

**Project:** Railway Crossing Vision–Audio Fusion Safety System
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`
**Date:** 2026-10-13
**Author:** Claude Sonnet 5
**Status:** Execution complete. Real model inference was run for the first time in this R04 effort, strictly within the authorized 11-event scope.

> **This experiment is exploratory, restricted to 11 events, and does not resolve full-cohort R04.** Full-cohort B3, B4, B6, and B7 remain `BLOCKED_BY_EVIDENCE`, unchanged by anything in this report. No ground-truth performance metric (MTR, POR, or similar) is calculated anywhere in this document. No model prediction is treated as an annotation. No ground-truth candidate was read, approved, or altered.

---

## 1. Authorization and Preconditions

The repository owner authorized this run explicitly: *"I authorize execution of the restricted 11-event exploratory dual-camera ablation, subject to all safeguards below. This authorization does NOT extend to full-cohort B3, B4, B6, or B7."*

All stated preconditions were checked before any inference ran:

| Precondition | Result |
|---|---|
| Phase 7 implementation, tests, hashes, and manifest still match reported state | **Confirmed.** Re-verified `configs/frozen_experiment_v1.yaml` (`999a7970...`), `configs/decision_policy_v1.yaml` (`051c908d...`), all three checkpoint hashes, and the candidate manifest (byte-identical MD5 `de103f15...`) before execution began. |
| Exact 11 included event IDs confirmed from the versioned config (not an old report) | **Confirmed by direct file read** of `configs/exploratory_dual_camera_v1_supported_subset.yaml`: `train_events/event_001, 002, 005, 006, 007, 009, 011, 012, 013, 014, 017`. |
| Every source file's SHA-256 verified against the manifest | **Confirmed.** All 22 files (11 events × 2 cameras) independently re-hashed and compared against `data/manifests/camera_sync_offsets_candidate.yaml`; all matched. |
| Each event's calibration verdict verified; runner rejects invalid/unsupported events | **Confirmed.** All 11 carry `CALIBRATION_SUPPORTED`. Live-tested: feeding `train_events/event_003` (verdict `PROVISIONAL`) directly to `load_validated_sync_aligner` raised `CalibrationNotAcceptedError` as expected. |
| Both authorization flags required by the actual runner | **Confirmed**, live, both before and after the execution described in §2: `--execute` alone and `--execute --authorize-exploratory-run` against the unauthorized config both blocked with exit code 1; `--execute` without `--authorize-exploratory-run` against the *authorized* config (see §2.1) also still blocked. |
| Frozen experiment and decision-policy configurations, and all model checkpoints, preserved | **Confirmed**, before and after execution — see §7. |
| No existing configuration modified in place | **Confirmed** — see §2.1 for how authorization was recorded without editing the already-hashed v1.0.0 exploratory config. |

No precondition failed. Execution proceeded.

---

## 2. Research Question

Recorded verbatim, exactly as specified, into the run's own manifest (a new, per-run artifact — not into any already-hashed configuration file):

> **"Does event-scoped acoustic-lag alignment of the selected front/back camera streams change multimodal evidence and state-machine behavior relative to independent camera processing?"**

Recorded alongside it, verbatim in the same manifest field, the required caveat:

> *"Acoustic-lag reproducibility (the basis of the CALIBRATION_SUPPORTED verdict) is NOT independent validation of true camera hardware synchronization. See `docs/R04_CALIBRATION_VALIDATION_REPORT.md` and the Phase 7 section of `docs/R04_IMPLEMENTATION_AND_UNBLOCK_REPORT.md`."*

Both fields are present and verified in `results/r04_sync_estimation/exploratory_live_run_20261013T194806Z/run_manifest.json` (keys `research_question` and `research_question_note`).

### 2.1 How authorization was recorded without modifying the hashed exploratory config

The brief requires both "do not modify any existing configuration in place" and that the config-side authorization flag be genuinely required. These are reconciled as follows, matching the pattern already established for frozen vs. exploratory configurations in this project:

- `configs/exploratory_dual_camera_v1_supported_subset.yaml` (v1.0.0, hash `ce42a13bb6c4758c8f3e2a092de492a2bec724c50fc03aa58768ad86ea0e6269`) is **untouched**, still ships `authorized_for_execution: false`, and was re-verified byte-identical to its Phase 6/7 content immediately before execution.
- A **new**, separately versioned file, `configs/exploratory_dual_camera_v1.1.0_authorized_20261013.yaml` (hash `ca07cd0f36527ef2296f2483dd39243b0b72db3672eddd17f31d817aa58a9b39`), was created. It is identical to v1.0.0 except `version: "1.0.0" → "1.1.0"`, `authorized_for_execution: false → true`, and a new `authorization_record` block quoting the owner's exact authorization statement, the date, and the unauthorized source config's path and hash.
- `scripts/run_exploratory_dual_camera_subset.py` was given a small, additive `--config` CLI override (defaulting to the unauthorized v1.0.0 path, so running it with no flags behaves exactly as before). This is a script capability addition, not a configuration edit.

The runner was invoked as:
```
venv/bin/python scripts/run_exploratory_dual_camera_subset.py \
  --execute --authorize-exploratory-run \
  --config configs/exploratory_dual_camera_v1.1.0_authorized_20261013.yaml
```

### 2.2 A bug found and fixed during this phase (disclosed, not hidden)

The first launch attempt crashed: `build_run_manifest`'s `config_path.relative_to(REPO_ROOT)` failed because `config_path` (from `--config`, a relative CLI argument) was never resolved to an absolute path before the comparison. **This happened before any model was loaded or any video was decoded** — confirmed by the crash traceback (failure inside manifest construction, prior to the `processor = LayerBEventProcessor(...)` line) and by inspecting the partially-created output directory, which contained only itself (zero files). The empty directory was removed; the fix (`config_path = (...).resolve()`) was applied; the existing authorization-gate regression suite (6 tests) was re-run and confirmed still passing; and the run was relaunched successfully. No inference of any kind occurred during the failed first attempt.

---

## 3. Execution

```
Command: venv/bin/python scripts/run_exploratory_dual_camera_subset.py --execute \
         --authorize-exploratory-run --config configs/exploratory_dual_camera_v1.1.0_authorized_20261013.yaml
Started:  2026-10-13T19:48:06Z
Finished: ~2026-10-13T19:56:06Z (last event's output file mtime; total wall time ~8 minutes for all 11 events' real inference)
Process exit: confirmed cleanly (via `ps` showing no running process after completion)
Output directory (new, unique): results/r04_sync_estimation/exploratory_live_run_20261013T194806Z
```

All 11 events processed in the order listed in the config, each performing real front-camera YOLO vision inference, real back-camera YOLO vision inference, and real Audio V3 inference (no cache reuse — the run's `cache/` subdirectory was empty at the start and was populated fresh by this run alone), followed by validated-offset dual-camera frame fusion and a full state-machine replay via `EventSimulationRunner`. Console output for all 11 events, captured directly (not reconstructed):

```
Processing train_events/event_001 with validated offset +7.4060s ...
  -> 249 decision steps written to .../train_events/event_001
Processing train_events/event_002 with validated offset +4.1867s ...
  -> 163 decision steps written to .../train_events/event_002
Processing train_events/event_005 with validated offset +6.0380s ...
  -> 398 decision steps written to .../train_events/event_005
Processing train_events/event_006 with validated offset +4.5124s ...
  -> 635 decision steps written to .../train_events/event_006
Processing train_events/event_007 with validated offset +8.8801s ...
  -> 192 decision steps written to .../train_events/event_007
Processing train_events/event_009 with validated offset +9.4043s ...
  -> 215 decision steps written to .../train_events/event_009
Processing train_events/event_011 with validated offset +5.2713s ...
  -> 189 decision steps written to .../train_events/event_011
Processing train_events/event_012 with validated offset +5.5679s ...
  -> 376 decision steps written to .../train_events/event_012
Processing train_events/event_013 with validated offset +3.2780s ...
  -> 369 decision steps written to .../train_events/event_013
Processing train_events/event_014 with validated offset +4.0806s ...
  -> 276 decision steps written to .../train_events/event_014
Processing train_events/event_017 with validated offset +4.5654s ...
  -> 419 decision steps written to .../train_events/event_017

Exploratory live execution complete. Outputs in .../exploratory_live_run_20261013T194806Z
```

No warning, error, or traceback appeared during the successful run. No event was skipped. No event outside the 11 authorized was processed. `results/experiments/phase5_full_dataset_run_20261013/` (the existing single-camera baseline) was confirmed untouched throughout (zero files with a modification time after the run started).

---

## 4. Per-Event Analysis

**Observation/interpretation separation:** every value in the tables below was read directly from a persisted output file (the run's `decision_steps.json` per event, its `run_manifest.json`, and its `cache/*.jsonl` raw inference records), re-verified by this report's author via direct inspection, not summarized from the script's own printed claims. Interpretive statements are explicitly marked as such in §4.4 and §5.

### 4.1 Calibration validation (all 11 — observation)

Every event's `calibration_verdict` in the run manifest reads `CALIBRATION_SUPPORTED`; every `front_sha256`/`back_sha256` recorded matches the live-computed hash of the actual video file used (re-verified in §1). The applied `back_offset_s` for each event matches, to the last recorded digit, the value independently re-derived in Phase 7 — see the table in §4.4.

### 4.2 Front- and back-camera detections, audio observations (observation)

| Event | Front frames | Front detections | Back frames | Back detections | Audio windows | Audio windows ≥ 0.3700 (label "train") |
|---|---:|---:|---:|---:|---:|---:|
| `event_001` | 249 | 200 | 231 | 60 | 98 | 0 |
| `event_002` | 163 | 159 | 151 | 167 | 63 | 2 |
| `event_005` | 398 | 294 | 391 | 365 | 158 | 78 |
| `event_006` | 631 | 257 | 635 | 628 | 251 | 2 |
| `event_007` | 192 | 219 | 173 | 158 | 75 | 7 |
| `event_009` | 215 | 444 | 188 | 205 | 84 | 0 |
| `event_011` | 189 | 357 | 187 | 139 | 74 | 0 |
| `event_012` | 376 | 289 | 354 | 282 | 149 | 12 |
| `event_013` | 369 | 363 | 366 | 481 | 146 | 21 |
| `event_014` | 275 | 200 | 268 | 284 | 109 | 7 |
| `event_017` | 408 | 395 | 419 | 522 | 162 | 7 |
| **Total** | **3,465** | **3,177** | **3,363** | **3,291** | **1,369** | **136** |

Every window's raw cached record carries a label and confidence regardless of threshold (e.g. `{"label": "ambient", "confidence": 5.99e-05, ...}` for a clearly negative window) — the "label == train" count is identical to the "confidence ≥ 0.3700" count for every event, confirming the frozen operational threshold (0.3700) was the one actually in effect for this run, cross-checked against the config's own recorded `audio.operating_threshold`.

### 4.3 Fusion evidence, state-machine transitions, gate commands (observation)

| Event | Offset applied | Decision steps | Distinct state transitions | Final crossing state | Reached `CROSSING_CLEAR` | Gate states observed | Max/min gate angle | `FAULT_FAIL_SAFE` count |
|---|---:|---:|---:|---|:---:|---|---|---:|
| `event_001` | +7.4060s | 249 | 182 | `REAR_CONFIRMED` | No | OPEN(12), CLOSING(14), CLOSED(223) | 90°/0° | 0 |
| `event_002` | +4.1867s | 163 | 138 | `REAR_CONFIRMED` | No | OPEN(12), CLOSING(14), CLOSED(137) | 90°/0° | 0 |
| `event_005` | +6.0380s | 398 | 372 | `CROSSING_OCCUPIED` | No | OPEN(12), CLOSING(14), CLOSED(372) | 90°/0° | 0 |
| `event_006` | +4.5124s | 635 | 589 | `CROSSING_OCCUPIED` | No | OPEN(16), CLOSING(14), CLOSED(605) | 90°/0° | 0 |
| `event_007` | +8.8801s | 192 | 165 | `TRAIN_DEPARTING` | No | OPEN(12), CLOSING(14), CLOSED(166) | 90°/0° | 0 |
| `event_009` | +9.4043s | 215 | 190 | `REAR_CONFIRMED` | No | OPEN(12), CLOSING(14), CLOSED(189) | 90°/0° | 0 |
| `event_011` | +5.2713s | 189 | 164 | `CROSSING_OCCUPIED` | No | OPEN(12), CLOSING(14), CLOSED(163) | 90°/0° | 0 |
| `event_012` | +5.5679s | 376 | 337 | `TRAIN_DEPARTING` | No | OPEN(12), CLOSING(14), CLOSED(350) | 90°/0° | 0 |
| `event_013` | +3.2780s | 369 | 342 | `REAR_CONFIRMED` | No | OPEN(12), CLOSING(14), CLOSED(343) | 90°/0° | 0 |
| `event_014` | +4.0806s | 276 | 250 | `REAR_CONFIRMED` | No | OPEN(12), CLOSING(14), CLOSED(250) | 90°/0° | 0 |
| `event_017` | +4.5654s | 419 | 394 | `REAR_CONFIRMED` | No | OPEN(12), CLOSING(14), CLOSED(393) | 90°/0° | 0 |

**Observation, directly read from the above:** for every one of the 11 events, the gate transitions `OPEN → CLOSING → CLOSED` exactly once, then the gate command remains `CLOSED` for the rest of the recorded clip. No event's gate command returns to `OPENING`/`OPEN`. No event reaches `CROSSING_CLEAR`. No `FAULT_FAIL_SAFE` entry occurred in any event (zero duplicate/out-of-order-induced faults, zero sensor-loss faults — consistent with all source media being continuously available real recordings).

**Observation, logical-state chattering:** the crossing *state* (as opposed to the gate *command*) changes very frequently — the "distinct state transitions" column is 66–93% of the step count for every event. Inspecting the state sequences directly (not shown in full here for length; available verbatim in each event's `decision_steps.json`) shows the engine cycling among `TRAIN_PRESENT → CROSSING_OCCUPIED → TRAIN_DEPARTING → REAR_CONFIRMED → TRAIN_PRESENT → ...` repeatedly, never completing a full, uninterrupted 3.0-second clearance dwell. This is consistent with — though this report does not claim to have proven the specific mechanism — the known fact (documented since the original independent audit of this repository, unrelated to R04) that the vision model's `side` label is a member of both `APPROACH_LABELS` and `DEPARTURE_LABELS` in `src/railway_detection/fusion/rules.py`, and `side` is by far the most common detected label in this dataset. **This report does not change, tune, or attempt to fix that behavior** — it is pre-existing decision-policy logic, present in the frozen configuration, and out of this phase's explicitly authorized scope ("Do not... tune thresholds").

### 4.4 Sensor-health, warnings, and rejected observations — explicit limitation

**This cannot be fully reported from the persisted output, and that gap is disclosed here rather than filled in with an unverifiable claim.** `scripts/run_exploratory_dual_camera_subset.py`'s `run_live` writes each event's `decision_steps.json` with only four fields per step (`timestamp_s`, `crossing_state`, `gate_state`, `gate_angle_deg`) — it does not persist `rule_id`, `fault_status`, `explanation`, `source_health`, `health_reasons`, or the fusion collector's `rejected_observations` list, all of which exist on the underlying `DecisionRecord`/`MultimodalEvidenceCollector` objects at runtime but were not wired into this script's output serialization. Consequently:

- **Sensor-health changes**: not independently verifiable from this run's saved files. Indirectly, zero `FAULT_FAIL_SAFE` states appearing in any event's state sequence (§4.3) implies no sustained all-vision-source loss was detected, consistent with all source media being complete, continuously-decodable real recordings — but per-tick health transitions (`HEALTHY`/`STALE`/`RECOVERING`) are not recorded anywhere in this run's output.
- **Warnings and rejected observations** (duplicate-frame, out-of-order, or collector-level rejections): not persisted anywhere this run wrote to disk. The regression tests re-run before and after this execution (§6) confirm the rejection *mechanisms* function correctly in isolation; this run's own output does not let us say whether they fired zero times or some nonzero number of times during this specific execution.
- **Execution errors**: none occurred — the process exited cleanly with no traceback after the one early, pre-inference crash described in §2.2 (which was fixed before any real inference was attempted).

This is recorded as a finding for future work: `run_live` should serialize the full `DecisionRecord` (or at minimum `rule_id`, `fault_status`, and the collector's `rejected_observations` count) per event, matching the richer schema already used by the existing single-camera baseline's `decision_records.jsonl` files (which do carry `resulting_state`-equivalent fields suitable for this kind of analysis — see §4.5).

### 4.5 Comparison against the existing single-camera baseline (technically valid comparison)

The comparison below is valid because **the baseline (B0, from `results/experiments/phase5_full_dataset_run_20261013/`) was produced by the identical decision-engine code** (`EventSimulationRunner` wrapping `MultimodalDecisionEngine`, constructed with the same frozen configuration) — the only difference between B0 and this run is which camera evidence is supplied (front-only vs. synchronized front+back). This is a like-for-like comparison of evidence source, not of different software.

| Event | Dual-camera reached `CLEAR` | Dual-camera final state | B0 (front-only) reached `CLEAR` | B0 final state |
|---|:---:|---|:---:|---|
| `event_001` | No | `REAR_CONFIRMED` | No | `TRAIN_DEPARTING` |
| `event_002` | No | `REAR_CONFIRMED` | No | `TRAIN_DEPARTING` |
| `event_005` | No | `CROSSING_OCCUPIED` | **Yes** | `CROSSING_OCCUPIED` |
| `event_006` | No | `CROSSING_OCCUPIED` | **Yes** | `TRAIN_DEPARTING` |
| `event_007` | No | `TRAIN_DEPARTING` | No | `REAR_CONFIRMED` |
| `event_009` | No | `REAR_CONFIRMED` | No | `REAR_CONFIRMED` |
| `event_011` | No | `CROSSING_OCCUPIED` | No | `CROSSING_OCCUPIED` |
| `event_012` | No | `TRAIN_DEPARTING` | **Yes** | `REAR_CONFIRMED` |
| `event_013` | No | `REAR_CONFIRMED` | No | `TRAIN_PRESENT` |
| `event_014` | No | `REAR_CONFIRMED` | No | `TRAIN_PRESENT` |
| `event_017` | No | `REAR_CONFIRMED` | No | `TRAIN_PRESENT` |
| **Totals** | **0 / 11** | — | **3 / 11** | — |

**Observation:** the dual-camera fused run reached `CROSSING_CLEAR` in 0 of 11 events; the front-camera-only baseline reached it in 3 of 11 (`event_005`, `event_006`, `event_012`) for the *same* 11 events. For the 8 events where neither condition reaches `CLEAR`, the two conditions' final states frequently still differ (e.g. `event_007`: `TRAIN_DEPARTING` vs `REAR_CONFIRMED`; `event_013/014/017`: `REAR_CONFIRMED` vs `TRAIN_PRESENT`), indicating the fused evidence does change the logical trace even when it does not change the gate-reopening outcome.

For completeness, the B1 (front audio only), B2 (front vision + front container-synced audio), and Back_Independent (back-camera-only) baselines were also checked (full per-event detail persisted at `results/r04_sync_estimation/exploratory_live_run_20261013T194806Z/baseline_comparison.json`, not reproduced in full here for length): B1 reached `CLEAR` in 0 of 11 (expected — audio alone never grants clearance, per `RULE_2_AUDIO_SUPPORT_ONLY`); B2 reached `CLEAR` in 2 of 11 of the same events (`event_006`, `event_012`); Back_Independent reached `CLEAR` in 0 of 11. **Interpretation, explicitly marked as such:** this pattern — every single-modality or single-camera condition that uses the front camera's evidence does somewhat better at reaching a clean `CROSSING_CLEAR` than the dual-camera fused condition, while the back-camera-only condition matches the fused condition at 0/11 — is consistent with (not proof of) the back camera's detections dominating the departure-camera staleness and clearance-interruption logic once both cameras' evidence streams are combined into one fused timeline; a firm causal claim would require instrumenting the per-tick rule firings (the exact gap identified in §4.4) and is not made here.

---

## 5. Observations vs. Interpretations — Summary

**Observations (directly read from persisted files, independently re-verified):**
- All 11 authorized events, and no others, were processed; all 11 calibration verdicts were `CALIBRATION_SUPPORTED`; all 22 source-media hashes matched.
- Each event's back-camera offset was applied to produce the recorded master timestamps exactly once (cross-checked programmatically in §6).
- 3,465 front-camera frames, 3,363 back-camera frames, 1,369 audio windows were processed; 136 audio windows scored at or above the 0.3700 operational threshold.
- The gate command transitioned `OPEN → CLOSING → CLOSED` exactly once per event and never returned to `OPEN`/`OPENING` within any of the 11 recorded clips. Zero `FAULT_FAIL_SAFE` states occurred in any event.
- 0 of 11 dual-camera fused events reached `CROSSING_CLEAR`, versus 3 of 11 for the front-camera-only baseline on the identical 11 events, using identical decision-engine code.
- Sensor-health transitions and rejected-observation counts for this specific run are not recoverable from the persisted output (§4.4) — a genuine gap, not a zero result.

**Interpretations (explicitly marked, not asserted as fact):**
- The reduced rate of reaching `CROSSING_CLEAR` under dual-camera fusion is plausibly related to the back camera's detection pattern combined with the known `side`-label ambiguity in the approach/departure rule sets, but the specific causal mechanism is not instrumented in this run's output and is not proven here.
- This pattern should not be read as "dual-camera fusion is unsafe" — in every case where the two conditions differ, the dual-camera result is *more conservative* (stays closed, never reopens within the clip) than the front-only baseline, not less. Whether that conservatism is appropriate, excessive, or simply an artifact of these specific 11 short clips (most of which are well under the 3.0s-dwell-plus-prior-state-time needed to complete a clean clearance cycle even in the single-camera baseline) is a scientific judgment for the researcher, not a determination this report makes.

---

## 6. Post-Run Verification

| Check | Result |
|---|---|
| Output directory contains only the 11 authorized events | **Pass.** `scripts/validate_exploratory_run_output.py` (new, written this phase) confirms the directory's event set equals exactly the 11 configured events — no extra, no missing, no negative controls, no engine-only event. |
| JSON/JSONL integrity and required fields | **Pass.** Every `decision_steps.json` parses as valid JSON, is a non-empty list, and every step carries all four required fields. Every cache `.jsonl` file parses line-by-line as valid JSON (used directly for the analysis in §4). |
| Offsets applied exactly once | **Pass**, checked two ways: (a) the run manifest's recorded `back_offset_s` for every event matches the independently-regenerated candidate manifest's value to floating-point precision (`scripts/validate_exploratory_run_output.py`); (b) the same direct-timestamp-arithmetic check used in Phase 6/7's `test_synchronization_applied_exactly_once` integration test continues to pass against the live code this run used (re-run in §6 below). |
| No unsupported timestamps were fused | **Pass.** All 11 manifest entries read `"verdict": "CALIBRATION_SUPPORTED"`; `load_validated_sync_aligner` was re-confirmed, live, to raise on a `PROVISIONAL` event before this run was launched (§1). |
| Run used the expected configuration and checkpoint hashes | **Pass.** `run_manifest.json`'s `base_frozen_config_canonical_hash` and the newly-added `frozen_experiment_config_canonical_hash_at_run_time` field both read `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`, matching the value re-verified immediately before and after execution. |
| Relevant integration and safety tests re-run | **Pass.** `tests/unit/test_independent_safety_invariants.py`, `test_production_dual_camera_integration.py`, `test_validated_sync_aligner.py`, `test_collector_fail_closed_fusion.py`, `test_exploratory_subset_authorization_gate.py` — **43 passed**, exit code 0, run both immediately before and immediately after the live execution. |
| Frozen configuration and decision-policy hashes unchanged | **Pass** — see §7. |
| All three checkpoint hashes unchanged | **Pass** — see §7. |
| `data/ground_truth/` untouched | **Pass** — see §7. |
| Changes left unstaged and uncommitted | **Pass** — see §7. |

---

## 7. Final Integrity Verification

```
configs/frozen_experiment_v1.yaml canonical hash:            999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e  (UNCHANGED)
configs/decision_policy_v1.yaml canonical hash:               051c908d4db23687db33cbc8349945b241a0735b362413be876d7017a5eacc9d  (UNCHANGED)
configs/exploratory_dual_camera_v1_supported_subset.yaml (v1.0.0) hash: ce42a13bb6c4758c8f3e2a092de492a2bec724c50fc03aa58768ad86ea0e6269  (UNCHANGED)
configs/exploratory_dual_camera_v1.1.0_authorized_20261013.yaml (new) hash: ca07cd0f36527ef2296f2483dd39243b0b72db3672eddd17f31d817aa58a9b39

Vision checkpoint SHA-256:        3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd  (UNCHANGED)
Audio V3 checkpoint SHA-256:      ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782  (UNCHANGED)
Prohibited Audio V2 SHA-256:      59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5  (UNCHANGED)

Calibration manifest (camera_sync_offsets_candidate.yaml) MD5: de103f1597b831d2b1dedc1a31340fd3  (UNCHANGED)

data/ground_truth/:        untracked, untouched (git status identical before/after this phase)
results/experiments/phase5_full_dataset_run_20261013/: zero files modified during this run (checked via mtime)

Git HEAD:                  d4db94d4a4ea83ae4c510d65dfc99c5d6798304b  (unchanged)
Git staged changes:        none
Git status:                13 modified (unchanged count), 150 untracked

No full-cohort B3/B4/B6/B7 condition was executed. No threshold was tuned. No model was retrained.
No frozen primary configuration was modified.
```

---

## 8. Deliverables

- This report: `docs/PHASE8_EXPLORATORY_DUAL_CAMERA_REPORT.md`.
- New experiment output directory: `results/r04_sync_estimation/exploratory_live_run_20261013T194806Z/` (run manifest + per-event `decision_steps.json` + fresh inference cache for all 11 events + `baseline_comparison.json`, the full data behind §4.5's table including B1/B2/Back_Independent). Never overwrites `results/experiments/phase5_full_dataset_run_20261013/` or any prior output.
- New authorization record (separately versioned, original config untouched): `configs/exploratory_dual_camera_v1.1.0_authorized_20261013.yaml`.
- Script changes (additive, not config edits): `--config` and `--research-question` CLI options added to `scripts/run_exploratory_dual_camera_subset.py`; the path-resolution bug from §2.2 fixed.
- New validation tool: `scripts/validate_exploratory_run_output.py`.
- Append-only entry in `reports/progress.md`.

## 9. What This Experiment Does Not Show

Repeated here because it bears repeating: this is 11 events, acoustically calibrated with no independent visual corroboration, run once, with no ground-truth comparison of any kind. It shows that dual-camera fusion *changes* state-machine behavior relative to single-camera processing on these 11 clips — the research question's first clause is answered, observably, in the affirmative. It does not show whether that changed behavior is more or less *correct* relative to what actually happened at each crossing, because no approved ground truth exists to compare against, and none was consulted or approved in the course of producing this report.
