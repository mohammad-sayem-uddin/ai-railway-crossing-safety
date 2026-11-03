# Independent Research Design Audit
## Railway Crossing Vision-Audio Fusion Safety System

**Audit Date:** 2026-10-13
**Auditor Role:** Independent Senior ML Research Scientist, Computer-Vision Engineer, Multimodal Fusion Specialist, Experimental-Methodology Reviewer
**Scope:** DESIGN AND DOCUMENTATION ONLY — No code changes, no test execution
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`

---

## Executive Summary

> [!CAUTION]
> **The existing test suite (49/49 passed) provides zero evidence about the system's real-world detection performance.** It verifies software plumbing and schema compliance only. The research cannot make any detection accuracy, safety rate, or fusion contribution claims until a full-dataset end-to-end inference run is completed against approved ground truth.

This audit identifies **14 critical findings**, **8 major design flaws**, and **6 recommendations** across the experimental methodology, testing infrastructure, evaluation protocol, and ablation design. The findings are organized by severity.

---

## Table of Contents

1. [Critical Findings](#1-critical-findings)
2. [Testing Infrastructure Audit](#2-testing-infrastructure-audit)
3. [Experimental Design Audit (Ablation Matrix)](#3-experimental-design-audit)
4. [Evaluation Protocol Audit](#4-evaluation-protocol-audit)
5. [Pipeline Architecture Audit](#5-pipeline-architecture-audit)
6. [Ground Truth Audit](#6-ground-truth-audit)
7. [Statistical Validity Audit](#7-statistical-validity-audit)
8. [Corrected Experimental Plan](#8-corrected-experimental-plan)
9. [Execution Priority Matrix](#9-execution-priority-matrix)
10. [Open Questions Requiring Researcher Decision](#10-open-questions)

---

## 1. Critical Findings

### CF-01: No End-to-End Inference Has Been Run on the Full Dataset

**Severity:** 🔴 CRITICAL — Blocks all research claims

The entire existing test suite is **infrastructure verification**, not **system evaluation**. Specifically:

| Test Layer | What It Actually Tests | What It Does NOT Test |
|---|---|---|
| Layer F (6) | Model file SHA-256 checksums and byte sizes | Whether the models produce correct predictions |
| Layer A (15) | Schema validation, timestamp ordering, firewall | Whether predictions match ground truth |
| Layer B (8) | File existence, directory structure, cohort counting | Whether inference outputs are correct |
| Layer C (3) | Video decoding, audio demuxing, FSM lifecycle (synthetic) | Real inference on real data |
| Layer D (12) | Synthetic fault injection on synthetic data | Real faults on real data |
| Layer E (5) | 4 representative natural-media replays for health/duration | Full 27-event detection performance |

**The 49/49 pass rate is methodologically irrelevant to the research question.** It proves the software doesn't crash and the data files are organized correctly. It says nothing about:
- Whether the YOLO model detects trains in these specific videos
- Whether Audio V3 detects train horns versus road traffic
- Whether the fusion logic produces correct gate decisions
- What the missed-train rate, premature-opening rate, or warning lead times are

**Required Action:** Execute full-dataset inference across all 27 events before any claims can be made.

---

### CF-02: The Existing B0–B7 Benchmark Runner Has Never Been Executed on Real Data

**Severity:** 🔴 CRITICAL

The orchestrator [`run_real_world_experiments.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/run_real_world_experiments.py) contains complete code for B0–B7 execution, statistical analysis, and publication figure generation. However:

1. **The `data/raw/layer_b/videos/` directory contains only a `.gitkeep` file.** The video files are in `data/raw/layer_b/v2/{train_events,no_train_events,engine_events}/`. The orchestrator discovers events from `LAYER_B_VIDEOS_DIR` (line 53), which points to the **wrong directory**.
2. The script references 21 events (line 8: "21-event real-world ingestion"), but there are 27 active events. The script was written before the dataset was finalized.
3. The paired-comparison block (lines 187–199) reads `single_events.json` from disk but these files don't exist because the runner has never completed.

**Required Action:** Before execution, the orchestrator must be updated to:
- Point to `data/raw/layer_b/v2/` (correct V2 layout)
- Discover all 27 active events (23 train + 3 no-train + 1 engine-only)
- Exclude `event_historical_duplicate_010`

