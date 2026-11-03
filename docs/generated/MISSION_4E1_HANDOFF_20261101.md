# Mission 4E.1 Handoff

**Mission:** D1/D2 Researcher Decision Binding Verification  
**Date:** 2026-11-01  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Branch:** `main`  
**HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`

## A. Git state

- Initial porcelain entries: 373
- Initial staged files: 0
- Final HEAD unchanged.
- No staged changes, commits, pushes, resets, cleans, or broad reverts.

## B. Researcher decisions as supplied

- D1 researcher-selected v9.0.0 real-world protocol + v7.0.0 ground-truth protocol.
- D2 researcher-selected conditional M4 identifier `first_blocked_to_t4_clearance`.
- D2 remains conditional pending technical verification/binding.

Mission 4E.1 did not re-ask these selections and did not record them as repository approvals.

## C. D1 verification

The current v9/v7 documents are internally compatible:
- v9 §5.4 references v7 §2.4.
- Both use the operational danger-zone convention.
- Both define T1/T2 approach and T3/T4 departure semantics consistently.
- Both preserve independent camera-local clocks and unresolved R04.
- Both require human verification and censoring/uncertainty handling.

HEAD v8/v6 differs primarily in R03: site survey remains a blocker and landmarks remain provisional. v9/v7 retires R03 as a separate blocker while disclosing that the operational convention is not geodetic ground truth.

Remaining v8/v6 source references are historical comparisons, canonical decision-register alternatives, and legacy annotator comments. They do not indicate active v8/v6 execution. No migration is required for invalidated legacy review records.

## D. D2 start boundary

`first_blocked` is not a ground-truth field. It is the timestamp of the first retained replay `SimulationStep` with `is_passage_blocked=True`. It is produced by the gate model/replay timeline and is not T0/T1/T2/T3/T4. If no blocked step exists before T4, M4 returns `None` and sets M5 `never_protected=True`.

## E. D2 end boundary

T4 is `boundary_adjudications.T4_tail_clearance`: the final vehicle rear buffer clears the unified departure roadway boundary plane on the back/departure camera under v9/v7. It must be human-observable and approved for point evaluation. CENSORED, UNCERTAIN, or missing T4 excludes the event from point M4 evaluation.

## F. Complete M4 contract

- Start: first replay blocked step.
- End: approved T4.
- Units: seconds on replay/back-camera local timelines.
- R04: not required for the boundary function itself, but required for any fused camera replay scope.
- M4 predicate: unblocked/opening state strictly between start and T4.
- No blocked step: M5, separate outcome, excluded from M4 denominator.
- Engine: excluded.
- No-train: false-alarm path, not M4 train denominator.
- Aggregation: only evaluable train events with non-null premature result; mixed windows rejected.

## G. Eligibility findings

- 27 total events: 23 train, 3 no-train, 1 engine.
- Confirmed M4-eligible events: 0 (no approved Stage-2.1 records).
- Engine confirmed ineligible for train denominator: 1.
- Train event eligibility remains unknown pending human review, approved T4, and replay.
- T0 censoring figures do not determine M4 eligibility because M4 does not use T0/T1.

## H. Required future artifacts (not created)

- `data/manifests/phase12_protocol_decision.json` binding D1 and M4.
- `data/manifests/phase12_r04_scope_decision.json` where dual-camera scope is used.
- Stage-2.1 review records and promotion receipt.
- Official split and evaluation manifest.
- EVAL-AUTH.

## I. Checks performed

- Read-only protocol/version/hash comparison.
- Source implementation inspection.
- Decision-register and profile-option loading.
- Official readiness assessment: `ready=False`, 9 blockers.
- Queue audit: 27/27 PASS; tracker 27 NOT_SCHEDULED.
- Regression suite: **76 passed**.
- Compile and diff checks: PASS for modified source/test paths.

## J. Safety confirmations

- No approval status or canonical register changed.
- No protocol decision or profile artifact written.
- No configuration, ground truth, reviewers, or authorizations changed.
- No raw media accessed.
- No experiment, inference, training, cache generation, review, promotion, or official evaluation occurred.
- No destructive Git operation occurred.

## Stop condition

Mission 4E.1 stops after technical verification and report creation. It does not finalize D1 in the repository, does not freeze D2, and does not start Mission 5.