"""Mission43 invocation utilities. Real-root guard records transcribe the actual user scope."""
from pathlib import Path
from datetime import datetime,UTC,timedelta
from contextlib import contextmanager
import os,json,hashlib,subprocess,sys
R=Path(__file__).resolve().parents[5];sys.path.insert(0,str(R/'src'));D=R/'docs/generated/professor_evidence/mission43'
def now():return datetime.now(UTC).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_name(p.name+'.writing');temp.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');temp.replace(p)
def stat(p):
 s=Path(p).stat();return {k:getattr(s,k)for k in ['st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns']}
def git():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
def identity(path,event,role):return f'doc:v2:{event}:{role}:video'
INV=read(R/'docs/PHASE11_3_REVIEW_INVENTORY.json')['events']
@contextmanager
def operation(phase):
 from railway_detection.safety.media_guard import _canonical_sha256,verify_authorization_record
 slot=R/'data/governance/AUTH-MEDIA-ACCESS.json';assert not slot.exists(),'Existing scope must not be overwritten'
 started=datetime.now(UTC);scope=D/'EXECUTION_SCOPE.md';record=read(R/'docs/generated/research_results/mission39/OP39_I_ISSUED_AUTHORIZATION.json')
 record.update(authorization_id='AUTH-MEDIA-ACCESS-M43-'+phase.upper()+'-'+started.strftime('%Y%m%dT%H%M%SZ'),authorized_at_utc=started.isoformat(),expires_at_utc=(started+timedelta(hours=8)).isoformat(),status='APPROVED',revoked=False,authorization_statement='Mission43 researcher explicitly directs full27-event source verification and existing frozen image/audio experiments, reusing completed five-event work. Authority attribution was previously explicitly confirmed; this is transcription of the current expanded direction, not a new signature.')
 record['recorded_by']['transcription_source']='Mission43 user attachment SHA256 '+read(D/'BASELINE_AND_PRESERVATION.json')['request_sha256']+' and existing authority/scope attribution in prior actual replies; EXECUTION_SCOPE.md records exact operative boundaries.'
 record['scope'].update(operations=['READ_RAW_MEDIA','HASH_RAW_MEDIA','MEDIA_PROBE','INFERENCE','AUDIO_EXTRACTION','FEATURE_EXTRACTION'],events=list(INV),purpose='Mission43 exact54-member read-only verification; remaining22 front/back frozen inference and22 front embedded-audio inference/input assembly; no GT promotion, decision replay, training, raw-media output or public release')
 record['restrictions']['path_prefixes']=[e['raw_media'][role]['path']for e in INV.values()for role in ['front','back']]
 record['bindings']['protocol_document']={'path':str(scope.relative_to(R)),'sha256':sha(scope)};record['record_sha256']=_canonical_sha256(record)
 assert record['authorized_by']=='raihankabirrahu@gmail.com'
 with slot.open('x')as f:json.dump(record,f,indent=2);f.write('\n')
 save(D/'operations'/f'{phase}_ISSUED_AUTHORIZATION.json',record)
 try:
  verify_authorization_record(R,operation='READ_RAW_MEDIA',media_path=R/record['restrictions']['path_prefixes'][0],event_id=next(iter(INV)))
  yield record
 finally:
  assert slot.exists()and read(slot)['record_sha256']==record['record_sha256'],'Canonical slot changed; preserve rather than overwrite'
  closed={**record,'status':'CLOSED','expires_at_utc':now()};closed['record_sha256']=_canonical_sha256(closed);save(D/'operations'/f'{phase}_CLOSED_AUTHORIZATION.json',closed);slot.unlink()
  save(D/'operations'/f'{phase}_COMPLETION.json',{'issued_record_sha256':record['record_sha256'],'closed_record_sha256':closed['record_sha256'],'closed_at_utc':now(),'canonical_slot_absent':not slot.exists(),'statement_origin':'Actual current Mission43 expanded execution direction; persistent confirmed authority attribution','no_GT_promotion_or_descriptive_replay_grant':True})
def art(path,rows):
 p=D/path;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),str(p)
 body=''.join(json.dumps(x,separators=(',',':'),allow_nan=False)+'\n'for x in rows);p.write_text(body);return {'path':str(p.relative_to(R)),'sha256':sha(p),'records':len(rows),'bytes':p.stat().st_size}
