# Final Ground Truth Annotation Protocol

**Document Version:** 6.0.0  
**Date:** 2026-10-09  
**Status:** PREREQUISITE SPECIFICATION — AI-Assisted, Human-Verified Canonical Ground Truth Protocol  
**Authority:** Referenced by `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` §6

---

## 1. AI-Assisted, Human-Verified Ground-Truth Architecture & Independence Policy

To reconcile rigorous methodological validity with practical annotation scalability, this protocol establishes an **AI-assisted, human-verified annotation lifecycle**. AI model assistance is permitted exclusively as an offline drafting tool; all authoritative ground truth is certified strictly by a qualified human researcher through frame-by-frame verification.

### 1.1 Three-Stage Annotation Lifecycle

Ground-truth creation is strictly partitioned into three sequential, auditable stages:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: AI Proposal Generation (Gemini Offline Annotation Assistant)       │
│ - Ingests raw video/audio media files from data/raw/layer_b/v2/             │
│ - Proposes candidate boundary timestamps (T0–T4), horn status, metadata     │
│ - Flags visual/acoustic ambiguities and potential unobservable intervals   │
│ - Output: data/ground_truth/proposals/ (IMMUTABLE, READ-ONLY ARCHIVE)       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: Human Verification & Frame-by-Frame Adjudication (Researcher)       │
│ - Opens raw video frames and audio in independent visual inspection tooling  │
│ - Verifies or corrects every proposed timestamp, frame index, and category   │
│ - Explicitly marks unobservable boundaries (observable: false, not_evaluable)│
│ - Logs per-field decision: accepted | corrected | marked_unobservable        │
│ - Output: data/ground_truth/reviews/ (AUDITABLE HUMAN REVIEW HISTORY)       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: Approved Ground Truth & Manifest Freeze (Evaluation Ingestion)     │
│ - Human researcher explicitly certifies approval_status: "APPROVED"         │
│ - Output: data/ground_truth/{train_events,no_train_events,engine_events}/    │
│ - Prerequisite R02: Hashes locked in data/ground_truth/ground_truth_manifest.json│
│ - ONLY Stage 3 approved artifacts are ingested by GroundTruthLoader         │
└─────────────────────────────────────────────────────────────────────────────┘
```

1. **Stage 1 (AI Proposal):** Gemini (acting strictly as an offline annotation assistant, external to the evaluated system) inspects raw media files and outputs candidate annotations with prompt metadata, model version, and potential ambiguity flags. Raw AI proposals are immutable and never ingested into evaluation.
2. **Stage 2 (Human Verification):** The human researcher opens the original video frames and embedded audio tracks, inspects physical boundaries against exact frame numbers, accepts or corrects candidate values, adjudicates ambiguities, and records a structured review history.
3. **Stage 3 (Approved Ground Truth):** Only human-reviewed and explicitly approved annotations (`approval_status: "APPROVED"`) enter the final evaluation dataset. The final dataset MUST NOT contain unreviewed AI suggestions or auto-approved labels.

### 1.2 Separation from Evaluated System & Anti-Leakage Firewall

The annotation assistant is an external offline drafting utility and MUST NOT have any connection to the runtime railway crossing safety architecture under test:

1. **Firewall Against Evaluated Models:** The annotation assistant and human reviewer must NOT use, ingest, or condition labels upon:
   - YOLOv8n detector predictions or bounding boxes from `experiments/vision/39f402dfe460/`
   - Audio V3 CNN predictions or spectrogram inferences from `experiments/audio/train_audio_v3/` or `RUN_20261008_AUDIO_V3_ESC50`
   - Multimodal fusion engine outputs, EMA states, or state-machine logs
   - Historical evaluation reports or previous baseline summaries (e.g., legacy B0–B7 reports)
2. **Derivation Exclusively from Raw Sensor Data:** Ground truth must be derived entirely from the physical visual scene (train contours, railhead contact, gate lines) and raw audio waveforms, preserving true ontological independence.
3. **No Target Leakage:** Using predictions of the evaluated system to establish or bias ground-truth labels constitutes circular reasoning and invalidates scientific evaluation.

### 1.3 Strict Anti-Synthesis & Anti-Auto-Approval Mandates

1. **Prohibition on Automated Label Synthesis:** Evaluation scripts, runners, loaders, and test harnesses are **strictly forbidden** from generating, predicting, interpolating, or synthesizing ground-truth timestamps.
2. **Prohibition on Auto-Approval:** No script or agent may automatically change `approval_status` to `"APPROVED"` without verified human researcher sign-off.
3. **Fail-Fast Ingestion Enforcement:**
   - The evaluation runner must invoke `GroundTruthLoader.validate_all()`.
   - If any required event file is missing, contains unapproved status, contains unreviewed AI proposals, contains unauthorized `null` values without `unobservable: true` and documented `reason`, or fails SHA-256 verification against `ground_truth_manifest.json`, **evaluation must immediately halt with a fatal error**.

### 1.4 Directory Segregation & Access Control

To ensure the evaluation runner cannot accidentally ingest draft proposals or unreviewed files, the filesystem is partitioned into strict directories:

```
data/ground_truth/
├── proposals/                 # STAGE 1: Immutable AI proposals (NEVER READ BY EVALUATOR)
│   ├── train_events/          # event_XXX_proposal.json
│   ├── no_train_events/       # event_XXX_proposal.json
│   └── engine_events/         # event_001_proposal.json
├── reviews/                   # STAGE 2: Human review audit logs (NEVER READ BY EVALUATOR)
│   ├── train_events/          # event_XXX_review.json
│   ├── no_train_events/       # event_XXX_review.json
│   └── engine_events/         # event_001_review.json
├── train_events/              # STAGE 3: Approved full-train annotations (READ BY EVALUATOR)
│   └── event_001.json ... event_023.json
├── no_train_events/           # STAGE 3: Approved no-train annotations (READ BY EVALUATOR)
│   └── event_001.json ... event_003.json
├── engine_events/             # STAGE 3: Approved engine-only annotation (READ BY EVALUATOR)
│   └── event_001.json
└── ground_truth_manifest.json # Cryptographic SHA-256 freeze manifest (R02)
```

The evaluator loader is hard-coded to load ONLY from `data/ground_truth/{train_events,no_train_events,engine_events}/` and asserts that every file has `"approval_status": "APPROVED"`.

---

## 2. Canonical Train-Boundary Definitions ($T_0$ through $T_4$)

To resolve prior ambiguities between locomotive departure and train tail clearance, this protocol establishes a single, unambiguous **Canonical Train-Boundary Taxonomy**.

### 2.1 Canonical Boundary Table

| Marker | Canonical Name | Physical Scene Definition | Primary Camera | Safety Criticality & Role |
|:---:|---|---|:---:|---|
| **$T_0$** | **First Visual Appearance** | Earliest frame where the approaching train is visually identifiable as a railway vehicle. If train is already in frame at recording start ($t=0.00\text{s}$), see §2.3. | Front (Approach) | Baseline for **Detection Latency** ($T_{\text{detect}} - T_0$). Subject to left-censoring rules. |
| **$T_1$** | **Danger Zone Entry** | Earliest frame where the leading edge (front bumper / cowcatcher) of the locomotive crosses into the physical crossing danger zone. | Front (Approach) | Baseline for **Warning Lead Time** ($T_1 - T_{\text{detect}}$). |
| **$T_2$** | **Crossing Occupancy Start** | Earliest frame where the locomotive body fully occupies the road crossing danger zone. | Front / Back | Road is actively blocked by railway vehicle. |
| **$T_3$** | **Locomotive Unit Clearance (rear end exits danger zone)** | Frame where the trailing edge / rear coupler of the leading locomotive unit(s) completely clears the defined crossing danger zone boundary, while trailing railcars continue traversing. | Back (Departure) | **Diagnostic Marker:** Isolates transition from motive power to trailing railcars; tests detector continuity across vehicle types. Distinguishes lead unit clearance from intermediate locomotive front exit. |
| **$T_4$** | **Tail Clearance (Last Vehicle Exit)** | Frame where the trailing edge / rear buffer of the final railcar completely exits the physical crossing danger zone. | Back (Departure) | **Primary Safety Clearance Boundary:** End of physical road collision hazard. Baseline for **POR** and **Clearance Latency** ($T_{\text{open}} - T_4$). |
| **$T_{\text{scene\_clear}}$** | **Scene Clear** | Earliest frame where the train has completely vacated all camera fields of view and track approaches. | Both Cameras | Scene verification; camera optical recovery. |
| **$T_{\text{horn}}$** | **Acoustic Horn Onset** | Earliest frame/timestamp of audible locomotive horn blast on embedded audio. | Embedded Audio | Acoustic lead-time reference; $T_{\text{horn}} < T_1$. |

### 2.2 Physical Boundary Distinctions and Hazard Interval

- **Physical Distinction — Locomotive Front Exit vs. Locomotive Unit Clearance:**
  - As a train traverses the crossing, the locomotive's front bumper / cowcatcher crosses the departure boundary first. This is an intermediate crossing traversal phase and does **NOT** constitute locomotive clearance.
  - Complete **Locomotive Unit Clearance ($T_3$)** occurs strictly when the *trailing edge / rear coupler / rear bogie* of the lead locomotive unit vacates the defined crossing danger zone.
  - **Tail Clearance ($T_4$):** $T_4$ is strictly preserved for the trailing edge of the *final vehicle / last railcar* of the entire consist.
  - **Diagnostic Value of Separating $T_3$ and $T_4$:** Detectors trained heavily on diesel locomotives frequently experience detection dropout when the locomotive vacates the crossing and plain passenger/freight cars continue traversing. If a gate opens between $T_3$ and $T_4$, it indicates catastrophic detector dropout while the roadway remains physically obstructed.
- **Physical Hazard Occupancy Interval:** The road crossing danger zone is physically obstructed during:
  $$t \in [T_1, T_4]$$
- **Premature Opening Rate (POR):** Any gate opening command or gate ascent initiated while $t < T_4$ (and $t \ge T_1$) is a **Premature Opening**.
- **Clearance Latency:** Delay between physical tail clearance and gate opening command:
  $$\text{Clearance Latency} = T_{\text{open}} - T_4$$
- **Engine-Only Event ($N=1$):** Because an engine-only train has zero trailing railcars, the locomotive is both the leading motive unit and the final vehicle, yielding:
  $$T_3 \equiv T_4 \quad (\text{Locomotive Unit Clearance} \equiv \text{Tail Clearance})$$

### 2.3 Left-Censored $T_0$ Definition & Latency Denominator Rules

When an approaching train is already visible in the camera field of view in frame 0 of the available recording ($t = 0.000\,\text{s}$, as in `event_001`):
1. **Physical Reality:** The true physical first appearance down the track corridor occurred prior to recording initiation ($T_{0,\text{physical}} \le 0.000\,\text{s}$). The true appearance timestamp is **left-censored**.
2. **Candidate Representation:**
   - In candidate proposals and review sheets, $T_0 = 0.00\,\text{s}$ is retained strictly as a **candidate recording-relative first observed frame** (`candidate_observable: true`, `value_s: 0.0`, `ambiguity_flag: true`).
   - The true physical onset is marked `left_censored` in rationale documentation. Fabricating a pre-recording timestamp (e.g., negative seconds) is strictly forbidden.
3. **Metric Calculation & Denominator Rules:**
   - True Detection Latency ($\Delta t_{\text{detect}} = T_{\text{detect}} - T_{0,\text{physical}}$) **cannot be computed** because the true denominator baseline is unknown. Calculating latency against $0.00\,\text{s}$ introduces an artificial lower bound that distorts physical reaction time.
   - **Mandatory Rule:** Left-censored events **MUST BE EXCLUDED** from the true physical detection-latency calculation denominator, marked as `not_evaluable` / `left_censored`.
   - **Exploratory Lower-Bound Exception:** If an evaluation report presents an observed recording-relative detection latency ($T_{\text{detect}} - 0.00\,\text{s}$), it must be reported in a dedicated exploratory lower-bound column with explicit left-censoring disclosure and NEVER pooled into unadjusted physical detection latency averages.

### 2.4 Crossing Geometry & Landmark Separation Under Prerequisite R03

Under **Prerequisite R03**, the repository currently contains **no surveyed geometry sheets, road line measurements, gate coordinates, or physical crossing boundary documentation** for Crossing A or Crossing B.
1. **Provisional Visual Landmarks:** Visible track features (e.g., turnout frog for $T_1$, camera lens transverse plane for $T_2$, vegetable vendor cart line / pedestrian surge line for $T_4$) represent **provisional visual landmarks**.
2. **Prohibition on Premature Designation:** Researchers and automated agents are strictly forbidden from designating visible landmarks as certified physical danger-zone boundaries without surveyed empirical evidence.
3. **Provisional Status:** In candidate proposals and reviews, $T_1$, $T_2$, and $T_4$ must carry `ambiguity_flag: true` and remain provisional until R03 crossing geometry is documented and certified. Acoustic engine-rumble peaks are rejected as substitutes for physical visual danger-zone boundaries.

---

## 3. Event-Type-Aware Field Applicability Matrix

To prevent validation failures on valid negative recordings, ground truth fields are classified as:
- **REQ (Required):** Must be present and non-null if observable.
- **POT_UNOBS (Potentially Unobservable):** Required if observable; if unobservable, value is `null`, `observable: false`, `not_evaluable: true`, with mandatory `reason`.
- **NA (Not Applicable):** Concept does not exist for this event type. Value MUST be `null`, `applicable: false`. Never raises an unobservable error.

| Field / Boundary Marker | Full-Train Events ($N=23$) | No-Train Events ($N=3$) | Engine-Only Event ($N=1$) |
|---|:---:|:---:|:---:|
| `event_id` | **REQ** | **REQ** | **REQ** |
| `event_type` | `REAL_WORLD_TRAIN_EVENT` | `REAL_WORLD_NO_TRAIN` | `REAL_WORLD_ENGINE_ONLY` |
| `crossing_id` | **REQ** | **REQ** | **REQ** |
| `session_id` | **REQ** | **REQ** | **REQ** |
| `train_present` | Strictly `true` | Strictly `false` | Strictly `true` |
| `train_type` | **REQ** (`passenger`/`freight`/`mixed`) | **NA** (`null`, `applicable: false`) | Strictly `engine_only` |
| `train_direction` | **REQ** (`left_to_right` / `right_to_left`) | **NA** (`null`, `applicable: false`) | **REQ** |
| `trailing_cars_count` | **REQ** (Integer $\ge 1$) | **NA** (`null`, `applicable: false`) | **NA** (`null` or `0`, `applicable: false`) |
| **$T_0$ (First Visible)** | **POT_UNOBS** (see §2.3 for left-censoring) | **NA** (`null`, `applicable: false`) | **POT_UNOBS** |
| **$T_1$ (Zone Entry)** | **POT_UNOBS** | **NA** (`null`, `applicable: false`) | **POT_UNOBS** |
| **$T_2$ (Occupancy Start)** | **POT_UNOBS** | **NA** (`null`, `applicable: false`) | **POT_UNOBS** |
| **$T_3$ (Locomotive Unit Clearance)** | **POT_UNOBS** | **NA** (`null`, `applicable: false`) | Coincident with $T_4$ ($T_3 \equiv T_4$) |
| **$T_4$ (Tail Clearance)** | **POT_UNOBS** | **NA** (`null`, `applicable: false`) | **POT_UNOBS** (same as $T_3$) |
| **$T_{\text{scene\_clear}}$** | **POT_UNOBS** | **NA** (`null`, `applicable: false`) | **POT_UNOBS** |
| **$T_{\text{horn}}$ (Horn Onset)** | **POT_UNOBS** (see `horn_status` enum below) | **NA** (`horn_not_applicable: true`) | **POT_UNOBS** (see `horn_status` enum below) |
| `evaluation_start_s` | **REQ** (Typically `0.0`) | **REQ** (`0.0`) | **REQ** (`0.0`) |
| `evaluation_end_s` | **REQ** (Container min duration) | **REQ** (Container min duration) | **REQ** (Container min duration) |
| `total_evaluable_duration_s` | **REQ** | **REQ** | **REQ** |
| `camera_alignment` | **REQ** | **REQ** | **REQ** |
| `verification_metadata` | **REQ** | **REQ** | **REQ** |
| `activity_log` | Optional / Recommended | **REQ** (road traffic events) | Optional / Recommended |

### 3.1 Canonical Horn Ground-Truth Schema (`horn_status`)

The legacy `horn_audible` field (`"yes"` / `"no"` / `"uncertain"`) is replaced by a structured enum:

| `horn_status` Value | Meaning | `horn_onset_s` | `horn_uncertainty_s` | `horn_reason` |
|---|---|:---:|:---:|---|
| `"present"` | Horn onset is audibly established on audio track. | **Required** (float, seconds) | **Required** (float) | Optional (may be `null`). |
| `"absent_observed"` | Audio is sufficiently available and clear, but no horn is heard during the event. | `null` | `null` | Optional (may be `null`). |
| `"unobservable"` | Horn presence cannot be determined because audio is missing, clipped, obscured, or otherwise insufficient. | `null` | `null` | **Required** (non-empty string explaining why). |

**No-train events:** Set `horn_not_applicable: true` and `horn_status: null`. The horn concept does not exist for negative-control recordings.

**GroundTruthLoader requirements:**
- Reject any annotation containing the legacy `horn_audible` field.
- If `horn_status == "present"`, require `horn_onset_s` to be a non-null float.
- If `horn_status == "unobservable"`, require `horn_reason` to be a non-null, non-empty string.
- If `horn_not_applicable == true`, require `horn_status`, `horn_onset_s`, and `horn_uncertainty_s` to be `null`.

---

## 4. No-Train Exposure & Nuisance-Alarm Counting Rules

### 4.1 Physical Audit of No-Train Event Durations
Audit of the three physical recordings in `data/raw/layer_b/v2/no_train_events/` yielded exact video container lengths:

| Event ID | Front Camera Duration | Back Camera Duration | Front + Back Stream Seconds |
|---|:---:|:---:|:---:|
| `event_001` | 24.635 s | 24.422 s | 49.057 s |
| `event_002` | 11.877 s | 13.333 s | 25.210 s |
| `event_003` | 23.788 s | 22.733 s | 46.521 s |
| **Cohort Total** | **60.300 s** | **60.488 s** | **120.788 s** ($\approx 120.8\text{ s}$) |

> [!WARNING]
> **Concurrent overlap is unresolved.** The previous `min(front, back)` formula yielding 59.032s assumed the shorter stream is fully contained within the longer on a shared timeline. Video container `creation_time` metadata shows dates on different calendar days across paired cameras (e.g., event_001: front = 2026-10-06, back = 2026-10-04), indicating these timestamps cannot establish recording start offsets. No measured inter-camera temporal offset ($\Delta t$) exists for any no-train event.
>
> **Reliable denominators:** Per-camera stream durations and aggregate stream exposure ($T_{\text{sensor}} = 120.788\text{ s}$) are directly measured and reliable. Concurrent wall-clock overlap may only be reported after Prerequisite **R04** is completed.

### 4.2 Exact Exposure Denominators Defined
To avoid denominator ambiguity, evaluations must report metrics against these explicit exposure quantities:
1. **Individual Camera Stream Exposure ($T_{\text{cam}}$):**
   - Front Camera Stream: $60.300\text{ s}$
   - Back Camera Stream: $60.488\text{ s}$
2. **Aggregate Sensor Stream Exposure ($T_{\text{sensor}}$):**
   $$T_{\text{sensor}} = T_{\text{front}} + T_{\text{back}} = 120.788\text{ camera-stream-seconds}$$
3. **Concurrent Wall-Clock Observation ($T_{\text{wall}}$):** **UNRESOLVED** pending per-event inter-camera offset measurement (Prerequisite R04). If R04 is completed and validates full containment of the shorter stream, concurrent overlap may be reported as a secondary denominator.

### 4.3 Multi-Level Nuisance Alarm Counting Rules
A single physical road object (e.g., a passing delivery truck) can trigger both cameras and audio simultaneously. The evaluator must report three distinct counting levels:

1. **Camera-Level False Detections ($N_{\text{cam\_FP}}$):**
   - Count of individual video frames on Camera 1 and Camera 2 where YOLO detection confidence exceeds threshold ($\ge 0.35$).
   - Reported unaggregated per camera: `front_false_frames`, `back_false_frames`.
2. **Acoustic False Detections ($N_{\text{audio\_FP}}$):**
   - Count of 1.0s audio windows where Audio V3 prediction exceeds operating threshold ($p_{\text{audio}} \ge 0.3700$) in the confirmed absence of a train.
3. **System-Level Nuisance Warning / Closure Episodes ($N_{\text{nuisance\_episodes}}$):**
   - Temporally clustered, contiguous time episodes where the fused system commanded an erroneous state transition:
     `IDLE` $\to$ `APPROACHING`, `WARNING`, `GATE_CLOSING`, or `TRAIN_PRESENT`.
   - Simultaneous visual detections across both cameras within the evidence confirmation window ($\le 0.4\text{s}$) are fused into **one single nuisance episode**, not double-counted.

### 4.4 Operational Limitation Mandate
- Total exposure is approximately **120.8 camera-stream-seconds** of real-world observation (concurrent overlap unresolved).
- **Prohibition:** All nuisance counts are populated exclusively from completed evaluation replay — never predetermined. Extrapolating ≈120.8 stream-seconds to an hourly operational false-alarm rate ($\text{FA/hr}$) carries extreme statistical uncertainty. Reporting MUST display observed raw counts alongside per-stream exposure. Any calculated $\text{FA/hr}$ must be explicitly labeled: **"Exploratory pilot extrapolation under ≈120.8 stream-seconds exposure; highly uncertain."**

---

## 5. Camera Alignment & Offset Specification

1. **No Assumed Uncertainties:** Blanket assumptions (e.g. $\pm 0.033\text{s}$ or $\pm 0.1\text{s}$) are prohibited.
2. **Per-Event Measured Offset:**
   $$\Delta t = t_{\text{back}} - t_{\text{front}}$$
3. **AI Role vs Empirical Evidence:** While the AI annotation assistant may point out candidate visual or acoustic synchronization points (e.g. horn onset transient or vehicle landmark), the assistant **cannot certify or prove an inter-camera temporal offset** without empirical measurement. All reported offsets must be based on reviewable evidence with documented method and justified uncertainty $\delta$.
4. **Alignment Status Eligibility:**
   - `aligned` ($\delta \le 0.5\text{s}$): Eligible for all cross-camera temporal metrics.
   - `partially_aligned` ($0.5\text{s} < \delta \le 2.0\text{s}$): Eligible for event-level presence detection; latencies reported with error bounds.
   - `unaligned` ($\delta > 2.0\text{s}$ or unmeasured): **Strictly excluded** from joint Warning Lead Time and Clearance Latency metrics.

---

## 6. Complete JSON Annotation Schemas

### 6.0 Provenance Specification & Checksum Validation Requirements

> [!IMPORTANT]
> **Strict Illustrative Status of Schema Examples:**
> 1. **Illustrative Only:** All JSON instances presented in §6.1 through §6.5 and §8 are **mock structural specifications**. The timestamps (e.g., 4.10s, 10.55s), frame indices, filenames, site identifiers, and checksum strings are purely illustrative examples. They do NOT represent measured ground truth for `event_001` or any actual recording in `data/raw/layer_b/v2/`.
> 2. **Prompt-Template Checksum Computation:** The value `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` is the SHA-256 hash of the empty string `""`. In actual annotation tooling, `prompt_template_sha256` **must be dynamically computed from the exact UTF-8 bytes of the versioned prompt template file on disk**. Reusing the empty-string hash or any placeholder string is strictly invalid and will be rejected.
> 3. **Cryptographic Format Validation:** Every checksum field (`sha256`, `prompt_template_sha256`, `proposal_sha256`, `review_sha256`, and manifest entries) MUST be a full-length, 64-character lowercase hexadecimal string matching regex `^[0-9a-f]{64}$`.
> 4. **Prohibition on Truncation & Placeholders:** Ellipses (e.g. `"a1b2c3..."`), shortened hashes, generic placeholders (e.g. `"<sha256>"`), or empty strings will fail validation in `GroundTruthLoader` and halt execution immediately with a fatal error.

### 6.1 Raw AI Proposal Schema (`data/ground_truth/proposals/{type}/event_XXX_proposal.json`)

> [!NOTE]
> **Illustrative Template:** The following schema instance uses mock timestamps and mock 64-character SHA-256 strings for structural demonstration only. Real values must be populated by the AI proposal tool from actual media bytes.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "proposal_id": "proposal_event_001_v1",
  "event_id": "event_001",
  "event_type": "REAL_WORLD_TRAIN_EVENT",
  "proposal_timestamp_utc": "2026-10-09T08:00:00Z",
  "schema_version": "5.0.0",
  "ai_assistant_metadata": {
    "model_name": "gemini-3.8-flash",
    "prompt_template_version": "v1.0.0",
    "prompt_template_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "input_media_files": [
      {
        "file_name": "camera_front.mov",
        "duration_s": 45.200,
        "sha256": "1111111111111111111111111111111111111111111111111111111111111111"
      },
      {
        "file_name": "camera_back.mov",
        "duration_s": 44.800,
        "sha256": "2222222222222222222222222222222222222222222222222222222222222222"
      }
    ]
  },
  "proposed_site_metadata": {
    "crossing_id": "crossing_A",
    "recording_session_id": "session_20260914_morning"
  },
  "proposed_environmental_conditions": {
    "lighting": "day",
    "weather": "clear"
  },
  "proposed_train_metadata": {
    "train_present": true,
    "train_direction": "left_to_right",
    "train_type": "passenger",
    "trailing_cars_count": 6,
    "horn_status": "present",
    "horn_onset_s": 3.42,
    "horn_uncertainty_s": 0.15,
    "horn_reason": null,
    "confidence_note": "Distinct dual-tone pneumatic horn blast observable in embedded audio."
  },
  "proposed_timestamps": {
    "T0_first_visible": {
      "applicable": true, "candidate_observable": true,
      "value_s": 4.10, "frame_index": 123, "reference_camera": "front", "native_fps": 29.97,
      "rationale": "Locomotive nose emerges from tree line at far right of frame.",
      "ambiguity_flag": false
    },
    "T1_danger_zone_entry": {
      "applicable": true, "candidate_observable": true,
      "value_s": 10.55, "frame_index": 316, "reference_camera": "front", "native_fps": 29.97,
      "rationale": "Front bumper crosses white pavement stop line.",
      "ambiguity_flag": false
    },
    "T2_crossing_occupancy_start": {
      "applicable": true, "candidate_observable": true,
      "value_s": 10.55, "frame_index": 316, "reference_camera": "front", "native_fps": 29.97,
      "rationale": "Coincident with T1 at this physical roadway angle.",
      "ambiguity_flag": false
    },
    "T3_locomotive_unit_clearance": {
      "applicable": true, "candidate_observable": true,
      "value_s": 16.20, "frame_index": 486, "reference_camera": "back", "native_fps": 30.00,
      "rationale": "Trailing end of lead locomotive clears departure gate line.",
      "ambiguity_flag": false
    },
    "T4_tail_clearance": {
      "applicable": true, "candidate_observable": true,
      "value_s": 38.80, "frame_index": 1164, "reference_camera": "back", "native_fps": 30.00,
      "rationale": "Coupler and marker light of final passenger coach clear roadway border.",
      "ambiguity_flag": false
    },
    "T_scene_clear": {
      "applicable": true, "candidate_observable": true,
      "value_s": 41.20, "frame_index": 1236, "reference_camera": "back", "native_fps": 30.00,
      "rationale": "Entire train disappears past road curve.",
      "ambiguity_flag": false
    }
  },
  "proposed_camera_alignment_markers": {
    "candidate_front_marker": "Front bumper crosses mast pole at t=10.55s",
    "candidate_back_marker": "Front bumper enters back view at t=12.00s",
    "candidate_offset_s": 1.45,
    "requires_human_empirical_verification": true
  },
  "raw_proposal_immutable": true
}
```

