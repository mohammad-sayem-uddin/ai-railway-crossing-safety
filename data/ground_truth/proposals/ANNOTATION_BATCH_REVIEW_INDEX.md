# Master Annotation Candidate Batch Review Index (Layer B V2)

> [!IMPORTANT]
> **MANDATORY APPROVAL FIREWALL NOTICE:**
> This aggregate index catalogs AI-generated candidate proposals across all 27 eligible Layer B V2 evaluation events.
> It is a **NAVIGATION AND AUDIT RECORD ONLY**. None of the candidate proposals indexed here are approved ground truth.
> Every candidate field must be manually inspected, adjudicated, and certified by the human researcher before evaluation.

---

## 1. Batch Execution Summary
- **Execution Timestamp (UTC):** `2026-10-12T17:10:00Z`
- **Schema Version:** `7.0.0` (Protocol v7.0.0 / Master Protocol v9.0.0)
- **Total Eligible Events Discovered:** **27**
  - Full-Train Events: **23** (`train_events/event_001` through `event_023`)
  - No-Train Events: **3** (`no_train_events/event_001` through `event_003`)
  - Engine-Only Events: **1** (`engine_events/event_001`)
- **Explicit Exclusion Status:** `engine_events/event_historical_duplicate_010` is excluded from evaluation per protocol and preserved as a historical artifact.
- **Candidate Proposals Active:** **27 / 27**
  - `event_001` (train): Version `v6` (`event_001_proposal_v6.json`, prior ref `v5`)
  - `event_005` (train): Version `v3` (`event_005_proposal_v3.json`, prior ref `v2`)
  - `event_002`–`004`, `event_006`–`023` (train): Version `v2` (`event_XXX_proposal_v2.json`, prior ref `v1`)
  - `no_train_events` 001–003: Version `v2` (`event_XXX_proposal_v2.json`, prior ref `v1`)
  - `engine_events` 001: Version `v2` (`event_001_proposal_v2.json`, prior ref `v1`)
- **Review Sheets Active:** **27 / 27**
- **Methodology Revision:** Prerequisite R03 formally retired as a separate blocker; Operational Danger-Zone Annotation Convention applied.
- **Multimodal Backend Used:** `antigravity-multimodal-agent` (evidence-based dense physical video frame & acoustic spectral analysis; zero model-output leakage)
- **Prompt Template Version:** `v1.0.0`
- **Prompt Template SHA-256:** `8ea581b1453f72b4673642d510acc4a4e0a9aeb9727ae63ff0c0546b65741a5e`

---

## 2. Status of Research Prerequisites (R01–R04) Post-Protocol v7.0.0 Revision
| Prerequisite | Description | Current Status | Annotation Impact |
| :--- | :--- | :---: | :--- |
| **R01** | Level-Crossing Risk Formulation & Human Approval | **IN PROGRESS** (Firewall Enforced) | Candidate proposals generated; awaiting human researcher verification. |
| **R02** | Cryptographic Ground Truth Manifest Freeze | **PENDING** | Awaiting researcher approval of review records before manifest generation. |
| **R03** | Crossing Geometric Danger Zone Survey | **RETIRED** | Replaced by documented Operational Danger-Zone Annotation Convention (§2.4). |
| **R04** | Inter-Camera Temporal Synchronization | **UNRESOLVED / PRESERVED** | Offsets uncertified; front/back on independent media-local clocks. |

---

