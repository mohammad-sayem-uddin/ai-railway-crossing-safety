# D1 — Protocol Authority Comparison

**Status:** `PROPOSED — NOT APPROVED`

## Verified versions

| Document | HEAD | Worktree | Difference/effect |
|---|---:|---:|---|
| Real-world protocol | v8.0.0 (2026-10-09) | v9.0.0 (2026-10-12) | R03/site-survey treatment and operational danger-zone wording differ; R04 remains unresolved |
| Ground truth | v6.0.0 | v7.0.0 | Ground-truth convention and R03 treatment differ |
| Data flow | v6.0.0 | v7.0.0 | Boundary/workflow references follow the paired revision |
| Ablation matrix | v6.0.0 | v7.0.0 | Reconciled companion version differs |

## Consequences

HEAD retains earlier R03/site-survey prerequisite language. Worktree v9/v7 uses an operational
danger-zone convention and retires R03 as a separate site-survey blocker. Both retain R04
independent camera clocks. Selection changes protocol/profile hashes, GT workflow interpretation,
R04/scope language, and downstream manifest provenance.

**PROPOSED recommendation:** researcher review worktree v9/v7 because it matches the current
working design and operational convention; this is not an authority selection.

## Approval path

Researcher creates `data/manifests/phase12_protocol_decision.json` under the existing
`phase12-protocol-decision/1` envelope with decision ID, `decision_status=APPROVED`, allowlisted
`decided_by`, UTC date, verbatim statement, choices, and binding hash. Existing governance
validators must accept it. Do not edit protocol files.

**Response:** chosen set __________; rationale __________; decision-maker/date __________.
