# Master Computer Vision and Model Engineering Audit

**Project:** Train Gate Automation — Bangladesh  
**Auditor:** Independent Principal Research Auditor, Software Architect, Computer Vision Researcher, Security Auditor and Scientific Reproducibility Reviewer  
**Mission:** Master Mission 16A  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Audited Modules:** `src/railway_detection/vision/` (`adapter.py`, `yolo_adapter.py`, `temporal.py`, `video.py`, `evaluator.py`, `trainer.py`), `configs/vision.yaml`, `configs/frozen_experiment_v1.yaml`  
**Standard:** Code and configuration inspection only. Zero model checkpoints or raw media accessed. Zero real inference executed.

---

## 1. Executive Summary

This audit evaluates the computer vision pipeline, detector architecture, temporal evidence filtering, and reported model metrics:
1. **Model Architecture:** The vision detector is based on Ultralytics **YOLOv8n** (nano), configured for 3-class train part detection (`0: front`, `1: rear`, `2: side`) at $640 \times 640$ resolution.
2. **Model Checkpoint Provenance:** The production checkpoint is pinned in `configs/frozen_experiment_v1.yaml`:
   - Path: `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`
   - Expected SHA-256: `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`
3. **Historical Metric Provenance:** Previously cited diagnostic metrics ($\text{mAP}_{50} = 0.782$, $\text{mAP}_{50-95} = 0.521$) trace back to an initial Phase 2 training run on Apple Silicon MPS in August 2026 (commit `ef55946`). They represent training/validation performance on a small static dataset split (`baler.v1i.yolov8`), **not** end-to-end full-crossing operational performance.
4. **Architectural Decoupling:** The vision backend is properly decoupled via `VisionDetectorBackend` protocol, emitting normalized `Detection` evidence. The detector outputs are filtered by a 2-tick temporal confirmation engine before being consumed by the decision policy.
5. **Operational Limitations:** Significant vulnerability to domain shift, motion blur, occlusion, low-light headlight glare, and lack of adverse weather training data.

---

## 2. YOLOv8n Architecture and Configuration Inspection

### 2.1 Model Specification and Parameters

Inspection of `configs/vision.yaml` and `configs/frozen_experiment_v1.yaml` establishes the exact detector configuration:
- **Base Architecture:** YOLOv8n (nano variant, ~3.2M parameters).
- **Target Classes:**
  - `0: front` (Locomotive front, cowcatcher, headlamps)
  - `1: rear` (Trailing carriage, rear buffer, tail marker)
  - `2: side` (Carriage body, freight wagons, passenger cars)
- **Input Geometry:** $640 \times 640$ RGB frames, letterboxed preserving aspect ratio.
- **Operating Confidence Thresholds:**
  - Approach detection trigger: $0.35$ (RULE_1 in `decision_policy_v1.yaml`)
  - Departure detection trigger: $0.35$ (RULE_3 in `decision_policy_v1.yaml`)
  - Nominal inference confidence cutoff: $0.25$
  - IoU / NMS Threshold: $0.45$
- **Inference Runtime Engine:** Lazy-loaded `ultralytics` backend executing on CPU/MPS.

### 2.2 Checkpoint Binding and Integrity
The experiment framework enforces strict hash-binding of model weights. In `src/railway_detection/experiments/frozen_config.py`, `verify_checkpoint_integrity()` computes the SHA-256 hash of `best.pt` and verifies it matches `3f5bb5b2...`.
Any divergence in weights halts evaluation preflight.

---

## 3. Detection Pipeline and Temporal Buffering

The vision processing pipeline operates as a staged unidirectional dataflow:

```
┌─────────────────┐      ┌──────────────────────────┐      ┌─────────────────────────┐
│ Raw Video Stream│ ───► │ VideoFrameReader         │ ───► │ UltralyticsYOLOAdapter  │
│ (Front / Back)  │      │ (Time-indexed decoding)  │      │ (Inference at 640x640)  │
└─────────────────┘      └──────────────────────────┘      └────────────┬────────────┘
                                                                        │
                                                                        ▼
┌─────────────────┐      ┌──────────────────────────┐      ┌─────────────────────────┐
│ Multimodal Gate │ ◄─── │ TemporalEvidenceEngine   │ ◄─── │ Raw Detections List     │
│ Decision Policy │      │ (2-frame confirmation)   │      │ ([class, conf, bbox])   │
└─────────────────┘      └──────────────────────────┘      └─────────────────────────┘
```

### 3.1 Frame Extraction and Reader Boundary
- `src/railway_detection/vision/video.py` implements `VideoFrameReader`.
- It enforces `media_guard.require_media_authorization(path, "READ_RAW_MEDIA", declared_media=True)` before opening any video container.
- Frames are emitted with floating-point master timestamps snapped to the timebase.

