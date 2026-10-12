# Research Concept

## Safety-Oriented Multimodal Railway Crossing Train Detection Research Framework for Bangladesh Using Computer Vision and Audio

**Status:** Working document — defines the research scope, architecture, assumptions, and open questions.

**Last updated:** 2026-08-10

> **Protocol status (2026-08-13):** This is a historical conceptual document. [`RESEARCH_PROTOCOL_V2.md`](RESEARCH_PROTOCOL_V2.md) supersedes its system-level claim, evaluation, synchronization, clearance-ground-truth, and terminology decisions. “Fail-safe” in retained historical text is not a physical-safety claim.

---

## 1. Research Problem

Railway level-crossings in Bangladesh present significant safety challenges. Many crossings still depend on human operators who must:

1. Recognize an approaching train.
2. Close the crossing gate in time.
3. Confirm the train has fully passed.
4. Reopen the gate.

This manual process is vulnerable to:

- Human error and delayed reaction
- Poor visibility (rain, fog, nighttime, occlusion)
- Camera detection failure (train front not clearly visible)
- Long trains (prolonged crossing occupation)
- Environmental noise and visual ambiguity
- False detections and missed detections

### Central Research Question

> Can a multi-view, audio-assisted, state-aware train-detection framework improve event-level crossing-detection outcomes under the synchronized, held-out recording protocol defined in `RESEARCH_PROTOCOL_V2.md`?

This question may be refined as the project evolves.

---

## 2. Research Goal

The goal is **not** simply to detect trains. The goal is to investigate whether a multi-view, audio-assisted, safety-oriented simulated decision architecture can provide more reliable evidence about three critical phases:

| Phase | Meaning | Required Decision |
|-------|---------|-------------------|
| **Approaching** | Train is approaching the crossing | Close the gate |
| **Occupying/Passing** | Train is at or passing through the crossing | Keep gate closed |
| **Departure** | Train has completely left the crossing | Open the gate |

---

## 3. Proposed Architecture

### 3.1 Overview

The system uses:

- **Two cameras** at different viewpoints
- **Computer vision** train detection (front/side/rear)
- **Audio** train horn detection
- A **state-based decision engine** that fuses evidence
- A **safety-oriented gate decision simulation**

### 3.2 Camera Configuration (Current Design Assumption)

| Camera | Position | Primary Role |
|--------|----------|-------------|
| Camera 1 | Approach side | Detect approaching train (front, side) |
| Camera 2 | Departure side | Monitor passage, confirm departure (side, rear) |

**Current assumption:** Cameras are positioned on opposite sides of the crossing, approximately 5–6 meters apart.

**⚠️ Assumption marker:** The 5–6 meter distance has not been scientifically validated. Optimal placement should be determined experimentally based on:
- Field of view
- Railway geometry and crossing layout
- Camera focal length and resolution
- Train approach distance
- Visibility and occlusion conditions

### 3.3 Evidence Flow

```
Camera 1 (Approach)           Camera 2 (Departure)          Microphone
      │                              │                         │
  Vision Evidence               Vision Evidence            Audio Evidence
  front / side                  side / rear               train horn confidence
      │                              │                         │
      └──────────────────────────────┼─────────────────────────┘
                                     │
                           ┌─────────▼─────────┐
                           │                   │
                           │  Decision Engine  │
                           │                   │
                           └─────────┬─────────┘
                                     │
                              Gate Decision
                              (Close / Keep Closed / Open)
```

The decision engine considers:

- Detection confidence per viewpoint
- Detected viewpoint type (front/side/rear)
- Temporal consistency of detections
- Current system state
- Camera source identity
- Audio horn confidence
- History of previous detections

**⚠️ Research question:** The exact mathematical fusion method is not finalized.

---

## 4. System States

The system conceptually operates through the following states:

