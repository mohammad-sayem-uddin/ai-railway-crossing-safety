"""Analyze real full-cohort saved outputs and scoped adopted-reference agreement; no raw I/O."""
from common import *
import csv,collections,math,shutil
import numpy as np
from railway_detection.audio.evaluation import compute_binary_metrics,compute_roc_curve,compute_pr_curve
from railway_detection.evaluation.cache_only_engine import CacheOnlyReplayEngine
from railway_detection.evaluation import descriptive_exec_gate as gate,governance,protocol_choices
from railway_detection.experiments.frozen_config import load_frozen_config

def rows(artifact):
 p=R/artifact['path'];assert sha(p)==artifact['sha256'];return[json.loads(line)for line in p.read_text().splitlines()]
def table(name,data):
 if not data:return
 with(D/name).open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
visual=read(D/'ACTUAL_VISUAL_RUN_MANIFEST.json');audio=read(D/'ACTUAL_AUDIO_RUN_MANIFEST.json');verification=read(D/'SOURCE_VERIFICATION_RECEIPT.json');anno=read(D/'ANNOTATION_RECORD_INSPECTION.json');adopted={e['event']:e for e in anno['events']};vmap={(x['event'],x['camera']):x for x in visual['events']};amap={x['event']:x for x in audio['events']};smap={(x['event'],x['camera']):x for x in verification['members']}
summary=[];classes=[];runs=[];confidences=[];cadence=[];boundarylinks=[];acoustics=[];inputrows=[];acousticruns=[];adoptedrows=[];metricrows=[];joined=[];outliers=[]
# Actual scalar output descriptors retain event/camera separation.
for e in visual['events']:
 if e['status']not in ['COMPLETED_ORIGINAL_INFERENCE','REUSED_MISSION39_ACTUAL_INFERENCE']:continue
 a=rows(e['predictions']);times=[x.get('timestamp_sec',x.get('timestamp_s'))for x in a];frameids=[x['metadata']['frame_index']for x in a];assert len(times)>0 and all(b>a for a,b in zip(times,times[1:]));assert all(math.isfinite(t)for t in times)
 cohort=e['event'].split('/')[0];detframes=sum(bool(x['detections'])for x in a);objects=sum(len(x['detections'])for x in a)
 summary.append(dict(event=e['event'],cohort=cohort,camera=e['camera'],execution=e['status'],sampled_records=len(a),frames_with_model_detections=detframes,frames_without_detections=len(a)-detframes,predicted_objects=objects,first_pts_s=times[0],last_pts_s=times[-1],original_pipeline_wall_s=e['wall_s_original'],sampled_records_per_pipeline_wall_s=len(a)/e['wall_s_original'],annotation=adopted[e['event']]['active_proposal_path'],reference_status='RESEARCHER_ADOPTED_AI_ASSISTED; no box reference',metric_status='DESCRIPTIVE_NOT_DETECTION_CORRECTNESS'))
 for label,c in e['predicted_classes'].items():classes.append(dict(event=e['event'],cohort=cohort,camera=e['camera'],class_id=label,label=c['label'],predicted_objects=c['detections'],mean_confidence=c['mean_confidence'],minimum_confidence=c.get('confidence_min'),maximum_confidence=c.get('confidence_max'),reference_boxes='MISSING; per-class accuracy/AP unavailable'))
 for x in a:
  for det in x['detections']:confidences.append(dict(event=e['event'],camera=e['camera'],native_time_s=x.get('timestamp_sec',x.get('timestamp_s')),frame_index=x['metadata']['frame_index'],class_id=det.get('class_id',det.get('metadata',{}).get('class_id')),label=det.get('class_name',det.get('label')),confidence=det['confidence'],box=json.dumps(det.get('bbox_xyxy',det.get('bbox')),separators=(',',':'))))
 start=0;state=bool(a[0]['detections'])
 for i in range(1,len(a)+1):
  if i==len(a)or bool(a[i]['detections'])!=state:
   runs.append(dict(event=e['event'],camera=e['camera'],model_detection_present=state,first_sample_index=start,last_sample_index=i-1,sampled_records=i-start,first_source_pts_s=times[start],last_source_pts_s=times[i-1],interpretation='Run over sampled outputs, not continuous physical presence or accepted truth'));start=i
   if i<len(a):state=bool(a[i]['detections'])
 dt=[round(b-a,12)for a,b in zip(times,times[1:])]
 for delta,n in sorted(collections.Counter(dt).items()):cadence.append(dict(event=e['event'],camera=e['camera'],sampled_source_interval_s=delta,count=n,interpretation='Observed sampled native-clock intervals; no invented sync/tolerance'))
 byframe={x['metadata']['frame_index']:x for x in a}
 proposal=read(R/adopted[e['event']]['active_proposal_path']);ts=proposal.get('proposed_timestamps',{})
 for name,t in ts.items():
  if not isinstance(t,dict)or t.get('reference_camera')!=e['camera']:continue
  target=t.get('frame_index');value=t.get('value_s');found=byframe.get(target);native=found.get('timestamp_sec',found.get('timestamp_s'))if found else None
  boundarylinks.append(dict(event=e['event'],camera=e['camera'],annotation_field=name,annotation_value_s=value,annotation_frame_index=target,annotation_native_fps=t.get('native_fps'),candidate_observable=t.get('candidate_observable'),ambiguity_flag=t.get('ambiguity_flag'),exact_frame_in_inference_samples=found is not None,decoded_source_pts_s=native,annotation_minus_exact_sample_pts_s=(value-native)if isinstance(value,(int,float))and native is not None else None,comparison_status='EXACT_REFERENCED_FRAME_DIAGNOSTIC'if found else'NO_EXACT_FRAME_IN_SAMPLED_OUTPUT; no interpolation or tolerance introduced',canonical_GT=False))
 # These are review candidates, not confirmed false positives/missed trains.
 if cohort=='no_train_events'and objects:outliers.append(dict(event=e['event'],camera=e['camera'],kind='MODEL_OBJECTS_ON_RESEARCHER_ADOPTED_NO_TRAIN_EVENT',count=objects,evidence=e['predictions']['path'],interpretation='Potential false detections relative to adopted event label; no matched-box FP count inferred'))
 if cohort=='train_events'and objects==0:outliers.append(dict(event=e['event'],camera=e['camera'],kind='ZERO_OBJECT_OUTPUTS_ON_ADOPTED_TRAIN_EVENT',count=0,evidence=e['predictions']['path'],interpretation='Detection-coverage concern; no frame-level FN count without boxes/coverage truth'))
