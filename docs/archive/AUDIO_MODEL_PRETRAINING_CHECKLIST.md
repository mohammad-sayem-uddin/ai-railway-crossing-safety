# Audio Model Pre-Training Audit & Readiness Checklist

**Project**: AI Railway Level-Crossing Safety Research  
**Document Version**: 1.0.0  
**Audit Date**: September 21, 2026  
**Status**: PRE-TRAINING AUDIT COMPLETE — TRAINING BLOCKED PENDING NEGATIVE DATA COLLECTION

---

## 1. Current Dataset Inventory

### 1.1 Positive Audio Class (`TRAIN_HORN`)
- **Directory**: `data/raw/audio/train_horn/positive/`
- **Total Physical Files**: 87 files
- **Total Unique Recordings**: 86 unique recordings (due to one exact bitwise duplicate pair)
- **Container / Codec**: MPEG Audio Layer III (`mp3`)
- **Sample Rate**: 44,100 Hz across 100% of files
- **Channels**: 2 channels (Stereo) across 100% of files
- **Bitrate Range**: 64 kbps to 136 kbps (mean ~128 kbps)
- **Durations**:
  - Shortest recording: **1.00 s** (`22.MP3`)
  - Longest recording: **12.00 s** (`40.mp3`)
  - Average duration: **3.42 s**
  - Cumulative duration: **297.69 s (~4.96 minutes)**
- **Audit Manifest**: `data/manifests/train_horn_audio_manifest.json` (87 records, cryptographic SHA-256 hashes verified)

### 1.2 Negative Audio Class (`NON_TRAIN_HORN`)
- **Directory**: `data/raw/audio/train_horn/negative/`
- **Current Physical Files**: **0 files**
- **Status**: **CURRENTLY MISSING** (Documented in `data/raw/audio/train_horn/negative/README.md`)

### 1.3 Held-Out Layer B Real-World Video Audio
- **Directory**: `data/raw/layer_b/videos/event_001/` through `event_021/`
- **Total Videos**: 42 videos (21 front cameras, 21 back cameras)
- **Audio Stream**: AAC stereo, 48,000 Hz, ~36.59 minutes total runtime
- **Strict Protocol Role**: `real_world_evaluation` ONLY.
- **Leakage Prohibition**: Embedded audio from these 21 events must **NEVER** be extracted, sampled, or consumed for audio model training or validation.

---

## 2. Current Implementation Status

| Pipeline Component | Existing Implementation | File Location | Readiness Status | Notes |
|---|---|---|:---:|---|
| **Audio Loading** | `load_wav()` via stdlib `wave` | `audio/preprocessor.py` | ⚠️ **Partial** | Reads uncompressed `.wav` only. Fails on `.mp3`. Needs MP3/ffmpeg ingestion backend. |
| **Resampling** | `resample_linear()` via NumPy | `audio/preprocessor.py` | ⚠️ **Partial** | Linear interpolation implemented. High-frequency anti-aliasing filter (sinc/polyphase) recommended for 44.1k→16k. |
| **Mono Conversion** | Average across channel axis | `audio/preprocessor.py` | ✅ **Complete** | Correctly averages stereo channels to mono. |
| **Windowing** | `sliding_windows()` | `audio/preprocessor.py` | ✅ **Complete** | Generates `AudioWindow` objects (default 1.0s window, 0.5s hop). |
| **STFT** | `compute_stft()` via Hann window | `audio/features.py` | ✅ **Complete** | Pure NumPy implementation with Hann window and `rfft`. |
| **Mel Filterbank** | `create_mel_filterbank()` | `audio/features.py` | ✅ **Complete** | Implements Slaney/O'Shaughnessy Mel scaling. |
| **Log-Mel Spectrogram** | `compute_log_mel_spectrogram()` | `audio/features.py` | ✅ **Complete** | Computes power spectrum and projects to 64 log-mel bands in dB. |
| **Classifier Interface** | `AudioClassifierBackend(Protocol)` | `audio/model.py` | ✅ **Complete** | Runtime-checkable Protocol: `predict_window(window, sample_rate) -> (float, str)`. |
| **Baseline Classifier** | `SpectralEnergyBaseline` | `audio/model.py` | ✅ **Complete** | Deterministic power ratio classifier (80–2500 Hz). |
| **Noise Robustness** | `mix_at_snr()`, `verify_snr()` | `audio/noise_mixer.py` | ✅ **Complete** | Exact SNR mixing harness for sensitivity evaluations. |
| **Inference Pipeline** | `AudioEvidencePipeline` | `audio/pipeline.py` | ✅ **Complete** | Processes audio into `EvidenceRecord`s with `audio_safety_role: "supporting_only"`. |
| **Training Pipeline** | None (`NotSupportedInPhase0`) | `audio/__init__.py` | ❌ **Missing** | No batching, loss, optimizer, or training loop. |
| **Validation Pipeline** | None | — | ❌ **Missing** | No validation loop or epoch tracking. |
| **Metrics Calculation** | System-level only | `evaluation/metrics.py` | ❌ **Missing** | Missing audio classification metrics (AUC, F1, Precision, Recall, ECE). |
| **ROC & PR Curves** | None | — | ❌ **Missing** | No curve generation or plotting routines. |
| **Confusion Matrix** | None | — | ❌ **Missing** | No 2×2 confusion matrix computation or figure export. |
| **Threshold Selection** | Hardcoded constants | `audio/model.py` | ❌ **Missing** | No automated threshold calibration on validation splits. |
| **Model Serialization** | None | — | ❌ **Missing** | No save/load mechanism for trained audio weights/checkpoints. |