### 6.2 Human Review History & Adjudication Schema (`data/ground_truth/reviews/{type}/event_XXX_review.json`)

> [!NOTE]
> **Illustrative Template:** The following review record is a mock example demonstrating the per-field adjudication format.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "review_id": "review_event_001_20261009",
  "event_id": "event_001",
  "schema_version": "5.0.0",
  "proposal_reference": {
    "proposal_file": "data/ground_truth/proposals/train_events/event_001_proposal.json",
    "proposal_sha256": "3333333333333333333333333333333333333333333333333333333333333333"
  },
  "reviewer_metadata": {
    "reviewer_id": "human_researcher_lead",
    "review_date_utc": "2026-10-09T08:30:00Z",
    "inspection_tool": "ffmpeg-frame-viewer v1.2 / audacity v3.4"
  },
  "adjudication_status": "APPROVED",
  "field_adjudications": {
    "train_metadata.horn_status": {
      "proposed": "present",
      "approved": "present",
      "decision": "accepted",
      "verified_horn_onset_s": 3.42,
      "notes": "Audible horn onset confirmed on track at 3.42s; clean acoustic transient."
    },
    "timestamps.T0_first_visible": {
      "proposed": 4.10,
      "approved": 4.10,
      "decision": "accepted",
      "verified_frame": 123,
      "notes": "Verified frame 123 in camera_front.mov; earliest appearance."
    },
    "timestamps.T1_danger_zone_entry": {
      "proposed": 10.55,
      "approved": 10.55,
      "decision": "accepted",
      "verified_frame": 316,
      "notes": "Front bumper touches crossing boundary exactly at frame 316."
    },
    "timestamps.T2_crossing_occupancy_start": {
      "proposed": 10.55,
      "approved": 10.55,
      "decision": "accepted",
      "verified_frame": 316,
      "notes": "Coincident with T1."
    },
    "timestamps.T3_locomotive_unit_clearance": {
      "proposed": 16.20,
      "approved": 16.30,
      "decision": "corrected",
      "verified_frame": 489,
      "notes": "Corrected +0.10s (3 frames); locomotive rear coupler actually clears crossing boundary at frame 489."
    },
    "timestamps.T4_tail_clearance": {
      "proposed": 38.80,
      "approved": 38.80,
      "decision": "accepted",
      "verified_frame": 1164,
      "notes": "Tail clearance confirmed frame 1164."
    },
    "timestamps.T_scene_clear": {
      "proposed": 41.20,
      "approved": 41.20,
      "decision": "accepted",
      "verified_frame": 1236,
      "notes": "Scene clear confirmed."
    },
    "camera_alignment.offset_s": {
      "proposed": 1.45,
      "approved": 1.45,
      "decision": "accepted",
      "notes": "Cross-correlation peak on horn onset confirms 1.45s lag; justified uncertainty 0.10s."
    }
  },
  "summary_counts": {
    "total_fields": 8,
    "accepted_count": 7,
    "corrected_count": 1,
    "marked_unobservable_count": 0,
    "rejected_count": 0
  },
  "general_review_notes": "All boundaries verified against physical video frames. Proposal was highly accurate; minor 3-frame correction applied to T3."
}
```

### 6.3 Approved Full-Train Event Schema (`data/ground_truth/train_events/event_XXX.json`)

> [!NOTE]
> **Illustrative Template:** The following approved record is a mock example. Only files that carry `"approval_status": "APPROVED"` and match the manifest are ingested.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "event_id": "event_001",
  "event_type": "REAL_WORLD_TRAIN_EVENT",
  "schema_version": "5.0.0",
  "verification_metadata": {
    "annotation_methodology": "AI-assisted, human-verified",
    "approval_status": "APPROVED",
    "ai_assistant": {
      "model_name": "gemini-3.8-flash",
      "proposal_ref": "data/ground_truth/proposals/train_events/event_001_proposal.json",
      "proposal_sha256": "3333333333333333333333333333333333333333333333333333333333333333"
    },
    "human_verifier": {
      "verifier_id": "human_researcher_lead",
      "review_ref": "data/ground_truth/reviews/train_events/event_001_review.json",
      "review_sha256": "4444444444444444444444444444444444444444444444444444444444444444",
      "approval_timestamp_utc": "2026-10-09T08:30:00Z"
    },
    "audit_summary": {
      "fields_accepted": 7,
      "fields_corrected": 1,
      "fields_marked_unobservable": 0
    }
  },
  "site_metadata": {
    "crossing_id": "crossing_A",
    "recording_session_id": "session_20260914_morning"
  },
  "environmental_conditions": {
    "lighting": "day",
    "weather": "clear"
  },
  "train_metadata": {
    "train_present": true,
    "train_direction": "left_to_right",
    "train_type": "passenger",
    "trailing_cars_count": 6,
    "horn_status": "present",
    "horn_onset_s": 3.42,
    "horn_uncertainty_s": 0.15,
    "horn_reason": null
  },
  "timestamps": {
    "T0_first_visible": {
      "applicable": true,
      "observable": true,
      "not_evaluable": false,
      "value_s": 4.10,
      "uncertainty_s": 0.20,
      "reference_camera": "front",
      "frame_index": 123,
      "native_fps": 29.97,
      "reason": null
    },
    "T1_danger_zone_entry": {
      "applicable": true,
      "observable": true,
      "not_evaluable": false,
      "value_s": 10.55,
      "uncertainty_s": 0.30,
      "reference_camera": "front",
      "frame_index": 316,
      "native_fps": 29.97,
      "reason": null
    },
    "T2_crossing_occupancy_start": {
      "applicable": true,
      "observable": true,
      "not_evaluable": false,
      "value_s": 10.55,
      "uncertainty_s": 0.30,
      "reference_camera": "front",
      "frame_index": 316,
      "native_fps": 29.97,
      "reason": null
    },
    "T3_locomotive_unit_clearance": {
      "applicable": true,
      "observable": true,
      "not_evaluable": false,
      "value_s": 16.30,
      "uncertainty_s": 0.35,
      "reference_camera": "back",
      "frame_index": 489,
      "native_fps": 30.00,
      "reason": null
    },
    "T4_tail_clearance": {
      "applicable": true,
      "observable": true,
      "not_evaluable": false,
      "value_s": 38.80,
      "uncertainty_s": 0.40,
      "reference_camera": "back",
      "frame_index": 1164,
      "native_fps": 30.00,
      "reason": null
    },
    "T_scene_clear": {
      "applicable": true,
      "observable": true,
      "not_evaluable": false,
      "value_s": 41.20,
      "uncertainty_s": 0.50,
      "reference_camera": "back",
      "frame_index": 1236,
      "native_fps": 30.00,
      "reason": null
    }
  },
  "camera_alignment": {
    "measured_offset_s": 1.45,
    "offset_formula": "t_back - t_front",
    "alignment_method": "audio_xcorr",
    "justified_uncertainty_s": 0.10,
    "alignment_status": "aligned",
    "method_notes": "Cross-correlation of initial locomotive horn peak yielded sharp peak at lag 1.45s."
  },
  "evaluation_window": {
    "evaluation_start_s": 0.0,
    "evaluation_end_s": 45.0,
    "total_evaluable_duration_s": 45.0
  },
  "activity_notes": "Moderate ambient wind. One bicycle stopped at gate."
}
```

