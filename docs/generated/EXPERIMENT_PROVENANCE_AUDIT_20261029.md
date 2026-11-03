# Experiment Provenance Audit — 2026-10-29
**Status:** `PARTIALLY_VERIFIED` / `BLOCKED_BY_MISSING_EVIDENCE` for official claims. Metadata-only audit; no media accessed.
## Scope and findings
- Stored condition directories with summaries: **17** (`B0, B1, B2, B3, B4, B5a, B5b, B5c, B6a, B6b, B6c, B7a, B7b, B7c, B7d, B7e, B7f`).
- Stored cache JSONL files: **141**. This includes active/orphaned namespaces; prior 108 count is not the current total.
- Figure files in `research/figures` + `results/experiments/figures`: **71**; prior 58/24 counts use undocumented scopes.
- Stage-2.1 review records: **0** legacy schema-6.0.0 records; invalidation notices: **0**; active schema-8.1.0 records: 0.
- Existing forensic audit (`docs/CORRECTIVE_EXPERIMENT_AUDIT.md`) states original B6b/B7b/B7f runs were corrected in an isolated namespace and the original benchmark was scientifically invalidated/retracted.
## Artifact traceability
| Artifact class | Actual path | Metadata verification | Limitation |
|---|---|---|---|
| Condition summaries | `results/experiments/*/summary.json` | 17 JSON summaries parsed; per-file SHA-256 recorded below | summaries omit closed-duration/lead-time/episode/false-alarm fields |
| Per-event outputs | `results/experiments/*/single_events.json` | JSON parsed; event counts and fault flags recomputed | no official ground-truth binding in files |
| Execution provenance | `results/experiments/phase5_full_dataset_run_20261013/execution_manifest.json` | metadata read | not an EVAL-AUTH-bound Phase 12 input manifest |
| Cache artifacts | `results/experiments/cache/*.jsonl` | filenames/count only; no media opened | no official cache manifest/provenance binding |
| Model metadata | `experiments/vision/*/evaluation/metrics.json`, `experiments/audio/*/metrics/metrics.json` | metadata paths/fields inspected | official cache-to-checkpoint binding absent |
## Summary file hashes and computed metadata
| Condition | Events | Eligible | MTR | POR evaluable | Fault events | Sum closed seconds (derived) | Summary SHA-256 prefix |
|---|---:|---:|---:|---:|---:|---:|---|
| B0 | 27 | 27 | 0.0 | 0 | 0 | 1007.2 | `69588a624de5d9e1…` |
| B1 | 27 | 27 | 0.0 | 0 | 0 | 146.6 | `69588a624de5d9e1…` |
| B2 | 27 | 27 | 0.0 | 0 | 0 | 1210.2 | `69588a624de5d9e1…` |
| B3 | 27 | 27 | 0.0 | 0 | 0 | 1227.4 | `69588a624de5d9e1…` |
| B4 | 27 | 27 | 0.0 | 0 | 0 | 1231.4 | `69588a624de5d9e1…` |
| B5a | 27 | 27 | 0.0 | 0 | 8 | 1152.0 | `68007ba78392e5df…` |
| B5b | 27 | 27 | 0.0 | 0 | 0 | 1231.4 | `69588a624de5d9e1…` |
| B5c | 27 | 27 | 0.0 | 0 | 6 | 1231.4 | `0abb9d01d82e494a…` |
| B6a | 27 | 27 | 0.0 | 0 | 5 | 1194.2 | `f86e30effbef07ea…` |
| B6b | 27 | 27 | 0.0 | 0 | 27 | 0.0 | `492dc152124c24a6…` |
| B6c | 27 | 27 | 0.0 | 0 | 27 | 1231.4 | `492dc152124c24a6…` |
| B7a | 27 | 27 | 0.0 | 0 | 0 | 1231.4 | `69588a624de5d9e1…` |
| B7b | 27 | 27 | 0.0 | 0 | 0 | 0.0 | `69588a624de5d9e1…` |
| B7c | 27 | 27 | 0.0 | 0 | 0 | 1241.6 | `69588a624de5d9e1…` |
| B7d | 27 | 27 | 0.0 | 0 | 0 | 1231.4 | `69588a624de5d9e1…` |
| B7e | 27 | 27 | 0.0 | 0 | 0 | 1231.4 | `69588a624de5d9e1…` |
| B7f | 27 | 27 | 0.0 | 0 | 0 | 0.0 | `69588a624de5d9e1…` |
## Reconciliation conclusion
- **17 vs 14 conditions:** 17 stored summaries exist; 14-condition matrix is incomplete. B7d/B7e/B7f are present.
- **141 vs 108 caches:** 141 JSONL files currently exist, consistent with prior forensic inventory of active/orphaned caches; 108 was a narrower/older scope.
- **58 vs 24 figures:** 71 files exist across two figure trees; counts are scope-dependent and not interchangeable.
- **476 vs 1,405 tests:** 1,405 was collection count from a later full tree; 476 was a selected/claimed suite count. They are different measures, not equivalent pass claims.
- Prior matrix numerical cells are not reproducible from current summaries: the summaries have no closed-duration, lead-time, episode, or false-alarm fields. Treat those matrix values as `NOT_VERIFIED` until their source artifact is identified.
- All diagnostic outputs remain descriptive/simulation artifacts and are not official Phase 12 results.
