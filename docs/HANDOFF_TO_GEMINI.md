# Handoff to Gemini 3.8 Flash High

| | |
|---|---|
| Date | 2026-10-13 |
| From | Claude Sonnet 5, Phase 0 (Git reconciliation, bounded scope) |
| Read first, in order | `docs/INDEPENDENT_MASTER_AUDIT.md` → `docs/EXPERIMENT_DESIGN_FINAL.md` → `docs/OPEN_DECISIONS_AND_BLOCKERS.md` → `docs/IMPLEMENTATION_PLAN_FOR_SONNET.md` → `docs/PHASE0_REPOSITORY_RECOVERY_REPORT.md` → this file |
| Findings reference | `docs/FINDINGS_REGISTER.csv`, IDs `IMA-nn` |

## 1. Actual current repository state

```
Path:   /Users/sayemuddin/Desktop/Train_automation
HEAD:   d4db94d4a4ea83ae4c510d65dfc99c5d6798304b  (branch main)
Status: 11 modified tracked files, 113 untracked paths, 0 staged, nothing committed
```

Git bookkeeping is now truthful: `git ls-files -v | grep '^h'` is empty, `git ls-files -d` is empty. The 68 previously-missing tracked files have been restored from `HEAD` (list: `reports/phase0_restored_files.txt`); the 73 assume-unchanged flags have been cleared (list: `reports/phase0_assume_unchanged_cleared.txt`). None of this touched checkpoints, media, candidate annotations, or results — verified by hash spot-check and by an untracked-file-set diff (both reported unchanged). Full detail: `docs/PHASE0_REPOSITORY_RECOVERY_REPORT.md`.

**Nothing is committed.** The working tree now matches what the researcher intends to keep, but Git still shows it as uncommitted changes against `d4db94d`. Whether and when to commit is the researcher's call (see `OPEN_DECISIONS_AND_BLOCKERS.md` D-1) — do not commit on your own initiative.

## 2. What is genuinely true right now (do not re-derive these)

- Both frozen checkpoints hash-match their recorded constants in `leakage_guard.py`: Vision `3f5bb5b2…fba18ebd`, Audio V3 `ea1bb81d…6c512782`. The prohibited Audio V2 checkpoint (`models/audio/best_checkpoint.pt`) also still matches its known prohibited hash `59b0785f…fcf7d5` and is **not** hard-blocked in code (IMA-25) — do not load it.
- `data/ground_truth/reviews/**` (27 files) are all marked `APPROVED` by a fabricated "human_researcher_lead" review that never happened (IMA-06, confirmed again by the user in this session: D-2 answered "no, I did not review these"). They are candidates only. **Never read these as approved ground truth, never write an approval field, never create an approval manifest.** This is a hard, standing rule — see the user's memory note referenced in `OPEN_DECISIONS_AND_BLOCKERS.md`.
- `src/railway_detection/data/sync.py` is a locally-rewritten, non-dataclass `SyncAligner` that the current `fusion/collector.py` depends on. It is **not** the version at `HEAD`. Diff saved at `reports/sync_py_local_vs_head.diff`. Leave it as-is; it is correct working code, just untracked-equivalent (now tracked-and-modified).
- The restored `pyproject.toml` is stale: it declares only `PyYAML>=6.0` and `Pillow>=10.0` as core dependencies, plus `pytest/ruff/mypy` (dev) and `numpy/matplotlib` (eval). **It does not declare `torch`, `ultralytics`, `opencv-python`, or `scipy`**, all of which the current `src/railway_detection` package (audio, vision, fusion modules) imports directly. This is a new, specific, confirmed gap — not previously quantified by the Opus audit, which only observed the old `.venv`'s installed versions (torch 2.13.0, ultralytics 8.4.121, numpy 2.4.6, opencv-python 5.0.0.93) without comparing them against `pyproject.toml`'s declared set.
- No Python environment on this machine currently imports `torch` successfully (IMA-03, unchanged — not touched this session). `python3 -c "import torch"` fails with `ModuleNotFoundError: No module named 'torch.torch_version'` in the existing broken `.venv`.
- No code, inference, training, or test suite was run in this session or the preceding audit. Every behavioral claim about the engine, metrics, or injector in the Opus audit is derived from reading source, not from execution.

## 3. Exact next task: `IMPLEMENTATION_PLAN_FOR_SONNET.md` Phase 1, with one addition

**Objective.** A reproducible interpreter that can import the package and the full ML stack, a recorded test baseline, and direct inspection of both checkpoints' stored keys — nothing else. (Resolves IMA-03; confirms or refutes IMA-22.)

