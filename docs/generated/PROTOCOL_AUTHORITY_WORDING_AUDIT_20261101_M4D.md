# Protocol Authority Wording Audit

**Date:** 2026-11-01  
**Mission:** 4D — Scientific Governance Integrity Remediation  
**Status:** AUDITED; conflicts documented; no historical records rewritten

## Issue

Mission 4C identified that worktree protocol documents use language that could mislead a reviewer into believing protocol authority has been formally resolved, while `GOV-D1-PROTOCOL-AUTHORITY` remains `PENDING_RESEARCHER_DECISION`.

## Findings

### Documents with potentially misleading "FINAL" or "Status: FINAL" language

| Document | Title/Status Line | Issue |
|---|---|---|
| `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` | "**Status:** FINAL MASTER PROTOCOL SPECIFICATION" | Implies finality while D1 is pending |
| `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` | "**Status:** PREREQUISITE SPECIFICATION" | Less misleading but still implies authority |
| `docs/FINAL_EXPERIMENT_DATA_FLOW.md` | "**Status:** REFERENCE ARCHITECTURAL GUIDE" | Neutral |
| `docs/FINAL_ABLATION_MATRIX.md` | "**Status:** REFERENCE SPECIFICATION — Reconciled with Ground Truth v7.0.0 & Protocol v9.0.0" | Implies v9 is the reconciled authority |

### Generated reports with potentially misleading language

| Report | Issue |
|---|---|
| `docs/generated/RESEARCH_GOVERNANCE_STATUS_20261101_M3.md` | Uses "D1" and "D2" for thresholds/ROI (superseded by M4A reconciliation) |
| `docs/generated/EXPERIMENT_PREFLIGHT_READINESS_20261101_M3.md` | Uses "D1" and "D2" for thresholds/ROI (superseded by M4A reconciliation) |

## Actions Taken

1. **No historical documents were rewritten.** The protocol documents (`FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`, `FINAL_GROUND_TRUTH_PROTOCOL.md`, etc.) are working-tree documents that represent the current design intent. They are not governance decision records.

2. **The canonical decision register remains the controlling source.** `GOV-D1-PROTOCOL-AUTHORITY` is `PENDING_RESEARCHER_DECISION` in `CANONICAL_DECISION_REGISTER`. This overrides any document-level "FINAL" language.

3. **M4C decision sheets explicitly state pending status.** The `GOV_D1_PROTOCOL_AUTHORITY_DECISION_20261101_M4C.md` sheet clearly marks the decision as pending and provides the exact question for the researcher.

4. **No canonical decision status was changed.** `GOV-D1-PROTOCOL-AUTHORITY` remains `PENDING_RESEARCHER_DECISION`.

## Recommendation

Future protocol documents should use the phrasing: "Candidate protocol — pending researcher approval (GOV-D1-PROTOCOL-AUTHORITY)" until the decision envelope is created.

## M3 Label Supersession Note

The M3 reports that used "D1" for operating thresholds and "D2" for ROI geometry were superseded by Mission 4A's reconciliation. The canonical IDs are now:
- `GOV-D1-PROTOCOL-AUTHORITY` (protocol authority)
- `GOV-D2-EVALUATION-PROFILE` (evaluation profile)
- `EXP-OPERATING-THRESHOLDS` (thresholds)
- `EXP-ROI-GEOMETRY` (ROI)

This supersession is recorded in `M3-OVERLOADED-D1-D2-LABELS` = `SUPERSEDED_WITH_EXPLICIT_RECORD`.
