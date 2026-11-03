# Researcher Decision Brief: Smallest Defensible Next Milestone

**Target Milestone:** Offline, Front-Camera Condition B0/B1/B2 Benchmark  
**Date:** 2026-10-25  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Repository HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Status:** INFORMATIONAL DECISION BRIEF — Requires explicit researcher decisions before any execution.

---

## Executive Summary

Following the full evidence reconciliation of repository governance, calibration logs, and readiness records, this brief provides the Principal Researcher with the necessary evidentiary basis to resolve the remaining blockers. 

The smallest scientifically defensible next research milestone is the **Offline Front-Camera Condition B0/B1/B2 Benchmark** (Single-Camera Vision, Audio, and Multimodal Fusion). Because front-camera video and audio are container-native ($\tau = 0.0\,\text{s}$ offset by hardware definition), this milestone bypasses cross-camera synchronization blockers while producing publication-quality empirical evaluations of the trained models and fail-closed decision logic.

---

## 1. R-SPLIT: Analysis Design & Dataset Limitations

### 1.1 Why Cross-Crossing Generalization Cannot Be Claimed
Every active recording in the 27-event evaluation corpus (`train_events/event_001`–`event_023`, `no_train_events/event_001`–`event_003`, `engine_events/event_001`) was captured at a **single physical railway crossing** in Bangladesh (`crossing_A`; see [`docs/RESEARCHER_READINESS_VERIFICATION_20261019T1456Z.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/RESEARCHER_READINESS_VERIFICATION_20261019T1456Z.md#L53-L61)).
* Track geometry, road approach angles, camera mounting positions, and background structures (concrete viaduct, red pedestrian bridge) are identical across all events.
* Background acoustic impulse response and environmental reverberation are shared.
* **Scientific Reality:** No partition of this dataset can establish cross-crossing generalization. Any claim of generalized multi-site safety performance would be scientifically invalid and easily falsified during peer review.

### 1.2 Why the Existing Candidate Split is Leakage-Prone
The unapproved candidate split proposal ([`docs/generated/final_readiness_20261019/CANDIDATE_EVENT_SPLIT_PROPOSAL.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_readiness_20261019/CANDIDATE_EVENT_SPLIT_PROPOSAL.json), 16 train / 6 val / 5 test) distributes the dataset across train, validation, and test sets using deterministic event-ID hashing:
* **Capture Session 1 (2026-09-14, 14:13–17:26 local):** Train 13 / Val 5 / Test 2.
* **Capture Session 2 (2026-10-04, 19:22–19:59 local):** Train 3 / Val 1 / Test 3.

Because events from both sessions appear across all three partitions, the candidate split leaks identical temporal and ambient conditions (same afternoon lighting, weather, and camera configurations) between training and evaluation.

### 1.3 Defensible Analysis Options (No Split Fabricated)

The researcher must select one of the following analytical framings for `phase12_event_split_decision.json`:

| Option | Framing & Methodology | Scientific Value | Limitations |
|---|---|---|---|
| **Option A (Recommended)** | **Full-Cohort Descriptive Benchmark (No Split)**<br>Evaluate all 27 events as an offline system characterization benchmark. | Evaluates full detection latency, kinematic state transitions, sensor health policies, and failure injection across all 27 real events. | No claim of statistical out-of-distribution generalization; reported strictly as a fixed-site operational benchmark. |
| **Option B** | **Two-Session Domain Contrast (Exploratory Shift)**<br>Partition Session 1 (20 events) vs. Session 2 (7 events). | Explores diurnal/sensor shift (iPhone daylight vs. iPad dusk/night). | Only two sessions exist (no 3rd group for validation); Session 2 has only 3 train events, confounding sensor change with cohort imbalance. |
| **Option C** | **Multi-Crossing Future Acquisition Gate**<br>Defer official evaluation until multi-crossing field data is gathered. | Enables legitimate out-of-distribution generalization claims. | Halts all current experimental milestones; requires physical site access, permissions, and safety review. |

---

## 2. R04-SCOPE: Camera Evaluation Scope