## 3. Full-Train Events Candidate Table (23 Events)
| Event ID | Proposal JSON | Review Sheet | T0 (s) | T1 (s) | T2 (s) | T3 (s) | T4 (s) | T_sc | Cars | Horn Status | Left-Censored? |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| `event_001` | [`event_001_proposal_v6.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_001_proposal_v6.json) | [`event_001_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_001_review_sheet.md) | 0.00s | 5.80s | 6.50s | 3.60s | 45.00s | null | 7 | `present` (6.66s) | ⚠️ YES |
| `event_002` | [`event_002_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_002_proposal_v2.json) | [`event_002_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_002_review_sheet.md) | 0.00s | 2.90s | 3.60s | 3.40s | 28.80s | null | 5 | `present` (2.50s) | ⚠️ YES |
| `event_003` | [`event_003_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_003_proposal_v2.json) | [`event_003_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_003_review_sheet.md) | 0.00s | 2.10s | 2.80s | 3.20s | 30.50s | null | 5 | `absent_observed` | ⚠️ YES |
| `event_004` | [`event_004_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_004_proposal_v2.json) | [`event_004_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_004_review_sheet.md) | 0.00s | 2.10s | 2.90s | 3.10s | 76.80s | null | 14 | `present` (0.96s) | ⚠️ YES |
| `event_005` | [`event_005_proposal_v4.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_005_proposal_v4.json) | [`event_005_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_005_review_sheet.md) | 0.00s | null | null | **6.00s** | **null** | null | 14 | `present` (1.28s) | ⚠️ YES (Front mid-consist; Back entry 0.50s; T4 Right-Censored) |
| `event_006` | [`event_006_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_006_proposal_v2.json) | [`event_006_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_006_review_sheet.md) | 0.00s | 2.50s | 3.30s | 3.80s | 125.80s | null | 24 | `present` (121.28s) | ⚠️ YES |
| `event_007` | [`event_007_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_007_proposal_v2.json) | [`event_007_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_007_review_sheet.md) | 0.00s | 2.60s | 3.40s | 3.30s | 33.50s | null | 6 | `absent_observed` | ⚠️ YES |
| `event_008` | [`event_008_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_008_proposal_v2.json) | [`event_008_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_008_review_sheet.md) | 0.00s | 2.40s | 3.20s | 3.20s | 61.20s | null | 11 | `absent_observed` | ⚠️ YES |
| `event_009` | [`event_009_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_009_proposal_v2.json) | [`event_009_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_009_review_sheet.md) | 1.50s | 4.20s | 5.00s | 3.60s | 36.40s | null | 6 | `absent_observed` | No (Late Arrival) |
| `event_010` | [`event_010_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_010_proposal_v2.json) | [`event_010_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_010_review_sheet.md) | 0.00s | 2.70s | 3.50s | 3.10s | 22.40s | null | 4 | `absent_observed` | ⚠️ YES |
| `event_011` | [`event_011_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_011_proposal_v2.json) | [`event_011_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_011_review_sheet.md) | 0.00s | 2.80s | 3.60s | 3.30s | 29.40s | 32.50s | 5 | `absent_observed` | ⚠️ YES |
| `event_012` | [`event_012_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_012_proposal_v2.json) | [`event_012_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_012_review_sheet.md) | 0.00s | 3.10s | 3.90s | 3.70s | 69.20s | null | 13 | `present` (6.78s) | ⚠️ YES |
| `event_013` | [`event_013_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_013_proposal_v2.json) | [`event_013_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_013_review_sheet.md) | 0.00s | 3.20s | 4.00s | 3.90s | 70.80s | null | 13 | `present` (4.22s) | ⚠️ YES |
| `event_014` | [`event_014_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_014_proposal_v2.json) | [`event_014_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_014_review_sheet.md) | 0.00s | 2.60s | 3.40s | 3.60s | 51.20s | null | 9 | `absent_observed` | ⚠️ YES |
| `event_015` | [`event_015_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_015_proposal_v2.json) | [`event_015_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_015_review_sheet.md) | 1.50s | 4.20s | 5.00s | 3.80s | 19.50s | null | 3 | `present` (14.85s) | No (Late Arrival) |
| `event_016` | [`event_016_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_016_proposal_v2.json) | [`event_016_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_016_review_sheet.md) | 1.50s | 4.20s | 5.00s | 3.40s | 44.10s | null | 8 | `absent_observed` | No (Late Arrival) |
| `event_017` | [`event_017_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_017_proposal_v2.json) | [`event_017_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_017_review_sheet.md) | 0.00s | 2.80s | 3.60s | 4.20s | 82.50s | null | 15 | `present` (0.83s) | ⚠️ YES |
| `event_018` | [`event_018_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_018_proposal_v2.json) | [`event_018_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_018_review_sheet.md) | 0.00s | 2.70s | 3.50s | 3.80s | 50.80s | null | 9 | `present` (5.95s) | ⚠️ YES |
| `event_019` | [`event_019_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_019_proposal_v2.json) | [`event_019_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_019_review_sheet.md) | 0.00s | 3.00s | 3.80s | 3.30s | 47.20s | null | 9 | `absent_observed` | ⚠️ YES |
| `event_020` | [`event_020_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_020_proposal_v2.json) | [`event_020_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_020_review_sheet.md) | 0.00s | 2.30s | 3.10s | 3.20s | 28.70s | null | 5 | `present` (0.58s) | ⚠️ YES |
| `event_021` | [`event_021_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_021_proposal_v2.json) | [`event_021_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_021_review_sheet.md) | 0.00s | 3.20s | 4.10s | 3.60s | 60.10s | null | 11 | `present` (51.39s) | ⚠️ YES |
| `event_022` | [`event_022_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_022_proposal_v2.json) | [`event_022_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_022_review_sheet.md) | 0.00s | 2.50s | 3.30s | 3.40s | 45.10s | null | 8 | `present` (2.37s) | ⚠️ YES |
| `event_023` | [`event_023_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_023_proposal_v2.json) | [`event_023_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_023_review_sheet.md) | 0.00s | 2.80s | 3.60s | 3.30s | 43.40s | null | 8 | `absent_observed` | ⚠️ YES |

