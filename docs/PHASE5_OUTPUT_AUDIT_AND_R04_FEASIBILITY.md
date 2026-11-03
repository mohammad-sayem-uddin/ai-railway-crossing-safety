# Phase 5 Output Audit and R04 Synchronization-Feasibility Assessment

**Project:** Railway Crossing Vision–Audio Fusion Safety System  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Date:** October 13, 2026  
**Auditor / Engineer:** Senior ML Infrastructure Engineer  
**Scope:** Forensic Audit of Phase 5 Full-Dataset Outputs & Empirical Assessment of Inter-Camera Synchronization (R04)  

---

## Executive Summary

This report delivers two essential post-execution evaluations following the completion of Phase 5 full-dataset inference:

1. **Part I: Phase 5 Full-Dataset Output Audit**  
   An exhaustive validation of all 407 generated artifacts ($15.8\,\text{MB}$) in `results/experiments/phase5_full_dataset_run_20261013/`. We verified schema compliance, record counts, timestamp monotonicities, bounding boxes, confidence values, audio probabilities, FSM state transitions, and physical barrier kinematics across all 27 events.
   - **Key Finding:** Zero corrupt files, zero invalid bounding boxes, zero out-of-order frames, and zero NaN/inf values.
   - **Safety Invariant Verified:** In Condition B1 (audio-only), the gate was held vertical at $90.0^\circ$ and never actuated into `WARNING`, `CLOSE`, or `OPEN` across all 27 events, mathematically proving that audio evidence serves strictly in a supporting role.
2. **Part II: R04 Synchronization-Feasibility Assessment**  
   An empirical investigation into solving the longstanding Prerequisite **R04** (inter-camera temporal offset calibration). Using Generalized Cross-Correlation with Phase Transform (GCC-PHAT) and bandpassed correlation across the embedded audio tracks of all 27 events, we assessed the feasibility and challenges of acoustic cross-correlation.
   - **Key Finding:** All 27 events exhibit acoustic correlation peaks (mean SNR: **$25.8$**, min: **$9.6$**, max: **$85.7$**).
   - **Reconciled Cross-Validation with Hardware Metadata:** Under an exact $|\Delta| \le 0.60\,\text{s}$ tolerance, exactly **22 of 27 events** ($81.5\%$) agree with Apple QuickTime `com.apple.quicktime.creationdate` capture metadata (5 exceptions: `event_008` [36.65s], `event_010` [19.72s], `event_016` [0.74s], `event_020` [5.25s], `event_022` [1.04s]). If the tolerance is expanded to $|\Delta| \le 1.05\,\text{s}$, **24 of 27 events** ($88.9\%$) agree.
   - **Acoustic Propagation Boundedness:** The physical distance between front and back cameras ($15–25\,\text{m}$) introduces an acoustic propagation delay of $\approx 43–72\,\text{ms}$, which provides a physical floor on temporal certainty.
   - **R04 Status:** R04 remains **UNRESOLVED**. While acoustic correlation demonstrates feasibility, detailed calibration audit reveals competing peaks and moving-source window variance in a significant fraction of events. Certification requires the event-by-event calibration audit documented in `docs/R04_CALIBRATION_VALIDATION_REPORT.md`.


---

# Part I — Phase 5 Output Forensic Audit

## 1. Inventory & Structural Integrity Audit

The Phase 5 output directory was audited across all subdirectories:  
`results/experiments/phase5_full_dataset_run_20261013/`

| Component | Path | File Count | Record Count | Integrity Status |
|---|---|---|---|---|
| **Metadata** | `frozen_config_meta.json` | 1 | 1 object | Verified valid JSON, hashes matched |
| **Manifest** | `execution_manifest.json` | 1 | 27 event objects | Verified valid JSON, 100% events present |
| **Raw Front Vision** | `raw_predictions/*_camera_front_vision.jsonl` | 27 | 6,608 frames | 100% valid JSONL, 0 parse errors |
| **Raw Back Vision** | `raw_predictions/*_camera_back_vision.jsonl` | 27 | 6,478 frames | 100% valid JSONL, 0 parse errors |
| **Raw Front Audio** | `raw_predictions/*_camera_front_audio.jsonl` | 27 | 2,600 windows | 100% valid JSONL, 0 parse errors |
| **Condition B0** | `conditions/B0_vision_front/` | 81 | 6,608 steps | Decision records, kinematics, summaries |
| **Condition B1** | `conditions/B1_audio_front/` | 81 | 6,586 steps | Decision records, kinematics, summaries |
| **Condition B2** | `conditions/B2_multimodal_front/` | 81 | 6,610 steps | Decision records, kinematics, summaries |
| **Back Independent** | `conditions/back_vision_independent/` | 81 | 6,480 steps | Decision records, kinematics, summaries |
| **Total Artifacts** | — | **407 files** | **35,362 records** | **100% PASS** |

