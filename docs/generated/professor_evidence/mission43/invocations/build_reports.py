"""Professor-facing reports from actual full-cohort evidence; never fabricates missing results."""
from common import *
import csv,shutil,collections,xml.etree.ElementTree as ET
r=read(D/'ACTUAL_FULL_COHORT_RESULTS.json');b=read(D/'BASELINE_AND_PRESERVATION.json');m=read(D/'AUDIO_ADOPTED_EVENT_LABEL_METRICS.json');counts=m['confusion_matrix'];rates=m['rates'];v=read(D/'ACTUAL_VISUAL_RUN_MANIFEST.json');a=read(D/'ACTUAL_AUDIO_RUN_MANIFEST.json');tests=read(D/'software_validation/CURRENT_VALIDATION_SUMMARY.json')
def load(n):return list(csv.DictReader((D/n).open()))
def text(n,s):(D/n).write_text(s.strip()+'\n')
def pct(k):return f'{100*rates[k]:.2f}%'if rates[k]is not None else'Unavailable'
# Focused immutable inputs and reused evidence: no raw recordings, weights or private caches.
copies={}
def copy(source,group):
 source=str(source);p=R/source;target=D/group/source;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);assert sha(p)==sha(target);copies[source]={'package_path':str(target.relative_to(D)),'sha256':sha(p),'kind':'COPIED_ORIGINAL'}
for e in INV.values():copy(e['active_proposal_file'],'adopted_annotation_originals')
for e in v['events']:
 if e['status']=='REUSED_MISSION39_ACTUAL_INFERENCE':copy(e['predictions']['path'],'reused_evidence')
for e in a['events']:
 if e['status']=='REUSED_MISSION39_CORRECTED_AUDIO':
  for key in ['predictions','descriptive_cache_rows','clock_ledger','B2_input_assembly']:copy(e[key]['path'],'reused_evidence')
for p in ['docs/PHASE11_3_REVIEW_INVENTORY.json','data/manifests/real_world_v2_video_manifest.json','data/manifests/layer_b_v2_annotation_inventory.json','data/ground_truth/reviews/_INTEGRITY_NOTICE.md','docs/generated/master_reaudit/MISSION_27_GENUINE_REVIEW_PILOT_PROTOCOL.md','docs/generated/master_reaudit/MISSION_27_HUMAN_REVIEWER_HANDBOOK.md','docs/generated/master_reaudit/mission38/HUMAN_REFERENCE_SESSION_STATUS.md','docs/generated/master_reaudit/mission37/CHECKPOINT_VERIFICATION_RECEIPT.json','docs/generated/research_results/mission39/ACTUAL_RUN_MANIFEST.json','docs/generated/research_results/mission39/ACTUAL_BACK_RUN_MANIFEST.json','docs/generated/research_results/mission39/audio_followup/CORRECTED_AUDIO_RUN_MANIFEST.json','docs/generated/research_results/mission39/audio_followup/TRAINING_RUNTIME_FEATURE_CORRECTION.json','docs/generated/research_results/mission39/audio_followup/legacy_db_diagnostic/README.md']:
 copy(p,'historical_inputs')
for p in ['configs/frozen_experiment_v1.yaml','configs/decision_policy_v1.yaml','pyproject.toml','requirements.lock','src/railway_detection/experiments/frozen_config.py','src/railway_detection/experiments/layer_b_processor.py','src/railway_detection/experiments/cache_provenance.py','src/railway_detection/vision/video.py','src/railway_detection/audio/model.py','src/railway_detection/audio/features.py','src/railway_detection/audio/pipeline.py','src/railway_detection/audio/evaluation.py','src/railway_detection/fusion/collector.py','src/railway_detection/evaluation/cache_only_engine.py','src/railway_detection/evaluation/descriptive_exec_gate.py','src/railway_detection/evaluation/ground_truth_loader.py','src/railway_detection/safety/media_guard.py','src/railway_detection/annotation/stage2_1_schema.py','scripts/train_audio_model_v3_esc50.py']:
 copy(p,'source_snapshot')
