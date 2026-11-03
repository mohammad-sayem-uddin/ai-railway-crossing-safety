# Same-Camera Feasibility, Censoring Effects, and Engine-Event Exclusion

> **PROPOSED — NOT APPROVED — NOT AUTHORIZATION.** Feasibility from **existing non-media documentation only** (Mission 4E.3).
> No raw `.mov`/`.mp4`/`.wav` was opened, previewed, decoded or hashed. Statements about what a camera "sees" are quotations of
> earlier-mission documents; they are **second-hand and not re-verified here**. Candidate (unapproved) figures are cited only to
> show scale of the problem; they are **not eligibility determinations** and no event was adjudicated.

## 1. Can a same-camera (onset, T4) pair be observed? — answered from documents

The occupancy duration needs the CCA **entry** event (`T_OCC_START`, §2 of the reconciliation document) and **T4** (exit plane X).

| Configuration | Documentary evidence | Verdict |
|---|---|---|
| **Front camera only** (E and X both on `camera_front`) | `OVERNIGHT_RESEARCH_HANDOFF.md:60`: "T4 … Observable **only on `camera_back`**. Completely absent from front camera stream." `B0_B1_B2_METRIC_SPECIFICATION.md:267-270`: the front camera views the approach zone and turnout frog; "the rear buffer of departing trains cannot be reliably observed on the front camera." | **Not feasible** (documented as contradicted) |
| **Back camera only** (E and X both on `camera_back`) | No document names an *entry-plane* landmark on the back camera. T2's landmark is defined on `camera_front.mov` only (GT §2.4(2)), although the §2.1 table lists T2's camera as "Front / Back". The only back-camera "entry" in the documents is a **frame-entry** event ("enters back frame", `R04_ALL_EVENT_CALIBRATION_INVESTIGATION.md` candidate sync pairs; `candidate_back_marker: "Front bumper enters back view"`, GT §6.1 example). The back camera is described as a lateral trackside camera "further along the track, toward the departure side" (`PHASE10_1_POLICY_COMPARISON_REPORT.md:106`). | **Not established.** Whether plane E is in the back camera's view is **undocumented**. |
| **Cross-camera** (E on front, X on back) | This is the *only* configuration the protocols define (T1/T2 front; T3/T4/scene-clear back; `PHASE11_GROUND_TRUTH_PROTOCOL.md:69`). Requires R04: independent media-local clocks, `Δt = t_back − t_front` (GT §5). | **Documented but blocked by R04** (see §2) |

**Why a back-camera "frame-entry" time is not an acceptable substitute for E.** A frame-entry event depends on where the camera is mounted and its field of view; it is a property of the *camera*, not of the *crossing*. The researcher's definition requires an *independently established physical* blocked onset. Using frame-entry would silently redefine the metric to a different physical instant (and a different one at each site). It must not be used unless the researcher defines it as a new, explicitly camera-relative boundary.

**Conclusion.** From non-media documentation **no same-camera pair is technically established.** The two ways to change that are outside this mission's authority:
1. a researcher statement of camera geometry (e.g. "plane E is visible on `camera_back` for events …"), or
2. an *authorized* human review/geometry-sheet step on the media (cf. `archive/SYNCHRONIZED_DATA_COLLECTION_PROTOCOL.md:41`).

Neither was done.

## 2. What cross-camera use would depend on (R04), per the documents

- Clocks are independent; container creation-time metadata is unreliable (v9 line 227: front/back dates differ by days).
- Documents **disagree on the supported subset size**: "exactly 11 of the 27" (`PHASE11_GROUND_TRUTH_PROTOCOL.md:70`) vs "supported on only 12 events; ambiguous on 8; provisional on 7" (`OVERNIGHT_RESEARCH_HANDOFF.md`). A reconciliation exists (`R04_ELEVEN_VS_TWELVE_RECONCILIATION_20261101_M4D.md`); **not re-verified here.**
- The validated offsets are "acoustic-lag reproducibility estimates, not independently-verified hardware synchronization"; `PHASE11_GROUND_TRUTH_PROTOCOL.md:70` refuses to use them to shift human-annotated ground-truth timestamps because that "would conflate two different kinds of evidence". Using them for occupancy would therefore be a **new, explicit researcher decision**, not a default.
- GT §5 eligibility: `aligned` (δ ≤ 0.5 s) / `partially_aligned` (≤ 2.0 s, with bounds) / `unaligned` (excluded).
- Today, `phase12_r04_scope_decision.json` is absent ⇒ every cross-camera occupancy duration is `clock_mismatch_r04_unresolved`.

**Trains in both directions?** If the cohort mixes travel directions, the fixed "front = approach, back = departure" assumption must hold per event (see reconciliation §3, condition 1). Undocumented.

## 3. Effect of left-censoring and missing boundaries

### 3.1 Definitions for the occupancy metric
- **Left-censored onset:** the train had already crossed E before the recording began. True onset ≤ 0 on the front clock; v7 forbids a pre-recording or synthetic timestamp (GT §2.3, §2.4(3)). `value_s = null`, rationale required.
- **Right-censored T4:** the recording ended before the final vehicle crossed X (GT §2.4(3)).
- **Uncertain:** the boundary is in-window but cannot be placed defensibly (occlusion, minimal visible change).

### 3.2 Direction of bias if censored events are simply dropped
- **Right-censoring (T4) biases the retained sample toward *shorter* durations**, because a longer occupancy is more likely to be cut off by the recording end. This is a structural, documentable effect.
- **Left-censoring (onset)** depends on when the recording began relative to arrival; the direction of bias cannot be assessed from documents. Report the counts; do not extrapolate.
- Neither effect is correctable by imputation (`D = T4 − 0`, or `D = recording end − E`) — those are lower bounds on a *different* quantity and are prohibited as point values. The documented profile default is `exclude_censored_from_point_estimates`; bound-reporting (`report_censored_as_bounds`) is **not implemented**.

