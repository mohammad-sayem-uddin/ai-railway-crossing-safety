# MISSION 16A-DATA-CHALLENGE: INDEPENDENT DATASET INTEGRITY AND GROUND-TRUTH AUDIT

**Project:** Train Gate Automation — Bangladesh  
**Mission:** Master Mission 16A Follow-up Challenge Audit  
**Auditor:** Independent Principal Dataset Auditor, Ground-Truth Protocol Reviewer, Temporal Annotation Auditor, and Scientific Reproducibility Researcher  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Git Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Audit Standard:** Strict Read-Only, Metadata-Only, Adversarial, Evidence-Based  
**Execution Authority:** NONE  
**Research Authorization:** NONE  
**Data Access Authorization:** NONE  

---

## 1. Executive Verdict

This independent challenge audit provides a forensic verification of the dataset inventory, event provenance, camera synchronization metadata, legacy ground-truth records, temporal boundary definitions, censoring mechanisms, and experiment eligibility across the Train Gate Automation project.

### Core Audit Determinations:
1. **Event Inventory Reality:** The historical dataset consists of **27 total candidate events** (23 train passage events, 3 negative control no-train events, and 1 isolated engine-only event). In addition, manifest records uncover an unindexed 28th historical recording pair (`event_historical_duplicate_010`) that was flagged as an engine duplicate and excluded from evaluation eligibility.
2. **R04 Dual-Camera Scope Discrepancy:** The authorized exploratory dual-camera configuration ([`configs/exploratory_dual_camera_v1.1.0_authorized_20261013.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/configs/exploratory_dual_camera_v1.1.0_authorized_20261013.yaml)) explicitly freezes the cohort at **11 events**. The candidate synchronization manifest ([`data/manifests/camera_sync_offsets_candidate.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/camera_sync_offsets_candidate.yaml)) reports 12 events due to the post-freeze addition of `train_events/event_010`. Under established researcher direction RD-026, the 11-event scope remains authoritative; silent expansion to 12 is prohibited.
3. **The `event_010` Discrepancy Deconstruction:** Historical narratives and audit prompts asserted a "+11.800 s audio-visual offset discrepancy" for `event_010`. Forensic inspection of primary synchronization manifests reveals this to be an **unsourced downstream narrative contradiction**. In primary candidate manifests, `event_010` has an acoustic cross-correlation lag of **`+2.7158 s`**, a QuickTime container metadata delta of **`-17.0 s`**, and a container disagreement of **`19.72 s`** (which tripped the $|lag - qt| \le 1.5\,\text{s}$ sanity gate). The figure "+11.8 s" was conflated with the duration of `no_train_events/event_002` ($11.877\,\text{s}$) or an unsourced report claim.
4. **Zero Approved Stage-2.1 Ground Truth:** Exactly **0 approved Stage-2.1 ground-truth records exist**. All 27 legacy review records in [`data/ground_truth/reviews/`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/reviews/) share the identical timestamp `2026-10-12T16:51:21Z` and generic reviewer ID `human_researcher_lead`, written in an automated ~5-second burst (~0.2s/record). All 27 records were officially invalidated via non-destructive sibling notices ([`*.INVALIDATION_NOTICE.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/reviews/)) in Phase 11.6. Zero promotion receipts exist in [`data/ground_truth/promoted/`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/).
5. **Severe Left-Censoring (20 of 23 Events):** Metadata analysis of active proposals confirms that **20 of 23 train events** have $T_0 = 0.0\,\text{s}$ (train already inside visual frame at recording onset). Only 3 events (`event_009`, `event_015`, `event_016`) have an observable visual entry ($T_0 = 1.5\,\text{s}$). Consequently, true approach detection latency cannot be measured on field footage.
6. **Vision Data Leakage Verified:** The primary vision development split ([`data/splits/705d388743ea/split_summary.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/705d388743ea/split_summary.json)) records **`leakage_risk: true`** and **`allow_ungrouped_fallback: true`**. The 99.46% mAP figure cannot support claims of out-of-distribution generalization.
7. **B0–B2 Descriptive Benchmark Eligibility:** The dataset and code structure can support the proposed B0–B2 benchmark as an **offline exploratory benchmark protocol**, but **CANNOT be executed or reported as empirical results** until human ground-truth adjudication and formal execution authorization (`EVAL-AUTH`) are granted.

---

## 2. Audit Scope and Safety Declaration