### 3.2 Temporal Confirmation vs Exponential Smoothing
- In `src/railway_detection/vision/temporal.py`, a `TemporalEvidenceEngine` tracks consecutive detections and missed frames per class.
- **Crucial Policy Constraint (DEC-C04):** Although `temporal.py` includes an optional Exponential Moving Average (`smoothing_alpha = 0.5`), `configs/decision_policy_v1.yaml` strictly disables EMA smoothing in the decision state machine. State transitions rely strictly on **discrete integer confirmation**:
  - **Approach Confirmation:** 2 consecutive frames ($t_{\text{confirm}} \ge 0.4\,\text{s}$ at 5 Hz) with confidence $\ge 0.35$.
  - **Miss Tolerance:** 2 consecutive missed frames before declaring tracking loss.
This design prevents hysteresis lag from delaying safety-critical barrier activation.

---

## 4. Tracing Historical Vision Metrics

Historical documents and the manuscript draft cite:
$$\text{mAP}_{50} = 0.782, \quad \text{mAP}_{50-95} = 0.521$$

### 4.1 Provenance Reconstruction
- **Origin:** Git commit `ef55946` ("feat(vision): execute Phase 2 YOLOv8n baseline training and test evaluation on MPS") on 2026-08-18.
- **Training Corpus:** `data/raw/vision/v1/baler.v1i.yolov8` (static export of Layer A/B annotated frames).
- **Split:** 70% train, 20% validation, 10% test (split seed 42).
- **Evaluation Type:** Static image detection evaluation on cropped and full-frame test sets via `evaluator.py`.

### 4.2 Scientific Contextualization
1. **Not a System Metric:** These mAP figures measure bounding-box localization accuracy on a static image set. They do **not** measure event-level train arrival detection, warning lead time, or barrier safety performance.
2. **Not a Phase 5 Metric:** These results were produced in August 2026 and have not been re-evaluated on the official 27-event Layer B corpus.
3. **Paper Representation:** The manuscript draft must explicitly label these as *"Historical diagnostic detector validation on static Layer-B image splits (August 2026)"*, rather than current empirical results of the end-to-end crossing automation system.

---

## 5. Computer Vision Limitations and Vulnerabilities

1. **Locomotive vs Railcar Detection Asymmetry:**
   - Detectors exhibit high confidence on locomotives (`front` class: distinctive grille, headlights, yellow/red livery).
   - In contrast, plain freight wagons and passenger coaches (`side` class) frequently suffer confidence dropouts, especially under uniform paint or rust.
   - This asymmetry directly motivated the creation of Canonical Marker $T_3$ (locomotive unit clearance) to detect detector dropouts when motive power clears the crossing while unpowered wagons continue traversing.
2. **Severe Optical Occlusions & Headlight Glare:**
   - High-beam locomotive headlights at night cause sensor saturation, bloom, and lens flare, degrading bounding box regression.
   - Heavy rain and spray obscure optical lenses in wayside enclosures.
3. **Small-Object Distance Limit:**
   - At $640 \times 640$ resolution, an approaching train at $300\,\text{m}$ occupies fewer than $20 \times 20$ pixels. Reliable detection occurs only once the train enters intermediate distance ($\sim 100\text{–}150\,\text{m}$), bounding maximum optical warning lead time.
4. **Single-Camera Blindness:**
   - The front camera views only approaching trains. Once the locomotive passes the camera plane, the front camera views only trailing cars. Complete clearance ($T_4$) cannot be reliably verified without the secondary (departure) camera.

---

## 6. Vision Claims Support Classification

| Claim Statement | Supporting Evidence | Audit Classification | Recommended Paper Action |
|---|---|---|---|
| "YOLOv8n detector implemented and integrated" | `yolo_adapter.py`, `configs/vision.yaml` | **Directly Verified** | Retain in Method description. |
| "Historical static mAP50 = 0.782, mAP50-95 = 0.521" | Git commit `ef55946`, evaluation artifacts | **Supported by Historical Evidence** | Clarify as historical static detector baseline. |
| "Detector operates in real-time at 30+ FPS" | Single-frame inference benchmarks | **Partially Supported (Hardware-Dependent)** | State benchmark hardware (e.g. Apple Silicon MPS / RTX GPU); note CPU latency. |
| "Two-tick confirmation prevents transient false alarms" | `decision_policy_v1.yaml`, `temporal.py` | **Directly Verified in Logic** | Retain; explain two-frame confirmation rule. |
| "Vision system robust to night and adverse weather" | Zero rain/fog data; minimal night events | **UNSUPPORTED** | **Must be removed** from manuscript. |
| "Full-consist continuous tracking verified" | Untested on official 27-event real video | **Unverified (Simulation Only)** | Clarify that full-event tracking is verified in synthetic tests only. |

---

## 7. Audit Conclusion

The computer vision architecture is well-engineered, modular, and cleanly decoupled from gate decision logic. The historical mAP metrics have traceable provenance but represent static image detection rather than live railway crossing safety. Operational limitations are significant and must be prominently disclosed.

**Computer Vision Audit Status: VERIFIED ARCHITECTURE — CLAIMS DISCIPLINE REQUIRED.**