| State | Description |
|-------|-------------|
| `IDLE` | No train detected; gate open |
| `TRAIN_APPROACHING` | Train detected approaching from Camera 1 direction |
| `WARNING` | Warning signal active |
| `GATE_CLOSING` | Gate closing in progress |
| `TRAIN_PRESENT` | Gate closed; train confirmed present at crossing |
| `CROSSING_OCCUPIED` | Train actively passing through crossing |
| `TRAIN_DEPARTING` | Rear of train detected; train is leaving |
| `REAR_CONFIRMED` | Rear visually confirmed by Camera 2 |
| `CROSSING_CLEAR` | Positive evidence that train has cleared the crossing |
| `GATE_OPENING` | Gate opening in progress |
| `FAULT / FAIL_SAFE` | Uncertainty detected; system defaults to safe state |

**Design principle:** The exact state machine may evolve during research.

---

## 5. Core Safety Principles

### Closing Principle (Aggressive toward safety)

If reliable evidence suggests a train is approaching, the system should move toward the safe **closed** state.

### Opening Principle (Conservative)

The system must **not** open the gate merely because the detector stops seeing a train. Loss of detection ≠ proof of departure. Opening requires **positive evidence**:

- Rear detection confirmed
- Temporal consistency (sustained rear detection)
- Crossing-clear condition simulated

If evidence becomes uncertain, the system should **prefer the safe state** (gate closed) rather than opening prematurely.

---

## 6. Vision Model

### 6.1 Viewpoint Classes

| Class | Definition |
|-------|-----------|
| **Front** | Leading locomotive/head/nose clearly visible facing the camera. Does not require perfectly straight-on view. If the locomotive front is identifiable even with some side visibility, classify as front. |
| **Side** | Train primarily viewed from the side. Neither the front nor rear end is dominantly identifiable. |
| **Rear** | Last coach/end of the train clearly visible facing the camera. |

### 6.2 Annotation Principle

Classify based on **which end/viewpoint is visually identifiable**, not based on pixel percentage or bounding box size.

**Examples discussed:**

- Long coach/body seen from side → **SIDE**
- Locomotive front/head clearly facing camera → **FRONT**
- Locomotive front visible with some side visible → **FRONT**
- Last coach/end facing camera → **REAR**

### 6.3 Ambiguous Cases

If ambiguous/oblique cases arise frequently, an internal metadata tag may be used, but a fourth detection class should **not** be created without experimental justification.

### 6.4 Viewpoint Roles in the Safety Workflow

| Viewpoint | Role |
|-----------|------|
| **Front** | Early approach detection |
| **Side** | Continued presence/occupancy evidence (visible for longer temporal window) |
| **Rear** | Departure confirmation (positive departure evidence) |

---

## 7. Audio Model

### 7.1 Binary Classification

| Class | Description |
|-------|-------------|
| `TRAIN_HORN` | Train horn from different trains, distances, crossings, environmental conditions |
| `NON_TRAIN_SOUND` | Vehicle horns, crowd noise, traffic, rain, wind, railway ambience without horn |

### 7.2 Dataset Targets (Proposed)

| Category | Target Count |
|----------|-------------|
| Train horn clips | 300–500 |
| Non-train audio clips | 300–500 |

**⚠️ These are aspirational targets, not absolute requirements.** Final counts depend on data diversity and experimental performance.

### 7.3 Audio Engineering Parameters (Initial)

| Parameter | Value |
|-----------|-------|
| Format | WAV |
| Sample rate | 16 kHz |
| Channels | Mono |
| Bit depth | 16-bit |
| Clip length | ~3–8 seconds |

**⚠️ These are initial engineering choices and may change if experiments justify different values.**

### 7.4 Audio Noise Robustness Testing

The audio model must be stress-tested under realistic background noise conditions, not only on clean recordings.

**Proposed SNR test levels:**

| SNR | Condition |
|-----|-----------|
| +10 dB | Mild noise |
| +5 dB | Moderate noise |
| 0 dB | Equal signal and noise |
| -5 dB | Severe noise |

**Goal:** Determine at what noise level the audio fallback becomes unreliable.

**⚠️ These are proposed test conditions — not finalized requirements.**

---

## 8. Image Dataset

### 8.1 Target

