# Idea Log

**Status:** Active — captures all proposed ideas, their evaluation, and their disposition.

**Last updated:** 2026-08-10

> **Protocol status (2026-08-13):** This is a historical idea record. The term “fail-safe” in retained entries does not describe a physical-safety claim. New ideas affecting multimodal system evaluation must first be checked against [`RESEARCH_PROTOCOL_V2.md`](RESEARCH_PROTOCOL_V2.md).

---

## Purpose

This file records every research idea proposed during the project. Ideas are captured, analyzed, and assigned a disposition. This prevents ideas from being lost in conversation and ensures that rejected ideas are recorded with their rationale.

---

## Disposition Categories

| Disposition | Meaning |
|-------------|---------|
| **PROPOSED** | Idea suggested but not yet evaluated |
| **ACCEPTED** | Accepted into the current research plan |
| **REJECTED** | Evaluated and rejected (reason recorded) |
| **NEEDS EXPERIMENT** | Requires experimental evidence before deciding |
| **DEFERRED** | Worthwhile but not in current scope; may revisit later |
| **SUPERSEDED** | Replaced by a better idea (cross-reference) |

---

## Idea Records

### I-001: Front/Side/Rear Viewpoint Classes

**DATE:** 2026-08-10
**SOURCE:** Initial project design
**IDEA:** Use three viewpoint classes (front, side, rear) instead of a single "train" class to support the approach-occupancy-departure workflow.
**ANALYSIS:** This is fundamental to the research architecture. The viewpoint distinction directly supports the decision engine's ability to differentiate approach from departure.
**AFFECTS:** Vision model, annotation strategy, dataset labels, decision engine, experiments.
**EVIDENCE NEEDED TO ACCEPT:** Annotation feasibility study — can human annotators consistently label these three classes with acceptable inter-annotator agreement?
**EVIDENCE NEEDED TO REJECT:** If inter-annotator agreement is poor or if model confusion between classes is so high that the distinction cannot be reliably learned.
**DISPOSITION:** ACCEPTED (recorded as decision D-001)

---

### I-002: Two Cameras at 5–6 Meter Separation

**DATE:** 2026-08-10
**SOURCE:** Initial project design
**IDEA:** Position Camera 1 and Camera 2 approximately 5–6 meters apart on opposite sides of the crossing.
**ANALYSIS:** This is a starting assumption, not a validated optimal. Camera placement affects FOV, occlusion patterns, and detection distance. The exact distance should be evaluated against real crossing geometry.
**AFFECTS:** Architecture, simulation geometry, future deployment.
**EVIDENCE NEEDED TO ACCEPT:** Simulation or field measurement showing that 5–6 meters provides adequate coverage of both approach and departure zones at a representative crossing. Alternatively, a sensitivity analysis showing that the system is robust to a range of camera distances.
**EVIDENCE NEEDED TO REJECT:** If this distance creates unacceptable blind spots or if most Bangladesh crossings cannot physically accommodate this separation.
**DISPOSITION:** ACCEPTED (recorded as decision D-002, with assumption noted in RESEARCH_CONCEPT.md §3.2)

---

### I-003: Audio Train Horn Detection as Fail-Safe

**DATE:** 2026-08-10
**SOURCE:** Initial project design
**IDEA:** Use audio train horn detection as an independent fail-safe when vision evidence is unreliable (night, fog, occlusion, camera failure).
**ANALYSIS:** Conceptually sound — audio is unaffected by visual occlusion and darkness. However, the idea must be experimentally validated: horn audibility at varying distances, noise robustness, and real-world false-positive rates from non-train horns (trucks, buses) in Bangladeshi environments.
**AFFECTS:** Audio model, dataset, fusion logic, experiments (R-EXP-2).
**EVIDENCE NEEDED TO ACCEPT:** Experiment showing that audio detection maintains acceptable accuracy at the distances and noise levels expected at real crossings.
**EVIDENCE NEEDED TO REJECT:** If horn detection is unreliable under realistic noise, or if truck/bus horns produce an unacceptable false-positive rate that makes audio more harmful than helpful in the fusion system.
**DISPOSITION:** ACCEPTED (recorded as decision D-003)

---

### I-004: Raspberry Pi / Edge Deployment

**DATE:** 2026-08-10
**SOURCE:** Initial project design
**IDEA:** Deploy the system on a Raspberry Pi or NVIDIA Jetson at a real crossing.
**ANALYSIS:** This would strengthen the publication by demonstrating real-world feasibility. However, it adds significant engineering complexity (model optimization, latency measurement, sensor integration, field testing, power, weatherproofing) that is not required to answer the current research question. Premature deployment claims without measurement would weaken the paper.
**AFFECTS:** Hardware, deployment, latency metrics, publication scope.
**EVIDENCE NEEDED TO ACCEPT:** Successful model optimization for the target hardware with measured latency and throughput, plus access to a test crossing and hardware.
**EVIDENCE NEEDED TO REJECT:** N/A
**DISPOSITION:** DEFERRED (future work, recorded as decision D-006)

