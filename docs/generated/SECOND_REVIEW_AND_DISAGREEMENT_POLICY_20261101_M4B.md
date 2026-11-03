# Second-Review and Disagreement Policy

**Date:** 2026-11-01  
**Status:** Safeguard documentation and synthetic validation; not a selection of pending scientific policy.

## Implemented controls

- The allowlist loader fails closed on missing, malformed, empty, duplicate, blocklisted, revoked, or inactive-overlapping identities.
- Reviewer metadata and history actors are checked against the blocklist; the review builder checks authorization before assembly; promotion checks it again.
- `second_review_of` cannot reference the same review ID.
- A history claiming a second review or resolution must contain distinct actors.
- Batch promotion emits `BATCH_SAME_REVIEWER_SECOND_REVIEW` for same-reviewer linked records.
- Synthetic IDs and temporary/synthetic media paths are blocked from canonical promotion when the guard is enabled.
- Duration is derived from timestamps and must meet the 30.0-second plausibility floor.
- `NEEDS_SECOND_REVIEW` and `DISPUTED` are unresolved and fail promotion; no automated averaging, tolerance, majority vote, or tie-breaker exists.
- History must be chronological, append-only, and non-duplicate.

## Pending researcher policy

The implementation does not decide when every `CENSORED` or `UNCERTAIN` boundary requires a second review. It blocks an explicitly unresolved `NEEDS_SECOND_REVIEW`/`DISPUTED` record and same-reviewer claims, but an `APPROVED` record with a non-observable boundary is not automatically routed solely by that state. D3(a) remains pending.

The researcher must decide which states/events trigger second review, whether all CENSORED/UNCERTAIN cases trigger it, clear-case auditing (D3(c)), escalation/final adjudicator, and any numeric tolerance. No unrelated system-resolution tolerance is silently reused.

## Operational escalation until policy is bound

Treat explicit `NEEDS_SECOND_REVIEW`, `DISPUTED`, conflicting observations, missing/ambiguous camera evidence, inconsistent hashes, model-firewall incidents, reviewer-independence concerns, and researcher-selected D3(a) cases as mandatory escalation. A second reviewer must be distinct, authorized, and independently protected from model outputs.

Never delete or rewrite the first review to hide disagreement. Link a correction, retain prior content/hash, append actor/time/rationale, and require human resolution.

## Synthetic tests

The M4B suite covers same-reviewer rejection, distinct-reviewer acceptance, revoked/blocklisted/duplicate identities, unresolved status, conflicting boundary state/value, duplicate history, duplicate event/cohort identity, synthetic reviewer/session/record rejection, missing queue event, and tracker inconsistency. These tests use temporary fixtures and are not human-review evidence.

## Conclusion

Controls are fail-closed for explicit unresolved disagreement and same-reviewer claims. Production use remains incomplete until D3(a), D3(c), and the disagreement process are researcher-bound. Mission 4B did not weaken or invent these rules.