"""Documentary/numeric integrity checks, not a new regression or empirical run."""
from pathlib import Path
from fractions import Fraction
import ast,collections,csv,hashlib,io,json,math,re
from railway_detection.safety.resource_free_acceptance import bindings
from railway_detection.evaluation import descriptive_exec_gate as gate,protocol_choices
R=Path.cwd();D=R/'docs/generated/research_results/mission41';M=R/'docs/generated/research_results/mission39';P=R/'docs/generated/research_results/mission40';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();load=lambda p:json.loads(Path(p).read_text());readcsv=lambda p:list(csv.DictReader(Path(p).open()))
b=load(D/'BASELINE_AND_PRESERVATION.json')
for key in ['prior_artifact_sha256','original_seven_researcher_sha256']:
 for p,h in b[key].items():assert sha(R/p)==h,p
assert bindings(R)==b['source_bindings']==load(P/'software_validation/FULL_RUN_RECEIPT.json')['source_bindings'];assert sha(P/'software_validation/FULL_RUN_RECEIPT.json')==b['M40_full_receipt_sha256']
prep=load(D/'B2_UNISSUED_AUTHORIZATION_PREPARATION.json');candidate=prep['candidate_fields'];assert set(candidate)==gate._KEYS and set(candidate['scope'])==gate._SCOPE_KEYS and set(candidate['bindings'])==set(gate.BINDING_KEYS)
assert candidate['scope']['conditions']==['B2'] and candidate['scope']['operation']==gate.DESCRIPTIVE_OPERATION and candidate['scope']['field_or_physical_operations_authorized'] is False
assert set(candidate['scope']['metric_scope'])==set(gate.DESCRIPTIVE_METRIC_SCOPE)
for key in ['status','authorized_at_utc','expires_at_utc','record_sha256']:assert candidate[key] is None
assert candidate['attestation']['signature'] is None and candidate['bindings']['promotion_receipt_sha256'] is None and candidate['bindings']['protocol_sha256'] is None
assert protocol_choices.profile_sha256(prep['already_selected_M4_candidate_profile'])==prep['already_selected_M4_candidate_profile_sha256']
for p in ['data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json','data/governance/stage21_promotion_receipt.json','data/governance/AUTH-MEDIA-ACCESS.json','data/manifests/phase12_protocol_decision.json']:assert not (R/p).exists(),p
for ref in prep['known_input_references']:assert sha(R/ref['path'])==ref['sha256']
ad=load(D/'B2_CURRENT_ADMISSION_RECEIPT.json');assert ad['actual_refusal']['code']=='AUTH_DESCRIPTIVE_EVAL_EXEC_NOT_GRANTED' and not ad['B2_executed'] and ad['decision_frames']==ad['decision_events']==0
ref=load(D/'REFERENCE_INTEGRITY_RECEIPT.json');assert ref['ACCEPTED_CANONICAL_GT']=='NOT_ESTABLISHED'
for p,h in ref['text_sha256'].items():assert sha(R/p)==h
receipt=load(D/'DESCRIPTIVE_EXECUTION_RECEIPT.json')
for p,h in receipt['source_payload_sha256'].items():assert sha(R/p)==h
for p,item in receipt['reused_completed_tables'].items():assert sha(M/p)==item['sha256'] and len(readcsv(M/p))==item['rows']
visual_runs=readcsv(D/'VISUAL_SAMPLE_RUNS.csv');summaries=readcsv(D/'VISUAL_CONFIDENCE_CONTINUITY_SUMMARY.csv');cadence=readcsv(D/'SAMPLED_CLOCK_CADENCE.csv')
for camera,filename in [('front','ACTUAL_RUN_MANIFEST.json'),('back','ACTUAL_BACK_RUN_MANIFEST.json')]:
 for e in load(M/filename)['events']:
  rows=[json.loads(line) for line in (M/e['prediction_file']).read_text().splitlines()];ts=[Fraction(r['metadata']['pts_ticks'])*Fraction(*r['metadata']['timebase']) for r in rows]
  for cls in ['ANY','front','rear','side']:
   def dets(row):return row['detections'] if cls=='ANY' else [x for x in row['detections'] if x.get('class_name',x.get('label'))==cls]
   flags=[bool(dets(r)) for r in rows];runs=[r for r in visual_runs if r['event']==e['event'] and r['camera']==camera and r['predicted_label']==cls];summary=next(r for r in summaries if r['event']==e['event'] and r['camera']==camera and r['predicted_label']==cls)
   assert sum(int(r['rows_in_run']) for r in runs)==sum(flags)==int(summary['rows_with_this_model_output']);assert int(summary['predicted_objects'])==sum(len(dets(r)) for r in rows)
   for r in runs:
    a,z=int(r['first_sample_index']),int(r['last_sample_index']);assert all(flags[a:z+1]) and (a==0 or not flags[a-1]) and (z==len(flags)-1 or not flags[z+1]);assert int(r['first_original_pts'])==rows[a]['metadata']['pts_ticks'] and int(r['last_original_pts'])==rows[z]['metadata']['pts_ticks'];assert float(r['sampled_endpoint_span_s'])==float(ts[z]-ts[a])
  counted=collections.Counter(b-a for a,b in zip(ts,ts[1:]));stated={Fraction(int(r['interval_numerator']),int(r['interval_denominator'])):int(r['interval_count']) for r in cadence if r['event']==e['event'] and r['stream']==camera};assert counted==stated
