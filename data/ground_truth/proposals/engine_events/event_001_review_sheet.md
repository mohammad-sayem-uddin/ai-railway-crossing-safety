# Ground-Truth Candidate Review Sheet: `event_001`

> [!IMPORTANT]
> **MANDATORY APPROVAL FIREWALL NOTICE:**
> This document contains AI-generated candidate proposals. It is **NOT** approved ground truth.
> Under Ground Truth Protocol v5.0.0, candidate proposals must be manually inspected and certified
> by the human researcher before being eligible for model evaluation.

## 1. Proposal Provenance & Media Hashes
- **Event ID:** `event_001`
- **Event Type:** `REAL_WORLD_ENGINE_ONLY`
- **Proposal ID:** `proposal_event_001_v2`
- **Generated At (UTC):** `2026-10-12T17:10:00Z`
- **Schema Version:** `7.0.0`
- **AI Assistant Model:** `antigravity-multimodal-agent`
- **Prompt Template Version:** `v1.0.0`
- **Prompt Template SHA-256:** `8ea581b1453f72b4673642d510acc4a4e0a9aeb9727ae63ff0c0546b65741a5e`

### Input Media Files
| File Name | Duration (s) | Verified SHA-256 |
| :--- | :--- | :--- |
| `camera_front.mov` | 7.873s | `d91b7d7f9cf4ddb9842d58185b59aed6e45de323a7c364dc15b62398269a0a28` |
| `camera_back.mov` | 9.800s | `80668547f4f5240779a4ab49c28c321e7c3eb2722876e30a2182121294836a72` |

## 2. Train Characteristics & Acoustic Horn
- **Train Present:** `True`
- **Train Direction:** `left_to_right`
- **Train Type:** `locomotive_light`
- **Trailing Cars Count:** `0`
- **Acoustic Horn Status:** `absent_observed`
- **Acoustic Evidence Note:** Front (7.87s) and back (9.80s) media inspected. Single diesel-electric locomotive running light with zero trailing cars. Engine low-frequency rumble recorded; no locomotive pneumatic horn blast. T3 and T4 coincide identically (6.20s) due to single-unit traversal.

## 3. Proposed Canonical Train-Boundary Timestamps
| Boundary | Applicable | Observable | Value (s) | Frame | FPS | Camera | Ambiguous | Visual Rationale |
| :--- | :---: | :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| `T0_first_visible` | True | True | 0.00s | 0 | 29.97 | front | ⚠️ YES | Locomotive already visible on tracks at recording start (Frame 0). Left-censored. |
| `T1_danger_zone_entry` | True | True | 0.00s | 0 | 29.97 | front | ⚠️ YES | Locomotive front already occupies crossing danger zone at t=0.00s. Left-censored. |
| `T2_crossing_occupancy_start` | True | True | 0.00s | 0 | 29.97 | front | ⚠️ YES | Locomotive pilot occupies crossing road lane at t=0.00s. Left-censored. |
| `T3_locomotive_unit_clearance` | True | True | 6.20s | 186 | 30.00 | back | No | Trailing end of single locomotive clears crossing departure boundary on camera_back.mov. |
| `T4_tail_clearance` | True | True | 6.20s | 186 | 30.00 | back | No | Coincident with T3: trailing buffer of single locomotive clears roadway boundary (zero trailing cars). |
| `T_scene_clear` | True | True | 6.20s | 186 | 30.00 | back | No | Locomotive clears camera frame along departure tracks. |

## 4. Forensic Verification Commands (FFmpeg)
Run these terminal commands to view the precise proposed frames:
```bash
# Verify T0_first_visible (0.000s on front camera)
ffmpeg -ss 0.000 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/engine_events/event_001/camera_front.mov -frames:v 1 -q:v 2 preview_event_001_T0_first_visible.jpg
# Verify T1_danger_zone_entry (0.000s on front camera)
ffmpeg -ss 0.000 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/engine_events/event_001/camera_front.mov -frames:v 1 -q:v 2 preview_event_001_T1_danger_zone_entry.jpg
# Verify T2_crossing_occupancy_start (0.000s on front camera)
ffmpeg -ss 0.000 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/engine_events/event_001/camera_front.mov -frames:v 1 -q:v 2 preview_event_001_T2_crossing_occupancy_start.jpg
# Verify T3_locomotive_unit_clearance (6.200s on back camera)
ffmpeg -ss 6.200 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/engine_events/event_001/camera_back.mov -frames:v 1 -q:v 2 preview_event_001_T3_locomotive_unit_clearance.jpg
# Verify T4_tail_clearance (6.200s on back camera)
ffmpeg -ss 6.200 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/engine_events/event_001/camera_back.mov -frames:v 1 -q:v 2 preview_event_001_T4_tail_clearance.jpg
# Verify T_scene_clear (6.200s on back camera)
ffmpeg -ss 6.200 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/engine_events/event_001/camera_back.mov -frames:v 1 -q:v 2 preview_event_001_T_scene_clear.jpg
```

## 5. Camera Synchronization & Geometry Status
> [!NOTE]
> **Prerequisite R03 Status: RETIRED (Operational Danger-Zone Convention Applied)**
> **Prerequisite R04 Status: UNRESOLVED (Camera Synchronization Limitation)**
> - Under Protocol v7.0.0, external site surveys (R03) are retired in favor of documented operational visible landmarks.
> - Inter-camera offsets (R04) remain uncertified; front and back camera timestamps exist in independent media-local timelines.
- **Candidate Front Marker:** locomotive_pilot_crossing
- **Candidate Back Marker:** locomotive_rear_buffer
- **Candidate Offset:** Unmeasured
- **Audited Front Stream Exposure:** `7.873s`
- **Audited Back Stream Exposure:** `9.800s`
- **Audited Combined Stream Exposure:** `17.673s` (stream-seconds; not wall-clock)

## 6. Human Adjudication Decision Checklist
To certify this event for evaluation, the human researcher must:
1. [ ] Inspect extracted frames against candidate boundaries $T_0$–$T_4$.
2. [ ] Confirm or adjust horn status and onset timestamp.
3. [ ] Verify camera alignment markers or declare inter-camera offset unmeasured.
4. [ ] Record human decisions in `data/ground_truth/reviews/{type}/{event_id}_review.json`.
5. [ ] If approved, write certified ground truth with `"approval_status": "APPROVED"` into `data/ground_truth/{type}/{event_id}.json`.