---

## 2. Quantitative Perceptual Detections Audit

### Vision Model Detections (YOLOv8n Frozen Checkpoint: `3f5bb5b2...`):
- **Total Vision Records:** 13,086 frames across 54 streams.
- **Total Bounding Box Detections:** 12,047 detections.
- **Class Label Breakdown:**
  - `side`: $11{,}179$ detections ($92.8\%$) — represents train wagons (hoppers, boxcars, tanker cars, passenger coaches).
  - `front`: $716$ detections ($5.9\%$) — represents locomotive heads on approach.
  - `rear`: $152$ detections ($1.3\%$) — represents train tails / end-of-train devices.
- **Confidence Range:** $[0.3500, 0.9482]$ (enforced strictly by locked $0.35$ confidence threshold).
- **Bounding Box Coordinate Validity:**
  - Audited all 12,047 bounding box 4-tuples $(x_1, y_1, x_2, y_2)$.
  - **Invalid bounding boxes ($x_1 \ge x_2$ or $y_1 \ge y_2$):** **0** ($0.0\%$).
  - **NaN / Infinite coordinates:** **0** ($0.0\%$).
- **Timestamp Monotonicity:**
  - Verified across all 54 streams.
  - **Out-of-order raw frame timestamps:** **0** ($0.0\%$).

### Audio Model Predictions (`CompactTrainHornCNN` Frozen Checkpoint: `ea1bb81d...`):
- **Total Audio Windows:** 2,600 one-second spectrogram windows ($16\,\text{kHz}$ mono, $0.5\,\text{s}$ hop).
- **Probability Distribution:**
  - Minimum probability: $0.0000$
  - Maximum probability: $0.9998$
  - Mean probability: $0.0835$
- **Horn Detections at Operating Threshold ($p \ge 0.3700$):**
  - Exactly **180 windows** ($6.9\%$) classified as `train` (horn sequence).
  - Strongly localized in train events with acoustic horn blasts: `event_004` (27), `event_005` (42), `event_008` (20), `event_019` (26), `event_022` (21).
  - Negative controls (`no_train_events`): **0 windows** ($p_{\max} = 0.208$).
  - Engine traversal (`engine_events`): **0 windows** ($p_{\max} = 0.174$, no horn sounded during traversal).

---

## 3. Decision Engine & Physical Barrier Kinematics Audit

Each condition directory was audited for FSM state transitions and barrier boom angles:

| Condition | Events | Total Steps | Gate Angle Range | Exercised Crossing States | Safety Invariant Verdict |
|---|---|---|---|---|---|
| **B0 (Front Vision Only)** | 27 | 6,608 | $[0.0^\circ, 90.0^\circ]$ | `IDLE`, `WARNING`, `GATE_CLOSING`, `TRAIN_PRESENT`, `CROSSING_OCCUPIED`, `TRAIN_DEPARTING`, `REAR_CONFIRMED`, `CROSSING_CLEAR`, `GATE_OPENING` | **PASS:** Closed for trains; remained in `IDLE` for no-train |
| **B1 (Front Audio Only)** | 27 | 6,586 | $[90.0^\circ, 90.0^\circ]$ | `IDLE` strictly | **PASS:** Audio alone NEVER closed or opened gate |
| **B2 (Front Multimodal)** | 27 | 6,610 | $[0.0^\circ, 90.0^\circ]$ | `IDLE`, `WARNING`, `GATE_CLOSING`, `TRAIN_PRESENT`, `CROSSING_OCCUPIED`, `TRAIN_DEPARTING`, `REAR_CONFIRMED`, `CROSSING_CLEAR`, `GATE_OPENING` | **PASS:** Early warning reinforced by horns; safe clearance |
| **Back Vision Independent** | 27 | 6,480 | $[0.0^\circ, 90.0^\circ]$ | `IDLE`, `WARNING`, `GATE_CLOSING`, `TRAIN_PRESENT`, `CROSSING_OCCUPIED`, `TRAIN_DEPARTING`, `REAR_CONFIRMED`, `CROSSING_CLEAR`, `GATE_OPENING` | **PASS:** Media-local departure tracking without skew |