Approximately **4,000 high-quality real images**.

### 8.2 Required Characteristics

- No intentional duplicates
- Multiple camera viewpoints
- Multiple train types
- **30+ railway crossings** (geographic diversity is critical)
- Bangladesh-specific railway environment

**Rationale for geographic diversity:** A model trained and tested on the same crossing may learn background-specific features rather than generalizing to train detection.

### 8.3 Current Data (As Discussed — Requires Verification)

| Category | Count |
|----------|-------|
| Front | 334 |
| Side | 244 |
| Rear | 216 |
| Mixed (front+rear+side) | 386 |
| Fog (rear+front+side) | 63 |
| Rain (rear+front+side) | 129 |

**⚠️ These folders may contain overlapping images. The counts do NOT necessarily represent ~1,372 unique images without deduplication.**

### 8.4 Weather Distribution

Most images are daytime. A smaller portion includes nighttime, rain, and fog. Approximately 500 images may represent difficult conditions.

**⚠️ Exact distribution must be calculated from the final deduplicated dataset. Do not claim strong weather robustness without experimental demonstration.**

### 8.5 Data Splitting Strategy (Critical)

**Do NOT randomly split near-duplicate images from the same video across train and test.**

Split by **railway crossing/location** or **recording session** where possible.

Example layout:

| Split | Crossings |
|-------|-----------|
| Train | Crossing 1–24 |
| Validation | Crossing 25–27 |
| Test | Crossing 28–30+ |

**Purpose:** Measure generalization to **unseen railway crossings** — a far more meaningful evaluation than testing on frames from the same locations used for training.

### 8.6 Data Collection Strategy

Record videos at crossings and extract multiple modalities:

```
VIDEO
  ├── Image frames → Vision dataset
  └── Audio track → Horn clips + ambient audio → Audio dataset
```

Prioritize **diversity** over raw quantity across:
- Railway crossing location
- Train type
- Viewpoint (front/side/rear)
- Distance
- Camera angle
- Time of day
- Weather (rain, fog)
- Occlusion conditions
- Crowded vs. empty environments

---

## 9. Annotation Strategy

### 9.1 Workflow: Human-in-the-Loop / Model-Assisted

1. Manually label a diverse initial subset (~500–800 images).
2. Train an initial detector on this subset.
3. Use the detector to auto-label additional images.
4. Manually review predictions: correct bounding boxes, add misses, remove false positives.
5. Retrain with the expanded set.
6. Repeat iteratively.

### 9.2 Initial Manual Labeling Requirements

The initial ~500–800 images must include:
- Front, side, rear viewpoints
- Different crossings
- Day, night, rain, fog
- Near and far train distances

**Do not simply select the first N images by alphabetical order.**

### 9.3 Tooling

Roboflow may be used for dataset management, annotation, model-assisted annotation, versioning, and visualization. However, final experiments should use a **reproducible training pipeline** with explicitly controlled hyperparameters — the project must not depend on opaque hosted training results.

---

## 10. Proposed Experiments

### 10.1 Modality Comparison

The research should compare progressively stronger systems:

| Experiment | Description |
|------------|-------------|
| A | Front-only single-view detector (Baseline 1) |
| B | Front + Side |
| C | Front + Side + Rear (Baseline 2: Three-view visual) |
| D | Vision only (full visual system) |
| E | Audio only (Baseline 3: Horn detector) |
| F | Vision + Audio (Baseline 4: Multimodal) |
| G | Full proposed architecture (state-aware multimodal fail-safe) |

**⚠️ The exact experiment matrix should be finalized after initial model results.**

### 10.2 Failure Injection Experiments

The simulation should allow controlled failure of individual components:

- Front detection disabled
- Side confidence lowered
- Rear detection removed
- Audio corrupted with noise
- False positive injection
- Temporary camera failure

**Goal:** Measure how the decision engine behaves when individual components fail — not to claim the system never fails.

---

## 11. Metrics

### 11.1 Vision Metrics

