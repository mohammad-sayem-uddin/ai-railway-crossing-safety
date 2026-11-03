# RESEARCH PROPOSAL — NOT APPROVED — NOT AUTHORIZATION

# Train Gate Automation — Descriptive-Only Mode Specification Proposal

**Date:** 2026-10-27 UTC
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`
**HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
**Status:** `PROPOSED_NOT_APPROVED`

## 1. Executive summary

The repository documents a scientifically defensible fixed-site descriptive B0/B1/B2 analysis,
but the current official Phase 12 contract requires exactly nonempty, disjoint `train`, `val`,
and `test` partitions and evaluates only `event_split["test"]`. This proposal defines a
**separate descriptive-only mode concept** without changing or bypassing the current official
validator, manifest builder, runner, or readiness gate.

The proposal is not implemented, accepted, or executable. Its purpose is to give the researcher
and independent architecture reviewer a precise contract to accept, amend, or reject.

## 2. Verified current architecture

Source-verified:

- `research_contracts.validate_event_level_split()` requires exact train/val/test keys,
  nonempty partitions, valid IDs, no within-partition duplicates, and no cross-partition overlap.
- `evaluation.input_contracts` repeats partition and identity constraints.
- `manifest_builder.build_evaluation_input_manifest()` requires verified split/R04 decisions,
  exact event-source coverage, and writes `phase12-evaluation-inputs/1` with real classification.
- `Phase12EvaluationRunner.run()` validates the split and evaluates only `event_split["test"]`.
- The official gate/runner require approved Stage-2.1 evidence, protocol/split/R04 artifacts,
  frozen bindings, and EVAL-AUTH.
- No descriptive-only mode or `evaluation_mode` field exists in current official contracts.

## 3. Proposed scientific purpose

**Proposed mode purpose:** characterize replay-derived detector, fusion, sensor-health, and
simulated gate behavior over an explicitly declared, approved fixed-site population, without
claiming held-out generalization, cross-crossing robustness, deployment safety, or physical
actuator performance.

Permitted claims would be limited to observed events, approved evidence, declared cohorts,
configuration/checkpoint identities, and declared censoring/exclusion rules. The mode would not
be used for model selection/tuning on the same reported population without disclosure, and would
not be represented as a held-out test evaluation.

This purpose does not eliminate selection bias, session leakage, threshold tuning leakage,
left-censoring, small negative-control limitations, or missing T4/R04 evidence.

## 4. Proposed contract (not implemented)

### Mode identity

Proposed identifier: `full_cohort_descriptive`.

This is a proposed value only. It does not exist in the official schema. A future contract would
need an explicit mode field, separate validation/reporting, and an unmistakable non-official
classification. It must not be accepted by current `phase12-evaluation-inputs/1` without an
approved schema change.

### Population and eligibility

A future descriptive manifest should require approved cohort-qualified event identities, a
researcher-approved inclusion/exclusion declaration, Stage-2.1 approval where a metric needs
boundaries, explicit censoring/uncertainty/missing-evidence states, cache/replay provenance,
and frozen configuration identity. Eligibility must never be inferred from filenames, candidate
proposals, or model output. No event list is proposed because no approved event decision exists.

### Split-handling alternatives

1. **Preserve the split contract for official work:** retain a genuine event split and optionally
   summarize approved events descriptively, reporting split/leakage limitations.
2. **Separate descriptive manifest:** new approved contract with an eligible-event list and
   population declaration, never consumed by the current official runner.
3. **Amend official contract:** add a formal descriptive mode to existing inputs; highest
   backward-compatibility and governance risk.

No option is selected.

## 5. Candidate metrics and evidence

| Candidate output | Required evidence | Limitation |
|---|---|---|
| B0 front vision | front vision cache + replay | descriptive only; no generalization |
| B1 front audio | front audio cache + replay | audio cannot authorize clearance/opening |
| B2 front fusion | both front caches + replay | frozen policy/provenance required |
| Missed train / warning lead | approved observable T1 + eligible simulation step | left-censoring/missing T1 excludes events |
| M4 | selected M4 profile, blocked replay step, approved T4/back clock | not front-only evaluable; M5 companion |
| v9 premature opening | selected v9 profile, approved T1/T4, accepted fused clock | R04/fused timeline required |
| Clearance latency | approved T4/back clock and compatible timeline | not front-only evaluable |
| False alarms | approved no-train cohort and exposure | three controls; no hourly extrapolation |

Censored, uncertain, missing, and clock-mismatched evidence must be reported as not-evaluable
with reasons. M4 remains `first_blocked_to_t4_clearance`; no definition is selected here.

## 6. Provenance and leakage safeguards

A future descriptive mode would bind frozen configuration, decision policy, vision and Audio V3
checkpoint hashes, thresholds, run identity, cache manifest/artifact hashes, approved population,
protocol profile, limitations, and permitted-claims text. It must report duplicate identities,
session/crossing overlap, repeated development use, selection criteria, censored events, missing
boundaries, and tuning on the reported population. Descriptive labeling does not remove these
risks.

## 7. Separation from official Phase 12

The existing official path must remain unchanged:

1. `validate_event_level_split()` remains unchanged.
2. `manifest_builder` continues requiring current researcher-approved split/R04 artifacts.
3. `Phase12EvaluationRunner` continues selecting `event_split["test"]`.
4. A descriptive proposal cannot satisfy official readiness.
5. A descriptive result cannot be serialized as a held-out test result.
6. Shared utilities must not bypass official validation via a flag or alternate caller path.
7. EVAL-AUTH is not implied by design/implementation approval.

The safest proposed boundary is a separate descriptive input/reporting contract and entrypoint,
not a hidden branch in the official runner. Architecture review is required before implementation.

## 8. Conceptual schema — illustrative only

```json
{
  "schema_version": "PROPOSED-descriptive-only/1",
  "mode": "full_cohort_descriptive",
  "status": "PROPOSED_NOT_APPROVED",
  "study_scope": {"site": "<researcher-approved site>", "population_reference": "<artifact>"},
  "eligible_events": ["<approved cohort-qualified event IDs>"],
  "inclusion_exclusions": {"rules": [], "excluded_events_with_reasons": []},
  "protocol_profile_sha256": "<bound only after approval>",
  "ground_truth_references": [],
  "metric_profile": {"metrics": [], "censoring_policy": "<approved policy>"},
  "configuration_provenance": {},
  "limitations": [],
  "permitted_claims": [],
  "researcher_approval_reference": "<required after approval>"
}
```

`ILLUSTRATIVE_ONLY_NOT_A_VALID_INPUT`: this example is not accepted by the current official
loader, is not an approved schema, and must not be saved under an authoritative manifest path.
Fields above are proposed extensions, not existing contract fields, except where their underlying
concepts reuse existing provenance/ground-truth contracts.

## 9. Approval and implementation gates

1. **Researcher scientific scope:** approve purpose, population, claims, metrics, and limitations.
2. **Protocol/contract authority:** resolve D1/D2 and authorize a separate descriptive contract.
3. **Independent architecture review:** verify no official-runner bypass and separate provenance.
4. **Schema/test approval:** approve fields, refusals, output labeling, and compatibility rules.
5. **Authorized implementation:** separate mission; no official activation by default.
6. **Synthetic validation:** test separation, provenance, refusal, leakage reporting, and no media.
7. **Evidence/authorization:** Stage-2.1, cache, manifest, R04, and EVAL-AUTH requirements
   must be satisfied separately before any real-data action.

Creating this proposal does not pass any gate.

## 10. Alternatives matrix

| Option | Contract fit | Scientific fit | Leakage/claims risk | Scope | Recommendation status |
|---|---|---|---|---|---|
| Preserve current split | Existing contract | Useful only with valid event split and limited claims | Depends on grouping; no current approved split | Low contract work | `PROPOSED_NOT_APPROVED` |
| Separate descriptive mode | Does not alter official contract | Best fit for fixed-site descriptive goal | Requires strict non-generalization/provenance/reporting | New contract + review | `PROPOSED_NOT_APPROVED` (recommended engineering direction) |
| Amend official contract | Changes official semantics | Could support full cohort if approved | Highest compatibility/governance risk | Schema/runner/gate migration | `BLOCKED_BY_AUTHORITY` |
| Defer | Fully compatible | No unsupported claims | No new risk | No implementation | `PROPOSED_NOT_APPROVED` |

The recommendation for discussion is a separately governed descriptive mode rather than weakening
the existing validator. This is an engineering recommendation, not a researcher decision.

## 11. Blank researcher approval form

**Status:** `PENDING_RESEARCHER_DECISION`

Purpose accepted: ________________________________________________
Population/site scope: ___________________________________________
Permitted claims: ________________________________________________
Candidate metrics/evidence: ______________________________________
Relationship to official Phase 12 split contract: _________________
Separate contract design authorized? [ ] yes [ ] no
Independent reviewer: _____________________________________________
Protocol/schema versioning requirement: ____________________________
Known risks/unresolved questions: _________________________________

Researcher decision: _____________________________________________
Researcher rationale: ____________________________________________
Authorized decision-maker: _______________________________________
Date: ___________________________________________________________
Required downstream approvals: ___________________________________

This form does not create an authoritative mode or authorization.

## 12. Current readiness and next action

Current gate: `ready=False`, **9 blockers**. No official artifact or real cache exists. The next
safe action is researcher approval/rejection of this proposed contract direction and explicit
resolution of D1/D2/D3/D4; implementation must wait for that decision and architecture review.
