# Implementation Plan for Claude Sonnet

## Railway Crossing Vision–Audio Fusion Safety System

| | |
|---|---|
| Version | 1.0 (2026-10-13) |
| Read first | `docs/INDEPENDENT_MASTER_AUDIT.md` (what is wrong), `docs/EXPERIMENT_DESIGN_FINAL.md` (what to build), `docs/OPEN_DECISIONS_AND_BLOCKERS.md` (what the researcher must decide) |
| Finding identifiers | `IMA-nn`, defined in `docs/FINDINGS_REGISTER.csv` |
| Repository at time of writing | `/Users/sayemuddin/Desktop/Train_automation`, `main` at `d4db94d` |

You are implementing a remediation, one phase at a time. Each phase has a stated acceptance test. A phase is done when that test passes and its artifacts exist — not when the code looks finished and not when tests "return zero".

---

## 0. Rules that apply to every phase

**Never**

1. Delete, move, rename or overwrite anything under `data/raw/`, `data/ground_truth/proposals/`, `data/ground_truth/reviews/`, `data/ground_truth/snapshots/`, `results/experiments/`, `results/archive/`, `results/testing/`, `experiments/*/checkpoints/`, `models/`, `docs/archive/`, or any existing `docs/*.md`.
2. Modify a checkpoint, or change the value of a frozen parameter (design §5.1).
3. Create, edit or sign approved ground truth, `APPROVAL_MANIFEST.json`, or any field stating that a human reviewed something.
4. Use outputs on the evaluation recordings (legacy caches, legacy results, or new raw outputs) to choose, adjust or justify a parameter, threshold, rule or label.
5. Write a result value as a literal in code, a table, a figure or a document.
6. Use `git add -A`, `git add .`, `git clean`, `git reset --hard`, `git checkout -- .`, `git stash`, `--force` pushes, or any history rewrite. Stage explicit paths only.
7. Describe anything as certified, SIL-rated, EN 5012x-compliant or physically safe.

**Always**

- Work on a branch per phase, created from the previous phase's accepted commit. Small commits. One concern per commit.
- Write new outputs only under `results/runs/<run_id>/`, `data/sync/`, `data/ground_truth/approved/` (templates and validators only, never values), `docs/preservation/`, `docs/verification/`.
- Tests for policy and metrics use synthetic inputs constructed in the test. They import production classes. A test that defines the thing it tests does not count.
- Record what you ran and what it printed in `docs/verification/PHASE_<n>_RECORD.md`: commands, commit hash, test counts (collected, passed, failed, skipped), and any deviation from this plan.

**Stop and ask the researcher when**

- A precondition or an "expected" observation in this plan is false.
- A decision marked `[D-n]` is still open and the phase depends on it.
- A step would touch a path in the "never" list.
- A checkpoint, media file or annotation hash differs from its recorded value.
- You find a defect not in the register that changes a result. Add it to the phase record; do not fix it silently.

---

## Phase 0 — Preserve the baseline

**1. Objective.** Make a verified second copy of everything, make Git tell the truth, and commit the current state unchanged, so every later step can be undone. (IMA-01, IMA-02, IMA-04, IMA-26)

**2. Preconditions.** `[D-1]` answered: backup destination and whether to push. No other process is writing to the repository.

**3. Files.** New only: `docs/preservation/BASELINE_STATE_20261013.txt`, `docs/preservation/EVIDENCE_MANIFEST_20261013.sha256`, `docs/preservation/ASSUME_UNCHANGED_PATHS.txt`, `docs/preservation/REWRITTEN_TRACKED_FILES.diff`, `docs/preservation/LEGACY_RESULTS_MANIFEST.sha256`.

