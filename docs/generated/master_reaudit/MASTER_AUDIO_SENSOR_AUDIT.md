# Master Audio and Sensor Processing Audit

**Project:** Train Gate Automation — Bangladesh  
**Auditor:** Independent Principal Research Auditor, Software Architect, Computer Vision Researcher, Security Auditor and Scientific Reproducibility Reviewer  
**Mission:** Master Mission 16A  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Audited Modules:** `src/railway_detection/audio/` (`model.py`, `preprocessor.py`, `features.py`, `pipeline.py`, `training.py`), `configs/audio.yaml`, `configs/frozen_experiment_v1.yaml`, `docs/AUDIO_MODEL_V3_ESC50_REPORT.md`  
**Standard:** Strict read-only inspection of source code, configurations, and reports. Zero raw audio decoded. Zero real-data audio inference.

---

## 1. Executive Summary

This audit independently assesses the acoustic train horn classification pipeline, feature extraction mathematics, model checkpoint provenance, synchronization mechanisms, and system cadence:
1. **Model Architecture:** The acoustic detector is **`CompactTrainHornCNN`**, an ultra-lightweight 3-layer convolutional network operating on log-mel spectrograms extracted from 16 kHz audio.
2. **Audio Model V3 Provenance:** The frozen checkpoint is pinned in `configs/frozen_experiment_v1.yaml`:
   - Checkpoint: `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`
   - Expected SHA-256: `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`
   - Operating Threshold: **0.3700**
   - Historical Test Metrics: $\text{F1} = 0.869$, $\text{AUC} = 0.961$.
3. **Prohibition of Audio V2:** The historical Audio Model V2 checkpoint (`models/audio/best_checkpoint.pt`) is **explicitly prohibited** in the frozen configuration due to severe negative pool bias and data leakage.
4. **Strict Supporting Role:** Under the frozen decision policy (`configs/decision_policy_v1.yaml`, RULE_2), **audio evidence can never independently actuate crossing barriers or grant clearance**. Its operational role is strictly confined to delaying clearance dwell if acoustic horn energy is actively detected during train departure.
5. **Multi-Rate Cadence Separation:** The system operates across three asynchronous rates: 10 Hz controller simulation ticks (0.1 s), 5 Hz vision frame evaluation (0.2 s), and 2 Hz audio feature windows (0.5 s hop).

---

## 2. CompactTrainHornCNN and Feature Extraction Architecture

### 2.1 Acoustic Preprocessing and Log-Mel Spectrogram Pipeline
The audio pipeline in `src/railway_detection/audio/` enforces deterministic mathematical transformations:
- **Audio Ingestion:** Monophonic 16,000 Hz float32 PCM audio.
- **Windowing:** 1.0-second sliding windows (16,000 samples) with 0.5-second hop (8,000 samples; 50% overlap).
- **Spectrogram Parameters:**
  - Fast Fourier Transform size: $N_{\text{fft}} = 512$
  - Hop size: $N_{\text{hop}} = 256$ frames
  - Window function: Hann window
  - Frequency range: $f_{\text{min}} = 80.0\,\text{Hz}$ to $f_{\text{max}} = 8,000.0\,\text{Hz}$
  - Mel Filterbank: 64 triangular mel bands
  - Tensor Dimensions: Exactly `[64, 61]` (64 mel channels across 61 time frames per 1.0 s window).
  - Normalization: Frozen training statistics: $\mu = -1.6010, \sigma = 5.1240$.

### 2.2 Network Layer Architecture
`CompactTrainHornCNN` (`src/railway_detection/audio/model.py`) contains approximately 25,000 trainable parameters:
```
Input: [B, 1, 64, 61]
├── Conv2D(1 -> 16, 3x3, pad=1) -> BatchNorm2D(16) -> ReLU -> MaxPool2D(2, 2)   -> [B, 16, 32, 30]
├── Conv2D(16 -> 32, 3x3, pad=1) -> BatchNorm2D(32) -> ReLU -> MaxPool2D(2, 2)  -> [B, 32, 16, 15]
├── Conv2D(32 -> 64, 3x3, pad=1) -> BatchNorm2D(64) -> ReLU -> AdaptiveAvgPool2D(1, 1) -> [B, 64, 1, 1]
├── Flatten()                                                                     -> [B, 64]
├── Linear(64 -> 32) -> ReLU -> Dropout(p=0.3)                                  -> [B, 32]
└── Linear(32 -> 1) -> Sigmoid()                                                 -> [B, 1] (Probability in [0, 1])
```

---

## 3. Provenance of Historical Audio Metrics (V2 vs V3)

Historical reports document a critical methodological correction between Audio V2 and Audio V3:

