# Three-Event Stage-2.1 Pilot Protocol

**Date:** 2026-11-01  
**Status:** Non-executing design. Explicit researcher authorization and real human participation are required before use.  
**Events:** `train_events/event_001`, `no_train_events/event_001`, `engine_events/event_001`

> This plan does not open media, select labels, invent timestamps, create review records, or promote ground truth. It tests whether the workflow is understandable and operational—not whether any event has a particular truth value.

## 1. Pilot objectives

The pilot should test event identification, cohort-qualified source selection, reviewer independence, front/back camera handling, camera-local clocks, full-file hash observation, duration capture, completion of all six boundaries, rationale quality, uncertainty/censoring handling, disagreement escalation, and append-only history. Pilot timing observations may inform D1 only after researcher review; they do not select a threshold.

## 2. Prerequisites (not satisfied by this document)

- Researcher authorizes the pilot (`AUTH-PILOT-EXEC`) and exact event scope.
- Real reviewers are selected and separately authorized; Mission 4B does not alter the allowlist.
- Media access, review environment, model firewall, and hash-observation procedure are approved.
- Researcher supplies the authoritative protocol/version and avoids mixing v8/v9/v7 semantics.
- D1/D3(a)/D3(c) are resolved or explicitly governed for the pilot.
- A separate record-writing authorization exists if any record is to be written.

## 3. Common future-execution procedure

1. Confirm cohort-qualified key against queue and inventory.
2. Confirm front/back sources and active proposal reference.
3. Establish a model-firewalled environment.
4. Observe both hashes using the approved procedure.
5. Record UTC start and session ID.
6. Inspect source evidence independently of model predictions.
7. Record all six boundary states and rationales.
8. Record missing evidence, interruptions, or stop conditions.
9. Record the honest UTC end and derived duration.
10. Validate a temporary draft; do not write authoritative ground truth without separate authorization.
11. Separate completion from `APPROVED` status.
12. Route second review/disputes under the researcher-approved rule.

## 4. `train_events/event_001`

**Purpose:** Full train-passage case for dual-camera source identity, six-boundary workflow, and the distinction between T3 locomotive-unit clearance and T4 final-tail clearance.

**Required steps/evidence:** Confirm the train cohort key; confirm both sources and hashes; inspect approach and departure evidence under the signed protocol; complete T0, T1, T2, T3, T4, and scene-clear states; preserve camera-local times; do not apply candidate R04 offsets or copy proposal values.

**Possible non-observable states:** Left/right censoring, uncertainty from occlusion/landmark ambiguity, or unobservable evidence. No expected state or timestamp is supplied.

**Duration:** At least the current schema floor of 30.0 seconds. D1's final floor and any fast-session routing remain pending.

**Independence/second review:** First reviewer must be authorized and independent. Apply D3(a) when selected, and always escalate explicit `NEEDS_SECOND_REVIEW`, `DISPUTED`, hash/source incidents, or model-firewall incidents. A second reviewer must be distinct.

**Completion checks:** Correct key/cohort; both sources and hashes; duration; six states/rationales; independence attestation; chronological history; no unsupported numeric values; completion kept separate from approval.

## 5. `no_train_events/event_001`

**Purpose:** Negative-control workflow case that tests explicit non-applicability without invented train-boundary timestamps and preserves the no-train denominator.

**Required steps/evidence:** Confirm the no-train cohort key; check both sources and any authorized audio evidence; review the required observation window without model outputs; address all six fields explicitly. If the approved protocol confirms train boundaries do not apply, use `UNOBSERVABLE_NOT_APPLICABLE` with a rationale.

**Possible non-observable states:** Not applicable is a possible outcome; uncertainty remains possible if evidence is incomplete. Censoring is not a synonym for no train.

**Duration:** At least 30.0 seconds under the current schema floor; do not infer a shorter requirement from clip length while D1 is unresolved.

**Independence/second review:** Same authorization and independence rules. Apply the researcher-approved trigger; software does not auto-approve a negative control.

**Completion checks:** Correct cohort; both sources checked; six explicit states/rationales; no invented train timestamp; duration, hashes, attestation, and history valid; no aggregate mixing.

## 6. `engine_events/event_001`

**Purpose:** Separate engine-only case study for special-case semantics and cohort isolation. It must never be counted as a train event or no-train control.

**Required steps/evidence:** Confirm engine key; confirm both sources/hashes; inspect under the signed protocol without full-train assumptions; address all six fields; document the approved treatment of T3/T4 for a single unit; do not copy prior engine proposal/review values.

**Possible non-observable states:** The protocol may make a tail boundary not applicable, or recording limits may censor it, or visual evidence may be uncertain. This plan selects none of these states and supplies no expected timestamp.

**Duration:** At least 30.0 seconds under the current floor.

**Independence/second review:** Same identity and independence controls; apply D3(a); escalate T3/T4 disagreement; retain engine isolation.

**Completion checks:** Engine identity/isolation; six explicit fields; T3/T4 tied to approved protocol, not prior records; hashes/duration; history and attestation; no train/no-train aggregate implication.

## 7. Researcher decision log (intentionally blank)

- Protocol authority/version: ____________________
- Evaluation profile: ____________________
- D1 floor and fast-session threshold: ____________________
- D3(a) second-review trigger: ____________________
- D3(c) clear-boundary audit: ____________________
- R04 scope: ____________________
- Pilot authorization ID/date: ____________________
- Record-writing authorization: ____________________

## 8. Non-execution statement

No pilot event was opened, played, decoded, listened to, timestamped, or recorded during Mission 4B. Synthetic tests use temporary text fixtures only and are not human review evidence.