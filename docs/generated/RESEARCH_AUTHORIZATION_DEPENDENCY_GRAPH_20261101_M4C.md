# Research Authorization Dependency Graph

This graph distinguishes required dependencies from independent preparation. It is a planning artifact, not authorization.

```mermaid
flowchart TD
  D1[GOV-D1 protocol authority] --> D2[GOV-D2 evaluation profile]
  D1 --> D4[GOV-D4 R04 scope]
  D1 --> RP[D3(a)/D3(c) review policy]
  RP --> RA[Named reviewer authorization]
  RA --> RE[Review-environment/media authorization]
  D1 --> RE
  RE --> PA[Three-event pilot authorization]
  RA --> PA
  PA --> HR[Genuine Stage-2.1 human review]
  RP --> HR
  HR --> DR[Disagreement/second-review resolution]
  DR --> GA[Researcher ground-truth approval]
  GA --> PM[Promotion authorization + promotion receipt]
  D1 --> PM
  D2 --> PM
  D4 --> PM
  PM --> ES[Official event split decision]
  D2 --> ES
  ES --> IM[Official input manifest/cache provenance]
  PM --> IM
  D4 --> IM
  IM --> EA[Official evaluation authorization EVAL-AUTH]
  D1 --> EA
  D2 --> EA
  ES --> EA
  GA --> EA
  ET[Operating thresholds] --> IM
  ROI[ROI geometry] --> IM
  B7[B7e numerical parameters] --> IM
  RP -. independent preparation .-> PA
  DES[D3 descriptive-only approval] -. permits descriptive-only scope only .-> HR
```

## Dependency interpretation

- D1 is upstream of D2, D4, review semantics, and official hashes.
- D3(a)/D3(c) can be prepared independently of D2, but must be bound before production review/approval.
- Reviewer authorization and environment authorization are separate gates; neither substitutes for D1/D3 policy.
- The pilot must precede using pilot timing observations to discuss D1, but pilot execution itself does not authorize promotion.
- Human review and disagreement resolution precede ground-truth approval and promotion.
- Threshold/ROI/B7e decisions are not prerequisites for merely documenting a review workflow, but are required before scientific experiment authorization/official claims.
- EVAL-AUTH is last and cannot be implied by a readiness report.

Source dependency evidence: `docs/generated/RESEARCH_PROTOCOL_DEPENDENCY_MAP_20261030.md`, `src/railway_detection/evaluation/governance.py`, `src/railway_detection/evaluation/execution_gate.py`, Stage-2.1 M4A/M4B reports.