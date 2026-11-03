# MISSION 16A-AUDIO-CHALLENGE — Independent Audio Audit Verification

**Date:** 2026-11-03
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`
**Role:** Independent Audio ML and Embedded-System Auditor (read-only)
**Execution authority:** NONE
**Research authorization:** NONE
**HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (unchanged)
**Staged files:** 0
**Protected assets accessed:** NONE

---

## 1. Executive Verdict

**Disposition: `AUDIO_AUDIT_VERIFIED_WITH_LIMITATIONS`**

The claims in `MASTER_AUDIO_SENSOR_AUDIT.md` are substantially correct when verified against source code, configuration files, and synthetic-only computation. Three factual corrections are confirmed: (1) parameter count is 25,697, not "approximately 25,000"; (2) the 10 Hz cadence originates from `decision_policy_v1.yaml` while the frozen experiment config uses 0.2 s (5 Hz), creating a documented but unresolved dual-rate configuration; (3) F1/AUC metrics are report-only with no independent real-crossing validation. Two limitations are documented: the operating threshold lacks independent validation on real crossing acoustics, and ESC-50 negative training data may not represent field conditions. No contradiction was found between the original audit's architectural claims and the source code. The audio subsystem correctly enforces RULE_2 (support-only) and the V2 prohibition in executable code.

---

## 2. Exact Architecture and Parameter Count

### 2.1 Source-verified layer sequence

From `src/railway_detection/audio/model.py` (class `CompactTrainHornCNN`, lines ~130–148):

```
Input: [B, 1, 64, 61]
├── Conv2d(1→16, k=3, p=1) → BatchNorm2d(16) → ReLU → MaxPool2d(2,2) → [B,16,32,30]
├── Conv2d(16→32, k=3, p=1) → BatchNorm2d(32) → ReLU → MaxPool2d(2,2) → [B,32,16,15]
├── Conv2d(32→64, k=3, p=1) → BatchNorm2d(64) → ReLU → AdaptiveAvgPool2d(1,1) → [B,64,1,1]
├── Flatten() → [B, 64]
├── Linear(64→32) → ReLU → Dropout(p=0.3) → [B, 32]
└── Linear(32→1) → Sigmoid → [B, 1]
```

### 2.2 Parameter count (mathematical, source-level)

| Layer | Calculation | Params |
|---|---|---|
| Conv2d(1,16,3,p=1) | 1×16×3×3 + 16 | 160 |
| BatchNorm2d(16) | 2×16 | 32 |
| MaxPool2d(2,2) | — | 0 |
| Conv2d(16,32,3,p=1) | 16×32×3×3 + 32 | 4,640 |
| BatchNorm2d(32) | 2×32 | 64 |
| MaxPool2d(2,2) | — | 0 |
| Conv2d(32,64,3,p=1) | 32×64×3×3 + 64 | 18,496 |
| BatchNorm2d(64) | 2×64 | 128 |
| AdaptiveAvgPool2d(1,1) | — | 0 |
| Linear(64,32) | 64×32 + 32 | 2,080 |
| BatchNorm1d(32) | 2×32 | 64 |
| Linear(32,1) | 32×1 + 1 | 33 |
| **TOTAL** | | **25,697** |

**Correction:** The original audit states "approximately 25,000 trainable parameters." Source-level calculation yields **25,697**. The original audit's figure is directionally correct but imprecise. The source docstring (`model.py:106`) separately claims "~75,000 parameters," which is incorrect. No checkpoint was loaded to verify empirically.

### 2.3 Discrepancy note


---

## 3. Feature Extraction Verification

### 3.1 Source-verified parameters

From `src/railway_detection/audio/features.py` and `configs/frozen_experiment_v1.yaml`:

| Parameter | Source value | Config value | Match |
|---|---|---|---|
| Sample rate | 16,000 Hz | `sample_rate: 16000` | ✓ |
| Window duration | 1.0 s (16,000 samples) | `window_s: 1.0` | ✓ |
| Hop (preprocessor) | 0.5 s (8,000 samples) | `hop_s: 0.5` | ✓ |
| FFT size | 512 | `n_fft: 512` | ✓ |
| STFT hop | 256 | `hop_length: 256` | ✓ |
| Window function | `np.hanning(n_fft)` | Hann | ✓ |
| Mel bands | 64 | `n_mels: 64` | ✓ |
| f_min | 80.0 Hz | `f_min: 80.0` | ✓ |
| f_max | 8,000.0 Hz | `f_max: 8000.0` | ✓ |
| Log transform | `10*log10(max(mel, 1e-10))` | — | ✓ |
| Expected shape | [64, 61] | `expected_feature_shape: [64, 61]` | ✓ |

### 3.2 Tensor shape verification (synthetic computation)

For a 16,000-sample input at 16 kHz:
- STFT frames: `1 + (16000 - 512) // 256 = 61`
- Output: `(64, 61)` — **confirmed by synthetic numpy computation**

