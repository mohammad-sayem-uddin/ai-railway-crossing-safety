# GOV-D4 — R04 Synchronization Decision Sheet

**Status:** `PENDING_RESEARCHER_DECISION`  
**Decision identifier:** `GOV-D4-R04-SYNCHRONIZATION` (historical alias `D4`)  
**Approval field:** ______________________________  
**Decision-maker/date:** ______________________________

## Exact question

Which events and camera mode may support cross-camera timing claims, under what calibration evidence and uncertainty/acceptance criteria?

## Existing evidence

- Candidate manifest: `data/manifests/camera_sync_offsets_candidate.yaml`, status `CANDIDATE_UNVALIDATED_DO_NOT_MERGE`.
- Candidate matrix counts: 12 `CALIBRATION_SUPPORTED`, 7 `PROVISIONAL`, 8 `AMBIGUOUS`.
- The separately authorized exploratory v1.1 configuration contains 11 train events, not 12. `governance.documented_r04_candidates()` detects this mismatch (`consistent: false`). This is a metadata contradiction, not permission to reconcile it automatically.
- `src/railway_detection/data/sync_calibration.py` defines deterministic candidate classification; it explicitly says acoustic-lag evidence is not hardware synchronization proof.
- `SyncAligner` requires explicit offset and uncertainty; omitted values cannot silently become zero.
- `research_contracts.validate_camera_scope()` permits `single_camera`, `independent_camera`, and `dual_camera`; dual-camera requires an accepted-sync event set supplied by a researcher decision artifact.

## Scope alternatives

| Mode | Permitted conclusion | Requirement |
|---|---|---|
| `single_camera` | Camera-local descriptive metrics; no cross-camera T4 claim | No merged clock. |
| `independent_camera` | Separate local-clock diagnostics | No fused timing claim. |
| `dual_camera` | Aligned T1/T4 metrics | Approved event modes, accepted-sync set, validated calibration, approved GT. |
| Restricted exploratory subset | Candidate-only exploratory dual-camera analysis | Separate explicit authorization; never full-cohort or official evidence. |

## Required acceptance criteria

The researcher must specify: accepted event keys; `event_modes`; accepted offsets and uncertainty semantics; corroboration standard (visual landmark/site survey/etc.); whether negative controls/engine are included; how T1/T4 camera-local values are mapped; and reporting restrictions. A valid `phase12-r04-scope-decision/1` envelope is required. Candidate labels alone do not satisfy acceptance.

## Risks of proceeding without D4

Cross-camera clocks may be incomparable; T1/T4 latency and premature-opening metrics can be shifted or misdenominated; candidate synchronization can be mistaken for accepted calibration. Official dual-camera execution is blocked by `R04_SCOPE_DECISION_MISSING`.

## Researcher response

**Event modes:** ___________________________________________________________________  
**Accepted-sync events:** __________________________________________________________  
**Evidence/acceptance rule:** _____________________________________________________  
**Uncertainty/reporting rule:** ___________________________________________________  
**Signature/identity/date:** _____________________________________________________

No synchronization scope is accepted by Mission 4C.