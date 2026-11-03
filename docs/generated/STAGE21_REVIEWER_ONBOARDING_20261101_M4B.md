# Stage-2.1 Reviewer Onboarding

**Mission:** 4B — Human Review Operational Preparation, Pilot Design & Review Queue Validation  
**Date:** 2026-11-01  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Status:** Preparation only; no real event was reviewed and no real Stage-2.1 record was created.

> **Important:** This is an operating guide, not an authorization. Do not start a real review until the execution checklist, reviewer authorization, protocol authority, and any required researcher approvals have been completed.

## 1. Purpose of Stage-2.1

Stage-2.1 is the human verification stage between candidate proposal material and any future approved ground truth. A reviewer examines the correct event and source streams, determines the state of each canonical boundary, records evidence and rationale, and preserves an auditable session history. A Stage-2.1 review is not model inference, not an acceptance of a proposal, and not ground-truth approval.

The current software schema is `8.1.0-stage2.1` in `src/railway_detection/annotation/stage2_1_schema.py`. It requires six boundary entries:

- `T0_first_visible`
- `T1_danger_zone_entry`
- `T2_crossing_occupancy_start`
- `T3_locomotive_unit_clearance`
- `T4_tail_clearance`
- `T_scene_clear`

Each entry must use exactly one of `OBSERVABLE`, `UNOBSERVABLE_NOT_APPLICABLE`, `CENSORED`, or `UNCERTAIN`.

## 2. Independence from model predictions

The reviewer must make boundary observations from the authorized source evidence, independently of evaluated-model predictions. Do not open, query, or use YOLO, audio-model, decision-engine, cached inference, experiment output, or evaluation-result files to choose a boundary. A candidate proposal may be used as an administrative navigation aid only after the independent review procedure is defined, and every proposed value must be checked against source evidence rather than copied.

At record creation, the reviewer must sign a specific model-independence attestation. The schema requires `attested: true`, a timestamp, and a statement of at least 20 characters. This field is an auditable assertion; it is not a substitute for an independent review environment or human oversight.

## 3. Who may review

### 3.1 Current authorization schema

`data/ground_truth/authorized_reviewers.json` currently has this shape:

```json
{
  "authorized_reviewers": ["<researcher-authorized-identity>"],
  "revoked_reviewers": [],
  "inactive_reviewers": []
}
```

The last two arrays are optional in the current loader. This codebase does **not** currently implement a role-rich reviewer registry, identity-provider verification, signatures, or an independently authenticated active-status service.

`promotion_gate.load_authorized_reviewers()` requires:

1. A readable JSON object.
2. A non-empty `authorized_reviewers` list.
3. Each entry to be a non-blank string.
4. No duplicate entries.
5. No entry to be in the blocklist.
6. If `revoked_reviewers` or `inactive_reviewers` is present, each must be a list of non-blank strings and neither may overlap with the authorized list.

Authorization is an exact identifier lookup. The record carries the same identity at `reviewer_metadata.reviewer_id`; it must be present in the supplied allowlist at record construction and again at promotion validation.

### 3.2 Current repository evidence

The current file contains one researcher-supplied email identity. This onboarding document does not repeat or extend that identity, and Mission 4B did not add anyone to the file. No second reviewer identity has been invented or authorized by this mission.

### 3.3 Blocklisted identities

The schema rejects generic, role-like, placeholder, or automation identities, including `human_researcher_lead`, `human_annotator`, `reviewer`, `unknown`, `system`, `ai`, `assistant`, `human`, `researcher`, `n/a`, `na`, `tbd`, and the empty string. The comparison is case-insensitive for the blocklist. A real reviewer must use an individually attributable identity, not a role label.

### 3.4 Independence and self-review

The allowlist alone does not prove independence. Before assignment, the researcher must confirm that reviewers have no prohibited access to model outputs and no conflict that would make a nominal second review dependent on the first. A reviewer must not review their own first review as the independent second reviewer.

The implementation rejects:

- a self-referential `second_review_of`;
- a history that claims a `second_review` or resolution step while all history actors are the same identity;
- a batch where a second-review record points to a first-review record by the same reviewer.

The implementation does **not** authenticate a person, infer conflicts of interest, or decide which scientific cases need a second review.

## 4. Identify the event before inspecting it

Use the cohort-qualified key, never a bare `event_001`:

`<cohort>/<event_id>`

The authoritative inventory currently contains 23 `train_events`, 3 `no_train_events`, and 1 `engine_events` event. Confirm all of the following before opening any source evidence:

1. The queue key and inventory key are identical.
2. The cohort directory matches the event key.
3. The active proposal path is the current candidate proposal for that same cohort/event.
4. Front and back camera source paths belong to that event.
5. The event is not a synthetic fixture.
6. The engine event remains isolated as `engine_events/event_001`.

Do not use a proposal version discovered by casual directory browsing if it differs from the active proposal reference in the queue.

## 5. Verify source cameras

For each event, verify the front-camera and back-camera source identities using the authorized inventory and the review environment's displayed metadata. The reviewer must record which camera supports each `OBSERVABLE` boundary and must not silently transfer a boundary from one camera clock to the other.

The current R04 state remains unresolved. Unless and until a researcher accepts a synchronization scope, treat front and back times as media-local observations. Do not apply a candidate offset during annotation. If a source is unavailable, mismatched, truncated, or otherwise inconsistent, stop and escalate; do not infer or repair the evidence.

## 6. Review duration

The schema derives duration from `review_end_utc - review_start_utc`; it ignores a caller-supplied duration and rejects a session below the current 30.0-second plausibility floor. The floor is a sanity check, not proof of a genuine review and not the unresolved pilot-derived D1 threshold.

