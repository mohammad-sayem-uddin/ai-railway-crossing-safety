# Reading copy — REMAINING_METRIC_EVALUATION.md

Derived presentation copy: local links are adapted for this package. Evidence text and historical status retain their original scope. Consult the current executive guide for the final result status. [Byte-identical original](../../../../../originals/docs/generated/research_results/mission40/REMAINING_METRIC_EVALUATION.md). Original SHA-256: `4ab20c5d53a6215b73471b2cf3caddffd9297f6c7f1a2ec36ba1ae4c37764a3e`.

# Remaining metric evaluation

Mission40 read and validated saved actual outputs; no original inference or decision replay ran. Thirty per-event raw descriptor rows (six existing descriptor families × five events) were calculated. Ten truth/replay evaluation families remain unavailable. The [metric register](../../../../../originals/docs/generated/research_results/mission40/METRIC_EXECUTION_REGISTER.json) records execution, exact numerators/denominators or null with reasons, source references, exclusions, missing observations, censoring and uncertainty for every family.

| Existing event | Front sampled frames / predicted objects | Back sampled frames / predicted objects | Audio score≥0.37 windows / all windows | Both-record B2 inputs / all input frames |
|---|---:|---:|---:|---:|
| train_events/event_005 | 398 / 0 | 391 / 0 | 105 / 158 | 236 / 398 |
| train_events/event_021 | 267 / 6 | 307 / 230 | 4 / 105 | 158 / 267 |
| engine_events/event_001 | 40 / 0 | 49 / 14 | 0 / 14 | 21 / 40 |
| train_events/event_001 | 250 / 6 | 231 / 7 | 0 / 98 | 147 / 250 |
| no_train_events/event_001 | 124 / 1 | 122 / 25 | 11 / 48 | 72 / 124 |

These are raw counts, not event-detection rates, accuracy, precision, recall, F1, FP or FN. The rows are the same five physical events, not additional independent samples. Engine and designated control remain separate. Cameras retain independent clocks; front/back counts do not establish relative quality. Audio windows overlap, so no independence assumption or new interval is applied. All 13 front/276 back object outputs and120 of423 threshold-crossing audio windows match the existing actual saved results.

B2 input coverage is634 of1079 frames with both stream records;445 have no audio record within the existing causal assembly window. This is not proof of a missing audio source or a reason to pad/interpolate. The existing assembly tolerance0.25s and audio hop0.5s are unchanged. Every original visual PTS and causal integer-sample acoustic timestamp is verified through the saved serialization. [Source/hash checks](../../../../../../10_REPRODUCIBILITY/originals/docs/generated/research_results/mission40/RETAINED_OUTPUT_ANALYSIS_RECEIPT.json), [per-event table](../../../../../originals/docs/generated/research_results/mission40/PER_EVENT_DESCRIPTIVE_RESULTS.csv).

| Scientific endpoint | Executed? | Numerator / denominator | Exact unavailable dependency |
|---|---|---|---|
| M4 primary / M5 integer companion | No | null / null | Accepted eligible T4/reference and legitimate causal replay/coverage |
| MTR feasibility / lead-in screen | No | null / null | Accepted lead-in/screen/control exposure and actual eligible population |
| T1 / warning correctness | No | null / null | Accepted camera-local T1 plus actual warning/replay outputs |
| Control false alarms / exposure | No | null / null | Accepted control truth/exposure; folder names and model scores are not truth |
| Engine identity/timing correctness | No | null / null | Accepted engine-specific observations; no pooled train endpoint |
| FP/FN, accuracy, precision, recall, F1 | No | null / null | Legitimate matching labels and eligibility |
| Human agreement | No | null / null | Separate original paired observations were not stored; do not reconstruct |
| Boundary censoring / uncertainty | No | null / null | Retained accepted boundary states/values/rationales absent |
| B2 decision-derived summaries | No | null / null | Actual guarded decision replay has not executed |

No sufficient active canonical record was found: the 32 inspected reference texts are unchanged, legacy schema6 records stay invalidated, and there is no promotion receipt. Human review remains researcher-reported complete and exact agreement reported; AI references stay separate. No repeat-review request or automatic promotion.

The table retains actual unwindowed audio tail sample counts and last whole-window endpoints in CSV. Those are model-window coverage descriptors, not invented human censoring states. Missing scientific values stay null, not zero; no new inferential method, confidence interval, cutoff, acoustic GT shift, exit or duration padding.
