# D2 M4 T4 End Boundary Verification

**Boundary:** `T4_tail_clearance`  
**Status:** Technically verified; profile remains conditional.

## Definition under v9/v7

T4 is the trailing edge/rear buffer of the final rail vehicle clearing the unified departure roadway boundary plane. It is the primary physical safety-clearance boundary and the end of the M4 interval.

The selected v9/v7 documents define the same operational convention:

- T4 tracking point: rear buffer/diaphragm of final rail vehicle.
- Reference landmark: vendor-stall/departure roadway boundary line on `camera_back.mov`.
- Camera role: back/departure camera.
- T4 is distinct from T3 locomotive-unit clearance.

## Schema field

The Stage-2.1 schema field is:

`boundary_adjudications.T4_tail_clearance`

Under `OBSERVABLE`, the schema requires a finite value and reference camera. Under `CENSORED`, `UNCERTAIN`, or `UNOBSERVABLE_NOT_APPLICABLE`, the value must be null with rationale.

## Evidence requirements

- Human reviewer identifies the final vehicle's rear edge/buffer.
- Reviewer identifies the approved departure boundary landmark.
- Reviewer records camera-local back-camera time, frame evidence, and rationale.
- Reviewer records censoring/uncertainty explicitly when no defensible point exists.

## Clock/R04 behavior

T4 is a back-camera-local timestamp. It does not become a common-clock value merely because a candidate R04 offset exists. A validated R04 scope is required for metrics that combine T4 with a front-camera timestamp (such as v9 T1-to-T4 calculations). M4 uses T4 plus replay-derived `first_blocked`, reducing—but not eliminating for fused replay—the R04 dependency.

## Censoring and uncertainty

- Right-censored T4: recording ends before final-tail clearance; M4 is not point-evaluable.
- Uncertain T4: in-window ambiguity prevents defensible placement; M4 is not point-evaluable.
- Missing/unapproved T4: event is excluded from M4 denominator.

T4 alone is not sufficient for M4: a valid replay must also produce a first-blocked step before T4. If it does not, M5 applies.