# Retain adopted lighting/weather descriptions as context, never as measured condition accuracy.
for row in summary:
 candidate=read(R/adopted[row['event']]['active_proposal_path']);conditions=candidate.get('proposed_environmental_conditions',{});row['adopted_lighting']=conditions.get('lighting');row['adopted_weather']=conditions.get('weather')
# Audio record/window outputs are distinct from whole-event labels and timing truth.
train_y=[];train_score=[];evalrows=[];engine=[];excluded=[];manifest={'manifest_version':'1.0.0','created_at':now(),'cohort':'full27_independent_front_audio','events':{}}
for event in INV:
 ann=adopted[event];candidate=read(R/ann['active_proposal_path']);meta=candidate.get('proposed_train_metadata',{});horn=meta.get('horn_status');label=1 if horn=='present'else 0 if horn=='absent_observed'else None;category=event.split('/')[0]
 for key,val in meta.items():
  if key.startswith('horn_')or key=='train_present':adoptedrows.append(dict(event=event,annotation_file=ann['active_proposal_path'],annotation_sha256=ann['active_proposal_sha256'],field=key,value=json.dumps(val),researcher_adopted=True,source_scope='Event-level adopted AI-assisted content; no per-field acoustic member binding recorded',independent_human_record=False))
 e=amap.get(event)
 if not e or e['status']not in ['COMPLETED_ORIGINAL_AUDIO_INFERENCE','REUSED_MISSION39_CORRECTED_AUDIO']:
  excluded.append(dict(event=event,reason='AUDIO_OUTPUT_UNAVAILABLE',label=label));continue
 a=rows(e['predictions']);probs=[x['metadata']['probability']for x in a];assert len(a)==e['window_count'];assert all(x['metadata']['feature_log_scale']=='natural'for x in a);score=max(probs);pred=int(score>=.37);positive=sum(p>=.37 for p in probs);assert positive==e['predicted_train_windows']
 hstatus='ELIGIBLE_EXPLORATORY_EVENT_LABEL_COMPARISON'if label is not None and category=='train_events'else'SEPARATE_ENGINE_CASE'if category=='engine_events'else'UNAVAILABLE_NULL_HORN_LABEL'
 ar=dict(event=event,cohort=category,execution=e['status'],windows=len(a),model_positive_windows=positive,maximum_window_score=score,mean_model_score=sum(probs)/len(probs),recording_prediction_at_0_37=pred,adopted_horn_status=horn,adopted_event_horn_label=label,comparison_status=hstatus,annotation_file=ann['active_proposal_path'],annotation_sha256=ann['active_proposal_sha256'],acoustic_member_reference_scope='Event label names both camera sources; horn field does not independently identify this front member',original_pipeline_wall_s=e['wall_s_original'],unwindowed_tail_samples=e['unwindowed_tail_samples'],window_accuracy='UNAVAILABLE_NO_WINDOW_LABELS')
 acoustics.append(ar)
 if label is not None and category=='train_events':train_y.append(label);train_score.append(score);evalrows.append({**ar,'agreement_class':('TP'if pred and label else'FP'if pred else'FN'if label else'TN')})
 elif category=='engine_events':engine.append({**ar,'matches_adopted_event_label':pred==label if label is not None else None})
 else:excluded.append(dict(event=event,reason='NULL_HORN_STATUS; no-train is not automatically no-horn',label=label))
 if label is not None and pred!=label:outliers.append(dict(event=event,camera='front_audio',kind='AUDIO_EVENT_LABEL_DISAGREEMENT_'+('FP'if pred else'FN'),count=1,evidence=e['predictions']['path'],interpretation='Exploratory max-window event-label mismatch; not localized horn/window error or independent human GT'))
 start=0;state=probs[0]>=.37
 for i in range(1,len(probs)+1):
  if i==len(probs)or(probs[i]>=.37)!=state:
   acousticruns.append(dict(event=event,model_positive=state,first_window=start,last_window=i-1,windows=i-start,first_causal_end_s=a[start]['timestamp_s'],last_causal_end_s=a[i-1]['timestamp_s'],interpretation='Correlated model-label run, not measured physical horn duration'));start=i
   if i<len(probs):state=probs[i]>=.37
 if 'B2_input_assembly'in e:
  assembly=rows(e['B2_input_assembly']);paired=sum(bool(a['front_prediction_timestamps'])and bool(a['causal_audio_window_end_timestamps'])for a in assembly);missing=[a for a in assembly if not a['causal_audio_window_end_timestamps']];initial=sum(x['master_timestamp_s']<a[0]['timestamp_s'] for x in missing)
  # Initial is count before actual first causal window; no fill or negative substitution.
  inputrows.append(dict(event=event,input_frames=len(assembly),both_stream_record_frames=paired,no_audio_record_frames=len(missing),initial_no_audio_record_frames=initial,later_no_audio_record_frames=len(missing)-initial,decision_frames='NOT_EXECUTED',assembly_sha256=e['B2_input_assembly']['sha256']))
  if(event,'front')in vmap:
   v=vmap[event,'front'];visionart=v.get('predictions');cache=e['descriptive_cache_rows'];assert sha(R/cache['path'])==cache['sha256']
   manifest['events'][event]=dict(event_id=event,front_vision_cache=dict(path=visionart['path'],sha256=visionart['sha256'],byte_size=(R/visionart['path']).stat().st_size,line_count=visionart['records']),front_audio_cache=dict(path=cache['path'],sha256=cache['sha256'],byte_size=(R/cache['path']).stat().st_size,line_count=cache['records']))
