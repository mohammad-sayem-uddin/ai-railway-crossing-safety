# Experiment Design — Final

## Railway Crossing Vision–Audio Fusion Safety System

| | |
|---|---|
| Version | 1.0 (2026-10-13) |
| Status | Governing specification for implementation and evaluation, subject to the decisions in `OPEN_DECISIONS_AND_BLOCKERS.md`. Where a decision is pending, this document states the default and marks it `[D-n]`. |
| Supersedes | `FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` v9 and `FINAL_ABLATION_MATRIX.md` v7 for endpoints, taxonomy, timing policy, statistics and approval mechanics. Their boundary definitions T0–T4 remain in force. |
| Evidence base | `INDEPENDENT_MASTER_AUDIT.md`; finding identifiers `IMA-nn` refer to `FINDINGS_REGISTER.csv`. |

This is a software replay study on recorded media. It supports statements about software behaviour on these recordings. It does not support any statement about SIL, EN 5012x compliance, certified railway safety or a physical barrier.

---

## 1. Research questions

**RQ1 (primary).** Given identical perception inputs, does a stateful decision policy reduce reopening of the simulated barrier during ground-truth occupancy compared with a stateless policy, and what does it cost in failure to reopen and in closure time?

**RQ2 (secondary).** How often, and how early relative to danger-zone entry, does the system issue a confirmed warning?

**RQ3 (secondary, conditional on synchronisation).** Does a second camera view change RQ1 or RQ2 outcomes?

**RQ4 (secondary, conditional on a corrected audio path).** Does audio evidence change any decision or its timing?

**RQ5 (descriptive).** How does the system behave on recordings with no train?

Nothing here tests generalisation to other crossings, weather, devices or mounting. The cohort is one site, two sessions, handheld devices.

---

## 2. Cohort

| Stratum | Events | Streams | Role |
|---|---|---|---|
| Train | 23 (`train_events/event_001`–`023`) | 46 | All RQ1–RQ4 denominators, subject to eligibility |
| No-train | 3 | 6 | RQ5 only. Never in a train denominator |
| Engine-only | 1 | 2 | Case study. Never pooled |
| Quarantined | `engine_events/event_historical_duplicate_010` | 2 | Excluded from every run by an explicit deny-list entry |

Each event also carries a session label: `S1` = 2026-09-14 (train 001–020), `S2` = 2026-10-04 (train 021–023, all no-train, engine). Every table reports S1 and S2 separately as well as together.

---

## 3. Canonical conditions

### 3.1 Factors

| Factor | Levels |
|---|---|
| **C** cameras | `F` front only · `B` back only · `FB` both, fused on a calibrated common clock |
| **T** temporal filter | `1` none · `2` confirm 2 ticks to activate, tolerate 2 missed ticks before deactivating `[D-6]` |
| **P** policy | `SL` stateless · `SM` state machine (section 5) |
| **A** audio | `0` off · `1` on, the stream's own audio at threshold 0.37 |

A condition is written `C-T-P-A`, for example `FB-2-SM-1`. The E identifiers are kept as aliases.

### 3.2 Condition table

| Alias | Code | Tier | Purpose | Legacy B |
|---|---|---|---|---|
| E1 | `F-1-SL-0` | Secondary | Lower bound | B0 (same factors) |
| E2 | `F-2-SL-0` | Secondary | Temporal filter on one view (vs E1) | — |
| E3 | `FB-1-SL-0` | Secondary, needs sync | Second view without filter (vs E1) | — |
| **E4** | `FB-2-SL-0` | **Primary** | Stateless reference | B3 (no miss tolerance there) |
| **E5** | `FB-2-SM-0` | **Primary** | State machine (vs E4) | — |
| E6 | `FB-2-SL-1` | Secondary | Audio without state machine (vs E4) | B2 used confirm 3; not equivalent |
| **E7** | `FB-2-SM-1` | **Primary** | Full system; audio (vs E5) | B4 (audio threshold was 0.50) |
| E8 | audio only | Secondary | Stand-alone audio descriptor | B1 |
| E9a / E9b / E9c | E7 + front loss / back loss / both lost, whole clip | Stress | Software verification | B5a / B6a / B6b |
| E10a | E7 + audio loss | Stress | — | B7a |
| E10b | E7 + 30% per-source frame loss | Stress | — | B7b |
| E10c | E7 + out-of-order delivery | Stress | — | B7d (was a no-op) |
| E10d | E7 + 2.0 s delivery delay on one camera | Stress | — | B7e (was a no-op) |
| E10e | E7 + injected `front` detection, conf 0.85, 1.0–2.5 s | Stress | — | B7c |
| E10f | E7 + audio loss + 10% frame loss | Stress | — | B7f |
| E10g | E7 + second approach during opening (synthetic trace) | Stress | Unit-level only | — |
| S1–S3 | mid-clip loss, flapping, sequential loss | Optional | — | B5b, B5c, B6c |

