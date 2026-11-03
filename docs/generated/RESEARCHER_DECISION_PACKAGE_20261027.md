# Train Gate Automation — Researcher Decision Package

**Date:** 2026-10-27 (UTC)
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`
**Branch / HEAD:** `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
**Status:** DECISION PACKAGE — NO DECISIONS OR AUTHORIZATIONS RECORDED
**Labels:** `VERIFIED`, `PROPOSED_NOT_APPROVED`, `TESTED_SYNTHETICALLY`, `BLOCKED_BY_AUTHORITY`, `BLOCKED_BY_MISSING_EVIDENCE`, `NOT_VERIFIED`

## 1. Executive summary

This package prepares the researcher to resolve the current empirical-evaluation blockers. It
does not select a protocol, approve ground truth, create a split, accept synchronization,
create EVAL-AUTH, generate caches, or run evaluation.

The actual readiness gate remains `ready=False` with nine blockers. The repository contains
substantial tested engineering, but no active valid Stage-2.1 ground truth, Phase 12 event
split decision, R04 scope decision, derived input manifest, protocol decision, promotion
receipt, EVAL-AUTH, or verified real cache set.

Unsigned templates are in:

```text
docs/proposals/researcher_decision_package_20261027/
```

Every template begins with `DRAFT — NOT APPROVED — NOT AUTHORIZATION` and is outside
authoritative governance paths.

## 2. Verified repository state

- Root: `/Users/sayemuddin/Desktop/Train_automation`.
- Branch/HEAD: `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`.
- System Python 3.14.4; project `.venv` Python 3.11.15.
- No staged changes; existing tracked modifications and untracked research artifacts preserved.
- No stage/commit/push/reset/clean/broad revert/delete operations performed.
- No original media accessed.
- Prior implementation, independent review, Phase 12 adapter audit, and readiness audit read.

## 3. Current readiness result

Metadata-only command executed:

```text
PYTHONPATH=src .venv/bin/python - <<'PY'
from pathlib import Path
from railway_detection.evaluation.execution_gate import assess_official_phase12_readiness
v = assess_official_phase12_readiness(Path('.'))
print('READY', v.ready)
print('BLOCKERS', len(v.blockers))
for b in v.blockers: print(b.code, '|', b.detail)
PY
```

Result:

```text
READY False
BLOCKERS 9
COHORT_APPROVAL_MISSING: no approved engine_events record
COHORT_APPROVAL_MISSING: no approved no_train_events record
COHORT_APPROVAL_MISSING: no approved train_events record
EVAL_AUTH_NOT_GRANTED
EVENT_SPLIT_DECISION_MISSING
MANIFEST_MISSING
PREMATURE_OPENING_DEFINITION_UNDECIDED
R04_SCOPE_DECISION_MISSING
STAGE21_RECORDS_MISSING
```

## 4. Blocker-to-decision register

| ID | Gate/blocker | Missing decision/evidence | Options/implication | Owner/status | Required artifact/validation |
|---|---|---|---|---|---|
| R-PROTOCOL | `PREMATURE_OPENING_DEFINITION_UNDECIDED`; protocol conflict | Effective v8/v6 vs v9/v7 and endpoint profile | Select HEAD set or worktree proposal; changes R03, annotation convention, metric interpretation | Researcher; `BLOCKED_BY_AUTHORITY` | `phase12-protocol-decision/1`; `verify_protocol_override`; live profile hash |
| R-ENDPOINT | `PREMATURE_OPENING_DEFINITION_UNDECIDED` | v9 T1–T4 versus M4 blocked–T4 | v9 needs aligned T1/T4; M4 needs T4 and replay blocked tick; neither front-only evaluable | Researcher; `BLOCKED_BY_AUTHORITY` | Same protocol decision; metric profile tests/binding |
| R-SPLIT | `EVENT_SPLIT_DECISION_MISSING` | Event-level analysis framing | Full-cohort descriptive; two-session exploratory; defer multi-site | Researcher; `BLOCKED_BY_AUTHORITY` | `phase12-event-split-decision/1`; `validate_event_level_split` or approved contract amendment |
| R-R04 | `R04_SCOPE_DECISION_MISSING` | Per-event camera mode and accepted sync set | Single front primary; restricted independent/dual scope; dual only accepted/calibrated events | Researcher; `BLOCKED_BY_AUTHORITY` | `phase12-r04-scope-decision/1`; `check_r04_body`; calibration evidence |
| R-TRAIN | `COHORT_APPROVAL_MISSING` | Approved train-event Stage-2.1 records | Human review required; legacy records cannot be reused | Human researcher; `BLOCKED_BY_MISSING_EVIDENCE` | Schema `8.1.0-stage2.1`, promotion validation/receipt |
| R-NOTRAIN | `COHORT_APPROVAL_MISSING` | Approved negative-control records | Human review and no-train evidence required | Human researcher; `BLOCKED_BY_MISSING_EVIDENCE` | Stage-2.1 records + cohort coverage |
| R-ENGINE | `COHORT_APPROVAL_MISSING` | Engine-event treatment | Isolate/case-study/pool only if researcher decides; no silent denominator inclusion | Researcher; `BLOCKED_BY_AUTHORITY` | Approved record plus explicit analysis framing |
| R-GT | `STAGE21_RECORDS_MISSING` | Active approved ground truth and promotion | Legacy schema-6.0 records are invalidated; candidates are not labels | Human researcher; `BLOCKED_BY_MISSING_EVIDENCE` | Stage-2.1 records, allowlist, media hashes, receipt |
| R-MANIFEST | `MANIFEST_MISSING` | Derived Phase 12 input manifest | Built only after decisions/payloads exist; never hand-authored | Engineering after decisions | `phase12-evaluation-inputs/1`; `manifest_builder` |
| R-CACHE | downstream evidence gap | Eligible cache artifacts/provenance | Frozen model outputs only, hash-bound, no raw-media fallback | Authorized engineering | Cache manifest `1.0.0`, JSONL hashes/counts/provenance |
| R-AUTH | `EVAL_AUTH_NOT_GRANTED` | Official execution authorization | Named stage, scope, and all live bindings | Researcher; `BLOCKED_BY_AUTHORITY` | `data/governance/eval_authorization.json`; `verify_eval_authorization` |

