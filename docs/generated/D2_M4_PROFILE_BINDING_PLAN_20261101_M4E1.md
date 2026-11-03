# D2 M4 Conditional Profile Binding Plan

**Status:** Non-executing plan; no approval artifact written.

## Required future binding

The researcher-selected profile must eventually be recorded through the validated protocol decision envelope:

`data/manifests/phase12_protocol_decision.json`

with the implemented choice:

`premature_opening_window: first_blocked_to_t4_clearance`

## Validation steps

1. Confirm D1 v9/v7 selection is formally recorded first.
2. Confirm exact M4 identifier is one of `IMPLEMENTED_OPTIONS`.
3. Bind selected protocol/profile hashes.
4. Confirm M4 boundary contract: first retained blocked replay step to approved T4.
5. Confirm M5 never-protected behavior and denominator treatment.
6. Confirm R04 scope for any replay that fuses camera streams.
7. Confirm Stage-2.1 records and T4 evidence exist before official use.
8. Run read-only readiness checks.

## If technical clarification is required

No schema change is currently necessary to represent M4: `first_blocked` is replay-side and T4 is already a canonical Stage-2.1 field. A future implementation change would only be needed if the researcher requires a persisted first-blocked audit field or a new aggregate metric; that would require separate authorization and tests.

## Current blockers

- No protocol decision envelope.
- No evaluation profile binding.
- No Stage-2.1 records/promotion receipt.
- No R04 scope decision.
- No official split/manifest/EVAL-AUTH.

No plan step was executed by Mission 4E.1.