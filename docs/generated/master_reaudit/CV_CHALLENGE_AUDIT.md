# MISSION 16A-CV-CHALLENGE — Independent Computer Vision Audit

**Date:** 2026-11-03  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Role:** Independent CV/ML/Dataset Auditor (read-only)  
**HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Disposition:** `CV_AUDIT_PARTIALLY_VERIFIED`

## 1. Executive verdict

The CV architecture and safety integration are source-verified, but the historical 99.46% mAP result is only a static image-development metric from a split explicitly marked `development_fallback` and `leakage_risk: true`. It cannot establish event-level detection, clearance, latency, robustness, or safety performance.

The labels `front`, `rear`, and `side` are detector appearance labels, not validated travel-direction labels. Frozen rules accept `side` as both approach and departure evidence. A candidate policy recognizes this ambiguity but is not the frozen policy.

No protected images/video, checkpoints, production caches, or processed media were accessed. No inference, training, replay, evaluation, or prediction was executed.

## 2. Scope and safety declaration

Inspected source/configuration/text metadata only:

- `configs/vision.yaml`, `configs/frozen_experiment_v1.yaml`, `configs/decision_policy_v1.yaml`, `configs/fusion.yaml`
- `src/railway_detection/vision/{adapter.py,yolo_adapter.py,video.py,trainer.py,evaluator.py,temporal.py,failure_analysis.py}`
- `src/railway_detection/fusion/{rules.py,collector.py,decision_engine.py}`
- `src/railway_detection/experiments/layer_b_processor.py`
- historical manifests, args, metrics, split summaries and failure reports
- Mission 16A CV, dataset, metric, historical and manuscript reports

No media-suffix file was opened. No checkpoint was loaded or hashed. No state-changing Git command was used.

## 3. Exact model architecture and configuration

### 3.1 Model selection

| Item | Evidence | Status |
|---|---|---|
| Detector family | `frozen_experiment_v1.yaml:13-20` | YOLOv8n, source/config verified |
| Training initialization | `args.yaml:3,18` | `yolov8n.pt`, `pretrained: true` |
| Fine-tuning | `yolo_adapter.py:83-129` | `YOLO(model).train(...)`, verified |
| Input size | frozen config `image_size: [640,640]` | Configuration verified |
| Nominal sampling | frozen config `sampling_fps: 5.0` | Configuration verified |
| Runtime confidence | `layer_b_processor.py:271-273` | 5 FPS, confidence 0.35 |
| NMS/IoU | adapter accepts `iou`; historical args IoU 0.7 | No single frozen inference IoU established |
| Frozen checkpoint | `frozen_experiment_v1.yaml:14-15` | Path/hash declared only; bytes not verified |

The adapter converts Ultralytics boxes into normalized `Detection` records (`yolo_adapter.py:161-190`) and never makes gate decisions. Checkpoint/framework internals were not loaded.

### 3.2 Training configuration

`configs/vision.yaml:19-25` declares 100 epochs, batch 16, seed 42, MPS, optimizer auto and `yolov8n.pt`. Historical `args.yaml:5-18,39-43` confirms pretrained initialization, MPS, 640 input, 100 epochs and validation split. This is pretrained YOLOv8n fine-tuning, not training from scratch.

## 4. Class-definition audit

- `configs/vision.yaml:8-11`: `front: 0`, `rear: 1`, `side: 2`.
- `frozen_experiment_v1.yaml:17-20`: same mapping.
- `yolo_adapter.py:64-68`: generated descriptor preserves mapping.

These are mutually exclusive detector labels describing visible train-part appearance. No source evidence proves that one label establishes physical travel direction.

`fusion/rules.py:58-81` defines `APPROACH_LABELS = {front, side, train}` and `DEPARTURE_LABELS = {rear, side, train}`. Thus `side` and `train` are accepted for both directions. `configs/decision_policy_v2_candidate.yaml:14-32` calls `front` unambiguous approach, `rear` unambiguous departure and `side/train` ambiguous, but that file is candidate/not authorized (`lines 4-12`).

**CV-01 — HIGH:** Frozen class semantics do not support reliable direction inference from labels alone. Direction requires source/camera role, temporal context and protocol-grounded evidence.

## 5. 99.46% mAP provenance audit

`experiments/vision/39f402dfe460/evaluation/metrics.json` declares `map50: 0.9946`, `map50_95: 0.855`, IoU threshold 0.5, confidence threshold 0.5, 487 GT boxes, 574 predictions, 480 TP, 94 FP and 7 FN. `metrics.md:1-18` repeats those values. `vision/evaluator.py:204-265` computes box-level mAP50 and mAP50:95.

| Question | Result |
|---|---|
| Exact metric | `VERIFIED_IMPLEMENTATION`: mAP50 and mAP50:95 |
| Image/object counts | `HISTORICAL_REPORT_ONLY`: 487 GT, 480 TP, 94 FP, 7 FN |
| Dataset sessions/events | `NOT_ASSESSED` by metric artifact |
| Event-level split independence | `NOT_ASSESSED` |
| Crossing-level detection/latency/clearance | `NOT_ASSESSED` |
| Railway safety performance | `NOT_ASSESSED` |