**Preconditions already met:**
- Phase 0 (this session's scope) is done: Git state is truthful, `pyproject.toml` is present (if stale), all package `__init__.py` files and configs are present.
- `[D-1]` (backup location) — user states personal Google Drive verification is complete. Treat as satisfied for the purpose of proceeding; do not re-verify.

**What you must do, precisely, per the plan's Phase 1 (`docs/IMPLEMENTATION_PLAN_FOR_SONNET.md`):**

1. **Before installing anything**, reconcile `pyproject.toml`'s `dependencies` list against what the current `src/railway_detection` package actually imports (grep for `^import`/`^from` across `src/railway_detection/**/*.py`, excluding optional lazy imports already guarded by try/except where the surrounding code degrades gracefully — e.g. `audio/model.py`'s lazy `import torch` inside `CompactTrainHornCNN.__new__`). Add `torch`, `ultralytics`, `opencv-python` (imported as `cv2`), and `scipy` to `dependencies` (not just `eval`) if the audit and your own grep confirm they are required for the experiment path, not just for optional demo/dashboard code. **Do not silently delete or rewrite other declared dependencies.** Record what you changed and why in `docs/verification/ENVIRONMENT.md` (per the plan) — this is a deviation from "pyproject.toml only if a dependency used by the code is undeclared," which the plan explicitly permits.
2. Create a **new** virtual environment outside `.venv/` (which is broken) at a location you record — do not attempt to repair the existing `.venv/`.
3. Install the versions the audit found in the old environment's metadata — torch 2.13.0, ultralytics 8.4.121, numpy 2.4.6, opencv-python 5.0.0.93, matplotlib 3.11.1, pytest 9.1.1 — plus scipy and PyYAML at whatever versions pip resolves. Install the package itself in editable mode. Write the resolved set to `requirements.lock`.
4. Record Python, package, ffmpeg, OS versions in `docs/verification/ENVIRONMENT.md`.
5. **Read, without running inference**, the keys and values stored in both audio checkpoints (`experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt` and `models/audio/best_checkpoint.pt`) and the class-name mapping stored in the YOLO checkpoint (`experiments/vision/39f402dfe460/checkpoints/weights/best.pt`). Write results to `docs/verification/CHECKPOINT_INSPECTION.md`. **This is the single highest-value action remaining**: it directly confirms or refutes IMA-22 (P0 — audio normalisation key mismatch between trainer and inference wrapper), which the Opus audit could only establish from source code because no working torch existed. Expected, per the audit: Audio V3 checkpoint contains `norm_mean`, `norm_std`, `operating_threshold` (should be 0.37); YOLO checkpoint's class names should be `{0: front, 1: rear, 2: side}`. If any of these is false, **stop and report** — do not proceed to Phase 2 on an unconfirmed assumption.
6. Run the existing test suite once, **unmodified**. Record collected/passed/failed/skipped/error counts in `docs/verification/TEST_BASELINE_<commit>.txt`. Do not fix any failure in this phase — that is Phase 3's job (policy/sensor-health tests) and later phases.

**Acceptance for this phase (from the plan, unchanged):**
- One command imports `railway_detection`, `torch`, `ultralytics`, `cv2` successfully.
- `pytest --collect-only` reports zero collection errors, or each is listed with cause.
- `CHECKPOINT_INSPECTION.md` states whether all three expected keys are present with the expected values, and the YOLO class names match.
- Recomputed SHA-256 of both frozen checkpoints still equals the constants in `leakage_guard.py` (re-verify; do not trust the number from this handoff document).