---

## 3. Missing Components Required Before Training

Before launching model training, the following concrete software components must be developed:

1. **Standardized Audio Ingestion Engine**:
   - A loader capable of reading `.mp3`, `.wav`, and extension-mismatched audio files using `ffmpeg` or `pydub`, converting them reproducibly to 16,000 Hz, 16-bit mono PCM.
2. **Audio Dataset & Split Module**:
   - Class `TrainHornDataset` inheriting from a standard dataset abstraction or PyTorch `Dataset`.
   - Group-aware split generator enforcing 70% Train / 15% Val / 15% Test partitions, grouping duplicate and co-recorded samples together.
3. **Training & Optimization Routine (`AudioTrainer`)**:
   - Configurable training pipeline for Scikit-Learn baseline (Logistic Regression / Random Forest) and Deep Learning baseline (Lightweight 2D CNN).
   - Cross-entropy or binary focal loss, Adam/AdamW optimizer, learning rate scheduler, early stopping on validation PR-AUC.
4. **Binary Audio Evaluation Metrics Suite**:
   - Implementation of Precision, Recall, Specificity, F1-Score, Area Under the ROC Curve (AUC-ROC), Average Precision (PR-AUC), Brier Score, and Expected Calibration Error (ECE).
5. **Evaluation Plotting Suite**:
   - `plot_audio_roc_curve()`, `plot_audio_pr_curve()`, and `plot_audio_confusion_matrix()`.
6. **Operating Threshold Calibrator**:
   - Validation-only threshold optimizer to select $T^*$ based on a safety-driven false positive constraint (e.g. $\text{FPR} \le 1.0\%$) or maximum F1 score.
7. **Model Checkpoint Serializer**:
   - Format for exporting model weights, input normalizers, feature parameters, operating threshold, git commit hash, and training metadata to `models/audio/`.

---

## 4. Negative-Data Requirements

The audio model is formulated as a binary classifier:
$$\mathcal{Y} \in \{\text{TRAIN\_HORN}, \text{NON\_TRAIN\_HORN}\}$$

### 4.1 Why Negative Data is Mandated
Training on positive samples alone or with pure Gaussian/white noise leads to catastrophic operational failure:
- The classifier will assign high horn probabilities to any loud acoustic transient.
- Level-crossing environments in Bangladesh are intensely noisy (traffic, horns, bells, market activity).
- Real-world false alarm rates (FAR) cannot be mathematically computed without negative background recordings.

### 4.2 Recommended Volume & Sampling Ratio
- **Current Positive Duration**: ~5.0 minutes (87 clips).
- **Target Ratio**: **1:4 to 1:6** positive-to-negative duration ratio.
- **Recommended Negative Dataset Volume**:
  - **Minimum**: 20 minutes (~300 to 400 clips of 3–5 seconds each).
  - **Recommended Research Target**: **30 to 45 minutes (~500 to 800 clips)**.