- Precision, Recall, F1-score
- mAP@50, mAP@50:95
- Confusion matrix
- Precision-Recall curve

### 11.2 Audio Metrics

- Accuracy, Precision, Recall, F1-score
- ROC-AUC (if appropriate)
- Confusion matrix

### 11.3 System-Level Metrics

- False positive rate
- False negative rate (safety-critical priority)
- Train-arrival detection success rate
- Train-departure confirmation accuracy
- Decision latency
- Warning time before crossing
- Failure recovery behavior
- State-transition correctness

**Safety-critical analysis should prioritize false negatives over false positives.**

---

## 12. False Positive / False Negative Tradeoff

A naive OR fusion rule: `front OR side OR rear OR horn = train` can inflate false positives. If each detector independently has false-positive probability \(p\), the combined false-positive probability can approach:

\[
1 - (1 - p)^n
\]

Adding more detectors is **not automatically better**.

### Proposed Investigation Approaches

1. Simple threshold logic (transparent baseline)
2. Confidence-weighted fusion
3. Calibrated probabilities
4. Temporal consistency filtering
5. State-dependent thresholds

**⚠️ Start with a transparent baseline; add complexity only when experiments justify it.**

---

## 13. Research Novelty (Handle Carefully)

### Potential Novelty Areas (Under Investigation)

1. **Bangladesh-specific railway crossing dataset** — if no comparable public dataset exists
2. **Multi-view train detection** designed around approach, occupancy, and departure roles
3. **Audio-assisted train detection** as fallback in a crossing safety context
4. **State-aware fail-safe decision logic** with explicit failure-mode testing
5. **Safety-oriented failure analysis** measuring system behavior under component failures
6. **Cross-crossing generalization evaluation** via location-aware data splitting

### ⚠️ Unverified Claims

Do **not** claim: "No one has ever combined audio and vision for trains."

This must be verified through systematic literature review. Existing literature may already include:
- Train horn detection systems
- Audio-visual railway datasets
- Sensor fusion for railway monitoring
- Multimodal railway perception

Novelty must be defined **precisely and defensibly** after a thorough literature review.

---

## 14. Publication Target

**Initial target:** Normal / mid-tier international conference.

**Possible venues:**
- IEEE conferences (region-specific or topic-specific)
- Springer conferences
- ACM/engineering conferences
- Transportation/railway/AI intersections

**Long-term possibility:** Q2 journal extension if experimental results are sufficiently strong.

**Current priority:** Technically sound + well evaluated + reproducible + clear contribution. Do not optimize for Q1 requirements unless the project naturally reaches that level.

---

## 15. Project Deliverables

### Data
- Cleaned dataset with annotation files
- Dataset statistics and metadata
- Train/validation/test split documentation

### Models
- Baseline vision model
- Final vision model
- Audio horn model
- Decision/fusion module

### Experiments
- Training logs
- Evaluation results
- Ablation studies
- Failure tests
- Robustness tests

### Figures
- System architecture diagram
- Workflow diagram
- Dataset distribution charts
- Training curves
- Confusion matrices
- Precision-Recall curves
- ROC curves (where appropriate)
- Model comparison graphs
- Failure analysis graphs
- State-transition results

### Tables
- Dataset statistics
- Model comparison
- Modality comparison
- Failure analysis
- Robustness results

### Code
- Data preprocessing utilities
- Annotation utilities
- Training scripts
- Evaluation scripts
- Inference pipeline
- Audio processing
- Decision engine
- Simulation framework
- Visualization tools

### Documentation
- README
- Experiment log
- Model configuration records
- Dataset documentation
- Reproducibility instructions

---

## 16. Scope Boundaries

### In Scope (Current Research Phase)

- Dataset collection and annotation
- AI model training and evaluation
- Decision engine design and implementation
- Software simulation of crossing states
- Experiments, graphs, tables, results
- Documentation and reproducibility

### Out of Scope (Deferred)

- Physical Raspberry Pi or edge deployment
- Real-time hardware testing
- Latency claims on embedded hardware
- Hardware gate controller integration
- Field deployment

