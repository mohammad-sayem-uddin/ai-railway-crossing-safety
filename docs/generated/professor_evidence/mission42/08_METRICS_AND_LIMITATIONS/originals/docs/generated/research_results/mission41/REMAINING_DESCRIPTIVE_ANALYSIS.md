# Remaining model-only descriptive analysis

Five existing descriptor families were processed from saved outputs, without new inference/replay. Each is mapped to existing Mission31 plan IDs in [the execution register](DESCRIPTIVE_EXECUTION_RECEIPT.json), with exact command, invocation/input hashes and exclusions. Previously completed per-event/per-class tables are reused by hash; no duplicate experimental total is added.

| Existing activity | New retained processing | Interpretation |
|---|---|---|
| Visual confidence continuity/output distributions |40 source/class summaries,78 consecutive-sample runs | Literal model labels; ANY overlaps class-specific summaries and is never summed as extra objects |
| Native sampled-clock diagnostics |28 interval-frequency rows across ten visual and five acoustic streams | Source-local presentation intervals and frozen audio hop, not physical synchronization |
| Supporting audio output continuity |74 consecutive model-label runs spanning423 windows | Correlated windows at frozen0.37; not74 horns/trains or accuracy |
| B2 input-record absence detail |847 present/absent runs, plus five-event absence breakdown | Input collector only, not decision replay or fabricated negative evidence |
| Existing processing-time summaries |15 retained member times, three aggregate rows | Different measured scopes; no new timing run or controlled speed comparison |

[Visual runs](VISUAL_SAMPLE_RUNS.csv) preserve actual sample indices/native integer PTS/timebase. [Confidence summaries](VISUAL_CONFIDENCE_CONTINUITY_SUMMARY.csv) retain zero model-output rows and unavailable scores where no output exists. Contiguous means adjacent selected rows, with no new temporal-gap threshold; endpoint span is not continuous occupancy or true trailing-car dropout. [Audio runs](AUDIO_MODEL_LABEL_RUNS.csv) retain integer window sample bounds and causal ends; ambient is a model label, not proof of train/horn absence.

[Sampled-clock intervals](SAMPLED_CLOCK_CADENCE.csv): front observed selected-row intervals range0.1683333333–0.2016666667s; back0.185–0.2016666667s; audio hop exactly0.5s. These are observed sampled presentation intervals, not a measurement of source capture FPS, VFR diagnosis, physical camera alignment or clock error. Front/back native clocks are not shifted or fused. Model/source time and processing wall time remain separate.

## The 445 audio-empty input frames

| Existing event | Before first causal audio output | Later single-frame input gaps | Total input frames without audio record |
|---|---:|---:|---:|
| train_events/event_005 | 5 | 157 | 162 |
| train_events/event_021 | 5 | 104 | 109 |
| engine_events/event_001 | 5 | 14 | 19 |
| train_events/event_001 | 5 | 98 | 103 |
| no_train_events/event_001 | 5 | 47 | 52 |

There are five initial absence runs of five frames (25 total, assembly time0 through0.8s before the first causal window end1.0s), and420 later single-frame gaps. Together they account for exactly445 input frames. Presence runs are212 two-frame runs and210 one-frame runs, totaling634 paired inputs. [Exact breakdown](B2_INPUT_RECORD_ABSENCE_BREAKDOWN.csv), [full run table](B2_INPUT_AUDIO_RECORD_RUNS.csv), [figure](figures/B2_INPUT_ABSENCE_BREAKDOWN.png).

These records remain absent; no padding, interpolation or negative evidence is supplied. The later pattern belongs to the existing0.25s input collector with0.5s audio hop and0.2s assembly grid. Actual replay uses a different0.5s collector window, so the audio-empty decision-frame count remains unknown until authorized execution. This diagnostic does not run or substitute for replay.

[Processing-time detail](EXISTING_PROCESSING_TIME_DETAIL.csv) and [aggregates](EXISTING_PROCESSING_TIME_AGGREGATES.csv) reuse observed sums: front98.308s/back174.395s/audio1.983s. Audio measurement includes clock decode/conversion/inference/serialization/B2 assembly and excludes initialization/superseded attempts; visual scopes differ. These are prior observed processing times, not a new benchmark, deployment/real-time claim or fair cross-modality speed comparison. Engine and control remain separate rows; all-frame counts are not independent event denominators.

Existing class output tables stay unchanged (front13 objects:2 front/0 rear/11 side; back276:40 front/4 rear/232 side). Supporting audio has120 of423 model scores≥0.37, not a measured detection rate or correctness. No new inferential tests, scientific cutoffs, labels, metrics, GT boundaries or performance comparison are introduced.