### 4.3 Required Negative Acoustic Categories
To prevent false alarms, the negative class must contain hard acoustic distractors:

```text
data/raw/audio/train_horn/negative/
├── motor_vehicle_horns/       (High Priority Hard Negatives)
│   ├── passenger_car_horns/   (High-pitch single/dual tone)
│   ├── truck_horns/           (Air horns, large diesel trucks)
│   ├── bus_horns/             (Loud pneumatic bus horns common at crossings)
│   ├── cng_auto_rickshaws/    (High-frequency electric horns)
│   └── motorcycle_horns/      (Piercing high-frequency buzzes)
│
├── stationary_crossing_sounds/
│   ├── crossing_warning_bells/ (Electric/mechanical bells ringing)
│   ├── barrier_gate_motors/    (Mechanical boom motor whine)
│   └── station_chimes/         (Stationary platform announcement tones)
│
├── railway_noise_without_horn/
│   ├── diesel_engine_idle/    (Low-frequency diesel rumble, 40-150 Hz)
│   ├── wheel_rail_flange/     (High-pitch metal wheel screech on curves)
│   ├── track_joint_click/     (Periodic wheel impact over rail joints)
│   └── train_air_brakes/      (Pneumatic brake release hisses)
│
├── ambient_traffic_flow/
│   ├── highway_vehicle_pass/  (Continuous tire-road noise)
│   ├── acceleration_revs/     (Engine revs, gear shifts)
│   └── heavy_braking_skid/    (Tire screech, sudden deceleration)
│
└── environmental_weather/
    ├── heavy_monsoon_rain/    (Continuous rain on ground/metal roofs)
    ├── wind_gusts/            (Wind turbulence buffeting microphone)
    └── crowd_market_voices/   (Human chatter, nearby roadside shop speakers)
```

> [!CAUTION]
> **Prohibition Against Synthetic Negatives**:
> Synthetic Gaussian noise, pink noise, or artificial sine waves must **NEVER** substitute for real negative audio in training. Synthetic noise is only permissible in `noise_mixer.py` for secondary SNR sensitivity benchmarks.

---

## 5. Data-Quality Audit of Current Positive Dataset

### 5.1 Duplicate Audio Files
- **Duplicate Pair**: `41.mp3` and `42.mp3`
- **SHA-256**: `17f81c16ee65f38e7d05089395e0005b8c75663f7b9470bec864274b76cf314a`
- **Action Taken**:
  - Neither file has been deleted (preserving full audit integrity).
  - Both files are tracked in `train_horn_audio_manifest.json` with `42.mp3` marked `is_duplicate: true, duplicate_of: "41.mp3"`.
- **Pre-Training Mandate**:
  - The split generator must assign `41.mp3` and `42.mp3` to the **SAME partition** (e.g. both in Train) or deduplicate them before splitting. They must never span train and test partitions.

### 5.2 File Extension Anomalies
- **Anomalous Files**: `43.pdf`, `44.pdf`, `45.pdf`, `46.pdf`
- **Technical Reality**: Despite the `.pdf` extension, all 4 files are valid MPEG Layer III (MP3) audio streams with ID3v2.4 headers and 44.1 kHz stereo audio.
  - `43.pdf`: 2.91 s, 44.1 kHz stereo MP3
  - `44.pdf`: 3.00 s, 44.1 kHz stereo MP3
  - `45.pdf`: 4.00 s, 44.1 kHz stereo MP3
  - `46.pdf`: 4.00 s, 44.1 kHz stereo MP3
- **Action Taken**:
  - Original files remain untouched in `data/raw/audio/train_horn/positive/`.
  - Non-destructive relative symlinks (`43.mp3` → `43.pdf`, etc.) have been placed in the folder.
- **Pre-Training Mandate**:
  - Preprocessing loader will ingest via the `.mp3` symlink or invoke `ffmpeg` which automatically sniffs the container header regardless of file extension.

### 5.3 Duration & Missing Number Anomalies
- Duration ranges from 1.00s to 12.00s. Sliding windowing (1.0s window, 0.5s hop) normalizes this variation.
- File `39.mp3` is missing from the numerical sequence (files go `38.mp3` → `40.mp3`). This is documented and does not affect integrity.

