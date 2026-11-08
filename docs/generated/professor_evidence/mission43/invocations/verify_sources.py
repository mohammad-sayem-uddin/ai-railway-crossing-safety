"""Actual guarded54-member source hash/header/stability inspection; no frame rendering."""
from common import *
import time,traceback,collections
from railway_detection.safety.media_guard import require_media_authorization,require_media_command_authorization
run={'schema':'mission43-original-source-verification/1','started_at_utc':now(),'git_commit':git(),'invocation_sha256':sha(__file__),'members':[],'planned':54,'actual_command':'PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/verify_sources.py','duplicate_exclusions':'Two historical engine duplicate camera references remain excluded; not opened','new_researcher_annotation_adoption':'RESEARCHER_ANNOTATION_ADOPTION.json'}
p=D/'SOURCE_VERIFICATION_RECEIPT.json';save(p,run)
with operation('verification'):
 for event,e in INV.items():
  for role in ['front','back']:
   info=e['raw_media'][role];original=R/info['path'];r={'event':event,'camera':role,'source_id':identity(original,event,role),'path':info['path'],'inventory_sha256':info['sha256'],'started_at_utc':now()};run['members'].append(r);t=time.perf_counter()
   try:
    require_media_authorization(original,'HASH_RAW_MEDIA',declared_media=True);before=stat(original);hh=hashlib.sha256()
    with original.open('rb')as f:
     for block in iter(lambda:f.read(4*1024*1024),b''):hh.update(block)
    r['fresh_sha256']=hh.hexdigest();assert r['fresh_sha256']==info['sha256'],'SOURCE_HASH_MISMATCH'
    command=['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(original)]
    require_media_command_authorization(command,'MEDIA_PROBE');proc=subprocess.run(command,capture_output=True,text=True,check=False);r.update(ffprobe_command=command,ffprobe_returncode=proc.returncode,ffprobe_stderr=proc.stderr);assert proc.returncode==0,proc.stderr
    probe=json.loads(proc.stdout);videos=[s for s in probe['streams']if s['codec_type']=='video'];audios=[s for s in probe['streams']if s['codec_type']=='audio'];assert len(videos)==1,'AMBIGUOUS_VIDEO_STREAM';after=stat(original);assert before==after,'SOURCE_CHANGED'
    r.update(status='VERIFIED_EXACT_SOURCE_BYTES_AND_HEADERS',before=before,after=after,source_stable=True,video=videos[0],audio=audios,format={k:probe['format'].get(k)for k in ['format_name','duration','size','bit_rate']},wall_s=time.perf_counter()-t)
   except Exception as exc:r.update(status='FAILED_VERIFICATION',error_type=type(exc).__name__,error=str(exc),wall_s=time.perf_counter()-t);traceback.print_exc()
   save(p,run);print(json.dumps({'event':event,'camera':role,'status':r['status'],'wall_s':r['wall_s']}),flush=True)
run.update(finished_at_utc=now(),verified=sum(r['status']=='VERIFIED_EXACT_SOURCE_BYTES_AND_HEADERS'for r in run['members']),failed=sum(r['status']!='VERIFIED_EXACT_SOURCE_BYTES_AND_HEADERS'for r in run['members']));save(p,run)
