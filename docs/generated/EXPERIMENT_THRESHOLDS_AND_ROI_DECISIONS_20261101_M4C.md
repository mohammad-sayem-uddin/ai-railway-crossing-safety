# Experimental Thresholds and ROI Decision Sheet

**Decision domains:** `EXP-OPERATING-THRESHOLDS`, `EXP-ROI-GEOMETRY`  
**Status:** Thresholds implemented but not scientifically approved; ROI pending researcher sign-off.  
**Approval fields:** ______________________________

## Operating thresholds

| Parameter | Live frozen software value | Other evidence | Current status | Scientific consequence |
|---|---:|---|---|---|
| Vision approach confidence | `0.35` | `configs/frozen_experiment_v1.yaml`; `decision_policy_v1.yaml` | Software/frozen exploratory value; not final scientific approval | Changes approach detections, false alarms, warning timing, and sensitivity. |
| Vision departure confidence | `0.35` | Same | Software/frozen exploratory value; not final scientific approval | Changes clearance confirmation and premature-opening outcomes. |
| Audio operating threshold | `0.3700` | Same; Audio V3 contract | Software/frozen exploratory value; not final scientific approval | Changes audio support and false alarms. |
| `source_staleness_s` | `2.0` s | Frozen config and decision policy | Software safety default; not B7e delay approval | Changes stale-source state transitions; must not be treated as `delay_s=2.0`. |
| Tick/confirmation/dwell values | `tick=0.2`, confirm `2`, warning/closing/opening/clearance values in frozen config | Frozen config | Engineering defaults unless separately approved | Changes state-machine timing and comparability. |
| Fusion weights (`w_v1`, `w_v2`, `w_a`) | No verified live explicit weight binding | Preflight register title mentions weights, but current config does not expose a verified set | Unresolved/undocumented | Prevents reproducible scientific interpretation of fusion weighting. |

The canonical register classifies `EXP-OPERATING-THRESHOLDS` as `IMPLEMENTED_BUT_NOT_SCIENTIFICALLY_APPROVED`. Do not convert software defaults into researcher-approved parameters.

## ROI and calibration geometry

- `configs/frozen_experiment_v1.yaml` contains no formal approved ROI polygon/calibration section.
- `roi_config` is an optional preflight/cache-provenance input; absence is a warning in exploratory mode and a blocker in official mode.
- `cache_provenance.py` validates supplied shape/identity but does not establish scientific acceptance.
- `EXP-ROI-GEOMETRY` is `PENDING_RESEARCHER_DECISION`.

## Alternatives

1. Preserve current defaults for synthetic/exploratory diagnostics only.
2. Researcher approves fixed per-camera ROI geometry and calibrated thresholds after authorized evidence collection.
3. Researcher explicitly defines a threshold/ROI sensitivity protocol before any official claim.

No alternative is selected here.

## Required evidence and response

Provide calibration evidence, per-camera polygon coordinates, coordinate convention, threshold rationale/validation set, fusion weights, and exact configuration hash. Bind them to the appropriate governance/manifest artifact.

**Approved threshold set:** ________________________________________________________  
**Approved ROI/calibration artifact:** ______________________________________________  
**Validation evidence:** ___________________________________________________________  
**Signature/identity/date:** ______________________________________________________