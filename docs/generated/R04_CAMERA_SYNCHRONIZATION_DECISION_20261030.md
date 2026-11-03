# D4 — R04 Camera and Synchronization Scope

**Status:** `PROPOSED — NOT APPROVED`

`validate_camera_scope()` supports `single_camera`, `independent_camera`, and `dual_camera`;
dual requires `accepted_sync_events`. Candidate matrix has 12 CALIBRATION_SUPPORTED, 7
PROVISIONAL, and 8 AMBIGUOUS events. Candidate calibration is not acceptance; uncertainty
unknown/provisional is not accepted. T4 is back-clock evidence.

| Mode | Permitted claim | Requirement |
|---|---|---|
| single_camera | front-local descriptive metrics only | no cross-camera T4 claim |
| independent_camera | separate local-clock diagnostics | no fused timing claim |
| dual_camera | aligned T1/T4 metrics | accepted event list + validated calibration + approved GT |

**PROPOSED recommendation:** accept no dual events until researcher scope decision; candidate
CALIBRATION_SUPPORTED events may be considered only after evidence/GT review. No tolerance is
invented.

**Response:** event modes __________; accepted-sync events __________; rationale/reviewer/date __________.