**4. Actions.**
1. Save `git rev-parse HEAD`, `git status --porcelain=v1`, `git ls-files -v | grep '^h'` and `git ls-files -d` to the baseline-state file. Expected: 73 flagged paths, 68 deleted.
2. Write the evidence manifest: SHA-256, size and path for every file in the repository except `.git/`, `.venv/`, `__pycache__/`, `.pytest_cache/`. Include `scratch/`, media and weights.
3. Copy the whole directory (same exclusions) to the destination from `[D-1]` with a copy tool that preserves timestamps and does not delete. Re-hash the copy and compare with the manifest.
3a. List (do not copy, do not run Git in) `~/Library/Mobile Documents/com~apple~CloudDocs/Desktop/Train_automation` and record any file that has no counterpart in the working tree, for the researcher to decide on. Known example: `scripts/create_event_label_templates.py`. Commands there can stall; use a timeout.
4. Clear the assume-unchanged flag on the 73 recorded paths.
5. For the five flagged files that exist (`config/__init__.py`, `config/exceptions.py`, `data/sync.py`, `fusion/__init__.py`, `fusion/evidence.py`), save `git diff HEAD` to the diff file. Do not revert them.
6. For each of the 68 paths that does not exist on disk, restore it from `HEAD`. Check non-existence per path immediately before restoring; skip and report any that exists.
7. Create branch `preserve/2026-10-13-baseline`. Stage by explicit path: `src/`, `tests/`, `scripts/`, `docs/`, the three root-level reports, `data/ground_truth/`, `data/manifests/`, `data/splits/`, `results/testing/`, `results/experiments/` and `results/archive/` (JSON, JSONL, CSV, MD, TeX and PNG), non-weight files under `experiments/`. Do not stage media, weights, `scratch/`, `.venv/`, `ESC-50-master/`, `Unseen_Video/`, `.commandcode/`. Do not edit `.gitignore` in this phase.
8. One commit: `chore(preservation): snapshot working tree before remediation (no functional change)`. Tag `baseline-pre-remediation-20261013`.
9. If `[D-1]` permits, push the branch and tag.

**5. Tests.** None added.

**6. Acceptance.**
- Copy hash comparison: zero mismatches, zero missing.
- `git ls-files -v | grep '^h'` prints nothing. `git ls-files -d` prints nothing.
- Re-hashing the working tree shows no pre-existing file changed (the only new files are the 68 restored ones and the five preservation files).
- A fresh clone of the branch into a temporary directory contains `src/railway_detection/fusion/decision_engine.py`, `scripts/run_real_world_experiments.py` and `data/ground_truth/proposals/train_events/event_001_proposal_v6.json`, each with the hash in the manifest.

**7. Artifacts.** The five preservation files; the branch; the tag; the external copy.

**8. Rollback.** Delete the branch and tag. Remove the 68 restored files using the recorded list. Re-apply the flags from `ASSUME_UNCHANGED_PATHS.txt` if the previous index state is wanted. The external copy is never rolled back.

**9. Must remain unchanged.** Content of every file that existed before the phase. Git history.

**10. Unblocks.** Phase 1; Phase 5; Phase 9 (human review can start now).

---

## Phase 1 — Rebuild the environment and establish what the tests say

**1. Objective.** A reproducible interpreter that can import the package and the ML stack, a recorded test baseline, and direct inspection of both checkpoints. (IMA-03, IMA-43; confirms IMA-22)

**2. Preconditions.** Phase 0 accepted. `pyproject.toml` restored.

**3. Files.** New: `requirements.lock`, `docs/preservation/ENVIRONMENT.md`, `docs/verification/CHECKPOINT_INSPECTION.md`, `docs/verification/TEST_BASELINE_<commit>.txt`. `pyproject.toml` only if a dependency used by the code is undeclared.

**4. Actions.**
1. Create a new virtual environment with Python 3.11 at the location agreed in `[D-1]`, outside any cloud-synced folder. Do not repair the existing `.venv`.
2. Install the versions found in the old environment's metadata: torch 2.13.0, torchvision 0.28.0, ultralytics 8.4.121, numpy 2.4.6, opencv-python 5.0.0.93, matplotlib 3.11.1, pytest 9.1.1, plus scipy and PyYAML at the versions pip resolves. Install the package in editable mode. Write the resolved set to `requirements.lock`.
3. Record Python, package, ffmpeg and OS versions in `ENVIRONMENT.md`.
4. Read, without running inference: the key names and scalar values stored in the Audio V3 and Audio V2 checkpoints, and the class-name mapping stored in the YOLO checkpoint. Write them to `CHECKPOINT_INSPECTION.md`.
5. Run the existing test suite once, unmodified. Save collected, passed, failed, skipped and error counts. Do not fix failures in this phase.

**5. Tests.** None added.

**6. Acceptance.**
- One command imports `railway_detection`, `torch`, `ultralytics` and `cv2`.
- `pytest --collect-only` reports zero collection errors, or each error is listed with its cause.
- `CHECKPOINT_INSPECTION.md` states whether the Audio V3 checkpoint contains `norm_mean`, `norm_std` and `operating_threshold`, with values, and the YOLO class names. **Expected:** all three keys present, threshold 0.37, names `{0: front, 1: rear, 2: side}`. If any expectation is false, stop.
- Recomputed SHA-256 of both frozen checkpoints equals the constants in `leakage_guard.py`.

