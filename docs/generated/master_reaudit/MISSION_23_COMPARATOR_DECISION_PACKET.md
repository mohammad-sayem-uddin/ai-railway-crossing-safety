# Mission 23 — Back-camera comparator decision packet

Prepared 2026-11-05, America/New_York. Decision remains **M22-COMP-MAPPING**. This packet supplies technical context for one complete researcher-authored mapping; it adopts no command cell and enables neither the comparator nor back audio.

The unchanged M19-METH-04 direction recorded in Mission 20 selects a separately labeled memoryless `B0_back_stateless` comparator while keeping `B0_back` primary and stateful. It does not define the per-frame command table. The Mission 22 technical contract already fixes admission, reset, exact native clock, actuator separation and deterministic error handling. None is reopened here.

## Exact input representation and current sources

Define `m = F + 2*S + 4*R`, where each bit is presence of at least one qualified detection in the single explicitly identified back-camera vision record at its exact local timestamp. The tuple below is **(F,S,R)**, not a binary rendering of the integer. Detector class IDs are independently mapped: config class0→front→F, class1→rear→R, class2→side→S. Multiple detections of the same class do not create extra bits; simultaneous classes are retained as a set. Box iteration order and highest-confidence-box selection cannot break ties.

`EvidenceRecord` supplies source ID, modality, availability, timestamp and detections. `configs/frozen_experiment_v1.yaml` supplies the three class names, approach/departure thresholds0.35 and evaluation cadence0.2s. `fusion/rules.py` uses `>= threshold`; both approach and departure predicates include side and the legacy generic label train. The generic train label is outside the three-class frozen mapping and needs an explicit unknown-label disposition. Class names do not establish physical travel direction or a roadway-entry landmark.

| Integer | Tuple F,S,R | Present classes / producer IDs | Current approach predicate | Current departure predicate | Stateless command |
|---:|---|---|---|---|---|
| 0 | 0,0,0 | valid empty record | false | false | UNADOPTED |
| 1 | 1,0,0 | front /0 | true | false | UNADOPTED |
| 2 | 0,1,0 | side /2 | true | true | UNADOPTED |
| 3 | 1,1,0 | front+side /0+2 | true | true | UNADOPTED |
| 4 | 0,0,1 | rear /1 | false | true | UNADOPTED |
| 5 | 1,0,1 | front+rear /0+1 | true | true | UNADOPTED |
| 6 | 0,1,1 | side+rear /2+1 | true | true | UNADOPTED |
| 7 | 1,1,1 | front+side+rear /0+2+1 | true | true | UNADOPTED |

These predicates describe current code; they are not a command mapping. In particular, side alone activates both predicates. Conflicts therefore include masks2,3,5,6,7, rather than only frames containing front and rear together.

## Existing transition behavior

The frozen engine is stateful: IDLE approach evidence starts confirmation; two qualifying ticks permit warning, then the2s warning and 3s closing stages advance. TRAIN_PRESENT and CROSSING_OCCUPIED retain closure; departure evidence advances through TRAIN_DEPARTING and REAR_CONFIRMED. In REAR_CONFIRMED, approach evidence takes precedence and resets clearance; otherwise stale/missing departure evidence aborts clearance, audio may postpone dwell, and 3s clear dwell permits CROSSING_CLEAR. Duplicate and decreasing timestamps are rejected separately. Rules4–6 cover sensor loss/degradation and Rule9 covers recovery.

Consequently the same mask can have different commands in different historical states. Rear-only at initial IDLE is not the same event as rear-only following observed departure. Empty valid vision is healthy negative evidence, but is not a universal clearance certificate. Copying counters, dwell timers or previous perceptual states into the proposed comparator would violate its memoryless decision definition.

## Remaining availability and interpretation cells

The one adopted mapping must also specify each of these, separately from the eight valid masks:

- Missing record, unavailable record, failed decode or missing stream: distinguish from valid empty mask0.
- Stale evidence: distinguish native source time/age from current master time; do not silently refresh old PTS. The existing source policy's2s reference is context, not an adopted new comparator rule.
- Degraded evidence, recovering source, unknown health or negative/inconsistent age: state which inputs are admissible and which are unavailable. Importing upstream history must be disclosed; no hidden comparator counter is allowed.
- Unknown class (including generic train), invalid/nonfinite confidence or incomplete producer identity: never coerce to a three-bit known mask without an adopted rule.
- Simultaneous approach/departure classes and side's dual role: specify every conflicting mask explicitly, without arbitrary detector-order priority.

Until those cells and all eight commands exist, the current result remains `UNAVAILABLE: COMPARATOR_MAPPING_NOT_ADOPTED`. Unavailable evidence cannot become zero M4/M5, RAISE or a fabricated HOLD observation.

## Options and consequences

**Recommended process option A:** retain the frozen primary and have the researcher supply/adopt one complete versioned table plus availability rules and producer/config references. This is the remaining scientific definition, not fourteen new permissions or a request to reselect cameras/metrics. No values are filled here. Engineering can then implement that exact definition and test all cells.

**Option B:** explicitly defer comparator activation while continuing the minimum frozen-model descriptive benchmark. Current unavailable results and the absence of comparator claims persist. Permanently removing the already selected condition would need an explicit scope amendment rather than an engineering default.

For consideration when authoring option A, the plausible interpretation families have different consequences:

| Interpretation family | Technical/scientific consequence; no cells adopted |
|---|---|
| Approach/presence dominates conflicting evidence | Produces more lowering/holding episodes; may suppress premature-opening witnesses while increasing blockage. It does not prove improved safety or calibrate the primary controller. |
| Departure dominates conflicts | Can raise in the presence of approach/side evidence and change M4 witnesses. Treating a rear class as complete passage needs an explicit scientific justification. |
| Empty frame permits release | Uses instantaneous absence as a release rule; detection gaps and genuinely missing frames must remain distinct. This differs from the frozen positive-clearance/dwell policy. |
| Ambiguous/unknown evidence unavailable | Preserves evidential limits and lowers evaluable denominators; it cannot be reported as success. |
| Ambiguous evidence maps to HOLD | The decision may be memoryless, but physical angle still depends on earlier actuation. HOLD is not a clear/closed physical state and cannot be substituted for missing evidence. |

These are consequences of possible interpretations, not recommended railway-control rules or a proposed adopted table. A memoryless comparator cannot be behaviorally equivalent to `decision_policy_v1`'s historical confirmation, dwell, fault and recovery semantics. It may be compared as a separate declared scientific condition only; it cannot replace or modify that policy. Audio supplies no mask bit and cannot independently initiate closure or clearance. Back-audio remains deferred.

## Exact post-adoption engineering

Record the genuine source statement, exact eight command cells, all availability/unknown-label cases and producer/config versions under the existing decision ID. Create a versioned pure mapping; separate its admission cursor from actuator history. Wire only the explicit back-camera comparator condition in the constructed orchestrator. Test all eight masks, conflict permutations, every availability case, repeat/no-history invariance, equality at thresholds, duplicate/decreasing/native time, reset, exact B command-to-angle behavior and missing-value denominators. Retain the primary policy and all historical outputs unchanged. Real data/model access and empirical comparison still require their separate valid operation evidence.

## Inspected references

- `configs/frozen_experiment_v1.yaml`, raw text SHA256 `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a`.
- `configs/decision_policy_v1.yaml`, raw text SHA256 `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575`. Its0.1s timing example is distinct from frozen0.2s evaluation; no cadence amendment is made.
- `src/railway_detection/fusion/rules.py`, SHA256 `3e11bdb9644c1d0e43d6a42c23487b38301e5cee9d3247c0f1d9a0b2db3d5e18`.
- `src/railway_detection/fusion/decision_engine.py`, SHA256 `3f5e3521e5b0b78e4ea2090855712cd36c0d91420ec125c09001382b1f0fcf40`.
- Mission 20 register M19-METH-04; Mission 22 comparator technical contract; current `descriptive_constructed.py` refusal of `B0_back_stateless` and `B2_back`.

These are source/config/document hashes. No checkpoint bytes, checkpoint hash verification, model inference or source observations were accessed.
