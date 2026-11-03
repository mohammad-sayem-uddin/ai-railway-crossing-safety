# EXP-OPERATING-THRESHOLDS: Recommendation

**Date:** 2026-11-01  
**Mission:** 4E — Researcher Decision Finalization  
**Status:** RECOMMENDATION ONLY — NOT APPROVED  
**Decision identifier:** `EXP-OPERATING-THRESHOLDS`  
**Approval field:** ______________________________

## Current Values and Their Status

| Parameter | Value | Source | Classification |
|---|---:|---|---|
| Vision approach threshold | 0.35 | `frozen_experiment_v1.yaml` | Software/frozen config |
| Vision departure threshold | 0.35 | `frozen_experiment_v1.yaml` | Software/frozen config |
| Audio operating threshold | 0.3700 | `frozen_experiment_v1.yaml` | Calibrated on Val Fold 4 |
| Source staleness | 2.0s | `frozen_experiment_v1.yaml` | Software default |
| Tick interval | 0.2s | `frozen_experiment_v1.yaml` | Software default |
| Confirm frames | 2 | `frozen_experiment_v1.yaml` | Software default |
| Miss tolerance | 2 | `frozen_experiment_v1.yaml` | Software default |
| Warning dwell | 2.0s | `frozen_experiment_v1.yaml` | Software default |
| Gate closing | 3.0s | `frozen_experiment_v1.yaml` | Software default |
| Gate opening | 3.0s | `frozen_experiment_v1.yaml` | Software default |
| Clearance dwell | 3.0s | `frozen_experiment_v1.yaml` | Software default |
| Fault confirmation | 2 | `frozen_experiment_v1.yaml` | Software default |
| Fault recovery hold | 3.0s | `frozen_experiment_v1.yaml` | Software default |
| Fusion weights | Not exposed | N/A | Undocumented |

## Classification Hierarchy

- **Software defaults**: Engineering choices without empirical validation.
- **Frozen configuration**: Locked for reproducibility but not scientifically approved.
- **Historical configuration**: Used in past runs, not current authority.
- **Calibrated values**: Audio 0.3700 was calibrated on validation data.
- **Researcher-approved**: NONE of the above have explicit scientific approval.

## What Has Empirical Validation

- Audio threshold 0.3700: Calibrated on Validation Fold 4 (F1=0.9942).
- Vision threshold 0.35: Used in training/evaluation but not independently validated.
- All timing parameters: Engineering defaults, not empirically optimized.

## What Requires Calibration or Sensitivity Analysis

- Vision approach/departure thresholds: No independent validation.
- Fusion weights: Not even documented in current config.
- Miss tolerance: Arbitrary choice of 2 frames.
- Clearance dwell: Safety parameter but not empirically justified.

## Recommended Decision Process

1. **For exploratory/descriptive runs:** Current frozen values are acceptable as software defaults.
2. **For controlled experiments:** Researcher should approve or explicitly accept current values.
3. **For official evaluation:** Thresholds must be either:
   - Explicitly approved as final scientific constants, OR
   - Subject to a sensitivity analysis protocol.
4. **Fusion weights:** Must be documented and approved before any official fusion evaluation.

## Recommendation

**Preserve current frozen values for exploratory/descriptive work. Require explicit researcher approval or sensitivity analysis before official evaluation.**

**Confidence:** HIGH (for the process recommendation; LOW for any specific value)

**This recommendation is NOT an approval of any numerical value.**

## Researcher Response

**Threshold disposition:** ______________________________  
**Fusion weights:** ______________________________  
**Sensitivity analysis required?** ______________________________  
**Decision-maker:** ______________________________  
**Date (UTC):** ______________________________