# Experiment Plan

**Status:** Working document — defines experiments, their design, and their dependencies.

**Last updated:** 2026-08-10

> **Protocol status (2026-08-13):** This historical experiment outline is superseded for system-level work by [`EXPERIMENT_PROTOCOL_V2.md`](EXPERIMENT_PROTOCOL_V2.md) and [`RESEARCH_PROTOCOL_V2.md`](RESEARCH_PROTOCOL_V2.md). Do not run its original experiments as a basis for multimodal/state-policy claims until reconciled with the synchronized Layer B protocol.

---

## 1. Experiment Philosophy

Experiments are designed to answer specific research questions, not to generate large tables of numbers. Each experiment should have:

- A **clear hypothesis** being tested
- A **control/baseline** for comparison
- **Defined metrics** for evaluation
- **Known limitations** acknowledged in advance

**Priority order:**
1. Can we reliably detect trains approaching and departing?
2. Does adding modalities improve reliability?
3. Does the safety-oriented simulated decision policy change event-level outcomes under the revised protocol?
4. How does the system degrade under failure conditions?

---

## 2. Experiment Dependency Graph

```
Phase 1: Dataset Preparation
  └── D-EXP-1: Dataset audit and deduplication
  └── D-EXP-2: Location-based split generation

Phase 2: Baseline Vision
  └── V-EXP-1: Single-view YOLO (front-only) baseline
  └── V-EXP-2: Multi-view YOLO (front+side+rear) baseline

Phase 3: Multimodal
  └── A-EXP-1: Audio horn detection baseline
  └── M-EXP-1: Vision + Audio fusion baseline

Phase 4: Decision Engine
  └── DE-EXP-1: State machine correctness
  └── DE-EXP-2: Failure injection analysis
  └── DE-EXP-3: Fusion method comparison

Phase 5: Robustness
  └── R-EXP-1: Weather condition degradation
  └── R-EXP-2: Audio noise stress testing
  └── R-EXP-3: False positive/false negative analysis
```

---

## 3. Phase 1: Dataset Preparation

### D-EXP-1: Dataset Audit and Deduplication

**Research question:** What is the actual size and composition of the current dataset?

**Method:**
1. Scan all image directories.
2. Compute perceptual hashes (pHash/dHash) for all images.
3. Identify near-duplicates (same frame from same video, different filename).
4. Generate a deduplicated dataset report.

**Output:**
- Exact count of unique images per class
- List of duplicate clusters
- Weather/time-of-day distribution
- Crossing-level distribution (if metadata available)

**Dependencies:** Current data folders must be accessible.

**Status:** Not started.

---

### D-EXP-2: Location-Based Split Generation

**Research question:** Can we create a valid location-aware train/val/test split?

**Method:**
1. Map each image to its crossing location (from filename or metadata).
2. Count images per crossing.
3. Assign crossings to train (70-80%), validation (10%), test (10-20%).
4. Verify that no crossing appears in more than one split.
5. Verify that class distribution is reasonably balanced across splits.

**Output:**
- Split assignment file (CSV/JSON)
- Per-split class distribution statistics
- Number of unique crossings per split

**Dependencies:** D-EXP-1 completed (need deduplicated image list).

**Status:** Not started.

---

## 4. Phase 2: Baseline Vision Experiments

### V-EXP-1: Single-View YOLO Baseline (Front-Only)

**Research question:** What is the baseline performance of a standard single-view train detector on this dataset?

**Hypothesis:** A standard object detector trained on a single "train" class (or front-only) will achieve reasonable detection but will fail to distinguish approach vs. departure.

**Design:**
- Train a YOLOv8 model on front-view images only.
- Use location-based train/val/test split.
- Report standard detection metrics.

**Hyperparameters (initial):**

| Parameter | Value |
|-----------|-------|
| Model | YOLOv8n or YOLOv8s |
| Image size | 640 |
| Epochs | TBD based on convergence |
| Batch size | TBD based on hardware |
| Optimizer | AdamW (default) |
| Augmentation | mosaic, hsv, flip |

**Metrics:**
- mAP@50, mAP@50:95
- Per-class precision, recall, F1

**Dependencies:** D-EXP-2 completed.

**Status:** Not started.

---

### V-EXP-2: Multi-View YOLO Baseline (Front+Side+Rear)

