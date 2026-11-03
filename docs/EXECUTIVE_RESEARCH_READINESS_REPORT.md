# Executive Research Readiness Report

**Date:** 2026-10-12 / 2026-10-13  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Git Commit HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Authority:** Autonomous Overnight Research Completion Pass  
**Associated Artifacts:**
- Master Verification Report: [`data/ground_truth/reviews/PHASE2_VERIFICATION_REPORT.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/reviews/PHASE2_VERIFICATION_REPORT.md) (v9.0.0)
- Frozen Candidate Snapshot: [`data/ground_truth/snapshots/candidate_annotation_manifest_20261012.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/snapshots/candidate_annotation_manifest_20261012.json)
- Snapshot Audit Summary: [`data/ground_truth/snapshots/CANDIDATE_SNAPSHOT_AUDIT_20261012.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/snapshots/CANDIDATE_SNAPSHOT_AUDIT_20261012.md)
- Canonical Test Plan: [`docs/FINAL_TEST_PLAN.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FINAL_TEST_PLAN.md) (v1.0.0)
- Canonical Execution Results: [`results/testing/FINAL_TEST_RESULTS.md`](file:///Users/sayemuddin/Desktop/Train_automation/results/testing/FINAL_TEST_RESULTS.md) (v1.0.0)
- Machine-Readable Results: [`results/testing/canonical_test_results.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/testing/canonical_test_results.json)

---

## 1. What was verified and corrected?

1. **`event_005` T3 Discrepancy Resolved (`v4`):**
   - Source media audit of `camera_back.mov` established that at 5.60s (Frame 168), the lead locomotive trailing coupler passes an intermediate trackside signal/relay cabinet box.
   - At 6.00s (Frame 180), the locomotive trailing coupler completely clears the camera's transverse departure boundary plane.
   - Under the canonical Operational Danger-Zone Annotation Convention (`docs/FINAL_GROUND_TRUTH_PROTOCOL.md` §2.1 & §2.4), $T_3$ and $T_4$ must denote clearance of the identical conceptual exit boundary plane.
   - Setting $T_3 = 6.00\text{s}$ (Frame 180) in new immutable proposal `event_005_proposal_v4.json` establishes topological congruence with the $T_4$ tail clearance convention.
2. **Unified Exit Boundary Convention Verified:**
   - Audited across all 23 train events and the engine-only event.
   - Confirmed that $T_3$ (locomotive unit clearance) and $T_4$ (tail clearance) consistently track clearance of the identical Level-Crossing Departure Roadway Boundary Plane (marked on `camera_back.mov` by the vendor-stall clearance line).
   - In `engine_events/event_001`, $T_3 \equiv T_4 = 6.20\text{s}$ (coincidence rule strictly enforced).
3. **Suspicious Timestamp Formula Counts Reconciled:**
   - Exactly explained all historical patterns originating from `scratch/compute_candidates.py`: Pattern 1 ($T_1=3.0, T_2=3.7$, $N=14$), Pattern 2 ($T_1=3.5, T_2=4.2$, $N=5$), Pattern 3 ($T_1=4.5, T_2=5.2$, $N=3$), and Pilot `001` ($N=1$).
   - Physical frame re-inspection timestamps in active `v2` proposals verified against raw media.
4. **SNR Ratio Demystification Confirmed:**
   - The reported value "156.4 dB" was an uncalibrated linear spectral prominence power ratio, NOT true decibels. True decibel prominence is $10 \log_{10}(156.4) \approx 21.94\text{ dB}$.
5. **Frozen Model Checkpoints Verified:**
   - Vision `best.pt`: SHA-256 `3f5bb5b2...`, size 24,493,159 bytes verified.
   - Audio V3 `best.pt`: SHA-256 `ea1bb81d...`, size 329,497 bytes, operating threshold 0.3700 verified.
   - Prohibited Audio V2 (`59b0785f...`): detected and hard-blocked.
6. **Candidate Batch Frozen:**
   - Exactly 27 active events frozen in `candidate_annotation_manifest_20261012.json`.
   - `event_historical_duplicate_010` strictly excluded.
   - Mandatory Approval Firewall verified 100% intact (zero approved GT files or manifests generated).

---

## 2. What remains provisional or unverified?

1. **Acoustic Horn Judgments (`NOT_LISTENED` / `PROVISIONAL`):**
   - All 54 embedded audio tracks were analyzed spectrally via STFT, but have **NOT been listened to by human ears**.
   - Spectral peaks in the 300–800 Hz band indicate prominent acoustic energy, but cannot distinguish between locomotive air horns and loud road-traffic horns (buses, trucks, auto-rickshaws) without human auditory adjudication.
2. **Inter-Camera Clock Synchronization (Prerequisite R04 `BLOCKED`):**
   - Front and back cameras remain on independent media-local timelines.
   - Empirical hardware cross-camera time offsets remain uncertified.
   - Cross-camera elapsed traversal times cannot be computed.
3. **Ground-Truth Approval Status:**
   - All 27 candidate proposals remain unapproved drafts. No proposal has been certified as ground truth.

---

## 3. What tests actually ran?

The canonical test suite (`scripts/run_canonical_tests.py`) executed 49 discrete tests across six layers:
- **Layer F (6 tests):** Frozen model integrity (Vision SHA-256 & size, Audio V3 SHA-256, size & operating threshold, Prohibited Audio V2 hard block).
- **Layer A (15 tests):** Unit tests & forensic regressions (11 schema/firewall/timestamp tests + 4 defect regression tests).
- **Layer B (8 tests):** Dataset & candidate annotation integrity (cohort size, duplicate exclusion, media file presence, native FPS timestamp math, schema 7.0.0 compliance, immutability, firewall preservation, master index synchrony).
- **Layer C (3 tests):** Pipeline & integration workflows (video decoding, audio demuxing, crossing FSM 10-step lifecycle).
- **Layer D (12 tests):** Synthetic & fault-injection safety scenarios (all 12 required railway crossing safety scenarios).
- **Layer E (5 tests):** Natural-media replay & operational behavior (replays across 4 representative natural media streams + firewall assertion).

---

## 4. What were the measured results?

```
================================================================================
CANONICAL TEST SUITE SUMMARY: 49 PASSED, 0 FAILED out of 49 tests (100% PASS)
================================================================================
```
- Total Execution Time: Under 2.0 seconds.
- Memory & System Health: Clean execution without memory leaks or crashes.
- Frozen Model Checkpoints: 100% cryptographic and byte-count match.
- Schema & Causality Invariants: 100% compliance across all 27 active candidate proposals.

---

## 5. Which failures were fixed?

1. **`event_005` T3 Landmark Conflict:** Fixed by creating immutable proposal `event_005_proposal_v4.json` setting canonical $T_3 = 6.00\text{s}$ (Frame 180) to align with canonical departure plane semantics, resolving the 5.60s intermediate cabinet ambiguity.
2. **Module Import Contention:** Fixed Pytest filesystem/GIL contention during high-load background states by isolating synthetic test doubles in `tests/test_fault_injection_scenarios.py` and implementing the canonical runner `scripts/run_canonical_tests.py`.
3. **Forensic Regressions Sealed:** Implemented 4 dedicated regression tests preventing synthetic fallback formulas, unit mislabeling, ungrounded landmark definitions, and unsynchronized exposure pooling.

---

## 6. Which failures remain?

- **Zero technical test failures remain.** All 49 planned tests passed.
- **Methodological Limitations Preserved:**
  - Prerequisite R04 (Camera Synchronization) remains a standing blocker for cross-camera time fusion and pooled false-alarm rate calculations.
  - Human Auditory Review remains a standing requirement before horn status can be certified.

---

## 7. What research conclusions are supported by the completed tests?

1. **Software Pipeline Robustness:** The crossing state machine, schema validators, media decoders, and safety rules execute correctly and fail-safe under all 12 tested fault-injection scenarios.
2. **Approval Firewall Reliability:** The evaluation loader reliably rejects candidate proposals, preventing accidental premature ingestion of draft annotations.
3. **Dataset File Integrity:** All 54 raw media streams for the 27 active events exist and are decodable on disk.
4. **Operational Exit Plane Topological Consistency:** Measuring $T_3$ and $T_4$ at the level-crossing departure roadway boundary plane provides a mathematically sound, reproducible framework that eliminates the need for external geodetic surveys (R03).

---

## 8. What claims cannot yet be made?

1. **Cannot claim real-world detection accuracy, precision, or recall:** Model evaluation has NOT been run because ground-truth annotations are not yet approved.
2. **Cannot claim Premature Opening Rate (POR) or clearance safety latency:** $T_4$ clearance latency requires approved ground truth.
3. **Cannot claim cross-camera fused false alarms per hour:** Cameras are unsynchronized (R04). Summing stream durations across cameras is methodologically invalid.
4. **Cannot claim acoustic horn detection performance:** Audio has not been verified by human listening (`NOT_LISTENED`).
5. **Cannot claim commercial railway safety certification:** The software is research code and has not been certified for live railway interlocking.

---

## 9. What requires personal annotation review by the researcher?

The researcher must personally review and adjudicate the frozen candidate proposals in `data/ground_truth/proposals/`:
1. **Audit Review Sheets:** Inspect the 27 review sheets in `data/ground_truth/proposals/{train_events,no_train_events,engine_events}/*_review_sheet.md`.
2. **Verify Boundary Keyframes:** Run the FFmpeg commands documented in Section 4 of each review sheet to confirm visual boundary frames ($T_0, T_1, T_2, T_3, T_4$).
3. **Auditory Listening Checks:** Listen to the embedded audio tracks for the 10 train events proposed with `horn_status: "present"` to confirm whether the acoustic peaks correspond to locomotive air horns versus road traffic horns.
4. **Adjudicate `event_005` Resolution:** Confirm agreement with setting $T_3 = 6.00\text{s}$ (Frame 180, canonical exit boundary plane) over 5.60s (Frame 168, signal cabinet).
5. **Formally Approve Ground Truth:** When satisfied, grant approval to generate Stage 3 approved ground truth files (`data/ground_truth/{train_events,no_train_events,engine_events}/`) and lock the cryptographic manifest `data/ground_truth/ground_truth_manifest.json` (Prerequisite R02).

---

## 10. What should happen immediately after the researcher wakes up?

1. **Step 1:** Review [`data/ground_truth/snapshots/CANDIDATE_SNAPSHOT_AUDIT_20261012.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/snapshots/CANDIDATE_SNAPSHOT_AUDIT_20261012.md) and [`ANNOTATION_BATCH_REVIEW_INDEX.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/ANNOTATION_BATCH_REVIEW_INDEX.md).
2. **Step 2:** Sample-check keyframe previews (e.g., `event_001`, `event_005`, `engine_events/event_001`, `no_train_events/event_001`).
3. **Step 3:** Perform acoustic listening checks on audio tracks flagged with candidate horns.
4. **Step 4:** Authorize the generation of Stage 3 approved ground-truth annotations and `ground_truth_manifest.json`.
5. **Step 5:** Execute the formal model evaluation pipeline against the certified ground truth.