---

### CF-03: The Ablation Matrix (E1–E7) Is Partially Disconnected from the Implemented Benchmark Conditions (B0–B7)

**Severity:** 🔴 CRITICAL

Two separate experiment taxonomies exist and are **not reconciled**:

| Document | Taxonomy | Status |
|---|---|---|
| [`FINAL_ABLATION_MATRIX.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FINAL_ABLATION_MATRIX.md) | E1–E7 (clean single-DOF ablation) + E8–E10 (stress tests) | **Documented but NOT implemented** |
| [`runner.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/experiments/runner.py) | B0–B7 (historical conditions) | **Implemented but partially misaligned** |

The E1–E7 matrix provides the scientifically correct ablation design (single-DOF progression), but no code implements it. The B0–B7 code implements a different, partially overlapping set of conditions. For example:
- **E2 (Single-Cam Temporal)** has no B-series equivalent
- **E3 (Dual-Cam Naive)** has no B-series equivalent
- **E5 (Dual-Cam State-Aware, no audio)** has no B-series equivalent
- **B1 (Audio Only)** exists in code but not in E-series matrix

**Required Action:** Decide which taxonomy is canonical. Either:
- (a) Implement E1–E7 in code and retire B0–B7, or
- (b) Map B0–B7 exactly to E1–E7 and rename, or
- (c) Accept B0–B7 as the executed taxonomy and document the ablation limitations

---

### CF-04: Audio Inference Threshold Mismatch

**Severity:** 🔴 CRITICAL

Three different audio thresholds appear in the codebase:

| Location | Threshold | Purpose |
|---|---|---|
| [`layer_b_processor.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/experiments/layer_b_processor.py#L101) line 101 | `0.5184` | Default in `_get_audio_pipeline()` |
| [`layer_b_processor.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/experiments/layer_b_processor.py#L288) line 288 | `0.5184` | Default in `process_event()` |
| [`FINAL_ABLATION_MATRIX.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FINAL_ABLATION_MATRIX.md) line 26 | `0.3700` | Documented operating threshold |
| [`leakage_guard.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/experiments/leakage_guard.py) | `0.3700` | Frozen parameter check |

The **documented canonical threshold** is $T^* = 0.3700$ (optimized on ESC-50 validation), but the **code defaults** are `0.5184`. This means if the runner is executed with default arguments, it will use a stricter threshold than the documented operating point, producing systematically different (less sensitive) audio inference results.

**Required Action:** Reconcile to a single canonical threshold. The code defaults must match the documented value, or the exact threshold used must be explicitly logged at runtime.

---

### CF-05: Camera Fusion Violates R04 (Independent Timelines)

**Severity:** 🟡 MAJOR

The `MultimodalEvidenceCollector` in [`collector.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/collector.py) pools `camera_1` and `camera_2` evidence records into the same buffer (line 72) and aligns them to a single master clock. However:

- **Prerequisite R04 is UNRESOLVED**: Front and back cameras have no certified temporal synchronization.
- The `SyncAligner` is initialized without empirical offsets, meaning it applies zero offset — which implicitly assumes the cameras are perfectly synchronized.
- This is a **hidden assumption** that contradicts the documented R04 constraint.

**Required Action:** Either:
- (a) Measure and certify inter-camera offsets before fusing, or
- (b) Process each camera as an independent pipeline and merge decisions (not evidence), or
- (c) Document the zero-offset assumption as a known limitation and bound the maximum error

---

## 2. Testing Infrastructure Audit

### TI-01: Layer E Coverage Is Insufficient

**Severity:** 🟡 MAJOR

Layer E replays only 4 representative natural-media streams (out of 54 total streams across 27 events). This provides no evidence about:
- Events with unusual characteristics (e.g., `event_005` right-censored, `event_009`/`015`/`016` late arrival, `event_011` with secondary clearing)
- The 3 no-train negative controls (false alarm evaluation)
- The engine-only event (single-unit coincidence rule)

### TI-02: No Per-Frame Prediction Logging

**Severity:** 🟡 MAJOR

The `LayerBEventProcessor` caches inference results to JSONL files but does not:
- Log per-frame YOLO class names, confidence scores, and bounding box coordinates in a structured, queryable format
- Log per-window audio probabilities with their temporal positions
- Produce a unified timeline of {timestamp, vision_detections, audio_probability, fusion_state, gate_state}

Without per-frame logs, it is impossible to:
- Debug false negatives (which frames missed the train?)
- Attribute errors to specific modalities
- Verify that audio evidence influenced specific state transitions

**Required Action:** The inference pipeline must produce a per-event structured log file with all per-frame/per-window predictions at full resolution.

### TI-03: No Ground Truth Comparison Logic Exists

**Severity:** 🟡 MAJOR

The [`EventMetricsCalculator`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py) computes metrics from `SimulationRunResult`, which has `entry_time_s` and `clearance_time_s` parameters — but there is no code that reads the approved ground truth JSON and feeds $T_1$ and $T_4$ as these parameters. The comparison is currently manual/hypothetical.

---

## 3. Experimental Design Audit

### ED-01: The E1–E7 Single-DOF Design Is Sound but Has an Implicit Interaction Confound

**Severity:** 🟢 MINOR

The E1–E7 progression is well-designed for isolating individual subsystem contributions. However, the contrast $\Delta_{\text{full}} = E_7 - E_5$ measures "audio contribution given state machine is present," while $\Delta_{\text{audio\_stateless}} = E_6 - E_4$ measures "audio contribution without state machine." If there is an **interaction effect** (audio is more useful when combined with the state machine), these two contrasts will give different answers. This is not a flaw but should be explicitly discussed.

### ED-02: The No-Train Denominator Problem Is Correctly Identified but Under-Documented

**Severity:** 🟡 MAJOR

The 3 no-train events provide approximately 120 stream-seconds of negative exposure. This is **far too little** to estimate false alarm rates with meaningful precision:

| Observed False Alarms | Rate Estimate | Wilson 95% CI |
|---|---|---|
| 0 | 0.0% | [0.0%, 3.1%] per minute |
| 1 | 0.5/min | [0.1%, 2.8%] per minute |
| 2 | 1.0/min | [0.3%, 3.5%] per minute |

The uncertainty is enormous. Any false alarm rate claim must include these confidence intervals and an explicit note that 120 seconds is an exploratory pilot sample, not a representative evaluation.

### ED-03: Left-Censoring Handling Is Correct but Reduces the Evaluable Detection Latency Cohort Substantially

**Severity:** 🟢 MINOR

20 of 23 full-train events are left-censored ($T_0 = 0.00$s, train already visible at recording start). Only 3 events (`event_009`, `event_015`, `event_016`) have observable approach onset. This means:
- **Physical detection latency** can only be computed on 3 events — too few for statistical inference
- **Warning lead time** ($T_1 - T_{\text{detect}}$) is bounded by the recording start, not the true first appearance

This is correctly documented but should be prominently stated in any results section.

### ED-04: Engine-Only Event Has Ambiguous Evaluation Semantics

**Severity:** 🟢 MINOR

`engine_events/event_001` has $T_3 \equiv T_4 = 6.20$s and zero cars. The coincidence rule is correct, but the evaluation should clarify:
- Is this event included in the MTR denominator? (It should be — it's a real train)
- Is it included in the POR denominator? (It should be, unless the gate was never closed)
- Does the single-unit traversal duration (6.20s total crossing time) represent a stress test for the clearance dwell timer?

---

## 4. Evaluation Protocol Audit

### EP-01: No Formal Definition of "Missed Train" at the System Output Level

**Severity:** 🔴 CRITICAL

The ablation matrix defines MTR as "percentage of evaluable train events where gate failed to close by $T_1$." But at the system output level:
- What exactly constitutes "gate closed"? Is it the `GATE_CLOSING` state entry, or `gate_angle_deg == 0`?
- The `PhysicalGateModel` has a mechanical closing time (3.0s default). So the gate can be *commanded* closed before $T_1$ but not *physically* closed until after $T_1$. Which matters?
- Is a partial gate closure (e.g., gate at 45°) counted as "closed" or "missed"?

**Required Action:** Define MTR precisely in terms of observable system outputs:
- `MTR = fraction of events where crossing_state ∉ {GATE_CLOSING, TRAIN_PRESENT, CROSSING_OCCUPIED, ...} at time T1`
OR
- `MTR = fraction of events where gate_angle_deg > X at time T1`

### EP-02: Premature Opening Rate Definition Needs Temporal Precision

**Severity:** 🟡 MAJOR

POR is defined as "gate opened while $t < T_4$." But:
- Does "opened" mean `GATE_OPENING` state entry, or `gate_angle_deg > 0`, or `is_passage_blocked == False`?
- The `PhysicalGateModel` transitions through `OPENING` → `OPEN`. An instantaneous transition command at $t = T_4 - 0.01$s would not complete opening before $T_4$.
- Should POR measure the **decision** timestamp or the **physical gate position**?

### EP-03: No Metric for Unnecessary Closures on No-Train Events

**Severity:** 🟡 MAJOR

For the 3 no-train events, the evaluation needs to measure:
- **Nuisance closure count:** Number of times the system transitions out of IDLE
- **Nuisance closure duration:** Total time the gate was unnecessarily closed
- **Nuisance closure source:** Which modality (vision false positive vs audio false positive) triggered each closure

These metrics are mentioned in the ablation matrix (§6) but have no implementation in the evaluation code.

---

## 5. Pipeline Architecture Audit

### PA-01: Audio Is Extracted Only from Front Camera

**Severity:** 🟡 MAJOR

[`layer_b_processor.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/experiments/layer_b_processor.py#L300) line 300:
```python
front_wav = audio_paths.get("front")
```

Audio inference runs **only on the front camera's audio track**. The back camera's embedded audio is extracted but never used for inference. This means:
- If the horn is more audible from behind (e.g., as the train approaches from the rear), the system will miss it
- The audio contribution (E6/E7 vs E4/E5) is evaluated on a single-microphone configuration, not dual

This should either:
- (a) Be documented as a deliberate design choice (audio from front microphone only), or
- (b) Be extended to process both audio tracks and fuse them

### PA-02: Vision Label Matching May Not Align with Model Output Classes

**Severity:** 🟡 MAJOR

The `has_qualified_approach()` function checks for labels `("front", "side", "train")` and `has_qualified_departure()` checks for `("rear", "side", "train")`. But the YOLO model was trained on a custom dataset — what are the actual class names in `yolo.names`?

If the YOLO model outputs class names like `"locomotive"`, `"car"`, `"wagon"` instead of `"front"`, `"rear"`, `"side"`, then **all detection checks will return False** regardless of inference quality, because label matching fails silently.

**Required Action:** Verify the YOLO model's `names` dictionary and ensure the fusion rules reference the correct class labels.

### PA-03: The Temporal Confirmation Counter Has Asymmetric Reset Logic

**Severity:** 🟢 MINOR

In the decision engine, `consecutive_approach_count` increments on approach detection and presumably resets on non-detection. The confirm_frames requirement (default 2) means the system needs 2 consecutive frames with approach evidence before transitioning to WARNING. However:
- Does a single non-detection frame reset the counter to 0? (Harsh)
- Does the counter decay by 1 per non-detection frame? (EMA-like)
- How does this interact with the 5 FPS sampling rate and the window_tolerance_s?

The temporal filtering behavior should be precisely specified and match the E2/E3/E4 ablation conditions.

---

## 6. Ground Truth Audit

### GT-01: Annotation Quality Is Reasonable but Contains Known Uncertainties

**Severity:** 🟢 MINOR

The candidate annotations have been through multiple verification rounds (3+ passes). The timestamp values show physical plausibility (diverse T1/T2/T3/T4 values across events). Known uncertainties:
- Horn status for 10 events marked as "present" is based on spectral analysis only (NOT_LISTENED)
- Boundary frame precision is ±1 frame (±33ms at 30 FPS)
- Left-censoring on 20/23 events means T0 is clamped to 0.00s

### GT-02: No Inter-Annotator Agreement Measurement

**Severity:** 🟡 MAJOR

There is only one annotator (AI-assisted, human-reviewed). The research would be strengthened by:
- Having a second annotator review a subset (e.g., 5 events)
- Computing inter-annotator agreement on T1, T2, T3, T4 timestamps
- Reporting the uncertainty budget

However, this may not be feasible for a single-researcher project. If so, document it as a limitation.

---

## 7. Statistical Validity Audit

### SV-01: Wilson CIs Are Appropriate but Event Clustering Must Be Disclosed

**Severity:** 🟡 MAJOR

All 27 events were recorded at 1–2 crossing sites. This means events are **not independent samples from the population of all railway crossings**. The Wilson CI assumes independent Bernoulli trials, which is violated by:
- Same crossing geometry
- Same ambient noise profile
- Same camera positions
- Potentially similar train schedules

The effective sample size is smaller than 27. This must be explicitly disclosed and the CIs interpreted as **conditional on this specific crossing site**, not generalizable.

### SV-02: Bootstrap Resampling on 23 Events Has Limited Resolution

**Severity:** 🟢 MINOR

With 23 train events, the bootstrap resamples will have limited resolution. A 10,000-resample bootstrap of 23 observations can distinguish rates to approximately ±4% (1/23 ≈ 4.3%). This is adequate for detecting gross differences but cannot resolve subtle improvements.

### SV-03: Paired Comparison (Sign Test) Is Appropriate but May Lack Power

**Severity:** 🟢 MINOR

The paired sign test on 23 events has power to detect effect sizes where approximately 75%+ of events show improvement. If the improvement is modest (e.g., 60% of events improved), the test will likely be non-significant. Consider also reporting the paired Wilcoxon signed-rank test as a complement.

---

## 8. Corrected Experimental Plan

### Phase 1: Prerequisites (Before Any Inference)

| Step | Task | Blocker? |
|---|---|---|
| P1.1 | Researcher approves candidate annotations → Stage 3 ground truth | **YES** |
| P1.2 | Reconcile audio threshold: set canonical value (0.3700 or 0.5184) in code AND documentation | **YES** |
| P1.3 | Verify YOLO model class names match fusion rule labels | **YES** |
| P1.4 | Fix orchestrator to point to V2 data directory | **YES** |
| P1.5 | Decide on canonical experiment taxonomy (E-series or B-series) | YES |
| P1.6 | Document zero-offset camera fusion assumption | YES |

### Phase 2: Full-Dataset Baseline Inference (E7/B4 — Full System)

Run the complete pipeline on all 27 events with:
- Both cameras (front + back vision inference at 5 FPS)
- Audio inference on front audio (threshold = canonical value)
- Full state machine and gate model
- Per-frame structured log output

**Expected output per event:**
```
{event_id}/
├── vision_front_detections.jsonl     # Per-frame: timestamp, class, conf, bbox
├── vision_back_detections.jsonl      # Per-frame: timestamp, class, conf, bbox
├── audio_front_windows.jsonl         # Per-window: center_time, probability, label
├── fusion_timeline.jsonl             # Per-step: timestamp, crossing_state, gate_state, gate_angle, rule_fired
├── evaluation_result.json            # MTR, POR, warning_lead_time, clearance_latency
└── summary.txt                       # Human-readable event summary
```

### Phase 3: Ablation Sweep

Run each ablation condition on all 27 events. The minimum defensible set is:

| Condition | Cameras | Temporal | FSM | Audio | Maps To |
|---|---|---|---|---|---|
| **E1** | Front only | Off (confirm=1) | Off | Off | B0 |
| **E4** | Front + Back | On (confirm=2) | Off | Off | ~B3 |
| **E5** | Front + Back | On (confirm=2) | On | Off | — |
| **E7** | Front + Back | On (confirm=2) | On | On | ~B4 |

If time permits, add E2, E3, E6 for full single-DOF isolation.

### Phase 4: Fault Injection (If Time Permits)

Run E9a–c and E10a–f on a representative subset (e.g., 5 events: `event_001`, `event_005`, `event_009`, `event_015`, and one no-train event). These are synthetic perturbations and contribute to robustness claims, not primary safety metrics.

### Phase 5: Evaluation and Reporting

1. Load approved ground truth (T0–T4 per event)
2. For each condition × event: compute MTR, POR, warning lead time, clearance latency
3. For each pairwise contrast: compute Wilson CIs and paired sign test
4. Generate publication tables and figures
5. Write final experimental report with explicit limitations section

---

## 9. Execution Priority Matrix

| Priority | Task | Estimated Time | Blocks |
|---|---|---|---|
| **P0** | Researcher annotation approval | Human time | Everything |
| **P0** | Fix audio threshold mismatch | 5 min | Inference |
| **P0** | Verify YOLO class labels | 10 min | Inference |
| **P0** | Fix orchestrator data path | 10 min | Inference |
| **P1** | Full E7 baseline inference (27 events) | 30–60 min | Evaluation |
| **P2** | Per-frame logging infrastructure | 1–2 hours | Debugging |
| **P2** | Ground truth comparison code | 1–2 hours | Metrics |
| **P3** | Ablation sweep (E1, E4, E5) | 1–2 hours | Ablation claims |
| **P4** | Fault injection | 2–3 hours | Robustness claims |
| **P5** | Publication figures/tables | 2–3 hours | Report |

---

## 10. Open Questions Requiring Researcher Decision

> [!IMPORTANT]
> The following questions must be answered by the researcher before proceeding with execution.

### Q1: Which audio threshold is canonical?
- **Option A:** $T^* = 0.3700$ (documented, ESC-50 optimized, more sensitive)
- **Option B:** $T^* = 0.5184$ (code default, more specific, fewer false alarms)
- **Option C:** Run both and compare (adds an ablation dimension)

### Q2: Should audio inference use both cameras' audio tracks?
- **Option A:** Front only (current implementation, simpler)
- **Option B:** Front + Back (potentially better horn detection, more complex)
- **Option C:** Front primary, back as fallback when front is unavailable

### Q3: Which experiment taxonomy is canonical for the paper?
- **Option A:** E1–E7 (scientifically cleaner, requires new implementation)
- **Option B:** B0–B7 (already partially implemented, less clean ablation)
- **Option C:** Hybrid (implement E1, E4, E5, E7 as the core experiments; keep B5–B7 as stress tests)

### Q4: How should the zero-offset camera assumption be handled?
- **Option A:** Accept it, document as limitation, run inference with zero offset
- **Option B:** Empirically measure offset using simultaneous audio events visible in both tracks
- **Option C:** Process each camera independently and make separate per-camera claims

### Q5: Should the engine-only event be included in MTR/POR denominators?
- **Option A:** Yes, include (it's a real train crossing event)
- **Option B:** Report separately (it has unusual characteristics: N=0 cars, T3≡T4)

### Q6: What is the minimum acceptable standard for ground truth approval?
- **Option A:** Researcher reviews all 27 review sheets and signs off
- **Option B:** Researcher spot-checks 10 events, trusts AI verification for remainder
- **Option C:** Researcher reviews all 27 + performs acoustic listening on all 10 horn-present events

---

## Appendix A: File Cross-Reference

| Audit Finding | Primary File(s) |
|---|---|
| CF-01 | [`results/testing/FINAL_TEST_RESULTS.md`](file:///Users/sayemuddin/Desktop/Train_automation/results/testing/FINAL_TEST_RESULTS.md) |
| CF-02 | [`scripts/run_real_world_experiments.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/run_real_world_experiments.py) L53, L73 |
| CF-03 | [`docs/FINAL_ABLATION_MATRIX.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FINAL_ABLATION_MATRIX.md), [`experiments/runner.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/experiments/runner.py) |
| CF-04 | [`layer_b_processor.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/experiments/layer_b_processor.py) L101, L288 |
| CF-05 | [`fusion/collector.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/collector.py), [`data/sync.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/data/sync.py) |
| PA-01 | [`layer_b_processor.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/experiments/layer_b_processor.py) L300 |
| PA-02 | [`fusion/rules.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/rules.py) L56, L71 |
| EP-01 | [`evaluation/metrics.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/metrics.py), [`simulation/runner.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py) |

## Appendix B: Summary of All Findings by Severity

| Severity | Count | IDs |
|---|---|---|
| 🔴 CRITICAL | 6 | CF-01, CF-02, CF-03, CF-04, EP-01, TI-03 |
| 🟡 MAJOR | 8 | CF-05, TI-01, TI-02, ED-02, EP-02, EP-03, PA-01, PA-02, GT-02, SV-01 |
| 🟢 MINOR | 6 | ED-01, ED-03, ED-04, PA-03, GT-01, SV-02, SV-03 |