**Research question:** Does a three-viewpoint detector improve over a single-class "train" detector, and can it reliably distinguish approach vs. departure viewpoints?

**Hypothesis:** A three-class detector (front/side/rear) will provide viewpoint information that a single-class detector cannot, enabling the decision engine to distinguish approach from departure. However, inter-class confusion (especially front vs. side, side vs. rear) may introduce label noise.

**Design:**
- Train a YOLOv8 model on all three classes.
- Use location-based split.
- Report per-class metrics with confusion matrix.
- Compare against V-EXP-1.

**Additional analysis:**
- Confusion matrix: which classes are most confused?
- Per-viewpoint recall degradation under weather conditions
- False positive analysis: what is the detector mistaking for trains?

**Dependencies:** V-EXP-1 completed (for comparison).

**Status:** Not started.

---

## 5. Phase 3: Multimodal Experiments

### A-EXP-1: Audio Horn Detection Baseline

**Research question:** Can a train horn be reliably detected in real-world railway crossing audio?

**Hypothesis:** A spectrogram-based CNN classifier trained on diverse horn recordings will achieve acceptable accuracy on clean recordings but will degrade under realistic noise.

**Design:**
- Convert audio clips to mel-spectrograms or MFCCs.
- Train a binary classifier (train horn vs. non-train sound).
- Evaluate on held-out test set.
- Report standard classification metrics.

**Model candidates:**
- CNN on mel-spectrograms (baseline)
- Pre-trained audio model fine-tuned (e.g., YAMNet, VGGish — if justified)
- Simple SVM on MFCC features (transparent baseline)

**Dependencies:** Audio dataset collected and labeled.

**Status:** Not started.

---

### M-EXP-1: Vision + Audio Fusion Baseline

**Research question:** Does adding audio evidence to vision evidence improve overall detection reliability?

**Hypothesis:** Audio will improve recall when vision is uncertain (night, fog, occlusion), but may increase false positives if not carefully fused.

**Design:**
1. Run vision and audio models independently on test data.
2. Implement a simple fusion rule (e.g., confidence-weighted OR).
3. Compare against vision-only baseline (V-EXP-2).
4. Measure changes in both recall and false-positive rate.

**Fusion methods to test (from simplest to more complex):**
1. Simple OR (vision OR audio → train present)
2. Confidence-weighted average
3. State-dependent weighting (e.g., audio weight increases when vision confidence is low)

**Analysis:**
- Where does audio help? (night, fog, occlusion cases)
- Where does audio hurt? (false horn detections in noisy environments)
- Per-sample analysis: cases where vision failed but audio succeeded, and vice versa

**Dependencies:** V-EXP-2 and A-EXP-1 completed.

**Status:** Not started.

---

## 6. Phase 4: Decision Engine Experiments

### DE-EXP-1: State Machine Correctness

**Research question:** Does the state-machine decision engine produce correct state transitions under normal (no-failure) conditions?

**Design:**
1. Create test sequences from real video data with known ground-truth state labels (approach, occupying, departure).
2. Feed frame-level detections through the decision engine.
3. Compare engine state transitions against ground truth.
4. Measure state-transition accuracy and latency.

**Metric:**
- State-transition correctness rate
- Time delay between ground-truth event and system state change
- False state transitions

**Dependencies:** V-EXP-2 completed (need reliable detector outputs).

**Status:** Not started.

---

### DE-EXP-2: Failure Injection Analysis

**Research question:** How does the system behave when individual components fail?

**Design:**
For each failure scenario, measure whether the system reaches the correct safe state:

| Failure Scenario | Expected Safe Behavior |
|-----------------|----------------------|
| Front detection disabled | Use side + audio to close gate |
| Side detection disabled | Maintain state from front/rear evidence |
| Rear detection disabled | Do not open gate without positive departure evidence |
| Audio disabled | Vision-only should still function |
| Camera 1 obstructed | Rely on Camera 2 + audio |
| Camera 2 obstructed | Rely on Camera 1 + audio |
| False positive injection | System should not open gate on false detection |
| Audio noise injection | Vision should maintain correct state |
| Temporary camera failure | State should persist through brief outages |

**Dependencies:** DE-EXP-1 completed.

**Status:** Not started.

---

### DE-EXP-3: Fusion Method Comparison

**Research question:** Which fusion method provides the best safety-reliability tradeoff?

