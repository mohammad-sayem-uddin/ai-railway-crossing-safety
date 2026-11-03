# T0–T4 Human Review Guide

**Date:** 2026-11-01  
**Mission:** 4B preparation only  
**Status:** Guidance for a future authorized review; no boundary was selected for any real event.

## 1. Do not silently combine protocol versions

The repository contains multiple protocol documents and an unresolved protocol-authority decision. `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` (worktree v7.0.0) provides the current canonical physical names and camera conventions; `docs/PHASE11_GROUND_TRUTH_PROTOCOL.md` supplements it with a four-state taxonomy; the decision package records a v9/v7 versus earlier-version authority conflict. The researcher has not selected the authoritative protocol for official evaluation.

This guide therefore describes the shared concepts and records conflicts explicitly. It does not choose v8, v9, v7, or any evaluation profile. A future reviewer must be given a signed protocol version before a real review begins.

## 2. State vocabulary

Use exactly one state per boundary:

| State | Use |
|---|---|
| `OBSERVABLE` | The boundary is directly supported by identifiable source evidence in the recording. Record value, reference camera, frame index where available/required by the approved workflow, and a specific rationale. |
| `UNOBSERVABLE_NOT_APPLICABLE` | The boundary concept does not apply to the event, such as train boundaries in a no-train control, or the approved protocol says it cannot be observed/applicable. Record no value and explain why. |
| `CENSORED` | The boundary lies outside the available recording window (left or right). Record no point value and state the direction and recording limitation. |
| `UNCERTAIN` | The boundary is nominally in scope but ambiguity prevents a defensible point placement. Record no value under the current Stage-2.1 schema and describe the ambiguity. |

Never convert a non-observable state to a numeric time by interpolation, nearest-neighbor copying, another camera's clock, or model output.

## 3. Shared review procedure for every boundary

1. Confirm event key, cohort, front/back source identity, and active proposal reference.
2. Review source evidence independently of evaluated-model outputs.
3. Locate the physical/visual boundary under the protocol version supplied by the researcher.
4. Decide whether the boundary is observable, not applicable/unobservable, censored, or uncertain.
5. Record the camera-local time and frame evidence only if observable.
6. Write a rationale that another reviewer can audit without guessing.
7. Note any missing source, hash discrepancy, clock limitation, or landmark ambiguity.
8. Identify which downstream metrics cannot be evaluated when the boundary is not observable.

## 4. Boundary-by-boundary guide

### T0 — `T0_first_visible`

**Current shared meaning:** earliest identifiable visual appearance of the approaching train/rail vehicle in the available scene. The current canonical table places it on the front/approach view and treats a vehicle already visible at recording start as a censoring case.

**Required evidence:** an identifiable rail vehicle at a specific frame, with the front-camera source and rationale describing the first defensible appearance. Do not use a detector confidence or proposal value as evidence.

**Observable when:** the first identifiable appearance lies within the recording and can be pointed to at a frame.

**Unobservable/not applicable when:** the approved protocol says the event type has no T0 concept, or available evidence cannot establish a first appearance and the case is not a censoring case. Explain the distinction.

**Censored when:** the vehicle is already visible at the beginning (left-censored), or the relevant observation window prevents seeing the boundary. State left/right direction explicitly.

**Uncertain when:** occlusion, lighting, compression, or scene ambiguity prevents identifying the first appearance at a defensible frame.

**Rationale:** identify the visual object and the recording limitation/ambiguity; never claim a synthetic time at zero.

**Metrics affected:** any detection-latency or T0-anchored lead-time metric is non-evaluable or must use the approved censoring rule when T0 is censored/uncertain. Do not substitute another boundary.

### T1 — `T1_danger_zone_entry`

**Current shared meaning:** earliest crossing of the operational danger-zone entry boundary by the leading edge of the locomotive/rail vehicle. The current worktree canonical table assigns it to the front/approach view, but the exact operational convention is tied to the unresolved protocol authority.

**Required evidence:** the leading edge crossing the approved danger-zone landmark/plane, with camera-local frame/time and rationale. The landmark must be named in the approved protocol, not invented during review.

**Observable when:** the leading edge and the approved landmark are simultaneously identifiable.

**Unobservable/not applicable when:** no train exists in a no-train event, or the approved protocol says the landmark cannot be established for this event. Explain why.

**Censored when:** the crossing occurred before recording began or after the usable recording ended. Do not infer from T0 or T2.

**Uncertain when:** the landmark, leading edge, or occlusion makes the crossing frame ambiguous.

**Rationale:** name the approved landmark and explain the camera-local evidence or the exact limitation.

**Metrics affected:** warning-lead-time and T1-anchored premature-opening profiles are non-evaluable when T1 is missing, censored, uncertain, or when the selected profile does not use T1. The evaluation-profile decision is pending.

### T2 — `T2_crossing_occupancy_start`

**Current shared meaning:** beginning of physical crossing occupancy under the current canonical table. The table describes the locomotive body occupying the road danger zone; exact interpretation and operational landmark remain protocol-dependent.

**Required evidence:** the approved occupancy boundary/plane and the leading vehicle's relationship to it, with camera-local frame/time and rationale.

