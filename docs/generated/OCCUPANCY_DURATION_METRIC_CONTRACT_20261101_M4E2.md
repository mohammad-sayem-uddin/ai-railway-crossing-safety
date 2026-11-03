# Full Crossing Occupancy Duration — Metric Contract

> **PROPOSED — NOT APPROVED — NOT VALIDATED — NOT AUTHORIZATION.**
> The researcher selected the *definition* below. No schema field, evaluator, validator, approval or data exists for it.
> **Occupancy-duration metric validation has not occurred.** Working identifier `full_crossing_occupancy_s` is a proposal
> only (it avoids the existing v9 use of "physical occupancy" for `T4 − T1`; see D1 doc C3).

> **Revised in Mission 4E.3:** `T_OCC_START` is a proposed prose alias only (it exists nowhere in the repo); the crossing conflict area, the T1/T2/T4 reconciliation, same-camera feasibility (**not established**), censoring effects and engine exclusion (ENG-1…8) are in `DEFINITION_RECONCILIATION_AND_CROSSING_CONFLICT_AREA_20261101_M4E3.md` and `SAME_CAMERA_FEASIBILITY_CENSORING_AND_ENGINE_EXCLUSION_20261101_M4E3.md`. Option A (T2 under reconciled wording) is a recommendation, not a decision.

## 1. Researcher-selected definition (verbatim intent)

`D_occupancy = T4 − T_physical_block_onset`, in **seconds**.

- `T_physical_block_onset`: independently established physical crossing-blocked onset.
- `T4`: approved tail-clearance boundary — rear of the final train vehicle clears the defined roadway boundary (GT v7 §2.4: rear buffer/diaphragm of final vehicle clears the vendor-stall / departure roadway boundary plane on `camera_back.mov`).
- **Never** substituted by replay-derived `first_blocked`, by `t_blocked`, by T0, or by any unrelated timestamp.

## 2. Is a suitable physical onset boundary already supported? (read-only finding)

**Verdict: a CANDIDATE exists but is NOT designated, and has unresolved definition/clock problems. For every event the
onset is currently *not evaluable*.** No field named for "physical block onset" exists in any schema.

| Candidate | Supported today? | Definition text | Camera | Problem |
|---|---|---|---|---|
| `T2_crossing_occupancy_start` | **Yes** — canonical name (`schemas.py:28`), accepted by Stage-2.1 `BoundaryAdjudication` (`state`, `value_s`, `reference_camera`, `frame_index`, `rationale`), exposed by `ApprovedEventGroundTruth.observable_value()` / `boundary_cameras` | §2.4: "front pilot crosses the transverse camera plane / roadway boundary line … commencing physical road lane blockage"; §2.1: "locomotive body *fully occupies* the danger zone" | landmark defined on **front** only | **Two conflicting definitions (C1)**; ambiguous reference line (C5); on the *front* clock while T4 is on the *back* clock |
| `T1_danger_zone_entry` | Yes | leading edge crosses into danger zone (frog/approach line) | front | v9 already calls `[T1,T4]` the "Physical Hazard Occupancy"; it is an *approach* line, not road blockage |
| (none: "physical crossing-blocked onset") | **No** | — | — | proposed field would be new; **not added** |

Nothing in the repository designates which of these (or a new boundary) the researcher means by "physical crossing-blocked onset".
That mapping is a **researcher decision** (open, see §9). My recommendation, not a binding choice: **T2 under the §2.4 wording**
("commencing physical road lane blockage") is the nearest literal match, *conditional on* resolving C1/C5 and the clock issue.

## 3. Can camera views and timestamp conventions support reliable independent adjudication?

Assessed from documents/schemas only; **no media was opened**, so visibility and occlusion are *unverified*, not "fine".

| Aspect | Finding |
|---|---|
| Landmark for onset | Documented on `camera_front.mov` only (turnout frog for T1; transverse plane/roadway boundary line for T2). No back-camera landmark for T2 exists (C4). |
| Landmark for T4 | Documented on `camera_back.mov` only. |
| Same-camera pair | Would avoid R04 but needs a **new landmark convention** (T2 on back, or T4 on front). Not defined; not invented here. |
| Cross-camera pair | `T2(front) → T4(back)` requires R04: independent media-local clocks (GT v7 §2.4(5), §7 item 4); container creation-time metadata is unreliable (v9 line 227: front/back dates differ by days). Offset convention `Δt = t_back − t_front`. |
| Alignment eligibility | GT v7 §5: `aligned` (δ≤0.5 s) eligible for cross-camera temporal metrics; `partially_aligned` (≤2.0 s) only with error bounds; `unaligned`/unmeasured **strictly excluded**. R04 is unresolved ⇒ all cross-camera durations are currently excluded. |
| Time resolution | `frame_index` supported; `native_fps` is only in proposals. The promoted schema has **no** timestamp-uncertainty field (the timing-pilot schema has `timestamp_uncertainty_s`, but pilot drafts are permanently unapproved). |
| Independence | Onset and T4 are both human-adjudicated ground truth ⇒ the metric is independent of the replay by construction. It then describes the *event*, not system performance. |

