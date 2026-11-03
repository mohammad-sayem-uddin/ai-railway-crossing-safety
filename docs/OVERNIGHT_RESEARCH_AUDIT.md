# Overnight Research Engineering Audit: Repository Baseline & Governance Status

**Document Version:** 1.0.0  
**Audit Timestamp:** 2026-10-25T16:56:00Z  
**Executing Agent:** Autonomous Research-Engineering Pair  
**Repository Working Directory:** `/Users/sayemuddin/Desktop/Train_automation`  
**Git HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Operational Status:** Strictly Informational Audit — Read-Only Static Verification. Zero Media Access. Zero Restricted Workflows. Worktree Preserved.

---

## 1. Executive Summary

This audit establishes the baseline technical and governance reality of the Train Gate Automation research repository prior to executing overnight research-engineering tasks. The mission goal is to advance scientific rigor, auditability, reproducibility, and paper-readiness without manufacturing unverified metrics, claiming physical safety certification, or breaching repository governance constraints.

---

## 2. Active Governance Restrictions

The following operational and security restrictions remain active across the repository:

1. **Media Access Hold (Strict Byte-Level Lockdown):**
   - *Authority:* [`docs/MEDIA_ACCESS_HOLD_RESOLUTION_PLAN.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/MEDIA_ACCESS_HOLD_RESOLUTION_PLAN.md) and [`docs/MEDIA_ACCESS_INCIDENT_INVESTIGATION_20261020.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/MEDIA_ACCESS_INCIDENT_INVESTIGATION_20261020.md).
   - *Scope:* Direct and indirect opening, decoding, hashing, reading, previewing, playing, transcoding, or extracting audio from raw source media files (`.mov`, `.mp4`, `.wav`) is strictly prohibited.
   - *Current State:* The historical media access incident investigation concluded with an administrative disposition recommendation, but formal researcher ratification remains pending. The media access hold remains in force.
2. **Evaluation & Readiness Command Prohibition:**
   - *Scope:* Execution of `railway_detection evaluation status`, `Phase12EvaluationRunner.run_official()`, `scripts/run_phase5_full_inference.py`, `scripts/run_real_world_experiments.py`, or any legacy CLI evaluation command is blocked.
   - *Rationale:* Running official evaluation without signed researcher authorizations (`EVAL-AUTH`, `ADJ-AUTH`) violates repository integrity controls.
3. **Ground-Truth Promotion & Receipt Lockdown:**
   - *Scope:* Generating synthetic ground truth, self-promoting candidate proposals to Stage-2.1 approved status, or forging reviewer signatures is prohibited.
   - *Current State:* All 27 event annotation proposals remain classified as `UNAPPROVED_CANDIDATE_PROPOSAL`.
4. **Timing-Pilot & LEG-EXEC Restrictions:**
   - *Scope:* Timing-pilot workflows and legacy execution runners (`scripts/run_leg_exec.py`) are deactivated and must not be triggered.

---

## 3. Decisions Awaiting the Principal Researcher

Scientific and governance decisions currently blocking an authorized evaluation:

| Decision ID | Domain | Pending Question | Documented Options | Impact if Unresolved |
| :--- | :--- | :--- | :--- | :--- |
| **R-SPLIT** | Scientific Design | How should the 27-event corpus be framed for evaluation? | **Option A (Recommended):** Full-Cohort Descriptive Benchmark (No Split).<br>**Option B:** Two-Session Domain Contrast.<br>**Option C:** Multi-Crossing Acquisition Gate. | Official evaluation runner is hardcoded to a 3-way split; descriptive cohort requires researcher authorization. |
| **R04-SCOPE** | Calibration & Sensors | What camera configuration governs primary benchmark evaluation? | **Primary:** Single-Camera Front (B0, B1, B2; $\tau = 0.0\,\text{s}$).<br>**Exploratory:** Dual-Camera (B3, B4) restricted to 11–12 calibrated events. | Prevents unverified zero-offset cross-camera temporal fusion across 15 uncalibrated events. |
| **PROTOCOL** | Metric Definition | Which premature opening definition governs evaluation? | **v9:** $[T_1, T_4)$ window (requires $T_1$ and $T_4$).<br>**M4:** $(t_{\text{blocked}}, T_4)$ window (requires $T_4$, paired with M5). | Premature opening cannot be calculated officially under either protocol until selected; non-computable on front-only runs. |
| **ADJ-AUTH** | Ground Truth | Who verifies candidate timestamps on `camera_front.mov`? | Human inspection of candidate timestamps by an allowlisted reviewer (`authorized_reviewers.json`). | Blocks promotion of candidate proposals to `data/ground_truth/phase12_ground_truth.json`. |
| **INCIDENT-DISP** | Governance | Ratification of Media Access Incident Closeout. | Ratify administrative disposition or order independent re-audit. | Maintains Media Access Hold on source media bytes. |

