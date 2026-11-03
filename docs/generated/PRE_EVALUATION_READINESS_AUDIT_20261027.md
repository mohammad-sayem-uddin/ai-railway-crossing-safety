# Train Gate Automation — Pre-Evaluation Readiness & Governance Audit

**Date:** 2026-10-27 (UTC)
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`
**Branch / HEAD:** `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
**Labels:** `VERIFIED`, `TESTED_SYNTHETICALLY`, `BLOCKED_BY_AUTHORITY`, `BLOCKED_BY_MISSING_EVIDENCE`, `BLOCKED_BY_ENGINEERING_DEFECT`, `NOT_VERIFIED`

## 1. Executive summary and overall decision

The repository is **not ready for empirical evaluation**. The engineering foundation is
substantially implemented and synthetic governance/readiness checks pass, but the live
official readiness gate currently reports `ready=False` with **9 blockers**:

- no valid active Stage-2.1 records (27 legacy schema-6.0.0 records are invalidated);
- no researcher event-split decision;
- no R04 scope decision;
- no derived Phase 12 input manifest;
- no protocol decision artifact / premature-opening choice;
- no Stage-2.1 promotion receipt;
- no EVAL-AUTH record;
- no approved evidence suitable for official evaluation;
- no real cache artifact manifest.

No official benchmark, inference, timing pilot, cache generation, or source-media access was
performed. No approval, label, hash, result, or protocol decision was fabricated.

## 2. Verified repository state

- Root: `/Users/sayemuddin/Desktop/Train_automation`.
- Branch/HEAD: `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`.
- Python: system 3.14.4; project `.venv` Python 3.11.15.
- Worktree: 19 tracked modifications and extensive pre-existing untracked research artifacts;
  no staged entries. All preserved.
- No stage/commit/push/reset/clean/broad revert/delete operations performed.
- No `.mov`, `.mp4`, or `.wav` file opened, decoded, previewed, played, or hashed.
- Existing cache implementation, independent review, and Phase 12 adapter reports were read.
- Official producer/runner remain disconnected from the standalone cache adapter.

## 3. Protocol-authority matrix

| Artifact | Committed HEAD | Working tree | Status/effect |
|---|---|---|---|
| `FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` | v8.0.0 | v9.0.0 | unresolved authority conflict |
| `FINAL_GROUND_TRUTH_PROTOCOL.md` | v6.0.0 | v7.0.0 | unresolved authority conflict |
| `FINAL_EXPERIMENT_DATA_FLOW.md` | v6.0.0 | v7.0.0 | follows worktree proposal |
| `FINAL_ABLATION_MATRIX.md` | v6.0.0 | v7.0.0 | follows worktree proposal |

The worktree revision retires R03 as a separate site-survey blocker and introduces an
operational danger-zone convention, while preserving unresolved R04 independent camera clocks.
The committed revision retains R03/R04 prerequisite wording. No effective version was selected.

### Unresolved decision register

| Decision | Repository-supported options | Implication | Required approval |
|---|---|---|---|
| Effective protocol set | HEAD v8/v6; worktree v9/v7 | Changes R03, annotation convention, prerequisites | Researcher protocol decision |
| Premature opening | `t1_entry_to_t4_clearance`; `first_blocked_to_t4_clearance` (M4) | Changes safety metric definition/eligibility | Researcher decision bound to EVAL-AUTH |
| Event split | Researcher-authored `phase12-event-split-decision/1` | Determines test eligibility/leakage claims | Researcher split decision |
| R04 scope | Per-event single/independent/accepted dual camera | Determines clock comparability | Researcher R04 decision |
| Ground truth | Stage-2.1 human adjudication/promotion | Determines official metric eligibility | Human review + receipt |
| Official execution | EVAL-AUTH bound to live hashes | Authorizes named official stage | Researcher EVAL-AUTH |

No document date, modified time, or agent-authored report was treated as authority.

## 4. Ground-truth readiness matrix

