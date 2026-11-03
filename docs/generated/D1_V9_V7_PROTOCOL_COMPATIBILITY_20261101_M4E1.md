# D1 v9/v7 Protocol Compatibility Verification

**Date:** 2026-11-01  
**Status:** Researcher-selected in conversation; repository approval artifact intentionally absent.  
**Selected set under review:** Real-world protocol v9.0.0 + ground-truth protocol v7.0.0

## Verification result

The v9/v7 pair is internally compatible at the documentation level:

- v9 §5.4 explicitly references ground-truth v7 §2.4.
- Both define the same operational danger-zone convention.
- Both preserve independent front/back camera-local clocks and unresolved R04.
- Both define T1/T2 approach boundaries, T3 locomotive-unit clearance, T4 final-tail clearance, and explicit censoring.
- Both require human verification and prohibit model-prediction leakage.
- Current Stage-2.1 schema uses the canonical v7-era boundary names and four-state taxonomy.

## Difference matrix: HEAD versus v9/v7

| Topic | HEAD v8/v6 | Selected v9/v7 | Impact |
|---|---|---|---|
| R03 | Site survey is an incomplete prerequisite; visual landmarks provisional | R03 retired; operational convention replaces it | v9/v7 permits video-based operational annotation; no physical geodetic claim |
| T1/T2/T3/T4 landmarks | Landmarks require survey before certification | Visible frog/roadway/vendor-stall landmarks define operational convention | Existing candidate proposals align with v9/v7 semantics |
| Censoring | Left/right censoring defined, less operational detail | Explicit stream-independent handling and rationale | Stage-2.1 reviewer guide aligns with v9/v7 |
| Engine event | Engine treatment present but earlier text | T3≡T4 operational case-study treatment | Engine remains isolated; no denominator change |
| R04 | Independent clocks, unresolved | Independent clocks, unresolved | No conflict |
| Human review | Stage-2/Stage-3 workflow | Same workflow plus current 8.1.0 Stage-2.1 safeguards | Current code aligns with v9/v7-era workflow |

## Source-code and artifact compatibility

- `src/railway_detection/annotation/stage2_1_schema.py` uses `T3_locomotive_unit_clearance`, the v7/v9 canonical name.
- `src/railway_detection/annotation/stage2_1_schema.py` requires schema `8.1.0-stage2.1`, which is newer than both protocol versions but operationally extends the v7 workflow.
- `data/ground_truth/proposals/` and the Stage-2.1 queue use v7/v9-era candidate boundary terminology.
- No source module assumes v8/v6 as an active authority; remaining v8/v6 references are decision-register comparisons, historical documentation, or legacy docstrings.
- The candidate R04 manifest and Stage-2.1 queue do not contain a protocol decision envelope.

## Historical records and migration

The 27 legacy review files are schema 6.0.0, invalidated by verified notices, and must remain intact. They are not migrated to v7/v9 or Stage-2.1. Genuine future Stage-2.1 review records must be created under the authorized workflow; no migration is technically required for old records because they are explicitly excluded.

## Remaining technical limitations

1. D1 is still `PENDING_RESEARCHER_DECISION` in the canonical register.
2. `data/manifests/phase12_protocol_decision.json` is absent.
3. R04 remains unresolved; v9/v7 does not remove that dependency.
4. Some worktree titles say “FINAL,” but that is documentary wording, not a governance approval artifact.

## Recommendation

**Compatibility recommendation: proceed with v9/v7 as the selected protocol pair, subject to the researcher creating the required decision envelope.**

This is a technical recommendation, not an approval. No protocol hash or canonical status was changed.