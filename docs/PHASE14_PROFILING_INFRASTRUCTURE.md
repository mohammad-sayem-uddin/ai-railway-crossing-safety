# Phase 14 — Profiling Infrastructure Status

**Status:** A small offline profiling primitive is implemented; Phase 14 profiling and optimization study remain NOT RUN / NOT AUTHORIZED.
**Verified:** 2026-10-16.

## Implemented engineering primitive

`src/railway_detection/optimization/profiler.py` provides `StageProfiler` for
callers to explicitly wrap a callable or record a duration. It reports sample
count, arithmetic mean, nearest-rank p50/p95/p99, and maximum durations in
milliseconds. The clock is injectable so unit tests can be deterministic.

`EventSimulationRunner.run_frames()` accepts an optional profiler. Profiling is
disabled unless a caller supplies one; the CLI enables it only with
`simulate run --profile` and writes `simulation_profile.json` separately from
the unchanged `simulation_result.json`. Wrapped stages include frame sorting,
engine/gate reset, per-frame decision evaluation, gate stepping, step recording,
and result aggregation. The report records workload identifiers/fingerprint,
runtime environment, runner/profiler source hashes, and effective decision/gate
configuration. Input provenance is labeled as offline replay with synthetic
provenance unverified unless independently established.

Profiler errors are captured in the report and do not skip or repeat a
simulation operation. A simulation-stage exception is recorded and re-raised;
it is never converted to a successful result. A profile-report serialization
failure produces a minimal failure report and does not change the simulation
result. Optional profile-file write errors are warnings after the ordinary
simulation result is written. When the simulation itself raises, the CLI attempts
to persist the profile/error report before re-raising the simulation exception.

The module does not automatically instrument inference or conduct a performance
study, select hardware, decide a tick budget, optimize the pipeline, or compare
behavioral outputs. Optional simulation replay instrumentation is now available,
but has not been used to claim performance. Integration tests use synthetic
frames and deterministic clock values only.

## Evidence boundary

The report serialization identifies itself as `local_engineering_profile` and
sets `is_target_hardware_evidence` and `is_safety_evidence` to `false`. No
measured pipeline performance or real-time feasibility is reported here. A
replay profile records the host/environment, exact frame fingerprint, config
values/hash when available, source hashes, and limitations. It does not record
or imply an inference checkpoint workload: `EventSimulationRunner` consumes
already-built frames. Such a replay profile is not a hardware benchmark, an
inference-latency measurement, or safety evidence. A Phase 14 performance study
still needs an authorized workload, checkpoint identifiers where applicable,
warm-up/repetition procedure, target-hardware scope, and researcher review.

## Verification

```text
.venv/bin/python -m pytest tests/unit/test_phase14_profiler.py -q
.venv/bin/python -m pytest tests/unit/test_simulation_runner_profiling.py -q
```

The tests validate deterministic duration aggregation, exceptions, invalid
inputs, decreasing clocks, and evidence-boundary metadata; they do not constitute
a performance experiment.

---

## Additive update — 2026-10-16 (benchmark tooling; no performance claim)

`src/railway_detection/optimization/benchmark.py` adds a predeclared measurement procedure and an equivalence check; `scripts/run_phase14_benchmark.py` applies it to a deterministic synthetic replay.

- `run_benchmark`: discarded warm-up, repeated measured iterations, host fingerprint, latency distribution, per-repetition medians and spread. Exceptions propagate (a failing workload yields no report).
- `real_time_claim_permitted` is always `false`. A sampled percentile is not a worst-case execution-time bound. An optional latency budget is compared descriptively only.
- `is_target_hardware_evidence` is `true` only if a target fingerprint was declared, every declared key equals the measuring host, and at least 100 samples were taken. Any other run, including every run so far, is local engineering evidence only.
- `compare_outputs_for_equivalence`: byte-compares reference and optimized implementations over fixed inputs; errors and non-bytes outputs are mismatches. Candidate optimizations (ONNX export, vectorization) remain unwritten; this is the acceptance test they must pass.
- Not done: inference-latency measurement (needs an authorized workload), any target-hardware measurement (no target platform has been specified), any optimization.
- Tests: `tests/unit/test_phase14_benchmark.py` (18, deterministic clocks).

---

## Additive update — 2026-10-16 (overnight): reproducible benchmark command

`python -m railway_detection benchmark run --output <path outside the repo trees>` (also `scripts/run_phase14_benchmark.py`) writes `phase14-benchmark-report/2`: exact code revision and dirty-worktree count, raw and canonical hashes of the frozen config and decision policy, checkpoint hash verification (Audio V2 presence is a failure), host/CPU/RAM/accelerator/dependency versions, warm-up and repetition counts, per-stage latency distributions, items/s and frames/s, process peak RSS (lifetime high-water mark), an output fingerprint (a non-reproducible workload aborts), explicit `synthetic`/`real` input classification, an acceptance assessment, and a limitations list.

Claim discipline (tested): a real-time claim requires real inputs **and** a documented acceptance criterion **and** a declared target platform equal to the measuring host **and** ≥ 100 samples **and** verified fingerprints **and** the observed statistic within the criterion. None of these holds today (no target platform, no documented criterion), so `real_time_claim_permitted` is `false` and measured values stand without a compliance statement. `check_candidate_equivalence` judges optimizations on the same input set with byte-identical outputs and caller-supplied property checks, and refuses a candidate that is the reference itself.

Environment limit found: the virtualenv's `ultralytics` directory has no `__init__.py`, so the frozen YOLO checkpoint cannot be loaded here; the `--vision-model` workload therefore records `status: unavailable` rather than numbers. No inference latency exists.

## Additive update — benchmark robustness and classification

Benchmark reports now classify inputs with an explicit evidence boundary and
require stable provenance (a manifest/source digest or path) before a workload
may be called `real`. Missing acceptance criteria produce an explicit blocker,
not an implicit pass. Benchmark report writes are atomic, so an interrupted
serialization cannot masquerade as a complete report. These changes remain
descriptive engineering measurements: no report grants a real-time or safety
claim, including when a target fingerprint happens to match.