**7. Artifacts.** Lock file; environment record; checkpoint inspection; test baseline.

**8. Rollback.** Remove the new environment; revert the commit.

**9. Must remain unchanged.** All source code. All checkpoints.

**10. Unblocks.** Phases 2, 3, 4, 5.

---

## Phase 2 — One frozen configuration; correct audio path

**1. Objective.** Every component takes its parameters from one hashed configuration, the audio classifier applies the training normalisation, and the guards can fail. (IMA-22, IMA-23, IMA-25, IMA-13 in part)

**2. Preconditions.** Phase 1 accepted with the expected checkpoint keys. `[D-5]` and `[D-6]` answered, or their defaults accepted.

**3. Files.** New: `configs/frozen_experiment_v1.yaml`, `src/railway_detection/experiments/frozen_config.py`. Edit: `audio/model.py`, `audio/pipeline.py`, `fusion/decision_engine.py` (constructor only), `simulation/runner.py`, `experiments/leakage_guard.py`.

**4. Changes.**
- The configuration file holds exactly the parameters in design §5.1, both checkpoint paths and hashes, and the prohibited Audio V2 hash. A loader returns an immutable object and a SHA-256 of the canonical content.
- `PyTorchTrainHornClassifier` reads the normalisation statistics under the names the trainer writes. Loading a checkpoint that lacks them raises. The threshold comes from the configuration; if the checkpoint stores a different threshold, raise. Constructing the classifier without a checkpoint is allowed only when a model object is passed explicitly.
- `AudioEvidencePipeline` emits one record per window carrying the probability, whatever its value, stamped at the window end. A missing classifier raises in the experiment path.
- `MultimodalDecisionEngine` and `EventSimulationRunner` take the configuration object. Remove numeric defaults for frozen parameters.
- `leakage_guard`: compare the values read back from the constructed components with the configuration; refuse any checkpoint whose hash equals the prohibited hash; compare SHA-256 of every evaluation media file with every file hash in the audio and vision training manifests.
- Do not change feature extraction, model architecture or any parameter value.

**5. Tests.** `tests/unit/test_frozen_config.py` (hash stability; mutation changes the hash); `tests/unit/test_audio_checkpoint_contract.py` (loads the real frozen checkpoint; asserts mean, std, threshold; asserts a checkpoint without normalisation raises); `tests/unit/test_guards_can_fail.py` (wrong threshold, prohibited checkpoint, evaluation file hash present in a training manifest — each aborts); `tests/unit/test_audio_pipeline_records.py` (one record per window, end-stamped, probability present). If per-window training features are stored under `data/processed/audio/v3/`, add a parity test: features from the inference path equal the stored features for one training clip within 1e-5.

**6. Acceptance.** All new tests pass. A search of `src/railway_detection/{fusion,simulation,experiments,audio}` for the literals `0.37`, `0.3700`, `0.35` and `0.50` finds them only in comments or in the configuration loader's schema. The existing decision-engine unit tests still pass after being updated to pass a configuration.

**7. Artifacts.** Configuration file and its hash recorded in the phase record.

**8. Rollback.** Revert the phase branch. No data is produced.

**9. Must remain unchanged.** Parameter values; checkpoints; `audio/features.py`; decision logic (that is Phase 3).

**10. Unblocks.** Phase 4 (audio), Phase 3.

---

## Phase 3 — Sensor health and decision policy

**1. Objective.** Implement design §5 and §6.1 exactly, verified on synthetic traces only. (IMA-14, IMA-15, IMA-16, IMA-17, IMA-18, IMA-19, IMA-20, IMA-42, IMA-47)

**2. Preconditions.** Phase 2 accepted. `[D-4]` and `[D-5]` answered or defaults accepted. **No evaluation recording, legacy cache or raw output may be opened during this phase.**

**3. Files.** Edit: `fusion/evidence.py` (typed status, reason, modality, role), `fusion/source_tracker.py`, `fusion/collector.py`, `fusion/rules.py`, `fusion/decision_engine.py`, `simulation/state_machine.py`, `simulation/runner.py`. New tests as below.

