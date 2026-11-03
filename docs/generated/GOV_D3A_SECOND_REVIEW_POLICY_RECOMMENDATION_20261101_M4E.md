# GOV-D3(a): Second-Review Policy Recommendation

**Date:** 2026-11-01  
**Mission:** 4E — Researcher Decision Finalization  
**Status:** RECOMMENDATION ONLY — NOT APPROVED  
**Decision identifiers:** D3(a) second-review trigger  
**Approval field:** ______________________________

## Current Implementation

The existing code enforces:
- `NEEDS_SECOND_REVIEW` and `DISPUTED` statuses block promotion.
- Same-reviewer second reviews are rejected (schema + batch).
- `second_review_of` cannot self-reference.
- History claiming second review requires distinct actors.

The code does NOT automatically trigger second review for every CENSORED or UNCERTAIN boundary. That trigger policy is the pending D3(a) decision.

## Policy Alternatives

### Option A: Second review only for explicit disagreement
- Trigger: Reviewer marks DISPUTED or NEEDS_SECOND_REVIEW.
- Workload: Minimal (only when reviewer self-reports uncertainty).
- Risk: Reviewer may not recognize their own bias.
- Scientific reliability: Low for systematic error detection.

### Option B: Second review for disagreement + UNCERTAIN/CENSORED
- Trigger: Any boundary marked UNCERTAIN or CENSORED, plus explicit disagreement.
- Workload: Moderate (20/23 events have censoring).
- Risk: May overwhelm with 20+ second reviews.
- Scientific reliability: Good for boundary cases.

### Option C: Second review for ALL non-observable states
- Trigger: Any boundary not OBSERVABLE.
- Workload: High (nearly all events have at least one non-observable boundary).
- Risk: Reviewer fatigue, diminishing returns.
- Scientific reliability: Highest but impractical for 27 events.

### Option D: Risk-based policy with explicit mandatory triggers
- Trigger: Defined list of conditions requiring second review.
- Workload: Controlled by trigger selection.
- Risk: Requires careful trigger definition.
- Scientific reliability: Targeted and defensible.

## Recommended Mandatory Triggers (Option D)

1. **Explicit DISPUTED or NEEDS_SECOND_REVIEW status** (already enforced).
2. **Any UNCERTAIN boundary** (reviewer acknowledges ambiguity).
3. **Engine-event T3/T4 interpretation** (special semantics).
4. **Conflicting camera evidence** (front and back disagree on observable state).
5. **Missing or inconsistent media hashes** (integrity concern).
6. **Boundary correction from proposal** (reviewer changed a candidate value).

## NOT Recommended as Mandatory Triggers

- CENSORED boundaries alone (censoring is a recording limitation, not reviewer uncertainty).
- UNOBSERVABLE_NOT_APPLICABLE (concept does not apply; no ambiguity).
- All OBSERVABLE boundaries (would require second review for everything).

## Impact on 27-Event Dataset

- 20/23 train events are left-censored at T0 (would NOT trigger under recommendation).
- ~5-8 events may have UNCERTAIN boundaries (would trigger).
- 1 engine event (would trigger for T3/T4 interpretation).
- 3 no-train events (unlikely to trigger unless evidence is ambiguous).

## Recommendation

**Option D — Risk-based policy with the 6 mandatory triggers listed above.**

**Confidence:** MEDIUM

**Rationale:**
1. Censoring is a recording property, not a reviewer judgment error.
2. UNCERTAIN boundaries represent genuine reviewer doubt.
3. Engine events have special semantics requiring verification.
4. Camera conflicts indicate evidence ambiguity.
5. Hash mismatches indicate integrity concerns.
6. Corrections from proposals indicate the reviewer exercised independent judgment.

**This recommendation is NOT an approval. The researcher must select and record the policy.**

## Researcher Response

**Chosen policy:** ______________________________  
**Mandatory triggers:** ______________________________  
**Decision-maker:** ______________________________  
**Date (UTC):** ______________________________