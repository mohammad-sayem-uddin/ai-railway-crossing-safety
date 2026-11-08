"""Validate retained Mission39 output evidence; never open original media/checkpoints."""
from pathlib import Path
from fractions import Fraction
import ast,collections,csv,gzip,hashlib,io,json,math,re,subprocess,xml.etree.ElementTree as ET
from railway_detection.safety.resource_free_acceptance import bindings
from railway_detection.safety.media_guard import _canonical_sha256
from railway_detection.experiments.layer_b_processor import deserialize_evidence_record,serialize_evidence_record
from railway_detection.evaluation.cache_only_engine import _validate_audio_record
R=Path.cwd();D=R/'docs/generated/research_results/mission39';A=D/'audio_followup';S=A/'software_validation'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
baseline=load(A/'FOLLOWUP_BASELINE_AND_BINDING.json')
for path,h in baseline['original_seven_researcher_sha256'].items():assert sha(R/path)==h,path
permitted_changes={'COMPLETE_EXPERIMENT_INVENTORY.md','EXPERIMENT_EXECUTION_MATRIX.csv','EXPERIMENT_INVENTORY_RECONCILIATION.json','FAILURE_AND_LIMITATION_REGISTER.md','METRIC_AND_STATISTICAL_ANALYSIS.md','MISSION_39_FINAL_RESULTS_REPORT.md','NEXT_RESEARCH_PHASE.md','ORIGINAL_INFERENCE_SUMMARY.json','SOFTWARE_VALIDATION_REPORT.md'}
immutable=0
for path,h in baseline['prior_committed_Mission39_sha256'].items():
 if Path(path).name not in permitted_changes:assert sha(R/path)==h,path;immutable+=1
assert subprocess.check_output(['git','diff','--name-only','--','docs/generated/master_reaudit']).decode().splitlines()==['docs/generated/master_reaudit/MISSION_17I_MISSION18_ACCEPTANCE_AND_DEPENDENCY_REGISTER.md']
full=load(S/'CORRECTED_CODE_FULL_RUN_RECEIPT.json');summary=load(S/'CORRECTED_CODE_VALIDATION_SUMMARY.json');assert full['execution_complete'] and full['source_bindings_unchanged'];assert bindings(R)==full['source_bindings'];assert full['totals']==dict(tests=3815,failures=87,errors=31,skipped=0,passed=3697)
assert sha(S/'CORRECTED_CODE_FULL_RUN_RECEIPT.json')==summary['full_receipt_sha256']
prior=load(D/'software_validation/FINAL_FULL_TEST_RECEIPT.json');bad=lambda x:{(c['class'],c['name']) for g in x['groups'] for c in g['cases'] if c['outcome'] in {'failed','error'}};assert bad(full)==bad(prior) and len(bad(full))==118
for command in summary['commands']:
 p=A/command['junit_gzip_path'];assert sha(p)==command['junit_gzip_sha256'];assert hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest()==command['junit_sha256'];ET.fromstring(gzip.decompress(p.read_bytes()))
assert not (R/'data/governance/AUTH-MEDIA-ACCESS.json').exists();assert not (R/'data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json').exists()
for suffix in ['','_RETRY','_CORRECTED']:
 receipt=load(A/f'OP39_A{suffix}_EXECUTION_RECEIPT.json')
 for state,field in [('ISSUED','issued_record_sha256'),('COMPLETED','closed_record_sha256')]:
  p=A/f'OP39_A{suffix}_{state}_AUTHORIZATION.json';record=load(p);assert sha(p)==receipt[field];assert _canonical_sha256(record)==record['record_sha256'];assert record['revoked']==(state=='COMPLETED')
  bound=record['bindings']['protocol_document'];assert sha(R/bound['path'])==bound['sha256']
 assert receipt['canonical_slot_returned_to_absent'] and receipt['subsequent_guard_refusal_verified']