**Do not, under any circumstance, in this phase:**
- Run inference, training, or calibration.
- Touch `data/ground_truth/`, `data/raw/`, any result file, or any checkpoint's bytes.
- Create, sign, or imply an approval of ground truth.
- Fix the audio normalisation bug (that's Phase 2) or the clearance-rule/liveness bug (Phase 3) — this phase only **confirms** IMA-22 by inspection; it does not fix anything.
- Commit or push without the researcher's explicit go-ahead.

## 4. Known open decisions that may block later phases (not this one)

From `docs/OPEN_DECISIONS_AND_BLOCKERS.md`: D-2 is now answered (user confirmed via this session's framing that the APPROVED reviews are not theirs — treat as invalid, per the standing memory rule). D-1 is effectively answered for backup purposes (user states Google Drive verification complete) but **not** for the separate question of whether/when to commit this reconciled state to Git — ask before committing. D-3 through D-11 remain open and do not block Phase 1.

## 5. If you find Phase 1's expectations are wrong

Stop and write findings to `docs/verification/CHECKPOINT_INSPECTION.md` or `docs/verification/ENVIRONMENT.md` as appropriate, then report to the researcher rather than improvising a fix. In particular: if the Audio V3 checkpoint does **not** contain `norm_mean`/`norm_std`, that is IMA-22 confirmed by direct evidence rather than by code inspection alone — upgrade its status from "confirmed (by source reading)" to "confirmed (by checkpoint inspection)" in your report, but do not attempt the Phase 2 fix in this pass unless explicitly asked.

---

## 6. Phase 1 Completion Status & Handoff to Next Phase (Phase 2)

**Completed by:** Senior ML Infrastructure Engineer (2026-10-13)  
**Detailed Report:** `docs/PHASE1_AUDIO_NORMALIZATION_AND_ENVIRONMENT_REPORT.md`

### Completed in Phase 1:
- Reconciled `pyproject.toml` with actual package dependencies (`numpy>=1.26`, `PyYAML>=6.0`, `Pillow>=10.0`, `torch>=2.0.0`, `torchvision>=0.15.0`, `ultralytics>=8.0.0`, `opencv-python>=4.8.0`).
- Established isolated, working virtual environment at `venv/` (Python 3.11.15).
- Verified joint import of `railway_detection`, `torch`, `ultralytics`, `cv2`, `scipy`, `numpy`, `yaml`, `PIL`.
- Pinned all dependencies into `requirements.lock`.
- Directly inspected Audio V3 checkpoint (`experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`) with `weights_only=True`:
  - `norm_mean = -1.600999355316162`
  - `norm_std = 5.1239728927612305`
  - `operating_threshold = 0.37`
  - `feature_mean` and `feature_std` confirmed absent.
- Directly inspected YOLO checkpoint class names: `{0: 'front', 1: 'rear', 2: 'side'}`.
- Traced training and inference pipelines, confirming the IMA-22 defect was caused by inference code querying `feature_mean`/`feature_std` rather than `norm_mean`/`norm_std`.
- Corrected `PyTorchTrainHornClassifier._load_checkpoint` in `src/railway_detection/audio/model.py`, eliminated silent fallback, and added parameter validation (`_validate_normalization_params`).
- Added and ran 6 targeted regression tests (`tests/unit/test_audio_normalization_regression.py`), all passing.
- Re-verified SHA-256 hashes of Audio V3, Vision YOLO, and prohibited Audio V2 checkpoints — unchanged.
- Preserved `src/railway_detection/data/sync.py` and uncommitted working tree.

### Phase 2: One Frozen Configuration; Pipeline Hardening
- Status: **COMPLETE** (2026-10-13)
- Canonical Hash: `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`
- Full Report: `docs/PHASE2_FROZEN_CONFIGURATION_REPORT.md`

---

## 7. Phase 2 Completion Status & Handoff to Next Phase (Phase 3)

**Completed by:** Senior ML Infrastructure Engineer (2026-10-13)  
**Detailed Report:** `docs/PHASE2_FROZEN_CONFIGURATION_REPORT.md`

### Completed in Phase 2:
1. **Established Single Authoritative Configuration:**
   - Created `configs/frozen_experiment_v1.yaml` specifying all parameters required for reproducible inference and simulation.
   - Canonical SHA-256 hash computed deterministically: `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`.
2. **Cryptographic Checkpoint Integrity & Hard Prohibition:**
   - Vision checkpoint (`experiments/vision/39f402dfe460/checkpoints/weights/best.pt`) verified: `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`.
   - Audio V3 checkpoint (`experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`) verified: `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`.
   - Prohibited Audio V2 (`models/audio/best_checkpoint.pt`) hard-blocked by path and hash (`59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5`). Raises `ProhibitedCheckpointError`.
3. **Execution Path Wiring:**
   - Wired `FrozenExperimentConfig` into `layer_b_processor.py`, `runner.py`, `decision_engine.py`, and `simulation/runner.py`.
   - Default `audio_threshold` in `MultimodalDecisionEngine` corrected from legacy `0.50` (IMA-23) to `0.3700`.
   - Unauthorized runtime threshold overrides rejected with `ValueError`.
4. **Camera Timing Safeguards (R04 Enforcement):**
   - Merging dual camera streams without an empirical `SyncAligner` raises `TimingIntegrityError` unless explicitly configured for exploratory evaluation.
5. **Traceable Condition Overrides:**
   - `create_condition_config()` supports explicit, traceable B0–B7 overrides while keeping base configuration immutable.
6. **Regression Tests:**
   - 18 focused regression tests in `tests/unit/test_frozen_config_safeguards.py` passing cleanly (35/35 passing across all associated suites).

### Next Phase: Phase 3 — Sensor Health, Staleness, and Decision Policy
Per `docs/IMPLEMENTATION_PLAN_FOR_SONNET.md` §Phase 3:
- **Objective:** Fix sensor health tracking (IMA-15: availability bit must distinguish healthy-no-train from sensor failure), clearance dwell policy (IMA-16: audio must delay clearance, not trigger opening), and premature opening prevention.
- **Key Modules:**
  - `src/railway_detection/fusion/decision_engine.py`
  - `src/railway_detection/fusion/source_tracker.py`
  - `src/railway_detection/fusion/rules.py`
- **Standing Invariants:**
  - Audio alone NEVER opens the gate.
  - Zero-offset camera fusion remains blocked until empirical calibration exists.
  - Reviews in `data/ground_truth/reviews/**` remain unapproved candidates; do not treat as ground truth.
- **Scope Restriction:**
  - Do not run full-dataset inference or benchmark B0–B7 runs until Phase 3 and Phase 4 acceptance criteria pass.