## 4. Censoring, occlusion, missingness

| Situation | Treatment (proposed) | Supported representation today |
|---|---|---|
| Train already occupying crossing at recording start (onset **left-censored**) | `NOT_EVALUABLE: onset_left_censored`; counted; no zero/negative timestamp; no use of recording start as onset | state `CENSORED`; **direction only in free-text `rationale`** (main schema has no `censoring_direction`; GT v7 §2.4(3) requires `value_s=null` + rationale) |
| Recording ends before T4 (**right-censored**) | `NOT_EVALUABLE: t4_right_censored` | same |
| Occluded / ambiguous onset or T4 | `UNCERTAIN` ⇒ `NOT_EVALUABLE: onset_uncertain` / `t4_uncertain` | `UNCERTAIN` state supported |
| Not applicable (no-train, engine) | `NOT_EVALUABLE: no_train_event` / `engine_event_excluded` | cohort + `UNOBSERVABLE_NOT_APPLICABLE` |
| Onset boundary not in any approved record | `NOT_EVALUABLE: physical_onset_missing` | **all events today** |
| Onset supplied from a replay/system source | `NOT_EVALUABLE: onset_not_independently_established` | needs a provenance attribute that does not exist (proposed) |
| Cross-camera, R04 unresolved or `unaligned` | `NOT_EVALUABLE: clock_mismatch_r04_unresolved` | `clock_aware.py` analogue exists for replay boundaries, none for occupancy |
| Non-finite, negative, or non-positive result | `invalid_timestamp` / `nonpositive_duration` | — |

Default censoring treatment in the documented profile is `exclude_censored_from_point_estimates`
(`protocol_choices.DOCUMENTED_PROFILE`). One-sided-bound reporting (`report_censored_as_bounds`) is **not implemented**.

## 5. Eligibility, missingness and denominator rules (proposed, occupancy-only)

| ID | Rule |
|---|---|
| OCC-E1 | Population: train-cohort events; cohort-qualified id (`train_events/event_NNN`). Engine and no-train excluded with their own reason codes. |
| OCC-E2 | **Evaluable** iff: promoted/approved GT; onset `OBSERVABLE`, human-sourced, finite ≥0, with `reference_camera`; T4 `OBSERVABLE`, finite ≥0, with `reference_camera`; same camera **or** accepted R04 alignment `aligned`/`partially_aligned` with stated uncertainty; computed `D > 0`. |
| OCC-E3 | Same-camera: `D = T4 − onset`. Cross-camera front-onset/back-T4: `D = T4 − (onset + Δt)`. |
| OCC-E4 | `partially_aligned` results carry `error_bound_s = δ` and are reported in a **separate stratum**; never silently pooled with `aligned`/same-camera values. |
| OCC-E5 | Everything else is `NOT_EVALUABLE` with exactly one primary reason code (order of precedence: cohort → onset → T4 → values → clocks). No imputation, interpolation, or fallback to T1/T0/`first_blocked`. |
| OCC-E6 | **Denominator = OCC-E2-evaluable events only.** Censored events are *not* in the denominator but are *counted* (by direction). |
| OCC-E7 | Occupancy and M4/M5 are **separate**: different boundary requirements, different evaluable sets (test `test_m4_and_occupancy_denominators_are_independent_and_not_combined`), **no combined or composite score**. A never-protected (M5) event can be occupancy-evaluable; an M4-evaluable event can be occupancy-not-evaluable. |
| OCC-E8 | Occupancy needs **no replay** — it must not be computed from, or conditioned on, any `SimulationStep`. |
| OCC-E9 | The protocol-choice envelope cannot currently carry this metric (`validate_protocol_choices` rejects unknown keys) — binding it requires an unapproved code/governance change (gap G-OCC-10). |

## 6. Status of what was tested

57 synthetic tests (see mission report) exercise the *written rules* through a **test-local** reference function.
They validate internal consistency of this contract. They do **not** validate any schema, evaluator or real-data result.