### 2.1 Proposed Primary Scope: Single-Camera Front (Conditions B0, B1, B2)
It is proposed that the primary official research evaluation be scoped to **Single-Camera Front**:
* **Condition B0:** Single-Camera Vision (Front Camera, YOLOv8n Viewpoint Classifier).
* **Condition B1:** Single-Camera Audio (Front Microphone, CompactTrainHornCNN Classifier).
* **Condition B2:** Container-Native Multimodal Fusion (Front Camera Vision + Audio).

**Scientific Justification:** Front-camera video and audio streams are multiplexed within the identical QuickTime container. The physical inter-sensor timing offset is $\tau = 0.0\,\text{s}$ by definition. This completely isolates the evaluation from cross-camera synchronization uncertainty, QuickTime clock drifts, and acoustic multipath ambiguities.

### 2.2 Dual-Camera Analysis as Separately Restricted Exploratory Option
Dual-camera fusion (Conditions B3, B4, B6, B7) must not be claimed for the full cohort (15–16 events remain uncalibrated or intractable). Instead, dual-camera analysis should be declared as a **separately restricted exploratory option**:
* Restricted strictly to the **11 baseline events** ([`docs/generated/final_readiness_20261019/r04/R04_EVENT_EVIDENCE.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_readiness_20261019/r04/R04_EVENT_EVIDENCE.json)) or **12 candidate events** ([`data/manifests/camera_sync_offsets_candidate.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/camera_sync_offsets_candidate.yaml)) meeting `CALIBRATION_SUPPORTED` criteria.
* Explicitly documented in the manuscript as a subset demonstration, not a full-system capability.

---

## 3. PROTOCOL: Premature-Opening Window Comparison

Per [`docs/PREMATURE_OPENING_DECISION_EVIDENCE.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/PREMATURE_OPENING_DECISION_EVIDENCE.md) and [`docs/generated/final_readiness_20261019/r04/PREMATURE_OPENING_V9_M4_COMPARISON.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_readiness_20261019/r04/PREMATURE_OPENING_V9_M4_COMPARISON.md), two documented endpoint definitions exist. Engineering cannot choose between them:

| Attribute | Protocol v9 (`t1_entry_to_t4_clearance`) | Protocol M4 (`first_blocked_to_t4_clearance`) |
|---|---|---|
| **Mathematical Interval** | $T_1 \le t < T_4$ | $t_{\text{blocked}} < t < T_4$ |
| **Failure Definition** | Gate issues opening command during $[T_1, T_4)$; replay predicate requires gate `OPENING`/`OPEN` and passage not blocked. | Gate issues opening command or transitions `blocked \to \text{not-blocked}` during $(t_{\text{blocked}}, T_4)$. |
| **Required Inputs** | Approved $T_1$ (front clock) and approved $T_4$ (back clock) on an aligned timeline. | Replay trace containing $t_{\text{blocked}}$ and approved $T_4$ (back clock). |
| **Cross-Camera Dependency** | **High:** Requires accepted R04 cross-camera synchronization offset to place $T_1$ and $T_4$ on a common master timeline. | **Low:** Can be evaluated directly on the back-camera replay trace without cross-clock fusion. |
| **Single-Camera (Front) Evaluability** | **Not evaluable:** $T_4$ is defined on the back-camera departure plane. | **Not evaluable:** $T_4$ is defined on the back-camera departure plane. |
| **Companion Metric** | None. Missing/censored boundaries exclude event from denominator. | Paired with **M5 (`never_protected`)**: events never blocked prior to $T_4$ are reported as M5, not M4 zero-failure successes. |
| **Implementation State** | Fully implemented in `simulation/runner.py`. | Trace logic implemented in `m4_premature_opening`; integration into runner pending. |

*Note on Single-Front Benchmark:* For a front-camera-only evaluation, neither v9 nor M4 premature opening to $T_4$ is evaluable because $T_4$ occurs off-screen on the back camera. Front-camera evaluations focus on **Approach Detection Latency ($T_1$)**, **Crossing Occupancy Presence ($T_2$)**, **False Alarm Rates on Controls**, and **Sensor Health State Transitions**.

---

## 4. Ground Truth and Authorization Architecture

