# D1 Protocol Binding Implementation Plan

**Status:** Non-executing plan; no binding artifact created.

## Required future artifact

`data/manifests/phase12_protocol_decision.json` with schema `phase12-protocol-decision/1`, validated by `src/railway_detection/evaluation/governance.py`.

## Proposed contents (not to be written by this mission)

- `schema_version`
- `decision_status: APPROVED`
- Decision ID
- Allowlisted researcher identity
- UTC decision date
- Verbatim researcher statement selecting real-world v9.0.0 and ground-truth v7.0.0
- Choices identifying both protocol files
- Notes covering R03 retirement, operational danger-zone convention, and preserved R04 independence
- Hash binding for selected protocol/profile artifacts as required by the governance envelope

## Validation sequence

1. Verify the researcher identity is already authorized for governance decisions.
2. Hash only the selected text protocol artifacts (not media).
3. Validate envelope schema and decision status.
4. Validate protocol choices against `protocol_choices.py`.
5. Confirm the selected pair is compatible with Stage-2.1 boundary names and censoring semantics.
6. Re-run read-only readiness checks.
7. Leave legacy records untouched; no migration is permitted.

## Risks

- Binding v9/v7 without resolving R04 does not authorize cross-camera timing.
- Binding D1 does not authorize reviewers, pilot, promotion, or evaluation.
- A protocol hash change later invalidates downstream manifests and EVAL-AUTH bindings.

## Rollback

Before artifact creation, rollback is simply no write. After creation, any correction requires a new researcher-authorized decision artifact/version; never edit historical decision records in place.

**No artifact was written by Mission 4E.1.**