**4. Changes.**
- Sources are registered with modality and role from the run configuration. Remove every substring test on source identifiers.
- The collector delivers records tick by tick; each record is consumed once in `(t − tick, t]`. Availability at a tick is computed only from records delivered up to that tick, with the 2.0 s staleness rule. An expected source with no record is unavailable.
- Train evidence, rear evidence, audio evidence and the active flag as in design §5.2.
- State transitions as in the table in design §5.4, including the clearance-rule variants `ABS` and `REAR`, fault entry after 2 ticks, and recovery into `TRAIN_PRESENT` after 3.0 s of availability.
- One legality table in `simulation/state_machine.py`. The engine checks each transition against it and raises on violation.
- The simulation loop processes frames in delivery order and records `t_warn`, `t_blocked`, reopening instants and `t_open` in its output. It takes no ground-truth arguments.
- Mark `tests/test_fault_injection_scenarios.py` and `tests/test_forensic_regressions.py` with a pytest marker `legacy_nonproduction` and exclude that marker from the gate. Do not delete them.

**5. Tests** (all synthetic, all importing production classes).
- `test_policy_table.py`: one case per row of design §5.4, both clearance variants, both audio settings.
- `test_sensor_health_cases.py`: the eight cases of design §6.1, plus "expected source never produces a record".
- `test_policy_properties.py`: (a) one isolated detection never yields `WARNING` with confirm 2; (b) no opening command is issued on a tick with train evidence; (c) the dwell restarts on new train evidence; (d) a stream of `side`-only detections followed by silence reaches `IDLE` under `ABS` and stays closed under `REAR`; (e) liveness bound of 14.5 s from every state under `ABS`; (f) fault recovery never passes directly to an open barrier; (g) audio alone never grants or shortens clearance; (h) identical input gives byte-identical output.
- `test_transition_legality.py`: an illegal transition raises; tests import the table from `src`.

**6. Acceptance.**
- All tests above pass.
- Mutation record in `docs/verification/MUTATION_CHECKS_phase3.md`: for each of — restore `side` to the departure set and the old cycle; widen the window to 0.25 s; remove fault recovery; remove the legality check; treat an unregistered source as healthy — apply the mutation on a scratch branch, show at least one gated test fails, discard the mutation.
- `docs/verification/POLICY_FREEZE.md` records the commit hash, configuration hash and date. From this point the policy changes only with a new freeze record and a stated reason.

**7. Artifacts.** Mutation record; policy freeze record.

**8. Rollback.** Revert the phase branch.

**9. Must remain unchanged.** Frozen parameter values; barrier model; anything under `results/` and `data/`.

**10. Unblocks.** Phase 7.

---

## Phase 4 — Raw inference outputs and run isolation

**1. Objective.** A per-stream inference path that writes complete, self-describing raw outputs into a content-addressed run directory, can resume, and classifies every stream. (IMA-12, IMA-13, IMA-24, IMA-26, IMA-27)

**2. Preconditions.** Phase 2 accepted.

**3. Files.** Edit: `vision/video.py` (yield decoder presentation time and a per-frame status). New: `experiments/run_identity.py`, `experiments/raw_inference.py`, `experiments/stream_status.py`, `scripts/run_raw_inference.py`. Leave `experiments/layer_b_processor.py` and `scripts/run_real_world_experiments.py` in place; add a module docstring line marking them legacy and import neither from new code.

**4. Changes.** Implement design §4 as written: run identity and manifest; directory layout; headers; atomic writes; completion records; raw vision records at confidence ≥ 0.05 with status; raw audio records for every window for **both** cameras' audio; stream status from the media manifest's expected list; refusal to start with a dirty working tree; the quarantined duplicate on an explicit deny list.

**5. Tests.** Run identifier changes when any identity input changes and is stable otherwise; interrupted write leaves no file that looks complete and resume redoes only that stream; status classification on small synthetic videos generated in the test, including a truncated file and a file whose decoder errors mid-way; any attempt to open a path under `results/experiments` or `results/archive` from new code fails the test; running the suite leaves `results/experiment_registry.jsonl` byte-identical.

**6. Acceptance.** Tests pass. A smoke run on `engine_events/event_001` (both streams, picture and sound) produces four raw files with headers, four `FULL` rows, and a manifest whose checkpoint hashes equal the frozen constants. Last presentation timestamp ≤ container duration for both.

**7. Artifacts.** `results/runs/<run_id>/` from the smoke run.

**8. Rollback.** Revert the branch; delete the smoke run directory.