### 6.4 Approved No-Train Event Schema (`data/ground_truth/no_train_events/event_XXX.json`)

> [!NOTE]
> **Illustrative Template:** Mock example for negative control events. Train timestamps are strictly `applicable: false`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "event_id": "no_train_event_001",
  "event_type": "REAL_WORLD_NO_TRAIN",
  "schema_version": "5.0.0",
  "verification_metadata": {
    "annotation_methodology": "AI-assisted, human-verified",
    "approval_status": "APPROVED",
    "ai_assistant": {
      "model_name": "gemini-3.8-flash",
      "proposal_ref": "data/ground_truth/proposals/no_train_events/event_001_proposal.json",
      "proposal_sha256": "5555555555555555555555555555555555555555555555555555555555555555"
    },
    "human_verifier": {
      "verifier_id": "human_researcher_lead",
      "review_ref": "data/ground_truth/reviews/no_train_events/event_001_review.json",
      "review_sha256": "6666666666666666666666666666666666666666666666666666666666666666",
      "approval_timestamp_utc": "2026-10-09T08:45:00Z"
    },
    "audit_summary": {
      "fields_accepted": 6,
      "fields_corrected": 0,
      "fields_marked_unobservable": 0
    }
  },
  "site_metadata": {
    "crossing_id": "crossing_A",
    "recording_session_id": "session_20260914_morning"
  },
  "environmental_conditions": {
    "lighting": "day",
    "weather": "clear"
  },
  "train_metadata": {
    "train_present": false,
    "train_direction": null,
    "train_type": null,
    "trailing_cars_count": null,
    "horn_not_applicable": true,
    "horn_status": null,
    "horn_onset_s": null,
    "horn_uncertainty_s": null,
    "horn_reason": "No train present"
  },
  "timestamps": {
    "T0_first_visible": {"applicable": false, "observable": false, "not_evaluable": false, "value_s": null, "uncertainty_s": null, "reason": "No train present"},
    "T1_danger_zone_entry": {"applicable": false, "observable": false, "not_evaluable": false, "value_s": null, "uncertainty_s": null, "reason": "No train present"},
    "T2_crossing_occupancy_start": {"applicable": false, "observable": false, "not_evaluable": false, "value_s": null, "uncertainty_s": null, "reason": "No train present"},
    "T3_locomotive_unit_clearance": {"applicable": false, "observable": false, "not_evaluable": false, "value_s": null, "uncertainty_s": null, "reason": "No train present"},
    "T4_tail_clearance": {"applicable": false, "observable": false, "not_evaluable": false, "value_s": null, "uncertainty_s": null, "reason": "No train present"},
    "T_scene_clear": {"applicable": false, "observable": false, "not_evaluable": false, "value_s": null, "uncertainty_s": null, "reason": "No train present"}
  },
  "camera_alignment": {
    "measured_offset_s": null,
    "offset_formula": "t_back - t_front",
    "alignment_method": "unmeasured",
    "justified_uncertainty_s": null,
    "alignment_status": "unresolved",
    "method_notes": "Pending Prerequisite R04 inter-camera offset measurement."
  },
  "evaluation_window": {
    "front_duration_s": 24.635,
    "back_duration_s": 24.422,
    "combined_stream_seconds": 49.057,
    "concurrent_overlap_status": "unresolved",
    "concurrent_overlap_duration_s": null,
    "concurrent_overlap_notes": "Inter-camera offset not measured. Cannot compute concurrent overlap without R04.",
    "evaluation_start_s": 0.0,
    "evaluation_end_s": null
  },
  "activity_log": [
    {"start_s": 0.0, "end_s": 5.2, "activity_type": "quiet_scene", "notes": "No road vehicles"},
    {"start_s": 5.2, "end_s": 8.0, "activity_type": "motorcycle_passage", "notes": "Motorcycle traverses tracks"},
    {"start_s": 12.0, "end_s": 13.5, "activity_type": "road_vehicle_horn", "notes": "Automotive horn in background"}
  ],
  "activity_notes": "Valid negative control: zero railway vehicles."
}
```

### 6.5 Approved Engine-Only Event Schema (`data/ground_truth/engine_events/event_001.json`)

> [!NOTE]
> **Illustrative Template:** Mock example for single-engine passage where $T_3 \equiv T_4$.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "event_id": "event_engine_001",
  "event_type": "REAL_WORLD_ENGINE_ONLY",
  "schema_version": "5.0.0",
  "verification_metadata": {
    "annotation_methodology": "AI-assisted, human-verified",
    "approval_status": "APPROVED",
    "ai_assistant": {
      "model_name": "gemini-3.8-flash",
      "proposal_ref": "data/ground_truth/proposals/engine_events/event_001_proposal.json",
      "proposal_sha256": "7777777777777777777777777777777777777777777777777777777777777777"
    },
    "human_verifier": {
      "verifier_id": "human_researcher_lead",
      "review_ref": "data/ground_truth/reviews/engine_events/event_001_review.json",
      "review_sha256": "8888888888888888888888888888888888888888888888888888888888888888",
      "approval_timestamp_utc": "2026-10-09T08:55:00Z"
    },
    "audit_summary": {
      "fields_accepted": 6,
      "fields_corrected": 0,
      "fields_marked_unobservable": 1
    }
  },
  "site_metadata": {
    "crossing_id": "crossing_B",
    "recording_session_id": "session_20260915_dusk"
  },
  "environmental_conditions": {
    "lighting": "dusk",
    "weather": "clear"
  },
  "train_metadata": {
    "train_present": true,
    "train_direction": "right_to_left",
    "train_type": "engine_only",
    "trailing_cars_count": 0,
    "horn_status": "unobservable",
    "horn_onset_s": null,
    "horn_uncertainty_s": null,
    "horn_reason": "Engine-only event; horn presence could not be determined from audio track."
  },
  "timestamps": {
    "T0_first_visible": {
      "applicable": true, "observable": true, "not_evaluable": false,
      "value_s": 1.20, "uncertainty_s": 0.25, "reference_camera": "front", "frame_index": 36, "native_fps": 29.97, "reason": null
    },
    "T1_danger_zone_entry": {
      "applicable": true, "observable": true, "not_evaluable": false,
      "value_s": 3.40, "uncertainty_s": 0.30, "reference_camera": "front", "frame_index": 102, "native_fps": 29.97, "reason": null
    },
    "T2_crossing_occupancy_start": {
      "applicable": true, "observable": true, "not_evaluable": false,
      "value_s": 3.40, "uncertainty_s": 0.30, "reference_camera": "front", "frame_index": 102, "native_fps": 29.97, "reason": null
    },
    "T3_locomotive_unit_clearance": {
      "applicable": true, "observable": true, "not_evaluable": false,
      "value_s": 6.80, "uncertainty_s": 0.40, "reference_camera": "back", "frame_index": 204, "native_fps": 30.00,
      "reason": "Coincident with T4 because locomotive has no trailing railcars."
    },
    "T4_tail_clearance": {
      "applicable": true, "observable": true, "not_evaluable": false,
      "value_s": 6.80, "uncertainty_s": 0.40, "reference_camera": "back", "frame_index": 204, "native_fps": 30.00,
      "reason": "Coincident with T3 because locomotive has no trailing railcars."
    },
    "T_scene_clear": {
      "applicable": true, "observable": true, "not_evaluable": false,
      "value_s": 8.50, "uncertainty_s": 0.50, "reference_camera": "back", "frame_index": 255, "native_fps": 30.00, "reason": null
    }
  },
  "camera_alignment": {
    "measured_offset_s": 0.80,
    "offset_formula": "t_back - t_front",
    "alignment_method": "visual_landmark",
    "justified_uncertainty_s": 0.30,
    "alignment_status": "aligned",
    "method_notes": "Locomotive bumper crossing track landmark."
  },
  "evaluation_window": {
    "evaluation_start_s": 0.0,
    "evaluation_end_s": 15.0,
    "total_evaluable_duration_s": 15.0
  },
  "activity_notes": "Single locomotive pass; T3 == T4."
}
```