### 2.1 Statutory Safety Compliance
In accordance with Section 2 of the Mission Charter, this audit operated under absolute data containment:
- **Zero Raw Media Access:** No `.mov`, `.mp4`, `.wav`, or `.mp3` media files were opened, previewed, played, decoded, or inspected.
- **Zero Subprocess Readers:** No instances of FFmpeg, ffprobe, OpenCV, PIL, PyAV, Librosa, or SoundFile were executed.
- **Zero Checkpoint Hashing / Inspection:** Model weights in `experiments/` were not opened, read, or hashed.
- **Zero Repository Modifications:** No source code, metadata, manifests, configs, protocols, or review records were created, modified, or deleted.
- **Zero Git Writes:** Git status and HEAD remained strictly untouched.

### 2.2 Evidence Classification Framework
Findings in this report are categorized strictly according to the statutory evidence standard:
- `VERIFIED_GOVERNANCE_RECORD`: Signed governance artifacts, integrity notices, and authorized reviewer lists.
- `VERIFIED_SAFE_METADATA`: Non-media JSON/YAML manifests, inventories, and schema files.
- `VERIFIED_SOURCE_IMPLEMENTATION`: Checked Python source code and test files in `src/` and `tests/`.
- `HISTORICAL_REPORT_ONLY`: Narrative claims in earlier mission reports not corroborated by machine metadata.
- `CONFIGURATION_DECLARED`: Settings in frozen YAML/JSON configurations.
- `UNVERIFIED`: Claims lacking authoritative backing in repository metadata.
- `CONTRADICTED`: Claims contradicted by primary code, metadata, or governance records.

---

## 3. Event Inventory Reconstruction

### 3.1 Authoritative Metadata Inspection
Inspection of [`data/manifests/layer_b_v2_annotation_inventory.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/layer_b_v2_annotation_inventory.json) (evidence: `VERIFIED_SAFE_METADATA`) confirms an active inventory of **27 events**:
- **Train Events:** 23 events (`train_events/event_001` through `train_events/event_023`).
- **Negative Control Events:** 3 events (`no_train_events/event_001` through `no_train_events/event_003`).
- **Engine-Only Events:** 1 event (`engine_events/event_001`).

### 3.2 Discovery of Excluded Historical Duplicate
Inspection of [`data/manifests/real_world_v2_video_manifest.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/real_world_v2_video_manifest.json) line 16 reveals that the original collection contained **56 raw video files** across 28 capture events:
```json
{
  "summary": {
    "train_events": 23,
    "engine_events_eligible": 1,
    "engine_events_historical_duplicate": 1,
    "no_train_events": 3,
    "total_video_files": 56
  }
}
```
The 28th event, recorded under source paths `TRAIN_VIDEO_AUDIO 2/Engine_front_camera/2.MOV` and `TRAIN_VIDEO_AUDIO 2/Engine_back_camera/2.MOV`, is explicitly designated:
- `event_id`: `event_historical_duplicate_010`
- `event_type`: `historical_engine_duplicate`
- `evaluation_eligible`: `false`

### 3.3 Event Inventory Consistency Analysis
| Cohort Identifier | Active Event Count | Manifest Key Stability | Categorical Separation | Evaluability Status |
| :--- | :---: | :---: | :---: | :--- |
| `train_events` | 23 | Stable (`event_001`–`event_023`) | Consistently full-consist passenger trains | 20 left-censored; 1 unobservable (`event_005`) |
| `no_train_events` | 3 | Stable (`event_001`–`event_003`) | Consistently non-train road traffic / empty | Negative controls for false alarm screening |
| `engine_events` | 1 | Stable (`event_001`) | Isolated single locomotive (shunting / light) | Governed by $T_3 \equiv T_4$; excluded from standard trains |
| `historical_duplicate` | 1 | Excluded (`event_historical_duplicate_010`) | Isolated duplicate engine recording | Excluded from Layer B evaluation inventory |
| **Total Cohort** | **27 Active** | **Internally Consistent** | **Properly Partitioned** | **Zero Approved Ground Truth** |

---

## 4. Event and Session Provenance Matrix

### 4.1 Provenance Metadata Extraction
Analysis of [`real_world_v2_video_manifest.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/real_world_v2_video_manifest.json) and [`dataset_inventory_summary.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/dataset_inventory_summary.json) establishes the capture environment:
- **Source Directory:** Recorded from physical storage volume path `TRAIN_VIDEO_AUDIO 2/`.
- **Location Geometry:** Single level-crossing location (`crossing_A` in Joypurhat corridor, Bangladesh).
- **Camera Pairing:** Dual fixed cameras:
  - `front`: Front-facing approach corridor (HEVC 1080p, 29.970 fps, 48 kHz stereo AAC).
  - `back`: Rear-facing departure corridor (HEVC/H.264 4K 2160p, 59.940 fps or 30.000 fps, 48 kHz stereo/mono AAC).
- **Physical Linking:** `rear_is_symlink: true` across all manifest records.

