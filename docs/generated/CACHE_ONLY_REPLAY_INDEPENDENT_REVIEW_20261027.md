# Train Gate Automation — Cache-Only Replay Independent Review & Integration-Readiness Audit

**Date:** 2026-10-27 (UTC)
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`
**Branch / HEAD:** `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (unchanged)
**Labels:** `VERIFIED`, `TESTED_SYNTHETICALLY`, `PARTIALLY_VERIFIED`, `NOT_VERIFIED`, `BLOCKED_BY_AUTHORITY`, `BLOCKED_BY_MISSING_EVIDENCE`

## A. Executive summary

The prior implementation and reported 64-test result were independently reproduced. The
review found a material contract defect: **B1 loaded front vision plus front audio**, while
the established B0/B1/B2 specification defines B1 as front-audio-only. It also found that
the claimed hash-before-parse guarantee had a TOCTOU gap: one file snapshot was hashed and
a second snapshot was parsed.

Authorized repairs now:

- B1 is audio-only; B2 remains front vision + front audio.
- Manifest/cache artifacts use one descriptor snapshot (`O_NOFOLLOW` on the final path
  component); size and SHA-256 are checked before decode/parse.
- Duplicate JSON keys, event-key mismatches, unsupported camera IDs, invalid class IDs/names,
  invalid strides, and protected output roots fail closed.
- Cache artifact provenance is preserved in typed evidence metadata and replay output.
- Deterministic run IDs bind condition, stride, and synchronization configuration.
- Batch replay records unexpected per-event errors as structured refusals.
- Validated manifest data is returned as a deep copy.

Final status: **82 dedicated synthetic tests pass**, **364 tests pass** in the prior baseline
selection plus cache tests, **189 tests pass** in the cache + official-shaped evaluation
selection, **28 metric tests pass**, and Ruff is clean. The standalone cache-only engine is
`VERIFIED`/`TESTED_SYNTHETICALLY`; official activation remains `BLOCKED_BY_AUTHORITY`; real
cache artifacts remain `BLOCKED_BY_MISSING_EVIDENCE`. Synthetic tests do not establish real-
world detection accuracy, benchmark performance, synchronization quality, or railway safety.

## B. Repository preservation

- Root: `/Users/sayemuddin/Desktop/Train_automation`.
- Start/end branch and HEAD: `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`.
- Start: 19 tracked modifications and a large pre-existing untracked research set; all
  preserved. No staged entries.
- No stage, commit, push, reset, clean, broad revert, or unrelated deletion occurred.
- Audit-touched paths: `src/railway_detection/evaluation/cache_only_engine.py`,
  `tests/unit/test_cache_only_replay.py`, and this report.
- `metrics.py`, `data/r04_evidence.py`, `protocol_choices.py`, frozen configs, protocol
  docs, ground truth, and synchronization implementation have empty diffs.
- No project `.mov`, `.mp4`, or `.wav` was opened, decoded, previewed, or hashed. Fixtures
  used pytest temporary directories only.

## C. Prior claims independently checked

| Claim | Independent result |
|---|---|
| Engine exists at reported path | `VERIFIED`; 771 lines before repair |
| 64 dedicated tests pass | `VERIFIED`; reproduced before repair |
| Historical selected regression suite passes | `VERIFIED`; baseline remained green after repair |
| Ruff passes touched files | `VERIFIED`; all checks pass |
| M4 preserved | `VERIFIED`; `evaluation/metrics.py:94` remains `first_blocked_to_t4_clearance` |
| Official evaluation unactivated | `VERIFIED`; producer/runner not wired or changed |

## D. Defects found and repairs

### R-01 — B1 condition leakage — `VERIFIED` fixed

`docs/B0_B1_B2_METRIC_SPECIFICATION.md` and `docs/B0_B1_B2_ARCHITECTURE_AUDIT.md`
define B0 = front vision, B1 = front audio, B2 = front multimodal fusion. The engine's
`CONDITION_STREAMS["B1"]` incorrectly contained both streams, and its prior test expected
15 records. It now contains `front_audio` only. `test_b1_condition_audio_only` and
`test_b1_ignores_strong_visual_detections` enforce the corrected contract.

### R-02 — Hash-before-parse TOCTOU — `VERIFIED` fixed

The design's `INV-CACHE-3` requires the hashed bytes to be the parsed bytes. Previously,
`_verify_cache_file()` hashed one open and `_load_cache_stream()` reopened the path. The new
`_read_snapshot()` uses `os.open(..., O_NOFOLLOW)` and `_read_verified_snapshot()` checks
size/hash on one byte snapshot; manifest and JSONL are decoded/parsed from that same snapshot.
A directory-component symlink race remains `PARTIALLY_VERIFIED` under an adversarial
filesystem threat model; final-component descriptor use is stable.

### R-03 — Duplicate keys — `VERIFIED` fixed

