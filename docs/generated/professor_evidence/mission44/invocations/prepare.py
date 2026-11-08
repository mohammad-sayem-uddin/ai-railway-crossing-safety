"""Freeze Mission43 and preselect diagnostic observations before new source inspection."""
from common import *
b=read(M/'BASELINE_AND_PRESERVATION.json');pins=b['prior_artifact_sha256'].copy()
for p in M.rglob('*'):
 if p.is_file():pins[str(p.relative_to(R))]=sha(p)
for s,h in pins.items():assert sha(R/s)==h,s
for group in ['original_seven_researcher_sha256','annotation_text_sha256','source_sha256']:
 for s,h in b[group].items():assert sha(R/s)==h,s
x={'schema':'mission44-preservation/1','date':'2026-11-08','timezone':'America/New_York','starting_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'tracking':subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip(),'initial_status':subprocess.check_output(['git','status','--short'],text=True),'prior_artifact_sha256':pins,**{k:b[k]for k in ['original_seven_researcher_sha256','annotation_text_sha256','source_sha256']},'request_sha256':sha(Path('/Users/sayemuddin/.codex/attachments/5e0ed8be-414a-476c-bc5a-a50ee5a156c6/Pasted text.txt')),'primary_audio_result':read(M/'AUDIO_ADOPTED_EVENT_LABEL_METRICS.json'),'no_inference_rerun_planned':True};save(D/'BASELINE_AND_PRESERVATION.json',x)
v=read(M/'ACTUAL_VISUAL_RUN_MANIFEST.json');source={(e['event'],e['camera']):e for e in read(M/'SOURCE_VERIFICATION_RECEIPT.json')['members']};visual=[];members={};counts=[]
for role in ['front','back']:
 for cohort in ['train_events','no_train_events','engine_events']:
  e=[r for r in v['events']if r['camera']==role and r['event'].startswith(cohort+'/')];counts.append({'camera':role,'cohort':cohort,'physical_events':len(e),'recordings_with_objects':sum(r['predicted_objects']>0 for r in e),'zero_object_recordings':sum(r['predicted_objects']==0 for r in e),'predicted_objects':sum(r['predicted_objects']for r in e),'positive_sampled_frames':sum(r['frames_with_detections']for r in e)})
for e in v['events']:
 zero=e['event'].startswith('train_events/')and e['predicted_objects']==0;control=e['event'].startswith('no_train_events/')and e['predicted_objects']>0
 if not(zero or control):continue
 rows=payload(e['predictions']);targets=[]
 if zero:
  indices={int((len(rows)-1)*q)for q in [.1,.5,.9]};ann=read(R/INV[e['event']]['active_proposal_file'])
  boundary='T1_danger_zone_entry'if e['camera']=='front'else'T3_locomotive_unit_clearance';q=ann.get('proposed_timestamps',{}).get(boundary,{})
  if q.get('reference_camera')==e['camera']and isinstance(q.get('value_s'),(int,float)):indices.add(min(range(len(rows)),key=lambda i:abs(rows[i].get('timestamp_sec',rows[i].get('timestamp_s'))-q['value_s'])))
 else:
  indices=sorted((i for i,r in enumerate(rows)if r['detections']),key=lambda i:(-max(d['confidence']for d in rows[i]['detections']),i))[:3]
 for i in sorted(indices):
  row=rows[i];targets.append({'prediction_row_index':i,'frame_index':row['metadata']['frame_index'],'source_pts_ticks':row['metadata']['pts_ticks'],'timebase':row['metadata']['timebase'],'source_timestamp_s':row.get('timestamp_sec',row.get('timestamp_s')),'existing_model_detections':row['detections']})
 s=source[e['event'],e['camera']];visual.append({'event':e['event'],'camera':e['camera'],'case_type':'ZERO_OBJECT_TRAIN_RECORDING'if zero else'DETECTIONS_ON_ADOPTED_NO_TRAIN_CONTROL','source':s,'prediction_artifact':e['predictions'],'targets':targets});members[s['path']]={'event':e['event'],'camera':e['camera'],'path':s['path']}
errors=csvrows(M/'AUDIO_ERROR_REVIEW_WINDOWS.csv');audio=read(M/'ACTUAL_AUDIO_RUN_MANIFEST.json');by={e['event']:e for e in audio['events']};selected=[]
for row in errors:
 e=by[row['event']];s=source[row['event'],'front'];selected.append({'event':row['event'],'error_type':row['comparison_class'],'source':s,'audio_record':e,'annotation':INV[row['event']]['active_proposal_file'],'top_window_count':3});members[s['path']]={'event':row['event'],'camera':'front','path':s['path']}
plan={'schema':'mission44-targeted-real-source-plan/1','visual_cases':visual,'audio_errors':selected,'members':list(members.values()),'selection':'All13 zero-object train-camera recordings plus all4 control-camera recordings with detections. Zero:10/50/90percent sample indices and nearest actual sample to adoptedT1/front orT3/back when present. Control:up to3 highest-confidence actual detection frames. Audio:all11 errors; full original front audio converted only for exact PCM identity and descriptors, top3 existing scored windows plus conditional adopted onset windows.','no_new_reference_labels_or_inference':True,'no_operating_config_or_threshold_change':True};save(D/'SOURCE_DIAGNOSTIC_PLAN.json',plan);table('BASELINE_COUNT_RECONCILIATION.csv',counts)
print('Baseline preserved',len(pins),'artifacts;',len(visual),'visual cases;',sum(len(e['targets'])for e in visual),'selected real frames;',len(selected),'audio errors;',len(members),'unique exact source members.')
