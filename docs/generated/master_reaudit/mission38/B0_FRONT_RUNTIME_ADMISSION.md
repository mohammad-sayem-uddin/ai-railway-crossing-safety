# Mission 38 B0_front runtime admission

**SOFTWARE_ROUTE_CONNECTED; MODEL_LOADED_ON_CPU; ORIGINAL_SOURCE_INFERENCE_NOT_ADMITTED.** Existing experiment M36-B0_FRONT-FIVE / descriptive cache condition B0 remains the selected target. All source hashes below are reused from completed AUTH35-V, and the checkpoint digest from Mission37; no original was opened/probed/hashed or checkpoint rehashed here.

| Event | Exact selected front reference | Established source SHA-256 | Absolute video index |
|---|---|---|---:|
| train_events/event_005 | doc:v2:train_events/event_005:front:video | `015ec78146d474385e447232c9c4048263bf0491cfbf265e967bb0d6bf887613` | 0 |
| train_events/event_021 | doc:v2:train_events/event_021:front:video | `380dcddbcd4fefab43f27134a5965e2b724b3c3cc707ad2bce514b0defb4c518` | 0 |
| engine_events/event_001 | doc:v2:engine_events/event_001:front:video | `d91b7d7f9cf4ddb9842d58185b59aed6e45de323a7c364dc15b62398269a0a28` | 0 |
| train_events/event_001 | doc:v2:train_events/event_001:front:video | `d80bd6565b066eddb099325db790823d0dfd6b416380965f5f2b280ea1af832b` | 0 |
| no_train_events/event_001 | doc:v2:no_train_events/event_001:front:video | `58b03f81169df9e67acf24627d7311e1f3a214c81647f41b03979442b2a4045f` | 1 |

All candidate paths remain `data/raw/layer_b/v2/<event>/camera_front.mov` for these exact five rows. crossing_A remains the existing site label, not a new physical-site verification. No back source, optional R04, audio, official split or extra cohort is added to B0_front.

## Actual connected route

`camera_front.mov → frame_generator(source_pts=True, video_stream_index=...) → LayerBEventProcessor.run_vision_inference → EvidenceRecord → serialize_front_visual_record → existing front visual JSONL/cache manifest → CacheOnlyReplayEngine.load_visual_records/execute_replay(B0) → existing reference-dependent metric contract`.

Three demonstrated integration gaps were closed in the existing modules:

1. **Scoped initialization:** `LayerBEventProcessor(..., vision_only=True)` checks selected vision weights and timing safeguards without creating audio directories, opening audio/retired weights or requiring audio-model access. Default initialization still checks all original safeguards. Vision-only audio initialization/extraction refuses. Future authorized constructor verification still checks the selected model; it was exercised only with temporary fixture weights here. Actual production checkpoint verification was reused, not rerun.
2. **Frozen inference arguments and cache identity:** new front-only `process_front_vision` selects only camera_front.mov, exact video index and native PTS, and requires run_id plus software commit. New-mode prediction explicitly binds 5 FPS/0.35 through the frozen config, image target 640×640, CPU, seed 42, square letterbox (`rect=False`), float32 (`half=False`) and no image/crop/text saving. Torch seed is set; the loaded class map must match the frozen map. These implement the declared image/device/seed choices; no scientific threshold is changed. Native-PTS provenance now also binds installed Ultralytics version and prediction options, preventing reuse of differently configured PTS caches. Existing configuration/software/run identity envelopes are retained.
3. **Descriptive cache handoff:** `serialize_front_visual_record` emits the existing frame_index/timestamp_sec/camera_id/detections form, preserving original clock metadata and actual class IDs. It refuses back/audio, unavailable or legacy-FPS evidence. The existing reader validates exact PTS/timebase/index consistency and retains those fields with its hash-bound cache provenance. A B0 front-only manifest can omit front_audio_cache; B1/B2 still refuse absent audio instead of fabricating it. Manifest version remains 1.0.0; old dual-stream manifests remain supported. The optional clock metadata is prediction metadata, not a new annotation schema.

The source-PTS reader/browser from Mission37 was reused unchanged. Missing/invalid/duplicate/decreasing source PTS and decode/prediction failures remain fail-closed before cache writes. No missing observations are turned into negative detections. Legacy inference defaults remain compatible. Existing collector and simulation runner use actual presentation timestamps; a generated-codec integration test now verifies a nonzero source time reaches the actual B0 replay result step without normalization to nominal FPS.

After actual approval, the API connection is concrete (not invoked on originals here):

```python
processor = LayerBEventProcessor(
    repo_root=repo_root, cache_dir=approved_controlled_cache_dir,
    config=frozen_config, vision_only=True,
)
records = processor.process_front_vision(
    approved_event_dir, video_stream_index=approved_absolute_index,
    run_id=actual_run_id, git_commit=actual_software_commit,
)
rows = [serialize_front_visual_record(record) for record in records]
```

The operator writes those rows to the existing JSONL format and binds exact content hash/size/count in the existing cache manifest; no manifest or cache for genuine sources is created now. After its actual current authorization, `CacheOnlyReplayEngine.execute_replay(event_id, "B0", ...)` consumes that manifest. Supply the existing frozen decision engine/policy configuration and actual accepted human reference/metric coverage to the downstream existing evaluation path; do not use retired runner aliases or silently treat a default engine as a verified scientific profile. A fake temporary-root authority or official EVAL-AUTH/test-split shortcut is not used for real data. No automatic promotion or new metric adapter was added.