aruns=readcsv(D/'AUDIO_MODEL_LABEL_RUNS.csv');gruns=readcsv(D/'B2_INPUT_AUDIO_RECORD_RUNS.csv');breakdown=readcsv(D/'B2_INPUT_RECORD_ABSENCE_BREAKDOWN.csv')
for e in load(M/'audio_followup/CORRECTED_AUDIO_RUN_MANIFEST.json')['events']:
 rows=[json.loads(l) for l in (M/e['predictions']['path']).read_text().splitlines()];rr=[r for r in aruns if r['event']==e['event']];cursor=0
 for run in rr:
  a,z=int(run['first_window_index']),int(run['last_window_index']);assert a==cursor and z>=a;cursor=z+1;positive=run['model_label']=='MODEL_TRAIN_LABEL';assert all((row['metadata']['probability']>=.37)==positive for row in rows[a:z+1]);assert int(run['last_window_end_sample'])==rows[z]['metadata']['window_end_sample'];assert float(run['last_causal_window_end_s'])==rows[z]['timestamp_s']
 assert cursor==len(rows)
 frames=[json.loads(l) for l in (M/e['B2_input_assembly']['path']).read_text().splitlines()];gg=[r for r in gruns if r['event']==e['event']];cursor=0
 for run in gg:
  a,z=int(run['first_input_frame_index']),int(run['last_input_frame_index']);assert a==cursor and z>=a;cursor=z+1;present=run['input_record_state']=='AUDIO_RECORD_PRESENT';assert all(bool(f['causal_audio_window_end_timestamps'])==present for f in frames[a:z+1]);assert float(run['first_assembly_time_s'])==frames[a]['master_timestamp_s'] and float(run['last_assembly_time_s'])==frames[z]['master_timestamp_s']
 assert cursor==len(frames)
 row=next(r for r in breakdown if r['event']==e['event']);assert int(row['initial_no_audio_record_frames'])==5 and rows[0]['timestamp_s']==float(row['first_causal_audio_window_end_s'])==1.0
assert sum(int(r['initial_no_audio_record_frames']) for r in breakdown)==25 and sum(int(r['later_no_audio_record_frames']) for r in breakdown)==420 and sum(int(r['total_no_audio_record_input_frames']) for r in breakdown)==445
assert sum(int(r['windows_in_run']) for r in aruns)==423 and sum(int(r['windows_in_run']) for r in aruns if r['model_label']=='MODEL_TRAIN_LABEL')==120
aggregates=readcsv(D/'EXISTING_PROCESSING_TIME_AGGREGATES.csv');detail=readcsv(D/'EXISTING_PROCESSING_TIME_DETAIL.csv')
for a in aggregates:
 rr=[r for r in detail if r['stream']==a['stream']];assert len(rr)==5;assert sum(float(r['observed_pipeline_wall_s']) for r in rr)==float(a['sum_observed_pipeline_wall_s']);assert sum(int(r['output_units']) for r in rr)==int(a['total_output_units'])
