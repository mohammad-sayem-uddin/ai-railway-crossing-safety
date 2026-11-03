# EXP-ROI-GEOMETRY: Recommendation

**Date:** 2026-11-01  
**Mission:** 4E — Researcher Decision Finalization  
**Status:** RECOMMENDATION ONLY — NOT APPROVED  
**Decision identifier:** `EXP-ROI-GEOMETRY`  
**Approval field:** ______________________________

## Current State

- No approved canonical ROI polygon exists.
- `configs/frozen_experiment_v1.yaml` contains no ROI section.
- `roi_config` is an optional preflight/cache-provenance input.
- `cache_provenance.py` validates shape but not scientific acceptance.
- `EXP-ROI-GEOMETRY` is `PENDING_RESEARCHER_DECISION`.
- No raw media was inspected to derive ROI geometry.

## What ROI Affects

- Detection filtering (detections outside ROI may be excluded).
- Danger-zone boundary definitions (T1, T2, T3, T4 reference physical zones).
- Evaluation metrics (premature opening, missed train depend on zone occupancy).
- Comparability across events (consistent zone definition required).

## Options

### Option A: Manually defined ROI with documented rationale
- Researcher defines polygon coordinates from video inspection.
- Requires media access authorization.
- Transparent and reproducible.
- No calibration equipment needed.

### Option B: Calibration-supported ROI
- Requires physical calibration (camera intrinsics/extrinsics).
- Most rigorous but requires equipment and expertise.
- May not be feasible for existing recordings.

### Option C: Camera-specific ROI with explicit versioning
- Different ROI per camera (front vs. back have different perspectives).
- Version-controlled for reproducibility.
- More complex but more accurate.

### Option D: No ROI-dependent official evaluation until calibration exists
- Most conservative.
- Blocks official evaluation indefinitely if calibration is not feasible.
- Appropriate if ROI cannot be reliably defined.

## Recommendation

**Option A (manually defined ROI) for exploratory work; Option D for official evaluation until calibration evidence exists.**

**Confidence:** MEDIUM

**Rationale:**
1. The operational danger-zone convention (v7.0.0) uses visual landmarks.
2. Manual ROI definition from video inspection is feasible.
3. Official evaluation should not proceed without documented ROI.
4. Camera-specific differences (front vs. back) should be acknowledged.

**This recommendation is NOT an approval. No ROI polygon is created or approved.**

## Researcher Response

**ROI approach:** ______________________________  
**Coordinate system:** ______________________________  
**Per-camera definitions:** ______________________________  
**Calibration requirement:** ______________________________  
**Decision-maker:** ______________________________  
**Date (UTC):** ______________________________