**9. Must remain unchanged.** Legacy caches and results. Model thresholds.

**10. Unblocks.** Phase 6.

---

## Phase 5 — Camera offset estimation

**1. Objective.** Produce per-event offset estimates with uncertainty for the researcher to accept or reject. (IMA-11)

**2. Preconditions.** Phase 1 accepted. `[D-3]` answered or default accepted. Independent of Phases 2–4.

**3. Files.** New: `src/railway_detection/data/sync_estimation.py`, `scripts/estimate_camera_offsets.py`, `tests/unit/test_sync_estimation.py`. Output: `data/sync/sync_offsets_v1.json`, `data/sync/plots/<cohort>_<event>.png`.

**4. Changes.** Implement design §6.3 steps 1–4 and 6. Extract audio to a working directory under `data/sync/`. The status written by code is `candidate_aligned` or `unaligned` only. The fields `status_final`, `reviewer` and `review_date` are written as `null`.

**5. Tests.** Two synthetic signals sharing a component with a known lag, each with independent noise: error ≤ 5 ms at several lags including negative. Two unrelated signals: `unaligned`. A signal whose lag differs between halves: uncertainty reflects it.

**6. Acceptance.** Tests pass. The output file has 27 rows with all fields of design §6.3 and no value in the human fields.

**7. Artifacts.** Offsets file, plots. The researcher then completes step 5 of design §6.3 by hand.

**8. Rollback.** Delete `data/sync/`; revert the branch.

**9. Must remain unchanged.** Media. The thresholds in design §6.3.

**10. Unblocks.** Fused (`FB`) conditions in Phases 7 and 10, once the researcher has accepted offsets and the mode rule has been applied.

---

## Phase 6 — Full-dataset raw inference

**1. Objective.** Raw predictions for every expected stream, each classified. (Gate D)

**2. Preconditions.** Gates A and B passed. Phase 4 accepted. Working tree clean. Annotation approval and synchronisation are **not** preconditions.

**3. Files.** None changed.

**4. Actions.** Run `scripts/run_raw_inference.py` over all 54 video and 54 audio streams. If interrupted, resume with the same run identifier. Then compute the D1 stream descriptors (design §8.3) from the raw files.

**5. Tests.** None added.

**6. Acceptance.** `stream_status.json` has 108 rows; each is `FULL`, or carries a recorded reason and the affected event is listed as excluded. Every raw file's header hashes match the media manifest and the frozen checkpoints. The quarantined duplicate has no output. A second invocation with resume does nothing. Descriptors exist for every `FULL` stream.

**7. Artifacts.** `results/runs/<run_id>/{run_manifest.json, stream_status.json, raw/, metrics/descriptors/}`.

**8. Rollback.** The run directory is new and self-contained; set it aside and start a new run. Never overwrite a run.

**9. Must remain unchanged.** Everything outside the run directory.

**10. Unblocks.** Phase 7 replays. Pre-approval reporting of D1.

---

## Phase 7 — Conditions, replay and fault injection

**1. Objective.** One replay path that realises every condition in design §3.2 from raw outputs, with fault injection that does what its name says. (IMA-28 in part, IMA-34, IMA-35, IMA-36, IMA-37, IMA-38)

**2. Preconditions.** Phases 3 and 6 accepted. For `FB` conditions: accepted offsets and the mode rule applied.

**3. Files.** New: `experiments/conditions.py`, `experiments/replay.py`, `scripts/run_replay.py`. Edit: `simulation/failure_injector.py`. Leave `experiments/runner.py` in place, marked legacy, unused.

**4. Changes.**
- `conditions.py` holds the condition table: alias, factor code, tier, and injection schedule. It is the only definition of a condition.
- `replay.py` builds the evidence stream for a condition from raw files (camera subset, audio on or off, thresholds from the configuration, offsets when fused), applies injection, runs the policy selected by the `P` factor through the same loop, and writes the decision trace. `SL` and `SM` are two policy objects behind one interface.
- Injection operates on individual source records before delivery. Frame loss is per source with probability `p`, using a generator seeded from run identifier, event and source. Parameters are required; a missing rate raises. Delay shifts delivery time, so staleness arises through the health model. Disorder permutes delivery order within its window. Injected detections name their source. Each injection writes the count of records affected to `injections/`.

