# Phase 11.8 Unit 0 — Test Environment and Baseline Report

**Status:** Unit 0 complete with a documented source-gap blocker; Units 1–4 not started.  
**Date:** 2026-10-15  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (`main`)

## 1. Scope and authorization boundary

Unit 0 repaired the existing Python 3.11 virtual environment and re-established the Phase 11.7 test baseline. No application source, test, configuration, checkpoint, legacy review record, or `data/ground_truth/reviews/` file was modified. Environment changes were limited to `/Users/sayemuddin/Desktop/Train_automation/.venv/`. No Stage-2.1 record was created or promoted, and no git operation changed staging, commits, or branches.

The documented baseline is reproducible under its documented exclusions, but the full suite still cannot collect because `railway_detection.audio.training` is absent from the source tree. This report records that blocker; it does not implement the missing module.

## 2. Environment repair

The environment had systemic package-payload corruption rather than a pytest-only problem. Repairs used versions already recorded in `requirements.lock`; project dependencies were not upgraded:

- Repaired pytest (`9.1.1`), NumPy (`2.4.6`), Pillow (`12.3.0`), Matplotlib (`3.11.1`), PyParsing (`3.3.3`), Torch (`2.13.0`), TorchVision (`0.28.0`), OpenCV (`5.0.0.93`), Polars and its runtime (`2.0.0`), Python-Dateutil (`2.9.0.post0`), KiwiSolver (`1.5.1`), SymPy (`1.14.0`), FontTools (`4.66.1`), and mpmath (`1.3.0`).
- Removed one stale `pyparsing-3.3.2.dist-info` directory left by the interrupted repair; imported code and package metadata now both report `3.3.3`.
- No environment package was added to or removed from the project repository; `.venv/` is not tracked.

Final checks:

```text
pytest: OK (9.1.1)            numpy: OK (2.4.6)
PIL: OK (12.3.0)              matplotlib: OK (3.11.1)
torch: OK (2.13.0)            torchvision: OK (0.28.0)
cv2: OK (5.0.0)               polars: OK (2.0.0)
No broken requirements found.
```

`.venv/bin/python -m pip check` — **exit 0**.

## 3. Collection results

### 3.1 Full collection

```bash
.venv/bin/python -m pytest --collect-only -q
```

Result: **478 tests collected, 2 collection errors, exit 2**.

Both errors are the same source-tree gap:

```text
ERROR tests/unit/test_audio_leakage_and_preprocessing.py
E ModuleNotFoundError: No module named 'railway_detection.audio.training'
ERROR tests/unit/test_audio_training.py
E ModuleNotFoundError: No module named 'railway_detection.audio.training'
```

The earlier Torch, Matplotlib, OpenCV, and other environment-origin failures no longer occur. The missing module is not present under `src/railway_detection/audio/`; it is not an environment package and was not created in Unit 0.

### 3.2 Collection with the plan-documented exclusions

```bash
.venv/bin/python -m pytest tests/ \
  --ignore=tests/unit/test_audio_leakage_and_preprocessing.py \
  --ignore=tests/unit/test_audio_training.py \
  --collect-only -q
```

Result: **478 tests collected, exit 0** (one pre-existing `cgi` deprecation warning from `src/railway_detection/demo/server.py`).

Research-script collection also succeeds: **7 tests collected, exit 0** for `tests/unit/test_research_scripts.py`.

## 4. Test execution results

### 4.1 Focused Phase 11.7 governance suites

```bash
.venv/bin/python -m pytest \
  tests/test_phase11_7_governance_controls.py \
  tests/test_phase11_2_stage21_promotion_gate.py \
  tests/test_phase11_3_pending_decisions_not_defaulted.py -q
```

Result: **69 passed, exit 0**.

### 4.2 Full documented baseline command

```bash
.venv/bin/python -m pytest tests/ -q \
  --ignore=tests/unit/test_audio_leakage_and_preprocessing.py \
  --ignore=tests/unit/test_audio_training.py
```

Result: **475 passed, 3 failed, 1 warning in 11.50s; exit 1**.

The failures exactly match the Phase 11.7 pre-existing set:

1. `test_audio_v2_pipeline.py::test_v2_figures_and_report_artifacts` — missing `metrics/v1_vs_v2_comparison.json`.
2. `test_audio_v3_pipeline.py::test_v3_publication_figures_and_reports` — missing `reports/forensic_analysis.json`.
3. `test_real_dataset_inventory.py::test_audio_extension_anomaly_tracking` — missing the `43.mp3` companion path (the assertion stops at the first of the expected 43–46 paths).

No artifact or data file was manufactured to make these tests pass.

## 5. Protected-artifact and repository integrity

### 5.1 Legacy review records

- Review JSON count: **27** (`train_events`: 23, `no_train_events`: 3, `engine_events`: 1).
- Fresh sorted SHA-256 comparison against `/tmp/phase11_1_reviews_baseline_hashes.txt`: **no differences; exit 0; 27/27 byte-identical**.
- No Stage-2.1 record was created; the review directory remains unchanged.

### 5.2 Frozen configuration and checkpoints

`PYTHONPATH=src .venv/bin/python` loaded `configs/frozen_experiment_v1.yaml`, returned canonical hash `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`, and `verify_all_safeguards(Path('.'))` passed.

Fresh hashes:

| Artifact | SHA-256 |
|---|---|
| `configs/frozen_experiment_v1.yaml` | `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a` |
| `configs/decision_policy_v1.yaml` | `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575` |
| `configs/decision_policy_v2_candidate.yaml` | `d90828b2ec37169d663c72ab7de7d86600728c0db170ebef3934b9565abaf07f` |
| Vision checkpoint (`.../39f402dfe460/.../best.pt`) | `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` |
| Audio V3 checkpoint (`.../AUDIO_V3_ESC50/.../best.pt`) | `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782` |
| Prohibited Audio V2 checkpoint (`models/audio/best_checkpoint.pt`) | `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5` |

### 5.3 Git state

- HEAD remains `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` on `main`.
- Staged paths: **0**.
- Pre-existing tracked modified paths: **13**.
- No `.venv` path appears in git diff or status.
- The broad worktree contains pre-existing untracked research/data artifacts; this report does not claim those as Unit 0 outputs. The only project file added by this resumed Unit 0 work is this report.

## 6. Finding and stop condition

**Finding U0-1 — unresolved source/test gap:** the full suite cannot collect two audio-training test modules because `src/railway_detection/audio/training.py` is absent. Unit 0 does not infer whether that module was intentionally removed, lost during repository recovery, or requires a new implementation. Creating it would be a source change outside environment repair and could affect historical audio-training behavior; that decision is escalated rather than guessed.

The documented `475 passed / 3 failed` baseline is nevertheless re-established exactly under the plan’s two exclusions. Therefore:

- **Unit 0 acceptance:** met, with U0-1 documented.
- **Phase 11.8 continuation:** stopped before Units 1–4 pending researcher disposition/authorization for the absent audio-training module and review of this baseline report.
- **No later phase (11.9–16) was started.**

## 7. Reproduction commands

From `/Users/sayemuddin/Desktop/Train_automation`:

```bash
.venv/bin/python -m pip check
.venv/bin/python -m pytest --collect-only -q
.venv/bin/python -m pytest tests/ --ignore=tests/unit/test_audio_leakage_and_preprocessing.py --ignore=tests/unit/test_audio_training.py --collect-only -q
.venv/bin/python -m pytest tests/test_phase11_7_governance_controls.py tests/test_phase11_2_stage21_promotion_gate.py tests/test_phase11_3_pending_decisions_not_defaulted.py -q
.venv/bin/python -m pytest tests/ -q --ignore=tests/unit/test_audio_leakage_and_preprocessing.py --ignore=tests/unit/test_audio_training.py
```

The final command intentionally exits 1 because the three documented pre-existing failures remain.

## 8. Next action requiring researcher input

Review U0-1 and decide whether the absent `railway_detection.audio.training` module should be (a) restored/implemented under a separately authorized source task, or (b) formally excluded/dispositioned as a pre-existing gap. Until then, no review-session workflow implementation or real adjudication activity should begin.

