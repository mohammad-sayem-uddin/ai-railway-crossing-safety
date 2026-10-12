# Synchronized Data Collection Protocol

## Layer B: Train-Passage Event Dataset

**Status:** Proposed collection protocol.  
**Purpose:** Create synchronized, event-labeled recordings for multimodal temporal/system evaluation. It is separate from the Layer A still-image dataset.

## 1. Event bundle

Preferred layout:

```text
data/raw/events/event_001/
├── camera_1.mp4
├── camera_2.mp4
├── audio.wav
├── metadata.json
├── geometry.json
└── labels/                         # created after collection
```

One bundle contains one train passage plus sufficient before/after context to assess approach, occupancy, departure, and false alarms. Retain empty/no-train recording intervals separately or as explicit event-context segments.

## 2. Required metadata

| Field | Requirement |
|---|---|
| `event_id`, `crossing_id`, `session_id`, `recording_id` | Stable identifiers with no reuse. |
| `start_time`, `end_time`, `time_zone` when available | Preserve source timing and note uncertainty. |
| `train_direction`, `event_order_in_session` | Known, observed, or `unknown`. |
| `camera_1` / `camera_2` roles and placement | Role, orientation, approximate position, visible zones, blind spots. |
| `geometry_version` | Link to fixed crossing-zone definition. |
| `recording_device` and settings | Device/model if known, frame rate/sample rate, codec, clock behavior. |
| `synchronization_method`, offsets, uncertainty | Required; never assume zero offset. |
| weather, lighting, traffic context, train type | Controlled label or `unknown`; record source. |
| data-quality flags | Occlusion, dropped frames, clipping, missing source, bad clock, abnormal operation. |
| consent/permission/provenance | Collection authority and use restrictions. |

## 3. Geometry record

For each crossing-camera arrangement, create a non-calibrated but explicit geometry sheet: annotated image landmarks for approach zone, crossing reference zone, downstream/tail-clearance boundary, direction of travel, camera orientation, and areas not observable. Approximate physical distances may be recorded only when measured or reliably supplied; otherwise use `unknown`.

The geometry sheet must state whether tail clearance is independently observable. If not, collection remains valid for approach/occupancy studies but cannot support the premature-opening primary endpoint.

## 4. Synchronization hierarchy

Use the strongest feasible method and record it.

1. **Preferred:** common synchronized clock/timestamp across both cameras and audio recorder.
2. **Acceptable:** visible/audible synchronization marker captured by all sources at session start and end; estimate offset/drift.
3. **Limited:** post-hoc alignment using identifiable shared audiovisual event(s), with documented method and uncertainty.
4. **Insufficient for timing/fusion:** no defensible common cue or unknown drift. Retain only for unimodal development unless a later alignment method is validated.

For every event, preserve raw timestamps, estimated offset(s), estimated drift where applicable, and alignment uncertainty. Never resave media in a way that destroys original timestamp/provenance.

## 5. Collection procedure

1. Record site/camera geometry and ODD suitability before a session.
2. Start all sources using the selected synchronization procedure; capture the synchronization cue when used.
3. Record continuous context around train passages and empty periods.
4. Assign event boundaries after collection; do not trim away evidence needed to establish false alarms or delayed detection.
5. Verify file integrity, duration, frame/sample rates, audio clipping, dropped frames, source availability, and synchronization quality.
6. Mark every anomaly rather than deleting it without provenance.
7. Split by crossing/session/event hierarchy only after event curation.

## 6. If exact synchronization is impossible

Estimate the offset from predeclared common cues, save the method and uncertainty, and use only events within an agreed uncertainty tolerance for temporal fusion/timing endpoints. Do not claim sample-level or frame-perfect multimodal alignment. Events with excessive uncertainty may still contribute to Layer A or unimodal analyses, with their limitation recorded.

## 7. Collection exclusions and ethics

Do not collect or label an event as in-domain if its direction, crossing zone, or train identity cannot be resolved. Flag abnormal operations separately. Follow all site-permission, privacy, and local legal requirements; protect faces, vehicle plates, location-sensitive material, and original-media access according to the approved data-governance plan.