### 4.1 The Four Stages of Evidence
To prevent procedural confusion, repository governance maintains strict distinctions across evidence stages:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. AI PROPOSALS (`data/ground_truth/proposals/*_proposal_v2.json`)    │
│    - Automated candidate timestamps generated by baseline models.      │
│    - NOT ground truth. Prohibited from serving as evaluation targets.   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼ (Human Video Inspection)
┌────────────────────────────────────────────────────────────────────────┐
│ 2. HUMAN-REVIEWED LABELS (`data/ground_truth/review_pilots/` or drafts)│
│    - Observed timestamps recorded by an allowlisted human reviewer.    │
│    - If captured during a pilot, marked `UNAPPROVED_PILOT` (ineligible)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼ (Promotion Gate & Media Re-Hash)
┌────────────────────────────────────────────────────────────────────────┐
│ 3. APPROVED GROUND TRUTH (`data/ground_truth/reviews/*_review.json`)   │
│    - Formally promoted Schema 8.1.0 records with promotion receipts.   │
│    - All 27 legacy reviews are currently INVALIDATED.                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼ (Final Hash-Bound Gate)
┌────────────────────────────────────────────────────────────────────────┐
│ 4. EVALUATION AUTHORIZATION (`EVAL-AUTH`)                              │
│    - Cryptographic binding over input manifest, policies, and labels.  │
│    - Grants execution permission for one official evaluation run.      │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Exact Steps to Validate Event Timestamps
1. **Adjudication Authorization (ADJ-AUTH):** Researcher records formal ADJ-AUTH naming the 27 events, allowlisted reviewer (`raihankabirrahu@gmail.com`), output directory, and review invariants.
2. **Human Timestamp Inspection:** Allowlisted reviewer inspects the 27 front/back video recordings. The reviewer verifies or corrects the candidate $T_1$, $T_2$, and tail clearance timestamps, recording physical left-censoring where trains are already present at $t=0.0\,\text{s}$.
3. **Dispute / Second Review Resolution:** Any boundary marked `UNCERTAIN` or listed in the Phase 11.6 Open Issue Register triggers second review per Decision 3(a). Clear boundaries receive a documented audit per Decision 3(c).
4. **Promotion Gate Execution:** Execute `promotion_gate.py` with full media re-hashing (`verify_sources=True`) to validate records against raw Layer-B media and generate promotion receipts.

---

## 5. Media Incident Status & Permitted Operations

### 5.1 Incident Summary & Uncertainty
On 2026-10-19, two official `evaluation status` command invocations were executed during readiness checks, exiting code 3. The operator reported concern that source-media bytes might have been read without authorization.
* **Verified:** Source video files on disk are bit-for-bit identical with the historical Layer-B inventory (54/54 matched, 0 mismatches).
* **Uncertainty:** Because `/tmp` output logs were purged by OS cleanup and macOS `/private/var/audit` returned permission denied, surviving evidence cannot prove or disprove whether media bytes were accessed in memory during those two specific runs.
* **Negative Evidence:** No checkpoints were modified, no media frames were saved, and tool logs show zero media access calls.

