# Train Gate Automation — Cache-Only Replay Engine Implementation Report

**Date:** 2026-10-27
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`
**Branch / HEAD at start and end:** `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (unchanged)
**Labels:** `IMPLEMENTED`, `TESTED_SYNTHETICALLY`, `NOT_VERIFIED`, `BLOCKED_BY_AUTHORITY`, `BLOCKED_BY_MISSING_EVIDENCE`

## 1. Executive summary

A fail-closed cache-only replay engine (`CacheOnlyReplayEngine`) was implemented at
`src/railway_detection/evaluation/cache_only_engine.py` (~770 lines), realizing the proposed
design in `docs/CACHE_ONLY_REPLAY_DESIGN.md` against the project's existing typed-evidence
contracts (`fusion/evidence.py`, `fusion/collector.py`, `fusion/decision_engine.py`,
`data/sync.py`, `simulation/runner.py`). It consumes only hash-bound JSONL detection
caches referenced by a validated manifest, converts records into the existing
`EvidenceRecord` type, and drives the existing `MultimodalEvidenceCollector` →
`EventSimulationRunner` pipeline. No raw media is opened, decoded, or referenced anywhere
in the engine. 64 new synthetic tests pass; the prior 282-test baseline suite plus metric
regression tests remain green. No frozen policy, protocol version, ground truth, metric
definition, or research artifact was altered.

## 2. Repository state verified

- **Start:** HEAD `d4db94d`, branch `main`; 19 tracked-modified files and a large untracked
  research set preserved (per `docs/generated/AUTONOMOUS_IMPLEMENTATION_BASELINE_20261026.md`
  and `docs/generated/POST_IMPLEMENTATION_AUDIT_20261026.md`). Protocol v8/v6 (committed)
  vs v9/v7 (worktree) conflict remains unresolved — no version selected here.
- **End:** HEAD still `d4db94d`; nothing staged, committed, pushed, reset, or deleted.
  Additions only: 2 new untracked source/test files, this report, and one modification to
  `src/railway_detection/evaluation/__init__.py` (export registration only).
  `git diff --stat` verified empty for `evaluation/metrics.py`, `data/r04_evidence.py`,
  `evaluation/protocol_choices.py`, frozen configs, and protocol documents.
  M4 remains `first_blocked_to_t4_clearance` at code level (`metrics.py:94`).
- No `.mov`/`.mp4`/`.wav` media was opened, decoded, hashed, or previewed at any point.

## 3. Files created and modified

| File | Action | Status |
| --- | --- | --- |
| `src/railway_detection/evaluation/cache_only_engine.py` | Created | `IMPLEMENTED`, `TESTED_SYNTHETICALLY` |
| `tests/unit/test_cache_only_replay.py` | Created (64 tests) | `TESTED_SYNTHETICALLY` |
| `src/railway_detection/evaluation/__init__.py` | Modified (docstring + imports + `__all__` additions only) | `IMPLEMENTED` |
| `docs/generated/CACHE_ONLY_REPLAY_IMPLEMENTATION_20261027.md` | Created (this report) | documentation |

No duplicate engine, schema, or competing contract was introduced: the engine reuses the
design document's manifest schema (`manifest_version 1.0.0`, visual/audio record schemas
from `docs/CACHE_ONLY_REPLAY_DESIGN.md` §3), the project's `EvidenceRecord`/`Detection`
types, and the existing collector/simulation runner.

## 4. Cache-only replay architecture and data flow

```
cache_manifest.json (validated: version, required fields, sha256 format, paths)
        |  _load_and_validate_manifest  ->  INV-CACHE-2 media-reference scan
        v
JSONL cache artifacts (data/cache/*.jsonl)
        |  _validate_cache_path (boundary: no absolute/traversal/symlink-escape,
        |     .jsonl/.json only; media extensions -> MediaAccessViolationError)
        |  _verify_cache_file (INV-CACHE-3: existence, byte_size, SHA-256 BEFORE parse)
        v
per-record validation -> typed EvidenceRecord streams
        |  _validate_visual_record / _validate_audio_record (finite numerics,
        |  [0,1] confidence, non-negative timestamps, required fields; explicit
        |  zero timestamps preserved; zero-confidence horn never fabricates evidence)
        v
_deterministic_sort (timestamp, source_id, frame/window index tie-breaker)
        v
MultimodalEvidenceCollector (+ optional SyncAligner; unregistered vision source
        |  raises fail-closed; duplicate/out-of-order observations rejected/logged)
        v
EventSimulationRunner(MultimodalDecisionEngine, PhysicalGateModel) -> ReplayOutput
```

