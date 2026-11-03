# Dataset & Candidate Annotation Quality Audit

**Document Version:** 1.0.0  
**Audit Type:** Static Ground-Truth, Schema, and Metadata Integrity Audit  
**Target Corpus:** 27 Active Evaluation Events (`crossing_A`, Bangladesh)  
**Governing Manifests & Records:**  
- `data/ground_truth/snapshots/candidate_annotation_manifest_20261012.json`  
- `data/ground_truth/proposals/{train_events, no_train_events, engine_events}/*_proposal_v*.json`  
- `data/ground_truth/reviews/{train_events, no_train_events, engine_events}/*.INVALIDATION_NOTICE.json`  
- `src/railway_detection/evaluation/ground_truth_loader.py`  
- `docs/PHASE11_1_ANNOTATION_INTEGRITY_AUDIT.md`  

---

## 1. Executive Summary

This audit performs an exhaustive static inspection of the 27 active event candidate proposals, annotation manifests, schema definitions, review sheets, and historical invalidation records. 

### Key Findings:
1. **Zero Approved Ground Truth:** Every candidate proposal in the repository is explicitly classified as `UNAPPROVED_CANDIDATE_PROPOSAL`. All 27 legacy human review records were formally invalidated via sibling `LEGACY_REVIEW_INVALIDATION_NOTICE` files due to automated write bursts and references to superseded proposal versions.
2. **Missing Boundary in `event_005`:** `train_events/event_005` has $T_1 = \text{null}$ (`candidate_observable: false`) due to severe left-censoring (passenger car occupied the crossing at $t=0.0\,\text{s}$). It cannot be evaluated for Missed-Train Rate or Warning Lead Time.
3. **Camera Boundary Partitioning:** All observable $T_1$ timestamps ($N=23$, including `engine_events/event_001`) reside strictly on `camera_front.mov`. All observable $T_4$ timestamps ($N=23$) reside strictly on `camera_back.mov`.
4. **Engine Event Coincidence:** `engine_events/event_001` physically and correctly satisfies the coincidence rule $T_3 \equiv T_4 = 6.20\,\text{s}$ (single locomotive running light with zero trailing cars).

---

## 2. Event Cohort Inventory & Schema State

| Cohort | Event Count | Event ID Range | Recording Sessions | Proposal Schema | Active Proposal Version | Ground Truth Status |
| :--- | :---: | :--- | :--- | :---: | :---: | :--- |
| **`train_events`** | 23 | `event_001` – `event_023` | Session 1: 2026-09-14 (17 events)<br>Session 2: 2026-10-04 (6 events) | `7.0.0` | v2 – v6 | `UNAPPROVED_CANDIDATE_PROPOSAL` |
| **`no_train_events`** | 3 | `event_001` – `event_003` | Session 1: 2026-09-14 (2 events)<br>Session 2: 2026-10-04 (1 event) | `7.0.0` | v2 | `UNAPPROVED_CANDIDATE_PROPOSAL` |
| **`engine_events`** | 1 | `event_001` | Session 1: 2026-09-14 | `7.0.0` | v2 | `UNAPPROVED_CANDIDATE_PROPOSAL` |
| **Quarantined** | 1 | `event_historical_duplicate_010` | N/A (Excluded historical copy) | N/A | Superseded | Quarantined Duplicate |

---

## 3. Boundary Timestamp Distribution & Camera Mapping

```
+──────────────────────────────────────────────────────────────────────────────────────────────────+
| FRONT CAMERA BOUNDARIES (camera_front.mov, native 29.97 FPS, tau = 0.0s)                         |
| • T0_first_visible: Observed in 23/23 train events (t=0.0s for 20 events, t=1.5s for 3 events).  |
| • T1_danger_zone_entry: Turnout frog plane. Observable in 22/23 train events (range: 2.1s - 5.8s)|
| • T2_crossing_occupancy_start: Roadway line. Observable in 22/23 train events (T1 + 0.7s to 0.9s)|
+──────────────────────────────────────────────────────────────────────────────────────────────────+
                                                  │
                                                  ▼
+──────────────────────────────────────────────────────────────────────────────────────────────────+
| BACK CAMERA BOUNDARIES (camera_back.mov, native 30.0 / 59.94 FPS, tau uncalibrated)             |
| • T3_locomotive_unit_clearance: Departure line. Observable in 23/23 train events (3.1s - 6.0s).   |
| • T4_tail_clearance: Final railcar clearance. Observable in 22/23 train events (19.5s - 125.8s). |
| • T_scene_clear: Train receding from track. Unobservable in 22/23 events (camera cutoff).        |
+──────────────────────────────────────────────────────────────────────────────────────────────────+
```

### Detailed Event Boundary Audit:
- **Left-Censored Train Arrivals ($T_0 \le 0.0\,\text{s}$):**
  - In 20 of 23 train events, $T_0 = 0.00\,\text{s}$ (locomotive cowcatcher already in frame at Frame 0).
  - In 3 events (`event_009`, `event_015`, `event_016`), recording started immediately prior to visual appearance ($T_0 = 1.50\,\text{s}$).
  - In all 23 events, the train was already moving within the approach corridor prior to recording.