### 5.2 Existing Administrative Dispositions vs. Future Evaluation Commands
* On 2026-10-25, Lead Researcher Raihan Kabir Rahu formally confirmed [`ADMINISTRATIVE_DISPOSITION_R04_READ_ONLY_UNBLOCK_20261025`](file:///Users/sayemuddin/Desktop/Train_automation/docs/MEDIA_ACCESS_HOLD_RESOLUTION_PLAN.md#L130).
* **Scope Boundary:** This disposition applies **strictly and exclusively to Tier 1** (read-only visual frame extraction for 12 candidate calibration events using `scripts/extract_sync_review_frames.py`).
* **Remaining Hold:** Running future evaluation execution commands (Tier 2), LEG-EXEC writes (Tier 3), or timing-pilot activations (Tier 4) remains **HELD AND PROHIBITED** until the researcher extends the disposition or formally closes the incident for evaluation execution.

---

## 6. Benchmark Readiness Checklist

Before an official evaluation command can execute with exit code 0, the following artifacts and bindings must be verified:

- [ ] **Data Integrity:** 54 Layer-B `.mov` and audio files verified against inventory SHA-256 (`5585e22ecc7841e2cca4d8e56b9d61999e252e1efaf5dfa6e57d81471b809a56`).
- [ ] **Ground Truth Labels:** 27 approved Stage-2.1 review records in `data/ground_truth/reviews/` with valid promotion receipts.
- [ ] **Frozen Configuration:** `configs/frozen_experiment_v1.yaml` (canonical hash `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`).
- [ ] **Decision Policy:** `configs/decision_policy_v1.yaml` (canonical hash `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575`).
- [ ] **Incident Disposition:** Formal Tier-2 evaluation execution carve-out recorded by researcher.
- [ ] **Research Decision Records:**
  - [ ] `data/manifests/phase12_event_split_decision.json` (schema `phase12-event-split-decision/1`)
  - [ ] `data/manifests/phase12_r04_scope_decision.json` (schema `phase12-r04-scope-decision/1`)
  - [ ] `data/manifests/phase12_protocol_decision.json` (schema `phase12-protocol-decision/1`)
- [ ] **Input Manifest:** `data/manifests/phase12_evaluation_inputs.json` generated by `manifest_builder.py` binding all live decision and source hashes.
- [ ] **Live Gate Verification:** `railway_detection evaluation status` reports all 7 bindings present and `ready: true`.
- [ ] **EVAL-AUTH:** Formal hash-bound authorization recorded by lead researcher.

---

## 7. Researcher Decision Register

| Decision ID | Core Question | Available Options | Evidence Needed | Responsible Decision-Maker | What Remains Blocked |
|---|---|---|---|:---:|---|
| **R-SPLIT** | How should the 27 events be partitioned given the single-crossing constraint? | **(A)** Full-cohort descriptive benchmark (no split).<br>**(B)** Two-session exploratory contrast.<br>**(C)** Defer until multi-site field data acquired. | Stated analytical claim and limitation text. | Lead Researcher (`raihankabirrahu@gmail.com`) | Manifest construction, EVAL-AUTH, official evaluation execution. |
| **R04-SCOPE** | What camera modalities and events are in scope for primary evaluation? | **(A)** Single-Camera Front (B0/B1/B2) primary; dual-camera restricted exploratory.<br>**(B)** Dual-camera on 11 baseline events.<br>**(C)** Dual-camera on 12 events (with event 010). | Selected camera modes per event in `accepted_sync_events`. | Lead Researcher (`raihankabirrahu@gmail.com`) | Multi-camera metric evaluation, manifest builder. |
| **PROTOCOL** | Which primary endpoint defines premature gate opening? | **(A)** v9 (`t1_entry_to_t4_clearance`).<br>**(B)** M4 (`first_blocked_to_t4_clearance`). | Verbatim selection in `phase12_protocol_decision.json`. | Lead Researcher (`raihankabirrahu@gmail.com`) | Safety metrics (premature opening rate, excess closure). |
| **ADJ-AUTH** | Shall formal human ground-truth annotation review begin? | **(A)** Authorize review under direct researcher execution ($\ge 30\,\text{s}$ floor).<br>**(B)** Execute timing pilot first to calibrate D1 numbers.<br>**(C)** Maintain review hold. | Completed ADJ-AUTH record naming reviewer and scope. | Lead Researcher (`raihankabirrahu@gmail.com`) | Ground-truth review, Stage-2.1 promotion, readiness gate. |
| **INCIDENT-T2** | Shall the media hold be resolved for Tier-2 evaluation execution? | **(A)** Extend administrative disposition to Tier 2 (accept residual risk).<br>**(B)** Maintain evaluation hold until BSM audit logs accessible. | Written attestation accepting residual risk. | Lead Researcher (`raihankabirrahu@gmail.com`) | Running evaluation commands and official inference. |
| **D3(c)** | What audit mechanism governs clear-boundary annotations? | **(A)** 100% researcher single-pass skim.<br>**(B)** Random 20% spot-check audit.<br>**(C)** Peer reviewer audit. | Documented sampling rule. | Lead Researcher (`raihankabirrahu@gmail.com`) | Stage-2.1 promotion receipt issuance. |

---

*Brief prepared by agent synthesis on 2026-10-25. Strictly informational. No authorizations, decisions, labels, or evaluations were executed or implied.*