### 4.2 Statistical Independence Limitation
> [!WARNING]
> **Lack of Event Independence:** All 27 events were recorded at a single physical installation during two daytime capture sessions. Distinct event IDs represent individual cropped train passages, **not** independent crossing sites. Consequently, independent identically distributed (i.i.d.) statistical assumptions are violated.

---

## 5. R04 Dual-Camera Cohort Verification

### 5.1 The 11-Event Authorized Scope
Inspection of [`configs/exploratory_dual_camera_v1.1.0_authorized_20261013.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/configs/exploratory_dual_camera_v1.1.0_authorized_20261013.yaml) lines 18–30 (evidence: `CONFIGURATION_DECLARED`) reveals the authoritative exploratory dual-camera cohort:
```yaml
included_events_calibration_supported:
  - train_events/event_001
  - train_events/event_002
  - train_events/event_005
  - train_events/event_006
  - train_events/event_007
  - train_events/event_009
  - train_events/event_011
  - train_events/event_012
  - train_events/event_013
  - train_events/event_014
  - train_events/event_017
```
Total verified events: **Exactly 11 events**.

### 5.2 The 11 vs. 12 Scope Discrepancy
As documented in [`docs/generated/R04_ELEVEN_VS_TWELVE_RECONCILIATION_20261101_M4D.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/R04_ELEVEN_VS_TWELVE_RECONCILIATION_20261101_M4D.md):
- The candidate manifest [`data/manifests/camera_sync_offsets_candidate.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/camera_sync_offsets_candidate.yaml) lists **12 events** under `CALIBRATION_SUPPORTED`.
- The 12th event is **`train_events/event_010`**.
- `event_010` was promoted in the manifest via visual landmark corroboration (`ADMINISTRATIVE_DISPOSITION_R04_READ_ONLY_UNBLOCK_20261025`) *after* the exploratory configuration was frozen.
- Code-level validation in `governance.documented_r04_candidates()` correctly flags `consistent: False`.
- **Verdict:** Established researcher direction **RD-026** mandates that the exploratory R04 scope remains strictly **11 events**. The 12th event (`event_010`) cannot be included in official benchmark runs without new researcher authorization.

---

## 6. Forensic Assessment of the `event_010` Synchronization Discrepancy

Task D requires an independent investigation of the reported `+11.800 s` discrepancy.

### 6.1 What the Authoritative Metadata Actually Contains
Inspection of [`data/manifests/camera_sync_offsets_candidate.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/camera_sync_offsets_candidate.yaml) lines 122–148 and [`docs/R04_CALIBRATION_VALIDATION_REPORT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/R04_CALIBRATION_VALIDATION_REPORT.md) line 130 reveals the true measured diagnostics for `train_events/event_010`:
- **Acoustic Estimated Offset (`offset_s`):** **`+2.7158 s`** (GCC-PHAT 16 kHz).
- **Acoustic Peak-to-Sidelobe Ratio (PSR):** **`2.14`** (threshold $\ge 2.0$).
- **Acoustic Signal-to-Noise Ratio (SNR):** **`22.34 dB`** (threshold $\ge 15.0\,\text{dB}$).
- **Window Stability Spread:** **`0.0001 s`** (0.1 ms jitter across windows, threshold $\le 0.20\,\text{s}$).
- **QuickTime Container Delta (`qt_delta_s`):** **`-17.0 s`**.
- **QuickTime Container Disagreement ($|lag - qt|$):** **`19.7158 s`** ($\approx 19.72\,\text{s}$).

### 6.2 Why `event_010` Was Flagged Ambiguous
The frozen deterministic acceptance rule in [`src/railway_detection/data/sync_calibration.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/data/sync_calibration.py) lines 75–88 enforces:
$$|lag\_s - qt\_delta\_s| \le 1.5\,\text{s}$$
Because $|2.7158 - (-17.0)| = 19.7158\,\text{s} > 1.5\,\text{s}$, the automated gate classified `event_010` as **`AMBIGUOUS`** due to `METADATA_CLOCK_DISCREPANCY`, despite its pristine acoustic peak.

### 6.3 The Origin of the Contradictory "+11.8 s" Figure
Forensic text search across all historical files reveals that **the figure `+11.800 s` never existed in the raw acoustic cross-correlation output of `event_010`**.
The number `11.8 s` originated from two distinct, unrelated sources:
1. **`no_train_events/event_002` Front Duration:** In [`docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md) line 221 and [`docs/PHASE11_EVENT_INVENTORY.csv`](file:///Users/sayemuddin/Desktop/Train_automation/docs/PHASE11_EVENT_INVENTORY.csv) line 26, `event_002` front duration is recorded as **`11.877 s`**.
2. **Historical B0 Forensic Table:** In [`docs/FORENSIC_EXPERIMENT_AUDIT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FORENSIC_EXPERIMENT_AUDIT.md) line 190, negative control false-closure duration is reported as *"1 / 3 (33.3%), 11.8s closed"*.
3. **Downstream Conflation:** Downstream audit reports and review prompts mistakenly conflated the `event_002` duration ($11.877\,\text{s}$) with `event_010`'s metadata discrepancy ($19.72\,\text{s}$), inventing the narrative phrase "+11.800 s audio-visual offset discrepancy".
4. **Governing Direction:** In accordance with **RD-027**, acoustic offsets must never be used to shift human ground-truth timestamps.