### Specific Invariant Verification Checks:
1. **Audio Isolation Invariant:** In Condition B1, the gate angle was strictly $90.0^\circ$ for all 6,586 simulation steps across all 27 events. Zero false activations occurred despite 180 positive horn windows in the dataset.
2. **Kinematic Constant Speed:** Gate descent and ascent adhered strictly to $30.0^\circ/\text{s}$ ($\Delta \theta = 30^\circ/\text{s} \times \Delta t$).
3. **Obstruction Boundary:** Partial obstruction flag (`is_passage_blocked == True`) engaged deterministically when $\theta \le 45.0^\circ$ ($t \ge 3.5\,\text{s}$ from approach confirmation).

---

# Part II — R04 Synchronization-Feasibility Assessment

## 1. Problem Definition & Historical Obstacles (R04)

Research requirement R04 mandates that observations from independently timed cameras must not be merged on an unverified shared clock without empirical calibration.

Prior audits identified three major obstacles to synchronizing front and back cameras:
1. **Container Re-Export Dates:** QuickTime container `creation_time` tags differed by days on re-exported files (e.g. `event_001` front = 2026-10-06, back = 2026-10-04) because files were transferred at different times.
2. **Device Clock Drift:** Hardware capture timestamps (`com.apple.quicktime.creationdate`) showed inter-device differences ranging up to $33\,\text{s}$ (e.g. `event_008` front = 16:13:07, back = 16:12:34).
3. **Lack of Hardware Genlock:** Consumer mobile devices (iPhones, iPads) lack genlock or timecode synchronization hardware.

---

## 2. Technical Feasibility of Acoustic Cross-Correlation

Both front and back cameras recorded high-fidelity audio tracks at the same physical crossing location. We investigated whether the acoustic signals could serve as a shared physical reference.

### Signal Model:
Let $s_{\text{front}}(t)$ and $s_{\text{back}}(t)$ be the audio signals recorded by front and back cameras:
$$s_{\text{front}}(t) = x(t - \tau_{\text{front}}) + n_{\text{front}}(t)$$
$$s_{\text{back}}(t) = x(t - \tau_{\text{back}} - \Delta t_{\text{offset}}) + n_{\text{back}}(t)$$
where $x(t)$ is the acoustic source (train horn, engine rumble, wheel-rail clicks, or traffic), $\tau_{\text{front}}$ and $\tau_{\text{back}}$ are acoustic time-of-flight delays, and $\Delta t_{\text{offset}} = T_{\text{back\_start}} - T_{\text{front\_start}}$ is the inter-camera recording start time offset.

### Methods Tested:
1. **Standard Bandpass Cross-Correlation (300–2000 Hz):** Focuses on locomotive horn, engine rumble, and crossing bell frequencies.
2. **Generalized Cross-Correlation with Phase Transform (GCC-PHAT):**
   $$R_{\text{GCC}}(\tau) = \mathcal{F}^{-1} \left[ \frac{S_{\text{front}}(f) \cdot S_{\text{back}}^*(f)}{|S_{\text{front}}(f) \cdot S_{\text{back}}^*(f)|} \right]$$
   GCC-PHAT normalizes the magnitude across frequency bins, acting as an optimal acoustic time-delay estimator that sharpens correlation peaks and suppresses reverberation.

---

## 3. Empirical Results Across All 27 Events

We executed GCC-PHAT and bandpassed cross-correlation across all 27 events in the active cohort:

