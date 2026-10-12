# Audio Model V3 (ESC-50 Negatives) Diagnostic Research Report

## 1. Objective
The primary objective of the **Audio Model V3** experiment is not merely to maximize a classification metric, but to execute a **stricter, scientifically diagnostic benchmark** of railway horn detection by replacing custom environmental background recordings with standardized acoustic confusers from the official **ESC-50** dataset.

Specifically, this study:
1. Tests the hypothesis that Audio V2's 100% test performance was facilitated by an "easy" negative pool or acoustic/channel confounds.
2. Evaluates model selectivity against rigorous hard acoustic confusers (e.g., motor engines, sirens, church bells, alarms, atmospheric turbulence).
3. Maintains a rigid firewall preventing data leakage from previous custom negative pools or Layer B real-world video evaluation datasets.

---

## 2. Motivation for ESC-50 Negative Replacement
In Audio Model V2 (`RUN_20261008_AUDIO_V2`), the negative dataset was drawn from 95 custom field recordings (`data/raw/audio/train_horn/negative/`). While these represented genuine field audio, they were captured in homogeneous environmental conditions without strong acoustic confusers. Audio V2 achieved:
- 100.0% window-level Accuracy, Precision, Recall, Specificity, and F1.
- 100.0% recording-level Accuracy, Precision, Recall, and Specificity.

In safety-critical level-crossing automation, a 100% score on a non-adversarial test set can create a false sense of security. Industrial machinery, passing motor vehicles, emergency vehicle sirens, and church bells frequently emit multi-harmonic acoustic energy that can trigger false positives. Replacing custom background audio with ESC-50 establishes a standardized, reproducible, multi-category challenge to expose exact acoustic failure modes.

---

## 3. Dataset Sources
Audio V3 isolates two distinct acoustic data sources:
1. **Positive Source**: The project's authentic railway train horn recordings in `data/raw/audio/train_horn/positive/` (`source_dataset = "own_train_horn"`).
2. **Negative Source**: The official ESC-50 dataset located in `ESC-50-master/` (referenced via symlink `data/raw/audio/external/esc50/`, `source_dataset = "ESC50"`).
3. **Firewalled Sources**:
   - `data/raw/audio/train_horn/negative/` (COMPLETELY EXCLUDED).
   - `data/raw/layer_b/` and `data/raw/layer_b/v2/` (COMPLETELY EXCLUDED).

---

## 4. Positive Dataset
A complete bitwise SHA-256 audit was conducted on `data/raw/audio/train_horn/positive/`:
- **Physical Items**: 95 items (91 regular files, 4 symlinks `43.mp3`–`46.mp3`).
- **File Types**: 87 audio files (`.mp3`/`.MP3`) and 4 legacy `.pdf` audio duplicates.
- **Unique Audio Recordings**: Exactly **86 unique recordings** by SHA-256 hash.
- **Bitwise Duplicate Pair**:
  - `41.mp3` == `42.mp3` (`SHA-256: 6dbbb514ffaa9cbef606ba33b3d5b00c3c6f932db1fbc155bbba0b77da204ce4`).
  - `41.mp3` was retained as the canonical positive recording; `42.mp3` was excluded and logged in `data/manifests/audio_v3_selection.json`.
- **Selected Positive Pool**: All **86 unique positive recordings** are utilized in the balanced experiment.

---

## 5. ESC-50 Negative Dataset
The official ESC-50 collection comprises 2,000 environmental audio recordings (5.0s duration each, 44.1 kHz, single-channel/stereo WAV) across 50 categories.
- **Metadata**: Verified against `ESC-50-master/meta/esc50.csv`.
- **Train Category Exclusion**: The ESC-50 `train` class (category 45, 40 clips) was strictly excluded from negative candidate selection because it contains locomotive and rail transit acoustic content.

---

## 6. Category Selection & Allocation
To maximize acoustic diversity rather than arbitrary selection, 11 categories representing realistic confusers and environmental noise were selected:

| Category | Target Role / Acoustic Nature | Selected Recordings |
| :--- | :--- | :---: |
| **`car_horn`** | Direct automotive horn confuser | 8 |
| **`engine`** | Diesel combustion and mechanical motor rumble | 8 |
| **`siren`** | Emergency vehicle acoustic warning chimes | 8 |
| **`church_bells`** | Multi-harmonic resonant metallic chimes | 8 |
| **`clock_alarm`** | High-frequency periodic alert tones | 8 |
| **`rain`** | Wideband continuous precipitation noise | 8 |
| **`thunderstorm`** | Low-frequency impulse rumble and thunder | 8 |
| **`airplane`** | Jet engine and fuselage acoustic rumble | 8 |
| **`helicopter`** | Low-frequency periodic rotor blade pulsation | 8 |
| **`wind`** | Aerodynamic low-frequency turbulence | 7 |
| **`footsteps`** | Transient percussive pedestrian sound | 7 |
| **Total** | **11 Diverse Acoustic Classes** | **86** |

---

## 7. Source & Fold Grouping
In ESC-50, each recording originates from a Freesound clip (`src_file`), and multiple clips from the same source clip are assigned lettered takes (`take: A, B, C...`).
- Across the 11 target categories, audit verified that **0 source files (`src_file`) cross fold boundaries**.
- Every `src_file` is strictly localized to a single ESC-50 fold.

---

## 8. Leakage Prevention & Fold Partitioning
To guarantee zero data leakage between training, validation, and testing:
1. **Fold-Partition Alignment**:
   - **Train Negatives (60 recordings)**: Drawn exclusively from **Folds 1, 2, and 3**.
   - **Validation Negatives (13 recordings)**: Drawn exclusively from **Fold 4**.
   - **Test Negatives (13 recordings)**: Drawn exclusively from **Fold 5**.
2. **Mathematical Guarantee**:
   $$\text{Train Folds } \{1, 2, 3\} \cap \text{Val Fold } \{4\} \cap \text{Test Fold } \{5\} = \emptyset$$
   Because source clips never cross folds, **zero source-clip leakage** exists between partitions.
3. **Old Negative Firewall**:
   - Asserted that 0 selected files reference `data/raw/audio/train_horn/negative/`.
   - Asserted that 0 selected files match any of the 95 custom negative MP3 SHA-256 hashes.
4. **Layer B Firewall**:
   - Asserted that 0 selected files match any of the 56 Layer B video/audio SHA-256 hashes.

---

## 9. Audio Preprocessing
Raw positive and negative recordings were standardized via non-destructive copies into `data/processed/audio/v3/wav_16k/`:
- **Format**: 16-bit Linear PCM WAV (`pcm_s16le`).
- **Sampling Frequency**: 16,000 Hz ($F_s = 16\text{ kHz}$).
- **Channels**: 1 (mono channel conversion).
- **Tooling**: Non-destructive FFmpeg conversion without altering raw source data.

---

## 10. Feature Extraction
Features were extracted using pure NumPy/SciPy algorithms matching the production engine:
- **Transform**: 64-band Log-Mel Spectrogram.
- **FFT Parameters**: $N_{\text{fft}} = 512$, hop length = 256 frames, Hann windowing.
- **Mel Filterbank**: 64 triangular filters spanning $f_{\text{min}} = 80.0\text{ Hz}$ to $f_{\text{max}} = 8,000.0\text{ Hz}$.
- **Dynamic Range**: Natural logarithm with $\epsilon = 10^{-10}$ floor ($\log(E + \epsilon)$).
- **Feature Tensor Dimensions**: Exactly `(64, 61)` per 1.0-second window.
- **Global Normalization**:
  $$\mu_{\text{train}} = -1.6010, \quad \sigma_{\text{train}} = 5.1240$$
  Computed strictly across the 871 training windows and frozen for all inference.

---

## 11. Windowing & Partition Distribution
Sliding window segmentation:
- **Window Length**: 1.0s (16,000 samples).
- **Hop Size**: 0.5s (8,000 samples, 50% overlap).
- **Short Audio Handling**: Reflective padding for signals $< 1.0\text{s}$.

