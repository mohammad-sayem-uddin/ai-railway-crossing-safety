# Reproducibility & Provenance Specification

**Baseline Git Commit:** `d1032756de80963130e1cbd3d2334cb32139b996` (`main`)  
**Completion Branch:** `exp/four-layer-completion`  
**Environment Snapshot:** [`BASELINE_SNAPSHOT.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/BASELINE_SNAPSHOT.json)  
**Experiment Manifest:** [`results/exploratory_v2/FILE_HASH_MANIFEST.sha256`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/FILE_HASH_MANIFEST.sha256) (`23` deterministic files)  
**Documentation Manifest:** [`docs/generated/final_research_v2/FILE_HASH_MANIFEST.sha256`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/FILE_HASH_MANIFEST.sha256)

---

## 1. Software & Hardware Environment

Recorded directly in [`BASELINE_SNAPSHOT.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/BASELINE_SNAPSHOT.json):

| Component | Exact Version / Status |
| --- | --- |
| **Platform** | `macOS-26.6.2-arm64-arm-64bit` |
| **Python** | `3.11.15` (`.venv/bin/python`) |
| **PyTorch** | `2.13.0` (`torch_mps_available: true`, `torch_cuda_available: false`) |
| **Ultralytics** | `8.4.121` |
| **PyAV (`av`)** | `18.1.0` |
| **OpenCV (`cv2`)** | `5.0.0` |
| **FFmpeg** | `ffmpeg version 8.1.1 Copyright (c) 2000-2026 the FFmpeg developers` |
| **NumPy / Matplotlib / PyYAML / Pytest** | `2.4.6` / `3.11.1` / `6.0.3` / `9.1.1` |

Note: Deterministic replays (`scripts/run_v2_experiments.py`) run cleanly on CPU (`total_runtime_s: 30.362 s` warm run, recorded in [`runtime_telemetry.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/analysis/runtime_telemetry.json)).

---

## 2. Preserved Model Checkpoints & Frozen Config Digests

All weights and frozen baseline configurations remained byte-identical vs baseline (`d1032756de80963130e1cbd3d2334cb32139b996`):

| Artifact Path | Size (Bytes) | Full SHA-256 Digest |
| --- | --- | --- |
| `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` | `24,493,159` | `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` |
| `experiments/vision/e1204e5c9790/checkpoints/weights/best.pt` | `24,480,807` | `b7afbe3724cdace199cdb1cc5b07b869b179182ac411859fdb984ece8943d6f0` |
| `experiments/vision/d9dfa4e34d02/checkpoints/weights/best.pt` | `24,480,807` | `20956cefe5c9a4b6683c6f11951da3fb3736ceef699839a5992249bde22d99d1a` |
| `experiments/audio/RUN_20261008_AUDIO_V2/checkpoints/best.pt` | `329,433` | `ddab244f1f2e18f7c8c4c2edc0a465215f8bd1f91d044b82b2a4d51553ec3053` |
| `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt` | `329,497` | `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782` |
| `configs/frozen_experiment_v1.yaml` | `1,898` | `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a` |
| `configs/decision_policy_v1.yaml` | `2,944` | `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575` |
| `configs/decision_policy_v2_candidate.yaml` | `9,862` | `d90828b2ec37169d663c72ab7de7d86600728c0db170ebef3934b9565abaf07f` |
| `data/manifests/camera_sync_offsets_candidate.yaml` | `43,211` | `aaac453b7047ff5302592203114bdc4fc13de1d149669ad4590f074fa4110dcc` |
| `data/governance/leg_exec_authorization.json` | `1,856` | `77933986b42b44d340723227c8319a4fb90687a9d6dbe00133de39780bd9cb7e` |

---

## 3. Core Implementation & Test Module Digests (`sha256[:16]`)

- `src/railway_detection/vision/video.py` (`1f37a8438fdcf16d`)
- `src/railway_detection/demo/video_demo.py` (`80bf1462f0477c21`)
- `src/railway_detection/audio/features.py` (`d056eed02cba5f51`)
- `src/railway_detection/fusion/evidence.py` (`83734ffc6b93b072`)
- `src/railway_detection/fusion/collector.py` (`8e284b2c8d31d1fd`)
- `src/railway_detection/fusion/rules.py` (`3e11bdb9644c1d0e`)
- `src/railway_detection/fusion/occupancy.py` (`92ccf3809442c49b`)
- `src/railway_detection/fusion/rules_v3_four_layer.py` (`bac7bd195fff7096`)
- `src/railway_detection/fusion/decision_engine_v3_four_layer.py` (`f024266775c85778`)
- `src/railway_detection/simulation/gate_model.py` (`b712d1c07030a43f`)
- `src/railway_detection/simulation/state_machine.py` (`d11b7509486247b0`)
- `src/railway_detection/simulation/runner.py` (`b3ddc5c71f42ef87`)
- `src/railway_detection/experiments/diagnostic_trace.py` (`7532878297e56dc7`)
- `scripts/run_v2_experiments.py` (`26ac708401186bcb`)
- `scripts/generate_v2_figures.py` (`14a2aedc38f07339`)
- `tests/unit/test_v3_four_layer_system.py` (`1f8980d572f83820`, `15` test functions / `20` parametrized test cases)

---

## 4. Exact Reproduction Commands & Verification

### A. Execute Full Experimental Programme (`Exp A` – `Exp N`)
```bash
PYTHONPATH=src:scripts .venv/bin/python scripts/run_v2_experiments.py
```
- Writes `23` deterministic artifacts to `results/exploratory_v2/` (plus non-hashed runtime stamp `analysis/runtime_telemetry.json`).
- **Two-run bit-identical verification:** Consecutive runs (`run1`, `run2`) verified `diff -u` empty across all `23` SHA-256 digests (`23/23 OK` via `shasum -a 256 -c results/exploratory_v2/FILE_HASH_MANIFEST.sha256`). Note `exp_n_event_matrix.csv` explicitly sets `csv.DictWriter(..., lineterminator="\n")` to guarantee POSIX `\n` byte parity across runs and platforms.

### B. Regenerate Publication Figures (`fig01` – `fig10`)
```bash
.venv/bin/python scripts/generate_v2_figures.py
```

### C. Verify Synthetic & Full Test Suites
```bash
# 1. V3 four-layer + orientation + causality suite
.venv/bin/python -m pytest tests/unit/test_v3_four_layer_system.py -v --import-mode=importlib

# 2. Check & enforce synthetic access boundary
.venv/bin/python scripts/classify_test_access.py --check
PYTHONPATH=src .venv/bin/python scripts/run_synthetic_tests.py --report-path /tmp/synthetic_runner_v3_report.json

# 3. Full repository regression triage
.venv/bin/python -m pytest tests/ -q --tb=line --import-mode=importlib
```

### D. Replay Trace Archives (`results/exploratory_v2/replays/`)
Full per-step deterministic simulation traces are preserved for independent inspection:
- `real_b4_v3_traces.json` (`27` events)
- `real_sync11_v3_traces.json` (`11` synced events)
- `real_sync11_policy_comparison_traces.json` (`V1`, `V2`, `V3_GUARDED`, `V3_CONSERVATIVE`)
- `synthetic_scenarios_traces.json` (controlled 4-layer & fault traces)
