# Definition Reconciliation — T1 / T2 / T4 / `T_OCC_START` and the Crossing Conflict Area

> **PROPOSED — NOT APPROVED — NOT AUTHORIZATION.** Documentation-only reconciliation (Mission 4E.3, a feasibility/definition mission).
> No protocol, schema, evaluator, register, readiness gate or approval was changed. No media was opened. No coordinates, distances or
> pixel positions are asserted anywhere below. Wording marked **[proposed]** is a candidate for the researcher, not a rule.

Sources read (all text): `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` v7.0.0 (working tree, SHA-256 `d100c1e6…49ecf4`), `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`
v9.0.0 (working tree, `7c183b32…8734c`), `docs/EXPERIMENT_DESIGN_FINAL.md` v1.0, `docs/DATASET_ANNOTATION_QUALITY_AUDIT.md`,
`docs/R04_ALL_EVENT_CALIBRATION_INVESTIGATION.md`, `docs/PHASE11_GROUND_TRUTH_PROTOCOL.md`, `src/railway_detection/annotation/schemas.py`.

## 1. Terminology as actually used (findings)

### 1.1 Boundary wording, with the internal conflicts

| Term | Where / exact wording | Camera | Observation |
|---|---|---|---|
| **T1** Danger Zone Entry | v9 §5.1 table: "front bumper crosses **into road danger zone**". v9 §5.4(2) / GT §2.4(2): "front cowcatcher reaches the **approach danger-zone line** (turnout switch frog / pedestrian approach corridor line)" | front | The **table** places T1 at entry to the *road* danger zone; the **operational landmark** is an *approach-side* line upstream of the roadway. These are two different places. |
| **T2** Crossing Occupancy Start | v9 §5.1 / GT §2.1: "locomotive **fully occupies** the road danger zone". v9 §5.4(3) / GT §2.4(2): "front pilot crosses the **transverse camera plane / roadway boundary line** … commencing physical road lane blockage". R04 investigation rows (candidate sync pairs): "crosses **front lens plane** (T2)", "front **roadway occupancy line**", "front roadway line". Dataset audit: "**Roadway line**" | front (§2.4); "Front / Back" (§2.1 table) | **Three different reference lines** ("camera plane / lens plane", "roadway boundary line", "roadway occupancy line") and **two different instants** (leading end *enters* vs. body *fully occupies*). |
| **T3** | trailing coupler / rear buffer of lead motive unit clears the unified departure roadway boundary plane (vendor-stall line) | back | consistent |
| **T4** | rear buffer / diaphragm of the final vehicle clears the **identical** departure roadway boundary plane | back | consistent; v9 table says "exits danger zone" (same sense) |
| **`T_OCC_START`** | **Does not exist.** `grep` over `docs/ src/ tests/ configs/ scripts/` finds no such identifier or schema field (the only substring hits are `fault_occurred`). | — | A *proposed label* only. |

### 1.2 The word "occupancy" currently carries five meanings

| Id | Sense | Source |
|---|---|---|
| O1 | T2 "Crossing Occupancy Start" (road lane blockage begins / body fully inside) | GT §2.1, §2.4; v9 §5.1, §5.4 |
| O2 | "Physical Hazard Occupancy" = `t ∈ [T1, T4]` | v9 §5.2; GT §2.2 |
| O3 | "physical occupancy time (`T4 − T1`)" as the Excess Closed Duration baseline | v9 §18 |
| O4 | "ground-truth occupancy" (RQ1) and M6 "Occupancy coverage" over `[T1, T4]` | `EXPERIMENT_DESIGN_FINAL.md` §1, §8.3 |
| O5 | Researcher's "full crossing occupancy": physical crossing-blocked onset → T4 | Mission 4E.2 decision |

O2–O4 are `T1`-anchored; O1 and O5 are about the road being physically blocked. Using the single word for all five is the root of the confusion.

### 1.3 Authority conflict that affects this reconciliation

`EXPERIMENT_DESIGN_FINAL.md` (**untracked** in git; "Governing specification … subject to `OPEN_DECISIONS_AND_BLOCKERS.md`") states it *supersedes* v9 "for endpoints, taxonomy, timing policy, statistics and approval mechanics" while keeping T0–T4 definitions "in force". The researcher selected v9/v7 as D1. Which document governs *metric* definitions is therefore **not settled** (new gap G-D1-08). This document reconciles terms; it does not rank the two.

## 2. Proposed reconciliation [proposed]

### 2.1 Keep three physically distinct things apart

| Name | Physical meaning | Anchor |
|---|---|---|
| **Approach hazard onset** — `T1` | Train's leading end reaches the approach-side danger-zone line (turnout frog / pedestrian approach corridor line). The train is **not yet** on the roadway. | front |
| **Crossing-conflict-area entry** — proposed alias `T_OCC_START` | Train's leading end first crosses the **entry plane E** of the crossing conflict area (§3). The road is physically blocked from here. | front (only documented camera) |
| **Crossing-conflict-area exit** — `T4` | Rear buffer of the final vehicle crosses the **exit plane X**. | back |