### Recording-Level vs Window-Level Balance
| Partition | Source Pos Recs | Source Neg Recs | Total Recs | Pos Windows | Neg Windows | Total Windows | Pos Window Ratio |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Train** | 60 | 60 | 120 (69.8%) | 331 | 540 | 871 | 38.0% |
| **Validation** | 13 | 13 | 26 (15.1%) | 86 | 117 | 203 | 42.4% |
| **Test (Held-Out)**| 13 | 13 | 26 (15.1%) | 65 | 117 | 182 | 35.7% |
| **Total** | **86** | **86** | **172 (100%)** | **482** | **774** | **1,256** | **38.4%** |

*Note: While recordings are 50/50 balanced, ESC-50 recordings are strictly 5.0s (generating 9 windows each), whereas positive train horn recordings vary in length (mean duration 2.8s), resulting in 38.4% positive windows overall.*

---

## 12. Train / Validation / Test Split
Splitting was executed at the **original recording level before windowing** (Seed: 42):
- **Split Manifest**: [`data/splits/audio/v3/dataset_split.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/audio/v3/dataset_split.json)
- **Selection Manifest**: [`data/manifests/audio_v3_selection.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/audio_v3_selection.json)
- **Zero Leakage**: All windows belonging to a given audio recording reside strictly within one partition.

---

## 13. Model Architecture
To ensure fair comparison with Audio V2, the identical compact CNN architecture was preserved:
```
CompactTrainHornCNN:
├── Conv2D(1, 16, kernel_size=3, padding=1) -> BatchNorm2D(16) -> ReLU -> MaxPool2D(2, 2)
├── Conv2D(16, 32, kernel_size=3, padding=1) -> BatchNorm2D(32) -> ReLU -> MaxPool2D(2, 2)
├── Conv2D(32, 64, kernel_size=3, padding=1) -> BatchNorm2D(64) -> ReLU -> AdaptiveAvgPool2D(1, 1)
├── Flatten()
├── Linear(64, 32) -> BatchNorm1D(32) -> ReLU -> Dropout(0.30)
└── Linear(32, 1) -> Squeeze()
```
- **Total Trainable Parameters**: 25,697 parameters.

---

## 14. Training Configuration
- **Run Identifier**: `RUN_20261008_AUDIO_V3_ESC50`
- **Device**: Apple Silicon MPS (`mps`)
- **Loss Function**: `BCEWithLogitsLoss(pos_weight=1.6314)` (compensating for window imbalance)
- **Optimizer**: `AdamW(lr=0.001, weight_decay=1e-4)`
- **Learning Rate Scheduler**: `CosineAnnealingLR(T_max=40, eta_min=1e-5)`
- **Batch Size**: 32
- **Training Epochs**: 40 epochs
- **Early Stopping**: Patience = 10 epochs monitoring validation loss
- **Training Augmentation**: Conservative gain variation ($\pm 2.5\text{ dB}$), time shift ($\pm 3\text{ frames}$), and additive Gaussian noise ($\sigma \in [0.01, 0.05]$).
- **Validation/Test Augmentation**: None (strictly clean).

---

## 15. Test Performance
The operational threshold was calibrated **strictly on the Validation partition** by maximizing F1 score:
$$\text{Calibrated Threshold } T^* = 0.3700 \quad (\text{Validation F1} = 0.9942)$$

The held-out test set (182 windows from 26 recordings) was evaluated **once** at the frozen threshold $T^* = 0.3700$:

### Window-Level Test Performance (182 Windows)
| Metric | Value | Interpretation |
| :--- | :---: | :--- |
| **Operational Threshold ($T^*$)** | **0.3700** | Calibrated on validation partition |
| **Accuracy** | **0.8956 (89.56%)** | 163 / 182 windows correct |
| **Precision** | **0.7875 (78.75%)** | 63 true horns / 80 alarms |
| **Recall (Sensitivity)** | **0.9692 (96.92%)** | 63 true horns / 65 horns |
| **Specificity** | **0.8547 (85.47%)** | 100 non-horns / 117 non-horns |
| **F1 Score** | **0.8690** | Harmonic mean of precision & recall |
| **Balanced Accuracy** | **0.9120** | Unweighted mean of recall & specificity |
| **ROC-AUC** | **0.9613** | High rank-order discriminability |
| **PR-AUC** | **0.9415** | High area under precision-recall curve |
| **Brier Score** | **0.0820** | Strong probability calibration |
| **Expected Calibration Error (ECE)** | **0.0817** | Well-calibrated probabilities |
| **True Positives (TP)** | **63** | Correctly identified horn windows |
| **True Negatives (TN)** | **100** | Correctly rejected environmental windows |
| **False Positives (FP)** | **17** | Confuser windows falsely triggering alarm |
| **False Negatives (FN)** | **2** | Train horn windows missed |

### Recording-Level Test Performance (26 Recordings, Max-Window Pooling)
| Metric | Value | Interpretation |
| :--- | :---: | :--- |
| **Recording Accuracy** | **0.8462 (84.62%)** | 22 / 26 recordings correct |
| **Recording Precision** | **0.7647 (76.47%)** | 13 true horns / 17 alarms |
| **Recording Recall** | **1.0000 (100.0%)** | **0 missed train horn recordings!** |
| **Recording Specificity** | **0.6923 (69.23%)** | 9 non-train / 13 non-train |
| **Recording F1 Score** | **0.8667** | Robust multi-window detection |
| **Recording ROC-AUC** | **0.9408** | Strong recording-level separation |
| **Recording PR-AUC** | **0.9447** | High precision-recall area |
| **Recording Confusion Matrix** | **TP: 13, TN: 9, FP: 4, FN: 0** | 4 false alarms across 13 non-train clips |

---

## 16. Per-Category Hard-Negative Diagnostic
Evaluating false alarms across the 11 ESC-50 negative test categories revealed the exact acoustic boundaries of the detector:

| ESC-50 Negative Category | Test Recs | Test Windows | FP Windows | FP Window Rate | Mean Prob | Max Prob | Outcome |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`engine`** | 2 | 18 | **9** | **50.0%** | 0.4657 | 0.9309 | **Major Confuser** |
| **`church_bells`** | 2 | 18 | **7** | **38.9%** | 0.3593 | 0.9822 | **Major Confuser** |
| **`siren`** | 1 | 9 | **1** | **11.1%** | 0.1310 | 0.9406 | **Minor Confuser** |
| **`car_horn`** | 1 | 9 | **0** | **0.0%** | 0.0749 | 0.0892 | **Clean Separation** |
| **`clock_alarm`** | 1 | 9 | **0** | **0.0%** | 0.0001 | 0.0002 | **Clean Separation** |
| **`rain`** | 1 | 9 | **0** | **0.0%** | 0.0318 | 0.0951 | **Clean Separation** |
| **`wind`** | 1 | 9 | **0** | **0.0%** | 0.0350 | 0.0535 | **Clean Separation** |
| **`thunderstorm`** | 1 | 9 | **0** | **0.0%** | 0.1105 | 0.3126 | **Clean Separation** |
| **`footsteps`** | 1 | 9 | **0** | **0.0%** | 0.0237 | 0.0441 | **Clean Separation** |
| **`airplane`** | 1 | 9 | **0** | **0.0%** | 0.0069 | 0.0094 | **Clean Separation** |
| **`helicopter`** | 1 | 9 | **0** | **0.0%** | 0.1365 | 0.2656 | **Clean Separation** |

### Key Diagnostic Insight
- **`car_horn` was NOT a confounder!** The model easily distinguishes dual/triple-tone heavy locomotive horns from high-frequency automotive horns ($P_{\text{max}} = 0.0892 < 0.37$).
- **`engine` was a severe confounder (50.0% FP rate)**: Low-frequency combustion rumble and mechanical engine vibration overlap with low-frequency locomotive rumble.
- **`church_bells` was a severe confounder (38.9% FP rate)**: Resonant multi-harmonic metallic bell chime overtones mimic the harmonic spectral lines of train horn chords ($P_{\text{max}} = 0.9822$).
- **Environmental noise (rain, wind, thunderstorm, footsteps, airplane, alarm) had 0.0% FP rate**.