**Independent-camera mode.** If synchronisation is not accepted `[D-3]`, every `FB` condition is replaced by two runs, `F-…` and `B-…`, each using only its own stream's picture and sound. E3 has no meaning in that mode. The primary contrast becomes E5 vs E4 within each camera. Independent-camera runs are produced in all cases, as the sensitivity analysis.

**Single-factor rule.** E2–E1, E4–E2, E5–E4, E6–E4 and E7–E5 each change exactly one factor. E5–E4 changes the policy as a bundle (warning dwell, latching, clearance dwell); it does not attribute effect to any one of those.

**All conditions share one code path**: the same evidence stream, the same tick, the same barrier model, the same evaluator. A condition is a configuration, not a function.

### 3.3 Minimum experiment

Required for the paper's core claim: **E4, E5, E7** on the train cohort, the same three on the no-train and engine strata, and independent-camera versions of each. Everything else is secondary or stress and may be dropped without affecting RQ1.

---

## 4. Full-dataset inference: identity, outputs, isolation

Raw inference is decoupled from decisions. It runs once per stream and stores model outputs; every condition is then a cheap replay over those outputs. Raw inference needs neither approved annotations nor synchronisation.

### 4.1 Run identity

`run_id` = first 12 hex characters of SHA-256 over the canonical JSON of: Git commit (working tree must be clean), frozen-configuration hash, vision and audio checkpoint SHA-256, media manifest hash, and versions of Python, torch, ultralytics, opencv and ffmpeg.

```
results/runs/<run_id>/
  run_manifest.json            identity inputs above, start/end time, host
  stream_status.json           one row per expected stream (4.3)
  raw/vision/<cohort>/<event>/<camera>.jsonl
  raw/audio/<cohort>/<event>/<camera>.jsonl
  decisions/<condition>/<cohort>/<event>[.<camera>].jsonl
  injections/<condition>/<cohort>/<event>.json
  metrics/…                    written only by the evaluator (section 8)
```

Rules:

- No component reads from anywhere outside its own `run_id` directory. `results/experiments/` and `results/archive/` are legacy and never opened by new code.
- Paths contain cohort and event as separate directories, so `event_001` of different cohorts cannot collide.
- The first line of every raw file is a header: `run_id`, media SHA-256, checkpoint SHA-256, parameters.
- Files are written to a temporary name and renamed on completion. A stream is resumable only if its completion record verifies record count and media hash.

### 4.2 Raw records

- **Vision**, one per sampled frame: frame index, presentation timestamp from the decoder, nominal timestamp (index / fps), `status` (`ok`, `decode_error`, `inference_error`), and every detection with confidence ≥ 0.05 (label, confidence, box). The 0.35 operating threshold is applied at replay. Storing sub-threshold scores is for audit; thresholds are not to be re-chosen from them.
- **Audio**, one per window: start, end, probability, `status`. All windows, not only positives. Evidence time is the window **end**.
- Sampling: 5 Hz by nearest presentation timestamp.

### 4.3 Stream status

| Status | Rule |
|---|---|
| `FULL` | Decoder reached end of file; records written = frames selected; no error records |
| `PARTIAL` | Some records written; fewer than selected or any error record. Reason and counts recorded |
| `FAILED` | Zero usable records or an unhandled exception. Message recorded |
| `UNPROCESSED` | Expected but not attempted |

Expected streams come from the media manifest (54 video, 54 audio), not from what is found on disk. A run with any stream not `FULL` is reported as incomplete; affected events are excluded by rule, with the reason, never silently.

---

## 5. Decision policy specification