assert len(train_y)>0
metrics=compute_binary_metrics(np.array(train_y),np.array(train_score),threshold=.37).to_dict()
# No artificial single-class curve or zero-denominator rate.
if len(set(train_y))<2:
 for k in ['auc_roc','pr_auc','balanced_accuracy']:metrics['rates'][k]=None
if metrics['confusion_matrix']['tp']+metrics['confusion_matrix']['fp']==0:metrics['rates']['precision']=None
if not sum(train_y):metrics['rates']['recall']=None
if all(train_y):metrics['rates']['specificity']=None
metrics.update(schema='mission43-exploratory-adopted-event-label-audio-agreement/1',evaluation_scope='EVALUATION_SCOPE_FREEZE.md; existing V3 max-window recording rule against adopted event horn_status; not independent/localized human GT',scope_sha256=sha(D/'EVALUATION_SCOPE_FREEZE.md'),metric_implementation='src/railway_detection/audio/evaluation.py',metric_implementation_sha256=sha(R/'src/railway_detection/audio/evaluation.py'),annotation_adoption_sha256=sha(D/'RESEARCHER_ANNOTATION_ADOPTION.json'),actual_event_denominator=len(train_y),unit='one physical train event, one front acoustic track',engine_excluded_from_pool=True,negative_controls_with_null_horn_label_excluded=True,excluded=excluded,engine_case=engine,window_labels_invented=False,canonical_GT_promotion=False,limitations=['AI-assisted labels adopted after reported manual verification; no separate observations stored','Event-level horn fields reference paired sources rather than verified front-only horn truth','Original five known results reused; not a newly blind confirmatory experiment','Max pooling varies with duration/window count; overlapping windows are not independent events','No horn timing/window accuracy/safety/generalization conclusion'])
# Calibration summaries are not meaningful for max-pooled event scores; remove rather than imply calibration.
for key in ['brier_score','expected_calibration_error','false_alarms_per_hour']:metrics['rates'][key]=None
save(D/'AUDIO_ADOPTED_EVENT_LABEL_METRICS.json',metrics);save(D/'B2_EVALUATION_INPUT_MANIFEST.json',manifest)
for name,data in [('VISUAL_PER_EVENT_RESULTS.csv',summary),('VISUAL_PER_CLASS_PREDICTIONS.csv',classes),('VISUAL_OUTPUT_RUNS.csv',runs),('VISUAL_CONFIDENCE_VALUES.csv',confidences),('VISUAL_NATIVE_SAMPLE_CADENCE.csv',cadence),('ANNOTATION_SAMPLED_FRAME_LINKAGE.csv',boundarylinks),('AUDIO_PER_EVENT_RESULTS.csv',acoustics),('AUDIO_ADOPTED_EVENT_COMPARISONS.csv',evalrows),('AUDIO_MODEL_LABEL_RUNS.csv',acousticruns),('B2_INPUT_COVERAGE.csv',inputrows),('ADOPTED_REFERENCE_FIELDS.csv',adoptedrows),('FAILURE_REVIEW_CANDIDATES.csv',outliers)]:table(name,data)
# Current full27 early admission call uses actual payload references, never fake canonical records.
output=R/'results/replays/mission43_admission_only';before=output.exists();engine_obj=CacheOnlyReplayEngine(D/'B2_EVALUATION_INPUT_MANIFEST.json',repo_root=R,output_base_dir=output)
try:engine_obj.execute_replay(next(iter(manifest['events'])),'B2')
except gate.DescriptiveExecutionNotAuthorized as exc:refusal={'code':exc.code,'detail':exc.detail}
else:raise AssertionError('Unexpected replay admission; do not execute outside missing-binding analysis')
assert output.exists()==before
save(D/'B2_CURRENT_ADMISSION_RECEIPT.json',dict(schema='mission43-full-cohort-B2-admission/1',condition='B2',operation=gate.DESCRIPTIVE_OPERATION,actual_refusal=refusal,manifest_sha256=sha(D/'B2_EVALUATION_INPUT_MANIFEST.json'),manifest_events=len(manifest['events']),decision_events=0,decision_frames=0,promotion_receipt_exists=(R/governance.PROMOTION_RECEIPT_RELATIVE).exists(),protocol_choice_exists=(R/'data/manifests/phase12_protocol_decision.json').exists(),canonical_authorization_created=False,output_created=False,annotation_approval_not_fake_promotion=True))
# Every unavailable family names the missing actual field/contract, rather than assigning zeros.
for family,reason in [('VISION_TP_FP_FN_PRECISION_RECALL_F1','No frame/instance bbox reference labels or adopted vision event-matching endpoint'),('VISION_AP_MAP50_MAP50_95_PER_CLASS','No source-frame class/bounding-box GT, so existing IoU matching cannot run'),('AUDIO_WINDOW_TP_FP_FN_CONFUSION_ROC_PR','No actual window labels or horn offsets; do not spread event horn_status over windows'),('AUDIO_CONTROL_EVENT_METRICS','Three no-train events have null horn_status, not negative acoustic labels'),('HUMAN_INTER_RATER_AGREEMENT','Original separate pre-comparison observations were not stored'),('M4_M5_MTR_T1_WARNING','No accepted Stage2.1 clock/boundary/reference promotion and no decision replay'),('B2_DECISION_METRICS','Actual descriptive replay not admitted; promotion/protocol bindings absent'),('PHYSICAL_T2_OCCUPANCY_RD046','Explicitly deferred; candidate content approval does not validate physical landmark'),('ROC_PR_FOR_ENGINE_ALONE','Single separate engine case cannot define two-class ROC/PR')]:metricrows.append(dict(metric_family=family,status='UNAVAILABLE',value='null',numerator='null',denominator='null',reason=reason))
metricrows.insert(0,dict(metric_family='AUDIO_EVENT_LABEL_TP_FP_FN_TN_PRECISION_RECALL_F1_SPECIFICITY_ROC_AP',status='EXECUTED_EXPLORATORY_ADOPTED_REFERENCE_AGREEMENT',value='AUDIO_ADOPTED_EVENT_LABEL_METRICS.json',numerator='See exact confusion counts',denominator=str(len(train_y))+' physical train events; engine/control separate',reason='Existing fixed recording max-pool/.37 method; camera-label scope and AI-assisted reference limitations disclosed'))
table('METRIC_EXECUTION_REGISTER.csv',metricrows)
for event,e in INV.items():
 vf=vmap.get((event,'front'),{});vb=vmap.get((event,'back'),{});a=amap.get(event,{});ss=smap[event,'front'];sb=smap[event,'back'];an=adopted[event];inp=next((x for x in inputrows if x['event']==event),{})
 joined.append(dict(event=event,category=e['cohort'],front_source=e['raw_media']['front']['path'],front_sha256=ss.get('fresh_sha256'),back_source=e['raw_media']['back']['path'],back_sha256=sb.get('fresh_sha256'),source_verification_front=ss.get('status'),source_verification_back=sb.get('status'),front_video_stream=ss['video']['index'],back_video_stream=sb['video']['index'],front_video_timebase=ss['video']['time_base'],back_video_timebase=sb['video']['time_base'],front_audio_streams=len(ss['audio']),back_audio_streams=len(sb['audio']),front_experiment=vf.get('status','UNAVAILABLE'),back_experiment=vb.get('status','UNAVAILABLE'),audio_experiment=a.get('status','UNAVAILABLE'),front_sampled_records=vf.get('sampled_records'),back_sampled_records=vb.get('sampled_records'),audio_windows=a.get('window_count'),B2_input_frames=inp.get('input_frames'),B2_decision_replay='NOT_EXECUTED',annotation_file=an['active_proposal_path'],annotation_sha256=an['active_proposal_sha256'],annotation_version=an['active_proposal_schema'],manual_verification='RESEARCHER_REPORTED_AND_CONTENT_ADOPTED',canonical_GT='NOT_ESTABLISHED',vision_box_reference='MISSING',audio_window_reference='MISSING',duplicate_exclusion='No active event excluded; two historical camera duplicate refs remain excluded',R04='OPTIONAL_EXACT11; event010 excluded only from R04'))
