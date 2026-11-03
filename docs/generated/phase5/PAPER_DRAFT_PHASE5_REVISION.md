> **MISSION 10 CORRECTION NOTICE (2026-11-02).** This document was written by the Phase 5 implementation
> agent before two failed independent audits (`INDEPENDENT_AUDIT_FAIL`, `REMEDIATION_AUDIT_FAIL`). Statements
> below that contradict `MISSION_10_RECOVERY_REPORT.md` are **superseded** by it. Known-wrong claims in this
> file are corrected in place or listed in `MISSION_10_DOCUMENT_RECONCILIATION.md`. In particular: file hashes
> are not asserted here (they change with every edit; use `MISSION_10_ARTIFACT_MANIFEST.json`), "Remaining Risk:
> None" statements are withdrawn, and no authorization, receipt or ground-truth approval exists or is implied.
> The two Sonnet audit reports are unmodified and remain the independent record.

# An Auditable Independent-Camera Descriptive Benchmark for Level-Crossing Protection: Outcome Definitions, Governance, and Provenance

> **MANUSCRIPT REVISION DRAFT — PHASE 5**  
> **Status:** METHODOLOGY AND SPECIFICATION REVISED — EMPIRICAL RESULTS PENDING AUTHORIZED EVALUATION  
> **Repository Baseline:** `/Users/sayemuddin/Desktop/Train_automation`  
> **Execution Agent:** Not independently verified; agent identity is not treated as provenance evidence.  
> **Author block:** `[AUTHOR IDENTITIES AND CONTRIBUTIONS — RESEARCHER TO COMPLETE]`  
> **AI-use disclosure draft:** AI systems assisted with software drafting and documentation; all scientific decisions, approvals, annotations, adjudications and execution authorizations remain researcher-controlled and are not claimed here.  
> **Date:** 2026-11-02  
> **Notice:** All empirical evaluation numbers are held as `[RESULTS PENDING AUTHORIZED EVALUATION]` pursuant to research governance decisions RD-051–055 and Section 9 of the Master Execution Prompt. No historical experimental values are presented as Phase 5 evaluation outputs.

---

## Abstract

Roadside multimodal sensing is investigated as a potential approach to railway-crossing monitoring; cost-effectiveness and deployment suitability are not evaluated here. This paper specifies an auditable descriptive-evaluation framework for a 27-event multimodal recording cohort from a single fixed crossing in Bangladesh (`crossing_A`). It formalizes fail-closed outcome contracts: premature opening (M4) over the strict open protection interval $(t_{\text{blocked}}, T_4)$, never-protected failure (M5) requiring full $[0, T_4)$ temporal observation, and missed-train detection (MTR) conditioned on physical lead-in feasibility screening. It encodes a proposed, not-yet-adopted second-review policy, a model-independence firewall, and isolation of engine movements and negative controls from pooled metrics. Because formal real-data evaluation and human adjudication remain pending researcher authorization, all empirical evaluation figures remain pending placeholders. The contribution is a methodology and engineering specification, not an evaluated real-world system.

---

## 1. Introduction and Research Motivation

Highway-rail crossings are an important safety context for this study. Specific national collision rankings, crossing counts, and comparative infrastructure costs are outside the evidence audited here and are therefore not asserted. The study focuses on an auditable software and evaluation methodology rather than an economic or safety-impact estimate.

Roadside multi-sensor systems combine optical cameras, microphones and learned perception models. This draft treats the following as methodological risks to be tested, not as frequency claims about the literature:
1. **Survivorship and Replay Truncation Bias:** Replay simulations that crash or terminate before train clearance ($T_4$) are often treated as "no premature opening detected," erroneously awarding safety credit to incomplete observations.
2. **Left-Censoring Distortion:** Field recordings frequently begin when the approaching train is already visible or within the critical approach zone. Treating the recording onset as train appearance severely distorts measured lead times and improperly penalizes system latency.
3. **Independent Clock Drift:** Multi-camera setups deployed without hardware genlock or Network Time Protocol (NTP) synchronization exhibit non-stationary inter-camera offsets. Merging unsynchronized timestamps into composite multi-camera metrics introduces severe spatial-temporal artifacts.
4. **Generalization Overclaiming:** Descriptive observations from a single crossing should not be presented as a generalizable safety proof or deployment-readiness assertion.

