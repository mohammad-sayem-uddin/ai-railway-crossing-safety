# Event Label Protocol

## Ground Truth for a Single Train-Passage Event

**Status:** Proposed; must be piloted before full annotation.  
**Rule:** Model outputs, including `rear` detection, are never ground truth.

## 1. Unit and annotation roles

One event is one identifiable train moving in one direction through the defined crossing reference zone. Two trained human annotators label a representative pilot independently; production labels use the agreed protocol and adjudication process in `ANNOTATION_GUIDELINE_V2.md`.

Annotators use original synchronized media plus the geometry sheet. They must not inspect model predictions while creating ground truth. Each label stores annotator ID, media timestamp, method, confidence/uncertainty, and notes.

## 2. Time reference and uncertainty

- Use each source’s original timestamp mapped to the event master clock using the recorded synchronization method.
- Record timestamps to the nearest source frame/sample precision; do not imply finer precision.
- Store `uncertainty_s` and `label_status`: `observed`, `estimated`, `unobservable`, `missing`, or `not_applicable`.
- A label is `estimated` only with a documented interpolation rule between observable frames.
- If synchronization uncertainty exceeds the protocol threshold, timing labels may remain descriptive but must not enter timing/fusion primary analyses.

## 3. Required event labels

| Event | Exact meaning and timestamp | Annotator/source | Ground truth? | Uncertainty and missing rule |
|---|---|---|---|---|
| `first_train_visual_appearance` | First frame in either defined camera zone where a train is visibly distinguishable by a human. Timestamp is frame start/onset. | Human annotator; named camera(s). | Yes, contextual. | `unobservable` if scene is occluded/outside recording; do not infer from detector. |
| `first_train_audible_evidence` | First audio time at which an annotator identifies a train-associated acoustic signal under the defined audio protocol; horn identity is separately tagged. | Human annotator using audio. | Yes, contextual. | `unobservable` with unusable/no audio; ambiguous sounds are tagged, not forced to horn. |
| `approach_confirmation` | First time the train is visibly/operationally confirmed approaching the crossing in the designated approach zone; must meet predeclared geometry cue. | Human annotator using geometry sheet. | Yes. | `estimated` only when movement between frames establishes crossing direction; otherwise `unobservable`. |
| `crossing_entry` | First time any part of the train intersects the predeclared crossing reference zone. | Human annotator using fixed visual zone/landmarks. | Yes. | If zone boundary is not visible, label `unobservable`; never substitute a bounding box or front class alone. |
| `crossing_occupied_start` | Same as crossing entry unless a distinct occupancy zone is defined; then first intersection with occupancy zone. | Human annotator. | Yes. | Must reference the saved geometry definition. |
| `crossing_occupied_end` / `crossing_exit` | First time no portion of the train remains in the crossing reference zone. | Human annotator using suitable view/zone. | Yes, if observable. | If tail or zone is hidden, mark `clearance_unobservable`; no model inference allowed. |
| `tail_clearance` | Time at which the final physical portion of the identified train has passed beyond the defined downstream boundary of the crossing zone. | Human annotator using independent visible zone/landmark or designated reference camera. | Yes, primary endpoint reference. | Requires observable tail and boundary. If unavailable, mark `unobservable`; exclude from premature-opening denominator. |
| `next_train_begins` | First reference event of a distinct subsequent train passage after the current event, with a new event ID. | Human annotator/event curator. | Yes. | If identity/order is ambiguous, flag `event_boundary_ambiguous`; do not merge silently. |
| `manual_gate_safe_interval` | Optional observational label: interval judged safe for a hypothetical gate to remain/open only under an explicitly defined study rule, normally beginning no earlier than tail clearance plus margin. | Human annotator with protocol; not an actual safety decision. | Optional reference label. | Not collected where clearance is unobservable; must state margin and uncertainty. |

## 4. Crossing clearance determination

Tail clearance must be independently determined from a fixed, pre-annotated crossing-zone boundary visible in at least one suitable reference view. Acceptable evidence is a visible tail crossing a known downstream landmark/zone boundary, with recorded frame time.

If existing geometry cannot show the downstream boundary, use the conservative study definition: **clearance is unobservable**, not “rear detected.” The event is usable for approach/occupancy analyses but excluded from the premature-opening primary endpoint. A future collection may add a dedicated reference view or physical non-actuating marker solely to establish the zone boundary.

## 5. Auxiliary labels

Record when observable: direction, train identity within session, train type, camera availability, audio quality, weather, lighting, occlusion, whether horn occurs, vehicle-horn occurrence, abnormal operation, and out-of-domain status. These are metadata; absence must be explicit.

## 6. Quality control

- Blind double-label a representative pilot and an ongoing random audit subset.
- Resolve timestamp disagreements using predefined tolerances; retain both raw labels and adjudicated label.
- Categorize disagreements: geometry unclear, source synchronization, train/vehicle confusion, occlusion, tail not visible, direction unclear, annotator error, or protocol ambiguity.
- Amend this protocol only through the decision log; do not relabel silently without versioning.