At session start:

- record the UTC start time and session identifier;
- confirm the event and camera sources;
- observe the media hashes using the authorized workflow;
- start the review clock only when the reviewer is ready to inspect.

At session end:

- record the UTC end time;
- verify that the session covered the required review steps;
- record any stop, interruption, source failure, or uncertainty rationale;
- do not inflate timestamps to pass the floor.

No software duration test establishes that a person actually watched or listened to the media.

## 7. Front-camera evidence

Use the front stream for approach-side observations when the applicable protocol semantics call for it, while preserving the camera-local clock. Inspect enough source context to decide whether a boundary is directly observable, outside the recording, not applicable, or ambiguous. Record a frame reference and specific rationale when a boundary is observable.

If the event begins after an approach boundary has already occurred, use the approved boundary-state vocabulary and explain the left-censoring or lack of applicability. Do not insert a guessed time at zero unless the researcher has explicitly approved the semantics for that protocol version; the current protocol authority is unresolved.

## 8. Back-camera evidence

Use the back stream for departure-side observations when the applicable protocol semantics call for it, again retaining its local clock. T3 and T4 have distinct meanings in the currently documented canonical table: locomotive-unit clearance versus final-tail clearance. Do not treat the front of a locomotive leaving view as proof that the locomotive unit or final train tail has cleared the danger zone.

If the recording ends before a boundary can be observed, document right censoring rather than inventing a timestamp. If the landmark or visual evidence is ambiguous, record `UNCERTAIN` with a concrete reason. Do not use another camera's time as a substitute.

## 9. Observe and record media hashes

The active Stage-2.1 workflow records the reviewer's observed full-file SHA-256 values for both front and back sources in `reviewer_observed_media_hashes`. The reviewer should:

1. Use only the authorized hash-observation procedure.
2. Confirm the displayed paths are the intended event's front and back sources.
3. Record the observed hash and UTC observation time.
4. Stop if a hash is missing, inconsistent, or changes during the session.

At later validation, the promotion gate independently compares live file content with both the inventory registry and the reviewer's observed hashes. A matching path string is not evidence of matching content. Mission 4B did not hash or open any real media.

## 10. Boundary observations and rationale

For every canonical boundary, complete all required fields. An observable boundary needs a finite non-negative value, a front/back reference camera, and a rationale. A non-observable state must have `value_s: null` and a non-empty rationale. The rationale must explain what was seen, what was not seen, which camera/recording limit applied, or why the event is not applicable. Do not use a proposal's wording as a substitute for a reviewer observation.

Do not force agreement with the first reviewer, a candidate proposal, or a model. If the evidence does not support a point value, preserve the appropriate non-observable state.

## 11. Corrections preserve history

Corrections are append-only. Do not edit an earlier review in place to erase a disagreement or overwrite its rationale. A correction must identify the prior review, preserve the prior record/hash as required by the workflow, append a history event, identify the actor and UTC time, and state why the correction was made. The schema rejects duplicate history entries, non-chronological history, and a history whose final status does not match the record status.

## 12. Disagreements and escalation

If a reviewer cannot determine a boundary, record `UNCERTAIN` and explain the ambiguity. If evidence is outside the recording, record `CENSORED`; if the concept does not apply, record `UNOBSERVABLE_NOT_APPLICABLE`. Do not average, majority-vote, or silently choose between reviewers.

An event is `DISPUTED` until an authorized human resolves the disagreement under the approved procedure. A second review, when required by the researcher's selected policy, must use a distinct authorized identity. A missing camera, hash mismatch, model-firewall concern, or tooling defect is a stop/escalation condition.

The current code rejects unresolved `DISPUTED` and `NEEDS_SECOND_REVIEW` records at promotion. It does not yet automatically decide that every `CENSORED` or `UNCERTAIN` boundary requires a second reviewer; that trigger is a pending researcher decision (D3(a)).

## 13. Review completion is not approval

Review completion means the session has a valid time window, required evidence/provenance fields, six boundary entries, and a history entry. Completion can end with `NEEDS_SECOND_REVIEW`, `DISPUTED`, or another non-promotable state. `APPROVED` is a later adjudication status and still does not itself create approved ground truth.

Promotion is a separate, fail-closed technical operation requiring current proposal binding, media-hash checks, authorized reviewers, schema validity, resolved status, batch integrity, and any separate researcher authorization. Evaluation readiness is also mechanical only. Ground-truth approval and official evaluation authorization remain human researcher decisions.

## 14. What the reviewer must not do

- Do not review a bare event ID without its cohort.
- Do not consult evaluated-model predictions or experiment outputs.
- Do not copy, interpolate, or normalize candidate timestamps into observations.
- Do not apply an unresolved R04 offset.
- Do not use synthetic IDs, synthetic sessions, or temporary fixtures as real evidence.
- Do not edit legacy review files.
- Do not write an authorization allowlist.
- Do not promote a record or create a promotion receipt.

## Evidence and authorization status

| Item | Status at Mission 4B close |
|---|---|
| Existing schema/gate behavior | Verified by source inspection and synthetic tests |
| Existing queue/inventory metadata | Audited read-only; 27/27 represented |
| Genuine human review | Not performed |
| Real Stage-2.1 records | None created by Mission 4B |
| Ground-truth approval | Not granted by Mission 4B |
| Promotion/evaluation authorization | Not granted by Mission 4B |
| Protocol authority, evaluation profile, split, R04, thresholds, ROI, B7e | Pending; not resolved here |