## 5. Protocol and endpoint package

Committed HEAD contains protocol v8.0.0 / ground-truth v6.0.0; the worktree contains v9.0.0
/ground-truth v7.0.0. The worktree revision retires R03 as a separate site-survey blocker and
adds the operational danger-zone convention; both preserve R04 independent clocks. No choice
is made here.

The two premature-opening definitions are documented in
`docs/PREMATURE_OPENING_DECISION_EVIDENCE.md`:

| Option | Semantics | Evidence/clock requirement | Current status |
|---|---|---|---|
| v9 | Opening command while `T1 <= t < T4`; T1 front, T4 back | Accepted fused timeline required | `PROPOSED_NOT_APPROVED`; no default |
| M4 | Opening or blocked-to-unblocked behavior in `(t_blocked, T4)`; paired M5 | T4 back clock and M4 trace logic | `PROPOSED_NOT_APPROVED`; no default |

Neither is evaluable on front-only replay. M4 remains the code-level name and is not redefined.
Use `PROTOCOL_AUTHORITY_DECISION_DRAFT.md` and `PREMATURE_OPENING_DECISION_DRAFT.md`.

## 6. Split decision package

The existing `data/splits/705d388743ea/` is an image/dataset split, not a Phase 12 event
split. The required event decision file is absent. Existing research documents support these
options:

1. Full-cohort descriptive benchmark with no held-out generalization claim.
2. Two-session exploratory contrast with severe imbalance/confounding caveat.
3. Defer until multi-crossing data exists.

Do not promote the image-level split. Use `EVENT_SPLIT_DECISION_DRAFT.md`; do not write it
to the authoritative path.

## 7. R04 package

`governance.py` requires an explicit per-event mode map and accepted-sync set. The candidate
calibration manifest is evidence only; it is not an R04 decision or official acceptance.
`configs/frozen_experiment_v1.yaml` explicitly disallows unverified zero offsets. Use
`R04_SCOPE_DECISION_DRAFT.md`; preserve blocked status for unsupported/uncertain events.

## 8. Stage-2.1 ground-truth package

The active schema is `8.1.0-stage2.1`; the review loader and promotion gate require reviewer
attribution, minimum duration floor, model-independence attestation, observed-media hashes,
four-state boundary adjudications, rationales, history, allowlist, proposal/media bindings,
and live promotion checks. Current review files are legacy schema 6.0.0 and invalidated;
proposal files remain candidate evidence. Use `STAGE21_GROUND_TRUTH_CHECKLIST.md` only as a
workflow aid. Do not modify reviews, promote proposals, or create receipts.

## 9. Cache and EVAL-AUTH package

Use `CACHE_PRODUCTION_AND_PROVENANCE_CHECKLIST.md` for future authorized cache generation.
Potential producer scripts are explicitly not to be run during this audit because static source
inspection shows raw-media/model/write side effects.

Use `EVAL_AUTH_CHECKLIST.md` for the actual `phase12-eval-authorization/1` requirements.
`leg_exec_authorization.json` is a separate legacy operation and cannot substitute for EVAL-AUTH.

## 10. Safe validation and results

Executed:

```text
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/unit/test_phase12_governance.py \
  tests/unit/test_readiness_audit.py \
  tests/test_phase11_12_readiness_cli.py \
  tests/test_phase11_12_readiness_gate.py \
  tests/unit/test_phase12_input_contracts.py -q
```

Result: **121 passed**, synthetic/metadata-only.

```text
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/unit/test_phase12_documented_metrics.py \
  tests/unit/test_phase12_metric_arithmetic.py -q
```

Result: **28 passed**, synthetic-only.

The cache/adapter and broader synthetic suites were previously validated in the current
repository reports; this mission did not rerun official or media-accessing commands. An
attempted nonexistent historical test path produced no tests and is not counted as a pass.

No engineering repair was necessary; changing any current gate criteria would be an authority
or scientific-contract change.

## 11. Ordered researcher action sequence

1. Select effective protocol version.
2. Select premature-opening definition.
3. Select event-level analysis/split framing.
4. Select per-event R04 scope and accepted synchronization.
5. Authorize and conduct genuine Stage-2.1 human adjudication across required cohorts.
6. Complete promotion/readiness receipt and recompute metric eligibility.
7. Authorize frozen-model cache production under a separately approved media operation.
8. Validate cache manifest and provenance.
9. Record EVAL-AUTH against all final live bindings.
10. Only then consider official evaluation.

## 12. Honest completion statement

This package is a decision-ready, unsigned research-governance handoff. It does not make any
research decision, does not alter official readiness, and does not authorize execution. Train
Gate Automation remains `BLOCKED_BY_AUTHORITY` and `BLOCKED_BY_MISSING_EVIDENCE` for empirical
evaluation.

