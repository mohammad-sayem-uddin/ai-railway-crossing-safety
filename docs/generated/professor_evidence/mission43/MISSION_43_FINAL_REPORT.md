# Mission43 actual full-cohort findings

Prepared 2026-11-08, America/New_York. **FULL27_ORIGINAL_INFERENCE_AND_INPUT_ASSEMBLY_COMPLETE; ADOPTED_REFERENCE_AUDIO_EVENT_COMPARISON_EXECUTED; B2_DECISION_REPLAY_BLOCKED; CANONICAL_GT_NOT_ESTABLISHED.** This mission executed original data rather than stopping at a plan. It does not claim completion of unsupported endpoints or a fully passing test suite.

| Existing direction | Prior five-event evidence reused | New original execution | Full27-event result |
|---|---|---|---|
| B0_front | 5 sources; 1079 records; 13 objects | 22 sources; 5534 records; 316 objects | 27 sources; 6613 records; 329 objects |
| B0_back | 5 sources; 1100 records; 276 objects | 22 sources; 5379 records; 744 objects | 27 sources; 6479 records; 1020 objects |
| B1 front embedded audio | 5 sources; 423 windows; 120 positive | 22 sources; 2177 windows; 325 positive | 27 sources; 2600 windows; 445 positive |
| B2 input assembly | 5 events; 1079 frames; 634 paired | 22 events; 5535 frames; 3263 paired | 27 events; 6614 frames; 3897 paired |
| B2 decision replay | Not executed | Not admitted | 0 decision events/frames |

All 54 exact source digests match the established inventory; all 54 have one video and one audio stream. Counts represent the same 27 physical events (23 train, 3 no-train, 1 engine), not 54 independent events. Two historical duplicate camera references remain excluded; no active event was dropped. All 44 new camera and 22 new acoustic inferences completed without errors. [27-event coverage](FULL_27_EVENT_COVERAGE_MATRIX.csv), [actual run summary](ACTUAL_FULL_COHORT_RESULTS.json).

## Actual reference adoption and evaluation

The researcher explicitly confirmed manual verification and approved the AI-assisted annotations as final, with no separate manual observations stored. [The genuine adoption receipt](RESEARCHER_ANNOTATION_ADOPTION.json) binds all 27 existing active versions/hashes. This is a positive new approval, not dismissed as no evidence. Original annotations remain unchanged; copied originals are included. The content is now a **researcher-adopted AI-assisted reference**, not independent stored human observations or automatic Stage2.1 promotion.

The existing V3 recording rule (maximum window score, frozen 0.37 threshold) supports a specifically documented exploratory comparison to explicit event horn labels. Among 23 train events (13 horn-present, 10 absent_observed), actual counts are **TP=12, FP=10, FN=1, TN=0**. Precision=54.55%, recall=92.31%, F1=0.6857, specificity=0.00%, accuracy=52.17%, ROC-AUC=0.6846, AP=0.7739. Exact counts/ranking metrics were independently cross-checked. The engine is separate; three controls have null horn labels and are excluded. [Metric results](AUDIO_ADOPTED_EVENT_LABEL_METRICS.json), [scope fixed before analysis](EVALUATION_SCOPE_FREEZE.md), [case table](AUDIO_ADOPTED_EVENT_COMPARISONS.csv).

The comparison targets adopted event labels using front audio; horn fields generally reference the paired event, without an independently established front-only acoustic member binding. It is not localized window/horn-boundary accuracy or independent-human-GT performance. Max pooling and recording duration affect event alarms. No separate observations, timestamps, labels or inter-rater agreement were invented.

## What fails or remains unavailable