table('FULL_27_EVENT_COVERAGE_MATRIX.csv',joined)
report={'schema':'mission43-actual-cohort-result-summary/1','physical_events':len(INV),'source_members_verified':verification['verified'],'new_visual_members_executed':visual['new_original_members_completed'],'reused_visual_members':visual['reused_original_members'],'failed_visual_members':visual['failed_members'],'visual':{role:{'members':sum(e['camera']==role for e in summary),'sampled_records':sum(e['sampled_records']for e in summary if e['camera']==role),'predicted_objects':sum(e['predicted_objects']for e in summary if e['camera']==role)}for role in ['front','back']},'new_audio_members_executed':audio['new_original_members_completed'],'reused_audio_members':audio['reused_members'],'failed_audio_members':audio['failed_members'],'audio_windows':sum(e['windows']for e in acoustics),'audio_model_positive_windows':sum(e['model_positive_windows']for e in acoustics),'audio_event_reference_denominator':len(train_y),'audio_event_reference_metrics':metrics,'B2_input_events':len(inputrows),'B2_input_frames':sum(e['input_frames']for e in inputrows),'B2_both_record_frames':sum(e['both_stream_record_frames']for e in inputrows),'B2_no_audio_record_frames':sum(e['no_audio_record_frames']for e in inputrows),'B2_decision_events':0,'B2_decision_frames':0,'failure_review_candidates':len(outliers),'canonical_GT':'NOT_ESTABLISHED','all27_adopted_annotation_contents_preserved':True,'annotation_reference_coverage_status':'27 researcher-adopted event/boundary files; no box/window-level reference rows','new_original_inference_run_counts_not_added_to_reused':True}
save(D/'ACTUAL_FULL_COHORT_RESULTS.json',report);print(json.dumps({k:v for k,v in report.items()if k!='audio_event_reference_metrics'},indent=2))