**5. Tests.** Each adjacent pair named in design §3.2 differs in exactly one factor (asserted from the table); the same raw input under two aliases with equal factors yields identical traces; each stress condition's injection count is greater than zero on a synthetic stream; out-of-order delivery reaches the engine's rejection path; delay produces `stale` unavailability; realised loss is within ±5 percentage points of `p` on 1,000 records; replay is deterministic.

**6. Acceptance.** Tests pass. Decision traces exist for E4, E5 and E7 (fused where permitted, and independent-camera) for all 27 events, plus the `REAR` variant of E5 and E7. For any stress condition run, the injection log shows a non-zero affected count for every event, or the event is listed with the reason.

**7. Artifacts.** `results/runs/<run_id>/decisions/`, `injections/`.

**8. Rollback.** Delete the `decisions/` and `injections/` subdirectories; revert the branch. Raw outputs are untouched.

**9. Must remain unchanged.** Raw outputs. The policy (frozen in Phase 3).

**10. Unblocks.** Phase 8; pre-approval reporting of V1, M10, F1.

---

## Phase 8 — Metrics, eligibility and statistics

**1. Objective.** Implement the metric contract of design §8 and the statistics of §9, validated on hand-computed fixtures. (IMA-08, IMA-28, IMA-29, IMA-30, IMA-31, IMA-32, IMA-33)

**2. Preconditions.** Phase 7 accepted. `[D-10]` answered or default accepted.

**3. Files.** New: `evaluation/metric_contract.py`, `evaluation/ground_truth.py`, `evaluation/invariants.py`, `scripts/run_evaluation.py`. Rewrite: `evaluation/metrics.py`, `experiments/statistics.py`. Leave `experiments/failure_classifier.py` in place, unused.

**4. Changes.**
- Metric record and aggregate types with the statuses of design §8.1. A zero evaluable count yields an undefined aggregate. The formatter raises on undefined or censored values requested as plain numbers.
- Ground-truth loader per design §7.2 step 6: approval manifest only; hash check; invalidation list; event-type-aware schema; explicit censoring field; clock label per marker.
- One evaluator implementing M1–M10, N1, D1, V1, F1 from a decision trace and, where needed, approved labels and offsets. No condition-specific branch. Clock rule for independent-camera mode as in design §8.3.
- Statistics: Wilson interval (undefined for zero denominator), exact McNemar, Wilcoxon signed-rank, bootstrap of the median difference, Holm adjustment across the three primary contrasts. Inputs are per-event metric records already filtered by eligibility.
- `run_evaluation.py` has two modes. `--pre-approval` computes only the metrics listed in design §8.4 and refuses any other. `--formal` requires the approval manifest and fails closed.

**5. Tests.** For each metric: a fixture trace with hand-computed expected value for each status it can take, including left- and right-censoring, the feasibility screen for M3, and M7's three classes. Loader: refuses `reviews/`, `proposals/`, an unlisted file, a hash mismatch, an invalidated hash, a censored marker without the censoring field; accepts a correctly listed fixture. Negatives and the engine event never appear in a train denominator. Negative lead time preserved. Formatter raises. Each V1 invariant fails on a deliberately violating trace and reports the number of steps examined. McNemar and Wilcoxon agree with published worked examples.

**6. Acceptance.** Tests pass. `--pre-approval` on the Phase 7 traces writes D1, V1, M10 and (if `[D-7]` is confirmed) N1, each with `n_total`, `n_evaluable` and exclusions. `--formal` without an approval manifest exits non-zero and writes nothing.

**7. Artifacts.** `results/runs/<run_id>/metrics/pre_approval/`.

**8. Rollback.** Delete `metrics/pre_approval/`; revert the branch.

**9. Must remain unchanged.** Decision traces; raw outputs; metric definitions in the design (change the document first, with the researcher, if one proves unworkable).

**10. Unblocks.** Phase 10, once Gate F is passed.

---

## Phase 9 — Annotation review support (human approval)

**1. Objective.** Give the researcher what is needed to review and approve, and make the invalid approvals unusable. (IMA-06, IMA-07, IMA-08, IMA-09, IMA-10, IMA-21)

**2. Preconditions.** Phase 0 accepted. Runs in parallel with Phases 1–8. `[D-2]`, `[D-7]`, `[D-8]`, `[D-9]` answered.

**3. Files.** New: `evaluation/gt_schema.py`, `scripts/build_review_packets.py`, `scripts/validate_approved_ground_truth.py`, `data/ground_truth/INVALIDATED_REVIEWS.json`, `data/ground_truth/approved/README.md`, `data/ground_truth/approved/TEMPLATE_{train,no_train,engine}.json`.

