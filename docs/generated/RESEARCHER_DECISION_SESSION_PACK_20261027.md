# RESEARCHER WORKING DOCUMENT — NOT APPROVED — NOT AUTHORIZATION

# Train Gate Automation — Researcher Decision Session Pack

**Created:** 2026-10-27 UTC
**Repository HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
**Status:** `PROPOSED_NOT_APPROVED`

## Purpose and source links

This concise pack prepares a genuine researcher decision session. It makes no scientific
decision, approval, synchronization acceptance, split, ground-truth promotion, cache, EVAL-AUTH,
or execution change.

Sources:

- `docs/generated/RESEARCHER_DECISION_PACKAGE_20261027.md`
- `docs/generated/RESEARCHER_DECISION_REVIEW_20261027.md`
- `docs/generated/PRE_EVALUATION_READINESS_AUDIT_20261027.md`
- `docs/proposals/researcher_decision_package_20261027/`
- `src/railway_detection/evaluation/execution_gate.py`
- `src/railway_detection/evaluation/governance.py`
- `src/railway_detection/evaluation/protocol_choices.py`

## Live readiness snapshot — `VERIFIED`

Metadata-only reassessment returned:

```text
ready=False
blocker_count=9
COHORT_APPROVAL_MISSING (engine_events)
COHORT_APPROVAL_MISSING (no_train_events)
COHORT_APPROVAL_MISSING (train_events)
EVAL_AUTH_NOT_GRANTED
EVENT_SPLIT_DECISION_MISSING
MANIFEST_MISSING
PREMATURE_OPENING_DEFINITION_UNDECIDED
R04_SCOPE_DECISION_MISSING
STAGE21_RECORDS_MISSING
```

All six authoritative Phase 12/EVAL-AUTH artifacts checked this session are missing. No newer
genuine researcher decision or approval artifact was found.

## Decision sheet

### D1 — Effective protocol authority

| Document | HEAD | Worktree | Material difference |
|---|---:|---:|---|
| Final real-world protocol | v8.0.0 | v9.0.0 | Worktree retires R03 as a separate site-survey blocker and introduces operational danger-zone wording; R04 remains unresolved. |
| Ground-truth protocol | v6.0.0 | v7.0.0 | Worktree follows the operational convention/R03 retirement and preserves independent clocks. |
| Data flow | v6.0.0 | v7.0.0 | Worktree references updated boundary taxonomy/workflow. |
| Ablation matrix | v6.0.0 | v7.0.0 | Worktree reconciles against GT v7/protocol v9. |

**Options:** HEAD v8/v6; worktree v9/v7; researcher-defined exact set.
**Required artifact:** `phase12-protocol-decision/1`, validated by governance.

Researcher choice: ____________________
Rationale: _____________________________
Decision-maker/date: ____________________

### D2 — Premature-opening definition

| Option | Definition | Required evidence | Limitation |
|---|---|---|---|
| v9 | Opening command while `T1 <= t < T4`; T1 front, T4 back | Accepted fused timeline and approved T1/T4 | Not front-only evaluable |
| M4 | Opening/blocked-to-unblocked in `(t_blocked, T4)` plus M5 | Replay blocked step and approved T4/back clock | Not front-only evaluable |

Missing/censored/uncertain boundaries remain not-evaluable, never imputed. M4 remains the
code-level name and no default profile exists.

Researcher selection: ____________________
Rationale/comparability: __________________
Required implementation work: ______________

### D3 — Event-level analysis framing

| Option | Can answer | Cannot claim | Artifact |
|---|---|---|---|
| Full-cohort descriptive | Fixed-site operational characterization | Held-out/cross-crossing generalization | Researcher framing/contract decision |
| Two-session exploratory | Session/domain contrast | Unconfounded shift/generalization | Event decision with confounding statement |
| Defer multi-crossing | Stronger future generalization | Current milestone | Researcher defer decision |

The image-level split is not an approved event split; existing metadata is insufficient to invent
session/crossing-safe membership.

Researcher selection: ____________________
Permitted claims: _________________________
Leakage limitation: _______________________

### D4 — R04 scope and synchronization

Schema validity, artifact integrity, measured synchronization quality, and researcher acceptance
are separate. Dual camera requires accepted membership plus validated calibration; independent
camera preserves local clocks; single front does not make back-clock T4 evaluable. Candidate
calibration is evidence only; no tolerance is invented.