The policy below replaces the current clearance and fault logic (IMA-15, IMA-16, IMA-17). It is fixed here, before any formal replay, and is to be verified on synthetic traces only (IMA-47, `[D-11]`).

### 5.1 Frozen parameters

Unchanged from `leakage_guard.py`: vision confidence 0.35; audio threshold 0.37; confirm 2 ticks; miss tolerance 2 ticks; warning dwell 2.0 s; barrier closing 3.0 s; barrier opening 3.0 s; clearance dwell 3.0 s; tick 0.2 s; audio window 1.0 s, hop 0.5 s, 16 kHz; seed 42.

Taken from existing code or documents, now made explicit: source staleness timeout 2.0 s (`source_tracker.py:38`); fault confirmation 2 ticks (`decision_engine.py:152`); fault recovery hold 3.0 s (stated in `CORRECTIVE_EXPERIMENT_AUDIT.md` §6.3).

Removed: EMA alpha and evidence expiry. They were never implemented in the experiment path `[D-6]`.

No parameter may be changed after the first formal replay. No parameter is to be selected by looking at evaluation results.

### 5.2 Evidence per tick

- A tick at time `t` consumes records with timestamp in `(t − 0.2, t]`. Each record is consumed once.
- **Train evidence**: any detection labelled `front`, `side` or `rear` with confidence ≥ 0.35 from an available vision source.
- **Rear evidence**: the subset labelled `rear`.
- **Audio evidence** (A = 1): any window ending in the tick with probability ≥ 0.37 from an available audio source.
- **Active** (T = 2): becomes true on the 2nd consecutive tick with train evidence; becomes false on the 3rd consecutive tick without. (T = 1): equals train evidence on this tick.

### 5.3 Stateless policy (`SL`)

Barrier command is `CLOSE` while active, `OPEN` otherwise, through the same barrier model. With A = 1, active is the OR of vision-active and audio evidence.

### 5.4 State-machine policy (`SM`)

| From | Condition | To | Barrier |
|---|---|---|---|
| `IDLE` | active | `WARNING` (records `t_warn`) | open |
| `WARNING` | 2.0 s elapsed | `GATE_CLOSING` | closing |
| `GATE_CLOSING` | 3.0 s elapsed | `TRAIN_PRESENT` | closed |
| `TRAIN_PRESENT`, `TRAIN_DEPARTING` | active | `CROSSING_OCCUPIED` | closed |
| `TRAIN_PRESENT`, `CROSSING_OCCUPIED` | not active | `TRAIN_DEPARTING` (dwell starts at last train evidence) | closed |
| `TRAIN_DEPARTING` | clearance rule met for 3.0 s | `CROSSING_CLEAR` | closed |
| `CROSSING_CLEAR` | next tick | `GATE_OPENING` (records `t_open`) | opening |
| `GATE_OPENING` | active | `GATE_CLOSING` | closing |
| `GATE_OPENING` | 3.0 s elapsed | `IDLE` | open |
| any | no vision source available for 2 consecutive ticks | `FAULT_FAIL_SAFE` | closed |
| `FAULT_FAIL_SAFE` | ≥ 1 vision source available continuously for 3.0 s | `TRAIN_PRESENT` | closed |

- **Clearance rule** `[D-4]`. Default `ABS`: no train evidence on any available vision source, and at least one vision source available. Predeclared variant `REAR`: as `ABS`, and rear evidence has been seen since the barrier closed. Both are replayed from the same raw outputs; `ABS` is primary. Under `REAR`, an event with no rear evidence stays closed and is counted as a failure to reopen.
- **Audio** `[D-5]`. Default: audio evidence during `TRAIN_DEPARTING` restarts the clearance dwell and has no other effect. If audio is given warning authority, audio evidence on 2 consecutive windows also satisfies the `IDLE → WARNING` condition. In neither case can audio shorten or grant clearance.
- Recovery from the fault state enters a closed holding state, never an open one. Reopening then follows the normal clearance rule.
- Every transition is checked against one legality table in `src`; an illegal transition raises.
- **Liveness bound**: from any state, with at least one vision source available and no train or audio evidence, the engine reaches `IDLE` within 14.5 s under `ABS` (3.0 recovery + 2.0 warning + 3.0 closing + 3.0 dwell + 3.0 opening + tick slack).

