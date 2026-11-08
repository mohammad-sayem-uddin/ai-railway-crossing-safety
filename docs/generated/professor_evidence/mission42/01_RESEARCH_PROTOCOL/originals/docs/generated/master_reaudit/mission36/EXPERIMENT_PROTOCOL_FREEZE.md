# M36-B0_FRONT-FIVE — preparation freeze

**FREEZE_PREPARED; RUN_NOT_AUTHORIZED_OR_EXECUTED.** This pins known scientific inputs/configuration/code and explicitly marks unresolved live bindings; it is not a fully verified run manifest or a new protocol adoption. Decision remains EXECUTABLE_AFTER_HUMAN_REVIEW with the co-requirements in FIRST_EXPERIMENT_EXECUTION_DECISION.md. No scientific threshold, label, metric, source role or data split is changed.

## Identity, question and scope

Experiment identifier M36-B0_FRONT-FIVE; existing condition B0_front (actual cache-engine condition string is B0, never an assumed CLI alias). Question: descriptive front-camera vision approach/warning/feasibility behavior on the existing five-event pilot subset under the frozen policy, with legitimate matching human reference and metric-specific eligible denominators. Three train cases, one no-train control and one separate engine case; this is not a held-out accuracy benchmark or all-weather/safety experiment. The five back partners remain available for independently scoped human evidence and later B0_back, never unaligned T4 borrowed into front metrics.

Software baseline commit: `c7c271b70d6ce4bc57e27a57abc2ec6f5a2a600c`. Preparation code/config/input document bytes are bound in the final report ledger. Actual future inference/evaluation command, environment/package versions, operator, private output, runtime invocation/code hash and exact grant: **NOT_RECORDED — no run occurred**. Do not infer a runtime environment receipt from installed dependencies or a Git commit alone.

| Event | Exact selected front reference | AUTH35-V fresh = historical SHA-256 | Video index | Header timebase / start PTS |
|---|---|---|---:|---|
| train_events/event_005 | doc:v2:train_events/event_005:front:video | `015ec78146d474385e447232c9c4048263bf0491cfbf265e967bb0d6bf887613` | 0 | 1/600 / 0 |
| train_events/event_021 | doc:v2:train_events/event_021:front:video | `380dcddbcd4fefab43f27134a5965e2b724b3c3cc707ad2bce514b0defb4c518` | 0 | 1/600 / 0 |
| engine_events/event_001 | doc:v2:engine_events/event_001:front:video | `d91b7d7f9cf4ddb9842d58185b59aed6e45de323a7c364dc15b62398269a0a28` | 0 | 1/600 / 0 |
| train_events/event_001 | doc:v2:train_events/event_001:front:video | `d80bd6565b066eddb099325db790823d0dfd6b416380965f5f2b280ea1af832b` | 0 | 1/600 / 0 |
| no_train_events/event_001 | doc:v2:no_train_events/event_001:front:video | `58b03f81169df9e67acf24627d7311e1f3a214c81647f41b03979442b2a4045f` | 1 | 1/600 / 0 |

No new recording, 27-event inventory expansion, test split or replacement easy-only sample. Retain 27 candidate events (23 train/three no-train/one engine), two duplicate-camera exclusions; R04 remains exactly eleven/event_010 excluded. Never exclude an unfavorable source after seeing results.

## Model, configuration and preprocessing

| Binding | Frozen known value / unresolved actual state |
|---|---|
| Frozen experiment config | configs/frozen_experiment_v1.yaml; raw YAML SHA-256 `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a` |
| Canonical semantic config identity | `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`; matches policy_metadata.reference_frozen_config_sha256; raw YAML and canonical JSON identities are distinct, not a configuration defect |
| Decision policy | configs/decision_policy_v1.yaml; raw SHA-256 `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575`; existing version v1.0.0 |
| Selected model candidate | YOLOv8n; declared path `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` |
| Expected checkpoint SHA-256 | `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` — declaration only; actual checkpoint NOT_OPENED/NOT_HASHED/NOT_LOADED and identity remains NOT_VERIFIED |
| Declared class map | 0 front / 1 rear / 2 side; historical single-class/class-role ambiguity retained; these names do not prove direction or detection validity |
| Declared vision preparation | Target 5.0 FPS; configured image size [640, 640]; approach/departure confidence 0.35/0.35; actual backend application/resize/normalization/version must be bound, not assumed from defaults |
| Seed / device | 42 / cpu; no new stochastic repeats or hardware profiling |
| Existing policy timing | Tick 0.1 s; nominal vision sampling 0.2 s; warning 2.0 s; closing 3.0 s; clearance dwell 3.0 s; opening 3.0 s; retain existing staleness/confirmation/fault rules |
| Audio/fusion in B0 | No audio inference/model required solely for visual B0; supporting-audio and exploratory fusion conditions remain separate; prohibited Audio V2 inactive |

