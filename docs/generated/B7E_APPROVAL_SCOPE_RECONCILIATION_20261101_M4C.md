# B7d/B7e Approval-Scope Reconciliation

**Status:** Evidence reconciliation; no behavior changed and no B7 experiment executed.

## B7d

**Canonical approval:** `GOV-B7D-DELIVERY-DISORDER` is `APPROVED_BY_RESEARCHER` (2026-10-30). Scope: delivery-layer frame-order disorder; preserve arrival order; downstream collector/Rule 8 observes and rejects out-of-order observations. It does not approve timestamp corruption, stale-frame replay, or arbitrary delivery transformations.

**Implementation binding:** `failure_injector.py`, `simulation/runner.py`, `fusion/collector.py`, and `experiments/runner.py` implement arrival-order preservation and Rule 8 rejection paths. Existing synthetic tests cover this mechanism.

**Scope warning:** `docs/generated/B7D_B7E_PERTURBATION_CONTRACTS_20261030.md` is marked `PROPOSED — NOT APPROVED` and describes alternative disorder meanings. The later canonical register/M2 record explicitly records B7d mechanism approval. The approval applies to delivery-layer disorder only; no additional disorder behavior is approved by implication.

## B7e mechanism

**Canonical approval:** `GOV-B7E-MECHANISM` is `APPROVED_BY_RESEARCHER` (2026-10-30), mechanism only. Scope: delayed frame timestamps with unchanged content; staleness is evaluated from received minus frame timestamp; omitted parameters fail closed.

## B7e parameters

`EXP-B7E-PARAMETERS` is `PENDING_RESEARCHER_DECISION`. The repository does not contain explicit researcher approval for:

- numerical `delay_s` value or sweep/range;
- `target_source`/camera scope;
- acceptance criteria or expected state/rejection behavior.

`delay_s=2.0` appears as `source_staleness_s` software default and in historical/legacy report language; it is not approval of B7e's numerical delay. `target_source=camera_front` appears in a historical authorization/readiness matrix and older execution descriptions, but is not a canonical approved parameter. Canonical source identifiers in current synthetic contracts are exact IDs such as `camera_1`, `camera_2`, and `audio_1`; this does not approve any B7e source.

## Contradictions requiring researcher awareness

1. `preflight_validator.classify_experiment_parameters()` classifies supplied non-synthetic B7e parameters as `researcher_approved` based on presence, despite `EXP-B7E-PARAMETERS` remaining pending. This is an approval-scope mismatch in diagnostic classification; Mission 4C does not alter it.
2. `B7D_B7E_PERTURBATION_CONTRACTS_20261030.md` remains marked proposed while later M2/M4A canonical records record mechanism approvals. The canonical register is the controlling status source.
3. Historical reports describe `delay_s=2.0`/`camera_front`; these are historical/software artifacts, not explicit researcher approval.

## Researcher response

**B7d scope confirmation:** _______________________________________________________  
**B7e mechanism confirmation:** ____________________________________________________  
**B7e delay value/range:** ________________________________________________________  
**B7e target source(s):** _________________________________________________________  
**Acceptance criteria:** __________________________________________________________  
**Signature/identity/date:** ______________________________________________________

No B7e numerical parameter is approved by Mission 4C.