---

## 6. Sensor health and timing

### 6.1 Health model

Expected sources are registered from the run configuration before replay. Health is computed causally at each tick from records seen so far.

| # | Situation | Representation | Engine behaviour |
|---|---|---|---|
| 1 | Camera healthy, no detections | record `ok`, empty detections | No fault. Counts as absence |
| 2 | One camera unavailable | see 4–6, 8 | Continue on the other; `degraded` flag logged |
| 3 | Both unavailable | — | Fault state after 2 ticks |
| 4 | Stale or delayed frames | newest record older than 2.0 s at the tick | Source unavailable, reason `stale` |
| 5 | Decoder error | record `decode_error` | Source unavailable for that tick; persists per rule 4 |
| 6 | Inference error or timeout | record `inference_error` | As 5 |
| 7 | Detection dropout | record `ok`, empty detections | Handled by miss tolerance only |
| 8 | Injected fault | record `available = false`, reason `injected:<mode>` | As 2 or 3 |

A source that is expected and has produced no record is unavailable from the first tick. End of a recording is not a fault: a replay ends at the end of the shortest participating stream.

Modality and role are typed fields set at registration. Nothing is inferred from the text of a source identifier.

### 6.2 Clocks

- **Within one file**: picture and sound share the file's clock. All 56 files report both streams starting at 0 with equal durations to 2 ms.
- **Across files**: no common clock is assumed. Each stream's timestamps are local to its file.
- Ground-truth markers are stored on the clock of the camera they were annotated on, and say which.

### 6.3 Cross-camera calibration `[D-3]`

Purpose: obtain, per event, `Δ = t_back − t_front` with a stated uncertainty, from evidence in the recordings.

1. **Estimate.** Band-pass both 16 kHz audio tracks (200–4,000 Hz). Compute generalised cross-correlation with phase transform over lags of ±60 s. `Δ̂` is the lag of the highest peak.
2. **Quality.** Record the ratio of the highest to the second-highest peak outside ±50 ms, and repeat the estimate on the first and second halves of the overlap separately.
3. **Uncertainty.** `δ` = half the spread of the three estimates (full, first half, second half) + 0.03 s for acoustic path difference between two devices up to about 10 m apart.
4. **Automatic status.** `candidate_aligned` if peak ratio ≥ 2.0 and `δ ≤ 0.10 s`; otherwise `unaligned`. These thresholds are fixed here and are not to be adjusted after seeing results.
5. **Human acceptance.** For each `candidate_aligned` event the researcher views one frame pair at a moment of clear motion (for example the locomotive front passing a fixed object visible in both views) using `Δ̂`, and records accept or reject. Only accepted events are `aligned`.
6. **Sanity bound.** `Δ̂` is compared with the difference of the recording-start tags; a disagreement above 5 s is flagged for the reviewer. The tags are never used as the offset.

Output: `data/sync/sync_offsets_v1.json` with `Δ̂`, `δ`, peak ratio, half-estimates, status, reviewer and date, plus one plot per event.

**Mode rule, fixed in advance.** If at least 20 of 23 train events are `aligned`, the fused (`FB`) analysis is primary on the aligned events and independent-camera results are the sensitivity analysis. Otherwise independent-camera analysis is primary and no dual-camera claim is made.

In fused mode the master clock is the front camera's. Back-camera records and back-clock markers are shifted by `−Δ̂`. Every metric that compares a shifted quantity with an unshifted one is also computed at `±δ`.

---

## 7. Ground truth

### 7.1 Status

There is no approved ground truth. The 27 files under `data/ground_truth/reviews/` are invalid as approvals (IMA-06). All proposals are candidates.

### 7.2 Approval mechanics

1. The researcher reviews each event from raw frames and audio, with no model output on screen.
2. For each marker the researcher records: value, frame index, camera, `censoring` (`none`, `left`, `right`), `observable`, and saves one evidence frame.
3. Approved files are written to `data/ground_truth/approved/<cohort>/<event>.json` with `annotator`, `date`, and the hash of the candidate that was reviewed.
4. `data/ground_truth/approved/APPROVAL_MANIFEST.json` lists each approved file with its SHA-256 and carries the researcher's name and date. Creating this manifest is a manual act by the researcher. No script may create or modify it.
5. `data/ground_truth/INVALIDATED_REVIEWS.json` lists the hashes of the 27 existing review files.
6. The loader accepts a file only if it is listed in the approval manifest with a matching hash, and refuses any file whose hash is on the invalidation list. It never reads `proposals/` or `reviews/`.