---

## 7. Legacy Ground-Truth Forensic Audit

### 7.1 Identical Timestamp Burst Verification
Direct inspection of all 27 files in [`data/ground_truth/reviews/`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/reviews/) confirms:
- **Timestamp:** Exactly **100% (27 of 27)** of the review records contain:
  ```json
  "reviewer_metadata": {
    "reviewer_id": "human_researcher_lead",
    "review_date_utc": "2026-10-12T16:51:21Z",
    "inspection_tool": "ffmpeg-frame-analyzer / scipy-spectral-auditor v2.0"
  }
  ```
- **Filesystem Write Burst:** Filesystem metadata demonstrates all 27 files were written within a ~5-second window (~0.2s per file).
- **Prohibited Reviewer ID:** The identifier `human_researcher_lead` is explicitly barred by [`promotion_gate.REVIEWER_ID_BLOCKLIST`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/promotion_gate.py).
- **Superseded Schema:** Records were authored under legacy `schema_version: "6.0.0"`.

### 7.2 Invalidation Notice Coverage Matrix
Every single legacy review file is paired with an authentic, non-destructive sibling invalidation notice authored in Phase 11.6:

| # | Event Path | Legacy File SHA-256 | Sibling Invalidation Notice | Notice Status | Target Verified? |
| :-: | :--- | :--- | :--- | :--- | :-: |
| 1 | `train_events/event_001` | `a0edd4a670e17063...` | `event_001_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 2 | `train_events/event_002` | `e2a5f5127cd8490a...` | `event_002_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 3 | `train_events/event_003` | `be68c227448888b1...` | `event_003_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 4 | `train_events/event_004` | `da7bf430c55b62b1...` | `event_004_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 5 | `train_events/event_005` | `eb1f021e06d9d10e...` | `event_005_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 6 | `train_events/event_006` | `d14210a562479e43...` | `event_006_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 7 | `train_events/event_007` | `f7b5311e9f0fc031...` | `event_007_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 8 | `train_events/event_008` | `6256920fbbad91c7...` | `event_008_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 9 | `train_events/event_009` | `3780ce148ef8b54b...` | `event_009_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 10 | `train_events/event_010` | `2e08cb68903cbe31...` | `event_010_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 11 | `train_events/event_011` | `784260a92d43bf42...` | `event_011_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 12 | `train_events/event_012` | `5c45f4cb66ce7710...` | `event_012_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 13 | `train_events/event_013` | `6ae7e651e01869e5...` | `event_013_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 14 | `train_events/event_014` | `62fcf8828b6d8594...` | `event_014_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 15 | `train_events/event_015` | `091176b5d9299100...` | `event_015_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 16 | `train_events/event_016` | `10f22f77732a3962...` | `event_016_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 17 | `train_events/event_017` | `71b2641571d70d79...` | `event_017_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 18 | `train_events/event_018` | `34d19d6d34bf47c2...` | `event_018_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 19 | `train_events/event_019` | `43fe53112a970e70...` | `event_019_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 20 | `train_events/event_020` | `16867dc1fec46369...` | `event_020_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 21 | `train_events/event_021` | `f2dc6146c9c64264...` | `event_021_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 22 | `train_events/event_022` | `457f6b9aa0c7dcf6...` | `event_022_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 23 | `train_events/event_023` | `3ec0df506bf95748...` | `event_023_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 24 | `no_train_events/event_001` | `82f9d501daefda07...` | `event_001_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 25 | `no_train_events/event_002` | `a3915f0d9842a197...` | `event_002_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 26 | `no_train_events/event_003` | `04d49a71beea4038...` | `event_003_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |
| 27 | `engine_events/event_001` | `6b97b690d7c71120...` | `event_001_review.INVALIDATION_NOTICE.json` | `INVALIDATED` | YES |

Total notices verified: **27 / 27 (100.0%)**.  
SHA-256 target mismatches: **0**.  
Original files preserved unmodified: **YES**.

---

## 8. Stage-2.1 Promotion Status