---

## 7. Researcher Prerequisite Verification (R01 through R04) — All Currently INCOMPLETE (NO-GO)

Every evaluation run requires formal verification that all real-world research prerequisites have been met. Based on repository inspection, all four prerequisites are currently unmet:

1. **Prerequisite R01 (AI-Assisted Annotation & Human Approval) — INCOMPLETE:**
   - Candidate proposals must be generated by Gemini into `data/ground_truth/proposals/`.
   - The human researcher must perform manual frame-by-frame and audio inspection of all 27 events, log decisions in `data/ground_truth/reviews/`, correct errors, and write approved files (`approval_status: "APPROVED"`) into `data/ground_truth/`.
   - *Current Repository Status:* **INCOMPLETE.** Directory `data/ground_truth/` does not exist; no ground-truth files exist.
2. **Prerequisite R02 (Cryptographic Ground Truth Manifest Freeze) — INCOMPLETE:**
   - The researcher must generate `data/ground_truth/ground_truth_manifest.json` locking the 64-character SHA-256 hashes of all 27 approved ground-truth JSON files, 27 review logs, and 27 raw proposals.
   - *Current Repository Status:* **INCOMPLETE.** No manifest file exists.
3. **Prerequisite R03 (Crossing Geographic & Landmark Documentation) — INCOMPLETE:**
   - Researcher must document physical crossing boundaries, road width, visual approach/departure landmarks, and camera mounting geometry for each crossing site (Crossing A and Crossing B).
   - *Current Repository Status:* **INCOMPLETE.** No geometry sheets, landmark annotations, or surveyed boundary documents exist in the repository.