### 2.2 What `T_OCC_START` should and should not be

- **It must be a prose alias, not a new field.** Until the researcher approves a schema change, `T_OCC_START` must not appear as a key in any record, validator or evaluator.
- **Proposed mapping, three options for the researcher:**

| Option | `T_OCC_START` ≡ | Needs | Consequence |
|---|---|---|---|
| **A (recommended, not binding)** | **`T2` under the §2.4 wording**, with T2's reference line **declared to be entry plane E** and the "fully occupies" and "camera/lens plane" wordings withdrawn | researcher resolves C1/C5; no schema change | Uses an already-supported boundary. Smallest change. Candidate T2 ≈ T1 + 0.7–0.9 s in the dataset audit (unapproved), so A vs B shifts D by well under 1 s per candidate event — comparable to the 0.5 s default tolerance in the design doc — not a negligible choice in an uncertainty budget. |
| B | `T1` | researcher states that the approach danger zone *is* the conflict area | The new duration collapses to v9's existing "physical occupancy time `T4 − T1`" (O3); no new metric, and "blocked" would be claimed while the train is still upstream of the roadway. |
| C | a new boundary | schema + protocol change, new landmark convention | Not available without approvals; this mission adds nothing. |

- **It must never be** `first_blocked` (replay-derived), `T0`, `T3`, `T_scene_clear`, a horn time, a detection time, or a back-camera frame-entry time (§4 of the feasibility document explains why).

### 2.3 Proposed disambiguation of the word "occupancy"

| Concept | Proposed fixed name |
|---|---|
| O1 (T2) | keep the canonical key `T2_crossing_occupancy_start`; gloss it "leading end enters the crossing conflict area" |
| O2 / O4 | "approach-to-clearance hazard interval `[T1, T4]`" |
| O3 | "approach-to-clearance time (`T4 − T1`)" |
| O5 | **"crossing-conflict-area occupancy duration"**, `D_cca = T4 − T_OCC_START`, seconds |

(Names are proposals; none is binding. The earlier working id `full_crossing_occupancy_s` can be kept as the report column name.)

## 3. Physical definition of the crossing conflict area (CCA) — landmark-defined only

**Definition [proposed].** The *crossing conflict area* is the stretch of railway alignment that lies within the road-and-pedestrian crossing corridor — the stretch road vehicles and pedestrians traverse when using the level crossing. Along the direction of train travel it is bounded by two **transverse planes perpendicular to the track**:

- **Exit plane X** — *documented.* GT v7 §2.4(1): the "Level-Crossing Departure Roadway Boundary Plane — the transverse plane where the vehicular road and pedestrian crossing corridor terminates on the departure side of the tracks", identified in the footage by the vendor-stall clearance line on `camera_back.mov`. T3 and T4 use this **same** plane.
- **Entry plane E** — *not documented as a named plane.* The protocols name only a "roadway boundary line" / "roadway occupancy line" on `camera_front.mov` (T2). That E is the approach-side edge of the same corridor — the mirror of X — is an **assumption this document makes visible but cannot verify**; it needs the researcher's statement.

**The train occupies the CCA** at time *t* if any part of any rail vehicle lies between E and X.
- **Onset:** the **leading end** (pilot / cowcatcher / front bumper) crosses E.
- **End:** the **trailing end** (rear buffer / diaphragm of the final vehicle) crosses X (= T4).
- "Full" in "full crossing occupancy" therefore means *the whole interval during which the CCA is physically obstructed by rolling stock*, **not** "the train is entirely inside".

**What the CCA is not:** the approach zone upstream of E (where T1's frog line lies); a camera lens plane (it depends on where the camera stands, not on the site); the gate-arm region; any region defined by detection, audio, ROI polygons, or system state.

**What is deliberately not specified (nothing invented):** coordinates, pixel positions, distances, CCA length, number of tracks or lanes, speed. R03 (site survey) is retired by v9/v7; the convention is *operational*, "not an independently surveyed physical geodetic ground truth" (GT §2.4(1)). Consequently the CCA cannot be converted to metres, and train speed cannot be inferred.

**Conditions the definition inherits (open):**
1. *Travel direction.* The schema allows `left_to_right` and `right_to_left`. The protocols name the front camera "Approach" and the back camera "Departure" as fixed roles. Whether the cohort contains both directions — and whether E/X then swap per event — is **not stated in any document read**. If directions differ, "front = entry side" cannot be assumed per event.
2. *Single site.* All events are `crossing_A`; the CCA is a property of that one site.
3. *Mirror assumption* for E (above).
4. *Observability* of E and X on a given recording is a human-review matter (Stage-2.1) and is untested here.

## 4. Proposed replacement wording for T2 [proposed — not applied]

The full replacement text, with current-versus-proposed side by side, is in `PROPOSED_REPLACEMENT_WORDING_20261101_M4E3.md`.

## 5. Not claimed

No wording here is adopted. D1 remains selected-but-unbound. The occupancy metric remains unvalidated. No event has been adjudicated.
