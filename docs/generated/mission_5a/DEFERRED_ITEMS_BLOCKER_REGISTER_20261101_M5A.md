# Deferred-Decision and Blocker Register — Mission 5A

> Each item is **deferred, not invented**. "Unblock" says what would unblock it; it is not an authorization.

| ID | Deferred item (RD) | Why blocked | What would unblock it | Who | Blocks |
|---|---|---|---|---|---|
| BR-01 | Exact physical entry landmark (RD-006) | only the exit plane is documented; no landmark was invented; "mirrors the exit plane" is unverified | researcher's written site statement **or** an authorized geometry step | researcher | T2, `T_OCC_START`, occupancy |
| BR-02 | Per-event train direction (RD-010) | candidate metadata is AI-generated and unapproved | direction verified per event in an authorized review | researcher + reviewer | direction-dependent camera roles |
| BR-03 | Full occupancy duration (RD-018, 019) | no valid same-camera pair; cross-camera alignment not approved; acoustic offsets must not shift GT | BR-01 + a same-camera landmark convention **or** approved R04 alignment | researcher | occupancy reporting |
| BR-04 | Human confirmation that no-train clips are train-free (RD-025) | no authorized human confirmation exists | authorized viewing by a named reviewer | researcher | N1 "train-free" claim |
| BR-05 | R04 official scope (RD-026) | candidates only; 11 vs 12 unresolved; 20/23 unmet | researcher-authored scope decision with accepted events | researcher | any official dual-camera claim |
| BR-06 | B7e numeric delay/source/acceptance (RD-034) | never specified | researcher-specified values | researcher | B7e experiments |
| BR-07 | Review timestamp tolerance (RD-012) | needs review evidence | pilot/second-review disagreement evidence | researcher | uncertainty reporting; `T4±u` |
| BR-08 | Review-duration floor (RD-046) | needs pilot timing | pilot timings | researcher | promotion-time plausibility check |
| BR-09 | Real-data descriptive pathway (RD-039) | descriptive mode accepts synthetic evidence only | governance approval + implementation of a real-evidence path | researcher | any real descriptive results |
| BR-10 | Audit percentage (RD-044) | deliberately not fixed | risk criteria agreed by researcher | researcher | clear-boundary audit |
| BR-11 | Pilot execution (RD-047) | no pilot authorization; prerequisites missing | bound D1, reviewer identities, media-access and pilot authorizations | researcher | Stage-2.1 start |
| BR-12 | Media access (RD-050) | prohibited | separate future mission with explicit authorization | researcher | all human review |
| BR-13 | Official split | not pursued (descriptive full cohort) | n/a unless the research design changes | researcher | official evaluation |
| BR-14 | EVAL-AUTH | requires all prerequisites | all of the above | researcher | official evaluation |
| BR-15 | Stage-2.1 human review / GT promotion | no approved records; no receipt | pilot → review → promotion authorizations | researcher | any GT-dependent metric |
| BR-16 | Real-data evaluation, experiments, caches | not authorized | EVAL-AUTH / execution authorizations; execution-environment verification | researcher | all results |
| BR-17 | Reviewer identities beyond the single allowlisted one | none supplied | researcher's explicit identity instruction | researcher | second review, audit |
| BR-18 | Formal D1/D2/D4/thresholds/ROI/B7e/M4-M5 approvals; ratification of 2026-10-30 items | no researcher-authored artifacts | researcher attestations (see GD, RT) | researcher | all downstream gates |
| BR-19 | Wiring of the lead-in screen into the official runner | provenance location for `min_block_latency_s` undecided | decide where the value + source is recorded (e.g., evaluation manifest) | engineering after decision | MTR reporting in official path |
| BR-20 | `no_steps_in_protection_interval` confirmation | implementation choice beyond the six-case table | researcher keeps or reverts | researcher | M4 on very sparse replays |