Refusals are structured: `CacheIntegrityError(code)`, `CacheReplayRefusal(code, event_id)`,
`MediaAccessViolationError(code)`. `replay_all_events` converts per-event failures into
`ReplayRefusalRecord` instead of claiming success; there is no partial-success path and
no exception handler that downgrades to a permissive or media-backed mode.

Determinism: identical manifest bytes + condition produce an identical
`deterministic_run_id = sha256(event_id:condition:manifest_sha256)[:16]` and identical
record/frame counts (pinned by `test_deterministic_replay` and
`test_deterministic_fusion_repeated_runs`).

## 5. Integration points with existing components

- **Typed evidence:** records become `railway_detection.fusion.evidence.EvidenceRecord`
  with `Modality.VISION` (`source_id=camera_1`) and `Modality.AUDIO` (`source_id=audio_1`),
  matching `STREAM_SPEC` in `evaluation/replay_evidence.py`. Audio evidence is stamped at
  window end (consistent with the IMA-13 window-start non-causality correction).
- **Fusion:** `MultimodalEvidenceCollector` (window tolerance 0.5 s) ingests records; the
  existing R04 fail-closed aligner registration rule and duplicate/out-of-order rejection
  apply unchanged.
- **State machine:** `EventSimulationRunner` + `MultimodalDecisionEngine` run with the
  existing default parameters; no threshold or dwell was invented or altered.
- **Synchronization:** an optional `SyncAligner` may be supplied (e.g. built via the
  existing `load_validated_sync_aligner` for researcher-accepted dual-camera events). The
  engine never defaults missing offsets/uncertainty to zero and never reads the candidate
  calibration manifest itself. B0/B1/B2 front-sensor replay is single-camera by design;
  no cross-camera offset is assumed.
- **Official evaluation:** the engine is deliberately **not** wired into
  `RealEventReplayProducer`/`Phase12EvaluationRunner` (those remain gated by the
  readiness/EVAL-AUTH contract). Activation in an authorized official run is a researcher
  decision (`BLOCKED_BY_AUTHORITY`).

## 6. Raw-media boundary audit — `IMPLEMENTED` for the cache-only path

Static evidence:

- `grep -nE 'cv2|VideoCapture|ffmpeg|subprocess|av\.open|frame_generator|extract_audio|\.mov|\.mp4|\.wav' cache_only_engine.py`
  matches only the docstring naming INV-CACHE-1 and the `PROHIBITED_EXTENSIONS` blacklist
  constant. There are no imports of cv2, av, subprocess, audio_extractor, layer_b,
  layer_b_processor, or vision.video.
- Import surface: stdlib (`hashlib`, `json`, `math`, `dataclasses`, `pathlib`, `typing`)
  plus `data.sync.SyncAligner`, `fusion.collector`, `fusion.decision_engine`,
  `fusion.evidence`, `simulation.runner` — none of which decode media for already-typed
  `EvidenceRecord` inputs.
- Fail-closed paths verified: missing cache file -> `CACHE_FILE_MISSING` (no fallback);
  invalid manifest -> refusal before any artifact read; hash/size/line-count mismatch ->
  refusal; unsupported condition -> explicit refusal; sync misregistration -> collector
  raises (no less-restrictive alignment path exists in the engine).

Dynamic evidence (tests, all passing): `TestRawMediaIsolation` monkeypatches
`cv2.VideoCapture` (if importable), `subprocess.run`/`Popen`,
`vision.video.frame_generator`, and `data.audio_extractor.extract_audio_from_video` to
raise on invocation, then proves zero invocations across: valid B1 replay, missing cache
artifact, invalid manifest, sync failure, and an injected parser exception.

Legacy raw-media routes (`LayerBEventProcessor`, `scripts/run_phase5_full_inference.py`,
`scripts/run_real_world_experiments.py`) remain present and unchanged; they are
unreachable from this engine. Legacy-path behavior is `NOT_VERIFIED` by design — those
scripts were not executed.

## 7. Synthetic test commands and exact outcomes

All commands run with `.venv/bin/python` (Python 3.11.15, project venv) from the
repository root. Every fixture lives in pytest `tmp_path`; no project media touched.