**4. Changes.**
- Schema per design §7.2–7.4.
- Review packets: for each event and each candidate marker, frames at native rate for ±1.5 s around the candidate from the camera named in the candidate, with frame index and local time burned into the file name, plus the audio clip around each candidate horn onset. Written under `scratch/review_packets/` (already ignored). **No detector output, score or decision may appear in a packet.**
- `INVALIDATED_REVIEWS.json`: path and SHA-256 of each of the 27 existing review files, with the reason "not produced by human review; references superseded proposals".
- Templates contain field names and `null` values only.
- The validator checks approved files against the schema and the approval manifest and prints, per event, which markers are observed, censored or not applicable.

**5. Tests.** Schema accepts each template once filled with fixture values and rejects: missing censoring field, a train marker in a no-train file, a no-train file without the train-free statement, an engine file with differing T3 and T4.

**6. Acceptance for the software part.** Tests pass; packets exist for 27 events; no value appears in any approved-directory file.

**Human part (not done by you).** The researcher reviews every event, writes approved files, has a second annotator mark the agreed subset if `[D-8]` is taken up, and creates and signs `APPROVAL_MANIFEST.json`.

**7. Artifacts.** Schema, packets, invalidation list, templates, validator.

**8. Rollback.** Revert the branch. Delete `scratch/review_packets/`.

**9. Must remain unchanged.** `proposals/`, `reviews/`, `snapshots/`.

**10. Unblocks.** Gate F, hence Phase 10.

---

## Phase 10 — Formal evaluation

**1. Objective.** Compute the predeclared metrics once, on approved labels, with the frozen policy. (Gate G)

**2. Preconditions.** Gates D, E and F passed. `POLICY_FREEZE.md` commit is an ancestor of the commit used. The mode rule of design §6.3 has been applied and recorded. Working tree clean.

**3. Files.** None changed.

**4. Actions.** Run `scripts/run_evaluation.py --formal` for the conditions of the minimum experiment, then any secondary and stress conditions that have traces. Write `EVALUATION_RECORD.json`: run identifier, commit, configuration hash, approval-manifest hash, offsets-file hash, mode (fused or independent), list of conditions.

**5. Tests.** None added.

**6. Acceptance.** Every reported aggregate carries numerator, `n_evaluable`, `n_total` and the excluded events with reasons. The per-event feasibility table for M3 exists. The three primary contrasts are reported with discordant counts or paired differences and Holm-adjusted p-values. Sensitivity results at `±u` (and `±δ` when fused) exist. S1 and S2 are shown separately.

Any re-run after this point is logged in `docs/verification/EVALUATION_LOG.md` with its reason. A re-run prompted by disliking a result is not a valid reason.

**7. Artifacts.** `results/runs/<run_id>/metrics/formal/`, `EVALUATION_RECORD.json`.

**8. Rollback.** Formal outputs are never deleted. A superseding evaluation gets a new directory and a log entry.

**9. Must remain unchanged.** Policy, configuration, labels, offsets, raw outputs, traces.

**10. Unblocks.** Phase 11.

---

## Phase 11 — Reporting

**1. Objective.** Tables, figures and text in which every number is read from the formal metrics and can be traced. (IMA-39, IMA-40, IMA-41, IMA-44, IMA-45, IMA-46; Gate H)

**2. Preconditions.** Phase 10 accepted.

**3. Files.** New: `scripts/build_report_artifacts.py`, `docs/CLAIMS_LEDGER.md`, `docs/RESULTS_<run_id>.md`. Leave `scripts/generate_publication_tables.py`, `scripts/generate_publication_figures.py`, `scripts/build_research_report_doc.py` and the report template in the legacy orchestrator untouched and unused.

**4. Changes.**
- The generator takes a run directory and reads only `metrics/formal/` and `EVALUATION_RECORD.json`. Every table and figure carries the run identifier. Undefined and censored values are rendered as such.
- `CLAIMS_LEDGER.md`: one row per sentence in the results text that states a finding — the sentence, the metric file and key it comes from, the run identifier.
- The results document includes the limitations list of design §10 verbatim and the cohort table with sessions, devices and exposure.

**5. Tests.** A static check over the generator's syntax tree: no numeric literal is passed to a table cell or plotted series (layout constants excepted and listed). Generating from two fixture run directories with different metrics yields different artifacts. A fixture with an undefined metric renders "not estimable", not a number.