## Actual MacBook compatibility

[Model-loading receipt](MODEL_LOADING_RECEIPT.json): the exact previously verified YOLOv8n checkpoint loaded using Ultralytics.YOLO(path, task="detect"), then `.model.to("cpu").float().eval()`. Loaded DetectionModel, classes 0 front/1 rear/2 side, 3,011,433 parameters; FP32 parameter storage 12,045,732 bytes and buffers 42,056 bytes. No forward pass, original decode or prediction occurred. Receipt records current stat identity and stability, reusing prior digest `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` rather than hashing again. No discrepancy was found; matching historical digest is not claimed as newly computed.

Python 3.11.15; Torch 2.13.0; torchvision 0.28.0; Ultralytics 8.4.121; PyAV 18.1.0; OpenCV 5.0.0.93; NumPy 2.4.6. CPU is frozen/used; CUDA unavailable and MPS available but not selected. Physical memory 8,589,934,592 bytes (8 GiB). Model initialization took 2.461 s; process peak RSS after loading 293,634,048 bytes (about 280.0 MiB). This demonstrates loading compatibility and model residency, not original five-event forward compatibility, throughput or peak inference memory. A 1×3×640×640 float32 input alone is 4,915,200 bytes; activations/decoder buffers/native images and retained prediction records add memory, with decoded BGR image cost 3×width×height bytes. Runtime streams frames but retains output records; event duration/detection density affect that cost. Full workload memory/time remain unmeasured. No replacement model, dependency change or hardware profiling was performed.

[Actual stdout](MODEL_LOADING_STDOUT.txt) includes an Ultralytics configuration warning: the requested private config parent did not exist and the library fell back to `/tmp/Ultralytics`, creating default settings there. No credentials/settings contents were read. For a future invocation, create the accepted private YOLO_CONFIG_DIR before import. This warning did not prevent loading; no second load was commissioned merely to remove it. Network/autoinstall were disabled through library settings; this is not OS isolation. No model or dependency was downloaded.

## Applicable operation boundaries and concrete requests

Live canonical record checks in this mission found **both absent**: `data/governance/AUTH-MEDIA-ACCESS.json` and `data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json`. Code was inspected without reading private GT/caches. Mission38 requests/authorizes technical model-loading compatibility and implementation work; it supplies no actual reviewer acceptance or narrowly approved original-use statement. AUTH35-V remains completed/expired verification only.

| Operation | Current disposition / actual existing requirement |
|---|---|
| Local verified-checkpoint initialization, no forward/source use | Performed under requested runtime compatibility scope; not an inference grant |
| Source presentation and original-frame decoding | Pending actual source-use method/assignment and current READ_RAW_MEDIA scope; browser guard unchanged |
| Original-frame model inference | Pending current INFERENCE plus READ_RAW_MEDIA on the exact five fronts; no human reference is required merely to calculate predictions, but this permission is absent |
| Private prediction storage | Must be explicitly scoped with the inference operation and actual destination/retention; no predictions generated |
| Descriptive replay and reference-dependent metrics | Existing AUTH-DESCRIPTIVE-EVAL-EXEC bound to the actual cache manifest, protocol, metric scope, config and genuine promotion/reference receipt; absent; relevant reference evidence absent |
| Official evaluation/publication/raw release | Separate; not proposed or used as universal private-preparation prerequisites |

**OP38-I — concrete pending inference-stage scope for researcher approval:** current Codex acts only as local technical operator, using the exact containing Mission38 implementation commit, the five front references/hashes/absolute indices above, the named verified YOLOv8n checkpoint and unchanged frozen config/policy. Permit source READ_RAW_MEDIA/native-PTS decode and INFERENCE at frozen 5 FPS, 640×640, confidence 0.35, CPU, seed 42 and the explicitly bound backend options; preserve exact PTS/timebase, every processed/failed case, actual logs and prediction JSONL/cache provenance in a fresh owner-only local run directory under `data/cache/b0_front/<actual-run-id>` with controlled cache under `results/experiments/cache/<actual-run-id>`. No source/model mutation, back/audio use, expanded events, training/tuning, review/GT, empirical metrics/replay, source render/upload/export or hardware. Hide predictions from reviewers; record actual authority/approval/validity/withdrawal and retention before execution. Bind the current point-of-use canonical raw-media record under the existing authority rules; no approval or allowlist entry is fabricated by this text. This inference leg can precede human truth after its actual scope is approved; it is not a completed B0 experiment or a newly adopted label-free scientific diagnostic.

**OP38-P — concrete pending source-only review method:** actual assigned humans use the existing Mission37 browser on their exact permitted front sources, with absolute stream index and exact PTS/timebase readout, no model/expected/cohort answers, actual session/clock/exposure records and original-preserving notes/seals. The researcher supplies real assignment/acceptance and approves the actual display/storage/access method first. A first-pass-only front stage does not claim completed ten-source canonical pilot; any back partner review uses the separately scoped existing human protocol, never B0 inference.

Neither request is an issued grant, signature, appointment, consent or exemption. No generic new authorization form is demanded. Actual applicable external conditions remain relevant at their real scope. An existing label-free replay computation is not itself a separately adopted model-only research experiment: the frozen selected B0 question requires matching reference for its metrics, and no original inference/replay grant is present in any case. No substitute diagnostic was executed or relabeled B0.