`_reject_duplicate_json_keys` is used for the manifest and cache records, refusing hidden
conflicting values instead of silently keeping the last key. Dedicated duplicate-key tests
were added.

### R-04 — Manifest identity — `VERIFIED` fixed

`_validate_event_entry()` now refuses `MANIFEST_EVENT_ID_MISMATCH` when an event key and
its declared `event_id` differ. A dedicated test covers it.

### R-05/R-06 — Camera and class identity — `VERIFIED` fixed

Visual cache records must declare `camera_front`; `class_id` must be a non-negative integer
and `class_name` a non-empty string. Dedicated unsupported-camera and invalid-class tests
cover these paths.

### R-07 — Provenance — `VERIFIED` fixed

Every loaded `EvidenceRecord` retains event, stream, artifact path, and artifact SHA-256 in
`metadata["provenance"]`; `ReplayOutput.provenance` records manifest hash, condition, stride,
sync summary, and cache paths. Tests cover both modalities and B2.

### R-08 — Protected output boundary — `VERIFIED` fixed

`output_base_dir` must remain under `<repo_root>/results/replays` (`OUTPUT_DIR_PROTECTED`),
matching design `INV-CACHE-4`. The current engine returns in-memory output and does not write
files, but the boundary is enforced before future output use.

### R-09 — Manifest mutation — `VERIFIED` fixed

`manifest_data` now returns `copy.deepcopy`; nested mutation cannot alter validated state.

### R-10/R-11 — Determinism and stride — `VERIFIED` fixed

The run ID now binds manifest hash, event, condition, stride, window tolerance, and sync
summary. Non-numeric/non-finite/non-positive stride refuses with `INVALID_FRAME_STRIDE`.
Tests cover changed IDs and repeated-run state reset.

### R-12 — Batch errors — `VERIFIED` fixed

`replay_all_events()` catches per-event exceptions and records `ReplayRefusalRecord` with
an explicit exception code or `REPLAY_ERROR`; no fallback or fabricated success occurs.
Batch outcome and media-spy tests cover this.

### Deliberately unresolved contract gaps

- The design manifest schema defines front caches only; back-camera cache support is not
  invented (`BLOCKED_BY_MISSING_EVIDENCE`).
- The design says “signed manifest” but defines no signature algorithm, key source, or
  verification field; external authenticity is a future design/authority decision.
- Only `.jsonl` is accepted, matching the documented cache artifact format.

## E. Cache manifest, integrity, and evidence audit

`_load_and_validate_manifest()` checks required fields, exact version `1.0.0`, non-empty
cohort, event structure, cache references, SHA-256 format, positive line/byte counts,
repository-bound paths, event identity, and recursive media references. `_validate_cache_path()`
rejects absolute paths, `..` traversal, prohibited media extensions, non-JSONL extensions,
and resolved escapes. Final cache loading verifies existence, regular-file type, byte size,
SHA-256, UTF-8 decoding, line count, duplicate keys, object type, and record schema before
creating typed evidence.

Visual records preserve explicit zero timestamps and require finite non-negative timestamps,
front camera identity, valid class IDs/names, finite boxes, and `[0,1]` confidence. Audio
records preserve zero-valued start/end timestamps, require `end_sec >= start_sec`, finite
confidence in `[0,1]`, boolean horn flags, and stamp evidence at the window end. A silent
or zero-confidence audio window produces no detection. Missing/empty required streams
refuse; they are never fabricated into positive evidence.

Synchronization is delegated to the existing `SyncAligner`; the engine accepts an optional
aligner and does not invent missing offsets or uncertainty. Attached aligners still trigger
the existing collector registration guard for vision sources. No candidate calibration
manifest is automatically loaded.

## F. Raw-media boundary audit

The cache engine imports only standard library plus `SyncAligner`, collector, decision engine,
typed evidence, and simulation runner. It does not import `LayerBEventProcessor`,
`layer_b_processor`, `vision.video`, `data.audio_extractor`, cv2, av, subprocess, ffmpeg, or
model loaders. The reachable path is:

```
manifest snapshot/validation -> verified JSONL snapshot -> EvidenceRecord
-> MultimodalEvidenceCollector -> EventSimulationRunner
```

`EventSimulationRunner._run_frames()` resets the decision engine and gate model before each
run. The collector rejects duplicate and out-of-order observations. Legacy raw-media routes
remain present but are not reachable from this engine (`NOT_VERIFIED` for those legacy paths).

Dynamic media-loader spies cover valid B1, missing cache, malformed manifest, sync refusal,
parser exception, hash mismatch, corrupt record, unsupported condition, and batch refusal.
All pass. Spies cover known loaders; arbitrary future imports are outside this test bound,
and directory-component symlink races remain `PARTIALLY_VERIFIED`.

## G. Fusion/state-machine safety audit

Actual implementations inspected: `fusion/evidence.py`, `fusion/collector.py`,
`fusion/rules.py`, `fusion/decision_engine.py`, `simulation/runner.py`, and
`source_tracker.py`.