Source preprocessing must preserve the actual video stream index and original decoded frame PTS/rational timebase, frame/source origin and any accepted local mapping. AUTH35-V's header start_pts/time_base is evidence, not the missing decoded-frame mapping. Static inspection of vision/video.py shows timestamps_for_frames = frame_index/native_fps and frame_generator uses those values; sampling uses rounded nominal-FPS steps. Header nominal/average rates differ for some sources, which does not itself prove a per-frame error/VFR pattern, but header evidence cannot certify the index/FPS sequence as original source PTS. Do not silently call that legacy path PTS-preserving. No decoded-frame check, algorithm correction, new dependency or new threshold is introduced here. Actual authorized producer/clock binding must be resolved before source-clock-sensitive results; unknown values stay explicit.

## Input/output schemas and route constraints

Source manifest binding: current ten-source integration, with the five fronts above selected for B0. Actual model-evidence input schema for an accepted existing official producer is phase12-replay-evidence/1, with event/cohort/camera_mode/streams/provenance and no annotation-label channel; its official manifest/test-split/EVAL-AUTH path is not adopted here. Existing cache B0 has its own real-cache manifest and AUTH-DESCRIPTIVE-EVAL-EXEC requirements. Neither shape can be fabricated from hashes or a synthetic adapter. Exact approved raw-to-evidence/replay route and real output manifest remain **NOT_BOUND**.

Human input uses the existing domain Observation/BoundaryObservation records and later active canonical 8.1.0-stage2.1 where applicable, not a proposed 8.2 schema. Actual human session/reviewer-observed hashes, independence/proposal lineage and canonical parents are not prefilled by AUTH35-V. No protected review corpus/proposal/GT is opened. The human package specifies the actual fields and stage-specific acceptance.

Planned outputs only: exact per-source model/evidence provenance and logs, camera-local outcome records, legitimate GT/metric-input binding, eligible per-event/per-camera metrics, null/uncertainty/censoring/error records and a run receipt/environment/command manifest in an actually approved private destination. No output rows/files are created as experiment results. Existing evaluation.metrics.SingleEventEvaluation is a relevant metric serialization type; any selected route's exact serializer/schema/version must be recorded at run, not invented as already produced. No model detections or old candidate labels flow into human GT.

## Metrics, exclusions and uncertainty

M4 remains the primary premature-opening endpoint, requiring matching T4 plus adequate causal replay coverage under its actual metric contract. M5 is the NEVER_PROTECTED_M5 integer companion only when its full-coverage condition is supported, never a substitute for missing/incomplete replay or GT. In a front-only analysis, report either only eligible matching front endpoints or explicit NOT_EVALUABLE/null reasons; never import unaligned back T4 to force a result. T1 approach/warning timing and MTR's adopted feasibility role apply only with their relevant actual reference/lead-in/screen evidence. Time diagnostics, missed-train rates and the feasibility screen are not interchangeable; no new regulatory lead-in or scientific threshold is added.

Use separate per-metric train/negative-control/engine eligibility and denominators; engine is a separate case excluded from pooled train M4/M5/occupancy statistics. No-train controls have no invented train T1–T4 boundaries. Preserve actual per-camera LEFT/RIGHT censoring, UNCERTAIN/NOT_OBSERVABLE states and missing/null reasons; null is not zero. No global “five is N for every metric”, imputation, averaging disputed boundaries, outcome-driven omission or new significance/confidence method. Only already-adopted summaries/intervals with legitimate denominators may later be used; none is computed now.

Physical T2/occupancy and RD046 sufficiency remain deferred, no lens-plane substitute/invented exit; T3 and T4 are not assumed identical for engine. Comparator remains inactive. Existing active-schema 30-second human-session plausibility floor is unchanged and must reflect real timing, never padding; it is not scientific duration sufficiency or an empirical tolerance.

## Failure handling and reproducibility acceptance

Before an actual run, bind actual source hash snapshot, real relevant GT/review version, selected actual checkpoint/config/backend/preprocessing/PTS method, code/runtime/packages/device/seed, exact grant/operator/purpose/private output/log/retention/validity and actual command. Preserve raw outputs/stdout/stderr/receipt and all denied/failed/missing cases without rewriting. Exact runtime versions/commands/repetition are only recorded if a real run occurs. Do not run the official CLI as a substitute for missing inputs or create a split to satisfy it.

Stop for changed source/model/config, missing/wrong/expired/withdrawn operation scope, missing relevant human truth, exposure/identity/clock mismatch, unavailable original-preserving records, incompatible actual schema, incomplete replay coverage or unsupported backend mapping. Retain partial evidence as such; no performance result or new threshold is invented. A new hash/header pass is not demanded absent a specific discrepancy; reuse AUTH35-V. Reproducibility of future outputs is pending an actual authorized run and complete receipt, not established by parsing this freeze.