Inspection of [`data/ground_truth/promoted/`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/) (evidence: `VERIFIED_GOVERNANCE_RECORD`):
- Total promoted files: **0**.
- Total promotion receipts: **0**.
- Total promoted dataset manifests: **0**.

**Verdict:** The repository contains **ZERO (0) promoted ground-truth records**. No promotion has ever been executed under the Phase 11.2 Stage-2.1 promotion gate.

---

## 9. Protocol and Schema Version Reconciliation

A critical potential source of methodological drift is protocol version confusion. The governance status of all related documents was verified:

| Document / Code Artifact | Documented Version | Governance Status | Authority / Role |
| :--- | :---: | :--- | :--- |
| [`FINAL_GROUND_TRUTH_PROTOCOL.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FINAL_GROUND_TRUTH_PROTOCOL.md) | **v7.0.0** (2026-10-12) | **RATIFIED SPECIFICATION** | Authoritative ground-truth protocol specification |
| [`FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md) | **v9.0.0** (2026-10-12) | **RATIFIED SPECIFICATION** | Authoritative experiment protocol specification |
| `FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md` | v7.1.0-PROPOSED | **PROPOSAL ONLY** | Pending researcher sign-off |
| `FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL_v9.1.0_PROPOSED.md`| v9.1.0-PROPOSED | **PROPOSAL ONLY** | Pending researcher sign-off |
| `FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL_v9.1.1_PROPOSED.md`| v9.1.1-PROPOSED | **PROPOSAL ONLY** | Pending researcher sign-off |
| [`stage2_1_schema.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/stage2_1_schema.py) | **`8.1.0-stage2.1`** | **RATIFIED CODE IMPLEMENTATION** | Python dataclass runtime schema |
| [`promotion_gate.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/promotion_gate.py) | **`8.1.0-stage2.1`** | **RATIFIED CODE IMPLEMENTATION** | Gate validator schema constant |

> [!NOTE]
> Under researcher directional decisions **RD-001** and **RD-002**, Protocol v7.0.0 and Protocol v9.0.0 serve as the baseline specifications. Newer "PROPOSED" documents under `docs/generated/` are unratified draft proposals. Review tools and validators strictly require schema `8.1.0-stage2.1`.

---

## 10. Temporal Ground-Truth Landmark Audit ($T_0\text{–}T_4, T_{\text{OCC\_START}}$)

The definitions and physical observability of all temporal boundaries were audited against Protocol v7.0.0, v9.0.0, and RD-004 through RD-008:

| Landmark | Formal Definition in Protocol | Physical Observability on Field Video | Status in Benchmark |
| :---: | :--- | :--- | :--- |
| **$T_0$** | First visible appearance of train in camera corridor. | **Severely Left-Censored.** Unobservable in 20/23 train events (train already present at frame 0). | Excluded from physical detection-latency point estimates. |
| **$T_1$** | Leading locomotive wheel/pilot crosses the danger-zone entry boundary (frog line). | **Physically Observable.** Discrete track boundary identifiable in 22/23 events (`event_005` unobservable). | Primary baseline for lead-in feasibility ($\text{MTR}$). |
| **$T_2$** | Leading locomotive end crosses physical roadway entry boundary. | **LANDMARK DEFINITION DEFERRED (RD-006).** Optical lens plane was historically used as an unvalidated proxy. | Cannot be used for official occupancy until landmark ratified. |
| **$T_3$** | Rear of locomotive unit clears crossing island. | **Physically Observable.** Coupler line visible in 22/23 events. For engine events, $T_3 \equiv T_4$ (RD-024). | Trailing engine boundary for single-unit and consist events. |
| **$T_4$** | Final vehicle tail clears departure crossing boundary. | **Physically Observable.** Tail buffer clears road exit. Observable in 22/23 events (`event_005` unobservable). | Authoritative clearance boundary for $M4$ and $M5$. |
| **$T_{\text{OCC\_START}}$** | Onset of roadway occupancy. | **Conditional Alias of $T_2$ (RD-005).** Not independently annotated. | Deferred alongside $T_2$. |

---

## 11. Censoring and Event Evaluability Assessment

### 11.1 Reconciling the Censoring Discrepancies (18 vs. 20 vs. 23)
Historical audit reports contained varying left-censoring claims:
- Early reports claimed **18 of 23** or **18 of 22**.
- Intermediate reports claimed **20 of 23**.
- Some informal summaries claimed **23 of 23**.

