# EXP-B7E: Delayed-Timestamp Parameter Recommendation

**Date:** 2026-11-01  
**Mission:** 4E — Researcher Decision Finalization  
**Status:** RECOMMENDATION ONLY — NOT APPROVED  
**Decision identifier:** `EXP-B7E-PARAMETERS`  
**Approval field:** ______________________________

## Approved Mechanism (GOV-B7E-MECHANISM)

The researcher approved on 2026-10-30:
- B7e = delayed frame timestamps.
- Frame content remains unchanged.
- Timestamps are shifted according to explicitly configured parameters.
- Staleness evaluated via `received_timestamp_s - frame_timestamp_s > source_staleness_s`.
- Fails closed when `delay_s` or `target_source` is omitted.

## What Remains Unresolved

- Numerical `delay_s` value or range.
- `target_source` (which camera/audio stream).
- Operational acceptance criteria.

## Important: What is NOT Approved

- `delay_s=2.0` is the `source_staleness_s` software default, NOT a B7e delay.
- `target_source=camera_front` appears in historical reports but is NOT approved.
- No B7e parameter has explicit researcher approval.
- Mission 4D remediation ensures parameter presence alone cannot grant approval.

## Candidate Delay Strategies

### Strategy 1: One fixed delay
- Example: `delay_s=3.0` on one source.
- Tests: Does the system detect a single stale source?
- Confounding: Minimal (one variable changed).
- Simplicity: High.

### Strategy 2: Multiple controlled delay levels
- Example: `delay_s ∈ {2.5, 3.0, 4.0}` on one source.
- Tests: Sensitivity to delay magnitude.
- Confounding: Low (systematic variation).
- Complexity: Moderate.

### Strategy 3: Delay sweep
- Example: `delay_s` from 2.1 to 5.0 in 0.5s steps.
- Tests: Full response curve.
- Confounding: Low but high computational cost.
- Complexity: High.

### Strategy 4: Source-specific delays
- Example: Different delays for camera_1, camera_2, audio_1.
- Tests: Which source's staleness is most critical.
- Confounding: Multiple variables.
- Complexity: High.

## Interaction with Other Parameters

- `source_staleness_s=2.0`: B7e delay MUST exceed this to trigger staleness.
- B7d delivery disorder: Independent mechanism; B7e should not sort frames.
- Clearance dwell (3.0s): Delays > 3.0s may prevent clearance.
- Fault recovery hold (3.0s): System may enter fail-safe if delay is long enough.

## What Constitutes a Successful B7e Test

1. The delayed source is detected as stale (staleness counter increments).
2. The system enters appropriate degraded/fail-safe state.
3. Other sources continue operating normally.
4. No false clearance occurs while delayed source is stale.
5. Recovery occurs when delayed source resumes normal timestamps.

## What Should Remain Constant

- Frame content (only timestamps change).
- All other sources' timing.
- Detection thresholds.
- State machine parameters.
- Evaluation metrics.

## Recommendation

**Strategy 2: Multiple controlled delay levels on a single source.**

**Candidate parameters (require researcher approval):**
- `delay_s`: {2.5, 3.5, 5.0} (all > source_staleness_s=2.0)
- `target_source`: `camera_1` (front camera, approach detection)
- Rationale: Tests staleness detection at increasing severity without excessive complexity.

**Confidence:** LOW (parameters are candidates, not approved)

**This recommendation is NOT an approval. The researcher must specify exact values.**

## Researcher Response

**Delay strategy:** ______________________________  
**delay_s value(s):** ______________________________  
**target_source:** ______________________________  
**Acceptance criteria:** ______________________________  
**Decision-maker:** ______________________________  
**Date (UTC):** ______________________________