- **`train_events/event_005` (Dual-Ended Censoring):**
  - $T_0 = 0.0\,\text{s}$, $T_1 = \text{null}$, $T_2 = \text{null}$, $T_3 = 6.0\,\text{s}$, $T_4 = \text{null}$.
  - Rationale in proposal v4: Locomotive cowcatcher crossed turnout frog and roadway line before recording started; camera begins with Dining Car 1402 occupying the frame. On back camera, recording cut off prematurely while trailing cars 1084 and 1032 were traversing the field of view.
  - Scientific Impact: `event_005` cannot provide ground-truth entry or exit boundaries.
- **`engine_events/event_001` (Single Locomotive Running Light):**
  - Consist: Zero trailing cars.
  - Front camera: $T_0 = 0.0\,\text{s}$, $T_1 = 0.0\,\text{s}$, $T_2 = 0.0\,\text{s}$.
  - Back camera: $T_3 = 6.20\,\text{s}$, $T_4 = 6.20\,\text{s}$.
  - Scientific Impact: Demonstrates exit coincidence ($T_3 \equiv T_4$). Must be isolated from train-event cohort.

---

## 4. Process Integrity Audit of Legacy Reviews

An inspection of `data/ground_truth/reviews/` confirms that **no valid human review records exist in the repository**:

1. **Systemic Invalidation of 27 Legacy Reviews:**
   - Every review file (`data/ground_truth/reviews/{cohort}/{event_id}_review.json`) is accompanied by a formal sibling notice: `{event_id}_review.INVALIDATION_NOTICE.json`.
   - Forensic Cause (Phase 11.1 Audit): All 27 files shared an identical `review_date_utc` (`2026-10-12T16:51:21Z`) and filesystem modification timestamps spanning approximately 5 seconds (~0.2s/record), proving that the files were generated by an automated batch script rather than genuine frame-by-frame human video review.
   - Proposal Version Mismatch: The review files evaluated superseded proposal versions (e.g., v1/v2) rather than active proposals (v4/v6).
2. **Schema Rejection by Promotion Gate:**
   - In `src/railway_detection/evaluation/ground_truth_loader.py` (lines 97–180), the loader requires schema `8.1.0-stage2.1` and `adjudication_status == "APPROVED"`.
   - All legacy reviews use legacy unversioned schemas and are rejected on `LEGACY_OR_UNKNOWN_SCHEMA` grounds.
3. **Absence of Promotion Receipts:**
   - The directory `data/ground_truth/receipts/` does not exist. No cryptographic promotion receipts have ever been generated.

---

## 5. Master Findings Table

| Finding | Evidence Path | Severity | Confirmed / Suspected | Scientific Impact | Recommended Resolution | Required Authorization |
| :--- | :--- | :---: | :---: | :--- | :--- | :---: |
| **F-GT01: No Approved Ground Truth** | `data/ground_truth/phase12_ground_truth.json` (absent) | **CRITICAL** | Confirmed | Official evaluation runner cannot execute (`GroundTruthMissingError`). | Human review of candidate $T_1$ on `camera_front.mov` by allowlisted reviewer. | `ADJ-AUTH` |
| **F-GT02: Legacy Reviews Systemically Invalidated** | `data/ground_truth/reviews/*/*.INVALIDATION_NOTICE.json` | **HIGH** | Confirmed | Prevents legacy synthetic reviews from contaminating evaluation. | Invalidation notices correctly isolate records; preserve in place. | None (Completed) |
| **F-GT03: Event 005 Entry Boundary Unobservable** | `data/ground_truth/proposals/train_events/event_005_proposal_v4.json` | **MEDIUM** | Confirmed | Train MTR and warning lead time denominators reduce from 23 to $\le 22$. | Formally record `event_005` in `summary.exclusions["missed_train"]`. | Researcher decision |
| **F-GT04: Left-Censored Train Arrivals ($T_0 \le 0.0\text{s}$)** | All 23 train event proposals (lines 45–54) | **HIGH** | Confirmed | True approach detection latency cannot be measured from video start. | State in paper that warning lead time is bounded by recording duration. | Scientific disclosure |
| **F-GT05: Engine Event Cohort Contamination Risk** | `data/ground_truth/proposals/engine_events/event_001_proposal_v2.json` | **MEDIUM** | Confirmed | Mixing engine event into train denominator confounds consist statistics. | Enforce `notes == "engine_event_excluded"` and report in Table 4. | Researcher decision |
| **F-GT06: Cross-Camera Boundary Disconnect** | All 23 train event proposals ($T_1$ front, $T_4$ back) | **CRITICAL** | Confirmed | Precludes computing premature opening and clearance latency on front camera. | Formally exclude Tier 3 endpoints under `clock_mismatch`. | Researcher decision |
| **F-GT07: Acoustic Listening Status Unverified** | `data/ground_truth/snapshots/candidate_annotation_manifest_20261012.json` line 17 | **MEDIUM** | Confirmed | Spectral prominence peaks may reflect ambient road/horn confounding. | Require human auditory listening check before final approval. | `ADJ-AUTH` |
| **F-GT08: Missing Promotion Receipts** | `data/ground_truth/receipts/` (absent) | **MEDIUM** | Confirmed | Audit trail for Stage-2.1 promotion cannot be cryptographically verified. | Generate signed promotion receipts upon human review completion. | `ADJ-AUTH` |
