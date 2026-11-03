# Mission 4E.3 Report — Definition Reconciliation and Feasibility

**Date:** 2026-11-01 · **Repo:** `/Users/sayemuddin/Desktop/Train_automation` · **Branch:** `main` · **HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (unchanged)
**Type:** documentation reconciliation and feasibility — *not* an implementation mission. The mission name "4E.3" is this report's own label.

> Everything is **proposed**. D1 remains selected-but-unbound, D2 unapproved, the occupancy metric unvalidated, no execution authorized.
> No media was opened. No canonical approval, register, schema, evaluator or readiness gate was modified.

## Scope delivered (the eight requested items)

| # | Request | Delivered in | Result |
|---|---|---|---|
| 1 | Reconcile T1, T2, T4, `T_OCC_START` | `DEFINITION_RECONCILIATION_AND_CROSSING_CONFLICT_AREA_…M4E3.md` §1–2 | T1 and T2 are each worded two ways inside v9/v7; T2's reference line three ways; **`T_OCC_START` exists nowhere in the repo**; "occupancy" has five meanings. Options A/B/C given; A recommended, not decided. |
| 2 | Physical definition of the crossing conflict area, no invented geometry | same, §3 | Defined by two transverse planes (entry E, exit X) via named landmarks only. X is documented; **E is an unconfirmed mirror assumption.** No coordinates/distances. |
| 3 | Same-camera pair observable from non-media docs? | `SAME_CAMERA_FEASIBILITY_…M4E3.md` §1–2 | **Not established.** Front: T4 documented as absent from the front stream. Back: no entry-plane landmark documented; only a camera-dependent frame-entry event. Cross-camera is the sole defined configuration and is blocked by R04. |
| 4 | Left-censoring and missing boundaries | same, §3 | Right-censoring biases retained durations short; left-censoring direction unassessable; effect matrix for occupancy vs M4 vs M5; documentation-derived candidate ceiling 22 → possibly 15 (not a result; actual evaluable today = 0). |
| 5 | Engine-event exclusion | same, §4 (ENG-1…8) | Excluded from M4, M5 and pooled occupancy; cohort-qualified id required; optional N=1 descriptive row. Flags a conflict with `EXPERIMENT_DESIGN_FINAL.md` §8.3. |
| 6 | Replacement wording for the T1-based premature-opening text | `PROPOSED_REPLACEMENT_WORDING_…M4E3.md` §A (+ B for T1/T2/CCA) | Side-by-side current vs proposed for v9 §5.2, INV-3, §18 and GT §2.2. **Not applied** (applying changes the hashes). |
| 7 | Correct the M4 incomplete-replay classification | `M4_INCOMPLETE_REPLAY_CLASSIFICATION_CORRECTION_…M4E3.md`; 4E.2 M4/M5/reporting docs revised | See "Correction" below. |
| 8 | Leave canonical items unchanged | — | Verified (see "Integrity"). |

## Correction to my own 4E.2 work (item 7)

4E.2 said only that a replay ending before T4 reads as "not premature". That was incomplete:
- **Current code also labels a short or empty replay with no blocked step as M5 `never_protected=True`**, asserting protection failure about an unobserved tail.
- A violation *already witnessed* before the replay ends is definite and must not be discarded.
- Both directions of current-code error are safety-relevant: understated premature-opening rate; overstated never-protected count.

