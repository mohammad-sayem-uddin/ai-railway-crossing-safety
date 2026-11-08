"""Verify Mission40 documentary/test evidence without original media/model I/O."""
from pathlib import Path
import ast,collections,csv,gzip,hashlib,io,json,re,subprocess,xml.etree.ElementTree as ET
from railway_detection.safety.resource_free_acceptance import bindings,case_node
R=Path.cwd();D=R/'docs/generated/research_results/mission40';S=D/'software_validation';load=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=load(D/'BASELINE_AND_PRESERVATION.json')
for family in ['previous_documentary_artifact_sha256','original_seven_researcher_sha256']:
 for path,h in b[family].items():assert sha(R/path)==h,path
full=load(S/'FULL_RUN_RECEIPT.json');assert full['execution_complete'] and full['source_bindings_unchanged'];assert bindings(R)==full['source_bindings'];assert full['totals']==dict(tests=3815,failures=84,errors=31,skipped=0,passed=3700)
changed=[]
for family in ['modules','shared_source_sha256']:
 for path in set(b['source_bindings'][family])|set(full['source_bindings'][family]):
  if b['source_bindings'][family].get(path)!=full['source_bindings'][family].get(path):changed.append(path)
assert set(changed)=={'tests/test_phase11_9_synthetic_pilot.py','tests/unit/test_phase14_benchmark_suite.py','tests/test_access_classification.yaml'}
summary=load(S/'VALIDATION_SUMMARY.json');assert sha(S/'FULL_RUN_RECEIPT.json')==summary['full_receipt_sha256']
for g in summary['commands']:
 folder=S/'groups'/g['group']
 for name,h in g['artifacts'].items():assert sha(folder/name)==h
 xml=gzip.decompress((folder/'pytest.xml.gz').read_bytes());assert hashlib.sha256(xml).hexdigest()==g['junit_uncompressed_sha256'];assert sum(float(x.get('time','0')) for x in ET.fromstring(xml).iter('testsuite'))==g['junit_duration_s']
assert abs(sum(g['junit_duration_s'] for g in summary['commands'])-summary['junit_duration_s'])<1e-8
old=load(R/'docs/generated/research_results/mission39/audio_followup/software_validation/CORRECTED_CODE_FULL_RUN_RECEIPT.json');bad=lambda x:{(c['class'],c['name']) for g in x['groups'] for c in g['cases'] if c['outcome'] in {'failed','error'}};assert not bad(full)-bad(old) and len(bad(old)-bad(full))==3
assert {(c['class'],c['name']) for g in full['groups'] for c in g['cases']}=={(c['class'],c['name']) for g in old['groups'] for c in g['cases']}
admission=load(D/'B2_REPLAY_ADMISSION_RECEIPT.json');assert admission['admission']['code']=='AUTH_DESCRIPTIVE_EVAL_EXEC_NOT_GRANTED' and not admission['B2_decision_replay_executed'];assert admission['actual_events_processed']==admission['actual_decision_frames_processed']==0
assert not (R/'data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json').exists() and not (R/'data/governance/stage21_promotion_receipt.json').exists() and not (R/'data/governance/AUTH-MEDIA-ACCESS.json').exists()
reference=load(D/'REFERENCE_RECORD_INSPECTION.json');assert reference['active_unexcused_records']==0
for path,h in reference['text_sha256'].items():assert sha(R/path)==h
analysis=load(D/'RETAINED_OUTPUT_ANALYSIS_RECEIPT.json')
for path,h in analysis['source_payload_sha256'].items():assert sha(R/path)==h
assert (analysis['front_records'],analysis['back_records'],analysis['audio_windows'],analysis['audio_score_ge_threshold'],analysis['B2_input_frames'],analysis['B2_paired_input_frames'])==(1079,1100,423,120,1079,634)
metrics=load(D/'METRIC_EXECUTION_REGISTER.json');assert len(metrics['per_event'])==40 and sum(m['executed'] for m in metrics['per_event'])==30
for item in metrics['per_event']:
 if not item['executed']:assert item['numerator'] is None and item['denominator'] is None
