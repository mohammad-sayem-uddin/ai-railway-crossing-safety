# Train Gate Automation — D3 Contract Resolution & Researcher Decision Preparation

**Date:** 2026-10-27 UTC
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`
**HEAD/branch:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` / `main`
**Status:** `PROPOSED_NOT_APPROVED` — no contract or decision changed
**Labels:** `VERIFIED`, `PROPOSED_NOT_APPROVED`, `BLOCKED_BY_AUTHORITY`, `BLOCKED_BY_MISSING_EVIDENCE`, `NOT_VERIFIED`

## 1. Executive summary

The intended **full-cohort descriptive benchmark** is scientifically documented as a fixed-site
descriptive option, but it does **not** fit the current Phase 12 execution contract as currently
implemented. The current contract requires exactly nonempty, disjoint `train`, `val`, and `test`
partitions of event IDs. `Phase12EvaluationRunner.run()` then evaluates only `event_split["test"]`.
`manifest_builder.py` requires a verified researcher split decision and exact source coverage.

Therefore the researcher’s D3 preference is:

- `CONSISTENT_WITH_CONTRACT` as a scientific/reporting framing only if explicitly scoped as
  descriptive and non-generalizing;
- `CONFLICTS_WITH_CONTRACT` with the current official Phase 12 split/input contract unless a
  researcher-authorized descriptive-mode contract amendment is made;
- `BLOCKED_BY_AUTHORITY` until the researcher chooses a supported framing or authorizes an
  explicit contract amendment.

No validator/schema/readiness criterion was changed. No event membership was invented.

## 2. Verified repository state and live gate

- Root: `/Users/sayemuddin/Desktop/Train_automation`.
- Branch/HEAD: `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`.
- No staged changes; all existing work preserved.
- No original media accessed.
- Required event-level and official artifacts are absent:

```text
data/splits/phase12_event_split_decision.json
 data/manifests/phase12_evaluation_inputs.json
 data/manifests/phase12_protocol_decision.json
 data/manifests/phase12_r04_scope_decision.json
 data/governance/stage21_promotion_receipt.json
 data/governance/eval_authorization.json
```

Live metadata-only gate:

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

## 3. Exact current split contract

`src/railway_detection/research_contracts.py:validate_event_level_split()` requires:

1. Input is a mapping.
2. Keys are exactly `train`, `val`, and `test`.
3. Each partition is a nonempty sequence.
4. Every event ID is a nonempty, trimmed string.
5. No duplicate ID within a partition.
6. No event ID appears across partitions.

This is a mechanical contract only; its docstring explicitly says it does not approve a split
or make an image/frame split suitable for evaluation.

Downstream enforcement:

- `governance.check_split_body()` calls this validator for the researcher decision artifact.
- `manifest_builder.build_evaluation_input_manifest()` requires the verified split decision,
  requires event sources to equal the decided event set, and emits `partitions` into the
  `phase12-evaluation-inputs/1` manifest.
- `Phase12EvaluationRunner.run()` calls the validator and then constructs `test_events =
  list(event_split["test"])`; missing/extra replay and ground-truth records are refused.
- `evaluation/input_contracts.py` requires exactly train/val/test partitions and checks duplicate
  and cross-partition leakage.

No current code path supports a full-cohort partition without train/val/test. No
`full_cohort_descriptive` mode exists in the current schema or validator.

## 4. Meaning of “full-cohort descriptive”

The phrase has three materially different interpretations:

| Interpretation | Compatible now? | Claim boundary |
|---|---|---|
| Report all eligible events descriptively, with no held-out claim, outside official Phase 12 runner | Potentially, as a separate descriptive analysis only; not an official runner result | Fixed-site operational characterization; no generalization |
| Use a train/val/test split for contract compliance but summarize all partitions descriptively | Mechanically compatible if a genuine researcher-approved event split exists | Split-specific plus aggregate descriptive summaries; still no leakage-safe generalization without grouping evidence |
| Treat all events as official Phase 12 test input with no train/val/test partition | **Not compatible** with current validator/manifest/runner | Requires contract amendment or separate approved mode |

The active B0/B1/B2 design review supports full-cohort descriptive characterization but explicitly
rejects cross-crossing generalization claims and warns of two-session/single-crossing leakage.
That scientific recommendation does not automatically amend the execution contract.

## 5. D3 option comparison

| Option | Contract compatibility | Scientific validity | Leakage risk | Implementation scope | Official readiness impact | Status |
|---|---|---|---|---|---|---|
| A — Preserve current split contract | Compatible only with a real nonempty disjoint event split | Supports split-specific descriptive reporting; claims limited | Depends on researcher grouping decision; current image split is insufficient | No contract change; requires researcher event decision and approved GT | Can feed current manifest/runner after all gates | `PROPOSED_NOT_APPROVED` |
| B — Add separate descriptive-only mode | Would require new mode/schema/runner semantics; current code does not support it | Best fit for full-cohort fixed-site characterization if explicitly bounded | Must prohibit held-out/generalization claims and define GT/provenance | New contract, validator, tests, reports, gate bindings | Must remain separate from official runner until approved | `PROPOSED_NOT_APPROVED`, `BLOCKED_BY_AUTHORITY` |
| C — Formal contract amendment | Explicitly changes current official contract | Could support full cohort only with researcher-approved scientific scope | Requires new leakage/reporting safeguards; backward compatibility risk | Schema/validator/manifest/runner/gate migration and independent review | Existing official readiness cannot change until amendment is approved/bound | `BLOCKED_BY_AUTHORITY` |
| D — Defer | Fully compatible; no execution | Avoids unsupported claims while evidence/design matures | No new leakage risk | No code change | Remains blocked | `PROPOSED_NOT_APPROVED` |