| Requirement | Implementation evidence | Tests |
|---|---|---|
| Missing evidence cannot open | no qualified approach keeps controller IDLE | missing-evidence tests |
| Silence cannot open | no audio detections trigger rules | audio-silence test |
| Audio alone cannot close/fabricate clearance | vision clearance path required | audio-only closing test |
| Explicit sync required | aligner refuses omitted offset/uncertainty | sync metadata test |
| Duplicate/out-of-order refusal | collector logs/drops observations | duplicate/order tests |
| Unavailable evidence cannot carry detections | `EvidenceRecord.__post_init__` | unavailable-evidence test |
| State reset | runner resets engine and gate each run | repeated-event test |
| Determinism | deterministic sort + configuration-bound ID | repeated-run/stride tests |

These tests exercise the real decision path but remain synthetic and are not a physical
safety argument.

## H. Metrics and research contracts

`evaluation/metrics.py:94` still defines `M4_WINDOW = "first_blocked_to_t4_clearance"`.
No M4/M5 arithmetic or protocol choice changed. The unresolved premature-opening profile
remains non-defaulted. Front-camera-only replay cannot empirically evaluate a metric
requiring T4 from the back-camera clock. Metric tests are synthetic only; no official
results were produced.

## I. Test reproduction and exact outcomes

All commands ran from the repository root with `.venv/bin/python`; no real media was
accessed.

| Command | Result |
|---|---|
| `-m pytest tests/unit/test_cache_only_replay.py -q` | **82 passed** in 1.20 s |
| Prior 12-module baseline list + cache tests | **364 passed** in 8.79 s |
| Cache + official-replay/evaluation tests | **189 passed** in 7.68 s |
| Two metric modules | **28 passed** in 0.12 s |
| Ruff on engine, tests, and `evaluation/__init__.py` | **All checks passed** |
| Decoder/fallback grep on engine | Only intentional docstring/blacklist matches |

The historical 64-test result was reproduced before repair. The final suite is 82 tests;
the increase is independent regression coverage. The full repository-wide suite was not
run, so no whole-repository pass is claimed.

## J. Integration-readiness assessment

### `RealEventReplayProducer`

`evaluation/replay_producer.py` consumes hash-bound `phase12-replay-evidence/1` payloads,
validates frozen configuration/checkpoints, reassesses readiness/EVAL-AUTH, handles camera
scope and accepted synchronization, and returns `EventReplay`/`SystemReplay`.

The cache engine consumes a cache manifest plus detector-record JSONL and returns
`ReplayOutput` wrapping `SimulationRunResult`. Mismatches are the evidence schema,
provenance requirements (frozen config/checkpoints versus cache hashes), authorization
lifecycle, and camera scope. A safe adapter would need to translate cache streams into the
existing evidence-payload contract and bind the readiness gate. It is not implemented or
activated here.

### `Phase12EvaluationRunner`

`run_official()` re-runs readiness through `RealEventReplayProducer`, loads approved
Stage-2.1 ground truth, evaluates `EventReplay` clock-aware, and writes atomic outputs.
Cache replay produces `SimulationRunResult` and has no approved-ground-truth/EVAL-AUTH
binding. Wiring requires a deliberate adapter and authority decision; it was not changed.

**Integration status:** standalone compatibility `PARTIALLY_VERIFIED`; official integration
`BLOCKED_BY_AUTHORITY`.

## K. Scientific validity and governance blockers

Synthetic tests verify software behavior only. They do not establish detector accuracy,
recorded-footage synchronization quality, benchmark results, generalization, physical gate
performance, or railway safety.

Untouched blockers:

- committed protocol v8/v6 vs worktree v9/v7;
- premature-opening choice (`t1_entry_to_t4_clearance` vs
  `first_blocked_to_t4_clearance`);
- approved ground truth and calibration authority;
- EVAL-AUTH and official evaluation authorization;
- real cache artifacts and model inference.

Status: `BLOCKED_BY_AUTHORITY` / `BLOCKED_BY_MISSING_EVIDENCE`.

## L. Next steps

### Safe engineering

1. Specify/review a back-camera cache schema before implementing back-camera support.
2. Design a non-activated adapter to the existing `EventReplay` contract with synthetic
   provenance/readiness tests.
3. Define manifest signatures only after specifying algorithm, key provenance, and
   rotation/revocation requirements.
4. Run mypy after the repository baseline is repaired.

### Researcher decisions

1. Select effective protocol document version.
2. Select premature-opening profile.
3. Approve ground truth and synchronization scope.
4. Authorize or reject official cache-engine activation.

### Execution gates

No official evaluation, real-data inference, timing pilot, or candidate promotion may run
until authority records, approved evidence, valid caches, and gate bindings exist.

## Synthetic-only run command

```bash
cd /Users/sayemuddin/Desktop/Train_automation
.venv/bin/python -m pytest tests/unit/test_cache_only_replay.py -q
```

