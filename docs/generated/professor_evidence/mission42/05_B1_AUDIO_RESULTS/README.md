# B1_audio corrected held-out results

Five original front-container embedded acoustic tracks produced **423 windows and 120 model-positive windows at score≥0.37**. Per-event positive/all windows are105/158,4/105,0/14,0/98,11/48 in the fixed event order. The engine and designated control stay separate. Windows overlap; scores are neither correctness probabilities nor horn counts. No video imagery or standalone development horn recording entered the audio model.

A demonstrated preprocessing defect was corrected: training used log(mel_energy+epsilon), while the former runtime used dB features. The classifier now uses the trained natural-log transform with explicit cache identity. The general feature API retains its legacy dB default. Checkpoint, normalization, threshold, seed, sources and feature/window parameters remain frozen; no retraining or favorable-result tuning occurred.

The final423/120 outputs are distinct from the preserved superseded dB423/80 diagnostics. The earlier partial attempt/retry and complete corrected invocation have separate manifests/logs. They are not added together as extra experiments. Unwindowed tails are retained as sample counts without padding. Successful per-member pipeline times exclude model initialization/superseded attempts and do not prove real-time operation.

- [B1_AUDIO_RESULTS.md](reading_views/docs/generated/research_results/mission39/B1_AUDIO_RESULTS.md)
- [B1_AUDIO_EVENT_SUMMARY.csv](originals/docs/generated/research_results/mission39/B1_AUDIO_EVENT_SUMMARY.csv)
- [TRAINING_RUNTIME_FEATURE_CORRECTION.json](originals/docs/generated/research_results/mission39/audio_followup/TRAINING_RUNTIME_FEATURE_CORRECTION.json)
- [CORRECTED_AUDIO_RUN_MANIFEST.json](originals/docs/generated/research_results/mission39/audio_followup/CORRECTED_AUDIO_RUN_MANIFEST.json)
- [ACTUAL_AUDIO_RUN_MANIFEST.json](originals/docs/generated/research_results/mission39/audio_followup/ACTUAL_AUDIO_RUN_MANIFEST.json)
- [AUDIO_AND_B2_INPUT_RESULT_VALIDATION.json](../06_B2_INPUT_ASSEMBLY/originals/docs/generated/research_results/mission39/audio_followup/AUDIO_AND_B2_INPUT_RESULT_VALIDATION.json)
- [README.md](reading_views/docs/generated/research_results/mission39/audio_followup/legacy_db_diagnostic/README.md)
- [run_embedded_audio_corrected.py](originals/docs/generated/research_results/mission39/audio_followup/invocations/run_embedded_audio_corrected.py)
- [B1_AUDIO_WINDOW_PREDICTIONS.png](originals/docs/generated/research_results/mission39/figures/B1_AUDIO_WINDOW_PREDICTIONS.png)
- [B1_AUDIO_SOURCE_PROBABILITIES.png](originals/docs/generated/research_results/mission39/figures/B1_AUDIO_SOURCE_PROBABILITIES.png)
