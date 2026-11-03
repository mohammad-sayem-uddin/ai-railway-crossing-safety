# Governance Approval Drafts — NOT APPROVED — NOT SIGNED

> **Every draft below is `DRAFT`.** Each decision field, identity, statement and date is left **blank for the researcher**. This mission did not and cannot approve anything: approval requires the researcher's own attestation recorded through the repository's governance mechanism (for example a `phase12-protocol-decision/1` envelope whose `decided_by` is on the maintained allowlist). Researcher *direction* given in conversation (confirmed RD answers) is noted as context only; **it is not an approval**. The 2026-10-30 agent-transcribed decisions are not represented as ratified (see the ratification draft).

Common envelope fields the researcher must author (not drafted by the agent): `schema_version`, `decision_status` (must be set by the researcher to `APPROVED`), `decision_id`, `decided_by`, `researcher_statement`, `decided_at_utc`.

---
## GD-1 · `GOV-D1-PROTOCOL-AUTHORITY` — protocol and ground-truth authority
**Context (not a decision):** selected direction v9 / v7. Proposed final files: `…v9.1.0_PROPOSED.md`, `…v7.1.0_PROPOSED.md`.
**Preconditions:** wording adopted; files preserved (RD-003: commit + hashed snapshot); final bytes hashed.
**To be completed by the researcher:** selected pair: ☐ v9.1/v7.1 (after edits) ☐ v9.0.0/v7.0.0 as-is ☐ v8.0.0/v6.0.0 · SHA-256 of final protocol: `________` · SHA-256 of final GT protocol: `________` · statement: `________` · identity/date: `________`
**Status: DRAFT — NOT APPROVED.**

## GD-2 · `GOV-D2-EVALUATION-PROFILE` — M4 profile
**Context:** direction M4 `first_blocked_to_t4_clearance`; envelope key `choices.premature_opening_window`. M5 companion, counts only. Corrected incomplete-replay classification implemented (`M4_M5_PRODUCTION_CORRECTION`).
**Researcher to complete:** `choices.premature_opening_window = ________` · confirmation of the `no_steps_in_protection_interval` rule (a deviation flagged in the correction document): ☐ keep ☐ revert · statement/identity/date: `________`
**Status: DRAFT — NOT APPROVED.**

## GD-3 · M4/M5 contract
Contract text = `M4_M5_PRODUCTION_CORRECTION_20261101_M5A.md` §2–3 and v9.1.0-PROPOSED §5.2. Researcher approval: `________`. **DRAFT — NOT APPROVED.**

## GD-4 · Descriptive-only real-data pathway (proposal)
**Context:** `GOV-D3-DESCRIPTIVE-MODE` was recorded as approved (agent-transcribed); the implementation accepts **synthetic evidence only**. A real-data pathway requires: an approved evidence classification for real replay, provenance fields, isolation from every official entry point, a statement that results are fixed-site descriptive with no official or cross-site claim.
**Researcher to complete:** ☐ authorize design of the pathway ☐ decline · constraints: `________` · identity/date: `________`
**Status: PROPOSAL — NOT AUTHORIZED. No real-data descriptive evaluation is permitted.**

## GD-5 · Engine-event exclusion
Proposed text: "`engine_events/event_001` is excluded from pooled M4, M5, occupancy and train aggregates; it is a separate case study; one descriptive row only if approved ground truth exists." Consistent with the previously recorded isolation decision, which still needs ratification (RD-049).
Researcher: `________`. **DRAFT — NOT APPROVED.**

## GD-6 · `GOV-D4-R04-SYNCHRONIZATION` — exploratory scope
Proposed: preserve the existing authorized **11-event** exploratory scope; no official dual-camera scope; `train_events/event_010` not silently added; independent-camera analysis primary; the 20/23 criterion not claimed met; acoustic offsets never shift human GT timestamps.
Envelope bodies (`event_modes`, `accepted_sync_events`) are to be authored by the researcher: `________`. **DRAFT — NOT APPROVED.**

## GD-7 · Reviewer policy (`GOV-REVIEW-SECOND-REVIEW-TRIGGERS`, `GOV-REVIEW-CLEAR-BOUNDARY-AUDIT`)
Proposed: risk-based mandatory second-review triggers (list in the schema/governance proposal); risk-based clear-boundary audit with **no fixed percentage**; disagreement via a separate researcher entry, unresolved = `UNCERTAIN`; external audit reviewer **if** one can be appointed (identity: `________`, not supplied). Allowlist unchanged.
**DRAFT — NOT APPROVED.**

## GD-8 · Thresholds and ROI — deferred status record
`EXP-OPERATING-THRESHOLDS`: current constants are exploratory/descriptive only; **no scientific approval; no calibration or sensitivity experiment**. `EXP-ROI-GEOMETRY`: **no ROI-dependent official analysis**; danger zone from GT landmarks. Researcher acknowledgement: `________`. **STATUS: DEFERRED.**

## GD-9 · `EXP-B7E-PARAMETERS` — deferred status record
Mechanism (delayed timestamps) was previously selected. **`delay_s`, `target_source`, acceptance criteria are DEFERRED; none is invented.** `delay_s = 2.0` is the `source_staleness_s` software default, and `camera_front` appears only in older reports; neither is an approval. Researcher values when ready: `________`. **STATUS: DEFERRED.**

## GD-10 · Authorizations (not drafted as approvable here)
`AUTH-STAGE21-ADJUDICATION`, `AUTH-PILOT-EXEC`, `AUTH-PROMOTE-EXEC`, `AUTH-EVENT-SPLIT` (no official split), `AUTH-EVAL-AUTH`: **remain pending/not authorized.** No draft is offered because the prerequisites do not exist.
