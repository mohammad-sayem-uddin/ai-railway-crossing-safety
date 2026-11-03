# D2 M4 Start Boundary Verification

**Profile:** `first_blocked_to_t4_clearance`  
**Status:** Conditional technical verification; not frozen or approved.

## Exact implementation

`src/railway_detection/evaluation/metrics.py::m4_premature_opening()` defines `t_blocked` as:

```python
t_blocked = next(
    (s.timestamp_s for s in sim_result.steps if s.is_passage_blocked),
    None,
)
```

Therefore, `first_blocked` is:

- A replay-derived timestamp.
- The timestamp of the first retained `SimulationStep` whose `is_passage_blocked` is true.
- Not a ground-truth field.
- Not T1, T2, T3, or T4.
- Not manually annotated.

`SimulationStep.is_passage_blocked` is produced by the physical gate model during replay. The step list excludes Rule 8/Rule 10 rejected frames, so rejected frames cannot become a first-blocked boundary.

## Evidence required

- A valid replay timeline with strictly increasing timestamps.
- A gate-model state that actually reaches `is_passage_blocked=True`.
- A valid approved T4 ground-truth boundary.
- A selected M4 profile binding.

No media evidence is needed to establish `first_blocked` itself; it is system-side replay evidence. Media/ground truth is required for the end boundary and event eligibility.

## Clock and R04 dependency

`first_blocked` is on the replay timeline. It does not require front/back clock synchronization by itself. If replay fuses multiple camera streams, the replay's camera scope still requires R04 acceptance. For a single/back-camera replay, M4 avoids using T1 front-camera time.

## Missing/uncertain start behavior

If no step is blocked before T4, `m4_premature_opening()` returns `(None, True)`: M4 is not evaluable and `never_protected=True` (M5). It does not substitute T1, T0, or another boundary.

## Technical conclusion

The M4 start boundary is technically well-defined in code as the first blocked replay step. It is not a human ground-truth boundary and should not be added to Stage-2.1 records. Final profile freezing still requires the researcher to accept this replay-side definition and its M5 treatment.