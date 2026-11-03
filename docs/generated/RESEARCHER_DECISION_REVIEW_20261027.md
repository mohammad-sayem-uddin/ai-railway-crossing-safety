# Train Gate Automation — Researcher Decision Review & Readiness Gate Reassessment

**Date:** 2026-10-27 (UTC)
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`
**Branch / HEAD:** `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
**Status:** REVIEW ONLY — NO RESEARCH DECISIONS OR AUTHORIZATIONS RECORDED
**Labels:** `VERIFIED`, `PROPOSED_NOT_APPROVED`, `TESTED_SYNTHETICALLY`, `BLOCKED_BY_AUTHORITY`, `BLOCKED_BY_MISSING_EVIDENCE`, `NOT_VERIFIED`

## 1. Executive summary

The researcher decision package and all seven drafts were independently reviewed against live
source contracts. The drafts are appropriately unsigned and non-authoritative. Their core
claims are consistent with the repository; important scope constraints are recorded below.
The authoritative governance schemas require allowlisted researcher identity, decision
envelopes, exact schema versions, live hash bindings, and validation after approval.

The live official gate remains `ready=False` with **9 blockers**. No researcher decision,
ground-truth approval, split, R04 acceptance, promotion receipt, EVAL-AUTH, cache generation,
official run, or media access occurred during this review.

## 2. Repository state

- Root: `/Users/sayemuddin/Desktop/Train_automation`.
- Branch/HEAD: `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`.
- System Python 3.14.4; project `.venv` Python 3.11.15.
- No staged changes; existing tracked modifications and untracked research artifacts preserved.
- Four protocol files remain modified in the worktree relative to HEAD; no authority selected.
- Required official artifacts remain absent:

```text
data/manifests/phase12_evaluation_inputs.json
 data/manifests/phase12_protocol_decision.json
 data/manifests/phase12_r04_scope_decision.json
 data/splits/phase12_event_split_decision.json
 data/governance/stage21_promotion_receipt.json
 data/governance/eval_authorization.json
```

- Seven unsigned drafts remain under `docs/proposals/researcher_decision_package_20261027/`.
- No original media was accessed.

## 3. Live readiness gate

Verified with:

```bash
PYTHONPATH=src .venv/bin/python - <<'PY'
from pathlib import Path
from railway_detection.evaluation.execution_gate import assess_official_phase12_readiness
r = assess_official_phase12_readiness(Path('.'))
print('ready=', r.ready)
print('blocker_count=', len(r.blockers))
for b in r.blockers: print(b.code, '|', b.detail)
PY
```

Actual result:

```text
ready=False
blocker_count=9
COHORT_APPROVAL_MISSING | no approved engine_events record
COHORT_APPROVAL_MISSING | no approved no_train_events record
COHORT_APPROVAL_MISSING | no approved train_events record
EVAL_AUTH_NOT_GRANTED
EVENT_SPLIT_DECISION_MISSING
MANIFEST_MISSING
PREMATURE_OPENING_DEFINITION_UNDECIDED
R04_SCOPE_DECISION_MISSING
STAGE21_RECORDS_MISSING
```

## 4. Independent draft audit

| Draft | Status | Finding |
|---|---|---|
| Protocol authority | `PROPOSED_NOT_APPROVED` | Correctly presents HEAD v8/v6 versus worktree v9/v7; final artifact still requires `phase12-protocol-decision/1`. |
| Premature opening | `PROPOSED_NOT_APPROVED` | Correct v9/M4 comparison, clocks, and front-only limitation; no default implied. |
| Event split | `PROPOSED_NOT_APPROVED` | Correctly distinguishes image split from Phase 12 event framing; no membership invented. |
| R04 scope | `PROPOSED_NOT_APPROVED` | Correctly separates candidate calibration from researcher acceptance; one-row table is only a template. |
| Stage-2.1 checklist | `PROPOSED_NOT_APPROVED` | Matches active schema requirements and correctly rejects legacy/candidate records. |
| Cache checklist | `PROPOSED_NOT_APPROVED` | Correctly lists JSONL/manifest/provenance prerequisites and marks producers not-to-run. |
| EVAL-AUTH checklist | `PROPOSED_NOT_APPROVED` | Mirrors actual governance fields/bindings and correctly rejects LEG-EXEC substitution. |

No draft implies approval, changes the gate, or silently creates an official artifact. No
editorial correction was necessary.

## 5. Concise researcher decision sheet

### D1 — Effective protocol authority

**Question:** Select the governing protocol set: HEAD v8/v6 or worktree v9/v7.

**Why:** The worktree proposal retires R03 as a separate site-survey blocker and changes
operational danger-zone wording; both preserve unresolved R04. Downstream ground truth,
split, R04, and reports depend on the choice.

**Independent?** Yes, as a researcher decision; it must precede protocol-bound artifacts and
EVAL-AUTH. **Output:** `phase12-protocol-decision/1`, using the existing draft.
**Status:** `BLOCKED_BY_AUTHORITY`.

### D2 — Premature-opening definition

| Option | Semantics | Evidence/clock requirement | Status |
|---|---|---|---|
| v9 | Opening command while `T1 <= t < T4`; T1 front, T4 back | Accepted fused timeline | `PROPOSED_NOT_APPROVED` |
| M4 | Opening/blocked-to-unblocked in `(t_blocked, T4)` plus M5 | Replay blocked step and approved T4 | `PROPOSED_NOT_APPROVED` |