---

## 4. Authoritative vs. Candidate Artifact Inventory

| Category | Authoritative Artifacts (Verified & Immutable) | Candidate / Non-Authoritative Artifacts (Provisional) |
| :--- | :--- | :--- |
| **Model Weights** | • YOLOv8n Vision (`experiments/vision/39f402dfe460/checkpoints/weights/best.pt`; SHA-256: `3f5bb5b2...`)<br>• CompactTrainHornCNN V3 (`experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`; SHA-256: `ea1bb81d...`) | • Legacy audio v1/v2 models.<br>• Unfrozen exploration checkpoints. |
| **Configuration** | • `configs/frozen_experiment_v1.yaml` (Canonical SHA-256: `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`) | • Unverified runtime parameter modifications. |
| **Ground Truth** | • None. `data/ground_truth/phase12_ground_truth.json` is **absent**. | • Candidate manifest: `data/ground_truth/snapshots/candidate_annotation_manifest_20261012.json`<br>• 27 proposal JSONs in `data/ground_truth/proposals/` (`UNAPPROVED_CANDIDATE_PROPOSAL`). |
| **Calibration** | • None officially accepted. | • Candidate calibration manifest: `data/manifests/camera_sync_offsets_candidate.yaml`<br>• R04 investigation candidate closeout (12 supported, 8 ambiguous, 7 provisional). |
| **Evaluation Manifest** | • None. `data/manifests/phase12_evaluation_inputs.json` is **absent**. | • Unapproved split proposals in `docs/generated/`. |
| **Evaluation Outputs** | • None official. | • Diagnostic results in `results/experiments/` (generated without approved GT). |

---

## 5. Governance Bypasses in Existing Diagnostic Scripts

Static code inspection reveals that the repository's research diagnostic scripts bypass formal evaluation safeguards:

1. **`scripts/run_real_world_experiments.py`:**
   - **Split Bypass:** Discovers and runs all 27 events across `data/raw/layer_b/v2/` without checking partition records or verifying `phase12_event_split_decision.json`.
   - **Ground-Truth Bypass:** Computes Wilson confidence intervals and signs tests directly against simulation steps without loading approved Stage-2.1 ground truth.
   - **Cross-Camera Fusion Violation:** Ingests unaligned front and back camera records into `build_multimodal_frames()` with `sync_aligner=None`. Raises fatal `TimingIntegrityError` unless `allow_unverified_zero_offset: true` is explicitly enabled in config.
   - **Documentation Overwrite:** Overwrites `docs/REAL_WORLD_EXPERIMENT_REPORT.md` on every run.
2. **`scripts/run_phase5_full_inference.py`:**
   - **Media-Access Hold Breach:** Lines 324, 343, 361 have `use_cache=False` hardcoded. Execution invokes `frame_generator()` to decode all 54 raw video files and extract audio tracks, directly breaching the Media Access Hold.

---

## 6. Stale, Contradictory, or Inconsistent Documentation