Forensic inspection of active candidate proposals in [`data/ground_truth/proposals/train_events/`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/) resolves this exact discrepancy:
1. **True $T_0 \le 0.0\,\text{s}$ Count (20 of 23):** Exactly 20 train events have `T0_first_visible.value_s = 0.0` with explicit left-censoring rationales (`train_events/event_001`–`008`, `010`–`014`, `017`–`023`).
2. **True Uncensored $T_0$ Count (3 of 23):** Exactly 3 train events have an observable arrival from beyond the corridor:
   - `train_events/event_009`: Locomotive emerges at Frame 45 ($t = 1.50\,\text{s}$).
   - `train_events/event_015`: Locomotive emerges at Frame 45 ($t = 1.50\,\text{s}$).
   - `train_events/event_016`: Locomotive emerges at Frame 45 ($t = 1.50\,\text{s}$).
3. **The "18 of 22" Figure:** In early finding `IMA-31`, only 22 train events had candidate $T_1$ values (excluding `event_005`), and exactly 18 of those 22 had $T_1 \le 3.2\,\text{s}$ (leaving inadequate physical lead time for warning). Subsequent authors mistook "18 events with short lead time" for "18 left-censored events".

### 11.2 Evaluability Denominators by Metric
Under **RD-011** and **RD-040**, censored events must not be dropped via outcome-dependent global filtering. Instead, each metric must maintain explicit, mathematically defensible denominators:

| Metric Endpoint | Candidate Denominator | Excluded Events & Justification |
| :--- | :---: | :--- |
| **Physical Detection Latency ($T_{\text{detect}} - T_0$)** | **3 events** (`009, 015, 016`) | 20 events left-censored ($T_0 \le 0.0\,\text{s}$); unobservable. |
| **Lead-in Feasibility ($\text{MTR} \ge 3.6\,\text{s}$)** | **22 events** | `event_005` excluded (unobservable entry); engine excluded. |
| **Premature Opening ($M4$)** | **22 events** | `event_005` excluded (unobservable $T_1, T_4$); engine evaluated separately. |
| **Companion Intrusion ($M5$)** | **22 events** | `event_005` excluded; engine evaluated separately. |
| **Negative Control False Warning** | **3 events** | `no_train_events/event_001`–`003`. |

---

## 12. Human Annotation and Reviewer Governance Assessment

### 12.1 Authorized Reviewer Allowlist Status
Inspection of [`data/ground_truth/authorized_reviewers.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/authorized_reviewers.json) (evidence: `VERIFIED_GOVERNANCE_RECORD`):
- Maintained allowlist:
  ```json
  {
    "authorized_reviewers": [
      "raihankabirrahu@gmail.com"
    ]
  }
  ```
- No second reviewer has been appointed.

### 12.2 Status of Reviewer Governance Decisions (RD-042 to RD-050)
- **RD-043 (Second-Review Triggers):** Implemented in [`second_review.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/second_review.py) with 5 deterministic triggers (`TRIGGER_CORRECTED`, `TRIGGER_ENGINE_T3_T4`, `TRIGGER_EXPLICIT_FLAG`, `TRIGGER_MEDIA_HASH`, `TRIGGER_UNCERTAIN_BOUNDARY`). **Status: PROPOSED, PENDING RESEARCHER ADOPTION.**
- **RD-045 (Disagreement Resolution):** Handling protocol for dual-reviewer variance. **Status: PENDING RESEARCHER ADOPTION.**
- **RD-046 (Review Duration Floor):** Proposed $\ge 30.0\,\text{s}$ floor in [`adjudication_session.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/adjudication_session.py). **Status: DEFERRED PENDING PILOT EVIDENCE.**
- **AI Auto-Approval Prohibition:** Strictly enforced by code in `promotion_gate.py`. No AI agent can promote annotations.

---

## 13. Dataset Split and Data Leakage Assessment

### 13.1 YOLOv8n Vision Split Deconstruction (`705d388743ea`)
Inspection of [`data/splits/705d388743ea/split_summary.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/705d388743ea/split_summary.json) (evidence: `VERIFIED_SAFE_METADATA`):
- `split_type`: `"development_fallback"`
- `leakage_risk`: **`true`**
- `require_grouping`: `true`
- `allow_ungrouped_fallback`: **`true`**
- `group_field`: `"crossing_id"`

### 13.2 Leakage Mechanism and Generalization Barrier
1. **Grouping Failure:** All source images shared the identical or null `crossing_id`. Consequently, grouped cross-validation by site was impossible.
2. **Ungrouped Fallback:** The split generator fell back to random image-level partitioning across 3,157 image crops (Train: 2,218, Val: 467, Test: 472).
3. **Temporal Near-Duplicates:** Consecutive frames from the exact same train passage exist simultaneously in both the training set and the test set (e.g., `Screenshot-2026-05-23-at-15-44-52` in train and `Screenshot-2026-05-23-at-15-45-35` in test).
4. **Scientific Consequence:** The reported Layer A mAP@50 of 99.46% evaluates recognition of near-duplicate frames from seen video sequences. It **does not prove generalization** to new crossings, unseen camera angles, or novel train rolling stock.

