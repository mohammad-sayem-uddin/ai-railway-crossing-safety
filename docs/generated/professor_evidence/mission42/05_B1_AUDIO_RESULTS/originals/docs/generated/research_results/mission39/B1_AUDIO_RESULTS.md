# B1_audio held-out acoustic results

**ORIGINAL_ACOUSTIC_INFERENCE_COMPLETE=5/5; WINDOWS=423; MODEL_POSITIVE_WINDOWS=120; ACCEPTED_GT_EVALUATIONS=0.** The intended V3 natural-log feature transform is used. No standalone development audio or video imagery enters the audio model.

| Existing front-container event | Windows, 1s/0.5s hop | Model score≥0.37 | Mean model score | Member pipeline wall seconds |
|---|---:|---:|---:|---:|
| train_events/event_005 | 158 | 105 | 0.506208 | 0.667 |
| train_events/event_021 | 105 | 4 | 0.125046 | 0.388 |
| engine_events/event_001 | 14 | 0 | 0.063163 | 0.098 |
| train_events/event_001 | 98 | 0 | 0.058334 | 0.350 |
| no_train_events/event_001 | 48 | 11 | 0.291184 | 0.479 |

The designated control has 11 model-positive windows and the engine case has zero. These are correlated window predictions, not horn/train counts or accuracy. Engine and the designated control stay separate; no measured FP/FN, human agreement or event-presence rate is inferred. Unwindowed tails stay explicit sample counts in [the event table](B1_AUDIO_EVENT_SUMMARY.csv); no duration padding. Wall times include audio clock decoding, conversion, inference, serialization and B2 input assembly, excluding model initialization and superseded attempts. No real-time/deployment claim.

The [inventory receipt](audio_followup/HELD_OUT_ACOUSTIC_RECONCILIATION_RECEIPT.json) reconciles56 historical rows,54 candidate camera members/27events and two duplicate exclusions. [Exact path checks](audio_followup/EXACT_MEMBER_LOCATION_RECEIPT.json) locate all 54. The videos/ root is retired; active paths are data/raw/layer_b/v2/. Exactly five fixed pilot fronts are processed, following the existing front-audio B1 condition. The 87 standalone horn recordings remain model-development data. The inspected training manifest has no candidate path/container-hash overlap; this is not a global waveform/origin independence proof or a new full-cohort execution claim.

**Concrete correction:** actual V3 preprocessing source uses log(mel_energy+epsilon); the runtime had used dB features. The classifier now uses the trained natural-log transform, with explicit cache identity tagging; the general feature API retains its legacy dB default. Exact training-source parity and classifier-normalization tests pass. [Correction evidence](audio_followup/TRAINING_RUNTIME_FEATURE_CORRECTION.json). Frozen model/checkpoint SHA ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782, normalization, threshold0.37, FFT512/hop256/mel64/80–8000Hz,64×61 shape,1s/0.5s windows,CPU/seed42 and five sources are unchanged. No retraining, threshold choice or favorable-result selection.

All 423 earlier dB-scale windows, including80 positive predictions, are retained as [superseded diagnostics](audio_followup/legacy_db_diagnostic/README.md), never added to final totals. An initial integral-sample-ratio check stopped three members before inference; only those three were retried at that stage. The subsequent demonstrated feature defect justifies repeating the five acoustic inferences with the intended transform. Both earlier attempt manifests/logs remain intact. Generated PCM checks validate resampler rounding, not a new scientific tolerance.

Temporary private AUTH35-V files became unavailable during interruption. Their old verification is retained through repository evidence, not claimed freshly reread. The corrected invocation requires exact equality of current extracted PCM digests and complete native PTS ledgers to the persisted actual diagnostic identities, with source stat stability. All five pass. Audio indices 1,1,1,1,0 and native 1/48000 clocks are retained; causal output times derive from integer sample positions. PCM stays in memory, with no raw/derived audio file copied into results or a synthetic directory. Prior container hashes remain prior references, not newly computed hashes. Native acoustic continuity is not physical synchronization or GT.

[Corrected actual run](audio_followup/CORRECTED_AUDIO_RUN_MANIFEST.json), [current union](audio_followup/ACTUAL_AUDIO_RUN_MANIFEST.json), [result validation](audio_followup/AUDIO_AND_B2_INPUT_RESULT_VALIDATION.json), exact invocation, original-derived JSONLs, issued/closed scopes and lossless logs are retained. Both visual predictions are reused unchanged. No GT/decision replay/promotion or raw release occurs.

Figures: [window counts](figures/B1_AUDIO_WINDOW_PREDICTIONS.png), [actual source traces](figures/B1_AUDIO_SOURCE_PROBABILITIES.png). Scores are not correctness probabilities or calibrated safety evidence.