**6. Acceptance.** Tests pass. Every row of the claims ledger resolves to an existing key whose value equals the number in the text. No sentence in the results document lacks a ledger row. No use of the words listed in rule 7 of section 0.

**7. Artifacts.** Results document, tables, figures, claims ledger.

**8. Rollback.** Revert the branch; delete generated artifacts.

**9. Must remain unchanged.** Formal metrics. All earlier reports (they stay as history; the master audit's section 8 says how to read them).

**10. Unblocks.** Writing the paper.

---

## Acceptance gates

A gate is passed by the evidence listed, checked by the researcher. File existence and a zero exit code are never sufficient.

| Gate | Passed when | Does not count |
|---|---|---|
| **A — Integrity** | External copy re-hashed equal to the evidence manifest. No assume-unchanged flags, no missing tracked files. Preservation branch clones to the manifest's hashes. Both frozen checkpoint hashes recomputed and equal. Environment lock file exists and the import check passes. | The recovery reports. A manifest that was written but not compared. |
| **B — Pipeline readiness** | Checkpoint inspection shows the expected keys and class names. The audio contract test passes against the real checkpoint. The three guard tests fail when they should. The run manifest of the smoke run echoes the effective parameters of every component and they equal the configuration. Design §6.2 timing assumptions are restated in the manifest. | A printed "parameters verified" line. Defaults that happen to equal the frozen values. |
| **C — Software correctness** | Phase 3, 7 and 8 tests pass with the legacy non-production tests excluded. The mutation record shows each named defect, when reintroduced, fails a gated test. Test report states collected, passed, failed, skipped. | A pass count that includes tests importing no production code. Tests asserting only that something ran. |
| **D — Full-dataset inference** | 108 stream-status rows. Each is `FULL` or has a recorded reason and a listed exclusion. Headers match media and checkpoint hashes. Resume is a no-op. | Presence of output files. Record counts without the expected count beside them. |
| **E — Result integrity** | Pre-approval metrics exist with numerator, evaluable count, total and exclusions for each. The evaluator fixture tests pass. `--formal` refuses to run without approved labels. The same trace under two names gives identical metrics. | Any metric computed from candidates. Any table produced by the legacy generators. |
| **F — Human annotation approval** | `APPROVAL_MANIFEST.json` created and signed by the researcher, listing 27 files whose hashes verify; each marker has a frame index and saved evidence frame; negatives carry the train-free statement; the validator passes; `[D-8]` outcome recorded. | The 27 existing review files. Any approval field written by software. |
| **G — Formal evaluation** | `EVALUATION_RECORD.json` ties results to run, commit, configuration, approval manifest and offsets; the policy freeze predates it; feasibility table, exclusions, sensitivity and session split are present; the evaluation log shows no undeclared re-run. | Results computed before the freeze or with a dirty tree. |
| **H — Publication readiness** | Claims ledger complete and verified; limitations present; no result literal in generator code; earlier reports referenced only as history. | Figures that look right. |

---

## Minimum viable path

Required, in order: **0 → 1 → 2 → 4 → 6** (raw inference complete) → **3 → 7** (E4, E5, E7 and their independent-camera forms, both clearance variants; no stress conditions) → **8 → 10 → 11**.

In parallel from the end of Phase 0: **9** (human review) and **5** (offsets). If offsets are not accepted for at least 20 of 23 train events, drop the fused conditions; nothing else changes.

This path answers RQ1, RQ2 and RQ5, and RQ4 in its minimal form (E7 vs E5).

## Optional, in order of value

1. Stress conditions E9–E10 (software verification section of the paper).
2. Secondary ablations E1, E2, E6, E8, and E3 if fused mode is active.
3. Second annotator on a subset (`[D-8]`) — small cost, sets `u` empirically.
4. A 30–60 minute negative recording and a few tripod-mounted passages with lead-in, lead-out and a sync clap (`[D-7]`, `[D-11]`).
5. Continuous integration running the gated suite on each push.
6. Large-file versioning for media and weights (for example Git LFS or DVC) once a storage location is chosen.
7. Regenerating vision label files from the tracked manifest (only if retraining is ever needed).

## Not to be done

- Retraining or re-thresholding either model for this study.
- Refactoring the demo, the annotation package or the vision training code.
- Removing legacy scripts, tests or results.
- Adding EMA smoothing, tracking, or new model classes.
