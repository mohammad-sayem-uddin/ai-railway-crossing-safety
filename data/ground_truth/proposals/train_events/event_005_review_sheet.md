# Ground-Truth Candidate Review Sheet: `event_005`

> [!IMPORTANT]
> **MANDATORY APPROVAL FIREWALL NOTICE:**
> This document contains AI-generated candidate proposals. It is **NOT** approved ground truth.
> Under Ground Truth Protocol v7.0.0, candidate proposals must be manually inspected and certified
> by the human researcher before being eligible for model evaluation.

## 1. Proposal Provenance & Media Hashes
- **Event ID:** `event_005`
- **Event Type:** `REAL_WORLD_TRAIN_EVENT`
- **Proposal ID:** `proposal_event_005_v4`
- **Prior Proposal Ref:** `data/ground_truth/proposals/train_events/event_005_proposal_v3.json`
- **Generated At (UTC):** `2026-10-12T19:25:00Z`
- **Schema Version:** `7.0.0`
- **AI Assistant Model:** `antigravity-multimodal-agent`
- **Prompt Template Version:** `v1.0.0`
- **Prompt Template SHA-256:** `8ea581b1453f72b4673642d510acc4a4e0a9aeb9727ae63ff0c0546b65741a5e`

### Input Media Files
| File Name | Duration (s) | Verified SHA-256 |
| :--- | :--- | :--- |
| `camera_front.mov` | 79.557s | `015ec78146d474385e447232c9c4048263bf0491cfbf265e967bb0d6bf887613` |
| `camera_back.mov` | 78.107s | `55d7498db1449507b9262d9302315606dc1a40e3f99f715150ff90a37f18933e` |

## 2. Train Characteristics & Acoustic Horn
- **Train Present:** `True`
- **Train Direction:** `left_to_right`
- **Train Type:** `passenger`
- **Trailing Cars Count:** `14` (active coaches observed in stream before recording truncation)
- **Acoustic Horn Status:** `present` (Candidate spectral prominence peak detected; listening status: `NOT_LISTENED`)
- **Horn Onset:** `1.28s` on `camera_front.mov` (uncertainty: `±0.25s`)
- **Acoustic Evidence Note:** Candidate horn spectral prominence peak detected on front camera at 1.28s (dimensionless linear peak-to-median ratio 156.7, corresponding to 22.0 dB, fundamental freq 500.0 Hz; back camera spectral prominence peak at 64.13s, linear ratio 17.0, 12.3 dB). Unverified by listening (`NOT_LISTENED`); mandatory human auditory listening check required before certification. Active coaches in view: 14 coaches observed before back recording cutoff.

## 3. Proposed Canonical Train-Boundary Timestamps
| Boundary | Applicable | Observable | Value (s) | Frame | FPS | Camera | Ambiguous | Visual Rationale |
| :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| `T0_first_visible` | True | True | 0.00s | 0 | 29.97 | front | ⚠️ YES | Left-censored stream arrival on camera_front.mov (Frame 0): mid-consist passenger vehicle (Dining Car 1402) occupies full frame at t=0.00s. Locomotive arrival occurred before front recording start (t < 0.00s); excluded from detection-latency denominator. On independent camera_back.mov stream, locomotive pilot is observed entering at t=0.50s (Frame 15). |
| `T1_danger_zone_entry` | True | False | null | null | 29.97 | front | No | Unobservable: Locomotive entered danger zone prior to camera_front.mov recording start (mid-consist vehicle occupies Frame 0). |
| `T2_crossing_occupancy_start` | True | False | null | null | 29.97 | front | No | Unobservable: Locomotive occupied crossing lens plane prior to camera_front.mov recording start. |
| `T3_locomotive_unit_clearance` | True | True | 6.00s | 180 | 30.00 | back | No | Operational Danger-Zone Exit Boundary Convention: Lead locomotive enters camera_back.mov at t=0.50s (Frame 15). At t=5.60s (Frame 168), locomotive rear coupler passes an intermediate trackside landmark (white signal/relay cabinet). Under the canonical exit boundary convention (docs/FINAL_GROUND_TRUTH_PROTOCOL.md §2.1 and §2.4), T3 and T4 must denote clearance of the exact same conceptual departure boundary plane. The canonical danger-zone departure boundary plane is the transverse departure boundary plane, which the lead locomotive trailing coupler clears at t=6.00s (Frame 180). Setting T3=6.00s (Frame 180) aligns T3 with canonical exit-plane semantics and resolves the landmark ambiguity from proposal v3. |
| `T4_tail_clearance` | True | False | null | null | 30.00 | back | No | Unobservable (right-censored): camera_back.mov recording terminates prematurely at t=78.107s (Frame 2342) while trailing passenger coaches 1084 and 1032 are still actively traversing the field of view. The rear buffer of the final rail vehicle never cleared the crossing boundary during recording. Replaces invalid 75.8s candidate from proposal v2. |
| `T_scene_clear` | True | False | null | null | 30.00 | back | ⚠️ YES | Unobservable: recording terminates at 78.107s while train actively occupies track. |