---

## 6. Leakage-Prevention Rules

1. **Layer B Complete Isolation**:
   - The 21 real-world Layer B events (`data/raw/layer_b/videos/`) are held out for zero-leakage multimodal evaluation.
   - Their audio tracks must NOT be used for audio model training, validation, or hyperparameter selection.
2. **Dataset V1 Complete Isolation**:
   - Dataset V1 vision data remains completely independent.
3. **Partition Disjointness**:
   - Partitioning must be performed at the **recording group level** (`split_group_id`). Multiple sliding windows derived from the same source clip must never be split across Train, Val, or Test.
4. **Duplicate Lock**:
   - `41.mp3` and `42.mp3` must share the same `split_group_id`.

---

## 7. Recommended Train / Validation / Test Methodology

- **Partition Ratios**:
  - **Train**: 70% of group-disjoint audio volume
  - **Validation**: 15% of group-disjoint audio volume
  - **Test**: 15% of group-disjoint audio volume
- **Validation Role**:
  - Model selection, early stopping, learning rate tuning, and operating threshold calibration ($T^*$).
- **Test Role**:
  - Final unbiased reporting of generalization performance. The test set is evaluated **once** and never used for threshold tuning.
- **Cross-Validation**:
  - Given the modest dataset size (~500–1000 windows), 5-fold group cross-validation on the development split (Train + Val) is strongly recommended for hyperparameter robustness before locking the final model.

---

## 8. Recommended Preprocessing Standard

All incoming audio (both positive and negative) must be standardized to a uniform raw PCM representation before feature extraction:

1. **Target Sampling Rate**: **16,000 Hz** (sufficient to capture train horns up to 8,000 Hz Nyquist frequency).
2. **Channel Format**: **Single-Channel (Mono)**.
3. **Bit Depth**: **16-bit signed PCM** (`pcm_s16le`).
4. **Amplitude Scaling**: Normalized to float64 in **$[-1.0, 1.0]$**.
5. **Windowing**:
   - Window Duration ($W$): **1.0 second** (16,000 samples).
   - Hop Size ($H$): **0.5 seconds** (8,000 samples / 50% overlap).
   - Minimum Duration: Clips $< 1.0\text{s}$ padded with symmetric reflection or zero-padding.

---

## 9. Recommended Feature Representation

### Log-Mel Spectrogram (Primary Representation)
- **FFT Size ($N_{\text{fft}}$)**: 512 samples (32.0 ms window)
- **Hop Length ($R$)**: 256 samples (16.0 ms frame step)
- **Window Function**: Hann window
- **Mel Filterbank ($M$)**: 64 triangular filters
- **Frequency Range**: $f_{\min} = 80\text{ Hz}$ to $f_{\max} = 8,000\text{ Hz}$
- **Dynamic Range Compression**: $S_{\text{dB}} = 10 \cdot \log_{10}(\max(S_{\text{mel}}, 10^{-10}))$
- **Output Tensor Shape**: $(64 \text{ mel bins}, 63 \text{ time frames})$ per 1.0-second window.

---

## 10. Recommended Classifier Architecture Hierarchy

1. **Level 1 — Deterministic Baseline (Implemented)**:
   - `SpectralEnergyBaseline`: Computes ratio of spectral power in 80–2500 Hz railway band vs wideband noise. Zero learned parameters.
2. **Level 2 — Classical ML Benchmark (Fast & Interpretable)**:
   - Feature summary: Mean, standard deviation, skewness, and delta coefficients across time for each of the 64 Mel bands (yielding a 192-dimensional feature vector).
   - Classifier: **L2-Regularized Logistic Regression** or **Random Forest** (100 trees).
3. **Level 3 — Deep Learning Acoustic Model**:
   - **Lightweight 2D CNN (Audio-CNN)**:
     - 3 Convolutional Blocks (Conv2D $3\times3$ + BatchNorm + ReLU + MaxPool2D $2\times2$)
     - Global Average Pooling
     - Dense Layer (64 units) + Dropout ($p = 0.3$)
     - Binary Sigmoid Output: $P(\text{train\_horn}) \in [0.0, 1.0]$
     - Total Parameters: $< 150,000$ (fast CPU inference on embedded hardware).