| Requirement | Existing evidence | Status | Next action |
|---|---|---|---|
| Stage-2.1 schema `8.1.0-stage2.1` | 27 review JSON files are schema `6.0.0`; 27 invalidation notices exist | `BLOCKED_BY_MISSING_EVIDENCE` | Genuine Stage-2.1 review/adjudication |
| Valid reviewer/approval | Legacy APPROVED fields are invalidated/blocklisted | `BLOCKED_BY_AUTHORITY` | Do not rely on legacy fields; use authorized workflow |
| Candidate proposals | 61 proposal JSONs exist; candidate schemas vary | `NOT_OFFICIAL` | Preserve; never auto-promote |
| Temporal fields/censoring | Active approved records absent | `BLOCKED_BY_MISSING_EVIDENCE` | Human adjudicates four-state boundary status |
| Boundary camera provenance | Candidate/R04 artifacts only | `BLOCKED_BY_AUTHORITY` | Approved records must carry reference-camera fields |
| Reviewed-media hashes | No acceptable active Stage-2.1 evidence | `BLOCKED_BY_MISSING_EVIDENCE` | Authorized review records observed-media hashes |
| Review history/independence | Required active records absent | `BLOCKED_BY_MISSING_EVIDENCE` | Complete schema-required review history |
| Cohort coverage | Gate requires train/no-train/engine approvals; none valid | `BLOCKED_BY_MISSING_EVIDENCE` | Valid approved records or approved exclusions |
| Promotion receipt | `data/governance/stage21_promotion_receipt.json` missing | `BLOCKED_BY_MISSING_EVIDENCE` | Authorized promotion workflow after prerequisites |
| Official eligibility | No active approved records | `NOT_VERIFIED` | Recompute only from approved records |

`ground_truth_loader.py` fail-closes on non-8.1.0 schema, candidate shape, non-APPROVED
status, duplicate IDs, and non-observable boundaries. No labels were modified.

## 5. EVAL-AUTH and official readiness

The actual read-only `execution_gate.assess_official_phase12_readiness()` assessment produced:

```text
READY False
BLOCKERS 9
COHORT_APPROVAL_MISSING: no approved engine_events record
COHORT_APPROVAL_MISSING: no approved no_train_events record
COHORT_APPROVAL_MISSING: no approved train_events record
EVAL_AUTH_NOT_GRANTED: no recorded EVAL-AUTH at data/governance/eval_authorization.json
EVENT_SPLIT_DECISION_MISSING
MANIFEST_MISSING: data/manifests/phase12_evaluation_inputs.json
PREMATURE_OPENING_DEFINITION_UNDECIDED
R04_SCOPE_DECISION_MISSING
STAGE21_RECORDS_MISSING: no active review records; 27 legacy records invalidated
```

| Prerequisite | Contract requirement | Evidence/status | Fix class |
|---|---|---|---|
| Frozen config integrity | Required | Live binding/hash present | `VERIFIED` mechanically |
| Decision policy integrity | Required | Gate validates config reference | `VERIFIED` mechanically |
| Valid Stage-2.1 records | Required | None active | human/research evidence |
| Cohort approvals | Required | All three missing | human/research evidence |
| Split decision | Required | Missing | researcher decision |
| R04 scope decision | Required | Missing | researcher decision |
| Protocol decision/profile | Required for unresolved profile | Missing; premature window undecided | researcher decision |
| Derived input manifest | Required | Missing | engineering derivation after decisions |
| Promotion receipt | Required | Missing | authorized governance workflow |
| EVAL-AUTH | Required | Missing | researcher authorization |
| Valid real evidence/cache provenance | Required official input | absent | authorized engineering + provenance |

`leg_exec_authorization.json` exists but authorizes a distinct legacy invalidation operation;
it is not EVAL-AUTH and is not used as such. No readiness flag was fabricated.

## 6. Cache-production runbook (not executed)

The cache design requires front-vision and front-audio JSONL records, manifest version 1.0.0,
cohort/event identity, relative paths, line counts, byte sizes, SHA-256 hashes, finite ordered
timestamps, and (for official payload provenance) frozen config/checkpoint/threshold/media/run
bindings. B0/B1/B2 semantics are front vision, front audio, and both respectively.

The following potential producers were inspected and are **NOT TO BE RUN DURING THIS MISSION**:

```text
scripts/run_phase5_full_inference.py
scripts/run_real_world_experiments.py
scripts/run_exploratory_dual_camera_subset.py
scripts/run_phase9_diagnostic_replay.py
```

The design and source audit identify cache-miss fallthrough to video frame generation, audio
extraction/ffmpeg, model loading, and repository writes in legacy routes. No safe production
command is asserted here. Future authorized production requires approved protocol/split/R04
decisions, frozen checkpoint verification, explicit media-authorized inference, hash-bound
cache manifest construction, independent cache-only validation, and EVAL-AUTH binding.

No cache generation, inference, or media access occurred.

## 7. Metric-by-metric readiness

