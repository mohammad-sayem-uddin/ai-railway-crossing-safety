# Research Results Reconciliation — Metadata/Artifact Audit — 2026-10-29
**Status:** `NOT_VERIFIED` for unsupported prior headline tables; descriptive artifacts only.

## Stored condition summary fields

The current `summary.json` files contain total/eligible events, missed-train rate/CI, premature-opening evaluability/rate, and fault counts. They do **not** contain the closed-duration, warning-lead, episode, or false-alarm fields used by the prior 14-condition matrix. Those values are not regenerated here.

| Condition | Events | Eligible | MTR | POR evaluable | Fault events | Derived sum closed_s from per-event file |
|---|---:|---:|---:|---:|---:|---:|
| B0 | 27 | 27 | 0.0 | 0 | 0 | 1007.2 |
| B1 | 27 | 27 | 0.0 | 0 | 0 | 146.6 |
| B2 | 27 | 27 | 0.0 | 0 | 0 | 1210.2 |
| B3 | 27 | 27 | 0.0 | 0 | 0 | 1227.4 |
| B4 | 27 | 27 | 0.0 | 0 | 0 | 1231.4 |
| B5a | 27 | 27 | 0.0 | 0 | 8 | 1152.0 |
| B5b | 27 | 27 | 0.0 | 0 | 0 | 1231.4 |
| B5c | 27 | 27 | 0.0 | 0 | 6 | 1231.4 |
| B6a | 27 | 27 | 0.0 | 0 | 5 | 1194.2 |
| B6b | 27 | 27 | 0.0 | 0 | 27 | 0.0 |
| B6c | 27 | 27 | 0.0 | 0 | 27 | 1231.4 |
| B7a | 27 | 27 | 0.0 | 0 | 0 | 1231.4 |
| B7b | 27 | 27 | 0.0 | 0 | 0 | 0.0 |
| B7c | 27 | 27 | 0.0 | 0 | 0 | 1241.6 |
| B7d | 27 | 27 | 0.0 | 0 | 0 | 1231.4 |
| B7e | 27 | 27 | 0.0 | 0 | 0 | 1231.4 |
| B7f | 27 | 27 | 0.0 | 0 | 0 | 0.0 |

## Statistical artifact

`results/experiments/statistical_analysis/comprehensive_statistics.json` reports all conditions with MTR=0 and POR non-evaluable; paired comparisons B4_vs_B0, B4_vs_B2, B4_vs_B3 are present. Its note calls the analysis exploratory (N=21), and no official ground-truth binding exists. Do not promote `statistically_significant` text as an official claim.

## Invalidated/diagnostic boundary

`docs/DEEP_RESEARCH_COMPLETION_AUDIT_20261025.md` and `docs/CORRECTIVE_EXPERIMENT_AUDIT.md` state the original benchmark had forensic invalidations (cache contamination, unapproved GT defaulting, negative-control pooling, B6b fail-safe defect, B7b/B7f injector defect). Corrected B6b/B7b/B7f are in `results/experiments/corrected_run/`; these remain diagnostic and not official Phase 12 results.

## Claim status

- Software safety invariants: `TESTED_SYNTHETICALLY`.
- Diagnostic simulation outputs: `VERIFIED_AS_ARTIFACTS`, not empirical benchmark evidence.
- Ground-truth-dependent MTR/POR/WLT/T4 metrics: `BLOCKED_BY_MISSING_EVIDENCE`.
- Official conclusions/generalization: `NOT_VERIFIED`.
