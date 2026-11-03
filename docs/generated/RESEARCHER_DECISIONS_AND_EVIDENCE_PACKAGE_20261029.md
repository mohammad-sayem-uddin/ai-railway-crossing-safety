# Researcher Decisions & Evidence Package — D1/D2/D3/D4 Preparation

**Date:** 2026-10-29 UTC
**Status:** `PROPOSED_NOT_APPROVED`

## Live status

HEAD `d4db94d` / `main`; existing work preserved. Live readiness is `False` with 9 blockers.
No media, inference, cache generation, promotion, EVAL-AUTH, or official evaluation occurred.

## D1 — Protocol authority

HEAD documents are v8.0.0/v6.0.0; worktree documents are v9.0.0/v7.0.0. Worktree changes
R03/site-survey treatment and operational danger-zone wording; R04 independent clocks remain
unresolved. No authority selected.

Existing workflow: researcher-authored `phase12-protocol-decision/1` with exact schema,
`decision_status=APPROVED`, decision ID, allowlisted `decided_by`, UTC date, statement,
`choices`, and validation via `governance.verify_protocol_override()`.

## D2 — M4

M4 is `first_blocked_to_t4_clearance` (`metrics.py:94-122`): first blocked replay step; strict
interval before approved T4; opening/unblocked behavior is premature; no blocked step before T4
is M5 `never_protected`, not M4 zero success. T4 is back-camera evidence. Missing/censored/
uncertain/un-aligned T4 is not evaluable. v9 instead uses `T1 <= t < T4`, requiring approved
front T1/back T4 on an accepted common timeline.

M4 is implemented as an option but not selected; no default profile exists. M4 requires a
researcher protocol choice and valid approved T4 evidence.

## D3 — Descriptive-only contract

The proposed `full_cohort_descriptive` concept remains synthetic-only and isolated. It must not
enter the official input manifest, bypass train/val/test validation, or claim held-out performance.
The current synthetic component aggregates typed event evaluations only.

## D4 — R04 scope

Contract supports per-event `single_camera`, `independent_camera`, and `dual_camera`; dual
requires accepted-sync membership. Candidate calibration is evidence only. No unverified zero
offset or invented tolerance is permitted. T4 requires back-clock evidence where metrics need it.

## Ground truth/cohorts

Current reviews: 27 legacy schema-6.0.0 records + 27 invalidation notices; no active
8.1.0-stage2.1 records. Candidates are not labels. Required human work includes allowlisted
reviewer, minimum duration, model-independence, observed media hashes, four-state boundaries,
rationales, history, proposal/media bindings, and promotion receipt.

Engine event should remain isolated unless the researcher separately approves pooling criteria.

## Readiness blockers

| Blocker | Required next artifact/evidence | Responsible |
|---|---|---|
| Cohort approvals ×3 | Active valid Stage-2.1 records | Human researcher/reviewer |
| EVAL-AUTH | `eval_authorization.json` with live seven bindings | Researcher |
| Split | `phase12-event-split-decision/1` | Researcher |
| Manifest | Derived `phase12-evaluation-inputs/1` | Engineering after decisions |
| Premature profile | Protocol decision choice | Researcher |
| R04 | `phase12-r04-scope-decision/1` | Researcher |
| Stage-2.1 | Review/adjudication + receipt | Human/researcher |
| Caches | Authorized production + manifest/provenance | Authorized engineering |

## Validation

```text
.venv/pytest tests/unit/test_descriptive_only.py tests/unit/test_cache_phase12_adapter.py tests/unit/test_cache_only_replay.py -q
118 passed

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_phase12_governance.py tests/unit/test_readiness_audit.py tests/test_phase11_12_readiness_cli.py tests/test_phase11_12_readiness_gate.py tests/unit/test_phase12_input_contracts.py tests/unit/test_phase12_documented_metrics.py tests/unit/test_phase12_metric_arithmetic.py -q
149 passed
```

No official artifact was created. No gate criterion changed.