---

## 14. B0–B2 Experiment Eligibility Matrix

Audit of readiness for the planned descriptive offline benchmark:

| Benchmark Condition | Sensor / Modality Scope | Input Caches Required | Ground Truth Required | Eligibility Status | Primary Blocker |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **B0** | Unimodal Front Vision (YOLOv8n) | Front perceptual JSONL feature caches | Approved Stage-2.1 $T_1, T_4$ | **BLOCKED** | Zero approved Stage-2.1 ground truth; EVAL-AUTH unissued |
| **B1** | Unimodal Front Audio (CompactTrainHornCNN V3) | Front audio spectrogram / feature caches | Approved Stage-2.1 $T_1, T_4$ | **BLOCKED** | Zero approved Stage-2.1 ground truth; EVAL-AUTH unissued |
| **B2** | Container-Native Multimodal Fusion (Front V+A) | Synchronized front feature caches | Approved Stage-2.1 $T_1, T_4$ | **BLOCKED** | Zero approved Stage-2.1 ground truth; EVAL-AUTH unissued |
| **B3 / B4** | Dual-Camera Cross-Stream (Front + Back) | Dual front/back perceptual caches | Approved Stage-2.1 + R04 offsets | **METHODOLOGICALLY CONSTRAINED** | R04 restricted to 11 events; ungenlocked clocks |

---

## 15. Dataset-Related Publication Claim Audit

A rigorous crosswalk between manuscript claims and underlying evidence:

| Manuscript Claim | Draft Location | Authoritative Evidence | Evidentiary Verdict | Required Publication Framing |
| :--- | :--- | :--- | :--- | :--- |
| *"Evaluated on a comprehensive 27-event crossing dataset"* | Abstract / Sec 1 | `layer_b_v2_annotation_inventory.json` | **SUPPORTED (Inventory Only)** | Frame as: *"An exploratory single-crossing cohort of 27 recorded events (23 train, 3 negative control, 1 engine)."* |
| *"Flawless train detection with 99.46% mAP"* | Historical Docx | `experiments/vision/39f402dfe460/` | **MISLEADING / LEAKAGE RISK** | Restrict claim to: *"Layer A still-image detection on a seen-corridor split with documented temporal leakage risk."* |
| *"Validated across 12 synchronized dual-camera events"* | Historical Docx | `camera_sync_offsets_candidate.yaml` | **CONTRADICTED (RD-026)** | Correct count to: *"11 exploratory dual-camera events with software-estimated acoustic alignment."* |
| *"Zero premature opening risk ($M4 = 0$)"* | Historical Docx | Pre-Phase 5 Replay Logs | **INADMISSIBLE** | Mark as: *"`[RESULTS PENDING]` - official Phase 5 evaluation not executed; ground truth unapproved."* |
| *"Approach detection latency under 1.0 second"* | Early Drafts | `candidate_values.json` | **INDEFENSIBLE** | Correct to: *"Approach latency unobservable due to left-censoring in 20 of 23 events; $T_1$ serves as surrogate."* |

---

## 16. Comprehensive Contradiction Register

| ID | Topic | Prior Audit / Prompt Claim | Verified Ground Truth in Repository | Evidence Source | Severity |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **CONTRA-01** | `event_010` Sync Discrepancy | Prompt & Mission 16A asserted `+11.800 s` discrepancy | Measured lag is `+2.7158 s`; QuickTime disagreement is `19.72 s`. `11.8 s` was conflated with `event_002` duration ($11.877\,\text{s}$). | `camera_sync_offsets_candidate.yaml` L125; `R04_CALIBRATION_VALIDATION_REPORT.md` L130 | **HIGH** |
| **CONTRA-02** | R04 Cohort Size | Candidate manifest reports $N=12$ | Authorized exploratory config explicitly freezes $N=11$; RD-026 prohibits expansion to 12. | `exploratory_dual_camera_v1.1.0_authorized_20261013.yaml` L18 | **HIGH** |
| **CONTRA-03** | Left-Censoring Count | Reports asserted 18/23 or 23/23 | Metadata proves exactly 20 of 23 train events have $T_0 \le 0.0\,\text{s}$; 3 events have observable entry ($T_0 = 1.5\,\text{s}$). | Active proposals in `data/ground_truth/proposals/` | **MEDIUM** |
| **CONTRA-04** | Vision Generalization | Manuscript claimed generalized detection | Split summary records `leakage_risk: true` and `allow_ungrouped_fallback: true` across 3,157 near-duplicate frames. | `data/splits/705d388743ea/split_summary.json` | **HIGH** |
| **CONTRA-05** | Legacy Review Legitimacy | Historical logs claimed 27 reviews were approved | All 27 reviews were written in a ~5-second automated burst (`2026-10-12T16:51:21Z`) and are officially invalidated. | `data/ground_truth/reviews/*/*.INVALIDATION_NOTICE.json` | **CRITICAL** |