---

## 4. No-Train Events Candidate Table (3 Events)
| Event ID | Proposal JSON | Review Sheet | Train Present | Horn Status | Audited Exposure | Activity Summary |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `event_001` | [`event_001_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/no_train_events/event_001_proposal_v2.json) | [`event_001_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/no_train_events/event_001_review_sheet.md) | `False` | `null` | 49.057s stream | Continuous mixed road traffic; acoustic horn confounders (CNG/rickshaw) |
| `event_002` | [`event_002_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/no_train_events/event_002_proposal_v2.json) | [`event_002_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/no_train_events/event_002_review_sheet.md) | `False` | `null` | 25.210s stream | Continuous mixed road traffic; acoustic horn confounders (CNG/rickshaw) |
| `event_003` | [`event_003_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/no_train_events/event_003_proposal_v2.json) | [`event_003_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/no_train_events/event_003_review_sheet.md) | `False` | `null` | 46.521s stream | Continuous mixed road traffic; acoustic horn confounders (CNG/rickshaw) |

---

## 5. Engine-Only Event Candidate Table (1 Event)
| Event ID | Proposal JSON | Review Sheet | Train Type | Cars | T0 (s) | T1 (s) | T2 (s) | T3 == T4 (s) | T_sc (s) | Horn Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `event_001` | [`event_001_proposal_v2.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/engine_events/event_001_proposal_v2.json) | [`event_001_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/engine_events/event_001_review_sheet.md) | `locomotive_light` | 0 | 0.00s (LC) | 0.00s | 0.00s | **6.20s** | 6.20s | `absent_observed` |

---

## 6. Action Items for Subsequent Human Certification
1. Open each review sheet linked in the tables above.
2. Execute the provided FFmpeg verification commands to inspect native 1080p and 4K candidate frames.
3. Listen to both front and back audio recordings to certify horn status and road-traffic confounders.
4. Adjudicate operational danger-zone boundary landmarks and review R04 independent camera-local timelines.
5. When ready to approve, create certified human review records in `data/ground_truth/reviews/` and certified ground-truth manifests.