### 7.3 Marker semantics

T0–T4 and scene-clear keep the definitions of protocol v9 §5. Additions:

- A censored marker stores a bound, not a point: `left` means the true time is at or before the value; `right` means at or after.
- Horn status is `present`, `absent` or `uncertain`, set by listening. Onset is recorded only for `present`.
- No-train events carry no train markers. They carry a signed statement that no rail vehicle is visible or audible in either stream `[D-7]`.

### 7.4 Engine-only event `[D-9]`

Default: T3 and T4 denote the same instant, the rear of the locomotive clearing the departure boundary, annotated on the back camera. If the recording ends first, both are right-censored at the recording end. A front-camera clearance time is not substituted.

### 7.5 Annotation uncertainty

A tolerance `u` is attached to every timing comparison. Default `u` = the 90th percentile of absolute disagreement between two annotators on a subset of at least 8 train events `[D-8]`; if there is no second annotator, `u = 0.5 s` and the paper says so.

---

## 8. Metric contract

### 8.1 Values and status

Every per-event metric is a record `{value, status, reason}`. `status` is one of `ok`, `not_applicable`, `not_evaluable`, `censored_left`, `censored_right`. Every aggregate reports `n_total`, `n_applicable`, `n_evaluable`, the numerator, and the list of excluded events with reasons.

- A proportion with `n_evaluable = 0` is undefined. It is stored as `null` with status `undefined`, never as 0.
- Formatting an undefined or censored value as a plain number raises an error.
- No clamping. Negative lead times and negative latencies are kept.
- An aggregate with `n_evaluable < 10` is reported as counts only, labelled "not estimable".
- All conditions are scored by one evaluator from the decision trace and the approved labels. The evaluator has no condition-specific branch.

### 8.2 Observable outputs

From each decision trace: tick time, state, barrier command, arm angle, `blocked` (angle ≤ 45°), per-source availability, evidence flags. Derived: `t_warn` (first `WARNING`, or first active tick under `SL`), `t_blocked` (first blocked tick), reopening instants (blocked → not blocked), `t_open` (first opening command after the last blocked interval), `t_end` (last tick).

Feasibility constants are derived, not typed in. `R_block` is the first blocked tick when the frozen `SM` policy is replayed on a synthetic trace with train evidence on every tick from 0 (about 3.6 s with the frozen parameters). `R_open` is the first opening command when it is replayed on a synthetic trace whose train evidence ends at time 0 (a little over 3 s).

### 8.3 Definitions `[D-10]`

| ID | Metric | Applies to | Evaluable when | Definition | Uncertainty |
|---|---|---|---|---|---|
| **M1** | Warned before entry | Train | T1 `ok` | Failure if no `t_warn ≤ T1`. Numerator = failures | Wilson 95% |
| M2 | Warning lead time | Train | T1 `ok` and `t_warn` exists | `T1 − t_warn`, signed. If T0 is left-censored and `t_warn` is at the earliest possible tick, status `censored_right` (true lead ≥ value) | Median, range, number censored |
| M3 | Blocked at entry (protocol "missed train") | Train | T1 `ok` **and** (T0 `ok` or `T1 ≥ R_block`) | Failure if not blocked at the tick containing T1. Events failing the screen are `not_evaluable: insufficient_lead_in` | Wilson 95%; feasibility table published |
| **M4** | Reopening during occupancy (premature opening) | Train, engine | T4 `ok` and `t_blocked < T4` | Failure if any blocked → not-blocked transition, or any opening command, occurs in `(t_blocked, T4)` | Wilson 95%; recomputed at `T4 ± u` |
| M5 | Never protected | Train, engine | T4 `ok` | Failure if never blocked before T4. Reported beside M4 so that M4's denominator is transparent | Count |
| M6 | Occupancy coverage | Train | T1 and T4 `ok`, same clock or aligned | Fraction of `[T1, T4]` with blocked = true | Median, range |
| **M7** | Reopened within recording | Train, engine | T4 `ok` | Success if `t_open` exists with `T4 ≤ t_open ≤ t_end`. Otherwise `censored_right` if `t_end − T4 < R_open`, else failure | Counts in three classes: reopened, failed, censored |
| M8 | Clearance latency | Train, engine | M7 success | `t_open − T4` | Median, range; number censored stated |
| M9 | Excess closure | Train | T1 and T4 `ok`, same clock or aligned | Blocked time outside `[T1, T4]` within the recording | Median, range |
| M10 | Barrier reversals | All | always | Number of blocked ↔ not-blocked changes | Median, max |
| **N1** | Nuisance closure | No-train | negative confirmed `[D-7]` | Event-level: any blocked tick. Also blocked seconds, number of closure episodes, exposure seconds | `k/3`, per-stream exposure. **No hourly rate** |
| D1 | Stream descriptors | All | always | Frames, detections by class, fraction of frames with train evidence, audio positive fraction | None. Needs no labels |
| V1 | Trace invariants | All | always | Counts of: opening command while train evidence present; illegal transitions; clearance attributed to audio; steps examined | Counts |
| F1 | Fault-condition outcome | Stress | always | Records affected by injection; fault state reached; time to reach; recovered; M4, M7 where evaluable | Descriptive |

