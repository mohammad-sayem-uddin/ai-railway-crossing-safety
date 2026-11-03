# GOV-D3(c): Clear-Boundary Audit Recommendation

**Date:** 2026-11-01  
**Mission:** 4E — Researcher Decision Finalization  
**Status:** RECOMMENDATION ONLY — NOT APPROVED  
**Decision identifier:** D3(c) clear-boundary audit mechanism/frequency  
**Approval field:** ______________________________

## Exact Meaning of D3(c)

D3(c) requires a documented audit mechanism for boundaries marked as "clear" (OBSERVABLE). It addresses the question: "How do we verify that boundaries the reviewer marked as observable are actually correct?"

This is distinct from:
- D3(a): When a second review is triggered.
- Descriptive-only mode: The approved evaluation isolation.
- Event split: The calibration vs. evaluation partition.

## Policy Alternatives

### Option A: No routine clear-boundary audit
- Benefit: Minimal workload.
- Risk: Systematic errors in OBSERVABLE boundaries go undetected.
- Suitability: Only appropriate if inter-reviewer agreement is very high.

### Option B: Random sample audit (fixed percentage)
- Benefit: Statistical coverage without full workload.
- Risk: May miss specific problematic events.
- Candidate percentage: 20-30% of OBSERVABLE boundaries (requires researcher approval).
- Suitability: Good for fixed-site descriptive research.

### Option C: Full independent second review of all boundaries
- Benefit: Maximum reliability.
- Risk: Doubles reviewer workload.
- Suitability: Impractical for 27 events × 6 boundaries.

### Option D: Risk-based sampling
- Benefit: Targets high-risk boundaries.
- Risk: Requires defining risk criteria.
- Suitability: Good balance for limited resources.

## Recommendation

**Option B — Random sample audit at 25% of OBSERVABLE boundaries.**

**Confidence:** LOW (percentage is a candidate, not approved)

**Rationale:**
1. For a 27-event fixed-site descriptive study, full second review is impractical.
2. No audit leaves systematic errors undetected.
3. 25% provides reasonable coverage (~40 boundaries out of ~162 total).
4. Random selection prevents reviewer from predicting which boundaries will be audited.
5. The audit should be conducted by a DIFFERENT reviewer than the original.

**Candidate parameters (require researcher approval):**
- Audit percentage: 25% (candidate)
- Selection method: Random (seeded for reproducibility)
- Auditor: Must be distinct from original reviewer
- Discrepancy threshold: Any disagreement triggers full second review of that event

**This recommendation is NOT an approval. The percentage and mechanism require explicit researcher sign-off.**

## Researcher Response

**Audit mechanism:** ______________________________  
**Audit percentage/frequency:** ______________________________  
**Selection method:** ______________________________  
**Discrepancy handling:** ______________________________  
**Decision-maker:** ______________________________  
**Date (UTC):** ______________________________