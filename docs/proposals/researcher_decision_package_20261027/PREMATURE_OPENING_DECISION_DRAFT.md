# DRAFT — NOT APPROVED — NOT AUTHORIZATION

## Premature-Opening Definition Decision Template

**Decision ID:** PREMATURE-OPENING-20261027
**Status:** DRAFT — NOT APPROVED — NOT AUTHORIZATION
**Decision-maker:** ____________________
**Decision date (UTC):** ____________________

### Options

- [ ] `t1_entry_to_t4_clearance` (Protocol v9): opening command while `T1 <= t < T4`.
  Requires T1 on front clock and T4 on back clock on an accepted common timeline.
- [ ] `first_blocked_to_t4_clearance` (M4): opening or blocked-to-unblocked behavior in
  `(t_blocked, T4)`, paired with M5 never-protected handling. Requires implementation/profile
  binding before official use.

### Evidence and limitations

- T1 is annotated on the front clock; T4 is annotated on the back clock.
- Neither option is evaluable on front-camera-only replay.
- Independent-camera replay cannot evaluate v9 cross-clock behavior without a fused timeline.
- Missing, censored, or uncertain boundaries are excluded/not-evaluable, never imputed.
- Current code implements v9 predicate; `protocol_choices.py` intentionally has no default.

Selected option: ____________________
Rationale: ______________________________________________________
Historical-comparability implications: ___________________________
Required implementation/test work: ______________________________

**This template does not modify M4, M5, or any protocol/metric implementation.**
