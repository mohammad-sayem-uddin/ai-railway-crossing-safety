# GOV-D2 — Evaluation Profile Decision Sheet

**Status:** `PENDING_RESEARCHER_DECISION`  
**Decision identifier:** `GOV-D2-EVALUATION-PROFILE` (historical alias `D2`)  
**Approval field:** ______________________________  
**Decision-maker:** ______________________________  
**Date (UTC):** ______________________________

## Exact question

Which implemented premature-opening profile, if any, shall be bound for official evaluation after approved ground truth exists?

## Alternatives actually present

| Option | Boundary/predicate | Required evidence | Consequences |
|---|---|---|---|
| v9 `t1_entry_to_t4_clearance` | Opening while `T1 <= t < T4` | T1 and T4; compatible clock/sync scope | T1/T4-dependent; censored/uncertain values are not point-evaluable. |
| M4 `first_blocked_to_t4_clearance` | Opening after first blocked tick and before T4 | T4 plus replay-derived `t_blocked` | Avoids requiring T1; no blocked step is handled as M5/never-protected, not M4 success. |
| `t0_first_visible_to_t4_clearance` | Opening in `[T0,T4)` | T0/T4 | Listed in `protocol_choices.py` but not implemented and documented as unsupported; cannot be selected without implementation authorization. |
| `dual_report` | Historical descriptive alternative | Both profiles and explicit reporting rule | Mentioned in historical register prose, but not an available implemented choice in `PROTOCOL_CHOICE_OPTIONS`; not selectable today. |

## Current repository state

- `src/railway_detection/evaluation/protocol_choices.py` has no documented premature-opening default.
- Implemented options are v9 and M4 only; `effective_profile()` raises `PREMATURE_OPENING_DEFINITION_UNDECIDED` until an explicit valid override exists.
- `docs/generated/M4_V9_EVALUATION_PROFILE_COMPARISON_20261030.md` calls M4 a proposed recommendation, not a decision.
- `data/manifests/phase12_protocol_decision.json` is absent.

## Scientific consequences and dependencies

D2 depends on D1 and approved Stage-2.1 T1/T4 semantics. It affects metric denominators, censoring treatment, replay requirements, and interpretation of premature opening. Selecting an unimplemented option would be rejected; implementing a new option requires separate engineering/scientific authorization and tests.

## Required evidence for approval

- Researcher-selected implemented option.
- Rationale for required boundary evidence and censoring.
- Explicit relation to D1 and R04 camera scope.
- Valid governance decision envelope binding the selected profile and hashes.
- Confirmation that official ground truth and split prerequisites will be satisfied first.

## Researcher response

**Selected profile:** ______________________________  
**Rationale:** ____________________________________________________________________  
**Required boundary/clock scope:** _________________________________________________  
**Signature/identity:** __________________________  **Date:** ______________________

Mission 4C does not select a profile.