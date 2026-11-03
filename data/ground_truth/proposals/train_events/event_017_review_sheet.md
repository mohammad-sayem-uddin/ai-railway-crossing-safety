# Ground-Truth Candidate Review Sheet: `event_017`

> [!IMPORTANT]
> **MANDATORY APPROVAL FIREWALL NOTICE:**
> This document contains AI-generated candidate proposals. It is **NOT** approved ground truth.
> Under Ground Truth Protocol v5.0.0, candidate proposals must be manually inspected and certified
> by the human researcher before being eligible for model evaluation.

## 1. Proposal Provenance & Media Hashes
- **Event ID:** `event_017`
- **Event Type:** `REAL_WORLD_TRAIN_EVENT`
- **Proposal ID:** `proposal_event_017_v2`
- **Generated At (UTC):** `2026-10-12T17:10:00Z`
- **Schema Version:** `7.0.0`
- **AI Assistant Model:** `antigravity-multimodal-agent`
- **Prompt Template Version:** `v1.0.0`
- **Prompt Template SHA-256:** `8ea581b1453f72b4673642d510acc4a4e0a9aeb9727ae63ff0c0546b65741a5e`

### Input Media Files
| File Name | Duration (s) | Verified SHA-256 |
| :--- | :--- | :--- |
| `camera_front.mov` | 81.658s | `188ff5ffd34d71080f8cdbaf08f03837703b0c79b47bbebbbf07d4d3028ebfe3` |
| `camera_back.mov` | 83.773s | `7b0d48f364c2f0a842c3cdca4793d634ee9743ce7c947b3b356c646865854d95` |

## 2. Train Characteristics & Acoustic Horn
- **Train Present:** `True`
- **Train Direction:** `left_to_right`
- **Train Type:** `passenger`
- **Trailing Cars Count:** `15`
- **Acoustic Horn Status:** `present`
- **Horn Onset:** `0.83s` (uncertainty: `±0.25s`)
- **Acoustic Evidence Note:** Candidate horn present (onset 0.83s, peak SNR 27.2, fundamental freq 648.4 Hz). Acoustic spectral audit verified against 16kHz audio track. Researcher must perform listening check before final approval. Verified trailing car count: 15 coaches.

## 3. Proposed Canonical Train-Boundary Timestamps
| Boundary | Applicable | Observable | Value (s) | Frame | FPS | Camera | Ambiguous | Visual Rationale |
| :--- | :---: | :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| `T0_first_visible` | True | True | 0.00s | 0 | 29.97 | front | ⚠️ YES | Candidate first observed train frame in available recording (Frame 0). Left-censored: locomotive is already visible approaching under corridor at recording start (t=0.00s); true physical visual arrival occurred at t <= 0.00s. Excluded from physical detection-latency denominator. |
| `T1_danger_zone_entry` | True | True | 2.80s | 84 | 29.97 | front | No | Operational Danger-Zone Annotation Convention (Protocol v7.0.0 §2.4, retiring R03): locomotive cowcatcher reaches turnout switch frog / pedestrian approach line on camera_front.mov. |
| `T2_crossing_occupancy_start` | True | True | 3.60s | 108 | 29.97 | front | No | Operational Danger-Zone Annotation Convention (Protocol v7.0.0 §2.4): locomotive pilot crosses front camera transverse lens plane / roadway occupancy line on camera_front.mov. |
| `T3_locomotive_unit_clearance` | True | True | 4.20s | 126 | 30.00 | back | No | Operational Danger-Zone Annotation Convention: trailing edge / rear coupler of lead locomotive clears vegetable vendor stall clearance line on camera_back.mov. |
| `T4_tail_clearance` | True | True | 82.50s | 2475 | 30.00 | back | No | Operational Danger-Zone Annotation Convention: rear buffer of final rail vehicle (#15) clears departure roadway boundary on camera_back.mov, permitting road and pedestrian crossing resumption. |
| `T_scene_clear` | True | False | null | null | 30.00 | back | ⚠️ YES | Recording terminates while train is still visible receding along departure tracks. |

## 4. Forensic Verification Commands (FFmpeg)
Run these terminal commands to view the precise proposed frames:
```bash
# Verify T0_first_visible (0.000s on front camera)
ffmpeg -ss 0.000 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/train_events/event_017/camera_front.mov -frames:v 1 -q:v 2 preview_event_017_T0_first_visible.jpg
# Verify T1_danger_zone_entry (2.800s on front camera)
ffmpeg -ss 2.800 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/train_events/event_017/camera_front.mov -frames:v 1 -q:v 2 preview_event_017_T1_danger_zone_entry.jpg
# Verify T2_crossing_occupancy_start (3.600s on front camera)
ffmpeg -ss 3.600 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/train_events/event_017/camera_front.mov -frames:v 1 -q:v 2 preview_event_017_T2_crossing_occupancy_start.jpg
# Verify T3_locomotive_unit_clearance (4.200s on back camera)
ffmpeg -ss 4.200 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/train_events/event_017/camera_back.mov -frames:v 1 -q:v 2 preview_event_017_T3_locomotive_unit_clearance.jpg
# Verify T4_tail_clearance (82.500s on back camera)
ffmpeg -ss 82.500 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/train_events/event_017/camera_back.mov -frames:v 1 -q:v 2 preview_event_017_T4_tail_clearance.jpg
```

## 5. Camera Synchronization & Geometry Status
> [!NOTE]
> **Prerequisite R03 Status: RETIRED (Operational Danger-Zone Convention Applied)**
> **Prerequisite R04 Status: UNRESOLVED (Camera Synchronization Limitation)**
> - Under Protocol v7.0.0, external site surveys (R03) are retired in favor of documented operational visible landmarks.
> - Inter-camera offsets (R04) remain uncertified; front and back camera timestamps exist in independent media-local timelines.
- **Candidate Front Marker:** turnout_frog_boundary
- **Candidate Back Marker:** vendor_stall_clearance_line
- **Candidate Offset:** Unmeasured
- **Audited Front Stream Exposure:** `81.658s`
- **Audited Back Stream Exposure:** `83.773s`
- **Audited Combined Stream Exposure:** `165.431s` (stream-seconds; not wall-clock)

## 6. Human Adjudication Decision Checklist
To certify this event for evaluation, the human researcher must:
1. [ ] Inspect extracted frames against candidate boundaries $T_0$–$T_4$.
2. [ ] Confirm or adjust horn status and onset timestamp.
3. [ ] Verify camera alignment markers or declare inter-camera offset unmeasured.
4. [ ] Record human decisions in `data/ground_truth/reviews/{type}/{event_id}_review.json`.
5. [ ] If approved, write certified ground truth with `"approval_status": "APPROVED"` into `data/ground_truth/{type}/{event_id}.json`.