---

## 17. Prioritized Findings and Required Researcher Decisions

### Prioritized Findings:
- **CRITICAL (DATA-F01):** Exactly zero approved Stage-2.1 ground-truth records exist. All 27 legacy reviews are invalidated. Real-data benchmark evaluation is completely blocked.
- **HIGH (DATA-F02):** The YOLOv8n still-image evaluation contains verified data leakage (`leakage_risk: true`), precluding claims of general crossing object detection.
- **HIGH (DATA-F03):** R04 dual-camera scope discrepancy between candidate manifest ($N=12$) and authorized configuration ($N=11$) must be formally resolved.
- **HIGH (DATA-F04):** Approach detection latency is unobservable on 20 of 23 train events due to left-censoring; manuscript must use $T_1$ surrogate framing.
- **MEDIUM (DATA-F05):** Downstream reports introduced an unsourced narrative error claiming a `+11.800 s` offset for `event_010`; actual container discrepancy is $19.72\,\text{s}$ ($lag = +2.7158\,\text{s}$).

### Required Researcher Decisions:
1. **Decision D-DATA-01:** Formally execute human adjudication sessions for all 27 events using [`adjudication_session.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/adjudication_session.py).
2. **Decision D-DATA-02:** Execute the Stage-2.1 promotion gate ([`promotion_gate.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/promotion_gate.py)) to generate official promotion receipts.
3. **Decision D-DATA-03:** Formally decide R04 dual-camera scope under **RD-026**: retain 11 events or author an authorized v1.2.0 config adding `event_010`.
4. **Decision D-DATA-04:** Adopt the 5 second-review triggers in [`second_review.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/second_review.py) (**RD-043**) and appoint a second human reviewer.
5. **Decision D-DATA-05:** Ratify the replacement of approach latency endpoints with lead-in feasibility screens ($\text{MTR}$).

---

## 18. Explicit List of Unverified Information Due to Safety Restrictions

In strict adherence to Section 2 of the Mission Charter, the following elements were **deliberately not inspected or verified**:
1. **Frame-Level Annotation Correctness:** The exact bounding boxes, pixel coordinates, and sub-second visual boundaries inside the raw video frames were not visually checked, because opening or decoding `.mov` media files is strictly prohibited.
2. **Audio Spectral Characteristics:** Raw acoustic waveforms and frequencies of locomotive horns were not decoded or listened to.
3. **Physical Media Duration Validation:** Exact video and audio stream durations were taken from safe manifest metadata; no direct `ffprobe` or `libav` decoding was run against raw files.
4. **Production Model Weight Inspection:** Checkpoint weights in `experiments/` were not loaded, evaluated, or hashed.
5. **Perceptual Feature Cache Validation:** Processed feature arrays (`.npy`, `.parquet`) in `data/processed/` were not opened or deserialized.

---

## 19. Final Disposition

Under the statutory terms of the Master Mission 16A Data-Challenge charter, the auditor assigns the official audit disposition:

```
========================================================================================
FINAL DISPOSITION:
DATA_AUDIT_CONTRADICTIONS_FOUND
========================================================================================
```

### Statutory Justification:
The audit successfully reconstructed the event inventory, verified legacy invalidations, and audited protocol schemas from safe metadata. However, the disposition **`DATA_AUDIT_CONTRADICTIONS_FOUND`** is strictly mandated by the discovery of major empirical contradictions:
1. The downstream narrative contradiction attributing a `+11.800 s` acoustic discrepancy to `event_010`, when primary manifests document $lag = +2.7158\,\text{s}$ and $qt\_delta = -17.0\,\text{s}$ ($19.72\,\text{s}$ container disagreement).
2. The discrepancy between the authorized R04 dual-camera cohort ($N=11$) and candidate manifest ($N=12$).
3. The contradiction between historical claims of generalized vision performance (99.46% mAP) and the primary split summary documenting `leakage_risk: true` across ungrouped near-duplicate frames.
4. The historical contradiction of claiming 27 approved human reviews when all 27 records were generated in an automated 5-second burst and are now marked `INVALIDATED`.

---

## 20. Concluding Statutory Statement

```
========================================================================================
                       REAL-DATA EXECUTION: NOT AUTHORIZED
========================================================================================
Zero approved Stage-2.1 ground-truth records exist.
No real-data inference, replay, evaluation, or media decoding is permitted.
========================================================================================
```