For a 32,000-sample input: `(64, 124)` — linear scaling confirmed.

### 3.3 Normalization

- Source: `configs/frozen_experiment_v1.yaml` lines 42–45: `mean: -1.600999355316162`, `std: 5.1239728927612305`, `source: "checkpoint"`
- `model.py` lines 222–240: checkpoint loading enforces presence of `norm_mean`/`norm_std` or legacy `feature_mean`/`feature_std`; silent fallback is prohibited.
- Training and inference use the same `compute_log_mel_spectrogram` function with identical parameters. **Identity confirmed.**

### 3.4 Two-hop ambiguity

The system has TWO hop values:
1. **Preprocessor hop** (`preprocessor.py`): 0.5 s between analysis windows (2 Hz emission rate)
2. **STFT hop** (`features.py`): 256 samples = 16 ms within each 1.0 s window (61 frames)

These are distinct and non-contradictory. The original audit correctly describes both.

---

## 4. Audio V3 Provenance Evidence Matrix

| Item | Value | Classification | Evidence |
|---|---|---|---|
| Checkpoint path | `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt` | Configuration-declared | `frozen_experiment_v1.yaml:22` |
| Expected SHA-256 | `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782` | Configuration-declared | `frozen_experiment_v1.yaml:23` |
| Operating threshold | 0.3700 | Configuration-declared | `frozen_experiment_v1.yaml:25`, `decision_policy_v1.yaml:48` |
| Model name | CompactTrainHornCNN | Source-verified | `model.py` class definition |
| F1 = 0.869 | Historical test metric | Report-only | `AUDIO_MODEL_V3_ESC50_REPORT.md` |
| AUC = 0.961 | Historical test metric | Report-only | `AUDIO_MODEL_V3_ESC50_REPORT.md` |
| Normalization μ/σ | -1.6010 / 5.1240 | Configuration-declared | `frozen_experiment_v1.yaml:43-44` |
| ESC-50 negative pool | 86 recordings, 11 confuser categories | Report-only | `select_and_manifest_audio_v3.py` |
| Checkpoint file exists | Not verified | Unverified | No file access performed |

**Critical limitation:** The checkpoint was NOT loaded, hashed, or inspected. All checkpoint-related claims are configuration-declared or report-only. The SHA-256 binding in `frozen_experiment_v1.yaml` provides integrity verification at load time but was not exercised in this audit.

---

## 5. Audio V2 Prohibition Enforcement Assessment

### 5.1 Declaration

`configs/frozen_experiment_v1.yaml` lines 26–29:
```yaml
prohibited:
  audio_v2:
    path: "models/audio/best_checkpoint.pt"
    sha256: "59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5"
```

### 5.2 Executable enforcement

- `src/railway_detection/experiments/frozen_config.py` line 33–36: `PROHIBITED_AUDIO_V2_SHA256` and `PROHIBITED_AUDIO_V2_PATH` constants defined.
- `frozen_config.py` lines 367–374: `verify_checkpoint_integrity` checks audio_v3 hash ≠ prohibited hash, path ≠ prohibited path, and path does not contain `models/audio`.
- `src/railway_detection/audio/model.py` lines 199–201: `_load_checkpoint` calls `verify_not_prohibited_checkpoint(ckpt_path)` before `torch.load`.
- `src/railway_detection/experiments/leakage_guard.py`: exports `verify_not_prohibited_checkpoint`.

### 5.3 Assessment

