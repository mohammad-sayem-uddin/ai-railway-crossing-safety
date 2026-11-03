# Environment Verification Record

**Date:** 2026-10-13  
**Host Architecture:** Darwin 24.6.0 (macOS) / Apple Silicon `arm64` (MacBook Air)  
**Virtual Environment Path:** `/Users/sayemuddin/Desktop/Train_automation/venv`  
**Python Version:** `Python 3.11.15` (Homebrew Cellar `/opt/homebrew/Cellar/python@3.11/3.11.15_1`)  
**FFmpeg Version:** `ffmpeg version 8.1.1` (`/opt/homebrew/bin/ffmpeg`)  
**Resolution Artifact:** `requirements.lock`

## 1. Verified Core Packages & Joint Import Status

The following joint import test passes in a single process:

```python
import railway_detection
import torch
import ultralytics
import cv2
import scipy
import yaml
import PIL
import numpy
```

| Package | Resolved Version | Role |
|---|---|---|
| `railway-detection` | `0.1.0` (editable) | Core research framework |
| `torch` | `2.13.0` | Audio CNN inference & MPS acceleration |
| `torchvision` | `0.28.0` | Vision transformations |
| `ultralytics` | `8.4.121` | YOLOv8/v11 vision detector |
| `opencv-python` | `5.0.0.93` | Video decoding & frame extraction |
| `numpy` | `2.4.6` | STFT, filterbanks, numerical tensors |
| `scipy` | `1.17.1` | Scientific processing (eval) |
| `PyYAML` | `6.0.3` | Configuration loader |
| `Pillow` | `12.3.0` | Image handling |
| `matplotlib` | `3.11.1` | Visualizations & figures |
| `pytest` | `9.1.1` | Test runner |

## 2. Dependency Reconciliation Rationale

- In the restored `pyproject.toml`, only `PyYAML` and `Pillow` were declared as dependencies, with `numpy` and `matplotlib` under `eval`.
- However, `railway_detection.audio` and `railway_detection.vision` directly import `torch`, `ultralytics`, `cv2`, and `numpy` during primary operations.
- `scipy` was audited due to a docstring mention in `audio/features.py`, but AST analysis verified it is not imported anywhere in python code. It was placed under `optional-dependencies.eval`.
- The broken `.venv` (lacking `torch_version.py` due to prior corruption) was left completely untouched. A dedicated isolated environment was established at `venv/` using Python 3.11.