**Source-derived conclusion:** Option A cannot represent a no-partition full-cohort input under
current code. **Engineering recommendation (not a decision):** if the researcher wants a full-
cohort descriptive milestone, prefer a separate explicitly descriptive contract/mode (Option B)
over weakening `validate_event_level_split()`; otherwise use Option D.

## 6. D3 researcher decision form — blank

**Decision ID:** `D3`
**Status:** `PENDING_RESEARCHER_DECISION`
**Decision-maker:** ____________________
**Decision date (UTC):** ____________________

Selected option:

- [ ] A — Preserve current train/val/test event-level contract.
- [ ] B — Authorize a separate descriptive-only mode proposal.
- [ ] C — Authorize a formal contract amendment proposal.
- [ ] D — Defer empirical analysis.

If A, researcher-authored partition/framing statement: ______________________________
If B/C, intended schema/mode scope: _______________________________________________
Scientific question: ______________________________________________________________
Permitted claims: _________________________________________________________________
Leakage/generalization limitations: ________________________________________________
Supporting evidence reviewed: ____________________________________________________
Researcher rationale: ____________________________________________________________
Required approval artifact/schema: ________________________________________________
Effective contract/protocol version: _______________________________________________

No selection is written to `data/splits/phase12_event_split_decision.json`.

## 7. D1/D2/D4 preparation

### D1 protocol authority

HEAD/worktree conflicts are v8/v6 versus v9/v7 for the four disputed documents. Material
worktree changes include R03 retirement/operational danger-zone wording; R04 independent clocks
remain unresolved. No version selected. Existing workflow: researcher-authored
`phase12-protocol-decision/1`, allowlisted envelope, then validation/profile hash.

Status: `REQUIRES_RESEARCHER_CLARIFICATION` / `BLOCKED_BY_AUTHORITY`.

### D2 premature opening

`metrics.py:94-122` and `docs/PREMATURE_OPENING_DECISION_EVIDENCE.md` distinguish v9
`T1 <= t < T4` from M4 `(t_blocked, T4)` plus M5. T1 is front clock, T4 back clock;
front-only cannot evaluate either. M4 is implemented as an arithmetic option but not accepted
by the researcher and has no official default.

Status: `PROPOSED_NOT_APPROVED`, `BLOCKED_BY_AUTHORITY`, `INSUFFICIENT_EVIDENCE`.

### D4 R04 scope

`research_contracts.validate_camera_scope()` supports per-event single/independent/dual modes;
dual requires accepted-sync membership. Candidate calibration is evidence, not acceptance;
no unverified zero offset is allowed. D4 depends on D3 only for final analysis scope/claims,
not for schema mechanics.

Status: `CONSISTENT_WITH_CONTRACT` in principle, `BLOCKED_BY_AUTHORITY` for execution.

## 8. Dependency map

| Relationship | Classification | Evidence |
|---|---|---|
| D1 → protocol-bound artifacts | `HARD_DEPENDENCY` | Governance protocol decision/profile hash |
| D2 → official metric profile | `HARD_DEPENDENCY` | `protocol_choices.effective_profile()` |
| D3 → official input manifest | `HARD_DEPENDENCY` | `manifest_builder` and input contract |
| D4 → camera/input manifest | `HARD_DEPENDENCY` | `manifest_builder`/`validate_camera_scope` |
| D3 → D1 | `SOFT_DEPENDENCY` | D3 framing must state which protocol set/claims it uses; validator itself is independent |
| D3 → D4 | `SOFT_DEPENDENCY` | Analysis scope informs camera claims; modes remain contract-valid independently |
| Stage-2.1 → promotion receipt | `HARD_DEPENDENCY` | Execution gate/promotion gate |
| Decisions/GT → cache eligibility | `HARD_DEPENDENCY` | Official provenance scope |
| Cache artifacts → EVAL-AUTH | `HARD_DEPENDENCY` | Seven live binding keys |
| Synthetic tests → D1–D4 | `INDEPENDENT` | No research artifact mutation |

## 9. Safe validation

Executed during this resolution:

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

The live gate returned `ready=False` with 9 blockers. No official evaluation, inference,
cache generation, timing pilot, promotion, EVAL-AUTH, or media access occurred.

## 10. Exact next action

The researcher should resolve D1 protocol authority and D2 endpoint first, then decide D3
framing and D4 scope. If full-cohort descriptive reporting remains preferred, the next
researcher decision must explicitly choose between preserving the current three-partition
contract (with limited claims) and authorizing a separately specified descriptive-only contract
mode. No official artifact should be written until that choice is genuine and validated.
