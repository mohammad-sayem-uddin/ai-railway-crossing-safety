# Proposed Replacement Wording — T1-based Premature Opening, T1/T2 and the Conflict Area

> **PROPOSED TEXT ONLY — NOT APPLIED — NOT APPROVED — NOT AUTHORIZATION.**
> Neither protocol file was edited. Applying any of this changes the file's SHA-256 and therefore **invalidates the hash pin** proposed in
> `D1_V9_V7_PROPOSED_BINDING_NOT_ACTIVATED_20261101_M4E2.md` (`7c183b32…` / `d100c1e6…`). If the researcher adopts any block, edit first, re-hash, then bind.
> Line numbers refer to the working-tree files at inspection (v9: 435 lines; v7: 847 lines).

Order below: A (premature opening) answers the request; B (T1/T2/CCA) is the minimum companion change, because M4's end boundary and the occupancy metric rely on the same terms.

---

## A. Premature opening — replace the T1-based text with M4

### A1. v9 §5.2 (lines 122–124) and GT v7 §2.2 (lines 121–123)

**Current v9 §5.2**
> - **Physical Hazard Occupancy:** The crossing danger zone is actively blocked during: t ∈ [T1, T4]
> - **Premature Opening Rate (POR):** Any gate opening commanded while t < T4 (and t ≥ T1).
>   - *Diagnostic Isolation:* Gate opening between T3 and T4 directly measures detector dropout on trailing cars after locomotive departs. Events with unobservable T4 are excluded from the denominator.

**Proposed**
> - **Approach-to-clearance hazard interval:** The approach hazard begins at T1 and the crossing is clear at T4: t ∈ [T1, T4]. This interval is descriptive. The crossing conflict area is physically obstructed only from the entry of the train's leading end into that area until T4 (see §5.4).
> - **Premature Opening (M4) and Premature Opening Rate (POR).** For a train event with an approved, observable T4 and a replay whose timeline reaches T4, let t_blocked be the timestamp of the first retained replay step at which the simulated barrier blocks the passage. The event is a **premature opening** if any retained step strictly between t_blocked and T4 has the passage unblocked or a gate state of OPENING or OPEN. **POR** = premature events ÷ M4-evaluable events. M4 is a per-event yes/no result; it is not a duration.
>   - *Excluded from the POR denominator:* events with a missing, censored or uncertain T4; events whose replay ends before T4 without a witnessed premature opening; events with no blocked step before T4.
>   - *Never Protected (M5):* events whose replay reaches T4 with no blocked step before T4 are reported separately as **Never Protected**, never as "not premature".
>   - *Diagnostic Isolation:* A premature opening that begins between T3 and T4 on the same timeline indicates detector dropout on trailing cars after the locomotive has departed.
>   - *Clocks:* t_blocked is on the replay timeline and T4 on the back-camera clock; the comparison is made only on the back-stream timeline or on a fused timeline for which R04 has been accepted for that event.

**What changes in meaning:** (i) the start moves from T1 (a ground-truth boundary on the *front* clock) to the replay-derived first blocked step; (ii) *a gate that never closed* is no longer a premature opening but an M5 / Missed-Train outcome; (iii) the measurement no longer needs T1 and so no longer crosses camera clocks on a back-only replay; (iv) POR becomes a replay-conditional measure, with the denominator shrinking by every M5 event.

### A2. v9 §16 INV-3 (line 271)

**Current:** "INV-3 (Zero Premature Clearance): Gate shall not open while train occupies crossing danger zone (t ∈ [T1, T4])."

**Proposed:**
> **INV-3 (Zero Premature Clearance — requirement):** Once the barrier has blocked the passage, the gate shall not open or begin opening before T4. *Verification:* the M4 predicate on replay traces and on synthetic harness traces. Timeliness of the first closure is a separate requirement, verified by Missed Train Rate and Never Protected (M5), not by INV-3.

### A3. v9 §18 (lines 290–294)