## 4. Forensic Verification Commands (FFmpeg)
Run these terminal commands to view the precise proposed frames:
```bash
# Verify T0_first_visible on front camera (mid-consist Dining Car 1402 at frame 0)
ffmpeg -ss 0.000 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/train_events/event_005/camera_front.mov -frames:v 1 -q:v 2 preview_event_005_T0_front.jpg

# Verify back camera locomotive entry at 0.500s (Frame 15)
ffmpeg -ss 0.500 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/train_events/event_005/camera_back.mov -frames:v 1 -q:v 2 preview_event_005_loco_entry_back.jpg

# Verify intermediate signal cabinet landmark at 5.600s (Frame 168 on back camera)
ffmpeg -ss 5.600 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/train_events/event_005/camera_back.mov -frames:v 1 -q:v 2 preview_event_005_intermediate_cabinet.jpg

# Verify T3_locomotive_unit_clearance canonical exit boundary plane (6.000s, Frame 180 on back camera)
ffmpeg -ss 6.000 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/train_events/event_005/camera_back.mov -frames:v 1 -q:v 2 preview_event_005_T3_loco_clearance.jpg

# Verify final frame right-censoring at 78.100s (coaches 1084 & 1032 actively occupying track)
ffmpeg -ss 78.050 -i /Users/sayemuddin/Desktop/Train_automation/data/raw/layer_b/v2/train_events/event_005/camera_back.mov -frames:v 1 -q:v 2 preview_event_005_back_final_frame.jpg
```

## 5. Camera Synchronization & Geometry Status
> [!NOTE]
> **Prerequisite R03 Status: RETIRED (Operational Danger-Zone Convention Applied)**
> **Prerequisite R04 Status: UNRESOLVED (Camera Synchronization Limitation)**
> - Under Protocol v7.0.0, external site surveys (R03) are retired in favor of documented operational visible landmarks.
> - Inter-camera offsets (R04) remain uncertified; front and back camera timestamps exist in independent media-local timelines.
- **Candidate Front Marker:** turnout_frog_boundary
- **Candidate Back Marker:** vendor_stall_clearance_line
- **Candidate Offset (s):** `null` (hardware synchronization pending empirical calibration)
- **Combined Stream Exposure:** `157.664s` (summed stream exposure; NOT concurrent wall-clock exposure)

## 6. Human Reviewer Certification Checklist
- [ ] Confirm $T_0$ front camera frame 0 shows mid-consist Dining Car 1402 (left-censored arrival).
- [ ] Confirm $T_1$ and $T_2$ are unobservable on front camera due to pre-recording passage.
- [ ] Confirm $T_3 = 6.00\text{s}$ (Frame 180) on back camera reflects locomotive rear coupler clearance across the canonical transverse departure boundary plane (and that 5.60s / Frame 168 represents the intermediate signal cabinet landmark).
- [ ] Confirm $T_4$ is unobservable on back camera due to stream termination at 78.107s while trailing coaches are still traversing the crossing.
- [ ] Listen to audio tracks on both streams to verify whether the 1.28s acoustic peak represents a locomotive horn or a road traffic horn.
