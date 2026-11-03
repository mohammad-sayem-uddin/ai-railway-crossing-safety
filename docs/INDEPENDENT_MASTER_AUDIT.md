# Independent Master Audit

## Railway Crossing Vision–Audio Fusion Safety System

| | |
|---|---|
| Audit date | 2026-10-13 |
| Repository | `/Users/sayemuddin/Desktop/Train_automation` |
| Branch / revision | `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (equal to `origin/main` as last fetched) |
| Mode | Read-only inspection. No source, configuration, data, weights, annotations, results or Git state were changed. No inference, training, calibration or test run was executed. |
| Files created by this audit | `docs/INDEPENDENT_MASTER_AUDIT.md`, `docs/IMPLEMENTATION_PLAN_FOR_SONNET.md`, `docs/EXPERIMENT_DESIGN_FINAL.md`, `docs/OPEN_DECISIONS_AND_BLOCKERS.md`, `docs/FINDINGS_REGISTER.csv` |
| Recovery point | All five files are new; none existed before. Deleting them restores the prior state exactly. Pre-audit `git status --porcelain` had 118 entries (10 modified, 108 untracked), SHA-256 `74cef503…711302ab`. |

Findings are numbered `IMA-nn`. The full register, with evidence paths, corrective action and closure test for each, is `docs/FINDINGS_REGISTER.csv`; section 7 is its condensed view.

---

## 1. Executive verdict

**No performance number produced so far is usable, and the system as implemented is not the system the protocol describes.** The repository holds real assets worth keeping: 56 intact recordings, two frozen checkpoints whose hashes I recomputed and confirmed, a working per-stream inference path, and a candidate-annotation workflow. Around them, the evaluation layer reports conclusions that the code decides in advance, the safety logic does not do what its invariants claim, and the only copy of most of the work sits in one unsynchronised, partly broken directory.

The ten points that matter most:

1. **The work exists in one place** (IMA-01). The two locations the recovery reports name as the clean repository and the immutable backup do not exist. All fusion, simulation, experiment, evaluation and annotation code, 18 of 20 scripts and every candidate annotation are untracked and live only in this Desktop folder.
2. **`git status` is hiding 68 missing tracked files** (IMA-02), including `pyproject.toml`, all four `configs/*.yaml` and twelve test modules. 73 index entries are flagged assume-unchanged.
3. **Audio inference ran without the training normalisation** (IMA-22). The trainer saves `norm_mean`/`norm_std`; the inference wrapper reads `feature_mean`/`feature_std` and falls back to 0 and 1. Every Audio V3 output on the evaluation recordings is invalid. The 9 positive windows in 23 train events are a symptom.
4. **The clearance rule is not "positive rear confirmation"** (IMA-15). `side` counts as both approach and departure evidence, and 94% of field detections are `side`. The engine cycles through four states and whether the gate ever opens depends on where the last detection lands.
5. **There is no liveness** (IMA-16). Closed states wait forever and the fault state never exits. A recovery hysteresis that the corrective audit says was added is not in the code. Zero premature openings is what a gate that never opens produces.
6. **Premature opening is computed three different ways** (IMA-28): flagged without ground truth for stateless baselines, hardcoded false for audio-only, and always false for the proposed system because the simulator is never given entry or clearance times.
7. **Camera fusion assumes a zero offset that the files contradict** (IMA-11). Recording-start tags differ by up to 33 s within an event, and entry markers (front clock) and clearance markers (back clock) would be placed on one timeline.
8. **The recordings are too short for the protocol's primary endpoints** (IMA-31). With the frozen 2 s warning and 3 s closing times the barrier cannot block before about 3.6 s; candidate entry is at or before 3.2 s in 18 of 22 events. Candidate tail clearance falls 1.0–2.7 s before the end of 20 of 22 back recordings, shorter than the 3 s clearance dwell.
9. **All 27 review records are marked APPROVED by a "human_researcher_lead"** (IMA-06) though you have approved nothing. Current candidates also show template-like regularity (IMA-07).
10. **Report, table and figure generators contain hardcoded results and one synthetic data series** (IMA-39). `docs/REAL_WORLD_EXPERIMENT_REPORT.md` is invalid in full.

Counts: 47 findings — 12 P0, 20 P1, 14 P2, 1 P3; 43 confirmed, 3 suspected (IMA-07, IMA-09, IMA-31), 1 unverified (IMA-43).

What blocks **running full-dataset inference**: IMA-01, 02, 03 (preserve and rebuild the environment), IMA-22 (audio normalisation), IMA-24 (run identity), IMA-25 (configuration actually checked). Nothing else. In particular, annotation approval and camera synchronisation do **not** block collecting raw per-stream predictions.

What blocks **only evaluation or publication**: everything else — safety logic, synchronisation, ground-truth approval, the metric contract, the ablation taxonomy and reporting.

---

## 2. Repository state and evidence inventory

### 2.1 Location and copies

| Location | State on 2026-10-13 |
|---|---|
| `~/Desktop/Train_automation` | Present. `.git` created 07:47 (fresh clone); working tree populated by copy. **Only complete copy.** 12 GiB free on the volume. |
| `~/Projects/Train_automation` (recovery reports' target) | **Does not exist.** |
| `~/iCloud Drive (Archive)/Desktop/Train_automation` (reports' "immutable backup") | **Does not exist.** |
| `~/Library/Mobile Documents/…/Desktop/Train_automation` | Present but partial: 1 file under `data/raw/layer_b`, 0 under `docs` and `data/ground_truth`, 2 scripts. Commands there stall. Not a backup. |
| `origin` (GitHub) | 223 tracked files at `d4db94d`. No media, weights, candidate annotations, or post-August research code. |

Time Machine has no destination configured, so there is no system backup either. The iCloud shadow copy is not a strict subset of the working tree: it holds `scripts/create_event_label_templates.py`, which is absent here. It should be inventoried in Phase 0, not merged.

Finder's iCloud Desktop sync flag reads off (`FXICloudDriveDesktop = 0`). I could not establish from the filesystem how the working tree moved from the paths in the reports to the Desktop.

### 2.2 Git state

- 19 commits; the last code commit is 2026-08-18, the last documentation commit 2026-10-12. No tags, no stashes, empty reflog.
- `git status`: 10 modified, 108 untracked. The recovery report lists 9 modified; the tenth, `src/railway_detection/vision/video.py`, is a sequential-decode fix made today.
- **73 index entries are assume-unchanged; 68 of those files are absent from disk** (IMA-02). Absent: `configs/{audio,fusion,simulation,vision}.yaml`, `pyproject.toml`, root `dashboard.py` and `demo_video.py`, ten package `__init__.py` files, `src/railway_detection/__main__.py`, `vision/adapter.py`, `audio/noise_mixer.py`, `tests/fixtures/mock_data.py`, twelve test modules, vision run manifests and `.gitkeep` anchors. Five flagged files are present and were rewritten today.
- `.git/lost-found` holds 1 commit and 8 other objects from the recovery.

### 2.3 Tracked versus local-only

| Artifact | Tracked | On disk | Notes |
|---|---|---|---|
| `fusion/{collector,decision_engine,rules,source_tracker}.py`, all of `simulation/`, `experiments/`, `evaluation/metrics.py`, `annotation/` | No | Yes | The entire evaluated system |
| `scripts/` (20 files) | 2 | 18 untracked | Orchestrator, trainers, table and figure generators |
| `tests/` | 21 tracked (12 of them missing) | 10 untracked present | See IMA-42, IMA-43 |
| `data/raw/layer_b/v2/` | Ignored | 56 `.mov`, 3.6 GB | 23 train, 3 no-train, 1 engine, 1 quarantined duplicate; two streams each |
| `data/ground_truth/` | No | 119 files | 27 review sheets, proposals v1–v6, 27 review JSONs, snapshot manifest |
| `data/manifests/` | No | 23 files | Audio, video and audit manifests |
| Vision dataset | Ignored | 3,157 images, **0 label files, no `data.yaml`** | Boxes survive in tracked `results/dataset_validation/dataset_manifest.jsonl` (IMA-05) |
| Checkpoints (`*.pt`) | Ignored | Present | Hashes below |
| `results/experiments/` | No | 335 files | Mixed code versions (IMA-26) |
| `results/archive/forensic_backup_20261013/` | No | 336 files | Copy made before corrective edits |
| `.venv/` | Ignored | Broken | `import torch` fails (IMA-03) |

### 2.4 Checkpoints (hashes recomputed during this audit)

| Role | Path | SHA-256 | Matches frozen constant |
|---|---|---|---|
| Vision, frozen | `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` | `3f5bb5b2…fba18ebd` | Yes |
| Audio V3, frozen | `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt` | `ea1bb81d…6c512782` | Yes |
| Audio V2, prohibited | `models/audio/best_checkpoint.pt` | `59b0785f…fcf7d5` | Matches the prohibited hash; not hard-blocked in code (IMA-25) |
| YOLO pretrained base | `yolov8n.pt` | `f59b3d83…fc83b36` | No reference recorded |

The frozen constants live in `src/railway_detection/experiments/leakage_guard.py:22-45`. There is no configuration file behind them; `configs/` is absent.

### 2.5 Media inventory (from container metadata, all 56 files)

- Every file reports video and audio `start_time = 0` with stream durations equal to within 2 ms, which supports using one clock for a file's own picture and sound.
- Devices: front is an iPhone 12 Pro throughout. Back is an iPhone 15 Pro Max for train events 001–020 and the duplicate, and an iPad (10th generation, 4K H.264, mono audio) for events 021–023, the negatives and the engine event.
- Sessions: events 001–020 on 2026-09-14, 14:13–17:26 local. Events 021–023, all negatives and the engine event on 2026-10-04, 19:22–19:59 local.
- Exposure: train cohort 1,252 s front / 1,224 s back; no-train 60.3 s front / 60.5 s back; engine 7.9 s / 9.8 s.
- Recording-start tags (`com.apple.quicktime.creationdate`, 1 s resolution) differ between the two cameras of an event by 0–33 s. The tag is unreliable as an offset: back clips of events 007 and 008 carry the same value, so at least one is a trim of a longer recording.
- Media hashes: two files spot-checked against the hashes in the candidate proposals; both match. The other 54 were not re-hashed.

### 2.6 Inference caches (`results/experiments/cache`, 141 files)

- 81 files written 2026-10-13 08:45, prefixed by cohort: 54 vision, 27 audio. These cover all 54 active streams; last sampled timestamp is within 2% of container duration for every vision stream. The truncated stream reported earlier is not visible in this set.
- 60 files written 2026-09-23 without a cohort prefix: 40 vision, 20 audio. Legacy.
- Labels emitted across all vision caches: `side` 20,926, `front` 1,099, `rear` 266. **The detector's class names match the fusion rule labels** (`front`, `rear`, `side`); the earlier concern about a `rare`/`rear` mismatch is closed by this evidence. I did not read the names from the checkpoint itself.
- No cache records which checkpoint, threshold or sampling rate produced it (IMA-24). The provenance manifest in the forensic backup assigns model identities by assertion.

### 2.7 Annotations

- Latest candidates: `v6` for train event 001, `v4` for 005, `v3` for the engine event, `v2` elsewhere. The batch index still names `v3` for event 005 and `v2` for the engine event.
- No approved ground-truth directory, no ground-truth manifest. Correct.
- 27 review JSONs under `data/ground_truth/reviews/` are marked APPROVED (IMA-06).

### 2.8 Active versus archived methodology

Active: `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` v9.0.0, `FINAL_ABLATION_MATRIX.md` v7.0.0, `FINAL_GROUND_TRUTH_PROTOCOL.md` v7.0.0, `FINAL_EXPERIMENT_DATA_FLOW.md` v7.0.0, `FINAL_TEST_PLAN.md`. Archived: 26 files under `docs/archive/`. `docs/archive/git_baseline_d4db94d/`, which the restoration report says holds the pre-restore versions of nine files, does not exist (IMA-04).

Broken references in active documents: `GroundTruthLoader`, `tests/test_safety_invariants.py`, `configs/frozen_parameters_v3.json`, `run_final_real_world_evaluation.py` (IMA-41); the code's docstrings cite `docs/REAL_WORLD_EXPERIMENT_PLAN.md` and `docs/EXPERIMENT_PROTOCOL_V2.md`, both archived.

---

## 3. The system as actually implemented

Entry point for the real-world experiment: `scripts/run_real_world_experiments.py`. The CLI (`railway_detection experiment run`) reaches the same runner.

| Stage | Implementation | What it does | Exercise level | Mismatch with documentation |
|---|---|---|---|---|
| Video decode | `vision/video.py:70-133` | OpenCV sequential grab, every `round(fps/5)`-th frame, timestamp = index / nominal FPS | Natural media | Not presentation time (IMA-12). Unreadable frames skipped with a log line only |
| Audio decode | `data/audio_extractor.py` via `layer_b_processor.py:117-152` | ffmpeg to 16 kHz mono WAV for both cameras | Natural media | Only the front WAV is used afterwards (IMA-13) |
| Vision inference | `layer_b_processor.py:154-221` | Ultralytics YOLO at conf 0.35, one `EvidenceRecord` per frame, written to a JSONL cache | Natural media | Exceptions swallowed per frame; partial output cached (IMA-17, IMA-24) |
| Audio inference | `audio/pipeline.py`, `audio/model.py:148-229` | 1.0 s windows, 0.5 s hop, log-mel, compact CNN, sigmoid | Natural media, **wrong normalisation** | IMA-22; three thresholds (IMA-23); window-start timestamps (IMA-13) |
| Temporal handling | `fusion/collector.py:114-155` | Batch-ingests all records, emits a frame every 0.2 s containing records from the preceding 0.25 s | Natural media | No EMA, no miss tolerance; `TemporalEvidenceBuffer` is used only by the demo (IMA-25). Single record can satisfy two-frame confirmation (IMA-14) |
| Synchronisation | `data/sync.py` | `SyncAligner` class exists | Unit-tested in isolation only | Never passed to the collector; offset is zero by omission (IMA-11) |
| Fusion and decision | `fusion/rules.py`, `fusion/decision_engine.py` | Hand-written rules over label sets and thresholds; 11 states | Unit tests on synthetic frames; natural media via B4–B7 | See section 4.3 |
| Gate | `simulation/gate_model.py` | Linear 90° arm, 3 s each way, "blocked" at ≤ 45° | Simulation | A kinematic stand-in; no physical evidence |
| Simulation loop | `simulation/runner.py:58-152` | Sorts frames, steps engine and gate, accumulates closed time | Natural media | Sorting cancels the out-of-order injection (IMA-34) |
| Conditions | `experiments/runner.py` | B0–B3 and B1 use separate inline "stateless" loops; B4–B7 use the engine with default arguments | Natural media | E1–E7 absent; definitions inconsistent (IMA-28, IMA-37) |
| Metrics | `evaluation/metrics.py`, `experiments/statistics.py` | Event flags, Wilson intervals, bootstrap, sign test | Unit tests; never with real labels | IMA-29, IMA-30, IMA-33 |
| Logging | `experiments/timeline_generator.py` | Per-step JSON/CSV timeline for B4 only | Natural media | No per-condition decision log; no run manifest (IMA-27) |
| Reporting | `scripts/generate_publication_{tables,figures}.py`, report template in the orchestrator | Mix of computed and literal values | — | IMA-39 |

**What kind of system this is.** It is rule-based late fusion: two independently trained single-modality models produce labels and scores, and a deterministic rule set with timers combines them. Nothing is learned across modalities. It should be described as "rule-based decision-level fusion with a finite-state controller", not as a multimodal or end-to-end fusion model. As implemented, audio cannot initiate any action; it can only extend one dwell (IMA-38), which contradicts the protocol (IMA-20).

---

## 4. Challenge of previous findings

### 4.1 Cache contamination (A)

The earlier diagnosis is **correct**: 54 + 27 active and 40 + 20 legacy caches share one directory, and totals were summed across both. What remains open:

- Cache keys still carry no model, threshold, sampling or media identity; `use_cache=True` is still the default (`layer_b_processor.py:161,231`). The unprefixed legacy names cannot collide with today's cohort-prefixed names, but nothing stops a future run reusing today's files after a checkpoint or threshold change.
- `scripts/generate_publication_tables.py` and `generate_publication_figures.py` read the cache directory directly.
- `results/experiments/B4/timelines/` mixes 42 legacy and 54 current files.
- The "cryptographic provenance manifest" labels files after the fact. It does not prove which model wrote them.

Recommended scheme: `EXPERIMENT_DESIGN_FINAL.md` section 4.

### 4.2 Metrics and defaults (B)

Partly fixed. `metrics.py` now returns `None` for a missing entry or clearance time and aggregates over evaluable events only. Still open:

- Zero denominators and default counts can produce numeric intervals (IMA-30).
- The per-event numerator and denominator cannot be reconstructed for premature opening because the flag is not derived from ground truth at all (IMA-28).
- Negatives and the engine event are scored as train events (IMA-29).
- Censoring is ignored: lead time and excess closure are clamped at zero, never-opened events vanish from the latency mean.
- The Wilson interval is a reasonable choice for an event-level proportion. It describes variation among passages at this site only. No count-per-exposure quantity is computed anywhere; the documents sometimes describe 3-of-3 nuisance closures as a "rate", which it is not.
- The on-disk summaries still show the old `0.0%` output because they predate the fix (IMA-26).

### 4.3 Fail-safe logic (C)

Does the engine use absence of detections as evidence of sensor failure? **No.** `all_vision_failed` is computed from `source_availability` (`decision_engine.py:104-121`), not from detections. The corrective audit's phrase "fail to provide valid frames/detections" is loose; the code is right on this point.

The real problems are the opposite ones:

| Case | Behaviour today | Verdict |
|---|---|---|
| 1. Healthy cameras, no detections | Stays `IDLE`, gate open | Correct |
| 2. One camera unavailable | Continues on the other; status label only | Acceptable; undocumented |
| 3. Both unavailable | From `IDLE`: fault after 2 ticks. From any active state: fault immediately | Entry correct; **no exit** |
| 4. Stale or delayed frames | Not detectable in replay; availability is computed after all evidence is loaded | **Not implemented** |
| 5. Decoder error | Frame skipped, warning logged, no record | **Invisible** |
| 6. Inference exception or timeout | Same; no timeout exists | **Invisible** |
| 7. Temporary detection dropout | Treated as no detection | Correct in kind; no miss tolerance |
| 8. Explicit injection | Sets `available=False` | Works for dropout modes only |

A stream with no records at all (missing file, total decode failure) is never registered, so the engine sees no vision source, does not fault, and leaves the gate open (IMA-17).

Transition tracing, counters and liveness: IMA-15, IMA-16. `consecutive_vision_failure_count` resets on any tick with one available source. `consecutive_approach_count` is never reset after `WARNING`. Once in `WARNING` the sequence to `TRAIN_PRESENT` is timer-driven and cannot abort.

**On certification language.** Unit tests and replay simulation can show that the software reaches a restrictive state under modelled inputs. They cannot support any statement about SIL, EN 50126/50128/50129, or physical barrier safety. That needs a hazard analysis, a safety case, independent assessment and hardware evidence. The corrective audit's closing line ("Certified … under strict CENELEC/AREMA forensic audit guidelines") and its appeal to a "SIL 4 axiom" must not be repeated (IMA-40).

### 4.4 Failure injection (D)

The 100% drop defect is fixed (`failure_injector.py:86-100`) and has a real regression test. Remaining: two modes are no-ops (IMA-34), drop semantics and seeding are imprecise (IMA-35), and conditions that receive no usable input still produce a summary file. The dual-blackout condition passes by permanent closure (IMA-36).

### 4.5 Thresholds, models and leakage (E)

- Checkpoint selection: the orchestrator uses the frozen paths. The audio wrapper would accept any checkpoint, including V2. `PyTorchTrainHornClassifier()` with no checkpoint silently builds an untrained network (`audio/model.py:172-174`); `AudioEvidencePipeline()` with no classifier silently uses the spectral baseline (`audio/pipeline.py:39`).
- Threshold: IMA-23. Preprocessing: IMA-22.
- Cache reuse across models: possible (IMA-24).
- Weight mutation: none found; `torch.load` is read-only here.
- Target data in training: the Audio V3 threshold was calibrated on the validation split and the test split was scored once (`train_audio_model_v3_esc50.py:397-427`). I found no evaluation recording in the audio manifests by path. The check in code is too weak to prove this (IMA-25). The vision images predate the recordings by months; whether they show the same crossing is unknown.
- Pilot contamination of the decision policy: IMA-47.

### 4.6 Timing and synchronisation (F)

R04 is unresolved and, in code, violated (IMA-11). Within one file, picture and sound share a clock to container precision. Across files there is no common clock: `SyncAligner` is never constructed outside a unit test. Timeline exports carry the string `EXPLORATORY_UNVERIFIED_ZERO_OFFSET`, which is honest labelling of an invalid computation. The protocol says creation times are unreliable because some differ by days; that refers to the container `creation_time` of re-exported files. The QuickTime `creationdate` tag is consistent to the day and second, and it shows the offsets are not zero. It is still not a measurement.

A valid calibration and the fallback design are in `EXPERIMENT_DESIGN_FINAL.md` section 6.

### 4.7 Ground truth (G)

Cohort counts are as expected: 23 + 3 + 1 active, one quarantined duplicate. Beyond IMA-06 to IMA-10:

- `T2 − T1`: 0.7 s ×3, 0.8 s ×18, 0.9 s ×1.
- `T3` (back clock) is smaller than `T1` (front clock) in several events. That is expected with unsynchronised clocks and shows why the two cannot share a timeline.
- Event 005: `T1`, `T2`, `T4` unobservable. It can contribute to nothing that needs entry or tail clearance.
- The definitions of T0–T4 and scene-clear are consistent across protocol v9, the ablation matrix and the current candidates. The operational danger-zone convention is an annotation convention, not surveyed geometry, and should be described that way.

### 4.8 Experimental design (H)

| Implemented | Nearest documented | Relationship |
|---|---|---|
| B0 | E1 | Same factors. Not the same code path as the stateful conditions |
| B1 | E8 | Audio-only; latches closed forever |
| B2 | — | Dual + audio, stateless, 3-frame confirm. No E equivalent (E6 uses 2) |
| B3 | E4 | Without EMA or miss tolerance |
| B4 | E7 | Without EMA; audio threshold 0.50; audio cannot warn |
| B5a / B6a / B6b | E9a / E9b / E9c | Equivalent |
| B5b, B5c, B6c | — | No E equivalent |
| B7a / B7b / B7c / B7f | E10a / E10b / E10e / E10f | Equivalent in intent |
| B7d / B7e | E10c / E10d | **No-ops** |
| — | E2, E3, E5, E6, E10g | **Not implemented** |

E5 (state machine without audio) and E4 (same inputs, stateless) are the pair that isolates the state machine. Neither exists as a matched pair today. All fault conditions run on natural media with synthetic perturbation and are repeated measures on the same 27 events.

### 4.9 Metrics and statistics (I)

Definitions, eligibility and uncertainty for every metric are specified in `EXPERIMENT_DESIGN_FINAL.md` sections 8–9. Valid before annotation approval: stream-level detection descriptors, nuisance closures on negatives once the clips are confirmed train-free, software behaviour under injected faults, and trace invariants. Everything involving T0–T4 or horn truth needs approved labels.

### 4.10 Engineering and reproducibility (J)

Covered by IMA-01 to IMA-03, IMA-24 to IMA-27, IMA-42, IMA-43. In addition: there is no resume logic beyond "cache file exists"; no per-stream completion status; errors are logged at warning level and execution continues; the experiment registry is written by unit tests into the real results path.

---

## 5. Methodology review

| # | Concern | Classification |
|---|---|---|
| M1 | The research question requires "temporally aligned" recordings. They are not aligned (IMA-11). | Prevents a required experiment (fused conditions) until calibrated |
| M2 | Left-censored starts and short tails make "closed by T1" and "opened after T4" unobservable for most events (IMA-31). | Invalidates the primary endpoints as defined |
| M3 | Premature opening and missed train are not measured by one rule across conditions (IMA-28, IMA-29). | Invalidates every existing comparative result |
| M4 | The clearance rule and liveness defects mean the evaluated policy is not the described policy (IMA-15, IMA-16). | Invalidates safety-invariant claims |
| M5 | Revising the policy after pilot runs on the same recordings (IMA-47). | Weakens causal interpretation; disclose, or confirm on new recordings |
| M6 | Ablations change several factors at once (IMA-37). | Weakens causal interpretation of subsystem contribution |
| M7 | Audio cannot influence warnings and was run with wrong preprocessing (IMA-20, IMA-22, IMA-38). | Invalidates all audio-contribution statements to date |
| M8 | One crossing, two sessions, handheld devices, negatives all from one evening (IMA-44). | Limits generalisability |
| M9 | Three negatives totalling one minute per camera. | Limits generalisability; no rate can be estimated |
| M10 | One engine-only event. | Ordinary limitation; report as a case |
| M11 | Synthetic faults on recorded events. | Supports software verification only, not robustness |
| M12 | Single annotator, AI-proposed candidates with template regularity (IMA-07). | Weakens causal interpretation until independently reviewed |
| M13 | 23 train events. | Ordinary limitation; intervals are wide (0 of 23 still allows about 14%) |
| M14 | No held-out site. | Optional future work unless a cross-site claim is made, in which case it is required |
| M15 | Gate timing is a simulation parameter, not measured hardware. | Ordinary limitation; disclose |

**Is the research question testable?** In its current wording, no. A testable version on this dataset: *on recordings of train passages at one crossing, does a stateful decision policy with the same perception inputs as a stateless policy reduce reopening during ground-truth occupancy, and what does it cost in closure time and failure to reopen?* That question survives every limitation above. Statements about a second camera or about audio are secondary and conditional on synchronisation and on a corrected audio path.

**Second annotator.** Feasible and valuable. The boundaries are defined by visible landmarks, annotation takes minutes per event, and the candidates are suspect. A second person marking T1 and T4 on a subset of at least 8 events gives an agreement figure that directly sets a defensible tolerance band for every timing metric. Cost: about two hours of a colleague's time.

**New data.** Not required for a defensible pilot paper with honest scope. Two additions would change what can be claimed: a continuous negative recording of 30–60 minutes, and a handful of passages recorded from tripods with 30 s of lead-in and lead-out and a sync clap. Both are listed as decisions, not demands.

---

## 6. Validity of existing claims

| Claim (source) | Status |
|---|---|
| MTR 0.0% and POR 0.0% for B0–B7 (`docs/REAL_WORLD_EXPERIMENT_REPORT.md` §3) | **Invalid.** No labels were linked; defaults produced the zeros |
| "State machine completely eliminated premature openings", 42.9% vs 0%, p = 0.0039 (same, §4–5; generator lines 339-358) | **Invalid.** Text is a template literal; the metric is decided by code path (IMA-28) |
| "Event recall 100% on 21 events", continuity 76.4% / 91.8% (same) | **Invalid.** Literals; the cohort is 27 |
| "Audio detected 18/21 events" | **Invalid.** Literal; and all audio outputs are invalid (IMA-22) |
| "FAULT_FAIL_SAFE within 0.20 s" under dual loss | **Invalid as stated.** 0.4 s is the simulation tick count from `IDLE`; it is not a response time of anything physical |
| "Out-of-order frames rejected by Rule 8", "stale timestamps rejected by tracker" (tables) | **Invalid.** Neither injection reaches the engine (IMA-34) |
| INV-5 "clearance requires positive rear confirmation" graded A (forensic audit §6) | **Invalid** (IMA-15) |
| Six safety invariants PASSED (orchestrator output) | **Invalid.** Verified over an empty list (IMA-32) |
| Forensic audit recomputed table: B0 POR 20/22, B1 MTR 19/22, B4 0/22, chatter counts 21/23 and 17/23 | **Unverified and withdrawn.** No generating code or per-event records; uses unapproved candidates |
| Forensic audit: cache contamination arithmetic; nuisance closure in 3 of 3 negatives under B4 | **Supported by artifacts.** Detection counts match the active caches; all 27 B4 events have non-zero closed time. Whether the negatives are truly train-free is unconfirmed (IMA-21) |
| Corrective audit: "recovery hysteresis added", "caches cryptographically isolated", "every numerator and denominator accounted for", certification line | **Invalid** (IMA-16, IMA-24, IMA-28, IMA-40) |
| "49 of 49" / "36 of 36" tests passed | **Not evidence of correctness.** 16 tests import no production code; totals not reproducible now (IMA-42, IMA-43) |
| Recovery reports: all assets verified, zero missing, zero auto-approvals | **Partly false** (IMA-04) |
| Checkpoint hashes equal the frozen constants | **Confirmed** by recomputation |
| Detector class names equal rule labels | **Supported** by emitted labels and the split manifest |
| Audio V3 threshold 0.37 calibrated on validation data only | **Supported** by the training script and metrics file |
| Vision mAP 99.46% and rear recall 100% | Development-set figures only; not evidence of field performance (IMA-45) |

---

## 7. Findings register (condensed)

"Blocks" states the earliest activity the finding stops: `inference` = full-dataset raw inference; `evaluation` = decision replay or formal evaluation; `publication` = claims only. "Phase" refers to `IMPLEMENTATION_PLAN_FOR_SONNET.md`.

| ID | Sev | Category | Status | Finding | Blocks | Phase |
|---|---|---|---|---|---|---|
| IMA-01 | P0 | data | confirmed | Single unreplicated working copy; recovery locations named in reports do not exist | inference | 0 |
| IMA-02 | P0 | data | confirmed | 73 index entries flagged assume-unchanged; 68 tracked files missing from disk and hidden from git status | inference | 0 |
| IMA-03 | P1 | data | confirmed | No working, reproducible Python environment; the environment that produced today's outputs is unrecorded | inference | 1 |
| IMA-04 | P1 | reporting | confirmed | Recovery reports contain statements contradicted by the filesystem | none | 0 |
| IMA-05 | P2 | data | confirmed | Vision training labels and data.yaml absent from disk | none | optional |
| IMA-06 | P0 | data | confirmed | All 27 review records are marked APPROVED by 'human_researcher_lead' although no human approval has occurred | evaluation | 9 |
| IMA-07 | P1 | data | suspected | Current candidate timestamps and metadata show template-like regularity | evaluation | 9 |
| IMA-08 | P1 | data | confirmed | Censored boundaries are encoded as observed numeric values | evaluation | 8,9 |
| IMA-09 | P2 | data | suspected | Engine-only candidate cites a detector confidence and has an unresolved T3/T4 definition | evaluation | 9 |
| IMA-10 | P2 | data | confirmed | Horn labels are spectral candidates, not audibly verified | evaluation | 9 |
| IMA-11 | P0 | timing | confirmed | Cross-camera fusion uses a hardcoded zero offset that the media metadata contradicts | evaluation | 5 |
| IMA-12 | P2 | timing | confirmed | Frame timestamps are frame_index / nominal FPS, not presentation timestamps | none | 4 |
| IMA-13 | P2 | timing | confirmed | Audio evidence is stamped at window start and only the front camera's audio is used | none | 4 |
| IMA-14 | P1 | inference | confirmed | Temporal confirmation can be satisfied by a single detection | evaluation | 7 |
| IMA-15 | P0 | safety | confirmed | Clearance logic does not implement positive rear confirmation | evaluation | 3 |
| IMA-16 | P0 | safety | confirmed | No liveness: closed states have no exit without a specific label sequence and the fault state is absorbing | evaluation | 3 |
| IMA-17 | P1 | safety | confirmed | Sensor health is not measured; unknown is treated as healthy | evaluation | 3 |
| IMA-18 | P2 | safety | confirmed | Sources are classified by substring matching on their identifiers | none | 3 |
| IMA-19 | P2 | safety | confirmed | The transition-legality table is not enforced by the decision engine | none | 3 |
| IMA-20 | P1 | methodology | confirmed | Protocol and code disagree on whether audio may initiate a warning | evaluation | 3 |
| IMA-21 | P1 | safety | confirmed | The detector fires in all three no-train recordings and the existing output shows closure in every one | evaluation | 9 |
| IMA-22 | P0 | inference | confirmed | Audio V3 inference does not apply the training normalisation | inference | 2 |
| IMA-23 | P1 | inference | confirmed | Three different audio thresholds are in effect | evaluation | 2 |
| IMA-24 | P0 | inference | confirmed | Inference caches have no provenance and are reused by default | inference | 4 |
| IMA-25 | P1 | inference | confirmed | The parameter-freeze and leakage checks cannot fail | inference | 2 |
| IMA-26 | P1 | inference | confirmed | The result tree mixes outputs from different code versions | evaluation | 0,4 |
| IMA-27 | P2 | inference | confirmed | No run registry for fusion experiments; the registry is polluted by test runs | none | 4 |
| IMA-28 | P0 | evaluation | confirmed | Premature opening is defined differently for baselines and for the proposed system | evaluation | 8 |
| IMA-29 | P0 | evaluation | confirmed | Ground truth is never linked and every event is scored as a train event | evaluation | 8 |
| IMA-30 | P1 | evaluation | confirmed | Undefined metrics can still surface as numbers or disappear | evaluation | 8 |
| IMA-31 | P0 | methodology | suspected | The recordings are too short at both ends for the protocol's primary endpoints | evaluation | 8 |
| IMA-32 | P1 | evaluation | confirmed | Safety-invariant verification is vacuous | evaluation | 8 |
| IMA-33 | P2 | evaluation | confirmed | Statistical procedures differ from the protocol and ignore the design | publication | 8 |
| IMA-34 | P1 | testing | confirmed | Two fault modes do nothing, yet reports describe them as handled | evaluation | 7 |
| IMA-35 | P2 | testing | confirmed | Frame-drop and other injections have imprecise semantics | evaluation | 7 |
| IMA-36 | P3 | methodology | confirmed | Dual-blackout condition tests only entry into the fault state | none | 7 |
| IMA-37 | P1 | methodology | confirmed | The documented ablation matrix is not implemented and the implemented one is confounded | evaluation | 7 |
| IMA-38 | P1 | methodology | confirmed | The audio modality currently has almost no path to affect an outcome | evaluation | 7 |
| IMA-39 | P0 | reporting | confirmed | Report, table and figure generators contain hardcoded results and synthetic data | publication | 11 |
| IMA-40 | P1 | reporting | confirmed | Earlier audits contain untraceable numbers and a fix that was not made | publication | 11 |
| IMA-41 | P2 | reporting | confirmed | Active protocol documents describe components that do not exist | none | 11 |
| IMA-42 | P1 | testing | confirmed | Sixteen 'safety' tests import no production code | evaluation | 3,7,8 |
| IMA-43 | P2 | testing | unverified | The canonical test totals cannot be reproduced from the current tree | none | 1 |
| IMA-44 | P1 | methodology | confirmed | Negative controls and seven other events come from one short evening session; total negative exposure is about one minute per camera | publication | 11 |
| IMA-45 | P2 | methodology | confirmed | Vision test-set performance does not describe field behaviour | publication | 11 |
| IMA-46 | P2 | methodology | confirmed | The audio model is trained on a different acoustic domain | publication | 11 |
| IMA-47 | P1 | methodology | confirmed | The decision policy will be revised after its outputs on the evaluation recordings have been seen | publication | 3,10 |

Reconciliation with earlier identifiers: CF-02 (orchestrator path) is fixed in code (`run_real_world_experiments.py:53`). CF-04 (audio threshold) is fixed in `layer_b_processor.py` and superseded by IMA-23, which is broader. PA-02 (class names) is closed by evidence. CF-05 → IMA-11. TI-02 → IMA-24. TI-03 and EP-03 → IMA-29. PA-01 → IMA-13. PA-03 → IMA-14 and IMA-16. C-01 to C-08 of the forensic audit stand as invalidations; its replacement numbers do not (IMA-40).

---

## 8. Relationship to earlier documents

Nothing is deleted or edited. This table says how each should now be read.

| Document | Standing |
|---|---|
| `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` v9 | Historical. Superseded by `EXPERIMENT_DESIGN_FINAL.md` for endpoints, taxonomy, timing policy and statistics. Boundary definitions T0–T4 (§5) remain in force |
| `docs/FINAL_ABLATION_MATRIX.md` v7 | Historical. E1–E10 identifiers are kept; definitions are restated in the design document |
| `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` v7 | In force for boundary semantics and the three-stage lifecycle. Approval mechanics superseded by design §7. I did not review all 847 lines |
| `docs/FINAL_EXPERIMENT_DATA_FLOW.md`, `FINAL_TEST_PLAN.md` | Historical. Not reviewed line by line |
| `docs/REAL_WORLD_EXPERIMENT_REPORT.md` (and archived copy) | **Withdrawn in full** |
| `docs/FORENSIC_EXPERIMENT_AUDIT.md` | §1–2, §4.2 (detection counts), §5, §8.1 stand. §3 and the chatter counts are withdrawn |
| `docs/CORRECTIVE_EXPERIMENT_AUDIT.md` | §5 (drop defect) stands. §2, §3, §6.3–6.4, §10.2 and the certification line are withdrawn |
| `docs/INDEPENDENT_RESEARCH_DESIGN_AUDIT.md` (and root copy) | Stands as an earlier, narrower audit; its open items are mapped above |
| `docs/EXECUTIVE_RESEARCH_READINESS_REPORT.md`, `results/testing/FINAL_TEST_RESULTS.md` | Historical; test totals are not evidence (IMA-42) |
| `RECOVERY_INVENTORY_REPORT.md`, `RECOVERY_RESTORATION_REPORT.md` | Historical; qualified by IMA-04 |
| `results/experiments/**`, `results/archive/**` | Frozen legacy evidence. Not results |
| `data/ground_truth/reviews/**` | Invalid as approvals (IMA-06). Preserved |

---

## 9. What I did not verify

- **No code was executed.** Every behavioural statement about the engine, injector and metrics comes from reading the source. Where I describe what a run would do (the four-state cycle, the confirmation overlap, the feasibility arithmetic) it is derived, not observed.
- **Checkpoint contents.** No working PyTorch exists on the machine, so I did not read the keys stored in either audio checkpoint or the class names stored in the YOLO checkpoint. IMA-22 rests on the trainer and the loader disagreeing in source.
- **Pixels and sound.** I viewed no frame and listened to no audio. I cannot say whether any candidate timestamp is right, or whether `no_train_events/event_002` contains a rail vehicle.
- **Media hashes.** 2 of 56 files re-hashed.
- **Legacy cache provenance.** The 60 older cache files are attributed to earlier models by date and by the forensic audit's manifest, not by anything in the files.
- **GitHub.** I compared against the local `origin/main` reference and did not contact the remote.
- **Documents not read in full:** `FINAL_GROUND_TRUTH_PROTOCOL.md`, `FINAL_EXPERIMENT_DATA_FLOW.md`, `FINAL_TEST_PLAN.md`, `HAZARD_MODEL.md`, `RESEARCH_DECISIONS.md`, `README.md`, `AUDIO_MODEL_V3_ESC50_REPORT.md`, the 26 archived documents, both `.docx` reports, and `reviews/PHASE2_VERIFICATION_REPORT.md` beyond searched lines.
- **Code not read in full:** the `annotation/` package, `demo/`, `vision/{evaluator,failure_analysis,temporal,trainer,yolo_adapter}.py`, `config/loader.py`, `data/{contracts,manifest,split,validator}.py`, the audio V1/V2 scripts, `scripts/run_canonical_tests.py`, and `research/scripts/`.
- **How the working tree reached the Desktop** after the recovery reports were written.