4. **Prerequisite R04 (Inter-Camera Offset for No-Train Events) — INCOMPLETE:**
   - Researcher must measure inter-camera temporal offset ($\Delta t$) for each no-train event using audio cross-correlation, visual landmark, or other justified method. Until R04 is completed, concurrent overlap denominators remain unresolved and must not be used.
   - *Current Repository Status:* **INCOMPLETE.** Container creation timestamps show different dates across cameras (unusable for synchronization); no empirical offset measurements exist.
5. **Automated Enforcement:**
   - The evaluation runner will call `GroundTruthLoader.validate_all()`.
   - If any required file is missing, unapproved, fails SHA-256 validation against `ground_truth_manifest.json`, contains ellipses, placeholders, or unauthorized `null`s, evaluation halts immediately with exit code 1.

---

## 8. Cryptographic Ground Truth Manifest Specification (`ground_truth_manifest.json`)

> [!NOTE]
> **Illustrative Manifest Example:** In production, every hash string in `data/ground_truth/ground_truth_manifest.json` MUST be a full 64-character lowercase hexadecimal hash.

```json
{
  "manifest_version": "1.0.0",
  "generated_utc": "2026-10-09T09:00:00Z",
  "methodology": "AI-assisted, human-verified",
  "verifier_id": "human_researcher_lead",
  "total_approved_events": 27,
  "approved_artifacts": {
    "train_events/event_001.json": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "no_train_events/event_001.json": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "engine_events/event_001.json": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
  },
  "review_audit_artifacts": {
    "reviews/train_events/event_001_review.json": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
  },
  "proposal_artifacts": {
    "proposals/train_events/event_001_proposal.json": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
  }
}
```