To address these vulnerabilities, this paper specifies an auditable, fail-closed descriptive evaluation framework. We define exact mathematical boundaries for crossing safety outcomes, implement strict human-review provenance, and enforce per-metric evaluable denominators.

---

## 2. Research Questions

- **RQ1 (Outcome Formalization & Auditability):** Can barrier protection outcomes—specifically premature opening (M4) and never-protected failure (M5)—be mathematically bounded such that incomplete or truncated replays are strictly classified as non-evaluable rather than safe?
- **RQ2 (Independent-Camera Decoupling):** How can front-facing and back-facing roadside cameras be decoupled into distinct, reproducible evaluation streams without relying on uncalibrated inter-camera clock synchronization?
- **RQ3 (Descriptive Performance Under Frozen Policy):** *Conditional on authorized human ground truth and execution authorization:* What are the exact descriptive operating characteristics of the frozen multimodal pipeline across the fixed-site cohort? **[RESULTS PENDING AUTHORIZED EVALUATION]**
- **RQ4 (Empirical Bounds of Small-Cohort Studies):** What are the rigorous statistical and methodological limits of drawing inferences from a 23-train, single-site recording population?

---

## 3. Study Design and Population

### 3.1 Single-Site Descriptive Scope
This investigation is strictly designed as a **single-site, fixed-crossing descriptive study** conducted at `crossing_A`. In accordance with Researcher Decisions RD-051 through RD-053:
- No train/validation/test split is asserted; no random splitting is performed.
- No cross-site generalization claims are made.
- No operational safety or commercial deployment readiness is claimed.
- The perception models, neural weights, and fusion decision policy remain entirely frozen.

### 3.2 Recording Population
The evaluation population comprises exactly 27 recording events captured at `crossing_A`:
- **Train Events (23 events):** Front and back video streams capturing passenger and freight movements (`train_events/event_001` through `train_events/event_023`).
- **No-Train Events (3 events):** Negative-control recordings capturing baseline road vehicle traffic and pedestrians without rail traffic (`no_train_events/event_001` through `no_train_events/event_003`, approx. 120.8 camera-stream-seconds total).
- **Engine-Only Event (1 event):** A single locomotive-only movement (`engine_events/event_001`). Per RD-022, engine movements exhibit distinct kinematic and acoustic profiles and are strictly isolated into a separate case study to prevent denominator contamination.

### 3.3 Cohort-Qualified Identity
To resolve historical ambiguities where event numbers collided across cohorts, all events are uniquely identified using canonical cohort-qualified identifiers: `train_events/event_001` through `train_events/event_023`, `no_train_events/event_001` through `no_train_events/event_003`, and `engine_events/event_001`. Bare event numbers (e.g., `event_001` without cohort prefix) are strictly rejected by the tooling.

---

## 4. Human Ground-Truth Governance and Provenance

Ground truth for safety-critical boundaries cannot rely on model predictions or unverified single-observer notes.

### 4.1 Stage-2.1 Protocol and Schema
Ground truth is governed by Ground Truth Protocol v7.1.1 and the Stage-2.1 review schema:
- **Canonical Landmark Definitions:**
  - $T_0$: Locomotive first visible in camera field of view.
  - $T_1$: Locomotive nose enters the approach danger zone.
  - $T_2$: Crossing occupancy start (*DEFERRED per RD-006; excluded from primary Phase 5 evaluation benchmarks*).
  - $T_3$: Lead locomotive unit clears the crossing quadrant.
  - $T_4$: Last car tail completely clears the crossing conflict area.
  - $T_{\text{clear}}$: Scene returned to idle state.
- **Temporal Snapping:** Timestamps are strictly snapped to a one-microsecond ($1\,\mu\text{s}$) grid; all mathematical comparisons are strict.

