# Official Replay Producer (Phase 12) — Contract and Status

**Status:** implemented and tested with synthetic fixtures. **No official or real-data result exists.** With the real repository, `evaluation run` exits `3` (blocked at readiness) before reading any evidence.

## 1. What it does

`RealEventReplayProducer.produce(root)` (`evaluation/replay_producer.py`):

1. re-assesses live readiness itself (recorded EVAL-AUTH, decisions, receipt, manifest, frozen artifacts); any blocker raises `ReplayFailure` before any payload is read;
2. loads the manifest with source hashes verified (twice, to catch change during validation) and requires its digest to equal the digest EVAL-AUTH binds;
3. replays **only test-split events**; train/validation payloads are never parsed;
4. validates each payload (`evaluation/replay_evidence.py`) against its manifest identity, the decided camera scope, the live frozen config and checkpoints;
5. builds frames with `MultimodalEvidenceCollector` and runs `EventSimulationRunner(config=frozen)` **without any labels**, so ground truth can neither influence nor be derived from a replay;
6. returns all replays or raises; there is no partial result.

`Phase12EvaluationRunner.run_official(...)` then loads Stage-2.1 ground truth from the repository (cohort-qualified identities, test events only), evaluates clock-aware (`evaluation/clock_aware.py`), and writes outputs to a staging directory that is moved into place only on success. `run_official_safe` returns/writes a structured failure report instead of raising.

## 2. Evidence payload (`phase12-replay-evidence/1`)

The manifest `source_path` of each event is one JSON file with exactly: `schema_version`, `event_id` (cohort-qualified, e.g. `train_events/event_001`), `cohort`, `camera_mode`, `streams`, `provenance`. There is **no field for labels or boundary times**; unknown keys are refused. `streams` may hold `front_vision` (`camera_1`), `back_vision` (`camera_2`), `front_audio` (`audio_1`), each `{source_id, records[]}` with serialized `EvidenceRecord`s as already produced by the frozen models (`build_replay_evidence_payload` packages existing records; **no model is run by this code**). `provenance` must carry `annotation_labels_used: false`, the live frozen-config canonical hash, both checkpoint hashes (Audio V2 is refused), the frozen vision/audio thresholds, media SHA-256s, an inference run id and `generated_by`.

| `camera_mode` | required streams | forbidden | replayed timelines |
|---|---|---|---|
| `single_camera` | `front_vision` | `back_vision` | `front` |
| `independent_camera` | `front_vision`, `back_vision` | — | `front`, `back` (separate clocks, no offset) |
| `dual_camera` | `front_vision`, `back_vision` | — | `fused` (validated offsets) |

`front_audio` is optional everywhere. `dual_camera` additionally requires: the event in the researcher's `accepted_sync_events` (decision contract), a `CALIBRATION_SUPPORTED` calibration entry (readiness check `R04_ACCEPTED_EVENT_NOT_SUPPORTED`), calibrated media hashes equal to the payload's, and a measured uncertainty. Per protocol v9 §7: ≤ 0.5 s is `aligned`, ≤ 2.0 s `partially_aligned` (recorded with a latency error bound), larger or unmeasured is `unaligned` and refused (`SYNC_UNALIGNED`).

## 3. Clock-aware evaluation

Each boundary is compared only on a timeline that has an offset for the camera it was annotated on (T1 front, T4 back). A metric needing boundaries from two clocks is computed only on a fused timeline; otherwise it is `not_evaluable` with a stated `clock_mismatch` reason (listed in `cohort_summary.exclusions`). No zero offset is ever assumed. Boundary-dependent flags are derived from recorded steps with the same predicate as the runner (a test asserts equality).

## 4. Failure codes (structured, all-or-nothing)