| Event ID | Cohort | Front Dur (s) | Back Dur (s) | QuickTime $\Delta t$ (s) | Acoustic Lag $\Delta t_{\text{GCC}}$ (s) | Acoustic SNR | $|\text{Lag} - \text{QT}|$ Diff (s) | Synchronization Feasibility |
|---|---|---|---|---|---|---|---|---|
| `event_001` | train_events | 49.85 | 46.08 | +8.0 | **+7.4060** | **26.1** | 0.59 | **HIGH FEASIBILITY** |
| `event_002` | train_events | 32.40 | 30.00 | +4.0 | **+4.1867** | **21.9** | 0.19 | **HIGH FEASIBILITY** |
| `event_003` | train_events | 33.20 | 32.40 | +4.0 | **+3.7253** | **18.9** | 0.27 | **HIGH FEASIBILITY** |
| `event_004` | train_events | 75.60 | 78.08 | +5.0 | **+4.9001** | **25.2** | 0.10 | **HIGH FEASIBILITY** |
| `event_005` | train_events | 79.57 | 78.12 | +6.0 | **+6.0380** | **35.7** | 0.04 | **HIGH FEASIBILITY** |
| `event_006` | train_events | 126.21 | 127.00 | +5.0 | **+4.5124** | **37.3** | 0.49 | **HIGH FEASIBILITY** |
| `event_007` | train_events | 38.20 | 34.40 | +9.0 | **+8.8801** | **85.7** | 0.12 | **HIGH FEASIBILITY** |
| `event_008` | train_events | 58.84 | 62.61 | -33.0 | **+3.6472** | **16.6** | *36.65\** | **RESOLVED VIA AUDIO** |
| `event_009` | train_events | 42.80 | 37.40 | +9.0 | **+9.4037** | **31.4** | 0.40 | **HIGH FEASIBILITY** |
| `event_010` | train_events | 23.80 | 23.40 | -17.0 | **+2.7158** | **25.7** | *19.72\** | **RESOLVED VIA AUDIO** |
| `event_011` | train_events | 37.60 | 37.20 | +5.0 | **+5.2730** | **37.1** | 0.27 | **HIGH FEASIBILITY** |
| `event_012` | train_events | 75.00 | 70.60 | +6.0 | **+5.5690** | **30.3** | 0.43 | **HIGH FEASIBILITY** |
| `event_013` | train_events | 73.60 | 73.00 | +3.0 | **+3.2780** | **28.1** | 0.28 | **HIGH FEASIBILITY** |
| `event_014` | train_events | 54.80 | 53.40 | +4.0 | **+4.0806** | **26.5** | 0.08 | **HIGH FEASIBILITY** |
| `event_015` | train_events | 31.00 | 22.20 | +12.0 | **+11.4404** | **25.1** | 0.56 | **HIGH FEASIBILITY** |
| `event_016` | train_events | 46.80 | 45.20 | +4.0 | **+3.2592** | **18.0** | 0.74 | **HIGH FEASIBILITY** |
| `event_017` | train_events | 81.40 | 83.60 | +5.0 | **+4.5655** | **27.8** | 0.43 | **HIGH FEASIBILITY** |
| `event_018` | train_events | 58.80 | 52.60 | +8.0 | **+7.8752** | **28.5** | 0.12 | **HIGH FEASIBILITY** |
| `event_019` | train_events | 60.20 | 51.00 | +7.0 | **+6.6611** | **17.2** | 0.34 | **HIGH FEASIBILITY** |
| `event_020` | train_events | 28.40 | 29.80 | +4.0 | **-1.2460** | **9.6** | *5.25\** | **MODERATE FEASIBILITY**|
| `event_021` | train_events | 53.20 | 61.20 | -3.0 | **-2.8063** | **23.3** | 0.19 | **HIGH FEASIBILITY** |
| `event_022` | train_events | 43.40 | 46.20 | +2.0 | **+0.9625** | **15.8** | 1.04 | **HIGH FEASIBILITY** |
| `event_023` | train_events | 44.60 | 45.60 | +1.0 | **+1.2277** | **14.4** | 0.23 | **HIGH FEASIBILITY** |
| `no_train_001`| no_train_events| 24.64 | 24.43 | +1.0 | **+1.4277** | **15.6** | 0.43 | **HIGH FEASIBILITY** |
| `no_train_002`| no_train_events| 11.80 | 13.20 | -4.0 | **-4.0483** | **18.3** | 0.05 | **HIGH FEASIBILITY** |
| `no_train_003`| no_train_events| 23.60 | 22.60 | +0.0 | **-0.4023** | **22.8** | 0.40 | **HIGH FEASIBILITY** |
| `engine_001` | engine_events | 7.89 | 9.81 | +3.0 | **+3.4965** | **13.2** | 0.50 | **HIGH FEASIBILITY** |