---

## 11. Required Evaluation Metrics

### 11.1 Window-Level Classification Metrics
- **Area Under the ROC Curve (AUC-ROC)**: Discriminative capability across all thresholds.
- **Average Precision / PR-AUC**: Essential metric under class-imbalanced deployment.
- **Precision, Recall (Sensitivity), Specificity, and F1-Score** at the calibrated threshold $T^*$.
- **False Alarm Rate (FAR)**: Number of false positive windows per hour of evaluable non-train audio:
  $$\text{FAR} = \frac{\text{False Positives}}{\text{Total Evaluated Hours of Non-Train Audio}}$$
- **Calibration Error**: Expected Calibration Error (ECE) and Brier Score.

### 11.2 Clip / Event-Level Metrics
- **Clip-Level Detection Rate**: Proportion of train-horn clips where at least $K \ge 1$ consecutive windows exceed $T^*$.
- **Detection Latency**: Time from horn acoustic onset to the first qualified positive detection.

---

## 12. Required Research Figures

When the model is trained and evaluated, the pipeline must automatically export the following figures to `results/figures/`:

1. **Fig-A1: Receiver Operating Characteristic (ROC) Curve**:
   - Compares Level 1 Baseline, Level 2 ML, and Level 3 CNN with Wilson score confidence bands and AUC values.
2. **Fig-A2: Precision-Recall (PR) Curve**:
   - Demonstrates precision retention across recall levels with horizontal dashed line indicating no-skill prevalence.
3. **Fig-A3: Confusion Matrix**:
   - Normalized $2\times2$ confusion matrix at the locked operating threshold $T^*$.
4. **Fig-A4: Noise Robustness & SNR Degradation Curves**:
   - F1-score and Recall plotted against noise SNR levels ($+10\text{ dB}$, $+5\text{ dB}$, $0\text{ dB}$, $-5\text{ dB}$, $-10\text{ dB}$) across traffic, rain, and wind distractors using `noise_mixer.py`.
5. **Fig-A5: Comparative Mel-Spectrogram Visualizations**:
   - Time-frequency plots contrasting: (a) Train horn multi-tone harmonic structure, (b) Truck horn, (c) Auto-rickshaw horn, and (d) Ambient rain noise.

---

## 13. Exact Conditions Required Before Audio Training is Allowed

Training must remain strictly **BLOCKED** until all 10 conditions below are satisfied and signed off:

- [ ] **Gate 1: Negative Dataset Collection**: At least 20 minutes (300+ clips) of real-world negative/background audio acquired and placed into `data/raw/audio/train_horn/negative/`.
- [ ] **Gate 2: Negative Manifest Generation**: Complete `train_horn_negative_manifest.json` generated with SHA-256 hashes, verified sample rates, and source provenance.
- [ ] **Gate 3: Standardized Ingestion Pipeline**: Ingestion script implemented that standardizes all MP3/WAV files to 16 kHz mono 16-bit PCM WAV.
- [ ] **Gate 4: Deduplication & Split Locking**: Group-disjoint Train/Val/Test split manifest created where `41.mp3` and `42.mp3` reside in the identical partition.
- [ ] **Gate 5: Layer B Data Firewall Verified**: Automated test confirms zero Layer B video audio paths are present in the audio training manifest.
- [ ] **Gate 6: Training Pipeline Implementation**: `AudioTrainer` class implemented with loss functions, optimizer, and early stopping.
- [ ] **Gate 7: Evaluation Metrics Implementation**: Binary classification metrics (AUC-ROC, PR-AUC, F1, FAR) implemented and unit-tested.
- [ ] **Gate 8: Threshold Calibration Logic**: Validation-based threshold selection utility implemented.
- [ ] **Gate 9: Model Checkpoint Serializer**: Safe model serialization format established.
- [ ] **Gate 10: Pre-Training Test Suite Pass**: 100% pass rate across all unit and integration tests.

---
**SUMMARY**: The repository's audio feature extraction, windowing, and multimodal evidence structures are solid and working. However, **model training must not proceed until the negative audio dataset is acquired and ingested under the strict conditions specified above.**