All 10 adopted horn-absent train events trigger the max-window rule; train_events/event_001 is the one adopted horn-present false negative (maximum score 0.2474883). This is an actual event-label failure finding, not concealed by changing the threshold. Detailed source-linked windows are retained in [error review cues](AUDIO_ERROR_REVIEW_WINDOWS.csv). Visual model outputs occur on designated controls (2 front/40 back objects), while 7 train-front and 6 train-back recordings have zero objects; these require matched reference review before declaring frame/box FP/FN. [Failure analysis](FAILURE_CASE_ANALYSIS.md).

Image AP/mAP/box TP-FP-FN/per-class correctness are unavailable because approved annotation content has no source-frame bounding boxes. Audio window correctness is unavailable because there are no actual window labels/horn offsets. Stage2.1/M4/M5/MTR/T1-warning remain unavailable under their existing boundary/clock/reference contracts. [Exact metric dispositions](METRIC_EXECUTION_REGISTER.csv). Nulls are not zero.

The actual 27-event replay admission returns AUTH_DESCRIPTIVE_EVAL_EXEC_NOT_GRANTED. Genuine canonical promotion receipt and canonical protocol-choice/live hash remain absent. Current content approval does not manufacture those records, required fields or independent parents. No guard bypass, synthetic-root real replay or fake canonical record. [Admission receipt](B2_CURRENT_ADMISSION_RECEIPT.json), [multimodal report](MULTIMODAL_EXPERIMENT_REPORT.md).

## Current software results

A fresh complete inherited guarded programme ran 3815 cases/168 modules/53 groups: **3700 passed, 84 failed, 31 errors, 0 skipped**. All 115 nonpassing IDs/outcomes match Mission40 (110 explicit policy exceptions, 5 indirect protected contexts); no new core defect was demonstrated. A separate normal run of 15 existing actual-metadata/integration checks passes 15/15 with original annotations/registry unchanged and normal production guards intact. These are overlapping cases in a different permitted context and are not added to 3815. The full guarded audit remains nonpassing; 100 of its nonpasses have no separate passing current-context result. [Software report](SOFTWARE_TESTING_REPORT.md), [all cases](software_validation/CURRENT_TEST_CASE_OUTCOMES.csv), [115-case triage](software_validation/CURRENT_NONPASSING_TEST_TRIAGE.csv).

No production/test/config/threshold change, retraining, new split, model replacement, raw-media release or external contact occurred. M39's genuine natural-log correction is reused; it is not counted as a new fix. No second identical-code full suite was run because no covered software defect/change justified it.

## Evidence delivery and next research

Nine actual-result figures, underlying tables, actual predictions/PTS/audio ledgers, scoped comparison/error records, complete test evidence, configuration/source identities and original issued/closed operation records are included. [Professor guide](README_FOR_PROFESSOR.md), [methodology](EXPERIMENTAL_METHODOLOGY.md), [reproduction](REPRODUCIBILITY.md), [acceptance](FINAL_ACCEPTANCE_STATUS.json).

Source/input/output integrity checks preserve 1914 prior artifacts (including all 1068 Mission42 files), all 148 original annotation texts, all 462 maintained binding files and all seven researcher paths. New private caches have unique Mission43 names; original caches remain outside staging. No professor package from another project was accessed. Only exact Mission43 files are eligible for local staging/commit; no push, broad staging or history rewrite. Starting HEAD is 8d03ba5e10f2defb71f2a54ddf46955a29e7185e; ending hash is the containing local commit, checked/reported after commit.

All genuinely executable original inferences, input assembly, scoped adopted-label evaluation and current relevant checks are complete. The whole research programme remains **partially complete** because boxed/window/canonical-reference-dependent endpoints and actual B2 decisions are missing. Further work should target those exact missing inputs/operative bindings, not repeat the completed 27-source inference or the researcher's/classmate's old five-event review. Independent-camera primary, supporting audio, exploratory fusion, M4/M5/MTR roles, metric-specific denominators, optional exact-eleven R04/event_010 exclusion and deferred physical T2/occupancy/RD046/comparator remain unchanged. No safety improvement, deployment readiness, generalization, p-value or confidence interval is claimed.
