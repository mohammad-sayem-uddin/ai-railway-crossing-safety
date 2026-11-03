# Research Contract Resolution Report — 2026-10-29

**Status:** `PROPOSED_NOT_APPROVED`  
**Scope:** Source-grounded resolution package; no official decision or execution.

## 1. Live facts

- Official gate: `ready=False`, 9 blockers.
- Official event input contract requires exact nonempty disjoint `train`, `val`, `test` partitions.
- `Phase12EvaluationRunner.run()` evaluates only `event_split["test"]`.
- `manifest_builder` derives manifests from verified split/R04 decisions and refuses missing decisions.
- `full_cohort_descriptive` exists only as a proposed synthetic-only component; no official mode exists.
- M4 remains `first_blocked_to_t4_clearance`; no profile is selected.

## 2. Contract classification

| Design element | Classification | Evidence |
|---|---|---|
| Synthetic typed aggregation | `EXISTING_CONTRACT` + `IMPLEMENTED_SYNTHETIC_ONLY` | `descriptive_only.py`, existing metric aggregator |
| Proposed mode identifier | `RESEARCHER_DECISION_REQUIRED` | no official schema field |
| Official full-cohort input without partitions | `NOT_SUPPORTED_BY_CURRENT_SCHEMA` | input contracts/validator/runner |
| Separate descriptive contract | `ENGINEERING_RECOMMENDATION` + `RESEARCHER_DECISION_REQUIRED` | proposal, no implementation |
| Approved population/event list | `MISSING_EVIDENCE` | no approved split/GT |
| Event ID normalization beyond nonempty string | `MISSING_EVIDENCE` | current official contracts reject invalid IDs but no descriptive extension exists |
| Censoring/missing reporting | `EXISTING_CONTRACT` | `SingleEventEvaluation`, metrics exclusions |
| T4-dependent metrics | `MISSING_EVIDENCE` / R04 | back-camera clock and approved T4 required |
| Official provenance | `EXISTING_CONTRACT` | `replay_evidence.py`, governance bindings |

## 3. Protocol differences

HEAD is protocol v8.0.0/GT v6.0.0; worktree is protocol v9.0.0/GT v7.0.0. The worktree
changes R03/site-survey treatment and operational danger-zone wording; both retain unresolved
R04 independent clocks. No authority was selected. This affects D3 scope language, GT workflow,
R04 interpretation, and protocol/profile hashes.

## 4. D1/D2/D3/D4 decisions still required

- **D1:** Select effective protocol set; create validated `phase12-protocol-decision/1`.
- **D2:** Select v9 or M4; bind profile hash. M4 needs replay `t_blocked` + approved back-clock T4;
  neither v9 nor M4 is front-only evaluable.
- **D3:** Preserve current split contract with a genuine event-level split, authorize a separate
  descriptive contract, amend official contract, or defer. Do not use image split as event split.
- **D4:** Select per-event camera modes/accepted-sync set; dual camera requires calibration evidence
  and researcher acceptance; no zero offset/tolerance invented.

## 5. D3 contract-resolution recommendation

The safest architecture is a separate descriptive-only contract and entrypoint that never feeds
`phase12-evaluation-inputs/1`, `manifest_builder`, or `Phase12EvaluationRunner`. This is only a
recommendation. It requires researcher scientific-scope approval and independent architecture/schema
review before implementation.

## 6. Ground truth/R04/cache dependencies

Active Stage-2.1 schema is `8.1.0-stage2.1`; current 27 review records are legacy schema 6.0.0
with invalidation notices. Candidate proposals are not labels. Stage-2.1 human adjudication,
promotion receipt, and cohort coverage precede official evidence.

Cache production remains deferred and not authorized. Official provenance requires frozen config,
policy/checkpoint/threshold identity, reviewed media hashes, inference identity, cache hashes,
protocol/split/R04 bindings, and later EVAL-AUTH.
