# GOV-D1 — Protocol Authority Decision Sheet

**Status:** `PENDING_RESEARCHER_DECISION`  
**Decision identifier:** `GOV-D1-PROTOCOL-AUTHORITY` (historical alias `D1`)  
**Approval field:** ______________________________  
**Decision-maker:** ______________________________  
**Date (UTC):** ______________________________

## Exact question

Which protocol pair is authoritative for the next authorized review/evaluation workflow?

1. Committed/HEAD pair: real-world protocol `v8.0.0` with ground-truth protocol `v6.0.0`.
2. Worktree design pair: real-world protocol `v9.0.0` with ground-truth protocol `v7.0.0`.

## Evidence-backed alternatives

| Alternative | Existing specification | Consequences |
|---|---|---|
| HEAD v8/v6 | `docs/archive/RESEARCH_PROTOCOL_V2.md`; comparison report | Retains earlier R03/site-survey prerequisite language and earlier paired definitions. Requires binding corresponding protocol/GT hashes before review/evaluation. |
| Worktree v9/v7 | `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`; `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` | Uses operational danger-zone convention and retires R03 as a separate blocker; still preserves independent R04 camera clocks. Requires binding v9/v7 hashes and corresponding review semantics. |

`docs/generated/PROTOCOL_AUTHORITY_COMPARISON_20261030.md` states that both choices alter ground-truth interpretation, R04 language, protocol/profile hashes, and downstream manifests. It recommends v9/v7 only as a technical recommendation, not an approval.

## Current implementation/documentation state

- Canonical register: pending in `src/railway_detection/experiments/preflight_validator.py`.
- Current worktree documents describe v9/v7 as final/current, but no researcher decision envelope exists at `data/manifests/phase12_protocol_decision.json`.
- `src/railway_detection/evaluation/governance.py` expects a `phase12-protocol-decision/1` envelope and refuses invalid/unimplementable overrides.
- Stage-2.1 schema terminology is implemented independently of a final authority choice; semantic interpretation must still be bound.

## Dependencies and risks

D1 affects Stage-2.1 reviewer instructions, boundary semantics, protocol/profile hashes, R04 scope language, official manifest construction, and all metrics. Proceeding without D1 risks reviewing under one semantic pair and evaluating under another. Existing candidate records must not be silently migrated between protocol interpretations.

## Required evidence for approval

- Researcher-selected protocol pair.
- Exact file paths and SHA-256 binding for the selected pair.
- Written rationale addressing R03/danger-zone differences.
- Statement of how the selected pair governs Stage-2.1 review and official evaluation.
- Valid `data/manifests/phase12_protocol_decision.json` accepted by governance validators.

## Researcher response

**Selected pair:** ______________________________  
**Rationale:** ____________________________________________________________________  
**Reviewer/evaluator binding statement:** __________________________________________  
**Signature/identity:** __________________________  **Date:** ______________________

No option is selected by Mission 4C.