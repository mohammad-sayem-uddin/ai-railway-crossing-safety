# Hazard Model

## Safety-Oriented Simulated Decision Policy

**Scope note:** This hazard model guides software simulation and evaluation. It is not a railway safety case, certification artifact, or proof of physical fail-safe operation.

## 1. Policy invariants

1. Missing detection alone must never authorize simulated gate opening.
2. Opening requires predeclared positive departure evidence and independently observed/defined clearance conditions.
3. Any detected fault behavior is recorded; conservative simulated closure is a policy response, not proof against unobservable failures.
4. Out-of-domain or unresolved multi-train events are not treated as successful normal operation.

## 2. Hazard register

| Hazard | Description/cause | Observable evidence | Unobservable possibility | Expected simulated behavior | Prohibited transition | Evaluation metric |
|---|---|---|---|---|---|---|
| Missed train approach | Train event not indicated before deadline; causes include model FN, occlusion, insufficient coverage. | Ground-truth approach with no qualifying evidence. | Train exists outside view/audio range. | Record missed/late event; do not infer absence. | `IDLE → GATE_OPENING` as response to no evidence. | Event-level missed-train rate; warning lead time. |
| Late warning | Warning/closure indication occurs too close to crossing entry under simulated timing. | Reference entry plus decision timestamp. | Actual physical stopping/actuation dynamics. | Flag late closure; retain conservative state. | Opening while unresolved train event exists. | Late-closure rate; warning-lead distribution. |
| Unnecessary closure | Closure indication without a train event. | No-train evaluable interval. | Unseen train outside reference data. | Record false alarm; do not relabel it as train. | Treating all closures as correct by default. | False alarms/hour; unnecessary-closure rate. |
| Premature opening | Opening before reference tail clearance. | Opening timestamp < observable clearance timestamp. | Clearance boundary itself hidden. | Flag critical simulated violation; transition to fault/conservative policy per spec. | Any opening before clearance guard. | Premature-opening rate. |
| Rear detection failure | Model lacks/mislabels rear evidence. | Reference tail/exit with no rear signal. | Rear not visible due geometry. | Do not open solely from absence; timeout/fault policy applies. | `TRAIN_PRESENT → GATE_OPENING` on rear loss. | Departure-confirmation recall/latency; premature opening. |
| Temporary camera failure | Short source interruption/drop frames. | Availability heartbeat/drop-frame record. | Silent degraded image quality. | Mark unavailable/stale; retain conservative state while unresolved. | Opening because camera became unavailable. | Recovery behavior; fault scenario outcomes. |
| Permanent camera failure | Source unavailable for remaining event. | Persistent unavailable status. | Camera produces plausible but incorrect stale stream. | Enter configured degraded/fault policy; report not physically safe. | Opening based on failed-source silence. | Component-removal results. |
| Audio false positive | Horn/non-train acoustic evidence appears without train. | Annotated vehicle horn/no-train interval. | Unlabeled distant train. | Do not use audio to open; closure behavior follows declared policy. | Audio-only opening authorization. | False alarms/hour; vehicle-horn FP rate. |
| Audio false negative | Train/horn present but acoustic evidence absent. | Reference horn/train event without audio trigger. | Microphone degradation undetected. | Vision/state rules remain independent; record miss. | Declaring no train from absent horn. | Horn-event recall; train-without-horn cases. |
| Stale evidence | Evidence age exceeds valid window. | Timestamp older than configured maximum age. | Incorrect source clock not detected. | Reject/flag evidence; do not use to open/close without policy. | State transition based on expired evidence. | Stale-evidence test pass rate. |
| Out-of-order evidence | Late message/frame arrives after newer one. | Timestamp monotonicity violation. | Clock reset hidden. | Reject or process under documented ordering rule; log it. | Reverting to unsafe/open state due old event. | Ordering regression outcomes. |
| Conflicting cameras | Cameras provide incompatible direction/view evidence. | Simultaneous incompatible qualified evidence. | One source silently wrong. | Apply explicit conflict priority/conservative rule; flag. | Opening while conflict unresolved. | Conflict scenario outcome. |
| Train appears while opening | New approach evidence occurs during `GATE_OPENING`. | Qualified new event before open completion. | New train outside all sensors. | Cancel/reverse simulated opening only if model explicitly supports such action; otherwise enter defined conservative state. | Completion to `IDLE/OPEN` ignoring new train evidence. | New-train-during-opening outcome. |
| Multiple trains | Overlapping or closely spaced passages. | Distinct event labels/evidence. | Train identity ambiguity. | Mark out-of-domain unless policy/data explicitly supports it. | Clearing after first tail while another is unresolved. | Exclusion count or multi-train success metric if added. |
| Stopped train | Train remains in crossing/zone beyond expected timing. | Reference occupancy persists. | Train stopped outside visible zone. | Hold non-opening state; timeout must not infer clearance. | Opening on elapsed time alone. | Stopped-train scenario outcome. |
| Reversing train | Direction changes. | Reference motion reversal. | Brief visual ambiguity. | Mark out-of-domain or invoke explicit separate policy. | Rear/clear transition based on initial direction only. | Exclusion/out-of-domain rate. |
| Partial occlusion | Train/zone partially hidden by vehicle, rain, person, vegetation. | Annotated occlusion tag. | Occlusion unrecognized by source. | Preserve uncertainty; no absence-to-open inference. | Opening after occluded evidence disappears. | Slice metrics; occlusion scenarios. |

## 3. Hazard-model limits

This register cannot identify unobservable physical hazards, validate brakes/barriers/communications, or establish adequate risk reduction. Any implementation must display that limitation in simulation reports.
