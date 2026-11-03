# Phase 1: Python Environment Recovery & Audio V3 Normalization Verification Report

**Date:** 2026-10-13  
**Role:** Senior ML Infrastructure Engineer  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Reference Findings:** `docs/FINDINGS_REGISTER.csv` (IMA-03, IMA-22)

---

## 1. Executive Summary

Phase 1 has been successfully completed in full strict conformance with the independent audit requirements and safety protocols:
1. **Dependency Reconciliation & Isolated Environment:**
   - Evaluated actual source code imports across `src/railway_detection`, `scripts/`, and `tests/`.
   - Identified and added missing core runtime dependencies (`numpy`, `torch`, `torchvision`, `ultralytics`, `opencv-python`) to `pyproject.toml`.
   - Established a dedicated, isolated Python 3.11 environment (`venv/`) without touching or deleting `.venv/`.
   - All core ML and signal processing libraries (`torch 2.13.0`, `ultralytics 8.4.121`, `cv2 5.0.0`, `scipy 1.17.1`, `numpy 2.4.6`, `yaml 6.0.3`, `PIL 12.3.0`) verified jointly importing in a single process.
   - Pinned dependencies to `requirements.lock`.
2. **Empirical Audio V3 Checkpoint Key Inspection:**
   - Inspected frozen checkpoint `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt` directly via safe `weights_only=True` CPU deserialization.
   - **CONFIRMED IMA-22:** Checkpoint stores normalization statistics under `norm_mean` (`-1.600999355316162`) and `norm_std` (`5.1239728927612305`), with `operating_threshold` (`0.3700`). Keys `feature_mean` and `feature_std` are completely absent.
   - Identified root historical cause: Prohibited Audio V2 (`models/audio/best_checkpoint.pt`) used `feature_mean` and `feature_std`. When Audio V3 was trained, key names were changed to `norm_mean`/`norm_std`, but `PyTorchTrainHornClassifier` was never updated, causing silent fallback to unnormalized defaults (`mean=0.0, std=1.0`).
3. **Normalization Correction & Guard Hardening:**
   - Corrected `PyTorchTrainHornClassifier` in `src/railway_detection/audio/model.py` to read `norm_mean` and `norm_std`.
   - Completely eliminated silent fallback; missing normalization metadata now raises an immediate `ValueError`.
   - Added parameter validation preventing non-finite (`NaN`/`Inf`), non-positive (`std <= 1e-6`), or out-of-bounds threshold values.
4. **Focused Regression Tests:**
   - Implemented `tests/unit/test_audio_normalization_regression.py` covering all 6 required verification angles.
   - All 6 tests passed (100% pass rate).
5. **Asset Integrity:**
   - Both frozen checkpoints (`Audio V3` and `Vision YOLO`) re-hashed before and after the work; hashes remain strictly identical.

---

## 2. Environment Specification & Verified Versions

| Component | Verified Specification | Notes |
|---|---|---|
| **OS / Architecture** | macOS (Darwin 24.6.0) / Apple Silicon `arm64` | Apple Silicon MacBook Air |
| **Python Binary** | `/Users/sayemuddin/Desktop/Train_automation/venv/bin/python` | Version `3.11.15` |
| **FFmpeg** | `/opt/homebrew/bin/ffmpeg` | Version `8.1.1` |
| **PyTorch (`torch`)** | `2.13.0` | MPS acceleration available |
| **Torchvision** | `0.28.0` | |
| **Ultralytics** | `8.4.121` | YOLO backend |
| **OpenCV (`cv2`)** | `5.0.0.93` | Video decoding backend |
| **NumPy** | `2.4.6` | STFT / Mel spectrogram processing |
| **SciPy** | `1.17.1` | Eval dependency |
| **PyYAML** | `6.0.3` | Configuration parser |
| **Pillow (`PIL`)** | `12.3.0` | Image processing |
| **Matplotlib** | `3.11.1` | Figure generation |
| **Pytest** | `9.1.1` | Test framework |

Lock file generated: `requirements.lock`.

---

## 3. Direct Checkpoint Inspection Findings

### 3.1 Audio V3 Frozen Checkpoint
- **Path:** `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`
- **File Size:** `329,497` bytes
- **SHA-256:** `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`
- **Loading Mode:** PyTorch safe `weights_only=True` succeeded without warnings.
- **Top-Level Keys:**
  - `epoch`: `34` (`int`)
  - `model_state_dict`: `dict` with 30 tensor parameters/buffers
  - `optimizer_state_dict`: `dict` with 2 entries
  - `norm_mean`: `-1.600999355316162` (`float`)
  - `norm_std`: `5.1239728927612305` (`float`)
  - `val_loss`: `0.079420305788517` (`float`)
  - `val_f1`: `0.9942` (`float`)
  - `operating_threshold`: `0.37` (`float`)
- **Missing Keys:** `feature_mean` (`False`), `feature_std` (`False`).
- **Model Architecture:** Compact 3-layer CNN (Conv2D -> BN -> MaxPool -> Conv2D -> BN -> MaxPool -> Conv2D -> BN -> AdaptiveAvgPool -> Linear -> BN -> Dropout -> Linear). Total parameters: ~75,000. Input tensor shape: `(B, 1, 64, 61)`.