---

### I-005: Oblique/Ambiguous Viewpoint Class

**DATE:** 2026-08-10
**SOURCE:** Initial project design discussion
**IDEA:** Add a fourth "oblique/ambiguous" class for images where the viewpoint is not clearly front, side, or rear.
**ANALYSIS:** Adding a fourth class increases annotation complexity and may fragment an already small dataset. An internal metadata tag could serve the same purpose (identifying ambiguous samples) without forcing the model to learn a fourth class. Whether the model needs this class depends on how many images are genuinely ambiguous.
**AFFECTS:** Vision model, annotation, class design.
**EVIDENCE NEEDED TO ACCEPT:** Annotation audit showing that >15-20% of images cannot be confidently assigned to front/side/rear, and that this ambiguity significantly harms model performance.
**EVIDENCE NEEDED TO REJECT:** If fewer than 10% of images are ambiguous and the three-class model handles them acceptably through confidence scores.
**DISPOSITION:** NEEDS EXPERIMENT (evaluate during annotation phase)

---

### I-006: Synthetic Weather Augmentation

**DATE:** 2026-08-10
**SOURCE:** Initial project design discussion
**IDEA:** Use synthetic augmentation (adding rain, fog overlays) to supplement limited real adverse-weather data for training.
**ANALYSIS:** This is a common practice and may help model robustness when real adverse-weather data is limited. However, evaluation must be kept separate — synthetic-augmented training should not be tested on synthetic-augmented test data. Real adverse-weather evaluation must use only real images.
**AFFECTS:** Training pipeline, augmentation strategy, experiment design.
**EVIDENCE NEEDED TO ACCEPT:** An initial experiment comparing (a) model trained on clean data only vs. (b) model trained with synthetic weather augmentation, both evaluated on real adverse-weather test images. If (b) significantly outperforms (a), augmentation is justified.
**EVIDENCE NEEDED TO REJECT:** If synthetic augmentation does not improve real-weather test performance, or if it degrades clean-weather performance.
**DISPOSITION:** NEEDS EXPERIMENT

---

### I-007: Pre-trained Audio Model Fine-tuning (YAMNet/VGGish)

**DATE:** 2026-08-10
**SOURCE:** Implicit from audio model design discussion
**IDEA:** Use a pre-trained audio model (e.g., YAMNet, VGGish) fine-tuned on train horn data instead of training a CNN from scratch.
**ANALYSIS:** Fine-tuning a pre-trained model may improve performance given the limited audio dataset size (~300-500 clips). However, it adds complexity and a dependency on a specific pre-trained model. Start with a simple baseline (CNN on mel-spectrograms, or SVM on MFCCs) and only escalate if the baseline is inadequate.
**AFFECTS:** Audio model, training pipeline, dependencies.
**EVIDENCE NEEDED TO ACCEPT:** Experiment showing that the fine-tuned model significantly outperforms the simple baseline, with the improvement justifying the added complexity.
**EVIDENCE NEEDED TO REJECT:** If the simple baseline already achieves acceptable performance (>90% accuracy on clean audio).
**DISPOSITION:** NEEDS EXPERIMENT (try simple baseline first — see A-EXP-1 in EXPERIMENT_PLAN.md)

---

### I-008: Three or More Cameras

**DATE:** 2026-08-10
**SOURCE:** Implicit from architecture discussion
**IDEA:** Add a third (or more) camera(s) for additional viewpoints or redundancy.
**ANALYSIS:** More cameras could improve coverage and redundancy but add cost, complexity, and synchronization requirements. A two-camera design already covers approach and departure. A third camera would need to provide a clearly distinct role (e.g., overhead view, crossing-clear verification) to justify its inclusion.
**AFFECTS:** Architecture, cost, complexity, synchronization.
**EVIDENCE NEEDED TO ACCEPT:** Experiment showing that the two-camera system has a significant blind spot or failure mode that a third camera would resolve, with quantified improvement.
**EVIDENCE NEEDED TO REJECT:** If the two-camera system already achieves acceptable coverage for the research question.
**DISPOSITION:** DEFERRED

---

### I-009: Learned Fusion (Neural Network Fusion Layer)