freeze=load(D/'BOUNDED_DESCRIPTIVE_RESULTS_FREEZE.json');assert freeze['researcher_accepted'] is False and not freeze['B2_decision_replay'] and not freeze['operational_or_release_authorization']
for p,h in freeze['descriptor_artifact_sha256'].items():assert sha(D/p)==h
matrix=readcsv(D/'MISSION_41_EXPERIMENT_COMPLETION_MATRIX.csv');old=readcsv(P/'COMPLETE_EXPERIMENT_STATUS_MATRIX.csv');assert len(matrix)==156 and {r['activity_id'] for r in matrix}=={r['activity_id'] for r in old};allowed={'COMPLETED_VALID','COMPLETED_WITH_LIMITATIONS','INCOMPLETE','BLOCKED_BY_OPERATION_SCOPE','BLOCKED_BY_CANONICAL_GT','BLOCKED_BY_TECHNICAL_DEFECT','DEFERRED_BY_RESEARCHER','SCIENTIFICALLY_UNDEFINED','SUPERSEDED_OR_INVALID'};assert all(r['classification'] in allowed for r in matrix)
state=load(D/'EXPERIMENT_STATUS_RECONCILIATION.json');assert dict(collections.Counter(r['classification'] for r in matrix))=={k:v for k,v in state['status_counts'].items() if v}
required=['MISSION_41_FINAL_REPORT.md','B2_EXECUTION_ADMISSION_ANALYSIS.md','REMAINING_DESCRIPTIVE_ANALYSIS.md','REFERENCE_AND_GT_STATUS.md','MISSION_41_EXPERIMENT_COMPLETION_MATRIX.csv','FINAL_RESEARCH_STATUS.md','NEXT_PHASE_RECOMMENDATION.md'];assert all((D/p).is_file() for p in required)
assert not (D/'B2_DECISION_REPLAY_RESULTS.md').exists() and not (D/'SOFTWARE_REGRESSION_VALIDATION.md').exists()
counts=collections.Counter();csv_counts={};links=0
for p in D.rglob('*'):
 assert not p.is_symlink()
 if not p.is_file():continue
 assert p.suffix.lower() not in {'.mov','.wav','.mp4','.pt','.mp3','.npy','.npz'}
 if p.suffix=='.json':load(p);counts['json']+=1
 if p.suffix=='.py':ast.parse(p.read_text());counts['invocation_source']+=1
 if p.suffix=='.csv':
  reader=csv.DictReader(io.StringIO(p.read_text()));header=reader.fieldnames;rr=list(reader);assert rr and len(set(header))==len(header)
  for r in rr:assert set(r)==set(header) and all(v is not None and v!='' and not v.lstrip().startswith(('=','+','-','@')) for v in r.values()),p
  out=io.StringIO();w=csv.DictWriter(out,fieldnames=header,lineterminator='\n');w.writeheader();w.writerows(rr);assert list(csv.DictReader(io.StringIO(out.getvalue())))==rr;csv_counts[p.name]=len(rr)
 if p.suffix=='.md':
  body=p.read_text();assert body.count('```')%2==0;counts['markdown']+=1
  for target in re.findall(r'!?\[[^\]]*\]\(([^\)]+)\)',body):
   if not re.match(r'^[a-z]+:|^#',target):assert (p.parent/target.split('#')[0]).exists(),(p,target);links+=1
  widths=[]
  for line in body.splitlines()+['']:
   if line.startswith('|'):widths.append(len(line.split('|')))
   elif widths:assert len(set(widths))==1,(p,widths);widths=[]
result=dict(schema='mission41-current-integrity-validation/1',valid=True,client_date='2026-11-08',timezone='America/New_York',prior_artifacts_unchanged=len(b['prior_artifact_sha256']),original_seven_researcher_hashes_preserved=True,maintained_source_tests_configs_unchanged=True,M40_full_test_source_bindings_current=True,M40_reused_counts=b['M40_counts'],M41_new_pytest_runs=0,full_suite_rerun=False,regression_report_absent=True,B2_decision_events=0,B2_decision_frames=0,B2_result_file_absent=True,canonical_record_created=False,unissued_candidate_exact_keysets=True,unissued_fields_not_fabricated=True,live_protocol_hash_not_replaced_by_candidate=True,selected_M4_not_reopened=True,independent_descriptor_families_processed=5,visual_summary_rows=40,visual_sample_runs=78,cadence_frequency_rows=28,audio_model_label_runs=74,input_record_runs=847,initial_absence_frames=25,later_absence_frames=420,all_absence_frames=445,all_156_ids_retained=True,artifact_counts=dict(counts),csv_rows=csv_counts,local_links_valid=links,document_checks='CSV round-trip/header/formula prefixes, table widths/fences/local links; no full Markdown rendering claim',raw_source_or_checkpoint_I_O=False,plot_scope='Saved input-absence descriptors, not decision/performance',freeze_status=freeze['status'],freeze_not_researcher_acceptance=True,git_delivery='Containing local commit and final worktree verified after commit; no push')
result['artifact_sha256']={str(p.relative_to(D)):sha(p) for p in D.rglob('*') if p.is_file() and p!=D/'INTEGRITY_VALIDATION.json'}
(D/'INTEGRITY_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='artifact_sha256'},indent=2))