Neither is front-only evaluable. **Output:** protocol decision artifact. **Status:**
`BLOCKED_BY_AUTHORITY`.

### D3 — Event-level analysis framing

Supported options are: full-cohort descriptive benchmark with no held-out claim; two-session
exploratory contrast with imbalance/confounding caveats; or defer until multi-crossing data.
The existing image-level split is not an approved event split. **Status:**
`BLOCKED_BY_AUTHORITY`; decision artifact absent.

### D4 — R04 scope/synchronization

Select per-event single/independent/accepted dual camera modes and accepted-sync set. Dual
camera requires accepted membership plus validated calibration; independent camera preserves
separate clocks; single front does not make back-clock T4 evaluable. Candidate calibration is
evidence, not acceptance. **Output:** `phase12-r04-scope-decision/1`.
**Status:** `BLOCKED_BY_AUTHORITY`.

### D5 — Ground-truth review/promotion

Requires genuine Stage-2.1 `8.1.0-stage2.1` records, allowlisted reviewer, review duration
floor, model-independence attestation, observed-media hashes, four-state boundaries, rationales,
history, proposal/media bindings, promotion checks, receipt, and required cohort coverage.
Legacy schema-6.0.0 records and candidates are not active ground truth.
**Status:** `BLOCKED_BY_AUTHORITY` / `BLOCKED_BY_MISSING_EVIDENCE`.

### D6 — Cache production

Requires approved event eligibility, frozen configuration/policy/checkpoint identity, threshold
identity, JSONL/schema validation, manifest paths/counts/bytes/hashes, timestamps, R04 metadata
where needed, and official provenance. Potential producers can access raw media/models/write
outputs and remain not-to-run. **Status:** `BLOCKED_BY_AUTHORITY` / missing evidence.

### D7 — EVAL-AUTH

Requires protocol, split, R04, promotion receipt, input manifest, frozen config, policy, and
seven live hash bindings; allowlisted authorizer; exact official operation; physical operations
false; recorded-statement attestation; digest and stage validation. **Status:**
`BLOCKED_BY_AUTHORITY`.

## 6. Dependency graph

| Dependency | Type | Source |
|---|---|---|
| Protocol authority → protocol-bound artifacts | `HARD_DEPENDENCY` | Governance decision artifact/profile must be bound |
| Premature profile → official metrics/EVAL-AUTH | `HARD_DEPENDENCY` | `effective_profile()` refuses unresolved choice |
| Split framing → input manifest | `HARD_DEPENDENCY` | Manifest builder verifies split decision |
| R04 scope → camera manifest | `HARD_DEPENDENCY` | Builder verifies event modes/accepted sync |
| Stage-2.1 review → promotion receipt | `HARD_DEPENDENCY` | Gate requires active valid records/receipt |
| Split + R04 + GT → input manifest | `HARD_DEPENDENCY` | Manifest is derived from verified decisions |
| Approved decisions/GT → cache eligibility | `HARD_DEPENDENCY` | Cache scope/provenance requires eligibility |
| Cache artifacts → official evidence | `HARD_DEPENDENCY` | Integrity/provenance validation |
| Live bindings → EVAL-AUTH | `HARD_DEPENDENCY` | Governance refuses missing bindings |
| EVAL-AUTH/readiness → official evaluation | `HARD_DEPENDENCY` | Official runner rechecks readiness |
| Candidate calibration → R04 decision | `SOFT_DEPENDENCY` | Evidence informs but does not replace acceptance |
| Synthetic tests → decisions | `INDEPENDENT` | Safe regression work can continue |

## 7. Safe work that can proceed

- Maintain synthetic cache/adapter/governance tests (`TESTED_SYNTHETICALLY`).
- Validate unsigned template structure and report drift (`INDEPENDENT`).
- Produce metadata-only blocker summaries (`INDEPENDENT`).
- Prepare, but do not activate, a future cache-production wrapper (`PROPOSED_NOT_APPROVED`).
- Add session/group validation once an event-level decision artifact exists.

No engineering defect was found that could be repaired without changing scientific authority or
gate criteria. No code change is justified by this review.

## 8. Safe validation results

Executed during this review:

```bash
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/unit/test_phase12_governance.py \
  tests/unit/test_readiness_audit.py \
  tests/test_phase11_12_readiness_cli.py \
  tests/test_phase11_12_readiness_gate.py \
  tests/unit/test_phase12_input_contracts.py \
  tests/unit/test_phase12_documented_metrics.py \
  tests/unit/test_phase12_metric_arithmetic.py -q
```

Result: **149 passed**, synthetic/metadata-only.

The live readiness assessment was executed through the inspected API and remains `ready=False`
with nine blockers. No official or media-access command was run.

## 9. Recommended next action

The single best next action is **not an evaluation command**: the authorized researcher should
first select the effective protocol and premature-opening profile, then decide event-level
analysis framing and R04 scope. Only after those decisions should genuine Stage-2.1 adjudication,
promotion, cache production, and EVAL-AUTH preparation proceed.

## 10. Explicit scope and safety statement

This review does not select a protocol, approve labels, accept synchronization, create a split,
create EVAL-AUTH, generate caches, run inference, run official evaluation, or access original
media. Existing user work and prior reports remain preserved.