This static bounding-box result cannot establish event-level arrival detection, T1/T4 correctness, gate timing or safety.

**CV-02 — HIGH:** The metric must not be used as generalization or operational-safety evidence.
## 6. Dataset and leakage assessment

`data/splits/705d388743ea/split_summary.json:2-13` explicitly declares `split_type: development_fallback`, `leakage_risk: true` and `allow_ungrouped_fallback: true`. `run_manifest.json:57-59` also records fallback enabled. Current config requests grouping (`vision.yaml:33-40`), but the historical artifact was generated under fallback conditions.

`data/split.py:65-156` correctly implements group-aware splitting and fails when required grouping is missing unless fallback is explicitly enabled. `trainer.py:3-6,88-103` records split/config provenance. These safeguards do not prove the historical metric used a leakage-safe split.

The permitted metadata supports a single crossing, two sessions and a Layer B cohort of 23 train/3 no-train/1 engine events, but does not establish that the Layer A split was event/session independent. **CV-03 — MEDIUM:** Duplicate/near-duplicate, session independence and weather/lighting strata are not independently established for the reported mAP artifact.

## 7. Detection-to-state-machine integration

```text
video → frame_generator() → run_vision_inference()
→ Detection(label, confidence, bbox)
→ EvidenceRecord(timestamp_s, source_id, modality=VISION)
→ MultimodalEvidenceCollector
→ MultimodalFrame.vision_records
→ MultimodalDecisionEngine.evaluate_frame()
→ has_qualified_approach/departure()
→ state transition
```

`layer_b_processor.py:266-370` confirms target FPS 5.0, confidence 0.35, cache provenance checks, authorization before inference, frame timestamp propagation and normalized detections.

- `rules.py:63-81`: labels plus confidence ≥0.35 qualify approach/departure.
- `decision_engine.py:388-430`: two confirmation frames precede WARNING/GATE_CLOSING.
- `decision_engine.py:432-451`: departure evidence transitions toward TRAIN_DEPARTING/REAR_CONFIRMED.
- `decision_engine.py:476-504`: stale/missing departure vision aborts clearance; audio cannot clear.
- `decision_engine.py:534-590`: vision failure clamps or holds closed.

## 8. Cadence and temporal limitations

| Concept | Value | Evidence |
|---|---|---|
| Frozen vision sampling | 5 FPS / 0.2 s | `frozen_experiment_v1.yaml:48,54` |
| Policy simulation tick | 10 Hz / 0.1 s | `decision_policy_v1.yaml:25` |
| Frame extraction | `target_fps` or integer stride | `vision/video.py:41-68` |
| Layer-B inference default | target_fps 5.0 | `layer_b_processor.py:271` |
| Timestamp | frame index / native FPS | `vision/video.py:32-38,98-110` |

Native FPS is read from media by `video.py:98-100`, but this audit did not access media and found no permitted metadata establishing one native FPS for all recordings. The 5 Hz target is a sampling rate, not a native camera-rate claim.

Sampling at 5 Hz can miss transients shorter than the sample interval and adds up to one sampling interval before an observation is available. No measured latency was inferred. **CV-04 — MEDIUM:** Native frame rate, inference latency and short-event miss behavior are not empirically established.

## 9. Model provenance matrix

### 9.1 Model provenance matrix

| Item | Evidence | Status |
|---|---|---|
| YOLOv8n family | frozen config/args | `VERIFIED_CONFIGURATION` |
| Pretrained initialization | args.yaml `pretrained: true` | `CONFIGURATION_DECLARED` |
| Training seed 42 | config/args | `CONFIGURATION_DECLARED` |
| MPS device | args/manifest | `HISTORICAL_REPORT_ONLY` |
| 640 input | config/args | `VERIFIED_CONFIGURATION` |
| Checkpoint path | frozen config line 14 | `CONFIGURATION_DECLARED` |
| Checkpoint SHA-256 | frozen config line 15 | `CONFIGURATION_DECLARED`; not independently hashed |
| Selection criterion | adapter protocol says validation-only; args split val | `SOURCE_VERIFIED` design / historical execution not independently proven |
| Dataset manifest | split/run metadata | `REPORT_ONLY` |
| Actual checkpoint identity | checkpoint not accessed | `UNVERIFIED` |

### 9.2 Robustness and domain shift

No permitted evidence establishes night, rain, fog, glare, motion-blur, vibration, occlusion or long-distance robustness. Historical failure metadata records categories but not representative environmental strata. `failure_analysis.py:221-245` records metadata slices only when keys exist and otherwise records `unknown`.

**CV-05 — MEDIUM:** Robustness claims are documented risk assessments, not validated performance.

## 10. Failure-mode register