**Design:**
Compare multiple fusion approaches on the same test sequences:

1. Naive OR
2. Weighted average (confidence-based)
3. Temporal consistency filter
4. State-dependent thresholds
5. (Optional) Learned fusion if justified

**Metrics:**
- False negative rate (safety-critical)
- False positive rate
- Decision latency
- Sensitivity to individual detector confidence calibration

**Dependencies:** DE-EXP-1 and M-EXP-1 completed.

**Status:** Not started.

---

## 7. Phase 5: Robustness Experiments

### R-EXP-1: Weather Condition Degradation

**Research question:** How does model performance degrade under adverse weather conditions?

**Design:**
1. Partition the test set by condition: clear day, night, rain, fog.
2. Evaluate V-EXP-2 model on each partition separately.
3. Report per-condition metrics.
4. Compare degradation patterns across viewpoint classes.

**Analysis:**
- Which viewpoint is most affected by rain/fog/night?
- Does the degradation justify synthetic augmentation?

**⚠️ Limitation:** If adverse-weather test samples are few, confidence intervals will be wide. Report uncertainty.

**Dependencies:** V-EXP-2 completed.

**Status:** Not started.

---

### R-EXP-2: Audio Noise Stress Testing

**Research question:** At what noise level does the audio fallback become unreliable?

**Design:**
1. Mix clean horn test clips with background noise at defined SNRs.
2. Evaluate A-EXP-1 model at each SNR level.
3. Plot accuracy vs. SNR curve.
4. Identify the SNR threshold where performance drops below acceptable level.

**SNR levels to test (proposed):**

| SNR | Condition |
|-----|-----------|
| Clean | No added noise |
| +10 dB | Mild noise |
| +5 dB | Moderate noise |
| 0 dB | Equal signal and noise |
| -5 dB | Severe noise |
| -10 dB | Extreme noise |

**Background noise sources (proposed):**
- Traffic noise
- Crowd noise
- Rain
- Wind
- Combined urban ambient

**Dependencies:** A-EXP-1 completed.

**Status:** Not started.

---

### R-EXP-3: False Positive / False Negative Tradeoff Analysis

**Research question:** What is the empirical tradeoff between false positives and false negatives for the full system?

**Design:**
1. Sweep decision thresholds across a range.
2. Measure false positive rate and false negative rate at each threshold.
3. Plot the tradeoff curve.
4. Identify the operating point that minimizes false negatives while keeping false positives below a defined threshold.
5. Compare tradeoff curves across: vision-only, audio-only, vision+audio, full system.

**Analysis:**
- How much does the multimodal system shift the tradeoff curve compared to vision-only?
- Is there a threshold where false negatives approach zero? At what false-positive cost?

**Dependencies:** DE-EXP-3 completed.

**Status:** Not started.

---

## 8. Ablation Studies

### AB-1: Viewpoint Ablation

**Research question:** What is the contribution of each viewpoint class?

Remove one viewpoint at a time and measure system impact:
- Without front: How much later is approach detected?
- Without side: Does the system lose track during passage?
- Without rear: Can the system still confirm departure?

**Dependencies:** V-EXP-2 and DE-EXP-1 completed.

---

### AB-2: Modality Ablation

**Research question:** What is the marginal contribution of each modality?

Compare:
- Vision only
- Audio only
- Vision + Audio
- Full system (vision + audio + state machine)

**Dependencies:** M-EXP-1 and DE-EXP-1 completed.

---

## 9. Experiment Execution Notes

### Reproducibility Requirements

For every experiment, record:
- Random seed(s)
- Software versions (Python, PyTorch, YOLO, libraries)
- Hardware (GPU model, CPU, RAM)
- Dataset version (commit hash or version tag)
- Exact train/val/test split used
- All hyperparameters
- Training duration

### Reporting Standards

- Report mean and standard deviation across multiple seeds where applicable
- Include confidence intervals for key metrics
- Do not cherry-pick the best seed — report the protocol for selecting the reported run
- For small test subsets (e.g., fog images), explicitly note the sample size

### What NOT to Do

- Do not tune hyperparameters on the test set
- Do not use test-set performance to guide model selection (use validation set)
- Do not report only the best-performing configuration without noting the selection method
- Do not omit negative results — they are valuable for the research narrative

---

*This plan is a living document. Update it as experiments are designed, executed, and results are obtained.*