**DATE:** 2026-08-10
**SOURCE:** Implicit from fusion discussion
**IDEA:** Instead of rule-based fusion, train a neural network to learn the optimal fusion of vision and audio evidence.
**ANALYSIS:** A learned fusion could theoretically discover more sophisticated integration patterns than hand-crafted rules. However, it introduces additional complexity, potential overfitting, and reduced interpretability. Start with transparent rule-based fusion and only move to learned fusion if rule-based methods are demonstrably insufficient.
**AFFECTS:** Fusion module, training pipeline, interpretability.
**EVIDENCE NEEDED TO ACCEPT:** Experiment showing that learned fusion significantly outperforms the best rule-based method on the safety-critical metrics (particularly false-negative rate).
**EVIDENCE NEEDED TO REJECT:** If rule-based fusion already achieves near-optimal performance, or if the learned fusion is too opaque to analyze failure modes.
**DISPOSITION:** DEFERRED (start with rule-based — see DE-EXP-3 in EXPERIMENT_PLAN.md)

---

### I-010: Temporal Model (LSTM/Transformer on Detection Sequences)

**DATE:** 2026-08-10
**SOURCE:** Implicit from temporal consistency discussion
**IDEA:** Use a sequence model (LSTM, Transformer) over frame-level detections to learn temporal patterns of approach, passage, and departure instead of rule-based temporal filtering.
**ANALYSIS:** A sequence model could capture complex temporal patterns and potentially reduce false positives from brief detection flickers better than simple temporal consistency rules. However, it requires temporally annotated sequences (approach/passage/departure ground truth), adds model complexity, and may be harder to debug. Start with simple temporal consistency filtering (e.g., detection must persist for N consecutive frames).
**AFFECTS:** Decision engine, annotation (temporal labels needed), model complexity.
**EVIDENCE NEEDED TO ACCEPT:** Experiment showing that the sequence model significantly outperforms rule-based temporal filtering on state-transition accuracy, with acceptable latency.
**EVIDENCE NEEDED TO REJECT:** If rule-based temporal filtering is sufficient, or if collecting temporal ground truth is infeasible.
**DISPOSITION:** DEFERRED

---

### I-011: Vibration or Other Sensor Modalities

**DATE:** 2026-08-10
**SOURCE:** Implicit from modality discussion
**IDEA:** Add vibration sensors, infrared, radar, or other sensing modalities to the system.
**ANALYSIS:** Additional sensor modalities could improve robustness, particularly for confirming train presence when visual and audio evidence are both uncertain. However, they add hardware complexity and move the project closer to a hardware deployment that is currently out of scope. For the current research phase, vision and audio are sufficient modalities to study the multimodal fusion problem.
**AFFECTS:** Hardware, scope, cost.
**EVIDENCE NEEDED TO ACCEPT:** A clear demonstration that vision+audio alone cannot achieve acceptable reliability, and that a third modality would close the gap.
**EVIDENCE NEEDED TO REJECT:** If vision+audio already achieves strong results for the research question.
**DISPOSITION:** DEFERRED

---

### I-012: Phase 0 Perceptual Duplicate Detection Placeholder

**DATE:** 2026-08-13
**SOURCE:** Phase 0 implementation review
**IDEA:** Add perceptual (pHash/dHash) duplicate detection to the Phase 0 validator.
**ANALYSIS:** Exact filename and SHA-256 duplicate detection are already implemented. Perceptual hashing is explicitly deferred to a later phase per the roadmap because it is heavier and not required for the foundation. The validator's report structure already separates exact basename and hash duplicate candidates.
**AFFECTS:** `data/validator.py`, dataset audit reporting.
**EVIDENCE NEEDED TO ACCEPT:** Real Layer A dataset arrives and exact-hash checks are insufficient for near-duplicate video frames.
**EVIDENCE NEEDED TO REJECT:** If exact-hash plus group-aware splitting already prevents the material leakage risk.
**DISPOSITION:** DEFERRED (documented as Phase 1+ candidate)

---

## Idea Capture Protocol

When a new idea is proposed (e.g., "What if we...", "Should we add...", "I have an idea..."):

1. Record it here immediately with a unique ID and DISPOSITION: PROPOSED.
2. Analyze what the idea affects (architecture, dataset, model, experiment, safety logic, publication).
3. Determine what evidence would be needed to accept or reject it.
4. Assign a final disposition after analysis.
5. If ACCEPTED, create a corresponding decision in RESEARCH_DECISIONS.md.
6. If NEEDS EXPERIMENT, add it to EXPERIMENT_PLAN.md.

**Do not modify implementation code based on an idea until it has been analyzed and dispositioned here.**

---

*Add new ideas at the bottom. Use sequential IDs (I-012, I-013, ...). Do not delete old ideas — update their disposition if they are superseded.*