---

## 9. Document Change Log

| Version | Date | Changes Made |
|---|---|---|
| 4.0.0 | 2026-10-09 | AI-Assisted Annotation Amendment: Formally replaced human-only annotation policy with 3-stage lifecycle (AI proposal → human review → approved ground truth); established immutable proposal repository and audit log schemas; enforced anti-leakage firewall separating annotator from runtime models; created prerequisites R01 and R02. |
| 5.0.0 | 2026-10-09 | Methodology Implementation Pass: Defined canonical boundary taxonomy with T3 as Locomotive Head Exit and T4 as Tail Clearance; integrated full 64-character SHA-256 validation; added full JSON schema templates for proposals, reviews, and ground truth; reinforced R01–R04 prerequisite enforcement. |
| 6.0.0 | 2026-10-09 | Canonical Terminology & Left-Censoring Harmonization Pass: (1) Resolved T3 canonical name as **Locomotive Unit Clearance (rear end exits danger zone)** with explicit physical definition (trailing edge of lead motive power unit clears danger zone while trailing cars continue); distinguished front exit during traversal from complete unit clearance. (2) Preserved T4 strictly as Tail Clearance (final vehicle clears danger zone). (3) Harmonized schema key to `T3_locomotive_unit_clearance` with backward-compatibility alias mapping for legacy `T3_locomotive_exit` (preserving draft proposals v1–v4). (4) Defined left-censored $T_0$ representation (recording-relative 0.00s candidate; mandatory exclusion from physical detection-latency denominator). (5) Explicitly distinguished provisional visual landmarks from certified danger-zone boundaries pending Prerequisite R03 crossing geometry survey. |
