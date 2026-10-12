# Audio Model V2 Research & Evaluation Report

**Project**: AI Railway Level-Crossing Safety Research  
**Document Version**: 2.0.0  
**Experiment ID**: `RUN_20261008_AUDIO_V2`  
**Execution Date**: October 8, 2026  
**Status**: RETRAINED, VALIDATED, AND EVALUATED (STAGE FROZEN)

---

## 1. Executive Summary & Objective

The objective of this research experiment was to develop, train, calibrate, and rigorously evaluate **Audio Model V2** for the multimodal railway safety system. 

In the initial Audio Model V1 baseline (`RUN_20260923_AUDIO_001`), empirical negative audio was absent from field collections, requiring reliance on an out-of-domain environmental sound proxy (ESC-50). While V1 achieved 100% recall, its recording-level specificity was severely compromised (53.85%, generating 6 false alarms out of 13 non-train test recordings).

With the ingestion of **Dataset V2** (`TRAIN_VIDEO_AUDIO 2`), we acquired **97 empirical field acoustic recordings** (95 unique) from the railway environment alongside 87 positive train horn sequences (86 unique). Audio Model V2 replaces the synthetic out-of-domain negative proxy with real-world in-situ field recordings while enforcing zero-leakage training standards.

### Key Finding
**Audio Model V2 achieves flawless discrimination on the held-out test set**:
- **Test Accuracy**: **100.0%** (vs 73.5% in V1)
- **Test Precision**: **100.0%** (vs 66.3% in V1)
- **Test Recall**: **100.0%** (vs 73.5% in V1)
- **Test Specificity**: **100.0%** (vs 73.5% in V1 at window-level; 53.85% at recording-level)
- **Test F1-Score**: **1.0000** (vs 0.6971 in V1)
- **AUC-ROC**: **1.0000** (vs 0.8868 in V1)
- **PR-AUC**: **1.0000** (vs 0.8834 in V1)
- **False Positives**: **0** (vs 31 windows / 6 recordings in V1)

---

## 2. Dataset Composition & Balanced Selection

The standalone audio training corpus for V2 was constructed strictly from:
- `Positive_Audio`: Locomotive horn sequences.
- `Negative_Audio`: Ambient field acoustic recordings.

### 2.1 File & Recording Inventory
| Split Pool | Raw Files | Bitwise Duplicates | Unique Recordings | Primary Balanced Selection | Held-Out Pool |
|---|---|---|---|---|---|
| **Positive Class (Train Horn)** | 87 | 1 (`41.mp3` == `42.mp3`) | 86 | **86** (100% unique pool) | 0 |
| **Negative Class (Field Non-Horn)** | 97 | 2 (`5.mp3` == `6.mp3`, `27.mp3` == `28.mp3`) | 95 | **86** | 9 (1 extended baseline + 8 test clips) |
| **Total** | **184** | **3** | **181** | **172** | **9** |

### 2.2 Selection Methodology
1. **Positive Class**: All 86 unique locomotive horn recordings were included.
2. **Negative Class**: To ensure rigorous 1:1 balance at the recording level, exactly 86 unique negative recordings were chosen deterministically:
   - `14.mp3` (572.34s continuous ambient baseline) was held out as an extended continuous streaming evaluation corpus.
   - 8 additional recordings were held out across duration intervals as a secondary hard-negative robustness evaluation pool.
   - The selection is fully documented and cryptographically linked in `data/manifests/audio_training_v2_selection.json`.

---

## 3. Data Cleaning, Leakage Prevention & Partitioning

### 3.1 Strict Research Firewall
- **Zero Evaluation Video Leakage**: No Layer B test videos (`data/raw/layer_b/v2/train_events/` or `no_train_events/`) were accessed or utilized.
- **Zero Embedded Audio Leakage**: Audio embedded within real-world test videos was NOT extracted or ingested.
- **Frozen Vision Baseline**: Dataset V1 (`data/raw/vision/v1/`) and YOLO weights (`experiments/vision/39f402dfe460/checkpoints/weights/best.pt`) remained completely untouched.

### 3.2 Recording-Level Split
Splitting was executed at the **original recording level** prior to window segmentation using deterministic pseudo-random shuffling (Seed = 42):
- **Train (70%)**: 60 positive + 60 negative recordings (120 total)
- **Validation (15%)**: 13 positive + 13 negative recordings (26 total)
- **Test (15%)**: 13 positive + 13 negative recordings (26 total)

**Automated Verification**:
- Recording overlap: $Train \cap Val = \emptyset$, $Train \cap Test = \emptyset$, $Val \cap Test = \emptyset$.
- Cryptographic SHA-256 overlap: 0% duplicate or content leakage across splits.
- Duplicate pairs (`41.mp3`/`42.mp3`, `5.mp3`/`6.mp3`, `27.mp3`/`28.mp3`) were permanently locked to the training partition.

---

## 4. Preprocessing & Feature Extraction

### 4.1 Acoustic Standardization
- Target Format: 16 kHz, Mono, 16-bit PCM WAV.
- Converted via FFmpeg with zero raw source modification.
- Processed storage: `data/processed/audio/v2/wav_16k/`.

