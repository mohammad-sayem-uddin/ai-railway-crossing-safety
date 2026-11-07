# Mission 39 consolidated research results

Date 2026-11-07, America/New_York. **EMPIRICAL_EXPERIMENT_EXECUTED=1 — B0_FRONT AND B0_BACK ORIGINAL INFERENCE EACH COMPLETE ON 5/5 SOURCES.** Reference-dependent evaluation remains unavailable; the entire research programme is not claimed complete. Actual model outputs, per-source/class tables, native-clock validation, timings, figures, exact invocation/logs and scoped authorization evidence are retained. The professor/publication package was not prepared.

## Human status recorded as directed

**HUMAN_REVIEW_REPORTED_COMPLETE=1; FIVE_FRONT_EVENTS_REVIEWED=5; RESEARCHER_CLASSMATE_REPORTED_EXACT_AGREEMENT=1; ORIGINAL_SEPARATE_OBSERVATION_RECORDS_STORED=0; FORMALLY_ACCEPTED_CANONICAL_GT=NOT_ESTABLISHED.** The researcher’s current workflow decision supersedes any generic repeat-review priority in earlier missions. [Human status](HUMAN_REVIEW_STATUS.json) keeps the two reported human passes, classmate familiarity and AI comparison separate. No new reviewer request, reconstructed observation, invented signature/date/qualification or automatic GT promotion.

## Direct answers to the seventeen requested questions

1. **Scientifically defined experiments?** Five current adopted directions in the existing register: B0_front, B0_back, B1_audio, B2_front and optional exact-eleven R04. The register contains 156 activity rows (129 Type1, 26 Type2, one paused admin), including 16 related current research/reference/analysis rows; it is not 156 distinct executable experiments. All IDs are covered once in [the complete matrix](EXPERIMENT_EXECUTION_MATRIX.csv).
2. **How many executable?** Two original-data inference stages were genuinely admitted and executed under separate OP39-I and OP39-B scopes. The other current directions require separate scope/inputs or remain optional/deferred. Ten previously completed support rows are reused, not ten new empirical experiments; all current software modules were attempted.
3. **How many actually executed?** Two original-data inference stages: B0_front 5/5 and B0_back 5/5, totaling ten camera source members over five physical pilot events. Zero accepted-GT metric/replay evaluations. Raw descriptor summaries share those runs and are not extra experiments.
4. **How many remain and why?** Three current directions remain unexecuted: B1 requires actual acoustic-member/feature/operation inputs; B2 depends on supporting audio; R04 is optional/deferred. The two GT-dependent visual comparisons also remain unavailable. Undefined/retired activities are not silently promoted into the execution queue.
5. **B0_front all five originals?** Yes: 1079 saved native-PTS sampled-frame prediction records; 13 frames containing detections and 13 predicted objects. These are per-frame model outputs, not unique trains or correctness labels.
6. **B0_back?** Yes, original inference completed on all five backs under separate genuine scope: 1,100 native-PTS sampled records, 274 frames with model detections and 276 per-frame predicted objects. Separate generic camera_2 evidence, not a front cache alias or adopted clearance/GT result. [Back results](B0_BACK_RESULTS.md).
7. **B1_audio?** Not executed; exact adopted acoustic members/feature/clock role and operation scope remain missing. Existing V3 digest, normalization and 0.37 threshold were safely verified as model metadata, not an audio experiment. No video substitute or invented sound.
8. **B2_front?** Not executed; supporting-audio dependencies and actual multimodal binding remain missing. Fusion remains exploratory.
9. **M4/M5/MTR/T1/warning/control/engine metrics?** None of the GT-dependent metrics calculated. Actual raw prediction counts/class confidences/source PTS and offline processing times were calculated from the real outputs.
10. **Actual results and denominators?** The separate tables give five fronts and five backs; sampled-frame counts are denominators only for raw descriptors, never GT accuracy. Front predicted classes: 2 front/0 rear/11 side = 13 objects. Back predicted classes: 40 front/4 rear/232 side = 276 objects. Per-class scores are in the separate [front](B0_FRONT_PREDICTED_CLASS_SUMMARY.csv) and [back](B0_BACK_PREDICTED_CLASS_SUMMARY.csv) tables. No empirical GT numerator/denominator or confidence interval is fabricated.
11. **Genuine tables/graphs?** [Event table](B0_FRONT_EVENT_SUMMARY.csv), [class table](B0_FRONT_PREDICTED_CLASS_SUMMARY.csv), [object-count figure](figures/B0_FRONT_PREDICTED_OBJECTS.png) and [processing-time figure](figures/B0_FRONT_PROCESSING_TIME.png). The analogous [back event table](B0_BACK_EVENT_SUMMARY.csv), [back count figure](figures/B0_BACK_PREDICTED_OBJECTS.png) and [back timing figure](figures/B0_BACK_PROCESSING_TIME.png) are genuine outputs too. Four empirical prediction/timing figures plus one software outcome figure are retained. Programme/software tables are not additional model experiments.
12. **Software totals?** Final full run: 3807 cases across 167 modules, **3689 passed, 87 raw failures, 31 raw errors, zero skips**. The failure/error cases are exactly the **118 historical protected dependencies**, a subset of raw failures/errors, not an additional count. No new unresolved software failures; whole repository is not fully passing. Initial and final runs are separate, not added together.
13. **Bugs fixed?** Two test-maintenance defects: live archival-loader coupling in semantic unit fixtures and missing/stale coarse test-inventory entries. Historical bindings/guards remain unchanged; no failing test disabled. No production/scientific algorithm change in Mission39.
14. **Which results need accepted GT?** M4, NEVER_PROTECTED_M5, MTR/lead-in, T1/warning and truth-based control/engine/FP-FN/accuracy/censoring/uncertainty comparisons. [Analysis disposition](METRIC_AND_STATISTICAL_ANALYSIS.md) states exact dependencies. Reported exact agreement is not substituted for retained canonical field values.
15. **Main limits?** Five selected single-site sources, no accepted field-level GT, correlated sampled frames, literal prediction labels, one offline CPU environment with recorded library warnings. No safety improvement, causal/all-weather/real-time/deployment or held-out benchmark claim.
16. **Experiments remaining?** Actual acoustic inputs/scope for B1, B2 dependencies, optional separately adopted R04 and reference-dependent analysis inputs. The two visual raw stages are complete and need no routine rerun. Retired/prohibited/unadopted conditions are enumerated without revival.
17. **Next priority?** Identify/supply the actual adopted B1 acoustic-member manifest/clock/feature role and scope, then execute B1 and dependent B2 where legitimate. Reuse both real visual outputs. Do not repeat human review or assemble a professor folder as a substitute.