`OFFICIAL_PREREQUISITES_UNSATISFIED`, `MANIFEST_BINDING_MISMATCH`, `SOURCE_HASH_MISMATCH` (and other input codes), `IDENTITY_MISMATCH`, `SCOPE_MISMATCH`, `SCOPE_VIOLATION`, `LABEL_LEAKAGE`, `PROVENANCE_MISMATCH`, `PROHIBITED_CHECKPOINT`, `PAYLOAD_INVALID`, `STREAM_INVALID`, `RECORD_INVALID`, `SYNC_NOT_ACCEPTED`, `SYNC_CALIBRATION_REJECTED`, `SYNC_MEDIA_MISMATCH`, `SYNC_UNALIGNED`, `REPLAY_ERROR`, `GROUND_TRUTH_REFUSED`, `GROUND_TRUTH_CAMERA_MISSING`, `CLOCK_ORDER_INVALID`, `OUTPUT_DIR_PROTECTED`, `OUTPUT_DIR_NOT_EMPTY`, `EVALUATION_RUNTIME_ERROR`. The failure report (`<output-dir>.failure_report.json`) is the only file written on failure.

## 5. CLI

`python -m railway_detection evaluation run --output-dir D` → `3` blocked at readiness, `2` ready but no `--output-dir`, `5` verified run failed (report written, no outputs), `0` success. `evaluation status` prints readiness, categorized blockers and `live_bindings`.

## 6. Not implemented / not claimed

- Producing the evidence payloads from raw media (running YOLO / the audio CNN) — payloads package existing frozen-model outputs; the Phase 5 raw predictions are the natural source but are not packaged here and were not used.
- Camera- and audio-level false-detection counts (`N_cam_FP`, `N_audio_FP`).
- The design document's M4 premature-opening window (pending `[D-10]`).
- Anything about real events: all tests use synthetic fixtures labelled as such, in temporary directories.

## 7. Additions (overnight 2026-10-16)

- **Identity.** Official identities are cohort-qualified (`train_events/event_001`); `event_001` exists in three cohorts. The readiness gate, readiness CLI, promotion gate and ground-truth loader previously keyed per-event data by the bare id, which would have refused (duplicate approved record) or mixed up a genuine corpus; fixed and covered by `tests/test_phase11_cohort_qualified_identity.py`.
- **"Real" is not self-declared.** A manifest's `evidence_classification: real` is a label. The gate additionally requires every manifest event to be a cohort-qualified key of `data/manifests/layer_b_v2_annotation_inventory.json` with the same cohort, and every test-split event to have an approved Stage-2.1 record; `run_official` requires the payload's media hashes to equal the media the approved reviewer observed (`EVIDENCE_MEDIA_NOT_REVIEWED_MEDIA`).
- **Premature opening.** `premature_opening_window` has no default anywhere. Without an explicit, implemented window the metric is *not computed* and is listed as excluded (`premature_opening_window_undecided`).
- **Failure codes added:** `EVIDENCE_MEDIA_NOT_REVIEWED_MEDIA`, `INPUT_CHANGED_DURING_VALIDATION` (review records changed between readiness and loading).

### Races (validation vs. consumption) — what is closed and what is not

| Input | Handling |
|---|---|
| Evidence payloads and manifest | Read once through a file descriptor with `O_NOFOLLOW`; the digest and the parsed object come from the same bytes. The manifest is loaded twice and compared. **Closed.** |
| Review records | `load_approved_ground_truth_with_hashes` parses the same bytes it hashes; the hashes must equal those the readiness gate observed (`INPUT_CHANGED_DURING_VALIDATION`). **Closed** between assessment and load. |
| Frozen config, policy, checkpoints | Verified by the readiness assessment immediately before replay; the config is then re-read by the producer. A swap in that interval would be caught only by EVAL-AUTH binding on the *next* run. **Narrow window remains.** |
| Calibration media (dual-camera) | Hashed by `load_validated_sync_aligner` at replay time, not at readiness. **Not covered by a pre-run binding.** |
| Output | Staged then moved atomically; a crash leaves only a `.<name>.partial` directory that the next run clears. |

None of the remaining windows can be closed without OS-level locks or immutable snapshots; run official evaluations on a quiescent checkout.