Corrected 6-row classification: empty → NOT_EVALUABLE (`replay_empty`); witnessed violation → premature (any coverage); blocked/no violation/covered → not premature; blocked/no violation/**not covered** → NOT_EVALUABLE (`replay_ended_before_T4`); no blocked/covered → M5; no blocked/**not covered** → NOT_EVALUABLE, **M5 not asserted**. For covered replays it is identical to the existing function (exhaustive check, > 200 cases). `metrics.py` is unchanged.

## New findings beyond the eight items

1. v9's own table puts T1 at entry to the *road* danger zone, while its operational landmark (the frog line) is upstream of the roadway.
2. The legacy AI annotator words T2 against a "**transverse lens plane**" (`batch_multimodal_annotator.py:201`), so *candidate* T2 values may be referenced to a camera plane, not the roadway. Candidates must not seed adjudication.
3. `EXPERIMENT_DESIGN_FINAL.md` (untracked) claims to supersede v9 for endpoints and includes engine in M4/M5; its authority relative to the selected v9/v7 is unsettled (G-D1-08, G-M4-11).
4. `evaluate_run` treats a **bare engine id** (no cohort) as a train event (G-M4-10; pinned by test).
5. Documents disagree on the R04-supported subset (11 vs 12) and on T0 left-censoring (20/23 vs 23/23) — neither changes a conclusion here, but both show documentation counts are non-authoritative.

## Tests

File: `tests/unit/test_mission4e2_m4_occupancy_contract.py` (4E.2 file, extended with Part 3). Synthetic only; no media, GT, cache, checkpoint or inference.
```
cd /Users/sayemuddin/Desktop/Train_automation && .venv/bin/python -m pytest tests/unit/test_mission4e2_m4_occupancy_contract.py -p no:cacheprovider -q
```
Result: **68 passed** (57 from 4E.2 + 11 new: six classification branches, no-tolerance boundary, exhaustive covered-replay equivalence, denominator partition, three current-behaviour characterizations).
Not run: the repository's wider suites; `ruff` (not installed).

## (A) Researcher decisions
Unchanged from 4E.2 (D1 v9/v7; both outcomes; M4; M5 separate; occupancy = physical onset → T4). The pasted recommendation for this mission (items 1–8) was treated as the instruction.

## (B) Technical findings
As above, plus the 4E.2 findings that stand: protocol files uncommitted; `metrics.py` untracked; no physical-onset field; R04 unresolved; 0 approved GT.

## (C) Proposed definitions (all unapproved)
CCA and `T_OCC_START` alias; options A/B/C; ENG-1…8; corrected incomplete-replay classification; replacement wording blocks A1–A3, B1–B4.

## (D) Formal approvals still pending
D1 binding (with *re-pinned* hashes if any wording is adopted) · choice of onset option A/B/C · T2 wording · entry-plane E statement · M4-supersedes-POR wording · authority ranking of `EXPERIMENT_DESIGN_FINAL.md` vs v9/v7 · engine population · acceptance of the corrected incomplete-replay rule (then a separate code change) · occupancy contract · R04 scope · Stage-2.1 review/promotion · official split.

## (E) Execution authorizations still pending
EVAL-AUTH · replay/cache/inference · media inspection or a geometry-sheet step to settle same-camera visibility · timing pilot · any experiment.

## Integrity

- HEAD `d4db94d…` unchanged; 0 staged; the same 19 modified tracked files as at the start; no stage/commit/push/reset/clean/restore.
- New this mission: five documents in `docs/generated/` (reconciliation, feasibility, M4 correction, replacement wording, this report). Edited in place: my own 4E.2 test file and my own 4E.2 proposal documents (M4 contract, M5 definition, reporting spec, occupancy contract, gap register, checklist).
- Not touched: either protocol file, any register/manifest/governance/authorization/readiness/config/schema/ground-truth file, any source module.

## Questions for the researcher
1. Option **A** (T2 under reconciled wording), **B** (T1) or **C** (new boundary) for `T_OCC_START`?
2. Do you confirm the entry plane E is the approach-side mirror of the documented exit plane X?
3. Does the cohort contain both travel directions, and is "front = entry side" fixed for every event?
4. Which governs metric definitions: `EXPERIMENT_DESIGN_FINAL.md` or the selected v9/v7? (Decides engine inclusion in M4/M5.)
5. Do you want the corrected incomplete-replay rule implemented as a separate, approved code change?