| Experiment Metric | Audio Model V2 (`RUN_20261008_AUDIO_V2`) | Audio Model V3 (`RUN_20261008_AUDIO_V3_ESC50`) | Audit Assessment |
|---|:---:|:---:|---|
| **Negative Pool Source** | 95 custom environmental field recordings | Official ESC-50 standardized dataset | V2 negatives were acoustically homogeneous; V3 introduced hard confusers. |
| **Window-Level Accuracy** | **100.0%** (Overfitted / Trivial) | **89.6%** | V2 100% result was artificial; V3 exposed real acoustic boundaries. |
| **Window-Level F1 Score** | **1.000** | **0.869** | Authoritative diagnostic baseline at threshold 0.3700. |
| **ROC Area Under Curve (AUC)** | **1.000** | **0.961** | Verified in `AUDIO_MODEL_V3_ESC50_REPORT.md` (October 8, 2026). |
| **Target Operating Threshold** | 0.5000 | **0.3700** | Calibrated to prioritize recall in safety-critical warning context. |
| **Policy Status** | **PROHIBITED** in frozen config | **AUTHORIZED** primary audio baseline | Prohibiting V2 prevents data leakage and overclaiming. |

**Audit Finding:** The reported V3 metrics ($\text{F1} = 0.869$, $\text{AUC} = 0.961$) have complete, transparent provenance documented in `docs/AUDIO_MODEL_V3_ESC50_REPORT.md`. They represent diagnostic performance on held-out ESC-50 negative audio test sets, **not** end-to-end crossing performance on Layer B video.

---

## 4. Operational Role in Decision Policy

A major strength of the system's engineering is the strict confinement of audio evidence. In level-crossing safety, acoustic false alarms from road horns, sirens, or construction noise would lead to unacceptable crossing gate closures and driver non-compliance.

Inspection of `configs/decision_policy_v1.yaml` confirms that audio is bound by **RULE_2_AUDIO_SUPPORT_ONLY**:
1. **Prohibition in IDLE:** In `IDLE` state (gate open), an acoustic horn detection ($P(\text{horn}) \ge 0.3700$) **CANNOT** actuate the barrier or initiate yellow/red warning lights. Primary activation requires qualified visual detection (RULE_1).
2. **Prohibition on Clearance:** Audio evidence **CANNOT** declare a crossing clear or initiate gate opening.
3. **Departure Dwell Extension:** If the gate is in `REAR_CONFIRMED` or `CLEARANCE_DWELL` (train departing), and acoustic horn energy is actively detected, the system delays clearance and resets the clearance dwell timer (holding the gate closed). This guards against situations where an obscured second train is approaching sounding its horn while the first train departs.

---

## 5. Sensor Synchronization & Timestamp Harmonization

### 5.1 Three Distinct Synchronization Concepts
The audit identified historical confusion between three separate timing concepts that must not be conflated:

1. **Embedded Audio-Video Alignment:** The primary audio track is physically muxed inside the front camera MP4 container. Sensor drift between video frames and embedded audio samples within one camera is bounded by container clock framing ($\sim 0.0\,\text{ms}$).
2. **Inter-Camera Clock Offset ($\Delta t_{\text{R04}}$):** Front and back cameras were independent consumer recording devices without genlock or NTP. Inter-camera synchronization requires estimating empirical time offsets. As established in the dataset audit, cross-camera sync is validated for only 11 events.
3. **Human Ground-Truth Snapping:** Human boundary annotations ($T_0\text{–}T_4$) are defined on the master video frame timeline. **Historical audio offsets MUST NEVER be subtracted or added to human ground-truth timestamps.** Ground truth represents physical scene reality, not sensor delay.

---

## 6. Multi-Rate System Cadence Analysis

The software architecture integrates three asynchronous operating cadences:

| Subsystem Component | Operating Rate | Time Interval ($\Delta t$) | Code Reference | Synchronization Mechanism |
|---|:---:|:---:|---|---|
| **Gate Simulation Controller** | **10 Hz** | **0.1 s** | `decision_policy_v1.yaml` (`tick_interval_s`) | Deterministic kinematic stepping |
| **Vision Inference Engine** | **5 Hz** | **0.2 s** | `decision_policy_v1.yaml` (`vision_nominal_sampling_s`) | Temporal evidence buffer |
| **Audio Feature Extractor** | **2 Hz** | **0.5 s** | `configs/frozen_experiment_v1.yaml` (`hop_s: 0.5`) | Sliding FIFO audio window buffer |

- At each 0.1 s controller tick, the decision engine queries the latest valid evidence emitted by the vision (5 Hz) and audio (2 Hz) buffers.
- If no new audio observation has arrived within the 0.5 s hop, the previous audio probability is held up to the staleness limit ($2.0\,\text{s}$). Beyond 2.0 s, audio health transitions to `STALE`.

---

## 7. Audit Conclusion

The audio and sensor processing subsystem is rigorously designed, with strong defenses against acoustic false alarms and clear provenance for the Model V3 baseline. Audio V2 is correctly prohibited. The multi-rate timing architecture is technically sound.

**Audio and Sensor Processing Audit Status: VERIFIED ARCHITECTURE — PROVENANCE RIGOROUS.**
