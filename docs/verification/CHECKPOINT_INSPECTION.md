# Direct Checkpoint Key & Metadata Inspection Record

**Date:** 2026-10-13  
**Auditor:** Senior ML Infrastructure Engineer  
**Method:** Direct safe CPU deserialization via `torch.load(..., map_location='cpu', weights_only=True)`.

---

## 1. Audio V3 Frozen Checkpoint

- **Path:** `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`
- **File Size:** `329,497` bytes
- **SHA-256:** `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`
- **Safe Load Result:** Successfully loaded with `weights_only=True`.

### Stored Metadata & Values

| Checkpoint Key | Type | Value | Verification Notes |
|---|---|---|---|
| `epoch` | `int` | `34` | Best training epoch |
| `val_loss` | `float` | `0.079420305788517` | Validation loss at epoch 34 |
| `val_f1` | `float` | `0.9942` | Validation F1 at epoch 34 |
| `norm_mean` | `float` | `-1.600999355316162` | **Present** (Audio V3 normalization mean) |
| `norm_std` | `float` | `5.1239728927612305` | **Present** (Audio V3 normalization std) |
| `operating_threshold` | `float` | `0.37` | **Present** (Calibrated threshold T*) |
| `model_state_dict` | `dict` | 30 tensors | `CompactTrainHornCNN` weights & batchnorm buffers |
| `optimizer_state_dict` | `dict` | 2 entries | Optimizer state |
| `feature_mean` | — | **ABSENT** | Key queried by uncorrected loader |
| `feature_std` | — | **ABSENT** | Key queried by uncorrected loader |

### Empirical Diagnosis of IMA-22
The trainer (`scripts/train_audio_model_v3_esc50.py:389-390`) explicitly serialized normalization parameters under the names `norm_mean` and `norm_std`. The inference wrapper (`PyTorchTrainHornClassifier._load_checkpoint`) queried `state.get("feature_mean", self.mean)` and `state.get("feature_std", self.std)`. Because neither existed, the loader silently used defaults `0.0` and `1.0`.

---

## 2. YOLO Vision Frozen Checkpoint

- **Path:** `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`
- **File Size:** `24,493,159` bytes
- **SHA-256:** `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`
- **Class Names (via Ultralytics backend):**
  ```python
  {0: 'front', 1: 'rear', 2: 'side'}
  ```
- **Verification:** Exact match with expected class map `{0: front, 1: rear, 2: side}`.

---

## 3. Prohibited Audio V2 Checkpoint (Audit Ground Truth)

- **Path:** `models/audio/best_checkpoint.pt`
- **File Size:** `111,703` bytes
- **SHA-256:** `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5`
- **Top-Level Keys:**
  - `epoch`: `17`
  - `feature_mean`: `-4.662394409905204`
  - `feature_std`: `23.724524500716207`
  - `operating_threshold`: `0.5183514356613159`
  - `val_loss`: `0.3733854694346708`
  - `val_f1`: `0.8602150537634408`
- **Significance:** Explains why the inference loader looked for `feature_mean` and `feature_std` — the loader was written for Audio V2 and never updated when V3 was introduced.
