# Ground-Truth Candidate Review Sheet: `event_003`

> [!IMPORTANT]
> **MANDATORY APPROVAL FIREWALL NOTICE:**
> This document contains AI-generated candidate proposals. It is **NOT** approved ground truth.
> Under Ground Truth Protocol v5.0.0, candidate proposals must be manually inspected and certified
> by the human researcher before being eligible for model evaluation.

## 1. Proposal Provenance & Media Hashes
- **Event ID:** `event_003`
- **Event Type:** `REAL_WORLD_NO_TRAIN`
- **Proposal ID:** `proposal_event_003_v2`
- **Generated At (UTC):** `2026-10-12T17:10:00Z`
- **Schema Version:** `7.0.0`
- **AI Assistant Model:** `antigravity-multimodal-agent`
- **Prompt Template Version:** `v1.0.0`
- **Prompt Template SHA-256:** `8ea581b1453f72b4673642d510acc4a4e0a9aeb9727ae63ff0c0546b65741a5e`

### Input Media Files
| File Name | Duration (s) | Verified SHA-256 |
| :--- | :--- | :--- |
| `camera_front.mov` | 23.788s | `969c8b118996d56d5593f8a3cb6ef9e16e571d4829076824952663d719239205` |
| `camera_back.mov` | 22.733s | `4914515714eb1ca8a282f61112afcfb11391dd2ec08543796611e22b884b4d9c` |

## 2. Train Characteristics & Acoustic Horn
- **Train Present:** `False`
- **Train Direction:** `N/A`
- **Train Type:** `N/A`
- **Trailing Cars Count:** `N/A`
- **Acoustic Horn Status:** `N/A`
- **Horn Reason:** No train present in recording. Ambient road traffic horns (CNG/rickshaw) present in audio.
- **Acoustic Evidence Note:** Full 23.8s front and 22.7s back recordings inspected. Zero rail vehicles observable on tracks. Continuous road traffic and pedestrian activity.

## 3. Proposed Canonical Train-Boundary Timestamps
| Boundary | Applicable | Observable | Value (s) | Frame | FPS | Camera | Ambiguous | Visual Rationale |
| :--- | :---: | :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| `T0_first_visible` | False | False | null | null | null | null | No | Not applicable: no train present. |
| `T1_danger_zone_entry` | False | False | null | null | null | null | No | Not applicable: no train present. |
| `T2_crossing_occupancy_start` | False | False | null | null | null | null | No | Not applicable: no train present. |
| `T3_locomotive_unit_clearance` | False | False | null | null | null | null | No | Not applicable: no train present. |
| `T4_tail_clearance` | False | False | null | null | null | null | No | Not applicable: no train present. |
| `T_scene_clear` | False | False | null | null | null | null | No | Not applicable: no train present. |

## 4. Forensic Verification Commands (FFmpeg)
Run these terminal commands to view the precise proposed frames:
```bash
```

## 5. Camera Synchronization & Geometry Status
> [!NOTE]
> **Prerequisite R03 Status: RETIRED (Operational Danger-Zone Convention Applied)**
> **Prerequisite R04 Status: UNRESOLVED (Camera Synchronization Limitation)**
> - Under Protocol v7.0.0, external site surveys (R03) are retired in favor of documented operational visible landmarks.
> - Inter-camera offsets (R04) remain uncertified; front and back camera timestamps exist in independent media-local timelines.
- **Candidate Front Marker:** None
- **Candidate Back Marker:** None
- **Candidate Offset:** Unmeasured
- **Audited Front Stream Exposure:** `23.788s`
- **Audited Back Stream Exposure:** `22.733s`
- **Audited Combined Stream Exposure:** `46.521s` (stream-seconds; not wall-clock)

## 6. Human Adjudication Decision Checklist
To certify this event for evaluation, the human researcher must:
1. [ ] Inspect extracted frames against candidate boundaries $T_0$–$T_4$.
2. [ ] Confirm or adjust horn status and onset timestamp.
3. [ ] Verify camera alignment markers or declare inter-camera offset unmeasured.
4. [ ] Record human decisions in `data/ground_truth/reviews/{type}/{event_id}_review.json`.
5. [ ] If approved, write certified ground truth with `"approval_status": "APPROVED"` into `data/ground_truth/{type}/{event_id}.json`.
