# B7e Approval Classification Remediation

**Date:** 2026-11-01  
**Mission:** 4D — Scientific Governance Integrity Remediation  
**Status:** REMEDIATED

## Defect Identified

In `src/railway_detection/experiments/preflight_validator.py`, the function `classify_experiment_parameters()` classified B7e injector parameters as `CONFIG_CLASS_RESEARCHER_APPROVED` whenever `delay_s` and `target_source` were present in the parameters dict, regardless of whether any researcher approval existed.

The defective logic (lines 845-853, pre-remediation):

```python
b7e_class = (
    CONFIG_CLASS_SYNTHETIC_TEST
    if (is_synthetic_test and has_b7e_params)
    else (
        CONFIG_CLASS_RESEARCHER_APPROVED
        if (has_b7e_params and not is_synthetic_test)
        else CONFIG_CLASS_UNRESOLVED
    )
)
```

This violated the governance invariant: **parameter presence alone must never grant approval**. The canonical register entry `EXP-B7E-PARAMETERS` has status `PENDING_RESEARCHER_DECISION`, yet the classification logic could label parameters as approved based solely on their existence.

## Remediation Applied

1. Added a new explicit parameter `b7e_parameters_approved: bool = False` to `classify_experiment_parameters()`.
2. Changed the classification condition to require `b7e_parameters_approved=True` in addition to parameter presence:

```python
b7e_class = (
    CONFIG_CLASS_SYNTHETIC_TEST
    if (is_synthetic_test and has_b7e_params)
    else (
        CONFIG_CLASS_RESEARCHER_APPROVED
        if (has_b7e_params and not is_synthetic_test and b7e_parameters_approved)
        else CONFIG_CLASS_UNRESOLVED
    )
)
```

3. Added the same parameter to `run_experiment_preflight()` and propagated it to the classification call.
4. Updated the notes string to distinguish "supplied (approval pending)" from "supplied and researcher-approved."

## Separation of Mechanism vs. Parameters

The approved B7e **mechanism** (`GOV-B7E-MECHANISM`, approved 2026-10-30) remains distinct from the pending **parameters** (`EXP-B7E-PARAMETERS`). The mechanism approval covers:
- Delayed frame timestamps with unchanged content.
- Staleness evaluation via `received_timestamp_s - frame_timestamp_s > source_staleness_s`.
- Fail-closed behavior when parameters are omitted.

The parameters decision covers:
- Numerical `delay_s` value or sweep/range.
- `target_source` / camera scope.
- Operational acceptance criteria.

## Tests Added

15 new synthetic tests in `tests/unit/test_mission4d_governance_integrity.py`:

| Test | Validates |
|---|---|
| `test_b7e_params_present_without_approval_remain_unresolved` | Presence ≠ approval |
| `test_b7e_params_present_with_pending_decision_remain_unresolved` | Pending decision ≠ approval |
| `test_b7e_params_synthetic_test_classification` | Synthetic gets synthetic class |
| `test_b7e_params_historical_classification` | Historical gets historical class |
| `test_b7e_params_with_explicit_approval_get_researcher_approved` | Explicit approval works |
| `test_b7e_params_missing_remain_unresolved` | Missing params stay unresolved |
| `test_b7e_preflight_reports_pending_decision_blocker` | Preflight reports blocker |

## What Was NOT Changed

- The approved B7e mechanism scope.
- The canonical decision register entry statuses.
- Any numerical parameter values.
- Any authoritative schema.
- Any gate behavior (fail-closed preserved).