**Observable when:** occupancy onset is directly supported by the approved landmark and source view.

**Unobservable/not applicable when:** no train is present, or the approved protocol makes the concept inapplicable/unobservable for the event.

**Censored when:** occupancy begins before the recording or outside the usable recording window.

**Uncertain when:** the occupancy plane, leading edge, or occlusion prevents defensible placement.

**Rationale:** distinguish occupancy from mere first visibility or danger-zone approach; explain any camera limitation.

**Metrics affected:** occupancy-onset and any metric requiring T2 cannot be evaluated as a point observation when T2 is censored/uncertain/unobservable.

### T3 — `T3_locomotive_unit_clearance`

**Current shared meaning:** trailing edge/rear coupler of the leading locomotive unit clears the defined danger-zone boundary while trailing vehicles may remain. The canonical worktree table assigns the departure-side view. This is distinct from the front of the locomotive leaving a view.

**Required evidence:** the rear of the locomotive unit and the approved departure boundary are identifiable in the applicable camera, with camera-local frame/time and rationale.

**Observable when:** the rear edge/coupler and boundary plane can be identified at a frame.

**Unobservable/not applicable when:** the concept does not apply to the event under the approved protocol (for example, a no-train event), or the required evidence cannot be obtained and the approved procedure classifies it as unobservable.

**Censored when:** the relevant event occurs outside the recording window. State whether left or right censoring applies; do not infer T3 from T4.

**Uncertain when:** locomotive-unit identity, coupler, landmark, or occlusion makes the clearance frame ambiguous.

**Rationale:** explicitly distinguish locomotive-unit clearance from final-tail clearance.

**Metrics affected:** locomotive-continuity diagnostics and any T3-dependent analysis are non-evaluable without an observable T3. T3 is not a substitute for T4 safety clearance.

### T4 — `T4_tail_clearance`

**Current shared meaning:** trailing edge/rear buffer of the final rail vehicle clears the physical danger-zone boundary. The current canonical table calls this the primary safety-clearance boundary and assigns the departure-side view.

**Required evidence:** the final vehicle's rear edge/buffer and the approved departure boundary are visible together in the relevant camera.

**Observable when:** the final vehicle can be identified and its complete exit is supported at a frame.

**Unobservable/not applicable when:** no train is present, or the event/protocol makes the concept inapplicable.

**Censored when:** the recording ends before the final vehicle clears (right-censoring), or the boundary lies outside the available window. Do not replace with the final visible frame.

**Uncertain when:** final-vehicle identity, tail edge, landmark, or occlusion prevents a defensible clearance frame.

**Rationale:** state that T4 refers to the final vehicle, not the locomotive unit; state the recording endpoint or ambiguity when applicable.

**Metrics affected:** premature-opening, clearance latency, and any safety metric anchored to final tail clearance are non-evaluable as point estimates when T4 is censored/uncertain/unobservable. The selected evaluation profile may further change metric eligibility.

### T0–T4 for the engine case

The engine event is a separate case study and must not be folded into train or no-train aggregates. Existing documents discuss a possible T3/T4 coincidence for a single locomotive, but this guide does not select or approve that semantic. The reviewer must follow the researcher-approved protocol instruction and document why any boundary is observable, not applicable, censored, or uncertain.

## 5. No-train controls

For a no-train event, do not manufacture train-boundary timestamps. The Stage-2.1 schema's `UNOBSERVABLE_NOT_APPLICABLE` state is the available representation when the approved protocol confirms that train boundaries do not apply. The reviewer must still perform the required source check, document the absence/non-applicability rationale, and keep the cohort separate from train and engine metrics.

## 6. Conflict register and pending decisions

| Issue | Existing evidence | Status |
|---|---|---|
| Protocol authority (earlier versus worktree v9/v7 documents) | `PROTOCOL_AUTHORITY_COMPARISON_20261030.md` | Pending; do not select here |
| T0–T4 state taxonomy versus older `applicable` fields | Phase 11 supplement and Stage-2.1 schema use four explicit states; older protocol examples use different fields | Preserve explicit state in Stage-2.1; researcher must bind protocol semantics |
| Observable frame requirement | Documentation describes frame evidence; current `BoundaryAdjudication` code requires value/camera but does not enforce a frame index | Workflow must require it operationally unless researcher approves a documented exception; no code change here |
| `reference_camera="both"` | M4A prose mentions `both`; current schema accepts only `front`/`back` for observable boundaries | Unresolved implementation/documentation discrepancy; do not silently use `both` |
| Second-review trigger | Current gate rejects unresolved statuses and same-reviewer claims, but does not auto-trigger on every CENSORED/UNCERTAIN state | D3(a) pending |
| R04 clock mapping | Candidate evidence exists but accepted scope is unresolved | Keep camera-local times; do not apply offsets |
| Evaluation profile | v9/M4 comparison is proposed, not approved | Do not label metrics evaluable based on a profile choice |

## 7. Reviewer stop rule

Stop and escalate on a hash mismatch, missing/wrong camera, model-output exposure, unknown event identity, ambiguous protocol instruction, inability to identify the approved landmark, or any pressure to fill a numeric value unsupported by evidence.