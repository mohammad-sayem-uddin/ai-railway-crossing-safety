# Reading copy — B2_FRONT_INPUT_ASSEMBLY_REPORT.md

Derived presentation copy: local links are adapted for this package. Evidence text and historical status retain their original scope. Consult the current executive guide for the final result status. [Byte-identical original](../../../../../originals/docs/generated/research_results/mission39/B2_FRONT_INPUT_ASSEMBLY_REPORT.md). Original SHA-256: `63f5c96159438ae06ddb6c4cff71b6fda25e3ad343f669f890b3ab39a7415e61`.

# B2_front input-stage results

**REAL_PAIRED_INPUT_ASSEMBLY_COMPLETE=5/5; INPUT_FRAMES=1079; DECISION_REPLAY=0; ACCEPTED_GT_COMPARISON=0.** Actual corrected B1 predictions and saved byte-bound front predictions were processed through the existing multimodal collector. This is an executed input stage, not a completed fusion decision experiment.

| Existing event | Input frames at0.2s stride | Frames with both stream records |
|---|---:|---:|
| train_events/event_005 | 398 | 236 |
| train_events/event_021 | 267 | 158 |
| engine_events/event_001 | 40 | 21 |
| train_events/event_001 | 250 | 147 |
| no_train_events/event_001 | 124 | 72 |

There are634 frames with both streams and445 with no audio record in the existing causal0.25s assembly window. Audio hop remains0.5s. These are input-coverage counts, not missing recordings, source-health proof, fusion accuracy or a reason to interpolate evidence. No collector parameter or timestamp was changed. The layer-B assembly tolerance0.25s differs from the cache-replay collector's existing0.5s; this stage is not substituted for replay.

Both modalities come from the same front container per event. Front original PTS is retained; audio native origin/contiguous clocks and causal sample ends are checked. All parent times are causal. No front inference, back source or cross-camera synchronization is repeated or invented. Actual assemblies, [summary](../../../../../originals/docs/generated/research_results/mission39/B2_FRONT_INPUT_ASSEMBLY_SUMMARY.csv), [coverage figure](../../../../../originals/docs/generated/research_results/mission39/figures/B2_FRONT_INPUT_COVERAGE.png) and [validation](../../../../../originals/docs/generated/research_results/mission39/audio_followup/AUDIO_AND_B2_INPUT_RESULT_VALIDATION.json) retain separate inputs; batch-ingested health flags are not performance evidence.

The [real hash-bound input manifest](../../../../../../05_B1_AUDIO_RESULTS/originals/docs/generated/research_results/mission39/audio_followup/FRONT_AUDIO_ACTUAL_INPUT_MANIFEST.json) references actual saved outputs. Existing CacheOnlyReplayEngine.execute_replay still requires current AUTH-DESCRIPTIVE-EVAL-EXEC with promotion receipt, exact manifest, protocol, metric-scope and model/config bindings. Those are not fabricated from reported human agreement or AI candidates, and no alternate ungated decision route is used. M4/M5/MTR/T1/warning/control/engine truth-based results remain unavailable. No fusion superiority, safety or complete B2 comparison is claimed.