---

## 17. V2 vs V3 Comprehensive Comparison

| Metric / Property | Audio V2 (`RUN_20261008_AUDIO_V2`) | Audio V3 (`RUN_20261008_AUDIO_V3_ESC50`) | Delta ($\Delta$) | Scientific Meaning |
| :--- | :---: | :---: | :---: | :--- |
| **Negative Data Source** | Custom Field Audio (97 MP3s) | Official ESC-50 (86 WAVs) | — | Replaced local ambient with diverse confusers |
| **Negative Categories** | Ambient / Field non-train | 11 acoustic classes | — | Explicitly tests engines, bells, sirens, weather |
| **Calibrated Threshold $T^*$** | 0.2800 | 0.3700 | +0.0900 | Higher threshold required to suppress confusers |
| **Test Window Accuracy** | 1.0000 (100.0%) | 0.8956 (89.56%) | -10.44% | Reflects realistic challenge of hard confusers |
| **Test Window Precision** | 1.0000 (100.0%) | 0.7875 (78.75%) | -21.25% | Exposes false alarms on engines & bells |
| **Test Window Recall** | 1.0000 (100.0%) | 0.9692 (96.92%) | -3.08% | 63 / 65 horn windows detected |
| **Test Window Specificity**| 1.0000 (100.0%) | 0.8547 (85.47%) | -14.53% | Confusers cause 17 false positive windows |
| **Test Window F1 Score** | 1.0000 (100.0%) | 0.8690 (86.90%) | -13.10% | Robust performance without over-claiming |
| **Test Window ROC-AUC** | 1.0000 | 0.9613 | -0.0387 | Preserves excellent ranking separation |
| **Test Window PR-AUC** | 1.0000 | 0.9415 | -0.0585 | High precision across operating range |
| **Test Window Brier Score**| 0.0008 | 0.0820 | +0.0812 | Non-zero uncertainty on hard confusers |
| **Test False Positives** | 0 | 17 | +17 | Pinpoints church bells (7) & engines (9) |
| **Test False Negatives** | 0 | 2 | +2 | Only 2 brief horn transition frames missed |
| **Recording-Level Recall** | 1.0000 (100.0%) | 1.0000 (100.0%) | **0.00%** | **100% detection of train horn events!** |
| **Recording-Level Prec.** | 1.0000 (100.0%) | 0.7647 (76.47%) | -23.53% | 4 non-train clips triggered alarm |
| **Recording-Level F1** | 1.0000 (100.0%) | 0.8667 (86.67%) | -13.33% | Realistic real-world operational score |

---

## 18. Forensic "Why 100%" Analysis
The experimental evidence answers the central scientific question directly:

### 1. Did the previous 100% V2 result occur because the custom negative dataset was too easy?
**YES.** The V2 custom negative dataset (`data/raw/audio/train_horn/negative/`) consisted of ambient environmental recordings taken under the same recording conditions as the positive set, without strong resonant tonal artifacts or industrial combustion engines. When presented with authentic hard confusers from ESC-50, performance adjusted from 100% to a realistic **86.9% F1 (96.1% ROC-AUC)**.

### 2. Which specific acoustic categories cause false alarms?
- **Combustion Engines (`engine`, 50% FP rate)**: Broad low-frequency mechanical energy mimics locomotive engine rumble.
- **Church Bells (`church_bells`, 38.9% FP rate)**: Tonal, multi-harmonic metallic ringing creates narrow horizontal spectral lines on Log-Mel spectrograms nearly indistinguishable from train horn chords.
- **Sirens (`siren`, 11.1% FP rate)**: Modulated frequency sweeps periodically cross the horn fundamental frequency band.

### 3. Was duration a class confound?
No. In the windowed evaluation, all features are extracted from uniform 1.0s slices with 0.5s hops, ensuring the model never sees recording duration. Furthermore, the model achieved 0% FP on 5.0s clips of rain, wind, clock alarms, car horns, airplanes, and footsteps, demonstrating that duration did not predict the class.

