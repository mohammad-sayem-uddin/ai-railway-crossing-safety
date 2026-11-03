# Premature-Opening: v9 vs M4 Technical Comparison and Decision Record

**Decision status: UNRESOLVED — no automatic approval.** This record is a technical comparison, not a researcher decision. The evaluator must continue to refuse an official run until an allowlisted researcher records `choices.premature_opening_window`.

## Exact predicates

| Candidate | Predicate | Required evidence | What is *not* included |
|---|---|---|---|
| **Protocol v9** (`t1_entry_to_t4_clearance`) | Failure if an opening command occurs while **T1 ≤ t < T4**; implemented replay flag additionally requires `OPENING`/`OPEN` and `not is_passage_blocked`. | Candidate/approved T1 and T4; one aligned common timeline. | T0, pre-T1 openings, and events with missing/unobservable T4. |
| **M4** (`first_blocked_to_t4_clearance`) | Set `t_blocked` to the first replay tick with `blocked=true`. Failure if a blocked→not-blocked transition or opening command occurs at **t_blocked < t < T4**; blocked status does not suppress the opening-command check. | Candidate/approved T4; replay trace with blocked state and opening commands. | T0 and T1 are not required by the predicate. A command exactly at `t_blocked` or exactly T4 is outside the strict interval. |

M4 is paired with **M5 (never protected)**: if no blocked tick occurs strictly before T4 (`t_blocked` is absent or `t_blocked ≥ T4`), the event is `never_protected`; M4 is **not evaluable**, not a zero-premature-opening success. The implementation records M5 as its own count and evaluable denominator; events where a metric cannot be computed remain excluded with reasons.

## Code/protocol compatibility note

The implemented v9 window is **[T1, T4)**. The trace predicate requires a gate state of `OPENING` or `OPEN` and `is_passage_blocked == false` at the sampled step. The window and this sampled-step/physical-blocked predicate are implementation semantics, not researcher acceptance. M4 is separately available through the trace-level `m4_premature_opening` function and intentionally flags an opening command even when the arm remains physically blocked; it also requires a blocked→not-blocked trace transition.

## T0–T4 and censoring

- **T0** first visual appearance; recording-start presence may be left-censored (`true physical T0 ≤ 0`) and must never be converted to a numeric point time for these metrics.
- **T1** danger-zone entry on the front-camera clock. v9 requires an observable, approved T1; M4 does not.
- **T2** occupancy start; diagnostic for physical occupancy, not required by either v9 or M4.
- **T3** locomotive-unit clearance on the back-camera clock; diagnostic only for these predicates.
- **T4** final-vehicle tail clearance on the back-camera clock; primary right boundary for both candidates.
- For v9, missing, ambiguous, unobservable, or right-censored T1 or T4 makes the event not evaluable; for M4, T4 is required but T1 is not. A missing T0 does not by itself exclude either candidate. `T3` and `T_scene_clear` do not define either window. The engine-only cohort has `T3 ≡ T4` only when that relationship is established by the annotation protocol; it does not supply a substitute T4 when T4 is censored.
- Candidate boundaries are not approved ground truth. Censoring is preserved as a status/reason and never replaced with `0`, an imputed time, or a favorable outcome.

## Clock and camera compatibility

T1 is on the front clock and T4 on the back clock. v9 requires both boundaries on one valid common timeline; compare them only after the researcher accepts the event scope and validated event-specific offset, with `t_master = t_back + offset_s` (front is master). M4 may use the back-local T4 and back-local replay trace without fusing camera clocks. The acoustic diagnostic has 12 `CALIBRATION_SUPPORTED` candidate events and 15 non-supported events; its manifest remains `CANDIDATE_UNVALIDATED_DO_NOT_MERGE`, with `human_review_status: REVIEWED_WITH_CORROBORATION. Visual landmark frame pairs inspected and verified by Lead Researcher Raihan Kabir Rahu under ADMINISTRATIVE_DISPOSITION_R04_READ_ONLY_UNBLOCK_20261025. train_events/event_010 promoted to CALIBRATION_SUPPORTED via verified visual landmark corroboration.`. Calibration availability does not approve scope.

- **Dual-camera candidate scope:** v9 can be computed only after accepted alignment and approved T1/T4. M4 can use the approved back-clock T4 and replay trace; it does not inherently require a fused clock.
- **Independent camera scope:** M4 may be computed on a back-stream replay if the system produces a back-clock `t_blocked` and back-clock T4. v9 is not comparable because T1 and T4 are on different clocks. This does not make an independent-camera M4 result a full physical safety result.
- **Front-only/single-camera scope:** T4 is on the back clock, so neither candidate is evaluable from front-only evidence; do not infer or synthesize T4.

## Edge cases and compatibility

| Edge case | v9 | M4 / M5 |
|---|---|---|
| Opening before T1 after an earlier block | Not a v9 failure; report separately only if a separate endpoint is predeclared. | Failure if strictly after `t_blocked` and before T4. |
| Opening exactly at T1 | Inside the window, but the implemented v9 sample still requires `not is_passage_blocked`; discrete samples and boundary equality must follow the locked trace rule. | Not determined by T1; apply only the M4 blocked-time interval. |
| Opening exactly at `t_blocked` | Not special to v9 except as it relates to T1 and blocked state. | Excluded by strict lower bound. |
| Opening exactly at T4 | Excluded by the half-open interval. | Excluded by strict upper bound. |
| Opening command while arm remains physically blocked | Implemented v9 predicate does not flag a sample with `is_passage_blocked == true`. | M4 command-level rule flags the opening command regardless of `blocked`; a blocked→not-blocked transition is also a failure. |
| Repeated blocked ticks | No special state needed. | First blocked tick defines `t_blocked`; later blocked ticks do not reset it. |
| Never blocked before T4 | Not a special class; v9 can still be evaluated if T1/T4 and trace are available. | M5=`never_protected`; M4 premature value is `null`, excluded from M4 denominator. |
| T4 missing, ambiguous, or right-censored | Not evaluable. | Not evaluable; do not classify as M5 from censoring. |
| T1 missing/ambiguous | Not evaluable. | Does not by itself affect M4. |
| Engine-only event | Apply T4 only if independently adjudicated under the engine-event rule. Do not assume T3=T4. | Same requirement; T4 censoring blocks M4 and M5 classification. |
| No-train event | Not applicable. | Not applicable; retain nuisance/false-alarm counts separately. |
| Sparse/no replay samples in the interval | No sampled qualifying v9 event is not evidence about unobserved times; use the evaluator's discrete trace semantics and sampling disclosure. | No observed transition/command only describes the available replay trace, not continuous-time behavior. |

## Decision and blocking record

No candidate is selected here. The exact unresolved choice remains either `t1_entry_to_t4_clearance` (v9) or `first_blocked_to_t4_clearance` (M4). The choice changes inclusion criteria and denominator: v9 requires approved T1 and T4 on a compatible common timeline, while M4 requires approved T4 plus replay `t_blocked` and makes never-protected events a separate M5 count rather than M4 successes. Censoring and unavailable clocks remain exclusions with reasons, never favorable zeroes. Selecting by recency, implementation convenience, or an AI recommendation would be an unauthorized scientific decision. Until a researcher records one option in `data/manifests/phase12_protocol_decision.json`, official evaluation remains blocked. This document also does not authorize the 12-event exploratory scope; that scope requires its separate decision and remains candidate-only.