| Bullet | Current | Proposed |
|---|---|---|
| POR | "Percentage of evaluable events where gate opened while t < T4 (and t ≥ T1). (Goal: 0.0 %)" | "Percentage of M4-evaluable events with a premature opening (M4, §5.2). (Goal: 0.0 %)" |
| (new) | — | "**Never Protected (M5):** count of train events whose replay reaches T4 with no blocked step before T4, reported beside POR; not part of its denominator." |
| Excess Closed Duration | "Gate closed time minus physical occupancy time (T4 − T1)" | "Gate closed time minus approach-to-clearance time (T4 − T1)" *(rename only; removes the clash with the conflict-area occupancy duration)* |
| (new, descriptive, ground-truth-only) | — | "**Crossing-conflict-area occupancy duration:** T4 − T_OCC_START, in seconds, reported separately; never combined with POR or M5." *(only if the researcher approves that metric and its onset boundary)* |

### A4. Wording elsewhere that mirrors the T1-based form (for a consistency pass, not drafted here)
v9 lines 205, 399–400 (and §18 line 290) ("0 MTR, 0 POR"; "E1/E3 show premature openings") and the A/B text in `FINAL_ABLATION_MATRIX.md` use POR as a name only; the name can stay if A1 is adopted.

---

## B. T1, T2 and the crossing conflict area

### B1. T1 — v9 §5.1 table row (line 110); GT v7 §2.1 row (line 107)

**Current:** "Earliest frame locomotive front bumper crosses into road danger zone."
**Proposed:** "Earliest frame the leading edge of the locomotive reaches the approach danger-zone line (turnout switch frog casting / pedestrian approach corridor line on `camera_front.mov`), upstream of the roadway boundary."
*Effect:* none operationally — §5.4(2) and GT §2.4(2) already use the frog line; the table is brought into line with them.

### B2. T2 — v9 §5.1 row (line 111), GT v7 §2.1 row (line 108), v9 §5.4(3) (line 145), GT v7 §2.4(2) (line 156)

**Current (two conflicting forms):** "Earliest frame locomotive fully occupies road danger zone." / "Locomotive front pilot crosses the transverse camera plane / roadway boundary line on `camera_front.mov`, commencing physical road lane blockage."

**Proposed (single form):**
> **T2 — Crossing Occupancy Start.** Earliest frame at which the leading end of the first rail vehicle (pilot / cowcatcher / front bumper) crosses the **entry plane** of the crossing conflict area, identified by the roadway boundary line on `camera_front.mov`. From this frame the crossing is physically obstructed by rolling stock. The reviewer records in the rationale which visible line was used. A camera's own lens or image plane is never used as the reference line.

*Effect:* withdraws "fully occupies" (a later instant) and the "camera plane / lens plane" reference.

### B3. New paragraph for GT v7 §2.4(1) / v9 §5.4 — crossing conflict area
> **Crossing conflict area (CCA).** The stretch of railway alignment that lies within the road-and-pedestrian crossing corridor, bounded along the direction of travel by two transverse planes perpendicular to the track: the **entry plane** (approach-side edge of the corridor) and the **exit plane** (the Level-Crossing Departure Roadway Boundary Plane, marked by the vendor-stall clearance line on `camera_back.mov`). The train occupies the CCA while any part of any rail vehicle lies between the two planes. This is an operational convention based on visible landmarks; no coordinates, distances or survey are implied.

*Open point for the researcher:* the entry plane is the approach-side mirror of the documented exit plane — an assumption, not yet stated in either protocol.

### B4. Occupancy duration — only if approved
> **Crossing-conflict-area occupancy duration** = T4 − T2, in seconds, same-camera or R04-accepted cross-camera only; events with a missing, censored or uncertain T2 or T4 are `not_evaluable` and excluded from point estimates.

---

## C. Impact checklist if the researcher adopts any block

| Item | Consequence |
|---|---|
| Hash pin | Both file hashes change; re-pin after editing |
| Candidate proposals / AI annotator | The legacy generator (`src/railway_detection/annotation/batch_multimodal_annotator.py:201`) words T2 as "passes front camera **transverse lens plane** / roadway occupancy line"; candidate T2 values may therefore be referenced to a lens plane. They are unapproved candidates and must not seed T2 adjudication |
| Reviewer guidance | `review_reporter.py` and the Stage-2.1 reviewer guide quote the existing T2 wording and should be checked after any change (not edited here) |
| Authority | `EXPERIMENT_DESIGN_FINAL.md` (untracked) claims to supersede v9 for endpoints; resolve which document governs before editing either |
| M4 profile | Choice key `premature_opening_window = first_blocked_to_t4_clearance` is unchanged by A |