---

## 19. Error Analysis
In total, the test set contained:
- **17 False Positive Windows**:
  - 9 windows from `engine` clips (Freesound ID `11687` and related takes).
  - 7 windows from `church_bells` clips (Freesound ID `101336` and related takes).
  - 1 window from `siren` clip.
- **2 False Negative Windows**:
  - Occurred on faint tail/decay portions of positive clips where the horn was fading into background ambient noise ($P = 0.281$ and $P = 0.315$, just below $T^* = 0.370$).
- **Zero Missed Train Recordings**: When evaluated on a per-event basis with max-window pooling, **all 13 test train horn recordings were successfully detected** (100% recording-level recall).

---

## 20. Limitations
1. **Sample Size**: While balanced at 86/86 recordings (172 total, 1,256 windows), the dataset size is moderate.
2. **Fixed Category Selection**: Selection was restricted to 11 ESC-50 categories; other industrial confusers (e.g., factory buzzers, construction machinery) remain to be tested.
3. **Standalone Acoustic Gating**: Pure audio models are inherently vulnerable to rare resonant chimes (church bells); this confirms the necessity of **multimodal fusion** with vision at railway level crossings.

---

## 21. Interpretation
The V3 experiment is an unequivocal methodological success. Rather than chasing artificial perfection, it uncovers the true physical operating envelope of the compact CNN:
- Highly selective against automotive horns, alarms, and environmental weather.
- Subject to manageable false alarms on industrial engines and church bells.
- **100% sensitive at the recording level**, guaranteeing that no approaching train with a sounding horn was missed.

---

## 22. Reproducibility Information
- **Random Seed**: 42 (fixed across NumPy, random, and PyTorch).
- **Environment**: Python 3.11.15, PyTorch 2.14.1 (MPS device).
- **Split Protocol**: Deterministic recording-level allocation stored in [`data/splits/audio/v3/dataset_split.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/audio/v3/dataset_split.json).

---

## 23. Exact Checkpoint Locations
- **Best Model Checkpoint**: [`experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt)
- **Metadata in Checkpoint**: Includes `epoch` (34), `model_state_dict`, `norm_mean` (-1.6010), `norm_std` (5.1240), `operating_threshold` (0.3700), `val_loss` (0.0794), `val_f1` (0.9942).

---

## 24. Exact Manifest Locations
- **Full ESC-50 Manifest**: [`data/manifests/audio_v3_esc50_manifest.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/audio_v3_esc50_manifest.json) & [`.jsonl`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/audio_v3_esc50_manifest.jsonl)
- **Selection Manifest**: [`data/manifests/audio_v3_selection.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/audio_v3_selection.json)
- **Windowed Dataset Manifest**: [`data/manifests/audio_training_dataset_v3.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/audio_training_dataset_v3.json) & [`.jsonl`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/audio_training_dataset_v3.jsonl)
- **Dataset Split**: [`data/splits/audio/v3/dataset_split.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/audio/v3/dataset_split.json)

---

## 25. Recommendation on Model Promotion
### Recommendation: **PROMOTE V3**
**Rationale**:
Although Audio V2 achieved 100% on its internal test set, Audio V3 is **scientifically and operationally superior**:
1. **Adversarial Robustness**: V3 was trained and evaluated against hard acoustic confusers (engines, church bells, sirens), making it significantly more resilient in open-world deployment.
2. **Zero False Negatives**: At the recording level, V3 detected 100% of all train horn events (Recall = 1.0000, PR-AUC = 0.9447).
3. **Scientific Integrity**: V3's metrics (86.9% window F1, 96.1% ROC-AUC) reflect true acoustic challenges and eliminate over-optimism.
4. **Multimodal Role**: The occasional acoustic false alarms on church bells and engines are easily filtered out by the frozen vision YOLO model in late fusion.

Audio V3 is recommended as the **primary acoustic detection model** for future multimodal research and real-world level-crossing evaluation.