| Metric/condition | Required evidence | Current status |
|---|---|---|
| B0 | Valid front-vision cache + replay | Software `VERIFIED`; empirical `BLOCKED_BY_MISSING_EVIDENCE` |
| B1 | Valid front-audio-only cache + replay | Software `VERIFIED`; empirical `BLOCKED_BY_MISSING_EVIDENCE` |
| B2 | Both front caches + frozen provenance | Software `VERIFIED`; empirical `BLOCKED_BY_MISSING_EVIDENCE` |
| M4 | `first_blocked_to_t4_clearance`, T4 on compatible timeline, selected profile | `BLOCKED_BY_AUTHORITY` |
| M5 | T4 and blocked-step evidence | `NOT_VERIFIED` |
| Missed train | Approved T1/censoring state + replay | `BLOCKED_BY_MISSING_EVIDENCE` |
| Warning lead | Approved observable T1 + replay | `BLOCKED_BY_MISSING_EVIDENCE` |
| Premature opening | T1/T4 clocks + selected profile | `BLOCKED_BY_AUTHORITY` / R04 |
| Clearance latency | Approved back-clock T4 + synchronization | `BLOCKED_BY_MISSING_EVIDENCE` |
| False alarms | Approved no-train cohort + exposure | `BLOCKED_BY_MISSING_EVIDENCE` |

M4 remains `first_blocked_to_t4_clearance` (`metrics.py:94`). The metric specification
explicitly states T4 is on `camera_back` and front-only replay cannot satisfy cross-clock
metrics. No official results were produced.

## 8. Data split and generalization audit

`data/splits/705d388743ea/` contains image/dataset JSONL files, not a researcher-authored
cohort-qualified Phase 12 event split. `data/splits/phase12_event_split_decision.json` is
missing. Therefore the existing split cannot be promoted to an approved Phase 12 split.

The active specification documents one crossing (`crossing_A`), limited sessions, left-censored
train events, three no-train controls, and explicit limits on leakage-safe generalization claims.
Required event/session grouping metadata and an approved decision artifact are absent, so no
safe metadata-only calculation can establish a group-disjoint evaluation split.

Status: `BLOCKED_BY_AUTHORITY` / `BLOCKED_BY_MISSING_EVIDENCE`.

## 9. Safe validation executed

Executed metadata-only readiness assessment:

```text
PYTHONPATH=src .venv/bin/python - <<'PY'
from pathlib import Path
from railway_detection.evaluation.execution_gate import assess_official_phase12_readiness
v = assess_official_phase12_readiness(Path('.'))
print(v.ready, len(v.blockers))
PY
```

Result: `ready=False`, 9 blockers; metadata-only, no media.

Synthetic/metadata-only governance tests:

```text
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/unit/test_phase12_governance.py \
  tests/unit/test_readiness_audit.py \
  tests/test_phase11_12_readiness_cli.py \
  tests/test_phase11_12_readiness_gate.py \
  tests/unit/test_phase12_input_contracts.py -q
```

Result: **121 passed**.

Metric tests:

```text
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/unit/test_phase12_documented_metrics.py \
  tests/unit/test_phase12_metric_arithmetic.py -q
```

Result: **28 passed**.

An attempted command referencing nonexistent `tests/unit/test_phase11_2_stage21_promotion_gate.py`
reported “file or directory not found; no tests ran”; it is recorded as a skipped historical
path, not a pass. No official evaluation, inference, cache generation, timing pilot, or raw-
media command was run.

## 10. Engineering fixes and regression status

No readiness/governance code defect was found that could be safely fixed without changing
research authority. No protocol, ground truth, split, EVAL-AUTH, calibration, frozen policy,
or protected report was changed. No engineering repair was necessary in this audit.

## 11. Outstanding decisions and next safe steps

### Researcher decisions

1. Select effective protocol authority (HEAD v8/v6 versus worktree v9/v7).
2. Select premature-opening profile.
3. Author event-level split with session/crossing leakage position.
4. Author per-event R04 scope and accepted synchronization set.
5. Complete genuine Stage-2.1 human adjudication and promotion.
6. Decide whether/when official cache production is authorized.
7. Record EVAL-AUTH only after all live bindings exist.

### Safe engineering

1. Maintain synthetic cache/adapter/governance regression tests.
2. Add metadata-only blocker summaries without modifying research artifacts.
3. Prepare, but do not activate, an authorized cache-production wrapper after side effects and
   media access are explicitly approved.
4. Add group/session metadata validation once an event-level decision artifact exists.

### Explicitly not to run during this mission

- Raw-media inference or replay.
- Cache-generation scripts.
- Official `evaluation run`.
- Timing pilots or field capture.
- Ground-truth promotion/invalidation execution.
- Candidate calibration promotion.

## 12. Honest overall readiness decision

**Train Gate Automation is not ready for empirical evaluation.**

Software readiness is substantial and synthetic governance/readiness behavior is tested, but
scientific validity and execution authorization are absent. The next legitimate milestone is
researcher-authorized protocol selection, event-level split and R04 decisions, genuine
Stage-2.1 adjudication/promotion, and only then an explicitly authorized cache-production and
provenance process. EVAL-AUTH must bind final live hashes before any official run.
