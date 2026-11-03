# GOV-D1: Protocol Authority Recommendation

**Date:** 2026-11-01  
**Mission:** 4E — Researcher Decision Finalization  
**Status:** RECOMMENDATION ONLY — NOT APPROVED  
**Decision identifier:** `GOV-D1-PROTOCOL-AUTHORITY`  
**Approval field:** ______________________________

## Alternatives

| Option | Real-world protocol | Ground-truth protocol | Source |
|---|---|---|---|
| A | v8.0.0 (2026-10-09) | v6.0.0 (2026-10-09) | Committed HEAD |
| B | v9.0.0 (2026-10-12) | v7.0.0 (2026-10-12) | Worktree |

## Difference Matrix

| Aspect | HEAD v8/v6 (Option A) | Worktree v9/v7 (Option B) | Consequence |
|---|---|---|---|
| R03 site-survey | Required as separate prerequisite | RETIRED as separate blocker | B removes a blocking dependency |
| Danger-zone semantics | Requires physical survey | Operational Danger-Zone Annotation Convention (§5.4) | B uses researcher-defined visual landmarks |
| T1 definition | Physical crossing danger zone entry | Turnout switch frog / pedestrian corridor line | B is operationally verifiable from video |
| T2 definition | Locomotive occupies road crossing | Transverse camera plane / roadway boundary | B is camera-observable |
| T3 definition | Rear coupler clears danger zone | Vendor-stall departure boundary plane | B uses visible landmark |
| T4 definition | Final vehicle clears danger zone | Same vendor-stall departure boundary | B consistent with T3 |
| T_scene_clear | Train vacates all camera FOV | Recedes past visible corridor sightlines | B is more specific |
| R04 treatment | Independent camera clocks, unresolved | Same — both retain R04 unresolved | No difference |
| Left-censoring | Acknowledged but less detailed | Detailed §2.3 with explicit prohibition | B is more precise |
| Right-censoring | Acknowledged | Explicit recording-end handling | B is more precise |
| Engine T3≡T4 | Mentioned | Explicit coincidence rule with back-camera preference | B is more specific |
| Anti-synthesis | Present | Present + strengthened | B adds more safeguards |
| Stage-2.1 schema | References 7.0.0 | References 8.1.0-stage2.1 | B aligns with current code |

## Scientific Consequences

### Option A (HEAD v8/v6)
- Requires physical site survey that does not exist in the repository.
- T1/T2/T3/T4 definitions reference physical geometry not verifiable from video alone.
- Creates a blocking dependency that cannot be resolved without field access.
- Incompatible with current Stage-2.1 schema (8.1.0-stage2.1).

### Option B (Worktree v9/v7)
- Uses operational conventions verifiable from video evidence.
- Aligns with current implementation (stage2_1_schema.py, promotion_gate.py).
- Removes blocking R03 dependency.
- Maintains R04 as unresolved (both options do this).
- Compatible with existing review workflow and queue.

## Operational Consequences

- Option A: Cannot proceed with review without physical survey.
- Option B: Can proceed with video-based review using visible landmarks.

## Compatibility with Existing Records

- All 27 legacy review records reference schema 6.0.0 (invalidated).
- Current Stage-2.1 schema is 8.1.0-stage2.1 (aligned with Option B).
- All 27 proposals were generated under v7.0.0 conventions (Option B).
- Mission 4B review preparation assumes Option B semantics.

## Recommendation

**Option B (Worktree v9.0.0 / GT v7.0.0)**

**Confidence:** HIGH

**Rationale:**
1. The worktree documents represent the current working design.
2. The operational danger-zone convention is verifiable from video evidence.
3. The current Stage-2.1 schema (8.1.0-stage2.1) was built against v7.0.0 semantics.
4. All existing proposals, review preparation, and queue artifacts assume v7.0.0.
5. Option A requires a physical site survey that does not exist.
6. The only material difference (R03 retirement) removes a blocker without weakening scientific rigor.

**This recommendation is NOT an approval. The researcher must explicitly select and record the decision.**

## Researcher Response

**Chosen option:** ______________________________  
**Rationale:** ______________________________  
**Decision-maker:** ______________________________  
**Date (UTC):** ______________________________