Clock rule for independent-camera mode: M1–M3 are computed on the front-stream system (T1 is on the front clock); M4, M5, M7, M8 on the back-stream system (T4 is on the back clock). M6 and M9 are `not_evaluable: clocks_unaligned`.

### 8.4 What may be reported before approval

D1, V1, F1 (without M4/M7), M10, and N1 once the negatives are confirmed train-free. Nothing that references T0–T4 or horn truth.

### 8.5 Engine-only and no-train

The engine event is evaluated with the same definitions and reported in its own table. No-train events are evaluated for N1, D1, V1 and M10 only.

---

## 9. Statistics

- **Unit of analysis**: the event. Streams and ticks are not independent observations.
- **Proportions**: `k/n` with a Wilson 95% interval. The interval describes variation among passages recorded at this site in these sessions. It is not a bound on field failure probability. For orientation, 0 of 23 gives an upper limit of about 14%.
- **Paired binary contrasts**: exact McNemar test on discordant pairs; discordant counts reported.
- **Paired continuous contrasts**: Wilcoxon signed-rank on events evaluable under both conditions; median difference with a bootstrap percentile interval (10,000 resamples of events, seed 42).
- **Censored quantities**: report the number censored. A median is given only if fewer than half are censored; otherwise "not estimable".
- **Primary contrasts**, fixed in advance, Holm-adjusted across the three:
  1. E5 vs E4 on M4.
  2. E5 vs E4 on M7.
  3. E7 vs E5 on M2.
- All other comparisons are descriptive. No significance language.
- **Clustering**: results are shown for S1 and S2 separately. With 20 and 3 events no between-session inference is attempted.
- **Negatives**: three clips, about 60 s per camera. Report `k/3` and seconds. Zero episodes in 60 s is compatible with up to roughly 180 per hour, so no rate is stated.
- **Stress conditions**: repeated measures on the same events. Reported descriptively, never pooled with natural replay, never presented as additional sample size.

---

## 10. Claims this design can and cannot support

| Can support (if the results show it) | Cannot support |
|---|---|
| On these recordings, the stateful policy reopened during occupancy in fewer events than the stateless policy, at a stated cost in failure to reopen | Any safety integrity level, standard compliance or physical safety |
| Warnings preceded entry in `k` of `n` evaluable events, by a stated lead time subject to left-censoring | A missed-train rate for deployment |
| The software reached a restrictive state under each modelled fault and recovered as specified | Robustness to real sensor failures, weather, night operation in general |
| Counts of closures on three no-train clips | A false-alarm rate per hour |
| Whether audio changed any decision at the frozen threshold | That audio "improves safety" in general |
| With accepted synchronisation, differences between one and two views | Cross-site generalisation |

The paper must state: one site; two sessions; handheld devices; recordings begin after the train is visible; the decision policy was revised after a pilot on the same recordings; barrier timing is simulated; ground truth is single-annotator unless `[D-8]` is taken up.