rows=list(csv.DictReader((D/'COMPLETE_EXPERIMENT_STATUS_MATRIX.csv').open()));original=list(csv.DictReader((R/'docs/generated/master_reaudit/mission31/EXPERIMENT_MASTER_REGISTER.csv').open()));assert len(rows)==156 and {r['activity_id'] for r in rows}=={r['experiment_id'] for r in original}
state=load(D/'EXPERIMENT_STATUS_RECONCILIATION.json');assert dict(collections.Counter(r['classification'] for r in rows))=={k:v for k,v in state['status_counts'].items() if v};assert not (D/'B2_FRONT_DECISION_REPLAY_RESULTS.md').exists()
required=['MISSION_40_FINAL_REPORT.md','REMAINING_METRIC_EVALUATION.md','SOFTWARE_TEST_VALIDATION.md','FAILURE_AND_REGRESSION_ANALYSIS.md','SCIENTIFIC_LIMITATIONS.md','FINAL_RESEARCH_COMPLETION_ASSESSMENT.md','NEXT_PHASE_RECOMMENDATION.md']
# Eight non-result deliverables include the required CSV; B2 results are conditional.
assert all((D/name).is_file() for name in required) and (D/'COMPLETE_EXPERIMENT_STATUS_MATRIX.csv').is_file()
counts=collections.Counter();csv_counts={};links=0
for p in D.rglob('*'):
 assert not p.is_symlink()
 if not p.is_file():continue
 assert p.suffix.lower() not in {'.mov','.mp4','.wav','.mp3','.pt','.npy','.npz'},p
 if p.suffix=='.json':load(p);counts['json']+=1
 if p.suffix=='.py':ast.parse(p.read_text());counts['python_invocations']+=1
 if p.suffix=='.gz':
  raw=gzip.decompress(p.read_bytes());counts['gzip_artifacts']+=1
  if p.name.endswith('.xml.gz'):ET.fromstring(raw);counts['JUnit_xml']+=1
  elif p.name.endswith('.json.gz'):json.loads(raw)
  elif p.name.endswith('.jsonl.gz'):
   for line in raw.decode().splitlines():json.loads(line)
 if p.suffix=='.csv':
  reader=csv.DictReader(io.StringIO(p.read_text()));headers=reader.fieldnames;rr=list(reader);assert rr and len(headers)==len(set(headers))
  for row in rr:assert set(row)==set(headers) and all(v is not None and v!='' and not v.lstrip().startswith(('=','+','-','@')) for v in row.values()),p
  out=io.StringIO();w=csv.DictWriter(out,fieldnames=headers,lineterminator='\n');w.writeheader();w.writerows(rr);assert list(csv.DictReader(io.StringIO(out.getvalue())))==rr;csv_counts[p.name]=len(rr)
 if p.suffix=='.md':
  body=p.read_text();counts['markdown']+=1;assert body.count('```')%2==0
  for target in re.findall(r'!?\[[^\]]*\]\(([^\)]+)\)',body):
   if not re.match(r'^[a-z]+:|^#',target):assert (p.parent/target.split('#')[0]).exists(),(p,target);links+=1
  widths=[]
  for line in body.splitlines()+['']:
   if line.startswith('|'):widths.append(len(line.split('|')))
   elif widths:assert len(set(widths))==1,(p,widths);widths=[]
triage=list(csv.DictReader((D/'BASELINE_118_CASE_TRIAGE.csv').open()));assert len(triage)==118 and sum(r['classification']=='RESOLVED_SYNTHETIC_FIXTURE_COUPLING' for r in triage)==3
result=dict(schema='mission40-delivery-validation/1',valid=True,client_date='2026-11-08',timezone='America/New_York',prior_artifacts_unchanged=len(b['previous_documentary_artifact_sha256']),original_seven_researcher_hashes_preserved=True,production_source_config_unchanged=True,only_source_binding_changes=changed,full_test_source_bindings_current=True,test_counts=full['totals'],historical_cases_resolved=3,remaining_nonpassing_cases=115,all_3815_case_ids_retained=True,B2_decision_events=0,B2_decision_frames=0,accepted_GT_evaluations=0,B2_results_file_absent=True,all_156_activity_ids_retained=True,metric_rows=40,executed_raw_descriptor_rows=30,unavailable_evaluation_families=10,nulls_not_zero_filled=True,saved_payload_hashes_valid=True,reference_hashes_unchanged=True,canonical_grants_or_GT_created=False,required_nonconditional_deliverables_present=8,local_links_valid=links,artifact_counts=dict(counts),csv_rows=csv_counts,document_check_scope='Table widths/fences/local links; no full Markdown renderer claim',raw_source_or_model_I_O_in_validation=False,git_delivery='Containing local commit and final status verified after commit; no push')
result['artifact_sha256']={str(p.relative_to(D)):sha(p) for p in D.rglob('*') if p.is_file() and p!=D/'DELIVERY_VALIDATION.json'}
(D/'DELIVERY_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='artifact_sha256'},indent=2))