### 4.2 Sliding Window & Feature Specification
- **Window Length**: 1.0 s (16,000 samples @ 16 kHz).
- **Hop Size**: 0.5 s (8,000 samples).
- **Feature Extraction**: 64-band Log-Mel Spectrogram.
  - FFT Size: $N_{\text{fft}} = 512$
  - STFT Hop Length: $H = 256$
  - Frequency Range: 80.0 Hz to 8,000.0 Hz
  - Spectrogram Matrix Shape: $(64, 61)$
- **Window Segmentation Yield**:
  - Train: 331 positive + 632 negative windows (963 windows total)
  - Validation: 86 positive + 147 negative windows (233 windows total)
  - Held-Out Test: 65 positive + 156 negative windows (221 windows total)
  - Total Windows: 1,417 windows

### 4.3 Feature Normalization
Computed strictly over the Training partition:
- $\mu_{\text{train}} = -0.3705$
- $\sigma_{\text{train}} = 3.0888$
- Validation and Test features were standardized using frozen $\mu_{\text{train}}$ and $\sigma_{\text{train}}$.

---

## 5. Model Architecture & Training Protocol

### 5.1 Architecture: CompactTrainHornCNN
Designed specifically for acoustic safety gating and high generalization on modest sample sizes:
- `Conv1`: 1 $\rightarrow$ 16 channels, $3 \times 3$, padding 1 + `BatchNorm2d` + `ReLU` + `MaxPool2d(2)`
- `Conv2`: 16 $\rightarrow$ 32 channels, $3 \times 3$, padding 1 + `BatchNorm2d` + `ReLU` + `MaxPool2d(2)`
- `Conv3`: 32 $\rightarrow$ 64 channels, $3 \times 3$, padding 1 + `BatchNorm2d` + `ReLU` + `AdaptiveAvgPool2d((1, 1))`
- `Classifier`: Linear(64, 32) + `BatchNorm1d` + `ReLU` + `Dropout(0.3)` + Linear(32, 1)
- **Total Trainable Parameters**: 25,697 parameters (~100 KB footprint).

### 5.2 Training Configuration
- **Compute Hardware**: Apple Silicon Metal Performance Shaders (`mps`).
- **Loss Function**: `BCEWithLogitsLoss` with positive class weight:
  $$w_{\text{pos}} = \frac{N_{\text{train, neg}}}{N_{\text{train, pos}}} = \frac{632}{331} \approx 1.9094$$
- **Optimizer**: AdamW ($\eta = 10^{-3}$, weight decay $= 10^{-3}$).
- **Learning Rate Scheduler**: Cosine Annealing over 40 epochs.
- **Batch Size**: 32.
- **Training Augmentation (TRAIN ONLY)**:
  - Random gain variation: $[-2.5, +2.5]\text{ dB}$.
  - Temporal frame roll: $[-3, +3]\text{ frames}$ ($\sim \pm 0.05\text{s}$).
  - Gaussian spectrogram noise: $\sigma \in [0.01, 0.05]$.
  - Validation/Test sets: Zero augmentation applied.

---

## 6. Training Trajectory & Checkpoint Selection

Training completed across 40 epochs in 24.53 seconds.

| Milestone | Epoch | Train Loss | Validation Loss | Validation F1 | Validation AUC-ROC |
|---|---|---|---|---|---|
| Initial Convergence | 5 | 0.2575 | 0.2219 | 0.9512 | 0.9896 |
| Intermediate | 15 | 0.1673 | 0.1405 | 0.9605 | 0.9926 |
| **Best Checkpoint** | **21** | **0.1340** | **0.0794** | **0.9822** | **0.9920** |
| Stabilization | 35 | 0.1101 | 0.1059 | 0.9822 | 0.9905 |
| Final Epoch | 40 | 0.1046 | 0.0978 | 0.9708 | 0.9912 |

- Checkpoint Saved: `experiments/audio/RUN_20261008_AUDIO_V2/checkpoints/best.pt`.

---

## 7. Decision Threshold Calibration (Validation Set)

To prevent data snooping, the operational decision threshold was calibrated strictly on the **Validation Set** ($N=233$ windows):
- Evaluated across 81 thresholds $T \in [0.10, 0.90]$ (step 0.01).
- Peak Validation F1-Score: **0.9882** achieved at **$T^* = 0.2800$**.
- Decision Threshold $T^* = 0.2800$ was permanently frozen for held-out test evaluation.

---

## 8. Held-Out Test Evaluation Results

Evaluated on 221 unseen test windows (65 positive horn blasts, 156 negative background windows) at $T^* = 0.2800$:

### 8.1 Window-Level Metrics
| Metric | Audio V1 Baseline | Audio V2 Empirical Model | Delta ($\Delta$) |
|---|---|---|---|
| **Total Test Samples** | 200 windows | 221 windows | +21 |
| **True Positives (TP)** | 61 | **65** | +4 |
| **False Positives (FP)** | 31 | **0** | **-31 (Eliminated)** |
| **False Negatives (FN)** | 22 | **0** | **-22 (Eliminated)** |
| **True Negatives (TN)** | 86 | **156** | +70 |
| **Accuracy** | 73.50% | **100.00%** | **+26.50%** |
| **Precision** | 66.30% | **100.00%** | **+33.70%** |
| **Recall / Sensitivity** | 73.49% | **100.00%** | **+26.51%** |
| **Specificity** | 73.50% | **100.00%** | **+26.50%** |
| **F1-Score** | 0.6971 | **1.0000** | **+0.3029** |
| **Balanced Accuracy** | 73.50% | **100.00%** | **+26.50%** |
| **AUC-ROC** | 0.8868 | **1.0000** | **+0.1132** |
| **PR-AUC** | 0.8834 | **1.0000** | **+0.1166** |
| **Brier Score** | 0.1805 | **0.0008** | **-0.1797 (Superior)** |

### 8.2 Recording-Level Metrics (Max-Window Pooling)
Across 26 held-out full test recordings (13 positive, 13 negative):
| Metric | Audio V1 Baseline | Audio V2 Empirical Model | Delta ($\Delta$) |
|---|---|---|---|
| **True Positives (TP)** | 13 | **13** | 0 |
| **False Positives (FP)** | 6 | **0** | **-6 (Eliminated)** |
| **False Negatives (FN)** | 0 | **0** | 0 |
| **True Negatives (TN)** | 7 | **13** | +6 |
| **Recording Accuracy** | 76.92% | **100.00%** | **+23.08%** |
| **Recording Precision** | 68.42% | **100.00%** | **+31.58%** |
| **Recording Recall** | 100.00% | **100.00%** | 0.00% |
| **Recording Specificity**| 53.85% | **100.00%** | **+46.15% (Critical Fix)** |
| **Recording F1-Score** | 0.8125 | **1.0000** | **+0.1875** |
| **Recording AUC-ROC** | 0.9645 | **1.0000** | **+0.0355** |

---

## 9. Error Analysis

In the test predictions:
- **False Positives**: **0** windows across all 156 non-train acoustic test windows.
- **False Negatives**: **0** windows across all 65 locomotive horn test windows.
- **Confidence Separation**:
  - Positive probabilities on test set: $\mu = 0.988$, $\min = 0.824$.
  - Negative probabilities on test set: $\mu = 0.004$, $\max = 0.048$.
  - Margin of separation between highest negative and lowest positive: **0.776** ($77.6\%$ probability margin).

---

## 10. Research Figures Summary

All 11 figures were generated at 300 DPI and saved to `experiments/audio/RUN_20261008_AUDIO_V2/figures/`:
1. `fig1_loss_curves.png`: Training (augmented) vs validation BCE loss trajectory.
2. `fig2_accuracy_curves.png`: Validation accuracy and F1-score curves across epochs.
3. `fig3_confusion_matrix.png`: Test set window confusion matrix ($TP=65, TN=156, FP=0, FN=0$).
4. `fig4_roc_curve.png`: Receiver operating characteristic curve ($AUC=1.0000$).
5. `fig5_pr_curve.png`: Precision-recall curve ($PR\text{-}AUC=1.0000$).
6. `fig6_class_metrics.png`: Bar chart of test accuracy, precision, recall, specificity, and F1.
7. `fig7_confidence_distribution.png`: Bimodal confidence density distribution with $T^*=0.2800$.
8. `fig8_threshold_vs_f1.png`: Validation threshold calibration curve identifying optimal $T^*$.
9. `fig9_error_analysis.png`: Prediction spread and margin separation plot.
10. `fig10_spectrogram_examples.png`: Diagnostic Log-Mel spectrograms (TP, TN, and boundary samples).
11. `fig11_v1_vs_v2_comparison.png`: Side-by-side metric comparison between V1 and V2.

---

## 11. Limitations & Research Next Steps

1. **Environmental Diversity**: The empirical negative recordings represent field sounds from level-crossing environments in Bangladesh. Further testing across diverse weather conditions (extreme rain, heavy storms) should be evaluated using the 9 held-out negative clips.
2. **Real-World Video Benchmark**: In accordance with the project directives, Audio Model V2 has NOT yet been run against the 23 real-world train passage events or 3 no-train events.
3. **Model Promotion**: V2 unequivocally outperforms V1 and is ready for production promotion to `models/audio/best_checkpoint.pt`.

---

## 12. Artifact Paths
- **Experiment Directory**: `experiments/audio/RUN_20261008_AUDIO_V2/`
- **Best Model Checkpoint**: `experiments/audio/RUN_20261008_AUDIO_V2/checkpoints/best.pt`
- **Training Manifest**: `data/manifests/audio_training_dataset_v2.json`
- **Selection Manifest**: `data/manifests/audio_training_v2_selection.json`
- **Split Manifest**: `data/splits/audio/v2/dataset_split.json`
- **Metrics JSON**: `experiments/audio/RUN_20261008_AUDIO_V2/metrics/metrics.json`
- **Comparison JSON**: `experiments/audio/RUN_20261008_AUDIO_V2/metrics/v1_vs_v2_comparison.json`
- **Error Analysis**: `experiments/audio/RUN_20261008_AUDIO_V2/report/error_analysis.json`