**Status: ENFORCED IN EXECUTABLE CODE.** The prohibition is not merely a YAML declaration. It is checked at checkpoint integrity verification time and again at model load time. No route was found that bypasses both checks.

### 5.4 Residual risk

If a caller constructs a `CompactTrainHornCNN` directly without going through `_load_checkpoint`, the prohibition is not enforced at the constructor level. However, this would require bypassing the entire frozen-config pipeline, which is a separate governance violation.

---

## 6. Audio-to-State-Machine Authority Trace

### 6.1 Complete path

```
Audio window → classifier.predict_window() → (confidence, label)
→ AudioEvidencePipeline.process_windows() → EvidenceRecord(timestamp_s=window_end_s, modality=AUDIO)
→ MultimodalEvidenceCollector.add_evidence() → buffer
→ MultimodalEvidenceCollector.generate_frame_at() → MultimodalFrame.audio_records
→ MultimodalDecisionEngine.evaluate_frame() → has_audio_train_presence(frame, threshold)
→ State transition logic
```

### 6.2 Authority matrix

| Action | Can audio do it? | Evidence |
|---|---|---|
| Initiate closure (IDLE→TRAIN_APPROACHING) | **NO** | `decision_engine.py:402-404`: audio in IDLE logs RULE_2 but does not transition |
| Extend closure | **NO** | No audio-driven extension path found |
| Delay clearance dwell | **YES** | `decision_engine.py:489-491`: audio in REAR_CONFIRMED resets dwell timer |
| Grant clearance | **NO** | RULE_3 requires vision departure evidence |
| Trigger opening | **NO** | Gate opening requires CROSSING_CLEAR state |
| Override stale vision | **NO** | RULE_5 stale-source abort is vision-driven |
| Affect fail-safe behavior | **INDIRECT** | `decision_engine.py:562-564`: audio in FAULT_FAIL_SAFE holds closed but does not change state |

### 6.3 Policy-to-implementation match

`decision_policy_v1.yaml` RULE_2_AUDIO_SUPPORT_ONLY states: "Audio alone cannot actuate gate in IDLE; delays clearance dwell in REAR_CONFIRMED."

Implementation in `decision_engine.py` matches this policy exactly. **NO MISMATCH FOUND.**

### 6.4 Audio label vocabulary

`fusion/rules.py` line 60: `AUDIO_TRAIN_LABELS = frozenset({"train", "horn", "rail", "train_horn"})`

The model outputs binary `train`/`ambient`. The label set includes additional synonyms for compatibility but the classifier only produces `train` or `ambient`. **INFORMATIONAL.**

---

## 7. Cadence Reconciliation

### 7.1 Observed rates

| Source | Rate | Interval | File | Line |
|---|---|---|---|---|
| Gate simulation controller | 10 Hz | 0.1 s | `configs/decision_policy_v1.yaml` | `tick_interval_s: 0.1` (line 25) |
| Frozen experiment evaluation tick | 5 Hz | 0.2 s | `configs/frozen_experiment_v1.yaml` | `timing.tick_s: 0.2` (line 54) |
| Vision nominal sampling | 5 Hz | 0.2 s | `configs/decision_policy_v1.yaml` | `vision_nominal_sampling_s: 0.2` (line 26) |
| Audio feature hop | 2 Hz | 0.5 s | `configs/frozen_experiment_v1.yaml` | `audio.hop_s: 0.5` (line 34) |
| Collector replay stride (default) | 10 Hz | 0.1 s | `src/railway_detection/fusion/collector.py` | `stride_s: float = 0.1` (line 217) |

### 7.2 Contradiction analysis

The original audio audit states: "10 Hz controller simulation ticks (0.1 s)." This is sourced from `decision_policy_v1.yaml` line 25 (`tick_interval_s: 0.1`).

The frozen experiment configuration (`frozen_experiment_v1.yaml` line 54) declares `tick_s: 0.2` (5 Hz).

**These are not contradictory.** They describe different contexts:
- `decision_policy_v1.yaml` defines the **simulation/decision stepping rate** (10 Hz).
- `frozen_experiment_v1.yaml` defines the **evaluation/replay tick** (5 Hz).

