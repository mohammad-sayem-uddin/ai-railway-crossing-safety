# Threshold Approval Integrity Audit

**Date:** 2026-11-01  
**Mission:** 4D — Scientific Governance Integrity Remediation  
**Status:** AUDITED AND REMEDIATED

## Defect Identified

In `classify_experiment_parameters()` and `run_experiment_preflight()`, the effective threshold approval (`eff_thresholds`) and ROI approval (`eff_roi`) were computed with fallback logic that conflated historical D1/D2 protocol flags with experimental parameter approval:

```python
# DEFECTIVE (pre-remediation):
eff_thresholds = d1_approved if operating_thresholds_approved is None else operating_thresholds_approved
eff_roi = d2_approved if roi_geometry_approved is None else roi_geometry_approved
```

This meant that a caller passing `d1_approved=True` (intending protocol authority approval) would implicitly classify operating thresholds as `researcher_approved`, and `d2_approved=True` would implicitly classify ROI geometry as approved. This violated the Mission 4A separation of `GOV-D1-PROTOCOL-AUTHORITY` from `EXP-OPERATING-THRESHOLDS` and `GOV-D2-EVALUATION-PROFILE` from `EXP-ROI-GEOMETRY`.

## Remediation Applied

Changed the fallback to `False` (no implicit inheritance):

```python
# REMEDIATED:
eff_thresholds = operating_thresholds_approved if operating_thresholds_approved is not None else False
eff_roi = roi_geometry_approved if roi_geometry_approved is not None else False
```

This ensures:
- Software defaults remain defaults.
- Frozen configuration remains configuration.
- Historical values remain historical.
- Only explicit `operating_thresholds_approved=True` or `roi_geometry_approved=True` can create researcher-approved status.
- Diagnostic preflight cannot grant scientific approval or EVAL-AUTH.

## Thresholds Audited

| Parameter | Live Frozen Value | Classification | Approval Status |
|---|---:|---|---|
| Vision approach confidence | 0.35 | Software/frozen | Not scientifically approved |
| Vision departure confidence | 0.35 | Software/frozen | Not scientifically approved |
| Audio operating threshold | 0.3700 | Software/frozen | Not scientifically approved |
| Source staleness (`source_staleness_s`) | 2.0s | Software safety default | Not B7e delay approval |
| Tick interval | 0.2s | Engineering default | Not scientifically approved |
| Confirm frames | 2 | Engineering default | Not scientifically approved |
| Miss tolerance frames | 2 | Engineering default | Not scientifically approved |
| Warning dwell | 2.0s | Engineering default | Not scientifically approved |
| Gate closing | 3.0s | Engineering default | Not scientifically approved |
| Gate opening | 3.0s | Engineering default | Not scientifically approved |
| Clearance dwell | 3.0s | Engineering default | Not scientifically approved |
| Fusion weights (`w_v1`, `w_v2`, `w_a`) | Not exposed in frozen config | Undocumented | Unresolved |

## Code Paths Verified

No code path was found that treats:
- Presence of a threshold value as approval.
- Frozen configuration as scientific approval.
- Historical configuration as approval.
- Successful preflight as approval.
- Configuration validity as approval.

The only path to `CONFIG_CLASS_RESEARCHER_APPROVED` for thresholds is now the explicit `operating_thresholds_approved=True` flag.

## Tests Added

| Test | Validates |
|---|---|
| `test_d1_approved_does_not_implicitly_grant_threshold_approval` | d1 ≠ threshold approval |
| `test_d2_approved_does_not_implicitly_grant_roi_approval` | d2 ≠ ROI approval |
| `test_explicit_threshold_approval_still_works` | Explicit flag works |
| `test_explicit_roi_approval_still_works` | Explicit flag works |
| `test_no_approval_flags_all_unresolved` | Default is unresolved |
| `test_preflight_never_grants_eval_auth` | Preflight is diagnostic-only |

## What Was NOT Changed

- No numerical threshold values were modified.
- No frozen configuration was altered.
- No canonical decision register status was changed.