Per-event mode table/attachment: ______________________________
Accepted-sync set: ____________________________________________
Evidence/uncertainty basis: ____________________________________
Researcher acceptance/rationale: _______________________________

### D5 — Stage-2.1 adjudication and promotion

Active schema: `8.1.0-stage2.1`. Required: allowlisted reviewer, review-duration floor,
model-independence attestation, observed front/back media hashes, four-state boundary states,
values/cameras for observable boundaries, rationales, append-only history, proposal/media
bindings, live promotion checks, promotion receipt, and required cohort coverage.

Current review files are legacy schema 6.0.0 and invalidated. Candidates are not labels.

Review scope/cohorts: ____________________
Reviewer/independence process: ____________
Promotion decision: _______________________

### D6 — Official cache production

Prerequisites: approved event/cohort eligibility; frozen config/policy/checkpoint identity;
threshold identity; valid front vision/audio JSONL; finite ordered timestamps; manifest v1.0.0;
relative paths; SHA-256/byte/line counts; approved synchronization metadata where needed;
official evidence provenance and later EVAL-AUTH binding.

Potential producers can access media/models/write outputs and are `NOT_TO_BE_RUN_PENDING_REVIEW`.

Authorized production scope: ____________________
Provenance owner: ______________________________

### D7 — EVAL-AUTH

Required by `governance.verify_eval_authorization()`: protocol/split/R04 decisions, valid
promotion receipt, real input manifest, seven live bindings, allowlisted authorizer, exact
operation `phase12_official_evaluation`, physical operations `false`, recorded-statement
attestation with null signature, self-consistent digest, and matching stage.

`leg_exec_authorization.json` is a separate legacy operation and cannot substitute.

Researcher authorization decision: ____________________
Authorized stage: _____________________________________

## Decision dependency map

| Dependency | Status | Source |
|---|---|---|
| Protocol → protocol-bound artifacts | `HARD_DEPENDENCY` | Governance decision/profile hash binding |
| Premature profile → official metrics/EVAL-AUTH | `HARD_DEPENDENCY` | `effective_profile()` refuses unresolved choice |
| Split framing → input manifest | `HARD_DEPENDENCY` | `manifest_builder` verifies decision |
| R04 scope → camera manifest | `HARD_DEPENDENCY` | Builder verifies modes/accepted sync |
| Stage-2.1 review → promotion receipt | `HARD_DEPENDENCY` | Gate requires active records/receipt |
| Decisions/GT → cache eligibility | `HARD_DEPENDENCY` | Official provenance scope |
| Cache artifacts → EVAL-AUTH | `HARD_DEPENDENCY` | Live binding keys |
| Candidate calibration → R04 discussion | `SOFT_DEPENDENCY` | Evidence informs, never accepts |
| Synthetic validation → researcher decisions | `INDEPENDENT` | Safe software work |

## Safe validation during this review

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

## Researcher worksheet

| Decision | Choice | Rationale | Evidence reviewed | Decision-maker/date | Approval status | Downstream updates |
|---|---|---|---|---|---|---|
| D1 protocol | `PENDING_RESEARCHER_DECISION` | | | | | |
| D2 endpoint | `PENDING_RESEARCHER_DECISION` | | | | | |
| D3 framing | `PENDING_RESEARCHER_DECISION` | | | | | |
| D4 R04 scope | `PENDING_RESEARCHER_DECISION` | | | | | |
| D5 adjudication | `PENDING_RESEARCHER_DECISION` | | | | | |
| D6 cache production | `PENDING_RESEARCHER_DECISION` | | | | | |
| D7 EVAL-AUTH | `PENDING_RESEARCHER_DECISION` | | | | | |

No selected value may be written into an authoritative JSON path until a genuine researcher
decision exists and the existing schema validation succeeds.

## Recommended next action

Enable a genuine researcher decision session: resolve D1/D2 first, then D3/D4, before any
Stage-2.1 adjudication, cache production, promotion, EVAL-AUTH, or official evaluation.

**Safety statement:** No protocol was selected, no evidence approved, no cache generated, no
EVAL-AUTH created, no official evaluation run, and no original media accessed.
