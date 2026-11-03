# Forensic Remediation Baseline — 2026-10-30

## Repository

- Root: `/Users/sayemuddin/Desktop/Train_automation`
- Branch/HEAD: `main` / `d4db94d`
- Initial working tree: pre-existing modified user files and extensive untracked research artifacts; no staged changes.
- Historical artifacts preserved; no media accessed.

## Scope inspected

- `src/railway_detection/experiments/runner.py`
- `src/railway_detection/experiments/layer_b_processor.py`
- `src/railway_detection/simulation/failure_injector.py`
- `src/railway_detection/evaluation/metrics.py`
- `src/railway_detection/experiments/statistics.py`
- `src/railway_detection/experiments/timeline_generator.py`
- Relevant unit tests and forensic/corrective audit reports.
- `results/experiments/*`, cache filenames, summaries, per-event JSON, R04 metadata.

## Dependency map

```text
ExperimentRunner.run_condition
  -> _prepare_frames_for_condition
  -> FailureInjector.inject_failures (B5/B6/B7)
  -> _execute_simulation
  -> EventMetricsCalculator.evaluate_run
  -> aggregate_cohort
  -> summary.json + single_events.json
  -> statistics.py / publication tables / figures
```

`LayerBEventProcessor` is the raw-media producer/cache reader. Its cache key includes cohort,
event, source, and modality, but not checkpoint/configuration/injector identity; this is a
confirmed provenance limitation. It was not executed.

## Existing artifacts

- 17 condition directories B0–B7f, plus corrected B6b/B7b/B7f namespace.
- 141 JSONL cache files (active/orphaned scopes).
- R04 event evidence and candidate proposals.
- Legacy schema-6.0.0 review records with invalidation notices; no active Stage-2.1.
- Existing forensic audit documents identify benchmark invalidation causes.

## Areas not inspected

Raw media contents, real inference, cache regeneration, ground-truth review, promotion,
EVAL-AUTH, and official evaluation were prohibited. Condition source and metadata were inspected.
