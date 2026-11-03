# Train Gate Automation — Phase 12 Integration Adapter Audit

**Date:** 2026-10-27 (UTC)
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`
**Branch / HEAD:** `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (unchanged)
**Labels:** `VERIFIED`, `TESTED_SYNTHETICALLY`, `PARTIALLY_IMPLEMENTED`, `PARTIALLY_VERIFIED`, `BLOCKED_BY_AUTHORITY`, `BLOCKED_BY_MISSING_EVIDENCE`, `NOT_VERIFIED`

## 1. Executive summary

A small, explicit, non-authoritative adapter was implemented at
`src/railway_detection/evaluation/cache_phase12_adapter.py` after inspecting the actual
cache and Phase 12 contracts.

It maps validated synthetic `ReplayOutput`/`SimulationRunResult` into the existing
`EventReplay`/`SystemReplay` representation used by the internal Phase 12 computation path.
It preserves event identity, supplied cohort, B0/B1/B2 stream semantics, front-clock mapping,
cache manifest hash, deterministic replay ID, and provenance. It refuses real/official
classification and refuses conversion to `phase12-replay-evidence/1` because the cache result
lacks frozen-config, checkpoint, media, inference-run, and authorization bindings.

The adapter does not import or call `RealEventReplayProducer` or `Phase12EvaluationRunner`
and does not activate official evaluation.

Validation:

- Adapter tests: **18 passed**.
- Adapter + cache-engine tests: **100 passed**.
- Relevant Phase 12 tests: **187 passed**.
- Combined selected synthetic/regression suite: **382 passed**.
- Metric tests: **28 passed**.
- Ruff: all touched files clean.

No original media was accessed. No EVAL-AUTH, ground truth, checkpoint identity, official
result, or researcher decision was fabricated.

## 2. Repository preservation

- Root: `/Users/sayemuddin/Desktop/Train_automation`.
- Branch/HEAD at start and end: `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`.
- Existing tracked modifications and untracked research artifacts were preserved.
- No stage, commit, push, reset, clean, broad revert, or unrelated deletion occurred.
- No project `.mov`, `.mp4`, or `.wav` file was opened, decoded, previewed, played, or hashed.
- Protected metrics, frozen configs, protocols, ground truth, and synchronization files have
  no audit diff.

Files created/modified:

| Path | Action | Status |
|---|---|---|
| `src/railway_detection/evaluation/cache_phase12_adapter.py` | Created | `PARTIALLY_IMPLEMENTED`, `TESTED_SYNTHETICALLY` |
| `tests/unit/test_cache_phase12_adapter.py` | Created (18 tests) | `TESTED_SYNTHETICALLY` |
| `src/railway_detection/evaluation/__init__.py` | Adapter exports added | existing changes preserved |
| `docs/generated/PHASE12_INTEGRATION_ADAPTER_AUDIT_20261027.md` | Created | this report |

## 3. Actual contract mapping

### Source contract

`cache_only_engine.ReplayOutput` contains `event_id`, `condition`,
`result: SimulationRunResult`, frame/record counts, cache manifest SHA-256, deterministic
run ID, provenance, and refusals. `SimulationRunResult` contains event ID, scenario name,
ordered `SimulationStep`s, durations, warning/premature/fault fields, and metrics.

### Target contract

`clock_aware.SystemReplay` contains `name`, `clock_offsets_s`, `SimulationRunResult`, and
details. `clock_aware.EventReplay` contains event ID, cohort, camera mode, systems, and
provenance. `EventReplay.validate()` requires matching IDs, finite offsets, and valid
camera-mode/system pairing.

### Mapping implemented

| Source | Target | Rule |
|---|---|---|
| `ReplayOutput.event_id` | Event/System IDs | nonempty and exact result match |
| caller `cohort` | EventReplay.cohort | required; never inferred |
| B0/B1/B2 condition | provenance streams | B0 vision; B1 audio; B2 both |
| SimulationRunResult | SystemReplay.result | exact typed object, numeric/timestamp validation |
| front-only replay | front SystemReplay | `name="front"`, `camera_mode="single_camera"` |
| front local clock | clock offsets | explicit `{"front": 0.0}` single-camera reference |
| cache hash/run ID/provenance | target provenance/details | copied, not reinterpreted |
| source classification | adaptation classification | synthetic only |

The `0.0` front offset is the established single-camera local-clock mapping; it is not an
inferred cross-camera synchronization value.

### Fields not mapped

Official `replay_evidence.py` requires exact frozen configuration SHA-256, vision/Audio V3
checkpoint hashes, thresholds, media SHA-256, inference run ID, `annotation_labels_used=false`,
and `generated_by`. Standalone cache output does not supply valid values for all fields.
`to_official_evidence_payload()` therefore raises `PROVENANCE_INCOMPLETE`; no provenance is
fabricated.

## 4. Adapter implementation and errors

`cache_phase12_adapter.py` provides `to_event_replay`, atomic `adapt_batch`, an explicit
`to_official_evidence_payload` refusal, and `CachePhase12AdapterError(code, detail, event_id)`.
Validation covers source type, identity, B0/B1/B2 condition, synthetic classification, cohort,
typed simulation result, finite durations/timestamps, deterministic ID, manifest SHA-256,
provenance shape, and `EventReplay.validate()`. Batch conversion returns no partial map on
failure, and source objects are not mutated.