| Failure mode | Evidence | Classification |
|---|---|---|
| Missed front | historical failure report: 6 | `HISTORICAL_REPORT_ONLY` |
| False train detection | historical failure report: 9 | `HISTORICAL_REPORT_ONLY` |
| Low-confidence detection | historical failure report: 18 | `HISTORICAL_REPORT_ONLY` |
| Front/side confusion | historical failure report: 1 | `HISTORICAL_REPORT_ONLY` |
| Rear/side confusion | historical report count 0 | `HISTORICAL_REPORT_ONLY` |
| Frame dropout/stale source | decision-engine fail-safe branches | `VERIFIED_IMPLEMENTATION` |
| Two-miss tolerance | frozen config and decision logic | `VERIFIED_CONFIGURATION` / `SYNTHETIC_TEST_ONLY` |
| Temporal EMA/persistence | optional temporal buffer | `VERIFIED_IMPLEMENTATION`, not universal production-path proof |
| Night/rain/fog | no permitted empirical strata | `NOT_ASSESSED` |
| Event-level missed arrival | no approved Layer B GT | `NOT_ASSESSED` |

## 11. Scientific validity and publication claims

- The detector is an off-the-shelf YOLOv8n baseline fine-tuned to three appearance classes, not an architectural research contribution.
- The 99.46% mAP50/85.50% mAP50:95 values are Layer A static image/object metrics only.
- The historical split is explicitly development-fallback and leakage-risk flagged.
- No evidence supports event-level detection, warning latency, clearance correctness, cross-site generalization, weather robustness or safety certification.
- Dataset reports zero approved Stage-2.1 ground truth and zero evaluable official cohort; Layer B empirical claims remain unsupported.
- Novelty/literature comparison was **NOT ASSESSED**; no external literature was verified.

**CV-06 — HIGH:** Publication must label detector metrics as historical Layer A static-image diagnostics and must not present them as crossing-level safety or generalization evidence.

## 12. Contradiction register

| Comparison | Finding | Severity |
|---|---|---|
| 99.46% metric vs split metadata | Metric exists but split is `development_fallback` with `leakage_risk: true` | HIGH |
| Frozen config vs policy tick | 0.2 s evaluation config vs 0.1 s policy simulation; contexts differ but documentation is ambiguous | MEDIUM |
| Frozen classes vs candidate policy | Frozen `side` is both approach/departure; candidate calls side/train ambiguous and is unauthorized | HIGH |
| 27-event corpus vs vision metric | 487 image objects are Layer A, not event outcomes | HIGH |
| Historical reports vs dataset audit | Zero approved/evaluable Layer B cohort | HIGH |
| Native FPS/30+ FPS claims vs source | No permitted metadata establishes all-camera native FPS or runtime benchmark | MEDIUM |
| Robustness claims vs coverage | No evidence supports all-weather/night robustness | MEDIUM |

## 13. Researcher decisions required

1. Decide whether the historical development-fallback metric is suitable for any claim beyond a qualified Layer A diagnostic baseline.
2. Decide whether the frozen 0.2 s evaluation tick and 0.1 s policy simulation tick are intentional and document their separate authority.
3. Decide whether `front/rear/side` classes are sufficient or directional semantics require a formally adopted candidate policy.
4. Require approved event-level ground truth before any Layer B vision performance claim.
5. Require event/session/site-disjoint splits before generalization claims.
6. Require independent night/weather/occlusion/distance strata before robustness claims.

## 14. Prioritized corrective recommendations

1. **HIGH:** Retain 99.46% only as historical Layer A static-image evidence and state the development-fallback/leakage-risk caveat.
2. **HIGH:** Prohibit conversion of class labels into travel-direction claims without source/camera/time evidence and adopted policy.
3. **HIGH:** Keep all Layer B detection, latency, clearance and safety results pending approved Stage-2.1 ground truth and authorization.
4. **MEDIUM:** Reconcile or document the dual-rate contexts.
5. **MEDIUM:** Establish event/session/site-disjoint evaluation metadata before generalization claims.
6. **MEDIUM:** Add independent robustness strata for night, rain, glare, occlusion, blur and distance if authorized.
7. **LOW:** Correct historical documentation that treats detector mAP as broader system performance.

## 15. Explicit no-access and stop statement

No protected images, video, model checkpoints or production caches were accessed. No inference, training, replay, benchmarking or evaluation was executed. No source/configuration/test/dataset/manuscript file was modified. No authorization, review record, receipt or annotation was created. No Git write command was executed.

Git HEAD remains `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`; no staged files were observed. This audit stops here and does not advance Mission 16 or authorize real-data execution.

## 16. Final disposition

**`CV_AUDIT_PARTIALLY_VERIFIED`**

Architecture, configuration wiring, temporal safety logic and historical metric artifact provenance are partially verified from permitted text evidence. Real-world CV performance, leakage-safe generalization, robustness, event-level timing and checkpoint identity remain unverified or unsupported.

This audit stops here. It does not advance Mission 16 or authorize real-data execution.


