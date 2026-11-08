"""Mission44 utilities; original-source diagnostics only with actual real-root scope."""
from pathlib import Path
from datetime import datetime,UTC,timedelta
from contextlib import contextmanager
import hashlib,json,csv,subprocess,sys,os
R=Path(__file__).resolve().parents[5];sys.path.insert(0,str(R/'src'));D=R/'docs/generated/professor_evidence/mission44';M=R/'docs/generated/professor_evidence/mission43'
def now():return datetime.now(UTC).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.writing');tmp.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def table(name,rows):
 with(D/name).open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def csvrows(p):return list(csv.DictReader(Path(p).open()))
def stat(p):
 s=Path(p).stat();return {k:getattr(s,k)for k in ['st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns']}
def payload(a):
 p=R/a['path'];assert sha(p)==a['sha256'];return [json.loads(t)for t in p.read_text().splitlines()]
INV=read(R/'docs/PHASE11_3_REVIEW_INVENTORY.json')['events']
@contextmanager
def source_operation():
 from railway_detection.safety.media_guard import _canonical_sha256,verify_authorization_record
 plan=read(D/'SOURCE_DIAGNOSTIC_PLAN.json');scope=D/'SOURCE_DIAGNOSTIC_SCOPE.md';slot=R/'data/governance/AUTH-MEDIA-ACCESS.json';assert not slot.exists();t=datetime.now(UTC)
 x=read(M/'operations/verification_ISSUED_AUTHORIZATION.json');x.update(authorization_id='AUTH-MEDIA-ACCESS-M44-DIAGNOSTICS-'+t.strftime('%Y%m%dT%H%M%SZ'),authorized_at_utc=t.isoformat(),expires_at_utc=(t+timedelta(hours=4)).isoformat(),status='APPROVED',revoked=False,authorization_statement='Mission44 user explicitly requests targeted original-frame and acoustic-source error investigation, reusing full27 predictions. Previously confirmed authority attribution persists; this recorded transcription covers the exact diagnostic members/method and creates no inference, GT or replay permission.')
 x['recorded_by']['transcription_source']='Actual Mission44 brief §§3.4/4.1 and final instruction; request SHA256 '+read(D/'BASELINE_AND_PRESERVATION.json')['request_sha256']+'; exact SOURCE_DIAGNOSTIC_PLAN.json and hash-bound scope'
 x['scope'].update(operations=['READ_RAW_MEDIA','FRAME_EXTRACTION','AUDIO_EXTRACTION','FEATURE_EXTRACTION'],events=sorted({a['event']for a in plan['members']}),purpose='Mission44 bounded actual-source frame/signal diagnostics on named zero-output/control/audio-error cases; no model inference/retraining/calibration, GT creation, raw/PCM retention in professor package, playback release or B2 decision replay')
 x['restrictions']['path_prefixes']=sorted({a['path']for a in plan['members']});x['bindings']['protocol_document']={'path':str(scope.relative_to(R)),'sha256':sha(scope)};x['record_sha256']=_canonical_sha256(x)
 with slot.open('x')as f:json.dump(x,f,indent=2);f.write('\n')
 save(D/'operations/DIAGNOSTICS_ISSUED_AUTHORIZATION.json',x)
 try:
  verify_authorization_record(R,operation='READ_RAW_MEDIA',media_path=R/x['restrictions']['path_prefixes'][0],event_id=None);yield x
 finally:
  assert read(slot)['record_sha256']==x['record_sha256'];closed={**x,'status':'CLOSED','expires_at_utc':now()};closed['record_sha256']=_canonical_sha256(closed);save(D/'operations/DIAGNOSTICS_CLOSED_AUTHORIZATION.json',closed);slot.unlink()
  save(D/'operations/DIAGNOSTICS_COMPLETION.json',{'closed_at_utc':now(),'canonical_slot_absent':not slot.exists(),'issued_record_sha256':x['record_sha256'],'closed_record_sha256':closed['record_sha256'],'no_new_inference_or_GT_or_B2_grant':True})
