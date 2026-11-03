# DRAFT — NOT APPROVED — NOT AUTHORIZATION

## R04 Camera Scope and Synchronization Decision Template

**Decision ID:** R04-SCOPE-20261027
**Status:** DRAFT — NOT APPROVED — NOT AUTHORIZATION
**Decision-maker:** ____________________
**Decision date (UTC):** ____________________

### Per-event scope table

| Cohort-qualified event ID | Mode (`single_camera` / `independent_camera` / `dual_camera`) | Accepted sync? | Evidence reference | Decision rationale |
|---|---|---:|---|---|
| ____________________ | ____________________ | [ ] yes [ ] no | ____________________ | ____________________ |

### Contract constraints

- `dual_camera` requires the event in `accepted_sync_events` and validated calibration.
- `independent_camera` means separate local clocks; it is not fused timing.
- `single_camera` uses front-local time and does not make T4/back-clock metrics evaluable.
- Candidate calibration status is evidence, not researcher acceptance.
- Missing/non-finite/uncertain offsets cannot default to zero.
- Synchronization tolerance must come from an approved existing contract; it must not be
  invented in this template.

Selected event set and rationale: _________________________________
T4 clock policy: _________________________________________________
Metric eligibility consequences: _________________________________
Accepted-sync evidence and uncertainty basis: _____________________

**Do not write this template to `data/manifests/phase12_r04_scope_decision.json`.**