### 4.2 Proposed Multi-Reviewer Risk-Based Adjudication (RD-043; NOT ADOPTED)
RD-043 and `GOV-REVIEW-SECOND-REVIEW-TRIGGERS` remain proposals pending researcher decision. The implementation currently applies the following fail-closed proposal for engineering tests; this text is not a formal approval. Under the proposal, a single-reviewer signoff is insufficient for high-risk events:
1. **Proposed trigger set:** The implementation tests explicit reviewer flags, uncertain boundaries, engine T3/T4 interpretation, missing/inconsistent media hashes, and corrections from the AI candidate. `FRONT_BACK_CONFLICT` is not mechanically evaluable and requires a reviewer flag. Censoring alone is not a trigger; the deferred duration-floor decision is not a trigger.
2. **Disagreement handling:** The implementation applies no timestamp tolerance and does not clear disagreement without an adopted adjudication format. Formal adoption of RD-043/RD-045 remains a researcher decision.
3. **Model Firewall:** Human reviewers are structurally prohibited from viewing model predictions during annotation. Automated agents (`gemini_annotator`, `researcher_agent`, etc.) are hard-blocked from authoring ground truth.

---

## 5. System Architecture and Experimental Conditions

### 5.1 Multimodal Pipeline and Cadence Decoupling
The evaluated system consists of:
- **Vision Subsystem:** Ultralytics YOLOv8n object-detector configuration is represented in the engineering artifacts; native front/back frame-rate claims are not asserted here because they are not independently verified in this audit. Frame dimensions and acquisition details remain configuration/data-provenance items for authorized evaluation.
- **Audio Subsystem:** Log-mel spectrogram feature extractor operating on 1.0 s audio windows with 0.5 s hop cadence, feeding a PyTorch 1D/2D CNN acoustic classifier detecting locomotive engine rumble, horn, and rail clatter.
- **Evidence Collector & Decision Engine:** Multi-source evidence tracker evaluating temporal persistence and sensor health. Actuation is evaluated at a discrete 5 Hz controller tick cadence ($\Delta t = 0.2\,\text{s}$, from `timing.tick_s: 0.2` in `configs/frozen_experiment_v1.yaml`). The decision engine tick rate is strictly decoupled from the sensory acquisition frame rates. Actuation policy is governed by `configs/decision_policy_v1.yaml` (SHA-256: `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575`).

### 5.2 Audio-Only Operational Boundary (RD-030)
Under the frozen policy, audio evidence alone cannot actuate the barrier. Audio serves exclusively as supporting evidence to validate or accelerate visual detections. Consequently, the audio-only experimental condition (`B1`) is evaluated for acoustic detection latency and presence descriptors only; it cannot produce gate-level lead-time or closure outcomes.

### 5.3 Decoupled Camera Roles
- **Front Camera (`B0`, `B1`, `B2`):** Primary sensor for train approach detection, computing warning lead time and MTR at $T_1$.
- **Back Camera (condition names `B0_back` / `B2_back` are PROVISIONAL, DEC-B05 PENDING; not implemented in the cache-only engine; the official independent-camera producer scores a separate `back` system):** Primary sensor for train clearance detection, computing M4 premature opening and M5 never-protected outcomes at $T_4$.
- **Fused Dual-Camera (`R04`):** Proposed exploratory multi-camera condition confined by the pending R04 decision; calibration support is not claimed as established in this draft.

---

## 6. Metric Formulations and Boundary Conditions

### 6.1 M4 — Premature Gate Opening (Primary Safety Metric)
M4 measures whether a retained replay witnesses an unblocked/opening state in the implemented protection interval. Let $t_{\text{blocked}}$ be the earliest retained simulation step with passage blocked before the approved T4 boundary; this is an operational replay definition, not a claim of continuous physical occupancy between samples.
- **Evaluation Interval:** Open interval $(t_{\text{blocked}}, T_4)$.
- **Witnessed Premature Opening:** Any retained replay step $t \in (t_{\text{blocked}}, T_4)$ where barrier status is unblocked (`OPENING` or `OPEN`).
- **Complete Replay Prerequisite:** The replay must observe all steps up to $T_4$ ($\text{last\_step} \ge T_4$). If a replay ends before $T_4$ without witnessing a violation, it is strictly classified as `NOT_EVALUABLE` (`replay_ended_before_T4`)—it is **never** counted as safe.
- **Interior Steps Requirement:** At least one simulation step must fall inside $(t_{\text{blocked}}, T_4)$. If zero steps fall inside, the event is `NOT_EVALUABLE` (`no_steps_in_protection_interval`).

