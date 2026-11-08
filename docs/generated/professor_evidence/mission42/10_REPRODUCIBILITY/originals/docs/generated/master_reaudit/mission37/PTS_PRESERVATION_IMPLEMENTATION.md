# Mission 37 original-PTS integration

**IMPLEMENTED_AND_FIXTURE_TESTED; ORIGINAL_RECORDINGS_NOT_DECODED.** The real defect was nominal `frame_index/native_fps` timing in vision/video.py. The default legacy API remains compatible; opt-in `source_pts=True` uses actual decoded frame PTS/timebase through PyAV. It does not call nominal FPS a source clock. Header rate differences alone establish neither VFR nor a measured timing error.

## Changed paths and operational use

- `src/railway_detection/vision/video.py`: optional PTS decoder, absolute video stream selection, rational sampling and original clock metadata on VideoFrame. Existing media authorization precedes source checks and decoder access.
- `src/railway_detection/experiments/layer_b_processor.py`: opt-in parameters on **LayerBEventProcessor.run_vision_inference** and build_stream_provenance; original clock metadata retained in EvidenceRecord; separate cache identity and strict timing/frame failure behavior. This is the actual class/method, correcting the earlier documentary shorthand `_process_vision` without altering historical reports.
- `scripts/review_source_pts.py`: neutral visual frame browser using that same decoder. It displays source PTS and frame index; creates no annotation, grant, model prediction or persistent image corpus.
- `pyproject.toml`: optional `pts` dependency on PyAV 18.1 series; no frozen config/schema/policy edits.
- `tests/synthetic_mission37/test_source_pts.py`: generated codec fixtures and constructed predictions/browser display calls; no original/model data.

After actual operation permission and runtime acceptance, the relevant existing method is called with `source_pts=True, video_stream_index=<absolute verified video index>`. Cache provenance is built with those same arguments. The five B0 fronts use indices 0,0,0,0,1 in the unchanged Mission36 source order. These are not video-ordinal indices. No real inference command was invoked or recorded as executed.

```python
# API usage only, not an executed or authorized original-source invocation.
provenance = processor.build_stream_provenance(
    cohort=cohort, event_id=event_id, source_id=source_id,
    modality="vision", run_id=run_id,
    source_pts=True, video_stream_index=video_index,
)
records = processor.run_vision_inference(
    video_path, checkpoint_path, source_id,
    target_fps=5.0, conf=0.35, provenance=provenance,
    source_pts=True, video_stream_index=video_index,
)
```

The legacy multimodal processor constructor still checks both vision/audio safeguards; it was not used to open unrelated real assets. This snippet assumes an actually accepted, appropriately scoped processor/runtime initialization. It is not a ready-made five-event CLI and does not impose audio-model permission as a scientific prerequisite for visual B0. The official replay/test-split path and descriptive cache authorization are unchanged. Do not bypass them or use test `object.__new__` setup as production initialization. Actual source/model/preprocessing and replay bindings must be recorded when that route is authorized.

## Clock contract

PyAV exposes frame.pts and frame.time_base; its documentation describes presentation time as their product ([time](https://pyav.org/docs/stable/api/time.html), [frame API](https://pyav.org/docs/stable/api/frame.html)). Implementation tested with installed PyAV 18.1.0:

1. Select an actual video stream by absolute `stream.index`; decode that stream only, no audio playback.
2. Require integer PTS and positive rational timebase on every decoded frame. Reject missing/invalid/negative PTS, duplicate or decreasing presentation times, empty streams and decoding failures. Validation includes frames omitted by sampling. No nominal-FPS fallback, fabricated zero timestamp or interpolation.
3. Keep `pts_ticks`, `(numerator, denominator)`, `stream_index`, `stream_start_pts` and decoded `frame_index`. `timestamp_s=float(pts_ticks*timebase)` keeps nonzero origins; no silent rebase. Rational original fields retain exact time even though existing timestamp_s is floating point. Source clock identity is separate from capture timezone, physical synchronization and original hardware identity.
4. Time sampling selects the first actual frame on/after each requested grid deadline anchored at the first decoded PTS, advancing the grid past that frame. It never duplicates a frame to fill a gap. Optional stride selects decoded indices while retaining their actual PTS. These implementation semantics need actual run/protocol binding; the requested 5 FPS parameter is unchanged.
5. Decode BGR arrays to preserve the previous OpenCV input convention. EvidenceRecord.timestamp_s uses actual presentation time; metadata carries the exact fields through existing JSON serialization/cache/evaluation collector records. Existing collector master-grid timestamps are separate from original observation timestamps; there is no original-clock renormalization in the tested handoff.
6. New provenance preprocessing includes `timestamp_basis=source_pts` and explicit video_stream_index; existing configuration hash separates these caches from legacy FPS-derived caches. Mode/index mismatches or missing controlled provenance with cache use fail before reuse. New-mode media authorization precedes model/cache access. New-mode frame/prediction/decoder errors propagate before any cache write; no failed frame becomes an empty negative detection. Legacy behavior stays unchanged.

## Actual validation and limits

52 selected cases pass: 24 new PTS/browser cases and 28 existing compatibility/refusal cases. Generated lossless FFV1 in a NUT container has nonzero PTS 900000,900090,903600,909000 at timebase 1/90000; optional audio stream 0 makes video stream 1. Tests cover raw clocks, irregular intervals, stream selection, grid/stride sampling, invalid/missing/unsorted clocks, empty stream, JSON handoff into evaluation collector frames, cache isolation, failure-before-output and authorization-before-decoder. Browser tests replace GUI display calls while decoding generated pixels, checking navigation and neutral labels. They do not certify native GUI usability, a human's observation, original MOV decoding, real model predictions, a full replay/metric run or production deployment.

Final [test evidence](FOCUSED_VALIDATION_RECEIPT.json) binds exact executed nodes, source hashes and genuine raw test files. Initial test API mistakes and a later protected-dependent legacy test refusal remain reported. New video/browser modules pass scoped mypy; the processor retains one identical preexisting bbox tuple typing error, proven against HEAD. Ruff passes the new modules/test; processor passes with E501 ignored (14 unchanged preexisting long lines). No whole-repository acceptance, current old-Mission29 classification or scientific performance is claimed. Python audit hooks are not OS isolation.
