# Available descriptors and unavailable evaluation metrics

Available saved descriptors include per-event camera/frame/class/object counts, acoustic window scores and counts, sampled-clock cadence/continuity runs, input-record availability and actual recorded processing time. Mission40 produced 30 raw per-event descriptor rows; Mission41 added five descriptor families. These are analyses of the same saved predictions, not new inference experiments or GT evaluations.

Unavailable: M4/M5/MTR, T1-warning, truth-based control/engine outcomes, FP/FN/accuracy/precision/recall/F1, human agreement and accepted boundary censoring/uncertainty. Required actual reference fields, eligibility, accepted promotion and/or guarded replay outputs are missing. Null numerator/denominator is unavailable, not zero. N=5 is not a universal metric denominator. No rate/interval is invented from correlated frames/windows or folder names.

The pilot is selected and single-site with small bounded scope. Camera roles, source-local clocks, engine/control cases, overlapping acoustic windows, unwindowed tails and unsupported back semantic mapping limit interpretation. No safety improvement, accident reduction, fusion superiority, deployment or generalization conclusion is supported.

- [PER_EVENT_DESCRIPTIVE_RESULTS.csv](originals/docs/generated/research_results/mission40/PER_EVENT_DESCRIPTIVE_RESULTS.csv)
- [METRIC_EXECUTION_REGISTER.json](originals/docs/generated/research_results/mission40/METRIC_EXECUTION_REGISTER.json)
- [REMAINING_METRIC_EVALUATION.md](reading_views/docs/generated/research_results/mission40/REMAINING_METRIC_EVALUATION.md)
- [SCIENTIFIC_LIMITATIONS.md](reading_views/docs/generated/research_results/mission40/SCIENTIFIC_LIMITATIONS.md)
- [REMAINING_DESCRIPTIVE_ANALYSIS.md](reading_views/docs/generated/research_results/mission41/REMAINING_DESCRIPTIVE_ANALYSIS.md)
- [VISUAL_CONFIDENCE_CONTINUITY_SUMMARY.csv](originals/docs/generated/research_results/mission41/VISUAL_CONFIDENCE_CONTINUITY_SUMMARY.csv)
- [SAMPLED_CLOCK_CADENCE.csv](originals/docs/generated/research_results/mission41/SAMPLED_CLOCK_CADENCE.csv)
- [AUDIO_MODEL_LABEL_RUNS.csv](../10_REPRODUCIBILITY/originals/docs/generated/research_results/mission41/AUDIO_MODEL_LABEL_RUNS.csv)
- [EXISTING_PROCESSING_TIME_DETAIL.csv](originals/docs/generated/research_results/mission41/EXISTING_PROCESSING_TIME_DETAIL.csv)
- [EXISTING_PROCESSING_TIME_AGGREGATES.csv](../06_B2_INPUT_ASSEMBLY/originals/docs/generated/research_results/mission41/EXISTING_PROCESSING_TIME_AGGREGATES.csv)