### 6.2 M5 — Never-Protected Failure (Companion Metric)
M5 identifies events where the barrier failed to close at all during a train passage:
- **Full Coverage Requirement:** The replay must begin at time zero ($t_{\text{start}} = 0$) and extend to at least $T_4$.
- **Never Protected:** Zero blocked steps observed throughout $[0, T_4)$.
- **Late Replay Guard:** Any replay starting at $t > 0$ with zero blocked steps is classified as `NOT_EVALUABLE` (`replay_started_late`), because protection may have occurred during unobserved time.

### 6.3 MTR — Missed Train at Approach (Secondary Metric)
MTR evaluates whether the barrier closed before the train reached the approach danger zone ($T_1$):
- **Physical Lead-In Screen:** To prevent unfair penalties due to left-censored recording starts, an event is evaluable for MTR only if the available observation window before $T_1$ equals or exceeds the minimum physical block latency $\tau_{\min}$. If available lead-in is $< \tau_{\min}$, the event is excluded under `insufficient_lead_in`.

---

## 7. Evaluation Results (Placeholders Pending Authorized Execution)

<!--RESULTS-TABLES-->
### 7.1 Primary and Secondary Safety Outcomes Across Replay Conditions

| Condition Identifier | Stream / Scope | Evaluable $N$ | Premature Opening M4 Count | Never Protected M5 Count | MTR (Feasibility Screen) | Median Warning Lead Time (s) | Median Clearance Latency (s) |
|---|---|---|---|---|---|---|---|
| **B0** (Front Vision) | Front Camera | `[PENDING]` | N/A (Clearance outside FOV) | N/A | `[PENDING]` | `[PENDING]` | N/A |
| **B1** (Front Audio) | Front Audio | `[PENDING]` | N/A (Audio cannot actuate) | N/A | N/A (RD-030) | N/A | N/A |
| **B2** (Front Vision+Audio) | Front Camera | `[PENDING]` | N/A (Clearance outside FOV) | N/A | `[PENDING]` | `[PENDING]` | N/A |
| **B0_back** (Back Vision) | Back Camera | `[PENDING]` | `[PENDING]` | `[PENDING]` | N/A (Approach outside FOV) | N/A | `[PENDING]` |
| **B2_back** (Back Fused; provisional name, not adopted, not implemented) | Back Camera | `[PENDING]` | `[PENDING]` | `[PENDING]` | N/A | N/A | `[PENDING]` |
| **R04** (Exploratory Fused) | 11-Event Dual | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` |

*Note: All values above are pending execution under authorized Stage C governance.*

---

### 7.2 Non-Train Control and Engine Movement Case Studies

| Evaluation Cohort | Event Identifier | Evaluated Exposure | Gate Actuation / False Alarm Count | Notes / Status |
|---|---|---|---|---|
| **Negative Control** | `no_train_events/event_001` | `[PENDING]` s | `[PENDING]` | Road vehicle baseline |
| **Negative Control** | `no_train_events/event_002` | `[PENDING]` s | `[PENDING]` | Pedestrian baseline |
| **Negative Control** | `no_train_events/event_003` | `[PENDING]` s | `[PENDING]` | Baseline traffic |
| **Engine Movement Case Study** | `engine_events/event_001` | `[PENDING]` s | `[PENDING]` | Isolated from train pooling; condition/decision provenance remains pending |

---

## 8. Discussion and Methodological Limitations

1. **Replay Start and Censoring Sensitivity:** As formalized in Section 6, the M5 metric requires full temporal coverage $[0, T_4)$. In field recordings where camera operators began recording after the locomotive was already visible, MTR and lead-time calculations must be carefully quarantined to avoid conflating recording artifacts with automation failures.
2. **Discrete Controller Tick Cadence:** Pipeline decision steps occur at discrete controller tick intervals ($\Delta t = 0.2\,\text{s}$ / 5 Hz). While our mathematical contracts enforce strict open intervals, physical barrier behavior between steps remains unobserved.
3. **Absence of Hardware Genlock:** Roadside installations in rural developing regions often lack synchronization cables between cameras. Decoupling front and back camera responsibilities (front for approach, back for clearance) is mathematically robust, but true end-to-end multi-camera tracking requires synchronized time bases.
4. **Descriptive Nature of Single-Site Data:** The 27-event corpus from `crossing_A` provides valuable empirical evidence regarding multi-modal sensor fusion dynamics in South Asian rail operating environments, but does not constitute a statistical warranty of cross-site generalization.

---

## 9. Claim-to-Evidence Matrix

| Manuscript Section / Claim | Evidence Source in Repository | Verification Status |
|---|---|---|
| Single-site descriptive study design | Decision materials / protocol draft | **PROPOSED / NOT INDEPENDENTLY VERIFIED** |
| 27-event cohort composition (23 train, 3 no-train, 1 engine) | Inventory metadata and synthetic-safe source checks | **SUPPORTED AS METADATA; NOT A PHASE 5 RESULT** |
| Decision policy hash binding (`c87c1432f473...`) | `configs/decision_policy_v1.yaml` (recomputed SHA-256) | **SUPPORTED FOR CURRENT WORKING TREE** |
| Fail-closed M4/M5 mathematical definitions | `src/railway_detection/evaluation/metrics.py` | **SUPPORTED BY SYNTHETIC ENGINEERING TESTS** |
| Reviewer allowlist and blocklist enforcement | `second_review.py` and focused tests | **SUPPORTED BY FOCUSED TESTS; POLICY NOT ADOPTED** |
| Empirical M4, M5, MTR numeric performance values | Real-data evaluation pipeline output | **PENDING AUTHORIZED EVALUATION** |
| Human ground truth promotion receipts | `data/ground_truth/stage21_promotion_receipt.json` | **PENDING RESEARCHER EXECUTION** |

---

## 10. Literature and Reference Verification Report

| Citation | Claimed Source / Citation | Verification Finding | Recommendation |
|---|---|---|---|
| Ref [1] | Jocher et al. (2023), Ultralytics YOLOv8 | **UNVERIFIED IN THIS AUDIT** | Researcher to complete external bibliography check |
| Ref [2] | Hershey et al. (2017), CNN architectures for audio | **UNVERIFIED IN THIS AUDIT** | Researcher to complete external bibliography check |
| Ref [3] | Wilson (1927), Binomial score intervals | **UNVERIFIED IN THIS AUDIT** | Researcher to complete external bibliography check |
| Ref [4] | Bangladesh Railway Information Book (2020) | Unverified in repository | Flag for researcher verification |
| Ref [5]–[9] | Specific sensor fusion and level-crossing papers | Unverified in repository | Mark as pending independent bibliography audit |

---

## 11. Reproducibility and Artifact Manifest

The current working-tree implementation and its limitations are described below; this is not a claim of a committed release or completed real-data evaluation:
- **Repository snapshot:** HEAD `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` at the Mission 12 baseline; current working tree has 22 modified tracked files and 379 untracked status entries (snapshot-specific, not a preservation certificate).
- **Environment observed:** Python 3.11.15; PyTorch 2.13.0; Ultralytics 8.4.121; ruff 0.16.3; pytest 9.1.1; macOS 26.6.2, Darwin kernel 25.6.0 ARM64.
- **Safe synthetic runner:** 1,802 tests passed across 92 files in the verified safe set; 21 checkpoint/processed-data/raw-media tests remain excluded and unexecuted. This is not a Phase 5 empirical result.
- **Authorization status:** No AUTH-MEDIA-ACCESS, AUTH-DESCRIPTIVE-EVAL-EXEC, EVAL-AUTH, promotion receipt or human-review approval exists in the repository.
- **Model/checkpoint hashes:** `NOT_VERIFIED — REQUIRES AUTHORIZED ACCESS`; no protected checkpoint was opened or hashed during this audit.
- **Dataset and ground-truth provenance:** metadata references are documented in the repository; real-data provenance and approval remain `PENDING AUTHORIZED EVALUATION`.
- **Known limitations:** Python-level guards are not an OS sandbox; unexecuted protected tests, pending RD-043/DEC-B05 decisions, untracked working-tree packages, and absent authorizations prevent claims of reproducible real-data evaluation.