1. **Legacy B2 Definition in Diagnostic Runner vs. Production Replay:**
   - `src/railway_detection/experiments/runner.py` (lines 250, 420–492) defines B2 as "Dual Vision + Audio" simulated under a stateless 3-frame persistence baseline that opens immediately when detections drop.
   - `scripts/run_phase5_full_inference.py` (lines 401–415) and `src/railway_detection/evaluation/replay_producer.py` (lines 275–276) define B2 as container-native front multimodal fusion executed via `EventSimulationRunner`.
2. **Table 1 Denominator in `docs/B0_B1_B2_METRIC_SPECIFICATION.md`:**
   - Table 1 lists `Eligible Events: 23 | Evaluable Events: 23` for B0, B1, and B2.
   - In `train_events/event_005`, $T_1$ is `null` (`candidate_observable: false`) because the train occupied the crossing before recording started. Under `metrics.py` (lines 305–309, 421–422), `missed_train` returns `None`. The true evaluable denominator is at most **22**, not 23.
3. **Cohort Accounting in `docs/B0_B1_B2_METRIC_SPECIFICATION.md`:**
   - Section 7.1 accounts for 26 events (23 train, 3 no-train), omitting `engine_events/event_001` from the tabular reporting plan.
4. **Overstated Claims in `docs/REAL_WORLD_EXPERIMENT_REPORT.md`:**
   - Report references 21 events (outdated cohort size), claims "H2 & H4 Supported (0.0% premature opening)", and uses the term "fail-safe" without physical SIL 4 certification.

---

## 7. Permitted Safe Autonomous Activities (Zero Media Access)

The following high-value research-engineering tasks can proceed safely:
- Correcting documentation defects in `docs/B0_B1_B2_METRIC_SPECIFICATION.md`.
- Authoring the comprehensive Metric-to-Code Evidence Matrix (`docs/B0_B1_B2_METRIC_EVIDENCE_MATRIX.md`).
- Creating the B0/B1/B2 Architectural Separation Audit (`docs/B0_B1_B2_ARCHITECTURE_AUDIT.md`).
- Formulating the Diagnostic Harness Safety Audit (`docs/DIAGNOSTIC_HARNESS_STATIC_SAFETY_AUDIT.md`).
- Auditing dataset and candidate annotation quality (`docs/DATASET_ANNOTATION_QUALITY_AUDIT.md`).
- Reviewing scientific claim defensibility and experiment design (`docs/B0_B1_B2_EXPERIMENT_DESIGN_REVIEW.md`).
- Drafting the descriptive paper skeleton (`docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`).
- Structuring the literature review plan (`docs/LITERATURE_REVIEW_PLAN.md`).
- Compiling the overnight researcher decision register (`docs/RESEARCHER_DECISION_REGISTER_OVERNIGHT.md`).
- Auditing repository-wide documentation consistency (`docs/DOCUMENTATION_CONSISTENCY_AUDIT.md`).
- Designing the cache-only replay interface and test plans (`docs/CACHE_ONLY_REPLAY_DESIGN.md`, `docs/B0_B1_B2_TEST_PLAN.md`).
- Synthesizing the actionable multi-stage roadmap (`docs/OVERNIGHT_TO_NEXT_MILESTONE_ROADMAP.md`).

---

## 8. Unverifiable Repository Claims (Static Constraints)

The following claims cannot be verified from available code without violating non-negotiable safety rules:
1. **Visual Accuracy of Candidate Bounding Boxes / Timestamps:** Verifying whether locomotive cowcatchers actually crossed the turnout frog frog at candidate $T_1$ requires video playback, which is prohibited under the Media Access Hold.
2. **Auditory Authenticity of Horn Detections:** Confirming that spectral prominence peaks correspond to audible train horn blasts rather than road traffic or wind noise requires audio listening, which is prohibited.
3. **True Train Arrival Times:** All 23 train events are left-censored ($T_0 \le 0.0\,\text{s}$); physical arrival times cannot be established from the video recordings.
4. **Historical Access Logs:** Exact past workstation user interactions that triggered the historical media incident cannot be reconstructed beyond the existing forensic audit records.