The original audit's cadence table is accurate but conflates simulation stepping with evaluation replay. **INFORMATIONAL finding — no code change required, but documentation should clarify the distinction.**

### 7.3 Audio evidence staleness

- Audio window duration: 1.0 s
- Audio hop: 0.5 s
- Controller tick: 0.1 s (simulation) or 0.2 s (evaluation)
- Collector window tolerance: 0.5 s (default in `collector.py` line 57)
- Source staleness timeout: 2.0 s (`frozen_experiment_v1.yaml` line 61)

Audio evidence is stamped at `window_end_s` (pipeline.py line 109). At a 0.5 s hop, the most recent audio evidence can be up to 0.5 s old relative to the current frame time. The 2.0 s staleness timeout provides ample margin. **No timing violation identified.**

---

## 8. Threshold and Metric Validity

### 8.1 Threshold 0.3700

- Declared in: `frozen_experiment_v1.yaml:25`, `decision_policy_v1.yaml:48`, `model.py` default parameter
- Enforcement: `model.py:245-249` prevents runtime override mismatch
- Calibration basis: Report-only (`AUDIO_MODEL_V3_ESC50_REPORT.md`)
- Independent validation on real crossing audio: **NOT PERFORMED**

### 8.2 F1 = 0.869, AUC = 0.961

- Source: `docs/AUDIO_MODEL_V3_ESC50_REPORT.md` (October 8, 2026)
- Test set: ESC-50 held-out negatives + positive train horn recordings
- Class balance: Not independently verified in this audit
- Leakage-resistant split: `dataset.py` references `split_group_id`, suggesting group-based splitting; exact protocol not independently verified here
- Event-independent evaluation: ESC-50 is window-level, not event-level
- Confidence intervals: **NOT REPORTED**
- Threshold-selection protocol: Report-only; no independent reproduction

### 8.3 Verdict

**The metrics cannot establish real-crossing acoustic performance.** They are diagnostic window-level classification results on a curated ESC-50 negative pool. Transfer to field conditions (road horns, sirens, construction, wind, rail clatter) is unverified. **HIGH finding.**

---

## 9. Synchronization and Latency Limitations

### 9.1 Audio timestamp assignment

`pipeline.py` line 109: `window_end_s = window.start_time_s + window.duration_s`

Audio evidence is stamped at the **end** of the analysis window, not the center. This is causally correct (the observation is only complete at window end) but introduces up to 1.0 s of inherent latency relative to the acoustic event within the window.

### 9.2 Collector matching

`collector.py` line 57: `window_tolerance_s: float = 0.5` (default)
`collector.py` line 166: `t_min = current_master_time_s - self.window_tolerance_s`

Audio records older than `window_tolerance_s` relative to the current frame are excluded. At 0.5 s tolerance and 0.5 s hop, at most one audio window is available per frame. **No overlap ambiguity.**

### 9.3 Inter-camera vs. audio-video sync

The original audit correctly distinguishes three synchronization concepts:
1. Embedded audio-video alignment (bounded by container framing)
2. Inter-camera clock offset (R04, validated for 11 events only)
3. Human ground-truth snapping (never offset by audio delays)

**No software cross-correlation can establish physical synchronization accuracy.** The audio-video alignment within a single camera is bounded by muxing, not measured. **INFORMATIONAL.**

### 9.4 Staleness

`frozen_experiment_v1.yaml` line 61: `source_staleness_s: 2.0`

If no new audio observation arrives within 2.0 s, the source transitions to STALE. At 0.5 s hop, this allows up to 4 missed windows before staleness. The decision engine holds the last audio probability during this window. **No timing uncertainty beyond the documented staleness limit.**

---

## 10. Contradictions Against Original Audio Audit

