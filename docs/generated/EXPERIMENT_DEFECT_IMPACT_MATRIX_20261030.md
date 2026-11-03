# Experiment Defect Impact Matrix — 2026-10-30

**Important:** Historical artifacts are unchanged. Classifications are metadata/source audit
results, not official validity claims.

| Condition | Source | Artifacts | Namespace/provenance | Known issue | Classification |
|---|---|---|---|---|---|
| B0 | `src/railway_detection/experiments/runner.py` | `results/experiments/B0/` | event-qualified Layer B cache names | summaries lack full provenance | None confirmed in current inspected path | NOT_VERIFIABLE |
| B1 | `src/railway_detection/experiments/runner.py` | `results/experiments/B1/` | event-qualified Layer B cache names | summaries lack full provenance | None confirmed in current inspected path | NOT_VERIFIABLE |
| B2 | `src/railway_detection/experiments/runner.py` | `results/experiments/B2/` | event-qualified Layer B cache names | summaries lack full provenance | None confirmed in current inspected path | NOT_VERIFIABLE |
| B3 | `src/railway_detection/experiments/runner.py` | `results/experiments/B3/` | event-qualified Layer B cache names | summaries lack full provenance | None confirmed in current inspected path | NOT_VERIFIABLE |
| B4 | `src/railway_detection/experiments/runner.py` | `results/experiments/B4/` | event-qualified Layer B cache names | summaries lack full provenance | None confirmed in current inspected path | NOT_VERIFIABLE |
| B5a | `src/railway_detection/experiments/runner.py` | `results/experiments/B5a/` | event-qualified Layer B cache names | summaries lack full provenance | None confirmed in current inspected path | NOT_VERIFIABLE |
| B5b | `src/railway_detection/experiments/runner.py` | `results/experiments/B5b/` | event-qualified Layer B cache names | summaries lack full provenance | None confirmed in current inspected path | NOT_VERIFIABLE |
| B5c | `src/railway_detection/experiments/runner.py` | `results/experiments/B5c/` | event-qualified Layer B cache names | summaries lack full provenance | None confirmed in current inspected path | NOT_VERIFIABLE |
| B6a | `src/railway_detection/experiments/runner.py` | `results/experiments/B6a/` | event-qualified Layer B cache names | summaries lack full provenance | None confirmed in current inspected path | NOT_VERIFIABLE |
| B6b | `src/railway_detection/experiments/runner.py` | `results/experiments/B6b/` | event-qualified Layer B cache names | summaries lack full provenance | Original dual-dropout fail-safe defect documented; corrected namespace exists; current source path requires synthetic regression confirmation | REQUIRES_RERUN |
| B6c | `src/railway_detection/experiments/runner.py` | `results/experiments/B6c/` | event-qualified Layer B cache names | summaries lack full provenance | None confirmed in current inspected path | NOT_VERIFIABLE |
| B7a | `src/railway_detection/experiments/runner.py` | `results/experiments/B7a/` | event-qualified Layer B cache names | summaries lack full provenance | None confirmed in current inspected path | NOT_VERIFIABLE |
| B7b | `src/railway_detection/experiments/runner.py` | `results/experiments/B7b/` | event-qualified Layer B cache names | summaries lack full provenance | Original injector defect documented; corrected namespace exists | REQUIRES_RERUN |
| B7c | `src/railway_detection/experiments/runner.py` | `results/experiments/B7c/` | event-qualified Layer B cache names | summaries lack full provenance | None confirmed in current inspected path | NOT_VERIFIABLE |
| B7d | `src/railway_detection/experiments/runner.py` | `results/experiments/B7d/` | event-qualified Layer B cache names | summaries lack full provenance | Forensic audit records no-op/insufficient implementation; current runner schedules exist but behavior needs synthetic verification | NOT_VERIFIABLE |
| B7e | `src/railway_detection/experiments/runner.py` | `results/experiments/B7e/` | event-qualified Layer B cache names | summaries lack full provenance | Forensic audit records no-op/insufficient implementation; current runner schedules exist but behavior needs synthetic verification | NOT_VERIFIABLE |
| B7f | `src/railway_detection/experiments/runner.py` | `results/experiments/B7f/` | event-qualified Layer B cache names | summaries lack full provenance | Original injector defect documented; corrected namespace exists | REQUIRES_RERUN |

## Metric-level impact

| Metric | Current evidence | Status |
|---|---|---|
| Closed duration | per-event `single_events.json` values exist; not in summaries | `RECOVERABLE_FROM_EXISTING_ARTIFACTS` for diagnostic descriptive use |
| Lead time | stored per-event values are null | `NOT_VERIFIABLE` |
| Premature opening | all current summaries POR non-evaluable | `BLOCKED_BY_MISSING_EVIDENCE` |
| Episode count | not present in summaries | `NOT_VERIFIABLE` |
| False alarms | forensic audit reports negative-control pooling; current summary lacks false-alarm fields | `INVALIDATED` for prior pooled headline; requires separate recomputation |
| Fail-safe activation | corrected namespaces exist; old B6b invalidated | `REQUIRES_RERUN` for validated diagnostic claim |
| Jitter robustness | injector source is deterministic but B7d/B7e behavior requires targeted testing | `NOT_VERIFIABLE` |
| Statistical comparisons | artifact has paired comparisons but depends on unsupported continuous inputs | `NOT_VERIFIABLE` for headline use |

## Provenance findings

`LayerBEventProcessor.run_vision_inference` cache names contain cohort/event/source/modality but
not checkpoint/config/injector identity. Audio cache names contain cohort/event/source/modality
but likewise omit checkpoint/configuration. This permits logical cross-run reuse unless the caller
isolates cache directories. No historical cache is rewritten here.
