# Mission 25 — Annotation schema and boundaries

Prepared 2026-11-05, America/New_York. Metadata/software infrastructure only; no genuine reviewer, observation, adjudication, source access or promotion established.

REVIEW_GOVERNANCE/1 uses frozen typed Batch, Source and BoundaryObservation contracts. The accompanying intake JSON Schema describes their wire shape; runtime validation adds identity, source, role, temporal and evidence constraints. This metadata schema does not activate or replace active Stage2.1 8.1 or the inactive proposed module.

| Boundary | Preserved meaning and evidence constraint |
|---|---|
| T1 | Leading approach at the adopted danger-zone/frog line; exact definition version bound. |
| T2 | Physical roadway-entry crossing only with PHYSICAL_ROADWAY_ENTRY landmark evidence. Missing landmark stays UNCERTAIN/NOT_OBSERVABLE; lens-plane fails. |
| T3 | Adopted protocol's locomotive-unit clearance: rear end of lead motive-power unit clears danger zone; not locomotive-head exit. No new geometry is inferred. |
| T4 | Adopted protocol's final vehicle/tail clearance; no invented exit landmark. |
| T_OCC_START | Only reconciled observable physical T2 can supply an alias, after verified physical-landmark and boundary-adoption evidence; constructed aliases return null. |

Observable values require exact integer local microseconds and original integer PTS/timebase/origin matching the named source and its range. Floats, booleans as clocks, mismatched cameras/versions and acoustic shifts refuse. Nonpoint states carry no numeric value. CENSORED preserves LEFT/RIGHT; uncertainty remains integer or explicitly unknown, with mandatory rationale. Different camera clocks are never averaged or shifted.

Original observation IDs cannot be overwritten. Exact duplicates are idempotent; a correction is a new ID with the exact predecessor digest and a reason after the first blind completion. Every original remains in history. No arbitrary tolerance or minimum review duration is added. The active 8.1 historical duration-floor mismatch remains a canonical-schema reconciliation gate; existing validators are unchanged.