| Claim in original audit | Verification result | Status |
|---|---|---|
| ~25,000 parameters | 25,697 (source-level) | CORRECTED (minor imprecision) |
| Source docstring "~75,000" | 25,697 actual | DOCUMENTATION ERROR IN SOURCE |
| 10 Hz controller tick | `decision_policy_v1.yaml` says 0.1 s; `frozen_experiment_v1.yaml` says 0.2 s | DUAL-RATE CONFIGURATION (not a single authoritative rate) |
| F1 = 0.869, AUC = 0.961 | Report-only, no independent verification | REPORT-ONLY |
| Threshold 0.3700 calibrated | No calibration protocol independently verified | REPORT-ONLY |
| Audio cannot actuate gate | Source-verified via RULE_2 and decision engine | VERIFIED |
| V2 prohibited | Source-verified in executable code | VERIFIED |
| Feature shape [64, 61] | Synthetic computation confirms | VERIFIED |
| Normalization from checkpoint | Config declares; not exercised | CONFIGURATION-DECLARED |

---

## 11. Findings

| ID | Severity | Finding | Source |
|---|---|---|---|
| AC-01 | INFORMATIONAL | Parameter count is 25,697, not ~25,000 or ~75,000 | `model.py` lines 116–144 |
| AC-02 | INFORMATIONAL | Source docstring claims ~75,000 params (wrong) | `model.py` line 106 |
| AC-03 | INFORMATIONAL | Dual-rate configuration (0.1 s vs 0.2 s) unresolved | `decision_policy_v1.yaml:25`, `frozen_experiment_v1.yaml:54` |
| AC-04 | HIGH | F1/AUC metrics lack real-crossing validation | `AUDIO_MODEL_V3_ESC50_REPORT.md` (report-only) |
| AC-05 | HIGH | Threshold 0.3700 lacks independent field validation | `frozen_experiment_v1.yaml:25` |
| AC-06 | MEDIUM | ESC-50 negatives may not represent field acoustics | `select_and_manifest_audio_v3.py` |
| AC-07 | INFORMATIONAL | Audio timestamp at window end introduces up to 1.0 s latency | `pipeline.py:109` |
| AC-08 | INFORMATIONAL | BatchNorm1d(32) omitted from original audit diagram | `model.py:132` |

---

## 12. Researcher Decisions Required

1. **Resolve dual-rate configuration:** Determine whether the authoritative controller tick is 0.1 s (simulation) or 0.2 s (frozen experiment). These are currently declared in two separate config files with different values.
2. **Validate threshold on real crossing audio:** The 0.3700 threshold is calibrated on ESC-50 + synthetic positives. A researcher decision is needed on whether field validation is required before any real-data evaluation.
3. **Assess ESC-50 representativeness:** Determine whether the 11 ESC-50 confuser categories adequately represent the acoustic environment at the Bangladesh crossing.
4. **Correct source docstring:** The `model.py` docstring claims ~75,000 parameters. This should be corrected to ~25,697 (or the researcher may choose to leave it as historical documentation).

---

## 13. Explicit Statement

**No protected assets or real audio were accessed during this audit.**

All verification was performed through:
- Static source code inspection (reading `.py` files)
- Configuration file inspection (reading `.yaml` files)
- Synthetic-only computation (numpy zeros array for feature shape)
- Git status verification (read-only commands)
- Runtime inspection of class/function signatures via Python import

No raw audio files were opened, decoded, played, hashed, or otherwise accessed. No model checkpoints were loaded. No production caches were read. No real-data inference or evaluation was performed.

**HEAD unchanged:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
**Staged:** 0
**data/governance/:** contains only `leg_exec_authorization.json`

---

## 14. Final Disposition

**`AUDIO_AUDIT_VERIFIED_WITH_LIMITATIONS`**

The original `MASTER_AUDIO_SENSOR_AUDIT.md` is architecturally accurate. Its feature pipeline, V2 prohibition, RULE_2 authority boundary, and synchronization concepts are confirmed by source inspection. The principal limitations are:

1. F1/AUC and threshold claims are diagnostic/report-only and do not establish real-crossing acoustic performance.
2. The repository declares two timing contexts (10 Hz simulation policy and 5 Hz frozen evaluation tick) that require documentation clarification.
3. ESC-50 representativeness for the Bangladesh crossing remains unestablished.
4. The source docstring's `~75,000` parameter claim is incorrect; source-level count is 25,697.

This audit does not advance the project to Mission 16 and does not authorize real-data execution.

---

*This report was produced as a read-only independent challenge audit. It does not advance the project to Mission 16, authorize real-data execution, or modify the original `MASTER_AUDIO_SENSOR_AUDIT.md`.*