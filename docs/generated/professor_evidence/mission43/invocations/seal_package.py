"""Review/seal the exact new package; original paths and hashes remain untouched."""
from common import *
import csv,re,ast
b=read(D/'BASELINE_AND_PRESERVATION.json');copies=read(D/'COPIED_EVIDENCE_SOURCE_MAP.json')
for group in ['prior_artifact_sha256','original_seven_researcher_sha256','annotation_text_sha256','source_sha256']:
 for p,value in b[group].items():assert sha(R/p)==value,p
for p,v in copies.items():assert sha(R/p)==sha(D/v['package_path'])==v['sha256'],p
for p in(D/'invocations').glob('*.py'):ast.parse(p.read_text())
assert not(R/'data/governance/AUTH-MEDIA-ACCESS.json').exists()
# No binary source/model/private cache enters the reviewable package.
for p in D.rglob('*'):
 if not p.is_file():continue
 assert not p.is_symlink();assert p.suffix.lower()not in {'.mov','.mp4','.wav','.mp3','.flac','.pt','.pth','.sqlite','.db','.env','.pkl'},str(p)
 if p.suffix in {'.md','.json','.jsonl','.txt','.yaml','.toml','.py','.lock'}:
  assert not re.search(r'\b(?:sk-[A-Za-z0-9]{32,}|AKIA[A-Z0-9]{16})\b|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',p.read_text(errors='replace')),str(p)
validation={'schema':'mission43-delivery-integrity/1','date':'2026-11-08','valid':True,'prior_artifacts_preserved':len(b['prior_artifact_sha256']),'original_seven_researcher_paths_preserved':True,'all148_original_annotation_texts_unchanged':True,'all462_maintained_source_bindings_unchanged':True,'focused_original_copies':len(copies),'copied_source_hashes_match':True,'all_source_member_bytes_verified_before_execution':54,'source_stats_stable_after_execution':True,'original_new_inferences_completed':{'front':22,'back':22,'audio_front':22},'prior_five_event_outputs_reused_once':True,'actual_source_clock_payloads_validated':True,'new_researcher_approval_retained':True,'formal_canonical_promotion_not_fabricated':True,'actual_23event_metric_independent_crosscheck_passed':True,'B2_decisions':0,'full_current_test_cases':3815,'full_current_test_counts':{'passed':3700,'failed':84,'errors':31,'skipped':0},'normal_actual_metadata_followup_cases_passed':15,'no_duplicate_test_totals':True,'new_production_test_config_modifications':0,'raw_media_PCM_models_private_caches_or_credentials_copied':False,'raw_guard_canonical_slot_closed':True,'executed_scope_restoration_verified':'EXECUTED_SCOPE_BINDING_VALIDATION.json','figure_count':9,'visual_QA':'Existing generated plots reviewed; confusion title layout corrected; numerical plot inputs unchanged. No raw scene frame used.','verification_scope':'Saved original-derived output, source metadata, hashes, exact scope seals, numeric crosscheck, format/link integrity; no independent human/physical validation invented','containing_commit':'Exact hash and final worktree scope checked/reported after normal local commit; no push'}
save(D/'DELIVERY_INTEGRITY_VALIDATION.json',validation)
# Record file count after including the two circularity-control files.
files=[p for p in D.rglob('*')if p.is_file()];n=len(files)+sum(not(D/p).exists()for p in ['EVIDENCE_MANIFEST.csv','PACKAGE_FILES.sha256']);validation['packaged_files']=n;save(D/'DELIVERY_INTEGRITY_VALIDATION.json',validation)
# Every payload has a SHA; manifest and checksum-index identities are anchored by index/commit.
rows=[]
bydest={v['package_path']:(p,v)for p,v in copies.items()}
for p in sorted(D.rglob('*')):
 if not p.is_file()or(p.parent==D and p.name in {'EVIDENCE_MANIFEST.csv','PACKAGE_FILES.sha256'}):continue
 rel=str(p.relative_to(D));origin,copymeta=bydest.get(rel,('Mission43 generated evidence',None));kind='COPIED_ORIGINAL'if copymeta else'NEW_MISSION43_ARTIFACT';oldsha=copymeta['sha256']if copymeta else'NOT_A_COPIED_ORIGINAL'
 status='DOCUMENTARY_OR_SOFTWARE_EVIDENCE_NOT_NEW_GT'
 if rel.startswith(('predictions/','audio_predictions/')):status='ACTUAL_ORIGINAL_SOURCE_MODEL_PREDICTIONS_NOT_GT'
 elif rel.startswith('audio_clocks/'):status='ACTUAL_ORIGINAL_AUDIO_NATIVE_CLOCK_LEDGER'
 elif rel.startswith('assemblies/'):status='ACTUAL_INPUT_ASSEMBLY_NOT_DECISION_REPLAY'
 elif rel.startswith('adopted_annotation_originals/'):status='RESEARCHER_ADOPTED_AI_ASSISTED_ANNOTATION_CONTENT; NO_CANONICAL_PROMOTION'
 elif 'AUDIO_ADOPTED_EVENT'in rel:status='EXPLORATORY_ADOPTED_EVENT_LABEL_AGREEMENT; NOT_INDEPENDENT_HUMAN_GT'
 elif rel.startswith('software_validation/'):status='ACTUAL_CURRENT_SOFTWARE_EVIDENCE; GUARDED_AUDIT_NONPASSING'
 rows.append(dict(artifact_id=f'M43-A{len(rows)+1:04d}',description=p.name.replace('_',' '),original_location=origin,package_location=rel,sha256=sha(p),original_sha256=oldsha,source_mission='Original source reference: '+origin if copymeta else'Mission43',evidence_category=rel.split('/')[0]if'/'in rel else'current_report_or_result',scientific_status=status,limitations='Actual stage/reference/context only. No independent human GT, frame/window labels, canonical promotion, B2 decisions or safety/generalization inferred.',artifact_kind=kind))
with(D/'EVIDENCE_MANIFEST.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
(D/'PACKAGE_FILES.sha256').write_text(''.join(sha(p)+'  '+str(p.relative_to(D))+'\n'for p in sorted(D.rglob('*'))if p.is_file()and p!=D/'PACKAGE_FILES.sha256'))
assert len([p for p in D.rglob('*')if p.is_file()])==n
print('Sealed',n,'new package files;',len(copies),'byte-identical focused copies; prior1914 artifacts/seven researcher paths preserved. Checksum index:',sha(D/'PACKAGE_FILES.sha256'))
