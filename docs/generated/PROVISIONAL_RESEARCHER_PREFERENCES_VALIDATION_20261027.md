# Train Gate Automation — Provisional Researcher Preferences Validation

**Date:** 2026-10-27 UTC
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`
**Branch / HEAD:** `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
**Status:** VALIDATION ONLY — NO DECISIONS OR AUTHORIZATIONS RECORDED
**Labels:** `CONSISTENT_WITH_CONTRACT`, `CONFLICTS_WITH_CONTRACT`, `INSUFFICIENT_EVIDENCE`, `REQUIRES_RESEARCHER_CLARIFICATION`, `BLOCKED_BY_AUTHORITY`, `BLOCKED_BY_MISSING_EVIDENCE`, `NOT_VERIFIED`

## 1. Executive summary

The four researcher statements are valid **provisional preferences**, not approved decisions.
They have been checked against the live protocol files, metric/profile code, split validator,
R04 validator, Stage-2.1 schema, and readiness gate.

| Preference | Validation classification | Summary |
|---|---|---|
| D1 protocol authority | `REQUIRES_RESEARCHER_CLARIFICATION` | Two document sets genuinely conflict; no automatic authority rule exists. |
| D2 M4 (`first_blocked_to_t4_clearance`) | `CONSISTENT_WITH_CONTRACT` + `INSUFFICIENT_EVIDENCE` | M4 is an implemented option and preserved metric name, but official selection requires a researcher decision and approved T4 evidence; M4 is not front-only evaluable. |
| D3 full-cohort descriptive framing | `CONFLICTS_WITH_CONTRACT` pending contract decision | Scientifically documented as an option, but current `validate_event_level_split()` requires nonempty train/val/test partitions; a full-cohort mode needs an approved contract decision/amendment. |
| D4 per-metric/per-event camera scope | `CONSISTENT_WITH_CONTRACT` + `INSUFFICIENT_EVIDENCE` | Per-event camera modes are supported, but no researcher R04 scope artifact or accepted synchronization evidence exists. |

The official gate remains `ready=False` with nine blockers. No protocol, metric, split, scope,
ground truth, cache, promotion receipt, or EVAL-AUTH artifact was changed or created.

## 2. Repository verification

- Root: `/Users/sayemuddin/Desktop/Train_automation`.
- HEAD/branch: `d4db94d` / `main`.
- System Python 3.14.4; project `.venv` Python 3.11.15.
- No staged changes; existing user changes/untracked research artifacts preserved.
- No original media accessed or hashed; no inference, cache generation, official evaluation,
  timing pilot, promotion, or EVAL-AUTH creation performed.
- Existing source reports reviewed: `RESEARCHER_DECISION_SESSION_PACK_20261027.md`,
  `RESEARCHER_DECISION_REVIEW_20261027.md`, `RESEARCHER_DECISION_PACKAGE_20261027.md`,
  `PRE_EVALUATION_READINESS_AUDIT_20261027.md`.

## 3. Current authoritative artifact status

| Artifact | Live status |
|---|---|
| `data/manifests/phase12_protocol_decision.json` | Missing |
| `data/manifests/phase12_r04_scope_decision.json` | Missing |
| `data/splits/phase12_event_split_decision.json` | Missing |
| `data/manifests/phase12_evaluation_inputs.json` | Missing |
| `data/governance/stage21_promotion_receipt.json` | Missing |
| `data/governance/eval_authorization.json` | Missing |

Presence is not treated as approval; none of these artifacts is present anyway.

## 4. Current readiness gate

Executed through the existing metadata-only API:

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

## 5. D1 — Protocol authority

**Provisional preference:** compare committed and working-tree versions without automatic selection.

**Classification:** `REQUIRES_RESEARCHER_CLARIFICATION`.

| Document | HEAD | Worktree | Material difference |
|---|---:|---:|---|
| Final real-world protocol | v8.0.0 | v9.0.0 | R03/site-survey treatment and operational danger-zone wording |
| Ground-truth protocol | v6.0.0 | v7.0.0 | Ground-truth convention/R03 treatment |
| Data flow | v6.0.0 | v7.0.0 | Boundary/workflow references |
| Ablation matrix | v6.0.0 | v7.0.0 | Reference reconciliation |