save(D/'COPIED_EVIDENCE_SOURCE_MAP.json',copies)
# Working links to packaged originals; historical originals themselves retain original links/bytes.
def link(source,label=None):return '['+(label or Path(source).name)+']('+copies[source]['package_path']+')'
visual=load('VISUAL_PER_EVENT_RESULTS.csv');audio=load('AUDIO_PER_EVENT_RESULTS.csv');inp=load('B2_INPUT_COVERAGE.csv');errors=load('FAILURE_REVIEW_CANDIDATES.csv');erroraudio=load('AUDIO_ERROR_REVIEW_WINDOWS.csv');initial=sum(int(e['initial_no_audio_record_frames'])for e in inp);later=sum(int(e['later_no_audio_record_frames'])for e in inp)
zero={role:[e['event']for e in visual if e['camera']==role and e['cohort']=='train_events'and int(e['predicted_objects'])==0]for role in ['front','back']}
controls={role:sum(int(e['predicted_objects'])for e in visual if e['camera']==role and e['cohort']=='no_train_events')for role in ['front','back']}
main=f'''# Mission43 actual full-cohort findings

Prepared2026-11-08, America/New_York. **FULL27_ORIGINAL_INFERENCE_AND_INPUT_ASSEMBLY_COMPLETE; ADOPTED_REFERENCE_AUDIO_EVENT_COMPARISON_EXECUTED; B2_DECISION_REPLAY_BLOCKED; CANONICAL_GT_NOT_ESTABLISHED.** This mission executed original data rather than stopping at a plan. It does not claim completion of unsupported endpoints or a fully passing test suite.

| Existing direction | Prior five-event evidence reused | New original execution | Full27-event result |
|---|---|---|---|
| B0_front | 5 sources;1079 records;13 objects | 22 sources;{r['visual']['front']['sampled_records']-1079} records;{r['visual']['front']['predicted_objects']-13} objects | 27 sources;{r['visual']['front']['sampled_records']} records;{r['visual']['front']['predicted_objects']} objects |
| B0_back | 5 sources;1100 records;276 objects | 22 sources;{r['visual']['back']['sampled_records']-1100} records;{r['visual']['back']['predicted_objects']-276} objects | 27 sources;{r['visual']['back']['sampled_records']} records;{r['visual']['back']['predicted_objects']} objects |
| B1 front embedded audio | 5 sources;423 windows;120 positive | 22 sources;{r['audio_windows']-423} windows;{r['audio_model_positive_windows']-120} positive | 27 sources;{r['audio_windows']} windows;{r['audio_model_positive_windows']} positive |
| B2 input assembly | 5 events;1079 frames;634 paired | 22 events;{r['B2_input_frames']-1079} frames;{r['B2_both_record_frames']-634} paired | 27 events;{r['B2_input_frames']} frames;{r['B2_both_record_frames']} paired |
| B2 decision replay | Not executed | Not admitted | 0 decision events/frames |

All54 exact source digests match the established inventory; all54 have one video and one audio stream. Counts represent the same27 physical events (23 train,3 no-train,1 engine), not54 independent events. Two historical duplicate camera references remain excluded; no active event was dropped. All44 new camera and22 new acoustic inferences completed without errors. [27-event coverage](FULL_27_EVENT_COVERAGE_MATRIX.csv), [actual run summary](ACTUAL_FULL_COHORT_RESULTS.json).

## Actual reference adoption and evaluation

The researcher explicitly confirmed manual verification and approved the AI-assisted annotations as final, with no separate manual observations stored. [The genuine adoption receipt](RESEARCHER_ANNOTATION_ADOPTION.json) binds all27 existing active versions/hashes. This is a positive new approval, not dismissed as no evidence. Original annotations remain unchanged; copied originals are included. The content is now a **researcher-adopted AI-assisted reference**, not independent stored human observations or automatic Stage2.1 promotion.

The existing V3 recording rule (maximum window score, frozen0.37 threshold) supports a specifically documented exploratory comparison to explicit event horn labels. Among23 train events (13 horn-present,10 absent_observed), actual counts are **TP={counts['tp']},FP={counts['fp']},FN={counts['fn']},TN={counts['tn']}**. Precision={pct('precision')},recall={pct('recall')},F1={rates['f1_score']:.4f},specificity={pct('specificity')},accuracy={pct('accuracy')},ROC-AUC={rates['auc_roc']:.4f},AP={rates['pr_auc']:.4f}. Exact counts/ranking metrics were independently cross-checked. The engine is separate; three controls have null horn labels and are excluded. [Metric results](AUDIO_ADOPTED_EVENT_LABEL_METRICS.json), [scope fixed before analysis](EVALUATION_SCOPE_FREEZE.md), [case table](AUDIO_ADOPTED_EVENT_COMPARISONS.csv).

The comparison targets adopted event labels using front audio; horn fields generally reference the paired event, without an independently established front-only acoustic member binding. It is not localized window/horn-boundary accuracy or independent-human-GT performance. Max pooling and recording duration affect event alarms. No separate observations, timestamps, labels or inter-rater agreement were invented.

## What fails or remains unavailable

All10 adopted horn-absent train events trigger the max-window rule; train_events/event_001 is the one adopted horn-present false negative (maximum score0.2474883). This is an actual event-label failure finding, not concealed by changing the threshold. Detailed source-linked windows are retained in [error review cues](AUDIO_ERROR_REVIEW_WINDOWS.csv). Visual model outputs occur on designated controls ({controls['front']} front/{controls['back']} back objects), while {len(zero['front'])} train-front and {len(zero['back'])} train-back recordings have zero objects; these require matched reference review before declaring frame/box FP/FN. [Failure analysis](FAILURE_CASE_ANALYSIS.md).

Image AP/mAP/box TP-FP-FN/per-class correctness are unavailable because approved annotation content has no source-frame bounding boxes. Audio window correctness is unavailable because there are no actual window labels/horn offsets. Stage2.1/M4/M5/MTR/T1-warning remain unavailable under their existing boundary/clock/reference contracts. [Exact metric dispositions](METRIC_EXECUTION_REGISTER.csv). Nulls are not zero.

The actual27-event replay admission returns AUTH_DESCRIPTIVE_EVAL_EXEC_NOT_GRANTED. Genuine canonical promotion receipt and canonical protocol-choice/live hash remain absent. Current content approval does not manufacture those records, required fields or independent parents. No guard bypass, synthetic-root real replay or fake canonical record. [Admission receipt](B2_CURRENT_ADMISSION_RECEIPT.json), [multimodal report](MULTIMODAL_EXPERIMENT_REPORT.md).

## Current software results

A fresh complete inherited guarded programme ran3815 cases/168 modules/53groups: **3700 passed,84 failed,31 errors,0 skipped**. All115 nonpassing IDs/outcomes match Mission40 (110 explicit policy exceptions,5 indirect protected contexts); no new core defect was demonstrated. A separate normal run of15 existing actual-metadata/integration checks passes15/15 with original annotations/registry unchanged and normal production guards intact. These are overlapping cases in a different permitted context and are not added to3815. The full guarded audit remains nonpassing;100 of its nonpasses have no separate passing current-context result. [Software report](SOFTWARE_TESTING_REPORT.md), [all cases](software_validation/CURRENT_TEST_CASE_OUTCOMES.csv), [115-case triage](software_validation/CURRENT_NONPASSING_TEST_TRIAGE.csv).

No production/test/config/threshold change, retraining, new split, model replacement, raw-media release or external contact occurred. M39's genuine natural-log correction is reused; it is not counted as a new fix. No second identical-code full suite was run because no covered software defect/change justified it.

## Evidence delivery and next research

Nine actual-result figures, underlying tables, actual predictions/PTS/audio ledgers, scoped comparison/error records, complete test evidence, configuration/source identities and original issued/closed operation records are included. [Professor guide](README_FOR_PROFESSOR.md), [methodology](EXPERIMENTAL_METHODOLOGY.md), [reproduction](REPRODUCIBILITY.md), [acceptance](FINAL_ACCEPTANCE_STATUS.json).

Source/input/output integrity checks preserve1914 prior artifacts (including all1068 Mission42 files), all148 original annotation texts, all462 maintained binding files and all seven researcher paths. New private caches have unique Mission43 names; original caches remain outside staging. No professor package from another project was accessed. Only exact Mission43 files are eligible for local staging/commit; no push, broad staging or history rewrite. Starting HEAD is{b['starting_commit']}; ending hash is the containing local commit, checked/reported after commit.

All genuinely executable original inferences, input assembly, scoped adopted-label evaluation and current relevant checks are complete. The whole research programme remains **partially complete** because boxed/window/canonical-reference-dependent endpoints and actual B2 decisions are missing. Further work should target those exact missing inputs/operative bindings, not repeat the completed27-source inference or the researcher's/classmate's old five-event review. Independent-camera primary, supporting audio, exploratory fusion, M4/M5/MTR roles, metric-specific denominators, optional exact-elevenR04/event_010 exclusion and deferred physicalT2/occupancy/RD046/comparator remain unchanged. No safety improvement, deployment readiness, generalization, p-value or confidence interval is claimed.
'''
# Make current prose readable without touching the actual evidence bytes.
def polish(x):
 for old,new in [('Prepared2026','Prepared 2026'),('FULL27','FULL27'),('All54','All 54'),('all54','all 54'),('same27','same 27'),('27-event result','27-event result'),('all27','all 27'),('all44','all 44'),('All44','All 44'),('All10','All 10'),('23 train,3','23 train, 3'),('no-train,1','no-train, 1'),('among23','among 23'),('Among23','Among 23'),('(13 horn-present,10','(13 horn-present, 10'),('threshold0.37','threshold 0.37'),('frozen0.37','frozen 0.37'),('score0.247','score 0.247'),('ran3815','ran 3815'),('/53groups','/53 groups'),('checks passes15','checks passes 15'),('run of15','run of 15'),('All115','All 115'),('(110 explicit policy exceptions,5','(110 explicit policy exceptions, 5'),('to3815','to 3815'),(';100','; 100'),('preserve1914','preserve 1914'),('all1068','all 1068'),('all148','all 148'),('all462','all 462'),('is'+b['starting_commit'],'is '+b['starting_commit']),('physicalT2','physical T2'),('exact-elevenR04','exact-eleven R04')]:x=x.replace(old,new)
 return x
