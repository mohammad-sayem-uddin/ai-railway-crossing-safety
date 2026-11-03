# Governance Boundary Audit (Mission 5A.1)

> Read-only checks of the Mission 5A artifacts and repository. No governance document was rewritten, approved or signed.

| Check | Evidence | Result |
|---|---|---|
| v9.1.0 / v7.1.0 clearly proposed | both begin with a blockquote "PROPOSED — NOT APPROVED — NOT AUTHORIZED", version suffix `-PROPOSED`, source hash recorded; historical text in marked blocks | **Pass** (but see wording finding W-1) |
| In-place v9.0.0 / v7.0.0 unchanged | SHA-256 `7c183b32…8734c` / `d100c1e6…49ecf4` identical to baseline, at start and end of this mission | **Pass** |
| Proposed Stage-2.1 schema not imported by any gate | search of `src`, `scripts`, `configs`: no reference; only `tests/unit/test_mission5a_production.py` imports it (asserted by a test that no `src` file does) | **Pass** |
| No fabricated signature/identity/date/approval in drafts | search for names, e-mail, "signed by", "approved by", dated `decided_at_utc`: none; `GOVERNANCE_APPROVAL_DRAFTS` and `RATIFICATION_DRAFT…` each carry 9 blank `________` fields and a DRAFT/NOT SIGNED banner | **Pass** |
| Ratification unsigned and DRAFT | banner "DRAFT — NOT RATIFIED — NOT SIGNED"; attestation block blank | **Pass** |
| D1 / D2 pending | code register: `GOV-D1-PROTOCOL-AUTHORITY`, `GOV-D2-EVALUATION-PROFILE` = `PENDING_RESEARCHER_DECISION`; `data/manifests/phase12_protocol_decision.json` absent | **Pass** |
| B7e numerics deferred | `EXP-B7E-PARAMETERS` pending; no `delay_s`/`target_source` in any 5A artifact except as "not approved" text | **Pass** |
| Thresholds / ROI unapproved | `EXP-OPERATING-THRESHOLDS` = `IMPLEMENTED_BUT_NOT_SCIENTIFICALLY_APPROVED`; `EXP-ROI-GEOMETRY` pending | **Pass** |
| R04 pending; scope not expanded | `GOV-D4-R04-SYNCHRONIZATION` pending; `phase12_r04_scope_decision.json` absent; both exploratory configs list **11** events, `event_010` not included; no config newer than the 5A report | **Pass** |
| Register totals | 12 PENDING (8 prior + 4 added by 5A), 7 APPROVED_BY_RESEARCHER (unchanged), 1 implemented-not-approved, 1 superseded | **Pass** — no approval created |
| Engine excluded from pooled train metrics | verified in code and tests (engine audit) | **Pass** |
| Occupancy duration deferred | no occupancy implementation in `src`; protocols/proposals say deferred | **Pass** |
| No official split / EVAL-AUTH / receipt | `data/splits/phase12_event_split_decision.json`, `data/governance/eval_authorization.json`, `stage21_promotion_receipt.json` absent; `data/governance` holds only `leg_exec_authorization.json`; nothing under `data/`, `configs/`, `schemas/` newer than the 5A report | **Pass** |
| Reviewer allowlist unchanged | `authorized_reviewers.json` still contains exactly one identity | **Pass** |
| Lead-in screen remains a technical proposal | default-off, unwired (tests), not referenced by any gate or approval draft as a rule | **Pass** — but its M3 semantics are undecided (see lead-in audit) |

## Wording and authority-escalation findings
* **W-1 (LOW) "Final" in proposed titles.** `FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL_v9.1.0_PROPOSED.md` and `FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md` keep the headline `# Final …` and file names starting `FINAL_`; the subtitle "Final Evaluation Design" remains. The banner immediately below says PROPOSED, but a reader of the title line alone could infer finality (the same pattern the Mission 4D wording audit flagged). Recommendation: prefix the headline with "PROPOSED —" when the researcher next edits; not changed here.
* **W-2 (INFORMATIONAL) Mission 5A report statements now superseded:** deviation 5 ("engine events reach the engine branch earlier") applies only to bare ids; the M4/M5 correction document's claim that incomplete evidence is never M5 is true for end-truncation only; the M4/M5 identity rule description predates the 5A.1 cohort/flag checks and the unresolved-cohort allowance. These documents were **not edited**; this audit supersedes them on those points.
* **W-3 (INFORMATIONAL) "implemented" vs "approved":** the 5A report keeps these separate throughout; no escalation found. The `RD_IMPLEMENTATION_MATRIX` correctly says confirmed RD answers are direction, not approvals.
* No document was found that presents a proposal as approved, grants an authorization, or signs for the researcher.
