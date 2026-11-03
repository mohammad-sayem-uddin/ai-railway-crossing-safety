# GOV-D4: R04 Camera Synchronization Scope Recommendation

**Date:** 2026-11-01  
**Mission:** 4E — Researcher Decision Finalization  
**Status:** RECOMMENDATION ONLY — NOT APPROVED  
**Decision identifier:** `GOV-D4-R04-SYNCHRONIZATION`  
**Approval field:** ______________________________

## Current State

| Artifact | Count | Status |
|---|---:|---|
| Candidate manifest CALIBRATION_SUPPORTED | 12 | Candidate only |
| Authorized exploratory config | 11 | Authorized 2026-10-13 |
| Discrepancy event | 1 (`train_events/event_010`) | Promoted after config freeze |
| PROVISIONAL | 7 | Not eligible for dual-camera |
| AMBIGUOUS | 8 | Not eligible for dual-camera |

## The 12 Supported Events

`train_events/event_001`, `event_002`, `event_005`, `event_006`, `event_007`, `event_009`, `event_010`, `event_011`, `event_012`, `event_013`, `event_014`, `event_017`

## The 11 Exploratory Events

Same as above minus `train_events/event_010`.

## Root Cause of Discrepancy

`train_events/event_010` was promoted to CALIBRATION_SUPPORTED via visual landmark corroboration (reviewer: Raihan_Kabir_Rahu, delta=0.000s, tolerance=0.10s) AFTER the exploratory config was authorized on 2026-10-13. The config was never updated.

## Decision Alternatives

### Option A: Preserve original 11-event exploratory scope
- No change to existing authorization.
- event_010 remains excluded from dual-camera exploratory runs.
- Simplest; no new authorization needed.

### Option B: Approve revised 12-event exploratory scope
- Requires new authorization record.
- event_010 joins the dual-camera subset.
- Corroboration evidence exists (visual landmark, verified).

### Option C: Keep 11-event exploratory + separate future official scope
- Exploratory remains unchanged.
- Official scope decision deferred until more evidence exists.
- Most conservative.

### Option D: Restrict R04-dependent conclusions to supported subset
- Any dual-camera claim limited to CALIBRATION_SUPPORTED events.
- PROVISIONAL/AMBIGUOUS events use single-camera or independent-clock mode.
- Applies regardless of exploratory scope size.

## Evidence Quality Assessment

- CALIBRATION_SUPPORTED: Acoustic GCC-PHAT with PSR≥2.0, SNR≥15.0, window stability ≤0.2s.
- Visual landmark corroboration exists for some events (not all 12).
- Acoustic-lag reproducibility is NOT hardware synchronization proof.
- Uncertainty for SUPPORTED events: ±0.05s (geometric jitter bound only).
- PROVISIONAL/AMBIGUOUS: Uncertainty unknown.

## Recommendation

**Option C + D combined: Keep 11-event exploratory scope; restrict dual-camera claims to supported subset; defer official scope.**

**Confidence:** MEDIUM

**Rationale:**
1. The existing 11-event authorization is valid and should not be silently expanded.
2. event_010's promotion is evidence but not authorization.
3. Official scope requires a separate decision with full evidence review.
4. Restricting conclusions to supported events is scientifically conservative.
5. PROVISIONAL/AMBIGUOUS events should use independent-camera mode.

**This recommendation is NOT an approval.**

## Researcher Response

**Chosen scope option:** ______________________________  
**Accepted sync events (if any):** ______________________________  
**Event modes:** ______________________________  
**Evidence/acceptance rule:** ______________________________  
**Decision-maker:** ______________________________  
**Date (UTC):** ______________________________