### 3.3 Scale indicators from documents (candidate/audit-level, unapproved — not a determination)
| Indicator | Document | Note |
|---|---|---|
| Candidate T1 and T2 "observable" in 22/23 train events; T4 in 22/23; `event_005` null for T1/T2/T4 (dual-ended censoring) | `DATASET_ANNOTATION_QUALITY_AUDIT.md:42-71` | candidate values; no human approval exists |
| T1/T2 flagged **ambiguous** on 12 rows across 6 events (004, 006, 007, 011, 013, 018): train already close/lateral from the first frame, "minimal visible positional change" | `PHASE11_4_FINAL_VIDEO_ANNOTATION_AUDIT_REPORT.md:67` | these are exactly the events where *onset* adjudication is likely to end `UNCERTAIN`/`CENSORED` |
| T4 ambiguous for `event_011` and `event_021` (night, small distant object); `event_006` T4 frame shows an unrelated locomotive | same, §3.2 | |
| `T0` left-censoring counted as **20/23** in one document and **23/23** in others (`DATASET_ANNOTATION_QUALITY_AUDIT.md:59` vs `PAPER_DRAFT…:163`, `DEEP_RESEARCH…:217`) | — | **Doc inconsistency; irrelevant to occupancy** (T0 is not used), but it shows censoring counts in the docs are not authoritative |

**Documentation-derived ceiling, not an estimate:** if every candidate marker were accepted, at most **22** of 23 train events could have both an onset and T4; if the six ambiguous-onset events and `event_021` all ended uncertain/censored, the ceiling would fall to **15**. These bound the *candidate* inventory only. The **actual evaluable count today is 0** (no approved GT, R04 unresolved). T0's censoring prevalence does **not** predict T2's; T2's prevalence is unknown.

### 3.4 Missing-boundary effect matrix

| Missing / unusable | Occupancy duration | M4 | M5 |
|---|---|---|---|
| Onset (E) missing / censored / uncertain | NOT_EVALUABLE | unaffected (M4 does not use onset) | unaffected |
| T4 missing / censored / uncertain | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE (not asserted) |
| Replay missing | **unaffected** (ground-truth-only) | NOT_EVALUABLE | NOT_EVALUABLE |
| Replay ends before T4 | unaffected | see M4 correction document | see M4 correction document |
| R04 absent | cross-camera ⇒ NOT_EVALUABLE | unaffected on a back-only replay; needed for fused replay | same as M4 |
| Occluded / minimal-change onset | `UNCERTAIN` ⇒ NOT_EVALUABLE | unaffected | unaffected |

### 3.5 Uncertainty budget (not invented)
D inherits the uncertainty of each endpoint (frame quantization; reviewer tolerance) and, cross-camera, the offset uncertainty δ. The design document proposes a tolerance `u` (default 0.5 s without a second annotator, `[D-8]`, pending). **How to combine them is a researcher decision**; this mission specifies none. The promoted schema carries no uncertainty field (G-OCC-04).

## 4. Engine-event exclusion specification [proposed]

| Id | Rule |
|---|---|
| ENG-1 | `engine_events/*` is excluded from the **M4 denominator, M5 denominator and the pooled occupancy-duration denominator**. |
| ENG-2 | The engine test runs **first**, before any boundary, replay or clock logic. |
| ENG-3 | Identification uses the **cohort-qualified id** (`engine_events/event_001`) or the cohort field. A **bare id** (`event_001`) in an occupancy/M4/M5 computation is rejected fail-closed with `cohort_unqualified_id`. *Reason:* current `evaluate_run` recognises an engine only via `cohort=="engine_events"`, `ground_truth_status=="engine"`, or an `engine_events/` id prefix — a bare id with no cohort is treated as a **train** event (characterized by test `test_current_code_bare_engine_id_without_cohort_is_treated_as_train`). |
| ENG-4 | Reason code: `engine_event_excluded` (identical to existing code; reuse, do not add a second). |
| ENG-5 | Reporting: counted on the existing separate `engine_events` line. **No engine value enters any pooled mean/median/min/max.** An optional **N=1 descriptive row** (its own onset and `T3≡T4`) may be shown only if approved GT exists *and* the researcher opts in; it is labelled "case study, not a distribution". |
| ENG-6 | Rationale from documents: zero trailing cars ⇒ `T3 ≡ T4` (GT §2.2, §3); "must be isolated from train-event cohort" (`DATASET_ANNOTATION_QUALITY_AUDIT.md:70`); N = 1; the occupancy of a lone locomotive reflects locomotive length and speed, not consist. The active candidate back-camera T4 is documented as right-censored (`PHASE11_4…:47`). |
| ENG-7 | **Open conflict, researcher to resolve:** `EXPERIMENT_DESIGN_FINAL.md` §8.3 lists the M4/M5 population as "**Train, engine**" and `[D-9]` sets `T3 = T4` for engine. The code and v7 exclude engine. This proposal follows the code and v7. If the design document governs, ENG-1 changes for M4/M5 (not for occupancy pooling). |
| ENG-8 | No-train events are separate: `no_train_event` (occupancy), false-alarm path (M4). |

## 5. Not claimed
No same-camera pair is declared feasible. No eligibility, censoring or approval is asserted for any real event. The ceilings in §3.3 come from earlier unapproved candidate documents and are not results.