| Command | Outcome |
| --- | --- |
| `-m pytest tests/unit/test_cache_only_replay.py -q` | **64 passed** in ~0.85 s |
| Same + the 12-module baseline suite from the 2026-10-26 audit | **346 passed** in 7.82 s |
| `-m pytest tests/unit/test_cache_only_replay.py tests/unit/test_phase12_official_replay.py tests/unit/test_phase12_evaluation_runner.py -q` | **171 passed** in 7.68 s |
| `-m pytest tests/unit/test_phase12_documented_metrics.py tests/unit/test_phase12_metric_arithmetic.py -q` | **28 passed** in 0.85 s |
| `.venv/bin/ruff check` on engine, tests, and `evaluation/__init__.py` | All checks passed |

Coverage categories: A. valid inputs (manifest/records, zero timestamps, zero confidence,
empty detections, determinism, B0/B1/B2, multi-modality); B. invalid inputs (missing/
malformed/empty manifest, bad version, missing fields, missing event, unsupported
condition, missing cache file, hash mismatch, truncation, non-finite/out-of-range
confidence, negative timestamp, missing record fields, end<start, non-boolean horn flag,
absolute/traversal/media-extension/disallowed-extension/symlink-escape paths, manifest
media references, bad sha256 format, manifest outside root); C. fail-closed (unavailable-
evidence invariant, audio-silence and audio-only no-opening, missing-evidence refusal,
refusal records, exception cannot switch modes); D. raw-media isolation (5 spy tests);
E. fusion/state-machine regression (no evidence -> IDLE, silence -> IDLE, audio alone
never closes gate, out-of-order/duplicate rejection, explicit sync metadata, repeated-run
determinism); plus record-validator unit tests.

Not run: the full repository-wide suite (several modules have known pre-existing failures
per prior audits; they were not touched here). No whole-repository pass is claimed.
Behavior on real events: `NOT_VERIFIED`. No official metric results were produced from
synthetic fixtures — these are software tests only.

## 8. Remaining defects and incomplete requirements

1. **Back-camera streams not supported.** The design's manifest schema (§3.3) declares
   only `front_vision_cache`/`front_audio_cache`; `back_vision` cache support is
   unspecified there and therefore not implemented (documented ambiguity; no invented
   contract).
2. **Checksums are mandatory** per the design schema; the engine validates them and has
   no optional-checksum legacy mode (intentional, fail-closed).
3. **No official evaluation integration.** `Phase12EvaluationRunner` /
   `RealEventReplayProducer` still use the manifest-bound serialized-evidence path;
   replacing them with the cache-only engine requires researcher authorization.
4. **No real cache artifacts exist** (`data/cache/` absent). Producing them requires
   running frozen-model inference — an execution-gated, researcher-authorized operation.

## 9. Governance and scientific blockers — `BLOCKED_BY_AUTHORITY`

Unchanged from prior reports; this session made no selection:

- Protocol version conflict (committed v8/v6 vs worktree v9/v7) unresolved.
- Premature-opening definition (`t1_entry_to_t4_clearance` vs
  `first_blocked_to_t4_clearance`) undecided; M4 remains `first_blocked_to_t4_clearance`
  at code level (`evaluation/metrics.py:94`), neither profile is defaulted, and M4 is not
  redefined as a `[T2,T3]` interval. M4 remains non-evaluable from front-camera-only
  evidence where T4 belongs to the back-camera clock.
- No approved ground truth created or promoted; no candidate calibration promoted; no
  frozen policy modified; no EVAL-AUTH, annotation approval, official evaluation,
  real-data inference, or timing pilot executed or fabricated.

## 10. Next steps

**Engineering (no authority required):**
- Synthetic contract tests for back-vision cache once a schema is specified.
- Optional cache-manifest builder (hashing existing JSONL artifacts only — never media)
  behind the execution gate, for when real caches exist.
- mypy pass on the new module once the repo mypy baseline is addressed.

**Researcher decisions required:**
- Select the effective protocol version and the premature-opening profile.
- Authorize (or not) activation of `CacheOnlyReplayEngine` in the official evaluation
  path. The design document marked implementation "Awaiting Researcher Review"; this
  session implemented and synthetically tested the engine but did not activate it
  officially.
- Approve ground truth, sync scope, and evaluation authorization before any real run.

## Run instructions (synthetic-only tests)

```bash
cd /Users/sayemuddin/Desktop/Train_automation
.venv/bin/python -m pytest tests/unit/test_cache_only_replay.py -q
```