## Actual front results

| Existing event/front source | Sampled frames | Frames with model detections | Pipeline wall seconds |
|---|---:|---:|---:|
| train_events/event_005 | 398 | 0 | 32.605 |
| train_events/event_021 | 267 | 6 | 22.206 |
| engine_events/event_001 | 40 | 0 | 3.440 |
| train_events/event_001 | 250 | 6 | 18.744 |
| no_train_events/event_001 | 124 | 1 | 21.314 |

Front wall times sum to **98.308 seconds**. Front model outputs on event005 and engine001 are genuinely empty above threshold; no source/frame set was excluded to improve results. One model detection occurs on the designated control source, without a measured false-positive claim. Engine remains a separate case. See [B0 results](B0_FRONT_RESULTS.md) for interpretation and actual hashes.

## Exact execution and software provenance

Baseline main HEAD `9472535e252b8b74a6e78b79f064f762c3037e6e`; tracking origin/main `fc3c29a761deaa9e36eca1e5eea4e0205b1f9a74`, unchanged/no push. Actual inference code commit `9472535e252b8b74a6e78b79f064f762c3037e6e` with two test-only maintenance changes in the worktree; production source/config unchanged. Exact executed script SHA `b3f5715f7e74e8526098845964cca3eeea0de7c0fe9a7de6388fbd80d5d1a475` is retained under invocations/, and actual command/stdout/stderr hashes under [result validation](B0_FRONT_RESULT_VALIDATION.json). Model SHA `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`; semantic frozen config `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`. Python/package/device/seed/backend args and actual run times are in [run manifest](ACTUAL_RUN_MANIFEST.json).