### 3.2 Vision Frozen Checkpoint
- **Path:** `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`
- **SHA-256:** `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`
- **Ultralytics Model Names:** `{0: 'front', 1: 'rear', 2: 'side'}` (exact match).

### 3.3 Prohibited Audio V2 Checkpoint (Audit Comparison)
- **Path:** `models/audio/best_checkpoint.pt`
- **SHA-256:** `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5`
- **Stored Keys:** `feature_mean: -4.662394409905204`, `feature_std: 23.724524500716207`, `operating_threshold: 0.5183514356613159`.
- **Verdict:** Confirmed prohibited. Do not load or use.

---

## 4. Pipeline Trace & Defect Correction

### 4.1 Training vs. Inference Parity Trace
- **Audio Preprocessing:**
  - Sample rate: `16,000` Hz.
  - Window size: `1.0` s (`16,000` samples).
  - Mel Filterbank: `64` bands, `f_min=80.0` Hz, `f_max=8000.0` Hz, `n_fft=512`, `hop_length=256`.
  - Output spectrogram dimension: `(64, 61)`.
  - Both training and inference code call `compute_log_mel_spectrogram` with identical parameters.
- **Normalization Formula:**
  - Training: `(X_train_raw - norm_mean) / norm_std`.
  - Inference: `(log_mel - self.mean) / self.std`.
- **Defect Mechanism:**
  - Prior inference code queried `state.get("feature_mean", self.mean)` and `state.get("feature_std", self.std)`.
  - In Audio V3, those keys did not exist; thus `self.mean` fell back to `0.0` and `self.std` to `1.0`.
  - Because inputs were unnormalized, activations inside the CNN were severely attenuated/shifted, causing almost zero horn detections on natural recordings.

### 4.2 Code Changes Implemented
In `src/railway_detection/audio/model.py`:
- `PyTorchTrainHornClassifier._load_checkpoint`:
  - Retrieves `norm_mean` (Audio V3 primary) or `feature_mean` (legacy).
  - Retrieves `norm_std` (Audio V3 primary) or `feature_std` (legacy).
  - Raises `ValueError` if neither is present (silent fallback eliminated).
- `PyTorchTrainHornClassifier._validate_normalization_params`:
  - Enforces `math.isfinite(mean)` and `math.isfinite(std)`.
  - Enforces `std > 1e-6`.
  - Enforces `math.isfinite(threshold)` and `0.0 <= threshold <= 1.0`.

---

## 5. Regression Test Results

Execution command: `venv/bin/pytest tests/unit/test_audio_normalization_regression.py -v`

| Test Case | Objective | Result |
|---|---|---|
| `test_actual_checkpoint_normalization_metadata` | Asserts mean (`-1.6010`), std (`5.1240`), and threshold (`0.37`) loaded from real checkpoint | **PASSED** |
| `test_agreement_between_training_and_inference_normalization` | Verifies inference normalizer numerically matches training formula | **PASSED** |
| `test_clear_failure_on_missing_required_normalization_values` | Asserts clear `ValueError` on missing mean/std, zero std, NaN mean, invalid threshold | **PASSED** |
| `test_stable_expected_feature_shape_and_preprocessing_config` | Verifies `(64, 61)` Mel spectrogram tensor dimensions | **PASSED** |
| `test_checkpoint_remains_unmodified_by_loading_and_inspection` | Verifies SHA-256 byte invariant before and after loading/prediction | **PASSED** |
| `test_regression_protection_norm_mean_vs_feature_mean` | Verifies precedence of `norm_mean` and robustness against naming variations | **PASSED** |

**Summary:** 6 passed in 4.24s.

---

## 6. Asset Checkpoint SHA-256 Invariants

| Asset Path | Expected SHA-256 | Verified Before | Verified After | Status |
|---|---|---|---|---|
| `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt` | `ea1bb81d...6c512782` | `ea1bb81d...6c512782` | `ea1bb81d...6c512782` | **MATCH** |
| `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` | `3f5bb5b2...fba18ebd` | `3f5bb5b2...fba18ebd` | `3f5bb5b2...fba18ebd` | **MATCH** |
| `models/audio/best_checkpoint.pt` (prohibited) | `59b0785f...ffcf7d5` | `59b0785f...ffcf7d5` | `59b0785f...ffcf7d5` | **MATCH** |

---

## 7. Unresolved Blockers and Next Steps

1. **Test Collection Anomalies:**
   - Running `pytest --collect-only` identifies 2 errors in untracked files (`tests/unit/test_audio_leakage_and_preprocessing.py`, `tests/unit/test_audio_training.py`) attempting to import `railway_detection.audio.training`. This module does not exist because training logic was historically kept in `scripts/train_audio_model_v3_esc50.py`. This should be addressed in subsequent refactoring phases.
2. **Next Task:**
   - Proceed to **Phase 2** (Hashed Frozen Configuration & Audio Pipeline Hardening) per `docs/IMPLEMENTATION_PLAN_FOR_SONNET.md`.