run=load(A/'CORRECTED_AUDIO_RUN_MANIFEST.json');assert run['original_audio_members_completed']==5 and run['frozen_parameters']['log_scale']=='natural';assert run['accepted_GT_evaluations_executed']==0
assert sha(A/'invocations/run_embedded_audio_corrected.py')==run['invocation_source_sha256']
for path,h in run['implementation_sha256'].items():assert sha(R/path)==h
old=load(A/'legacy_db_diagnostic/ACTUAL_AUDIO_RUN_MANIFEST.json');oldby={e['event']:e for e in old['events']};windows=positives=frames=both=0
for e in run['events']:
 assert e['source_stat_stable'];assert e['pcm_audio_sha256']==oldby[e['event']]['pcm_audio_sha256'];assert e['clock_ledger']['sha256']==oldby[e['event']]['clock_ledger']['sha256']
 for key in ['predictions','descriptive_cache_rows','clock_ledger','B2_input_assembly']:
  art=e[key];p=D/art['path'];assert sha(p)==art['sha256'];assert len(p.read_text().splitlines())==art['records']
 records=[json.loads(l) for l in (D/e['predictions']['path']).read_text().splitlines()];cache=[json.loads(l) for l in (D/e['descriptive_cache_rows']['path']).read_text().splitlines()];ledger=[json.loads(l) for l in (D/e['clock_ledger']['path']).read_text().splitlines()]
 prev=None
 for frame in ledger:
  start=Fraction(frame['pts'])*Fraction(*frame['timebase']);assert prev is None or start==prev;prev=start+Fraction(frame['samples'],frame['sample_rate'])
 assert ledger[0]['pts']==0 and all(f['timebase']==[1,48000] for f in ledger)
 for i,row in enumerate(records):
  assert serialize_evidence_record(deserialize_evidence_record(row))==row;m=row['metadata'];p=m['probability'];assert row['source_id']=='audio_1' and row['modality']=='audio' and row['available'];assert math.isfinite(p) and 0<=p<=1 and m['feature_log_scale']=='natural' and m['audio_safety_role']=='supporting_only';assert row['timestamp_s']==i*.5+1 and Fraction(*m['causal_end_fraction'])==Fraction(i*8000+16000,16000);assert cache[i]['horn_confidence']==p and cache[i]['is_horn_detected']==(p>=.37);_validate_audio_record(cache[i],i)
 assert len(records)==e['window_count'];assert sum(r['is_horn_detected'] for r in cache)==e['predicted_train_windows'];windows+=len(records);positives+=e['predicted_train_windows'];frames+=e['B2_input_assembly']['records'];both+=e['B2_frames_with_both_stream_records']
 assembly=[json.loads(l) for l in (D/e['B2_input_assembly']['path']).read_text().splitlines()]
 for f in assembly:assert all(t<=f['master_timestamp_s']+1e-6 for t in f['front_prediction_timestamps']+f['causal_audio_window_end_timestamps'])
assert (windows,positives,frames,both)==(423,120,1079,634)
preservation=load(A/'LEGACY_DB_DIAGNOSTIC_PRESERVATION.json')
for path,h in preservation['hashes'].items():assert sha(A/path)==h,path
archive_map=load(A/'legacy_db_diagnostic/ARCHIVE_PATH_RESOLUTION.json')['original_to_archived_path']
for e in old['events']:
 for key in ['predictions','descriptive_cache_rows','B2_input_assembly']:assert sha(D/archive_map[e[key]['path']])==e[key]['sha256']
result=load(A/'AUDIO_AND_B2_INPUT_RESULT_VALIDATION.json')
for path,meta in result['logs'].items():
 p=D/path;assert sha(p)==meta['gzip_sha256'];raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==meta['uncompressed_sha256'] and len(raw)==meta['uncompressed_bytes']