All 1,079 front rows validate against the existing front-cache row parser; all 1,100 back rows validate and round-trip exactly through existing generic EvidenceRecord serialization with source_id=camera_2. Both sets retain original PTS×timebase1/600 and exact absolute video indices. Prior AUTH35-V source identity/stat bindings were reused and checked stable across inference; no original-media rehash/probe/preview or source mutation. The existing constructor integrity check was enforced at actual run, not bypassed. Actual authority confirmation was received, transcribed into the canonical mechanism and validated at actual point of use; both single-use scopes are closed, issued/closed evidence preserved and the canonical slot restored to baseline absence. No allowlist change, fake grant, GT promotion or descriptive replay authorization.

Complete software validation used the existing guarded runner across all modules. [Software report](SOFTWARE_VALIDATION_REPORT.md), [full evidence](SOFTWARE_VALIDATION_RECEIPT.json), raw initial/final receipts and per-case table retain exact commands/outcomes/durations/source bindings. Initial fixture/inventory failures were fixed; final resource failures remain the same 118 historical dependencies. Guarded synthetic software evidence is not empirical research, and Python hooks are not OS isolation.

All 262 pinned prior researcher/Mission21–38 artifacts, seven original private AUTH35-V files and seven preexisting researcher worktree paths are preserved. Original records/model/config/policy and prior experiment outputs are not overwritten. New private derived runtime caches are retained separately; no raw videos are copied into this results directory. Only exact new results/receipts/figures and the two justified test/inventory files are staged for a local commit, with final hash/status verified after commit. No broad staging, reset/clean/amend/rebase/force-push/history rewrite or push.

See [failure/limitation register](FAILURE_AND_LIMITATION_REGISTER.md) and [next phase](NEXT_RESEARCH_PHASE.md). No professor folder, manuscript/journal search, new training/CV/split/threshold/inferential test/sensor/hardware, physical T2/occupancy/RD046, acoustic GT shift or invented exit.

## Independent back results and model-input clarification

Back native-camera results: 1,100 sampled records, 274 frames with detections, 276 predicted objects and 174.395 summed event wall seconds. Back peak RSS 465,780,736 bytes. No cross-camera alignment, back human review, class-to-clearance rule or GT metric is inferred. The original raw back manifest is retained; its global human-workflow context flag has been clarified in the current manifest to refer only to the reported five fronts, without altering source/prediction/time data. Validation binds both manifest versions.

The existing Audio V3 file was hashed for the first time in this workflow and matches ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782. Safe weights-only metadata loading confirms frozen norm_mean -1.600999355316162, norm_std 5.1239728927612305 and threshold0.37. No acoustic samples or model forward pass; [identity receipt](AUDIO_V3_INPUT_IDENTITY_RECEIPT.json). The remaining B1 source selection is not filled from historical training lists or a visual-video substitute.

## Actual back results — independent camera clock

| Existing back source/event | Sampled frames | Frames with model detections | Pipeline wall seconds |
|---|---:|---:|---:|
| train_events/event_005 | 391 | 0 | 40.690 |
| train_events/event_021 | 307 | 230 | 54.007 |
| engine_events/event_001 | 49 | 13 | 8.808 |
| train_events/event_001 | 231 | 7 | 58.847 |
| no_train_events/event_001 | 122 | 24 | 12.044 |

Back event wall times sum to 174.395 seconds. These are the same five physical pilot events viewed from the other camera, not five additional independent events. Back source005 emitted no above-threshold detections; the back engine case and designated control emitted raw predictions without a correctness/clearance claim. No cross-camera timing alignment or pooled performance calculation.

## Delivery consistency checks

[Delivery validation](MISSION_39_DELIVERY_VALIDATION.json) passes: all 2,179 saved prediction records retain exact native clocks and serializer validity; event/class totals agree with actual manifests, both closed grants retain valid record/scope hashes, and lossless logs match captured output hashes. Ten Markdown documents and 50 relative links validate; all six CSVs round-trip, including every one of the 156 original activity IDs and 3,807 software outcomes. Both back manifest versions differ only in the explained front-only human-review context. All 262 prior pins, seven private verification artifacts and the original seven researcher changes remain preserved. Current complete source bindings match the final full test run, with only the two justified test/manifest changes versus the starting snapshot. No extra inference or original-source verification was run for delivery checks.

New private derived runtime outputs remain untracked at data/cache/b0_front/mission39_20261107T202523Z/, data/cache/b0_back/mission39_back_20261107T204353Z/ and the two corresponding results/experiments/cache/ run directories. They are preserved and excluded from staging. The containing local commit hash is reported after commit; origin/main remains unchanged and nothing is pushed.