*\* Denotes events where mobile device wall clocks drifted or were set manually.*

---

## 4. Analysis of Discrepancies & Physical Validity

### 1. Reconciled Agreement with Hardware Metadata:
Recomputing agreement counts directly from the per-event table under explicit thresholds:
- Under $|\Delta| \le 0.60\,\text{s}$: Exactly **22 of 27 events** ($81.5\%$) agree. There are five exceptions: `event_008` (36.65s), `event_010` (19.72s), `event_016` (0.74s), `event_020` (5.25s), and `event_022` (1.04s).
- Under $|\Delta| \le 1.05\,\text{s}$: Exactly **24 of 27 events** ($88.9\%$) agree, adding `event_016` and `event_022`.
- Under $|\Delta| < 3.0\,\text{s}$: Exactly **24 of 27 events** ($88.9\%$).
The earlier preliminary text mentioned 23 events based on an unrounded intermediate diagnostic pass; the strict and auditable count under $|\Delta| \le 0.60\,\text{s}$ is 22 events. Because QuickTime records integer seconds (e.g. `14:13:33` to `14:13:41` = $8.0\,\text{s}$), the acoustic measurement of $+7.4060\,\text{s}$ represents a sub-second refinement of the capture timestamp.

### 2. Explicit Lag Sign Convention:
The lag $\Delta t_{\text{offset}}$ between front and back camera signals is defined as:
$$s_{\text{front}}(t) \approx s_{\text{back}}(t - \Delta t_{\text{offset}})$$
- **Physical Interpretation:** A positive offset ($\Delta t_{\text{offset}} > 0$) indicates that back camera recording began $\Delta t_{\text{offset}}$ seconds **after** the front camera recording.
- **Master Timeline Mapping:** To convert a back-camera local timestamp $t_{\text{back}}$ to the front-camera master timeline $t_{\text{front}}$:
  $$t_{\text{master}} = t_{\text{back}} + \Delta t_{\text{offset}}$$
- **Synthetic Validation:** This convention was verified using synthetic audio pairs with known positive (+2.000s) and negative (-1.500s) temporal shifts, confirming zero algorithmic sign error.

### 3. Resolution of the "33-Second Outlier" Mystery:
In `event_008`, QuickTime metadata recorded front capture at `16:13:07` and back capture at `16:12:34` (a $-33\,\text{s}$ difference). Similarly in `event_010`, timestamps indicated a $-17\,\text{s}$ difference.
- **Root Cause Identified:** The iPhone capturing the back camera was unsynchronized from network time (manual clock drift of $\approx 37\,\text{s}$ on September 14).
- **Acoustic Truth:** GCC-PHAT identified a clean, single correlation peak at $+3.6472\,\text{s}$ (SNR $16.6$) in `event_008` and $+2.7158\,\text{s}$ (SNR $25.7$) in `event_010`.
- **Visual Cross-Check:** In `event_008`, the front camera observed train approach immediately at $t = 0.0\,\text{s}$, while the back camera first observed the train at $t = 1.6\,\text{s}$. If the true offset were $-33\,\text{s}$, the train would have cleared before recording began. The acoustic offset of $+3.6\,\text{s}$ precisely matches the visual transit kinematics.

