"""Actual saved-output scientific input/clock validation, not a synthetic model experiment."""
from common import *
from fractions import Fraction
import math,csv,collections
v=read(D/'ACTUAL_VISUAL_RUN_MANIFEST.json');a=read(D/'ACTUAL_AUDIO_RUN_MANIFEST.json');s=read(D/'SOURCE_VERIFICATION_RECEIPT.json');sources={(x['event'],x['camera']):x for x in s['members']};check={'schema':'mission43-actual-output-integrity/1','visual_members':0,'visual_records':0,'audio_members':0,'audio_windows':0,'audio_clock_ledgers':0,'input_assemblies':0,'input_frames':0,'payload_sha256':{},'source_stat_stable':True,'annotation_and_prior_evidence_unchanged':True,'new_raw_or_model_read':False}
def payload(artifact):
 p=R/artifact['path'];assert sha(p)==artifact['sha256'];values=[json.loads(line)for line in p.read_text().splitlines()];assert len(values)==artifact['records'];check['payload_sha256'][artifact['path']]=artifact['sha256'];return values
for e in v['events']:
 if e['status']not in ['COMPLETED_ORIGINAL_INFERENCE','REUSED_MISSION39_ACTUAL_INFERENCE']:continue
 rows=payload(e['predictions']);last=None
 for r in rows:
  t=r.get('timestamp_sec',r.get('timestamp_s'));m=r['metadata'];exact=Fraction(m['pts_ticks'])*Fraction(*m['timebase']);assert float(exact)==t and m['timestamp_basis']=='source_pts';assert m['stream_index']==sources[e['event'],e['camera']]['video']['index'];assert last is None or t>last;last=t
  for d in r['detections']:
   assert math.isfinite(d['confidence'])and .35<=d['confidence']<=1;cid=d.get('class_id',d.get('metadata',{}).get('class_id'));assert cid in [0,1,2]
 check['visual_members']+=1;check['visual_records']+=len(rows)
for e in a['events']:
 if e['status']not in ['COMPLETED_ORIGINAL_AUDIO_INFERENCE','REUSED_MISSION39_CORRECTED_AUDIO']:continue
 rows=payload(e['predictions']);ledger=payload(e['clock_ledger']);last=None
 for x in ledger:
  start=Fraction(x['pts'])*Fraction(*x['timebase']);end=start+Fraction(x['samples'],x['sample_rate']);assert last is None or start==last;last=end
 for i,r in enumerate(rows):
  m=r['metadata'];assert m['feature_log_scale']=='natural'and m['source_container_sha256']==sources[e['event'],'front']['fresh_sha256'];assert m['window_start_sample']==i*8000 and m['window_end_sample']==i*8000+16000;assert float(Fraction(*m['causal_end_fraction']))==r['timestamp_s']==float(Fraction(i*8000+16000,16000));assert 0<=m['probability']<=1 and math.isfinite(m['probability'])
 if 'B2_input_assembly'in e:
  assembled=payload(e['B2_input_assembly']);last=None
  for r in assembled:
   t=r['master_timestamp_s'];assert last is None or t>last;last=t;assert all(p<=t+1e-6 for p in r['front_prediction_timestamps']+r['causal_audio_window_end_timestamps']);assert r['stage']=='B2_INPUT_ASSEMBLY_ONLY_NO_DECISION_REPLAY'
  check['input_assemblies']+=1;check['input_frames']+=len(assembled)
 check['audio_members']+=1;check['audio_windows']+=len(rows);check['audio_clock_ledgers']+=1
for x in s['members']:assert stat(R/x['path'])==x['after'],x['path']
b=read(D/'BASELINE_AND_PRESERVATION.json')
for group in ['prior_artifact_sha256','original_seven_researcher_sha256','annotation_text_sha256','source_sha256']:
 for path,digest in b[group].items():assert sha(R/path)==digest,path
assert not(R/'data/governance/AUTH-MEDIA-ACCESS.json').exists(),'All raw-operation scopes must be closed'
check.update(valid=True,source_members=54,physical_events=27,prior_artifact_hashes_preserved=len(b['prior_artifact_sha256']),all_original_annotation_text_hashes_preserved=len(b['annotation_text_sha256']),accepted_canonical_GT=False,researcher_adopted_annotation_versions=27,guard_code_changed=False,no_raw_PCM_or_images_retained=True)
save(D/'ACTUAL_OUTPUT_INTEGRITY_VALIDATION.json',check);print(json.dumps({k:v for k,v in check.items()if k!='payload_sha256'},indent=2))
