# ROI Approval Integrity Audit

**Date:** 2026-11-01  
**Mission:** 4D — Scientific Governance Integrity Remediation  
**Status:** AUDITED AND REMEDIATED (via threshold/ROI fallback fix)

## Findings

1. **No approved canonical ROI polygon exists.** `configs/frozen_experiment_v1.yaml` contains no ROI section. `EXP-ROI-GEOMETRY` is `PENDING_RESEARCHER_DECISION` in the canonical register.

2. **`roi_config` is an optional preflight/cache-provenance input.** When absent:
   - Exploratory mode: `ROI_GEOMETRY_UNSPECIFIED` warning (non-blocking).
   - Official mode: `ROI_GEOMETRY_UNSPECIFIED` blocker.

3. **Shape validation does not equal scientific approval.** `cache_provenance.py` validates the structural shape of a supplied ROI (bounding box/polygon format), but this does not establish that the geometry is scientifically accepted or researcher-approved.

4. **Pre-remediation defect:** The `eff_roi` fallback to `d2_approved` meant that passing `d2_approved=True` (evaluation profile approval) would implicitly classify ROI as approved. This has been remediated: ROI approval now requires the explicit `roi_geometry_approved=True` flag only.

5. **No exploratory ROI can become official ROI without authorization.** The preflight validator treats ROI as unresolved unless `roi_geometry_approved=True` is explicitly passed.

6. **Historical ROI values cannot be mistaken for approved calibration.** The `is_historical=True` path returns a single `historical_configuration` classification, preventing any parameter-level approval inference.

## Verification

- No code path converts a valid polygon shape into `CONFIG_CLASS_RESEARCHER_APPROVED` without the explicit flag.
- No code path converts exploratory ROI usage into official ROI approval.
- The readiness gate (`run_experiment_preflight`) correctly reports `ROI_GEOMETRY_UNSPECIFIED` when ROI is absent and `eff_roi` is False.

## What Was NOT Changed

- No ROI geometry was created, modified, or approved.
- No canonical ROI artifact was written.
- No camera calibration was performed.