Both retain unresolved R04 independent camera clocks. Selecting either set affects protocol-
bound hashes, ground-truth workflow interpretation, and reports. Existing governance expects a
researcher-authored `phase12-protocol-decision/1` envelope; no selection is recorded.

## 6. D2 — Premature opening

**Provisional preference:** `first_blocked_to_t4_clearance` (M4).

**Classification:** `CONSISTENT_WITH_CONTRACT` as an implemented option, plus
`INSUFFICIENT_EVIDENCE` for official use and `REQUIRES_RESEARCHER_CLARIFICATION` for selection.

The implementation (`metrics.py:94-122`) defines M4 using the first blocked replay step and
strict interior `(t_blocked, T4)` behavior, with M5 `never_protected` when no blocked step
precedes T4. `protocol_choices.py` lists M4 implemented but `effective_profile()` refuses
unresolved profiles.

| Option | Required evidence | Limitation |
|---|---|---|
| v9 `t1_entry_to_t4_clearance` | Accepted fused timeline, approved front T1/back T4 | Not front-only or independent-clock evaluable |
| M4 `first_blocked_to_t4_clearance` | Replay blocked step, approved back-clock T4 | Still not front-only evaluable; profile must be bound |

Missing/censored/uncertain boundaries are not evaluated, never imputed. M4 preference cannot
become official without the decision artifact and approved evidence.

## 7. D3 — Full-cohort descriptive framing

**Provisional preference:** full-cohort descriptive benchmark if supported.

**Classification:** `CONFLICTS_WITH_CONTRACT` under the current split contract, plus
`REQUIRES_RESEARCHER_CLARIFICATION` and `INSUFFICIENT_EVIDENCE`.

Research documents support full-cohort descriptive reporting with no held-out/generalization
claim. However `research_contracts.validate_event_level_split()` requires exactly nonempty,
disjoint train/val/test partitions, and `manifest_builder.py` verifies a researcher split
decision and exact event set. Full-cohort framing therefore needs an approved contract/schema
decision or supported descriptive mode; the existing image split is not an event approval.

## 8. D4 — Per-metric/per-event R04 scope

**Provisional preference:** camera requirements determined per metric/event, with sync evidence
where required.

**Classification:** `CONSISTENT_WITH_CONTRACT` in principle, plus `INSUFFICIENT_EVIDENCE` and
`BLOCKED_BY_AUTHORITY` for execution.

`validate_camera_scope()` supports per-event single/independent/dual modes; dual requires
accepted-sync membership. Frozen config disallows unverified zero offsets. Candidate calibration
is evidence only, not researcher acceptance. No tolerance is invented. R04 artifact is missing.

## 9. Workflow and confirmation sheet

| Preference | Can enter existing workflow? | Required artifact | Confirmation status |
|---|---|---|---|
| D1 protocol | Yes, after genuine decision envelope | `phase12-protocol-decision/1` | `PENDING_RESEARCHER_DECISION` |
| D2 M4 | Yes, as `choices.premature_opening_window` if researcher selects it | protocol decision + profile hash | `PENDING_RESEARCHER_DECISION` |
| D3 full cohort | Not under current train/val/test validator without contract decision/amendment | split decision or approved descriptive-mode contract | `PENDING_RESEARCHER_CLARIFICATION` |
| D4 per-event scope | Yes, after per-event modes/accepted sync set | `phase12-r04-scope-decision/1` | `PENDING_RESEARCHER_DECISION` |

### Blank final confirmation

| Decision | Final choice | Rationale/evidence | Decision-maker/date | Approval artifact | Validation result |
|---|---|---|---|---|---|
| D1 protocol authority | | | | | |
| D2 premature opening | | | | | |
| D3 analysis framing | | | | | |
| D4 R04 scope | | | | | |

No selected value from the provisional preferences has been written to an authoritative JSON
path. No approval is implied by this report.

## 10. Safe validation commands and results

Executed during this validation:

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

Result: **149 passed** (synthetic/metadata-only).

The metadata-only readiness gate returned `ready=False` with 9 blockers. No official,
raw-media, inference, cache-generation, timing-pilot, promotion, or authorization command ran.

## 11. Next action

The next safe action is a genuine researcher decision session resolving D1/D2 first, then D3/D4.
After genuine decisions, the existing schemas and governance validators must be used to create
and validate authoritative artifacts. Until then, empirical evaluation remains blocked.