text('MISSION_43_FINAL_REPORT.md',polish(main))
text('README_FOR_PROFESSOR.md',f'''# Professor guide — full27-event execution

Start with [the final findings](MISSION_43_FINAL_REPORT.md), then [the exact27-event coverage](FULL_27_EVENT_COVERAGE_MATRIX.csv), [annotation/reference verification](ANNOTATION_AND_REFERENCE_VERIFICATION.md) and [quantitative metrics](QUANTITATIVE_METRICS_AND_SCOPE.md).

Original inference now covers27 front recordings,27 back recordings and27 front embedded acoustic tracks. The previous five-event inference is reused, not repeated. Actual totals:6613 front records/329 objects;6479 back records/1020 objects;2600 audio windows/445 positive at0.37;6614 B2 input frames/3897 with both records. No B2 decisions.

Your researcher's approval is preserved as adoption of all27 active AI-assisted annotation contents. It enabled a limited exploratory event-label audio comparison:TP12/FP10/FN1/TN0 among23 train events with explicit horn labels. Engine separate; controls' null horn labels excluded. This reveals poor specificity relative to those labels. It is not a frame/window or independent-human-GT accuracy finding.

Read [image findings](IMAGE_MODEL_EXPERIMENT_REPORT.md), [audio findings](AUDIO_MODEL_EXPERIMENT_REPORT.md), [multimodal status](MULTIMODAL_EXPERIMENT_REPORT.md), [failure review](FAILURE_CASE_ANALYSIS.md), [software outcomes](SOFTWARE_TESTING_REPORT.md), [limitations/next work](LIMITATIONS_AND_NEXT_RESEARCH.md) and [reproducibility](REPRODUCIBILITY.md). All nine figures are listed with their actual data inputs in [figure provenance](FIGURE_PROVENANCE.json); no manuscript is prepared.

The package contains original-derived predictions/clock metadata and copied annotation/text evidence, not raw media, PCM, checkpoint binaries, credentials or private caches. Historical inputs keep original filenames/bytes and may contain historical links; their source mapping is explicit. The current reports control current status. No material was sent to anyone.

From this folder run `python3 verify_package.py` for package-local integrity verification. Do not execute old inference scripts as if their past operation grants remain live. Exact grants used here were closed; B2 promotion/protocol bindings remain absent. [Acceptance criteria](FINAL_ACCEPTANCE_STATUS.json) distinguish complete execution from unavailable evaluations.
''')
text('EXPERIMENTAL_METHODOLOGY.md',f'''# Existing methods and precise evaluation scope

The active cohort is23 train/3 no-train/1 engine, paired front/back camera members,54 unique verified container hashes; two historical duplicate references remain excluded. This is a single-site selected cohort, not an official new train/test split. Physical event is the independent interpretation unit. Front/back counts are separate observations, never doubled event N.

[Actual visual manifest](ACTUAL_VISUAL_RUN_MANIFEST.json) binds the frozen YOLOv8n checkpoint{v['checkpoint_sha256']} and canonical config{v['canonical_config_sha256']}, actual package versions, code revision, invocation hash, CPU/seed42, exact stream selection,5FPS sampling,640x640 square letterbox/confidence0.35 and native PTS. The54 actual camera outputs reuse ten prior results and execute44 new sources. No detector, threshold or preprocessing was selected from outcomes.

[Actual audio manifest](ACTUAL_AUDIO_RUN_MANIFEST.json) binds checkpoint{a['model_sha256']}, corrected log(mel_energy+1e-10),fixed normalization,16kmono,1s/0.5s windows,FFT512/hop256/mel64/80–8000Hz,CPU/seed42 and threshold0.37. Only the existing front-embedded B1 condition is run across27 events; the54 available embedded tracks do not automatically create an unadopted back-audio condition. The87 standalone development recordings are not evaluation inputs. No raw PCM file is retained.

B2 input assembly reuses the existing causal collector/window0.25s, its source-based temporal grid and frozen timing configuration. It has no decision replay/accepted-reference result. Actual native video fields and causal integer-sample acoustic times are preserved; no physical cross-camera sync, GT shift or duration padding is inferred. Absolute frame/stream identities are explicit. Cadence display groups floating intervals to12 decimal places only; all original rational PTS remain unrounded in source outputs and integrity checks.

The narrowly defined [evaluation scope](EVALUATION_SCOPE_FREEZE.md) was documented before new full-cohort audio result analysis, using the existing V3 recording max-window rule against explicit researcher-adopted event horn_status. It is exploratory because source-local horn binding/independent manual records are absent and five prior outputs were known. No new vision IoU/event aggregation, temporal tolerance, operating threshold, bootstrap or inferential procedure was invented. Box/window/canonical-timing endpoints remain unavailable.

Existing protocol and active schema are copied for inspection: {link('docs/generated/master_reaudit/MISSION_27_GENUINE_REVIEW_PILOT_PROTOCOL.md')}, {link('src/railway_detection/annotation/stage2_1_schema.py')}. PhysicalT2/occupancy/RD046/comparator remain deferred/inactive; R04 remains optional exact11 and excludes event_010 only within R04.
''')
text('ANNOTATION_AND_REFERENCE_VERIFICATION.md',f'''# Annotation content, adoption and technical eligibility

The initial Mission43 brief newly reports that all27 dataset annotations were manually verified. The follow-up explicitly says the researcher verified/approved all AI annotation content as final and did not retain separate manual records. [Verbatim adoption record](RESEARCHER_ANNOTATION_ADOPTION.json) records that genuine decision with exact current active versions/hashes from the maintained inventory. All27 active proposals' paired source hashes match the inventory and the54 freshly verified original files. [Per-event status](ANNOTATION_COVERAGE_MATRIX.csv), [actual inspected fields/versions](ANNOTATION_RECORD_INSPECTION.json), [adopted scalar fields](ADOPTED_REFERENCE_FIELDS.csv).

These are **researcher-adopted AI-assisted references**. No independent researcher/classmate observation file, date, timestamp, signature, qualification or missing label is invented. The earlier five-front separate review/exact agreement remains researcher-reported; classmate partial familiarity remains preserved. No classmate review of the remaining22 events or human inter-rater statistic is inferred, and no repeat pass is requested.

The27 old schema6 review bodies retain their sibling INVALIDATED notices unchanged. User adoption of active proposal content does not revive different superseded legacy values. Current active schemas are26 proposal7.0.0 and one8.0.0; there are no accepted8.1 Stage2.1 records or genuine promotion receipt. Formal canonical timing/GT acceptance is separate from actual content approval; the latter is positively retained, not rejected.

The active files contain event metadata, horn status/onset and boundary candidates, not frame-box or acoustic window labels. Horn labels are13 present/11 absent_observed/3 null; pooled comparison uses23 train events (13/10), engine absent separately, controls null excluded. Do not turn no-train into no-horn. Most horn fields identify the paired event rather than one independently verified acoustic camera member, limiting interpretation to explicit exploratory event-label agreement.

[Sampled frame linkage](ANNOTATION_SAMPLED_FRAME_LINKAGE.csv) checks exact referenced frames where actually present among model samples; absent exact samples are not interpolated or assigned invented tolerances. Values/frame-index/FPS correspondence and source hashes are not by themselves canonical clock/state validation. PhysicalT2 and censoring/uncertainty states remain governed by their existing contracts. No fake8.1 conversion, parent record or promotion is created. All148 original annotation text fingerprints remain unchanged.

[Copied active originals](COPIED_EVIDENCE_SOURCE_MAP.json) retain filename/content with a clear original-source hash. Historical AI text may still say candidate/awaiting review; the new additive approval record supplies current adoption context without rewriting that history.
''')
text('IMAGE_MODEL_EXPERIMENT_REPORT.md',f'''# Full-cohort image inference

All27 fronts and27 backs completed at the frozen model/configuration. New original executions:22 fronts+22 backs; reused unchanged prior outputs:5 each. Zero inference errors. Actual records:front{r['visual']['front']['sampled_records']}/back{r['visual']['back']['sampled_records']}; predicted objects:front{r['visual']['front']['predicted_objects']}/back{r['visual']['back']['predicted_objects']}. Independent clocks/stream indices and rational PTS are retained.

[Per-event outputs](VISUAL_PER_EVENT_RESULTS.csv), [per-class prediction counts/confidence](VISUAL_PER_CLASS_PREDICTIONS.csv), [all confidence values/boxes](VISUAL_CONFIDENCE_VALUES.csv), [sampled-output runs](VISUAL_OUTPUT_RUNS.csv), [native sampling intervals](VISUAL_NATIVE_SAMPLE_CADENCE.csv), [actual manifest](ACTUAL_VISUAL_RUN_MANIFEST.json).

There are{len(zero['front'])} train-front recordings and{len(zero['back'])} train-back recordings with zero model objects. Designated controls produce{controls['front']} front/{controls['back']} back objects. These are concrete detection-coverage/false-output review candidates, not matched-box FN/FP rates. Literal front/rear/side labels are maintained and do not establish a valid back-clearance mapping. Larger back counts do not prove better performance.

Researcher-approved event/boundary annotations do not supply spatial boxes or exact class/instance matching. Image TP/FP/FN,precision/recall/F1,AP/mAP50/mAP50:95 and per-class correctness therefore remain unavailable. No new IoU rule or inference threshold is introduced to force a number. Lighting/weather strata in [condition output table](OUTPUTS_BY_ADOPTED_CONDITION.csv) are adopted annotation context only, not measured difficult-condition accuracy. No scene or physical visibility condition is invented.

![Objects by event](figures/VISUAL_OBJECTS_PER_EVENT.png)

![Object confidence distribution](figures/VISUAL_CONFIDENCE_DISTRIBUTION.png)

Processing times/rates are actual per-member pipeline measurements, combining prior and new runs under their recorded conditions. They are not native video FPS, a matched hardware benchmark, real-time acceptance or a safety claim.
''')
text('AUDIO_MODEL_EXPERIMENT_REPORT.md',f'''# Full-cohort corrected acoustic findings

All27 front embedded tracks completed with22 new original inferences and5 byte-bound prior corrected runs, zero failures. Actual windows={r['audio_windows']}; model scores≥0.37={r['audio_model_positive_windows']}. Overlapping windows are not independent physical events, horn counts or correctness probabilities. The corrected natural-log feature transform is preserved; the old five-event dB423/80 diagnostics remain superseded and excluded from these totals. No standalone development recordings entered this run.

[Per-event table](AUDIO_PER_EVENT_RESULTS.csv), [actual manifest](ACTUAL_AUDIO_RUN_MANIFEST.json), [model-label runs](AUDIO_MODEL_LABEL_RUNS.csv), [event comparison inputs](AUDIO_ADOPTED_EVENT_COMPARISONS.csv), [complete metrics](AUDIO_ADOPTED_EVENT_LABEL_METRICS.json).

| Adopted event-label endpoint | Actual value / denominator |
|---|---|
| Eligible physical train events | 23:13 horn-present,10 absent_observed |
| TP/FP/FN/TN | {counts['tp']}/{counts['fp']}/{counts['fn']}/{counts['tn']} |
| Precision | {counts['tp']}/({counts['tp']}+{counts['fp']})={pct('precision')} |
| Recall | {counts['tp']}/13={pct('recall')} |
| Specificity | {counts['tn']}/10={pct('specificity')} |
| F1 | {rates['f1_score']:.4f} |
| Accuracy | {pct('accuracy')} |
| ROC-AUC / AP | {rates['auc_roc']:.4f}/{rates['pr_auc']:.4f} |

The method is existing recording max-window pooling at0.37, fixed before new audio-result inspection. Against the adopted labels, all10 absent-observed train cases trigger and event_001 is missed. This is a limited event-label comparison using front audio. Reference horn fields do not independently bind one camera's acoustic truth, annotations are AI-assisted and no separate manual records exist; therefore it is not independent/localized human-GT performance. The engine's absent label matches its negative prediction, reported separately without single-case ROC/PR. Controls have null horn labels and are excluded, never relabeled.

Unwindowed tails and actual native sample/PTS ledgers remain explicit. There is no fabricated horn offset, window label, timestamp shift, padding, calibrated score, hourly false-alarm rate or threshold tuning. Whole-event agreement does not establish horn timing or per-window TP/FP/FN. [Scope and limitations](EVALUATION_SCOPE_FREEZE.md), [independent metric cross-check](METRIC_CALCULATION_CROSSCHECK.json).

![Adopted-label confusion](figures/AUDIO_ADOPTED_EVENT_CONFUSION.png)

![Scores](figures/AUDIO_MAX_SCORES_BY_EVENT.png)

![ROC](figures/AUDIO_ADOPTED_EVENT_ROC.png)

![PR](figures/AUDIO_ADOPTED_EVENT_PR.png)
''')
text('MULTIMODAL_EXPERIMENT_REPORT.md',f'''# Full-cohort input assembly; decision replay remains blocked

All27 front/audio input assemblies are available:6614 query frames,3897 with both stream records and2717 without an audio record inside the existing input window. Initial missing-record frames={initial};later={later}. Missing input is not a negative acoustic prediction or proof the source is absent. No interpolation/fill/padding or scientific tolerance was added. Input window0.25s differs from the replay collector0.5s; input missingness does not establish decision-stage missingness.

Front inference has6613 records, while assembly has6614 query frames. The one extra query is train_events/event_010:120 sampled visual records,121 queries. Last actual visual PTS=23.8166666667s;last causal audio end=24.0s. The existing collector runs to their maximum and its nominal24.0s query retains the real preceding visual record within its existing window. This is not an additional model/decoded frame or invented duration. [Exact reconciliation](INPUT_GRID_RECONCILIATION.json), [per-event coverage](B2_INPUT_COVERAGE.csv), [actual input manifest](B2_EVALUATION_INPUT_MANIFEST.json).

The real-root CacheOnlyReplayEngine.execute_replay boundary returned AUTH_DESCRIPTIVE_EVAL_EXEC_NOT_GRANTED before decision processing. Zero decision events/frames, no B2 decision result or placeholder. The current full27 scope requires its exact actual manifest plus existing fixed metric set/model/config, genuine Stage2.1 promotion receipt and live canonical protocol hash. data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json,data/governance/stage21_promotion_receipt.json and data/manifests/phase12_protocol_decision.json remain absent in the inspection. [Actual refusal](B2_CURRENT_ADMISSION_RECEIPT.json), [binding status](CURRENT_EVALUATION_BINDING_STATUS.json).

Researcher adoption of candidate content does not create those canonical fields/parents/receipts. M4 first_blocked_to_t4_clearance is retained, not reopened; a candidate profile is not a live operative record. The algorithm can compute states without human GT conceptually, but this governed operation remains promotion-bound/fixed-scope. No bypass or alternate synthetic-root replay occurred. No fusion superiority, B2 accuracy, safe gate behavior or hardware actuation is inferred.

![Actual input coverage](figures/B2_INPUT_RECORD_COVERAGE.png)
''')
text('QUANTITATIVE_METRICS_AND_SCOPE.md',f'''# Quantitative endpoints and unavailable values

The executed reference comparison is exploratory max-window audio output versus researcher-adopted event horn labels, N=23 train events, engine separate, null controls excluded. Confusion={counts};precision={pct('precision')};recall={pct('recall')};specificity={pct('specificity')};F1={rates['f1_score']:.4f};ROC-AUC={rates['auc_roc']:.4f};AP={rates['pr_auc']:.4f}. [Raw metric payload](AUDIO_ADOPTED_EVENT_LABEL_METRICS.json), [independent exact-count/ranking check](METRIC_CALCULATION_CROSSCHECK.json), [curve input/data](AUDIO_EVENT_CURVE_DATA.json).

This denominator is neither27 universally nor2600 windows. Two-class metrics are not calculated for the single engine or unknown-control labels. Max-window scores are ranking values, not calibrated event correctness probabilities. No calibration claim, significance, confidence interval, bootstrap or threshold choice is introduced. Rates are serialized to4 decimals by the existing metric API; exact counts and full inputs are retained.

Raw model descriptors include per-event/class objects/confidences, no-detection samples, native sampled cadence, acoustic windows/positive counts and input presence. All are valid at their declared observational unit. They do not imply independent frame/window sample size or false-positive correctness.

[Metric execution register](METRIC_EXECUTION_REGISTER.csv) gives exact remaining dependencies: image frame boxes/class-instance labels and matching coverage are absent; audio window labels/offsets are absent; control horn labels are null; human separate observation records were not stored; canonical timing/clock/state/promotion and actual guarded replay are absent. Thus image mAP/AP/box correctness, acoustic window metrics, human agreement and M4/M5/MTR/T1-warning stay null, not zero. The candidate-derived adopted event comparison is not secretly promoted to independent canonical GT.
''')
text('FAILURE_CASE_ANALYSIS.md',f'''# What fails and what requires review

The fixed acoustic recording rule returns positive on all10 adopted horn-absent train events. It misses train_events/event_001 despite its adopted horn-present label (maximum score0.24748830497 below0.37). No threshold/preprocessing was changed in response. [Eleven exact event-label mismatches](AUDIO_ERROR_REVIEW_WINDOWS.csv) include maximum-score window start/end/native fractions, first positive window where present, positive-window count and source/prediction/annotation hashes. These are actual review cues, not invented localized false-window labels.

The event target is horn status, not train presence: a train event can legitimately carry an absent horn label. Max pooling can trigger an entire recording from a small number of background responses; differing recording lengths/window counts limit comparison. The controls' approved text mentions road traffic context, but their horn_status is null and is not converted to train-horn truth. Background-noise causes are not asserted without source-specific acoustic reference. Original model-score traces/window outputs remain available for qualified investigation.

Visual coverage concerns: {len(zero['front'])} train-front and{len(zero['back'])} train-back recordings have zero predicted objects. Designated no-train recordings produce{controls['front']} front/{controls['back']} back objects. Exact event/camera/output evidence is in [failure candidates](FAILURE_REVIEW_CANDIDATES.csv); its{len(errors)} rows may concern the same physical event more than once and are not an independent error sample. Missing boxes prevent matched detection FN/FP, duplication and class-confusion assertions. Output runs/confidence and adopted lighting/weather context are retained without inventing difficult-condition accuracy or explaining a false detection by guessed visibility.

There were no failed original input/model invocations across54 camera and27 acoustic members. That execution success is not prediction success. The actual audio-label failures, visual review candidates and software nonpassing results remain in the package. No favorable case exclusion, synthetic replacement observation, new operating threshold or hidden rerun occurred.
''')
text('SOFTWARE_TESTING_REPORT.md',f'''# Current complete software execution and follow-up

A fresh complete inherited guarded programme executed3815 unique cases in168 modules/53groups. Actual initial/final unchanged-code result:3700 passed,84 failed,31 errors,0 skipped. All115 failure/error IDs and outcomes are exactly the Mission40 set;110 are explicit MISSION22_POLICY exceptions and5 indirect protected-data/readiness contexts. Source/config/test bindings remain identical to the tested closure. This is current Mission43 execution, not reuse of historical counts.

[Full receipt](software_validation/FULL_RUN_RECEIPT.json), [wall time](software_validation/FULL_RUN_WALL_TIME.json), [3815 outcomes](software_validation/CURRENT_TEST_CASE_OUTCOMES.csv), [115-case investigation](software_validation/CURRENT_NONPASSING_TEST_TRIAGE.csv), [summary](software_validation/CURRENT_VALIDATION_SUMMARY.json). All completed group JUnit/stdout/stderr/collection/policy files are retained compressed. The audit includes unit/integration/regression, dataset/annotation, inference/preprocessing, PTS/cache/replay/reproducibility and metric-contract test families. A protected dependency denial does not prove the physical input is absent or the scientific result is wrong.

Fifteen existing previously denied checks were inspected and separately run with normal pytest against actual user-authorized inventory/review metadata:15 passed,0 failures/errors/skips. These include real27-event queue, allowlist, seven inventory checks and five read-only corpus/preflight/adversarial-copy checks. Production media/evaluation guards and source tests stay unchanged; registry isolation remains active; original annotation text/registry hashes are unchanged. [Actual integration receipt](software_validation/READ_ONLY_DATA_INTEGRATION_RECEIPT.json), [JUnit](software_validation/READ_ONLY_DATA_INTEGRATION.xml). This is a different allowed context, not a changed resource-free classification or a new pass for the full profile. The15 overlapping cases are not added to3815. The guarded audit retains115 nonpasses;100 have no separately passing current context.

No new material production defect was demonstrated, so no production/test/config change, disabled assertion, deleted case or second identical-code full suite was commissioned. Historical M39 natural-log parity and M40 fixture fixes are preserved rather than counted anew. Remaining dependencies include production checkpoint/features/corpus/live readiness, historical V2 directions and optional synchronization contexts; they do not become mandatory new27-event experiments. Relevant actual source/inference/clock/output integrity is additionally checked on the genuine27-event outputs in [actual-data integrity](ACTUAL_OUTPUT_INTEGRITY_VALIDATION.json) and [metric cross-check](METRIC_CALCULATION_CROSSCHECK.json).

The full repository is not certified passing. Resource-free Python guards are not OS isolation, and synthetic/adversarial checks are not original-data model accuracy. All initial failures remain disclosed.
''')
text('REPRODUCIBILITY.md',f'''# Reproduction and operation boundaries

Starting Git HEAD:{b['starting_commit']}; tracking origin/main:{b['tracking']}. No push. Actual visual/audio manifests record real run IDs, start/end times, invocation SHA, model/config identities, environment versions, original-source/annotation hashes, logs and per-event outcomes. Because the new invocation files were not yet committed at run time, their exact file hashes supplement the baseline Git revision; the containing final commit anchors their delivered bytes.

Executed entrypoints (from repository root, using the existing environment):

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. .venv/bin/python docs/generated/professor_evidence/mission43/invocations/run_full_validation.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/reconcile_annotations.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/record_researcher_adoption.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/verify_sources.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/run_vision.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/run_metadata_integration.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/run_audio.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/analyze_results.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/validate_actual_outputs.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/crosscheck_metrics.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/plot_results.py
```

Exact pytest/ffprobe/ffmpeg commands are recorded in their execution receipts/manifests; full inference/analysis stdout/stderr is retained in logs/. Source snapshots/configs/dependency references are included with byte-identical identities in COPIED_EVIDENCE_SOURCE_MAP.json. New output filenames are immutable on reuse; old predictions are hash-checked and reused instead of repeated. Plot layout was refined after visual inspection without rerunning inference or changing numerical inputs.

The actual Mission43 request authorizes the expanded ordinary inference work; previously confirmed authority identity is retained. Each original-operation phase uses the existing real-root AUTH-MEDIA-ACCESS schema, exact27 event IDs/54 paths, actual current issue/expiry/scope hash and unsigned recorded-statement provenance. Issued/closed records are retained in operations/; the canonical raw-media slot is returned to absence. No allowlist or guard change, fake GT promotion, temporary-root real replay or expired grant reuse. B2 remains separately blocked.

These are recorded commands, not authority to re-run now: the transcribed phase scopes were closed and scripts may issue their run-scoped records when intentionally executed. Reproduction requires the actual researcher direction, exact original/model assets, compatible packages and current relevant operation authority; do not treat a copied historical approval or edited JSON as new permission. Ordinary verification of this evidence uses `python3 verify_package.py` **from this package folder** and reads package files only.

Raw videos/audio/PCM, checkpoint binaries, private runtime caches, credentials and absent manual notes are not included. Reused evidence and adopted originals are copied byte-for-byte; original repository references remain documentary pointers. Package verification resolves those references to included copies through the source map, so it does not open raw assets. Source clock stability is not physical camera identity or synchronization. Timings vary by host/load and are not deployment profiling.
''')
text('LIMITATIONS_AND_NEXT_RESEARCH.md',f'''# Remaining research and claim boundaries

All existing eligible27-event front/back vision, front embedded acoustic inference and input assembly are now complete. Do not repeat them to fill missing metrics. The researcher-adopted AI-assisted annotation content is retained as final content at its real stated scope, and its limited23-event horn-label comparison is computed. Independent human provenance, camera-local acoustic binding and canonical timing/promotion remain separate, not fabricated.

For image mAP/instance correctness, actual source-frame boxes/class labels and supported matching coverage are missing. For acoustic window/timing correctness, actual source-local labels/offsets/coverage are missing. Those are different annotation capabilities from the completed event/boundary verification; no repeat five-event review or reconstruction of absent notes is requested. Whether to supply those missing annotation types or limit paper claims is an explicit next research decision.

For B2/M4/M5/MTR/T1-warning, obtain genuine compatible canonical reference/promotion plus the operative protocol-choice/live hash and exact27-event execution scope, then perform actual admitted replay and eligible per-metric evaluation. Current content approval cannot invent missing session/exposure/clock states, required independent engine/triggered-review parents or adjudication reasons. Resolve genuine disputes only if they exist. Do not remove the guard or reselect M4 to force execution.

The audio comparison exposes poor specificity at the unchanged0.37 recording max-window rule relative to adopted event labels. This merits source-specific reference/error investigation; it is not a license to retune on this evaluation set. No window labels, weather causes, model superiority or human accuracy are inferred. All observations come from27 selected physical events at one site, so thousands of outputs do not establish generalization, safety benefits or deployment readiness.

R04 stays optional exact-eleven with event_010 excluded; event_010 remains included in primary full-cohort independent-camera analyses. PhysicalT2/occupancy/RD046 and comparator remain deferred/inactive. No new training/CV/split/site/sensor/hardware/actuation programme is introduced. The remaining100 unpassed current-context test cases are explicit in software triage; do not relabel the full guarded suite passing.

The professor can now assess actual full-cohort findings, AI-assisted reference scope, error patterns and exact missing endpoints. No manuscript/journal or external handoff has been performed.
''')
# Objective acceptance distinguishes completed operational work from unsupported scientific endpoints.
criteria=[('All27 events reconciled','COMPLETE','54 exact current hashes/streams;27-event matrix'),('Annotation coverage and verification documented','COMPLETE_WITH_LIMITATIONS','27 active AI-assisted contents genuinely researcher-adopted; no frame boxes/window labels/canonical promotion'),('Image inference on all eligible sources','COMPLETE','54 camera members:44 new+10 reused, no failures'),('Audio inference on all eligible existing B1 sources','COMPLETE','27 front tracks:22 new+5 reused; back-audio condition not adopted'),('Multimodal experiments where actually admitted','INPUT_ASSEMBLY_COMPLETE; DECISION_REPLAY_BLOCKED','27 actual assemblies; no genuine promotion/protocol binding for guarded B2'),('Scientifically valid supported metrics','PARTIAL','23-event adopted-label horn agreement complete; image/window/canonical timing endpoints unavailable'),('Per-event findings','COMPLETE','Visual/audio/input tables preserve27 event identities'),('Failure investigation','COMPLETE_AT_AVAILABLE_REFERENCE_SCOPE','11 acoustic event-label mismatches and28 total review-candidate rows; no fake matched-box errors'),('Full relevant software programme','EXECUTED_NONPASSING','3815/3700pass/84fail/31error/0skip plus separate15/15 normal metadata integration'),('Genuine defects fixed where possible','NO_NEW_CORE_DEFECT_DEMONSTRATED','No production/test/config changes; no test weakened'),('Final test results documented','COMPLETE','All3815 IDs preserved;115 audited nonpasses classified with15 follow-up passes'),('Reproducibility','COMPLETE_AT_AVAILABLE_ASSET_SCOPE','Actual commands/run manifests/hashes/versions/logs; raw/model/private assets deliberately excluded'),('Figures and data','COMPLETE','Nine actual-output figures plus underlying tables/plot script'),('Final evidence package','COMPLETE_AVAILABLE_EVIDENCE_SCOPE','This package; Mission42 untouched; no claim entire science complete'),('Integrity','CHECKED_BEFORE_COMMIT','Package verifier and actual-data/metric/source preservation checks'),('Git safety','LOCAL_EXACT_PATH_ONLY','Original seven researcher changes/caches preserved; no push/history rewrite')]
save(D/'FINAL_ACCEPTANCE_STATUS.json',{'schema':'mission43-final-acceptance/1','overall':'ALL_GENUINELY_EXECUTABLE_WORK_COMPLETE; SCIENTIFIC_PROGRAMME_PARTIAL','criteria':[dict(item=i,status=s,evidence=e)for i,s,e in criteria],'not_falsely_marked_complete':['Actual B2 decision replay','Canonical Stage2.1 promotion','Image bbox/AP/mAP performance','Acoustic window correctness','Independent human inter-rater agreement','Fully passing whole-repository tests']})
# Polish only new current documents; copied original evidence is immutable.
for p in D.glob('*.md'):
 if p.name not in {'EXECUTION_SCOPE.md','EVALUATION_SCOPE_FREEZE.md'}:p.write_text(polish(p.read_text()))
print('Current full-cohort professor reports and',len(copies),'focused original/source copies prepared.')