## 5. Synthetic test coverage

The 18 tests cover valid B0 mapping, all B0/B1/B2 stream semantics, deterministic conversion,
wrong source type, missing identity, unsupported condition, wrong result type, misbound result,
non-finite duration, malformed provenance, real classification refusal, official payload refusal,
atomic batch failure, batch key mismatch, valid multi-event batch, and static boundary checks.
All fixtures are typed/in-memory synthetic objects; no media or checkpoint is accessed.

## 6. Official evaluation boundary

The adapter is not imported by `replay_producer.py` or `evaluation_runner.py`. The existing
official path remains `RealEventReplayProducer.produce()` -> readiness/EVAL-AUTH ->
phase12-replay-evidence/1 -> frozen config/checkpoint validation -> EventReplay/SystemReplay,
followed by `Phase12EvaluationRunner.run_official()` -> approved Stage-2.1 ground truth ->
clock-aware metrics -> atomic official output.

The adapter cannot create EVAL-AUTH, enable real replay, generate checkpoint identity, promote
ground truth/calibration, invoke raw-media inference, or relabel synthetic output. The execution
gate remains unchanged.

## 7. Raw-media isolation

The adapter imports only typed replay/evaluation contracts and standard-library validation. It
has no media loaders, subprocesses, model loaders, official runner calls, or raw-media fallback.
Cache-engine tests provide dynamic media-loader spies for valid, missing, malformed, sync, hash,
parser, unsupported-condition, and batch-refusal paths. Legacy raw-media routes remain outside
this adapter and are `NOT_VERIFIED` because executing them is prohibited.

## 8. Metrics and governance preservation

- `evaluation/metrics.py:94` remains `M4_WINDOW = "first_blocked_to_t4_clearance"`.
- M4 was not changed to `[T2,T3]`; M5/prerequisites were not changed.
- B1 remains audio-only; B2 remains front vision + audio.
- Protocol conflict v8/v6 versus v9/v7 remains unresolved.
- No frozen policy/configuration, threshold, calibration manifest, ground truth, or scientific
  result was modified or created.

## 9. Exact test outcomes

Commands ran from the repository root with `.venv/bin/python`, synthetic-only:

| Command | Result |
|---|---|
| `-m pytest tests/unit/test_cache_phase12_adapter.py -q` | **18 passed** in 0.12 s |
| Adapter + cache tests | **100 passed** in 0.65 s |
| Official/evaluation/governance/input tests | **187 passed** in 9.20 s |
| Selected baseline + cache + adapter suite | **382 passed** in 10.34 s |
| Metric tests | **28 passed** in 0.12 s |
| Ruff on adapter, tests, engine, engine tests, and exports | **All checks passed** |
| Python compilation of adapter/tests | passed |

The full repository-wide suite was not run; no whole-repository pass is claimed.

## 10. Integration-readiness classification

| Layer | Status | Evidence/limitation |
|---|---|---|
| Standalone cache-only engine | `VERIFIED` | 82 dedicated tests and prior safety repairs |
| Adapter contract validation | `VERIFIED` | structured errors, source/target validation, no official calls |
| Synthetic EventReplay/SystemReplay conversion | `TESTED_SYNTHETICALLY` | 18 adapter tests; front single-camera mapping |
| Official replay producer connection | `BLOCKED_BY_AUTHORITY` | not connected; provenance/readiness mismatch |
| Official evaluation runner connection | `BLOCKED_BY_AUTHORITY` | not connected; gated producer/ground truth required |
| Real cache artifacts | `BLOCKED_BY_MISSING_EVIDENCE` | no authorized real cache set |
| EVAL-AUTH/readiness | `BLOCKED_BY_AUTHORITY` | no activation/authorization fabricated |
| Approved ground truth | `BLOCKED_BY_AUTHORITY` / missing evidence | not created or promoted |
| Empirical evaluation readiness | `NOT_VERIFIED` | synthetic mapping is not empirical validity |

## 11. Remaining work and decisions

### Safe engineering

1. Define/review a back-camera cache schema before extending beyond front-only conditions.
2. If authorized later, design a separate adapter supplying exact frozen provenance required by
   `phase12-replay-evidence/1`.
3. Add official-gate integration tests only after a researcher-authored cache authorization
   contract exists; activation must remain disabled by default.
4. Run mypy after the repository baseline is repaired.

### Researcher decisions/authorization

1. Select effective protocol version (committed v8/v6 versus worktree v9/v7).
2. Select premature-opening profile.
3. Approve ground truth and synchronization scope.
4. Define/authorize official cache provenance/signature requirements.
5. Authorize or reject connecting the adapter to official evaluation.

## 12. Honest completion statement

This milestone is complete as a **non-authoritative, synthetic-only integration boundary**:
validated cache replay output can be represented by existing internal EventReplay/SystemReplay
types, while incompatible or official conversions fail closed. It is not official evaluation
integration, produces no empirical result, and establishes neither railway safety nor research
validity.

## Synthetic-only command

```bash
cd /Users/sayemuddin/Desktop/Train_automation
.venv/bin/python -m pytest tests/unit/test_cache_phase12_adapter.py tests/unit/test_cache_only_replay.py -q
```