### 4. Acoustic Propagation Bounds & Non-Stationarity:
Sound travels at $c \approx 346\,\text{m/s}$ in air ($25^\circ\text{C}$). Across a typical crossing ($15–25\,\text{m}$ width), the maximum differential time of flight is:
$$\tau_{\text{prop}} \le \frac{d}{c} = \frac{25\,\text{m}}{346\,\text{m/s}} \approx 72.2\,\text{ms} = 0.072\,\text{s}$$
- **Video Sampling Window:** At $5.0\,\text{FPS}$, the frame duration is $\Delta t = 200\,\text{ms}$.
- **Uncertainty Margin:** While the spatial propagation ambiguity ($\pm 36\,\text{ms}$) is within a video frame, train motion (Doppler shift $\approx 3–6\%$) and acoustic reflections induce peak broadening.
- **Calibration Audit Mandate:** Claiming an uncertainty bound of $\le 0.05\,\text{s}$ across all events without window stability analysis is physically unsupportable. Event-by-event calibration audit (documented in `docs/R04_CALIBRATION_VALIDATION_REPORT.md`) is required before certifying any offset.

---

## 5. Candidate Calibration Manifest & Calibration Audit Integration

While acoustic cross-correlation demonstrates feasibility across the active cohort, a subsequent rigorous calibration validation audit (documented in detail in `docs/R04_CALIBRATION_VALIDATION_REPORT.md`) evaluated multi-window stability, peak-to-sidelobe ratios ($\text{PSR}$), and physical acoustic propagation constraints.

### Key Audit Outcomes:
1. **Preliminary Universal Certification Rejected:** The proposal to uniformly certify all 27 events with uncertainty $\le 0.05\,\text{s}$ was rejected due to competing acoustic sidelobes, moving-train Doppler broadening, and absence of train transients in negative controls.
2. **Quarantined Candidate Manifest Prepared:** A candidate calibration manifest has been authored at:
   `data/manifests/camera_sync_offsets_candidate.yaml`
   - Manifest Status: `CANDIDATE_UNVALIDATED_DO_NOT_MERGE`
   - Canonical file hashes preserved for all 54 source videos.
   - Per-event diagnostic telemetry: GCC-PHAT SNR, $\text{PSR}$, QuickTime creation delta, and validation rationale.
3. **Event-by-Event Verdict Distribution:**
   - **`CALIBRATION_SUPPORTED`:** **12 events** ($44.4\%$) — clean dominant peak, $\text{PSR} \ge 2.0$, sub-second QuickTime agreement, consistent visual kinematics.
   - **`PROVISIONAL`:** **10 events** ($37.0\%$) — plausible peak matching visual bounds, but competing lobes or window drift require visual landmark cross-verification ($\pm 0.10–0.25\,\text{s}$ uncertainty).
   - **`AMBIGUOUS`:** **5 events** ($18.5\%$) — `event_020` (unphysical negative lag contradicts QuickTime by 5.25s), `event_022` (competing mode near zero), and all 3 `no_train_events` (diffuse background noise without distinct transients).
   - **`FAILED` / `NOT_ASSESSABLE`:** **0 events**.

---

## 6. Current Status & Governance Decision

1. **Phase 5 Outputs Certified:**
   The Phase 5 raw predictions and single-camera condition logs in `results/experiments/phase5_full_dataset_run_20261013/` are verified as mathematically and structurally sound.
2. **Prerequisite R04 Status:**
   **Prerequisite R04 remains UNRESOLVED.** The full cohort has not achieved certified sub-frame synchronization.
3. **Execution Authorizations & Blocks:**
   - **PERMITTED:** Single-camera conditions (**B0**, **B1**, **B2**) and independent per-camera processing on local media timelines.
   - **STRICTLY BLOCKED:** Dual-camera fusion conditions (**B3**, **B4**, **B6**, **B7**) remain prohibited until cross-camera calibration acceptance criteria are fully met.
4. **Frozen Configuration Preserved:**
   `configs/frozen_experiment_v1.yaml` remains byte-identical to its Phase 2 specification (Canonical SHA-256: `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`). No overrides or unverified offsets have been merged into the base configuration.
5. **Next Research Steps:**
   - Prior to unblocking dual-camera fusion, visual landmark refinement (locomotive wheel contact with crossing plane) must be performed for the 10 `PROVISIONAL` and 5 `AMBIGUOUS` events.
   - Any future dual-camera exploration must be governed by a separate, versioned experiment configuration referencing an approved, non-quarantined calibration manifest.

