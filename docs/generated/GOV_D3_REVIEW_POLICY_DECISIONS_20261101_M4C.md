# GOV-D3 — Review Policy Decision Sheet

**Status:** Partially approved, partially pending.  
**Decision identifiers:** `GOV-D3-DESCRIPTIVE-MODE` (approved), `AUTH-EVENT-SPLIT` (pending), D3(a), D3(c) review-policy questions (pending).  
**Approval fields:** ______________________________  
**Decision-maker/date:** ______________________________

## D3(c): exact unresolved decision

The canonical register identifies D3(c) as the **clear-boundary audit mechanism and frequency**: how boundaries marked clear/observable are independently audited or spot-checked before they are treated as final/promotable. It is not the descriptive-only mode, not the event split, and not the second-review trigger. The repository records no selected audit method or frequency.

## D3(a): second-review policy question

The researcher must define when an independent second review is mandatory. Candidate triggers supported by existing workflow documents are:

| Trigger | Meaning | Current implementation |
|---|---|---|
| `UNCERTAIN` boundary | In-window ambiguity prevents a defensible point | Schema accepts state; explicit unresolved status fails promotion. Automatic trigger for every such boundary is **not** implemented. |
| `CENSORED` boundary | Boundary outside recording window | Schema accepts state; automatic second-review trigger is **not** implemented. |
| `UNOBSERVABLE_NOT_APPLICABLE` | Concept does not apply or cannot be observed | No automatic second-review trigger. |
| Reviewer disagreement | Conflicting observations | `DISPUTED` is unresolved; same-reviewer history/batch claims are rejected. |
| Missing/inconsistent evidence | Camera, hash, source, or model-firewall issue | Operational stop/escalation; promotion must fail until resolved. |
| Engine interpretation | T3/T4 single-unit meaning is disputed or protocol-dependent | Engine remains isolated; policy must state whether second review is mandatory. |

Current code enforces identity independence, history integrity, and unresolved-status blocking. It does not choose the scientific trigger or numeric disagreement tolerance.

## D3 status separation

- `GOV-D3-DESCRIPTIVE-MODE`: approved 2026-10-30 for descriptive-only isolation; it does not authorize official evaluation.
- `AUTH-EVENT-SPLIT`: pending; no official split artifact exists.
- D3(a) second-review trigger: pending policy decision.
- D3(c) clear-boundary audit method/frequency: pending policy decision.

## Required evidence

- Exact trigger set and whether triggers apply per-boundary or per-event.
- Distinct reviewer and independence requirements.
- Disagreement escalation/final adjudicator.
- Numeric tolerance decision, if any; no unrelated tolerance may be reused.
- Clear-boundary audit sample/method/frequency.
- Link to Stage-2.1 instructions and promotion gate interpretation.

## Researcher response

**D3(a) triggers:** _________________________________________________________________  
**D3(c) audit method/frequency:** _________________________________________________  
**Disagreement resolution:** ______________________________________________________  
**Tolerance (or explicitly none):** ______________________________________________  
**Signature/identity/date:** _____________________________________________________

Mission 4C does not modify the current safeguards or select these policies.