**⚠️ Do not claim real-time edge performance without hardware testing.**

---

## 17. What Makes This Project Strong vs. Weak

### Strong Version

- ~4,000 high-quality real images across 30+ crossings
- Diverse train types and viewpoints (front/side/rear)
- Real rain, night, fog samples
- 300–500 train horn clips with realistic negatives
- Rigorous, verifiable annotation
- Location-aware dataset split
- Strong baselines properly compared
- Multimodal comparison with ablation
- State-machine decision engine
- Failure injection experiments
- False-positive/false-negative analysis
- Noise stress testing
- Comprehensive graphs and tables
- Reproducible code

### Weak Version (Avoid)

- "Train YOLO on 4,000 images and report mAP"
- Random train/test split with no location awareness
- No baseline comparisons
- No failure analysis
- No audio evaluation
- No temporal analysis
- No multimodal comparison
- Unexplained decision logic
- Unsupported novelty claims
- Claims of real-time deployment without hardware testing

---

## 18. Assumptions Register

The following are current design assumptions — **not verified findings**:

| # | Assumption | Status |
|---|-----------|--------|
| A1 | ~5–6 meters between cameras is a reasonable starting distance | Needs experimental validation |
| A2 | 3–8 second audio clips capture meaningful horn events | Needs verification on real horn events |
| A3 | 16 kHz mono WAV is sufficient for horn classification | Standard choice, test if needed |
| A4 | Three viewpoint classes (front/side/rear) cover the needed information | Will be evaluated through annotation quality |
| A5 | ~500 difficult-condition images provide meaningful robustness signal | Must be verified experimentally |
| A6 | Location-based splitting captures generalization better than random | Standard practice, but magnitude of effect should be measured |
| A7 | Audio provides complementary evidence to vision | Must be experimentally demonstrated, not assumed |
| A8 | 300–500 clips per audio class is sufficient | Depends on acoustic diversity achieved |

---

## 19. Unresolved Research Questions

1. What is the optimal camera placement geometry for this specific crossing scenario?
2. What fusion method best balances safety and false-positive rate?
3. How does the system degrade as individual components fail?
4. What is the minimum reliable detection distance for safe gate closure?
5. How does temporal consistency filtering affect detection latency?
6. At what SNR does the audio fallback become unreliable?
7. Is the three-class viewpoint scheme sufficient or does it introduce unacceptable label noise?
8. Does cross-crossing generalization hold at a statistically meaningful level?
9. What is the false-negative rate under worst-case conditions?
10. How should the decision engine handle conflicting evidence (e.g., vision says no train, audio says horn)?
11. What is the publication novelty, precisely defined and literature-supported?

---

## 20. Research Discipline Rules

When implementing:

- Does this help answer the research question?
- How will we evaluate it?
- What baseline does it need?
- What data does it require?
- Could this introduce data leakage?
- Could this create unfair comparisons?
- Can we reproduce this result?
- Is the metric appropriate?
- Does this strengthen or weaken the publication argument?

**Prefer experimentally justified complexity over complexity for its own sake.**

---

## 21. Project Structure (Proposed)

```
Train_automation/
├── docs/
│   ├── RESEARCH_CONCEPT.md      ← This file
│   ├── RESEARCH_DECISIONS.md    ← Decision log
│   ├── EXPERIMENT_PLAN.md       ← Experiment designs
│   ├── IDEA_LOG.md              ← Captured ideas
│   ├── DATASET_DOCUMENTATION.md ← (future)
│   └── LITERATURE_NOTES.md      ← (future)
├── data/                        ← (future)
├── vision/                      ← (future)
├── audio/                       ← (future)
├── fusion/                      ← (future)
├── simulation/                  ← (future)
├── experiments/                 ← (future)
├── results/                     ← (future)
├── models/                      ← (future)
└── README.md
```

**Do not create empty directories preemptively. Create them when they are needed.**

---

*This document is the persistent source of truth for this research project. Update it when design decisions change, assumptions are validated or invalidated, or the research direction shifts.*