# Machine-readable files, tables and links. Historical literal text snapshots are not live documents.
counts=collections.Counter();csv_counts={};links=0
for p in sorted(D.rglob('*')):
 assert not p.is_symlink()
 if not p.is_file():continue
 assert p.suffix.lower() not in {'.mov','.mp4','.pt','.wav','.mp3','.npz','.npy'},p
 if p.suffix=='.json':load(p);counts['json']+=1
 if p.suffix=='.jsonl':
  for line in p.read_text().splitlines():json.loads(line)
  counts['jsonl']+=1
 if p.name.endswith('.xml.gz'):ET.fromstring(gzip.decompress(p.read_bytes()));counts['junit_xml_gzip']+=1
 if p.suffix=='.xml':ET.parse(p);counts['junit_xml']+=1
 if p.suffix=='.py':ast.parse(p.read_text());counts['invocation_python']+=1
 if p.suffix=='.csv':
  reader=csv.DictReader(io.StringIO(p.read_text()));headers=reader.fieldnames;rr=list(reader);assert headers and len(set(headers))==len(headers);assert rr
  for row in rr:assert set(row)==set(headers) and all(v is not None and v!='' and not v.lstrip().startswith(('=','+','-','@')) for v in row.values()),p
  out=io.StringIO();w=csv.DictWriter(out,fieldnames=headers,lineterminator='\n');w.writeheader();w.writerows(rr);assert list(csv.DictReader(io.StringIO(out.getvalue())))==rr;csv_counts[str(p.relative_to(D))]=len(rr)
 if p.suffix=='.md':
  body=p.read_text();assert body.count('```')%2==0,p;counts['markdown']+=1
  for target in re.findall(r'!?\[[^\]]*\]\(([^\)]+)\)',body):
   if not re.match(r'^[a-z]+:|^#',target):assert (p.parent/target.split('#')[0]).exists(),(p,target);links+=1
  widths=[]
  for line in body.splitlines()+['']:
   if line.startswith('|'):widths.append(len(line.split('|')))
   elif widths:assert len(set(widths))==1,(p,widths);widths=[]
rows=list(csv.DictReader((D/'EXPERIMENT_EXECUTION_MATRIX.csv').open()));original=list(csv.DictReader((R/'docs/generated/master_reaudit/mission31/EXPERIMENT_MASTER_REGISTER.csv').open()));assert len(rows)==156 and {r['activity_id'] for r in rows}=={r['experiment_id'] for r in original}
assert not (D/'B2_FRONT_RESULTS.md').exists() and (D/'B2_FRONT_INPUT_ASSEMBLY_REPORT.md').exists()
assert (D/'B1_AUDIO_RESULTS.md').exists();loc=load(A/'EXACT_MEMBER_LOCATION_RECEIPT.json');assert loc['located']==loc['members']==54 and not loc['missing']
status=dict(schema='mission39-audio-followup-delivery-validation/1',valid=True,corrected_B1_sources=5,windows=windows,model_positive_windows=positives,B2_input_frames=frames,B2_paired_input_frames=both,B2_decision_replays=0,GT_metrics=0,all_actual_prediction_hashes_serializers_clock_and_PCM_bindings_valid=True,three_audio_capabilities_closed=True,canonical_media_and_descriptive_grants_absent=True,full_test_totals=full['totals'],full_test_bindings_current=True,historical_nonpassing_IDs_exact_match=118,prior_committed_result_files_unchanged=immutable,original_seven_researcher_hashes_preserved=True,diagnostic_archive_hashes_preserved=True,temporary_original_AUTH35_V_files_unavailable_disclosed=True,original_media_or_model_opened_by_this_validation=False,document_checks='Table widths, fenced blocks and local links; no claim of full Markdown renderer validation',artifact_types=dict(counts),csv_rows=csv_counts,valid_relative_links=links,conditional_full_B2_result_absent=True,git_delivery='Exact local commit and final worktree verified after commit; no push')
status['artifact_sha256']={str(p.relative_to(D)):sha(p) for p in D.rglob('*') if p.is_file() and p!=A/'FOLLOWUP_DELIVERY_VALIDATION.json'}
(A/'FOLLOWUP_DELIVERY_VALIDATION.json').write_text(json.dumps(status,indent=2)+'\n');print(json.dumps(status,indent=2))
